"""A refusal record must be JSON for every refusal text the drivers can emit.

MAJOR-2 of the 2026-08-29 publication review: ``refusal_record`` interpolated
``GraphError::detail()``, ``GraphError::program_key()`` and
``std::exception::what()`` directly between quote characters while the adjacent
``schema`` field went through the owned escaper. The DSL frontend embeds literal
``"`` in its messages as a matter of course -- ``src/dsl/parser.cpp`` builds
``Expected "<lexeme>"`` and ``src/dsl/lexer.cpp`` builds
``Unexpected character "<char>"`` -- and a refusal is a first-class recorded
outcome, so that text reaches the record verbatim. The corpus lane reads the
record with ``json.loads`` (``tests/test_dsl_corpus_parity.py``), so the defect
turned a structured refusal into an unparseable blob for a whole class of
programs.

These cases run the real driver over the review's own reproductions and require
the emitted record to parse and to carry the quoted text back intact.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import tempfile
import unittest

from tools.benchmark.corpus_lane import resolve_driver

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS_CASE = ROOT / "tools/benchmark/corpus_case.cpp"

RUN_SCHEMA = "noisemaker-cpp.dsl-cpu-run.v1"
EXIT_REFUSED = 4

# Each program refuses in the DSL frontend with a message that embeds a literal
# double quote, which is exactly the byte the record has to escape.
QUOTED_REFUSALS = {
    "parser-expected-token": ("let a = solid(1 2)\n", 'Expected ")"'),
    "lexer-unexpected-brace": ("solid{\n", 'Unexpected character "{"'),
    "lexer-unexpected-tilde": ("let a = solid(); ~\n", 'Unexpected character "~"'),
}


class RefusalRecordJsonTest(unittest.TestCase):
    def _refuse(self, driver: pathlib.Path, source_text: str) -> tuple[int, str]:
        # The driver requires absolute output paths that resolve outside the
        # checkout, so the whole case lives in a temporary directory.
        with tempfile.TemporaryDirectory(prefix="noisemaker-refusal-json-") as directory:
            scratch = pathlib.Path(directory).resolve()
            source = scratch / "case.dsl"
            source.write_text(source_text, encoding="utf-8")
            digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
            completed = subprocess.run(
                [str(driver),
                 "--source-file", str(source),
                 "--source-sha256", digest,
                 "--width", "4", "--height", "4",
                 "--time", "0.0", "--frame", "0", "--seed", "1.0",
                 "--rgba8-output", str(scratch / "case.rgba8"),
                 "--metadata-output", str(scratch / "case.json"),
                 "--repo-root", str(ROOT)],
                capture_output=True, text=True)
            return completed.returncode, completed.stdout

    def test_a_refusal_whose_text_contains_a_quote_is_still_json(self) -> None:
        driver = resolve_driver("NOISEMAKER_DSL_CPU_CASE", "noisemaker-dsl-cpu-case")
        for name, (source_text, expected_fragment) in QUOTED_REFUSALS.items():
            with self.subTest(case=name):
                code, stdout = self._refuse(driver, source_text)
                self.assertEqual(code, EXIT_REFUSED, stdout)
                # json.loads is the assertion: an unescaped quote terminates the
                # `detail` string early and the parse fails outright.
                record = json.loads(stdout)
                self.assertEqual(record["schema"], RUN_SCHEMA)
                self.assertEqual(record["status"], "refused")
                self.assertEqual(record["code"], "exception")
                # Escaping must be reversible, not lossy: the parsed text is the
                # driver's own message, quotes and all.
                self.assertIn('"', expected_fragment)
                self.assertTrue(record["detail"].endswith(expected_fragment),
                                record["detail"])

    def test_every_interpolated_error_string_goes_through_the_owned_escaper(self) -> None:
        # Both overloads, and every error-derived field in them, must be built
        # with `json_string`. A behavioural case can only reach the fields a DSL
        # program can refuse on; this holds the contract for the rest.
        source = CORPUS_CASE.read_text(encoding="utf-8")
        for expression in ('json_string(error.detail())',
                           'json_string(error.program_key())',
                           'json_string(error.what())'):
            self.assertIn(expression, source)


if __name__ == "__main__":
    unittest.main()
