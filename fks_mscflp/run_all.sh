#!/usr/bin/env bash
# run_all.sh — queue all 1180 runs sequentially (295 instances × 4 modes).
#
# Run this in a nohup session so it survives terminal close:
#   nohup bash run_all.sh > logs/run_all.log 2>&1 &
#
# To run a single combination instead, use run_batch.sh directly.
# Already-completed instances are always skipped.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
mkdir -p logs

MILP_TIME=300

FAMILIES_A="800-4400 1000-1000 1200-3000 1000-4000 2000-2000"
FAMILIES_B="800-4400 1000-1000 1200-3000 1000-4000 2000-2000"
MODES="ks-full ks-cg ks-cg-ws fks-cg-ws"

for MODE in $MODES; do
    for FAMILY in $FAMILIES_A; do
        echo "--- tba $FAMILY $MODE ---"
        bash run_batch.sh a "$FAMILY" "$MODE" "$MILP_TIME" \
            2>&1 | tee -a "logs/tba_${FAMILY}_${MODE}.log"
    done
    for FAMILY in $FAMILIES_B; do
        echo "--- tbb $FAMILY $MODE ---"
        bash run_batch.sh b "$FAMILY" "$MODE" "$MILP_TIME" \
            2>&1 | tee -a "logs/tbb_${FAMILY}_${MODE}.log"
    done
done

echo "=== ALL DONE: $(date) ==="
