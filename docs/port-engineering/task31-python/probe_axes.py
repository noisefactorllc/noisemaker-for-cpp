import dataclasses
import hashlib
import pathlib
import sys

sys.path.insert(0, ".")

REPOSITORY = pathlib.Path(".")

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.curl_vector_math_profile import (
    CURL_KEY, PROFILE, authenticate_curl_vector_math)
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.semantic_types import FLOAT, vector
from tools.glslcpp.frontend.typed_ir import PreprocessorDefine

source = (REPOSITORY / "tools/glslcpp/corpus/"
          "a024dc3a960cc44af454abc7aebce50456c194e6/"
          "sources/synth/curl/curl.glsl").read_text()
source_hash = hashlib.sha256(source.encode()).hexdigest()
exact = analyze_program(parse_program(
    source, CURL_KEY, {"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True}), CURL_KEY)


def at(value, path):
    for part in path:
        value = value[part] if isinstance(part, int) else getattr(value, part)
    return value


def replaced(value, path, replacement):
    if len(path) == 1:
        part = path[0]
        if isinstance(part, int):
            items = list(value); items[part] = replacement
            return tuple(items)
        return dataclasses.replace(value, **{part: replacement})
    part = path[0]
    child = value[part] if isinstance(part, int) else getattr(value, part)
    updated = replaced(child, path[1:], replacement)
    if isinstance(part, int):
        items = list(value); items[part] = updated
        return tuple(items)
    return dataclasses.replace(value, **{part: updated})


tanh_path = ("functions", 2, "body", 6, "expressions", 0, "children", 1, "children", 0, "children", 0)
mod_dead_path = ("functions", 3, "body", 0, "expressions", 0)
mod_v4_path = ("functions", 4, "body", 0, "expressions", 0)
mod_simplex_path = ("functions", 5, "body", 12, "expressions", 0, "children", 1)

tanh_node = at(exact, tanh_path)
mod_dead_node = at(exact, mod_dead_path)
mod_v4_node = at(exact, mod_v4_path)
mod_simplex_node = at(exact, mod_simplex_path)

print("tanh", tanh_node.callee, tanh_node.type.display(), len(tanh_node.children))
print("mod_dead", mod_dead_node.callee, mod_dead_node.type.display(), len(mod_dead_node.children),
      tuple(c.type.display() for c in mod_dead_node.children))
print("mod_v4", mod_v4_node.callee, mod_v4_node.type.display(), len(mod_v4_node.children),
      tuple(c.type.display() for c in mod_v4_node.children))
print("mod_simplex", mod_simplex_node.callee, mod_simplex_node.type.display(), len(mod_simplex_node.children),
      tuple(c.type.display() for c in mod_simplex_node.children))

axes = {
    "program-key": (("key",), "synth/curl:foreign"),
    "normalized-source": (("source",), exact.source + " "),
    "raw-source": (("raw_source",), exact.raw_source + " "),
    "body-status": (("body_status",), "task31-mutated"),
    "define-name": (("preprocessor_defines",),
                    (PreprocessorDefine("TASK31", "int", "1"),
                     PreprocessorDefine("OUTPUT_MODE", "int", "3"),
                     PreprocessorDefine("RIDGES", "bool", "true"))),
    "define-order": (("preprocessor_defines",), tuple(reversed(exact.preprocessor_defines))),
    "struct-presence": (("structs",), (object(),)),
    "uniform-block-presence": (("uniform_blocks",), (object(),)),
    "loop-count": (("counted_loop_proof", "loop_count"), 2),
    "loop-unproved-count": (("counted_loop_proof", "unproved_loop_count"), 1),
    "loop-depth": (("counted_loop_proof", "max_effective_depth"), 2),
    "loop-product": (("counted_loop_proof", "max_lexical_product"), 4),
    "loop-charge": (("counted_loop_proof", "entrypoint_charge"), 13),
    "call-graph-cycle": (("counted_loop_proof", "call_graph_acyclic"), False),
    "resource-uniform-order": (("resources", "uniforms"), tuple(reversed(exact.resources.uniforms))),
    "resource-uniform-count": (("resources", "uniforms"), exact.resources.uniforms[:-1]),
    "resource-sampler-count": (("resources", "samplers"), (object(),)),
    "resource-output": (("resources", "outputs", 0), "otherColor"),
    "resource-texture": (("resources", "uses_texture"), True),
    "resource-derivative": (("resources", "uses_derivatives"), True),
    "function-count": (("functions",), exact.functions[:-1]),
    "function-order": (("functions",), tuple(reversed(exact.functions))),
    "tanh-span": (tanh_path + ("span", "start_column"), 99),
    "tanh-callee": (tanh_path + ("callee",), "sin"),
    "tanh-type": (tanh_path + ("type",), vector("float", 4)),
    "tanh-children-count": (tanh_path + ("children",), ()),
    "mod-dead-span": (mod_dead_path + ("span", "start_column"), 99),
    "mod-dead-callee": (mod_dead_path + ("callee",), "min"),
    "mod-dead-type": (mod_dead_path + ("type",), vector("float", 4)),
    "mod-dead-children-order": (mod_dead_path + ("children",),
                                tuple(reversed(mod_dead_node.children))),
    "mod-dead-children-count": (mod_dead_path + ("children",), mod_dead_node.children[:1]),
    "mod-v4-span": (mod_v4_path + ("span", "start_column"), 99),
    "mod-v4-callee": (mod_v4_path + ("callee",), "max"),
    "mod-v4-type": (mod_v4_path + ("type",), vector("float", 3)),
    "mod-v4-children-order": (mod_v4_path + ("children",), tuple(reversed(mod_v4_node.children))),
    "mod-v4-children-count": (mod_v4_path + ("children",), mod_v4_node.children[:1]),
    "mod-simplex-span": (mod_simplex_path + ("span", "start_column"), 99),
    "mod-simplex-callee": (mod_simplex_path + ("callee",), "clamp"),
    "mod-simplex-type": (mod_simplex_path + ("type",), vector("float", 4)),
    "mod-simplex-children-order": (mod_simplex_path + ("children",),
                                   tuple(reversed(mod_simplex_node.children))),
    "mod-simplex-children-count": (mod_simplex_path + ("children",), mod_simplex_node.children[:1]),
}

candidates = {name: replaced(exact, path, value) for name, (path, value) in axes.items()}
print("axes", len(axes), "candidates", len(candidates))
print("names-hash",
      hashlib.sha256(("\n".join(sorted(candidates)) + "\n").encode()).hexdigest())

errors = []
for name, candidate in candidates.items():
    if exact == candidate:
        errors.append((name, "no-op"))
        continue
    try:
        authenticate_curl_vector_math(candidate, source_hash, PROFILE)
        errors.append((name, "profile-accepted"))
    except ValueError:
        pass
    try:
        generate_typed_slice.validate_capabilities(
            candidate, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash, curl_vector_math_profile=PROFILE)
        errors.append((name, "validator-accepted"))
    except generate_typed_slice.GeneratorError:
        pass
    try:
        render_typed_cpp(candidate, candidate.key, source_hash,
                         curl_vector_math_profile=PROFILE)
        errors.append((name, "emitter-accepted"))
    except TypedEmissionError:
        pass

print("ERRORS", errors)
