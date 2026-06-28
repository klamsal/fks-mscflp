# FKS MSCFLP

Standalone repository for the Funnel Kernel Search work on the multi-source
capacitated facility location problem.

## Layout

* `fks_mscflp/` - solver code, runners, and result writers
* `analysis/` - comparison scripts and derived objective tables
* `fks_paper/` - tracked FKS paper source
* `Literature/` - local reference library, not tracked in Git
* `benchmarks/` - local instance data and archives, not tracked in Git
* `cflp_instances_objectives_General Corridor.csv` - local reference CSV used by the comparison scripts
* `tprs_a_1636320_sm2925.doc` - local corridor-method reference document

## Usage

Run the main solver entrypoint from the solver directory:

```bash
cd fks_mscflp
/opt/anaconda3/bin/python3.11 solve.py --testbed=a --family=1000-4000 --idx=7 --mode=fks-cg-ws
```

The raw benchmark files are expected under `benchmarks/` when you run the
solver locally. They are intentionally excluded from version control.

When moving this repo to another machine, copy `benchmarks/`, `Literature/`,
and the two reference files above into the new local checkout before running
the analysis or paper scripts. The FKS paper itself is tracked in Git.
