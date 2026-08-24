from __future__ import annotations

import hashlib
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from tools.glslcpp import generate_typed_slice  # noqa: E402

spec = generate_typed_slice.load_slice(REPO)
keys = [item["program_key"] for item in spec["programs"]
        if item["program_key"] not in {
            "filter/rotate:rot", "mixer/focusBlur:focusBlur",
            "filter/extrude:extrude", "synth/curl:curl",
            "filter/grade:creative", "filter/grade:hslSecondary",
            "filter/grade:lut", "filter/grade:primary",
            "filter/grade:vignette", "filter/grade:wheels", "filter/reindex:nmReindexStats", "filter/zoomBlur:zoomBlur", "classicNoisedeck/caustic:caustic", "synth/bitwise:bitwise",
            "filter/adjust:adjust", "filter/colorspace:colorspace",
            "classicNoisedeck/cellNoise:cellNoise", "filter/lighting:lighting",
            "filter/invert:inv", "synth/solid:solid",
            "filter/reindex:nmReindexReduce",
            "filter/posterize:posterize", "filter/waves:waves",
            "filter/watercolor:wcSimplify"}]
print("len(keys):", len(keys))
print("perlin index:", keys.index("synth/perlin:perlin"))
print("keys sha:", hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest())
