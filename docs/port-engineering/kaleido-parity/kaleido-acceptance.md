# kaleido187 — acceptance record

`classicNoisedeck/kaleido:kaleido` landed as typed row 187 (2026-08-18),
namespace `typed_6` between `glitch:glitch` and `lensDistortion`. Second
program of the **mutable uninitialized global `float[9]` array** mechanism
(record `mutable-global-nine-array-kaleido-v1`, moved from PREPARED to
landed in `tools/glslcpp/frontend/mutable_global_array_profile.py`), fourth
key of `fixed_array_in_parameter_proof.py` dispatch order aside — its
`kaleido-convolve-v1` record was frozen by the preparation lane and wired at
integration. Companions: the pre-frozen `scalar-uint-xor-v1` (wired via the
per-key absent-set carve in `scalar_uint_xor_profile.py` — the carve the
design review demanded). Design `kaleido-design.md` (reviewed GO;
corrections folded); frozen review
`../prepared-designs-review-kaleido-varying-effects.md`.

## Slice row

```json
{
  "defines": {"DIRECTION": 2, "KERNEL": 0, "LOOP_OFFSET": 10, "METRIC": 0},
  "mutable_global_array_profile": "mutable-global-nine-array-kaleido-v1",
  "program_key": "classicNoisedeck/kaleido:kaleido",
  "scalar_uint_xor_profile": "scalar-uint-xor-v1"
}
```

## Post-slice artifacts (quoted from the generated files)

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tools/glslcpp/typed_slice.json` | 23,751 | `460edeccdce784b3d08f160ab32c6de399c07ff22aa99e04314b94435b59ac58` |
| `src/typed_generated/typed_slice.cpp` | 2,001,343 | `89575abdaef3b2b2db7aeaea1cd06a72540c6bdac696d1b37214e5e8a725343d` |
| `src/typed_generated/typed_manifest.json` | 299,169 | `158d034396d123f44e62def895c2578f381a015d8b1518f1137334a1b9f32c9b` |
| `include/noisemaker/generated/catalog.hpp` | 17,301 | `f7ba369927d0bd71f25d80339e650e91cc3722fa61b523a94ebbc9a8cddbb7fc` |

Census: 187 typed rows; 189 catalog binds; corpus keys absent 25; genuinely
unported 24; sorted 187-key SHA-256 (trailing newline)
`587bd0fc54a7aa6a55f65bd8d1a8d36c06f566f369f617c03e90045652747acd`;
`factories.size()` 188U → 189U; shared expected-keys array carries kaleido
(sorted beside `glitch:glitch`).

## Gates (focused at landing; full matrix is wave-end batched)

- **Generator gates**: all four `--check` exit 0 at 187 programs
  (controller-run after recovery).
- **Focused Python**: `KaleidoMutableGlobalArrayIntegrationTests` +
  `tests.test_mutable_global_array` — **160/160 green** (includes the
  187→186 historical reconstruction and the schema/census pins).
- **Milestone modules** (the seven from the cellRefract repair pass, updated
  for kaleido by the integration lane) + `test_semantic`: green
  (controller-run; log in the run root).
- **Emitted namespace read-back**: `typed_6` carries the family contract —
  `Kernel9`/`Offsets9` aliases, every helper `[[maybe_unused]] const Frame&
  frame` at ordinal 2, `loadKernels` the sole `Frame&` writer, `struct Frame`
  with the five `Kernel9` members; source SHA matches the design pin
  (`3a155a9b…`).
- **Native Debug** build + suite on the 187-row state: see the wave-end
  record (build run post-recovery; kaleido has no native oracle block yet —
  its oracle package is the wave's remaining native-lane work).

## Process record — the agent kill and recovery

The integration lane was killed by a platform usage limit mid-verification
(all three in-flight lanes died together). The tree was recovered by the
controller without redoing work: the row, registry move, regeneration,
census pins, factories assertion, and milestone updates were all already
landed; the controller ran the remaining verification (generator gates,
focused modules, milestone modules, namespace read-back, native build) and
quoted the artifacts above. No work was lost; the killed lane's final report
never arrived, so every figure here was re-measured by the controller rather
than transcribed from any agent claim.

## Claim boundaries

Same family boundaries as cellRefract186: the five tables are write-only at
the frozen defines (the preparation lane's measured census; assembly-level
witness pending the wave-end sweep), no oracle case can discriminate table
mutations, and the XOR sites are runtime-dead at `LOOP_OFFSET=10` while
structurally retained (the `if (10 == 10)` constant-guard chain the design
recorded — structural reachability ≠ runtime liveness). The conditional
assembly-gate rule from Shapes applies: any define variant re-runs the gate.
