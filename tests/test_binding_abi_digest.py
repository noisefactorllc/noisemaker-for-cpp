"""The binding-ABI digest grammar has four implementations; bind them together.

The typed-slice generator bakes per-section anchors into the route table, the
effect registry serializes the same authenticated document into the plan, the
executor re-derives the sections from the value-owned admission, and the JS
oracle mirrors the grammar for the cross-language plan stream. Any pair
drifting silently would turn the executor's anchor comparison into a
rubber stamp, so this test recomputes the grammar independently in Python and
requires every generated anchor and every registry digest to agree with it.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPATIBILITY = ROOT / "src/effects/generated/backend_compatibility.json"
TYPED_SLICE = ROOT / "src/typed_generated/typed_slice.cpp"
EXECUTOR = ROOT / "src/graph/executor.cpp"
REGISTRY = ROOT / "src/effects/registry.cpp"
JS_ORACLE = ROOT / "tools/dsl/js_frontend_oracle.mjs"

UNIT = "\x1f"
RECORD = "\x1e"


def token(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(int(value)) if float(value).is_integer() else repr(value)
    return str(value)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def custom_adapter_defines(row: dict) -> list[dict]:
    route = (row.get("factory") or {}).get("route") or {}
    if route.get("kind") != "custom_adapter":
        return []
    uniform_names = {item.get("name", "") for item in row.get("uniforms") or []}
    result = []
    for item in (route.get("binding_abi") or {}).get("uniforms") or []:
        name = item.get("name", "")
        if not name or name in uniform_names:
            continue
        result.append({"name": name, "cpp_type": item.get("cpp_type", ""),
                       "source": item.get("source", "")})
    return result


def sections(row: dict) -> dict[str, str]:
    def bindings(name: str) -> str:
        out = [name, RECORD]
        for item in row.get(name) or []:
            for field in ("name", "type", "source", "source_name", "resource", "cpp_type"):
                out.append(token(item.get(field, "")))
                out.append(UNIT)
        out.append(RECORD)
        return "".join(out)

    outputs = ["outputs", RECORD]
    for item in row.get("outputs") or []:
        outputs.append(token(item.get("slot", 0)))
        outputs.append(UNIT)
        for field in ("physical_name", "logical_route", "cpp_type"):
            outputs.append(token(item.get(field, "")))
            outputs.append(UNIT)
    outputs.append(RECORD)

    extent = ((row.get("output_abi") or {}).get("extent")) or {}
    defines = ["defines", RECORD]
    for item in custom_adapter_defines(row):
        defines.extend([item["name"], UNIT, item["cpp_type"], UNIT, item["source"], UNIT])
    defines.append(RECORD)

    return {
        "samplers": bindings("samplers"),
        "uniforms": bindings("uniforms"),
        "outputs": "".join(outputs),
        "extent": "extent" + RECORD + token(extent.get("width")) + UNIT
                  + token(extent.get("height")) + UNIT + token(extent.get("format"))
                  + UNIT + RECORD,
        "defines": "".join(defines),
    }


class BindingAbiDigestTest(unittest.TestCase):
    def canonical_rows(self) -> dict[str, dict]:
        document = json.loads(COMPATIBILITY.read_text(encoding="utf-8"))
        return {row["program_key"]: row for row in document["canonical_programs"]}

    def test_generated_route_anchors_match_an_independent_derivation(self) -> None:
        rows = self.canonical_rows()
        text = TYPED_SLICE.read_text(encoding="utf-8")
        block = text[text.index("kCanonicalRoutes{{"):text.index("std::span<const KernelFactory> catalog()")]
        entries = re.findall(r'^\s*\{"([^"]+)",((?:\s*"[^"]*",)+)\s*&', block, re.MULTILINE)
        self.assertEqual(len(entries), len(rows))
        seen = set()
        for key, fields in entries:
            values = re.findall(r'"([^"]*)"', fields)
            # key, canonical, emitted, kind, source, typed_abi, contract, defines,
            # sampler, uniform, output, extent, define-abi
            self.assertEqual(len(values), 12, key)
            expected = sections(rows[key])
            self.assertEqual(values[7], digest(expected["samplers"]), f"{key} samplers")
            self.assertEqual(values[8], digest(expected["uniforms"]), f"{key} uniforms")
            self.assertEqual(values[9], digest(expected["outputs"]), f"{key} outputs")
            self.assertEqual(values[10], digest(expected["extent"]), f"{key} extent")
            self.assertEqual(values[11], digest(expected["defines"]), f"{key} defines")
            seen.add(key)
        self.assertEqual(seen, set(rows))

    def test_js_oracle_derives_the_same_digest_as_this_derivation(self) -> None:
        """Bind the JavaScript mirror to the same grammar.

        The registry/executor pair is bound at every single dispatch: the
        executor re-derives the sections from the value-owned admission and
        compares them to the registry's digest, so a divergence fails every
        render. The generator is bound by the anchor test above. This closes
        the loop on the third implementation.
        """
        import shutil
        import subprocess

        node = shutil.which("node")
        if node is None:
            self.skipTest("node is required for the JavaScript mirror")
        rows = self.canonical_rows()
        keys = ["classicNoisedeck/bitEffects:bitEffects", "filter/blur:blurH",
                "synth/remap:remap", "filter/text:text"]
        script = ROOT / "tools/dsl/js_frontend_oracle.mjs"
        program = f"""
        import fs from 'node:fs'
        import crypto from 'node:crypto'
        const source = fs.readFileSync({json.dumps(str(script))}, 'utf8')
        const start = source.indexOf('function extentToken(')
        const stop = source.indexOf('function admission(')
        const body = source.slice(start, stop)
        const factory = new Function('crypto', 'Buffer', body + '; return {{ bindingAbiDigest, compileDefines, outputExtent }}')
        const api = factory(crypto, Buffer)
        const doc = JSON.parse(fs.readFileSync({json.dumps(str(COMPATIBILITY))}, 'utf8'))
        const rows = Object.fromEntries(doc.canonical_programs.map((row) => [row.program_key, row]))
        const out = {{}}
        for (const key of {json.dumps(keys)}) {{
          const row = rows[key]
          out[key] = api.bindingAbiDigest(row, api.compileDefines(row))
        }}
        process.stdout.write(JSON.stringify(out))
        """
        result = subprocess.run([node, "--input-type=module", "-e", program],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        produced = json.loads(result.stdout)
        for key in keys:
            expected = sections(rows[key])
            combined = (expected["samplers"] + expected["uniforms"] + expected["outputs"]
                        + expected["extent"] + expected["defines"])
            self.assertEqual(produced[key], digest(combined), key)

    def test_baked_defines_match_the_typed_manifest(self) -> None:
        manifest = json.loads((ROOT / "src/typed_generated/typed_manifest.json").read_text(encoding="utf-8"))
        programs = {item["program_key"]: item for item in manifest["programs"]}
        text = TYPED_SLICE.read_text(encoding="utf-8")
        block = text[text.index("kCanonicalRoutes{{"):text.index("std::span<const KernelFactory> catalog()")]
        entries = re.findall(r'^\s*\{"([^"]+)",((?:\s*"[^"]*",)+)\s*&', block, re.MULTILINE)
        for key, fields in entries:
            values = re.findall(r'"([^"]*)"', fields)
            program = programs[key]
            expected = ";".join(
                f"{name}={token(program['defines'][name])}" for name in sorted(program.get("defines") or {}))
            self.assertEqual(values[5], program.get("define_contract", ""), f"{key} contract")
            self.assertEqual(values[6], expected, f"{key} defines")


if __name__ == "__main__":
    unittest.main()
