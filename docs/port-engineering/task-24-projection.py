from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path('.')
sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice as gen
from tools.glslcpp import emit_typed_cpp as emit
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


CORPUS = ROOT / 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6'
MANIFEST = json.loads((CORPUS / 'manifest.json').read_text())
ENTRIES = {item['program_key']: item for item in MANIFEST['programs']}
CURRENT_CAPABILITIES = tuple(gen.APPROVED_CAPABILITIES)


def typed(key: str):
    entry = ENTRIES[key]
    source = (CORPUS / entry['source']).read_text()
    defines = gen._defaults(ROOT, key)
    return analyze_program(parse_program(source, key, defines), key), entry, defines


def expressions(value):
    yield value
    for child in value.children:
        yield from expressions(child)


def statement_expressions(statement):
    for value in statement.expressions:
        yield from expressions(value)
    for child in statement.children:
        yield from statement_expressions(child)


def all_expressions(program):
    for function in program.functions:
        for statement in function.body:
            for value in statement_expressions(statement):
                yield function, value


def transform_expression(value):
    children = tuple(transform_expression(child) for child in value.children)
    value = dataclasses.replace(value, children=children)
    if (value.kind == 'index' and len(value.children) == 2
            and value.children[0].type.display() == 'vec3'
            and value.children[1].kind == 'literal'
            and value.children[1].type.display() == 'int'
            and value.children[1].literal_value in (0, 1, 2)):
        return dataclasses.replace(
            value, kind='swizzle', children=(value.children[0],),
            member='xyz'[value.children[1].literal_value])
    return value


def transform_statement(value):
    return dataclasses.replace(
        value,
        expressions=tuple(transform_expression(item) for item in value.expressions),
        children=tuple(transform_statement(item) for item in value.children),
    )


def literal_vec3_projection(key: str):
    program, entry, defines = typed(key)
    sites = []
    for function, value in all_expressions(program):
        if value.kind == 'index':
            sites.append({
                'function': function.name,
                'span': f'{value.span.start_line}:{value.span.start_column}-{value.span.end_line}:{value.span.end_column}',
                'base_type': value.children[0].type.display(),
                'index_kind': value.children[1].kind,
                'index_value': value.children[1].literal_value,
            })
    projected = dataclasses.replace(program, functions=tuple(
        dataclasses.replace(function, body=tuple(transform_statement(item) for item in function.body))
        for function in program.functions))
    gen.validate_capabilities(projected, CURRENT_CAPABILITIES,
                              source_hash=entry['raw_sha256'])
    cpp = emit.render_typed_cpp(projected, key, entry['raw_sha256'], 'typed_projection',
                                'bind_' + key.replace('/', '_').replace(':', '_'))
    return {
        'key': key, 'defines': defines, 'sites': sites,
        'projected_cpp_bytes': len(cpp.encode()),
        'projected_cpp_sha256': hashlib.sha256(cpp.encode()).hexdigest(),
        'later_blocker': None,
    }


def round_projection(key: str):
    program, entry, defines = typed(key)
    sites = []
    for function, value in all_expressions(program):
        if value.kind == 'builtin' and value.callee == 'round':
            sites.append({
                'function': function.name,
                'span': f'{value.span.start_line}:{value.span.start_column}-{value.span.end_line}:{value.span.end_column}',
                'type': value.type.display(),
                'argument_type': value.children[0].type.display(),
                'argument_repr_sha256': hashlib.sha256(repr(value.children[0]).encode()).hexdigest(),
            })
    try:
        gen.validate_capabilities(program, CURRENT_CAPABILITIES + ('round',),
                                  source_hash=entry['raw_sha256'])
        cpp = emit.render_typed_cpp(program, key, entry['raw_sha256'], 'typed_projection',
                                    'bind_' + key.replace('/', '_').replace(':', '_'))
        result = {'later_blocker': None, 'projected_cpp_bytes': len(cpp.encode()),
                  'projected_cpp_sha256': hashlib.sha256(cpp.encode()).hexdigest()}
    except Exception as error:
        result = {'later_blocker': str(error)}
    return {'key': key, 'defines': defines, 'sites': sites, **result}


def literal_int_macro_projection(key: str):
    entry = ENTRIES[key]
    source = (CORPUS / entry['source']).read_text()
    definitions = re.findall(r'\bconst\s+int\s+([A-Za-z_]\w*)\s*=\s*([0-9]+)\s*;', source)
    projected = re.sub(r'\bconst\s+int\s+[A-Za-z_]\w*\s*=\s*[0-9]+\s*;', '', source)
    for name, literal in definitions:
        projected = re.sub(rf'\b{re.escape(name)}\b', literal, projected)
    try:
        program = analyze_program(parse_program(projected, key, gen._defaults(ROOT, key)), key)
        gen.validate_capabilities(program, CURRENT_CAPABILITIES,
                                  source_hash=entry['raw_sha256'])
        cpp = emit.render_typed_cpp(program, key, entry['raw_sha256'], 'typed_projection',
                                    'bind_' + key.replace('/', '_').replace(':', '_'))
        result = {'later_blocker': None, 'projected_cpp_bytes': len(cpp.encode()),
                  'projected_cpp_sha256': hashlib.sha256(cpp.encode()).hexdigest()}
    except Exception as error:
        result = {'later_blocker': str(error)}
    return {'key': key, 'literal_int_globals': definitions, **result}


def main():
    # Process-local projection only: expose an already-implemented runtime
    # scalar builtin through the validator/emitter name tables.
    gen.APPROVED_CAPABILITIES = CURRENT_CAPABILITIES + ('round',)
    gen._BUILTINS = frozenset((*gen._BUILTINS, 'round'))
    emit._BUILTIN_NAMES = {**emit._BUILTIN_NAMES, 'round': 'round'}
    data = {
        'literal_vec3': [literal_vec3_projection(key) for key in (
            'classicNoisedeck/lensDistortion:lensDistortion',
            'filter/prismaticAberration:prismaticAberration')],
        'round': [round_projection(key) for key in (
            'filter/pixelSort:gatherSorted', 'filter/posterize:posterize')],
        'remaining_literal_int_globals': [literal_int_macro_projection(key) for key in (
            'filter/dither:dither', 'filter/lightLeak:lightLeak',
            'filter/parallax:parallax', 'filter/reindex:nmReindexReduce',
            'filter/reindex:nmReindexStats', 'synth/mandelbrot:mandelbrot')],
    }
    print(json.dumps(data, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
