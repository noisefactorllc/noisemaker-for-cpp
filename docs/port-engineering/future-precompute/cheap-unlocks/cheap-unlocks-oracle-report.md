# Cheap-unlocks oracle report -- two small clusters, four programs

Combined summary of two hermetic JS-golden oracle generators built for the
future bit-exact C++20 port, covering the two smallest/cheapest unlock
clusters identified by prior precompute work:

- **Cluster 1 -- loop-proof fingerprint reuse** (3 programs):
  `filter/lightLeak:lightLeak`, `filter/parallax:parallax`,
  `filter/reindex:nmReindexStats`. Generator:
  `loopproof_oracle_generator.mjs` / `loopproof-oracles.json` /
  `loopproof-oracle-report.md`.
- **Cluster 2 -- bitwise-only** (1 program): `synth/bitwise:bitwise`.
  Generator: `bitwise_oracle_generator.mjs` / `bitwise-oracles.json` /
  `bitwise-oracle-report.md`.

Corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`, resolved from its
`manifest.json` (never from a glob, per the roadmap's own documented trap).
Both generators are hermetic (only import from `noisemaker-for-cpu`, which is
read-only in this task), pin runtime file hashes before rendering a single
pixel, and are byte-identical across two consecutive `--check` runs (verified
below). Nothing under `noisemaker-for-cpp` or `noisemaker-for-cpu` was
modified; no `git` command was run anywhere in this task.

## Per-program case counts

| Cluster | Program | `program_key` | Eligible cases | Diagnostic cases | Total | Mutations |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | lightLeak | `filter/lightLeak:lightLeak` | 4 | 1 | 5 | 2 |
| 1 | parallax | `filter/parallax:parallax` | 4 | 1 | 5 | 2 |
| 1 | reindexStats | `filter/reindex:nmReindexStats` | 4 | 0 | 4 | 2 |
| 2 | bitwise | `synth/bitwise:bitwise` | 5 | 1 | 6 | 5 |
| **Total** | | | **17** | **3** | **20** | **11** |

reindexStats has no diagnostic case: `fragCoord % TILE_SIZE == 0` is
trivially true at `(0,0)` for **any** `TILE_SIZE` value, so the mutated site
is reached by construction for every non-empty render -- documented rather
than fabricating a synthetic reach=false case that would not reflect
anything real about this program.

## Cluster 1 -- which three programs, and why exactly these three

Per `docs/port-engineering/loopproof/loop-proof-study.md` SS4, six
programs were originally claimed as "`source-global-literal-int-v1` reuse,
just new fingerprints." Re-verified against the mechanism's actual
requirement (`initializer.kind == "literal"`, not a computed expression):
only **3 of 6** structurally qualify AND need no budget-cap change --
`lightLeak` (`POINT_COUNT = 6`), `parallax` (`MARCH_STEPS = 32`),
`reindexStats` (`TILE_SIZE = 8`). `dither`'s `FS_ERR_W` initializer is
`binary` (`FS_BLOCK + FS_APRON_MAX + FS_RPAD + 1`), not `literal` -- excluded
per the task brief. `reindexReduce` (`MAX_TILE_DIM = 512`,
`lexical_product` ~64x over cap) and `mandelbrot` (`MAX_ITER = 500`,
`trip_count` ~4x over cap) qualify structurally but additionally need a
numeric budget-cap increase -- not fingerprint-only, excluded per the task
brief.

## Cluster 1 -- evidence that trip count is genuinely discriminated

Every mutation in this cluster swaps the compiled JS's `var <CONST> =
<original>;` declaration for a plausible-but-wrong literal (an off-by-one
value AND a materially different "swap" value, two mutations per program)
and asserts, at generation time, nonzero byte-divergence among reach-eligible
cases and zero divergence among non-reach-eligible (diagnostic) cases. A
generator run that failed to discriminate throws instead of shipping.

- **lightLeak** (`POINT_COUNT`, Voronoi seed count): both mutations (6->5,
  6->3) diverge on **4/4** eligible cases, 0/1 on the diagnostic
  (`alpha<=0` early-return, proven never to reach `voronoiCell()`).
  `POINT_COUNT` determines which of the candidate seed points is nearest for
  most pixels, so a wrong count changes the leak color/wormhole distortion
  materially, not marginally.
- **parallax** (`MARCH_STEPS`, ray-march step count): both mutations (32->31,
  32->16) diverge on **4/4** eligible cases, 0/1 on the diagnostic (a
  deliberately flat, height >= 1 height map that forces the `if (f > 0.0)`
  guard false before the loop is ever entered). **This required an explicit
  redesign, caught by verification rather than assumed correct**: the first
  height-map design (small, same-resolution-as-canvas patterned noise) made
  the off-by-one mutation diverge on only **1/4** cases -- traced to
  `SHIFT_SCALE = 0.15` (parallax.glsl) capping the ray's total UV traversal
  to a fraction of one texel at that scale, so the sampled height-vs-t curve
  is close to affine and the loop's own linear-interpolation refine step
  recovers nearly the same crossing point regardless of step count. This is
  precisely the "loop body is idempotent" / "result saturates" trap the task
  warns about. The height map was redesigned to a 16x16 deterministic
  diagonal-gradient-plus-ripple field with the full `0.05..0.95` dynamic
  range, re-verified empirically against the real mutations for every
  direction/pivot/canvas-size combination before being locked in -- now 4/4
  for both mutations. See `parallaxHeightMap()` and its header comment in
  `loopproof_oracle_generator.mjs` for the full derivation.
- **reindexStats** (`TILE_SIZE`, tile-anchor grid + reduction window): both
  mutations (8->7, 8->4) diverge on **3/4** and **4/4** eligible cases
  respectively. The off-by-one mutation's one non-divergent case
  (`single-tile-small`, confirmed by inspecting `case_results` in the JSON,
  not assumed) is the smallest, 6x5 canvas: both the real (`TILE_SIZE=8`)
  and mutated (`TILE_SIZE=7`) reductions break their inner loops on
  `px/py >= texSize` (the canvas dimensions), not on `TILE_SIZE` itself, and
  since 6x5 is smaller than BOTH 7 and 8, that early-break clause makes the
  aggregated pixel SET identical either way -- a genuine, understood
  degeneracy specific to "canvas smaller than both the real and mutated tile
  size," not a coverage gap. The remaining three (larger) cases, and the
  swap mutation on all four, are not subject to this degeneracy and diverge
  fully, so `TILE_SIZE` remains a proven discriminator. `TILE_SIZE` governs
  both which pixels are tile anchors and the reduction loop bound, so a wrong
  value generally changes which pixels carry output at all, not just the
  aggregated value.

## Cluster 2 -- which shift semantics `synth/bitwise:bitwise` actually gets

**Finding, stated explicitly per the task's instruction: `synth/bitwise:bitwise`
has ZERO shift-operator (`<<`, `>>`) sites.** The bitops report's headline
hazard -- "`glsl-transpiler` emits JavaScript's **signed** `>>` for a GLSL
`uint >> uint` whenever the enclosing function is not a recognized canonical
idiom" -- does **not** apply to this program. Verified two independent ways,
both live and machine-asserted in `loadProgram()` (the generator throws if
either check fails):

1. `grep -n '<<\|>>' sources/synth/bitwise/bitwise.glsl` -- zero matches
   across all 90 lines of the pinned corpus source.
2. A regex scan of `canonicalFactory244.toString()` (the actual JS-golden
   reference this oracle freezes) -- zero `<<`/`>>` substrings anywhere in
   the compiled factory body. `bitOp()` contains only `r = a ^ b`,
   `r = a & b`, `r = a | b`, `r = ~(a & b)`, `r = ~(a ^ b)` (plus the
   pre-existing, already-admitted `*`/`+`/`-` arithmetic branches); `main()`
   has two more scalar `^` sites (`x ^= seed`, `y ^= seed*3`) and nothing
   else touches a bit operator.

**Consequence**: this program's entire new-capability surface is scalar
signed-`int` `&`, `|`, `^`, unary `~` (and their `op=3`/`op=4` nand/xnor
combinations) -- governed only by Hazard #2 from `bitops-precompute.md`
(JS's ToInt32-based bitwise operators already match C++20 two's-complement
`int32_t` bit-for-bit) and **not** Hazard #1 (signed-vs-logical shift) or
Hazard #3 (shift-count masking), both structurally inapplicable: there is no
shift operator, so there is no shift semantics to get wrong and no shift
count to mask. A shift-count-masking test was deliberately **not**
constructed, because fabricating one would misrepresent this program.

**High-bit-set operand confirmation**: every non-diagnostic case supplies at
least one operand with the int32 sign bit set -- mask values at or composed
around `INT32_MIN`/`INT32_MAX` or with only bit 31 set (`-2147483648`,
`2147483647`, `-65536`, `-3`), and/or `seed`/`offsetX`/`offsetY` values at or
near `INT32_MIN`/`INT32_MAX` (`-1`, `-2000000000`, `2147483647`,
`+-1500000000`/`+-2000000000`) that XOR directly into the per-pixel integer
coordinates before every `bitOp()` call. This mirrors the task's stated
intent for the shift hazard (operands with the high bit set), applied here to
the hazard that actually governs this program: an implementation that widens
to float, uses unsigned-only arithmetic, or gets two's-complement `~` wrong
would diverge on exactly these operands, while a small-positive-only test
suite would never catch it.

## Mutation tables

### Cluster 1

| Mutation | Program | Kind | New value | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| lightLeak-point-count-minus-one | lightLeak | off-by-one | 5 | 4 | 4 | 1 | 0 |
| lightLeak-point-count-swap | lightLeak | swap | 3 | 4 | 4 | 1 | 0 |
| parallax-march-steps-minus-one | parallax | off-by-one | 31 | 4 | 4 | 1 | 0 |
| parallax-march-steps-swap | parallax | swap | 16 | 4 | 4 | 1 | 0 |
| reindexStats-tile-size-minus-one | reindexStats | off-by-one | 7 | 4 | 3 | 0 | 0 |
| reindexStats-tile-size-swap | reindexStats | swap | 4 | 4 | 4 | 0 | 0 |

### Cluster 2

| Mutation | Op mutated to | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| bitwise-xor-and-confusion | xor -> and | 1 | 1 | 5 | 0 |
| bitwise-and-or-confusion | and -> or | 1 | 1 | 5 | 0 |
| bitwise-or-xor-confusion | or -> xor | 1 | 1 | 5 | 0 |
| bitwise-nand-nor-confusion | nand -> nor | 1 | 1 | 5 | 0 |
| bitwise-xnor-nand-confusion | xnor -> nand | 1 | 1 | 5 | 0 |

Every non-reaching case shows exactly zero divergence for every mutation in
both clusters -- each mutation is exactly scoped to its own site/branch, not
leaking into unrelated code paths. Cluster 2's `mask=0` diagnostic case
reaches none of the five operator mutations by construction (`r = r & 0`
collapses to `0` regardless of which operator computed the pre-mask value,
so the mutated and real renders are identical there for a structural reason,
not a coverage gap) -- separately, that same case is the oracle's proof that
`mask=0` produces JS's `x/0` -> `NaN` propagation (27/36 lanes nonfinite, the
3 color channels across all 9 pixels; alpha is always 1 and stays finite),
not a silently-substituted value a C++ divide-by-zero guard might produce.

## Other non-negotiable requirements

- **Intent verification (reserved top-level keys)**: every case in both
  generators is rendered through a `renderCase()` that refuses to build if
  `uniforms` illegally contains one of the nine reserved top-level keys
  (`resolution`, `fullResolution`, `tileOffset`, `aspectRatio`, `aspect`,
  `time`, `globalTime`, `deltaTime`, `frame`), and independently
  re-reconstructs `createCanonicalBindings()`'s output to assert the kernel's
  own bound `time`/`tileOffset`/`fullResolution` AND every declared
  per-program uniform equal the caller's intended values, bit-for-bit
  (`f32Bits` comparison). No case in either oracle was found to violate this.
- **Defines bound as uniforms, not preprocessed**: inapplicable to both
  clusters -- all four programs authorize the empty define map `{}`,
  confirmed live via `tools.glslcpp.generate_typed_slice._defaults(repo,
  key)` for all four keys in this session, and independently by reading
  every source file (no effect-specific `#ifdef`/`#define` anywhere; only
  the universal `#ifdef GL_ES` guard in two of the four, and no preprocessor
  directive at all in the other two).
- **Reachability**: all four programs' mutated sites are called directly
  from `main()` with no intervening dispatch -- `lightLeak`'s
  `voronoiCell()`, `parallax`'s ray-march loop, `reindexStats`'s reduction
  loop, and `bitwise`'s `bitOp()` are each invoked unconditionally (or, for
  `lightLeak`/`parallax`, conditionally on a uniform whose both branches this
  oracle's diagnostic case set exercises) directly inside `main()`.
  `lightLeak`, `parallax`, AND `reindexStats` are all three members of
  `loop-proof-study.md`'s "the 16" terminal loop-shape programs, and SS6 of
  that study independently confirms "all 16 terminal programs'
  unproved-loop-containing functions are reachable from `main()`" via a real
  call-graph BFS -- corroborating (not superseding) this generator's own
  direct-source-reading confirmation.
- **`--check` determinism**: both generators regenerate in memory and
  compare byte-for-byte against the file on disk; both pass on two
  consecutive runs (see below).

```
$ node loopproof_oracle_generator.mjs --check
loopproof oracle fixture ok (3 programs, 14 cases, 6 mutations)

$ node bitwise_oracle_generator.mjs --check
bitwise oracle fixture ok (1 program, 6 cases, 5 mutations)
```

## `filter/reindex:nmReindexStats` -- adapter-override finding

This program's public factory (`kernelFactories.get(key)`) is **not** its
canonical factory: `canonicalAdapterFactories['filter/reindex:nmReindexStats']`
is `reindexStatsFactory` (`noisemaker-for-cpu/src/effects/adapters/f32-color.js`
:56-79), a hand-written, performance-optimized reimplementation used by the
live app that **hard-codes tile size 8 directly** rather than reading a
`TILE_SIZE` variable at all -- confirmed live in `loadProgram()` (the
generator throws if this claim is ever wrong). The grade and derivative
oracle generators both required (and asserted) no adapter override for every
program they covered; this is the first program in this whole porting
project's oracle history to break that precondition. This does not
invalidate the oracle: the C++ port's ground truth is the corpus GLSL ->
typed-IR -> canonical-kernel pipeline (`tools/glslcpp`), which corresponds
exactly to `canonicalKernelFactories['filter/reindex:nmReindexStats']`
(`canonicalFactory120`, the literal transpilation of the pinned corpus
source), never to the hand-optimized adapter -- so `loopproof_oracle_generator.mjs`
renders exclusively through the canonical factory, bypassing the public
`kernelFactories` map that would silently prefer the adapter for this one
program. The adapter's independent, hand-written commitment to exactly 8 is
corroborating (not authoritative) evidence that `TILE_SIZE=8` is the
intended value.

## What could not be constructed or verified

- **A genuine reach=false diagnostic case for `reindexStats`**: not
  constructible. `fragCoord % TILE_SIZE == 0` is trivially true at `(0,0)`
  for any `TILE_SIZE`, so the mutated site is reached by every non-empty
  render. Documented rather than fabricated.
- **A shift-count-masking test for `synth/bitwise:bitwise`**: not
  constructible, and deliberately not fabricated -- the program has zero
  shift operators (see the shift-semantics finding above). Any such test
  would misrepresent this program's actual compiled JS.
- **Full divergence (4/4, not 3/4) for `reindexStats-tile-size-minus-one`**:
  the off-by-one mutation's non-divergence on the smallest (6x5) case is
  fully explained (both `TILE_SIZE=8` and `TILE_SIZE=7` break their
  reduction loops on the canvas dimensions before reaching either tile-size
  bound, since 6x5 is smaller than both -- a genuine structural degeneracy,
  not a mystery gap) but a fifth case specifically sized to avoid that
  degeneracy (e.g. a canvas between 7 and 8 pixels wide/tall on the relevant
  axis) was not added, since the swap mutation already proves the site is a
  genuine discriminator and the task requires verifying divergence exists,
  not that every mutation diverges on every case.
