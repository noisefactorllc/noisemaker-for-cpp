"""Source and typed-object boundaries for the Palette3D constant table."""

import dataclasses
import hashlib
import json
from pathlib import Path

import unittest

from tools.glslcpp import corpus_ratchet
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tools/glslcpp/corpus/6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d"
KEY = "filter3d/palette3d:palette3d"


def source_and_effect():
    for filename, records in (("pending.json", "pending"), ("manifest.json", "programs")):
        data = json.loads((CORPUS / filename).read_text())
        row = next((item for item in data[records] if item["program_key"] == KEY), None)
        if row is not None:
            metadata = data if filename == "pending.json" else json.loads((CORPUS / "metadata.json").read_text())
            return (CORPUS / row["source"]).read_bytes(), metadata["effects"][KEY.split(":")[0]]
    raise AssertionError("Palette3D source is absent")


class Palette3DAdmissionTests(unittest.TestCase):
    def test_palette3d_completes_the_existing_admission_probe(self):
        raw, effect = source_and_effect()
        assert corpus_ratchet.probe_program(KEY, raw, effect) is None


    def test_palette3d_proof_is_limited_to_the_exact_source_and_tree(self):
        from tools.glslcpp.frontend.palette3d_profile import authenticate_palette3d

        raw, _ = source_and_effect()
        typed = analyze_program(parse_program(raw.decode(), KEY, {}), KEY)
        source_hash = hashlib.sha256(raw).hexdigest()
        proof = authenticate_palette3d(typed, source_hash)
        assert len(proof.constructors) == 56
        assert len(proof.members) == 5
        assert len(proof.indexes) == 1
        assert proof.table.symbol.storage == "const"
        assert not proof.table.symbol.writable
        assert authenticate_palette3d(dataclasses.replace(typed, key="foreign:palette"), source_hash) is None
        for candidate, digest in (
            (typed, "0" * 64),
            (dataclasses.replace(typed, raw_source=typed.raw_source + "\n"), source_hash),
            (dataclasses.replace(typed, functions=typed.functions[:-1]), source_hash),
            (dataclasses.replace(typed, structs=()), source_hash),
            (dataclasses.replace(typed, declarations=typed.declarations[:-1]), source_hash),
        ):
            with self.assertRaisesRegex(ValueError, "Palette3D"):
                authenticate_palette3d(candidate, digest)
