"""Strongly typed C++ emission from the fail-closed parsed GLSL subset."""

from __future__ import annotations

import re

from .parser import GeneratorError
from .types import Expr, Program, Statement


_CPP_TYPES = {
    "float": "float",
    "int": "std::int32_t",
    "vec2": "glsl::Vec2",
    "vec3": "glsl::Vec3",
    "vec4": "glsl::Vec4",
    "ivec2": "glsl::IVec2",
}


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r"_\1", name).lower()


def _factory_name(key: str) -> str:
    return "bind_" + key.split(":", 1)[0].replace("/", "_")


def _swizzle(member: str, target: str) -> str:
    lanes = {"x": 0, "y": 1, "z": 2, "w": 3, "r": 0, "g": 1, "b": 2, "a": 3}
    try:
        return f"glsl::swizzle<{', '.join(str(lanes[letter]) for letter in member)}>({target})"
    except KeyError as error:
        raise GeneratorError(f"unsupported swizzle {member}") from error


class _Emitter:
    def __init__(self, program: Program, pass_bindings: dict[str, str]) -> None:
        self.program = program
        self.uniforms = pass_bindings

    def fail(self, expression: Expr | Statement | None, message: str) -> GeneratorError:
        if isinstance(expression, Expr):
            return GeneratorError(f"{self.program.key}:{expression.line}:{expression.column}: {message}")
        return GeneratorError(f"{self.program.key}: emit: {message}")

    def expression(self, expression: Expr) -> str:
        if expression.kind == "literal":
            suffix = "f" if "." in (expression.value or "") else ""
            return f"{expression.value}{suffix}"
        if expression.kind == "name":
            if expression.value in self.uniforms:
                return f"state.{_snake(expression.value or '')}"
            if expression.value == "gl_FragCoord":
                return "context.frag_coord"
            return _snake(expression.value or "")
        if expression.kind == "member":
            return _swizzle(expression.value or "", self.expression(expression.children[0]))
        if expression.kind == "unary":
            return f"(-{self.expression(expression.children[0])})"
        if expression.kind == "binary":
            left, right = expression.children
            return f"({self.expression(left)} {expression.value} {self.expression(right)})"
        if expression.kind != "call":
            raise self.fail(expression, "unsupported expression")
        arguments = [self.expression(argument) for argument in expression.children]
        if expression.value == "vec2":
            return f"glsl::Vec2({', '.join(arguments)})"
        if expression.value == "vec4":
            return f"glsl::Vec4({', '.join(arguments)})"
        if expression.value == "textureSize":
            if len(expression.children) != 2 or expression.children[0].kind != "name":
                raise self.fail(expression, "unsupported textureSize arguments")
            texture = _snake(expression.children[0].value or "")
            return ("glsl::IVec2(static_cast<std::int32_t>(state." + texture + "->width()), "
                    "static_cast<std::int32_t>(state." + texture + "->height()))")
        if expression.value == "texture":
            if len(expression.children) != 2 or expression.children[0].kind != "name":
                raise self.fail(expression, "unsupported texture arguments")
            texture = _snake(expression.children[0].value or "")
            return f"sample_texture(*state.{texture}, {arguments[1]})"
        if expression.value == "min":
            return f"glsl::component_min({', '.join(arguments)})"
        raise self.fail(expression, f"unsupported call {expression.value}")

    def statement(self, statement: Statement, indent: str) -> list[str]:
        if statement.kind == "declaration":
            if statement.type_name not in _CPP_TYPES or statement.target is None or statement.value is None:
                raise self.fail(statement, "unsupported declaration")
            return [f"{indent}{_CPP_TYPES[statement.type_name]} {_snake(statement.target.value or '')} = {self.expression(statement.value)};"]
        if statement.kind == "assignment":
            if statement.target is None or statement.value is None:
                raise self.fail(statement, "malformed assignment")
            if statement.target.kind == "member":
                base = self.expression(statement.target.children[0])
                member = statement.target.value or ""
                lanes = {"x": 0, "y": 1, "z": 2, "w": 3, "r": 0, "g": 1, "b": 2, "a": 3}
                try:
                    indices = ", ".join(str(lanes[letter]) for letter in member)
                except KeyError as error:
                    raise self.fail(statement.target, f"unsupported assignment swizzle {member}") from error
                return [f"{indent}glsl::set_swizzle<{indices}>({base}, {self.expression(statement.value)});"]
            if statement.target.kind == "name" and statement.target.value == "fragColor":
                return [f"{indent}output = {self.expression(statement.value)};"]
            raise self.fail(statement.target, "unsupported assignment target")
        if statement.kind == "if":
            if statement.target is None:
                raise self.fail(statement, "malformed if")
            lines = [f"{indent}if ({self.expression(statement.target)}) {{"]
            for nested in statement.then_body:
                lines.extend(self.statement(nested, indent + "  "))
            lines.append(f"{indent}}} else {{")
            for nested in statement.else_body:
                lines.extend(self.statement(nested, indent + "  "))
            lines.append(f"{indent}}}")
            return lines
        raise self.fail(statement, "unsupported statement")

    def render(self, revision: str, source_hash: str) -> str:
        state_lines: list[str] = []
        constructor_parameters: list[str] = []
        constructor_initializers: list[str] = []
        factory_arguments: list[str] = []
        for name, type_name in sorted(self.uniforms.items()):
            field = _snake(name)
            if type_name == "sampler2D":
                state_lines.append(f"  const Surface* {field};")
                constructor_parameters.append(f"const Surface* {field}_value")
                constructor_initializers.append(f"{field}({field}_value)")
                factory_arguments.append(f"&bindings.texture(\"{name}\")")
            elif type_name in _CPP_TYPES:
                state_lines.append(f"  {_CPP_TYPES[type_name]} {field};")
                constructor_parameters.append(f"{_CPP_TYPES[type_name]} {field}_value")
                constructor_initializers.append(f"{field}({field}_value)")
                fallback = "0.0f" if type_name == "float" else f"{_CPP_TYPES[type_name]}(0.0f)"
                factory_arguments.append(
                    f"bindings.get_or<{_CPP_TYPES[type_name]}>(\"{name}\", {fallback})")
            else:
                raise GeneratorError(f"{self.program.key}: unsupported uniform type {type_name}")
        body: list[str] = []
        for statement in self.program.statements:
            body.extend(self.statement(statement, "  "))
        factory = _factory_name(self.program.key)
        lines = [
            "// Generated by glslcpp schema 1.",
            f"// Revision: {revision}",
            f"// Program: {self.program.key}",
            f"// Source SHA-256: {source_hash}",
            "#include \"noisemaker/generated/catalog.hpp\"",
            "",
            "#include <cstdint>",
            "#include <memory>",
            "",
            "#include \"noisemaker/sampler.hpp\"",
            "",
            "namespace noisemaker::generated {",
            "namespace {",
            "struct State final : KernelState {",
            f"  State({', '.join(constructor_parameters)}) : {', '.join(constructor_initializers)} {{}}",
            *state_lines,
            "};",
            "",
            "[[nodiscard]] glsl::Vec4 sample_texture(const Surface& surface, const glsl::Vec2& uv) noexcept {",
            "  const Rgba sample = sample_nearest_bottom_left(surface, uv[0], uv[1]);",
            "  return glsl::Vec4(sample[0], sample[1], sample[2], sample[3]);",
            "}",
            "",
            "void pixel(const KernelState& base, const glsl::PixelContext& context, glsl::Vec4& output) noexcept {",
            "  const auto& state = static_cast<const State&>(base);",
            *body,
            "}",
            "}  // namespace",
            "",
            f"BoundKernel {factory}(const glsl::Bindings& bindings) {{",
            f"  const auto state = std::make_shared<State>({', '.join(factory_arguments)});",
            "  return BoundKernel(state, &pixel);",
            "}",
            "",
            "}  // namespace noisemaker::generated",
            "",
        ]
        return "\n".join(lines)


def render_cpp(program: Program, revision: str, source_hash: str, pass_bindings: dict[str, str]) -> str:
    return _Emitter(program, pass_bindings).render(revision, source_hash)
