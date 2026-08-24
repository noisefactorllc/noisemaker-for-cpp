from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('.')
sys.path.insert(0, str(ROOT))

REVISION = 'a024dc3a960cc44af454abc7aebce50456c194e6'
CORPUS = ROOT / 'tools/glslcpp/corpus' / REVISION
MANIFEST = json.loads((CORPUS / 'manifest.json').read_text())
SPEC = json.loads((ROOT / 'tools/glslcpp/typed_slice.json').read_text())


def list_digest(values):
    return hashlib.sha256(('\n'.join(values) + '\n').encode()).hexdigest()


typed_keys = [row['program_key'] for row in SPEC['programs']]
public_keys = sorted((*typed_keys, 'filter/invert:inv', 'synth/solid:solid'))
corpus_keys = [row['program_key'] for row in MANIFEST['programs']]

print('=== CURRENT (live, pre-Extrude) state ===')
print('corpus total:', len(corpus_keys))
print('typed count:', len(typed_keys))
print('public count:', len(public_keys))
print('publicly unported:', len(set(corpus_keys) - set(public_keys)))
print('typed_ordered_sha256:', list_digest(typed_keys))
print('public_ordered_sha256:', list_digest(public_keys))
print('has focusBlur in typed:', 'mixer/focusBlur:focusBlur' in typed_keys)
print('has extrude in typed:', 'filter/extrude:extrude' in typed_keys)

projected_typed = sorted((*typed_keys, 'filter/extrude:extrude'))
projected_public = sorted((*projected_typed, 'filter/invert:inv', 'synth/solid:solid'))
ordinal = projected_typed.index('filter/extrude:extrude')

print()
print('=== PROJECTED (after adding Extrude) state ===')
print('typed count:', len(projected_typed))
print('public count:', len(projected_public))
print('publicly unported:', len(set(corpus_keys) - set(projected_public)))
print('typed_ordered_sha256:', list_digest(projected_typed))
print('public_ordered_sha256:', list_digest(projected_public))
print('ordinal (0-based):', ordinal)
lo = max(0, ordinal - 1)
hi = min(len(projected_typed), ordinal + 2)
print('neighbors:', projected_typed[lo:hi])

out = {
    'corpus_revision': REVISION,
    'current_live_state': {
        'corpus_total': len(corpus_keys),
        'typed_count': len(typed_keys),
        'public_count': len(public_keys),
        'publicly_unported_count': len(set(corpus_keys) - set(public_keys)),
        'typed_ordered_sha256': list_digest(typed_keys),
        'public_ordered_sha256': list_digest(public_keys),
    },
    'projected_after_extrude': {
        'typed_count': len(projected_typed),
        'public_count': len(projected_public),
        'publicly_unported_count': len(set(corpus_keys) - set(projected_public)),
        'typed_ordered_sha256': list_digest(projected_typed),
        'public_ordered_sha256': list_digest(projected_public),
        'ordinal': ordinal,
        'neighbors': projected_typed[lo:hi],
    },
}
Path(__file__).with_name('task30_projection_result.json').write_text(json.dumps(out, indent=2) + '\n')
print()
print('wrote', Path(__file__).with_name('task30_projection_result.json'))
