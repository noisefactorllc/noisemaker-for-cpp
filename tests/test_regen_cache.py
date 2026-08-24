"""The historical-reconstruction memo (``tools/glslcpp/regen_cache.py``).

A cache that can serve wrong bytes is worse than no cache: it turns a real
regression into a green suite. Most of what follows is therefore about the
guards, not the speed. Each guard is exercised in the failing direction --
the cache is made to *want* to serve a stale entry and required to refuse.

Only one test pays for a real regeneration (~29 s); the rest drive the
cache's own logic with cheap synthetic payloads.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from tools.glslcpp import generate_typed_slice, regen_cache  # noqa: E402

ENV = "NOISEMAKER_REGEN_CACHE"


class _CacheTempDir:
    """A cache root outside the repository, with the env var set."""

    def __enter__(self):
        self._previous = os.environ.get(ENV)
        self._temporary = tempfile.TemporaryDirectory()
        os.environ[ENV] = self._temporary.name
        return pathlib.Path(self._temporary.name)

    def __exit__(self, *exc):
        if self._previous is None:
            os.environ.pop(ENV, None)
        else:
            os.environ[ENV] = self._previous
        self._temporary.cleanup()
        return False


class OffByDefaultTests(unittest.TestCase):
    """The default must be the old behaviour, exactly."""

    def test_unset_env_disables_the_cache_entirely(self) -> None:
        previous = os.environ.pop(ENV, None)
        try:
            self.assertIsNone(regen_cache.cache_root())
        finally:
            if previous is not None:
                os.environ[ENV] = previous

    def test_empty_env_is_treated_as_unset(self) -> None:
        previous = os.environ.get(ENV)
        os.environ[ENV] = ""
        try:
            self.assertIsNone(regen_cache.cache_root())
        finally:
            if previous is None:
                os.environ.pop(ENV, None)
            else:
                os.environ[ENV] = previous

    def test_the_installed_wrapper_is_transparent_when_off(self) -> None:
        # The generator's public callable is wrapped, and the wrapper keeps a
        # handle on the original so an audit can bypass it.
        self.assertTrue(
            getattr(generate_typed_slice.generate_outputs, "_regen_cached", False))
        self.assertTrue(
            callable(generate_typed_slice.generate_outputs._uncached))

    def test_installing_twice_does_not_double_wrap(self) -> None:
        first = generate_typed_slice.generate_outputs
        again = regen_cache.install(generate_typed_slice)
        self.assertIs(first, again)
        self.assertIs(first._uncached, again._uncached)


class ContainmentTests(unittest.TestCase):
    """Caches, like builds, never live in the tree."""

    def test_a_cache_root_inside_the_repository_is_refused(self) -> None:
        previous = os.environ.get(ENV)
        os.environ[ENV] = str(REPOSITORY / "scratch-cache")
        try:
            with self.assertRaises(regen_cache.RegenCacheError):
                regen_cache.cache_root()
        finally:
            if previous is None:
                os.environ.pop(ENV, None)
            else:
                os.environ[ENV] = previous
            # `cache_root` mkdirs before validating; leave nothing behind.
            stray = REPOSITORY / "scratch-cache"
            if stray.is_dir():
                stray.rmdir()

    def test_the_repository_itself_is_refused(self) -> None:
        previous = os.environ.get(ENV)
        os.environ[ENV] = str(REPOSITORY)
        try:
            with self.assertRaises(regen_cache.RegenCacheError):
                regen_cache.cache_root()
        finally:
            if previous is None:
                os.environ.pop(ENV, None)
            else:
                os.environ[ENV] = previous


class KeyTests(unittest.TestCase):
    """What the key covers, proved by making each input change it."""

    def setUp(self) -> None:
        regen_cache._SOURCE_FINGERPRINT = None

    def tearDown(self) -> None:
        regen_cache._SOURCE_FINGERPRINT = None

    def test_an_emitter_edit_changes_the_source_fingerprint(self) -> None:
        """THE load-bearing guard. Without it a cache would serve pre-fix
        bytes after an emitter fix -- and the 2026-08-19 alias fix moved 42
        frozen pins, every one of which would have stayed green."""
        before = regen_cache.source_fingerprint()
        victim = REPOSITORY / "tools/glslcpp/emit_typed_cpp.py"
        original = victim.read_bytes()
        try:
            victim.write_bytes(original + b"\n# probe\n")
            regen_cache._SOURCE_FINGERPRINT = None
            self.assertNotEqual(before, regen_cache.source_fingerprint())
        finally:
            victim.write_bytes(original)
            regen_cache._SOURCE_FINGERPRINT = None
        self.assertEqual(before, regen_cache.source_fingerprint())

    def test_a_frontend_profile_edit_also_changes_it(self) -> None:
        """Not just the two authorities: any frontend record is an input."""
        before = regen_cache.source_fingerprint()
        victim = REPOSITORY / "tools/glslcpp/frontend/varying_uv_profile.py"
        original = victim.read_bytes()
        try:
            victim.write_bytes(original + b"\n# probe\n")
            regen_cache._SOURCE_FINGERPRINT = None
            self.assertNotEqual(before, regen_cache.source_fingerprint())
        finally:
            victim.write_bytes(original)
            regen_cache._SOURCE_FINGERPRINT = None

    def test_bytecode_directories_are_excluded_from_the_fingerprint(self) -> None:
        """Otherwise the key churns whenever the interpreter writes bytecode,
        and the cache never hits. Proved by planting one and requiring the
        fingerprint to hold still."""
        before = regen_cache.source_fingerprint()
        planted = REPOSITORY / "tools/glslcpp/__pycache__/regen_probe.cpython-99.py"
        planted.parent.mkdir(parents=True, exist_ok=True)
        try:
            planted.write_text("# planted bytecode-adjacent source\n")
            regen_cache._SOURCE_FINGERPRINT = None
            self.assertEqual(before, regen_cache.source_fingerprint())
        finally:
            planted.unlink(missing_ok=True)
            regen_cache._SOURCE_FINGERPRINT = None

    def test_removing_one_row_changes_the_spec_fingerprint(self) -> None:
        spec = generate_typed_slice.load_slice(REPOSITORY)
        projection = copy.deepcopy(spec)
        projection["programs"] = projection["programs"][:-1]
        self.assertNotEqual(regen_cache.spec_fingerprint(spec),
                            regen_cache.spec_fingerprint(projection))

    def test_key_ordering_is_irrelevant_but_content_is_not(self) -> None:
        spec = generate_typed_slice.load_slice(REPOSITORY)
        reordered = json.loads(json.dumps(spec))  # same content, fresh dict
        self.assertEqual(regen_cache.spec_fingerprint(spec),
                         regen_cache.spec_fingerprint(reordered))
        mutated = copy.deepcopy(spec)
        mutated["programs"][0] = dict(mutated["programs"][0])
        mutated["programs"][0]["defines"] = {"PROBE": 1}
        self.assertNotEqual(regen_cache.spec_fingerprint(spec),
                            regen_cache.spec_fingerprint(mutated))

    def test_the_entry_key_combines_both_inputs(self) -> None:
        spec = generate_typed_slice.load_slice(REPOSITORY)
        expected = hashlib.sha256(
            f"{regen_cache.source_fingerprint()}:"
            f"{regen_cache.spec_fingerprint(spec)}".encode()).hexdigest()
        self.assertEqual(expected, regen_cache.entry_key(spec))


class StoreAndLoadTests(unittest.TestCase):
    """Round-tripping, and the ways a half-written entry could be served."""

    PAYLOAD = {"src/typed_generated/typed_slice.cpp": b"// bytes\n",
               "src/typed_generated/typed_manifest.json": b"{}\n"}

    def test_round_trip_is_byte_exact(self) -> None:
        with _CacheTempDir() as root:
            regen_cache.store(root, "a" * 64, self.PAYLOAD, {"programs": []})
            self.assertEqual(self.PAYLOAD, regen_cache.load(root, "a" * 64))

    def test_a_missing_entry_is_a_miss_not_an_error(self) -> None:
        with _CacheTempDir() as root:
            self.assertIsNone(regen_cache.load(root, "b" * 64))

    def test_a_missing_blob_makes_the_entry_a_miss(self) -> None:
        """A truncated entry must never be served as a partial hit."""
        with _CacheTempDir() as root:
            regen_cache.store(root, "c" * 64, self.PAYLOAD, {"programs": []})
            directory = regen_cache._entry_dir(root, "c" * 64)
            blobs = [p for p in directory.iterdir()
                     if p.name not in {"index.json", "spec.json"}]
            self.assertTrue(blobs)
            blobs[0].unlink()
            self.assertIsNone(regen_cache.load(root, "c" * 64))

    def test_a_corrupt_index_makes_the_entry_a_miss(self) -> None:
        with _CacheTempDir() as root:
            regen_cache.store(root, "d" * 64, self.PAYLOAD, {"programs": []})
            (regen_cache._entry_dir(root, "d" * 64) / "index.json").write_text("{")
            self.assertIsNone(regen_cache.load(root, "d" * 64))

    def test_no_partial_files_survive_a_completed_store(self) -> None:
        with _CacheTempDir() as root:
            regen_cache.store(root, "e" * 64, self.PAYLOAD, {"programs": []})
            leftovers = list(regen_cache._entry_dir(root, "e" * 64)
                             .glob("*.partial"))
            self.assertEqual([], leftovers)

    def test_the_spec_is_stored_so_the_entry_can_be_audited(self) -> None:
        with _CacheTempDir() as root:
            regen_cache.store(root, "f" * 64, self.PAYLOAD, {"programs": [1]})
            spec_path = regen_cache._entry_dir(root, "f" * 64) / "spec.json"
            self.assertTrue(spec_path.is_file())
            self.assertEqual({"programs": [1]},
                             json.loads(spec_path.read_text()))


class RuntimeSourceDriftTests(unittest.TestCase):
    """A long-lived process must not cache with code loaded before an edit."""

    def test_source_edit_after_import_bypasses_read_and_write(self) -> None:
        class FakeGenerator:
            _ROOT = REPOSITORY

            def __init__(self) -> None:
                self.payload = b"before-edit"

            def load_slice(self, _repository):
                return {"programs": []}

            def generate_outputs(self, _repository=None):
                return {"artifact": self.payload}

        fake = FakeGenerator()
        with _CacheTempDir(), \
                mock.patch.object(regen_cache, "_import_collaborators"), \
                mock.patch.object(regen_cache, "_callable_snapshot",
                                  return_value={}), \
                mock.patch.object(regen_cache, "_fresh_source_fingerprint",
                                  return_value="loaded-source") as fresh:
            wrapped = regen_cache.install(fake)
            self.assertEqual(b"before-edit", wrapped(REPOSITORY)["artifact"])
            fake.payload = b"after-edit"
            fresh.return_value = "edited-on-disk"
            self.assertEqual(b"after-edit", wrapped(REPOSITORY)["artifact"])
            self.assertEqual(1, wrapped.source_drift_bypassed)


class EquivalenceTests(unittest.TestCase):
    """The only claim that ultimately matters: a hit equals the real thing.

    This is the one test that pays for a real regeneration.
    """

    def test_a_hit_is_byte_identical_to_an_uncached_regeneration(self) -> None:
        uncached = generate_typed_slice.generate_outputs._uncached
        spec = generate_typed_slice.load_slice(REPOSITORY)
        projection = copy.deepcopy(spec)
        projection["programs"] = [row for row in projection["programs"]
                                  if row["program_key"] != "filter/wobble:wobble"]
        with _CacheTempDir():
            with mock.patch.object(generate_typed_slice, "load_slice",
                                   return_value=projection):
                miss = generate_typed_slice.generate_outputs(REPOSITORY)
                hit = generate_typed_slice.generate_outputs(REPOSITORY)
                truth = uncached(REPOSITORY)
        self.assertEqual(set(truth), set(miss))
        for name in truth:
            self.assertEqual(truth[name], miss[name], f"{name}: miss differs")
            self.assertEqual(truth[name], hit[name], f"{name}: hit differs")

    def test_two_different_projections_do_not_share_an_entry(self) -> None:
        """The failure this rules out: one projection served for another."""
        spec = generate_typed_slice.load_slice(REPOSITORY)
        first = copy.deepcopy(spec)
        first["programs"] = [r for r in first["programs"]
                             if r["program_key"] != "filter/wobble:wobble"]
        second = copy.deepcopy(spec)
        second["programs"] = [r for r in second["programs"]
                              if r["program_key"] != "filter/parallax:parallax"]
        self.assertNotEqual(regen_cache.entry_key(first),
                            regen_cache.entry_key(second))


if __name__ == "__main__":
    unittest.main()


class ForgedProgramBypassTests(unittest.TestCase):
    """The hole the suite found on this cache's first run.

    Several tests forge a program by patching a collaborator and require
    `generate_outputs` to RAISE. The spec is untouched, so a spec-keyed memo
    would hand back the good bytes and the guard would never fire. The cache
    must stand down instead.
    """

    def test_a_patched_collaborator_is_detected(self) -> None:
        self.assertFalse(regen_cache._collaborators_are_patched(generate_typed_slice))
        with mock.patch.object(generate_typed_slice, "validate_capabilities"):
            self.assertTrue(
                regen_cache._collaborators_are_patched(generate_typed_slice))
        self.assertFalse(regen_cache._collaborators_are_patched(generate_typed_slice))

    def test_every_collaborator_the_suite_forges_is_detected(self) -> None:
        """The guard scans the namespace rather than a list of names. A list
        was tried first and missed `apply_smooth_edge_luma_weights` -- one of
        an `apply_*` family that grows with every carrier. These are the
        names the suite actually patches, plus one from that family."""
        for name in ("analyze_program", "validate_capabilities",
                     "render_typed_cpp", "apply_smooth_edge_luma_weights"):
            if not hasattr(generate_typed_slice, name):
                continue
            with self.subTest(collaborator=name):
                with mock.patch.object(generate_typed_slice, name):
                    self.assertTrue(
                        regen_cache._collaborators_are_patched(generate_typed_slice),
                        f"{name} is patched but the cache would still serve")
        for owner, name in (("check_corpus", "validate_corpus"),
                            ("check_semantics", "semantic_report")):
            target = getattr(generate_typed_slice, owner, None)
            if target is None or not hasattr(target, name):
                continue
            with self.subTest(collaborator=f"{owner}.{name}"):
                with mock.patch.object(target, name):
                    self.assertTrue(
                        regen_cache._collaborators_are_patched(generate_typed_slice))

    def test_a_patched_class_attribute_is_detected(self) -> None:
        """The second hole, and the one that cost three RED tests.

        `emit_typed_cpp._Emitter` is reached through a `from ... import`
        binding, so the emitter module is not an attribute of the generator
        and a module-level-only scan never saw it. Worse, the alias suite
        patches *methods* on that class, which a module-level scan could not
        see even if it had the module. The memo served pre-patch bytes and
        three neutralization tests -- whose whole job is to go RED -- came
        back green under the cache and red without it.

        The snapshot now walks every module under `tools.glslcpp` and every
        class inside them, so both shapes are covered.
        """
        from tools.glslcpp import emit_typed_cpp

        self.assertFalse(regen_cache._collaborators_are_patched(generate_typed_slice))
        for method in ("_collect_pooled_vector_aliases", "__post_init__"):
            with self.subTest(method=method):
                with mock.patch.object(emit_typed_cpp._Emitter, method,
                                       lambda self, *a, **k: None):
                    self.assertTrue(
                        regen_cache._collaborators_are_patched(generate_typed_slice),
                        f"_Emitter.{method} is patched but the cache would "
                        f"still serve")
        self.assertFalse(regen_cache._collaborators_are_patched(generate_typed_slice))

    def test_the_baseline_covers_the_whole_package_not_what_happened_to_load(
            self) -> None:
        """A collaborator imported after the snapshot would never be compared.

        It cannot be snapshot on first sight either: `mock.patch` imports its
        target before patching it, so first sight is already the patched
        value. `install` therefore imports the package up front, and this
        pins that the baseline really does span it.
        """
        baseline = generate_typed_slice._regen_cache_baseline
        owners = {owner for owner, _ in baseline if owner is not None}
        modules = {name for name in owners if name in sys.modules}
        self.assertIn("tools.glslcpp.emit_typed_cpp", modules)
        self.assertIn("tools.glslcpp.frontend.varying_uv_profile", modules)
        self.assertIn(("tools.glslcpp.emit_typed_cpp._Emitter",
                       "_collect_pooled_vector_aliases"), baseline)
        # And nothing under the package is missing from the recorded set.
        recorded = generate_typed_slice._regen_cache_baseline_modules
        self.assertLessEqual(set(regen_cache._collaborator_modules()),
                             set(recorded))

    def test_patching_with_a_plain_lambda_is_detected(self) -> None:
        """The hole that showed up as a FLAKY test.

        `mock.patch.object(target, name, a_lambda)` installs the lambda
        itself -- no Mock object ever exists -- so a type-sniffing guard
        misses it, and whether the test passed depended on whether an
        earlier test had already populated the entry. Identity against the
        import-time snapshot catches it.
        """
        self.assertFalse(regen_cache._collaborators_are_patched(generate_typed_slice))
        with mock.patch.object(generate_typed_slice,
                               "apply_const_global_tables",
                               lambda program, *a, **k: program):
            self.assertTrue(
                regen_cache._collaborators_are_patched(generate_typed_slice))
        self.assertFalse(regen_cache._collaborators_are_patched(generate_typed_slice))

    def test_the_guard_compares_identity_not_type(self) -> None:
        """Replacing a collaborator with an identical-looking function is
        still a replacement."""
        original = generate_typed_slice.validate_capabilities
        twin = lambda *a, **k: original(*a, **k)  # noqa: E731
        with mock.patch.object(generate_typed_slice,
                               "validate_capabilities", twin):
            self.assertTrue(
                regen_cache._collaborators_are_patched(generate_typed_slice))

    def test_the_snapshot_excludes_load_slice_and_non_callables(self) -> None:
        baseline = generate_typed_slice._regen_cache_baseline
        self.assertNotIn((None, "load_slice"), baseline)
        self.assertTrue(baseline, "the snapshot must not be empty")
        for (_owner, _name), value in baseline.items():
            self.assertTrue(callable(value))

    def test_patching_load_slice_alone_does_NOT_bypass(self) -> None:
        """Projections are the cache's whole purpose; they must still hit."""
        spec = generate_typed_slice.load_slice(REPOSITORY)
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=spec):
            self.assertFalse(
                regen_cache._collaborators_are_patched(generate_typed_slice))

    def test_a_forged_program_still_raises_with_the_cache_warm(self) -> None:
        """End to end: warm the cache on the live spec, then forge and
        require the generator's guard to fire anyway."""
        with _CacheTempDir():
            generate_typed_slice.generate_outputs(REPOSITORY)   # warm
            self.assertGreaterEqual(generate_typed_slice.generate_outputs.misses, 1)

            def refuse(*args, **kwargs):
                raise generate_typed_slice.GeneratorError("forged")

            with mock.patch.object(generate_typed_slice,
                                   "validate_capabilities", side_effect=refuse):
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.generate_outputs(REPOSITORY)


class AuditTests(unittest.TestCase):
    """The audit reports, it never crashes.

    A real audit found a poisoned entry -- one stored during a run with a
    forged collaborator, before the bypass guard existed -- and the first
    version of `verify_all` died on it instead of reporting it. An audit that
    aborts on the first bad entry cannot tell you how many others there are.
    """

    def test_an_unverifiable_entry_is_reported_not_raised(self) -> None:
        with _CacheTempDir() as root:
            # A spec that cannot possibly regenerate: the audit must survive it.
            regen_cache.store(root, "9" * 64,
                              {"src/typed_generated/typed_slice.cpp": b"x"},
                              {"programs": [{"program_key": "nope:nope",
                                             "defines": {}}]})
            code = regen_cache.verify_all()
        self.assertEqual(1, code, "a poisoned entry must fail the audit")

    def test_an_entry_without_a_stored_spec_is_unverifiable_not_passing(self) -> None:
        with _CacheTempDir() as root:
            regen_cache.store(root, "8" * 64,
                              {"src/typed_generated/typed_slice.cpp": b"x"})
            self.assertFalse((regen_cache._entry_dir(root, "8" * 64)
                              / "spec.json").exists())
            # Counted as unverifiable, which is not the same as verified.
            self.assertEqual(0, regen_cache.verify_all())
