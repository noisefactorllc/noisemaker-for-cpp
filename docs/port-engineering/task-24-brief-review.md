# Task 24 Gather Sorted brief/oracle/audit review

## Verdict

**APPROVED.** The amended one-key exact-profile slice is sound. All frozen
identities and public oracles reproduce on the accepted Task 23 tree, and the
amendment resolves the prior numeric/emission mismatch by making the existing
clamp helper mandatory only for the authenticated Gather parent/site.

Reviewed brief SHA-256:
`a5184121126d75b32372440aae13ef9cde06006c5f4189607327e323e7d16e53`.

## Prior finding resolved by the amendment

The earlier brief described the exclusion model as native without requiring
the emitter to call the saturating helper. The amended brief now requires the
exact authenticated `int(round(...))` parent to emit as:

```cpp
glsl::detail::float_to_int32(glsl::round(/* authenticated argument */))
```

The helper already exists at `src/glsl_runtime.cpp:9`. The accepted Task 23
generic scalar constructor emitter does not call it and still projects Gather
as:

```cpp
std::int32_t brightestX = std::int32_t(glsl::round(...));
```

That baseline fact is now an intentional RED condition, not a contradiction.
The amendment requires parent-owned emission through the existing helper,
forbids changing generic scalar `int(float)` emission, locks the exact nested
spelling and absence of direct casts, and requires native execution of both
closed-scope exclusion controls. The admitted `[0,1]` domain remains unchanged;
the helper clamp is inactive for normative cases, and huge-value clamp/wrap
divergence remains explicitly non-normative. No runtime or numeric edit is
authorized.

## Independently reproduced evidence

### Accepted Task 23 gate and projection

- The Task 23 brief/audit/generator/JSON/report hashes are exactly the five
  values frozen in Task 24. The accepted Task 23 report and final independent
  review are present with SHA-256
  `961292d3b0f75f1b471b2a568f8fd6f8f344fbabb35508d012618d3e0ca6a28f`
  and
  `9e36cdc5b6fe86834f7eb0dfff60596531f9c21ef13ed8716a496aaf23dff7be`.
- Current publication is exactly 122 typed / 124 public / 88 remaining / 212
  corpus. Adding only Gather Sorted gives 123 / 125 / 87 / 212.
- Current typed/public list hashes are
  `9db3013a6b0f78d0b95fcb6713c54ace95e82d1545e796e7a380add23c009f0b`
  and
  `2b84fff4d6f35aec1ac6bcc35188d9893e3194c90b9c428775a7308ce1f6281a`.
  Projected hashes reproduce
  `df7750a48a77733e50f0e20072e291c2404e761932f6df8ddbcf8793d58fb6ac`
  and
  `bcf196794ff17ec62c1121347b3fe49a0907baa7ce3c3bd51352ec8a51fbac4e`.
- Gather's zero-based insertion is exactly 51, between
  `filter/pixelSort:findBrightest` and `filter/pixelSort:luminance`.
- `round` is absent from both the accepted capability vocabulary and the
  emitter builtin-name table. Gather remains untyped and its first blocker is
  exactly `24:26: unsupported builtin round`.

### Artifact and public-oracle integrity

- Audit, generator, JSON, report, and projection-script SHA-256 values reproduce
  exactly:
  `fa4e0481ea50534be05923cf2c673b9f45195315121fbac7cbd05bece4f21220`,
  `35d20a4428af390ed437f3c829a250a1974d254b66712c900d684d54a7e682d6`,
  `07dd6f31c3e2b5451cbde8fc0ae6f68ec7c3b06cd6296222ac938cdcee37a72a`,
  `b33894f0d69c97de5392d686bc9d5b469d672fc59f522b7b79c15604ae4299f6`,
  and
  `a864160c1c92f198003dbb1371d5814f268a18365d2775612f27bcc712d41409`.
- `node task-24-oracle-generator.mjs --check` succeeds against the pinned
  public CPU factory. It independently authenticates direct canonical/public
  identity, absence of an adapter, source/factory/runtime hashes, repeat
  identity, three-input immutability, and finite output.
- The JSON has exactly four normative cases, four normative mutations, two
  exclusion cases, and three exclusion controls. All four frozen F32 and RGBA8
  output hash pairs reproduce. Floor diverges on half/wide, ceil on the
  half-boundary case, loop-8 on width 67, and the synthetic saturating model is
  byte-identical on all normative cases. Negative-half native-model identity,
  away-from-zero divergence, and huge-positive wrap/clamp divergence also
  reproduce.

### Source, tree, site, and profile

- Raw source is 1,896 bytes with SHA-256
  `a45eb039bae3e7b0a5f804de68c441092b6b7826b594c4aa5221c22a6c7b1386`;
  normalized source is 1,185 bytes with SHA-256
  `28e7ad80ef7db266559deb4b822f52251ab899af61feb9f915e32c0ecce079a9`.
  Defines are `{}`.
- The program has only `main`. Individual-main, function-tuple, whole-program,
  and interface hashes reproduce
  `89ca9cc42483c88f4351e39338079ab5f742300493815982dff04ece432fba7e`,
  `6378f26aa15c43dda1ceba1d098d5b7f7fd76174618bbc5428e6659622cf8218`,
  `23120c79e838032a4ac54abeac0929d1dc2c7c89c895b083b68e6188b6f36fe3`,
  and
  `f18371bad7d92151cd361663a4b56266fffa2228b7b6379ad16518d9af8a8ed6`.
- There is exactly one `round`: path `(0,6,'e0',0,0)`, span
  `24:26-24:66`, signature `-38`, scalar-float rvalue, one scalar-float child.
  Round, argument, immediate int-parent, and declaration-statement repr hashes
  reproduce
  `a5f412a1949fdfae93b759bf1c01a22afb44f9a48e71710f2c54cdcdf312c625`,
  `a3797427a6fd439f07e4b1a5d33f7f13edcff528e71bee77a80489ae1697761d`,
  `b16eb98c5a1cef7a40f78c65448f5f127c5feaa7cfa64dfdda0e167283aaba3c`,
  and
  `3c98243330c489b4216d526ba594bac28177a8c3c1f1eb3799528ddbad358ea5`.
  The declaration is writable local `int brightestX`, symbol 13.
- Reconstructing the exact profile tuple gives SHA-256
  `a100420798a4964c67ec4b2e98a09c62e5ca5b3b0d7f2fe1eb7a8ff8180e43fa`.

### Loop, resources, fetches, and stack shape

- The sole loop is `38:5-48:6`, induction symbol 19, `0; s <
  NUM_SAMPLES; s++`, with local literal-const bound 64. Its loop-proof and
  program-proof hashes reproduce
  `c9df47f651e3ee7232826b3bf13ac40e29889e3d69a2d7a2f6dedecba5c579d4`
  and
  `dd9dc4392ed9350b896854ad13cee5a242281bbe2b791f19b28cd2bd361251ca`;
  depth/product/charge are 1/64/64 and the call graph is acyclic.
- Bindings reproduce exactly as three samplers
  `preparedTex:sampler2D@1/S1`, `rankTex:sampler2D@2/S2`, and
  `brightestTex:sampler2D@3/S3`, plus `fragColor:vec4@4`. There are no ordinary
  uniforms, source globals, varyings, blocks, derivatives, structs, arrays, or
  user helper functions.
- The tree contains one `textureSize`, three static `texelFetch` nodes, and no
  conditional exit. One pre-loop fetch plus one fetch for each of 64 loop trips
  plus one result fetch proves exactly 66 dynamic fetches per pixel.
- Re-running the process-local round exposure on accepted Task 23 still emits
  the frozen 3,413-byte diagnostic block with SHA-256
  `3961e66b3940a929c7adb5788d503327aad7d90b690c1f7723c53f03699d503a`.
  Its pixel body has one fixed 64-trip loop, one round call, three fetch calls,
  one texture-size call, and only fixed-size scalar/`Vec` automatic objects.
  It has no allocation, container, string, callback, exception, recursion,
  VLA, or `alloca` route. Exact compiler `.su` and Release disassembly remain
  correctly deferred to post-implementation verification.

### Accepted-Task-23 frontier rerun

The full emitter-aware first-blocker census on the actual 88 remaining keys is
unchanged from the audit: 31 globals, 19 unproved loops, 11 `dFdx`, 5 `fwidth`,
3 loop-cap, 3 index, 2 scalar XOR, 2 `round`, 2 varying, and one each of sampler
parameter emission, `all`, `any`, `floatBitsToUint`, `reflect`, `tanh`, matrix
return, `inout`, `mat4`, and uniform block. Gather projects cleanly after only
process-local scalar-round exposure; Posterize next fails at `fwidth` line 80.

The older audit's diagnostic `nmReindexStats` block hash changes after Task 23,
as the audit explicitly warned it could. This does not affect the chosen key or
any identity frozen by the Task 24 brief.

No repository file or Git state was changed.
