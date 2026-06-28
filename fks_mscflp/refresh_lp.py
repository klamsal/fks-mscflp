"""refresh_lp.py — Transportation LP slave T(y^k) for post-integer dual refresh.

Given a fixed binary allocation y^k, solves:

    min  Σ_{j: y^k_j=1} Σ_i  c_{ji} x_{ji}
    s.t. Σ_{j: y^k_j=1}      x_{ji}  = d_i     ∀i   [dual: π^k_i]
                         Σ_i  x_{ji} ≤ q_j      ∀j: y^k_j=1   [dual: α^k_j]
                              x_{ji} ∈ [0, d_i]

Solved via column generation: start with the cheapest open facility per
client, price all remaining arcs with rc = c_{ji} − π_i − α_j, add negatives,
repeat.  Typically converges in 2-3 iterations; far cheaper than admitting
all |open| × |I| arcs upfront.

CS Separation Lemma: for closed facilities j (y^k_j = 0), the capacity
constraint is structurally absent from T(y^k), so α^k_j = 0 in every dual
optimal solution.  The arc signal c_{ji} − π^k_i is therefore a pure
customer-scarcity signal, free of fractional capacity noise.

Returns (pi, alpha, solve_time), or None if the LP is infeasible.
  pi[i]    — demand dual for every client i
  alpha[j] — capacity dual for open facilities; 0.0 for closed (by CS)
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

import numpy as np
import gurobipy as gp
from gurobipy import GRB

from instance import CflpInstance, Client, Facility
from lp_solver import _ENV

TlpResult = Tuple[Dict[Client, float], Dict[Facility, float], float]


def solve_refresh_lp(
    inst:    CflpInstance,
    y_fixed: Dict[Facility, float],
    tol:     float = 1e-6,
) -> Optional[TlpResult]:
    """Solve T(y^k) via column generation; return π^k, α^k, solve time."""
    t0 = time.perf_counter()

    open_facs: List[Facility] = [j for j in inst.facilities if y_fixed.get(j, 0.0) > 0.5]
    if not open_facs:
        return None

    clis = list(inst.clients)
    J, I = len(open_facs), len(clis)
    fac_idx = {j: k for k, j in enumerate(open_facs)}
    cli_idx = {i: k for k, i in enumerate(clis)}

    # Cost matrix [J × I] for open facilities only
    C = np.array(
        [[inst.ship_costs[(j, i)] for i in clis] for j in open_facs],
        dtype=np.float64,
    )

    m = gp.Model(env=_ENV)
    m.setParam("Method", 1)   # dual simplex
    m.ModelSense = GRB.MINIMIZE

    # Demand constraints (initially empty LHS; arcs added as columns)
    dem = {i: m.addConstr(gp.LinExpr() == inst.demands[i]) for i in clis}

    # Capacity constraints for every open facility
    cap = {j: m.addConstr(gp.LinExpr() <= inst.capacities[j]) for j in open_facs}

    # Artificial variables ensure initial feasibility
    art = {
        i: m.addVar(lb=0.0, ub=inst.demands[i], obj=1e8,
                    column=gp.Column([1.0], [dem[i]]))
        for i in clis
    }

    active = np.zeros((J, I), dtype=bool)
    x: dict = {}

    def _add_col(j_idx: int, i_idx: int) -> None:
        j, i = open_facs[j_idx], clis[i_idx]
        col = gp.Column([1.0, 1.0], [dem[i], cap[j]])
        x[(j, i)] = m.addVar(lb=0.0, ub=inst.demands[i],
                              obj=inst.ship_costs[(j, i)], column=col)
        active[j_idx, i_idx] = True

    # Warm start: cheapest open facility per client
    for i_idx in range(I):
        best_j = int(np.argmin(C[:, i_idx]))
        _add_col(best_j, i_idx)

    m.update()

    total_demand = sum(inst.demands[i] for i in clis)

    while True:
        m.optimize()
        if m.Status != GRB.OPTIMAL:
            m.dispose()
            return None

        art_sum = sum(art[i].X for i in clis)
        pi_arr    = np.array([dem[i].Pi for i in clis])
        alpha_arr = np.array([cap[j].Pi for j in open_facs])

        rc = C - pi_arr[np.newaxis, :] - alpha_arr[:, np.newaxis]
        new_mask = (~active) & (rc < -tol)
        if new_mask.sum() == 0:
            if art_sum > tol * total_demand:
                m.dispose()
                return None   # infeasible
            break

        for j_idx, i_idx in zip(*np.where(new_mask)):
            _add_col(int(j_idx), int(i_idx))
        m.update()

    pi    = {clis[k]: float(dem[clis[k]].Pi) for k in range(I)}
    alpha = {open_facs[k]: float(cap[open_facs[k]].Pi) for k in range(J)}

    m.dispose()
    return pi, alpha, time.perf_counter() - t0
