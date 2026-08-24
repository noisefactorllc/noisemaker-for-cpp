"""Corpus-wide scan (all 58 currently-unported programs) for how many
programs are really gated by:
  (a) `out`/`inout` parameter direction
  (b) `textureLod`

Method per program, all against the REAL parse_program/analyze_program:
  1. unmodified validate_capabilities() -> terminal blocker.
  2. generate_typed_slice_relaxed_loopproof_only -> blocker with ONLY the
     loop-proof gates relaxed (isolates what's immediately behind loop-proof,
     without also masking parameter-direction or anything else).
  3. generate_typed_slice_relaxed_no_paramdir -> blocker with everything
     EXCEPT parameter-direction relaxed (isolates whether `out`/`inout`
     survives as the real remaining blocker once every other known
     construct is provisionally admitted).
  4. generate_typed_slice_relaxed_all -> blocker with everything relaxed
     (the textureLod scan: since textureLod is never relaxed by any variant,
     it surfaces here or in (1)/(2) whenever it is truly the next construct).

A program "is gated by out/inout" if step 3's message names
"unsupported parameter direction" (out or inout) -- i.e. it is the one
thing standing between that program and a full validator pass once every
other currently-characterized capability gap is provisionally closed.

A program "is gated by textureLod" if step (1), (2), or (4)'s message is
exactly "unsupported builtin textureLod".

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
from tools.glslcpp import generate_typed_slice_relaxed_all as genr_all  # noqa: E402
from tools.glslcpp import generate_typed_slice_relaxed_loopproof_only as genr_lp  # noqa: E402
from tools.glslcpp import generate_typed_slice_relaxed_no_paramdir as genr_np  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = PROBE_REPO / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

UNPORTED = json.loads((HERE / "unported_58.json").read_text())
assert len(UNPORTED) == 58


def first_line(error: BaseException) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else type(error).__name__


def run_validator(module, program, entry):
    try:
        module.validate_capabilities(
            program, module.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"])
        return "VALIDATOR-PASS"
    except module.GeneratorError as error:
        return first_line(error)
    except Exception as error:  # noqa: BLE001
        return f"UNEXPECTED {type(error).__name__}: {first_line(error)}"


def probe(key: str) -> dict:
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    row = {"program_key": key}
    try:
        defines = gen._defaults(PROBE_REPO, key)
    except Exception as error:  # noqa: BLE001
        row["error"] = f"DEFAULTS: {first_line(error)}"
        return row

    def fresh_program():
        return analyze_program(parse_program(raw, key, defines), key)

    try:
        row["terminal_unmodified"] = run_validator(gen, fresh_program(), entry)
    except Exception as error:  # noqa: BLE001
        row["terminal_unmodified"] = f"PARSE/ANALYZE ERROR: {first_line(error)}"
        row["parse_traceback"] = traceback.format_exc()
        return row

    row["loopproof_only_relaxed"] = run_validator(genr_lp, fresh_program(), entry)
    row["no_paramdir_relaxed"] = run_validator(genr_np, fresh_program(), entry)
    row["all_relaxed"] = run_validator(genr_all, fresh_program(), entry)
    return row


def main() -> int:
    results = {}
    out_path = HERE / "scan_out_texturelod_results.json"
    for i, key in enumerate(UNPORTED, 1):
        try:
            results[key] = probe(key)
        except Exception:  # noqa: BLE001
            results[key] = {"program_key": key, "crash": traceback.format_exc()}
        print(f"[{i}/{len(UNPORTED)}] {key}", flush=True)
        for field in ("terminal_unmodified", "loopproof_only_relaxed",
                       "no_paramdir_relaxed", "all_relaxed"):
            if field in results[key]:
                print(f"    {field}: {results[key][field]}", flush=True)
        out_path.write_text(json.dumps(results, indent=1, sort_keys=True, default=str))

    out_gated = []
    texturelod_gated = []
    for key, row in results.items():
        msgs = [row.get(f, "") for f in ("terminal_unmodified", "loopproof_only_relaxed",
                                          "no_paramdir_relaxed", "all_relaxed")]
        if any(isinstance(m, str) and "unsupported parameter direction" in m for m in msgs):
            out_gated.append(key)
        if any(isinstance(m, str) and m.endswith("unsupported builtin textureLod") for m in msgs):
            texturelod_gated.append(key)

    summary = {
        "out_or_inout_gated_programs": sorted(out_gated),
        "textureLod_gated_programs": sorted(texturelod_gated),
    }
    (HERE / "out_texturelod_summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True))
    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
