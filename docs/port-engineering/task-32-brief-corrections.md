# Task 32 brief — mandatory text corrections before implementation

The design review (`task-32-design-review.md`, verdict ACCEPT) raised three
Important findings against `task-32-brief.md`. All three are **evidence-quality
errors in the brief's prose, not errors in its design boundary** — §8's capability
scope is correct as written. I re-verified each one independently against the
live tree; all three confirmed. Fix the brief text (or correct it explicitly in
the implementation report) before any of this wording is copied into code
comments, mirroring the accepted Task 30 rereview precedent.

## I1 — "no existing track admits an id-indexed write" is FALSE

`generate_typed_slice.py:2131-2135`:

```python
grid_store_valid = (
    context == "lvalue" and index.kind == "id"
    and index.symbol_id is not None
    and (base.symbol_id, index.symbol_id, value.span)
    in proved_grid_dynamic_stores)
```

That is exactly an id-indexed write, already live for `celShadingEdges` /
`outlineSobel`. **Verified by direct read.**

The correct argument — which the brief also makes elsewhere — is narrower:
grade cannot reuse this track because `base_valid` requires a *proved array*,
and grade's plain-`vec3` locals never have one. Use that reasoning instead.

## I2 — the cited span is a read, not a write

The brief cites `filter/grade:primary:41:13` as "the `linear[i] =` line". At that
normalized-source position the node is a **read** inside an `if` condition; the
write is on the following line. Confirmed against the raw source, where
`linearToSrgb`'s loop reads `linear[i]` in its guard (`if (linear[i] <=
0.0031308)`) and writes `srgb[i]` on the next line.

Root cause of the mislabel: `typed.functions` is **alphabetically ordered**, so
`linearToSrgb` is walked before `srgbToLinear`, and the brief's author matched
the wrong function's loop. Note the brief's own §4b table already tags this span
`rvalue`, directly contradicting its §1 prose — the table is right.

Related trap worth carrying forward: `TypedStatement.span` indexes the
**normalized** source (`typed.source`), not the raw corpus file; they differ by
roughly 18 lines in some files. Cite spans the way the generator's own
diagnostics do, never by eyeballing the `.glsl`.

## I3 — "every prior task ported exactly one program" is FALSE

Task 25 landed **two**: `classicNoisedeck/lensDistortion:lensDistortion` and
`filter/prismaticAberration:prismaticAberration`, sharing one capability shape.
**Verified** — both keys are present in the live `typed_slice.json`.

This *strengthens* §9's recommendation to land grade as one task rather than
weakening it: multi-program tasks have precedent.

## Minor / nit (from the same review)

- Smooth Edge's precedent is a **1-read-path** template; grade needs it
  generalized to a variable 0-4 reads. It is not a literal copy.
- The "Extrude ... have a bespoke factory constant" list is wrong — only
  `degauss` and `crt` do.
- The `bitEffects` precedent is analyzed-only, not yet landed.
- The +6 ordinal shift also renames 102 C++ namespaces in the generated file.
  Confirmed harmless: no test references them by number.

## Independently reconfirmed (no change needed)

I recomputed all four of §7's projected hashes and the blast radius from the
live `typed_slice.json`, and every one reproduces:

| | Value | Matches brief |
|---|---|---|
| Current typed (131) | `ea5c0628867261e889e8235cae1c1da4a92d289cfd3ae97f3bd659728abb0dc2` | yes |
| Projected typed (137) | `dfb7c7c43d7fd118c4a1b9a266d6957a90b189ec63ac6b0d49538bd853a360d7` | yes |
| Projected public (139) | `a873c537d3d8ffb872859389812ae7c1e68954c9fcd381334eca4998195f319f` | yes |
| Insertion index / shifted | 29 / **102 programs +6** | yes |

The one number in the brief that *is* wrong is inherited, not original:
"unported 79 → 73" should be **80 → 74** (the corpus holds 211 programs, not
212). This does not affect any hash, since all four derive from the key list.
