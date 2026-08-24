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

spec = generate_typed_slice.load_slice(REPO)
typed = tuple(item["program_key"] for item in spec["programs"])
print("current typed count:", len(typed))

REMOVE = {
    "filter/grade:creative", "filter/grade:hslSecondary",
    "filter/grade:lut", "filter/grade:primary",
    "filter/grade:vignette", "filter/grade:wheels",
    "filter/reindex:nmReindexStats", "filter/zoomBlur:zoomBlur",
    "classicNoisedeck/caustic:caustic", "synth/bitwise:bitwise",
    "filter/adjust:adjust", "filter/colorspace:colorspace",
    "classicNoisedeck/cellNoise:cellNoise", "filter/lighting:lighting",
    "filter/invert:inv", "synth/solid:solid",
    "filter/reindex:nmReindexReduce",
    "filter/posterize:posterize", "filter/waves:waves",
    "filter/watercolor:wcSimplify",
}
print("removal set size:", len(REMOVE))

task31_spec = copy.deepcopy(spec)
task31_spec["programs"] = [
    item for item in task31_spec["programs"]
    if item["program_key"] not in REMOVE]
task31_keys = tuple(item["program_key"] for item in task31_spec["programs"])
print("task31 keys count:", len(task31_keys))
task31_keys_sha = hashlib.sha256(("\n".join(task31_keys) + "\n").encode()).hexdigest()
print("task31_keys sha256:", task31_keys_sha)

with mock.patch.object(generate_typed_slice, "load_slice", return_value=task31_spec):
    task31 = generate_typed_slice.generate_outputs(REPO)
task31["include/noisemaker/generated/catalog.hpp"] = (
    generate_typed_slice.render_catalog_header(task31_spec))

manifest = json.loads(task31["src/typed_generated/typed_manifest.json"].decode())
print("manifest programs:", len(manifest["programs"]))

for path in ("src/typed_generated/typed_slice.cpp",
             "src/typed_generated/typed_manifest.json",
             "include/noisemaker/generated/catalog.hpp"):
    print(path, hashlib.sha256(task31[path]).hexdigest())

current = generate_typed_slice.generate_outputs(REPO)
marker = re.compile(r"(?m)^// Typed IR program: ([^\n]+)\n")


def blocks(payload):
    source = payload.decode()
    starts = list(marker.finditer(source))
    catalog = source.index("\nnamespace {\nconstexpr std::array<KernelFactory")
    return {match.group(1): source[
        match.start():(starts[index + 1].start()
                       if index + 1 < len(starts) else catalog)]
        for index, match in enumerate(starts)}


current_blocks = blocks(current["src/typed_generated/typed_slice.cpp"])
task31_blocks = blocks(task31["src/typed_generated/typed_slice.cpp"])
print("current_blocks, task31_blocks:", len(current_blocks), len(task31_blocks))
diff = set(current_blocks) - set(task31_blocks)
print("diff size:", len(diff))
print("diff == REMOVE:", diff == REMOVE)
if diff != REMOVE:
    print("only in diff:", diff - REMOVE)
    print("only in REMOVE:", REMOVE - diff)

ordinal = re.compile(r"typed_[0-9]+")
mismatches = []
for key, block in task31_blocks.items():
    if ordinal.sub("typed_SENTINEL", block) != ordinal.sub("typed_SENTINEL", current_blocks[key]):
        mismatches.append(key)
print("block mismatches (should be empty):", mismatches)
