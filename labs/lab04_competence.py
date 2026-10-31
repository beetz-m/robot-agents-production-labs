"""Lab for Ch. 4 (competence as production parameters): how much of the supply robots' gain survives imperfect robots,
against the expected net relief, without and with one buffer place. Every parameter ILLUSTRATIVE (register.yaml)."""
import matplotlib.pyplot as plt
from _common import per_year, save, SEEDS
from tmodel.line import Line, mean_over_seeds
from tmodel.robots import Profile, expected

SUPPLY = {i: [0.4, 0.4, 0.3] for i in range(5)}
profiles = [Profile(), Profile(p=0.95, A=0.97, r_h=0.25), Profile(p=0.8, A=0.9, r_h=0.5), Profile(p=0.7, A=0.9, r_h=0.5),
            Profile(p=0.6, A=0.9, r_h=0.5), Profile(p=0.8, A=1.0, r_h=0.5, recovery="operator")]
fig, ax = plt.subplots(figsize=(5, 3.5))
for B, mark in ((0, "o"), (1, "s")):
    base = Line(times=[10] * 5, buffers=B, supply=SUPPLY)
    none, _ = mean_over_seeds(base, 40000, SEEDS)
    det, _ = mean_over_seeds(Line(**{**base.__dict__, "robot": "deterministic"}), 40000, SEEDS)
    print(f"buffers {B}: no robots {per_year(none):.1f}, perfect robots {per_year(det):.1f} a year")
    xs, ys = [], []
    for pr in profiles:
        th, _ = mean_over_seeds(Line(**{**base.__dict__, "robot": pr}), 40000, SEEDS)
        share, _, crew = expected(pr)
        tasks = SUPPLY[0]
        net = (share * sum(tasks) - crew * len(tasks)) / sum(tasks)      # Ch. 4, Eq. relief, per station visit
        kept = (th - none) / (det - none)
        xs.append(net)
        ys.append(kept)
        print(f"  p {pr.p:.2f} A {pr.A:.2f} r {pr.r_h:.2f} {pr.recovery:8s}: net relief {net:5.2f}  gain kept {kept:5.2f}")
    ax.plot(xs, ys, mark, label=f"{B} buffer place(s)")
ax.plot([-0.2, 1], [-0.2, 1], ":", color="grey")
ax.set_xlabel("expected net relief (share of nominal)")
ax.set_ylabel("share of the gain kept")
ax.legend()
save(fig, "lab04_competence.png")

# Q: Write down, before running: will the gain kept lie above, on or below the line 'kept = net relief'?
# Q: Why does operator recovery keep almost all of the gain?
# Q: In the twin of the book, losses on a balanced line without buffers passed through one for one; here they do not. What could make the difference?
