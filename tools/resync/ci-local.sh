#!/usr/bin/env bash
# Local reproduction of noisemaker-for-cpp .github/workflows/ci.yml.
# usage: ci-local.sh <source-tree> <authority-dir> <log-dir> [jobs...]
# jobs: generator native sanitizers python parity consumer (default: all)
set -uo pipefail
SRC=$(cd "$1" && pwd); AUTH=$(cd "$2" && pwd); LOG=$3; shift 3
JOBS=${*:-generator native parity consumer sanitizers python}
mkdir -p "$LOG"; cd "$SRC"
export PYTHONDONTWRITEBYTECODE=1
status() { echo "$(date +%H:%M:%S) $1 $2" | tee -a "$LOG/summary.txt"; }
result=0
run() { local name=$1; shift; status START "$name"; if "$@" >"$LOG/$name.log" 2>&1; then status PASS "$name"; else result=1; status FAIL "$name"; fi; }

for job in $JOBS; do case $job in
generator)
  run gen-check_corpus python3 -m tools.glslcpp.check_corpus --check
  run gen-check_semantics python3 -m tools.glslcpp.check_semantics --check
  run gen-typed_slice python3 -m tools.glslcpp.generate_typed_slice --check
  run gen-kernels python3 -m tools.glslcpp.generate_kernels --check ;;
native)
  run native-configure cmake -S . -B build-ci -DCMAKE_BUILD_TYPE=Release
  run native-build cmake --build build-ci --target noisemaker-cpu-tests -j10
  run native-ctest ctest --test-dir build-ci --output-on-failure ;;
sanitizers)
  run san-configure cmake -S . -B build-san -DCMAKE_BUILD_TYPE=Debug \
    "-DCMAKE_CXX_FLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer" \
    "-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=address,undefined"
  run san-build cmake --build build-san --target noisemaker-cpu-tests -j10
  ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 run san-run ./build-san/noisemaker-cpu-tests ;;
python)
  run python-suite python3 -m unittest discover -s tests -p 'test_*.py' -q ;;
parity)
  run parity-configure cmake -S . -B build-parity -DCMAKE_BUILD_TYPE=Release
  run parity-build cmake --build build-parity --target noisemaker-dsl-cpu-case -j10
  NOISEMAKER_CPU_ROOT="$AUTH" NOISEMAKER_CPU_AUTHORITY_LEDGER="$AUTH.ledger.sha256" \
  NOISEMAKER_DSL_CPU_CASE="$SRC/build-parity/noisemaker-dsl-cpu-case" \
    run parity-lane python3 -B -m unittest tests.test_dsl_corpus_parity -v
  NOISEMAKER_CPU_ROOT="$AUTH" NOISEMAKER_CPU_AUTHORITY_LEDGER="$AUTH.ledger.sha256" \
  NOISEMAKER_DSL_CPU_CASE="$SRC/build-parity/noisemaker-dsl-cpu-case" \
    run parity-sweep python3 -B tools/parity/sweep.py --out "$LOG/sweep" --variants 6 --gate kit --force
  NOISEMAKER_CPU_ROOT="$AUTH" NOISEMAKER_CPU_AUTHORITY_LEDGER="$AUTH.ledger.sha256" \
  NOISEMAKER_DSL_CPU_CASE="$SRC/build-parity/noisemaker-dsl-cpu-case" \
    run parity-sweep-defines python3 -B tools/parity/sweep.py --out "$LOG/sweep-defines" --define-enum --gate kit --force
  run authority-drift python3 -B tools/dsl/check_authority_drift.py --cpu-root "$AUTH"
  run kit-coverage node export-kit/check-authority-coverage.mjs --cpu-root "$AUTH" ;;
consumer)
  B=$LOG/consumer; rm -rf "$B"; mkdir -p "$B"
  run consumer bash -c "set -euxo pipefail
    cmake -S '$SRC' -B '$B/build' -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX='$B/prefix'
    cmake --build '$B/build' --target noisemaker-cpu --parallel 10
    cmake --install '$B/build'
    test -f '$B/prefix/lib/cmake/noisemaker-for-cpp/noisemaker-for-cppConfig.cmake'
    test -f '$B/prefix/include/noisemaker/generated/catalog.hpp'
    cmake -S '$SRC/tests/cmake_package_consumer' -B '$B/cbuild' -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH='$B/prefix'
    cmake --build '$B/cbuild' --parallel 10
    '$B/cbuild/noisemaker-package-consumer'" ;;
esac; done
status DONE all
exit "$result"
