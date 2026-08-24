from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
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
KEYS = (
    'classicNoisedeck/lensDistortion:lensDistortion',
    'filter/prismaticAberration:prismaticAberration',
)

def digest(value):
    return hashlib.sha256(repr(value).encode()).hexdigest()

def function_hash(program):
    return digest(program.functions)

def whole_hash(program):
    return digest((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))

def interface_hash(program):
    return digest((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))

def span(value):
    x = value.span
    return f'{x.start_line}:{x.start_column}-{x.end_line}:{x.end_column}'

def expr_nodes(value, path, parent=None, child_index=None):
    yield path, value, parent, child_index
    for index, child in enumerate(value.children):
        yield from expr_nodes(child, (*path, index), value, index)

def statement_nodes(statement, path):
    yield path, statement
    for index, value in enumerate(statement.expressions):
        yield from expr_nodes(value, (*path, f'e{index}', 0))
    for index, child in enumerate(statement.children):
        yield from statement_nodes(child, (*path, f's{index}'))

def all_nodes(function):
    for index, statement in enumerate(function.body):
        yield from statement_nodes(statement, (index,))

def transform_expression(value):
    children = tuple(transform_expression(child) for child in value.children)
    current = dataclasses.replace(value, children=children) if children != value.children else value
    if (current.kind == 'index' and len(current.children) == 2
            and current.children[0].type.display() == 'vec3'
            and current.children[0].kind == 'id'
            and current.children[0].symbol is not None
            and current.children[0].symbol.name == 'hsv'
            and current.children[0].symbol.storage == 'local'
            and current.children[1].kind == 'literal'
            and current.children[1].type.display() == 'int'
            and current.children[1].literal_value in (0, 1, 2)):
        return dataclasses.replace(current, kind='swizzle', children=(current.children[0],),
                                   member='xyz'[current.children[1].literal_value])
    return current

def transform_statement(value):
    expressions = tuple(transform_expression(item) for item in value.expressions)
    children = tuple(transform_statement(item) for item in value.children)
    if expressions == value.expressions and children == value.children:
        return value
    return dataclasses.replace(value, expressions=expressions, children=children)

def recompute(key):
    entry = ENTRIES[key]
    raw = (CORPUS / entry['source']).read_text()
    defines = gen._defaults(ROOT, key)
    pre = analyze_program(parse_program(raw, key, defines), key)
    main = next(function for function in pre.functions if function.name == 'main')
    sites = []
    all_indices = []
    for function in pre.functions:
        for row in all_nodes(function):
            if len(row) != 4:
                continue
            path, value, parent, child_index = row
            if value.kind != 'index':
                continue
            all_indices.append((function.name, path, value))
            base, index = value.children
            if not (function.name == 'main' and base.kind == 'id' and base.symbol is not None
                    and base.symbol.name == 'hsv' and base.symbol.storage == 'local'
                    and base.type.display() == 'vec3' and index.kind == 'literal'
                    and index.type.display() == 'int' and index.literal_value in (0, 1, 2)):
                continue
            role = ('direct-= lvalue' if parent is not None and parent.kind == 'assign'
                    and parent.operator == '=' and child_index == 0 else 'read')
            sites.append({
                'function_id': function.signature.id,
                'function': function.name,
                'path': path,
                'span': span(value),
                'expr_sha256': digest(value),
                'base_sha256': digest(base),
                'index_sha256': digest(index),
                'base_symbol_id': base.symbol_id,
                'base_symbol': base.symbol.name,
                'base_storage': base.symbol.storage,
                'base_type': base.type.display(),
                'result_type': value.type.display(),
                'category': value.category,
                'index_kind': index.kind,
                'index_type': index.type.display(),
                'index_category': index.category,
                'index_literal': index.literal,
                'index_value': index.literal_value,
                'role': role,
                'parent_kind': parent.kind if parent else None,
                'parent_operator': parent.operator if parent else None,
                'parent_sha256': digest(parent) if parent else None,
                'parent_child_index': child_index,
            })
    post_functions = tuple(
        dataclasses.replace(function, body=tuple(transform_statement(item) for item in function.body))
        if function.name == 'main' else function
        for function in pre.functions
    )
    post = dataclasses.replace(pre, functions=post_functions)
    gen.validate_capabilities(post, tuple(gen.APPROVED_CAPABILITIES), source_hash=entry['raw_sha256'])
    cpp = emit.render_typed_cpp(post, key, entry['raw_sha256'], 'typed_projection',
                                'bind_' + key.replace('/', '_').replace(':', '_'))
    declarations = []
    sampler_ordinals = {name: index + 1 for index, name in enumerate(pre.resources.samplers)}
    for item in pre.declarations:
        if item.symbol.storage in {'uniform', 'output'}:
            suffix = f'/S{sampler_ordinals[item.symbol.name]}' if item.symbol.name in sampler_ordinals else ''
            declarations.append(f'{item.symbol.name}:{item.type.display()}@{item.symbol.id}{suffix}/{item.symbol.storage}')
    post_main = next(function for function in post.functions if function.name == 'main')
    result = {
        'key': key,
        'defines': defines,
        'raw_bytes': len(raw.encode()),
        'raw_sha256': hashlib.sha256(raw.encode()).hexdigest(),
        'normalized_bytes': len(pre.source.encode()),
        'normalized_sha256': hashlib.sha256(pre.source.encode()).hexdigest(),
        'function_count': len(pre.functions),
        'function_profiles_pre': [[fn.signature.id, fn.name, len(fn.body), digest(fn)] for fn in pre.functions],
        'function_profiles_post': [[fn.signature.id, fn.name, len(fn.body), digest(fn)] for fn in post.functions],
        'main_id': main.signature.id,
        'main_hash_pre': digest(main),
        'main_hash_post': digest(post_main),
        'function_tuple_sha256_pre': function_hash(pre),
        'function_tuple_sha256_post': function_hash(post),
        'whole_program_sha256_pre': whole_hash(pre),
        'whole_program_sha256_post': whole_hash(post),
        'interface_sha256_pre': interface_hash(pre),
        'interface_sha256_post': interface_hash(post),
        'resources': dataclasses.asdict(pre.resources),
        'bindings_and_output': declarations,
        'all_index_count': len(all_indices),
        'selected_site_count': len(sites),
        'sites': sites,
        'post_index_count': sum(1 for fn in post.functions for row in all_nodes(fn) if len(row) == 4 and row[1].kind == 'index'),
        'post_selected_swizzles': [
            {'path': row[0], 'span': span(row[1]), 'member': row[1].member, 'sha256': digest(row[1])}
            for row in all_nodes(post_main)
            if len(row) == 4 and row[1].kind == 'swizzle'
            and span(row[1]) in {x['span'] for x in sites}
        ],
        'projected_cpp_bytes': len(cpp.encode()),
        'projected_cpp_sha256': hashlib.sha256(cpp.encode()).hexdigest(),
        'projected_cpp_set_swizzle_hsv': cpp.count('glsl::set_swizzle<0>(hsv') + cpp.count('glsl::set_swizzle<1>(hsv') + cpp.count('glsl::set_swizzle<2>(hsv'),
        'projected_cpp_read_swizzle_hsv': cpp.count('glsl::swizzle<0>(hsv)') + cpp.count('glsl::swizzle<1>(hsv)') + cpp.count('glsl::swizzle<2>(hsv)'),
    }
    assert result['all_index_count'] == result['selected_site_count']
    assert result['post_index_count'] == 0
    assert len(result['post_selected_swizzles']) == len(sites)
    return result

print(json.dumps([recompute(key) for key in KEYS], indent=2))
