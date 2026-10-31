"""Checks of the teaching model against laws and closed forms; each fails if the model is wrong in a specific way."""
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tmodel.des import Env, Store                      # noqa: E402
from tmodel.line import Line, run, mean_over_seeds     # noqa: E402
from tmodel.robots import Profile, IDEAL, expected, realise  # noqa: E402
from tmodel.docks import Docks, run as run_docks       # noqa: E402
from tmodel.chain import Chain, plan                   # noqa: E402


def test_store_capacity_zero_is_a_hand_over():
    # wrong if a capacity-0 store holds items (then a line without buffers would have hidden buffers)
    env, s, log = Env(), Store(Env(), 0), []
    env = s.env

    def producer():
        yield s.put("a")
        log.append(("put done", env.now))

    def consumer():
        yield env.timeout(5)
        x = yield s.get()
        log.append(("got " + x, env.now))
    env.process(producer())
    env.process(consumer())
    env.run(10)
    assert ("put done", 5.0) in log and ("got a", 5.0) in log


@pytest.mark.parametrize("B", [0, 1, 2])
def test_two_station_exponential_line_matches_closed_form(B):
    # Ch. 5: TH = mu (B+2)/(B+3) for two exponential stations with equal rates and B buffer places
    th, se = mean_over_seeds(Line(times=[1.0, 1.0], buffers=B, dist="exp"), 60000, seeds=range(1, 5))
    assert th == pytest.approx((B + 2) / (B + 3), rel=0.02)


def test_littles_law_holds_with_measured_wip():
    # Ch. 3: measured time-average WIP = throughput x mean lead time (a real check: WIP is counted, not computed)
    r = run(Line(times=[10, 12, 9, 12, 8], buffers=1), hours=200000, seed=3)
    assert r["wip"] == pytest.approx(r["throughput_per_h"] * r["lead_h"], rel=0.02)


def test_deterministic_line_runs_at_its_bottleneck_rate():
    r = run(Line(times=[10, 12, 9, 12, 8], buffers=0, dist="det"), hours=20000, seed=1)
    assert r["throughput_per_h"] == pytest.approx(1 / 12, rel=0.01)


def test_one_pooled_crew_serialises_the_line():
    # wrong if a pooled crew can work at two stations at once
    r = run(Line(times=[10, 12, 9], buffers=5, dist="det", crews=1), hours=20000, seed=1)
    assert r["throughput_per_h"] <= 1 / 31 * 1.01


@pytest.mark.parametrize("pr", [Profile(p=0.9, A=0.95, r_h=0.25), Profile(p=0.7, A=0.8, r_h=0.5, rho=0.5, k_max=2)])
def test_robot_closed_form_matches_sampler(pr):
    rng, hs, n = random.Random(5), [0.5] * 10, 20000
    rel = intv = 0.0
    for _ in range(n):
        a, b = realise(hs, pr, rng)
        rel += a
        intv += b
    share, interv_h, _ = expected(pr)
    assert rel / (n * sum(hs)) == pytest.approx(share, abs=0.01)
    assert intv / (n * len(hs)) == pytest.approx(interv_h, rel=0.03)


SUPPLY = {i: [0.4, 0.4, 0.3] for i in range(5)}


def test_ideal_robots_reproduce_deterministic_relief_and_are_not_vacuous():
    base = Line(times=[10] * 5, buffers=0, supply=SUPPLY)
    det = [run(Line(**{**base.__dict__, "robot": "deterministic"}), 20000, seed=s)["completed"] for s in (1, 2)]
    ideal = [run(Line(**{**base.__dict__, "robot": IDEAL}), 20000, seed=s)["completed"] for s in (1, 2)]
    none = [run(base, 20000, seed=s)["completed"] for s in (1, 2)]
    assert ideal == det
    assert sum(det) > sum(none) * 1.05            # guard: the relief reaches the model


def test_no_availability_is_no_robots():
    base = Line(times=[10] * 5, buffers=0, supply=SUPPLY)
    none = [run(base, 20000, seed=s)["completed"] for s in (1, 2)]
    zero = [run(Line(**{**base.__dict__, "robot": Profile(A=0.0)}), 20000, seed=s)["completed"] for s in (1, 2)]
    assert zero == none


def test_breakdowns_stretch_work_by_one_over_availability():
    # Ch. 4: t_e = t_0 / A for outages while working
    A, mttr = 0.8, 2.0
    mtbf = mttr * A / (1 - A)
    r = run(Line(times=[10.0], dist="det", breakdown=(mtbf, mttr)), hours=400000, seed=2)
    assert 1 / r["throughput_per_h"] == pytest.approx(10.0 / A, rel=0.03)


def test_docks_without_crew_limits_work_in_parallel():
    r1 = run_docks(Docks(n_docks=1, steps=[("A", 5), ("B", 5)], crews={"A": 3, "B": 3}, dist="det"), 20000)
    r3 = run_docks(Docks(n_docks=3, steps=[("A", 5), ("B", 5)], crews={"A": 3, "B": 3}, dist="det"), 20000)
    assert r1["throughput_per_h"] == pytest.approx(1 / 10, rel=0.01)
    assert r3["throughput_per_h"] == pytest.approx(3 / 10, rel=0.01)


def test_rework_bay_costs_less_than_rework_back_into_the_line():
    base = dict(times=[10, 10, 10, 10, 10], buffers=1)
    park, _ = mean_over_seeds(Line(**base, rework=(0.15, 2, "park", 16)), 40000, range(1, 4))
    bay, _ = mean_over_seeds(Line(**base, rework=(0.15, 2, "bay", 16)), 40000, range(1, 4))
    clean, _ = mean_over_seeds(Line(**base), 40000, range(1, 4))
    assert park < clean and bay > park


def test_chain_alone_meets_flat_demand_without_shortfall():
    r = plan(Chain(demand=200), coupled=False)
    assert r["short"] < 1e-6 and r["output"] == pytest.approx(200, rel=1e-6)


def test_chain_coupled_builds_ahead_of_the_season():
    r = plan(Chain(demand=240), coupled=True)
    w = r["weekly"]
    assert sum(w[:14]) > 0                         # output before the campaign starts goes to the quay
