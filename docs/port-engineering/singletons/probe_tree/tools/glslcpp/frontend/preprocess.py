"""GLSL preprocessing + light normalization (pure Python).

Reproduces the parts of the reference JS pipeline (glsl-normalize.js + prepr)
that matter for the Python codegen:
  - strip `#version`
  - object-like `#define` expansion
  - `#ifdef`/`#ifndef`/`#if`/`#elif`/`#else`/`#endif`: static conditions are
    evaluated; conditions on a *runtime define* are lowered into real GLSL
    `if/else` fed by a uniform of that name
  - capture `out vec4 X;` -> global `vec4 X;` + record X in outputs
  - capture `in vecN Y;` varyings (dropped; codegen maps them to ctx.uv)

Unlike the JS normalizer we do NOT rewrite `uint`/`uvec`->`int`/`vec`: the Python
codegen handles unsigned types natively via the bit-exact uintmath runtime.
"""

from __future__ import annotations

import re

_IDENT = re.compile(r"\b[A-Za-z_]\w*\b")
_DEFINE = re.compile(r"define\s+(\w+)(?:\(|\s|$)")


class PreprocessError(ValueError):
    def __init__(self, message: str, line: int | None = None, column: int = 1) -> None:
        self.line = line
        self.column = column
        super().__init__(message)


def _strip_comments(source: str) -> str:
    """Remove block and line comments before preprocessing. The tokenizer strips
    comments too, but the preprocessor runs first on raw text — a `//` comment
    trailing a `#define` value (e.g. `#define MAX_PAIRS 32  // ...`) would
    otherwise be captured into the macro and comment out every later expansion.
    GLSL has no string literals, so this is unambiguous."""
    source = re.sub(r"/\*.*?\*/", " ", source, flags=re.DOTALL)
    source = re.sub(r"//[^\n]*", "", source)
    return source


def normalize(source: str, runtime_defines: dict | None = None) -> dict:
    runtime_defines = runtime_defines or {}
    body = _preprocess(_strip_comments(source), runtime_defines)

    out_lines = []
    outputs = []
    varyings = []
    varying_types = {}
    for line in body.split("\n"):
        m = re.match(r"\s*out\s+(\w+)\s+(\w+)\s*;\s*$", line)
        if m:
            outputs.append(m.group(2))
            out_lines.append(f"{m.group(1)} {m.group(2)};")
            continue
        m = re.match(r"\s*(?:flat\s+)?in\s+(\w+)\s+(\w+)\s*;\s*$", line)
        if m:
            varyings.append(m.group(2))
            varying_types[m.group(2)] = m.group(1)
            continue  # codegen maps varyings to ctx.uv
        out_lines.append(line)

    # Declare runtime-define uniforms (they were lowered to runtime branches).
    decls = "".join(f"uniform {'float' if t == 'float' else 'int'} {name};\n"
                    for name, t in runtime_defines.items() if isinstance(t, str))
    return {"source": decls + "\n".join(out_lines), "outputs": outputs or ["fragColor"],
            "varyings": varyings, "varying_types": varying_types}


def _preprocess(source: str, runtime_defines: dict) -> list:
    out = []
    # Literal values select an audited metadata default at preprocessing time;
    # only string ``int``/``float`` entries describe dynamic uniform defines.
    defines: dict[str, str] = {name: ("true" if value else "false") if isinstance(value, bool) else str(value)
                               for name, value in runtime_defines.items()
                               if isinstance(value, (int, float, bool))}
    dynamic_defines = {name: value for name, value in runtime_defines.items() if isinstance(value, str)}
    stack = []  # frames: {"kind": "static"|"runtime"|"include_all", "active", "taken", "outer"}
    depth = [0]  # brace nesting of emitted content; list for closure mutation

    def emitting():
        return all(f["active"] for f in stack)

    def emit(line):
        out.append(line)
        depth[0] += line.count("{") - line.count("}")

    def evaluated(directive: str, head: str, line: int, outer: bool) -> bool:
        if not outer:
            return False
        try:
            return _eval(directive, head, defines, runtime_defines)
        except PreprocessError as error:
            raise PreprocessError(str(error), line) from error

    for line_number, raw in enumerate(source.split("\n"), start=1):
        s = raw.strip()
        if s.startswith("#"):
            d = s[1:].strip()
            head = d.split()[0] if d else ""
            if head == "version" or head in ("extension", "pragma", "line"):
                continue
            if head == "define":
                if emitting() and not re.match(r"define\s+\w+\(", d):  # object-like only
                    m = re.match(r"define\s+(\w+)(?:\s+(.*))?$", d)
                    if m:
                        defines[m.group(1)] = (m.group(2) or "").strip()
                continue
            if head == "undef":
                if emitting():
                    defines.pop(d.split()[1], None)
                continue
            if head in ("ifdef", "ifndef", "if"):
                outer = emitting()
                if outer and _cond_runtime(d, head, dynamic_defines):
                    if depth[0] == 0:
                        # A runtime #if at global scope gates whole declarations
                        # (e.g. conditionally-compiled functions), which can't be
                        # a runtime `if`. Include ALL branches — the transpiled
                        # functions are uniquely named and dispatched at runtime
                        # by a separate statement-scope #if.
                        stack.append({"kind": "include_all", "active": True, "taken": True, "outer": outer, "line": line_number, "else_seen": False})
                    else:
                        emit(f"if ({_glsl_cond(d, head, defines)}) {{")
                        stack.append({"kind": "runtime", "active": True, "taken": True, "outer": outer, "line": line_number, "else_seen": False})
                else:
                    val = evaluated(d, head, line_number, outer)
                    stack.append({"kind": "static", "active": outer and val, "taken": val, "outer": outer, "line": line_number, "else_seen": False})
                continue
            if head == "elif":
                if not stack:
                    raise PreprocessError("#elif without matching conditional", line_number)
                fr = stack[-1]
                if fr["else_seen"]:
                    raise PreprocessError("#elif after #else", line_number)
                if fr["kind"] == "include_all":
                    pass  # every branch is emitted
                elif fr["kind"] == "runtime":
                    emit(f"}} else if ({_glsl_cond(d, 'if', defines)}) {{")
                    fr["active"] = True
                else:
                    if fr["taken"]:
                        fr["active"] = False
                    else:
                        val = evaluated(d, "if", line_number, fr["outer"])
                        fr["active"] = fr["outer"] and val
                        fr["taken"] = fr["taken"] or val
                continue
            if head == "else":
                if not stack:
                    raise PreprocessError("#else without matching conditional", line_number)
                fr = stack[-1]
                if fr["else_seen"]:
                    raise PreprocessError("duplicate #else", line_number)
                fr["else_seen"] = True
                if fr["kind"] == "include_all":
                    pass
                elif fr["kind"] == "runtime":
                    emit("} else {")
                    fr["active"] = True
                else:
                    fr["active"] = fr["outer"] and (not fr["taken"])
                    fr["taken"] = True
                continue
            if head == "endif":
                if not stack:
                    raise PreprocessError("#endif without matching conditional", line_number)
                fr = stack.pop()
                if fr["kind"] == "runtime":
                    emit("}")
                continue
            raise PreprocessError(f"unsupported directive: {head or d}", line_number)
        if emitting():
            emit(_expand(raw, defines))
    if stack:
        raise PreprocessError("unterminated conditional directive", stack[-1]["line"])
    return "\n".join(out)


def _expand(line: str, defines: dict) -> str:
    if not defines:
        return line
    for _ in range(16):
        changed = False

        def repl(m):
            nonlocal changed
            name = m.group(0)
            if name in defines:
                changed = True
                return defines[name]
            return name

        new = _IDENT.sub(repl, line)
        line = new
        if not changed:
            break
    return line


def _cond_runtime(directive: str, head: str, runtime_defines: dict) -> bool:
    # #ifdef/#ifndef are about DEFINEDNESS: a runtime define is always "defined"
    # (bound as a uniform), so those resolve statically. Only `#if <expr on the
    # value>` needs runtime lowering.
    if not runtime_defines or head in ("ifdef", "ifndef"):
        return False
    return any(rd in set(_IDENT.findall(directive)) for rd in runtime_defines)


def _strip_kw(directive: str) -> str:
    return re.sub(r"^(elif|ifdef|ifndef|if)\b\s*", "", directive).strip()


def _glsl_cond(directive: str, head: str, defines: dict) -> str:
    if head == "ifdef":
        return "true"
    if head == "ifndef":
        return "false"
    return _expand(_strip_kw(directive), defines)


def _eval(directive: str, head: str, defines: dict, runtime_defines: dict | None = None) -> bool:
    runtime_defines = runtime_defines or {}
    if head == "ifdef":
        n = directive.split()[1]
        return n in defines or n in runtime_defines
    if head == "ifndef":
        n = directive.split()[1]
        return n not in defines and n not in runtime_defines
    expr = _strip_kw(directive)
    expr = re.sub(r"defined\s*\(\s*(\w+)\s*\)", lambda m: "1" if m.group(1) in defines else "0", expr)
    expr = re.sub(r"defined\s+(\w+)", lambda m: "1" if m.group(1) in defines else "0", expr)
    expr = _expand(expr, defines)
    # Undefined identifiers are zero in GLSL's preprocessor.  Evaluate the
    # remaining tiny integer expression with a parser, never Python eval.
    expr = _IDENT.sub(lambda m: m.group(0) if m.group(0) in ("true", "false") else "0", expr)
    tokens = re.findall(r"0[xX][0-9A-Fa-f]+|\d+|&&|\|\||==|!=|<=|>=|[()!<>+\-*/%]", expr)
    if "".join(tokens) != re.sub(r"\s+", "", expr):
        raise PreprocessError(f"invalid conditional expression: {expr}")
    index = 0

    def primary():
        nonlocal index
        if index >= len(tokens):
            raise PreprocessError("incomplete conditional expression")
        token = tokens[index]
        if token == "!":
            index += 1
            return 0 if primary() else 1
        if token == "(":
            index += 1
            value = logical_or()
            if index >= len(tokens) or tokens[index] != ")":
                raise PreprocessError("unclosed conditional parenthesis")
            index += 1
            return value
        if token in ("true", "false"):
            index += 1
            return int(token == "true")
        try:
            value = int(token, 0)
        except ValueError as error:
            raise PreprocessError(f"invalid conditional token: {token}") from error
        index += 1
        return value

    def product():
        nonlocal index
        value = primary()
        while index < len(tokens) and tokens[index] in ("*", "/", "%"):
            operator = tokens[index]; index += 1; right = primary()
            if operator == "*": value *= right
            elif operator == "/": value = 0 if right == 0 else int(value / right)
            else: value = 0 if right == 0 else value % right
        return value

    def sum_expr():
        nonlocal index
        value = product()
        while index < len(tokens) and tokens[index] in ("+", "-"):
            operator = tokens[index]; index += 1; right = product()
            value = value + right if operator == "+" else value - right
        return value

    def comparison():
        nonlocal index
        value = sum_expr()
        while index < len(tokens) and tokens[index] in ("==", "!=", "<", ">", "<=", ">="):
            operator = tokens[index]; index += 1; right = sum_expr()
            value = int({"==": value == right, "!=": value != right, "<": value < right,
                         ">": value > right, "<=": value <= right, ">=": value >= right}[operator])
        return value

    def logical_and():
        nonlocal index
        value = comparison()
        while index < len(tokens) and tokens[index] == "&&":
            index += 1
            right = comparison()
            value = int(bool(value) and bool(right))
        return value

    def logical_or():
        nonlocal index
        value = logical_and()
        while index < len(tokens) and tokens[index] == "||":
            index += 1
            right = logical_and()
            value = int(bool(value) or bool(right))
        return value

    result = logical_or()
    if index != len(tokens):
        raise PreprocessError("trailing conditional expression tokens")
    return bool(result)
