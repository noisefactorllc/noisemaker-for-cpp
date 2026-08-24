"""Strict body checker for the pinned GLSL ES fragment corpus.

The parser intentionally emits compact plain mappings.  This module is the
one place where those mappings acquire stable symbols, exact types and value
categories.  It deliberately has no evaluator or C++ code generation hooks.
"""

from __future__ import annotations

from dataclasses import replace

from .diagnostics import SemanticDiagnostic, SemanticError
from .constant_expr import evaluate_int_constant
from .semantic_types import BOOL, FLOAT, INT, UINT, VOID, Type, array, matrix, vector
from .span import SourceSpan
from .typed_ir import (FunctionSignature, ResourceRequirements, Symbol,
                       TypedDeclaration, TypedExpression, TypedFunction,
                       TypedProgram, TypedStatement)


_BUILTIN_IDS = {name: -(index + 1) for index, name in enumerate((
    "__array_length", "abs", "all", "any", "atan", "ceil", "clamp", "cos", "degrees",
    "dFdx", "dFdy", "distance", "dot", "equal", "exp", "floatBitsToUint",
    "floor", "fract", "fwidth", "greaterThanEqual", "inversesqrt", "length",
    "lessThan", "lessThanEqual", "log", "log2", "max", "min", "mix", "mod",
    "normalize", "notEqual", "packHalf2x16", "pow", "radians", "reflect",
    "refract", "round", "sign", "sin", "smoothstep", "sqrt", "step", "tanh",
    "texelFetch", "texture", "textureLod", "textureSize", "unpackHalf2x16",
))}

# Declarative GLSL ES builtin surface.  Names select a reusable signature
# family; matching itself is entirely family-driven in ``_builtin_family``.
_BUILTIN_FAMILIES = {
    "__array_length": ("array_length",), "abs": ("unary_numeric",),
    "all": ("bool_reduction",), "any": ("bool_reduction",), "atan": ("atan",),
    "ceil": ("unary_float",), "clamp": ("clamp",), "cos": ("unary_float",),
    "dFdx": ("derivative",), "dFdy": ("derivative",), "degrees": ("unary_float",),
    "distance": ("distance",), "dot": ("dot",), "equal": ("relational",),
    "exp": ("unary_float",), "floatBitsToUint": ("float_bits",),
    "floor": ("unary_float",), "fract": ("unary_float",), "fwidth": ("derivative",),
    "greaterThanEqual": ("relational",), "inversesqrt": ("unary_float",),
    "length": ("length",), "lessThan": ("relational",), "lessThanEqual": ("relational",),
    "log": ("unary_float",), "log2": ("unary_float",), "max": ("minmax",),
    "min": ("minmax",), "mix": ("mix",), "mod": ("mod",),
    "normalize": ("normalize",), "notEqual": ("relational",),
    "packHalf2x16": ("pack_half",), "pow": ("pow",), "radians": ("unary_float",),
    "reflect": ("reflect",), "refract": ("refract",), "round": ("unary_float",),
    "sign": ("unary_float",), "sin": ("unary_float",), "smoothstep": ("smoothstep",),
    "sqrt": ("unary_float",), "step": ("step",), "tanh": ("unary_float",),
    "texelFetch": ("texel_fetch",), "texture": ("texture",),
    "textureLod": ("texture_lod",), "textureSize": ("texture_size",),
    "unpackHalf2x16": ("unpack_half",),
}


def _scalar(t: Type, base: str | None = None) -> bool:
    return t.kind == "scalar" and (base is None or t.base == base)


def _numeric(t: Type) -> bool:
    return (_scalar(t) and t.base in {"int", "uint", "float"}) or (t.kind == "vector" and t.base in {"int", "uint", "float"})


def _integral(t: Type) -> bool:
    return (_scalar(t) and t.base in {"int", "uint"}) or (t.kind == "vector" and t.base in {"int", "uint"})


def _same_shape(a: Type, b: Type) -> bool:
    return a == b


def _span(spans: dict[tuple[object, ...], SourceSpan], path: tuple[object, ...], fallback: SourceSpan) -> SourceSpan:
    return spans.get(path, fallback)


class BodyAnalyzer:
    def __init__(self, parsed: dict, key: str, *, globals_: dict[str, Symbol],
                 signatures: dict[str, tuple[FunctionSignature, ...]],
                 structs: dict[str, tuple[Type, dict[str, Type]]],
                 resources: ResourceRequirements, next_id: int,
                 constants: dict[str, int]) -> None:
        self.parsed, self.key = parsed, key
        self.spans = dict(parsed.get("spans", ()))
        self.fallback = next(iter(self.spans.values()))
        self.globals = globals_
        self.signatures = signatures
        self.structs = structs
        self.resources = resources
        self.next_id = next_id
        self.constants = constants
        self.scopes: list[dict[str, Symbol]] = []
        self.constant_scopes: list[dict[str, int]] = []
        self.diagnostics: list[SemanticDiagnostic] = []
        self.uses_texture = False
        self.uses_derivatives = False

    def error(self, code: str, path: tuple[object, ...], message: str) -> None:
        self.diagnostics.append(SemanticDiagnostic(code, _span(self.spans, path, self.fallback), message))

    def symbol(self, name: str, path: tuple[object, ...]) -> Symbol | None:
        for scope in reversed(self.scopes):
            if name in scope: return scope[name]
        result = self.globals.get(name)
        if result is None: self.error("E_UNKNOWN_SYMBOL", path, f"unknown symbol {name}")
        return result

    def declare(self, name: str, typ: Type, storage: str, path: tuple[object, ...], writable: bool) -> Symbol:
        scope = self.scopes[-1]
        if name in scope:
            self.error("E_DUPLICATE_SYMBOL", path, f"duplicate symbol {name}")
        result = Symbol(self.next_id, name, typ, storage, _span(self.spans, path, self.fallback), writable)
        self.next_id += 1
        scope[name] = result
        return result

    def push_scope(self, symbols: dict[str, Symbol] | None = None) -> None:
        self.scopes.append({} if symbols is None else symbols)
        self.constant_scopes.append({})

    def pop_scope(self) -> None:
        self.scopes.pop()
        self.constant_scopes.pop()

    def expr(self, node: dict | None, path: tuple[object, ...]) -> TypedExpression:
        if node is None:
            return TypedExpression("void", VOID, _span(self.spans, path, self.fallback), "rvalue")
        kind = node["k"]
        loc = _span(self.spans, path, self.fallback)
        if kind == "num":
            value = node["value"]
            lower = value.lower()
            try:
                if lower.endswith("u"):
                    integer = int(lower[:-1], 0)
                    if not 0 <= integer <= 0xffffffff: raise ValueError
                    typ = UINT; typed_value = integer
                elif lower.startswith("0x"):
                    integer = int(lower, 0)
                    if lower.startswith("0x") and integer <= 0xffffffff:
                        typ = INT; typed_value = integer if integer <= 0x7fffffff else integer - 0x100000000
                    else: raise ValueError
                elif any(item in lower for item in (".", "e")):
                    typed_value = float(lower); typ = FLOAT
                else:
                    integer = int(lower, 0)
                    if -0x80000000 <= integer <= 0x7fffffff: typ = INT; typed_value = integer
                    else: raise ValueError
            except ValueError:
                self.error("E_LITERAL_RANGE", path, f"literal out of range {value}"); typ = INT
                typed_value = 0
            return TypedExpression("literal", typ, loc, "rvalue", literal=value, literal_value=typed_value)
        if kind == "bool": return TypedExpression("literal", BOOL, loc, "rvalue", literal=node["value"], literal_value=node["value"])
        if kind == "id":
            symbol = self.symbol(node["name"], path)
            if symbol is None: return TypedExpression("id", FLOAT, loc, "rvalue")
            category = "lvalue" if symbol.writable else "readonly lvalue"
            return TypedExpression("id", symbol.type, loc, category, symbol_id=symbol.id, symbol=symbol)
        if kind == "construct":
            args = tuple(self.expr(value, path + ("args", index)) for index, value in enumerate(node["args"]))
            target = (array(self.type_of(node["type"], None, path), len(args))
                      if node.get("array") is True else self.type_of(node["type"], node.get("array"), path))
            self.constructor(target, args, path)
            return TypedExpression("construct", target, loc, "rvalue", children=args, constructor_type=target)
        if kind == "member":
            obj = self.expr(node["obj"], path + ("obj",))
            field = node["field"]
            if obj.type.kind == "vector":
                families = [set("xyzw"), set("rgba"), set("stpq")]
                family = next((item for item in families if set(field) <= item), None)
                if family is None or not field or any("xyzwrgba stpq".replace(" ", "").index(ch) < 0 for ch in field):
                    self.error("E_FIELD", path, f"invalid vector swizzle {field}"); typ = FLOAT
                else:
                    alphabet = "xyzw" if family == set("xyzw") else "rgba" if family == set("rgba") else "stpq"
                    if any(alphabet.index(ch) >= (obj.type.width or 0) for ch in field):
                        self.error("E_FIELD", path, f"swizzle {field} exceeds vector width"); typ = FLOAT
                    else: typ = vector(obj.type.base or "float", len(field)) if len(field) > 1 else Type("scalar", obj.type.base)
                writable = obj.category == "lvalue" and len(set(field)) == len(field)
                category = "lvalue" if writable else "readonly lvalue" if obj.category != "rvalue" else "rvalue"
                return TypedExpression("swizzle", typ, loc, category, children=(obj,), member=field)
            fields = self.structs.get(obj.type.name or "", (None, {}))[1] if obj.type.kind == "struct" else {}
            typ = fields.get(field)
            if typ is None:
                self.error("E_UNKNOWN_FIELD", path, f"unknown field {field}"); typ = FLOAT
            category = obj.category if obj.category != "rvalue" else "rvalue"
            return TypedExpression("member", typ, loc, category, children=(obj,), member=field)
        if kind == "index":
            obj, index = self.expr(node["obj"], path + ("obj",)), self.expr(node["idx"], path + ("idx",))
            if not _scalar(index.type) or index.type.base not in {"int", "uint"}:
                self.error("E_INDEX", path + ("idx",), "index must be scalar int or uint")
            if obj.type.kind == "array": typ = obj.type.element or FLOAT
            elif obj.type.kind == "vector": typ = Type("scalar", obj.type.base)
            elif obj.type.kind == "matrix": typ = vector("float", obj.type.rows or 1)
            else:
                self.error("E_INDEX", path, "indexing requires array, vector, or matrix"); typ = FLOAT
            constant_index = self.constant_int(node["idx"], path + ("idx",))
            bound = obj.type.size if obj.type.kind == "array" else obj.type.width if obj.type.kind == "vector" else obj.type.columns if obj.type.kind == "matrix" else None
            if constant_index is not None and bound is not None and not 0 <= constant_index < bound:
                self.error("E_INDEX_BOUNDS", path + ("idx",), f"constant index {constant_index} is outside [0, {bound})")
            return TypedExpression("index", typ, loc, obj.category if obj.category != "rvalue" else "rvalue", children=(obj, index))
        if kind == "unary":
            x = self.expr(node["x"], path + ("x",)); op = node["op"]
            if op in {"++", "--"}:
                self.require_writable(x, path); self.require_numeric(x.type, path)
            elif op == "!":
                if not (_scalar(x.type, "bool") or (x.type.kind == "vector" and x.type.base == "bool")): self.error("E_OPERATOR", path, f"! does not accept {x.type.display()}")
            elif op == "~":
                if not _integral(x.type): self.error("E_OPERATOR", path, f"~ does not accept {x.type.display()}")
            else: self.require_numeric(x.type, path)
            return TypedExpression("unary", x.type, loc, "rvalue", children=(x,), operator=op)
        if kind == "post":
            x = self.expr(node["x"], path + ("x",)); self.require_writable(x, path); self.require_numeric(x.type, path)
            return TypedExpression("post", x.type, loc, "rvalue", children=(x,), operator=node["op"])
        if kind == "binary":
            left, right = self.expr(node["l"], path + ("l",)), self.expr(node["r"], path + ("r",))
            typ = self.binary(node["op"], left.type, right.type, path)
            return TypedExpression("binary", typ, loc, "rvalue", children=(left, right), operator=node["op"])
        if kind == "assign":
            target, value = self.expr(node["target"], path + ("target",)), self.expr(node["value"], path + ("value",))
            self.require_writable(target, path + ("target",))
            if node["op"] == "=":
                if target.type != value.type: self.error("E_TYPE", path, f"assignment requires {target.type.display()}, got {value.type.display()}")
            else:
                result = self.binary(node["op"][:-1], target.type, value.type, path)
                if result != target.type: self.error("E_TYPE", path, "compound assignment changes target type")
            return TypedExpression("assign", target.type, loc, "rvalue", children=(target, value), operator=node["op"])
        if kind == "cond":
            c, a, b = self.expr(node["c"], path + ("c",)), self.expr(node["a"], path + ("a",)), self.expr(node["b"], path + ("b",))
            if c.type != BOOL: self.error("E_CONDITION", path + ("c",), "conditional condition must be bool")
            if a.type != b.type: self.error("E_TYPE", path, "conditional arms must have exactly the same type")
            return TypedExpression("conditional", a.type, loc, "rvalue", children=(c, a, b))
        if kind == "call":
            args = tuple(self.expr(value, path + ("args", index)) for index, value in enumerate(node["args"]))
            return self.call(node["name"], args, path)
        self.error("E_AST", path, f"unsupported expression {kind}")
        return TypedExpression("invalid", FLOAT, loc, "rvalue")

    def type_of(self, name: str, extent: object, path: tuple[object, ...]) -> Type:
        from .semantic_types import named_type
        structs = {key: item[0] for key, item in self.structs.items()}
        result = named_type(name, structs)
        if result is None:
            self.error("E_UNKNOWN_TYPE", path, f"unknown type {name}"); result = FLOAT
        if extent is not None:
            value = self.constant_int(extent, path)
            if value is None or value <= 0: self.error("E_ARRAY_SIZE", path, "array dimension must be positive constant int"); value = 1
            result = array(result, value)
        return result

    def constant_int(self, node: object, path: tuple[object, ...]) -> int | None:
        def lookup(name: str) -> int | None:
            for scope in reversed(self.constant_scopes):
                if name in scope: return scope[name]
            return self.constants.get(name)
        return evaluate_int_constant(node, lookup)

    def constructor(self, target: Type, args: tuple[TypedExpression, ...], path: tuple[object, ...]) -> None:
        types = tuple(item.type for item in args)
        if target.kind == "scalar":
            if len(types) != 1 or not _scalar(types[0]): self.error("E_CONSTRUCTOR", path, f"{target.display()} requires one scalar")
        elif target.kind == "vector":
            if len(types) == 1 and (_scalar(types[0]) or types[0].kind == "vector"):
                if _scalar(types[0]) or (types[0].width or 0) >= (target.width or 0): return
            if len(types) == 1 and types[0].kind == "matrix" and (types[0].columns or 0) * (types[0].rows or 0) == target.width: return
            count = sum(1 if _scalar(item) else item.width or 0 if item.kind == "vector" else (item.columns or 0) * (item.rows or 0) if item.kind == "matrix" else -999 for item in types)
            if count != target.width or any(not (_scalar(item) or item.kind in {"vector", "matrix"}) for item in types): self.error("E_CONSTRUCTOR", path, f"invalid {target.display()} constructor")
        elif target.kind == "matrix":
            total = (target.columns or 0) * (target.rows or 0)
            if len(types) == 1 and types[0] == FLOAT: return
            if len(types) == 1 and types[0].kind == "matrix" and types[0].base == "float": return
            if sum(1 if item == FLOAT else item.width or 0 if item.kind == "vector" and item.base == "float" else -999 for item in types) != total: self.error("E_CONSTRUCTOR", path, f"invalid {target.display()} constructor")
        elif target.kind == "array":
            if len(types) != target.size or any(item != target.element for item in types): self.error("E_CONSTRUCTOR", path, "array constructor arguments must exactly match element type and count")
        elif target.kind == "struct":
            fields = self.structs.get(target.name or "", (target, {}))[1]
            if len(types) != len(fields) or any(left != right for left, right in zip(types, fields.values())): self.error("E_CONSTRUCTOR", path, f"invalid {target.display()} constructor")

    def require_writable(self, expression: TypedExpression, path: tuple[object, ...]) -> None:
        if expression.category != "lvalue": self.error("E_NOT_WRITABLE", path, "expression is not a writable lvalue")

    def require_numeric(self, typ: Type, path: tuple[object, ...]) -> None:
        if not _numeric(typ): self.error("E_OPERATOR", path, f"numeric operand required, got {typ.display()}")

    def binary(self, op: str, left: Type, right: Type, path: tuple[object, ...]) -> Type:
        if op in {"&&", "||"}:
            if left != BOOL or right != BOOL: self.error("E_OPERATOR", path, f"{op} requires bool operands")
            return BOOL
        if op in {"==", "!="}:
            if left != right: self.error("E_TYPE", path, "comparison requires exact operand types")
            return BOOL
        if op in {"<", ">", "<=", ">="}:
            if left != right or not (_scalar(left) and left.base in {"int", "uint", "float"}): self.error("E_OPERATOR", path, "ordered comparison requires same scalar numeric types")
            return BOOL
        if op in {"&", "|", "^", "<<", ">>"}:
            if not _integral(left) or not _integral(right) or (left.kind == "vector" and not _scalar(right) and left != right) or (right.kind == "vector" and not _scalar(left) and left != right): self.error("E_OPERATOR", path, f"{op} requires integral operands of compatible shape")
            return left
        if op == "%":
            if left != right or not _integral(left): self.error("E_OPERATOR", path, "% requires same integral operands")
            return left
        if op in {"+", "-", "/"}:
            if left == right and (_numeric(left) or left.kind == "matrix"): return left
            if left.kind == "vector" and right == Type("scalar", left.base): return left
            if right.kind == "vector" and left == Type("scalar", right.base): return right
            if left.kind == "matrix" and right == FLOAT: return left
            if right.kind == "matrix" and left == FLOAT: return right
            self.error("E_OPERATOR", path, f"invalid {op} operands {left.display()} and {right.display()}"); return left
        if op == "*":
            if left == right and _numeric(left): return left
            if left.kind == "vector" and right == Type("scalar", left.base): return left
            if right.kind == "vector" and left == Type("scalar", right.base): return right
            if left.kind == "matrix" and right == FLOAT or right.kind == "matrix" and left == FLOAT: return left if left.kind == "matrix" else right
            if left.kind == "matrix" and right.kind == "vector" and left.columns == right.width: return vector("float", left.rows or 1)
            if left.kind == "vector" and right.kind == "matrix" and left.width == right.rows: return vector("float", right.columns or 1)
            if left.kind == "matrix" and right.kind == "matrix" and left.columns == right.rows: return matrix(right.columns or 1, left.rows or 1)
            self.error("E_OPERATOR", path, f"invalid matrix/vector multiplication"); return left
        self.error("E_OPERATOR", path, f"unknown operator {op}"); return left

    def call(self, name: str | None, args: tuple[TypedExpression, ...], path: tuple[object, ...]) -> TypedExpression:
        loc = _span(self.spans, path, self.fallback)
        candidates = [item for item in self.signatures.get(name or "", ()) if len(item.parameters) == len(args)]
        exact = []
        for item in candidates:
            valid = True
            for parameter, argument in zip(item.parameters, args):
                if parameter.type != argument.type: valid = False
                if parameter.direction in {"out", "inout"} and argument.category != "lvalue": valid = False
            if valid: exact.append(item)
        if exact:
            if len(exact) != 1:
                self.error("E_AMBIGUOUS_CALL", path, f"ambiguous overload {name}")
            signature = exact[0]
            return TypedExpression("call", signature.return_type, loc, "rvalue", signature_id=signature.id, children=args, callee=name)
        builtin = self.builtin(name or "", args, path)
        if builtin is not None: return TypedExpression("builtin", builtin, loc, "rvalue", signature_id=_BUILTIN_IDS[name], children=args, callee=name)
        self.error("E_NO_OVERLOAD", path, f"no exact overload for {name}")
        return TypedExpression("call", FLOAT, loc, "rvalue", children=args, callee=name)

    def builtin(self, name: str, args: tuple[TypedExpression, ...], path: tuple[object, ...]) -> Type | None:
        families = _BUILTIN_FAMILIES.get(name)
        if families is None: return None
        types = tuple(item.type for item in args)
        for family in families:
            result = self._builtin_family(family, types)
            if result is not None:
                if family == "derivative": self.uses_derivatives = True
                if family in {"texture", "texture_lod", "texel_fetch", "texture_size"}: self.uses_texture = True
                return result
        return None

    @staticmethod
    def _builtin_family(family: str, types: tuple[Type, ...]) -> Type | None:
        float_gen = lambda typ: _scalar(typ, "float") or (typ.kind == "vector" and typ.base == "float")
        numeric_gen = lambda typ: (_scalar(typ) and typ.base in {"int", "uint", "float"}) or (typ.kind == "vector" and typ.base in {"int", "uint", "float"})
        if family == "array_length": return INT if len(types) == 1 and types[0].kind == "array" else None
        if family == "unary_numeric": return types[0] if len(types) == 1 and numeric_gen(types[0]) else None
        if family == "unary_float": return types[0] if len(types) == 1 and float_gen(types[0]) else None
        if family == "bool_reduction": return BOOL if len(types) == 1 and types[0].kind == "vector" and types[0].base == "bool" else None
        if family == "atan": return types[0] if len(types) in {1, 2} and all(float_gen(item) for item in types) and (len(types) == 1 or types[0] == types[1]) else None
        if family == "minmax":
            if len(types) != 2: return None
            if types[0] == types[1] and numeric_gen(types[0]): return types[0]
            return types[0] if types[0].kind == "vector" and numeric_gen(types[0]) and types[1] == Type("scalar", types[0].base) else None
        if family == "mod":
            if len(types) != 2: return None
            if types[0] == types[1] and float_gen(types[0]): return types[0]
            return types[0] if types[0].kind == "vector" and types[0].base == "float" and types[1] == FLOAT else None
        if family == "pow": return types[0] if len(types) == 2 and types[0] == types[1] and float_gen(types[0]) else None
        if family == "step":
            if len(types) != 2: return None
            if types[0] == types[1] and float_gen(types[0]): return types[0]
            return types[1] if types[0] == FLOAT and types[1].kind == "vector" and types[1].base == "float" else None
        if family == "clamp":
            if len(types) != 3: return None
            if types[0] == types[1] == types[2] and numeric_gen(types[0]): return types[0]
            return types[0] if types[0].kind == "vector" and numeric_gen(types[0]) and types[1] == types[2] == Type("scalar", types[0].base) else None
        if family == "smoothstep":
            if len(types) != 3: return None
            if types[0] == types[1] == types[2] and float_gen(types[0]): return types[0]
            return types[2] if types[2].kind == "vector" and types[2].base == "float" and types[0] == types[1] == FLOAT else None
        if family == "mix":
            if len(types) != 3 or types[0] != types[1] or not float_gen(types[0]): return None
            if types[2] in {FLOAT, types[0]}: return types[0]
            return types[0] if types[0].kind == "vector" and types[2] == vector("bool", types[0].width or 1) else None
        if family == "length": return FLOAT if len(types) == 1 and float_gen(types[0]) else None
        if family == "distance": return FLOAT if len(types) == 2 and types[0] == types[1] and float_gen(types[0]) else None
        if family == "dot": return FLOAT if len(types) == 2 and types[0] == types[1] and types[0].kind == "vector" and types[0].base == "float" else None
        if family == "normalize": return types[0] if len(types) == 1 and types[0].kind == "vector" and types[0].base == "float" else None
        if family == "reflect": return types[0] if len(types) == 2 and types[0] == types[1] and float_gen(types[0]) else None
        if family == "refract": return types[0] if len(types) == 3 and types[0] == types[1] and float_gen(types[0]) and types[2] == FLOAT else None
        if family == "relational": return vector("bool", types[0].width or 1) if len(types) == 2 and types[0] == types[1] and types[0].kind == "vector" else None
        if family == "derivative": return types[0] if len(types) == 1 and float_gen(types[0]) else None
        if family == "float_bits":
            if len(types) != 1: return None
            return UINT if types[0] == FLOAT else vector("uint", types[0].width or 1) if types[0].kind == "vector" and types[0].base == "float" else None
        if family == "pack_half": return UINT if types == (vector("float", 2),) else None
        if family == "unpack_half": return vector("float", 2) if types == (UINT,) else None
        if family == "texture": return vector("float", 4) if len(types) == 2 and types[0].kind == "sampler" and types[1] == vector("float", 2) else None
        if family == "texture_lod": return vector("float", 4) if len(types) == 3 and types[0].kind == "sampler" and types[1] == vector("float", 2) and types[2] == FLOAT else None
        if family == "texel_fetch": return vector("float", 4) if len(types) == 3 and types[0].kind == "sampler" and types[1] == vector("int", 2) and types[2] == INT else None
        if family == "texture_size": return vector("int", 2) if len(types) == 2 and types[0].kind == "sampler" and types[1] == INT else None
        raise AssertionError(f"unregistered builtin family {family}")

    def statement(self, node: dict, path: tuple[object, ...], return_type: Type, loop_depth: int = 0) -> TypedStatement:
        kind = node["k"]; loc = _span(self.spans, path, self.fallback)
        if kind == "block":
            self.push_scope(); children = tuple(self.statement(value, path + ("body", index), return_type, loop_depth) for index, value in enumerate(node["body"])); self.pop_scope()
            return TypedStatement("block", loc, children=children)
        if kind == "decl":
            declarations = []
            for index, item in enumerate(node["declarators"]):
                item_path = path + ("declarators", index); typ = self.type_of(node["type"], item.get("array"), item_path)
                initializer = self.expr(item["init"], item_path + ("init",)) if item.get("init") is not None else None
                if initializer and initializer.type != typ: self.error("E_TYPE", item_path, f"initializer requires {typ.display()}, got {initializer.type.display()}")
                if "const" in node["quals"] and (initializer is None or not self._constant_expression(initializer)):
                    self.error("E_CONST_INITIALIZER", item_path, "const initializer must be a constant expression")
                symbol = self.declare(item["name"], typ, "const" if "const" in node["quals"] else "local", item_path, "const" not in node["quals"])
                if "const" in node["quals"] and typ == INT and item.get("init") is not None:
                    value = self.constant_int(item["init"], item_path + ("init",))
                    if value is not None: self.constant_scopes[-1][item["name"]] = value
                declarations.append(TypedExpression("declaration", typ, symbol.span, "rvalue", symbol_id=symbol.id, children=() if initializer is None else (initializer,), symbol=symbol))
            return TypedStatement("decl", loc, tuple(declarations))
        if kind == "expr": return TypedStatement("expr", loc, (self.expr(node["expr"], path + ("expr",)),))
        if kind == "if":
            condition = self.expr(node["cond"], path + ("cond",));
            if condition.type != BOOL: self.error("E_CONDITION", path + ("cond",), "if condition must be bool")
            self.push_scope()
            then = self.statement(node["then"], path + ("then",), return_type, loop_depth)
            self.pop_scope()
            els = None
            if node.get("els"):
                self.push_scope()
                els = self.statement(node["els"], path + ("els",), return_type, loop_depth)
                self.pop_scope()
            return TypedStatement("if", loc, (condition,), (then,) if els is None else (then, els))
        if kind in {"while", "dowhile"}:
            condition = self.expr(node["cond"], path + ("cond",));
            if condition.type != BOOL: self.error("E_CONDITION", path + ("cond",), "loop condition must be bool")
            body = self.statement(node["body"], path + ("body",), return_type, loop_depth + 1)
            return TypedStatement(kind, loc, (condition,), (body,))
        if kind == "for":
            self.push_scope(); init = self.statement(node["init"], path + ("init",), return_type, loop_depth) if node.get("init") else None
            condition = self.expr(node["cond"], path + ("cond",)) if node.get("cond") else None
            if condition and condition.type != BOOL: self.error("E_CONDITION", path + ("cond",), "for condition must be bool")
            update = self.expr(node["update"], path + ("update",)) if node.get("update") else None
            body = self.statement(node["body"], path + ("body",), return_type, loop_depth + 1); self.pop_scope()
            return TypedStatement("for", loc, tuple(item for item in (condition, update) if item), tuple(item for item in (init, body) if item))
        if kind == "return":
            value = self.expr(node["value"], path + ("value",)) if node.get("value") else None
            if (value is None and return_type != VOID) or (value is not None and value.type != return_type): self.error("E_RETURN", path, "return value does not exactly match function type")
            return TypedStatement("return", loc, () if value is None else (value,))
        if kind in {"break", "continue"}:
            if loop_depth == 0: self.error("E_LOOP_CONTROL", path, f"{kind} outside loop")
            return TypedStatement(kind, loc)
        if kind == "discard": return TypedStatement("discard", loc)
        self.error("E_AST", path, f"unsupported statement {kind}"); return TypedStatement("invalid", loc)

    def functions(self, definitions: list[tuple[dict, FunctionSignature, tuple[Symbol, ...], tuple[object, ...]]]) -> tuple[TypedFunction, ...]:
        result = []
        for node, signature, parameters, path in definitions:
            if node["k"] == "proto":
                result.append(TypedFunction(signature, _span(self.spans, path, self.fallback)))
                continue
            self.push_scope({parameter.name: parameter for parameter in parameters})
            body = tuple(self.statement(statement, path + ("body", index), signature.return_type) for index, statement in enumerate(node["body"]))
            self.pop_scope()
            result.append(TypedFunction(signature, _span(self.spans, path, self.fallback), body))
        return tuple(result)

    def _constant_expression(self, expression: TypedExpression) -> bool:
        """GLSL global/const initializer predicate over typed IR only."""
        if expression.kind == "literal": return True
        if expression.kind == "id":
            return expression.symbol is not None and expression.symbol.storage == "const"
        if expression.kind in {"construct", "unary", "binary", "conditional", "swizzle", "member", "index"}:
            return all(self._constant_expression(child) for child in expression.children)
        return False

    def global_initializers(self, ast: dict) -> dict[int, TypedExpression]:
        """Analyze source globals in declaration order and retain their IR.

        All globals, including non-const globals, require a constant expression
        in GLSL ES.  The visible namespace is intentionally grown only after a
        declarator initializer is checked, preserving shadow/order semantics.
        """
        all_globals = self.globals
        visible = {name: symbol for name, symbol in all_globals.items()
                   if symbol.storage in {"builtin", "varying"}}
        self.globals = visible
        result: dict[int, TypedExpression] = {}
        for declaration_index, node in enumerate(ast["decls"]):
            if node["k"] == "decl":
                for declarator_index, declarator in enumerate(node["declarators"]):
                    name = declarator["name"]
                    symbol = all_globals.get(name)
                    path = ("decls", declaration_index, "declarators", declarator_index)
                    initializer = declarator.get("init")
                    if initializer is not None:
                        typed = self.expr(initializer, path + ("init",))
                        if symbol is not None and typed.type != symbol.type:
                            self.error("E_TYPE", path, f"initializer requires {symbol.type.display()}, got {typed.type.display()}")
                        if not self._constant_expression(typed):
                            self.error("E_CONST_INITIALIZER", path, "global initializer must be a constant expression")
                        if symbol is not None: result[symbol.id] = typed
                    if symbol is not None: visible[name] = symbol
            elif node["k"] == "struct" and node.get("inst"):
                symbol = all_globals.get(node["inst"])
                if symbol is not None: visible[symbol.name] = symbol
            elif node["k"] == "ubo":
                if node.get("inst"):
                    symbol = all_globals.get(node["inst"])
                    if symbol is not None: visible[symbol.name] = symbol
                else:
                    for member in node["members"]:
                        symbol = all_globals.get(member["name"])
                        if symbol is not None: visible[symbol.name] = symbol
        self.globals = all_globals
        return result
