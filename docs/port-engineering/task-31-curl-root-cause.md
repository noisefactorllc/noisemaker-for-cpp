# Task 31 (Curl): root cause — `std::tanh` does not match V8's `Math.tanh`

Date: 2026-08-12
Author: integration owner

Supersedes the "undiagnosed parity failure" framing in
`task-31-curl-parity-diagnosis.md`. Two separate causes were found; neither is
a defect in the Curl port's structure.

## Cause 1 — the oracle never bound `time` (4 of 6 failures)

Fully documented in `task-31-curl-oracle-defect.md`
(`8248454e70cb85cc957300de9b8b5d8ad1861f99f8c626568cd2e10886f8d02f`).
`createCanonicalBindings` assigns `time: f32(time)` *after* spreading
`...uniforms`, so a `time` passed inside `uniforms` is discarded. The Curl
oracle passes it that way, so every frozen case is a `time = 0` render.

With `time` bound correctly, the C++ port matches JavaScript on **4 of 6**
cases. Those four "failures" were oracle artifacts.

## Cause 2 — transcendental last-bit disagreement (the remaining 2)

For the `negative-seed` case, exactly **one pixel of 24 differs, in one lane,
by 2 ULP** at f32 — not the systematic error the oracle bug had made it look
like.

Layer-by-layer comparison (C++ against the real JS factory, both driven with
identical inputs) shows:

| Layer | Result |
|---|---|
| `simplex3D` | **bit-identical** (8 samples, incl. negative seed) |
| `fbmSimplex3D` | **bit-identical** |
| `curlNoise3D` | **bit-identical** |
| `tanh(curl * intensity)` | **DIVERGES by 1 ULP at double** |

At the divergent pixel, the arguments to `tanh` are bit-identical in both
engines, and the results differ:

```
lane1   C++ bfb3039c4cf6c61f    JS bfb3039c4cf6c61e
lane2   C++ 3fe165f7aa9e3ea7    JS 3fe165f7aa9e3ea8
```

The JS runtime calls `Math.tanh` directly
(`noisemaker-for-cpu/src/csl/glsl-runtime.js:352`, `tanh: unary(Math.tanh)`),
and V8 implements it with its own fdlibm port rather than the platform libm.
Apple's `std::tanh` and V8's `Math.tanh` are both accurate but neither is
correctly-rounded, and they disagree in the last bit.

### Measured disagreement rates

400 doubles over [-4, 4), compared at double precision, inputs verified
bit-identical between engines:

| function | disagreements |
|---|---|
| `tanh` | **65/400 (16.2%)** |
| `exp` | 42/400 (10.5%) |
| `sin` | 17/400 (4.2%) |
| `cos` | 14/400 (3.5%) |
| `sqrt` | 0/400 |
| `pow` | 0/400 |

`sqrt` and `pow` agreeing is the sanity check — IEEE 754 requires `sqrt` to be
correctly rounded, so any harness reporting `sqrt` disagreement is broken.

## Two harness errors I made, corrected here

Recorded because both produce confidently wrong numbers:

1. **A first sweep reported 131/400 tanh disagreements and, impossibly, 158/400
   for `sqrt`.** Cause: the C++ helper returned a `static char buf[32]`, so all
   seven `H(...)` calls in one `printf` shared one buffer and printed the same
   value seven times. Every number from that sweep was meaningless. Fixed by
   converting the bit pattern to `uint64_t` and formatting inline.
2. **Ad-hoc probe binaries omitted `-ffp-contract=off`.** The project's CMake
   sets it deliberately; without it clang fuses `-4.0 + i*0.02` into an FMA and
   even the *inputs* stop matching JS. Any standalone comparison harness must
   use the same flags as the library, or it measures the wrong thing.

The layer-by-layer `simplex3D`/`curlNoise3D` comparisons above were run before
that flag was corrected; they nonetheless agreed bit-for-bit, so their
conclusion stands. The `tanh` conclusion was re-verified with the corrected
harness.

## Why 130 typed programs already pass with `sin`/`cos`

`sin` and `cos` disagree at ~4% at double precision, yet every shipped program
passes bit-exact parity. The reason is that most results are narrowed to f32
soon after, and a 1-ULP double difference almost always vanishes in that
narrowing. Curl is different: `tanh`'s result feeds further double arithmetic
(`* 0.5 + 0.5`, then the RIDGES/OUTPUT_MODE chain) before any narrowing, so the
difference survives to the output.

**This is a latent risk for every future program**, not a Curl quirk. Any
program whose transcendental result feeds more double arithmetic before
narrowing can expose it.

## The fix

Bit-exact parity with the JavaScript reference **cannot** be achieved by
calling `std::tanh`. The C++ runtime needs a `tanh` that reproduces V8's
result exactly — i.e. a port of the fdlibm `tanh` V8 uses
(`src/base/ieee754.cc`). fdlibm's `tanh` is short and self-contained, so this
is a well-bounded task.

Recommended sequence:

1. Port fdlibm `tanh` into the C++ runtime and route `glsl::tanh` to it.
2. Verify against a large randomized sweep versus `Math.tanh` — require
   **0 disagreements at double precision**, not merely at f32.
3. Fix `curl_oracle_generator.mjs` to bind `time` top-level, re-freeze
   `curl-oracles.json`, then re-run Curl parity. Expect 6/6.
4. Audit `exp` the same way before any program needing it is ported — it
   disagrees at 10.5% and no shipped program appears to stress it.
5. Leave `sin`/`cos` alone for now, but record that they are not bit-safe in
   the general case; if a future program exposes them, the same fdlibm
   treatment applies.

## Status

Curl remains backed out; the tree is green at the accepted Task 30 state. The
port's structure, profile, both authorities, and the new `tanh`/wide-`mod`
runtime are all correct — the blocker is the shared `tanh` implementation and a
defective oracle, both fixable and both now precisely identified.
