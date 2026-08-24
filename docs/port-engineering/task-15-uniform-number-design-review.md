# Task 15 scalar-uniform precision review

## Decision

Adopt a **scalar Number path**: `double` is the native representation for a
canonical JavaScript scalar uniform, while the pre-existing `float` alternative
remains supported as a legacy caller input.  Do not widen vector uniforms in
this change.  The proposed `UniformValue`/`Bindings::get_number()`/emitter
shape is the smallest systemic change that fixes the lowPoly class of mismatch,
provided the fixture generator distinguishes renderer-built scalar bindings
from ordinary effect parameters.

## Evidence and required semantics

`createCanonicalBindings()` in the CPU reference copies `uniforms` directly
into its binding object.  An ordinary scalar parameter such as lowPoly
`edgeStrength: 0.15` is therefore a JavaScript binary64 Number.  It is not
rounded when bound.  Generated source then passes it to operations such as
`mix`; the CSL runtime supplies the float rounding at the operation/vector
boundary, not at uniform lookup.  Binding it natively as `float` first changes
the input from `0.15` to `0.15000000596046448`, which is enough to alter a
final Float32 pixel.

The following implementation contract matches that behavior:

* Add `double` to `glsl::UniformValue`.
* `Bindings::get_number(name)` returns a stored `double` exactly, or widens a
  stored `float` exactly; it rejects all other alternatives and retains the
  existing missing/wrong-type messages.
* The emitter stores a declared scalar GLSL `float` uniform in `State` as
  `double` and binds it via `get_number`.  Float locals/parameters already use
  `double`, so this preserves the value until the existing modeled float
  boundary.
* Leave `Bindings::get<float>()` exact-type-only.  This preserves old explicit
  float APIs and prevents integers/bools from silently becoming shader
  numbers.  `set_uniform(name, 0.15f)` remains valid; `get_number` widens it
  to its exact float value.  `set_uniform(name, 0.15)` selects the new double
  alternative.

The current working implementation follows this shape, including a focused
runtime test for exact doubles and legacy float widening.  Add a direct
generated-kernel test if practical: one scalar bound as `0.15` must differ
from the same binding supplied as `0.15f` at the relevant modeled boundary,
and both must bind successfully.  Keep the existing wrong-type tests (an
integer must still fail for a float uniform).

## Fixture rule: doubles require provenance, not merely scalar type

The Task 15 table must pass ordinary effect scalar values as `double` literals
with their JavaScript decimal value (for example, lowPoly `edgeStrength: 0.15`
without an `f` suffix).  A `std::array<double, 3>` table is safe for that only
if the producer marks the renderer-supplied scalar exceptions separately.

There is one material exception already in this slice.  The canonical binding
constructor spreads `uniforms`, then overwrites these scalar values:

| Binding | Canonical precision |
| --- | --- |
| `seed` | `f32(seed)` |
| `time`, `globalTime`, `deltaTime` | `f32(...)` |
| `aspect`, `aspectRatio` | `f32(width / height)` |

Task 15's `synth/mandala:mandala` table currently records
`aspect = 1.2857142857142858` for a 9x7 render.  Canonical runtime actually
binds `Math.fround(9 / 7) = 1.2857142686843872`.  The old float fixture happened
to be correct; a blanket scalar-to-double setter makes it wrong.  Its `time`
value (`0.375`) and shown `seed` values are exactly representable, so they do
not expose the same issue, but they must follow the same provenance rule.

Safest fixture design: preserve the `Task15BindingType`, add a scalar precision
tag (`canonical_number` vs `canonical_f32`) or construct the bindings directly
from the same canonical-binding generator.  The setter then uses `double` only
for `canonical_number`, and uses `static_cast<float>` for `canonical_f32`.
This is preferable to name-based exceptions hidden in the test renderer.  At
minimum, tag `aspect` now and add a non-integral time/seed regression fixture
so the overwrite ordering cannot regress unnoticed.

## Vector uniforms: deliberate non-goal

Canonical vector uniforms are normally plain JavaScript arrays.  Their lanes
are binary64 at binding time; the precise point at which each lane becomes
Float32 depends on the emitted canonical code (constructor, vector operation,
or scalar/swizzle use).  Native `Vec2`/`Vec3`/`Vec4` store float lanes at
binding time.  The current Task 15 table's double backing storage still narrows
vector values on construction, so it preserves the native vector behavior but
does not solve that parity question.

Do not add double-vector alternatives or change `Vec*` for this fix.  Doing so
would alter operation overloads and rounding placement across the renderer.
First create a focused oracle with a non-F32 vector lane (for example `0.1`) in
both direct vector arithmetic and scalar swizzle use, then model the observed
boundaries deliberately.  The all-zero lowPoly `edgeColor` cannot validate
this.  Existing Task 15 vectors such as hatch/relief colors are useful audit
targets.

## Verification checklist

1. Runtime: double exactness, float widening, missing binding, and non-number
   rejection; also assert `get<float>` does not accept a stored double.
2. Generator: scalar uniforms emit `double` state fields and `get_number`,
   while integer/bool/vector/sampler binding calls are unchanged.
3. Fixture source: ordinary parameter scalars keep round-trippable JS Number
   literals; canonical post-spread built-ins are explicitly F32.
4. Regression: all prior float-supplied oracle inputs remain byte-identical;
   Task 15 lowPoly matches its external Float32/RGBA hashes; add the aspect
   fixture assertion above before treating the whole 38-case table as green.

## Scope

This review was read-only.  No repository files or Git state were changed.
