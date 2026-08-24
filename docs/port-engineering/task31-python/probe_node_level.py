import hashlib
import pathlib
import sys
from unittest import mock

sys.path.insert(0, ".")
REPOSITORY = pathlib.Path(".")

from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend import curl_vector_math_profile as profile
from tools.glslcpp.frontend.semantic import analyze_program

source = (REPOSITORY / "tools/glslcpp/corpus/"
          "a024dc3a960cc44af454abc7aebce50456c194e6/"
          "sources/synth/curl/curl.glsl").read_text()
source_hash = hashlib.sha256(source.encode()).hexdigest()


def exact_program():
    return analyze_program(parse_program(
        source, profile.CURL_KEY, {"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True}),
        profile.CURL_KEY)


def walk_expression(value):
    yield value
    for child in value.children:
        yield from walk_expression(child)


def walk_statement(statement):
    yield statement
    for child in statement.children:
        yield from walk_statement(child)


def function_by_id(program, fid):
    return next(f for f in program.functions if f.id == fid)


def sites_in_function(function, callee):
    result = []
    for statement in function.body:
        for owner in walk_statement(statement):
            for expression in owner.expressions:
                for node in walk_expression(expression):
                    if node.kind == "builtin" and node.callee == callee:
                        result.append(node)
    return result


def rename_tanh(program):
    node = sites_in_function(function_by_id(program, 18), "tanh")[0]
    object.__setattr__(node, "callee", "sin")


def rename_mod_v4(program):
    node = sites_in_function(function_by_id(program, 20), "mod")[0]
    object.__setattr__(node, "callee", "min")


def orphan_tanh_child(program):
    node = sites_in_function(function_by_id(program, 18), "tanh")[0]
    object.__setattr__(node, "children", ())


def widen_mod_simplex_arity(program):
    node = sites_in_function(function_by_id(program, 21), "mod")[0]
    object.__setattr__(node, "children", (*node.children, node.children[0]))


def retype_mod_dead_argument(program):
    node = sites_in_function(function_by_id(program, 19), "mod")[0]
    from tools.glslcpp.frontend.semantic_types import vector
    object.__setattr__(node.children[0], "type", vector("float", 2))


def collide_simplex_function_id(program):
    function = function_by_id(program, 21)
    object.__setattr__(function.signature, "id", 20)


COARSE = ("source, define, function, whole-program, or interface mismatch")

cases = (
    ("tanh -> sin", rename_tanh, "closure site cardinality mismatch"),
    ("mod(vec4) -> min", rename_mod_v4, "closure site cardinality mismatch"),
    ("tanh loses its only child", orphan_tanh_child, "closure node identity mismatch"),
    ("mod(simplex3D) gains a third argument", widen_mod_simplex_arity,
     "closure node identity mismatch"),
    ("mod(dead) vec3 argument retyped to vec2", retype_mod_dead_argument,
     "closure node identity mismatch"),
    ("simplex3D function id collides with permute(vec4)",
     collide_simplex_function_id, "function inventory mismatch"),
)

baseline_functions = profile._sha(exact_program().functions)

for label, mutate, expected in cases:
    candidate = exact_program()
    mutate(candidate)
    assert baseline_functions != profile._sha(candidate.functions), label

    normalized = candidate.source.encode("utf-8")
    loop_proof = candidate.counted_loop_proof
    with mock.patch.multiple(
            profile,
            _FUNCTIONS_SHA256=profile._sha(candidate.functions),
            _WHOLE_SHA256=profile._whole(candidate),
            _INTERFACE_SHA256=profile._interface(candidate),
            _NORMALIZED_SHA256=hashlib.sha256(normalized).hexdigest(),
            _NORMALIZED_BYTES=len(normalized),
            _LOOP_PROOF=(loop_proof.loop_count, loop_proof.unproved_loop_count,
                         loop_proof.max_effective_depth,
                         loop_proof.max_lexical_product,
                         loop_proof.entrypoint_charge,
                         loop_proof.call_graph_acyclic)):
        try:
            profile.authenticate_curl_vector_math(candidate, source_hash, profile.PROFILE)
            message = None
        except ValueError as error:
            message = str(error)
    print(label, "->", message)
    assert message is not None, label
    assert COARSE not in message, (label, message)
    assert expected in message, (label, message, expected)

exact = exact_program()
profile.authenticate_curl_vector_math(exact, source_hash, profile.PROFILE)
print("restore OK")
