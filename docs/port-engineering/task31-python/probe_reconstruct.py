import hashlib
import pathlib
import sys
from unittest import mock

sys.path.insert(0, ".")
REPOSITORY = pathlib.Path(".")

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend.curl_vector_math_profile import CURL_KEY

spec = generate_typed_slice.load_slice(REPOSITORY)
task30_spec = dict(spec)
task30_spec["programs"] = [item for item in spec["programs"]
                           if item["program_key"] != CURL_KEY]
keys = tuple(item["program_key"] for item in task30_spec["programs"])
print("count", len(keys))
print("keys-hash", hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest())

with mock.patch.object(generate_typed_slice, "load_slice", return_value=task30_spec):
    outputs = generate_typed_slice.generate_outputs(REPOSITORY)
outputs["include/noisemaker/generated/catalog.hpp"] = (
    generate_typed_slice.render_catalog_header(task30_spec))
for path in ("src/typed_generated/typed_slice.cpp",
             "src/typed_generated/typed_manifest.json",
             "include/noisemaker/generated/catalog.hpp"):
    print(path, hashlib.sha256(outputs[path]).hexdigest())
