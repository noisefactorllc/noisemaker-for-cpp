# Task 23 Brief and Frozen-Package Review

## Verdict

**APPROVED FOR DESIGN AND IMPLEMENTATION**

No residual P0, P1, P2, or P3 scope/proof finding remains in the final amended
brief or its frozen frontier/oracle package.

This was an independent read-only review. No Git command was used and no
repository file was modified. Approval is for the bounded Task 23 contract
only; it is not implementation acceptance.

## Authenticated inputs

| Artifact | SHA-256 |
| --- | --- |
| final Task 23 brief | `8aab4f5a9274879f7061c51595bba30f29f02d9606c4f76cf0e1e7312227915f` |
| Task 23 frontier audit | `cc49663ed312f95fc3d83cde245a95dc8719a1a90059d750ae9f7b9611061666` |
| Task 23 oracle generator | `f91ece9510c092e9c0221fc9b326522840c0b10eb3433b858eea3d786f7f57a2` |
| Task 23 frozen oracle JSON | `a832ea550911634dbe2e98e62b51837d8fa57612243416a88f70af69f626c52d` |
| Task 23 oracle report | `8a060f2b74fcc4c7d8ed74ca315b8239a28be0475a57067f3f223667bd009303` |
| accepted Task 22 report | `69bcc357de8a8e6df73b8b80ec0e8b5d3e2ca71f12edee25750e21f95c68a7d9` |
| accepted amended Task 22 brief | `f8c5a9fdd18a5ca587dee47d7d297503325b1eea374a867f5e9ad8d196c57e59` |
| accepted Task 22 implementation design | `1e347e6565ae37aecd5c2edf9db3b9fc851fe3b2591f253c9f57eaf409be63f1` |
| accepted Task 22 final independent review | `102a56ab642c1884319a827530639d0dc9943441393e03ea497274812912e5af` |

The accepted Task 22 gate is present: 116 typed, 118 public, 94 publicly
unported, 212 corpus programs, full Python discovery 122/122, and accepted CRT
oracle, transform, generated-isolation, native, sanitizer, and stack evidence.

## Accepted Task 22 preflight hashes for Task 23-owned files

| File | SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/semantic.py` | `01c772aae5732d048c11c28b93d18d00fce63f6373ecb294324773f5e8817f2b` |
| `tools/glslcpp/frontend/loop_proof.py` | `830ed013d791eb201dfbac8f1a65996b6427656a0e2c7dc953df62dd8c3cb6c8` |
| `tools/glslcpp/generate_typed_slice.py` | `b8fade4315e3bb510163c18fc51c5ddc8ab3c20af6272dcc6e9a7f78b8412562` |
| `tools/glslcpp/emit_typed_cpp.py` | `9ee63f4aa7f2b15b52d6dc5b83fc9bc7ca6e2dcaa881787a60aa5bc784647bba` |
| `tools/glslcpp/typed_slice.json` | `c6683f5eaf782c53194f90f0ec2c3dd71436fc09b4c84ac12a83b79cfe1e2dd0` |
| `tests/test_semantic.py` | `53192b002dfb17490f679341411c4862e4e08930116d1dfb66b61543933e4b27` |
| `tests/test_typed_generator.py` | `c4c3be1d130611ebe790e7519dfd8067331d6494db99048d43bf0ed6c8f1893d` |
| `tests/test_generated_kernels.cpp` | `16dc18f60f28a94cb43b302e3df5d7bab3acabbcb58c98d447fcf0ce7bff8180` |
| `tests/test_typed_slice.cpp` | `f85ad92eecbd386d549eb85402a17e93a5a17c08c122c37e474fe9ae6d91dd3e` |
| `src/typed_generated/typed_slice.cpp` | `a3f8135d41e9f2abc864fada60532309b56c43f6e6eb138d548a23b57f944c4f` |
| `src/typed_generated/typed_manifest.json` | `8b5ba832204e6f346563e0ff721e4c7bd7cfcd5194df6f428347188eff35f680` |
| `include/noisemaker/generated/catalog.hpp` | `a96420439fbd3f4289335a08d0a6506687a6222e52cb052475bd01442cec0408` |

The owned-file list is sufficient. The new proof uses existing typed-IR proof
fields and bound-kind strings, so no typed-IR, parser, runtime, sampler,
Surface, corpus, or CMake change is justified.

## Independent six-key recomputation

All six exact source paths, define maps, raw byte counts/hashes, normalized
hashes, canonical function names/text hashes, typed pre/post function hashes,
pre/post whole-program hashes, and pre/post interface hashes reproduced. The
pinned canonical runtime hash also reproduced through the frozen generator.

Runtime catalog inspection independently proved for every selected key that
the public factory object is the canonical factory object and that no adapter
entry exists:

| Key | Canonical factory | Factory text SHA-256 |
| --- | --- | --- |
| `filter/bloom:ntapGather` | `canonicalFactory23` | `a737ac48f663f041f763677680ab5d5282482ab6d10143939de055b980c4207c` |
| `filter/directionalBlur:directionalBlur` | `canonicalFactory47` | `a3803238488c9bd2fe786b931a0a2ba81a057d02f984017d8e10073c68873344` |
| `filter/spinBlur:spinBlur` | `canonicalFactory145` | `c6b97d30339acd21fc01d2d2cd31073c62d2ba82dbb80e95d9457b0f59737547` |
| `filter/strokes:stkSmear` | `canonicalFactory155` | `8f82fbdc740e4bf5448e53823c833e22f37db0aacadad01bc4983a4e58e72010` |
| `filter/vaseline:upsample` | `canonicalFactory170` | `322ba53c3b001878f026c615998086ef7732277b5f2d2401064ea2497cb6113a` |
| `filter/wind:wind` | `canonicalFactory177` | `163a65997398acd140ec10572d9253914d1659fc240187c1eae5a9de354810dd` |

The resolved `MODE=0` and `METHOD=1` define maps were used for Strokes and
Wind. No raw-canonical/public-adapter mismatch is hidden in this slice.

## Global and loop proof boundary

An independent in-memory projection seeded the existing counted-loop proof
from the exact typed `const int` declaration without changing any expression,
statement, declaration, interface, resource, or define object. Every frozen
post hash reproduced:

| Key | New integer global | Trips | Depth/product | Charge | Post function / whole SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| Bloom | `MAX_TAPS@8=64` | `[64]` | 1 / 64 | 64 | `66138a890082a6185afea09a5f9a169114193bf0134b6153737a663b27a86270` / `ff1fa1ba17abb3bdcd8daf7059b517609db49cfc62c10836b86ea86a1d4c696c` |
| Directional | `N@6=32` | `[32]` | 1 / 32 | 32 | `6e57feabe450d500b7ac2ddf328e855d72e0eb2c764c89b94c6c6f9afa184f96` / `21e4cc0784b7bbffa453e549776e3ed332df1219bf77d1c42bf32d650f8c1f7b` |
| Spin | `N@9=32` | `[32]` | 1 / 32 | 32 | `974b46a9db569acad639c8fd500c839f48f15b9bd42baac27374e204ca1d9e51` / `af920749f40d2f9eafcfa3bf9d1ffccf3164571475e1b9162053cba5b3e43bff` |
| Strokes | `MAX_TAPS@8=24` | `[3,3,24]` | 2 / 24 | 72 | `0ee608091d09aece9a1eba08224b1980be15e2c1eb288b206fe47f95c2cfb344` / `5ac93407e6a52ef895a887b3817c781d58ac9b974afe30415f31c6b4a9e8cbbf` |
| Vaseline | `TAP_COUNT@8=32` | `[32]` | 1 / 32 | 32 | `2e86ae95c587a74560e8cdd1d72bdf3f1d5cc9a14183ed136dc1950a590b2389` / `831676d46152cd861a4f658fb6bfe75c06c3a8275d2b9acaae00ae8038cc39a6` |
| Wind | `MAX_STEPS@8=128` | `[128]` | 1 / 128 | 128 | `70e4d4612ed144e0beb110e8fbbaf5d02b60e27e23fbf6961a30ac8d43bbb8e4` / `6a5cb2724a9dfa61aaf5f7879a65fe9ec3cd353b7e815f20eb0915e4a103f9e0` |

All projected loops use bound kind `source-global-const-literal`, are proved,
remain acyclic, and stay below the unchanged trip/depth/product/charge limits.
The final brief correctly distinguishes the one new `const int` from the exact
already-supported `const float` globals in Bloom, Vaseline, and Wind and locks
their identities and existing automatic-local materialization.

The four-mode semantic/generator/emitter matrix and forgery rows are complete:
pre-proof with/without profile rejects, post-proof absent/wrong rejects, and
only exact post-proof plus the exact six-row profile accepts. Declaration,
initializer, symbol, read/write, loop-bound, proof-metric, call-graph,
key/source/define, capability, borrowed-profile, and caller-hash forgery are
all explicitly required at both validator and emitter boundaries.

## Interfaces, resources, fetches, and stack contract

All six binding/output signatures reproduced from typed declarations. Every
program has one sampler and one output, uses texture sampling, and uses no
derivatives. Reachable static texture sites reproduce as 1/1/1/2/2/2 in brief
order.

Dynamic bounds were checked from the exact source:

- Bloom 1..64; Directional 32; Spin 32.
- Strokes 29..119 for the UI domain and 21..119 for arbitrary finite F32
  `strokeLength`.
- Vaseline copy 1, normal 33.
- Wind copy 1 and normal 1..129. The frozen tiny-positive case proves the
  non-return normal path can break before its first candidate fetch and remain
  a one-fetch exact output copy.

The corrected Strokes source call graph includes `strokeVariation ->
valueNoise2 -> hash12`, `brushStrokeField -> hash12/hash22/srcSample`, `smear
-> srcSample`, and the conservative `smear -> sprayJitter -> valueNoise2 ->
hash12` route unless Release disassembly proves MODE-0 pruning.

There is intentionally no post-Task-23 generated C++ or `.su` evidence at this
pre-implementation review. The brief correctly makes fresh Debug, Release,
ASan/UBSan, `.su`, bounded call-chain, and Release-disassembly evidence a hard
implementation-acceptance gate; unresolved/inlined functions must be resolved
by disassembly, and dynamic stack, allocation, recursion, or indirect dispatch
is failure.

## Public behavior and mutation package

The final frozen package contains 19 cases: three for each selected key except
four for Wind. It contains exactly 12 mutations, two per key. Fresh regeneration
reproduced both JSON and report byte-for-byte.

All cases are finite, input-immutable, and exact-repeat for input F32, output
F32, and output RGBA8. Exact-copy cases pass. Every required mutation
divergence is non-identical in F32, and every required identity case matches in
both F32 and RGBA8. The added `wind-tiny-positive-no-march` case is an exact
identity control for both Wind mutations and directly covers the corrected
one-fetch normal-path minimum.

## Publication projection and exclusions

Starting from the accepted explicit 116-key Task 22 slice, adding only the six
selected keys independently reproduces:

- 122 typed, 124 public, 88 publicly unported, 212 corpus;
- typed-list SHA-256
  `9db3013a6b0f78d0b95fcb6713c54ace95e82d1545e796e7a380add23c009f0b`;
- public-list SHA-256
  `2b84fff4d6f35aec1ac6bcc35188d9893e3194c90b9c428775a7308ce1f6281a`;
- exact new typed positions 7, 23, 77, 82, 92, and 96 with the brief's stated
  neighbors.

`filter/reindex:nmReindexStats` remains in the 88-key excluded set. Independent
inspection reproduced its source SHA
`06525e054fc4910e7bc53345ad656071d2fcb33fc897f4aa35e8fc59b6f0b951`,
canonical factory SHA
`0b59d682d882cc0f01348e950c114aaaeb4249f23094741060e482840c7200b3`,
public adapter SHA
`bf9edac9f940e4f435ef55712245be8821b5893f04d68af11d32a059cd0d060f`,
and adapter-file SHA
`b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046`.
Its public factory is the adapter object and is not the canonical factory, so
exclusion is mandatory and correctly specified.

The remaining closed-world exclusions are explicit: other keys, global forms,
initializer forms, runtime bounds, loop forms/caps, derivatives, vector
indexing, numeric/word work, compatibility transforms, adapters, sampler/
resource/function ABI changes, corpus edits, and unrelated cleanup cannot
borrow this capability.

## Fresh review verification

- Task 23 oracle generator `--check`: pass on final frozen hashes.
- Corpus `--check`: pass.
- Current Task 22 typed generator `--check`: pass, 116 programs.
- Independent source/typed/proof/interface/resource/list recomputation: pass
  for all six programs.
- Independent public/canonical object identity and adapter absence: pass for
  all six programs.
- Frozen package census: 6 programs, 19 cases, 12 mutations; all case and
  mutation invariants pass.
- Accepted Task 22 baseline and all Task 23 preflight file hashes: match.

## Review audit trail

The original candidate brief was not approved. Review identified an obsolete
Task 22 brief/report gate; wording that incorrectly excluded existing
`const float` globals; an incorrect Wind normal-path minimum; a missing tiny-
positive Wind oracle/control; an incorrect/incomplete Strokes call-chain
inventory; and a contradictory 19-case distribution sentence. Each issue was
reported before approval and corrected in successive brief/oracle amendments.
The final exact bytes and regenerated package were rereviewed after the last
amendment.

No residual scope/proof finding remains. The implementation must still stop on
any failure to reproduce the frozen identities, matrices, parity, generated
isolation, native oracles, stack/disassembly, or prior acceptance gates.
