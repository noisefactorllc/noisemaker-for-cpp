"""Closed rewrite for the two literal ``vec3 hsv`` lane-index programs."""

from __future__ import annotations

import dataclasses
import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "literal-vec3-lane-index-v1"
LENS_KEY = "classicNoisedeck/lensDistortion:lensDistortion"
PRISMATIC_KEY = "filter/prismaticAberration:prismaticAberration"
KEYS = (LENS_KEY, PRISMATIC_KEY)
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _whole_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def _profile_tuple(key: str, lock: dict[str, object]) -> tuple[object, ...]:
    return (
        PROFILE, key, lock["raw_sha"], {},
        tuple((path, span, pre_hash, post_hash, lock["base_id"], lane, role)
              for path, span, lane, role, pre_hash, post_hash in lock["sites"]),
        lock["pre_functions"], lock["post_functions"],
        lock["pre_whole"], lock["post_whole"], lock["interface"],
    )


_LOCKS = {
    LENS_KEY: {'raw_bytes': 8192, 'raw_sha': '925f4150c4029d13c35de55203d58cb91d8a1f9abfb8146fbb40dcf7cfc1b402', 'source_bytes': 7646, 'source_sha': '5a28ab1e571db951bafcbf6b4e59b6ec488d08308785f86e999b7c1639ac27b7', 'main_id': 38, 'main_body': 25, 'pre_main': 'f7e69cce9ea76f95421cad4ce14f617ab193beab8af149ac7a1139d52423c675', 'post_main': '5e230dc77f0948fc63f0388f9e814985d90fc7135a387e3c0c4a7e823bc1263c', 'pre_functions': '2104d6186cd8a42acc8506b0cbdddbee05873a022043783573dbaa6c31c78e33', 'post_functions': '10fd8ca6c968b92ee912ecb28f4ab6fb0a8c8e6a34958c7b750e22279adf194b', 'pre_whole': '79ea379a1b97f660c09b5dc748acc92c17512a7115716d42e38e79abe2085536', 'post_whole': '0727313b7b8e6faae302aa3fbd298a44b35314ca2d71b2e1eaecb129f67042ec', 'interface': 'eba53b76b6673ca7f57a1622c24c902d2ed8fe711802bf92064d7e419bce2693', 'base_id': 72, 'sites': (((18, 's0', 's3', 'e0', 0, 0), '234:9-234:15', 0, 'write', '1fbb420ac0d1698ff76b11f1210b799e51e1aac00fb84e6b53ea47dc576e5d77', '3b55bb271c4076611d0f8a3eea99613dc14454d67714fae360808909d7851872'), ((18, 's0', 's3', 'e0', 0, 1, 0, 0, 0, 0), '234:24-234:30', 0, 'read', '2c12a39a47bacdb8d18442dc7dcca1ac3505e98160ff9bb041295da6e2a55465', 'cc4c6552e4e30a9acabd909ed7268a49deb5f93539f0a7bc3e3577f671775e77'), ((18, 's0', 's3', 'e0', 0, 1, 0, 0, 1, 0, 0), '234:65-234:71', 0, 'read', 'e866442be780416ff8d3bfc43dff3e049911c62cd219a1c6b754bd2babb5f09a', '1db79c666885b64939494ca148bc26c5897b2ae4ed036531a658a390528b2545'), ((18, 's0', 's4', 'e0', 0, 0), '235:9-235:15', 1, 'write', 'edcddd31aff9cc163b510395c1b6d46efca0a8962b0d0b76c16e92e93ee27de3', '0c0496eced25be758ff8a180b5fc30f1b6d76e8dc115c2d7dae5b8423c9b2fab'), ((18, 's1', 's3', 'e0', 0, 0), '245:9-245:15', 0, 'write', '4b8c2adfe3816a52236803af43eb54da4505efc16744f7d4e1d43376511f40ce', '8f688931999cfcf863c9699a4de48f5c4eb64074e261e5c761b3035ad67ec25c'), ((18, 's1', 's3', 'e0', 0, 1, 0, 0, 0, 0, 0), '245:26-245:32', 0, 'read', 'b7b85056782cb3eba37892781c9417b4ee3ee33b92468f1d49b6e2e27b820829', '352dbc05cfeab9426e1f8caf694abd4107d77426a9421bf05292e6ecca88b932'), ((18, 's1', 's4', 'e0', 0, 0), '246:9-246:15', 1, 'write', 'adaa401e1fbceef9d6444fd60e79d3157f85c985fa1f63aab5fc537ede2a5676', 'bcaa1f856a92a0084da744eec961c794a0b94b9af2daf2da2750d05fc1f2460b'), ((20, 's1', 's0', 's0', 'e0', 0, 1, 0, 0, 0, 1, 0), '258:46-258:52', 2, 'read', '09b84694a417778678fb642e22586d504c4e7dca73353e45baa0b52d8d408b83', '1d4960e3dde9a09e3bd2c42beb40962ffa56cc4cbc277846275e6f38adc530b6')), 'profile': 'b04fe574170ccd989420ceff01174ff1c2b4dbab49204a6eac980dbf78f721a6'},
    PRISMATIC_KEY: {'raw_bytes': 4170, 'raw_sha': '3461a6b0ec3d47f4be1d06ae3ecfbacdb98836a8424bb0ed7f3d3c67af3173d9', 'source_bytes': 3830, 'source_sha': 'df19640f0fb7eb57ef5b2a0af84f5e3d6eacdc2a3c6d814bc6b146efe7b17ffa', 'main_id': 22, 'main_body': 31, 'pre_main': 'e888c9dd411dfde88d0479a05233e9673be39e974ad5a6a02ecca027860cfa6d', 'post_main': 'ffac773e15c4cea69671392841c12ed7772cb8313936b691472a959c048f31a0', 'pre_functions': '523262e5ddad24e7700bd5f8c5a502cf8e9973f71697787318660ae79002d63c', 'post_functions': '229baa43e7c20ab5e6c5b18486983a654dc7e1036cdb17ada61951b9be0e5835', 'pre_whole': '73c9b3324941185bbffab09fcc82832b918c452084145ecb9e1668a843232f98', 'post_whole': 'b50879db8c6f5a838c254d3ad38150f0f3b841e51361bcbca159147b65276701', 'interface': '26690f0fda47e41974dacb4b2fd76aa49dbd6cb4dd96d01f38b82d2f618a0bd7', 'base_id': 55, 'sites': (((26, 'e0', 0, 0), '129:5-129:11', 0, 'write', 'cfd86dcca1d2b6b8a34648870a03091f606e7ad5a2ffa9d1d4e4050057038eb8', '79763d765cc3a24822ea778d8b5d69fa2701fe22613741dce14ef2882e2cebe1'), ((26, 'e0', 0, 1, 0, 0, 0, 0, 0), '129:22-129:28', 0, 'read', '60ca033f3e67a3b45886abc0c76c8308ade858a4a90ba6bb00813630e5e51444', '62011955fac40211c6948ef6a987d0ef1369b3b51144aed9a00b8c6cef04c1ad'), ((27, 'e0', 0, 0), '130:5-130:11', 1, 'write', '16364a676cc4d9bba82e533dc4f980f7d4c1dbbbe041eb9082adfd446a8f461c', '118690a93c33ddacb31a4fa431a382670aaa7a217f797ae54d3ab0bada6ead1c')), 'profile': '572efbae94569ec471147d70d0dfe280223b65180e211d3e258ee92500dadbaf'},
}


def _selected_source_key(program: TypedProgram) -> str | None:
    """Return a selected source identity without trusting the program key/tree."""
    raw_sha = hashlib.sha256(program.raw_source.encode("utf-8")).hexdigest()
    source_sha = hashlib.sha256(program.source.encode("utf-8")).hexdigest()
    matches = tuple(key for key, lock in _LOCKS.items()
                    if raw_sha == lock["raw_sha"] or source_sha == lock["source_sha"])
    if len(matches) == 1:
        return matches[0]
    return "" if matches else None


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _main(program: TypedProgram, lock: dict[str, object]):
    matches = [function for function in program.functions if function.name == "main"]
    if (len(matches) != 1 or len(program.functions) not in (5, 8)
            or matches[0].id != lock["main_id"]
            or len(matches[0].body) != lock["main_body"]):
        raise _fail("main function profile mismatch")
    return matches[0]


def _statement_at(main, path: tuple[object, ...]) -> object:
    value: object = main.body[path[0]]
    expression_root = False
    for step in path[1:]:
        if isinstance(step, str):
            if step.startswith("s"):
                value = getattr(value, "children")[int(step[1:])]
            elif step.startswith("e"):
                value = getattr(value, "expressions")[int(step[1:])]
                expression_root = True
            else:
                raise _fail("invalid frozen site path")
        else:
            if expression_root:
                if step != 0:
                    raise _fail("frozen expression-root marker mismatch")
                expression_root = False
                continue
            value = getattr(value, "children")[step]
    if expression_root:
        raise _fail("frozen path omitted its expression-root marker")
    return value


def _walk_expression(value: TypedExpression, parent: object | None = None,
                     child_index: int | None = None):
    yield value, parent, child_index
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, index)


def _walk_statement_expressions(value: TypedStatement):
    for index, expression in enumerate(value.expressions):
        yield from _walk_expression(expression, value, index)
    for child in value.children:
        yield from _walk_statement_expressions(child)


def _check_common(program: TypedProgram, source_hash: str | None,
                  profile: str | None) -> tuple[dict[str, object], object]:
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    lock = _LOCKS.get(program.key)
    if lock is None or source_hash != lock["raw_sha"]:
        raise _fail("selected key and exact caller source hash required")
    if _sha(_profile_tuple(program.key, lock)) != lock["profile"]:
        raise _fail("internal frozen profile tuple mismatch")
    raw = program.raw_source.encode("utf-8")
    source = program.source.encode("utf-8")
    if (len(raw) != lock["raw_bytes"] or hashlib.sha256(raw).hexdigest() != lock["raw_sha"]
            or len(source) != lock["source_bytes"]
            or hashlib.sha256(source).hexdigest() != lock["source_sha"]
            or program.preprocessor_defines != () or program.body_status != "analyzed"
            or _interface_fingerprint(program) != lock["interface"]):
        raise _fail("source, define, body, or interface profile mismatch")
    if any(getattr(program, field) is not None for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("optional proof carrier is not absent")
    proof = program.counted_loop_proof
    if (proof is None or proof.loop_count != 0 or proof.unproved_loop_count != 0
            or proof.max_effective_depth != 0 or proof.max_lexical_product != 0
            or proof.entrypoint_charge != 0 or not proof.call_graph_acyclic):
        raise _fail("loop or call graph profile mismatch")
    return lock, _main(program, lock)


def _check_site(value: object, *, lock: dict[str, object], span: str,
                lane: int, role: str, expected_kind: str,
                expected_hash: str, parent: object | None,
                child_index: int | None) -> None:
    if not isinstance(value, TypedExpression):
        raise _fail("site path did not resolve an expression")
    if (_sha(value) != expected_hash or value.kind != expected_kind
            or _span(value) != span or value.type.display() != "float"
            or value.category != "lvalue"):
        raise _fail("site value profile mismatch")
    expected_role = ("write" if isinstance(parent, TypedExpression)
                     and parent.kind == "assign" and parent.operator == "="
                     and child_index == 0 else "read")
    if expected_role != role:
        raise _fail("site role profile mismatch")
    if expected_kind == "index":
        if len(value.children) != 2:
            raise _fail("index site arity mismatch")
        base, literal = value.children
        if (base.kind != "id" or base.symbol_id != lock["base_id"]
                or base.symbol is None or base.symbol.name != "hsv"
                or base.symbol.storage != "local" or not base.symbol.writable
                or base.type.display() != "vec3" or base.category != "lvalue"
                or literal.kind != "literal" or literal.type.display() != "int"
                or literal.category != "rvalue" or literal.literal_value != lane):
            raise _fail("literal vec3 base or lane profile mismatch")
    else:
        if (len(value.children) != 1 or value.member != "xyz"[lane]
                or value.children[0].kind != "id" or value.children[0].symbol_id != lock["base_id"]
                or value.children[0].symbol is None
                or value.children[0].symbol.name != "hsv"
                or value.children[0].symbol.storage != "local"
                or not value.children[0].symbol.writable
                or value.children[0].type.display() != "vec3"
                or value.children[0].category != "lvalue"):
            raise _fail("fixed swizzle base or lane profile mismatch")


def _authenticate(program: TypedProgram, source_hash: str | None,
                  profile: str | None, *, post: bool):
    lock, main = _check_common(program, source_hash, profile)
    stage = "post" if post else "pre"
    if (_sha(main) != lock[f"{stage}_main"]
            or _sha(program.functions) != lock[f"{stage}_functions"]
            or _whole_fingerprint(program) != lock[f"{stage}_whole"]):
        raise _fail(f"{stage} function or whole-program profile mismatch")
    expected_kind = "swizzle" if post else "index"
    resolved = []
    for path, span, lane, role, pre_hash, post_hash in lock["sites"]:
        value = _statement_at(main, path)
        matches = [(item, parent, child_index)
                   for statement in main.body
                   for item, parent, child_index in _walk_statement_expressions(statement)
                   if isinstance(item, TypedExpression) and item is value]
        if len(matches) != 1:
            raise _fail("frozen site path is not unique")
        _check_site(value, lock=lock, span=span, lane=lane, role=role,
                    expected_kind=expected_kind,
                    expected_hash=post_hash if post else pre_hash,
                    parent=matches[0][1], child_index=matches[0][2])
        resolved.append(value)
    index_census = [item for function in program.functions
                    for statement in function.body
                    for item, _, _ in _walk_statement_expressions(statement)
                    if isinstance(item, TypedExpression) and item.kind == "index"]
    if not post and tuple(index_census) != tuple(resolved):
        raise _fail("complete whole-program pre-index census mismatch")
    if post and index_census:
        raise _fail("post tree retains an index expression")
    return lock, main, tuple(resolved)


def authenticate_literal_vec3_lane_index_pre(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Return the ordered, source-locked literal-index sites."""
    _, _, sites = _authenticate(program, source_hash, profile, post=False)
    return sites


def authenticate_literal_vec3_lane_index_post(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[tuple[TypedExpression, int, str], ...]:
    """Return value authority for the ordered fixed-swizzle sites."""
    lock, _, sites = _authenticate(program, source_hash, profile, post=True)
    return tuple((site, row[2], row[3]) for site, row in zip(sites, lock["sites"]))


def authenticate_literal_vec3_lane_index_transition(
        before: TypedProgram, after: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[tuple[TypedExpression, int, str], ...]:
    """Require only the exact rewrite while both tree identities are available."""
    pre_sites = authenticate_literal_vec3_lane_index_pre(before, source_hash, profile)
    post_sites = authenticate_literal_vec3_lane_index_post(after, source_hash, profile)
    if len(before.functions) != len(after.functions):
        raise _fail("function count changed across transition")
    before_main = next(function for function in before.functions if function.name == "main")
    after_main = next(function for function in after.functions if function.name == "main")
    for prior, current in zip(before.functions, after.functions):
        if prior is before_main:
            if current is not after_main:
                raise _fail("main function identity mismatch")
        elif current is not prior:
            raise _fail("non-main function identity changed")
    for field in _OPTIONAL_PROOF_FIELDS:
        if (getattr(before, field) != getattr(after, field)
                or getattr(before, field) is not getattr(after, field)):
            raise _fail("optional proof carrier changed across transition")
    for pre, (post, lane, _) in zip(pre_sites, post_sites):
        if post.children[0] is not pre.children[0]:
            raise _fail("post site did not retain the pre base identity")
        expected = dataclasses.replace(
            pre, kind="swizzle", children=(pre.children[0],), member="xyz"[lane])
        if post != expected:
            raise _fail("transition changed more than the fixed lane rewrite")
    return post_sites


def _rewrite_expression(value: TypedExpression, replacements: dict[int, int],
                        count: list[int]) -> TypedExpression:
    lane = replacements.get(id(value))
    if lane is not None:
        count[0] += 1
        return dataclasses.replace(value, kind="swizzle", children=(value.children[0],),
                                   member="xyz"[lane])
    children = tuple(_rewrite_expression(child, replacements, count)
                     for child in value.children)
    return (value if all(child is original for child, original in zip(children, value.children))
            else dataclasses.replace(value, children=children))


def _rewrite_statement(value: TypedStatement, replacements: dict[int, int],
                       count: list[int]) -> TypedStatement:
    expressions = tuple(_rewrite_expression(expression, replacements, count)
                        for expression in value.expressions)
    children = tuple(_rewrite_statement(child, replacements, count)
                     for child in value.children)
    if (all(expression is original for expression, original in zip(expressions, value.expressions))
            and all(child is original for child, original in zip(children, value.children))):
        return value
    return dataclasses.replace(value, expressions=expressions, children=children)


def apply_literal_vec3_lane_index(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Rewrite exactly the authenticated literal lane indexes in one main walk."""
    pre_sites = authenticate_literal_vec3_lane_index_pre(program, source_hash, profile)
    lock = _LOCKS[program.key]
    replacements = {id(site): row[2] for site, row in zip(pre_sites, lock["sites"])}
    main = next(function for function in program.functions if function.name == "main")
    count = [0]
    rewritten_main = dataclasses.replace(
        main, body=tuple(_rewrite_statement(statement, replacements, count)
                         for statement in main.body))
    if count[0] != len(pre_sites):
        raise _fail("one-walk rewrite did not replace every authenticated site")
    transformed = dataclasses.replace(
        program,
        functions=tuple(rewritten_main if function is main else function
                        for function in program.functions))
    authenticate_literal_vec3_lane_index_transition(
        program, transformed, source_hash, profile)
    return transformed
