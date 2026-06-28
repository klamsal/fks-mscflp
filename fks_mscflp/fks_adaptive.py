"""fks_adaptive.py -- Adaptive Benders-refreshed Funnel Kernel Search.

This module is intentionally a sidecar to fks.py.  The original FKS
implementation is not modified; this variant keeps the same staged restricted-MILP
structure and imports the existing MILP builder.

The only new idea is at the stage transition:

1. Tight stages use the original LP reduced costs, exactly as FKS does.
2. After an incumbent integer facility set y^k exists, solve the transportation
   LP slave T(y^k).
3. If the incumbent looks loose, use the resulting customer duals pi^k to rank
   closed-facility challengers and the arcs attached to them.
4. If the incumbent looks tight, continue as an ordinary arc-refinement funnel.

This keeps the FKS "soul" alive: stages, incumbent-arc preservation, restricted
MILPs, improvement cutoffs, and bucket/challenger forcing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

from instance import CflpInstance, Client, Edge, Facility
from lp_solver import LpResult
from fks import DEFAULT_STAGES, FksResult, Stage, _BIG, _flat_k_edges, _solve_milp
from refresh_lp import solve_refresh_lp


@dataclass
class AdaptiveFksResult(FksResult):
    """FksResult plus diagnostics for adaptive stage transitions."""

    transport_lp_times: List[float] = field(default_factory=list)
    stage_modes: List[str] = field(default_factory=list)
    stage_open_counts: List[int] = field(default_factory=list)
    stage_capacity_slacks: List[float] = field(default_factory=list)
    stage_challengers: List[int] = field(default_factory=list)


def _safe_gap(obj: float, lp_obj: float) -> float:
    if obj < float("inf") and lp_obj > 0:
        return (obj - lp_obj) / lp_obj * 100.0
    return float("nan")


def _capacity_slack(inst: CflpInstance, y: Dict[Facility, float]) -> float:
    """Return incumbent capacity slack as fraction of total demand."""

    total_demand = sum(inst.demands[i] for i in inst.clients)
    if total_demand <= 0:
        return 0.0
    open_capacity = sum(
        inst.capacities[j] for j in inst.facilities if y.get(j, 0.0) > 0.5
    )
    return (open_capacity - total_demand) / total_demand


def _looks_loose(
    inst: CflpInstance,
    y: Dict[Facility, float],
    kernel: Set[Facility],
    *,
    loose_slack: float,
    loose_open_ratio: float,
) -> bool:
    """Classify the incumbent regime using Avella-style capacity structure.

    Loose instances tend to need only a small open set and have substantial
    excess capacity once that set is opened.  In that regime, facility replacement
    is usually the main search problem; narrower arcs alone do not help enough.
    """

    if not y:
        return False
    open_count = sum(1 for value in y.values() if value > 0.5)
    if not kernel:
        return False
    open_ratio = open_count / max(1, len(kernel))
    return open_ratio <= loose_open_ratio and _capacity_slack(inst, y) >= loose_slack


def _refreshed_rc(
    inst: CflpInstance,
    j: Facility,
    i: Client,
    pi: Optional[Dict[Client, float]],
    alpha: Optional[Dict[Facility, float]],
) -> float:
    """Reduced-cost-like loose-stage signal.

    With no refreshed dual, callers should use the original LP reduced costs.
    With refreshed duals, closed facilities have alpha_j = 0 by construction,
    while open facilities use the alpha_j returned by T(y^k).
    """

    if pi is None:
        return _BIG
    return inst.ship_costs.get((j, i), _BIG) - pi[i] - (
        alpha.get(j, 0.0) if alpha else 0.0
    )


def _refreshed_flat_k_edges(
    inst: CflpInstance,
    lp: LpResult,
    facs: Set[Facility],
    k: int,
    pi: Optional[Dict[Client, float]],
    alpha: Optional[Dict[Facility, float]],
    prev_x: Optional[Dict[Edge, float]] = None,
) -> Set[Edge]:
    """Top-k edge selection, falling back to ordinary FKS when pi is None."""

    if pi is None:
        return _flat_k_edges(inst, lp, facs, k, prev_x=prev_x)

    fl = list(facs)
    edges: Set[Edge] = set()
    for i in inst.clients:
        if prev_x:
            for j in fl:
                if prev_x.get((j, i), 0.0) > 1e-9:
                    edges.add((j, i))

        ranked = sorted(fl, key=lambda j: _refreshed_rc(inst, j, i, pi, alpha))
        for j in ranked[:k]:
            edges.add((j, i))

    return edges


def _benders_facility_score(
    inst: CflpInstance,
    j: Facility,
    pi: Optional[Dict[Client, float]],
) -> float:
    """Facility challenger score f_j + fractional-KP(c_ji - pi_i).

    The optional assignment z is filled only along negative reduced-cost-like arcs:
    positive terms would not be used by an opening challenger.  Lower is better.
    """

    if pi is None:
        return 0.0

    remaining = inst.capacities[j]
    score = inst.open_costs[j]
    unit_terms = sorted(
        (inst.ship_costs.get((j, i), _BIG) - pi[i], inst.demands[i])
        for i in inst.clients
    )

    for unit_delta, demand in unit_terms:
        if remaining <= 1e-9 or unit_delta >= 0.0:
            break
        flow = min(remaining, demand)
        score += unit_delta * flow
        remaining -= flow

    return score


def _rank_candidates(
    inst: CflpInstance,
    lp: LpResult,
    kernel: Set[Facility],
    pi: Optional[Dict[Client, float]],
) -> List[Facility]:
    """Rank nonkernel candidates by refreshed Benders score when available."""

    pool = [j for j in lp.J0 if j not in kernel]
    if not pool:
        pool = [j for j in inst.facilities if j not in kernel]

    if pi is None:
        return sorted(pool, key=lambda j: lp.rc_y.get(j, float("inf")))

    return sorted(pool, key=lambda j: _benders_facility_score(inst, j, pi))


def _select_challengers(
    ranked: Sequence[Facility],
    incumbent_y: Dict[Facility, float],
    *,
    challenger_factor: float,
    min_challengers: int,
    max_challengers: Optional[int],
) -> List[Facility]:
    open_count = sum(1 for value in incumbent_y.values() if value > 0.5)
    target = max(min_challengers, int(round(challenger_factor * max(1, open_count))))
    if max_challengers is not None:
        target = min(target, max_challengers)
    return list(ranked[:target])


def run_adaptive_fks(
    inst: CflpInstance,
    lp: LpResult,
    *,
    stages: List[Stage] = DEFAULT_STAGES,
    n_buckets: int = 3,
    loose_slack: float = 0.25,
    loose_open_ratio: float = 0.35,
    challenger_factor: float = 2.0,
    min_challengers: int = 8,
    max_challengers: Optional[int] = None,
    bucket_k_policy: str = "stage",
) -> AdaptiveFksResult:
    """Run Adaptive Benders-refreshed FKS.

    Parameters mirror run_fks where possible.  The new controls are intentionally
    simple and transparent:

    loose_slack/open_ratio
        Decide whether a post-incumbent stage is a loose facility-search case.
    challenger_factor/min/max
        Size of the Benders-ranked challenger set in loose mode.
    bucket_k_policy
        "stage" uses the current stage k for bucket arcs; "wide" uses Stage-1 k.
    """

    if stages[0][0] <= 1.0:
        raise ValueError("run_adaptive_fks currently supports flat-k stages only")
    if bucket_k_policy not in {"stage", "wide"}:
        raise ValueError("bucket_k_policy must be 'stage' or 'wide'")

    t0 = time.perf_counter()

    kernel = set(lp.kernel())
    lbuck = max(1, len(kernel))
    stage1_k = int(stages[0][0])

    best_obj = float("inf")
    best_y: Dict[Facility, float] = {}
    best_x: Dict[Edge, float] = {}
    prev_x: Dict[Edge, float] = {}

    current_pi: Optional[Dict[Client, float]] = None
    current_alpha: Optional[Dict[Facility, float]] = None

    n_milps = 0
    stage_gaps: List[float] = []
    stage_times: List[float] = []
    stage_n_edges: List[int] = []
    stage_n_milps: List[int] = []
    stage_objs: List[float] = []
    transport_times: List[float] = []
    stage_modes: List[str] = []
    stage_open_counts: List[int] = []
    stage_capacity_slacks: List[float] = []
    stage_challengers: List[int] = []

    for s, (mult, t_lim) in enumerate(stages):
        st = time.perf_counter()
        k_int = max(1, int(mult))

        mode = "root" if s == 0 else (
            "loose" if _looks_loose(
                inst,
                best_y,
                kernel,
                loose_slack=loose_slack,
                loose_open_ratio=loose_open_ratio,
            ) else "tight"
        )
        use_refresh = mode == "loose"
        edges = _refreshed_flat_k_edges(
            inst,
            lp,
            kernel,
            k_int,
            current_pi if use_refresh else None,
            current_alpha if use_refresh else None,
            prev_x=prev_x if s > 0 and prev_x else None,
        )

        mip_focus = 1 if s == 0 else 0
        cutoff_kernel = (best_obj if best_obj < float("inf") else None) if s == 0 else None
        cutoff_bucket = best_obj if best_obj < float("inf") else None

        _, obj, y_sol, x_sol = _solve_milp(
            inst,
            kernel,
            edges,
            cutoff_kernel,
            forcing=None,
            time_limit=t_lim,
            warm_y=best_y if best_y else None,
            warm_x=best_x if best_x else None,
            mip_focus=mip_focus,
        )
        n_milps += 1
        s_milps = 1
        s_challengers = 0

        if obj < best_obj:
            best_obj, best_y, best_x, prev_x = obj, y_sol, x_sol, x_sol

        if s > 0:
            mode = "loose" if _looks_loose(
                inst,
                best_y,
                kernel,
                loose_slack=loose_slack,
                loose_open_ratio=loose_open_ratio,
            ) else "tight"
            use_refresh = mode == "loose"
            ranked = _rank_candidates(inst, lp, kernel, current_pi if use_refresh else None)

            if mode == "loose":
                challengers = _select_challengers(
                    ranked,
                    best_y,
                    challenger_factor=challenger_factor,
                    min_challengers=min_challengers,
                    max_challengers=max_challengers,
                )
                s_challengers = len(challengers)

                if challengers:
                    b_facs = kernel | set(challengers)
                    b_edges = _refreshed_flat_k_edges(
                        inst,
                        lp,
                        b_facs,
                        k_int,
                        current_pi,
                        current_alpha,
                        prev_x=best_x if best_x else None,
                    )
                    _, obj, y_sol, x_sol = _solve_milp(
                        inst,
                        b_facs,
                        b_edges,
                        cutoff_bucket,
                        forcing=challengers,
                        time_limit=t_lim,
                        warm_y=best_y if best_y else None,
                        warm_x=best_x if best_x else None,
                    )
                    n_milps += 1
                    s_milps += 1

                    if obj < best_obj:
                        best_obj, best_y, best_x, prev_x = obj, y_sol, x_sol, x_sol
                        opened = {j for j in challengers if y_sol.get(j, 0.0) > 0.5}
                        if opened:
                            kernel.update(opened)
                            lbuck = max(1, len(kernel))

            else:
                bucket_k = stage1_k if bucket_k_policy == "wide" else k_int
                available = [j for j in ranked if j not in kernel]
                for h in range(n_buckets):
                    bucket = available[h * lbuck:(h + 1) * lbuck]
                    if not bucket:
                        break

                    b_facs = kernel | set(bucket)
                    b_edges = _refreshed_flat_k_edges(
                        inst,
                        lp,
                        b_facs,
                        bucket_k,
                        None,
                        None,
                        prev_x=best_x if best_x else None,
                    )
                    _, obj, y_sol, x_sol = _solve_milp(
                        inst,
                        b_facs,
                        b_edges,
                        cutoff_bucket,
                        forcing=bucket,
                        time_limit=t_lim,
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

        stage_gaps.append(_safe_gap(best_obj, lp.objective))
        stage_times.append(time.perf_counter() - st)
        stage_n_edges.append(len(edges))
        stage_n_milps.append(s_milps)
        stage_objs.append(best_obj)
        stage_modes.append(mode)
        stage_open_counts.append(sum(1 for value in best_y.values() if value > 0.5))
        stage_capacity_slacks.append(_capacity_slack(inst, best_y) if best_y else float("nan"))
        stage_challengers.append(s_challengers)

        if (
            s < len(stages) - 1
            and best_y
            and _looks_loose(
                inst,
                best_y,
                kernel,
                loose_slack=loose_slack,
                loose_open_ratio=loose_open_ratio,
            )
        ):
            tlp = solve_refresh_lp(inst, best_y)
            if tlp is not None:
                current_pi, current_alpha, tlp_time = tlp
                transport_times.append(round(tlp_time, 4))
            else:
                transport_times.append(0.0)
        elif s < len(stages) - 1:
            current_pi, current_alpha = None, None
            transport_times.append(0.0)

    final_use_refresh = _looks_loose(
        inst,
        best_y,
        kernel,
        loose_slack=loose_slack,
        loose_open_ratio=loose_open_ratio,
    )
    final_edges = _refreshed_flat_k_edges(
        inst,
        lp,
        kernel,
        int(stages[-1][0]),
        current_pi if final_use_refresh else None,
        current_alpha if final_use_refresh else None,
        prev_x=best_x if best_x else None,
    )

    return AdaptiveFksResult(
        obj=best_obj,
        gap_lp=_safe_gap(best_obj, lp.objective),
        lp_obj=lp.objective,
        n_milps=n_milps,
        n_edges=len(final_edges),
        total_time=time.perf_counter() - t0,
        stage_gaps=stage_gaps,
        stage_times=stage_times,
        y=best_y,
        x=best_x,
        stage_n_edges=stage_n_edges,
        stage_n_milps=stage_n_milps,
        stage_objs=stage_objs,
        transport_lp_times=transport_times,
        stage_modes=stage_modes,
        stage_open_counts=stage_open_counts,
        stage_capacity_slacks=stage_capacity_slacks,
        stage_challengers=stage_challengers,
    )
