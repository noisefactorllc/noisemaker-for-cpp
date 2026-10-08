"""Exact source and binding contract for the CPU mesh whole-pass route."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
KEY = "render/meshRender:render"
FACTORY = "noisemaker::effects::render_triangles"
NATIVE_SOURCE = "src/effects/mesh_render.cpp"
HEADER = "include/noisemaker/effects/mesh_render_contract.hpp"
CPU_SOURCE = "src/effects/cpu/mesh-render.js"
CPU_SHA256 = "4fa90cc2681e51dce259e79bf807fb352868cc5e31823a313c818b7c1deeb051"
REVISION = "5976b7a6b77f69c47c41f4ee296a54d5318e1f9d"
UPSTREAM = {
    "definition.js": "4ab85873f6851d0d212e6ed71ff8335430ea69310d62924e32e02dd29e045e6f",
    "glsl/render.vert": "a4baf8432c78f411ba28782c3f1276aa08c7448a4e748ce864a1c9178d34ddb9",
    "glsl/render.frag": "b39386c2cb0877e2381fd04c8fc9cb6e51f7126801f91faac11fb75e54d6c873",
}
EFFECT_SHA256 = "ab6f3870f5fc044569f1690adec951b9b840102e96f8063461bd9ec83cf5973d"
PASS_UNIFORM_ORDER = (
    "meshScale", "meshOffsetX", "meshOffsetY", "meshOffsetZ", "rotateX", "rotateY", "rotateZ",
    "viewScale", "posX", "posY", "lightDirection", "diffuseColor", "diffuseIntensity",
    "specularColor", "specularIntensity", "shininess", "ambientColor", "rimIntensity",
    "rimPower", "meshColor", "wireframe")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def authenticate_fragment(raw: bytes, effect: dict) -> None:
    if digest(raw) != UPSTREAM["glsl/render.frag"] or len(raw) != 2047:
        raise ValueError("mesh whole-pass fragment source drift")
    if digest(canonical(effect)) != EFFECT_SHA256:
        raise ValueError("mesh whole-pass effect contract drift")


def authenticate_authority(cpu_root: pathlib.Path, shader_git: pathlib.Path) -> None:
    source = cpu_root / CPU_SOURCE
    if source.is_symlink() or digest(source.read_bytes()) != CPU_SHA256:
        raise ValueError("mesh CPU adapter source drift")
    for name, expected in UPSTREAM.items():
        raw = subprocess.check_output([
            "git", "-C", str(shader_git), "show",
            f"{REVISION}:shaders/effects/render/meshRender/{name}"])
        if digest(raw) != expected:
            raise ValueError(f"mesh upstream geometry source drift: {name}")


def compatibility_row(repository: pathlib.Path = ROOT) -> dict:
    from tools.glslcpp import check_corpus
    root = check_corpus._corpus_root(repository)
    effect = json.loads((root / "metadata.json").read_text())["effects"]["render/meshRender"]
    source = root / "sources/render/meshRender/render.frag"
    if not source.exists():
        source = root / "pending-sources/render/meshRender/render.frag"
    authenticate_fragment(source.read_bytes(), effect)
    native = repository / NATIVE_SOURCE
    if native.is_symlink() or not native.is_file():
        raise ValueError("mesh native adapter source missing")
    current_pass = effect["passes"][1]
    aliases = {value.get("uniform", name): name for name, value in effect["params"].items()}
    uniforms = []
    for name, mapped in sorted(current_pass["uniforms"].items()):
        parameter = aliases.get(mapped, mapped)
        vector = effect["params"][parameter]["type"] in {"color", "vec3"}
        uniforms.append({"name": name, "type": "vec3" if vector else "float",
                         "cpp_type": "glsl::DVec3" if vector else "double",
                         "source": "effect_parameter", "source_name": parameter})
    uniforms.append({"name": "fullResolution", "type": "vec2", "cpp_type": "glsl::DVec2",
                     "source": "reserved_runtime_state", "source_name": "fullResolution"})
    samplers = [{"name": name, "type": "sampler2D", "cpp_type": "const Surface&",
                 "source": "resource", "resource": target}
                for name, target in sorted(current_pass["inputs"].items())]
    contract = {"cpu_adapter_sha256": CPU_SHA256,
                "vertex_sha256": UPSTREAM["glsl/render.vert"],
                "fragment_sha256": UPSTREAM["glsl/render.frag"],
                "definition_sha256": UPSTREAM["definition.js"],
                "effect_projection_sha256": EFFECT_SHA256,
                "external_input": "meshData", "destination_mutation": "preserve_uncovered",
                "depth": "per_pass_less_clear_one", "count": "input"}
    output_abi = {"cardinality": 1, "canonical_slots": [0], "extent": {
        "width": "screen", "height": "screen", "format": "rgba16f"},
        "logical_routes": ["outputTex"], "physical_names": ["fragColor"],
        "single_output_canonical": True}
    abi_hash = digest(canonical({"uniforms": uniforms, "samplers": samplers,
                                 "output_abi": output_abi, "contract": contract}))
    return {
        "row_kind": "canonical", "effect_id": "render/meshRender", "program": "render",
        "program_key": KEY, "status": "compatible", "reasons": [],
        "source": "sources/render/meshRender/render.frag",
        "old_raw_sha256": UPSTREAM["glsl/render.frag"], "new_raw_sha256": UPSTREAM["glsl/render.frag"],
        "old_raw_bytes": 2047, "new_raw_bytes": 2047, "source_classification": "raw_exact",
        # Shared admission field: typed binding ABI, with no emitted GLSL/IR claim.
        "typed_abi_sha256": abi_hash, "whole_pass_contract": contract,
        "draw_mode": "triangles", "dimensionality": "image", "capabilities": [],
        "uniforms": uniforms, "samplers": samplers,
        "outputs": [{"slot": 0, "physical_name": "fragColor", "logical_route": "outputTex", "cpp_type": "glsl::Vec4"}],
        "output_abi": output_abi,
        "factory": {"canonical": FACTORY, "emitted_factory": FACTORY,
                    "route": {"kind": "whole_pass", "factory": FACTORY,
                              "source": NATIVE_SOURCE, "source_sha256": digest(native.read_bytes())}},
        "authority_pass": {"name": "render", "inputs": {
                           name: current_pass["inputs"][name] for name in ("inputTex", "meshPositions", "meshNormals")},
                           "outputs": current_pass["outputs"], "uniforms": {
                           name: current_pass["uniforms"][name] for name in PASS_UNIFORM_ORDER},
                           "blend": False, "repeat": None},
    }


def validate_row(row: dict, repository: pathlib.Path = ROOT) -> None:
    if row != compatibility_row(repository):
        raise ValueError("mesh whole-pass route/source/ABI contract drift")


def render_header(repository: pathlib.Path = ROOT) -> bytes:
    from tools.dsl.generate_effect_catalog import _raw_pairs
    from tools.glslcpp.generate_typed_slice import _binding_abi_sections
    row = compatibility_row(repository)
    sections = _binding_abi_sections(row, [])
    fields = [KEY, FACTORY, FACTORY, "whole_pass", row["new_raw_sha256"],
              row["typed_abi_sha256"], "whole-pass", "", *sections.values()]
    return ("// Generated by tools/dsl/mesh_render_contract.py; do not edit.\n"
            "#pragma once\n#include \"noisemaker/graph/executor.hpp\"\n"
            "namespace noisemaker::effects::mesh_contract {\n"
            "inline const std::vector<std::pair<std::string, Value>>& expected_row() {\n"
            "  static const std::vector<std::pair<std::string, Value>> row = " + _raw_pairs(row) + ";\n"
            "  return row;\n}\n"
            "inline const graph::FactoryRouteDescriptor route{" +
            ", ".join(json.dumps(value) for value in fields) + ", nullptr};\n"
            "}\n").encode()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / HEADER
    expected = render_header()
    if args.check:
        if target.read_bytes() != expected:
            raise SystemExit("mesh whole-pass generated contract drift")
    else:
        target.write_bytes(expected)


if __name__ == "__main__":
    main()
