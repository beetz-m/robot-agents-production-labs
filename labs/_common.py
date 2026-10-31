import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
HOURS_PER_YEAR = 5250          # register.yaml: 250 days x 21 h (ILLUSTRATIVE)
SEEDS = range(1, 7)


def per_year(th_per_h):
    return th_per_h * HOURS_PER_YEAR


def save(fig, name):
    p = OUT / name
    fig.savefig(p, dpi=130, bbox_inches="tight")
    print("figure:", p)
