"""C++ side of the exhaustive palette override sweep: replays every case
exhaustive_js.mjs captured (six admitted palette effects x palette indexes
0..55 x two sizes) through noisemaker-dsl-cpu-case, and requires the RGBA8
sha256 match the JS authority's own capture exactly. classicNoisedeck/
shapes3d:shapes3d is not swept -- its corpus record is recordKind
"excluded" (an unrelated 3D/volume-output limitation), so this port's
executor never admits it at all.
"""
import hashlib
import json
import pathlib
import subprocess
import tempfile

PALETTE = pathlib.Path("/Users/alex/platform/.nm-cpp-work/lanes/palette")
DRIVER = PALETTE / "build-lane/noisemaker-dsl-cpu-case"
CASES = json.loads(pathlib.Path(
    "/private/tmp/claude-502/-Users-alex-platform-scaffold/4b35d94f-8f1c-451d-b220-88b458c1bfa7/scratchpad/exhaustive_cases.json"
).read_text())

mismatches = []
errors = []
ok = 0

with tempfile.TemporaryDirectory(prefix="palette-exhaustive-") as tmp:
    scratch = pathlib.Path(tmp)
    for case in CASES:
        source_path = scratch / "case.dsl"
        source_path.write_text(case["source"], encoding="utf-8")
        source_hash = hashlib.sha256(case["source"].encode("utf-8")).hexdigest()
        rgba_path = scratch / "case.rgba8"
        meta_path = scratch / "case.json"
        result = subprocess.run(
            [str(DRIVER), "--source-file", str(source_path), "--source-sha256", source_hash,
             "--width", str(case["width"]), "--height", str(case["height"]),
             "--time", str(case["time"]), "--frame", "0", "--seed", str(case["seed"]),
             "--rgba8-output", str(rgba_path), "--metadata-output", str(meta_path)],
            capture_output=True, text=True)
        if result.returncode != 0:
            errors.append((case["case_id"], (result.stdout or result.stderr).strip()[:200]))
            continue
        actual = hashlib.sha256(rgba_path.read_bytes()).hexdigest()
        if actual != case["rgba8_sha256"]:
            mismatches.append((case["case_id"], case["rgba8_sha256"], actual))
        else:
            ok += 1

print(f"total cases: {len(CASES)}")
print(f"byte-exact: {ok}")
print(f"errors (driver failed): {len(errors)}")
for case_id, detail in errors[:20]:
    print(f"  ERROR {case_id}: {detail}")
print(f"mismatches (wrong bytes): {len(mismatches)}")
for case_id, expected, actual in mismatches[:20]:
    print(f"  MISMATCH {case_id}: expected={expected} actual={actual}")
print(f"\nFINAL DIVERGENCE COUNT: {len(mismatches)}")
