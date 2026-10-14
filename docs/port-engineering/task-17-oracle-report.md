# Task 17 frozen external oracle report

The Task 17 external oracle contract is frozen for exactly the proposed
`fixed-nine-local-literal-init-counted-read-v1` pair:

- `filter/sharpen:sharpen`
- `filter/sobel:sobel`

The generator binds the pinned
`noisemaker-for-cpu` `canonicalKernelFactories` directly through
`bindCanonicalKernel`, renders through `runPass`, and stores output in the
canonical `Surface` type.

Artifacts:

- `task-17-oracle-generator.mjs` — SHA-256 `2b7af41b00c67c2db556702d94c8f5141008b0d571f3adf848c304e9d6095ce0`
- `task-17-oracles.json` — SHA-256 `1d613185da53458974ae43b3515a7698057bb8b91bd423873b50e4076de9aa95`

The shared input is a non-square 11x9 top-down Float32 formula surface;
output is 9x7 with `tileOffset=[2,1]` and `fullResolution=[13,11]`.  These
dimensions preserve bottom-left fragment orientation and exercise all nine
offset-table reads on every output pixel.  Every case records canonical source
and factory digests, bindings, F32/RGBA8 SHA-256, F32 bit probes, and a fresh
surface double-render identity check.

| Case | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- |
| `sharpen-default` | `54bffb81920b79c85198238c2fcd4f52b94ae25ca208747fb0048f24a71b05ec` | `d1bd7b35b2890258c385d294879556b4586d33f4af29feeeb7be5a4931ec2094` |
| `sharpen-amount-2.3f` | `53f12c6e6047f31edb9e157202674a405489df96dd995adcc3bf4aea5a20128f` | `560e7225289764f8d2c108b3f0746859ceb38ce4dee47753710d6d18473101e3` |
| `sobel-default-alpha-one` | `891443c519cf988ba5eea5acdb4e84759160ac1a992f9f8fcac2824e331e8483` | `6841efab285a153de30bebaad4a6550107a1de719c37337a159ef07667d76777` |
| `sobel-amount-2.3f-alpha-zero` | `f7e50759990c46d868b22bdf83241e3866b14a6406fee043b8cad46cbea6b1d8` | `05f02465cc5eacd61320b5d1b304f4b8face9993f604f540466d9582075bb3e0` |

With `CPU_ROOT` and `CPU_LEDGER` set to the authenticated CPU root and matching
ledger, verification from the repository root is:

```text
node docs/port-engineering/task-17-oracle-generator.mjs --cpu-root "$CPU_ROOT" --ledger "$CPU_LEDGER" --check
ok task-17-oracles.json
```

`--check` recomputes all four canonical cases and byte-compares the complete
existing JSON.  It performs no write.

## Numeric edge notes

- Canonical `createCanonicalBindings` spreads explicit `uniforms` without
  rounding them.  The oracle therefore passes `Math.fround(2.3)` explicitly,
  frozen as `2.299999952316284` / `0x40133333`, rather than relying on a JS
  double `2.3`.  Native tests must bind that same F32 uniform value.
- The scalar convolution tables in canonical code are zero-filled plain
  JavaScript Number arrays, whereas each offset is a zeroed F32 vector.  The
  literals themselves are integral, but native scalar tables must remain
  `double[9]`-equivalent and vector tables F32-lane equivalents.
- Sobel at alpha one produces finite RGB values above one (for example the
  `(4,3)` blue probe is `0x406c128c`), because its source does not clamp the
  result.  RGBA8 consequently saturates, so F32 hashes/probes are essential;
  RGBA8 alone would hide a precision or range regression.
- Sobel at alpha zero returns the original RGB through `mix`, but still runs
  the convolution.  It checks the alpha/mix boundary while retaining the same
  table and offset execution.  Sharpen clamps RGB but preserves sampled alpha.
