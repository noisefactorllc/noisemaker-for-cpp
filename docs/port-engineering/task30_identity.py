from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('.')
sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice as gen
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program

REVISION = 'a024dc3a960cc44af454abc7aebce50456c194e6'
CORPUS = ROOT / 'tools/glslcpp/corpus' / REVISION
MANIFEST = json.loads((CORPUS / 'manifest.json').read_text())
ENTRIES = {row['program_key']: row for row in MANIFEST['programs']}

KEY = 'filter/extrude:extrude'


def digest(value):
    return hashlib.sha256(repr(value).encode()).hexdigest()


def span(value):
    s = value.span
    return f'{s.start_line}:{s.start_column}-{s.end_line}:{s.end_column}'


def expressions(value, path):
    yield path, value
    for i, child in enumerate(value.children):
        yield from expressions(child, (*path, i))


def statements(value, path):
    for i, expression in enumerate(value.expressions):
        yield from expressions(expression, (*path, f'e{i}', 0))
    for i, child in enumerate(value.children):
        yield from statements(child, (*path, f's{i}'))


def nodes(function):
    for i, statement in enumerate(function.body):
        yield from statements(statement, (i,))


entry = ENTRIES[KEY]
raw = (CORPUS / entry['source']).read_text()
defines = gen._defaults(ROOT, KEY)
program = analyze_program(parse_program(raw, KEY, defines), KEY)

raw_bytes = len(raw.encode())
raw_sha256 = hashlib.sha256(raw.encode()).hexdigest()
normalized_bytes = len(program.source.encode())
normalized_sha256 = hashlib.sha256(program.source.encode()).hexdigest()
function_count = len(program.functions)
function_tuple_sha256 = digest(program.functions)
whole_program_sha256 = digest((program.key, program.source, program.raw_source,
    program.declarations, program.functions, program.resources, program.body_status,
    program.local_type_names, program.structs, program.uniform_blocks,
    program.interface_symbols, program.builtin_symbols,
    program.counted_loop_proof, program.preprocessor_defines))
interface_sha256 = digest((program.declarations, program.resources,
    program.local_type_names, program.structs, program.uniform_blocks,
    program.interface_symbols, program.builtin_symbols, program.preprocessor_defines))

print('KEY', KEY)
print('source', entry['source'])
print('raw_bytes', raw_bytes)
print('raw_sha256', raw_sha256)
print('normalized_bytes', normalized_bytes)
print('normalized_sha256', normalized_sha256)
print('defines', defines)
print('function_count', function_count)
print('function_tuple_sha256', function_tuple_sha256)
print('whole_program_sha256', whole_program_sha256)
print('interface_sha256', interface_sha256)

print()
print('=== four-node closure ===')
targets = {
    (12, 's1', 's8', 'e0', 0, 0): 'top all',
    (12, 's1', 's8', 'e0', 0, 0, 0): 'top lessThanEqual',
    (12, 's1', 's9', 'e0', 0, 0, 1): 'side all',
    (12, 's1', 's9', 'e0', 0, 0, 1, 0): 'side lessThanEqual',
}
found = {}
for function in program.functions:
    if function.name != 'main':
        continue
    for path, value in nodes(function):
        if tuple(path) in targets:
            found[tuple(path)] = {
                'label': targets[tuple(path)],
                'span': span(value),
                'kind': value.kind,
                'callee': getattr(value, 'callee', None),
                'result_type': value.type.display(),
                'argument_types': [c.type.display() for c in value.children],
                'sha256': digest(value),
                'num_children': len(value.children),
            }
for path, info in found.items():
    print(path, info)

# Check parentage: bvec2-typed lessThanEqual nodes must be immediate (only) child of the all() node
print()
print('=== parent-child immediacy check ===')
for function in program.functions:
    if function.name != 'main':
        continue
    for path, value in nodes(function):
        if tuple(path) in ((12, 's1', 's8', 'e0', 0, 0), (12, 's1', 's9', 'e0', 0, 0, 1)):
            assert value.kind == 'builtin' and value.callee == 'all'
            assert len(value.children) == 1, f'all() has {len(value.children)} children, expected 1'
            child = value.children[0]
            print(path, '-> all() single child kind:', child.kind, 'callee:', getattr(child, 'callee', None), 'type:', child.type.display())
            assert child.kind == 'builtin' and child.callee == 'lessThanEqual' and child.type.display() == 'bvec2'

print('Immediacy check PASSED: each all() has exactly one child, which is the lessThanEqual bvec2 node.')

out_path = Path(__file__).with_name('task30_identity_result.json')
out_path.write_text(json.dumps({
    'raw_bytes': raw_bytes, 'raw_sha256': raw_sha256,
    'normalized_bytes': normalized_bytes, 'normalized_sha256': normalized_sha256,
    'defines': defines, 'function_count': function_count,
    'function_tuple_sha256': function_tuple_sha256,
    'whole_program_sha256': whole_program_sha256,
    'interface_sha256': interface_sha256,
    'closure_nodes': {str(k): v for k, v in found.items()},
}, indent=2) + '\n')
print()
print('wrote', out_path)
