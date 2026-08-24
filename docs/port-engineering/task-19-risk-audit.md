# Task 19 implementation-risk audit: fixed array input parameter

Date: 2026-08-10  
Scope: projected post-Task-18 baseline (112 typed / 114 public), read-only
inspection of the pinned corpus, direct canonical CPU factory, and current
typed frontend/emitter. No repository file was changed and no Git command was
used.

## Recommendation

Admit at most this one source-identity-locked program and complete ABI shape:

```text
fixed-array-in-parameter-v1
  classicNoisedeck/refract:refract
```

It is one coherent key, not independently deployable helper and call
capabilities. `convolve`'s `float kernel[9]` parameter, the two caller tables
(`deriv_x` and `deriv_y`), and `convolve`'s separate `vec2 offset[9]` table
form one data-flow proof. Exposing an array parameter in a generic function
signature first would be a materially larger ABI/alias feature with no
additional tested program. Conversely, admitting only the caller tables would
not emit the callee parameter or its dynamic reads.

The projected result is 113 typed / 115 public / 97 publicly unported programs
from the 212-program manifest. That is a Task-19 projection only; it assumes
Task 18 has been accepted and does not authorize an implementation now.

## Provenance and exact binding contract

| Field | Locked value |
| --- | --- |
| Key | `classicNoisedeck/refract:refract` |
| Source | `sources/classicNoisedeck/refract/refract.glsl` |
| Raw / normalized SHA-256 | `d9675b5de9c329aa619f4ef68129611faac8cbe515b6e80aa8528c593a49cfa2` / `bff1818ad5db7e637a01d6f10476cebba8ac04d6ffdf467d02508fa23671757e` |
| Runtime defines | `{}`; source-local `PI` and `TAU` macros are part of the source digest, not runtime defines |
| Canonical factory | `canonicalFactory14`; exact `Function.prototype.toString()` SHA-256 `b404a801dea1ba438da7bad20d7cae059d0aa7f25c76610221ca07546fdfe2f6` |
| Canonical generated runtime | `src/effects/generated/canonical-kernels.js`, SHA-256 `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56` |
| Exact source binding order | `inputTex:sampler2D@1/S1, resolution:vec2@2, tileOffset:vec2@3, fullResolution:vec2@4, time:float@5, mode:int@6, amount:float@7, direction:float@8, blendMode:int@9, mixAmt:float@10, wrap:int@11` |
| Pass route | `inputTex <- inputTex`, `fragColor -> outputTex`, with pass uniform alias `mixAmt <- mix` |
| Metadata/runtime defaults | `mode=0`, `amount=50`, `direction=0`, `blendMode=10`, `mix=50`, `wrap=0`; `resolution`, tile/full resolution, and time are supplied by render bindings |

The proof must bind all of those fields, source plus canonical factory hashes,
and a freshly recomputed typed shape. Current counted-loop diagnostics are one
proved loop, acyclic call graph, `i=0; i<9; i++`, one effective/lexical depth,
lexical product 9, and entrypoint charge 18. A fresh full-function typed-IR
fingerprint is `ccde114d367313d1feb218c7f956df4059534b5c139c757a30ae156292e9cc09`.
The fingerprint is an additional drift alarm, not a substitute for structural
checks or source provenance.

## Exact array ownership and flow

The program has exactly four relevant identities:

| Function | Identity and source initialization | Allowed uses |
| --- | --- | --- |
| `derivX(vec3 color, vec2 uv, bool divide)` | local `float deriv_x[9]`, nine literal stores `{0,0,0,0,1,-1,0,0,0}` | passed once as argument two to `convolve`; never read, written, returned, or used after that call |
| `derivY(vec3 color, vec2 uv, bool divide)` | local `float deriv_y[9]`, nine literal stores `{0,0,0,0,1,0,0,-1,0}` | passed once as argument two to `convolve`; never read, written, returned, or used after that call |
| `convolve(vec2 uv, float kernel[9], bool divide)` | `in` parameter `kernel`; no initializer at callee entry | exactly `kernel[i]` in `conv += color * kernel[i]` and `kernelWeight += kernel[i]`; no write, address/return, assignment, further array call, or other reference |
| `convolve` | local `vec2 offset[9]`, no declaration initializer; nine literal-index stores using `steps` | exactly one `offset[i]` dynamic read in the proved loop; no post-init write, parameter pass, return, or escape |

Both caller tables are completely initialized before their calls, with no
condition, loop, return, break, or continue between a table declaration and
all nine stores. `convolve` similarly completes its nine `offset[0]` through
`offset[8]` stores before entering the only loop. The loop visits every `i` in
`[0,8]`, reads `offset[i]` once and `kernel[i]` twice per visit, and performs
no array write. Therefore all reads are in bounds and initialized; no rule may
weaken this to partial initialization merely because some kernel entries are
zero.

`main` reaches these tables only in `mode == 1`: it calls `derivX` and then
`derivY`, each with `divide=false`. `mode == 0` never enters either caller.
The two caller tables do not overlap live: `derivX` returns before `derivY`
is called. The helper is synchronous, has no closure/capture/global storage,
and returns only a `vec3`; its input array cannot outlive the caller frame.

## ABI and precision decision

Canonical JavaScript constructs `deriv_x` and `deriv_y` as zero-filled plain
Number arrays, writes the nine literals, and passes the array object to
`convolve` by reference. It also constructs `offset` as nine zeroed
`PooledFloat32Array` `vec2` values and stores each `vec2` through F32 vector
boundaries. This yields the only safe narrow lowering:

```cpp
using Kernel9 = std::array<double, 9>;
using Offsets9 = std::array<glsl::Vec2, 9>;

[[nodiscard]] glsl::Vec3 convolve(
    const State& state, const glsl::PixelContext& context,
    glsl::Vec2 uv, const Kernel9& kernel, bool divide) noexcept;
```

The `const Kernel9&` is permitted only under the exact no-write/no-escape
proof above. It reflects the canonical reference object without an unnecessary
72-byte copy, and is safe despite GLSL `in`'s conceptual copy-in ABI because
this exact callee neither observes identity nor mutates the parameter. Passing
`Kernel9` by value would also be observationally sound for this pinned source,
but adds a copy at each `convolve` call and should not become the default ABI.
Do not use a pointer, span, vector, heap allocation, template/general array
signature, non-const reference, or a generic conversion rule.

The two caller tables lower as `Kernel9 deriv_x{};` / `deriv_y{}`; the helper
table as `Offsets9 offset{};`. The braces preserve canonical zero-fill even
though full initialization is proved. In particular, do not lower the float
tables to `float[9]`/`std::array<float,9>`: their elements are ordinary JS
Numbers and participate in scalar Number arithmetic until vector/builtin/output
boundaries. `glsl::Vec2` remains the F32 vector container for `offset`.

Raw simultaneous table payload on the mode-1 call path is 144 bytes: 72-byte
caller `Kernel9` plus 72-byte callee `Offsets9`; the reference itself has no
array copy. A by-value parameter would raise that to 216 bytes. This excludes
ordinary local vectors, call ABI spill, and compiler red zones, so debug and
release stack measurements remain required. The mode-1 path calls `convolve`
twice serially, not recursively or concurrently.

## Required proof and emitter boundaries

Current code deliberately cannot emit this source: it rejects `float[9]` at
the callee parameter first. Even after local-array admission, `function_type`
cannot spell an array parameter, and the existing fixed-nine proof recognizes
only two main-function profiles (`sharpen` and `sobel`). Its broad
array-identity index acceptance must not be repurposed as generic array ABI
support.

`fixed-array-in-parameter-v1` should recompute and bind all of the following:

1. Exactly this key, digest pair, no runtime defines, factory/binding contract,
   functions `main`, `derivX`, `derivY`, and `convolve`, and the four stable
   array identities/type/extent/structural ancestry above. Reject stale,
   forged, absent, or source-mismatched proof.
2. Both caller arrays have a fresh `float[9]` declaration, exactly nine direct
   literal indices `0..8` in source order, the stated values, and exactly one
   argument-two call to the same resolved `convolve` signature after complete
   initialization. Reject aliases, copies, array constructors, dynamic caller
   stores, array reads before call, argument reordering, reuse, or post-call
   access.
3. The parameter has direction `in`, exact `float[9]` type, is only a direct
   `kernel[i]` rvalue in the one resolved helper, and is neither assigned,
   incremented, returned, stored, passed, copied, nor used as a whole value.
   No `out`/`inout` array parameter is in scope.
4. The helper's one `vec2[9]` local is fully literal-index initialized before
   its exact counted loop. The loop is `i=0; i<9; i++`, has the recorded
   safety proof, and has exactly one `offset[i]` read plus two `kernel[i]`
   reads per visit; no array write/escape occurs in or after it.
5. The emitter may use the explicit `Kernel9` and `Offsets9` spellings only
   for this proof profile, `const Kernel9&` only for that parameter, and direct
   proved indexing only at its registered source spans. Preserve `noexcept`,
   source ordering, no heap allocation, and `std::array` zero initialization.

Negative tests must cover changed key/hash/defines/bindings, array extent or
element type, any `out`/`inout`, parameter write or whole-array escape,
caller copy/reuse/post-call read, missing/reordered literal store, wrong call
target/argument/order, `kernel` passed onward, unproved loop/different bound,
wrong induction index, dynamic store, index outside the role/span, and forged
proof. Test that by-value and non-const-reference emission are rejected rather
than silently broadened.

## Exclusions and oracle requirements

This does **not** admit generic fixed arrays, arbitrary function array
parameters, aliasing, caller-to-callee ownership transfer, pointers/spans,
`out`/`inout`, return arrays, nested/multidimensional arrays, array values in
structs, different extents/elements, dynamic table initialization, or another
`classicNoisedeck` key. Task 17 and 18 profiles remain independent.

Freeze direct canonical-factory oracles before implementation. At minimum use
a non-square, top-down F32 texture with nonzero `tileOffset` and
`fullResolution`, an output/tile configuration that exercises the displacement
budget branch, F32 nondefault `amount` and `direction`, and `mode=1` so both
caller arrays and both `convolve` calls run. Cover all three wrap modes
(`mirror`, `repeat`, `clamp`) and at least two blend/mix paths; retain a
`mode=0` control case showing the non-array path. Record canonical source and
factory digests, exact bindings, uniform F32 words, F32/RGBA8 hashes,
top-down lane-bit probes, and fresh-surface repeat identity.

The test fixture must distinguish the two derivative kernels (their `-1`
positions differ) and use an amount whose `floor(map(amount,0,100,0,20))`
is nonzero. Native differential tests must run debug/release plus sanitizers,
measure stack use, and compare the mode-1/array path bitwise against every
frozen F32 oracle. Canonical explicit uniforms are spread without automatic
`Math.fround`; use the recorded F32 values deliberately. RGBA8 alone is
insufficient because it can hide Number-vs-F32 scalar-table drift and
clamping/rounding differences.
