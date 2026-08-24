#!/bin/bash
# Task 29 checklist items 4-6: fresh Debug, Release, and sanitizer lanes plus
# the Focus-specific counter test. Every stage's exit code is captured on its
# own; no pipe or loop can mask a red leg.
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
    RESULTS+=("$(printf '%-44s exit=%-3d %s' "$label" "$status" \
        "$([ $status -eq 0 ] && echo PASS || echo FAIL)")")
    if [ $status -ne 0 ]; then
        FAILED=$((FAILED + 1))
        printf '\n===== FAIL: %s (exit %d) =====\n%s\n\n' "$label" "$status" "$out"
    else
        printf '[PASS] %-44s %s\n' "$label" "$(printf '%s' "$out" | tail -1)"
    fi
    printf '%s\n' "$out" > "$SDD/task-30-gate-native-${label// /-}.log"
}

cd "$REPO" || exit 2

lane() {
    local name="$1" dir="$2"; shift 2
    rm -rf "$dir"
    run "$name configure" cmake -S . -B "$dir" "$@"
    run "$name build" cmake --build "$dir" --target noisemaker-cpu-tests -j8
    run "$name ctest" ctest --test-dir "$dir" --output-on-failure
}

lane "debug" "build-task30-final-debug" -DCMAKE_BUILD_TYPE=Debug
lane "release" "build-task30-final-release" -DCMAKE_BUILD_TYPE=Release

# Sanitizer lane. Apple platforms do not support LeakSanitizer; the documented
# procedure is to attempt the normal leak setting first, record the platform
# limitation, then retry with leak detection disabled. The first attempt is
# never silently skipped.
SAN_DIR=build-task30-final-sanitize
rm -rf "$SAN_DIR"
run "sanitize configure" cmake -S . -B "$SAN_DIR" -DCMAKE_BUILD_TYPE=Debug \
    -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer" \
    -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
run "sanitize build" cmake --build "$SAN_DIR" --target noisemaker-cpu-tests -j8

printf '\n--- sanitizer attempt 1: leak detection ENABLED (expected to be unsupported on Apple) ---\n'
ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 \
    "./$SAN_DIR/noisemaker-cpu-tests" > "$SDD/task-30-sanitize-attempt1.log" 2>&1
ATTEMPT1=$?
printf 'attempt 1 exit=%d\n' "$ATTEMPT1"
tail -5 "$SDD/task-30-sanitize-attempt1.log"

if [ $ATTEMPT1 -eq 0 ]; then
    RESULTS+=("$(printf '%-44s exit=0   PASS (leaks enabled)' 'sanitize run')")
else
    printf '\n--- attempt 1 non-zero; retrying with leak detection DISABLED ---\n'
    ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 \
        "./$SAN_DIR/noisemaker-cpu-tests" > "$SDD/task-30-sanitize-attempt2.log" 2>&1
    ATTEMPT2=$?
    printf 'attempt 2 exit=%d\n' "$ATTEMPT2"
    tail -5 "$SDD/task-30-sanitize-attempt2.log"
    if [ $ATTEMPT2 -eq 0 ]; then
        RESULTS+=("$(printf '%-44s exit=0   PASS (leaks disabled retry; attempt1 exit=%d)' \
            'sanitize run' "$ATTEMPT1")")
    else
        FAILED=$((FAILED + 1))
        RESULTS+=("$(printf '%-44s exit=%-3d FAIL' 'sanitize run' "$ATTEMPT2")")
    fi
fi

printf '\n========== SUMMARY ==========\n'
for line in "${RESULTS[@]}"; do printf '%s\n' "$line"; done
printf '=============================\nfailures=%d\n' "$FAILED"
exit $([ "$FAILED" -eq 0 ] && echo 0 || echo 1)
