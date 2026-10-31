"""Robot competence profiles (textbook Ch. 4): from a profile to relief and crew time.

A profile: p (success per attempt), k_max (attempts before a person does the task by hand), A (availability per
station visit), rho (share of failed attempts that need a person), r_h (that person's hours per intervention),
recovery ('crew': the station's crew recovers, its time adds to the station; 'operator': someone else does).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    p: float = 1.0
    k_max: int = 3
    A: float = 1.0
    rho: float = 1.0
    r_h: float = 0.0
    recovery: str = "crew"


IDEAL = Profile()


def expected(pr: Profile):
    """(share of a task's relief realised, intervention hours per task, of which on the station) - Ch. 4, Eq. relief"""
    q = 1.0 - pr.p
    realised = pr.A * (1.0 - q ** pr.k_max)
    interv = pr.A * pr.rho * pr.r_h * sum(q ** i for i in range(1, pr.k_max + 1))
    return realised, interv, interv if pr.recovery == "crew" else 0.0


def realise(task_hours, pr: Profile, rng):
    """one station visit: (relief hours, intervention hours) for a list of supply tasks, drawn with rng"""
    if not task_hours:
        return 0.0, 0.0
    if rng.random() >= pr.A:
        return 0.0, 0.0
    relief = interv = 0.0
    for h in task_hours:
        for _ in range(pr.k_max):
            if rng.random() < pr.p:
                relief += h
                break
            if rng.random() < pr.rho:
                interv += pr.r_h
    return relief, interv
