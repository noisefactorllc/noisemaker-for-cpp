from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path('.')
sys.path.insert(0, str(ROOT))

from tools.glslcpp import check_corpus, check_semantics
from tools.glslcpp import generate_typed_slice as gen
from tools.glslcpp import emit_typed_cpp as emit
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program

CORPUS = ROOT / 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6'
MANIFEST = json.loads((CORPUS / 'manifest.json').read_text())
ENTRIES = {x['program_key']: x for x in MANIFEST['programs']}
TYPED = {x['program_key'] for x in json.loads((ROOT / 'tools/glslcpp/typed_slice.json').read_text())['programs']}


def first_line(e: Exception) -> str:
    return str(e).splitlines()[0]


def classify(s: str) -> str:
    pairs = (
        ('unsupported top-level global declaration', 'global'),
        ('unsupported loop statement', 'loop'),
        ('unproved counted loop', 'loop'),
        ('counted loop', 'loop-cap'),
        ('unsupported builtin dFdx', 'dFdx'),
        ('unsupported builtin fwidth', 'fwidth'),
        ('unsupported builtin all', 'all'),
        ('unsupported builtin any', 'any'),
        ('unsupported builtin reflect', 'reflect'),
        ('unsupported builtin tanh', 'tanh'),
        ('unsupported builtin floatBitsToUint', 'floatBitsToUint'),
        ('unsupported builtin round', 'round'),
        ('unsupported matrix return type', 'matrix-return'),
        ('unsupported parameter direction inout', 'inout'),
        ('unsupported parameter direction out', 'out'),
        ('unsupported type mat4', 'mat4'),
        ('unsupported uniform block', 'uniform-block'),
        ('unsupported varying', 'varying'),
        ('unsupported index', 'index'),
        ('unsupported binary operator ^', 'scalar-xor'),
    )
    for needle, label in pairs:
        if needle in s:
            return label
    if 'sampler2D' in s and ('emission' in s or 'unsupported' in s):
        return 'sampler-param'
    return s


def program(key: str, source_override: str | None = None):
    e = ENTRIES[key]
    source = source_override if source_override is not None else (CORPUS / e['source']).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(source, key, defines), key)
    return e, source, defines, typed


remaining = sorted(set(ENTRIES) - TYPED - {'filter/invert:inv', 'synth/solid:solid'})
rows = []
for key in remaining:
    e, source, defines, typed = program(key)
    try:
        gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES, source_hash=e['raw_sha256'])
        validator = 'pass'
    except Exception as error:
        validator = first_line(error)
    try:
        emit.render_typed_cpp(typed, key, e['raw_sha256'], 'probe', 'bind_probe')
        emitter = 'pass'
    except Exception as error:
        emitter = first_line(error)
    globals_ = []
    for d in typed.declarations:
        if d.symbol.storage not in ('uniform', 'output', 'input'):
            globals_.append({
                'name': d.symbol.name,
                'type': d.type.display(),
                'const': bool(getattr(d, 'is_const', False) or getattr(d, 'const', False)),
                'has_initializer': bool(d.initializer),
                'span': f'{d.span.start_line}:{d.span.start_column}',
            })
    rows.append({
        'key': key,
        'source': e['source'],
        'raw_bytes': e['raw_bytes'],
        'raw_sha256': e['raw_sha256'],
        'normalized_bytes': e['normalized_bytes'],
        'normalized_sha256': e['normalized_sha256'],
        'defines': defines,
        'validator': validator,
        'validator_class': classify(validator),
        'emitter': emitter,
        'emitter_class': classify(emitter),
        'globals': globals_,
        'functions': [
            {
                'id': f.signature.id,
                'name': f.name,
                'return': f.return_type.display(),
                'params': [[p.name, p.type.display(), p.direction] for p in f.parameters],
                'body_statements': len(f.body),
            }
            for f in typed.functions
        ],
        'loop_proof': dataclasses.asdict(typed.counted_loop_proof),
        'resources': dataclasses.asdict(typed.resources),
    })

print(json.dumps({
    'corpus_revision': check_corpus.REVISION,
    'typed_count': len(TYPED),
    'public_count': len(TYPED) + 2,
    'remaining_count': len(remaining),
    'typed_sha256': hashlib.sha256(('\n'.join(sorted(TYPED)) + '\n').encode()).hexdigest(),
    'public_sha256': hashlib.sha256(('\n'.join(sorted(TYPED | {'filter/invert:inv', 'synth/solid:solid'})) + '\n').encode()).hexdigest(),
    'rows': rows,
}, indent=2))
