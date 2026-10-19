#!/usr/bin/env python3
"""Fail-closed native include materializer for the Newton authority oracle."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import sys

# Revision authenticated by the immutable oracle capture.
CORPUS_REVISION = "0ed489ec46842bffba33ee2ec65a218b6dda51f5"

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/newton-parity"
ORACLE = PACKAGE / "newton-oracles.json"
TARGET = ROOT / "tests/oracles/newton_expected.inc"
SCHEMA = "noisemaker-for-cpp.newton.pixel-parity.v1"
KEY = "synth/newton:newton"
SOURCE = f"tools/glslcpp/corpus/{CORPUS_REVISION}/sources/synth/newton/newton.glsl"
SOURCE_SHA = "603090e299ccb08fd4db4bf54a2aa6668ed81be971a84a8b679c7f560e5c27ac"
FACTORY_SHA = "75c306dcb6df750cfe3312654336613603e37910d5f8aac907f30b98f200dbc9"
GENERATOR_RELATIVE = "docs/port-engineering/newton-parity/newton_oracle_generator.mjs"
MATERIALIZER_RELATIVE = "tools/glslcpp/generate_newton_native_oracle_include.py"
GENERATOR_SHA = "39dcb4d62909fc80dee2226199e424f66c08236df4c4d573c0ac66bd51be70e4"
EXPECTED_BINDING_NAMES = ["resolution", "tileOffset", "fullResolution", "time", "degree", "relaxation", "iterations", "tolerance", "poi", "centerHiX", "centerHiY", "centerLoX", "centerLoY", "zoomSpeed", "zoomDepth", "degreeSpeed", "degreeRange", "relaxSpeed", "relaxRange", "rotation", "outputMode", "invert"]
EXPECTED_BINDING_ABI = {name: ("Vec2" if name in {"resolution", "tileOffset", "fullResolution"} else "number") for name in EXPECTED_BINDING_NAMES}
EXPECTED_CLOSURE = {
    "src/csl/glsl-kernel.js": "f5664e2c90289c82f7109cea910fb5de71ae08f5c2204fb569299a9c49a645ff",
    "src/csl/glsl-runtime.js": "ad71e22deeb31ad1f19f81923704c9ad0e1ef0475f9a333e0d5fe9088051eebd",
    "src/csl/metal-division.js": "104cda4fda758fcdfd20f69264a92c1190830102814aec8aa9706058642ce2a8",
    "src/csl/metal-reciprocal-data.js": "08905259e72a066e77675f98b9700d6c3a6467662f5de562d8f8e1e14d082c87",
    "src/csl/metal-reciprocal-grid.js": "bd6613830c4239ff9b21a4157875a7c92ced898fd706e735527f39552be11e39",
    "src/csl/runtime.js": "a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee",
    "src/effects/adapters/bit-effects.js": "5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7",
    "src/effects/adapters/crt.js": "c37f70e15b6481b2f870761bf103529cd45cf6e5e714a0a6fd731dbe90c1c73f",
    "src/effects/adapters/f32-color.js": "b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046",
    "src/effects/adapters/fractal.js": "73bb60668d98a142edcd535c146527945af445baa694595da2a19fe0a649e804",
    "src/effects/adapters/index.js": "dd2ca7681884fbc3fa2687faeb52aced50076a5f0856736b63831e859073d22e",
    "src/effects/adapters/julia.js": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
    "src/effects/adapters/median.js": "e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583",
    "src/effects/adapters/palette.js": "8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452",
    "src/effects/adapters/remap.js": "91fd829ba2ad68fabab4124f5464994fc267daa097af4f3dd5a7e20f075f9e79",
    "src/effects/adapters/snow.js": "9acaa9c8a612e3b58e5935646bc37540146a52cda6c947cc67d5443d468f041c",
    "src/effects/catalog.js": "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4",
    "src/effects/definition.js": "4edcee437bc4fd4364f5fbf84878b9d6ca49f5799a49d876ec8df05ac0135545",
    "src/effects/generated/canonical-adapter-data.js": "ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab",
    "src/effects/generated/canonical-kernels.js": "86fc0a3b6fdd2227341b2b59e0d7dd4177980f1b78b57e61c85c8f7525391423",
    "src/effects/generated/kernels.js": "b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01",
    "src/effects/generated/upstream-snapshot.js": "272570c86da679801350fdfd78922635249f1475a3afffd74950c7a5136fe467",
    "src/effects/registry.js": "8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618",
    "src/runtime/automation.js": "7ec5b11a269eae6899a2e2d78a4687d87e82b0e623a8b150d0fa7d8feb09065f",
    "src/runtime/pass-runner.js": "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa",
    "src/runtime/sampler.js": "5a3e494e79f431605fecd682fd9fe6fc8437dde1332f1dc872632af59d0eeaf5",
    "src/runtime/surface.js": "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59",
}
EXPECTED_CASES = [
    ("manual-baseline", 4, 4, 0.25, 0, 0, 80, 3, 1, 0.001, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1),
    ("poi-spiral", 4, 3, 0.75, 2, 0, 100, 3, 1, 0.0001, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 11, 0, 0.25, -0.25, 2),
    ("root-mode", 3, 4, 1.25, 4, 1, 120, 5, 0.9, 0.01, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, -17, 0, 0, 0, 3),
    ("combined-mode", 5, 3, 2, 3, 2, 150, 5, 1.2, 0.005, 0.01, -0.02, 1e-7, -2e-7, 1.2, 4, 0.5, 1, 0.7, 0.3, 25, 0, -0.5, 0.5, 4),
    ("invert-axis", 4, 4, 0.5, 1, 0, 70, 3, 1, 0.002, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 1, 0, 0, 5),
    ("degree-axis", 3, 3, 1.1, 0, 0, 90, 7, 1, 0.003, -0.2, 0.15, 0, 0, 0, 1, 0, 0, 0, 0, 8, 0, 0, 0, 6),
    ("relax-axis", 3, 5, 1.7, 0, 2, 110, 4, 1.6, 0.002, 0.1, -0.1, 0, 0, 0.8, 2, 0, 0, 0, 0, 33, 0, 0, 0, 7),
    ("tolerance-axis", 5, 4, 0.9, 5, 1, 100, 6, 1, 0.05, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, -9, 0, 0, 0, 8),
]
EXPECTED_CASE_DIGESTS = {
    "manual-baseline": ("e80fc7f38abf3cc8ac361cd92433fcb790d9dcec267c02b0199e1f37ec59b845", "aed506c39dd6f18653a080b888f062e0edbf4d572233008f98e7655276d9f9e3", "28e91afec23518e5b92bef795eec893e5652808f3ed4c0b51b9b768bc0ef9cf5"),
    "poi-spiral": ("bbd46a43c09ccf4f74ce4462c0274ab7a6acc7ad2b66d06b8ca313aaac8041f1", "60cbc94cfa8aaad6c39f20eea141abac03a9539cb75097a00e9a454f33bba3b5", "af0cd18078f807003084e0bab8ef9fed5991f05cdccf351b476b8cfb66a07bb1"),
    "root-mode": ("c92ddf2878c9bc13d0383da081bfccf25942161d1ec31617a4284e9e446c29e8", "e31a8a32fcc21d45b6a4ed14023ed1829a79ebb6c2b6e76f25b9f68f36843ba3", "c62ad7f6c19131f0be1d9c0de6b941582f85cd83a3a8ff78ab652be146faa2ce"),
    "combined-mode": ("ee903d8d811e3a09ab1b8be472bff389ef46ce3317ac26d2dfb2c4d05f7c0789", "8697bd2a989eff81638b29b347081ec49803c02442c4dc7920e066685acfcb60", "472fa4a98844b3670cda33e1eed0cc07bcbf6d8fd6b46282246c211451bace73"),
    "invert-axis": ("0cf32eaaf33b72ee8475938c52a05f7a3b757296f4532fb63743948faf9fec50", "9c9a2fcc22d027ccc9a490459361e97710c2d856bc50140373d6af6fa08aaac8", "1b4cbb2005f0fbe5016c28fdeebc1369ee035e297a4c386ad9b30063dc436519"),
    "degree-axis": ("066e1e51950144111002465f8d5ef97174c7e3d18e227cedcb9bdc73f20a6660", "290a12bc87bac6c65ee05410c810acc85f4029c0db4197dcd9e88d04ddc7ce29", "184e963bba2f4ba8c8df92e7988af205863226fee1b0560c9f43b6f523cba664"),
    "relax-axis": ("576e50f143b304713b25d9bb3d52de9c73504a194ec24a2de44528c3f1b26952", "2d34fa9d3435ef0cf102859c2e0a9d80e646502f5d6e18f46dcc1fadab3e4778", "1e978090954cc8d18a2c95546577f7eae6f5f183bb787651a56c6d8285c23b21"),
    "tolerance-axis": ("4e472aa6d3b790eb920cdbcc20bfb1f6cd989e6ff530bee0ae4c18baf25a9e26", "68ce3ccc4770b082b0ca69e38a2dff21faf781a4627e582ab05cc611e6ad5508", "b1afc3dbe46c96d9627c89a90caea13bd4d5768cdc9929dcddb759fc39b5d1fa"),
}
MUTATION_EXPECTATIONS = {
    "cross-lane-assignment": ("cross-lane-assignment", "replace source-order sequential matrix lane writes with swapped lane owners", "(uv[0] = cpu_matrix_assignment_0[0], uv[1] = cpu_matrix_assignment_0[1], uv);", "(uv[0] = cpu_matrix_assignment_0[1], uv[1] = cpu_matrix_assignment_0[0], uv);", "149ab0159311acdd8cca9e53898eabcdea648df6bb7fb24e4752f2939c84f8bf", "60de283bd0993a17990a04714b5d2fb0fe173335ff8544f0867c22e64539dbb6", "366d9831d5cd8197c0654a21251d0c25b8de62d5cf5a7ff7c6a787693800114b", 1, False),
    "df64-cmul-rr-owner": ("out-materialization", "replace df64_cmul real out-owner materialization", "df64_sub(df64_mul(ar, br), df64_mul(ai, bi)).reduce((res,el,i)=>(res[i] = el, res), rr);", "rr.fill(0);", "e89208ecd9ab8332fffdbe4883ad83d6cef61189a6a5f90fa17bff53c20d4b3b", "abf4cef99e6692abbc206f6b09ae63292eb618dee0e848b2c6d177a82aaf343a", "c37782c9bf5a8802f18eb1383029ecd1e3d1b97e1d54fe490ebb8e2a17dac930", 1, False),
    "df64-cmul-ri-owner": ("out-materialization", "replace df64_cmul imaginary out-owner materialization", "df64_add(df64_mul(ar, bi), df64_mul(ai, br)).reduce((res,el,i)=>(res[i] = el, res), ri);", "ri.fill(0);", "8da16872d98cd3143127f4f0e7896c939285713f40494cec23312062f323eb07", "4636913edbd7895e0beaa15d30ef8604dc468ee98fa736cf4c19820611a136c1", "1e980c943cc3559f26a96a890217ce22eba1a1406b3abfa646ff996b1bab9580", 1, False),
    "transform-re-owner": ("out-materialization", "replace transformCoords real out-owner materialization", "df64_add(uv_re_df, cX_df).reduce((res,el,i)=>(res[i] = el, res), re_df);", "re_df.fill(0);", "c64a4ed2e242a7d5f91cde6bd08b632ef75c166a8f129711ca85b2c3b2cab016", "d8b4046abb0651fd28f0b8374d77fbd53a407a35d690132a0fae69c29631fb46", "fd1935899ebfe754da0b63465a66df983aa9fe94d7e318ef59201c92f9938dcb", 1, False),
    "transform-im-owner": ("out-materialization", "replace transformCoords imaginary out-owner materialization", "df64_add(uv_im_df, cY_df).reduce((res,el,i)=>(res[i] = el, res), im_df);", "im_df.fill(0);", "02c85b90268647deca65ce6711344bc566a99ed16d03bb68a11f480b9c16da86", "479fc270dd981006542b1dcbdcfe3f626091c75896a4ca0546ae042715ddf147", "8423858fb360cbe9aa945b089bcb4735c7c6d97c28e6d89402ec23186ac846d4", 1, False),
    "cmul-call-materialization": ("out-materialization", "replace df64_cmul power carrier with a zero imaginary owner", "(df64_cmul(pwr, pwi, zr_df, zi_df, tr, ti), [tr, ti] = df64_cmul.__out__, df64_cmul.__return__);", "(df64_cmul(pwr, pwi, zr_df, zi_df, tr, ti), [tr, ti] = [tr, new $runtime.PooledFloat32Array([0, 0])], df64_cmul.__return__);", "ca28e3d43a7c75caf297884c6edc444ae8e14233e7078349e6bc18e6166c8ec1", "7f61da5c2e9554b5ab2a67bd61fd76a1932002d18baf4130418f225ef1061eed", "66177a1eb787ed5da3ff8e0e407cb633e33b89ebb99084fe90ac861d7b3c6c98", 1, False),
    "znr-call-materialization": ("out-materialization", "replace df64_cmul result carrier at the z-power owner", "(df64_cmul(pwr, pwi, zr_df, zi_df, znr, zni), [znr, zni] = df64_cmul.__out__, df64_cmul.__return__);", "(df64_cmul(pwr, pwi, zr_df, zi_df, znr, zni), [znr, zni] = [znr, new $runtime.PooledFloat32Array([0, 0])], df64_cmul.__return__);", "85d12836ac2ccaf218c77f5c199394bec3593e3ea6756d93ac5267e5495d60be", "dbb2b5a5d06422d312c2f54e51501cec804ee54a1534e35dee5e35fb3304921d", "e684a7ce019b81572fabb81b70f2a493e3a89c659c25c409025eab22b5d9a9af", 1, False),
    "transform-call-materialization": ("out-materialization", "replace transformCoords out carrier owner", "(transformCoords_df64(globalCoord, new $runtime.PooledFloat32Array([cHi[0], cLo[0]]), new $runtime.PooledFloat32Array([cHi[1], cLo[1]]), zoom, rotation, re_df, im_df), [re_df, im_df] = transformCoords_df64.__out__, transformCoords_df64.__return__);", "(transformCoords_df64(globalCoord, new $runtime.PooledFloat32Array([cHi[0], cLo[0]]), new $runtime.PooledFloat32Array([cHi[1], cLo[1]]), zoom, rotation, re_df, im_df), [re_df, im_df] = [transformCoords_df64.__out__[0], new $runtime.PooledFloat32Array([0, 0])], transformCoords_df64.__return__);", "bea400d7e4fac3585776e8ccf8414b55772bf4a2aab5ca69a1586747c5e0f1ce", "88330c4f8c159ed29c5d64ac9c90251f0a0327dddcc3b64afcb43e732bff0893", "cd73ab7dc3bbe35eda1ae994c8010bc4a8589bf121bbe26ef6d2ef9b4f7d5727", 1, False),
    "iteration-outer-bound": ("control-axis", "shorten Newton iteration bound", "for (var n = 0; n < 500; n++)", "for (var n = 0; n < 1; n++)", "2fa5d3708bc706606f156ddc0d8051c0192db13c897fde90d3af264dc8c99176", "0af2e648612cac1f2b754f89c7d2bf20990bd0260a875d0dfbb6dc0336a29dd3", "643566303f4e8ac9c29d7468face8c52cefd9211db08389ce1c87a255e5f9db2", 1, False),
    "iteration-power-bound": ("control-axis", "shorten repeated-power bound", "for (var j = 0; j < 7; j++)", "for (var j = 0; j < 1; j++)", "517bd559aa3a66d02c27299d99e0cf7c5425159edfb1a777ab8cbe5b6f31f5e5", "44d41ffcb3a2df0da1327c2e879f0881d5df6f96050ad8a7d144461c1c155fc1", "a89dad5ee88b72ecfa0d9f4c7f3729cc37e1a393badeab7524c74f20af712227", 1, False),
    "degree-control-axis": ("control-axis", "offset effective degree control", "var effDegree = degree instanceof Float32Array ? $runtime.copy(degree) : degree;", "var effDegree = (degree instanceof Float32Array ? $runtime.copy(degree) : degree) + 1;", "d17e5df4de39b0f461d971701faf7ee249469f57805546210a566361481289df", "403a746a5b2f624cdd5446ffdc2ed7fb4ed6a19569ee3602b12b72fb2edb368b", "b6977df6d5f0a3ba48350b49198a2329dd1d566214e6c810551418e5b573c621", 1, False),
    "relaxation-control-axis": ("control-axis", "offset effective relaxation control", "var effRelax = relaxation instanceof Float32Array ? $runtime.copy(relaxation) : relaxation;", "var effRelax = (relaxation instanceof Float32Array ? $runtime.copy(relaxation) : relaxation) + 0.25;", "57655b5b826bc285e3907291bb835ba11036ed747fad73765cb39467bc5f0204", "855d6e3d5afd533df8516f85092e198d84219a9627f4344b26805bfaaf7bc47a", "9370abcfbe11c54986a7752a3af12ae85ba2a03d4c7ba50a0022f89ec05a5db2", 1, False),
    "tolerance-control-axis": ("control-axis", "widen convergence tolerance control", "if (d < tolerance) {", "if (d < (tolerance * 2)) {", "2f2f19fee0d0a168d807ca756638258383b824a4753fb9128dda53cb982da0d5", "0e93565ab39d09935a82bc7a85872fbee939ee6aafcea224608509b0c7b9f15c", "3e61d43dcbd50c6d8ae3cbcd10475303e60a0f4c3bc7c4c35496364aa8dd0dba", 1, False),
    "rotation-control-axis": ("control-axis", "reverse rotation control", "var angle = (-rot * TAU) / 360;", "var angle = (rot * TAU) / 360;", "8fdfbf563a832b96d431c97cbea608b2641c27c432cf6e3419206e02283f57b7", "a78682a72d8db423b7a0e786da8692ffc8210e028d52d3723e228874748946e2", "3229bed719c214d905b459dc024d341dabbd1b17cada375e51186bffcdb1aa8b", 1, False),
    "invert-control-axis": ("control-axis", "remove inversion control", "value = 1 - value;", "value = value;", "220c9f783a3f9c7ce4ba4fcee7ef7cb10425c6b74f6513c056850879b3d32d51", "b2bbdd0bed7c146e526bf4a47052b71622efdbec0d1480c86864c1b6b911c06a", "02d187376dfd606d121182feb82539d4b970e5bdadc1be6a259f0119f1d261d0", 1, False),
    "struct-POIData-declaration": ("struct-declaration", "source-bound POIData declaration probe paired with an executed canonical POI representation mutant", "struct POIData {", "struct POIData { float provenanceWitness;", "36b6b7fe0fbf811c40555409cbacd624785ddf8adc99f882a1027a3ab64c6777", "78716247ad319ac410b49146c19f56a47ebe9ea3fe6460969aff58253343e533", "7c74f52b2a8b829703c2974156b5294756d4285cb52a693d01af57a024bb2498", 1, False),
}
STRUCTURAL_FACTORY_EXPECTATION = {
    "factory_anchor": "return {\n  \tcenter: new $runtime.PooledFloat32Array([0, 0, 0, 0]),\n  \tdeg: 3,\n  \tmaxZoom: 7\n  \t};\n  \t};\n  \tif (idx == 2) {",
    "factory_replacement": "return {\n  \tcenter: new $runtime.PooledFloat32Array([0, 0, 0, 0]),\n  \tdeg: 4,\n  \tmaxZoom: 7\n  \t};\n  \t};\n  \tif (idx == 2) {",
    "factory_anchor_sha256": "bd04d93c5fae58e0e94b9918d8f0012aac371ae99bfa5e1be39d64416a701675",
    "factory_replacement_sha256": "698f6e0fe1cba9f57298ab13f15f76d23890d7b63c0b6a83b7c3b6d13ac147b4",
}

class MaterializationError(RuntimeError):
    pass


HEX_WORD = re.compile(r"^0x[0-9a-f]{8}$")
HEX256 = re.compile(r"^[0-9a-f]{64}$")


def digest_words(values: list[str]) -> str:
    return hashlib.sha256(b"".join(int(value, 16).to_bytes(4, "little") for value in values)).hexdigest()


def reject_absolute(value: object, label: str = "document") -> None:
    if isinstance(value, str):
        if value.startswith(("/", "\\\\")) or re.search(r"(?:^|[\\/])(Users|private|tmp|home)[\\/]", value):
            raise MaterializationError(f"{label}: absolute-looking string")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_absolute(item, f"{label}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            reject_absolute(item, f"{label}.{key}")


def exact(value: object, expected: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise MaterializationError(f"{label}: missing/extra fields")


def words(value: object, count: int, label: str) -> list[str]:
    if not isinstance(value, list) or len(value) != count or any(not isinstance(item, str) or not HEX_WORD.fullmatch(item) for item in value):
        raise MaterializationError(f"{label}: malformed Float32 words/count")
    return value


def validate(document: dict) -> dict:
    reject_absolute(document)
    top = {"schema", "schema_version", "program_key", "effect_key", "runtime_key", "corpus_revision", "upstream_revision", "factory", "runtime_binding_names", "runtime_binding_abi", "canonical_binding_contract", "exactness_contract", "comparer_self_tests", "provenance", "render_cases", "source_mutation_contract", "mutation_anchor_cardinality", "mutation_ledger", "control_group", "cross_lane_assignment_profile", "claim_boundaries"}
    exact(document, top, "document")
    if document["schema"] != SCHEMA or document["schema_version"] != 1 or document["program_key"] != KEY or document["effect_key"] != "synth/newton" or document["runtime_key"] != KEY:
        raise MaterializationError("schema/program identity")
    if document["corpus_revision"] != CORPUS_REVISION or document["upstream_revision"] != "6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d":
        raise MaterializationError("revision provenance")
    if document["factory"] != {"name": "canonicalFactory272", "text_sha256": FACTORY_SHA, "public_factory_is_canonical_identity": True, "adapter_own_key": False}:
        raise MaterializationError("factory identity/adapter contract")
    if document["runtime_binding_names"] != EXPECTED_BINDING_NAMES or document["runtime_binding_abi"] != EXPECTED_BINDING_ABI or document["canonical_binding_contract"] != {"names": EXPECTED_BINDING_NAMES, "abi": EXPECTED_BINDING_ABI}:
        raise MaterializationError("binding names/ABI contract")
    exactness = {"float32": "raw little-endian uint32 words; signed zero and NaN payloads significant", "rgba8": "complete independently captured RGBA8 bytes", "tolerance": "none", "dimensions": "checked before lane access", "comparison": "dimensions, counts, every uint32 word, every RGBA8 byte"}
    if document["exactness_contract"] != exactness:
        raise MaterializationError("exactness contract")
    comparer = document["comparer_self_tests"]
    if comparer != {"dimensions_before_access": True, "first_mismatch_reported": True, "raw_words_and_rgba8_independent": True, "cases": {"good": True, "dimensions": True, "short": True, "long": True, "rgba8_count": True, "rgba8_mismatch": True, "signed_zero": True, "nan_payload": True}}:
        raise MaterializationError("comparer self-test contract")
    provenance = document["provenance"]
    exact(provenance, {"source", "cpu_snapshot", "generator", "materializer"}, "provenance")
    if provenance["source"] != {"relative_path": SOURCE, "sha256": SOURCE_SHA}:
        raise MaterializationError("source provenance")
    snapshot = provenance["cpu_snapshot"]
    if snapshot.get("argument") != "<immutable-cpu-snapshot-root>" or snapshot.get("immutable_snapshot") is not True or snapshot.get("realpath_containment_checked") is not True or snapshot.get("live_checkout_rejected") is not True or snapshot.get("closure_cardinality") != len(EXPECTED_CLOSURE):
        raise MaterializationError("immutable CPU snapshot contract")
    closure = snapshot.get("import_closure")
    if not isinstance(closure, list) or {item.get("relative_path"): item.get("sha256") for item in closure} != EXPECTED_CLOSURE or len(closure) != len(EXPECTED_CLOSURE) or any(set(item) != {"relative_path", "sha256"} for item in closure):
        raise MaterializationError("import closure contract")
    if provenance["generator"] != {"relative_path": GENERATOR_RELATIVE, "sha256": GENERATOR_SHA}:
        raise MaterializationError("generator provenance")
    if provenance["materializer"] != {"relative_path": MATERIALIZER_RELATIVE}:
        raise MaterializationError("materializer provenance")
    cases = document["render_cases"]
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES):
        raise MaterializationError("case cardinality")
    names = [item.get("name") for item in cases]
    if names != [item[0] for item in EXPECTED_CASES]:
        raise MaterializationError("case names/order")
    for case, expected in zip(cases, EXPECTED_CASES):
        expected_case_keys = {"name", "width", "height", "time", "poi", "outputMode", "iterations", "degree", "relaxation", "tolerance", "centerHiX", "centerHiY", "centerLoX", "centerLoY", "zoomSpeed", "zoomDepth", "degreeSpeed", "degreeRange", "relaxSpeed", "relaxRange", "rotation", "invert", "tileX", "tileY", "salt", "input", "expected", "input_immutable_exact_bits", "bindings", "repeat_identity", "repeat_output_object_distinct", "repeat_output_data_distinct", "public_direct_identity", "independent_output_storage"}
        exact(case, expected_case_keys, f"case {case.get('name')}")
        if tuple(case[key] for key in ("name", "width", "height", "time", "poi", "outputMode", "iterations", "degree", "relaxation", "tolerance", "centerHiX", "centerHiY", "centerLoX", "centerLoY", "zoomSpeed", "zoomDepth", "degreeSpeed", "degreeRange", "relaxSpeed", "relaxRange", "rotation", "invert", "tileX", "tileY", "salt")) != expected:
            raise MaterializationError(f"case {case['name']}: frozen controls")
        width, height = case["width"], case["height"]
        bindings = {name: ([width, height] if name in {"resolution", "fullResolution"} else [case["tileX"], case["tileY"]] if name == "tileOffset" else case[name]) for name in EXPECTED_BINDING_NAMES}
        if case["bindings"] != bindings or case["repeat_identity"] is not True or case["repeat_output_object_distinct"] is not True or case["repeat_output_data_distinct"] is not True or case["public_direct_identity"] is not True or case["independent_output_storage"] is not True or case["input_immutable_exact_bits"] is not True:
            raise MaterializationError(f"case {case['name']}: binding/control identity")
        count = width * height * 4
        input_data, output = case["input"], case["expected"]
        exact(input_data, {"width", "height", "f32_words_le", "f32_sha256"}, f"case {case['name']} input")
        exact(output, {"f32_words_le", "f32_sha256", "rgba8_bytes", "rgba8_sha256"}, f"case {case['name']} output")
        if input_data["width"] != width or input_data["height"] != height or output.get("width", width) != width or output.get("height", height) != height:
            raise MaterializationError(f"case {case['name']}: dimensions")
        input_words = words(input_data["f32_words_le"], count, f"case {case['name']} input")
        output_words = words(output["f32_words_le"], count, f"case {case['name']} output")
        input_digest, output_digest, rgba_digest = EXPECTED_CASE_DIGESTS[case["name"]]
        if input_data["f32_sha256"] != input_digest or output["f32_sha256"] != output_digest or input_data["f32_sha256"] != digest_words(input_words) or output["f32_sha256"] != digest_words(output_words):
            raise MaterializationError(f"case {case['name']}: Float32 digest")
        rgba = output["rgba8_bytes"]
        if not isinstance(rgba, list) or len(rgba) != count or any(not isinstance(item, int) or not 0 <= item <= 255 for item in rgba) or output["rgba8_sha256"] != rgba_digest or output["rgba8_sha256"] != hashlib.sha256(bytes(rgba)).hexdigest():
            raise MaterializationError(f"case {case['name']}: RGBA8 digest/count")
    if document["control_group"] != {"repeatability": {"case": "manual-baseline", "identical_float32": True, "identical_rgba8": True, "distinct_output_objects": True, "distinct_output_data": True}, "input_immutability": {"case": "manual-baseline", "unchanged": True}, "independent_output_storage": {"case": "manual-baseline", "distinct_data_objects": True}, "public_direct_identity": True}:
        raise MaterializationError("control group")
    if document["source_mutation_contract"] != {"source_relative_path": SOURCE, "source_sha256": SOURCE_SHA, "canonical_factory_text_sha256": FACTORY_SHA, "execution": "each exact factory anchor/replacement is evaluated and executed through bindCanonicalKernel/runPass; struct-POIData-declaration additionally records a source-bound struct probe paired with its executed POI representation mutant"}:
        raise MaterializationError("source mutation contract")
    if document["claim_boundaries"] != {"absolute_paths": "stable placeholders only", "authority": "unmodified public canonicalFactory272 from immutable CPU snapshot; no local reimplementation or C++ output participates", "adapter": "no adapter owns this key", "mutations": "exact source/factory anchor replacements are executed authority mutations, not uniform perturbations"}:
        raise MaterializationError("claim boundaries")
    ledger = document["mutation_ledger"]
    if not isinstance(ledger, list) or [item.get("name") for item in ledger] != list(MUTATION_EXPECTATIONS):
        raise MaterializationError("mutation ledger identity/order")
    for item in ledger:
        name = item["name"]
        expected = MUTATION_EXPECTATIONS[name]
        common_mutation_keys = {"name", "group", "mechanism", "independent", "structural_only", "source_relative_path", "source_sha256", "canonical_factory_text_sha256", "source_anchor", "replacement", "source_anchor_sha256", "replacement_sha256", "mutated_factory_text_sha256", "anchor_occurrence_count", "required_witnesses", "required_witness_results"}
        expected_mutation_keys = common_mutation_keys | ({"structural_probe", "source_probe_anchor", "source_probe_replacement", "source_probe_anchor_sha256", "source_probe_replacement_sha256", "factory_anchor", "factory_replacement", "factory_anchor_sha256", "factory_replacement_sha256"} if name == "struct-POIData-declaration" else set())
        if set(item) != expected_mutation_keys:
            raise MaterializationError(f"{name}: mutation fields")
        if tuple(item[key] for key in ("group", "mechanism", "source_anchor", "replacement", "source_anchor_sha256", "replacement_sha256", "mutated_factory_text_sha256", "anchor_occurrence_count", "structural_only")) != expected:
            raise MaterializationError(f"{name}: mutation pin")
        if item["independent"] is not True or item["source_relative_path"] != SOURCE or item["source_sha256"] != SOURCE_SHA or item["canonical_factory_text_sha256"] != FACTORY_SHA or hashlib.sha256(item["source_anchor"].encode()).hexdigest() != item["source_anchor_sha256"] or hashlib.sha256(item["replacement"].encode()).hexdigest() != item["replacement_sha256"]:
            raise MaterializationError(f"{name}: mutation provenance/hash")
        if name == "struct-POIData-declaration":
            if item["structural_probe"] is not True or item["source_probe_anchor"] != item["source_anchor"] or item["source_probe_replacement"] != item["replacement"] or item["source_probe_anchor_sha256"] != item["source_anchor_sha256"] or item["source_probe_replacement_sha256"] != item["replacement_sha256"] or any(item[key] != value for key, value in STRUCTURAL_FACTORY_EXPECTATION.items()) or hashlib.sha256(item["factory_anchor"].encode()).hexdigest() != item["factory_anchor_sha256"] or hashlib.sha256(item["factory_replacement"].encode()).hexdigest() != item["factory_replacement_sha256"]:
                raise MaterializationError(f"{name}: source-bound structural probe/factory mutation")
        results = item["required_witness_results"]
        if not item["required_witnesses"] or [row.get("case") for row in results] != item["required_witnesses"] or any(not isinstance(row.get("mismatched_lanes"), int) or row["mismatched_lanes"] <= 0 for row in results):
            raise MaterializationError(f"{name}: behavioral witness contract")
    cardinality = document["mutation_anchor_cardinality"]
    expected_groups = {group: sum(1 for row in MUTATION_EXPECTATIONS.values() if row[0] == group) for group in {row[0] for row in MUTATION_EXPECTATIONS.values()}}
    if cardinality != {"total": len(MUTATION_EXPECTATIONS), "by_group": expected_groups, "anchors": {name: row[7] for name, row in MUTATION_EXPECTATIONS.items()}}:
        raise MaterializationError("mutation cardinality")
    profile = document["cross_lane_assignment_profile"]
    cross = document["mutation_ledger"][0]
    if profile != {"status": "authenticated", "source_bound": "newton source and canonical factory pins", "anchor": cross["source_anchor"], "replacement": cross["replacement"], "mutated_factory_text_sha256": cross["mutated_factory_text_sha256"]}:
        raise MaterializationError("cross-lane assignment profile")
    return document


def cpp_number(value: object) -> str:
    if isinstance(value, int) and not isinstance(value, bool):
        return f"{value}.0F"
    return f"{float(value):.9g}F"


def render(document: dict) -> str:
    cases = document["render_cases"]
    out = ["// Generated from the authenticated Newton JSON oracle.\n#pragma once\n#include <array>\n#include <cstddef>\n#include <cstdint>\n#include <span>\n#include <string_view>\n\nnamespace newton_oracle {\n", f'inline constexpr std::string_view kProgramKey = "{KEY}";\n', f'inline constexpr std::string_view kOracleSha256 = "{hashlib.sha256(ORACLE.read_bytes()).hexdigest()}";\n', f'inline constexpr std::string_view kFactoryTextSha256 = "{FACTORY_SHA}";\n']
    out.append(f"inline constexpr std::array<std::string_view, {len(EXPECTED_BINDING_NAMES)}> kBindingNames{{{{\n  " + ", ".join('"' + name + '"' for name in EXPECTED_BINDING_NAMES) + "\n}};\n")
    out.append(f"struct BindingAbiView {{ std::string_view name; std::string_view category; }};\ninline constexpr std::array<BindingAbiView, {len(EXPECTED_BINDING_NAMES)}> kBindingAbi{{{{\n")
    for name in EXPECTED_BINDING_NAMES:
        out.append(f'  BindingAbiView{{"{name}", "{EXPECTED_BINDING_ABI[name]}"}},\n')
    out.append("}};\nstruct BindingControl { std::array<float, 2> resolution; std::array<float, 2> tileOffset; std::array<float, 2> fullResolution; float time; float degree; float relaxation; float iterations; float tolerance; float poi; float centerHiX; float centerHiY; float centerLoX; float centerLoY; float zoomSpeed; float zoomDepth; float degreeSpeed; float degreeRange; float relaxSpeed; float relaxRange; float rotation; float outputMode; float invert; };\n")
    for index, case in enumerate(cases):
        b = case["bindings"]
        scalar_values = [b[name] for name in EXPECTED_BINDING_NAMES[3:]]
        scalar_text = ", ".join(cpp_number(value) for value in scalar_values)
        out.append(f"inline constexpr BindingControl kCase{index}Bindings{{{{{cpp_number(b['resolution'][0])}, {cpp_number(b['resolution'][1])}}}, {{{cpp_number(b['tileOffset'][0])}, {cpp_number(b['tileOffset'][1])}}}, {{{cpp_number(b['fullResolution'][0])}, {cpp_number(b['fullResolution'][1])}}}, {scalar_text}}};\n")
        for label, values in (("Input", case["input"]["f32_words_le"]), ("Expected", case["expected"]["f32_words_le"])):
            out.append(f"inline constexpr std::array<std::uint32_t, {len(values)}> kCase{index}{label}Words{{{{\n  " + ", ".join(value + "U" for value in values) + "\n}};\n")
        values = case["expected"]["rgba8_bytes"]
        out.append(f"inline constexpr std::array<std::uint8_t, {len(values)}> kCase{index}Rgba8{{{{\n  " + ", ".join(str(value) + "U" for value in values) + "\n}};\n")
    out.append(f"struct CaseView {{ std::string_view name; std::size_t width; std::size_t height; BindingControl bindings; std::span<const std::uint32_t> input; std::span<const std::uint32_t> expected; std::span<const std::uint8_t> rgba8; }};\ninline constexpr std::array<CaseView, {len(cases)}> kCases{{{{\n")
    for index, case in enumerate(cases):
        out.append(f'  CaseView{{"{case["name"]}", {case["width"]}U, {case["height"]}U, kCase{index}Bindings, kCase{index}InputWords, kCase{index}ExpectedWords, kCase{index}Rgba8}},\n')
    out.append("}};\nstruct MutationView { std::string_view name; std::string_view group; std::size_t anchor_occurrence_count; std::size_t witness_count; bool structural_only; bool structural_probe; };\ninline constexpr std::array<MutationView, " + str(len(document["mutation_ledger"])) + "> kMutations{{\n")
    for item in document["mutation_ledger"]:
        out.append(f'  MutationView{{"{item["name"]}", "{item["group"]}", {item["anchor_occurrence_count"]}U, {len(item["required_witnesses"])}U, {str(item["structural_only"]).lower()}, {str(item.get("structural_probe", False)).lower()}}},\n')
    out.append("}};\nstruct MutationWitnessView { std::string_view mutation; std::string_view case_name; std::size_t mismatched_lanes; std::size_t mismatched_bytes; };\ninline constexpr std::array<MutationWitnessView, " + str(sum(len(item["required_witness_results"]) for item in document["mutation_ledger"])) + "> kMutationWitnesses{{\n")
    for item in document["mutation_ledger"]:
        for witness in item["required_witness_results"]:
            out.append(f'  MutationWitnessView{{"{item["name"]}", "{witness["case"]}", {witness["mismatched_lanes"]}U, {witness["mismatched_bytes"]}U}},\n')
    out.append("}};\n}\n")
    return "".join(out)


def sidecar(path: pathlib.Path) -> str:
    return (path.parent / f"{path.name}.sha256").read_text()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if sum((args.write, args.check, args.self_test)) != 1:
        raise MaterializationError("choose exactly one of --write, --check, or --self-test")
    if args.self_test:
        baseline = json.loads(ORACLE.read_text())
        checks: list[tuple[str, bool]] = []
        for label, mutate in [
            ("factory", lambda d: d["factory"].__setitem__("name", "forged")),
            ("case", lambda d: d["render_cases"][0].__setitem__("degree", 9)),
            ("binding", lambda d: d["render_cases"][0]["bindings"].__setitem__("degree", 9)),
            ("closure", lambda d: d["provenance"]["cpu_snapshot"]["import_closure"].pop()),
            ("mutation", lambda d: d["mutation_ledger"][0].__setitem__("replacement", "forged")),
            ("absolute", lambda d: d["claim_boundaries"].__setitem__("foreign", "/tmp/escape")),
        ]:
            forged = copy.deepcopy(baseline)
            mutate(forged)
            try:
                validate(forged)
            except (MaterializationError, KeyError, TypeError):
                checks.append((label, True))
            else:
                checks.append((label, False))
        for label, ok in checks:
            print(f"  [{'ok' if ok else 'FAIL'}] {label} forge rejected")
        print(f"newton native oracle materializer self-test: {sum(ok for _, ok in checks)}/{len(checks)} pass")
        return 0 if all(ok for _, ok in checks) else 1
    payload = ORACLE.read_bytes()
    if sidecar(ORACLE) != f"{hashlib.sha256(payload).hexdigest()}  {ORACLE.name}\n":
        raise MaterializationError("oracle sidecar drift")
    document = validate(json.loads(payload))
    rendered = render(document)
    if args.write:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_text(rendered)
        (TARGET.parent / f"{TARGET.name}.sha256").write_text(f"{hashlib.sha256(rendered.encode()).hexdigest()}  {TARGET.name}\n")
        materializer = pathlib.Path(__file__)
        (materializer.parent / f"{materializer.name}.sha256").write_text(f"{hashlib.sha256(materializer.read_bytes()).hexdigest()}  {materializer.name}\n")
        print(f"newton include written ({len(rendered)} bytes)")
    else:
        materializer = pathlib.Path(__file__)
        if sidecar(materializer) != f"{hashlib.sha256(materializer.read_bytes()).hexdigest()}  {materializer.name}\n":
            raise MaterializationError("materializer sidecar drift")
        if not TARGET.is_file() or TARGET.read_text() != rendered:
            raise MaterializationError("generated include drift")
        print("newton materializer: ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MaterializationError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
