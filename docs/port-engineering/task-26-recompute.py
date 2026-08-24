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
ENTRY = next(item for item in MANIFEST['programs'] if item['program_key'] == 'filter/smooth:smoothEdge')
KEY = ENTRY['program_key']

def digest(value): return hashlib.sha256(repr(value).encode()).hexdigest()
def span(value):
    x = value.span
    return f'{x.start_line}:{x.start_column}-{x.end_line}:{x.end_column}'
def whole_hash(program):
    return digest((program.key, program.source, program.raw_source, program.declarations,
                   program.functions, program.resources, program.body_status,
                   program.local_type_names, program.structs, program.uniform_blocks,
                   program.interface_symbols, program.builtin_symbols,
                   program.counted_loop_proof, program.preprocessor_defines))
def interface_hash(program):
    return digest((program.declarations, program.resources, program.local_type_names,
                   program.structs, program.uniform_blocks, program.interface_symbols,
                   program.builtin_symbols, program.preprocessor_defines))
def expr_nodes(value, path, parent=None, child_index=None):
    yield path, value, parent, child_index
    for index, child in enumerate(value.children):
        yield from expr_nodes(child, (*path, index), value, index)
def statement_nodes(statement, path):
    for index, value in enumerate(statement.expressions):
        yield from expr_nodes(value, (*path, f'e{index}', 0))
    for index, child in enumerate(statement.children):
        yield from statement_nodes(child, (*path, f's{index}'))
def all_nodes(function):
    for index, statement in enumerate(function.body):
        yield from statement_nodes(statement, (index,))

raw = (CORPUS / ENTRY['source']).read_text()
defines = gen._defaults(ROOT, KEY)
program = analyze_program(parse_program(raw, KEY, defines), KEY)
constant = next(item for item in program.declarations if item.symbol.name == 'LUMA_WEIGHTS')
reads = []
for function in program.functions:
    for path, value, parent, child_index in all_nodes(function):
        if value.kind == 'id' and value.symbol_id == constant.symbol.id:
            reads.append((function, path, value, parent, child_index))
assert len(reads) == 1
owner, read_path, read, parent, child_index = reads[0]

sampler_ordinals = {name: index + 1 for index, name in enumerate(program.resources.samplers)}
bindings = []
output = None
for item in program.declarations:
    if item.symbol.storage == 'uniform':
        suffix = f'/S{sampler_ordinals[item.symbol.name]}' if item.symbol.name in sampler_ordinals else ''
        bindings.append(f'{item.symbol.name}:{item.type.display()}@{item.symbol.id}{suffix}')
    elif item.symbol.storage == 'output':
        output = f'{item.symbol.name}:{item.type.display()}@{item.symbol.id}'

local_source = raw.replace('const vec3 LUMA_WEIGHTS = vec3(0.299, 0.587, 0.114);\n\n', '')
local_source = local_source.replace('float luminance(vec3 rgb) {\n', 'float luminance(vec3 rgb) {\n    const vec3 LUMA_WEIGHTS = vec3(0.299, 0.587, 0.114);\n')
local_program = analyze_program(parse_program(local_source, KEY, defines), KEY)
gen.validate_capabilities(local_program, tuple(gen.APPROVED_CAPABILITIES), source_hash=ENTRY['raw_sha256'])
cpp = emit.render_typed_cpp(local_program, KEY, ENTRY['raw_sha256'], 'typed_projection',
                            'bind_' + KEY.replace('/', '_').replace(':', '_'))

data = {
    'key': KEY,
    'defines': defines,
    'raw_bytes': len(raw.encode()), 'raw_sha256': hashlib.sha256(raw.encode()).hexdigest(),
    'normalized_bytes': len(program.source.encode()), 'normalized_sha256': hashlib.sha256(program.source.encode()).hexdigest(),
    'function_tuple_sha256': digest(program.functions),
    'whole_program_sha256': whole_hash(program),
    'interface_sha256': interface_hash(program),
    'function_profiles': [[fn.signature.id, fn.name, len(fn.body), digest(fn), [[p.id, p.name, p.type.display(), p.direction] for p in fn.parameters]] for fn in program.functions],
    'declaration': {
        'symbol_id': constant.symbol.id, 'symbol': constant.symbol.name, 'storage': constant.symbol.storage,
        'writable': constant.symbol.writable, 'type': constant.type.display(), 'span': span(constant),
        'declaration_sha256': digest(constant), 'initializer_kind': constant.initializer.kind,
        'initializer_span': span(constant.initializer), 'initializer_sha256': digest(constant.initializer),
        'initializer_children': [[child.literal, child.literal_value, span(child), digest(child)] for child in constant.initializer.children],
    },
    'read': {
        'owner_id': owner.signature.id, 'owner': owner.name, 'path': read_path, 'span': span(read),
        'read_sha256': digest(read), 'type': read.type.display(), 'category': read.category,
        'parent_kind': parent.kind, 'parent_callee': parent.callee, 'parent_signature_id': parent.signature_id,
        'parent_type': parent.type.display(), 'parent_category': parent.category, 'parent_child_index': child_index,
        'parent_span': span(parent), 'parent_sha256': digest(parent),
        'first_argument_sha256': digest(parent.children[0]),
    },
    'bindings': bindings, 'output': output, 'resources': dataclasses.asdict(program.resources),
    'counted_loop_proof': dataclasses.asdict(program.counted_loop_proof),
    'diagnostic_local_cpp_bytes': len(cpp.encode()), 'diagnostic_local_cpp_sha256': hashlib.sha256(cpp.encode()).hexdigest(),
    'diagnostic_luminance_lines': [line for line in cpp.splitlines() if 'LUMA_WEIGHTS' in line or 'luminance(' in line or 'glsl::dot' in line],
}

profile_tuple = (
    'smooth-edge-luma-weights-v1', KEY, data['raw_sha256'], {},
    (constant.symbol.id, constant.symbol.name, constant.symbol.storage, constant.type.display(),
     span(constant), data['declaration']['declaration_sha256'], data['declaration']['initializer_sha256'],
     tuple((child.literal, child.literal_value, span(child), digest(child)) for child in constant.initializer.children)),
    (owner.signature.id, owner.name, read_path, span(read), digest(read), digest(parent), child_index),
    data['function_tuple_sha256'], data['whole_program_sha256'], data['interface_sha256'],
)
data['profile_tuple_repr'] = repr(profile_tuple)
data['profile_tuple_sha256'] = digest(profile_tuple)
print(json.dumps(data, indent=2))
