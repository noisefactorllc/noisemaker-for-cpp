# Task 25 amended brief and oracle-package independent review

Date: 2026-08-11

## Verdict

**APPROVED.** I found no material scope, identity, oracle, projection, or
implementability defect in the amended Task 25 brief on SHA-256
`193523a6e94642c7c1b6c4da86b08de8616d0d15a3edc0b3257e068ac930ddd2`.
It is sufficient to proceed to a separately reviewed implementation design.
It does not itself authorize repository edits or Git operations.

The superseded draft's impossible post-only object-lineage rejection has been
fixed. The amended contract requires `is` identity only during the
deterministic pre-to-post transition, when both trees exist. Standalone
validator/emitter authority is exact observable post-tree value
authentication and explicitly accepts a dataclass-equal reconstruction. This
is implementable without adding a lineage registry, proof token, or typed-IR
field.

## Reviewed inputs

| Artifact | SHA-256 |
| --- | --- |
| amended `task-25-brief.md` | `193523a6e94642c7c1b6c4da86b08de8616d0d15a3edc0b3257e068ac930ddd2` |
| `task-25-frontier-audit.md` | `e754d9e02e3d98069297dda9f2c8071d25ba2347ddd812af0c41dc74b82e7d27` |
| `task-25-oracle-generator.mjs` | `3594cd9f0a82e7a21e662f8897f43eac0c86943b15ca36b2a0d3d0f805b2772c` |
| `task-25-oracles.json` | `09d8d8a9667fe3b3b90cd582e501b7c0a61d2a41e65ea2d175771a105e32e116` |
| `task-25-oracle-report.md` | `f72b69688d9a2f10df1603d1a012f6df8d0834f012438386038637630eb20611` |
| accepted `task-24-report.md` | `3a9d0086141061ed54a894a42ae4508cc32e483cb531361a212747a345315f0e` |
| Task 24 final independent review | `f6e7e6158a5a3f7bf03a2c99bcc6e5baa6e27d9c567c453f4ff7e4a2bdec7d0a` |

The Task 24 hard gate is present on the current workspace: `123 / 125 / 87 /
212`, Gather Sorted at typed position 51, and the nine existing Task 25-owned
files exactly match the accepted Task 24 report. Their current SHA-256 values
are `a227a011...` (generator), `5beff60a...` (emitter), `e6a0bbe1...`
(typed-slice manifest), `8d653a85...`, `ae903b17...`, `55fee138...` (tests),
`8d06f586...` (generated C++), `bf702062...` (generated manifest), and
`1ca4f356...` (catalog header). The new profile helper is correctly absent
before implementation.

## Independent source, public identity, and projection recomputation

Fresh reparsing of the corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6` reproduced both exact sources and
all frozen program locks:

- Lens Distortion: raw `8269 / f4e6453f...d444`, normalized `7723 /
  6586c49b...df52`, 8 functions, main `38 / 25`, main pre/post
  `dc6d4d2a...93ee / 8de66581...0ec`, function tuple pre/post
  `263870c4...04c1 / c166fa2b...a756`, whole program pre/post
  `f63fb6db...81f5 / e5dbb049...63d2e`, and interface
  `53e759b5...b4ca` unchanged.
- Prismatic Aberration: raw `4247 / 513eac95...380e`, normalized `3907 /
  1c157e7f...0860`, 5 functions, main `22 / 31`, main pre/post
  `416ffbae...0e56 / f0d3926e...187f`, function tuple pre/post
  `69495778...cf24 / 80fb20a8...58fd`, whole program pre/post
  `fdc004aa...997c / 1a808ce2...482c`, and interface
  `788b0390...010` unchanged.
- Exact diagnostic projections reproduced `27446 / 6cfa9d58...7fc5` and
  `13316 / 8d6c98fe...155f`. The scoped projected C++ has zero `operator[]`,
  zero `hsv[...]`, and zero runtime lane `switch` routes.
- The canonical/public entries are the same objects, respectively
  `canonicalFactory10` and `canonicalFactory117`, with factory-text hashes
  `151b1e86...adcf` and `2eab8943...ef02`; neither key has an adapter.
- Adding only these keys projects exactly `125 typed / 127 public / 85
  publicly unported / 212 corpus`, with Lens at position 2, Gather Sorted at
  52, and Prismatic at 59. The independently reproduced newline-terminated
  list hashes are `9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4`
  typed and `9d773dde79594d81d54b2d4cd1cab8b8929201eaa01ef276db38530c39edeaab`
  public. Grade LUT remains excluded.

## Exact closed site inventory

The complete pre-tree index census is exactly 11 nodes, all selected. Every
base is the direct writable main-local `vec3 hsv`; every index is an `int`
rvalue literal; every result is a `float` lvalue. The mechanical role rule
gives six writes and five reads, with lane incidence `7 / 3 / 1` for lanes
`0 / 1 / 2`. Fresh transformation leaves zero index nodes. Exact rows are:

| Key | Path | Span | Lane/role | Pre SHA-256 | Post SHA-256 |
| --- | --- | --- | --- | --- | --- |
| Lens | `(18,'s0','s3','e0',0,0)` | `236:9-236:15` | 0/write | `8b56c4f52b2113fa843aeb30133f38a488eda92edca236b9260285e426c632a3` | `1d9ee202f7c93a030803d2c61782ef959a8ef56fc8890b39de56bfe6cb2df13b` |
| Lens | `(18,'s0','s3','e0',0,1,0,0,0,0)` | `236:24-236:30` | 0/read | `1cc773177b9c87d54bd4289dd97c6384f43c0619d1c29a1b5cf1a09a2225a9e6` | `c7daed1dbf0ebc39669fa33212fa1d9b3233fbe7112e07c05ebeaa05a9120920` |
| Lens | `(18,'s0','s3','e0',0,1,0,0,1,0,0)` | `236:65-236:71` | 0/read | `27987cf202ec44e367f3edbacf025685a95a579d3bd1766ed007f3a39fba0233` | `689cb485e1d153df4ba2f46f52e10f7843c818cf111cbdf6d79aa26419f9f69a` |
| Lens | `(18,'s0','s4','e0',0,0)` | `237:9-237:15` | 1/write | `e67ab422ce4f28337e56fef80f8bfb4dbd93a1bbe30eb0165c0aa3cc7dc6cb44` | `829b7f013b6ca2c1cbf03eb25079f7a02ec32731eb0bb8d8015dbfa77152e16b` |
| Lens | `(18,'s1','s3','e0',0,0)` | `247:9-247:15` | 0/write | `92be124aed858e61dff4316731b67be8a46a881c527285b56263477b81193f12` | `0ee30fa6b2497642b0b1b2cbb0fe9fee6fc7594191d410f3ff2b20f7ba6c8243` |
| Lens | `(18,'s1','s3','e0',0,1,0,0,0,0,0)` | `247:26-247:32` | 0/read | `af51ced1d6aafe987b1914573554213afb0c123619134749a44fdb603d08b818` | `d3a7a9840bbe6523a9038c402537928e10b5abaca692762a7b8947f821f4add0` |
| Lens | `(18,'s1','s4','e0',0,0)` | `248:9-248:15` | 1/write | `569c4bc0beead7e391d0bddbcfe03fb78b78286f8bb00754eb37bfa5bc1720de` | `2c94a065f64b606da19073ffe0afd554d57c9222714af12c034b37f90a6b192a` |
| Lens | `(20,'s1','s0','s0','e0',0,1,0,0,0,1,0)` | `260:46-260:52` | 2/read | `e2faad5610537f7e86b817e16c093b165a4d4d84bac84799bfc055f3de262fea` | `96a5a6b39df3fba890e8286278615e6518ec77b6c9d440f9e315bdc70d596250` |
| Prism | `(26,'e0',0,0)` | `131:5-131:11` | 0/write | `2637ccd727e74a3b5583230bf07d8ceed92e72dfc4434041075f90515950f23d` | `2c240e9eae37323e092e20ac3d21e7382fcd86b7160b8f041cc3a2eb9cb7bdeb` |
| Prism | `(26,'e0',0,1,0,0,0,0,0)` | `131:22-131:28` | 0/read | `9af4f5115d7b784cac89bd118123e8b0935194c93b970da62f01541590b17ce2` | `94558e9138e38ceb285c1746af1473ca77f5f56ef564626edaad0be6546d6072` |
| Prism | `(27,'e0',0,0)` | `132:5-132:11` | 1/write | `155a0535e006b5b61f14d842415d9bba0633f15d905e7fbf8944ff847f5685f2` | `8e585f401b1450e2f7c58dd3fada71b23f0cb2b4e85f7e75c6371459db863306` |

The independently recomputed exact profile-tuple hashes are
`d1235bb6045a5795c4c10c5db8a990f51ee42e5541dcfa7a663c91f3245d10d3`
and `25ad8a580a8263b4d2d15b41eb783abeed3433c94b9c8fffbbae2546300fd6b2`.
No dynamic, induction, uniform, negative, out-of-range, or generic vector index
is admitted.

## Oracle and execution-contract audit

`node task-25-oracle-generator.mjs --check` passes on the frozen package. The
JSON has exactly six cases in the brief's order and eleven unique one-site
wrong-lane mutations. Each case has a full input F32 hash plus five probes,
full output F32/RGBA8 hashes plus five probes, byte-identical repeat, immutable
input, and zero nonfinite lanes. Finite lane counts are exactly
`308, 320, 324, 288, 280, 216`.

Each Lens mutation has four results, diverges in exactly its two active branch
cases, and remains identical in the other two. Each Prismatic mutation
diverges in both of its two cases. The line-260 mutation correctly records
three generated occurrences for its one authenticated source splat read; all
other mutations record one occurrence. This proves sensitivity of all six
writes and all five reads without creating a generic indexing capability.

Bindings and resources also reproduce exactly. Lens has sampler `inputTex`,
twenty ordinary uniforms, output `fragColor`, three static texture sites, no
texture-size call, no loops, and no derivatives. Prismatic has the same
sampler/output shape, ten ordinary uniforms, three static texture sites, one
`textureSize(inputTex,0)`, no loops, and no derivatives. Both have empty
struct, uniform-block, and varying collections; only scalar/vector/sampler
types; and acyclic zero-loop program proofs. The brief correctly defers actual
`.su`, maximum call-chain, Release disassembly, and native fetch verification
to implementation, while making them mandatory completion gates below 16 KiB
and forbidding runtime lane branches or indirect routes.

## Fresh checks

- `node docs/port-engineering/task-25-oracle-generator.mjs --check` —
  exit 0.
- `python3 docs/port-engineering/task-25-recompute.py` — reproduced the
  frozen two-program record and all pre/post identities.
- `python3 tools/glslcpp/check_corpus.py --check` — `check_corpus: ok`.
- `python3 tools/glslcpp/generate_typed_slice.py --check` — exit 0.
- `python3 tools/glslcpp/check_semantics.py --check` —
  `bodies ok (212 programs)`.
- `python3 tools/glslcpp/generate_kernels.py --check` — exit 0.

No repository file was changed, and no Git operation was used for this review.
