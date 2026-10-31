"""Lab for Ch. 5 (where competence becomes output): relief at one station against relief everywhere, for a line with
a clear constraint and for a balanced line. Every parameter ILLUSTRATIVE (register.yaml)."""
import matplotlib.pyplot as plt
from _common import per_year, save, SEEDS
from tmodel.line import Line, mean_over_seeds

lines = {"one constraint": [10, 12, 9, 12, 8], "balanced": [10, 10, 10, 10, 10]}
shares = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3]
fig, axs = plt.subplots(1, 2, figsize=(9, 3.2), sharey=True)
for ax, (name, times) in zip(axs, lines.items()):
    worst = max(range(len(times)), key=lambda i: times[i])
    for label, which in (("station 2 only", [2]), ("the longest station only", [worst]), ("every station", range(len(times)))):
        ys = []
        for s in shares:
            t = [x * (1 - s) if i in which else x for i, x in enumerate(times)]
            th, _ = mean_over_seeds(Line(times=t, buffers=0), 30000, SEEDS)
            ys.append(per_year(th))
        ax.plot(shares, ys, "o-", label=label)
        print(name, label, [round(y, 1) for y in ys])
    ax.set_title(name)
    ax.set_xlabel("relief share")
axs[0].set_ylabel("products a year (ILLUSTRATIVE)")
axs[1].legend(fontsize=8)
save(fig, "lab05_staircase.png")

# Q: In the line with one constraint, why does relief at the longest station stop paying so early?
# Q: Why does relief at one station of the balanced line still raise output a little?
# Q: Where would a robot pay most, and what would you need to know about a real line to say so?
