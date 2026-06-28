# FKS MSCFLP

Standalone repository for the Funnel Kernel Search work on the multi-source
capacitated facility location problem.

## Layout

* `fks_mscflp/` - solver code, runners, and result writers
* `analysis/` - comparison scripts and derived objective tables
* `benchmarks/` - local instance data and archives, not tracked in Git

## Usage

Run the main solver entrypoint from the solver directory:

```bash
cd fks_mscflp
/opt/anaconda3/bin/python3.11 solve.py --testbed=a --family=1000-4000 --idx=7 --mode=fks-cg
```

The raw benchmark files are expected under `benchmarks/` when you run the
solver locally. They are intentionally excluded from version control.