"""loaders.py — Instance loaders for MSCFLP benchmark families.

Supported formats:
  .plc   Avella et al. (2009) — Test Bed A, B, and TBED1
  .txt   OR-Library (Beasley 1990) — cap* instances

Expected directory layout (relative to this file):
  ../benchmarks/testbed_a/   — Test Bed A (.plc, up to 2000×4400)
  ../benchmarks/testbed_b/   — Test Bed B (.plc, same families)
  ../benchmarks/orlib/       — OR-Library cap* (.txt)
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from instance import CflpInstance, Facility, Client, Edge

BENCH  = Path(__file__).parent.parent / "benchmarks"
AVELLA = BENCH / "avella"


# ── .plc loader (Avella Test Bed A/B and TBED1) ──────────────────

def load_plc(path: Path, name: str = "") -> CflpInstance:
    """Load an Avella .plc instance.

    Token order:
      n_cli  n_fac
      d_0 ... d_{n_cli-1}               client demands
      q_0 ... q_{n_fac-1}               facility capacities
      f_0 ... f_{n_fac-1}               facility fixed costs
      c_{0,0} ... c_{0,n_cli-1}         unit shipping costs, facility 0
      ...
      c_{n_fac-1,0} ... c_{n_fac-1,n_cli-1}
    """
    tokens = path.read_text().split()
    it = iter(tokens)

    def _f() -> float: return float(next(it))
    def _i() -> int:   return int(float(next(it)))

    n_cli = _i();  n_fac = _i()

    demands:    Dict[Client,   float] = {i: _f() for i in range(n_cli)}
    capacities: Dict[Facility, float] = {j: _f() for j in range(n_fac)}
    open_costs: Dict[Facility, float] = {j: _f() for j in range(n_fac)}
    ship_costs: Dict[Edge,     float] = {
        (j, i): _f() for j in range(n_fac) for i in range(n_cli)
    }

    return CflpInstance(
        facilities = list(range(n_fac)),
        clients    = list(range(n_cli)),
        capacities = capacities,
        open_costs = open_costs,
        demands    = demands,
        ship_costs = ship_costs,
        name       = name or path.stem,
    )


# ── OR-Library loader ─────────────────────────────────────────────

def load_orlib(path: Path, name: str = "") -> CflpInstance:
    """Load an OR-Library CFLP instance.

    Token order:
      n_fac  n_cli
      q_0  f_0  ...  q_{n_fac-1}  f_{n_fac-1}
      d_0 ... d_{n_cli-1}
      For each client i: d_i  total_cost_{0,i} ... total_cost_{n_fac-1,i}

    c_{ji} = total_cost_{j,i} / d_i  (converted to unit cost).
    """
    tokens = path.read_text().split()
    it = iter(tokens)

    def _f() -> float: return float(next(it))
    def _i() -> int:   return int(float(next(it)))

    n_fac = _i();  n_cli = _i()

    capacities: Dict[Facility, float] = {}
    open_costs: Dict[Facility, float] = {}
    for j in range(n_fac):
        capacities[j] = _f();  open_costs[j] = _f()

    demands:    Dict[Client, float] = {}
    ship_costs: Dict[Edge,   float] = {}
    for i in range(n_cli):
        d = _f();  demands[i] = d
        for j in range(n_fac):
            total = _f()
            ship_costs[(j, i)] = total / d if d > 0 else total

    return CflpInstance(
        facilities = list(range(n_fac)),
        clients    = list(range(n_cli)),
        capacities = capacities,
        open_costs = open_costs,
        demands    = demands,
        ship_costs = ship_costs,
        name       = name or path.stem,
    )


# ── Path finders ──────────────────────────────────────────────────

def find_instance(testbed: str, name: str) -> Path:
    """Find a Test Bed A or B .plc file by instance name."""
    folder = BENCH / f"testbed_{testbed.lower()}"
    matches = list(folder.rglob(f"{name}.plc"))
    if not matches:
        raise FileNotFoundError(f"Instance '{name}' not found in {folder}")
    return matches[0]


def find_orlib(name: str) -> Path:
    """Find an OR-Library instance file by name."""
    folder = BENCH / "orlib"
    for suffix in ["", ".txt", ".dat"]:
        p = folder / f"{name}{suffix}"
        if p.exists():
            return p
    raise FileNotFoundError(f"OR-Library instance '{name}' not found in {folder}")


# ── Instance name lists ───────────────────────────────────────────

def list_testbed(testbed: str, size: str = "") -> List[str]:
    """Return sorted instance names for a test bed, optionally filtered by size.

    size: e.g. '1000-1000', '800-4400' — matched as substring of instance name.
    """
    def _num(s: str) -> tuple:
        parts = s.rsplit("-", 1)
        try: return (parts[0], int(parts[1]))
        except (IndexError, ValueError): return (s, 0)

    folder = BENCH / f"testbed_{testbed.lower()}"
    names = sorted((f.stem for f in folder.rglob("*.plc")), key=_num)
    if size:
        names = [n for n in names if size in n]
    return names


def list_orlib() -> List[str]:
    """Return all OR-Library instance names found on disk."""
    folder = BENCH / "orlib"
    return sorted(f.stem for f in folder.glob("*.txt"))


# ── TBED1 (Avella et al. 2009) ────────────────────────────────────

_TBED1_FAMILIES = {
    "i300":     "data_set_300",
    "i500":     "data_set_500",
    "i700":     "data_set_700",
    "i1000":    "data_set_1000",
    "i3001500": "data_set_300_1500",
}


def find_tbed1(name: str) -> Path:
    """Find a TBED1 .plc file by instance name, e.g. 'i300_1', 'i1000_15'."""
    if name.startswith("i3001500"):
        p = AVELLA / "data_set_300_1500" / f"{name}.plc"
        if p.exists():
            return p
    for prefix, folder in _TBED1_FAMILIES.items():
        if name.startswith(prefix):
            p = AVELLA / folder / f"{name}.plc"
            if p.exists():
                return p
    raise FileNotFoundError(f"TBED1 instance '{name}' not found under {AVELLA}")


def load_tbed1_optima() -> Dict[str, float]:
    """Load TBED1 best-known values → {name: z*}.

    For proven-optimal instances, z* = the proven optimum.
    For others, z* = best known upper bound (best feasible solution in the literature).
    """
    p = AVELLA / "TBED1_Solution_Values.txt"
    result: Dict[str, float] = {}
    for line in p.read_text().splitlines():
        if "&" not in line or "hline" in line or "Name" in line:
            continue
        parts = [x.strip().rstrip("\\") for x in line.split("&")]
        if len(parts) < 5:
            continue
        name   = parts[0].strip()
        lb_raw = parts[3].strip()
        ub_raw = parts[4].strip()
        proven = "(*)" in lb_raw
        try:
            lb = float(lb_raw.replace("(*)", "").strip())
            ub = float(ub_raw.strip())
            result[name] = lb if proven else ub
        except ValueError:
            pass
    return result


def list_tbed1(family: str = "all") -> List[str]:
    """Return TBED1 instance names.

    family: 'i300', 'i500', 'i700', 'i1000', 'i3001500', or 'all'.
    """
    selected = (
        list(_TBED1_FAMILIES.items()) if family == "all"
        else [(family, _TBED1_FAMILIES[family])]
    )
    def _num(s: str) -> int:
        parts = s.replace("-", "_").split("_")
        try: return int(parts[-1])
        except ValueError: return 0

    names: List[str] = []
    for _, folder in selected:
        d = AVELLA / folder
        if d.exists():
            names += sorted(
                (f.stem for f in d.iterdir() if f.suffix == ".plc"),
                key=_num
            )
    return names
