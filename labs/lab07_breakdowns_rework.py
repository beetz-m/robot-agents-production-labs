"""Lab for Ch. 7 (breakdowns, rework): short against long repairs at the same availability, line against docks; rework
back into the line against a rework bay. Every parameter ILLUSTRATIVE (register.yaml)."""
import statistics
from _common import per_year, SEEDS
from tmodel.line import Line, run as run_line
from tmodel.docks import Docks, run as run_docks

times, A = [10, 10, 10, 10, 10], 0.95
steps = [(f"S{i}", t) for i, t in enumerate(times)]
for mttr in (1, 24):
    mtbf = mttr * A / (1 - A)
    ln = [per_year(run_line(Line(times=times, buffers=1, breakdown=(mtbf, mttr)), 40000, seed=s)["throughput_per_h"]) for s in SEEDS]
    dk = [per_year(run_docks(Docks(n_docks=6, steps=steps, crews={f"S{i}": 1 for i in range(5)}, breakdown=(mtbf, mttr)), 40000, seed=s)["throughput_per_h"]) for s in SEEDS]
    dw = [per_year(run_docks(Docks(n_docks=6, steps=steps, crews={f"S{i}": 1 for i in range(5)}, breakdown=(mtbf, mttr), crew_waits=True), 40000, seed=s)["throughput_per_h"]) for s in SEEDS]
    f = lambda v: f"{statistics.mean(v):6.1f} (sd {statistics.stdev(v):4.1f})"  # noqa: E731
    print(f"repair {mttr:2d} h: line {f(ln)}  docks {f(dk)}  docks, crews wait {f(dw)}")
for mode in ("park", "bay"):
    v = [per_year(run_line(Line(times=times, buffers=1, rework=(0.15, 2, mode, 16)), 40000, seed=s)["throughput_per_h"]) for s in SEEDS]
    print(f"rework 15 %, 16 h, {mode}: {statistics.mean(v):.1f} a year")

# Q: At equal availability, why do long repairs hurt the line more than the docks?
# Q: Why do docks lose when crews wait during repairs, and win when they leave?
# Q: What does the spread across seeds tell a plant manager that the mean does not?
