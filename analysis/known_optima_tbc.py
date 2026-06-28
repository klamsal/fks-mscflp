"""
Known optimal / best known objective values for TB-C Avella instances.

Source: Avella, Boccia, Mattia, Rossi (2021) EJOR 289:485-494
        "Weak flow cover inequalities for the capacitated facility location problem"
        Algorithm: XP+WFC-enum (Xpress + Weak Flow Cover inequalities, cut-and-branch)
        Time limit: 3600 seconds
        Hardware: Intel Xeon Silver 4110 2.1 GHz, 32 GB RAM limit, Windows Server 2016
        Table A.9 — Best UB column (XP+WFC-enum)

TB-C instance indexing:  p{fac}-{cust}-{idx}  where idx in 61..90
  idx 61-65: ratio r=1.1   (time limit hit — best known UBs only)
  idx 66-70: ratio r=1.5   (time limit hit — best known UBs only)
  idx 71-75: ratio r=2.0   (time limit hit — best known UBs only)
  idx 76-80: ratio r=3.0   (proven optimal — LB=UB, terminated early)
  idx 81-85: ratio r=5.0   (proven optimal — LB=UB, terminated early)
  idx 86-90: ratio r=10.0  (proven optimal — root node, fastest)

Data format:
    instance -> (z_ref, source, proven_optimal)
    z_ref         = best known upper bound (= proven optimal when proven_optimal=True)
    source        = 'WFC2021'
    proven_optimal = True if LB=UB and algorithm terminated before time limit
"""

# ============================================================
# TB-C p2000-2000  (instances 61-90)
# ============================================================

TBC_2000_2000 = {
    # r=1.1 — best known UBs only (time limit hit)
    'p2000-2000-61': (9420045.0,   'WFC2021', False),
    'p2000-2000-62': (9566575.4,   'WFC2021', False),
    'p2000-2000-63': (10004760.5,  'WFC2021', False),
    'p2000-2000-64': (9768829.5,   'WFC2021', False),
    'p2000-2000-65': (9830472.4,   'WFC2021', False),
    # r=1.5 — best known UBs only
    'p2000-2000-66': (7426559.0,   'WFC2021', False),
    'p2000-2000-67': (7787608.1,   'WFC2021', False),
    'p2000-2000-68': (7294775.0,   'WFC2021', False),
    'p2000-2000-69': (7424499.6,   'WFC2021', False),
    'p2000-2000-70': (7296891.3,   'WFC2021', False),
    # r=2.0 — best known UBs only
    'p2000-2000-71': (6483777.1,   'WFC2021', False),
    'p2000-2000-72': (6570727.8,   'WFC2021', False),
    'p2000-2000-73': (6559197.2,   'WFC2021', False),
    'p2000-2000-74': (6373115.5,   'WFC2021', False),
    'p2000-2000-75': (6466400.0,   'WFC2021', False),
    # r=3.0 — PROVEN OPTIMAL (LB=UB, terminated early)
    'p2000-2000-76': (5579061.8,   'WFC2021', True),
    'p2000-2000-77': (5344227.6,   'WFC2021', True),
    'p2000-2000-78': (5266726.8,   'WFC2021', True),
    'p2000-2000-79': (5364116.2,   'WFC2021', True),
    'p2000-2000-80': (5272553.9,   'WFC2021', True),
    # r=5.0 — PROVEN OPTIMAL
    'p2000-2000-81': (5028251.2,   'WFC2021', True),
    'p2000-2000-82': (4987222.9,   'WFC2021', True),
    'p2000-2000-83': (4910622.4,   'WFC2021', True),
    'p2000-2000-84': (5041409.7,   'WFC2021', True),
    'p2000-2000-85': (5124973.6,   'WFC2021', True),
    # r=10.0 — PROVEN OPTIMAL (root node solve)
    'p2000-2000-86': (4971500.5,   'WFC2021', True),
    'p2000-2000-87': (4814108.5,   'WFC2021', True),
    'p2000-2000-88': (4986966.7,   'WFC2021', True),
    'p2000-2000-89': (5007857.5,   'WFC2021', True),
    'p2000-2000-90': (4947837.8,   'WFC2021', True),
}

ALL_TBC_OPTIMA = {}
ALL_TBC_OPTIMA.update(TBC_2000_2000)

if __name__ == '__main__':
    proven  = [(k, v) for k, v in TBC_2000_2000.items() if v[2]]
    bestknown = [(k, v) for k, v in TBC_2000_2000.items() if not v[2]]
    print(f'TB-C p2000-2000: {len(proven)} proven optimal, {len(bestknown)} best known UBs')
    print('\nProven optimal:')
    for k, (z, src, _) in proven:
        print(f'  {k}: {z:.1f}')
    print('\nBest known upper bounds:')
    for k, (z, src, _) in bestknown:
        print(f'  {k}: {z:.1f}')
