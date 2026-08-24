# Task 23 implementation-design review

## Verdict

**APPROVED FOR IMPLEMENTATION**

No residual P0, P1, P2, or P3 finding remains in the final amended Task 23
implementation design.

This was an independent read-only review against the approved Task 23 brief,
the frozen oracle package, and the accepted Task 22 repository architecture.
No repository file or Git state was changed.

## Authenticated design and inputs

| Artifact | SHA-256 |
| --- | --- |
| final Task 23 implementation design | `dab4ce6d8b6859fea782e2dd447921d07dc56a77edc9f972fd8b90ca9c5a529d` |
| final Task 23 brief | `8aab4f5a9274879f7061c51595bba30f29f02d9606c4f76cf0e1e7312227915f` |
| final Task 23 brief review | `23e68c35e77af2a821ba211b0b29c8ec856db194ef12cd9ad24647af7fc5bad2` |
| Task 23 frontier audit | `cc49663ed312f95fc3d83cde245a95dc8719a1a90059d750ae9f7b9611061666` |
| Task 23 oracle generator | `f91ece9510c092e9c0221fc9b326522840c0b10eb3433b858eea3d786f7f57a2` |
| Task 23 oracle JSON | `a832ea550911634dbe2e98e62b51837d8fa57612243416a88f70af69f626c52d` |
| Task 23 oracle report | `8a060f2b74fcc4c7d8ed74ca315b8239a28be0475a57067f3f223667bd009303` |

The oracle generator's `--check` passed on the reviewed bytes. All twelve
Task 23-owned repository paths still match the accepted Task 22 preflight
hashes recorded in the design, including the corrected generated-manifest
SHA-256 `8b5ba832204e6f346563e0ff721e4c7bd7cfcd5194df6f428347188eff35f680`.

## Review conclusions

### Proof reconstruction and authorization

The design now defines one fail-closed state transition at all three trust
boundaries: clear only submitted counted-loop proofs, run ordinary unseeded
proof attachment to reconstruct the canonical pre-Task23 state, authenticate
its exact frozen functions/summary/whole/interface identities, seed the
existing proof algorithm from the authenticated source-global declaration,
and require exact submitted-versus-reconstructed post-tree equality plus
frozen post functions/whole/summary identities. The fully cleared tree is only
normalization input, never proof authority or an accepted final state; forged
proofs and caller-updated hashes cannot bypass the reconstructed-post
comparison.

Strokes locks this distinction with exact evidence: its fully cleared function
tuple is
`dc58c8e53799e41f8ab4c9263af336b37540ee58b1418cac6d3734e878bc7bc6`
with 0 proved / 3 unproved loops and is non-authoritative. Ordinary unseeded
attachment produces frozen pre functions
`5e5e0bb5091f6d4221e5396f3ed5dc73854543281ef519fbaddb0fdcd5c3fbc9`
and pre whole
`b7b6c65e3275843bd141f9b0c1fcf40daad671dcbeebef2db6a4684ec750790c`
with 2 proved / 1 unproved. Authenticated seeded attachment produces frozen
post functions
`0ee608091d09aece9a1eba08224b1980be15e2c1eb288b206fe47f95c2cfb344`
and post whole
`5ac93407e6a52ef895a887b3817c781d58ac9b974afe30415f31c6b4a9e8cbbf`
with 3 proved / 0 unproved and entry charge 72.

Every current production proof-reconstruction site is covered. Semantic
analysis seeds its initial attachment, generator validation routes its generic
recomputation through the authenticated helper, and the emitter caches one
authenticated seed and routes all six current predecessor-proof call sites
through it. Prior programs receive the empty seed and remain byte-identical.
The helper's final signature consistently returns both reconstructed functions
and `CountedLoopProgramProof`.

The capability model also matches the current schema: the capability
vocabulary is slice-global and copied into every manifest entry, while the
explicit carrier/profile is the sole per-program authorization. The exact six
keys require the carrier; foreign keys tolerate the shared vocabulary item but
reject a foreign carrier. No per-program schema field or key-only inference is
introduced.

### Six-key scope, generated output, and ABI

The profile remains closed over Bloom, Directional Blur, Spin Blur, Strokes,
Vaseline, and Wind, with exact sources, defines, declaration/read/loop spans,
typed pre/post hashes, interfaces, resources, proof metrics, slice positions,
and projected 122 typed / 124 public / 88 unported / 212 corpus counts.
`filter/reindex:nmReindexStats` and the remaining frontier stay excluded.

Production validation owns the frozen corpus and typed identities only. The
external frozen oracle package owns JavaScript runtime/factory hashes, public
function-object identity, and adapter absence, so production does not acquire
an invalid dependency on `noisemaker-for-cpu` or carry unused external hashes.

`MODE=0` and `METHOD=1` are correctly treated as compile-time define profiles,
not runtime `Bindings` values. The design requires exact define metadata and
external-oracle execution, generated-branch evidence, and absence of both
names from the native binding ABI.

Generated isolation is mechanically specified for all 116 prior blocks, the
six insertions, namespace ordinal shifts, manifest/catalog identity, local-only
integer materialization, and allocation/dispatch/storage exclusions.

### Native and negative evidence

The semantic, generator, and emitter negative matrices cover the required
four authorization states plus source, declaration, initializer, symbol,
read/write, proof, call-graph, resource, capability-vocabulary, carrier, and
caller-hash forgeries.

The 19 canonical native fixtures use a hermetic embedded C++ table. A Python
test mechanically parses it and compares every relevant field against the
frozen JSON, eliminating an unreviewed fixture-blessing path without adding a
JSON/CMake/runtime dependency.

The twelve source-factory mutations have an executable in-scope native path:
test-local structural mutations are first rejected by production admission,
then rendered into temporary unique namespaces, compiled once with the local
runtime, and compared field-for-field to the frozen mutated F32/RGBA8 hashes
and changed-lane/byte metrics. The test renderer explicitly rebuilds all
declaration/function-derived caches after tree substitution, and asserts each
intended mutation is present exactly once with the canonical structural form
absent. Temporary mutation code cannot enter generated outputs or installed
artifacts.

Wind's tiny-positive case is no longer accepted from output identity alone.
The design requires generated ordering and exact F32 binding arithmetic proving
that the positive-strength normal path is entered, reach is `0.64`, the first
distance is `1`, and the break dominates the candidate fetch, yielding exactly
the initial fetch. The corrected Strokes call graph, conservative stack-chain
rule, fetch bounds, Debug/Release/sanitizer stack evidence, and disassembly
fallback are retained.

## Approval boundary

Approval applies only to the twelve owned paths and the exact test-first and
verification sequence in the design. It is implementation authorization, not
implementation acceptance. Any parser, typed-IR, runtime, sampler, Surface,
CMake, corpus, adapter, or other out-of-table change requires renewed scope
review.
