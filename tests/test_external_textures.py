"""External textures for filter/text and synth/media through noisemaker-render.

`noisemaker-render --input FILE` and `--texture NAME=FILE` bind PNGs as the
`imageTex` (synth/media) and `textTex` (filter/text) routes the same way the
JS CLI's `--input`/`--texture` do (bin/noisemaker-cpu.js). The frozen
`rgba8Sha256` values in `tests/fixtures/external-textures/cases.json` were
captured from the JS CPU authority by
`tests/fixtures/external-textures/compare_with_js_authority.py` -- run that
script directly (it needs node and a checkout of the JS authority) for a
live, byte-for-byte proof against the authority; re-run it with --capture
after touching a fixture PNG or a .dsl program here.

This module needs neither: it drives only the built `noisemaker-render`
binary and checks its raw RGBA8 output against those frozen hashes, so it
runs under plain ctest with no external dependency.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tools.benchmark.corpus_lane import resolve_driver

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/external-textures"
CASES = json.loads((FIXTURES / "cases.json").read_text(encoding="utf-8"))["cases"]


def texture_args(case: dict) -> list[str]:
    args: list[str] = []
    if case.get("input"):
        args += ["--input", str(FIXTURES / case["input"])]
    for assignment in case.get("textures", []):
        name, _, filename = assignment.partition("=")
        args += ["--texture", f"{name}={FIXTURES / filename}"]
    return args


class ExternalTextureCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cli = resolve_driver("NOISEMAKER_RENDER_CLI", "noisemaker-render build")

    def render_raw(self, case: dict, work: pathlib.Path) -> bytes:
        raw = work / f"{case['name']}.rgba8"
        args = [
            str(self.cli), str(FIXTURES / case["dsl"]),
            "--width", str(case["width"]), "--height", str(case["height"]),
            *texture_args(case), "--raw-rgba8", str(raw),
            "-o", str(work / f"{case['name']}.png"),
        ]
        result = subprocess.run(args, text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        return raw.read_bytes()

    def test_every_case_matches_its_frozen_js_authority_hash(self) -> None:
        with tempfile.TemporaryDirectory(prefix="external-textures-cli-") as directory:
            work = pathlib.Path(directory)
            for case in CASES:
                with self.subTest(case=case["name"]):
                    raw = self.render_raw(case, work)
                    digest = hashlib.sha256(raw).hexdigest()
                    self.assertEqual(
                        case["rgba8Sha256"], digest,
                        f"{case['name']}: raw RGBA8 no longer matches the hash frozen from "
                        "the JS CPU authority; re-run "
                        "tests/fixtures/external-textures/compare_with_js_authority.py",
                    )

    def test_render_is_reproducible_for_an_external_texture_case(self) -> None:
        case = CASES[0]
        with tempfile.TemporaryDirectory(prefix="external-textures-repro-") as directory:
            work = pathlib.Path(directory)
            first = self.render_raw(case, work)
            second = self.render_raw(case, work)
            self.assertEqual(first, second)

    def test_texture_naming_a_route_overrides_the_input_binding(self) -> None:
        # filter-text-override binds --input mask-16x16.png (imageTex+textTex)
        # then --texture textTex=overlay-37x53.png, which must win for
        # textTex specifically -- exactly the case cases.json records.
        case = next(c for c in CASES if c["name"] == "filter-text-override")
        self.assertEqual(["textTex=overlay-37x53.png"], case["textures"])
        self.assertEqual("mask-16x16.png", case["input"])
        with tempfile.TemporaryDirectory(prefix="external-textures-override-") as directory:
            work = pathlib.Path(directory)
            overridden = hashlib.sha256(self.render_raw(case, work)).hexdigest()
            self.assertEqual(case["rgba8Sha256"], overridden)
            # Rendering with --input alone (mask bound as textTex too) must
            # differ: the override is doing real work, not a no-op.
            mask_only = dict(case)
            mask_only["name"] = "filter-text-override-mask-only"
            mask_only["textures"] = []
            without_override = hashlib.sha256(self.render_raw(mask_only, work)).hexdigest()
            self.assertNotEqual(overridden, without_override)


if __name__ == "__main__":
    unittest.main()
