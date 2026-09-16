#!/bin/bash
# run_differential.sh -- runs the full v8-math differential harness for
# every function, on one (node binary, cpp probe binary, arch label)
# triple, at the given input count. Writes a JSON result file per
# function under $OUT_DIR, and a combined summary.
#
# Usage: run_differential.sh <node-bin> <cpp-probe-bin> <arch-label> <count> <out-dir>
set -euo pipefail
NODE_BIN="$1"
CPP_PROBE="$2"
ARCH_LABEL="$3"
COUNT="$4"
OUT_DIR="$5"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$OUT_DIR"

UNARY="sin cos tan asin acos atan exp expm1 log log2 tanh"
BINARY="pow atan2 hypot2"
TERNARY="hypot3"

summary="$OUT_DIR/summary_${ARCH_LABEL}.jsonl"
: > "$summary"

for fn in $UNARY; do
  in_file="$OUT_DIR/${fn}_inputs.bin"
  v8_file="$OUT_DIR/${fn}_v8_${ARCH_LABEL}.bin"
  cpp_file="$OUT_DIR/${fn}_cpp_${ARCH_LABEL}.bin"
  [ -f "$in_file" ] || "$NODE_BIN" "$SCRIPT_DIR/gen_inputs.mjs" "$fn" "$COUNT" "$in_file" >/dev/null
  "$NODE_BIN" "$SCRIPT_DIR/node_probe.mjs" "$fn" "$in_file" "$v8_file" 2>>"$OUT_DIR/node.log"
  "$CPP_PROBE" "$fn" "$in_file" "$cpp_file" 2>>"$OUT_DIR/cpp.log"
  "$NODE_BIN" "$SCRIPT_DIR/compare.mjs" "$fn" "$in_file" "$v8_file" "$cpp_file" 1 >> "$summary.tmp"
  echo "---" >> "$summary.tmp"
done

for fn in $BINARY; do
  in_file="$OUT_DIR/${fn}_inputs.bin"
  v8_file="$OUT_DIR/${fn}_v8_${ARCH_LABEL}.bin"
  cpp_file="$OUT_DIR/${fn}_cpp_${ARCH_LABEL}.bin"
  [ -f "$in_file" ] || "$NODE_BIN" "$SCRIPT_DIR/gen_inputs.mjs" "$fn" "$COUNT" "$in_file" >/dev/null
  "$NODE_BIN" "$SCRIPT_DIR/node_probe.mjs" "$fn" "$in_file" "$v8_file" 2>>"$OUT_DIR/node.log"
  "$CPP_PROBE" "$fn" "$in_file" "$cpp_file" 2>>"$OUT_DIR/cpp.log"
  "$NODE_BIN" "$SCRIPT_DIR/compare.mjs" "$fn" "$in_file" "$v8_file" "$cpp_file" 2 >> "$summary.tmp"
  echo "---" >> "$summary.tmp"
done

for fn in $TERNARY; do
  in_file="$OUT_DIR/${fn}_inputs.bin"
  v8_file="$OUT_DIR/${fn}_v8_${ARCH_LABEL}.bin"
  cpp_file="$OUT_DIR/${fn}_cpp_${ARCH_LABEL}.bin"
  [ -f "$in_file" ] || "$NODE_BIN" "$SCRIPT_DIR/gen_inputs.mjs" "$fn" "$COUNT" "$in_file" >/dev/null
  "$NODE_BIN" "$SCRIPT_DIR/node_probe.mjs" "$fn" "$in_file" "$v8_file" 2>>"$OUT_DIR/node.log"
  "$CPP_PROBE" "$fn" "$in_file" "$cpp_file" 2>>"$OUT_DIR/cpp.log"
  "$NODE_BIN" "$SCRIPT_DIR/compare.mjs" "$fn" "$in_file" "$v8_file" "$cpp_file" 3 >> "$summary.tmp"
  echo "---" >> "$summary.tmp"
done

mv "$summary.tmp" "$summary"
echo "Wrote $summary"
