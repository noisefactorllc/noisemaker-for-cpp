from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from tools.glslcpp.check_corpus import REVISION
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.runtime_loop_bound_profile import (
    PROFILE, ROLL_KEY, apply_runtime_loop_bound, authenticate_runtime_loop_bound,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]


def unproved():
    corpus = ROOT / 'tools/glslcpp/corpus' / REVISION
    source = corpus / 'sources/synth/roll/roll.glsl'
    if not source.exists():
        source = corpus / 'pending-sources/synth/roll/roll.glsl'
    raw = source.read_text()
    return analyze_program(parse_program(raw, ROLL_KEY, {}), ROLL_KEY)


class RollAdmissionTests(unittest.TestCase):
    def test_ratchet_promotes_both_required_roll_carriers(self):
        from tools.glslcpp import corpus_ratchet
        from tools.glslcpp.frontend.ceil_admission_profile import PROFILE as CEIL_PROFILE
        corpus = ROOT / 'tools/glslcpp/corpus' / REVISION
        manifest = json.loads((corpus / 'manifest.json').read_text())
        entry = next(row for row in manifest['programs'] if row['program_key'] == ROLL_KEY)
        metadata = json.loads((corpus / 'metadata.json').read_text())
        spec = json.loads((ROOT / 'tools/glslcpp/typed_slice.json').read_text())
        spec['programs'] = [row for row in spec['programs'] if row['program_key'] != ROLL_KEY]
        with tempfile.TemporaryDirectory() as directory:
            repository = pathlib.Path(directory)
            target = repository / 'tools/glslcpp/typed_slice.json'
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(spec))
            corpus_ratchet._add_typed_slice_rows(repository, [entry], metadata)
            row = next(row for row in json.loads(target.read_text())['programs']
                       if row['program_key'] == ROLL_KEY)
            self.assertEqual(row, {'program_key': ROLL_KEY, 'defines': {},
                                   'runtime_loop_bound_profile': PROFILE,
                                   'ceil_admission_profile': CEIL_PROFILE})

    def test_native_factory_checks_height_before_running_the_loop(self):
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend.ceil_admission_profile import PROFILE as CEIL_PROFILE
        program = unproved()
        digest = hashlib.sha256(program.raw_source.encode()).hexdigest()
        applied = apply_runtime_loop_bound(program, digest, PROFILE)
        emitted = render_typed_cpp(applied, ROLL_KEY, digest, runtime_loop_bound_profile=PROFILE,
                                  ceil_admission_profile=CEIL_PROFILE, factory='bind_roll_probe')
        unit = '''
#include "noisemaker/kernel.hpp"
#include "noisemaker/sampler.hpp"
#include <cmath>
#include <limits>
namespace noisemaker {
''' + emitted + r'''
}
int main() {
  using namespace noisemaker;
  const float infinity = std::numeric_limits<float>::infinity();
  for (float height : {0.0F, -1.0F, infinity, -infinity,
                       std::numeric_limits<float>::quiet_NaN(), std::nextafter(1.0F, 0.0F)}) {
    glsl::Bindings bindings;
    bindings.set_uniform("fullResolution", glsl::Vec2(1.0F, height));
    try { (void)bind_roll_probe(bindings); return 1; }
    catch (const glsl::KernelBindingError& error) {
      if (std::string(error.what()).find("fullResolution.y must be finite and at least 1") == std::string::npos) return 2;
    }
  }
  Surface texture(1U, 1U);
  for (float height : {1.0F, 512.0F, std::numeric_limits<float>::max()}) {
    glsl::Bindings bindings;
    bindings.set_uniform("fullResolution", glsl::Vec2(1.0F, height));
    bindings.set_uniform("resolution", glsl::Vec2(1.0F, height));
    bindings.set_uniform("tileOffset", glsl::Vec2(0.0F));
    bindings.set_uniform("lineColor", glsl::DVec3(1.0));
    for (const auto name : {"time", "deltaTime", "gain", "speed", "midiClockCount"}) bindings.set_uniform(name, 0.0);
    bindings.set_texture("feedbackTex", texture);
    bindings.set_texture("noteGridTex", texture);
    auto kernel = bind_roll_probe(bindings);
    glsl::PixelContext context;
    context.frag_coord = glsl::Vec4(.5F, .5F, 0.0F, 1.0F);
    glsl::Vec4 output;
    kernel.run_pixel(context, output);
    for (std::size_t lane = 0; lane < 4U; ++lane) if (!std::isfinite(output[lane])) return 3;
  }
}
'''
        compiler = shutil.which('c++') or shutil.which('clang++')
        self.assertIsNotNone(compiler)
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / 'probe.cpp'
            binary = pathlib.Path(directory) / 'probe'
            source.write_text(unit)
            result = subprocess.run([compiler, '-std=c++20', '-ffp-contract=off', '-I', str(ROOT / 'include'),
                                     str(source), *(str(ROOT / 'src' / f'{name}.cpp') for name in
                                     ['surface', 'numeric', 'sampler', 'glsl_runtime', 'kernel']), '-o', str(binary)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_both_authorities_emit_a_guard_before_binding_state(self):
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.generate_typed_slice import APPROVED_CAPABILITIES, validate_capabilities
        from tools.glslcpp.frontend.ceil_admission_profile import PROFILE as CEIL_PROFILE
        program = unproved()
        digest = hashlib.sha256(program.raw_source.encode()).hexdigest()
        applied = apply_runtime_loop_bound(program, digest, PROFILE)
        kwargs = dict(runtime_loop_bound_profile=PROFILE, ceil_admission_profile=CEIL_PROFILE)
        validate_capabilities(applied, APPROVED_CAPABILITIES, source_hash=digest, **kwargs)
        emitted = render_typed_cpp(applied, ROLL_KEY, digest, **kwargs)
        guard = 'if (!std::isfinite(fullResolution[1]) || fullResolution[1] < 1.0F)'
        self.assertEqual(emitted.count(guard), 1)
        self.assertLess(emitted.index(guard), emitted.index('std::make_shared<typed_kernel::State>'))

    def test_source_loop_is_not_admitted_without_its_bound(self):
        program = unproved()
        self.assertEqual(program.counted_loop_proof.unproved_loop_count, 1)
        with self.assertRaisesRegex(ValueError, 'exact profile carrier required'):
            apply_runtime_loop_bound(program, hashlib.sha256(program.raw_source.encode()).hexdigest(), None)

    def test_resolution_bound_covers_the_one_pixel_height(self):
        program = unproved()
        digest = hashlib.sha256(program.raw_source.encode()).hexdigest()
        contract = authenticate_runtime_loop_bound(program, digest, PROFILE)
        self.assertEqual((contract.minimum, contract.maximum), (1, 768))
        applied = apply_runtime_loop_bound(program, digest, PROFILE)
        summary = applied.counted_loop_proof
        self.assertEqual((summary.loop_count, summary.unproved_loop_count,
                          summary.max_lexical_product, summary.entrypoint_charge),
                         (1, 0, 1537, 1537))

    def test_source_and_forged_ir_do_not_inherit_bound(self):
        program = unproved()
        digest = hashlib.sha256(program.raw_source.encode()).hexdigest()
        for changed in (
            dataclasses.replace(program, key='synth/foreign:foreign'),
            dataclasses.replace(program, raw_source=program.raw_source + '\n'),
            dataclasses.replace(program, functions=()),
        ):
            with self.assertRaises(ValueError):
                apply_runtime_loop_bound(changed, digest, PROFILE)


if __name__ == '__main__':
    unittest.main()
