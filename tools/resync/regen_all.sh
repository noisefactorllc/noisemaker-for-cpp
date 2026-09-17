#!/usr/bin/env bash
# Regenerate every generated artifact of noisemaker-for-cpp, in dependency order, to a fixed point.
# usage: NOISEMAKER_CPU_ROOT=<pinned cpu authority> NOISEMAKER_SHADER_GIT=<noisemaker git> tools/resync/regen_all.sh <repo>
set -euo pipefail
cd "$1"
A=${NOISEMAKER_CPU_ROOT:?set NOISEMAKER_CPU_ROOT to the pinned noisemaker-for-cpu checkout}
G=${NOISEMAKER_SHADER_GIT:?set NOISEMAKER_SHADER_GIT to a noisemaker git checkout}
export PYTHONDONTWRITEBYTECODE=1 NOISEMAKER_CPU_AUTHORITY_LEDGER=${NOISEMAKER_CPU_AUTHORITY_LEDGER:-$A.ledger.sha256}
HERE=$(cd "$(dirname "$0")" && pwd)
step() { echo "== $*"; }

step corpus + semantics
python3 -m tools.glslcpp.check_corpus --check
python3 -m tools.glslcpp.check_semantics --check

step legacy Task-5 kernels
python3 -m tools.glslcpp.generate_kernels --write
python3 -m tools.glslcpp.generate_kernels --check

step typed slice / backend compatibility fixed point
fixed=0
for i in 1 2 3 4; do
  python3 -m tools.glslcpp.generate_typed_slice --write
  python3 -m tools.dsl.generate_backend_compatibility --write --cpu-root "$A" --shader-git "$G"
  if python3 -m tools.glslcpp.generate_typed_slice --check && \
     python3 -m tools.dsl.generate_backend_compatibility --check --cpu-root "$A" --shader-git "$G"; then fixed=1; break; fi
done
[ "$fixed" = 1 ] || { echo "no typed/compat fixed point"; exit 1; }

step pin compatibility sha in consumers
new=$(shasum -a 256 src/effects/generated/backend_compatibility.json | cut -d' ' -f1)
old=$(grep -oE 'COMPATIBILITY_SHA256 = "[0-9a-f]{64}"' tools/dsl/generate_effect_catalog.py | grep -oE '[0-9a-f]{64}')
if [ "$old" != "$new" ]; then
  for f in tools/dsl/generate_effect_catalog.py tools/dsl/generate_executable_corpus.mjs tools/dsl/js_frontend_oracle.mjs src/effects/registry.cpp; do
    sed -i '' "s/$old/$new/g" "$f"
  done
fi
echo "compat sha $new"

step effect catalog + registry live pins
python3 -m tools.dsl.generate_effect_catalog --cpu-root "$A" --shader-git "$G"
python3 -m tools.dsl.generate_effect_catalog --check --cpu-root "$A" --shader-git "$G"
python3 "$HERE/repin_registry.py" .

step DSL executable corpus
node tools/dsl/generate_executable_corpus.mjs --cpu-root "$A" --output "$PWD/tests/fixtures/dsl/executable-corpus.json"
python3 -c "import json;print(json.load(open('tests/fixtures/dsl/executable-corpus.json'))['manifestSha256'])" > tests/oracles/dsl_executable_corpus.sha256

step DSL compiler oracle stream
node tools/dsl/js_frontend_oracle.mjs --compiler --cpu-root "$A" --fixtures tests/fixtures/dsl/compiler-cases.json --output "$PWD/tests/oracles/dsl_compiler_expected.txt"
old=$(grep -oE "EXPECTED_STREAM_SHA256 = '[0-9a-f]{64}'" tools/dsl/js_frontend_oracle.mjs | grep -oE '[0-9a-f]{64}')
new=$(shasum -a 256 tests/oracles/dsl_compiler_expected.txt | cut -d' ' -f1)
[ "$old" = "$new" ] || { sed -i '' "s/$old/$new/" tools/dsl/js_frontend_oracle.mjs; sed -i '' "s/$old/$new/" tests/test_dsl_frontend_oracle.py; }
node tools/dsl/js_frontend_oracle.mjs --compiler --cpu-root "$A" --fixtures tests/fixtures/dsl/compiler-cases.json --output "${TMPDIR:-/tmp}/.compiler-check.txt" --check "$PWD/tests/oracles/dsl_compiler_expected.txt"
cmp "${TMPDIR:-/tmp}/.compiler-check.txt" tests/oracles/dsl_compiler_expected.txt && rm -f "${TMPDIR:-/tmp}/.compiler-check.txt"

step export kit compat list
node export-kit/generate-compat.mjs
node export-kit/generate-compat.mjs --check
echo "REGEN OK"
