#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cpu_root=${NOISEMAKER_CPU_ROOT:?NOISEMAKER_CPU_ROOT must name the immutable CPU snapshot}
live_root=${NOISEMAKER_FOR_CPU:?NOISEMAKER_FOR_CPU must name the non-symlink live checkout}
export NOISEMAKER_FOR_CPU="$live_root"
node "$root/docs/port-engineering/remap-parity/remap_oracle_generator.mjs" --self-test --cpu-root "$cpu_root"
python3 -B "$root/tools/glslcpp/generate_remap_native_oracle_include.py" --self-test
python3 -B "$root/tools/glslcpp/generate_remap_native_oracle_include.py" --check
cat <<'CPP' | c++ -std=c++20 -I "$root" -x c++ -fsyntax-only -
#include "tests/oracles/remap_expected.inc"
int main() {
  if (remap_oracle::kCases.size() != 10 || remap_oracle::kMutations.size() != 7 || remap_oracle::kBindingAbi.size() != 11) return 1;
  const auto& c = remap_oracle::kCases[0];
  (void)c.name; (void)c.width; (void)c.height; (void)c.salt; (void)c.controls.zone_count;
  (void)c.controls.bg_color; (void)c.controls.bg_alpha; (void)c.controls.smooth_edge;
  (void)c.controls.tile_offset; (void)c.controls.full_resolution; (void)c.controls.zones;
  (void)c.input_words; (void)c.output_words; (void)c.output_alpha_float_words;
  (void)c.input_rgba8_bytes; (void)c.output_rgba8_bytes; (void)c.output_alpha_rgba8_bytes;
  (void)c.repeat_identity; (void)c.public_identity; (void)c.input_immutable_exact_bits;
  const auto& m = remap_oracle::kMutations[0]; const auto& r = m.results[0];
  (void)m.name; (void)m.anchor; (void)m.replacement; (void)m.source_sha256; (void)m.mutated_factory_text_sha256;
  (void)m.results; (void)m.witness_cases; (void)m.control_cases; (void)r.float32_witness.index;
  (void)r.float32_witness.expected_word; (void)r.rgba8_witness.actual_byte; (void)remap_oracle::kClaimBoundaries;
  return 0;
}
CPP
echo "remap oracle standalone smoke: ok"
