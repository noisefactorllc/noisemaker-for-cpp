# Task 16 frozen canonical oracle report

The frozen Task 16 oracle contract has been created without repository edits.
It covers only `filter/pixelSort:computeRank` at the pinned corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`.

Artifacts:

- `task-16-oracle-generator.mjs` — SHA-256 `bf38cb756ab23c4d7a69b8f320bafe77481b251545fbe31585a6527196a98bab`
- `task-16-oracles.json` — SHA-256 `878959f2afb5d16889e546ba1ef0280b45c6cb6a7fbf4668c9a2c7310a4e5eee`

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
| `width-one` | `24f56616adaf6242697f97e5d9420c4bafa1529c99e8e053b9dc0cb6bc87341c` | `1f71b62d981be40a6adc0ccd7ef62b6bc47317c7a1de96d4b934f761b67b135e` | `width - 1 == 0`; blue is canonical `0x7fc00000` NaN |

Verification performed:

```text
node docs/port-engineering/task-16-oracle-generator.mjs --check
ok task-16-oracles.json
```

`--check` recomputes all three canonical cases and compares the complete
existing JSON byte-for-byte.  It performs no write.
