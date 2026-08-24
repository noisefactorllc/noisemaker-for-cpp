# Independent rereview of the frozen Task 21 Degauss brief

## Decision

**CHANGES REQUESTED.** The frozen brief at SHA-256
`456f88940ab6e6f9b2afea81737df015b988d794759f57271c07843d4b19e5af`
has no P0 or P1 scope/semantic defect, but it has two P2 acceptance-mechanics
defects. Correct both and refreeze/rereview the brief before implementation.

This was a read-only review. I did not edit the brief or repository and used no
Git command. This requested `/tmp` review is the only written artifact.

## Findings

### P2 — corpus verification command cannot run as written

Brief line 660 specifies:

```sh
python3 tools/glslcpp/check_corpus.py
```

The current command requires exactly one of `--check` or `--report`; the brief's
command exits with argparse usage and status 2. The acceptance command must be:

```sh
python3 tools/glslcpp/check_corpus.py --check
```

This is fail-loud rather than a silent proof bypass, but it makes the frozen
verification block non-executable and therefore blocks approval.

### P2 — generated/native `main` extraction and stack frame do not exist

Brief lines 243-250 require a native chain `pixel -> main ->
warped_channel_value`; line 708 searches generated code for `void main`; lines
717-720 require brace extraction of both generated `main` and `pixel`; and the
stack guidance includes `main` as a separate compiler frame.

The typed IR does contain source `main@56` with 27 top-level statements, so the
source/tree assertions are valid. The C++ emitter deliberately excludes
`main` from emitted helper declarations/definitions and writes its statements
directly into `void pixel(...)`. An independent in-memory Degauss emission
contained one `pixel` definition and no `main` definition or call.

The corrected native contract is:

```text
pixel [contains source main body]
  -> warped_channel_value
     -> compute_noise_value -> simplex_noise -> permute/mod289/taylor helpers
     -> sample_bilinear -> wrap_float/wrap_index/fetch_texel
```

Keep the typed-AST count of five `texelFetch(...,0)` sites as one in source
`main` and four in source `sample_bilinear`. For generated-code tests, require
one `fetch_texel` call in `pixel` and four in `sample_bilinear`; extract `pixel`,
not a nonexistent C++ `main`. Stack evidence must report `pixel` and reachable
helpers, not require a `main` `.su` record. This also removes `main` from the
generated `rg`/function-extraction target while retaining it in typed-tree
tests.

## Recomputed provenance

All frozen input artifact hashes match:

| Artifact | Recomputed SHA-256 |
| --- | --- |
| `task-21-frontier-audit.md` | `2f4665fa7a7d6471291030c02b3e259a797a95d33dd15dabd3b10433749ec7b0` |
| `task-21-oracle-generator.mjs` | `0c1f12904e1c17a39c61055596be9f0d46ecded252a9d5c7cf1339653472c5c9` |
| `task-21-oracles.json` | `bddb1ca8f8b7a8b905412318c48414594736ca4a972c440da7e8c3525b31bb38` |
| `task-21-oracle-report.md` | `4196f7a238c63eadb2e167b3f76528b620cea56fabad999525c8fbc5826f02fc` |

Independent source analysis reproduced:

| Lock | Recomputed value |
| --- | --- |
| Raw source | 10,803 bytes; `915f208e47a5bf012a3e0583e03a7ee888b7103d5834b386d32c916b8715050c` |
| Normalized source | 10,512 bytes; `7d413b240236506511f405319025281a92eb1108c6193ef26a6d0d7bcbae7560` |
| Function tuple | 17 functions; `f68d742e44e341c1332f8c37ac8544aaa8c5bef979e496a27d45ac28ba48f95a` |
| Whole profile | `73e7e3e3b5e0b7ee9b4e1558d51fc14a01e9820c89674a0b5e42e568bec8d13d` |
| Interface profile | `6ceb3a3a3c7b0263b29d9950790bbe24b186759a4048b593b0a5447b733ae227` |
| Loop proof | 0 loops, 0 unproved, depth/product/charge 0, acyclic |
| Foreign proof fields | Task 17/18/19/20 all `None` |

All 17 per-function IDs, statement counts, and hashes in the brief matched the
independently analyzed typed tree.

An independent Node import of the canonical CPU catalog reproduced:

- factory name `canonicalFactory45`;
- factory-text SHA-256
  `f515a7ac409c98fc420d9fa9a7e460eb37018b34e3be40419191fc7655a29c38`;
- canonical runtime SHA-256
  `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`.

The source interface, sampler S1, uniform/output IDs, route, metadata defaults,
TAU F32 word `0x40c90fdb`, and resource tuple also match. The exact source
validates and emits under the existing capability vocabulary. No compatibility
transform, new capability, numeric exception, proof kind, runtime rule, or ABI
addition is justified.

## Oracle and mutation rereview

`node task-21-oracle-generator.mjs --check` passes. Independently hashing the
generator's stdout yields the exact frozen JSON SHA-256
`bddb1ca8f8b7a8b905412318c48414594736ca4a972c440da7e8c3525b31bb38`.
All 13 canonical mutation source patterns occur exactly once in
`canonicalFactory45`, matching their asserted replacement counts.

Independent JSON recomputation confirmed the brief's sensitivity counts:

| Mutation | F32-changing | RGBA8-changing |
| --- | ---: | ---: |
| channel-order-red-zero-to-blue-two | 8/9 | 8/9 |
| direction-rotation-disabled | 7/9 | 7/9 |
| wrap-index-next-neighbor-clamped | 8/9 | 8/9 |
| wrap-float-coordinate-clamped | 8/9 | 8/9 |
| bilinear-fx-forced-zero | 8/9 | 8/9 |
| bilinear-fy-forced-zero | 8/9 | 8/9 |
| time-noise-branch-disabled | 6/9 | 6/9 |
| singularity-mask-forced-one | 8/9 | 8/9 |
| alpha-clamp-disabled | 8/9 | 0/9 |
| displacement-cap-disabled | 1/9 | 1/9 |
| simplex-amplitude-42-to-41 | 8/9 | 8/9 |
| frequency-axes-unswapped | 7/9 | 7/9 |
| seed-offset-disabled | 8/9 | 8/9 |

Every named required-divergence case differs and every named required-identity
case is byte-identical. The alpha mutation changes 49-53 F32 lanes per affected
case and zero RGBA8 bytes. The nine canonical cases total 4,228 output lanes,
all finite. The exact-copy case is 1,872 F32 bytes, preserves its input hash,
and contains the stated 50 out-of-range alpha pixels. All nine output hashes,
binding words, dimensions, and branch-control descriptions in the brief match
the JSON/report.

## Frontier, count, and exclusion rereview

I reran the projected remaining-key census from the current 113-key slice
while excluding planned Sacred and the two separately public legacy
factories. Exactly 96 keys remain, and exactly two validate and emit with the
current vocabulary:

```text
filter/crt:crt
filter/degauss:degauss
```

Therefore Degauss-only remains the correct smallest slice and CRT remains a
sound explicit exclusion. Adding projected Sacred and Degauss to the current
113 typed keys gives exactly 115 typed keys; adding Invert and Solid gives the
brief's exact 117-key public catalog. The listed catalog is sorted, unique,
contains Degauss once between Craquelure and Deriv, and excludes CRT. The
115/117/95/212 projection is correct.

The current checkout still has 113 typed programs and contains neither Sacred
nor Degauss. Thus Task 20 is not currently an accepted baseline. This is not a
brief defect: the brief explicitly requires accepted Task 20 114/116/96
evidence and captured baseline hashes before Task 21 implementation. That hard
stop is necessary and correctly scoped.

## Scope and gate assessment

Apart from the two P2 corrections, the brief is appropriately bounded:

- owned production scope is one slice entry plus a source-key profile/count
  lock; no emitter/runtime/IR/proof change;
- only the three existing generator outputs are regenerated;
- direct factory provenance is kept external rather than becoming a build
  dependency;
- generic validator/emitter behavior is not distorted to reject otherwise
  valid current-vocabulary synthetic programs;
- the nine native cases, thirteen canonical mutations, binding negatives,
  exact catalog, sanitizers, stack/disassembly, scoped code-shape scan, and
  unrelated-body drift checks are proportionate;
- native parity failure correctly stops and reclassifies rather than inventing
  a transform or bundling CRT.

After amending the corpus command and generated/native main-vs-pixel contract,
refreeze the brief and perform a focused rereview. No broader redesign is
needed.
