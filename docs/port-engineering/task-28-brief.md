# Task 28 Rotate exact `mat2` return scope and proof brief

> **Status:** frozen read-only scope/proof contract. This authorizes no Git or
> repository operation beyond the implementation explicitly described below.

## Goal

Add exactly `filter/rotate:rot` under identity profile
`rotate-mat2-return-v1`. Admit only signature 10 `rotate2D(in float) -> mat2`,
whose exact three-statement body returns `mat2(c, -s, s, c)`, and its sole
direct use as the left operand of `mat2 * vec2` in `main`.

This is not general matrix-return support. It adds no runtime type/operator,
matrix parameter, `mat3`/`mat4`, matrix state, returned matrix local, generic
capability, or second call. Existing `glsl::Mat2` column-major construction and
matrix-vector multiplication are reused unchanged.

## Hard accepted Task 27 gate

Implementation starts only from 212 corpus / 127 typed / 129 public / 83
unported, typed/public ordered hashes
`ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72`
and `37e41894bc62b658a3454e13ab60fe814baf2492fa2a74b0f4305e05480a7883`.
Accepted Task 27 authorities are the current files:

| Artifact | SHA-256 |
| --- | --- |
| implementation design | `c6abf725ad560cdee02de716df98fa977ab4cefcaafea07860ac7ee5cd8f1218` |
| implementation report | `945f837aeaf55c8413b602b4bcfecd948e34be5b661c7ed41392a832a77dc4c7` |
| review-fixes report | `f7a2af820025c27196fcd1083bc5d8ff2a083e0a4915ff88966487974bc7f985` |
| implementation re-review | `fde73c3ec58fdcdaa8573f9131f9ade64664610abc92a1da83b2a4a41b20df21` |

Adding only Rotate projects 128 typed / 130 public / 82 unported. Rotate is
typed ordinal 67 between Ridge and Scale. Projected typed/public hashes are
`30f0333cfd995ba1b866fcbd9589507151255204088675bae6575e42d7328c55`
and `102f5436a5416399f2601879c7d5219706111bc64b93989acbb67d973a01b6c5`.

## Frozen audit and oracle artifacts

| Artifact | SHA-256 |
| --- | --- |
| `task-28-frontier-audit.md` | `972e8e1d89ed9260674a040b60d639aa6c321e675ce20447b4126e52653385a9` |
| `task-28-recompute.py` | `44f556acf1c8e812ae8a1085f041b1cf8af3f3152d55f1731b6c76d736d9e28a` |
| `task-28-recomputed.json` | `38bd8b45d48e8da06c8b1f3bcd3e3162bbc48d6619ae960a2319bbbca08ca267` |
| `task-28-oracle-generator.mjs` | `b3f5f1b25989cb10c94922b9a0b4612fab3d8f360df697e79318438d6486a17a` |
| `task-28-oracles.json` | `db74b7e1883c1d9f71ec00caa80451793c404039bfd26943be4844faaeef3b44` |
| `task-28-oracle-report.md` | `8eea0603b37673ec50531f1b1bfe895f257286e839f4a75b5ea43066c3559b0f` |

Run both recomputation and oracle `--check` before the first RED and at review
gates. The pinned CPU checkout is oracle provenance only and must not become a
native build, runtime, install, or generation dependency.

## Exact identity and closure

- revision `a024dc3a960cc44af454abc7aebce50456c194e6`;
- source `sources/filter/rotate/rot.glsl`, 1,197 bytes,
  `c23e8462e8240f25a715fa3eb05e567269c8d410d27943ba346ebccdd0de1f8f`;
- normalized 964 bytes,
  `e0e2b723289b08cbfcd6f1fc0a8481869e674de3cfedc0ec5df6d96f64748bb5`;
- exact defines `{}`, `glsl-f32`, two functions, function tuple
  `f5b9f47764c12f05a55925aaca0cf99027ef0b78f67d0122df657f068ba23d56`,
  whole program `3e4312d4c94a8d8b207aa351f8974f417cb5acd63d45a70b1f4a8e606ed2e1b6`,
  interface `bfdeb36f89cb3dd84ec4339564e5d830f0f18c9f011d4b563f3cca45973e28df`;
- exact direct public `canonicalFactory127`, factory-text SHA-256
  `4dd2ffadbcf25ec3f88c090b014da6cd3ee7faa3ddea970f21714c873dfcf903`,
  no adapter;
- exact bindings `inputTex:sampler2D@1/S1`, `rotation:float@2`, `wrap:int@3`,
  `speed:int@4`, `time:float@5`, `fragColor:vec4@6/out`;
- signature 10 `rotate2D(in float angle ID 8) -> mat2`, exact signature/body
  hashes `a04f91...` / `f88f63...`, span `14:1-18:2`, three statements;
- locals ID 17 `c=cos(angle)` and ID 18 `s=sin(angle)` only;
- sole matrix constructor path `(2,'e0',0)`, span `17:12-17:29`, SHA
  `e663648e5aadc5bbaf20fe171459a9a64e2deb713a46665e63e3a6c08d416796`,
  exact ordered children `c`, `-s`, `s`, `c`;
- sole call path `(8,'e0',0,1,0)`, span `35:10-35:40`, SHA
  `5328e90c21b68b353d8c9ab9caf2a1f3ba59d9de557d72729978670f851ff1b1`;
- sole matrix-vector parent path `(8,'e0',0,1)`, span `35:10-35:45`, SHA
  `4e166653131410b87db5123dfe23746cd54e3096b4728e7ea22cd908607d766f`,
  operator `*`, exact children `mat2, vec2`, call at child 0;
- exactly two matrix expressions program-wide, no matrix parameter, and exact
  profile tuple SHA-256
  `2cfd54eca913518997b359a75e179eb45a323bf50c635b8d2d70874a1dfec76c`.

## Fail-closed implementation contract

Create one profile module exposing `PROFILE`, `ROTATE_KEY`,
`authenticate_rotate_mat2_return(program, source_hash, profile)` and identity
`apply_rotate_mat2_return(...)`. Authentication independently recomputes every
identity above and returns the exact helper, constructor, call, and parent
objects. No registry, generic matrix capability, proof field, or IR schema
change is permitted.

Add exactly one sorted slice row:

```json
{"defines": {}, "program_key": "filter/rotate:rot", "rotate_mat2_return_profile": "rotate-mat2-return-v1"}
```

The loader requires exactly one carrier on exactly Rotate, forbids Rotate
without it, forbids it on any other key, and forbids coexistence with every
other per-program carrier. Pipeline order appends this identity step after
Perlin, then validator and emitter independently authenticate it.

The validator adds only keyword-only `rotate_mat2_return_profile`. It retains
the authenticated objects and bypasses the blanket matrix-return rejection
only when the visited function object is the exact helper. All function body
and expression traversal remains active. Completion requires exactly one
visit to the helper return, constructor, call, and matrix-vector parent.

The emitter adds the same keyword-only carrier solely for independent
authentication/mandatory-carrier closure. Existing code generation is used
unchanged and must spell `glsl::Mat2` by value, exact two `glsl::Vec2` columns
`(c,-s)` / `(s,c)`, and one direct `rotate2D(...) * uv`. No emitter semantic
branch or runtime change is needed unless a failing test proves otherwise.

Required carrier matrix:

| Tree | Carrier | Validator | Emitter |
| --- | --- | --- | --- |
| exact Rotate | exact | accept | accept |
| exact Rotate | absent/foreign | reject | reject |
| foreign or single-axis-mutated | exact | reject | reject |
| foreign | absent | retain prior result; never gain matrix return |
| exact Rotate | any combined carrier | reject | reject |

## Proof matrix

Every negative is a named unequal single-axis candidate with a precondition
showing exactly that coordinate changed. Pass it separately to profile,
validator, and emitter. Cover key/path/raw/normalized/caller hash, define
name/value/order/count, numeric mode, declaration/resource/interface
name/type/storage/binding/order, function count/order/ID/name/return/signature/
parameter direction/body/span, local symbol/type/storage/initializer,
constructor path/span/kind/type/arity/order/each child/operator/symbol,
return-statement shape, matrix-return cardinality, call owner/path/span/hash/
signature/argument/cardinality, parent path/operator/type/order/role,
returned-local/state escape, overload/prototype/recursion, `mat3`/`mat4`,
matrix parameter/index/arithmetic, second call, vector-matrix/matrix-matrix,
and every unrelated carrier. Candidate names and precondition names must have
identical exhaustive key sets; require at least 45 candidates.

Use analyzer-produced alternatives when source changes can express the axis;
otherwise use `dataclasses.replace`. Value-equal reconstructed trees must
authenticate their own new objects; forged authorization retaining objects
from the original tree must fail validator and emitter.

## Pixel, direct-value, table, ABI, and isolation proof

Transcribe all six frozen public cases exactly. Bind the texture plus four
ordinary uniforms; for every case assert width/height first, immutable input,
repeat-identical full F32 bytes, exact F32/RGBA8 hashes and five probes, finite
lane count, and direct-binder/public-catalog identity. Remove each binding and
supply each wrong variant independently; both must throw.

Execute all six direct modes for all six frozen angle/vector rows. Each
explicit switch arm must construct/use a genuinely distinct form and record
numeric ID, exact name, return-shape witness, four matrix-lane bits, and two
product bits. `default` throws. Exact direct-return and helper-local-return
must be value-identical but witness-distinct; every incorrect value/layout mode
must diverge. Python parses all executable case/mode fields one-to-one and
independently tampers each while the oracle JSON is unchanged.

Generated isolation starts from the actual post-Task-28 spec, removes only
Rotate, proves 127 exact remaining rows, and regenerates through the real
pipeline. It must reproduce Task 27 generated SHA-256 values:

```text
typed_slice.cpp       aa15e469d2283ac4f919a3f61edf85f5046f414674ff3cebdb85e5c06d2327c5
typed_manifest.json   f25401d49121ad6dcda189730b6e99ca5946fb0fafd2fbac83c637740ea1cd58
catalog.hpp           b82abfa09c224185a4152d487d290d9b6bc475bb15ae744ddc3550c86ded1da5
```

Compare all 127 historical blocks after normalizing only namespace ordinal,
all historical manifest rows after excluding only the common monolithic
output hash, and all 129 historical public mappings exactly. Prove the only
new block/row/declaration/catalog mapping belongs to Rotate and only it owns
the carrier.

Final gates: TDD RED/GREEN; exact oracle `--check`; full Python discovery;
fresh warnings-as-errors Debug/Release builds and CTest; ASan/UBSan with the
documented Apple leak-detection retry only if necessary; stack usage for
`rotate2D`, `pixel`, and maximum helper; release disassembly proving direct
four-float by-value return, fixed stack, one direct helper call, no sret
pointer/heap/indirect call; all prior Task 15-28 oracle checks; exact catalog/
count/order/hash; independent implementation review with zero Critical or
Important findings.

No parser, typed IR, runtime header/source, CMake, corpus, existing profile,
public adapter, compatibility transform, or Git state may change.
