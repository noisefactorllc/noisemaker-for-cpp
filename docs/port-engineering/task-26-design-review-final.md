# Task 26 repaired-package and implementation-design review

Date: 2026-08-11  
Mode: independent read-only review; no repository or frozen-package artifact edit and no Git command

## Verdict

**SPEC CONSISTENT: YES.**  
**IMPLEMENTATION READY: YES.**

Blockers: **none**.

Finding counts:

- Critical: **0**
- Important: **0**
- Minor: **0**

## Findings

### Critical

None.

### Important

None.

### Minor

None.

## Independent validation

### Workspace and scope controls

The workspace mandate requires the force-push postmortem before action and makes its controls binding (`../AGENTS.md:3-5`). The postmortem requires append-only published history, exact-file scope review, action-specific authorization, and no second write after an unexpected publish (`../POSTMORTEM-2026-07-14-NOISEMAKER-FORCE-PUSH.md:109-121`). The target repository has no repository-local `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` override. This review performed no Git command and changed only this requested review file and its requested sidecar.

### Repaired frozen package

Fresh SHA-256 computation matched every repaired authority pinned by the final design (`task-26-implementation-design-final.md:9-15`):

- frontier audit `f0971b7cc06b9758975f6d856950c9a5067a2fd9ea71e4c68e46edc699bdf6f6`;
- brief `5df8328d28859ced1b0782008087902fbd9bb6bc23bbdcfe28e71c72d1c1e975`;
- oracle generator `43300fee88354bcce9d1294071858fce432e2297ce1dd3dcccfed524ba2268f9`;
- oracle JSON `7975cbe59733df0178956b7f145e03c2e872e269327d9f8dd1126c3bb9c3ccf9`;
- oracle report `b3e4a175ea95fe4bdd3319a11996451551ab9a3281412d10aa856f906515f816`;
- repair report `6334ea50c9b9b7ed6d272bafd2309e9b3e865667cf89c8d26228e6476c461545`;
- final design `784e4f8588f51cca22167364e60f3e669246f8847706ce22233c40414c94e8b5`;
- design preflight `af681234f4f5798be1baa0e29597b7d3175b659c9e9c8fd9025148cc43735b4b`.

The three existing sidecars for the repair report, final design, and design preflight match their files. Fresh execution of `node docs/port-engineering/task-26-oracle-generator.mjs --check` returned `ok task-26-oracles.json and task-26-oracle-report.md`, satisfying the brief's required pre-implementation gate (`task-26-brief.md:79-92`) and the final design's authority claim (`task-26-implementation-design-final.md:3-17`).

The repair report correctly distinguishes six syntactic fetch sites from 1-or-5 runtime executions (`task-26-artifact-repair-report.md:6-21`). Independent traversal of the current typed AST found `texelFetch` at normalized spans `25:21-25:51` and `31:26-35:98`, one `textureSize` at `20:21-20:45`, and five `luminance` calls at normalized lines 31-35, matching the repair recount (`task-26-artifact-repair-report.md:37-49`). The source control flow has the first fetch only in the `smoothType == 0` early-return branch and the other five only after that branch (`tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/smooth/smoothEdge.glsl:25-47`), establishing exactly six static sites and dynamic counts 1 or 5. One `textureSize` call precedes the branch, so it executes once on either path.

The repaired JSON contains eight cases, eleven mutations/controls, and eight results per mutation (88 total). Fresh `--check` regeneration reproduced the exact case hashes. The mutation table independently reproduces the design's changed-case and maximum-lane counts, including the three intentionally output-identical structural controls (`task-26-implementation-design-final.md:312-345`). Node `JSON.stringify` semantic hashes for `cases`, `cross_case_controls`, `mutations`, and `fixture`, plus the neutralized `program`, reproduce the repair report values (`task-26-artifact-repair-report.md:51-63`).

### Exact source, tree, factory, and profile lock

Independent parse/analyze and hashing reproduced every required source/tree/profile value in the brief (`task-26-brief.md:94-154`, `task-26-brief.md:156-226`) and final design (`task-26-implementation-design-final.md:77-121`):

- raw 1554 bytes, SHA-256 `b18be207f35a2bf3bcbdb19eb87018fac241856359d6094362f468fa048b5265`;
- normalized 1235 bytes, SHA-256 `42f61c507d633c07415bc816b6ba61f8a862642429943be1c0c1208c97b90f7c`;
- function tuple `8a7f2ac058a23e438f31787c55d235235271429fb79fc1d085c4dd1ba08cd4fc`;
- whole program `5586658ce1f621887647e5fb77990606e8637b7d759d2c9f1096f26b7385cd89`;
- interface `9149a7b19b47edea7179f8460443ee67c4a314bcb3ed2a83b7a68d91550f4930`;
- declaration `be8644a44ad3d2710e4dfaa87045257a5bd7c0e7e0a363c12893ea77c3d2ee27`;
- initializer `57ee749ccff2d5029ccbd10b7ce01320fdeb694bf2d02d5835a0e6ccd5836104`;
- sole read `df251d3d8461278afd63b36f1f3cef0d48777196908b8571a11d65dc54b83880`;
- dot parent `0f4d0fe02d9ee23557db69dfaca7ffa5c2542295d385c0d075f5b7e374fa43ae`;
- first argument `0c947970257b7042745712013dccbc9cbe816a36827840e4e403bd36c3e06ef3`;
- profile tuple `fbb3808e4392e3b3fa56a48965a36a47ce1a438626c9acdc6d33613fd3f57b80`.

The declaration is exact symbol 7, readonly `const vec3`, and has only the one resolved readonly use in `luminance`. Literal lexemes, spans, hashes, and F32 bits independently match all three frozen lanes. The functions are exactly `9:luminance` with one statement and `10:main` with thirteen statements. Loop proof is zero loops with an acyclic call graph.

Fresh hashes of the pinned CPU canonical runtime, public catalog, and adapter index matched the design (`task-26-implementation-design-final.md:302-310`). The public factory is the exact `canonicalFactory140` object, its string is 2660 bytes with SHA-256 `732feb5a9bb518cb46c38b59efb7f2901467fa74ae341f640822d22c20f2380e`, and the adapter entry is absent.

### Current Task 25 baseline

Fresh checks established the exact baseline required by the final design (`task-26-implementation-design-final.md:36-75`):

- `check_corpus.py --check`: `check_corpus: ok`;
- `check_semantics.py --check`: `bodies ok (212 programs)`;
- `generate_kernels.py --check`: exit 0;
- `generate_typed_slice.py --check`: `typed slice ok (125 programs)`;
- current Debug tree rebuilt from current source and CTest passed 1/1;
- Task 25 oracle generator `--check` returned `ok`;
- Task 25 frozen artifact hashes match the values at `task-26-brief.md:44-50` and `task-26-design-preflight-report.md:40-47`.

Independent key-list calculation gives 125 typed, 127 public, 212 corpus, and 85 publicly unported; positions Lens/Gather Sorted/Prismatic are 2/52/59; ordered-key hashes are `9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4` and `9d773dde79594d81d54b2d4cd1cab8b8929201eaa01ef276db38530c39edeaab`. Adding only Smooth gives 126/128/212/84, position 77 between Skew and Smoothstep, and projected hashes `01b1dd9d0ec83e375275bc3928ee0f652d1495666616e5280e4b878a71b5db76` and `d46ed864c5ed1795201981b7fc4aeec8fd330caa54c09d890235e5023c91e6e3`, matching the design (`task-26-implementation-design-final.md:63-73`).

All twelve current relevant repository hashes exactly match the preflight inventory (`task-26-design-preflight-report.md:77-94`), and the new Smooth profile file is absent. The current validator independently rejects the unprofiled Smooth tree with `filter/smooth:smoothEdge:12:1: unsupported global declaration`, matching the preflight (`task-26-design-preflight-report.md:113-127`).

### Implementation design sufficiency

The design admits only `filter/smooth:smoothEdge`:

- it expressly forbids generic global/vector/constant support and all adjacent subsystem changes (`task-26-implementation-design-final.md:19-34`);
- one exact per-row carrier is required only on the exact key with empty defines (`task-26-implementation-design-final.md:157-180`);
- profile application is an authenticated identity transform, while validator and emitter reauthenticate independently and admit only the exact declaration object from their own input tree (`task-26-implementation-design-final.md:123-155`, `task-26-implementation-design-final.md:200-252`);
- the negative closure covers foreign carriers, adjacent profiles, declaration/read/owner/materialization drift, and attempts to authorize another const Vec3 (`task-26-implementation-design-final.md:254-269`);
- historical generated blocks, manifests, and catalog entries are isolated mechanically (`task-26-implementation-design-final.md:283-300`).

The five-step RED/GREEN order covers profile, schema, independent validator/emitter authority, generation, and native catalog/binder exposure before regeneration, with focused failure evidence required before each production change (`task-26-implementation-design-final.md:271-281`). This is a valid bounded TDD sequence for the implementation surface.

Native coverage is complete at design level: the exact eight corrected oracle cases, public-twice/direct-once rendering, dimensions, hashes, probes, finite lanes, immutability, repeat identity, alpha/origin/threshold/clamp behavior, exact five-binding ABI, missing/wrong-type rejection, extra-binding acceptance, and all eleven mutations are explicit (`task-26-implementation-design-final.md:302-345`). The native artifact is hermetic and has a separate Python transcription gate, so `/tmp` and the CPU checkout cannot become runtime dependencies (`task-26-implementation-design-final.md:304-325`).

The stack/disassembly/sanitizer gates require fresh Debug, Release, and ASan/UBSan trees; preserved contraction/stack flags; helper and pixel frame records; a shown sub-16-KiB non-inlined chain; scoped Release disassembly; exact F32 constants feeding the dot; no global load, allocation, indirect/exception/dynamic-stack path; binder accounting; exact static/dynamic fetch evidence; and explicit LeakSanitizer fallback recording (`task-26-implementation-design-final.md:347-363`). The final sequence also reruns all generators, Python tests, fresh native configurations, prior Task 15-26 oracles, counts, positions, and hashes (`task-26-implementation-design-final.md:365-379`).

The ten-path ownership list is identical to the brief's authorized list (`task-26-brief.md:392-419`; `task-26-implementation-design-final.md:381-396`). Generated files are generator-only, `tests/test_typed_slice.cpp` is exceptional and expected unchanged, and parser/IR/runtime/CMake/corpus/existing-profile edits remain forbidden.

## Final gate

The repaired package is internally and externally reproducible, the current Task 25 tree has not drifted from the refreshed baseline, and the final design provides narrow authority plus sufficient TDD, isolation, native, ABI, mutation, stack, disassembly, sanitizer, and regression gates. Repository implementation may begin under the design's owned-file and no-Git boundaries. Any subsequent baseline, artifact, source, count, order, or hash drift remains the stop condition stated at `task-26-design-preflight-report.md:145-147`.
