"""
Compare our method objectives against known proven optimal values.

Gap formula: gap% = 100 * (our_obj - z_star) / z_star
Should always be >= 0. A gap of 0.00% means we found the proven optimum.
"""

import os, sys
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from known_optima import ALL_OPTIMA

RESULTS = os.path.join(os.path.dirname(__file__), '..', 'fks_mscflp', 'results')


def load_csv(family_tag, mode):
    tb, fam = family_tag.split('_', 1)
    path = os.path.join(RESULTS, f'{tb}_{fam}_{mode}.csv')
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, on_bad_lines='skip')
    df = df[df['instance'].str.startswith('p')].copy()
    return df[['instance', 'obj', 'lp_obj', 'total_time']].rename(
        columns={'obj': f'obj_{mode}', 'lp_obj': f'lp_{mode}',
                 'total_time': f'time_{mode}'})


def build_comparison(family_tag, modes=('ks-full', 'ks-cg', 'fks-cg-ws')):
    # Collect our results
    merged = None
    for mode in modes:
        df = load_csv(family_tag, mode)
        if df is None:
            continue
        merged = df if merged is None else merged.merge(df, on='instance', how='outer')

    if merged is None:
        return None

    # Attach known optima
    opt_rows = []
    for _, row in merged.iterrows():
        inst = row['instance']
        if inst in ALL_OPTIMA:
            z_star, source, exact = ALL_OPTIMA[inst]
            opt_rows.append({
                'instance': inst,
                'z_star': z_star,
                'opt_source': source,
                'opt_exact': exact,
            })
        else:
            opt_rows.append({'instance': inst, 'z_star': None,
                             'opt_source': None, 'opt_exact': None})

    opt_df = pd.DataFrame(opt_rows)
    merged = merged.merge(opt_df, on='instance', how='left')

    # Compute gaps vs proven optimal
    for mode in modes:
        col = f'obj_{mode}'
        if col not in merged.columns:
            continue
        merged[f'gap_opt_{mode}'] = merged.apply(
            lambda r: 100 * (r[col] - r['z_star']) / r['z_star']
            if pd.notna(r['z_star']) and pd.notna(r[col]) else None,
            axis=1
        )

    return merged


def print_summary(family_tag, modes=('ks-full', 'ks-cg', 'fks-cg-ws')):
    df = build_comparison(family_tag, modes)
    if df is None:
        print(f'  No results for {family_tag}')
        return None

    fam = family_tag.replace('tba_', '')
    known = df['z_star'].notna().sum()
    print(f'\n=== TB-A {fam}  ({len(df)} instances, {known} with known optimum) ===')

    for mode in modes:
        gcol = f'gap_opt_{mode}'
        if gcol not in df.columns:
            continue
        sub = df[df[gcol].notna()][gcol]
        if len(sub) == 0:
            continue
        at_opt = (sub.abs() < 1e-4).sum()
        print(f'  {mode:12s}: avg gap {sub.mean():.4f}%  '
              f'max gap {sub.max():.4f}%  '
              f'at_opt (gap<0.0001%): {at_opt}/{len(sub)}')

    return df


def run_all():
    all_dfs = {}
    families = [
        'tba_1000-1000',
        'tba_800-4400',
        'tba_1000-4000',
        'tba_1200-3000',
        'tba_2000-2000',
    ]

    print('=' * 72)
    print('GAP VS PROVEN OPTIMAL  (gap% = 100*(our_obj - z*)/z*)')
    print('Source: Sampathkumar (2019) corridor method paper, CPLEX column')
    print('=' * 72)

    for tag in families:
        df = print_summary(tag)
        if df is not None:
            all_dfs[tag] = df

    # Save combined CSV
    out_dir = os.path.dirname(__file__)
    for tag, df in all_dfs.items():
        path = os.path.join(out_dir, f'optgap_{tag}.csv')
        df.to_csv(path, index=False)

    # Overall summary
    print('\n=== OVERALL TB-A SUMMARY ===')
    for mode in ('ks-full', 'ks-cg', 'fks-cg-ws'):
        gaps = []
        for df in all_dfs.values():
            col = f'gap_opt_{mode}'
            if col in df.columns:
                gaps.extend(df[col].dropna().tolist())
        if gaps:
            import numpy as np
            arr = pd.Series(gaps)
            print(f'  {mode:12s}: avg {arr.mean():.4f}%  max {arr.max():.4f}%  '
                  f'n={len(arr)}')

    return all_dfs


if __name__ == '__main__':
    run_all()
