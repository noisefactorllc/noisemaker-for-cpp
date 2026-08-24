# Task 27 Design Preflight Report

## Result

**DESIGN COMPLETE; IMPLEMENTATION READY. No blocker.**

The frozen package adds exactly `synth/perlin:perlin` under
`perlin-scalar-uint-xor-v1`. It authorizes only the two nested scalar
`uint ^ uint` nodes in unreachable default-profile helper `hash3`, using
source-typed `std::uint32_t` semantics. It does not authorize generic scalar
bitwise operations or `DIMENSIONS=3`. No repository file or Git state was
changed during design.

## Independently refreshed baseline

Current accepted state was recomputed from repository files:

| Measure | Current | Projected after only Task 27 |
| --- | ---: | ---: |
| Corpus | 212 | 212 |
| Typed | 126 | 127 |
| Public | 128 | 129 |
| Unported | 84 | 83 |
| Typed ordered SHA-256 | `01b1dd9d0ec83e375275bc3928ee0f652d1495666616e5280e4b878a71b5db76` | `ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72` |
| Public ordered SHA-256 | `d46ed864c5ed1795201981b7fc4aeec8fd330caa54c09d890235e5023c91e6e3` | `37e41894bc62b658a3454e13ab60fe814baf2492fa2a74b0f4305e05480a7883` |

Perlin's projected zero-based typed position is 123, between Pattern and
Polygon. The refreshed recomputation was byte-identical to
`task-27-recomputed.json` (`5273b52f...`).

Read-only baseline gates passed:

```text
python3 tools/glslcpp/check_corpus.py --check
check_corpus: ok

python3 tools/glslcpp/generate_typed_slice.py --check
exit 0

fresh AppleClang 16 Debug configure/build with warnings-as-errors
CTest 1/1 passed in 2.22 seconds
```

Task 26's oracle generator also passed `--check`; its final fix/rereview hashes
matched the accepted artifacts.

## Exact source/tree/public evidence

Fresh parsing and semantic analysis reproduced:

- raw source 10,882 bytes,
  `9580baa0f637b8b4f2488e6e26288d885fe748973a121f52281b63c16d530318`;
- normalized source 4,875 bytes,
  `88cb30dfb53c75f2d1bf51e9f9b865dca48ffb528e6ff2f77dec224dab309f64`;
- exact `DIMENSIONS=2`, 13 functions, function tuple
  `3dbb088e...`, whole program `a47c9ae9...`, interface `b8ff41d2...`;
- exactly two scalar `uint ^ uint` nodes, both in signature 49 `hash3`, at
  `(10,'e0',0,0,0)` and `(10,'e0',0,0,0,0)`, with the frozen hashes and
  parent roles in the brief;
- reachable IDs `45,46,48,50,51,52,53,54,55,56`; unreachable IDs
  `47,49,57`; exactly three static `grad3 -> hash3` calls and no reachable
  call; exact loop proof 2/0/1/8/28/acyclic;
- current validator and emitter both first reject the outer site at
  `73:18` as unsupported scalar `^`; a diagnostic tree changing only those
  two operators exposed no later blocker;
- exact direct-public identity `canonicalFactory268`, factory-text SHA-256
  `55ea0bb4...`, and no adapter.

The proposed frozen profile-tuple SHA-256 independently recomputed as
`bc712abd28da325cb3f3d162a6b542b9c28a7491564c44a90a6b090af39c0cbf`.

## Oracle evidence

`node task-27-oracle-generator.mjs --check` passed. The oracle freezes:

- 8 repeat-identical finite default-profile public render cases with exact
  F32/RGBA8 hashes and five probes each;
- 4 structurally changed scalar-expression factories, all byte-identical on
  all 8 cases, proving the sites are unreachable rather than correct;
- 12 direct unsigned-word cases, including high-bit rows that discriminate
  source-unsigned from canonical-JS signed conversion;
- OR/AND mutation divergence and right-associated XOR value-identity controls;
- explicit negative closure for foreign sites/types/operators/defines and
  `DIMENSIONS=3`.

All Task 15 through Task 27 oracle generators passed their current `--check`
commands.

## Projection-only build evidence

A diagnostic exact-source projection was compiled outside the repository with
C++20, warnings-as-errors, `-ffp-contract=off`, and direct nested word XOR. It
confirmed the frozen generated spelling and no additional emitter blocker.
Observed stack planning values were 576/64 bytes for `hash3` and 608/96 bytes
for `pixel` in Debug/Release. Release AArch64 disassembly contained exactly the
two terminal scalar `eor` instructions followed by `ucvtf`, distinguishing
unsigned conversion. These observations are sizing/preflight only; the design
requires fresh measurements on final generated code.

## Frozen files and baseline hashes

| Artifact | SHA-256 |
| --- | --- |
| `task-27-frontier-audit.md` | `da7ea68d62f05dc0710ab2aa2f0c825614625d1155f1aafdb4cbf5f6fdc07d8d` |
| `task-27-recompute.py` | `38d4124729dbfbcf2721f70542a05d4ac8060f48ce3304884d810eeb67da4287` |
| `task-27-recomputed.json` | `5273b52fe99259f7be1bc1e66513fb3d6731dc240873884c35780bedea3b5231` |
| `task-27-brief.md` | `cb63edbc129eaab3c963ac333b2079c15db4fee019564427173114dca1806c54` |
| `task-27-oracle-generator.mjs` | `95e9c5da0d0284f33ffcd0579c014ef29a7761785fed30d4047a75a1107dfd1e` |
| `task-27-oracles.json` | `27e12edfdec79a9f1ad9c07d3d076da2553e36f63d8c9a5ac43c1bc1592bcc54` |
| `task-27-oracle-report.md` | `9686b2107312f327ce898d438fe849b7bc7298158885d252210e76a72a3721b2` |
| `task-27-implementation-design-final.md` | `c6abf725ad560cdee02de716df98fa977ab4cefcaafea07860ac7ee5cd8f1218` |

Relevant accepted repository baselines:

| File | SHA-256 |
| --- | --- |
| `tools/glslcpp/generate_typed_slice.py` | `04914609adcef2c1f5b5ffcdae322ebad66fbad0c418b83a306b2707addb29a1` |
| `tools/glslcpp/emit_typed_cpp.py` | `11fc8432478ec887562c873062fdb60a026b8878164db5c1240fcda65fa29cf5` |
| `tools/glslcpp/typed_slice.json` | `a717f8d076dc3b921c657340eb81ab0313d275cd2cf911c467c568696cb88935` |
| `tests/test_typed_generator.py` | `fa87e65b014415e8eda4ccc86b45ed0b301b5f3c77fe3d9eac3d4ef66ee25765` |
| `tests/test_generated_kernels.cpp` | `cc86c7d7e9ac23548e3a7679bcd06618e4f29a179b9ef37e7aab4796bfa24b52` |
| `tests/test_typed_slice.cpp` | `55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6` |
| `src/typed_generated/typed_slice.cpp` | `df4aa212f312dcaf12bc348df1b1449a25db52542c97d0bc0350a7a2162b2d38` |
| `src/typed_generated/typed_manifest.json` | `e7f7acd56c96951d5610276cb72ad2df19637f142ae08022b92c2c718a7e7def` |
| `include/noisemaker/generated/catalog.hpp` | `557ccdbee5a58ff6129269ad4a4dfdc25486b8a9f8c455da2bf2c8663d55527d` |
| `include/noisemaker/glsl_types.hpp` | `37e71f566d5b8d5e1abf68fee1b27338898e4afacb116764824274dfda6780d8` |
| `CMakeLists.txt` | `bca6b4ab77d26c72449ef8d7a66d5832fdc939ebb35a85211b7684dde62216d5` |

## Implementation gate

Rerun every baseline/hash/oracle gate immediately before the first RED. The
owned-file allowlist and full TDD/negative/native/sanitizer/stack/disassembly/
prior-oracle sequence are frozen in the implementation design. No known
blocker remains.
