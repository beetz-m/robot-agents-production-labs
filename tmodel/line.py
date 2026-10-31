"""A serial production line (textbook Ch. 3-7): stations, buffers, crews, breakdowns, rework, supply robots.

    from tmodel.line import Line, run
    r = run(Line(times=[10, 12, 9, 12, 8], buffers=0), hours=20000, seed=1)
    r["throughput_per_h"], r["wip"], r["lead_h"]

Semantics
- Station 0 never starves (raw material always there). A product holds its station until the next station or a
  buffer place takes it (blocking after service). `buffers` = places between consecutive stations (0 = none).
- Work per product = mean time x a variability factor: 'det' (1), 'tri' (triangular 0.9 / 1.0 / 1.3, as a multiplier;
  its mean is 1.067) or 'exp' (exponential with the mean).
- Crews: crews=None gives every station its own crew; crews=N pools N crews over all stations (a station works only
  while it holds a crew; the crew leaves when the work is done, not while the station is blocked).
- Breakdowns (mtbf_h, mttr_h): failures strike while a station works (exponential times); the repair adds to the job.
- Rework (share, back_to, mode, hours): after the last station a product fails with probability `share` and is
  reworked once: 'park' sends it back into station `back_to` (served before new work), 'bay' to a separate rework bay
  with one crew, after which it is tested again.
- Supply robots: supply = {station: [task hours, ...]} is part of that station's mean work; robot=None leaves it with
  the crew, robot='deterministic' removes all of it, robot=Profile(...) removes what the profile realises per visit
  (and adds crew recovery time if recovery='crew'). The robots draw from their own generator.
Measures over the time after warm-up: throughput, time-average work in process (measured, not computed), mean lead
time, station states. All parameters are ILLUSTRATIVE (register.yaml).
"""
import random
from dataclasses import dataclass, field

from .des import Env, Resource, Store
from .robots import Profile, realise


@dataclass
class Line:
    times: list
    buffers: int = 0
    dist: str = "tri"
    crews: int | None = None
    breakdown: tuple | None = None          # (mtbf_h, mttr_h)
    rework: tuple | None = None             # (share, back_to, 'park' | 'bay', rework_h)
    supply: dict = field(default_factory=dict)
    robot: object = None                    # None | 'deterministic' | Profile


def _factor(dist, rng):
    if dist == "det":
        return 1.0
    if dist == "tri":
        return rng.triangular(0.9, 1.3, 1.0)
    if dist == "exp":
        return rng.expovariate(1.0)
    raise ValueError(dist)


def run(line: Line, hours: float, seed: int = 1, warmup: float | None = None):
    rng, rrng = random.Random(seed), random.Random(10_007 * seed + 3)
    env = Env()
    n = len(line.times)
    warm = hours * 0.1 if warmup is None else warmup
    stores = [Store(env, line.buffers) for _ in range(n)]          # stores[i]: input of station i (i >= 1)
    pool = Resource(env, line.crews) if line.crews else None
    bay = Resource(env, 1)
    park = [[] for _ in range(n)]
    st = [dict(work=0.0, blocked=0.0, starved=0.0) for _ in range(n)]
    done, wip = [], dict(n=0, area=0.0, t=0.0)
    robot_h = dict(relief=0.0, interv=0.0)

    def wip_change(d):
        if env.now > warm:
            wip["area"] += wip["n"] * (env.now - max(wip["t"], warm))
        wip["t"] = env.now
        wip["n"] += d

    def acc(i, key, t0):
        lo = max(t0, warm)
        if env.now > lo:
            st[i][key] += env.now - lo

    def work_hours(i, item):
        base = line.times[i] * _factor(line.dist, rng)
        tasks = line.supply.get(i, [])
        if tasks and line.robot is not None:
            if line.robot == "deterministic":
                rel, intv = sum(tasks), 0.0
            else:
                rel, intv = realise(tasks, line.robot, rrng)
            robot_h["relief"] += rel
            robot_h["interv"] += intv
            crew_extra = intv if (line.robot != "deterministic" and line.robot.recovery == "crew") else 0.0
            base = max(base - rel * (base / line.times[i]), 0.0) + crew_extra
        if line.breakdown:
            mtbf, mttr = line.breakdown
            t, down = rng.expovariate(1 / mtbf), 0.0
            while t < base:
                down += rng.expovariate(1 / mttr)
                t += rng.expovariate(1 / mtbf)
            base += down
        return base

    def station(i):
        while True:
            t0 = env.now
            if park[i]:
                item = park[i].pop(0)
            elif i == 0:
                item = dict(start=env.now, reworked=False)
                wip_change(+1)
            else:
                item = yield stores[i].get()
            acc(i, "starved", t0)
            if pool:
                yield pool.request()
            t1 = env.now
            w = line.rework[3] if item.pop("rework_here", False) else work_hours(i, item)
            yield env.timeout(w)
            if pool:
                pool.release()
            acc(i, "work", t1)
            t2 = env.now
            if i == n - 1:
                rw = line.rework
                if rw and not item["reworked"] and rng.random() < rw[0]:
                    item["reworked"] = True
                    if rw[2] == "park":
                        item["rework_here"] = True
                        park[rw[1]].append(item)
                    else:
                        env.process(rework_bay(item))
                else:
                    item["end"] = env.now
                    wip_change(-1)
                    if env.now > warm:
                        done.append(item)
            else:
                yield stores[i + 1].put(item)
            acc(i, "blocked", t2)

    def rework_bay(item):
        yield bay.request()
        yield env.timeout(line.rework[3])
        bay.release()
        yield stores[n - 1].put(item)

    for i in range(n):
        env.process(station(i))
    env.run(hours)
    wip_change(0)
    span = hours - warm
    lead = [d["end"] - d["start"] for d in done]
    return dict(
        throughput_per_h=len(done) / span,
        completed=len(done),
        wip=wip["area"] / span,
        lead_h=sum(lead) / len(lead) if lead else float("nan"),
        states=[{k: v / span for k, v in s.items()} for s in st],
        robot_hours=robot_h,
        crew_utilisation=(pool.busy_time / (pool.n * env.now)) if pool else None,
    )


def mean_over_seeds(line, hours, seeds, key="throughput_per_h", **kw):
    vals = [run(line, hours, seed=s, **kw)[key] for s in seeds]
    m = sum(vals) / len(vals)
    sd = (sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5 if len(vals) > 1 else 0.0
    return m, sd / len(vals) ** 0.5
