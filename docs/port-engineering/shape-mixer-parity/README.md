# Shape Mixer182 parity package

This package freezes the independent canonical JavaScript authority for
`classicNoisedeck/shapeMixer:shapeMixer` with exact `LOOP_OFFSET=10`. C++ output
never participates in expected data.

The 42 fixtures comprise 20 mode cases (`blendMode=0..9`, scalar and vector)
and 22 focused cases. Every case stores both complete input surfaces, the
complete expected output as raw Float32 words, and RGBA8 bytes captured
independently from canonical `Surface.toRgba8()`. All surface arrays use
top-down storage coordinates. The canonical pass runner supplies bottom-left
fragment coordinates; nearest and linear samplers apply the authority runtime's
own y conversion.

Each fixture also freezes pre/post Float32 SHA-256 and exact immutability for
both inputs on three fresh routes: canonical, canonical repeat, and public
catalog. The include validator requires the exact route schema and equal hashes.

The custom comparer rejects dimensions and lane/byte counts before iteration,
compares every raw Float32 word, then compares every independent RGBA8 byte. It
self-tests equal-area shape mismatch, signed zero, distinct quiet-NaN payloads,
the final alpha lane, a byte-only mismatch, and short/long expected arrays.

Mutation evidence is classified honestly:

- rendered behavioral rows are one-anchor/one-replacement canonical factory
  mutants with named raw-word witnesses;
- direct-helper rows cover published vector/scalar geometric words and wide-mod
  cases that require negative or specially chosen operands;
- structural-only rows rely on the authenticated frontend/profile/emitter
  identities and never claim fabricated pixel divergence.

Four non-pixel facts are explicit in the JSON/report. The frozen rendered
mode-5 inputs are positive, so negative-operand `fmod` behavior is direct-only;
a fourth `linearToSrgb` loop iteration writes beyond a three-lane typed array
and is rejected structurally; inverse OKLab matrices are authenticated globals
but their conversion function is unreachable from `main`; and omitting only a
vector helper's final narrowing is immediately rematerialized by the factory.

Run from `/Users/aayars/platform/noisemaker-for-cpp`, with all disposable state
outside the repository:

```sh
SHAPE_MIXER_TMP=/tmp/noisemaker-cpp-shapemixer182-oracle-repair
mkdir -p "$SHAPE_MIXER_TMP"/{pycache,tmp,cache,node-cache}
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SHAPE_MIXER_TMP/pycache" TMPDIR="$SHAPE_MIXER_TMP/tmp" XDG_CACHE_HOME="$SHAPE_MIXER_TMP/cache" python3 -B docs/port-engineering/shape-mixer-parity/shape_mixer_frontend_probe.py --check
NODE_REPL_HISTORY="$SHAPE_MIXER_TMP/node-cache/repl-history" npm_config_cache="$SHAPE_MIXER_TMP/node-cache" TMPDIR="$SHAPE_MIXER_TMP/tmp" PYTHONPYCACHEPREFIX="$SHAPE_MIXER_TMP/pycache" node docs/port-engineering/shape-mixer-parity/shape_mixer_parity_oracle_generator.mjs --write
NODE_REPL_HISTORY="$SHAPE_MIXER_TMP/node-cache/repl-history" npm_config_cache="$SHAPE_MIXER_TMP/node-cache" TMPDIR="$SHAPE_MIXER_TMP/tmp" PYTHONPYCACHEPREFIX="$SHAPE_MIXER_TMP/pycache" node docs/port-engineering/shape-mixer-parity/shape_mixer_parity_oracle_generator.mjs --check
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SHAPE_MIXER_TMP/pycache" TMPDIR="$SHAPE_MIXER_TMP/tmp" XDG_CACHE_HOME="$SHAPE_MIXER_TMP/cache" python3 -B tools/glslcpp/generate_shape_mixer_native_oracle_include.py --check
```

The native include generator's `--write` owns only
`tests/oracles/shape_mixer182_expected.inc` and its sidecar. That output belongs
to the native parity owner and is not written by the oracle lane.
