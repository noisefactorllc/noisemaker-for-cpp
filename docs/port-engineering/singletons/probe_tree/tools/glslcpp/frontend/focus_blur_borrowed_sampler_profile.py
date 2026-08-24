"""Exact borrowed-sampler helper ABI profile for Focus Blur.

This module does not add a general sampler parameter type.  It authenticates
the one corpus program whose two helper parameters may be emitted as immutable
``Surface`` references and returns the candidate-owned IR objects consumed by
the validator and emitter.
"""

from __future__ import annotations

from dataclasses import dataclass
import ast
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "focus-blur-borrowed-sampler-parameters-v1"
FOCUS_BLUR_KEY = "mixer/focusBlur:focusBlur"

_RAW_BYTES = 2268
_RAW_SHA256 = "dff787c7de67122abe60ac14f0fc8995e8087fc4549626e6fe678d8f86b3d7d1"
_NORMALIZED_BYTES = 1685
_NORMALIZED_SHA256 = "8b3cfb07882d0e409f617b2f86b02fa54cd36db213a60881370306306306be9f"
_FUNCTIONS_SHA256 = "95428219c60cd14910f90e572857773e22818bfaf17436f6a249a10b4364c6e3"
_WHOLE_SHA256 = "96468ba160d253f7d064c2caccd9db686d772a2af94d13ee836996dc488e037b"
_INTERFACE_SHA256 = "3158dcf83a1d13f84a2d8f3d374d464230ff24b1ed812603cc02fbc96e56be96"
_PROFILE_SHA256 = "869eafed0199be24c6fcf5a13d39211c1ea0c1227f9ee12b55f5c69196e9780b"
_FROZEN_PROFILE_TUPLE_REPR = """('focus-blur-borrowed-sampler-parameters-v1', 'mixer/focusBlur:focusBlur', 'dff787c7de67122abe60ac14f0fc8995e8087fc4549626e6fe678d8f86b3d7d1', (), 'glsl-f32', '95428219c60cd14910f90e572857773e22818bfaf17436f6a249a10b4364c6e3', '96468ba160d253f7d064c2caccd9db686d772a2af94d13ee836996dc488e037b', '3158dcf83a1d13f84a2d8f3d374d464230ff24b1ed812603cc02fbc96e56be96', (16, 'applyFocusBlur', '35b78a99ce2d7506016ac0645631155b59ee260e50a3776906f88192778c5d79', 'fd9a2496e322b3b035258d1532ac4dd37c79f778a5c53c55a1231cfad24e00bb', '29:1-46:2', 7, ((13, 'sceneTex', 'sampler2D', 'in', '29:21-29:39', '09e40c6d31b787f60fd4ad93e2e9edba976fabc24ba24434aeb8581960958a14'), (14, 'depthTex', 'sampler2D', 'in', '29:41-29:59', '07258bb2b58f1de0ca4cfd81edd11b519bf23efae4a5f19eb277ea0019c72252'), (15, 'uv', 'vec2', 'in', '29:61-29:68', 'f23d8c4ed6bb89cb61f02914aec289b97d297d0dcd891b815d4d2077890f57cd'))), (((0, 'e0', 0, 0, 0), '30:32-30:40', 'e1faaf1503a69bf30fcc59725e44a685aa08388951202a1374cc60c922733175', 14, 'builtin', -46, 0, 'af38790d624a4812e73f52a399abec0cef059e3372b9e948482ca8459bc1d2c2'), ((0, 'e0', 0, 0, 1, 1, 0, 0), '30:77-30:85', '54cb713f1b9d5dd2bbe5f8c4189fb35cf7aad23668e9d9138dfc8ddc53c89e61', 14, 'builtin', -48, 0, '9cdd39da62fb15565acfd2ad84e6bd3e6b4f56c0125b93f85580f6b73d3f6b48'), ((5, 's1', 's3', 'e0', 0, 1, 0), '42:26-42:34', '7d56c435e0db8a292b3990201095f6337acefa4485f39269dfac0cabb269cc26', 13, 'builtin', -46, 0, 'aeb1742bc4673aab6f94e67bdf993f701e8280d1d1f633d646fc4403b30eef05'), ((5, 's1', 's3', 'e0', 0, 1, 1, 1, 0, 0), '42:101-42:109', '59f8fe65b17ba149c322d14f76f5ae6379612e034dff9f526d602ca829fbd8b5', 13, 'builtin', -48, 0, '05fb7d5f31950126a312078d817dc427b489a612fb47cd4b64e662e7766320f7')), (((3, 's0', 's0', 'e0', 0, 1), '57:17-57:50', '025a7dce21804b69158b70710ffd975af31a0dc7569313d3a0ed29692722d2c8', 16, (2, 1, 33), ('sampler2D', 'sampler2D', 'vec2'), ('5a03db4215473a0c74dce71a1359ad2b6d1f53fe9fa9bd29118c007ba9f9fcbc', '9967055be5eac15e6b51b30d4010565176e6d161e6b088c5d9d02d28317a1a3c', '34f533d9626bf6cd8e949dfb10799763ed437dbdde7d9c2102a1e0d74a3116f5'), 'assign', 1, '04ddf0a5628905033b6f25766b0781f1329667c4fe7923cc311546b567696fcc', (((3, 's0', 's0', 'e0', 0), 'assign', '57:9-57:50', '04ddf0a5628905033b6f25766b0781f1329667c4fe7923cc311546b567696fcc', None),), (((3,), 'if', '56:5-60:6', 'b86152c26ce7379f0fd078d49e74699c76476f3ec34aaee1345506f46a2356c9', None, 2, 1), ((3, 's0'), 'block', '56:27-58:6', 'ec8cbb5d802f2f3079766b21615f56d14815c59bbdc8ab2b34d0b2a0db818ed0', 0, 1, 0), ((3, 's0', 's0'), 'expr', '57:9-57:51', '1f31366c027aa18b2da8c08065913e486ed50f36e269037e97ea8c4917db1639', 0, 0, 1)), (3,), 'if', '56:5-60:6', 'b86152c26ce7379f0fd078d49e74699c76476f3ec34aaee1345506f46a2356c9', (3, 'e0', 0), 'binary', '==', 'bool', '56:9-56:25', '150350bdf498d009c67fbc4782ec274f91674f15d0cfaff473744c683bb57774', (9, None), ('id', 'literal'), ('int', 'int'), (None, 0), ('1ef38c87a1ddfb650b7bf3c5f5e0626191075a4cbabdda7189f35e36df8616ee', 'c2c4bf6aef38f2ed9fdbfea1dede78dbee1add983f6a3cfc593427a67738ab71'), 0, 'then', (3, 's0'), 'block', '56:27-58:6', 'ec8cbb5d802f2f3079766b21615f56d14815c59bbdc8ab2b34d0b2a0db818ed0', 1, 0), ((3, 's1', 's0', 'e0', 0, 1), '59:17-59:50', 'de171d5c1c8f406685b0ecd9552474ac936c22b8070953b236b9e828cd57c394', 16, (1, 2, 33), ('sampler2D', 'sampler2D', 'vec2'), ('a18ea0caa0fc37376bdc38d38d27ace2355e7782c3469d10c897cd0104aee62f', '57436557c228b1f3ea8f3455e4bb0c56933e3248891e11ad82eb1e39ba3d93e0', '56d9e6c68f56f793903d489913f55b7aa338fc61d07b6be659285ed489286b21'), 'assign', 1, 'f7cafb6b9894d0829841b264386ce0a8baf37603a8f23acdfc12da5479c6e9da', (((3, 's1', 's0', 'e0', 0), 'assign', '59:9-59:50', 'f7cafb6b9894d0829841b264386ce0a8baf37603a8f23acdfc12da5479c6e9da', None),), (((3,), 'if', '56:5-60:6', 'b86152c26ce7379f0fd078d49e74699c76476f3ec34aaee1345506f46a2356c9', None, 2, 1), ((3, 's1'), 'block', '58:12-60:6', 'd4c4b59d25148207cf5fbc21388751e24e6632136f17d55371597eb173768af1', 1, 1, 0), ((3, 's1', 's0'), 'expr', '59:9-59:51', '748350e159fe5e0761f747894d3a2dea2532c5e83b9352ff85793335eaa129a0', 0, 0, 1)), (3,), 'if', '56:5-60:6', 'b86152c26ce7379f0fd078d49e74699c76476f3ec34aaee1345506f46a2356c9', (3, 'e0', 0), 'binary', '==', 'bool', '56:9-56:25', '150350bdf498d009c67fbc4782ec274f91674f15d0cfaff473744c683bb57774', (9, None), ('id', 'literal'), ('int', 'int'), (None, 0), ('1ef38c87a1ddfb650b7bf3c5f5e0626191075a4cbabdda7189f35e36df8616ee', 'c2c4bf6aef38f2ed9fdbfea1dede78dbee1add983f6a3cfc593427a67738ab71'), 1, 'else', (3, 's1'), 'block', '58:12-60:6', 'd4c4b59d25148207cf5fbc21388751e24e6632136f17d55371597eb173768af1', 1, 0)), ((16, (0, 'e0', 0, 0), '30:24-30:91', 'af38790d624a4812e73f52a399abec0cef059e3372b9e948482ca8459bc1d2c2', 14), (16, (5, 's1', 's3', 'e0', 0, 1), '42:18-42:115', 'aeb1742bc4673aab6f94e67bdf993f701e8280d1d1f633d646fc4403b30eef05', 13), (19, (4, 'e0', 0, 1, 0, 0), '63:19-63:86', 'b4a42b659276297270cdf2d467a6e2a9f253d240cc2d30806b12dd1333cca5e7', 1), (19, (4, 'e0', 0, 1, 1, 0), '63:90-63:147', '746c018747191098bf1d4685729c87a1cb778020880d05ef4f3a2d6ccb25753e', 2)), ((16, (0, 'e0', 0, 0, 1, 1, 0), '30:65-30:89', '9cdd39da62fb15565acfd2ad84e6bd3e6b4f56c0125b93f85580f6b73d3f6b48', 14), (16, (5, 's1', 's3', 'e0', 0, 1, 1, 1, 0), '42:89-42:113', '05fb7d5f31950126a312078d817dc427b489a612fb47cd4b64e662e7766320f7', 13), (19, (4, 'e0', 0, 1, 0, 0, 1, 1, 0), '63:60-63:84', '36ad171b1f97d660f178ed039c2524240b87fe7b2ccba347121b53d10e817219', 1), (19, (4, 'e0', 0, 1, 1, 0, 1, 1, 0), '63:126-63:145', 'ff71a2a2f2fcca9b85e176f39344bd42c169810b3bda3f2d7c5948cf08e3eb44', 2)), {'loop_count': 1, 'unproved_loop_count': 0, 'max_effective_depth': 1, 'max_lexical_product': 64, 'entrypoint_charge': 64, 'call_graph_acyclic': True})"""

_HELPER_SIGNATURE_SHA256 = "35b78a99ce2d7506016ac0645631155b59ee260e50a3776906f88192778c5d79"
_HELPER_BODY_SHA256 = "fd9a2496e322b3b035258d1532ac4dd37c79f778a5c53c55a1231cfad24e00bb"
_CALL_SHA256 = (
    "025a7dce21804b69158b70710ffd975af31a0dc7569313d3a0ed29692722d2c8",
    "de171d5c1c8f406685b0ecd9552474ac936c22b8070953b236b9e828cd57c394",
)
_USE_SHA256 = (
    "e1faaf1503a69bf30fcc59725e44a685aa08388951202a1374cc60c922733175",
    "54cb713f1b9d5dd2bbe5f8c4189fb35cf7aad23668e9d9138dfc8ddc53c89e61",
    "7d56c435e0db8a292b3990201095f6337acefa4485f39269dfac0cabb269cc26",
    "59f8fe65b17ba149c322d14f76f5ae6379612e034dff9f526d602ca829fbd8b5",
)
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)


@dataclass(frozen=True, slots=True)
class FocusBlurBorrowedSamplerProof:
    helper: TypedFunction
    sampler_parameters: tuple[object, object]
    sampler_uses: tuple[TypedExpression, ...]
    calls: tuple[TypedExpression, TypedExpression]
    call_parents: tuple[TypedExpression, TypedExpression]
    conditional: TypedStatement
    predicate: TypedExpression
    branches: tuple[TypedStatement, TypedStatement]
    statement_parent_chains: tuple[tuple[TypedStatement, ...], ...]
    texture_sites: tuple[TypedExpression, ...]
    texture_size_sites: tuple[TypedExpression, ...]

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        values: list[object] = [self.helper, *self.sampler_parameters,
                                *self.sampler_uses, *self.calls,
                                *self.call_parents, self.conditional,
                                self.predicate, *self.branches]
        values.extend(self.texture_sites)
        values.extend(self.texture_size_sites)
        for chain in self.statement_parent_chains:
            values.extend(chain)
        unique: list[object] = []
        for value in values:
            if not any(value is item for item in unique):
                unique.append(value)
        return tuple(unique)


__all__ = ("PROFILE", "FOCUS_BLUR_KEY", "FocusBlurBorrowedSamplerProof",
           "authenticate_focus_blur_borrowed_sampler_parameters",
           "apply_focus_blur_borrowed_sampler_parameters")


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


def _profile_tuple() -> tuple[object, ...]:
    # This tuple is the independently recomputed frozen package identity.  The
    # whole-program lock below authenticates every detailed coordinate; this
    # compact tuple prevents accidental retargeting of the profile itself.
    value = ast.literal_eval(_FROZEN_PROFILE_TUPLE_REPR)
    if not isinstance(value, tuple):
        raise _fail("internal frozen profile tuple is not a tuple")
    return value


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk_expression(value: TypedExpression, parent: TypedExpression | None = None):
    yield value, parent
    for child in value.children:
        yield from _walk_expression(child, value)


def _walk_statement(value: TypedStatement, ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for expression in value.expressions:
        for item, parent in _walk_expression(expression):
            yield item, parent, chain
    for child in value.children:
        yield from _walk_statement(child, chain)


def authenticate_focus_blur_borrowed_sampler_parameters(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> FocusBlurBorrowedSamplerProof:
    """Authenticate Focus Blur and return only candidate-owned exact objects."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    if _sha(_profile_tuple()) != _PROFILE_SHA256:
        raise _fail("internal frozen profile tuple mismatch")
    if program.key != FOCUS_BLUR_KEY or source_hash != _RAW_SHA256:
        raise _fail("selected key and exact caller source hash required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != _RAW_BYTES or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or program.preprocessor_defines != ()
            or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256):
        raise _fail("source, define, function, whole-program, or interface mismatch")
    if any(getattr(program, field) is not None for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    proof = program.counted_loop_proof
    if (proof is None or
            (proof.loop_count, proof.unproved_loop_count,
             proof.max_effective_depth, proof.max_lexical_product,
             proof.entrypoint_charge, proof.call_graph_acyclic)
            != (1, 0, 1, 64, 64, True)):
        raise _fail("loop or call graph profile mismatch")
    if len(program.functions) != 4:
        raise _fail("function cardinality mismatch")
    helper = next((item for item in program.functions if item.id == 16), None)
    main = next((item for item in program.functions if item.id == 19), None)
    if (helper is None or main is None
            or (helper.name, helper.return_type.display(), len(helper.parameters),
                len(helper.body), _sha(helper.signature), _sha(helper), _span(helper))
            != ("applyFocusBlur", "vec4", 3, 7, _HELPER_SIGNATURE_SHA256,
                _HELPER_BODY_SHA256, "29:1-46:2")
            or (main.name, main.return_type.display(), len(main.parameters),
                len(main.body), _span(main)) != ("main", "void", 0, 6, "48:1-66:2")):
        raise _fail("helper or main identity mismatch")
    parameters = helper.parameters
    expected_parameters = (
        (13, "sceneTex", "sampler2D", "parameter", "in", True,
         "29:21-29:39"),
        (14, "depthTex", "sampler2D", "parameter", "in", True,
         "29:41-29:59"),
        (15, "uv", "vec2", "parameter", "in", True, "29:61-29:68"),
    )
    actual_parameters = tuple(
        (item.id, item.name, item.type.display(), item.storage,
         item.direction, item.writable, _span(item)) for item in parameters)
    if actual_parameters != expected_parameters:
        raise _fail("helper parameter mismatch")
    if ((program.resources.uniforms, program.resources.samplers,
         program.resources.outputs, program.resources.uses_texture,
         program.resources.uses_derivatives)
            != (("inputTex", "tex", "resolution", "tileOffset",
                 "fullResolution", "focalDistance", "aperture",
                 "sampleBias", "depthSource"),
                ("inputTex", "tex"), ("fragColor",), True, False)):
        raise _fail("resource or binding signature mismatch")

    helper_items = [item for statement in helper.body
                    for item in _walk_statement(statement)]
    sampler_uses = tuple(item for item, parent, _ in helper_items
                         if item.kind == "id" and item.symbol_id in {13, 14})
    if (tuple(_sha(item) for item in sampler_uses) != _USE_SHA256
            or tuple(item.symbol_id for item in sampler_uses) != (14, 14, 13, 13)):
        raise _fail("sampler parameter use mismatch")
    for item, parent, _ in helper_items:
        if item in sampler_uses and not (
                parent is not None and parent.kind == "builtin"
                and parent.callee in {"texture", "textureSize"}
                and parent.children and parent.children[0] is item):
            raise _fail("sampler parameter escape or write")

    main_items = [item for statement in main.body
                  for item in _walk_statement(statement)]
    call_records = [(item, parent, chain) for item, parent, chain in main_items
                    if item.kind == "call" and item.signature_id == helper.id]
    if (len(call_records) != 2
            or tuple(_sha(item) for item, _, _ in call_records) != _CALL_SHA256):
        raise _fail("helper call cardinality or identity mismatch")
    calls = tuple(item for item, _, _ in call_records)
    parents = tuple(parent for _, parent, _ in call_records)
    if any(parent is None or parent.kind != "assign" or len(parent.children) != 2
           or parent.children[1] is not call for call, parent in zip(calls, parents)):
        raise _fail("helper call parent mismatch")
    if tuple(tuple(child.symbol_id for child in call.children) for call in calls) != (
            (2, 1, 33), (1, 2, 33)):
        raise _fail("helper call argument order mismatch")
    conditional = main.body[3]
    if (conditional.kind != "if" or len(conditional.expressions) != 1
            or len(conditional.children) != 2
            or _sha(conditional)
            != "b86152c26ce7379f0fd078d49e74699c76476f3ec34aaee1345506f46a2356c9"):
        raise _fail("conditional identity mismatch")
    predicate = conditional.expressions[0]
    branches = conditional.children
    if (predicate.kind != "binary" or predicate.operator != "=="
            or predicate.type.display() != "bool"
            or tuple(child.symbol_id for child in predicate.children) != (9, None)
            or tuple(child.literal_value for child in predicate.children) != (None, 0)
            or _sha(predicate)
            != "150350bdf498d009c67fbc4782ec274f91674f15d0cfaff473744c683bb57774"
            or tuple(_sha(item) for item in branches) != (
                "ec8cbb5d802f2f3079766b21615f56d14815c59bbdc8ab2b34d0b2a0db818ed0",
                "d4c4b59d25148207cf5fbc21388751e24e6632136f17d55371597eb173768af1")):
        raise _fail("predicate or branch ownership mismatch")
    chains = tuple(chain for _, _, chain in call_records)
    if (any(not chain or chain[0] is not conditional for chain in chains)
            or chains[0][1] is not branches[0]
            or chains[1][1] is not branches[1]
            or tuple(len(chain) for chain in chains) != (3, 3)):
        raise _fail("complete conditional ancestry mismatch")
    all_expressions = [item for function in program.functions
                       for statement in function.body
                       for item, _, _ in _walk_statement(statement)]
    texture_sites = tuple(item for item in all_expressions
                          if item.kind == "builtin" and item.callee == "texture")
    texture_size_sites = tuple(
        item for item in all_expressions
        if item.kind == "builtin" and item.callee == "textureSize")
    if (tuple(_sha(item) for item in texture_sites) != (
            "af38790d624a4812e73f52a399abec0cef059e3372b9e948482ca8459bc1d2c2",
            "aeb1742bc4673aab6f94e67bdf993f701e8280d1d1f633d646fc4403b30eef05",
            "b4a42b659276297270cdf2d467a6e2a9f253d240cc2d30806b12dd1333cca5e7",
            "746c018747191098bf1d4685729c87a1cb778020880d05ef4f3a2d6ccb25753e")
            or tuple(_sha(item) for item in texture_size_sites) != (
                "9cdd39da62fb15565acfd2ad84e6bd3e6b4f56c0125b93f85580f6b73d3f6b48",
                "05fb7d5f31950126a312078d817dc427b489a612fb47cd4b64e662e7766320f7",
                "36ad171b1f97d660f178ed039c2524240b87fe7b2ccba347121b53d10e817219",
                "ff71a2a2f2fcca9b85e176f39344bd42c169810b3bda3f2d7c5948cf08e3eb44")
            or tuple(item.children[0].symbol_id for item in texture_sites)
            != (14, 13, 1, 2)
            or tuple(item.children[0].symbol_id for item in texture_size_sites)
            != (14, 13, 1, 2)):
        raise _fail("texture or textureSize site mismatch")
    result = FocusBlurBorrowedSamplerProof(
        helper, (parameters[0], parameters[1]), sampler_uses, calls, parents,
        conditional, predicate, branches, chains, texture_sites,
        texture_size_sites)
    if len(result.consumed_objects) != 25:
        raise _fail(f"consumed object cardinality mismatch: {len(result.consumed_objects)}")
    return result


def apply_focus_blur_borrowed_sampler_parameters(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_focus_blur_borrowed_sampler_parameters(
        program, source_hash, profile)
    return program
