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

from tools.glslcpp import check_corpus, generate_typed_slice  # noqa: E402
from tools.glslcpp.frontend.curl_vector_math_profile import CURL_KEY  # noqa: E402
from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (  # noqa: E402
    EXTRUDE_KEY)
from tools.glslcpp.frontend.focus_blur_borrowed_sampler_profile import (  # noqa: E402
    FOCUS_BLUR_KEY, PROFILE)

marker = re.compile(r"(?m)^// Typed IR program: ([^\n]+)\n")


def blocks(payload):
    source = payload.decode()
    starts = list(marker.finditer(source))
    catalog = source.index("\nnamespace {\nconstexpr std::array<KernelFactory")
    return {match.group(1): source[
        match.start():(starts[index + 1].start()
                       if index + 1 < len(starts) else catalog)]
        for index, match in enumerate(starts)}


spec = generate_typed_slice.load_slice(REPO)
typed = tuple(item["program_key"] for item in spec["programs"])
public = tuple(sorted(set(typed) | {"filter/invert:inv", "synth/solid:solid"}))
corpus = json.loads((check_corpus._corpus_root(REPO) / "manifest.json").read_text())
unported = tuple(sorted({item["program_key"] for item in corpus["programs"]} - set(public)))
print("task29 counts:", (len(typed), len(public), len(unported), len(corpus["programs"])))
print("task29 typed sha:", hashlib.sha256(("\n".join(typed) + "\n").encode()).hexdigest())
print("task29 focus index:", typed.index(FOCUS_BLUR_KEY))
print("task29 window:", typed[143:146])

current = generate_typed_slice.generate_outputs(REPO)
current_header = generate_typed_slice.render_catalog_header(spec)

task28_spec = copy.deepcopy(spec)
task28_spec["programs"] = [item for item in task28_spec["programs"]
                           if item["program_key"] not in
                           (FOCUS_BLUR_KEY, EXTRUDE_KEY, CURL_KEY,
                            "filter/grade:creative",
                            "filter/grade:hslSecondary",
                            "filter/grade:lut",
                            "filter/grade:primary",
                            "filter/grade:vignette",
                            "filter/grade:wheels", "filter/reindex:nmReindexStats", "filter/zoomBlur:zoomBlur", "classicNoisedeck/caustic:caustic", "synth/bitwise:bitwise",
                            "filter/adjust:adjust", "filter/colorspace:colorspace",
                            "classicNoisedeck/cellNoise:cellNoise", "filter/lighting:lighting",
                            "filter/invert:inv", "synth/solid:solid",
                            "filter/reindex:nmReindexReduce",
                            "filter/posterize:posterize", "filter/waves:waves",
                            "filter/watercolor:wcSimplify")]
task28_keys = tuple(item["program_key"] for item in task28_spec["programs"])
task28_public = tuple(sorted((*task28_keys, "filter/invert:inv", "synth/solid:solid")))
task28_unported = tuple(sorted({item["program_key"] for item in corpus["programs"]} - set(task28_public)))
print("task28 counts:", (len(task28_keys), len(task28_public), len(task28_unported)))
print("task28 keys sha:", hashlib.sha256(("\n".join(task28_keys) + "\n").encode()).hexdigest())
print("task28 public sha:", hashlib.sha256(("\n".join(task28_public) + "\n").encode()).hexdigest())

with mock.patch.object(generate_typed_slice, "load_slice", return_value=task28_spec):
    task28 = generate_typed_slice.generate_outputs(REPO)
task28["include/noisemaker/generated/catalog.hpp"] = (
    generate_typed_slice.render_catalog_header(task28_spec))
for path in ("src/typed_generated/typed_slice.cpp",
             "src/typed_generated/typed_manifest.json",
             "include/noisemaker/generated/catalog.hpp"):
    print("task28", path, hashlib.sha256(task28[path]).hexdigest())

current_blocks = blocks(current["src/typed_generated/typed_slice.cpp"])
task28_blocks = blocks(task28["src/typed_generated/typed_slice.cpp"])
print("counts current/task28:", (len(current_blocks), len(task28_blocks)))
diff = set(current_blocks) - set(task28_blocks)
expected_diff = {FOCUS_BLUR_KEY, EXTRUDE_KEY, CURL_KEY,
                 "filter/grade:creative", "filter/grade:hslSecondary",
                 "filter/grade:lut", "filter/grade:primary",
                 "filter/grade:vignette", "filter/grade:wheels", "filter/reindex:nmReindexStats", "filter/zoomBlur:zoomBlur",
                 "classicNoisedeck/caustic:caustic", "synth/bitwise:bitwise",
                 "filter/adjust:adjust", "filter/colorspace:colorspace",
                 "classicNoisedeck/cellNoise:cellNoise", "filter/lighting:lighting",
                 "filter/invert:inv", "synth/solid:solid",
                 "filter/reindex:nmReindexReduce",
                 "filter/posterize:posterize", "filter/waves:waves",
                 "filter/watercolor:wcSimplify"}
print("diff == expected:", diff == expected_diff)
ordinal = re.compile(r"typed_[0-9]+")
mismatches = [k for k in task28_blocks
              if ordinal.sub("typed_SENTINEL", task28_blocks[k])
              != ordinal.sub("typed_SENTINEL", current_blocks[k])]
print("mismatches:", mismatches)
focus = current_blocks[FOCUS_BLUR_KEY]
m = re.search(r"namespace (typed_[0-9]+) \{", focus)
print("focus namespace:", m.group(1) if m else None)

# ---- task29 ----
task29_spec = copy.deepcopy(spec)
task29_spec["programs"] = [item for item in task29_spec["programs"]
                           if item["program_key"] not in (
                               EXTRUDE_KEY, CURL_KEY,
                               "filter/grade:creative",
                               "filter/grade:hslSecondary",
                               "filter/grade:lut",
                               "filter/grade:primary",
                               "filter/grade:vignette",
                               "filter/grade:wheels", "filter/reindex:nmReindexStats", "filter/zoomBlur:zoomBlur", "classicNoisedeck/caustic:caustic", "synth/bitwise:bitwise",
                               "filter/adjust:adjust", "filter/colorspace:colorspace",
                               "classicNoisedeck/cellNoise:cellNoise", "filter/lighting:lighting",
                               "filter/invert:inv", "synth/solid:solid",
                               "filter/reindex:nmReindexReduce",
                               "filter/posterize:posterize", "filter/waves:waves",
                               "filter/watercolor:wcSimplify")]
task29_keys = tuple(item["program_key"] for item in task29_spec["programs"])
print("task29b len:", len(task29_keys))
print("task29b sha:", hashlib.sha256(("\n".join(task29_keys) + "\n").encode()).hexdigest())
with mock.patch.object(generate_typed_slice, "load_slice", return_value=task29_spec):
    task29 = generate_typed_slice.generate_outputs(REPO)
task29["include/noisemaker/generated/catalog.hpp"] = (
    generate_typed_slice.render_catalog_header(task29_spec))
for path in ("src/typed_generated/typed_slice.cpp",
             "src/typed_generated/typed_manifest.json",
             "include/noisemaker/generated/catalog.hpp"):
    print("task29", path, hashlib.sha256(task29[path]).hexdigest())
task29_blocks = blocks(task29["src/typed_generated/typed_slice.cpp"])
print("task29 block count:", len(task29_blocks))
print("EXTRUDE_KEY in task29_blocks:", EXTRUDE_KEY in task29_blocks)
