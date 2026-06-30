"""
Known proven optimal objective values for MS-CFLP Avella test bed instances.

Sources:
  CV2020  — Caserta, M. & Voß, S. (2020), "A general corridor method-based approach for
             capacitated facility location," International Journal of Production Research,
             58(13):3855-3880. DOI: 10.1080/00207543.2019.1636320.
             Supplementary material: tprs_a_1636320_sm2925.doc, Table 16 (Test Bed A).
             Column 'cplex' with no flag = proven optimal by CPLEX (10,000s time limit).
             Column 'cplex' with 'o' flag = within optimality tolerance 1e-8 (treated as optimal).
             Column 'cplex' with 't' flag = timed out, NOT included here.

  FISCH16 — Fischetti, Ljubić, Sinnl (2016), EJOR 253:557-569. Proved 97/150 TB-A instances
             to optimality via Benders decomposition (50,000s time limit). Per-instance values
             not yet extracted; only summary statistics available.

Data format:
    instance_name -> (z_star, source, exact)
    z_star  = proven optimal objective value
    source  = citation key
    exact   = True if proven optimal (no tolerance); False if within 1e-8 tolerance ('o' flag)

These values are the TRUE OPTIMUM (or proven within 1e-8) for each instance.
They are the reference for computing optimality gaps of our methods.

Gap formula: gap% = 100 * (our_obj - z_star) / z_star
(positive = our solution is above optimal; negative would mean we beat it, impossible if z_star is truly optimal)
"""

# ============================================================
# TEST BED A — p1000-1000
# All 30 instances proven optimal by CV2020 CPLEX
# ============================================================
TBA_1000_1000_OPT = {
    'p1000-1000-1':  (920505.22445, 'CV2020', True),
    'p1000-1000-2':  (920834.16909, 'CV2020', True),
    'p1000-1000-3':  (931305.42212, 'CV2020', True),
    'p1000-1000-4':  (917951.67276, 'CV2020', True),
    'p1000-1000-5':  (915635.35050, 'CV2020', True),
    'p1000-1000-6':  (530737.47132, 'CV2020', False),  # 'o' flag: within 1e-8 tolerance
    'p1000-1000-7':  (570792.94414, 'CV2020', True),
    'p1000-1000-8':  (573827.77861, 'CV2020', True),
    'p1000-1000-9':  (556686.44779, 'CV2020', True),
    'p1000-1000-10': (543599.77830, 'CV2020', True),
    'p1000-1000-11': (350069.26967, 'CV2020', True),
    'p1000-1000-12': (311516.15073, 'CV2020', True),
    'p1000-1000-13': (331149.17475, 'CV2020', True),
    'p1000-1000-14': (334622.61070, 'CV2020', True),
    'p1000-1000-15': (347407.29584, 'CV2020', True),
    'p1000-1000-16': ( 95959.21666, 'CV2020', True),
    'p1000-1000-17': ( 93998.80723, 'CV2020', True),
    'p1000-1000-18': ( 95737.23238, 'CV2020', True),
    'p1000-1000-19': ( 91057.26173, 'CV2020', True),
    'p1000-1000-20': ( 97280.06753, 'CV2020', True),
    'p1000-1000-21': ( 49884.82588, 'CV2020', True),
    'p1000-1000-22': ( 51137.53722, 'CV2020', True),
    'p1000-1000-23': ( 50060.79298, 'CV2020', True),
    'p1000-1000-24': ( 50504.31549, 'CV2020', True),
    'p1000-1000-25': ( 48338.05942, 'CV2020', True),
    'p1000-1000-26': ( 27490.95601, 'CV2020', True),
    'p1000-1000-27': ( 26586.94385, 'CV2020', True),
    'p1000-1000-28': ( 26563.89072, 'CV2020', True),
    'p1000-1000-29': ( 27859.42135, 'CV2020', True),
    'p1000-1000-30': ( 26825.19503, 'CV2020', True),
}

# ============================================================
# TEST BED A — p800-4400
# 21 of 30 proven optimal (instances 6,17,18,21-25,28 timed out)
# ============================================================
TBA_800_4400_OPT = {
    'p800-4400-1':  (745157.62523, 'CV2020', True),
    'p800-4400-2':  (742345.88184, 'CV2020', True),
    'p800-4400-3':  (747284.67896, 'CV2020', True),
    'p800-4400-4':  (754884.22567, 'CV2020', True),
    'p800-4400-5':  (749490.69026, 'CV2020', True),
    # 6: timed out
    'p800-4400-7':  (447436.80664, 'CV2020', True),
    'p800-4400-8':  (468724.72501, 'CV2020', True),
    'p800-4400-9':  (424875.96520, 'CV2020', True),
    'p800-4400-10': (441218.45184, 'CV2020', True),
    'p800-4400-11': (290546.19753, 'CV2020', True),
    'p800-4400-12': (292210.14819, 'CV2020', True),
    'p800-4400-13': (304561.73711, 'CV2020', True),
    'p800-4400-14': (304417.41462, 'CV2020', True),
    'p800-4400-15': (282870.37226, 'CV2020', True),
    'p800-4400-16': (100662.71955, 'CV2020', True),
    # 17, 18: timed out
    'p800-4400-19': (104689.01140, 'CV2020', True),
    'p800-4400-20': (102453.94740, 'CV2020', True),
    # 21-25: timed out
    'p800-4400-26': ( 59499.34230, 'CV2020', True),
    'p800-4400-27': ( 58852.11067, 'CV2020', True),
    # 28: timed out
    'p800-4400-29': ( 57936.39921, 'CV2020', True),
    'p800-4400-30': ( 58041.44423, 'CV2020', True),
}

# ============================================================
# TEST BED A — p1000-4000
# 21 of 30 proven optimal (instances 16,19-25,27 timed out)
# ============================================================
TBA_1000_4000_OPT = {
    'p1000-4000-1':  ( 935346.19236, 'CV2020', True),
    'p1000-4000-2':  ( 961530.55676, 'CV2020', True),
    'p1000-4000-3':  ( 924322.09106, 'CV2020', True),
    'p1000-4000-4':  ( 961794.30851, 'CV2020', True),
    'p1000-4000-5':  ( 955174.82778, 'CV2020', True),
    'p1000-4000-6':  ( 559009.85914, 'CV2020', True),
    'p1000-4000-7':  ( 582189.88438, 'CV2020', True),
    'p1000-4000-8':  ( 572170.10414, 'CV2020', True),
    'p1000-4000-9':  ( 537074.91340, 'CV2020', True),
    'p1000-4000-10': ( 562949.07447, 'CV2020', True),
    'p1000-4000-11': ( 338880.03645, 'CV2020', True),
    'p1000-4000-12': ( 353171.94813, 'CV2020', True),
    'p1000-4000-13': ( 354229.64893, 'CV2020', True),
    'p1000-4000-14': ( 368438.25806, 'CV2020', True),
    'p1000-4000-15': ( 359137.89462, 'CV2020', True),
    # 16: timed out
    'p1000-4000-17': ( 116302.25560, 'CV2020', True),
    'p1000-4000-18': ( 119521.78726, 'CV2020', True),
    # 19-25: timed out
    'p1000-4000-26': (  55590.87110, 'CV2020', True),
    # 27: timed out
    'p1000-4000-28': (  55869.13169, 'CV2020', True),
    'p1000-4000-29': (  55853.15327, 'CV2020', True),
    'p1000-4000-30': (  54939.91068, 'CV2020', True),
}

# ============================================================
# TEST BED A — p1200-3000
# 19 of 30 proven optimal (instances 8,16,20,22-25,27-30 timed out)
# ============================================================
TBA_1200_3000_OPT = {
    'p1200-3000-1':  (1081002.01820, 'CV2020', True),
    'p1200-3000-2':  (1107883.62200, 'CV2020', True),
    'p1200-3000-3':  (1078677.41980, 'CV2020', True),
    'p1200-3000-4':  (1113783.82287, 'CV2020', True),
    'p1200-3000-5':  (1087166.44553, 'CV2020', True),
    'p1200-3000-6':  ( 627192.89110, 'CV2020', False),  # 'o' flag
    'p1200-3000-7':  ( 636045.11016, 'CV2020', True),
    # 8: timed out
    'p1200-3000-9':  ( 660310.50969, 'CV2020', True),
    'p1200-3000-10': ( 638753.46363, 'CV2020', True),
    'p1200-3000-11': ( 410938.10766, 'CV2020', True),
    'p1200-3000-12': ( 404562.92392, 'CV2020', True),
    'p1200-3000-13': ( 426698.57867, 'CV2020', True),
    'p1200-3000-14': ( 414823.40034, 'CV2020', True),
    'p1200-3000-15': ( 410574.05705, 'CV2020', True),
    # 16: timed out
    'p1200-3000-17': ( 124868.80963, 'CV2020', True),
    'p1200-3000-18': ( 126550.88017, 'CV2020', True),
    'p1200-3000-19': ( 130075.33724, 'CV2020', True),
    # 20: timed out
    'p1200-3000-21': (  73073.32990, 'CV2020', True),
    # 22-25: timed out
    'p1200-3000-26': (  47911.27380, 'CV2020', True),
    # 27-30: timed out
}

# ============================================================
# TEST BED A — p2000-2000
# 19 of 30 proven optimal (instances 5,9-12,23,26-30 timed out)
# ============================================================
TBA_2000_2000_OPT = {
    'p2000-2000-1':  (1821914.12536, 'CV2020', False),  # 'o' flag
    'p2000-2000-2':  (1848136.28654, 'CV2020', True),
    'p2000-2000-3':  (1799167.06916, 'CV2020', True),
    'p2000-2000-4':  (1851083.97392, 'CV2020', True),
    # 5: timed out
    'p2000-2000-6':  (1061472.74153, 'CV2020', True),
    'p2000-2000-7':  (1042839.28798, 'CV2020', True),
    'p2000-2000-8':  (1044710.02171, 'CV2020', True),
    # 9, 10: timed out
    # 11, 12: timed out
    'p2000-2000-13': ( 648821.96878, 'CV2020', True),
    'p2000-2000-14': ( 661298.62236, 'CV2020', True),
    'p2000-2000-15': ( 699290.01601, 'CV2020', True),
    'p2000-2000-16': ( 183580.50872, 'CV2020', True),
    'p2000-2000-17': ( 192332.35807, 'CV2020', True),
    'p2000-2000-18': ( 181451.61687, 'CV2020', False),  # 'o' flag
    'p2000-2000-19': ( 185587.06511, 'CV2020', True),
    'p2000-2000-20': ( 177992.43989, 'CV2020', False),  # 'o' flag
    'p2000-2000-21': (  93236.56796, 'CV2020', True),
    'p2000-2000-22': (  94302.29782, 'CV2020', True),
    # 23: timed out
    'p2000-2000-24': (  96221.19070, 'CV2020', True),
    'p2000-2000-25': (  94113.42537, 'CV2020', True),
    # 26-30: timed out
}

# ============================================================
# Combined lookup — all families
# ============================================================
ALL_OPTIMA = {}
ALL_OPTIMA.update(TBA_1000_1000_OPT)
ALL_OPTIMA.update(TBA_800_4400_OPT)
ALL_OPTIMA.update(TBA_1000_4000_OPT)
ALL_OPTIMA.update(TBA_1200_3000_OPT)
ALL_OPTIMA.update(TBA_2000_2000_OPT)

# Coverage summary
COVERAGE = {
    'p1000-1000': (len(TBA_1000_1000_OPT), 30),
    'p800-4400':  (len(TBA_800_4400_OPT),  30),
    'p1000-4000': (len(TBA_1000_4000_OPT), 30),
    'p1200-3000': (len(TBA_1200_3000_OPT), 30),
    'p2000-2000': (len(TBA_2000_2000_OPT), 30),
}

if __name__ == '__main__':
    total_known = sum(v[0] for v in COVERAGE.values())
    total_inst  = sum(v[1] for v in COVERAGE.values())
    print(f'Known proven optima: {total_known}/{total_inst} TB-A instances')
    for fam, (k, n) in COVERAGE.items():
        exact = sum(1 for inst, (z, src, ex) in ALL_OPTIMA.items()
                    if fam in inst and ex)
        tol   = sum(1 for inst, (z, src, ex) in ALL_OPTIMA.items()
                    if fam in inst and not ex)
        print(f'  p{fam}: {k}/{n} proven  ({exact} exact + {tol} within 1e-8)')
