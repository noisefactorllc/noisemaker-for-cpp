# Task 28 independent design review

## Verdict

- **SPEC CONSISTENT: YES**
- **IMPLEMENTATION READY: YES**
- **Critical findings: 0**
- **Important findings: 0**
- **Minor findings: 0**
- **Blockers: none**

This review was read-only with respect to the repository and Git state. The
package admits exactly `filter/rotate:rot` under
`rotate-mat2-return-v1`: one authenticated `mat2 rotate2D(in float)` value
return, one four-scalar constructor, and its one immediate left-hand
`mat2 * vec2` use. It does not authorize a matrix parameter, returned matrix
local, second call, `mat3`/`mat4`, general matrix-return support, or a runtime
or emitter semantic expansion.

## Frozen-package integrity

Every Task 28 sidecar authenticates. Independently computed SHA-256 values are:

| Artifact | SHA-256 |
| --- | --- |
| `task-28-frontier-audit.md` | `972e8e1d89ed9260674a040b60d639aa6c321e675ce20447b4126e52653385a9` |
| `task-28-recompute.py` | `44f556acf1c8e812ae8a1085f041b1cf8af3f3152d55f1731b6c76d736d9e28a` |
| `task-28-recomputed.json` | `38bd8b45d48e8da06c8b1f3bcd3e3162bbc48d6619ae960a2319bbbca08ca267` |
| `task-28-oracle-generator.mjs` | `b3f5f1b25989cb10c94922b9a0b4612fab3d8f360df697e79318438d6486a17a` |
| `task-28-oracles.json` | `db74b7e1883c1d9f71ec00caa80451793c404039bfd26943be4844faaeef3b44` |
| `task-28-oracle-report.md` | `8eea0603b37673ec50531f1b1bfe895f257286e839f4a75b5ea43066c3559b0f` |
| `task-28-brief.md` | `57291c23f8c42145efa25cda83efeb962ef82bb53849242aa1585d9224d3dbcd` |
| `task-28-implementation-design-final.md` | `6791164c2d85c66fe1a6a843bd275cbcb9b6f5d5e5b36fb77c071ef6a50450a5` |
| `task-28-design-preflight-report.md` | `45eedffbf5ea8743b368d2c339619b1cfaa5af8eed798baae38e1e829b5df395` |

The advisory post-Task-27 frontier check also authenticates as
`e81c89cdba604ad6cdbb747bc22e36f75e818d7449a756c8899d4358bd0326f5`.
The four hard Task 27 authorities independently match the brief:
`c6abf725...`, `945f837a...`, `f7a2af82...`, and `fde73c3e...`.

Fresh execution of `task-28-recompute.py --check` reproduced the frozen JSON
and `node task-28-oracle-generator.mjs --check` passed. Current corpus and
canonical generation checks passed at the accepted 127-program baseline.

## Independent source, tree, interface, and catalog reconstruction

The independent recomputation reproduced the pinned corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`, raw source size/hash
1,197 / `c23e8462...`, normalized size/hash 964 / `e0e2b723...`, exact empty
defines, `glsl-f32`, two functions, the frozen function/whole/interface hashes,
and the complete ordered six-symbol interface. Resource closure is five
uniforms, one sampler, one output, texture use, no derivatives, and an empty
0/0/0/0/0/acyclic counted-loop proof.

The public CPU oracle independently authenticates `canonicalFactory127`,
factory-text hash `4dd2ffad...`, direct canonical/public object identity, and
no adapter. The accepted state is 212 corpus / 127 typed / 129 public / 83
unported with ordered hashes `ed2b5d24...` / `37e41894...`. Adding only Rotate
projects 128 / 130 / 82, typed ordinal 67 between Ridge and Scale, with hashes
`30f0333c...` / `102f5436...`.

Semantic traversal reproduced signature 10, parameter ID 8, local IDs 17/18,
the exact three-statement body, the sole constructor path/span/hash and ordered
children `c,-s,s,c`, the sole call path/span/hash, and its sole binary parent.
There are exactly two matrix-typed expressions program-wide, one matrix-return
function, no matrix parameter, and no second matrix call or escaped matrix
state. The exact profile tuple hashes to `2cfd54ec...`.

## Matrix orientation and value-return ABI

The proposed orientation is correct. `glsl::Mat<2>` stores two `Vec2` columns,
and its matrix-vector operator computes each row as
`matrix[column][row] * vector[column]`. Therefore the emitter's existing
lowering of `mat2(c,-s,s,c)` to columns `(c,-s)` and `(s,c)` is exactly the
canonical JavaScript `this[j*2+i] * v[j]` convention. It is not transposed or
row-major.

A fresh AppleClang C++20 warnings-as-errors compile of the isolated unmodified
emission succeeded. Release AArch64 inspection shows `rotate2D` with a fixed
32-byte frame and four scalar return lanes in `s0`-`s3`: `c,-s,s,c`. There is
no hidden result pointer, dynamic stack, heap call, indirect call, or exception
edge within that symbol. The projected pixel body inlines the one helper call;
its direct `sincos`/F32 conversion sequence is visible. This remains projection
evidence, and the plan correctly requires repeating it on canonical final code.

## Fail-closed authorization and negative closure

The profile/loader/validator/emitter split is coherent and narrow. The profile
recomputes identity and returns exact objects; the loader permits one carrier
on one row and forbids all combinations; the validator bypasses only the
blanket return-policy check for the exact helper object while retaining normal
type, parameter, statement, and expression traversal; and the emitter performs
its own authentication without adding a semantic matrix branch. Mandatory
carrier handling closes the current emitter's otherwise-generic ability to
spell this source.

The required at-least-45 single-axis matrix includes source, defines, numeric
mode, declarations/resources/interface, function identity/signature/body,
locals, constructor children and signs, return shape, call ownership and
cardinality, parent role/orientation, matrix escape/state, alternate matrix
types and operations, and every unrelated carrier. Requiring identical
candidate/precondition key sets, protected-coordinate equality, independent
profile/validator/emitter rejection, analyzer-derived alternatives where
possible, distinct candidate text, and both correct reconstruction and forged
old-object rejection is sufficient to expose accidental widening rather than
merely rechecking a monolithic hash.

## Non-vacuous native and oracle proof

The frozen public oracle has six non-square quadrant-marked cases, all three
wrap modes, stationary and both speed signs, immutable inputs, repeat identity,
finite outputs, exact F32/RGBA8 hashes, and five probes. Public mutations are
non-vacuous: transpose diverges in 5/6 images, changed child identity in 6/6,
diagonal in 5/6, and row-major multiplication in 5/6. The helper-local-return
control is deliberately value-identical and is rejected structurally.

All six direct modes have distinct IDs/names and an explicit return-shape
witness. Across the six frozen rows, transpose changes matrix lanes in 6 and
products in 5; row-major changes products in 5; diagonal changes lanes in 6
and products in 5; wrong-sine-sign changes lanes in 6 and products in 4. The
helper-local mode is value-identical in all rows but witness-distinct. The plan
requires six explicit switch arms using actual matrix operations, an invalid
enum throw, all 36 executions, and Python one-to-one parsing plus independent
tampering of every case/mode/witness/table field. That specifically prevents
fallthrough, fabricated witnesses, and output-inert controls from satisfying
the proof.

## Isolation and completion gates

The isolation contract starts from the actual post-Task-28 spec, removes only
Rotate, proves the 127-row precondition, and regenerates through the real
pipeline. It authenticates exact Task 27 artifacts (`aa15e469...`,
`f25401d4...`, `b82abfa0...`), compares all historical generated blocks after
only namespace-ordinal normalization, all prior manifest rows after only the
common monolithic hash exclusion, the exact catalog delta, and all 129 public
mappings. This is a real prior-state reconstruction, not a stale fixture.

Final requirements cover strict RED/GREEN evidence, exact public and direct
pixels, all binding omissions/wrong types, executable-table authentication,
full Python discovery, fresh Debug/Release CTest, ASan/UBSan, stack usage,
release disassembly, every prior Task 15-28 oracle, exact counts/order/hashes,
and independent implementation review. The owned-file allowlist excludes the
parser, typed IR, runtime, CMake, corpus, existing profiles, adapters, and Git
state.

## Correction contract

None. Implementation may proceed from the authenticated accepted Task 27
baseline. Any drift in the frozen source, typed tree, factory, oracle, baseline
hashes, owned-file allowlist, or proof package is a hard stop requiring a new
bounded review.
