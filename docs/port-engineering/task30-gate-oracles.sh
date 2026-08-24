#!/bin/bash
# Task 29 checklist item 7: strict corpus + canonical generator checks and every
# Task 15-29 oracle generator --check. Fail-fast, every exit code captured
# individually so a shell loop cannot mask a failure with the last command.
set -u

REPO=.
SDD=docs/port-engineering
FAILED=0
declare -a RESULTS=()

run() {
    local label="$1"; shift
    local out status
    out="$("$@" 2>&1)"
    status=$?
    RESULTS+=("$(printf '%-46s exit=%-3d %s' "$label" "$status" \
        "$([ $status -eq 0 ] && echo PASS || echo FAIL)")")
    if [ $status -ne 0 ]; then
        FAILED=$((FAILED + 1))
        printf '\n===== FAIL: %s (exit %d) =====\n%s\n\n' "$label" "$status" "$out"
    else
        printf '[PASS] %-46s %s\n' "$label" "$(printf '%s' "$out" | tail -1)"
    fi
}

cd "$REPO" || exit 2

run "check_corpus --check" python3 -m tools.glslcpp.check_corpus --check
run "check_semantics --check" python3 -m tools.glslcpp.check_semantics --check
run "generate_typed_slice --check" python3 -m tools.glslcpp.generate_typed_slice --check
run "generate_kernels --check" python3 -m tools.glslcpp.generate_kernels --check

cd "$SDD" || exit 2
for n in 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29; do
    generator="task-${n}-oracle-generator.mjs"
    [ -f "$generator" ] || { echo "MISSING $generator"; FAILED=$((FAILED + 1)); continue; }
    run "oracle task-${n} --check" node "$generator" --check
done

run "oracle task-30 --check" node \
    "$SDD/future-precompute/task30/extrude_oracle_generator.mjs" --check

printf '\n========== SUMMARY ==========\n'
for line in "${RESULTS[@]}"; do printf '%s\n' "$line"; done
printf '=============================\nfailures=%d\n' "$FAILED"
exit $([ "$FAILED" -eq 0 ] && echo 0 || echo 1)
