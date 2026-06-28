"""lp_solver.py — LP relaxation solver for the MSCFLP.

Solves the LP relaxation using Gurobi with the strong (VUB) formulation.
Dual simplex is used to obtain reduced costs directly.

Two solvers are provided:
  solve_lp    — full 4M-variable LP (exact, slow for large instances)
  solve_lp_cg — column generation (starts small, adds negative-rc columns iteratively)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Set

import numpy as np
import gurobipy as gp
from gurobipy import GRB

from instance import CflpInstance, Facility, Client, Edge

_ENV = gp.Env()
_ENV.setParam("OutputFlag",    0)
_ENV.setParam("LogToConsole",  0)
_ENV.setParam("LogFile",       "")

def enable_verbose() -> None:
    _ENV.setParam("OutputFlag",   1)
    _ENV.setParam("LogToConsole", 1)


@dataclass
class LpResult:
    objective:      float
    y:              Dict[Facility, float]   # y_j^LP ∈ [0, 1]
    x:              Dict[Edge,     float]   # x_{ji}^LP (absolute flow)
    rc_y:           Dict[Facility, float]   # reduced cost of y_j
    rc_x:           Dict[Edge,     float]   # reduced cost of x_{ji}
    J1:             Set[Facility]           # LP-open  (y_j ≈ 1)
    Jfrac:          Set[Facility]           # LP-fractional
    J0:             Set[Facility]           # LP-closed (y_j ≈ 0)
    demand_served:  Dict[Facility, float]   # Σ_i x_{ji}^LP per facility
    solve_time:     float = 0.0
    cg_iters:       int   = 0              # CG: number of LP solves (0 = full LP)
    cg_active_cols: int   = 0              # CG: active (j,i) columns at termination

    def kernel(self) -> Set[Facility]:
        """J1 ∪ Jfrac — facilities with positive LP value."""
        return self.J1 | self.Jfrac


def solve_lp(inst: CflpInstance) -> LpResult:
    """Solve the full LP relaxation of the MSCFLP instance.

    Returns an LpResult with primal values, reduced costs, and the
    LP basis partition (J1, Jfrac, J0).
    """
    t0 = time.perf_counter()

    m = gp.Model(env=_ENV)
    m.setParam("Method", 1)     # dual simplex → reduced costs available directly

    y = {j: m.addVar(lb=0.0, ub=1.0, obj=inst.open_costs[j]) for j in inst.facilities}
    x = {(j, i): m.addVar(lb=0.0, ub=inst.demands[i], obj=inst.ship_costs[(j, i)])
         for j in inst.facilities for i in inst.clients}

    m.ModelSense = GRB.MINIMIZE

    for i in inst.clients:
        m.addConstr(gp.quicksum(x[(j, i)] for j in inst.facilities) == inst.demands[i])

    for j in inst.facilities:
        m.addConstr(
            gp.quicksum(x[(j, i)] for i in inst.clients) <= inst.capacities[j] * y[j]
        )
        for i in inst.clients:
            m.addConstr(x[(j, i)] <= inst.demands[i] * y[j])

    m.optimize()

    if m.Status != GRB.OPTIMAL:
        raise RuntimeError(f"LP solve failed with status {m.Status}")

    EPS = 1e-6
    y_val = {j: max(0.0, y[j].X) for j in inst.facilities}
    x_val = {(j, i): max(0.0, x[(j, i)].X) for j in inst.facilities for i in inst.clients}

    J1    = {j for j in inst.facilities if y_val[j] >= 1.0 - EPS}
    J0    = {j for j in inst.facilities if y_val[j] <= EPS}
    Jfrac = set(inst.facilities) - J1 - J0

    demand_served = {
        j: sum(x_val[(j, i)] for i in inst.clients) for j in inst.facilities
    }

    result = LpResult(
        objective     = m.ObjVal,
        y             = y_val,
        x             = x_val,
        rc_y          = {j: y[j].RC for j in inst.facilities},
        rc_x          = {(j, i): x[(j, i)].RC for j in inst.facilities for i in inst.clients},
        J1            = J1,
        Jfrac         = Jfrac,
        J0            = J0,
        demand_served = demand_served,
        solve_time    = time.perf_counter() - t0,
    )
    m.dispose()
    return result


def solve_lp_cg(inst: CflpInstance, k_init: int = 30, tol: float = 1e-6) -> LpResult:
    """LP relaxation via column generation.

    Starts with k_init cheapest facilities per client.  Each iteration solves
    the restricted master problem (RMP), then prices ALL inactive columns with
    rc_{ji} = c_{ji} - pi_i - alpha_j (vectorised via numpy).  Columns with
    rc < 0 are added and the RMP is re-solved.  Terminates when no negative-rc
    column exists, at which point the RMP solution is LP-optimal for the full
    problem.

    Returns the same LpResult as solve_lp, including rc_x for every (j,i).
    Non-active (j,i) use the analytical formula; active ones use Gurobi's RC
    (which correctly accounts for VUB duals).
    """
    t0   = time.perf_counter()
    facs = list(inst.facilities)
    clis = list(inst.clients)
    J, I = len(facs), len(clis)
    fac_idx = {j: k for k, j in enumerate(facs)}
    cli_idx = {i: k for k, i in enumerate(clis)}

    # Shipping cost matrix [J x I]
    C = np.array(
        [[inst.ship_costs[(j, i)] for i in clis] for j in facs], dtype=np.float64
    )

    m = gp.Model(env=_ENV)
    m.setParam("Method", 1)
    m.ModelSense = GRB.MINIMIZE

    y = {j: m.addVar(lb=0.0, ub=1.0, obj=inst.open_costs[j]) for j in facs}

    # Demand constraints — initially 0 = d_i, corrected by artificials below
    dem = {i: m.addConstr(gp.LinExpr() == inst.demands[i]) for i in clis}

    # Capacity constraints — start as -Q_j y_j ≤ 0; x columns add +1 terms
    cap = {j: m.addConstr(-inst.capacities[j] * y[j] <= 0) for j in facs}

    # Artificial variables (obj = 1e8) ensure RMP is feasible from the start
    art = {}
    for i in clis:
        art[i] = m.addVar(
            lb=0.0, ub=inst.demands[i], obj=1e8,
            column=gp.Column([1.0], [dem[i]])
        )

    active = np.zeros((J, I), dtype=bool)
    x:   dict = {}
    vub: dict = {}

    def _add_col(j_idx: int, i_idx: int) -> None:
        j, i = facs[j_idx], clis[i_idx]
        col = gp.Column([1.0, 1.0], [dem[i], cap[j]])
        xji = m.addVar(lb=0.0, ub=inst.demands[i],
                       obj=inst.ship_costs[(j, i)], column=col)
        x[(j, i)]   = xji
        vub[(j, i)] = m.addConstr(xji <= inst.demands[i] * y[j])
        active[j_idx, i_idx] = True

    # Warm start: k_init cheapest facilities per client
    for i_idx in range(I):
        for j_idx in np.argsort(C[:, i_idx])[:k_init]:
            _add_col(int(j_idx), i_idx)

    m.update()

    total_demand = sum(inst.demands[i] for i in clis)
    n_iter  = 0
    n_solves = 0

    while True:
        m.optimize()
        n_solves += 1
        if m.Status != GRB.OPTIMAL:
            raise RuntimeError(f"CG RMP failed: status={m.Status}")

        art_sum = sum(art[i].X for i in clis)
        pi    = np.array([dem[i].Pi for i in clis])
        alpha = np.array([cap[j].Pi for j in facs])

        # Pricing: vectorised over all J×I pairs
        rc = C - pi[np.newaxis, :] - alpha[:, np.newaxis]
        new_mask = (~active) & (rc < -tol)
        n_new = int(new_mask.sum())

        if n_new == 0:
            if art_sum > tol * total_demand:
                raise RuntimeError(f"LP infeasible (art_sum={art_sum:.4f})")
            break

        for j_idx, i_idx in zip(*np.where(new_mask)):
            _add_col(int(j_idx), int(i_idx))
        m.update()
        n_iter += 1

    # ── Read all Gurobi values before dispose ─────────────────────────────────
    obj_val  = m.ObjVal
    y_vals   = {j: max(0.0, y[j].X)  for j in facs}
    x_rc_map = {k: v.RC               for k, v in x.items()}
    x_vals   = {k: max(0.0, v.X)      for k, v in x.items() if v.X > 1e-9}
    rc_y_d   = {j: y[j].RC            for j in facs}
    pi_d     = {i: dem[i].Pi          for i in clis}
    alpha_d  = {j: cap[j].Pi          for j in facs}

    m.dispose()

    # ── Full rc_x: Gurobi RC for active cols, analytical for the rest ─────────
    pi_arr    = np.array([pi_d[i]    for i in clis])
    alpha_arr = np.array([alpha_d[j] for j in facs])
    rc_ana    = C - pi_arr[np.newaxis, :] - alpha_arr[:, np.newaxis]

    rc_x: Dict[Edge, float] = {}
    for j_idx, j in enumerate(facs):
        for i_idx, i in enumerate(clis):
            key = (j, i)
            rc_x[key] = (x_rc_map[key] if active[j_idx, i_idx]
                         else float(rc_ana[j_idx, i_idx]))

    EPS   = 1e-6
    J1    = {j for j in facs if y_vals[j] >= 1.0 - EPS}
    J0    = {j for j in facs if y_vals[j] <= EPS}
    Jfrac = set(facs) - J1 - J0

    demand_served = {
        j: sum(x_vals.get((j, i), 0.0) for i in clis) for j in facs
    }

    return LpResult(
        objective     = obj_val,
        y             = y_vals,
        x             = x_vals,
        rc_y          = rc_y_d,
        rc_x          = rc_x,
        J1            = J1,
        Jfrac         = Jfrac,
        J0            = J0,
        demand_served = demand_served,
        solve_time    = time.perf_counter() - t0,
        cg_iters      = n_solves,
        cg_active_cols= int(active.sum()),
    )
