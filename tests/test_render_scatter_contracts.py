"""Exact current authority pass sets for the two render scatter adapters."""

import copy
import json
from pathlib import Path

import pytest

from tools.dsl.generate_backend_compatibility import authenticate_scatter_contract


CORPUS = (Path(__file__).resolve().parents[1] / "tools/glslcpp/corpus"
          / "6cb1a3c3e21010db956d41e7a6d57a02b0be1e7d")
KEYS = ("render/pointsRender:deposit", "render/pointsBillboardRender:deposit")


def source_bytes(key):
    for name, field in (("pending.json", "pending"), ("manifest.json", "programs")):
        rows = json.loads((CORPUS / name).read_text())[field]
        row = next((entry for entry in rows if entry["program_key"] == key), None)
        if row is not None:
            return (CORPUS / row["source"]).read_bytes()
    raise AssertionError(f"missing scatter source: {key}")


@pytest.mark.parametrize("key", KEYS)
def test_current_render_scatter_pass_set_is_registered(key):
    effect = json.loads((CORPUS / "metadata.json").read_text())["effects"][key.split(":")[0]]
    authenticate_scatter_contract(key, source_bytes(key), effect)


@pytest.mark.parametrize("key", KEYS)
def test_render_scatter_pass_forgery_is_rejected(key):
    effect = json.loads((CORPUS / "metadata.json").read_text())["effects"][key.split(":")[0]]
    raw = source_bytes(key)
    indices = [i for i, item in enumerate(effect["passes"]) if item["program"] == "deposit"]
    assert len(indices) == (3 if key == KEYS[0] else 8)

    def rejects(change):
        forged = copy.deepcopy(effect)
        change(forged["passes"])
        with pytest.raises(ValueError):
            authenticate_scatter_contract(key, raw, forged)

    rejects(lambda passes: passes.pop(indices[0]))
    rejects(lambda passes: passes.insert(indices[0], copy.deepcopy(passes[indices[0]])))
    rejects(lambda passes: passes.__setitem__(slice(indices[0], indices[0] + 2),
                                              list(reversed(passes[indices[0]:indices[0] + 2]))))
    for field, value in (
        ("name", "forged"), ("drawMode", "fragment"), ("count", "forged"),
        ("inputs", {}), ("outputs", {"fragColor": "forged"}),
        ("blend", False), ("defines", {"VIEW_MODE": 99}),
    ):
        rejects(lambda passes, field=field, value=value: passes[indices[0]].__setitem__(field, value))
    with pytest.raises(ValueError):
        authenticate_scatter_contract(key, raw + b"\n", effect)
