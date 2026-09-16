# classicNoisedeck palette override -- exhaustive sweep result

Ran `exhaustive_sweep_js.mjs` (against the frozen JS authority) then
`exhaustive_sweep_cpp.py` (against this lane's `noisemaker-dsl-cpu-case`
build), covering:

- All six palette effects this port's executor actually admits:
  classicNoisedeck/{cellNoise,colorLab,fractal,noise,shapeMixer,shapes}.
- classicNoisedeck/shapes3d:shapes3d is NOT swept: its DSL corpus record
  is `recordKind: "excluded"` (a pre-existing, unrelated 3D/volume-output
  limitation) -- this port's executor never admits it at all, with or
  without this change.
- All 56 palette indexes per effect (0 = no override, 1..55 = every table
  entry).
- Two sizes: 24x24 (square) and 37x13 (non-square). A genuine tiled/offset
  render was not covered: `noisemaker-dsl-cpu-case` (the CLI harness used
  for this sweep and by the DSL corpus parity lane) does not expose a
  tileOffset/renderScale flag, and extending it was out of scope for this
  fix. `run_pass`'s own tiling is otherwise already exercised elsewhere in
  the native suite and is unrelated to the palette-uniform precision this
  change addresses (tileOffset/fullResolution bind as ordinary scalars,
  not through the palette-uniform carrier).

Comparison: RGBA8 sha256, exact (matching this whole port's zero-tolerance
comparison convention and the DSL corpus parity lane's own method).
Float32-lane comparison was not separately captured: the CLI harness has
no such output flag; the native `test_palette_override_oracle.cpp` suite
(40 cases, all six effects, checked in from this lane's earlier commit)
does capture the raw float32 sha256 per case as a frozen native-test
regression subset.

## Result

```
total cases: 672
byte-exact: 672
errors (driver failed): 0
mismatches (wrong bytes): 0

FINAL DIVERGENCE COUNT: 0
```

Every one of the 672 rendered cases (6 effects x 56 entries x 2 sizes) is
byte-exact RGBA8 against the frozen JS authority.
