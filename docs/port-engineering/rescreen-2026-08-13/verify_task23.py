from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from tools.glslcpp import check_corpus, generate_typed_slice  # noqa: E402
from tools.glslcpp.frontend.derivative_admission_profile import (  # noqa: E402
    DERIVATIVE_ADMISSION_KEYS)

new_keys = (
    "filter/bloom:ntapGather",
    "filter/directionalBlur:directionalBlur",
    "filter/spinBlur:spinBlur",
    "filter/strokes:stkSmear",
    "filter/vaseline:upsample",
    "filter/wind:wind",
)

live_spec = generate_typed_slice.load_slice(REPO)
spec = copy.deepcopy(live_spec)
spec["programs"] = [
    item for item in spec["programs"]
    if item["program_key"] not in DERIVATIVE_ADMISSION_KEYS
    and item["program_key"] not in {
        "classicNoisedeck/lensDistortion:lensDistortion",
        "filter/pixelSort:gatherSorted",
        "filter/prismaticAberration:prismaticAberration",
        "filter/smooth:smoothEdge",
        "synth/perlin:perlin",
        "filter/rotate:rot",
        "mixer/focusBlur:focusBlur",
        "filter/extrude:extrude",
        "synth/curl:curl",
        "filter/grade:creative",
        "filter/grade:hslSecondary",
        "filter/grade:lut",
        "filter/grade:primary",
        "filter/grade:vignette",
        "filter/grade:wheels", "filter/reindex:nmReindexStats", "filter/zoomBlur:zoomBlur",
        "classicNoisedeck/caustic:caustic", "synth/bitwise:bitwise",
        "filter/adjust:adjust", "filter/colorspace:colorspace",
        "classicNoisedeck/cellNoise:cellNoise", "filter/lighting:lighting",
        "filter/invert:inv", "synth/solid:solid",
        "filter/reindex:nmReindexReduce",
        "filter/posterize:posterize", "filter/waves:waves",
        "filter/watercolor:wcSimplify",
    }]
keys = [item["program_key"] for item in spec["programs"]
        if item["program_key"] != "filter/rotate:rot"]
public = sorted((*keys, "filter/invert:inv", "synth/solid:solid"))
corpus = json.loads((check_corpus._corpus_root(REPO) / "manifest.json").read_text())
print("counts:", (len(keys), len(public), len(corpus["programs"]) - len(public), len(corpus["programs"])))
print("keys sha:", hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest())
print("public sha:", hashlib.sha256(("\n".join(public) + "\n").encode()).hexdigest())
print("new_keys indices:", tuple(keys.index(key) for key in new_keys))
print("nmReindexStats in keys:", "filter/reindex:nmReindexStats" in keys)

with mock.patch.object(generate_typed_slice, "load_slice", return_value=spec):
    current = generate_typed_slice.generate_outputs(REPO)
current_cpp = current["src/typed_generated/typed_slice.cpp"].decode()
prior_spec = copy.deepcopy(spec)
prior_spec["programs"] = [item for item in prior_spec["programs"]
                          if item["program_key"] not in new_keys]
with mock.patch.object(generate_typed_slice, "load_slice", return_value=prior_spec):
    prior_cpp = generate_typed_slice.generate_outputs(REPO)[
        "src/typed_generated/typed_slice.cpp"].decode()
print("prior_cpp len/sha:", len(prior_cpp.encode()), hashlib.sha256(prior_cpp.encode()).hexdigest())

import re
marker = re.compile(r"(?m)^// Typed IR program: (.+)$")


def blocks(text):
    hits = list(marker.finditer(text))
    result = {}
    for index, hit in enumerate(hits):
        end = (hits[index + 1].start() if index + 1 < len(hits)
               else text.index("\nnamespace {", hit.end()))
        result[hit.group(1)] = text[hit.start():end]
    return result


before, after = blocks(prior_cpp), blocks(current_cpp)
print("len(before):", len(before))
print("set(before) == set(after)-set(new_keys):", set(before) == set(after) - set(new_keys))
normalize = lambda value: re.sub(r"typed_[0-9]+", "typed_SENTINEL", value)
mismatches = [key for key in before if normalize(before[key]) != normalize(after[key])]
print("normalized mismatches (should be empty):", mismatches)
