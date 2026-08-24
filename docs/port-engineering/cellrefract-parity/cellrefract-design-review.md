# cellRefract186 design review — verdict GO

**Frozen record. Never edit.** Independent review of
`cellrefract-design.md` (pre-implementation state), executed 2026-08-16
against the live `noisemaker-for-cpp` (185 typed rows, commit `8edff08`) and
the pinned `noisemaker-for-cpu` JS authority. The reviewer re-derived every
checkable figure through the real frontend rather than re-reading the design's
numbers, ran the real `validate_capabilities` for the RED boundary, hashed the
live artifacts, and read the validator/emitter gate paths end to end.
Read-only; scratch scripts outside both repositories.

## Verdict

**GO.** Four Important findings, all folded into the design as Amendments
§§11-14 (with minor corrections unnumbered); none changes the mechanism
decomposition. Every frozen fact in design §§1-2 reproduced exactly:

- Raw 13,719 bytes / `aa93167f…a70`; normalized 10,221 / `31cce61e…3c`;
  whole `10049e9b…c28`; interface `09c626e4…352`; census 1,670/173;
  22 functions; 21 declarations; defines `(("KERNEL","int","0"),
  ("SHAPE","int","1"))`.
- Arrays at ordinals 16-20 / symbol ids 17-21 / spans `32:1`…`36:16`, all
  `float[9]`, mutable, uninitialized.
- `loadKernels` id 70 `38:1-64:2`; `convolve` id 66, `kernel` symbol 23 at
  `66:29-66:44`; `convolutionKernel` collapsed to `return color;`
  (`279:1-281:2`); `main` `378:1-410:2`; caller tables 67/73/81/84 with
  symbols 107/108, 131/132, 152/153, 162/163; `offset` table symbol 101;
  induction symbol 104, trip 9, `kernel` reads at `87:25`/`90:25`.
- Call graph 16 edges; reachable {main, loadKernels, cells, map, pcg, prng,
  smin}; the 15 unreachable functions as listed.
- Write-only strengthened: exactly 45 `id` references to symbols 17-21
  program-wide, all assign-target bases inside `loadKernels`; zero reads;
  zero whole-array bases; no initializers anywhere.
- RED boundary reproduced live: `32:1 unsupported global declaration`.
- JS quotes exact (`canonical-kernels.js:1144/36183/1172-1176/1177-1223/
  1608/1224-1248/1154-1155`; `glsl-runtime.js:549-556`); all six pinned
  CPU-file hashes still match.
- Precedents verified: refract emission (`typed_slice.cpp:1715-1718/1856/
  1884-1893`), dict-keyed `mutable_global_frame_profile.py`
  (`KEYS`/`PROFILES` at 115-117), hard-frozen `fixed_array_in_parameter_proof.py`
  (symbol 19, induction 54, census `(1,3,35,32,27,3,30,2,2)`).
- Neighbors: `cellNoise` < cellRefract < `coalesce`, insertion index 2;
  `_defaults` supplies exactly `{'KERNEL': 0, 'SHAPE': 1}`; today's four
  artifact hashes equal the handoff stop line; cellRefract is in neither
  adapter table; `resolution` declared-but-unread; 19 Python test modules;
  no `out`/`inout` parameters.
- Loop profile complete and inside `COUNTED_FOR_V1_MAX_*`; `cellNoise`
  precedent needs no loop carrier (basis for dropping §3D).
- Const-write audit covers only the const set (`generate_typed_slice.py:
  3958-3964`), so a separate mutable admission keeps the 45 stores
  admissible.

## Findings (folded into design Amendments §§11-14; summaries here)

**Important**

1. §5 native census contradiction: `factories.size()` is 187 today
   (`tests/test_generated_kernels.cpp:249`) and moves 187 → 188; the design's
   "186 → 187" was a hand-transcription of the previous slice's correction.
2. The emitter cannot lower the bare `loadKernels();` call statement today
   (`emit_typed_cpp.py:4409-4417`, `only typed assignments are admitted`);
   a new identity-gated bare-call arm is required work — the documented
   wcSimplify failure class, surfacing only on the emitter side.
3. Two unnamed integration sites: the refract-keyed proof-recomputation chain
   (`generate_typed_slice.py:3652-3686`) raises `malformed fixed-array
   input-parameter proof key` for any non-refract attachment unless a
   cellRefract arm registers the `proved_array_*` sets; and the template
   module's `_OPTIONAL_PROOF_FIELDS` (`mutable_global_frame_profile.py:
   158-163`, `:1111-1113`) rejects programs carrying
   `fixed_array_in_parameter_proof`, which auto-attach makes unavoidable.
4. §3A's "all values literal floats" is unsatisfiable: 19 of 45 store values
   are `unary(-)`-of-literal nodes; extract via the `_number()` form
   (`fixed_array_in_parameter_proof.py:143-153`).

**Minor**

5. Right-hand sorted neighbor is `coalesce`, not `colorLab`.
6. §3D (loop carrier) almost certainly dead weight; drop-path expected.
7. Line-citation drift: `beginPixel` at `glsl-runtime.js:132`; factory closing
   brace at 1646.
8. Landing is row 186 but the namespace is `typed_2`; label both schemes.

## Judgment

The mechanism decomposition, lock design (value-before-identity ordering,
per-key `_fail` prefixes, write-only census freeze with no reads-allowed
switch, `Frame&` single writer, per-key array-parameter record with refract
byte-identical), foreign-carrier sweep with ownership recording,
delete-the-check with sub-clause pair testing, and the oracle-mutant
satisfiability reasoning (write-only tables not pixel-discriminable at frozen
defines; reachable-path mutants plus the `KERNEL != 0` invariance witness)
are sound and well-matched to the project's documented traps. Census
projections 186 rows / 26 absent / 25 genuinely unported verified. Historical
reconstruction plan correctly specified.
