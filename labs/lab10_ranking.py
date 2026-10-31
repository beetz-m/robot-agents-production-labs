"""Lab for Ch. 10 (ranking over parameter ranges): sample a box with a Latin hypercube and count where the robot
decision flips between the factory alone and the factory coupled to a seasonal campaign. Every parameter and every
bound ILLUSTRATIVE (register.yaml); write your predictions down before you run it."""
from scipy.stats import qmc
import _common  # noqa: F401  (puts tmodel on the path)
from tmodel.chain import Chain, ranks

BOX = {"demand": (180, 300), "quay": (40, 300), "season_len": (12, 36), "robot_cost": (2000, 15000), "premium": (0.0, 0.5)}
u = qmc.LatinHypercube(d=len(BOX), seed=20261031).random(60)
kinds = {"flip": 0, "partial": 0, "stable": 0}
for row in u:
    p = {k: lo + x * (hi - lo) for x, (k, (lo, hi)) in zip(row, BOX.items())}
    c = Chain(demand=p["demand"], quay=p["quay"], season=(14, 14 + int(p["season_len"])), robot_cost=p["robot_cost"],
              premium=p["premium"])
    r = ranks(c)
    kind = "stable" if r["alone"] == r["coupled"] else "partial" if "tie" in r.values() else "flip"
    kinds[kind] += 1
print({k: f"{v / len(u):.0%}" for k, v in kinds.items()}, "of", len(u), "points")
print("Now: where in the box are the flips? Compare their parameters with the rest (and register that comparison first).")

# Q: Register your prediction first: in what share of the box will the robot decision flip?
# Q: Compare the parameters of the flipping points with the rest. Was this comparison planned before you looked?
# Q: Who chose the bounds of the box, and how would the result change with other bounds?
