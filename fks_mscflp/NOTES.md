# FKS Development Notes

## Option 2: γ-threshold edge selection for Stage 1

**Problem**: On small instances (300×300), FKS Stage 1 top-k LP primal misses some
arcs that KS keeps via the γ-threshold, causing tiny quality losses (< 0.06%).

**Proposed fix**: Replace Stage 1 top-k LP primal with the γ-threshold edge selection
identical to KS. Stages 2 and 3 continue with adaptive incumbent edges (top-k narrowing).

This gives:
- Stage 1: γ-threshold (same edge set as KS) → guarantees KS-quality incumbent
- Stage 2: adaptive incumbent edges, k=20 → narrows to promising arcs
- Stage 3: adaptive incumbent edges, k=10 → fine refinement + warm start

Benefits:
- Closes quality gap on small/dense instances (300×300, 500×500)
- Stage 1 edge set becomes adaptive (no need to tune k=50)
- Warm-start + funnel narrowing in Stages 2/3 still provide speedup vs plain KS

**Status**: Pending — observe i3001500 and larger families first before implementing.

---

## Algorithm positioning: FKS as a variation of Kernel Search

FKS is not a new paradigm — it is a principled critique-and-repair of G&K (2012) Kernel Search. The paper's contribution is:

1. Identifying specific design flaws in G&K's KS (γ-threshold J0 bias, no warm start, drop criterion flaw, bucket ordering by opening cost alone)
2. Proposing targeted fixes (top-k per client, warm start every MILP, multi-stage funnel)
3. Providing a ladder of experiments that proves each fix contributes independently

This framing is stronger than claiming a new algorithm — it is a rigorous empirical and theoretical critique of an established method with demonstrated improvements.

## Component-wise comparison ladder

The ladder adds one modification at a time:

```text
KS-full    → KS-CG       : Fix 1 — replaces full LP with CG LP
KS-CG      → KS-CG-WS    : Fix 3 — adds feasibility-preserving stage transitions
KS-CG-WS   → FKS-CG-WS   : Fix 2 — replaces γ-threshold with flat-k arc selection
```

**Why Fix 3 before Fix 2 in the ladder:**
Fix 3 (feasibility-preserving transitions) is the structural prerequisite for Fix 2.
The flat-k funnel (Fix 2) deliberately narrows arc sets across stages (k=50→20→10).
When the arc set shrinks, incumbent arcs may be discarded and the incumbent becomes
infeasible in the next stage. Fix 3 prevents this by including all incumbent arcs in
the next stage's edge set — guaranteeing feasibility by construction (Proposition 2).
Without Fix 3, the flat-k funnel would force cold restarts at every stage transition.
The natural order is therefore: prove the safety guarantee (Fix 3) first, then apply
the aggressive narrowing design that relies on it (Fix 2).

**Naming rationale (paper-side only; internal CSVs keep fks-cg):**
The `-WS` suffix marks variants with feasibility-preserving transitions throughout:
- KS-CG-WS: γ-threshold arc selection + feasibility-preserving
- FKS-CG-WS: flat-k arc selection + feasibility-preserving (the full method)
The `FKS` prefix marks the flat-k funnel design. Each name element maps to one fix:
  "CG" = Fix 1, "WS" = Fix 3, "FKS" prefix = Fix 2.

**Algorithm section order (matches ladder):**
  §3.3 Fix 1 — Column Generation LP
  §3.4 Fix 3 — Feasibility-Preserving Stage Transitions
  §3.5 Fix 2 — Flat-k Arc Selection

The section presenting Fix 3 before Fix 2 because Fix 3's guarantee motivates
and enables the flat-k design: the Proposition 2 result is the reason flat-k
narrowing is safe to use.
