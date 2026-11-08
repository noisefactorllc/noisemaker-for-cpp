"""Which GLSL float divisions the CPU authority lowers to Metal division.

The authority's kernel generator (scripts/upstream/compile-glsl.js) routes a
float division to ``$runtime.fdiv`` (src/csl/metal-division.js) only when its
divisor holds a run-time value after the GPU compiler folds constants. It
decides this from glsl-transpiler's scope records, not from GLSL semantics:

- the division is a float division (an int or ivec division is not routed);
- the divisor names a uniform or ``gl_FragCoord``, or a ``main`` or global
  variable whose initializer is run-time by the same rule;
- a name in a helper function's scope (a parameter or a local), or a ``main``
  or global variable without an initializer, makes the divisor unknown, and
  an unknown divisor keeps the float64 ``/``;
- ``const`` names and runtime define names are constants.

The transpiler keeps one scope per function, keyed by name, so a variable's
record is the most recent declaration of that name processed before the
division, in source order, whatever block declared it. A redeclaration
without an initializer keeps the previous initializer, and a declaration is
registered before its own initializer is processed.

Compound ``/=`` reaches the hook only for a whole vector divided by a scalar,
or for a swizzle target with two or more components; every other ``/=`` keeps
the float64 operator.

``metal_division_sites`` returns the binary ``/`` and compound ``/=`` nodes
that the authority routes. A census of every division of the 298 transpiled
programs at authority 7f473400 (the instrumented kernel generator against
this module) matched every routed and every unrouted site.

The authority also routes one division by source-guarded rewrite, outside the
rule above. compile-glsl.js's ``restoreCraquelureUintHash`` lowers
filter/craquelure's ``vec2 p = (gc + wob) / spacingPx;``, a division by
crackMask's parameter, to ``$runtime.fdiv(gc[i] + wob[i], spacingPx)``: the
Metal compile is ``a * rcp(spacingPx)``. That site is added here only for the
pinned craquelure source, by node identity.
"""

from __future__ import annotations

import hashlib

from .typed_ir import TypedExpression, TypedProgram, TypedStatement

FLOAT_TYPES = frozenset({"float", "vec2", "vec3", "vec4"})
VECTOR_TYPES = frozenset({"vec2", "vec3", "vec4"})

CRAQUELURE_KEY = "filter/craquelure:craquelure"
CRAQUELURE_SOURCE_SHA256 = "876e499ca270346151a873e74c744c884e96e9db7632a9341a0baf5107724d53"


class MetalDivisionSites:
    """Routed division nodes, compared by identity (typed IR nodes compare by value)."""

    __slots__ = ("nodes", "_ids")

    def __init__(self, nodes: tuple[TypedExpression, ...]) -> None:
        self.nodes = nodes
        self._ids = frozenset(id(node) for node in nodes)

    def __contains__(self, node: object) -> bool:
        return id(node) in self._ids

    def __len__(self) -> int:
        return len(self.nodes)


def _names(expression: TypedExpression | None, out: list[tuple[str, object]]) -> list[tuple[str, object]]:
    """Identifier references in source order, as the transpiled divisor text shows them."""
    if expression is None:
        return out
    if expression.kind == "id":
        out.append(("id", expression.symbol))
    elif expression.kind == "builtin" and expression.callee == "gl_FragCoord":
        out.append(("name", "gl_FragCoord"))
    for child in expression.children:
        _names(child, out)
    if expression.kind == "member":
        # `a.field` keeps the field name in the transpiled text.
        out.append(("name", expression.member))
    return out


class _Classifier:
    def __init__(self, program: TypedProgram) -> None:
        names = (getattr(item, "name", None) or (item[0] if isinstance(item, tuple) and item else None)
                 for item in program.preprocessor_defines)
        self.defines = frozenset(name for name in names if isinstance(name, str))
        self.globals: dict[str, tuple[object, TypedExpression | None]] = {}
        for declaration in program.declarations:
            self.globals[declaration.symbol.name] = (declaration.symbol, declaration.initializer)
        for symbol in program.interface_symbols + program.builtin_symbols:
            self.globals.setdefault(symbol.name, (symbol, None))
        self.program = program
        self.function = ""
        self.sites: list[TypedExpression] = []

    def _lookup(self, scope: dict, name: str):
        if name in scope:
            return scope[name], self.function
        if name in self.globals:
            return self.globals[name], "global"
        return None, None

    def _divisor_kind(self, expression: TypedExpression, scope: dict, stack: dict) -> str:
        kind = "constant"
        for tag, item in _names(expression, []):
            name = item.name if tag == "id" else item
            if name == "gl_FragCoord":
                kind = "runtime"
                continue
            if name in self.defines:
                continue
            entry, owner = self._lookup(scope, name)
            if entry is None:
                continue
            symbol, initializer = entry
            storage = getattr(symbol, "storage", None)
            if storage == "const":
                continue
            if storage == "uniform":
                kind = "runtime"
                continue
            if owner not in {"main", "global"} or initializer is None:
                return "unknown"
            if name not in stack:
                # A name already on the stack refers to itself.
                stack[name] = "unknown"
                stack[name] = self._divisor_kind(initializer, scope, stack)
            value = stack[name]
            if value == "unknown":
                return "unknown"
            if value == "runtime":
                kind = "runtime"
        return kind

    def _consider(self, node: TypedExpression, divisor: TypedExpression, scope: dict) -> None:
        if node.type.display() not in FLOAT_TYPES:
            return
        if self._divisor_kind(divisor, scope, {}) == "runtime":
            self.sites.append(node)

    def _expression(self, value: TypedExpression | None, scope: dict) -> None:
        if value is None:
            return
        if value.kind == "assign":
            target, right = value.children
            # The transpiler processes the assigned value before the target.
            self._expression(right, scope)
            self._expression(target, scope)
            if value.operator == "/=":
                if target.kind == "swizzle":
                    routed = len(target.member or "") > 1
                else:
                    routed = target.type.display() in VECTOR_TYPES and right.type.display() == "float"
                if routed:
                    self._consider(value, right, scope)
            return
        for child in value.children:
            self._expression(child, scope)
        if value.kind == "binary" and value.operator == "/":
            self._consider(value, value.children[1], scope)

    def _statement(self, value: TypedStatement, scope: dict) -> None:
        if value.kind == "decl":
            for declaration in value.expressions:
                name = declaration.symbol.name
                previous = scope.get(name)
                scope[name] = (declaration.symbol, previous[1] if previous else None)
                if declaration.children:
                    self._expression(declaration.children[0], scope)
                    scope[name] = (declaration.symbol, declaration.children[0])
            return
        if value.kind == "for":
            # for (init; condition; update) body: the transpiler processes them in that order.
            init = value.children[0] if value.children and value.children[0].kind == "decl" else None
            if init is not None:
                self._statement(init, scope)
            for expression in value.expressions:
                self._expression(expression, scope)
            for child in value.children:
                if child is not init:
                    self._statement(child, scope)
            return
        for expression in value.expressions:
            self._expression(expression, scope)
        for child in value.children:
            self._statement(child, scope)

    def run(self) -> MetalDivisionSites:
        for function in self.program.functions:
            self.function = function.name
            scope: dict = {parameter.name: (parameter, None) for parameter in function.parameters}
            for statement in function.body:
                self._statement(statement, scope)
        if self.program.key == CRAQUELURE_KEY and (
                hashlib.sha256(self.program.raw_source.encode("utf-8")).hexdigest()
                == CRAQUELURE_SOURCE_SHA256):
            self.sites.append(_craquelure_cell_division(self.program))
        return MetalDivisionSites(tuple(self.sites))


def _craquelure_cell_division(program: TypedProgram) -> TypedExpression:
    """The pinned craquelure's `(gc + wob) / spacingPx` node in crackMask."""
    functions = [item for item in program.functions if item.name == "crackMask"]
    if len(functions) != 1:
        raise ValueError(f"{CRAQUELURE_KEY}: crackMask identity drift")
    function = functions[0]
    parameters = {item.name: item for item in function.parameters}
    nodes: list[TypedExpression] = []

    def expression(value: TypedExpression) -> None:
        nodes.append(value)
        for child in value.children:
            expression(child)

    def statement(value: TypedStatement) -> None:
        for item in value.expressions:
            expression(item)
        for child in value.children:
            statement(child)

    for item in function.body:
        statement(item)
    divisions = [node for node in nodes if node.kind == "binary" and node.operator == "/"]
    matches = [
        node for node in divisions
        if node.type.display() == "vec2"
        and node.children[0].kind == "binary" and node.children[0].operator == "+"
        and tuple((child.kind, child.symbol.name if child.symbol else None)
                  for child in node.children[0].children) == (("id", "gc"), ("id", "wob"))
        and node.children[1].kind == "id"
        and node.children[1].type.display() == "float"
        and node.children[1].symbol is not None
        and node.children[1].symbol.name == "spacingPx"
        and node.children[1].symbol_id == getattr(parameters.get("spacingPx"), "id", None)]
    if len(matches) != 1:
        raise ValueError(f"{CRAQUELURE_KEY}: (gc + wob) / spacingPx division identity drift")
    return matches[0]


def metal_division_sites(program: TypedProgram) -> MetalDivisionSites:
    """The divisions of ``program`` that the authority lowers to ``$runtime.fdiv``."""
    return _Classifier(program).run()
