# Task 31 target reselection: Caustic → Curl

Date: 2026-08-12
Author: integration owner

## Why the target changed

`classicNoisedeck/caustic:caustic` was selected by precompute and passed design
review, but implementation surfaced a disqualifying property (see
`task-31-blockers.md`): at its authorized define map `{"NOISE_TYPE": 10}` the
entire new closure is **dead code**. `randomFromLatticeWithOffset` is not
reachable from `main()`, and all four structural mutations render bit-identical
output. Full-render pixel parity — the strongest evidence Tasks 29 and 30 both
delivered — cannot validate it.

The separate emitter defect Caustic exposed has been fixed independently and
retained (`task-31a-reserved-identifier-guard.md`); it unblocks ten programs.

## A selection criterion that was missing

Neither the precompute nor the design review checked **reachability of the
closure from `main` at the authorized define map**. Both verified the gate
chain and the AST closure, which is necessary but not sufficient: a closure can
be structurally present, type-check, emit, and still be unreachable, in which
case no rendering evidence can discriminate it.

**This check is now mandatory before selecting any future target.** It is
cheap — walk the call graph from `main` following `call` nodes' `signature_id`,
then ask whether each closure site's owning function is in the reachable set.

## Curl passes the check

`synth/curl:curl`, defines `{"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True}`,
7 functions, loop proof `(1, 0, 1, 1, 12, True)`. Six of seven functions are
reachable from `main`.

| Closure site | Owning function | Span | Reachable |
|---|---|---|---|
| `tanh(vec3) -> vec3` | `main` (id 18) | 196:12 | **yes** |
| `mod(vec4, float) -> vec4` | `permute` (id 20) | 35:12 | **yes** |
| `mod(vec3, float) -> vec3` | `simplex3D` (id 21) | 65:9 | **yes** |
| `mod(vec3, float) -> vec3` | `permute` (id 19) | 32:12 | no |

Three of four sites are live and reachable, so mutating them changes rendered
output and full-surface bit-exact parity is a meaningful gate.

The fourth site is an unreachable overload variant of `permute`. It must still
be authenticated — it exists in the program and the emitter will lower it — but
any Task 31 report must state plainly that this one site is validated
structurally rather than by rendering. Do not claim four-site render coverage.

Note the existing generic `mod` gate already admits `("float","float")`,
`("vec2","float")` and `("vec2","vec2")`; the new work is exactly the `vec3`
and `vec4` by-scalar overloads, plus `tanh` on `vec3`.

## Consequence for the roadmap

`remaining-capability-roadmap.md` ranks candidates by programs-unblocked and
gate-chain depth. Add reachability as a gating filter before that ranking:
a candidate whose closure is unreachable at its authorized defines should be
deprioritized regardless of how cheap its gate chain looks, because it cannot
be validated to the standard the accepted tasks set.

Caustic remains a legitimate future port, but whoever takes it must accept
direct-closure-probe parity instead of full-render parity, and must say so.

---

## Refinement: reachability is necessary but NOT sufficient

Added after the Curl oracle was built. The criterion above is correct as far as
it goes, but it would have given false confidence here.

The Curl oracle owner found that **both reachable `mod(vecN, float)` sites are
structurally immune to the floor-versus-trunc hazard when observed through full
rendering** — proven algebraically, not merely observed:

- `mod(vec4, float)` in `permute` (id 20): every operand at that site is an
  exact integer, and `34x² + 10x >= 0` for all integers `x`. GLSL floor-mod and
  naive trunc-mod/`fmod` are therefore identical for non-negative dividends.
- `mod(vec3, float)` in `simplex3D` (id 21): the downstream permute polynomial
  is exactly periodic mod 289 for integer `x`, so the ±289 shift a naive `fmod`
  introduces is silently absorbed.

Evidence: a naive-fmod mutation diverges 0/6 eligible cases, 0/3 ineligible, and
0/40 in a randomized stress sweep with seed in [-1e6, 1e6].

The sites are nonetheless genuinely **live**. A supplementary wrong-divisor
mutation (mod 288 instead of 289) breaks both invariants and diverges 6/6
eligible and 40/40 in the sweep — proving the code executes on every pixel and
its output reaches the image. It is specifically the rounding distinction that
full-render cannot observe.

`tanh(vec3)` in `main` behaves as the criterion predicts: an identity-passthrough
mutation diverges 5/6.

### The corrected criterion

Two separate questions must be asked of every closure site:

1. **Reachability** — is the owning function reachable from `main` at the
   authorized define map? If not, no rendering evidence can validate it at all.
   (This is what disqualified Caustic.)
2. **Discriminability of the specific hazard** — does mutating the site in the
   way the port could realistically get wrong actually change rendered output?
   A site can be fully live and still mask its own hazard through algebraic
   invariants downstream.

Where (2) fails, full-render parity proves the site executes but not that its
semantics are right. Direct rows binding the exact operation become the
authoritative parity surface, and the implementation report must say so plainly
instead of implying full-render coverage.

For Curl the honest split is:

| Site | Liveness evidence | Semantic evidence |
|---|---|---|
| `tanh(vec3)`, main | full render (5/6) | full render |
| `mod(vec4,float)`, permute 20 | full render, wrong-divisor (6/6) | direct rows |
| `mod(vec3,float)`, simplex3D 21 | full render, wrong-divisor (6/6) | direct rows |
| `mod(vec3,float)`, permute 19 | none — unreachable | direct rows / structural |

The oracle's `direct_mod_rows` (8 rows against the real `stdlib.mod` versus JS
`%`) deliberately include negative operands, ±0.0, and near-float32 extremes,
with every negative-lane row machine-asserted to diverge from naive fmod at bit
level. A further finding worth keeping: GLSL `mod` collapses `-0.0` to signless
`+0.0` whereas naive fmod preserves the sign bit.

Curl remains the right target — this is a nuance in how its parity must be
argued, not a disqualification like Caustic's dead code.
