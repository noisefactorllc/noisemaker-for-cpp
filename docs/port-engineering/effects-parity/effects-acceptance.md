# effects188 — acceptance record

`classicNoisedeck/effects:effects` landed as typed row 188 (2026-08-18),
namespace `typed_5` between `composite:composite` and `glitch:glitch`. Third
and final member of the **mutable uninitialized global `float[9]` array**
family (`mutable-global-nine-array-effects-v1`, seven arrays — the family's
five plus `edge3` and `sharpenBlur`, 63 stores), and the family's first
**four-carrier row**: array + mat4 (`mat4-bicubic-chain-effects-v1`, the
per-key authorization over the emitter's existing mat4 lowering — no new
lowering, exactly as the design's §4.4 coverage proof predicted) + ceil
(`ceil-admission-v1` key) + the auto-attached fourth FAP key
(`effects-convolve-v1`). Design `effects-design.md` (reviewed
GO-WITH-CORRECTIONS, corrections folded); frozen review
`../prepared-designs-review-kaleido-varying-effects.md`.

## Slice row

```json
{
  "ceil_admission_profile": "ceil-admission-v1",
  "defines": {"EFFECT": 0, "FLIP": 0},
  "glitch_mat4_chain_profile": "mat4-bicubic-chain-effects-v1",
  "mutable_global_array_profile": "mutable-global-nine-array-effects-v1",
  "program_key": "classicNoisedeck/effects:effects"
}
```

## Post-slice artifacts (quoted from the generated files)

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tools/glslcpp/typed_slice.json` | 24,086 | `bc32451249e6b11de2944f69318cea54172b1b5a8c4656ad09ce6b50e2b0da04` |
| `src/typed_generated/typed_slice.cpp` | 2,058,845 | `cd85e5ffd88060e2825b4ccbd613bc4701d150e41f7f1db4469b092af66069fd` |
| `src/typed_generated/typed_manifest.json` | 300,959 | `f07380dc996fa13fdb4ba9d24453916835920f6b7e5b6e85a7c3094ac76dbc0e` |
| `include/noisemaker/generated/catalog.hpp` | 17,398 | `ab45fef3f312345ebd8eb281e8f2ac9310888b37c37cca1dd95c420cd896965e` |

Census: 188 typed rows; 190 catalog binds; corpus keys absent 24; genuinely
unported 23; sorted 188-key SHA-256 (trailing newline)
`28ca8a0f585107d84b94d2f878da2d9422780a65c9d8b7695918f92186764ded`;
`factories.size()` 189U → 190U; shared expected-keys array carries effects.

## Gates (focused at landing; full matrix is wave-end batched)

- **Generator gates**: all four `--check` exit 0 at 188 programs
  (controller-run after recovery).
- **Focused battery** (controller-run, the full ten-module set):
  `test_typed_generator` + `test_mutable_global_array` + `test_semantic` +
  `test_scalar_uint_xor` + `test_glitch_mat4_chain` +
  `test_edge_bvec3_contour` + `test_glyph_map_nonnegative_int_shift` +
  `test_emboss_color_style` + `test_task35_bitwise_number_profile` +
  `test_shape_mixer_builtin_closure` — **518 tests / 0 failures**, which
  includes the lane's `EffectsMutableGlobalArrayIntegrationTests` (188→187
  historical reconstruction and census pins) and the completed milestone
  repair pass.
- **Emitted namespace read-back** (controller): `typed_5` carries the
  contract — all **63** `frame.<array>[k]` stores, `loadKernels` the sole
  `Frame&` writer, and the bicubic mat4 closure emitted verbatim in the
  design's §4.4 form (`glsl::Mat4(glsl::Vec4(...))` columns, `((T*Q)*S)`,
  `glsl::dot((tv * A), uv)`); source SHA matches the design pin
  (`e3b742be…`).
- **Native Debug**: build + suite on the 188-row state — see the wave-end
  record.

## Process record — the second agent kill and recovery

The integration lane ran 7.3 hours and died of a context overflow
("Invalid string length") during verification — the same recovery situation
as kaleido187, with the same outcome: the row, registry move, module records
(all three carves included), regeneration, census pins, factories assertion,
keys array, integration tests, and the milestone repair pass were all landed;
the controller ran the remaining verification and re-quoted every figure
above from the artifacts. Lesson repeated: the lane briefs now carry their
own verification as the controller's closing step, and both kills landed
~95%-complete work that verified green without rework.

## Claim boundaries

Family boundaries hold as for cellRefract/kaleido: the seven tables are
write-only at the frozen defines (`EFFECT=0/FLIP=0` — the measured census),
so no oracle case can discriminate table mutations and their protection is
structural. The mat4 closure lives in unreachable `bicubic` (no caller at
these defines) — its emitted form is verified by read-back and the design's
emitter-arms proof, not by pixels; any define variant that wakes
`convolutionEffect`/`bicubic` re-runs the assembly gate (Shapes'
conditional-liveness rule). No crop identity is asserted (the family rule;
see the cellRefract §15 and varying amendments).
