"""
Compare our results against the CM paper reference CSV.

Instance name mapping:
  CSV: p1000x1000_1  →  ours: p1000-1000-1
  CSV: p800x4400_31  →  ours: p800-4400-31  (TB-B)

For "Proven Optimal" rows:   gap = 100*(our_obj - z*)/z*  (should be ~0)
For "Best Known" rows:       gap = 100*(our_obj - z_BK)/z_BK  (negative = we beat it)
"""

import os, sys
import pandas as pd

RESULTS = os.path.join(os.path.dirname(__file__), '..', 'fks_mscflp', 'results')
CM_CSV  = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..',
                       'cflp_instances_objectives_General Corridor.csv')
# Try relative path from project root
_proj = os.path.join(os.path.dirname(__file__), '..', '..')
CM_CSV2 = os.path.join(_proj, 'cflp_instances_objectives_General Corridor.csv')


def load_cm_csv():
    for p in [CM_CSV, CM_CSV2]:
        if os.path.exists(p):
            return pd.read_csv(p)
    raise FileNotFoundError('Cannot find CM reference CSV')


def cm_name_to_ours(name: str) -> str:
    """p1000x1000_1 → p1000-1000-1"""
    name = name.strip()
    # replace 'x' separating dimensions with '-'
    # replace '_' separating instance number with '-'
    parts = name.split('_')   # ['p1000x1000', '1']
    dim   = parts[0].replace('x', '-')
    idx   = parts[1]
    return f'{dim}-{idx}'


def load_our_csv(family, mode):
    """family like '1000-1000', mode like 'ks-full'"""
    for tb in ('tba', 'tbb'):
        path = os.path.join(RESULTS, f'{tb}_{family}_{mode}.csv')
        if os.path.exists(path):
            df = pd.read_csv(path, on_bad_lines='skip')
            df = df[df['instance'].str.startswith('p')].copy()
            return df[['instance', 'obj']].rename(columns={'obj': f'obj_{mode}'})
    return None


def run():
    ref = load_cm_csv()
    ref['our_name'] = ref['Instance Name'].apply(cm_name_to_ours)
    ref['z_ref']    = ref['Objective Value'].astype(float)
    ref['proven']   = ref['Status'].str.startswith('Proven Optimal')

    # Detect families present
    families = ref['Dimensions'].str.replace('x', '-').unique()
    modes    = ['ks-full', 'ks-cg', 'fks-cg']

    # Load all our results
    our_all = None
    for fam in families:
        for mode in modes:
            df = load_our_csv(fam, mode)
            if df is None:
                continue
            our_all = df if our_all is None else pd.concat([our_all, df], ignore_index=True)

    if our_all is None:
        print('No result CSVs found.')
        return

    # Pivot: one row per instance, columns per mode
    our_pivot = our_all.groupby('instance').first().reset_index()
    for mode in modes:
        col = f'obj_{mode}'
        sub = our_all[our_all.columns[our_all.columns.str.endswith(mode)].tolist() + ['instance']]
        sub = sub.dropna()
        if not sub.empty:
            our_pivot = our_pivot.merge(sub, on='instance', how='left', suffixes=('', f'_dup'))

    # Actually rebuild cleanly
    our_by_mode = {}
    for mode in modes:
        frames = []
        for fam in families:
            df = load_our_csv(fam, mode)
            if df is not None:
                frames.append(df)
        if frames:
            our_by_mode[mode] = pd.concat(frames, ignore_index=True)

    # Merge reference with our results
    merged = ref[['our_name', 'Test Bed', 'Dimensions', 'z_ref', 'Gap (%)', 'proven', 'Status']].copy()
    for mode, df in our_by_mode.items():
        merged = merged.merge(df.rename(columns={'instance': 'our_name'}),
                              on='our_name', how='left')

    # Compute gaps
    rows = []
    for _, r in merged.iterrows():
        row = {'instance': r['our_name'], 'testbed': r['Test Bed'],
               'family': r['Dimensions'], 'z_ref': r['z_ref'],
               'ref_status': r['Status'], 'proven': r['proven']}
        for mode in modes:
            col = f'obj_{mode}'
            if col in r and pd.notna(r[col]):
                gap = 100 * (r[col] - r['z_ref']) / r['z_ref']
                row[f'gap_{mode}'] = round(gap, 6)
                row[f'obj_{mode}'] = r[col]
            else:
                row[f'gap_{mode}'] = None
                row[f'obj_{mode}'] = None
        rows.append(row)

    result = pd.DataFrame(rows)

    # ── Print summary ──────────────────────────────────────────────
    print('=' * 74)
    print('COMPARISON VS GENERAL CORRIDOR METHOD (CM2019) REFERENCE')
    print('gap% = 100*(our_obj - z_ref)/z_ref  [negative = we beat ref]')
    print('=' * 74)

    for tb in ['Test Bed A', 'Test Bed B']:
        sub = result[result['testbed'] == tb]
        if sub.empty:
            continue
        have_results = sub[[f'obj_{m}' for m in modes]].notna().any(axis=1)
        sub = sub[have_results]
        if sub.empty:
            print(f'\n{tb}: no matching results')
            continue
        print(f'\n── {tb} ── ({len(sub)} instances with our results) ──')

        for fam in sub['family'].unique():
            fsub = sub[sub['family'] == fam]
            proven = fsub[fsub['proven']]
            best   = fsub[~fsub['proven']]
            print(f'\n  {fam}  (n={len(fsub)}: '
                  f'{len(proven)} proven opt, {len(best)} best known)')
            for mode in modes:
                gcol = f'gap_{mode}'
                vals = fsub[gcol].dropna()
                if vals.empty:
                    continue
                p_vals = proven[gcol].dropna()
                b_vals = best[gcol].dropna()
                beats  = (vals < -1e-6).sum()
                ties   = (vals.abs() <= 1e-6).sum()
                print(f'    {mode:12s}: avg {vals.mean():+.4f}%  '
                      f'max {vals.max():+.4f}%  '
                      f'beats_ref: {beats}  ties: {ties}  n={len(vals)}')
                if not p_vals.empty:
                    print(f'               vs proven opt: avg {p_vals.mean():+.4f}%  '
                          f'max {p_vals.max():+.4f}%  '
                          f'at_opt(|gap|<1e-4): {(p_vals.abs()<1e-4).sum()}/{len(p_vals)}')
                if not b_vals.empty:
                    print(f'               vs best known: avg {b_vals.mean():+.4f}%  '
                          f'beats: {(b_vals < -1e-6).sum()}/{len(b_vals)}')

    # ── Overall proven-optimal summary ────────────────────────────
    print('\n── OVERALL PROVEN OPTIMAL SUMMARY (TB-A) ──')
    tba = result[(result['testbed'] == 'Test Bed A') & result['proven']]
    for mode in modes:
        gcol = f'gap_{mode}'
        vals = tba[gcol].dropna()
        if vals.empty:
            continue
        at_opt = (vals.abs() < 1e-4).sum()
        print(f'  {mode:12s}: n={len(vals):3d}  avg {vals.mean():+.5f}%  '
              f'max {vals.max():+.5f}%  at_opt: {at_opt}/{len(vals)}')

    # ── Save full CSV ──────────────────────────────────────────────
    out = os.path.join(os.path.dirname(__file__), 'comparison_vs_cm_paper.csv')
    result.to_csv(out, index=False)
    print(f'\nSaved: {out}')
    return result


if __name__ == '__main__':
    run()
