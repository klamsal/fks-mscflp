# Algorithm Modes (Canonical)

Last updated: 2026-06-28

This file defines the canonical algorithm mode names and their inclusion order.
Use these names consistently in scripts, experiments, tables, and paper text.

## Canonical mode set

1. `ks-full`
2. `ks-cg`
3. `ks-cg-ws`
4. `fks-cg-ws`

## Inclusion order

Use the following component-wise ladder:

1. `ks-full` -> baseline G&S-style KS with full LP.
2. `ks-cg` -> adds CG LP (Fix 1).
3. `ks-cg-ws` -> adds feasibility-preserving stage transitions / warm starts (Fix 3).
4. `fks-cg-ws` -> full method with flat-k funnel + WS (Fix 2 on top of Fix 1 + Fix 3).

## Naming policy

- `fks-cg-ws` is the canonical name of the full method.
- Legacy aliases are not supported.
- Non-canonical experimental mode names are not part of the standard run ladder.

## Current codebase status

- `solve.py` accepts only the four canonical modes above.
- `run_all.sh` and `progress.sh` use the same four-mode set.
- `run_batch.sh` examples and top-level `README.md` examples use `fks-cg-ws`.
