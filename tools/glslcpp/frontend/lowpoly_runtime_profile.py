"""Exact dynamic LowPoly closure proof for one relational pair and one fwidth."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "lowpoly-runtime-closure-v1"
KEY = "filter/lowPoly:lowPoly"
_RAW_BYTES = 8719
_RAW_SHA256 = "2f6a184ef4d372ebf811eaa59420bbce66fa25702e23a278557521679ce7b2f5"
_NORMALIZED_BYTES = 6693
_NORMALIZED_SHA256 = "eaf683912a89a76a13777dbd0b3a51e5e353cf8bb1da1b070e6f012f6265bb24"
_FUNCTIONS_SHA256 = "0d698938c1e8a0d3c9e47a12096e1681619e8a941b88ea032148da3d24cbcadb"
_WHOLE_SHA256 = "073686731d484f26c440c558e3772e662b39ef1b212d7e8b327b3eae0fe1f9b3"
_INTERFACE_SHA256 = "039fab56dc86203276cf157114217d117bef57432c6e5273b5af6ed30d19ac45"
_DEFINES = (("LP_BORDER", "str", "int"), ("LP_LIGHT", "str", "int"))
_LOOP_PROOF = (6, 0, 2, 25, 72, True)
_RESOURCES = (("LP_BORDER", "LP_LIGHT", "inputTex", "tileOffset", "fullResolution",
               "scale", "seed", "mode", "edgeStrength", "edgeColor", "speed",
               "time", "alpha"), ("inputTex",), ("fragColor",), True, True)
_FUNCTIONS = ((23, "hash2", "vec2", 2, 2, "40:1-47:2"),
              (24, "lowPolySite", "vec2", 4, 4, "49:1-61:2"),
              (25, "main", "void", 0, 32, "63:1-227:2"),
              (26, "pcg", "uvec3", 1, 9, "28:1-38:2"))
_RELATIONAL_PATH = (28, "s0", "s0", "s5", "s1", "s0", "s1", "s1", "e0")
_DERIVATIVE_PATH = (28, "s0", "s0", "s8", "e0", 0, 0)
_SITES = (("any", 25, _RELATIONAL_PATH, "187:21-187:68", "bool",
           "efa468eccddcb767936c572918108b013ef99b401ed2156d52bdd960df0fff2a", -4),
          ("notEqual", 25, (*_RELATIONAL_PATH, 0), "187:25-187:67", "bvec2",
           "4efb6fe12504b6c7054173d5ac16bbce5e277b16fcc444b88abd489d4740a0f1", -32),
          ("fwidth", 25, _DERIVATIVE_PATH, "201:35-201:53", "float",
           "0cb31f8db4f67affe524feadf7c9f5353116ec003c35c87de52db4420cf9dece", -19))


@dataclass(frozen=True, slots=True)
class LowPolyRuntimeProof:
    reductions: tuple[TypedExpression, ...]
    relationals: tuple[TypedExpression, ...]
    derivatives: tuple[TypedExpression, ...]

    @property
    def nodes(self) -> tuple[TypedExpression, ...]:
        return self.derivatives


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = value.span
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _walk_expression(value: TypedExpression, path: tuple[object, ...]):
    yield value, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, (*path, index))


def _walk_statement(value: TypedStatement, path: tuple[object, ...]):
    for index, expression in enumerate(value.expressions):
        yield from _walk_expression(expression, (*path, f"e{index}"))
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"))


def authenticate_lowpoly_runtime(program: TypedProgram, source_hash: str | None,
                                 profile: str | None) -> LowPolyRuntimeProof:
    if profile != PROFILE or program.key != KEY or source_hash != _RAW_SHA256:
        raise ValueError(f"{PROFILE}: profile, key, or source hash mismatch")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    whole = _sha((program.key, program.source, program.raw_source,
                  program.declarations, program.functions, program.resources,
                  program.body_status, program.local_type_names, program.structs,
                  program.uniform_blocks, program.interface_symbols,
                  program.builtin_symbols, program.counted_loop_proof,
                  program.preprocessor_defines))
    interface = _sha((program.declarations, program.resources,
                      program.local_type_names, program.structs,
                      program.uniform_blocks, program.interface_symbols,
                      program.builtin_symbols, program.preprocessor_defines))
    if (len(raw) != _RAW_BYTES or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or defines != _DEFINES or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or whole != _WHOLE_SHA256 or interface != _INTERFACE_SHA256):
        raise ValueError(f"{PROFILE}: source, define, or typed tree mismatch")
    loop = program.counted_loop_proof
    if loop is None or (loop.loop_count, loop.unproved_loop_count,
                        loop.max_effective_depth, loop.max_lexical_product,
                        loop.entrypoint_charge, loop.call_graph_acyclic) != _LOOP_PROOF:
        raise ValueError(f"{PROFILE}: counted-loop proof mismatch")
    resources = program.resources
    if (resources.uniforms, resources.samplers, resources.outputs,
            resources.uses_texture, resources.uses_derivatives) != _RESOURCES:
        raise ValueError(f"{PROFILE}: resource signature mismatch")
    functions = tuple((fn.id, fn.name, fn.return_type.display(),
                       len(fn.parameters), len(fn.body), _span(fn))
                      for fn in sorted(program.functions, key=lambda item: item.id))
    if functions != _FUNCTIONS:
        raise ValueError(f"{PROFILE}: function inventory mismatch")
    found = []
    bvec = []
    for fn in program.functions:
        for index, statement in enumerate(fn.body):
            for node, path in _walk_statement(statement, (index,)):
                if node.type is not None and node.type.display().startswith("bvec"):
                    bvec.append(node)
                if node.kind == "builtin" and node.callee in {"any", "notEqual", "fwidth"}:
                    found.append((fn.id, node, path))
    actual = tuple((node.callee, owner, path, _span(node), node.type.display(),
                    _sha(node), node.signature_id) for owner, node, path in found)
    if actual != _SITES:
        raise ValueError(f"{PROFILE}: relational or derivative site mismatch")
    reduction, relational, derivative = (item[1] for item in found)
    if (len(bvec) != 1 or bvec[0] is not relational or
            len(reduction.children) != 1 or reduction.children[0] is not relational or
            relational.type.display() != "bvec2" or
            tuple(child.type.display() for child in relational.children)
            != ("ivec2", "ivec2") or
            len(derivative.children) != 1 or
            derivative.children[0].type.display() != "float"):
        raise ValueError(f"{PROFILE}: closure shape mismatch")
    return LowPolyRuntimeProof((reduction,), (relational,), (derivative,))
