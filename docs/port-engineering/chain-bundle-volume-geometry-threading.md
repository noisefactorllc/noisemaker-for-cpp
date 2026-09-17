# Chain bundle (volume/geometry) threading

Design for wiring Family D's `{image, volume, geometry, volumeSize}` chain
bundle into `GraphExecutor::execute()`, both the non-iterated per-step path
and the iterated-group per-step path landed in the prior task. Written
before the wiring, per the coordinator's instruction. Every citation is
against the JS authority at 61aa869, `src/runtime/renderer.js`.

## What JS does

A chain's "current" value starts as `null` and is normally a bare `Surface`
(every image-domain effect's `image` output). Two helpers make that
polymorphic:

- `isChainBundle(value)` (97-99): true iff `value` is a non-null object with
  an own `image` property.
- `chainBundle(value)` (101-105): normalizes either shape into
  `{image, volume, geometry, volumeSize}` -- a bare value becomes
  `{image: value, volume: null, geometry: null, volumeSize: null}`.

Every effect step calls `chainBundle` on its input, then at the end decides
whether ITS OWN result is a bundle or a bare image:
`(inputWasBundle || isVolumeDomain) ? {image, volume, geometry, volumeSize} :
image` (1335-1337, and identically at 1201-1203/1341-1343/1487-1489). Once
any step in a chain crosses into bundle territory, every later step in that
chain inherits the bundle shape (since it re-reads `isChainBundle(current)`
on ITS OWN input next); an all-image chain never touches any of this.

Four call sites duplicate the same per-step logic exactly (sync/async x
non-iterated/iterated-group -- `runCanonicalEffectSync`/`Async`,
`runGroupStepIterationSync`/`Async`): `inheritVolumeSize` runs before
`effectParams`; `inputTex3d`/`inputGeo` are seeded into the step's resource
map alongside `inputTex`; and after the pass loop, `image`/`volume`/
`geometry` are each resolved via `bundleOutput`, `volumeSize` via a fixed
ternary, then re-validated. This port has no async variant, so the four
collapse to two: the ordinary `EffectStep` block in `execute()`, and
`run_group_step_iteration`.

### `inheritVolumeSize` (107-116)

```js
function inheritVolumeSize(definition, params, inputBundle) {
  const volume = inputBundle.volume
  if (!volume || !Object.hasOwn(params, 'volumeSize')) return params
  if (definition.domain !== 'volume-generator' && definition.domain !== 'volume-filter' && definition.domain !== 'volume-renderer') return params
  const volumeSize = volume.width
  if (volume.height !== volumeSize ** 2) throw ...
  return params.volumeSize === volumeSize ? params : { ...params, volumeSize }
}
```

Only fires when the step HAS an input volume AND declares its own
`volumeSize` parameter AND its domain is one of the three volume domains;
otherwise the step's own bound value is untouched. Ported as
`bundle::inherit_volume_size` (pure: takes the declared-or-not bool and the
input volume's own width/height, returns the value to override to, or
`nullopt` to leave the step's binding alone; throws on the N x N^2
mismatch).

### `bundleOutput` (118-124)

```js
function bundleOutput(name, input, resources) {
  if (!name) return input
  if (name === 'inputTex' || name === 'inputTex3d' || name === 'inputGeo') return input
  return resources.get(name) ?? null
}
```

Four names mean "identity, hand the input straight through unchanged" (an
undeclared output, or a declared output that is literally one of the three
reserved input tokens -- an effect that passes its volume through
unmodified declares `outputTex3d: 'inputTex3d'`, for example); anything else
looks the resource up by name in the step's own resource map (the arena, for
the non-iterated path; `state.resources`/`GroupResourceMap`, for the
iterated-group path -- exactly the SAME routing predicate
`store_group_output` already uses). Ported as
`bundle::is_passthrough_output_name`; the actual lookup stays the caller's
concern (a real Surface fetch).

### The volumeSize ternary and output-shape re-validation (four identical sites)

```js
const volumeSize = definition.domain === 'volume-generator'
  ? (params.volumeSize ?? volume?.width ?? null)
  : (inputBundle.volumeSize ?? params.volumeSize ?? volume?.width ?? null)
if (isVolumeDomain && !volume && definition.domain !== 'volume-renderer') throw ... 'did not produce outputTex3d'
if (volume && (definition.domain === 'volume-generator' || definition.domain === 'volume-filter')) {
  const expectedWidth = volumeSize, expectedHeight = volumeSize ** 2
  if (volume.width !== expectedWidth || volume.height !== expectedHeight) throw ...
}
...
if (!image && definition.domain !== 'volume-generator' && definition.domain !== 'volume-filter') throw ... 'did not produce outputTex'
```

Ported as `bundle::resolve_volume_size`, `bundle::validate_volume_output_shape`,
`bundle::requires_output_image`. `isVolumeDomain` itself
(`domain !== 'image' && domain !== 'loop-begin' && domain !== 'loop-end'`)
is `bundle::is_volume_domain`.

### Pass viewport sizing and the `{screenDivide}`/`{param}` dimension forms

`canonicalDestination` (381-389): `textureDimension(pass?.viewport?.width ??
texture.width, 'width', ctx)` -- a pass may override the OUTPUT texture's own
declared width/height spec with its own, same shape (number/percent-string/
`{param}`/`{screenDivide}`/`{inputOverride}`). `textureDimension` itself
(129-154) is already ported byte-for-byte as `resolve_dimension`'s
`DimensionKind::parameter`/`parameter_default`/`power`/`screen_division`
branches (`executor.cpp`) -- confirmed by re-reading both side by side; there
is no gap there. The actual gap is that `PassDefinition::viewport` is parsed
by the catalog generator as a raw, UNSTRUCTURED `effects::Value` (never a
`DimensionExpression`, unlike every declared texture's own width/height),
because no admitted program has ever declared one. Rather than touching the
generator and re-deriving the whole catalog for a capability zero admitted
or near-term kernels use, this port adds one small RUNTIME parser,
`value_to_dimension_expression()` (`executor.cpp`, mirrors
`generate_effect_catalog.py`'s `_dimension()` exactly, string/number/object
forms included), applied only when `pass.viewport.has_value()` -- which is
never true for any current admission (confirmed: `validate_ordinary_pass_
metadata` already blanket-refuses `pass.viewport.has_value()` for the
ordinary dispatch path, so a currently-admitted effect provably has none).

### `zeroIterationGroupOutput`'s volume-generator branch (615-627)

A zero-iteration group whose owner is `domain === 'volume-generator'` and
has no `groupInput` (opens the chain) allocates a cleared volume (and
geometry, if declared and not itself `'inputGeo'`) instead of a cleared
Surface. Ported into `zero_iteration_group_output`.

## Why this is safe for every currently-admitted effect

Every one of the 167+ admitted effects declares `domain: "image"`. For an
image-domain effect: `is_volume_domain` is false, so the output-shape checks
and the `volumeSize` ternary's `!image` branch never fire meaningfully;
`inherit_volume_size` never fires (its domain guard excludes "image");
`bundleOutput`/`bundle_output` for a null `outputTex3d`/`outputGeo` (every
image-domain effect declares neither) returns the input unchanged --
which is already `nullptr`, since nothing upstream in an all-image chain
ever produces a volume. The new `current_volume`/`current_geometry`/
`current_volume_size` threading variables in `execute()` therefore stay
`nullptr`/`nullopt` for the entire life of any admitted chain, exactly
mirroring `chainBundle(null)`'s own `{volume: null, geometry: null,
volumeSize: null}`. The `image` threading variable (`current`) is completely
untouched by this change -- every line that reads or writes it is the same
line that existed before this task. Verified with a `--variants 6`
before/after sweep over every currently-admitted effect: zero per-case
differences (see the implementation report for the command and result
counts).

## MRT inside an iterated group (Family E addition)

Per the coordinator's follow-up: `run_iterated_group`/`run_group_step_
iteration` (landed in the prior task) had no MRT branch at all -- an
`admission.outputs.size() > 1U` pass inside an iterated group would
silently take the ordinary single-output path, reading only
`pass.outputs.front()`. `groupMrtDestinations` (806-814) is short: resolve
every declared output's own destination via `groupOutputDestination`
(already ported as `allocate_group_output_destination`), assert they share
dimensions (`assertMrtDestinationsShareDimensions`, 51-58, already ported as
part of the non-iterated MRT branch), bind through `bind_factory_route_mrt`,
run through `run_mrt_pass` (both already landed for the non-iterated path by
`lanes/integ4`), then store each output via the SAME `store_group_output`
routing predicate every other output already uses. Zero admitted programs
declare more than one output today (`grep` the compatibility manifest: 0
canonical programs with `outputs.length > 1`), so this new branch is
reachable only from a hand-built synthetic plan, exactly like the rest of
the iterated-group machinery.
