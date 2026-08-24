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
    LENS_KEY: {
        "raw_bytes": 8269,
        "raw_sha": "f4e6453fe233692fa67c5fdbb3eb8f7a512d21bc722e63af6fc23166a62dd444",
        "source_bytes": 7723,
        "source_sha": "6586c49b079a3b0f4aa3538c8e735e70db088ff2e5d2ea1037e9e9c5486fdf52",
        "main_id": 38,
        "main_body": 25,
        "pre_main": "dc6d4d2a3b5c50598a879dc6679553b3f89d964a19f5d4c79716970a7f2493ee",
        "post_main": "8de6658184c69cb679f0453e37e37f538eebabb0e14f720d1eeea61e715d30ec",
        "pre_functions": "263870c469a9dc3b1f4d5f3a2498864c6da4ff4eaf2cc3efaf198376e4d304c1",
        "post_functions": "c166fa2b38ec68661fb4d73be1bfb3eef4f879da7d82dbfca44deba1b651a756",
        "pre_whole": "f63fb6dba6626791c248501bcfc5ca1c94f073a0593f34dbe846056fe35c81f5",
        "post_whole": "e5dbb049717ce77ba79a36c6ea39ddde88e561df1ba06c98fba0ddd179a63d2e",
        "interface": "53e759b54c0710d9cb3375cc2353878abebec06b378aeaaf9d745c6ecfd2b4ca",
        "profile": "d1235bb6045a5795c4c10c5db8a990f51ee42e5541dcfa7a663c91f3245d10d3",
        "base_id": 72,
        "sites": (
            ((18, "s0", "s3", "e0", 0, 0), "236:9-236:15", 0, "write", "8b56c4f52b2113fa843aeb30133f38a488eda92edca236b9260285e426c632a3", "1d9ee202f7c93a030803d2c61782ef959a8ef56fc8890b39de56bfe6cb2df13b"),
            ((18, "s0", "s3", "e0", 0, 1, 0, 0, 0, 0), "236:24-236:30", 0, "read", "1cc773177b9c87d54bd4289dd97c6384f43c0619d1c29a1b5cf1a09a2225a9e6", "c7daed1dbf0ebc39669fa33212fa1d9b3233fbe7112e07c05ebeaa05a9120920"),
            ((18, "s0", "s3", "e0", 0, 1, 0, 0, 1, 0, 0), "236:65-236:71", 0, "read", "27987cf202ec44e367f3edbacf025685a95a579d3bd1766ed007f3a39fba0233", "689cb485e1d153df4ba2f46f52e10f7843c818cf111cbdf6d79aa26419f9f69a"),
            ((18, "s0", "s4", "e0", 0, 0), "237:9-237:15", 1, "write", "e67ab422ce4f28337e56fef80f8bfb4dbd93a1bbe30eb0165c0aa3cc7dc6cb44", "829b7f013b6ca2c1cbf03eb25079f7a02ec32731eb0bb8d8015dbfa77152e16b"),
            ((18, "s1", "s3", "e0", 0, 0), "247:9-247:15", 0, "write", "92be124aed858e61dff4316731b67be8a46a881c527285b56263477b81193f12", "0ee30fa6b2497642b0b1b2cbb0fe9fee6fc7594191d410f3ff2b20f7ba6c8243"),
            ((18, "s1", "s3", "e0", 0, 1, 0, 0, 0, 0, 0), "247:26-247:32", 0, "read", "af51ced1d6aafe987b1914573554213afb0c123619134749a44fdb603d08b818", "d3a7a9840bbe6523a9038c402537928e10b5abaca692762a7b8947f821f4add0"),
            ((18, "s1", "s4", "e0", 0, 0), "248:9-248:15", 1, "write", "569c4bc0beead7e391d0bddbcfe03fb78b78286f8bb00754eb37bfa5bc1720de", "2c94a065f64b606da19073ffe0afd554d57c9222714af12c034b37f90a6b192a"),
            ((20, "s1", "s0", "s0", "e0", 0, 1, 0, 0, 0, 1, 0), "260:46-260:52", 2, "read", "e2faad5610537f7e86b817e16c093b165a4d4d84bac84799bfc055f3de262fea", "96a5a6b39df3fba890e8286278615e6518ec77b6c9d440f9e315bdc70d596250"),
        ),
    },
    PRISMATIC_KEY: {
        "raw_bytes": 4247,
        "raw_sha": "513eac95fdf7f67a6839ee5d96e5bbfd76b6cfa62d3254df6fed23d8effe380e",
        "source_bytes": 3907,
        "source_sha": "1c157e7f3dc7c9c122cc185812cd2988a98a52024055a482265bded7561a0860",
        "main_id": 22,
        "main_body": 31,
        "pre_main": "416ffbaef2ada8e19fb0f161034a964d4fcfd88c8b2e34fe4f66c1b415a70e56",
        "post_main": "f0d3926e68fcb9c4672779fa36c363d9471240395f36e2857146225e5a87187f",
        "pre_functions": "6949577823e5eccde21335182d379a590db90188f004f3d479503ac33990cf24",
        "post_functions": "80fb20a869a84f8c23942fab3b033e554e48c5e5dda2097eb8dbd346a1c758fd",
        "pre_whole": "fdc004aa9e36925670b4a33446690150a81ed8b13ffba4aed1b944b2d80b997c",
        "post_whole": "1a808ce2ca4aae60be185b04ac96078521db41bcb04d5bb0e9cdb7552f6d482c",
        "interface": "788b0390952c998db1945320c681f114bcbc150fe1f91738894f77a6220df010",
        "profile": "25ad8a580a8263b4d2d15b41eb783abeed3433c94b9c8fffbbae2546300fd6b2",
        "base_id": 55,
        "sites": (
            ((26, "e0", 0, 0), "131:5-131:11", 0, "write", "2637ccd727e74a3b5583230bf07d8ceed92e72dfc4434041075f90515950f23d", "2c240e9eae37323e092e20ac3d21e7382fcd86b7160b8f041cc3a2eb9cb7bdeb"),
            ((26, "e0", 0, 1, 0, 0, 0, 0, 0), "131:22-131:28", 0, "read", "9af4f5115d7b784cac89bd118123e8b0935194c93b970da62f01541590b17ce2", "94558e9138e38ceb285c1746af1473ca77f5f56ef564626edaad0be6546d6072"),
            ((27, "e0", 0, 0), "132:5-132:11", 1, "write", "155a0535e006b5b61f14d842415d9bba0633f15d905e7fbf8944ff847f5685f2", "8e585f401b1450e2f7c58dd3fada71b23f0cb2b4e85f7e75c6371459db863306"),
        ),
    },
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
