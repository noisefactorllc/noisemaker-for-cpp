# Task 23 completion report: six literal source-global integer CPU kernels

Date: 2026-08-11  
Repository: `.`  
Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`

## Outcome

Task 23 is complete on the exact final bytes. The typed C++ CPU slice now adds
exactly these six direct-public-canonical kernels:

- `filter/bloom:ntapGather`
- `filter/directionalBlur:directionalBlur`
- `filter/spinBlur:spinBlur`
- `filter/strokes:stkSmear` with exact compile-time `MODE=0`
- `filter/vaseline:upsample`
- `filter/wind:wind` with exact compile-time `METHOD=1`

The final census is **122 typed / 124 public / 88 remaining / 212 corpus**.
The typed-key and public-key list SHA-256 values are respectively
`9db3013a6b0f78d0b95fcb6713c54ace95e82d1545e796e7a380add23c009f0b`
and `2b84fff4d6f35aec1ac6bcc35188d9893e3194c90b9c428775a7308ce1f6281a`.
The six insertion positions are exactly `7, 23, 77, 82, 92, 96`.
`filter/reindex:nmReindexStats` remains excluded.

No Git operation, branch, worktree, pull request, corpus edit, runtime edit,
adapter, compatibility transform, numeric exception, or production dependency
on `noisemaker-for-cpu` was introduced.

## Authenticated inputs

| Artifact | SHA-256 |
| --- | --- |
| Final Task 23 brief | `8aab4f5a9274879f7061c51595bba30f29f02d9606c4f76cf0e1e7312227915f` |
| Frontier audit | `cc49663ed312f95fc3d83cde245a95dc8719a1a90059d750ae9f7b9611061666` |
| Oracle generator | `f91ece9510c092e9c0221fc9b326522840c0b10eb3433b858eea3d786f7f57a2` |
| Frozen oracle JSON | `a832ea550911634dbe2e98e62b51837d8fa57612243416a88f70af69f626c52d` |
| Oracle report | `8a060f2b74fcc4c7d8ed74ca315b8239a28be0475a57067f3f223667bd009303` |
| Brief review | `23e68c35e77af2a821ba211b0b29c8ec856db194ef12cd9ad24647af7fc5bad2` |
| Accepted Task 22 report | `69bcc357de8a8e6df73b8b80ec0e8b5d3e2ca71f12edee25750e21f95c68a7d9` |
| Amended implementation design | `dab4ce6d8b6859fea782e2dd447921d07dc56a77edc9f972fd8b90ca9c5a529d` |
| Amended design review | `a2690803296c938d64d558d4b000b4b8d5a190aaed14f6fec55d83e4197e7c42` |

The Task 23 oracle generator passed `--check` before implementation and again
on final bytes. The accepted Task 15 through Task 24 oracle generators all pass
their read-only `--check` commands.

## Architecture and proof boundary

The only new capability is `source-global-literal-int-v1`, present exactly
once in the slice-global capability vocabulary. An explicit per-program
carrier is required for exactly the six admitted keys and rejected everywhere
else.

The implementation authenticates the closed key/raw source/normalized source/
define/declaration/read/interface/pre-proof profile, returns one immutable
integer-bound seed, and rebuilds proof state through this fixed sequence:

1. clear all submitted counted-loop proofs;
2. perform ordinary unseeded proof attachment;
3. authenticate the canonical pre-Task23 function, whole-program, interface,
   global declaration, and read-site identities;
4. attach proofs again with the authenticated source-global bound seed;
5. require exact equality with the submitted post-proof functions, summary,
   post-function hash, and post-whole-program hash.

The generator and emitter independently reconstruct and validate this state.
Both also require the exact explicit carrier and exact caller source hash. A
missing, wrong, or attacker-updated caller hash cannot authorize a tree.

| Key | Raw SHA | Normalized SHA | Pre function SHA | Post function SHA | Pre whole SHA | Post whole SHA | Interface SHA |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bloom | `f11c983976cb8450d611e8d888bd151a4c2cfdda8d9d772f906608dedb99d237` | `1d20c3bccadf30a1f6c3c6f8903ed805287933fcc1257d3ae6d4b98c5d0b9f81` | `a000425b8ae57882a6877bf2c390f3d1fb3ce226d0181f0fa76d8851d7a79163` | `66138a890082a6185afea09a5f9a169114193bf0134b6153737a663b27a86270` | `915a83f7673ec52fd79e8ed7a0a02094f720fbaa575db63318227f14c3aa2f51` | `ff1fa1ba17abb3bdcd8daf7059b517609db49cfc62c10836b86ea86a1d4c696c` | `b1bbe45469447847e91fbb66b6ee1b0cfc5a5a07cdac53cb322a728e295b8fb8` |
| Directional | `1e4a9d6371683b75a1dbefa968e1536e0017e921fe02f80e600e8f1482e8691c` | `587b19df3989bf8bb649a86265f4210561077ccadcec30f0a92077510bcbf668` | `8c0e81f16787bce2ab63a414b9774702ce3ceac9be71f7bad46c9bccde14ddfa` | `6e57feabe450d500b7ac2ddf328e855d72e0eb2c764c89b94c6c6f9afa184f96` | `30011a8fd6f15943857b5d978a5383cbf0408becbfcdd2a8e9fd08eddab11153` | `21e4cc0784b7bbffa453e549776e3ed332df1219bf77d1c42bf32d650f8c1f7b` | `3934c143ad58175d44458d78b2641badf31363c0f8438b1b5f656cbf6e269858` |
| Spin | `a5ee242e189066b55d4d5c3140e957418bdff582b367d1f6d4cdfee4c333b405` | `b829271f6c58fccde0e5723cd2bc7d7d3f47acfeb4cf1ce157bc996fb04ff1ee` | `f9563d0e1e160ac48d4f6b0becdcb4ced10342039f0ef8c0a09f822e0c8cc8e8` | `974b46a9db569acad639c8fd500c839f48f15b9bd42baac27374e204ca1d9e51` | `5d3e1a5f3907bc1678620013f2a5e6854c386d12af60a1e92bc196c06ee7e6bc` | `af920749f40d2f9eafcfa3bf9d1ffccf3164571475e1b9162053cba5b3e43bff` | `4b4d07b3a0cd718e48c976ef202de9dff5e7c35d422c371f6243ff0fbf9fa723` |
| Strokes | `dac057232a650f3c9eb56829aa12507b639d8632f6fc132cbd067a28996fa4db` | `796bad6231e640aec7c6f471465f57112f77394d921bff9902833955e1e20f15` | `5e5e0bb5091f6d4221e5396f3ed5dc73854543281ef519fbaddb0fdcd5c3fbc9` | `0ee608091d09aece9a1eba08224b1980be15e2c1eb288b206fe47f95c2cfb344` | `b7b6c65e3275843bd141f9b0c1fcf40daad671dcbeebef2db6a4684ec750790c` | `5ac93407e6a52ef895a887b3817c781d58ac9b974afe30415f31c6b4a9e8cbbf` | `8fe812a5bdfa275782969cb6146b0e8005e8dc521af9e5b10926bc49d2b89fef` |
| Vaseline | `39055a214903d09a9b2dd8db9ec5b2023a920c22707ec424ae90d5fb90ebf461` | `1785f58af7b191e5a4f1a55223476d12372c97f87c062d34ecefe07550b05c93` | `9f2f11099585a38441157f4e4bb847808c4fd81df1c69cc79d1b651b0fe90374` | `2e86ae95c587a74560e8cdd1d72bdf3f1d5cc9a14183ed136dc1950a590b2389` | `5771c7b74d9e30e47f0b84438bc40e16d4c0da36346325862bef6516c5f0d60d` | `831676d46152cd861a4f658fb6bfe75c06c3a8275d2b9acaae00ae8038cc39a6` | `fc9fd33b3e14a9808c66c17f3b358d79be3b97c11c6fd6ea281ce51118e0de9e` |
| Wind | `68eb0f4deca51ab5352307fa06509b153cf19a29cea4820d054adafa42655f22` | `665e842850e766cbf988212669457fb9fd76dff59e52a2f7b2cedd242e490fa4` | `214d03b9c58da73392e8b05200035b6e81244dbec06705302a237da23081ef6d` | `70e4d4612ed144e0beb110e8fbbaf5d02b60e27e23fbf6961a30ac8d43bbb8e4` | `b08edc234c42aa039867a7c549eff408e7c3c51cfa28d0951a437a00043a2dc0` | `6a5cb2724a9dfa61aaf5f7879a65fe9ec3cd353b7e815f20eb0915e4a103f9e0` | `455e2e5350b3a027556adc181e5ce3099ca395f801add229956b750d31acdf85` |

The exact automatic globals and proof charges are Bloom `MAX_TAPS@8=64` / 64,
Directional `N@6=32` / 32, Spin `N@9=32` / 32, Strokes
`MAX_TAPS@8=24` / 72, Vaseline `TAP_COUNT@8=32` / 32, and Wind
`MAX_STEPS@8=128` / 128. Each emits exactly once as an automatic
`const std::int32_t`; none is static, thread-local, State storage, or a runtime
binding.

## Negative and reconstruction evidence

All six authentic post-proof controls pass independently at the semantic,
generator, and emitter boundaries. For every key, the canonical pre-proof with
absent or exact carrier, exact post with absent/wrong carrier, fully cleared
tree, forged post proof, and forged post with attacker-updated raw/caller hash
all fail closed as required.

The complete design matrix is exercised independently at all three boundaries:
wrong key; separate raw/normalized/define drift; declaration name, ID, storage,
type, writability, literal spelling, and literal value; zero, signed, suffix,
hex, octal, unary, binary, cast, constructor, and ID initializers; missing,
extra, and dependent globals; applicable const-float drift; coherent shadow,
assignment, update, and resolved escape; read owner, ID, and span; literalized
and wrong-ID loop bounds; proof bound kind, trips, lexical/effective depth,
product, and charge; type-correct return in loop; and arity/type-correct
recursion. Target shapes and changed-node census are asserted. Capability
vocabulary absent/wrong/extra/duplicate, foreign carrier borrowing, and a prior
key with the new global vocabulary but no carrier are also covered.

The caller-hash four-state test proves exact acceptance and rejection of
missing, wrong, and attacker-updated states. Independent focused review found
this matrix and production boundary clean after the coherent-IR corrections.

## Generation and isolation

Canonical generation and immediate regeneration check both pass at 122
programs. The accepted Task 22 counterfactual 116-program generated source is
exactly **932,898 bytes** with SHA-256
`a3f8135d41e9f2abc864fada60532309b56c43f6e6eb138d548a23b57f944c4f`.
Blocks 0 through 6 are raw-byte identical; all 116 accepted blocks are
byte-identical after replacing only `typed_[0-9]+` namespace ordinals. The six
new blocks are the only additions.

The Strokes source prototype is emitted once as a declaration and its helper
definition once with a nonempty body. The emitter selects function-definition
occurrences by exact definition span, so a source prototype cannot become an
empty duplicate definition.

Generated fetch accounting matches the frozen profile: Bloom 1 static and
1..64 dynamic; Directional 1 / exactly 32; Spin 1 / exactly 32; Strokes 2
resolved static and 29..119 UI-domain dynamic (21..119 arbitrary finite F32);
Vaseline 2 with copy 1 and normal 33; Wind 2 with copy 1 and normal 1..129.
The Wind tiny-positive case enters the normal guard, computes exact F32 reach
`0.64`, and breaks before a candidate fetch.

## Native oracle and ABI evidence

The embedded C++ table mechanically matches every field of the frozen JSON:
19 cases distributed 3/3/3/3/3/4, complete F32 and RGBA8 hashes, five probe
coordinates and 30 lane words per case, metrics, ordering, copy/divergence
flags, and exact uniform bits. Every case renders twice identically, remains
finite, and leaves its input immutable. Exact-copy controls pass.

All twelve frozen mutations first fail production validation/emission, then a
test-only reconstructed emitter compiles twelve unique temporary namespaces
once with `-ffp-contract=off`; all mutated F32/RGBA8 hashes and changed-lane/
byte metrics match the frozen oracle. No temporary mutation byte enters the
repository or generated artifacts.

Every required runtime binding is checked missing and wrong-type; unrelated
bindings remain accepted. `MODE` and `METHOD` are proven absent from runtime
bindings. The public catalog has exactly 124 sorted unique entries. The final
native executable passes all **118** internal tests.

## Stack, disassembly, and resource evidence

Fresh Debug, Release, and sanitizer builds used `-ffp-contract=off`,
`-fstack-usage`, and `-fstack-size-section`. Debug and Release `.su` records
are static. Sanitizer dynamic classifications are instrumentation-only and are
not used as the resource proof, matching accepted Task 21 practice.

| Program / maximum non-inlined chain | Debug bytes | Release bytes |
| --- | ---: | ---: |
| Bloom `pixel` | 832 | 240 |
| Directional `pixel -> hash12` | 880 | 208 |
| Spin max of `pixel -> hash12 / rotateAround` | 1,040 | 256 |
| Strokes conservative maximum | 3,328 | 704 |
| Vaseline `pixel -> clamp01 / chebyshev_mask` | 1,744 | 400 |
| Wind `pixel -> lum` | 1,120 | 368 |

Strokes includes the conservative
`pixel -> smear -> sprayJitter -> valueNoise2 -> hash12` chain (3,328 Debug,
688 Release); the Release maximum is the `brushStrokeField` route at 704.
Scoped Release disassembly over all 41 symbols in the six generated namespaces
contains zero `blr`/`br`, allocator/deallocator, `alloca`, or exception-throw
targets. The routes are acyclic and bounded; no callback, virtual dispatch,
VLA, recursion, or per-pixel allocation route exists.

## Final verification

- `node task-15-oracle-generator.mjs --check` through Task 24: all pass.
- `python3 tools/glslcpp/check_corpus.py --check`: `check_corpus: ok`.
- `python3 tools/glslcpp/check_semantics.py --check`: 212 bodies pass.
- `python3 tools/glslcpp/generate_kernels.py --check`: exit 0.
- `python3 tools/glslcpp/generate_typed_slice.py --check`: 122 programs pass.
- Full semantic module: **32 tests**, 162.643 seconds, pass.
- Full typed-generator module: **83 tests**, 532.479 seconds, pass.
- Full Python discovery on final bytes: **131 tests**, 543.931 seconds, pass.
- Fresh Debug Unix Makefiles build and CTest: 1/1 pass in 3.49 seconds.
- Fresh Release Unix Makefiles build and CTest: 1/1 pass in 0.46 seconds.
- Fresh combined ASan/UBSan build: pass. Apple's ASan runtime rejects
  `detect_leaks=1` as unsupported before test execution; the accepted-platform
  rerun with `detect_leaks=0`, ASan `halt_on_error=1`, and UBSan halt/stacktrace
  passes CTest 1/1 in 8.61 seconds with no sanitizer finding.
- Hardened generated isolation: pass in 89.801 seconds.
- Comprehensive all-six semantic matrix: pass in 1.651 seconds.
- Comprehensive all-six generator/emitter matrix: pass in 3.288 seconds.
- Independent focused matrix rerun: 2/2 pass in 4.308 seconds.

## Exact final owned-file inventory

| Path | Final SHA-256 |
| --- | --- |
| `tools/glslcpp/frontend/semantic.py` | `77a6c23e9369436b6d5e65a6ce8b95bec2a496266fdb9859e84a461f3f8bbeb6` |
| `tools/glslcpp/frontend/loop_proof.py` | `0cfe3a1d6c3f5c8b6781e4961b0220546d426af22662558959a3d66d3c221a09` |
| `tools/glslcpp/generate_typed_slice.py` | `3a77d1702484e6ffed83c52e20d7b79315536f39150b43daed134b75bae2133d` |
| `tools/glslcpp/emit_typed_cpp.py` | `54bdacfc2912c6a33a1da76820ef4182d9722a2b5f03ea7f08f43d15bd8eb1f3` |
| `tools/glslcpp/typed_slice.json` | `4af84d22d3272f98f8d1698f34874b1fb249ad0ec9deec2c87cb8f9b354d163f` |
| `tests/test_semantic.py` | `6454f442367177347cf06ea271793840c2d9127d278f7be97c8ba5ec3af4ae87` |
| `tests/test_typed_generator.py` | `f0809d1c832e3e86857f0452291d765ec76e3631a22fcb9640e18dcd009aeb24` |
| `tests/test_generated_kernels.cpp` | `6dba52360129c0fbd79f513d9e3fb1979e6ed99fe6c684577e7809f2c39bd2ba` |
| `tests/test_typed_slice.cpp` | `f85ad92eecbd386d549eb85402a17e93a5a17c08c122c37e474fe9ae6d91dd3e` |
| `src/typed_generated/typed_slice.cpp` | `c36f84aa5bcf09d932837bb84ba323ce51d44398ca29deb4dfb71151c32442a8` |
| `src/typed_generated/typed_manifest.json` | `d979fe5d968030cfc3ec9d688367b8b4418b9a841a6f612d65eac03ed5bd4184` |
| `include/noisemaker/generated/catalog.hpp` | `0704695854c772e26ca014d001d0573ce8fb87e367ffaf1c5cbc7e581bf675ed` |

`tests/test_typed_slice.cpp` intentionally remains byte-identical to accepted
Task 22. Protected unowned parser, typed IR, body semantic, prior proof modules,
and compatibility modules retain their accepted hashes. No file outside the
twelve-path Task 23 scope was changed.

## Review status

The amended design was independently approved before implementation. Focused
final implementation rereview is clean: every Step 1/2 row maps to an asserted,
coherent mutation; caller-hash and central reproof boundaries are sound; and
Strokes emits one prototype plus one nonempty definition. Final report and
exact-byte approval are requested on this completed evidence.
