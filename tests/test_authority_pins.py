import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
READER = Path('scripts/authority-pins')
PARITY = Path('scripts/parity-summary')
GENERATOR = Path('tools/dsl/generate_backend_compatibility.py')
CHECK_CORPUS = Path('tools/glslcpp/check_corpus.py')
COMPATIBILITY = Path('src/effects/generated/backend_compatibility.json')
CORPUS = Path('tests/fixtures/dsl/executable-corpus.json')
INPUTS = (PARITY, GENERATOR, CHECK_CORPUS, COMPATIBILITY, CORPUS)
CPU = '3ea825a87224de9eb26d786acf5fc8262b4ce2eb'
SHADER = '6f98d26ab84f17ba7fb154bb74252d6362736f89'
TREE = 'ea1d5eb2a92021a2850f0f26a2b54dd16f243847'
BINDINGS = ((PARITY, 'CPU_REV', CPU), (GENERATOR, 'UPSTREAM_REVISION', SHADER),
            (GENERATOR, 'UPSTREAM_TREE', TREE), (CHECK_CORPUS, 'REVISION', SHADER))


class AuthorityPinsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name in INPUTS:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def run_reader(self, mode='github', canonical=False):
        root = ROOT if canonical else self.root
        if not canonical and (ROOT / READER).is_file():
            shutil.copyfile(ROOT / READER, root / READER)
        return subprocess.run([sys.executable, '-B', str(root / READER), mode],
                              capture_output=True, text=True, timeout=20)

    def reject(self):
        result = self.run_reader()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertIn('authority-pins:', result.stderr)

    def replace(self, path, old, new):
        target = self.root / path
        source = target.read_text()
        self.assertIn(old, source)
        target.write_text(source.replace(old, new, 1))

    def update_json(self, path, change):
        target = self.root / path
        document = json.loads(target.read_text())
        change(document)
        target.write_text(json.dumps(document))

    def test_canonical_cpu_and_workflow_outputs_without_source_mutation(self):
        before = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in INPUTS}
        cpu = self.run_reader('cpu', canonical=True)
        self.assertEqual(cpu.returncode, 0, cpu.stderr)
        self.assertEqual(cpu.stdout, CPU + '\n')
        result = self.run_reader(canonical=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(result.stdout, f'cpu={CPU}\nshader={SHADER}\nshader_tree={TREE}\n')
        self.assertEqual(before, {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in INPUTS})

    def test_consistent_pin_move_follows_real_source_structures(self):
        for path in INPUTS:
            target = self.root / path
            target.write_text(target.read_text().replace(CPU, '1' * 40).replace(SHADER, '2' * 40).replace(TREE, '3' * 40))
        result = self.run_reader()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f'cpu={"1" * 40}\nshader={"2" * 40}\nshader_tree={"3" * 40}\n')

    def test_shader_mode_emits_only_the_validated_revision(self):
        result = self.run_reader('shader')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, SHADER + '\n')

    def test_sources_are_data_parsed_without_import_or_execution(self):
        for path in (PARITY, GENERATOR, CHECK_CORPUS):
            target = self.root / path
            target.write_text(target.read_text() + '\nraise RuntimeError("source was executed")\n')
        result = self.run_reader()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_every_binding_rejects_duplicate_assignment(self):
        for path, name, value in BINDINGS:
            with self.subTest(binding=name, path=path):
                target = self.root / path
                original = target.read_text()
                target.write_text(original + f'\n{name} = "{value}"\n')
                self.reject()
                target.write_text(original)

    def test_every_binding_rejects_nonliteral_and_bad_hex(self):
        for path, name, value in BINDINGS:
            target = self.root / path
            original = target.read_text()
            for expression in ('str("' + value + '")', '"' + value.upper() + '"',
                               '"' + value[:-1] + '"', '"' + 'g' * 40 + '"',
                               '"' + value[:20] + '" "' + value[20:] + '"'):
                with self.subTest(binding=name, expression=expression):
                    target.write_text(original.replace(f'{name} = "{value}"', f'{name} = {expression}', 1))
                    self.reject()
            target.write_text(original)

    def test_rejects_ambiguous_binding_forms(self):
        original = (self.root / PARITY).read_text()
        for assignment in (f'CPU_REV: str = "{CPU}"', f'CPU_REV = other = "{CPU}"',
                           f'if True:\n    CPU_REV = "{CPU}"',
                           f'CPU_REV = "{CPU}"\nCPU_REV += ""',
                           f'CPU_REV = "{CPU}"\nfrom somewhere import CPU_REV'):
            with self.subTest(assignment=assignment):
                (self.root / PARITY).write_text(original.replace(f'CPU_REV = "{CPU}"', assignment, 1))
                self.reject()

    def reject_pattern_capture(self, pattern):
        for path, name, _ in BINDINGS:
            with self.subTest(binding=name, path=path):
                target = self.root / path
                original = target.read_text()
                target.write_text(original + '\n' + pattern.format(name=name))
                self.reject()
                target.write_text(original)

    def test_rejects_match_as_capture_bindings(self):
        self.reject_pattern_capture('match "replacement":\n    case {name}:\n        pass\n')

    def test_rejects_match_star_capture_bindings(self):
        self.reject_pattern_capture('match ["replacement"]:\n    case [*{name}]:\n        pass\n')

    def test_rejects_match_mapping_rest_bindings(self):
        self.reject_pattern_capture('match {{"replacement": 1}}:\n    case {{**{name}}}:\n        pass\n')

    def test_each_shader_identity_mismatch_is_rejected(self):
        mutations = ((COMPATIBILITY, lambda d: d.__setitem__('corpus_revision', 'a' * 40)),
                     (COMPATIBILITY, lambda d: d['authority'].__setitem__('upstream_revision', 'a' * 40)),
                     (COMPATIBILITY, lambda d: d['authority'].__setitem__('upstream_tree', 'a' * 40)),
                     (CORPUS, lambda d: d['provenance'].__setitem__('upstreamRevision', 'a' * 40)),
                     (CORPUS, lambda d: d['provenance'].__setitem__('upstreamTree', 'a' * 40)),
                     (CORPUS, lambda d: d['records'][-1]['provenance'].__setitem__('upstreamRevision', 'a' * 40)),
                     (CORPUS, lambda d: d['records'][-1]['provenance'].__setitem__('upstreamTree', 'a' * 40)))
        for path, change in mutations:
            with self.subTest(path=path, change=change):
                original = (self.root / path).read_text()
                self.update_json(path, change)
                self.reject()
                (self.root / path).write_text(original)
        self.replace(CHECK_CORPUS, f'REVISION = "{SHADER}"', f'REVISION = "{"a" * 40}"')
        self.reject()

    def test_json_authorities_require_valid_hex_and_existing_structures(self):
        for path, change in ((COMPATIBILITY, lambda d: d['authority'].__setitem__('upstream_revision', None)),
                             (COMPATIBILITY, lambda d: d.__delitem__('authority')),
                             (CORPUS, lambda d: d.__setitem__('records', [])),
                             (CORPUS, lambda d: d['records'][0].__delitem__('provenance')),
                             (CORPUS, lambda d: d['provenance'].__setitem__('upstreamTree', TREE.upper()))):
            with self.subTest(path=path, change=change):
                original = (self.root / path).read_text()
                self.update_json(path, change)
                self.reject()
                (self.root / path).write_text(original)

    def test_duplicate_json_keys_are_rejected_even_when_values_match(self):
        for path in (COMPATIBILITY, CORPUS):
            with self.subTest(path=path):
                target = self.root / path
                original = target.read_text()
                target.write_text(original.replace('{', '{"duplicate": 0, "duplicate": 0,', 1))
                self.reject()
                target.write_text(original)

    def test_cpu_mode_still_validates_shader_consistency(self):
        self.replace(CHECK_CORPUS, f'REVISION = "{SHADER}"', f'REVISION = "{"a" * 40}"')
        result = self.run_reader('cpu')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
