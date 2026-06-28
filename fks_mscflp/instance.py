"""instance.py — Data types for the Multi-Source Capacitated Facility Location Problem.

MSCFLP formulation (Avella et al. 2009 / Guastaroba & Speranza 2012):

    min   Σ_j f_j y_j  +  Σ_j Σ_i c_{ji} x_{ji}

    s.t.  Σ_j x_{ji}  = d_i          ∀i   (demand satisfaction)
          Σ_i x_{ji} ≤ q_j y_j       ∀j   (facility capacity)
          x_{ji}      ≤ d_i y_j      ∀j,i  (variable upper bounds)
          x_{ji}      ≥ 0,  y_j ∈ {0,1}

x_{ji} is the flow (in demand units) from facility j to client i.
c_{ji} is the unit shipping cost; the objective contribution is c_{ji} * x_{ji}.
The VUB constraints are essential: they tighten the LP relaxation substantially,
making the LP bound a reliable predictor of the integer optimum.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

Facility = int
Client   = int
Edge     = Tuple[Facility, Client]


@dataclass
class CflpInstance:
    facilities:  List[Facility]
    clients:     List[Client]
    capacities:  Dict[Facility, float]   # q_j
    open_costs:  Dict[Facility, float]   # f_j
    demands:     Dict[Client,   float]   # d_i
    ship_costs:  Dict[Edge,     float]   # c_{ji}  (unit cost)
    name:        str = ""

    @property
    def n_fac(self) -> int:
        return len(self.facilities)

    @property
    def n_cli(self) -> int:
        return len(self.clients)

    @property
    def capacity_ratio(self) -> float:
        return sum(self.capacities.values()) / sum(self.demands.values())
