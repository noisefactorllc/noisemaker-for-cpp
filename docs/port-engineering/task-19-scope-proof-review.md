# Task 19 frozen scope/proof/ABI/oracle review

## Decision

**NOT APPROVED.** The proposed fixed-array ABI is coherent, but the frozen
whole-program design misses one already-known canonical-JavaScript semantic
repair in Refract's `blend` helper. That is a P1 parity hole, and the four
oracles deliberately avoid the affected public `blendMode` values. Stack
acceptance is also under-specified for this first split caller/callee table
profile (P2).

This was a read-only repository review. I invoked no Git command and changed
no repository file. This `/tmp` review is the only file written.

## P1 — Refract needs the vector-conditional compatibility repair, but Task 19 specifies only arrays

Refract contains four ternary assignments guarded by vector equality:

- source lines 127, 130, 142, and 166;
- public `blendMode` values 2, 3, 7, and 15.

The canonical JavaScript does not implement these as scalar all-lane equality.
At `canonical-kernels.js:6345-6349`, `:6360-6361`, and `:6384-6385`, each
condition constructs a `PooledFloat32Array` of lane comparisons and uses that
object directly as the JavaScript ternary condition. Every object is truthy.
Moreover, the generated `.reduce(..., middle)` write appears only in the false
arm, so the always-taken true arm leaves `middle` unchanged. The four canonical
arms are therefore source-locked no-ops on `middle`, not ordinary GLSL vector
equality conditionals.

The current C++ path would not match that behavior:

- `glsl::Vec::operator==` is a scalar boolean
  (`include/noisemaker/glsl_types.hpp:121`).
- The generic emitter renders the boolean expression and a normal C++ ternary
  (`tools/glslcpp/emit_typed_cpp.py:636-645`).
- No Refract compatibility transform is registered. The only relevant repair
  is inside `coalesce-uv-alias-v1`, is key/signature locked to Coalesce, and
  matches `blend(vec4, vec4, int, float)` with `mode`/`factor` parameters
  (`generate_typed_slice.py:305-395`). Refract instead has
  `blend(vec4, vec4)` and reads global `blendMode`/`mixAmt`.

The existing Coalesce repair proves this is an established canonical-runtime
compatibility issue rather than a speculative interpretation. Task 19's brief
does not mention a Refract repair, a new compatibility-transform entry, its
structural proof, or its boundary ordering relative to the proposed
whole-program array fingerprint.

### Reproduction

I rendered the same frozen Task 19 input/context in mode zero, changing only
`blendMode`. I compared the pinned canonical factory with an otherwise
identical in-memory factory whose four typed-array-object predicates were
replaced by scalar all-lanes booleans—the behavior the current C++ `Vec ==`
and ternary would provide.

| blendMode | canonical F32 SHA-256 | scalar-boolean F32 SHA-256 |
| ---: | --- | --- |
| 2 | `fe10460e38e63ea876aec9f4388e5dd6500b31cdf7f73b356cfced61495d28af` | `56335614ff79ae07da785a7ec5c06541eb09284080dd4618448b66653a6e4da0` |
| 3 | `fe10460e38e63ea876aec9f4388e5dd6500b31cdf7f73b356cfced61495d28af` | `837716281fc1d3038efe8850ba1fa66032d23e429e708fa04079c709865880c6` |
| 7 | `fe10460e38e63ea876aec9f4388e5dd6500b31cdf7f73b356cfced61495d28af` | `bb3e515298beae12ede739892179a8d2e327fa69b9a518a734778072709b7891` |
| 15 | `fe10460e38e63ea876aec9f4388e5dd6500b31cdf7f73b356cfced61495d28af` | `fd5476250283bfa7f9175ffbc4b7ff3b1268677eb2f0ee66dcd473432601ff45` |

All four diverge. This occurs on mode zero, before the new array path matters,
so a correct array proof cannot compensate for it.

The frozen external cases use blend modes 5, 13, 17, and 10 only. They would
all pass an implementation that emits the wrong behavior for 2, 3, 7, and
15, even though `blendMode` remains an unrestricted required public integer
binding.

### Required correction

Freeze a Refract-specific compatibility transform, or a rigorously
source/key/signature-locked reuse of the existing vector-conditional repair,
that proves exactly the four authored mode guards, equality operands/constants,
true symbols, false builtins, assignment target, and nested control ancestry,
then preserves the canonical no-op on `middle`. Require zero/missing/duplicate/
near-match failures as Coalesce does.

Specify whether the Task 19 structural proof and hard-coded function
fingerprint authenticate the post-transform tree; both validator and emitter
must reject the authentic-source but untransformed tree and any forged or
partially transformed version. Add direct canonical/native F32 oracles for all
four affected blend modes (mode zero is sufficient to isolate this issue),
plus their hashes/probes/repeat identity. The implementation scope is not safe
to freeze as “array-only” until this is included.

## P2 — stack evidence does not define the maximum live call path

Task 19 is the first proposed table profile whose 144-byte raw live payload is
split across frames: a 72-byte `Kernel9` in `derivX` or `derivY` remains live
while `convolve` owns a 72-byte `Offsets9`. A `.su` record is per emitted
function, while Debug may retain `pixel -> derivX/derivY -> convolve` and
Release may inline some or all of that chain.

The brief asks for Debug/Release “frames” but does not state which symbols must
be captured or how to report the maximum dynamic call path. Reporting only
`pixel`, or only `convolve`, could satisfy the wording while omitting the
simultaneously live caller table.

Require `.su` evidence for `pixel`, `derivX`, `derivY`, and `convolve` (plus
optimizer-created/inlined clones), with static/dynamic classification and the
maximum non-inlined mode-one call-chain sum in Debug and Release. Where Release
inlines, retain the resulting containing-frame record and code/disassembly
evidence. Keep that full-stack figure separate from the independently verified
144-byte raw table payload.

## Verified design evidence outside the findings

- Conditional count arithmetic is correct: the accepted Task 18 projection
  is 112 typed / 114 public / 98 unported; one new corpus key yields
  **113 / 115 / 97** from 212. The current repository is still at the earlier
  110 / 112 / 100 state, so the Task 19 numbers are properly conditional, not
  claims about current implementation state.
- Fresh raw/normalized hashes are
  `d9675b5de9c329aa619f4ef68129611faac8cbe515b6e80aa8528c593a49cfa2`
  /
  `bff1818ad5db7e637a01d6f10476cebba8ac04d6ffdf467d02508fa23671757e`;
  retained runtime defines are exactly empty.
- Fresh canonical factory text hash is
  `b404a801dea1ba438da7bad20d7cae059d0aa7f25c76610221ca07546fdfe2f6`;
  canonical runtime hash is
  `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`.
- Typed declarations/resources reproduce the exact eleven-field source order,
  `inputTex` sampler, `fragColor` output, `uses_texture=True`, and
  `uses_derivatives=False`. Metadata confirms defaults and `mixAmt <- mix`.
- Semantic analysis records exactly `convolve(vec2, in float[9], bool) ->
  vec3`; the array parameter has direction `in`. Its fresh function-tuple hash
  is the stated
  `ccde114d367313d1feb218c7f956df4059534b5c139c757a30ae156292e9cc09`.
- The program proof is one exact nine-trip `i=0; i<9; i++` loop, depth one,
  lexical product nine, entrypoint charge 18, and an acyclic call graph.
- Independent recursive census found exactly 30 index expressions: nine
  literal stores in each caller, nine literal `offset` stores, one
  `offset[i]` read, and two `kernel[i]` reads. Each caller array is passed once
  as resolved argument two after complete initialization and has no post-call
  use. The caller activations are serial; the callee neither writes nor escapes
  the direction-`in` array.
- `const std::array<double, 9>&` is observationally safe for this exact
  synchronous read-only callee and avoids introducing source-level copy ABI.
  Caller Number tables require `double`; the canonical offset elements are
  `PooledFloat32Array` vectors and require `glsl::Vec2`. A local compile-time
  size check produced 72 bytes for `Kernel9`, 72 for `Offsets9`, and 144 raw
  simultaneously live bytes.
- The ordinary non-array vocabulary is already admitted: all remaining typed
  types, statement/expression kinds, operators, and builtins are in current
  allowlists. Current validation stops at the expected array-parameter error.
- `node task-19-oracle-generator.mjs --check` returned
  `ok task-19-oracles.json`. Provenance, direct factory binding, F32/RGBA8
  hashing, top-down probes, fresh-surface repeatability, all wrap modes,
  below/equal/above-half mix paths, displacement min outcomes, and mode-one
  derivative execution are otherwise sound.
- A derivative-kernel mutant that changed `deriv_y[7] = -1` to the X-kernel
  position `deriv_y[5] = -1` changed every mode-one F32 oracle hash, while the
  mode-zero hash stayed identical. The fixture therefore distinguishes the two
  caller kernels as required.

One oracle limitation should be stated explicitly: because the union of the
exact derivative kernels has zero coefficients at offsets 0, 1, 2, 3, 6, and
8, no output fixture can make those authored offset values observationally
relevant. In-memory mutations confirmed only offsets 4, 5, and 7 affect these
outputs. Exact initialization of all nine entries must therefore remain a
structural both-boundary proof obligation; the oracle label “all-nine reads”
means execution, not output sensitivity.

## Frozen artifact hashes

- Risk audit:
  `cba1e6b5c9e8f5d95dda761b07c46798e9bdb9ee92a231cdff504e804f8b880e`
- Brief:
  `d12484b0ad48468fb99bbf7abaf668c741d1fa51f440d10444588f26a3ab1235`
- Oracle report:
  `479043c94b3ee25bc338d3f1156bc58863e2e60f032b52934fb32595d6a96767`
- Oracle generator:
  `c682d7e161ecc542a2db9057316efd9201a5a31cd30ad469ab55c62e39f1e23d`
- Oracle JSON:
  `b11606e86730238f6f609eabc739482603441d9dca996afd2334734929a3effa`

