# Task 31 (Curl): the oracle is defective — `time` never reached the kernel

Date: 2026-08-12
Author: integration owner

## Root cause

`createCanonicalBindings` (`noisemaker-for-cpu/src/csl/glsl-kernel.js:20-61`)
builds the binding object in this order:

```js
return Object.freeze({
  renderScale: 1,
  speed: 0,
  seed: f32(seed),
  ...
  ...uniforms,          // <-- caller's uniforms spread HERE
  ...textures,
  resolution,
  fullResolution: completeResolution,
  tileOffset: tileOffset ?? new Float32Array(2),
  aspectRatio: f32(width / height),
  aspect: f32(width / height),
  time: f32(time),      // <-- OVERRIDES any `time` from uniforms
  globalTime: f32(time),
  deltaTime: f32(deltaTime),
  frame,
})
```

`time` is a **top-level option defaulting to 0**, and it is assigned *after*
the `...uniforms` spread. Any `time` passed inside `uniforms` is therefore
silently discarded.

`curl_oracle_generator.mjs:190` passes `time` inside `uniforms` and never sets
the top-level option:

```js
const kernel = bindCanonicalKernel(factory, {
  width, height, uniforms, textures: {},
  tileOffset: ..., fullResolution: ...,
})
```

**Every eligible Curl oracle case was therefore rendered with `time = 0`,**
regardless of the `time` value recorded in its own case metadata.

The same applies to `globalTime`, `deltaTime`, `frame`, `resolution`,
`fullResolution`, `tileOffset`, `aspect` and `aspectRatio` — all are assigned
after the spread and cannot be set through `uniforms`.

## Proof

Rendering the real pinned factory both ways and hashing full-surface F32:

| Case | oracle stored | JS, `time` in uniforms (broken) | JS, `time` top-level (correct) |
|---|---|---|---|
| default-seed0-time0 | `38fb7d9a…` | `38fb7d9a…` | `38fb7d9a…` |
| seed7-tiled-midtime | `a3da792e…` | `a3da792e…` | `e6f49b49…` |
| negative-seed-… | `6325f219…` | `6325f219…` | `6325f219…` |
| negative-intensity-… | `495aca12…` | `495aca12…` | `311e9b96…` |
| large-seed-… | `a138c72b…` | `a138c72b…` | `aa573876…` |
| two-pi-time-… | `865cfbf1…` | `865cfbf1…` | `7a006260…` |

The stored oracle column is **identical to the broken column in all six cases**.
That is conclusive: the frozen expectations are `time = 0` renders.

(`default-seed0-time0` and `negative-seed-…` agree across all three columns for
good reason — the first declares `time = 0`, and the second sets `speed = 0`,
which makes `a` and `b` time-independent since both are
`(trig(...) * speed + 1) / OCTAVES * 0.2`.)

## Consequence for the earlier parity verdict

The previous diagnosis recorded 4 genuine mismatches. With `time` bound
correctly, the C++ port **matches JavaScript on 4 of the 6 cases**:

| Case | JS correct | C++ | |
|---|---|---|---|
| default-seed0-time0 | `38fb7d9a…` | `38fb7d9a…` | match |
| negative-intensity-… | `311e9b96…` | `311e9b96…` | match |
| large-seed-… | `aa573876…` | `aa573876…` | match |
| two-pi-time-… | `7a006260…` | `7a006260…` | match |
| seed7-tiled-midtime | `e6f49b49…` | `09ccc733…` | **MISMATCH** |
| negative-seed-… | `6325f219…` | `37242a55…` | **MISMATCH** |

Four of the six reported failures were **artifacts of the defective oracle**,
not port defects. Two genuine divergences remain.

## The two genuine divergences

1. **`negative-seed-drives-negative-mod-operands`** — `seed = -13`, `scale = 0`,
   `speed = 0`. Time-independent (speed = 0), so this is unrelated to the oracle
   defect. A negative seed drives `v += float(seed) * 0.1271` negative, which is
   exactly the path that pushes lattice indices negative into
   `i = mod(i, 289)`. Prime suspect.
2. **`seed7-tiled-midtime`** — the only case with a non-trivial tile
   (`tileOffset [3,2]`, `fullResolution [13,11]`). Distinct from the seed case;
   likely a tiling-coordinate issue rather than a numeric one.

Note the direct `mod` rows still pass, so if (1) is a `mod` problem it is about
*which values reach the call*, not the operation.

## Required actions

1. **Fix `curl_oracle_generator.mjs`** to pass `time` as a top-level option, and
   re-freeze `curl-oracles.json`. The current file must not be used as a parity
   gate.
2. **Audit every other oracle in this project for the same defect.** Any
   generator that passes `time`, `frame`, `deltaTime`, `resolution`,
   `fullResolution`, `tileOffset`, `aspect` or `aspectRatio` through `uniforms`
   has silently frozen default values. Tasks 29 and 30 both passed full parity,
   which suggests their programs did not read the affected uniforms — but that
   is an inference and must be checked, not assumed.
3. Add a guard to future oracle generators: after binding, assert that the
   kernel actually observed the intended values rather than trusting the call.
