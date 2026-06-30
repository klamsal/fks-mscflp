"""
Compare G&S 2012 reconstructed objectives against our KS-LP, KS-CG, FKS-CG-WS objectives.

Rule: each method's objective is compared against its OWN lower bound for gap%.
For cross-method comparison, only the raw objective (z_H) is used — no shared bound.

Reconstruction of G&S z_H:
  TB-C: z_H_GS = z_LB_GS / (1 - opt_gap_pct/100)
  TB-A: z_H_GS = z_UB_avella * (1 + impr_pct/100)
"""

import pandas as pd
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gs2012_reported_data import (
    TBC_800_4400, TBC_1000_1000, TBC_1000_4000,
    TBC_1200_3000, TBC_2000_2000,
    TBA_1000_4000_PARTIAL, TBA_1000_1000_PARTIAL,
)

RESULTS = os.path.join(os.path.dirname(__file__), '..', 'fks_mscflp', 'results')


def load_our_results(family, mode):
    """Load our CSV results for a given (testbed-family, mode) pair."""
    tb = family.split('_')[0]          # e.g. 'tbc'
    fam = '_'.join(family.split('_')[1:])  # e.g. '1000-1000'
    path = os.path.join(RESULTS, f'{tb}_{fam}_{mode}.csv')
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, on_bad_lines='skip')
    return df[['instance', 'lp_obj', 'obj']].rename(
        columns={'lp_obj': f'lp_{mode}', 'obj': f'obj_{mode}'}
    )


def reconstruct_gs_tbc(data):
    """Build DataFrame of G&S TB-C data with reconstructed z_H."""
    rows = []
    for (inst, ratio, z_lb, gap_pct) in data:
        z_h = z_lb / (1 - gap_pct / 100)
        rows.append({'instance': inst, 'ratio': ratio,
                     'gs_zLB': z_lb, 'gs_gap_pct': gap_pct, 'gs_obj': z_h})
    return pd.DataFrame(rows)


def reconstruct_gs_tba(data):
    """Build DataFrame of G&S TB-A data with reconstructed z_H."""
    rows = []
    for (inst, z_ub, z_lb, impr_pct, opt_gap_pct) in data:
        if z_ub is not None and impr_pct is not None:
            z_h = z_ub * (1 + impr_pct / 100)
        elif z_lb is not None:
            z_h = z_lb / (1 - opt_gap_pct / 100)
        else:
            z_h = None
        rows.append({'instance': inst, 'gs_zUB_avella': z_ub,
                     'gs_zLB': z_lb, 'gs_impr_pct': impr_pct,
                     'gs_opt_gap_pct': opt_gap_pct, 'gs_obj': z_h})
    return pd.DataFrame(rows)


def compare_tbc(family_tag, gs_data, modes=('ks-full', 'ks-cg', 'fks-cg-ws')):
    gs = reconstruct_gs_tbc(gs_data)

    # Load our results
    our = None
    for mode in modes:
        df = load_our_results(family_tag, mode)
        if df is None:
            continue
        our = df if our is None else our.merge(df, on='instance', how='outer')

    if our is None:
        print(f'  No results found for {family_tag}')
        return None

    merged = gs.merge(our, on='instance', how='inner')

    # Compute % difference: how much better (negative) or worse (positive) is our obj vs G&S
    for mode in modes:
        col = f'obj_{mode}'
        if col in merged.columns:
            merged[f'diff_{mode}_pct'] = 100 * (merged[col] - merged['gs_obj']) / merged['gs_obj']

    return merged


def summary_tbc(family_tag, gs_data, modes=('ks-full', 'ks-cg', 'fks-cg-ws')):
    df = compare_tbc(family_tag, gs_data, modes)
    if df is None:
        return
    n = len(df)
    fam = family_tag.replace('tbc_', '').replace('tba_', '')
    print(f'\n=== TB-C {fam} (n={n}) ===')
    print(f'  G&S z_H range: [{df.gs_obj.min():.0f}, {df.gs_obj.max():.0f}]')
    for mode in modes:
        col = f'diff_{mode}_pct'
        if col not in df.columns:
            continue
        wins = (df[col] < -1e-6).sum()
        ties = (df[col].abs() <= 1e-6).sum()
        losses = (df[col] > 1e-6).sum()
        print(f'  {mode:12s}: avg diff {df[col].mean():+.4f}%  '
              f'max diff {df[col].max():+.4f}%  '
              f'W/T/L vs G&S: {wins}/{ties}/{losses}')
    return df


def run_all():
    results = {}

    print('=' * 70)
    print('OBJECTIVE COMPARISON: OUR METHODS vs G&S 2012 B-KS')
    print('Diff% = 100*(our_obj - gs_obj)/gs_obj  (negative = we win)')
    print('=' * 70)

    for tag, data in [
        ('tbc_800-4400',  TBC_800_4400),
        ('tbc_1000-1000', TBC_1000_1000),
        ('tbc_1000-4000', TBC_1000_4000),
        ('tbc_1200-3000', TBC_1200_3000),
        ('tbc_2000-2000', TBC_2000_2000),
    ]:
        df = summary_tbc(tag, data)
        if df is not None:
            results[tag] = df

    # Save full comparison CSVs
    out_dir = os.path.dirname(__file__)
    for tag, df in results.items():
        out_path = os.path.join(out_dir, f'comparison_{tag}.csv')
        df.to_csv(out_path, index=False)
        print(f'\nSaved: {out_path}')

    return results


if __name__ == '__main__':
    run_all()
