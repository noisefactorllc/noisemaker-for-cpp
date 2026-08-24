"""Structural, immutable GLSL ES types for later statically bound codegen."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Type:
    kind: str
    base: str | None = None
    width: int | None = None
    columns: int | None = None
    rows: int | None = None
    element: "Type | None" = None
    size: int | None = None
    symbol_id: int | None = None
    name: str | None = None

    def display(self) -> str:
        if self.kind == "vector": return f"{'' if self.base == 'float' else self.base[0]}vec{self.width}"
        if self.kind == "matrix": return f"mat{self.columns}" if self.columns == self.rows else f"mat{self.columns}x{self.rows}"
        if self.kind == "array": return f"{self.element.display()}[{self.size}]"
        return self.name or self.base or self.kind


VOID = Type("void", "void")
BOOL = Type("scalar", "bool")
INT = Type("scalar", "int")
UINT = Type("scalar", "uint")
FLOAT = Type("scalar", "float")
SAMPLER2D = Type("sampler", "sampler2D")
SCALARS = {item.base: item for item in (VOID, BOOL, INT, UINT, FLOAT)}


def vector(base: str, width: int) -> Type: return Type("vector", base, width)
def matrix(columns: int, rows: int | None = None) -> Type: return Type("matrix", "float", columns, columns, rows or columns)
def array(element: Type, size: int) -> Type: return Type("array", element=element, size=size)
def struct(symbol_id: int, name: str) -> Type: return Type("struct", symbol_id=symbol_id, name=name)


def named_type(name: str, structs: dict[str, Type]) -> Type | None:
    if name in SCALARS: return SCALARS[name]
    if name == "sampler2D": return SAMPLER2D
    for prefix, base in (("vec", "float"), ("ivec", "int"), ("uvec", "uint"), ("bvec", "bool")):
        if name.startswith(prefix) and name[len(prefix):] in {"2", "3", "4"}:
            return vector(base, int(name[len(prefix):]))
    if name.startswith("mat"):
        tail = name[3:]
        parts = tail.split("x")
        if len(parts) in (1, 2) and all(part in {"2", "3", "4"} for part in parts):
            return matrix(int(parts[0]), int(parts[-1]))
    return structs.get(name)
