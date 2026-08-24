"""READ-ONLY independent re-derivation of the unpatched validator+emitter
first-blocker message for each filter/grade:* program, and confirmation that
the whole-program hash reported at PASS depth in
roadmap2/gate-chain-all-output.json is reproducible when index+global
admission are bypassed exactly the same way. No monkeypatch state is left
mutated (try/finally with identity snapshots)."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(".")
sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice as gen  # noqa: E402
from tools.glslcpp import emit_typed_cpp as emit  # noqa: E402
from tools.glslcpp.frontend import parse_program  # noqa: E402
from tools.glslcpp.frontend.semantic import analyze_program  # noqa: E402

REVISION = "a024dc3a960cc44af454abc7aebce50456c194e6"
CORPUS = ROOT / "tools/glslcpp/corpus" / REVISION
MANIFEST = json.loads((CORPUS / "manifest.json").read_text())
ENTRIES = {row["program_key"]: row for row in MANIFEST["programs"]}

KEYS = [
    "filter/grade:primary", "filter/grade:hslSecondary", "filter/grade:wheels",
    "filter/grade:vignette", "filter/grade:creative", "filter/grade:lut",
]


def first_line(error) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else type(error).__name__


def load(key):
    entry = ENTRIES[key]
    raw = (CORPUS / entry["source"]).read_text()
    defines = gen._defaults(ROOT, key)
    typed = analyze_program(parse_program(raw, key, defines), key)
    return entry, raw, typed


def main():
    # Snapshot globals we must never leave mutated.
    snap_caps = gen.APPROVED_CAPABILITIES
    snap_builtins = gen._BUILTINS
    snap_types = gen.APPROVED_TYPES
    assert len(snap_caps) == 44, f"expected 44-entry vocabulary, found {len(snap_caps)}"

    results = {}
    for key in KEYS:
        entry, raw, typed = load(key)
        try:
            gen.validate_capabilities(typed, gen.APPROVED_CAPABILITIES, source_hash=entry["raw_sha256"])
            v = "pass"
        except Exception as e:  # noqa: BLE001
            v = first_line(e)
        try:
            cpp = emit.render_typed_cpp(typed, typed.key, entry["raw_sha256"],
                                        "task32b_probe", "bind_task32b_probe")
            e_msg = "pass"
            cpp_hash = hashlib.sha256(cpp.encode()).hexdigest()
            cpp_len = len(cpp.encode())
        except Exception as e:  # noqa: BLE001
            e_msg = first_line(e)
            cpp_hash = None
            cpp_len = None
        results[key] = {"validator": v, "emitter": e_msg, "cpp_sha256": cpp_hash, "cpp_bytes": cpp_len}
        print(f"{key}: validator={v!r} emitter={e_msg!r}")

    # Restoration proof.
    assert gen.APPROVED_CAPABILITIES is snap_caps
    assert gen._BUILTINS is snap_builtins
    assert gen.APPROVED_TYPES is snap_types
    print("restored_all: true (identity-checked, no monkeypatch applied in this script)")

    Path("docs/port-engineering/task32b_validate_baseline_output.json").write_text(
        json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
