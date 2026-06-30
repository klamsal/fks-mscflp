"""fks.py — Funnel Kernel Search (FKS) for the MSCFLP.

FKS is a multi-stage matheuristic that extends Kernel Search (G&S 2012) with
a client-centric edge selection criterion and inter-stage warm starting.

Edge selection — two modes (auto-detected from stage multiplier):
  Flat-k  (mult > 1, treated as integer k):
    For each client i, select the top-k facilities by LP reduced cost.
    Produces a predictable base edge set of size k×|I|; later stages also
    preserve incumbent arcs that fall outside this base.
  γ_i threshold  (mult ≤ 1.0):
    For each client i, γ_i = mean reduced cost over LP-active edges in kernel.
    Stage s uses γ_i × mult as threshold.  Adapts to LP concentration.

Warm starting: inter-stage incumbent arcs
  Stages 2+ always preserve all arcs used in the previous integer solution,
  and bucket facilities opened by an improving incumbent are promoted into the
  kernel.  The previous y and x values are injected as a MIP start, so Gurobi
  begins from a known feasible point whenever the incumbent is available in the
  next restricted MILP.

Default stages (flat-k):
  Stage 1  k=50, 300s — wide net, MIPFocus=1
  Stage 2  k=20, 300s — narrower + incumbent warm start
  Stage 3  k=10, 300s — tightest  + incumbent warm start

Bucket expansion (stages 2+, identical structure to G&S 2012):
  LP-closed facilities are tested in batches.  For flat-k mode the Stage-1 k
  is reused so bucket facilities have a fair chance of entering the edge set.
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

_BIG = 1e18

Stage = Tuple[float, float]   # (k_or_gamma_mult, time_limit_seconds)
# mult > 1  → flat-k mode  (e.g. 50, 20, 10)
# mult ≤ 1  → γ_i threshold mode (e.g. 1.0, 0.5, 0.25)

DEFAULT_STAGES: List[Stage] = [(50.0, 300.0), (20.0, 300.0), (10.0, 300.0)]


@dataclass
class FksResult:
    obj:            float
    gap_lp:         float
    lp_obj:         float
    n_milps:        int
    n_edges:        int
    total_time:     float
    stage_gaps:     List[float]
    stage_times:    List[float]
    y:              Dict[Facility, float]
    x:              Dict[Edge,     float]
    stage_n_edges:  List[int]   = None   # edge count at start of each stage
    stage_n_milps:  List[int]   = None   # MILPs solved in each stage (kernel + buckets)
    stage_objs:     List[float] = None   # best obj after each stage


# ── MILP solver with warm-start support ──────────────────────────────────────

def _solve_milp(
    inst:       CflpInstance,
    facs:       Set[Facility],
    edges:      Set[Edge],
    cutoff:     Optional[float],
    forcing:    Optional[List[Facility]],
    time_limit: float,
    warm_y:     Optional[Dict[Facility, float]] = None,
    warm_x:     Optional[Dict[Edge, float]] = None,
    mip_focus:  int = 0,
) -> Tuple[str, float, Dict[Facility, float], Dict[Edge, float]]:
    cli_facs: Dict[Client,   List[Facility]] = defaultdict(list)
    fac_clis: Dict[Facility, List[Client]]   = defaultdict(list)
    for (j, i) in edges:
        if j in facs:
            cli_facs[i].append(j)
            fac_clis[j].append(i)

    for i in inst.clients:
        if not cli_facs[i]:
            best = min(facs, key=lambda j: inst.ship_costs.get((j, i), _BIG))
            cli_facs[i].append(best)
            fac_clis[best].append(i)

    m = gp.Model(env=_ENV)
    m.setParam("TimeLimit", time_limit)
    m.setParam("MIPGap",    1e-6)
    if mip_focus:
        m.setParam("MIPFocus", mip_focus)

    y = {j: m.addVar(vtype=GRB.BINARY, obj=inst.open_costs[j]) for j in facs}
    x = {(j, i): m.addVar(lb=0.0, ub=inst.demands[i], obj=inst.ship_costs[(j, i)])
         for (j, i) in edges if j in facs}

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

    if warm_y:
        for j in facs:
            y[j].Start = float(warm_y.get(j, 0.0))
    if warm_x:
        for edge, var in x.items():
            var.Start = float(warm_x.get(edge, 0.0))

    m.optimize()

    if m.SolCount == 0:
        status = "Infeasible" if m.Status == GRB.INFEASIBLE else "Cutoff"
        m.dispose()
        return status, float("nan"), {}, {}

    status = "Optimal" if m.Status == GRB.OPTIMAL else "Feasible"
    obj    = m.ObjVal
    y_out  = {j: round(y[j].X) for j in facs if y[j].X > 0.5}
    x_out  = {(j, i): x[(j, i)].X for (j, i) in x if x[(j, i)].X > 1e-9}
    m.dispose()
    return status, obj, y_out, x_out


# ── Flat-k edge selection ─────────────────────────────────────────────────────

def _flat_k_edges(
    inst:   CflpInstance,
    lp:     LpResult,
    facs:   Set[Facility],
    k:      int,
    prev_x: Optional[Dict[Edge, float]] = None,
) -> Set[Edge]:
    """Select top-k facilities per client by LP reduced cost, plus incumbent arcs.

    Incumbent arcs from prev_x are always included (feasibility-preservation
    guarantee), and the top-k by rc are added from facs.  This means stages 2+
    begin from a proven feasible point without any feasibility-search overhead.
    """
    fl    = list(facs)
    edges: Set[Edge] = set()
    for i in inst.clients:
        # Preserve all incumbent arcs whose facilities are available.
        if prev_x:
            for j in fl:
                if prev_x.get((j, i), 0.0) > 1e-9:
                    edges.add((j, i))
        # Add top-k by reduced cost from the full facility set for this stage
        ranked = sorted(fl, key=lambda j: lp.rc_x.get((j, i), _BIG))
        for j in ranked[:k]:
            edges.add((j, i))
    return edges


# ── Per-client γ_i and threshold edge selection ───────────────────────────────

def _per_client_gamma(
    inst:   CflpInstance,
    lp:     LpResult,
    kernel: Set[Facility],
) -> Dict[Client, float]:
    """γ_i = mean reduced cost over LP-active edges for client i in the kernel."""
    gammas: Dict[Client, float] = {}
    for i in inst.clients:
        rc_vals = [lp.rc_x[(j, i)] for j in kernel if lp.x.get((j, i), 0.0) > 1e-9]
        gammas[i] = sum(rc_vals) / len(rc_vals) if rc_vals else 0.0
    return gammas


def _threshold_edges(
    inst:    CflpInstance,
    lp:      LpResult,
    facs:    Set[Facility],
    gammas:  Dict[Client, float],
    mult:    float,
    prev_x:  Optional[Dict[Edge, float]] = None,
) -> Set[Edge]:
    """Build edge set using per-client γ_i * mult threshold.

    For each client i:
      1. Preserve all arcs used in prev_x (incumbent arcs guarantee feasibility).
      2. Add all (j,i) where j ∈ facs and rc_{ji} ≤ γ_i * mult.
      3. Safety: if client still has no edge, add the single lowest-rc arc.
    """
    fl     = list(facs)
    edges: Set[Edge] = set()
    for i in inst.clients:
        incumbent: Set[Facility] = set()
        if prev_x:
            incumbent = {j for j in fl if prev_x.get((j, i), 0.0) > 1e-9}
        edges |= {(j, i) for j in incumbent}

        threshold = gammas[i] * mult
        edges |= {
            (j, i) for j in fl
            if j not in incumbent and lp.rc_x.get((j, i), _BIG) <= threshold
        }

        if not any((j, i) in edges for j in fl):
            best = min(fl, key=lambda j: lp.rc_x.get((j, i), _BIG))
            edges.add((best, i))
    return edges


# ── Main FKS driver ───────────────────────────────────────────────────────────

def run_fks(
    inst:      CflpInstance,
    lp:        LpResult,
    *,
    stages:    List[Stage] = DEFAULT_STAGES,
    n_buckets: int         = 3,
) -> FksResult:
    """Run Funnel Kernel Search on a pre-solved LP.

    Parameters
    ----------
    inst      : MSCFLP instance
    lp        : LP relaxation result (solved externally)
    stages    : list of (k_or_gamma_mult, time_limit) tuples defining the funnel
    n_buckets : maximum bucket batches per stage (stages 2+ only)
    """
    t0 = time.perf_counter()

    kernel    = lp.kernel()
    lbuck     = max(1, len(kernel))
    j0_sorted = sorted(lp.J0, key=lambda j: lp.rc_y.get(j, float("inf")))

    # Auto-detect edge-selection mode from the first stage multiplier
    use_flat_k  = stages[0][0] > 1.0
    bucket_k    = int(stages[0][0]) if use_flat_k else None  # Stage-1 k reused for buckets
    gammas      = None if use_flat_k else _per_client_gamma(inst, lp, kernel)

    def _edges(facs: Set[Facility], mult: float,
               prev_x: Optional[Dict[Edge, float]] = None) -> Set[Edge]:
        if use_flat_k:
            return _flat_k_edges(inst, lp, facs, int(mult), prev_x=prev_x)
        else:
            return _threshold_edges(inst, lp, facs, gammas, mult, prev_x=prev_x)

    best_obj  = float("inf")
    best_y:   Dict[Facility, float] = {}
    best_x:   Dict[Edge,     float] = {}
    prev_x:   Dict[Edge,     float] = {}
    n_milps      = 0
    stage_gaps:   List[float] = []
    stage_times:  List[float] = []
    stage_n_edges: List[int]  = []
    stage_n_milps: List[int]  = []
    stage_objs:    List[float] = []

    for s, (mult, t_lim) in enumerate(stages):
        st = time.perf_counter()

        edges = _edges(kernel, mult,
                       prev_x=prev_x if s > 0 and prev_x else None)

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

        # Bucket expansion (stages 2+ only)
        if s > 0:
            available_j0 = [j for j in j0_sorted if j not in kernel]
            for h in range(n_buckets):
                bucket = available_j0[h * lbuck:(h + 1) * lbuck]
                if not bucket:
                    break
                b_facs = kernel | set(bucket)
                b_mult  = float(bucket_k) if use_flat_k else 1.0
                b_edges = _edges(b_facs, b_mult,
                                 prev_x=best_x if best_x else None)
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

    final_gap = (best_obj - lp.objective) / lp.objective * 100 \
                if best_obj < float("inf") and lp.objective > 0 else float("nan")

    last_mult   = stages[-1][0]
    final_edges = _edges(kernel, last_mult,
                         prev_x=best_x if best_x else None)

    return FksResult(
        obj            = best_obj,
        gap_lp         = final_gap,
        lp_obj         = lp.objective,
        n_milps        = n_milps,
        n_edges        = len(final_edges),
        total_time     = time.perf_counter() - t0,
        stage_gaps     = stage_gaps,
        stage_times    = stage_times,
        y              = best_y,
        x              = best_x,
        stage_n_edges  = stage_n_edges,
        stage_n_milps  = stage_n_milps,
        stage_objs     = stage_objs,
    )
