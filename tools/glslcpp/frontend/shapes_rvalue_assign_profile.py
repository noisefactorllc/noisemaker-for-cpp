"""Exact one-node rvalue compound-assignment profile for `classicNoisedeck/shapes`.

Shapes uses an assignment in **rvalue position** exactly once, in a rotation
helper (normalized `42:19`, raw `shapes.glsl:56`):

```glsl
vec2 rotate2D(vec2 st, float rot) {
    float angle = rot *= PI;
```

The validator already accepts this program -- `*=` is a member of the frozen
six-entry `APPROVED_ASSIGNMENT_OPERATORS` tuple. The gap is in the **emitter**,
which lowers assignment only at statement level and has no `assign` arm in its
expression dispatcher. This module admits that one node by identity so the
emitter's new, identity-gated `assign` arm can never fire anywhere else.

**The lowering is settled by the shipped JavaScript, not by reading the GLSL.**
`canonicalFactory16` does *not* dead-code-eliminate `rotate2D`; it materializes
the line as:

```js
function rotate2D (st, rot) {
	st = $runtime.copy(st);
	var angle = rot *= 3.1415927410125732;
```

So the reference keeps the compound assignment as an rvalue, with `PI`
materialized as the f32 value widened to double, and
`float angle = (rot *= <f32 pi>);` is directly expressible in C++ with
identical semantics.

**Claim boundary.** `rotate2D` has zero callers -- normalized line 41 is its
only occurrence in the program -- and `rot` is read nowhere after the
assignment. The construct is therefore dead, and **no oracle case can
discriminate this lowering**. Full-surface parity must not be cited as evidence
that it is correct, and this module makes no execution claim. Structural
authentication, the mutation and lock-deletion coverage in
`tests/test_shapes_rvalue_assign.py`, and the JavaScript materialization quoted
above are what carry the proof -- exactly the posture the float-bit ingress
closure already takes for the dynamically dead hash branch.

**No vocabulary growth.** Nothing here touches `APPROVED_CAPABILITIES` (44),
`APPROVED_TYPES` (17), `APPROVED_BINARY_OPERATORS` (17), or
`APPROVED_ASSIGNMENT_OPERATORS` (6); the caller must skip `used.add(...)` for
the admitted node, as with the lane-index and float-bit-ingress closures.

Two structural notes, both consequences of review findings on this worker's
earlier closures:

* the `Symbol` dataclass embeds its own declaration span, so an operator- or
  value-level mutation shifts every enclosing node hash. The operator, operand
  and target locks are therefore evaluated **ahead** of node identity, and each
  is a separately named predicate so a test can delete exactly one and prove it
  was load-bearing; and
* the census walks the four `mat3` **global declaration initializers** as well
  as every function body, so an assignment hidden in a global cannot escape
  into the coarse hash gate.

The census selects by "**not** statement-rooted" rather than by "has an
expression parent". The emitter lowers exactly one shape at statement level --
an assignment that is the sole expression of an `expr` statement -- and
everything else reaches its expression dispatcher. Selecting by parent would
miss an assignment at the root of a *non-*`expr` statement's expression list
(`return a = b;`) and one at the root of a global initializer: both have
`parent is None` yet both reach the dispatcher. On the frozen Shapes program
the two predicates agree exactly -- all 57 statement-level assignments are the
sole expression of an `expr` statement -- so the stricter test changes neither
frozen count nor the result for valid input.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "shapes-rvalue-assign-v1"
SHAPES_KEY = "classicNoisedeck/shapes:shapes"
SHAPES_RVALUE_ASSIGN_KEYS = frozenset({SHAPES_KEY})

_RAW_BYTES = 21289
_RAW_SHA256 = "60bc6e76ac9d9f5bc83638fa934b279499559f7733806e462cea16a4cbe85eb0"
_NORMALIZED_BYTES = 18713
_NORMALIZED_SHA256 = (
    "347d19f46adb59129ec2f5eb58910b1ea981be9ec03788a068ff6e884bb848e6")
_FUNCTIONS_SHA256 = (
    "dfd7220ab36ed03702afbc5e69e7e3a7346c60d488d9b3a2087d31214219943a")
_WHOLE_SHA256 = (
    "e072ec89fef6122ed3d581ea5efb6cec953d9b7492294ca9d8b0f011af5411f0")
_INTERFACE_SHA256 = (
    "e27ca4581c14991de7a17e296353b1993e8f9c6e5a4ec48b170dde8f8d1b1b6c")

_DEFINES = (("LOOP_A_OFFSET", "int", "40"), ("LOOP_B_OFFSET", "int", "30"))
_DECLARATION_COUNT = 23
_FUNCTION_COUNT = 36

_OWNER = (143, "rotate2D", "vec2",
          ((25, "st", "vec2", "in"), (26, "rot", "float", "in")),
          5, "41:1-47:2")
_OWNER_BODY = (("decl", "42:5-42:40"), ("expr", "43:5-43:64"),
               ("expr", "44:5-44:69"), ("expr", "45:5-45:64"),
               ("return", "46:5-46:15"))
_OWNER_STATEMENT_INDEX = 0

# The compound operator, isolated so `_operator_holds` can be deleted alone.
_OPERATOR = "*="
# Assign node: span, type, category, hash.
_ASSIGN = ("42:19-42:39", "float", "rvalue",
           "a1020f2e429ff513f4cec3abde71a7b5b3f067c98c9fba371f441c57400386c7")
# Declaration parent: kind, span, type, symbol id/name/storage/writable, hash.
_PARENT = ("declaration", "42:11-42:39", "float", 317, "angle", "local", True,
           "c09be5df8b80d45ef51ffddb4f299b00ff0fe6b62bbf10320603f0c60103f7f3")
# Target: kind, span, type, category, symbol id/name/storage/writable, hash.
_TARGET = ("id", "42:19-42:22", "float", "lvalue", 26, "rot", "parameter",
           True,
           "e5961d61b421f161caf09e502fc4e5b5a551de61cd889a95b94e05340bd8468a")
# Operand: kind, span, type, category, literal text, literal value, hash. `PI`
# is a preprocessor macro, substituted during normalization, so it arrives as
# this literal rather than as a global reference.
_OPERAND = ("literal", "42:26-42:39", "float", "rvalue", "3.14159265359",
            3.14159265359,
            "6c9fb072ebaee55e5cee220180e99cbc855173f07deb6686412b079563a202e0")
_PATH = (0, "e0", 0)
_STATEMENT_CHAIN = (("decl", "42:5-42:40"),)

# Exactly one assignment is not statement-rooted -- i.e. reaches the emitter's
# expression dispatcher; 58 assignment nodes exist program-wide across function
# bodies and the four `mat3` global declaration initializers.
_RVALUE_ASSIGN_CENSUS = 1
_TOTAL_ASSIGN_CENSUS = 58
# `rot` is referenced exactly once as an expression, program-wide: the
# assignment target. It is never read after the assignment.
_TARGET_REFERENCES = 1

_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)

# Owner, assign node, declaration parent, target, operand, and the declaration
# statement: six distinct objects, each visited and consumed exactly once.
_CONSUMED_LEDGER = 6

__all__ = (
    "PROFILE", "SHAPES_KEY", "SHAPES_RVALUE_ASSIGN_KEYS",
    "authenticate_shapes_rvalue_assign", "apply_shapes_rvalue_assign",
)


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


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _check_ledger(entries: list, expected: int, label: str) -> None:
    """Require ``entries`` to hold exactly ``expected`` distinct objects."""
    identities = [id(item) for item in entries]
    if len(identities) != expected or len(set(identities)) != expected:
        raise _fail(f"{label} visitation ledger mismatch")


def _walk_expression(value: TypedExpression,
                     parent: TypedExpression | None = None,
                     path: tuple[object, ...] = ()):
    yield value, parent, path
    for index, child in enumerate(value.children):
        yield from _walk_expression(child, value, (*path, index))


def _walk_statement(value: TypedStatement, path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for index, expression in enumerate(value.expressions):
        yield from ((item, parent, expression_path, chain, index)
                    for item, parent, expression_path in _walk_expression(
                        expression, None, (*path, f"e{index}")))
    for index, child in enumerate(value.children):
        yield from _walk_statement(child, (*path, f"s{index}"), chain)


def _is_statement_rooted(parent: TypedExpression | None,
                         statement: TypedStatement | None,
                         expression_index: int) -> bool:
    """True when the assignment *is* the whole of an ``expr`` statement.

    The emitter lowers exactly this shape at statement level; everything else
    reaches its expression dispatcher and is therefore in scope for the
    census. Censusing by "not statement-rooted" rather than by "has an
    expression parent" closes two holes the parent test leaves open: an assign
    at the root of a **non-**``expr`` statement's expression list
    (``return a = b;``), and an assign at the root of a global declaration
    initializer -- both have ``parent is None`` yet both reach the dispatcher.

    On the frozen Shapes program the two predicates agree exactly: all 57
    statement-level assignments are the sole expression of an ``expr``
    statement, and the one rvalue site is unchanged. Both frozen counts are
    therefore unaffected by using the stricter test.
    """
    return (parent is None and statement is not None
            and statement.kind == "expr" and expression_index == 0
            and len(statement.expressions) == 1)


# --- individually deletable locks -------------------------------------------
#
# Each predicate below is one lock. A test proves a lock load-bearing by
# re-executing this module into a scratch namespace, replacing exactly one of
# these functions with an always-true stand-in, and showing that the lock's
# message disappears. Keep them small, single-purpose, and side-effect free.

def _operator_holds(node: TypedExpression) -> bool:
    """The compound operator is exactly `*=`."""
    return node.operator == _OPERATOR


def _operand_holds(operand: TypedExpression) -> bool:
    """The right operand is the exact `PI` literal, by text and value."""
    return (operand.kind == _OPERAND[0]
            and operand.type is not None
            and operand.type.display() == _OPERAND[2]
            and operand.category == _OPERAND[3]
            and operand.literal == _OPERAND[4]
            and isinstance(operand.literal_value, float)
            and operand.literal_value.hex() == _OPERAND[5].hex()
            and operand.children == ())


def _target_holds(target: TypedExpression) -> bool:
    """The assignment target is the writable `rot` parameter."""
    return (target.kind == _TARGET[0]
            and target.type is not None
            and target.type.display() == _TARGET[2]
            and target.category == _TARGET[3]
            and target.symbol_id == _TARGET[4]
            and target.symbol is not None
            and target.symbol.id == _TARGET[4]
            and target.symbol.name == _TARGET[5]
            and target.symbol.storage == _TARGET[6]
            and target.symbol.writable == _TARGET[7]
            and target.children == ())


def _node_identity_holds(node: TypedExpression, target: TypedExpression,
                         operand: TypedExpression) -> bool:
    """Span and node hashes of the assignment and both operands."""
    return ((_span(node), "" if node.type is None else node.type.display(),
             node.category, _sha(node)) == _ASSIGN
            and _span(target) == _TARGET[1] and _sha(target) == _TARGET[8]
            and _span(operand) == _OPERAND[1]
            and _sha(operand) == _OPERAND[6])


def _parent_holds(parent: TypedExpression | None,
                  node: TypedExpression) -> bool:
    """The `float angle = ...` declaration owns the assignment directly."""
    return (parent is not None
            and (parent.kind, _span(parent),
                 "" if parent.type is None else parent.type.display(),
                 parent.symbol_id,
                 None if parent.symbol is None else parent.symbol.name,
                 None if parent.symbol is None else parent.symbol.storage,
                 None if parent.symbol is None else parent.symbol.writable,
                 _sha(parent)) == _PARENT
            and len(parent.children) == 1
            and parent.children[0] is node)


def _ancestry_holds(path: tuple[object, ...],
                    chain: tuple[TypedStatement, ...],
                    statement: TypedStatement) -> bool:
    """Expression path and statement ancestry inside the owner body."""
    return (path == _PATH
            and len(chain) == 1
            and tuple((item.kind, _span(item)) for item in chain)
            == _STATEMENT_CHAIN
            and chain[0] is statement)


def _reference_census_holds(references: list[TypedExpression],
                            target: TypedExpression) -> bool:
    """`rot` is referenced exactly once program-wide: as this target."""
    return (len(references) == _TARGET_REFERENCES
            and references[0] is target)


def authenticate_shapes_rvalue_assign(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Return the one exact rvalue compound-assignment node from the tree.

    Returns an empty tuple when ``program.key`` is not the carrier, so callers
    can treat the result as a membership set unconditionally; supplying a
    profile for a non-carrier key is a hard failure that names Shapes as the
    sole program the widened emitter boundary exists for.
    """
    if program.key not in SHAPES_RVALUE_ASSIGN_KEYS:
        if profile is not None:
            raise _fail(
                "program key is not an admitted Shapes rvalue-assign carrier; "
                f"the rvalue compound assignment at {SHAPES_KEY} "
                f"{_ASSIGN[0]} is the sole admitted site")
        return ()
    if profile != PROFILE:
        raise _fail("exact profile carrier required")

    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if defines != _DEFINES:
        raise _fail("exact preprocessor define lock mismatch")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (source_hash != _RAW_SHA256
            or len(raw) != _RAW_BYTES
            or hashlib.sha256(raw).hexdigest() != _RAW_SHA256
            or len(normalized) != _NORMALIZED_BYTES
            or hashlib.sha256(normalized).hexdigest() != _NORMALIZED_SHA256
            or program.body_status != "analyzed"
            or _sha(program.functions) != _FUNCTIONS_SHA256
            or _whole(program) != _WHOLE_SHA256
            or _interface(program) != _INTERFACE_SHA256):
        raise _fail("source, define, function, whole-program, or interface "
                    "mismatch")
    if any(getattr(program, field, None) is not None
           for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    if (len(program.declarations) != _DECLARATION_COUNT
            or len(program.functions) != _FUNCTION_COUNT):
        raise _fail("declaration or function cardinality mismatch")

    (owner_id, owner_name, owner_return, owner_parameters, owner_body_length,
     owner_span) = _OWNER
    owners = [item for item in program.functions if item.id == owner_id]
    if len(owners) != 1:
        raise _fail("rotate2D owner identity mismatch")
    owner = owners[0]
    if ((owner.name, owner.return_type.display(),
         tuple((item.id, item.name, item.type.display(), item.direction)
               for item in owner.parameters),
         len(owner.body), _span(owner))
            != (owner_name, owner_return, owner_parameters, owner_body_length,
                owner_span)):
        raise _fail("rotate2D owner identity mismatch")
    if tuple((item.kind, _span(item)) for item in owner.body) != _OWNER_BODY:
        raise _fail("rotate2D owner body shape mismatch")

    # Whole-program census. Global declaration initializers are walked as well
    # as function bodies: a node hidden in one of Shapes' four `mat3` globals
    # must be censused here, not left to the coarse hash gate.
    located: list[tuple[tuple[object, ...], TypedExpression,
                        TypedExpression | None,
                        tuple[TypedStatement, ...]]] = []
    total = 0
    references: list[TypedExpression] = []
    for declaration in program.declarations:
        initializer = getattr(declaration, "initializer", None)
        if initializer is None:
            continue
        for item, parent, path in _walk_expression(initializer):
            if item.symbol_id == _TARGET[4]:
                references.append(item)
            if item.kind != "assign":
                continue
            total += 1
            # A global initializer has no enclosing statement, so nothing
            # inside one can be statement-rooted: every assignment here is in
            # scope for the census, including one at the initializer root.
            if not _is_statement_rooted(parent, None, 0):
                located.append((path, item, parent, ()))
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for item, parent, path, chain, expression_index in _walk_statement(
                    statement, (index,)):
                if item.symbol_id == _TARGET[4]:
                    references.append(item)
                if item.kind != "assign":
                    continue
                total += 1
                if _is_statement_rooted(parent, chain[-1], expression_index):
                    continue
                if function is not owner:
                    raise _fail("rvalue assignment outside the owner function")
                located.append((path, item, parent, chain))
    if len(located) != _RVALUE_ASSIGN_CENSUS:
        raise _fail("rvalue assignment census cardinality mismatch: "
                    f"{len(located)}")
    if total != _TOTAL_ASSIGN_CENSUS:
        raise _fail(f"total assignment census mismatch: {total}")

    path, node, parent, chain = located[0]
    if len(node.children) != 2:
        raise _fail("rvalue assignment arity mismatch")
    target, operand = node.children

    # Value- and operator-level locks run AHEAD of node identity: `Symbol`
    # embeds its declaration span, so a mutation at this level also shifts the
    # enclosing node hashes, and a coarser ordering would let the hash absorb
    # the change and make these locks vacuous.
    if not _operator_holds(node):
        raise _fail("compound assignment operator mismatch")
    if not _operand_holds(operand):
        raise _fail("compound assignment operand mismatch")
    if not _target_holds(target):
        raise _fail("assignment target symbol mismatch")
    if not _node_identity_holds(node, target, operand):
        raise _fail("rvalue assignment node identity mismatch")
    if not _parent_holds(parent, node):
        raise _fail("rvalue assignment declaration parent mismatch")

    statement = owner.body[_OWNER_STATEMENT_INDEX]
    if not _ancestry_holds(path, chain, statement):
        raise _fail("rvalue assignment ancestry mismatch")
    if not _reference_census_holds(references, target):
        raise _fail("rot reference census mismatch")

    _check_ledger([owner, node, parent, target, operand, statement],
                  _CONSUMED_LEDGER, "rvalue-assign")
    return (node,)


def apply_shapes_rvalue_assign(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_shapes_rvalue_assign(program, source_hash, profile)
    return program
