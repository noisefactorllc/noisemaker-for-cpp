"""Derive export-kit/verified-effects.json from parity sweep results.

Supply current, complete sampled and define-enumeration sweeps. Sampled evidence must
meet the continuation plan's 20-variant minimum. An effect is verified only
when it belongs to every supplied cohort and every one of its single-effect sweep cases
was byte-exact on RGBA8 and float32, or was refused by both the authority and this port. Any
divergent, timed-out, or C++-only refused case disqualifies it, and so does having no byte-exact
case at all. export-kit/generate-compat.mjs lists only verified effects.

usage: python3 tools/parity/verified_effects.py --sweep <out-dir> [--sweep <out-dir> ...] [--check]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.parity.sweep import (  # noqa: E402
    Job, RunConfig, build_chain_jobs, build_define_jobs, build_single_jobs,
    define_params, load_catalog, load_existing, run_manifest,
)

TARGET = ROOT / "export-kit/verified-effects.json"
SCHEMA = "noisemaker-cpp.verified-effects.v1"
ACCEPTED = {"byte_exact", "both_refused"}


def expected_jobs(config: RunConfig, selection: dict, directory: Path) -> list[Job]:
    """Recover the mandatory cohort from authenticated source, not saved claims."""
    if (any(type(selection[name]) is not int for name in ("seed", "variants", "joint_samples"))
            or selection["joint_samples"] < 0 or type(selection["no_chains"]) is not bool):
        raise ValueError("invalid case-generation options")
    # The catalog dumper authenticates the CPU source before loading it. Use
    # disposable output beside the evidence; --check never rewrites a sweep.
    with tempfile.TemporaryDirectory(prefix=".verified-catalog-", dir=directory.parent) as scratch:
        catalog = load_catalog(Path(config.cpu_root), Path(config.ledger), Path(scratch), config.node)
    by_id = {effect["id"]: effect for effect in catalog}
    requested = selection["effect_ids"]
    if len(set(requested)) != len(requested) or not set(requested) <= set(by_id):
        raise ValueError("selected effects are absent from the authenticated catalog")
    effects = [effect for effect in catalog if effect["id"] in requested]
    if sorted(selection["define_effect_ids"]) != sorted(effect["id"] for effect in effects if define_params(effect)):
        raise ValueError("selected define effects differ from the authenticated catalog")
    by_kind: dict[str, list[dict]] = {"generator": [], "filter": [], "mixer": []}
    for effect in catalog:
        if (effect.get("domain") == "image" and not effect.get("externalTexture")
                and not effect.get("needsParticlePipeline") and effect["kind"] in by_kind):
            by_kind[effect["kind"]].append(effect)
    jobs = []
    for effect in effects:
        if selection["mode"] == "define-enum":
            jobs.extend(build_define_jobs(effect, selection["seed"], selection["joint_samples"]))
        else:
            jobs.extend(build_single_jobs(effect, selection["variants"], selection["seed"]))
            if not selection["no_chains"]:
                jobs.extend(build_chain_jobs(effect, by_kind, selection["variants"], selection["seed"]))
    return jobs


def validated_sweep(directory: Path) -> tuple[dict, dict[str, dict]]:
    try:
        manifest = json.loads((directory / "run-manifest.json").read_text(encoding="utf-8"))
        document = json.loads((directory / "results.json").read_text(encoding="utf-8"))
        jobs = [Job(**job) for job in manifest["jobs"]]
        config = RunConfig(
            node=manifest["node"]["path"], driver=manifest["cpp_driver"]["path"],
            cpu_root=manifest["cpu_root"], ledger=manifest["authority_ledger"]["path"],
            scratch_root="", timeout=manifest["timeout"])
        selection = manifest["selection"]
        current = run_manifest(config, jobs, manifest["timeout_retry_factor"], selection)
        if current != manifest:
            raise ValueError("saved authority, driver, Node, or harness identity is stale")
        # Hashing the ledger alone cannot detect source edits made without
        # regenerating that ledger. Recheck the files it authenticates too.
        authority_root = Path(config.cpu_root).resolve()
        entries = Path(config.ledger).read_text(encoding="utf-8").splitlines()
        if not entries:
            raise ValueError("empty authority ledger")
        for entry in entries:
            expected_digest, file_name = entry.split("  ", 1)
            file = Path(file_name)
            if not file.is_absolute() or file.resolve() != file or not file.is_relative_to(authority_root):
                raise ValueError("authority ledger contains an escaping or aliased path")
            if hashlib.sha256(file.read_bytes()).hexdigest() != expected_digest:
                raise ValueError(f"authority ledger source changed: {file}")
        digest = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
        meta = document["meta"]
        if meta["manifest_sha256"] != digest or any(meta[name] != selection[name]
                                                  for name in ("mode", "seed", "variants", "joint_samples", "no_chains")):
            raise ValueError("summary does not identify this sweep manifest")
        if selection["mode"] not in ("sampled", "define-enum"):
            raise ValueError("unknown sweep mode")
        effects = set(selection["effect_ids"])
        define_effects = set(selection["define_effect_ids"])
        if not effects or not define_effects <= effects:
            raise ValueError("invalid selected effect identities")
        expected_effects = effects if selection["mode"] == "sampled" else define_effects
        if {job.effect_id for job in jobs if job.kind != "chain"} != expected_effects:
            raise ValueError("case manifest does not cover its selected effects")
        expected = {job.case_id: job for job in jobs}
        regenerated = {job.case_id: job for job in expected_jobs(config, selection, directory)}
        if expected != regenerated:
            raise ValueError("manifest case cohort differs from authenticated catalog and options")
        rows = load_existing(directory / "results.jsonl")
        if len(expected) != len(jobs) or set(rows) != set(expected):
            raise ValueError("results do not cover every unique manifested case")
        for case_id, row in rows.items():
            job = expected[case_id]
            if row["effect_id"] != job.effect_id or row["kind"] != job.kind:
                raise ValueError(f"case identity mismatch: {case_id}")
            if row["classification"] == "byte_exact" and row.get("float32_ok") is not True:
                raise ValueError(f"missing float32 parity proof: {case_id}")
        return manifest, rows
    except (OSError, KeyError, TypeError, ValueError, subprocess.CalledProcessError) as error:
        raise ValueError(f"{directory}: invalid sweep evidence: {error}") from error


def verified(sweeps: list[Path]) -> dict:
    classes: dict[str, set[str]] = {}
    runs = []
    modes = set()
    common_effects: set[str] | None = None
    identity = None
    for sweep in sweeps:
        manifest, rows = validated_sweep(sweep)
        current_identity = {name: manifest[name] for name in
                            ("cpu_root", "authority_ledger", "cpp_driver", "node", "harness")}
        if identity is not None and identity != current_identity:
            raise ValueError("sweeps were produced by different authorities, drivers, Nodes, or harnesses")
        identity = current_identity
        selection = manifest["selection"]
        # The kit's established proof profile is --variants 20 plus define
        # enumeration. A complete but default-only/smaller requested cohort
        # is useful diagnostic evidence, not permission to publish support.
        if selection["mode"] == "sampled" and selection["variants"] < 20:
            raise ValueError("export claims require at least 20 sampled variants per effect")
        modes.add(selection["mode"])
        selected_effects = set(selection["effect_ids"])
        common_effects = selected_effects if common_effects is None else common_effects & selected_effects
        runs.append({"seed": selection["seed"], "variants": selection["variants"],
                     "mode": selection["mode"], "cases": len(rows),
                     "manifest_sha256": hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()})
        for row in rows.values():
            if row["kind"] == "chain":
                continue
            classes.setdefault(row["effect_id"], set()).add(row["classification"])
    if modes != {"sampled", "define-enum"}:
        raise ValueError("both sampled and define-enum sweeps are required")
    effects = sorted(effect for effect, seen in classes.items()
                     if effect in (common_effects or set()) and seen <= ACCEPTED and "byte_exact" in seen)
    return {"schema": SCHEMA, "sweeps": runs, "swept_effects": len(classes), "effects": effects}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep", action="append", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        output = json.dumps(verified(arguments.sweep), indent=2) + "\n"
    except ValueError as error:
        print(f"verified_effects: {error}", file=sys.stderr)
        return 1
    if arguments.check:
        if TARGET.read_text(encoding="utf-8") != output:
            print("verified_effects: export-kit/verified-effects.json does not match these sweeps", file=sys.stderr)
            return 1
    else:
        TARGET.write_text(output, encoding="utf-8")
    print(f"verified_effects: {len(json.loads(output)['effects'])} verified effects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
