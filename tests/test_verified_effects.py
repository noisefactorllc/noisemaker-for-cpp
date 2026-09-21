"""Export claims require complete, current sweep evidence."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from tools.parity import sweep, verified_effects


class VerifiedEffectsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="verified-effects-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name).resolve()
        inputs = {}
        for name in ("node", "driver", "ledger"):
            file = self.root / name
            file.write_text(f"original {name}\n")
            inputs[name] = str(file)
        self.authority_source = self.root / "cpu-source.mjs"
        self.authority_source.write_text("original CPU behavior\n")
        digest = hashlib.sha256(self.authority_source.read_bytes()).hexdigest()
        (self.root / "ledger").write_text(f"{digest}  {self.authority_source}\n")
        self.config = sweep.RunConfig(**inputs, cpu_root=str(self.root),
                                     scratch_root=str(self.root / "scratch"), timeout=45.0)
        self.catalog = [{"id": effect, "namespace": effect.split("/")[0],
                         "func": effect.split("/")[1], "domain": "image", "kind": "generator",
                         "params": {"a": {"type": "bool", "default": False, "define": "A"},
                                    "b": {"type": "bool", "default": True, "define": "B"}}}
                        for effect in ("synth/solid", "other/effect")]
        self.catalog.extend({"id": effect, "namespace": kind, "func": "test",
                             "domain": "image", "kind": kind, "params": {}}
                            for kind, effect in (("filter", "filter/test"), ("mixer", "mixer/test")))
        catalog_patch = patch.object(verified_effects, "load_catalog", return_value=self.catalog, create=True)
        catalog_patch.start()
        self.addCleanup(catalog_patch.stop)
        self.directories = []
        for mode in ("sampled", "define-enum"):
            directory = self.root / mode
            directory.mkdir()
            self.write_cohort(directory, mode)
            self.directories.append(directory)

    def write_cohort(self, directory, mode, effect_index=0, joint_samples=3, no_chains=True, variants=20):
        effect = self.catalog[effect_index]
        jobs = (sweep.build_define_jobs(effect, 1, joint_samples) if mode == "define-enum"
                else sweep.build_single_jobs(effect, variants, 1))
        if mode == "sampled" and not no_chains:
            by_kind = {kind: [item for item in self.catalog if item["kind"] == kind]
                       for kind in ("generator", "filter", "mixer")}
            jobs.extend(sweep.build_chain_jobs(effect, by_kind, variants, 1))
        selection = {"mode": mode, "seed": 1, "variants": variants, "joint_samples": joint_samples,
                     "no_chains": no_chains, "effect_ids": [effect["id"]], "define_effect_ids": [effect["id"]]}
        manifest = sweep.run_manifest(self.config, jobs, 4.0, selection)
        self.write_evidence(directory, manifest)

    def write_evidence(self, directory, manifest):
        (directory / "run-manifest.json").write_text(json.dumps(manifest))
        meta = {name: manifest["selection"][name] for name in
                ("seed", "variants", "mode", "joint_samples", "no_chains") if name in manifest["selection"]}
        meta["manifest_sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
        (directory / "results.json").write_text(json.dumps({"meta": meta}))
        rows = [{"case_id": job["case_id"], "effect_id": job["effect_id"], "kind": job["kind"],
                 "classification": "byte_exact", "float32_ok": True} for job in manifest["jobs"]]
        (directory / "results.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))

    def test_final_successful_retry_supersedes_timeout(self) -> None:
        file = self.directories[0] / "results.jsonl"
        original = file.read_text()
        row = json.loads(original.splitlines()[0])
        file.write_text(json.dumps(dict(row, classification="timeout", float32_ok=False)) + "\n" + original)
        result = verified_effects.verified(self.directories)
        self.assertEqual(result["effects"], ["synth/solid"])
        self.assertEqual(result["sweeps"][0]["cases"], 20)

    def test_missing_manifest_or_summary_identity_is_rejected(self) -> None:
        for name in ("run-manifest.json", "results.json"):
            file = self.directories[0] / name
            original = file.read_text()
            with self.subTest(name=name):
                file.write_text("{}")
                with self.assertRaises(ValueError):
                    verified_effects.verified(self.directories)
            file.write_text(original)

    def test_changed_authority_driver_or_node_is_rejected(self) -> None:
        for name in ("ledger", "driver", "node"):
            file = self.root / name
            original = file.read_text()
            with self.subTest(name=name):
                file.write_text("changed input\n")
                with self.assertRaises(ValueError):
                    verified_effects.verified(self.directories)
            file.write_text(original)

    def test_changed_authority_file_cannot_hide_behind_unchanged_ledger(self) -> None:
        self.authority_source.write_text("changed CPU behavior\n")
        with self.assertRaises(ValueError):
            verified_effects.verified(self.directories)

    def test_incomplete_case_cohort_is_rejected(self) -> None:
        (self.directories[0] / "results.jsonl").write_text("")
        with self.assertRaises(ValueError):
            verified_effects.verified(self.directories)

    def test_exact_row_without_float32_proof_is_rejected(self) -> None:
        file = self.directories[0] / "results.jsonl"
        rows = [json.loads(line) for line in file.read_text().splitlines()]
        del rows[0]["float32_ok"]
        file.write_text("".join(json.dumps(row) + "\n" for row in rows))
        with self.assertRaises(ValueError):
            verified_effects.verified(self.directories)

    def test_default_only_or_reduced_sampling_cannot_justify_claims(self) -> None:
        for variants in (1, 19):
            with self.subTest(variants=variants):
                self.write_cohort(self.directories[0], "sampled", variants=variants)
                with self.assertRaisesRegex(ValueError, "at least 20 sampled variants"):
                    verified_effects.verified(self.directories)

    def test_missing_define_enumeration_cannot_justify_claims(self) -> None:
        with self.assertRaises(ValueError):
            verified_effects.verified(self.directories[:1])

    def test_unrelated_define_sweep_does_not_verify_sampled_effect(self) -> None:
        directory = self.directories[1]
        self.write_cohort(directory, "define-enum", effect_index=1)
        self.assertEqual(verified_effects.verified(self.directories)["effects"], [])

    def test_rewritten_manifest_cannot_reduce_or_relabel_expected_cases(self) -> None:
        for index, mutation in ((0, "drop"), (1, "drop"), (1, "relabel"),
                                (1, "joint_count"), (0, "source"), (0, "seed"),
                                (1, "missing_option"), (1, "hide_defines")):
            directory = self.directories[index]
            original = json.loads((directory / "run-manifest.json").read_text())
            manifest = json.loads(json.dumps(original))
            if mutation == "drop":
                manifest["jobs"].pop(0)
            elif mutation == "relabel":
                manifest["jobs"] = json.loads((self.directories[0] / "run-manifest.json").read_text())["jobs"]
            elif mutation == "joint_count":
                manifest["selection"]["joint_samples"] = 1
            elif mutation == "source":
                manifest["jobs"][0]["source"] = "solid()"
            elif mutation == "seed":
                manifest["jobs"][0]["seed"] += 1
            elif mutation == "missing_option":
                del manifest["selection"]["joint_samples"]
            elif mutation == "hide_defines":
                manifest["selection"]["define_effect_ids"] = []
                manifest["jobs"] = []
            with self.subTest(index=index, mutation=mutation):
                self.write_evidence(directory, manifest)
                with self.assertRaises(ValueError):
                    verified_effects.verified(self.directories)
            self.write_evidence(directory, original)

    def test_custom_joint_sample_count_is_reproduced(self) -> None:
        self.write_cohort(self.directories[1], "define-enum", joint_samples=1)
        self.assertEqual(verified_effects.verified(self.directories)["effects"], ["synth/solid"])

    def test_requested_chain_cohort_cannot_be_omitted(self) -> None:
        directory = self.directories[0]
        self.write_cohort(directory, "sampled", no_chains=False)
        self.assertEqual(verified_effects.verified(self.directories)["effects"], ["synth/solid"])
        manifest = json.loads((directory / "run-manifest.json").read_text())
        manifest["jobs"] = [job for job in manifest["jobs"] if job["kind"] != "chain"]
        self.write_evidence(directory, manifest)
        with self.assertRaises(ValueError):
            verified_effects.verified(self.directories)

    def test_check_failure_does_not_rewrite_committed_claims(self) -> None:
        target = self.root / "verified.json"
        target.write_text("original committed claims\n")
        with patch.object(verified_effects, "TARGET", target), \
             contextlib.redirect_stderr(io.StringIO()):
            result = verified_effects.main(["--sweep", str(self.directories[0]),
                                            "--sweep", str(self.directories[1]), "--check"])
        self.assertEqual(result, 1)
        self.assertEqual(target.read_text(), "original committed claims\n")


if __name__ == "__main__":
    unittest.main()
