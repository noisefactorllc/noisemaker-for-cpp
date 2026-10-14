"""Exact two-node signed-shift admission for Glyph Map.

The global operator vocabulary is deliberately unchanged.  This profile
authenticates the complete frozen program and returns only its candidate-owned
scalar shift and literal-one mask nodes for independent validator/emitter
consumption.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "glyph-map-nonnegative-int-shift-v1"
GLYPH_MAP_KEY = "filter/glyphMap:glyphMap"
_RAW_BYTES = 7899
_RAW_SHA256 = "35804656234712aab4ee62aad97399d287e3d2d2d566a00afe8630272a333abe"
_NORMALIZED_BYTES = 4935
_NORMALIZED_SHA256 = "c46ada7dc9029ea2c487f595930e0d123708d78b3f7e86ec29161e5127094459"
_FUNCTIONS_SHA256 = "72c3b35331ca9fdfadb2bd879cdc6b2bfd26a6aade40bc17c5115dec59ae70c6"
_WHOLE_SHA256 = "c81dc479b2d6895f919e244baddcc7e15e64d8356dd28411a593da8a68686cb2"
_INTERFACE_SHA256 = "62261e20f7bfb07a047be5ab94309602c4945c64f596bd8502b7d2cb4f3a57a9"
_ORIGIN_RAW_BYTES = 8145
_ORIGIN_RAW_SHA256 = "dc0af9a6a6fb4d0cd62ea25c4508a714a36a1dc66923f5578d91ac190d9f4dd6"
_ORIGIN_NORMALIZED_BYTES = 4967
_ORIGIN_NORMALIZED_SHA256 = "1e0aa0b503cb7fd14b614a78ef475746f2105493ad787bfbdeff8883ce00e18f"
_ORIGIN_FUNCTIONS_SHA256 = "d5bc950de06944d7ed4ea48b5cc27b20172f0b0e15f4d41d145ec2fab4a9bca0"
_ORIGIN_WHOLE_SHA256 = "83db28647014ef2a91bf062634ab55864ed1af687f4d4535136961a5f4eb21eb"
_ORIGIN_INTERFACE_SHA256 = "b430c360f715e4e63260a7042b8b4df79d4f9fbef3edb614cc257cd271dc9293"
_RESOURCES = (("inputTex", "tileOffset", "fullResolution", "renderScale",
               "cellSize", "seed", "colorMode"),
              ("inputTex",), ("fragColor",), True, False)
_LOOP_PROOF = (0, 0, 0, 0, 0, True)
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)


@dataclass(frozen=True, slots=True)
class GlyphMapBitExtractionProof:
    mask: TypedExpression
    shift: TypedExpression
    bit_declaration: TypedExpression
    row_declaration: TypedExpression
    return_conversion: TypedExpression
    self_assignment: TypedExpression
    tile_any: TypedExpression | None
    tile_not_equal: TypedExpression | None
    _candidate: TypedProgram

    @property
    def sites(self) -> tuple[TypedExpression, TypedExpression]:
        return (self.mask, self.shift)

    @property
    def tile_sites(self) -> tuple[TypedExpression, ...]:
        if self.tile_any is None or self.tile_not_equal is None:
            return ()
        return (self.tile_any, self.tile_not_equal)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = getattr(value, "span")
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _walk_expression(value: TypedExpression,
                     parent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value: TypedStatement, path: tuple[object, ...] = ()):
    for index, expression in enumerate(value.expressions):
        yield from _walk_expression(expression, None, (*path, f"e{index}"))
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"))


def _walk_statements(value: TypedStatement, path: tuple[int, ...]):
    yield value, path
    for index, child in enumerate(value.children):
        yield from _walk_statements(child, (*path, index))


def _nodes(program: TypedProgram):
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path in _walk_statement(statement, (index,)):
                yield function, item, parent, path


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def authenticate_glyph_map_nonnegative_int_shift(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> GlyphMapBitExtractionProof:
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if program.key != GLYPH_MAP_KEY:
        raise _fail("profile on foreign key")
    if source_hash not in {_RAW_SHA256, _ORIGIN_RAW_SHA256}:
        raise _fail("exact caller source hash required")
    origin = source_hash == _ORIGIN_RAW_SHA256
    expected = ((_ORIGIN_RAW_BYTES, _ORIGIN_RAW_SHA256,
                 _ORIGIN_NORMALIZED_BYTES, _ORIGIN_NORMALIZED_SHA256,
                 _ORIGIN_FUNCTIONS_SHA256, _ORIGIN_WHOLE_SHA256,
                 _ORIGIN_INTERFACE_SHA256) if origin else
                (_RAW_BYTES, _RAW_SHA256, _NORMALIZED_BYTES,
                 _NORMALIZED_SHA256, _FUNCTIONS_SHA256, _WHOLE_SHA256,
                 _INTERFACE_SHA256))

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != expected[0] or hashlib.sha256(raw).hexdigest() != expected[1]
            or len(normalized) != expected[2]
            or hashlib.sha256(normalized).hexdigest() != expected[3]
            or program.preprocessor_defines != ()
            or program.body_status != "analyzed"
            or _sha(program.functions) != expected[4]
            or _whole(program) != expected[5]
            or _interface(program) != expected[6]):
        raise _fail("source, function, whole-program, or interface mismatch")
    if program.structs != () or program.uniform_blocks != () or any(
            getattr(program, field, None) is not None
            for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated structural or proof carrier is present")
    resources = program.resources
    if ((resources.uniforms, resources.samplers, resources.outputs,
         resources.uses_texture, resources.uses_derivatives) != _RESOURCES):
        raise _fail("resource signature mismatch")
    loop = program.counted_loop_proof
    if (loop is None or (loop.loop_count, loop.unproved_loop_count,
                         loop.max_effective_depth, loop.max_lexical_product,
                         loop.entrypoint_charge, loop.call_graph_acyclic)
            != _LOOP_PROOF):
        raise _fail("loop proof mismatch")

    host = next((item for item in program.functions if item.id == 15), None)
    if (len(program.functions) != 4 or host is None
            or (host.name, host.return_type.display(),
                tuple((item.id, item.name, item.type.display())
                      for item in host.parameters), len(host.body), _span(host))
            != ("glyphPixel", "float",
                ((12, "g", "int"), (13, "x", "int"), (14, "y", "int")),
                4, "190:1-289:2")):
        raise _fail("host function mismatch")
    function_names = {item.id: item.name for item in program.functions}
    graph = {}
    for function in program.functions:
        graph[function.name] = tuple(sorted({
            function_names[item.signature_id]
            for owner, item, _, _ in _nodes(program)
            if owner is function and item.kind == "call"
        }))
    if graph != {"glyphPixel": (), "hash": ("pcg",),
                 "main": ("glyphPixel", "hash"), "pcg": ()}:
        raise _fail("call graph or render reachability mismatch")

    declaration = next((item for item in program.declarations
                        if item.symbol.id == 11), None)
    reads = [(fn, item, path) for fn, item, _, path in _nodes(program)
             if item.kind == "id" and item.symbol_id == 11]
    if (declaration is None or declaration.symbol.name != "GLYPH_COUNT"
            or declaration.symbol.storage != "const"
            or declaration.type.display() != "int"
            or _span(declaration) != "186:1-186:28"
            or _sha(declaration) != "f7b49cfb78c1c72d280c1120a7040e68031899ff4b5a57710ae38e8646704386"
            or declaration.initializer.kind != "literal"
            or declaration.initializer.literal_value != 16
            or tuple((_span(item), fn.name, path) for fn, item, path in reads)
            != ((("322:43-322:54" if origin else "319:43-319:54"),
                 "main", (17, "e0", 0, 0, 0, 1, 0)),
                (("323:35-323:46" if origin else "320:35-320:46"),
                 "main", (18, "e0", 1, 2, 0)),
                (("328:52-328:63" if origin else "325:52-325:63"),
                 "main", (21, "e0", 1, 1, 0)))):
        raise _fail("global constant or read closure mismatch")

    scalar_sites = [(fn, item, parent, path)
                    for fn, item, parent, path in _nodes(program)
                    if item.kind == "binary" and item.operator in {"&", ">>"}
                    and item.type.display() == "int"]
    if len(scalar_sites) != 2:
        raise _fail("scalar bit-operation census mismatch")
    mask_row = next((item for item in scalar_sites if item[1].operator == "&"), None)
    shift_row = next((item for item in scalar_sites if item[1].operator == ">>"), None)
    if mask_row is None or shift_row is None:
        raise _fail("scalar bit-operation identities missing")
    mask, shift = mask_row[1], shift_row[1]
    if (mask_row[0] is not host or shift_row[0] is not host
            or mask_row[3] != (2, "e0", 0)
            or shift_row[3] != (2, "e0", 0, 0)
            or _span(mask) != "287:16-287:35"
            or _sha(mask) != "13b7e8039e75aa419da56f7ef88177d338c517f59c50bde9497165b098fdbb33"
            or _span(shift) != "287:16-287:30"
            or _sha(shift) != "532c26faeec29026185a9557f1173553d28752a77964835374dd94a4a476831b"
            or mask.children[0] is not shift
            or mask.children[1].kind != "literal"
            or mask.children[1].literal_value != 1
            or tuple(child.type.display() for child in mask.children)
            != ("int", "int")
            or tuple(child.type.display() for child in shift.children)
            != ("int", "int")
            or shift.children[0].kind != "id"
            or shift.children[0].symbol_id != 20
            or shift.children[1].kind != "binary"
            or shift.children[1].operator != "-"
            or _sha(shift.children[1])
            != "e0e9f7b40384f96ff80bcb109c300ebfb004584ef90d328194f0c4804a6e2882"):
        raise _fail("shift or mask closure mismatch")

    declarations = [item for _, item, _, _ in _nodes(program)
                    if item.kind == "declaration"]
    row_declaration = next((item for item in declarations
                            if item.symbol_id == 20), None)
    bit_declaration = next((item for item in declarations
                            if item.symbol_id == 21), None)
    assignments = [item for _, item, _, _ in _nodes(program)
                   if item.kind == "assign" and item.operator == "="
                   and len(item.children) == 2
                   and item.children[0].symbol_id == 20]
    if (row_declaration is None or _span(row_declaration) != "194:9-194:16"
            or _sha(row_declaration)
            != "2608c7b93985fb65352f962d15fd69200139f3a3b17d809f711114f5553b8383"
            or row_declaration.children[0].literal_value != 0
            or bit_declaration is None
            or _sha(bit_declaration)
            != "9a881f6291c544b8f7f3f461b11b28285ae0f9b765d8631f442f818f69e2201b"
            or bit_declaration.children[0] is not mask
            or len(assignments) != 40
            or _sha(tuple(assignments))
            != "05f32dbdd73f16e5a283dfde9535ac3469923bb9d6c6422a1f884f151b486455"
            or tuple(sorted({item.children[1].literal_value
                             for item in assignments}))
            != (4, 9, 10, 11, 14, 16, 17, 19, 21, 22, 23, 25, 26, 27, 31)):
        raise _fail("row range or bit materialization mismatch")
    branch_rows = []
    for index, statement in enumerate(host.body):
        for nested, path in _walk_statements(statement, (index,)):
            expression = nested.expressions[0] if nested.expressions else None
            is_row_write = (expression is not None
                            and expression.kind == "assign"
                            and len(expression.children) == 2
                            and expression.children[0].symbol_id == 20)
            if nested.kind == "return" or is_row_write:
                branch_rows.append((
                    nested.kind, path, _span(nested),
                    expression.children[1].literal_value
                    if is_row_write else None))
    if (tuple((item.kind, _span(item)) for item in host.body)
            != (("decl", "194:5-194:17"), ("if", "196:5-284:6"),
                ("decl", "287:5-287:36"), ("return", "288:5-288:23"))
            or len(branch_rows) != 57
            or sum(row[0] == "return" for row in branch_rows) != 17
            or any(int(row[2].split(":", 1)[0]) >= 287
                   for row in branch_rows[:-1] if row[0] == "return")
            or branch_rows[-1] != ("return", (3,), "288:5-288:23", None)
            or _sha(tuple(branch_rows))
            != "a0efdee4115efff741ac75fca4f9395893506fc0669d5272c906e8ff8b248dbc"):
        raise _fail("return-before-shift or row range control-flow mismatch")

    clamps = [item for _, item, _, _ in _nodes(program)
              if item.kind == "builtin" and item.callee == "clamp"
              and len(item.children) == 3 and item.children[0].symbol_id == 31]
    calls = [item for _, item, _, _ in _nodes(program)
             if item.kind == "call" and item.signature_id == 15]
    returns = [item for _, item, _, _ in _nodes(program)
               if item.kind == "construct" and item.type.display() == "float"
               and len(item.children) == 1 and item.children[0].symbol_id == 21]
    if (len(clamps) != 1 or _span(clamps[0]) != (
            "313:10-313:25" if origin else "310:10-310:25")
            or _sha(clamps[0])
            != ("742fb5ac014f8a3578571fcc55ad6005faf0c3d396bae9d762f64d44e40b0ba8"
                if origin else "7ed9d9762fd62ed2016ff6172b989db7bb4c3ec6398aa8ada04bb5b5188f0768")
            or tuple(child.literal_value for child in clamps[0].children[1:])
            != (0, 4)
            or len(calls) != 1 or _span(calls[0]) != (
                "334:22-334:50" if origin else "331:22-331:50")
            or _sha(calls[0])
            != ("989e0a0f53ec1b2570f46857af888dde97a7fce9aa85c7629d48268a783cb948"
                if origin else "9b9a03f748e9a188de2f713fe3931c6a5fbd1cad260d489a53815f8cdacc76e1")
            or tuple(child.symbol_id for child in calls[0].children)
            != (37, 31, 32)
            or len(returns) != 1 or _span(returns[0]) != "288:12-288:22"
            or _sha(returns[0])
            != "9a729fd6e0b5e130b90ed981a2d5c1e0b9f9f7346cefec23f51640c0075e987a"):
        raise _fail("clamp, call, or return closure mismatch")
    self_assignments = [item for _, item, _, _ in _nodes(program)
                        if item.kind == "assign" and item.operator == "="
                        and len(item.children) == 2
                        and item.children[0].kind == "id"
                        and item.children[1].kind == "id"
                        and item.children[0].symbol_id
                        == item.children[1].symbol_id]
    if (len(self_assignments) != 1
            or _span(self_assignments[0]) != (
                "329:9-329:28" if origin else "326:9-326:28")
            or _sha(self_assignments[0])
            != ("36950d71ead367d7859ea8f601438980c308e69806c1795d4bde4bfd5ea07125"
                if origin else "2281426a7ceef36d6583a8179b39bfea27e1836c1fe7fdd9af25fa2aec1d8b23")
            or self_assignments[0].children[0].symbol_id != 37):
        raise _fail("canonical self-assignment no-op mismatch")

    tile_any = None
    tile_not_equal = None
    tile_nodes = [(fn, item, parent, path) for fn, item, parent, path in _nodes(program)
                  if item.kind == "builtin" and item.callee in {"any", "notEqual"}]
    if origin:
        main = next((fn for fn in program.functions if fn.id == 17 and fn.name == "main"), None)
        if main is None or len(main.body) != 24 or len(tile_nodes) != 2:
            raise _fail("origin tile closure census mismatch")
        tile_declaration = main.body[4].expressions[0]
        tile_any = tile_declaration.children[0]
        tile_not_equal = tile_any.children[0]
        if (tile_nodes != [(main, tile_any, tile_declaration, (4, "e0", 0)),
                           (main, tile_not_equal, tile_any, (4, "e0", 0, 0))]
                or tile_declaration.kind != "declaration"
                or tile_declaration.symbol_id != 27
                or tile_declaration.symbol is None
                or tile_declaration.symbol.name != "isTileRendering"
                or _span(tile_declaration) != "303:10-303:69"
                or _sha(tile_declaration)
                != "4988b881c3a469fd961d378ebdb0a0e9718b1044d2eb3eedf25108417ccac716"
                or tile_any.kind != "builtin" or tile_any.callee != "any"
                or tile_any.signature_id != -4 or tile_any.type.display() != "bool"
                or _span(tile_any) != "303:28-303:69"
                or _sha(tile_any) != "87af8bebf7e24bd9a4f4abe2c564a5b3195ffe229089b1dbc158f242cc3e4ca7"
                or tile_not_equal.kind != "builtin" or tile_not_equal.callee != "notEqual"
                or tile_not_equal.signature_id != -32
                or tile_not_equal.type.display() != "bvec2"
                or _span(tile_not_equal) != "303:32-303:68"
                or _sha(tile_not_equal)
                != "343d66243750b2206a851cfbd77bb90e338ba8e509dfb0ada3aafb4981d4e435"
                or tuple(child.symbol_id for child in tile_not_equal.children) != (3, 24)
                or tuple(child.type.display() for child in tile_not_equal.children)
                != ("vec2", "vec2")):
            raise _fail("origin tile any/notEqual source tree mismatch")
    elif tile_nodes:
        raise _fail("historical source gained a relational closure")

    return GlyphMapBitExtractionProof(
        mask, shift, bit_declaration, row_declaration, returns[0],
        self_assignments[0], tile_any, tile_not_equal, program)



def authenticated_glyph_map_tile_sites(
        proof: object, program: TypedProgram,
        source_hash: str | None) -> tuple[TypedExpression, ...]:
    sites = getattr(proof, "tile_sites", None)
    if sites is not None:
        return sites
    # The frozen historical profile has no tile_sites field. It is accepted
    # only for the exact old whole program that the frozen authenticator proved.
    raw = program.raw_source.encode("utf-8")
    if (source_hash == "853c3c15f300cf56ba3c11d5613cb91bfcb14b8b2f1be6bb5193e71397fdcea1"
            and len(raw) == 7838
            and hashlib.sha256(raw).hexdigest() == source_hash
            and _whole(program) == "837cf0f8548c8e39960c3aa0cc55f92d2aab0bf4aae1e878c0857679322b8d69"
            and getattr(proof, "_candidate", None) is program):
        return ()
    raise _fail("origin tile proof field missing")


def apply_glyph_map_nonnegative_int_shift(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    authenticate_glyph_map_nonnegative_int_shift(program, source_hash, profile)
    return program


__all__ = (
    "PROFILE", "GLYPH_MAP_KEY", "GlyphMapBitExtractionProof",
    "authenticate_glyph_map_nonnegative_int_shift",
    "authenticated_glyph_map_tile_sites",
    "apply_glyph_map_nonnegative_int_shift",
)
