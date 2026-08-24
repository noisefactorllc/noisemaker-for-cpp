#!/usr/bin/env bash
# Builds the standalone wormhole-deposit verification harness with the
# mandatory flags (-ffp-contract=off is non-negotiable -- see
# wormhole_deposit.hpp's header comment and wormhole-report.md for why).
set -euo pipefail
cd "$(dirname "$0")"

CXX="${CXX:-clang++}"
"$CXX" -std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off -O2 \
  verify_wormhole.cpp -o verify_wormhole

echo "built ./verify_wormhole"
