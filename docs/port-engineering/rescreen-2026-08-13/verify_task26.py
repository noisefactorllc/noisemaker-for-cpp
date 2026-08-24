from __future__ import annotations

import copy
import pathlib
import re
import sys
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from tools.glslcpp import generate_typed_slice  # noqa: E402
from tools.glslcpp.frontend.smooth_edge_luma_weights_profile import (  # noqa: E402
    SMOOTH_EDGE_KEY)
from tools.glslcpp.frontend.derivative_admission_profile import (  # noqa: E402
    DERIVATIVE_ADMISSION_KEYS)

spec = generate_typed_slice.load_slice(REPO)
task26_spec = copy.deepcopy(spec)
task26_spec["programs"] = [
    item for item in task26_spec["programs"]
    if item["program_key"] not in DERIVATIVE_ADMISSION_KEYS
    and item["program_key"] not in {
        "synth/perlin:perlin", "filter/rotate:rot",
        "mixer/focusBlur:focusBlur", "filter/extrude:extrude",
        "synth/curl:curl",
        "filter/grade:creative", "filter/grade:hslSecondary",
        "filter/grade:lut", "filter/grade:primary",
        "filter/grade:vignette", "filter/grade:wheels", "filter/reindex:nmReindexStats", "filter/zoomBlur:zoomBlur", "classicNoisedeck/caustic:caustic", "synth/bitwise:bitwise",
        "filter/adjust:adjust", "filter/colorspace:colorspace",
        "classicNoisedeck/cellNoise:cellNoise", "filter/lighting:lighting",
        "filter/invert:inv", "synth/solid:solid",
        "filter/reindex:nmReindexReduce",
        "filter/posterize:posterize", "filter/waves:waves",
        "filter/watercolor:wcSimplify"}]
with mock.patch.object(generate_typed_slice, "load_slice", return_value=task26_spec):
    current = generate_typed_slice.generate_outputs(REPO)
current["include/noisemaker/generated/catalog.hpp"] = (
    generate_typed_slice.render_catalog_header(task26_spec))
prior_spec = copy.deepcopy(task26_spec)
prior_spec["programs"] = [
    item for item in prior_spec["programs"]
    if item["program_key"] != SMOOTH_EDGE_KEY]
with mock.patch.object(generate_typed_slice, "load_slice", return_value=prior_spec):
    prior = generate_typed_slice.generate_outputs(REPO)
prior["include/noisemaker/generated/catalog.hpp"] = (
    generate_typed_slice.render_catalog_header(prior_spec))

marker = re.compile(r"(?m)^// Typed IR program: ([^\n]+)\n")


def blocks(payload):
    source = payload.decode()
    starts = list(marker.finditer(source))
    catalog = source.index("\nnamespace {\nconstexpr std::array<KernelFactory")
    return {
        match.group(1): source[
            match.start():(starts[index + 1].start()
                           if index + 1 < len(starts) else catalog)]
        for index, match in enumerate(starts)
    }


current_blocks = blocks(current["src/typed_generated/typed_slice.cpp"])
prior_blocks = blocks(prior["src/typed_generated/typed_slice.cpp"])
print("len(current_blocks):", len(current_blocks))
print("diff == {SMOOTH_EDGE_KEY}:", set(current_blocks) - set(prior_blocks) == {SMOOTH_EDGE_KEY})
ordinal = re.compile(r"typed_[0-9]+")
mismatches = [k for k in prior_blocks
              if ordinal.sub("typed_SENTINEL", prior_blocks[k])
              != ordinal.sub("typed_SENTINEL", current_blocks[k])]
print("normalized mismatches:", mismatches)
smooth = current_blocks[SMOOTH_EDGE_KEY]
m = re.search(r"namespace (typed_[0-9]+) \{", smooth)
print("smooth namespace:", m.group(1) if m else None)
