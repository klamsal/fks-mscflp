#!/usr/bin/env bash
# run_batch.sh — run one (testbed, family, mode) combination sequentially.
#
# Usage:
#   bash run_batch.sh <testbed> <family> <mode> [milp_time] [idx_start] [idx_end]
#
# Examples:
#   bash run_batch.sh a 1000-4000 fks-cg-ws
#   bash run_batch.sh b 1200-3000 ks-full 300
#   bash run_batch.sh c 1000-1000 fks-cg-ws 300 61 90
#
# Each instance is a fresh python process — clean memory between instances.
# Already-completed instances are skipped automatically by solve.py.

TESTBED=${1:?usage: run_batch.sh <testbed> <family> <mode> [milp_time] [idx_start] [idx_end]}
FAMILY=${2:?}
MODE=${3:?}
MILP_TIME=${4:-300}
IDX_START=${5:-1}
IDX_END=${6:-30}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -f "$REPO_ROOT/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$REPO_ROOT/.env"
    set +a
fi

if [[ -z "$PYTHON_BIN" ]]; then
    if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
        PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
    else
        PYTHON_BIN="python"
    fi
fi

echo "=== run_batch  testbed=$TESTBED  family=$FAMILY  mode=$MODE  milp_time=${MILP_TIME}s  idx=${IDX_START}..${IDX_END} ==="
echo "    started: $(date)"

for i in $(seq "$IDX_START" "$IDX_END"); do
    "$PYTHON_BIN" solve.py \
        --testbed="$TESTBED" \
        --family="$FAMILY" \
        --idx="$i" \
        --mode="$MODE" \
        --milp-time="$MILP_TIME"
done

echo "=== done: $(date) ==="
