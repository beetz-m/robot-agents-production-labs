"""A factory planned with a seasonal installation campaign behind it (textbook Ch. 10-11), as a linear program.

    from tmodel.chain import Chain, plan
    r = plan(Chain(demand=240), coupled=True)

Weeks t = 0..51 of one year. The factory makes x_t <= cap per week at crew-hours h per unit, plus a premium for output
above `base` per week; robots (robots=True) raise the cap by `robot_peak` and cut h by `robot_save`, at a fixed annual
cost. Coupled: output goes to a quay (inventory I_t <= quay), installs y_t happen only in campaign weeks up to the
weekly installation capacity, and every turbine not installed by the end of the year costs `late`. Alone (coupled=False):
the factory meets a flat weekly demand, shortfalls cost `late`. The objective is total cost in crew-hour equivalents.
All parameters ILLUSTRATIVE. Needs scipy.
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

W = 52


@dataclass
class Chain:
    demand: float = 240.0          # per year
    cap: float = 5.5               # units per week at full working time
    base: float = 4.6              # units per week without premium hours
    h: float = 520.0               # crew-hours per unit
    premium: float = 0.3           # extra share of h for units above base
    quay: float = 120.0            # units the quay can hold
    season: tuple = (14, 40)       # campaign weeks [start, end)
    install_cap: float = 12.0      # installs per campaign week
    late: float = 5000.0           # per turbine not installed / not delivered in time
    robots: bool = False
    robot_peak: float = 0.03
    robot_save: float = 0.03
    robot_cost: float = 8000.0


def plan(c: Chain, coupled: bool = True):
    cap = c.cap * (1 + c.robot_peak if c.robots else 1)
    h = c.h * (1 - c.robot_save if c.robots else 1)
    # variables: x_base[t], x_prem[t], I[t], y[t], short (scalar)
    nb, npm, ni, ny = W, W, W, W
    N = nb + npm + ni + ny + 1
    cost = np.zeros(N)
    cost[:nb] = h
    cost[nb:nb + npm] = h * (1 + c.premium)
    cost[-1] = c.late
    A_eq, b_eq, A_ub, b_ub = [], [], [], []
    bounds = [(0, c.base)] * nb + [(0, max(cap - c.base, 0))] * npm + [(0, c.quay)] * ni + [(0, 0)] * ny + [(0, None)]
    if coupled:
        s0, s1 = c.season
        for t in range(s0, s1):
            bounds[nb + npm + ni + t] = (0, c.install_cap)
        for t in range(W):                          # I_t = I_{t-1} + x_t - y_t
            row = np.zeros(N)
            row[t] = row[nb + t] = 1.0
            row[nb + npm + ni + t] = -1.0
            row[nb + npm + t] = -1.0
            if t > 0:
                row[nb + npm + t - 1] = 1.0
            A_eq.append(row)
            b_eq.append(0.0)
        row = np.zeros(N)                           # installs + short >= demand
        row[nb + npm + ni:nb + npm + ni + ny] = -1.0
        row[-1] = -1.0
        A_ub.append(row)
        b_ub.append(-c.demand)
    else:
        weekly = c.demand / W
        for t in range(W):                          # cumulative output >= cumulative demand - short
            row = np.zeros(N)
            row[:t + 1] = -1.0
            row[nb:nb + t + 1] = -1.0
            row[-1] = -1.0
            A_ub.append(row)
            b_ub.append(-weekly * (t + 1))
    res = linprog(cost, A_ub=np.array(A_ub), b_ub=np.array(b_ub), A_eq=np.array(A_eq) if A_eq else None,
                  b_eq=np.array(b_eq) if b_eq else None, bounds=bounds, method="highs")
    assert res.status == 0, res.message
    x = res.x[:nb] + res.x[nb:nb + npm]
    total = res.fun + (c.robot_cost if c.robots else 0.0)
    return dict(cost=total, output=float(x.sum()), short=float(res.x[-1]), premium_units=float(res.x[nb:nb + npm].sum()),
                weekly=x.tolist())


def ranks(c: Chain):
    """robots or not, alone and coupled: which is cheaper in each condition (2 % margin, else a tie)"""
    out = {}
    for cond in (False, True):
        a = plan(Chain(**{**c.__dict__, "robots": True}), cond)["cost"]
        b = plan(Chain(**{**c.__dict__, "robots": False}), cond)["cost"]
        d = (a - b) / min(a, b)
        out["coupled" if cond else "alone"] = "robots" if d <= -0.02 else "no robots" if d >= 0.02 else "tie"
    return out
