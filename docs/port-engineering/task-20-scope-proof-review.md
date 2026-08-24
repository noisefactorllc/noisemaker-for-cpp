# Task 20 independent scope/proof review

## Decision

**APPROVED.** No P0, P1, P2, or P3 finding remains in the frozen Task 20 brief or oracle design.

This was a read-only pre-implementation review. I used no Git command and changed no repository file. This requested `/tmp` review is the only written artifact. Approval means the contract is sound and implementation-ready; it does not claim that Task 20 sanitizer, stack, native-parity, or tamper evidence already exists.

Frozen brief SHA-256:
`65dcd5a522234a8c024edaafe7b942e678c5c0f2c643a260543547380c545ab5`

## Frozen inputs and provenance

The reviewed artifacts match the identities embedded in the brief:

- risk audit: `6798f1459cd6ae512a8bd70ac730684d2b2b2b5389e2d367099d6fad07b85149`
- oracle generator: `4e9bead18c312cbf0aa5b3239bb575cfaec3ddd40cb246f3d47e8f3ccd49f75e`
- oracle JSON: `1f71fc6fb2f91f0c3b660decda30d533ecca20070bb318cc9757242be3499d03`
- oracle report: `02db6d234953dd23b2bea50b02e1c5d25449aefbdd7117e0959be003395b3f30`

I independently confirmed the pinned source is 9,710 bytes with raw SHA-256 `24e5bc642f5a1f368d4514fd33590ef7d479f56c1c862144576f7bde321f53de`; semantic normalization is 8,395 bytes with SHA-256 `6b3c4e8492a69969f3d6f78689cfd19de846656fd0c6d5c8dfd5a758427c61d3`; and the pinned canonical runtime file has SHA-256 `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`. The direct generator check passes with `ok task-20-oracles.json`, which also reauthenticates `canonicalFactory273` and its frozen function-text hash.

## Star Number-division transform

The compatibility blocker is real and the selected remedy is narrowly correct. The analyzed Sacred program contains exactly one binary `/` whose operands are both typed `int`: normalized `starPolygonMask` line 260, columns 29-39. There is no second integral-division site requiring a compatibility decision, and the program contains no vector equality or vector conditional predicate analogous to the Refract hazard.

I independently reconstructed the specified rewrite in memory. It changed exactly these five typed expression nodes:

1. `/` at `260:29-39`, `int -> float`;
2. its `*` parent at `260:29-44`, `int -> float`;
3. the root `-` at `260:18-44`, `int -> float`;
4. declaration `j@107` at `260:13-44`, including its attached symbol, `int -> float`; and
5. the sole later `j@107` read at `262:30-31`, including its attached symbol, `int -> float`.

That independent reconstruction reproduced both frozen post locks exactly:

- `SHA256(repr(program.functions)) = fdaf48f945303bfe83c56ee0e2e75ae62d418904c02fc2bc6621fc0da907f7b2`
- post whole-program fingerprint = `de499dea91a59d8fc5ec4591be30a9b4350bb6a9e0317259aa97e8d3e3586ee0`

The untouched analyzed tree likewise reproduces the stated pre-transform function hash `261327d6c1700f71cef056020358ba1ea4dd56c1e8d1017f545df805a4f9b1d8` and whole-program hash `2dda5c4f3931965da85ac54fca2b6e4748cb2cb1ca61b03316f750c2f6754388`.

The rewrite composes correctly with the current emitter. A typed `float` local lowers to C++ `double`; float-typed binary nodes cast both operands to `double`; the original integer additions remain exact; and the authored `float(j)` constructor remains the F32 narrowing boundary. With `-ffp-contract=off`, this produces separate binary64 divide, multiply, and subtract operations without a native integer division, `%`, `integer_mod`, integral cast, or contracted multiply-subtract. The pre/post hard locks and exact structural checks make a global integer rule, geometry shortcut, hard-coded NaN, partial transform, second site, or attacker-selected rewrite unnecessary and inadmissible.

For every metadata-supported `starPoints` value 5 through 12, both JavaScript Number arithmetic and a direct AppleClang C++ double check produce positive zero at `2 - (2/n)*n`. The first Star segment is therefore degenerate. An independent canonical rerender found exactly one RGB word, `0x7fc00000`, and one alpha word, `0x3f800000`, across all 851 pixels for each of the eight values. The frozen finite intended-integer-remainder controls differ in all 2,553 RGB lanes; the `starPoints=7` F32/RGBA8 control hashes agree with the report.

## Affine centers proof

The current typed tree confirms `fruitMask` signature 40 has exactly 12 body statements, parameters `p:vec2@31` and `drawLines:bool@32`, and one local array declaration `centers:vec2[13]@73` at body index 2. It contains exactly seven array index expressions and no other array-typed object:

- center store `centers[0]` at `97:5`;
- inner affine store `centers[1+k@74]` at `100:9`;
- outer affine store `centers[7+k@76]` at `104:9`;
- circle reads using `i@81` at `114:39` and `120:30`;
- line endpoint reads using `i@88` and `j@89` at `140:46` and `140:58`.

The two initializer loops each prove start 0, strict bound 6, post-increment, and six trips. Their exact index sets are `{1..6}` and `{7..12}`; together with `{0}` they are pairwise disjoint and cover all 13 elements exactly once before any read. The exact RHS/operator/source lock correctly prevents an interval-only proof from accepting swapped rings, a phase or radius change, `k+1`, missing Vec2 materialization, reordered regions, overlap, gap, or conditional initialization.

`std::array<glsl::Vec2, 13> centers{}` is the correct canonical storage boundary. The current `Vec<2,float>` has an eight-byte two-float payload whose member array is value-initialized; braces therefore produce 26 positive F32 zero lanes. Assignment from `FloatExpr<2>` narrows both lanes through `noisemaker::f32`. The required 8-byte and 104-byte static assertions fail closed on an unsupported ABI, while the source-locked scalar `angle` path retains Number precision between the existing F32 literal and builtin/storage boundaries.

## Reads, calls, and work accounting

The dynamic arithmetic is correct:

- the circle loop performs 13 visits and two center reads per visit: 26 reads;
- the nested line grid visits `13 x 13 = 169` pairs;
- `j <= i` rejects `1+2+...+13 = 91` diagonal/lower-triangle pairs;
- 78 pairs remain, each reading `centers[i]` and `centers[j]`: 156 reads;
- Metatron therefore performs 182 center reads and 78 line evaluations;
- Fruit performs 26 reads and no line evaluation;
- the Metatron charge is `6+6+13+13+169 = 207`.

Independent semantic analysis reproduces the whole-program loop proof exactly: nine loops, zero unproved loops, effective depth two, lexical product 169, entrypoint charge 207, and an acyclic call graph. The profile adds no loop or control capability.

The required recursive census, complete-initialization dominance, no-post-write rule, exact direct call routing, and no-copy/alias/parameter/return/address/capture/escape conditions are sufficient. Per-site validator and emitter authorization is limited to the one declaration and seven index expressions; neither `vec2[13]` nor arbitrary affine indexing enters the ambient type/operator vocabulary.

## Proof and tamper boundaries

The brief correctly requires the compatibility rewrite before the affine proof and requires validator and emitter to repeat the security-sensitive work independently. Both boundaries must reattach counted-loop and discarded-counter proofs, clear all fixed-array proof fields, rebuild earlier layers in order, authenticate the transformed Sacred post profile, recompute the entire immutable Task 20 proof, and compare the whole proof object.

Raw and normalized source locks, empty defines, fixed key/function/symbol/span/operator/child identities, binding/resource/interface locks, the post-transform function hash, and the hard-coded whole-program hash provide authority. Caller-supplied proof hashes remain only drift alarms. The retained/cleared/attacker-replaced matrix at both boundaries adequately covers stale proof, cleared proof, and an attacker who recomputes exposed hash fields after structural, top-level, source, binding, transform, array, control, or use-site drift.

The negative matrix is appropriately broader than rendered mutation coverage. It requires exact typed-node replacement, rejects generic arrays and affine indices, and covers transform registration, declaration/storage, write topology, RHS precision, read/control ancestry, ownership/escape, unrelated capabilities, hot-loop code shape, and adjacent keys. The exact key/source locks plus final allowlist/count/catalog assertions keep CRT, Degauss, neighboring synth keys, other extents, and any future Sacred variant excluded.

## Bindings, catalog, and counts

The source and typed tree confirm the ordered 17-uniform signature with stable symbol IDs 1 through 17, `fragColor:vec4@18`, no sampler, no resource input, and logical `color -> outputTex` route. Metadata confirms the stated defaults and the existing UI/source distinction that `speed` is an integer-valued control bound to a shader `float`.

The current accepted post-Task-19 baseline is 113 typed factories and a sorted, unique 115-entry public catalog; Sacred Geometry is not already present. The projected Task 20 movement is therefore exactly 114 typed, 116 public, and `212-116 = 96` publicly unported, with the corpus fixed at 212. The brief requires all three count assertions, exact catalog equality, bindings with missing/wrong-type rejection, and exclusion checks.

## Oracle and mutation adequacy

The ten direct-canonical cases cover every defined geometry choice and every animation code, with four array-sensitive paths: Fruit off, Metatron off, Fruit Ripple, and Metatron Unfold. The 37x23 non-square fixture, nonzero tile offset, distinct full resolution, exact F32 uniforms, nine probes, top-down orientation, full F32 and RGBA8 hashes, opaque-alpha/nonfinite profiles, and fresh-surface repeat identity are adequate.

All seven counted factory mutations were independently present in the JSON with the reported detecting-pair F32 lane differences `567/863`, `2553/84`, `2553/84`, `955/117`, `330/210`, `1431/1755`, and `82/110`. Every mutation preserves all six non-array controls byte-for-byte. The inner-ring permutation changes 82/110 F32 lanes while changing zero RGBA8 bytes, directly justifying full-F32 native comparison and structural rejection of symmetry-equivalent reorderings. The Star 5-through-12 matrix and finite remainder controls adequately expose the compatibility transform without pretending rendered pixels prove structural authorization.

## Required implementation evidence

The acceptance gate is proportionate and complete. Task 20 cannot be declared implemented until fresh Debug, Release, ASan, and UBSan executions match all ten F32 and RGBA8 oracle surfaces, all Star qNaN words, probes, orientation, and repeat identity; corpus/generator/semantic/Python/native/prior-oracle checks pass; and unrelated generated bodies remain unchanged.

The stack gate correctly separates the 104-byte table payload from compiler-reported total frames, requires static/dynamic classification for `fruitMask`, `starPolygonMask`, `lineSegmentSDF`, `main`, the pixel lambda, and optimizer clones, and requires maximum non-inlined call-chain accounting or Release inlining/disassembly evidence. The sanitizer contract preserves ASan/UBSan while excluding only the intentionally canonical floating divide-by-zero fatal check. The hot-loop inspection forbids allocation/deallocation, virtual or indirect dispatch, callbacks, `std::function`, associative/string/variant lookup, exceptions, recursion, and dynamic stack growth; catalog lookup remains outside the pixel loop.

These are future implementation acceptance requirements, not evidence waived by this design approval.
