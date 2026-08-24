"""Assembles singleton-triage.json from the probe outputs already checkpointed
in this directory (probe_results.json, scan_out_texturelod_results.json,
out_texturelod_summary.json), plus hand-verified findings recorded inline
below (each traceable to a specific probe run documented in
singleton-triage.md). Read-only w.r.t. the real repo; writes only under
docs/port-engineering/singletons/. Never runs git.
"""
from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
probe = json.loads((HERE / "probe_results.json").read_text())
scan = json.loads((HERE / "scan_out_texturelod_results.json").read_text())
summary = json.loads((HERE / "out_texturelod_summary.json").read_text())

CORPUS_REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"

report = {
    "schema": "noisemaker-for-cpp.singleton-triage.v1",
    "corpus_revision": CORPUS_REVISION,
    "generated_against": "live tools/glslcpp tree (2026-08-13), typed_slice.json count 154",
    "method": (
        "Real parse_program/analyze_program/validate_capabilities/render_typed_cpp, "
        "run in-process against a byte-identical `cp -R` copy of tools/glslcpp "
        "(verified via `diff -rq`, see probe_tree/). Downstream chains traced by "
        "re-running validate_capabilities against copies of generate_typed_slice.py "
        "with a targeted, single-purpose provisional admission applied at the exact "
        "raise site of one already-known blocker (see build_relaxed_all.py, "
        "build_relaxed_variants.py, build_extra_hop_variants.py for every patch, "
        "each asserted to match exactly one occurrence in the unmodified source), "
        "never at the real tools/glslcpp/generate_typed_slice.py."
    ),
    "primary_targets": {},
    "other_singletons_found": {},
    "multi_program_adjacent_blockers": {
        "out_or_inout_parameter_direction": {
            "gates_programs": summary["out_or_inout_gated_programs"],
            "count": len(summary["out_or_inout_gated_programs"]),
            "method": (
                "Corpus-wide scan of all 58 currently-unported programs "
                "(scan_out_texturelod.py), isolating parameter-direction from "
                "every other relaxation (generate_typed_slice_relaxed_no_paramdir.py, "
                "12/13 patches, param_direction withheld) so 'unsupported parameter "
                "direction' can only surface if it is genuinely the remaining blocker "
                "once everything else characterized so far is provisionally admitted."
            ),
            "detail": {
                "filter/lightLeak:lightLeak": "out, function voronoiCell:60, 2nd blocker behind loop-proof",
                "filter/watercolor:wcSimplify": "inout, function sort2:10, terminal blocker (the operator's named target)",
                "synth/mandelbrot:mandelbrot": "out, functions getPOI/mandelbrot_df64/transformCoords_df64 (df64 double-float emulation helpers), 2nd blocker behind loop-proof; a 3rd blocker (unsupported builtin log) sits behind it",
            },
        },
        "textureLod": {
            "gates_programs": summary["textureLod_gated_programs"],
            "count": len(summary["textureLod_gated_programs"]),
            "method": "Same corpus-wide scan; textureLod is never relaxed by any variant, so it surfaces naturally wherever it is the true next construct.",
            "detail": {
                "filter/parallax:parallax": (
                    "2nd (and confirmed FINAL) blocker behind loop-proof, at main:24. "
                    "Verified clean: once loop-proof + textureLod are both admitted "
                    "(generate_typed_slice_relaxed_all_plus_texturelod.py), the validator "
                    "fully passes with no further hop."
                ),
            },
        },
    },
    "loop_proof_cluster_note": (
        "2 of the census's 20 remaining loop-proof-cluster members (filter/oilPaint:"
        "oilFlatten, filter/smooth:smoothBlend) do NOT actually terminate on the "
        "loop-proof gate on the CURRENT live tree -- confirmed directly against the "
        "real top-level tools/glslcpp (not the probe copy). oilFlatten's real terminal "
        "blocker is 'unsupported builtin ceil' at 19:27 (before the loop is ever "
        "reached); smoothBlend's is 'unsupported global declaration' at 17:1. Both "
        "sit earlier in validate_capabilities' fixed walk order than the loop-proof "
        "checks... no wait, loop-proof checks run FIRST architecturally, meaning "
        "these two programs' loops themselves now pass the loop-proof audit clean on "
        "the live tree (unlike census, which recorded them as loop-proof rejections). "
        "Likely explanation: loop_proof.py's ACCEPTED set was widened for the "
        "zoomBlur/nmReindexStats landing (2026-08-13, after the census's "
        "20260812T225121Z snapshot), incidentally letting other programs' loops "
        "through too. frontier-census.json is accordingly STALE for at least these "
        "two programs and should be re-run before being treated as authoritative "
        "again for the loop-proof cluster."
    ),
    "scan_out_texturelod_results": scan,
}


def pull(key: str) -> dict:
    return probe.get(key, {})


report["primary_targets"] = {
    "synth/bitwise:bitwise": {
        "terminal_blocker": pull("synth/bitwise:bitwise").get("terminal_blocker"),
        "reachable": pull("synth/bitwise:bitwise").get("terminal_blocker_reachable_from_main"),
        "enclosing_function": pull("synth/bitwise:bitwise").get("terminal_blocker_enclosing_function"),
        "downstream_chain": ["none found -- sole blocker, confirmed by relaxing every other "
                              "known construct simultaneously (13-patch mega-relax) with no change"],
        "mechanism": "New scalar-uint XOR admission (distinct from the existing uint-VECTOR "
                     "'uint-vector-bitwise' capability, which only covers uvec2/3/4). No shift "
                     "operators present (independently re-confirmed: unaffected by mega-relax, "
                     "matching the prior report's regex-verified zero-shift-operators finding).",
        "cost": "cheap",
        "portable_via_typed_kernel": True,
    },
    "filter/watercolor:wcSimplify": {
        "terminal_blocker": pull("filter/watercolor:wcSimplify").get("terminal_blocker"),
        "reachable": pull("filter/watercolor:wcSimplify").get("terminal_blocker_reachable_from_main"),
        "enclosing_function": pull("filter/watercolor:wcSimplify").get("terminal_blocker_enclosing_function"),
        "downstream_chain": [
            "VALIDATOR: passes fully once inout admitted (validate_capabilities has no "
            "further objection).",
            "EMITTER (emit_typed_cpp.py, separate module, unpatched): "
            "'only typed assignments are admitted' at 37:5 -- a previously undocumented "
            "second-stage blocker. sort2(...) is called as a bare void-function-call "
            "statement 19 times (Devillard opt_med9 compare-exchange network, confirmed "
            "node-by-node: all 19 are expr-statements whose single expression is 'call', "
            "not 'assign'). The emitter's statement lowering currently has ZERO support "
            "for a bare call-statement of any kind, independent of inout.",
        ],
        "mechanism": "(1) inout parameter admission in BOTH validate_capabilities and "
                     "emit_typed_cpp.py; (2) a genuinely new emitter capability: lowering "
                     "a void user-function call as a bare statement. (2) is not needed by "
                     "any currently-typed program and not needed by filter/median (which "
                     "the source comments say shares the same compare-exchange algorithm "
                     "but implements it without a void helper, avoiding this shape).",
        "cost": "moderate -- two real capability gaps, one of them (bare void-call "
                "statement lowering) unprecedented in the emitter",
        "portable_via_typed_kernel": True,
    },
    "synth/remap:remap": {
        "terminal_blocker": pull("synth/remap:remap").get("terminal_blocker"),
        "reachable": "n/a (uniform block, global scope; unconditionally present regardless "
                     "of control flow) -- but its `data[267]` array is read from main()'s "
                     "per-pixel zone-walk per the source's own header comment, i.e. clearly live",
        "downstream_chain": [
            "unsupported typed type vec4[267] at 6:5 -- `layout(std140) uniform "
            "RemapUniforms { vec4 data[267]; }`, a packed-record buffer (8 zones x 64 "
            "verts + header/control/meta slots) read with RUNTIME-COMPUTED indices "
            "(zone and vertex-pair loop counters), not compile-time-literal ones.",
        ],
        "mechanism": "Two gaps: (1) uniform-block admission itself (singleton, no other "
                     "program declares one); (2) a genuinely NEW runtime capability -- none "
                     "of the existing bounded fixed-size-table mechanisms (fixed-nine caps "
                     "at 9, fixed-grid, fixed-array-parameter, fixed-affine-centers13) "
                     "supports an array this large with dynamically-computed indices; they "
                     "all require a whole-program STATIC proof of the exact index pattern. "
                     "A 267-entry dynamically-indexed uniform array needs a general runtime "
                     "read primitive, not a per-program proof.",
        "cost": "expensive -- the most architecturally novel of the 7 named targets that "
                "still stays inside the typed-kernel path (no new pass needed, unlike "
                "wormhole:deposit)",
        "portable_via_typed_kernel": True,
    },
    "mixer/distortion:distortion": {
        "terminal_blocker": pull("mixer/distortion:distortion").get("terminal_blocker"),
        "reachable": pull("mixer/distortion:distortion").get("terminal_blocker_reachable_from_main"),
        "enclosing_function": pull("mixer/distortion:distortion").get("terminal_blocker_enclosing_function"),
        "downstream_chain": [
            "1. unsupported sampler parameter at 91:33 (applyDisplacement) -- TERMINAL.",
            "2. [sampler-param admitted] -> unsupported sampler expression at 92:29 "
            "(using the sampler once it arrives as a parameter).",
            "3. [+ sampler-expression admitted] -> unsupported builtin dFdx at 102:19 "
            "(would be this program's 16th derivative-admission grant; dFdx/dFdy/fwidth "
            "are admitted only per-node by derivative-admission-v1, never blanket).",
            "4. [+ dFdx/dFdy/fwidth admitted regardless of node identity, extra-hop probe] "
            "-> unsupported typed type float[9] at 31:11 -- ANOTHER local 9-tap kernel, "
            "independent of filter/lighting's.",
            "5. Not reached in this pass: reflect (recorded downstream by the census's "
            "own earlier probe, not independently re-verified past hop 4 here).",
        ],
        "mechanism": "At least FOUR previously-separate capability families stacked: "
                     "sampler-as-parameter (+ sampler-as-expression), a NEW float[9] "
                     "fixed-table profile (own shape, distinct from lighting's and "
                     "sobel's), a 16th program's worth of derivative-admission wiring, "
                     "and reflect builtin admission (shared with filter/lighting).",
        "cost": "most expensive of the 7 named targets; CORRECTS the roadmap's framing "
                "of distortion as bounded by 2 known downstream blockers -- direct "
                "re-probing on the live tree finds at least 4 hops, not 2, before "
                "even reaching reflect",
        "portable_via_typed_kernel": True,
        "caveat": "chain not exhaustively walked past hop 4; could not determine "
                  "whether reflect (hop 5, per census) is genuinely final or whether "
                  "a 6th blocker exists behind it",
    },
    "classicNoisedeck/caustic:caustic": {
        "terminal_blocker": pull("classicNoisedeck/caustic:caustic").get("terminal_blocker"),
        "reachable": False,
        "reachability_method": (
            "THIRD independent verification (after the two cited in "
            "REMAINING-WORK-ROADMAP.md: caustic_word_hash_profile.py's comment and "
            "an independent BFS+manual #if trace). This pass's own call-graph BFS "
            "from main() at the authorized NOISE_TYPE=10 define confirms `constant`, "
            "`constantOffset`, and `randomFromLatticeWithOffset` (which contains the "
            "floatBitsToUint/XOR word-hash carrier at lines 218-236) are ABSENT from "
            "the reachable-function set. Traced to source: `value()`'s NOISE_TYPE "
            "dispatcher (#if/#elif chain) calls `simplexValue` under `#elif "
            "NOISE_TYPE == 10`; the ONLY call site for constant/constantOffset sits "
            "in the final `#else` branch (NOISE_TYPE 1 or 2), which is not taken. "
            "constant/constantOffset/randomFromLatticeWithOffset are defined outside "
            "any #if guard so they DO survive preprocessing into the typed IR (which "
            "is why validate_capabilities even sees the floatBitsToUint/XOR calls and "
            "needs the profile-carrier mechanism at all) -- they are dead by ordinary "
            "call-graph unreachability, not preprocessor elimination."
        ),
        "downstream_chain": ["n/a -- dead code; the 'exact Caustic word hash profile "
                              "carrier required' check is a structural authentication "
                              "gate, not a rejected construct, and is unaffected by any "
                              "construct-level relaxation (confirmed unchanged before/after "
                              "the 13-patch mega-relax)."],
        "mechanism": "authenticate_caustic_word_hash() already implemented per the "
                     "roadmap; remaining work is slice-row wiring only, to formally "
                     "authenticate the carrier as dead-but-present.",
        "cost": "cheap -- definitively settled dead, three independent analyses agree",
        "portable_via_typed_kernel": True,
    },
    "classicNoisedeck/glitch:glitch": {
        "terminal_blocker": pull("classicNoisedeck/glitch:glitch").get("terminal_blocker"),
        "reachable": pull("classicNoisedeck/glitch:glitch").get("terminal_blocker_reachable_from_main"),
        "enclosing_function": pull("classicNoisedeck/glitch:glitch").get("terminal_blocker_enclosing_function"),
        "downstream_chain": [
            "1. unsupported typed type mat4 at 76:10 (function bicubic) -- TERMINAL.",
            "2. [mat4 type admitted] -> unsupported matrix constructor at 76:14 "
            "(only the mat2 4-float constructor is supported today).",
            "3. [+ mat3/mat4 constructors admitted] -> unsupported matrix binary "
            "expression (mat*mat / mat*vec4 multiply restricted to mat2*vec2 today).",
            "4. [+ any mat*mat/mat*vec product admitted] -> VALIDATOR FULLY PASSES, "
            "no further hop (verified via generate_typed_slice_relaxed_all_plus_matctor.py).",
            "EMITTER (unpatched, separate module): still independently rejects mat4 "
            "at its own type-check (1:1, 'unsupported typed type mat4') -- confirms "
            "emitter widening is required in lockstep, exactly matching the roadmap's "
            "already-documented Slice C plan.",
        ],
        "mechanism": "Matrix-dispatch cluster's Slice C: widen mat3-style admission to "
                     "mat4 (type + 16-float constructor + mat*mat/mat*vec4 product) in "
                     "BOTH validator and emitter, preserving double-accumulation "
                     "narrowing (the Curl-tanh-class hazard the roadmap already flags "
                     "for the chained T*Q*S product). No NEW capability family in the "
                     "frozen-44 sense -- widens the existing matrix mechanism the same "
                     "way mat3 already gets node-identity admission for the 5 other "
                     "matrix-cluster programs.",
        "cost": "moderate -- 3 admission points but all one mechanism family, no "
                "surprises beyond what the roadmap already predicted",
        "portable_via_typed_kernel": True,
    },
    "filter/lighting:lighting": {
        "terminal_blocker": pull("filter/lighting:lighting").get("terminal_blocker"),
        "reachable": pull("filter/lighting:lighting").get("terminal_blocker_reachable_from_main"),
        "enclosing_function": pull("filter/lighting:lighting").get("terminal_blocker_enclosing_function"),
        "downstream_chain": [
            "1. unsupported builtin reflect at 93:26 (applyReflection) -- TERMINAL.",
            "2. [reflect admitted] -> unsupported typed type float[9] at 40:11 -- a "
            "LOCAL Sobel-X 9-tap convolution kernel (`float sobel_x[9]`) inside "
            "calculateNormal.",
        ],
        "mechanism": "(1) reflect builtin admission via node-identity (same pattern as "
                     "round/tanh/any -- roadmap already calls this 'likely cheap... but "
                     "unbuilt'). (2) The float[9] blocker is NOT a new capability: "
                     "filter/sobel:sobel is ALREADY TYPED using the identical "
                     "'fixed-nine' mechanism for its own sobel_x/sobel_y kernels "
                     "(SOBEL_KEY = 'filter/sobel:sobel' has a landed profile in "
                     "fixed_nine_table_proof.py). lighting needs its OWN new profile "
                     "entry in that same, already-battle-tested mechanism class -- "
                     "bespoke wiring, not new architecture.",
        "cost": "cheap-ish -- one new node-identity admission plus one new profile "
                "entry reusing an existing, already-shipped mechanism; no unknown-"
                "architecture risk",
        "portable_via_typed_kernel": True,
    },
}

report["other_singletons_found"] = {
    "filter/grime:grime": {
        "note": "Cluster 'Varying admission (v_texCoord): 1 terminal + 3 downstream' "
                "in frontier-census.json. grime is the terminal (own row); "
                "filter/spookyTicker:spookyTicker, filter/texture:texture, and "
                "filter/wobble:wobble each independently need the SAME vec2 varying "
                "admission as their own downstream (2nd) blocker, behind an unrelated "
                "terminal blocker each (confirmed: all three show 'unsupported "
                "varying' as their downstream_after_relax in probe_results.json).",
        "terminal_blocker": pull("filter/grime:grime").get("terminal_blocker"),
        "downstream_chain": [pull("filter/grime:grime").get("downstream_after_relax")],
        "mechanism": "vec2 varying (v_texCoord-shaped) admission gates 4 programs "
                     "total (grime + 3 downstream), a smaller but structurally "
                     "identical situation to the out/textureLod asks.",
        "cost": "cheap-ish per program once the vec2-varying admission itself is built; "
                "grime's own downstream (floatBitsToUint at 38:25) still needs its own "
                "per-node authorization though.",
    },
    "synth/shape:shape": {
        "note": "Genuinely unique cluster ('Global declaration: non-const mutable "
                "global scratch (float)', count 1).",
        "terminal_blocker": pull("synth/shape:shape").get("terminal_blocker"),
        "downstream_chain": [pull("synth/shape:shape").get("downstream_after_relax")],
        "mechanism": "(1) admit a non-const, non-uniform/output mutable float global; "
                     "(2) 'write to source const global' at 459:5 -- a SEPARATE guard "
                     "(distinct from the declaration-admission gate) that fires when "
                     "code writes to something the generator's source-global-literal "
                     "machinery has classified as effectively const. Two real gaps, "
                     "not one.",
        "cost": "not independently costed in depth here (outside the operator's named "
                "7); flagged as a genuine 2-hop singleton for future triage",
    },
    "classicNoisedeck/shapeMixer:shapeMixer": {
        "note": "Part of the matrix-dispatch cluster (shares the mat3 'fwdA' "
                "declaration mechanism with 5 other programs) but its OWN downstream "
                "blocker is unique: refract, not reflect as an earlier roadmap note "
                "speculated. CORRECTION to REMAINING-WORK-ROADMAP.md's matrix-census "
                "paragraph, which says 'shapeMixer hits reflect' -- direct re-probe "
                "on the live tree shows 'unsupported builtin refract' at 675:17, "
                "inside blend() (confirmed reachable from main via the same "
                "call-graph BFS: 'blend' and 'linear_srgb_from_oklab' (the fwdA/"
                "invA consumer) are both in the reachable-function set).",
        "terminal_blocker": pull("classicNoisedeck/shapeMixer:shapeMixer").get("terminal_blocker"),
        "downstream_chain": [pull("classicNoisedeck/shapeMixer:shapeMixer").get("downstream_after_relax")],
        "mechanism": "mat3 admission (shared, matrix-cluster Slice B) then a NEW "
                     "refract() node-identity admission (same family as reflect/any/"
                     "round, zero existing admission path).",
        "cost": "not independently costed in depth; matrix cluster's own readiness "
                "is documented as 'not clean' in REMAINING-WORK-ROADMAP.md and this "
                "finding does not change that verdict, only corrects which builtin "
                "shapeMixer specifically needs",
        "caveat": "chain not walked past refract; could not determine if a further "
                  "blocker (e.g. matrix indexing, which 6 other matrix-cluster "
                  "programs hit) also applies to shapeMixer",
    },
    "classicNoisedeck/moodscape:moodscape": {
        "note": "Matrix cluster's dead-code exclusion (1 of 3 the roadmap already "
                "names). RE-VERIFIED here, one level deeper than the roadmap: not "
                "only is the mat3 fwdA declaration itself unreachable, but the "
                "SECOND blocker behind it ('unsupported typed expression index' at "
                "137:13, inside rgb2hsv) is ALSO dead -- rgb2hsv is absent from the "
                "main()-reachable function set (only hsv2rgb, the reverse conversion, "
                "is reachable). Confirmed by function-name reachability rather than "
                "by reading the source at that line/column, since GLSL "
                "#if-conditional line renumbering during preprocessing makes direct "
                "line/column cross-referencing against the raw corpus .glsl "
                "unreliable (could not independently confirm the exact token at "
                "137:13 in the ORIGINAL source text; relied on the AST's own "
                "reachability data instead, which does not depend on line numbers).",
        "terminal_blocker": pull("classicNoisedeck/moodscape:moodscape").get("terminal_blocker"),
        "downstream_chain": [pull("classicNoisedeck/moodscape:moodscape").get("downstream_after_relax")],
        "cost": "n/a -- doubly dead, confirms roadmap's exclusion",
    },
    "filter/waves:waves": {
        "note": "Cluster 'Builtin admission: any' (count 1), already characterized "
                "by the roadmap's 'Next targets' table as needing a new node-identity "
                "admission with zero existing path. This pass adds one refinement: "
                "'any' admission alone is NOT sufficient -- once admitted, waves hits "
                "a SECOND blocker, 'unsupported typed type bvec2' at 41:13 (the "
                "notEqual(tileOffset, vec2(0.0)) intermediate). bvec2 is currently "
                "admitted only for one exact authenticated node elsewhere "
                "(extrude-bvec2-relational-reduction-v1); waves would need its own.",
        "terminal_blocker": pull("filter/waves:waves").get("terminal_blocker"),
        "downstream_chain": [pull("filter/waves:waves").get("downstream_after_relax")],
        "cost": "not independently costed in depth; flagged as a correction to the "
                "roadmap's 'any admission unlocks waves' framing -- it does not, alone",
    },
    "filter/posterize:posterize": {
        "note": "Cluster 'Builtin admission: round' (count 1). Re-confirmed unchanged "
                "on the live tree: round is not relaxed by this pass's patches "
                "(deliberately, to avoid touching the real per-node round-authentication "
                "machinery), so posterize's terminal blocker is identical before and "
                "after. Matches the roadmap's own detailed round/Math.round-semantics "
                "finding; not re-derived here.",
        "terminal_blocker": pull("filter/posterize:posterize").get("terminal_blocker"),
        "cost": "already well-characterized by REMAINING-WORK-ROADMAP.md; not re-costed here",
    },
    "filter/invert:inv": {
        "note": "Zero-blocker, administrative only (matches roadmap: 'free today'). "
                "Confirmed: VALIDATOR-PASS with NO relaxation applied at all.",
        "terminal_blocker": None,
        "cost": "free",
    },
    "synth/solid:solid": {
        "note": "Zero-blocker, administrative only (matches roadmap: 'free today'). "
                "Confirmed: VALIDATOR-PASS with NO relaxation applied at all.",
        "terminal_blocker": None,
        "cost": "free",
    },
    "filter/wormhole:deposit": {
        "note": "STRUCTURALLY INELIGIBLE for the typed-kernel path (varying vColor, "
                "not vec2 -- confirmed unaffected by this pass's vec2-only varying "
                "relaxation). NOT an open singleton any more: independently confirmed "
                "already resolved via a separate scatter-pass mechanism outside the "
                "typed generator entirely -- include/noisemaker/effects/scatter/"
                "wormhole.hpp and tests/test_scatter_wormhole.cpp both exist in the "
                "live tree, matching REMAINING-WORK-ROADMAP.md's 'PORTED, bit-exact' "
                "closeout.",
        "terminal_blocker": pull("filter/wormhole:deposit").get("terminal_blocker"),
        "cost": "already done -- not part of the open singleton tail",
        "portable_via_typed_kernel": False,
        "portable_via_other_door": "scatter-pass adapter (landed)",
    },
}

out_path = HERE / "singleton-triage.json"
out_path.write_text(json.dumps(report, indent=1, sort_keys=True, default=str))
print("wrote", out_path)
