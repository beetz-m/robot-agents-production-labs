"""Fixed-position assembly in docks (textbook Ch. 6-7): the product stays in its dock, crews come to it.

    from tmodel.docks import Docks, run
    r = run(Docks(n_docks=6, steps=[("A", 10), ("B", 12), ("C", 9)], crews={"A": 1, "B": 1, "C": 1}), hours=20000)

Each dock builds one product at a time through the steps in order; a step needs one crew of its type
(crews = {type: count}, specialist crews) or any crew of a pool (crews = N, cross-trained). A crew that finishes a step
leaves the dock. Breakdowns (mtbf_h, mttr_h) strike a dock step while it works; crew_waits=True keeps the crew at the
dock during the repair, False sends it elsewhere and re-requests a crew afterwards. Variability as in line.py.
All parameters ILLUSTRATIVE.
"""
import random
from dataclasses import dataclass

from .des import Env, Resource
from .line import _factor


@dataclass
class Docks:
    n_docks: int
    steps: list                   # [(crew type, mean hours), ...]
    crews: object                 # {type: count} or int (pooled)
    dist: str = "tri"
    breakdown: tuple | None = None
    crew_waits: bool = False


def run(d: Docks, hours: float, seed: int = 1, warmup: float | None = None):
    rng = random.Random(seed)
    env = Env()
    warm = hours * 0.1 if warmup is None else warmup
    pooled = isinstance(d.crews, int)
    res = Resource(env, d.crews) if pooled else {k: Resource(env, v) for k, v in d.crews.items()}
    done = []

    def crew(kind):
        return res if pooled else res[kind]

    def dock(k):
        while True:
            start = env.now
            for kind, mean in d.steps:
                c = crew(kind)
                yield c.request()
                w = mean * _factor(d.dist, rng)
                if d.breakdown:
                    mtbf, mttr = d.breakdown
                    t = rng.expovariate(1 / mtbf)
                    while t < w:
                        yield env.timeout(t)
                        w -= t
                        rep = rng.expovariate(1 / mttr)
                        if d.crew_waits:
                            yield env.timeout(rep)
                        else:
                            c.release()
                            yield env.timeout(rep)
                            yield c.request()
                        t = rng.expovariate(1 / mtbf)
                yield env.timeout(w)
                c.release()
            if env.now > warm:
                done.append(env.now - start)

    for k in range(d.n_docks):
        env.process(dock(k))
    env.run(hours)
    span = hours - warm
    return dict(throughput_per_h=len(done) / span, completed=len(done),
                lead_h=sum(done) / len(done) if done else float("nan"))
