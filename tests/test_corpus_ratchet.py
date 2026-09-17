"""The corpus/pending ratchet: closure over the authority, exact blockers, derived gates."""

from __future__ import annotations

import copy
import json
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))

from tests import corpus_census  # noqa: E402
from tools.glslcpp import check_corpus, corpus_ratchet  # noqa: E402


class CorpusRatchetTests(unittest.TestCase):
    def temporary_repository(self) -> tempfile.TemporaryDirectory[str]:
        temporary = tempfile.TemporaryDirectory()
        destination = pathlib.Path(temporary.name) / "tools" / "glslcpp" / "corpus"
        destination.parent.mkdir(parents=True)
        shutil.copytree(REPOSITORY / "tools" / "glslcpp" / "corpus", destination)
        return temporary

    @staticmethod
    def corpus(root: pathlib.Path) -> pathlib.Path:
        return check_corpus._corpus_root(root)

    @staticmethod
    def rewrite_pending(root: pathlib.Path, callback) -> None:
        path = check_corpus._corpus_root(root) / "pending.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        callback(document)
        path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def recorded_probe(self, root: pathlib.Path):
        """A probe stand-in returning each program's recorded blocker (the real probe is exercised once below)."""
        document = corpus_ratchet.load_pending(self.corpus(root))
        recorded = {item["program_key"]: item["blocker"] for item in document["pending"]}
        return lambda key, source, effect: copy.deepcopy(recorded[key])

    def test_committed_split_is_closed_over_the_authority_and_every_blocker_reprobes_exactly(self) -> None:
        document = corpus_ratchet.check_pending(REPOSITORY)
        authority = {item["program_key"] for item in document["authority"]["programs"]}
        vendored = {item["program_key"] for item in corpus_census.manifest_programs()}
        pending = {item["program_key"] for item in document["pending"]}
        self.assertFalse(vendored & pending)
        self.assertEqual(authority, vendored | pending)
        self.assertEqual(len(authority), corpus_census.vendored_count() + corpus_census.pending_count())
        for item in document["pending"]:
            self.assertIn(item["blocker"]["stage"], corpus_ratchet.STAGES)

    def test_manifest_builder_reproduces_every_vendored_record(self) -> None:
        corpus_ratchet.verify_builder_reproduces_manifest(REPOSITORY)

    def test_closure_rejects_a_dropped_or_duplicated_program(self) -> None:
        def duplicate(document):
            document["pending"].append({**document["pending"][0],
                                        "program_key": corpus_census.manifest_programs()[0]["program_key"]})
            document["pending"].sort(key=lambda item: item["program_key"])

        cases = {
            "dropped-pending": (lambda document: document["pending"].pop(0), "vendored \\+ pending != authority"),
            "vendored-also-pending": (duplicate, "vendored and pending overlap"),
            "foreign-authority": (lambda document: document["authority"]["programs"].append(
                {"program_key": "zz/never:never", "status": "generated", "file": "never.glsl"}),
                "vendored \\+ pending != authority"),
        }
        for name, (callback, message) in cases.items():
            with self.subTest(case=name), self.temporary_repository() as temporary:
                root = pathlib.Path(temporary)
                self.rewrite_pending(root, callback)
                with self.assertRaisesRegex(check_corpus.CorpusError, message):
                    check_corpus.validate_corpus(root)

    def test_pending_sources_are_hash_bound_and_exactly_enumerated(self) -> None:
        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            first = corpus_ratchet.load_pending(self.corpus(root))["pending"][0]
            (self.corpus(root) / first["source"]).write_bytes(b"tampered")
            with self.assertRaisesRegex(check_corpus.CorpusError, "pending source hash or size mismatch"):
                check_corpus.validate_corpus(root)
        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            (self.corpus(root) / "pending-sources" / "stray.glsl").write_text("void main() {}", encoding="utf-8")
            with self.assertRaisesRegex(check_corpus.CorpusError, "pending source file set drift"):
                check_corpus.validate_corpus(root)

    def test_pending_effect_projections_are_exactly_the_unvendored_effects(self) -> None:
        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            self.rewrite_pending(root, lambda document: document["effects"].pop(sorted(document["effects"])[0]))
            with self.assertRaisesRegex(check_corpus.CorpusError, "pending effect projections drift"):
                check_corpus.validate_corpus(root)

    def test_a_changed_blocker_fails_the_ratchet(self) -> None:
        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            probe = self.recorded_probe(root)
            first = corpus_ratchet.load_pending(self.corpus(root))["pending"][0]["program_key"]

            def drifted(key, source, effect):
                blocker = probe(key, source, effect)
                if key == first:
                    blocker["diagnostic"] += " (moved)"
                return blocker

            with mock.patch.object(corpus_ratchet, "probe_program", side_effect=drifted), \
                    self.assertRaisesRegex(check_corpus.CorpusError, f"{first}: blocker changed"):
                corpus_ratchet.check_pending(root)

    def test_a_pending_program_that_starts_passing_fails_the_ratchet(self) -> None:
        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            probe = self.recorded_probe(root)
            first = corpus_ratchet.load_pending(self.corpus(root))["pending"][0]["program_key"]

            def passing(key, source, effect):
                return None if key == first else probe(key, source, effect)

            with mock.patch.object(corpus_ratchet, "probe_program", side_effect=passing), \
                    self.assertRaisesRegex(check_corpus.CorpusError, f"{first}: now passes every probe stage"):
                corpus_ratchet.check_pending(root)

    def test_a_recorded_stage_outside_the_pipeline_is_rejected(self) -> None:
        with self.temporary_repository() as temporary:
            root = pathlib.Path(temporary)
            self.rewrite_pending(root, lambda document: document["pending"][0]["blocker"].__setitem__("stage", "later"))
            with self.assertRaisesRegex(check_corpus.CorpusError, "malformed pending blocker"):
                check_corpus.validate_corpus(root)

    def test_probe_reports_pass_binding_blockers_before_source_stages(self) -> None:
        passthrough = {"passes": [{"name": "copy", "program": "p"}, {"name": "again", "program": "p"}], "params": {}}
        blocker = corpus_ratchet.probe_program("x/y:p", b"not glsl at all", passthrough)
        self.assertEqual("corpus.pass_binding", blocker["stage"])
        self.assertIn("bound by 2 authority passes (copy, again)", blocker["diagnostic"])
        scatter = {"passes": [{"name": "deposit", "program": "p", "drawMode": "points"}], "params": {}}
        self.assertIn("scatter pass", corpus_ratchet.probe_program("x/y:p", b"", scatter)["diagnostic"])
        defines = {"passes": [{"name": "d", "program": "p", "defines": {"A": 1}}], "params": {}}
        self.assertIn("pass-level defines", corpus_ratchet.probe_program("x/y:p", b"", defines)["diagnostic"])

    def test_derived_gates_follow_the_split(self) -> None:
        counts = check_corpus.validate_corpus()["counts"]
        self.assertEqual(counts["passes"] + counts["pending"], counts["authority_programs"])
        pending = corpus_census.pending()
        self.assertEqual(sorted(pending["effects"]),
                         sorted({item["effect_id"] for item in pending["pending"]}
                                - {entry["effect_id"] for entry in corpus_census.manifest_programs()}))


if __name__ == "__main__":
    unittest.main()
