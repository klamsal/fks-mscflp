"""fks_dr.py — Funnel Kernel Search with Dual Refresh (FKS-DR).

Same three-stage structure as FKS (fks.py) with one addition: after each
stage MILP, the transportation LP slave T(y^k) is solved to obtain refreshed
customer duals π^k.  Stage k+1 arc selection uses c_{ji} − π^k_i − α^k_j
instead of the stale c_{ji} − π*_i − α*_j from the original LP.

CS Separation Lemma (Gal & Nedoma 1972; Fischetti et al. 2017 KKT (38)-(42)):
  For closed facilities j with y^k_j = 0, α^k_j = 0 by LP complementary
  slackness.  The signal c_{ji} − π^k_i is free of fractional capacity noise
  and reflects actual customer-assignment cost under the current integer y^k.

Stage 1 arc selection is identical to FKS (original LP reduced costs).
Stages 2 and 3 use duals refreshed after Stage 1 and Stage 2 respectively.

fks.py is NOT modified.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from instance import CflpInstance, Client, Edge, Facility
from lp_solver import LpResult
from fks import DEFAULT_STAGES, FksResult, Stage, _BIG, _solve_milp
from refresh_lp import solve_refresh_lp

_Duals = Tuple[Optional[Dict[Client, float]], Optional[Dict[Facility, float]]]


@dataclass
class FksDrResult(FksResult):
    """FksResult extended with per-transition transport LP solve times."""
    transport_lp_times: List[float] = field(default_factory=list)


def _edges_dr(
    inst:    CflpInstance,
    lp:      LpResult,
    facs:    Set[Facility],
    k:       int,
    pi:      Optional[Dict[Client,   float]],
    alpha:   Optional[Dict[Facility, float]],
    prev_x:  Optional[Dict[Edge, float]] = None,
) -> Set[Edge]:
    """Select top-k facilities per client by reduced cost, with optional dual refresh.

    When pi/alpha are None (Stage 1, no prior MILP), falls back to lp.rc_x.
    Incumbent arcs from prev_x are always preserved (feasibility guarantee).
    """
    fl    = list(facs)
    edges: Set[Edge] = set()

    for i in inst.clients:
        if prev_x:
            for j in fl:
                if prev_x.get((j, i), 0.0) > 1e-9:
                    edges.add((j, i))

        if pi is not None:
            # Refreshed signal: c_{ji} − π^k_i − α^k_j (α^k_j = 0 for closed by CS)
            def rc(j: Facility) -> float:
                return inst.ship_costs.get((j, i), _BIG) - pi[i] - (alpha.get(j, 0.0) if alpha else 0.0)
            ranked = sorted(fl, key=rc)
        else:
            ranked = sorted(fl, key=lambda j: lp.rc_x.get((j, i), _BIG))

        for j in ranked[:k]:
            edges.add((j, i))

    return edges


def run_fks_dr(
    inst:      CflpInstance,
    lp:        LpResult,
    *,
    stages:    List[Stage] = DEFAULT_STAGES,
    n_buckets: int         = 3,
) -> FksDrResult:
    """Funnel Kernel Search with post-integer dual refresh.

    After each stage MILP completes (kernel + buckets), T(best_y) is solved
    and the resulting π^k, α^k are used for the next stage's arc selection.
    Stage 1 uses the original LP duals unchanged.
    """
    t0 = time.perf_counter()

    kernel    = lp.kernel()
    lbuck     = max(1, len(kernel))
    j0_sorted = sorted(lp.J0, key=lambda j: lp.rc_y.get(j, float("inf")))
    bucket_k  = int(stages[0][0])   # Stage-1 k reused for bucket arc selection

    best_obj = float("inf")
    best_y:  Dict[Facility, float] = {}
    best_x:  Dict[Edge,     float] = {}
    prev_x:  Dict[Edge,     float] = {}

    n_milps          = 0
    stage_gaps:      List[float] = []
    stage_times:     List[float] = []
    stage_n_edges:   List[int]   = []
    stage_n_milps:   List[int]   = []
    stage_objs:      List[float] = []
    transport_times: List[float] = []

    current_pi:    Optional[Dict[Client,   float]] = None
    current_alpha: Optional[Dict[Facility, float]] = None

    for s, (mult, t_lim) in enumerate(stages):
        st    = time.perf_counter()
        k_int = int(mult)

        edges = _edges_dr(
            inst, lp, kernel, k_int,
            pi=current_pi, alpha=current_alpha,
            prev_x=prev_x if s > 0 and prev_x else None,
        )

        mip_focus     = 1 if s == 0 else 0
        cutoff_kernel = (best_obj if best_obj < float("inf") else None) if s == 0 else None
        cutoff_bucket = best_obj if best_obj < float("inf") else None

        _, obj, y_sol, x_sol = _solve_milp(
            inst, kernel, edges, cutoff_kernel,
            forcing=None, time_limit=t_lim,
            warm_y=best_y if best_y else None,
            warm_x=best_x if best_x else None,
            mip_focus=mip_focus,
        )
        n_milps += 1
        s_milps  = 1
        if obj < best_obj:
            best_obj, best_y, best_x, prev_x = obj, y_sol, x_sol, x_sol

        if s > 0:
            available_j0 = [j for j in j0_sorted if j not in kernel]
            for h in range(n_buckets):
                bucket = available_j0[h * lbuck:(h + 1) * lbuck]
                if not bucket:
                    break
                b_facs  = kernel | set(bucket)
                b_edges = _edges_dr(
                    inst, lp, b_facs, bucket_k,
                    pi=current_pi, alpha=current_alpha,
                    prev_x=best_x if best_x else None,
                )
                _, obj, y_sol, x_sol = _solve_milp(
                    inst, b_facs, b_edges, cutoff_bucket,
                    forcing=bucket, time_limit=t_lim,
                    warm_y=best_y if best_y else None,
                    warm_x=best_x if best_x else None,
                )
                n_milps += 1
                s_milps += 1
                if obj < best_obj:
                    best_obj, best_y, best_x, prev_x = obj, y_sol, x_sol, x_sol
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

        # Dual refresh after each stage except the last
        if s < len(stages) - 1 and best_y:
            tlp = solve_refresh_lp(inst, best_y)
            if tlp is not None:
                current_pi, current_alpha, tlp_time = tlp
                transport_times.append(round(tlp_time, 4))
            else:
                transport_times.append(0.0)

    final_gap = (best_obj - lp.objective) / lp.objective * 100 \
                if best_obj < float("inf") and lp.objective > 0 else float("nan")

    final_edges = _edges_dr(
        inst, lp, kernel, int(stages[-1][0]),
        pi=current_pi, alpha=current_alpha,
        prev_x=best_x if best_x else None,
    )

    return FksDrResult(
        obj                = best_obj,
        gap_lp             = final_gap,
        lp_obj             = lp.objective,
        n_milps            = n_milps,
        n_edges            = len(final_edges),
        total_time         = time.perf_counter() - t0,
        stage_gaps         = stage_gaps,
        stage_times        = stage_times,
        y                  = best_y,
        x                  = best_x,
        stage_n_edges      = stage_n_edges,
        stage_n_milps      = stage_n_milps,
        stage_objs         = stage_objs,
        transport_lp_times = transport_times,
    )
