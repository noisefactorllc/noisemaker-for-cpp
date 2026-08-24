#!/usr/bin/env python3
"""Fail-closed native materializer for the synth/remap exact-pixel oracle."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import pathlib
import re
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/remap-parity"
ORACLE = PACKAGE / "remap-oracles.json"
REPORT = PACKAGE / "remap-oracle-report.md"
GENERATOR = PACKAGE / "remap_oracle_generator.mjs"
TARGET = ROOT / "tests/oracles/remap_expected.inc"
SCHEMA = "noisemaker-for-cpp.remap.pixel-parity.v2"
KEY = "synth/remap:remap"
SOURCE = "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/remap/remap.glsl"
FACTORY_SOURCE = "src/effects/generated/canonical-kernels.js"
SHA = re.compile(r"^[0-9a-f]{64}$")
WORD = re.compile(r"^0x[0-9a-f]{8}$")

EXPECTED_CLOSURE = {
    "src/csl/glsl-kernel.js": "a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa",
    "src/csl/glsl-runtime.js": "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072",
    "src/csl/runtime.js": "a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee",
    "src/effects/adapters/bit-effects.js": "5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7",
    "src/effects/adapters/crt.js": "c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc",
    "src/effects/adapters/f32-color.js": "b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046",
    "src/effects/adapters/fractal.js": "0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29",
    "src/effects/adapters/index.js": "40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267",
    "src/effects/adapters/julia.js": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
    "src/effects/adapters/median.js": "e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583",
    "src/effects/adapters/palette.js": "8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452",
    "src/effects/adapters/snow.js": "202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366",
    "src/effects/catalog.js": "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4",
    "src/effects/definition.js": "fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02",
    "src/effects/generated/canonical-adapter-data.js": "ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab",
    "src/effects/generated/canonical-kernels.js": "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe",
    "src/effects/generated/kernels.js": "b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01",
    "src/effects/generated/upstream-snapshot.js": "e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090",
    "src/effects/registry.js": "8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618",
    "src/runtime/pass-runner.js": "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa",
    "src/runtime/sampler.js": "1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328",
    "src/runtime/surface.js": "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59",
}

EXPECTED_CASES = [
    ("background", 5, 4, 1, "c1dcb82352c378c0570195ccb046effadb37993f1a3524ab0db7aa1e05156da5", "310e2d2fd973f33bb30174bad54c52f2584b057ebdcc75304b7c61e9464c7c52", "f1533840a4df3a39028bd9faa823e6584d986daa13c9976c63909139b8c6e1b3", "e3a01d4b1c46c083ac4babf4925886079472394d533d65a3dfc313c9d003c592", "8e9daf1a9853fe992270c9eb2389e513df3461e3a79c3f71984a989fee03bad8"),
    ("triangle", 7, 5, 2, "d61eed63da79802634ae1cb12b0858dd515aea2bd8d84a5c9409d6c522fc7a86", "72250f8e7d4c36f8bfcca0ed8187afbd20893e81137adc86a21aad56d04a94cf", "3a45a7e7a6ec30e5713a9d4c53fc0557728b563728545c29bb59f9b802015a34", "328a6919fa2ae1327b9b5286250594cda729746e601d43f89a25de9f341aa241", "2877646c8a492e2b9dc8945d06fa62a2386685e4b56aa818b3fe07c071c338df"),
    ("square-soft", 6, 6, 3, "28022ee011aa7ab3ae15320e57110b172ae5adcb7dd04d4dacacc24536cefc79", "3666a7975700a3cf27699cf46756ec1c333703ae2aa1be1e64c0b495cfe2f642", "3386901f7a20014097a4c19311e9bc795a7cfc42eb119241b5e8e1c3a00e6db0", "d6e90ad43d10d9a6860ba1e67fb40ee9411e702d4fef5fd54cb64bd587969afc", "6d8d439c0b11ea0893b4dd196c78e2e34075247d3d37ceb1d9d2d52e3ee26940"),
    ("overlap", 8, 5, 4, "06c155a2a2692d1db83b0c94f12cbddea0782e3f659b2e3923969914ab9bf230", "9475694ec4971933cb80001f4fc6edf8100cd7c8e95e79a483e0e58e68933b18", "46797cd8aa397bc559d59ea299d633ac68dc57bb399780e44f3e5f2845628d3f", "5232f108c30ed2071cd83caac9685e720d34a29c0e2766299109c32d7213b65a", "5a5a59c6c155c56165032c554108f8d5e56640c85397c8fe0bf126c85dae48a5"),
    ("inactive", 5, 7, 5, "564bceb0aeae4010fdaaec10d6a0eb2773b9041f334f11862d9dfd970cad065d", "4b62476bcb8534a15e8582608c7e0063aaab3c5bc823af90f04943740f54ff6a", "41b99ad7265722dbb6bf2cbf1fd62854da8db33fdbbd43bc84a9c999ceded11d", "e893ba33ecfd6f069c0be62bef24f27cef047b0565c4b1e3684545b269b31bfc", "cfeccd8a83d7209dc8a025a14bac3fbc0511e0f8cee5f6a32b53b18acbea0d60"),
    ("tiled", 6, 4, 6, "eb27877cb754ad1ff61dfe4937152ae26f49b3af145751ce539b086c469ce23f", "f72a8d7e8063d73bc276e9d114567e45bbbddc8ee77aca69492a51de103c95b5", "fb28c349e557adb93af1b1ff274e25693aab8d8c808242b8e4703e65ac984e14", "8b77b96e92824857fb2fe0c784d71fd5cb9a57f10b10b8c81f19ecfc81af6a92", "b65de9c139e6fcec192dfab7f91ebf82cd706edc5c4b7bf6422fb83cf1fa64f6"),
    ("alpha-zero", 4, 4, 7, "f74c01178387e30010225057405f2de7317b4d7f7a338b28adab2ee2c46da89c", "0ef2c25ca88fef4cce645c68dd6005042f5e404df9baf33bc88362c98ed36bb0", "7836792b9c982185d3460dbb89eeaf389b7b70933f1afbd75c5957f92d85f773", "16c366459a082d8269274f016791b2cf35017a7b3409ee826fee07f046e26eb3", "8eb31ef06450a7cfe7a8c8e00d33a46abdc318bf83224e384bf1b820a5506403"),
    ("eight-zone-cap", 9, 3, 8, "5ba99e4986349708a0eb0ffa6dcd0b129489fd3c6a85138bfbcad5baeb842211", "c72eec5399e5a0545a1cdbb57be01c7e9126981af75e5882e6996b5a6e74c65e", "2eb5fc0e9d65cc02ed68e2c74d35fc4f394b3b5f98f2f93aa99bf116a8a64040", "d477153fdbb2912a4d967bef244d6ce61e649c7de6987264fa7266c6ef926896", "7c3fd1177273004e1776c731b299dde35aee1b1a216a86d3e7b0c83de307082a"),
    ("dispatch-all-zones", 16, 8, 9, "31b54095afea2e98510bb1029f102057b833d85a98e829c029cd3dba59a942bf", "e91df1ff0dde30f97ea9e83fdb2e9fd738cdd4b0eb3057d7d4bdd5966d68875b", "641b3a4ecb7bc3f268920a586fd2d86725f3327a6fbcdf0c4b8dbdbd94532909", "dd424c66dcb2f98c9cea3eed6a9a455c9985f5e8315c824b1a773106f7a09d35", "c0e8f57554b30bdbe9305f4d1db12cb018ccd5a1f75aab5feba6bd426844b8a7"),
    ("degenerate-active", 5, 4, 10, "b7562af49edf43a2f60b2ffd00f831e064017e58d29d4c66e24ae98b36191f1a", "16daa74cedb8de40b59e7c48590d52465275e9463a6c01192685863d8400ade6", "7ca5455bbd2f2955d64011ff9a2d73982b8caf8c0dfebaa4346292562bd00de0", "a8905a28af32ea3b29698650937ad719db57402e461b3b905994b2433182fcc6", "a4591cdb4f9605162c5234e21da998bf8d97d8c367bed24bdc7379ce722b4927"),
]
EXPECTED_CONTROLS = [
    {"zone_count": 0, "bg_color": [0.1, 0.2, 0.3], "bg_alpha": 0.75, "smooth_edge": 0.04, "tile_offset": [0, 0], "full_resolution": [5, 4], "zones": []},
    {"zone_count": 1, "bg_color": [0, 0, 0], "bg_alpha": 1, "smooth_edge": 0, "tile_offset": [0, 0], "full_resolution": [7, 5], "zones": [{"count": 3, "alpha": 1, "active": 1, "verts": [[0, 0], [1, 0], [0.5, 1]]}]},
    {"zone_count": 1, "bg_color": [0.05, 0.1, 0.15], "bg_alpha": 0.5, "smooth_edge": 0.8, "tile_offset": [0, 0], "full_resolution": [6, 6], "zones": [{"count": 4, "alpha": 0.6, "active": 1, "verts": [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]]}]},
    {"zone_count": 2, "bg_color": [0.2, 0.1, 0.05], "bg_alpha": 0.8, "smooth_edge": 0, "tile_offset": [0, 0], "full_resolution": [8, 5], "zones": [{"count": 4, "alpha": 0.5, "active": 1, "verts": [[0, 0], [0.8, 0], [0.8, 1], [0, 1]]}, {"count": 4, "alpha": 0.9, "active": 1, "verts": [[0.2, 0], [1, 0], [1, 1], [0.2, 1]]}]},
    {"zone_count": 2, "bg_color": [0.4, 0.3, 0.2], "bg_alpha": 0.9, "smooth_edge": 0.2, "tile_offset": [0, 0], "full_resolution": [5, 7], "zones": [{"count": 4, "alpha": 1, "active": 0, "verts": [[0, 0], [1, 0], [1, 1], [0, 1]]}]},
    {"zone_count": 1, "bg_color": [0, 0, 0], "bg_alpha": 1, "smooth_edge": 0.1, "tile_offset": [3, 2], "full_resolution": [12, 8], "zones": [{"count": 4, "alpha": 0.75, "active": 1, "verts": [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]]}]},
    {"zone_count": 1, "bg_color": [0.3, 0.4, 0.5], "bg_alpha": 0.7, "smooth_edge": 0, "tile_offset": [0, 0], "full_resolution": [4, 4], "zones": [{"count": 4, "alpha": 0, "active": 1, "verts": [[0, 0], [1, 0], [1, 1], [0, 1]]}]},
    {"zone_count": 9, "bg_color": [0, 0, 0], "bg_alpha": 1, "smooth_edge": 0, "tile_offset": [0, 0], "full_resolution": [9, 3], "zones": [{"count": 3, "alpha": 0.1, "active": 1, "verts": [[0, 0], [1, 0], [0.5, 1]]}, {"count": 3, "alpha": 0.2, "active": 1, "verts": [[0, 0], [1, 0], [0.5, 1]]}, {"count": 3, "alpha": 0.30000000000000004, "active": 1, "verts": [[0, 0], [1, 0], [0.5, 1]]}, {"count": 3, "alpha": 0.4, "active": 1, "verts": [[0, 0], [1, 0], [0.5, 1]]}, {"count": 3, "alpha": 0.5, "active": 1, "verts": [[0, 0], [1, 0], [0.5, 1]]}, {"count": 3, "alpha": 0.6, "active": 1, "verts": [[0, 0], [1, 0], [0.5, 1]]}, {"count": 3, "alpha": 0.7000000000000001, "active": 1, "verts": [[0, 0], [1, 0], [0.5, 1]]}, {"count": 3, "alpha": 0.8, "active": 1, "verts": [[0, 0], [1, 0], [0.5, 1]]}]},
    {"zone_count": 8, "bg_color": [0, 0, 0], "bg_alpha": 1, "smooth_edge": 0, "tile_offset": [0, 0], "full_resolution": [16, 8], "zones": [{"count": 4, "alpha": 1, "active": 1, "verts": [[0, 0], [0.125, 0], [0.125, 1], [0, 1]]}, {"count": 4, "alpha": 1, "active": 1, "verts": [[0.125, 0], [0.25, 0], [0.25, 1], [0.125, 1]]}, {"count": 4, "alpha": 1, "active": 1, "verts": [[0.25, 0], [0.375, 0], [0.375, 1], [0.25, 1]]}, {"count": 4, "alpha": 1, "active": 1, "verts": [[0.375, 0], [0.5, 0], [0.5, 1], [0.375, 1]]}, {"count": 4, "alpha": 1, "active": 1, "verts": [[0.5, 0], [0.625, 0], [0.625, 1], [0.5, 1]]}, {"count": 4, "alpha": 1, "active": 1, "verts": [[0.625, 0], [0.75, 0], [0.75, 1], [0.625, 1]]}, {"count": 4, "alpha": 1, "active": 1, "verts": [[0.75, 0], [0.875, 0], [0.875, 1], [0.75, 1]]}, {"count": 4, "alpha": 1, "active": 1, "verts": [[0.875, 0], [1, 0], [1, 1], [0.875, 1]]}]},
    {"zone_count": 1, "bg_color": [0.25, 0.35, 0.45], "bg_alpha": 0.6, "smooth_edge": 0, "tile_offset": [0, 0], "full_resolution": [5, 4], "zones": [{"count": 2, "alpha": 1, "active": 1, "verts": [[0.1, 0.1], [0.9, 0.9]]}]},
]

EXPECTED_FACTORY = {"name": "canonicalFactory272", "text_sha256": "0696adfebdd8c106778777142a98833cee35b09e4c63e28cce296bf2e5b5b8ab", "public_factory_is_canonical_identity": True, "adapter_own_key": False, "canonical_own_key": True}
EXPECTED_BINDINGS = ["data", "tileOffset", "fullResolution", *[f"zone{i}_tex" for i in range(8)]]
EXPECTED_RUNTIME_ABI = {"data": "std140 vec4[267]", "tileOffset": "Vec2", "fullResolution": "Vec2", **{f"zone{i}_tex": "sampler2D" for i in range(8)}}
EXPECTED_SOURCE_ABI = {"data": "vec4[267]", "tileOffset": "vec2", "fullResolution": "vec2", **{f"zone{i}_tex": "sampler2D" for i in range(8)}}
EXPECTED_COMPARER = {"good": True, "dimensions": True, "short": True, "long": True, "rgba8_count": True, "rgba8_mismatch": True, "signed_zero": True, "nan_payload": True, "first_mismatch": True}
EXPECTED_CONTROL_GROUP = {"repeatability": {"case": "triangle", "identical_float32": True, "identical_rgba8": True, "distinct_output_objects": True, "distinct_backing_buffers": True}, "input_immutability": {"case": "triangle", "unchanged": True}, "input_lifetime": {"case": "triangle", "stable_after_independent_render": True}, "independent_output_storage": {"case": "triangle", "distinct_data_objects": True, "distinct_backing_buffers": True}, "public_direct_identity": True, "canonical_own_key": True, "adapter_own_key": False}
EXPECTED_RESULTS_HASHES = ["2bdb448cf1ab4a668a965cf17ac9eed90c4c6543017afa76d986430984f41aa4", "2bdb448cf1ab4a668a965cf17ac9eed90c4c6543017afa76d986430984f41aa4", "5928ff019f6058cf044cad6adc4255330624f8e327e2bcaa22c4c17a0248b478", "2bdb448cf1ab4a668a965cf17ac9eed90c4c6543017afa76d986430984f41aa4", "2bdb448cf1ab4a668a965cf17ac9eed90c4c6543017afa76d986430984f41aa4", "8b30c4490935022bd99020cac0b146e83bd0c7d522428478f502bb46ede2f4fa", "3334a02a70f26384ac68224761399fc2b1f1988dd45d833ae18fa3f190c4778d"]
EXPECTED_MUTATION_META = [
    ("zone-meta-count", "zone-metadata", "replace packed zone count read with zero", "return getZoneMeta(z)[0]|0;", "return 0;", "e2d43ec3b4bb2eeffd22c030dd215e49002c6c36fb2abb9bf2867dd880ef7507", "30b22af6f0053cf3692ba1c65bd00851659c66f67ddff82e866e630753199058", "6be2e46a3d0765fd4d08def164c35b75afcc481db6fd11cc5118c4e2c20b634d", ["triangle", "square-soft", "overlap", "tiled", "eight-zone-cap", "dispatch-all-zones"], ["background", "inactive", "alpha-zero", "degenerate-active"]),
    ("zone-meta-active", "zone-metadata", "replace active-source read with zero", "return getZoneMeta(z)[1] + 0.5|0;", "return 0;", "fa8037bf9873b0246f6bf50a83528553e2a784eea4d60fefed3446dbe0b4dc43", "20b1f771a64bd51c1e348d612d93721cb19b6b7bb0fd09ddd3953c70f0b3bfd4", "6be2e46a3d0765fd4d08def164c35b75afcc481db6fd11cc5118c4e2c20b634d", ["triangle", "square-soft", "overlap", "tiled", "eight-zone-cap", "dispatch-all-zones"], ["background", "inactive", "alpha-zero", "degenerate-active"]),
    ("zone-alpha-read", "zone-metadata", "replace packed alpha read with one", "return getZoneMeta(z)[3];", "return 1;", "59225937cce5006cb0b67bfd602981c4a3653c87d47c0b45a773e0b5c3c39fc8", "243c95c198fae3f96350cace292b221317ce7ccef637708e9f477bfc7ef73940", "f58b7c3af621b52a2bb7dc67d4491f9ab6c6d16e3cfa1e46e670ff4f9a301fdc", ["square-soft", "overlap", "tiled", "alpha-zero", "eight-zone-cap"], ["background", "triangle", "inactive", "dispatch-all-zones", "degenerate-active"]),
    ("vertex-pair-index", "vertex-pack", "replace runtime pair indexing with first pair", "var _packed = getZonePack(zoneIdx, vertIdx >> 1);", "var _packed = getZonePack(zoneIdx, 0);", "461aa890bc7444d52fdd60f60492e7a27e1720734adf752f8042944230c97244", "3e5d478762a4cc558f13da03f357ce8ce6fbb26020db59dbbf08fa6869d59706", "6d6c9258bef78476db62004c61b77d3375beda94c45f6415575787f4a96aa95a", ["triangle", "square-soft", "overlap", "tiled", "eight-zone-cap", "dispatch-all-zones"], ["background", "inactive", "alpha-zero", "degenerate-active"]),
    ("point-crossing", "polygon-branch", "disable polygon crossing toggle", "inside = !inside;", "inside = false;", "bdaad3f653fa5f5fe3abc3a400ce205479fcf92b913dd014e08edc803978a62f", "42e66aa1252ed2fcc2df230565137ea846de177f349df07b1b9eaf64a233d845", "d0b3b2f210ddedd2c7cf999ed91214658049ea725eb207d889e3f5245e67ec55", ["triangle", "square-soft", "overlap", "tiled", "eight-zone-cap", "dispatch-all-zones"], ["background", "inactive", "alpha-zero", "degenerate-active"]),
    ("edge-distance", "edge-smoothing", "replace edge distance with zero", "return d;\n  };\n  function main", "return 0;\n  };\n  function main", "6b065c419875e187f7a4b4f4438d5b2951309d90d77b22bc382bba85d776aced", "1662b8df464a5e05eeedbb8c767065c695561efaecdce101608f7a1005cbafb6", "8c6421132f3e77d1c1f1eaec3880a31074dbf70eb9289d07890482d124346bb4", ["square-soft", "tiled"], ["background", "triangle", "overlap", "inactive", "alpha-zero", "eight-zone-cap", "dispatch-all-zones", "degenerate-active"]),
    ("sample-zone-dispatch", "sampler-dispatch", "route zone one sample to zone zero", "return texture(zone1_tex, uv);", "return texture(zone0_tex, uv);", "e608182250b15cfa7f46bd6f044a002df3408c90a6a160b19d1a2f29b8d9008d", "1c8a5f7bb9b9822a5ed3f4740da426ccd80cd5dccb0eefbff9654aa0c8fda2af", "7540e5abe6fb281fe4b6c7250f3237c8b8f136fcbf704caefd0bd4a161282c2e", ["overlap", "eight-zone-cap", "dispatch-all-zones"], ["background", "triangle", "square-soft", "inactive", "tiled", "alpha-zero", "degenerate-active"]),
]
EXPECTED_SOURCE_HASH = "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe"
EXPECTED_FACTORY_TEXT_HASH = EXPECTED_FACTORY["text_sha256"]

class OracleError(RuntimeError):
    pass

def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def strict_json(payload: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise OracleError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    def parse_float(text):
        value = float(text)
        if not math.isfinite(value):
            raise OracleError("non-finite JSON number")
        return value
    def parse_constant(text):
        raise OracleError(f"non-finite JSON constant: {text}")
    try:
        return json.loads(payload, object_pairs_hook=pairs, parse_float=parse_float, parse_constant=parse_constant)
    except OracleError:
        raise
    except (json.JSONDecodeError, ValueError, TypeError) as error:
        raise OracleError(f"invalid JSON: {error}") from error

def exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise OracleError(f"{label}: exact field set drift")
    return value

def string(value, label):
    if type(value) is not str:
        raise OracleError(f"{label}: expected string")
    return value

def boolean(value, label):
    if type(value) is not bool:
        raise OracleError(f"{label}: expected bool")
    return value

def integer(value, label, low=None, high=None):
    if type(value) is not int:
        raise OracleError(f"{label}: expected integer")
    if low is not None and value < low or high is not None and value > high:
        raise OracleError(f"{label}: integer out of range")
    return value

def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise OracleError(f"{label}: expected finite number")
    return value

def sha(value, label):
    value = string(value, label)
    if not SHA.fullmatch(value):
        raise OracleError(f"{label}: malformed SHA-256")
    return value

def reject_absolute(value, label="document"):
    if isinstance(value, str) and (re.match(r"^(?:[A-Za-z]:[\\/]|\\\\|/)", value) or re.search(r"(?:^|[\\/])(?:Users|private|tmp|home)[\\/]", value)):
        raise OracleError(f"{label}: absolute-looking path")
    if isinstance(value, list):
        for index, child in enumerate(value):
            reject_absolute(child, f"{label}[{index}]")
    elif isinstance(value, dict):
        for key, child in value.items():
            reject_absolute(child, f"{label}.{key}")

def sidecar(path, content):
    return f"{digest(content)}  {path.name}\n"

def checked(path):
    side = path.with_name(path.name + ".sha256")
    if not path.is_file() or not side.is_file():
        raise OracleError(f"missing checked asset or sidecar: {path}")
    content = path.read_bytes()
    if side.read_text() != sidecar(path, content):
        raise OracleError(f"checksum sidecar drift: {path}")
    return content

def words(value, count, label):
    if type(value) is not list or len(value) != count or any(type(item) is not str or not WORD.fullmatch(item) for item in value):
        raise OracleError(f"{label}: malformed exact word payload")

def byte_values(value, count, label):
    if type(value) is not list or len(value) != count or any(type(item) is not int or not 0 <= item <= 255 for item in value):
        raise OracleError(f"{label}: malformed exact byte payload")

def packed_words(value):
    return b"".join(int(item, 16).to_bytes(4, "little") for item in value)

def validate_controls(value, expected, label):
    exact(value, {"zone_count", "bg_color", "bg_alpha", "smooth_edge", "tile_offset", "full_resolution", "zones"}, label)
    integer(value["zone_count"], f"{label}.zone_count", 0, 9)
    if type(value["bg_color"]) is not list or len(value["bg_color"]) != 3: raise OracleError(f"{label}.bg_color: shape drift")
    for i, item in enumerate(value["bg_color"]): number(item, f"{label}.bg_color[{i}]")
    number(value["bg_alpha"], f"{label}.bg_alpha"); number(value["smooth_edge"], f"{label}.smooth_edge")
    for name in ("tile_offset", "full_resolution"):
        if type(value[name]) is not list or len(value[name]) != 2: raise OracleError(f"{label}.{name}: shape drift")
        for i, item in enumerate(value[name]): integer(item, f"{label}.{name}[{i}]")
    if type(value["zones"]) is not list or len(value["zones"]) > 8: raise OracleError(f"{label}.zones: shape drift")
    for i, zone in enumerate(value["zones"]):
        exact(zone, {"count", "alpha", "active", "verts"}, f"{label}.zones[{i}]")
        integer(zone["count"], f"{label}.zones[{i}].count", 0, 32); number(zone["alpha"], f"{label}.zones[{i}].alpha"); integer(zone["active"], f"{label}.zones[{i}].active", 0, 1)
        if type(zone["verts"]) is not list or len(zone["verts"]) != zone["count"]: raise OracleError(f"{label}.zones[{i}].verts: count drift")
        for j, point in enumerate(zone["verts"]):
            if type(point) is not list or len(point) != 2: raise OracleError(f"{label}.zones[{i}].verts[{j}]: shape drift")
            number(point[0], f"{label}.zones[{i}].verts[{j}][0]"); number(point[1], f"{label}.zones[{i}].verts[{j}][1]")
    if value != expected: raise OracleError(f"{label}: fixed control drift")

def validate(document):
    reject_absolute(document)
    exact(document, {"schema", "schema_version", "program_key", "effect_key", "runtime_key", "corpus_revision", "upstream_revision", "factory", "runtime_binding_names", "runtime_binding_abi", "source_uniform_abi", "canonical_binding_contract", "exactness_contract", "comparer_self_tests", "provenance", "input_fixture", "render_cases", "source_mutation_contract", "mutation_anchor_cardinality", "mutation_ledger", "control_group", "claim_boundaries"}, "document")
    integer(document["schema_version"], "schema_version", 2, 2)
    if (document["schema"], document["schema_version"], document["program_key"], document["effect_key"], document["runtime_key"]) != (SCHEMA, 2, KEY, "synth/remap", KEY): raise OracleError("identity drift")
    for field in ("schema", "program_key", "effect_key", "runtime_key", "corpus_revision", "upstream_revision"): string(document[field], field)
    if document["corpus_revision"] != "a024dc3a960cc44af454abc7aebce50456c194e6" or document["upstream_revision"] != "117a236679d1db3ab8f0e278230ece277b57564c": raise OracleError("revision drift")
    if document["factory"] != EXPECTED_FACTORY: raise OracleError("factory identity drift")
    for key in document["factory"]: string(document["factory"][key], f"factory.{key}") if key in ("name", "text_sha256") else boolean(document["factory"][key], f"factory.{key}")
    if document["runtime_binding_names"] != EXPECTED_BINDINGS or document["runtime_binding_abi"] != EXPECTED_RUNTIME_ABI or document["source_uniform_abi"] != EXPECTED_SOURCE_ABI: raise OracleError("binding ABI drift")
    if any(type(item) is not str for item in document["runtime_binding_names"]): raise OracleError("binding name type drift")
    for mapping, label in ((document["runtime_binding_abi"], "runtime ABI"), (document["source_uniform_abi"], "source ABI")):
        for key, value in mapping.items(): string(key, label); string(value, f"{label}.{key}")
    contract = exact(document["canonical_binding_contract"], {"names", "abi", "source_abi"}, "canonical_binding_contract")
    if contract != {"names": EXPECTED_BINDINGS, "abi": EXPECTED_RUNTIME_ABI, "source_abi": EXPECTED_SOURCE_ABI}: raise OracleError("canonical binding contract drift")
    exactness = exact(document["exactness_contract"], {"float32", "rgba8", "tolerance", "dimensions"}, "exactness_contract")
    if exactness != {"float32": "raw little-endian uint32 words; signed zero and NaN payloads significant", "rgba8": "complete independently captured RGBA8 bytes", "tolerance": "none", "dimensions": "checked before lane access"}: raise OracleError("exactness contract drift")
    comparer = exact(document["comparer_self_tests"], set(EXPECTED_COMPARER), "comparer_self_tests")
    if comparer != EXPECTED_COMPARER: raise OracleError("comparer self-test drift")
    provenance = exact(document["provenance"], {"source", "factory_source", "cpu_snapshot", "generator", "materializer"}, "provenance")
    source = exact(provenance["source"], {"relative_path", "sha256"}, "provenance.source")
    if source != {"relative_path": SOURCE, "sha256": "e70bb491b2838bc2e5632a458fb2aeb5488d772d734b6e4caf7958afa9737e7f"}: raise OracleError("shader provenance drift")
    factory_source = exact(provenance["factory_source"], {"relative_path", "sha256"}, "provenance.factory_source")
    if factory_source != {"relative_path": FACTORY_SOURCE, "sha256": EXPECTED_SOURCE_HASH}: raise OracleError("factory source provenance drift")
    snapshot = exact(provenance["cpu_snapshot"], {"argument", "immutable_snapshot", "realpath_containment_checked", "live_checkout_rejected", "import_closure"}, "provenance.cpu_snapshot")
    if snapshot["argument"] != "<immutable-cpu-snapshot-root>" or snapshot["immutable_snapshot"] is not True or snapshot["realpath_containment_checked"] is not True or snapshot["live_checkout_rejected"] is not True: raise OracleError("authority provenance drift")
    closure = snapshot["import_closure"]
    if type(closure) is not list or [(item.get("relative_path"), item.get("sha256")) for item in closure] != sorted(EXPECTED_CLOSURE.items()): raise OracleError("exact 22-file closure drift")
    for index, item in enumerate(closure): exact(item, {"relative_path", "sha256"}, f"closure[{index}]"); string(item["relative_path"], f"closure[{index}].relative_path"); sha(item["sha256"], f"closure[{index}].sha256")
    for name, expected in (("generator", "docs/port-engineering/remap-parity/remap_oracle_generator.mjs"), ("materializer", "tools/glslcpp/generate_remap_native_oracle_include.py")):
        item = exact(provenance[name], {"relative_path", "sha256"}, f"provenance.{name}"); string(item["relative_path"], f"provenance.{name}.relative_path"); sha(item["sha256"], f"provenance.{name}.sha256")
        if item["relative_path"] != expected or item["sha256"] != digest((GENERATOR if name == "generator" else pathlib.Path(__file__)).read_bytes()): raise OracleError(f"{name} provenance drift")
    fixture = exact(document["input_fixture"], {"schema", "coordinate_order", "component_order", "formula"}, "input_fixture")
    if fixture != {"schema": "noisemaker-for-cpp.remap.input-texture.v2", "coordinate_order": "x-fastest row-major", "component_order": ["r", "g", "b", "a"], "formula": "f32(((x*3+y*5+salt)%17)/16), f32(((x*7+y*2+salt)%19)/18), f32(((x*11+y*13+salt)%23)/22), f32(.25+((x+y+salt)%7)/10)"}: raise OracleError("input fixture drift")
    if document["control_group"] != EXPECTED_CONTROL_GROUP: raise OracleError("runtime control group drift")
    for key, value in document["control_group"].items():
        if isinstance(value, dict):
            for nested in value.values(): boolean(nested, f"control_group.{key}") if type(nested) is bool else string(nested, f"control_group.{key}.case")
        else: boolean(value, f"control_group.{key}")
    cases = document["render_cases"]
    if type(cases) is not list or len(cases) != len(EXPECTED_CASES): raise OracleError("render case count drift")
    for case, expected, expected_controls in zip(cases, EXPECTED_CASES, EXPECTED_CONTROLS):
        exact(case, {"name", "width", "height", "salt", "controls", "control_sha256", "input", "expected", "repeat_identity", "public_identity", "input_immutable_exact_bits"}, f"case {case.get('name')}")
        name, width, height, salt, control_hash, input_hash, input_rgba_hash, output_hash, output_rgba_hash = expected
        if (case["name"], case["width"], case["height"], case["salt"], case["control_sha256"]) != (name, width, height, salt, control_hash): raise OracleError(f"fixed case metadata drift: {name}")
        string(case["name"], "case.name"); integer(case["width"], "case.width", 1); integer(case["height"], "case.height", 1); integer(case["salt"], "case.salt", 0); sha(case["control_sha256"], "case.control_sha256"); boolean(case["input_immutable_exact_bits"], "case.input_immutable_exact_bits")
        if case["input_immutable_exact_bits"] is not True or digest((json.dumps(case["controls"], indent=2, ensure_ascii=False) + "\n").encode()) != control_hash: raise OracleError(f"control hash drift: {name}")
        validate_controls(case["controls"], expected_controls, f"case {name}.controls")
        if case["repeat_identity"] != {"exact_float32": True, "exact_rgba8": True, "distinct_output_object": True, "distinct_backing_buffer": True} or case["public_identity"] != {"exact_float32": True, "exact_rgba8": True, "factory_identity": True}: raise OracleError(f"identity controls drift: {name}")
        for identity_name, identity in (("repeat_identity", case["repeat_identity"]), ("public_identity", case["public_identity"])):
            for field, value in identity.items(): boolean(value, f"case {name}.{identity_name}.{field}")
        inp = exact(case["input"], {"width", "height", "salt", "f32_words_le", "f32_sha256", "rgba8_bytes", "rgba8_sha256"}, f"case {name}.input")
        out = exact(case["expected"], {"f32_words_le", "f32_sha256", "rgba8_bytes", "rgba8_sha256"}, f"case {name}.expected")
        if (inp["width"], inp["height"], inp["salt"]) != (width, height, salt): raise OracleError(f"input fixture metadata drift: {name}")
        integer(inp["width"], "input.width", 1); integer(inp["height"], "input.height", 1); integer(inp["salt"], "input.salt", 0); words(inp["f32_words_le"], width * height * 4, f"{name}.input words"); words(out["f32_words_le"], width * height * 4, f"{name}.output words"); byte_values(inp["rgba8_bytes"], width * height * 4, f"{name}.input bytes"); byte_values(out["rgba8_bytes"], width * height * 4, f"{name}.output bytes")
        if (inp["f32_sha256"], inp["rgba8_sha256"], out["f32_sha256"], out["rgba8_sha256"]) != (input_hash, input_rgba_hash, output_hash, output_rgba_hash): raise OracleError(f"fixed payload hash drift: {name}")
        if digest(packed_words(inp["f32_words_le"])) != input_hash or digest(bytes(inp["rgba8_bytes"])) != input_rgba_hash or digest(packed_words(out["f32_words_le"])) != output_hash or digest(bytes(out["rgba8_bytes"])) != output_rgba_hash: raise OracleError(f"payload digest drift: {name}")
        if any(out["f32_words_le"][i] != out["f32_words_le"][3] for i in range(3, len(out["f32_words_le"]), 4)): pass
    source_contract = exact(document["source_mutation_contract"], {"source_relative_path", "source_sha256", "shader_relative_path", "shader_sha256", "execution"}, "source_mutation_contract")
    if source_contract != {"source_relative_path": FACTORY_SOURCE, "source_sha256": EXPECTED_SOURCE_HASH, "shader_relative_path": SOURCE, "shader_sha256": "e70bb491b2838bc2e5632a458fb2aeb5488d772d734b6e4caf7958afa9737e7f", "execution": "independent exact factory source anchor replacements rendered through bindCanonicalKernel/runPass"}: raise OracleError("source mutation contract drift")
    if document["mutation_anchor_cardinality"] != {"total": 7, "anchors": {item[0]: 1 for item in EXPECTED_MUTATION_META}}: raise OracleError("mutation anchor cardinality drift")
    integer(document["mutation_anchor_cardinality"]["total"], "mutation_anchor_cardinality.total", 7, 7)
    for mutation_name, count in document["mutation_anchor_cardinality"]["anchors"].items(): string(mutation_name, "mutation anchor name"); integer(count, f"mutation anchor {mutation_name}", 1, 1)
    ledger = document["mutation_ledger"]
    if type(ledger) is not list or len(ledger) != 7: raise OracleError("mutation count drift")
    for index, (mutation, expected) in enumerate(zip(ledger, EXPECTED_MUTATION_META)):
        name, group, mechanism, anchor, replacement, mutated_hash, anchor_hash, replacement_hash, witnesses, controls = expected
        exact(mutation, {"name", "group", "mechanism", "anchor", "replacement", "independent", "source_relative_path", "source_sha256", "canonical_factory_text_sha256", "mutated_factory_text_sha256", "anchor_occurrence_count", "source_anchor_sha256", "replacement_sha256", "results", "witness_cases", "control_cases"}, f"mutation {index}")
        if (mutation["name"], mutation["group"], mutation["mechanism"], mutation["anchor"], mutation["replacement"], mutation["independent"], mutation["source_relative_path"], mutation["source_sha256"], mutation["canonical_factory_text_sha256"], mutation["mutated_factory_text_sha256"], mutation["anchor_occurrence_count"], mutation["source_anchor_sha256"], mutation["replacement_sha256"], mutation["witness_cases"], mutation["control_cases"]) != (name, group, mechanism, anchor, replacement, True, FACTORY_SOURCE, EXPECTED_SOURCE_HASH, EXPECTED_FACTORY_TEXT_HASH, mutated_hash, 1, anchor_hash, replacement_hash, witnesses, controls): raise OracleError(f"mutation metadata drift: {name}")
        for field in ("name", "group", "mechanism", "anchor", "replacement", "source_relative_path"): string(mutation[field], f"mutation.{field}")
        boolean(mutation["independent"], f"mutation.{name}.independent"); integer(mutation["anchor_occurrence_count"], f"mutation.{name}.anchor_occurrence_count", 1, 1)
        for field in ("source_sha256", "canonical_factory_text_sha256", "mutated_factory_text_sha256", "source_anchor_sha256", "replacement_sha256"): sha(mutation[field], f"mutation.{name}.{field}")
        results = mutation["results"]
        if type(results) is not list or len(results) != len(cases): raise OracleError(f"mutation rows drift: {name}")
        result_hash = digest((json.dumps(results, indent=2, ensure_ascii=False) + "\n").encode())
        if result_hash != EXPECTED_RESULTS_HASHES[index]: raise OracleError(f"mutation witness digest drift: {name}")
        for result, case in zip(results, cases):
            exact(result, {"case", "changed_float32_lanes", "changed_rgba8_bytes", "float32_witness", "rgba8_witness"}, f"mutation {name}.result")
            string(result["case"], "mutation result.case"); integer(result["changed_float32_lanes"], "mutation result.float32 count", 0); integer(result["changed_rgba8_bytes"], "mutation result.rgba8 count", 0)
            for field, max_count in (("changed_float32_lanes", case["width"] * case["height"] * 4), ("changed_rgba8_bytes", case["width"] * case["height"] * 4)):
                if result[field] > max_count: raise OracleError(f"mutation result count out of range: {name}")
            for witness, field in ((result["float32_witness"], "float32_witness"), (result["rgba8_witness"], "rgba8_witness")):
                if witness is None:
                    if result["changed_float32_lanes"] if field == "float32_witness" else result["changed_rgba8_bytes"]: raise OracleError(f"missing mismatch witness: {name}")
                else:
                    exact(witness, {"index", "expected", "actual"}, f"{name}.{field}"); integer(witness["index"], f"{name}.{field}.index", 0); 
                    if field == "float32_witness": string(witness["expected"], f"{name}.{field}.expected"); string(witness["actual"], f"{name}.{field}.actual");
                    else: integer(witness["expected"], f"{name}.{field}.expected", 0, 255); integer(witness["actual"], f"{name}.{field}.actual", 0, 255)
    if document["claim_boundaries"] != {"authority": "canonicalFactory272 from immutable snapshot; C++ output does not participate", "source": "Remap GLSL and generated factory are hash-pinned", "mutations": "independent source anchor replacements, never uniform perturbations"}: raise OracleError("claim boundary drift")
    return document

def q(value): return json.dumps(str(value))
def cpp_float(value):
    text = f"{float(value):.9g}"
    if "." not in text and "e" not in text and "E" not in text: text += ".0"
    return text + "F"
def arr(values, formatter=str): return ", ".join(formatter(value) for value in values)

def emit(document):
    lines = ["// Generated by generate_remap_native_oracle_include.py; exact JSON authority.", "#pragma once", "#include <array>", "#include <cstddef>", "#include <cstdint>", "#include <span>", "#include <string_view>", "namespace remap_oracle {"]
    lines += ["struct BindingAbi { std::string_view name; std::string_view runtime; std::string_view source; };", f"inline constexpr std::array<BindingAbi, {len(EXPECTED_BINDINGS)}> kBindingAbi{{{{"]
    lines += [f"  BindingAbi{{{q(name)}, {q(EXPECTED_RUNTIME_ABI[name])}, {q(EXPECTED_SOURCE_ABI[name])}}}," for name in EXPECTED_BINDINGS]
    lines += ["}};", "struct ZoneControlView { std::uint32_t count; float alpha; bool active; std::span<const std::array<float, 2>> vertices; };", "struct ControlView { std::uint32_t zone_count; std::array<float, 3> bg_color; float bg_alpha; float smooth_edge; std::array<std::int32_t, 2> tile_offset; std::array<std::int32_t, 2> full_resolution; std::array<ZoneControlView, 8> zones; };", "struct RepeatIdentityView { bool exact_float32, exact_rgba8, distinct_output_object, distinct_backing_buffer; };", "struct PublicIdentityView { bool exact_float32, exact_rgba8, factory_identity; };", "struct CaseView { std::string_view name; std::uint32_t width, height, salt; ControlView controls; std::string_view control_sha256, input_f32_sha256, input_rgba8_sha256, f32_sha256, rgba8_sha256; std::span<const std::uint32_t> input_words, output_words, output_alpha_float_words; std::span<const std::uint8_t> input_rgba8_bytes, output_rgba8_bytes, output_alpha_rgba8_bytes; RepeatIdentityView repeat_identity; PublicIdentityView public_identity; bool input_immutable_exact_bits; };", "struct MismatchWitnessView { bool present; std::size_t index; std::uint32_t expected_word, actual_word; std::uint8_t expected_byte, actual_byte; std::uint32_t expected, actual; };", "struct MutationResultView { std::string_view case_name; std::uint32_t changed_float32_lanes, changed_rgba8_bytes; MismatchWitnessView float32_witness, rgba8_witness; };", "struct MutationView { std::string_view name, group, mechanism, anchor, replacement, source_relative_path, source_sha256, canonical_factory_text_sha256, mutated_factory_text_sha256, source_anchor_sha256, replacement_sha256; std::uint32_t anchor_occurrence_count; std::span<const MutationResultView> results; std::span<const std::string_view> witness_cases, control_cases; };", "struct MechanismView { std::string_view name, profile, status, reason; };", f"inline constexpr std::size_t kCaseCount = {len(document['render_cases'])}U;", f"inline constexpr std::string_view kSchema = {q(document['schema'])};", f"inline constexpr std::string_view kProgramKey = {q(KEY)};"]
    for index, case in enumerate(document["render_cases"]):
        zones = list(case["controls"]["zones"])
        while len(zones) < 8: zones.append({"count": 0, "alpha": 1, "active": 0, "verts": []})
        for zone_index, zone in enumerate(zones):
            vertices = zone["verts"] + [[0, 0]] * (32 - len(zone["verts"]))
            lines.append(f"inline constexpr std::array<std::array<float, 2>, 32> kCase{index}Zone{zone_index}Vertices{{{{")
            lines.append("  " + ", ".join(f"std::array<float, 2>{{{cpp_float(point[0])}, {cpp_float(point[1])}}}" for point in vertices))
            lines.append("}};")
        inp, out = case["input"], case["expected"]
        for suffix, values, typ, formatter in (("InputWords", inp["f32_words_le"], "std::uint32_t", lambda x: f"0x{int(x,16):08x}U"), ("OutputWords", out["f32_words_le"], "std::uint32_t", lambda x: f"0x{int(x,16):08x}U"), ("InputBytes", inp["rgba8_bytes"], "std::uint8_t", lambda x: f"{int(x)}U"), ("OutputBytes", out["rgba8_bytes"], "std::uint8_t", lambda x: f"{int(x)}U")):
            lines.append(f"inline constexpr std::array<{typ}, {len(values)}> kCase{index}{suffix}{{{{{arr(values, formatter)}}}}};")
        alpha_words = out["f32_words_le"][3::4]; alpha_bytes = out["rgba8_bytes"][3::4]
        lines.append(f"inline constexpr std::array<std::uint32_t, {len(alpha_words)}> kCase{index}OutputAlphaWords{{{{{arr(alpha_words, lambda x: f'0x{int(x,16):08x}U')}}}}};")
        lines.append(f"inline constexpr std::array<std::uint8_t, {len(alpha_bytes)}> kCase{index}OutputAlphaBytes{{{{{arr(alpha_bytes, lambda x: f'{int(x)}U')}}}}};")
        zone_inits = []
        for zone_index, zone in enumerate(zones): zone_inits.append(f"ZoneControlView{{{zone['count']}U, {cpp_float(zone['alpha'])}, {str(bool(zone['active'])).lower()}, std::span<const std::array<float, 2>>(kCase{index}Zone{zone_index}Vertices)}}")
        control = case["controls"]
        control_init = f"ControlView{{{control['zone_count']}U, {{{arr(control['bg_color'], cpp_float)}}}, {cpp_float(control['bg_alpha'])}, {cpp_float(control['smooth_edge'])}, {{{arr(control['tile_offset'], lambda x: f'{int(x)}')}}}, {{{arr(control['full_resolution'], lambda x: f'{int(x)}')}}}, {{{', '.join(zone_inits)}}}}}"
        repeat, public = case["repeat_identity"], case["public_identity"]
        lines.append(f"inline constexpr CaseView kCase{index}{{{q(case['name'])}, {case['width']}U, {case['height']}U, {case['salt']}U, {control_init}, {q(case['control_sha256'])}, {q(inp['f32_sha256'])}, {q(inp['rgba8_sha256'])}, {q(out['f32_sha256'])}, {q(out['rgba8_sha256'])}, std::span<const std::uint32_t>(kCase{index}InputWords), std::span<const std::uint32_t>(kCase{index}OutputWords), std::span<const std::uint32_t>(kCase{index}OutputAlphaWords), std::span<const std::uint8_t>(kCase{index}InputBytes), std::span<const std::uint8_t>(kCase{index}OutputBytes), std::span<const std::uint8_t>(kCase{index}OutputAlphaBytes), RepeatIdentityView{{{str(repeat['exact_float32']).lower()}, {str(repeat['exact_rgba8']).lower()}, {str(repeat['distinct_output_object']).lower()}, {str(repeat['distinct_backing_buffer']).lower()}}}, PublicIdentityView{{{str(public['exact_float32']).lower()}, {str(public['exact_rgba8']).lower()}, {str(public['factory_identity']).lower()}}}, {str(case['input_immutable_exact_bits']).lower()}}};")
    lines.append(f"inline constexpr std::array<CaseView, {len(document['render_cases'])}> kCases{{{{")
    lines += [f"  kCase{i}," for i in range(len(document["render_cases"]))] + ["}};"]
    for index, mutation in enumerate(document["mutation_ledger"]):
        result_names = f"kMutation{index}Results"; lines.append(f"inline constexpr std::array<MutationResultView, {len(mutation['results'])}> {result_names}{{{{")
        for result in mutation["results"]:
            def witness(value, is_float):
                if value is None: return "MismatchWitnessView{false, 0U, 0U, 0U, 0U, 0U, 0U, 0U}"
                if is_float: return f"MismatchWitnessView{{true, {value['index']}U, 0x{int(value['expected'],16):08x}U, 0x{int(value['actual'],16):08x}U, 0U, 0U, 0x{int(value['expected'],16):08x}U, 0x{int(value['actual'],16):08x}U}}"
                return f"MismatchWitnessView{{true, {value['index']}U, 0U, 0U, {value['expected']}U, {value['actual']}U, {value['expected']}U, {value['actual']}U}}"
            lines.append(f"  MutationResultView{{{q(result['case'])}, {result['changed_float32_lanes']}U, {result['changed_rgba8_bytes']}U, {witness(result['float32_witness'], True)}, {witness(result['rgba8_witness'], False)}}},")
        lines.append("}};")
        for suffix in ("Witness", "Control"):
            names = mutation["witness_cases"] if suffix == "Witness" else mutation["control_cases"]
            lines.append(f"inline constexpr std::array<std::string_view, {len(names)}> kMutation{index}{suffix}Cases{{{{{arr(names, lambda x: q(x))}}}}};")
    lines.append(f"inline constexpr std::array<MutationView, {len(document['mutation_ledger'])}> kMutations{{{{")
    for index, mutation in enumerate(document["mutation_ledger"]):
        mutation_fields = ", ".join(q(mutation[field]) for field in ("name", "group", "mechanism", "anchor", "replacement", "source_relative_path", "source_sha256", "canonical_factory_text_sha256", "mutated_factory_text_sha256", "source_anchor_sha256", "replacement_sha256"))
        lines.append("  MutationView{" + mutation_fields + f", {mutation['anchor_occurrence_count']}U, std::span<const MutationResultView>(kMutation{index}Results), std::span<const std::string_view>(kMutation{index}WitnessCases), std::span<const std::string_view>(kMutation{index}ControlCases)" + "},")
    lines += ["}};", f"inline constexpr std::array<MechanismView, {len(document['claim_boundaries'])}> kClaimBoundaries{{{{"]
    for name, claim in document["claim_boundaries"].items(): lines.append(f"  MechanismView{{{q(name)}, {q('authenticated')}, {q('exact')}, {q(claim)}}},")
    lines += ["}};", f"inline constexpr std::array<MechanismView, 0> kPreparedMechanisms{{{{}}}};", f"inline constexpr std::string_view kSourcePath = {q(SOURCE)};", f"inline constexpr std::string_view kFactoryPath = {q(FACTORY_SOURCE)};", f"inline constexpr std::string_view kFactoryTextSha256 = {q(EXPECTED_FACTORY_TEXT_HASH)};", "static_assert(kCases.size() == kCaseCount);", "static_assert(kMutations.size() == 7U);", "} // namespace remap_oracle", ""]
    return "\n".join(lines)

def checked_payload(path):
    content = checked(path)
    return strict_json(content)

def checked_target(document, path=TARGET):
    actual = checked(path)
    expected = emit(document).encode()
    if actual != expected:
        raise OracleError(f"generated include drift: {path}")
    return actual

def materialize():
    document = validate(checked_payload(ORACLE)); checked(REPORT)
    rendered = emit(document).encode()
    TARGET.write_bytes(rendered); TARGET.with_name(TARGET.name + ".sha256").write_text(sidecar(TARGET, rendered))
    return rendered

def self_test():
    document = validate(checked_payload(ORACLE)); checked(REPORT)
    probes = []
    def reject_raw(raw, label):
        with tempfile.TemporaryDirectory(prefix="remap-oracle-forgery-") as directory:
            path = pathlib.Path(directory) / "forged.json"; path.write_bytes(raw); path.with_name(path.name + ".sha256").write_text(sidecar(path, raw))
            try: validate(strict_json(checked(path)))
            except OracleError as error:
                if str(error).startswith("forgery accepted"): raise OracleError(f"sentinel failure: {label}")
                probes.append(label); return
        raise OracleError(f"forgery accepted: {label}")
    def reject(candidate, label): reject_raw(json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode(), label)
    top_fields = ["schema", "schema_version", "program_key", "effect_key", "runtime_key", "corpus_revision", "upstream_revision", "factory", "runtime_binding_names", "runtime_binding_abi", "source_uniform_abi", "canonical_binding_contract", "exactness_contract", "comparer_self_tests", "provenance", "input_fixture", "render_cases", "source_mutation_contract", "mutation_anchor_cardinality", "mutation_ledger", "control_group", "claim_boundaries"]
    for field in top_fields:
        candidate = copy.deepcopy(document); candidate.pop(field); reject(candidate, f"missing-{field}")
    for label, mutate in (("output-word", lambda x: x["render_cases"][0]["expected"]["f32_words_le"].__setitem__(0, "0x00000000")), ("output-rgba", lambda x: x["render_cases"][0]["expected"]["rgba8_bytes"].__setitem__(0, 0)), ("output-alpha-word", lambda x: x["render_cases"][0]["expected"]["f32_words_le"].__setitem__(3, "0x00000000")), ("output-alpha-byte", lambda x: x["render_cases"][0]["expected"]["rgba8_bytes"].__setitem__(3, 0)), ("output-hash", lambda x: x["render_cases"][0]["expected"].__setitem__("f32_sha256", "0" * 64)), ("output-rgba-hash", lambda x: x["render_cases"][0]["expected"].__setitem__("rgba8_sha256", "0" * 64)), ("input-word", lambda x: x["render_cases"][0]["input"]["f32_words_le"].__setitem__(0, "0x00000000")), ("input-rgba", lambda x: x["render_cases"][0]["input"]["rgba8_bytes"].__setitem__(0, 0)), ("input-f32-hash", lambda x: x["render_cases"][0]["input"].__setitem__("f32_sha256", "0" * 64)), ("input-rgba-hash", lambda x: x["render_cases"][0]["input"].__setitem__("rgba8_sha256", "0" * 64)), ("input-width", lambda x: x["render_cases"][0]["input"].__setitem__("width", 4)), ("input-height", lambda x: x["render_cases"][0]["input"].__setitem__("height", 3)), ("control", lambda x: x["render_cases"][0]["controls"].__setitem__("zone_count", 1)), ("control-hash", lambda x: x["render_cases"][0].__setitem__("control_sha256", "0" * 64)), ("control-zone", lambda x: x["render_cases"][1]["controls"]["zones"][0].__setitem__("count", 4)), ("control-active", lambda x: x["render_cases"][1]["controls"]["zones"][0].__setitem__("active", 0)), ("closure-path", lambda x: x["provenance"]["cpu_snapshot"]["import_closure"][0].__setitem__("relative_path", "escape.js")), ("closure-hash", lambda x: x["provenance"]["cpu_snapshot"]["import_closure"][0].__setitem__("sha256", "0" * 64)), ("closure-extra", lambda x: x["provenance"]["cpu_snapshot"]["import_closure"].append({"relative_path": "extra.js", "sha256": "0" * 64})), ("factory", lambda x: x["factory"].__setitem__("name", "forged")), ("factory-bool", lambda x: x["factory"].__setitem__("canonical_own_key", 1)), ("binding", lambda x: x["runtime_binding_abi"].__setitem__("data", "float")), ("comparer", lambda x: x["comparer_self_tests"].__setitem__("nan_payload", False)), ("mutation", lambda x: x["mutation_ledger"][0].__setitem__("anchor", "forged")), ("mutation-result", lambda x: x["mutation_ledger"][0]["results"][1].__setitem__("changed_float32_lanes", 1)), ("unknown-field", lambda x: x.__setitem__("forged", True)), ("unknown-nested", lambda x: x["render_cases"][0]["expected"].__setitem__("extra", 1)), ("bool-schema", lambda x: x.__setitem__("schema_version", True)), ("float-schema", lambda x: x.__setitem__("schema_version", 2.0)), ("bool-zone-count", lambda x: x["render_cases"][0]["controls"].__setitem__("zone_count", True)), ("float-width", lambda x: x["render_cases"][0].__setitem__("width", 5.0)), ("nonfinite", lambda x: x["render_cases"][0]["controls"].__setitem__("bg_alpha", float("inf"))), ("input-salt", lambda x: x["render_cases"][0]["input"].__setitem__("salt", 2)), ("identity", lambda x: x["render_cases"][0]["repeat_identity"].__setitem__("distinct_output_object", False)), ("identity-bool-int", lambda x: x["render_cases"][0]["public_identity"].__setitem__("factory_identity", 1)), ("source-abi", lambda x: x["source_uniform_abi"].__setitem__("data", "float")), ("source-contract", lambda x: x["source_mutation_contract"].__setitem__("execution", "uniform perturbation")), ("witness-case", lambda x: x["mutation_ledger"][0]["witness_cases"].pop())):
        candidate = copy.deepcopy(document); mutate(candidate); reject(candidate, label)
    canonical = checked(ORACLE)
    reject_raw(canonical.replace(b'"schema_version": 2,', b'"schema_version": 1,\n  "schema_version": 2,', 1), "duplicate-top-level-final-valid")
    reject_raw(canonical.replace(b'"width": 5,\n      "height": 4', b'"width": 5,\n      "width": 5,\n      "height": 4', 1), "duplicate-nested")
    reject_raw(canonical.replace(b'"f32_sha256": "310e2d2fd973f33bb30174bad54c52f2584b057ebdcc75304b7c61e9464c7c52"', b'"f32_sha256": "' + b'0' * 64 + b'",\n        "f32_sha256": "310e2d2fd973f33bb30174bad54c52f2584b057ebdcc75304b7c61e9464c7c52"', 1), "duplicate-nested-final-valid")
    reject_raw(canonical.replace(b'"schema_version": 2', b'"schema_version": ' + b'1' * 5000, 1), "huge-integer")
    expected_include = emit(document).encode()
    with tempfile.TemporaryDirectory(prefix="remap-include-forgery-") as directory:
        forged = pathlib.Path(directory) / TARGET.name
        forged_bytes = expected_include + b"\n// matching-sidecar forge\n"
        forged.write_bytes(forged_bytes); forged.with_name(forged.name + ".sha256").write_text(sidecar(forged, forged_bytes))
        try:
            checked_target(document, forged)
        except OracleError:
            probes.append("matching-sidecar-include")
        else:
            raise OracleError("forgery accepted: matching-sidecar-include")
    if len(probes) < 40: raise OracleError(f"self-test census too small: {len(probes)}")
    print(f"remap materializer self-test: {len(probes)}/{len(probes)} JSON forgeries rejected; matching-sidecar include forge rejected; 64 matching-sidecar forgery probes (JSON); duplicate keys and sidecars verified")

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); parser.add_argument("--check", action="store_true"); parser.add_argument("--self-test", action="store_true"); args = parser.parse_args()
    if sum((args.write, args.check, args.self_test)) != 1: raise SystemExit("choose exactly one of --write, --check, or --self-test")
    if args.self_test: self_test(); return
    if args.write: print(f"remap native include written ({len(materialize())} bytes)"); return
    document = validate(checked_payload(ORACLE)); checked(REPORT); checked_target(document); print(f"remap native oracle: ok ({len(document['render_cases'])} cases, {len(document['mutation_ledger'])} mutations)")

if __name__ == "__main__": main()
