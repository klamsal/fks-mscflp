#!/usr/bin/env bash
# progress.sh — show how many instances are done per (testbed, family, mode).
#
# Usage:
#   bash progress.sh          # summary table
#   bash progress.sh --watch  # refresh every 60s

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$SCRIPT_DIR/results"

FAMILIES="800-4400 1000-1000 1200-3000 1000-4000 2000-2000"
MODES="ks-full ks-cg ks-cg-ws fks-cg-ws"

# Expected counts per family (p800-4400 in testbed_b only has 25)
expected() {
    local tb=$1 fam=$2
    if [[ "$tb" == "b" && "$fam" == "800-4400" ]]; then echo 25; else echo 30; fi
}

print_table() {
    printf "\n%-14s  %-12s  %9s  %9s  %9s  %9s\n" "family" "testbed" "ks-full" "ks-cg" "ks-cg-ws" "fks-cg-ws"
    printf "%-14s  %-12s  %9s  %9s  %9s  %9s\n" "--------------" "--------" "---------" "---------" "---------" "---------"

    for TB in a b; do
        for FAM in $FAMILIES; do
            EXP=$(expected "$TB" "$FAM")
            row_str="$(printf "%-14s  tb%s" "$FAM" "$TB")"
            for MODE in $MODES; do
                CSV="$RESULTS/tb${TB}_${FAM}_${MODE}.csv"
                if [[ -f "$CSV" ]]; then
                    DONE=$(tail -n +2 "$CSV" | grep -c ".")
                else
                    DONE=0
                fi
                row_str="$row_str  $(printf "%4d/%-3d" "$DONE" "$EXP")"
            done
            printf "%s\n" "$row_str"
        done
    done
    printf "\nLast updated: %s\n" "$(date)"
}

if [[ "$1" == "--watch" ]]; then
    while true; do
        clear
        print_table
        sleep 60
    done
else
    print_table
fi
