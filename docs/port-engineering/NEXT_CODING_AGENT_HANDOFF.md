# noisemaker-for-cpp Continuation Plan

> ## PUBLICATION CHECKPOINT 2026-08-30 — READ THIS FIRST
>
> This block supersedes the 2026-08-26 checkpoint below (kept as history).
>
> ### What happened
>
> - The repository is PUBLISHED: `github.com/noisefactorllc/noisemaker-for-cpp`,
>   pushed at `686d421` under explicit operator authorization. NOTE: it was
>   created public and verified public via the API, then something org-side
>   flipped it to private within ~15 minutes; do not override visibility
>   without the operator.
> - A six-lane independent review (hygiene / parity / cpp / generator / docs /
>   tests) ran against `686d421` and every actionable finding was fixed in the
>   working tree (commits after `686d421`). Full evidence:
>   `.superpowers/sdd/2026-08-29-publication-review/` (git-ignored, machine-local).
>
> ### Defects found and fixed after publication
>
> 1. **Parity**: `float_to_half_rte` implemented ties-to-even; the authority
>    rounds half-up (8,420,351 of 2^32 inputs diverged; the suite pinned the
>    wrong value). Now `float_to_half_js`, exhaustive differential 0 divergent.
>    `half_to_float` now canonicalizes NaN like the authority (2045/65536
>    codes diverged). Both proven against the live node authority.
> 2. **Runtime**: use-after-free of the effect input when a non-final pass
>    rewrites its arena name (latent; ASan-proven both ways; fixed with an
>    arena pin primitive). Refusal records emitted unescaped JSON; now routed
>    through `json_string` (python regression added).
> 3. **Portability (CI was red on every native job)**: generated slice used
>    `std::clamp` without `<algorithm>` (fixed in the EMITTER, cascaded);
>    `-Wmisleading-indentation` on dense generated-style files (scoped
>    suppression in CMake); GCC `-Wdangling-reference` false positives in
>    registry.cpp (context strings hoisted); fdlibm `fq` zero-init;
>    Darwin-GCC `<xlocale.h>` guards; `bit_effects.cpp` one-line if split.
> 4. **Python suite on clean machines**: pytest declared in CI (library only,
>    runner stays unittest); backend-compat/frontend-oracle/dither/julia
>    env-gates converted to visible skips (set-but-wrong stays fatal); all
>    machine-absolute defaults removed.
> 5. **Docs**: README coverage table re-derived from the tree (211 of 212 in
>    the typed slice; 213 catalog rows); oracle-reproduction recipe verified
>    against real generators; corpus attribution added (MIT
>    noisefactorllc/noisemaker@a024dc3a, 211 files byte-verified).
> 6. **Sidecars**: 106 stale refreshed, 20 orphans deleted, one misnamed
>    renamed; dated float_to_half corrections appended to task-1 report and
>    task-31 design review.
>
> ### The emitter-change re-freeze (doctrine case 3)
>
> Adding `<algorithm>` to the emitted include list moved every historical
> reconstruction uniformly (+21 bytes). Live and reconstruction pins were
> re-frozen once; spec-level input locks stayed frozen as independent witness.
> New anchors: slice `86e8794f…` (2,710,848B), manifest `a53b1df4…`,
> backend compatibility `ec076aec…`, catalog payload `24c38ccb…`,
> corpus manifest `f45da8c3…`, compiler-expected pin `1eb8d0bb…`.
>
> ### Environment contract (all external roots arrive by env, no defaults)
>
> ```text
> NOISEMAKER_CPU_ROOT            frozen CPU authority (public repo
>                                noisemaker-for-cpu @ 4834b0144ee0…, whose
>                                90-file behavioral aggregate matches the
>                                pinned lock e2d52e1b…)
> NOISEMAKER_FOR_CPU             live CPU checkout (must differ from the
>                                authority except for julia, which wants all
>                                three equal)
> NOISEMAKER_SHADER_GIT          shader git checkout (read-only)
> NOISEMAKER_ORACLE_LEDGER       the oracle ledger file (713 entries)
> NOISEMAKER_DSL_CPP_ORACLE      built noisemaker-dsl-frontend-oracle binary
> NOISEMAKER_DSL_PARSER_ORACLE   built noisemaker-dsl-parser-oracle binary
> NOISEMAKER_DSL_COMPILER_ORACLE built noisemaker-dsl-compiler-oracle binary
> NOISEMAKER_DSL_CPU_CASE        built noisemaker-dsl-cpu-case driver
> NOISEMAKER_DSL_CPU_BENCHMARK   built corpus benchmark driver
> NOISEMAKER_DITHER_BASELINE_ROOT dither pre-port baseline snapshot (REAPED on
>                                the original machine; regenerate or retire —
>                                open decision)
> NOISEMAKER_REGEN_CACHE         optional reconstruction cache root
> ```
>
> ### The /private/tmp reaper (institutional memory)
>
> macOS deletes /private/tmp files by atime after ~3 days. It destroyed the
> working tree twice and the ENTIRE frozen authority + ledger once. The
> authority was reconstructed provably: live checkout HEAD `4834b01` matches
> the pinned behavioral aggregate; `git archive` restored 713 files; the
> ledger was regenerated. If it happens again, that is the procedure. The
> durable fix is moving the authority out of /private/tmp (open queue item).
> CI now needs no local authority for the byte-exact lane: the new
> `corpus-parity` job checks out the public authority at the pinned revision.
>
> ### Post-publication round 2 (2026-08-30, same day, after the push of cb47328)
>
> - Public CI immediately earned its keep: it caught an LP64-only duplicate
>   overload (json_number size_t/uint64_t — same type on Linux, distinct on
>   Darwin) and two x86-only bit-exactness failures.
> - THE ARCHITECTURE PARITY CONTRACT, settled: V8 does NOT canonicalize NaN.
>   x86-64 node produces 0xffc00000 for hardware-manufactured NaNs exactly
>   like x86 SSE; arm64 produces 0x7fc00000. The port matches the
>   SAME-ARCHITECTURE JS authority byte-for-byte on both ISAs (proven with a
>   sha256-verified x64 node under Rosetta; independently reproduces the
>   Lane G report docs/port-engineering/x86-64-divergences/). The contract is
>   therefore "bit-exact against the JS authority on the same architecture",
>   implemented as per-architecture frozen pins (compile-time ISA selection,
>   #error on a third arch; oracle packages carry both captures with
>   process.arch provenance, frozen via the generators' --freeze). Never
>   "fix" this by canonicalizing NaN in noisemaker::f32 — that manufactures a
>   real divergence from x86 JS to make an arm64 pin green.
> - `noisemaker-render` exists now (PNG out, defaults, --list-effects,
>   refusals exit 4 with the executor's reason) — the harness driver
>   noisemaker-dsl-cpu-case is for the corpus lane, not humans.
> - API hardening landed: exported target carries cxx_std_20 (find_package
>   consumers literally could not compile before) and INTERFACE
>   -ffp-contract=off for AppleClang/Clang/GNU; EffectCatalog::find() is
>   thread-safe (was a TSan-proven race on a const path); PNG decode throws
>   PngError : std::runtime_error; executor internals headers are marked NOT
>   A STABLE API.
> - Running x86_64 suites on macOS/Rosetta: `ulimit -s 65520` or the run
>   SIGSEGVs in the catalog test with silently truncated stdout. Reading NaN
>   bits in node: use a DataView over the surface's own buffer, never
>   `new Float32Array([v])` (constructor paths canonicalize on x64).
>
> ### Remaining queue (supersedes the 2026-08-26 list; items 2–9 there stand)
> - Finish EffectCatalog::find() properly at the next oracle re-freeze: eager
>   index in the constructor (the clean fix moves generated_payload_sha256,
>   213 pin occurrences; the shipped fix is a correct mutex memo).
> - Rename typed_task16_..._preserves_canonical_quiet_nan (accurate on arm64
>   only now); bitwise package probe collapses NaN sign at probe level
>   (arch_divergence.probe_note); no gate runs the two dual-arch generators'
>   --check (CI has no JS authority; consider a corpus-parity-style arm).
> - Deliberate design decisions queued from the API review: noisemaker::Error
>   base hierarchy; UniformValue is 4280 bytes (one 267-Vec4 variant
>   alternative); real set_texture borrow enforcement; installing
>   noisemaker-render; a diagnostic for compilers that get neither
>   -ffp-contract=off nor a warning.
>
> - Move the frozen authority + ledger to a durable machine-local home.
> - 49 doc-package generators hardcode `../noisemaker-for-cpu` sibling roots
>   (F4, deferred: each is coherence-pinned; env-first rewrites cascade 49
>   package re-freezes). 15 of them pin authority revisions predating both
>   local roots — provenance drift documented in docs/port-engineering/README.
> - No automated cross-check between test-side kOracleSha256 anchors and
>   generator ORACLE_SHA256 constants (this let 50 pixel comparisons sit
>   disabled behind red CI). glitch-parity-native.inc lacks a .sha256 sidecar.
> - Consolidate the strtod_l locale-parse blocks (js_number.hpp, lexer.cpp,
>   executor.cpp) into one code path.
> - js_render_oracle.mjs lines 36-38 are freeze-time provenance stamps, not
>   live verification — label or re-derive.
> - Bridge manifest cannot see a NEW pytest-style module; test_texture_oracle
>   sidecar unenforced; coverage table has no pinning test.
> - Dither pre-port baseline: regenerate or retire (env var exists, snapshot
>   is gone).
> - kMeasuredParityExclusions (filter/snow, synth/testPattern) are excluded on
>   the DSL executor path but still bindable via the public catalog API —
>   decide gate-or-document (README now describes the mechanism honestly).
>

> ## HANDOFF CHECKPOINT 2026-08-26 — READ THIS FIRST (superseded)
>
> This section supersedes every older status block below it, including the
> 2026-08-25 STOP checkpoint. The older blocks are historical evidence only;
> in particular, their statements that Task 7 is uncommitted or not ready are
> obsolete.
>
> ### Checkout and Git state
>
> Work only in:
>
> ```text
> /private/tmp/noisemaker-cpp-continuation.e033lt/work/noisemaker-for-cpp
> ```
>
> Local `main`, clean tree, no remote, nothing pushed. Seven commits since
> the Task 6 base `4062bc8`:
>
> ```text
> a592b3e test: take lane test paths from the environment, not the session
> 2431f81 fix(benchmark): bind the shader expectation to its render options
> 1532e2c feat(benchmark): add the C++ corpus benchmark driver
> acb9460 fix(julia): make the checked oracle package a pure function of its own inputs
> 2b7be8c feat(dsl): serialize doubles as ECMAScript Number::toString everywhere
> 7437b75 feat: render the supported DSL effect corpus exactly
> 4062bc8 feat: execute multipass DSL graphs on CPU
> ```
>
> `7437b75` is the Task 7 checkpoint: executor connected to the generated
> canonical route table with authenticated route/ABI/define/output identity,
> read-only preflight before any copy or allocation, every ordered sampler
> route materialized, all 20 pass-derived bindings fail-closed by source
> name. It landed only after four review rounds closed all eight blockers of
> the independent executor review plus every finding of two scoped
> re-reviews and a final gate matrix.
>
> ### Verified state (all re-derivable; evidence in .superpowers/sdd/2026-08-24-polymorphic-dsl-and-benchmarks/)
>
> - **Corpus:** 166 records = **150 byte-exact / 13 refused with frozen
>   structured reasons / 3 authority-also-refuses / 0 divergent**, pinned by
>   `tests/test_dsl_corpus_parity.py` with zero tolerance.
> - **Step 8 (dual full-corpus passes):** JS CPU lane, the C++ benchmark
>   driver and the C++ parity driver agree byte-for-byte: RGBA8 aggregate
>   `e37414538f4af27c…`, relation aggregate `dff27acc0e595851…`, identical
>   across two independent passes, re-verified after the final serializer
>   rewire. Protocol: `tools/benchmark/two_pass_corpus.py` (enforces
>   warmups>=5, samples>=30).
> - **Full Python discovery:** 1997 tests, 0 failures (fresh external regen
>   cache; NOISEMAKER_CPU_ROOT must point at the frozen mirror
>   `/private/tmp/noisemaker-cpp-continuation.e033lt/oracle/noisemaker-for-cpu`
>   — it has the oracle-ledger sidecar; the live platform checkout does not).
> - **Native:** 476 PASS / 2 FAIL — the two FAILs are the documented
>   pre-existing glitch/shapeMixer fixtures, byte-identical to the Task 6
>   base. ASan 0 diagnostics; UBSan exactly the 2 pre-existing reports in
>   untouched typed_slice.cpp. Sanitizer runs need `ulimit -s 65520`.
> - **Generator gates:** typed slice (211 programs), effect catalog, backend
>   compatibility all `--check` exit 0. Compatibility regeneration needs
>   `--cpu-root <frozen mirror> --shader-git /Users/aayars/platform/noisemaker`
>   (read-only, cat-file only).
> - **Shader smoke (real browser):** webgl2 145 pass / 15 fail / 3 compile,
>   webgpu 139 / 21 / 3; honest cross-backend intersection **138 records**
>   (100 flat / 38 spatially varying / 26 flip-sensitive) — always publish
>   that split with any "138 exact" claim. Adapter identity is recorded and
>   software rasterizers are refused unless `--allow-software`.
>
> ### Step 9 — DONE at this checkpoint
>
> The WebGL2/WebGPU expansion ran to completion: 332 hardware runs
> (166 records x 2 backends, Apple M2 Metal, software gate untouched).
> Distributions: webgl2 145 byte-exact / 15 mismatch / 6 refused; webgpu
> 139 / 21 / 6. The measured intersection is **exactly the re-review's 138**
> with zero status changes. Divergences are classified as failures with
> per-record first-divergence evidence: A1 low-amplitude backend-independent
> (3), A2 high-amplitude backend-independent (9, incl. synth/gradient), B1
> one-lane-only (6), B2 both-lanes-different-signatures (2: snow, stipple),
> **F upstream per-effect WGSL orientation defect (2: grime, texture — the
> WebGPU raw readback equals the expectation byte-for-byte, so the flip is
> upstream, not the harness)**, C 3 S005, D 3 no-CPU-expectation. The
> protocol contract is pinned in `tests/test_benchmark_shader.py`
> (hardware-dependent counts deliberately NOT pinned); the full report is
> `task-7-step9-expansion.md` beside the ledger. Handoff steps 1-10 of the
> 2026-08-25 sequence are all complete.
>
> ### Remaining work queue (in rough priority order)
>
> 1. Step-9 expansion record (in flight, above).
> 2. **paletteData override port** — closes 6 of the 13 corpus refusals
>    (shapes/fractal class).
> 3. **Worm-overlay port** (`filter/{fibers,scratches,strayHair}` 'ready'
>    mode) — needs bit-exact Math.log/Math.hypot; fdlibm.hpp documents the
>    gap. The one_shot=='initial' shortcut is REFUTED; the guard stays.
> 4. `synth/testPattern` codegen-level divergence (2 grid-boundary pixels).
> 5. `kMeasuredParityExclusions` is a 2-entry measured deny-list; entries can
>    only refuse, never render. Shrink it by porting, never by relabeling.
> 6. The 3 S005 chain-structure records + `synth/media` external-texture
>    support; `filter/lighting`/`filter/parallax` are heightMap:o0 SELF-READS,
>    not external textures (mislabeled upstream of the corpus generator).
> 7. DEFECTS-FOUND item 7 (cross-lane whole-vector assignment) — still open;
>    blocks `synth/mandelbrot`; the browser-side evidence now exists too
>    (synth/gradient: both GPU backends agree against the CPU authority).
> 8. Upstream report: WebGPU/WebGL2 `@builtin(position)` orientation
>    inconsistency (driver now authenticates readback orientation per
>    backend; the upstream defect itself is unreported).
> 9. M6: single-frame ping-pong read-side property is unproven; the only two
>    feedback-shaped records are excluded — keep them excluded until proven.
>
> ### Operating rules that keep binding the next agent
>
> - Bit-exact or fail-closed. No tolerances, no relabels, no epsilon.
>   A dispatched program rendering wrong bytes is the worst failure class.
> - **Two kinds of pin** (see the 2026-08-20 block below for the full
>   lesson): live pins repin from the tree; reconstruction pins never move
>   for a row landing (extend the removal set); when an EMITTER change moves
>   historical regenerated bytes uniformly and the projected spec still
>   regenerates identically, re-freeze once with a justification comment —
>   that is the alias-fix precedent, and the spec-level input locks stay
>   frozen as the independent witness.
> - Oracle resolvers are env-first with one documented staging fallback
>   (`/private/tmp/noisemaker-cpp-dsl-build/`). A stale binary from a
>   per-task build tree has already forged one false defect report.
> - Generated artifacts move only through their generators, exactly once per
>   change, with the pin cascade propagated in dependency order (compat →
>   effect catalog → corpus fixture → sidecars).
> - No session-absolute or user-home paths in committed files; env-required
>   with documented skips (the shader lane's scanner test enforces this for
>   its files).
> - Builds and caches only in external mktemp dirs; PYTHONDONTWRITEBYTECODE=1
>   python3 -B; no pytest; one lane per file surface when parallel.
> - Publication (public Noise Factor MIT repo, push) remains authorized only
>   after the remaining port/parity work and formal review complete.
>
> ### SDD ledger
>
> The execution record for this whole phase (rulings, lane reports, review
> verdicts, exact commands) is
> `.superpowers/sdd/2026-08-24-polymorphic-dsl-and-benchmarks/progress.md`
> and the task-7-* reports beside it. Read the ledger before re-deriving any
> decision recorded there.


> ## STOP CHECKPOINT 2026-08-25 — READ THIS FIRST
>
> This section supersedes every older status block below it. The older blocks
> are retained only as historical evidence. Their statements that this is not
> a Git repository, their effect counts, and their next actions are stale.
>
> ### User boundary
>
> The user stopped this coding run and requested this handoff as the only final
> change. The next agent is explicitly banned from unrelated tasks, unrelated
> changes, unrequested changes, and touching unrelated code. Resume only the
> requested `noisemaker-for-cpp` polymorphic DSL execution, reproducible corpus,
> exact cross-platform parity, benchmark, review, and checkpoint work. Do not
> do cleanup, redesign, publication, or adjacent repository work unless it is
> strictly required by those outcomes and separately authorized where needed.
>
> ### Checkout and Git checkpoint
>
> Work only in:
>
> ```text
> /private/tmp/noisemaker-cpp-continuation.e033lt/work/noisemaker-for-cpp
> ```
>
> The repository now has a clean committed Task 6 base:
>
> ```text
> 4062bc8462e0042571a57e5f805f8333a23e7258
> feat: execute multipass DSL graphs on CPU
> ```
>
> The two preceding commits are:
>
> ```text
> 5505c08 fix: close DSL authority admission gaps
> f8f42ce fix: authenticate DSL catalog construction
> ```
>
> Do not create a branch, worktree, or PR. Do not push or publish at this
> checkpoint. The user authorized a later checkpoint commit, then continued
> DSL implementation; the Task 7 delta below is not ready to commit because an
> independent executor review found blocking integration defects.
>
> ### What Task 6 proved before commit
>
> Task 6 added value-owned multipass graph execution for the authenticated
> Solid -> Blur vertical slice and was independently reviewed clean before
> commit. Retained acceptance evidence included:
>
> ```text
> frontend oracles: 11/11
> render oracles:   11/11
> package consumer: 1/1
> UBSan focused:    36/36
> ASan new paths:   clean (known pre-existing glitch/shapeMixer baseline remains separate)
> ```
>
> The formal whole-project `superpowers:requesting-code-review`, review repair,
> public Noise Factor MIT repository creation, and push still belong only after
> the entire port and pixel-level parity work are complete.
>
> ### Current uncommitted Task 7 delta
>
> `git status --short` immediately before this handoff showed only the following
> Task 7 files (plus this handoff after it is saved):
>
> ```text
> M  include/noisemaker/generated/catalog.hpp
> M  include/noisemaker/graph/executor.hpp
> M  src/graph/executor.cpp
> M  src/typed_generated/typed_manifest.json
> M  src/typed_generated/typed_slice.cpp
> M  tools/glslcpp/generate_typed_slice.py
> ?? tests/fixtures/dsl/executable-corpus.json
> ?? tests/oracles/dsl_executable_corpus.sha256
> ?? tests/test_benchmark_cpu_exact.py
> ?? tests/test_benchmark_shader.py
> ?? tests/test_dsl_executable_corpus.py
> ?? tests/test_graph_features.cpp
> ?? tests/test_task7_generated_routes.py
> ?? tools/benchmark/
> ?? tools/dsl/corpus_authority.mjs
> ?? tools/dsl/generate_executable_corpus.mjs
> ?? tools/dsl/js_shader_benchmark.mjs
> ?? tools/dsl/shader_benchmark_lib.mjs
> ```
>
> Preserve this delta. Do not discard or overwrite it. All build trees, raw
> frames, browser profiles, installed benchmark dependencies, and benchmark
> result JSON remain outside the repository under `/private/tmp`.
>
> ### Task 7 completed pieces
>
> 1. **Generated authenticated factory routing is implemented.** The generated
>    catalog retains 213 physical route rows and exposes 211 canonical unique
>    routes. It selects the authenticated duplicate factories
>    `filter/invert:inv -> bind_filter_invert_inv` and
>    `synth/solid:solid -> bind_synth_solid_solid`, keeps `bitEffects` as a
>    `custom_adapter`, and keeps `filter/text:text` explicitly incompatible.
>    Every route carries program key, canonical/emitted factory, route kind,
>    source SHA-256, typed ABI SHA-256, and binder pointer. Focused route tests
>    were 5/5 and the generator `--check` was green in the implementing lane.
>
> 2. **The authenticated reproducible corpus is implemented.** The generated
>    snapshot contains all 205 effect definitions: 166 admitted and 39
>    explicitly excluded. It authenticates the frozen JS CPU authority and
>    upstream shader revision, generates a canonical default program per
>    definition, includes a dedicated raw top-down RGBA8 JS CPU runner, and
>    uses a custom zero-tolerance comparer that reports dimensions, lengths,
>    first `(x,y,channel)`, mismatch count, maximum delta, and both hashes.
>    The current corpus oracle is:
>
>    ```text
>    326792648a25319a2a83300e0915773b3f74cfb16bc3952bdc8a8a1d2dfc0c07
>    ```
>
>    It is internally bound to the settled typed-manifest file hash:
>
>    ```text
>    51e62f207d5b0ce3f7fdc735c62cc874af81058339a672ccff05833af893a456
>    ```
>
>    The focused corpus/CPU lane was 7/7, Node syntax checks were green, and
>    two fresh JS CPU Blur runs produced identical raw bytes and metadata.
>
> 3. **A narrow real upstream shader benchmark smoke exists.** The driver pins
>    upstream shader commit `117a236679d1db3ab8f0e278230ece277b57564c`, tree
>    `a7a997dfdc807697adba008729dcdfdfcfbaf53c`, Playwright 1.62.1, and the
>    authenticated CPU source lock. It archives the pinned shader revision to
>    external scratch, uses the real upstream `CanvasRenderer`, performs a 2x2
>    orientation probe, reads the physical final texture as raw top-down
>    RGBA8, uses separate correctness and timing renderers, and fences WebGL2
>    and WebGPU samples. One existing 17x11 Solid -> Blur program was exact on
>    both backends against the JS CPU expected bytes:
>
>    ```text
>    expected/actual RGBA8 SHA-256:
>    5462562a69fbf2751af9aecf9b8e423104c866b5465e8a4402ae00214eac928a
>    mismatch count: 0
>    maximum delta:  0
>    WebGL2 result:  /private/tmp/noisemaker-task7-webgl2-blur-result.json
>    WebGPU result:  /private/tmp/noisemaker-task7-webgpu-blur-result.json
>    ```
>
>    This proves only the narrow real browser smoke. It is not evidence that
>    the full corpus or the C++ executor is at parity. The independent shader
>    benchmark review was interrupted by the user's stop and must be rerun.
>
> A fresh combined focused Python run immediately before the stop was:
>
> ```text
> PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
>   tests.test_task7_generated_routes \
>   tests.test_dsl_executable_corpus \
>   tests.test_benchmark_cpu_exact \
>   tests.test_benchmark_shader -v
> 17 tests, OK
> ```
>
> Do not infer that the subsequently started typed-generator check completed;
> the turn was interrupted before its result was captured.
>
> ### Blocking executor review — Task 7 is not ready
>
> Read these reports completely before editing:
>
> ```text
> .superpowers/sdd/2026-08-24-polymorphic-dsl-and-benchmarks/task-7-executor-codegen-preflight.md
> .superpowers/sdd/2026-08-24-polymorphic-dsl-and-benchmarks/task-7-generated-routes.md
> .superpowers/sdd/2026-08-24-polymorphic-dsl-and-benchmarks/task-7-executor-codegen-report.md
> .superpowers/sdd/2026-08-24-polymorphic-dsl-and-benchmarks/task-7-executor-review.md
> .superpowers/sdd/2026-08-24-polymorphic-dsl-and-benchmarks/task-7-corpus-cpu-lane-report.md
> .superpowers/sdd/2026-08-24-polymorphic-dsl-and-benchmarks/task-7-corpus-benchmark-design.md
> .superpowers/sdd/2026-08-24-polymorphic-dsl-and-benchmarks/task-7-platform-inventory.md
> ```
>
> The independent executor review disposition is **not ready**. The current
> `include/noisemaker/graph/executor.hpp`, `src/graph/executor.cpp`, and
> `tests/test_graph_features.cpp` are an incomplete intermediate delta. Exact
> blockers:
>
> - `GraphExecutor::execute` still rejects every route outside the three Task 6
>   Solid/Blur factories.
> - The generated canonical route table is not connected to execution.
> - Multi-sampler routes are neither completely preflighted nor materialized.
> - Pass-derived uniforms fail because execution supplies no resolver.
> - Generated source/typed-ABI route metadata is not authenticated at dispatch.
> - `execute()` copies caller-owned `ExecutionInputs` before complete preflight.
> - Output physical ABI authentication is insufficient.
> - The new tests check helper shape but do not prove actual non-Task6 dispatch
>   or the no-copy/no-allocation-before-failure safety property.
>
> Do not accept, benchmark, or commit Task 7 until these are fixed and reviewed.
>
> ### Exact next implementation sequence
>
> 1. Connect `generated::canonical_routes()` / exact
>    `generated::find_canonical(program_key, canonical_factory)` to
>    `GraphExecutor`. Never dispatch by program key alone; the two duplicate
>    legacy rows make that observably wrong.
> 2. Authenticate the selected route against the value-owned `PassAdmission`,
>    including canonical factory, route kind, source hash, ordered sampler and
>    uniform ABI, output ABI, and typed ABI identity. If `PassAdmission` lacks
>    a load-bearing typed ABI field, extend the value-owned compiler snapshot
>    narrowly and update its hashes/oracles rather than weakening this check.
> 3. Perform a complete read-only plan/input/route/ABI/resource preflight before
>    copying a seed or external surface or allocating a destination.
> 4. Materialize every ordered sampler route, including named intermediates,
>    secondary/external surfaces, and declared filtering. Never alias every
>    sampler to `inputTex`.
> 5. Implement explicit, source-name-based pass-derived resolution for all 20
>    live bindings listed in the executor preflight report. Fail closed for an
>    unknown source. Preserve exact typed compile defines, aspect ratio,
>    canonical defaults, and the owned remap block.
> 6. Add native actual-dispatch tests for at least a non-Task6 duplicate
>    canonical route, a two-sampler route, a pass-derived route, incompatible
>    text rejection, custom-adapter routing, and preflight-before-copy safety.
>    Add `tests/test_graph_features.cpp` to the native CMake test target only
>    after those tests exercise the real executor.
> 7. Build the C++ raw RGBA8 benchmark driver. It must consume the same corpus
>    source bytes/options, compile once for render-only timing, execute the
>    value-owned plan, emit normalized plan metadata, and write raw top-down
>    RGBA8 outside the repository. Do not use PNG, screenshots, epsilon, or
>    normalized randomness.
> 8. Run two independent full admitted-corpus passes through JS CPU and C++ CPU.
>    Require identical normalized program relations and every RGBA8 byte. Keep
>    only bounded diagnostics; do not check raw frames into Git.
> 9. Rerun the independent shader-driver review, address valid findings, then
>    expand WebGL2/WebGPU comparison only over the honestly supported
>    intersection. Record exact mismatches as failures; never relabel them.
> 10. Run fresh strict Release, ASan, and UBSan native builds plus the existing
>     frontend/generator/oracle/package matrix. Use external build directories,
>     remove only those exact disposable directories after recording evidence,
>     request focused independent review, fix all valid findings, and only then
>     create the Task 7 checkpoint commit.
>
> ### Non-negotiable parity contract
>
> `noisemaker-for-cpu` is the behavioral reference implementation for this C++
> CPU port. The upstream `noisemaker` shader platform is the second comparison
> platform for the same reproducible DSL bytes. Success means strict top-down
> RGBA8 equality at every pixel and channel, with dimensions and length checked
> first, mismatch count zero, maximum delta zero, and equal SHA-256 values.
> Matching source text, compilation, generated C++, plan shape, or a screenshot
> is not a substitute for rendered-byte parity.

> ## RESTART CHECKPOINT 2026-08-23 13:32 MDT — READ THIS FIRST
>
> This section supersedes every older status block below it.  The previous
> blocks remain historical evidence; do not use their counts, hashes, or next
> actions as current truth.
>
> ### Workspace and hard constraints
>
> Actual checkout:
>
> ```text
> /private/tmp/noisemaker-cpp-continuation.e033lt/work/noisemaker-for-cpp
> ```
>
> Stable Scaffold link:
>
> ```text
> /Users/aayars/platform/scaffold/.cpp-staging-link
> ```
>
> The checkout is still not a Git repository.  Do not create a branch,
> worktree, PR, commit, remote, or publication state during porting.  Build,
> compiler-probe, regeneration-cache, and temporary output belong only under
> `/private/tmp`.  Use `apply_patch` for edits.  Every Python command must set
> `PYTHONDONTWRITEBYTECODE=1` and use `python3 -B`; do not use pytest.  Preserve
> unrelated work and every frozen historical hash.  When reconstructing an
> older typed-slice milestone, add newly landed rows to that test's later-row
> removal projection rather than replacing the frozen expected hashes.
>
> Formal `superpowers:requesting-code-review`, feedback repair, Git setup, and
> public Noise Factor MIT publication remain authorized only after Fractal,
> Julia, and Dither are complete and the full exact parity/integration matrix
> is green.
>
> ### Live catalog state
>
> | Metric | Current value |
> | --- | ---: |
> | Canonical corpus programs | 212 |
> | Typed rows | **209** |
> | Generated public catalog binds | **211** |
> | Sorted typed-key SHA-256 | `bb8da3153926d085430f4da2952396070564e8ee57b58ff42cf84609c1b6b535` |
> | Absent from typed slice | **3**: Dither, Julia, and the already-public Wormhole deposit scatter path |
> | Genuinely unported effects | **2**: Dither and Julia |
>
> Current generated artifacts:
>
> ```text
> 41b063ada5e5f1708232f77c4a6fe5812f440e0476cfbdcff09960170a7ef3a8     28,174  tools/glslcpp/typed_slice.json
> ad5a21f623002d911661a3a7682374b3bbff5155a617765142544937afbf322f  2,521,549  src/typed_generated/typed_slice.cpp
> fd59e692dac2d17cb5c3912379fae0b572ed46af2b5e9e290cfc5ddf6c8a1ed0    336,057  src/typed_generated/typed_manifest.json
> edbb57c00769c2513afde4d53a36eb2903c0e5720ba8fd6f112ce6bb0f659220     19,303  include/noisemaker/generated/catalog.hpp
> ```
>
> The checkout measured about 85 MB and 2,741 files.  There are no live build,
> object, archive, regeneration-cache, or pytest-cache trees in it.  At this
> checkpoint the 23 disposable `.pyc` files and four live cache directories at
> `tests/__pycache__`, `tools/__pycache__`, `tools/glslcpp/__pycache__`, and
> `tools/glslcpp/frontend/__pycache__` were removed.  Do not delete the bytecode inside
> `docs/port-engineering/census/snapshot/20260812T225121Z`; that is frozen
> historical evidence.  The numerous logs under `docs/port-engineering` are
> also retained engineering evidence, not active build output.
>
> ### Fractal row 209: current implementation and exact evidence
>
> `classicNoisedeck/fractal:fractal` is zero-based typed index 8 and is bound
> publicly between Effects and Glitch.  Its source-bound frontend profile now
> authenticates the 29-uniform ABI; exact source/interface/function hashes;
> four counted loops and their metadata-backed runtime bound; mode `[0,1]`;
> terminal fallbacks; alpha, distance/fract, palette, HSV, and Newton node
> identities; the exact Newton body-span census; and one-time emitter
> consumption/cardinality.
>
> The Fractal-only emitter paths preserve canonical JavaScript Number
> semantics for:
>
> - escaped-background `bgAlpha * 0.01`;
> - palette distance mapping and `fract`;
> - direct HSV hue and HSV arithmetic through `FloatExpr<3>` binary64 lanes;
> - palette cosine/Oklab arithmetic with Float32 stores only at canonical
>   output-array boundaries;
> - Newton coordinate/iteration state, direct main-call coordinates, and a
>   local normalized two-argument `Math.hypot` equivalent.
>
> The first Newton repair removed the generic Vec2 Float32 state divergence.
> The second fixed the one-double-ULP `std::hypot`/V8 `Math.hypot` difference.
> A tempting Oklab component narrowing was explicitly rejected by a direct
> JS/C++ checkpoint: it changed pixel `(3,0)` red from expected `0x3dba27f7`
> to `0x3dba2800`.  Keep the current Number `a`/`b` intermediates.
>
> Current retained gates:
>
> ```text
> Fractal frontend/oracle/runtime-loop focused suite: 47 tests OK
> check_corpus.py --check:                       OK
> check_semantics.py --check:                    bodies OK (212)
> generate_typed_slice.py --check:               typed slice OK (209)
> fresh AppleClang 16 Release build:              clean with -Wall -Wextra -Wpedantic -Werror -ffp-contract=off
> fresh native executable:                       347 PASS, 0 FAIL
> fresh CTest:                                   1/1 passed
> ```
>
> Fresh native build directory for this checkpoint:
>
> ```text
> /private/tmp/noisemaker-fractal-strict.RA8z7j
> ```
>
> The six frozen canonical Fractal cases are exact at every Float32 word and
> every RGBA8 byte across public/direct/repeat paths, delayed-Bindings lifetime,
> and mutation/comparer controls.  Direct and public invalid `mode=-1` and
> `mode=2` binding negatives were added after review; the strict harness stayed
> 347/347.
>
> ### Fractal is not yet accepted complete: genuine review blocker
>
> Independent review found that the generic Julia and Mandelbrot generated
> helpers still store iterative coordinates in `glsl::Vec2<float>` while the
> pinned CPU adapter keeps JavaScript Numbers.  Their `mode=1` returns also use
> Float32-vector `length` rather than Number-state `Math.hypot`.  The current
> six-case package covers Julia/Mandelbrot mode 0 but does not deliberately
> cover their mode-1 or near-escape-threshold boundaries.  Therefore 347/347
> proves the frozen package, not all reachable Fractal controls.
>
> The same review claimed direct HSV hue was narrowed.  That claim is rejected:
> `glsl::FloatExpr<3>` stores `double` lanes, the custom helper accepts it by
> value, and the `newton-hsv-tile` exact-word case is green.  Do not redesign
> the already-exact HSV path.
>
> Next agent must finish Fractal before beginning standalone Julia:
>
> 1. Extend the immutable Fractal oracle generator with explicit Julia mode-1,
>    Mandelbrot mode-1, and adversarial near-threshold/nonrepresentable
>    coordinate cases.  Regenerate the JSON, sidecars, native include, and
>    load-bearing case-count assertions; never invent expected C++ values.
> 2. Reproduce the new cases red against the current generated C++.
> 3. Add narrowly authenticated Fractal-only Number scalar paths for the exact
>    Julia and Mandelbrot functions/calls.  Reconstruct their main-call x/y
>    from `context.frag_coord`, `tileOffset`, and `fullResolution` as Newton
>    does; mirror the pinned adapter's operation order and local normalized
>    two-argument hypot.  Do not widen shared Vec2 semantics.
> 4. Regenerate once, require all expanded exact cases green, and rerun every
>    gate above in a new external strict build.
>
> Read the severity-ranked review and numeric trace before editing:
>
> ```text
> /Users/aayars/platform/scaffold/.codex-noisemaker-classic208/task-26-fractal-numeric-review.md
> /Users/aayars/platform/scaffold/.codex-noisemaker-classic208/task-23-fractal-newton-diagnosis.md
> ```
>
> ### Python integration checkpoint
>
> A run of every Python test module except `tests.test_typed_generator` reached
> 1,525 tests in 1,052.851 seconds with 40 skipped and 15 failures.  All 15 were
> isolated historical projection failures: Edge, Glyph Map, and Task 35 did
> not remove the newly landed Fractal row.  Each exact failing method now
> passes after adding only Fractal to its later-row exclusion set:
>
> ```text
> tests.test_edge_bvec3_contour...test_edge_is_exact_single_program_delta_from_glyph_178       OK
> tests.test_glyph_map_nonnegative_int_shift...test_glyph_map_is_exact_single_program_delta_from_scanline_177  OK
> tests.test_task35_bitwise_number_profile...test_current_and_task35_absent_generation_are_exact_and_isolated OK
> ```
>
> No second 1,525-test run has been retained after those three focused repairs.
> Run it, or the final full discovery, before accepting Fractal.
>
> `tests.test_typed_generator` is the remaining integration lane at checkpoint.
> Its first 272-test run had 67 stale live/current/history pins.  The sole owner
> then repaired current artifact sizes/hashes, counts, ordinals/windows,
> namespaces, catalog/manifest pins, and Fractal later-row projections while
> preserving frozen history.  Five current artifact tests, committed-slice
> equality, focused Task21-32 groups, and the affected historical
> reconstructions are green.  A new hermetic full-module run emitted only
> passing dots for roughly three minutes but was deliberately interrupted for
> this restart, so its exact final failure count remains unknown.  Read:
>
> ```text
> /Users/aayars/platform/scaffold/.codex-noisemaker-classic208/task-24-fractal-typed-generator-repair.md
> ```
>
> Re-run the full module and record exact remaining failures.  Repair live
> artifact/count/ordinal pins from measured outputs; for old milestones add
> Fractal to their later-row projections.  Never bless a failing regenerated
> historical hash as the new frozen expectation.
>
> ### After Fractal acceptance
>
> Port `synth/julia:julia`, then `filter/dither:dither`, each with the same
> immutable CPU authority, custom exact comparer, source-bound frontend,
> adversarial pixel cases, fresh strict native build, and full Python/native
> matrix.  Only after both land: run formal code review, address every valid
> finding, verify repository hygiene, create the public Noise Factor MIT OSS
> repository, and push normally without PR/worktree/feature-branch machinery.

> ## RESTART CHECKPOINT 2026-08-22 23:12 MDT — READ THIS FIRST
>
> This is the live continuation boundary. Stop reconstructing history from the
> older status blocks below and start here.
>
> ### Workspace and operating constraints
>
> The actual checkout is:
>
> ```text
> /private/tmp/noisemaker-cpp-continuation.e033lt/work/noisemaker-for-cpp
> ```
>
> Scaffold exposes it as:
>
> ```text
> /Users/aayars/platform/scaffold/.cpp-staging-link
> ```
>
> The checkout is **not a Git repository yet**. Do not create a branch,
> worktree, PR, commit or remote during porting. The user authorized final
> publication only after the entire port is coded, exact pixel parity is
> complete, formal `superpowers:requesting-code-review` has run, and all review
> feedback is addressed. Publication must then use the usual public Noise
> Factor MIT OSS pattern.
>
> Use `apply_patch` for edits. Every Python invocation must be
> `PYTHONDONTWRITEBYTECODE=1 python3 -B ...`. Do not use pytest. Build only in a
> fresh `mktemp -d` path under `/private/tmp`, and clean that exact path. Never
> put a regeneration cache, build tree, object file, `__pycache__`, or
> `.pytest_cache` in this checkout. At checkpoint the tree is **82 MB**, has no
> live build/cache/compiled-artifact directories, and no test process is
> running. The pyc files under the frozen 2026-08-12 census snapshot are
> historical evidence and must not be deleted.
>
> ### Live port state
>
> | Metric | Current value |
> | --- | ---: |
> | Canonical corpus programs | 212 |
> | Typed rows | **207** |
> | Generated catalog binds | **209** |
> | Sorted typed-key SHA-256 | `1638e3159c54a905f591f16df3a1b05416993c6e240cfc7f6c0d0d1ec2234bae` |
> | Absent from typed slice | **5** (one is already public via the wormhole scatter path) |
> | Genuinely unported | **4**: Classic Noise, Fractal, Dither, Julia |
>
> Current generated artifacts are clean for the 207-row state:
>
> ```text
> bc59f36b175807e25a7f57c434b25b2678c7ecf2e68293ae73698c0bc8b4167b   27,727  tools/glslcpp/typed_slice.json
> 0f8cc49e0faaa7d3218886ef97845edf5a0fffdeb5bca3a654bff087967552e4 2,461,921  src/typed_generated/typed_slice.cpp
> d98b04d5a9c0139c51d42339ffc21d3ef28dc7fd1330dedbeed840bc8cd699f6  332,610  src/typed_generated/typed_manifest.json
> 35c67a0b85e26985cf413637813e5b41003c7f5d8950edc327194a4079d48349   19,113  include/noisemaker/generated/catalog.hpp
> ```
>
> `docs/port-engineering/REMAINING-EFFECTS.md` is stale (its header still says
> 206/208). Refresh it from live artifacts after Classic Noise lands; preserve
> its historical sections.
>
> ### Moodscape is row 207 and is accepted locally
>
> `classicNoisedeck/moodscape:moodscape` is zero-based index 11 (`typed_11`),
> between Lens and Refract. It has:
>
> - a source-bound key-specific frontend projection, exact defines
>   `COLOR_MODE=2`, `NOISE_TYPE=10`, and exact 13-uniform native ABI;
> - an immutable 22-file canonical CPU authority package with six exact
>   Float32/RGBA8 cases and mutation/forgery coverage;
> - exact native public/direct/repeat comparison and delayed-binding lifetime
>   coverage;
> - all source/generator gates green at 207, independently reviewed repairs,
>   and a fresh strict AppleClang `-Werror` native build with executable PASS
>   and CTest 1/1.
>
> The last fully retained Python baseline before Moodscape was 1,755 tests OK,
> 40 skipped. Moodscape's first full discovery found three stale Task25 pins;
> after repair the second found one accidental Task21 exclusion. The exact
> affected methods were repaired and independently re-reviewed clean. A third
> discovery was still running when Classic Noise files began changing and was
> deliberately terminated for this restart, so **do not claim a final clean
> full Python suite yet**. The post-Classic full run is the required retained
> acceptance for both rows.
>
> ### Classic Noise: oracle and frontend are DONE; row integration has NOT begun
>
> Target: `classicNoisedeck/noise:noise`.
>
> Source authority:
>
> ```text
> raw bytes:       31,255
> raw SHA-256:     4cd68543729f94788ef6fa2a484dd47d76154814b027128bef5eb9c8d7461663
> normalized:      14,064 bytes
> normalized SHA:  9f97d19e355f32e3821057ba8859770a87cbec56c57946d14378764deb8da0f0
> canonical CPU:   canonicalFactory12
> factory SHA:     b5b2743ef755306503df6ab2ab5dd81ab944a121e0fd383ef8d641db4d247424
> fixed defines:   COLOR_MODE=6 LOOP_OFFSET=300 METRIC=0 NOISE_TYPE=10 REFRACT_MODE=2
> ```
>
> The dedicated canonical oracle package is implemented and independently
> reviewed **CLEAN**. It authenticates the immutable 22-file CPU closure,
> canonical/public factory identity, all 24 uniforms plus five compile-time
> defines, eight exact cases, dead-binding invariance, strict raw Float32 word
> and complete RGBA8 comparison, repeat/storage/control/input-lifetime rules,
> five independently executed behavioral mutations, negative authority paths,
> materializer self-tests, and C++20 fixture compilation.
>
> ```text
> 7768dad900e68e565eb9a5857f423dbbe4a892234b56116f3cf705456664f28d  docs/port-engineering/classic-noise-parity/classic_noise_oracle_generator.mjs
> a0e39957155553cb21e814339e502d272db1c6640f5bfc9ea6a47a659032877d  docs/port-engineering/classic-noise-parity/classic-noise-oracles.json
> f85c69762d07fa49c0002725c92b5f679ae6bb52c09e1e7b20f08c0067e217f2  docs/port-engineering/classic-noise-parity/classic-noise-oracle-report.md
> 7821daf2782c2ad47110b381b63cada71415c3358d0c2d818d48006fd9e86f5d  tools/glslcpp/generate_classic_noise_native_oracle_include.py
> ae4bee722021289b31e66c2875cd595379858f3cd387429708adcf8945b579e5  tests/oracles/classic_noise_expected.inc
> ```
>
> The dedicated frontend/projection/runtime-loop lane is also implemented and
> independently reviewed **CLEAN**. Its accepted profile is
> `classic-noise-frontend-admission-v1`. It authenticates the complete source
> tree before exact dead-closure projection, removes unreachable scalar-XOR,
> mutable-global, typed-index and mat3 carriers, preserves reachable
> `rotate2D`/mat2, clears and rebuilds canonical loop proofs, reattaches the
> `octaves` runtime proof `[1,8]`, and authenticates the projected tree in both
> generator and emitter.
>
> First review found two real defects: `zip()` accepted truncated proof ledgers,
> and the exported runtime authenticator lacked a whole-tree fingerprint. They
> were repaired tests-first. The same reviewer directly proved rejection of
> empty/short function and declaration proofs, missing loop summary, empty
> matrix/consumed ledgers, and an unrelated dead-function rename. Re-review:
> **43 tests OK, no remaining findings**.
>
> ```text
> bccfa07965ec7ff9220890e5db7845c6ee658378f70d322adb69c56f542d56de  tools/glslcpp/frontend/noise_frontend_profile.py
> 443e9c00d2fdb1f14c3fb3f86e0e2318181b88271bb29c08d4bcf15bd83d3caa  tools/glslcpp/generate_typed_slice.py
> c5f270e61eddf1b122a3c0cc1fe3eaa91d0f42df9c3f892b1ea1eae4754491ca  tools/glslcpp/emit_typed_cpp.py
> 7a2a38b6aac6b5f9b8bcb938cfb891d2f1d1f778454f7912ef70b95b831829cd  tests/test_noise_frontend_profile.py
> ```
>
> Root also re-ran the final profile at 9/9 and the four current source gates:
>
> ```text
> check_corpus: ok
> check_semantics: bodies ok (212 programs)
> generate_kernels.py --check: exit 0
> generate_typed_slice: typed slice ok (207 programs)
> ```
>
> ### Exact next action: land Classic Noise as row 208
>
> Do not redesign either accepted lane. Add this sorted row at zero-based index
> **12**, immediately after Moodscape and before Refract:
>
> ```json
> {
>   "defines": {
>     "COLOR_MODE": 6,
>     "LOOP_OFFSET": 300,
>     "METRIC": 0,
>     "NOISE_TYPE": 10,
>     "REFRACT_MODE": 2
>   },
>   "noise_frontend_profile": "classic-noise-frontend-admission-v1",
>   "program_key": "classicNoisedeck/noise:noise"
> }
> ```
>
> There is intentionally no separate `runtime_loop_bound_profile` row field:
> the accepted Classic Noise frontend owns the projection-aware runtime proof.
> Defines are compile/provenance values only and must not become native uniform
> bindings. The emitted binder must have exactly these 24 uniforms in source
> order:
>
> ```text
> time seed resolution tileOffset fullResolution xScale yScale octaves ridges
> refractAmt kaleido loopScale speed paletteMode paletteOffset paletteAmp
> paletteFreq palettePhase cyclePalette rotatePalette repeatPalette hueRange
> hueRotation wrap
> ```
>
> After adding the row, regenerate the four canonical artifacts exactly once,
> then repair the mechanical census without repinning frozen history. The
> projected live state is 208 typed rows, 210 catalog binds, four absent rows,
> Classic Noise namespace `typed_12`, Refract and every later namespace shifted
> by one, and sorted-key SHA:
>
> ```text
> 2a1b723df783e8f3e6309c2b02edcfdb7fd8daf16c0df59cdde5c32ae27a18e5
> ```
>
> `tests/test_typed_generator.py` needs current 207->208, catalog 209->210,
> absent 5->4, the new live hash, the Classic Noise define row, and live ordinal
> shifts. Frozen historical reconstruction tests must instead remove Classic
> Noise so their old counts/hashes remain unchanged. The read-only census found
> these projection/removal sites (line numbers are pre-integration and may move):
>
> ```text
> Task23 2717
> Task24 754,1699,11220
> Task22 10665
> Task26 13442
> Task27 14345,14436,14509
> Task28 15579
> Task29 16440,16529
> Task30 17274
> Task31 18215
> Task32 18768,18858
> single-delta fixtures 7910,8032,8155,8276
> LATER_ROWS 19429,20126,21393
> integration projections 22817,23582,24106,24695
> Task25 current/transitional removals 10951,11220
> ```
>
> Live ordinal shifts identified by the same census are at old lines
> `9458,11035,11036,13488,14568,16544,17166,18123,19427,20124,23706,24232`.
> Task21 live/current projections retain the new row and move 144->145,
> 184->185, `(184,186,26,212)`->`(185,187,25,212)`. Do not add Classic Noise
> to Task21 merely to preserve old counts. Preserve the unrelated pre-existing
> duplicate `cellRefract` exclusions near old lines 9139 and 10934.
>
> Native integration belongs in `tests/test_generated_kernels.cpp`; CMake needs
> no source-list change. Include `oracles/classic_noise_expected.inc`, add four
> wrappers adjacent to Moodscape, and implement exact public/direct/repeat and
> metadata/mutation tests. The oracle fixture lists 29 authority bindings
> because it includes five defines; the C++ `Bindings` object must contain only
> the 24 source uniforms. Assert the catalog function pointer and 210-entry
> ordering. Use the project's custom raw-word/RGBA comparer pattern. Preserve
> controls by snapshotting the actual `Bindings` object before bind/run, test a
> delayed kernel after a local `Bindings` scope ends, test both overflow paths,
> and assert all mutation metadata/witness records rather than only counts.
>
> Then run, in order:
>
> 1. oracle generator/materializer `--check` and `--self-test`;
> 2. focused Classic Noise oracle/frontend/generator tests;
> 3. all four source/generator `--check` gates;
> 4. a fresh strict AppleClang C++20 `-Werror` native build and executable,
>    then CTest 1/1, entirely under `/private/tmp`;
> 5. independent review of the generated/native landing, repair and re-review;
> 6. the retained full Python discovery, then a final cache/size sweep.
>
> ### After Classic Noise
>
> Re-probe rather than carrying this by arithmetic, but the expected genuinely
> unported set is then exactly:
>
> ```text
> classicNoisedeck/fractal:fractal
> filter/dither:dither
> synth/julia:julia
> ```
>
> `filter/wormhole:deposit` remains absent from the typed slice but already
> public through the scatter pass. Current preflight says Dither has an exact
> nine-input-palette oracle but a deep error-row/array/loop/bitwise frontend and
> a public non-input-palette `.reduce` failure; Julia has a strong adapter oracle
> but structs, `out`, and two 1000-trip loops; Fractal lacks a canonical factory.
> Do not weaken or normalize any of these obstacles. Use the same source-bound,
> mutation-backed, pixel-exact approach used for Moodscape and Classic Noise.
>
> No formal completion review or publication has occurred. Those remain the
> last steps only after all three remaining effects are honestly resolved and
> the entire exact parity matrix is green.

> ## TOOLING DEBT PAID 2026-08-20 — the reconstruction memo
>
> The suite's quadratic cost is fixed. `tools/glslcpp/regen_cache.py` is a
> content-addressed memo over `generate_outputs`, off unless
> `NOISEMAKER_REGEN_CACHE` names a directory **outside** the checkout.
>
> ```
> export NOISEMAKER_REGEN_CACHE="$RUN_ROOT/regen-cache"
> python3 -m unittest tests.test_typed_generator     # transparently cached
> python3 -m tools.glslcpp.regen_cache --verify      # re-derive and compare
> python3 -m tools.glslcpp.regen_cache --stats
> ```
>
> Measured at 191 rows. One regeneration is ~29 s and is 96-99 % of these
> modules' wall clock. Six milestone modules: **500.7 s → 9.6 s warm.**
> `test_typed_generator`: ~2400 s uncached → 1259 s cold → **225 s warm**, a
> ~10x improvement, with an identical failure set across three consecutive
> runs. Each repair iteration is now minutes, not most of an hour.
>
> **The key covers spec + pinned corpus + every `tools/glslcpp/**.py`**, so an
> emitter change invalidates the whole cache. That property is not optional:
> without it the 2026-08-19 alias fix would have served pre-fix bytes and all
> 42 moved pins would have stayed green.
>
> ### The hole the suite found, and the shape of the fix
>
> The first version keyed on the spec alone and **broke six forgery tests**.
> They patch a collaborator (`analyze_program`, `validate_capabilities`,
> `apply_smooth_edge_luma_weights`, …) and require `generate_outputs` to
> RAISE; the spec is untouched, so the memo returned the good bytes and the
> guard never fired. It failed in the safe direction — the tests went red
> rather than silently passing — but it was a real hole.
>
> `_collaborators_are_patched()` now bypasses the cache, read and write,
> whenever any callable the generator might call **differs by identity from
> an import-time snapshot**. `load_slice` and `generate_outputs` are the only
> exclusions (patching the first is how a projection is expressed and its
> result is in the key; the second is the wrapper itself).
>
> That shape was arrived at by being wrong twice, and the suite caught both:
>
> 1. A hand-written list of collaborator names missed
>    `apply_smooth_edge_luma_weights` — one of an `apply_*` family that grows
>    with every carrier, so the list would have gone stale at the next
>    landing.
> 2. An `isinstance(..., NonCallableMock)` scan missed
>    `apply_const_global_tables`, because `mock.patch.object(target, name,
>    a_lambda)` installs the lambda and no Mock ever exists. That surfaced as
>    a **flaky test** — pass or fail depending on whether an earlier test had
>    populated the entry. Three consecutive runs now give identical failure
>    sets.
>
> Identity-against-snapshot catches all three shapes and anything else, which
> is why the guard is not a check for "looks mocked".
> `tests/test_regen_cache.py` (29 tests) pins all of this, each guard
> exercised in the failing direction.
>
> An audit reports, it never crashes: the first `--verify` died on a poisoned
> entry left by the pre-guard cache instead of counting it. It now reports
> per-entry and tells you to delete the cache.
>
> Do not trust a cached green run you have not audited: `--verify` re-derives
> every entry from its stored spec and requires byte equality.

> ## STATUS 2026-08-20 (session close) — grime is row 191 and the Python census is GREEN
>
> `filter/grime:grime` is landed as typed row 191 (insertion index 54,
> namespace `typed_54`), promoting the varying-uv carrier out of PREPARED
> together with its float-bit ingress companion. The census cascade that
> lands with it is **finished**, and a second, unrelated cache defect was
> found and fixed on the way.
>
> ### Verified
>
> - four generator gates exit 0 at **191 programs**;
> - artifacts read off the tree, not carried: `typed_slice.json`
>   24,575/`6b215a7c…`, `typed_slice.cpp` 2,095,000/`a582cb1f…`,
>   `typed_manifest.json` 305,807/`0a04836b…`, `catalog.hpp`
>   17,655/`2f85ca26…`; sorted 191-key SHA `1a4da414…`;
> - 191 typed rows, 193 catalog binds, 21 absent, **192 of 212 distinct
>   ported**, 20 genuinely unported;
> - native Debug **271 PASS / 0 FAIL**, zero warnings, ctest 1/1, built
>   out-of-tree;
> - `tests/test_typed_generator.py` **269 tests, OK**;
> - the whole Python suite, `unittest discover -s tests -p 'test_*.py'`:
>   **1462 tests, OK**;
> - `python3 -m tools.glslcpp.regen_cache --verify`: **95 entries, 0 bad, 0
>   unverifiable** (a full re-derivation; it costs about forty minutes, so
>   run it in the background).
>
> ### The lesson: two kinds of pin, and telling them apart
>
> This is the part worth reading. Nearly every red test in the cascade was
> one of two shapes, and they take **opposite** repairs:
>
> **A reconstruction pin** freezes the generated bytes of an earlier
> milestone — an isolation proof that landing new rows perturbs nothing
> already emitted. When a row lands, the fix is to add its key to that
> test's removal set, so the projection still describes the milestone and
> the frozen digests **do not move**. Repinning one instead silently
> destroys the proof: afterwards you cannot distinguish "grime landed" from
> "grime perturbed 128 other programs", which is the only thing the test
> existed to tell you. The suite says so itself, in a comment above one of
> them: *"bumping them would be measuring a different milestone than the one
> this class froze."*
>
> **A live pin** describes the current slice — its key count, its sorted-key
> SHA, an ORDINAL, the committed artifacts. Those move on every landing and
> repinning is the whole point. Repin from the tree (`shasum`, `stat`), never
> from a report.
>
> Discriminator: *does the pinned value describe generated output of a
> projected spec, or the live one?* Thirty removal sets needed grime; every
> frozen milestone digest in the file is still HEAD's.
>
> An earlier pass in this session got this wrong and repinned about two dozen
> reconstruction digests. It was caught by noticing that five red tests went
> green from the exclusion alone, with zero repins. The repair was to restore
> the file to HEAD, insert grime into every removal set, and only then repin
> what still moved: **216 moved equalities → 136 → 80 → 15 → 0**, and roughly
> eighty frozen digests that the first pass would have overwritten are
> untouched.
>
> ### The tool that made it tractable
>
> `unittest` aborts a test at its first failing assertion, so one round of
> repair yields one moved pin per test and the cascade takes as many rounds
> as a test has pins. A ~40-line runner that wraps `TestCase.assertEqual`,
> **records** the mismatch instead of raising, and prints
> `line / test / WANT / GOT` collapses that to one run per round. Two
> cautions, both learned here:
>
> - it reports, it never edits — rewriting an expected *tuple* to the actual
>   value is how a neighbour-window assertion stops asserting anything. When
>   a window moves, move its **index**; the well-built classes already write
>   it as `keys[self.ORDINAL - 1:self.ORDINAL + 2]`, and then only the
>   `ORDINAL` constant needs to change;
> - swallowing `AssertionError` breaks any test whose barrier is
>   `assertRaises(AssertionError)`. Three "failures" it reported for
>   `test_task26_cpp_native_oracle_table_…` were artefacts of the tool.
>
> **Do not blanket-shift windows.** A script that incremented every
> `typed[a:b]` near a traceback once ran thirty rounds against a test failing
> for an unrelated reason and walked `typed[1:4]` to `typed[31:34]` on an
> assertion that should never have moved.
>
> ### A real cache defect the alias suite caught
>
> `tests/test_pooled_vector_alias.py` failed **4 tests with the memo on and 2
> with it off**. The two extra were the cache serving pre-patch bytes: the
> guard snapshotted module-level callables in `generate_typed_slice`,
> `check_corpus` and `check_semantics`, but the alias suite patches *methods
> on `emit_typed_cpp._Emitter`* — a class in a module the generator reaches
> through `from … import`, so it is not even an attribute of the generator.
> Three neutralization tests whose entire job is to go RED came back green.
>
> Fixed in `regen_cache.py`: the snapshot now walks **every module under
> `tools.glslcpp` and every class inside them**, `install()` imports the
> package up front so the baseline cannot be short (a module cannot be
> snapshot on first sight — `mock.patch` imports its target *before* patching
> it, so first sight is already the patched value), and comparison reads
> `vars(target).get(name)` rather than `getattr`, because a classmethod hands
> back a freshly bound object on every access and `getattr` identity reported
> every run as patched. Two new tests in `tests/test_regen_cache.py` pin both.
>
> That is the third hole in this guard, all found by the suite, all in the
> safe direction. The pattern is consistent: **any enumeration of what to
> watch goes stale.** Prefer "everything under the package" to a list.
>
> ### Not done
>
> - **DEFECTS-FOUND item 7** (cross-lane whole-vector assignment) is recorded
>   and NOT fixed. It blocks `synth/mandelbrot`.
> - The **binding-sourced alias class** (`synth/osc2d`, `synth/perlin`) is
>   deliberately not aliased — a `glsl::Vec2&` cannot bind to a field of
>   `const State&`. `test_pooled_vector_alias` pins that the emitter guard
>   for it is reachable.
> - Oracle packages for kaleido and effects.
> - The session goal was 195 distinct ported effects; the tree is at **192**.
>
> ### Working-tree state
>
> Nothing is committed. `git status` shows the grime landing plus the tooling
> in one changeset; the three commits already on `main` are `977ffc7`,
> `cbfa82f`, `a1b8deb`. There are no remotes, so nothing has been pushed.
> Run the suite with the memo before believing anything:
>
> ```
> export NOISEMAKER_REGEN_CACHE="$SOMEWHERE_OUTSIDE_THE_CHECKOUT/regen-cache"
> python3 -m unittest discover -s tests -p 'test_*.py'
> python3 -m tools.glslcpp.regen_cache --verify
> ```


> ## STATUS 2026-08-19 (independent review of commit `04ea735`) — READ FIRST
>
> A separate agent re-verified the rows 186-190 commit from scratch. Most of
> it holds up exactly. One shipped row does not.
>
> ### Reproduced independently, every figure matching the claim
>
> Four generator gates exit 0 at 190. Artifacts byte-for-byte **as committed
> at `04ea735`**: `typed_slice.json` 24,374/`bb8bf931…`, `typed_slice.cpp`
> 2,075,210/`28a28b1a…`, `typed_manifest.json` 304,207/`b0d2f812…`,
> `catalog.hpp` 17,572/`34bbbe17…`; sorted 190-key SHA `199fbb5e…`. (The
> alias fix below moved two of those — the live values are in
> `counted-for-parity/parallax-acceptance.md`; the slice spec, the catalog
> and the 190-key SHA did not move.) Census
> re-derived from the artifacts rather than carried: 190 typed, 22 absent,
> 192 binds, 191 of 212 distinct ported, 21 genuinely unported. Native
> **Debug 268/0, Release 268/0, ASan+UBSan 268/0** — ctest 1/1, zero
> warnings, zero sanitizer diagnostics, `-ffp-contract=off` read off
> `flags.make` in every lane. **x86_64 266/2**, both failures exactly the
> documented pre-existing arch-NaN fixtures. `DEFECTS-FOUND` item 4 did not
> reproduce again and is still not claimed fixed.
>
> **The wave-2 native batch and parallax's assembly gate are now DONE** — the
> `typed_80` pixel scope (7 symbols, 458 instrs ARM64 / 687 x86_64) carries
> zero indirect branches, zero jump tables and zero fused-FP on both
> architectures, with TU-wide fused-FP zero on both. The cellRefract and
> wobble oracle packages both re-check green from a fresh authority snapshot;
> all six pinned CPU authority files still hash as pinned at `4834b014`.
>
> ### Found AND fixed: `filter/parallax` (row 190) was not bit-exact
>
> See `DEFECTS-FOUND.md` item 6,
> `counted-for-parity/parallax190-alias-divergence.md` and
> `counted-for-parity/parallax-acceptance.md`. The JavaScript's
> `var prevUV = rayUV` aliases one `PooledFloat32Array`, so the march
> refinement is a **no-op** in the authority; the emitter value-copied and
> performed it. Measured over 20 pixels: all 309 march coordinates identical,
> the final `getInput` coordinate different on **20 of 20**, two pixels
> changing colour.
>
> **Fixed.** `emit_typed_cpp.py` now emits `TYPE& name = source;` for a
> `vec2/vec3/vec4` declaration initialized from a bare vector identifier when
> a write to either name makes the aliasing observable. 28 declarations
> became references; `typed_slice.cpp` grew by exactly 28 bytes;
> `typed_slice.json` and `catalog.hpp` are byte-identical; the 190-key SHA is
> unchanged. The whole native suite stayed green through the change, which is
> the load-bearing evidence — every program with oracle coverage still
> matches the authority.
>
> **Row 190 now has the oracle package it should have had**: generator with
> full provenance (immutable-snapshot-only, six pinned authority hashes,
> factory text cross-validated against cellRefract), 6 cases, a 6-mutant
> ledger, a materializer with 38 self-test checks, and three
> `typed_parallax190_*` native tests. The `refinement-copy-restored` mutant
> reproduces the old emission exactly and is witnessed by 3 of 6 cases, so
> the regression cannot land silently again. Note `full-basic` does **not**
> witness it — the defect was invisible at that shape, and the generator
> fails if that ever changes.
>
> **Three classes are still open, one of them a second confirmed defect.**
> The first census said nine typed rows carry the alias shape; that was an
> undercount — it missed parameter- and binding-sourced aliases. The measured
> figure is **13 typed rows**, and the **binding-sourced pair
> (`synth/osc2d`, `synth/perlin`) is NOT fixed**: they alias `fullResolution`
> and write it in place, which the port cannot express through a
> `const State&`. Whether that is observable is unmeasured.
>
> **`DEFECTS-FOUND.md` item 7 — `synth/gradient` is shipped and NOT
> bit-exact.** A whole-vector assignment whose right-hand side reads a lane of
> its own destination that an earlier component write already clobbered.
> Proven with a mutant: the port matches the unaliased form on all 120 lanes
> and disagrees with the authority on 89. The item-6 alias fix does **not**
> change it. `mixer/shapeMask` carries the same JS tuple shape but is NOT
> divergent (verified 0/168 across all 8 `shape` values) because its GLSL
> writes the components as separate statements, which the emitter already
> lowers sequentially.
>
> **This blocks `synth/mandelbrot`.** `mandelbrot.glsl:247-250` is the
> identical construct and it is on the wave-2 landing list. Landing it against
> today's emitter repeats parallax's history exactly — every structural gate
> green, the pixels wrong. Fix item 7 first.
>
> ### Repaired in this review
>
> The 4 residual `test_typed_generator` failures — all stale live pins that
> parallax's insertion at index 80 moved, none a reconstruction break:
> `SOURCE_GLOBAL_LITERAL_INT_KEYS` gained parallax (task22-crt); absent count
> 23→22 (allowlist-182); focusBlur's live namespace 165→166 (task29);
> Curl's neighbour window `[174:177]`→`[175:178]` and its live namespace
> 175→176 (task31 — two pins, the second only visible after the first was
> fixed). `REMAINING-EFFECTS.md`'s "Current state" was still the 189-row
> census and is refreshed. Three newly-committed absolute `/Users/aayars/…`
> paths in the design docs are now sibling-relative.
>
> ### Gates after the fix and the oracle package
>
> Generator gates 4/4 exit 0 at 190. Native **Debug 271/0, Release 271/0,
> ASan+UBSan 271/0** (ctest 1/1, zero warnings, zero sanitizer diagnostics,
> no LeakSanitizer claim); **x86_64 269/2**, both the documented arch-NaN
> fixtures. Assembly **re-run after the fix**: `typed_80` pixel scope 7
> symbols, 447 instrs ARM64 / 681 x86_64, zero indirect branches, zero jump
> tables, zero fused-FP; TU-wide fused-FP zero on both arches. Oracle
> generator `--check` green; include materializer `--check` and
> `--self-test` green (38/38).
>
> ### Note on how to read `04ea735`'s commit message
>
> Its "1410 tests / 0 failures" and the rest of that block describe the
> **189-row wave-1 state**, not the tree the commit contains. As committed,
> `test_typed_generator` was 265/4.

> ## STATUS 2026-08-19 (session close) — 190 typed rows, **191 of 212
> ported**. Wave 1 (cellRefract 186, kaleido 187, effects 188, wobble 189)
> fully gated: full suite 1410/0 across 28 modules; native Debug/Release/
> ASan each 268/0; x86_64 266/2 (pre-existing arch-NaN); assembly GO 4
> namespaces both arches. **parallax190 landed at focused level** (row at
> index 80, namespace typed_80; gates 4/4 at 190; its tests 11/11 + 69/69;
> Debug native 268/0; 190→189 reconstruction green; structural-only parity
> — oracle package deferred). Sorted 190-key SHA
> `199fbb5eda87c1206ae3793767d746a06c8c5a8d293268c9d6c9489607c09398`;
> artifacts 24,374/`bb8bf931…`, 2,075,210/`28a28b1a…`, 304,207/`b0d2f812…`,
> 17,572/`34bbbe17…`; catalog binds 192; absent 22; genuinely unported 21.
> **Deferred to the wave-2-end matrix (known, bounded):** the milestone
> modules' parallax repairs were applied mechanically (exclusion sets +
> live pins to the measured 190 values) but NOT re-run — verify them first;
> `test_typed_generator` has 4 residual tests from parallax's truncated
> second run (task22-crt, task29, task31, allowlist-182) — diagnose/repair
> per the established classification; parallax's oracle package + the
> wave-2 Release/ASan/x86_64/assembly batch. **Session-close commit made
> with operator authorization.** Wave-2 remaining: lightLeak, mandelbrot,
> synth/noise, newton (+ designed palette pair, grime prepared).

> ## STATUS 2026-08-19 (earlier) — 189 typed rows, wave 1 complete.
> History: cellRefract (186), kaleido (187), effects (188), wobble (189) —
> all landed and accepted (each `*-parity/*-acceptance.md`). **THE TREE IS
> UNCOMMITTED** — the operator authorizes commits per instance only; ask.
> Gates at this stop line: generator gates 4/4 exit 0 at 189; **the
> authoritative full-suite run: 28 modules, 1,410 tests, 0 failures, 0
> errors, 0 skipped** (log: `$RUN_ROOT/verification/full-python-189.log`);
> the 12-module focused battery 643/0 (after wobble's milestone repair
> pass); native
> Debug, Release, and ASan+UBSan each **268/0**, zero sanitizer diagnostics;
> x86_64 266/2 (the two PRE-EXISTING arch-NaN fixtures — the JS authority
> itself is arch-dependent; `x86-64-divergences/`). Sorted 189-key SHA
> `b341c0761af4b038f290961d870a9a5a2df07183c3d948a95b6a9fb1536f55fd`;
> artifacts: typed_slice.json 24,216/`d950efd9…`, typed_slice.cpp
> 2,069,112/`a2da68ff…`, typed_manifest.json 302,565/`12f352d2…`,
> catalog.hpp 17,483/`37ae5bff…`; catalog binds 191; absent 23; genuinely
> unported 22; wobble's insertion index is 155 (grain sits at 53).
> Prepared for wave 2 (frontend records PREPARED, landings enumerated):
> parallax, lightLeak, mandelbrot, synth/noise, newton; grime is prepared
> behind wobble's mechanism; the palette pair is designed
> (struct-parity/struct-design.md — adapters measured portable). GOAL in
> force: all effects ported — every corpus key lands or carries a measured
> upstream blocker (`fractal`: no canonical factory — the sole known
> unportable). See REMAINING-EFFECTS' current header for the live census.
>
> **Known tooling debt — the test suite's runtime is now the bottleneck**
> (operator-flagged 2026-08-19): the full suite is ~36 min and the 12-module
> focused battery ~37 min, dominated by `test_typed_generator`'s milestone
> reconstructions — each rebuilds a historical state by deep-copying the
> LIVE spec, excluding rows, and regenerating ALL ~190 programs in memory,
> and the count of such tests grows with every slice (18 more at wobble).
> The cost is therefore roughly quadratic in landings. Candidate fix for a
> dedicated tooling slice (NOT to be bolted onto a program slice): cache the
> regenerated historical artifacts per milestone (keyed on the exclusion
> set) instead of regenerating per test, or collapse the taskNN family into
> parameterized reconstruction against a shared regenerate-once harness.
> Until then, per-slice verification uses the focused-minimum (gates + the
> slice's own tests + one native build) with the wave-end matrix batching
> the rest — the wave model's intended shape.
>
> **Wave-1 assembly gate: GO, all four namespaces (typed_2, typed_5,
> typed_7, typed_155), both architectures.** Zero indirect branches and zero
> jump tables in every pixel scope; zero fused-FP TU-wide both arches (the
> `-ffp-contract=off` witness); the three array-family Frames remain
> dead-store-eliminated (loadKernels zero callers TU-wide, both arches);
> wobble's varying lowers to bare `context.uv` member loads; binder
> machinery confined to the binders. Claim boundary with teeth:
> **kaleido's `typed_7::value` carries a live indirect branch one
> define-change away from pixel scope** — any alternate-LOOP_OFFSET work
> MUST re-run the assembly gate. The systemic terminate-pad count grew to
> 60/62 TU-wide (the known non-noexcept-Vec condition; one per array-family
> namespace, all in dead `hsv2rgb`; recognized, recorded for the eventual
> cleanup).

> ## STATUS 2026-08-18 (superseded by 2026-08-19 above) — 187 typed rows.
> History: cellRefract (row 186, accepted) and kaleido (row 187, accepted at
> focused level) landed since the 2026-08-16 block.
>
> Sections 1-6 below remain the executed record of Shapes183 (row 183) and
> are history. The 2026-08-16 STATUS block's stop-line tables are superseded
> by this one.
>
> ### Current stop line (kaleido187, quoted from the generated files)
>
> **187 typed rows, 189 catalog binds, 25 corpus keys absent, 24 genuinely
> unported.** Typed-list SHA-256 (sorted keys joined by `\n` WITH trailing
> newline) `587bd0fc54a7aa6a55f65bd8d1a8d36c06f566f369f617c03e90045652747acd`.
>
> | Artifact | Bytes | SHA-256 |
> | --- | ---: | --- |
> | `tools/glslcpp/typed_slice.json` | 23,751 | `460edeccdce784b3d08f160ab32c6de399c07ff22aa99e04314b94435b59ac58` |
> | `src/typed_generated/typed_slice.cpp` | 2,001,343 | `89575abdaef3b2b2db7aeaea1cd06a72540c6bdac696d1b37214e5e8a725343d` |
> | `src/typed_generated/typed_manifest.json` | 299,169 | `158d034396d123f44e62def895c2578f381a015d8b1518f1137334a1b9f32c9b` |
> | `include/noisemaker/generated/catalog.hpp` | 17,301 | `f7ba369927d0bd71f25d80339e650e91cc3722fa61b523a94ebbc9a8cddbb7fc` |
>
> Gates at this stop line: four generator gates exit 0 at 187; focused
> modules green (kaleido integration + profile 160/160; the seven milestone
> modules + semantic green after the controller completed the killed lane's
> repair pass); native Debug 262/0 on the 187-row state. cellRefract186's
> full gate record (Release/ASan 262/0, assembly GO both arches, x86_64
> 260/2 pre-existing with the arch-NaN root cause) is in
> `cellrefract-parity/cellrefract-acceptance.md`. The **wave-end combined
> matrix** (full Python, Release, ASan, x86_64, assembly sweep over
> typed_2+typed_6, kaleido's oracle package) is the outstanding gate batch —
> see "The wave model" below.
>
> ### The wave model (process change, in force)
>
> Authentication stays per-program (own carrier, own RED/GREEN, own
> historical reconstruction at landing); expensive verification is batched
> per wave. Wave 1 = kaleido (landed) → effects (landed, row 188) → wobble
> (landed, row 189 — the wave-1 finale); each acceptance record states its
> focused gates and the wave-end record carries the matrix.
> Known races are paid knowingly: a parallel landing invalidates an
> in-flight full-suite run (discard and re-run at wave end; happened once,
> contained).
>
> ### Prepared inventory (reviewed GO, awaiting integration)
>
> - **wobble — LANDED 2026-08-18 as typed row 189** (`varying-parity/`
>   design + oracle package): the varying-uv carrier's record moved from
>   PREPARED into `KEYS` with the row (insertion index 155 against the live
>   188-row slice; the design's 153 was measured against 186); pure
>   expression lowering (`v_texCoord` → `context.uv`), no ABI change;
>   `factories.size()` 190U→191U; native `typed_wobble189_*` block mirrors
>   the cellrefract pattern with NO crop identity on any arm (the
>   2026-08-18 amendment). Wave-1's last row — the wave-end combined matrix
>   (full Python, Release, ASan, x86_64) is the outstanding gate batch.
> - **effects — LANDED 2026-08-18 as typed row 188** (three-carrier row,
>   ordinal 5; see `EffectsMutableGlobalArrayIntegrationTests`).
> - **parallax** — `counted-for-parity/counted-for-design.md`; TWO rungs
> from CLEAN; its RED test file is PARKED at the run root
> (`workers/parallax-parked-test_texture_lod_admission.py` — restore before
> completing, it breaks any suite run while its module is absent).
> - **newton / struct bucket** — `struct-parity/struct-design.md`; the
> bucket is 3 portable programs (both palette adapters measured
> algorithm-identical, 207,360/207,360 bit-exact — the adapter limbo is
> RESOLVED portable); newton is 8 rungs (struct + out/inout + 4 more);
> julia is a 4th struct family behind counted-for.
> - **counted-for bucket** — parallax (2 rungs) → lightLeak (3) →
>   mandelbrot (4) → synth/noise (4, frame-module key `mutable-global-frame-
>   noise-v1`); classicNoisedeck/noise blocked on typed index; testPattern
>   on int-bitwise; median deep. **dither's upstream defect no longer
>   reproduces** (portable-in-principle, deep); fractal remains
>   no-canonical-factory (its "different algorithm" attribution could NOT be
>   confirmed — see counted-for-design §fractal).
>
> ### Known conditions (measured this session, recorded not fixed)
>
> - **The `.sha256` sidecar convention is not repo-wide integrity** (measured
>   2026-08-19, during the `04ea735` review): of 422 tracked sidecars, **105
>   do not match their adjacent file and 21 name a file that no longer
>   exists**. Spot-checking two — `task-29-oracle-generator.mjs` and
>   `wormhole/wormhole-report.md` — shows both arrived mismatched in the
>   **initial commit**, so this predates every slice and is not slice damage.
>   Sidecars are genuinely load-bearing only where a generator verifies its
>   own (the oracle packages do; those all match). Treat a bare sidecar
>   elsewhere as decoration until this is triaged at the publication gate,
>   and do not cite one as evidence a file is unmodified. Note the two
>   formats in use — bare hash, and `hash␣␣name` with a *repo-relative*
>   name — which defeats a naive `shasum -c` run from the file's own
>   directory and will hand you a false "everything is stale" list.
> - **The handoff's own sidecar went stale in `04ea735`** (the commit edited
>   the document by 184 lines and did not refresh it). Refreshed during the
>   review. If you edit this file, refresh
>   `NEXT_CODING_AGENT_HANDOFF.md.sha256` in the same change.
> - **x86_64 hardware-NaN divergence**: two pre-existing native failures
>   (`0xffc00000` vs `0x7fc00000` from `divsd`/`fdiv`); the JS authority
>   ITSELF produces the same arch-dependent bytes (node x86_64 reproduces
>   the port's values exactly). Classification + recommended per-arch
>   dual-pinning: `x86-64-divergences/x86-64-divergences-report.md`.
> - **The 186-state full-suite figure** carries a runner-harness env caveat
>   (cellrefract-acceptance.md §Gates). The wave-end run is authoritative.
>
> ### Superseded 2026-08-16 stop line (history)
>
> 185 typed rows / 187 catalog / 27 absent / 26 genuine; typed-list SHA
> `75ea3f39…`; artifacts `69deb0c8…` / `e7b52cd1…` / `de223751…` /
> `4c30f680…` (bytes 23,202 / 1,886,817 / 295,588 / 17,099). These remain
> the reconstruction targets for the 186 state.
>
> Gates at the pause, all green and all re-verified by the controller
> independently of the agents that produced them: four generator gates exit 0;
> Python **660 tests / 0 failures** across 19 modules; native Debug, Release and
> ASan+UBSan each **256 PASS / 0 FAIL**, ctest 1/1, zero warnings, zero
> sanitizer diagnostics (**no LeakSanitizer claim** — `detect_leaks=0` on Apple
> means LSan did not run); assembly pixel scope clean on ARM64 and x86_64;
> historical 185 → 184 reconstruction **exact**, 184/184 surviving blocks
> byte-identical.
>
> ### The two slices since Shapes183
>
> | Row | Program | Mechanism | Record |
> | ---: | --- | --- | --- |
> | 184 | `synth/shape:shape` | `mutable-global-frame-shape-v1` + reused `scalar-uint-xor-v1` | `shape-parity/shape-acceptance.md` |
> | 185 | `filter/normalMap:normalMap` | `const-global-nine-table-v1` + a 4th key on `as-u32-round-admission-v1` | `normalmap-parity/normalmap-acceptance.md` |
>
> Both are global-declaration sub-shapes. Read **`normalmap-parity/normalmap-design.md`
> Amendments §§11-16 before trusting anything in §§1-10 of that design** — six
> independent findings, each reproduced by execution, each recording something
> the design asserted that turned out to be false.
>
> ### The next task is not in this document
>
> Go to **`REMAINING-EFFECTS.md`**, re-probed against the live 185-row slice.
> **Re-run its probe before choosing work** — that document was one slice stale
> before this refresh, and three bucket counts changed in the last slice alone.
> Do not carry the census forward by arithmetic.
>
> Its recommendation is the **mutable-uninitialized-global array** shape:
> `cellRefract`, `kaleido`, `effects` (`float emboss[9];`, byte-identical in the
> first three) and `synth/noise`. `const-global-nine-table-v1` is the
> precondition it was built to provide, but **it is not a carrier you can add a
> key to** — those tables are mutable, written by a non-`main` writer, and passed
> as `float[9]` call arguments. Plan `effects` separately; it additionally needs
> `mat4`.
>
> ### Four things left open, none blocking
>
> 1. **`DEFECTS-FOUND.md` item 5** — five shipped programs (`crt`, `degauss`,
>    `fxaa`, `grain`, `normalMap`) write **black** on an early `return;` where
>    JavaScript writes the *previous pixel's colour*, because the port does not
>    model the persistent factory-scope `fragColor`. Recorded, not fixed; the fix
>    is a runtime change to the output-persistence model. **No sanitizer can find
>    it** — it is a value divergence, not a memory-safety bug. Read the
>    correction note in that item before re-investigating.
> 2. **Publication hygiene.** `docs/port-engineering/` holds **1,891 tracked
>    files, 38 MB of a 70 MB repo**, including **117 tracked `.log`/`.err`/`.orig`
>    build transcripts**, plus `CMakeLists.txt.orig`, `screen.err` and
>    `screen_out.json` at the repo root. Per-task scratch that was committed.
>    Belongs to the publication gate (§8).
> 3. **`tests/test_generated_kernels.cpp:18345`** holds a hand-maintained second
>    copy of `kOracleSha256`. Same transcription pattern that produced three
>    stale figures in the last slice. Worth deriving.
> 4. **`unittest discover -s tests -t .` has never worked** — `tests/` has no
>    `__init__.py`, so it refuses with `ImportError: Start directory is not
>    importable`. Every prior acceptance record citing a "full discover" figure
>    measured it some other way. The 660-test figure above comes from a scratch
>    runner that loads each `tests/test_*.py` under its real `tests.<name>` path
>    and **asserts the module count** (19, not 20 — the assertion caught that).
>
> ### Method corrections earned in the last slice — carry these forward
>
> These cost real time to discover and each one invalidated a result that looked
> green:
>
> - **Delete-the-check has a granularity.** A whole-predicate sweep can be
>   honest and complete and still miss that a predicate's *sub-clauses* are
>   mutually redundant. In the last slice, 72 frozen fields were proved by
>   nothing while every whole-predicate deletion went red. Sweep sub-clauses,
>   and when two delete green individually, test them **together**.
> - **Neutralize behavior, never delete text.** Textually removing a clause also
>   strips its string literals, which trips any test that greps the module
>   source — making the clause look guarded twice when it is guarded once. Use
>   `... or True`.
> - **Guard-coverage auditing needs an AST, and the AST must render
>   interpolations.** Source-text search fails in *both* directions: it
>   over-reports by matching docstrings and under-reports by missing implicit
>   concatenation. An AST walk that *drops* `FormattedValue` instead of rendering
>   it as `{}` fabricates guards that do not exist — that produced a false "two
>   malformed messages" finding. Measure coverage against test literals that are
>   **arguments to a call**.
> - **A row-adding slice must budget for the native catalog census**, not only
>   the Python ones. The last slice left `factories.size() == 186U` against a
>   187-entry catalog, and a review that recomputed every Python census did not
>   look at it.
> - **Sanity-check a reconstruction block splitter on an unchanged pair first.**
>   Two reviewers in two slices produced a false mismatch by gluing the trailing
>   catalog block onto the last program.
> - **Do not hand-transcribe measured figures into prose.** Three stale numbers
>   in one slice. Quote them from the artifact.
> - **A slice is not done until every dispatched review has reported — and the
>   controller must not claim a review happened when it did not.** Both failure
>   modes occurred; the second was caught only because an implementer checked a
>   convenient claim against the ledger instead of accepting it.
>
> ### Where the process record lives
>
> `.superpowers/sdd/normalmap-slice185/progress.md` carries every ruling, every
> review verdict, what each reviewer reproduced rather than read, and every
> controller error with its correction. Task briefs and reports sit beside it.
>
> **It is git-ignored and therefore machine-local** — a fresh clone will not have
> it. That is deliberate: it is process scratch, not product. Everything durable
> in it is already distilled into committed files — the review verdicts and what
> each reviewer reproduced into `normalmap-parity/normalmap-acceptance.md`, the
> design corrections into that design's Amendments §§11-16, and the process
> lessons into "Method corrections" above. If you are resuming on a different
> machine and want the blow-by-blow, it is gone; the conclusions are not.

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` or
> `superpowers:executing-plans` to execute this handoff. Use
> `superpowers:test-driven-development` for implementation,
> `superpowers:systematic-debugging` for any unexpected result, and
> `superpowers:verification-before-completion` before accepting a slice.

**Goal:** Finish the C++20 CPU port of `noisemaker-for-cpu` with exact
JavaScript pixel parity, starting from the accepted 182-row typed state and the
approved `classicNoisedeck/shapes:shapes` design.

**Architecture:** Keep the existing authenticated typed-GLSL pipeline:
pinned corpus -> independent validator -> independent C++ emitter -> checked-in
generated kernels -> structural/mutation tests -> native parity against the
canonical JavaScript public runtime. Add one narrowly authenticated program at
a time; do not replace or broadly generalize this architecture.

**Tech stack:** C++20, CMake, Python 3.12+, Node.js, canonical
`noisemaker-for-cpu`, exact float32/RGBA8 fixtures, ASan/UBSan, ARM64 and x86_64
assembly inspection.

## Global constraints

- Repository: `/Users/aayars/platform/noisemaker-for-cpp`.
- Behavioral reference: `/Users/aayars/platform/noisemaker-for-cpu`.
- The checkout currently has no `.git` metadata. Do not initialize or use Git
  during implementation. No worktrees, feature branches, or pull requests.
- Work autonomously and fan out independent mechanical work, with disjoint
  file ownership and one integration owner.
- TDD is mandatory. Every widening needs a named accepted witness and a new
  rejection at the widened boundary.
- The validator and emitter are independent authorities. A change in one is
  not proof for the other.
- Never weaken frozen hashes, historical reconstruction, exact mutation
  barriers, or oracle independence to make a test pass.
- Pixel parity means exact float32 words, including signed zero and NaN
  payloads, plus exact RGBA8 bytes. Do not introduce tolerance.
- Match the shipped JavaScript materialization and its float32 staging, not
  assumed GLSL semantics.
- Do not run builds, caches, bytecode, logs, snapshots, or scratch probes in
  the repository. Use exactly one task-owned external root as described below.
- Do not delete or modify pre-existing repository artifacts or unrelated
  `/private/tmp` content. Delete only the exact task-owned run root after its
  evidence has been summarized.
- Do not invoke the final `superpowers:requesting-code-review` or publish until
  every eligible effect, full parity, and the complete verification matrix are
  done. The user has authorized creation and ordinary push of the final new
  public MIT repository after review feedback is addressed; that authorization
  does not waive any earlier gate.

---

## 1. Exact stop line — SUPERSEDED, see STATUS above

*Historical: this was the state before Shapes183. Retained so the executed plan
reads coherently. The current stop line is in the STATUS block at the top.*

| Metric | Current value |
| --- | ---: |
| Canonical corpus programs | 212 |
| Typed programs | **182** |
| Generated catalog rows | **184** |
| Corpus keys absent from typed slice | **30** |
| Already public outside typed slice | **1** — `filter/wormhole:deposit` |
| Distinct ported/public corpus keys | **183** |
| Genuinely unported | **29** |
| Rows with non-empty `defines` | **25** |
| Scalar-XOR carriers | **2** |
| Linear-sRGB lane-index carriers | **3** |

Current sorted typed-key SHA-256:

```text
33cc895dbee2e0b0451081f5e940d3ee101442a5e3ae90b49dec34d84f5b124b
```

Current generated/input locks:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `tools/glslcpp/typed_slice.json` | 22,305 | `8d58736afa431f2d2c3fa992c22301d9775e4bed7d122d43c85218ccfada315c` |
| `src/typed_generated/typed_slice.cpp` | 1,757,260 | `7e3b659ff007b08acda39d8f67f931e61742befe8959c4fa212ffa8f051fc6c7` |
| `src/typed_generated/typed_manifest.json` | 290,280 | `242c49a756b541a6fbbf94a984039a6ab4db41437d21770e43c302692f57e50d` |
| `include/noisemaker/generated/catalog.hpp` | 16,831 | `6f89a6b51bf8b6eba2c4c1f16a1852cce3e293d514be8d57efaaca96827b77c4` |

The first typed keys are currently Shape Mixer at ordinal 7 and Splat at 8.
Shapes must be inserted at ordinal 8, moving Splat to 9.

`docs/port-engineering/IN-PROGRESS-HANDOFF.md` and
`docs/port-engineering/FRONTIER-2026-08-13.md` are historical and stale. The
current frontier is `docs/port-engineering/REMAINING-EFFECTS.md`, refreshed
with this handoff.

## 2. Shape Mixer182 acceptance evidence

Do not redo or reopen Shape Mixer unless a later full-suite failure produces
new evidence.

- Full Python discovery: **352/352 passed**, zero failures/errors/skips.
  Report:
  `/private/tmp/noisemaker-for-cpp-shapemixer182-full-python-rerun-report.md`,
  SHA-256
  `c4f129c517266934c5641039f27342d9f7b881c683074f5621a635cdf5c2ef89`.
- Compact full log:
  `/private/tmp/noisemaker-for-cpp-shapemixer182-full-python-rerun.log`,
  SHA-256
  `e4b6c16cf5a4faeea0610806ea60a99693f48974a43c90f824d2b9e41e2e29e0`.
- Debug, Release, and ASan+UBSan: **236/236 direct** and **CTest 1/1** in
  every configuration. ARM64 and x86_64 pixel paths have no indirect dispatch
  or fused FP. Report:
  `/private/tmp/noisemaker-shapemixer182-final-native-asm2.gKhyKG/FINAL-GO-REPORT.md`,
  SHA-256
  `62035591841692fb208b63a6130a9d1830bd8fb53b6f606d693acf45be611494`.
- Toolchain/no-write lane: corpus, semantics, fixed kernels, typed slice,
  Shape oracle/include checks, focused 14/14, historical reconstruction 1/1,
  and a 2,132-file custom comparison all passed. Report:
  `/private/tmp/noisemaker-shapemixer182-toolchain.37wYAE/FINAL-REPORT.md`,
  SHA-256
  `d315e5ae02d3a5f384f0d8d803602e185f179d9d38f129946965901b33a800ee`.
- Full Python before/after repository manifest: 2,878 records,
  byte-identical, SHA-256
  `43a48a9e5f45337a522250424eb2d5ed00d4ad2dbfdfed8f7aee9f2a5abeb386`.
- Repository transient inventory: 113 preserved historical documentation
  logs before/after, byte-identical, SHA-256
  `6479e28309c14ceaf04aec583e2e5a979f396999cc178b3e118b66fbcb74c586`.

The final full-Python rerun initially exposed two stale test-only `_Emitter`
objects in `tests/test_typed_generator.py`. Production stayed fail-closed. Both
manual render-body bypasses now initialize all seven Shape Mixer fields, and an
AST test locks that list:

```python
authorized_shape_mixer_proof = None
candidate_shape_mixer_guards = ()
candidate_shape_mixer_ladders = ()
emitted_shape_mixer_guards = []
emitted_shape_mixer_roots = []
emitted_shape_mixer_bodies = []
emitted_shape_mixer_exceptional = []
```

Do not add a production `getattr` fallback; the explicit test construction is
the correct repair pattern if this class of test harness failure recurs.

## 3. Storage state and non-accumulation rule

Live read-only audit at this handoff:

- Repository size: approximately **47 MiB** (`48,024 KiB` at the accepted
  full-suite audit).
- No repository build, CMakeFiles, cache, Python bytecode, object, or temporary
  directories were found.
- The old immutable Shape Mixer snapshot beneath
  `/private/tmp/noisemaker-shapemixer182-final2.CQRWet` has already been
  deleted; only a roughly 312 KiB evidence manifest remains.
- Compact accepted evidence roots are roughly 172 KiB (native/assembly) and
  48 KiB (toolchain).
- Top-level `CMakeLists.txt.orig`, `screen.err`, and `screen_out.json`, plus the
  historical documentation logs, predate this handoff. Do not infer authority
  to remove them.
- A repository-wide audit found pre-existing `.sha256` sidecar debt: 397
  sidecars, 184 valid, 192 mismatched, and 21 missing sibling targets in the
  accepted live tree. Do not bulk-repair that historical set. Enforce only the
  current task's exact new sidecars and record the old debt separately.

Earlier work accumulated many build trees and then over-corrected by deleting
ignored repository build/cache directories. Those products were rebuildable,
but the deletion was outside the preservation gate. Do not repeat either
failure. There may also be unrelated historical temporary roots outside this
task; do not scan or bulk-delete them.

For Shapes allocate exactly one owned root:

```bash
CPP_ROOT=/Users/aayars/platform/noisemaker-for-cpp
RUN_ROOT="$(mktemp -d /private/tmp/noisemaker-shapes183.XXXXXX)"
test -d "$RUN_ROOT"
case "$(cd "$RUN_ROOT" && pwd -P)" in
  /private/tmp/noisemaker-shapes183.*) ;;
  *) exit 1 ;;
esac
mkdir -p "$RUN_ROOT"/{profiles,integration,native,verification,Debug,Release,sanitizer,reconstruction,assembly,oracle/tmp,oracle/xdg-cache,oracle/pycache}
export TMPDIR="$RUN_ROOT/oracle/tmp"
export TMP="$RUN_ROOT/oracle/tmp"
export TEMP="$RUN_ROOT/oracle/tmp"
export XDG_CACHE_HOME="$RUN_ROOT/oracle/xdg-cache"
export PYTHONPYCACHEPREFIX="$RUN_ROOT/oracle/pycache"
export PYTHONDONTWRITEBYTECODE=1
```

Every Python invocation must be `python3 -B`. All workers share this root and
receive a unique subdirectory; no worker creates another scratch root. Before
edits, record deterministic full and transient repository manifests outside an
explicit retained-product allowlist. After all lanes, require unchanged bytes
outside that allowlist and zero new transient paths. Summarize evidence, check
the exact prefix again, then delete only `"$RUN_ROOT"` and prove it no longer
exists.

## 4. Shapes183 — COMPLETE (executed record)

Port exactly `classicNoisedeck/shapes:shapes`. **DONE 2026-08-16.** The plan
below was executed; where reality diverged from it, design amendments §§11-13
are authoritative over this section.

### Frozen authority

- Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`.
- Corpus ordinal: 16, between Shape Mixer 15 and Splat 17.
- Source:
  `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/classicNoisedeck/shapes/shapes.glsl`.
- Raw: 21,289 bytes, SHA-256
  `60bc6e76ac9d9f5bc83638fa934b279499559f7733806e462cea16a4cbe85eb0`.
- Normalized: 18,713 bytes, SHA-256
  `347d19f46adb59129ec2f5eb58910b1ea981be9ec03788a068ff6e884bb848e6`.
- Typed functions SHA-256:
  `dfd7220ab36ed03702afbc5e69e7e3a7346c60d488d9b3a2087d31214219943a`.
- Whole-program SHA-256:
  `e072ec89fef6122ed3d581ea5efb6cec953d9b7492294ca9d8b0f011af5411f0`.
- Interface SHA-256:
  `e27ca4581c14991de7a17e296353b1993e8f9c6e5a4ec48b170dde8f8d1b1b6c`.
- Default defines only: `LOOP_A_OFFSET=40`, `LOOP_B_OFFSET=30`.
- Canonical JS factory: `canonicalFactory16`; function-text SHA-256
  `a4e1aeaf8cbc3d748517369e054b7ec4a2fd5f70962cbafef61d5e473527c2c3`.
- No samplers, texture reads, or derivatives.
- Exactly 18 runtime bindings:
  `time`, `seed`, `wrap`, `resolution`, `tileOffset`, `fullResolution`,
  `loopAScale`, `loopBScale`, `speedA`, `speedB`, `paletteMode`,
  `paletteOffset`, `paletteAmp`, `paletteFreq`, `palettePhase`,
  `cyclePalette`, `rotatePalette`, `repeatPalette`.
- The two defines are compile-time values, not runtime bindings.

The independently approved design and its GO review have been **moved into the
repository** — they previously existed only under `/private/tmp`, where they
were one cleanup away from being lost:

| File | Bytes | SHA-256 | Frozen? |
| --- | ---: | --- | --- |
| `docs/port-engineering/shapes-parity/shapes183-design-review.md` | 3,173 | `44b749c29a59ed371418be764dba7f12497b8f5d9749f129a1ad6802fd6354cf` | **yes** — the GO review, never edit it |
| `docs/port-engineering/shapes-parity/shapes183-design.md` | 34,723 | `478e510354a6d3929da013a1a4a8f17b8201558187d1b33637ea52b5d8eeacb1` | **no** — living; see below |

Both were byte-verified against the original temp copies before being moved
(design `e40ad1c0bb62c6797a270060498765823f072284b1b0a505f59644fe7bd4425f`,
review `44b749c2…`).

**Do not treat the design's hash as an authority gate.** It is a living document
that accumulates numbered amendments as implementation disproves parts of it —
§11 is the first — so its hash changes and the value above is a point-in-time
record, not a lock. Sections 1-10 are the originally reviewed text and stay
unedited apart from forward pointers, so the frozen GO review remains auditable
against them. If the hash does not match, read the amendment list before
concluding anything drifted. The implementation contract is also reproduced
below.

### Exact slice row

Insert this row in sorted position and no other row:

```json
{
  "defines": {"LOOP_A_OFFSET": 40, "LOOP_B_OFFSET": 30},
  "linear_srgb_lane_index_profile": "linear-srgb-shapes-lane-index-v1",
  "program_key": "classicNoisedeck/shapes:shapes",
  "scalar_uint_xor_profile": "scalar-uint-xor-v1",
  "shapes_float_bits_ingress_profile": "shapes-float-bits-ingress-v1"
}
```

Projected generated/test metrics:

- 183 typed rows and 185 catalog rows;
- 29 corpus keys outside the typed slice, of which wormhole remains already
  public, so 28 are genuinely unported after Shapes;
- 26 rows with non-empty `defines` maps;
- scalar-XOR / linear-sRGB / Shapes-ingress carrier counts 3 / 4 / 1;
- sorted typed-list SHA-256
  `b10e0d7eb918c60dae3fa24d0a09b1a9578a334c39ab5a9561db54176eca539b`;
- exact neighborhood Shape Mixer / Shapes / Splat / Adjust at ordinals 7-10.

### Required proof composition

1. Reuse the existing `scalar-uint-xor-v1` Shapes lock in
   `tools/glslcpp/frontend/scalar_uint_xor_profile.py`. It already authenticates
   the three scalar XOR sites at normalized lines 122-124 and their call graph.
   Do not add a new XOR implementation or duplicate this proof.
2. Extend `tools/glslcpp/frontend/linear_srgb_lane_index_profile.py` with
   `linear-srgb-shapes-lane-index-v1`. Authenticate exactly five `vec3[i]`
   sites in `linearToSrgb` at `576:13-576:22`, `577:13-577:20`,
   `577:23-577:32`, `579:13-579:20`, and `579:35-579:44`. Lock the owner,
   parents, one `for (int i=0; i<3; ++i)` loop, resources, exact defines, base
   and induction identities, read/write roles, and branch-complete `srgb`
   initialization. Do not admit generic vector indexing.
3. Create `tools/glslcpp/frontend/shapes_float_bits_ingress_profile.py` for
   the one `floatBitsToUint(seedFrac)` at `119:21-119:46`. Lock the exact
   `randomFromLatticeWithOffset` owner, declaration parent, scalar
   `float -> uint` signature, `seedFrac` initialized to positive `+0.0`,
   complete one-node census, reachability, and ancestry into the three
   authenticated XOR nodes. Reuse the scalar-XOR authenticator's returned
   candidate objects when binding that ancestry.
4. Both validator and emitter must require all three carriers together,
   re-authenticate independently, and consume all six new profile nodes exactly
   once. Admission is by object identity and skips `used.add(...)`; the frozen
   44-entry capability vocabulary and approved type tuple must not change.

The hash branch containing the float-bit ingress and XOR sites is conservative
call-graph reachable but dynamically dead in default `40/30` full renders.
Full-surface parity must not be cited as proof that branch executed. Structural
mutations and direct numeric bit-pattern tests carry that proof.

## 5. Parallel implementation ownership (as executed)

The user explicitly asked for fan-out. Use the root agent as integration owner
and three bounded workers, with no concurrent edits to the same file.

### Worker A: profile RED/GREEN

**Owns:**

- Create `tests/test_linear_srgb_lane_index_profile.py`.
- Create `tests/test_shapes_float_bits_ingress.py`.
- Modify `tools/glslcpp/frontend/linear_srgb_lane_index_profile.py`.
- Create `tools/glslcpp/frontend/shapes_float_bits_ingress_profile.py`.

**Contract:** Write exact failing profile tests first. Include missing/wrong/
foreign carrier cases; every node/span/parent/role mutation; extra/missing node
censuses; `+0.0 -> -0.0`; call-graph/ancestry drift; and unrelated proof
carriers. For local mutations, refreeze coarse hashes to the mutant, prove the
coarse failure did not fire, and assert the intended node-level message. Add a
sabotage test for each visitation ledger.

**Focused cycle:**

```bash
cd "$CPP_ROOT"
python3 -B -m unittest \
  tests.test_linear_srgb_lane_index_profile \
  tests.test_shapes_float_bits_ingress -v
```

### Worker B: integration/schema

**Owns:**

- Modify `tests/test_typed_generator.py`.
- Modify focused live census/reconstruction assertions where semantically
  required in `tests/test_scalar_uint_xor.py`,
  `tests/test_runtime_loop_bound.py`, `tests/test_glitch_mat4_chain.py`,
  `tests/test_shape_mixer_builtin_closure.py`, and
  `tests/test_emboss_color_style.py`.
- Modify `tools/glslcpp/generate_typed_slice.py`.
- Modify `tools/glslcpp/emit_typed_cpp.py`.
- Modify `tools/glslcpp/typed_slice.json`.
- Generate, never hand-edit,
  `src/typed_generated/typed_slice.cpp`,
  `src/typed_generated/typed_manifest.json`, and
  `include/noisemaker/generated/catalog.hpp`.

**Contract:** First lock the current RED boundary: Shapes absent, corpus ordinal
16, exact source/defines/resources, and first rejection at normalized
`576:13` with `unsupported typed expression index`. Then add the proposed row
and prove it still rejects before profile wiring. Require all three carriers at
both authorities. Insert in sorted position. Historical reconstruction must
deep-copy the live 183-row spec, remove only Shapes, regenerate in memory, and
recover the three pre-Shape generated hashes above. Normalize only `typed_N`
ordinals when comparing surviving blocks; the set difference is exactly
Shapes. Hand-classify historical assertions—never bulk-rewrite milestone data.

Generate only with:

```bash
cd "$CPP_ROOT"
python3 -B tools/glslcpp/generate_typed_slice.py --write
python3 -B tools/glslcpp/generate_typed_slice.py --check
```

Serialize the shared integration only after Worker A's profile interfaces and
tests are stable.

### Worker C: canonical oracle/native parity

**Owns:**

- Create `docs/port-engineering/shapes-parity/shapes183_oracle_generator.mjs`.
- Create `docs/port-engineering/shapes-parity/shapes183-oracles.json`.
- Create `docs/port-engineering/shapes-parity/shapes183-oracle-report.md`.
- Create `tools/glslcpp/generate_shapes_native_oracle_include.py`.
- Create `tests/oracles/shapes183_expected.inc`.
- Create and validate a sibling `.sha256` for each of those five files.
- Modify `tests/test_generated_kernels.cpp`.
- Modify `tests/test_numeric.cpp` only for the controlled bit-pattern case.

**Contract:** Snapshot the CPU reference once at
`$RUN_ROOT/oracle/noisemaker-for-cpu`. The oracle must run the unmodified public
`canonicalFactory16` path from that snapshot, reject live/foreign imports and
adapter substitution, and pin the source/runtime hashes from the approved
design:

| CPU-relative file | SHA-256 |
| --- | --- |
| `src/effects/generated/canonical-kernels.js` | `66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe` |
| `src/effects/catalog.js` | `d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4` |
| `src/csl/glsl-kernel.js` | `a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa` |
| `src/csl/glsl-runtime.js` | `a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072` |
| `src/runtime/pass-runner.js` | `fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa` |
| `src/runtime/surface.js` | `0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59` |

Require `kernelFactories.get(key) === canonicalKernelFactories[key]`, require
the factory name/text hash above, and require the adapter table not to own the
key. Resolve every imported real path beneath the frozen CPU root.

Use exactly six top-level cases:

```text
oklab-palette-a
oklab-palette-tiled
oklab-palette-extreme
oklab-palette-negative-speed
diagnostic-palette-hsv
diagnostic-palette-rgb
```

Store each full float32-word array and RGBA8 array once in the JSON and
materialize the single C++ include from it. Prove public/direct/repeat routes,
independent output storage, all 18 binding types and missing/wrong variants,
caller vector/binding immutability, exact alpha `0x3f800000`/255, top-down crop
translation, and deterministic repeatability.

For a top-down crop `(crop_x,crop_y,tile_width,tile_height)` from
`(full_width,full_height)`, the full route binds full-sized
`resolution/fullResolution` with `tileOffset=(0,0)`. The tile route binds
tile-sized `resolution`, the same full size, and
`tileOffset=(crop_x, full_height-crop_y-tile_height)`. Compare the full tile to
the corresponding top-down crop exactly.

Attach one-axis controls to `oklab-palette-a`: changing only external
`runPass` time/seed from words `(0x00000000,0x3f800000)` to
`(0x4f000000,0xcf000000)` must not change output; changing only bound `time`
from `0x3f000000` to `0x41200000` must change it. Store the controlled full
arrays and ledger.

**Amended 2026-08-15 — the bound-`seed` axis does NOT change the output and must
not be required to.** At the default defines `40/30`, `seed` is not consumed on
any live path: `offset()` reads its `seed` parameter only in the
`loopOffset >= 300 && loopOffset <= 380` arm (`shapes.glsl:519`), which neither
`40` nor `30` selects, and `value()` — holding the other two `float(seed)` uses
— has that dead line as its only caller. `shapes.glsl:12-19` documents this in
the source. Record the axis as measured, with a `seed_liveness_census`, rather
than requiring a difference. `seed` remains a required int32 ABI binding and
must still be ABI-tested. Full reasoning: `shapes-parity/shapes183-design.md`
§11.

Write the requested custom comparer in `tests/test_generated_kernels.cpp`. It
must check width and height before lane count, require exactly
`width*height*4` float words and bytes, compare every float by raw 32-bit word
including signed zero and NaN payload, compare every RGBA8 byte, and report the
first mismatch with top-down x/y, channel, expected/actual words, and bytes.
Self-test dimension mismatch with equal lane counts, `+0/-0`, differing NaN
payloads, word-only and byte-only mismatches, and short/long arrays.

ABI types are exact: `seed`, `paletteMode`, and `cyclePalette` are `int32`;
`wrap` is bool; `paletteOffset`, `paletteAmp`, `paletteFreq`, and
`palettePhase` are `Vec3`; `resolution`, `tileOffset`, and `fullResolution` are
`Vec2`; every remaining scalar uses `get_number`. Omit each binding once and
supply its wrong variant once, requiring `KernelBindingError` to name it.
Unrelated extra uniform/texture entries are ignored and behavior-neutral.

The JSON-to-C++ materializer must reject missing/extra fields, duplicate case
names, malformed dimensions/counts/words/bytes, incorrect sidecars/hashes, and
truncated or extra arrays.

Add this exact direct numeric proof:

```cpp
REQUIRE(float_bits_to_uint(uint_bits_to_float(0x7fc12345U)) == 0x7fc12345U);
```

The oracle also independently computes `shapes-fwdB-column-swap` and
`shapes-cube-unnarrowed`. All four OKLab cases must discriminate both mutants;
HSV/RGB are non-reaching controls.

### Integration order

1. RED test contracts.
2. Profile implementations.
3. Validator/emitter composition.
4. Sorted slice row and generated outputs.
5. Oracle/include and native integration.
6. Historical 183 -> 182 reconstruction.
7. Full verification and assembly.
8. Independent slice review.

If two owners need one file, serialize that file under the integration owner.
Do not reconcile concurrent edits by wholesale replacement.

## 6. Shapes verification gates (all passed; reusable for the next program)

Run all commands from `CPP_ROOT` with the external environment above.

```bash
python3 -B tools/glslcpp/check_corpus.py --check
python3 -B tools/glslcpp/check_semantics.py --check
python3 -B tools/glslcpp/generate_kernels.py --check
python3 -B tools/glslcpp/generate_typed_slice.py --check
node "$CPP_ROOT/docs/port-engineering/shapes-parity/shapes183_oracle_generator.mjs" \
  --check --cpu-root "$RUN_ROOT/oracle/noisemaker-for-cpu"
python3 -B "$CPP_ROOT/tools/glslcpp/generate_shapes_native_oracle_include.py" --check
python3 -B -m unittest discover -s tests -p 'test_*.py' -q
```

The full Python run is slow by design; the accepted 352-test run took about 67
minutes wall time. Do not interrupt it because output is quiet.

Fresh native lanes:

```bash
cmake -S "$CPP_ROOT" -B "$RUN_ROOT/Debug" -DCMAKE_BUILD_TYPE=Debug
cmake --build "$RUN_ROOT/Debug" --target noisemaker-cpu-tests -j
"$RUN_ROOT/Debug/noisemaker-cpu-tests"
ctest --test-dir "$RUN_ROOT/Debug" --output-on-failure

cmake -S "$CPP_ROOT" -B "$RUN_ROOT/Release" -DCMAKE_BUILD_TYPE=Release
cmake --build "$RUN_ROOT/Release" --target noisemaker-cpu-tests -j
"$RUN_ROOT/Release/noisemaker-cpu-tests"
ctest --test-dir "$RUN_ROOT/Release" --output-on-failure

cmake -S "$CPP_ROOT" -B "$RUN_ROOT/sanitizer" \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer" \
  -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=address,undefined"
cmake --build "$RUN_ROOT/sanitizer" --target noisemaker-cpu-tests -j
ASAN_OPTIONS=detect_leaks=0:halt_on_error=1 \
UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 \
  "$RUN_ROOT/sanitizer/noisemaker-cpu-tests"
ASAN_OPTIONS=detect_leaks=0:halt_on_error=1 \
UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 \
  ctest --test-dir "$RUN_ROOT/sanitizer" --output-on-failure
```

On Apple, `detect_leaks=0` means no LeakSanitizer claim. Require zero ASan and
UBSan diagnostics and confirm `-Wall -Wextra -Wpedantic -Werror` plus
`-ffp-contract=off` in all three builds.

Audit final exact ARM64 and x86_64 assembly for `typed_8::pixel`,
`linearToSrgb`, `linear_srgb_from_oklab`, `oklab_from_linear_srgb`,
`randomFromLatticeWithOffset`, and the binder. Pixel/helper scope must have no
indirect branch, fused FP, allocation, exception/unwind path, virtual/callback
dispatch, container/string work, or dynamic stack allocation. Direct helper
calls are allowed. Binder-only `shared_ptr` construction/cleanup must stay
outside the pixel path. Record instruction counts, frame sizes, and callees.

Stop and redesign instead of widening if source locks drift, another capability
is needed, oracle provenance cannot be authenticated, a tolerance is proposed,
a local mutation is caught only by a coarse hash, historical reconstruction
changes a surviving block, or sanitizer/assembly finds UB or dynamic pixel-path
behavior.

## 7. After Shapes — HISTORICAL, its number is two slices stale

*The "29-program genuine frontier" below was true at 183 rows. It is **26** at
185. The standing instruction is still exactly right and is why this section is
retained: re-run the probe, never subtract.*

Do not continue by subtracting one from this handoff's frontier. Re-run the
read-only validator probe and refresh `REMAINING-EFFECTS.md`. The current live
29-program genuine frontier is grouped there by first blocker. First blockers
are not complete closures.

The known special cases remain:

- `classicNoisedeck/fractal:fractal` is adapter-only and has no canonical
  factory for its corpus GLSL; its adapter implements a different algorithm.
- `filter/dither:dither` has no working JavaScript error-diffusion behavior to
  match until the upstream defect is fixed.
- `filter/wormhole:deposit` is already public via the scatter pass and must not
  be counted as genuinely unported merely because it is absent from the typed
  slice.

Continue with the same one-program authenticated cycle. Every accepted slice
gets exact source/profile locks, RED/GREEN mutation coverage past coarse hashes,
canonical public-path JS oracles, exact native parity, historical
reconstruction, the full Python/native/sanitizer matrix, assembly inspection,
and the storage manifest/cleanup gate.

## 8. Whole-port completion, review, and publication

Shapes acceptance is not whole-port completion. When every eligible public
program is implemented and pixel-level parity is proven:

1. Run a fresh complete corpus/semantics/generator/Python/Debug/Release/
   sanitizer/assembly/storage matrix from one owned external root.
2. Invoke the user-named
   `superpowers:requesting-code-review` skill for an independent review of the
   entire port, not merely the final slice.
3. Use `superpowers:receiving-code-review` to evaluate and address every
   Critical and Important finding. Re-run affected focused tests and the full
   final matrix.
4. Perform the final secrets, license, README, CI, example, package, and clean
   clone/publication audit.
   **Known item, scanned 2026-08-16 at `git init`, partially resolved:** no
   secrets, no key material, no `.env` files. Absolute `/Users/aayars` paths
   were present in **11 files**; **8 remain**.

   The three that were hardest are now **fixed at the root cause**, not
   scrubbed. Both oracle packages recorded their run-root snapshot path as
   provenance, and `--check` byte-compares the regenerated JSON — so those
   permanently-checked-in gates could only pass from the exact machine-specific
   temp directory that produced them. Verified broken, then fixed: the path is
   replaced by a stable placeholder, the live-checkout location is derived from
   `NOISEMAKER_FOR_CPU` or `$HOME`, and both materializers now reject any
   absolute-looking string anywhere in the document. **Both `--check` gates now
   pass from an arbitrary fresh snapshot path and still refuse the live
   checkout** — confirmed independently.

   The remaining 8 are prose in engineering docs, where a path is usually
   recording where something ran. Scrub or parameterise them before any push;
   none is load-bearing. Current list: `git grep -Il /Users/aayars`.
   Factor OSS presentation.
5. Only then initialize the repository, create a new public GitHub repository,
   commit the exact reviewed tree on the default branch, and perform the one
   authorized ordinary push. Do not create a feature branch, worktree, PR, or
   rewrite history.
6. Verify the public repository, clean clone, CI, buildable example, generator
   determinism, and release/package metadata from the published state.

The next coding action is Task 1 above: create the single owned Shapes run root,
record the pre-edit manifests, then fan out the three disjoint RED-test lanes.
