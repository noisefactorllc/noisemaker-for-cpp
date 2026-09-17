#!/usr/bin/env bash
# Run the full Python unittest discovery of a repo in N parallel shards (modules round-robin by file size).
# usage: pyshards.sh <repo> <shards> <log-prefix> [authority]
set -uo pipefail
repo=$1; shards=$2; prefix=$3; authority=${4:-}
cd "$repo"
export PYTHONDONTWRITEBYTECODE=1
if [ -n "$authority" ]; then
  export NOISEMAKER_CPU_ROOT=${NOISEMAKER_CPU_ROOT:?} NOISEMAKER_CPU_AUTHORITY_LEDGER=${NOISEMAKER_CPU_AUTHORITY_LEDGER:-$NOISEMAKER_CPU_ROOT.ledger.sha256}
fi
modules=$(ls -S tests/test_*.py | sed 's#tests/##; s#\.py$##')
i=0
declare -a lists
for m in $modules; do
  lists[$((i % shards))]+=" tests.$m"
  i=$((i + 1))
done
pids=()
for s in $(seq 0 $((shards - 1))); do
  python3 -B -m unittest ${lists[$s]} > "$prefix.shard$s.log" 2>&1 &
  pids+=($!)
done
status=0
for p in "${pids[@]}"; do wait "$p" || status=1; done
for s in $(seq 0 $((shards - 1))); do
  echo "shard $s: $(grep -E '^(Ran|OK|FAILED)' "$prefix.shard$s.log" | tr '\n' ' ')"
done
echo "PYSHARDS DONE status=$status"
