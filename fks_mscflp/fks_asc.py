"""fks_asc.py — FKS with ascending arc expansion (column-generation style).

Instead of the top-down funnel (k=50→20→10), starts with the tightest
arc set (k=10), solves it well (small MILP, tight LP bound), then expands:
k=10 → k=20 → k=50.

Rationale: the smallest MILP is easiest to solve to near-optimality.  Each
expansion is a deliberate "price and add" step: do any of the newly admitted
arcs improve the incumbent?  If a stage is solved to optimality and finds no
improvement, expansion terminates early — the current solution is proven
optimal within the enlarged arc set.

Differences from run_fks:
  - Stages in ascending k order (default: 10 → 20 → 50)
  - MIPFocus=0 for all stages (Stage 1 is small enough to solve properly)
  - Bucket arc selection always uses max_k (widest set) so LP-closed
    facilities have a fair chance regardless of current stage k
  - Early termination: if a stage (s > 0) is solved to optimality with no
    improvement, further expansion cannot help → stop
"""

from __future__ import annotations

import math
import time
from typing import Dict, List, Optional, Set, Tuple

from instance import CflpInstance, Facility, Client, Edge
from lp_solver import LpResult
from fks import FksResult, _solve_milp, _flat_k_edges

Stage = Tuple[float, float]   # (k, time_limit_seconds)

DEFAULT_ASC_STAGES: List[Stage] = [(10.0, 300.0), (20.0, 300.0), (50.0, 300.0)]

_BIG = 1e18


def run_fks_asc(
    inst:      CflpInstance,
    lp:        LpResult,
    *,
    stages:    List[Stage] = DEFAULT_ASC_STAGES,
    n_buckets: int         = 3,
) -> FksResult:
    """Run ascending FKS on a pre-solved LP.

    Parameters
    ----------
    inst      : MSCFLP instance
    lp        : LP relaxation result (solved externally)
    stages    : list of (k, time_limit) tuples in ascending k order
    n_buckets : maximum bucket batches per stage (stages 2+ only)
    """
    t0 = time.perf_counter()

    kernel    = lp.kernel()
    lbuck     = max(1, len(kernel))
    j0_sorted = sorted(lp.J0, key=lambda j: lp.rc_y.get(j, float("inf")))

    # Bucket facilities always get the widest arc set so they have a fair shot
    max_k = int(max(s[0] for s in stages))

    best_obj  = float("inf")
    best_y:   Dict[Facility, float] = {}
    best_x:   Dict[Edge,     float] = {}
    prev_x:   Dict[Edge,     float] = {}
    n_milps        = 0
    stage_gaps:    List[float] = []
    stage_times:   List[float] = []
    stage_n_edges: List[int]   = []
    stage_n_milps: List[int]   = []
    stage_objs:    List[float] = []

    for s, (mult, t_lim) in enumerate(stages):
        st = time.perf_counter()
        k  = int(mult)

        edges = _flat_k_edges(inst, lp, kernel, k,
                              prev_x=prev_x if s > 0 and prev_x else None)

        # All stages use MIPFocus=0: Stage 1 is small enough to solve well
        status, obj, y_sol, x_sol = _solve_milp(
            inst, kernel, edges,
            cutoff     = best_obj if best_obj < float("inf") else None,
            forcing    = None,
            time_limit = t_lim,
            warm_y     = best_y if best_y else None,
            warm_x     = best_x if best_x else None,
            mip_focus  = 0,
        )
        n_milps  += 1
        s_milps   = 1
        stage_improved = False

        if obj < best_obj:
            best_obj, best_y, best_x, prev_x = obj, y_sol, x_sol, x_sol
            stage_improved = True

        # Early termination check 1: kernel MILP found no improvement and was
        # conclusive (Optimal or Cutoff) — skip buckets entirely and stop expanding.
        # "Cutoff" means no solution better than incumbent exists in this arc set,
        # which is stronger evidence than "Optimal" (which may have found a worse sol).
        if s > 0 and status in ("Optimal", "Cutoff") and not stage_improved:
            gap = (best_obj - lp.objective) / lp.objective * 100 \
                  if best_obj < float("inf") and lp.objective > 0 else float("nan")
            stage_gaps.append(gap)
            stage_times.append(time.perf_counter() - st)
            stage_n_edges.append(len(edges))
            stage_n_milps.append(s_milps)
            stage_objs.append(best_obj)
            break

        # Bucket expansion (stages 2+ only — Stage 1 establishes the incumbent)
        if s > 0:
            available_j0 = [j for j in j0_sorted if j not in kernel]
            for h in range(n_buckets):
                bucket = available_j0[h * lbuck:(h + 1) * lbuck]
                if not bucket:
                    break
                b_facs  = kernel | set(bucket)
                b_edges = _flat_k_edges(inst, lp, b_facs, max_k,
                                        prev_x=best_x if best_x else None)
                _, obj, y_sol, x_sol = _solve_milp(
                    inst, b_facs, b_edges,
                    cutoff     = best_obj if best_obj < float("inf") else None,
                    forcing    = bucket,
                    time_limit = t_lim,
                    warm_y     = best_y if best_y else None,
                    warm_x     = best_x if best_x else None,
                )
                n_milps += 1
                s_milps += 1
                if obj < best_obj:
                    best_obj, best_y, best_x, prev_x = obj, y_sol, x_sol, x_sol
                    stage_improved = True
                    opened = {j for j in bucket if y_sol.get(j, 0.0) > 0.5}
                    if opened:
                        kernel.update(opened)
                        lbuck = max(1, len(kernel))

        gap = (best_obj - lp.objective) / lp.objective * 100 \
              if best_obj < float("inf") and lp.objective > 0 else float("nan")
        stage_gaps.append(gap)
        stage_times.append(time.perf_counter() - st)
        stage_n_edges.append(len(edges))
        stage_n_milps.append(s_milps)
        stage_objs.append(best_obj)

        # Early termination check 2: full stage (kernel + all buckets) found no
        # improvement — adding more arcs in the next stage is unlikely to help.
        if s > 0 and not stage_improved:
            break

    final_gap = (best_obj - lp.objective) / lp.objective * 100 \
                if best_obj < float("inf") and lp.objective > 0 else float("nan")

    last_k      = int(stages[len(stage_gaps) - 1][0])
    final_edges = _flat_k_edges(inst, lp, kernel, last_k,
                                prev_x=best_x if best_x else None)

    return FksResult(
        obj           = best_obj,
        gap_lp        = final_gap,
        lp_obj        = lp.objective,
        n_milps       = n_milps,
        n_edges       = len(final_edges),
        total_time    = time.perf_counter() - t0,
        stage_gaps    = stage_gaps,
        stage_times   = stage_times,
        y             = best_y,
        x             = best_x,
        stage_n_edges = stage_n_edges,
        stage_n_milps = stage_n_milps,
        stage_objs    = stage_objs,
    )
