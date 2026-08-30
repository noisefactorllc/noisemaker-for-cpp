# Task 16 frozen canonical oracle report

The frozen Task 16 oracle contract has been created without repository edits.
It covers only `filter/pixelSort:computeRank` at the pinned corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`.

Artifacts:

- `task-16-oracle-generator.mjs` — SHA-256 `126f0cb3908c615e27418ef4b825dfb49b727e384fe5b887b4f96d5306138707`
- `task-16-oracles.json` — SHA-256 `370aa41a4a2711dd038935d5cd67d611e6a97daabb3db9e631289de5c5e15ed3`

**Re-frozen 2026-08-30 as a dual-architecture package (schema `…oracles.v2`).**
The `width-one` case pins the bytes of a NaN the hardware manufactures
(`0.0/0.0`), whose sign is an ISA property, and V8 does not canonicalize NaN,
so the JS authority itself differs per architecture. The package now records
one capture per architecture with its own provenance, and the generator gained
`--capture` / `--freeze` alongside `--check` (which now verifies the frozen
selection for the architecture it is running on). It also resolves the JS
authority from `NOISEMAKER_CPU_ROOT` / `NOISEMAKER_FOR_CPU` — as committed, its
import and fs paths could not both be satisfied by any checkout layout, so it
was unrunnable in place. Pre-refreeze artifact hashes were
`21be6bb03a268cc51ad5acc649c953b8f1acaa14a6276ebe470dcaed08410ff7` (generator)
and `878959f2afb5d16889e546ba1ef0280b45c6cb6a7fbf4668c9a2c7310a4e5eee` (JSON);
the report line above previously quoted `bf38cb75…` for the generator, which
matched neither. Full measurement:
`docs/port-engineering/x86-64-divergences/x86-64-divergences-report.md`.

The generator imports only the pinned canonical CPU `canonicalKernelFactories`,
`bindCanonicalKernel`, `runPass`, and `Surface` APIs.  It records source and
canonical factory provenance, binding identity, dimensions, top-down storage
and bottom-left fragment orientation, F32 and RGBA8 hashes, F32 lane bits,
and byte-identical double-render results for all cases.

Frozen cases:

| Case | F32 SHA-256 | RGBA8 SHA-256 | Purpose |
| --- | --- | --- | --- |
| `formula` | `b232b1b98b9d973eed9b21ffabfe2039974f4e431269fe05d1ed9741b0e06bf3` | `f9021ce571b2f8234509a7df8f9ec2379cb91db4aa56c42dab39f3a0657cfce6` | strict comparison, skip, orientation |
| `flat-tie` | `37826c52ed556af08540665ec5435fd99188af1aeb525900647b710f0ecf800f` | `472adcee73849262e3cc7ce4a7bcfdfbb2e4191f7c51e6d49ab4e02404e8d753` | equality tie-break and `sampleX < x` |
| `width-one` (arm64 capture) | `24f56616adaf6242697f97e5d9420c4bafa1529c99e8e053b9dc0cb6bc87341c` | `1f71b62d981be40a6adc0ccd7ef62b6bc47317c7a1de96d4b934f761b67b135e` | `width - 1 == 0`; blue is `0x7fc00000` (AArch64 `fdiv` default NaN) |
| `width-one` (x86_64 capture) | `79d1c1af5c1c16157179b44c4a5c04320924e03c6748cbb0eeb40ae4cb8a5582` | `1f71b62d981be40a6adc0ccd7ef62b6bc47317c7a1de96d4b934f761b67b135e` | same case; blue is `0xffc00000` (SSE2 `divsd` QNaN indefinite). RGBA8 is arch-independent: any NaN maps to 0. |

Verification performed:

```text
NOISEMAKER_CPU_ROOT=<authority> node docs/port-engineering/task-16-oracle-generator.mjs --check
ok task-16-oracles.json (arm64, node v24.7.0)
ok task-16-oracles.json (x64, node v24.7.0)
```

`--check` recomputes all three canonical cases and compares the frozen JSON's
selection for the architecture it is running on, leaf by leaf.  It performs no
write.  Both lines above are real output: the second is the same command under
the sha256-verified `node-v24.7.0-darwin-x64` build running on Rosetta 2.
