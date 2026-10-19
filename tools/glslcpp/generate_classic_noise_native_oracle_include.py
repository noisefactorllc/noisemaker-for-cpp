#!/usr/bin/env python3
"""Fail-closed materializer for the Classic Noise canonical CPU oracle."""
from __future__ import annotations
import argparse, copy, hashlib, json, math, pathlib, re, struct, sys

# Revision authenticated by the immutable oracle capture.
CORPUS_REVISION = "6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d"

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/classic-noise-parity"
ORACLE = PACKAGE / "classic-noise-oracles.json"
GENERATOR = PACKAGE / "classic_noise_oracle_generator.mjs"
REPORT = PACKAGE / "classic-noise-oracle-report.md"
TARGET = ROOT / "tests/oracles/classic_noise_expected.inc"
SOURCE = f"tools/glslcpp/corpus/{CORPUS_REVISION}/sources/classicNoisedeck/noise/noise.glsl"
SCHEMA = "noisemaker-for-cpp.classic-noise.pixel-parity.v1"
KEY = "classicNoisedeck/noise:noise"
FACTORY_SHA256 = "1a082f9e24533bf5e7f0e4cdb61469fb8a3c01c580c468f4760a3d9463b095a2"
WORD = re.compile(r"^0x[0-9a-f]{8}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
DEFINES = {"NOISE_TYPE": 10, "REFRACT_MODE": 2, "LOOP_OFFSET": 300, "METRIC": 0, "COLOR_MODE": 6}
NAMES = ["NOISE_TYPE", "REFRACT_MODE", "LOOP_OFFSET", "METRIC", "COLOR_MODE", "time", "seed", "resolution", "tileOffset", "fullResolution", "xScale", "yScale", "octaves", "ridges", "refractAmt", "kaleido", "loopScale", "speed", "paletteMode", "paletteOffset", "paletteAmp", "paletteFreq", "palettePhase", "cyclePalette", "rotatePalette", "repeatPalette", "hueRange", "hueRotation", "wrap"]
COMPARER_TESTS = {"good", "dimensions_before_access", "f32_short_count", "f32_long_count", "rgba8_mismatch", "signed_zero", "nan_payload", "control_mutation_rejected"}
MUTATION_NAMES = {"mutable-global-frame", "runtime-loop-bound", "owner-speed-control", "hue-range-factor", "refract-amount"}
RUNTIME_ABI = {"NOISE_TYPE":"int32", "REFRACT_MODE":"int32", "LOOP_OFFSET":"int32", "METRIC":"int32", "COLOR_MODE":"int32", "time":"float", "seed":"int32", "resolution":"Vec2", "tileOffset":"Vec2", "fullResolution":"Vec2", "xScale":"float", "yScale":"float", "octaves":"int32", "ridges":"bool", "refractAmt":"float", "kaleido":"float", "loopScale":"float", "speed":"float", "paletteMode":"int32", "paletteOffset":"Vec3", "paletteAmp":"Vec3", "paletteFreq":"Vec3", "palettePhase":"Vec3", "cyclePalette":"int32", "rotatePalette":"float", "repeatPalette":"float", "hueRange":"float", "hueRotation":"float", "wrap":"bool"}
SOURCE_ABI = {"time":"float", "seed":"int", "resolution":"vec2", "tileOffset":"vec2", "fullResolution":"vec2", "xScale":"float", "yScale":"float", "octaves":"int", "ridges":"bool", "refractAmt":"float", "kaleido":"float", "loopScale":"float", "speed":"float", "paletteMode":"int", "paletteOffset":"vec3", "paletteAmp":"vec3", "paletteFreq":"vec3", "palettePhase":"vec3", "cyclePalette":"int", "rotatePalette":"float", "repeatPalette":"float", "hueRange":"float", "hueRotation":"float", "wrap":"bool"}
EXPECTED_CLOSURE = [('src/csl/glsl-kernel.js', 'f5664e2c90289c82f7109cea910fb5de71ae08f5c2204fb569299a9c49a645ff'), ('src/csl/glsl-runtime.js', 'ad71e22deeb31ad1f19f81923704c9ad0e1ef0475f9a333e0d5fe9088051eebd'), ('src/csl/metal-division.js', '104cda4fda758fcdfd20f69264a92c1190830102814aec8aa9706058642ce2a8'), ('src/csl/metal-reciprocal-data.js', '08905259e72a066e77675f98b9700d6c3a6467662f5de562d8f8e1e14d082c87'), ('src/csl/metal-reciprocal-grid.js', 'bd6613830c4239ff9b21a4157875a7c92ced898fd706e735527f39552be11e39'), ('src/csl/runtime.js', 'a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee'), ('src/effects/adapters/bit-effects.js', '5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7'), ('src/effects/adapters/crt.js', 'c37f70e15b6481b2f870761bf103529cd45cf6e5e714a0a6fd731dbe90c1c73f'), ('src/effects/adapters/f32-color.js', 'b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046'), ('src/effects/adapters/fractal.js', '73bb60668d98a142edcd535c146527945af445baa694595da2a19fe0a649e804'), ('src/effects/adapters/index.js', 'dd2ca7681884fbc3fa2687faeb52aced50076a5f0856736b63831e859073d22e'), ('src/effects/adapters/julia.js', '0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5'), ('src/effects/adapters/median.js', 'e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583'), ('src/effects/adapters/palette.js', '8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452'), ('src/effects/adapters/remap.js', '91fd829ba2ad68fabab4124f5464994fc267daa097af4f3dd5a7e20f075f9e79'), ('src/effects/adapters/snow.js', '9acaa9c8a612e3b58e5935646bc37540146a52cda6c947cc67d5443d468f041c'), ('src/effects/catalog.js', 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4'), ('src/effects/definition.js', '4edcee437bc4fd4364f5fbf84878b9d6ca49f5799a49d876ec8df05ac0135545'), ('src/effects/generated/canonical-adapter-data.js', 'ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab'), ('src/effects/generated/canonical-kernels.js', '86fc0a3b6fdd2227341b2b59e0d7dd4177980f1b78b57e61c85c8f7525391423'), ('src/effects/generated/kernels.js', 'b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01'), ('src/effects/generated/upstream-snapshot.js', '272570c86da679801350fdfd78922635249f1475a3afffd74950c7a5136fe467'), ('src/effects/registry.js', '8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618'), ('src/runtime/automation.js', '7ec5b11a269eae6899a2e2d78a4687d87e82b0e623a8b150d0fa7d8feb09065f'), ('src/runtime/pass-runner.js', 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa'), ('src/runtime/sampler.js', '5a3e494e79f431605fecd682fd9fe6fc8437dde1332f1dc872632af59d0eeaf5'), ('src/runtime/surface.js', '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59')]
EXPECTED_CASE_PINS = [{'controls': {'name': 'origin-min', 'width': 1, 'height': 1, 'time': 0, 'seed': 1, 'resolution': [1, 1], 'tileOffset': [0, 0], 'fullResolution': [1, 1], 'xScale': 1, 'yScale': 1, 'octaves': 1, 'ridges': False, 'refractAmt': 0, 'kaleido': 1, 'loopScale': 1, 'speed': 0, 'paletteMode': 3, 'paletteOffset': [0.5, 0.5, 0.5], 'paletteAmp': [0.5, 0.5, 0.5], 'paletteFreq': [1, 1, 1], 'palettePhase': [0.3, 0.2, 0.2], 'cyclePalette': 1, 'rotatePalette': 0, 'repeatPalette': 1, 'hueRange': 0, 'hueRotation': 0, 'wrap': False}, 'f32_sha256': 'c53c479135e1e0199b4c286bd113cce3ad26caf18b6ab60f04a11ba1d302e0a3', 'rgba8_sha256': 'f8f6e67d01a7404b190b09bac91dc9498f9d4a27b61c0e10bb583905cfe0c381'}, {'controls': {'name': 'max-ridges', 'width': 5, 'height': 4, 'time': 3.25, 'seed': 100, 'resolution': [5, 4], 'tileOffset': [0, 0], 'fullResolution': [5, 4], 'xScale': 100, 'yScale': 100, 'octaves': 8, 'ridges': True, 'refractAmt': 100, 'kaleido': 32, 'loopScale': 100, 'speed': 100, 'paletteMode': 3, 'paletteOffset': [0.5, 0.5, 0.5], 'paletteAmp': [0.5, 0.5, 0.5], 'paletteFreq': [1, 1, 1], 'palettePhase': [0.3, 0.2, 0.2], 'cyclePalette': 1, 'rotatePalette': 0, 'repeatPalette': 1, 'hueRange': 100, 'hueRotation': 360, 'wrap': True}, 'f32_sha256': '391971ab136b949f7e363b81b81950aacf525187568278b7b4e32f66f2592040', 'rgba8_sha256': '76e7e623ad3d71f05ee6a26dd4ac5595ab2419a49b0c448599ea618770ef77cc'}, {'controls': {'name': 'negative-speed-offset', 'width': 4, 'height': 5, 'time': -2.5, 'seed': 37, 'resolution': [4, 5], 'tileOffset': [2, 1], 'fullResolution': [11, 9], 'xScale': 17, 'yScale': 83, 'octaves': 3, 'ridges': False, 'refractAmt': 33, 'kaleido': 7, 'loopScale': 42, 'speed': -100, 'paletteMode': 3, 'paletteOffset': [0.5, 0.5, 0.5], 'paletteAmp': [0.5, 0.5, 0.5], 'paletteFreq': [1, 1, 1], 'palettePhase': [0.3, 0.2, 0.2], 'cyclePalette': 1, 'rotatePalette': 0, 'repeatPalette': 1, 'hueRange': 25, 'hueRotation': 180, 'wrap': True}, 'f32_sha256': '56af3fd81d1487a42dbaa102322ca25dd3dc2ac2cee3643f341461fb12828854', 'rgba8_sha256': 'bb9d425b85882693b50b679aadb998a74a5cf44daeaaed6879a01062b1a24c26'}, {'controls': {'name': 'asymmetric-axis', 'width': 6, 'height': 3, 'time': 1.25, 'seed': 64, 'resolution': [6, 3], 'tileOffset': [-1, 2], 'fullResolution': [13, 8], 'xScale': 1, 'yScale': 100, 'octaves': 2, 'ridges': True, 'refractAmt': 50, 'kaleido': 2, 'loopScale': 1, 'speed': -1, 'paletteMode': 3, 'paletteOffset': [0.5, 0.5, 0.5], 'paletteAmp': [0.5, 0.5, 0.5], 'paletteFreq': [1, 1, 1], 'palettePhase': [0.3, 0.2, 0.2], 'cyclePalette': 1, 'rotatePalette': 0, 'repeatPalette': 1, 'hueRange': 1, 'hueRotation': 359, 'wrap': False}, 'f32_sha256': '1637ea3a41cfca75edb1786373ab36f3086d924b489bff617821607d8e5ca199', 'rgba8_sha256': 'b58492ef631d67080ed512c6e98a7365acd04cd69c8d37cea49cfc66bb373ed6'}, {'controls': {'name': 'refract-mid', 'width': 3, 'height': 2, 'time': 19.25, 'seed': 3, 'resolution': [3, 2], 'tileOffset': [1, -1], 'fullResolution': [10, 7], 'xScale': 75, 'yScale': 75, 'octaves': 4, 'ridges': False, 'refractAmt': 50, 'kaleido': 16, 'loopScale': 75, 'speed': 1, 'paletteMode': 3, 'paletteOffset': [0.5, 0.5, 0.5], 'paletteAmp': [0.5, 0.5, 0.5], 'paletteFreq': [1, 1, 1], 'palettePhase': [0.3, 0.2, 0.2], 'cyclePalette': 1, 'rotatePalette': 0, 'repeatPalette': 1, 'hueRange': 50, 'hueRotation': 90, 'wrap': True}, 'f32_sha256': '04ac1ed4755002c283086ccc8bd0c3383aeb9da6918b4b992f0dba38e8762034', 'rgba8_sha256': '3c6261100abb90d27416ab4c9dc0e161448a6bffed1179129371cf65b3294c8e'}, {'controls': {'name': 'seam-and-hue', 'width': 7, 'height': 3, 'time': 0.125, 'seed': 91, 'resolution': [7, 3], 'tileOffset': [0, 0], 'fullResolution': [7, 3], 'xScale': 100, 'yScale': 1, 'octaves': 8, 'ridges': True, 'refractAmt': 1, 'kaleido': 31, 'loopScale': 100, 'speed': -25, 'paletteMode': 3, 'paletteOffset': [0.5, 0.5, 0.5], 'paletteAmp': [0.5, 0.5, 0.5], 'paletteFreq': [1, 1, 1], 'palettePhase': [0.3, 0.2, 0.2], 'cyclePalette': 1, 'rotatePalette': 0, 'repeatPalette': 1, 'hueRange': 99, 'hueRotation': 1, 'wrap': False}, 'f32_sha256': '676d60c13eae209a5f14a26cd3f9173fd94cfd101a6688761c19139ff57c5b16', 'rgba8_sha256': 'dc52c608d6424cdb1e4dac1f3fc60261faaa0de147fc4d8a6276722c4f28dcb8'}, {'controls': {'name': 'dead-bindings-base', 'width': 3, 'height': 2, 'time': 19.25, 'seed': 3, 'resolution': [3, 2], 'tileOffset': [1, -1], 'fullResolution': [10, 7], 'xScale': 75, 'yScale': 75, 'octaves': 4, 'ridges': False, 'refractAmt': 50, 'kaleido': 16, 'loopScale': 75, 'speed': 1, 'paletteMode': 3, 'paletteOffset': [0.5, 0.5, 0.5], 'paletteAmp': [0.5, 0.5, 0.5], 'paletteFreq': [1, 1, 1], 'palettePhase': [0.3, 0.2, 0.2], 'cyclePalette': 1, 'rotatePalette': 0, 'repeatPalette': 1, 'hueRange': 50, 'hueRotation': 90, 'wrap': False}, 'f32_sha256': '04ac1ed4755002c283086ccc8bd0c3383aeb9da6918b4b992f0dba38e8762034', 'rgba8_sha256': '3c6261100abb90d27416ab4c9dc0e161448a6bffed1179129371cf65b3294c8e'}, {'controls': {'name': 'dead-bindings-sentinel', 'width': 3, 'height': 2, 'time': 19.25, 'seed': 3, 'resolution': [97, 53], 'tileOffset': [1, -1], 'fullResolution': [10, 7], 'xScale': 75, 'yScale': 75, 'octaves': 4, 'ridges': False, 'refractAmt': 50, 'kaleido': 16, 'loopScale': 75, 'speed': 1, 'paletteMode': 0, 'paletteOffset': [0, 0, 0], 'paletteAmp': [1, 1, 1], 'paletteFreq': [7, 11, 13], 'palettePhase': [-0.7, 0.4, 1.2], 'cyclePalette': -1, 'rotatePalette': 100, 'repeatPalette': 10, 'hueRange': 50, 'hueRotation': 90, 'wrap': True}, 'f32_sha256': '04ac1ed4755002c283086ccc8bd0c3383aeb9da6918b4b992f0dba38e8762034', 'rgba8_sha256': '3c6261100abb90d27416ab4c9dc0e161448a6bffed1179129371cf65b3294c8e'}]
EXPECTED_MUTATION_PINS = {'mutable-global-frame': {'anchor': 'var globalCoord = new $runtime.PooledFloat32Array([gl_FragCoord[0] + tileOffset[0], gl_FragCoord[1] + tileOffset[1]]);', 'replacement': 'var globalCoord = new $runtime.PooledFloat32Array([gl_FragCoord[0] + tileOffset[0], gl_FragCoord[1] + tileOffset[1] + 1]);', 'anchor_sha256': '0d11617c98d25c93f05e739688294223f87b3c5ab27f575136f9cef9750e0852', 'replacement_sha256': '0857e8fc5c5e075ef856e8f99957026440543ad1f22d500c573f5d69797f0b4c', 'mutated_factory_sha256': 'fa0c8a044dbd143345afa959d65a199501a49ae4c58095396f3b571e4413ca26', 'witnesses': ['origin-min', 'max-ridges', 'negative-speed-offset', 'asymmetric-axis', 'refract-mid', 'seam-and-hue', 'dead-bindings-base', 'dead-bindings-sentinel'], 'results': [{'case': 'origin-min', 'exact': False, 'changed_float32_lanes': 3, 'changed_rgba8_bytes': 3}, {'case': 'max-ridges', 'exact': False, 'changed_float32_lanes': 57, 'changed_rgba8_bytes': 49}, {'case': 'negative-speed-offset', 'exact': False, 'changed_float32_lanes': 60, 'changed_rgba8_bytes': 60}, {'case': 'asymmetric-axis', 'exact': False, 'changed_float32_lanes': 54, 'changed_rgba8_bytes': 34}, {'case': 'refract-mid', 'exact': False, 'changed_float32_lanes': 18, 'changed_rgba8_bytes': 18}, {'case': 'seam-and-hue', 'exact': False, 'changed_float32_lanes': 63, 'changed_rgba8_bytes': 63}, {'case': 'dead-bindings-base', 'exact': False, 'changed_float32_lanes': 18, 'changed_rgba8_bytes': 18}, {'case': 'dead-bindings-sentinel', 'exact': False, 'changed_float32_lanes': 18, 'changed_rgba8_bytes': 18}]}, 'runtime-loop-bound': {'anchor': 'for (var i = 1; i <= octaves; i++) {', 'replacement': 'for (var i = 1; i < octaves; i++) {', 'anchor_sha256': '01d7187685b3214554fcae3d2318d8596b0537236f78b7cc48ef164bef683fbe', 'replacement_sha256': 'd21fee3af24c6ee08b0eed3b29e3fa2eccb4811499f4be256696ecd9539353a9', 'mutated_factory_sha256': '4fb763f368fbc67fe647ea42a4bacb41c186b5490ac1e7b42994771b31ffe623', 'witnesses': ['origin-min', 'max-ridges', 'negative-speed-offset', 'asymmetric-axis', 'refract-mid', 'seam-and-hue', 'dead-bindings-base', 'dead-bindings-sentinel'], 'results': [{'case': 'origin-min', 'exact': False, 'changed_float32_lanes': 3, 'changed_rgba8_bytes': 3}, {'case': 'max-ridges', 'exact': False, 'changed_float32_lanes': 60, 'changed_rgba8_bytes': 20}, {'case': 'negative-speed-offset', 'exact': False, 'changed_float32_lanes': 60, 'changed_rgba8_bytes': 58}, {'case': 'asymmetric-axis', 'exact': False, 'changed_float32_lanes': 54, 'changed_rgba8_bytes': 54}, {'case': 'refract-mid', 'exact': False, 'changed_float32_lanes': 18, 'changed_rgba8_bytes': 14}, {'case': 'seam-and-hue', 'exact': False, 'changed_float32_lanes': 63, 'changed_rgba8_bytes': 19}, {'case': 'dead-bindings-base', 'exact': False, 'changed_float32_lanes': 18, 'changed_rgba8_bytes': 14}, {'case': 'dead-bindings-sentinel', 'exact': False, 'changed_float32_lanes': 18, 'changed_rgba8_bytes': 14}]}, 'owner-speed-control': {'anchor': 'var speed = $bindings["speed"];', 'replacement': 'var speed = $bindings["speed"] * 2;', 'anchor_sha256': 'd5773b533941651b0dcb30546a6d1bc4d1648f61f51058a0610f93cc9293e949', 'replacement_sha256': '3cfb6c567f23b6ee56ca6e028f219de34f54050bcea85ef424a4502e1c9ddc43', 'mutated_factory_sha256': 'e1c9acecbc43b1e66484cb3e37ab84dba04867fc8251cf0843bf945ee179854f', 'witnesses': ['max-ridges', 'negative-speed-offset', 'asymmetric-axis', 'refract-mid', 'seam-and-hue', 'dead-bindings-base', 'dead-bindings-sentinel'], 'results': [{'case': 'origin-min', 'exact': True, 'changed_float32_lanes': 0, 'changed_rgba8_bytes': 0}, {'case': 'max-ridges', 'exact': False, 'changed_float32_lanes': 60, 'changed_rgba8_bytes': 60}, {'case': 'negative-speed-offset', 'exact': False, 'changed_float32_lanes': 60, 'changed_rgba8_bytes': 58}, {'case': 'asymmetric-axis', 'exact': False, 'changed_float32_lanes': 54, 'changed_rgba8_bytes': 46}, {'case': 'refract-mid', 'exact': False, 'changed_float32_lanes': 18, 'changed_rgba8_bytes': 17}, {'case': 'seam-and-hue', 'exact': False, 'changed_float32_lanes': 63, 'changed_rgba8_bytes': 52}, {'case': 'dead-bindings-base', 'exact': False, 'changed_float32_lanes': 18, 'changed_rgba8_bytes': 17}, {'case': 'dead-bindings-sentinel', 'exact': False, 'changed_float32_lanes': 18, 'changed_rgba8_bytes': 17}]}, 'hue-range-factor': {'anchor': 'color[0] = (color[0] * hueRange) * 0.009999999776482582;', 'replacement': 'color[0] = (color[0] * hueRange) * 0.019999999552965164;', 'anchor_sha256': '37b1cfefcd1db98d7389ef143dbe05a7542407fb7cdebb9e06ebee9ba8dbfbe7', 'replacement_sha256': 'c824a77821a780c002f0d69846d5102485f65c977d1132ce888566eac5c4744b', 'mutated_factory_sha256': '6735695eef839b5298fe873d85f98222624239f7fd857e7d3cf836d72bca953f', 'witnesses': ['max-ridges', 'negative-speed-offset', 'asymmetric-axis', 'refract-mid', 'seam-and-hue', 'dead-bindings-base', 'dead-bindings-sentinel'], 'results': [{'case': 'origin-min', 'exact': True, 'changed_float32_lanes': 0, 'changed_rgba8_bytes': 0}, {'case': 'max-ridges', 'exact': False, 'changed_float32_lanes': 60, 'changed_rgba8_bytes': 60}, {'case': 'negative-speed-offset', 'exact': False, 'changed_float32_lanes': 33, 'changed_rgba8_bytes': 30}, {'case': 'asymmetric-axis', 'exact': False, 'changed_float32_lanes': 18, 'changed_rgba8_bytes': 14}, {'case': 'refract-mid', 'exact': False, 'changed_float32_lanes': 12, 'changed_rgba8_bytes': 12}, {'case': 'seam-and-hue', 'exact': False, 'changed_float32_lanes': 58, 'changed_rgba8_bytes': 56}, {'case': 'dead-bindings-base', 'exact': False, 'changed_float32_lanes': 12, 'changed_rgba8_bytes': 12}, {'case': 'dead-bindings-sentinel', 'exact': False, 'changed_float32_lanes': 12, 'changed_rgba8_bytes': 12}]}, 'refract-amount': {'anchor': 'var ref = (map(refractAmt, 0, 100, 0, 1)) / multiplier;', 'replacement': 'var ref = (map(refractAmt, 0, 100, 0, 0.5)) / multiplier;', 'anchor_sha256': '7e23e8b009bd2dc6cca439979ef62b528d177369fca9935eae06d7eb87de31d1', 'replacement_sha256': 'd92b010a2a28001378b41faf78f27b9bde10a2daf0a253853eed38fdc2e51afd', 'mutated_factory_sha256': 'b6122af5afbd0895bdb362ab84581914ff15a55f230eab4c14f65759ec7da831', 'witnesses': ['max-ridges', 'negative-speed-offset', 'asymmetric-axis', 'refract-mid', 'seam-and-hue', 'dead-bindings-base', 'dead-bindings-sentinel'], 'results': [{'case': 'origin-min', 'exact': True, 'changed_float32_lanes': 0, 'changed_rgba8_bytes': 0}, {'case': 'max-ridges', 'exact': False, 'changed_float32_lanes': 60, 'changed_rgba8_bytes': 60}, {'case': 'negative-speed-offset', 'exact': False, 'changed_float32_lanes': 60, 'changed_rgba8_bytes': 60}, {'case': 'asymmetric-axis', 'exact': False, 'changed_float32_lanes': 54, 'changed_rgba8_bytes': 54}, {'case': 'refract-mid', 'exact': False, 'changed_float32_lanes': 18, 'changed_rgba8_bytes': 18}, {'case': 'seam-and-hue', 'exact': False, 'changed_float32_lanes': 63, 'changed_rgba8_bytes': 54}, {'case': 'dead-bindings-base', 'exact': False, 'changed_float32_lanes': 18, 'changed_rgba8_bytes': 18}, {'case': 'dead-bindings-sentinel', 'exact': False, 'changed_float32_lanes': 18, 'changed_rgba8_bytes': 18}]}}

class OracleError(RuntimeError):
    pass

def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def sidecar(path: pathlib.Path) -> bytes:
    companion = pathlib.Path(f"{path}.sha256")
    if not path.is_file() or not companion.is_file():
        raise OracleError(f"missing checked asset: {path}")
    payload = path.read_bytes()
    if companion.read_text() != f"{digest(payload)}  {path.name}\n":
        raise OracleError(f"stale sidecar: {path}")
    return payload

def strict_json(payload: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise OracleError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    def parse_constant(value):
        raise OracleError(f"non-finite JSON constant: {value}")
    try:
        return json.loads(payload, object_pairs_hook=pairs, parse_constant=parse_constant)
    except OracleError:
        raise
    except (ValueError, TypeError) as error:
        raise OracleError(f"invalid JSON: {error}") from error

def exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise OracleError(f"{label}: field set drift")
    return value

def check_hash(value, label):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise OracleError(f"{label}: malformed SHA-256")

def check_words(value, count, label):
    if not isinstance(value, list) or len(value) != count or any(not isinstance(x, str) or not WORD.fullmatch(x) for x in value):
        raise OracleError(f"{label}: malformed word array")

def check_bytes(value, count, label):
    if not isinstance(value, list) or len(value) != count or any(type(x) is not int or not 0 <= x <= 255 for x in value):
        raise OracleError(f"{label}: malformed byte array")

def word_digest(words):
    return digest(b"".join(struct.pack("<I", int(word, 16)) for word in words))

def validate(document):
    top = {"schema","schema_version","program_key","effect_key","runtime_key","corpus_revision","upstream_revision","defines","exactness_contract","comparer_self_tests","authority","factory","provenance","runtime_binding_names","runtime_binding_abi","source_uniform_abi","output_abi","render_cases","mutation_anchor_cardinality","mutation_ledger","prepared_mechanisms","claim_boundaries"}
    if not isinstance(document, dict) or set(document) != top:
        raise OracleError("document fields mismatch")
    if (document["schema"], document["schema_version"], document["program_key"], document["effect_key"], document["runtime_key"]) != (SCHEMA, 1, KEY, "classicNoisedeck/noise", KEY):
        raise OracleError("identity drift")
    if document["corpus_revision"] != CORPUS_REVISION or document["upstream_revision"] != CORPUS_REVISION:
        raise OracleError("revision provenance drift")
    if document["defines"] != DEFINES or document["runtime_binding_names"] != NAMES or document["runtime_binding_abi"] != RUNTIME_ABI or document["source_uniform_abi"] != SOURCE_ABI:
        raise OracleError("define or ABI drift")
    exact(document["factory"], {"name","text_sha256","public_factory_is_canonical_identity","canonical_adapter_factories_own_key"}, "factory")
    check_hash(document["factory"]["text_sha256"], "factory hash")
    if document["factory"]["name"] != "canonicalFactory12" or document["factory"]["text_sha256"] != FACTORY_SHA256 or not document["factory"]["public_factory_is_canonical_identity"] or document["factory"]["canonical_adapter_factories_own_key"]:
        raise OracleError("factory identity drift")
    if document["output_abi"] != {"name":"fragColor","source_type":"vec4","runtime_type":"Vec4","role":"output"}:
        raise OracleError("output ABI drift")
    provenance = document["provenance"]
    exact(provenance, {"source","generator","materializer"}, "provenance")
    if provenance["source"] != {"relative_path":SOURCE,"bytes":32527,"sha256":"d86306e285a2f80dae86fe79cde92ceb89ec898ef78e6a15d140bfdf0e030bb2"}:
        raise OracleError("source provenance drift")
    exact(document["authority"], {"node_version","oracle","cpu_root_argument","immutable_snapshot","realpath_containment_checked","live_checkout_rejected","closure_cardinality","import_closure"}, "authority")
    if document["authority"]["closure_cardinality"] != len(EXPECTED_CLOSURE) or len(document["authority"]["import_closure"]) != len(EXPECTED_CLOSURE):
        raise OracleError("closure cardinality drift")
    if not all(isinstance(x, dict) and set(x) == {"relative_path","sha256"} and isinstance(x["relative_path"], str) and SHA.fullmatch(x["sha256"]) for x in document["authority"]["import_closure"]):
        raise OracleError("closure entry drift")
    closure = [(item["relative_path"], item["sha256"]) for item in document["authority"]["import_closure"]]
    if closure != EXPECTED_CLOSURE or len({path for path, _ in closure}) != len(closure):
        raise OracleError("closure path/hash drift")
    authority = document["authority"]
    if any(authority[key] is not True for key in ("immutable_snapshot", "realpath_containment_checked", "live_checkout_rejected")) or authority["cpu_root_argument"] != "<immutable-cpu-snapshot-root>" or authority["node_version"] != "v26.0.0" or authority["oracle"] != "unmodified canonical Classic Noise factory from immutable CPU snapshot":
        raise OracleError("authority contract drift")
    if set(document["comparer_self_tests"]) != COMPARER_TESTS or not all(document["comparer_self_tests"].values()):
        raise OracleError("comparer self-test failure")
    if len(document["render_cases"]) != 8:
        raise OracleError("case count drift")
    for index, case in enumerate(document["render_cases"]):
        required = {"name","width","height","time","seed","resolution","tileOffset","fullResolution","xScale","yScale","octaves","ridges","refractAmt","kaleido","loopScale","speed","paletteMode","paletteOffset","paletteAmp","paletteFreq","palettePhase","cyclePalette","rotatePalette","repeatPalette","hueRange","hueRotation","wrap","expected","f32_byte_count","rgba8_byte_count","repeat","storage","controls_snapshot"}
        exact(case, required, f"case {case.get('name')}")
        pin = EXPECTED_CASE_PINS[index]
        if {key:case[key] for key in pin["controls"]} != pin["controls"]:
            raise OracleError(f"case controls drift: {case['name']}")
        count = case["width"] * case["height"] * 4
        output = exact(case["expected"], {"f32_words_le","f32_sha256","rgba8_bytes","rgba8_sha256"}, "expected")
        check_words(output["f32_words_le"], count, "output words"); check_bytes(output["rgba8_bytes"], count, "output bytes")
        if any(word != "0x3f800000" for word in output["f32_words_le"][3::4]) or any(byte != 255 for byte in output["rgba8_bytes"][3::4]):
            raise OracleError(f"alpha lane drift: {case['name']}")
        check_hash(output["f32_sha256"], "output f32 hash"); check_hash(output["rgba8_sha256"], "output rgba8 hash")
        if output["f32_sha256"] != word_digest(output["f32_words_le"]): raise OracleError(f"f32 digest drift: {case['name']}")
        if output["rgba8_sha256"] != digest(bytes(output["rgba8_bytes"])): raise OracleError(f"rgba8 digest drift: {case['name']}")
        if output["f32_sha256"] != pin["f32_sha256"] or output["rgba8_sha256"] != pin["rgba8_sha256"]:
            raise OracleError(f"case output authority drift: {case['name']}")
        if case["f32_byte_count"] != count * 4 or case["rgba8_byte_count"] != count: raise OracleError(f"count drift: {case['name']}")
        if case["repeat"] != {"exact":True,"dimensions":True,"f32_words":True,"rgba8_bytes":True} or case["storage"] != {"distinct_surface_objects":True,"distinct_f32_backing_stores":True} or case["controls_snapshot"] != {"unchanged":True,"typed_array_bits_unchanged":True}: raise OracleError(f"runtime control drift: {case['name']}")
    if len(document["mutation_ledger"]) != 5 or {item.get("name") for item in document["mutation_ledger"]} != MUTATION_NAMES or document["mutation_anchor_cardinality"] != {"total":5,"anchors":{item["name"]:1 for item in document["mutation_ledger"]}}:
        raise OracleError("mutation census drift")
    for mutation in document["mutation_ledger"]:
        exact(mutation, {"name","anchor","replacement","anchor_sha256","replacement_sha256","mutated_factory_sha256","independent","anchor_cardinality","witnesses","results"}, "mutation")
        if mutation["name"] not in EXPECTED_MUTATION_PINS or {key:mutation[key] for key in EXPECTED_MUTATION_PINS[mutation["name"]]} != EXPECTED_MUTATION_PINS[mutation["name"]]:
            raise OracleError(f"mutation authority drift: {mutation['name']}")
        if type(mutation["independent"]) is not bool or not mutation["independent"] or type(mutation["anchor_cardinality"]) is not int or mutation["anchor_cardinality"] != 1 or not isinstance(mutation["witnesses"], list) or not mutation["witnesses"] or len(mutation["witnesses"]) != len(set(mutation["witnesses"])): raise OracleError(f"mutation witness drift: {mutation['name']}")
        for key in ("anchor_sha256","replacement_sha256","mutated_factory_sha256"): check_hash(mutation[key], f"mutation {key}")
        rows = {row["case"]: row for row in mutation["results"]}
        if set(rows) != {case["name"] for case in document["render_cases"]}: raise OracleError(f"mutation rows drift: {mutation['name']}")
        if len(mutation["results"]) != len(document["render_cases"]): raise OracleError(f"mutation result count drift: {mutation['name']}")
        for row in mutation["results"]:
            exact(row, {"case", "exact", "changed_float32_lanes", "changed_rgba8_bytes"}, "mutation result")
            if type(row["exact"]) is not bool or type(row["changed_float32_lanes"]) is not int or type(row["changed_rgba8_bytes"]) is not int or row["changed_float32_lanes"] < 0 or row["changed_rgba8_bytes"] < 0:
                raise OracleError(f"mutation result drift: {mutation['name']}")
        for witness in mutation["witnesses"]:
            if witness not in rows: raise OracleError(f"mutation witness case drift: {mutation['name']}")
            if rows[witness]["changed_float32_lanes"] <= 0 or rows[witness]["changed_rgba8_bytes"] <= 0: raise OracleError(f"mutation witness has no positive evidence: {mutation['name']}")

def emit(document):
    q = lambda value: json.dumps(str(value))
    def cxx_words(values): return ", ".join(f"0x{int(v,16):08x}u" for v in values)
    def cxx_bytes(values): return ", ".join(str(int(v)) for v in values)
    lines = ["// Generated by generate_classic_noise_native_oracle_include.py; exact JSON authority.", "#pragma once", "#include <cstdint>", "#include <string>", "#include <vector>", "namespace noisemaker_classic_noise_oracle {", "struct Binding { const char* name; const char* runtime_abi; const char* source_abi; };", "struct Case { const char* name; std::uint32_t width, height; std::vector<std::uint32_t> f32; const char* f32_sha256; std::vector<std::uint8_t> rgba8; const char* rgba8_sha256; bool repeat_exact; bool distinct_storage; bool controls_unchanged; };", "struct MutationResult { const char* case_name; bool exact; std::uint32_t changed_float32_lanes; std::uint32_t changed_rgba8_bytes; };", "struct Mutation { const char* name; const char* anchor; const char* replacement; const char* anchor_sha256; const char* replacement_sha256; const char* mutated_factory_sha256; bool independent; std::uint32_t anchor_cardinality; std::vector<const char*> witnesses; std::vector<MutationResult> results; };", f"inline constexpr const char* kSchema = {q(document['schema'])};", f"inline constexpr const char* kProgramKey = {q(KEY)};", f"inline constexpr const char* kFactorySha256 = {q(document['factory']['text_sha256'])};", f"inline constexpr const char* kSourceSha256 = {q(document['provenance']['source']['sha256'])};", f"inline constexpr std::uint32_t kSourceBytes = {document['provenance']['source']['bytes']}U;", f"inline constexpr std::uint32_t kImportClosureCardinality = {document['authority']['closure_cardinality']}U;", f"inline constexpr std::uint32_t kRuntimeBindingCardinality = {len(NAMES)}U;", "inline const std::vector<Binding> kRuntimeBindings = {"]
    for name in NAMES: lines.append(f"  {{{q(name)}, {q(RUNTIME_ABI[name])}, {q('define' if name in DEFINES else SOURCE_ABI[name])}}},")
    lines += ["};", "inline const std::vector<Case> kCases = {"]
    for case in document["render_cases"]:
        output = case["expected"]
        lines.append(f"  {{{q(case['name'])}, {case['width']}U, {case['height']}U, {{{cxx_words(output['f32_words_le'])}}}, {q(output['f32_sha256'])}, {{{cxx_bytes(output['rgba8_bytes'])}}}, {q(output['rgba8_sha256'])}, true, true, true}},")
    lines += ["};", "inline const std::vector<Mutation> kMutations = {"]
    for mutation in document["mutation_ledger"]:
        witnesses = "{" + ", ".join(q(witness) for witness in mutation["witnesses"]) + "}"
        results = "{" + ", ".join("{" + ", ".join((q(row["case"]), str(row["exact"]).lower(), f"{row['changed_float32_lanes']}U", f"{row['changed_rgba8_bytes']}U")) + "}" for row in mutation["results"]) + "}"
        lines.append(f"  {{{q(mutation['name'])}, {q(mutation['anchor'])}, {q(mutation['replacement'])}, {q(mutation['anchor_sha256'])}, {q(mutation['replacement_sha256'])}, {q(mutation['mutated_factory_sha256'])}, {str(mutation['independent']).lower()}, {mutation['anchor_cardinality']}U, {witnesses}, {results}}},")
    lines += ["};", "} // namespace noisemaker_classic_noise_oracle", ""]
    return "\n".join(lines).encode()

def main():
    parser = argparse.ArgumentParser(); group = parser.add_mutually_exclusive_group(required=True); group.add_argument("--write", action="store_true"); group.add_argument("--check", action="store_true"); group.add_argument("--self-test", action="store_true"); args = parser.parse_args()
    document = strict_json(sidecar(ORACLE)); sidecar(GENERATOR); sidecar(REPORT); validate(document); rendered = emit(document)
    if args.write:
        TARGET.parent.mkdir(parents=True, exist_ok=True); TARGET.write_bytes(rendered); pathlib.Path(f"{TARGET}.sha256").write_text(f"{digest(rendered)}  {TARGET.name}\n"); print(f"classic noise include written ({digest(rendered)})")
    elif args.check:
        if sidecar(TARGET) != rendered: raise OracleError("generated include drift")
        print(f"classic noise include check passed ({digest(rendered)})")
    else:
        forgeries = [
            ("closure hash", lambda d: d["authority"]["import_closure"][0].__setitem__("sha256", "0" * 64)),
            ("case control", lambda d: d["render_cases"][0].__setitem__("speed", 999)),
            ("case output", lambda d: d["render_cases"][0]["expected"].__setitem__("f32_sha256", "0" * 64)),
            ("mutation result", lambda d: d["mutation_ledger"][0]["results"][0].__setitem__("changed_float32_lanes", 0)),
        ]
        checks = [("schema", document["schema"] == SCHEMA), ("cases", len(document["render_cases"]) == 8), ("mutations", len(document["mutation_ledger"]) == 5), ("sidecars", True)]
        for label, mutate in forgeries:
            forged = copy.deepcopy(document)
            mutate(forged)
            try:
                validate(forged)
            except OracleError:
                checks.append((label, True))
            else:
                checks.append((label, False))
        for label, ok in checks: print(f"  [{'ok' if ok else 'FAIL'}] {label}")
        if not all(ok for _, ok in checks): raise OracleError("Classic Noise materializer self-test failed")
        print(f"strict schema and payload self-tests verified ({len(checks)}/{len(checks)})")

if __name__ == "__main__":
    main()
