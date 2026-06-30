#!/usr/bin/env bash
# run_all.sh — run the full experiment campaign across all three testbeds.
#
# Testbed A: 5 families × 30 instances (idx 1-30)  = 150 instances
# Testbed B: 5 families × 25-30 instances (idx 31-60, 800-4400 ends at 55) = 145 instances
# Testbed C: 5 families × 30 instances (idx 61-90) = 150 instances
# Total: 445 instances × 4 modes = 1780 runs
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

FAMILIES="800-4400 1000-1000 1200-3000 1000-4000 2000-2000"
MODES="ks-full ks-cg ks-cg-ws fks-cg-ws"

# Testbed B instance files use indices 31-60 (800-4400 only has 31-55).
tbb_idx_end() {
    if [[ "$1" == "800-4400" ]]; then echo 55; else echo 60; fi
}

for MODE in $MODES; do
    for FAMILY in $FAMILIES; do
        echo "--- tba $FAMILY $MODE ---"
        bash run_batch.sh a "$FAMILY" "$MODE" "$MILP_TIME" \
            2>&1 | tee -a "logs/tba_${FAMILY}_${MODE}.log"
    done
    for FAMILY in $FAMILIES; do
        echo "--- tbb $FAMILY $MODE ---"
        bash run_batch.sh b "$FAMILY" "$MODE" "$MILP_TIME" 31 "$(tbb_idx_end "$FAMILY")" \
            2>&1 | tee -a "logs/tbb_${FAMILY}_${MODE}.log"
    done
    for FAMILY in $FAMILIES; do
        echo "--- tbc $FAMILY $MODE ---"
        bash run_batch.sh c "$FAMILY" "$MODE" "$MILP_TIME" 61 90 \
            2>&1 | tee -a "logs/tbc_${FAMILY}_${MODE}.log"
    done
done

echo "=== ALL DONE: $(date) ==="
