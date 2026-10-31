"""Run complete deterministic test partitions with bounded child processes."""
from __future__ import annotations

import argparse
import concurrent.futures
import itertools
import json
import math
import os
import pathlib
import platform
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def validate_ids(ids):
    if not ids or any(not isinstance(item, str) or not item or
                      any(character.isspace() for character in item) for item in ids):
        raise ValueError("test discovery returned empty or invalid IDs")
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate discovered test ID")
    return sorted(ids)


FROZEN_MACOS_IDS = (
    "test_julia_oracle.JuliaOracleTests.test_authority_generator_and_materializer",
    "test_publication_roots_shape_spooky.PublicationRootShapeSpookyTests.test_shape_mixer_requires_strict_external_authority_and_live_roots",
    "test_top_level_oracle_unittest_bridge.TopLevelOracleUnittestBridge.test_test_mandelbrot_oracle__test_generator_check_self_test_and_materializer_contract",
)


def select_python_ids(ids, suite):
    ids = validate_ids(ids)
    if suite == "all":
        return ids, []
    if suite not in ("portable", "frozen-macos"):
        raise ValueError("unknown Python suite")
    if any(ids.count(identity) != 1 for identity in FROZEN_MACOS_IDS):
        raise ValueError("frozen macOS routing IDs must each occur exactly once in discovery")
    if suite == "frozen-macos" and (sys.platform != "darwin" or platform.machine() != "arm64"):
        raise ValueError("frozen-macos suite requires darwin/arm64")
    frozen = set(FROZEN_MACOS_IDS)
    selected = [identity for identity in ids if (identity in frozen) == (suite == "frozen-macos")]
    routed = [identity for identity in ids if identity not in selected]
    if Counter(selected + routed) != Counter(ids):
        raise ValueError("Python suite routing does not preserve discovery")
    return selected, routed


def python_discovery(start, pattern):
    loader = unittest.TestLoader()
    suite = loader.discover(str(start), pattern=pattern)
    if loader.errors:
        raise ValueError("test discovery failed: " + "\n".join(loader.errors))
    return validate_ids([case.id() for case in flatten(suite)])


def partition_ids(ids, count):
    partitions = [ids[index::count] for index in range(count)]
    if Counter(item for group in partitions for item in group) != Counter(ids):
        raise ValueError("partition coverage is not the exact discovered ID set")
    return partitions


def bounded(command, seconds):
    started = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=(os.name == "posix"))
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
    return {"exit_code": process.returncode, "timed_out": timed_out,
            "seconds": time.monotonic() - started, "stdout": stdout, "stderr": stderr}


def python_child(start, ids, report):
    sys.path.insert(0, str(start.resolve()))
    loader = unittest.TestLoader()
    print("Loading Python test IDs: " + json.dumps(ids), file=sys.stderr, flush=True)
    suite = loader.loadTestsFromNames(ids)
    loaded = [case.id() for case in flatten(suite)]
    if loader.errors or Counter(loaded) != Counter(ids):
        raise ValueError("selected Python IDs did not load exactly once")
    executed = []
    skipped = []
    fixture_skipped = []

    class Result(unittest.TextTestResult):
        def startTest(self, test):
            executed.append(test.id())
            super().startTest(test)

        def addSkip(self, test, reason):
            identity = test.id()
            if identity in ids:
                skipped.append(identity)
            else:
                # unittest does not call startTest for cases blocked by a
                # skipped class/module fixture. Account for those IDs as
                # skipped, without claiming their methods executed.
                match = re.fullmatch(r"setUp(?:Class|Module) \((.+)\)", identity)
                if match:
                    affected = [item for item in ids if item.startswith(match[1] + ".")]
                    fixture_skipped.extend(affected)
                    skipped.extend(affected)
            super().addSkip(test, reason)

    result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
    report.write_text(json.dumps({"executed_ids": executed,
                                 "accounted_ids": executed + fixture_skipped,
                                 "skipped_ids": skipped,
                                 "failure_count": len(result.failures) + len(result.errors),
                                 "skip_count": len(result.skipped),
                                 "successful": result.wasSuccessful()}))
    return 0 if result.wasSuccessful() else 1


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("python", "native"))
    parser.add_argument("--start-directory", type=pathlib.Path, default=ROOT / "tests")
    parser.add_argument("--pattern", default="test_*.py")
    parser.add_argument("--python-suite", choices=("all", "portable", "frozen-macos"), default="all")
    parser.add_argument("--executable", type=pathlib.Path)
    parser.add_argument("--partitions", type=int, default=8)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--groups", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=float, default=300)
    parser.add_argument("--internal-discover", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--internal-ids", type=pathlib.Path, help=argparse.SUPPRESS)
    parser.add_argument("--internal-report", type=pathlib.Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 1 <= args.partitions <= 8 or not 1 <= args.workers <= 2 or not 1 <= args.groups <= 8:
        parser.error("partitions and groups must be 1..8 and workers must be 1..2")
    if not math.isfinite(args.timeout_seconds) or not 0 < args.timeout_seconds <= 300:
        parser.error("timeout must be positive and at most 300 seconds")
    if args.mode != "python" and args.python_suite != "all":
        parser.error("--python-suite applies only to Python checks")
    return args


def main():
    args = arguments()
    if args.internal_discover:
        args.internal_report.write_text(json.dumps(python_discovery(args.start_directory, args.pattern)))
        return 0
    if args.internal_ids:
        ids = validate_ids(args.internal_ids.read_text().splitlines())
        return python_child(args.start_directory, ids, args.internal_report)
    report = {"mode": args.mode, "success": False, "partitions": [], "peak_children": 0}
    try:
        with tempfile.TemporaryDirectory(prefix="partitioned-checks-") as directory:
            temporary = pathlib.Path(directory)
            if args.mode == "python":
                discovery = temporary / "discovery.json"
                command = [sys.executable, str(pathlib.Path(__file__).resolve()), "python",
                           "--start-directory", str(args.start_directory), "--pattern", args.pattern,
                           "--internal-discover", "--internal-report", str(discovery)]
                found = bounded(command, min(300, max(5, args.timeout_seconds)))
                if found["timed_out"] or found["exit_code"] != 0 or not discovery.is_file():
                    raise ValueError("Python discovery failed: " + found["stderr"])
                ids = validate_ids(json.loads(discovery.read_text()))
            else:
                if not args.executable or args.executable.is_symlink() or not args.executable.is_file():
                    raise ValueError("native executable must be a regular file")
                found = bounded([str(args.executable.resolve()), "--list-tests"], 30)
                if found["timed_out"] or found["exit_code"] != 0:
                    raise ValueError("native discovery failed: " + found["stderr"])
                ids = validate_ids(found["stdout"].splitlines())
                if any(not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", item) for item in ids):
                    raise ValueError("native discovery returned invalid IDs")
            report.update(discovered_ids=ids, discovered_count=len(ids))
            selected_ids, routed_ids = (select_python_ids(ids, args.python_suite)
                                        if args.mode == "python" else (ids, []))
            report.update(python_suite=args.python_suite, selected_ids=selected_ids,
                          selected_count=len(selected_ids), routed_ids=routed_ids,
                          routed_count=len(routed_ids))
            groups = partition_ids(selected_ids, args.partitions)
            lock = threading.Lock()
            active = 0

            def run(index, selected):
                nonlocal active
                row = {"partition": index, "selected_ids": selected, "executed_ids": [],
                       "accounted_ids": [], "skipped_ids": [],
                       "failure_count": 0, "skip_count": 0, "timed_out": False,
                       "coverage_valid": True, "exit_code": 0, "seconds": 0}
                if not selected:
                    return row
                sequence = itertools.count()

                def execute(group):
                    """Run one child invocation for exactly these IDs."""
                    nonlocal active
                    stamp = f"{index}-{next(sequence)}"
                    selection = temporary / f"ids-{stamp}.txt"
                    selection.write_text("\n".join(group) + "\n")
                    child_report = temporary / f"result-{stamp}.json"
                    if args.mode == "python":
                        command = [sys.executable, str(pathlib.Path(__file__).resolve()), "python",
                                   "--start-directory", str(args.start_directory), "--internal-ids",
                                   str(selection), "--internal-report", str(child_report)]
                    else:
                        command = [str(args.executable.resolve()), "--test-ids-file", str(selection)]
                    with lock:
                        active += 1
                        report["peak_children"] = max(report["peak_children"], active)
                    try:
                        actual = bounded(command, args.timeout_seconds)
                    finally:
                        with lock:
                            active -= 1
                    if actual["exit_code"] != 0 or actual["timed_out"]:
                        with lock:
                            print(f"Failed child {stamp}: exit={actual['exit_code']} "
                                  f"timed_out={actual['timed_out']}", file=sys.stderr)
                            print(actual["stdout"], file=sys.stderr, end="")
                            print(actual["stderr"], file=sys.stderr, end="", flush=True)
                    if args.mode == "python" and child_report.is_file():
                        child = json.loads(child_report.read_text())
                        actual.update(executed_ids=child["executed_ids"],
                                      accounted_ids=child["accounted_ids"],
                                      skipped_ids=child["skipped_ids"],
                                      failure_count=child["failure_count"],
                                      skip_count=child["skip_count"])
                        if not child["successful"] and actual["exit_code"] == 0:
                            actual["exit_code"] = 1
                    elif args.mode == "native":
                        outcomes = re.findall(r"^(PASS|FAIL) ([A-Za-z_][A-Za-z_0-9]*)(?::.*)?$",
                                              actual["stdout"] + "\n" + actual["stderr"], re.MULTILINE)
                        actual.update(executed_ids=[item for _, item in outcomes],
                                      accounted_ids=[item for _, item in outcomes],
                                      skipped_ids=[],
                                      skip_count=0,
                                      failure_count=sum(status == "FAIL" for status, _ in outcomes))
                    return actual

                def combine(results):
                    """Merge child results; a timed-out child forces a failure."""
                    row.update(
                        executed_ids=[item for result in results for item in result["executed_ids"]],
                        accounted_ids=[item for result in results for item in result["accounted_ids"]],
                        skipped_ids=[item for result in results for item in result["skipped_ids"]],
                        failure_count=sum(result["failure_count"] for result in results),
                        skip_count=sum(result["skip_count"] for result in results),
                        exit_code=next((result["exit_code"] for result in results
                                        if result["exit_code"] != 0), 0),
                        seconds=sum(result["seconds"] for result in results))
                    row["timed_out"] = any(result["timed_out"] for result in results)

                def attempt(group, depth):
                    """Run IDs; split a timed-out group into bounded halves."""
                    if not group:
                        return []
                    actual = execute(group)
                    if actual["timed_out"] and len(group) > 1 and depth < 3:
                        middle = len(group) // 2
                        return attempt(group[:middle], depth + 1) + attempt(group[middle:], depth + 1)
                    if actual["timed_out"]:
                        # A timed-out child leaves its remaining IDs unaccounted;
                        # no PASS may be claimed for the unfinished group.
                        actual.update(executed_ids=[], accounted_ids=[],
                                      skipped_ids=[], failure_count=1, skip_count=0)
                    return [actual]

                # Start a partition as contiguous groups, so a partition that
                # cannot finish in one child does not first spend a timed-out
                # run on the whole of it.
                size = -(-len(selected) // args.groups)
                results = [result for start in range(0, len(selected), size)
                           for result in attempt(selected[start:start + size], 0)]
                combine(results)
                row["coverage_valid"] = Counter(row["accounted_ids"]) == Counter(selected)
                return row

            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = [pool.submit(run, index, selected) for index, selected in enumerate(groups)]
                report["partitions"] = [future.result() for future in futures]
            all_accounted = [item for row in report["partitions"] for item in row["accounted_ids"]]
            report["success"] = Counter(all_accounted) == Counter(selected_ids) and all(
                row["exit_code"] == 0 and not row["timed_out"] and row["coverage_valid"] and
                row["failure_count"] == 0 for row in report["partitions"])
    except Exception as error:
        report["error"] = str(error)
    print("PARTITIONED_CHECKS " + json.dumps(report, sort_keys=True))
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
