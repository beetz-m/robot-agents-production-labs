"""Lab for Ch. 6 (lines, docks, pooling): output against crews for a line with fixed crews, a line with floaters,
and docks with specialist or cross-trained crews. Every parameter ILLUSTRATIVE (register.yaml)."""
from _common import per_year, SEEDS
from tmodel.line import Line, mean_over_seeds
from tmodel.docks import Docks, run

times = [10, 10, 10, 10, 10]
fixed, _ = mean_over_seeds(Line(times=times, buffers=1), 30000, SEEDS)
print(f"line, 5 fixed crews, one buffer place: {per_year(fixed):.1f} a year")
for n in (3, 4, 5):
    th, _ = mean_over_seeds(Line(times=times, buffers=1, crews=n), 30000, SEEDS)
    print(f"line with {n} floaters (pooled):      {per_year(th):.1f} a year")
steps = [(f"S{i}", t) for i, t in enumerate(times)]
for nd in (5, 8):
    spec = sum(run(Docks(n_docks=nd, steps=steps, crews={f"S{i}": 1 for i in range(5)}), 30000, seed=s)["throughput_per_h"] for s in SEEDS) / len(SEEDS)
    cross = sum(run(Docks(n_docks=nd, steps=steps, crews=5), 30000, seed=s)["throughput_per_h"] for s in SEEDS) / len(SEEDS)
    print(f"{nd} docks, 5 specialist crews: {per_year(spec):.1f}; 5 cross-trained crews: {per_year(cross):.1f} a year")
print("Question: which lever does each comparison change, and which comparison is fair (Ch. 6, Section 'A fair comparison')?")

# Q: Which of these comparisons give both options the same levers (crews, buffers, pooling)?
# Q: Why do cross-trained crews at docks reach the line's output with fewer docks than specialist crews?
# Q: What does the model leave out that would favour fixed crews (walking, training, skill)?
