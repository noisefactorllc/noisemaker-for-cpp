# Julia exact-pixel CPU oracle

Program: synth/julia:julia; factory: juliaFactory.

## Status and claim boundary

This checked report is generated from the authenticated JSON document below. It records 18 complete render cases, 25 complete mutation rows, and 1 diagnostic witness. The standalone Julia production path remains intentionally RED at the missing generated binder; no native runtime-green or production parity claim is made.

## Authority and identity

- Source: tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/julia/julia.glsl; SHA-256: 825e175c22fea086ad2860e16bcf0a79d797574a9dfad937a23baaadaffdeef0.
- Factory source: src/effects/adapters/julia.js; SHA-256: 0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5.
- Canonical factory: juliaFactory; text SHA-256: ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6; public/direct identity is canonical; adapter owns the key.
- Corpus revision: a024dc3a960cc44af454abc7aebce50456c194e6; upstream revision: 117a236679d1db3ab8f0e278230ece277b57564c.
- Import closure: 22 files, each realpath-confined and hash-pinned; checked data stores only the stable placeholder <immutable-cpu-snapshot-root>.
- Authority contract: --cpu-root, NOISEMAKER_CPU_ROOT, and NOISEMAKER_FOR_CPU were the same non-symlink external pinned root; live checkout and symlink roots are rejected.

## Complete authenticated case, mutation, relation, and diagnostic records

The following canonical JSON record is emitted directly from the generator document. It is intentionally complete: every case control/input/output hash and array, every mutation result row and witness, every source/factory/anchor/replacement/mutant identity, every relation, and the diagnostic record are included.

```json
{
  "schema": "noisemaker-for-cpp.julia.pixel-parity.v1",
  "schema_version": 1,
  "program_key": "synth/julia:julia",
  "effect_key": "synth/julia",
  "runtime_key": "synth/julia:julia",
  "corpus_revision": "a024dc3a960cc44af454abc7aebce50456c194e6",
  "upstream_revision": "117a236679d1db3ab8f0e278230ece277b57564c",
  "factory": {
    "name": "juliaFactory",
    "text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
    "public_factory_is_canonical_identity": true,
    "adapter_own_key": true
  },
  "runtime_binding_names": [
    "resolution",
    "tileOffset",
    "fullResolution",
    "time",
    "cReal",
    "cImag",
    "poi",
    "outputMode",
    "centerX",
    "centerY",
    "rotation",
    "iterations",
    "stripeFreq",
    "trapShape",
    "lightAngle",
    "cPath",
    "cSpeed",
    "cRadius",
    "invert",
    "zoomSpeed",
    "zoomDepth"
  ],
  "runtime_binding_abi": {
    "resolution": "Vec2",
    "tileOffset": "Vec2",
    "fullResolution": "Vec2",
    "time": "number",
    "cReal": "number",
    "cImag": "number",
    "poi": "int32",
    "outputMode": "int32",
    "centerX": "number",
    "centerY": "number",
    "rotation": "number",
    "iterations": "int32",
    "stripeFreq": "number",
    "trapShape": "int32",
    "lightAngle": "number",
    "cPath": "int32",
    "cSpeed": "number",
    "cRadius": "number",
    "invert": "bool",
    "zoomSpeed": "number",
    "zoomDepth": "number"
  },
  "source_uniform_abi": {
    "resolution": "vec2",
    "tileOffset": "vec2",
    "fullResolution": "vec2",
    "time": "float",
    "cReal": "float",
    "cImag": "float",
    "poi": "int",
    "outputMode": "int",
    "centerX": "float",
    "centerY": "float",
    "rotation": "float",
    "iterations": "int",
    "stripeFreq": "float",
    "trapShape": "int",
    "lightAngle": "float",
    "cPath": "int",
    "cSpeed": "float",
    "cRadius": "float",
    "invert": "bool",
    "zoomSpeed": "float",
    "zoomDepth": "float"
  },
  "canonical_binding_contract": {
    "names": [
      "resolution",
      "tileOffset",
      "fullResolution",
      "time",
      "cReal",
      "cImag",
      "poi",
      "outputMode",
      "centerX",
      "centerY",
      "rotation",
      "iterations",
      "stripeFreq",
      "trapShape",
      "lightAngle",
      "cPath",
      "cSpeed",
      "cRadius",
      "invert",
      "zoomSpeed",
      "zoomDepth"
    ],
    "abi": {
      "resolution": "Vec2",
      "tileOffset": "Vec2",
      "fullResolution": "Vec2",
      "time": "number",
      "cReal": "number",
      "cImag": "number",
      "poi": "int32",
      "outputMode": "int32",
      "centerX": "number",
      "centerY": "number",
      "rotation": "number",
      "iterations": "int32",
      "stripeFreq": "number",
      "trapShape": "int32",
      "lightAngle": "number",
      "cPath": "int32",
      "cSpeed": "number",
      "cRadius": "number",
      "invert": "bool",
      "zoomSpeed": "number",
      "zoomDepth": "number"
    },
    "source_abi": {
      "resolution": "vec2",
      "tileOffset": "vec2",
      "fullResolution": "vec2",
      "time": "float",
      "cReal": "float",
      "cImag": "float",
      "poi": "int",
      "outputMode": "int",
      "centerX": "float",
      "centerY": "float",
      "rotation": "float",
      "iterations": "int",
      "stripeFreq": "float",
      "trapShape": "int",
      "lightAngle": "float",
      "cPath": "int",
      "cSpeed": "float",
      "cRadius": "float",
      "invert": "bool",
      "zoomSpeed": "float",
      "zoomDepth": "float"
    }
  },
  "exactness_contract": {
    "float32": "raw little-endian uint32 words; signed zero and NaN payloads significant",
    "rgba8": "complete independently captured RGBA8 bytes",
    "tolerance": "none",
    "dimensions": "checked before lane access",
    "comparison": "dimensions, counts, every uint32 word, every RGBA8 byte"
  },
  "comparer_self_tests": {
    "dimensions_before_access": true,
    "first_mismatch_reported": true,
    "raw_words_and_rgba8_independent": true,
    "cases": {
      "good": true,
      "dimensions": true,
      "short": true,
      "long": true,
      "rgba8_count": true,
      "rgba8_mismatch": true,
      "signed_zero": true,
      "nan_payload": true
    }
  },
  "provenance": {
    "source": {
      "relative_path": "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/julia/julia.glsl",
      "sha256": "825e175c22fea086ad2860e16bcf0a79d797574a9dfad937a23baaadaffdeef0"
    },
    "factory_source": {
      "relative_path": "src/effects/adapters/julia.js",
      "sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5"
    },
    "cpu_snapshot": {
      "argument": "<immutable-cpu-snapshot-root>",
      "immutable_snapshot": true,
      "realpath_containment_checked": true,
      "live_checkout_rejected": true,
      "import_closure": [
        {
          "relative_path": "src/csl/glsl-kernel.js",
          "sha256": "a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa"
        },
        {
          "relative_path": "src/csl/glsl-runtime.js",
          "sha256": "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072"
        },
        {
          "relative_path": "src/csl/runtime.js",
          "sha256": "a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee"
        },
        {
          "relative_path": "src/effects/adapters/bit-effects.js",
          "sha256": "5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7"
        },
        {
          "relative_path": "src/effects/adapters/crt.js",
          "sha256": "c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc"
        },
        {
          "relative_path": "src/effects/adapters/f32-color.js",
          "sha256": "b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046"
        },
        {
          "relative_path": "src/effects/adapters/fractal.js",
          "sha256": "0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29"
        },
        {
          "relative_path": "src/effects/adapters/index.js",
          "sha256": "40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267"
        },
        {
          "relative_path": "src/effects/adapters/julia.js",
          "sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5"
        },
        {
          "relative_path": "src/effects/adapters/median.js",
          "sha256": "e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583"
        },
        {
          "relative_path": "src/effects/adapters/palette.js",
          "sha256": "8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452"
        },
        {
          "relative_path": "src/effects/adapters/snow.js",
          "sha256": "202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366"
        },
        {
          "relative_path": "src/effects/catalog.js",
          "sha256": "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4"
        },
        {
          "relative_path": "src/effects/definition.js",
          "sha256": "fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02"
        },
        {
          "relative_path": "src/effects/generated/canonical-adapter-data.js",
          "sha256": "ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab"
        },
        {
          "relative_path": "src/effects/generated/canonical-kernels.js",
          "sha256": "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe"
        },
        {
          "relative_path": "src/effects/generated/kernels.js",
          "sha256": "b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01"
        },
        {
          "relative_path": "src/effects/generated/upstream-snapshot.js",
          "sha256": "e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090"
        },
        {
          "relative_path": "src/effects/registry.js",
          "sha256": "8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618"
        },
        {
          "relative_path": "src/runtime/pass-runner.js",
          "sha256": "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa"
        },
        {
          "relative_path": "src/runtime/sampler.js",
          "sha256": "1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328"
        },
        {
          "relative_path": "src/runtime/surface.js",
          "sha256": "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59"
        }
      ]
    },
    "generator": {
      "relative_path": "docs/port-engineering/julia-parity/julia_oracle_generator.mjs",
      "sha256": "4445d39ddc05e720d2583d0b1cf785434464c1e764eb3059f20da65165158017"
    },
    "materializer": {
      "relative_path": "tools/glslcpp/generate_julia_native_oracle_include.py",
      "sha256": "d74c67eeeda0c4cddd9f2b06d1c3ebc15afc7137b33511e583e5c522a34c5998"
    }
  },
  "render_cases": [
    {
      "name": "manual-smooth",
      "width": 5,
      "height": 4,
      "time": 0.25,
      "cReal": -0.123,
      "cImag": 0.745,
      "poi": 0,
      "outputMode": 0,
      "centerX": -0.1,
      "centerY": 0.05,
      "rotation": 0,
      "iterations": 80,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 30,
      "cPath": 0,
      "cSpeed": 0,
      "cRadius": 0.5,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 1,
      "tileX": 0,
      "tileY": 0,
      "salt": 1,
      "input": {
        "width": 5,
        "height": 4,
        "f32_words_le": [
          "0x3d800000",
          "0x3d638e39",
          "0x3d3a2e8c",
          "0x3f800000",
          "0x3e800000",
          "0x3ee38e39",
          "0x3f0ba2e9",
          "0x3f800000",
          "0x3ee00000",
          "0x3f555555",
          "0x00000000",
          "0x3f800000",
          "0x3f200000",
          "0x3e2aaaab",
          "0x3f000000",
          "0x3f800000",
          "0x3f500000",
          "0x3f0e38e4",
          "0x3f800000",
          "0x3f800000",
          "0x3ec00000",
          "0x3e2aaaab",
          "0x3f22e8ba",
          "0x3f800000",
          "0x3f100000",
          "0x3f0e38e4",
          "0x3dba2e8c",
          "0x3f800000",
          "0x3f400000",
          "0x3f71c71c",
          "0x3f1745d1",
          "0x3f800000",
          "0x3f700000",
          "0x3e8e38e4",
          "0x3d3a2e8c",
          "0x3f800000",
          "0x3d800000",
          "0x3f2aaaab",
          "0x3f0ba2e9",
          "0x3f800000",
          "0x3f300000",
          "0x3e8e38e4",
          "0x3e3a2e8c",
          "0x3f800000",
          "0x3f600000",
          "0x3f2aaaab",
          "0x3f2e8ba3",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x3e0ba2e9",
          "0x3f800000",
          "0x3e400000",
          "0x3ec71c72",
          "0x3f22e8ba",
          "0x3f800000",
          "0x3ec00000",
          "0x3f471c72",
          "0x3dba2e8c",
          "0x3f800000",
          "0x3f800000",
          "0x3ec71c72",
          "0x3f45d174",
          "0x3f800000",
          "0x3e000000",
          "0x3f471c72",
          "0x3e68ba2f",
          "0x3f800000",
          "0x3ea00000",
          "0x3de38e39",
          "0x3f3a2e8c",
          "0x3f800000",
          "0x3f000000",
          "0x3f000000",
          "0x3e3a2e8c",
          "0x3f800000",
          "0x3f300000",
          "0x3f638e39",
          "0x3f2e8ba3",
          "0x3f800000"
        ],
        "f32_sha256": "04ec1b2e75cba0252250ddb7c2015a6866b7b62c6073d4fbf00edda49a77a1cb"
      },
      "expected": {
        "f32_words_le": [
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000"
        ],
        "f32_sha256": "68ce3ccc4770b082b0ca69e38a2dff21faf781a4627e582ab05cc611e6ad5508",
        "rgba8_bytes": [
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255
        ],
        "rgba8_sha256": "b1afc3dbe46c96d9627c89a90caea13bd4d5768cdc9929dcddb759fc39b5d1fa"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          5,
          4
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          5,
          4
        ],
        "time": 0.25,
        "cReal": -0.123,
        "cImag": 0.745,
        "poi": 0,
        "outputMode": 0,
        "centerX": -0.1,
        "centerY": 0.05,
        "rotation": 0,
        "iterations": 80,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 30,
        "cPath": 0,
        "cSpeed": 0,
        "cRadius": 0.5,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 1
      }
    },
    {
      "name": "manual-distance-tile",
      "width": 4,
      "height": 5,
      "time": 0.75,
      "cReal": 0.28,
      "cImag": 0.008,
      "poi": 0,
      "outputMode": 1,
      "centerX": 0,
      "centerY": 0,
      "rotation": 12,
      "iterations": 120,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 60,
      "cPath": 0,
      "cSpeed": 0,
      "cRadius": 0.5,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 1,
      "tileX": 0.5,
      "tileY": -0.25,
      "salt": 2,
      "input": {
        "width": 4,
        "height": 5,
        "f32_words_le": [
          "0x3e000000",
          "0x3de38e39",
          "0x3dba2e8c",
          "0x3f800000",
          "0x3ea00000",
          "0x3f000000",
          "0x3f1745d1",
          "0x3f800000",
          "0x3f000000",
          "0x3f638e39",
          "0x3d3a2e8c",
          "0x3f800000",
          "0x3f300000",
          "0x3e638e39",
          "0x3f0ba2e9",
          "0x3f800000",
          "0x3ee00000",
          "0x3e638e39",
          "0x3f2e8ba3",
          "0x3f800000",
          "0x3f200000",
          "0x3f1c71c7",
          "0x3e0ba2e9",
          "0x3f800000",
          "0x3f500000",
          "0x3f800000",
          "0x3f22e8ba",
          "0x3f800000",
          "0x3f800000",
          "0x3eaaaaab",
          "0x3dba2e8c",
          "0x3f800000",
          "0x3f400000",
          "0x3eaaaaab",
          "0x3e68ba2f",
          "0x3f800000",
          "0x3f700000",
          "0x3f38e38e",
          "0x3f3a2e8c",
          "0x3f800000",
          "0x3d800000",
          "0x3d638e39",
          "0x3e3a2e8c",
          "0x3f800000",
          "0x3e800000",
          "0x3ee38e39",
          "0x3f2e8ba3",
          "0x3f800000",
          "0x00000000",
          "0x3ee38e39",
          "0x3f51745d",
          "0x3f800000",
          "0x3e400000",
          "0x3f555555",
          "0x3e8ba2e9",
          "0x3f800000",
          "0x3ec00000",
          "0x3e2aaaab",
          "0x3f45d174",
          "0x3f800000",
          "0x3f100000",
          "0x3f0e38e4",
          "0x3e68ba2f",
          "0x3f800000",
          "0x3ea00000",
          "0x3f0e38e4",
          "0x3eba2e8c",
          "0x3f800000",
          "0x3f000000",
          "0x3f71c71c",
          "0x3f5d1746",
          "0x3f800000",
          "0x3f300000",
          "0x3e8e38e4",
          "0x3ea2e8ba",
          "0x3f800000",
          "0x3f600000",
          "0x3f2aaaab",
          "0x3f51745d",
          "0x3f800000"
        ],
        "f32_sha256": "e0f86664cee61f34fcde6f54e7f5409e68d9383f86fbdd328df64321f537f05c"
      },
      "expected": {
        "f32_words_le": [
          "0x3e01ca12",
          "0x3e01ca12",
          "0x3e01ca12",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x3a02883a",
          "0x3a02883a",
          "0x3a02883a",
          "0x3f800000",
          "0x3ce51b89",
          "0x3ce51b89",
          "0x3ce51b89",
          "0x3f800000",
          "0x3bfa12b3",
          "0x3bfa12b3",
          "0x3bfa12b3",
          "0x3f800000",
          "0x3dbdc006",
          "0x3dbdc006",
          "0x3dbdc006",
          "0x3f800000",
          "0x3dcb2451",
          "0x3dcb2451",
          "0x3dcb2451",
          "0x3f800000",
          "0x3cc73571",
          "0x3cc73571",
          "0x3cc73571",
          "0x3f800000",
          "0x3d7792ed",
          "0x3d7792ed",
          "0x3d7792ed",
          "0x3f800000",
          "0x3e90d2b4",
          "0x3e90d2b4",
          "0x3e90d2b4",
          "0x3f800000",
          "0x3c387e18",
          "0x3c387e18",
          "0x3c387e18",
          "0x3f800000",
          "0x3a34011a",
          "0x3a34011a",
          "0x3a34011a",
          "0x3f800000",
          "0x3d35bdb6",
          "0x3d35bdb6",
          "0x3d35bdb6",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x3d8b0064",
          "0x3d8b0064",
          "0x3d8b0064",
          "0x3f800000",
          "0x3e149028",
          "0x3e149028",
          "0x3e149028",
          "0x3f800000",
          "0x3c9014a2",
          "0x3c9014a2",
          "0x3c9014a2",
          "0x3f800000",
          "0x37863802",
          "0x37863802",
          "0x37863802",
          "0x3f800000",
          "0x3e3d0b7d",
          "0x3e3d0b7d",
          "0x3e3d0b7d",
          "0x3f800000",
          "0x3e94a491",
          "0x3e94a491",
          "0x3e94a491",
          "0x3f800000"
        ],
        "f32_sha256": "2420f5e9856fb635232e4025ed4d56c7ff00f46a9ff392992883f9db311a0e6a",
        "rgba8_bytes": [
          32,
          32,
          32,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          7,
          7,
          7,
          255,
          2,
          2,
          2,
          255,
          24,
          24,
          24,
          255,
          25,
          25,
          25,
          255,
          6,
          6,
          6,
          255,
          15,
          15,
          15,
          255,
          72,
          72,
          72,
          255,
          3,
          3,
          3,
          255,
          0,
          0,
          0,
          255,
          11,
          11,
          11,
          255,
          0,
          0,
          0,
          255,
          17,
          17,
          17,
          255,
          37,
          37,
          37,
          255,
          4,
          4,
          4,
          255,
          0,
          0,
          0,
          255,
          47,
          47,
          47,
          255,
          74,
          74,
          74,
          255
        ],
        "rgba8_sha256": "6350bb261836336ff3b357cbeb7a1c3438c0ffa2c093efe1316ce3d1e8b98a04"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          4,
          5
        ],
        "tileOffset": [
          0.5,
          -0.25
        ],
        "fullResolution": [
          4,
          5
        ],
        "time": 0.75,
        "cReal": 0.28,
        "cImag": 0.008,
        "poi": 0,
        "outputMode": 1,
        "centerX": 0,
        "centerY": 0,
        "rotation": 12,
        "iterations": 120,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 60,
        "cPath": 0,
        "cSpeed": 0,
        "cRadius": 0.5,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 1
      }
    },
    {
      "name": "manual-stripe",
      "width": 6,
      "height": 3,
      "time": 1.5,
      "cReal": 0.28,
      "cImag": 0.008,
      "poi": 0,
      "outputMode": 2,
      "centerX": 0,
      "centerY": 0,
      "rotation": 0,
      "iterations": 90,
      "stripeFreq": 2.75,
      "trapShape": 1,
      "lightAngle": 120,
      "cPath": 0,
      "cSpeed": 0,
      "cRadius": 0.5,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 1,
      "tileX": 0,
      "tileY": 0,
      "salt": 3,
      "input": {
        "width": 6,
        "height": 3,
        "f32_words_le": [
          "0x3e400000",
          "0x3e2aaaab",
          "0x3e0ba2e9",
          "0x3f800000",
          "0x3ec00000",
          "0x3f0e38e4",
          "0x3f22e8ba",
          "0x3f800000",
          "0x3f100000",
          "0x3f71c71c",
          "0x3dba2e8c",
          "0x3f800000",
          "0x3f400000",
          "0x3e8e38e4",
          "0x3f1745d1",
          "0x3f800000",
          "0x3f700000",
          "0x3f2aaaab",
          "0x3d3a2e8c",
          "0x3f800000",
          "0x3d800000",
          "0x00000000",
          "0x3f0ba2e9",
          "0x3f800000",
          "0x3f000000",
          "0x3e8e38e4",
          "0x3f3a2e8c",
          "0x3f800000",
          "0x3f300000",
          "0x3f2aaaab",
          "0x3e3a2e8c",
          "0x3f800000",
          "0x3f600000",
          "0x00000000",
          "0x3f2e8ba3",
          "0x3f800000",
          "0x00000000",
          "0x3ec71c72",
          "0x3e0ba2e9",
          "0x3f800000",
          "0x3e400000",
          "0x3f471c72",
          "0x3f22e8ba",
          "0x3f800000",
          "0x3ec00000",
          "0x3de38e39",
          "0x3dba2e8c",
          "0x3f800000",
          "0x3f500000",
          "0x3ec71c72",
          "0x3e8ba2e9",
          "0x3f800000",
          "0x3f800000",
          "0x3f471c72",
          "0x3f45d174",
          "0x3f800000",
          "0x3e000000",
          "0x3de38e39",
          "0x3e68ba2f",
          "0x3f800000",
          "0x3ea00000",
          "0x3f000000",
          "0x3f3a2e8c",
          "0x3f800000",
          "0x3f000000",
          "0x3f638e39",
          "0x3e3a2e8c",
          "0x3f800000",
          "0x3f300000",
          "0x3e638e39",
          "0x3f2e8ba3",
          "0x3f800000"
        ],
        "f32_sha256": "696e64435afb893bf92064201a0a8317209ec4e05cc93d73931087777bc23847"
      },
      "expected": {
        "f32_words_le": [
          "0x3f21db1a",
          "0x3f21db1a",
          "0x3f21db1a",
          "0x3f800000",
          "0x3f23e2c7",
          "0x3f23e2c7",
          "0x3f23e2c7",
          "0x3f800000",
          "0x3f0b44cf",
          "0x3f0b44cf",
          "0x3f0b44cf",
          "0x3f800000",
          "0x3f1e29a1",
          "0x3f1e29a1",
          "0x3f1e29a1",
          "0x3f800000",
          "0x3f25aa90",
          "0x3f25aa90",
          "0x3f25aa90",
          "0x3f800000",
          "0x3f191266",
          "0x3f191266",
          "0x3f191266",
          "0x3f800000",
          "0x3f151447",
          "0x3f151447",
          "0x3f151447",
          "0x3f800000",
          "0x3f1962fc",
          "0x3f1962fc",
          "0x3f1962fc",
          "0x3f800000",
          "0x3ef0267a",
          "0x3ef0267a",
          "0x3ef0267a",
          "0x3f800000",
          "0x3ef0267a",
          "0x3ef0267a",
          "0x3ef0267a",
          "0x3f800000",
          "0x3f1962fc",
          "0x3f1962fc",
          "0x3f1962fc",
          "0x3f800000",
          "0x3f151447",
          "0x3f151447",
          "0x3f151447",
          "0x3f800000",
          "0x3f191266",
          "0x3f191266",
          "0x3f191266",
          "0x3f800000",
          "0x3f25aa90",
          "0x3f25aa90",
          "0x3f25aa90",
          "0x3f800000",
          "0x3f1e29a1",
          "0x3f1e29a1",
          "0x3f1e29a1",
          "0x3f800000",
          "0x3f0b44cf",
          "0x3f0b44cf",
          "0x3f0b44cf",
          "0x3f800000",
          "0x3f23e2c7",
          "0x3f23e2c7",
          "0x3f23e2c7",
          "0x3f800000",
          "0x3f21db1a",
          "0x3f21db1a",
          "0x3f21db1a",
          "0x3f800000"
        ],
        "f32_sha256": "1194a269b70b781d38398a4f2c46e4dbf18061dfe8d9e4a1c26fc401a7b76f85",
        "rgba8_bytes": [
          161,
          161,
          161,
          255,
          163,
          163,
          163,
          255,
          139,
          139,
          139,
          255,
          158,
          158,
          158,
          255,
          165,
          165,
          165,
          255,
          152,
          152,
          152,
          255,
          148,
          148,
          148,
          255,
          153,
          153,
          153,
          255,
          120,
          120,
          120,
          255,
          120,
          120,
          120,
          255,
          153,
          153,
          153,
          255,
          148,
          148,
          148,
          255,
          152,
          152,
          152,
          255,
          165,
          165,
          165,
          255,
          158,
          158,
          158,
          255,
          139,
          139,
          139,
          255,
          163,
          163,
          163,
          255,
          161,
          161,
          161,
          255
        ],
        "rgba8_sha256": "cc4cb3f21a2715c0383b0a024d1b613eff3354f064dd5d763e61c57ea93589f3"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          6,
          3
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          6,
          3
        ],
        "time": 1.5,
        "cReal": 0.28,
        "cImag": 0.008,
        "poi": 0,
        "outputMode": 2,
        "centerX": 0,
        "centerY": 0,
        "rotation": 0,
        "iterations": 90,
        "stripeFreq": 2.75,
        "trapShape": 1,
        "lightAngle": 120,
        "cPath": 0,
        "cSpeed": 0,
        "cRadius": 0.5,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 1
      }
    },
    {
      "name": "poi-trap",
      "width": 5,
      "height": 5,
      "time": 2,
      "cReal": 0,
      "cImag": 0,
      "poi": 7,
      "outputMode": 3,
      "centerX": 0.1,
      "centerY": -0.1,
      "rotation": 0,
      "iterations": 150,
      "stripeFreq": 0,
      "trapShape": 2,
      "lightAngle": 210,
      "cPath": 0,
      "cSpeed": 0,
      "cRadius": 0.5,
      "invert": false,
      "zoomSpeed": 1.25,
      "zoomDepth": 8,
      "tileX": -0.375,
      "tileY": 0.625,
      "salt": 4,
      "input": {
        "width": 5,
        "height": 5,
        "f32_words_le": [
          "0x3e800000",
          "0x3e638e39",
          "0x3e3a2e8c",
          "0x3f800000",
          "0x3ee00000",
          "0x3f1c71c7",
          "0x3f2e8ba3",
          "0x3f800000",
          "0x3f200000",
          "0x3f800000",
          "0x3e0ba2e9",
          "0x3f800000",
          "0x3f500000",
          "0x3eaaaaab",
          "0x3f22e8ba",
          "0x3f800000",
          "0x3f800000",
          "0x3f38e38e",
          "0x3dba2e8c",
          "0x3f800000",
          "0x3f100000",
          "0x3eaaaaab",
          "0x3f45d174",
          "0x3f800000",
          "0x3f400000",
          "0x3f38e38e",
          "0x3e68ba2f",
          "0x3f800000",
          "0x3f700000",
          "0x3d638e39",
          "0x3f3a2e8c",
          "0x3f800000",
          "0x3d800000",
          "0x3ee38e39",
          "0x3e3a2e8c",
          "0x3f800000",
          "0x3e800000",
          "0x3f555555",
          "0x3f2e8ba3",
          "0x3f800000",
          "0x3f600000",
          "0x3ee38e39",
          "0x3ea2e8ba",
          "0x3f800000",
          "0x00000000",
          "0x3f555555",
          "0x3f51745d",
          "0x3f800000",
          "0x3e400000",
          "0x3e2aaaab",
          "0x3e8ba2e9",
          "0x3f800000",
          "0x3ec00000",
          "0x3f0e38e4",
          "0x3f45d174",
          "0x3f800000",
          "0x3f100000",
          "0x3f71c71c",
          "0x3e68ba2f",
          "0x3f800000",
          "0x3e000000",
          "0x3f0e38e4",
          "0x3f68ba2f",
          "0x3f800000",
          "0x3ea00000",
          "0x3f71c71c",
          "0x3eba2e8c",
          "0x3f800000",
          "0x3f000000",
          "0x3e8e38e4",
          "0x3f5d1746",
          "0x3f800000",
          "0x3f300000",
          "0x3f2aaaab",
          "0x3ea2e8ba",
          "0x3f800000",
          "0x3f600000",
          "0x00000000",
          "0x3f51745d",
          "0x3f800000",
          "0x3ee00000",
          "0x3f2aaaab",
          "0x3ee8ba2f",
          "0x3f800000",
          "0x3f200000",
          "0x00000000",
          "0x3f745d17",
          "0x3f800000",
          "0x3f500000",
          "0x3ec71c72",
          "0x3ed1745d",
          "0x3f800000",
          "0x3f800000",
          "0x3f471c72",
          "0x3f68ba2f",
          "0x3f800000",
          "0x3e000000",
          "0x3de38e39",
          "0x3eba2e8c",
          "0x3f800000"
        ],
        "f32_sha256": "ac3df82128d83e2e89260464cfbb004457912bb155a5eb972f74717e3907c7e5"
      },
      "expected": {
        "f32_words_le": [
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f7ff7da",
          "0x3f800000"
        ],
        "f32_sha256": "75352c0017ab1e77ff8eb69b000c8758e33ea992d501ee74b15034f5a84a997f",
        "rgba8_bytes": [
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255
        ],
        "rgba8_sha256": "da6f14970ce356ce01a5b340291e9d8b2652eb63fbf8f328ca6a87a727fde4d9"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          5,
          5
        ],
        "tileOffset": [
          -0.375,
          0.625
        ],
        "fullResolution": [
          5,
          5
        ],
        "time": 2,
        "cReal": 0,
        "cImag": 0,
        "poi": 7,
        "outputMode": 3,
        "centerX": 0.1,
        "centerY": -0.1,
        "rotation": 0,
        "iterations": 150,
        "stripeFreq": 0,
        "trapShape": 2,
        "lightAngle": 210,
        "cPath": 0,
        "cSpeed": 0,
        "cRadius": 0.5,
        "invert": false,
        "zoomSpeed": 1.25,
        "zoomDepth": 8
      }
    },
    {
      "name": "manual-normal",
      "width": 4,
      "height": 4,
      "time": 3.25,
      "cReal": -0.8,
      "cImag": 0.156,
      "poi": 0,
      "outputMode": 4,
      "centerX": -0.25,
      "centerY": 0.01,
      "rotation": -18,
      "iterations": 64,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 300,
      "cPath": 0,
      "cSpeed": 0,
      "cRadius": 0.5,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 2,
      "tileX": 0,
      "tileY": 0,
      "salt": 5,
      "input": {
        "width": 4,
        "height": 4,
        "f32_words_le": [
          "0x3ea00000",
          "0x3e8e38e4",
          "0x3e68ba2f",
          "0x3f800000",
          "0x3f000000",
          "0x3f2aaaab",
          "0x3f3a2e8c",
          "0x3f800000",
          "0x3f300000",
          "0x00000000",
          "0x3e3a2e8c",
          "0x3f800000",
          "0x3f600000",
          "0x3ec71c72",
          "0x3f2e8ba3",
          "0x3f800000",
          "0x3f200000",
          "0x3ec71c72",
          "0x3f51745d",
          "0x3f800000",
          "0x3f500000",
          "0x3f471c72",
          "0x3e8ba2e9",
          "0x3f800000",
          "0x3f800000",
          "0x3de38e39",
          "0x3f45d174",
          "0x3f800000",
          "0x3e000000",
          "0x3f000000",
          "0x3e68ba2f",
          "0x3f800000",
          "0x3f700000",
          "0x3f000000",
          "0x3eba2e8c",
          "0x3f800000",
          "0x3d800000",
          "0x3f638e39",
          "0x3f5d1746",
          "0x3f800000",
          "0x3e800000",
          "0x3e638e39",
          "0x3ea2e8ba",
          "0x3f800000",
          "0x3ee00000",
          "0x3f1c71c7",
          "0x3f51745d",
          "0x3f800000",
          "0x3e400000",
          "0x3f1c71c7",
          "0x3f745d17",
          "0x3f800000",
          "0x3ec00000",
          "0x3f800000",
          "0x3ed1745d",
          "0x3f800000",
          "0x3f100000",
          "0x3eaaaaab",
          "0x3f68ba2f",
          "0x3f800000",
          "0x3f400000",
          "0x3f38e38e",
          "0x3eba2e8c",
          "0x3f800000"
        ],
        "f32_sha256": "0cf32eaaf33b72ee8475938c52a05f7a3b757296f4532fb63743948faf9fec50"
      },
      "expected": {
        "f32_words_le": [
          "0x3f0e1ac1",
          "0x3f0e1ac1",
          "0x3f0e1ac1",
          "0x3f800000",
          "0x3f0ed7d6",
          "0x3f0ed7d6",
          "0x3f0ed7d6",
          "0x3f800000",
          "0x3f0f8bef",
          "0x3f0f8bef",
          "0x3f0f8bef",
          "0x3f800000",
          "0x3f1032ef",
          "0x3f1032ef",
          "0x3f1032ef",
          "0x3f800000",
          "0x3f0e934b",
          "0x3f0e934b",
          "0x3f0e934b",
          "0x3f800000",
          "0x3f0f8a2c",
          "0x3f0f8a2c",
          "0x3f0f8a2c",
          "0x3f800000",
          "0x3f1091c2",
          "0x3f1091c2",
          "0x3f1091c2",
          "0x3f800000",
          "0x3f11ad6d",
          "0x3f11ad6d",
          "0x3f11ad6d",
          "0x3f800000",
          "0x3f0f1303",
          "0x3f0f1303",
          "0x3f0f1303",
          "0x3f800000",
          "0x3f1043d8",
          "0x3f1043d8",
          "0x3f1043d8",
          "0x3f800000",
          "0x3f1199e0",
          "0x3f1199e0",
          "0x3f1199e0",
          "0x3f800000",
          "0x3f131c12",
          "0x3f131c12",
          "0x3f131c12",
          "0x3f800000",
          "0x3f0f9598",
          "0x3f0f9598",
          "0x3f0f9598",
          "0x3f800000",
          "0x3f110378",
          "0x3f110378",
          "0x3f110378",
          "0x3f800000",
          "0x3f12ac44",
          "0x3f12ac44",
          "0x3f12ac44",
          "0x3f800000",
          "0x3f149ac9",
          "0x3f149ac9",
          "0x3f149ac9",
          "0x3f800000"
        ],
        "f32_sha256": "a48b5c5dfb26c1525ec288ea6dd6f09734e204437fde85b0d1681ac4733c1dca",
        "rgba8_bytes": [
          142,
          142,
          142,
          255,
          142,
          142,
          142,
          255,
          143,
          143,
          143,
          255,
          144,
          144,
          144,
          255,
          142,
          142,
          142,
          255,
          143,
          143,
          143,
          255,
          144,
          144,
          144,
          255,
          145,
          145,
          145,
          255,
          143,
          143,
          143,
          255,
          144,
          144,
          144,
          255,
          145,
          145,
          145,
          255,
          147,
          147,
          147,
          255,
          143,
          143,
          143,
          255,
          144,
          144,
          144,
          255,
          146,
          146,
          146,
          255,
          148,
          148,
          148,
          255
        ],
        "rgba8_sha256": "7db70c0ff3cb9d1760bcbe349ff2f3cd4e374680720d96dffaf52b65fb48ac7a"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          4,
          4
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          4,
          4
        ],
        "time": 3.25,
        "cReal": -0.8,
        "cImag": 0.156,
        "poi": 0,
        "outputMode": 4,
        "centerX": -0.25,
        "centerY": 0.01,
        "rotation": -18,
        "iterations": 64,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 300,
        "cPath": 0,
        "cSpeed": 0,
        "cRadius": 0.5,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 2
      }
    },
    {
      "name": "animated-circle",
      "width": 4,
      "height": 3,
      "time": 0.5,
      "cReal": 0,
      "cImag": 0,
      "poi": 0,
      "outputMode": 0,
      "centerX": 0.3,
      "centerY": 0.4,
      "rotation": 0,
      "iterations": 64,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 45,
      "cPath": 2,
      "cSpeed": 0.75,
      "cRadius": 0.55,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 1,
      "tileX": 0,
      "tileY": 0,
      "salt": 6,
      "input": {
        "width": 4,
        "height": 3,
        "f32_words_le": [
          "0x3ec00000",
          "0x3eaaaaab",
          "0x3e8ba2e9",
          "0x3f800000",
          "0x3f100000",
          "0x3f38e38e",
          "0x3f45d174",
          "0x3f800000",
          "0x3f400000",
          "0x3d638e39",
          "0x3e68ba2f",
          "0x3f800000",
          "0x3f700000",
          "0x3ee38e39",
          "0x3f3a2e8c",
          "0x3f800000",
          "0x3f300000",
          "0x3ee38e39",
          "0x3f5d1746",
          "0x3f800000",
          "0x3f600000",
          "0x3f555555",
          "0x3ea2e8ba",
          "0x3f800000",
          "0x00000000",
          "0x3e2aaaab",
          "0x3f51745d",
          "0x3f800000",
          "0x3e400000",
          "0x3f0e38e4",
          "0x3e8ba2e9",
          "0x3f800000",
          "0x3f800000",
          "0x3f0e38e4",
          "0x3ed1745d",
          "0x3f800000",
          "0x3e000000",
          "0x3f71c71c",
          "0x3f68ba2f",
          "0x3f800000",
          "0x3ea00000",
          "0x3e8e38e4",
          "0x3eba2e8c",
          "0x3f800000",
          "0x3f000000",
          "0x3f2aaaab",
          "0x3f5d1746",
          "0x3f800000"
        ],
        "f32_sha256": "354b8e6e312ddf00b3d4bc2f734c506ad24a9c0c48df6ba6f23890443119040f"
      },
      "expected": {
        "f32_words_le": [
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x3db4ccd1",
          "0x3db4ccd1",
          "0x3db4ccd1",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x3e435eaa",
          "0x3e435eaa",
          "0x3e435eaa",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000"
        ],
        "f32_sha256": "e24ee7903037973363d2ac465310ae2ad5f67321352811f8a40e03904c69bb83",
        "rgba8_bytes": [
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          23,
          23,
          23,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          49,
          49,
          49,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255
        ],
        "rgba8_sha256": "f5656fbf77f179e0b98440ab8e06bd87debbc5bdddf60d661e395bef58ee1899"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          4,
          3
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          4,
          3
        ],
        "time": 0.5,
        "cReal": 0,
        "cImag": 0,
        "poi": 0,
        "outputMode": 0,
        "centerX": 0.3,
        "centerY": 0.4,
        "rotation": 0,
        "iterations": 64,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 45,
        "cPath": 2,
        "cSpeed": 0.75,
        "cRadius": 0.55,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 1
      }
    },
    {
      "name": "invert-output",
      "width": 3,
      "height": 4,
      "time": 1.1,
      "cReal": -0.7455,
      "cImag": 0.113,
      "poi": 0,
      "outputMode": 1,
      "centerX": 0,
      "centerY": 0,
      "rotation": 25,
      "iterations": 96,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 90,
      "cPath": 0,
      "cSpeed": 0,
      "cRadius": 0.5,
      "invert": true,
      "zoomSpeed": 0,
      "zoomDepth": 2,
      "tileX": 0,
      "tileY": 0,
      "salt": 7,
      "input": {
        "width": 3,
        "height": 4,
        "f32_words_le": [
          "0x3ee00000",
          "0x3ec71c72",
          "0x3ea2e8ba",
          "0x3f800000",
          "0x3f200000",
          "0x3f471c72",
          "0x3f51745d",
          "0x3f800000",
          "0x3f500000",
          "0x3de38e39",
          "0x3e8ba2e9",
          "0x3f800000",
          "0x3f400000",
          "0x3f000000",
          "0x3f68ba2f",
          "0x3f800000",
          "0x3f700000",
          "0x3f638e39",
          "0x3eba2e8c",
          "0x3f800000",
          "0x3d800000",
          "0x3e638e39",
          "0x3f5d1746",
          "0x3f800000",
          "0x00000000",
          "0x3f1c71c7",
          "0x3ee8ba2f",
          "0x3f800000",
          "0x3e400000",
          "0x3f800000",
          "0x3f745d17",
          "0x3f800000",
          "0x3ec00000",
          "0x3eaaaaab",
          "0x3ed1745d",
          "0x3f800000",
          "0x3ea00000",
          "0x3f38e38e",
          "0x00000000",
          "0x3f800000",
          "0x3f000000",
          "0x3d638e39",
          "0x3f000000",
          "0x3f800000",
          "0x3f300000",
          "0x3ee38e39",
          "0x3f800000",
          "0x3f800000"
        ],
        "f32_sha256": "58ab9329ff6a09a1179c3580f8a787da461583678ecc6dee47f24c000fed568d"
      },
      "expected": {
        "f32_words_le": [
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000"
        ],
        "f32_sha256": "c90489868a1a64a74239d5331b18d608ef69e28579f36f3ae1949cfe7354907a",
        "rgba8_bytes": [
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255
        ],
        "rgba8_sha256": "80a76a18acf8cb64fec3a659ffc4bab4a87cd9a6fde4dab2161a8751d136c9d2"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          3,
          4
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          3,
          4
        ],
        "time": 1.1,
        "cReal": -0.7455,
        "cImag": 0.113,
        "poi": 0,
        "outputMode": 1,
        "centerX": 0,
        "centerY": 0,
        "rotation": 25,
        "iterations": 96,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 90,
        "cPath": 0,
        "cSpeed": 0,
        "cRadius": 0.5,
        "invert": true,
        "zoomSpeed": 0,
        "zoomDepth": 2
      }
    },
    {
      "name": "animated-lissajous",
      "width": 3,
      "height": 3,
      "time": 0.9,
      "cReal": 0,
      "cImag": 0,
      "poi": 0,
      "outputMode": 3,
      "centerX": 0,
      "centerY": 0,
      "rotation": -12,
      "iterations": 72,
      "stripeFreq": 0,
      "trapShape": 1,
      "lightAngle": 180,
      "cPath": 1,
      "cSpeed": 1.1,
      "cRadius": 0.4,
      "invert": false,
      "zoomSpeed": 0.8,
      "zoomDepth": 3,
      "tileX": 0.25,
      "tileY": -0.5,
      "salt": 8,
      "input": {
        "width": 3,
        "height": 3,
        "f32_words_le": [
          "0x3f000000",
          "0x3ee38e39",
          "0x3eba2e8c",
          "0x3f800000",
          "0x3f300000",
          "0x3f555555",
          "0x3f5d1746",
          "0x3f800000",
          "0x3f600000",
          "0x3e2aaaab",
          "0x3ea2e8ba",
          "0x3f800000",
          "0x3f500000",
          "0x3f0e38e4",
          "0x3f745d17",
          "0x3f800000",
          "0x3f800000",
          "0x3f71c71c",
          "0x3ed1745d",
          "0x3f800000",
          "0x3e000000",
          "0x3e8e38e4",
          "0x3f68ba2f",
          "0x3f800000",
          "0x3d800000",
          "0x3f2aaaab",
          "0x3f000000",
          "0x3f800000",
          "0x3e800000",
          "0x00000000",
          "0x3f800000",
          "0x3f800000",
          "0x3ee00000",
          "0x3ec71c72",
          "0x3ee8ba2f",
          "0x3f800000"
        ],
        "f32_sha256": "a0c51cd0aa9ad8a182b9d62fd6205b2339e03f1430b49cb37e56a6d70fec75e3"
      },
      "expected": {
        "f32_words_le": [
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000"
        ],
        "f32_sha256": "8657f768505e95acfcb2802903768a6bf4e72e408ddea917bc9780784ffd2c44",
        "rgba8_bytes": [
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255
        ],
        "rgba8_sha256": "d574fbbbc44a56d8ec9bf06a4221e0c975b101e434c87e030572be6660dfb538"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          3,
          3
        ],
        "tileOffset": [
          0.25,
          -0.5
        ],
        "fullResolution": [
          3,
          3
        ],
        "time": 0.9,
        "cReal": 0,
        "cImag": 0,
        "poi": 0,
        "outputMode": 3,
        "centerX": 0,
        "centerY": 0,
        "rotation": -12,
        "iterations": 72,
        "stripeFreq": 0,
        "trapShape": 1,
        "lightAngle": 180,
        "cPath": 1,
        "cSpeed": 1.1,
        "cRadius": 0.4,
        "invert": false,
        "zoomSpeed": 0.8,
        "zoomDepth": 3
      }
    },
    {
      "name": "iterations-min",
      "width": 1,
      "height": 1,
      "time": 0,
      "cReal": 0,
      "cImag": 0,
      "poi": 0,
      "outputMode": 0,
      "centerX": 0,
      "centerY": 0,
      "rotation": 0,
      "iterations": 1,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 45,
      "cPath": 0,
      "cSpeed": 0,
      "cRadius": 0.5,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 1,
      "tileX": 0,
      "tileY": 0,
      "salt": 9,
      "input": {
        "width": 1,
        "height": 1,
        "f32_words_le": [
          "0x3f100000",
          "0x3f000000",
          "0x3ed1745d",
          "0x3f800000"
        ],
        "f32_sha256": "9ab27ec849e1d15f5c1b80a7c88f41b3be7c10af6e8fdf00649fd5a45f183c76"
      },
      "expected": {
        "f32_words_le": [
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000"
        ],
        "f32_sha256": "7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e",
        "rgba8_bytes": [
          0,
          0,
          0,
          255
        ],
        "rgba8_sha256": "e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          1,
          1
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          1,
          1
        ],
        "time": 0,
        "cReal": 0,
        "cImag": 0,
        "poi": 0,
        "outputMode": 0,
        "centerX": 0,
        "centerY": 0,
        "rotation": 0,
        "iterations": 1,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 45,
        "cPath": 0,
        "cSpeed": 0,
        "cRadius": 0.5,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 1
      }
    },
    {
      "name": "iterations-max",
      "width": 1,
      "height": 1,
      "time": 6.4456087906019786,
      "cReal": 0.7145556327222278,
      "cImag": 0.18602843191149376,
      "poi": 0,
      "outputMode": 3,
      "centerX": -0.5526962232665849,
      "centerY": -0.20907021993982378,
      "rotation": -24.482864887566052,
      "iterations": 1000,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 284.247223381942,
      "cPath": 3,
      "cSpeed": 1.1909674250499735,
      "cRadius": 0.8099422763590567,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 4.561745525235716,
      "tileX": 0,
      "tileY": 0,
      "salt": 15,
      "input": {
        "width": 1,
        "height": 1,
        "f32_words_le": [
          "0x3f700000",
          "0x3f555555",
          "0x3f2e8ba3",
          "0x3f800000"
        ],
        "f32_sha256": "3e528f72f53b49516bb6c44bdd3db8f688f2c0105fa1120e8ea941ca5d88ead2"
      },
      "expected": {
        "f32_words_le": [
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000"
        ],
        "f32_sha256": "7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e",
        "rgba8_bytes": [
          0,
          0,
          0,
          255
        ],
        "rgba8_sha256": "e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          1,
          1
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          1,
          1
        ],
        "time": 6.4456087906019786,
        "cReal": 0.7145556327222278,
        "cImag": 0.18602843191149376,
        "poi": 0,
        "outputMode": 3,
        "centerX": -0.5526962232665849,
        "centerY": -0.20907021993982378,
        "rotation": -24.482864887566052,
        "iterations": 1000,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 284.247223381942,
        "cPath": 3,
        "cSpeed": 1.1909674250499735,
        "cRadius": 0.8099422763590567,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 4.561745525235716
      }
    },
    {
      "name": "iterations-clamp-1001",
      "width": 1,
      "height": 1,
      "time": 6.4456087906019786,
      "cReal": 0.7145556327222278,
      "cImag": 0.18602843191149376,
      "poi": 0,
      "outputMode": 3,
      "centerX": -0.5526962232665849,
      "centerY": -0.20907021993982378,
      "rotation": -24.482864887566052,
      "iterations": 1001,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 284.247223381942,
      "cPath": 3,
      "cSpeed": 1.1909674250499735,
      "cRadius": 0.8099422763590567,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 4.561745525235716,
      "tileX": 0,
      "tileY": 0,
      "salt": 15,
      "input": {
        "width": 1,
        "height": 1,
        "f32_words_le": [
          "0x3f700000",
          "0x3f555555",
          "0x3f2e8ba3",
          "0x3f800000"
        ],
        "f32_sha256": "3e528f72f53b49516bb6c44bdd3db8f688f2c0105fa1120e8ea941ca5d88ead2"
      },
      "expected": {
        "f32_words_le": [
          "0x3f56a8ef",
          "0x3f56a8ef",
          "0x3f56a8ef",
          "0x3f800000"
        ],
        "f32_sha256": "e59c766c5f4c4faface8b7b5e30bafb20c6d10c89c12aba22784010e24fd1b67",
        "rgba8_bytes": [
          214,
          214,
          214,
          255
        ],
        "rgba8_sha256": "118a1615c6cfc6ba1f8f9c5f3a4c07e4f79edd70d13f56c086d7f0c2a655e66b"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          1,
          1
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          1,
          1
        ],
        "time": 6.4456087906019786,
        "cReal": 0.7145556327222278,
        "cImag": 0.18602843191149376,
        "poi": 0,
        "outputMode": 3,
        "centerX": -0.5526962232665849,
        "centerY": -0.20907021993982378,
        "rotation": -24.482864887566052,
        "iterations": 1001,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 284.247223381942,
        "cPath": 3,
        "cSpeed": 1.1909674250499735,
        "cRadius": 0.8099422763590567,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 4.561745525235716
      }
    },
    {
      "name": "bulb-path",
      "width": 2,
      "height": 2,
      "time": 0.25,
      "cReal": 0,
      "cImag": 0,
      "poi": 0,
      "outputMode": 1,
      "centerX": 0,
      "centerY": 0,
      "rotation": 0,
      "iterations": 64,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 45,
      "cPath": 3,
      "cSpeed": 0.5,
      "cRadius": 0.5,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 1,
      "tileX": 0,
      "tileY": 0,
      "salt": 11,
      "input": {
        "width": 2,
        "height": 2,
        "f32_words_le": [
          "0x3f300000",
          "0x3f1c71c7",
          "0x3f000000",
          "0x3f800000",
          "0x3f600000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f800000",
          "0x3f38e38e",
          "0x3d3a2e8c",
          "0x3f800000",
          "0x3e000000",
          "0x3d638e39",
          "0x3f0ba2e9",
          "0x3f800000"
        ],
        "f32_sha256": "eaa3484acd7fa41d0ad4941309bab6374f222c210b17764fb521d5cf4eefcb7f"
      },
      "expected": {
        "f32_words_le": [
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000"
        ],
        "f32_sha256": "9ba3b531624710dece54456c2e5cb1cb31d7df8cfb6fee2b1180d0cb791ea049",
        "rgba8_bytes": [
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255
        ],
        "rgba8_sha256": "cc0fa51d4d0a97b664030be5052f3b2b69a1267f89ace4c9bbc65007566725df"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          2,
          2
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          2,
          2
        ],
        "time": 0.25,
        "cReal": 0,
        "cImag": 0,
        "poi": 0,
        "outputMode": 1,
        "centerX": 0,
        "centerY": 0,
        "rotation": 0,
        "iterations": 64,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 45,
        "cPath": 3,
        "cSpeed": 0.5,
        "cRadius": 0.5,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 1
      }
    },
    {
      "name": "poi-fallback",
      "width": 2,
      "height": 2,
      "time": 0.5,
      "cReal": 0.2,
      "cImag": -0.3,
      "poi": 99,
      "outputMode": 1,
      "centerX": 0,
      "centerY": 0,
      "rotation": 0,
      "iterations": 64,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 45,
      "cPath": 0,
      "cSpeed": 0,
      "cRadius": 0.5,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 1,
      "tileX": 0,
      "tileY": 0,
      "salt": 12,
      "input": {
        "width": 2,
        "height": 2,
        "f32_words_le": [
          "0x3f400000",
          "0x3f2aaaab",
          "0x3f0ba2e9",
          "0x3f800000",
          "0x3f700000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x3f471c72",
          "0x3dba2e8c",
          "0x3f800000",
          "0x3e400000",
          "0x3de38e39",
          "0x3f1745d1",
          "0x3f800000"
        ],
        "f32_sha256": "7b8fcf38d596b67f0caf52ff4ba76e5a14213cae87d9ee2d7ba8ea354aa19b2d"
      },
      "expected": {
        "f32_words_le": [
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000"
        ],
        "f32_sha256": "9ba3b531624710dece54456c2e5cb1cb31d7df8cfb6fee2b1180d0cb791ea049",
        "rgba8_bytes": [
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255
        ],
        "rgba8_sha256": "cc0fa51d4d0a97b664030be5052f3b2b69a1267f89ace4c9bbc65007566725df"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          2,
          2
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          2,
          2
        ],
        "time": 0.5,
        "cReal": 0.2,
        "cImag": -0.3,
        "poi": 99,
        "outputMode": 1,
        "centerX": 0,
        "centerY": 0,
        "rotation": 0,
        "iterations": 64,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 45,
        "cPath": 0,
        "cSpeed": 0,
        "cRadius": 0.5,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 1
      }
    },
    {
      "name": "period-convergence",
      "width": 1,
      "height": 1,
      "time": 0,
      "cReal": 0,
      "cImag": 0,
      "poi": 0,
      "outputMode": 3,
      "centerX": 0,
      "centerY": 0,
      "rotation": 0,
      "iterations": 50,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 45,
      "cPath": 0,
      "cSpeed": 0,
      "cRadius": 0.5,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 1,
      "tileX": 0,
      "tileY": 0,
      "salt": 13,
      "input": {
        "width": 1,
        "height": 1,
        "f32_words_le": [
          "0x3f500000",
          "0x3f38e38e",
          "0x3f1745d1",
          "0x3f800000"
        ],
        "f32_sha256": "df5b7da9a846298cb6d8132039eef63d490145aec049791b61256d076cde4877"
      },
      "expected": {
        "f32_words_le": [
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000"
        ],
        "f32_sha256": "7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e",
        "rgba8_bytes": [
          0,
          0,
          0,
          255
        ],
        "rgba8_sha256": "e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          1,
          1
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          1,
          1
        ],
        "time": 0,
        "cReal": 0,
        "cImag": 0,
        "poi": 0,
        "outputMode": 3,
        "centerX": 0,
        "centerY": 0,
        "rotation": 0,
        "iterations": 50,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 45,
        "cPath": 0,
        "cSpeed": 0,
        "cRadius": 0.5,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 1
      }
    },
    {
      "name": "fallback-output-mode",
      "width": 5,
      "height": 4,
      "time": 0.25,
      "cReal": -0.123,
      "cImag": 0.745,
      "poi": 0,
      "outputMode": 5,
      "centerX": -0.1,
      "centerY": 0.05,
      "rotation": 0,
      "iterations": 80,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 30,
      "cPath": 0,
      "cSpeed": 0,
      "cRadius": 0.5,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 1,
      "tileX": 0,
      "tileY": 0,
      "salt": 1,
      "input": {
        "width": 5,
        "height": 4,
        "f32_words_le": [
          "0x3d800000",
          "0x3d638e39",
          "0x3d3a2e8c",
          "0x3f800000",
          "0x3e800000",
          "0x3ee38e39",
          "0x3f0ba2e9",
          "0x3f800000",
          "0x3ee00000",
          "0x3f555555",
          "0x00000000",
          "0x3f800000",
          "0x3f200000",
          "0x3e2aaaab",
          "0x3f000000",
          "0x3f800000",
          "0x3f500000",
          "0x3f0e38e4",
          "0x3f800000",
          "0x3f800000",
          "0x3ec00000",
          "0x3e2aaaab",
          "0x3f22e8ba",
          "0x3f800000",
          "0x3f100000",
          "0x3f0e38e4",
          "0x3dba2e8c",
          "0x3f800000",
          "0x3f400000",
          "0x3f71c71c",
          "0x3f1745d1",
          "0x3f800000",
          "0x3f700000",
          "0x3e8e38e4",
          "0x3d3a2e8c",
          "0x3f800000",
          "0x3d800000",
          "0x3f2aaaab",
          "0x3f0ba2e9",
          "0x3f800000",
          "0x3f300000",
          "0x3e8e38e4",
          "0x3e3a2e8c",
          "0x3f800000",
          "0x3f600000",
          "0x3f2aaaab",
          "0x3f2e8ba3",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x3e0ba2e9",
          "0x3f800000",
          "0x3e400000",
          "0x3ec71c72",
          "0x3f22e8ba",
          "0x3f800000",
          "0x3ec00000",
          "0x3f471c72",
          "0x3dba2e8c",
          "0x3f800000",
          "0x3f800000",
          "0x3ec71c72",
          "0x3f45d174",
          "0x3f800000",
          "0x3e000000",
          "0x3f471c72",
          "0x3e68ba2f",
          "0x3f800000",
          "0x3ea00000",
          "0x3de38e39",
          "0x3f3a2e8c",
          "0x3f800000",
          "0x3f000000",
          "0x3f000000",
          "0x3e3a2e8c",
          "0x3f800000",
          "0x3f300000",
          "0x3f638e39",
          "0x3f2e8ba3",
          "0x3f800000"
        ],
        "f32_sha256": "04ec1b2e75cba0252250ddb7c2015a6866b7b62c6073d4fbf00edda49a77a1cb"
      },
      "expected": {
        "f32_words_le": [
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000"
        ],
        "f32_sha256": "68ce3ccc4770b082b0ca69e38a2dff21faf781a4627e582ab05cc611e6ad5508",
        "rgba8_bytes": [
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255
        ],
        "rgba8_sha256": "b1afc3dbe46c96d9627c89a90caea13bd4d5768cdc9929dcddb759fc39b5d1fa"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          5,
          4
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          5,
          4
        ],
        "time": 0.25,
        "cReal": -0.123,
        "cImag": 0.745,
        "poi": 0,
        "outputMode": 5,
        "centerX": -0.1,
        "centerY": 0.05,
        "rotation": 0,
        "iterations": 80,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 30,
        "cPath": 0,
        "cSpeed": 0,
        "cRadius": 0.5,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 1
      }
    },
    {
      "name": "fallback-trap-shape",
      "width": 4,
      "height": 3,
      "time": 1.5,
      "cReal": 0.28,
      "cImag": 0.008,
      "poi": 0,
      "outputMode": 3,
      "centerX": 0,
      "centerY": 0,
      "rotation": 0,
      "iterations": 90,
      "stripeFreq": 0,
      "trapShape": 9,
      "lightAngle": 120,
      "cPath": 0,
      "cSpeed": 0,
      "cRadius": 0.5,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 1,
      "tileX": 0,
      "tileY": 0,
      "salt": 3,
      "input": {
        "width": 4,
        "height": 3,
        "f32_words_le": [
          "0x3e400000",
          "0x3e2aaaab",
          "0x3e0ba2e9",
          "0x3f800000",
          "0x3ec00000",
          "0x3f0e38e4",
          "0x3f22e8ba",
          "0x3f800000",
          "0x3f100000",
          "0x3f71c71c",
          "0x3dba2e8c",
          "0x3f800000",
          "0x3f400000",
          "0x3e8e38e4",
          "0x3f1745d1",
          "0x3f800000",
          "0x3f000000",
          "0x3e8e38e4",
          "0x3f3a2e8c",
          "0x3f800000",
          "0x3f300000",
          "0x3f2aaaab",
          "0x3e3a2e8c",
          "0x3f800000",
          "0x3f600000",
          "0x00000000",
          "0x3f2e8ba3",
          "0x3f800000",
          "0x00000000",
          "0x3ec71c72",
          "0x3e0ba2e9",
          "0x3f800000",
          "0x3f500000",
          "0x3ec71c72",
          "0x3e8ba2e9",
          "0x3f800000",
          "0x3f800000",
          "0x3f471c72",
          "0x3f45d174",
          "0x3f800000",
          "0x3e000000",
          "0x3de38e39",
          "0x3e68ba2f",
          "0x3f800000",
          "0x3ea00000",
          "0x3f000000",
          "0x3f3a2e8c",
          "0x3f800000"
        ],
        "f32_sha256": "a099727fbe3dc3ca104ec1229bf5ad6d2c537046798fd6a199a6f4db641e9fe3"
      },
      "expected": {
        "f32_words_le": [
          "0x3f6f5fec",
          "0x3f6f5fec",
          "0x3f6f5fec",
          "0x3f800000",
          "0x3f7d7166",
          "0x3f7d7166",
          "0x3f7d7166",
          "0x3f800000",
          "0x3f7abb76",
          "0x3f7abb76",
          "0x3f7abb76",
          "0x3f800000",
          "0x3f7eaf3d",
          "0x3f7eaf3d",
          "0x3f7eaf3d",
          "0x3f800000",
          "0x3f7ec631",
          "0x3f7ec631",
          "0x3f7ec631",
          "0x3f800000",
          "0x3f7fa01a",
          "0x3f7fa01a",
          "0x3f7fa01a",
          "0x3f800000",
          "0x3f7fa01a",
          "0x3f7fa01a",
          "0x3f7fa01a",
          "0x3f800000",
          "0x3f7ec631",
          "0x3f7ec631",
          "0x3f7ec631",
          "0x3f800000",
          "0x3f7eaf3d",
          "0x3f7eaf3d",
          "0x3f7eaf3d",
          "0x3f800000",
          "0x3f7abb76",
          "0x3f7abb76",
          "0x3f7abb76",
          "0x3f800000",
          "0x3f7d7166",
          "0x3f7d7166",
          "0x3f7d7166",
          "0x3f800000",
          "0x3f6f5fec",
          "0x3f6f5fec",
          "0x3f6f5fec",
          "0x3f800000"
        ],
        "f32_sha256": "e1b2ea7b0afff299f71fe14a7e7030191d30ae0b6aa94d6247c0d9480ee37cc3",
        "rgba8_bytes": [
          238,
          238,
          238,
          255,
          252,
          252,
          252,
          255,
          250,
          250,
          250,
          255,
          254,
          254,
          254,
          255,
          254,
          254,
          254,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          255,
          254,
          254,
          254,
          255,
          254,
          254,
          254,
          255,
          250,
          250,
          250,
          255,
          252,
          252,
          252,
          255,
          238,
          238,
          238,
          255
        ],
        "rgba8_sha256": "7b40c20788a3091bcce9e5ad651c7629b9302cfc25d9f35063b62bb8121e311d"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          4,
          3
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          4,
          3
        ],
        "time": 1.5,
        "cReal": 0.28,
        "cImag": 0.008,
        "poi": 0,
        "outputMode": 3,
        "centerX": 0,
        "centerY": 0,
        "rotation": 0,
        "iterations": 90,
        "stripeFreq": 0,
        "trapShape": 9,
        "lightAngle": 120,
        "cPath": 0,
        "cSpeed": 0,
        "cRadius": 0.5,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 1
      }
    },
    {
      "name": "fallback-c-path",
      "width": 4,
      "height": 3,
      "time": 0.5,
      "cReal": 0,
      "cImag": 0,
      "poi": 0,
      "outputMode": 0,
      "centerX": 0.3,
      "centerY": 0.4,
      "rotation": 0,
      "iterations": 64,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 45,
      "cPath": 9,
      "cSpeed": 0.75,
      "cRadius": 0.55,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 1,
      "tileX": 0,
      "tileY": 0,
      "salt": 6,
      "input": {
        "width": 4,
        "height": 3,
        "f32_words_le": [
          "0x3ec00000",
          "0x3eaaaaab",
          "0x3e8ba2e9",
          "0x3f800000",
          "0x3f100000",
          "0x3f38e38e",
          "0x3f45d174",
          "0x3f800000",
          "0x3f400000",
          "0x3d638e39",
          "0x3e68ba2f",
          "0x3f800000",
          "0x3f700000",
          "0x3ee38e39",
          "0x3f3a2e8c",
          "0x3f800000",
          "0x3f300000",
          "0x3ee38e39",
          "0x3f5d1746",
          "0x3f800000",
          "0x3f600000",
          "0x3f555555",
          "0x3ea2e8ba",
          "0x3f800000",
          "0x00000000",
          "0x3e2aaaab",
          "0x3f51745d",
          "0x3f800000",
          "0x3e400000",
          "0x3f0e38e4",
          "0x3e8ba2e9",
          "0x3f800000",
          "0x3f800000",
          "0x3f0e38e4",
          "0x3ed1745d",
          "0x3f800000",
          "0x3e000000",
          "0x3f71c71c",
          "0x3f68ba2f",
          "0x3f800000",
          "0x3ea00000",
          "0x3e8e38e4",
          "0x3eba2e8c",
          "0x3f800000",
          "0x3f000000",
          "0x3f2aaaab",
          "0x3f5d1746",
          "0x3f800000"
        ],
        "f32_sha256": "354b8e6e312ddf00b3d4bc2f734c506ad24a9c0c48df6ba6f23890443119040f"
      },
      "expected": {
        "f32_words_le": [
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000",
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000"
        ],
        "f32_sha256": "8cea1b2ba74e80909c56b26a87e7d02eee4517266ae0ab2f34d8fa601d4e2ba8",
        "rgba8_bytes": [
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255,
          0,
          0,
          0,
          255
        ],
        "rgba8_sha256": "937d497ff9439479f9a77994b703e6ebced8ca0b9b3c66640567d267c5387a75"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          4,
          3
        ],
        "tileOffset": [
          0,
          0
        ],
        "fullResolution": [
          4,
          3
        ],
        "time": 0.5,
        "cReal": 0,
        "cImag": 0,
        "poi": 0,
        "outputMode": 0,
        "centerX": 0.3,
        "centerY": 0.4,
        "rotation": 0,
        "iterations": 64,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 45,
        "cPath": 9,
        "cSpeed": 0.75,
        "cRadius": 0.55,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 1
      }
    },
    {
      "name": "non-square-f32-transform",
      "width": 7,
      "height": 3,
      "time": 1.25,
      "cReal": -0.4,
      "cImag": 0.6,
      "poi": 0,
      "outputMode": 4,
      "centerX": 0.125,
      "centerY": -0.2,
      "rotation": 33,
      "iterations": 73,
      "stripeFreq": 0,
      "trapShape": 0,
      "lightAngle": 271,
      "cPath": 0,
      "cSpeed": 0,
      "cRadius": 0.5,
      "invert": false,
      "zoomSpeed": 0,
      "zoomDepth": 2.5,
      "tileX": 0.375,
      "tileY": -0.125,
      "salt": 14,
      "input": {
        "width": 7,
        "height": 3,
        "f32_words_le": [
          "0x3f600000",
          "0x3f471c72",
          "0x3f22e8ba",
          "0x3f800000",
          "0x00000000",
          "0x3de38e39",
          "0x3dba2e8c",
          "0x3f800000",
          "0x3e400000",
          "0x3f000000",
          "0x3f1745d1",
          "0x3f800000",
          "0x3ec00000",
          "0x3f638e39",
          "0x3d3a2e8c",
          "0x3f800000",
          "0x3f100000",
          "0x3e638e39",
          "0x3f0ba2e9",
          "0x3f800000",
          "0x3f400000",
          "0x3f1c71c7",
          "0x00000000",
          "0x3f800000",
          "0x3f700000",
          "0x3f800000",
          "0x3f000000",
          "0x3f800000",
          "0x3e000000",
          "0x3f638e39",
          "0x3e3a2e8c",
          "0x3f800000",
          "0x3ea00000",
          "0x3e638e39",
          "0x3f2e8ba3",
          "0x3f800000",
          "0x3f000000",
          "0x3f1c71c7",
          "0x3e0ba2e9",
          "0x3f800000",
          "0x3f300000",
          "0x3f800000",
          "0x3f22e8ba",
          "0x3f800000",
          "0x3f600000",
          "0x3eaaaaab",
          "0x3dba2e8c",
          "0x3f800000",
          "0x00000000",
          "0x3f38e38e",
          "0x3f1745d1",
          "0x3f800000",
          "0x3e400000",
          "0x3d638e39",
          "0x3d3a2e8c",
          "0x3f800000",
          "0x3ee00000",
          "0x3f800000",
          "0x3f45d174",
          "0x3f800000",
          "0x3f200000",
          "0x3eaaaaab",
          "0x3e68ba2f",
          "0x3f800000",
          "0x3f500000",
          "0x3f38e38e",
          "0x3f3a2e8c",
          "0x3f800000",
          "0x3f800000",
          "0x3d638e39",
          "0x3e3a2e8c",
          "0x3f800000",
          "0x3e000000",
          "0x3ee38e39",
          "0x3f2e8ba3",
          "0x3f800000",
          "0x3ea00000",
          "0x3f555555",
          "0x3e0ba2e9",
          "0x3f800000",
          "0x3f000000",
          "0x3e2aaaab",
          "0x3f22e8ba",
          "0x3f800000"
        ],
        "f32_sha256": "6347d28706b4fa2aaa32f7e6ffb6ad011ee58c9937806df40040149fe5dc2a8f"
      },
      "expected": {
        "f32_words_le": [
          "0x3f2c9ba5",
          "0x3f2c9ba5",
          "0x3f2c9ba5",
          "0x3f800000",
          "0x3f2935e8",
          "0x3f2935e8",
          "0x3f2935e8",
          "0x3f800000",
          "0x3f273cec",
          "0x3f273cec",
          "0x3f273cec",
          "0x3f800000",
          "0x3f260337",
          "0x3f260337",
          "0x3f260337",
          "0x3f800000",
          "0x3f2523b5",
          "0x3f2523b5",
          "0x3f2523b5",
          "0x3f800000",
          "0x3f2459b4",
          "0x3f2459b4",
          "0x3f2459b4",
          "0x3f800000",
          "0x3f236348",
          "0x3f236348",
          "0x3f236348",
          "0x3f800000",
          "0x3f31c389",
          "0x3f31c389",
          "0x3f31c389",
          "0x3f800000",
          "0x3f2bdf58",
          "0x3f2bdf58",
          "0x3f2bdf58",
          "0x3f800000",
          "0x3f28e0bd",
          "0x3f28e0bd",
          "0x3f28e0bd",
          "0x3f800000",
          "0x3f272323",
          "0x3f272323",
          "0x3f272323",
          "0x3f800000",
          "0x3f25fe8a",
          "0x3f25fe8a",
          "0x3f25fe8a",
          "0x3f800000",
          "0x3f251bb1",
          "0x3f251bb1",
          "0x3f251bb1",
          "0x3f800000",
          "0x3f2447ae",
          "0x3f2447ae",
          "0x3f2447ae",
          "0x3f800000",
          "0x3f364193",
          "0x3f364193",
          "0x3f364193",
          "0x3f800000",
          "0x3f2e38af",
          "0x3f2e38af",
          "0x3f2e38af",
          "0x3f800000",
          "0x3f2a4fd5",
          "0x3f2a4fd5",
          "0x3f2a4fd5",
          "0x3f800000",
          "0x3f282f73",
          "0x3f282f73",
          "0x3f282f73",
          "0x3f800000",
          "0x3f26de62",
          "0x3f26de62",
          "0x3f26de62",
          "0x3f800000",
          "0x3f25f56c",
          "0x3f25f56c",
          "0x3f25f56c",
          "0x3f800000",
          "0x3f254d26",
          "0x3f254d26",
          "0x3f254d26",
          "0x3f800000"
        ],
        "f32_sha256": "d87a4033d8f1c820c25ea77bf66190fe4cead0a837704e9eb2acd2942dcdbf59",
        "rgba8_bytes": [
          172,
          172,
          172,
          255,
          169,
          169,
          169,
          255,
          167,
          167,
          167,
          255,
          165,
          165,
          165,
          255,
          164,
          164,
          164,
          255,
          164,
          164,
          164,
          255,
          163,
          163,
          163,
          255,
          177,
          177,
          177,
          255,
          171,
          171,
          171,
          255,
          168,
          168,
          168,
          255,
          166,
          166,
          166,
          255,
          165,
          165,
          165,
          255,
          164,
          164,
          164,
          255,
          164,
          164,
          164,
          255,
          182,
          182,
          182,
          255,
          174,
          174,
          174,
          255,
          170,
          170,
          170,
          255,
          168,
          168,
          168,
          255,
          166,
          166,
          166,
          255,
          165,
          165,
          165,
          255,
          165,
          165,
          165,
          255
        ],
        "rgba8_sha256": "7f71dc59b8540f092d688fd38421ef3d240c09f4490fd47e175f3cce8d171117"
      },
      "alpha_f32_word": "0x3f800000",
      "alpha_rgba8_byte": 255,
      "input_immutable_exact_bits": true,
      "bindings": {
        "resolution": [
          7,
          3
        ],
        "tileOffset": [
          0.375,
          -0.125
        ],
        "fullResolution": [
          7,
          3
        ],
        "time": 1.25,
        "cReal": -0.4,
        "cImag": 0.6,
        "poi": 0,
        "outputMode": 4,
        "centerX": 0.125,
        "centerY": -0.2,
        "rotation": 33,
        "iterations": 73,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 271,
        "cPath": 0,
        "cSpeed": 0,
        "cRadius": 0.5,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 2.5
      }
    }
  ],
  "source_mutation_contract": {
    "source_relative_path": "src/effects/adapters/julia.js",
    "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
    "shader_relative_path": "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/julia/julia.glsl",
    "shader_sha256": "825e175c22fea086ad2860e16bcf0a79d797574a9dfad937a23baaadaffdeef0",
    "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
    "execution": "each exact adapter source anchor/replacement is evaluated as a mutated juliaFactory and executed through bindCanonicalKernel/runPass"
  },
  "mutation_anchor_cardinality": {
    "total": 25,
    "by_group": {
      "cross-lane-assignment": 1,
      "df64-carrier": 4,
      "out-materialization": 10,
      "iteration-loop": 3,
      "log-sites": 4,
      "normal-three-sample": 3
    },
    "anchors": {
      "cross-lane-dz-assignment": 1,
      "df64-re2-carrier": 1,
      "df64-im2-carrier": 1,
      "df64-product-carrier": 1,
      "df64-next-re-carrier": 1,
      "out-iteration": 1,
      "out-z-magnitude2": 1,
      "out-derivative-magnitude2": 1,
      "out-stripe-sum": 1,
      "out-stripe-count": 1,
      "out-stripe-last": 1,
      "out-trap-min": 1,
      "transform-re-owner": 1,
      "transform-im-owner": 1,
      "loop-bound": 1,
      "loop-clamp-1001": 1,
      "period-loop-bound": 1,
      "log-smoothing": 1,
      "log-distance": 1,
      "log-stripe": 1,
      "log-stripe-normalization": 1,
      "normal-base": 1,
      "normal-right": 1,
      "normal-up": 1,
      "result-trap-number": 1
    }
  },
  "mutation_ledger": [
    {
      "name": "cross-lane-dz-assignment",
      "group": "cross-lane-assignment",
      "mechanism": "replace next-derivative temporary with source-order aliasing",
      "anchor": "const nextDerivativeX = F32(2 * F32(F32(reHigh * derivativeX) - F32(imHigh * derivativeY)))\n      derivativeY = F32(2 * F32(F32(reHigh * derivativeY) + F32(imHigh * derivativeX)))\n      derivativeX = nextDerivativeX",
      "replacement": "derivativeX = F32(2 * F32(F32(reHigh * derivativeX) - F32(imHigh * derivativeY)))\n      derivativeY = F32(2 * F32(F32(reHigh * derivativeY) + F32(imHigh * derivativeX)))",
      "independent": true,
      "source_anchor": "const nextDerivativeX = F32(2 * F32(F32(reHigh * derivativeX) - F32(imHigh * derivativeY)))\n      derivativeY = F32(2 * F32(F32(reHigh * derivativeY) + F32(imHigh * derivativeX)))\n      derivativeX = nextDerivativeX",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "9fdd53914591d4bb4209094359c1450847beef8bf0426bf737c872de286d081e",
      "anchor_sha256": "c83c5e436be035614cc98e1b8e96d71c5a31804e1c543c8e9001b9052ff4e44a",
      "replacement_sha256": "60737b08ed7eb5909a883d8c0fba2abf6ffe477ffe7fc747d15e84e3de2cddd1",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 45,
          "float32_witness": {
            "index": 0,
            "expected": "0x3e01ca12",
            "actual": "0x3d458f5c"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 32,
            "actual": 12
          }
        },
        {
          "case": "manual-stripe",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        }
      ],
      "result_sha256": "4acdbcb21f93a80e55b86b5146a1de0ae96b576d7b23889e01fdca7f7bbd77cf",
      "witness_cases": [
        "manual-distance-tile"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-stripe",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path",
        "non-square-f32-transform"
      ]
    },
    {
      "name": "df64-re2-carrier",
      "group": "df64-carrier",
      "mechanism": "replace df64 real-square carrier owner",
      "anchor": "const re2High = scratchHigh\n      const re2Low = scratchLow",
      "replacement": "const re2High = 0\n      const re2Low = 0",
      "independent": true,
      "source_anchor": "const re2High = scratchHigh\n      const re2Low = scratchLow",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "94c4d51c7c00b1ae740f57b0bc783c4d60a30aba5dc35312e3796069f16f4480",
      "anchor_sha256": "8179e52b0d81507ebe5ea947187d17e13369707e41a6724a1c3e9c4718d46333",
      "replacement_sha256": "7aff87de41586aa57188e9fadaed79afddb149412e1f898a9a2c2ba583b8f1eb",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 45,
          "float32_witness": {
            "index": 0,
            "expected": "0x3e01ca12",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 32,
            "actual": 0
          }
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 54,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f21db1a",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 161,
            "actual": 0
          }
        },
        {
          "case": "poi-trap",
          "differs": true,
          "changed_float32_lanes": 75,
          "changed_rgba8_bytes": 75,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f7ff7da",
            "actual": "0x3f6f502f"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 255,
            "actual": 238
          }
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 42,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x3f0d8dff"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 141
          }
        },
        {
          "case": "animated-circle",
          "differs": true,
          "changed_float32_lanes": 27,
          "changed_rgba8_bytes": 27,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x3dbcfe4d"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 0,
            "actual": 24
          }
        },
        {
          "case": "invert-output",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 36,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f800000",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 255,
            "actual": 0
          }
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f56a8ef",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 214,
            "actual": 0
          }
        },
        {
          "case": "bulb-path",
          "differs": true,
          "changed_float32_lanes": 12,
          "changed_rgba8_bytes": 12,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x3f800000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 0,
            "actual": 255
          }
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 36,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f6f5fec",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 238,
            "actual": 0
          }
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": true,
          "changed_float32_lanes": 63,
          "changed_rgba8_bytes": 63,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f2c9ba5",
            "actual": "0x3f12ce6e"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 172,
            "actual": 146
          }
        }
      ],
      "result_sha256": "15a47a2e97e32935c2851c33c16a79f73bfffcf07570f8b571e865b756f82ae2",
      "witness_cases": [
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "iterations-clamp-1001",
        "bulb-path",
        "fallback-trap-shape",
        "non-square-f32-transform"
      ],
      "control_cases": [
        "manual-smooth",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-c-path"
      ]
    },
    {
      "name": "df64-im2-carrier",
      "group": "df64-carrier",
      "mechanism": "replace df64 imaginary-square carrier owner",
      "anchor": "const im2High = scratchHigh\n      const im2Low = scratchLow",
      "replacement": "const im2High = 0\n      const im2Low = 0",
      "independent": true,
      "source_anchor": "const im2High = scratchHigh\n      const im2Low = scratchLow",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "5b81a2db3058cfab7595b182f445bfa32fa143279a8dc1ddf1e32f1416b54194",
      "anchor_sha256": "869cd06339a147e9cb452afdaded26b2cc082b17ff9d2e05d5fbdd0e60296d08",
      "replacement_sha256": "f728fc3c75861ac1908f3c99d0ea01a573cd339d8690a2d89f4b082b48bff44d",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": true,
          "changed_float32_lanes": 60,
          "changed_rgba8_bytes": 60,
          "float32_witness": {
            "index": 0,
            "expected": "0x3e01ca12",
            "actual": "0x3f2d9e2a"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 32,
            "actual": 173
          }
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 54,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f21db1a",
            "actual": "0x3f24768c"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 161,
            "actual": 164
          }
        },
        {
          "case": "poi-trap",
          "differs": true,
          "changed_float32_lanes": 75,
          "changed_rgba8_bytes": 75,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f7ff7da",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 255,
            "actual": 0
          }
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 45,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x3f12ce6e"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 146
          }
        },
        {
          "case": "animated-circle",
          "differs": true,
          "changed_float32_lanes": 6,
          "changed_rgba8_bytes": 6,
          "float32_witness": {
            "index": 12,
            "expected": "0x3db4ccd1",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 12,
            "expected": 23,
            "actual": 0
          }
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f56a8ef",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 214,
            "actual": 0
          }
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 36,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f6f5fec",
            "actual": "0x3f70f225"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 238,
            "actual": 240
          }
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": true,
          "changed_float32_lanes": 63,
          "changed_rgba8_bytes": 63,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f2c9ba5",
            "actual": "0x3f12ce6e"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 172,
            "actual": 146
          }
        }
      ],
      "result_sha256": "6df249c1c71abb6262030b8425d4d37628c629dc7fc44ff38aa7f6a6b5f3bad7",
      "witness_cases": [
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "iterations-clamp-1001",
        "fallback-trap-shape",
        "non-square-f32-transform"
      ],
      "control_cases": [
        "manual-smooth",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-c-path"
      ]
    },
    {
      "name": "df64-product-carrier",
      "group": "df64-carrier",
      "mechanism": "replace df64 product carrier owner",
      "anchor": "const productHigh = scratchHigh\n      const productLow = scratchLow",
      "replacement": "const productHigh = 0\n      const productLow = 0",
      "independent": true,
      "source_anchor": "const productHigh = scratchHigh\n      const productLow = scratchLow",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "78904c52122d5ab142be1628ff4290dac7d143b529f4116dd4df4ad1927ad0fc",
      "anchor_sha256": "bf08c13264b7df9f6d350909bf4fbaee0ec152b327f508c9c971c80dedbc8e40",
      "replacement_sha256": "76695fed4c1fa0e89f85bc1ca8703292489b39d3bf317152ee53cfc328a0fbce",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": true,
          "changed_float32_lanes": 60,
          "changed_rgba8_bytes": 60,
          "float32_witness": {
            "index": 0,
            "expected": "0x3e01ca12",
            "actual": "0x3f800000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 32,
            "actual": 255
          }
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 54,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f21db1a",
            "actual": "0x3f044dc6"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 161,
            "actual": 132
          }
        },
        {
          "case": "poi-trap",
          "differs": true,
          "changed_float32_lanes": 75,
          "changed_rgba8_bytes": 75,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f7ff7da",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 255,
            "actual": 0
          }
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 45,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x3f12ce6e"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 146
          }
        },
        {
          "case": "animated-circle",
          "differs": true,
          "changed_float32_lanes": 6,
          "changed_rgba8_bytes": 6,
          "float32_witness": {
            "index": 12,
            "expected": "0x3db4ccd1",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 12,
            "expected": 23,
            "actual": 0
          }
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f56a8ef",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 214,
            "actual": 0
          }
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 36,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f6f5fec",
            "actual": "0x3f710295"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 238,
            "actual": 240
          }
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": true,
          "changed_float32_lanes": 63,
          "changed_rgba8_bytes": 63,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f2c9ba5",
            "actual": "0x3f12ce6e"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 172,
            "actual": 146
          }
        }
      ],
      "result_sha256": "77da401b37b415f8286e8599265f3035a8d9ded0091b0c1e1cf0348121270afa",
      "witness_cases": [
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "iterations-clamp-1001",
        "fallback-trap-shape",
        "non-square-f32-transform"
      ],
      "control_cases": [
        "manual-smooth",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-c-path"
      ]
    },
    {
      "name": "df64-next-re-carrier",
      "group": "df64-carrier",
      "mechanism": "replace df64 next-real carrier owner",
      "anchor": "const nextReHigh = scratchHigh\n      const nextReLow = scratchLow",
      "replacement": "const nextReHigh = 0\n      const nextReLow = 0",
      "independent": true,
      "source_anchor": "const nextReHigh = scratchHigh\n      const nextReLow = scratchLow",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "900bf690c575f4fdc517db041aac51ef59f78051ff257616e1750fe3dbbd1813",
      "anchor_sha256": "d6589040e2a74df6e07a87fde42351b2fd29cc93550947d1106b23f6d8c0fc4d",
      "replacement_sha256": "3a1ab0e1e7a77817560db1257ff5e1d0a782e99ae4e0c09512501a932b87b84d",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 45,
          "float32_witness": {
            "index": 0,
            "expected": "0x3e01ca12",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 32,
            "actual": 0
          }
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 54,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f21db1a",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 161,
            "actual": 0
          }
        },
        {
          "case": "poi-trap",
          "differs": true,
          "changed_float32_lanes": 75,
          "changed_rgba8_bytes": 75,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f7ff7da",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 255,
            "actual": 0
          }
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 45,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x3f12ce6e"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 146
          }
        },
        {
          "case": "animated-circle",
          "differs": true,
          "changed_float32_lanes": 6,
          "changed_rgba8_bytes": 6,
          "float32_witness": {
            "index": 12,
            "expected": "0x3db4ccd1",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 12,
            "expected": 23,
            "actual": 0
          }
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f56a8ef",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 214,
            "actual": 0
          }
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 36,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f6f5fec",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 238,
            "actual": 0
          }
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": true,
          "changed_float32_lanes": 63,
          "changed_rgba8_bytes": 63,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f2c9ba5",
            "actual": "0x3f12ce6e"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 172,
            "actual": 146
          }
        }
      ],
      "result_sha256": "3251bfa71d38c3b48b52ec497f7ef4c4bf1335ba79cfc880058ffa1cb41de247",
      "witness_cases": [
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "iterations-clamp-1001",
        "fallback-trap-shape",
        "non-square-f32-transform"
      ],
      "control_cases": [
        "manual-smooth",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-c-path"
      ]
    },
    {
      "name": "out-iteration",
      "group": "out-materialization",
      "mechanism": "mutate iteration result owner materialization",
      "anchor": "result.iteration = iteration",
      "replacement": "result.iteration = 0",
      "independent": true,
      "source_anchor": "result.iteration = iteration",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "c8f88c760fad861bfb6dbc4cd63f2f9a2c127daa35d2645e21418a8d8258ea3d",
      "anchor_sha256": "30c8fb06d7d4f895e14cb9b022ff7c4192e3ca90fe8780cc4de9ffb8b2610d4e",
      "replacement_sha256": "7c4cfbe45467c7ae34c862d91ea3a57fca56ae082223347c90bebf83c421e206",
      "results": [
        {
          "case": "manual-smooth",
          "differs": true,
          "changed_float32_lanes": 60,
          "changed_rgba8_bytes": 0,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-stripe",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 45,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x3f12ce6e"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 146
          }
        },
        {
          "case": "animated-circle",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 6,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": {
            "index": 12,
            "expected": 23,
            "actual": 0
          }
        },
        {
          "case": "invert-output",
          "differs": true,
          "changed_float32_lanes": 6,
          "changed_rgba8_bytes": 6,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f800000",
            "actual": "0x3f7e81c6"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 255,
            "actual": 254
          }
        },
        {
          "case": "animated-lissajous",
          "differs": true,
          "changed_float32_lanes": 27,
          "changed_rgba8_bytes": 27,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x3f7ff4eb"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 0,
            "actual": 255
          }
        },
        {
          "case": "iterations-min",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 0,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x3f56a8ef"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 0,
            "actual": 214
          }
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": true,
          "changed_float32_lanes": 6,
          "changed_rgba8_bytes": 0,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x3f800000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 0,
            "actual": 255
          }
        },
        {
          "case": "fallback-output-mode",
          "differs": true,
          "changed_float32_lanes": 60,
          "changed_rgba8_bytes": 0,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 0,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": true,
          "changed_float32_lanes": 63,
          "changed_rgba8_bytes": 63,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f2c9ba5",
            "actual": "0x3f12ce6e"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 172,
            "actual": 146
          }
        }
      ],
      "result_sha256": "f50656a389d4bbd9370f9d19a61822df479dfe125386d8b083e34cdd2b90bc1d",
      "witness_cases": [
        "manual-smooth",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "bulb-path",
        "period-convergence",
        "fallback-output-mode",
        "fallback-c-path",
        "non-square-f32-transform"
      ],
      "control_cases": [
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "iterations-clamp-1001",
        "poi-fallback",
        "fallback-trap-shape"
      ]
    },
    {
      "name": "out-z-magnitude2",
      "group": "out-materialization",
      "mechanism": "mutate zMagnitude2 result owner materialization",
      "anchor": "result.zMagnitude2 = F32(F32(reHigh * reHigh) + F32(imHigh * imHigh))",
      "replacement": "result.zMagnitude2 = 0",
      "independent": true,
      "source_anchor": "result.zMagnitude2 = F32(F32(reHigh * reHigh) + F32(imHigh * imHigh))",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "69507160fcd2f53af070bd4db5c14749f09a7475339f72f498d5495993613427",
      "anchor_sha256": "7ba3eacc7b9b8b8da2605660a467a5bce50d9e9b6e07c19454d550a2b66e8f66",
      "replacement_sha256": "d36ed37ea88cc317e08d4c3ac1e323f95b964662c0462e1a851a0a3cf133a0e5",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 45,
          "float32_witness": {
            "index": 0,
            "expected": "0x3e01ca12",
            "actual": "0x7fc00000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 32,
            "actual": 0
          }
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 54,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f21db1a",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 161,
            "actual": 0
          }
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 48,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 0
          }
        },
        {
          "case": "animated-circle",
          "differs": true,
          "changed_float32_lanes": 6,
          "changed_rgba8_bytes": 6,
          "float32_witness": {
            "index": 12,
            "expected": "0x3db4ccd1",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": {
            "index": 12,
            "expected": 23,
            "actual": 0
          }
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": true,
          "changed_float32_lanes": 63,
          "changed_rgba8_bytes": 63,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f2c9ba5",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 172,
            "actual": 0
          }
        }
      ],
      "result_sha256": "e9ec50a9e509fa3847ba149892528d5320aa08418a98fa566e697f3badde58a9",
      "witness_cases": [
        "manual-distance-tile",
        "manual-stripe",
        "manual-normal",
        "animated-circle",
        "non-square-f32-transform"
      ],
      "control_cases": [
        "manual-smooth",
        "poi-trap",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path"
      ]
    },
    {
      "name": "out-derivative-magnitude2",
      "group": "out-materialization",
      "mechanism": "mutate derivativeMagnitude2 result owner materialization",
      "anchor": "result.derivativeMagnitude2 = F32(F32(derivativeX * derivativeX) + F32(derivativeY * derivativeY))",
      "replacement": "result.derivativeMagnitude2 = 0",
      "independent": true,
      "source_anchor": "result.derivativeMagnitude2 = F32(F32(derivativeX * derivativeX) + F32(derivativeY * derivativeY))",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "d836409e43fa5c3b1a222303b8a40dcba144eff89a813720ac5ee2773fe86541",
      "anchor_sha256": "0aa48418f5c21ee957c609cdf0331624a843282cfb70eb70183de6d0870c9504",
      "replacement_sha256": "4938e9681edd141d48686819c27b08698980e07efc1757c4e65917c5e470bec6",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 45,
          "float32_witness": {
            "index": 0,
            "expected": "0x3e01ca12",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 32,
            "actual": 0
          }
        },
        {
          "case": "manual-stripe",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        }
      ],
      "result_sha256": "bda52bbbf81c7ae6324de92efa8ed6031d752b00bfadee8a72261d62e28ce8cf",
      "witness_cases": [
        "manual-distance-tile"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-stripe",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path",
        "non-square-f32-transform"
      ]
    },
    {
      "name": "out-stripe-sum",
      "group": "out-materialization",
      "mechanism": "mutate stripeSum result owner materialization",
      "anchor": "result.stripeSum = stripeSum",
      "replacement": "result.stripeSum = 0",
      "independent": true,
      "source_anchor": "result.stripeSum = stripeSum",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "c1e17b234f588162749c5a8766c48af04fd231af2ff24b7f439a580326fbbd33",
      "anchor_sha256": "66392efe93e894248bac6c6bca7ae0d8f8549199289356b51b8ee66e1cfe7eb6",
      "replacement_sha256": "fd870248bb90468d89ea28efe5c0c9d53ecc29b04edcf28bc48e9de75de94471",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 54,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f21db1a",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 161,
            "actual": 0
          }
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        }
      ],
      "result_sha256": "29d37266e62062713a9f57016275b0d427adeb2171aed6ce08e70f0ff061a209",
      "witness_cases": [
        "manual-stripe"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-distance-tile",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path",
        "non-square-f32-transform"
      ]
    },
    {
      "name": "out-stripe-count",
      "group": "out-materialization",
      "mechanism": "mutate stripeCount result owner materialization",
      "anchor": "result.stripeCount = stripeCount",
      "replacement": "result.stripeCount = stripeCount + 1",
      "independent": true,
      "source_anchor": "result.stripeCount = stripeCount",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "0bb332675454140bf47a02c53d47d18a8667500a0c6a642a616919b75c204a66",
      "anchor_sha256": "d79ff37e0390f4091a72fe78876b0caa2f92347cf4eefff5bbbeca74a5b765fe",
      "replacement_sha256": "0f9d1fbd21929c819e18d9ac761c6492b874dfed91d452c17baf867baea78651",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 54,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f21db1a",
            "actual": "0x3f19b2ee"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 161,
            "actual": 153
          }
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        }
      ],
      "result_sha256": "42ab9d6e31b8f9b24a2c257d5564337d00b3e0f89ae62ed5d1eb5c5a2f8c65b7",
      "witness_cases": [
        "manual-stripe"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-distance-tile",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path",
        "non-square-f32-transform"
      ]
    },
    {
      "name": "out-stripe-last",
      "group": "out-materialization",
      "mechanism": "mutate stripeLast result owner materialization",
      "anchor": "result.stripeLast = stripeLast",
      "replacement": "result.stripeLast = 0",
      "independent": true,
      "source_anchor": "result.stripeLast = stripeLast",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "bf00af11ec4f923f4c29890f8b53f55eaab6aaf36667dbd835513871fbf02018",
      "anchor_sha256": "69a85b0ccde99c3821f03dde06cb9e4ec3c94d7cbd1aae65306f3c75d6e65b4a",
      "replacement_sha256": "e6b5d74c85d2c2ee381cb0302783776b2a008732775233d75d870d4a63f6ede5",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 36,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f21db1a",
            "actual": "0x3f237eee"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 161,
            "actual": 163
          }
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        }
      ],
      "result_sha256": "399c49689696fbb38060af8b5ca33c2f50c9f595a6df829859ff49013d22a5b3",
      "witness_cases": [
        "manual-stripe"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-distance-tile",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path",
        "non-square-f32-transform"
      ]
    },
    {
      "name": "out-trap-min",
      "group": "out-materialization",
      "mechanism": "mutate trapMin result owner materialization",
      "anchor": "result.trapMin = trapMin",
      "replacement": "result.trapMin = 1",
      "independent": true,
      "source_anchor": "result.trapMin = trapMin",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "0c18b2a9a2d2e2989e1bcc8f53ffbfb34606726710dc03b2f64d4358faef04aa",
      "anchor_sha256": "1a01779573462d720c6ae74e6bb10083ad6a9c3209ca508c262088f3903b1df2",
      "replacement_sha256": "5648290fd2fc4f963aed60553d5e08eb31bd05d7e9dc77c6853fcb4612e58ae9",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-stripe",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-trap",
          "differs": true,
          "changed_float32_lanes": 75,
          "changed_rgba8_bytes": 75,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f7ff7da",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 255,
            "actual": 0
          }
        },
        {
          "case": "manual-normal",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f56a8ef",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 214,
            "actual": 0
          }
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 36,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f6f5fec",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 238,
            "actual": 0
          }
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        }
      ],
      "result_sha256": "52e45382437e15a0004b2c25fea5b1dcbb522ec8f08c15ef10be2dfd85fc5997",
      "witness_cases": [
        "poi-trap",
        "iterations-clamp-1001",
        "fallback-trap-shape"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-distance-tile",
        "manual-stripe",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-c-path",
        "non-square-f32-transform"
      ]
    },
    {
      "name": "transform-re-owner",
      "group": "out-materialization",
      "mechanism": "mutate transform real coordinate owner",
      "anchor": "coordinates[0] = scratchHigh",
      "replacement": "coordinates[0] = 0",
      "independent": true,
      "source_anchor": "coordinates[0] = scratchHigh",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "e0db5ab13c82c1a50b6a2538bd97aaff2317d0f8a45345e21675abe6760d0e4b",
      "anchor_sha256": "04cd174c201170ba87b4cc0f4c8e3a832aba6cff09ffcd6a884156ca9d4d627e",
      "replacement_sha256": "8826e0fbf5c6623a03a15cfe86306fa89e8ad1df362be765d151b390b26a0a51",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": true,
          "changed_float32_lanes": 60,
          "changed_rgba8_bytes": 57,
          "float32_witness": {
            "index": 0,
            "expected": "0x3e01ca12",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 32,
            "actual": 0
          }
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 48,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f21db1a",
            "actual": "0x3f1ec5d5"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 161,
            "actual": 158
          }
        },
        {
          "case": "poi-trap",
          "differs": true,
          "changed_float32_lanes": 75,
          "changed_rgba8_bytes": 75,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f7ff7da",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 255,
            "actual": 0
          }
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 45,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x3f12ce6e"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 146
          }
        },
        {
          "case": "animated-circle",
          "differs": true,
          "changed_float32_lanes": 6,
          "changed_rgba8_bytes": 6,
          "float32_witness": {
            "index": 12,
            "expected": "0x3db4ccd1",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 12,
            "expected": 23,
            "actual": 0
          }
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f56a8ef",
            "actual": "0x3f7e8396"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 214,
            "actual": 254
          }
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 24,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f6f5fec",
            "actual": "0x3f7d45b8"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 238,
            "actual": 252
          }
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": true,
          "changed_float32_lanes": 63,
          "changed_rgba8_bytes": 63,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f2c9ba5",
            "actual": "0x3f12ce6e"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 172,
            "actual": 146
          }
        }
      ],
      "result_sha256": "e99ceaec06045d872d591a097cac99c40fd34aab391271c90bb029d1456bbdc6",
      "witness_cases": [
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "iterations-clamp-1001",
        "fallback-trap-shape",
        "non-square-f32-transform"
      ],
      "control_cases": [
        "manual-smooth",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-c-path"
      ]
    },
    {
      "name": "transform-im-owner",
      "group": "out-materialization",
      "mechanism": "mutate transform imaginary coordinate owner",
      "anchor": "coordinates[2] = scratchHigh",
      "replacement": "coordinates[2] = 0",
      "independent": true,
      "source_anchor": "coordinates[2] = scratchHigh",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "7d4ac5cb76054fa93bfa948bd867b32343ff171ab19d37308219c78db8156292",
      "anchor_sha256": "7d323b5bac250bf655fecb32049b8754f5f65b9f5e2f2edac90caf7a993d2444",
      "replacement_sha256": "6b85f53f990d823afdd18bd215c236941a89c26d9b5be1365d8b57daad46bcfc",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": true,
          "changed_float32_lanes": 60,
          "changed_rgba8_bytes": 60,
          "float32_witness": {
            "index": 0,
            "expected": "0x3e01ca12",
            "actual": "0x3ca2a71a"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 32,
            "actual": 5
          }
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 36,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f21db1a",
            "actual": "0x3f151447"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 161,
            "actual": 148
          }
        },
        {
          "case": "poi-trap",
          "differs": true,
          "changed_float32_lanes": 75,
          "changed_rgba8_bytes": 0,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f7ff7da",
            "actual": "0x3f7f9b35"
          },
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 48,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x3f15cdf7"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 149
          }
        },
        {
          "case": "animated-circle",
          "differs": true,
          "changed_float32_lanes": 6,
          "changed_rgba8_bytes": 6,
          "float32_witness": {
            "index": 12,
            "expected": "0x3db4ccd1",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 12,
            "expected": 23,
            "actual": 0
          }
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x3ef0a5ce"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 0,
            "actual": 120
          }
        },
        {
          "case": "iterations-clamp-1001",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f56a8ef",
            "actual": "0x3ef0a5ce"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 214,
            "actual": 120
          }
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": true,
          "changed_float32_lanes": 24,
          "changed_rgba8_bytes": 18,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f6f5fec",
            "actual": "0x3f7ec631"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 238,
            "actual": 254
          }
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": true,
          "changed_float32_lanes": 63,
          "changed_rgba8_bytes": 63,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f2c9ba5",
            "actual": "0x3f184d7d"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 172,
            "actual": 152
          }
        }
      ],
      "result_sha256": "f7af78218f8f7d1f4b3e71f2970da9c6bbe5d1487fb2a716dce795a9ec5924f3",
      "witness_cases": [
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "iterations-max",
        "iterations-clamp-1001",
        "fallback-trap-shape",
        "non-square-f32-transform"
      ],
      "control_cases": [
        "manual-smooth",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-c-path"
      ]
    },
    {
      "name": "loop-bound",
      "group": "iteration-loop",
      "mechanism": "shorten Julia outer iteration bound",
      "anchor": "Math.min(maxIterations, 1000)",
      "replacement": "Math.min(maxIterations, 1)",
      "independent": true,
      "source_anchor": "Math.min(maxIterations, 1000)",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "dc56981c1d347992b9c390393acd073b9640afc653b476027230b2c437f8f4fb",
      "anchor_sha256": "d7827a7823840b51b49c31a86c8e2653bb2d14e2b28d599205c61f29ce05d461",
      "replacement_sha256": "848242238dd18b61ae89a14eebdf9ce4857f349e446cf4f62907e58e715f5c1f",
      "results": [
        {
          "case": "manual-smooth",
          "differs": true,
          "changed_float32_lanes": 60,
          "changed_rgba8_bytes": 0,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": true,
          "changed_float32_lanes": 60,
          "changed_rgba8_bytes": 45,
          "float32_witness": {
            "index": 0,
            "expected": "0x3e01ca12",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 32,
            "actual": 0
          }
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 54,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f21db1a",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 161,
            "actual": 0
          }
        },
        {
          "case": "poi-trap",
          "differs": true,
          "changed_float32_lanes": 75,
          "changed_rgba8_bytes": 75,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f7ff7da",
            "actual": "0x3f4fbd00"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 255,
            "actual": 207
          }
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 48,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 0
          }
        },
        {
          "case": "animated-circle",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 6,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": {
            "index": 12,
            "expected": 23,
            "actual": 0
          }
        },
        {
          "case": "invert-output",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 36,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f800000",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 255,
            "actual": 0
          }
        },
        {
          "case": "animated-lissajous",
          "differs": true,
          "changed_float32_lanes": 27,
          "changed_rgba8_bytes": 27,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x3f7ff1cf"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 0,
            "actual": 255
          }
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x3e19f5f7"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 0,
            "actual": 38
          }
        },
        {
          "case": "iterations-clamp-1001",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f56a8ef",
            "actual": "0x3e19f5f7"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 214,
            "actual": 38
          }
        },
        {
          "case": "bulb-path",
          "differs": true,
          "changed_float32_lanes": 12,
          "changed_rgba8_bytes": 0,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": true,
          "changed_float32_lanes": 12,
          "changed_rgba8_bytes": 0,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": true,
          "changed_float32_lanes": 60,
          "changed_rgba8_bytes": 0,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 36,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f6f5fec",
            "actual": "0x3e93f34f"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 238,
            "actual": 74
          }
        },
        {
          "case": "fallback-c-path",
          "differs": true,
          "changed_float32_lanes": 36,
          "changed_rgba8_bytes": 0,
          "float32_witness": {
            "index": 0,
            "expected": "0x00000000",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": true,
          "changed_float32_lanes": 63,
          "changed_rgba8_bytes": 63,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f2c9ba5",
            "actual": "0x7fe00000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 172,
            "actual": 0
          }
        }
      ],
      "result_sha256": "b7e2fad5e0b22d15dac9c45cb2e259aca69928363111918be8aefb5348634e18",
      "witness_cases": [
        "manual-smooth",
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path",
        "non-square-f32-transform"
      ],
      "control_cases": [
        "iterations-min",
        "period-convergence"
      ]
    },
    {
      "name": "loop-clamp-1001",
      "group": "iteration-loop",
      "mechanism": "remove the runtime maxIterations clamp at the direct 1001 boundary",
      "anchor": "Math.min(maxIterations, 1000)",
      "replacement": "maxIterations",
      "independent": true,
      "source_anchor": "Math.min(maxIterations, 1000)",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "a5c1e3fe9530d06a8d6ccfaafd3f1b29c2221a35a7a874b6d48881281d9a9a18",
      "anchor_sha256": "d7827a7823840b51b49c31a86c8e2653bb2d14e2b28d599205c61f29ce05d461",
      "replacement_sha256": "825df14610cc75d3e2a1e1e35276bce9686d82063e3d66f9c449100bc1e74f7b",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-stripe",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f56a8ef",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 214,
            "actual": 0
          }
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        }
      ],
      "result_sha256": "8d2097f509bb15eb75a1f3d7e4c184ef8a55d303c1c80585eec4cec8b2fcb796",
      "witness_cases": [
        "iterations-clamp-1001"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path",
        "non-square-f32-transform"
      ]
    },
    {
      "name": "period-loop-bound",
      "group": "iteration-loop",
      "mechanism": "widen period detection convergence bound",
      "anchor": "Math.hypot(reHigh - slowX, imHigh - slowY) < 1e-10",
      "replacement": "Math.hypot(reHigh - slowX, imHigh - slowY) < 1e-1",
      "independent": true,
      "source_anchor": "Math.hypot(reHigh - slowX, imHigh - slowY) < 1e-10",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "1fb47da10ab8baa42ee7fd469724eb7d282b8c37d8ec02ba767f23cbd47a5c5e",
      "anchor_sha256": "447482a148196100135bf5d27c8fa26cf758afd687b5207a377a0ae10395c3cd",
      "replacement_sha256": "f65b14b1826bb113e75206d47e8644461c4cd4feeb9a24718d557a1b1134c16a",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": true,
          "changed_float32_lanes": 27,
          "changed_rgba8_bytes": 18,
          "float32_witness": {
            "index": 8,
            "expected": "0x3a02883a",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 12,
            "expected": 7,
            "actual": 0
          }
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 18,
          "changed_rgba8_bytes": 18,
          "float32_witness": {
            "index": 16,
            "expected": "0x3f25aa90",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 16,
            "expected": 165,
            "actual": 0
          }
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 45,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x3f12ce6e"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 146
          }
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": true,
          "changed_float32_lanes": 3,
          "changed_rgba8_bytes": 3,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f56a8ef",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 214,
            "actual": 0
          }
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": true,
          "changed_float32_lanes": 12,
          "changed_rgba8_bytes": 12,
          "float32_witness": {
            "index": 12,
            "expected": "0x3f7eaf3d",
            "actual": "0x00000000"
          },
          "rgba8_witness": {
            "index": 12,
            "expected": 254,
            "actual": 0
          }
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        }
      ],
      "result_sha256": "ea095a58e3b6d5df72611ca9dfbd20f602979362bf390b78da3cc5fb8b6c82a2",
      "witness_cases": [
        "manual-distance-tile",
        "manual-stripe",
        "manual-normal",
        "iterations-clamp-1001",
        "fallback-trap-shape"
      ],
      "control_cases": [
        "manual-smooth",
        "poi-trap",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-c-path",
        "non-square-f32-transform"
      ]
    },
    {
      "name": "log-smoothing",
      "group": "log-sites",
      "mechanism": "mutate smooth iteration logarithm",
      "anchor": "const nu = Math.log(logMagnitude / LOG2) / LOG2\n    return clamp((iterationResult.iteration + 1 - nu) / maxIterations)",
      "replacement": "const nu = Math.log(logMagnitude / LOG2) / (LOG2 * 2)\n    return clamp((iterationResult.iteration + 1 - nu) / maxIterations)",
      "independent": true,
      "source_anchor": "const nu = Math.log(logMagnitude / LOG2) / LOG2\n    return clamp((iterationResult.iteration + 1 - nu) / maxIterations)",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "9937f3ecb41404f1c3f4a90763f31c75435c0baf0e88740eec6f539be5ccf0fc",
      "anchor_sha256": "d3bdfef870e6dc5fd8912686b44441d8441f6ad793f0caff514c9f46752e1f3a",
      "replacement_sha256": "cd6ca2a350c60483ae4e939d5283d448a9c577b3d79d39454e7af1dfcd665603",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-stripe",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 42,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x3f108c2b"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 144
          }
        },
        {
          "case": "animated-circle",
          "differs": true,
          "changed_float32_lanes": 6,
          "changed_rgba8_bytes": 6,
          "float32_witness": {
            "index": 12,
            "expected": "0x3db4ccd1",
            "actual": "0x3dea6668"
          },
          "rgba8_witness": {
            "index": 12,
            "expected": 23,
            "actual": 29
          }
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": true,
          "changed_float32_lanes": 63,
          "changed_rgba8_bytes": 63,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f2c9ba5",
            "actual": "0x3f36ad71"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 172,
            "actual": 182
          }
        }
      ],
      "result_sha256": "ed124e272782a8e08152fca66b52c5c26e42310cd1e384244392c2edaf247086",
      "witness_cases": [
        "manual-normal",
        "animated-circle",
        "non-square-f32-transform"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path"
      ]
    },
    {
      "name": "log-distance",
      "group": "log-sites",
      "mechanism": "mutate distance estimation logarithm",
      "anchor": "Math.log(2 * magnitude * Math.log(magnitude) / derivative + 1) * 2",
      "replacement": "Math.log(2 * magnitude * Math.log(magnitude * 2) / derivative + 1) * 2",
      "independent": true,
      "source_anchor": "Math.log(2 * magnitude * Math.log(magnitude) / derivative + 1) * 2",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "e7b841834a4022189633c1374841a638b0e1c5dbc567059d0e3b7b84461fa50b",
      "anchor_sha256": "b25f59f85a9fc1f67ab9871f119ece6223efe996d84d10e4713a050cd6f88b20",
      "replacement_sha256": "23792fe1424127784d6fbbdcbf39cbb0929ed9248a0a75def3f46d265839f78d",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 39,
          "float32_witness": {
            "index": 0,
            "expected": "0x3e01ca12",
            "actual": "0x3e0bcee9"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 32,
            "actual": 35
          }
        },
        {
          "case": "manual-stripe",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        }
      ],
      "result_sha256": "d7c742fe96564afc28cb5d863d1b24119c0ef8ae4ed0e60feca4fe2e9cfe918c",
      "witness_cases": [
        "manual-distance-tile"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-stripe",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path",
        "non-square-f32-transform"
      ]
    },
    {
      "name": "log-stripe",
      "group": "log-sites",
      "mechanism": "mutate stripe logarithm",
      "anchor": "const logMagnitude = Math.log(r.zMagnitude2) * 0.5",
      "replacement": "const logMagnitude = Math.log(r.zMagnitude2) * 5",
      "independent": true,
      "source_anchor": "const logMagnitude = Math.log(r.zMagnitude2) * 0.5",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "c2da8e6fccffc9ae07940766e80c928d88e4641d7a6c23eae259d53c69c983f8",
      "anchor_sha256": "a8ab022104954ba54031d07439b3370f16a0429130ef09ee0077c44782d3238d",
      "replacement_sha256": "e25fa0a0c4a95a122b863167b47c6b43cd7c01ac8aa96371d8341a3a16c48500",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 36,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f21db1a",
            "actual": "0x3f214823"
          },
          "rgba8_witness": {
            "index": 4,
            "expected": 163,
            "actual": 164
          }
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        }
      ],
      "result_sha256": "fa98057c765a6f6901336ba44627a27efab51397e85fc694cc608c2e677a0292",
      "witness_cases": [
        "manual-stripe"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-distance-tile",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path",
        "non-square-f32-transform"
      ]
    },
    {
      "name": "log-stripe-normalization",
      "group": "log-sites",
      "mechanism": "mutate stripe normalization logarithm",
      "anchor": "const nu = Math.log(logMagnitude / LOG2) / LOG2\n          value = clamp(mix(previous, average",
      "replacement": "const nu = Math.log(logMagnitude / LOG2) / (LOG2 * 10)\n          value = clamp(mix(previous, average",
      "independent": true,
      "source_anchor": "const nu = Math.log(logMagnitude / LOG2) / LOG2\n          value = clamp(mix(previous, average",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "328117479d486f509a70358ae46b8beda46b311f70084e0998f01c3d06f2d1a9",
      "anchor_sha256": "c9a5e600d8ac570b5a455d0abe636b41250288e4c2dd9e539de3d89cd310566f",
      "replacement_sha256": "a73eaca2557ae94a9f8c1a9012d0f0a901df7f728417738a426d9604438f94a4",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-stripe",
          "differs": true,
          "changed_float32_lanes": 54,
          "changed_rgba8_bytes": 12,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f21db1a",
            "actual": "0x3f219098"
          },
          "rgba8_witness": {
            "index": 12,
            "expected": 158,
            "actual": 157
          }
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        }
      ],
      "result_sha256": "b0088d0eaaf30bcc4f15841d75b8e3b4abcd1b540dc177a68d041ea155df9eab",
      "witness_cases": [
        "manual-stripe"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-distance-tile",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path",
        "non-square-f32-transform"
      ]
    },
    {
      "name": "normal-base",
      "group": "normal-three-sample",
      "mechanism": "mutate normal base sample coordinate",
      "anchor": "const base = iterateSmooth(globalX, globalY, constant[0], constant[1], $bindings.iterations, zoom)",
      "replacement": "const base = iterateSmooth(globalX + 1, globalY, constant[0], constant[1], $bindings.iterations, zoom)",
      "independent": true,
      "source_anchor": "const base = iterateSmooth(globalX, globalY, constant[0], constant[1], $bindings.iterations, zoom)",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "66c65e0b35b23b2d1f045ebc4b9526ff9f34c4ad8f387deddebbc142cec3ccb3",
      "anchor_sha256": "ce8cafa48121a9466b05c1f0af84d75f2519ab4db210237cc85ac291fc403d76",
      "replacement_sha256": "3e04065cbf9c389094b96442deb9efd72d584a8880ab25b33582377cc472db88",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-stripe",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 48,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x3f1252c3"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 146
          }
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": true,
          "changed_float32_lanes": 63,
          "changed_rgba8_bytes": 63,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f2c9ba5",
            "actual": "0x3f229e44"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 172,
            "actual": 162
          }
        }
      ],
      "result_sha256": "8520a894a1cdd89832fb2750eb673c9c9ca354e64137ab7b2f98953a1bc5e565",
      "witness_cases": [
        "manual-normal",
        "non-square-f32-transform"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path"
      ]
    },
    {
      "name": "normal-right",
      "group": "normal-three-sample",
      "mechanism": "mutate normal right sample coordinate",
      "anchor": "const right = iterateSmooth(globalX + 1, globalY, constant[0], constant[1], $bindings.iterations, zoom)",
      "replacement": "const right = iterateSmooth(globalX, globalY, constant[0], constant[1], $bindings.iterations, zoom)",
      "independent": true,
      "source_anchor": "const right = iterateSmooth(globalX + 1, globalY, constant[0], constant[1], $bindings.iterations, zoom)",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "c124fce8fea05b2c9f75ce6d3e5f6c9bbe9aa1b2b1de4bdb79a11f98e4b3c8f9",
      "anchor_sha256": "ad0e24dfb436b1d9a353c9f662a29c736ff41e054eb09bd846ba6cc0576f264a",
      "replacement_sha256": "5ba5243c6744df3cc79bdf3c3c7c6a000cbb804e3d0936b9101fe3f7632ba490",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-stripe",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 48,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x3f0909cd"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 137
          }
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": true,
          "changed_float32_lanes": 63,
          "changed_rgba8_bytes": 9,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f2c9ba5",
            "actual": "0x3f2d0f3a"
          },
          "rgba8_witness": {
            "index": 28,
            "expected": 177,
            "actual": 178
          }
        }
      ],
      "result_sha256": "fa3cb216ac0941e39827719196c4166658bd8c6cf4cb1db3e5d3143f2296925c",
      "witness_cases": [
        "manual-normal",
        "non-square-f32-transform"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path"
      ]
    },
    {
      "name": "normal-up",
      "group": "normal-three-sample",
      "mechanism": "mutate normal up sample coordinate",
      "anchor": "const up = iterateSmooth(globalX, globalY + 1, constant[0], constant[1], $bindings.iterations, zoom)",
      "replacement": "const up = iterateSmooth(globalX, globalY, constant[0], constant[1], $bindings.iterations, zoom)",
      "independent": true,
      "source_anchor": "const up = iterateSmooth(globalX, globalY + 1, constant[0], constant[1], $bindings.iterations, zoom)",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "32d90bc43c3c826cedfa0bb03c268b34e53babd03187fb3d826ca3a45bf75797",
      "anchor_sha256": "80ab37e7e4f95e706d4b5473d54d6704ec700dbc78e78462464dc3af644798fb",
      "replacement_sha256": "59be8b2147353bae92cd1b09433f6d57c1bcd283d158fddf9a5eebff852ebe0e",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-stripe",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": true,
          "changed_float32_lanes": 48,
          "changed_rgba8_bytes": 48,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f0e1ac1",
            "actual": "0x3f17ddfd"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 142,
            "actual": 151
          }
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": true,
          "changed_float32_lanes": 63,
          "changed_rgba8_bytes": 63,
          "float32_witness": {
            "index": 0,
            "expected": "0x3f2c9ba5",
            "actual": "0x3f126349"
          },
          "rgba8_witness": {
            "index": 0,
            "expected": 172,
            "actual": 146
          }
        }
      ],
      "result_sha256": "59e3cfc76f8f46b63c0d269912d1b036d0fa0bb062ace36dd7a46e450954a058",
      "witness_cases": [
        "manual-normal",
        "non-square-f32-transform"
      ],
      "control_cases": [
        "manual-smooth",
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path"
      ]
    },
    {
      "name": "result-trap-number",
      "group": "out-materialization",
      "mechanism": "preserve the JS Number trap accumulator instead of forcing an unsafe Float32 result boundary",
      "anchor": "trapMin = Math.min(trapMin, trapDistance)",
      "replacement": "trapMin = F32(Math.min(trapMin, trapDistance))",
      "source_span": "julia.js:158:7-47",
      "independent": true,
      "source_anchor": "trapMin = Math.min(trapMin, trapDistance)",
      "anchor_occurrence_count": 1,
      "source_relative_path": "src/effects/adapters/julia.js",
      "source_sha256": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "mutated_factory_text_sha256": "abd2a68d17ebff2e2390ab0645e60f7a582dc1f42690228db9e3ae286939eda5",
      "anchor_sha256": "0705f06f3f6101e0f7990e839bd1c4aef343ee08dc7bafccd654669843890eb3",
      "replacement_sha256": "68ec4220d8cf63fd98aa5a0c94a2ed59c776f3d5081c671ff1bc89f20eb1f358",
      "results": [
        {
          "case": "manual-smooth",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-distance-tile",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-stripe",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-trap",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "manual-normal",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-circle",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "invert-output",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "animated-lissajous",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-min",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-max",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "iterations-clamp-1001",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "bulb-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "poi-fallback",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "period-convergence",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-output-mode",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-trap-shape",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "fallback-c-path",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        },
        {
          "case": "non-square-f32-transform",
          "differs": false,
          "changed_float32_lanes": 0,
          "changed_rgba8_bytes": 0,
          "float32_witness": null,
          "rgba8_witness": null
        }
      ],
      "result_sha256": "9115e939e6b95fb0dc42683155c5d69bc2038d15090387c90be7c114e01dac73",
      "witness_cases": [],
      "control_cases": [
        "manual-smooth",
        "manual-distance-tile",
        "manual-stripe",
        "poi-trap",
        "manual-normal",
        "animated-circle",
        "invert-output",
        "animated-lissajous",
        "iterations-min",
        "iterations-max",
        "iterations-clamp-1001",
        "bulb-path",
        "poi-fallback",
        "period-convergence",
        "fallback-output-mode",
        "fallback-trap-shape",
        "fallback-c-path",
        "non-square-f32-transform"
      ]
    }
  ],
  "control_group": {
    "repeatability": {
      "case": "manual-smooth",
      "identical_float32": true,
      "identical_rgba8": true
    },
    "input_immutability": {
      "case": "manual-smooth",
      "unchanged": true
    },
    "input_lifetime": {
      "case": "manual-smooth",
      "stable_after_independent_render": true
    },
    "independent_output_storage": {
      "case": "manual-distance-tile",
      "distinct_data_objects": true,
      "distinct_backing_buffers": true
    },
    "public_direct_identity": true,
    "adapter_own_key": true
  },
  "cross_lane_assignment_profile": {
    "status": "authenticated",
    "contract": "derivative destination lanes are kept source-order sequential only for this exact adapter key",
    "source_bound": "Julia GLSL source and juliaFactory adapter pins",
    "anchor": "const nextDerivativeX = F32(2 * F32(F32(reHigh * derivativeX) - F32(imHigh * derivativeY)))\n      derivativeY = F32(2 * F32(F32(reHigh * derivativeY) + F32(imHigh * derivativeX)))\n      derivativeX = nextDerivativeX",
    "replacement": "derivativeX = F32(2 * F32(F32(reHigh * derivativeX) - F32(imHigh * derivativeY)))\n      derivativeY = F32(2 * F32(F32(reHigh * derivativeY) + F32(imHigh * derivativeX)))",
    "mutated_factory_text_sha256": "9fdd53914591d4bb4209094359c1450847beef8bf0426bf737c872de286d081e"
  },
  "claim_boundaries": {
    "absolute_paths": "stable placeholders only",
    "authority": "unmodified public juliaFactory adapter from immutable snapshot; C++ output does not participate",
    "adapter": "adapter owns synth/julia:julia by authenticated canonical identity",
    "mutations": "adapter source anchor replacements are executed authority mutations, not uniform perturbations",
    "df64_low_carriers": "coordinates low-lane owner writes are structurally authenticated but do not change final Float32/RGBA8 pixels; pixel mutation count excludes those non-discriminable lanes"
  },
  "relations": {
    "clamp_1001_vs_1000": {
      "name": "iterations-clamp-1001-vs-1000",
      "kind": "runtime-loop-clamp-observation",
      "candidate_case": "iterations-clamp-1001",
      "control_case": "iterations-max",
      "identical_float32": false,
      "identical_rgba8": false,
      "mutant_name": "loop-clamp-1001",
      "mutant_candidate_changed_float32_lanes": 3,
      "mutant_candidate_changed_rgba8_bytes": 3,
      "mutant_control_changed_float32_lanes": 0,
      "mutant_control_changed_rgba8_bytes": 0,
      "source_anchor": "for (let index = 0; index < Math.min(maxIterations, 1000); index += 1) {",
      "instrumentation": "for (let index = 0; index < Math.min(maxIterations, 1000); index += 1) {\n      $bindings.__juliaLoopEntries.count += 1",
      "mutant_replacement": "maxIterations",
      "loop_anchor_occurrence_count": 1,
      "loop_anchor_sha256": "fdc2d5bff18e5d7cce09258a645aa8276d2d8370d3d10013df9bf613059f44ba",
      "instrumentation_sha256": "764cabab720a2754486049b80e36e0096825b32eeeaec98734304cf93f1a33f8",
      "mutant_factory_text_sha256": "a5c1e3fe9530d06a8d6ccfaafd3f1b29c2221a35a7a874b6d48881281d9a9a18",
      "case": "iterations-clamp-1001",
      "canonical_1000_loop_entries": 1000,
      "canonical_1001_loop_entries": 1000,
      "no_clamp_mutant_loop_entries": 1001,
      "instrumented_canonical_1000_pixel_identical": true,
      "instrumented_canonical_1001_pixel_identical": true,
      "instrumented_mutant_pixel_identical": true,
      "canonical_1000": {
        "f32_words_le": [
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000"
        ],
        "rgba8_bytes": [
          0,
          0,
          0,
          255
        ]
      },
      "canonical_1001": {
        "f32_words_le": [
          "0x3f56a8ef",
          "0x3f56a8ef",
          "0x3f56a8ef",
          "0x3f800000"
        ],
        "rgba8_bytes": [
          214,
          214,
          214,
          255
        ]
      },
      "canonical_1000_vs_1001_identical_float32": false,
      "canonical_1000_vs_1001_identical_rgba8": false,
      "mutant_candidate_first_float32_witness": {
        "index": 0,
        "expected": "0x3f56a8ef",
        "actual": "0x00000000"
      },
      "mutant_candidate_first_rgba8_witness": {
        "index": 0,
        "expected": 214,
        "actual": 0
      }
    },
    "fallbacks": [
      {
        "name": "fallback-output-mode",
        "kind": "outputMode-default",
        "candidate_case": "fallback-output-mode",
        "canonical_control": {
          "outputMode": 0
        },
        "identical_float32": true,
        "identical_rgba8": true,
        "candidate": {
          "f32_words_le": [
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000"
          ],
          "rgba8_bytes": [
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255
          ]
        },
        "control": {
          "f32_words_le": [
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000"
          ],
          "rgba8_bytes": [
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255
          ]
        }
      },
      {
        "name": "fallback-trap-shape",
        "kind": "trapShape-else",
        "candidate_case": "fallback-trap-shape",
        "canonical_control": {
          "trapShape": 2
        },
        "identical_float32": true,
        "identical_rgba8": true,
        "candidate": {
          "f32_words_le": [
            "0x3f6f5fec",
            "0x3f6f5fec",
            "0x3f6f5fec",
            "0x3f800000",
            "0x3f7d7166",
            "0x3f7d7166",
            "0x3f7d7166",
            "0x3f800000",
            "0x3f7abb76",
            "0x3f7abb76",
            "0x3f7abb76",
            "0x3f800000",
            "0x3f7eaf3d",
            "0x3f7eaf3d",
            "0x3f7eaf3d",
            "0x3f800000",
            "0x3f7ec631",
            "0x3f7ec631",
            "0x3f7ec631",
            "0x3f800000",
            "0x3f7fa01a",
            "0x3f7fa01a",
            "0x3f7fa01a",
            "0x3f800000",
            "0x3f7fa01a",
            "0x3f7fa01a",
            "0x3f7fa01a",
            "0x3f800000",
            "0x3f7ec631",
            "0x3f7ec631",
            "0x3f7ec631",
            "0x3f800000",
            "0x3f7eaf3d",
            "0x3f7eaf3d",
            "0x3f7eaf3d",
            "0x3f800000",
            "0x3f7abb76",
            "0x3f7abb76",
            "0x3f7abb76",
            "0x3f800000",
            "0x3f7d7166",
            "0x3f7d7166",
            "0x3f7d7166",
            "0x3f800000",
            "0x3f6f5fec",
            "0x3f6f5fec",
            "0x3f6f5fec",
            "0x3f800000"
          ],
          "rgba8_bytes": [
            238,
            238,
            238,
            255,
            252,
            252,
            252,
            255,
            250,
            250,
            250,
            255,
            254,
            254,
            254,
            255,
            254,
            254,
            254,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            254,
            254,
            254,
            255,
            254,
            254,
            254,
            255,
            250,
            250,
            250,
            255,
            252,
            252,
            252,
            255,
            238,
            238,
            238,
            255
          ]
        },
        "control": {
          "f32_words_le": [
            "0x3f6f5fec",
            "0x3f6f5fec",
            "0x3f6f5fec",
            "0x3f800000",
            "0x3f7d7166",
            "0x3f7d7166",
            "0x3f7d7166",
            "0x3f800000",
            "0x3f7abb76",
            "0x3f7abb76",
            "0x3f7abb76",
            "0x3f800000",
            "0x3f7eaf3d",
            "0x3f7eaf3d",
            "0x3f7eaf3d",
            "0x3f800000",
            "0x3f7ec631",
            "0x3f7ec631",
            "0x3f7ec631",
            "0x3f800000",
            "0x3f7fa01a",
            "0x3f7fa01a",
            "0x3f7fa01a",
            "0x3f800000",
            "0x3f7fa01a",
            "0x3f7fa01a",
            "0x3f7fa01a",
            "0x3f800000",
            "0x3f7ec631",
            "0x3f7ec631",
            "0x3f7ec631",
            "0x3f800000",
            "0x3f7eaf3d",
            "0x3f7eaf3d",
            "0x3f7eaf3d",
            "0x3f800000",
            "0x3f7abb76",
            "0x3f7abb76",
            "0x3f7abb76",
            "0x3f800000",
            "0x3f7d7166",
            "0x3f7d7166",
            "0x3f7d7166",
            "0x3f800000",
            "0x3f6f5fec",
            "0x3f6f5fec",
            "0x3f6f5fec",
            "0x3f800000"
          ],
          "rgba8_bytes": [
            238,
            238,
            238,
            255,
            252,
            252,
            252,
            255,
            250,
            250,
            250,
            255,
            254,
            254,
            254,
            255,
            254,
            254,
            254,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            254,
            254,
            254,
            255,
            254,
            254,
            254,
            255,
            250,
            250,
            250,
            255,
            252,
            252,
            252,
            255,
            238,
            238,
            238,
            255
          ]
        }
      },
      {
        "name": "fallback-c-path",
        "kind": "cPath-explicit-default",
        "candidate_case": "fallback-c-path",
        "canonical_control": {
          "cPath": 0
        },
        "identical_float32": true,
        "identical_rgba8": true,
        "candidate": {
          "f32_words_le": [
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000"
          ],
          "rgba8_bytes": [
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255
          ]
        },
        "control": {
          "f32_words_le": [
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000",
            "0x00000000",
            "0x00000000",
            "0x00000000",
            "0x3f800000"
          ],
          "rgba8_bytes": [
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255,
            0,
            0,
            0,
            255
          ]
        }
      }
    ]
  },
  "diagnostic_witnesses": [
    {
      "name": "period-convergence",
      "source_anchor": "else if (Math.hypot(reHigh - slowX, imHigh - slowY) < 1e-10) {",
      "replacement": "else if (Math.hypot(reHigh - slowX, imHigh - slowY) < 1e-10) {\n        $bindings.__juliaDiagnostic.periodHits += 1",
      "anchor_occurrence_count": 1,
      "anchor_sha256": "fc8f0c37a014b2f996687589bf96d3fd9a70c2d82392e90d27b91ffdd03d71dc",
      "replacement_sha256": "4b07de3f6020508a97bd3a436a1d6111651703fcbc4a75010b281e4895171f12",
      "canonical_factory_text_sha256": "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6",
      "instrumented_factory_text_sha256": "e64f2eadd238f437ed23f0812e35b8b145fbb8c96f4fa3cd38c19adde16bf40c",
      "period_hit_count": 1,
      "canonical": {
        "f32_words_le": [
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000"
        ],
        "rgba8_bytes": [
          0,
          0,
          0,
          255
        ]
      },
      "instrumented": {
        "f32_words_le": [
          "0x00000000",
          "0x00000000",
          "0x00000000",
          "0x3f800000"
        ],
        "rgba8_bytes": [
          0,
          0,
          0,
          255
        ]
      }
    }
  ],
  "result_trap_search": {
    "selection_rule": "poi-trap-first, then trap-search-000000 through trap-search-199999",
    "tested_candidates": 152236,
    "limit": 200000,
    "selected": {
      "order_index": 152235,
      "binding": {
        "name": "trap-search-152217",
        "width": 1,
        "height": 1,
        "time": 3.7923567490168746,
        "cReal": -0.3738171601141377,
        "cImag": 0.4634542822519909,
        "poi": 6,
        "outputMode": 3,
        "centerX": 0.44228784680419775,
        "centerY": -0.3502212589025081,
        "rotation": 77.56369656360795,
        "iterations": 992,
        "stripeFreq": 0,
        "trapShape": 0,
        "lightAngle": 237.31254449982956,
        "cPath": 0,
        "cSpeed": 1.9575383979728302,
        "cRadius": 0.13296835996046857,
        "invert": false,
        "zoomSpeed": 0,
        "zoomDepth": 4.020128862238519,
        "tileX": 0,
        "tileY": 0,
        "salt": 1
      },
      "canonical": {
        "f32_words_le": [
          "0x3f3d3d3d",
          "0x3f3d3d3d",
          "0x3f3d3d3d",
          "0x3f800000"
        ],
        "rgba8_bytes": [
          188,
          188,
          188,
          255
        ]
      },
      "mutated": {
        "f32_words_le": [
          "0x3f3d3d3e",
          "0x3f3d3d3e",
          "0x3f3d3d3e",
          "0x3f800000"
        ],
        "rgba8_bytes": [
          189,
          189,
          189,
          255
        ]
      },
      "changed_float32_lanes": 3,
      "changed_rgba8_bytes": 3,
      "float32_witness": {
        "index": 0,
        "expected": "0x3f3d3d3d",
        "actual": "0x3f3d3d3e"
      },
      "rgba8_witness": {
        "index": 0,
        "expected": 188,
        "actual": 189
      }
    }
  }
}
```

## Reviewed witness summary

- Package cardinality: cases=18, mutations=25, diagnostics=1; binding names=21; closure files=22.
- Clamp observation iterations-clamp-1001-vs-1000: canonical 1000 loop entries=1000; canonical 1001=1000; no-clamp mutant=1001; instrumented canonical 1000/1001/mutant pixel identity=true/true/true. Canonical 1000-vs-1001 Float32/RGBA8 equality is false/false; this is recorded authority output, not normalized.
- Clamp source anchor/replacement: for (let index = 0; index < Math.min(maxIterations, 1000); index += 1) { -> maxIterations; anchor/instrumentation/mutant hashes=fdc2d5bff18e5d7cce09258a645aa8276d2d8370d3d10013df9bf613059f44ba/764cabab720a2754486049b80e36e0096825b32eeeaec98734304cf93f1a33f8/a5c1e3fe9530d06a8d6ccfaafd3f1b29c2221a35a7a874b6d48881281d9a9a18; mutant changed lanes/bytes=3/3; first witnesses={"index":0,"expected":"0x3f56a8ef","actual":"0x00000000"} / {"index":0,"expected":214,"actual":0}.
- Result-trap-number source span=julia.js:158:7-47; anchor=trapMin = Math.min(trapMin, trapDistance); replacement=trapMin = F32(Math.min(trapMin, trapDistance)); source/anchor/replacement/mutant hashes=0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5/0705f06f3f6101e0f7990e839bd1c4aef343ee08dc7bafccd654669843890eb3/68ec4220d8cf63fd98aa5a0c94a2ed59c776f3d5081c671ff1bc89f20eb1f358/abd2a68d17ebff2e2390ab0645e60f7a582dc1f42690228db9e3ae286939eda5; occurrence count=1.
- Result-trap-number fixed selection: poi-trap-first, then trap-search-000000 through trap-search-199999; tested=152236; selected=trap-search-152217; changed lanes/bytes=3/3; witnesses={"index":0,"expected":"0x3f3d3d3d","actual":"0x3f3d3d3e"} / {"index":0,"expected":188,"actual":189}.
- Period diagnostic period-convergence: anchor=else if (Math.hypot(reHigh - slowX, imHigh - slowY) < 1e-10) {; replacement=else if (Math.hypot(reHigh - slowX, imHigh - slowY) < 1e-10) {
        $bindings.__juliaDiagnostic.periodHits += 1; occurrence count=1; hit count=1; anchor/replacement/instrumented-factory hashes=fc8f0c37a014b2f996687589bf96d3fd9a70c2d82392e90d27b91ffdd03d71dc/4b07de3f6020508a97bd3a436a1d6111651703fcbc4a75010b281e4895171f12/e64f2eadd238f437ed23f0812e35b8b145fbb8c96f4fa3cd38c19adde16bf40c; canonical and instrumented outputs are exact-identical.

## Baseline seven-test RED before package expansion

The Task34 brief records the required pre-expansion baseline as the 8-case/23-mutation/no-diagnostic package. The exact seven-test unittest conversion was required to prove RED against that baseline; this fix report preserves that historical boundary and does not relabel the current 18/25/1 package as a baseline. Baseline result: RED because the baseline document did not satisfy the expanded 18-case, 25-mutation, one-diagnostic contract.

## Verification transcripts and results

```sh\n$ export NOISEMAKER_CPU_ROOT=<pinned-external-authority> NOISEMAKER_FOR_CPU=<same-pinned-external-authority>\n```
```sh\n $ node docs/port-engineering/julia-parity/julia_oracle_generator.mjs --check --cpu-root "$NOISEMAKER_CPU_ROOT"\n```
```sh\n# julia oracle generator: ok\n```
```sh\n$ node docs/port-engineering/julia-parity/julia_oracle_generator.mjs --self-test --cpu-root "$NOISEMAKER_CPU_ROOT"\n```
```sh\n# 8/8 checks pass\n```
```sh\n$ PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/generate_julia_native_oracle_include.py --check\n```
```sh\n# julia materializer: ok\n```
```sh\n$ PYTHONDONTWRITEBYTECODE=1 python3 -B tools/glslcpp/generate_julia_native_oracle_include.py --self-test\n```
```sh\n# 65/65 pass\n```
```sh\n$ PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_julia_oracle\n```
```sh\n# 7 tests, OK\n```
```sh\n$ c++ -std=c++20 -Iinclude -Isrc -Itests -fsyntax-only tests/test_generated_kernels.cpp\n```
```sh\n# expected RED: exactly one diagnostic at tests/test_generated_kernels.cpp:30264: missing noisemaker::generated::bind_synth_julia_julia\n```

## Changed-file audit

- Owned authored/tool files: docs/port-engineering/julia-parity/julia_oracle_generator.mjs; tools/glslcpp/generate_julia_native_oracle_include.py; tests/test_julia_oracle.py.
- Owned generated artifacts and sidecars: docs/port-engineering/julia-parity/julia-oracles.json(.sha256); docs/port-engineering/julia-parity/julia-oracle-report.md(.sha256); tests/oracles/julia_expected.inc(.sha256).
- No frontend, emitter, generated typed slice/catalog/runtime, corpus metadata, authority snapshot, unrelated tests/docs, build outputs, or Git files were changed.
- JSON SHA-256: 4c752915ca441b197774b6f1d746068c88087fed028df6b5f42f2572d416a318.

## Remaining concerns

- The native Julia production binder/admission is intentionally absent. The syntax-only native check therefore stops at exactly one missing bind_synth_julia_julia diagnostic; it does not establish native runtime parity.
- The package records canonical 1000/1001 pixel inequality truthfully because raw maxIterations remains observable outside the loop; the accepted clamp evidence is the exact loop-entry and instrumented identity contract plus the no-clamp word/byte witness.
- The result-trap mutation now carries and materializes the exact authenticated span julia.js:158:7-47; no source-only pixel claim is made because the bounded selected search supplies the discriminating witness.

## Fix3 complete Task34 changed-file audit

This table supersedes the earlier abbreviated audit. It is the complete Task34-owned delta against frozen baseline /private/tmp/noisemaker-julia-baseline.te8c7S. Separate Task35/39 frontend/profile files are intentionally excluded. Rows dispositioned "not re-read" are cross-lane files this package does not authenticate; their Task34 post-change hashes are recorded so this checked report stays a pure function of the pinned authority and the julia package itself.

| Task34-owned relative path | Frozen baseline SHA-256 | Current SHA-256 or generation marker | Disposition |
| --- | --- | --- | --- |
| docs/port-engineering/julia-parity/julia_oracle_generator.mjs | 99783dcab73ddd3b333495d70390e6a3e6333b0ea068ec3ab13f03a1278f4647 | 4445d39ddc05e720d2583d0b1cf785434464c1e764eb3059f20da65165158017 | changed |
| docs/port-engineering/julia-parity/julia_oracle_generator.mjs.sha256 | cacaaef1b8403925cfda2aa3b911387e896d29724aa2c1ca5b5c0422f3208cff | b103da7c6cec01e6e34d6cfa0c01f18c4656a5019ebcb7d35490d9ec8259c37c | changed |
| docs/port-engineering/julia-parity/julia-oracles.json | 1e79bbc37b90164259f7005762239d082184e1cb43fe0efd3dcfec14659ebd64 | 4c752915ca441b197774b6f1d746068c88087fed028df6b5f42f2572d416a318 | changed |
| docs/port-engineering/julia-parity/julia-oracles.json.sha256 | 6ad87dda7864df0053aa0d1d0e64c16787f91b0970163bba49d9faf29a1c17a4 | 7310fb9cbab2269cddb0a3ba1defe284aa7b32186cd677155efa1fa4c756cb13 | changed |
| docs/port-engineering/julia-parity/julia-oracle-report.md | c3813c7024c861fcba27809c66997f97947bcd621842c4ef396a4f827d25bccf | generated-by-this-report | changed |
| docs/port-engineering/julia-parity/julia-oracle-report.md.sha256 | c3c3da4de0568075bbc18dadb9cbc12e007b7d8d18c9ef9a888ee9c848f51479 | generated-by-this-report | changed |
| tools/glslcpp/generate_julia_native_oracle_include.py | 5745ce5bc874908a55210ea748e5266ef8e7863dafed6cae34710fae94030a74 | d74c67eeeda0c4cddd9f2b06d1c3ebc15afc7137b33511e583e5c522a34c5998 | changed |
| tools/glslcpp/generate_julia_native_oracle_include.py.sha256 | ABSENT | b89d544cac8bdb33a465359afabe670a57c5db377fdb063986aecf811baa190c | new |
| tests/oracles/julia_expected.inc | 111b1ed7c0e5132335c81c6aab353744c8d1d882960f616f0e587127ff3fc057 | 8fa6d370657ae859294fa470e01646f4077a86054831749f1b8d3f1f9726f80e | changed |
| tests/oracles/julia_expected.inc.sha256 | 2c0a2e7f0c71d6f75b597bae93c7f77b7526a677db099144111cbc3efdc87288 | 2bd1d4356779c4dd779f0e545472f5817df969bd51a157143c0cfaaea318fce4 | changed |
| tests/test_generated_kernels.cpp | d2210b840fa6ffe3b07b73330f7a336d01683c163e5887f276c254de40beb685 | e375c33914a968634ab7276c1f1146031c57ea182ae63c269bad72e81559649b | changed (recorded at Task34; cross-lane file, not re-read) |
| tests/test_julia_oracle.py | c2e58eb8673ba45191e7ddfcf0841d1decb4bf204af71e6f97066a6f19d8bfdb | 5bc6d65fdeccbb53bd0823f69a44432e9e5fcbf8ce51fb76a7c097854b785b54 | changed |

## Fix3 observed seven-test RED reconstruction

This is a current reproducible reconstruction, not a historical transcript copied from an intermediate checkout. The frozen baseline package contains exactly 8 render cases, 23 mutation rows, and no diagnostic witness. The current converted seven-test unittest module was retained unchanged in the scratch overlay.

Reconstruction: copied /private/tmp/noisemaker-cpp-continuation.e033lt/work/noisemaker-for-cpp to external scratch path /private/tmp/julia-task34-red.FEFeXP; overlaid from /private/tmp/noisemaker-julia-baseline.te8c7S docs/port-engineering/julia-parity/julia_oracle_generator.mjs and its sidecar, julia-oracles.json and its sidecar, julia-oracle-report.md and its sidecar, tools/glslcpp/generate_julia_native_oracle_include.py, tests/oracles/julia_expected.inc and its sidecar, and tests/test_generated_kernels.cpp; the baseline materializer sidecar was absent; retained current converted tests/test_julia_oracle.py (SHA-256 e85e577f3decc6af20a9a6e9f199c522ee3cc344e46796abbb6b8dd25efefe06).

Exact command:
```sh
NOISEMAKER_CPU_ROOT=/private/tmp/noisemaker-cpp-continuation.e033lt/oracle/noisemaker-for-cpu NOISEMAKER_FOR_CPU=/private/tmp/noisemaker-cpp-continuation.e033lt/oracle/noisemaker-for-cpu PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_julia_oracle
```

Observed status lines (all seven discovered tests):
```text
test_authority_generator_and_materializer (tests.test_julia_oracle.JuliaOracleTests.test_authority_generator_and_materializer) ... FAIL
test_authority_rejects_literal_dynamic_nonliteral_and_path_roots (tests.test_julia_oracle.JuliaOracleTests.test_authority_rejects_literal_dynamic_nonliteral_and_path_roots) ... FAIL
test_include_compiles_as_cxx20 (tests.test_julia_oracle.JuliaOracleTests.test_include_compiles_as_cxx20) ... FAIL
test_include_exposes_complete_typed_metadata_views (tests.test_julia_oracle.JuliaOracleTests.test_include_exposes_complete_typed_metadata_views) ... FAIL
test_materializer_rejects_coordinated_forgery_matrix (tests.test_julia_oracle.JuliaOracleTests.test_materializer_rejects_coordinated_forgery_matrix) ... ok
test_materializer_rejects_duplicate_json_keys_with_matching_sidecar (tests.test_julia_oracle.JuliaOracleTests.test_materializer_rejects_duplicate_json_keys_with_matching_sidecar) ... ok
test_package_contract_and_sidecars (tests.test_julia_oracle.JuliaOracleTests.test_package_contract_and_sidecars) ... FAIL
```

Observed summary: 5 failures, 0 errors, 2 passes; FAILED (failures=5).

Load-bearing observed failure output:
```text
authority_generator_and_materializer: Error: --cpu-root must be an immutable snapshot, never the live checkout
authority_rejects_literal_dynamic_nonliteral_and_path_roots: AssertionError: 'nonliteral dynamic import' not found; observed Error: live checkout must not be a symlink
include_compiles_as_cxx20: static assertion failed for kCases.size() == 18U with expression 8 == 18; static assertion failed for kMutations.size() == 25U with expression 23 == 25; two errors: use of undeclared identifier kDiagnosticWitnesses
include_exposes_complete_typed_metadata_views: AssertionError: 'struct DiagnosticWitnessView' not found
package_contract_and_sidecars: AssertionError: sidecar drift: <scratch-clone>/tools/glslcpp/generate_julia_native_oracle_include.py
```

Captured streams: stdout 0 bytes (SHA-256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855); stderr 79281 bytes (SHA-256 73cacd384fccf1bee7dec37daf95562424eb39e62107e9cdadc3413033e2b3aa).

Disk hygiene: Exact scratch clone /private/tmp/julia-task34-red.FEFeXP and scratch path record /tmp/julia-task34-red-path were removed after capture and verified absent (recoverable OS-trash removal because direct rm was rejected). The removed clone occupied 87,142,400 bytes; no current checkout cache was cleaned.

## Fix3 evidence boundary

The RED reconstruction is evidence that the current seven-test module rejects the frozen package for the recorded reasons. It is not a claim that the old pytest module itself was a seven-test unittest run. The live package remains the 18/25/1 package and its live seven-test gate is green.

