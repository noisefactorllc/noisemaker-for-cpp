from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import re
import sys
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from tools.glslcpp import generate_typed_slice  # noqa: E402
from tools.glslcpp.frontend.gather_sorted_round_profile import (  # noqa: E402
    GATHER_SORTED_KEY, PROFILE)
from tools.glslcpp.frontend.literal_vec3_lane_index_profile import KEYS  # noqa: E402
from tools.glslcpp.frontend.derivative_admission_profile import (  # noqa: E402
    DERIVATIVE_ADMISSION_KEYS)

REMOVE_EXTRA = (
    "filter/posterize:posterize", "filter/waves:waves", "filter/watercolor:wcSimplify")

print("=== task24 loader ===")
spec = copy.deepcopy(generate_typed_slice.load_slice(REPO))
spec["programs"] = [item for item in spec["programs"]
                    if item["program_key"] not in KEYS
                    and item["program_key"] not in DERIVATIVE_ADMISSION_KEYS
                    and item["program_key"] not in {
                        "filter/smooth:smoothEdge", "synth/perlin:perlin",
                        "filter/rotate:rot", "mixer/focusBlur:focusBlur",
                        "filter/extrude:extrude", "synth/curl:curl",
                        "filter/grade:creative", "filter/grade:hslSecondary",
                        "filter/grade:lut", "filter/grade:primary",
                        "filter/grade:vignette", "filter/grade:wheels",
                        "filter/reindex:nmReindexStats", "filter/zoomBlur:zoomBlur",
                        "classicNoisedeck/caustic:caustic", "synth/bitwise:bitwise",
                        "filter/adjust:adjust", "filter/colorspace:colorspace",
                        "classicNoisedeck/cellNoise:cellNoise", "filter/lighting:lighting",
                        "filter/invert:inv", "synth/solid:solid",
                        "filter/reindex:nmReindexReduce", *REMOVE_EXTRA}]
print("len:", len(spec["programs"]))
gather_index = next(index for index, item in enumerate(spec["programs"])
                    if item["program_key"] == GATHER_SORTED_KEY)
print("gather index:", gather_index)
with mock.patch.object(generate_typed_slice, "load_slice", return_value=spec):
    outputs = generate_typed_slice.generate_outputs(REPO)
manifest = json.loads(outputs["src/typed_generated/typed_manifest.json"].decode())
print("manifest programs:", len(manifest["programs"]))
keys = [item["program_key"] for item in manifest["programs"]]
print("keys sha:", hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest())

print("=== task24 generation ===")
current_spec = copy.deepcopy(generate_typed_slice.load_slice(REPO))
current_spec["programs"] = [
    item for item in current_spec["programs"]
    if item["program_key"] not in KEYS
    and item["program_key"] not in {
        "filter/smooth:smoothEdge", "synth/perlin:perlin",
        "filter/rotate:rot", "mixer/focusBlur:focusBlur",
        "filter/extrude:extrude", "synth/curl:curl",
        "filter/grade:creative", "filter/grade:hslSecondary",
        "filter/grade:lut", "filter/grade:primary",
        "filter/grade:vignette", "filter/grade:wheels",
        "filter/reindex:nmReindexStats", "filter/zoomBlur:zoomBlur",
        "classicNoisedeck/caustic:caustic", "synth/bitwise:bitwise",
        "filter/adjust:adjust", "filter/colorspace:colorspace",
        "classicNoisedeck/cellNoise:cellNoise", "filter/lighting:lighting",
        "filter/invert:inv", "synth/solid:solid",
        "filter/reindex:nmReindexReduce", *REMOVE_EXTRA}]
with mock.patch.object(generate_typed_slice, "load_slice", return_value=current_spec):
    current = generate_typed_slice.generate_outputs(REPO)
prior_spec = copy.deepcopy(current_spec)
prior_spec["programs"] = [
    item for item in prior_spec["programs"]
    if item["program_key"] != GATHER_SORTED_KEY]
with mock.patch.object(generate_typed_slice, "load_slice", return_value=prior_spec):
    prior = generate_typed_slice.generate_outputs(REPO)
header_path = "include/noisemaker/generated/catalog.hpp"
current[header_path] = generate_typed_slice.render_catalog_header(current_spec)
prior[header_path] = generate_typed_slice.render_catalog_header(prior_spec)
for path in ("src/typed_generated/typed_slice.cpp",
             "src/typed_generated/typed_manifest.json",
             header_path):
    print("prior", path, hashlib.sha256(prior[path]).hexdigest())


def blocks(payload: bytes):
    source = payload.decode()
    starts = list(re.finditer(r"(?m)^// Typed IR program: ([^\n]+)\n", source))
    catalog = source.index("\nnamespace {\nconstexpr std::array<KernelFactory")
    result = {}
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else catalog
        result[match.group(1)] = source[match.start():end]
    return result


prior_blocks = blocks(prior["src/typed_generated/typed_slice.cpp"])
current_blocks = blocks(current["src/typed_generated/typed_slice.cpp"])
prior_keys = list(prior_blocks)
current_keys = list(current_blocks)
print("prior/current key counts:", len(prior_keys), len(current_keys))
print("gather index in current:", current_keys.index(GATHER_SORTED_KEY))
print("window:", current_keys[max(0, current_keys.index(GATHER_SORTED_KEY) - 1):
                              current_keys.index(GATHER_SORTED_KEY) + 2])
print("prior[:idx] == current[:idx]:",
      prior_keys[:current_keys.index(GATHER_SORTED_KEY)]
      == current_keys[:current_keys.index(GATHER_SORTED_KEY)])
print("diff == {GATHER}:", set(current_blocks) - set(prior_blocks) == {GATHER_SORTED_KEY})
ordinal = re.compile(r"typed_[0-9]+")
mismatches = [k for k in prior_keys
              if ordinal.sub("typed_ORDINAL", prior_blocks[k])
              != ordinal.sub("typed_ORDINAL", current_blocks[k])]
print("mismatches:", mismatches)
