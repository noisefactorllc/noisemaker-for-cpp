# Task 27 Perlin exact scalar uint XOR scope and proof brief

> **Status:** frozen read-only scope/proof contract. This file authorizes no
> repository edit and no Git operation.

## Goal and boundary

Add exactly `synth/perlin:perlin` under identity profile
`perlin-scalar-uint-xor-v1`. The profile admits exactly the two nested scalar
`uint ^ uint` rvalues in `hash3` under exact default define
`{"DIMENSIONS": 2}` and emits them as the ordinary left-associated C++20 word
expression `(a ^ b) ^ c` on `std::uint32_t` operands.

This is not a generic scalar-bitwise capability. It adds no runtime helper,
overload, signed-bitwise rule, mixed scalar/vector rule, or `DIMENSIONS=3`
profile. Existing `uvec3 ^= uvec3`, `uvec3 >> uint`, and
`glsl::bitwise_xor` behavior remain unchanged.

The two scalar sites are unreachable from the resolved default entrypoint.
Therefore Task 27 requires two independent proof tracks:

1. exact F32 and RGBA8 public render parity for the reachable
   `DIMENSIONS=2` program; and
2. exact typed-tree/code-shape authentication plus executable direct unsigned
   word tests for the otherwise-dead `hash3` expression.

Image equality is not evidence that either scalar XOR is correct.

## Hard accepted Task 26 gate

Implementation may start only from the accepted post-Task-26 tree:

| Measure | Required value |
| --- | ---: |
| Corpus programs | 212 |
| Typed programs | 126 |
| Public programs | 128 |
| Publicly unported | 84 |
| Smooth zero-based typed position | 77 |
| Typed ordered-key SHA-256 | `01b1dd9d0ec83e375275bc3928ee0f652d1495666616e5280e4b878a71b5db76` |
| Public ordered-key SHA-256 | `d46ed864c5ed1795201981b7fc4aeec8fd330caa54c09d890235e5023c91e6e3` |

Task 26 final implementation/review authorities are:

| Artifact | SHA-256 |
| --- | --- |
| `task-26-implementation-design-final.md` | `784e4f8588f51cca22167364e60f3e669246f8847706ce22233c40414c94e8b5` |
| `task-26-implementation-report.md` | `cf2b8e3756d7ab783c1bccdaf46efdd5e0b22f62c583f6e16cea96d0a2ccf531` |
| `task-26-mutation-fix-report.md` | `4b5f324f826d18ef87c02968011d7aeaae59a1e1f53daf7824e96de4121fe3f1` |
| `task-26-implementation-rereview.md` | `9fbc4bfb8f16da1507c467d44f6e29d6da934c1375e1f9ed9d8a5214cc2ac62a` |

Task 27 must not stack onto an in-flight or drifted Task 26 tree. At preflight,
rerun corpus/generator checks and a fresh warnings-as-errors Debug build/CTest.

Adding only Perlin projects:

| State | Typed | Public | Unported |
| --- | ---: | ---: | ---: |
| Accepted Task 26 | 126 | 128 | 84 |
| Exact Task 27 | **127** | **129** | **83** |

The projected newline-terminated sorted typed/public list SHA-256 values are
`ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72`
and `37e41894bc62b658a3454e13ab60fe814baf2492fa2a74b0f4305e05480a7883`.
Perlin is zero-based typed position 123:

```text
synth/pattern:pattern
synth/perlin:perlin
synth/polygon:shape
```

## Frozen audit and oracle artifacts

| Artifact | SHA-256 |
| --- | --- |
| `task-27-frontier-audit.md` | `da7ea68d62f05dc0710ab2aa2f0c825614625d1155f1aafdb4cbf5f6fdc07d8d` |
| `task-27-recompute.py` | `38d4124729dbfbcf2721f70542a05d4ac8060f48ce3304884d810eeb67da4287` |
| `task-27-recomputed.json` | `5273b52fe99259f7be1bc1e66513fb3d6731dc240873884c35780bedea3b5231` |
| `task-27-oracle-generator.mjs` | `95e9c5da0d0284f33ffcd0579c014ef29a7761785fed30d4047a75a1107dfd1e` |
| `task-27-oracles.json` | `27e12edfdec79a9f1ad9c07d3d076da2553e36f63d8c9a5ac43c1bc1592bcc54` |
| `task-27-oracle-report.md` | `9686b2107312f327ce898d438fe849b7bc7298158885d252210e76a72a3721b2` |

Run `node docs/port-engineering/task-27-oracle-generator.mjs
--check` before implementation and at every review gate. The pinned
`noisemaker-for-cpu` checkout is oracle provenance only and must not become a
native build/runtime/install/generator dependency.

## Exact source, public factory, program, and interface identity

| Field | Required value |
| --- | --- |
| Corpus revision | `a024dc3a960cc44af454abc7aebce50456c194e6` |
| Key/runtime key | `synth/perlin:perlin` |
| Source | `sources/synth/perlin/perlin.glsl` |
| Raw bytes / SHA-256 | 10,882 / `9580baa0f637b8b4f2488e6e26288d885fe748973a121f52281b63c16d530318` |
| Normalized bytes / SHA-256 | 4,875 / `88cb30dfb53c75f2d1bf51e9f9b865dca48ffb528e6ff2f77dec224dab309f64` |
| Exact defines | `{"DIMENSIONS": 2}` |
| Numeric contract | `glsl-f32` |
| Profile | `perlin-scalar-uint-xor-v1` |
| Canonical/public factory | exact same `canonicalFactory268` object |
| Factory text SHA-256 | `55ea0bb422438d8ed6182fc4f587395de5321dc8f8ca0588c0202f23732ca0f4` |
| Public adapter | absent |
| Function count / tuple SHA-256 | 13 / `3dbb088e9f6a0ae35d25a3ae197008f62bc7932f3a31697f2ce3fdb05c3e1abc` |
| Whole-program SHA-256 | `a47c9ae9ef983c68c6c867296aaa33401841e5a089dddf9842630c6453e775bc` |
| Interface SHA-256 | `b8ff41d2d2259908c8efa422227f27b89469110330908e8eb34410319e878066` |
| `hash3` signature/body SHA-256 | 49 / `3c3253eaa535ee944476a6c5d60bcb8e66212482d3e4b5af44db96d0e1dfcc50` |

The exact interface is fourteen uniforms and one output, in order:

```text
resolution:vec2@1
tileOffset:vec2@2
fullResolution:vec2@3
aspect:float@4
time:float@5
scale:float@6
seed:int@7
octaves:int@8
colorMode:int@9
ridges:int@10
warpIterations:int@11
warpScale:float@12
warpIntensity:float@13
speed:float@14
fragColor:vec4@15/out
```

There are no samplers, textures, derivatives, structs, uniform blocks,
varyings, arrays, matrix values, non-`in` parameters, or public adapters.

## Exact two-node typed-tree closure

The sole source expression is raw line 81 and normalized line 73:

```glsl
return float(q.x ^ q.y ^ q.z) / 4294967295.0;
```

Path grammar starts at `function.body[index]`, uses `eN` for statement
expression N, `0` as the expression-root sentinel, then child indices.

| Site | Path | Span | Expression SHA-256 | Parent/role |
| --- | --- | --- | --- | --- |
| Outer | `(10,'e0',0,0,0)` | `73:18-73:33` | `31049e8d38c4a6d26d051659ccd435fb7715906fb861440b7904429f3514495c` | child 0 of float constructor `73:12-73:34`, SHA `98f5cc12b9b7d44fefc28337f7d4a2d605eb455d2b36f39f3e80296114e57e2b` |
| Inner | `(10,'e0',0,0,0,0)` | `73:18-73:27` | `f51b3a1264df7050a8528a5094da6d16c464978d1cb5c8b680461c9173d195cc` | child 0 of outer XOR |

Both nodes are binary `^`, rvalue, result `uint`, with exactly two `uint`
children. Operand identities are:

| Operand | Span | SHA-256 |
| --- | --- | --- |
| `q.x` | `73:18-73:21` | `7a2954d83ebe2be4dfd2ca31558438ff5423668aa4bb593b349b489b7fc92023` |
| `q.y` | `73:24-73:27` | `d15d2568d9165294874cd3c76406e368a48b31c6834d2949d91f7ac4845a81cc` |
| `q.z` | `73:30-73:33` | `5387f564b5e3d096fd99fe10781613d0adab40bc86ebb50a00b79725118f7f08` |

There are exactly two scalar XOR nodes in the entire normalized program. The
existing vector compound-XOR and shift nodes are outside this profile.

The frozen profile tuple is:

```python
(
  'perlin-scalar-uint-xor-v1',
  'synth/perlin:perlin',
  '9580baa0f637b8b4f2488e6e26288d885fe748973a121f52281b63c16d530318',
  {'DIMENSIONS': 2},
  (49, 'hash3', (10, 'e0', 0, 0, 0), '73:18-73:33',
   '31049e8d38c4a6d26d051659ccd435fb7715906fb861440b7904429f3514495c',
   '98f5cc12b9b7d44fefc28337f7d4a2d605eb455d2b36f39f3e80296114e57e2b', 0),
  (49, 'hash3', (10, 'e0', 0, 0, 0, 0), '73:18-73:27',
   'f51b3a1264df7050a8528a5094da6d16c464978d1cb5c8b680461c9173d195cc',
   '31049e8d38c4a6d26d051659ccd435fb7715906fb861440b7904429f3514495c', 0),
  '3dbb088e9f6a0ae35d25a3ae197008f62bc7932f3a31697f2ce3fdb05c3e1abc',
  'a47c9ae9ef983c68c6c867296aaa33401841e5a089dddf9842630c6453e775bc',
  'b8ff41d2d2259908c8efa422227f27b89469110330908e8eb34410319e878066',
  (45, 46, 48, 50, 51, 52, 53, 54, 55, 56),
  (47, 49, 57),
)
```

Its SHA-256 under `sha256(repr(tuple).encode())` is
`bc712abd28da325cb3f3d162a6b542b9c28a7491564c44a90a6b090af39c0cbf`.
Caller-supplied hashes are drift alarms, not authority.

## Reachability and semantic choice

The exact default-entrypoint reachable function IDs are
`45,46,48,50,51,52,53,54,55,56`. Unreachable definitions are `grad3` 47,
`hash3` 49, and `wrapZ` 57. `grad3` contains exactly three static calls to
`hash3`; no reachable function calls it. Both loops are proved, with loop
count 2, unproved 0, effective depth 1, lexical product 8, entrypoint charge
28, and an acyclic call graph.

The public JavaScript factory uses signed Int32 bitwise semantics. The source
typed operands are unambiguously unsigned. Task 27 chooses source semantics:
direct `std::uint32_t ^ std::uint32_t`, then the existing float-constructor
boundary. This difference is safe only because `hash3` is dead for the exact
default profile. Task 27 must state that it does not prove `hash3` public-JS
behavior and cannot be reused for `DIMENSIONS=3`.

## Required generated spelling

The generated `hash3` return must contain exactly:

```cpp
return (static_cast<double>(float(
    ((glsl::swizzle<0>(q) ^ glsl::swizzle<1>(q)) ^
     glsl::swizzle<2>(q)))) /
    static_cast<double>(static_cast<float>(4294967295.0)));
```

Formatting may remain generator-native, but code-shape tests must prove two
direct `^` operators, left nesting, exact operands, unsigned operand/result
types, the unchanged float-constructor boundary, and no scalar helper call.

## Oracle and negative closure

The hermetic oracle contains eight exact public render cases, four mutated
factories whose default outputs remain byte-identical because `hash3` is dead,
and twelve direct unsigned word cases. Every native render must match full F32
and RGBA8 hashes and frozen probes exactly, repeat identically, remain finite,
and preserve exact dimensions.

The direct-word test must execute `(a ^ b) ^ c` on `std::uint32_t` for every
frozen triple and compare inner/result words, unsigned numerator F32 bits, and
ratio bits. High-bit rows must distinguish source-unsigned conversion from
canonical-JS signed conversion. OR/AND mutation tables must diverge somewhere;
right-associated XOR must be value-identical but structurally rejected.

Separate profile, validator, and emitter tests must reject every single-axis
mutation of key, source/raw/normalized hash, define name/value/order/count,
numeric mode, function tuple/body/signature/owner, interface/resource order,
site path/span/hash/operator/category/type, operand identity/type/order,
parent kind/hash/role, site cardinality, reachability partition, loop proof,
and any foreign/missing/combined carrier. They must also reject signed int,
mixed scalar/vector, an added third scalar site, a right-associated tree,
generic helper lowering, and `DIMENSIONS=3`.

## Verification and stop boundary

Required completion gates are: TDD RED/GREEN evidence; generator isolation;
all 8 public cases and 12 direct words; exact public ABI/binder failures;
warnings-as-errors Debug/Release; full Python discovery; CTest; ASan/UBSan;
stack-usage and release disassembly; all prior Task 15-26 oracle checks; exact
manifest/catalog/count/order/hash checks; and independent implementation
review with zero Critical/Important findings.

No parser, typed-IR schema, runtime header/source, CMake file, existing profile,
compatibility transform, numeric behavior, global/loop/array/matrix/sampler
support, corpus file, public adapter, or Git state may change.
