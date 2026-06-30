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

## Solver Code Structure

Main solver package: `fks_mscflp/`

* `solve.py` - single-instance entrypoint; runs one mode on one instance and appends one CSV row
* `loaders.py` - benchmark instance discovery and parsing (`.plc`, OR-Library)
* `lp_solver.py` - LP relaxation solvers (full LP and column generation LP)
* `ks.py` - Kernel Search (baseline full/CG path)
* `ks_ws.py` - Kernel Search with feasibility-preserving warm-start transitions
* `fks.py` - Funnel Kernel Search stages (`k=50 -> 20 -> 10`)
* `run_batch.sh` - sequential runner for one `(testbed, family, mode)` slice
* `run_all.sh` - full campaign runner across families/modes/testbeds
* `progress.sh` - completed/expected status table from result CSVs
* `README_ALGORITHM_MODES.md` - canonical mode names and intended inclusion ladder

## Canonical Modes

Use only the canonical modes below (also enforced by `solve.py`):

1. `ks-full`
2. `ks-cg`
3. `ks-cg-ws`
4. `fks-cg-ws`

## Data And Indexing Notes

* Testbed A instances are loaded from `benchmarks/testbed_a/`.
* Testbed B instances are loaded from `benchmarks/testbed_b/`.
* Some families in testbed B have non-`1..30` index ranges in filenames (for example
	`p1000-1000-31.plc`, ...), so not every `(family, idx)` pair exists.
* Missing files are handled safely by `solve.py` with `[skip] ... not found`.

## Usage

### Reproducible Benchmark Setup

1. Create and activate a local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install exact locked dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
```

3. Configure local environment variables for solver runtime:

```bash
cp .env.example .env
# then set GRB_LICENSE_FILE in .env
```

Run the main solver entrypoint from the solver directory:

```bash
cd fks_mscflp
../.venv/bin/python solve.py --testbed=a --family=1000-4000 --idx=7 --mode=fks-cg-ws
```

For batch runs, use the provided shell scripts. They auto-load `.env` from the
repository root and prefer `.venv/bin/python` when available.

### Run Patterns

Run one slice:

```bash
cd fks_mscflp
bash run_batch.sh a 1000-4000 fks-cg-ws 300
```

Run full campaign:

```bash
cd fks_mscflp
nohup bash run_all.sh > logs/run_all.log 2>&1 &
```

Watch progress:

```bash
cd fks_mscflp
bash progress.sh --watch
```

### Output Files

* Result CSVs are written to `fks_mscflp/results/`.
* File naming convention:
	`tb{testbed}_{family}_{mode}.csv` (for example `tba_1000-1000_fks-cg-ws.csv`).
* `solve.py` is resume-safe: if `(instance, mode)` already exists in the output CSV,
	that run is skipped.
* Derived comparison tables are written under `analysis/`. Some historical
	derived CSVs may use the legacy column label `fks-cg`; new runs and scripts
	use the canonical mode name `fks-cg-ws`.

## Reproducibility Checklist

1. Use the project virtual environment (`.venv`).
2. Install from `requirements-lock.txt`.
3. Set `GRB_LICENSE_FILE` in `.env`.
4. Run via `run_batch.sh`/`run_all.sh` (they load `.env` and prefer `.venv/bin/python`).
5. Record command, mode, family, and `milp-time` with each run log.

## Troubleshooting

* `ModuleNotFoundError: gurobipy`:
	install dependencies into `.venv` and run with `.venv/bin/python`.
* `Academic license ...` or other Gurobi startup messages are expected at runtime.
* Frequent `[skip] ... not found` for one family in testbed B usually means index
	mismatch with available filenames; verify actual file names in `benchmarks/testbed_b/`.

The raw benchmark files are expected under `benchmarks/` when you run the
solver locally. They are intentionally excluded from version control.

When moving this repo to another machine, copy `benchmarks/`, `Literature/`,
and the two reference files above into the new local checkout before running
the analysis or paper scripts. The FKS paper itself is tracked in Git.
