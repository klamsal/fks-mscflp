"""ks_ws.py — KS-CG-WS: Kernel Search with feasibility-preserving stage transitions.

Identical to KS-CG in every structural detail (γ-threshold arc selection,
adaptive kernel add/drop, bucket expansion, iterative restart) but augments
every arc set with the arcs used by the current incumbent before passing to
the next subproblem.

This implements Fix 3 alone: by including all incumbent arcs in the next
stage's edge set, the incumbent is guaranteed feasible in the next restricted
MILP (Proposition 2), making it a valid warm start by construction.

Arc selection (γ-threshold) is unchanged from KS — Fix 2 is NOT applied.
This allows the component-wise comparison:
  KS-CG  vs  KS-CG-WS  →  measures Fix 3 alone
  KS-CG-WS  vs  FKS-CG  →  measures Fix 2 alone
"""

from __future__ import annotations

import math
import time
from typing import Dict, List, Set

from instance import CflpInstance, Facility, Edge
from lp_solver import LpResult
from ks import KsResult, _kernel_edges, _bucket_edges
from fks import _solve_milp


def _incumbent_arcs(best_x: Dict[Edge, float], threshold: float = 0.5) -> Set[Edge]:
    """Return the set of arcs used by the current incumbent."""
    return {e for e, v in best_x.items() if v > threshold}


def run_ks_ws(
    inst:      CflpInstance,
    lp:        LpResult,
    *,
    milp_time: float = 300.0,
    n_buckets: int   = 3,
    p_remove:  int   = 2,
) -> KsResult:
    """Run KS-CG-WS on a pre-solved CG LP.

    Uses γ-threshold arc selection (same as KS-CG) but augments every arc set
    with incumbent arcs before each stage transition, guaranteeing the incumbent
    is feasible in the next restricted MILP by construction.
    """
    t0 = time.perf_counter()

    kernel = sorted(lp.kernel(), key=lambda j: -lp.demand_served.get(j, 0.0))
    lbuck  = max(1, len(kernel))

    j0_sorted = sorted(lp.J0, key=lambda j: lp.rc_y.get(j, float("inf")))
    buckets   = [j0_sorted[h * lbuck:(h + 1) * lbuck]
                 for h in range(math.ceil(len(j0_sorted) / lbuck))]

    rc_vals = [v for (j, i), v in lp.rc_x.items() if j in set(kernel) and v > 1e-9]
    gamma   = sum(rc_vals) / len(rc_vals) if rc_vals else 0.0

    edges               = _kernel_edges(inst, lp, kernel, gamma)
    best_obj            = float("inf")
    best_y:  Dict[Facility, float] = {}
    best_x:  Dict[Edge,     float] = {}
    n_milps             = 0
    n_restarts          = 0
    n_buckets_used      = 0
    initial_kernel_size = len(kernel)
    absent: Dict[Facility, int] = {j: 0 for j in kernel}

    def _augment(arc_set: Set[Edge]) -> Set[Edge]:
        """Add all incumbent arcs to arc_set (Fix 3: feasibility-preserving)."""
        if best_x:
            return arc_set | _incumbent_arcs(best_x)
        return arc_set

    def _run_pass(nb_bar: int) -> int:
        nonlocal kernel, edges, best_obj, best_y, best_x, n_milps, absent, n_buckets_used

        # Kernel MILP — augment arc set with incumbent arcs, then warm start
        kernel_edges = _augment(edges)
        _, obj, y_sol, x_sol = _solve_milp(
            inst, set(kernel), kernel_edges,
            cutoff     = best_obj if best_obj < float("inf") else None,
            forcing    = None,
            time_limit = milp_time,
            warm_y     = best_y if best_y else None,
            warm_x     = best_x if best_x else None,
        )
        n_milps += 1
        if obj < best_obj:
            best_obj, best_y, best_x = obj, y_sol, x_sol

        last_improving = -1
        for h, bucket in enumerate(buckets[:nb_bar]):
            # Build γ-threshold bucket arc set, then augment with incumbent arcs
            b_edges = _bucket_edges(lp, bucket, edges, gamma)
            b_edges = _augment(b_edges)

            _, obj, y_sol, x_sol = _solve_milp(
                inst, set(kernel + bucket), b_edges,
                cutoff     = best_obj if best_obj < float("inf") else None,
                forcing    = bucket,
                time_limit = milp_time,
                warm_y     = best_y if best_y else None,
                warm_x     = best_x if best_x else None,
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
