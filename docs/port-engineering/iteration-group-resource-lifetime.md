# Iteration-group resource lifetime

Design for wiring `noisemaker::graph::iteration::compute_iteration_groups` (already
ported, `include/noisemaker/graph/iteration.hpp` / `src/graph/iteration.cpp`) into
`GraphExecutor::execute()` (`src/graph/executor.cpp`). Written before the wiring
landed, per the coordinator's instruction to design the resource-lifetime model
first. Every citation below is against the JS authority at the pinned revision
(`noisemaker-for-cpu` 61aa869), files `src/runtime/renderer.js` and
`src/runtime/iteration.js`.

## The question

`iteration.hpp`'s own doc comment (written when `compute_iteration_groups` first
landed, deliberately unwired) named the open problem exactly:

> a real design pass on ResourceArena's lifetime model first (it has no category
> today for "persists across N re-executions of a subgraph, never published to a
> name any other step could bind by mistake").

`ResourceArena` (`include/noisemaker/graph/resource.hpp`) is a single flat
`name -> GraphResource` map, global for the lifetime of one `execute()` call.
Every non-iterated `EffectStep` today publishes its declared textures and pass
outputs straight into that one namespace (`arena.allocate`/`arena.insert`), and
nothing ever tears a name back out mid-run except a later publish over the same
name. That works because a non-iterated effect's pass graph runs exactly once:
whatever it allocates lives at most as long as the whole `execute()` call, and no
two *live* effects ever need the same declared name at the same time.

An iterated group runs its whole pass graph, and every step in it, `N` times in
place (`renderer.js:566-571`). Two lifetime problems fall out of that which the
existing arena model has no answer for:

1. **A step's own scratch texture must persist across all `N` iterations**, not
   be recreated (and re-zeroed) each time. `synth/cellularAutomata`'s `update`
   pass, for example, both reads and writes its own `global_ca_state` in the same
   pass -- iteration 0 needs it to already exist, zeroed; iteration 1 needs
   iteration 0's real output, not a fresh zero-fill
   (`renderer.js:767-774`, `ensureGroupScratchResources`).
2. **A particle group's state (`global_xyz`/`global_vel`/`global_rgba`/
   `global_life_data`/`global_*_trail`) and a loop region's `global_accum` are
   shared by every step in the group**, for the group's whole run, and must
   never be visible to -- or bindable by -- any step outside that one group run
   (`renderer.js:706-720`, `resolveGroupParticleTexture`; `storeGroupOutput`,
   `renderer.js:762-765`).

## Resolution: keep these out of `ResourceArena` entirely

The JS authority already answers this, by construction: `state.resources` and
`groupResources` (`renderer.js:667`, `857`/`900`) are plain, ephemeral `Map`s
created fresh for one `runIteratedGroupSync`/`Async` call. They are never merged
into `this.surfaces` -- the renderer's own persistent, chain-wide named map (the
JS analog of `ResourceArena::named_`). A name published into `state.resources` or
`groupResources` is invisible to `buildBindings`'s surface-parameter resolution,
to a `read`/`write` step, and to every other effect in the chain; only the
group's *final returned surface* ever crosses back into `surfaces`, and only
because the renderer's `render()` loop assigns it to `current` the same way any
non-iterated step's output does (`renderer.js:1627-1637`).

This port keeps that separation instead of growing `ResourceArena` a new
lifetime category. Concretely, `execute()` gains, scoped to one iterated
group's run (stack-local, never touching `ResourceArena::named_`):

- `iteration::GroupResourceMap` (already built) for particle-state names and the
  literal `global_accum` -- exactly the routing predicate it already implements
  (`is_group_shared_resource_name`), created once per group and dropped when the
  group's run returns.
- One `GroupStepState` per step in the group (`std::vector`, index-ordered,
  built once before the `N`-loop), each owning:
  - `std::unordered_map<std::string, noisemaker::Surface> resources` -- the
    step-local analog of JS's `state.resources`: declared scratch textures
    (zero-filled once, `ensureGroupScratchResources`), plus `inputTex` and every
    surface-parameter route, *refreshed* into this map at the top of every
    iteration (`renderer.js:947-950`, `buildBindings`'s `textures` merged into
    `state.resources`).
  - `std::optional<noisemaker::Surface> self_tex` -- allocated once (sized from
    the step's own `outputTex` texture spec), zero-cleared, and updated by a raw
    byte copy at the end of every iteration
    (`renderer.js:1068-1072`, `assertSelfTexMatchesOutput`). It is never stored
    under a name in either map, so no pass-output publish can ever recycle it
    mid-run -- matching JS's own comment at `renderer.js:654-659` almost word
    for word.

Only the group's *last* rendered surface (an independent clone, taken the
instant it is produced -- never a reference into either map above) is ever
handed to `ResourceArena::insert`, under that pass's own output route, exactly
like a non-iterated step's final pass already publishes. Everything else --
every step's local map, the group-shared map, every intermediate iteration's
surfaces -- is a plain local variable that goes out of scope (and is freed, via
ordinary destructors -- there is no shared allocator/pool to return anything to
in this port, non-iterated or iterated) when the group's run function returns.
This is a direct structural mirror of `finishGroupResources`
(`renderer.js:832-850`): "release everything not retained by the final result."

No new `ResourceLifetime` enumerator, no new `ResourceArena` method. The arena's
contract -- "a name published here is chain-global and any later step can bind
it" -- stays true precisely because iteration-group bookkeeping never enters it.

## Route resolution inside a group step

`BindingMaterializationContext` (`executor.hpp`) already has the seam this
needs: a `SurfaceLookup` function pointer plus an opaque `void*` context, used
today only to resolve against the arena. The group-step path builds a *second*
lookup, `lookup_group_step_route`, backed by a small context struct holding the
step's `GroupStepState*` and the group's `GroupResourceMap*`:

1. `selfTex` / `feedback` (the reserved tokens, `renderer.js:395-402`) resolve to
   the step's own `self_tex`, or the executor's existing empty 1x1 surface as a
   defensive fallback (unreachable in practice, same as JS's own
   `emptySurface` fallback at the same two lines -- `usesSelfTex` and the
   selfTex allocation scan the identical pass-input set, so a step that ever
   reaches this lookup for these two names has already allocated `self_tex`).
2. The literal `global_accum` resolves to the group map *only if the map already
   has it* (seeded once, before the `N`-loop, only for a loop region --
   `renderer.js:858-865`) -- otherwise it falls through to the step's own map,
   matching `resourceName === 'global_accum' && groupResources.has(resourceName)`
   exactly (`renderer.js:733-736`). It is never lazily created by input
   resolution.
3. Any other particle-state name resolves to the group map, lazily created on
   first reference (`resolveGroupParticleTexture`, `renderer.js:711-720`): sized
   from whichever step in the group *declares* that texture name in its own
   `definition.textures` (first match, group order), or -- if none does, e.g. a
   `points/*` effect run with no `pointsEmit` ahead of it -- a synthetic
   `{param: 'stateSize', default: 256}` spec resolved against the *referencing*
   step, with the format table `renderer.js:23-32` hard-codes per name.
4. Everything else resolves to the step's own local map (declared scratch,
   `inputTex`, surface parameters -- refreshed every iteration as above).

Output-side allocation (`groupOutputDestination`, `renderer.js:750-760`) mirrors
the same split: a particle-state output name is sized via the *declaring* step's
spec (same search as #3); everything else -- including the literal
`global_accum`, which is an ordinary declared texture on whichever effect owns
it, `filter/convolutionFeedback` -- is sized via the *current* step's own
declared texture. Storage after render always follows
`is_group_shared_resource_name` (`storeGroupOutput`, `renderer.js:762-765`,
already ported byte-for-byte as `iteration::is_group_shared_resource_name`):
particle-state or literal `global_accum` goes to the group map; everything else
to the step's own map.

## The `N`-iteration loop

Per `renderer.js:852-855` / `872-878` (sync and async are identical here): `N` is
the group-owning step's own bound `iterationCount` parameter, defaulting to 60
only when absent/non-finite (`iteration::resolve_iteration_count`, already
ported). `N <= 0` skips every pass and clones the group's input surface through
unchanged (`zeroIterationGroupOutput`, `renderer.js:592-634` -- this port only
ever threads a plain `Surface`, so the volume/geometry-bundle branches of that
function do not apply; every executed effect in this codebase is image-domain).
Otherwise, iteration `i` of `N` binds a *local* `ExecutionInputs` copy with
`frame = i`, `delta_time = kIterationDeltaTime` (1/600s), and
`time = wrap01(inputs.time - (N-1-i) * kIterationDeltaTime)` -- `wrap01` and the
constant are already ported. `BindingMaterializationContext::inputs` is already
a plain pointer, so handing it this per-iteration copy (instead of the outer
`inputs`) is the entire change needed to make every existing pass-derived
uniform (`time`/`frame`/`seed`/`deltaTime`/`resolution`/`fullResolution`) resolve
correctly for free, with no changes to `resolve_authenticated_pass_derived` or
`reserved_uniform`.

Within one iteration, each step in group order runs its whole pass graph once
(`run_group_step_iteration`, the C++ analog of `runGroupStepIterationSync`),
threading its own produced surface to the next step as that step's `inputTex`
-- exactly `let stepInput = groupInput; for (const state of stepStates) stepInput
= runGroupStepIterationSync(...)` (`renderer.js:879-883`). A joining step's own
`stateSize` parameter is unconditionally overridden to the group owner's
resolved value before anything else runs for that step (`groupOwnerStateSize`,
`renderer.js:34-45`; `initializeGroupStepState`'s `sourceStep`,
`renderer.js:660-663`) -- ported as a one-time clone of that step's `EffectStep`
with its `stateSize` binding replaced, reused for the group's whole run.

Pass execution inside `run_group_step_iteration` reuses every existing
authenticated helper unchanged -- `preflight_pass_abi`,
`materialize_uniform_bindings`, `materialize_sampler_bindings`,
`apply_classic_noisedeck_palette_override`, `bind_factory_route`,
`materialize_scatter_bindings`, `scatter_pass_from_definition`,
`resolve_scatter_adapter`, `run_pass`, `quantize_texture` -- only the route
lookup callback and the per-iteration `ExecutionInputs` differ from the
non-iterated path. Both pass shapes the non-iterated path supports (ordinary
single fragment output, and scatter/points/billboards) are wired the same way
here. MRT (`drawBuffers >= 2`) needs no special handling in either path: every
pass, iterated or not, is required to declare exactly one fragment output by
`validate_pass_output_abi`, which both `validate_plan_before_allocation` (the
pre-allocation dry run) and `preflight_pass_abi` (the real per-pass
authentication) already call unconditionally -- an MRT-shaped pass is refused
with `unsupported_mrt` before `execute()`'s main loop reaches *any* pass,
grouped or not. There is no gap here to defer.

## Zero behavior change for every currently-admitted effect

`compute_iteration_groups` only ever produces an *iterated* group when the
group-owning step's `EffectDefinition::iterated` is true, or the step opens a
loop region, or joins an open particle group. Today exactly 24 catalog entries
set `iterated = true` (`grep -c 'e.iterated = true;'
src/effects/generated/effect_catalog.cpp`), plus `render/pointsEmit` (the
particle-group owner) and `render/loopBegin`/`loopEnd` (the loop-region
markers) -- and every one of them refuses at admission with
`missing_backend_program` (confirmed by a full-catalog sweep,
`sweep-out/full-catalog-check`, 36 effects / 273 `"exception"`-coded refusals,
all `Effect pass "..." unavailable: missing_backend_program`). None of the
167+ effects the corpus currently admits sets `iterated`, declares a loop role,
or declares/references a particle-state texture. `compute_iteration_groups`
therefore always partitions every admitted chain into single-step,
`iterated: false` groups, in original order -- structurally identical to the
existing flat `for (const auto& variant : chain.steps)` loop. Wiring groups into
`execute()` is consequently a pure refactor for every admission that exists
today: the non-iterated branch's code is untouched, byte-for-byte, and the new
`run_iterated_group` path is reachable only from a hand-built synthetic plan
(native tests) until a Family B/C/D/E kernel is admitted. Verified with a
`--variants 6` before/after sweep over every currently-admitted effect: zero
per-case differences (see the implementation report for the exact command and
result counts).
