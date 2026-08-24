# Task 19 frozen implementation brief

Status: corrected frozen design after pre-implementation P1/P2 review; implementation is gated on Task 17 and Task 18 acceptance plus independent re-review.

## Exact scope and count

Add one source-locked capability, `fixed-array-in-parameter-v1`, for exactly `classicNoisedeck/refract:refract`. The caller tables, helper array parameter, helper offsets table, resolved calls, and no-alias/no-escape facts are one indivisible proof profile.

Conditional on the accepted Task 18 baseline, counts move from 112 typed / 114 public / 98 publicly unported to 113 typed / 115 public / 97 publicly unported.

## Identity, provenance, and bindings

- Raw/normalized source SHA-256: `d9675b5de9c329aa619f4ef68129611faac8cbe515b6e80aa8528c593a49cfa2` / `bff1818ad5db7e637a01d6f10476cebba8ac04d6ffdf467d02508fa23671757e`.
- Immutable runtime define tuple: exactly empty.
- Canonical factory text SHA-256: `b404a801dea1ba438da7bad20d7cae059d0aa7f25c76610221ca07546fdfe2f6`.
- Bindings in source order: `inputTex:sampler2D@1/S1`, `resolution:vec2@2`, `tileOffset:vec2@3`, `fullResolution:vec2@4`, `time:float@5`, `mode:int@6`, `amount:float@7`, `direction:float@8`, `blendMode:int@9`, `mixAmt:float@10`, `wrap:int@11`.

Validator and emitter independently hash retained raw/normalized source, require empty defines, and reconstruct a hard-coded whole-program/interface and function-tree profile. Caller-provided digests and proof fingerprints are extra drift gates, never authority.

Before array proofing, apply one Refract-specific, source/key/signature/control-locked compatibility transform for the four vector-equality ternaries in `blend(vec4 color1, vec4 color2)`: blend modes 2, 3, 7 compare `color2` to `vec4(0.0/1.0)` and mode 15 compares `color1` to `vec4(1.0)`. Canonical JavaScript constructs a typed-array comparison object, which is always truthy; its selected true arm evaluates a bare color operand but performs no `.reduce(..., middle)` write, so the zero-filled `middle` remains unchanged. The transform must prove the exact assignment target, enclosing blendMode arms, operands/constants, true symbol, false expression/builtins, signature, and ancestry, then lower the four assignments to the canonical no-op. Zero/missing/duplicate/near-match shapes reject. Both validator and emitter authenticate the exact post-transform typed tree and reject untransformed, partial, or altered variants; generic vector equality or ternary semantics are not changed.

## Exact ownership and proof

Prove all facts together:

1. `derivX` has one fresh local `float[9] deriv_x`, zero-initialized natively and fully written once at literal indices 0..8 with exact Number values `{0,0,0,0,1,-1,0,0,0}` before exactly one direct argument-two call to the resolved `convolve` signature.
2. `derivY` analogously owns `float[9] deriv_y` with `{0,0,0,0,1,0,0,-1,0}` and exactly one direct argument-two call.
3. Neither caller array is read, copied, aliased, returned, escaped, passed elsewhere, or used after its call. There is no control edge that bypasses or reorders complete initialization. The two caller tables are never simultaneously live.
4. `convolve` has exact direction-`in` parameter `float kernel[9]`. It is read-only and nonescaping: only two direct `kernel[i]` rvalues per loop visit, no write/update/whole-value use/copy/return/store/further pass.
5. `convolve` owns one local `vec2[9] offset`, zero-initialized natively and fully written once at literal indices 0..8 with the exact authored `steps`-based vec2 expressions before the read loop.
6. The sole loop is exact `i=0; i<9; i++`, nine trips, depth one, lexical product nine, entrypoint charge 18. Each visit reads `offset[i]` once and `kernel[i]` twice with the exact source-specific texture/convolution/control tree and no array write.
7. `main` reaches both derivative helpers only in the exact `mode == 1` path, calls `derivX` then `derivY` with `divide=false`, and the mode-zero path remains array-free.
8. A recursive whole-program census accounts for every array type, declaration, parameter, argument, reference, store, read, index, call, and control ancestor. Any unregistered array/index/function-boundary use rejects.
9. Forged IR retaining authentic source/provenance/spans and with retained, cleared, or attacker-updated proof metadata must reject when any whole-program interface, resource, function, signature/direction, declaration, value, store, call, use, loop, index, operator, or order changes.
10. The exact four Refract compatibility sites are already transformed to the canonical no-op before the whole-program fingerprint and array proof are reconstructed. No other conditional or blend arm is transformed.

## Exact C++ ABI and lowering

Only this proof may emit explicit aliases equivalent to:

```cpp
using Kernel9 = std::array<double, 9>;
using Offsets9 = std::array<glsl::Vec2, 9>;
```

Emit `Kernel9 deriv_x{};`, `Kernel9 deriv_y{};`, and `Offsets9 offset{};`. Emit `convolve(..., const Kernel9& kernel, ...) noexcept` only for the exact proved direction-`in`, read-only, synchronous, nonescaping parameter. Passing by value, pointer/span, non-const reference, `out`/`inout`, generic array signatures, templates, and array return/copy are forbidden.

Use direct `operator[]` only at registered literal stores and registered induction reads. No `.at()`, exception path, heap allocation, runtime string/map/variant work, callbacks, virtual dispatch, runtime dependency, or resource ABI change.

Canonical caller scalar arrays are JavaScript Number arrays and therefore require `double` elements; the offset array retains F32 `glsl::Vec2` lanes. Raw simultaneous mode-one table payload is 144 bytes with const-reference ABI; by-value would be 216 and must not appear. Report compiler Debug/Release `.su` frames separately.

## Explicit exclusions

No generic fixed arrays, array parameters, aliasing, pointer/span ownership, `out`/`inout`, array return, multidimensional/nested arrays, struct arrays, other extents/elements, other keys, or dynamic table initialization. Task 17/18 and Sacred Geometry remain separate capabilities.

## Frozen external oracle

- Risk audit SHA-256: `cba1e6b5c9e8f5d95dda761b07c46798e9bdb9ee92a231cdff504e804f8b880e`.
- Generator SHA-256: `a9ff40af61e15c6a73c34a8b844ca2f41da5be1d2ae85e957d2805a8da0d7a30`.
- JSON SHA-256: `169cb5607777051de3962fdbedd32d7dab4ac2095d6b356041c48bccc3c41c88`.
- Report SHA-256: `ad053999676b49e0c75907bf66c2ec12678d99934571bfde7d1ebdcd1a113b1d`.

The direct canonical generator must pass `--check`. Four cases cover both caller derivative tables/helper calls, all wrap modes, below/exact/above-half mix branches, difference/overlay/soft-light blends, nondefault exact-F32 amount/direction/mix, displacement min outcomes, and an array-free mode-zero control:

- mode1 mirror/difference/under-half: F32 `d173f4368e000081b9b3921caccfd02790284c025ad5bd69d605f7310a23e2e2`, RGBA8 `9f345b48aafb6d69ec9d7757a161f86a103e92a7a2efdadd5eba5d3b8b7ad8c3`.
- mode1 repeat/overlay/half: F32 `6e02e60356ea964074be3b941e5ef976eeb5dfd4ee12041b8ab5cae484f2dea2`, RGBA8 `e71609cfd1cfba0c3977abceb360939d22638858df33e02b551783f87d0c0fc1`.
- mode1 clamp/softlight/over-half: F32 `3d38aee57222eb8460953f2a1e86418992f60c220b668b357d63f260346db56b`, RGBA8 `25152ac17ca38d55d15e1c7f02c5cea715f659e9f4d2bc04cffbd58b10d4aa86`.
- mode0 mirror control: F32 `3d791dbae4d93b61ab31f06b88105678c751ea3d369be9705661ed3a29879a0e`, RGBA8 `24841a3ec260bb15d549f066207c52a2e82be2fa22743d81feb1995201f28af9`.

Four additional mode-one direct canonical cases cover blendMode 2, 3, 7, and 15. Each freezes F32 `165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24` and RGBA8 `13a15bd48e6f739c5ec9e3f08affe0fe2c115418341a3b2e1742d8d3868e03e0`: zero RGB with sampled alpha, proving the canonical no-op. The oracle report also records a scalar-boolean sensitivity mutant with a distinct hash for every mode; native tests must match canonical and must not emit scalar `Vec ==` ternaries at these sites.

Native tests consume exact recorded F32 uniform bits, full F32/RGBA8 hashes, lane probes, orientation, and repeat identity. Const-reference and copy are observationally equivalent only under the locked read-only/no-escape source; native code shape must assert const reference and absence of copies.

## Acceptance evidence

- Positive semantic proof/ABI records and whole-program fingerprint locks.
- Both-boundary negative matrix for every identity/ownership/call/parameter/index/control/provenance fact, including attacker-updated proof and all exclusions.
- Exact binding failures and catalog/count tests.
- All eight native frozen oracle cases in strict Debug/Release, including blend modes 2, 3, 7, and 15; sanitizers if supported.
- Full Python suite, every drift gate, Tasks 15–19 oracle checks, direct native suite and CTest.
- Exact code-shape inspection: const ref, zero-init, direct indices, no by-value array copy, no allocation/throwing constructs.
- Debug/Release `.su` records for pixel, `derivX`, `derivY`, `convolve`, and optimizer-created/inlined clones, including static/dynamic classification. Report the maximum non-inlined mode-one call-chain sum; if Release inlines, report the containing frame plus code/disassembly evidence. Keep this full dynamic path distinct from the 144-byte raw live payload.
- Counts 113 typed / 115 public / 97 unported.

No Git command, branch, worktree, commit, push, or pull request is authorized.
