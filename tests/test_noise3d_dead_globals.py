"""Exact-source admission for the unused Noise3D rhash globals."""

import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION
from tools.glslcpp import corpus_ratchet
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.dynamic_define_hoist import transform_source


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / f"tools/glslcpp/corpus/{CORPUS_REVISION}"
KEY = "classicNoisedeck/noise3d:noise3d"


def source_bytes():
    for filename, field in (("pending.json", "pending"), ("manifest.json", "programs")):
        document = json.loads((CORPUS / filename).read_text())
        row = next((entry for entry in document[field] if entry["program_key"] == KEY), None)
        if row is not None:
            return (CORPUS / row["source"]).read_bytes()
    raise AssertionError("Noise3D source is absent")


def test_noise3d_completes_the_existing_admission_probe():
    raw = source_bytes()
    pending = json.loads((CORPUS / "pending.json").read_text())
    metadata = json.loads((CORPUS / "metadata.json").read_text())
    effect = (pending["effects"].get(KEY.split(":")[0])
              or metadata["effects"][KEY.split(":")[0]])
    assert corpus_ratchet.probe_program(KEY, raw, effect) is None


def test_noise3d_dead_globals_are_exact_and_unreachable():
    from tools.glslcpp.frontend.noise3d_dead_globals import authenticate_noise3d_dead_globals

    raw = source_bytes()
    typed = analyze_program(parse_program(raw.decode(), KEY, {"NOISE_TYPE": 12}), KEY)
    digest = hashlib.sha256(raw).hexdigest()
    proof = authenticate_noise3d_dead_globals(typed, digest)
    assert tuple(item.symbol.name for item in proof.globals) == ("myt", "mys")
    assert "rhash" in {item.name for item in proof.dead_functions}
    assert "spheres" in {item.name for item in proof.dead_functions}
    assert "cubes" in {item.name for item in proof.dead_functions}
    assert authenticate_noise3d_dead_globals(dataclasses.replace(typed, key="foreign:noise3d"), digest) is None

    for candidate, candidate_digest in (
        (typed, "0" * 64),
        (dataclasses.replace(typed, raw_source=typed.raw_source + "\n"), digest),
        (dataclasses.replace(typed, declarations=typed.declarations[:-1]), digest),
        (dataclasses.replace(typed, functions=tuple(
            function for function in typed.functions if function.name != "rhash")), digest),
        (analyze_program(parse_program(raw.decode(), KEY, {"NOISE_TYPE": 20}), KEY), digest),
    ):
        with pytest.raises(ValueError, match="Noise3D"):
            authenticate_noise3d_dead_globals(candidate, candidate_digest)


def test_noise3d_repin_does_not_hide_new_rhash_call(monkeypatch):
    from tools.glslcpp.frontend import noise3d_dead_globals as profile

    source = source_bytes().decode()
    assert source.count("void main() {") == 1
    changed = source.replace("void main() {",
                             "void main() {\n    vec2 deadUse = rhash(vec2(0.0));")
    typed = analyze_program(parse_program(changed, KEY, {"NOISE_TYPE": 12}), KEY)
    digest = hashlib.sha256(changed.encode()).hexdigest()
    original_digest = hashlib.sha256(source.encode()).hexdigest()
    selected = dict(profile._SOURCE_VARIANTS[original_digest])
    selected.update(normalized_sha256=hashlib.sha256(typed.source.encode()).hexdigest(),
                    whole_sha256=profile._whole(typed))
    monkeypatch.setitem(profile._SOURCE_VARIANTS, digest, selected)
    with pytest.raises(ValueError, match="Noise3D dead function graph mismatch"):
        profile.authenticate_noise3d_dead_globals(typed, digest)


def test_noise3d_dynamic_tree_keeps_all_source_branches():
    from tools.glslcpp.frontend.noise3d_dead_globals import authenticate_noise3d_dead_globals

    raw = source_bytes()
    source = raw.decode()
    parsed = parse_program(transform_source(source, KEY), KEY, {"NOISE_TYPE": "int"})
    parsed["raw_source"] = source
    typed = analyze_program(parsed, KEY)
    proof = authenticate_noise3d_dead_globals(typed, hashlib.sha256(raw).hexdigest())
    assert {item.name for item in proof.dead_functions} == {
        "random", "rgb2hsv", "rhash", "rotate2D", "smax", "smin"}
    assert {item.name for item in typed.functions} >= {
        "cellular", "voronoi3d", "sine3D", "spheres", "cubes"}
    assert tuple((item.span.start_line, item.type.display()) for item in proof.rounds) == (
        (445, "vec3"), (433, "vec3"))
    assert proof.max_effective_depth == 4
    assert proof.max_entrypoint_charge == 4156
    assert tuple(item.symbol.name for item in proof.value_copies) == ("q",)
    assert tuple(item.symbol.name for item in proof.cellular_distances) == (
        "d11", "d12", "d13", "d21", "d22", "d23", "d31", "d32", "d33")
    assert tuple(item.symbol.name for item in proof.cellular_oy) == (
        "oy11", "oy12", "oy13", "oy21", "oy22", "oy23", "oy31", "oy32", "oy33")

    changed = dataclasses.replace(typed, preprocessor_defines=())
    with pytest.raises(ValueError, match="Noise3D"):
        authenticate_noise3d_dead_globals(changed, hashlib.sha256(raw).hexdigest())
