from __future__ import annotations

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
KEY = 'filter/extrude:extrude'

entry = ENTRIES[KEY]
raw = (CORPUS / entry['source']).read_text()
defines = gen._defaults(ROOT, KEY)
program = analyze_program(parse_program(raw, KEY, defines), KEY)

# snapshot state BEFORE any patch, to compare after, proving restoration
snap_caps_before = gen.APPROVED_CAPABILITIES
snap_builtins_before = frozenset(gen._BUILTINS)
snap_names_before = dict(emit._BUILTIN_NAMES)
snap_types_before = dict(emit._TYPES)

def probe(validator_extra=(), emitter_extra=(), add_bvec2_type=False):
    old_caps, old_builtins = gen.APPROVED_CAPABILITIES, gen._BUILTINS
    old_names, old_types = dict(emit._BUILTIN_NAMES), dict(emit._TYPES)
    try:
        gen.APPROVED_CAPABILITIES = (*old_caps, *validator_extra)
        gen._BUILTINS = frozenset((*old_builtins, *validator_extra))
        emit._BUILTIN_NAMES.update({name: name for name in emitter_extra})
        if add_bvec2_type:
            emit._TYPES.update({'bvec2': 'glsl::BVec2'})
        try:
            gen.validate_capabilities(program, gen.APPROVED_CAPABILITIES, source_hash=entry['raw_sha256'])
            v = 'pass'
        except Exception as error:
            v = str(error).splitlines()[0]
        try:
            text = emit.render_typed_cpp(program, program.key, entry['raw_sha256'], 'task30_gates', 'bind_task30_gates')
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

print('=== gate 1: no patches (baseline current gates) ===')
r0 = probe()
print(json.dumps(r0, indent=2))
assert r0['validator'] == 'filter/extrude:extrude:159:23: unsupported builtin all'
assert r0['emitter'] == 'filter/extrude:extrude:159:27: unsupported builtin lessThanEqual'
print('CONFIRMED baseline validator/emitter first-rejection sites.')

print()
print('=== gate 2a: emitter-only projection with validator fully untouched ===')
print('(sanity check: widening ONLY the emitter still leaves the validator failing at the earliest node, "all")')
r1a = probe(validator_extra=(), emitter_extra=('all', 'lessThanEqual', 'bvec2'), add_bvec2_type=True)
print(json.dumps(r1a, indent=2))
assert r1a['emitter'] == 'pass', 'expected emitter to render the whole program'
assert r1a['validator'] == 'filter/extrude:extrude:159:23: unsupported builtin all'
print('CONFIRMED: with validator builtin/capability set untouched, validator still fails at the first node (all), as expected.')

print()
print('=== gate 2b: the actual precompute closure_projection technique ===')
print('(widen BOTH validator capability/builtin set AND emitter name/type map with the same three identifiers: all, lessThanEqual, bvec2)')
r1b = probe(validator_extra=('all', 'lessThanEqual', 'bvec2'), emitter_extra=('all', 'lessThanEqual', 'bvec2'), add_bvec2_type=True)
print(json.dumps(r1b, indent=2))
assert r1b['emitter'] == 'pass', 'expected emitter to render the whole program'
assert 'bvec2' in r1b['validator'] and '159:27' in r1b['validator'], r1b['validator']
print('CONFIRMED: even after widening the validator BUILTIN/capability set to admit all/lessThanEqual/bvec2 as callable names,')
print('the validator STILL independently rejects at 159:27 because bvec2 fails a SEPARATE typed-type admission check')
print('unrelated to the builtin/capability list. This proves builtin admission and type admission are two distinct')
print('authorities in the validator, and the implementation needs an identity-scoped TYPE visit in addition to builtin admission.')

print()
print('=== gate 3: restoration proof (state must equal pre-probe snapshot) ===')
assert gen.APPROVED_CAPABILITIES == snap_caps_before, 'APPROVED_CAPABILITIES leaked'
assert frozenset(gen._BUILTINS) == snap_builtins_before, '_BUILTINS leaked'
assert dict(emit._BUILTIN_NAMES) == snap_names_before, '_BUILTIN_NAMES leaked'
assert dict(emit._TYPES) == snap_types_before, '_TYPES leaked'
print('CONFIRMED: all four monkeypatched globals restored to pre-probe state after try/finally.')

print()
print('ALL GATE CHECKS PASSED')
