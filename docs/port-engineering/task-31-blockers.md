# Task 31 (Caustic): two blockers found during implementation

Date: 2026-08-12
Author: integration owner

Task 31 was implemented up to slice registration and then **deliberately backed
out** because implementation surfaced two problems the design phase missed. The
tree is green at the accepted Task 30 state; generated outputs are byte-identical
(`typed_slice.cpp` `5765f863…`, `typed_manifest.json` `3a6b5289…`,
`catalog.hpp` `16ebd7b1…`), native 148/148, all generator gates pass.

## What IS done and verified (retained, currently inert)

- `tools/glslcpp/frontend/caustic_word_hash_profile.py` — profile module,
  frozen tuple SHA `f97e506b0bd1a5b009e56809e33cfb1015e541a658dd4eff72388419f6244c80`.
  Authenticates the live program, re-authenticates an independently
  reconstructed tree with distinct objects, fails closed on wrong/absent
  profile, wrong source hash, and foreign programs. Consumed-object
  cardinality is **9** (host, ingress, three word XORs, two unique parents —
  the three XORs share one `construct` — and two unique `decl` statements).
- Validator wiring in `generate_typed_slice.py`: identity-scoped admission of
  the ingress and the three scalar XORs, mutual exclusion against all eight
  prior profiles, traversal-completeness check, and `floatBitsToUint` excluded
  from `used.add` so the vocabulary stays at 44 (verified).
- Emitter wiring in `emit_typed_cpp.py`: independent re-authentication,
  identity-scoped emission, completeness check.
- Both wirings are **inert** while no program in `typed_slice.json` carries the
  profile, which is why the tree is green.

Closure census correction: the design brief said "3 scalar XOR". There are in
fact **four** `^` sites in function 94 — three scalar `uint ^ uint`
(195:10, 196:10, 197:10) plus one **`uvec3 ^ uvec3` at 200:19** which is
already admitted by the pre-existing `uint-vector-bitwise` capability and is
correctly excluded from the closure. The 4-node total is right; the reasoning
in the brief was not.

## BLOCKER 1 — emitter has no reserved-identifier guard (CRITICAL)

Caustic's GLSL declares a local named `state`, which collides with the
emitter's reserved kernel-state identifier. The generated C++ does not compile:

```text
src/typed_generated/typed_slice.cpp:241:32: error: redefinition of 'state' with
  a different type: 'glsl::UVec3' vs 'const State &'
src/typed_generated/typed_slice.cpp:242:44: error: no matching function for
  call to 'pcg'
```

Emitted line 241-242:

```cpp
[[maybe_unused]] glsl::UVec3 state = glsl::bitwise_xor(...);
[[maybe_unused]] glsl::UVec3 prngState = pcg(state, context, state);
```

The local shadows the `const State&`, so the helper call passes the wrong
argument type.

This is a **pre-existing emitter defect**, not a Caustic-specific one. Local
names are stored raw with no collision check — see
`emit_typed_cpp.py` where `self.locals[...]` is assigned (four sites,
around lines 780, 978, 1503, 1537). Caustic is simply the first corpus program
to declare a local named `state`.

**Required fix (its own TDD cycle, ideally its own task):** mangle GLSL local
and parameter names that collide with emitter-reserved identifiers — at
minimum `state`, `context`, `output`, `kernel_base`. Before implementing,
verify no currently-typed program declares such a local, so the change is
byte-neutral for all 130 existing programs; assert that byte-neutrality as a
test. Do **not** rename the emitter's own reserved identifiers — that would
change every generated block.

## BLOCKER 2 — the closure is DEAD CODE at the authorized define map (CRITICAL)

The design brief asserted Caustic's XOR closure is "live, reachable, rendered
code, unlike Perlin's dead-code XORs". The oracle owner disproved this two
independent ways:

1. **Static.** At the authorized define map `{"NOISE_TYPE": 10}`, `value()`'s
   body contains exactly two calls, both to `simplexValue`. `constant`,
   `constantOffset`, and `randomFromLatticeWithOffset` are all absent from the
   call graph reachable from `main()`.
2. **Dynamic.** Rendering the real hash-pinned `canonicalFactory1` with all
   four structural mutations applied produces **bit-identical** F32 output to
   baseline across every eligible case.

Worse, even where the closure IS reachable (`NOISE_TYPE` ∈ {0,1,3,4,5,6}),
every legitimate uniform-driven path threads `s` from
`float(seed) + <integer offset>`, so `seedFrac` is always exactly `0.0`.
Since 0 is the identity for both XOR and the mutated operators,
`floatBitsToUint`↔`uint()` and `^`↔`+`/`|` mutations cannot be discriminated by
any full-render path. Only an AND-style mutation discriminates, and only where
reachable.

**Consequence:** full-render pixel parity cannot validate this closure at all.
Task 30's Extrude had genuine full-surface bit-exact parity; Caustic cannot.

The oracle owner's mitigation — direct invocation of the byte-for-byte
extracted public factory function with non-integer `s` — does discriminate
(7/8, 7/8, 7/8, 8/8 across the four mutations) and is a legitimate closure-parity
surface. But it is a weaker guarantee than Tasks 29 and 30 delivered, and that
difference must be stated plainly in any Task 31 report rather than presented
as equivalent parity.

Oracle artifacts (built, `--check` green, deterministic across two runs):
`future-precompute/task31/caustic_oracle_generator.mjs`,
`caustic-oracles.json` (`0cdc304448d66de5ae0dc14b8e27230150e4d84bb9d06ed8330c5d49774fed45`),
`caustic-oracle-report.md`.

## Recommendation for the next agent

1. **Fix Blocker 1 first, as its own task.** The reserved-identifier guard is a
   genuine latent defect that will block other programs too, and it is
   independently valuable and testable.
2. **Then reconsider Task 31's target.** Given Blocker 2, Caustic buys a
   capability whose semantics cannot be validated by rendering at its authorized
   defines. The precompute's runner-up, `synth/curl:curl`, also resolves in two
   gates (`tanh`, then `mod(vec3,float)`/`mod(vec4,float)`) and does not appear
   to have a reachability problem — re-verify that before committing. It may be
   the better next slice.
3. If Caustic is still chosen, the report must state explicitly that parity
   rests on direct closure probes rather than full-render pixel equality, and
   must not claim the latter.
