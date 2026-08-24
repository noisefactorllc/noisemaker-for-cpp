# Task 29 Focus Blur exact borrowed sampler ABI brief

## Goal and hard gate

Add exactly `mixer/focusBlur:focusBlur` under identity profile
`focus-blur-borrowed-sampler-parameters-v1`, emitting only its two exact helper
sampler parameters as `const Surface&`. Start only from accepted Task28:
212/128/130/82, typed/public hashes `30f0333c...` / `102f5436...`, and accepted
review/fix/rereview hashes `c740a5b9...` / `6b47ee5f...` / `76e976a0...`.

Projected state is 129 typed / 131 public / 81 unported, Focus ordinal 110,
typed/public hashes `c2561c59...` / `2325f8d0...`.

## Frozen identity and ABI

The source, normalized tree, function tuple, whole program, interface, public
factory, bindings, helper body, parameter objects, four recursive parameter
uses, two complete calls, their complete expression/statement parent chains,
the exact enclosing if/predicate and then/else slots, argument IDs/order, four texture
sites, four textureSize sites, loop proof, and empty defines are frozen by
`task-29-recomputed.json`; profile tuple SHA is
`869eafed0199be24c6fcf5a13d39211c1ea0c1227f9ee12b55f5c69196e9780b`.

The exact ABI is:

```cpp
[[nodiscard]] glsl::Vec4 applyFocusBlur(
    const State&, const glsl::PixelContext&,
    const Surface& sceneTex, const Surface& depthTex,
    glsl::Vec2 uv) noexcept;
```

Both declaration and definition must match. Calls are exactly
`applyFocusBlur(state, context, *state.tex, *state.inputTex, uv)` and the
reverse. Parameters are canonical `direction=in,writable=True`; prove no
writes/escapes from recursive uses rather than changing IR flags. References
are synchronous borrows from setup-owned pointers. Stable address, lifetime,
no concurrent mutation, alias validity, and fresh-output separation are part
of the binding contract.

The selected pixel path has one helper call, 67 texture reads, and separately
67 textureSize evaluations. Neither count may be conflated or omitted.

## Fail-closed requirements

Create one exact profile module returning the exact helper, two parameter
objects, four sampler identifier objects, two call objects, their complete
parent chains, and exact candidate-owned predicate/if/branch objects and slots.
Apply is identity. Validator and emitter authenticate independently, require
the carrier for exact Focus Blur, reject it on foreign/mutated trees, and count
all authenticated objects as visited exactly once. Equal reconstructed trees
authenticate their own objects; forged old-tree returns fail completion.

Emitter admission belongs only in `function_parameter_type` for the exact
function/ordinal/parameter objects. Never widen `_TYPES` or `function_type`.
Reject by-value, mutable-reference, pointer/wrapper, nullable, copied, stored,
returned, captured, array/aggregate/local/global sampler forms; arbitrary or
second helper samplers; changed calls/branches/order/alias rules; nonempty
defines; adapters; runtime/CMake/parser/IR/corpus changes.

Exhaustively test each one-axis coordinate listed in
`task-29-adversarial-audit.md`, including every existing carrier coexistence,
caller hash/numeric/define matrix, code-shape alternatives, and independently
analyzed foreign sampler-helper programs. Each candidate must prove its named
coordinate changed and every protected coordinate remained equal before
profile/validator/emitter rejection.

## Pixel, ABI, and non-vacuity proof

Transcribe all six frozen public cases and eight direct ABI modes. Assert input
immutability, dimensions before hashes, repeat identity, finite lanes, full
F32/RGBA8 hashes, all probes, public/direct binder identity, each missing/wrong
binding, and same-Surface alias parity. Add lifetime coverage that destroys
Bindings after binding while surfaces remain alive, then runs under sanitizer.

Execute the semantic mutation table for branch/order/read/loop/alpha changes.
Every mode executes a genuine distinct handler shape. Its semantic structural
signature excludes ID, name, acceptance, and result and is pairwise unique.
The value-copy negative allocates, owns, and reads two independent Surface
copies. Authenticate every enum ID/name, switch arm, ABI/resource-order/
alias/copy/null/write witness, counter, and result; mutation of any switch or
witness token fails while JSON remains unchanged. Require declared == handled
== observed and invalid enum rejection. Cover predicate replacement/equal
reconstruction, branch swap, call move/copy/both-executed, and call-slot swap.

Final gates: real Task28 reconstruction/isolation; canonical checks; full
Python discovery; Debug/Release warnings-as-errors and CTest; ASan/UBSan;
stack usage and AArch64 disassembly for helper/pixel; exactly 67 samples plus
67 size queries; no heap/indirect/exception/dynamic stack; all Task15-29
oracles; independent implementation review with zero Critical/Important.

No Git action is authorized by this package.
