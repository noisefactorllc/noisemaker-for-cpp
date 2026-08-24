# Task 31: exact ordinal blast radius of inserting Caustic at ordinal 0

Measured by the integration owner against the live 130-typed tree.

`classicNoisedeck/caustic:caustic` sorts alphabetically first, so it takes typed
ordinal **0** and shifts every existing program's `typed_NN` namespace by +1.
Task 30 inserted at ordinal 25 and shifted only the programs after it; this one
shifts all 130.

## Why the frozen historical hashes are SAFE

Historical reconstruction removes the later-added program(s) before
regenerating. With Caustic removed, the remaining 130 programs occupy ordinals
0..129 exactly as they do today, so reconstruction reproduces the frozen Task
28/29/30 outputs byte-for-byte. Ordinal-0 insertion does **not** endanger frozen
reconstruction hashes.

This should be asserted explicitly, not assumed: the Task 31 Python tests must
include a "removing only Caustic regenerates the accepted Task 30 outputs
byte-for-byte" test, matching the pattern already used for Tasks 28→29 and
29→30.

## Exactly what must be updated (live assertions only)

Every site below shifts by +1. This list is complete as of
`tests/test_typed_generator.py` at the current revision; re-derive before
editing, since line numbers move.

### Explicit ordinal index assertions (3)

| Line | Assertion | New value |
|---:|---|---:|
| 11155 | `assertEqual(77, typed.index(SMOOTH_EDGE_KEY))` | 78 |
| 13976 | `assertEqual(111, typed.index(FOCUS_BLUR_KEY))` | 112 |
| 14649 | `assertEqual(25, typed.index(EXTRUDE_KEY))` | 26 |

### `namespace typed_NN` string assertions (9)

| Line | Current | New |
|---:|---|---|
| 7607 | `typed_22` (degauss) | `typed_23` |
| 9041 | `typed_2` (lens) | `typed_3` |
| 9042 | `typed_59` (prismatic) | `typed_60` |
| 9043 | `typed_52` | `typed_53` |
| 9045 | `typed_51` | `typed_52` |
| 11299 | `typed_77` (smooth) | `typed_78` |
| 12255 | `typed_123` (perlin) | `typed_124` |
| 14054 | `typed_111` (focus) | `typed_112` |
| 14672 | `typed_25` (extrude) | `typed_26` |

### Embedded binder source string (1)

| Line | Current | New |
|---:|---|---|
| 1362 | `std::make_shared<typed_53::State>(...)` | `typed_54` |

Total: **13 sites**, all mechanical.

## Native tests

No hardcoded `typed_NN` occurrences exist in `tests/test_generated_kernels.cpp`
or `tests/test_typed_slice.cpp` (verified by `rg -c`), so the native suite needs
no ordinal work. Native tests bind by public key and factory name, both of
which are ordinal-independent.

## Caution

Do **not** "fix" these by loosening the assertions to regex-normalized ordinals.
They are deliberately exact: they pin which generated namespace a given program
occupies, and normalizing them away would hide a real class of regression. The
reconstruction tests already normalize ordinals where normalization is the
correct semantics (`ordinal.sub("typed_ORDINAL", ...)` at
`tests/test_typed_generator.py:1504-1508`); the live assertions above are a
different, intentionally stricter contract.
