# Task 32 target selection: the `filter/grade` cluster

Date: 2026-08-12
Author: integration owner. Numbers re-derived from
`roadmap2/gate-chain-all-output.json` directly, not taken from prose.

## Correction to the full-chain analysis headline

`roadmap2/full-chain-frontier-map.md` reports `global_admission` as unblocking
**13 programs**. That is a *participation* count — how many chains mention it —
not a *landed* count.

Re-extracted from the raw rows (excluding the two already-public manual
programs, giving exactly 79 unported):

- `final_status` distribution: **PASS 35, NO_GENERIC_PATCH 43,
  PATCH_INSUFFICIENT 1**.
- **No program is landed by `global_admission` alone.** It appears in 14 PASS
  chains but is never sufficient by itself — which is what the *original*
  roadmap said, and that conclusion stands.

Capability participation among the 35 PASS programs:

| capability | chains |
|---|---:|
| `global_admission` | 14 |
| `builtin:dFdx` / `builtin:dFdy` | 11 each |
| `index_expression_admission` | 9 |
| `builtin:fwidth` | 6 |
| `builtin:round` | 5 |
| `scalar_uint_xor_admission` | 4 |
| `bitwise_and_admission` | 4 |
| `uvec_shift_by_vector` | 3 |
| `array_global_admission` | 3 |

## What actually lands programs

Grouping PASS programs by their COMPLETE gate set:

| gate set | programs |
|---|---:|
| `dFdx` + `dFdy` | 10 |
| `fwidth` | 5 |
| **`global_admission` + `index_expression_admission`** | **5** |
| `global_admission` + `round` | 2 |
| `index_expression_admission` alone | 1 |
| eleven further sets | 1 each |

The derivative sets are the largest but need runtime architecture that does not
exist (2×2-quad record/replay). The largest **generator-only** slice is
`global_admission + index_expression_admission`.

## Selected: `filter/grade` — 6 programs, one source file

```text
filter/grade:creative        global_admission + index_expression_admission
filter/grade:hslSecondary    global_admission + index_expression_admission
filter/grade:primary         global_admission + index_expression_admission
filter/grade:vignette        global_admission + index_expression_admission
filter/grade:wheels          global_admission + index_expression_admission
filter/grade:lut             index_expression_admission only
```

**Correction (from the Task 32 brief, which checked the corpus rather than
assuming):** these are **six separate GLSL files** — `primary.glsl`,
`hslSecondary.glsl`, `wheels.glsl`, `vignette.glsl`, `creative.glsl`,
`lut.glsl` — sharing only an `effect_id`. My earlier claim that they are six
passes of one file was wrong. The consequence is real: authentication needs
**six independent per-program profiles**, not one shared parse tree. They
remain a coherent slice because they share the same two capability *shapes*,
not because they share a source file. This is still the first genuine
multi-program slice since the port began. Adding `builtin:round` would extend
the same set to 8, but `round`'s own hazard is not render-discriminable for
those programs (see `task32-precompute-report.md`), so it should be a separate,
smaller task rather than bundled.

Projected state if all six land: **137 typed / 139 public / 73 unported**.

## Required before implementation

1. Re-verify each program's full chain independently — cluster counts from
   first-blocker grouping have been proven optimistic twice, and this
   analysis's own headline needed the correction above.
2. Apply both mandatory filters per program: **reachability** from `main` at the
   authorized define map, and **discriminability** of each capability's real
   hazard. `filter/snow` and `caustic` were both disqualified by the first.
3. Confirm what `index_expression_admission` actually requires. The full-chain
   engine classifies it as one capability, but the report itself warns it is
   "really 2-4 real per-program proofs, not 1". Establish the true shape before
   writing a brief.
4. Note the analysis found `Mat<N>`, `Vec<N,bool>`, `reflect`, `refract`,
   `bitwise_xor` and `shift_right` **already exist** in the C++ runtime.
   Matrix support for 9 programs is blocked only by generator-side dispatch
   hardcoded to `mat2 * vec2` — no runtime work. That is the highest-value
   follow-on after this cluster.
