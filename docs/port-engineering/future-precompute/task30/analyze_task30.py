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
ENTRIES = {row['program_key']: row for row in MANIFEST['programs']}
SPEC = json.loads((ROOT / 'tools/glslcpp/typed_slice.json').read_text())
TARGETS = ('filter/extrude:extrude', 'filter/watercolor:wcSimplify',
           'synth/curl:curl', 'classicNoisedeck/caustic:caustic')


def digest(value: object) -> str:
    return hashlib.sha256(repr(value).encode()).hexdigest()


def list_digest(values: list[str]) -> str:
    return hashlib.sha256(('\n'.join(values) + '\n').encode()).hexdigest()


def span(value: object) -> str:
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


def load(key: str):
    entry = ENTRIES[key]
    raw = (CORPUS / entry['source']).read_text()
    defines = gen._defaults(ROOT, key)
    program = analyze_program(parse_program(raw, key, defines), key)
    return entry, raw, defines, program


def probe(program, source_hash, validator=(), emitter=()):
    old_caps, old_builtins = gen.APPROVED_CAPABILITIES, gen._BUILTINS
    old_names, old_types = dict(emit._BUILTIN_NAMES), dict(emit._TYPES)
    try:
        gen.APPROVED_CAPABILITIES = (*old_caps, *validator)
        gen._BUILTINS = frozenset((*old_builtins, *validator))
        emit._BUILTIN_NAMES.update({name: name for name in emitter})
        emit._TYPES.update({'bvec2': 'glsl::BVec2'} if 'bvec2' in emitter else {})
        try:
            gen.validate_capabilities(program, gen.APPROVED_CAPABILITIES,
                                      source_hash=source_hash)
            v = 'pass'
        except Exception as error:
            v = str(error).splitlines()[0]
        try:
            text = emit.render_typed_cpp(program, program.key, source_hash,
                                         'task30_probe', 'bind_task30_probe')
            e = 'pass'
            cpp = {'bytes': len(text.encode()), 'sha256': hashlib.sha256(text.encode()).hexdigest()}
        except Exception as error:
            e = str(error).splitlines()[0]
            cpp = None
        return {'validator': v, 'emitter': e, 'rendered_cpp': cpp}
    finally:
        gen.APPROVED_CAPABILITIES = old_caps
        gen._BUILTINS = old_builtins
        emit._BUILTIN_NAMES.clear(); emit._BUILTIN_NAMES.update(old_names)
        emit._TYPES.clear(); emit._TYPES.update(old_types)


typed_keys = [row['program_key'] for row in SPEC['programs']]
public_keys = sorted((*typed_keys, 'filter/invert:inv', 'synth/solid:solid'))
corpus_keys = [row['program_key'] for row in MANIFEST['programs']]
remaining = [key for key in corpus_keys if key not in set(typed_keys)]

hist = collections.Counter()
passing = []
for key in remaining:
    entry, _, _, program = load(key)
    initial = probe(program, entry['raw_sha256'])
    category = initial['validator'].split(': ', 1)[-1]
    hist[category] += 1
    if initial['validator'] == 'pass' or initial['emitter'] == 'pass':
        passing.append({'key': key, **initial})

rows = []
for key in TARGETS:
    entry, raw, defines, program = load(key)
    builtins = []
    calls = []
    binary = []
    parameters = []
    for function in program.functions:
        parameters += [{'owner': function.name, 'owner_id': function.signature.id,
                        'id': p.id, 'name': p.name, 'type': p.type.display(),
                        'direction': p.direction, 'span': span(p)} for p in function.parameters]
        for path, value in nodes(function):
            base = {'owner': function.name, 'owner_id': function.signature.id,
                    'path': list(path), 'span': span(value), 'sha256': digest(value),
                    'result_type': value.type.display(),
                    'argument_types': [c.type.display() for c in value.children]}
            if value.kind == 'builtin': builtins.append({**base, 'callee': value.callee})
            elif value.kind == 'call': calls.append({**base, 'callee': value.callee})
            elif value.kind == 'binary' and value.operator == '^': binary.append({**base, 'operator': '^'})
    extra = {}
    if key == 'filter/extrude:extrude':
        extra['closure_projection'] = probe(program, entry['raw_sha256'],
                                            ('all', 'lessThanEqual', 'bvec2'),
                                            ('all', 'lessThanEqual', 'bvec2'))
    elif key == 'synth/curl:curl':
        extra['first_gate_projection'] = probe(program, entry['raw_sha256'], ('tanh',), ('tanh',))
    elif key == 'classicNoisedeck/caustic:caustic':
        extra['first_gate_projection'] = probe(program, entry['raw_sha256'], ('floatBitsToUint',), ('floatBitsToUint',))
    rows.append({
        'key': key, 'source': entry['source'], 'raw_bytes': len(raw.encode()),
        'raw_sha256': hashlib.sha256(raw.encode()).hexdigest(),
        'normalized_bytes': len(program.source.encode()),
        'normalized_sha256': hashlib.sha256(program.source.encode()).hexdigest(),
        'defines': defines, 'function_count': len(program.functions),
        'function_tuple_sha256': digest(program.functions),
        'whole_program_sha256': digest((program.key, program.source, program.raw_source,
            program.declarations, program.functions, program.resources, program.body_status,
            program.local_type_names, program.structs, program.uniform_blocks,
            program.interface_symbols, program.builtin_symbols,
            program.counted_loop_proof, program.preprocessor_defines)),
        'interface_sha256': digest((program.declarations, program.resources,
            program.local_type_names, program.structs, program.uniform_blocks,
            program.interface_symbols, program.builtin_symbols, program.preprocessor_defines)),
        'resources': dataclasses.asdict(program.resources),
        'loop_proof': dataclasses.asdict(program.counted_loop_proof),
        'parameters': parameters, 'builtins': builtins, 'calls': calls,
        'scalar_xor_sites': binary,
        'initial_probe': probe(program, entry['raw_sha256']), **extra,
    })

projected_typed = sorted((*typed_keys, 'filter/extrude:extrude'))
projected_public = sorted((*projected_typed, 'filter/invert:inv', 'synth/solid:solid'))
payload = {
    'schema': 'noisemaker-for-cpp.future-precompute.task30.analysis.v1',
    'corpus_revision': REVISION,
    'baseline': {'typed_count': len(typed_keys), 'public_count': len(public_keys),
        'publicly_unported_count': len(set(corpus_keys) - set(public_keys)),
        'typed_ordered_sha256': list_digest(typed_keys),
        'public_ordered_sha256': list_digest(public_keys)},
    'projected_extrude': {'typed_count': len(projected_typed),
        'public_count': len(projected_public),
        'publicly_unported_count': len(set(corpus_keys)-set(projected_public)),
        'typed_ordered_sha256': list_digest(projected_typed),
        'public_ordered_sha256': list_digest(projected_public),
        'ordinal': projected_typed.index('filter/extrude:extrude'),
        'neighbors': projected_typed[projected_typed.index('filter/extrude:extrude')-1:projected_typed.index('filter/extrude:extrude')+2]},
    'remaining': {'absent_from_typed_including_manual': len(remaining),
        'publicly_unported_count': len(set(corpus_keys)-set(public_keys)),
        'validator_histogram': dict(sorted(hist.items())), 'pass_rows': passing},
    'candidates': rows,
}
out = Path(__file__).with_name('analysis.json')
out.write_text(json.dumps(payload, indent=2) + '\n')
print(out)
