# parallax190 — acceptance record

`filter/parallax:parallax`, typed row 190, namespace `typed_80`, sorted index
80 — the counted-for ladder's first landing (source-global literal-int seed
`MARCH_STEPS = 32` plus the textureLod identity admission
`texture-lod-admission-parallax-v1`).

**This record is written after the fact.** The row landed on 2026-08-18 at
"focused level" — admitted, gated, assembly-clean, and **wrong**. It had no
oracle package, and the defect it was hiding is the one an oracle package
exists to catch. What follows is the acceptance the row should have had, plus
an honest account of what shipping without one cost.

## What was wrong

`DEFECTS-FOUND.md` item 6, in one paragraph: the authority's
`var prevUV = rayUV` binds a **reference** to a single
`PooledFloat32Array`, and the march writes `rayUV` in place, so the
refinement `mix(rayUV, prevUV, w)` is `mix(x, x, w) == x` — a no-op. The
emitter wrote `glsl::Vec2 prevUV = rayUV;`, a value copy, and performed the
interpolation the GLSL describes. The port ran code the authority does not.

The trap is the one this project has hit more than any other: **the parity
target is the transpiler's materialization, not GLSL semantics.**

Measured at 4x5 over an 11x9 input, `direction = (-0.8, 0.4, 0.2)`,
`pivot = 0`:

| | textureLod calls | pixels where the final `getInput` coord equals the last `getHeight` coord |
| --- | ---: | ---: |
| JavaScript authority | 309 | **20 / 20** |
| emitted `typed_80` (before) | 309 | **0 / 20** |

Every march coordinate was already bit-identical. Only the post-refinement
coordinate differed — on every pixel — and two of twenty changed colour.

## The fix

`emit_typed_cpp.py` models the alias. A `vec2`/`vec3`/`vec4` declaration
whose initializer is a bare vector identifier emits `TYPE& name = source;`
when a write to either name makes the aliasing observable; where neither is
written, copy and alias are indistinguishable and nothing changes. The
analysis is re-derived from the live program on every run and is never frozen.

Scope is deliberately narrower than "wherever the JS aliases":

- **`vec2`/`vec3`/`vec4` only** — the types measured to materialize as
  `PooledFloat32Array`. `ivec`/`uvec`/`bvec`/`mat` are left alone rather than
  assumed.
- **Local and parameter sources only.** A binding-sourced alias
  (`var res = fullResolution;` in `synth/osc2d` and `synth/perlin`) would have
  to write through a `const State&` field. The collector skips that class and
  a defence-in-depth guard in the emitter raises if one ever reaches emission
  — that guard **fired on `synth/osc2d:osc2d:87:10`** during development,
  which is how the class was confirmed rather than assumed.

Blast radius: **28 declarations** became references. `typed_slice.cpp` grew by
exactly 28 bytes; `typed_slice.json` and `catalog.hpp` are byte-identical.

## Artifacts (quoted from the generated files)

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tools/glslcpp/typed_slice.json` | 24,374 | `bb8bf931eb315145a5476af65d9e0c843a57ab03c14545119d736bd7c0e748b5` |
| `src/typed_generated/typed_slice.cpp` | 2,075,238 | `79685b9e1114c06634da5d786f969aebbd72da0f14b9e849fda2420419819670` |
| `src/typed_generated/typed_manifest.json` | 304,207 | `0de4e6b6bc377f86a29090c31ab7bc086b41a08155a563eb2ecd456c7cb1e626` |
| `include/noisemaker/generated/catalog.hpp` | 17,572 | `34bbbe17380e159a388ae4fff52c5a64e2e309e90c28a30b9ce08535f0c0e9c8` |

Census, re-derived from the artifacts rather than carried: 190 typed rows,
192 catalog binds, 22 corpus keys absent, 191 of 212 distinct ported, 21
genuinely unported. Sorted 190-key SHA-256 (trailing newline included)
`199fbb5eda87c1206ae3793767d746a06c8c5a8d293268c9d6c9489607c09398` —
unchanged by the fix, which touched emission only.

## The oracle package

`parallax190_oracle_generator.mjs` → `parallax190-oracles.json` (+ report,
all sidecarred); `tools/glslcpp/generate_parallax_native_oracle_include.py`
(38 self-test checks) → `tests/oracles/parallax190_expected.inc`; three
`typed_parallax190_*` native tests.

Provenance is the same discipline the cellRefract and wobble packages use:
immutable snapshot only (the live checkout is refused by real-path
containment), six pinned authority-file hashes, a closed import graph, the
factory text pinned **and** cross-validated against cellRefract's frozen
digest so the `toString` method itself is under test, and the factory text
required to be a verbatim prefix of its slice in the pinned source.

Beyond the template, this generator asserts the **alias contract against the
authority text**: the declaration, the in-place march update and the
refinement write must each occur exactly once, and `prevUV` must never be
rebound. Prose about aliasing would rot; those three assertions do not.

### Mutation ledger — changed float32 lanes per case

| mutant | budgeted as | full-basic | straddle | straddle-tile | zero-direction | tile-clamped | mismatched-maps |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `refinement-copy-restored` | discriminator | . | 6 | 6 | . | 42 | . |
| `refinement-weight-negated` | measured invariant | . | . | . | . | . | . |
| `march-steps-halved` | discriminator | . | . | . | . | 24 | . |
| `shift-scale-halved` | discriminator | . | 24 | 24 | . | . | . |
| `luminosity-weights-swapped` | discriminator | . | 3 | 3 | . | 6 | . |
| `textureLod-becomes-texelFetch-origin` | discriminator | . | . | 60 | . | 42 | . |

`refinement-copy-restored` **is** the emission the port shipped. It is the
regression guard, and the generator fails if no case discriminates it.

`refinement-weight-negated` is budgeted as a measured **invariant**: under the
alias the weight multiplies a zero delta, so negating it cannot move a lane.
Its all-identical row is the positive evidence that the refinement really is
inert, rather than an argument that it ought to be.

## Gates

| Gate | Result |
| --- | --- |
| `check_corpus --check` | exit 0 |
| `check_semantics --check` | exit 0, 212 programs |
| `generate_kernels --check` | exit 0 |
| `generate_typed_slice --check` | exit 0, 190 programs |
| oracle generator `--check` | green, 6 cases, 6 ledger mutants, 1 control |
| include materializer `--check` + `--self-test` | green, 38/38 checks |
| Native Debug | **271 PASS / 0 FAIL**, ctest 1/1, zero warnings |
| Native Release | **271 PASS / 0 FAIL**, ctest 1/1, zero warnings |
| ASan + UBSan | **271 PASS / 0 FAIL**, zero sanitizer diagnostics |
| x86_64 | **269 PASS / 2 FAIL** — both the documented pre-existing arch-NaN fixtures, unchanged by this work |
| Assembly, ARM64 + x86_64 | GO, **re-run after the fix** — `typed_80` pixel scope (7 symbols, 447 instrs ARM64 / 681 x86_64): zero indirect branches, zero jump tables, zero fused-FP; TU-wide fused-FP zero on both arches |

## Claim boundaries

1. **`full-basic` does not discriminate the defect mutant, and is kept
   anyway.** The shipped defect was invisible at exactly that shape. A thin
   case list would have produced a green record over a wrong kernel, and the
   generator now fails if `full-basic` ever starts witnessing — that
   asymmetry is the lesson, encoded.
2. **The straddle cases are the only real parity evidence for the
   refinement.** `zero-direction` and `mismatched-maps` never enter it.
3. **The binding-sourced alias class is NOT fixed** (`synth/osc2d`,
   `synth/perlin`). Whether it is observable is unmeasured — see item 6.
4. **`synth/gradient:gradient` has an open, unconfirmed near-ULP
   differential** that this fix does not change. It is not this mechanism and
   must not be cited as fixed by it.
5. **No LeakSanitizer claim.** `detect_leaks=0` on Apple means LSan did not
   run; the sanitizer lane is ASan + UBSan only.
6. `DEFECTS-FOUND` item 5 (early `return;` output persistence) still applies
   to this program — parallax is the fifth carrier. Unrelated to the alias
   defect and still recorded, not fixed.
