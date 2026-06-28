"""ks.py — Kernel Search for the MSCFLP (Guastaroba & Speranza 2012).

Implements the Iterative Kernel Search (I-KS) algorithm from:

    Guastaroba, G. & Speranza, M.G. (2012).
    Kernel search for the capacitated facility location problem.
    Journal of Heuristics, 18(6), 877–917.

Algorithm summary:
  1. Solve LP relaxation (provided externally).
  2. Kernel K = LP-open ∪ LP-fractional facilities.
  3. Select edges E(K): all (j,i) with reduced cost rc_{ji} ≤ γ,
     where γ = mean reduced cost over LP-positive kernel edges.
  4. Solve restricted MILP(K, E(K)).
  5. Bucket expansion: add batches of LP-closed facilities (sorted by
     rc_y ascending), each batch forced to open ≥1 facility.
  6. Iterative restart: if any bucket improved the solution, restart
     with a reduced bucket range.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import gurobipy as gp
from gurobipy import GRB

from instance import CflpInstance, Facility, Client, Edge
from lp_solver import LpResult, _ENV


@dataclass
class KsResult:
    obj:            float                  # best feasible objective
    gap_lp:         float                  # (obj - lp_obj) / lp_obj × 100 (%)
    lp_obj:         float                  # LP lower bound
    n_milps:        int                    # total MILP subproblems solved
    n_edges:        int                    # edge set size at termination
    total_time:     float                  # wall-clock seconds (excl. LP)
    y:              Dict[Facility, float]  # best y solution
    x:              Dict[Edge,     float]  # best x solution
    kernel_size:    int   = 0             # |K| at start
    gamma:          float = 0.0           # γ threshold used for edge selection
    n_restarts:     int   = 0             # number of restarts after the first pass
    n_buckets_used: int   = 0             # total bucket MILPs solved


# ── Restricted MILP solver ────────────────────────────────────────

def _solve_milp(
    inst:         CflpInstance,
    facs:         List[Facility],
    edges:        Set[Edge],
    cutoff:       Optional[float],
    forcing:      Optional[List[Facility]],
    time_limit:   float,
) -> Tuple[str, float, Dict[Facility, float], Dict[Edge, float]]:
    """Solve one restricted MILP subproblem.

    Returns (status, obj, y_vals, x_vals).
    status ∈ {'Optimal', 'Feasible', 'Infeasible', 'Cutoff'}.
    """
    fac_set = set(facs)
    cli_facs: Dict[Client,   List[Facility]] = defaultdict(list)
    fac_clis: Dict[Facility, List[Client]]   = defaultdict(list)
    for (j, i) in edges:
        if j in fac_set:
            cli_facs[i].append(j)
            fac_clis[j].append(i)

    # Every client must have at least one facility in the edge set
    for i in inst.clients:
        if not cli_facs[i]:
            best = min(facs, key=lambda j: inst.ship_costs.get((j, i), 1e18))
            cli_facs[i].append(best)
            fac_clis[best].append(i)

    m = gp.Model(env=_ENV)
    m.setParam("TimeLimit", time_limit)
    m.setParam("MIPGap",    1e-6)

    y = {j: m.addVar(vtype=GRB.BINARY, obj=inst.open_costs[j]) for j in facs}
    x = {(j, i): m.addVar(lb=0.0, ub=inst.demands[i], obj=inst.ship_costs[(j, i)])
         for (j, i) in edges if j in fac_set}

    m.ModelSense = GRB.MINIMIZE

    for i in inst.clients:
        m.addConstr(
            gp.quicksum(x[(j, i)] for j in cli_facs[i] if (j, i) in x) == inst.demands[i]
        )
    for j in facs:
        clis = [i for i in fac_clis[j] if (j, i) in x]
        if clis:
            m.addConstr(gp.quicksum(x[(j, i)] for i in clis) <= inst.capacities[j] * y[j])

    if cutoff is not None and not math.isnan(cutoff):
        m.addConstr(
            gp.quicksum(inst.open_costs[j] * y[j] for j in facs)
            + gp.quicksum(inst.ship_costs[(j, i)] * x[(j, i)] for (j, i) in x)
            <= cutoff - 1e-4
        )

    if forcing:
        m.addConstr(gp.quicksum(y[j] for j in forcing if j in y) >= 1)

    m.optimize()

    if m.SolCount == 0:
        status = "Infeasible" if m.Status == GRB.INFEASIBLE else "Cutoff"
        m.dispose()
        return status, float("nan"), {}, {}

    status = "Optimal" if m.Status == GRB.OPTIMAL else "Feasible"
    obj    = m.ObjVal
    y_out  = {j: round(y[j].X) for j in facs}
    x_out  = {(j, i): v for (j, i), v in
              ((e, x[e].X) for e in x) if v > 1e-9}
    m.dispose()
    return status, obj, y_out, x_out


# ── Edge selection (γ-threshold) ─────────────────────────────────

def _kernel_edges(
    inst:    CflpInstance,
    lp:      LpResult,
    kernel:  List[Facility],
    gamma:   float,
) -> Set[Edge]:
    """Select edges for kernel facilities using the γ reduced-cost threshold."""
    kset  = set(kernel)
    edges: Set[Edge] = {
        (j, i)
        for (j, i), rc in lp.rc_x.items()
        if j in kset and rc <= gamma
    }
    # Guarantee every client has at least one edge
    covered = {i for (_, i) in edges}
    for i in inst.clients:
        if i not in covered:
            best = min(kernel, key=lambda j: lp.rc_x.get((j, i), 0.0))
            edges.add((best, i))
    return edges


def _bucket_edges(
    lp:     LpResult,
    bucket: List[Facility],
    base:   Set[Edge],
    gamma:  float,
) -> Set[Edge]:
    """Add edges for bucket facilities (same γ threshold)."""
    bset      = set(bucket)
    new_edges = set(base)
    new_edges |= {
        (j, i) for (j, i), rc in lp.rc_x.items()
        if j in bset and rc <= gamma
    }
    return new_edges


# ── Main KS driver ────────────────────────────────────────────────

def run_ks(
    inst:        CflpInstance,
    lp:          LpResult,
    *,
    milp_time:   float = 300.0,
    n_buckets:   int   = 3,
    p_remove:    int   = 2,
) -> KsResult:
    """Run Iterative Kernel Search (I-KS) on a pre-solved LP.

    Parameters
    ----------
    inst       : MSCFLP instance
    lp         : LP relaxation result (solved externally — not repeated here)
    milp_time  : Gurobi time limit per MILP subproblem (seconds)
    n_buckets  : maximum buckets to test per pass
    p_remove   : consecutive absences before a facility is removed from kernel
    """
    t0 = time.perf_counter()

    kernel = sorted(lp.kernel(), key=lambda j: -lp.demand_served.get(j, 0.0))
    lbuck  = max(1, len(kernel))

    j0_sorted = sorted(lp.J0, key=lambda j: lp.rc_y.get(j, float("inf")))
    buckets   = [j0_sorted[h * lbuck:(h + 1) * lbuck]
                 for h in range(math.ceil(len(j0_sorted) / lbuck))]

    rc_vals = [v for (j, i), v in lp.rc_x.items() if j in set(kernel) and v > 1e-9]
    gamma   = sum(rc_vals) / len(rc_vals) if rc_vals else 0.0

    edges         = _kernel_edges(inst, lp, kernel, gamma)
    best_obj      = float("inf")
    best_y: Dict[Facility, float] = {}
    best_x: Dict[Edge,     float] = {}
    n_milps       = 0
    n_restarts    = 0
    n_buckets_used = 0
    initial_kernel_size = len(kernel)
    absent: Dict[Facility, int] = {j: 0 for j in kernel}

    def _run_pass(nb_bar: int) -> int:
        nonlocal kernel, edges, best_obj, best_y, best_x, n_milps, absent, n_buckets_used

        # Kernel MILP
        status, obj, y_sol, x_sol = _solve_milp(
            inst, kernel, edges,
            cutoff=best_obj if best_obj < float("inf") else None,
            forcing=None, time_limit=milp_time,
        )
        n_milps += 1
        if obj < best_obj:
            best_obj, best_y, best_x = obj, y_sol, x_sol

        last_improving = -1
        for h, bucket in enumerate(buckets[:nb_bar]):
            b_edges = _bucket_edges(lp, bucket, edges, gamma)
            status, obj, y_sol, x_sol = _solve_milp(
                inst, kernel + bucket, b_edges,
                cutoff=best_obj if best_obj < float("inf") else None,
                forcing=bucket, time_limit=milp_time,
            )
            n_milps += 1

            if obj < best_obj - 1e-6:
                best_obj, best_y, best_x = obj, y_sol, x_sol
                opened = [j for j in bucket if y_sol.get(j, 0) > 0.5]
                kernel = kernel + opened
                edges  = set(b_edges)
                absent.update({j: 0 for j in opened})
                last_improving = h
            n_buckets_used += 1

            if y_sol:
                for j in list(kernel):
                    absent[j] = 0 if y_sol.get(j, 0) > 0.5 else absent.get(j, 0) + 1
                to_drop = {j for j in kernel if absent.get(j, 0) >= p_remove}
                if to_drop:
                    kernel = [j for j in kernel if j not in to_drop]
                    edges  = {e for e in edges if e[0] not in to_drop}
                    for j in to_drop:
                        absent.pop(j, None)

        return last_improving

    last = _run_pass(min(n_buckets, len(buckets)))
    while last >= 0:
        nb = last
        if nb == 0:
            break
        absent     = {j: 0 for j in kernel}
        n_restarts += 1
        last       = _run_pass(nb)

    gap = (best_obj - lp.objective) / lp.objective * 100 \
          if best_obj < float("inf") and lp.objective > 0 else float("nan")

    return KsResult(
        obj             = best_obj,
        gap_lp          = gap,
        lp_obj          = lp.objective,
        n_milps         = n_milps,
        n_edges         = len(edges),
        total_time      = time.perf_counter() - t0,
        y               = best_y,
        x               = best_x,
        kernel_size     = initial_kernel_size,
        gamma           = gamma,
        n_restarts      = n_restarts,
        n_buckets_used  = n_buckets_used,
    )
