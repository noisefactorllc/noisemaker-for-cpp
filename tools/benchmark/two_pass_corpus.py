#!/usr/bin/env python3
"""Two independent full admitted-corpus passes, per lane, into an external root.

Each pass renders every admitted corpus record twice -- once through the JS CPU
authority runner and once through the C++ benchmark driver -- writing raw
top-down RGBA8 and a normalized plan relation for each. ``--compare`` then
proves four things in order, per record: the refusal classification lands in
the frozen table, the two lanes' relations are identical, their RGBA8 bytes are
identical to the byte, and each lane reproduces itself across the two passes.

Nothing this script writes ever has a path inside the checkout. ``--output-root``
must be absolute and outside ``--repo-root``, and the drivers themselves refuse
an in-repo output path, so "do not check raw frames into Git" holds because the
frames never have a name in the repository to begin with.

Correctness blocks; performance only reports. No timing figure is compared,
thresholded, or asserted anywhere below.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from tools.benchmark.corpus_lane import (  # noqa: E402
    BENCHMARK_SAMPLES,
    BENCHMARK_WARMUPS,
    DIVERGENCE_SCHEMA,
    JS_RUNNER,
    admitted_records,
    contains_declared_tail,
    load_corpus,
    load_exclusions,
    record_flags,
    relation_field_diff,
    relation_sha256,
)
from tools.benchmark.exact_compare import compare_rgba8, format_diagnostics  # noqa: E402

SUMMARY_SCHEMA = "noisemaker-cpp.corpus-pass-summary.v1"
# Bounded diagnostics: a divergence report names at most this many records in
# full, exactly like the parity lane's bounded batch reporting.
DIVERGENCE_PREVIEW = 4


def safe_name(record_id: str) -> str:
    """A filesystem name for a record id such as ``filter/bloom#default``."""
    return record_id.replace("/", "__").replace("#", "--")


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_external(path: pathlib.Path, repo_root: pathlib.Path, label: str) -> pathlib.Path:
    if not path.is_absolute():
        raise SystemExit(f"{label} must be absolute: {path}")
    resolved = path.resolve()
    if resolved == repo_root or repo_root in resolved.parents:
        raise SystemExit(f"{label} must resolve outside the repository: {path}")
    return resolved


def read_json(path: pathlib.Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def refusal_detail(completed: subprocess.CompletedProcess[str]) -> str:
    if completed.returncode == 0:
        return ""
    try:
        return json.loads(completed.stdout or "{}").get("detail", "")
    except json.JSONDecodeError:
        return (completed.stdout or completed.stderr).strip()[:200]


def run_pass(args: argparse.Namespace) -> int:
    repo_root = pathlib.Path(args.repo_root).resolve()
    output_root = require_external(pathlib.Path(args.output_root), repo_root, "--output-root")
    cpu_root = pathlib.Path(args.cpu_root).resolve()
    node = shutil.which("node")
    if node is None:
        raise SystemExit("node is required for the CPU authority runner")

    manifest = load_corpus()
    records = admitted_records(manifest)

    js_dir = output_root / "js"
    cpp_dir = output_root / "cpp"
    work_dir = output_root / "work"
    for directory in (js_dir, cpp_dir, work_dir):
        directory.mkdir(parents=True, exist_ok=True)

    entries: list[dict] = []
    started = time.monotonic()
    for record in records:
        name = safe_name(record["id"])
        options = record["options"]
        source = work_dir / f"{name}.dsl"
        source.write_text(record["source"], encoding="utf-8")
        case = work_dir / f"{name}.case.json"
        case.write_text(json.dumps(record), encoding="utf-8")

        js_raw = js_dir / f"{name}.rgba8"
        js_meta = js_dir / f"{name}.json"
        js_relation = js_dir / f"{name}.relation.json"
        js = subprocess.run(
            [node, str(JS_RUNNER), "--cpu-root", str(cpu_root), "--case", str(case),
             "--rgba8-output", str(js_raw), "--metadata-output", str(js_meta),
             "--plan-relation-output", str(js_relation)],
            capture_output=True, text=True)

        cpp_raw = cpp_dir / f"{name}.rgba8"
        cpp_benchmark = cpp_dir / f"{name}.benchmark.json"
        cpp_relation = cpp_dir / f"{name}.relation.json"
        cpp = subprocess.run(
            [args.cpp_benchmark, *record_flags(record, source),
             "--record-id", record["id"],
             "--one-shot", str(options["oneShot"]),
             "--render-scale", repr(options["renderScale"]),
             "--timing-mode", args.timing_mode,
             "--warmups", str(args.warmups), "--samples", str(args.samples),
             "--repo-root", str(repo_root),
             "--rgba8-output", str(cpp_raw),
             "--benchmark-output", str(cpp_benchmark),
             "--plan-relation-output", str(cpp_relation)],
            capture_output=True, text=True)

        # The parity driver runs on the same record so the benchmark driver's
        # timing wrapper can be proven not to have moved a single byte. Only
        # its digest is retained; a second copy of every frame would be
        # diagnostics nobody reads.
        case_raw = work_dir / f"{name}.case.rgba8"
        case_meta = work_dir / f"{name}.case.json.out"
        case_run = subprocess.run(
            [args.cpp_case, *record_flags(record, source),
             "--repo-root", str(repo_root),
             "--rgba8-output", str(case_raw), "--metadata-output", str(case_meta)],
            capture_output=True, text=True)

        benchmark_document = read_json(cpp_benchmark)
        entries.append({
            "id": record["id"],
            "effectId": record["effectId"],
            "name": name,
            "jsExit": js.returncode,
            "cppExit": cpp.returncode,
            "cppCaseExit": case_run.returncode,
            "cppDetail": refusal_detail(cpp),
            "cppCaseDetail": refusal_detail(case_run),
            "jsStderr": js.stderr.strip()[:200] if js.returncode != 0 else "",
            "jsRgba8Sha256": sha256_file(js_raw),
            "cppRgba8Sha256": sha256_file(cpp_raw),
            "cppCaseRgba8Sha256": sha256_file(case_raw),
            "mode": None if benchmark_document is None else benchmark_document.get("mode"),
            "declaredEffectIds": record["plan"]["effectIds"],
            "declaredPassKeys": record["plan"]["passKeys"],
            "dimensions": {"width": options["width"], "height": options["height"]},
        })
        case_raw.unlink(missing_ok=True)

    summary = {
        "schema": SUMMARY_SCHEMA,
        "timingMode": args.timing_mode,
        "warmups": args.warmups,
        "samples": args.samples,
        "repoRoot": str(repo_root),
        "cpuRoot": str(cpu_root),
        "cppBenchmark": args.cpp_benchmark,
        "cppCase": args.cpp_case,
        "manifestSha256": manifest["manifestSha256"],
        "recordCount": len(records),
        "wallClockSeconds": round(time.monotonic() - started, 3),
        "records": entries,
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"pass complete: {len(records)} records -> {output_root}")
    return 0


def classify(entry: dict, exclusions: dict) -> str:
    effect = entry["effectId"]
    if effect in exclusions["authorityRefused"]:
        return "authorityRefused"
    if effect in exclusions["executorRefused"]:
        return "executorRefused"
    return "rendered"


def compare_passes(first: pathlib.Path, second: pathlib.Path,
                   report_path: pathlib.Path | None) -> int:
    exclusions = load_exclusions()
    summaries = []
    for root in (first, second):
        document = read_json(root / "summary.json")
        if document is None or document.get("schema") != SUMMARY_SCHEMA:
            raise SystemExit(f"{root} does not hold a {SUMMARY_SCHEMA} summary")
        summaries.append(document)
    if summaries[0]["timingMode"] != summaries[1]["timingMode"]:
        raise SystemExit(
            "refusing to compare passes measured in different timing modes: "
            f"{summaries[0]['timingMode']} vs {summaries[1]['timingMode']}")
    if summaries[0]["manifestSha256"] != summaries[1]["manifestSha256"]:
        raise SystemExit("refusing to compare passes taken against different corpus manifests")

    divergences: list[dict] = []
    counts = {"records": 0, "byteExact": 0, "executorRefused": 0,
              "authorityRefused": 0, "divergent": 0}

    by_id = [{entry["id"]: entry for entry in summary["records"]} for summary in summaries]
    if sorted(by_id[0]) != sorted(by_id[1]):
        raise SystemExit("the two passes cover different record sets")

    for record_id in sorted(by_id[0]):
        counts["records"] += 1
        entries = [by_id[0][record_id], by_id[1][record_id]]
        expected = classify(entries[0], exclusions)
        record_divergent = False

        for index, (root, entry) in enumerate(zip((first, second), entries), start=1):
            name = entry["name"]
            # Stage 1 -- refusal classification against the frozen table.
            if expected == "rendered":
                ok = entry["jsExit"] == 0 and entry["cppExit"] == 0
            elif expected == "executorRefused":
                ok = (entry["jsExit"] == 0 and entry["cppExit"] == 4
                      and entry["cppDetail"] == exclusions["executorRefused"][entry["effectId"]])
            else:
                ok = entry["jsExit"] != 0 and entry["cppExit"] == 4
            if not ok:
                divergences.append({
                    "recordId": record_id, "pass": index, "stage": "classification",
                    "expected": expected, "jsExit": entry["jsExit"],
                    "cppExit": entry["cppExit"], "cppDetail": entry["cppDetail"],
                })
                record_divergent = True
                continue
            if expected != "rendered":
                continue
            if entry["mode"] != summaries[index - 1]["timingMode"]:
                divergences.append({
                    "recordId": record_id, "pass": index, "stage": "classification",
                    "expected": summaries[index - 1]["timingMode"], "mode": entry["mode"],
                })
                record_divergent = True
                continue

            # Stage 2 -- relation equality, plus the containment oracle.
            js_relation = read_json(root / "js" / f"{name}.relation.json")
            cpp_relation = read_json(root / "cpp" / f"{name}.relation.json")
            if js_relation is None or cpp_relation is None:
                divergences.append({"recordId": record_id, "pass": index,
                                    "stage": "relation", "detail": "a relation document is missing"})
                record_divergent = True
                continue
            for label, document in (("js", js_relation), ("cpp", cpp_relation)):
                derived = relation_sha256(document)
                if derived != document["relationSha256"]:
                    divergences.append({
                        "recordId": record_id, "pass": index, "stage": "relation",
                        "detail": f"{label} relationSha256 is not the digest of its own fields",
                        "declared": document["relationSha256"], "derived": derived,
                    })
                    record_divergent = True
            if js_relation["relationSha256"] != cpp_relation["relationSha256"]:
                divergences.append({
                    "recordId": record_id, "pass": index, "stage": "relation",
                    "fields": relation_field_diff(js_relation, cpp_relation),
                })
                record_divergent = True
                continue
            for label, document in (("js", js_relation), ("cpp", cpp_relation)):
                if not contains_declared_tail(document["effectIds"], entry["declaredEffectIds"]):
                    divergences.append({"recordId": record_id, "pass": index, "stage": "relation",
                                        "detail": f"{label} effectIds do not end with the declared tail",
                                        "observed": document["effectIds"],
                                        "declared": entry["declaredEffectIds"]})
                    record_divergent = True
                if not contains_declared_tail(document["passKeys"], entry["declaredPassKeys"]):
                    divergences.append({"recordId": record_id, "pass": index, "stage": "relation",
                                        "detail": f"{label} passKeys do not end with the declared tail",
                                        "observed": document["passKeys"],
                                        "declared": entry["declaredPassKeys"]})
                    record_divergent = True

            # Stage 3 -- byte equality, zero tolerance.
            js_bytes = (root / "js" / f"{name}.rgba8").read_bytes()
            cpp_bytes = (root / "cpp" / f"{name}.rgba8").read_bytes()
            result = compare_rgba8(entry["dimensions"]["width"], entry["dimensions"]["height"],
                                   js_bytes, cpp_bytes)
            if not result["ok"]:
                divergences.append({
                    "recordId": record_id, "pass": index, "stage": "bytes", "bytes": result,
                    "artifacts": {"jsRgba8": str(root / "js" / f"{name}.rgba8"),
                                  "cppRgba8": str(root / "cpp" / f"{name}.rgba8")},
                })
                record_divergent = True
                continue
            if entry["cppCaseExit"] != 0 or entry["cppCaseRgba8Sha256"] != entry["cppRgba8Sha256"]:
                divergences.append({
                    "recordId": record_id, "pass": index, "stage": "bytes",
                    "detail": "the benchmark driver and the parity driver disagree",
                    "benchmarkSha256": entry["cppRgba8Sha256"],
                    "caseSha256": entry["cppCaseRgba8Sha256"],
                    "caseExit": entry["cppCaseExit"],
                })
                record_divergent = True

        # Stage 4 -- pass-to-pass determinism, per lane. Timing samples are the
        # only thing excluded from this comparison.
        for lane, key in (("js", "jsRgba8Sha256"), ("cpp", "cppRgba8Sha256")):
            if entries[0][key] != entries[1][key]:
                divergences.append({"recordId": record_id, "stage": "determinism",
                                    "lane": lane, "pass1": entries[0][key], "pass2": entries[1][key]})
                record_divergent = True
        for lane in ("js", "cpp"):
            digests = []
            for root, entry in zip((first, second), entries):
                document = read_json(root / lane / f"{entry['name']}.relation.json")
                digests.append(None if document is None else document["relationSha256"])
            if digests[0] != digests[1]:
                divergences.append({"recordId": record_id, "stage": "determinism",
                                    "lane": f"{lane}-relation",
                                    "pass1": digests[0], "pass2": digests[1]})
                record_divergent = True

        if record_divergent:
            counts["divergent"] += 1
        elif expected == "rendered":
            counts["byteExact"] += 1
        elif expected == "executorRefused":
            counts["executorRefused"] += 1
        else:
            counts["authorityRefused"] += 1

    report = {
        "schema": DIVERGENCE_SCHEMA,
        "timingMode": summaries[0]["timingMode"],
        "passes": [str(first), str(second)],
        "counts": counts,
        "divergences": divergences,
        "firstFour": divergences[:DIVERGENCE_PREVIEW],
    }
    if report_path is not None:
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    print(json.dumps({"counts": counts, "divergenceCount": len(divergences)}, sort_keys=True))
    for divergence in divergences[:DIVERGENCE_PREVIEW]:
        if divergence.get("stage") == "bytes" and "bytes" in divergence:
            print(f"{divergence['recordId']}: {format_diagnostics(divergence['bytes'])}")
        else:
            print(f"{divergence['recordId']}: {json.dumps(divergence, sort_keys=True)[:400]}")

    expected_counts = {
        "rendered": exclusions["byteExactCount"],
        "executorRefused": len(exclusions["executorRefused"]),
        "authorityRefused": len(exclusions["authorityRefused"]),
    }
    ok = (not divergences
          and counts["byteExact"] == expected_counts["rendered"]
          and counts["executorRefused"] == expected_counts["executorRefused"]
          and counts["authorityRefused"] == expected_counts["authorityRefused"]
          and counts["records"] == sum(expected_counts.values()))
    if not ok:
        print(f"expected {expected_counts} over {sum(expected_counts.values())} records",
              file=sys.stderr)
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root")
    parser.add_argument("--cpu-root")
    parser.add_argument("--cpp-benchmark")
    parser.add_argument("--cpp-case")
    parser.add_argument("--output-root")
    parser.add_argument("--timing-mode", default="render_only",
                        choices=("render_only", "compile_and_render"))
    parser.add_argument("--warmups", type=int, default=BENCHMARK_WARMUPS)
    parser.add_argument("--samples", type=int, default=BENCHMARK_SAMPLES)
    parser.add_argument("--compare", nargs=2, metavar=("PASS1", "PASS2"))
    parser.add_argument("--report")
    args = parser.parse_args(argv)

    if args.compare:
        report = pathlib.Path(args.report).resolve() if args.report else None
        return compare_passes(pathlib.Path(args.compare[0]).resolve(),
                              pathlib.Path(args.compare[1]).resolve(), report)

    missing = [name for name in ("repo_root", "cpu_root", "cpp_benchmark", "cpp_case",
                                 "output_root") if getattr(args, name) is None]
    if missing:
        parser.error("missing required options: " + ", ".join(f"--{n.replace('_', '-')}" for n in missing))
    if args.warmups < BENCHMARK_WARMUPS or args.samples < BENCHMARK_SAMPLES:
        parser.error(f"--warmups must be >= {BENCHMARK_WARMUPS} and --samples >= {BENCHMARK_SAMPLES}")
    for name in ("cpp_benchmark", "cpp_case"):
        candidate = pathlib.Path(getattr(args, name))
        if not (candidate.is_file() and os.access(candidate, os.X_OK)):
            parser.error(f"--{name.replace('_', '-')} is not an executable file: {candidate}")
    return run_pass(args)


if __name__ == "__main__":
    raise SystemExit(main())
