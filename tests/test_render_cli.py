"""The user-facing `noisemaker-render` CLI contract.

These tests are about the experience of a person who has just cloned the
repository: does a bare `noisemaker-render program.dsl` render, is the refusal
readable, and — the load-bearing one — does the picture a user gets come out of
the *same* code path the parity harness validates. `test_render_cli_and_case_driver_agree_byte_for_byte`
is that proof: both binaries are driven over the same source with the same
options and their raw frames and metadata documents must be byte-identical.

Both binaries are built externally, so they arrive by env:

    NOISEMAKER_RENDER_CLI       built noisemaker-render binary
    NOISEMAKER_DSL_CPU_CASE     built noisemaker-dsl-cpu-case driver
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tools.benchmark.corpus_lane import resolve_driver


ROOT = pathlib.Path(__file__).resolve().parents[1]
BLUR = ROOT / "tests/fixtures/dsl/blur.dsl"
GENERATED_CATALOG = ROOT / "src/effects/generated/effect_catalog.cpp"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# A program the executor refuses: `filter/snow:snow` is on the measured parity
# exclusion list in src/graph/executor.cpp, so it compiles and then refuses.
REFUSED_PROGRAM = "search synth, filter\nsolid(color: #3a7).snow().write(o0)\nrender(o0)\n"


def catalog_row_count() -> int:
    """Derive the catalog row count from the generated catalog, never a literal."""
    source = GENERATED_CATALOG.read_text(encoding="utf-8")
    declared = re.search(r"counts\.definitions = (\d+);", source)
    assert declared is not None, "the generated catalog no longer declares its definition count"
    rows = len(re.findall(r'^  e\.id = "', source, flags=re.MULTILINE))
    assert rows == int(declared.group(1)), (
        f"the generated catalog declares {declared.group(1)} definitions but emits {rows}"
    )
    return rows


def png_dimensions(png: bytes) -> tuple[int, int]:
    assert png[:8] == PNG_MAGIC
    assert png[12:16] == b"IHDR"
    return struct.unpack(">II", png[16:24])


class RenderCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cli = resolve_driver("NOISEMAKER_RENDER_CLI", "noisemaker-render build")

    def run_cli(self, *args: str, cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.cli), *args], cwd=str(cwd) if cwd else None, text=True, capture_output=True
        )

    # ------------------------------------------------------------------
    # Discoverability: the two things a newcomer needs before anything else.
    # ------------------------------------------------------------------
    def test_help_documents_every_option_the_binary_accepts(self) -> None:
        result = self.run_cli("--help")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("noisemaker-render", result.stdout)
        for flag in ("--output", "--width", "--height", "--time", "--frame", "--seed",
                     "--raw-rgba8", "--metadata", "--list-effects"):
            self.assertIn(flag, result.stdout, f"{flag} is undocumented")
        self.assertIn("No environment variables are needed", result.stdout)

    def test_no_source_digest_flag_exists_anywhere_in_the_user_surface(self) -> None:
        """Input authentication is a harness concern; it must not reach a user."""
        help_text = self.run_cli("--help").stdout
        self.assertNotIn("sha256", help_text.lower())
        rejected = self.run_cli(str(BLUR), "--source-sha256", "0" * 64)
        self.assertEqual(2, rejected.returncode)
        self.assertIn("--source-sha256", rejected.stderr)

    def test_list_effects_prints_every_catalog_key_sorted(self) -> None:
        result = self.run_cli("--list-effects")
        self.assertEqual(0, result.returncode, result.stderr)
        keys = result.stdout.splitlines()
        self.assertEqual(catalog_row_count(), len(keys))
        self.assertEqual(sorted(keys), keys)
        self.assertEqual(len(set(keys)), len(keys))
        self.assertIn("filter/blur", keys)

    # ------------------------------------------------------------------
    # Rendering: defaults, explicit options, determinism.
    # ------------------------------------------------------------------
    def test_bare_invocation_writes_the_program_basename_as_png_at_512(self) -> None:
        with tempfile.TemporaryDirectory(prefix="noisemaker-render-default-") as directory:
            work = pathlib.Path(directory)
            (work / "blur.dsl").write_bytes(BLUR.read_bytes())
            # Deliberately relative: a user should never have to spell an absolute path.
            result = self.run_cli("blur.dsl", cwd=work)
            self.assertEqual(0, result.returncode, result.stderr)
            png = (work / "blur.png").read_bytes()
            self.assertEqual(PNG_MAGIC, png[:8])
            self.assertEqual((512, 512), png_dimensions(png))

    def test_explicit_options_are_honoured_and_the_render_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory(prefix="noisemaker-render-explicit-") as directory:
            work = pathlib.Path(directory)
            (work / "blur.dsl").write_bytes(BLUR.read_bytes())
            renders = []
            for index in (1, 2):
                out = work / f"run-{index}.png"
                result = self.run_cli(
                    "blur.dsl", "-o", out.name, "--width", "64", "--height", "64",
                    "--seed", "7", "--time", "0.5", "--frame", "3", cwd=work,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                renders.append(out.read_bytes())
            self.assertEqual((64, 64), png_dimensions(renders[0]))
            # Byte-for-byte, not "visually identical".
            self.assertEqual(renders[0], renders[1])

    def test_machine_readable_outputs_describe_the_frame_that_was_written(self) -> None:
        with tempfile.TemporaryDirectory(prefix="noisemaker-render-machine-") as directory:
            work = pathlib.Path(directory)
            (work / "blur.dsl").write_bytes(BLUR.read_bytes())
            result = self.run_cli(
                "blur.dsl", "--width", "64", "--height", "64",
                "--raw-rgba8", "frame.rgba8", "--metadata", "frame.json", cwd=work,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            raw = (work / "frame.rgba8").read_bytes()
            metadata = json.loads((work / "frame.json").read_text(encoding="utf-8"))
            self.assertEqual("noisemaker-cpp.dsl-cpu-run.v1", metadata["schema"])
            self.assertEqual("rendered", metadata["status"])
            self.assertEqual("top-down", metadata["orientation"])
            self.assertEqual(64 * 64 * 4, metadata["byteLength"])
            self.assertEqual(len(raw), metadata["byteLength"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), metadata["rgba8Sha256"])
            self.assertEqual(
                hashlib.sha256((work / "blur.dsl").read_bytes()).hexdigest(),
                metadata["sourceSha256"],
            )

    # ------------------------------------------------------------------
    # The one-code-path proof.
    # ------------------------------------------------------------------
    def test_render_cli_and_case_driver_agree_byte_for_byte(self) -> None:
        driver = resolve_driver("NOISEMAKER_DSL_CPU_CASE", "noisemaker-dsl-cpu-case")
        with tempfile.TemporaryDirectory(prefix="noisemaker-render-parity-") as directory:
            work = pathlib.Path(directory)
            source = work / "blur.dsl"
            source.write_bytes(BLUR.read_bytes())
            digest = hashlib.sha256(source.read_bytes()).hexdigest()

            cli = self.run_cli(
                "blur.dsl", "--width", "64", "--height", "64", "--seed", "7",
                "--time", "0.5", "--frame", "3", "-o", "cli.png",
                "--raw-rgba8", "cli.rgba8", "--metadata", "cli.json", cwd=work,
            )
            self.assertEqual(0, cli.returncode, cli.stderr)

            harness = subprocess.run(
                [str(driver), "--source-file", str(source), "--source-sha256", digest,
                 "--width", "64", "--height", "64", "--time", "0.5", "--frame", "3",
                 "--seed", "7", "--rgba8-output", str(work / "harness.rgba8"),
                 "--metadata-output", str(work / "harness.json")],
                text=True, capture_output=True,
            )
            self.assertEqual(0, harness.returncode, harness.stderr)

            self.assertEqual(
                (work / "harness.rgba8").read_bytes(), (work / "cli.rgba8").read_bytes()
            )
            self.assertEqual(
                (work / "harness.json").read_bytes(), (work / "cli.json").read_bytes()
            )

    # ------------------------------------------------------------------
    # Fail-closed.
    # ------------------------------------------------------------------
    def test_a_refused_program_exits_nonzero_and_carries_the_executor_reason(self) -> None:
        with tempfile.TemporaryDirectory(prefix="noisemaker-render-refusal-") as directory:
            work = pathlib.Path(directory)
            (work / "refused.dsl").write_text(REFUSED_PROGRAM, encoding="utf-8")
            result = self.run_cli("refused.dsl", "--width", "32", "--height", "32", cwd=work)
            self.assertNotEqual(0, result.returncode)
            self.assertEqual(4, result.returncode)
            # The exact reason string the executor produced, not a paraphrase.
            executor = (ROOT / "src/graph/executor.cpp").read_text(encoding="utf-8")
            self.assertIn("measured divergent", executor)
            self.assertIn(
                "the authority executes a hand-written CPU adapter for this program",
                result.stderr,
            )
            self.assertIn("unavailable_pass", result.stderr)
            self.assertIn("filter/snow:snow", result.stderr)
            self.assertEqual("", result.stdout)
            # Fail-closed means no half-written picture is left behind.
            self.assertFalse((work / "refused.png").exists())

    def test_an_unparseable_program_refuses_instead_of_rendering_something(self) -> None:
        with tempfile.TemporaryDirectory(prefix="noisemaker-render-broken-") as directory:
            work = pathlib.Path(directory)
            (work / "broken.dsl").write_text("search synth\nsolid(\n", encoding="utf-8")
            result = self.run_cli("broken.dsl", cwd=work)
            self.assertEqual(4, result.returncode)
            self.assertIn("broken.dsl", result.stderr)
            self.assertFalse((work / "broken.png").exists())

    def test_command_line_mistakes_report_usage_rather_than_a_stack_trace(self) -> None:
        for args, needle in (
            ((), "name a DSL program"),
            (("missing.dsl",), "cannot read the program file"),
            ((str(BLUR), "--nope"), 'unknown option "--nope"'),
            ((str(BLUR), "--width", "wide"), "--width needs a number"),
            ((str(BLUR), "--width", "0"), "at least 1"),
            ((str(BLUR), "--frame", "-1"), "at least 0"),
            ((str(BLUR), str(BLUR)), "only one program"),
        ):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn(needle, result.stderr)
                self.assertIn("--help", result.stderr)


if __name__ == "__main__":
    unittest.main()
