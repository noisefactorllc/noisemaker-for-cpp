"""Authenticate the scalar degrees calls in the exact Hatch and Strokes runtime trees."""

import hashlib

from .loop_proof import clear_counted_loop_proofs

KEY = "filter/hatch:hatch"
RAW_SHA256 = "510c07e58308c1b0ffb16aafdd90362decc92f818fe25da676bb6c348b120106"
WHOLE_SHA256 = "f6d492b0d8f44940e28384b8ef8b36fe6b1593335789e158b88b4eaf2d0b7ccc"


def authenticate(program, source_hash):
    whole = (program.key, program.source, program.raw_source,
             program.declarations, clear_counted_loop_proofs(program.functions),
             program.resources, program.body_status, program.local_type_names,
             program.structs, program.uniform_blocks, program.interface_symbols,
             program.builtin_symbols, program.preprocessor_defines)
    identities = {
        KEY: (RAW_SHA256, WHOLE_SHA256),
        "filter/strokes:stkSmear": (
            "dac057232a650f3c9eb56829aa12507b639d8632f6fc132cbd067a28996fa4db",
            "c576df2ad32360613db104907e3e97e4378fb05b67adcbee24ac28527ae5e2a6"),
    }
    expected = identities.get(program.key)
    if (expected is None or source_hash != expected[0]
            or hashlib.sha256(program.raw_source.encode()).hexdigest() != expected[0]
            or hashlib.sha256(repr(whole).encode()).hexdigest() != expected[1]):
        raise ValueError("degrees source or typed-tree mismatch")

    def expressions(value):
        yield value
        for child in value.children:
            yield from expressions(child)

    def statements(value):
        for expression in value.expressions:
            yield from expressions(expression)
        for child in value.children:
            yield from statements(child)

    sites = tuple(node for function in program.functions
                  for statement in function.body for node in statements(statement)
                  if node.kind == "builtin" and node.callee == "degrees")
    if (len(sites) != 1 or sites[0].type.display() != "float"
            or len(sites[0].children) != 1
            or sites[0].children[0].type.display() != "float"):
        raise ValueError("degrees node census mismatch")
    return sites


def authenticate_hatch_multiplier(program, source_hash):
    """Return the one runtime Hatch vec2 that stores the stroke reciprocal."""
    authenticate(program, source_hash)
    if (program.key != KEY or len(program.preprocessor_defines) != 1
            or (program.preprocessor_defines[0].name,
                program.preprocessor_defines[0].canonical_value) != ("MODE", "int")):
        raise ValueError("Hatch runtime define mismatch")
    functions = tuple(function for function in program.functions
                      if function.name == "strokeField")
    if len(functions) != 1 or len(functions[0].body) != 2:
        raise ValueError("Hatch strokeField census mismatch")
    declaration = functions[0].body[0]
    if (declaration.kind != "decl" or len(declaration.expressions) != 1):
        raise ValueError("Hatch strokeField declaration mismatch")
    initializer = declaration.expressions[0]
    if (initializer.kind != "declaration" or initializer.symbol.name != "p"
            or len(initializer.children) != 1):
        raise ValueError("Hatch strokeField initializer mismatch")
    product = initializer.children[0]
    if (product.kind != "binary" or product.operator != "*"
            or len(product.children) != 2
            or product.children[0].kind != "call"
            or product.children[0].callee != "rotate2D"):
        raise ValueError("Hatch strokeField product mismatch")
    constructor = product.children[1]
    if (constructor.kind != "construct" or constructor.type.display() != "vec2"
            or len(constructor.children) != 2
            or (constructor.span.start_line, constructor.span.start_column,
                constructor.span.end_line, constructor.span.end_column)
            != (94, 39, 94, 66)
            or program.source[constructor.span.start:constructor.span.end]
            != "vec2(1.0 / stretchAmt, 0.9)"):
        raise ValueError("Hatch multiplier constructor mismatch")
    reciprocal, transverse = constructor.children
    if (reciprocal.kind != "binary" or reciprocal.operator != "/"
            or reciprocal.type.display() != "float"
            or len(reciprocal.children) != 2
            or reciprocal.children[0].kind != "literal"
            or reciprocal.children[0].literal_value != 1.0
            or reciprocal.children[1].kind != "id"
            or reciprocal.children[1].symbol.name != "stretchAmt"
            or transverse.kind != "literal"
            or transverse.literal_value != 0.9):
        raise ValueError("Hatch multiplier lanes mismatch")
    return constructor
