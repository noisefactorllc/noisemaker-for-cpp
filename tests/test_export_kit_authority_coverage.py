"""Exercise kit coverage against the authority's current runtime catalog."""

import json
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ExportKitAuthorityCoverageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = pathlib.Path(temporary.name)
        kit = root / "export-kit"
        kit.mkdir()
        script = kit / "check-authority-coverage.mjs"
        script.write_bytes((ROOT / "export-kit/check-authority-coverage.mjs").read_bytes())
        self.claims = kit / "compat-effects.json"
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
        self.command = ["node", str(script), "--cpu-root", str(authority)]

    def check(self, claims):
        self.claims.write_text(json.dumps(claims), encoding="utf-8")
        return subprocess.run(self.command, capture_output=True, text=True)

    def test_reintroduced_effect_is_required_despite_historical_exclusion(self):
        missing = self.check(["synth/solid"])
        self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr)
        self.assertIn("authority renders 2 effects", missing.stdout)
        self.assertIn("synth/scope", missing.stdout)

        complete = self.check(["synth/solid", "synth/scope"])
        self.assertEqual(complete.returncode, 0, complete.stdout + complete.stderr)

    def test_kit_must_not_claim_an_effect_the_authority_cannot_render(self):
        extra = self.check(["synth/solid", "synth/scope", "synth/notRendered"])
        self.assertEqual(extra.returncode, 1, extra.stdout + extra.stderr)
        self.assertIn("claimed but not rendered by the authority (1):", extra.stdout)
        self.assertIn("synth/notRendered", extra.stdout)


if __name__ == "__main__":
    unittest.main()
