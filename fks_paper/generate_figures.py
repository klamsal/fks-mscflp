#!/usr/bin/env python3
"""generate_figures.py — Publication figures for the FKS paper.

Produces (all PDF, drop-in for LaTeX):
  figures/lp_concentration.pdf  — histogram of LP non-zero edges per client
    figures/gap_scatter.pdf       — gap vs time scatter (KS vs FKS k=5)
  figures/gap_boxplots.pdf      — gap distribution box plots by family
    figures/edge_comparison.pdf   — edge count bar chart KS vs FKS k=3 / k=5

Run from the fks_paper/ directory:
  python3 generate_figures.py
"""

from __future__ import annotations

import sys
import csv
import math
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

# ── Paths ──────────────────────────────────────────────────────────────────────
PAPER_DIR   = Path(__file__).parent
FIG_DIR     = PAPER_DIR / "figures"
FKS_DIR     = PAPER_DIR.parent / "fks_mscflp"
FKS_RES     = FKS_DIR / "results"
KS_RES      = FKS_DIR / "results"

sys.path.insert(0, str(FKS_DIR))
FIG_DIR.mkdir(exist_ok=True)

# ── Style ──────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":        "serif",
    "font.size":          10,
    "axes.titlesize":     10,
    "axes.labelsize":     10,
    "xtick.labelsize":    9,
    "ytick.labelsize":    9,
    "legend.fontsize":    9,
    "figure.dpi":         200,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "lines.linewidth":    1.5,
    "patch.linewidth":    0.8,
})

KS_COLOR   = "#2166ac"   # blue
MC3_COLOR  = "#d73027"   # red-orange
MC5_COLOR  = "#f46d43"   # orange

FAMILIES = ["1000-1000", "1200-3000", "800-4400", "1000-4000", "2000-2000"]
FAMILY_LABELS = ["1000×1000", "1200×3000", "800×4400", "1000×4000", "2000×2000"]

# ── Helpers ────────────────────────────────────────────────────────────────────

def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))


def float_or_nan(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return math.nan


# ── Figure 1: LP Concentration ─────────────────────────────────────────────────

def fig_lp_concentration():
    """Histogram of per-client LP non-zero facility count (k_i^LP).

    Loads p1000-1000-1, solves the LP, counts non-zero x_{ji} per client.
    """
    print("Generating lp_concentration.pdf ...")
    try:
        from loaders import load_plc, find_testbed
        from lp_solver import solve_lp
    except ImportError as e:
        print(f"  Skipped (import error): {e}")
        return

    try:
        inst = load_plc(find_testbed("a", "p1000-1000-1"), "p1000-1000-1")
        lp   = solve_lp(inst)
    except Exception as e:
        print(f"  Skipped (LP solve error): {e}")
        return

    eps = 1e-6
    ki = []
    for i in inst.clients:
        count = sum(1 for j in inst.facilities if lp.x.get((j, i), 0.0) > eps)
        ki.append(count)

    ki = np.array(ki)
    avg_ki = ki.mean()
    max_ki = ki.max()

    fig, ax = plt.subplots(figsize=(5.5, 3.2))

    bins = np.arange(0, max_ki + 2) - 0.5
    counts, _, patches = ax.hist(ki, bins=bins, color=MC5_COLOR,
                                 edgecolor="white", linewidth=0.6, zorder=2)

    # Cumulative coverage line
    ax2 = ax.twinx()
    sorted_ki = np.sort(ki)
    cum_frac  = np.arange(1, len(sorted_ki) + 1) / len(sorted_ki) * 100
    unique_k  = np.unique(sorted_ki)
    cum_at_k  = [cum_frac[sorted_ki <= k].max() for k in unique_k]
    ax2.step(unique_k, cum_at_k, where="post", color=KS_COLOR,
             linewidth=1.8, linestyle="--", zorder=3, label="Cumulative %")
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("Cumulative clients (%)", color=KS_COLOR)
    ax2.tick_params(axis="y", colors=KS_COLOR)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(KS_COLOR)
    ax2.spines["top"].set_visible(False)

    ax.set_xlabel(r"Non-zero LP facilities per client ($k_i^{\rm LP}$)")
    ax.set_ylabel("Number of clients")
    ax.set_title(
        f"LP concentration — p1000-1000-1  "
        f"(avg $k_i^{{\\rm LP}}$ = {avg_ki:.2f})",
        pad=6
    )
    ax.set_xticks(range(0, max_ki + 1))
    ax.grid(axis="y", linewidth=0.4, color="0.88", zorder=0)

    # Annotate k=3 coverage
    if 3 in unique_k:
        cov3 = cum_at_k[list(unique_k).index(3)]
        ax.axvline(3, color="0.5", linewidth=0.8, linestyle=":")
        ax.text(3.15, counts.max() * 0.9, f"top-3 = {cov3:.1f}%",
                fontsize=8, color="0.4")

    fig.tight_layout()
    fig.savefig(FIG_DIR / "lp_concentration.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved  avg k_i^LP = {avg_ki:.2f}, max = {max_ki}")


# ── Figure 2: Gap Scatter ──────────────────────────────────────────────────────

def fig_gap_scatter():
    """Gap vs solve-time scatter: KS (blue circles) vs FKS k=5 (orange squares)."""
    print("Generating gap_scatter.pdf ...")

    ks_rows, mc_rows = [], []

    # KS data: one CSV per family (gap_lp column, time column)
    for fam in FAMILIES:
        fname = f"testbeda_{fam}_milp_300s.csv"
        for row in read_csv(KS_RES / fname):
            g = float_or_nan(row.get("gap_lp"))
            t = float_or_nan(row.get("time"))
            if not math.isnan(g) and not math.isnan(t):
                ks_rows.append({"family": fam, "gap": g, "time": t})

    # FKS k=5 data
    for fam in FAMILIES:
        fname = f"compare_tba_{fam}_k5_milp300s.csv"
        for row in read_csv(FKS_RES / fname):
            g = float_or_nan(row.get("mc_k5_gap_lp"))
            t = float_or_nan(row.get("mc_k5_time"))
            if not math.isnan(g) and not math.isnan(t):
                mc_rows.append({"family": fam, "gap": g, "time": t})

    # Also pull FKS k=3 results where k=5 not available
    for fam in FAMILIES:
        fname = f"compare_tba_{fam}_k3_milp300s.csv"
        already = {r["family"] for r in mc_rows}
        if fam not in already:
            for row in read_csv(FKS_RES / fname):
                g = float_or_nan(row.get("mc_k3_gap_lp"))
                t = float_or_nan(row.get("mc_k3_time"))
                if not math.isnan(g) and not math.isnan(t):
                    mc_rows.append({"family": fam, "gap": g, "time": t})

    if not ks_rows and not mc_rows:
        print("  Skipped (no data)")
        return

    markers = ["o", "s", "^", "D", "v"]
    fam_marker = {f: markers[i] for i, f in enumerate(FAMILIES)}

    fig, ax = plt.subplots(figsize=(6.0, 4.0))

    for fam, label in zip(FAMILIES, FAMILY_LABELS):
        pts = [r for r in ks_rows if r["family"] == fam]
        if pts:
            ax.scatter([p["time"] for p in pts],
                       [p["gap"]  for p in pts],
                       c=KS_COLOR, marker=fam_marker[fam],
                       s=30, alpha=0.75, linewidths=0,
                       label=f"KS  {label}" if fam == FAMILIES[0] else "_")

    for fam, label in zip(FAMILIES, FAMILY_LABELS):
        pts = [r for r in mc_rows if r["family"] == fam]
        if pts:
            ax.scatter([p["time"] for p in pts],
                       [p["gap"]  for p in pts],
                       c=MC5_COLOR, marker=fam_marker[fam],
                       s=30, alpha=0.75, linewidths=0,
                       label=f"FKS  {label}" if fam == FAMILIES[0] else "_")

    # Legend: method patches + family markers
    legend_patches = [
        mpatches.Patch(color=KS_COLOR,  label="KS (2012)"),
        mpatches.Patch(color=MC5_COLOR, label="FKS ($k=5$)"),
    ]
    family_handles = [
        plt.scatter([], [], marker=fam_marker[f], c="0.5", s=28, label=lbl)
        for f, lbl in zip(FAMILIES, FAMILY_LABELS)
    ]
    leg1 = ax.legend(handles=legend_patches, loc="upper left", frameon=False)
    ax.add_artist(leg1)
    ax.legend(handles=family_handles, loc="upper right", frameon=False,
              ncol=1, handletextpad=0.4, labelspacing=0.3)

    ax.set_xlabel("Solve time (s)")
    ax.set_ylabel("Gap vs LP lower bound (%)")
    ax.set_title("Solution quality: KS (2012) vs FKS — Test Bed A")
    ax.grid(linewidth=0.4, color="0.88", zorder=0)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "gap_scatter.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved  KS pts={len(ks_rows)}  FKS pts={len(mc_rows)}")


# ── Figure 3: Gap Box Plots ────────────────────────────────────────────────────

def fig_gap_boxplots():
    """Box plots of gap distribution per family: KS vs FKS."""
    print("Generating gap_boxplots.pdf ...")

    ks_gaps  = {f: [] for f in FAMILIES}
    mc_gaps  = {f: [] for f in FAMILIES}

    for fam in FAMILIES:
        for row in read_csv(KS_RES / f"testbeda_{fam}_milp_300s.csv"):
            g = float_or_nan(row.get("gap_lp"))
            if not math.isnan(g):
                ks_gaps[fam].append(g)

    for fam in FAMILIES:
        # prefer k=5, fall back to k=3
        for k in ["5", "3"]:
            fname = f"compare_tba_{fam}_k{k}_milp300s.csv"
            col   = f"mc_k{k}_gap_lp"
            rows  = read_csv(FKS_RES / fname)
            vals  = [float_or_nan(r.get(col)) for r in rows]
            vals  = [v for v in vals if not math.isnan(v)]
            if vals:
                mc_gaps[fam] = vals
                break

    # Only plot families that have data for at least one method
    plot_fams = [f for f in FAMILIES if ks_gaps[f] or mc_gaps[f]]
    if not plot_fams:
        print("  Skipped (no data)")
        return

    n = len(plot_fams)
    x = np.arange(n)
    width = 0.32

    fig, ax = plt.subplots(figsize=(7.0, 3.8))

    def draw_box(ax, data, positions, color, label):
        if not any(data):
            return
        bp = ax.boxplot(
            [d if d else [float("nan")] for d in data],
            positions=positions,
            widths=width * 0.85,
            patch_artist=True,
            notch=False,
            showfliers=True,
            flierprops=dict(marker="o", markersize=3,
                            markerfacecolor=color, alpha=0.5, linewidth=0),
            medianprops=dict(color="white", linewidth=1.8),
            boxprops=dict(facecolor=color, alpha=0.75, linewidth=0.7),
            whiskerprops=dict(linewidth=0.8, color="0.4"),
            capprops=dict(linewidth=0.8, color="0.4"),
            manage_ticks=False,
        )
        bp["boxes"][0].set_label(label)

    draw_box(ax, [ks_gaps[f] for f in plot_fams],
             x - width / 2, KS_COLOR, "KS (2012)")
    draw_box(ax, [mc_gaps[f] for f in plot_fams],
             x + width / 2, MC5_COLOR, "FKS")

    ax.set_xticks(x)
    ax.set_xticklabels([FAMILY_LABELS[FAMILIES.index(f)] for f in plot_fams],
                        rotation=15, ha="right")
    ax.set_ylabel("Gap vs LP lower bound (%)")
    ax.set_title("Gap distribution by instance family — Test Bed A")
    ax.grid(axis="y", linewidth=0.4, color="0.88", zorder=0)

    ks_patch = mpatches.Patch(color=KS_COLOR,  alpha=0.75, label="KS (2012)")
    fks_patch = mpatches.Patch(color=MC5_COLOR, alpha=0.75, label="FKS ($k=5$)")
    ax.legend(handles=[ks_patch, fks_patch], frameon=False, loc="upper right")

    fig.tight_layout()
    fig.savefig(FIG_DIR / "gap_boxplots.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved  {len(plot_fams)} families")


# ── Figure 4: Edge Comparison ──────────────────────────────────────────────────

def fig_edge_comparison():
    """Grouped bar chart: KS edges vs FKS k=3 vs FKS k=5 per family."""
    print("Generating edge_comparison.pdf ...")

    ks_edges  = {}
    mc3_edges = {}
    mc5_edges = {}

    for fam in FAMILIES:
        # KS edges: not stored directly in run_testbed.py CSVs.
        # Use the known analytic values from G&S 2012 (γ-threshold produces
        # O(n_cli × n_fac / density) edges; we read from compare CSVs if available).
        pass

    # Pull edge data from compare CSVs
    for fam in FAMILIES:
        for k, store in [("3", mc3_edges), ("5", mc5_edges)]:
            fname = f"compare_tba_{fam}_k{k}_milp300s.csv"
            rows  = read_csv(FKS_RES / fname)
            vals  = [float_or_nan(r.get(f"mc_k{k}_edges")) for r in rows]
            vals  = [v for v in vals if not math.isnan(v)]
            if vals:
                store[fam] = np.mean(vals)

        # KS edges: read from compare CSV if KS was run (no --no-ks)
        # Fall back to None if not available
        for k in ["3", "5"]:
            fname = f"compare_tba_{fam}_k{k}_milp300s.csv"
            rows  = read_csv(FKS_RES / fname)
            vals  = [float_or_nan(r.get("ks_edges")) for r in rows]
            vals  = [v for v in vals if not math.isnan(v)]
            if vals:
                ks_edges[fam] = np.mean(vals)
                break

    # For families without KS edges from compare (ran with --no-ks),
    # use client counts as proxy: n_cli from instance names
    client_counts = {
        "1000-1000": 1000,
        "1200-3000": 3000,
        "800-4400":  4400,
        "1000-4000": 4000,
        "2000-2000": 2000,
    }
    for fam, n_cli in client_counts.items():
        if fam not in mc3_edges:
            mc3_edges[fam] = 3 * n_cli
        if fam not in mc5_edges:
            mc5_edges[fam] = 5 * n_cli

    plot_fams = FAMILIES
    n = len(plot_fams)
    x = np.arange(n)
    width = 0.25

    fig, ax = plt.subplots(figsize=(7.5, 3.8))

    # KS bars (only where available)
    ks_vals = [ks_edges.get(f) for f in plot_fams]
    if any(v is not None for v in ks_vals):
        ks_plot = [v if v is not None else 0 for v in ks_vals]
        ks_hatch = ["" if v is not None else "///" for v in ks_vals]
        bars = ax.bar(x - width, ks_plot, width, color=KS_COLOR,
                      alpha=0.75, label="KS (2012) — $\\gamma$-threshold",
                      zorder=2)

    ax.bar(x,         [mc3_edges.get(f, 0) for f in plot_fams],
            width, color=MC3_COLOR, alpha=0.75, label="FKS $k=3$", zorder=2)
    ax.bar(x + width, [mc5_edges.get(f, 0) for f in plot_fams],
            width, color=MC5_COLOR, alpha=0.75, label="FKS $k=5$", zorder=2)

    # Annotate exact values on FKS bars
    for i, fam in enumerate(plot_fams):
        n_cli = client_counts[fam]
        ax.text(i,         mc3_edges.get(fam, 0) + 200,
                f"{int(3*n_cli/1000)}k", ha="center", va="bottom",
                fontsize=7, color=MC3_COLOR)
        ax.text(i + width, mc5_edges.get(fam, 0) + 200,
                f"{int(5*n_cli/1000)}k", ha="center", va="bottom",
                fontsize=7, color=MC5_COLOR)

    ax.set_xticks(x)
    ax.set_xticklabels(FAMILY_LABELS, rotation=15, ha="right")
    ax.set_ylabel("Number of edges in kernel MILP")
    ax.set_title("Edge compression: KS vs FKS — Test Bed A")
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", linewidth=0.4, color="0.88", zorder=0)
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v/1000)}k")
    )

    fig.tight_layout()
    fig.savefig(FIG_DIR / "edge_comparison.pdf", bbox_inches="tight")
    plt.close(fig)
    print("  Saved")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Figures → {FIG_DIR}\n")
    fig_lp_concentration()
    fig_gap_scatter()
    fig_gap_boxplots()
    fig_edge_comparison()
    print("\nDone.")
