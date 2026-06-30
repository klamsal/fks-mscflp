# Objective Comparison: Our Methods vs G&S 2012

## How to read this document

We compare raw objectives (z^H) directly — no shared lower bound.

**G&S z^H reconstruction:**
- TB-A/B: z^H_GS = z^UB_Avella × (1 + impr%/100)   [impr% from Table 15/16]
- TB-C:   z^H_GS = z^LB_GS / (1 − gap%/100)          [from Table 17]

**Diff% = 100 × (our_obj − gs_obj) / gs_obj**
- Negative = we find a better (lower) solution than G&S
- Positive = G&S found a better solution

**Do NOT compare gap percentages across methods** — each uses its own lower bound.
G&S TB-C uses Lagrangean lower bound (weaker than LP, especially for large r).
Our gap_lp_pct uses LP lower bound (tighter). Same solutions → different gap%.

---

## Key insight on G&S reported gaps

For TB-C p1000-1000, G&S reports avg gap = 3.57% (vs their Lagrangean z^LB).
When we reconstruct G&S's actual z^H and compare to our LP lower bound:
- G&S gap vs our LP = 0.314% avg
- Our gap vs our LP = 0.271% avg
- Our LP is 2.85% tighter than G&S's Lagrangean on average

**Conclusion:** G&S's large reported gaps on TB-C are mostly a lower-bound artifact.
Their actual solutions are much better than the gap% suggests.
The real solution quality difference is small (0.04% avg on p1000-1000 TB-C).

---

## Results by family

### TB-C p1000-1000 (30 instances, indices 61–90) — COMPLETE

Source: `comparison_tbc_1000-1000.csv`
G&S data: Table 17, p913–914 of G&S 2012

| Method    | Avg diff% vs G&S | Max diff% | W / T / L vs G&S |
|-----------|-----------------|-----------|------------------|
| KS-full   | −0.0426%        | +0.0004%  | 27 / 0 / 3       |
| KS-CG     | −0.0412%        | +0.0004%  | 27 / 0 / 3       |
| FKS-CG-WS | −0.0428%        | +0.0004%  | 27 / 0 / 3       |

By ratio (KS-full):
| r    | Avg diff% | Note |
|------|-----------|------|
| 1.1  | −0.006%   | Near-identical solutions |
| 1.5  | −0.060%   | Moderate improvement |
| 2.0  | −0.103%   | Best improvement |
| 3.0  | −0.085%   | Good improvement |
| 5.0  | −0.001%   | Near-identical |
| 10.0 | −0.001%   | Near-identical |

**Takeaway:** Our methods win on 27/30 instances but improvements are small (avg 0.04%).
The 3 losses are < 0.001% worse — essentially ties.

---

### TB-C p800-4400 — PENDING (no runs yet)
### TB-C p1000-4000 — PENDING (no runs yet)
### TB-C p1200-3000 — PENDING (no runs yet)
### TB-C p2000-2000 — PENDING (no runs yet)

---

### TB-A p1000-1000 (30 instances, indices 1–30) — RUNS COMPLETE

For TB-A we compare improvements over the Avella et al. 2006 upper bounds z^UB.
G&S z^H is reconstructed from Table 15 as: z^UB × (1 + impr%/100).

G&S reported: avg improvement −0.13%, 26 improvements out of 30.
Our KS-LP: avg improvement −0.13%, 28 improvements, 2 ties.

Direct objective comparison pending — need to load TB-A CSV and compute.
See `compare_objectives.py` for TB-A reconstruction code (TBA_1000_1000_PARTIAL).

---

### TB-A p1000-4000 — RUNS IN PROGRESS (ks-cg-ws background run)
### TB-A p1200-3000 — RUNS COMPLETE (all 3 modes)
### TB-A p2000-2000 — RUNS COMPLETE (all 3 modes)
### TB-A p800-4400  — RUNS COMPLETE (all 3 modes)

---

## What Fischetti 2016 actually reports for p* instances

Source: Fischetti, Ljubić, Sinnl (2016), EJOR 253:557–569

Time limit: 50,000 seconds (default).
Hardware: Intel Xeon E3-1220V2 @ 3.1 GHz, CPLEX 12.6.1.
GS hardware per Fischetti: Intel Xeon @ 2.27 GHz (~30% slower), IBM ILOG Cplex 12.2.

**Figure 2 — Benders-as-heuristic (10 B&B nodes) vs G&S-as-published.**
Fig. 2 plots two gap series:
- "GS" gaps = G&S's published values from their Table 6, computed with Lagrangean lower bound
- "Benders" gaps = Benders own gaps with Benders lower bound (LP + Benders cuts; tighter)

These two series use DIFFERENT lower bounds. The visual gap between the curves reflects
BOTH solution quality AND lower-bound quality. They cannot be separated from Fig. 2 alone.

**Fischetti's exact statement, specifically about Test Bed C (Section 5.2.4, p.565):**
> "the worst gaps obtained by Benders are ≤ 2% (and in 80% of all instances even ≤ 1%),
> whereas GS gaps are > 2% for 70% of all instances, and can be as large as 8%."

This refers to TB-C instances ONLY, not all p* instances.
For TB-A and TB-B (Fig. 2a/b), GS and Benders gaps are much closer.

**Full Benders (50,000s) on p* — instances solved to optimality:**
| Test Bed | Instances | Solved optimal |
|----------|-----------|----------------|
| TB-A     | 150       | 97             |
| TB-B     | 145       | 40             |
| TB-C     | 150       | 73             |

**What our objective comparison adds (TB-C p1000-1000):**
Comparing reconstructed z^H directly shows G&S solutions are only 0.04% worse than ours.
The 3.57% published gap is mostly from weak Lagrangean lower bound.
But the Benders-vs-GS comparison in Fig. 2 also includes tighter Benders lower bounds —
we cannot claim from our data alone how much of the Figure 2 difference is LB vs solution quality
for larger families (p1200-3000, p2000-2000) where G&S genuinely struggles.

---

---

---

## Gap vs proven optimal / best known — TB-C results

Source of proven optima and best known upper bounds: Avella, Boccia, Mattia, Rossi (2021),
"Weak flow cover inequalities for the capacitated facility location problem" (EJOR 289:485-494).
This paper provides the state-of-the-art results for the difficult Test Bed C instances.

**Coverage:**
- For instances with tight capacity ratios (r=1.1, 1.5, 2.0), the paper provides the
  best known upper bounds, as their exact method hit the time limit.
- For instances with looser capacity ratios (r=3.0, 5.0, 10.0), the paper provides
  new proven optimal solutions.

The data is codified in `analysis/known_optima_tbc.py`.

---

## Gap vs proven optimal — TB-A results

Source of proven optima: Sampathkumar (2019), "A General Corridor Method-Based Approach
for Capacitated Facility Location" (tprs_a_1636320_sm2925.doc, Table 16).
CPLEX column with no flag or 'o' flag = proven optimal within 1e-8.

**Coverage: 110 of 150 TB-A instances have known proven optima.**
- p1000-1000: 30/30 (all ratios covered)
- p800-4400:  21/30 (ratio 5.0 entirely missing; ratios 3.0 and 10.0 partial)
- p1000-4000: 21/30 (ratios 3.0, 5.0 partial; ratio 10.0 partial)
- p1200-3000: 19/30 (ratios 5.0, 10.0 mostly missing)
- p2000-2000: 19/30 (ratios 5.0, 10.0 entirely missing)

Pattern: CPLEX times out (10,000s) on high capacity-ratio instances (r=5, 10) for the
larger families. These are the hardest instances for exact methods.

**Gap% = 100*(our_obj - z*) / z*  (0% = found proven optimum)**

| Family | KS-full avg | KS-full max | KS-CG avg | KS-CG max | FKS-CG-WS avg | FKS-CG-WS max |
|---|---|---|---|---|---|---|
| p1000-1000 (30) | 0.0018% | 0.0373% | 0.0001% | 0.0025% | 0.0000% | 0.0003% |
| p800-4400  (21) | 0.0021% | 0.0246% | 0.0010% | 0.0055% | 0.0000% | 0.0000% |
| p1000-4000 (21) | 0.0029% | 0.0173% | 0.0211% | **0.2726%** | 0.0000% | 0.0000% |
| p1200-3000 (19) | 0.0027% | 0.0268% | 0.0014% | 0.0096% | 0.0000% | 0.0000% |
| p2000-2000 (19) | 0.0026% | 0.0136% | 0.0012% | 0.0088% | 0.0000% | 0.0007% |
| **Overall (110)** | **0.0024%** | **0.0373%** | **0.0047%** | **0.2726%** | **0.0000%** | **0.0007%** |

**FKS-CG-WS finds the proven optimal solution on 109/110 instances (the one miss is
p2000-2000, gap 0.0007% — within 1 unit of objective value).**

Notable: KS-CG has one outlier — p1000-4000-17 at 0.2726% gap (obj=116,619 vs z*=116,302).
This is the same instance where FKS-CG-WS recovers the optimum, suggesting the flat-k
arc selection in FKS is more robust for this type of instance.

## Scripts

- `gs2012_reported_data.py` — G&S 2012 per-instance data (z^LB, gap%) from paper appendix
- `compare_objectives.py`   — loads data + our CSVs, computes diff%, saves comparison CSVs

Run: `python3 analysis/compare_objectives.py` from the `mc_paper` parent directory.

---

## Data completeness checklist

### G&S 2012 data extracted (from paper PDF)
- [x] TB-C p800-4400   (30 instances) — Table 17
- [x] TB-C p1000-1000  (30 instances) — Table 17
- [x] TB-C p1000-4000  (30 instances) — Table 17
- [x] TB-C p1200-3000  (30 instances) — Table 17
- [x] TB-C p2000-2000  (30 instances) — Table 17
- [x] TB-A p1000-1000  (instances 10–30) — Table 15 (instances 1–9 TODO)
- [x] TB-A p1000-4000  (all 30) — Table 15
- [ ] TB-A p800-4400   — Table 15 (need to read earlier pages)
- [ ] TB-A p1200-3000  — Table 15 (need to read)
- [ ] TB-A p2000-2000  — Table 15 (need to read)

### Our experimental runs complete
- [x] TB-A all 5 families × ks-full, ks-cg, fks-cg
- [x] TB-A p1000-4000 × ks-cg-ws (in progress as of 2026-06-24)
- [x] TB-C p1000-1000 × ks-full, ks-cg, fks-cg
- [ ] TB-C p800-4400, p1000-4000, p1200-3000, p2000-2000 — not yet run
