"""Re-pin src/effects/registry.cpp's production catalog provenance checks from the generated provenance.

Live pins only: every value is read from src/effects/generated/effect_catalog.provenance.json and
src/effects/generated/backend_compatibility.json (both produced by their generators); each target
expression must occur exactly once in registry.cpp.
"""
import json, pathlib, re, sys

REPO = pathlib.Path(sys.argv[1]).resolve()
path = REPO / "src/effects/registry.cpp"
text = path.read_text(encoding="utf-8")
prov = json.loads((REPO / "src/effects/generated/effect_catalog.provenance.json").read_text())
compat = json.loads((REPO / "src/effects/generated/backend_compatibility.json").read_text())
a, c, bc = prov["authority"], prov["counts"], prov["backend_counts"]


def sub(pattern, replacement):
    global text
    matches = re.findall(pattern, text)
    if len(matches) != 1:
        raise SystemExit(f"pattern must match exactly once ({len(matches)}): {pattern}")
    text = re.sub(pattern, replacement, text)


def s(field, value):
    sub(rf'provenance_\.{field} != "[^"]*"', f'provenance_.{field} != "{value}"')


s("corpus_revision", prov["corpus_revision"])
s("generated_payload_sha256", prov["generated_payload_sha256"])
s("normalized_record_stream_sha256", prov["normalized_record_stream_sha256"])
s("compatibility_sha256", prov["compatibility_sha256"])
s("cpu_behavioral_lock", a["cpu_behavioral_lock"])
s("cpu_revision", a["cpu_behavioral_lock"])
s("source_lock_sha256", a["source_lock_sha256"])
s("cpu_package_sha256", a["cpu_package_sha256"])
s("cpu_package_lock_sha256", a["cpu_package_lock_sha256"])
s("cpu_source_lock_sha256", a["cpu_source_lock_sha256"])
s("upstream_revision", a["upstream_revision"])
s("upstream_tree", a["upstream_tree"])
s("upstream_package_sha256", a["upstream_package_sha256"])
s("upstream_package_lock_sha256", a["upstream_package_lock_sha256"])
s("first_effect_id", prov["first_effect_id"])
s("last_effect_id", prov["last_effect_id"])
sub(r"provenance_\.cpu_behavioral_file_count != \d+", f"provenance_.cpu_behavioral_file_count != {a['cpu_behavioral_file_count']}")
sub(r"canonical_programs_\.size\(\) != \d+ \|\| reference_passes_\.size\(\) != \d+",
    f"canonical_programs_.size() != {len(compat['canonical_programs'])} || reference_passes_.size() != {len(compat['reference_passes'])}")
for field, key in (("definitions", "definitions"), ("passes", "passes"), ("reference_program_keys", "reference_program_keys"),
                   ("backend_programs", "backend_programs"), ("compatible_programs", "compatible_programs"),
                   ("incompatible_programs", "incompatible_programs"), ("missing_passes", "missing_passes"),
                   ("scatter_passes", "scatter_passes"), ("executable_definitions", "executable_definitions"),
                   ("incomplete_definitions", "incomplete_definitions")):
    sub(rf"provenance_\.counts\.{field} != \d+", f"provenance_.counts.{field} != {c[key]}")
for field, key in (("backend_fragment_rows", "fragment_rows"), ("backend_unique_fragment_keys", "unique_fragment_keys"),
                   ("backend_raw_exact", "raw_exact"), ("backend_semantic_exact", "semantic_exact")):
    sub(rf"provenance_\.{field} != \d+", f"provenance_.{field} != {bc[key]}")
sub(r"strict_manifest && expected_reference != \d+\)", f"strict_manifest && expected_reference != {len(compat['reference_passes'])})")
path.write_text(text, encoding="utf-8")
print("registry.cpp re-pinned from generated provenance")

# tests/test_effect_catalog.cpp pins the same live provenance values; re-pin them from the same source.
test_path = REPO / "tests/test_effect_catalog.cpp"
test_text = test_path.read_text(encoding="utf-8")
for field in ("generated_payload_sha256", "normalized_record_stream_sha256", "compatibility_sha256", "corpus_revision"):
    pattern = rf'provenance\.{field} == "[^"]*"'
    count = len(re.findall(pattern, test_text))
    if count > 1:
        raise SystemExit(f"test_effect_catalog.cpp: {field} pinned {count} times")
    test_text = re.sub(pattern, lambda _m, f=field: f'provenance.{f} == "{prov[f]}"', test_text)
test_path.write_text(test_text, encoding="utf-8")
print("test_effect_catalog.cpp re-pinned from generated provenance")
