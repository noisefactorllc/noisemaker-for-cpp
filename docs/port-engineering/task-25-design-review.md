# Task 25 implementation-design independent review

Date: 2026-08-11

## Verdict

**APPROVED.** I found no material correctness, scope, proof-authority,
testability, or completion-gate defect in Task 25 implementation design
SHA-256
`9900749a387a30c6f1db0e584d2382288d44c2f3b0d5670f3b1968f1312c357b`.
It faithfully implements the approved amended brief
`193523a6e94642c7c1b6c4da86b08de8616d0d15a3edc0b3257e068ac930ddd2`
and is sufficiently bounded to execute. This review authorizes no repository
edit or Git operation by itself.

## Authority split and implementation viability

The design preserves the amended contract's essential separation:

- `authenticate_*_pre` proves the exact pre-index value and returns the exact
  ordered pre-site objects.
- `apply_*` performs one authenticated walk and replaces all 8/3 sites with
  fixed swizzles.
- `authenticate_*_transition` is the only layer that claims Python object
  lineage; while pre and post coexist it requires each replacement base to be
  the original base by `is` identity and rejects a cloned base.
- `authenticate_*_post` proves only observable value structure. Direct
  validator and emitter calls accept an exact dataclass-equal reconstruction
  and never claim post-only lineage.

No registry, side table, token, proof dataclass, typed-IR field, or runtime
helper is introduced. The proposed module boundary is viable with the current
frozen `TypedProgram`/`TypedExpression` model. The current validator and
emitter already accept explicit keyword metadata, already emit fixed
`glsl::swizzle<I>`/`glsl::set_swizzle<I>` routes, and can take the one new
profile keyword/cache without changing parser, semantics, IR, runtime, or
CMake.

The selected-key fail-closed rules are correctly present in both layers:
pre-index values cannot pass ordinary validation, selected post-swizzle values
without the exact carrier reject even though generic swizzles are otherwise
approved, and exact-carrier pre values reject direct post authentication.
Within an emitter invocation, identity is used only to locate nodes already
authenticated by post value, which does not reintroduce the superseded lineage
claim.

## Exact carrier and eleven-site transform

The design's site table is field-for-field identical to the approved brief and
brief review: 11 rows, Lens 8 and Prismatic 3, six direct plain-`=` writes,
five reads, and lane incidence `7 / 3 / 1`. All paths, normalized spans, lanes,
roles, and 11 pre/post expression SHA-256 values match. The complete pre census
must contain exactly those index nodes and no unselected index; the post census
must contain none.

The frozen identities also match: Lens/Prismatic raw and normalized bytes and
hashes, main IDs/body counts and pre/post hashes, function-tuple and
whole-program hashes, unchanged interface hashes, diagnostic C++ hashes, and
profile-tuple hashes. The proposed transform changes only `kind`, `children`,
and `member`; preserves each base identity during transition; keeps every
non-main function equal and identical; rejects partial, duplicate, twelfth,
reordered, and repeat application; and does not add a generic or dynamic index
capability.

The emitter ownership is exact. The four Lens writes and two Prismatic writes
use fixed `set_swizzle<I>`; the four Lens reads and one Prismatic read use fixed
`swizzle<I>`. The Lens scalar-to-vec3 splat remains one authenticated source
read. Read-as-write, write-as-read, compound/update, wrong member/lane, and
runtime lane routing all reject.

## Loader, validator, emitter, and forgery coverage

The loader adds the carrier only to the two sorted `{}` records, retains
Gather's independent carrier, requires exactly two selected records and 125
unique sorted programs, and keeps all global vocabularies/maps unchanged. The
carrier is intentionally absent from typed IR and the generated manifest.

The four-mode matrix matches the amended brief exactly. The design requires
literal carrier-by-caller-hash Cartesian coverage for exact controls and every
forged pre/post value at application, validator, and emitter boundaries, with
patched-analyzer driver tests preventing one accepting layer from laundering a
forgery into the next. It correctly confines the cloned-base negative to the
transition boundary and requires post-only dataclass-equal acceptance.

The negative inventory covers all required identity, source, function,
interface, resource, proof, path, parent, role, type, storage, writability,
index, control-flow, recursion, allocation, exception, callback, indirect
call, dynamic-stack, capability, Grade-LUT, and loader-schema variants. Real
parser/semantic fixtures with nearby accepted controls are required rather
than comment-label simulations. Existing `object.__new__` emitter tests and
the temporary Task 25 bypass must initialize every cache explicitly.

Implementation precision note: in each test-only wrong-lane emitter, the
authorization tuple must be rebuilt from the mutated member so its lane is the
frozen wrong lane. This is the natural meaning of the design's requirement to
initialize the lane-profile cache from the mutated program and is necessary
for the native candidate to execute the intended mutation.

## Canonical/native, isolation, ABI, and resource gates

The native plan is hermetic and field-complete. A machine-parseable table is
compared against the pinned JSON for all six canonical public-factory cases
and eleven mutations, including order, dimensions, tile/full resolution,
uniform bits, input/output hashes and five probes, finiteness, repeat,
immutability, candidate hashes, changed bytes/lanes, maximum differences, and
generated-occurrence counts. Production validator/emitter rejection precedes
every test-only mutation execution. Canonical and all eleven uniquely named
wrong namespaces compile once in a fresh temporary directory, while inactive
Lens branch cases must remain exact.

The projection and generated-isolation contract is complete: exactly
`125 typed / 127 public / 85 publicly unported / 212 corpus`, typed/public
list hashes `9b8f9475...cdbd4` and `9d773dde...deaab`, Lens/Gather/Prismatic
positions `2 / 52 / 59`, exactly two blocks/manifest rows/catalog rows/header
declarations, and all 123 Task 24 blocks unchanged after namespace-ordinal
normalization. Grade LUT and an adjacent unported control remain absent.

The explicit ABI/resource plan matches the brief: Lens has one sampler,
twenty ordinary uniforms, one output, three straight-line samples, no
texture-size call, loops, or derivatives; Prismatic has one sampler, ten
ordinary uniforms, one output, three samples, exactly one
`textureSize(inputTex,0)`, no loops, and no derivatives. Complete binding
tuples, missing/wrong fields, allowed extras, source/typed/generated resource
shape, fetch mutations, zero generated `main`, and forbidden code routes are
all tested.

## Stack, disassembly, and completion gates

The design requires fresh Debug, Release, and ASan/UBSan full CTest runs,
Python discovery, current generator/corpus/semantic checks, Task 15-25 oracle
checks, and focused native tests. It preserves `.su` records for both pixels
and every reachable helper, calculates maximum non-inlined chain sums below
16 KiB, distinguishes sanitizer instrumentation from production static
proof, and resolves inlining through Release disassembly.

Scoped disassembly must establish fixed lane loads/stores, exact sample and
texture-size behavior, direct acyclic helper calls, and absence of runtime
lane branches/subscripts, indirect branches, allocation, exceptions, VLA,
`alloca`, recursion, or dynamic stack. The final report must include exact
owned-file hashes and independent review. Generator success alone is
explicitly insufficient.

## Review checks

- Read all 662 lines of the design and compared every section against the
  amended brief and approved brief review.
- Re-hashed the design, brief, and brief review on the reviewed bytes.
- Mechanically parsed the design and review site tables: 11/11 rows identical,
  roles `6 write / 5 read`, lanes `7 / 3 / 1`.
- Inspected current `load_slice`, `generate_outputs`, `validate_capabilities`,
  `_Emitter`, swizzle/lvalue emission, and `render_typed_cpp` interfaces to
  confirm the proposed plumbing and fixed-swizzle route are implementable in
  the authorized files.
- Reconfirmed the accepted Task 24 owned-file baseline and that the new profile
  module is absent before implementation.

No repository file was changed and no Git operation was used for this review.
