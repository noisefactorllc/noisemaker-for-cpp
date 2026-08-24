from __future__ import annotations

import collections
import dataclasses
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('.')
sys.path.insert(0, str(ROOT))

from tools.glslcpp import emit_typed_cpp as emit
from tools.glslcpp import generate_typed_slice as gen
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program

REVISION = 'a024dc3a960cc44af454abc7aebce50456c194e6'
CORPUS = ROOT / 'tools/glslcpp/corpus' / REVISION
MANIFEST = json.loads((CORPUS / 'manifest.json').read_text())
ENTRIES = {item['program_key']: item for item in MANIFEST['programs']}
SPEC = json.loads((ROOT / 'tools/glslcpp/typed_slice.json').read_text())
KEY = 'filter/rotate:rot'
MANUAL = ('filter/invert:inv', 'synth/solid:solid')

def digest(value: object) -> str:
    return hashlib.sha256(repr(value).encode()).hexdigest()

def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def list_sha256(values: list[str]) -> str:
    return hashlib.sha256(('\n'.join(values) + '\n').encode()).hexdigest()

def span(value: object) -> str:
    item = value.span
    return f'{item.start_line}:{item.start_column}-{item.end_line}:{item.end_column}'

def whole(program: object) -> str:
    return digest((program.key, program.source, program.raw_source,
                   program.declarations, program.functions, program.resources,
                   program.body_status, program.local_type_names, program.structs,
                   program.uniform_blocks, program.interface_symbols,
                   program.builtin_symbols, program.counted_loop_proof,
                   program.preprocessor_defines))

def interface(program: object) -> str:
    return digest((program.declarations, program.resources,
                   program.local_type_names, program.structs,
                   program.uniform_blocks, program.interface_symbols,
                   program.builtin_symbols, program.preprocessor_defines))

def expression_nodes(value: object, path: tuple[object, ...], parent=None,
                     child_index=None):
    yield path, value, parent, child_index
    for ordinal, child in enumerate(value.children):
        yield from expression_nodes(child, (*path, ordinal), value, ordinal)

def statement_nodes(value: object, path: tuple[object, ...]):
    for ordinal, expression in enumerate(value.expressions):
        yield from expression_nodes(expression, (*path, f'e{ordinal}', 0))
    for ordinal, child in enumerate(value.children):
        yield from statement_nodes(child, (*path, f's{ordinal}'))

def nodes(function: object):
    for ordinal, statement in enumerate(function.body):
        yield from statement_nodes(statement, (ordinal,))

def typed(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry['source']).read_text()
    defines = gen._defaults(ROOT, key)
    return analyze_program(parse_program(raw, key, defines), key), entry, raw, defines

def binding_signature(program: object) -> list[str]:
    sampler_bindings = {name: ordinal + 1 for ordinal, name in enumerate(program.resources.samplers)}
    result = []
    for declaration in program.declarations:
        symbol = declaration.symbol
        if symbol.storage == 'uniform':
            suffix = f'/S{sampler_bindings[symbol.name]}' if symbol.name in sampler_bindings else ''
            result.append(f'{symbol.name}:{declaration.type.display()}@{symbol.id}{suffix}')
        elif symbol.storage == 'output':
            result.append(f'{symbol.name}:{declaration.type.display()}@{symbol.id}/out')
    return result

typed_keys = [item['program_key'] for item in SPEC['programs']]
public_keys = sorted((*typed_keys, *MANUAL))
projected_typed = sorted((*typed_keys, KEY))
projected_public = sorted((*projected_typed, *MANUAL))
corpus_keys = [item['program_key'] for item in MANIFEST['programs']]
remaining = [key for key in corpus_keys if key not in set(typed_keys)]

candidate_rows = []
validator_histogram: collections.Counter[str] = collections.Counter()
emitter_passes = []
for candidate_key in remaining:
    try:
        candidate, entry, _, _ = typed(candidate_key)
    except Exception as error:
        candidate_rows.append({'key': candidate_key, 'stage': 'analyzer', 'error': str(error)})
        validator_histogram[f'analyzer: {error}'] += 1
        continue
    try:
        gen.validate_capabilities(candidate, tuple(gen.APPROVED_CAPABILITIES),
                                  source_hash=entry['raw_sha256'])
        validator = 'pass'
    except Exception as error:
        validator = str(error)
    try:
        emit.render_typed_cpp(candidate, candidate_key, entry['raw_sha256'],
                              'task28_probe', 'bind_task28_probe')
        emitter = 'pass'
        emitter_passes.append(candidate_key)
    except Exception as error:
        emitter = str(error)
    category = validator.split(': ', 1)[-1]
    validator_histogram[category] += 1
    if validator == 'pass' or emitter == 'pass' or candidate_key in {KEY, 'mixer/focusBlur:focusBlur'}:
        candidate_rows.append({'key': candidate_key, 'validator': validator, 'emitter': emitter})

program, entry, raw, defines = typed(KEY)
functions = {function.name: function for function in program.functions}
rotate = functions['rotate2D']
main = functions['main']
rotate_nodes = list(nodes(rotate))
main_nodes = list(nodes(main))
constructor_record = next((path, value, parent, child_index)
                          for path, value, parent, child_index in rotate_nodes
                          if value.kind == 'construct' and value.type.display() == 'mat2')
call_record = next((path, value, parent, child_index)
                   for path, value, parent, child_index in main_nodes
                   if value.kind == 'call' and value.signature_id == rotate.signature.id)
matrix_binary_record = next((path, value, parent, child_index)
                            for path, value, parent, child_index in main_nodes
                            if value.kind == 'binary' and value.type.display() == 'vec2'
                            and any(child.type.display() == 'mat2' for child in value.children))

constructor_path, constructor, constructor_parent, constructor_child_index = constructor_record
call_path, call, call_parent, call_child_index = call_record
binary_path, matrix_binary, matrix_binary_parent, matrix_binary_child_index = matrix_binary_record

child_records = []
for ordinal, child in enumerate(constructor.children):
    child_records.append({
        'ordinal': ordinal, 'path': (*constructor_path, ordinal),
        'kind': child.kind, 'type': child.type.display(), 'operator': child.operator,
        'symbol_id': child.symbol_id,
        'child_symbol_id': child.children[0].symbol_id if child.kind == 'unary' else None,
        'span': span(child), 'sha256': digest(child),
    })

matrix_return_functions = [function.signature.id for function in program.functions
                           if function.return_type.kind == 'matrix']
matrix_parameters = [parameter.id for function in program.functions
                     for parameter in function.parameters if parameter.type.kind == 'matrix']
matrix_expressions = []
for function in program.functions:
    for path_value, value, parent, child_index in nodes(function):
        if value.type.kind == 'matrix':
            matrix_expressions.append({
                'owner_id': function.signature.id, 'owner': function.name,
                'path': path_value, 'kind': value.kind, 'span': span(value),
                'sha256': digest(value), 'parent_kind': parent.kind if parent else None,
                'parent_child_index': child_index,
            })

profile_tuple = (
    'rotate-mat2-return-v1', KEY,
    'c23e8462e8240f25a715fa3eb05e567269c8d410d27943ba346ebccdd0de1f8f',
    (),
    digest(program.functions), whole(program), interface(program),
    (rotate.signature.id, rotate.name, digest(rotate.signature), digest(rotate),
     span(rotate), len(rotate.body)),
    (constructor_path, span(constructor), digest(constructor),
     tuple((child.kind, child.type.display(), child.operator, child.symbol_id,
            child.children[0].symbol_id if child.kind == 'unary' else None,
            span(child), digest(child)) for child in constructor.children)),
    (call_path, span(call), digest(call), call.signature_id,
     call_parent.kind, call_child_index, digest(call_parent)),
    (binary_path, span(matrix_binary), digest(matrix_binary),
     matrix_binary.operator, tuple(child.type.display() for child in matrix_binary.children)),
)

result = {
    'corpus_revision': REVISION,
    'baseline': {
        'corpus_count': len(corpus_keys), 'typed_count': len(typed_keys),
        'public_count': len(public_keys),
        'publicly_unported_count': len(set(corpus_keys) - set(public_keys)),
        'typed_ordered_sha256': list_sha256(typed_keys),
        'public_ordered_sha256': list_sha256(public_keys),
        'typed_order_is_sorted': typed_keys == sorted(typed_keys),
    },
    'projected': {
        'typed_count': len(projected_typed), 'public_count': len(projected_public),
        'publicly_unported_count': len(set(corpus_keys) - set(projected_public)),
        'typed_ordered_sha256': list_sha256(projected_typed),
        'public_ordered_sha256': list_sha256(projected_public),
        'typed_zero_based_position': projected_typed.index(KEY),
        'typed_neighbors': projected_typed[projected_typed.index(KEY) - 1:projected_typed.index(KEY) + 2],
    },
    'remaining_frontier': {
        'absent_from_typed_count_including_two_manual_programs': len(remaining),
        'publicly_unported_count': len(set(corpus_keys) - set(public_keys)),
        'emitter_passes': emitter_passes,
        'validator_first_blocker_histogram': dict(sorted(validator_histogram.items())),
        'distinguishing_rows': candidate_rows,
    },
    'rotate': {
        'key': KEY, 'source': entry['source'],
        'raw_bytes': len(raw.encode()), 'raw_sha256': hashlib.sha256(raw.encode()).hexdigest(),
        'normalized_bytes': len(program.source.encode()),
        'normalized_sha256': hashlib.sha256(program.source.encode()).hexdigest(),
        'defines': defines, 'numeric_contract': 'glsl-f32',
        'function_count': len(program.functions),
        'function_tuple_sha256': digest(program.functions),
        'whole_program_sha256': whole(program),
        'interface_sha256': interface(program),
        'binding_signature': binding_signature(program),
        'resources': dataclasses.asdict(program.resources),
        'loop_proof': dataclasses.asdict(program.counted_loop_proof),
        'functions': [{
            'id': function.signature.id, 'name': function.name,
            'return_type': function.return_type.display(), 'signature_sha256': digest(function.signature),
            'body_statements': len(function.body), 'body_sha256': digest(function),
            'span': span(function),
            'parameters': [[parameter.id, parameter.name, parameter.type.display(),
                            parameter.direction, span(parameter)] for parameter in function.parameters],
        } for function in program.functions],
        'matrix_return_function_ids': matrix_return_functions,
        'matrix_parameter_ids': matrix_parameters,
        'matrix_expressions': matrix_expressions,
        'constructor': {
            'owner_id': rotate.signature.id, 'path': constructor_path,
            'span': span(constructor), 'sha256': digest(constructor),
            'parent_statement_kind': rotate.body[2].kind,
            'children': child_records,
        },
        'call': {
            'owner_id': main.signature.id, 'path': call_path,
            'span': span(call), 'sha256': digest(call),
            'signature_id': call.signature_id,
            'argument_sha256': digest(call.children[0]),
            'parent_kind': call_parent.kind, 'parent_sha256': digest(call_parent),
            'parent_child_index': call_child_index,
        },
        'matrix_vector_binary': {
            'path': binary_path, 'span': span(matrix_binary),
            'sha256': digest(matrix_binary), 'operator': matrix_binary.operator,
            'children': [child.type.display() for child in matrix_binary.children],
            'call_is_left_child': matrix_binary.children[0] is call,
        },
        'profile_tuple_sha256': digest(profile_tuple),
        'profile_tuple_repr': repr(profile_tuple),
        'validator': next(row['validator'] for row in candidate_rows if row['key'] == KEY),
        'emitter': next(row['emitter'] for row in candidate_rows if row['key'] == KEY),
    },
    'accepted_task27_file_hashes': {
        path: file_sha256(ROOT / path) for path in (
            'tools/glslcpp/frontend/perlin_scalar_uint_xor_profile.py',
            'tools/glslcpp/generate_typed_slice.py',
            'tools/glslcpp/emit_typed_cpp.py',
            'tools/glslcpp/typed_slice.json',
            'tests/test_typed_generator.py',
            'tests/test_generated_kernels.cpp',
            'tests/test_typed_slice.cpp',
            'src/typed_generated/typed_slice.cpp',
            'src/typed_generated/typed_manifest.json',
            'include/noisemaker/generated/catalog.hpp',
            'include/noisemaker/glsl_types.hpp',
            'CMakeLists.txt',
        )
    },
}

print(json.dumps(result, indent=2))
