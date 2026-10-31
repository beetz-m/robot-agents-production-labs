"""Lab for Ch. 3 (flow laws): Little's law with measured work in process, and what buffer places buy.
Every parameter ILLUSTRATIVE (register.yaml)."""
import matplotlib.pyplot as plt
from _common import per_year, save, SEEDS
from tmodel.line import Line, run, mean_over_seeds

line = Line(times=[10, 10, 10, 10, 10])
print("Little's law, measured WIP against throughput x mean lead time:")
for B in (0, 1, 3):
    r = run(Line(**{**line.__dict__, "buffers": B}), 100000, seed=1)
    print(f"  buffers {B}: WIP {r['wip']:.2f}  TH x lead {r['throughput_per_h'] * r['lead_h']:.2f}")
print("Output against buffer places (balanced line, triangular variability):")
xs, ys = list(range(0, 6)), []
for B in xs:
    th, se = mean_over_seeds(Line(**{**line.__dict__, "buffers": B}), 40000, SEEDS)
    ys.append(per_year(th))
    print(f"  {B} places: {per_year(th):6.1f} a year (+- {per_year(se):.1f})")
fig, ax = plt.subplots(figsize=(5, 3))
ax.plot(xs, ys, "o-")
ax.set_xlabel("buffer places per hand-over")
ax.set_ylabel("products a year (ILLUSTRATIVE)")
save(fig, "lab03_buffers.png")

# Q: Why does the measured work in process agree with throughput times lead time, and when would it not (short runs, warm-up)?
# Q: Which buffer against variability does the line without places use, and which the line with one place?
# Q: The second buffer place buys far less than the first. Why?
