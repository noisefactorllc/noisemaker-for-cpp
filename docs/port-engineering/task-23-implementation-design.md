# Task 23 implementation design: literal source-global integer proof

> **Status:** implementation design only. This document authorizes no repository
> edit and no Git operation.

## 1. Authenticated inputs and completion target

Implementation must start from the independently accepted Task 22 tree and stop
if any preflight identity differs.

| Input | Required SHA-256 |
| --- | --- |
| Final Task 23 brief | `8aab4f5a9274879f7061c51595bba30f29f02d9606c4f76cf0e1e7312227915f` |
| Task 23 frontier audit | `cc49663ed312f95fc3d83cde245a95dc8719a1a90059d750ae9f7b9611061666` |
| Task 23 oracle generator | `f91ece9510c092e9c0221fc9b326522840c0b10eb3433b858eea3d786f7f57a2` |
| Task 23 oracle JSON | `a832ea550911634dbe2e98e62b51837d8fa57612243416a88f70af69f626c52d` |
| Task 23 oracle report | `8a060f2b74fcc4c7d8ed74ca315b8239a28be0475a57067f3f223667bd009303` |
| Final Task 23 brief review | `23e68c35e77af2a821ba211b0b29c8ec856db194ef12cd9ad24647af7fc5bad2` |
| Accepted Task 22 report | `69bcc357de8a8e6df73b8b80ec0e8b5d3e2ca71f12edee25750e21f95c68a7d9` |
| Accepted Task 22 independent review | `102a56ab642c1884319a827530639d0dc9943441393e03ea497274812912e5af` |

The accepted starting tree is exactly 116 typed / 118 public / 94 publicly
unported / 212 corpus, with the final full Python discovery result 122/122.
Task 23 adds exactly these six direct-public-canonical keys and nothing else:

```text
filter/bloom:ntapGather
filter/directionalBlur:directionalBlur
filter/spinBlur:spinBlur
filter/strokes:stkSmear
filter/vaseline:upsample
filter/wind:wind
```

The result is exactly 122 typed / 124 public / 88 publicly unported / 212
corpus. The sorted typed-key digest is
`9db3013a6b0f78d0b95fcb6713c54ace95e82d1545e796e7a380add23c009f0b`;
the public-key digest is
`2b84fff4d6f35aec1ac6bcc35188d9893e3194c90b9c428775a7308ce1f6281a`.
Tests compare explicit lists and digests.

At implementation preflight, hash all Task 23-owned files and generated outputs.
The accepted Task 22 bytes currently expected are:

| Path | Accepted SHA-256 |
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

The manifest hash above must be checked against the accepted Task 22 report
before editing; if the report's byte value and the preflight calculation do not
agree, stop rather than treating this design transcription as authority.

## 2. Chosen architecture

Use one explicit authorization carrier plus one shared, pure typed-tree
authenticator, then seed the existing counted-loop proof algorithm with the
authenticated global bound.

The carrier value is exactly the capability string
`source-global-literal-int-v1`; absence is `None`. It is passed explicitly to
the semantic analyzer, generator validator, and emitter. It is never inferred
from the key alone and is not stored as a new typed-IR proof field. The existing
slice-global capability vocabulary remains the publication record; the
explicit carrier/profile is the sole per-program authorization.

The shared authenticator lives in `frontend/loop_proof.py`, an already-owned
file. It accepts the actual key, raw and normalized source, define map, typed
declarations, and typed functions, and returns an immutable seed tuple only
after the complete six-row profile matches. A conceptual signature is:

```python
SOURCE_GLOBAL_LITERAL_INT_CAPABILITY = "source-global-literal-int-v1"

def authenticate_source_global_literal_int(
    *, key: str, raw_source: str, source: str,
    preprocessor_defines: tuple[tuple[str, object], ...],
    declarations: tuple[TypedDeclaration, ...],
    functions: tuple[TypedFunction, ...],
    profile: str | None,
) -> tuple[tuple[int, int, str, Symbol], ...]: ...

def attach_counted_loop_proofs(
    functions: tuple[TypedFunction, ...], key: str, *,
    source_global_bounds: tuple[tuple[int, int, str, Symbol], ...] = (),
) -> tuple[TypedFunction, ...]: ...

def clear_counted_loop_proofs(
    functions: tuple[TypedFunction, ...],
) -> tuple[TypedFunction, ...]: ...

def validate_source_global_literal_int_program(
    program: TypedProgram, profile: str | None,
) -> None: ...

def rebuild_authenticated_counted_loop_proofs(
    program: TypedProgram, profile: str | None,
) -> tuple[tuple[TypedFunction, ...], CountedLoopProgramProof]: ...
```

`authenticate_source_global_literal_int` accepts only the exact canonical
pre-Task23 function tuple. That tuple is reconstructed mechanically by clearing
all submitted counted-loop proofs and running the existing ordinary unseeded
`attach_counted_loop_proofs`; this restores every previously supported local
or literal proof while leaving only the Task23 source-global-bound loop(s)
unproved. It rejects if this ordinary tuple misses the exact frozen
pre-functions hash or if any declaration/read/profile identity differs. A fully
cleared tuple is never authoritative. The
returned tuple has one item `(symbol_id, maximum,
"source-global-const-literal", symbol)`. `attach_counted_loop_proofs` converts
that tuple to the existing per-function `bounded` map before calling
`_annotate_sequence`; every function begins with the same immutable global
seed. Local bound discovery remains source-ordered and unchanged. No new
`CountedLoopProof` or `CountedLoopProgramProof` member, proof kind, safety
limit, or typed-IR dataclass is added.

Whenever a pre whole-program hash is checked, first clear submitted proofs,
then reconstruct `pre_functions=attach_counted_loop_proofs(cleared, key)` with
the default empty global seed and
`pre_summary=summarize_counted_loop_proofs(pre_functions)`; preserve every
other program field exactly. Never hash the fully cleared functions as the pre
state and never combine pre functions with the submitted post summary. The
ordinary serialization must equal the frozen pre-functions/pre-whole hashes.
The seeded functions plus their recomputed summary must equal the frozen
post-functions and post-whole hashes.

The flow is:

```text
parsed source + explicit profile
  -> semantic declarations and typed bodies
  -> ordinary unseeded proof attachment reconstructs canonical pre state
  -> authenticate exact pre tuple/hash/summary
  -> seed existing counted-loop proof
  -> authenticate exact post tuple/hash/summary
  -> TypedProgram with ordinary existing proof records
  -> generator independently clears, ordinary-attaches, authenticates pre, seeds, compares post
  -> emitter independently clears, ordinary-attaches, authenticates pre, seeds, compares post
  -> automatic const std::int32_t in each referencing function
```

Two alternatives are rejected:

1. Key-only implicit proof attachment would make `pre-proof + profile` and
   `post-proof + absent profile` indistinguishable and would fail the required
   four-mode authorization matrix.
2. A new global-IR type, proof dataclass, namespace constant, or runtime helper
   would broaden the language/runtime surface and is unnecessary. The existing
   typed declaration, expression, local-type, reference-closure, and loop-proof
   mechanisms already represent the admitted program exactly.

## 3. Exact six-row profile

The authenticator uses a closed constant table; no wildcard, structural
fallback, or seventh-key path exists.

| Key | Defines | Raw bytes / SHA | Normalized SHA | Int declaration | Loops / caps | Max depth/product | Charge |
| --- | --- | --- | --- | --- | --- | --- | ---: |
| `filter/bloom:ntapGather` | `{}` | 2196 / `f11c983976cb8450d611e8d888bd151a4c2cfdda8d9d772f906608dedb99d237` | `1d20c3bccadf30a1f6c3c6f8903ed805287933fcc1257d3ae6d4b98c5d0b9f81` | `MAX_TAPS@8 = 64` | 1 / `[64]` | 1 / 64 | 64 |
| `filter/directionalBlur:directionalBlur` | `{}` | 1153 / `1e4a9d6371683b75a1dbefa968e1536e0017e921fe02f80e600e8f1482e8691c` | `587b19df3989bf8bb649a86265f4210561077ccadcec30f0a92077510bcbf668` | `N@6 = 32` | 1 / `[32]` | 1 / 32 | 32 |
| `filter/spinBlur:spinBlur` | `{}` | 3077 / `a5ee242e189066b55d4d5c3140e957418bdff582b367d1f6d4cdfee4c333b405` | `b829271f6c58fccde0e5723cd2bc7d7d3f47acfeb4cf1ce157bc996fb04ff1ee` | `N@9 = 32` | 1 / `[32]` | 1 / 32 | 32 |
| `filter/strokes:stkSmear` | `{"MODE":0}` | 14787 / `dac057232a650f3c9eb56829aa12507b639d8632f6fc132cbd067a28996fa4db` | `796bad6231e640aec7c6f471465f57112f77394d921bff9902833955e1e20f15` | `MAX_TAPS@8 = 24` | 3 / `[3,3,24]` | 2 / 24 | 72 |
| `filter/vaseline:upsample` | `{}` | 2524 / `39055a214903d09a9b2dd8db9ec5b2023a920c22707ec424ae90d5fb90ebf461` | `1785f58af7b191e5a4f1a55223476d12372c97f87c062d34ecefe07550b05c93` | `TAP_COUNT@8 = 32` | 1 / `[32]` | 1 / 32 | 32 |
| `filter/wind:wind` | `{"METHOD":1}` | 3520 / `68eb0f4deca51ab5352307fa06509b153cf19a29cea4820d054adafa42655f22` | `665e842850e766cbf988212669457fb9fd76dff59e52a2f7b2cedd242e490fa4` | `MAX_STEPS@8 = 128` | 1 / `[128]` | 1 / 128 | 128 |

The publication profile also locks direct public identity to these canonical
factories; all six have no canonical adapter:

| Key | Canonical factory | Factory text SHA-256 |
| --- | --- | --- |
| Bloom | `canonicalFactory23` | `a737ac48f663f041f763677680ab5d5282482ab6d10143939de055b980c4207c` |
| Directional | `canonicalFactory47` | `a3803238488c9bd2fe786b931a0a2ba81a057d02f984017d8e10073c68873344` |
| Spin | `canonicalFactory145` | `c6b97d30339acd21fc01d2d2cd31073c62d2ba82dbb80e95d9457b0f59737547` |
| Strokes | `canonicalFactory155` | `8f82fbdc740e4bf5448e53823c833e22f37db0aacadad01bc4983a4e58e72010` |
| Vaseline | `canonicalFactory170` | `322ba53c3b001878f026c615998086ef7732277b5f2d2401064ea2497cb6113a` |
| Wind | `canonicalFactory177` | `163a65997398acd140ec10572d9253914d1659fc240187c1eae5a9de354810dd` |

Each integer declaration must be exactly top-level storage `const`, type
`int`, non-writable, with one positive decimal literal child and no dependency.
The spelling must match `[1-9][0-9]*`; reject zero, sign nodes, suffixes,
hexadecimal/octal spelling, constructors, casts, identifiers, unary/binary
expressions, missing initializers, multiple children, and extra integers.

The authenticator also compares the complete set of non-interface globals.
The following existing float globals remain frozen under the pre-existing
source-global behavior and do not acquire the new capability:

| Key | Existing exact float globals |
| --- | --- |
| Bloom | `GOLDEN_ANGLE@9 = 2.39996323`, `PI@10 = 3.14159265359` |
| Directional | none |
| Spin | none |
| Strokes | none |
| Vaseline | `RADIUS@9 = 48.0`, `GOLDEN_ANGLE@10 = 2.39996323`, `BRIGHTNESS_ADJUST@11 = 0.15` |
| Wind | `STEP_PX@9 = 1.0`, `MAX_REACH@10 = 128.0` |

All integer reads are audited by exact symbol identity, owning function, span,
and read-only-lvalue category; assignments, pre/post updates, aliasing, address
escape, or shadow substitution reject. The frozen read inventory is:

| Key | Owner / normalized spans |
| --- | --- |
| Bloom | `main@11`: `30:35-43`, `37:25-33` |
| Directional | `main@9`: `22:42-43`, `26:25-26`, `27:37-38`, `31:29-30` |
| Spin | `main@16`: `45:37-38`, `54:25-26`, `55:41-42`, `60:29-30` |
| Strokes | `smear@39`: `156:26-34` |
| Vaseline | `main@16`: `49:25-34`, `50:36-45` |
| Wind | `main@13`: `46:26-35` |

The exact loop spans are Bloom `main@11 37:5-59:6`; Directional
`main@9 26:5-30:6`; Spin `main@16 54:5-59:6`; Strokes
`brushStrokeField@32 87:5-115:6`, nested `88:9-114:10`, and
`smear@39 156:5-170:6`; Vaseline `main@16 49:5-62:6`; Wind
`main@13 46:5-65:6`. Every source-global-bound proof has bound kind exactly
`source-global-const-literal`. Existing trip limit 128, depth 3, lexical
product 4096, and entry charge 4096 remain unchanged.

## 4. Independent authority at each layer

### 4.1 Semantic analyzer

Change `analyze_program` to accept only the new keyword:

```python
def analyze_program(parsed: dict, program_key: str | None = None, *,
                    source_global_literal_int_profile: str | None = None
                    ) -> TypedProgram:
```

Build typed declarations, including initializers, before proof attachment.
First run the existing ordinary unseeded proof attachment on the freshly typed
functions and authenticate that canonical pre tuple, summary, and hashes with
the declarations. For Strokes this intentionally retains the two nested local
3-trip proofs while leaving the global 24-trip loop unproved.
Pass the returned seed to `attach_counted_loop_proofs`, then run the existing
downstream proof passes and summary construction. Require the resulting exact
post-functions hash, post whole-program hash, and program summary. Finish by
calling `validate_source_global_literal_int_program` on that post-proof program.

The semantic validator always treats its argument as a submitted final state:
it saves the submitted functions, clears counted-loop proofs, runs ordinary
unseeded attachment to reconstruct an independent canonical pre tuple,
authenticates the pre tuple/hash/summary, reattaches from the authenticated
global seed, and accepts only if the submitted functions are dataclass-equal to the
recomputed exact post tuple and its frozen post hash/summary. Thus the semantic
pipeline's internal pre tuple is construction input, never an accepted program
state. For one of the six exact keys, an absent/wrong carrier is a semantic
error; an exact carrier is the only way `analyze_program` returns the exact
post-proof program. Other keys with no carrier retain their existing behavior,
while any other key with this carrier rejects.

The analyzer does not trust a caller hash and does not store the carrier in the
IR. The current source, raw source, defines, declarations, symbol graph, typed
bodies, and spans are the authority.

### 4.2 Generator validator

Add the capability to `APPROVED_CAPABILITIES`, but exclude it from builtin
capabilities just like other structural capabilities. Extend
`validate_capabilities` with:

```python
source_global_literal_int_profile: str | None = None
```

For an exact six-row key, require all of:

- the slice-global declared capability vocabulary contains
  `source-global-literal-int-v1` exactly once;
- carrier equals `source-global-literal-int-v1`;
- no compatibility transform and numeric contract exactly `glsl-f32`;
- save submitted functions, clear counted-loop proof fields, reconstruct the
  canonical pre tuple through ordinary unseeded attachment, and authenticate
  its exact frozen tuple/hash/summary;
- proof recomputation from that authenticated pre tuple plus the authenticated
  seed, followed by dataclass equality between submitted and recomputed post;
- exact post-functions/post-whole hashes, program summary, and safety metrics;
- corpus raw/normalized source plus function/whole/interface/profile identities
  below;
- exact binding, resource, and helper/fetch metadata. Public JavaScript
  identity remains external oracle provenance.

For every other key, the carrier must be absent; the key must tolerate the new
item in the shared global vocabulary. A foreign key with the carrier, an exact
six key with absent/wrong carrier, or a global vocabulary with the capability
missing, duplicated, misspelled, or accompanied by an unknown item rejects.

The generation driver derives the carrier only after matching the exact key,
capability membership, and frozen profile. It passes the carrier separately to
`analyze_program`, `validate_capabilities`, and `render_typed_cpp`. It must not
silently infer authorization inside any of those functions.

The existing manifest schema is sufficient. `typed_slice.json` has one
slice-global capability vocabulary, and generation copies that identical list
into every manifest program entry; add
`source-global-literal-int-v1` exactly once to that vocabulary and expect it in
all 122 manifest records. That shared metadata does not authorize any
individual program. The internal explicit carrier selects only the exact six.
Their `compatibility_transform` remains `none`, and their
`numeric_literal_contract` remains `glsl-f32`. Do not add a per-program
capability/profile schema field or transform map.

All proof recomputation must go through the same authenticated seed. Add one
central `rebuild_authenticated_counted_loop_proofs` helper that saves the
submitted tuple, clears counted-loop proof fields, reconstructs ordinary
unseeded proofs, authenticates that exact canonical pre tuple/profile and its
summary/whole hash, and calls
`attach_counted_loop_proofs(..., source_global_bounds=seed)`. It returns both
the reconstructed post functions and post summary. Use it at the generator's current generic
recomputation site (currently near `generate_typed_slice.py:1276`) and at every
new Task 23 profile validation. A direct unseeded recomputation outside this
centralized canonical-pre reconstruction is a bug.

### 4.3 Emitter

Extend `render_typed_cpp` and `_Emitter` with the same explicit keyword
carrier. During `_Emitter.__post_init__`:

1. independently authenticate the actual source/global/read profile;
2. save the submitted functions; clear counted-loop proofs; run ordinary
   unseeded attachment; require that exact frozen pre tuple/hash/summary;
   independently reattach from that authenticated pre tuple using the returned
   global seed; require submitted/recomputed post
   dataclass equality plus the exact post tuple/hash/summary;
3. retain the current generic const-float dependency validation unchanged;
4. admit exactly the authenticated int declaration as dependency-free;
5. reject every unprofiled global, write, malformed initializer, proof drift,
   wrong/absent carrier, or seventh-key attempt.

Cache the one independently authenticated per-program seed on `_Emitter` and
route every counted-loop reconstruction through one emitter method, for example
`self._attach_counted(functions)`. Replace every current direct call (currently
near `emit_typed_cpp.py:160`, `218`, `253`, `271`, `294`, and `321`), including
calls made while recomputing discarded-counter, fixed-table, fixed-grid,
fixed-array, and fixed-affine predecessor proof families. Each call receives
the same seed. No later validator may erase Task 23 proof by recomputing with
the default empty seed.

`source_global_locals` already computes a function reference closure and
`local_type(int)` already yields `std::int32_t`. Preserve that mechanism. The
new output is therefore an ordinary function automatic such as:

```cpp
const std::int32_t MAX_TAPS = 64;
```

Only functions that reference the symbol receive it. No namespace, State,
function-static, thread-local, capture, or writable storage is permitted.
Existing float reference closure and emitted literal text remain byte-identical.

### 4.4 Split identity authority

The production generator freezes corpus raw/normalized source and the typed
identities below. It must not import, execute, or read
`../noisemaker-for-cpu`, and it must not carry unused
JavaScript factory/runtime hashes as false authority. The frozen external
oracle generator and its `--check`, artifact hash, and independent review own
the canonical runtime SHA, canonical factory text hashes, public function-object
identity, and canonical-adapter absence. The factory table in section 3 is
normative oracle provenance, not a `generate_typed_slice.py` constant table.

The production typed identities are:

| Key | Pre funcs | Post funcs | Pre whole | Post whole | Interface |
| --- | --- | --- | --- | --- | --- |
| Bloom | `a000425b8ae57882a6877bf2c390f3d1fb3ce226d0181f0fa76d8851d7a79163` | `66138a890082a6185afea09a5f9a169114193bf0134b6153737a663b27a86270` | `915a83f7673ec52fd79e8ed7a0a02094f720fbaa575db63318227f14c3aa2f51` | `ff1fa1ba17abb3bdcd8daf7059b517609db49cfc62c10836b86ea86a1d4c696c` | `b1bbe45469447847e91fbb66b6ee1b0cfc5a5a07cdac53cb322a728e295b8fb8` |
| Directional | `8c0e81f16787bce2ab63a414b9774702ce3ceac9be71f7bad46c9bccde14ddfa` | `6e57feabe450d500b7ac2ddf328e855d72e0eb2c764c89b94c6c6f9afa184f96` | `30011a8fd6f15943857b5d978a5383cbf0408becbfcdd2a8e9fd08eddab11153` | `21e4cc0784b7bbffa453e549776e3ed332df1219bf77d1c42bf32d650f8c1f7b` | `3934c143ad58175d44458d78b2641badf31363c0f8438b1b5f656cbf6e269858` |
| Spin | `f9563d0e1e160ac48d4f6b0becdcb4ced10342039f0ef8c0a09f822e0c8cc8e8` | `974b46a9db569acad639c8fd500c839f48f15b9bd42baac27374e204ca1d9e51` | `5d3e1a5f3907bc1678620013f2a5e6854c386d12af60a1e92bc196c06ee7e6bc` | `af920749f40d2f9eafcfa3bf9d1ffccf3164571475e1b9162053cba5b3e43bff` | `4b4d07b3a0cd718e48c976ef202de9dff5e7c35d422c371f6243ff0fbf9fa723` |
| Strokes | `5e5e0bb5091f6d4221e5396f3ed5dc73854543281ef519fbaddb0fdcd5c3fbc9` | `0ee608091d09aece9a1eba08224b1980be15e2c1eb288b206fe47f95c2cfb344` | `b7b6c65e3275843bd141f9b0c1fcf40daad671dcbeebef2db6a4684ec750790c` | `5ac93407e6a52ef895a887b3817c781d58ac9b974afe30415f31c6b4a9e8cbbf` | `8fe812a5bdfa275782969cb6146b0e8005e8dc521af9e5b10926bc49d2b89fef` |
| Vaseline | `9f2f11099585a38441157f4e4bb847808c4fd81df1c69cc79d1b651b0fe90374` | `2e86ae95c587a74560e8cdd1d72bdf3f1d5cc9a14183ed136dc1950a590b2389` | `5771c7b74d9e30e47f0b84438bc40e16d4c0da36346325862bef6516c5f0d60d` | `831676d46152cd861a4f658fb6bfe75c06c3a8275d2b9acaae00ae8038cc39a6` | `fc9fd33b3e14a9808c66c17f3b358d79be3b97c11c6fd6ea281ce51118e0de9e` |
| Wind | `214d03b9c58da73392e8b05200035b6e81244dbec06705302a237da23081ef6d` | `70e4d4612ed144e0beb110e8fbbaf5d02b60e27e23fbf6961a30ac8d43bbb8e4` | `b08edc234c42aa039867a7c549eff408e7c3c51cfa28d0951a437a00043a2dc0` | `6a5cb2724a9dfa61aaf5f7879a65fe9ec3cd353b7e815f20eb0915e4a103f9e0` | `455e2e5350b3a027556adc181e5ce3099ca395f801add229956b750d31acdf85` |

Caller-provided hashes are drift alarms only. Clear plus ordinary unseeded
attachment is normalization for canonical pre-state authentication, not
normalization of the accepted program: the original submitted tuple must still
equal the independently reconstructed exact post tuple. Tests exercise
authentic, fully cleared, canonical-pre, stale, and attacker-updated
caller-hash combinations; exact pre authentication, proof reconstruction, and
exact post equality decide acceptance in every combination.

Strokes is the regression lock for this distinction. Its fully cleared
functions hash is
`dc58c8e53799e41f8ab4c9263af336b37540ee58b1418cac6d3734e878bc7bc6`
with 0 proved / 3 unproved loops and is non-authoritative. Ordinary unseeded
attachment must yield pre-functions
`5e5e0bb5091f6d4221e5396f3ed5dc73854543281ef519fbaddb0fdcd5c3fbc9`,
pre-whole
`b7b6c65e3275843bd141f9b0c1fcf40daad671dcbeebef2db6a4684ec750790c`,
and 2 proved / 1 unproved. Seeded reconstruction must yield post-functions
`0ee608091d09aece9a1eba08224b1980be15e2c1eb288b206fe47f95c2cfb344`,
post-whole
`5ac93407e6a52ef895a887b3817c781d58ac9b974afe30415f31c6b4a9e8cbbf`,
3 proved / 0 unproved, and entry charge 72.

Regression tests enumerate every `attach_counted_loop_proofs` call path in the
generator and emitter. The six Task 23 programs retain the source-global seed
through all predecessor-proof recomputations. All previously accepted programs
receive the default empty seed, retain identical proof records and generated
bytes, and keep the Task 15-22 proof-family tests green.

## 5. Slice, generated code, and ABI

Add the capability once to `typed_slice.json`'s global vocabulary and add six
program entries with the exact defines. No per-program capability field,
compatibility transform, or numeric override is added. Final zero-based
positions are 7, 23, 77, 82, 92, and 96 with the exact neighboring keys from
the brief. `filter/reindex:nmReindexStats` and all other 88 unported public keys
remain excluded.

For each generated namespace, assert exact binder ABI, one sampler, one output,
texture use, no derivatives, and the following interface/fetch profile:

| Key | Binding ABI | Fetch accounting |
| --- | --- | --- |
| Bloom | `tileOffset@1`, `fullResolution@2`, `inputTex@3/S1`, `radius@4`, `renderScale@5`, `taps@6`, output `fragColor@7`, global `MAX_TAPS@8` | 1 static; dynamic 1..64 |
| Directional | `inputTex@1/S1`, `resolution@2`, `angle@3`, `blurDistance@4`, output `fragColor@5`, global `N@6` | 1 static; exactly 32 |
| Spin | `inputTex@1/S1`, `resolution@2`, `tileOffset@3`, `fullResolution@4`, `amount@5`, `centerX@6`, `centerY@7`, output `fragColor@8`, global `N@9` | 1 static; exactly 32 |
| Strokes | `inputTex@1/S1`, `resolution@2`, `tileOffset@3`, `strokeLength@4`, `balance@5`, `intensity@6`, output `fragColor@7`, global `MAX_TAPS@8`; exact `MODE=0` | 2 resolved static; UI 29..119, arbitrary finite F32 21..119 |
| Vaseline | `inputTex@1/S1`, `resolution@2`, `tileOffset@3`, `fullResolution@4`, `renderScale@5`, `alpha@6`, output `fragColor@7`, global `TAP_COUNT@8` | 2 static; copy 1, normal 33 |
| Wind | `inputTex@1/S1`, `resolution@2`, `tileOffset@3`, `direction@4`, `strength@5`, `threshold@6`, output `fragColor@7`, global `MAX_STEPS@8`; exact `METHOD=1` | 2 static; copy 1, normal 1..129; positive reach below 1 has only the initial fetch |

Binding tests cover every missing binding, wrong type, wrong sampler/output, and
extra control. `MODE=0` and `METHOD=1` are compile-time define profiles, not
runtime `Bindings` entries: freeze them in slice/source/profile metadata and in
the external JavaScript oracle execution, assert they select the generated
branch, and assert both names are absent from the native runtime binding ABI.

Generated isolation is mechanical:

- Task 22 blocks 0..6 remain raw-byte identical;
- all 116 prior blocks remain identical after replacing only namespace ordinals
  `typed_[0-9]+` with one sentinel;
- exactly six new blocks appear at the frozen positions;
- the integer automatic appears exactly in its reference closure, with no
  namespace/static/thread-local/State storage;
- no other token, manifest record, catalog ABI, allocation, dispatch,
  recursion, exception, callback/container, `alloca`, or generated `main`
  changes.

## 6. Test-first implementation sequence

### Step 0: immutable preflight

Authenticate all frozen artifacts, run the oracle generator `--check`, verify
the accepted Task 22 report/review/counts/list/hashes, and record hashes for all
owned files and generated outputs. Stop on any mismatch.

### Step 1: RED semantic and proof tests

In `tests/test_semantic.py`, first add failing tests for all six exact global
profiles and proof summaries. Add the complete negative matrix: wrong key,
raw/normalized source/define/name/ID/storage/type/writability/literal spelling
or value; zero/signed/suffix/hex/octal/unary/binary/cast/constructor/id
initializer; missing/extra/dependent global; float-profile drift; shadow,
write/update/escape; owner/read/span drift; literalized or wrong-ID loop bound;
wrong bound kind/trips/depth/product/charge; return in loop; recursion.

Explicitly test this identical four-mode algorithm against the semantic program
validator, generator validator, and emitter. “Pre-proof” means the canonical
pre-Task23 state after ordinary unseeded attachment, not a fully cleared tree.
Reconstruct that state from an accepted analyzer result for the two submitted
pre cases:

| Tree | Carrier | Expected |
| --- | --- | --- |
| canonical pre-Task23 | absent | rejected |
| canonical pre-Task23 | exact | pre tuple authenticates, but submitted-pre versus recomputed-post equality fails; rejected |
| exact post-proof | absent/wrong | rejected |
| exact post-proof | exact | ordinary reconstructed pre authenticates, reconstructed post equals submitted post, exact post hash/summary; accepted |

Also submit a fully cleared tree and a forged post tree whose forged proofs
disappear during reconstruction. Their ordinary pre tuple may authenticate, but
submitted/reconstructed post equality must fail;
an attacker-updated caller hash cannot change that result.

Then implement the authenticator, analyzer carrier, and proof seeding. Run only
semantic tests, review the diff and hashes, then continue.

### Step 2: RED generator and emitter tests

In `tests/test_typed_generator.py`, add the same four-mode matrix independently
for `validate_capabilities` and `render_typed_cpp`. Exercise capability
absent/wrong/extra/duplicate in the global vocabulary, carrier absent/wrong,
another key borrowing the carrier/profile, and a prior key with no carrier
while the global vocabulary includes the new item. Also exercise every
declaration/read/proof forgery and all four caller-hash states.
Assert existing float globals and every prior program remain byte-identical.

Then implement explicit driver propagation, capability/profile validation,
independent emitter authentication/reproof, and automatic int emission. Run
the focused generator tests before changing the slice.

### Step 3: slice and generation

Add only the six exact slice records. Run generator check expecting failure,
generate once, then immediately run `--check`. In production validation, check
explicit key lists, counts, list digests, exact positions/neighbors, corpus
source/function/whole/interface hashes, defines, no transform, and `glsl-f32`.
The external frozen oracle generator `--check` separately validates canonical
factory/runtime/public/no-adapter identity. Mechanically compare prior generated
blocks and inspect the six new blocks before continuing.

### Step 4: native ABI and oracle tests

In `tests/test_typed_slice.cpp`, add catalog/manifest/binding/resource tests and
generated shape assertions. In `tests/test_generated_kernels.cpp`, embed the
canonical C++ fixture records in the existing test style; add no JSON parser,
runtime dependency, CMake dependency, or generated fixture file. Use one
clearly delimited, machine-parseable initializer table. A Python test in the
already-owned `tests/test_typed_generator.py` reads the frozen JSON and
mechanically parses that C++ table, then compares every case name, key,
dimensions, tile/full resolution, uniform name/type/F32 bits, input and output
F32/RGBA8 hash, five probe coordinates and 30 lane words, metrics,
copy/divergence flags, and ordering field-for-field. It similarly compares the
complete mutation names/specifications and expected results used by the
temporary harness below. Fixture insertion may be script-assisted or
transcribed, but no manually changed expected value can pass without exact JSON
equality. The native executable itself is hermetic and consumes only embedded
fixtures.

Reproduce all 19 public-canonical cases with distribution 3 Bloom, 3
Directional, 3 Spin, 3 Strokes, 3 Vaseline, and 4 Wind. Each case checks full
F32 bytes and RGBA8, all five probes, finite lanes, input immutability, and two
fresh identical renders. Wind's tiny-positive normal-path case must be a
byte-exact output identity, but output identity alone is not path proof. Add
exact generated code-shape and binding-arithmetic assertions: the initial
texture fetch precedes the `amount <= 0` early-return guard; the fixture's tiny
positive amount makes that guard false; exact F32 evaluation gives reach
`0.64`; on loop iteration zero the computed distance is `1`; and the reach
break dominates the candidate texture fetch. This proves exactly one fetch on
the entered normal path. Use an existing counting-sampler seam if one already
exists; do not add a runtime seam for Task 23. Without one, structural ordering
plus exact binding/F32 arithmetic is the required evidence.

Reproduce all 12 mutations natively with this explicit in-scope harness in
`tests/test_typed_generator.py`:

1. Analyze each exact canonical program with the production profile and save
   its accepted typed tree and rendered namespace.
2. Apply each frozen mutation with a test-local structural `dataclasses.replace`
   helper. Each helper asserts exactly one intended typed node and exact
   before/after type, owner, span, operator/literal/callee identity. Prove first
   that production validation and production rendering reject every mutated
   tree; mutation execution is not a production admission path.
3. A test-only mutation renderer defined wholly in
   `tests/test_typed_generator.py` reuses the existing emitter's pure typed
   expression/statement rendering. After substituting the structurally mutated
   program, it mechanically rebuilds every rendering cache derived from that
   program's declarations/functions without invoking the production admission
   boundary: at minimum `source_globals`, source-global dependency closure,
   mutated-symbol sets, locals/function-name maps, and any function-shape cache
   consulted by rendering. This is essential for the four bound mutations;
   canonical declaration caches must not leak 64/32/24/128 into their temporary
   namespaces. For each namespace, assert the intended mutated literal or
   expression occurs exactly once at the frozen structural site and the
   canonical form occurs zero times there before compilation. The renderer
   emits twelve uniquely named temporary namespaces. It is not exported by
   production code, cannot write catalog/generated outputs, and cannot be
   called by `generate_typed_slice.py`.
4. Assemble the twelve namespaces and a small harness into one temporary
   multi-namespace C++ translation unit under a fresh temporary directory.
   Compile it once against the accepted local runtime headers/sources with the
   same compiler/ABI flags and explicit `-ffp-contract=off`; do not change
   CMake. The executable writes deterministic raw F32/RGBA8 result records for
   Python to hash and compare.
5. Run every JSON-named divergent and identity control and compare complete
   mutated F32/RGBA8 hashes and changed-lane/byte metrics field-for-field to the
   frozen JSON. Normal temporary-directory cleanup removes all code and binary
   output. Temporary mutation code is not a catalog/generated block and is
   explicitly excluded from isolation comparisons and installed artifacts.

The exact mutations are:

- Bloom bound 64->8; taps forced one;
- Directional bound 32->8; jitter disabled;
- Spin bound 32->8; jitter disabled;
- Strokes bound 24->8; MODE-0 selector forced to 135 degrees;
- Vaseline bound 32->8; edge mask forced zero;
- Wind bound 128->16; direction forced right.

Compilation alone is not discrimination. The test-local renderer is acceptable
only for this sensitivity harness because the same test proves production
validator/emitter rejection first and because no temporary byte enters the
repository, catalog, manifest, or installed library.

### Step 5: stack, disassembly, fetch, and isolation evidence

Configure fresh `/tmp` Debug, Release, and ASan/UBSan builds with
`-ffp-contract=off`, `-fstack-usage`, and `-fstack-size-section`. Preserve `.su`
records for `pixel` and all reachable helpers and calculate maximum non-inlined
chain sums for:

```text
Bloom:       pixel
Directional: pixel -> hash12
Spin:        pixel -> hash12 / rotateAround
Strokes:     pixel -> strokeVariation -> valueNoise2 -> hash12
             pixel -> brushStrokeField -> hash12 / hash22 / srcSample
             pixel -> smear -> srcSample
             pixel -> smear -> sprayJitter -> valueNoise2 -> hash12
Vaseline:    pixel -> clamp01 / chebyshev_mask
Wind:        pixel -> lum
```

The conservative Strokes `smear -> sprayJitter -> valueNoise2 -> hash12`
chain stays in the stack sum unless Release `MODE=0`, `jitterPx=0`
disassembly proves that branch and calls absent. Source reasoning alone cannot
remove it. Resolve every inlined/missing `.su` record with Release disassembly.
Reject dynamic/unbounded frames, allocation, VLA/`alloca`, recursion,
indirect/virtual calls, callbacks, exceptions, or fetches above the exact table.

### Step 6: complete verification and independent review

Run, on final bytes:

```sh
node docs/port-engineering/task-23-oracle-generator.mjs --check
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
```

Then build and run all CTest tests in fresh Debug and Release directories and
ASan/UBSan with leak checking and `halt_on_error=1`. Rerun every accepted Task
15-22 oracle/check command. Recompute all counts, identities, generated
isolation, stack/disassembly/fetch evidence, and an exact before/after hash
inventory for the twelve owned paths. Obtain independent review of the final
bytes and the completion report.

No Git operation is part of this design.

## 7. File-by-file scope

Only the following changes are contemplated:

| File | Bounded responsibility |
| --- | --- |
| `tools/glslcpp/frontend/loop_proof.py` | closed six-row authenticator; immutable global-bound seed support |
| `tools/glslcpp/frontend/semantic.py` | explicit carrier; authenticate declarations before proof attachment |
| `tools/glslcpp/generate_typed_slice.py` | capability/profile map, independent validation/reproof, driver propagation, frozen identities |
| `tools/glslcpp/emit_typed_cpp.py` | independent profile/global/proof validation and ordinary int automatic emission |
| `tools/glslcpp/typed_slice.json` | six exact entries only |
| `tests/test_semantic.py` | semantic/proof positive, negative, and four-mode matrices |
| `tests/test_typed_generator.py` | generator/emitter authorization, forgery, identity/isolation, JSON-to-C++ transcription audit, and temporary 12-mutation native harness |
| `tests/test_generated_kernels.cpp` | embedded 19-case canonical fixtures and deterministic/finite/immutable checks |
| `tests/test_typed_slice.cpp` | exact catalog, binder/resource ABI, shape, and generated isolation checks |
| `src/typed_generated/typed_slice.cpp` | deterministic generated output only |
| `src/typed_generated/typed_manifest.json` | deterministic generated output only |
| `include/noisemaker/generated/catalog.hpp` | deterministic generated output only |

Parser, `body_semantic.py`, typed IR, runtime, sampler, Surface, CMake, corpus,
adapters, and all other files remain untouched. Any necessary edit outside this
table is a scope failure requiring a revised brief and independent review.
