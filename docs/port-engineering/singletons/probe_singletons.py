"""Singleton-tail triage probe.

Runs the REAL generate_typed_slice.validate_capabilities() (unmodified,
straight `cp -R` copy of the live tools/glslcpp tree, imported from
probe_tree/, never the real tools/glslcpp) against every requested program
key, to get its true terminal blocker. Then runs the SAME programs through
generate_typed_slice_relaxed_all (see build_relaxed_all.py for the exact
11 provisional-admission patches and why each is needed) to see what breaks
next -- the downstream blocker chain.

Also runs a best-effort call-graph BFS from `main()` (same technique as
docs/port-engineering/census/run_census.py) to independently verify whether
the span reported by the terminal-blocker error sits inside a function
reachable from main() at the program's authorized define map
(generate_typed_slice._defaults), which is the mandatory reachability filter.

Read-only w.r.t. the real repo. Writes only under
docs/port-engineering/singletons/. Never runs git.
"""
from __future__ import annotations

import json
import pathlib
import sys
import traceback

HERE = pathlib.Path(__file__).resolve().parent
PROBE_REPO = HERE / "probe_tree"
sys.path.insert(0, str(PROBE_REPO))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp import generate_typed_slice_relaxed_all as genr  # noqa: E402
from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = PROBE_REPO / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}
assert len(ENTRIES) == 212, f"expected 212 corpus programs, got {len(ENTRIES)}"

CENSUS = json.loads((HERE.parent / "census" / "frontier-census.json").read_text())
CENSUS_ROWS = {row["program_key"]: row for row in CENSUS["rows"]}

SLICE = json.loads((PROBE_REPO / "tools/glslcpp/typed_slice.json").read_text())
TYPED_NOW = {row["program_key"] for row in SLICE["programs"]}


def first_line(error: BaseException) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else type(error).__name__


def call_graph_reachable_from_main(program) -> set[str]:
    by_name: dict[str, list] = {}
    for fn in program.functions:
        name = getattr(fn, "name", None)
        if name:
            by_name.setdefault(name, []).append(fn)

    def walk_expr(value, calls: set[str]):
        if value is None:
            return
        kind = getattr(value, "kind", None)
        callee = getattr(value, "callee", None)
        if kind in ("call", "builtin") and isinstance(callee, str):
            calls.add(callee)
        for child in getattr(value, "children", ()) or ():
            walk_expr(child, calls)
        for expr in getattr(value, "expressions", ()) or ():
            walk_expr(expr, calls)

    def walk_stmt(value, calls: set[str]):
        if value is None:
            return
        for expr in getattr(value, "expressions", ()) or ():
            walk_expr(expr, calls)
        for child in getattr(value, "children", ()) or ():
            walk_stmt(child, calls)

    visited: set[str] = set()
    frontier = ["main"] if "main" in by_name else []
    while frontier:
        name = frontier.pop()
        if name in visited:
            continue
        visited.add(name)
        for fn in by_name.get(name, ()):
            calls: set[str] = set()
            for stmt in getattr(fn, "body", ()) or ():
                walk_stmt(stmt, calls)
            for callee in calls:
                if callee in by_name and callee not in visited:
                    frontier.append(callee)
    return visited


def enclosing_function_for_span(program, line: int):
    """Best-effort: which function (by name) lexically contains a span
    starting at `line`? Used to test whether the terminal-blocker location
    sits inside a function reachable from main()."""
    best = None
    for fn in program.functions:
        span = getattr(fn, "span", None)
        if span is None:
            continue
        if span.start_line <= line <= getattr(span, "end_line", span.start_line):
            if best is None or (span.end_line - span.start_line) < (
                    best.span.end_line - best.span.start_line):
                best = fn
    return best


def probe_one(key: str) -> dict:
    entry = ENTRIES[key]
    row: dict = {
        "program_key": key,
        "typed_now": key in TYPED_NOW,
        "census_row": CENSUS_ROWS.get(key),
    }
    try:
        raw = (CORPUS / entry["source"]).read_text()
        defines = gen._defaults(PROBE_REPO, key)
        row["defines"] = defines
        parsed = parse_program(raw, key, defines)
        program = analyze_program(parsed, key)
    except Exception as error:  # noqa: BLE001
        row["parse_error"] = first_line(error)
        row["parse_traceback"] = traceback.format_exc()
        return row

    # Reachability.
    try:
        reachable_fns = call_graph_reachable_from_main(program)
        row["main_reachable_functions"] = sorted(reachable_fns)
    except Exception as error:  # noqa: BLE001
        row["main_reachable_functions"] = f"ERROR: {first_line(error)}"
        reachable_fns = set()

    # Real (unmodified) validator: terminal blocker.
    try:
        gen.validate_capabilities(
            program, gen.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"])
        row["terminal_blocker"] = None
        row["terminal_blocker_status"] = "VALIDATOR-PASS"
    except gen.GeneratorError as error:
        msg = first_line(error)
        row["terminal_blocker"] = msg
        row["terminal_blocker_status"] = "GeneratorError"
        # Try to parse "key:line:col: message" to test reachability.
        try:
            parts = msg.split(":", 3)
            if len(parts) >= 3 and parts[0] == key.split(":")[0].split("/")[0] or True:
                # msg format is "{typed.key}:{line}:{col}: text" where
                # typed.key itself contains ':' (e.g. "synth/bitwise:bitwise"),
                # so split from the right of the key prefix instead.
                assert msg.startswith(key + ":"), "unexpected message shape"
                rest = msg[len(key) + 1:]
                line_str, col_str, _text = rest.split(":", 2)
                line = int(line_str)
                fn = enclosing_function_for_span(program, line)
                row["terminal_blocker_line"] = line
                row["terminal_blocker_enclosing_function"] = getattr(fn, "name", None)
                row["terminal_blocker_reachable_from_main"] = (
                    getattr(fn, "name", None) in reachable_fns if fn is not None else None
                )
        except Exception as parse_error:  # noqa: BLE001
            row["terminal_blocker_location_parse_error"] = first_line(parse_error)
    except Exception as error:  # noqa: BLE001
        row["terminal_blocker"] = f"UNEXPECTED {type(error).__name__}: {first_line(error)}"
        row["terminal_blocker_status"] = "UNEXPECTED"
        row["terminal_blocker_traceback"] = traceback.format_exc()

    # Relaxed validator: downstream blocker chain (one hop past every
    # provisionally-admitted construct simultaneously).
    try:
        parsed_r = parse_program(raw, key, defines)
        program_r = analyze_program(parsed_r, key)
        genr.validate_capabilities(
            program_r, genr.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"])
        row["downstream_after_relax"] = "VALIDATOR-PASS"
        try:
            emit.render_typed_cpp(
                program_r, key, entry["raw_sha256"], "singleton_probe", "bind_singleton_probe")
            row["downstream_emitter_after_relax"] = "pass"
        except Exception as error:  # noqa: BLE001
            row["downstream_emitter_after_relax"] = first_line(error)
    except genr.GeneratorError as error:
        row["downstream_after_relax"] = first_line(error)
    except Exception as error:  # noqa: BLE001
        row["downstream_after_relax"] = f"UNEXPECTED {type(error).__name__}: {first_line(error)}"
        row["downstream_traceback"] = traceback.format_exc()

    return row


TARGETS = [
    # Required singleton targets.
    "synth/bitwise:bitwise",
    "filter/watercolor:wcSimplify",
    "synth/remap:remap",
    "mixer/distortion:distortion",
    "classicNoisedeck/caustic:caustic",
    "classicNoisedeck/glitch:glitch",
    "filter/lighting:lighting",
    # Multi-program adjacent blockers.
    "filter/lightLeak:lightLeak",
    "filter/parallax:parallax",
    # Other one-off clusters found by enumerating frontier-census.json
    # (cluster size <= 2), not in the operator's explicit list.
    "filter/waves:waves",
    "filter/posterize:posterize",
    "classicNoisedeck/shapeMixer:shapeMixer",
    "classicNoisedeck/moodscape:moodscape",
    "synth/shape:shape",
    "filter/grime:grime",
    "filter/invert:inv",
    "synth/solid:solid",
    "filter/wormhole:deposit",
]

# Full loop-proof cluster (program-proof + safety-charge), minus the 2 that
# have already landed since the census was built (zoomBlur, nmReindexStats),
# to determine how many programs `out` and `textureLod` actually gate.
LOOP_PROOF_CLUSTER = [
    "classicNoisedeck/effects:effects",
    "classicNoisedeck/fractal:fractal",
    "classicNoisedeck/noise:noise",
    "filter/blur:blurH",
    "filter/blur:blurV",
    "filter/dither:dither",
    "filter/lightLeak:lightLeak",
    "filter/median:median",
    "filter/normalize:statsFinal",
    "filter/oilPaint:oilFlatten",
    "filter/parallax:parallax",
    "filter/reindex:nmReindexReduce",
    "filter/smooth:smoothBlend",
    "filter/tetraColorArray:tetraColorArray",
    "synth/gabor:gabor",
    "synth/julia:julia",
    "synth/mandelbrot:mandelbrot",
    "synth/newton:newton",
    "synth/noise:noise",
    "synth/testPattern:testPattern",
]

ALL_KEYS = sorted(set(TARGETS) | set(LOOP_PROOF_CLUSTER))


def main() -> int:
    results = {}
    out_path = HERE / "probe_results.json"
    for i, key in enumerate(ALL_KEYS, 1):
        try:
            results[key] = probe_one(key)
        except Exception:  # noqa: BLE001
            results[key] = {"program_key": key, "crash": traceback.format_exc()}
        print(f"[{i}/{len(ALL_KEYS)}] {key}: "
              f"terminal={results[key].get('terminal_blocker')!r} "
              f"downstream={results[key].get('downstream_after_relax')!r}",
              flush=True)
        # Checkpoint after every program.
        out_path.write_text(json.dumps(results, indent=1, sort_keys=True, default=str))
    print("wrote", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
