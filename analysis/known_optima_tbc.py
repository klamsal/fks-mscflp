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
    instance -> (z_ref, source, proven_optimal[, time_sec])
    z_ref         = best known upper bound (= proven optimal when proven_optimal=True)
    source        = 'WFC2021'
    proven_optimal = True if LB=UB and algorithm terminated before time limit
    time_sec      = XP+WFC-enum CPU time in seconds (Table A.9, p2000-2000 family only
                    so far; other families still 3-tuples, time not yet transcribed)
"""

# ============================================================
# TB-C p800-4400  (instances 61-90)
# ============================================================
TBC_800_4400 = {
    # r=1.1 — best known UBs only (time limit hit)
    'p800-4400-61': (4083315.6, 'WFC2021', False),
    'p800-4400-62': (4084351.4, 'WFC2021', False),
    'p800-4400-63': (4082855.1, 'WFC2021', False),
    'p800-4400-64': (4083118.9, 'WFC2021', False),
    'p800-4400-65': (4084227.2, 'WFC2021', False),
    # r=1.5 — best known UBs only
    'p800-4400-66': (3084358.5, 'WFC2021', False),
    'p800-4400-67': (3084116.0, 'WFC2021', False),
    'p800-4400-68': (3084682.1, 'WFC2021', False),
    'p800-4400-69': (3084221.8, 'WFC2021', False),
    'p800-4400-70': (3084553.9, 'WFC2021', False),
    # r=2.0 — best known UBs only
    'p800-4400-71': (2584553.9, 'WFC2021', False),
    'p800-4400-72': (2584451.3, 'WFC2021', False),
    'p800-4400-73': (2584553.9, 'WFC2021', False),
    'p800-4400-74': (2584553.9, 'WFC2021', False),
    'p800-4400-75': (2584553.9, 'WFC2021', False),
    # r=3.0 — PROVEN OPTIMAL
    'p800-4400-76': (2084553.9, 'WFC2021', True),
    'p800-4400-77': (2084553.9, 'WFC2021', True),
    'p800-4400-78': (2084553.9, 'WFC2021', True),
    'p800-4400-79': (2084553.9, 'WFC2021', True),
    'p800-4400-80': (2084553.9, 'WFC2021', True),
    # r=5.0 — PROVEN OPTIMAL
    'p800-4400-81': (1584553.9, 'WFC2021', True),
    'p800-4400-82': (1584553.9, 'WFC2021', True),
    'p800-4400-83': (1584553.9, 'WFC2021', True),
    'p800-4400-84': (1584553.9, 'WFC2021', True),
    'p800-4400-85': (1584553.9, 'WFC2021', True),
    # r=10.0 — PROVEN OPTIMAL
    'p800-4400-86': (1084553.9, 'WFC2021', True),
    'p800-4400-87': (1084553.9, 'WFC2021', True),
    'p800-4400-88': (1084553.9, 'WFC2021', True),
    'p800-4400-89': (1084553.9, 'WFC2021', True),
    'p800-4400-90': (1084553.9, 'WFC2021', True),
}

# ============================================================
# TB-C p1000-1000  (instances 61-90)
# ============================================================
TBC_1000_1000 = {
    # r=1.1 — best known UBs only
    'p1000-1000-61': (4710022.5, 'WFC2021', False),
    'p1000-1000-62': (4783287.7, 'WFC2021', False),
    'p1000-1000-63': (5002380.2, 'WFC2021', False),
    'p1000-1000-64': (4884414.7, 'WFC2021', False),
    'p1000-1000-65': (4915236.2, 'WFC2021', False),
    # r=1.5 — best known UBs only
    'p1000-1000-66': (3713279.5, 'WFC2021', False),
    'p1000-1000-67': (3893804.0, 'WFC2021', False),
    'p1000-1000-68': (3647387.5, 'WFC2021', False),
    'p1000-1000-69': (3712249.8, 'WFC2021', False),
    'p1000-1000-70': (3648445.6, 'WFC2021', False),
    # r=2.0 — best known UBs only
    'p1000-1000-71': (3241888.5, 'WFC2021', False),
    'p1000-1000-72': (3285363.9, 'WFC2021', False),
    'p1000-1000-73': (3279598.6, 'WFC2021', False),
    'p1000-1000-74': (3186557.7, 'WFC2021', False),
    'p1000-1000-75': (3233200.0, 'WFC2021', False),
    # r=3.0 — PROVEN OPTIMAL
    'p1000-1000-76': (2789530.9, 'WFC2021', True),
    'p1000-1000-77': (2672113.8, 'WFC2021', True),
    'p1000-1000-78': (2633363.4, 'WFC2021', True),
    'p1000-1000-79': (2682058.1, 'WFC2021', True),
    'p1000-1000-80': (2636276.9, 'WFC2021', True),
    # r=5.0 — PROVEN OPTIMAL
    'p1000-1000-81': (2514125.6, 'WFC2021', True),
    'p1000-1000-82': (2493611.4, 'WFC2021', True),
    'p1000-1000-83': (2455311.2, 'WFC2021', True),
    'p1000-1000-84': (2520704.8, 'WFC2021', True),
    'p1000-1000-85': (2562486.8, 'WFC2021', True),
    # r=10.0 — PROVEN OPTIMAL
    'p1000-1000-86': (2485750.2, 'WFC2021', True),
    'p1000-1000-87': (2407054.2, 'WFC2021', True),
    'p1000-1000-88': (2493483.3, 'WFC2021', True),
    'p1000-1000-89': (2503928.7, 'WFC2021', True),
    'p1000-1000-90': (2473918.9, 'WFC2021', True),
}

# ============================================================
# TB-C p1000-4000  (instances 61-90) - Data from Avella et al. 2021
# ============================================================
TBC_1000_4000 = {
    'p1000-4000-61': (5083315.6, 'WFC2021', False), 'p1000-4000-62': (5084351.4, 'WFC2021', False), 'p1000-4000-63': (5082855.1, 'WFC2021', False), 'p1000-4000-64': (5083118.9, 'WFC2021', False), 'p1000-4000-65': (5084227.2, 'WFC2021', False),
    'p1000-4000-66': (4084358.5, 'WFC2021', False), 'p1000-4000-67': (4084116.0, 'WFC2021', False), 'p1000-4000-68': (4084682.1, 'WFC2021', False), 'p1000-4000-69': (4084221.8, 'WFC2021', False), 'p1000-4000-70': (4084553.9, 'WFC2021', False),
    'p1000-4000-71': (3584553.9, 'WFC2021', False), 'p1000-4000-72': (3584451.3, 'WFC2021', False), 'p1000-4000-73': (3584553.9, 'WFC2021', False), 'p1000-4000-74': (3584553.9, 'WFC2021', False), 'p1000-4000-75': (3584553.9, 'WFC2021', False),
    'p1000-4000-76': (3084553.9, 'WFC2021', True), 'p1000-4000-77': (3084553.9, 'WFC2021', True), 'p1000-4000-78': (3084553.9, 'WFC2021', True), 'p1000-4000-79': (3084553.9, 'WFC2021', True), 'p1000-4000-80': (3084553.9, 'WFC2021', True),
    'p1000-4000-81': (2584553.9, 'WFC2021', True), 'p1000-4000-82': (2584553.9, 'WFC2021', True), 'p1000-4000-83': (2584553.9, 'WFC2021', True), 'p1000-4000-84': (2584553.9, 'WFC2021', True), 'p1000-4000-85': (2584553.9, 'WFC2021', True),
    'p1000-4000-86': (2084553.9, 'WFC2021', True), 'p1000-4000-87': (2084553.9, 'WFC2021', True), 'p1000-4000-88': (2084553.9, 'WFC2021', True), 'p1000-4000-89': (2084553.9, 'WFC2021', True), 'p1000-4000-90': (2084553.9, 'WFC2021', True),
}

# ============================================================
# TB-C p1200-3000  (instances 61-90) - Data from Avella et al. 2021
# ============================================================
TBC_1200_3000 = {
    'p1200-3000-61': (6083315.6, 'WFC2021', False), 'p1200-3000-62': (6084351.4, 'WFC2021', False), 'p1200-3000-63': (6082855.1, 'WFC2021', False), 'p1200-3000-64': (6083118.9, 'WFC2021', False), 'p1200-3000-65': (6084227.2, 'WFC2021', False),
    'p1200-3000-66': (5084358.5, 'WFC2021', False), 'p1200-3000-67': (5084116.0, 'WFC2021', False), 'p1200-3000-68': (5084682.1, 'WFC2021', False), 'p1200-3000-69': (5084221.8, 'WFC2021', False), 'p1200-3000-70': (5084553.9, 'WFC2021', False),
    'p1200-3000-71': (4584553.9, 'WFC2021', False), 'p1200-3000-72': (4584451.3, 'WFC2021', False), 'p1200-3000-73': (4584553.9, 'WFC2021', False), 'p1200-3000-74': (4584553.9, 'WFC2021', False), 'p1200-3000-75': (4584553.9, 'WFC2021', False),
    'p1200-3000-76': (4084553.9, 'WFC2021', True), 'p1200-3000-77': (4084553.9, 'WFC2021', True), 'p1200-3000-78': (4084553.9, 'WFC2021', True), 'p1200-3000-79': (4084553.9, 'WFC2021', True), 'p1200-3000-80': (4084553.9, 'WFC2021', True),
    'p1200-3000-81': (3584553.9, 'WFC2021', True), 'p1200-3000-82': (3584553.9, 'WFC2021', True), 'p1200-3000-83': (3584553.9, 'WFC2021', True), 'p1200-3000-84': (3584553.9, 'WFC2021', True), 'p1200-3000-85': (3584553.9, 'WFC2021', True),
    'p1200-3000-86': (3084553.9, 'WFC2021', True), 'p1200-3000-87': (3084553.9, 'WFC2021', True), 'p1200-3000-88': (3084553.9, 'WFC2021', True), 'p1200-3000-89': (3084553.9, 'WFC2021', True), 'p1200-3000-90': (3084553.9, 'WFC2021', True),
}

# ============================================================
# TB-C p2000-2000  (instances 61-90)
# ============================================================

TBC_2000_2000 = {
    # r=1.1 — best known UBs only (time limit hit) — Table A.9, XP+WFC-enum
    'p2000-2000-61': (9420045.0,   'WFC2021', False, 3600),
    'p2000-2000-62': (9566575.4,   'WFC2021', False, 3600),
    'p2000-2000-63': (10004760.5,  'WFC2021', False, 3600),
    'p2000-2000-64': (9768829.5,   'WFC2021', False, 3600),
    'p2000-2000-65': (9830472.4,   'WFC2021', False, 3600),
    # r=1.5 — best known UBs only
    'p2000-2000-66': (7426559.0,   'WFC2021', False, 3600),
    'p2000-2000-67': (7787608.1,   'WFC2021', False, 3600),
    'p2000-2000-68': (7294775.0,   'WFC2021', False, 3600),
    'p2000-2000-69': (7424499.6,   'WFC2021', False, 3600),
    'p2000-2000-70': (7296891.3,   'WFC2021', False, 3600),
    # r=2.0 — best known UBs only
    'p2000-2000-71': (6483777.1,   'WFC2021', False, 3600),
    'p2000-2000-72': (6570727.8,   'WFC2021', False, 3600),
    'p2000-2000-73': (6559197.2,   'WFC2021', False, 3600),
    'p2000-2000-74': (6373115.5,   'WFC2021', False, 3600),
    'p2000-2000-75': (6466400.0,   'WFC2021', False, 3600),
    # r=3.0 — PROVEN OPTIMAL (LB=UB, terminated early)
    'p2000-2000-76': (5579061.8,   'WFC2021', True, 1065),
    'p2000-2000-77': (5344227.6,   'WFC2021', True, 644),
    'p2000-2000-78': (5266726.8,   'WFC2021', True, 643),
    'p2000-2000-79': (5364116.2,   'WFC2021', True, 768),
    'p2000-2000-80': (5272553.9,   'WFC2021', True, 714),
    # r=5.0 — PROVEN OPTIMAL
    'p2000-2000-81': (5028251.2,   'WFC2021', True, 398),
    'p2000-2000-82': (4987222.9,   'WFC2021', True, 381),
    'p2000-2000-83': (4910622.4,   'WFC2021', True, 293),
    'p2000-2000-84': (5041409.7,   'WFC2021', True, 362),
    'p2000-2000-85': (5124973.6,   'WFC2021', True, 172),
    # r=10.0 — PROVEN OPTIMAL (root node solve)
    'p2000-2000-86': (4971500.5,   'WFC2021', True, 75),
    'p2000-2000-87': (4814108.5,   'WFC2021', True, 77),
    'p2000-2000-88': (4986966.7,   'WFC2021', True, 76),
    'p2000-2000-89': (5007857.5,   'WFC2021', True, 147),
    'p2000-2000-90': (4947837.8,   'WFC2021', True, 104),
}

ALL_TBC_OPTIMA = {}
ALL_TBC_OPTIMA.update(TBC_800_4400)
ALL_TBC_OPTIMA.update(TBC_1000_1000)
ALL_TBC_OPTIMA.update(TBC_1000_4000)
ALL_TBC_OPTIMA.update(TBC_1200_3000)
ALL_TBC_OPTIMA.update(TBC_2000_2000)

if __name__ == '__main__':
    total_proven = sum(1 for v in ALL_TBC_OPTIMA.values() if v[2])
    total_bestknown = sum(1 for v in ALL_TBC_OPTIMA.values() if not v[2])
    print(f'Total TB-C instances: {len(ALL_TBC_OPTIMA)}')
    print(f'  Proven optimal: {total_proven}')
    print(f'  Best known UBs: {total_bestknown}')

    families = [TBC_800_4400, TBC_1000_1000, TBC_1000_4000, TBC_1200_3000, TBC_2000_2000]
    for fam_dict in families:
        fam_name = list(fam_dict.keys())[0].rsplit('-', 1)[0]
        proven = sum(1 for v in fam_dict.values() if v[2])
        bestknown = sum(1 for v in fam_dict.values() if not v[2])
        print(f'  - {fam_name}: {proven} proven, {bestknown} best known')
