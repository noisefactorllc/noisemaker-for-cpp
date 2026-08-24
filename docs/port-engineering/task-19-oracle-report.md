# Task 19 frozen external oracle report

The Task 19 external oracle contract is frozen for exactly
`classicNoisedeck/refract:refract` and its proposed
`fixed-array-in-parameter-v1` profile. No repository file was changed and no
Git command was used.

The generator binds pinned `canonicalKernelFactories` directly through
`bindCanonicalKernel`, executes through `runPass`, and stores canonical
`Surface` output. It does not reimplement convolution, derivative kernels,
array passing, wrapping, or blending.

Artifacts:

- `task-19-oracle-generator.mjs` — SHA-256 `a9ff40af61e15c6a73c34a8b844ca2f41da5be1d2ae85e957d2805a8da0d7a30`
- `task-19-oracles.json` — SHA-256 `169cb5607777051de3962fdbedd32d7dab4ac2095d6b356041c48bccc3c41c88`

The fixture is a top-down 11x9 non-square formula `Float32Array`, rendered to
a top-down 9x7 destination with `tileOffset=[128,64]` and
`fullResolution=[1024,768]`. The latter is deliberately greater than the
output resolution, so the displacement-budget branch runs with a frozen cap
of `0.25`. The 13.7f case retains its 0.137f displacement while the 29.9f,
73.4f, and 43.2f cases select the cap. All mode-1 cases call canonical
`derivX` then `derivY`, meaning their distinct fully initialized
`deriv_x[9]`/`deriv_y[9]` arrays are each passed into `convolve`; that helper
also initializes and reads every `offset[0..8]` and `kernel[0..8]` through its
proved `i=0..8` loop.

The three mode-1 fixtures cover all wrap branches and all mix-position
branches: mirror/difference with mix below 0.5, repeat/overlay at exact 0.5,
and clamp/soft-light above 0.5. The additional mode-0 mirror/mix case locks
the control path that does not call either derivative helper. All amount and
direction values are explicit nondefault F32 values; their mapped offset
widths are respectively 2, 5, 14, and 8.

Four additional direct canonical mode-1 fixtures hold the repeat/29.9f/
137.6f/exact-half-mix context constant and select blend modes 2, 3, 7, and
15. They isolate the canonical typed-array-object ternary behavior while still
running both derivative tables and both `convolve` calls.

Every case renders twice with fresh input and destination surfaces. A mismatch
in either F32 bytes or RGBA8 bytes aborts generation before freezing the
oracle. The JSON includes raw/normalized source digests, canonical-runtime and
factory-text digests, empty define map, exact binding order, F32 uniform
words, top-down lane probes, hashes, and repeat identity.

| Case | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- |
| `mode-1-mirror-difference-mix-under-half` | `d173f4368e000081b9b3921caccfd02790284c025ad5bd69d605f7310a23e2e2` | `9f345b48aafb6d69ec9d7757a161f86a103e92a7a2efdadd5eba5d3b8b7ad8c3` |
| `mode-1-repeat-overlay-mix-half` | `6e02e60356ea964074be3b941e5ef976eeb5dfd4ee12041b8ab5cae484f2dea2` | `e71609cfd1cfba0c3977abceb360939d22638858df33e02b551783f87d0c0fc1` |
| `mode-1-clamp-softlight-mix-over-half` | `3d38aee57222eb8460953f2a1e86418992f60c220b668b357d63f260346db56b` | `25152ac17ca38d55d15e1c7f02c5cea715f659e9f4d2bc04cffbd58b10d4aa86` |
| `mode-0-mirror-mix-control` | `3d791dbae4d93b61ab31f06b88105678c751ea3d369be9705661ed3a29879a0e` | `24841a3ec260bb15d549f066207c52a2e82be2fa22743d81feb1995201f28af9` |
| `mode-1-blendMode-2-truthy-typed-array-noop` | `165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24` | `13a15bd48e6f739c5ec9e3f08affe0fe2c115418341a3b2e1742d8d3868e03e0` |
| `mode-1-blendMode-3-truthy-typed-array-noop` | `165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24` | `13a15bd48e6f739c5ec9e3f08affe0fe2c115418341a3b2e1742d8d3868e03e0` |
| `mode-1-blendMode-7-truthy-typed-array-noop` | `165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24` | `13a15bd48e6f739c5ec9e3f08affe0fe2c115418341a3b2e1742d8d3868e03e0` |
| `mode-1-blendMode-15-truthy-typed-array-noop` | `165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24` | `13a15bd48e6f739c5ec9e3f08affe0fe2c115418341a3b2e1742d8d3868e03e0` |

## Vector-equality compatibility contract

The four authored source assignments are:

- mode 2: `(color2 == vec4(0.0)) ? color2 : max(1.0 - ((1.0 - color1) / color2), vec4(0.0))`
- mode 3: `(color2 == vec4(1.0)) ? color2 : min(color1 / (1.0 - color2), vec4(1.0))`
- mode 7: `(color2 == vec4(1.0)) ? color2 : min(color1 * color1 / (1.0 - color2), vec4(1.0))`
- mode 15: `(color1 == vec4(1.0)) ? color1 : min(color2 * color2 / (1.0 - color1), vec4(1.0))`

In the pinned canonical factory, each equality constructs a
`PooledFloat32Array` of lane booleans and that object becomes the JavaScript
ternary condition. The object is always truthy. The generated true arm is a
bare `color1` or `color2` expression, while only the false arm contains the
`.reduce(..., middle)` write. Therefore all four selected blend-mode branches
leave the zero-filled `middle` unchanged. With exact-half mix, `blend` returns
zero RGB; `main` replaces only `color.rgb`, so sampled alpha survives. The
three probes in each new JSON case explicitly freeze those zero RGB words and
nonzero alpha words.

The required source-specific post-transform behavior is thus a no-op on
`middle` for exactly these four key/signature/guard/predicate/arm shapes. It
must not emit a scalar `glsl::Vec4::operator==` ternary assignment. As a
read-only sensitivity check, replacing only the four typed-array conditions
in an in-memory copy of the same pinned factory with scalar all-lane booleans
produced distinct mode-1 F32 hashes:

| blendMode | Direct canonical F32 | Scalar-boolean mutant F32 |
| ---: | --- | --- |
| 2 | `165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24` | `9efce411c9e2ae02ca5019613d82090b07675e2eebe05ae2ab70bf7e6fb1e9da` |
| 3 | `165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24` | `23e31fcbcbf1a5abd6a5280f9ed7b6860c43c0230c6f51690322323832c38b4f` |
| 7 | `165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24` | `c835dcd727d0e3c71037d0bf6d5101f260f593ce777fca9548a1dabbec33abba` |
| 15 | `165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24` | `f26fa3fdb8bd3ae38497e29d1640469609cfdb2203656f01b94fae6858fb483f` |

Those mutant hashes are diagnostic evidence only; the frozen JSON contains
only direct canonical results.

## Array ABI and numeric notes

- Canonical JavaScript passes each `kernel` as an ordinary Array reference,
  not a copied array. This source's `convolve` only reads that reference and
  does not retain it, so a native `const std::array<double,9>&` and a by-value
  copy are observationally indistinguishable *only for this locked source*.
  A parameter write, array identity observation, escape, callback, or
  post-call caller read would make that substitution unsafe; the implementation
  proof must reject all such drift.
- `deriv_x` and `deriv_y` are zero-filled ordinary JS Number arrays. Their
  scalar table arithmetic and `kernelWeight` retain Number precision until
  vector/builtin/output boundaries. Native lowering must preserve that with
  zero-initialized `double[9]`-equivalent storage, not F32 scalar arrays.
- `offset` is instead an array of zeroed F32 vector containers in canonical
  code. Its correct narrow native form is zero-initialized
  `std::array<glsl::Vec2,9>`, preserving vector write/storage boundaries.
- `createCanonicalBindings` spreads explicit uniforms without automatic
  rounding. The generator calls `Math.fround` for amount, direction, and mix
  before binding and records their words. Native tests must consume those
  recorded F32 values rather than host double spellings such as `13.7`.
- `Surface` rows are top-down while `runPass` supplies bottom-left
  `fragCoord`; the JSON's three probes per case and byte layout lock that
  orientation. RGBA8 hashes complement, but cannot replace, F32 hashes and
  lane words because conversion rounds/clamps values.

Verification performed:

```text
node docs/port-engineering/task-19-oracle-generator.mjs --check
ok task-19-oracles.json
```

`--check` recomputes all eight direct canonical cases and byte-compares the
complete existing JSON. It performs no write.
