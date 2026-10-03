"""Exercise kit coverage against the authority's current runtime catalog."""

import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ExportKitAuthorityCoverageTests(unittest.TestCase):
    def test_reintroduced_effect_is_required_despite_historical_exclusion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            kit = root / "export-kit"
            kit.mkdir()
            script = kit / "check-authority-coverage.mjs"
            script.write_bytes((ROOT / "export-kit/check-authority-coverage.mjs").read_bytes())
            (kit / "compat-effects.json").write_text('["synth/solid"]')
            authority = root / "authority"
            generated = authority / "src/effects/generated"
            generated.mkdir(parents=True)
            (authority / "package.json").write_text('{"type":"module"}')
            (generated / "upstream-snapshot.js").write_text(
                "export const sourceEffectIds = ['synth/solid', 'synth/scope'];\n"
                "export const excludedEffects = {reactive: ['synth/scope']};\n"
            )
            (authority / "src/effects/catalog.js").write_text(
                "export function createDefaultRegistry() { return {list() {"
                "return [{id: 'synth/solid'}, {id: 'synth/scope'}]}} }\n"
            )
            command = ["node", str(script), "--cpu-root", str(authority)]
            missing = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr)
            self.assertIn("authority renders 2 effects", missing.stdout)
            self.assertIn("synth/scope", missing.stdout)

            (kit / "compat-effects.json").write_text('["synth/solid", "synth/scope"]')
            complete = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(complete.returncode, 0, complete.stdout + complete.stderr)


if __name__ == "__main__":
    unittest.main()
