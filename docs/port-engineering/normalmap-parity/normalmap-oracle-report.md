# Normalmap185 exact-parity oracle

Program `filter/normalMap:normalMap`; corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`; **no preprocessor defines**.

## The contracts this program exists to prove

`filter/normalMap` declares three **const** file-scope tables, and the parity target is the
transpiler's materialization, not GLSL semantics:

| Table | GLSL | JavaScript | Contract | Oracle-discriminable |
| --- | --- | --- | --- | --- |
| `SOBEL_OFFSETS` | `const ivec2[9]` | `[cpu_ivec2(...), ...]` | pooled `Int32Array` elements, exact int32 | yes |
| `SOBEL_X_KERNEL` | `const float[9]` | plain `Array` | **doubles**, never narrowed to f32 | **no** |
| `SOBEL_Y_KERNEL` | `const float[9]` | plain `Array` | **doubles**, never narrowed to f32 | **no** |

The two float tables are **not** oracle-discriminable, and this package never pretends otherwise.
Every element (`0.5`, `0`, `1` and their negations) is exactly representable in binary32 as well
as binary64, so no value in this program separates `std::array<double, 9>` from
`std::array<float, 9>`. `kernel_table_narrowing_axis` renders the narrowing mutant on every case
and records 0 changed lanes: it **cannot
diverge**, so it is not shipped as a control. The double contract is proven structurally, by the
emitted native type and by the JavaScript being a plain `Array`. A green parity run is not evidence
for it.

## Authority

This oracle is produced by the unmodified public canonicalFactory86 from an immutable noisemaker-for-cpu snapshot, executed through the pinned bindCanonicalKernel/GlslCpuRuntime/runPass path; no C++ output participates. The generator refuses to run unless
`kernelFactories.get(key) === canonicalKernelFactories[key]`, the factory is named
`canonicalFactory86`, its `Function.prototype.toString` SHA-256 is `9b1348836825b6efe90109747ca5ef341651527077d8ad7dbbcbc7080369842a`, neither
adapter table owns the key, `canonicalAdapterFactories` matches its
11-key census exactly, the key is absent from the
4-key `check_corpus._ADAPTERS` eligibility table
**parsed out of the live `tools/glslcpp/check_corpus.py`**
rather than transcribed, all six pinned CPU files match, and every module in the
22-file import closure resolves by real path
beneath the immutable snapshot. Bare module specifiers other than `node:` builtins are rejected,
and the live checkout is refused as a `--cpu-root`.

No absolute path is recorded anywhere in this package. The `--cpu-root` argument is stored as
`<immutable-cpu-snapshot-root>` and the rejected live checkout as
`<live-noisemaker-for-cpu-checkout>`, resolved at run time from
process.env.NOISEMAKER_FOR_CPU when set, else $HOME/platform/noisemaker-for-cpu. The gate therefore passes against a valid
snapshot at any path and still refuses the live checkout.

## Bindings, and what production actually binds

The program has exactly 5 runtime bindings:
`tileOffset`, `fullResolution`, `inputTex`, `size`, `motion`. There are no compile-time
defines.

`filter/normalMap` declares **no params**, so `createCanonicalBindings` leaves `size` as the
zero vec4 on every shipped render. Three consequences, all recorded as claim boundaries rather than
discovered later: `channelCount` is always 1, the entire `oklab_l_component` /
`srgb_to_linear` / `cbrt_safe` subtree is dynamically dead, and `main()`'s early return is
unreachable. Cases that bind a non-zero `size` are **synthetic ABI coverage** and are labelled
`synthetic-size` in the table below.

## Render fixtures

| Case | Size | Route | Input | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- | --- |
| normalmap-default-16x9 | 16x9 | production-binding-set | ramp | 5686c048f61e3ea8c07162321e56412341632e975ce79bf820e146c27223a124 | a69a90038473ed638c660304a1f9d5e184b9598917e81cd54b26d46c256a9d30 |
| normalmap-default-7x5 | 7x5 | production-binding-set | ramp | d1d4d14e36afaa87e10a4f0a7f978d41e5357d2cf039e038eb01862bbd3014aa | eb21e3d08b1705b1a56151e52e0c7eb29f0325898827296862a871734c350cc1 |
| normalmap-high-contrast-8x6 | 8x6 | production-binding-set | contrast | 53b925d36f1b422c9c78caed69edf5dc680b3b9e694453cb91ce7fae28fcf657 | dec920069ec31ed6fecda82708f08db32c497a0be177c6925babb67aca114e43 |
| normalmap-channelcount-2-8x6 | 8x6 | synthetic-size | ramp | 153c3f88be7aa805b3521608565feda200d0cd26d8b0f56cb8968ab31fa81175 | e4eec62fd2f39098e6c2d4c71d48c90bc143c2f8582d01867bbf63cfa5ccc615 |
| normalmap-channelcount-3-oklab-8x6 | 8x6 | synthetic-size | ramp | 1c4b5d54b0177cc3f053a20c46824be8a72041e945170175d8690f55c9fe28d4 | 05301491fc644e095c8d6821f32fc458517fd79c8e14cb6073bc08e1e90d0087 |
| normalmap-channelcount-4-clamped-8x6 | 8x6 | synthetic-size | wide | a14d32248ffd24ae4b7e88c162122f9e79935e1962e90172cd39002a553fe071 | db0ae687dceb79c1ef627e98c2483facdda86459faf6a434d49c4f81b3d40d66 |
| normalmap-explicit-size-larger-8x6 | 8x6 | synthetic-size | ramp | ae3d870a2dd6568f5eafe2890175799cbffeda3fdb8d2a2955773ae0b2631425 | 50d10af766c6dc377df110621b66c04b978a993f006708f31ec4764ee80d285d |
| normalmap-flat-alpha-8x6 | 8x6 | production-binding-set | flat | 0b87411c5672208865efaf35a1877527492f971c5f7574af0b4db2715f916495 | 633bccd2d81b7dcea74e902bc82411e35e7ee08ddcbbdc906c9440896021b104 |

Every case stores exact dimensions, the complete input texture as raw Float32 words, all
5 bindings with every vector lane as a hexadecimal f32 word, the
external `runPass` time/seed pair, the complete expected Float32 word array, the complete
independently captured RGBA8 byte array, finite/non-finite lane counts, and a SHA-256 over each
array. Every input lane is a small dyadic rational, so the input itself contributes no rounding.

## Coverage

| Axis | Bucket | Witnesses |
| --- | --- | --- |
| binding_set | production_size_is_the_zero_vec4 | normalmap-default-16x9, normalmap-default-7x5, normalmap-high-contrast-8x6, normalmap-flat-alpha-8x6 |
| binding_set | synthetic_non_zero_size | normalmap-channelcount-2-8x6, normalmap-channelcount-3-oklab-8x6, normalmap-channelcount-4-clamped-8x6, normalmap-explicit-size-larger-8x6 |
| channel_count_arm | one (texel.x, the only production-reachable arm) | normalmap-default-16x9, normalmap-default-7x5, normalmap-high-contrast-8x6, normalmap-explicit-size-larger-8x6, normalmap-flat-alpha-8x6 |
| channel_count_arm | two (texel.x again: a distinct source path, byte-identical to the <= 1 arm) | normalmap-channelcount-2-8x6 |
| channel_count_arm | three (oklab on raw texel.xyz) | normalmap-channelcount-3-oklab-8x6 |
| channel_count_arm | four (oklab again: the pre-clamp is redundant, byte-identical to arm three) | normalmap-channelcount-4-clamped-8x6 |
| dimension_source | textureSize_fallback | normalmap-default-16x9, normalmap-default-7x5, normalmap-high-contrast-8x6, normalmap-channelcount-2-8x6, normalmap-channelcount-3-oklab-8x6, normalmap-channelcount-4-clamped-8x6, normalmap-flat-alpha-8x6 |
| dimension_source | explicit_size_xy | normalmap-explicit-size-larger-8x6 |
| clamp01_saturation | saturates_at_one_bound | normalmap-default-16x9, normalmap-channelcount-2-8x6, normalmap-channelcount-4-clamped-8x6 |
| clamp01_saturation | interior_only | normalmap-default-7x5, normalmap-channelcount-3-oklab-8x6, normalmap-flat-alpha-8x6 |
| clamp01_saturation | saturates_at_both_bounds | normalmap-high-contrast-8x6, normalmap-explicit-size-larger-8x6 |
| input_range | inside_unit_interval | normalmap-default-16x9, normalmap-default-7x5, normalmap-high-contrast-8x6, normalmap-channelcount-2-8x6, normalmap-channelcount-3-oklab-8x6, normalmap-explicit-size-larger-8x6, normalmap-flat-alpha-8x6 |
| input_range | outside_unit_interval_including_negative_zero | normalmap-channelcount-4-clamped-8x6 |
| alpha_construction | uniform_one | normalmap-default-16x9, normalmap-default-7x5, normalmap-high-contrast-8x6, normalmap-channelcount-2-8x6, normalmap-channelcount-3-oklab-8x6, normalmap-channelcount-4-clamped-8x6, normalmap-explicit-size-larger-8x6 |
| alpha_construction | varying | normalmap-flat-alpha-8x6 |
| gradient_liveness | dx_and_dy_both_live | normalmap-default-16x9, normalmap-default-7x5, normalmap-high-contrast-8x6, normalmap-channelcount-2-8x6, normalmap-channelcount-3-oklab-8x6, normalmap-channelcount-4-clamped-8x6, normalmap-explicit-size-larger-8x6 |
| gradient_liveness | dx_and_dy_exactly_plus_zero | normalmap-flat-alpha-8x6 |
| wrap_limits | 16x9 | normalmap-default-16x9 |
| wrap_limits | 7x5 | normalmap-default-7x5 |
| wrap_limits | 8x6 | normalmap-high-contrast-8x6, normalmap-channelcount-2-8x6, normalmap-channelcount-3-oklab-8x6, normalmap-channelcount-4-clamped-8x6, normalmap-flat-alpha-8x6 |
| wrap_limits | 11x8 | normalmap-explicit-size-larger-8x6 |

## One-axis control group on `normalmap-default-16x9`

| Control | Axis | Expected | Observed | Result | Changed lanes |
| --- | --- | --- | --- | --- | ---: |
| external-pass-extreme | external runPass time/seed words (0x4f000000, 0xcf000000) | identical | identical | pass | 0 |
| motion-extreme | bound motion vec4 (0,0,0,0) -> (1,-1,1024,-0.5) | identical | identical | pass | 0 |
| tile-offset-extreme | bound tileOffset (0,0) -> (131072.1, 0.3) | identical | identical | pass | 0 |
| full-resolution-extreme | bound fullResolution (16,9) -> (1280,720) | identical | identical | pass | 0 |
| size-w-extreme | bound size.w 0 -> 12345.5 with size.xyz held at zero | identical | identical | pass | 0 |
| size-z-three | bound size.z 0 -> 3 | differs | differs | pass | 432 |
| size-xy-smaller | bound size.xy (0,0) -> (8,9) on a 16-wide surface | differs | differs | pass | 120 |

## Binding inertness census

| Binding | Probe | Versus baseline | Changed lanes |
| --- | --- | --- | ---: |
| motion | [1, -1, 1024, -0.5] | identical | 0 |
| motion | [-2147483648, 2147483647, 0.5, -0.5] | identical | 0 |
| motion | [1e-30, -1e+30, 3, 4] | identical | 0 |
| fullResolution | [1280, 720] | identical | 0 |
| fullResolution | [1, 1] | identical | 0 |
| fullResolution | [131072.1, 0.3] | identical | 0 |
| tileOffset | [131072.1, 0.3] | identical | 0 |
| tileOffset | [-16, -9] | identical | 0 |
| tileOffset | [1e+30, -1e-30] | identical | 0 |

a binding is recorded inert only after the anchor case is re-rendered with a deliberately extreme value and compared exactly. Inertness is a parity assertion: a port that wrongly made one of these live would differ from an oracle that is invariant.

## Amendment 11: two of design section 7's three mutants are the same function

| Case | Lanes differing from `normalmap-sobel-x-y-swapped` | Lanes differing from canonical |
| --- | ---: | ---: |
| normalmap-default-16x9 | 0 | 176 |
| normalmap-default-7x5 | 0 | 50 |
| normalmap-high-contrast-8x6 | 0 | 96 |
| normalmap-channelcount-2-8x6 | 0 | 64 |
| normalmap-channelcount-3-oklab-8x6 | 0 | 96 |
| normalmap-channelcount-4-clamped-8x6 | 0 | 96 |
| normalmap-explicit-size-larger-8x6 | 0 | 68 |
| normalmap-flat-alpha-8x6 | 0 | 0 |

SOBEL_X_KERNEL viewed as 3x3 is exactly the transpose of SOBEL_Y_KERNEL (X[3r+c] == Y[3c+r] for all nine, checked elementwise by this generator). Transposing every offset permutes the sample list by the involution s(3r+c) = 3c+r, so dx' = SUM X[s(j)]*v_j = SUM Y[j]*v_j = dy. The two mutants are therefore the same function of the input.

design section 7 asked for both. Two mutants that cannot be told apart cannot attribute a divergence to a contract, so only normalmap-sobel-x-y-swapped is carried in the disjoint ledger. This proof is what justifies dropping the other, and it is re-measured on every run rather than asserted in prose.

## Mutation discrimination, per case

| Mutant | Case | Class | Result | Changed lanes |
| --- | --- | --- | --- | ---: |
| normalmap-sobel-x-y-swapped | normalmap-default-16x9 | witness | differs | 176 |
| normalmap-sobel-x-y-swapped | normalmap-default-7x5 | witness | differs | 50 |
| normalmap-sobel-x-y-swapped | normalmap-high-contrast-8x6 | witness | differs | 96 |
| normalmap-sobel-x-y-swapped | normalmap-channelcount-2-8x6 | witness | differs | 64 |
| normalmap-sobel-x-y-swapped | normalmap-channelcount-3-oklab-8x6 | witness | differs | 96 |
| normalmap-sobel-x-y-swapped | normalmap-channelcount-4-clamped-8x6 | witness | differs | 96 |
| normalmap-sobel-x-y-swapped | normalmap-explicit-size-larger-8x6 | witness | differs | 68 |
| normalmap-sobel-x-y-swapped | normalmap-flat-alpha-8x6 | control | identical | 0 |
| normalmap-alpha-source-transposed | normalmap-default-16x9 | control | identical | 0 |
| normalmap-alpha-source-transposed | normalmap-default-7x5 | control | identical | 0 |
| normalmap-alpha-source-transposed | normalmap-high-contrast-8x6 | control | identical | 0 |
| normalmap-alpha-source-transposed | normalmap-channelcount-2-8x6 | control | identical | 0 |
| normalmap-alpha-source-transposed | normalmap-channelcount-3-oklab-8x6 | control | identical | 0 |
| normalmap-alpha-source-transposed | normalmap-channelcount-4-clamped-8x6 | control | identical | 0 |
| normalmap-alpha-source-transposed | normalmap-explicit-size-larger-8x6 | control | identical | 0 |
| normalmap-alpha-source-transposed | normalmap-flat-alpha-8x6 | witness | differs | 30 |

Both ledger mutants are independent one-anchor/one-replacement rewrites of the canonical factory
text, compiled and rendered by this generator. The expected outcome is frozen **per case and per
mutant**; `--check` fails if any single cell flips, in either direction.

The ledger mutants must have DISJOINT witness sets. They carry different contracts -- the kernel tables versus the alpha source coordinate -- and a case that witnessed both could not attribute a divergence to one of them. This is enforced, not merely observed: the generator throws and the materializer rejects the document if any case appears in two witness sets.

Disjointness is engineered and stated, not accidental. Every kernel witness case carries a uniformly opaque input, so transposing the alpha-source coordinate fetches alpha 1 either way; the one case with a varying alpha has a constant value map, so dx and dy are exactly +0 and swapping the kernels is a no-op. Both halves are re-measured every run.

### Kernel-table mutants deliberately kept out of the disjoint ledger

| Mutant | Case | Result | Changed lanes |
| --- | --- | --- | ---: |
| normalmap-sobel-x-negated | normalmap-default-16x9 | differs | 80 |
| normalmap-sobel-x-negated | normalmap-default-7x5 | differs | 25 |
| normalmap-sobel-x-negated | normalmap-high-contrast-8x6 | differs | 48 |
| normalmap-sobel-x-negated | normalmap-channelcount-2-8x6 | differs | 26 |
| normalmap-sobel-x-negated | normalmap-channelcount-3-oklab-8x6 | differs | 48 |
| normalmap-sobel-x-negated | normalmap-channelcount-4-clamped-8x6 | differs | 48 |
| normalmap-sobel-x-negated | normalmap-explicit-size-larger-8x6 | differs | 29 |
| normalmap-sobel-x-negated | normalmap-flat-alpha-8x6 | identical | 0 |
| normalmap-sobel-x1-perturbed | normalmap-default-16x9 | differs | 252 |
| normalmap-sobel-x1-perturbed | normalmap-default-7x5 | differs | 60 |
| normalmap-sobel-x1-perturbed | normalmap-high-contrast-8x6 | differs | 12 |
| normalmap-sobel-x1-perturbed | normalmap-channelcount-2-8x6 | differs | 84 |
| normalmap-sobel-x1-perturbed | normalmap-channelcount-3-oklab-8x6 | differs | 94 |
| normalmap-sobel-x1-perturbed | normalmap-channelcount-4-clamped-8x6 | differs | 87 |
| normalmap-sobel-x1-perturbed | normalmap-explicit-size-larger-8x6 | differs | 84 |
| normalmap-sobel-x1-perturbed | normalmap-flat-alpha-8x6 | differs | 96 |

| Mutant | Witness count | Relation to `normalmap-sobel-x-y-swapped`'s witness set |
| --- | ---: | --- |
| normalmap-sobel-x-negated | 7 | identical |
| normalmap-sobel-x1-perturbed | 8 | strict-superset |

Amendment 11 suggests replacing the retracted mutant with a kernel-element perturbation. Measured,
each candidate's witness set **contains** `normalmap-sobel-x-y-swapped`'s, and the two rows are not
the same relation: the perturbation is a genuine strict superset, while
`normalmap-sobel-x-negated` witnesses **exactly the same seven cases** -- on this case set it is
wholly indiscriminable from the retained mutant, which is stronger than a superset, not weaker.
Either way neither can be a second *disjoint* ledger entry on any case set that also covers the
program's real behaviour. Both relations are re-derived from the stored rows on every run. They ship
as a census with per-case results, and the ledger's second slot is filled by a mutant on a different
contract entirely -- which is what amendment 11's own criterion, "something no offset permutation can
produce", admits.

## The `as_u32` round axis is unsatisfiable, and proven invariant

`as_u32` has **3 call sites**, not one:
`var count = as_u32(raw_value);`, `var width = as_u32(size[0]);`, `var height = as_u32(size[1]);`.

Math.round and round-half-away-from-zero differ ONLY on negative half-integers, and every negative result is collapsed by the max(..., 0) clamp. The discriminating domain is empty because of the clamp, not because this oracle's bindings happen to miss it, so no binding set can make this mutant discriminate.

A 40022-sample scan over half-integers, quarter-integers,
ties, signed zero, NaN, the infinities and the 2^23 boundary finds
**7505 values where the two rounders
disagree** and **0 divergences in
`as_u32`**. The rendered `normalmap-round-half-away` mutant changes
0 lanes across every case.

**This oracle package can prove NOTHING WHATSOEVER about the round contract for this program. The axis is recorded and proven invariant; it is not waived, and it is not evidence.**

## Per-pixel re-evaluation is measured equivalent

shadow all three factory-scope tables with identical declarations at the top of main(): 0
changed lanes across every case.

Design amendment 15 retracts section 3.1's reason. Literal-only initializers are NECESSARY BUT NOT SUFFICIENT. The operative reason is ELEMENT MATERIALIZATION: SOBEL_X_KERNEL and SOBEL_Y_KERNEL are plain Number arrays, and SOBEL_OFFSETS holds pooled Int32Arrays whose pool index beginPixel restores to a snapshotted base. See pooled_table_hazard.

## Amendment 15: the pooled-table hazard, reproduced

beginPixel snapshots signedBaseIndices on first call and resets the integer index to that base (glsl-runtime.js:132-137), so a factory-scope pooled Int32Array survives. The float pool has no such base -- beginPixel does this.indices.fill(0) -- so the first per-pixel scratch allocation aliases and overwrites a factory-scope PooledFloat32Array.

An instrumented probe factory declares a factory-scope `PooledFloat32Array` table beside a pooled
`ivec2` table and publishes both. Observed lanes:
`0.5, 2, -11, -44` --
the float table has been clobbered from its `111` / `444` initializers, while the integer table
still reads `-11` / `-44`.

**This mechanism must NOT be extended to a float-vector element type (vec2[N], vec3[N], vec4[N] const globals) without re-deriving the pool argument from glsl-runtime.js. The predicate set would admit such a table and the port would silently disagree with the authority. The element-type check must be an allowlist, never a denylist and never "any approved type".**

## What each `value_map_component` arm is worth

| Input | `size.z` | Resolved channelCount | Float32 SHA-256 |
| --- | ---: | ---: | --- |
| ramp (lanes inside [0, 1]) | 0 | 1 | 153c3f88be7aa805b3521608565feda200d0cd26d8b0f56cb8968ab31fa81175 |
| ramp (lanes inside [0, 1]) | 1 | 1 | 153c3f88be7aa805b3521608565feda200d0cd26d8b0f56cb8968ab31fa81175 |
| ramp (lanes inside [0, 1]) | 2 | 2 | 153c3f88be7aa805b3521608565feda200d0cd26d8b0f56cb8968ab31fa81175 |
| ramp (lanes inside [0, 1]) | 3 | 3 | 1c4b5d54b0177cc3f053a20c46824be8a72041e945170175d8690f55c9fe28d4 |
| ramp (lanes inside [0, 1]) | 4 | 4 | 1c4b5d54b0177cc3f053a20c46824be8a72041e945170175d8690f55c9fe28d4 |
| wide (lanes outside [0, 1]) | 0 | 1 | ad3d28b9f172ed483241e36547b9eca0e9a637aaa0d49329e8883877c1831dec |
| wide (lanes outside [0, 1]) | 1 | 1 | ad3d28b9f172ed483241e36547b9eca0e9a637aaa0d49329e8883877c1831dec |
| wide (lanes outside [0, 1]) | 2 | 2 | ad3d28b9f172ed483241e36547b9eca0e9a637aaa0d49329e8883877c1831dec |
| wide (lanes outside [0, 1]) | 3 | 3 | a14d32248ffd24ae4b7e88c162122f9e79935e1962e90172cd39002a553fe071 |
| wide (lanes outside [0, 1]) | 4 | 4 | a14d32248ffd24ae4b7e88c162122f9e79935e1962e90172cd39002a553fe071 |

value_map_component has FIVE source arms and exactly TWO behaviours. size.z 0, 1 and 2 collapse because both the `<= 1` and the `== 2` arm return texel.x. size.z 3 and 4 collapse because arm 4's clamp(texel.xyz, 0, 1) is REDUNDANT: oklab_l_component already applies clamp01 to each channel before srgb_to_linear, so pre-clamping the argument cannot change the result -- measured byte-identical even on an input whose lanes leave [0, 1].

Five source arms, **two** behaviours. `normalmap-channelcount-2-8x6` pins a distinct **source path**
whose output is byte-identical to the `channelCount <= 1` arm, and `normalmap-channelcount-4-clamped-8x6`
pins one that is byte-identical to arm three: the `channelCount == 4` arm's clamp(texel.xyz, vec3(0), vec3(1)) is idempotent with oklab_l_component's own per-channel clamp01 and changes no pixel. The channelCount-4 case is still the only case whose input lanes leave [0, 1] and include exact -0, which is what reaches srgb_to_linear's low arm and cbrt_safe's value == 0 arm; it is NOT coverage of a distinct value map.
Neither is coverage of a second value map, and the generator throws if either equivalence stops
holding or if `oklab_l_component`'s three per-channel `clamp01` calls disappear.

## The double accumulator

| Case | Result | Changed lanes |
| --- | --- | ---: |
| normalmap-default-16x9 | identical | 0 |
| normalmap-default-7x5 | identical | 0 |
| normalmap-high-contrast-8x6 | identical | 0 |
| normalmap-channelcount-2-8x6 | identical | 0 |
| normalmap-channelcount-3-oklab-8x6 | differs | 48 |
| normalmap-channelcount-4-clamped-8x6 | differs | 46 |
| normalmap-explicit-size-larger-8x6 | identical | 0 |
| normalmap-flat-alpha-8x6 | identical | 0 |

The witnesses are exactly the cases whose value map leaves the dyadic grid. Every input lane is a small dyadic rational and both kernels are powers of two, so on the channelCount <= 2 arms every partial sum is exact in binary32 as well as binary64 and narrowing changes nothing. The oklab arms produce full-precision doubles, where narrowing each step is observable.

every witness below is also a witness of normalmap-sobel-x-y-swapped, so this census is NOT attributive on its own. It is recorded because a green parity run on its witness cases is real evidence that the native accumulator is a double.

## `fragColor` persistence, quarantined

fragColor is a factory-scope `new Float32Array([0, 0, 0, 0])`. It is NOT reset per pixel, so a pixel that takes main()'s early return writes the PREVIOUS pixel's colour. With size.x = 5 on an 8-wide surface, the last three columns of every row smear the last rendered pixel of that row.

UNREACHABLE through the shipped binding set. `filter/normalMap` declares no params, so createCanonicalBindings leaves `size` as the zero vec4 and width/height always come from textureSize(inputTex, 0); global_id is then always in range. Only a host that binds a non-zero `size` smaller than the destination reaches the early return.

**src/pass_runner.cpp declares `glsl::Vec4 output;` INSIDE the per-pixel loop and the emitted `pixel()` assigns `output` only on the path that reaches the end of main(). A bare `return;` therefore leaves `output` default-initialized -- and glsl::Vec holds `std::array<T, N> lanes_{}`, a default member initializer, so the defaulted constructor VALUE-initializes and the lanes read as exactly zero. This is a PARITY divergence, not undefined behaviour and not a read of an uninitialized object: JavaScript writes the previous pixel's colour where native writes (0, 0, 0, 0). The arrays are published so the boundary is visible and testable, NOT so a parity test can be written against them unchanged.**

The configuration's complete expected arrays are stored under
`fragcolor_persistence_witness` and emitted into the native include behind
`kFragColorPersistenceNativelyExpressible = false`, so the boundary is visible rather than silently
absent. normalmap-fragcolor-reset-per-pixel would be an ideal second disjoint ledger entry -- its only witness is this configuration -- but putting it in the ledger would gate the slice on a native ABI gap that is out of this package's scope. It is recorded in full instead.

## Claim boundaries

- Every element of both tables (0.5, 0, 1 and their negations) is exactly representable in binary32 AND binary64, so no value in this program distinguishes std::array<double, 9> from std::array<float, 9>. The double contract is proven STRUCTURALLY -- by the emitted native type and by the JS being a plain Array rather than a Float32Array -- and a green pixel run is not evidence for it. Shipping such a mutant as a control would be shipping a mutant that cannot diverge.
- This oracle package can prove NOTHING WHATSOEVER about the round contract for this program. The axis is recorded and proven invariant; it is not waived, and it is not evidence.
- Design amendment 15 retracts section 3.1's reason. Literal-only initializers are NECESSARY BUT NOT SUFFICIENT. The operative reason is ELEMENT MATERIALIZATION: SOBEL_X_KERNEL and SOBEL_Y_KERNEL are plain Number arrays, and SOBEL_OFFSETS holds pooled Int32Arrays whose pool index beginPixel restores to a snapshotted base. See pooled_table_hazard.
- This mechanism must NOT be extended to a float-vector element type (vec2[N], vec3[N], vec4[N] const globals) without re-deriving the pool argument from glsl-runtime.js. The predicate set would admit such a table and the port would silently disagree with the authority. The element-type check must be an allowlist, never a denylist and never "any approved type".
- filter/normalMap declares no params, so `size` is the zero vec4 on every shipped render. channelCount is therefore always 1, the whole oklab_l_component / srgb_to_linear / cbrt_safe subtree and the channelCount 2/3/4 arms are dynamically dead, and main()'s early return is unreachable. The synthetic-size cases here cover the ABI, not the shipped route, and must never be cited as evidence about production behaviour.
- fragColor's cross-pixel persistence is real in the JavaScript and is stored in fragcolor_persistence_witness, but the native pixel ABI cannot express it today. It is NOT a parity case and NOT a ledger mutant.
- Normalized/typed source, function, interface, and whole-program hashes are the frontend profiles' authority and are deliberately not restated here.

## Regeneration

```sh
node docs/port-engineering/normalmap-parity/normalmap_oracle_generator.mjs --write --cpu-root "$CPU_ROOT"
node docs/port-engineering/normalmap-parity/normalmap_oracle_generator.mjs --check --cpu-root "$CPU_ROOT"
python3 -B tools/glslcpp/generate_normalmap_native_oracle_include.py --write
python3 -B tools/glslcpp/generate_normalmap_native_oracle_include.py --check
python3 -B tools/glslcpp/generate_normalmap_native_oracle_include.py --self-test
```

Both generators are fail-closed and check mode performs no writes.
