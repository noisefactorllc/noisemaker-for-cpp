# Task 27 independent design review

## Verdict

- **SPEC CONSISTENT: YES**
- **IMPLEMENTATION READY: YES**
- **Critical findings: 0**
- **Important findings: 0**
- **Minor findings: 0**
- **Blockers: none**

This review is read-only with respect to the repository and Git state. Task 27
is correctly bounded to `synth/perlin:perlin` under
`perlin-scalar-uint-xor-v1`, and only to the two authenticated scalar
`uint ^ uint` rvalues in the unreachable default-profile `hash3` definition.
It does not authorize generic scalar bitwise support, signed or mixed bitwise
semantics, another program, or `DIMENSIONS=3`.

## Frozen-package integrity

Every sidecar verifies from `docs/port-engineering`. Independently
computed artifact digests agree with the package:

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
| `task-27-design-preflight-report.md` | `9c3545bdd79d3c6aac0f82403848df4f0e0fb6441d3205287e0f144abf8b870c` |

Fresh execution of `task-27-recompute.py` produced a byte-identical JSON file.
Fresh `node task-27-oracle-generator.mjs --check` passed. Current
`check_corpus.py --check` and `generate_typed_slice.py --check` passed at 126
typed programs.

## Independently reproduced source and catalog evidence

- Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`.
- Raw source: 10,882 bytes,
  `9580baa0f637b8b4f2488e6e26288d885fe748973a121f52281b63c16d530318`.
- Normalized source: 4,875 bytes,
  `88cb30dfb53c75f2d1bf51e9f9b865dca48ffb528e6ff2f77dec224dab309f64`.
- Defines: exactly the one typed preprocessor define `DIMENSIONS=2`.
- Functions: 13, with frozen tuple hash
  `3dbb088e9f6a0ae35d25a3ae197008f62bc7932f3a31697f2ce3fdb05c3e1abc`.
- Declarations: the fourteen ordered uniforms, output 15, and only `TAU` 16
  plus `Z_PERIOD` 17.
- Resources: fourteen uniforms, one output, no samplers, no texture use, and no
  derivatives.
- Current validator and emitter independently stop first at the outer scalar
  XOR at normalized `73:18`; changing only the two diagnostic operators exposes
  no later blocker.
- Public and canonical factory are the same `canonicalFactory268` object; its
  text hash is
  `55ea0bb422438d8ed6182fc4f587395de5321dc8f8ca0588c0202f23732ca0f4`,
  and there is no adapter.

The current 126-key typed list hash is
`01b1dd9d0ec83e375275bc3928ee0f652d1495666616e5280e4b878a71b5db76`.
Inserting only Perlin yields 127 keys, places it at zero-based ordinal 123
between Pattern and Polygon, and yields
`ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72`.
Adding the two existing manual public entries yields 129 public keys and
`37e41894bc62b658a3454e13ab60fe814baf2492fa2a74b0f4305e05480a7883`.

## Typed-tree and reachability closure

Independent semantic traversal found exactly two scalar binary `^` nodes in
the normalized program. Both are `uint/uint -> uint`, both belong to signature
49 `hash3`, and their left-nested paths, spans, expression hashes, operand
hashes, and parent roles agree with the brief. The existing vector `^=` and
`>>` operations are distinct and remain outside this profile.

The reachable signature IDs are exactly
`45,46,48,50,51,52,53,54,55,56`. Signatures 47 (`grad3`), 49 (`hash3`), and
57 (`wrapZ`) are unreachable. `grad3` has exactly three direct calls to
`hash3`; no reachable function calls it. The frozen counted-loop record
2/0/1/8/28/acyclic is reproduced. Consequently, the eight image cases can
prove only the reachable default program, while the typed-tree/code-shape and
direct-word tracks are necessary for the two dead nodes. The design maintains
that separation and never treats output-identical mutations as scalar-XOR
semantic evidence.

## Unsigned, signed-JavaScript, and denominator audit

The package describes the semantic distinction correctly:

- GLSL types all three operands and the result as `uint`, so the selected
  native definition is left-associated `std::uint32_t` XOR followed by
  unsigned-to-binary32 conversion.
- JavaScript bitwise operators first produce a signed Int32 result. That is a
  genuinely different numerator for high-bit words and is explicitly not
  claimed as Task 27 behavior or as authority for a future 3D profile.
- The GLSL denominator lexeme is `4294967295.0`. Under the `glsl-f32`
  contract, `static_cast<float>(4294967295.0)` is exactly 4294967296 with bits
  `0x4f800000`, matching the canonical JavaScript spelling `4294967296`.
  The generated spelling, direct-word oracle, and report are therefore
  consistent rather than off by one.

The twelve frozen word rows include eight signed/unsigned numerator
discriminators. Mutation divergence is non-vacuous: outer OR diverges in 5
rows, inner OR in 5, outer AND in 11, and inner AND in 11. Right-associated XOR
is value-identical in all rows, as required, while the authenticated tree and
mode witness provide the structural rejection.

## Test and implementation closure

The design explicitly prevents the Task 26 vacuous-mutation failure: all six
native evaluator modes require separate switch arms, an invalid enum must
throw, witnesses must record the executed arm/intermediate/result/association,
and Python transcription tests must parse and tamper the C++ mode/table data.
The implementation review must reject any arm that falls through to baseline
or any witness synthesized without executing the named mode.

Profile, loader, validator, and emitter responsibilities are independently
specified. Exact object-identity admission, mandatory-carrier rejection,
post-traversal exactly-once accounting, combined-carrier rejection, foreign
tree rejection, and historical-block isolation prevent the profile from
widening the existing scalar/vector operator surface.

Required completion gates cover TDD RED/GREEN evidence, eight exact public
F32/RGBA8 cases, twelve direct words, all binding omissions and wrong types,
fresh warnings-as-errors Debug/Release builds, full Python discovery, CTest,
ASan/UBSan, stack ceilings, release disassembly (`eor`, then `ucvtf`), every
prior Task 15-26 oracle, generated count/order/hash/isolation, and independent
implementation review. The nine-file owned allowlist is sufficient and does
not authorize runtime, parser, IR, CMake, corpus, documentation, Git, or public
state changes.

## Correction contract

None. Implementation may proceed from the exact accepted Task 26 baseline.
Any baseline, source, factory, typed-tree, define, oracle, count/order/hash, or
owned-file drift is a hard stop requiring a refreshed bounded package.
