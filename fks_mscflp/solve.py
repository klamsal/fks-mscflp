"""solve.py — Solve ONE instance with ONE mode, append ONE row to CSV, exit.

Usage:
    python solve.py --testbed=a --family=1000-4000 --idx=7 --mode=fks-cg-ws
    python solve.py --testbed=b --family=1200-3000 --idx=12 --mode=ks-full
    python solve.py --testbed=a --family=1000-1000 --idx=1 --mode=ks-cg --milp-time=300

Modes:
    ks-full   Full LP  + G&K 2012 Kernel Search
    ks-cg     CG LP   + G&K 2012 Kernel Search
    ks-cg-ws  CG LP   + KS with feasibility-preserving stage transitions
    fks-cg-ws CG LP   + Funnel KS (k=50→20→10, warm starts)

Output:
    results/tb{testbed}_{family}_{mode}.csv  — one row appended per run

Resume: if this (testbed, family, idx, mode) row already exists in the CSV,
        prints "already done" and exits immediately with code 0.
"""

from __future__ import annotations

import csv
import math
import sys
import time
from pathlib import Path

from loaders   import load_plc, find_instance
from lp_solver import solve_lp, solve_lp_cg
from ks        import run_ks
from fks       import run_fks
from ks_ws     import run_ks_ws
from testa_zub import TESTA_ZUB

RESULTS = Path(__file__).parent / "results"
RESULTS.mkdir(exist_ok=True)

FKS_STAGES = [(50.0, 300.0), (20.0, 300.0), (10.0, 300.0)]

# ── CLI ───────────────────────────────────────────────────────────────────────

args      = sys.argv[1:]
TESTBED   = next((a.split("=")[1] for a in args if a.startswith("--testbed=")), None)
FAMILY    = next((a.split("=")[1] for a in args if a.startswith("--family=")),  None)
IDX       = next((int(a.split("=")[1]) for a in args if a.startswith("--idx=")), None)
MODE      = next((a.split("=")[1] for a in args if a.startswith("--mode=")),    None)
MILP_TIME = next((float(a.split("=")[1]) for a in args if a.startswith("--milp-time=")), 300.0)

if not all([TESTBED, FAMILY, IDX, MODE]):
    print("Usage: python solve.py --testbed=a --family=1000-4000 --idx=7 --mode=fks-cg-ws")
    sys.exit(1)

if MODE not in ("ks-full", "ks-cg", "ks-cg-ws", "fks-cg-ws"):
    print(f"Unknown mode '{MODE}'. Must be ks-full, ks-cg, ks-cg-ws, or fks-cg-ws.")
    sys.exit(1)

INSTANCE_NAME = f"p{FAMILY}-{IDX}"
CSV_PATH = RESULTS / f"tb{TESTBED}_{FAMILY}_{MODE}.csv"

# ── CSV schema ────────────────────────────────────────────────────────────────
# Every field is written for every mode; fields not applicable to a mode are "".

FIELDNAMES = [
    # identity
    "instance", "testbed", "family", "n_fac", "n_cli", "mode",
    # LP phase
    "lp_solver", "lp_obj", "lp_time",
    "cg_iters", "cg_active_cols",
    # solution
    "obj", "gap_lp_pct", "gap_lp_h_pct",
    # vs G&K 2012 published upper bound
    "zub_gk", "impr_gk_pct",
    # MILP totals
    "n_milps", "milp_time", "total_time",
    # KS-specific
    "ks_kernel_size", "ks_gamma", "ks_n_edges", "ks_n_restarts", "ks_n_buckets",
    # FKS per-stage (3 stages)
    "fks_s1_k", "fks_s1_n_edges", "fks_s1_n_milps", "fks_s1_obj", "fks_s1_gap_lp", "fks_s1_time",
    "fks_s2_k", "fks_s2_n_edges", "fks_s2_n_milps", "fks_s2_obj", "fks_s2_gap_lp", "fks_s2_time",
    "fks_s3_k", "fks_s3_n_edges", "fks_s3_n_milps", "fks_s3_obj", "fks_s3_gap_lp", "fks_s3_time",
    # Reserved historical columns kept for CSV compatibility
    "fks_dr_tlp_s1_time", "fks_dr_tlp_s2_time",
]

# ── Resume check ──────────────────────────────────────────────────────────────

def _already_done() -> bool:
    if not CSV_PATH.exists():
        return False
    with CSV_PATH.open() as fh:
        for row in csv.DictReader(fh):
            if row.get("instance") == INSTANCE_NAME and row.get("mode") == MODE:
                return True
    return False

if _already_done():
    print(f"[skip] {INSTANCE_NAME} {MODE} already in {CSV_PATH.name}")
    sys.exit(0)

# ── Load instance ─────────────────────────────────────────────────────────────

print(f"[run ] {INSTANCE_NAME}  mode={MODE}  milp_time={MILP_TIME}s", flush=True)
t_start = time.perf_counter()

try:
    inst_path = find_instance(TESTBED, INSTANCE_NAME)
except FileNotFoundError:
    print(f"[skip] {INSTANCE_NAME} not found in testbed_{TESTBED} — skipping")
    sys.exit(0)

inst = load_plc(inst_path, INSTANCE_NAME)

# ── LP solve ──────────────────────────────────────────────────────────────────

use_cg = (MODE in ("ks-cg", "ks-cg-ws", "fks-cg-ws"))
if use_cg:
    lp = solve_lp_cg(inst)
else:
    lp = solve_lp(inst)

lp_time = lp.solve_time

# ── Algorithm ─────────────────────────────────────────────────────────────────

row: dict = {f: "" for f in FIELDNAMES}

# Identity
row["instance"] = INSTANCE_NAME
row["testbed"]  = TESTBED
row["family"]   = FAMILY
row["n_fac"]    = inst.n_fac
row["n_cli"]    = inst.n_cli
row["mode"]     = MODE

# LP
row["lp_solver"]      = "cg" if use_cg else "full"
row["lp_obj"]         = lp.objective
row["lp_time"]        = round(lp_time, 4)
row["cg_iters"]       = lp.cg_iters      if use_cg else ""
row["cg_active_cols"] = lp.cg_active_cols if use_cg else ""

# Published upper bound
zub = TESTA_ZUB.get(INSTANCE_NAME)
row["zub_gk"] = zub if zub is not None else ""

# Run algorithm
if MODE in ("ks-full", "ks-cg"):
    res = run_ks(inst, lp, milp_time=MILP_TIME)
elif MODE == "ks-cg-ws":
    res = run_ks_ws(inst, lp, milp_time=MILP_TIME)

if MODE in ("ks-full", "ks-cg", "ks-cg-ws"):
    obj       = res.obj
    milp_time = res.total_time
    n_milps   = res.n_milps

    row["ks_kernel_size"] = res.kernel_size
    row["ks_gamma"]       = round(res.gamma, 8)
    row["ks_n_edges"]     = res.n_edges
    row["ks_n_restarts"]  = res.n_restarts
    row["ks_n_buckets"]   = res.n_buckets_used

elif MODE == "fks-cg-ws":
    res = run_fks(inst, lp, stages=FKS_STAGES)

    obj       = res.obj
    milp_time = res.total_time
    n_milps   = res.n_milps

    for s, (mult, _) in enumerate(FKS_STAGES, start=1):
        prefix = f"fks_s{s}"
        i = s - 1
        s_obj  = res.stage_objs[i]   if res.stage_objs   and i < len(res.stage_objs)   else float("nan")
        s_gap  = res.stage_gaps[i]   if res.stage_gaps   and i < len(res.stage_gaps)   else float("nan")
        s_time = res.stage_times[i]  if res.stage_times  and i < len(res.stage_times)  else float("nan")
        s_ne   = res.stage_n_edges[i] if res.stage_n_edges and i < len(res.stage_n_edges) else ""
        s_nm   = res.stage_n_milps[i] if res.stage_n_milps and i < len(res.stage_n_milps) else ""
        row[f"{prefix}_k"]        = int(mult)
        row[f"{prefix}_n_edges"]  = s_ne
        row[f"{prefix}_n_milps"]  = s_nm
        row[f"{prefix}_obj"]      = round(s_obj,  6) if not math.isnan(s_obj)  else "nan"
        row[f"{prefix}_gap_lp"]   = round(s_gap,  6) if not math.isnan(s_gap)  else "nan"
        row[f"{prefix}_time"]     = round(s_time, 4) if not math.isnan(s_time) else "nan"

# Common solution quality
gap_lp_pct   = (obj - lp.objective) / lp.objective * 100 \
               if obj < float("inf") and lp.objective > 0 else float("nan")
gap_lp_h_pct = (obj - lp.objective) / obj * 100 \
               if obj < float("inf") and obj > 0 else float("nan")
impr_gk_pct  = (obj - zub) / obj * 100 \
               if (zub is not None and obj < float("inf") and obj > 0) else ""

row["obj"]          = round(obj, 6) if obj < float("inf") else "nan"
row["gap_lp_pct"]   = round(gap_lp_pct,   6) if not math.isnan(gap_lp_pct)   else "nan"
row["gap_lp_h_pct"] = round(gap_lp_h_pct, 6) if not math.isnan(gap_lp_h_pct) else "nan"
row["impr_gk_pct"]  = round(impr_gk_pct,  6) if impr_gk_pct != "" else ""

row["n_milps"]    = n_milps
row["milp_time"]  = round(milp_time, 4)
row["total_time"] = round(lp_time + milp_time, 4)

# ── Write CSV row ─────────────────────────────────────────────────────────────

write_header = not CSV_PATH.exists()
with CSV_PATH.open("a", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
    if write_header:
        writer.writeheader()
    writer.writerow(row)

elapsed = time.perf_counter() - t_start
print(f"[done] {INSTANCE_NAME} {MODE}  obj={row['obj']}  gap={row['gap_lp_pct']}%  "
      f"lp={lp_time:.1f}s  milp={milp_time:.1f}s  total={elapsed:.1f}s", flush=True)
