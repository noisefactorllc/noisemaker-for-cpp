"""Contracts for the typed-IR-only native emission slice."""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))


def _task26_parse_executable_tables(cpp: str) -> dict[str, object]:
    import ast

    def braced_after(marker: str, offset: int = 0) -> str:
        marker_offset = cpp.index(marker, offset)
        start = cpp.index("{", marker_offset)
        depth = 0
        quoted = False
        escaped = False
        for offset in range(start, len(cpp)):
            character = cpp[offset]
            if quoted:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    quoted = False
                continue
            if character == '"':
                quoted = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return cpp[start:offset + 1]
        raise AssertionError(f"unterminated initializer after {marker}")

    def initializer(marker: str):
        source = braced_after(marker)
        source = re.sub(r"std::int32_t\{([^{}]+)\}", r"\1", source)
        source = re.sub(
            r"(?<=\b)(0[xX][0-9a-fA-F]+|[0-9]+)U\b", r"\1", source)
        source = re.sub(r"\btrue\b", "True", source)
        source = re.sub(r"\bfalse\b", "False", source)
        value = ast.literal_eval(source.replace("{", "[").replace("}", "]"))
        while (isinstance(value, list) and len(value) == 1 and
               isinstance(value[0], list)):
            value = value[0]
        return value

    enum_source = braced_after("enum class Task26Mutation")
    enum_names = [item.strip() for item in enum_source[1:-1].split(",")
                  if item.strip()]
    render_offset = cpp.index(
        "Task26MutationExecution task26_mutation_render_with_witness")
    switch_source = braced_after("switch (mutation)", render_offset)
    dispatch_names = re.findall(
        r"case Task26Mutation::([a-z0-9_]+)\s*:", switch_source)
    return {
        "cases": initializer("kTask26NativeCases"),
        "names": initializer("kTask26MutationNames"),
        "results": initializer("kTask26MutationResults"),
        "enum_names": enum_names,
        "dispatch_names": dispatch_names,
    }


def _task27_parse_executable_tables(cpp: str) -> dict[str, object]:
    import ast

    def braced_after(marker: str, offset: int = 0) -> str:
        start = cpp.index("{", cpp.index(marker, offset))
        depth = 0
        quoted = False
        escaped = False
        for index in range(start, len(cpp)):
            character = cpp[index]
            if quoted:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    quoted = False
            elif character == '"':
                quoted = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return cpp[start:index + 1]
        raise AssertionError(f"unterminated initializer after {marker}")

    def initializer(marker: str):
        source = braced_after(marker)
        source = re.sub(r"\b(0[xX][0-9a-fA-F]+|[0-9]+)(?:ULL|U)\b", r"\1", source)
        source = re.sub(r"\bfalse\b", "False", source)
        source = re.sub(r"\btrue\b", "True", source)
        value = ast.literal_eval(source.replace("{", "[").replace("}", "]"))
        while isinstance(value, list) and len(value) == 1 and isinstance(value[0], list):
            value = value[0]
        return value

    enum_source = braced_after("enum class Task27WordMode")
    enum_names = [item.strip() for item in enum_source[1:-1].split(",") if item.strip()]
    switch_offset = cpp.index("Task27WordWitness task27_word_with_witness")
    switch_source = braced_after("switch (mode)", switch_offset)
    dispatch_names = re.findall(r"case Task27WordMode::([a-z0-9_]+)\s*:", switch_source)
    return {
        "cases": initializer("kTask27NativeCases"),
        "words": initializer("kTask27WordCases"),
        "enum_names": enum_names,
        "dispatch_names": dispatch_names,
    }


def _task28_parse_executable_tables(cpp: str) -> dict[str, object]:
    import ast
    def braced_after(marker: str, offset: int = 0) -> str:
        start = cpp.index("{", cpp.index(marker, offset)); depth = 0
        quoted = False; escaped = False
        for index in range(start, len(cpp)):
            character = cpp[index]
            if quoted:
                if escaped: escaped = False
                elif character == "\\": escaped = True
                elif character == '"': quoted = False
            elif character == '"': quoted = True
            elif character == "{": depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0: return cpp[start:index + 1]
        raise AssertionError(f"unterminated initializer after {marker}")
    def initializer(marker: str):
        source = braced_after(marker)
        source = re.sub(r"\b(0[xX][0-9a-fA-F]+|[0-9]+)(?:ULL|U)\b", r"\1", source)
        value = ast.literal_eval(source.replace("{", "[").replace("}", "]"))
        while isinstance(value, list) and len(value) == 1 and isinstance(value[0], list):
            value = value[0]
        return value
    def compact(source: str) -> str:
        return re.sub(r"\s+", "", source)

    def enum_values(marker: str) -> list[list[object]]:
        source = braced_after(marker)
        values = []
        for item in source[1:-1].split(","):
            name, numeric_id = item.strip().split("=", 1)
            values.append([name.strip(), int(numeric_id.strip())])
        return values

    helper_marker = "[[nodiscard]] noisemaker::glsl::Mat2 task28_local"
    helper_start = cpp.index(helper_marker)
    helper_body = braced_after(helper_marker)
    helper_source = cpp[helper_start:cpp.index(helper_body, helper_start) + len(helper_body)]
    witness_marker = "[[nodiscard]] Task28MatrixWitness task28_matrix_witness"
    witness_start = cpp.index(witness_marker)
    witness_body = braced_after(witness_marker)
    witness_source = cpp[witness_start:cpp.index(witness_body, witness_start) + len(witness_body)]
    switch_source = braced_after("switch(mode)", witness_start)
    switch_offset = witness_source.index("switch(mode)")
    switch_end = switch_offset + len("switch(mode)") + len(switch_source)
    arm_matches = list(re.finditer(
        r"case\s+Task28MatrixMode::([a-z0-9_]+)\s*:(.*?)"
        r"(?=case\s+Task28MatrixMode::|default\s*:)",
        switch_source, re.DOTALL))
    default_match = re.search(r"default\s*:(.*?)\}\s*$", switch_source, re.DOTALL)
    if default_match is None:
        raise AssertionError("Task28 switch default is missing")
    arms = [[match.group(1), compact(match.group(2))]
            for match in arm_matches]
    shape_by_mode = [[name, "local_return" if
                      "shape=Task28ReturnShape::local_return" in body
                      else "direct_return"] for name, body in arms]
    return {"cases": initializer("kTask28NativeCases"),
            "names": initializer("kTask28ModeNames"),
            "matrices": initializer("kTask28MatrixRows"),
            "mode_enum": enum_values("enum class Task28MatrixMode"),
            "return_shape_enum": enum_values("enum class Task28ReturnShape"),
            "dispatch": [name for name, _ in arms],
            "shape_by_mode": shape_by_mode,
            "helper": compact(helper_source),
            "witness_signature": compact(witness_source[:witness_source.index("{")]),
            "witness_prefix": compact(witness_source[
                witness_source.index("{") + 1:switch_offset]),
            "arms": arms,
            "default": compact(default_match.group(1)),
            "witness_epilogue": compact(witness_source[switch_end:-1])}


def _task29_parse_executable_tables(cpp: str) -> dict[str, object]:
    """Parse Task29's tables and the code that makes their witnesses true."""
    import ast

    def braced_after(marker: str, offset: int = 0) -> str:
        start = cpp.index("{", cpp.index(marker, offset))
        depth = 0
        quoted = False
        escaped = False
        for index in range(start, len(cpp)):
            character = cpp[index]
            if quoted:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    quoted = False
            elif character == '"':
                quoted = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return cpp[start:index + 1]
        raise AssertionError(f"unterminated initializer after {marker}")

    def initializer(marker: str, offset: int = 0):
        source = braced_after(marker, offset)
        source = re.sub(r"\b(0[xX][0-9a-fA-F]+|[0-9]+)(?:ULL|U)\b", r"\1", source)
        source = re.sub(r"(?<![A-Za-z0-9_])([0-9]+\.[0-9]+)f\b",
                        r"\1", source)
        source = re.sub(r"\bfalse\b", "False", source)
        source = re.sub(r"\btrue\b", "True", source)
        value = ast.literal_eval(source.replace("{", "[").replace("}", "]"))
        while isinstance(value, list) and len(value) == 1 and isinstance(value[0], list):
            value = value[0]
        return value

    def compact(source: str) -> str:
        return re.sub(r"\s+", "", source)

    def enum_values(marker: str) -> list[list[object]]:
        values = []
        for item in braced_after(marker)[1:-1].split(","):
            if not item.strip():
                continue
            name, numeric_id = item.strip().split("=", 1)
            values.append([name.strip(), int(numeric_id.strip())])
        return values

    harness_start = cpp.index("// TASK29_DIRECT_ABI_HARNESS_BEGIN")
    harness_end_marker = "// TASK29_DIRECT_ABI_HARNESS_END"
    harness_end_start = cpp.index(harness_end_marker, harness_start)
    harness_end = cpp.index("\n", harness_end_start) + 1
    harness = cpp[harness_start:harness_end]
    table_start = cpp.index("// TASK29_NATIVE_ORACLE_TABLE_BEGIN")
    switch_start = harness.index("// TASK29_DIRECT_ABI_SWITCH_BEGIN")
    switch_end = harness.index("// TASK29_DIRECT_ABI_SWITCH_END", switch_start)
    dispatch_region = harness[switch_start:switch_end]
    switch_source = braced_after("switch (mode)", harness_start)
    arm_matches = list(re.finditer(
        r"case\s+Task29DirectMode::([a-z0-9_]+)\s*:(.*?)"
        r"(?=case\s+Task29DirectMode::|\}\s*$)", switch_source, re.DOTALL))
    signature_body = braced_after("return {", cpp.index(
        "task29_semantic_signature", harness_start))
    expectation_start = cpp.index(
        "TEST(typed_task29_direct_borrow_switch_executes_eight", harness_end)

    def symbolic_array(marker: str) -> list[str]:
        return re.findall(r"Task29[A-Za-z]+::([a-z0-9_]+)",
                          braced_after(marker, expectation_start))

    return {
        "cases": initializer("kTask29Cases"),
        "mode_enum": enum_values("enum class Task29DirectMode"),
        "names": initializer("kTask29DirectModeNames"),
        "declared_ids": initializer("kTask29DeclaredDirectModeIds"),
        "switch_ids": initializer("kTask29SwitchDirectModeIds"),
        "dispatch": [match.group(1) for match in arm_matches],
        "arms": [[match.group(1), compact(match.group(2))]
                 for match in arm_matches],
        "dispatch_prefix": compact(dispatch_region[:dispatch_region.index("switch (mode)")]),
        "dispatch_suffix": compact(dispatch_region[
            dispatch_region.index(switch_source) + len(switch_source):]),
        "semantic_signature": [compact(item) for item in
                               signature_body[1:-1].split(",") if item.strip()],
        "results": initializer("constexpr std::array<std::uint32_t, 8> results",
                               expectation_start),
        "branches": symbolic_array("constexpr std::array<Task29BranchSlot, 8> branches"),
        "abis": symbolic_array("constexpr std::array<Task29AbiKind, 8> abis"),
        "scene_roles": symbolic_array("constexpr std::array<Task29SurfaceRole, 8> scene_roles"),
        "depth_roles": symbolic_array("constexpr std::array<Task29SurfaceRole, 8> depth_roles"),
        "scene_input": initializer("constexpr std::array<bool, 8> scene_input",
                                   expectation_start),
        "scene_tex": initializer("constexpr std::array<bool, 8> scene_tex",
                                 expectation_start),
        "depth_input": initializer("constexpr std::array<bool, 8> depth_input",
                                   expectation_start),
        "depth_tex": initializer("constexpr std::array<bool, 8> depth_tex",
                                 expectation_start),
        "scene_depth": initializer("constexpr std::array<bool, 8> scene_depth",
                                   expectation_start),
        "counters": initializer("constexpr std::array<Task29CounterExpectation, 8> expected_counters",
                                expectation_start),
        "alias_setup": "mode==Task29DirectMode::exact_alias?input:distinct_tex" in compact(harness),
        "copy_implementation": all(token in compact(harness) for token in (
            "scene_copy.emplace(tex.clone())", "depth_copy.emplace(input.clone())",
            "execution.scene==&*scene_copy", "execution.depth==&*depth_copy")),
        "invalid_guard": "invaliddirectABImode" in compact(dispatch_region),
        "harness": compact(harness),
        "authenticated_source": compact(cpp[table_start:harness_end]),
    }


def _task30_parse_executable_tables(cpp: str) -> dict[str, object]:
    """Parse Task30's native oracle/relational tables and dispatch code."""
    import ast

    def braced_after(marker: str, offset: int = 0) -> str:
        start = cpp.index("{", cpp.index(marker, offset))
        depth = 0
        quoted = False
        escaped = False
        for index in range(start, len(cpp)):
            character = cpp[index]
            if quoted:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    quoted = False
            elif character == '"':
                quoted = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return cpp[start:index + 1]
        raise AssertionError(f"unterminated initializer after {marker}")

    def initializer(marker: str, offset: int = 0):
        source = braced_after(marker, offset)
        source = re.sub(r"\b(0[xX][0-9a-fA-F]+|[0-9]+)(?:ULL|U)\b", r"\1", source)
        source = re.sub(r"(?<![A-Za-z0-9_])([0-9]+\.[0-9]+)f\b", r"\1", source)
        source = re.sub(r"\bfalse\b", "False", source)
        source = re.sub(r"\btrue\b", "True", source)
        value = ast.literal_eval(source.replace("{", "[").replace("}", "]"))
        while isinstance(value, list) and len(value) == 1 and isinstance(value[0], list):
            value = value[0]
        return value

    def compact(source: str) -> str:
        return re.sub(r"\s+", "", source)

    def enum_values(marker: str) -> list[list[object]]:
        values = []
        for item in braced_after(marker)[1:-1].split(","):
            if not item.strip():
                continue
            name, numeric_id = item.strip().split("=", 1)
            values.append([name.strip(), int(numeric_id.strip())])
        return values

    table_start = cpp.index("// TASK30_NATIVE_ORACLE_TABLE_BEGIN")
    harness_start = cpp.index("// TASK30_DIRECT_ABI_HARNESS_BEGIN")
    harness_end_marker = "// TASK30_DIRECT_ABI_HARNESS_END"
    harness_end = cpp.index("\n", cpp.index(harness_end_marker, harness_start)) + 1
    harness = cpp[harness_start:harness_end]
    switch_start = harness.index("// TASK30_DIRECT_ABI_SWITCH_BEGIN")
    switch_end = harness.index("// TASK30_DIRECT_ABI_SWITCH_END", switch_start)
    dispatch_region = harness[switch_start:switch_end]
    switch_source = braced_after("switch (mode)", harness_start)
    arm_matches = list(re.finditer(
        r"case\s+Task30RelationalMode::([a-z0-9_]+)\s*:(.*?)"
        r"(?=case\s+Task30RelationalMode::|\}\s*$)", switch_source, re.DOTALL))
    guard_source = compact(dispatch_region[
        dispatch_region.index(switch_source) + len(switch_source):])
    signature_start = cpp.index("task30_relational_signature", harness_start)
    signature_body = braced_after("{", signature_start)
    signature_fields = [compact(item) for item in re.findall(
        r"signature\[cursor\+\+\]\s*=\s*(.*?);", signature_body)]

    return {
        "cases": initializer("kTask30NativeCases"),
        "relational_rows": initializer("kTask30RelationalRows"),
        "mode_enum": enum_values("enum class Task30RelationalMode"),
        "names": initializer("kTask30RelationalModeNames"),
        "dispatch": [match.group(1) for match in arm_matches],
        "arms": [[match.group(1), compact(match.group(2))]
                 for match in arm_matches],
        "signature_fields": signature_fields,
        "guard": guard_source,
        "authenticated_source": compact(cpp[table_start:harness_end]),
    }


class TypedGeneratorTests(unittest.TestCase):
    @staticmethod
    def tree_bytes(root: pathlib.Path) -> dict[str, bytes]:
        return {str(path.relative_to(root)): path.read_bytes() for path in sorted(root.rglob("*"))
                if path.is_file() and not path.is_symlink()}

    def test_task25_cpp_native_oracle_table_is_exact_frozen_transcription(self) -> None:
        import hashlib

        oracle_path = pathlib.Path(
            REPOSITORY / "tests/oracles/task-25-oracles.json")
        self.assertTrue(oracle_path.is_file(), "Task 25 frozen oracle JSON is required")
        oracle_bytes = oracle_path.read_bytes()
        self.assertEqual(
            "09d8d8a9667fe3b3b90cd582e501b7c0a61d2a41e65ea2d175771a105e32e116",
            hashlib.sha256(oracle_bytes).hexdigest())
        oracle = json.loads(oracle_bytes)

        cpp = (REPOSITORY / "tests/test_generated_kernels.cpp").read_text()
        begin = "// TASK25_NATIVE_ORACLE_TABLE_BEGIN"
        end = "// TASK25_NATIVE_ORACLE_TABLE_END"
        self.assertEqual(1, cpp.count(begin))
        self.assertEqual(1, cpp.count(end))
        match = re.search(
            r'constexpr std::string_view kTask25OracleTableJson = R"TASK25\(\n'
            r'(.*?)'
            r'\n\)TASK25";',
            cpp[cpp.index(begin) + len(begin):cpp.index(end)], re.DOTALL)
        self.assertIsNotNone(match)
        embedded_bytes = (match.group(1) + "\n").encode()
        self.assertEqual(oracle_bytes, embedded_bytes)
        embedded = json.loads(embedded_bytes)

        self.assertEqual(oracle["schema"], embedded["schema"])
        self.assertEqual(oracle["fixture"], embedded["fixture"])
        self.assertEqual(oracle["programs"], embedded["programs"])
        self.assertEqual(oracle["cases"], embedded["cases"])
        self.assertEqual(oracle["mutations"], embedded["mutations"])
        self.assertEqual(6, len(embedded["cases"]))
        self.assertEqual(11, len(embedded["mutations"]))
        self.assertEqual(
            ["classicNoisedeck/lensDistortion:lensDistortion",
             "filter/prismaticAberration:prismaticAberration"],
            [embedded["programs"][name]["key"] for name in ("lens", "prism")])
        self.assertEqual(
            [
                "inputTex:sampler2D@1/S1", "resolution:vec2@2",
                "tileOffset:vec2@3", "fullResolution:vec2@4", "time:float@5",
                "aspectLens:bool@6", "shape:int@7", "tint:vec3@8",
                "alpha:float@9", "vignetteAmt:float@10", "distortion:float@11",
                "speed:float@12", "loopScale:float@13", "aberration:float@14",
                "hueRotation:float@15", "hueRange:float@16", "mode:int@17",
                "modulate:bool@18", "blendMode:int@19", "saturation:float@20",
                "passthru:float@21", "fragColor:vec4@22/out",
            ], embedded["programs"]["lens"]["bindings"])
        self.assertEqual(
            [
                "inputTex:sampler2D@1/S1", "resolution:vec2@2",
                "tileOffset:vec2@3", "fullResolution:vec2@4", "time:float@5",
                "aberrationAmt:float@6", "hueRotation:float@7",
                "hueRange:float@8", "modulate:bool@9", "saturation:float@10",
                "passthru:float@11", "fragColor:vec4@12/out",
            ], embedded["programs"]["prism"]["bindings"])
        self.assertEqual(
            {
                "samplers": 1, "ordinary_uniforms": 20, "outputs": 1,
                "uses_texture": True, "uses_derivatives": False,
                "static_texture_sites": 3,
                "dynamic_texture_calls_per_pixel": 3,
                "texture_size_calls_per_pixel": 0,
            }, embedded["programs"]["lens"]["resources"])
        self.assertEqual(
            {
                "samplers": 1, "ordinary_uniforms": 10, "outputs": 1,
                "uses_texture": True, "uses_derivatives": False,
                "static_texture_sites": 3,
                "dynamic_texture_calls_per_pixel": 3,
                "texture_size_calls_per_pixel": 1,
            }, embedded["programs"]["prism"]["resources"])

        generated = (REPOSITORY / "src/typed_generated/typed_slice.cpp").read_text()
        contracts = (
            ("classicNoisedeck/lensDistortion:lensDistortion",
             "classicNoisedeck/refract:refract",
             ["_distance", "hsv2rgb", "hsv2rgb2", "map", "rgb2hsv",
              "rgb2hsv2", "saturate"], 0),
            ("filter/prismaticAberration:prismaticAberration",
             "filter/reindex:nmReindexApply",
             ["hsv2rgb", "map", "rgb2hsv", "saturate"], 1),
        )
        for key, next_key, helpers, texture_sizes in contracts:
            begin = generated.index(f"// Typed IR program: {key}")
            finish = generated.index(f"// Typed IR program: {next_key}", begin)
            block = generated[begin:finish]
            pixel = block[block.index("void pixel("):
                          block.index("}  // namespace")]
            self.assertEqual(3, pixel.count("sample_texture("), key)
            self.assertEqual(texture_sizes, pixel.count("texture_size("), key)
            self.assertEqual(helpers, re.findall(
                r'\[\[nodiscard\]\] (?:double|glsl::Vec[234]) '
                r'([A-Za-z_]\w*)\([^;{]*\) noexcept;', block), key)
            self.assertNotRegex(
                pixel,
                r"operator\[\]|hsv\[|\b(?:new|throw|alloca)\b|"
                r"std::(?:vector|variant|function|allocator|string)|"
                r"\b(?:for|while)\s*\(|"
                r"\(\s*\*\s*[A-Za-z_]\w*\s*\)",
                key)

    def test_task24_gather_sorted_identity_profile_owns_exact_parent_and_round(self) -> None:
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.gather_sorted_round_profile import (
            GATHER_SORTED_KEY, PROFILE,
            apply_gather_sorted_round_to_int,
            authenticate_gather_sorted_round_to_int)
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == GATHER_SORTED_KEY)
        raw = (root / entry["source"]).read_text()
        typed = analyze_program(parse_program(raw, GATHER_SORTED_KEY, {}),
                                GATHER_SORTED_KEY)

        parent, round_value = authenticate_gather_sorted_round_to_int(
            typed, entry["raw_sha256"], PROFILE)
        self.assertIs(parent.children[0], round_value)
        self.assertEqual("construct", parent.kind)
        self.assertEqual("int", parent.constructor_type.display())
        self.assertEqual("round", round_value.callee)
        self.assertEqual(-38, round_value.signature_id)
        self.assertEqual(
            "a5f412a1949fdfae93b759bf1c01a22afb44f9a48e71710f2c54cdcdf312c625",
            hashlib.sha256(repr(round_value).encode()).hexdigest())
        profiled = apply_gather_sorted_round_to_int(
            typed, entry["raw_sha256"], PROFILE)
        self.assertIs(typed, profiled)
        self.assertIs(profiled, apply_gather_sorted_round_to_int(
            profiled, entry["raw_sha256"], PROFILE))

        generate_typed_slice.validate_capabilities(
            profiled, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=entry["raw_sha256"],
            gather_sorted_round_profile=PROFILE)
        emitted = render_typed_cpp(
            profiled, GATHER_SORTED_KEY, entry["raw_sha256"],
            gather_sorted_round_profile=PROFILE)
        nested = "glsl::detail::float_to_int32(glsl::round("
        self.assertEqual(1, emitted.count(nested))
        self.assertNotIn("std::int32_t(glsl::round(", emitted)
        self.assertNotIn("static_cast<std::int32_t>(glsl::round(", emitted)
        self.assertNotIn("\"round\"", generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertNotIn("round", generate_typed_slice._BUILTINS)

    def test_task24_loader_carries_only_gather_profile_and_generates_one_new_block(self) -> None:
        import copy
        import hashlib
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.gather_sorted_round_profile import (
            GATHER_SORTED_KEY, PROFILE)
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import KEYS

        spec = copy.deepcopy(generate_typed_slice.load_slice(REPOSITORY))
        spec["programs"] = [item for item in spec["programs"]
                            if item["program_key"] not in KEYS
                            and item["program_key"] != "filter/smooth:smoothEdge"
                            and item["program_key"] != "synth/perlin:perlin"
                            and item["program_key"] != "filter/rotate:rot"
                            and item["program_key"] != "mixer/focusBlur:focusBlur"
                            and item["program_key"] != "filter/extrude:extrude"
                            and item["program_key"] != "synth/curl:curl"
                            and item["program_key"] != "filter/grade:creative"
                            and item["program_key"] != "filter/grade:hslSecondary"
                            and item["program_key"] != "filter/grade:lut"
                            and item["program_key"] != "filter/grade:primary"
                            and item["program_key"] != "filter/grade:vignette"
                            and item["program_key"] != "filter/grade:wheels"]
        self.assertEqual(123, len(spec["programs"]))
        self.assertEqual(51, next(index for index, item in enumerate(
            spec["programs"]) if item["program_key"] == GATHER_SORTED_KEY))
        carriers = [(item["program_key"], item.get("gather_sorted_round_profile"))
                    for item in spec["programs"]
                    if "gather_sorted_round_profile" in item]
        self.assertEqual([(GATHER_SORTED_KEY, PROFILE)], carriers)
        self.assertNotIn("round", spec["capabilities"])
        self.assertNotIn("round", generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertNotIn("round", generate_typed_slice._BUILTINS)

        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=spec):
            outputs = generate_typed_slice.generate_outputs(REPOSITORY)
        cpp = outputs["src/typed_generated/typed_slice.cpp"].decode()
        manifest = json.loads(outputs[
            "src/typed_generated/typed_manifest.json"].decode())
        self.assertEqual(123, len(manifest["programs"]))
        self.assertEqual(1, cpp.count(
            "// Typed IR program: filter/pixelSort:gatherSorted"))
        self.assertEqual(1, cpp.count(
            "glsl::detail::float_to_int32(glsl::round("))
        keys = [item["program_key"] for item in manifest["programs"]]
        self.assertEqual(
            "df7750a48a77733e50f0e20072e291c2404e761932f6df8ddbcf8793d58fb6ac",
            hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest())

    def test_task24_emitter_initializes_empty_authorization_for_non_gather_programs(self) -> None:
        from tools.glslcpp import check_corpus
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        key = "filter/bc:bc"
        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == key)
        raw = (corpus / entry["source"]).read_text()
        typed = analyze_program(parse_program(raw, key, {}), key)
        emitted = render_typed_cpp(typed, key, entry["raw_sha256"])
        self.assertIn("namespace typed_kernel {", emitted)
        self.assertNotIn("glsl::round(", emitted)

    def test_task24_four_mode_caller_and_complete_profile_forgery_matrix(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.gather_sorted_round_profile import (
            GATHER_SORTED_KEY, PROFILE,
            apply_gather_sorted_round_to_int)
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.semantic_types import FLOAT, INT, vector

        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == GATHER_SORTED_KEY)
        exact = analyze_program(parse_program(
            (corpus / entry["source"]).read_text(), GATHER_SORTED_KEY, {}),
            GATHER_SORTED_KEY)
        source_hash = entry["raw_sha256"]

        def accepted(candidate, carrier, caller_hash=source_hash,
                     capabilities=generate_typed_slice.APPROVED_CAPABILITIES,
                     *, compatibility=None, numeric="glsl-f32"):
            results = []
            try:
                generate_typed_slice.validate_capabilities(
                    candidate, capabilities, source_hash=caller_hash,
                    compatibility_transform=compatibility,
                    numeric_literal_contract=numeric,
                    gather_sorted_round_profile=carrier)
                results.append(True)
            except generate_typed_slice.GeneratorError:
                results.append(False)
            try:
                render_typed_cpp(
                    candidate, candidate.key, caller_hash,
                    compatibility_transform=compatibility,
                    numeric_literal_contract=numeric,
                    gather_sorted_round_profile=carrier)
                results.append(True)
            except TypedEmissionError:
                results.append(False)
            return tuple(results)

        def replace_site(program, *, round_change=lambda value: value,
                         parent_change=lambda value: value,
                         declaration_change=lambda value: value,
                         statement_change=lambda value: value):
            function = program.functions[0]
            statement = function.body[6]
            declaration = statement.expressions[0]
            parent = declaration.children[0]
            round_value = parent.children[0]
            changed_round = round_change(round_value)
            changed_parent = parent_change(dataclasses.replace(
                parent, children=(changed_round,)))
            changed_declaration = declaration_change(dataclasses.replace(
                declaration, children=(changed_parent,)))
            changed_statement = statement_change(dataclasses.replace(
                statement, expressions=(changed_declaration,)))
            body = (*function.body[:6], changed_statement, *function.body[7:])
            changed_function = dataclasses.replace(function, body=body)
            return dataclasses.replace(
                program, functions=(changed_function, *program.functions[1:]))

        profiled = apply_gather_sorted_round_to_int(exact, source_hash, PROFILE)
        self.assertIs(exact, profiled)
        self.assertIs(exact, apply_gather_sorted_round_to_int(
            profiled, source_hash, PROFILE))
        self.assertEqual((False, False), accepted(exact, None))
        self.assertEqual((False, False), accepted(exact, "wrong"))
        self.assertEqual((True, True), accepted(exact, PROFILE))
        self.assertEqual((False, False), accepted(
            exact, PROFILE, compatibility="crt-metal-sine-v1"))
        self.assertEqual((False, False), accepted(
            exact, PROFILE, numeric="source-double"))
        self.assertEqual((False, False), accepted(exact, PROFILE, None))
        self.assertEqual((False, False), accepted(exact, PROFILE, "0" * 64))
        self.assertEqual((False, True), accepted(
            exact, PROFILE, capabilities=(*generate_typed_slice.APPROVED_CAPABILITIES,
                                          "round")))

        round_mutations = {
            "missing-round": lambda value: value.children[0],
            "duplicate-round": lambda value: dataclasses.replace(
                value, children=(value,)),
            "vector-round": lambda value: dataclasses.replace(
                value, type=vector("float", 2)),
            "round-span": lambda value: dataclasses.replace(
                value, span=dataclasses.replace(
                    value.span, start_column=value.span.start_column + 1)),
            "round-callee-floor": lambda value: dataclasses.replace(
                value, callee="floor"),
            "round-callee-ceil": lambda value: dataclasses.replace(
                value, callee="ceil"),
            "round-callee-std": lambda value: dataclasses.replace(
                value, callee="std::round"),
            "round-callee-lround": lambda value: dataclasses.replace(
                value, callee="lround"),
            "round-callee-nearbyint": lambda value: dataclasses.replace(
                value, callee="nearbyint"),
            "round-signature": lambda value: dataclasses.replace(
                value, signature_id=-37),
            "round-result-type": lambda value: dataclasses.replace(
                value, type=INT),
            "round-category": lambda value: dataclasses.replace(
                value, category="lvalue"),
            "round-argument-type": lambda value: dataclasses.replace(
                value, children=(dataclasses.replace(
                    value.children[0], type=INT),)),
            "round-argument-hash": lambda value: dataclasses.replace(
                value, children=(dataclasses.replace(
                    value.children[0], category="lvalue"),)),
            "round-arity": lambda value: dataclasses.replace(
                value, children=(*value.children, value.children[0])),
        }
        forged_rounds = {}
        for name, mutate in round_mutations.items():
            candidate = replace_site(exact, round_change=mutate)
            forged_rounds[name] = candidate
            self.assertNotEqual(exact.functions, candidate.functions, name)
            with self.subTest(mutation=name, carrier=None):
                self.assertEqual((False, False), accepted(candidate, None))
            with self.subTest(mutation=name, carrier="wrong"):
                self.assertEqual((False, False), accepted(candidate, "wrong"))
            with self.subTest(mutation=name, carrier=PROFILE):
                self.assertEqual((False, False), accepted(candidate, PROFILE))

        parent_mutations = {
            "non-int-parent": lambda value: dataclasses.replace(
                value, constructor_type=FLOAT, type=FLOAT),
            "parent-arity": lambda value: dataclasses.replace(
                value, children=(*value.children, value.children[0])),
            "parent-span": lambda value: dataclasses.replace(
                value, span=dataclasses.replace(
                    value.span, end_column=value.span.end_column - 1)),
            "parent-generic-cast": lambda value: dataclasses.replace(
                value, kind="cast"),
        }
        declaration_mutations = {
            "declaration-symbol-id": lambda value: dataclasses.replace(
                value, symbol_id=113),
            "declaration-name": lambda value: dataclasses.replace(
                value, symbol=dataclasses.replace(value.symbol, name="notBrightestX")),
            "declaration-type": lambda value: dataclasses.replace(value, type=FLOAT),
            "declaration-storage": lambda value: dataclasses.replace(
                value, symbol=dataclasses.replace(value.symbol, storage="global")),
            "declaration-writable": lambda value: dataclasses.replace(
                value, symbol=dataclasses.replace(value.symbol, writable=False)),
            "declaration-observable-float": lambda value: dataclasses.replace(
                value, type=FLOAT, symbol=dataclasses.replace(
                    value.symbol, type=FLOAT)),
        }
        statement_mutations = {
            "statement-span": lambda value: dataclasses.replace(
                value, span=dataclasses.replace(
                    value.span, start_column=value.span.start_column + 1)),
            "statement-kind-return": lambda value: dataclasses.replace(
                value, kind="return"),
            "statement-extra-expression": lambda value: dataclasses.replace(
                value, expressions=(*value.expressions, value.expressions[0])),
        }
        structured = {}
        structured.update((name, replace_site(exact, parent_change=change))
                          for name, change in parent_mutations.items())
        structured.update((name, replace_site(exact, declaration_change=change))
                          for name, change in declaration_mutations.items())
        structured.update((name, replace_site(exact, statement_change=change))
                          for name, change in statement_mutations.items())
        function = exact.functions[0]
        moved = list(function.body)
        moved[6], moved[7] = moved[7], moved[6]
        structured["moved-round-statement"] = dataclasses.replace(
            exact, functions=(dataclasses.replace(function, body=tuple(moved)),))
        for name, candidate in structured.items():
            with self.subTest(structural_mutation=name):
                self.assertEqual((False, False), accepted(candidate, PROFILE))

        program_mutations = {
            "key": dataclasses.replace(exact, key="filter/posterize:posterize"),
            "normalized-source": dataclasses.replace(exact, source=exact.source + "\n"),
            "defines": dataclasses.replace(
                exact, preprocessor_defines=(("MODE", 1),)),
            "function-tuple": dataclasses.replace(exact, functions=()),
            "whole-program": dataclasses.replace(exact, body_status="forged"),
            "interface-declarations": dataclasses.replace(
                exact, declarations=tuple(reversed(exact.declarations))),
            "resource-derivative": dataclasses.replace(
                exact, resources=dataclasses.replace(
                    exact.resources, uses_derivatives=True)),
            "program-loop-proof": dataclasses.replace(
                exact, counted_loop_proof=dataclasses.replace(
                    exact.counted_loop_proof,
                    entrypoint_charge=exact.counted_loop_proof.entrypoint_charge + 1)),
        }
        loop_statement = function.body[12]
        self.assertEqual("for", loop_statement.kind)
        loop_body = list(function.body)
        loop_body[12] = dataclasses.replace(
            loop_statement, loop_proof=dataclasses.replace(
                loop_statement.loop_proof,
                trip_count=loop_statement.loop_proof.trip_count - 1))
        program_mutations["loop-proof"] = dataclasses.replace(
            exact, functions=(dataclasses.replace(function, body=tuple(loop_body)),))
        for name, candidate in program_mutations.items():
            with self.subTest(program_mutation=name):
                self.assertEqual((False, False), accepted(candidate, PROFILE))

        forged_raw = dataclasses.replace(exact, raw_source=exact.raw_source + "\n")
        attacker_hash = hashlib.sha256(
            forged_raw.raw_source.encode("utf-8")).hexdigest()
        self.assertNotEqual(source_hash, attacker_hash)
        self.assertEqual((False, False), accepted(
            forged_raw, PROFILE, attacker_hash))

        foreign = dataclasses.replace(exact, key="filter/posterize:posterize")
        self.assertEqual((False, False), accepted(foreign, PROFILE))

    def test_task24_loader_negative_profile_matrix_is_closed(self) -> None:
        import copy
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.gather_sorted_round_profile import (
            GATHER_SORTED_KEY, PROFILE)

        original = json.loads(
            (REPOSITORY / "tools/glslcpp/typed_slice.json").read_text())
        gather = next(item for item in original["programs"]
                      if item["program_key"] == GATHER_SORTED_KEY)
        foreign_key = next(item["program_key"] for item in original["programs"]
                           if item["program_key"] != GATHER_SORTED_KEY)
        mutations = {}
        changed = copy.deepcopy(original); del next(
            item for item in changed["programs"]
            if item["program_key"] == GATHER_SORTED_KEY)["gather_sorted_round_profile"]
        mutations["absent"] = changed
        changed = copy.deepcopy(original); next(
            item for item in changed["programs"]
            if item["program_key"] == GATHER_SORTED_KEY
        )["gather_sorted_round_profile"] = "wrong"
        mutations["wrong"] = changed
        changed = copy.deepcopy(original); changed["programs"].append(copy.deepcopy(gather)); changed["programs"].sort(key=lambda item: item["program_key"])
        mutations["duplicate"] = changed
        changed = copy.deepcopy(original); next(
            item for item in changed["programs"]
            if item["program_key"] == foreign_key
        )["gather_sorted_round_profile"] = PROFILE
        mutations["foreign"] = changed
        changed = copy.deepcopy(original); next(
            item for item in changed["programs"]
            if item["program_key"] == GATHER_SORTED_KEY)["extra"] = True
        mutations["extra-field"] = changed
        changed = copy.deepcopy(original); changed["compatibility_transforms"][
            GATHER_SORTED_KEY] = "crt-metal-sine-v1"
        mutations["compatibility-carrier"] = changed
        changed = copy.deepcopy(original); changed["capabilities"].append("round")
        mutations["global-round-capability"] = changed

        for name, payload in mutations.items():
            with self.subTest(loader_mutation=name), tempfile.TemporaryDirectory() as temporary:
                repository = pathlib.Path(temporary)
                path = repository / "tools/glslcpp/typed_slice.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(payload))
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.load_slice(repository)

    def test_task24_design_section_six_forgery_and_driver_matrix_is_closed(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import FrontendError, parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.gather_sorted_round_profile import (
            GATHER_SORTED_KEY, PROFILE,
            authenticate_gather_sorted_round_to_int)
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.semantic_types import BOOL, FLOAT
        from tools.glslcpp.frontend.typed_ir import UniformBlock

        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == GATHER_SORTED_KEY)
        raw = (corpus / entry["source"]).read_text()
        exact = analyze_program(parse_program(raw, GATHER_SORTED_KEY, {}),
                                GATHER_SORTED_KEY)
        source_hash = entry["raw_sha256"]
        function = exact.functions[0]
        statement = function.body[6]
        declaration = statement.expressions[0]
        parent = declaration.children[0]
        round_value = parent.children[0]
        argument = round_value.children[0]
        loop = function.body[12]
        self.assertEqual(("round", -38, "float", 64),
                         (round_value.callee, round_value.signature_id,
                          round_value.type.display(), loop.loop_proof.trip_count))

        def program_with_body(body):
            return dataclasses.replace(
                exact, functions=(dataclasses.replace(function, body=tuple(body)),))

        def program_with_statement(changed):
            body = list(function.body); body[6] = changed
            return program_with_body(body)

        def program_with_declaration(changed):
            return program_with_statement(dataclasses.replace(
                statement, expressions=(changed,)))

        def program_with_parent(changed):
            return program_with_declaration(dataclasses.replace(
                declaration, children=(changed,)))

        def program_with_round(changed):
            return program_with_parent(dataclasses.replace(
                parent, children=(changed,)))

        def program_with_loop(changed):
            body = list(function.body); body[12] = changed
            return program_with_body(body)

        observable = {
            "round-stored-float": program_with_declaration(dataclasses.replace(
                declaration, type=FLOAT,
                symbol=dataclasses.replace(declaration.symbol, type=FLOAT),
                children=(round_value,))),
            "round-returned": program_with_statement(dataclasses.replace(
                statement, kind="return", expressions=(round_value,))),
            "round-compared": program_with_declaration(dataclasses.replace(
                declaration, type=BOOL,
                symbol=dataclasses.replace(declaration.symbol, type=BOOL),
                children=(dataclasses.replace(
                    parent, kind="binary", type=BOOL, constructor_type=None,
                    operator=">", children=(round_value, argument)),))),
            "round-passed": program_with_parent(dataclasses.replace(
                parent, kind="call", type=FLOAT, constructor_type=None,
                callee="forgedConsumer", signature_id=5,
                children=(round_value,))),
            "declaration-owner": program_with_declaration(dataclasses.replace(
                declaration, symbol=dataclasses.replace(
                    declaration.symbol, id=113), symbol_id=113)),
            "declaration-initializer-missing": program_with_declaration(
                dataclasses.replace(declaration, children=())),
            "declaration-initializer-extra": program_with_declaration(
                dataclasses.replace(declaration,
                                    children=(parent, parent))),
        }

        loop_forged = {}
        loop_changes = {
            "loop-induction": {"induction_symbol_id": 119},
            "loop-start": {"start_value": 1},
            "loop-comparison-proof": {"comparison": "<="},
            "loop-update-proof": {"update": "--"},
            "loop-bound-value": {"bound_value": 63},
            "loop-bound-kind": {"bound_kind": "literal"},
            "loop-trip-count": {"trip_count": 63},
            "loop-lexical-depth": {"lexical_depth": 2},
            "loop-effective-depth": {"effective_depth": 2},
            "loop-product": {"lexical_product": 63},
            "loop-charge": {"entrypoint_charge": 63},
        }
        for name, changes in loop_changes.items():
            loop_forged[name] = program_with_loop(dataclasses.replace(
                loop, loop_proof=dataclasses.replace(loop.loop_proof, **changes)))
        initializer = loop.children[0]
        init_decl = initializer.expressions[0]
        init_literal = init_decl.children[0]
        changed_init = dataclasses.replace(
            initializer, expressions=(dataclasses.replace(
                init_decl, children=(dataclasses.replace(
                    init_literal, literal="1", literal_value=1),)),))
        loop_forged["loop-start-expression"] = program_with_loop(
            dataclasses.replace(loop, children=(changed_init, loop.children[1])))
        condition, update = loop.expressions
        loop_forged["loop-comparison-expression"] = program_with_loop(
            dataclasses.replace(loop, expressions=(dataclasses.replace(
                condition, operator="<="), update)))
        loop_forged["loop-update-expression"] = program_with_loop(
            dataclasses.replace(loop, expressions=(condition, dataclasses.replace(
                update, operator="--"))))
        bound = condition.children[1]
        loop_forged["loop-bound-expression"] = program_with_loop(
            dataclasses.replace(loop, expressions=(dataclasses.replace(
                condition, children=(condition.children[0], dataclasses.replace(
                    bound, symbol_id=16,
                    symbol=dataclasses.replace(bound.symbol, name="FORGED_BOUND"))),),
                                                   update)))
        loop_block = loop.children[1]
        loop_forged["loop-return"] = program_with_loop(dataclasses.replace(
            loop, children=(initializer, dataclasses.replace(
                loop_block, children=(*loop_block.children,
                                      dataclasses.replace(statement, kind="return"))))))
        loop_forged["loop-break"] = program_with_loop(dataclasses.replace(
            loop, children=(initializer, dataclasses.replace(
                loop_block, children=(*loop_block.children,
                                      dataclasses.replace(statement, kind="break",
                                                          expressions=()))))))

        program_proofs = {}
        for name, changes in {
                "program-loop-count": {"loop_count": 2},
                "program-unproved-loop": {"unproved_loop_count": 1},
                "program-depth": {"max_effective_depth": 2},
                "program-product": {"max_lexical_product": 63},
                "program-charge": {"entrypoint_charge": 63},
                "program-call-cycle": {"call_graph_acyclic": False},
        }.items():
            program_proofs[name] = dataclasses.replace(
                exact, counted_loop_proof=dataclasses.replace(
                    exact.counted_loop_proof, **changes))

        first_declaration = exact.declarations[0]
        interface = {
            "missing-declaration": dataclasses.replace(
                exact, declarations=exact.declarations[1:]),
            "extra-declaration": dataclasses.replace(
                exact, declarations=(*exact.declarations, first_declaration)),
            "global": dataclasses.replace(
                exact, declarations=(dataclasses.replace(
                    first_declaration, symbol=dataclasses.replace(
                        first_declaration.symbol, storage="global")),
                                     *exact.declarations[1:])),
            "varying": dataclasses.replace(
                exact, interface_symbols=(first_declaration.symbol,)),
            "uniform-block": dataclasses.replace(
                exact, uniform_blocks=(UniformBlock(
                    900, "ForgedBlock", None, (), first_declaration.span),)),
            "derivative": dataclasses.replace(
                exact, resources=dataclasses.replace(
                    exact.resources, uses_derivatives=True)),
            "missing-sampler": dataclasses.replace(
                exact, resources=dataclasses.replace(
                    exact.resources,
                    uniforms=exact.resources.uniforms[1:],
                    samplers=exact.resources.samplers[1:])),
            "extra-sampler": dataclasses.replace(
                exact, resources=dataclasses.replace(
                    exact.resources,
                    uniforms=(*exact.resources.uniforms, "forgedTex"),
                    samplers=(*exact.resources.samplers, "forgedTex"))),
            "missing-output": dataclasses.replace(
                exact, resources=dataclasses.replace(
                    exact.resources, outputs=())),
            "extra-output": dataclasses.replace(
                exact, resources=dataclasses.replace(
                    exact.resources, outputs=(*exact.resources.outputs,
                                             "forgedOutput"))),
            "extra-function": dataclasses.replace(
                exact, functions=(*exact.functions, function)),
            "array": dataclasses.replace(
                exact, local_type_names=(*exact.local_type_names, "float[2]")),
        }

        def replace_first_fetch(program):
            replaced = 0
            def expression(value):
                nonlocal replaced
                children = tuple(expression(child) for child in value.children)
                result = (value if all(left is right for left, right in
                                       zip(children, value.children))
                          else dataclasses.replace(value, children=children))
                if (replaced == 0 and result.kind == "builtin"
                        and result.callee == "texelFetch"):
                    replaced += 1
                    return dataclasses.replace(result, callee="texture")
                return result
            def visit(value):
                expressions = tuple(expression(item) for item in value.expressions)
                children = tuple(visit(item) for item in value.children)
                return dataclasses.replace(value, expressions=expressions,
                                           children=children)
            candidate = program_with_body(visit(item) for item in function.body)
            self.assertEqual(1, replaced)
            return candidate
        interface["changed-fetch"] = replace_first_fetch(exact)

        raw_source_drift = dataclasses.replace(
            exact, raw_source=exact.raw_source + "\n// authenticated-byte-drift\n")
        all_forgeries = {**observable, **loop_forged, **program_proofs,
                         **interface, "raw-source-drift": raw_source_drift}

        exact_callers = {
            "exact": source_hash,
            "missing": None,
            "wrong": "0" * 64,
            "attacker-updated": hashlib.sha256(
                exact.raw_source.encode()).hexdigest(),
        }
        self.assertEqual(source_hash, exact_callers["attacker-updated"])
        for carrier_name, carrier in (
                ("absent", None), ("wrong", "wrong"), ("exact", PROFILE)):
            for caller_name, caller_hash in exact_callers.items():
                accepted_control = (carrier_name == "exact"
                                    and caller_name in {"exact", "attacker-updated"})
                label = (f"exact-control/carrier={carrier_name}/"
                         f"caller={caller_name}")
                if accepted_control:
                    with self.subTest(target=label, boundary="validator"):
                        generate_typed_slice.validate_capabilities(
                            exact, generate_typed_slice.APPROVED_CAPABILITIES,
                            source_hash=caller_hash,
                            gather_sorted_round_profile=carrier)
                    with self.subTest(target=label, boundary="emitter"):
                        render_typed_cpp(
                            exact, exact.key, caller_hash,
                            gather_sorted_round_profile=carrier)
                else:
                    with self.subTest(target=label, boundary="validator"), self.assertRaises(
                            generate_typed_slice.GeneratorError):
                        generate_typed_slice.validate_capabilities(
                            exact, generate_typed_slice.APPROVED_CAPABILITIES,
                            source_hash=caller_hash,
                            gather_sorted_round_profile=carrier)
                    with self.subTest(target=label, boundary="emitter"), self.assertRaises(
                            TypedEmissionError):
                        render_typed_cpp(
                            exact, exact.key, caller_hash,
                            gather_sorted_round_profile=carrier)

        def reject(candidate, name):
            self.assertNotEqual(exact, candidate, name)
            with self.subTest(mutation=name, boundary="helper"), self.assertRaises(
                    ValueError):
                authenticate_gather_sorted_round_to_int(
                    candidate, source_hash, PROFILE)
            caller_hashes = {
                "exact": source_hash,
                "missing": None,
                "wrong": "0" * 64,
                "attacker-updated": hashlib.sha256(
                    candidate.raw_source.encode()).hexdigest(),
            }
            if name == "raw-source-drift":
                self.assertNotEqual(source_hash,
                                    caller_hashes["attacker-updated"])
            for carrier_name, carrier in (
                    ("absent", None), ("wrong", "wrong"), ("exact", PROFILE)):
                for caller_name, caller_hash in caller_hashes.items():
                    label = (f"{name}/carrier={carrier_name}/"
                             f"caller={caller_name}")
                    with self.subTest(target=label, boundary="validator"), self.assertRaises(
                            generate_typed_slice.GeneratorError):
                        generate_typed_slice.validate_capabilities(
                            candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                            source_hash=caller_hash,
                            gather_sorted_round_profile=carrier)
                    with self.subTest(target=label, boundary="emitter"), self.assertRaises(
                            TypedEmissionError):
                        render_typed_cpp(
                            candidate, candidate.key, caller_hash,
                            gather_sorted_round_profile=carrier)
        for name, candidate in all_forgeries.items():
            reject(candidate, name)

        emitted = render_typed_cpp(
            exact, GATHER_SORTED_KEY, source_hash,
            gather_sorted_round_profile=PROFILE)
        route = "glsl::detail::float_to_int32(glsl::round("
        self.assertEqual(1, emitted.count(route))
        canonical_assignment = next(
            line for line in emitted.splitlines()
            if "std::int32_t brightestX =" in line)
        route_forgeries = {
            "missing-helper": canonical_assignment.replace(
                "glsl::detail::float_to_int32(glsl::round(", "glsl::round(", 1),
            "wrong-helper": canonical_assignment.replace(
                "glsl::detail::float_to_int32(", "forged_to_int32(", 1),
            "reversed-helper": canonical_assignment.replace(
                "glsl::detail::float_to_int32(glsl::round(",
                "glsl::round(glsl::detail::float_to_int32(", 1),
            "wrong-helper-arity": canonical_assignment[:-2] + ", 0);",
            "separate-child": canonical_assignment.replace(
                "glsl::detail::float_to_int32(glsl::round(",
                "glsl::detail::float_to_int32(rounded /* child separated from round */ + glsl::round(", 1),
            "direct-cast": canonical_assignment.replace(
                "glsl::detail::float_to_int32(", "static_cast<std::int32_t>(", 1),
        }
        generated = (REPOSITORY / "src/typed_generated/typed_slice.cpp").read_text()
        for name, spelling in route_forgeries.items():
            with self.subTest(route_mutation=name):
                self.assertNotIn(spelling, emitted)
                self.assertNotIn(spelling, generated)

        original_analyze = generate_typed_slice.analyze_program
        driver_candidates = {
            "stored-round": observable["round-stored-float"],
            "loop-charge": loop_forged["loop-charge"],
            "missing-sampler": interface["missing-sampler"],
            "changed-fetch": interface["changed-fetch"],
        }
        for name, candidate in driver_candidates.items():
            def forged_analyze(parsed, key, *args, _candidate=candidate, **kwargs):
                analyzed = original_analyze(parsed, key, *args, **kwargs)
                return _candidate if key == GATHER_SORTED_KEY else analyzed
            with self.subTest(driver_forgery=name), mock.patch.object(
                    generate_typed_slice.check_corpus, "validate_corpus"), mock.patch.object(
                        generate_typed_slice.check_semantics, "semantic_report",
                        return_value={"body_success": 212}), mock.patch.object(
                            generate_typed_slice, "analyze_program",
                            side_effect=forged_analyze), self.assertRaises(
                                generate_typed_slice.GeneratorError):
                generate_typed_slice.generate_outputs(REPOSITORY)

        # These are language-boundary fixtures, not comment labels standing in
        # for constructs.  The recursion target reaches typed IR and carries a
        # cyclic call graph.  Allocation, callback and exception syntax are
        # rejected by the total parser; a VLA reaches parsing and is rejected by
        # semantic array-extent validation.  Every target has a nearby accepted
        # control so the assertion proves the intended construct boundary.
        source_prefix = (
            "#version 300 es\nprecision highp float;\n"
            "out vec4 fragColor;\n")
        recursion_control = source_prefix + (
            "void helper() {}\n"
            "void main() { helper(); fragColor = vec4(1.0); }\n")
        recursion_target = source_prefix + (
            "void recur() { recur(); }\n"
            "void main() { recur(); fragColor = vec4(1.0); }\n")
        control_typed = analyze_program(
            parse_program(recursion_control, "task24/recursion-control", {}),
            "task24/recursion-control")
        recursion_typed = analyze_program(
            parse_program(recursion_target, "task24/recursion-target", {}),
            "task24/recursion-target")
        self.assertTrue(control_typed.counted_loop_proof.call_graph_acyclic)
        self.assertFalse(recursion_typed.counted_loop_proof.call_graph_acyclic)
        self.assertTrue(any(expression.callee == "recur"
                            for function_value in recursion_typed.functions
                            for statement_value in function_value.body
                            for expression in statement_value.expressions))
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                recursion_typed, generate_typed_slice.APPROVED_CAPABILITIES)

        grammar_targets = {
            "allocation": "float x = new float; fragColor = vec4(x);",
            "callback": "float (*cb)(float) = helper; fragColor = vec4(cb(1.0));",
            "exception": "throw 1; fragColor = vec4(1.0);",
        }
        grammar_control = source_prefix + (
            "float helper(float x) { return x; }\n"
            "void main() { float x = helper(1.0); fragColor = vec4(x); }\n")
        analyze_program(parse_program(
            grammar_control, "task24/grammar-control", {}),
            "task24/grammar-control")
        required_tokens = {
            "allocation": "new float",
            "callback": "(*cb)(float)",
            "exception": "throw 1",
        }
        for name, body in grammar_targets.items():
            target = source_prefix + (
                "float helper(float x) { return x; }\n"
                f"void main() {{ {body} }}\n")
            self.assertIn(required_tokens[name], target)
            with self.subTest(source_construct=name), self.assertRaises(FrontendError):
                parse_program(target, f"task24/{name}-target", {})

        fixed_stack = source_prefix + (
            "void main() { float values[2]; values[0] = 1.0; "
            "fragColor = vec4(values[0]); }\n")
        dynamic_stack = source_prefix + (
            "void main() { int n = int(gl_FragCoord.x); float values[n]; "
            "fragColor = vec4(values[0]); }\n")
        fixed_parsed = parse_program(
            fixed_stack, "task24/fixed-stack-control", {})
        fixed_typed = analyze_program(
            fixed_parsed,
            "task24/fixed-stack-control")
        self.assertEqual(
            "2", fixed_parsed["ast"]["decls"][1]["body"][0][
                "declarators"][0]["array"]["value"])
        self.assertTrue(fixed_typed.functions)
        dynamic_parsed = parse_program(
            dynamic_stack, "task24/dynamic-stack-target", {})
        self.assertEqual(
            "id", dynamic_parsed["ast"]["decls"][1]["body"][1][
                "declarators"][0]["array"]["k"])
        with self.assertRaisesRegex(SemanticError, "E_ARRAY_SIZE"):
            analyze_program(dynamic_parsed, "task24/dynamic-stack-target")

        forged_raw = raw_source_drift
        attacker_hash = hashlib.sha256(
            forged_raw.raw_source.encode()).hexdigest()
        with self.assertRaises(ValueError):
            authenticate_gather_sorted_round_to_int(
                forged_raw, attacker_hash, PROFILE)

    def test_task24_resource_contract_is_mechanical_and_mutation_closed(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.gather_sorted_round_profile import GATHER_SORTED_KEY
        from tools.glslcpp.frontend.semantic import analyze_program

        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == GATHER_SORTED_KEY)
        raw = (corpus / entry["source"]).read_text()
        typed = analyze_program(parse_program(raw, GATHER_SORTED_KEY, {}),
                                GATHER_SORTED_KEY)

        self.assertEqual(
            (("preparedTex", "rankTex", "brightestTex"),
             ("preparedTex", "rankTex", "brightestTex"),
             ("fragColor",), True, False),
            (typed.resources.uniforms, typed.resources.samplers,
             typed.resources.outputs, typed.resources.uses_texture,
             typed.resources.uses_derivatives))
        self.assertEqual(
            (("preparedTex", "uniform", "sampler2D"),
             ("rankTex", "uniform", "sampler2D"),
             ("brightestTex", "uniform", "sampler2D"),
             ("fragColor", "output", "vec4")),
            tuple((item.symbol.name, item.symbol.storage, item.type.display())
                  for item in typed.declarations))
        self.assertEqual(((), (), ()),
                         (typed.structs, typed.uniform_blocks,
                          typed.interface_symbols))

        generated = (REPOSITORY / "src/typed_generated/typed_slice.cpp").read_text()
        start = generated.index(
            "// Typed IR program: filter/pixelSort:gatherSorted\n")
        end = generated.index("\n// Typed IR program: ", start + 1)
        block = generated[start:end]

        exact_members = (
            "  const Surface* preparedTex;\n"
            "  const Surface* rankTex;\n"
            "  const Surface* brightestTex;\n")
        exact_ctor = (
            "  State(const Surface* preparedTex_value, const Surface* rankTex_value, "
            "const Surface* brightestTex_value) : preparedTex(preparedTex_value), "
            "rankTex(rankTex_value), brightestTex(brightestTex_value) {}")
        exact_binder = (
            '  const auto state = std::make_shared<typed_53::State>(&bindings.texture('
            '"preparedTex"), &bindings.texture("rankTex"), &bindings.texture('
            '"brightestTex"));')
        fetch_sites = (
            "fetch_texel(*state.brightestTex, glsl::IVec2(std::int32_t(0), y))",
            "fetch_texel(*state.rankTex, glsl::IVec2(sampleX, y))",
            "fetch_texel(*state.preparedTex, glsl::IVec2(bestX, y))",
        )

        def audit(candidate: str) -> int:
            state_start = candidate.index("struct State final : KernelState {")
            state_end = candidate.index("\n};", state_start)
            state = candidate[state_start:state_end]
            if state.count("const Surface*") != 6:
                # Three constructor parameters and exactly three stored pointers.
                raise ValueError("State sampler pointer count")
            if exact_members not in candidate or candidate.count(exact_members) != 1:
                raise ValueError("State members")
            if candidate.count(exact_ctor) != 1 or candidate.count(exact_binder) != 1:
                raise ValueError("State/binder ABI")
            if candidate.count("texture_size(*state.preparedTex)") != 1:
                raise ValueError("texture-size role/LOD")
            if "texture_size(*state.preparedTex," in candidate:
                raise ValueError("texture-size LOD")
            if sum(candidate.count(site) for site in fetch_sites) != 3:
                raise ValueError("fetch role/count")
            if any(candidate.count(site) != 1 for site in fetch_sites):
                raise ValueError("fetch role multiplicity")
            if "fetch_texel(*state." in candidate and any(
                    token in candidate for token in (
                        "fetch_texel(*state.preparedTex, glsl::IVec2(bestX, y),",
                        "fetch_texel(*state.rankTex, glsl::IVec2(sampleX, y),",
                        "fetch_texel(*state.brightestTex, glsl::IVec2(std::int32_t(0), y),")):
                raise ValueError("fetch LOD")
            pixel = candidate[candidate.index("void pixel("):
                              candidate.index("\n}\n}  // namespace", candidate.index("void pixel("))]
            loop_header = ("for ([[maybe_unused]] std::int32_t s = std::int32_t(0); "
                           "(s < NUM_SAMPLES); ++s) {")
            if pixel.count(loop_header) != 1 or pixel.count(
                    "std::int32_t NUM_SAMPLES = std::int32_t(64);") != 1:
                raise ValueError("bounded loop")
            loop_body = pixel[pixel.index(loop_header):
                              pixel.index("\n  }", pixel.index(loop_header))]
            if "break;" in loop_body or "continue;" in loop_body or "return " in loop_body:
                raise ValueError("early exit")
            # Runtime accounting is derived from the exact static role sites and
            # the authenticated loop trip count: brightest + rank loop + result.
            loop = typed.functions[0].body[12]
            dynamic_fetches = (fetch_sites[0] in pixel) + (
                fetch_sites[1] in loop_body) * loop.loop_proof.trip_count + (
                    fetch_sites[2] in pixel)
            return dynamic_fetches

        self.assertEqual(66, audit(block))
        mutations = {
            "missing-state": block.replace(
                "  const Surface* rankTex;\n", "", 1),
            "extra-state": block.replace(
                "  const Surface* rankTex;\n",
                "  const Surface* rankTex;\n  const Surface* extraTex;\n", 1),
            "wrong-role": block.replace(
                fetch_sites[0],
                "fetch_texel(*state.rankTex, glsl::IVec2(std::int32_t(0), y))", 1),
            "texture-size-lod": block.replace(
                "texture_size(*state.preparedTex)",
                "texture_size(*state.preparedTex, 1)", 1),
            "fetch-lod": block.replace(
                fetch_sites[1], fetch_sites[1][:-1] + ", 1)", 1),
            "missing-fetch": block.replace(fetch_sites[2], "glsl::Vec4(0.0)", 1),
            "extra-fetch": block.replace(
                fetch_sites[2], fetch_sites[2] + " /* " + fetch_sites[2] + " */", 1),
        }
        for name, candidate in mutations.items():
            with self.subTest(mutation=name), self.assertRaises(ValueError):
                audit(candidate)

    def test_task24_generation_isolated_to_one_block_manifest_row_and_catalog_entry(self) -> None:
        import copy
        import hashlib
        import re
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.frontend.gather_sorted_round_profile import GATHER_SORTED_KEY
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import KEYS

        current_spec = copy.deepcopy(generate_typed_slice.load_slice(REPOSITORY))
        current_spec["programs"] = [
            item for item in current_spec["programs"]
            if item["program_key"] not in KEYS
            and item["program_key"] != "filter/smooth:smoothEdge"
            and item["program_key"] != "synth/perlin:perlin"
            and item["program_key"] != "filter/rotate:rot"
            and item["program_key"] != "mixer/focusBlur:focusBlur"
            and item["program_key"] != "filter/extrude:extrude"
            and item["program_key"] != "synth/curl:curl"
            and item["program_key"] != "filter/grade:creative"
            and item["program_key"] != "filter/grade:hslSecondary"
            and item["program_key"] != "filter/grade:lut"
            and item["program_key"] != "filter/grade:primary"
            and item["program_key"] != "filter/grade:vignette"
            and item["program_key"] != "filter/grade:wheels"]
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=current_spec):
            current = generate_typed_slice.generate_outputs(REPOSITORY)
        prior_spec = copy.deepcopy(current_spec)
        prior_spec["programs"] = [
            item for item in prior_spec["programs"]
            if item["program_key"] != GATHER_SORTED_KEY]
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=prior_spec):
            prior = generate_typed_slice.generate_outputs(REPOSITORY)
        header_path = "include/noisemaker/generated/catalog.hpp"
        current[header_path] = generate_typed_slice.render_catalog_header(
            current_spec)
        prior[header_path] = generate_typed_slice.render_catalog_header(prior_spec)

        expected_prior_hashes = {
            "src/typed_generated/typed_slice.cpp":
                "c36f84aa5bcf09d932837bb84ba323ce51d44398ca29deb4dfb71151c32442a8",
            "src/typed_generated/typed_manifest.json":
                "d979fe5d968030cfc3ec9d688367b8b4418b9a841a6f612d65eac03ed5bd4184",
            "include/noisemaker/generated/catalog.hpp":
                "0704695854c772e26ca014d001d0573ce8fb87e367ffaf1c5cbc7e581bf675ed",
        }
        for path, expected in expected_prior_hashes.items():
            self.assertEqual(expected, hashlib.sha256(prior[path]).hexdigest(), path)

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
        self.assertEqual(122, len(prior_keys))
        self.assertEqual(123, len(current_keys))
        self.assertEqual(51, current_keys.index(GATHER_SORTED_KEY))
        self.assertEqual(
            ["filter/pixelSort:findBrightest", GATHER_SORTED_KEY,
             "filter/pixelSort:luminance"], current_keys[50:53])
        self.assertEqual(prior_keys[:51], current_keys[:51])
        for key in prior_keys[:51]:
            self.assertEqual(prior_blocks[key], current_blocks[key], key)
        ordinal = re.compile(r"typed_[0-9]+")
        for key in prior_keys:
            self.assertEqual(
                ordinal.sub("typed_ORDINAL", prior_blocks[key]),
                ordinal.sub("typed_ORDINAL", current_blocks[key]), key)
        self.assertEqual({GATHER_SORTED_KEY}, set(current_blocks) - set(prior_blocks))
        gather = current_blocks[GATHER_SORTED_KEY]
        self.assertEqual(1, gather.count(
            "glsl::detail::float_to_int32(glsl::round("))
        self.assertEqual(1, gather.count(
            "for ([[maybe_unused]] std::int32_t s = std::int32_t(0);"))
        self.assertIn("(s < NUM_SAMPLES)", gather)
        self.assertIn("++s", gather)

        prior_manifest = json.loads(
            prior["src/typed_generated/typed_manifest.json"])
        current_manifest = json.loads(
            current["src/typed_generated/typed_manifest.json"])
        prior_rows = {item["program_key"]: item
                      for item in prior_manifest["programs"]}
        current_rows = {item["program_key"]: item
                        for item in current_manifest["programs"]}
        for key, row in prior_rows.items():
            before = {name: value for name, value in row.items()
                      if name != "output_sha256"}
            after = {name: value for name, value in current_rows[key].items()
                     if name != "output_sha256"}
            self.assertEqual(before, after, key)
        gather_row = current_rows[GATHER_SORTED_KEY]
        self.assertNotIn("gather_sorted_round_profile", gather_row)
        self.assertEqual("none", gather_row["compatibility_transform"])
        self.assertEqual("glsl-f32", gather_row["numeric_literal_contract"])

        prior_header = prior["include/noisemaker/generated/catalog.hpp"].decode()
        current_header = current[
            "include/noisemaker/generated/catalog.hpp"].decode()
        declaration = ("[[nodiscard]] BoundKernel "
                       "bind_filter_pixelSort_gatherSorted("
                       "const glsl::Bindings& bindings);\n")
        self.assertEqual(1, current_header.count(declaration))
        self.assertEqual(prior_header, current_header.replace(declaration, ""))

        cpp = current["src/typed_generated/typed_slice.cpp"].decode()
        catalog_keys = re.findall(
            r'(?m)^    \{"([^"]+)", &bind_[^}]+\},$', cpp)
        typed_keys = [item["program_key"]
                      for item in current_manifest["programs"]]
        public_keys = sorted((*typed_keys, "filter/invert:inv", "synth/solid:solid"))
        self.assertEqual(public_keys, catalog_keys)
        self.assertEqual(125, len(public_keys))
        self.assertEqual(
            "bcf196794ff17ec62c1121347b3fe49a0907baa7ce3c3bd51352ec8a51fbac4e",
            hashlib.sha256(("\n".join(public_keys) + "\n").encode()).hexdigest())
        corpus = check_corpus._corpus_root(REPOSITORY)
        corpus_manifest = json.loads((corpus / "manifest.json").read_text())
        remaining = sorted({item["program_key"]
                            for item in corpus_manifest["programs"]}
                           - set(public_keys))
        self.assertEqual((123, 125, 87, 212),
                         (len(typed_keys), len(public_keys), len(remaining),
                          len(corpus_manifest["programs"])))
        self.assertIn("filter/posterize:posterize", remaining)

    def test_task24_cpp_oracle_table_is_exact_frozen_json_transcription(self) -> None:
        import hashlib
        import re

        oracle_path = pathlib.Path(
            REPOSITORY / "tests/oracles/task-24-oracles.json")
        self.assertTrue(oracle_path.is_file(), "Task 24 frozen oracle JSON is required")
        oracle_bytes = oracle_path.read_bytes()
        self.assertEqual(
            "07dd6f31c3e2b5451cbde8fc0ae6f68ec7c3b06cd6296222ac938cdcee37a72a",
            hashlib.sha256(oracle_bytes).hexdigest())
        oracle = json.loads(oracle_bytes)

        source = (REPOSITORY / "tests/test_generated_kernels.cpp").read_text()
        self.assertEqual(1, source.count("// TASK24_ORACLE_TABLE_BEGIN"))
        self.assertEqual(1, source.count("// TASK24_ORACLE_TABLE_END"))
        match = re.search(
            r'// TASK24_ORACLE_TABLE_BEGIN\n'
            r'constexpr std::string_view kTask24OracleTableJson = R"TASK24\(\n'
            r'(.*?)\n\)TASK24";\n'
            r'// TASK24_ORACLE_TABLE_END', source, re.DOTALL)
        self.assertIsNotNone(match)
        embedded_bytes = ("\n" + match.group(1) + "\n").encode()
        self.assertEqual(31764, len(embedded_bytes))
        self.assertEqual(
            "d090c406de8a7a4f16b6e4869c52e8a71fee1cd33ca34555ecde51eccb0da29e",
            hashlib.sha256(embedded_bytes).hexdigest())
        embedded = json.loads(embedded_bytes)
        expected = {name: oracle[name] for name in (
            "cases", "cross_case_controls", "mutations", "exclusions")}
        self.assertEqual(expected, embedded)
        self.assertEqual(4, len(embedded["cases"]))
        self.assertEqual(4, len(embedded["mutations"]))
        self.assertEqual(2, len(embedded["exclusions"]["cases"]))
        self.assertEqual(3, len(embedded["exclusions"]["controls"]))

    def test_task24_rejected_round_and_loop_mutations_have_exact_native_sensitivity(self) -> None:
        import dataclasses
        import hashlib
        import struct

        from tools.glslcpp import check_corpus, emit_typed_cpp, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import (
            TypedEmissionError, _Emitter, render_typed_cpp,
        )
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.gather_sorted_round_profile import (
            GATHER_SORTED_KEY, PROFILE,
        )
        from tools.glslcpp.frontend.loop_proof import (
            rebuild_authenticated_counted_loop_proofs,
        )
        from tools.glslcpp.frontend.semantic import analyze_program

        oracle_path = pathlib.Path(
            REPOSITORY / "tests/oracles/task-24-oracles.json")
        self.assertTrue(oracle_path.is_file(), "Task 24 frozen oracle JSON is required")
        oracle_bytes = oracle_path.read_bytes()
        self.assertEqual(
            "07dd6f31c3e2b5451cbde8fc0ae6f68ec7c3b06cd6296222ac938cdcee37a72a",
            hashlib.sha256(oracle_bytes).hexdigest())
        oracle = json.loads(oracle_bytes)

        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == GATHER_SORTED_KEY)
        source_hash = entry["raw_sha256"]
        exact = analyze_program(parse_program(
            (corpus / entry["source"]).read_text(), GATHER_SORTED_KEY, {}),
            GATHER_SORTED_KEY)
        function = exact.functions[0]
        round_statement = function.body[6]
        round_declaration = round_statement.expressions[0]
        round_parent = round_declaration.children[0]
        round_value = round_parent.children[0]
        self.assertEqual("brightestX", round_declaration.symbol.name)
        self.assertEqual("int", round_parent.constructor_type.display())
        self.assertEqual(("round", -38),
                         (round_value.callee, round_value.signature_id))
        self.assertEqual(
            "a5f412a1949fdfae93b759bf1c01a22afb44f9a48e71710f2c54cdcdf312c625",
            hashlib.sha256(repr(round_value).encode()).hexdigest())
        samples_statement = function.body[9]
        samples_declaration = samples_statement.expressions[0]
        samples_literal = samples_declaration.children[0]
        self.assertEqual("NUM_SAMPLES", samples_declaration.symbol.name)
        self.assertEqual(("64", 64),
                         (samples_literal.literal, samples_literal.literal_value))
        self.assertEqual(
            "e78d35b12e4720d4df59a17878674a2a43fa038992ff43a763d1ae3e8f428f7e",
            hashlib.sha256(repr(samples_declaration).encode()).hexdigest())
        self.assertEqual(
            "c9df47f651e3ee7232826b3bf13ac40e29889e3d69a2d7a2f6dedecba5c579d4",
            hashlib.sha256(repr(function.body[12].loop_proof).encode()).hexdigest())

        def round_mutation(callee, signature):
            changed_round = dataclasses.replace(
                round_value, callee=callee, signature_id=signature)
            changed_parent = dataclasses.replace(
                round_parent, children=(changed_round,))
            changed_declaration = dataclasses.replace(
                round_declaration, children=(changed_parent,))
            changed_statement = dataclasses.replace(
                round_statement, expressions=(changed_declaration,))
            body = (*function.body[:6], changed_statement, *function.body[7:])
            return dataclasses.replace(
                exact, functions=(dataclasses.replace(function, body=body),))

        floor_program = round_mutation("floor", -17)
        ceil_program = round_mutation("ceil", -6)
        std_round_program = round_mutation("std::round", -38)
        changed_samples_literal = dataclasses.replace(
            samples_literal, literal="8", literal_value=8)
        changed_samples_declaration = dataclasses.replace(
            samples_declaration, children=(changed_samples_literal,))
        changed_samples_statement = dataclasses.replace(
            samples_statement, expressions=(changed_samples_declaration,))
        loop_body = (*function.body[:9], changed_samples_statement,
                     *function.body[10:])
        loop_program = dataclasses.replace(
            exact, functions=(dataclasses.replace(function, body=loop_body),))
        rebuilt_functions, rebuilt_summary = (
            rebuild_authenticated_counted_loop_proofs(loop_program, None))
        loop_program = dataclasses.replace(
            loop_program, functions=rebuilt_functions,
            counted_loop_proof=rebuilt_summary)
        self.assertEqual(8, loop_program.functions[0].body[12].loop_proof.trip_count)
        self.assertEqual(8, loop_program.counted_loop_proof.entrypoint_charge)

        rejected = {
            "round-replaced-by-floor": floor_program,
            "round-replaced-by-ceil": ceil_program,
            "sample-loop-64-to-8": loop_program,
            "negative-half-std-round-away-from-zero-control": std_round_program,
        }
        for name, candidate in rejected.items():
            self.assertNotEqual(exact.functions, candidate.functions, name)
            with self.subTest(mutation=name, boundary="validator"), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash,
                    gather_sorted_round_profile=PROFILE)
            with self.subTest(mutation=name, boundary="emitter"), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    candidate, GATHER_SORTED_KEY, source_hash,
                    gather_sorted_round_profile=PROFILE)

        def exact_round_nodes(program):
            declaration = program.functions[0].body[6].expressions[0]
            parent = declaration.children[0]
            return parent, parent.children[0]

        def render_rejected_mutation(program, namespace, factory, *,
                                     authorize_round=False,
                                     std_round_node=None):
            # The exact candidate has already failed both production boundaries.
            # This emitter is test-local and rebuilds every cache used by rendering.
            class TemporaryEmitter(_Emitter):
                def expression(self, value):
                    if value is std_round_node:
                        return ("std::round(" +
                                super().expression(value.children[0]) + ")")
                    return super().expression(value)

            emitter = object.__new__(TemporaryEmitter)
            emitter.program = program
            emitter.source_hash = source_hash
            emitter.numeric_literal_contract = "glsl-f32"
            emitter.compatibility_transform = None
            emitter.custom_comparer_profile = None
            emitter.source_global_literal_int_profile = None
            emitter.gather_sorted_round_profile = None
            emitter.uniforms = {
                item.symbol.id: item.symbol for item in program.declarations
                if item.symbol.storage == "uniform"}
            emitter.outputs = {
                item.symbol.id: item.symbol for item in program.declarations
                if item.symbol.storage == "output"}
            emitter.source_globals = {
                item.symbol.id: item for item in program.declarations
                if item.symbol.storage == "const"}
            emitter.source_global_dependencies = {}
            emitter.source_global_bounds = ()
            emitter.function_names = {
                item.signature.id: item.name for item in program.functions}
            emitter.ordinary_array_return_signatures = {
                item.signature.id for item in program.functions
                if emitter._function_returns_integral_call_map(item)}
            emitter.mutated_symbol_ids = set()
            for typed_function in program.functions:
                for statement in typed_function.body:
                    emitter._collect_mutated_symbols(statement)
            emitter.locals = {}
            emitter.current_function_name = None
            emitter.current_function_signature_id = None
            emitter.authorized_custom_comparer_predicate = None
            if authorize_round:
                (emitter.authorized_round_parent,
                 emitter.authorized_round) = exact_round_nodes(program)
            else:
                emitter.authorized_round_parent = None
                emitter.authorized_round = None
            with mock.patch.dict(emit_typed_cpp._BUILTIN_NAMES,
                                 {"ceil": "ceil"}):
                return "\n".join(emitter.render_body(namespace, factory)) + "\n"

        canonical_cpp = render_typed_cpp(
            exact, GATHER_SORTED_KEY, source_hash,
            "task24_canonical", "bind_task24_canonical",
            gather_sorted_round_profile=PROFILE)
        floor_cpp = render_rejected_mutation(
            floor_program, "task24_floor", "bind_task24_floor")
        ceil_cpp = render_rejected_mutation(
            ceil_program, "task24_ceil", "bind_task24_ceil")
        loop_cpp = render_rejected_mutation(
            loop_program, "task24_loop8", "bind_task24_loop8",
            authorize_round=True)
        _, std_round_node = exact_round_nodes(std_round_program)
        std_round_cpp = render_rejected_mutation(
            std_round_program, "task24_std_round", "bind_task24_std_round",
            std_round_node=std_round_node)

        nested = "glsl::detail::float_to_int32(glsl::round("
        self.assertEqual(1, canonical_cpp.count(nested))
        self.assertEqual(1, floor_cpp.count("std::int32_t(glsl::floor("))
        self.assertEqual(0, floor_cpp.count("glsl::round("))
        self.assertEqual(1, ceil_cpp.count("std::int32_t(glsl::ceil("))
        self.assertEqual(0, ceil_cpp.count("glsl::round("))
        self.assertEqual(1, loop_cpp.count(nested))
        self.assertEqual(1, loop_cpp.count("NUM_SAMPLES = std::int32_t(8);"))
        self.assertEqual(0, loop_cpp.count("NUM_SAMPLES = std::int32_t(64);"))
        self.assertEqual(1, std_round_cpp.count("std::int32_t(std::round("))
        for index, rendered in enumerate(
                (floor_cpp, ceil_cpp, loop_cpp, std_round_cpp)):
            self.assertEqual(1, rendered.count(
                f"namespace task24_{('floor', 'ceil', 'loop8', 'std_round')[index]} {{"))

        def bits(value):
            return f"{int(value, 16)}U"

        harness = [
            '#include "noisemaker/generated/catalog.hpp"',
            '#include "noisemaker/numeric.hpp"',
            '#include "noisemaker/pass_runner.hpp"',
            '#include "noisemaker/sampler.hpp"',
            '#include <array>', '#include <bit>', '#include <cmath>',
            '#include <cstdint>', '#include <iomanip>', '#include <iostream>',
            '#include <span>', '#include <string_view>', '#include <vector>',
            'namespace noisemaker::glsl {',
            '[[nodiscard]] inline float ceil(double value) noexcept { return noisemaker::f32(std::ceil(value)); }',
            '}  // namespace noisemaker::glsl',
            'namespace noisemaker {', canonical_cpp, floor_cpp, ceil_cpp,
            loop_cpp, std_round_cpp, '}  // namespace noisemaker',
            'namespace {',
            'struct Inputs { noisemaker::Surface prepared; noisemaker::Surface rank; noisemaker::Surface brightest; };',
            'noisemaker::Surface prepared(std::size_t width, std::size_t height) {',
            '  std::vector<float> data(width * height * 4U);',
            '  for (std::size_t y=0; y<height; ++y) for (std::size_t x=0; x<width; ++x) {',
            '    const std::size_t i=(y*width+x)*4U;',
            '    data[i]=static_cast<float>(static_cast<double>((37U*x+17U*y+11U)%113U)/112.0);',
            '    data[i+1U]=static_cast<float>(static_cast<double>((19U*x+29U*y+7U)%109U)/108.0);',
            '    data[i+2U]=static_cast<float>(static_cast<double>((53U*x+13U*y+3U)%107U)/106.0);',
            '    const std::int64_t alpha=static_cast<std::int64_t>((7U*x+5U*y+2U)%19U)-4;',
            '    data[i+3U]=static_cast<float>(static_cast<double>(alpha)/11.0);',
            '  } return noisemaker::Surface(width,height,std::move(data));',
            '}',
            'noisemaker::Surface rank(std::size_t width, std::size_t height) {',
            '  std::vector<float> data(width * height * 4U); const std::size_t d=width-1U;',
            '  for (std::size_t y=0; y<height; ++y) for (std::size_t x=0; x<width; ++x) {',
            '    const std::size_t i=(y*width+x)*4U;',
            '    data[i]=static_cast<float>(static_cast<double>((x*23U+y*11U+5U)%width)/static_cast<double>(d));',
            '    data[i+1U]=static_cast<float>(static_cast<double>((x*7U+y*3U)%width)/static_cast<double>(d));',
            '    data[i+2U]=static_cast<float>(static_cast<double>(x)/static_cast<double>(d)); data[i+3U]=1.0f;',
            '  } return noisemaker::Surface(width,height,std::move(data));',
            '}',
            'Inputs inputs(std::size_t width, std::span<const std::uint32_t> rows) {',
            '  std::vector<float> data(rows.size()*4U); for (std::size_t y=0; y<rows.size(); ++y) { data[y*4U]=noisemaker::uint_bits_to_float(rows[y]); data[y*4U+3U]=1.0f; }',
            '  return {prepared(width,rows.size()),rank(width,rows.size()),noisemaker::Surface(1U,rows.size(),std::move(data))};',
            '}',
            'noisemaker::glsl::Bindings bindings(const Inputs& value) { noisemaker::glsl::Bindings b; b.set_texture("preparedTex",value.prepared); b.set_texture("rankTex",value.rank); b.set_texture("brightestTex",value.brightest); return b; }',
            'void hex_byte(std::uint8_t value) { std::cout << std::hex << std::setfill(\'0\') << std::setw(2) << static_cast<unsigned>(value); }',
            'void emit(std::string_view kind, std::string_view mutation, std::string_view name, const noisemaker::Surface& value) {',
            '  std::cout << kind << "|" << mutation << "|" << name << "|"; static_assert(std::endian::native==std::endian::little);',
            '  for (float lane:value.data()) { const auto bits=std::bit_cast<std::uint32_t>(lane); for (unsigned shift=0; shift<32; shift+=8) hex_byte(static_cast<std::uint8_t>(bits>>shift)); }',
            '  std::cout << "|"; for (std::uint8_t byte:value.to_rgba8()) hex_byte(byte); std::cout << "\\n";',
            '}',
            'using Factory=noisemaker::BoundKernel (*)(const noisemaker::glsl::Bindings&);',
            'constexpr std::array<Factory,3> mutations{&noisemaker::bind_task24_floor,&noisemaker::bind_task24_ceil,&noisemaker::bind_task24_loop8};',
            '}  // namespace', 'int main() {',
        ]
        for case in oracle["cases"]:
            width = case["dimensions"]["width"]
            rows = ",".join(
                bits(item["f32_bits_le"]) for item in case["brightest_rows"])
            harness.extend([
                '  {', f'    constexpr std::array row_bits{{{rows}}};',
                f'    auto value=inputs({width}U,row_bits); auto b=bindings(value);',
                f'    emit("C","native-floor-plus-half-with-int32-clamp","{case["name"]}",noisemaker::run_pass(noisemaker::bind_task24_canonical(b),{width}U,row_bits.size()));',
            ])
            for index, mutation in enumerate(oracle["mutations"][:3]):
                harness.append(
                    f'    emit("M","{mutation["name"]}","{case["name"]}",'
                    f'noisemaker::run_pass(mutations[{index}](b),{width}U,row_bits.size()));')
            harness.append('  }')
        negative_half = oracle["exclusions"]["cases"][0]
        negative_width = negative_half["dimensions"]["width"]
        negative_rows = ",".join(
            bits(item["f32_bits_le"])
            for item in negative_half["brightest_rows"])
        harness.extend([
            '  {', f'    constexpr std::array row_bits{{{negative_rows}}};',
            f'    auto value=inputs({negative_width}U,row_bits); auto b=bindings(value);',
            f'    emit("E","canonical-negative-half","{negative_half["name"]}",noisemaker::run_pass(noisemaker::bind_task24_canonical(b),{negative_width}U,row_bits.size()));',
            f'    emit("X","negative-half-std-round-away-from-zero-control","{negative_half["name"]}",noisemaker::run_pass(noisemaker::bind_task24_std_round(b),{negative_width}U,row_bits.size()));',
            '  }', '  return 0;', '}',
        ])

        protected_paths = tuple(REPOSITORY / path for path in (
            "src/typed_generated/typed_slice.cpp",
            "src/typed_generated/typed_manifest.json",
            "include/noisemaker/generated/catalog.hpp",
        ))
        protected_before = {path: path.read_bytes() for path in protected_paths}
        compiler = os.environ.get("CXX") or shutil.which("c++")
        self.assertIsNotNone(compiler, "a C++20 compiler is required")
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = pathlib.Path(temporary)
            source = temporary_path / "task24_mutations.cpp"
            executable = temporary_path / "task24_mutations"
            source.write_text("\n".join(harness) + "\n")
            command = [
                compiler, "-std=c++20", "-O0", "-Wall", "-Wextra",
                "-Wpedantic", "-Werror", "-ffp-contract=off",
                "-I", str(REPOSITORY / "include"), str(source),
                str(REPOSITORY / "src/surface.cpp"),
                str(REPOSITORY / "src/numeric.cpp"),
                str(REPOSITORY / "src/sampler.cpp"),
                str(REPOSITORY / "src/glsl_runtime.cpp"),
                str(REPOSITORY / "src/kernel.cpp"),
                str(REPOSITORY / "src/pass_runner.cpp"),
                "-o", str(executable),
            ]
            compiled = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(0, compiled.returncode,
                             compiled.stdout + compiled.stderr)
            executed = subprocess.run(
                [str(executable)], text=True, capture_output=True)
            self.assertEqual(0, executed.returncode,
                             executed.stdout + executed.stderr)
        self.assertEqual(protected_before,
                         {path: path.read_bytes() for path in protected_paths})

        canonical_results = {}
        mutation_results = {}
        exclusion_references = {}
        exclusion_results = {}
        for line in executed.stdout.splitlines():
            kind, mutation_name, case_name, float_hex, rgba_hex = line.split("|")
            record = (bytes.fromhex(float_hex), bytes.fromhex(rgba_hex))
            if kind == "C":
                self.assertNotIn(case_name, canonical_results)
                canonical_results[case_name] = record
            elif kind == "M":
                key = (mutation_name, case_name)
                self.assertNotIn(key, mutation_results)
                mutation_results[key] = record
            elif kind == "E":
                self.assertNotIn(case_name, exclusion_references)
                exclusion_references[case_name] = record
            else:
                key = (mutation_name, case_name)
                self.assertNotIn(key, exclusion_results)
                exclusion_results[key] = record
        self.assertEqual([item["name"] for item in oracle["cases"]],
                         list(canonical_results))
        self.assertEqual(12, len(mutation_results))
        self.assertEqual([negative_half["name"]], list(exclusion_references))
        self.assertEqual(1, len(exclusion_results))

        def result_record(case_name, reference, candidate):
            reference_f32, reference_rgba = reference
            candidate_f32, candidate_rgba = candidate
            reference_lanes = struct.unpack(
                f"<{len(reference_f32) // 4}f", reference_f32)
            candidate_lanes = struct.unpack(
                f"<{len(candidate_f32) // 4}f", candidate_f32)
            return {
                "case": case_name,
                "same_f32_bytes": candidate_f32 == reference_f32,
                "same_rgba8_bytes": candidate_rgba == reference_rgba,
                "different_f32_bytes": sum(
                    left != right for left, right in zip(
                        candidate_f32, reference_f32)),
                "different_f32_lanes": sum(
                    left != right for left, right in zip(
                        struct.iter_unpack("<I", candidate_f32),
                        struct.iter_unpack("<I", reference_f32))),
                "different_rgba8_bytes": sum(
                    left != right for left, right in zip(
                        candidate_rgba, reference_rgba)),
                "max_absolute_f32_difference": max(
                    abs(left - right) for left, right in zip(
                        candidate_lanes, reference_lanes)),
                "candidate_f32_sha256": hashlib.sha256(candidate_f32).hexdigest(),
                "candidate_rgba8_sha256": hashlib.sha256(candidate_rgba).hexdigest(),
            }

        cases_by_name = {item["name"]: item for item in oracle["cases"]}
        for case_name, (floats, rgba) in canonical_results.items():
            expected = cases_by_name[case_name]["output"]
            self.assertEqual(expected["f32_sha256"],
                             hashlib.sha256(floats).hexdigest(), case_name)
            self.assertEqual(expected["rgba8_sha256"],
                             hashlib.sha256(rgba).hexdigest(), case_name)
        for mutation in oracle["mutations"][:3]:
            for expected in mutation["case_results"]:
                case_name = expected["case"]
                actual = result_record(
                    case_name, canonical_results[case_name],
                    mutation_results[(mutation["name"], case_name)])
                self.assertEqual(expected, actual,
                                 (mutation["name"], case_name))
        identity = oracle["mutations"][3]
        self.assertEqual("native-floor-plus-half-with-int32-clamp",
                         identity["name"])
        for expected in identity["case_results"]:
            case_name = expected["case"]
            self.assertEqual(
                expected, result_record(
                    case_name, canonical_results[case_name],
                    canonical_results[case_name]),
                (identity["name"], case_name))

        negative_case = negative_half["name"]
        canonical_f32_hash = negative_half["output"]["f32_sha256"]
        canonical_rgba_hash = negative_half["output"]["rgba8_sha256"]
        negative_reference = exclusion_references[negative_case]
        self.assertEqual(canonical_f32_hash,
                         hashlib.sha256(negative_reference[0]).hexdigest())
        self.assertEqual(canonical_rgba_hash,
                         hashlib.sha256(negative_reference[1]).hexdigest())
        std_expected = next(
            item for item in oracle["exclusions"]["controls"]
            if item["name"] ==
            "negative-half-std-round-away-from-zero-control")["case_results"][0]
        std_candidate = exclusion_results[
            ("negative-half-std-round-away-from-zero-control", negative_case)]
        self.assertEqual(std_expected, result_record(
            negative_case, negative_reference, std_candidate))

    def test_task23_literal_int_profile_is_independently_required_by_validator_and_emitter(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.loop_proof import clear_counted_loop_proofs
        from tools.glslcpp.frontend.semantic import analyze_program

        key = "filter/bloom:ntapGather"
        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"] if item["program_key"] == key)
        raw = (root / entry["source"]).read_text()
        profile = "source-global-literal-int-v1"
        typed = analyze_program(parse_program(raw, key, {}), key,
                                source_global_literal_int_profile=profile)
        capabilities = generate_typed_slice.APPROVED_CAPABILITIES

        generate_typed_slice.validate_capabilities(
            typed, capabilities, source_hash=entry["raw_sha256"],
            source_global_literal_int_profile=profile)
        emitted = render_typed_cpp(
            typed, key, entry["raw_sha256"],
            source_global_literal_int_profile=profile)
        self.assertEqual(1, emitted.count("const std::int32_t MAX_TAPS = 64;"))
        self.assertNotIn("static const std::int32_t MAX_TAPS", emitted)

        pre = dataclasses.replace(
            typed, functions=clear_counted_loop_proofs(typed.functions))
        for candidate, carrier in ((pre, profile), (typed, None), (typed, "wrong")):
            with self.subTest(boundary="validator", carrier=carrier), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, capabilities, source_hash=entry["raw_sha256"],
                    source_global_literal_int_profile=carrier)
            with self.subTest(boundary="emitter", carrier=carrier), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    candidate, key, entry["raw_sha256"],
                    source_global_literal_int_profile=carrier)

    def test_task23_caller_source_hash_has_exact_four_state_boundary(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        key = "filter/bloom:ntapGather"
        profile = "source-global-literal-int-v1"
        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == key)
        raw = (root / entry["source"]).read_text()
        typed = analyze_program(parse_program(raw, key, {}), key,
                                source_global_literal_int_profile=profile)
        attacker_raw = raw + "\n"
        attacker = dataclasses.replace(typed, raw_source=attacker_raw)
        states = (
            ("exact", typed, entry["raw_sha256"], True),
            ("missing", typed, None, False),
            ("wrong", typed, "0" * 64, False),
            ("attacker-updated", attacker,
             hashlib.sha256(attacker_raw.encode()).hexdigest(), False),
        )
        for name, candidate, caller_hash, accepted in states:
            if accepted:
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=caller_hash,
                    source_global_literal_int_profile=profile)
                render_typed_cpp(
                    candidate, key, caller_hash,
                    source_global_literal_int_profile=profile)
                continue
            with self.subTest(state=name, boundary="validator"), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=caller_hash,
                    source_global_literal_int_profile=profile)
            with self.subTest(state=name, boundary="emitter"), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    candidate, key, caller_hash,
                    source_global_literal_int_profile=profile)

    def test_task23_six_key_generator_emitter_forgery_and_mode_matrix_is_closed(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.loop_proof import (
            attach_counted_loop_proofs, clear_counted_loop_proofs,
            summarize_counted_loop_proofs)
        from tools.glslcpp.frontend.semantic import analyze_program
        from tests.test_semantic import _task23_complete_ir_forgery_matrix

        profile = "source-global-literal-int-v1"
        profiles = {
            "filter/bloom:ntapGather": ({}, "MAX_TAPS"),
            "filter/directionalBlur:directionalBlur": ({}, "N"),
            "filter/spinBlur:spinBlur": ({}, "N"),
            "filter/strokes:stkSmear": ({"MODE": 0}, "MAX_TAPS"),
            "filter/vaseline:upsample": ({}, "TAP_COUNT"),
            "filter/wind:wind": ({"METHOD": 1}, "MAX_STEPS"),
        }
        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        capabilities = generate_typed_slice.APPROVED_CAPABILITIES

        def replace_first_loop(functions):
            replaced = 0
            def statement(value):
                nonlocal replaced
                proof = value.loop_proof
                if proof is not None and replaced == 0:
                    proof = dataclasses.replace(
                        proof, trip_count=proof.trip_count + 1)
                    replaced += 1
                return dataclasses.replace(
                    value, loop_proof=proof,
                    children=tuple(statement(child) for child in value.children))
            result = tuple(dataclasses.replace(
                function, body=tuple(statement(item) for item in function.body))
                for function in functions)
            self.assertEqual(1, replaced)
            return result

        def replace_first_read(program, symbol_id):
            replaced = 0
            def expression(value):
                nonlocal replaced
                changed = value
                if (value.kind == "id" and value.symbol_id == symbol_id
                        and replaced == 0):
                    changed = dataclasses.replace(value, symbol_id=symbol_id + 10000)
                    replaced += 1
                return dataclasses.replace(
                    changed,
                    children=tuple(expression(child) for child in changed.children))
            def statement(value):
                return dataclasses.replace(
                    value,
                    expressions=tuple(expression(item) for item in value.expressions),
                    children=tuple(statement(child) for child in value.children))
            functions = tuple(dataclasses.replace(
                function, body=tuple(statement(item) for item in function.body))
                for function in program.functions)
            self.assertEqual(1, replaced)
            return dataclasses.replace(program, functions=functions)

        def reject(candidate, source_hash, carrier, *, label, key):
            with self.subTest(key=key, case=label, boundary="validator"), \
                    self.assertRaises(generate_typed_slice.GeneratorError) as caught:
                generate_typed_slice.validate_capabilities(
                    candidate, capabilities, source_hash=source_hash,
                    source_global_literal_int_profile=carrier)
            self.assertRegex(str(caught.exception),
                             r"source-global literal-int|counted-for")
            with self.subTest(key=key, case=label, boundary="emitter"), \
                    self.assertRaises(TypedEmissionError) as caught:
                render_typed_cpp(
                    candidate, candidate.key, source_hash,
                    source_global_literal_int_profile=carrier)
            self.assertRegex(str(caught.exception),
                             r"source-global literal-int|counted-for")

        for key, (defines, global_name) in profiles.items():
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            raw = (root / entry["source"]).read_text()
            source_hash = hashlib.sha256(raw.encode()).hexdigest()
            self.assertEqual(entry["raw_sha256"], source_hash)
            post = analyze_program(
                parse_program(raw, key, defines), key,
                source_global_literal_int_profile=profile)
            generate_typed_slice.validate_capabilities(
                post, capabilities, source_hash=source_hash,
                source_global_literal_int_profile=profile)
            render_typed_cpp(
                post, key, source_hash,
                source_global_literal_int_profile=profile)

            pre_functions = attach_counted_loop_proofs(post.functions, key)
            pre = dataclasses.replace(
                post, functions=pre_functions,
                counted_loop_proof=summarize_counted_loop_proofs(pre_functions))
            cleared_functions = clear_counted_loop_proofs(post.functions)
            cleared = dataclasses.replace(
                post, functions=cleared_functions,
                counted_loop_proof=summarize_counted_loop_proofs(cleared_functions))
            forged_functions = replace_first_loop(post.functions)
            forged = dataclasses.replace(
                post, functions=forged_functions,
                counted_loop_proof=dataclasses.replace(
                    post.counted_loop_proof,
                    entrypoint_charge=post.counted_loop_proof.entrypoint_charge + 1))
            attacker_raw = raw + "\n"
            attacker = dataclasses.replace(forged, raw_source=attacker_raw)
            rejected_modes = (
                ("pre-absent", pre, source_hash, None),
                ("pre-exact", pre, source_hash, profile),
                ("post-absent", post, source_hash, None),
                ("post-wrong", post, source_hash, "wrong"),
                ("cleared-exact", cleared, source_hash, profile),
                ("forged-post-exact", forged, source_hash, profile),
                ("forged-attacker-updated-hash", attacker,
                 hashlib.sha256(attacker_raw.encode()).hexdigest(), profile),
            )
            for label, candidate, caller_hash, carrier in rejected_modes:
                reject(candidate, caller_hash, carrier, label=label, key=key)

            forgeries = _task23_complete_ir_forgery_matrix(
                self, post, global_name)
            forgeries["submitted-callgraph-summary"] = dataclasses.replace(
                post, counted_loop_proof=dataclasses.replace(
                    post.counted_loop_proof, call_graph_acyclic=False))
            for label, candidate in forgeries.items():
                caller_hash = (hashlib.sha256(
                    candidate.raw_source.encode()).hexdigest()
                    if label == "raw-source" else source_hash)
                if label == "raw-source":
                    self.assertNotEqual(source_hash, caller_hash)
                reject(candidate, caller_hash, profile,
                       label=f"forgery-{label}", key=key)

        bloom_key = "filter/bloom:ntapGather"
        bloom_entry = next(item for item in manifest["programs"]
                           if item["program_key"] == bloom_key)
        bloom_raw = (root / bloom_entry["source"]).read_text()
        bloom = analyze_program(
            parse_program(bloom_raw, bloom_key, {}), bloom_key,
            source_global_literal_int_profile=profile)
        vocabulary_cases = {
            "absent": tuple(item for item in capabilities if item != profile),
            "wrong": tuple(item if item != profile else profile + "-wrong"
                           for item in capabilities),
            "extra": capabilities + (profile + "-extra",),
            "duplicate": capabilities + (profile,),
        }
        for label, declared in vocabulary_cases.items():
            with self.subTest(vocabulary=label), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    bloom, declared, source_hash=bloom_entry["raw_sha256"],
                    source_global_literal_int_profile=profile)

        prior_key = "filter/bc:bc"
        prior_entry = next(item for item in manifest["programs"]
                           if item["program_key"] == prior_key)
        prior_raw = (root / prior_entry["source"]).read_text()
        prior = analyze_program(parse_program(prior_raw, prior_key, {}), prior_key)
        generate_typed_slice.validate_capabilities(
            prior, capabilities, source_hash=prior_entry["raw_sha256"])
        render_typed_cpp(prior, prior_key, prior_entry["raw_sha256"])
        reject(prior, prior_entry["raw_sha256"], profile,
               label="foreign-borrowed-carrier", key=prior_key)

    def test_task23_six_key_counts_positions_and_generated_isolation_are_exact(self) -> None:
        import copy
        import hashlib
        from unittest import mock
        from tools.glslcpp import check_corpus, generate_typed_slice

        new_keys = (
            "filter/bloom:ntapGather",
            "filter/directionalBlur:directionalBlur",
            "filter/spinBlur:spinBlur",
            "filter/strokes:stkSmear",
            "filter/vaseline:upsample",
            "filter/wind:wind",
        )
        live_spec = generate_typed_slice.load_slice(REPOSITORY)
        spec = copy.deepcopy(live_spec)
        spec["programs"] = [
            item for item in spec["programs"]
            if item["program_key"] not in {
                "classicNoisedeck/lensDistortion:lensDistortion",
                "filter/pixelSort:gatherSorted",
                "filter/prismaticAberration:prismaticAberration",
                "filter/smooth:smoothEdge",
                "synth/perlin:perlin",
                "filter/rotate:rot",
                "mixer/focusBlur:focusBlur",
                "filter/extrude:extrude",
                "synth/curl:curl",
                "filter/grade:creative",
                "filter/grade:hslSecondary",
                "filter/grade:lut",
                "filter/grade:primary",
                "filter/grade:vignette",
                "filter/grade:wheels",
            }]
        keys = [item["program_key"] for item in spec["programs"]
                if item["program_key"] != "filter/rotate:rot"]
        public = sorted((*keys, "filter/invert:inv", "synth/solid:solid"))
        corpus = json.loads((check_corpus._corpus_root(REPOSITORY) / "manifest.json").read_text())
        self.assertEqual((122, 124, 88, 212), (
            len(keys), len(public), len(corpus["programs"]) - len(public),
            len(corpus["programs"])))
        self.assertEqual(
            "9db3013a6b0f78d0b95fcb6713c54ace95e82d1545e796e7a380add23c009f0b",
            hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest())
        self.assertEqual(
            "2b84fff4d6f35aec1ac6bcc35188d9893e3194c90b9c428775a7308ce1f6281a",
            hashlib.sha256(("\n".join(public) + "\n").encode()).hexdigest())
        self.assertEqual((7, 23, 77, 82, 92, 96),
                         tuple(keys.index(key) for key in new_keys))
        self.assertNotIn("filter/reindex:nmReindexStats", keys)
        self.assertEqual(1, spec["capabilities"].count(
            "source-global-literal-int-v1"))

        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=spec):
            current = generate_typed_slice.generate_outputs(REPOSITORY)
        current_cpp = current["src/typed_generated/typed_slice.cpp"].decode()
        prior_spec = copy.deepcopy(spec)
        prior_spec["programs"] = [item for item in prior_spec["programs"]
                                  if item["program_key"] not in new_keys]
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=prior_spec):
            prior_cpp = generate_typed_slice.generate_outputs(REPOSITORY)[
                "src/typed_generated/typed_slice.cpp"].decode()
        self.assertEqual(
            (932898,
             "a3f8135d41e9f2abc864fada60532309b56c43f6e6eb138d548a23b57f944c4f"),
            (len(prior_cpp.encode()),
             hashlib.sha256(prior_cpp.encode()).hexdigest()))

        marker = re.compile(r"(?m)^// Typed IR program: (.+)$")
        def blocks(text):
            hits = list(marker.finditer(text)); result = {}
            for index, hit in enumerate(hits):
                end = (hits[index + 1].start() if index + 1 < len(hits)
                       else text.index("\nnamespace {", hit.end()))
                result[hit.group(1)] = text[hit.start():end]
            return result
        before, after = blocks(prior_cpp), blocks(current_cpp)
        self.assertEqual(116, len(before))
        self.assertEqual(set(before), set(after) - set(new_keys))
        for key in keys[:7]:
            self.assertEqual(before[key], after[key])
        normalize = lambda value: re.sub(
            r"typed_[0-9]+", "typed_SENTINEL", value)
        for key in before:
            with self.subTest(prior_key=key):
                self.assertEqual(normalize(before[key]), normalize(after[key]))

        expected_ints = {
            new_keys[0]: ("MAX_TAPS", "64"), new_keys[1]: ("N", "32"),
            new_keys[2]: ("N", "32"), new_keys[3]: ("MAX_TAPS", "24"),
            new_keys[4]: ("TAP_COUNT", "32"), new_keys[5]: ("MAX_STEPS", "128"),
        }
        for key, (name, value) in expected_ints.items():
            block = after[key]
            with self.subTest(new_key=key):
                self.assertEqual(1, block.count(
                    f"const std::int32_t {name} = {value};"))
                self.assertNotIn("static const", block)
                self.assertNotIn("thread_local", block)
                self.assertNotIn("void main(", block)
                self.assertNotIn("new ", block)

        strokes = after["filter/strokes:stkSmear"]
        self.assertEqual(2, strokes.count("glsl::Vec4 srcSample("))
        self.assertNotRegex(
            strokes,
            r"glsl::Vec4 srcSample\([^;]*\) noexcept \{\s*\}",
            "a source prototype must not become an empty helper definition")

        manifest = json.loads(current[
            "src/typed_generated/typed_manifest.json"].decode())
        self.assertEqual(122, len(manifest["programs"]))
        self.assertTrue(all(item["capabilities"] == spec["capabilities"]
                            for item in manifest["programs"]))
        by_key = {item["program_key"]: item for item in manifest["programs"]}
        self.assertEqual({"MODE": 0}, by_key[new_keys[3]]["defines"])
        self.assertEqual({"METHOD": 1}, by_key[new_keys[5]]["defines"])
        self.assertTrue(all(by_key[key]["compatibility_transform"] == "none"
                            and by_key[key]["numeric_literal_contract"] == "glsl-f32"
                            for key in new_keys))

    def test_task23_cpp_canonical_fixture_table_is_an_exact_oracle_transcription(self) -> None:
        oracle_path = pathlib.Path(
            REPOSITORY / "tests/oracles/task-23-oracles.json")
        self.assertTrue(oracle_path.is_file(), "Task 23 frozen oracle JSON is required")
        oracle = json.loads(oracle_path.read_text())
        cpp = (REPOSITORY / "tests/test_generated_kernels.cpp").read_text()
        begin = "// TASK23_CANONICAL_FIXTURES_BEGIN"
        end = "// TASK23_CANONICAL_FIXTURES_END"
        self.assertEqual(1, cpp.count(begin))
        self.assertEqual(1, cpp.count(end))
        table = cpp[cpp.index(begin) + len(begin):cpp.index(end)]
        table = table[table.index("{{") + 1:table.rindex("}};") + 1]

        token = re.compile(
            r'\s*(?:("(?:[^"\\]|\\.)*")|(0x[0-9a-fA-F]+|[0-9]+)U?'
            r'|(true|false)|([A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_][A-Za-z0-9_]*)*)'
            r'|([{},]))')
        tokens = []
        position = 0
        while position < len(table):
            match = token.match(table, position)
            self.assertIsNotNone(match, f"unparsed C++ fixture text at {position}")
            value = next(item for item in match.groups() if item is not None)
            tokens.append(value)
            position = match.end()

        cursor = 0
        def parse_value():
            nonlocal cursor
            value = tokens[cursor]
            cursor += 1
            if value == "{":
                result = []
                while tokens[cursor] != "}":
                    result.append(parse_value())
                    if tokens[cursor] == ",":
                        cursor += 1
                    else:
                        self.assertEqual("}", tokens[cursor])
                cursor += 1
                return result
            if value.startswith('"'):
                return json.loads(value)
            if value in {"true", "false"}:
                return value == "true"
            if re.fullmatch(r"(?:0x[0-9a-fA-F]+|[0-9]+)U?", value):
                return int(value.removesuffix("U"), 0)
            return value

        rows = parse_value()
        self.assertEqual(len(tokens), cursor)
        self.assertEqual(19, len(rows))

        program_names = {
            "filter/bloom:ntapGather": "Task23Program::bloom",
            "filter/directionalBlur:directionalBlur": "Task23Program::directional",
            "filter/spinBlur:spinBlur": "Task23Program::spin",
            "filter/strokes:stkSmear": "Task23Program::strokes",
            "filter/vaseline:upsample": "Task23Program::vaseline",
            "filter/wind:wind": "Task23Program::wind",
        }
        expected_rows = []
        for case in oracle["cases"]:
            uniforms = []
            for name, uniform in case["uniforms"].items():
                kind = ("Task23UniformKind::i32" if uniform["glsl_type"] == "int"
                        else "Task23UniformKind::f32")
                bits = (uniform["value"] if uniform["glsl_type"] == "int"
                        else int(uniform["f32_bits_le"], 16))
                uniforms.append([name, kind, bits])
            while len(uniforms) < 3:
                uniforms.append(["", "Task23UniformKind::f32", 0])
            probes = []
            for probe in case["output"]["probes"]:
                probes.extend(probe["at_top_down_xy"])
                probes.extend(int(value, 16) for value in probe["f32_bits_le"])
            metrics = case["output"]["metrics"]
            expected_rows.append([
                case["name"], case["key"], program_names[case["key"]],
                case["dimensions"]["width"], case["dimensions"]["height"],
                [int(value, 16) for value in case["tileOffset"]["f32_bits_le"]],
                [int(value, 16) for value in case["fullResolution"]["f32_bits_le"]],
                uniforms, len(case["uniforms"]),
                case["input"]["f32_sha256"], case["input"]["rgba8_sha256"],
                case["output"]["f32_sha256"], case["output"]["rgba8_sha256"],
                probes, metrics["pixels"], metrics["finite_lanes"],
                metrics["nonfinite_lanes"],
                metrics["changed_f32_lanes_from_same_input_position"],
                metrics["alpha_preserved_pixels"], case["input_immutable"],
                case["repeat_identity"]["input_f32_bytes"],
                case["repeat_identity"]["output_f32_bytes"],
                case["repeat_identity"]["output_rgba8_bytes"],
                case["output"]["f32_sha256"] == case["input"]["f32_sha256"],
            ])
        self.assertEqual(expected_rows, rows)

    def test_task23_rejected_structural_mutations_have_exact_native_sensitivity(self) -> None:
        import dataclasses
        import hashlib
        import struct

        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import (
            TypedEmissionError, _Emitter, render_typed_cpp,
        )
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.typed_ir import TypedExpression

        oracle_path = pathlib.Path(
            REPOSITORY / "tests/oracles/task-23-oracles.json")
        self.assertTrue(oracle_path.is_file(), "Task 23 frozen oracle JSON is required")
        oracle = json.loads(oracle_path.read_text())
        sensitivity = oracle["mutation_sensitivity"]
        frozen_sensitivity = json.dumps(
            sensitivity, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(
            "df29ceac2f2df56b9e73fe8fa92842b39dee48e0f0482367f2bb6ec56d5bccca",
            hashlib.sha256(frozen_sensitivity).hexdigest())

        # name, key, owner, target, mutation kind, before shape/value,
        # replacement spelling/value.  The full contract, source replacement,
        # controls, results, and ordering are frozen by the digest above and
        # then consumed field-for-field below.
        structural_specs = (
            ("bloom-global-bound-64-to-8", "filter/bloom:ntapGather", None,
             "MAX_TAPS", "global", 64, "8", 8),
            ("bloom-tap-count-forced-one", "filter/bloom:ntapGather", "main",
             "tapCount", "local", ("builtin", "int", "clamp", None, 30, 20), "1", 1),
            ("directional-global-bound-32-to-8", "filter/directionalBlur:directionalBlur",
             None, "N", "global", 32, "8", 8),
            ("directional-jitter-disabled", "filter/directionalBlur:directionalBlur",
             "main", "jitter", "local", ("binary", "float", None, "*", 23, 21),
             "0.0", 0.0),
            ("spin-global-bound-32-to-8", "filter/spinBlur:spinBlur", None,
             "N", "global", 32, "8", 8),
            ("spin-jitter-disabled", "filter/spinBlur:spinBlur", "main", "jitter",
             "local", ("binary", "float", None, "*", 51, 21), "0.0", 0.0),
            ("strokes-global-bound-24-to-8", "filter/strokes:stkSmear", None,
             "MAX_TAPS", "global", 24, "8", 8),
            ("strokes-field-selection-forced-135", "filter/strokes:stkSmear", "main",
             "side", "local", ("builtin", "float", "smoothstep", None, 196, 18),
             "0.0", 0.0),
            ("vaseline-global-bound-32-to-8", "filter/vaseline:upsample", None,
             "TAP_COUNT", "global", 32, "8", 8),
            ("vaseline-edge-mask-forced-zero", "filter/vaseline:upsample", "main",
             "edgeMask", "local", ("call", "float", "chebyshev_mask", None, 68, 22),
             "0.0", 0.0),
            ("wind-global-bound-128-to-16", "filter/wind:wind", None,
             "MAX_STEPS", "global", 128, "16", 16),
            ("wind-direction-forced-right", "filter/wind:wind", "main", "marchDir",
             "local", ("conditional", "float", None, None, 38, 23), "1.0", 1.0),
        )
        mutations = sensitivity["mutations"]
        self.assertEqual(12, sensitivity["mutation_count"])
        self.assertEqual(
            [(item[0], item[1]) for item in structural_specs],
            [(item["name"], item["key"]) for item in mutations])
        self.assertTrue(all(item["replacement"]["exact_replacement_count"] == 1
                            for item in mutations))

        corpus_root = check_corpus._corpus_root(REPOSITORY)
        corpus_manifest = json.loads((corpus_root / "manifest.json").read_text())
        slice_spec = generate_typed_slice.load_slice(REPOSITORY)
        defines_by_key = {item["program_key"]: item["defines"]
                          for item in slice_spec["programs"]}
        profile = "source-global-literal-int-v1"
        programs = {}
        source_hashes = {}
        canonical_cpp = {}
        ordered_keys = tuple(dict.fromkeys(item[1] for item in structural_specs))
        for canonical_index, key in enumerate(ordered_keys):
            entry = next(item for item in corpus_manifest["programs"]
                         if item["program_key"] == key)
            raw = (corpus_root / entry["source"]).read_text()
            source_hash = hashlib.sha256(raw.encode()).hexdigest()
            self.assertEqual(entry["raw_sha256"], source_hash)
            typed = analyze_program(
                parse_program(raw, key, defines_by_key[key]), key,
                source_global_literal_int_profile=profile)
            generate_typed_slice.validate_capabilities(
                typed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                source_global_literal_int_profile=profile)
            programs[key] = typed
            source_hashes[key] = source_hash
            canonical_cpp[key] = render_typed_cpp(
                typed, key, source_hash,
                f"task23_canonical_{canonical_index}",
                f"bind_task23_canonical_{canonical_index}",
                source_global_literal_int_profile=profile)

        def mutate_program(spec):
            name, key, owner, target, kind, before, spelling, value = spec
            program = programs[key]
            if kind == "global":
                matches = [item for item in program.declarations
                           if item.symbol.name == target]
                self.assertEqual(1, len(matches), name)
                declaration = matches[0]
                initializer = declaration.initializer
                self.assertIsNotNone(initializer)
                self.assertEqual(
                    ("const", False, "in", "int", "literal", "rvalue", before,
                     str(before), (), declaration.symbol.span.program_key),
                    (declaration.symbol.storage, declaration.symbol.writable,
                     declaration.symbol.direction, declaration.type.display(),
                     initializer.kind, initializer.category, initializer.literal_value,
                     initializer.literal, initializer.children,
                     declaration.symbol.span.program_key))
                replacement = dataclasses.replace(
                    initializer, literal=spelling, literal_value=value)
                changed = dataclasses.replace(declaration, initializer=replacement)
                declarations = tuple(changed if item is declaration else item
                                     for item in program.declarations)
                return dataclasses.replace(program, declarations=declarations)

            found = 0
            def statement(item, function_name):
                nonlocal found
                expressions = []
                for expression in item.expressions:
                    candidate = expression
                    if (function_name == owner and expression.kind == "declaration"
                            and expression.symbol is not None
                            and expression.symbol.name == target):
                        found += 1
                        self.assertEqual(1, len(expression.children), name)
                        initializer = expression.children[0]
                        actual = (initializer.kind, initializer.type.display(),
                                  initializer.callee, initializer.operator,
                                  initializer.span.start_line,
                                  initializer.span.start_column)
                        self.assertEqual(before, actual, name)
                        self.assertEqual("rvalue", initializer.category, name)
                        replacement = TypedExpression(
                            "literal", initializer.type, initializer.span,
                            initializer.category, literal=spelling,
                            literal_value=value)
                        candidate = dataclasses.replace(
                            expression, children=(replacement,))
                    expressions.append(candidate)
                return dataclasses.replace(
                    item, expressions=tuple(expressions),
                    children=tuple(statement(child, function_name)
                                   for child in item.children))
            functions = tuple(dataclasses.replace(
                function, body=tuple(statement(item, function.name)
                                     for item in function.body))
                for function in program.functions)
            self.assertEqual(1, found, name)
            return dataclasses.replace(program, functions=functions)

        def render_rejected_mutation(program, source_hash, namespace, factory):
            # Deliberately bypass only _Emitter.__post_init__, after the test
            # has proved both production boundaries reject this exact tree.
            # Rebuild every program-derived rendering cache from the mutation.
            emitter = object.__new__(_Emitter)
            emitter.program = program
            emitter.source_hash = source_hash
            emitter.numeric_literal_contract = "glsl-f32"
            emitter.compatibility_transform = None
            emitter.custom_comparer_profile = None
            emitter.source_global_literal_int_profile = profile
            emitter.authorized_round_parent = None
            emitter.authorized_round = None
            emitter.authorized_custom_comparer_predicate = None
            emitter.uniforms = {
                item.symbol.id: item.symbol for item in program.declarations
                if item.symbol.storage == "uniform"}
            emitter.outputs = {
                item.symbol.id: item.symbol for item in program.declarations
                if item.symbol.storage == "output"}
            emitter.source_globals = {
                item.symbol.id: item for item in program.declarations
                if item.symbol.storage == "const"}
            emitter.source_global_dependencies = {}
            integer = next(item for item in program.declarations
                           if item.symbol.storage == "const"
                           and item.type.display() == "int")
            emitter.source_global_bounds = ((
                integer.symbol.id, integer.initializer.literal_value,
                "source-global-const-literal", integer.symbol),)
            emitter.function_names = {
                item.signature.id: item.name for item in program.functions}
            emitter.ordinary_array_return_signatures = {
                item.signature.id for item in program.functions
                if emitter._function_returns_integral_call_map(item)}
            emitter.mutated_symbol_ids = set()
            for function in program.functions:
                for item in function.body:
                    emitter._collect_mutated_symbols(item)
            emitter.locals = {}
            emitter.current_function_name = None
            emitter.current_function_signature_id = None
            emitter._validate_source_globals()
            return "\n".join(emitter.render_body(namespace, factory)) + "\n"

        rendered_mutations = []
        for index, spec in enumerate(structural_specs):
            name, key, _owner, target, kind, _before, spelling, _value = spec
            mutated = mutate_program(spec)
            with self.subTest(mutation=name, boundary="validator"), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    mutated, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hashes[key],
                    source_global_literal_int_profile=profile)
            with self.subTest(mutation=name, boundary="emitter"), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    mutated, key, source_hashes[key],
                    source_global_literal_int_profile=profile)
            rendered = render_rejected_mutation(
                mutated, source_hashes[key], f"task23_mut_{index}",
                f"bind_task23_mut_{index}")
            marker = (f"const std::int32_t {target} = {spelling};"
                      if kind == "global" else
                      f"[[maybe_unused]] {'std::int32_t' if spelling == '1' else 'double'} "
                      f"{target} = {'std::int32_t(1)' if spelling == '1' else f'static_cast<float>({spelling})'};")
            canonical_lines = [line.strip() for line in canonical_cpp[key].splitlines()
                               if target in line and " = " in line]
            mutated_lines = [line.strip() for line in rendered.splitlines()
                             if target in line and " = " in line]
            self.assertIn(marker, mutated_lines, name)
            self.assertNotIn(marker, canonical_lines, name)
            self.assertTrue(set(canonical_lines) - set(mutated_lines), name)
            self.assertEqual(1, rendered.count(f"namespace task23_mut_{index} {{"))
            rendered_mutations.append(rendered)

        case_by_name = {item["name"]: item for item in oracle["cases"]}
        program_ids = {
            "filter/bloom:ntapGather": "bloom",
            "filter/directionalBlur:directionalBlur": "directional",
            "filter/spinBlur:spinBlur": "spin",
            "filter/strokes:stkSmear": "strokes",
            "filter/vaseline:upsample": "vaseline",
            "filter/wind:wind": "wind",
        }

        def f32(bits):
            return f"noisemaker::uint_bits_to_float({bits}U)"

        def bindings_lines(case):
            width = case["dimensions"]["width"]
            height = case["dimensions"]["height"]
            key = case["key"]
            program_id = program_ids[key]
            result = [
                f"    auto input = task23_input({width}U, {height}U);",
                "    noisemaker::glsl::Bindings bindings;",
                '    bindings.set_texture("inputTex", input);',
            ]
            vectors = {
                "resolution": [f"0x{struct.unpack('<I', struct.pack('<f', float(width)))[0]:08x}",
                               f"0x{struct.unpack('<I', struct.pack('<f', float(height)))[0]:08x}"],
                "tileOffset": case["tileOffset"]["f32_bits_le"],
                "fullResolution": case["fullResolution"]["f32_bits_le"],
            }
            required = {
                "bloom": ("tileOffset", "fullResolution"),
                "directional": ("resolution",),
                "spin": ("resolution", "tileOffset", "fullResolution"),
                "strokes": ("resolution", "tileOffset"),
                "vaseline": ("resolution", "tileOffset", "fullResolution"),
                "wind": ("resolution", "tileOffset"),
            }[program_id]
            for name in required:
                x, y = vectors[name]
                result.append(
                    f'    bindings.set_uniform("{name}", noisemaker::glsl::Vec2('
                    f'{f32(x)}, {f32(y)}));')
            for name, value in case["uniforms"].items():
                native = (f"std::int32_t({value['value']})"
                          if value["glsl_type"] == "int"
                          else f32(value["f32_bits_le"]))
                result.append(f'    bindings.set_uniform("{name}", {native});')
            return result

        harness = [
            '#include "noisemaker/generated/catalog.hpp"',
            '#include "noisemaker/numeric.hpp"',
            '#include "noisemaker/pass_runner.hpp"',
            '#include "noisemaker/sampler.hpp"',
            '#include <array>', '#include <bit>', '#include <cstdint>',
            '#include <iomanip>', '#include <iostream>', '#include <span>',
            '#include <string_view>', '#include <vector>',
            'namespace noisemaker {', *canonical_cpp.values(),
            *rendered_mutations, '}  // namespace noisemaker',
            'namespace {',
            'noisemaker::Surface task23_input(std::size_t width, std::size_t height) {',
            '  std::vector<float> data(width * height * 4U);',
            '  for (std::size_t y = 0; y < height; ++y) for (std::size_t x = 0; x < width; ++x) {',
            '    const std::size_t lane = (y * width + x) * 4U;',
            '    data[lane] = static_cast<float>(static_cast<double>((17U*x + 31U*y + 13U)%101U)/100.0);',
            '    data[lane+1U] = static_cast<float>(static_cast<double>((7U*x + 19U*y + 23U)%97U)/96.0);',
            '    data[lane+2U] = static_cast<float>(static_cast<double>((29U*x + 11U*y + 5U)%89U)/88.0);',
            '    const std::int64_t alpha = static_cast<std::int64_t>((5U*x + 7U*y + 3U)%23U)-5;',
            '    data[lane+3U] = static_cast<float>(static_cast<double>(alpha)/12.0);',
            '  }',
            '  return noisemaker::Surface(width, height, std::move(data));',
            '}',
            'void hex_byte(std::uint8_t value) { std::cout << std::hex << std::setfill(\'0\') << std::setw(2) << static_cast<unsigned>(value); }',
            'void emit(std::string_view kind, std::string_view mutation, std::string_view name, const noisemaker::Surface& value) {',
            '  std::cout << kind << "|" << mutation << "|" << name << "|";',
            '  static_assert(std::endian::native == std::endian::little);',
            '  for (float lane : value.data()) { const auto bits = std::bit_cast<std::uint32_t>(lane); for (unsigned shift=0; shift<32; shift+=8) hex_byte(static_cast<std::uint8_t>(bits >> shift)); }',
            '  std::cout << "|"; for (std::uint8_t byte : value.to_rgba8()) hex_byte(byte); std::cout << "\\n";',
            '}',
            'using Factory = noisemaker::BoundKernel (*)(const noisemaker::glsl::Bindings&);',
            'constexpr std::array<Factory, 12> factories{',
            *[f'  &noisemaker::bind_task23_mut_{index},' for index in range(12)],
            '};',
            'constexpr std::array<Factory, 6> canonical_factories{',
            *[f'  &noisemaker::bind_task23_canonical_{index},' for index in range(6)],
            '};', '}  // namespace', 'int main() {',
        ]
        for case in oracle["cases"]:
            harness.append("  {")
            harness.extend(bindings_lines(case))
            width = case["dimensions"]["width"]
            height = case["dimensions"]["height"]
            canonical_index = ordered_keys.index(case["key"])
            harness.append(
                f'    emit("C", "-", "{case["name"]}", noisemaker::run_pass('
                f'canonical_factories[{canonical_index}](bindings), '
                f'{width}U, {height}U, 0.0f, 41.0f, 23U, '
                'noisemaker::uint_bits_to_float(0x3c888889U)));')
            harness.append("  }")
        for index, mutation in enumerate(mutations):
            for result in mutation["case_results"]:
                case = case_by_name[result["case"]]
                harness.append("  {")
                harness.extend(bindings_lines(case))
                width = case["dimensions"]["width"]
                height = case["dimensions"]["height"]
                harness.append(
                    f'    emit("M", "{mutation["name"]}", "{case["name"]}", '
                    f'noisemaker::run_pass(factories[{index}](bindings), '
                    f'{width}U, {height}U, 0.0f, 41.0f, 23U, '
                    'noisemaker::uint_bits_to_float(0x3c888889U)));')
                harness.append("  }")
        harness.extend(["  return 0;", "}"])

        compiler = os.environ.get("CXX") or shutil.which("c++")
        self.assertIsNotNone(compiler, "a C++20 compiler is required")
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = pathlib.Path(temporary)
            source = temporary_path / "task23_mutations.cpp"
            executable = temporary_path / "task23_mutations"
            source.write_text("\n".join(harness) + "\n")
            command = [
                compiler, "-std=c++20", "-O0", "-Wall", "-Wextra",
                "-Wpedantic", "-Werror", "-ffp-contract=off",
                "-I", str(REPOSITORY / "include"), str(source),
                str(REPOSITORY / "src/surface.cpp"),
                str(REPOSITORY / "src/numeric.cpp"),
                str(REPOSITORY / "src/sampler.cpp"),
                str(REPOSITORY / "src/glsl_runtime.cpp"),
                str(REPOSITORY / "src/kernel.cpp"),
                str(REPOSITORY / "src/pass_runner.cpp"),
                "-o", str(executable),
            ]
            compiled = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(0, compiled.returncode, compiled.stdout + compiled.stderr)
            executed = subprocess.run(
                [str(executable)], text=True, capture_output=True)
            self.assertEqual(0, executed.returncode, executed.stdout + executed.stderr)

        canonical_results = {}
        mutation_results = {}
        for line in executed.stdout.splitlines():
            kind, mutation_name, case_name, float_hex, rgba_hex = line.split("|")
            record = (bytes.fromhex(float_hex), bytes.fromhex(rgba_hex))
            if kind == "C":
                self.assertNotIn(case_name, canonical_results)
                canonical_results[case_name] = record
            else:
                key = (mutation_name, case_name)
                self.assertNotIn(key, mutation_results)
                mutation_results[key] = record
        self.assertEqual([item["name"] for item in oracle["cases"]],
                         list(canonical_results))
        self.assertEqual(sum(len(item["case_results"]) for item in mutations),
                         len(mutation_results))

        for case in oracle["cases"]:
            floats, rgba = canonical_results[case["name"]]
            self.assertEqual(case["output"]["f32_sha256"],
                             hashlib.sha256(floats).hexdigest(), case["name"])
            self.assertEqual(case["output"]["rgba8_sha256"],
                             hashlib.sha256(rgba).hexdigest(), case["name"])
        for mutation in mutations:
            results_by_case = {item["case"]: item
                               for item in mutation["case_results"]}
            self.assertEqual([item["case"] for item in mutation["case_results"]],
                             list(results_by_case))
            for case_name, expected in results_by_case.items():
                canonical_float, canonical_rgba = canonical_results[case_name]
                mutated_float, mutated_rgba = mutation_results[
                    (mutation["name"], case_name)]
                canonical_lanes = struct.unpack(
                    f"<{len(canonical_float) // 4}f", canonical_float)
                mutated_lanes = struct.unpack(
                    f"<{len(mutated_float) // 4}f", mutated_float)
                actual = {
                    "case": case_name,
                    "same_f32_bytes": mutated_float == canonical_float,
                    "same_rgba8_bytes": mutated_rgba == canonical_rgba,
                    "different_f32_bytes": sum(a != b for a, b in zip(
                        mutated_float, canonical_float)),
                    "different_f32_lanes": sum(
                        a != b for a, b in zip(
                            struct.iter_unpack("<I", mutated_float),
                            struct.iter_unpack("<I", canonical_float))),
                    "different_rgba8_bytes": sum(a != b for a, b in zip(
                        mutated_rgba, canonical_rgba)),
                    "max_absolute_f32_difference": max(
                        abs(a - b) for a, b in zip(mutated_lanes, canonical_lanes)),
                    "mutated_f32_sha256": hashlib.sha256(mutated_float).hexdigest(),
                    "mutated_rgba8_sha256": hashlib.sha256(mutated_rgba).hexdigest(),
                }
                self.assertEqual(expected, actual, (mutation["name"], case_name))
            for case_name in mutation["required_identity_cases"]:
                self.assertTrue(results_by_case[case_name]["same_f32_bytes"])
                self.assertTrue(results_by_case[case_name]["same_rgba8_bytes"])
            for case_name in mutation["required_divergence_cases"]:
                self.assertFalse(results_by_case[case_name]["same_f32_bytes"])
                self.assertFalse(results_by_case[case_name]["same_rgba8_bytes"])


    def test_refract_fixed_array_parameter_validates_and_emits_only_exact_owned_sites(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.fixed_array_in_parameter_proof import (
            attach_fixed_array_in_parameter_proof,
        )
        from tools.glslcpp.frontend.refract_compatibility import (
            apply_refract_truthy_vector_noops,
        )
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "classicNoisedeck/refract:refract")
        raw = (root / entry["source"]).read_text()
        analyzed = analyze_program(
            parse_program(raw, entry["program_key"], {}), entry["program_key"])
        typed = attach_fixed_array_in_parameter_proof(
            apply_refract_truthy_vector_noops(analyzed))
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=entry["raw_sha256"])
        emitted = render_typed_cpp(typed, entry["program_key"], entry["raw_sha256"])
        namespace_body = emitted[:emitted.index("}  // namespace typed_kernel")]
        self.assertIn("using Kernel9 = std::array<double, 9>;", emitted)
        self.assertIn("using Offsets9 = std::array<glsl::Vec2, 9>;", emitted)
        self.assertIn("static_assert(sizeof(Kernel9) == 72U);", emitted)
        self.assertIn("static_assert(sizeof(Offsets9) == 72U);", emitted)
        self.assertEqual(1, emitted.count("Kernel9 deriv_x{};"))
        self.assertEqual(1, emitted.count("Kernel9 deriv_y{};"))
        self.assertEqual(1, emitted.count("Offsets9 offset{};"))
        self.assertEqual(2, emitted.count("const Kernel9& kernel"))
        self.assertEqual(2, emitted.count("convolve(state, context, uv, deriv_"))
        self.assertEqual(1, emitted.count(
            "offset[static_cast<std::size_t>(i)]"))
        self.assertEqual(2, emitted.count(
            "kernel[static_cast<std::size_t>(i)]"))
        for index in range(9):
            self.assertEqual(1, emitted.count(f"offset[{index}] ="))
            self.assertEqual(1, emitted.count(f"deriv_x[{index}] ="))
            self.assertEqual(1, emitted.count(f"deriv_y[{index}] ="))
        self.assertNotIn("std::vector", emitted)
        self.assertNotIn("std::span", emitted)
        self.assertNotIn(".at(", emitted)
        self.assertNotIn("Kernel9 kernel", emitted)
        self.assertIsNone(re.search(r"(?<!const )Kernel9& kernel", emitted))
        self.assertNotIn("Kernel9*", emitted)
        self.assertNotIn("return kernel", emitted)
        self.assertNotIn("new ", namespace_body)
        self.assertNotIn("std::make_shared", namespace_body)
        self.assertNotIn("std::function", namespace_body)
        self.assertNotIn("std::map", namespace_body)
        self.assertNotIn("std::variant", namespace_body)
        self.assertNotIn("std::string", namespace_body)
        self.assertNotIn("virtual ", namespace_body)
        self.assertNotIn("throw ", namespace_body)
        self.assertNotIn("middle = ((", emitted)
        self.assertTrue(all("?" not in line for line in emitted.splitlines()
                            if "middle =" in line))

        for name, candidate in {
            "cleared": dataclasses.replace(typed, fixed_array_in_parameter_proof=None),
            "raw": dataclasses.replace(typed, raw_source=raw + "\n"),
            "normalized": dataclasses.replace(typed, source=typed.source + "\n"),
        }.items():
            with self.subTest(name=name, boundary="validator"), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=entry["raw_sha256"])
            with self.subTest(name=name, boundary="emitter"), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(candidate, entry["program_key"], entry["raw_sha256"])

    def test_refract_fixed_array_parameter_rejects_structural_and_forged_proof_mutations_at_both_boundaries(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend import fixed_array_in_parameter_proof as proof_module
        from tools.glslcpp.frontend.fixed_array_in_parameter_proof import (
            attach_fixed_array_in_parameter_proof,
        )
        from tools.glslcpp.frontend.refract_compatibility import (
            apply_refract_truthy_vector_noops,
        )
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.semantic_types import FLOAT, array, vector
        from tools.glslcpp.frontend.typed_ir import (
            PreprocessorDefine, StructDeclaration, Symbol, TypedDeclaration,
            UniformBlock,
        )

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "classicNoisedeck/refract:refract")
        raw = (root / entry["source"]).read_text()
        analyzed = analyze_program(
            parse_program(raw, entry["program_key"], {}), entry["program_key"])
        typed = attach_fixed_array_in_parameter_proof(
            apply_refract_truthy_vector_noops(analyzed))
        proof = typed.fixed_array_in_parameter_proof
        self.assertIsNotNone(proof)

        def replace_function(program, replacement):
            return dataclasses.replace(
                program,
                functions=tuple(replacement if function.signature.id == replacement.signature.id
                                else function for function in program.functions))

        def replace_function_id(program, signature_id, replacement):
            return dataclasses.replace(
                program,
                functions=tuple(replacement if function.signature.id == signature_id
                                else function for function in program.functions))

        blend = next(function for function in typed.functions
                     if function.signature.id == 35 and function.body)
        raw_blend = next(function for function in analyzed.functions
                         if function.signature.id == 35 and function.body)
        convolve = next(function for function in typed.functions
                        if function.signature.id == 38 and function.body)
        deriv_x = next(function for function in typed.functions
                       if function.signature.id == 39 and function.body)
        main = next(function for function in typed.functions
                    if function.signature.id == 42 and function.body)

        def mutate_first_self_assignment(statement, changed):
            expressions = []
            for value in statement.expressions:
                if (not changed[0] and value.kind == "assign"
                        and len(value.children) == 2
                        and value.children[0].kind == "id"
                        and value.children[0].symbol_id == 47
                        and value.children[1].kind == "id"
                        and value.children[1].symbol_id == 47):
                    changed[0] = True
                    source = dataclasses.replace(
                        value.children[1], symbol_id=34, symbol=blend.parameters[1])
                    value = dataclasses.replace(
                        value, children=(value.children[0], source))
                expressions.append(value)
            return dataclasses.replace(
                statement, expressions=tuple(expressions),
                children=tuple(mutate_first_self_assignment(child, changed)
                               for child in statement.children))

        changed = [False]
        blend_body = list(blend.body)
        blend_body[3] = mutate_first_self_assignment(blend_body[3], changed)
        self.assertTrue(changed[0])
        compatibility = replace_function(
            typed, dataclasses.replace(blend, body=tuple(blend_body)))

        def mutate_first_expression(statement, predicate, mutator, changed):
            def expression(value):
                if not changed[0] and predicate(value):
                    changed[0] = True
                    return mutator(value)
                return dataclasses.replace(
                    value, children=tuple(expression(child)
                                          for child in value.children))

            expressions = []
            for value in statement.expressions:
                expressions.append(expression(value))
            return dataclasses.replace(
                statement, expressions=tuple(expressions),
                children=tuple(mutate_first_expression(
                    child, predicate, mutator, changed)
                               for child in statement.children))

        def compatibility_program(name, predicate, mutator, source=blend):
            changed = [False]
            body = tuple(mutate_first_expression(
                statement, predicate, mutator, changed)
                         for statement in source.body)
            self.assertTrue(changed[0], name)
            return replace_function(
                typed, dataclasses.replace(source, body=body))

        self_assignment = lambda value: (
            value.kind == "assign" and len(value.children) == 2
            and value.children[0].kind == "id"
            and value.children[0].symbol_id == 47
            and value.children[1].kind == "id"
            and value.children[1].symbol_id == 47)
        raw_conditional = lambda value: value.kind == "conditional"
        compatibility_target = compatibility_program(
            "target", self_assignment,
            lambda value: dataclasses.replace(
                value, children=(dataclasses.replace(
                    value.children[0], symbol_id=34,
                    symbol=blend.parameters[1]), value.children[1])))
        compatibility_extra = compatibility_program(
            "extra", self_assignment,
            lambda value: dataclasses.replace(value, operator="+="))
        compatibility_raw_operand = compatibility_program(
            "raw-operand", raw_conditional,
            lambda value: dataclasses.replace(
                value, children=(dataclasses.replace(
                    value.children[0], operator="!="),
                                 *value.children[1:])), raw_blend)
        compatibility_raw_constant = compatibility_program(
            "raw-constant", raw_conditional,
            lambda value: dataclasses.replace(
                value, children=(dataclasses.replace(
                    value.children[0], children=(
                        value.children[0].children[0],
                        dataclasses.replace(
                            value.children[0].children[1],
                            literal="2.0", literal_value=2.0))),
                                 *value.children[1:])), raw_blend)
        compatibility_raw_true = compatibility_program(
            "raw-true", raw_conditional,
            lambda value: dataclasses.replace(
                value, children=(value.children[0],
                                 dataclasses.replace(
                                     value.children[1], symbol_id=34,
                                     symbol=raw_blend.parameters[1]),
                                 value.children[2])), raw_blend)
        compatibility_raw_false = compatibility_program(
            "raw-false", raw_conditional,
            lambda value: dataclasses.replace(
                value, children=(value.children[0], value.children[1],
                                 dataclasses.replace(
                                     value.children[2], callee="abs"))), raw_blend)
        compatibility_raw_subtree = compatibility_program(
            "raw-subtree", raw_conditional,
            lambda value: dataclasses.replace(
                value, children=(value.children[0], value.children[2],
                                 value.children[1])), raw_blend)

        def compatibility_site_structure(duplicate):
            changed = [False]

            def statement(value):
                children = tuple(statement(child) for child in value.children)
                value = dataclasses.replace(value, children=children)
                if (not changed[0] and value.kind == "block"
                        and len(value.children) == 1
                        and len(value.children[0].expressions) == 1
                        and self_assignment(value.children[0].expressions[0])):
                    changed[0] = True
                    return dataclasses.replace(
                        value, children=((value.children[0], value.children[0])
                                         if duplicate else ()))
                return value

            body = tuple(statement(value) for value in blend.body)
            self.assertTrue(changed[0])
            return replace_function(
                typed, dataclasses.replace(blend, body=body))

        compatibility_missing = compatibility_site_structure(False)
        compatibility_duplicated = compatibility_site_structure(True)

        convolve_parameters = list(convolve.parameters)
        convolve_parameters[1] = dataclasses.replace(
            convolve_parameters[1], direction="out")
        parameter_signature = dataclasses.replace(
            convolve.signature, parameters=tuple(convolve_parameters))
        parameter = replace_function(
            typed, dataclasses.replace(convolve, signature=parameter_signature))

        offset_body = list(convolve.body)
        first_offset = offset_body[3].expressions[0]
        center_offset = offset_body[7].expressions[0]
        offset_body[3] = dataclasses.replace(
            offset_body[3], expressions=(dataclasses.replace(
                first_offset,
                children=(first_offset.children[0], center_offset.children[1])),))
        offset = replace_function(
            typed, dataclasses.replace(convolve, body=tuple(offset_body)))

        loop_body = list(convolve.body)
        loop_body[14] = dataclasses.replace(
            loop_body[14], loop_proof=dataclasses.replace(
                loop_body[14].loop_proof, trip_count=8))
        loop = replace_function(
            typed, dataclasses.replace(convolve, body=tuple(loop_body)))

        caller_body = list(deriv_x.body)
        negative_store = caller_body[7].expressions[0]
        negative_rhs = negative_store.children[1]
        caller_body[7] = dataclasses.replace(
            caller_body[7], expressions=(dataclasses.replace(
                negative_store, children=(negative_store.children[0],
                                          dataclasses.replace(
                                              negative_rhs,
                                              children=(dataclasses.replace(
                                                  negative_rhs.children[0],
                                                  literal="2.0",
                                                  literal_value=2.0),)))),))
        caller = replace_function(
            typed, dataclasses.replace(deriv_x, body=tuple(caller_body)))

        main_body = list(main.body)
        mode_one = main_body[8].children[1]
        mode_one_block = mode_one.children[0]
        reversed_block = dataclasses.replace(
            mode_one_block, children=tuple(reversed(mode_one_block.children)))
        main_body[8] = dataclasses.replace(
            main_body[8], children=(main_body[8].children[0],
                                    dataclasses.replace(
                                        mode_one, children=(reversed_block,))))
        reachability = replace_function(
            typed, dataclasses.replace(main, body=tuple(main_body)))

        def body_program(function, body):
            return replace_function(
                typed, dataclasses.replace(function, body=tuple(body)))

        def caller_call_program(mutator):
            body = list(deriv_x.body)
            declaration = body[11].expressions[0]
            call = declaration.children[0]
            body[11] = dataclasses.replace(
                body[11], expressions=(dataclasses.replace(
                    declaration, children=(mutator(call),)),))
            return body_program(deriv_x, body)

        caller_declaration = deriv_x.body[1].expressions[0]
        caller_store = deriv_x.body[2].expressions[0]
        caller_target = caller_store.children[0]
        caller_literal = caller_target.children[1]
        caller_call = deriv_x.body[11].expressions[0].children[0]
        deriv_y = next(function for function in typed.functions
                       if function.signature.id == 40 and function.body)
        deriv_y_array = deriv_y.body[1].expressions[0]

        caller_extent_body = list(deriv_x.body)
        extent_type = array(FLOAT, 8)
        caller_extent_body[1] = dataclasses.replace(
            caller_extent_body[1], expressions=(dataclasses.replace(
                caller_declaration, type=extent_type,
                symbol=dataclasses.replace(
                    caller_declaration.symbol, type=extent_type)),))
        caller_extent = body_program(deriv_x, caller_extent_body)

        caller_extent_ten_body = list(deriv_x.body)
        extent_ten_type = array(FLOAT, 10)
        caller_extent_ten_body[1] = dataclasses.replace(
            caller_extent_ten_body[1], expressions=(dataclasses.replace(
                caller_declaration, type=extent_ten_type,
                symbol=dataclasses.replace(
                    caller_declaration.symbol, type=extent_ten_type)),))
        caller_extent_ten = body_program(deriv_x, caller_extent_ten_body)

        caller_vec2_body = list(deriv_x.body)
        caller_vec2_type = array(vector("float", 2), 9)
        caller_vec2_body[1] = dataclasses.replace(
            caller_vec2_body[1], expressions=(dataclasses.replace(
                caller_declaration, type=caller_vec2_type,
                symbol=dataclasses.replace(
                    caller_declaration.symbol, type=caller_vec2_type)),))
        caller_vec2 = body_program(deriv_x, caller_vec2_body)

        def caller_symbol_program(**changes):
            body = list(deriv_x.body)
            body[1] = dataclasses.replace(
                body[1], expressions=(dataclasses.replace(
                    caller_declaration,
                    symbol=dataclasses.replace(
                        caller_declaration.symbol, **changes)),))
            return body_program(deriv_x, body)

        caller_initializer_body = list(deriv_x.body)
        caller_initializer_body[1] = dataclasses.replace(
            caller_initializer_body[1], expressions=(dataclasses.replace(
                caller_declaration, children=(caller_call.children[1],)),))
        caller_initializer = body_program(deriv_x, caller_initializer_body)

        caller_index_body = list(deriv_x.body)
        out_of_range = dataclasses.replace(
            caller_literal, literal="9", literal_value=9)
        caller_index_body[2] = dataclasses.replace(
            caller_index_body[2], expressions=(dataclasses.replace(
                caller_store, children=(dataclasses.replace(
                    caller_target,
                    children=(caller_target.children[0], out_of_range)),
                                        caller_store.children[1])),))
        caller_index = body_program(deriv_x, caller_index_body)

        caller_dynamic_body = list(deriv_x.body)
        dynamic_index = dataclasses.replace(
            caller_literal, kind="id", type=deriv_x.parameters[1].type,
            symbol_id=deriv_x.parameters[1].id,
            symbol=deriv_x.parameters[1], literal=None, literal_value=None)
        caller_dynamic_body[2] = dataclasses.replace(
            caller_dynamic_body[2], expressions=(dataclasses.replace(
                caller_store, children=(dataclasses.replace(
                    caller_target,
                    children=(caller_target.children[0], dynamic_index)),
                                        caller_store.children[1])),))
        caller_dynamic = body_program(deriv_x, caller_dynamic_body)

        caller_alias_body = list(deriv_x.body)
        caller_alias_body[1] = dataclasses.replace(
            caller_alias_body[1], expressions=(dataclasses.replace(
                caller_declaration, children=(caller_call.children[1],)),))
        caller_alias = body_program(deriv_x, caller_alias_body)

        caller_unary_body = list(deriv_x.body)
        caller_unary_body[7] = dataclasses.replace(
            caller_unary_body[7], expressions=(dataclasses.replace(
                negative_store, children=(negative_store.children[0],
                                          dataclasses.replace(
                                              negative_rhs, operator="+"))),))
        caller_unary = body_program(deriv_x, caller_unary_body)

        caller_pre_read_body = list(deriv_x.body)
        caller_pre_read_body[2] = dataclasses.replace(
            caller_pre_read_body[2], expressions=(dataclasses.replace(
                caller_store, children=(caller_store.children[0],
                                        caller_target)),))
        caller_pre_read = body_program(deriv_x, caller_pre_read_body)

        caller_early_return = body_program(
            deriv_x, (*deriv_x.body[:11], deriv_x.body[12],
                      *deriv_x.body[11:]))

        convolve_loop = convolve.body[14]
        loop_block = convolve_loop.children[1]
        extra_parameter_read_body = list(convolve.body)
        extra_parameter_read_body[14] = dataclasses.replace(
            convolve_loop, children=(convolve_loop.children[0],
                                     dataclasses.replace(
                                         loop_block,
                                         children=(*loop_block.children,
                                                   loop_block.children[2]))))
        extra_parameter_read = body_program(convolve, extra_parameter_read_body)

        parameter_extent_values = list(convolve.parameters)
        parameter_extent_type = array(FLOAT, 8)
        parameter_extent_values[1] = dataclasses.replace(
            parameter_extent_values[1], type=parameter_extent_type)
        parameter_extent = replace_function(
            typed, dataclasses.replace(
                convolve, signature=dataclasses.replace(
                    convolve.signature,
                    parameters=tuple(parameter_extent_values))))

        parameter_vec2_values = list(convolve.parameters)
        parameter_vec2_values[1] = dataclasses.replace(
            parameter_vec2_values[1], type=array(vector("float", 2), 9))
        parameter_vec2 = replace_function(
            typed, dataclasses.replace(
                convolve, signature=dataclasses.replace(
                    convolve.signature,
                    parameters=tuple(parameter_vec2_values))))

        parameter_inout_values = list(convolve.parameters)
        parameter_inout_values[1] = dataclasses.replace(
            parameter_inout_values[1], direction="inout")
        parameter_inout = replace_function(
            typed, dataclasses.replace(
                convolve, signature=dataclasses.replace(
                    convolve.signature,
                    parameters=tuple(parameter_inout_values))))

        changed_signature = dataclasses.replace(convolve.signature, id=938)
        parameter_signature_id = replace_function_id(
            typed, 38, dataclasses.replace(
                convolve, signature=changed_signature))

        parameter_name_values = list(convolve.parameters)
        parameter_name_values[1] = dataclasses.replace(
            parameter_name_values[1], name="kernel_alias")
        parameter_name = replace_function(
            typed, dataclasses.replace(
                convolve, signature=dataclasses.replace(
                    convolve.signature,
                    parameters=tuple(parameter_name_values))))

        parameter_ordinal_values = list(convolve.parameters)
        parameter_ordinal_values[0], parameter_ordinal_values[1] = (
            parameter_ordinal_values[1], parameter_ordinal_values[0])
        parameter_ordinal = replace_function(
            typed, dataclasses.replace(
                convolve, signature=dataclasses.replace(
                    convolve.signature,
                    parameters=tuple(parameter_ordinal_values))))

        kernel_index = loop_block.children[1].expressions[0].children[1].children[1]
        parameter_literal_body = list(convolve.body)
        convolution = loop_block.children[1].expressions[0]
        convolution_rhs = convolution.children[1]
        literal_kernel_index = dataclasses.replace(
            kernel_index,
            children=(kernel_index.children[0], caller_literal))
        changed_convolution_rhs = dataclasses.replace(
            convolution_rhs,
            children=(convolution_rhs.children[0], literal_kernel_index))
        changed_convolution = dataclasses.replace(
            convolution,
            children=(convolution.children[0], changed_convolution_rhs))
        changed_loop_block = dataclasses.replace(
            loop_block,
            children=(loop_block.children[0],
                      dataclasses.replace(
                          loop_block.children[1],
                          expressions=(changed_convolution,)),
                      loop_block.children[2]))
        parameter_literal_body[14] = dataclasses.replace(
            convolve_loop,
            children=(convolve_loop.children[0], changed_loop_block))
        parameter_literal = body_program(convolve, parameter_literal_body)

        parameter_write_body = list(convolve.body)
        parameter_write = dataclasses.replace(
            convolution, operator="=",
            children=(kernel_index, kernel_index))
        parameter_write_block = dataclasses.replace(
            loop_block,
            children=(loop_block.children[0],
                      dataclasses.replace(
                          loop_block.children[1],
                          expressions=(parameter_write,)),
                      loop_block.children[2]))
        parameter_write_body[14] = dataclasses.replace(
            convolve_loop,
            children=(convolve_loop.children[0], parameter_write_block))
        parameter_write_program = body_program(convolve, parameter_write_body)

        whole_kernel_id = kernel_index.children[0]
        parameter_whole_copy_body = list(convolve.body)
        parameter_whole_copy_declaration = convolve.body[13].expressions[0]
        parameter_whole_copy_body[13] = dataclasses.replace(
            convolve.body[13], expressions=(dataclasses.replace(
                parameter_whole_copy_declaration,
                children=(whole_kernel_id,)),))
        parameter_whole_copy = body_program(
            convolve, parameter_whole_copy_body)

        parameter_return_body = list(convolve.body)
        parameter_return_body[16] = dataclasses.replace(
            parameter_return_body[16], expressions=(whole_kernel_id,))
        parameter_return = body_program(convolve, parameter_return_body)

        parameter_pass_body = list(convolve.body)
        parameter_pass_body.insert(
            15, dataclasses.replace(
                convolve.body[15], kind="expr", expressions=(whole_kernel_id,)))
        parameter_pass = body_program(convolve, parameter_pass_body)

        parameter_update_expression = dataclasses.replace(
            convolve_loop.expressions[1], children=(kernel_index,),
            operator="++")
        parameter_update_body = list(convolve.body)
        parameter_update_body.insert(
            15, dataclasses.replace(
                convolve.body[15], kind="expr",
                expressions=(parameter_update_expression,)))
        parameter_update = body_program(convolve, parameter_update_body)

        parameter_whole_assignment_body = list(convolve.body)
        parameter_whole_assignment_body.insert(
            15, dataclasses.replace(
                convolve.body[15], kind="expr", expressions=(dataclasses.replace(
                    convolution, operator="=",
                    children=(whole_kernel_id, whole_kernel_id)),)))
        parameter_whole_assignment = body_program(
            convolve, parameter_whole_assignment_body)

        parameter_whole_store_body = list(convolve.body)
        parameter_whole_store_body[13] = dataclasses.replace(
            convolve.body[13], expressions=(dataclasses.replace(
                parameter_whole_copy_declaration, kind="assign", operator="=",
                children=(parameter_whole_copy_declaration,
                          whole_kernel_id)),))
        parameter_whole_store = body_program(
            convolve, parameter_whole_store_body)

        parameter_other_induction_body = list(convolve.body)
        other_induction = convolve.body[12].expressions[0]
        parameter_other_index = dataclasses.replace(
            kernel_index, children=(kernel_index.children[0],
                                    dataclasses.replace(
                                        kernel_index.children[1],
                                        symbol_id=other_induction.symbol_id,
                                        symbol=other_induction.symbol)))
        other_convolution_rhs = dataclasses.replace(
            convolution_rhs,
            children=(convolution_rhs.children[0], parameter_other_index))
        other_convolution = dataclasses.replace(
            convolution,
            children=(convolution.children[0], other_convolution_rhs))
        other_loop_block = dataclasses.replace(
            loop_block,
            children=(loop_block.children[0], dataclasses.replace(
                loop_block.children[1], expressions=(other_convolution,)),
                      loop_block.children[2]))
        parameter_other_induction_body[14] = dataclasses.replace(
            convolve_loop,
            children=(convolve_loop.children[0], other_loop_block))
        parameter_other_induction = body_program(
            convolve, parameter_other_induction_body)

        offset_initializer_body = list(convolve.body)
        offset_declaration = convolve.body[2].expressions[0]
        offset_initializer_body[2] = dataclasses.replace(
            offset_initializer_body[2], expressions=(dataclasses.replace(
                offset_declaration,
                children=(convolve.body[3].expressions[0].children[0].children[0],)),))
        offset_initializer = body_program(convolve, offset_initializer_body)

        def offset_declaration_program(type_value=None, **symbol_changes):
            body = list(convolve.body)
            changed_type = type_value or offset_declaration.type
            body[2] = dataclasses.replace(
                body[2], expressions=(dataclasses.replace(
                    offset_declaration, type=changed_type,
                    symbol=dataclasses.replace(
                        offset_declaration.symbol, type=changed_type,
                        **symbol_changes)),))
            return body_program(convolve, body)

        offset_extent_eight = offset_declaration_program(
            array(vector("float", 2), 8))
        offset_extent_ten = offset_declaration_program(
            array(vector("float", 2), 10))
        offset_float = offset_declaration_program(array(FLOAT, 9))

        offset_index_body = list(convolve.body)
        first_offset_target = first_offset.children[0]
        offset_index_body[3] = dataclasses.replace(
            convolve.body[3], expressions=(dataclasses.replace(
                first_offset, children=(dataclasses.replace(
                    first_offset_target,
                    children=(first_offset_target.children[0],
                              dataclasses.replace(
                                  first_offset_target.children[1],
                                  literal="1", literal_value=1))),
                                        first_offset.children[1])),))
        offset_index = body_program(convolve, offset_index_body)

        offset_span_body = list(convolve.body)
        offset_span_body[3] = dataclasses.replace(
            convolve.body[3], expressions=(dataclasses.replace(
                first_offset, children=(dataclasses.replace(
                    first_offset_target, span=caller_target.span),
                                        first_offset.children[1])),))
        offset_span = body_program(convolve, offset_span_body)

        offset_in_loop_body = list(convolve.body)
        offset_in_loop_body[14] = dataclasses.replace(
            convolve_loop,
            children=(convolve_loop.children[0], dataclasses.replace(
                loop_block,
                children=(*loop_block.children, convolve.body[3]))))
        offset_in_loop = body_program(convolve, offset_in_loop_body)

        whole_offset_id = first_offset_target.children[0]
        offset_escape_body = list(convolve.body)
        offset_escape_body.insert(
            15, dataclasses.replace(
                convolve.body[15], kind="expr", expressions=(whole_offset_id,)))
        offset_escape = body_program(convolve, offset_escape_body)

        offset_return_body = list(convolve.body)
        offset_return_body[16] = dataclasses.replace(
            offset_return_body[16], expressions=(whole_offset_id,))
        offset_return = body_program(convolve, offset_return_body)

        loop_bound_body = list(convolve.body)
        loop_condition = convolve_loop.expressions[0]
        changed_bound = dataclasses.replace(
            loop_condition.children[1], literal="8", literal_value=8)
        loop_bound_body[14] = dataclasses.replace(
            convolve_loop, expressions=(dataclasses.replace(
                loop_condition,
                children=(loop_condition.children[0], changed_bound)),
                                        convolve_loop.expressions[1]))
        loop_bound = body_program(convolve, loop_bound_body)

        loop_update_body = list(convolve.body)
        loop_update_body[14] = dataclasses.replace(
            convolve_loop, expressions=(convolve_loop.expressions[0],
                                        dataclasses.replace(
                                            convolve_loop.expressions[1],
                                            operator="--")))
        loop_update = body_program(convolve, loop_update_body)

        loop_start_body = list(convolve.body)
        loop_initializer = convolve_loop.children[0].expressions[0]
        loop_start_body[14] = dataclasses.replace(
            convolve_loop, children=(dataclasses.replace(
                convolve_loop.children[0], expressions=(dataclasses.replace(
                    loop_initializer, children=(dataclasses.replace(
                        loop_initializer.children[0], literal="1",
                        literal_value=1),)),)), convolve_loop.children[1]))
        loop_start = body_program(convolve, loop_start_body)

        loop_comparison_body = list(convolve.body)
        loop_comparison_body[14] = dataclasses.replace(
            convolve_loop, expressions=(dataclasses.replace(
                loop_condition, operator="<="), convolve_loop.expressions[1]))
        loop_comparison = body_program(convolve, loop_comparison_body)

        loop_identity_body = list(convolve.body)
        loop_identity_body[14] = dataclasses.replace(
            convolve_loop, expressions=(dataclasses.replace(
                loop_condition, children=(dataclasses.replace(
                    loop_condition.children[0], symbol_id=52,
                    symbol=other_induction.symbol), loop_condition.children[1])),
                                        convolve_loop.expressions[1]))
        loop_identity = body_program(convolve, loop_identity_body)

        loop_control_body = list(convolve.body)
        loop_control_body[14] = dataclasses.replace(
            convolve_loop,
            children=(convolve_loop.children[0], dataclasses.replace(
                loop_block, children=(*loop_block.children,
                                      dataclasses.replace(
                                          convolve.body[16], kind="break",
                                          expressions=())))))
        loop_control = body_program(convolve, loop_control_body)

        def loop_control_program(kind):
            body = list(convolve.body)
            body[14] = dataclasses.replace(
                convolve_loop,
                children=(convolve_loop.children[0], dataclasses.replace(
                    loop_block, children=(*loop_block.children,
                                          dataclasses.replace(
                                              convolve.body[16], kind=kind,
                                              expressions=())))))
            return body_program(convolve, body)

        loop_continue = loop_control_program("continue")
        loop_return = loop_control_program("return")
        loop_conditional = loop_control_program("if")

        loop_body_reordered_body = list(convolve.body)
        loop_body_reordered_body[14] = dataclasses.replace(
            convolve_loop, children=(convolve_loop.children[0],
                                     dataclasses.replace(
                                         loop_block,
                                         children=tuple(reversed(
                                             loop_block.children)))))
        loop_body_reordered = body_program(convolve, loop_body_reordered_body)

        loop_body_missing_body = list(convolve.body)
        loop_body_missing_body[14] = dataclasses.replace(
            convolve_loop, children=(convolve_loop.children[0],
                                     dataclasses.replace(
                                         loop_block,
                                         children=loop_block.children[:-1])))
        loop_body_missing = body_program(convolve, loop_body_missing_body)

        mode_guard_body = list(main.body)
        mode_guard = mode_one.expressions[0]
        mode_guard_body[8] = dataclasses.replace(
            main.body[8], children=(main.body[8].children[0],
                                    dataclasses.replace(
                                        mode_one,
                                        expressions=(dataclasses.replace(
                                            mode_guard, operator="!="),))))
        mode_guard_program = body_program(main, mode_guard_body)

        divide_true_body = list(main.body)
        first_mode_statement = mode_one_block.children[0]
        def truthify(value):
            if value.kind == "literal" and value.type.display() == "bool":
                return dataclasses.replace(value, literal="true", literal_value=True)
            return dataclasses.replace(
                value, children=tuple(truthify(child) for child in value.children))
        divide_true_statement = dataclasses.replace(
            first_mode_statement,
            expressions=tuple(truthify(value)
                              for value in first_mode_statement.expressions))
        divide_true_block = dataclasses.replace(
            mode_one_block,
            children=(divide_true_statement, mode_one_block.children[1]))
        divide_true_body[8] = dataclasses.replace(
            main.body[8], children=(main.body[8].children[0],
                                    dataclasses.replace(
                                        mode_one, children=(divide_true_block,))))
        divide_true = body_program(main, divide_true_body)

        mode_zero_body = list(main.body)
        mode_zero_block = mode_zero_body[8].children[0]
        mode_zero_body[8] = dataclasses.replace(
            mode_zero_body[8], children=(dataclasses.replace(
                mode_zero_block,
                children=(*mode_zero_block.children,
                          mode_one_block.children[0])), mode_one))
        mode_zero_reachability = body_program(main, mode_zero_body)

        simultaneous_body = list(main.body)
        simultaneous_block = dataclasses.replace(
            mode_one_block,
            children=(dataclasses.replace(
                mode_one_block.children[0],
                expressions=(*mode_one_block.children[0].expressions,
                             *mode_one_block.children[1].expressions)),
                      mode_one_block.children[1]))
        simultaneous_body[8] = dataclasses.replace(
            main.body[8], children=(main.body[8].children[0],
                                    dataclasses.replace(
                                        mode_one,
                                        children=(simultaneous_block,))))
        simultaneous = body_program(main, simultaneous_body)

        span = typed.declarations[0].span
        forged_struct = StructDeclaration(
            900, "Forged", vector("float", 2), (), span)
        forged_block = UniformBlock(901, "ForgedBlock", None, (), span)
        forged_varying = Symbol(902, "forgedVarying", FLOAT, "input", span, False)
        time_declaration = typed.declarations[4]
        forged_global_symbol = dataclasses.replace(
            time_declaration.symbol, id=903, name="forgedGlobal",
            storage="const", writable=False)
        forged_global = TypedDeclaration(
            forged_global_symbol, FLOAT, span, convolve.body[12].expressions[0].children[0])

        mutations = {
            "wrong-key": dataclasses.replace(typed, key="wrong/refract:key"),
            "raw-source": dataclasses.replace(typed, raw_source=typed.raw_source + "\n"),
            "normalized-source": dataclasses.replace(typed, source=typed.source + "\n"),
            "define-contract": dataclasses.replace(
                typed, preprocessor_defines=(PreprocessorDefine(
                    "UNRELATED", "int", "1"),)),
            "source-changing-define": dataclasses.replace(
                typed, preprocessor_defines=(PreprocessorDefine(
                    "GL_ES", "int", "1"),)),
            "declaration-order": dataclasses.replace(
                typed, declarations=(typed.declarations[1], typed.declarations[0],
                                     *typed.declarations[2:])),
            "uniform-type": dataclasses.replace(
                typed, declarations=(typed.declarations[0], dataclasses.replace(
                    typed.declarations[1], type=FLOAT,
                    symbol=dataclasses.replace(
                        typed.declarations[1].symbol, type=FLOAT)),
                                     *typed.declarations[2:])),
            "uniform-storage": dataclasses.replace(
                typed, declarations=(dataclasses.replace(
                    typed.declarations[0], symbol=dataclasses.replace(
                        typed.declarations[0].symbol, storage="const")),
                                     *typed.declarations[1:])),
            "uniform-name": dataclasses.replace(
                typed, declarations=(dataclasses.replace(
                    typed.declarations[0], symbol=dataclasses.replace(
                        typed.declarations[0].symbol,
                        name="renamedInputTex")),
                                     *typed.declarations[1:])),
            "uniform-writable": dataclasses.replace(
                typed, declarations=(dataclasses.replace(
                    typed.declarations[0], symbol=dataclasses.replace(
                        typed.declarations[0].symbol, writable=True)),
                                     *typed.declarations[1:])),
            "uniform-symbol-id": dataclasses.replace(
                typed, declarations=(dataclasses.replace(
                    typed.declarations[0], symbol=dataclasses.replace(
                        typed.declarations[0].symbol, id=900)),
                                     *typed.declarations[1:])),
            "uniform-resource-order": dataclasses.replace(
                typed, resources=dataclasses.replace(
                    typed.resources,
                    uniforms=(typed.resources.uniforms[1],
                              typed.resources.uniforms[0],
                              *typed.resources.uniforms[2:]))),
            "resource-sampler": dataclasses.replace(
                typed, resources=dataclasses.replace(
                    typed.resources, samplers=())),
            "resource-output": dataclasses.replace(
                typed, resources=dataclasses.replace(
                    typed.resources, outputs=())),
            "resource-flags": dataclasses.replace(
                typed, resources=dataclasses.replace(
                    typed.resources, uses_derivatives=True)),
            "extra-struct": dataclasses.replace(typed, structs=(forged_struct,)),
            "extra-ubo": dataclasses.replace(typed, uniform_blocks=(forged_block,)),
            "extra-varying": dataclasses.replace(
                typed, interface_symbols=(forged_varying,)),
            "extra-global": dataclasses.replace(
                typed, declarations=(*typed.declarations, forged_global)),
            "compatibility-rhs": compatibility,
            "compatibility-restored-original": replace_function(typed, raw_blend),
            "compatibility-target": compatibility_target,
            "compatibility-wrong-operator": compatibility_extra,
            "compatibility-raw-operand": compatibility_raw_operand,
            "compatibility-raw-constant": compatibility_raw_constant,
            "compatibility-raw-true-arm": compatibility_raw_true,
            "compatibility-raw-false-builtin": compatibility_raw_false,
            "compatibility-raw-subtree": compatibility_raw_subtree,
            "compatibility-signature-name": replace_function_id(
                typed, 35, dataclasses.replace(
                    blend, signature=dataclasses.replace(
                        blend.signature, name="blendChanged"))),
            "compatibility-signature-return": replace_function_id(
                typed, 35, dataclasses.replace(
                    blend, signature=dataclasses.replace(
                        blend.signature, return_type=FLOAT))),
            "compatibility-body-count": replace_function(
                typed, dataclasses.replace(blend, body=blend.body[:-1])),
            "compatibility-site-missing": compatibility_missing,
            "compatibility-site-duplicated": compatibility_duplicated,
            "compatibility-extra-site": compatibility_duplicated,
            "compatibility-guard": replace_function(
                typed, dataclasses.replace(
                    blend, body=(*blend.body[:3], dataclasses.replace(
                        blend.body[3], expressions=(dataclasses.replace(
                            blend.body[3].expressions[0], operator="!="),)),
                                      *blend.body[4:]))),
            "compatibility-guard-order": replace_function(
                typed, dataclasses.replace(
                    blend, body=(*blend.body[:3], dataclasses.replace(
                        blend.body[3], expressions=(dataclasses.replace(
                            blend.body[3].expressions[0],
                            children=tuple(reversed(
                                blend.body[3].expressions[0].children))),)),
                                      *blend.body[4:]))),
            "compatibility-ancestry": replace_function(
                typed, dataclasses.replace(
                    blend, body=(*blend.body[:3], dataclasses.replace(
                        blend.body[3], children=tuple(reversed(
                            blend.body[3].children))), *blend.body[4:]))),
            "parameter-direction": parameter,
            "parameter-direction-inout": parameter_inout,
            "parameter-extent": parameter_extent,
            "parameter-element": parameter_vec2,
            "parameter-name": parameter_name,
            "parameter-ordinal": parameter_ordinal,
            "parameter-signature-id": parameter_signature_id,
            "parameter-literal-index": parameter_literal,
            "parameter-write": parameter_write_program,
            "parameter-update": parameter_update,
            "parameter-whole-copy": parameter_whole_copy,
            "parameter-whole-assignment": parameter_whole_assignment,
            "parameter-whole-store": parameter_whole_store,
            "parameter-return": parameter_return,
            "parameter-pass": parameter_pass,
            "parameter-different-induction": parameter_other_induction,
            "parameter-extra-read": extra_parameter_read,
            "offset-value": offset,
            "offset-initializer": offset_initializer,
            "offset-extent-eight": offset_extent_eight,
            "offset-extent-ten": offset_extent_ten,
            "offset-element": offset_float,
            "offset-storage": offset_declaration_program(storage="const"),
            "offset-name": offset_declaration_program(name="offsetChanged"),
            "offset-writable": offset_declaration_program(writable=False),
            "offset-symbol-id": offset_declaration_program(id=951),
            "offset-index": offset_index,
            "offset-span": offset_span,
            "offset-store-missing": body_program(
                convolve, (*convolve.body[:3], *convolve.body[4:])),
            "offset-store-duplicate": body_program(
                convolve, (*convolve.body[:4], convolve.body[3],
                           *convolve.body[4:])),
            "offset-store-reordered": body_program(
                convolve, (*convolve.body[:3], convolve.body[4],
                           convolve.body[3], *convolve.body[5:])),
            "offset-post-loop-write": body_program(
                convolve, (*convolve.body[:15], convolve.body[3],
                           *convolve.body[15:])),
            "offset-write-in-loop": offset_in_loop,
            "offset-pass-or-escape": offset_escape,
            "offset-return": offset_return,
            "loop-proof": loop,
            "loop-bound": loop_bound,
            "loop-update": loop_update,
            "loop-start": loop_start,
            "loop-comparison": loop_comparison,
            "loop-induction-identity": loop_identity,
            "loop-control": loop_control,
            "loop-continue": loop_continue,
            "loop-return": loop_return,
            "loop-conditional": loop_conditional,
            "loop-body-order": loop_body_reordered,
            "loop-body-missing": loop_body_missing,
            "loop-body-duplicate": body_program(
                convolve, (*convolve.body[:14], dataclasses.replace(
                    convolve_loop,
                    children=(convolve_loop.children[0], dataclasses.replace(
                        loop_block,
                        children=(*loop_block.children,
                                  loop_block.children[1])))),
                           *convolve.body[15:])),
            "loop-before-initialization": body_program(
                convolve, (*convolve.body[:2], convolve.body[14],
                           *convolve.body[2:14], *convolve.body[15:])),
            "caller-value": caller,
            "caller-extent": caller_extent,
            "caller-extent-ten": caller_extent_ten,
            "caller-element": caller_vec2,
            "caller-storage": caller_symbol_program(storage="const"),
            "caller-name": caller_symbol_program(name="deriv_x_changed"),
            "caller-writable": caller_symbol_program(writable=False),
            "caller-symbol-id": caller_symbol_program(id=957),
            "caller-initializer": caller_initializer,
            "caller-index": caller_index,
            "caller-dynamic-index": caller_dynamic,
            "caller-store-missing": body_program(
                deriv_x, (*deriv_x.body[:2], *deriv_x.body[3:])),
            "caller-store-duplicate": body_program(
                deriv_x, (*deriv_x.body[:3], deriv_x.body[2],
                          *deriv_x.body[3:])),
            "caller-store-reordered": body_program(
                deriv_x, (*deriv_x.body[:2], deriv_x.body[3],
                          deriv_x.body[2], *deriv_x.body[4:])),
            "caller-control-inserted": body_program(
                deriv_x, (*deriv_x.body[:6], convolve.body[15],
                          *deriv_x.body[6:])),
            "caller-loop-inserted": body_program(
                deriv_x, (*deriv_x.body[:6], convolve_loop,
                          *deriv_x.body[6:])),
            "caller-alias-copy": caller_alias,
            "caller-unary-minus": caller_unary,
            "caller-pre-initialization-read": caller_pre_read,
            "caller-return-before-call": caller_early_return,
            "caller-call-before-init": body_program(
                deriv_x, (*deriv_x.body[:2], deriv_x.body[11],
                          *deriv_x.body[2:11], deriv_x.body[12])),
            "caller-second-call": body_program(
                deriv_x, (*deriv_x.body[:12], deriv_x.body[11],
                          deriv_x.body[12])),
            "caller-post-call-use": body_program(
                deriv_x, (*deriv_x.body[:12], deriv_x.body[2],
                          deriv_x.body[12])),
            "call-target": caller_call_program(
                lambda call: dataclasses.replace(
                    call, callee="derivY", signature_id=40)),
            "call-argument-order": caller_call_program(
                lambda call: dataclasses.replace(
                    call, children=(call.children[1], call.children[0],
                                    call.children[2]))),
            "call-argument-removed": caller_call_program(
                lambda call: dataclasses.replace(
                    call, children=(call.children[0], call.children[2]))),
            "call-argument-duplicated": caller_call_program(
                lambda call: dataclasses.replace(
                    call, children=(call.children[0], call.children[1],
                                    call.children[1], call.children[2]))),
            "call-wrong-array": caller_call_program(
                lambda call: dataclasses.replace(
                    call, children=(call.children[0], dataclasses.replace(
                        call.children[1], symbol_id=60,
                        symbol=deriv_y_array.symbol), call.children[2]))),
            "main-call-order": reachability,
            "main-mode-guard": mode_guard_program,
            "main-divide": divide_true,
            "main-mode-zero-reachability": mode_zero_reachability,
            "main-simultaneous-caller-liveness": simultaneous,
            "main-call-outside-mode-one": body_program(
                main, (*main.body[:9], mode_one_block.children[0],
                       *main.body[9:])),
            "cross-proof-fixed-nine": dataclasses.replace(
                typed, fixed_nine_table_proof=proof),
            "cross-proof-fixed-grid": dataclasses.replace(
                typed, fixed_grid_counter_store_proof=proof),
        }

        for index in range(9):
            body = list(convolve.body)
            store = body[3 + index].expressions[0]
            replacement = (convolve.body[7].expressions[0].children[1]
                           if index != 4
                           else convolve.body[3].expressions[0].children[1])
            body[3 + index] = dataclasses.replace(
                body[3 + index], expressions=(dataclasses.replace(
                    store, children=(store.children[0], replacement)),))
            mutations[f"offset-value-{index}"] = body_program(convolve, body)

        for field, value in {
            "lexical_depth": 2,
            "effective_depth": 2,
            "lexical_product": 18,
            "entrypoint_charge": 17,
        }.items():
            body = list(convolve.body)
            body[14] = dataclasses.replace(
                convolve_loop,
                loop_proof=dataclasses.replace(
                    convolve_loop.loop_proof, **{field: value}))
            mutations[f"loop-proof-{field.replace('_', '-')}"] = body_program(
                convolve, body)

        for name, candidate in mutations.items():
            attacker = dataclasses.replace(
                proof,
                typed_ir_sha256=hashlib.sha256(
                    repr(candidate.functions).encode("utf-8")).hexdigest(),
                interface_sha256=proof_module._interface_fingerprint(candidate),
                whole_program_sha256=proof_module._whole_program_fingerprint(candidate))
            for proof_mode, carried in {
                "authentic": proof,
                "cleared": None,
                "stale": dataclasses.replace(proof, loop_trip_count=8),
                "attacker-updated": attacker,
            }.items():
                forged = dataclasses.replace(
                    candidate, fixed_array_in_parameter_proof=carried)
                with self.subTest(name=name, proof=proof_mode,
                                  boundary="validator"), self.assertRaises(
                        generate_typed_slice.GeneratorError):
                    generate_typed_slice.validate_capabilities(
                        forged, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=entry["raw_sha256"])
                with self.subTest(name=name, proof=proof_mode,
                                  boundary="emitter"), self.assertRaises(
                        TypedEmissionError):
                    render_typed_cpp(
                        forged, entry["program_key"], entry["raw_sha256"])

        for name, changed_proof in {
            "factory-hash": dataclasses.replace(
                proof, canonical_factory_sha256="0" * 64),
            "abi-by-value": dataclasses.replace(
                proof, parameter=dataclasses.replace(
                    proof.parameter, native_abi="Kernel9")),
            "abi-mutable-reference": dataclasses.replace(
                proof, parameter=dataclasses.replace(
                    proof.parameter, native_abi="Kernel9&")),
            "abi-pointer": dataclasses.replace(
                proof, parameter=dataclasses.replace(
                    proof.parameter, native_abi="Kernel9*")),
            "abi-span": dataclasses.replace(
                proof, parameter=dataclasses.replace(
                    proof.parameter,
                    native_abi="std::span<const double>")),
            "mode-zero-proof": dataclasses.replace(
                proof, mode_zero_array_free=False),
            "simultaneous-proof": dataclasses.replace(
                proof, caller_tables_never_simultaneously_live=False),
            "retained-proof": dataclasses.replace(
                proof, no_alias_copy_escape_return_or_post_call_use=False),
        }.items():
            candidate = dataclasses.replace(
                typed, fixed_array_in_parameter_proof=changed_proof)
            with self.subTest(name=name, boundary="validator"), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=entry["raw_sha256"])
            with self.subTest(name=name, boundary="emitter"), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    candidate, entry["program_key"], entry["raw_sha256"])

        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                typed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash="0" * 64)
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(typed, entry["program_key"], "0" * 64)

    def test_refract_fixed_array_parameter_exclusions_and_task17_task18_regressions(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend import fixed_array_in_parameter_proof as proof_module
        from tools.glslcpp.frontend.fixed_array_in_parameter_proof import (
            attach_fixed_array_in_parameter_proof,
        )
        from tools.glslcpp.frontend.refract_compatibility import (
            apply_refract_truthy_vector_noops,
        )
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.semantic_types import FLOAT, array, struct, vector

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())

        def corpus_program(key):
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            raw = (root / entry["source"]).read_text()
            return entry, analyze_program(parse_program(raw, key, {}), key)

        entry, analyzed = corpus_program("classicNoisedeck/refract:refract")
        typed = attach_fixed_array_in_parameter_proof(
            apply_refract_truthy_vector_noops(analyzed))
        convolve = next(function for function in typed.functions
                        if function.signature.id == 38 and function.body)

        def parameter_type_program(type_value, key=typed.key):
            parameters = list(convolve.parameters)
            parameters[1] = dataclasses.replace(parameters[1], type=type_value)
            replacement = dataclasses.replace(
                convolve, signature=dataclasses.replace(
                    convolve.signature, parameters=tuple(parameters)))
            return dataclasses.replace(
                typed, key=key,
                functions=tuple(replacement if function.signature.id == 38
                                else function for function in typed.functions))

        exclusions = {
            "analogous-other-key": dataclasses.replace(
                typed, key="fixture/analogous:arrayParameter"),
            "other-extent": parameter_type_program(array(FLOAT, 8)),
            "other-element": parameter_type_program(
                array(vector("float", 2), 9)),
            "nested-array": parameter_type_program(
                array(array(FLOAT, 3), 3)),
            "multidimensional-array": parameter_type_program(
                array(array(FLOAT, 9), 9)),
            "struct-array": parameter_type_program(
                array(struct(999, "FixtureCell"), 9)),
        }
        for name, candidate in exclusions.items():
            proof = typed.fixed_array_in_parameter_proof
            attacker = dataclasses.replace(
                proof,
                typed_ir_sha256=hashlib.sha256(
                    repr(candidate.functions).encode("utf-8")).hexdigest(),
                interface_sha256=proof_module._interface_fingerprint(candidate),
                whole_program_sha256=proof_module._whole_program_fingerprint(candidate))
            for carried_name, carried in {
                "authentic": proof,
                "cleared": None,
                "stale": dataclasses.replace(proof, loop_trip_count=8),
                "attacker-updated": attacker,
            }.items():
                forged = dataclasses.replace(
                    candidate, fixed_array_in_parameter_proof=carried)
                with self.subTest(name=name, proof=carried_name,
                                  boundary="validator"), self.assertRaises(
                        generate_typed_slice.GeneratorError):
                    generate_typed_slice.validate_capabilities(
                        forged, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=entry["raw_sha256"])
                with self.subTest(name=name, proof=carried_name,
                                  boundary="emitter"), self.assertRaises(
                        TypedEmissionError):
                    render_typed_cpp(
                        forged, forged.key, entry["raw_sha256"])

        sacred_entry, sacred = corpus_program(
            "synth/sacredGeometry:sacredGeometry")
        self.assertIsNone(sacred.fixed_array_in_parameter_proof)
        proof = typed.fixed_array_in_parameter_proof
        sacred_attacker = dataclasses.replace(
            proof,
            typed_ir_sha256=hashlib.sha256(
                repr(sacred.functions).encode("utf-8")).hexdigest(),
            interface_sha256=proof_module._interface_fingerprint(sacred),
            whole_program_sha256=proof_module._whole_program_fingerprint(sacred))
        for carried_name, carried in {
            "authentic": proof,
            "cleared": None,
            "stale": dataclasses.replace(proof, loop_trip_count=8),
            "attacker-updated": sacred_attacker,
        }.items():
            forged = dataclasses.replace(
                sacred, fixed_array_in_parameter_proof=carried)
            with self.subTest(key=sacred.key, proof=carried_name,
                              boundary="validator"), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    forged, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=sacred_entry["raw_sha256"])
            with self.subTest(key=sacred.key, proof=carried_name,
                              boundary="emitter"), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    forged, sacred.key, sacred_entry["raw_sha256"])

        for key, expected_proof in {
            "filter/sharpen:sharpen": "fixed_nine_table_proof",
            "filter/sobel:sobel": "fixed_nine_table_proof",
            "filter/celShading:celShadingEdges": "fixed_grid_counter_store_proof",
            "filter/outline:outlineSobel": "fixed_grid_counter_store_proof",
        }.items():
            prior_entry, prior = corpus_program(key)
            self.assertIsNone(prior.fixed_array_in_parameter_proof)
            self.assertIsNotNone(getattr(prior, expected_proof))
            with self.subTest(key=key, boundary="validator"):
                generate_typed_slice.validate_capabilities(
                    prior, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=prior_entry["raw_sha256"])
            with self.subTest(key=key, boundary="emitter"):
                render_typed_cpp(prior, key, prior_entry["raw_sha256"])

    def test_fixed_grid_counter_store_validates_and_emits_only_exact_proved_sites(self) -> None:
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        for key, (dimension, sampler) in {
            "filter/celShading:celShadingEdges": ("texSize", "colorTex"),
            "filter/outline:outlineSobel": ("dimensions", "valueTexture"),
        }.items():
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            raw = (root / entry["source"]).read_text()
            typed = analyze_program(parse_program(raw, key, {}), key)
            with self.subTest(key=key):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=entry["raw_sha256"])
                emitted = render_typed_cpp(typed, key, entry["raw_sha256"])
                self.assertEqual(1, emitted.count("std::array<double, 9> samples{};"))
                self.assertEqual(1, emitted.count(
                    "samples[static_cast<std::size_t>(idx)] ="))
                self.assertEqual(1, emitted.count("++idx;"))
                self.assertEqual(12, sum(emitted.count(f"samples[{index}]")
                                         for index in (0, 1, 2, 3, 5, 6, 7, 8)))
                self.assertNotIn("samples[4]", emitted)
                self.assertNotIn(".at(", emitted)
                self.assertNotIn("std::vector", emitted)
                self.assertNotIn("std::array<float", emitted)
                self.assertIn("noexcept", emitted)
                pixel = emitted[emitted.index("void pixel("):]
                texture_size = pixel.index(
                    f"{dimension} = texture_size(*state.{sampler});")
                exact_predicate = pixel.index(
                    f"if ((glsl::swizzle<0>({dimension}) == std::int32_t(0)) || "
                    f"(glsl::swizzle<1>({dimension}) == std::int32_t(0))) {{")
                zero_assignment = pixel.index(
                    "output = glsl::Vec4(glsl::FloatExpr<4>(static_cast<float>(0.0)));",
                    exact_predicate)
                early_return = pixel.index("return;", zero_assignment)
                array = pixel.index("std::array<double, 9> samples{};")
                fetch = pixel.index("fetch_texel(", array)
                store = pixel.index("samples[static_cast<std::size_t>(idx)] =")
                update = pixel.index("++idx;")
                first_read = pixel.index("samples[0]", store + 1)
                self.assertLess(texture_size, exact_predicate)
                self.assertLess(exact_predicate, zero_assignment)
                self.assertLess(zero_assignment, early_return)
                self.assertLess(early_return, array)
                self.assertLess(array, fetch)
                self.assertLess(array, store)
                self.assertLess(store, update)
                self.assertLess(update, first_read)

    def test_fixed_grid_counter_store_provenance_and_whole_program_tampering_reject_at_both_boundaries(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        for key in ("filter/celShading:celShadingEdges",
                    "filter/outline:outlineSobel"):
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            raw = (root / entry["source"]).read_text()
            typed = analyze_program(parse_program(raw, key, {}), key)
            provenance_candidates = {
                "raw": dataclasses.replace(typed, raw_source=raw + "\n"),
                "normalized": dataclasses.replace(typed, source=typed.source + "\n"),
                "same-normalized-define": analyze_program(
                    parse_program(raw, key, {"UNRELATED": 1}), key),
                "changed-normalized-define": analyze_program(
                    parse_program(raw, key, {"GL_ES": 1}), key),
            }
            for name, candidate in provenance_candidates.items():
                with self.subTest(key=key, mutation=name, boundary="validator"), self.assertRaisesRegex(
                        generate_typed_slice.GeneratorError, "source provenance"):
                    generate_typed_slice.validate_capabilities(
                        candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=entry["raw_sha256"])
                with self.subTest(key=key, mutation=name, boundary="emitter"), self.assertRaisesRegex(
                        TypedEmissionError, "source provenance"):
                    render_typed_cpp(candidate, key, entry["raw_sha256"])
            with self.subTest(key=key, mutation="caller-digest", boundary="validator"), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError, "source provenance"):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash="0" * 64)
            with self.subTest(key=key, mutation="caller-digest", boundary="emitter"), self.assertRaisesRegex(
                    TypedEmissionError, "source provenance"):
                render_typed_cpp(typed, key, "0" * 64)
            wrong_key = dataclasses.replace(typed, key="forged-task18-key")
            with self.subTest(key=key, mutation="wrong-key", boundary="validator"), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError, "malformed fixed-grid"):
                generate_typed_slice.validate_capabilities(
                    wrong_key, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=entry["raw_sha256"])
            with self.subTest(key=key, mutation="wrong-key", boundary="emitter"), self.assertRaisesRegex(
                    TypedEmissionError, "malformed fixed-grid"):
                render_typed_cpp(wrong_key, wrong_key.key, entry["raw_sha256"])

    def test_fixed_grid_counter_store_control_index_and_update_forgery_reject_at_both_boundaries(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())

        def mutate_first(program, predicate, change):
            matched = False

            def expression(value):
                nonlocal matched
                if not matched and predicate(value):
                    matched = True
                    return change(value)
                return dataclasses.replace(
                    value, children=tuple(expression(child)
                                          for child in value.children))

            def statement(value):
                return dataclasses.replace(
                    value,
                    expressions=tuple(expression(item)
                                      for item in value.expressions),
                    children=tuple(statement(child) for child in value.children))

            functions = tuple(dataclasses.replace(
                function, body=tuple(statement(item) for item in function.body))
                for function in program.functions)
            self.assertTrue(matched)
            return dataclasses.replace(program, functions=functions)

        def mutate_first_statement(program, predicate, change):
            matched = False

            def statement(value):
                nonlocal matched
                if not matched and predicate(value):
                    matched = True
                    return change(value)
                return dataclasses.replace(
                    value, children=tuple(statement(child)
                                          for child in value.children))

            functions = tuple(dataclasses.replace(
                function, body=tuple(statement(item) for item in function.body))
                for function in program.functions)
            self.assertTrue(matched)
            return dataclasses.replace(program, functions=functions)

        def replace_main_body(program, signature_id, body):
            return dataclasses.replace(
                program,
                functions=tuple(
                    dataclasses.replace(function, body=tuple(body))
                    if function.signature.id == signature_id else function
                    for function in program.functions))

        def walk_expression(value):
            yield value
            for child in value.children:
                yield from walk_expression(child)

        def walk_statement(value):
            for expression in value.expressions:
                yield from walk_expression(expression)
            for child in value.children:
                yield from walk_statement(child)

        for key in ("filter/celShading:celShadingEdges",
                    "filter/outline:outlineSobel"):
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            raw = (root / entry["source"]).read_text()
            typed = analyze_program(parse_program(raw, key, {}), key)
            proof = typed.fixed_grid_counter_store_proof
            self.assertIsNotNone(proof)
            main = next(function for function in typed.functions
                        if function.signature.id == proof.main_signature_id)
            expressions = tuple(node for statement in main.body
                                for node in walk_statement(statement))
            dynamic_store = next(
                node for node in expressions
                if node.kind == "index"
                and node.span == proof.dynamic_store_index_span)
            counter_identifier = dynamic_store.children[1]
            counter_literal = main.body[
                proof.counter_declaration_statement_index].expressions[0].children[0]
            early_removed = main.body[:proof.early_return_statement_index] + main.body[
                proof.early_return_statement_index + 1:]
            early_moved = list(main.body)
            early_moved[proof.early_return_statement_index], early_moved[
                proof.array_declaration_statement_index] = (
                    early_moved[proof.array_declaration_statement_index],
                    early_moved[proof.early_return_statement_index])
            declaration_reordered = list(main.body)
            declaration_reordered[proof.array_declaration_statement_index], declaration_reordered[
                proof.counter_declaration_statement_index] = (
                    declaration_reordered[proof.counter_declaration_statement_index],
                    declaration_reordered[proof.array_declaration_statement_index])
            grid = main.body[proof.outer_loop_statement_index]
            inner = grid.children[1].children[0]
            inner_body = inner.children[1]
            store_statement = next(
                child for child in inner_body.children
                if child.span == proof.dynamic_store_statement_span)
            update_statement = next(
                child for child in inner_body.children
                if child.span == proof.counter_update_statement_span)
            post_grid_update = list(main.body)
            post_grid_update.insert(proof.outer_loop_statement_index + 1,
                                    update_statement)
            post_grid_store = list(main.body)
            post_grid_store.insert(proof.outer_loop_statement_index + 1,
                                   store_statement)
            candidates = {
                "removed-early-return": replace_main_body(
                    typed, proof.main_signature_id, early_removed),
                "moved-early-return": replace_main_body(
                    typed, proof.main_signature_id, early_moved),
                "weakened-early-predicate": mutate_first(
                    typed,
                    lambda value: (value.kind == "binary"
                                   and value.operator == "||"
                                   and value.span == proof.zero_predicate_span),
                    lambda value: dataclasses.replace(value, operator="&&")),
                "changed-zero-assignment": mutate_first(
                    typed,
                    lambda value: (value.kind == "literal"
                                   and value.literal == "0.0"
                                   and proof.zero_assignment_span.start
                                   <= value.span.start < proof.zero_assignment_span.end),
                    lambda value: dataclasses.replace(
                        value, literal="1.0", literal_value=1.0)),
                "return-with-value": mutate_first_statement(
                    typed,
                    lambda value: value.span == proof.zero_return_span,
                    lambda value: dataclasses.replace(
                        value, expressions=(counter_literal,))),
                "array-extent-eight": mutate_first(
                    typed,
                    lambda value: (value.kind == "declaration"
                                   and value.symbol_id == proof.array_symbol_id),
                    lambda value: dataclasses.replace(
                        value,
                        type=dataclasses.replace(value.type, size=8),
                        symbol=dataclasses.replace(
                            value.symbol,
                            type=dataclasses.replace(value.type, size=8)))),
                "array-initializer": mutate_first(
                    typed,
                    lambda value: (value.kind == "declaration"
                                   and value.symbol_id == proof.array_symbol_id),
                    lambda value: dataclasses.replace(
                        value, children=(counter_literal,))),
                "counter-initializer-one": mutate_first(
                    typed,
                    lambda value: value.span == proof.counter_initializer_span,
                    lambda value: dataclasses.replace(
                        value, literal="1", literal_value=1)),
                "declaration-reorder": replace_main_body(
                    typed, proof.main_signature_id, declaration_reordered),
                "postfix-loop-header": mutate_first(
                    typed,
                    lambda value: (value.kind == "unary"
                                   and value.operator == "++"
                                   and value.children
                                   and value.children[0].symbol_id
                                   == proof.outer_induction_symbol_id),
                    lambda value: dataclasses.replace(value, kind="post")),
                "postfix-inner-loop-header": mutate_first(
                    typed,
                    lambda value: (value.kind == "unary"
                                   and value.operator == "++"
                                   and value.children
                                   and value.children[0].symbol_id
                                   == proof.inner_induction_symbol_id),
                    lambda value: dataclasses.replace(value, kind="post")),
                "literal-dynamic-store": mutate_first(
                    typed,
                    lambda value: (value.kind == "index"
                                   and value.span == proof.dynamic_store_index_span),
                    lambda value: dataclasses.replace(
                        value, children=(value.children[0], dataclasses.replace(
                            value.children[1], kind="literal", symbol_id=None,
                            symbol=None, children=(), literal="0",
                            literal_value=0)))),
                "changed-store-rhs": mutate_first(
                    typed,
                    lambda value: (value.kind == "assign"
                                   and value.children
                                   and value.children[0].span
                                   == proof.dynamic_store_index_span),
                    lambda value: dataclasses.replace(
                        value, children=(value.children[0], counter_literal))),
                "store-update-reorder": mutate_first_statement(
                    typed,
                    lambda value: (value.kind == "block"
                                   and any(child.span
                                           == proof.counter_update_statement_span
                                           for child in value.children)),
                    lambda value: dataclasses.replace(
                        value, children=value.children[:-2]
                        + (value.children[-1], value.children[-2]))),
                "duplicate-store": mutate_first_statement(
                    typed,
                    lambda value: (value.kind == "block"
                                   and any(child.span
                                           == proof.counter_update_statement_span
                                           for child in value.children)),
                    lambda value: dataclasses.replace(
                        value, children=value.children[:-1]
                        + (value.children[-2], value.children[-1]))),
                "duplicate-update": mutate_first_statement(
                    typed,
                    lambda value: (value.kind == "block"
                                   and any(child.span
                                           == proof.counter_update_statement_span
                                           for child in value.children)),
                    lambda value: dataclasses.replace(
                        value, children=value.children + (value.children[-1],))),
                "prefix-counter-update": mutate_first(
                    typed,
                    lambda value: (value.kind == "post"
                                   and value.span
                                   == proof.counter_update_expression_span),
                    lambda value: dataclasses.replace(value, kind="unary")),
                "index-four-read": mutate_first(
                    typed,
                    lambda value: (value.kind == "index"
                                   and value.span == proof.literal_reads[0].index_span),
                    lambda value: dataclasses.replace(
                        value, children=(value.children[0], dataclasses.replace(
                            value.children[1], literal="4", literal_value=4)))),
                "dynamic-read": mutate_first(
                    typed,
                    lambda value: (value.kind == "index"
                                   and value.span == proof.literal_reads[0].index_span),
                    lambda value: dataclasses.replace(
                        value, children=(value.children[0], counter_identifier))),
                "post-grid-counter-use": replace_main_body(
                    typed, proof.main_signature_id, post_grid_update),
                "post-grid-array-write": replace_main_body(
                    typed, proof.main_signature_id, post_grid_store),
            }
            for name, candidate in candidates.items():
                with self.subTest(key=key, mutation=name, boundary="validator"), self.assertRaisesRegex(
                        generate_typed_slice.GeneratorError,
                        "malformed fixed-grid whole-program profile"):
                    generate_typed_slice.validate_capabilities(
                        candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=entry["raw_sha256"])
                with self.subTest(key=key, mutation=name, boundary="emitter"), self.assertRaisesRegex(
                        TypedEmissionError,
                        "malformed fixed-grid whole-program profile"):
                    render_typed_cpp(candidate, key, entry["raw_sha256"])

            structural_candidates = {
                "cleared": dataclasses.replace(
                    typed, fixed_grid_counter_store_proof=None),
                "stale-interval": dataclasses.replace(
                    typed, fixed_grid_counter_store_proof=dataclasses.replace(
                        proof, store_upper_bound=9)),
                "resource": dataclasses.replace(
                    typed, resources=dataclasses.replace(
                        typed.resources,
                        uniforms=typed.resources.uniforms + ("forged",))),
            }
            for name, candidate in structural_candidates.items():
                with self.subTest(key=key, mutation=name, boundary="validator"), self.assertRaisesRegex(
                        generate_typed_slice.GeneratorError,
                        "malformed fixed-grid whole-program profile"):
                    generate_typed_slice.validate_capabilities(
                        candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=entry["raw_sha256"])
                with self.subTest(key=key, mutation=name, boundary="emitter"), self.assertRaisesRegex(
                        TypedEmissionError,
                        "malformed fixed-grid whole-program profile"):
                    render_typed_cpp(candidate, key, entry["raw_sha256"])

    def test_fixed_grid_counter_store_keeps_refract_and_sacred_geometry_excluded_at_both_boundaries(self) -> None:
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        for key in ("classicNoisedeck/refract:refract",
                    "synth/sacredGeometry:sacredGeometry"):
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            raw = (root / entry["source"]).read_text()
            typed = analyze_program(parse_program(raw, key, {}), key)
            self.assertIsNone(typed.fixed_grid_counter_store_proof)
            with self.subTest(key=key, boundary="validator"), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=entry["raw_sha256"])
            with self.subTest(key=key, boundary="emitter"), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(typed, key, entry["raw_sha256"])

    def test_fixed_nine_slice_validates_and_emits_only_exact_proved_tables(self) -> None:
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        for key, expected_lines in {
            "filter/sharpen:sharpen": (
                "std::array<double, 9> kernel{};",
                "std::array<glsl::Vec2, 9> offsets{};",
            ),
            "filter/sobel:sobel": (
                "std::array<double, 9> sobel_x{};",
                "std::array<double, 9> sobel_y{};",
                "std::array<glsl::Vec2, 9> offsets{};",
            ),
        }.items():
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            raw = (root / entry["source"]).read_text()
            typed = analyze_program(parse_program(raw, key, {}), key)
            with self.subTest(key=key):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=entry["raw_sha256"])
                emitted = render_typed_cpp(typed, key, entry["raw_sha256"])
                for line in expected_lines:
                    self.assertIn(line, emitted)
                self.assertIn("offsets[i]", emitted)
                self.assertNotIn(".at(", emitted)
                self.assertNotIn("std::vector", emitted)

    def test_fixed_nine_provenance_rejects_define_and_raw_source_forgery_at_both_boundaries(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "filter/sharpen:sharpen")
        raw = (root / entry["source"]).read_text()
        candidates = (
            analyze_program(parse_program(raw, entry["program_key"], {"UNRELATED": 1}),
                            entry["program_key"]),
            analyze_program(parse_program(raw, entry["program_key"], {"GL_ES": 1}),
                            entry["program_key"]),
            dataclasses.replace(
                analyze_program(parse_program(raw, entry["program_key"], {}),
                                entry["program_key"]),
                raw_source=raw + "\n"),
        )
        for index, candidate in enumerate(candidates):
            with self.subTest(index=index, boundary="validator"), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError, "source provenance"):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=entry["raw_sha256"])
            with self.subTest(index=index, boundary="emitter"), self.assertRaisesRegex(
                    TypedEmissionError, "source provenance"):
                render_typed_cpp(candidate, candidate.key, entry["raw_sha256"])

    def test_fixed_nine_structural_proof_tampering_is_rejected_at_both_boundaries(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "filter/sobel:sobel")
        raw = (root / entry["source"]).read_text()
        typed = analyze_program(parse_program(raw, entry["program_key"], {}), entry["program_key"])
        proof = dataclasses.replace(typed.fixed_nine_table_proof, trip_count=8)
        malformed = dataclasses.replace(typed, fixed_nine_table_proof=proof)
        with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                    "malformed fixed-nine"):
            generate_typed_slice.validate_capabilities(
                malformed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=entry["raw_sha256"])
        with self.assertRaisesRegex(TypedEmissionError, "malformed fixed-nine"):
            render_typed_cpp(malformed, malformed.key, entry["raw_sha256"])

    def test_fixed_nine_whole_program_profile_rejects_binding_resource_and_global_array_forgery(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.typed_ir import TypedDeclaration

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        for key in ("filter/sharpen:sharpen", "filter/sobel:sobel"):
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            raw = (root / entry["source"]).read_text()
            typed = analyze_program(parse_program(raw, key, {}), key)
            fresh_id = max(item.symbol.id for item in typed.declarations) + 10000

            amount = next(item for item in typed.declarations
                          if item.symbol.name == "amount")
            extra_symbol = dataclasses.replace(
                amount.symbol, id=fresh_id, name="forgedExtra")
            extra_uniform = dataclasses.replace(amount, symbol=extra_symbol)
            extra_resources = dataclasses.replace(
                typed.resources,
                uniforms=typed.resources.uniforms + ("forgedExtra",))

            main = next(function for function in typed.functions
                        if function.name == "main")
            local_array = next(expression for statement in main.body
                               for expression in statement.expressions
                               if expression.kind == "declaration"
                               and expression.type.display() == "float[9]")
            global_symbol = dataclasses.replace(
                local_array.symbol, id=fresh_id + 1, name="forgedGlobalArray",
                storage="output")
            global_array = TypedDeclaration(
                global_symbol, local_array.type, local_array.span)
            output_resources = dataclasses.replace(
                typed.resources,
                outputs=typed.resources.outputs + ("forgedGlobalArray",))

            candidates = {
                "extra-uniform": dataclasses.replace(
                    typed, declarations=typed.declarations + (extra_uniform,),
                    resources=extra_resources),
                "resources-only": dataclasses.replace(
                    typed, resources=dataclasses.replace(
                        typed.resources,
                        uniforms=typed.resources.uniforms + ("forgedExtra",))),
                "global-array-output": dataclasses.replace(
                    typed, declarations=typed.declarations + (global_array,),
                    resources=output_resources),
            }
            def attacker_hash(program) -> str:
                profile = (
                    program.key, program.source, program.raw_source,
                    program.declarations, program.functions, program.resources,
                    program.body_status, program.local_type_names,
                    program.structs, program.uniform_blocks,
                    program.interface_symbols, program.builtin_symbols,
                    program.counted_loop_proof, program.preprocessor_defines,
                )
                return hashlib.sha256(repr(profile).encode("utf-8")).hexdigest()

            for name, forged in candidates.items():
                proof_variants = {
                    "retained": forged,
                    "cleared": dataclasses.replace(
                        forged, fixed_nine_table_proof=None),
                    "attacker-updated": dataclasses.replace(
                        forged,
                        fixed_nine_table_proof=dataclasses.replace(
                            forged.fixed_nine_table_proof,
                            whole_program_sha256=attacker_hash(forged))),
                }
                for proof_mode, candidate in proof_variants.items():
                    with self.subTest(key=key, forgery=name, proof=proof_mode,
                                      boundary="validator"), self.assertRaisesRegex(
                            generate_typed_slice.GeneratorError,
                            "malformed fixed-nine whole-program profile"):
                        generate_typed_slice.validate_capabilities(
                            candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                            source_hash=entry["raw_sha256"])
                    with self.subTest(key=key, forgery=name, proof=proof_mode,
                                      boundary="emitter"), self.assertRaisesRegex(
                            TypedEmissionError,
                            "malformed fixed-nine whole-program profile"):
                        render_typed_cpp(candidate, candidate.key,
                                         entry["raw_sha256"])

    def test_allowlist_is_schema_locked_sorted_and_contains_exactly_one_hundred_twenty_six_typed_keys(self) -> None:
        from tools.glslcpp import generate_typed_slice

        slice_spec = generate_typed_slice.load_slice(REPOSITORY)
        self.assertEqual(1, slice_spec["schema"])
        self.assertEqual("a024dc3a960cc44af454abc7aebce50456c194e6", slice_spec["revision"])
        self.assertEqual({"filter/scatter:scatterJitter": "source-double"},
                         slice_spec["numeric_literal_contracts"])
        self.assertEqual({"classicNoisedeck/coalesce:coalesce": "coalesce-uv-alias-v1",
                          "classicNoisedeck/refract:refract":
                              "refract-truthy-vector-conditional-noop-v1",
                          "filter/corrupt:corrupt": "corrupt-sample-uv-alias-v1",
                          "filter/crt:crt": "crt-metal-sine-v1",
                          "mixer/shapeMask:shapeMask": "shape-mask-sequential-lanes-v1",
                          "synth/polygon:shape": "polygon-zero-smoothing-v1",
                          "synth/sacredGeometry:sacredGeometry":
                              "sacred-star-number-division-v1"},
                         slice_spec["compatibility_transforms"])
        self.assertEqual({
            "classicNoisedeck/lensDistortion:lensDistortion":
                "canonical-js-vector-equality-result-truthiness-v1",
        }, slice_spec["custom_comparer_profiles"])
        existing = [
            "classicNoisedeck/coalesce:coalesce",
            "classicNoisedeck/composite:composite",
            "classicNoisedeck/splat:splat",
            "filter/bc:bc",
            "filter/bloom:brightPass",
            "filter/bloom:composite",
            "filter/celShading:celShadingBlend",
            "filter/channel:channel",
            "filter/chroma:chroma",
            "filter/chromaticAberration:chromaticAberration",
            "filter/chrome:chMap",
            "filter/colorReplace:colorReplace",
            "filter/corrupt:corrupt",
            "filter/deriv:deriv",
            "filter/fibers:fibersBlend",
            "filter/flipMirror:flipMirror",
            "filter/glowingEdge:glowingEdge",
            "filter/highPass:hpCombine",
            "filter/hs:hs",
            "filter/lensFlare:lensFlare",
            "filter/mosaicTiles:mosaicTiles",
            "filter/normalize:apply",
            "filter/outline:outlineBlend",
            "filter/outline:outlineValueMap",
            "filter/photocopy:pcCombine",
            "filter/pixelSort:finalize",
            "filter/pixelSort:luminance",
            "filter/pixelSort:prepare",
            "filter/pixels:pixels",
            "filter/plasticWrap:pwSpec",
            "filter/reindex:nmReindexApply",
            "filter/relief:rlShade",
            "filter/repeat:repeat",
            "filter/ridge:ridge",
            "filter/scale:scale",
            "filter/scatter:scatterJitter",
            "filter/scratches:scratchesBlend",
            "filter/scroll:scroll",
            "filter/seamless:seamless",
            "filter/simpleAberration:chromaticAberration",
            "filter/sine:sine",
            "filter/skew:skew",
            "filter/smoothstep:smoothstep",
            "filter/spatter:spatter",
            "filter/strayHair:strayHairBlend",
            "filter/tetraCosine:tetraCosine",
            "filter/text:text",
            "filter/threshold:thresh",
            "filter/tile:tile",
            "filter/tint:colorize",
            "filter/translate:translate",
            "filter/unsharpMask:usmCombine",
            "filter/vignette:vignette",
            "filter/watercolor:wcComposite",
            "filter/watercolor:wcSeed",
            "filter/wormhole:clear",
            "mixer/alphaMask:alphaMask",
            "mixer/applyMode:applyMode",
            "mixer/blendMode:blendMode",
            "mixer/centerMask:centerMask",
            "mixer/channelCombine:channelCombine",
            "mixer/patternMix:patternMix",
            "mixer/shapeMask:shapeMask",
            "mixer/split:split",
            "mixer/thresholdMix:thresholdMix",
            "mixer/uvRemap:uvRemap",
            "synth/media:mediaInput",
            "synth/modPattern:modPattern",
            "synth/osc2d:osc2d",
            "synth/pattern:pattern",
            "synth/polygon:shape",
        ]
        task15 = {
            "filter/chrome:chBlurH", "filter/chrome:chBlurV", "filter/clouds:clouds",
            "filter/craquelure:craquelure", "filter/hatch:hatch",
            "filter/highPass:hpBlurH", "filter/highPass:hpBlurV",
            "filter/lowPoly:lowPoly", "filter/morphology:morphA",
            "filter/morphology:morphB", "filter/normalize:reduce",
            "filter/normalize:reduceMinmax", "filter/oilPaint:oilPost",
            "filter/patchwork:patchwork", "filter/photocopy:pcBlurH",
            "filter/photocopy:pcBlurV", "filter/pixelSort:findBrightest",
            "filter/plasticWrap:pwBlurH", "filter/plasticWrap:pwBlurV",
            "filter/relief:rlBlurH", "filter/relief:rlBlurV",
            "filter/reverb:reverb", "filter/scatter:scatterSmooth",
            "filter/stamp:stBlurH", "filter/stamp:stBlurV",
            "filter/strokes:stkPost", "filter/unsharpMask:usmBlurH",
            "filter/unsharpMask:usmBlurV", "filter/wormhole:blend",
            "mixer/cellSplit:cellSplit", "mixer/mashup:mashup",
            "mixer/shadow:shadow", "synth/cell:cell", "synth/gradient:gradient",
            "synth/mandala:mandala", "synth/subdivide:subdivide",
        }
        self.assertEqual(36, len(task15))
        task18 = {
            "filter/celShading:celShadingEdges",
            "filter/outline:outlineSobel",
        }
        task23 = {
            "filter/bloom:ntapGather",
            "filter/directionalBlur:directionalBlur",
            "filter/spinBlur:spinBlur",
            "filter/strokes:stkSmear",
            "filter/vaseline:upsample",
            "filter/wind:wind",
        }
        self.assertEqual(sorted([*existing, *task15, "filter/pixelSort:computeRank",
                                 "filter/sharpen:sharpen", "filter/sobel:sobel",
                                 *task18, "classicNoisedeck/refract:refract",
                                 "classicNoisedeck/lensDistortion:lensDistortion",
                                 "filter/prismaticAberration:prismaticAberration",
                                 "synth/sacredGeometry:sacredGeometry",
                                 "filter/crt:crt", "filter/degauss:degauss",
                                 *task23, "filter/pixelSort:gatherSorted",
                                 "filter/smooth:smoothEdge",
                                 "synth/perlin:perlin", "filter/rotate:rot",
                                 "mixer/focusBlur:focusBlur",
                                 "filter/extrude:extrude", "synth/curl:curl"]),
                         [entry["program_key"] for entry in slice_spec["programs"]])
        self.assertTrue(all(entry["defines"] == {} for entry in slice_spec["programs"]
                            if entry["program_key"] in task18))
        task15_defines = {entry["program_key"]: entry["defines"]
                          for entry in slice_spec["programs"]
                          if entry["program_key"] in task15}
        self.assertEqual({
            **{key: {} for key in task15},
            "filter/hatch:hatch": {"MODE": 0},
            "filter/lowPoly:lowPoly": {"LP_BORDER": 0, "LP_LIGHT": 0},
            "filter/morphology:morphA": {"SHAPE": 0},
            "filter/morphology:morphB": {"SHAPE": 0},
            "filter/oilPaint:oilPost": {"MODE": 1},
            "filter/relief:rlBlurH": {"MODE": 0},
            "filter/relief:rlBlurV": {"MODE": 0},
            "filter/scatter:scatterSmooth": {"MODE": 0},
            "filter/strokes:stkPost": {"MODE": 0},
        }, task15_defines)

        task12 = {
            "classicNoisedeck/coalesce:coalesce", "classicNoisedeck/composite:composite",
            "filter/hs:hs", "filter/repeat:repeat", "filter/scale:scale",
            "filter/scroll:scroll", "filter/translate:translate",
            "mixer/patternMix:patternMix", "mixer/shapeMask:shapeMask",
            "mixer/split:split", "mixer/uvRemap:uvRemap",
            "synth/modPattern:modPattern", "synth/pattern:pattern",
        }
        self.assertEqual(task12, {entry["program_key"] for entry in slice_spec["programs"]
                                  if entry["program_key"] in task12})
        self.assertTrue(all(entry["defines"] == {} for entry in slice_spec["programs"]
                            if entry["program_key"] in task12))

        task13 = {
            "filter/bloom:brightPass", "filter/bloom:composite",
            "filter/fibers:fibersBlend", "filter/normalize:apply",
            "filter/pixelSort:luminance", "filter/reindex:nmReindexApply",
            "filter/scratches:scratchesBlend", "filter/strayHair:strayHairBlend",
        }
        self.assertEqual(task13, {entry["program_key"] for entry in slice_spec["programs"]
                                  if entry["program_key"] in task13})
        self.assertTrue(all(entry["defines"] == {} for entry in slice_spec["programs"]
                            if entry["program_key"] in task13))
        task14 = {
            "filter/pixelSort:finalize", "filter/pixelSort:prepare", "filter/skew:skew",
            "filter/tetraCosine:tetraCosine", "filter/tile:tile", "synth/osc2d:osc2d",
        }
        self.assertEqual(task14, {entry["program_key"] for entry in slice_spec["programs"]
                                  if entry["program_key"] in task14})
        self.assertTrue(all(entry["defines"] == {} for entry in slice_spec["programs"]
                            if entry["program_key"] in task14))
        corpus_manifest = json.loads((
            REPOSITORY / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/manifest.json"
        ).read_text())
        corpus_keys = {entry["program_key"] for entry in corpus_manifest["programs"]}
        public_keys = {entry["program_key"] for entry in slice_spec["programs"]} | {
            "filter/invert:inv", "synth/solid:solid",
        }
        self.assertEqual(79, len(corpus_keys - public_keys))

    def test_typed_generator_owns_exact_public_catalog_header(self) -> None:
        from tools.glslcpp import generate_typed_slice

        expected = generate_typed_slice.render_catalog_header(
            generate_typed_slice.load_slice(REPOSITORY))
        actual = (REPOSITORY / "include/noisemaker/generated/catalog.hpp").read_bytes()
        self.assertEqual(expected, actual)
        self.assertIn(b"bind_filter_sharpen_sharpen", expected)
        self.assertIn(b"bind_filter_sobel_sobel", expected)
        self.assertIn(b"bind_classicNoisedeck_refract_refract", expected)

    def test_task11_language_frontier_is_schema_locked_and_fail_closed(self) -> None:
        from tools.glslcpp import generate_typed_slice

        slice_spec = generate_typed_slice.load_slice(REPOSITORY)
        self.assertEqual((
            "bool", "float", "int", "uint", "vec2", "vec3", "vec4",
            "ivec2", "ivec3", "ivec4", "uvec2", "uvec3", "uvec4",
            "mat2", "sampler2D", "void",
        ), tuple(slice_spec["types"]))
        self.assertEqual((
            "!=", "%", "&&", "*", "+", "-", "/", "<", "<=", "==",
            ">", ">=", ">>", "^", "||",
        ), tuple(slice_spec["binary_operators"]))
        self.assertEqual(("*=", "+=", "-=", "/=", "=", "^="),
                         tuple(slice_spec["assignment_operators"]))

    def test_task11_language_vocabularies_reject_add_remove_and_reordering(self) -> None:
        from tools.glslcpp import generate_typed_slice

        original = json.loads((REPOSITORY / "tools/glslcpp/typed_slice.json").read_text())
        diagnostics = {"capabilities": "capability", "types": "type", "binary_operators": "binary operator",
                       "assignment_operators": "assignment operator"}
        for field in ("capabilities", "types", "binary_operators", "assignment_operators"):
            values = original[field]
            mutations = (values[:-1], [*values, "arbitrary"], [values[1], values[0], *values[2:]])
            for index, replacement in enumerate(mutations):
                with self.subTest(field=field, mutation=index), tempfile.TemporaryDirectory() as temporary:
                    root = pathlib.Path(temporary)
                    target = root / "tools/glslcpp/typed_slice.json"
                    target.parent.mkdir(parents=True)
                    mutated = dict(original); mutated[field] = replacement
                    target.write_text(json.dumps(mutated), encoding="utf-8")
                    with self.assertRaisesRegex(
                            generate_typed_slice.GeneratorError,
                            rf"typed slice {diagnostics[field]} vocabulary drift"):
                        generate_typed_slice.load_slice(root)

    def test_task11_uint_multideclaration_and_mat2_emit_from_typed_ir(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = """
        out vec4 fragColor;
        uvec3 pcg(uvec3 value) {
          value = value * 1664525u + 1013904223u;
          value ^= value >> 48u;
          value = value ^ uvec3(1u, 2u, 3u);
          return value;
        }
        uint remainder(uint value) { return value % 7u; }
        void main() {
          float a = 1.0, b = a + 2.0;
          uvec3 bits = pcg(uvec3(4294967295u, uint(b), remainder(10u)));
          vec2 point = mat2(1.0, 2.0, 3.0, 4.0) * vec2(bits.xy);
          fragColor = vec4(point, float(bits.z), 1.0);
        }
        """
        typed = analyze_program(parse_program(source, "task11-language"), "task11-language")
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES)
        emitted = render_typed_cpp(typed, "task11-language", "8" * 64)
        self.assertIn("glsl::UVec3 pcg", emitted)
        self.assertIn("glsl::shift_right(value, std::uint32_t(48))", emitted)
        self.assertIn("value = glsl::bitwise_xor(value,", emitted)
        self.assertGreaterEqual(emitted.count("glsl::bitwise_xor(value,"), 2)
        self.assertIn("std::uint32_t remainder", emitted)
        self.assertIn("glsl::integer_mod(value, std::uint32_t(7))", emitted)
        a_line = next(index for index, line in enumerate(emitted.splitlines())
                      if "double a =" in line)
        b_line = next(index for index, line in enumerate(emitted.splitlines())
                      if "double b =" in line)
        self.assertEqual(a_line + 1, b_line)
        self.assertIn("a", emitted.splitlines()[b_line])
        self.assertIn(
            "glsl::Mat2(glsl::Vec2(static_cast<float>(1.0), static_cast<float>(2.0)), "
            "glsl::Vec2(static_cast<float>(3.0), static_cast<float>(4.0)))",
            emitted)

        shadowed = analyze_program(parse_program(
            "out vec4 fragColor; void main(){ float value=2.0; { float value=value+1.0, next=value+1.0; fragColor=vec4(next); } }",
            "task11-shadow"), "task11-shadow")
        shadowed_cpp = render_typed_cpp(shadowed, "task11-shadow", "9" * 64)
        declarations = [line for line in shadowed_cpp.splitlines() if "double value" in line]
        self.assertEqual(2, len(declarations))
        self.assertRegex(declarations[1], r"double value_\d+ = .*\(value\).*")
        next_line = next(line for line in shadowed_cpp.splitlines() if "double next" in line)
        self.assertRegex(next_line, r"value_\d+")

    def test_task12_mod_builtin_is_exactly_vec2_or_scalar_and_emits_glsl_mod(self) -> None:
        import dataclasses

        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import SemanticError, analyze_program

        source = """
        uniform float inputValue;
        out vec4 fragColor;
        void main() {
          float scalarValue = mod(inputValue, 2.25);
          vec2 vectorScalar = mod(vec2(inputValue, -inputValue) + 1.0, 2.0);
          vec2 vectorVector = mod(vectorScalar + vec2(0.5), vec2(1.25, 0.75));
          fragColor = vec4(vectorVector, scalarValue, 1.0);
        }
        """
        typed = analyze_program(parse_program(source, "task12-mod"), "task12-mod")
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES)
        emitted = render_typed_cpp(typed, typed.key, "d" * 64)
        self.assertEqual(3, emitted.count("glsl::mod("))
        self.assertNotIn("std::fmod", emitted)
        self.assertNotIn(" % ", emitted)

        main = next(function for function in typed.functions if function.name == "main")
        declaration = main.body[0]
        initializer = declaration.expressions[0].children[0]
        malformed_call = dataclasses.replace(initializer, children=(initializer.children[0],))
        malformed_declaration = dataclasses.replace(
            declaration,
            expressions=(dataclasses.replace(
                declaration.expressions[0], children=(malformed_call,)),))
        malformed = dataclasses.replace(
            typed,
            functions=tuple(dataclasses.replace(function, body=(malformed_declaration, *function.body[1:]))
                            if function.name == "main" else function
                            for function in typed.functions))
        with self.assertRaisesRegex(TypedEmissionError,
                                    r"task12-mod:5:\d+: unsupported builtin mod overload"):
            render_typed_cpp(malformed, malformed.key, "e" * 64)
        with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                    r"task12-mod:5:\d+: unsupported builtin mod overload"):
            generate_typed_slice.validate_capabilities(
                malformed, generate_typed_slice.APPROVED_CAPABILITIES)

        semantic_near_misses = {
            "scalar-vector": "mod(1.0,vec2(2.0))",
            "wrong-widths": "mod(vec2(1.0),vec3(2.0))",
            "integer": "mod(3,2)",
            "arity-one": "mod(1.0)",
            "arity-three": "mod(1.0,2.0,3.0)",
        }
        for name, call in semantic_near_misses.items():
            near_source = f"out vec4 fragColor;void main(){{fragColor=vec4({call});}}"
            with self.subTest(name=name), self.assertRaisesRegex(
                    SemanticError, rf"task12-{re.escape(name)}:1:\d+: E_NO_OVERLOAD"):
                analyze_program(parse_program(near_source, f"task12-{name}"),
                                f"task12-{name}")

        for width in (3, 4):
            key = f"task12-vec{width}"
            output = "vec4(x,1.0)" if width == 3 else "x"
            near_source = (f"out vec4 fragColor;void main(){{vec{width} x="
                           f"mod(vec{width}(1.0),vec{width}(2.0));fragColor={output};}}")
            candidate = analyze_program(parse_program(near_source, key), key)
            with self.subTest(width=width), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    rf"{key}:1:\d+: unsupported builtin mod overload"):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES)
            with self.subTest(width=width), self.assertRaisesRegex(
                    TypedEmissionError,
                    rf"{key}:1:\d+: unsupported builtin mod overload"):
                render_typed_cpp(candidate, key, "f" * 64)

    def test_task12_mod_capability_does_not_admit_adjacent_builtins(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        cases = {
            "ceil": "fragColor=vec4(ceil(1.25));",
            "reflect": "fragColor=vec4(reflect(vec2(1.0),vec2(0.0,1.0)),0.0,1.0);",
            "any": "fragColor=any(bvec2(true,false))?vec4(1.0):vec4(0.0);",
            "floatBitsToUint": "fragColor=vec4(float(floatBitsToUint(1.0)));",
            "derivative": "fragColor=vec4(dFdx(1.0));",
        }
        for name, body in cases.items():
            sampler = ""
            key = f"task12-excluded-{name}"
            source = f"{sampler}out vec4 fragColor;void main(){{{body}}}"
            typed = analyze_program(parse_program(source, key), key)
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    rf"{key}:1:\d+: unsupported"):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES)

    def test_task13_texel_fetch_is_exactly_sampler2d_ivec2_literal_zero(self) -> None:
        import dataclasses

        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import SemanticError, analyze_program

        source = """
        uniform sampler2D inputTex;
        out vec4 fragColor;
        void main() {
          ivec2 coord = ivec2(gl_FragCoord.xy);
          fragColor = texelFetch(inputTex, coord, 0);
        }
        """
        typed = analyze_program(parse_program(source, "task13-texel-fetch"),
                                "task13-texel-fetch")
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES)
        emitted = render_typed_cpp(typed, typed.key, "1" * 64)
        self.assertIn("glsl::Vec4 fetch_texel", emitted)
        self.assertIn("texel_fetch_bottom_left(surface, coord[0], coord[1])", emitted)
        self.assertIn("fetch_texel(*state.inputTex, coord)", emitted)

        mip_near_misses = {
            "nonzero": "1",
            "negative": "-1",
            "hex-zero": "0x0",
            "arithmetic": "1 - 1",
            "variable": "level",
            "uniform": "level",
        }
        for name, mip in mip_near_misses.items():
            global_declaration = "uniform int level;" if name == "uniform" else ""
            declaration = "int level = 0;" if name == "variable" else ""
            key = f"task13-mip-{name}"
            candidate_source = (f"uniform sampler2D inputTex;{global_declaration}"
                                "out vec4 fragColor;void main(){"
                                f"{declaration}ivec2 coord=ivec2(0);"
                                f"fragColor=texelFetch(inputTex,coord,{mip});}}")
            candidate = analyze_program(parse_program(candidate_source, key), key)
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    rf"{re.escape(key)}:1:\d+: unsupported builtin texelFetch overload"):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES)

            with self.subTest(name=name), self.assertRaisesRegex(
                    TypedEmissionError,
                    rf"{re.escape(key)}:1:\d+: unsupported builtin texelFetch overload"):
                render_typed_cpp(candidate, key, "2" * 64)

        main = next(function for function in typed.functions if function.name == "main")
        assignment = main.body[1].expressions[0]
        fetch = assignment.children[1]
        malformed_fetch = dataclasses.replace(fetch, children=fetch.children[:2])
        malformed_assignment = dataclasses.replace(
            assignment, children=(assignment.children[0], malformed_fetch))
        malformed_statement = dataclasses.replace(main.body[1], expressions=(malformed_assignment,))
        malformed = dataclasses.replace(
            typed,
            functions=tuple(dataclasses.replace(function, body=(function.body[0], malformed_statement))
                            if function.name == "main" else function
                            for function in typed.functions))
        with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                    r"task13-texel-fetch:6:\d+: unsupported builtin texelFetch overload"):
            generate_typed_slice.validate_capabilities(
                malformed, generate_typed_slice.APPROVED_CAPABILITIES)
        with self.assertRaisesRegex(TypedEmissionError,
                                    r"task13-texel-fetch:6:\d+: unsupported builtin texelFetch overload"):
            render_typed_cpp(malformed, malformed.key, "3" * 64)

        semantic_near_misses = {
            "arity-two": "texelFetch(inputTex,ivec2(0))",
            "arity-four": "texelFetch(inputTex,ivec2(0),0,0)",
            "float-coordinate": "texelFetch(inputTex,vec2(0.0),0)",
            "scalar-coordinate": "texelFetch(inputTex,0,0)",
            "float-mip": "texelFetch(inputTex,ivec2(0),0.0)",
        }
        for name, call in semantic_near_misses.items():
            key = f"task13-{name}"
            candidate_source = ("uniform sampler2D inputTex;out vec4 fragColor;"
                                f"void main(){{fragColor={call};}}")
            with self.subTest(name=name), self.assertRaisesRegex(
                    SemanticError, rf"{re.escape(key)}:1:\d+: E_NO_OVERLOAD"):
                analyze_program(parse_program(candidate_source, key), key)

        with self.assertRaisesRegex(SemanticError,
                                    r"task13-other-sampler:1:\d+: E_UNKNOWN_TYPE"):
            analyze_program(parse_program(
                "uniform samplerCube inputTex;out vec4 fragColor;"
                "void main(){fragColor=texelFetch(inputTex,ivec2(0),0);}",
                "task13-other-sampler"), "task13-other-sampler")

        capability_near_misses = {
            "texture-lod": ("uniform sampler2D inputTex;out vec4 fragColor;void main(){"
                            "fragColor=textureLod(inputTex,vec2(0.0),0.0);}"),
            "loop": ("uniform sampler2D inputTex;out vec4 fragColor;void main(){"
                     "for(int i=0;i<1;i=i+1)fragColor=texelFetch(inputTex,ivec2(0),0);}"),
            "index": ("uniform sampler2D inputTex;out vec4 fragColor;void main(){"
                      "ivec2 p=ivec2(0);fragColor=texelFetch(inputTex,ivec2(p[0],p[1]),0);}"),
        }
        for name, candidate_source in capability_near_misses.items():
            key = f"task13-{name}"
            candidate = analyze_program(parse_program(candidate_source, key), key)
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError, rf"{re.escape(key)}:1:\d+: unsupported"):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES)

    def test_task14_admits_only_initialized_const_float_source_globals(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.semantic import analyze_program

        accepted = ("const float PI = 3.141592653589793; out vec4 fragColor; "
                    "float helper(float x){return x+PI;} "
                    "void main(){fragColor=vec4(helper(PI));}")
        typed = analyze_program(parse_program(accepted, "task14-admitted"),
                                "task14-admitted")
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES)

        rejected = {
            "mutable": "float G=1.0;",
            "uninitialized": "const float G;",
            "bool": "const bool G=true;",
            "int": "const int G=1;",
            "uint": "const uint G=1u;",
            "vector": "const vec2 G=vec2(1.0);",
            "matrix": "const mat2 G=mat2(1.0,0.0,0.0,1.0);",
            "array": "float G[1];",
            "sampler": "sampler2D G;",
        }
        for name, declaration in rejected.items():
            source = f"{declaration} out vec4 fragColor; void main(){{fragColor=vec4(0.0);}}"
            candidate = analyze_program(parse_program(source, f"task14-global-{name}"),
                                        f"task14-global-{name}")
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    rf"task14-global-{name}:1:\d+: unsupported global"):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES)

        struct_source = ("struct Holder { float value; }; "
                         "const Holder G=Holder(1.0); out vec4 fragColor; "
                         "void main(){fragColor=vec4(0.0);}")
        struct_program = analyze_program(parse_program(struct_source, "task14-global-struct"),
                                         "task14-global-struct")
        with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                    r"task14-global-struct:1:\d+: unsupported global"):
            generate_typed_slice.validate_capabilities(
                struct_program, generate_typed_slice.APPROVED_CAPABILITIES)

        invalid_initializers = {
            "call": "sin(1.0)",
            "conditional": "true ? 1.0 : 2.0",
            "index": "vec2(1.0)[0]",
            "member": "vec2(1.0).x",
            "cast": "float(1)",
        }
        for name, initializer in invalid_initializers.items():
            source = (f"const float G={initializer}; out vec4 fragColor; "
                      "void main(){fragColor=vec4(G);}")
            key = f"task14-initializer-{name}"
            if name == "call":
                with self.subTest(name=name), self.assertRaisesRegex(
                        SemanticError, rf"{key}:1:\d+: E_CONST_INITIALIZER"):
                    analyze_program(parse_program(source, key), key)
                continue
            candidate = analyze_program(parse_program(source, key), key)
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    rf"{key}:1:\d+: unsupported global initializer"):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES)

    def test_task14_const_globals_are_localized_per_function_with_dependency_closure(self) -> None:
        import dataclasses

        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = ("const float PI=3.141592653589793; const float TAU=PI*2.0; "
                  "out vec4 fragColor; "
                  "float helper(float x){return x+TAU;} "
                  "float unused(float x){return x;} "
                  "void main(){fragColor=vec4(PI);}")
        typed = analyze_program(parse_program(source, "task14-localize"),
                                "task14-localize")
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES)
        emitted = render_typed_cpp(typed, typed.key, "4" * 64)
        helper_start = emitted.index("double helper(", emitted.index("double helper(") + 1)
        unused_start = emitted.index("double unused(", emitted.index("double unused(") + 1)
        helper = emitted[helper_start:unused_start]
        unused = emitted[unused_start:emitted.index("void pixel(")]
        pixel = emitted[emitted.index("void pixel("):]
        self.assertLess(helper.index("const double PI ="), helper.index("const double TAU ="))
        self.assertEqual(1, helper.count("const double PI ="))
        self.assertEqual(1, helper.count("const double TAU ="))
        self.assertNotIn("const double PI =", unused)
        self.assertNotIn("const double TAU =", unused)
        self.assertEqual(1, pixel.count("const double PI ="))
        self.assertNotIn("const double TAU =", pixel)
        self.assertFalse(any(line.startswith("const ") or line.startswith("static ")
                             for line in emitted.splitlines()))

        tau = next(item for item in typed.declarations if item.symbol.name == "TAU")
        malformed_initializer = dataclasses.replace(tau.initializer, children=())
        malformed = dataclasses.replace(
            typed,
            declarations=tuple(dataclasses.replace(item, initializer=malformed_initializer)
                               if item.symbol.id == tau.symbol.id else item
                               for item in typed.declarations))
        with self.assertRaisesRegex(
                TypedEmissionError,
                r"task14-localize:1:\d+: malformed source const global initializer"):
            render_typed_cpp(malformed, malformed.key, "5" * 64)

    def test_task14_malformed_typed_globals_fail_both_validator_and_emitter_audits(self) -> None:
        import dataclasses

        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.semantic_types import FLOAT, INT
        from tools.glslcpp.frontend.typed_ir import TypedExpression

        source = ("const float PI=3.141592653589793; const float TAU=PI*2.0; "
                  "out vec4 fragColor; void main(){fragColor=vec4(0.0);}")
        typed = analyze_program(parse_program(source, "task14-malformed"),
                                "task14-malformed")
        pi = next(item for item in typed.declarations if item.symbol.name == "PI")
        tau = next(item for item in typed.declarations if item.symbol.name == "TAU")
        pi_reference = tau.initializer.children[0]
        tau_reference = dataclasses.replace(
            pi_reference, symbol=tau.symbol, symbol_id=tau.symbol.id)

        forward = dataclasses.replace(
            typed,
            declarations=tuple(
                dataclasses.replace(item, initializer=tau_reference)
                if item.symbol.id == pi.symbol.id else
                dataclasses.replace(item, initializer=pi.initializer)
                if item.symbol.id == tau.symbol.id else item
                for item in typed.declarations))
        cycle = dataclasses.replace(
            typed,
            declarations=tuple(dataclasses.replace(item, initializer=tau_reference)
                               if item.symbol.id == pi.symbol.id else item
                               for item in typed.declarations))
        for name, candidate in {"forward": forward, "cycle": cycle}.items():
            with self.subTest(name=name, layer="validator"), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    r"global initializer dependency must name an earlier admitted const float"):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES)
            with self.subTest(name=name, layer="emitter"), self.assertRaisesRegex(
                    TypedEmissionError,
                    r"source const global dependency must name an earlier admitted declaration"):
                render_typed_cpp(candidate, candidate.key, "6" * 64)

        main = next(item for item in typed.functions if item.name == "main")
        statement = main.body[0]
        assignment = statement.expressions[0]
        literal = pi.initializer
        index = TypedExpression("literal", INT, pi.span, "rvalue",
                                literal="0", literal_value=0)
        targets = {
            "direct": pi_reference,
            "compound": pi_reference,
            "swizzle": TypedExpression("swizzle", FLOAT, pi.span, "lvalue",
                                        children=(pi_reference,), member="x"),
            "index": TypedExpression("index", FLOAT, pi.span, "lvalue",
                                      children=(pi_reference, index)),
            "member": TypedExpression("member", FLOAT, pi.span, "lvalue",
                                       children=(pi_reference,), member="value"),
        }
        expressions = {
            name: dataclasses.replace(assignment, type=FLOAT, children=(target, literal),
                                      operator="+=" if name == "compound" else "=")
            for name, target in targets.items()
        }
        expressions.update({
            "prefix-increment": TypedExpression("unary", FLOAT, pi.span, "rvalue",
                                                children=(pi_reference,), operator="++"),
            "prefix-decrement": TypedExpression("unary", FLOAT, pi.span, "rvalue",
                                                children=(pi_reference,), operator="--"),
            "postfix-increment": TypedExpression("post", FLOAT, pi.span, "rvalue",
                                                 children=(pi_reference,), operator="++"),
            "postfix-decrement": TypedExpression("post", FLOAT, pi.span, "rvalue",
                                                 children=(pi_reference,), operator="--"),
        })
        for name, expression in expressions.items():
            malformed_statement = dataclasses.replace(statement, expressions=(expression,))
            candidate = dataclasses.replace(
                typed,
                functions=tuple(dataclasses.replace(function, body=(malformed_statement,))
                                if function.name == "main" else function
                                for function in typed.functions))
            with self.subTest(name=name, layer="validator"), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError, r"write to source const global"):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES)
            with self.subTest(name=name, layer="emitter"), self.assertRaisesRegex(
                    TypedEmissionError, r"write to source const global"):
                render_typed_cpp(candidate, candidate.key, "7" * 64)

    def test_task11_rejects_adjacent_bitwise_matrix_and_modulo_forms(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        cases = {
            "bitwise-or": "out vec4 fragColor; void main(){ uint x=1u|2u; fragColor=vec4(float(x)); }",
            "bitwise-and": "out vec4 fragColor; void main(){ uint x=1u&2u; fragColor=vec4(float(x)); }",
            "left-shift": "out vec4 fragColor; void main(){ uvec2 x=uvec2(1u)<<2u; fragColor=vec4(vec2(x),0.0,1.0); }",
            "scalar-shift": "out vec4 fragColor; void main(){ uint x=1u>>2u; fragColor=vec4(float(x)); }",
            "signed-shift": "out vec4 fragColor; void main(){ ivec2 x=ivec2(1)>>2; fragColor=vec4(vec2(x),0.0,1.0); }",
            "or-assign": "out vec4 fragColor; void main(){ uvec2 x=uvec2(1u); x|=uvec2(2u); fragColor=vec4(vec2(x),0.0,1.0); }",
            "float-modulo": "out vec4 fragColor; void main(){ float x=5.0%2.0; fragColor=vec4(x); }",
            "mat3": "out vec4 fragColor; void main(){ vec3 x=mat3(1.0)*vec3(1.0); fragColor=vec4(x,1.0); }",
            "matrix-uniform": "uniform mat2 m; out vec4 fragColor; void main(){ fragColor=vec4(m*vec2(1.0),0.0,1.0); }",
            "matrix-parameter": "out vec4 fragColor; vec2 f(mat2 m){return m*vec2(1.0);} void main(){fragColor=vec4(f(mat2(1.0)),0.0,1.0);}",
            "matrix-vector-ctor": "out vec4 fragColor; void main(){ vec2 x=mat2(vec2(1.0),vec2(2.0))*vec2(1.0); fragColor=vec4(x,0.0,1.0); }",
            "matrix-diagonal-ctor": "out vec4 fragColor; void main(){ vec2 x=mat2(1.0)*vec2(1.0); fragColor=vec4(x,0.0,1.0); }",
            "vector-matrix": "out vec4 fragColor; void main(){ vec2 x=vec2(1.0)*mat2(1.0); fragColor=vec4(x,0.0,1.0); }",
            "matrix-matrix": "out vec4 fragColor; void main(){ mat2 x=mat2(1.0)*mat2(1.0); fragColor=vec4(0.0); }",
        }
        for name, source in cases.items():
            if name == "float-modulo":
                with self.subTest(name=name), self.assertRaises(Exception):
                    analyze_program(parse_program(source, f"task11-{name}"), f"task11-{name}")
                continue
            typed = analyze_program(parse_program(source, f"task11-{name}"), f"task11-{name}")
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    rf"task11-{re.escape(name)}:1:\d+: unsupported"):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES)

    def test_numeric_literal_contract_rejects_extra_keys_and_unknown_modes(self) -> None:
        from tools.glslcpp import generate_typed_slice

        original = json.loads((REPOSITORY / "tools/glslcpp/typed_slice.json").read_text())
        mutations = [
            {"filter/scatter:scatterJitter": "source-double", "filter/ridge:ridge": "source-double"},
            {"filter/scatter:scatterJitter": "unknown"},
        ]
        for contracts in mutations:
            with self.subTest(contracts=contracts), tempfile.TemporaryDirectory() as temporary:
                root = pathlib.Path(temporary)
                target = root / "tools/glslcpp/typed_slice.json"
                target.parent.mkdir(parents=True)
                mutated = dict(original)
                mutated["numeric_literal_contracts"] = contracts
                target.write_text(json.dumps(mutated), encoding="utf-8")
                with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                            "numeric literal contract drift"):
                    generate_typed_slice.load_slice(root)

    def test_compatibility_transform_contract_rejects_extra_keys_and_unknown_modes(self) -> None:
        from tools.glslcpp import generate_typed_slice

        original = json.loads((REPOSITORY / "tools/glslcpp/typed_slice.json").read_text())
        mutations = [
            {"classicNoisedeck/coalesce:coalesce": "coalesce-uv-alias-v1",
             "filter/corrupt:corrupt": "corrupt-sample-uv-alias-v1",
             "mixer/shapeMask:shapeMask": "shape-mask-sequential-lanes-v1",
             "synth/polygon:shape": "polygon-zero-smoothing-v1",
             "filter/ridge:ridge": "polygon-zero-smoothing-v1"},
            {"synth/polygon:shape": "unknown"},
        ]
        for transforms in mutations:
            with self.subTest(transforms=transforms), tempfile.TemporaryDirectory() as temporary:
                root = pathlib.Path(temporary)
                target = root / "tools/glslcpp/typed_slice.json"
                target.parent.mkdir(parents=True)
                mutated = dict(original)
                mutated["compatibility_transforms"] = transforms
                target.write_text(json.dumps(mutated), encoding="utf-8")
                with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                            "compatibility transform drift"):
                    generate_typed_slice.load_slice(root)

    def test_capability_vocabulary_and_typed_usage_are_fail_closed(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        self.assertEqual(generate_typed_slice.APPROVED_CAPABILITIES,
                         tuple(generate_typed_slice.load_slice(REPOSITORY)["capabilities"]))
        typed = analyze_program(parse_program(
            "uniform sampler2D inputTex; out vec4 fragColor; float f(vec4 c) { return dot(c.rgb, vec3(1.0)); } "
            "void main() { vec4 c = texture(inputTex, vec2(textureSize(inputTex, 0))); c.rgb = smoothstep(0.0, 1.0, c.rgb); fragColor = vec4(f(c)); }",
            "capability"), "capability")
        generate_typed_slice.validate_capabilities(typed, generate_typed_slice.APPROVED_CAPABILITIES)
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        emitted = render_typed_cpp(typed, "capability", "1" * 64)
        for form in ("double f([[maybe_unused]] const State& state, [[maybe_unused]] const glsl::PixelContext& context, [[maybe_unused]] glsl::Vec4 c)", "glsl::dot", "sample_texture", "texture_size",
                     "glsl::set_swizzle", "output ="):
            self.assertIn(form, emitted)
        with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                    "typed capability vocabulary mismatch"):
            generate_typed_slice.validate_capabilities(typed, tuple(item for item in generate_typed_slice.APPROVED_CAPABILITIES if item != "smoothstep"))
        with self.assertRaisesRegex(generate_typed_slice.GeneratorError, "unknown capability"):
            generate_typed_slice.validate_capabilities(typed, (*generate_typed_slice.APPROVED_CAPABILITIES, "arbitrary"))
        for direction in ("out", "inout"):
            source = (f"out vec4 fragColor; void mutate({direction} float x) {{ x = 1.0; }} "
                      "void main() { float x = 0.0; mutate(x); fragColor = vec4(x); }")
            directed = analyze_program(parse_program(source, f"parameter-{direction}"),
                                       f"parameter-{direction}")
            with self.subTest(direction=direction), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    rf"parameter-{direction}:1:\d+: unsupported parameter direction {direction}"):
                generate_typed_slice.validate_capabilities(
                    directed, generate_typed_slice.APPROVED_CAPABILITIES)

    def test_scoped_blocks_if_else_and_lazy_ternary_emit_from_typed_ir(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = """
        out vec4 fragColor;
        float arm(float value) { return value; }
        float choose(bool outer, bool inner, float inputValue) {
          float result = inputValue;
          {
            float result = 2.0;
            if (outer && inner) {
              float result = 3.0;
              return result;
            } else if (outer) result = 4.0;
          }
          if (inner) result = 5.0;
          result = outer ? arm(6.0) : arm(7.0);
          return result;
        }
        vec3 selectVec(bool condition, vec3 yes, vec3 no) {
          return condition ? yes : no;
        }
        vec2 rotateVec(vec2 point) {
          point = vec2(point.y, -point.x);
          return point;
        }
        void early(bool stop) {
          if (stop) return;
        }
        void main() {
          vec4 base = vec4(0.0);
          float scalar = choose(true, false, 1.0);
          vec3 color = selectVec(false, vec3(0.1), vec3(0.2));
          fragColor = vec4(color, scalar) + base;
        }
        """
        typed = analyze_program(parse_program(source, "control-flow"), "control-flow")
        generate_typed_slice.validate_capabilities(typed, generate_typed_slice.APPROVED_CAPABILITIES)
        emitted = render_typed_cpp(typed, "control-flow", "6" * 64)
        self.assertIn("if (outer && inner) {", emitted)
        self.assertNotIn("if ((", emitted)
        self.assertIn("} else {\n      if (outer) {", emitted)
        self.assertIn("if (inner) {\n    result =", emitted)
        self.assertIn("return result;", emitted)
        self.assertIn("if (stop) {\n    return;\n  }", emitted)
        self.assertIn("result = (outer ? arm(state, context,", emitted)
        self.assertIn(": arm(state, context,", emitted)
        self.assertIn("return (condition ? glsl::Vec3(yes) : glsl::Vec3(no));", emitted)
        self.assertIn("point = glsl::Vec2(glsl::FloatExpr<2>", emitted)
        self.assertGreaterEqual(emitted.count("double result ="), 3)
        self.assertIn("    [[maybe_unused]] double result =", emitted)
        self.assertIn("void pixel(const KernelState& kernel_base", emitted)
        self.assertIn("glsl::Vec4 base =", emitted)

    def test_polygon_zero_smoothing_transform_is_exact_and_rejects_near_misses(self) -> None:
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        corpus = check_corpus._corpus_root(REPOSITORY)
        polygon_source = (corpus / "sources/synth/polygon/shape.glsl").read_text()
        polygon = analyze_program(parse_program(polygon_source, "synth/polygon:shape"),
                                  "synth/polygon:shape")
        transformed = generate_typed_slice.apply_compatibility_transform(
            polygon, "polygon-zero-smoothing-v1")
        emitted = render_typed_cpp(transformed, "synth/polygon:shape", "7" * 64)
        mask_line = next(line for line in emitted.splitlines() if "double m =" in line)
        self.assertIn("state.smoothing ==", mask_line)
        self.assertIn("d <= state.radius", mask_line)
        self.assertIn("? static_cast<float>(1.0) : static_cast<float>(0.0)", mask_line)
        self.assertIn(": glsl::smoothstep(", mask_line)
        self.assertEqual(1, mask_line.count("glsl::smoothstep("))

        near_misses = {
            "wrong-key": ("not/polygon:shape", "smoothstep(radius, radius - smoothing, d)"),
            "reversed-edges": ("synth/polygon:shape", "smoothstep(radius - smoothing, radius, d)"),
            "different-distance": ("synth/polygon:shape", "smoothstep(radius, radius - smoothing, d + 0.0)"),
        }
        for name, (key, call) in near_misses.items():
            source = ("uniform float radius; uniform float smoothing; out vec4 fragColor; "
                      f"void main() {{ float d = 0.25; float m = {call}; fragColor = vec4(m); }}")
            typed = analyze_program(parse_program(source, key), key)
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    rf"{re.escape(key)}: polygon-zero-smoothing-v1 expected exactly one structural match"):
                generate_typed_slice.apply_compatibility_transform(
                    typed, "polygon-zero-smoothing-v1")

        shadowed = analyze_program(parse_program(
            "uniform float radius; uniform float smoothing; out vec4 fragColor; "
            "float helper(float radius, float smoothing, float d) { "
            "return smoothstep(radius, radius - smoothing, d); } "
            "void main() { fragColor = vec4(helper(0.4, 0.1, 0.2)); }",
            "synth/polygon:shape"), "synth/polygon:shape")
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                r"synth/polygon:shape: polygon-zero-smoothing-v1 expected exactly one structural match, got 0"):
            generate_typed_slice.apply_compatibility_transform(
                shadowed, "polygon-zero-smoothing-v1")

    def test_refract_truthy_vector_conditionals_transform_is_exact_and_source_locked(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        key = "classicNoisedeck/refract:refract"
        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == key)
        raw = (root / entry["source"]).read_text()
        typed = analyze_program(parse_program(raw, key, {}), key)
        self.assertEqual(
            "ccde114d367313d1feb218c7f956df4059534b5c139c757a30ae156292e9cc09",
            hashlib.sha256(repr(typed.functions).encode()).hexdigest())

        transformed = generate_typed_slice.apply_compatibility_transform(
            typed, "refract-truthy-vector-conditional-noop-v1")
        self.assertEqual(
            "4c9e125cd4dda55f2688c362a5ab7e81acf1b08c9e284bc5c25e04da39020188",
            hashlib.sha256(repr(transformed.functions).encode()).hexdigest())

        matches = []
        def expression(value):
            if (value.kind == "assign" and value.operator == "="
                    and len(value.children) == 2
                    and value.children[0].kind == "id"
                    and value.children[0].symbol is not None
                    and value.children[0].symbol.name == "middle"
                    and value.children[1].kind == "id"
                    and value.children[1].symbol_id == value.children[0].symbol_id):
                matches.append(value.span.start_line)
            for child in value.children:
                expression(child)
        def statement(value):
            for item in value.expressions:
                expression(item)
            for child in value.children:
                statement(child)
        for function in transformed.functions:
            for item in function.body:
                statement(item)
        self.assertEqual([120, 123, 135, 159], matches)

        for name, candidate in {
            "wrong-key": dataclasses.replace(typed, key="not/refract:refract"),
            "raw-source": dataclasses.replace(typed, raw_source=raw + "\n"),
            "normalized-source": dataclasses.replace(typed, source=typed.source + "\n"),
            "already-transformed": transformed,
        }.items():
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    "refract-truthy-vector-conditional-noop-v1"):
                generate_typed_slice.apply_compatibility_transform(
                    candidate, "refract-truthy-vector-conditional-noop-v1")

    def test_corrupt_alias_transform_is_symbol_exact_and_main_scoped(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        helper = ("vec3 bitCorrupt(vec3 color, vec2 uv, float row, float amount, float rt, float resX) "
                  "{ return color + vec3(uv, row + amount + rt + resX); }")
        overload = "vec3 bitCorrupt(vec3 color){return color;}"
        body = ("out vec4 fragColor; " + helper + overload +
                " void main(){ vec2 uv=vec2(0.25); vec2 sampleUv=uv; vec3 color=vec3(0.5); "
                "color=bitCorrupt(color,uv,1.0,2.0,3.0,4.0); fragColor=vec4(color,1.0); }")
        typed = analyze_program(parse_program(body, "filter/corrupt:corrupt"),
                                "filter/corrupt:corrupt")
        transformed = generate_typed_slice.apply_compatibility_transform(
            typed, "corrupt-sample-uv-alias-v1")
        emitted = render_typed_cpp(transformed, "filter/corrupt:corrupt", "a" * 64)
        call_line = next(line for line in emitted.splitlines() if "color = glsl::Vec3(bitCorrupt" in line)
        self.assertIn("color, sampleUv,", call_line)

        near_misses = {
            "wrong-key": ("not/corrupt:corrupt", body),
            "non-alias": ("filter/corrupt:corrupt", body.replace("vec2 sampleUv=uv;", "vec2 sampleUv=uv+vec2(0.0);")),
            "non-id-argument": ("filter/corrupt:corrupt", body.replace("bitCorrupt(color,uv,", "bitCorrupt(color,uv+vec2(0.0),")),
            "shadowed": ("filter/corrupt:corrupt", body.replace(
                "color=bitCorrupt", "{ vec2 sampleUv=uv; color=bitCorrupt").replace(
                "; fragColor", "; } fragColor")),
            "shadowed-uv": ("filter/corrupt:corrupt", body.replace(
                "color=bitCorrupt", "{ vec2 uv=vec2(0.75); color=bitCorrupt").replace(
                "; fragColor", "; } fragColor")),
            "same-name-wrong-signature": ("filter/corrupt:corrupt",
                "out vec4 fragColor; vec3 bitCorrupt(vec3 color){return color;} "
                "void main(){vec2 uv=vec2(0.25);vec2 sampleUv=uv;"
                "fragColor=vec4(bitCorrupt(vec3(0.5)),1.0);}"),
            "helper-scope": ("filter/corrupt:corrupt",
                "out vec4 fragColor; " + helper +
                " vec3 wrapper(){vec2 uv=vec2(0.25);vec2 sampleUv=uv;return bitCorrupt(vec3(0.5),uv,1.0,2.0,3.0,4.0);}"
                " void main(){fragColor=vec4(wrapper(),1.0);}"),
            "two-matches": ("filter/corrupt:corrupt", body.replace(
                "color=bitCorrupt(color,uv,1.0,2.0,3.0,4.0);",
                "color=bitCorrupt(color,uv,1.0,2.0,3.0,4.0);"
                "color=bitCorrupt(color,uv,1.0,2.0,3.0,4.0);")),
        }
        for name, (key, source) in near_misses.items():
            candidate = analyze_program(parse_program(source, key), key)
            expected_matches = 2 if name == "two-matches" else 0
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    rf"{re.escape(key)}: corrupt-sample-uv-alias-v1 expected exactly one structural match, got {expected_matches}"):
                generate_typed_slice.apply_compatibility_transform(
                    candidate, "corrupt-sample-uv-alias-v1")

    def test_coalesce_uv_alias_transform_is_symbol_exact_and_cloak_main_scoped(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        blend = ("vec3 blend(vec4 color1,vec4 color2,int mode,float factor){vec4 middle;"
                 "if(mode==2){middle=(color2==vec4(0.0))?color2:max(1.0-((1.0-color1)/color2),vec4(0.0));}"
                 "if(mode==3){middle=(color2==vec4(1.0))?color2:min(color1/(1.0-color2),vec4(1.0));}"
                 "if(mode==7){middle=(color2==vec4(1.0))?color2:min((color1*color1)/(1.0-color2),vec4(1.0));}"
                 "if(mode==15){middle=(color1==vec4(1.0))?color1:min((color2*color2)/(1.0-color1),vec4(1.0));}"
                 "return middle.rgb;}")
        body = ("out vec4 fragColor; " + blend +
                "vec4 cloak(vec2 st){vec2 leftUV=vec2(st);leftUV.x+=1.0;leftUV.y+=1.0;"
                "vec2 rightUV=vec2(st);return vec4(rightUV,0.0,1.0);} "
                "void main(){vec2 st=vec2(0.25);vec2 leftUV=vec2(st);leftUV.x+=2.0;leftUV.y+=2.0;"
                "vec2 rightUV=vec2(st);fragColor=cloak(rightUV);}")
        typed = analyze_program(parse_program(body, "classicNoisedeck/coalesce:coalesce"),
                                "classicNoisedeck/coalesce:coalesce")
        transformed = generate_typed_slice.apply_compatibility_transform(
            typed, "coalesce-uv-alias-v1")
        emitted = render_typed_cpp(transformed, "classicNoisedeck/coalesce:coalesce", "b" * 64)
        self.assertEqual(2, emitted.count("rightUV = glsl::Vec2(leftUV)"))
        self.assertNotIn("rightUV = glsl::Vec2(st)", emitted)
        self.assertEqual(4, emitted.count("middle = glsl::Vec4(middle)"))

        near_misses = {
            "wrong-key": ("not/coalesce:coalesce", body),
            "wrong-helper": ("classicNoisedeck/coalesce:coalesce",
                             body.replace("vec4 cloak", "vec4 helper").replace("cloak(rightUV)", "helper(rightUV)")),
            "non-alias": ("classicNoisedeck/coalesce:coalesce",
                          body.replace("vec2 rightUV=vec2(st);return", "vec2 rightUV=vec2(st+vec2(0.0));return")),
            "wrong-left-source": ("classicNoisedeck/coalesce:coalesce",
                                  body.replace("vec2 leftUV=vec2(st);leftUV.x", "vec2 leftUV=vec2(st+vec2(0.0));leftUV.x")),
            "missing-y-write": ("classicNoisedeck/coalesce:coalesce",
                                body.replace("leftUV.y+=1.0;", "leftUV.y-=1.0;")),
            "intervening-st-write": ("classicNoisedeck/coalesce:coalesce",
                                     body.replace("leftUV.x+=1.0;", "leftUV.x+=1.0;st.x+=0.0;")),
            "missing-main-site": ("classicNoisedeck/coalesce:coalesce",
                                  body.replace("vec2 rightUV=vec2(st);fragColor", "vec2 rightUV=vec2(st+vec2(0.0));fragColor")),
        }
        for name, (key, source) in near_misses.items():
            candidate = analyze_program(parse_program(source, key), key)
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    rf"{re.escape(key)}: coalesce-uv-alias-v1 expected exactly two structural matches"):
                generate_typed_slice.apply_compatibility_transform(candidate, "coalesce-uv-alias-v1")

        conditional_near_misses = {
            "wrong-mode-arm": body.replace("if(mode==15)", "if(mode==14)"),
            "scalar-condition": body.replace("color2==vec4(0.0)", "color2.x==0.0"),
            "wrong-true-symbol": body.replace("?color2:max", "?color1:max", 1),
            "wrong-false-builtin": body.replace("?color2:max", "?color2:min", 1),
        }
        for name, source in conditional_near_misses.items():
            candidate = analyze_program(parse_program(source, "classicNoisedeck/coalesce:coalesce"),
                                        "classicNoisedeck/coalesce:coalesce")
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    r"coalesce-uv-alias-v1 expected exact vector-conditional modes"):
                generate_typed_slice.apply_compatibility_transform(candidate, "coalesce-uv-alias-v1")

        mode2_arm = ("if(mode==2){middle=(color2==vec4(0.0))?color2:"
                     "max(1.0-((1.0-color1)/color2),vec4(0.0));}")
        mode15_arm = ("if(mode==15){middle=(color1==vec4(1.0))?color1:"
                      "min((color2*color2)/(1.0-color1),vec4(1.0));}")
        mode_set_near_misses = {
            "duplicate-mode": body.replace(mode15_arm, mode2_arm),
            "missing-mode": body.replace(mode15_arm, ""),
            "wrong-mode": body.replace("if(mode==15)", "if(mode==14)"),
        }
        for name, source in mode_set_near_misses.items():
            candidate = analyze_program(parse_program(source, "classicNoisedeck/coalesce:coalesce"),
                                        "classicNoisedeck/coalesce:coalesce")
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    r"coalesce-uv-alias-v1 expected exact vector-conditional modes"):
                generate_typed_slice.apply_compatibility_transform(candidate, "coalesce-uv-alias-v1")

    def test_shape_mask_sequential_lane_transform_is_function_and_symbol_exact(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        body = ("out vec4 fragColor;"
                "float sdfTriangle(vec2 p,float r){float k=1.732050808;p.x=abs(p.x)-r;p.y=p.y+r/k;"
                "if(p.x+k*p.y>0.0)p=vec2(p.x-k*p.y,-k*p.x-p.y)/2.0;return p.x;}"
                "float sdfStar5(vec2 p,float r){vec2 k1=vec2(0.8,-0.6);vec2 k2=vec2(-k1.x,k1.y);"
                "p-=2.0*max(dot(k1,p),0.0)*k1;p-=2.0*max(dot(k2,p),0.0)*k2;return p.y+r;}"
                "void main(){fragColor=vec4(sdfTriangle(vec2(0.2),0.4)+sdfStar5(vec2(0.3),0.5));}")
        typed = analyze_program(parse_program(body, "mixer/shapeMask:shapeMask"),
                                "mixer/shapeMask:shapeMask")
        transformed = generate_typed_slice.apply_compatibility_transform(
            typed, "shape-mask-sequential-lanes-v1")
        emitted = render_typed_cpp(transformed, "mixer/shapeMask:shapeMask", "c" * 64)
        self.assertEqual(4, emitted.count("glsl::set_swizzle<0>(p,"))
        self.assertEqual(4, emitted.count("glsl::set_swizzle<1>(p,"))
        self.assertNotIn("p = glsl::Vec2", emitted)
        self.assertNotIn("} else {", emitted)

        near_misses = {
            "wrong-key": ("not/shapeMask:shapeMask", body),
            "wrong-triangle": ("mixer/shapeMask:shapeMask", body.replace("sdfTriangle", "triangle")),
            "wrong-divisor": ("mixer/shapeMask:shapeMask", body.replace("/2.0;return p.x", "/3.0;return p.x")),
            "wrong-star-op": ("mixer/shapeMask:shapeMask", body.replace("p-=2.0*max(dot(k1,p),0.0)*k1", "p+=2.0*max(dot(k1,p),0.0)*k1")),
            "wrong-dot-vector": ("mixer/shapeMask:shapeMask", body.replace("dot(k2,p)", "dot(k1,p)")),
        }
        for name, (key, source) in near_misses.items():
            candidate = analyze_program(parse_program(source, key), key)
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    rf"{re.escape(key)}: shape-mask-sequential-lanes-v1 expected"):
                generate_typed_slice.apply_compatibility_transform(
                    candidate, "shape-mask-sequential-lanes-v1")

    def test_capability_validation_rejects_every_remaining_frontier_family_with_spans(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        cases = {
            "array": "out vec4 fragColor; void main(){ float a[2]; fragColor=vec4(0.0); }",
            "global": "float g=1.0; out vec4 fragColor; void main(){ fragColor=vec4(g); }",
            "matrix": "out vec4 fragColor; void main(){ mat3 m=mat3(1.0); fragColor=vec4(0.0); }",
            "struct": "struct S { float x; }; out vec4 fragColor; void main(){ fragColor=vec4(0.0); }",
            "ubo": "uniform B { float x; } b; out vec4 fragColor; void main(){ fragColor=vec4(b.x); }",
            "varying": "in vec2 vUv; out vec4 fragColor; void main(){ fragColor=vec4(vUv,0.0,1.0); }",
            "for": "out vec4 fragColor; void main(){ for(int i=0;i<1;i=i+1) fragColor=vec4(0.0); }",
            "while": "out vec4 fragColor; void main(){ int i=0; while(i<1) i=i+1; fragColor=vec4(0.0); }",
            "dowhile": "out vec4 fragColor; void main(){ int i=0; do i=i+1; while(i<1); fragColor=vec4(0.0); }",
            "derivative": "out vec4 fragColor; void main(){ fragColor=vec4(dFdx(1.0)); }",
            "dynamic-index": "out vec4 fragColor; void main(){ vec2 v=vec2(1.0); int i=1; fragColor=vec4(v[i]); }",
            "prefix-increment": "out vec4 fragColor; void main(){ float x=0.0; float y=++x; fragColor=vec4(y); }",
            "bitwise-not": "out vec4 fragColor; void main(){ int x=1; int y=~x; fragColor=vec4(float(y)); }",
            "discard": "out vec4 fragColor; void main(){ if(true) discard; fragColor=vec4(0.0); }",
            "textureLod": "uniform sampler2D t; out vec4 fragColor; void main(){ fragColor=textureLod(t,vec2(0.0),0.0); }",
        }
        for name, source in cases.items():
            typed = analyze_program(parse_program(source, f"excluded-{name}"), f"excluded-{name}")
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError, rf"excluded-{re.escape(name)}:1:\d+: unsupported"):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES)

    def test_typed_generation_is_cwd_independent_and_matches_committed_slice(self) -> None:
        from tools.glslcpp import generate_typed_slice

        expected = generate_typed_slice.generate_outputs(REPOSITORY)
        self.assertEqual(expected["src/typed_generated/typed_slice.cpp"],
                         (REPOSITORY / "src/typed_generated/typed_slice.cpp").read_bytes())
        self.assertEqual(expected["src/typed_generated/typed_manifest.json"],
                         (REPOSITORY / "src/typed_generated/typed_manifest.json").read_bytes())
        output = subprocess.check_output(
            [sys.executable, str(REPOSITORY / "tools/glslcpp/generate_typed_slice.py"), "--check"],
            cwd="/tmp", text=True)
        self.assertIn("typed slice ok (137 programs)", output)

    def test_typed_emitter_refuses_raw_or_unsupported_nodes_with_program_span(self) -> None:
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        raw = parse_program("out vec4 fragColor; void main() { fragColor = vec4(0.0); }", "raw")
        with self.assertRaisesRegex(TypedEmissionError, r"raw:1:"):
            render_typed_cpp(raw, "raw", "0" * 64)
        typed = analyze_program(parse_program(
            "out vec4 fragColor; void main() { for (int i = 0; i < 1; i += 2) fragColor = vec4(0.0); }",
            "unsupported"), "unsupported")
        with self.assertRaisesRegex(TypedEmissionError, r"unsupported:1:"):
            render_typed_cpp(typed, "unsupported", "0" * 64)
        unary = analyze_program(parse_program(
            "out vec4 fragColor; void main() { float x = 0.0; fragColor = vec4(++x); }",
            "unsupported-unary"), "unsupported-unary")
        with self.assertRaisesRegex(TypedEmissionError, r"unsupported-unary:1:.*unsupported unary operator"):
            render_typed_cpp(unary, "unsupported-unary", "0" * 64)

    def test_counted_for_v1_accepts_only_exact_proved_headers_and_control(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        accepted = {
            "literal-post": ("out vec4 fragColor; void main(){ float x=0.0; "
                             "for(int i=0;i<4;i++){ if(i==2) continue; x+=1.0; } "
                             "fragColor=vec4(x); }"),
            "negative-prefix": ("out vec4 fragColor; void main(){ float x=0.0; "
                                 "for(int i=-2;i<=2;++i){ if(i==1) break; x+=1.0; } "
                                 "fragColor=vec4(x); }"),
            "local-const-literal": ("out vec4 fragColor; void main(){ const int N=2; "
                                    "float x=0.0; for(int i=0;i<N;i++){x+=1.0;} "
                                    "fragColor=vec4(x); }"),
            "reverb-clamp": ("uniform int iterations; out vec4 fragColor; void main(){ "
                             "int iters=clamp(iterations,1,8); float x=0.0; "
                             "for(int i=0;i<iters;i++){x+=1.0;} fragColor=vec4(x); }"),
        }
        for name, source in accepted.items():
            key = "filter/reverb:reverb" if name == "reverb-clamp" else f"loop-{name}"
            typed = analyze_program(parse_program(source, key), key)
            with self.subTest(accepted=name):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES)

    def test_counted_for_v1_rejects_effective_depth_product_charge_and_call_cycles(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        sequential = " ".join(
            f"for(int i{index}=0;i{index}<128;i{index}++){{x+=1.0;}}"
            for index in range(33))
        cases = {
            "effective-depth-four": (
                "void helper(){for(int a=0;a<2;a++){for(int b=0;b<2;b++){"
                "for(int c=0;c<2;c++){}}}} out vec4 fragColor; void main(){"
                "for(int d=0;d<2;d++){helper();} fragColor=vec4(0.0);}"),
            "zero-depth-hop-effective-four": (
                "void g(){for(int a=0;a<2;a++){for(int b=0;b<2;b++){"
                "for(int c=0;c<2;c++){}}}} void f(){for(int d=0;d<2;d++){g();}} "
                "out vec4 fragColor; void main(){f();fragColor=vec4(0.0);}"),
            "nested-product": (
                "out vec4 fragColor; void main(){for(int y=0;y<65;y++){"
                "for(int x=0;x<65;x++){}} fragColor=vec4(0.0);}"),
            "entry-charge": (
                f"out vec4 fragColor; void main(){{float x=0.0; {sequential} fragColor=vec4(x);}}"),
            "call-cycle": (
                "void f(); void g(); void f(){for(int i=0;i<2;i++){g();}} "
                "void g(){f();} out vec4 fragColor; void main(){f();fragColor=vec4(0.0);}"),
            "call-cycle-without-loop": (
                "float f(); float g(); float f(){return g();} float g(){return f();} "
                "out vec4 fragColor; void main(){fragColor=vec4(f());}"),
        }
        for name, source in cases.items():
            key = f"loop-whole-{name}"
            typed = analyze_program(parse_program(source, key), key)
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    r"unsupported counted-for (program proof|safety charge)"):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES)
            if name == "call-cycle-without-loop":
                with self.subTest(emitter=name), self.assertRaisesRegex(
                        TypedEmissionError, r"unsupported counted-for program proof"):
                    render_typed_cpp(typed, key, "7" * 64)

    def test_counted_for_v1_emits_native_for_break_and_continue_without_broad_increment(self) -> None:
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = ("out vec4 fragColor; void main(){ float x=0.0; "
                  "for(int y=-1;y<=1;y++){ for(int i=0;i<4;++i){ "
                  "if(i==1) continue; if(i==3) break; x+=1.0; } } "
                  "fragColor=vec4(x); }")
        emitted = render_typed_cpp(analyze_program(parse_program(source, "loop-emit"),
                                                   "loop-emit"),
                                   "loop-emit", "6" * 64)
        self.assertIn("for ([[maybe_unused]] std::int32_t y = (-std::int32_t(1)); "
                      "(y <= std::int32_t(1)); ++y) {", emitted)
        self.assertIn("for ([[maybe_unused]] std::int32_t i = std::int32_t(0); "
                      "(i < std::int32_t(4)); ++i) {", emitted)
        self.assertIn("continue;", emitted)
        self.assertIn("break;", emitted)
        self.assertNotIn("goto", emitted)

    def test_discarded_local_counter_v1_validates_and_emits_only_compute_rank_statement(self) -> None:
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "filter/pixelSort:computeRank")
        source = (root / entry["source"]).read_text()
        typed = analyze_program(parse_program(source, entry["program_key"]), entry["program_key"])
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=entry["raw_sha256"])
        emitted = render_typed_cpp(typed, entry["program_key"], entry["raw_sha256"])
        self.assertEqual(1, emitted.count("++brighterCount;"))
        self.assertNotIn("brighterCount++;", emitted)
        self.assertNotIn("std::function", emitted)
        self.assertNotIn("std::vector", emitted)

    def test_discarded_local_counter_v1_rejects_adjacent_body_mutations(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        bodies = {
            "prefix": "int brighterCount=0; ++brighterCount;",
            "decrement": "int brighterCount=0; brighterCount--;",
            "compound": "int brighterCount=0; brighterCount += 1;",
            "expression-valued": "int brighterCount=0; int y = brighterCount++;",
            "call-valued": "int brighterCount=0; float y = float(brighterCount++);",
            "float-target": "float brighterCount=0.0; brighterCount++;",
            "uint-target": "uint brighterCount=0u; brighterCount++;",
            "nonzero-init": "int brighterCount=1; brighterCount++;",
            "second-write": "int brighterCount=0; brighterCount=1; brighterCount++;",
            "wrong-target": "int brighterCount=0; int other=0; other++;",
        }
        for name, mutation in bodies.items():
            source = ("out vec4 fragColor; void main(){ " + mutation +
                      " fragColor=vec4(0.0); }")
            typed = analyze_program(parse_program(
                source, "filter/pixelSort:computeRank"), "filter/pixelSort:computeRank")
            with self.subTest(name=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError, "unsupported|source digest"):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash="6ce61bb5cb69bb22ac51f48603d5b40755b1e3f700acad1bc685a1e8a4dea6a4")

    def test_discarded_local_counter_v1_rejects_source_and_frozen_proof_tampering(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "filter/pixelSort:computeRank")
        typed = analyze_program(parse_program(
            (root / entry["source"]).read_text(), entry["program_key"]), entry["program_key"])

        with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                    "source digest"):
            generate_typed_slice.validate_capabilities(
                typed, generate_typed_slice.APPROVED_CAPABILITIES, source_hash="0" * 64)
        with self.assertRaisesRegex(TypedEmissionError, "source digest"):
            render_typed_cpp(typed, typed.key, "0" * 64)

        def tamper(statement):
            proof = statement.counter_proof
            if proof is not None:
                proof = dataclasses.replace(proof, upper_bound=33)
            return dataclasses.replace(
                statement, counter_proof=proof,
                children=tuple(tamper(child) for child in statement.children))
        malformed = dataclasses.replace(
            typed, functions=tuple(dataclasses.replace(
                function, body=tuple(tamper(statement) for statement in function.body))
                for function in typed.functions))
        with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                    "malformed discarded local-counter proof"):
            generate_typed_slice.validate_capabilities(
                malformed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=entry["raw_sha256"])
        with self.assertRaisesRegex(TypedEmissionError,
                                    "malformed discarded local-counter proof"):
            render_typed_cpp(malformed, malformed.key, entry["raw_sha256"])

        def strip_postfix_child(statement):
            expressions = statement.expressions
            if statement.counter_proof is not None:
                expressions = (dataclasses.replace(expressions[0], children=()),)
            return dataclasses.replace(
                statement, expressions=expressions,
                children=tuple(strip_postfix_child(child) for child in statement.children))
        malformed_child = dataclasses.replace(
            typed, functions=tuple(dataclasses.replace(
                function, body=tuple(strip_postfix_child(statement)
                                     for statement in function.body))
                for function in typed.functions))
        with self.assertRaisesRegex(TypedEmissionError,
                                    "malformed discarded local-counter proof"):
            render_typed_cpp(malformed_child, malformed_child.key,
                             entry["raw_sha256"])

    def test_discarded_local_counter_v1_rejects_forged_control_tree_at_both_boundaries(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "filter/pixelSort:computeRank")
        typed = analyze_program(parse_program(
            (root / entry["source"]).read_text(), entry["program_key"]), entry["program_key"])

        def contains_proof(statement):
            return (statement.counter_proof is not None
                    or any(contains_proof(child) for child in statement.children))

        def mutate_counter_predicate(statement, mutation):
            children = tuple(mutate_counter_predicate(child, mutation)
                             for child in statement.children)
            result = dataclasses.replace(statement, children=children)
            if (result.kind == "if" and len(result.expressions) == 1
                    and any(contains_proof(child) for child in result.children)):
                result = dataclasses.replace(
                    result, expressions=(mutation(result.expressions[0]),))
            return result

        def drop_tie(predicate):
            return predicate.children[0]

        def change_outer_operator(predicate):
            return dataclasses.replace(predicate, operator="&&")

        def make_tie_inclusive(predicate):
            tie = predicate.children[1]
            inclusive = dataclasses.replace(tie.children[1], operator="<=")
            return dataclasses.replace(
                predicate,
                children=(predicate.children[0],
                          dataclasses.replace(tie, children=(tie.children[0], inclusive))))

        def reorder_loop_body(statement):
            children = tuple(reorder_loop_body(child) for child in statement.children)
            result = dataclasses.replace(statement, children=children)
            if (result.kind == "for" and len(result.children) == 2
                    and contains_proof(result.children[1])):
                body = result.children[1]
                self.assertEqual(4, len(body.children))
                body = dataclasses.replace(
                    body, children=(body.children[0], body.children[2],
                                    body.children[3], body.children[1]))
                result = dataclasses.replace(result, children=(result.children[0], body))
            return result

        candidates = {
            "drop-tie": tuple(mutate_counter_predicate(statement, drop_tie)
                              for statement in next(function for function in typed.functions
                                                    if function.name == "main").body),
            "outer-and": tuple(mutate_counter_predicate(statement, change_outer_operator)
                               for statement in next(function for function in typed.functions
                                                     if function.name == "main").body),
            "inclusive-tie": tuple(mutate_counter_predicate(statement, make_tie_inclusive)
                                  for statement in next(function for function in typed.functions
                                                        if function.name == "main").body),
            "reordered-loop-body": tuple(reorder_loop_body(statement)
                                         for statement in next(function for function in typed.functions
                                                               if function.name == "main").body),
        }
        main_id = next(function.signature.id for function in typed.functions
                       if function.name == "main")
        for name, body in candidates.items():
            forged = dataclasses.replace(
                typed, functions=tuple(
                    dataclasses.replace(function, body=body)
                    if function.signature.id == main_id else function
                    for function in typed.functions))
            with self.subTest(name=name, boundary="validator"), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    "malformed discarded local-counter proof"):
                generate_typed_slice.validate_capabilities(
                    forged, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=entry["raw_sha256"])
            with self.subTest(name=name, boundary="emitter"), self.assertRaisesRegex(
                    TypedEmissionError, "malformed discarded local-counter proof"):
                render_typed_cpp(forged, forged.key, entry["raw_sha256"])

    def test_counted_for_v1_preserves_plain_array_scalar_map_precision(self) -> None:
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = ("uniform sampler2D inputTex; out vec4 fragColor; void main(){"
                  "vec4 sum=texture(inputTex,vec2(0.5)); float w=0.25;"
                  "for(int i=0;i<2;i++){sum+=(texture(inputTex,vec2(0.25))+"
                  "texture(inputTex,vec2(0.75)))*w;} fragColor=sum;}")
        emitted = render_typed_cpp(analyze_program(parse_program(source, "loop-vector-map"),
                                                   "loop-vector-map"),
                                   "loop-vector-map", "a" * 64)
        update = next(line.strip() for line in emitted.splitlines()
                      if line.strip().startswith("sum ="))
        self.assertIn("glsl::Vec4((sample_texture", update)
        self.assertIn(" * w)", update)
        self.assertEqual(2, update.count("glsl::Vec4("))

    def test_integral_vector_conversion_defers_float_rounding_until_expression_storage(self) -> None:
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = ("out vec4 fragColor; void main(){uvec3 u=uvec3(4000000001u,3000000001u,1u);"
                  "vec2 v=vec2(u.xy)/float(0xffffffffu);fragColor=vec4(v,0.0,1.0);}")
        emitted = render_typed_cpp(analyze_program(parse_program(source, "uint-vector-convert"),
                                                   "uint-vector-convert"),
                                   "uint-vector-convert", "b" * 64)
        declaration = next(line.strip() for line in emitted.splitlines()
                           if "glsl::Vec2 v =" in line)
        self.assertIn("glsl::FloatExpr<2>(glsl::swizzle<0, 1>(u))", declaration)
        self.assertNotIn("glsl::Vec2(glsl::swizzle<0, 1>(u))", declaration)

    def test_integral_vector_call_conversion_materializes_before_arithmetic(self) -> None:
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = ("out vec4 fragColor; uvec3 values(){return uvec3(4000000001u,3000000001u,1u);}"
                  "void main(){vec3 v=vec3(values())/float(0xffffffffu);fragColor=vec4(v,1.0);}")
        emitted = render_typed_cpp(analyze_program(parse_program(source, "uint-call-convert"),
                                                   "uint-call-convert"),
                                   "uint-call-convert", "d" * 64)
        declaration = next(line.strip() for line in emitted.splitlines()
                           if "glsl::Vec3 v =" in line)
        self.assertIn("glsl::Vec3(values(state, context))", declaration)
        self.assertNotIn("glsl::FloatExpr<3>(values(state, context))", declaration)

    def test_integral_call_map_return_preserves_plain_array_scalar_chain(self) -> None:
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = ("out vec4 fragColor; uvec3 pcg(uvec3 v){return v;}"
                  "vec3 prng(){return vec3(pcg(uvec3(4000000001u,3000000001u,1u)))"
                  "/float(0xffffffffu);} void main(){vec3 r=prng()*0.5-0.25;"
                  "fragColor=vec4(r,1.0);}")
        emitted = render_typed_cpp(analyze_program(parse_program(source, "plain-call-map"),
                                                   "plain-call-map"),
                                   "plain-call-map", "e" * 64)
        self.assertIn("[[nodiscard]] glsl::FloatExpr<3> prng(", emitted)
        self.assertIn("return glsl::FloatExpr<3>(glsl::Vec3(", emitted)
        self.assertIn("[[maybe_unused]] glsl::FloatExpr<3> r =", emitted)

    def test_vector_vector_declaration_remains_concrete_storage(self) -> None:
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = ("out vec4 fragColor; void main(){vec2 a=vec2(0.25);vec2 b=vec2(0.5);"
                  "vec2 stored=a+b;fragColor=vec4(stored,0.0,1.0);}")
        emitted = render_typed_cpp(analyze_program(parse_program(source, "stored-vector-op"),
                                                   "stored-vector-op"),
                                   "stored-vector-op", "f" * 64)
        self.assertIn("[[maybe_unused]] glsl::Vec2 stored =", emitted)
        self.assertNotIn("[[maybe_unused]] glsl::FloatExpr<2> stored =", emitted)

    def test_scalar_uniforms_preserve_renderer_number_precision_in_generated_state(self) -> None:
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = "uniform float amount; out vec4 fragColor; void main(){fragColor=vec4(amount); }"
        emitted = render_typed_cpp(analyze_program(parse_program(source, "number-uniform"),
                                                   "number-uniform"),
                                   "number-uniform", "c" * 64)
        self.assertIn("State(double amount_value)", emitted)
        self.assertIn("double amount;", emitted)
        self.assertIn('bindings.get_number("amount")', emitted)
        self.assertNotIn('bindings.get<float>("amount")', emitted)

    def test_counted_for_v1_rejects_header_and_control_near_misses(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        rejected = {
            "while": "int i=0; while(i<2){i=i+1;}",
            "do": "int i=0; do{i=i+1;}while(i<2);",
            "float-induction": "for(float i=0.0;i<2.0;i++){ }",
            "external-induction": "int i=0; for(i=0;i<2;i++){ }",
            "step-two": "for(int i=0;i<4;i+=2){ }",
            "decrement": "for(int i=2;i>=0;i--){ }",
            "swapped": "for(int i=0;4>i;i++){ }",
            "uniform-bound": "for(int i=0;i<n;i++){ }",
            "arithmetic-bound": "for(int i=0;i<2+2;i++){ }",
            "mutable-local-bound": "int N=2; for(int i=0;i<N;i++){ }",
            "local-const-arithmetic": "const int N=1+1; for(int i=0;i<N;i++){ }",
            "local-const-alias": "const int N=2; const int M=N; for(int i=0;i<M;i++){ }",
            "global-const-bound": "for(int i=0;i<N;i++){ }",
            "loop-return": "for(int i=0;i<2;i++){ return; }",
            "body-increment": "int x=0; for(int i=0;i<2;i++){ x++; }",
            "trip-129": "for(int i=0;i<129;i++){ }",
            "scan-512": "for(int y=0;y<512;y++){ for(int x=0;x<512;x++){ } }",
        }
        prefixes = {
            "uniform-bound": "uniform int n; ",
            "global-const-bound": "const int N=2; ",
        }
        for name, body in rejected.items():
            source = prefixes.get(name, "") + f"out vec4 fragColor; void main(){{ {body} fragColor=vec4(0.0); }}"
            typed = analyze_program(parse_program(source, f"loop-reject-{name}"),
                                    f"loop-reject-{name}")
            with self.subTest(rejected=name), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError, r"loop-reject-.*:.*unsupported"):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES)

    def test_counted_for_v1_rejects_forged_induction_symbol_in_validator_and_emitter(self) -> None:
        import dataclasses
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        typed = analyze_program(parse_program(
            "out vec4 fragColor; void main(){for(int i=0;i<2;i++){ } fragColor=vec4(0.0);}",
            "loop-forged-symbol"), "loop-forged-symbol")
        main = next(function for function in typed.functions if function.name == "main")
        loop = main.body[0]
        condition = loop.expressions[0]
        induction = condition.children[0]
        forged = dataclasses.replace(induction,
                                     symbol=dataclasses.replace(induction.symbol, name="forged"))
        malformed_loop = dataclasses.replace(
            loop, expressions=(dataclasses.replace(condition,
                                                    children=(forged, condition.children[1])),
                               loop.expressions[1]))
        malformed = dataclasses.replace(
            typed,
            functions=tuple(dataclasses.replace(function, body=(malformed_loop, *function.body[1:]))
                            if function.signature.id == main.signature.id else function
                            for function in typed.functions))
        with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                    "malformed counted-for proof"):
            generate_typed_slice.validate_capabilities(
                malformed, generate_typed_slice.APPROVED_CAPABILITIES)
        with self.assertRaisesRegex(TypedEmissionError, "malformed counted-for proof"):
            render_typed_cpp(malformed, malformed.key, "7" * 64)

    def test_counted_for_v1_rejects_malformed_control_depth_and_tampered_proofs(self) -> None:
        import dataclasses
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.typed_ir import TypedStatement

        typed = analyze_program(parse_program(
            "out vec4 fragColor; void main(){for(int i=0;i<2;i++){ } fragColor=vec4(0.0);}",
            "loop-malformed-control"), "loop-malformed-control")
        main = next(function for function in typed.functions if function.name == "main")
        loop = main.body[0]

        malformed_programs = []
        for kind in ("break", "continue"):
            control = TypedStatement(kind, loop.span)
            malformed_programs.append(dataclasses.replace(
                typed,
                functions=tuple(
                    dataclasses.replace(function, body=(control, *function.body))
                    if function.signature.id == main.signature.id else function
                    for function in typed.functions)))

        body = loop.children[1]
        return_statement = TypedStatement("return", body.span)
        malformed_loop = dataclasses.replace(
            loop,
            children=(loop.children[0], dataclasses.replace(
                body, children=(*body.children, return_statement))))
        malformed_programs.append(dataclasses.replace(
            typed,
            functions=tuple(
                dataclasses.replace(function, body=(malformed_loop, *function.body[1:]))
                if function.signature.id == main.signature.id else function
                for function in typed.functions)))

        for malformed in malformed_programs:
            with self.subTest(statement=malformed.functions[-1].body[0].kind):
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.validate_capabilities(
                        malformed, generate_typed_slice.APPROVED_CAPABILITIES)
                with self.assertRaises(TypedEmissionError):
                    render_typed_cpp(malformed, malformed.key, "8" * 64)

        tampered = dataclasses.replace(
            typed,
            counted_loop_proof=dataclasses.replace(
                typed.counted_loop_proof, entrypoint_charge=1 << 63))
        with self.assertRaisesRegex(generate_typed_slice.GeneratorError,
                                    "malformed counted-for program proof"):
            generate_typed_slice.validate_capabilities(
                tampered, generate_typed_slice.APPROVED_CAPABILITIES)
        with self.assertRaisesRegex(TypedEmissionError,
                                    "malformed counted-for program proof"):
            render_typed_cpp(tampered, tampered.key, "9" * 64)

    def test_committed_manifest_has_one_hundred_twenty_nine_typed_outputs_without_absolute_paths(self) -> None:
        manifest = json.loads((REPOSITORY / "src/typed_generated/typed_manifest.json").read_text())
        self.assertEqual(137, len(manifest["programs"]))
        self.assertEqual("typed-ir-v1", manifest["emitter"])
        for program in manifest["programs"]:
            self.assertEqual("typed_slice.cpp", program["output"])
            self.assertEqual(manifest["typed_slice_sha256"], program["output_sha256"])
        defined = {program["program_key"]: (program["define_contract"], program["defines"])
                   for program in manifest["programs"] if program["defines"]}
        smooth = next(program for program in manifest["programs"]
                      if program["program_key"] == "filter/smooth:smoothEdge")
        self.assertEqual("smooth-edge-luma-weights-v1",
                         smooth["smooth_edge_luma_weights_profile"])
        perlin = next(program for program in manifest["programs"]
                      if program["program_key"] == "synth/perlin:perlin")
        self.assertEqual("perlin-scalar-uint-xor-v1",
                         perlin["perlin_scalar_uint_xor_profile"])
        self.assertEqual({
            "filter/extrude:extrude": (
                "default-only", {"DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0}),
            "synth/curl:curl": (
                "default-only", {"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True}),
            "filter/lensFlare:lensFlare": ("default-only", {"LENS_TYPE": 0}),
            "filter/lowPoly:lowPoly": ("default-only", {"LP_BORDER": 0, "LP_LIGHT": 0}),
            "filter/morphology:morphA": ("default-only", {"SHAPE": 0}),
            "filter/morphology:morphB": ("default-only", {"SHAPE": 0}),
            "filter/mosaicTiles:mosaicTiles": ("default-only", {"MODE": 0}),
            "filter/oilPaint:oilPost": ("default-only", {"MODE": 1}),
            "filter/relief:rlBlurH": ("default-only", {"MODE": 0}),
            "filter/relief:rlBlurV": ("default-only", {"MODE": 0}),
            "filter/relief:rlShade": ("default-only", {"MODE": 0}),
            "filter/scatter:scatterJitter": ("default-only", {"MODE": 0}),
            "filter/scatter:scatterSmooth": ("default-only", {"MODE": 0}),
            "filter/strokes:stkPost": ("default-only", {"MODE": 0}),
            "filter/strokes:stkSmear": ("default-only", {"MODE": 0}),
            "filter/wind:wind": ("default-only", {"METHOD": 1}),
            "filter/hatch:hatch": ("default-only", {"MODE": 0}),
            "synth/perlin:perlin": ("default-only", {"DIMENSIONS": 2}),
        }, defined)
        transformed = {program["program_key"]: program["compatibility_transform"]
                       for program in manifest["programs"]
                       if program["compatibility_transform"] != "none"}
        self.assertEqual({"classicNoisedeck/coalesce:coalesce": "coalesce-uv-alias-v1",
                          "classicNoisedeck/refract:refract":
                              "refract-truthy-vector-conditional-noop-v1",
                          "filter/corrupt:corrupt": "corrupt-sample-uv-alias-v1",
                          "filter/crt:crt": "crt-metal-sine-v1",
                          "mixer/shapeMask:shapeMask": "shape-mask-sequential-lanes-v1",
                          "synth/polygon:shape": "polygon-zero-smoothing-v1",
                          "synth/sacredGeometry:sacredGeometry":
                              "sacred-star-number-division-v1"}, transformed)
        self.assertNotIn(str(REPOSITORY), json.dumps(manifest, sort_keys=True))

    def test_math_builtins_emit_only_from_typed_calls(self) -> None:
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = """
        out vec4 fragColor;
        void main() {
          vec2 v = vec2(-0.25, 1.5);
          vec2 w = abs(v) + cos(v) + floor(v) + fract(v + vec2(0.125)) + sign(v) + sin(v) + sqrt(abs(v));
          float a = fract((v.x + v.y) * v.x) + atan(v.y, v.x) + distance(v, w) + length(v) + pow(abs(v.x), 2.0) + radians(90.0);
          vec2 b = clamp(mix(min(v, w), max(v, w), 0.25), -1.0, 1.0);
          fragColor = vec4(normalize(b), step(0.0, a), smoothstep(0.0, 1.0, a));
        }
        """
        typed = analyze_program(parse_program(source, "math-forms"), "math-forms")
        emitted = render_typed_cpp(typed, "math-forms", "2" * 64)
        self.assertIn("[[maybe_unused]] double a =", emitted)
        self.assertNotIn("glsl::fract(static_cast<float>(", emitted)
        for builtin in ("abs", "atan", "clamp", "cos", "distance", "floor", "fract", "length",
                        "component_max", "component_min", "mix", "normalize", "pow", "radians",
                        "sign", "sin", "sqrt", "step", "smoothstep"):
            self.assertIn(f"glsl::{builtin}(", emitted)

    def test_hash_precision_fences_are_structural_and_scatter_is_excluded(self) -> None:
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = """
        out vec4 fragColor;
        float hash12(vec2 p) {
          vec3 p3 = fract(vec3(p.xyx) * 0.1031);
          p3 += dot(p3, p3.yzx + 33.33);
          return fract((p3.x + p3.y) * p3.z);
        }
        vec2 hash22(vec2 p) {
          vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
          p3 += dot(p3, p3.yzx + 33.33);
          return fract((p3.xx + p3.yz) * p3.zy);
        }
        void main() {
          float ordinary = fract((1.0 + 2.0) * 3.0);
          fragColor = vec4(hash12(vec2(ordinary)), hash22(vec2(ordinary)), 1.0);
        }
        """
        typed = analyze_program(parse_program(source, "hash-forms"), "hash-forms")
        emitted = render_typed_cpp(typed, "hash-forms", "3" * 64)
        self.assertIn("glsl::fract(static_cast<float>(static_cast<double>(static_cast<float>(", emitted)
        self.assertIn("glsl::fract(glsl::Vec2(static_cast<float>(", emitted)
        self.assertIn("hash12(state, context, glsl::FloatExpr<2>(ordinary))", emitted)
        ordinary_line = next(line for line in emitted.splitlines() if "double ordinary" in line)
        self.assertIn("glsl::fract(static_cast<float>(9.0))", ordinary_line)
        self.assertNotIn("static_cast<float>(static_cast<double>", ordinary_line)

        scatter = analyze_program(parse_program(source, "filter/scatter:scatterJitter"),
                                  "filter/scatter:scatterJitter")
        scatter_emitted = render_typed_cpp(scatter, "filter/scatter:scatterJitter", "4" * 64,
                                           numeric_literal_contract="source-double")
        self.assertNotIn("glsl::fract(static_cast<float>(", scatter_emitted)
        self.assertNotIn("glsl::fract(glsl::Vec2(static_cast<float>(", scatter_emitted)
        self.assertIn("static_cast<double>(0.1031)", scatter_emitted)
        self.assertIn("static_cast<double>(33.33)", scatter_emitted)
        self.assertIn("static_cast<float>(0.1031)", emitted)

    def test_vector_arithmetic_rooted_in_builtin_materializes_each_operation(self) -> None:
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = """
        out vec4 fragColor;
        void main() {
          vec4 value = vec4(0.1, 0.2, 0.3, 0.4);
          float denom = 0.58;
          vec4 result = vec4(1.0) - abs(value - vec4(0.42)) / denom;
          fragColor = result;
        }
        """
        typed = analyze_program(parse_program(source, "builtin-vector-boundary"),
                                "builtin-vector-boundary")
        emitted = render_typed_cpp(typed, "builtin-vector-boundary", "5" * 64)
        result_line = next(line for line in emitted.splitlines() if "Vec4 result" in line)
        self.assertGreaterEqual(result_line.count("glsl::Vec4("), 2)
        self.assertIn("glsl::abs(", result_line)

    def test_vector_builtin_boundary_materializes_plain_binary_operand(self) -> None:
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = """
        out vec4 fragColor;
        vec4 burn(vec4 color1, vec4 color2) {
          return vec4(1.0) - min((vec4(1.0) - color1) / max(color2, vec4(0.001)), vec4(1.0));
        }
        void main() { fragColor = burn(vec4(0.2), vec4(0.4)); }
        """
        typed = analyze_program(parse_program(source, "vector-builtin-operand-boundary"),
                                "vector-builtin-operand-boundary")
        emitted = render_typed_cpp(typed, "vector-builtin-operand-boundary", "8" * 64)
        burn_line = next(line for line in emitted.splitlines()
                         if line.strip().startswith("return glsl::Vec4")
                         and "component_min" in line)
        self.assertIn("/ glsl::component_max", burn_line)
        self.assertIn(
            "glsl::Vec4((glsl::FloatExpr<4>(static_cast<float>(1.0)) - color1)) / ",
            burn_line)

    def test_literal_only_float_arithmetic_folds_once_at_canonical_precision(self) -> None:
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = """
        uniform float inputValue;
        out vec4 fragColor;
        void main() {
          float quotient = 1.0 / 3.0;
          float nested = (0.1 + 0.2) * (7.0 - 2.0);
          float signedValue = -(1.0 / 8.0);
          float positiveInfinity = 1.0 / 0.0;
          float negativeInfinity = -1.0 / 0.0;
          float notANumber = 0.0 / 0.0;
          float dynamic = inputValue + (1.0 / 3.0);
          fragColor = vec4(quotient + nested + signedValue + dynamic
                           + positiveInfinity + negativeInfinity + notANumber);
        }
        """
        typed = analyze_program(parse_program(source, "literal-float-fold"),
                                "literal-float-fold")
        emitted = render_typed_cpp(typed, "literal-float-fold", "9" * 64)
        lines = {line.split("double ", 1)[1].split(" =", 1)[0]: line
                 for line in emitted.splitlines() if "[[maybe_unused]] double " in line}
        self.assertIn("static_cast<float>(0.3333333432674408)", lines["quotient"])
        self.assertIn("static_cast<float>(1.5)", lines["nested"])
        self.assertIn("static_cast<float>(-0.125)", lines["signedValue"])
        self.assertIn("std::numeric_limits<float>::infinity()", lines["positiveInfinity"])
        self.assertIn("-std::numeric_limits<float>::infinity()", lines["negativeInfinity"])
        self.assertIn("std::numeric_limits<float>::quiet_NaN()", lines["notANumber"])
        self.assertIn("state.inputValue", lines["dynamic"])
        self.assertIn("static_cast<float>(0.3333333432674408)", lines["dynamic"])
        self.assertIn("static_cast<double>(state.inputValue)", lines["dynamic"])

        source_double = render_typed_cpp(
            typed, "literal-float-fold", "a" * 64, numeric_literal_contract="source-double")
        quotient_line = next(line for line in source_double.splitlines() if "double quotient" in line)
        self.assertIn("static_cast<double>(0.3333333333333333)", quotient_line)

    def test_literal_float_folder_does_not_hide_malformed_or_unsupported_typed_ir(self) -> None:
        import dataclasses

        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        source = "out vec4 fragColor; void main(){float x=1.0+2.0;fragColor=vec4(x);}"
        typed = analyze_program(parse_program(source, "literal-fold-fail-closed"),
                                "literal-fold-fail-closed")
        main = next(function for function in typed.functions if function.name == "main")
        declaration = main.body[0]
        initializer = declaration.expressions[0].children[0]
        unsupported = dataclasses.replace(initializer, operator="**")
        unsupported_decl = dataclasses.replace(
            declaration,
            expressions=(dataclasses.replace(
                declaration.expressions[0], children=(unsupported,)),))
        unsupported_program = dataclasses.replace(
            typed,
            functions=tuple(dataclasses.replace(function, body=(unsupported_decl, *function.body[1:]))
                            if function.name == "main" else function
                            for function in typed.functions))
        with self.assertRaisesRegex(TypedEmissionError, "unsupported binary operator \\*\\*"):
            render_typed_cpp(unsupported_program, typed.key, "b" * 64)

        malformed = dataclasses.replace(initializer, children=(initializer.children[0],))
        malformed_decl = dataclasses.replace(
            declaration,
            expressions=(dataclasses.replace(
                declaration.expressions[0], children=(malformed,)),))
        malformed_program = dataclasses.replace(
            typed,
            functions=tuple(dataclasses.replace(function, body=(malformed_decl, *function.body[1:]))
                            if function.name == "main" else function
                            for function in typed.functions))
        with self.assertRaisesRegex(TypedEmissionError, "malformed typed binary expression"):
            render_typed_cpp(malformed_program, typed.key, "c" * 64)

    def test_typed_writer_rolls_back_every_swap_step_and_rejects_invalid_owned_targets(self) -> None:
        from tools.glslcpp import generate_typed_slice
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            target = root / "src" / "typed_generated"
            target.mkdir(parents=True)
            old = {"typed_manifest.json": b"old manifest", "typed_slice.cpp": b"old source"}
            for name, value in old.items(): (target / name).write_bytes(value)
            (root / "src" / "generated").mkdir()
            (root / "src" / "generated" / "unrelated.cpp").write_bytes(b"preserve")
            outputs = {"src/typed_generated/typed_manifest.json": b"new manifest",
                       "src/typed_generated/typed_slice.cpp": b"new source"}
            before = self.tree_bytes(root)
            real_replace = os.replace
            for failure_index in (1, 2):
                calls = 0
                def fail_step(source, destination):
                    nonlocal calls
                    calls += 1
                    if calls == failure_index: raise OSError(f"injected swap failure {failure_index}")
                    real_replace(source, destination)
                with mock.patch.object(generate_typed_slice, "generate_outputs", return_value=outputs), \
                     mock.patch.object(generate_typed_slice.os, "replace", side_effect=fail_step):
                    with self.assertRaisesRegex(OSError, "injected swap failure"):
                        generate_typed_slice.write_outputs(root)
                self.assertEqual(before, self.tree_bytes(root))
                self.assertFalse(list((root / "src").glob(".typed-glslcpp-*")))
            (target / "typed_slice.cpp").unlink()
            (target / "typed_slice.cpp").symlink_to(target / "typed_manifest.json")
            with mock.patch.object(generate_typed_slice, "generate_outputs", return_value=outputs):
                with self.assertRaisesRegex(generate_typed_slice.GeneratorError, "symlink"):
                    generate_typed_slice.write_outputs(root)

    def test_typed_owned_tree_rejects_path_attacks_devices_fifos_and_directories(self) -> None:
        from tools.glslcpp import generate_typed_slice
        for name in ("../escape.cpp", "subdir/file.cpp", "COM1.cpp", "NUL.cpp", "typed_manifest.json/extra"):
            with self.subTest(name=name):
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice._validate_typed_output_name(name)
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary); target = root / "src" / "typed_generated"; target.mkdir(parents=True)
            (target / "typed_manifest.json").write_bytes(b"manifest")
            (target / "typed_slice.cpp").mkdir()
            with self.assertRaisesRegex(generate_typed_slice.GeneratorError, "unexpected entry"):
                generate_typed_slice._validate_owned_tree(target, {"typed_manifest.json", "typed_slice.cpp"})
            shutil.rmtree(target / "typed_slice.cpp")
            try: os.mkfifo(target / "typed_slice.cpp")
            except (AttributeError, OSError): self.skipTest("FIFO creation unavailable")
            with self.assertRaisesRegex(generate_typed_slice.GeneratorError, "unexpected entry"):
                generate_typed_slice._validate_owned_tree(target, {"typed_manifest.json", "typed_slice.cpp"})

    def test_typed_check_rejects_committed_tamper_and_failed_restore_retains_backup(self) -> None:
        from tools.glslcpp import generate_typed_slice
        outputs = {"src/typed_generated/typed_manifest.json": b"new manifest",
                   "src/typed_generated/typed_slice.cpp": b"new source"}
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary); target = root / "src" / "typed_generated"; target.mkdir(parents=True)
            (target / "typed_manifest.json").write_bytes(b"old manifest"); (target / "typed_slice.cpp").write_bytes(b"old source")
            with mock.patch.object(generate_typed_slice, "generate_outputs", return_value=outputs):
                (target / "typed_slice.cpp").write_bytes(b"tampered")
                with self.assertRaisesRegex(generate_typed_slice.GeneratorError, "drift"):
                    generate_typed_slice.check_outputs(root)
                (target / "typed_slice.cpp").write_bytes(b"old source")
                real_replace = os.replace; calls = 0
                def fail_install_and_restore(source, destination):
                    nonlocal calls
                    calls += 1
                    if calls in {2, 3}: raise OSError("injected restore failure")
                    real_replace(source, destination)
                with mock.patch.object(generate_typed_slice.os, "replace", side_effect=fail_install_and_restore):
                    with self.assertRaisesRegex(generate_typed_slice.GeneratorError, "rollback could not restore"):
                        generate_typed_slice.write_outputs(root)
            backups = list((root / "src").glob(".typed-glslcpp-backup-*"))
            self.assertEqual(1, len(backups))
            self.assertEqual(b"old manifest", (backups[0] / "typed_manifest.json").read_bytes())
            self.assertEqual(b"old source", (backups[0] / "typed_slice.cpp").read_bytes())

    def test_sacred_star_number_division_transform_is_exact_and_source_locked(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.sacred_geometry_compatibility import (
            POST_FUNCTION_SHA256, POST_WHOLE_PROGRAM_SHA256,
            apply_sacred_star_number_division,
            authenticate_sacred_star_number_division,
            whole_program_fingerprint,
        )
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "synth/sacredGeometry:sacredGeometry")
        raw = (root / entry["source"]).read_text()
        analyzed = analyze_program(
            parse_program(raw, entry["program_key"], {}), entry["program_key"])
        transformed = apply_sacred_star_number_division(analyzed)
        authenticate_sacred_star_number_division(transformed, entry["raw_sha256"])

        before = next(function for function in analyzed.functions
                      if function.signature.id == 46 and function.body)
        after = next(function for function in transformed.functions
                     if function.signature.id == 46 and function.body)
        self.assertEqual(POST_FUNCTION_SHA256,
                         hashlib.sha256(repr(transformed.functions).encode()).hexdigest())
        self.assertEqual(POST_WHOLE_PROGRAM_SHA256,
                         whole_program_fingerprint(transformed))

        changed = []
        def compare(left, right, path=""):
            if type(left) is not type(right):
                changed.append((path, left, right)); return
            if dataclasses.is_dataclass(left):
                for field in dataclasses.fields(left):
                    compare(getattr(left, field.name), getattr(right, field.name),
                            f"{path}.{field.name}")
            elif isinstance(left, tuple):
                self.assertEqual(len(left), len(right))
                for index, (lvalue, rvalue) in enumerate(zip(left, right)):
                    compare(lvalue, rvalue, f"{path}[{index}]")
            elif left != right:
                changed.append((path, left, right))
        compare(before, after, "starPolygonMask")
        changed_types = [item for item in changed if item[0].endswith(".type.base")]
        self.assertEqual(7, len(changed_types))
        self.assertEqual({("int", "float")},
                         {(left, right) for _, left, right in changed_types})
        self.assertTrue(all(path.endswith(".type.base") for path, _, _ in changed))

    def test_sacred_star_number_division_transform_rejects_partial_duplicate_and_drift(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.sacred_geometry_compatibility import (
            apply_sacred_star_number_division,
            authenticate_sacred_star_number_division,
        )
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.semantic_types import FLOAT, INT, vector

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "synth/sacredGeometry:sacredGeometry")
        raw = (root / entry["source"]).read_text()
        analyzed = analyze_program(
            parse_program(raw, entry["program_key"], {}), entry["program_key"])
        transformed = apply_sacred_star_number_division(analyzed)
        pre_candidates = {
            "duplicate": transformed,
            "raw-source": dataclasses.replace(
                analyzed, raw_source=analyzed.raw_source + "\n"),
            "task17-proof": dataclasses.replace(
                analyzed, fixed_nine_table_proof=object()),
            "task18-proof": dataclasses.replace(
                analyzed, fixed_grid_counter_store_proof=object()),
            "task19-proof": dataclasses.replace(
                analyzed, fixed_array_in_parameter_proof=object()),
            "task20-proof": dataclasses.replace(
                analyzed, fixed_affine_centers13_proof=object()),
        }
        for name, candidate in pre_candidates.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                apply_sacred_star_number_division(candidate)

        def revert_division_expression(value):
            children = tuple(revert_division_expression(child) for child in value.children)
            value = dataclasses.replace(value, children=children)
            if (value.kind == "binary" and value.operator == "/"
                    and value.span.start_line == 260
                    and value.span.start_column == 29
                    and value.span.end_column == 39):
                value = dataclasses.replace(value, type=INT)
            return value

        def revert_division_statement(statement):
            return dataclasses.replace(
                statement,
                expressions=tuple(revert_division_expression(value)
                                  for value in statement.expressions),
                children=tuple(revert_division_statement(child)
                               for child in statement.children))

        partial = dataclasses.replace(
            transformed,
            functions=tuple(
                dataclasses.replace(
                    function,
                    body=tuple(revert_division_statement(statement)
                               for statement in function.body))
                if function.signature.id == 46 and function.body else function
                for function in transformed.functions))
        with self.assertRaises(ValueError):
            apply_sacred_star_number_division(partial)
        with self.assertRaises(ValueError):
            authenticate_sacred_star_number_division(partial, entry["raw_sha256"])
        star = next(function for function in transformed.functions
                    if function.signature.id == 46 and function.body)
        drifted = dataclasses.replace(
            transformed,
            functions=tuple(dataclasses.replace(function, span=function.span)
                            if function is not star else dataclasses.replace(
                                function, body=function.body[:-1])
                            for function in transformed.functions))
        with self.assertRaises(ValueError):
            authenticate_sacred_star_number_division(drifted, entry["raw_sha256"])

    def test_sacred_fixed_affine_centers13_proof_is_exact(self) -> None:
        from tools.glslcpp import check_corpus
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.fixed_affine_centers13_proof import (
            attach_fixed_affine_centers13_proof,
        )
        from tools.glslcpp.frontend.sacred_geometry_compatibility import (
            apply_sacred_star_number_division,
        )
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "synth/sacredGeometry:sacredGeometry")
        typed = attach_fixed_affine_centers13_proof(
            apply_sacred_star_number_division(analyze_program(
                parse_program((root / entry["source"]).read_text(),
                              entry["program_key"], {}), entry["program_key"])))
        proof = typed.fixed_affine_centers13_proof
        self.assertIsNotNone(proof)
        self.assertEqual("fixed-affine-centers13-v1", proof.proof_kind)
        self.assertEqual((73, "centers", "vec2[13]", 13, "Centers13", 2),
                         (proof.symbol_id, proof.symbol_name, proof.array_type,
                          proof.extent, proof.native_alias,
                          proof.declaration_statement_index))
        self.assertEqual((96, 10, 21),
                         (proof.declaration_span.start_line,
                          proof.declaration_span.start_column,
                          proof.declaration_span.end_column))
        self.assertEqual(("center", "inner", "outer"),
                         tuple(region.role for region in proof.store_regions))
        self.assertEqual(
            ((3, None, None, None, None, None, 1, "literal:0", 0, 0, 1,
              97, 5, "b4192d798e6aa86813402556ac424648d3cec31bdbb9ccae290bb3333ae71460"),
             (4, 74, 0, 6, "<", "++", 6, "1+k@74", 1, 6, 6,
              100, 9, "afcc88b6f4d46a9c142ac22bb405b1e889b746a55efeba0571eed154f2b08868"),
             (5, 76, 0, 6, "<", "++", 6, "7+k@76", 7, 12, 6,
              104, 9, "82967ef419b7cdcb50c973bc75bd0de6a7d37cbd31eab59889ecd35579771b21")),
            tuple((region.statement_index, region.induction_symbol_id,
                   region.loop_start, region.loop_bound, region.comparison,
                   region.update, region.trip_count, region.index_profile,
                   region.lower_index, region.upper_index, region.write_count,
                   region.index_span.start_line, region.index_span.start_column,
                   region.rhs_profile) for region in proof.store_regions))
        self.assertEqual(("circle-origin", "circle-distance",
                          "line-left", "line-right"),
                         tuple(site.role for site in proof.read_sites))
        self.assertEqual(
            ((114, 39, "i@81", 81, 113, None, 13,
              "fe857f63689a36f1a7ac45c612f74f991455dc0e80e232470c66b9705b36572a"),
             (120, 30, "i@81", 81, 113, None, 13,
              "1defe8dd202804628f5018dff5d82d8f510af36e67ba193ee9ff6c998e7a68a5"),
             (140, 46, "i@88", 88, 137, 139, 78,
              "23c2caeec7badf25809db005d5d3b7ca665fd8ba0b8bfd50f81955eff1f61ae5"),
             (140, 58, "j@89", 89, 138, 139, 78,
              "23c2caeec7badf25809db005d5d3b7ca665fd8ba0b8bfd50f81955eff1f61ae5")),
            tuple((site.index_span.start_line, site.index_span.start_column,
                   site.index_profile, site.induction_symbol_id,
                   site.owning_loop_span.start_line,
                   None if site.control_span is None else site.control_span.start_line,
                   site.dynamic_read_count, site.enclosing_expression_profile)
                  for site in proof.read_sites))
        self.assertEqual(
            ("sacred-star-number-division-v1", 46, 106, 37, 107,
             (260, 13, 44), (260, 29, 39), (260, 29, 44),
             (260, 18, 44), (262, 30, 31)),
            (proof.compatibility_site.transform,
             proof.compatibility_site.function_signature_id,
             proof.compatibility_site.induction_symbol_id,
             proof.compatibility_site.divisor_symbol_id,
             proof.compatibility_site.local_symbol_id,
             (proof.compatibility_site.declaration_span.start_line,
              proof.compatibility_site.declaration_span.start_column,
              proof.compatibility_site.declaration_span.end_column),
             (proof.compatibility_site.division_span.start_line,
              proof.compatibility_site.division_span.start_column,
              proof.compatibility_site.division_span.end_column),
             (proof.compatibility_site.multiplication_span.start_line,
              proof.compatibility_site.multiplication_span.start_column,
              proof.compatibility_site.multiplication_span.end_column),
             (proof.compatibility_site.subtraction_span.start_line,
              proof.compatibility_site.subtraction_span.start_column,
              proof.compatibility_site.subtraction_span.end_column),
             (proof.compatibility_site.consumption_span.start_line,
              proof.compatibility_site.consumption_span.start_column,
              proof.compatibility_site.consumption_span.end_column)))
        self.assertEqual(
            ("261327d6c1700f71cef056020358ba1ea4dd56c1e8d1017f545df805a4f9b1d8",
             "fdaf48f945303bfe83c56ee0e2e75ae62d418904c02fc2bc6621fc0da907f7b2",
             "2dda5c4f3931965da85ac54fca2b6e4748cb2cb1ca61b03316f750c2f6754388",
             "de499dea91a59d8fc5ec4591be30a9b4350bb6a9e0317259aa97e8d3e3586ee0"),
            (proof.compatibility_site.pre_function_sha256,
             proof.compatibility_site.post_function_sha256,
             proof.compatibility_site.pre_whole_program_sha256,
             proof.compatibility_site.post_whole_program_sha256))
        self.assertEqual("9f8307702faa0f459256108a315cbeaa3ccb2e59d9181f7d6bd622b461009227",
                         proof.call_routing_profile)
        self.assertEqual("0eef7a910e92d8f9d010d54c68bb11cbd24492b24b14bdccb5f5a866ba84650d",
                         proof.draw_lines_guard_profile)
        self.assertEqual((1, 8, 7, 7, 3, 13, 4, 26, 156, 182),
                         (proof.array_declaration_count,
                          proof.array_typed_expression_count,
                          proof.array_base_identifier_count,
                          proof.index_expression_count,
                          proof.static_store_site_count,
                          proof.dynamic_store_count,
                          proof.static_read_site_count,
                          proof.circle_read_count,
                          proof.line_endpoint_read_count,
                          proof.maximum_dynamic_read_count))
        self.assertEqual((9, 0, 2, 169, 207, True),
                         (proof.loop_count, proof.unproved_loop_count,
                          proof.max_effective_depth, proof.max_lexical_product,
                          proof.entrypoint_charge, proof.call_graph_acyclic))
        self.assertEqual(104, proof.table_payload_bytes)
        self.assertTrue(proof.initialization_complete)
        self.assertTrue(proof.write_sets_disjoint)
        self.assertTrue(proof.initialization_dominates_reads)
        self.assertTrue(proof.no_post_read_writes)
        self.assertTrue(proof.no_alias_copy_escape)

    def test_sacred_fixed_affine_centers13_proof_rejects_structural_drift(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.fixed_affine_centers13_proof import (
            attach_fixed_affine_centers13_proof, prove_fixed_affine_centers13,
        )
        from tools.glslcpp.frontend import fixed_affine_centers13_proof as proof_module
        from tools.glslcpp.frontend.sacred_geometry_compatibility import (
            apply_sacred_star_number_division,
        )
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "synth/sacredGeometry:sacredGeometry")
        typed = attach_fixed_affine_centers13_proof(
            apply_sacred_star_number_division(analyze_program(
                parse_program((root / entry["source"]).read_text(),
                              entry["program_key"], {}), entry["program_key"])))
        fruit = next(function for function in typed.functions
                     if function.signature.id == 40 and function.body)
        changed_store = dataclasses.replace(
            fruit.body[3].expressions[0].children[0].children[1], literal="1",
            literal_value=1)
        target = fruit.body[3].expressions[0].children[0]
        changed_target = dataclasses.replace(
            target, children=(target.children[0], changed_store))
        assignment = fruit.body[3].expressions[0]
        changed_assignment = dataclasses.replace(
            assignment, children=(changed_target, assignment.children[1]))
        body = list(fruit.body)
        body[3] = dataclasses.replace(body[3], expressions=(changed_assignment,))
        drifted = dataclasses.replace(
            typed,
            functions=tuple(dataclasses.replace(fruit, body=tuple(body))
                            if function is fruit else function
                            for function in typed.functions),
            fixed_affine_centers13_proof=None)
        with self.assertRaises(ValueError):
            prove_fixed_affine_centers13(drifted)
        foreign = dataclasses.replace(typed, key="synth/subdivide:subdivide")
        self.assertIsNone(
            attach_fixed_affine_centers13_proof(foreign).fixed_affine_centers13_proof)
        base = dataclasses.replace(typed, fixed_affine_centers13_proof=None)
        with mock.patch.object(
                proof_module, "_affine_index",
                return_value=("1+k@74", 1, 6, 5)):
            with self.assertRaises(ValueError):
                prove_fixed_affine_centers13(base)

    def test_sacred_fixed_affine_centers13_validates_and_emits_only_proved_sites(self) -> None:
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.fixed_affine_centers13_proof import (
            CAPABILITY, attach_fixed_affine_centers13_proof,
        )
        from tools.glslcpp.frontend.sacred_geometry_compatibility import (
            TRANSFORM, apply_sacred_star_number_division,
        )
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "synth/sacredGeometry:sacredGeometry")
        typed = attach_fixed_affine_centers13_proof(
            apply_sacred_star_number_division(analyze_program(
                parse_program((root / entry["source"]).read_text(),
                              entry["program_key"], {}), entry["program_key"])))
        capabilities = (*generate_typed_slice.APPROVED_CAPABILITIES,)
        self.assertIn(CAPABILITY, capabilities)
        generate_typed_slice.validate_capabilities(
            typed, capabilities, source_hash=entry["raw_sha256"],
            compatibility_transform=TRANSFORM, numeric_literal_contract="glsl-f32")
        emitted = render_typed_cpp(
            typed, entry["program_key"], entry["raw_sha256"],
            numeric_literal_contract="glsl-f32", compatibility_transform=TRANSFORM)
        self.assertIn("using Centers13 = std::array<glsl::Vec2, 13>;", emitted)
        self.assertIn("static_assert(sizeof(glsl::Vec2) == 8U);", emitted)
        self.assertIn("static_assert(sizeof(Centers13) == 104U);", emitted)
        self.assertEqual(1, emitted.count("Centers13 centers{};"))
        self.assertEqual(7, emitted.count("centers[static_cast<std::size_t>("))
        j_line = next(line for line in emitted.splitlines()
                      if "double j =" in line)
        self.assertIn("static_cast<double>", j_line)
        self.assertNotIn("integer_mod", j_line)
        self.assertNotIn("%", j_line)
        self.assertNotRegex(j_line, r"static_cast<std::int(?:32|64)_t>")

    def test_sacred_task20_tampering_rejects_at_both_boundaries(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.fixed_affine_centers13_proof import (
            attach_fixed_affine_centers13_proof,
        )
        from tools.glslcpp.frontend.sacred_geometry_compatibility import (
            TRANSFORM, apply_sacred_star_number_division,
        )
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "synth/sacredGeometry:sacredGeometry")
        typed = attach_fixed_affine_centers13_proof(
            apply_sacred_star_number_division(analyze_program(
                parse_program((root / entry["source"]).read_text(),
                              entry["program_key"], {}), entry["program_key"])))
        proof = typed.fixed_affine_centers13_proof
        self.assertIsNotNone(proof)
        stale = dataclasses.replace(typed, source=typed.source + "\n")
        attacker_raw = typed.raw_source + "\n"
        attacker = dataclasses.replace(
            typed, raw_source=attacker_raw,
            fixed_affine_centers13_proof=dataclasses.replace(
                proof, raw_source_sha256=hashlib.sha256(attacker_raw.encode()).hexdigest()))
        candidates = {
            "cleared": dataclasses.replace(typed, fixed_affine_centers13_proof=None),
            "stale": stale,
            "attacker-updated": attacker,
            "forged-task17": dataclasses.replace(typed, fixed_nine_table_proof=object()),
            "forged-task18": dataclasses.replace(typed, fixed_grid_counter_store_proof=object()),
            "forged-task19": dataclasses.replace(typed, fixed_array_in_parameter_proof=object()),
        }
        for name, candidate in candidates.items():
            with self.subTest(name=name, boundary="validator"), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=entry["raw_sha256"],
                    compatibility_transform=TRANSFORM,
                    numeric_literal_contract="glsl-f32")
            with self.subTest(name=name, boundary="emitter"), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    candidate, entry["program_key"], entry["raw_sha256"],
                    numeric_literal_contract="glsl-f32",
                    compatibility_transform=TRANSFORM)
        for transform, numeric in ((None, "glsl-f32"), ("none", "glsl-f32"),
                                   ("wrong", "glsl-f32"), (TRANSFORM, "source-double")):
            with self.subTest(transform=transform, numeric=numeric, boundary="validator"), \
                    self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=entry["raw_sha256"],
                    compatibility_transform=transform,
                    numeric_literal_contract=numeric)
            with self.subTest(transform=transform, numeric=numeric, boundary="emitter"), \
                    self.assertRaises(TypedEmissionError):
                render_typed_cpp(
                    typed, entry["program_key"], entry["raw_sha256"],
                    numeric_literal_contract=numeric,
                    compatibility_transform=transform)

    def test_sacred_task20_exclusions_remain_closed(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.fixed_affine_centers13_proof import (
            CAPABILITY, attach_fixed_affine_centers13_proof,
        )
        from tools.glslcpp.frontend.sacred_geometry_compatibility import (
            TRANSFORM, apply_sacred_star_number_division,
        )
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        sacred_entry = next(item for item in manifest["programs"]
                            if item["program_key"] == "synth/sacredGeometry:sacredGeometry")
        typed = attach_fixed_affine_centers13_proof(
            apply_sacred_star_number_division(analyze_program(
                parse_program((root / sacred_entry["source"]).read_text(),
                              sacred_entry["program_key"], {}),
                sacred_entry["program_key"])))
        foreign = dataclasses.replace(typed, key="synth/subdivide:subdivide")
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=sacred_entry["raw_sha256"],
                compatibility_transform=TRANSFORM)
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(
                foreign, foreign.key, sacred_entry["raw_sha256"],
                compatibility_transform=TRANSFORM)
        non_sacred = dataclasses.replace(typed, fixed_affine_centers13_proof=None,
                                         key="synth/subdivide:subdivide")
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                non_sacred, (*generate_typed_slice.APPROVED_CAPABILITIES, CAPABILITY),
                source_hash=sacred_entry["raw_sha256"])

    def test_task21_degauss_profile_is_exact_and_current_vocabulary(self) -> None:
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        metadata = json.loads((root / "metadata.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "filter/degauss:degauss")
        typed = analyze_program(parse_program(
            (root / entry["source"]).read_text(), entry["program_key"], {}),
            entry["program_key"])

        generate_typed_slice.validate_current_vocabulary_degauss(
            typed, entry, {}, compatibility_transform=None,
            numeric_literal_contract="glsl-f32",
            metadata_effect=metadata["effects"]["filter/degauss"])
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=entry["raw_sha256"], compatibility_transform=None,
            numeric_literal_contract="glsl-f32")
        emitted = render_typed_cpp(
            typed, entry["program_key"], entry["raw_sha256"],
            numeric_literal_contract="glsl-f32", compatibility_transform=None)
        self.assertIn("namespace typed_kernel {", emitted)
        self.assertNotIn("void main(", emitted)

        slice_spec = generate_typed_slice.load_slice(REPOSITORY)
        slice_spec["programs"] = [item for item in slice_spec["programs"]
                                  if item["program_key"] not in {
                                      "filter/rotate:rot",
                                      "mixer/focusBlur:focusBlur",
                                      "filter/extrude:extrude",
                                      "synth/curl:curl",
                                      "filter/grade:creative",
                                      "filter/grade:hslSecondary",
                                      "filter/grade:lut",
                                      "filter/grade:primary",
                                      "filter/grade:vignette",
                                      "filter/grade:wheels"}]
        self.assertEqual(127, len(slice_spec["programs"]))
        self.assertEqual(1, sum(item["program_key"] == "filter/degauss:degauss"
                                for item in slice_spec["programs"]))
        self.assertNotIn("filter/degauss:degauss",
                         slice_spec["compatibility_transforms"])
        self.assertNotIn("filter/degauss:degauss",
                         slice_spec["numeric_literal_contracts"])
        self.assertEqual("f515a7ac409c98fc420d9fa9a7e460eb37018b34e3be40419191fc7655a29c38",
                         generate_typed_slice.DEGAUSS_CANONICAL_FACTORY_TEXT_SHA256)
        self.assertEqual("e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56",
                         generate_typed_slice.DEGAUSS_CANONICAL_RUNTIME_SHA256)

        vocabulary = {
            "approved_capabilities": list(generate_typed_slice.APPROVED_CAPABILITIES),
            "approved_types": list(generate_typed_slice.APPROVED_TYPES),
            "approved_binary_operators": list(generate_typed_slice.APPROVED_BINARY_OPERATORS),
            "approved_assignment_operators": list(generate_typed_slice.APPROVED_ASSIGNMENT_OPERATORS),
            "builtins": sorted(generate_typed_slice._BUILTINS),
            "slice_capabilities": slice_spec["capabilities"],
            "slice_types": slice_spec["types"],
            "slice_binary_operators": slice_spec["binary_operators"],
            "slice_assignment_operators": slice_spec["assignment_operators"],
            "compatibility_transforms": slice_spec["compatibility_transforms"],
            "numeric_literal_contracts": slice_spec["numeric_literal_contracts"],
        }
        payload = json.dumps(vocabulary, sort_keys=True,
                             separators=(",", ":")).encode()
        self.assertEqual("99afa5a55593e8c5b5756e1a0d23c06ee7bbf8a2cf44fbb6cc7ce25c43a718d5",
                         hashlib.sha256(json.dumps({
                             **vocabulary,
                             "compatibility_transforms": {
                                 key: value for key, value in
                                 slice_spec["compatibility_transforms"].items()
                                 if key != "filter/crt:crt"
                             },
                         }, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
        self.assertEqual((None, None, None, None), (
            typed.fixed_nine_table_proof,
            typed.fixed_grid_counter_store_proof,
            typed.fixed_array_in_parameter_proof,
            typed.fixed_affine_centers13_proof))

    def test_task21_degauss_profile_rejects_identity_interface_and_tree_drift(self) -> None:
        import copy
        import dataclasses
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        metadata = json.loads((root / "metadata.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "filter/degauss:degauss")
        typed = analyze_program(parse_program(
            (root / entry["source"]).read_text(), entry["program_key"], {}),
            entry["program_key"])

        def reject(candidate=typed, candidate_entry=entry, defines=None,
                   transform=None, numeric="glsl-f32", effect=None):
            with self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_current_vocabulary_degauss(
                    candidate, candidate_entry, {} if defines is None else defines,
                    compatibility_transform=transform,
                    numeric_literal_contract=numeric,
                    metadata_effect=(metadata["effects"]["filter/degauss"]
                                     if effect is None else effect))

        for field, value in {
                "program_key": "filter/crt:crt", "runtime_key": "filter/crt:crt",
                "effect_id": "filter/crt", "program": "crt", "pass_index": 1,
                "pass_name": "wrong", "source": "sources/filter/crt/crt.glsl",
                "raw_bytes": entry["raw_bytes"] + 1,
                "raw_sha256": "0" * 64, "normalized_bytes": entry["normalized_bytes"] + 1,
                "normalized_sha256": "1" * 64, "status": "adapter"}.items():
            changed = dict(entry); changed[field] = value
            with self.subTest(entry_field=field): reject(candidate_entry=changed)
        changed = dict(entry); changed["outputs"] = []
        reject(candidate_entry=changed)
        changed = dict(entry); changed["varyings"] = ["uv"]
        reject(candidate_entry=changed)
        reject(defines={"MODE": 1})
        reject(transform="degauss-transform-v1")
        reject(numeric="source-double")

        effect = copy.deepcopy(metadata["effects"]["filter/degauss"])
        effect["params"]["displacement"]["default"] = 0.125
        reject(effect=effect)
        effect = copy.deepcopy(metadata["effects"]["filter/degauss"])
        effect["passes"][0]["inputs"]["inputTex"] = "other"
        reject(effect=effect)

        reject(dataclasses.replace(typed, key="filter/crt:crt"))
        reject(dataclasses.replace(typed, raw_source=typed.raw_source + "\n"))
        reject(dataclasses.replace(typed, source=typed.source + "\n"))
        reject(dataclasses.replace(typed, functions=tuple(reversed(typed.functions))))
        reject(dataclasses.replace(typed, declarations=tuple(reversed(typed.declarations))))
        reject(dataclasses.replace(
            typed, resources=dataclasses.replace(typed.resources, uses_derivatives=True)))
        reject(dataclasses.replace(
            typed, counted_loop_proof=dataclasses.replace(
                typed.counted_loop_proof, entrypoint_charge=1)))
        for field in ("fixed_nine_table_proof", "fixed_grid_counter_store_proof",
                      "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof"):
            with self.subTest(foreign_proof=field):
                reject(dataclasses.replace(typed, **{field: object()}))

        def mutate_one(program, function_id, matcher, rewrite):
            matches = 0
            def expression(value):
                nonlocal matches
                updated = dataclasses.replace(
                    value, children=tuple(expression(child) for child in value.children))
                if matcher(updated):
                    matches += 1
                    return rewrite(updated)
                return updated
            def statement(value):
                return dataclasses.replace(
                    value,
                    expressions=tuple(expression(item) for item in value.expressions),
                    children=tuple(statement(child) for child in value.children))
            functions = tuple(
                dataclasses.replace(function, body=tuple(statement(item) for item in function.body))
                if function.signature.id == function_id else function
                for function in program.functions)
            self.assertEqual(1, matches)
            return dataclasses.replace(program, functions=functions)

        mutations = (
            (56, (365, 9, "literal", None, None, "0u"), {"literal": "2u", "literal_value": 2}),
            (66, (311, 38, "literal", None, None, "360.0"), {"literal": "1.0", "literal_value": 1.0}),
            (68, (36, 19, "binary", "%", None, None), {"operator": "/"}),
            (67, (47, 28, "builtin", None, "floor", None), {"callee": "abs"}),
            (62, (280, 16, "builtin", None, "clamp", None), {"callee": "max"}),
            (62, (281, 16, "builtin", None, "clamp", None), {"callee": "max"}),
            (54, (215, 9, "binary", "&&", None, None), {"operator": "||"}),
            (64, (249, 24, "literal", None, None, "5.0"), {"literal": "1.0", "literal_value": 1.0}),
            (56, (400, 19, "call", None, "clamp01", None), {"callee": "normalized_sine"}),
            (56, (357, 33, "builtin", None, "min", None), {"callee": "max"}),
            (63, (170, 12, "literal", None, None, "42.0"), {"literal": "41.0", "literal_value": 41.0}),
            (54, (189, 24, "swizzle", None, None, None), {"member": "x"}),
            (54, (200, 39, "literal", None, None, "73.0"), {"literal": "0.0", "literal_value": 0.0}),
        )
        for index, (function_id, signature, changes) in enumerate(mutations):
            line, column, kind, operator, callee, literal = signature
            def matcher(value, line=line, column=column, kind=kind,
                        operator=operator, callee=callee, literal=literal):
                return (value.span.start_line == line and value.span.start_column == column
                        and value.kind == kind
                        and (operator is None or value.operator == operator)
                        and (callee is None or value.callee == callee)
                        and (literal is None or value.literal == literal))
            with self.subTest(semantic_mutation=index):
                reject(mutate_one(
                    typed, function_id, matcher,
                    lambda value, changes=changes: dataclasses.replace(value, **changes)))

        generic_candidate = mutate_one(
            typed, 56,
            lambda value: (value.span.start_line == 365
                           and value.span.start_column == 9
                           and value.kind == "literal" and value.literal == "0u"),
            lambda value: dataclasses.replace(
                value, literal="2u", literal_value=2))
        generate_typed_slice.validate_capabilities(
            generic_candidate, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=entry["raw_sha256"], compatibility_transform=None,
            numeric_literal_contract="glsl-f32")
        reject(generic_candidate)

    def test_task21_adds_no_capability_transform_or_numeric_exception(self) -> None:
        from tools.glslcpp import generate_typed_slice

        spec = generate_typed_slice.load_slice(REPOSITORY)
        self.assertEqual(tuple(spec["capabilities"]),
                         generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertEqual(tuple(spec["types"]), generate_typed_slice.APPROVED_TYPES)
        self.assertEqual(tuple(spec["binary_operators"]),
                         generate_typed_slice.APPROVED_BINARY_OPERATORS)
        self.assertEqual(tuple(spec["assignment_operators"]),
                         generate_typed_slice.APPROVED_ASSIGNMENT_OPERATORS)
        self.assertEqual({"filter/scatter:scatterJitter": "source-double"},
                         spec["numeric_literal_contracts"])
        self.assertEqual({
            "classicNoisedeck/coalesce:coalesce": "coalesce-uv-alias-v1",
            "classicNoisedeck/refract:refract": "refract-truthy-vector-conditional-noop-v1",
            "filter/corrupt:corrupt": "corrupt-sample-uv-alias-v1",
            "filter/crt:crt": "crt-metal-sine-v1",
            "mixer/shapeMask:shapeMask": "shape-mask-sequential-lanes-v1",
            "synth/polygon:shape": "polygon-zero-smoothing-v1",
            "synth/sacredGeometry:sacredGeometry": "sacred-star-number-division-v1",
        }, spec["compatibility_transforms"])

    # NOT a historical reconstruction despite the task-numbered name. The
    # exclusion set is deliberately narrow: it drops only the programs whose
    # generalized profiles would perturb the exact neighbour/ordering
    # assertions below. Programs added after Task 21 (e.g. synth/perlin:perlin
    # from Task 27) remain present in the resulting list. For true as-of-stage
    # byte reconstruction see the tests that mock load_slice and hash-compare
    # generate_outputs, e.g.
    # test_task29_schema_counts_hashes_and_real_task28_reconstruction_isolation.
    def test_task21_degauss_exclusions_remain_closed(self) -> None:
        import copy
        import re
        from unittest import mock
        from tools.glslcpp import check_corpus, generate_typed_slice

        spec = generate_typed_slice.load_slice(REPOSITORY)
        keys = [item["program_key"] for item in spec["programs"]
                if item["program_key"] not in {
                    "filter/rotate:rot", "mixer/focusBlur:focusBlur",
                    "filter/extrude:extrude", "synth/curl:curl",
                    "filter/grade:creative", "filter/grade:hslSecondary",
                    "filter/grade:lut", "filter/grade:primary",
                    "filter/grade:vignette", "filter/grade:wheels"}]
        self.assertEqual(127, len(keys))
        self.assertEqual(keys, sorted(set(keys)))
        self.assertEqual("filter/crt:crt",
                         keys[keys.index("filter/degauss:degauss") - 1])
        self.assertEqual("filter/deriv:deriv",
                         keys[keys.index("filter/degauss:degauss") + 1])
        self.assertEqual("filter/craquelure:craquelure",
                         keys[keys.index("filter/crt:crt") - 1])
        self.assertEqual(1, keys.count("filter/crt:crt"))
        original = json.loads(
            (REPOSITORY / "tools/glslcpp/typed_slice.json").read_text())
        for name, replacement in (
                ("missing-degauss", "filter/zzz:zzz"),
                ("missing-crt", "filter/zzz:zzz")):
            mutated = copy.deepcopy(original)
            if name == "missing-degauss":
                mutated["programs"] = [
                    ({"defines": {}, "program_key": replacement}
                     if item["program_key"] == "filter/degauss:degauss" else item)
                    for item in mutated["programs"]]
            else:
                mutated["programs"] = [
                    ({"defines": {}, "program_key": replacement}
                     if item["program_key"] == "filter/crt:crt" else item)
                    for item in mutated["programs"]]
            mutated["programs"].sort(key=lambda item: item["program_key"])
            with self.subTest(loader_mutation=name), tempfile.TemporaryDirectory() as temporary:
                repository = pathlib.Path(temporary)
                target = repository / "tools/glslcpp/typed_slice.json"
                target.parent.mkdir(parents=True)
                target.write_text(json.dumps(mutated), encoding="utf-8")
                with self.assertRaisesRegex(
                        generate_typed_slice.GeneratorError,
                        "typed slice literal vec3 lane profile drift"):
                    generate_typed_slice.load_slice(repository)
        corpus_root = check_corpus._corpus_root(REPOSITORY)
        corpus_manifest = json.loads((corpus_root / "manifest.json").read_text())
        self.assertEqual((127, 129, 83, 212),
                         (len(keys), len(keys) + 2,
                          len(corpus_manifest["programs"]) - len(keys) - 2,
                          len(corpus_manifest["programs"])))

        current = generate_typed_slice.generate_outputs(REPOSITORY)
        current_cpp = current["src/typed_generated/typed_slice.cpp"].decode()
        old = copy.deepcopy(spec)
        old["programs"] = [item for item in old["programs"]
                           if item["program_key"] != "filter/degauss:degauss"]
        with mock.patch.object(generate_typed_slice, "load_slice", return_value=old):
            prior_cpp = generate_typed_slice.generate_outputs(REPOSITORY)[
                "src/typed_generated/typed_slice.cpp"].decode()

        marker = re.compile(r"(?m)^// Typed IR program: (.+)$")
        def blocks(text):
            hits = list(marker.finditer(text)); result = {}
            for index, hit in enumerate(hits):
                end = (hits[index + 1].start() if index + 1 < len(hits)
                       else text.index("\nnamespace {", hit.end()))
                result[hit.group(1)] = text[hit.start():end]
            return result
        before = blocks(prior_cpp); after = blocks(current_cpp)
        self.assertEqual(set(before), set(after) - {"filter/degauss:degauss"})
        for key in sorted(before):
            with self.subTest(key=key):
                if key < "filter/degauss:degauss":
                    self.assertEqual(before[key], after[key])
                normalize = lambda value: re.sub(r"typed_[0-9]+", "typed_N", value)
                self.assertEqual(normalize(before[key]), normalize(after[key]))

        degauss = after["filter/degauss:degauss"]
        self.assertEqual(1, degauss.count("namespace typed_22 {"))
        self.assertNotIn("void main(", degauss)
        def function_body(signature):
            start = degauss.rindex(signature)
            opening = degauss.index("{", start)
            depth = 0
            for offset in range(opening, len(degauss)):
                if degauss[offset] == "{":
                    depth += 1
                elif degauss[offset] == "}":
                    depth -= 1
                    if depth == 0:
                        return degauss[start:offset + 1]
            self.fail(f"unterminated generated function {signature}")

        pixel_body = function_body("void pixel(")
        warped_body = function_body("[[nodiscard]] double warped_channel_value(")
        compute_body = function_body("[[nodiscard]] double compute_noise_value(")
        simplex_body = function_body("[[nodiscard]] double simplex_noise(")
        sample_body = function_body("[[nodiscard]] glsl::Vec4 sample_bilinear(")
        wrap_float_body = function_body("[[nodiscard]] double wrap_float(")
        wrap_index_body = function_body("[[nodiscard]] std::int32_t wrap_index(")
        self.assertEqual(4, sample_body.count("fetch_texel("))
        self.assertEqual(1, pixel_body.count("fetch_texel("))
        self.assertEqual(6, degauss.count("fetch_texel("))  # definition + calls
        self.assertEqual(1, wrap_index_body.count("glsl::integer_mod("))
        self.assertNotIn("%", wrap_index_body)
        self.assertEqual(3, pixel_body.count("warped_channel_value("))
        for channel in range(3):
            self.assertIn(f"warped_channel_value(state, context, std::uint32_t({channel})",
                          pixel_body)
        self.assertEqual(1, pixel_body.count("singularity_mask("))
        self.assertEqual(1, pixel_body.count("freq_for_shape("))
        self.assertEqual(1, warped_body.count("compute_noise_value("))
        self.assertEqual(1, warped_body.count("sample_bilinear("))
        self.assertEqual(2, compute_body.count("simplex_noise("))
        self.assertEqual(2, compute_body.count("periodic_value("))
        self.assertEqual(1, simplex_body.count("mod289_vec3("))
        self.assertEqual(3, simplex_body.count("permute("))
        self.assertEqual(1, simplex_body.count("taylor_inv_sqrt("))
        self.assertEqual(2, sample_body.count("wrap_float("))
        self.assertEqual(2, sample_body.count("wrap_index("))
        hot_bodies = "\n".join((pixel_body, warped_body, compute_body,
                                 simplex_body, sample_body, wrap_float_body,
                                 wrap_index_body))
        self.assertNotRegex(
            hot_bodies,
            r"operator new|operator delete|malloc|free|std::function|std::map|"
            r"std::unordered_map|std::variant|std::string|throw|alloca|\.at\(")

        manifest = json.loads(current[
            "src/typed_generated/typed_manifest.json"].decode())
        entries = [item for item in manifest["programs"]
                   if item["program_key"] == "filter/degauss:degauss"]
        self.assertEqual(1, len(entries))
        self.assertEqual("none", entries[0]["compatibility_transform"])
        self.assertEqual("glsl-f32", entries[0]["numeric_literal_contract"])
        self.assertEqual("none", entries[0]["define_contract"])

    def test_task22_crt_transform_is_exact(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "filter/crt:crt")
        raw = analyze_program(parse_program(
            (corpus / entry["source"]).read_text(), entry["program_key"], {}),
            entry["program_key"])

        def expressions(function):
            result = []
            def visit_expression(value):
                result.append(value)
                for child in value.children:
                    visit_expression(child)
            def visit_statement(value):
                for expression in value.expressions:
                    visit_expression(expression)
                for child in value.children:
                    visit_statement(child)
            for statement in function.body:
                visit_statement(statement)
            return result

        raw_sine_arguments = {
            (function.id, value.span.start_line, value.span.start_column):
                value.children[0]
            for function in raw.functions
            for value in expressions(function)
            if value.kind == "builtin" and value.callee == "sin"
        }
        self.assertEqual(6, len(raw_sine_arguments))
        transformed = generate_typed_slice.apply_compatibility_transform(
            raw, "crt-metal-sine-v1")

        self.assertEqual(
            "1b67fa6d01135e98434bc9e6a4627f0d23565c81fa1e17cbdba10082e23e37a3",
            hashlib.sha256(repr(transformed.functions).encode()).hexdigest())
        whole = (
            transformed.key, transformed.source, transformed.raw_source,
            transformed.declarations, transformed.functions,
            transformed.resources, transformed.body_status,
            transformed.local_type_names, transformed.structs,
            transformed.uniform_blocks, transformed.interface_symbols,
            transformed.builtin_symbols, transformed.counted_loop_proof,
            transformed.preprocessor_defines,
        )
        self.assertEqual(
            "7aa853a51316b1122750af1155411a5ca8c1e11cf02688a33d9ef6fcace5f6a2",
            hashlib.sha256(repr(whole).encode()).hexdigest())

        sin_expected = {
            (98, 257, 37): "fee8d1478892ff364e1f2222fbe484ec9c2821fde88981ac3411c7f460b0c991",
            (105, 278, 18): "7b805551b3f93876e1bd5ecf76a76efea15276160a8aa7bad7a570ba5da70457",
            (111, 61, 12): "37e92090742c393c51e58b0e243ed94b7c496d81713c72f50a81965ab65d0906",
            (114, 32, 18): "ebf5806ccb5844082b4824ae98be478a0ccbbedcc446d11e1f782a05a5259fb7",
            (118, 38, 15): "d86ca37ad7e92a214a0aa669208b860c8c2691623ef830abe7275b6f83a99034",
            (118, 39, 18): "13a34f969f04eca11820a7aadee45a56f11e5ae369dfac59e02cb88e78673746",
        }
        sin_actual = {}
        for function in transformed.functions:
            for value in expressions(function):
                if value.kind == "builtin" and value.callee == "sin":
                    site_key = (function.id, value.span.start_line,
                                value.span.start_column)
                    sin_actual[site_key] = hashlib.sha256(
                        repr(value).encode()).hexdigest()
                    reduced = value.children[0]
                    phase = reduced.children[0]
                    turns, floor = phase.children
                    self.assertIs(turns, floor.children[0])
                    retained_argument = turns.children[0].children[0]
                    self.assertIs(retained_argument,
                                  raw_sine_arguments[site_key])
                    equal_field_clone = dataclasses.replace(
                        raw_sine_arguments[site_key])
                    self.assertEqual(raw_sine_arguments[site_key],
                                     equal_field_clone)
                    self.assertIsNot(raw_sine_arguments[site_key],
                                     equal_field_clone)
                    self.assertIsNot(retained_argument, equal_field_clone)
                    self.assertEqual(("0.15915493667125702",
                                      0.15915493667125702),
                                     (turns.children[0].children[1].literal,
                                      turns.children[0].children[1].literal_value))
                    self.assertEqual(("6.2831854820251465",
                                      6.2831854820251465),
                                     (reduced.children[1].literal,
                                      reduced.children[1].literal_value))
        self.assertEqual(sin_expected, sin_actual)

        cos_expected = {
            (118, 37, 15): "d73adbb7e0f3b9c5cb4eb121ac454f08d16cd19bb651b9b3bfb6ddf352fae17a",
            (91, 198, 20): "aa8a39a243601c48cdaa3b328c2aeb5ee045908c55f154e1c7ba69058d29966e",
            (98, 257, 25): "9c88ea057347d9c9f968a43c5b9d0a289a689cf6166b8f19a8c7ff1586e64bd9",
            (94, 329, 27): "f9a0165495911c862940e37195b8d97eba9709c3b6e42ce42b5822e4f152c95d",
        }
        cos_actual = {
            (function.id, value.span.start_line, value.span.start_column):
                hashlib.sha256(repr(value).encode()).hexdigest()
            for function in transformed.functions
            for value in expressions(function)
            if value.kind == "builtin" and value.callee == "cos"
        }
        self.assertEqual(cos_expected, cos_actual)

        changed = {
            before.id for before, after in zip(raw.functions, transformed.functions)
            if before != after
        }
        self.assertEqual({98, 105, 111, 114, 118}, changed)
        for before, after in zip(raw.functions, transformed.functions):
            if before.id not in changed:
                self.assertEqual(before, after)
        for field in ("fixed_nine_table_proof", "fixed_grid_counter_store_proof",
                      "fixed_array_in_parameter_proof",
                      "fixed_affine_centers13_proof"):
            self.assertIsNone(getattr(transformed, field))

    def test_task22_crt_four_mode_forgery_matrix(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "filter/crt:crt")
        raw = analyze_program(parse_program(
            (corpus / entry["source"]).read_text(), entry["program_key"], {}),
            entry["program_key"])
        post = generate_typed_slice.apply_compatibility_transform(
            raw, "crt-metal-sine-v1")

        def shared_turn_sites(program):
            count = 0
            def expression(value):
                nonlocal count
                if value.kind == "builtin" and value.callee == "sin":
                    try:
                        phase = value.children[0].children[0]
                        turns, floor = phase.children
                        if floor.children[0] is turns: count += 1
                    except (IndexError, TypeError):
                        pass
                for child in value.children: expression(child)
            def statement(value):
                for item in value.expressions: expression(item)
                for child in value.children: statement(child)
            for function in program.functions:
                for item in function.body: statement(item)
            return count

        self.assertEqual(6, shared_turn_sites(post))

        def accepted(candidate, carrier, source_hash, numeric="glsl-f32"):
            results = []
            try:
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash, compatibility_transform=carrier,
                    numeric_literal_contract=numeric)
                results.append(True)
            except generate_typed_slice.GeneratorError:
                results.append(False)
            try:
                render_typed_cpp(
                    candidate, candidate.key, source_hash,
                    compatibility_transform=carrier,
                    numeric_literal_contract=numeric)
                results.append(True)
            except TypedEmissionError:
                results.append(False)
            return tuple(results)

        pinned = entry["raw_sha256"]
        self.assertEqual((False, False), accepted(raw, None, pinned))
        self.assertEqual((False, False), accepted(raw, "crt-metal-sine-v1", pinned))
        self.assertEqual((False, False), accepted(post, None, pinned))
        self.assertEqual((True, True), accepted(post, "crt-metal-sine-v1", pinned))
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.apply_compatibility_transform(
                post, "crt-metal-sine-v1")

        raw_function = raw.functions[0]
        raw_mutations = {
            "defines": dataclasses.replace(
                raw, preprocessor_defines=(("MODE", 1),)),
            "declaration-order": dataclasses.replace(
                raw, declarations=tuple(reversed(raw.declarations))),
            "loop-proof": dataclasses.replace(
                raw, counted_loop_proof=dataclasses.replace(
                    raw.counted_loop_proof, entrypoint_charge=1)),
            "function-id": dataclasses.replace(
                raw, functions=(dataclasses.replace(
                    raw_function, signature=dataclasses.replace(
                        raw_function.signature,
                        id=raw_function.signature.id + 1000)), *raw.functions[1:])),
            "function-name": dataclasses.replace(
                raw, functions=(dataclasses.replace(
                    raw_function, signature=dataclasses.replace(
                        raw_function.signature,
                        name=raw_function.signature.name + "_drift")),
                                *raw.functions[1:])),
            "function-body": dataclasses.replace(
                raw, functions=(dataclasses.replace(
                    raw_function, body=raw_function.body[:-1]),
                                *raw.functions[1:])),
            "function-span": dataclasses.replace(
                raw, functions=(dataclasses.replace(
                    raw_function, span=raw.functions[1].span),
                                *raw.functions[1:])),
        }
        for name, candidate in raw_mutations.items():
            with self.subTest(raw_mutation=name), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.apply_compatibility_transform(
                    candidate, "crt-metal-sine-v1")
            self.assertEqual((False, False),
                             accepted(candidate, "crt-metal-sine-v1", pinned))

        def clone_shared_turns(program):
            matches = 0
            def expression(value):
                nonlocal matches
                children = tuple(expression(child) for child in value.children)
                if not all(left is right for left, right in
                           zip(children, value.children)):
                    value = dataclasses.replace(value, children=children)
                if (value.kind == "builtin" and value.callee == "sin"
                        and value.span.start_line == 257
                        and value.span.start_column == 37):
                    reduced = value.children[0]
                    phase, tau = reduced.children
                    turns, floor = phase.children
                    cloned = dataclasses.replace(turns)
                    phase = dataclasses.replace(
                        phase, children=(turns, dataclasses.replace(
                            floor, children=(cloned,))))
                    matches += 1
                    return dataclasses.replace(
                        value, children=(dataclasses.replace(
                            reduced, children=(phase, tau)),))
                return value
            def statement(value):
                expressions = tuple(expression(item) for item in value.expressions)
                children = tuple(statement(item) for item in value.children)
                if (all(left is right for left, right in
                        zip(expressions, value.expressions))
                        and all(left is right for left, right in
                                zip(children, value.children))):
                    return value
                return dataclasses.replace(value, expressions=expressions,
                                           children=children)
            candidate = dataclasses.replace(
                program, functions=tuple(dataclasses.replace(
                    function, body=tuple(statement(item) for item in function.body))
                    for function in program.functions))
            self.assertEqual(1, matches)
            return candidate

        forged = {
            "normalized-source": dataclasses.replace(post, source=post.source + "\n"),
            "raw-source": dataclasses.replace(post, raw_source=post.raw_source + "\n"),
            "function-order": dataclasses.replace(post, functions=tuple(reversed(post.functions))),
            "resource": dataclasses.replace(
                post, resources=dataclasses.replace(
                    post.resources, uses_derivatives=True)),
            "shared-turns-clone": clone_shared_turns(post),
            "task17-proof": dataclasses.replace(post, fixed_nine_table_proof=object()),
            "task18-proof": dataclasses.replace(post, fixed_grid_counter_store_proof=object()),
            "task19-proof": dataclasses.replace(post, fixed_array_in_parameter_proof=object()),
            "task20-proof": dataclasses.replace(post, fixed_affine_centers13_proof=object()),
            "defines": dataclasses.replace(post, preprocessor_defines=(("MODE", 1),)),
            "declaration-order": dataclasses.replace(
                post, declarations=tuple(reversed(post.declarations))),
            "loop-proof": dataclasses.replace(
                post, counted_loop_proof=dataclasses.replace(
                    post.counted_loop_proof, entrypoint_charge=1)),
            "function-id": dataclasses.replace(
                post, functions=(dataclasses.replace(
                    post.functions[0], signature=dataclasses.replace(
                        post.functions[0].signature,
                        id=post.functions[0].signature.id + 1000)),
                                 *post.functions[1:])),
            "function-name": dataclasses.replace(
                post, functions=(dataclasses.replace(
                    post.functions[0], signature=dataclasses.replace(
                        post.functions[0].signature,
                        name=post.functions[0].signature.name + "_drift")),
                                 *post.functions[1:])),
            "function-body": dataclasses.replace(
                post, functions=(dataclasses.replace(
                    post.functions[0], body=post.functions[0].body[:-1]),
                                 *post.functions[1:])),
            "function-span": dataclasses.replace(
                post, functions=(dataclasses.replace(
                    post.functions[0], span=post.functions[1].span),
                                 *post.functions[1:])),
            "function-parameter": dataclasses.replace(
                post, functions=tuple(
                    dataclasses.replace(function, signature=dataclasses.replace(
                        function.signature, parameters=(dataclasses.replace(
                            function.parameters[0], name="parameter_drift"),
                            *function.parameters[1:])))
                    if function.id == post.functions[0].id else function
                    for function in post.functions)),
            "duplicate-functions": dataclasses.replace(
                post, functions=(*post.functions, post.functions[-1])),
        }
        for name, candidate in forged.items():
            self.assertEqual(5 if name == "shared-turns-clone" else 6,
                             shared_turn_sites(candidate))
            recomputed = hashlib.sha256(candidate.raw_source.encode()).hexdigest()
            for hash_name, source_hash in (("authentic", pinned),
                                           ("cleared", None),
                                           ("stale", "0" * 64),
                                           ("attacker-updated", recomputed)):
                with self.subTest(name=name, hash=hash_name):
                    self.assertEqual(
                        (False, False),
                        accepted(candidate, "crt-metal-sine-v1", source_hash))

        def mutate_sine(program, site_key, rewrite):
            matches = 0
            def expression(function, value):
                nonlocal matches
                children = tuple(expression(function, child)
                                 for child in value.children)
                current = (dataclasses.replace(value, children=children)
                           if children != value.children else value)
                key = (function.id, current.span.start_line,
                       current.span.start_column)
                if (current.kind == "builtin" and current.callee == "sin"
                        and key == site_key):
                    matches += 1
                    return rewrite(current)
                return current
            def statement(function, value):
                return dataclasses.replace(
                    value,
                    expressions=tuple(expression(function, item)
                                      for item in value.expressions),
                    children=tuple(statement(function, item)
                                   for item in value.children))
            candidate = dataclasses.replace(
                program, functions=tuple(dataclasses.replace(
                    function, body=tuple(statement(function, item)
                                         for item in function.body))
                    for function in program.functions))
            self.assertEqual(1, matches)
            return candidate

        site_keys = ((98, 257, 37), (105, 278, 18), (111, 61, 12),
                     (114, 32, 18), (118, 38, 15), (118, 39, 18))
        for site_key in site_keys:
            candidate = mutate_sine(
                post, site_key,
                lambda value: dataclasses.replace(value, callee="cos"))
            for mode, source_hash in (("authentic", pinned),
                                      ("cleared", None),
                                      ("stale", "0" * 64),
                                      ("attacker-updated", hashlib.sha256(
                                          candidate.raw_source.encode()).hexdigest())):
                with self.subTest(site=site_key, mode=mode):
                    self.assertEqual((False, False), accepted(
                        candidate, "crt-metal-sine-v1", source_hash))

        first_site = site_keys[0]
        def rewrite_inner(value, part):
            reduced = value.children[0]
            phase, tau = reduced.children
            turns, floor = phase.children
            scaled = turns.children[0]
            arg, inv_tau = scaled.children
            if part == "tau": tau = dataclasses.replace(tau, literal="6.0")
            elif part == "tau-value": tau = dataclasses.replace(tau, literal_value=6.0)
            elif part == "tau-type": tau = dataclasses.replace(
                tau, type=post.declarations[9].type)
            elif part == "tau-category": tau = dataclasses.replace(tau, category="lvalue")
            elif part == "tau-span": tau = dataclasses.replace(
                tau, span=post.declarations[0].span)
            elif part == "outer-op": reduced = dataclasses.replace(reduced, operator="+")
            elif part == "phase-op": phase = dataclasses.replace(phase, operator="+")
            elif part == "floor": floor = dataclasses.replace(floor, callee="abs")
            elif part == "floor-signature": floor = dataclasses.replace(
                floor, signature_id=-18)
            elif part == "floor-order": phase = dataclasses.replace(
                phase, children=(floor, turns))
            elif part == "construct": turns = dataclasses.replace(turns, kind="call")
            elif part == "construct-type": turns = dataclasses.replace(
                turns, type=post.declarations[9].type)
            elif part == "constructor-type": turns = dataclasses.replace(
                turns, constructor_type=post.declarations[9].type)
            elif part == "floor-kind": floor = dataclasses.replace(floor, kind="call")
            elif part == "inv-tau": inv_tau = dataclasses.replace(
                inv_tau, literal="0.16")
            elif part == "inv-tau-value": inv_tau = dataclasses.replace(
                inv_tau, literal_value=0.16)
            elif part == "inv-tau-type": inv_tau = dataclasses.replace(
                inv_tau, type=post.declarations[9].type)
            elif part == "inv-tau-category": inv_tau = dataclasses.replace(
                inv_tau, category="lvalue")
            elif part == "inv-tau-span": inv_tau = dataclasses.replace(
                inv_tau, span=post.declarations[0].span)
            elif part == "scaled-op": scaled = dataclasses.replace(
                scaled, operator="+")
            elif part == "argument":
                arg = dataclasses.replace(
                    arg, symbol_id=8, symbol=post.declarations[7].symbol)
            if part.startswith("inv-tau") or part == "scaled-op":
                scaled = dataclasses.replace(scaled, children=(arg, inv_tau))
                turns = dataclasses.replace(turns, children=(scaled,))
            if part == "argument":
                scaled = dataclasses.replace(scaled, children=(arg, inv_tau))
                turns = dataclasses.replace(turns, children=(scaled,))
            if part in {"floor", "floor-signature", "construct", "phase-op",
                        "construct-type", "constructor-type", "floor-kind",
                        "inv-tau", "inv-tau-value", "inv-tau-type",
                        "inv-tau-category", "inv-tau-span", "scaled-op",
                        "argument"}:
                phase = dataclasses.replace(phase, children=(turns, floor))
            if part != "outer-op":
                reduced = dataclasses.replace(reduced, children=(phase, tau))
            result = dataclasses.replace(value, children=(reduced,))
            if part == "outer-kind": result = dataclasses.replace(result, kind="call")
            elif part == "outer-signature": result = dataclasses.replace(
                result, signature_id=-41)
            elif part == "outer-type": result = dataclasses.replace(
                result, type=post.declarations[9].type)
            elif part == "outer-category": result = dataclasses.replace(
                result, category="lvalue")
            elif part == "outer-span": result = dataclasses.replace(
                result, span=post.declarations[0].span)
            return result

        for part in ("tau", "tau-value", "tau-type", "tau-category", "tau-span",
                     "outer-op", "phase-op", "floor", "floor-signature",
                     "floor-order", "construct", "inv-tau", "inv-tau-value",
                     "inv-tau-type", "inv-tau-category", "inv-tau-span",
                     "scaled-op", "construct-type", "constructor-type",
                     "floor-kind", "argument", "outer-kind", "outer-signature",
                     "outer-type", "outer-category", "outer-span"):
            candidate = mutate_sine(
                post, first_site,
                lambda value, part=part: rewrite_inner(value, part))
            with self.subTest(site_tree=part):
                self.assertEqual((False, False), accepted(
                    candidate, "crt-metal-sine-v1", pinned))

        def first_builtin(program, callee):
            found = []
            def expression(value):
                if value.kind == "builtin" and value.callee == callee:
                    found.append(value)
                for child in value.children: expression(child)
            def statement(value):
                for item in value.expressions: expression(item)
                for child in value.children: statement(child)
            for function in program.functions:
                for item in function.body: statement(item)
            return found[0]

        raw_site = first_builtin(raw, "sin")
        partial = mutate_sine(post, (114, 32, 18), lambda _: raw_site)
        self.assertEqual((False, False), accepted(
            partial, "crt-metal-sine-v1", pinned))
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.apply_compatibility_transform(
                partial, "crt-metal-sine-v1")

        def add_seventh_sine(program):
            target = first_builtin(program, "cos")
            matches = 0
            def expression(value):
                nonlocal matches
                children = tuple(expression(child) for child in value.children)
                current = (value if all(left is right for left, right in
                                        zip(children, value.children))
                           else dataclasses.replace(value, children=children))
                if value is target:
                    matches += 1
                    return dataclasses.replace(current, callee="sin", signature_id=-40)
                return current
            def statement(value):
                expressions = tuple(expression(item) for item in value.expressions)
                children = tuple(statement(item) for item in value.children)
                if (all(left is right for left, right in
                        zip(expressions, value.expressions))
                        and all(left is right for left, right in
                                zip(children, value.children))):
                    return value
                return dataclasses.replace(value, expressions=expressions,
                                           children=children)
            result = dataclasses.replace(program, functions=tuple(
                dataclasses.replace(function, body=tuple(
                    statement(item) for item in function.body))
                for function in program.functions))
            self.assertEqual(1, matches)
            return result

        seventh = add_seventh_sine(post)
        self.assertEqual(6, shared_turn_sites(seventh))
        self.assertEqual((False, False), accepted(
            seventh, "crt-metal-sine-v1", pinned))
        duplicate_target = first_builtin(post, "sin")
        duplicate_owner = post.functions[0]
        duplicate_statement = duplicate_owner.body[0]
        duplicate_statement = dataclasses.replace(
            duplicate_statement,
            expressions=(*duplicate_statement.expressions, duplicate_target))
        duplicate_sine = dataclasses.replace(
            post, functions=(dataclasses.replace(
                duplicate_owner,
                body=(duplicate_statement, *duplicate_owner.body[1:])),
                             *post.functions[1:]))
        self.assertEqual(7, shared_turn_sites(duplicate_sine))
        self.assertEqual((False, False), accepted(
            duplicate_sine, "crt-metal-sine-v1", pinned))
        compound_raw = mutate_sine(
            raw, (118, 39, 18),
            lambda value: dataclasses.replace(
                value, children=(dataclasses.replace(
                    value.children[0], operator="-"),)))
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.apply_compatibility_transform(
                compound_raw, "crt-metal-sine-v1")
        self.assertEqual((False, False), accepted(
            compound_raw, "crt-metal-sine-v1", pinned))

        unchanged_ids = set(function.id for function in post.functions) - {
            98, 105, 111, 114, 118}
        self.assertEqual(30, len(unchanged_ids))
        for function in post.functions:
            if function.id not in unchanged_ids: continue
            candidate = dataclasses.replace(
                post, functions=tuple(
                    dataclasses.replace(item, signature=dataclasses.replace(
                        item.signature, name=item.name + "_drift"))
                    if item.id == function.id else item
                    for item in post.functions))
            with self.subTest(unchanged_function=function.id):
                self.assertEqual((False, False), accepted(
                    candidate, "crt-metal-sine-v1", pinned))

        foreign = dataclasses.replace(post, key="filter/degauss:degauss")
        self.assertEqual((False, False),
                         accepted(foreign, "crt-metal-sine-v1", pinned))
        for carrier in ("none", "wrong", "sacred-star-number-division-v1"):
            with self.subTest(carrier=carrier):
                self.assertEqual((False, False), accepted(post, carrier, pinned))
        for numeric in (None, "source-double", "wrong"):
            with self.subTest(numeric=numeric):
                self.assertEqual((False, False),
                                 accepted(post, "crt-metal-sine-v1", pinned,
                                          numeric=numeric))

    def test_task22_crt_profile_rejects_identity_interface_and_tree_drift(self) -> None:
        import copy
        import dataclasses
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        self.assertTrue(hasattr(generate_typed_slice,
                                "validate_current_vocabulary_crt"))
        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())
        metadata = json.loads((corpus / "metadata.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == "filter/crt:crt")
        raw = analyze_program(parse_program(
            (corpus / entry["source"]).read_text(), entry["program_key"], {}),
            entry["program_key"])
        typed = generate_typed_slice.apply_compatibility_transform(
            raw, "crt-metal-sine-v1")

        def validate(candidate=typed, candidate_entry=entry, defines=None,
                     transform="crt-metal-sine-v1", numeric="glsl-f32",
                     effect=None):
            generate_typed_slice.validate_current_vocabulary_crt(
                candidate, candidate_entry, {} if defines is None else defines,
                compatibility_transform=transform,
                numeric_literal_contract=numeric,
                metadata_effect=(metadata["effects"]["filter/crt"]
                                 if effect is None else effect))

        validate()
        for field, value in {
                "program_key": "filter/degauss:degauss",
                "runtime_key": "filter/degauss:degauss",
                "effect_id": "filter/degauss", "program": "wrong",
                "pass_index": 1, "pass_name": "wrong",
                "source": "sources/filter/degauss/degauss.glsl",
                "raw_bytes": entry["raw_bytes"] + 1,
                "raw_sha256": "0" * 64,
                "normalized_bytes": entry["normalized_bytes"] + 1,
                "normalized_sha256": "1" * 64, "status": "adapter"}.items():
            changed = dict(entry); changed[field] = value
            with self.subTest(entry=field), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                validate(candidate_entry=changed)
        for field in ("outputs", "varyings"):
            changed = copy.deepcopy(entry)
            changed[field] = ["wrong"]
            with self.subTest(entry_collection=field), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                validate(candidate_entry=changed)
        for defines, transform, numeric in (({"MODE": 1}, "crt-metal-sine-v1", "glsl-f32"),
                                             ({}, None, "glsl-f32"),
                                             ({}, "wrong", "glsl-f32"),
                                             ({}, "crt-metal-sine-v1", "source-double")):
            with self.subTest(defines=defines, transform=transform, numeric=numeric), \
                    self.assertRaises(generate_typed_slice.GeneratorError):
                validate(defines=defines, transform=transform, numeric=numeric)
        effect = copy.deepcopy(metadata["effects"]["filter/crt"])
        effect["params"]["alpha"]["default"] = 0.25
        with self.assertRaises(generate_typed_slice.GeneratorError):
            validate(effect=effect)

        def leaf_paths(value, prefix=()):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield from leaf_paths(child, (*prefix, key))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    yield from leaf_paths(child, (*prefix, index))
            else:
                yield prefix

        def drift_leaf(value):
            if isinstance(value, bool): return not value
            if isinstance(value, int): return value + 1
            if isinstance(value, float): return value + 0.125
            if value is None: return "drift"
            return str(value) + "-drift"

        canonical_effect = metadata["effects"]["filter/crt"]
        for path in leaf_paths(canonical_effect):
            changed = copy.deepcopy(canonical_effect)
            parent = changed
            for component in path[:-1]: parent = parent[component]
            parent[path[-1]] = drift_leaf(parent[path[-1]])
            with self.subTest(metadata_leaf=path), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                validate(effect=changed)
        for name, candidate in {
                "key": dataclasses.replace(typed, key="filter/degauss:degauss"),
                "source": dataclasses.replace(typed, source=typed.source + "\n"),
                "functions": dataclasses.replace(
                    typed, functions=tuple(reversed(typed.functions))),
                "resources": dataclasses.replace(
                    typed, resources=dataclasses.replace(
                        typed.resources, uses_derivatives=True)),
                "proof": dataclasses.replace(typed, fixed_nine_table_proof=object()),
        }.items():
            with self.subTest(name=name), self.assertRaises(
                generate_typed_slice.GeneratorError):
                validate(candidate=candidate)

        def reject_everywhere(name, candidate):
            def shared_turn_sites(program):
                count = 0
                def expression(value):
                    nonlocal count
                    if value.kind == "builtin" and value.callee == "sin":
                        try:
                            phase = value.children[0].children[0]
                            turns, floor = phase.children
                            if floor.children[0] is turns: count += 1
                        except (IndexError, TypeError):
                            pass
                    for child in value.children: expression(child)
                def statement(value):
                    for item in value.expressions: expression(item)
                    for child in value.children: statement(child)
                for function in program.functions:
                    for item in function.body: statement(item)
                return count
            self.assertEqual(6, shared_turn_sites(candidate))
            with self.subTest(profile_semantic=name), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                validate(candidate=candidate)
            with self.subTest(validator_semantic=name), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=entry["raw_sha256"],
                    compatibility_transform="crt-metal-sine-v1",
                    numeric_literal_contract="glsl-f32")
            with self.subTest(emitter_semantic=name), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    candidate, candidate.key, entry["raw_sha256"],
                    compatibility_transform="crt-metal-sine-v1",
                    numeric_literal_contract="glsl-f32")

        semantic_candidates = {
            "pi-f32": dataclasses.replace(
                typed, declarations=(dataclasses.replace(
                    typed.declarations[0], initializer=dataclasses.replace(
                        typed.declarations[0].initializer,
                        literal_value=3.0)), *typed.declarations[1:])),
            "tau-f32": dataclasses.replace(
                typed, declarations=(typed.declarations[0], dataclasses.replace(
                    typed.declarations[1], initializer=dataclasses.replace(
                        typed.declarations[1].initializer,
                        literal="6.0")), *typed.declarations[2:])),
            "inv-three-f32": dataclasses.replace(
                typed, declarations=(*typed.declarations[:2], dataclasses.replace(
                    typed.declarations[2], initializer=dataclasses.replace(
                        typed.declarations[2].initializer,
                        literal_value=0.25)), *typed.declarations[3:])),
        }

        def mutate_expression(program, matcher, rewrite):
            matches = 0
            def expression(value):
                nonlocal matches
                children = tuple(expression(child) for child in value.children)
                current = (value if all(left is right for left, right in
                                        zip(children, value.children))
                           else dataclasses.replace(value, children=children))
                if matcher(current):
                    matches += 1
                    return rewrite(current)
                return current
            def statement(value):
                expressions = tuple(expression(item) for item in value.expressions)
                children = tuple(statement(item) for item in value.children)
                if (all(left is right for left, right in
                        zip(expressions, value.expressions))
                        and all(left is right for left, right in
                                zip(children, value.children))):
                    return value
                return dataclasses.replace(value, expressions=expressions,
                                           children=children)
            candidate = dataclasses.replace(program, functions=tuple(
                dataclasses.replace(function, body=tuple(
                    statement(item) for item in function.body))
                for function in program.functions))
            self.assertEqual(1, matches)
            return candidate

        local_source_rewrites = {
            193: lambda value: dataclasses.replace(
                value, children=(dataclasses.replace(
                    value.children[0], symbol_id=9,
                    symbol=typed.declarations[8].symbol),)),
            194: lambda value: dataclasses.replace(
                value, children=(dataclasses.replace(
                    value.children[0], symbol_id=8,
                    symbol=typed.declarations[7].symbol),)),
            205: lambda value: dataclasses.replace(
                value, children=(dataclasses.replace(
                    value.children[0], member="x"),)),
        }
        for symbol_id, label in ((193, "local-time-source"),
                                 (194, "local-speed-source"),
                                 (205, "local-alpha-source")):
            semantic_candidates[label] = mutate_expression(
                typed,
                lambda value, symbol_id=symbol_id:
                    value.kind == "declaration" and value.symbol_id == symbol_id,
                local_source_rewrites[symbol_id])

        semantic_candidates["output-alpha-route"] = mutate_expression(
            typed,
            lambda value: (value.kind == "swizzle" and value.member == "w"
                           and value.span.start_line == 603),
            lambda value: dataclasses.replace(value, member="x"))
        local_alpha_symbols = []
        def collect_local_alpha(value):
            for expression in value.expressions:
                def visit(item):
                    if item.kind == "declaration" and item.symbol_id == 205:
                        local_alpha_symbols.append(item.symbol)
                    for child in item.children: visit(child)
                visit(expression)
            for child in value.children: collect_local_alpha(child)
        for function in typed.functions:
            for statement in function.body: collect_local_alpha(statement)
        self.assertEqual(1, len(local_alpha_symbols))
        semantic_candidates["dead-local-alpha-used"] = mutate_expression(
            typed,
            lambda value: (value.kind == "swizzle" and value.member == "w"
                           and value.span.start_line == 603),
            lambda value: dataclasses.replace(
                value, kind="id", children=(), member=None, symbol_id=205,
                symbol=local_alpha_symbols[0],
                type=typed.declarations[10].type))
        main = next(function for function in typed.functions if function.name == "main")
        fetch_owner = next(function for function in typed.functions
                           if function.id != main.id)
        moved_fetch_statement = main.body[6]
        semantic_candidates["fetch-owner"] = dataclasses.replace(
            typed, functions=tuple(
                dataclasses.replace(
                    function, body=tuple(item for index, item in
                                         enumerate(function.body) if index != 6))
                if function.id == main.id else
                dataclasses.replace(function, body=(*function.body,
                                                     moved_fetch_statement))
                if function.id == fetch_owner.id else function
                for function in typed.functions))
        semantic_candidates["fetch-lod"] = mutate_expression(
            typed,
            lambda value: (value.kind == "builtin" and value.callee == "texelFetch"
                           and value.span.start_line == 475),
            lambda value: dataclasses.replace(
                value, children=(*value.children[:-1], dataclasses.replace(
                    value.children[-1], literal="1", literal_value=1))))

        semantic_candidates["fetch-count"] = dataclasses.replace(
            typed, functions=tuple(
                dataclasses.replace(function, body=(*function.body, function.body[21]))
                if function.id == main.id else function
                for function in typed.functions))
        def fetch_census(program):
            count = 0
            def expression(value):
                nonlocal count
                if value.kind == "builtin" and value.callee == "texelFetch": count += 1
                for child in value.children: expression(child)
            def statement(value):
                for item in value.expressions: expression(item)
                for child in value.children: statement(child)
            for function in program.functions:
                for item in function.body: statement(item)
            return count
        def fetch_owners(program):
            result = {}
            for function in program.functions:
                function_program = dataclasses.replace(program, functions=(function,))
                count = fetch_census(function_program)
                if count: result[function.id] = count
            return result
        self.assertEqual(4, fetch_census(typed))
        self.assertEqual(4, fetch_census(semantic_candidates["fetch-owner"]))
        self.assertEqual({main.id: 4}, fetch_owners(typed))
        self.assertEqual({main.id: 3, fetch_owner.id: 1},
                         fetch_owners(semantic_candidates["fetch-owner"]))
        self.assertEqual(5, fetch_census(semantic_candidates["fetch-count"]))
        semantic_candidates["loop-injected"] = dataclasses.replace(
            typed, functions=tuple(
                dataclasses.replace(function, body=(dataclasses.replace(
                    function.body[0], kind="while"), *function.body[1:]))
                if function.id == main.id else function
                for function in typed.functions))
        for name, candidate in semantic_candidates.items():
            reject_everywhere(name, candidate)

        generic_control = dataclasses.replace(
            semantic_candidates["pi-f32"], key="filter/noncrt:control")
        generate_typed_slice.validate_capabilities(
            generic_control, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash="0" * 64, compatibility_transform=None,
            numeric_literal_contract="glsl-f32")

    def test_task22_adds_only_exact_transform_no_capability_proof_or_numeric_mode(self) -> None:
        import struct
        from tools.glslcpp import generate_typed_slice

        spec = generate_typed_slice.load_slice(REPOSITORY)
        self.assertEqual(tuple(spec["capabilities"]),
                         generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertEqual(tuple(spec["types"]), generate_typed_slice.APPROVED_TYPES)
        self.assertEqual(tuple(spec["binary_operators"]),
                         generate_typed_slice.APPROVED_BINARY_OPERATORS)
        self.assertEqual(tuple(spec["assignment_operators"]),
                         generate_typed_slice.APPROVED_ASSIGNMENT_OPERATORS)
        self.assertEqual({"filter/scatter:scatterJitter": "source-double"},
                         spec["numeric_literal_contracts"])
        self.assertEqual({
            "classicNoisedeck/coalesce:coalesce": "coalesce-uv-alias-v1",
            "classicNoisedeck/refract:refract":
                "refract-truthy-vector-conditional-noop-v1",
            "filter/corrupt:corrupt": "corrupt-sample-uv-alias-v1",
            "filter/crt:crt": "crt-metal-sine-v1",
            "mixer/shapeMask:shapeMask": "shape-mask-sequential-lanes-v1",
            "synth/polygon:shape": "polygon-zero-smoothing-v1",
            "synth/sacredGeometry:sacredGeometry":
                "sacred-star-number-division-v1",
        }, spec["compatibility_transforms"])
        self.assertEqual("canonicalFactory44",
                         generate_typed_slice.CRT_CANONICAL_FACTORY)
        self.assertEqual(
            "6d65f4984f8749ca7cdfec976e082662d3a7ad614aabb15ce8a168fca7d8e303",
            generate_typed_slice.CRT_CANONICAL_FACTORY_TEXT_SHA256)
        self.assertEqual("crtFactory", generate_typed_slice.CRT_PUBLIC_FACTORY)
        self.assertEqual(
            "240972f95f908452bf87fc681e360553759f374fa81613adc415a5a7c5eb4bf7",
            generate_typed_slice.CRT_PUBLIC_FACTORY_TEXT_SHA256)
        self.assertEqual(
            "c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc",
            generate_typed_slice.CRT_PUBLIC_ADAPTER_SHA256)
        self.assertEqual(
            "e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56",
            generate_typed_slice.CRT_CANONICAL_RUNTIME_SHA256)
        inv_tau = 0.15915493667125702
        self.assertEqual(0x3E22F983, generate_typed_slice.CRT_INV_TAU_F32_BITS)
        self.assertEqual(generate_typed_slice.CRT_INV_TAU_F32_BITS,
                         struct.unpack("<I", struct.pack("<f", inv_tau))[0])
        generated = generate_typed_slice.generate_outputs(REPOSITORY)[
            "src/typed_generated/typed_slice.cpp"].decode()
        start = generated.index("// Typed IR program: filter/crt:crt")
        end = generated.index("// Typed IR program: filter/degauss:degauss", start)
        crt = generated[start:end]
        self.assertEqual(12, crt.count("static_cast<float>(0.15915493667125702)"))
        self.assertEqual(6, crt.count("static_cast<float>(6.2831854820251465)"))
        self.assertEqual(6, crt.count("glsl::sin("))

    # NOT a historical reconstruction; see the note on
    # test_task21_degauss_exclusions_remain_closed. The narrow exclusion set
    # leaves later-added programs present in the 127-key list.
    def test_task22_crt_exclusions_remain_closed(self) -> None:
        import copy
        import hashlib
        import re
        from unittest import mock
        from tools.glslcpp import check_corpus, generate_typed_slice

        spec = generate_typed_slice.load_slice(REPOSITORY)
        typed = [item["program_key"] for item in spec["programs"]
                 if item["program_key"] not in {
                     "filter/rotate:rot", "mixer/focusBlur:focusBlur",
                     "filter/extrude:extrude", "synth/curl:curl",
                     "filter/grade:creative", "filter/grade:hslSecondary",
                     "filter/grade:lut", "filter/grade:primary",
                     "filter/grade:vignette", "filter/grade:wheels"}]
        public = sorted((*typed, "filter/invert:inv", "synth/solid:solid"))
        self.assertEqual(127, len(typed))
        self.assertEqual(typed, sorted(set(typed)))
        self.assertEqual(("filter/craquelure:craquelure", "filter/crt:crt",
                          "filter/degauss:degauss", "filter/deriv:deriv"),
                         tuple(typed[typed.index("filter/crt:crt") - 1:
                                     typed.index("filter/crt:crt") + 3]))
        self.assertEqual(
            "ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72",
            hashlib.sha256(("\n".join(typed) + "\n").encode()).hexdigest())
        self.assertEqual(
            "37e41894bc62b658a3454e13ab60fe814baf2492fa2a74b0f4305e05480a7883",
            hashlib.sha256(("\n".join(public) + "\n").encode()).hexdigest())
        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())
        remaining = sorted({item["program_key"] for item in manifest["programs"]}
                           - set(public))
        self.assertEqual((127, 129, 83, 212),
                         (len(typed), len(public), len(remaining),
                          len(manifest["programs"])))
        self.assertEqual(1, typed.count("filter/crt:crt"))
        self.assertEqual(1, typed.count("filter/degauss:degauss"))

        original_slice = json.loads(
            (REPOSITORY / "tools/glslcpp/typed_slice.json").read_text())
        slice_mutations = {}
        changed = copy.deepcopy(original_slice); changed["schema"] = 2
        slice_mutations["schema"] = changed
        changed = copy.deepcopy(original_slice)
        changed["programs"].append(copy.deepcopy(next(
            item for item in changed["programs"]
            if item["program_key"] == "filter/crt:crt")))
        changed["programs"].sort(key=lambda item: item["program_key"])
        slice_mutations["duplicate-crt"] = changed
        changed = copy.deepcopy(original_slice)
        changed["programs"].append({"program_key": "filter/zzz:zzz", "defines": {}})
        changed["programs"].sort(key=lambda item: item["program_key"])
        slice_mutations["admitted-key"] = changed
        changed = copy.deepcopy(original_slice)
        changed["compatibility_transforms"]["filter/crt:crt"] = "wrong"
        slice_mutations["wrong-crt-transform"] = changed
        changed = copy.deepcopy(original_slice)
        changed["compatibility_transforms"]["filter/zzz:zzz"] = "crt-metal-sine-v1"
        slice_mutations["foreign-extra-transform"] = changed
        changed = copy.deepcopy(original_slice)
        changed["programs"][0] = {"program_key": changed["programs"][0]["program_key"]}
        slice_mutations["program-shape"] = changed
        for name, changed in slice_mutations.items():
            with self.subTest(slice_mutation=name), tempfile.TemporaryDirectory() as temporary:
                repository = pathlib.Path(temporary)
                path = repository / "tools/glslcpp/typed_slice.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(changed))
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.load_slice(repository)

        authentic_outputs = generate_typed_slice.generate_outputs(REPOSITORY)
        authentic_manifest = json.loads(authentic_outputs[
            "src/typed_generated/typed_manifest.json"].decode())
        crt_index = next(index for index, item in enumerate(
            authentic_manifest["programs"])
            if item["program_key"] == "filter/crt:crt")
        for name, rewrite in {
                "carrier-cleared": lambda item: item.update(
                    compatibility_transform="none"),
                "carrier-stale": lambda item: item.update(
                    compatibility_transform="wrong"),
                "numeric": lambda item: item.update(
                    numeric_literal_contract="source-double"),
                "key": lambda item: item.update(program_key="filter/zzz:zzz"),
                "source-hash": lambda item: item.update(source_sha256="0" * 64),
                "duplicate": lambda item: authentic_manifest["programs"].append(
                    copy.deepcopy(item)),
        }.items():
            manifest_mutation = copy.deepcopy(authentic_manifest)
            item = manifest_mutation["programs"][crt_index]
            if name == "duplicate":
                manifest_mutation["programs"].append(copy.deepcopy(item))
            else:
                rewrite(item)
            mutated_outputs = dict(authentic_outputs)
            mutated_outputs["src/typed_generated/typed_manifest.json"] = (
                json.dumps(manifest_mutation, sort_keys=True, indent=2) + "\n").encode()
            with self.subTest(manifest_mutation=name), tempfile.TemporaryDirectory() as temporary:
                repository = pathlib.Path(temporary)
                for relative, content in authentic_outputs.items():
                    target = repository / pathlib.PurePosixPath(relative)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                with mock.patch.object(generate_typed_slice, "generate_outputs",
                                       return_value=authentic_outputs):
                    generate_typed_slice.check_outputs(repository)
                    manifest_target = (repository /
                        "src/typed_generated/typed_manifest.json")
                    manifest_target.write_bytes(mutated_outputs[
                        "src/typed_generated/typed_manifest.json"])
                    with self.assertRaisesRegex(
                            generate_typed_slice.GeneratorError,
                            "typed generated output drift"):
                        generate_typed_slice.check_outputs(repository)

        task22_spec = copy.deepcopy(spec)
        task23_keys = (
            "filter/bloom:ntapGather",
            "filter/directionalBlur:directionalBlur",
            "filter/spinBlur:spinBlur",
            "filter/strokes:stkSmear",
            "filter/vaseline:upsample",
            "filter/wind:wind",
        )
        self.assertEqual(frozenset(task23_keys),
                         generate_typed_slice.SOURCE_GLOBAL_LITERAL_INT_KEYS)
        post_task22_keys = frozenset((
            *task23_keys,
            "filter/pixelSort:gatherSorted",
            "classicNoisedeck/lensDistortion:lensDistortion",
            "filter/prismaticAberration:prismaticAberration",
            "filter/smooth:smoothEdge",
            "synth/perlin:perlin",
            "filter/rotate:rot",
            "mixer/focusBlur:focusBlur",
            "filter/extrude:extrude",
            "synth/curl:curl",
        ))
        task22_spec["programs"] = [
            item for item in task22_spec["programs"]
            if item["program_key"] not in post_task22_keys]
        self.assertEqual(1, task22_spec["capabilities"].count(
            "source-global-literal-int-v1"))
        task22_spec["capabilities"].remove("source-global-literal-int-v1")
        task22_keys = [item["program_key"] for item in task22_spec["programs"]]
        task22_public = sorted((*task22_keys, "filter/invert:inv",
                                "synth/solid:solid"))
        task22_unported = sorted(
            {item["program_key"] for item in manifest["programs"]}
            - set(task22_public))
        self.assertEqual((116, 118, 94, 212),
                         (len(task22_keys), len(task22_public),
                          len(task22_unported), len(manifest["programs"])))
        self.assertEqual(
            "76c81945ef992ed258900815335a23ae4f36d8756b7763ebd5e03d8562fde8e3",
            hashlib.sha256(("\n".join(task22_keys) + "\n").encode()).hexdigest())
        self.assertEqual(
            "019a80df52192e3c898af58a5e3a2a9da654896eadde78097ce4a818579328f9",
            hashlib.sha256(("\n".join(task22_public) + "\n").encode()).hexdigest())
        self.assertEqual((19, 20),
                         (task22_keys.index("filter/crt:crt"),
                          task22_keys.index("filter/degauss:degauss")))
        self.assertNotIn("source-global-literal-int-v1",
                         task22_spec["capabilities"])
        current_validate_capabilities = generate_typed_slice.validate_capabilities
        def validate_historical_task22(typed_program, _declared, **kwargs):
            return current_validate_capabilities(
                typed_program, generate_typed_slice.APPROVED_CAPABILITIES,
                **kwargs)
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=task22_spec), \
                mock.patch.object(generate_typed_slice, "validate_capabilities",
                                  side_effect=validate_historical_task22):
            current_cpp = generate_typed_slice.generate_outputs(REPOSITORY)[
                "src/typed_generated/typed_slice.cpp"].decode()
        prior_spec = copy.deepcopy(task22_spec)
        prior_spec["programs"] = [
            item for item in prior_spec["programs"]
            if item["program_key"] != "filter/crt:crt"]
        prior_spec["compatibility_transforms"].pop("filter/crt:crt")
        self.assertEqual(115, len(prior_spec["programs"]))
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=prior_spec), \
                mock.patch.object(generate_typed_slice, "validate_capabilities",
                                  side_effect=validate_historical_task22):
            prior_cpp = generate_typed_slice.generate_outputs(REPOSITORY)[
                "src/typed_generated/typed_slice.cpp"].decode()
        self.assertEqual(
            "a3f8135d41e9f2abc864fada60532309b56c43f6e6eb138d548a23b57f944c4f",
            hashlib.sha256(current_cpp.encode()).hexdigest())
        self.assertEqual(
            "986d6d3116497282e468440a6786be5728ee53f0558ea8c5a553831e353aa5ba",
            hashlib.sha256(prior_cpp.encode()).hexdigest())

        marker = re.compile(r"(?m)^// Typed IR program: (.+)$")
        def blocks(text):
            hits = list(marker.finditer(text))
            result = {}
            for index, hit in enumerate(hits):
                end = (hits[index + 1].start() if index + 1 < len(hits)
                       else text.index("\nnamespace {", hit.end()))
                result[hit.group(1)] = text[hit.start():end]
            return result

        before = blocks(prior_cpp)
        after = blocks(current_cpp)
        self.assertEqual(115, len(before))
        self.assertEqual(116, len(after))
        self.assertEqual(set(before), set(after) - {"filter/crt:crt"})
        pre_crt = [key for key in before if key < "filter/crt:crt"]
        self.assertEqual(19, len(pre_crt))
        for key in sorted(before):
            with self.subTest(generated_isolation=key):
                if key < "filter/crt:crt":
                    self.assertEqual(before[key], after[key])
                normalize = lambda value: re.sub(
                    r"typed_[0-9]+", "typed_SENTINEL", value)
                self.assertEqual(normalize(before[key]), normalize(after[key]))

        crt = after["filter/crt:crt"][:-1]
        self.assertEqual(56865, len(crt.encode()))
        self.assertEqual(
            "c2cad7e88fb817c311abb0041fec98d14c28ae3c3bd731b67944c745b8c295ec",
            hashlib.sha256(crt.encode()).hexdigest())
        normalized_crt = re.sub(r"typed_[0-9]+", "typed_SENTINEL", crt)
        self.assertEqual(
            "36410c4f25e2a0d53bba3bdc7164c18f74cc7f06de8f7589186da182b7246922",
            hashlib.sha256(normalized_crt.encode()).hexdigest())

    def test_task25_slice_counts_lists_positions_and_generated_isolation_are_exact(self) -> None:
        import copy
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import (
            LENS_KEY, PRISMATIC_KEY, PROFILE)

        expected_typed = tuple("""\
classicNoisedeck/coalesce:coalesce
classicNoisedeck/composite:composite
classicNoisedeck/lensDistortion:lensDistortion
classicNoisedeck/refract:refract
classicNoisedeck/splat:splat
filter/bc:bc
filter/bloom:brightPass
filter/bloom:composite
filter/bloom:ntapGather
filter/celShading:celShadingBlend
filter/celShading:celShadingEdges
filter/channel:channel
filter/chroma:chroma
filter/chromaticAberration:chromaticAberration
filter/chrome:chBlurH
filter/chrome:chBlurV
filter/chrome:chMap
filter/clouds:clouds
filter/colorReplace:colorReplace
filter/corrupt:corrupt
filter/craquelure:craquelure
filter/crt:crt
filter/degauss:degauss
filter/deriv:deriv
filter/directionalBlur:directionalBlur
filter/fibers:fibersBlend
filter/flipMirror:flipMirror
filter/glowingEdge:glowingEdge
filter/hatch:hatch
filter/highPass:hpBlurH
filter/highPass:hpBlurV
filter/highPass:hpCombine
filter/hs:hs
filter/lensFlare:lensFlare
filter/lowPoly:lowPoly
filter/morphology:morphA
filter/morphology:morphB
filter/mosaicTiles:mosaicTiles
filter/normalize:apply
filter/normalize:reduce
filter/normalize:reduceMinmax
filter/oilPaint:oilPost
filter/outline:outlineBlend
filter/outline:outlineSobel
filter/outline:outlineValueMap
filter/patchwork:patchwork
filter/photocopy:pcBlurH
filter/photocopy:pcBlurV
filter/photocopy:pcCombine
filter/pixelSort:computeRank
filter/pixelSort:finalize
filter/pixelSort:findBrightest
filter/pixelSort:gatherSorted
filter/pixelSort:luminance
filter/pixelSort:prepare
filter/pixels:pixels
filter/plasticWrap:pwBlurH
filter/plasticWrap:pwBlurV
filter/plasticWrap:pwSpec
filter/prismaticAberration:prismaticAberration
filter/reindex:nmReindexApply
filter/relief:rlBlurH
filter/relief:rlBlurV
filter/relief:rlShade
filter/repeat:repeat
filter/reverb:reverb
filter/ridge:ridge
filter/scale:scale
filter/scatter:scatterJitter
filter/scatter:scatterSmooth
filter/scratches:scratchesBlend
filter/scroll:scroll
filter/seamless:seamless
filter/sharpen:sharpen
filter/simpleAberration:chromaticAberration
filter/sine:sine
filter/skew:skew
filter/smoothstep:smoothstep
filter/sobel:sobel
filter/spatter:spatter
filter/spinBlur:spinBlur
filter/stamp:stBlurH
filter/stamp:stBlurV
filter/strayHair:strayHairBlend
filter/strokes:stkPost
filter/strokes:stkSmear
filter/tetraCosine:tetraCosine
filter/text:text
filter/threshold:thresh
filter/tile:tile
filter/tint:colorize
filter/translate:translate
filter/unsharpMask:usmBlurH
filter/unsharpMask:usmBlurV
filter/unsharpMask:usmCombine
filter/vaseline:upsample
filter/vignette:vignette
filter/watercolor:wcComposite
filter/watercolor:wcSeed
filter/wind:wind
filter/wormhole:blend
filter/wormhole:clear
mixer/alphaMask:alphaMask
mixer/applyMode:applyMode
mixer/blendMode:blendMode
mixer/cellSplit:cellSplit
mixer/centerMask:centerMask
mixer/channelCombine:channelCombine
mixer/mashup:mashup
mixer/patternMix:patternMix
mixer/shadow:shadow
mixer/shapeMask:shapeMask
mixer/split:split
mixer/thresholdMix:thresholdMix
mixer/uvRemap:uvRemap
synth/cell:cell
synth/gradient:gradient
synth/mandala:mandala
synth/media:mediaInput
synth/modPattern:modPattern
synth/osc2d:osc2d
synth/pattern:pattern
synth/polygon:shape
synth/sacredGeometry:sacredGeometry
synth/subdivide:subdivide""".splitlines())
        expected_public = tuple(sorted((
            *expected_typed, "filter/invert:inv", "synth/solid:solid")))

        spec = generate_typed_slice.load_slice(REPOSITORY)
        spec = copy.deepcopy(spec)
        spec["programs"] = [
            item for item in spec["programs"]
            if item["program_key"] not in {
                "filter/smooth:smoothEdge", "synth/perlin:perlin",
                "filter/rotate:rot", "mixer/focusBlur:focusBlur",
                "filter/extrude:extrude", "synth/curl:curl",
                "filter/grade:creative", "filter/grade:hslSecondary",
                "filter/grade:lut", "filter/grade:primary",
                "filter/grade:vignette", "filter/grade:wheels"}]
        typed = tuple(item["program_key"] for item in spec["programs"])
        self.assertEqual(expected_typed, typed)
        self.assertEqual(125, len(typed))
        self.assertEqual(
            "9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4",
            hashlib.sha256(("\n".join(typed) + "\n").encode()).hexdigest())
        self.assertEqual((2, 52, 59), (
            typed.index(LENS_KEY), typed.index("filter/pixelSort:gatherSorted"),
            typed.index(PRISMATIC_KEY)))
        self.assertEqual((
            "classicNoisedeck/composite:composite", LENS_KEY,
            "classicNoisedeck/refract:refract"), typed[1:4])
        self.assertEqual((
            "filter/pixelSort:findBrightest", "filter/pixelSort:gatherSorted",
            "filter/pixelSort:luminance"), typed[51:54])
        self.assertEqual((
            "filter/plasticWrap:pwSpec", PRISMATIC_KEY,
            "filter/reindex:nmReindexApply"), typed[58:61])

        carriers = tuple(
            (item["program_key"], item.get("literal_vec3_lane_index_profile"),
             item["defines"])
            for item in spec["programs"]
            if "literal_vec3_lane_index_profile" in item)
        self.assertEqual(((LENS_KEY, PROFILE, {}),
                          (PRISMATIC_KEY, PROFILE, {})), carriers)

        corpus = json.loads((check_corpus._corpus_root(REPOSITORY) /
                             "manifest.json").read_text())
        public = expected_public
        unported = tuple(sorted(
            {item["program_key"] for item in corpus["programs"]} - set(public)))
        self.assertEqual((125, 127, 85, 212),
                         (len(typed), len(public), len(unported),
                          len(corpus["programs"])))
        self.assertEqual(
            "9d773dde79594d81d54b2d4cd1cab8b8929201eaa01ef276db38530c39edeaab",
            hashlib.sha256(("\n".join(public) + "\n").encode()).hexdigest())
        self.assertIn("filter/grade:lut", unported)
        self.assertIn("filter/posterize:posterize", unported)

        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=spec):
            current = generate_typed_slice.generate_outputs(REPOSITORY)
        current["include/noisemaker/generated/catalog.hpp"] = (
            generate_typed_slice.render_catalog_header(spec))
        prior_spec = copy.deepcopy(spec)
        prior_spec["programs"] = [
            item for item in prior_spec["programs"]
            if item["program_key"] not in (LENS_KEY, PRISMATIC_KEY)]
        prior_keys = tuple(item["program_key"] for item in prior_spec["programs"])
        self.assertEqual(123, len(prior_keys))
        self.assertEqual(
            "df7750a48a77733e50f0e20072e291c2404e761932f6df8ddbcf8793d58fb6ac",
            hashlib.sha256(("\n".join(prior_keys) + "\n").encode()).hexdigest())
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=prior_spec):
            prior = generate_typed_slice.generate_outputs(REPOSITORY)
        prior["include/noisemaker/generated/catalog.hpp"] = (
            generate_typed_slice.render_catalog_header(prior_spec))

        marker = re.compile(r"(?m)^// Typed IR program: ([^\n]+)\n")
        def blocks(payload):
            source = payload.decode()
            starts = list(marker.finditer(source))
            catalog = source.index(
                "\nnamespace {\nconstexpr std::array<KernelFactory")
            return {
                match.group(1): source[
                    match.start():(starts[index + 1].start()
                                   if index + 1 < len(starts) else catalog)]
                for index, match in enumerate(starts)
            }

        prior_blocks = blocks(prior["src/typed_generated/typed_slice.cpp"])
        current_blocks = blocks(current["src/typed_generated/typed_slice.cpp"])
        self.assertEqual(123, len(prior_blocks))
        self.assertEqual(125, len(current_blocks))
        self.assertEqual({LENS_KEY, PRISMATIC_KEY},
                         set(current_blocks) - set(prior_blocks))
        self.assertIn("namespace typed_2 {", current_blocks[LENS_KEY])
        self.assertIn("namespace typed_59 {", current_blocks[PRISMATIC_KEY])
        self.assertIn("namespace typed_52 {",
                      current_blocks["filter/pixelSort:gatherSorted"])
        self.assertIn("namespace typed_51 {",
                      prior_blocks["filter/pixelSort:gatherSorted"])
        ordinal = re.compile(r"typed_[0-9]+")
        for key, prior_block in prior_blocks.items():
            with self.subTest(task24_block=key):
                self.assertEqual(
                    ordinal.sub("typed_SENTINEL", prior_block),
                    ordinal.sub("typed_SENTINEL", current_blocks[key]))

        projections = {
            LENS_KEY: (27519,
                       "a516c15ef5eee1c0e16766f4104e4397b01293fc2a39df75154a029f3c312dc6"),
            PRISMATIC_KEY: (13316,
                            "8d6c98fed4ab2d2a2130566081386cdfb74d01ae84c11b198a1be08ae187155f"),
        }
        for key, expected in projections.items():
            projected = ordinal.sub("typed_projection", current_blocks[key][:-1])
            self.assertEqual(expected, (
                len(projected.encode()), hashlib.sha256(projected.encode()).hexdigest()))

        prior_manifest = json.loads(
            prior["src/typed_generated/typed_manifest.json"])
        current_manifest = json.loads(
            current["src/typed_generated/typed_manifest.json"])
        prior_rows = {item["program_key"]: item
                      for item in prior_manifest["programs"]}
        current_rows = {item["program_key"]: item
                        for item in current_manifest["programs"]}
        self.assertEqual({LENS_KEY, PRISMATIC_KEY},
                         set(current_rows) - set(prior_rows))
        for key, row in prior_rows.items():
            self.assertEqual(
                {name: value for name, value in row.items()
                 if name != "output_sha256"},
                {name: value for name, value in current_rows[key].items()
                 if name != "output_sha256"}, key)
        expected_manifest_rows = {
            LENS_KEY: {
                "capabilities": list(generate_typed_slice.APPROVED_CAPABILITIES),
                "compatibility_transform": "none", "define_contract": "none",
                "custom_comparer_profile":
                    "canonical-js-vector-equality-result-truthiness-v1",
                "defines": {},
                "factory": "bind_classicNoisedeck_lensDistortion_lensDistortion",
                "numeric_literal_contract": "glsl-f32", "output": "typed_slice.cpp",
                "program_key": LENS_KEY,
                "source": "sources/classicNoisedeck/lensDistortion/lensDistortion.glsl",
                "source_sha256":
                    "f4e6453fe233692fa67c5fdbb3eb8f7a512d21bc722e63af6fc23166a62dd444",
            },
            PRISMATIC_KEY: {
                "capabilities": list(generate_typed_slice.APPROVED_CAPABILITIES),
                "compatibility_transform": "none", "define_contract": "none",
                "defines": {},
                "factory": "bind_filter_prismaticAberration_prismaticAberration",
                "numeric_literal_contract": "glsl-f32", "output": "typed_slice.cpp",
                "program_key": PRISMATIC_KEY,
                "source": "sources/filter/prismaticAberration/prismaticAberration.glsl",
                "source_sha256":
                    "513eac95fdf7f67a6839ee5d96e5bbfd76b6cfa62d3254df6fed23d8effe380e",
            },
        }
        for key, expected in expected_manifest_rows.items():
            self.assertEqual(expected, {
                name: value for name, value in current_rows[key].items()
                if name != "output_sha256"})

        current_header = current[
            "include/noisemaker/generated/catalog.hpp"].decode()
        prior_header = prior[
            "include/noisemaker/generated/catalog.hpp"].decode()
        declarations = (
            "[[nodiscard]] BoundKernel "
            "bind_classicNoisedeck_lensDistortion_lensDistortion("
            "const glsl::Bindings& bindings);\n",
            "[[nodiscard]] BoundKernel "
            "bind_filter_prismaticAberration_prismaticAberration("
            "const glsl::Bindings& bindings);\n",
        )
        for declaration in declarations:
            self.assertEqual(1, current_header.count(declaration))
            current_header = current_header.replace(declaration, "")
        self.assertEqual(prior_header, current_header)

        current_cpp = current["src/typed_generated/typed_slice.cpp"].decode()
        prior_cpp = prior["src/typed_generated/typed_slice.cpp"].decode()
        current_catalog = re.findall(
            r'(?m)^    \{"([^"]+)", &([^}]+)\},$', current_cpp)
        prior_catalog = re.findall(
            r'(?m)^    \{"([^"]+)", &([^}]+)\},$', prior_cpp)
        self.assertEqual(list(public), [key for key, _ in current_catalog])
        self.assertEqual({
            (LENS_KEY, "bind_classicNoisedeck_lensDistortion_lensDistortion"),
            (PRISMATIC_KEY,
             "bind_filter_prismaticAberration_prismaticAberration"),
        }, set(current_catalog) - set(prior_catalog))
        self.assertEqual(
            "55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6",
            hashlib.sha256((REPOSITORY / "tests/test_typed_slice.cpp").read_bytes()
                           ).hexdigest())

    def test_task25_loader_rejects_transitional_task24_no_carrier_slice(self) -> None:
        import copy
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import KEYS

        task24 = copy.deepcopy(json.loads(
            (REPOSITORY / "tools/glslcpp/typed_slice.json").read_text()))
        task24["programs"] = [item for item in task24["programs"]
                              if item["program_key"] not in KEYS
                              and item["program_key"] != "filter/smooth:smoothEdge"
                              and item["program_key"] != "synth/perlin:perlin"
                              and item["program_key"] != "filter/rotate:rot"
                              and item["program_key"] != "mixer/focusBlur:focusBlur"
                              and item["program_key"] != "filter/extrude:extrude"
                              and item["program_key"] != "synth/curl:curl"]
        self.assertEqual(123, len(task24["programs"]))
        self.assertFalse(any("literal_vec3_lane_index_profile" in item
                             for item in task24["programs"]))
        with tempfile.TemporaryDirectory() as temporary:
            repository = pathlib.Path(temporary)
            path = repository / "tools/glslcpp/typed_slice.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(task24))
            with self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    "typed slice literal vec3 lane profile drift"):
                generate_typed_slice.load_slice(repository)

    def test_task25_lens_custom_comparer_profile_is_admitted_with_lane_profile(self) -> None:
        import copy
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import (
            LENS_KEY, PROFILE as LANE_PROFILE)

        comparer_profile = "canonical-js-vector-equality-result-truthiness-v1"
        planned = copy.deepcopy(json.loads(
            (REPOSITORY / "tools/glslcpp/typed_slice.json").read_text()))
        planned["custom_comparer_profiles"] = {LENS_KEY: comparer_profile}
        lens = next(item for item in planned["programs"]
                    if item["program_key"] == LENS_KEY)
        self.assertEqual(LANE_PROFILE, lens["literal_vec3_lane_index_profile"])

        with tempfile.TemporaryDirectory() as temporary:
            repository = pathlib.Path(temporary)
            path = repository / "tools/glslcpp/typed_slice.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(planned))
            try:
                loaded = generate_typed_slice.load_slice(repository)
            except generate_typed_slice.GeneratorError as error:
                self.fail(f"exact Lens custom comparer profile was rejected: {error}")
        self.assertEqual({LENS_KEY: comparer_profile},
                         loaded["custom_comparer_profiles"])

    def test_task25_lens_custom_comparer_routes_only_the_tint_predicate(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import LENS_KEY

        cpp = generate_typed_slice.generate_outputs(REPOSITORY)[
            "src/typed_generated/typed_slice.cpp"].decode()
        marker = f"// Typed IR program: {LENS_KEY}\n"
        start = cpp.index(marker)
        end = cpp.index("// Typed IR program:", start + len(marker))
        lens = cpp[start:end]
        comparer = "glsl::canonical_js_vector_equality_result_is_truthy("

        self.assertEqual(1, lens.count(comparer))
        self.assertEqual(1, cpp.count(comparer))
        expected = (
            "  glsl::set_swizzle<0, 1, 2>(color, glsl::mix("
            "glsl::swizzle<0, 1, 2>(color), "
            "(glsl::canonical_js_vector_equality_result_is_truthy("
            "glsl::Vec3(glsl::swizzle<0, 1, 2>(color)), "
            "glsl::Vec3(glsl::FloatExpr<3>(static_cast<float>(1.0)))) ? "
            "glsl::Vec3(glsl::swizzle<0, 1, 2>(color)) : "
            "glsl::Vec3(glsl::component_min(((state.tint * state.tint) / "
            "(static_cast<float>(1.0) - glsl::swizzle<0, 1, 2>(color))), "
            "glsl::FloatExpr<3>(static_cast<float>(1.0))))), "
            "(static_cast<double>(state.alpha) * "
            "static_cast<double>(static_cast<float>(0.01)))));"
        )
        self.assertEqual(1, lens.splitlines().count(expected))
        self.assertNotIn(
            "(glsl::swizzle<0, 1, 2>(color) == "
            "glsl::FloatExpr<3>(static_cast<float>(1.0)))", lens)

    def test_task25_lens_custom_comparer_profile_rejects_structural_mutations(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend import lens_distortion_comparer_profile as comparer
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import (
            PROFILE as LANE_PROFILE, apply_literal_vec3_lane_index)
        from tools.glslcpp.frontend.semantic import analyze_program

        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == comparer.LENS_KEY)
        pre = analyze_program(parse_program(
            (corpus / entry["source"]).read_text(), comparer.LENS_KEY, {}),
            comparer.LENS_KEY)
        final = apply_literal_vec3_lane_index(
            pre, entry["raw_sha256"], LANE_PROFILE)
        pre_predicate = comparer.authenticate_lens_custom_comparer_pre(
            pre, entry["raw_sha256"], comparer.PROFILE)
        final_predicate = comparer.authenticate_lens_custom_comparer_final(
            final, entry["raw_sha256"], comparer.PROFILE)
        self.assertIs(pre_predicate, final_predicate)
        self.assertEqual(273, comparer.RAW_SOURCE_LINE)
        self.assertEqual((21, "e0", 0, 1, 1), comparer.SITE_PATH)
        self.assertEqual(comparer.PROFILE_SHA256,
                         comparer._sha(comparer._profile_tuple()))

        for authenticator, candidate in (
                (comparer.authenticate_lens_custom_comparer_pre, pre),
                (comparer.authenticate_lens_custom_comparer_final, final)):
            for carrier, caller_hash in (
                    (None, entry["raw_sha256"]),
                    ("wrong", entry["raw_sha256"]),
                    (comparer.PROFILE, None),
                    (comparer.PROFILE, "0" * 64)):
                with self.subTest(stage=authenticator.__name__, carrier=carrier,
                                  caller_hash=caller_hash), self.assertRaises(ValueError):
                    authenticator(candidate, caller_hash, carrier)

        with self.assertRaises(ValueError):
            comparer.authenticate_lens_custom_comparer_pre(
                final, entry["raw_sha256"], comparer.PROFILE)
        with self.assertRaises(ValueError):
            comparer.authenticate_lens_custom_comparer_final(
                pre, entry["raw_sha256"], comparer.PROFILE)

        main = next(function for function in pre.functions
                    if function.name == "main")
        assignment, mix, site = comparer._site_at(main)
        predicate = site.children[0]

        def replace_expression(program, target, replacement):
            matches = 0
            def expression(value):
                nonlocal matches
                if value is target:
                    matches += 1
                    return replacement(value)
                children = tuple(expression(child) for child in value.children)
                return (value if all(child is original for child, original
                                     in zip(children, value.children))
                        else dataclasses.replace(value, children=children))
            def statement(value):
                expressions = tuple(expression(item) for item in value.expressions)
                children = tuple(statement(item) for item in value.children)
                return (value if (all(item is original for item, original
                                      in zip(expressions, value.expressions))
                                  and all(child is original for child, original
                                          in zip(children, value.children)))
                        else dataclasses.replace(
                            value, expressions=expressions, children=children))
            changed = dataclasses.replace(program, functions=tuple(
                dataclasses.replace(function, body=tuple(
                    statement(item) for item in function.body))
                if function is main else function
                for function in program.functions))
            self.assertEqual(1, matches)
            return changed

        other_conditional = next(
            value for statement in main.body
            for value in comparer._walk_statement(statement)
            if value.kind == "conditional" and value is not site)
        mutations = {
            "key": dataclasses.replace(pre, key=pre.key + "-forged"),
            "raw-source": dataclasses.replace(pre, raw_source=pre.raw_source + "\n"),
            "normalized-source": dataclasses.replace(pre, source=pre.source + "\n"),
            "main-body": dataclasses.replace(pre, functions=tuple(
                dataclasses.replace(function, body=function.body[:-1])
                if function is main else function for function in pre.functions)),
            "assignment": replace_expression(
                pre, assignment,
                lambda value: dataclasses.replace(value, operator="+=")),
            "mix": replace_expression(
                pre, mix, lambda value: dataclasses.replace(value, callee="min")),
            "site-span": replace_expression(
                pre, site, lambda value: dataclasses.replace(
                    value, span=dataclasses.replace(
                        value.span, start_column=value.span.start_column + 1))),
            "predicate": replace_expression(
                pre, predicate,
                lambda value: dataclasses.replace(value, operator="!=")),
            "operands": replace_expression(
                pre, predicate,
                lambda value: dataclasses.replace(
                    value, children=(value.children[1], value.children[0]))),
            "true-arm": replace_expression(
                pre, site, lambda value: dataclasses.replace(
                    value, children=(value.children[0], value.children[2],
                                     value.children[2]))),
            "false-arm": replace_expression(
                pre, site, lambda value: dataclasses.replace(
                    value, children=(value.children[0], value.children[1],
                                     value.children[1]))),
            "site-missing": replace_expression(
                pre, site, lambda value: value.children[1]),
            "site-extra": replace_expression(
                pre, other_conditional, lambda value: dataclasses.replace(
                    value, children=(predicate, *value.children[1:]))),
        }
        for name, candidate in mutations.items():
            with self.subTest(mutation=name), self.assertRaises(ValueError):
                comparer.authenticate_lens_custom_comparer_pre(
                    candidate, entry["raw_sha256"], comparer.PROFILE)

        with mock.patch.object(comparer, "PROFILE_SHA256", "0" * 64), \
                self.assertRaisesRegex(ValueError, "internal frozen profile tuple"):
            comparer.authenticate_lens_custom_comparer_pre(
                pre, entry["raw_sha256"], comparer.PROFILE)

    def test_task25_literal_vec3_lane_profile_authenticates_and_rewrites_exact_sites(self) -> None:
        import dataclasses
        from collections import Counter
        from tools.glslcpp import check_corpus
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend import literal_vec3_lane_index_profile as profile_module
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import (
            KEYS, LENS_KEY, PRISMATIC_KEY, PROFILE,
            apply_literal_vec3_lane_index,
            authenticate_literal_vec3_lane_index_post,
            authenticate_literal_vec3_lane_index_pre,
            authenticate_literal_vec3_lane_index_transition)
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entries = {
            item["program_key"]: item for item in manifest["programs"]
            if item["program_key"] in KEYS
        }
        self.assertEqual(set(KEYS), set(entries))

        typed = {}
        for key in KEYS:
            entry = entries[key]
            raw = (root / entry["source"]).read_text()
            typed[key] = analyze_program(parse_program(raw, key, {}), key)

        self.assertEqual((LENS_KEY, PRISMATIC_KEY), KEYS)
        expected_paths = {
            LENS_KEY: (
                (18, "s0", "s3", "e0", 0, 0),
                (18, "s0", "s3", "e0", 0, 1, 0, 0, 0, 0),
                (18, "s0", "s3", "e0", 0, 1, 0, 0, 1, 0, 0),
                (18, "s0", "s4", "e0", 0, 0),
                (18, "s1", "s3", "e0", 0, 0),
                (18, "s1", "s3", "e0", 0, 1, 0, 0, 0, 0, 0),
                (18, "s1", "s4", "e0", 0, 0),
                (20, "s1", "s0", "s0", "e0", 0, 1, 0, 0, 0, 1, 0),
            ),
            PRISMATIC_KEY: (
                (26, "e0", 0, 0),
                (26, "e0", 0, 1, 0, 0, 0, 0, 0),
                (27, "e0", 0, 0),
            ),
        }
        profile_hashes = {
            LENS_KEY: "d1235bb6045a5795c4c10c5db8a990f51ee42e5541dcfa7a663c91f3245d10d3",
            PRISMATIC_KEY: "25ad8a580a8263b4d2d15b41eb783abeed3433c94b9c8fffbbae2546300fd6b2",
        }
        for key in KEYS:
            lock = profile_module._LOCKS[key]
            self.assertEqual(expected_paths[key], tuple(row[0] for row in lock["sites"]))
            self.assertEqual(profile_hashes[key], profile_module._sha(
                profile_module._profile_tuple(key, lock)))
        expected = {
            LENS_KEY: (8, Counter({"write": 4, "read": 4}), Counter({0: 5, 1: 2, 2: 1})),
            PRISMATIC_KEY: (3, Counter({"write": 2, "read": 1}), Counter({0: 2, 1: 1})),
        }
        all_roles = Counter()
        all_lanes = Counter()
        for key in KEYS:
            program = typed[key]
            source_hash = entries[key]["raw_sha256"]
            pre_sites = authenticate_literal_vec3_lane_index_pre(
                program, source_hash, PROFILE)
            site_count, roles, lanes = expected[key]
            self.assertEqual(site_count, len(pre_sites))
            self.assertTrue(all(site.kind == "index" for site in pre_sites))

            locked_profile_hash = profile_module._LOCKS[key]["profile"]
            try:
                profile_module._LOCKS[key]["profile"] = "0" * 64
                with self.assertRaises(ValueError):
                    authenticate_literal_vec3_lane_index_pre(
                        program, source_hash, PROFILE)
            finally:
                profile_module._LOCKS[key]["profile"] = locked_profile_hash

            transformed = apply_literal_vec3_lane_index(
                program, source_hash, PROFILE)
            self.assertIsNot(program, transformed)
            for before_function, after_function in zip(
                    program.functions, transformed.functions):
                if before_function.name == "main":
                    self.assertIsNot(before_function, after_function)
                else:
                    self.assertIs(before_function, after_function)
                    self.assertEqual(before_function, after_function)

            transition_sites = authenticate_literal_vec3_lane_index_transition(
                program, transformed, source_hash, PROFILE)
            post_sites = authenticate_literal_vec3_lane_index_post(
                transformed, source_hash, PROFILE)
            self.assertEqual(post_sites, transition_sites)
            self.assertEqual(roles, Counter(role for _, _, role in post_sites))
            self.assertEqual(lanes, Counter(lane for _, lane, _ in post_sites))
            self.assertTrue(all(
                site.kind == "swizzle" and site.member == "xyz"[lane]
                for site, lane, _ in post_sites))
            self.assertTrue(all(
                post.children[0] is pre.children[0]
                for pre, (post, _, _) in zip(pre_sites, transition_sites)))

            def clone_expression(value):
                return dataclasses.replace(
                    value,
                    children=tuple(clone_expression(child)
                                   for child in value.children))

            def clone_statement(value):
                return dataclasses.replace(
                    value,
                    expressions=tuple(clone_expression(expression)
                                      for expression in value.expressions),
                    children=tuple(clone_statement(child)
                                   for child in value.children))

            reconstructed = dataclasses.replace(
                transformed,
                functions=tuple(dataclasses.replace(
                    function,
                    body=tuple(clone_statement(statement)
                               for statement in function.body))
                                for function in transformed.functions))
            self.assertEqual(post_sites, authenticate_literal_vec3_lane_index_post(
                reconstructed, source_hash, PROFILE))
            with self.assertRaises(ValueError):
                authenticate_literal_vec3_lane_index_transition(
                    program, reconstructed, source_hash, PROFILE)
            with self.assertRaises(ValueError):
                apply_literal_vec3_lane_index(transformed, source_hash, PROFILE)
            all_roles.update(role for _, _, role in post_sites)
            all_lanes.update(lane for _, lane, _ in post_sites)

        self.assertEqual(Counter({"write": 6, "read": 5}), all_roles)
        self.assertEqual(Counter({0: 7, 1: 3, 2: 1}), all_lanes)

    def test_task25_literal_vec3_lane_profile_rejects_proof_injection_and_nonmain_indexes(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend import literal_vec3_lane_index_profile as profile_module
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import (
            LENS_KEY, PROFILE,
            apply_literal_vec3_lane_index,
            authenticate_literal_vec3_lane_index_post,
            authenticate_literal_vec3_lane_index_pre,
            authenticate_literal_vec3_lane_index_transition)
        from tools.glslcpp.frontend.semantic import analyze_program

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == LENS_KEY)
        exact = analyze_program(parse_program(
            (root / entry["source"]).read_text(), LENS_KEY, {}), LENS_KEY)
        source_hash = entry["raw_sha256"]
        post = apply_literal_vec3_lane_index(exact, source_hash, PROFILE)

        proof_fields = (
            "fixed_nine_table_proof",
            "fixed_grid_counter_store_proof",
            "fixed_array_in_parameter_proof",
            "fixed_affine_centers13_proof",
        )
        for field in proof_fields:
            injected_pre = dataclasses.replace(exact, **{field: object()})
            injected_post = dataclasses.replace(post, **{field: object()})
            with self.subTest(field=field, boundary="pre"), self.assertRaises(ValueError):
                authenticate_literal_vec3_lane_index_pre(
                    injected_pre, source_hash, PROFILE)
            with self.subTest(field=field, boundary="post"), self.assertRaises(ValueError):
                authenticate_literal_vec3_lane_index_post(
                    injected_post, source_hash, PROFILE)
            with self.subTest(field=field, boundary="transition"), self.assertRaises(ValueError):
                authenticate_literal_vec3_lane_index_transition(
                    exact, injected_post, source_hash, PROFILE)
            self.assertIsNone(getattr(exact, field))
            self.assertIs(getattr(exact, field), getattr(post, field))

        auxiliary = next(function for function in exact.functions
                         if function.name != "main")
        original_statement = auxiliary.body[0]
        original_expression = original_statement.expressions[0]
        forged_expression = dataclasses.replace(original_expression, kind="index")
        forged_statement = dataclasses.replace(
            original_statement, expressions=(forged_expression,))
        forged_auxiliary = dataclasses.replace(
            auxiliary, body=(forged_statement, *auxiliary.body[1:]))
        forged = dataclasses.replace(
            exact,
            functions=tuple(forged_auxiliary if function is auxiliary else function
                            for function in exact.functions))
        self.assertEqual("index", forged_auxiliary.body[0].expressions[0].kind)
        self.assertEqual(8, len(authenticate_literal_vec3_lane_index_pre(
            exact, source_hash, PROFILE)))

        lock = profile_module._LOCKS[LENS_KEY]
        original_lock = {
            name: lock[name]
            for name in ("pre_functions", "pre_whole", "profile")
        }
        try:
            lock["pre_functions"] = profile_module._sha(forged.functions)
            lock["pre_whole"] = profile_module._whole_fingerprint(forged)
            lock["profile"] = profile_module._sha(
                profile_module._profile_tuple(LENS_KEY, lock))
            with self.assertRaises(ValueError):
                authenticate_literal_vec3_lane_index_pre(
                    forged, source_hash, PROFILE)
        finally:
            lock.update(original_lock)

    def test_task25_loader_schema_admits_only_the_two_later_lane_carriers(self) -> None:
        import copy
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import (
            KEYS, PROFILE)

        original = json.loads(
            (REPOSITORY / "tools/glslcpp/typed_slice.json").read_text())
        planned = copy.deepcopy(original)
        mutations = {"exact": planned}
        missing = copy.deepcopy(planned)
        del next(item for item in missing["programs"]
                 if item["program_key"] == KEYS[0])["literal_vec3_lane_index_profile"]
        mutations["missing"] = missing
        wrong = copy.deepcopy(planned)
        next(item for item in wrong["programs"]
             if item["program_key"] == KEYS[0])["literal_vec3_lane_index_profile"] = "wrong"
        mutations["wrong"] = wrong
        duplicate = copy.deepcopy(planned)
        duplicate["programs"].append(copy.deepcopy(next(
            item for item in planned["programs"] if item["program_key"] == KEYS[0])))
        duplicate["programs"].sort(key=lambda item: item["program_key"])
        mutations["duplicate"] = duplicate
        foreign = copy.deepcopy(planned)
        next(item for item in foreign["programs"]
             if item["program_key"] not in KEYS)["literal_vec3_lane_index_profile"] = PROFILE
        mutations["foreign"] = foreign
        compatibility = copy.deepcopy(planned)
        compatibility["compatibility_transforms"][KEYS[0]] = "crt-metal-sine-v1"
        mutations["compatibility"] = compatibility
        # "zz/forgedGrade:lut" (not "filter/grade:lut", which landed for real
        # in Task 32 and is no longer a safe stand-in for a nonexistent key)
        # is a permanently-nonexistent placeholder, matching the
        # "zz/forged:extra" convention used below.
        substituted = copy.deepcopy(planned)
        victim = next(item for item in substituted["programs"]
                      if item["program_key"] not in KEYS
                      and item["program_key"] != "zz/forgedGrade:lut")
        victim["program_key"] = "zz/forgedGrade:lut"
        substituted["programs"].sort(key=lambda item: item["program_key"])
        mutations["substituted-key"] = substituted

        grade = copy.deepcopy(planned)
        self.assertFalse(any(item["program_key"] == "zz/forgedGrade:lut"
                             for item in grade["programs"]))
        grade["programs"].append({
            "defines": {},
            "literal_vec3_lane_index_profile": PROFILE,
            "program_key": "zz/forgedGrade:lut",
        })
        grade["programs"].sort(key=lambda item: item["program_key"])
        mutations["grade-borrows-carrier"] = grade
        extra_field = copy.deepcopy(planned)
        next(item for item in extra_field["programs"]
             if item["program_key"] == KEYS[0])["extra"] = True
        mutations["selected-extra-field"] = extra_field
        selected_defines = copy.deepcopy(planned)
        next(item for item in selected_defines["programs"]
             if item["program_key"] == KEYS[0])["defines"] = {"MODE": 1}
        mutations["selected-nonempty-defines"] = selected_defines
        reordered = copy.deepcopy(planned)
        selected_index = next(index for index, item in enumerate(reordered["programs"])
                              if item["program_key"] == KEYS[0])
        reordered["programs"][selected_index], reordered["programs"][selected_index + 1] = (
            reordered["programs"][selected_index + 1],
            reordered["programs"][selected_index])
        mutations["program-order"] = reordered
        additional = copy.deepcopy(planned)
        additional["programs"].append({"defines": {}, "program_key": "zz/forged:extra"})
        additional["programs"].sort(key=lambda item: item["program_key"])
        mutations["additional-program"] = additional

        for name, change in {
                "capability-missing": lambda value: value.pop(),
                "capability-duplicate": lambda value: value.append(value[-1]),
                "capability-index": lambda value: value.append("index"),
                "capability-runtime-subscript": lambda value: value.append("runtime-subscript"),
                "capability-reordered": lambda value: value.reverse(),
        }.items():
            changed = copy.deepcopy(planned)
            change(changed["capabilities"])
            mutations[name] = changed
        for name, contracts in {
                "numeric-missing": {},
                "numeric-selected": {"filter/scatter:scatterJitter": "source-double",
                                     KEYS[0]: "source-double"},
                "numeric-unknown": {"filter/scatter:scatterJitter": "wrong"},
                "numeric-duplicate-equivalent-extra": {
                    "filter/scatter:scatterJitter": "source-double",
                    "filter/scatter:scatterSmooth": "source-double"},
        }.items():
            changed = copy.deepcopy(planned)
            changed["numeric_literal_contracts"] = contracts
            mutations[name] = changed
        for name, transform in {
                "compatibility-missing": {},
                "compatibility-selected-other": {
                    **planned["compatibility_transforms"], KEYS[1]: "coalesce-uv-alias-v1"},
                "compatibility-unknown": {
                    **planned["compatibility_transforms"], "filter/bc:bc": "wrong"},
        }.items():
            changed = copy.deepcopy(planned)
            changed["compatibility_transforms"] = transform
            mutations[name] = changed
        for name, profiles in {
                "custom-comparer-missing": {},
                "custom-comparer-wrong": {KEYS[0]: "wrong"},
                "custom-comparer-prismatic": {
                    KEYS[1]: planned["custom_comparer_profiles"][KEYS[0]]},
                "custom-comparer-foreign": {
                    KEYS[0]: planned["custom_comparer_profiles"][KEYS[0]],
                    "filter/bc:bc": planned["custom_comparer_profiles"][KEYS[0]]},
        }.items():
            changed = copy.deepcopy(planned)
            changed["custom_comparer_profiles"] = profiles
            mutations[name] = changed

        for name, payload in mutations.items():
            with self.subTest(schema=name), tempfile.TemporaryDirectory() as temporary:
                repository = pathlib.Path(temporary)
                path = repository / "tools/glslcpp/typed_slice.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(payload))
                if name == "exact":
                    loaded = generate_typed_slice.load_slice(repository)
                    self.assertEqual(137, len(loaded["programs"]))
                else:
                    with self.assertRaises(generate_typed_slice.GeneratorError):
                        generate_typed_slice.load_slice(repository)

    def test_task25_four_modes_and_value_forgery_reject_at_each_boundary(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import (
            KEYS, PROFILE, apply_literal_vec3_lane_index)
        from tools.glslcpp.frontend.lens_distortion_comparer_profile import (
            LENS_KEY, PROFILE as COMPARER_PROFILE)
        from tools.glslcpp.frontend.semantic import analyze_program

        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())

        def direct(candidate, carrier, caller_hash, custom_comparer_profile):
            validator = emitter = False
            try:
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=caller_hash,
                    custom_comparer_profile=custom_comparer_profile,
                    literal_vec3_lane_index_profile=carrier)
                validator = True
            except generate_typed_slice.GeneratorError:
                pass
            try:
                render_typed_cpp(
                    candidate, candidate.key, caller_hash,
                    custom_comparer_profile=custom_comparer_profile,
                    literal_vec3_lane_index_profile=carrier)
                emitter = True
            except TypedEmissionError:
                pass
            return validator, emitter

        for key in KEYS:
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            source_hash = entry["raw_sha256"]
            pre = analyze_program(parse_program(
                (corpus / entry["source"]).read_text(), key, {}), key)
            for carrier in (None, "wrong"):
                with self.subTest(key=key, loader_carrier=carrier), self.assertRaises(ValueError):
                    apply_literal_vec3_lane_index(pre, source_hash, carrier)
            post = apply_literal_vec3_lane_index(pre, source_hash, PROFILE)
            comparer = COMPARER_PROFILE if key == LENS_KEY else None
            self.assertEqual((False, False), direct(pre, None, source_hash, comparer))
            self.assertEqual((False, False), direct(pre, "wrong", source_hash, comparer))
            self.assertEqual((False, False), direct(pre, PROFILE, source_hash, comparer))
            self.assertEqual((False, False), direct(post, None, source_hash, comparer))
            self.assertEqual((False, False), direct(post, "wrong", source_hash, comparer))
            self.assertEqual((True, True), direct(post, PROFILE, source_hash, comparer))
            if key == LENS_KEY:
                self.assertEqual((False, False), direct(
                    post, PROFILE, source_hash, None))
                self.assertEqual((False, False), direct(
                    post, PROFILE, source_hash, "wrong"))
            else:
                self.assertEqual((False, False), direct(
                    post, PROFILE, source_hash, COMPARER_PROFILE))
            capability_cases = {
                "missing": generate_typed_slice.APPROVED_CAPABILITIES[:-1],
                "duplicate": (*generate_typed_slice.APPROVED_CAPABILITIES, "assign"),
                "unknown": (*generate_typed_slice.APPROVED_CAPABILITIES, "index"),
            }
            for capability_case, capabilities in capability_cases.items():
                with self.subTest(key=key, capability=capability_case), \
                        self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.validate_capabilities(
                        post, capabilities, source_hash=source_hash,
                        custom_comparer_profile=comparer,
                        literal_vec3_lane_index_profile=PROFILE)

            def clone_expression(value):
                return dataclasses.replace(
                    value, children=tuple(clone_expression(child)
                                          for child in value.children))
            def clone_statement(value):
                return dataclasses.replace(
                    value,
                    expressions=tuple(clone_expression(item)
                                      for item in value.expressions),
                    children=tuple(clone_statement(item)
                                   for item in value.children))
            reconstructed = dataclasses.replace(post, functions=tuple(
                dataclasses.replace(function, body=tuple(
                    clone_statement(item) for item in function.body))
                for function in post.functions))
            self.assertEqual((True, True), direct(
                reconstructed, PROFILE, source_hash, comparer))

            for caller_hash in (None, "0" * 64):
                with self.subTest(key=key, caller_hash=caller_hash):
                    self.assertEqual((False, False), direct(
                        post, PROFILE, caller_hash, comparer))

            site = next(value for value, _, _ in __import__(
                "tools.glslcpp.frontend.literal_vec3_lane_index_profile",
                fromlist=["authenticate_literal_vec3_lane_index_post"]
            ).authenticate_literal_vec3_lane_index_post(post, source_hash, PROFILE))
            def replace(value):
                if value is site:
                    return dataclasses.replace(value, member="y" if value.member != "y" else "x")
                return dataclasses.replace(value, children=tuple(replace(child) for child in value.children))
            def statement(value):
                return dataclasses.replace(
                    value, expressions=tuple(replace(item) for item in value.expressions),
                    children=tuple(statement(item) for item in value.children))
            forged = dataclasses.replace(
                post, raw_source=post.raw_source + "\nforged",
                functions=tuple(dataclasses.replace(
                    function, body=tuple(statement(item) for item in function.body))
                    for function in post.functions))
            attacker_hash = hashlib.sha256(
                forged.raw_source.encode()).hexdigest()
            for carrier in (None, "wrong", PROFILE):
                for caller_hash in (source_hash, None, "0" * 64, attacker_hash):
                    with self.subTest(key=key, carrier=carrier, caller_hash=caller_hash):
                        self.assertEqual((False, False), direct(
                            forged, carrier, caller_hash, comparer))

    def test_task25_profiled_emission_uses_only_fixed_hsv_lanes(self) -> None:
        from tools.glslcpp import check_corpus
        from tools.glslcpp.emit_typed_cpp import _Emitter, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import (
            KEYS, PROFILE, apply_literal_vec3_lane_index)
        from tools.glslcpp.frontend.lens_distortion_comparer_profile import (
            LENS_KEY, PROFILE as COMPARER_PROFILE)
        from tools.glslcpp.frontend.semantic import analyze_program

        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())
        writes = reads = 0
        for key in KEYS:
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            pre = analyze_program(parse_program(
                (corpus / entry["source"]).read_text(), key, {}), key)
            post = apply_literal_vec3_lane_index(pre, entry["raw_sha256"], PROFILE)
            emitted = render_typed_cpp(
                post, key, entry["raw_sha256"],
                custom_comparer_profile=(COMPARER_PROFILE
                                         if key == LENS_KEY else None),
                literal_vec3_lane_index_profile=PROFILE)
            pixel = emitted[emitted.index("void pixel("):emitted.index("}  // namespace", emitted.index("void pixel("))]
            writes += pixel.count("glsl::set_swizzle<0>(hsv,")
            writes += pixel.count("glsl::set_swizzle<1>(hsv,")
            writes += pixel.count("glsl::set_swizzle<2>(hsv,")
            reads += pixel.count("glsl::swizzle<0>(hsv)")
            reads += pixel.count("glsl::swizzle<1>(hsv)")
            reads += pixel.count("glsl::swizzle<2>(hsv)")
            self.assertNotIn("hsv[", pixel)
            self.assertNotIn("operator[]", pixel)
            if key == KEYS[0]:
                self.assertIn("glsl::FloatExpr<3>(glsl::swizzle<2>(hsv))", pixel)
        self.assertEqual(6, writes)
        self.assertEqual(5, reads)

        ordinary_key = "filter/bc:bc"
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == ordinary_key)
        ordinary = analyze_program(parse_program(
            (corpus / entry["source"]).read_text(), ordinary_key, {}), ordinary_key)
        emitter = _Emitter(ordinary, entry["raw_sha256"])
        self.assertEqual((), emitter.authorized_literal_vec3_lane_sites)
        bare = object.__new__(_Emitter)
        self.assertIsNone(bare._literal_lane_site(None))
        self.assertEqual((), bare.authorized_literal_vec3_lane_sites)

    def test_task25_pre_and_exact_raw_post_forgery_cartesians_are_closed(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import (
            KEYS, PROFILE, apply_literal_vec3_lane_index,
            authenticate_literal_vec3_lane_index_post,
            authenticate_literal_vec3_lane_index_pre)
        from tools.glslcpp.frontend.lens_distortion_comparer_profile import (
            LENS_KEY, PROFILE as COMPARER_PROFILE)
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.semantic_types import FLOAT, INT, vector

        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())

        def replace_expression(program, target, mutate):
            def expression(value):
                if value is target:
                    return mutate(value)
                return dataclasses.replace(
                    value, children=tuple(expression(child) for child in value.children))
            def statement(value):
                return dataclasses.replace(
                    value, expressions=tuple(expression(item) for item in value.expressions),
                    children=tuple(statement(item) for item in value.children))
            return dataclasses.replace(program, functions=tuple(
                dataclasses.replace(function, body=tuple(statement(item) for item in function.body))
                for function in program.functions))

        def replace_assignment_context(program, target, operator):
            def expression(value):
                children = tuple(expression(child) for child in value.children)
                if value.kind == "assign" and value.children[0] is target:
                    return dataclasses.replace(value, children=children, operator=operator)
                return dataclasses.replace(value, children=children)
            def statement(value):
                return dataclasses.replace(
                    value, expressions=tuple(expression(item) for item in value.expressions),
                    children=tuple(statement(item) for item in value.children))
            return dataclasses.replace(program, functions=tuple(
                dataclasses.replace(function, body=tuple(statement(item) for item in function.body))
                for function in program.functions))

        def replace_main_body(program, body):
            return dataclasses.replace(program, functions=tuple(
                dataclasses.replace(function, body=body)
                if function.name == "main" else function
                for function in program.functions))

        for key in KEYS:
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            frozen_hash = entry["raw_sha256"]
            pre = analyze_program(parse_program(
                (corpus / entry["source"]).read_text(), key, {}), key)
            custom_comparer_profile = (COMPARER_PROFILE
                                       if key == LENS_KEY else None)
            post = apply_literal_vec3_lane_index(pre, frozen_hash, PROFILE)
            pre_sites = authenticate_literal_vec3_lane_index_pre(pre, frozen_hash, PROFILE)
            post_rows = authenticate_literal_vec3_lane_index_post(
                post, frozen_hash, PROFILE)
            self.assertEqual(len(pre_sites), len(post_rows), key)

            pre_fixtures = {
                f"index-lane-site-{index}": replace_expression(
                    pre, site, lambda value: dataclasses.replace(
                        value, children=(value.children[0], dataclasses.replace(
                            value.children[1], literal="2" if value.children[1].literal_value != 2 else "1",
                            literal_value=2 if value.children[1].literal_value != 2 else 1))))
                for index, site in enumerate(pre_sites)
            }
            first_pre = pre_sites[0]
            first_pre_base = first_pre.children[0]
            first_pre_index = first_pre.children[1]
            pre_fixtures.update({
                "index-kind": replace_expression(
                    pre, first_pre, lambda value: dataclasses.replace(value, kind="swizzle")),
                "index-children": replace_expression(
                    pre, first_pre, lambda value: dataclasses.replace(value, children=value.children[:1])),
                "index-type": replace_expression(
                    pre, first_pre, lambda value: dataclasses.replace(value, type=INT)),
                "index-category": replace_expression(
                    pre, first_pre, lambda value: dataclasses.replace(value, category="rvalue")),
                "index-span": replace_expression(
                    pre, first_pre, lambda value: dataclasses.replace(
                        value, span=dataclasses.replace(value.span, start_column=value.span.start_column + 1))),
                "write-role-context": replace_assignment_context(pre, first_pre, "+="),
                "base-name": replace_expression(
                    pre, first_pre_base, lambda value: dataclasses.replace(
                        value, symbol=dataclasses.replace(value.symbol, name="forgedHsv"))),
                "base-id": replace_expression(
                    pre, first_pre_base, lambda value: dataclasses.replace(
                        value, symbol_id=value.symbol_id + 1,
                        symbol=dataclasses.replace(value.symbol, id=value.symbol.id + 1))),
                "base-type": replace_expression(
                    pre, first_pre_base, lambda value: dataclasses.replace(
                        value, type=vector("float", 2),
                        symbol=dataclasses.replace(value.symbol, type=vector("float", 2)))),
                "base-storage": replace_expression(
                    pre, first_pre_base, lambda value: dataclasses.replace(
                        value, symbol=dataclasses.replace(value.symbol, storage="uniform"))),
                "base-writability": replace_expression(
                    pre, first_pre_base, lambda value: dataclasses.replace(
                        value, symbol=dataclasses.replace(value.symbol, writable=False))),
                "index-nonint": replace_expression(
                    pre, first_pre_index, lambda value: dataclasses.replace(value, type=FLOAT)),
                "index-nonliteral": replace_expression(
                    pre, first_pre_index, lambda value: dataclasses.replace(value, kind="id")),
                "index-negative": replace_expression(
                    pre, first_pre_index, lambda value: dataclasses.replace(
                        value, literal="-1", literal_value=-1)),
                "index-lane3": replace_expression(
                    pre, first_pre_index, lambda value: dataclasses.replace(
                        value, literal="3", literal_value=3)),
                "index-effectful": replace_expression(
                    pre, first_pre_index, lambda value: dataclasses.replace(value, kind="call")),
                "raw-source": dataclasses.replace(pre, raw_source=pre.raw_source + "\nforged"),
                "normalized-source": dataclasses.replace(pre, source=pre.source + "\nforged"),
                "key": dataclasses.replace(pre, key="filter/grade:lut"),
                "defines": dataclasses.replace(pre, preprocessor_defines=(("FORGED", 1),)),
                "function-tuple": dataclasses.replace(pre, functions=pre.functions[:-1]),
                "interface": dataclasses.replace(pre, declarations=tuple(reversed(pre.declarations))),
                "compound-assignment": replace_assignment_context(pre, first_pre, "+="),
            })

            carrier_cases = (("absent", None), ("wrong", "wrong"), ("exact", PROFILE))
            control_hashes = (
                ("frozen", frozen_hash), ("missing", None),
                ("wrong", "0" * 64),
                ("recomputed", hashlib.sha256(pre.raw_source.encode()).hexdigest()))
            for carrier_label, carrier in carrier_cases:
                for hash_label, caller_hash in control_hashes:
                    expected = carrier == PROFILE and caller_hash == frozen_hash
                    with self.subTest(
                            boundary="application", key=key, family="exact-pre-control",
                            carrier=carrier_label, caller_hash=hash_label,
                            matrix="3x4"):
                        if expected:
                            self.assertIsNot(pre, apply_literal_vec3_lane_index(
                                pre, caller_hash, carrier))
                        else:
                            with self.assertRaises(ValueError):
                                apply_literal_vec3_lane_index(pre, caller_hash, carrier)
            for name, candidate in pre_fixtures.items():
                self.assertNotEqual(pre, candidate, (key, name))
                caller_cases = (
                    ("frozen", frozen_hash), ("missing", None),
                    ("wrong", "0" * 64),
                    ("recomputed", hashlib.sha256(candidate.raw_source.encode()).hexdigest()))
                self.assertEqual(3, len(carrier_cases), (key, name))
                self.assertEqual(4, len(caller_cases), (key, name))
                for carrier_label, carrier in carrier_cases:
                    for hash_label, caller_hash in caller_cases:
                        with self.subTest(
                                boundary="application", key=key, family=name,
                                carrier=carrier_label, caller_hash=hash_label,
                                matrix="3x4"):
                            with self.assertRaises(ValueError):
                                apply_literal_vec3_lane_index(candidate, caller_hash, carrier)

            post_fixtures = {
                f"member-site-{index}": replace_expression(
                    post, site, lambda value: dataclasses.replace(
                        value, member="y" if value.member != "y" else "x"))
                for index, (site, _, _) in enumerate(post_rows)
            }
            first_post = post_rows[0][0]
            first_post_base = first_post.children[0]
            post_fixtures.update({
                "kind": replace_expression(
                    post, first_post, lambda value: dataclasses.replace(value, kind="index")),
                "children": replace_expression(
                    post, first_post, lambda value: dataclasses.replace(value, children=())),
                "type": replace_expression(
                    post, first_post, lambda value: dataclasses.replace(value, type=INT)),
                "category": replace_expression(
                    post, first_post, lambda value: dataclasses.replace(value, category="rvalue")),
                "span": replace_expression(
                    post, first_post, lambda value: dataclasses.replace(
                        value, span=dataclasses.replace(value.span, start_column=value.span.start_column + 1))),
                "write-role-context": replace_assignment_context(post, first_post, "+="),
                "base-name": replace_expression(
                    post, first_post_base, lambda value: dataclasses.replace(
                        value, symbol=dataclasses.replace(value.symbol, name="forgedHsv"))),
                "base-id": replace_expression(
                    post, first_post_base, lambda value: dataclasses.replace(
                        value, symbol_id=value.symbol_id + 1,
                        symbol=dataclasses.replace(value.symbol, id=value.symbol.id + 1))),
                "base-type": replace_expression(
                    post, first_post_base, lambda value: dataclasses.replace(
                        value, type=vector("float", 2),
                        symbol=dataclasses.replace(value.symbol, type=vector("float", 2)))),
                "base-storage": replace_expression(
                    post, first_post_base, lambda value: dataclasses.replace(
                        value, symbol=dataclasses.replace(value.symbol, storage="uniform"))),
                "base-writability": replace_expression(
                    post, first_post_base, lambda value: dataclasses.replace(
                        value, symbol=dataclasses.replace(value.symbol, writable=False))),
                "raw-source": dataclasses.replace(post, raw_source=post.raw_source + "\nforged"),
                "normalized-source": dataclasses.replace(post, source=post.source + "\nforged"),
                "key": dataclasses.replace(post, key="filter/grade:lut"),
                "defines": dataclasses.replace(post, preprocessor_defines=(("FORGED", 1),)),
                "function-tuple": dataclasses.replace(post, functions=post.functions[:-1]),
                "interface": dataclasses.replace(post, declarations=tuple(reversed(post.declarations))),
                "compound-assignment": replace_assignment_context(post, first_post, "+="),
            })
            post_fixtures.update({
                f"foreign-key-plus-{name}": dataclasses.replace(
                    candidate, key="filter/bc:bc")
                for name, candidate in tuple(post_fixtures.items())
                if name != "key"
            })
            for carrier_label, carrier in carrier_cases:
                for hash_label, caller_hash in control_hashes:
                    expected = carrier == PROFILE and caller_hash == frozen_hash
                    for boundary in ("validator", "emitter"):
                        with self.subTest(
                                boundary=boundary, key=key, family="exact-post-control",
                                carrier=carrier_label, caller_hash=hash_label,
                                matrix="3x4"):
                            if boundary == "validator":
                                if expected:
                                    generate_typed_slice.validate_capabilities(
                                        post, generate_typed_slice.APPROVED_CAPABILITIES,
                                        source_hash=caller_hash,
                                        custom_comparer_profile=custom_comparer_profile,
                                        literal_vec3_lane_index_profile=carrier)
                                else:
                                    with self.assertRaises(generate_typed_slice.GeneratorError):
                                        generate_typed_slice.validate_capabilities(
                                            post, generate_typed_slice.APPROVED_CAPABILITIES,
                                            source_hash=caller_hash,
                                            custom_comparer_profile=custom_comparer_profile,
                                            literal_vec3_lane_index_profile=carrier)
                            elif expected:
                                render_typed_cpp(
                                    post, post.key, caller_hash,
                                    custom_comparer_profile=custom_comparer_profile,
                                    literal_vec3_lane_index_profile=carrier)
                            else:
                                with self.assertRaises(TypedEmissionError):
                                    render_typed_cpp(
                                        post, post.key, caller_hash,
                                        custom_comparer_profile=custom_comparer_profile,
                                        literal_vec3_lane_index_profile=carrier)
            for name, candidate in post_fixtures.items():
                self.assertEqual(post.raw_source, candidate.raw_source,
                                 (key, name, "exact-raw")) if "raw-source" not in name else None
                caller_cases = (
                    ("frozen", frozen_hash), ("missing", None),
                    ("wrong", "0" * 64),
                    ("recomputed", hashlib.sha256(candidate.raw_source.encode()).hexdigest()))
                for carrier_label, carrier in carrier_cases:
                    for hash_label, caller_hash in caller_cases:
                        for boundary in ("validator", "emitter"):
                            with self.subTest(
                                    boundary=boundary, key=key, family=name,
                                    carrier=carrier_label, caller_hash=hash_label,
                                    matrix="3x4"):
                                if boundary == "validator":
                                    with self.assertRaises(generate_typed_slice.GeneratorError):
                                        generate_typed_slice.validate_capabilities(
                                            candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                                            source_hash=caller_hash,
                                            custom_comparer_profile=custom_comparer_profile,
                                            literal_vec3_lane_index_profile=carrier)
                                else:
                                    with self.assertRaises(TypedEmissionError):
                                        render_typed_cpp(
                                            candidate, candidate.key, caller_hash,
                                            custom_comparer_profile=custom_comparer_profile,
                                            literal_vec3_lane_index_profile=carrier)

    def test_task25_exact_site_shape_origin_and_context_cartesians_are_closed(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import (
            KEYS, PROFILE, _LOCKS, _statement_at,
            apply_literal_vec3_lane_index,
            authenticate_literal_vec3_lane_index_post,
            authenticate_literal_vec3_lane_index_pre)
        from tools.glslcpp.frontend.semantic import analyze_program

        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())

        def expressions(program):
            def expression(value):
                yield value
                for child in value.children:
                    yield from expression(child)
            def statement(value):
                for item in value.expressions:
                    yield from expression(item)
                for child in value.children:
                    yield from statement(child)
            for function in program.functions:
                for item in function.body:
                    yield from statement(item)

        def replacement(program, target, change):
            matches = 0
            def expression(value):
                nonlocal matches
                if value is target:
                    matches += 1
                    return change(value)
                children = tuple(expression(child) for child in value.children)
                return (value if all(left is right for left, right in
                                     zip(children, value.children))
                        else dataclasses.replace(value, children=children))
            def statement(value):
                changed_expressions = tuple(expression(item) for item in value.expressions)
                children = tuple(statement(item) for item in value.children)
                return (value if all(left is right for left, right in
                                     zip(changed_expressions, value.expressions))
                        and all(left is right for left, right in
                                zip(children, value.children))
                        else dataclasses.replace(
                            value, expressions=changed_expressions, children=children))
            candidate = dataclasses.replace(program, functions=tuple(
                dataclasses.replace(function, body=tuple(statement(item)
                                                          for item in function.body))
                for function in program.functions))
            self.assertEqual(1, matches, (program.key, target))
            return candidate

        def replace_many(program, targets, change):
            target_ids = {id(value) for value in targets}
            matches = 0
            def expression(value):
                nonlocal matches
                if id(value) in target_ids:
                    matches += 1
                    return change(value)
                children = tuple(expression(child) for child in value.children)
                return (value if all(left is right for left, right in
                                     zip(children, value.children))
                        else dataclasses.replace(value, children=children))
            def statement(value):
                changed_expressions = tuple(expression(item) for item in value.expressions)
                children = tuple(statement(item) for item in value.children)
                return (value if all(left is right for left, right in
                                     zip(changed_expressions, value.expressions))
                        and all(left is right for left, right in
                                zip(children, value.children))
                        else dataclasses.replace(
                            value, expressions=changed_expressions, children=children))
            candidate = dataclasses.replace(program, functions=tuple(
                dataclasses.replace(function, body=tuple(statement(item)
                                                          for item in function.body))
                for function in program.functions))
            self.assertEqual(len(targets), matches, program.key)
            return candidate

        def expression_parent(program, target):
            matches = []
            def visit(value, parent=None):
                if value is target:
                    matches.append(parent)
                for child in value.children:
                    visit(child, value)
            def statement(value):
                for item in value.expressions:
                    visit(item)
                for child in value.children:
                    statement(child)
            for function in program.functions:
                for item in function.body:
                    statement(item)
            self.assertEqual(1, len(matches), (program.key, target))
            return matches[0]

        def main_with_body(program, body):
            matches = 0
            functions = []
            for function in program.functions:
                if function.name == "main":
                    matches += 1
                    functions.append(dataclasses.replace(function, body=tuple(body)))
                else:
                    functions.append(function)
            self.assertEqual(1, matches, program.key)
            return dataclasses.replace(program, functions=tuple(functions))

        def one_typed_index(name, source, *, select=lambda values: values[0]):
            typed = analyze_program(parse_program(source, f"task25/{name}", {}),
                                    f"task25/{name}")
            indexes = [value for value in expressions(typed) if value.kind == "index"]
            self.assertTrue(indexes, name)
            selected = select(indexes)
            self.assertIn(selected, indexes, name)
            return typed, selected

        source_prefix = "out vec4 fragColor; "
        origin_sources = {
            "alternate-local": source_prefix +
                "void main(){vec3 other=vec3(1.0);float x=other[0];fragColor=vec4(x);}",
            "parameter-base": source_prefix +
                "float f(vec3 hsv){return hsv[0];}void main(){fragColor=vec4(f(vec3(1.0)));}",
            "global-base": "vec3 hsv=vec3(1.0);" + source_prefix +
                "void main(){float x=hsv[0];fragColor=vec4(x);}",
            "uniform-base": "uniform vec3 hsv;" + source_prefix +
                "void main(){float x=hsv[0];fragColor=vec4(x);}",
            "vec2-base": source_prefix +
                "void main(){vec2 hsv=vec2(1.0);float x=hsv[0];fragColor=vec4(x);}",
            "vec4-base": source_prefix +
                "void main(){vec4 hsv=vec4(1.0);float x=hsv[0];fragColor=vec4(x);}",
            "integer-vector-base": source_prefix +
                "void main(){ivec3 hsv=ivec3(1);int x=hsv[0];fragColor=vec4(float(x));}",
            "array-base": source_prefix +
                "void main(){float hsv[3];hsv[0]=1.0;fragColor=vec4(hsv[0]);}",
            "matrix-base": source_prefix +
                "void main(){mat3 hsv=mat3(1.0);vec3 x=hsv[0];fragColor=vec4(x,1.0);}",
            "uniform-index": "uniform int lane;" + source_prefix +
                "void main(){vec3 hsv=vec3(1.0);float x=hsv[lane];fragColor=vec4(x);}",
            "induction-index": source_prefix +
                "void main(){vec3 hsv=vec3(1.0);float x=0.0;for(int i=0;i<1;i++){x+=hsv[i];}fragColor=vec4(x);}",
            "effectful-index": source_prefix +
                "int lane(){return 0;}void main(){vec3 hsv=vec3(1.0);float x=hsv[lane()];fragColor=vec4(x);}",
            "nested-index": source_prefix +
                "void main(){mat3 hsv=mat3(1.0);float x=hsv[0][1];fragColor=vec4(x);}",
            "alias-index": source_prefix +
                "void main(){vec3 hsv=vec3(1.0);vec3 alias=hsv;float x=alias[0];fragColor=vec4(x);}",
            "delayed-indexed-lvalue": source_prefix +
                "void main(){vec3 hsv=vec3(1.0);vec3 alias=hsv;alias[0]=2.0;fragColor=vec4(alias,1.0);}",
            "runtime-subscript": source_prefix +
                "void main(){vec3 hsv=vec3(1.0);int lane=int(gl_FragCoord.x);float x=hsv[lane];fragColor=vec4(x);}",
        }
        typed_origins = {
            name: one_typed_index(name, source, select=(lambda values: values[0]))[1]
            for name, source in origin_sources.items()
        }
        self.assertEqual("index", typed_origins["nested-index"].children[0].kind)
        self.assertEqual("parameter", typed_origins["parameter-base"].children[0].symbol.storage)
        self.assertEqual("uniform", typed_origins["uniform-base"].children[0].symbol.storage)

        context_sources = {
            "direct-write": source_prefix +
                "void main(){vec3 hsv=vec3(1.0);hsv[0]=2.0;fragColor=vec4(hsv,1.0);}",
            "compound-write": source_prefix +
                "void main(){vec3 hsv=vec3(1.0);hsv[0]+=2.0;fragColor=vec4(hsv,1.0);}",
            "prefix-update": source_prefix +
                "void main(){vec3 hsv=vec3(1.0);float x=++hsv[0];fragColor=vec4(x);}",
            "postfix-update": source_prefix +
                "void main(){vec3 hsv=vec3(1.0);float x=hsv[0]++;fragColor=vec4(x);}",
            "out-escape": source_prefix +
                "void f(out float x){x=1.0;}void main(){vec3 hsv=vec3(1.0);f(hsv[0]);fragColor=vec4(hsv,1.0);}",
            "inout-escape": source_prefix +
                "void f(inout float x){x+=1.0;}void main(){vec3 hsv=vec3(1.0);f(hsv[0]);fragColor=vec4(hsv,1.0);}",
            "rhs-order": source_prefix +
                "void main(){vec3 hsv=vec3(1.0);hsv[0]=hsv[1]+hsv[2];fragColor=vec4(hsv,1.0);}",
            "scalar-splat": source_prefix +
                "void main(){vec3 hsv=vec3(1.0);vec3 x=vec3(hsv[2]);fragColor=vec4(x,1.0);}",
        }
        typed_contexts = {}
        for name, source in context_sources.items():
            typed, site = one_typed_index(name, source)
            parent = expression_parent(typed, site)
            typed_contexts[name] = (site, parent)
        self.assertEqual(("unary", "++"),
                         (typed_contexts["prefix-update"][1].kind,
                          typed_contexts["prefix-update"][1].operator))
        self.assertEqual(("post", "++"),
                         (typed_contexts["postfix-update"][1].kind,
                          typed_contexts["postfix-update"][1].operator))

        feature_sources = {
            "global": "float g=1.0;" + source_prefix +
                "void main(){fragColor=vec4(g);}",
            "array": source_prefix +
                "void main(){float a[2];a[0]=1.0;fragColor=vec4(a[0]);}",
            "matrix": source_prefix +
                "void main(){mat3 m=mat3(1.0);fragColor=vec4(m[0],1.0);}",
            "struct": "struct S{float x;};" + source_prefix +
                "void main(){S s;fragColor=vec4(0.0);}",
            "ubo": "uniform B{float x;}b;" + source_prefix +
                "void main(){fragColor=vec4(b.x);}",
            "loop": source_prefix +
                "void main(){float x=0.0;for(int i=0;i<2;i++){x+=1.0;}fragColor=vec4(x);}",
            "derivative": source_prefix +
                "void main(){float x=dFdx(1.0);fragColor=vec4(x);}",
            "sampler": "uniform sampler2D tex;" + source_prefix +
                "void main(){fragColor=vec4(0.0);}",
            "fetch": "uniform sampler2D tex;" + source_prefix +
                "void main(){fragColor=texelFetch(tex,ivec2(0),0);}",
            "output": "out vec4 fragColor;out vec4 auxColor;"
                "void main(){fragColor=vec4(0.0);auxColor=vec4(1.0);}",
            "function": source_prefix +
                "float helper(float x){return x;}void main(){fragColor=vec4(helper(1.0));}",
            "early-return": source_prefix +
                "void main(){if(gl_FragCoord.x<0.0)return;fragColor=vec4(0.0);}",
            "recursion": source_prefix +
                "float recur(){return recur();}void main(){fragColor=vec4(recur());}",
        }
        feature_programs = {
            name: analyze_program(parse_program(source, f"task25/feature-{name}", {}),
                                  f"task25/feature-{name}")
            for name, source in feature_sources.items()
        }
        self.assertFalse(feature_programs["recursion"].counted_loop_proof.call_graph_acyclic)
        self.assertEqual(1, feature_programs["loop"].counted_loop_proof.loop_count)
        self.assertTrue(feature_programs["derivative"].resources.uses_derivatives)
        self.assertTrue(feature_programs["fetch"].resources.uses_texture)

        def feature_mutations(program):
            main_value = next(function for function in program.functions
                              if function.name == "main")
            global_declaration = next(
                declaration for declaration in feature_programs["global"].declarations
                if declaration.symbol.storage == "global")
            sampler_declaration = next(
                declaration for declaration in feature_programs["sampler"].declarations
                if declaration.type.display() == "sampler2D")
            output_declaration = next(
                declaration for declaration in feature_programs["output"].declarations
                if declaration.symbol.name == "auxColor")
            loop_statement = next(
                statement for statement in next(
                    function for function in feature_programs["loop"].functions
                    if function.name == "main").body if statement.kind == "for")
            derivative_statement = next(
                function for function in feature_programs["derivative"].functions
                if function.name == "main").body[0]
            fetch_statement = next(
                function for function in feature_programs["fetch"].functions
                if function.name == "main").body[0]
            early_statement = next(
                function for function in feature_programs["early-return"].functions
                if function.name == "main").body[0]
            helper = next(function for function in feature_programs["function"].functions
                          if function.name == "helper")
            recur = next(function for function in feature_programs["recursion"].functions
                         if function.name == "recur")
            sampler_resources = feature_programs["sampler"].resources
            fetch_resources = feature_programs["fetch"].resources
            return {
                "global-insertion": dataclasses.replace(
                    program, declarations=(*program.declarations, global_declaration)),
                "array-insertion": dataclasses.replace(
                    program, local_type_names=(*program.local_type_names, "float[2]")),
                "matrix-insertion": dataclasses.replace(
                    program, local_type_names=(*program.local_type_names, "mat3")),
                "struct-insertion": dataclasses.replace(
                    program, structs=(*program.structs,
                                      feature_programs["struct"].structs[0])),
                "ubo-insertion": dataclasses.replace(
                    program, uniform_blocks=(*program.uniform_blocks,
                                             feature_programs["ubo"].uniform_blocks[0])),
                "loop-insertion": main_with_body(
                    program, (*main_value.body, loop_statement)),
                "derivative-insertion": main_with_body(
                    dataclasses.replace(program, resources=dataclasses.replace(
                        program.resources, uses_derivatives=True)),
                    (*main_value.body, derivative_statement)),
                "sampler-insertion": dataclasses.replace(
                    program,
                    declarations=(*program.declarations, sampler_declaration),
                    resources=dataclasses.replace(
                        program.resources,
                        uniforms=(*program.resources.uniforms,
                                  *sampler_resources.uniforms),
                        samplers=(*program.resources.samplers,
                                  *sampler_resources.samplers))),
                "fetch-insertion": main_with_body(
                    dataclasses.replace(program, resources=dataclasses.replace(
                        program.resources,
                        uniforms=(*program.resources.uniforms,
                                  *fetch_resources.uniforms),
                        samplers=(*program.resources.samplers,
                                  *fetch_resources.samplers),
                        uses_texture=True)),
                    (*main_value.body, fetch_statement)),
                "output-insertion": dataclasses.replace(
                    program,
                    declarations=(*program.declarations, output_declaration),
                    resources=dataclasses.replace(
                        program.resources,
                        outputs=(*program.resources.outputs, "auxColor"))),
                "function-insertion": dataclasses.replace(
                    program, functions=(*program.functions, helper)),
                "early-return-insertion": main_with_body(
                    program, (early_statement, *main_value.body)),
                "recursion-insertion": dataclasses.replace(
                    program, functions=(*program.functions, recur)),
            }

        carrier_cases = (("absent", None), ("wrong", "wrong"), ("exact", PROFILE))

        def caller_cases(candidate, frozen_hash):
            return (("exact", frozen_hash), ("missing", None), ("wrong", "0" * 64),
                    ("attacker-recomputed",
                     hashlib.sha256(candidate.raw_source.encode()).hexdigest()))

        def reject_application(candidate, name, frozen_hash):
            for carrier_name, carrier in carrier_cases:
                for caller_name, caller_hash in caller_cases(candidate, frozen_hash):
                    with self.subTest(boundary="application", key=candidate.key,
                                      mutation=name, carrier=carrier_name,
                                      caller=caller_name, matrix="3x4"), \
                            self.assertRaises(ValueError):
                        apply_literal_vec3_lane_index(candidate, caller_hash, carrier)

        def reject_post(candidate, name, frozen_hash):
            for carrier_name, carrier in carrier_cases:
                for caller_name, caller_hash in caller_cases(candidate, frozen_hash):
                    with self.subTest(boundary="validator", key=candidate.key,
                                      mutation=name, carrier=carrier_name,
                                      caller=caller_name, matrix="3x4"), \
                            self.assertRaises(generate_typed_slice.GeneratorError):
                        generate_typed_slice.validate_capabilities(
                            candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                            source_hash=caller_hash,
                            literal_vec3_lane_index_profile=carrier)
                    with self.subTest(boundary="emitter", key=candidate.key,
                                      mutation=name, carrier=carrier_name,
                                      caller=caller_name, matrix="3x4"), \
                            self.assertRaises(TypedEmissionError):
                        render_typed_cpp(
                            candidate, candidate.key, caller_hash,
                            literal_vec3_lane_index_profile=carrier)

        pristine_site_counts = {}
        for key in KEYS:
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == key)
            frozen_hash = entry["raw_sha256"]
            pre = analyze_program(parse_program(
                (corpus / entry["source"]).read_text(), key, {}), key)
            post = apply_literal_vec3_lane_index(pre, frozen_hash, PROFILE)
            pre_sites = authenticate_literal_vec3_lane_index_pre(pre, frozen_hash, PROFILE)
            post_rows = authenticate_literal_vec3_lane_index_post(post, frozen_hash, PROFILE)
            post_sites = tuple(row[0] for row in post_rows)
            lock = _LOCKS[key]
            main = next(function for function in pre.functions if function.name == "main")
            post_main = next(function for function in post.functions if function.name == "main")
            self.assertEqual(len(lock["sites"]), len(pre_sites), key)
            for row, pre_site, post_site in zip(lock["sites"], pre_sites, post_sites):
                self.assertIs(pre_site, _statement_at(main, row[0]), (key, row[0]))
                self.assertIs(post_site, _statement_at(post_main, row[0]), (key, row[0]))
                self.assertEqual(row[1],
                    f"{pre_site.span.start_line}:{pre_site.span.start_column}-"
                    f"{pre_site.span.end_line}:{pre_site.span.end_column}")
            pristine_site_counts[key] = len(pre_sites)

            main_index = lock["sites"][0][0][0]
            self.assertLess(main_index + 1, len(main.body), key)
            moved_body = list(main.body)
            moved_body[main_index], moved_body[main_index + 1] = (
                moved_body[main_index + 1], moved_body[main_index])
            pre_mutations = {
                "site-count-zero": replace_many(pre, pre_sites,
                                                lambda value: value.children[0]),
                "site-count-partial": replacement(pre, pre_sites[-1],
                                                  lambda value: value.children[0]),
                "site-moved": main_with_body(pre, moved_body),
                "site-order-reversed": main_with_body(pre, tuple(reversed(main.body))),
                "already-transformed": post,
            }
            template = next(statement for statement in main.body
                            if statement.kind == "expr")
            additional_site = dataclasses.replace(pre_sites[0])
            extra = dataclasses.replace(
                template, expressions=(additional_site,), children=())
            pre_mutations["site-count-additional"] = main_with_body(
                pre, (*main.body, extra))
            duplicate = dataclasses.replace(
                template, expressions=(pre_sites[0],), children=())
            pre_mutations["site-duplicate-object"] = main_with_body(
                pre, (*main.body, duplicate))

            first_site = pre_sites[0]
            first_parent = expression_parent(pre, first_site)
            read_site = next(site for site, row in zip(pre_sites, lock["sites"])
                             if row[3] == "read")
            read_parent = expression_parent(pre, read_site)
            self.assertEqual(("write", "read"),
                             (lock["sites"][0][3], next(
                                 row[3] for site, row in zip(pre_sites, lock["sites"])
                                 if site is read_site)))
            for name, external in typed_origins.items():
                pre_mutations[name] = replacement(pre, first_site, lambda _, value=external: value)
            for name, (external_site, external_parent) in typed_contexts.items():
                selected_site = read_site if name == "direct-write" else first_site
                selected_parent = read_parent if name == "direct-write" else first_parent
                grafted_parent = replacement(
                    dataclasses.replace(pre, functions=(dataclasses.replace(
                        next(function for function in pre.functions if function.name == "main"),
                        body=(dataclasses.replace(template, expressions=(external_parent,), children=()),)),)),
                    external_site, lambda _, site=selected_site: site
                ).functions[0].body[0].expressions[0]
                pre_mutations[name] = replacement(
                    pre, selected_parent, lambda _, value=grafted_parent: value)
            self.assertEqual("assign", typed_contexts["direct-write"][1].kind)
            self.assertEqual("=", typed_contexts["direct-write"][1].operator)
            pre_mutations["read-to-direct-write"] = pre_mutations.pop("direct-write")
            pre_mutations["write-to-read-scalar-splat"] = pre_mutations.pop("scalar-splat")
            self.assertEqual("assign", first_parent.kind)
            self.assertEqual("=", first_parent.operator)
            pre_mutations["rhs-order-reversed"] = replacement(
                pre, first_parent, lambda value: dataclasses.replace(
                    value, children=(value.children[1], value.children[0])))
            if key == KEYS[0]:
                splat_site = next(site for site, row in zip(pre_sites, lock["sites"])
                                  if row[2:] and row[2] == 2 and row[3] == "read")
                splat_parent = expression_parent(pre, splat_site)
                self.assertEqual(("construct", "vec3", 1),
                    (splat_parent.kind, splat_parent.constructor_type.display(),
                     len(splat_parent.children)))
                scalar_literals = [value for value in expressions(pre)
                                   if value.kind == "literal"
                                   and value.type.display() == "float"]
                self.assertGreaterEqual(len(scalar_literals), 2)
                pre_mutations["line260-nonsplat"] = replacement(
                    pre, splat_parent, lambda value: dataclasses.replace(
                        value, children=(scalar_literals[0], scalar_literals[1],
                                         splat_site)))

            non_main = next(function for function in pre.functions if function.name != "main")
            pre_mutations.update({
                "function-order": dataclasses.replace(pre, functions=tuple(reversed(pre.functions))),
                "main-id": dataclasses.replace(pre, functions=tuple(
                    dataclasses.replace(function, signature=dataclasses.replace(
                        function.signature, id=function.id + 1))
                    if function.name == "main" else function for function in pre.functions)),
                "main-signature": dataclasses.replace(pre, functions=tuple(
                    dataclasses.replace(function, signature=dataclasses.replace(
                        function.signature, name="forgedMain"))
                    if function.name == "main" else function for function in pre.functions)),
                "main-body-count": main_with_body(pre, main.body[:-1]),
                "non-site-function": dataclasses.replace(pre, functions=tuple(
                    dataclasses.replace(function, body=(*function.body, function.body[-1]))
                    if function is non_main else function for function in pre.functions)),
                "resource": dataclasses.replace(pre, resources=dataclasses.replace(
                    pre.resources, uses_derivatives=True)),
                "control-proof": dataclasses.replace(pre, counted_loop_proof=dataclasses.replace(
                    pre.counted_loop_proof, call_graph_acyclic=False)),
                "whole-body-status": dataclasses.replace(pre, body_status="forged"),
            })
            pre_mutations.update(feature_mutations(pre))

            def selected_census(program, kind):
                return sum(value.kind == kind for value in expressions(program))
            self.assertEqual(0, selected_census(pre_mutations["site-count-zero"], "index"))
            self.assertEqual(len(pre_sites) - 1,
                             selected_census(pre_mutations["site-count-partial"], "index"))
            self.assertEqual(len(pre_sites) + 1,
                             selected_census(pre_mutations["site-count-additional"], "index"))
            self.assertEqual(len(pre_sites) + 1,
                             selected_census(pre_mutations["site-duplicate-object"], "index"))
            self.assertEqual(len(pre_sites), selected_census(pre_mutations["site-moved"], "index"))
            for name, candidate in pre_mutations.items():
                self.assertNotEqual(pre, candidate, (key, name))
                reject_application(candidate, name, frozen_hash)

            moved_post_body = list(post_main.body)
            moved_post_body[main_index], moved_post_body[main_index + 1] = (
                moved_post_body[main_index + 1], moved_post_body[main_index])

            def nested_swizzle(value):
                inner = dataclasses.replace(value)
                self.assertIsNot(inner, value)
                self.assertEqual(inner, value)
                return dataclasses.replace(value, children=(inner,))

            post_mutations = {
                "site-count-zero": replace_many(post, post_sites,
                                                lambda value: value.children[0]),
                "site-count-partial": replacement(post, post_sites[-1],
                                                  lambda value: value.children[0]),
                "site-moved": main_with_body(post, moved_post_body),
                "site-order-reversed": main_with_body(post, tuple(reversed(post_main.body))),
                "twice-transformed": replacement(
                    post, post_sites[0], nested_swizzle),
            }
            post_template = next(statement for statement in post_main.body
                                 if statement.kind == "expr")
            additional_post_site = dataclasses.replace(post_sites[0])
            post_extra = dataclasses.replace(
                post_template, expressions=(additional_post_site,), children=())
            post_mutations["site-count-additional"] = main_with_body(
                post, (*post_main.body, post_extra))
            post_duplicate = dataclasses.replace(
                post_template, expressions=(post_sites[0],), children=())
            post_mutations["site-duplicate-object"] = main_with_body(
                post, (*post_main.body, post_duplicate))
            first_post = post_sites[0]
            first_post_parent = expression_parent(post, first_post)
            read_post = next(site for site, (_, _, role) in zip(post_sites, post_rows)
                             if role == "read")
            read_post_parent = expression_parent(post, read_post)
            for name, external in typed_origins.items():
                post_mutations[name] = replacement(
                    post, first_post, lambda value, external=external:
                    dataclasses.replace(value, children=(external.children[0],)))
            for name, (external_site, external_parent) in typed_contexts.items():
                selected_site = read_post if name == "direct-write" else first_post
                selected_parent = (read_post_parent if name == "direct-write"
                                   else first_post_parent)
                holder = dataclasses.replace(
                    post, functions=(dataclasses.replace(
                        next(function for function in post.functions if function.name == "main"),
                        body=(dataclasses.replace(
                            post_template, expressions=(external_parent,), children=()),)),))
                grafted_parent = replacement(
                    holder, external_site, lambda _, site=selected_site: site
                ).functions[0].body[0].expressions[0]
                post_mutations[name] = replacement(
                    post, selected_parent, lambda _, value=grafted_parent: value)
            post_mutations["read-to-direct-write"] = post_mutations.pop("direct-write")
            post_mutations["write-to-read-scalar-splat"] = post_mutations.pop("scalar-splat")
            post_mutations["rhs-order-reversed"] = replacement(
                post, first_post_parent, lambda value: dataclasses.replace(
                    value, children=(value.children[1], value.children[0])))
            if key == KEYS[0]:
                splat_post = next(site for site, (_, lane, role) in zip(post_sites, post_rows)
                                  if lane == 2 and role == "read")
                splat_post_parent = expression_parent(post, splat_post)
                self.assertEqual(("construct", "vec3", 1),
                    (splat_post_parent.kind,
                     splat_post_parent.constructor_type.display(),
                     len(splat_post_parent.children)))
                scalar_literals = [value for value in expressions(post)
                                   if value.kind == "literal"
                                   and value.type.display() == "float"]
                post_mutations["line260-nonsplat"] = replacement(
                    post, splat_post_parent, lambda value: dataclasses.replace(
                        value, children=(scalar_literals[0], scalar_literals[1],
                                         splat_post)))
            post_mutations.update({
                "function-order": dataclasses.replace(post, functions=tuple(reversed(post.functions))),
                "main-id": dataclasses.replace(post, functions=tuple(
                    dataclasses.replace(function, signature=dataclasses.replace(
                        function.signature, id=function.id + 1))
                    if function.name == "main" else function for function in post.functions)),
                "main-signature": dataclasses.replace(post, functions=tuple(
                    dataclasses.replace(function, signature=dataclasses.replace(
                        function.signature, name="forgedMain"))
                    if function.name == "main" else function for function in post.functions)),
                "main-body-count": main_with_body(post, post_main.body[:-1]),
                "non-site-function": dataclasses.replace(post, functions=tuple(
                    dataclasses.replace(function, body=(*function.body, function.body[-1]))
                    if function is non_main else function for function in post.functions)),
                "resource": dataclasses.replace(post, resources=dataclasses.replace(
                    post.resources, uses_derivatives=True)),
                "control-proof": dataclasses.replace(post, counted_loop_proof=dataclasses.replace(
                    post.counted_loop_proof, call_graph_acyclic=False)),
                "whole-body-status": dataclasses.replace(post, body_status="forged"),
            })
            post_mutations.update(feature_mutations(post))
            for name, candidate in post_mutations.items():
                self.assertEqual(post.raw_source, candidate.raw_source, (key, name))
                self.assertNotEqual(post, candidate, (key, name))
                reject_post(candidate, name, frozen_hash)

            moved_post_values = tuple(expressions(post_mutations["site-moved"]))
            self.assertEqual(
                (1,) * len(post_sites),
                tuple(sum(value is site for value in moved_post_values)
                      for site in post_sites))

        self.assertEqual({KEYS[0]: 8, KEYS[1]: 3}, pristine_site_counts)
        self.assertEqual(11, sum(pristine_site_counts.values()))
        self.assertEqual(10, pristine_site_counts[KEYS[0]] - 1 + pristine_site_counts[KEYS[1]])
        self.assertEqual(12, pristine_site_counts[KEYS[0]] + 1 + pristine_site_counts[KEYS[1]])

    def test_task25_real_parser_semantic_resource_and_control_exclusions_are_closed(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend import FrontendError, parse_program
        from tools.glslcpp.frontend.diagnostics import SemanticError
        from tools.glslcpp.frontend.semantic import analyze_program

        control = (
            "out vec4 fragColor;float helper(float x){return x;}"
            "void main(){vec3 hsv=vec3(1.0);float x=hsv.x;"
            "fragColor=vec4(helper(x));}")
        control_typed = analyze_program(
            parse_program(control, "task25/exclusion-control", {}),
            "task25/exclusion-control")
        generate_typed_slice.validate_capabilities(
            control_typed, generate_typed_slice.APPROVED_CAPABILITIES)

        def expression_walk(program):
            def expression(value):
                yield value
                for child in value.children:
                    yield from expression(child)
            def statement(value):
                for item in value.expressions:
                    yield from expression(item)
                for child in value.children:
                    yield from statement(child)
            for function in program.functions:
                for item in function.body:
                    yield from statement(item)

        typed_targets = {
            "alternate-local": "out vec4 fragColor;void main(){vec3 other=vec3(1.0);float x=other[0];fragColor=vec4(x);}",
            "parameter-base": "out vec4 fragColor;float f(vec3 hsv){return hsv[0];}void main(){fragColor=vec4(f(vec3(1.0)));}",
            "global-base": "vec3 hsv=vec3(1.0);out vec4 fragColor;void main(){float x=hsv[0];fragColor=vec4(x);}",
            "uniform-base": "uniform vec3 hsv;out vec4 fragColor;void main(){float x=hsv[0];fragColor=vec4(x);}",
            "vec2-base": "out vec4 fragColor;void main(){vec2 hsv=vec2(1.0);float x=hsv[0];fragColor=vec4(x);}",
            "vec4-base": "out vec4 fragColor;void main(){vec4 hsv=vec4(1.0);float x=hsv[0];fragColor=vec4(x);}",
            "integer-vector": "out vec4 fragColor;void main(){ivec3 hsv=ivec3(1);int x=hsv[0];fragColor=vec4(float(x));}",
            "array": "out vec4 fragColor;void main(){float hsv[3];hsv[0]=1.0;fragColor=vec4(hsv[0]);}",
            "matrix": "out vec4 fragColor;void main(){mat3 hsv=mat3(1.0);float x=hsv[0][1];fragColor=vec4(x);}",
            "uniform-index": "uniform int lane;out vec4 fragColor;void main(){vec3 hsv=vec3(1.0);float x=hsv[lane];fragColor=vec4(x);}",
            "induction-index": "out vec4 fragColor;void main(){vec3 hsv=vec3(1.0);float x=0.0;for(int i=0;i<1;i++){x+=hsv[i];}fragColor=vec4(x);}",
            "effectful-index": "out vec4 fragColor;int lane(){return 0;}void main(){vec3 hsv=vec3(1.0);float x=hsv[lane()];fragColor=vec4(x);}",
            "alias": "out vec4 fragColor;void main(){vec3 hsv=vec3(1.0);vec3 alias=hsv;float x=alias[0];fragColor=vec4(x);}",
            "delayed-lvalue": "out vec4 fragColor;void main(){vec3 hsv=vec3(1.0);vec3 alias=hsv;alias[0]=2.0;fragColor=vec4(alias,1.0);}",
            "direct-write": "out vec4 fragColor;void main(){vec3 hsv=vec3(1.0);hsv[0]=2.0;fragColor=vec4(hsv,1.0);}",
            "compound-write": "out vec4 fragColor;void main(){vec3 hsv=vec3(1.0);hsv[0]+=2.0;fragColor=vec4(hsv,1.0);}",
            "prefix": "out vec4 fragColor;void main(){vec3 hsv=vec3(1.0);float x=++hsv[0];fragColor=vec4(x);}",
            "postfix": "out vec4 fragColor;void main(){vec3 hsv=vec3(1.0);float x=hsv[0]++;fragColor=vec4(x);}",
            "out-escape": "out vec4 fragColor;void f(out float x){x=1.0;}void main(){vec3 hsv=vec3(1.0);f(hsv[0]);fragColor=vec4(hsv,1.0);}",
            "inout-escape": "out vec4 fragColor;void f(inout float x){x+=1.0;}void main(){vec3 hsv=vec3(1.0);f(hsv[0]);fragColor=vec4(hsv,1.0);}",
            "runtime-subscript": "out vec4 fragColor;void main(){vec3 hsv=vec3(1.0);int lane=int(gl_FragCoord.x);float x=hsv[lane];fragColor=vec4(x);}",
            "scalar-splat": "out vec4 fragColor;void main(){vec3 hsv=vec3(1.0);vec3 x=vec3(hsv[2]);fragColor=vec4(x,1.0);}",
            "global": "float g=1.0;out vec4 fragColor;void main(){fragColor=vec4(g);}",
            "struct": "struct S{float x;};out vec4 fragColor;void main(){S s;fragColor=vec4(0.0);}",
            "ubo": "uniform B{float x;}b;out vec4 fragColor;void main(){fragColor=vec4(b.x);}",
            "varying": "in vec2 vUv;out vec4 fragColor;void main(){fragColor=vec4(vUv,0.0,1.0);}",
            "derivative": "out vec4 fragColor;void main(){fragColor=vec4(dFdx(1.0));}",
            "sampler": "uniform sampler2D tex;out vec4 fragColor;void main(){fragColor=texture(tex,vec2(0.0));}",
            "fetch": "uniform sampler2D tex;out vec4 fragColor;void main(){fragColor=texelFetch(tex,ivec2(0),0);}",
            "extra-output": "out vec4 fragColor;out vec4 auxColor;void main(){fragColor=vec4(0.0);auxColor=vec4(1.0);}",
        }
        for name, source in typed_targets.items():
            typed = analyze_program(parse_program(source, f"task25/{name}", {}),
                                    f"task25/{name}")
            index_count = sum(
                1 for function in typed.functions for statement in function.body
                for expression in statement.expressions
                if expression.kind == "index")
            if "index" in name or name in {
                    "alternate-local", "parameter-base", "global-base", "uniform-base",
                    "vec2-base", "vec4-base", "integer-vector", "array", "matrix",
                    "alias", "delayed-lvalue", "direct-write", "compound-write",
                    "prefix", "postfix", "out-escape", "inout-escape", "scalar-splat"}:
                self.assertTrue(any(value.kind == "index"
                    for value in expression_walk(typed)), (name, index_count))
            if name in {"sampler", "fetch", "extra-output"}:
                generate_typed_slice.validate_capabilities(
                    typed, generate_typed_slice.APPROVED_CAPABILITIES)
            else:
                with self.subTest(real_typed_boundary=name), self.assertRaises(
                        generate_typed_slice.GeneratorError):
                    generate_typed_slice.validate_capabilities(
                        typed, generate_typed_slice.APPROVED_CAPABILITIES)

        recursion_source = (
            "out vec4 fragColor;float recur(){return recur();}"
            "void main(){fragColor=vec4(recur());}")
        recursion = analyze_program(
            parse_program(recursion_source, "task25/recursion", {}),
            "task25/recursion")
        self.assertFalse(recursion.counted_loop_proof.call_graph_acyclic)
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                recursion, generate_typed_slice.APPROVED_CAPABILITIES)

        semantic_targets = {
            "non-int-index": "out vec4 fragColor;void main(){vec3 hsv=vec3(1.0);float x=hsv[1.0];fragColor=vec4(x);}",
            "negative-index": "out vec4 fragColor;void main(){vec3 hsv=vec3(1.0);float x=hsv[-1];fragColor=vec4(x);}",
            "out-of-range-index": "out vec4 fragColor;void main(){vec3 hsv=vec3(1.0);float x=hsv[3];fragColor=vec4(x);}",
            "struct-index": "struct S{float x;};out vec4 fragColor;void main(){S hsv;float x=hsv[0];fragColor=vec4(x);}",
            "sampler-index": "uniform sampler2D hsv;out vec4 fragColor;void main(){float x=hsv[0];fragColor=vec4(x);}",
            "pointer": "out vec4 fragColor;void main(){float *ptr;fragColor=vec4(0.0);}",
        }
        for name, source in semantic_targets.items():
            parsed = parse_program(source, f"task25/{name}", {})
            self.assertTrue(parsed["ast"]["decls"], name)
            if name == "pointer":
                pointer_expression = parsed["ast"]["decls"][-1]["body"][0]["expr"]
                self.assertEqual(("binary", "*"),
                                 (pointer_expression["k"], pointer_expression["op"]))
                context = self.assertRaisesRegex(SemanticError, "E_UNKNOWN_SYMBOL")
            else:
                context = self.assertRaises(SemanticError)
            with self.subTest(real_semantic_boundary=name), context:
                analyze_program(parsed, f"task25/{name}")

        fixed_stack = (
            "out vec4 fragColor;void main(){float values[2];values[0]=1.0;"
            "fragColor=vec4(values[0]);}")
        dynamic_stack = (
            "out vec4 fragColor;void main(){int n=int(gl_FragCoord.x);"
            "float values[n];fragColor=vec4(values[0]);}")
        self.assertTrue(analyze_program(
            parse_program(fixed_stack, "task25/fixed-stack", {}),
            "task25/fixed-stack").functions)
        dynamic_parsed = parse_program(dynamic_stack, "task25/dynamic-stack", {})
        with self.assertRaisesRegex(SemanticError, "E_ARRAY_SIZE"):
            analyze_program(dynamic_parsed, "task25/dynamic-stack")

        parser_targets = {
            "allocation": "float x=new float;fragColor=vec4(x);",
            "callback": "float (*cb)(float)=helper;fragColor=vec4(cb(1.0));",
            "exception": "throw 1;fragColor=vec4(0.0);",
            "indirect-call": "float (*fn)(float)=helper;fragColor=vec4(fn(1.0));",
        }
        for name, body in parser_targets.items():
            source = ("out vec4 fragColor;float helper(float x){return x;}"
                      f"void main(){{{body}}}")
            with self.subTest(real_parser_boundary=name), self.assertRaises(FrontendError):
                parse_program(source, f"task25/{name}", {})

    def test_task25_selected_corpus_identity_drift_rejects_at_real_preflight(self) -> None:
        import copy
        from tools.glslcpp import check_corpus
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import KEYS

        root = check_corpus._corpus_root(REPOSITORY)
        exact_manifest = json.loads((root / "manifest.json").read_text())
        check_corpus.validate_corpus(REPOSITORY)
        mutations = {}
        revision = copy.deepcopy(exact_manifest)
        revision["revision"] = "0" * 40
        mutations["corpus-revision"] = revision
        for selected_key in KEYS:
            entry = next(item for item in exact_manifest["programs"]
                         if item["program_key"] == selected_key)
            other = next(item for item in exact_manifest["programs"]
                         if item["program_key"] != selected_key)
            field_values = {
                "effect_id": "filter/forged",
                "program": "forgedProgram",
                "program_key": selected_key + "-forged",
                "runtime_key": other["runtime_key"],
                "source": "sources/filter/forged/forged.glsl",
                "raw_bytes": entry["raw_bytes"] + 1,
                "raw_sha256": "0" * 64,
                "normalized_bytes": entry["normalized_bytes"] + 1,
                "normalized_sha256": "1" * 64,
                "status": "adapter",
                "pass_index": entry["pass_index"] + 1,
                "pass_name": "forged-pass",
                "outputs": [*entry["outputs"], "forgedOutput"],
                "varyings": ["forgedVarying"],
            }
            for field, value in field_values.items():
                changed = copy.deepcopy(exact_manifest)
                changed_entry = next(item for item in changed["programs"]
                                     if item["program_key"] == selected_key)
                changed_entry[field] = value
                mutations[f"{selected_key}/{field}"] = changed

        original_load = check_corpus._load_json
        for name, candidate in mutations.items():
            def patched_load(path, label, *, candidate=candidate):
                if path.name == "manifest.json":
                    return copy.deepcopy(candidate)
                return original_load(path, label)
            with self.subTest(corpus_identity=name), mock.patch.object(
                    check_corpus, "_load_json", side_effect=patched_load), \
                    self.assertRaises(check_corpus.CorpusError):
                check_corpus.validate_corpus(REPOSITORY)

    def test_task25_driver_rejects_patched_profile_disagreement_before_emission(self) -> None:
        import copy
        import dataclasses
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.literal_vec3_lane_index_profile import (
            KEYS, PROFILE, apply_literal_vec3_lane_index,
            authenticate_literal_vec3_lane_index_post,
            authenticate_literal_vec3_lane_index_pre)
        from tools.glslcpp.frontend.semantic import analyze_program

        corpus = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((corpus / "manifest.json").read_text())
        planned = copy.deepcopy(generate_typed_slice.load_slice(REPOSITORY))
        original_apply = generate_typed_slice.apply_literal_vec3_lane_index
        original_analyze = generate_typed_slice.analyze_program
        original_corpus_preflight = generate_typed_slice.check_corpus.validate_corpus
        original_semantic_preflight = generate_typed_slice.check_semantics.semantic_report
        real_preflight_calls = [0, 0]
        real_preflight_pending = True
        generated_paths = (
            REPOSITORY / "src/typed_generated/typed_slice.cpp",
            REPOSITORY / "src/typed_generated/typed_manifest.json",
            REPOSITORY / "include/noisemaker/generated/catalog.hpp",
        )

        def snapshot():
            return tuple(path.read_bytes() for path in generated_paths)

        def replace_site(program, target, change):
            matches = 0
            def expression(value):
                nonlocal matches
                if value is target:
                    matches += 1
                    return change(value)
                return dataclasses.replace(
                    value, children=tuple(expression(child) for child in value.children))
            def statement(value):
                return dataclasses.replace(
                    value,
                    expressions=tuple(expression(item) for item in value.expressions),
                    children=tuple(statement(item) for item in value.children))
            changed = dataclasses.replace(program, functions=tuple(
                dataclasses.replace(function, body=tuple(
                    statement(item) for item in function.body))
                for function in program.functions))
            self.assertEqual(1, matches, program.key)
            return changed

        for selected_key in KEYS:
            entry = next(item for item in manifest["programs"]
                         if item["program_key"] == selected_key)
            pre = analyze_program(parse_program(
                (corpus / entry["source"]).read_text(), selected_key, {}),
                selected_key)
            source_hash = entry["raw_sha256"]
            pre_site = authenticate_literal_vec3_lane_index_pre(
                pre, source_hash, PROFILE)[0]
            forged_pre = replace_site(
                pre, pre_site, lambda value: dataclasses.replace(
                    value, children=(value.children[0], dataclasses.replace(
                        value.children[1], literal="2", literal_value=2))))
            post = apply_literal_vec3_lane_index(pre, source_hash, PROFILE)
            post_site, _, _ = authenticate_literal_vec3_lane_index_post(
                post, source_hash, PROFILE)[0]
            forged_post = replace_site(
                post, post_site, lambda value: dataclasses.replace(
                    value, member="y" if value.member != "y" else "x"))
            self.assertEqual(pre.raw_source, forged_pre.raw_source)
            self.assertEqual(post.raw_source, forged_post.raw_source)

            prioritized = copy.deepcopy(planned)
            target_record = next(item for item in prioritized["programs"]
                                 if item["program_key"] == selected_key)
            prioritized["programs"] = [target_record] + [
                item for item in prioritized["programs"] if item is not target_record]

            def patched_apply(candidate, caller_hash, carrier):
                if candidate.key == selected_key:
                    return forged_post
                return original_apply(candidate, caller_hash, carrier)

            def forged_pre_analyze(parsed, key, *args, **kwargs):
                if key == selected_key:
                    return forged_pre
                return original_analyze(parsed, key, *args, **kwargs)

            def post_analyze(parsed, key, *args, **kwargs):
                if key == selected_key:
                    return post
                return original_analyze(parsed, key, *args, **kwargs)

            driver_cases = (
                ("forged-post-from-application", "apply", patched_apply),
                ("forged-pre-from-analyzer", "analyze", forged_pre_analyze),
                ("already-post-from-analyzer", "analyze", post_analyze),
            )
            for name, boundary, patch_value in driver_cases:
                before = snapshot()
                patch_target = (generate_typed_slice.apply_literal_vec3_lane_index
                                if boundary == "apply"
                                else generate_typed_slice.analyze_program)
                if real_preflight_pending:
                    def corpus_preflight(repository):
                        real_preflight_calls[0] += 1
                        return original_corpus_preflight(repository)
                    def semantic_preflight(repository):
                        real_preflight_calls[1] += 1
                        return original_semantic_preflight(repository)
                else:
                    def corpus_preflight(repository):
                        return None
                    def semantic_preflight(repository):
                        return {"body_success": 212}
                with self.subTest(key=selected_key, driver_forgery=name), \
                        mock.patch.object(generate_typed_slice, "load_slice",
                                          return_value=prioritized), \
                        mock.patch.object(generate_typed_slice.check_corpus,
                                          "validate_corpus",
                                          side_effect=corpus_preflight), \
                        mock.patch.object(generate_typed_slice.check_semantics,
                                          "semantic_report",
                                          side_effect=semantic_preflight), \
                        mock.patch.object(generate_typed_slice,
                                          patch_target.__name__,
                                          side_effect=patch_value), \
                        self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.generate_outputs(REPOSITORY)
                self.assertEqual(before, snapshot(), (selected_key, name, "generated bytes"))
                real_preflight_pending = False
        # semantic_report performs its own corpus validation, so one real
        # driver preflight intentionally reaches that validator twice.
        self.assertEqual([2, 1], real_preflight_calls)

    def test_task26_profile_authenticates_exact_identity_and_rejects_mutations(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import check_corpus
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.smooth_edge_luma_weights_profile import (
            PROFILE, SMOOTH_EDGE_KEY,
            apply_smooth_edge_luma_weights,
            authenticate_smooth_edge_luma_weights)

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == SMOOTH_EDGE_KEY)
        source = (root / entry["source"]).read_text()
        typed = analyze_program(parse_program(source, SMOOTH_EDGE_KEY, {}),
                                SMOOTH_EDGE_KEY)

        declaration, read = authenticate_smooth_edge_luma_weights(
            typed, entry["raw_sha256"], PROFILE)
        self.assertIs(declaration, typed.declarations[6])
        self.assertEqual((7, "LUMA_WEIGHTS", "const", "vec3"), (
            declaration.symbol.id, declaration.symbol.name,
            declaration.symbol.storage, declaration.type.display()))
        self.assertEqual(
            "be8644a44ad3d2710e4dfaa87045257a5bd7c0e7e0a363c12893ea77c3d2ee27",
            hashlib.sha256(repr(declaration).encode()).hexdigest())
        self.assertEqual(("id", 7, "vec3", "readonly lvalue"), (
            read.kind, read.symbol_id, read.type.display(), read.category))
        self.assertEqual(
            "df251d3d8461278afd63b36f1f3cef0d48777196908b8571a11d65dc54b83880",
            hashlib.sha256(repr(read).encode()).hexdigest())
        self.assertIs(typed, apply_smooth_edge_luma_weights(
            typed, entry["raw_sha256"], PROFILE))

        mutations = {
            "key": dataclasses.replace(typed, key="filter/other:other"),
            "declaration": dataclasses.replace(
                typed, declarations=(*typed.declarations[:6], dataclasses.replace(
                    declaration, symbol=dataclasses.replace(
                        declaration.symbol, name="OTHER")))),
            "functions": dataclasses.replace(
                typed, functions=(*typed.functions,
                                  dataclasses.replace(typed.functions[0]))),
        }
        for name, candidate in mutations.items():
            with self.subTest(mutation=name), self.assertRaises(ValueError):
                authenticate_smooth_edge_luma_weights(
                    candidate, entry["raw_sha256"], PROFILE)
        for source_hash, profile in (
                ("0" * 64, PROFILE), (entry["raw_sha256"], None),
                (entry["raw_sha256"], "wrong")):
            with self.subTest(source_hash=source_hash, profile=profile), \
                    self.assertRaises(ValueError):
                authenticate_smooth_edge_luma_weights(
                    typed, source_hash, profile)

    # The census half is NOT a historical reconstruction; see the note on
    # test_task21_degauss_exclusions_remain_closed. The narrow exclusion set
    # leaves later-added programs present in the resulting list.
    def test_task26_loader_admits_only_exact_smooth_carrier_and_census(self) -> None:
        import copy
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.frontend.smooth_edge_luma_weights_profile import (
            PROFILE, SMOOTH_EDGE_KEY)

        spec = generate_typed_slice.load_slice(REPOSITORY)
        typed = tuple(item["program_key"] for item in spec["programs"]
                      if item["program_key"] not in {
                          "filter/rotate:rot", "mixer/focusBlur:focusBlur",
                          "filter/extrude:extrude", "synth/curl:curl",
                          "filter/grade:creative", "filter/grade:hslSecondary",
                          "filter/grade:lut", "filter/grade:primary",
                          "filter/grade:vignette", "filter/grade:wheels"})
        public = tuple(sorted((*typed, "filter/invert:inv", "synth/solid:solid")))
        corpus = json.loads((check_corpus._corpus_root(REPOSITORY) /
                             "manifest.json").read_text())
        unported = tuple(sorted(
            {item["program_key"] for item in corpus["programs"]} - set(public)))
        self.assertEqual(typed, tuple(sorted(set(typed))))
        self.assertEqual((127, 129, 83, 212),
                         (len(typed), len(public), len(unported),
                          len(corpus["programs"])))
        self.assertEqual(77, typed.index(SMOOTH_EDGE_KEY))
        self.assertEqual(("filter/skew:skew", SMOOTH_EDGE_KEY,
                          "filter/smoothstep:smoothstep"), typed[76:79])
        self.assertEqual(
            "ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72",
            hashlib.sha256(("\n".join(typed) + "\n").encode()).hexdigest())
        self.assertEqual(
            "37e41894bc62b658a3454e13ab60fe814baf2492fa2a74b0f4305e05480a7883",
            hashlib.sha256(("\n".join(public) + "\n").encode()).hexdigest())
        carriers = [(item["program_key"],
                     item.get("smooth_edge_luma_weights_profile"),
                     item["defines"])
                    for item in spec["programs"]
                    if "smooth_edge_luma_weights_profile" in item]
        self.assertEqual([(SMOOTH_EDGE_KEY, PROFILE, {})], carriers)

        original = json.loads(
            (REPOSITORY / "tools/glslcpp/typed_slice.json").read_text())
        mutations = {}
        changed = copy.deepcopy(original)
        next(item for item in changed["programs"]
             if item["program_key"] == SMOOTH_EDGE_KEY).pop(
                 "smooth_edge_luma_weights_profile")
        mutations["missing"] = changed
        changed = copy.deepcopy(original)
        next(item for item in changed["programs"]
             if item["program_key"] == SMOOTH_EDGE_KEY)[
                 "smooth_edge_luma_weights_profile"] = "wrong"
        mutations["wrong"] = changed
        changed = copy.deepcopy(original)
        next(item for item in changed["programs"]
             if item["program_key"] != SMOOTH_EDGE_KEY)[
                 "smooth_edge_luma_weights_profile"] = PROFILE
        mutations["foreign"] = changed
        changed = copy.deepcopy(original)
        changed["programs"].append(copy.deepcopy(next(
            item for item in changed["programs"]
            if item["program_key"] == SMOOTH_EDGE_KEY)))
        mutations["duplicate"] = changed
        for name, candidate in mutations.items():
            with self.subTest(mutation=name), tempfile.TemporaryDirectory() as temporary:
                repository = pathlib.Path(temporary)
                path = repository / "tools/glslcpp/typed_slice.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(candidate))
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.load_slice(repository)

    def test_task26_validator_and_emitter_independently_authorize_exact_declaration(self) -> None:
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.smooth_edge_luma_weights_profile import (
            PROFILE, SMOOTH_EDGE_KEY)

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == SMOOTH_EDGE_KEY)
        typed = analyze_program(parse_program(
            (root / entry["source"]).read_text(), SMOOTH_EDGE_KEY, {}),
            SMOOTH_EDGE_KEY)
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                typed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=entry["raw_sha256"])
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=entry["raw_sha256"],
            smooth_edge_luma_weights_profile=PROFILE)
        emitted = render_typed_cpp(
            typed, SMOOTH_EDGE_KEY, entry["raw_sha256"],
            smooth_edge_luma_weights_profile=PROFILE)
        local = (
            "const glsl::Vec3 LUMA_WEIGHTS = glsl::FloatExpr<3>("
            "static_cast<float>(0.299), static_cast<float>(0.587), "
            "static_cast<float>(0.114));")
        self.assertEqual(1, emitted.count(local))
        self.assertLess(emitted.index(local),
                        emitted.index("glsl::dot(rgb, LUMA_WEIGHTS)"))
        pixel = emitted[emitted.index("void pixel("):]
        self.assertNotIn("LUMA_WEIGHTS", pixel)
        state = emitted[emitted.index("struct State final"):
                        emitted.index("};", emitted.index("struct State final"))]
        self.assertNotIn("LUMA_WEIGHTS", state)
        self.assertNotRegex(emitted, r"(?m)^(?:static|thread_local|const glsl::Vec3) .*LUMA_WEIGHTS")

    def test_task26_generation_adds_only_smooth_block_manifest_and_catalog(self) -> None:
        import copy
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.smooth_edge_luma_weights_profile import (
            PROFILE, SMOOTH_EDGE_KEY)

        spec = generate_typed_slice.load_slice(REPOSITORY)
        task26_spec = copy.deepcopy(spec)
        task26_spec["programs"] = [
            item for item in task26_spec["programs"]
            if item["program_key"] not in {
                "synth/perlin:perlin", "filter/rotate:rot",
                "mixer/focusBlur:focusBlur", "filter/extrude:extrude",
                "synth/curl:curl",
                "filter/grade:creative", "filter/grade:hslSecondary",
                "filter/grade:lut", "filter/grade:primary",
                "filter/grade:vignette", "filter/grade:wheels"}]
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=task26_spec):
            current = generate_typed_slice.generate_outputs(REPOSITORY)
        self.assertNotIn("synth/perlin:perlin", {
            item["program_key"] for item in task26_spec["programs"]})
        current["include/noisemaker/generated/catalog.hpp"] = (
            generate_typed_slice.render_catalog_header(task26_spec))
        prior_spec = copy.deepcopy(task26_spec)
        prior_spec["programs"] = [
            item for item in prior_spec["programs"]
            if item["program_key"] != SMOOTH_EDGE_KEY]
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=prior_spec):
            prior = generate_typed_slice.generate_outputs(REPOSITORY)
        prior["include/noisemaker/generated/catalog.hpp"] = (
            generate_typed_slice.render_catalog_header(prior_spec))

        marker = re.compile(r"(?m)^// Typed IR program: ([^\n]+)\n")
        def blocks(payload):
            source = payload.decode()
            starts = list(marker.finditer(source))
            catalog = source.index(
                "\nnamespace {\nconstexpr std::array<KernelFactory")
            return {
                match.group(1): source[
                    match.start():(starts[index + 1].start()
                                   if index + 1 < len(starts) else catalog)]
                for index, match in enumerate(starts)
            }

        current_blocks = blocks(current["src/typed_generated/typed_slice.cpp"])
        prior_blocks = blocks(prior["src/typed_generated/typed_slice.cpp"])
        self.assertEqual(126, len(current_blocks))
        self.assertEqual({SMOOTH_EDGE_KEY},
                         set(current_blocks) - set(prior_blocks))
        ordinal = re.compile(r"typed_[0-9]+")
        for key, block in prior_blocks.items():
            with self.subTest(historical_block=key):
                self.assertEqual(
                    ordinal.sub("typed_SENTINEL", block),
                    ordinal.sub("typed_SENTINEL", current_blocks[key]))
                self.assertNotIn("LUMA_WEIGHTS", block)
        smooth = current_blocks[SMOOTH_EDGE_KEY]
        self.assertIn("namespace typed_77 {", smooth)
        self.assertEqual(1, smooth.count("const glsl::Vec3 LUMA_WEIGHTS"))
        self.assertEqual(1, smooth.count("glsl::dot(rgb, LUMA_WEIGHTS)"))
        self.assertEqual(6, smooth.count("fetch_texel(*state.inputTex"))
        self.assertEqual(1, smooth.count("texture_size(*state.inputTex"))
        self.assertNotRegex(
            smooth,
            r"\b(?:static|thread_local|new|throw|alloca)\b|"
            r"std::(?:array|vector|map|variant|function|allocator|string)")

        current_manifest = json.loads(
            current["src/typed_generated/typed_manifest.json"])
        prior_manifest = json.loads(
            prior["src/typed_generated/typed_manifest.json"])
        current_rows = {item["program_key"]: item
                        for item in current_manifest["programs"]}
        prior_rows = {item["program_key"]: item
                      for item in prior_manifest["programs"]}
        self.assertEqual({SMOOTH_EDGE_KEY}, set(current_rows) - set(prior_rows))
        for key, row in prior_rows.items():
            self.assertEqual(
                {name: value for name, value in row.items()
                 if name != "output_sha256"},
                {name: value for name, value in current_rows[key].items()
                 if name != "output_sha256"}, key)
        self.assertEqual(PROFILE, current_rows[SMOOTH_EDGE_KEY][
            "smooth_edge_luma_weights_profile"])
        self.assertFalse(any(
            "smooth_edge_luma_weights_profile" in row
            for key, row in current_rows.items() if key != SMOOTH_EDGE_KEY))

        declaration = (
            "[[nodiscard]] BoundKernel bind_filter_smooth_smoothEdge("
            "const glsl::Bindings& bindings);\n")
        current_header = current[
            "include/noisemaker/generated/catalog.hpp"].decode()
        self.assertEqual(1, current_header.count(declaration))
        self.assertEqual(
            prior["include/noisemaker/generated/catalog.hpp"].decode(),
            current_header.replace(declaration, ""))

    def test_task26_exhaustive_profile_validator_and_emitter_negative_closure(self) -> None:
        import dataclasses
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.smooth_edge_luma_weights_profile import (
            PROFILE, SMOOTH_EDGE_KEY,
            authenticate_smooth_edge_luma_weights)

        root = check_corpus._corpus_root(REPOSITORY)
        manifest = json.loads((root / "manifest.json").read_text())
        entry = next(item for item in manifest["programs"]
                     if item["program_key"] == SMOOTH_EDGE_KEY)
        raw = (root / entry["source"]).read_text()
        exact = analyze_program(parse_program(raw, SMOOTH_EDGE_KEY, {}),
                                SMOOTH_EDGE_KEY)
        source_hash = entry["raw_sha256"]
        declaration = exact.declarations[6]
        initializer = declaration.initializer
        self.assertIsNotNone(initializer)
        luminance, main = exact.functions
        parent = luminance.body[0].expressions[0]
        read = parent.children[1]
        rgb = parent.children[0]

        mutation_shapes = analyze_program(parse_program(
            "out vec4 color;\n"
            "void escape(inout vec3 value) { value = vec3(0.0); }\n"
            "void main() { vec3 local = vec3(1.0); escape(local); "
            "color = vec4(local, 1.0); }\n",
            "task26:mutation-shapes", {}), "task26:mutation-shapes")
        assignment_statement = mutation_shapes.functions[0].body[0]
        escape_call_statement = mutation_shapes.functions[1].body[1]

        def replace_expression(program, target, replacement):
            def expression(value):
                if value is target:
                    return replacement
                return dataclasses.replace(
                    value, children=tuple(expression(child)
                                          for child in value.children))
            def statement(value):
                return dataclasses.replace(
                    value,
                    expressions=tuple(expression(item)
                                      for item in value.expressions),
                    children=tuple(statement(child)
                                   for child in value.children))
            return dataclasses.replace(
                program,
                functions=tuple(dataclasses.replace(
                    function,
                    body=tuple(statement(item) for item in function.body))
                    for function in program.functions))

        def replace_signature_calls(program, old_id, new_id):
            def expression(value):
                replacement_id = (new_id if value.kind == "call" and
                                  value.signature_id == old_id else
                                  value.signature_id)
                return dataclasses.replace(
                    value, signature_id=replacement_id,
                    children=tuple(expression(child)
                                   for child in value.children))
            def statement(value):
                return dataclasses.replace(
                    value,
                    expressions=tuple(expression(item)
                                      for item in value.expressions),
                    children=tuple(statement(child)
                                   for child in value.children))
            return dataclasses.replace(
                program,
                functions=tuple(dataclasses.replace(
                    function,
                    body=tuple(statement(item) for item in function.body))
                    for function in program.functions))

        calls = []
        def collect_expression(value):
            if value.kind == "call" and value.signature_id == luminance.id:
                calls.append(value)
            for child in value.children:
                collect_expression(child)
        def collect_statement(value):
            for item in value.expressions:
                collect_expression(item)
            for child in value.children:
                collect_statement(child)
        for statement in main.body:
            collect_statement(statement)
        self.assertEqual(5, len(calls))

        wrong_source_path = dataclasses.replace(
            declaration.span, program_key="forged/source:path")
        wrong_declaration_span = dataclasses.replace(
            declaration.span, start_column=2)
        wrong_symbol = dataclasses.replace(declaration.symbol, name="OTHER")
        wrong_declaration = dataclasses.replace(
            declaration, symbol=wrong_symbol)
        changed_lane = dataclasses.replace(
            initializer.children[0], literal_value=0.3)
        changed_parent = dataclasses.replace(parent, callee="max")
        changed_read = dataclasses.replace(read, symbol_id=8, symbol=rgb.symbol)

        owned_signature_id = 90
        owned_program = replace_signature_calls(
            exact, luminance.id, owned_signature_id)
        owned_program = dataclasses.replace(
            owned_program,
            functions=(dataclasses.replace(
                owned_program.functions[0],
                signature=dataclasses.replace(
                    owned_program.functions[0].signature,
                    id=owned_signature_id)),
                       owned_program.functions[1]))

        assignment_expression = dataclasses.replace(
            assignment_statement.expressions[0],
            type=declaration.type,
            span=parent.span,
            children=(read, initializer),
            category="rvalue")
        declaration_write_statement = dataclasses.replace(
            assignment_statement,
            span=luminance.body[0].span,
            expressions=(assignment_expression,))
        declaration_write = dataclasses.replace(
            exact, functions=(dataclasses.replace(
                luminance,
                body=(declaration_write_statement, *luminance.body)), main))

        escape_signature_id = 901
        escape_parameter = dataclasses.replace(
            luminance.parameters[0], id=900, name="escaped_weights",
            type=declaration.type, storage="parameter", writable=True,
            direction="inout", span=read.span)
        escape_function = dataclasses.replace(
            luminance,
            signature=dataclasses.replace(
                luminance.signature, id=escape_signature_id, name="escape",
                return_type=main.signature.return_type,
                parameters=(escape_parameter,)),
            body=())
        escape_call_expression = dataclasses.replace(
            escape_call_statement.expressions[0],
            type=main.signature.return_type,
            span=read.span,
            signature_id=escape_signature_id,
            callee="escape",
            children=(read,))
        declaration_escape_statement = dataclasses.replace(
            escape_call_statement,
            span=luminance.body[0].span,
            expressions=(escape_call_expression,))
        declaration_escape = dataclasses.replace(
            exact,
            functions=(escape_function,
                       dataclasses.replace(
                           luminance,
                           body=(declaration_escape_statement,
                                 *luminance.body)),
                       main))

        mutations = {
            "program-key": dataclasses.replace(exact, key="filter/other:other"),
            "normalized-source": dataclasses.replace(exact, source=exact.source + " "),
            "raw-source": dataclasses.replace(exact, raw_source=exact.raw_source + " "),
            "defines": dataclasses.replace(exact, preprocessor_defines=(object(),)),
            "body-status": dataclasses.replace(exact, body_status="not analyzed"),
            "resource-uniform-order": dataclasses.replace(
                exact, resources=dataclasses.replace(
                    exact.resources,
                    uniforms=tuple(reversed(exact.resources.uniforms)))),
            "resource-sampler-name": dataclasses.replace(
                exact, resources=dataclasses.replace(
                    exact.resources, samplers=("otherTex",))),
            "resource-output-name": dataclasses.replace(
                exact, resources=dataclasses.replace(
                    exact.resources, outputs=("otherColor",))),
            "resource-derivative": dataclasses.replace(
                exact, resources=dataclasses.replace(
                    exact.resources, uses_derivatives=True)),
            "interface-order": dataclasses.replace(
                exact, declarations=(exact.declarations[1],
                                     exact.declarations[0],
                                     *exact.declarations[2:])),
            "interface-name": dataclasses.replace(
                exact, declarations=(dataclasses.replace(
                    exact.declarations[0], symbol=dataclasses.replace(
                        exact.declarations[0].symbol, name="other")),
                    *exact.declarations[1:])),
            "interface-binding-id": dataclasses.replace(
                exact, declarations=(dataclasses.replace(
                    exact.declarations[0], symbol=dataclasses.replace(
                        exact.declarations[0].symbol, id=999)),
                    *exact.declarations[1:])),
            "builtin-interface": dataclasses.replace(
                exact, builtin_symbols=exact.builtin_symbols[:-1]),
            "loop-proof-count": dataclasses.replace(
                exact, counted_loop_proof=dataclasses.replace(
                    exact.counted_loop_proof, loop_count=1)),
            "recursion-proof": dataclasses.replace(
                exact, counted_loop_proof=dataclasses.replace(
                    exact.counted_loop_proof, call_graph_acyclic=False)),
            "unrelated-proof": dataclasses.replace(
                exact, fixed_nine_table_proof=object()),
            "declaration-id": dataclasses.replace(
                exact, declarations=(*exact.declarations[:6],
                                     dataclasses.replace(
                                         declaration,
                                         symbol=dataclasses.replace(
                                             declaration.symbol, id=700)))),
            "declaration-name": dataclasses.replace(
                exact, declarations=(*exact.declarations[:6],
                                     wrong_declaration)),
            "declaration-storage": dataclasses.replace(
                exact, declarations=(*exact.declarations[:6],
                                     dataclasses.replace(
                                         declaration,
                                         symbol=dataclasses.replace(
                                             declaration.symbol,
                                             storage="uniform")))),
            "declaration-writable": dataclasses.replace(
                exact, declarations=(*exact.declarations[:6],
                                     dataclasses.replace(
                                         declaration,
                                         symbol=dataclasses.replace(
                                             declaration.symbol,
                                             writable=True)))),
            "declaration-type": dataclasses.replace(
                exact, declarations=(*exact.declarations[:6],
                                     dataclasses.replace(
                                         declaration,
                                         type=initializer.children[0].type))),
            "declaration-source-path": dataclasses.replace(
                exact, declarations=(*exact.declarations[:6],
                                     dataclasses.replace(
                                         declaration,
                                         span=wrong_source_path))),
            "declaration-span": dataclasses.replace(
                exact, declarations=(*exact.declarations[:6],
                                     dataclasses.replace(
                                         declaration,
                                         span=wrong_declaration_span))),
            "declaration-position": dataclasses.replace(
                exact, declarations=(declaration, *exact.declarations[:6])),
            "second-equal-declaration": dataclasses.replace(
                exact, declarations=(*exact.declarations,
                                     dataclasses.replace(declaration))),
            "initializer-kind": dataclasses.replace(
                exact, declarations=(*exact.declarations[:6],
                                     dataclasses.replace(
                                         declaration,
                                         initializer=dataclasses.replace(
                                             initializer, kind="literal")))),
            "constructor-arity": dataclasses.replace(
                exact, declarations=(*exact.declarations[:6],
                                     dataclasses.replace(
                                         declaration,
                                         initializer=dataclasses.replace(
                                             initializer,
                                             children=initializer.children[:2])))),
            "literal-spelling": dataclasses.replace(
                exact, declarations=(*exact.declarations[:6],
                                     dataclasses.replace(
                                         declaration,
                                         initializer=dataclasses.replace(
                                             initializer, children=(
                                                 dataclasses.replace(
                                                     initializer.children[0],
                                                     literal="0.2990"),
                                                 *initializer.children[1:]))))),
            "literal-order": dataclasses.replace(
                exact, declarations=(*exact.declarations[:6],
                                     dataclasses.replace(
                                         declaration,
                                         initializer=dataclasses.replace(
                                             initializer, children=(
                                                 initializer.children[2],
                                                 initializer.children[1],
                                                 initializer.children[0]))))),
            "literal-f32-bits": dataclasses.replace(
                exact, declarations=(*exact.declarations[:6],
                                     dataclasses.replace(
                                         declaration,
                                         initializer=dataclasses.replace(
                                             initializer, children=(
                                                 changed_lane,
                                                 *initializer.children[1:]))))),
            "function-id": dataclasses.replace(
                exact, functions=(dataclasses.replace(
                    luminance, signature=dataclasses.replace(
                        luminance.signature, id=90)), main)),
            "function-name": dataclasses.replace(
                exact, functions=(dataclasses.replace(
                    luminance, signature=dataclasses.replace(
                        luminance.signature, name="other")), main)),
            "function-signature": dataclasses.replace(
                exact, functions=(dataclasses.replace(
                    luminance, signature=dataclasses.replace(
                        luminance.signature, return_type=declaration.type)), main)),
            "parameter-name": dataclasses.replace(
                exact, functions=(dataclasses.replace(
                    luminance, signature=dataclasses.replace(
                        luminance.signature, parameters=(dataclasses.replace(
                            luminance.parameters[0], name="other"),))), main)),
            "body-size": dataclasses.replace(
                exact, functions=(dataclasses.replace(
                    luminance, body=(*luminance.body, luminance.body[0])), main)),
            "read-missing": replace_expression(exact, read, rgb),
            "read-symbol": replace_expression(exact, read, changed_read),
            "second-read": dataclasses.replace(
                exact, functions=(dataclasses.replace(
                    luminance, body=(*luminance.body, luminance.body[0])), main)),
            "function-owner-signature": owned_program,
            "dot-parent": replace_expression(exact, parent, changed_parent),
            "dot-child-role": replace_expression(
                exact, parent, dataclasses.replace(
                    parent, children=(read, rgb))),
            "dot-first-argument": replace_expression(
                exact, parent, dataclasses.replace(
                    parent, children=(read, read))),
            "write": declaration_write,
            "reference-escape": declaration_escape,
            "call-count": replace_expression(
                exact, calls[0], dataclasses.replace(calls[0], signature_id=999)),
        }

        def program_expressions(program):
            found = []
            def expression(value):
                found.append(value)
                for child in value.children:
                    expression(child)
            def statement(value):
                for item in value.expressions:
                    expression(item)
                for child in value.children:
                    statement(child)
            for function in program.functions:
                for item in function.body:
                    statement(item)
            return found

        def reads_of(program, symbol_id):
            return [value for value in program_expressions(program)
                    if value.kind == "id" and value.symbol_id == symbol_id]

        def calls_of(program, signature_id):
            return [value for value in program_expressions(program)
                    if value.kind == "call" and
                    value.signature_id == signature_id]

        mutation_preconditions = {
            "program-key": lambda p: p.key == "filter/other:other",
            "normalized-source": lambda p: p.source == exact.source + " ",
            "raw-source": lambda p: p.raw_source == exact.raw_source + " ",
            "defines": lambda p: len(p.preprocessor_defines) == 1,
            "body-status": lambda p: p.body_status == "not analyzed",
            "resource-uniform-order": lambda p: (
                p.resources.uniforms == tuple(reversed(
                    exact.resources.uniforms))),
            "resource-sampler-name": lambda p: (
                p.resources.samplers == ("otherTex",)),
            "resource-output-name": lambda p: (
                p.resources.outputs == ("otherColor",)),
            "resource-derivative": lambda p: p.resources.uses_derivatives,
            "interface-order": lambda p: (
                p.declarations[0] == exact.declarations[1] and
                p.declarations[1] == exact.declarations[0]),
            "interface-name": lambda p: (
                p.declarations[0].symbol.name == "other"),
            "interface-binding-id": lambda p: (
                p.declarations[0].symbol.id == 999),
            "builtin-interface": lambda p: (
                len(p.builtin_symbols) == len(exact.builtin_symbols) - 1),
            "loop-proof-count": lambda p: p.counted_loop_proof.loop_count == 1,
            "recursion-proof": lambda p: (
                not p.counted_loop_proof.call_graph_acyclic),
            "unrelated-proof": lambda p: (
                p.fixed_nine_table_proof is not
                exact.fixed_nine_table_proof),
            "declaration-id": lambda p: p.declarations[6].symbol.id == 700,
            "declaration-name": lambda p: (
                p.declarations[6].symbol.name == "OTHER"),
            "declaration-storage": lambda p: (
                p.declarations[6].symbol.storage == "uniform"),
            "declaration-writable": lambda p: (
                p.declarations[6].symbol.writable),
            "declaration-type": lambda p: (
                p.declarations[6].type == initializer.children[0].type),
            "declaration-source-path": lambda p: (
                p.declarations[6].span.program_key == "forged/source:path" and
                p.declarations[6].span.start_column ==
                declaration.span.start_column),
            "declaration-span": lambda p: (
                p.declarations[6].span.program_key ==
                declaration.span.program_key and
                p.declarations[6].span.start_column == 2),
            "declaration-position": lambda p: (
                p.declarations[0] == declaration),
            "second-equal-declaration": lambda p: (
                len(p.declarations) == len(exact.declarations) + 1 and
                p.declarations[-1] == declaration),
            "initializer-kind": lambda p: (
                p.declarations[6].initializer.kind == "literal"),
            "constructor-arity": lambda p: (
                len(p.declarations[6].initializer.children) == 2),
            "literal-spelling": lambda p: (
                p.declarations[6].initializer.children[0].literal ==
                "0.2990"),
            "literal-order": lambda p: (
                p.declarations[6].initializer.children == tuple(reversed(
                    initializer.children))),
            "literal-f32-bits": lambda p: (
                p.declarations[6].initializer.children[0].literal_value ==
                0.3),
            "function-id": lambda p: p.functions[0].id == 90,
            "function-name": lambda p: p.functions[0].name == "other",
            "function-signature": lambda p: (
                p.functions[0].signature.return_type == declaration.type),
            "parameter-name": lambda p: (
                p.functions[0].parameters[0].name == "other"),
            "body-size": lambda p: len(p.functions[0].body) == 2,
            "read-missing": lambda p: len(reads_of(p, 7)) == 0,
            "read-symbol": lambda p: (
                len(reads_of(p, 8)) >= 1 and
                any(value.symbol == rgb.symbol for value in reads_of(p, 8))),
            "second-read": lambda p: len(reads_of(p, 7)) == 2,
            "function-owner-signature": lambda p: (
                p.functions[0].id == owned_signature_id and
                len(reads_of(p, 7)) == 1 and
                len(calls_of(p, owned_signature_id)) == 5 and
                len(calls_of(p, luminance.id)) == 0),
            "dot-parent": lambda p: any(
                value.kind == "builtin" and value.callee == "max"
                for value in program_expressions(p)),
            "dot-child-role": lambda p: any(
                value.kind == "builtin" and value.callee == "dot" and
                tuple(child.symbol_id for child in value.children) == (7, 8)
                for value in program_expressions(p)),
            "dot-first-argument": lambda p: any(
                value.kind == "builtin" and value.callee == "dot" and
                tuple(child.symbol_id for child in value.children) == (7, 7)
                for value in program_expressions(p)),
            "write": lambda p: (
                len(p.functions[0].body) == 2 and
                p.functions[0].body[0].kind == "expr" and
                p.functions[0].body[0].expressions[0].kind == "assign" and
                p.functions[0].body[0].expressions[0].operator == "=" and
                p.functions[0].body[0].expressions[0].children[0].symbol_id ==
                declaration.symbol.id and
                p.functions[0].body[0].expressions[0].children[1] ==
                initializer),
            "reference-escape": lambda p: (
                len(p.functions) == 3 and
                p.functions[0].id == escape_signature_id and
                p.functions[0].parameters[0].direction == "inout" and
                len(calls_of(p, escape_signature_id)) == 1 and
                calls_of(p, escape_signature_id)[0].children[0].symbol_id ==
                declaration.symbol.id),
            "call-count": lambda p: (
                len(calls_of(p, luminance.id)) == 4 and
                len(calls_of(p, 999)) == 1),
        }
        self.assertEqual(set(mutations), set(mutation_preconditions))
        self.assertEqual(len(mutations), len(set(mutations)))

        for label, candidate in mutations.items():
            self.assertNotEqual(exact, candidate, label)
            with self.subTest(case=label, boundary="structural-precondition"):
                self.assertTrue(mutation_preconditions[label](candidate), label)
            with self.subTest(case=label, boundary="profile"), \
                    self.assertRaises(ValueError):
                authenticate_smooth_edge_luma_weights(
                    candidate, source_hash, PROFILE)
            with self.subTest(case=label, boundary="validator"), \
                    self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash,
                    smooth_edge_luma_weights_profile=PROFILE)
            with self.subTest(case=label, boundary="emitter"), \
                    self.assertRaises(TypedEmissionError):
                render_typed_cpp(
                    candidate, candidate.key, source_hash,
                    smooth_edge_luma_weights_profile=PROFILE)

        forged_without_global = dataclasses.replace(
            exact, declarations=exact.declarations[:6])
        modes = (
            (exact, None, source_hash, False, "exact-absent"),
            (exact, PROFILE, source_hash, True, "exact-exact"),
            (forged_without_global, None, source_hash, False, "forged-absent"),
            (forged_without_global, PROFILE, source_hash, False, "forged-exact"),
            (exact, PROFILE, "0" * 64, False, "wrong-caller-hash"),
            (dataclasses.replace(exact, key="foreign:key"), PROFILE,
             source_hash, False, "foreign-carrier"),
        )
        for candidate, carrier, caller_hash, accepted, label in modes:
            if accepted:
                authenticate_smooth_edge_luma_weights(
                    candidate, caller_hash, carrier)
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=caller_hash,
                    smooth_edge_luma_weights_profile=carrier)
                render_typed_cpp(
                    candidate, candidate.key, caller_hash,
                    smooth_edge_luma_weights_profile=carrier)
                continue
            with self.subTest(mode=label, boundary="profile"), \
                    self.assertRaises(ValueError):
                authenticate_smooth_edge_luma_weights(
                    candidate, caller_hash, carrier)
            with self.subTest(mode=label, boundary="validator"), \
                    self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=caller_hash,
                    smooth_edge_luma_weights_profile=carrier)
            with self.subTest(mode=label, boundary="emitter"), \
                    self.assertRaises(TypedEmissionError):
                render_typed_cpp(
                    candidate, candidate.key, caller_hash,
                    smooth_edge_luma_weights_profile=carrier)

        foreign_carriers = (
            {"numeric_literal_contract": "source-double"},
            {"compatibility_transform": "coalesce-uv-alias-v1"},
            {"custom_comparer_profile": "lens-comparer-v1"},
            {"source_global_literal_int_profile":
             "source-global-literal-int-v1"},
            {"gather_sorted_round_profile": "gather-round-v1"},
            {"literal_vec3_lane_index_profile": "literal-vec3-v1"},
        )
        for kwargs in foreign_carriers:
            with self.subTest(carrier=kwargs, boundary="validator"), \
                    self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    exact, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash,
                    smooth_edge_luma_weights_profile=PROFILE, **kwargs)
            with self.subTest(carrier=kwargs, boundary="emitter"), \
                    self.assertRaises(TypedEmissionError):
                render_typed_cpp(
                    exact, exact.key, source_hash,
                    smooth_edge_luma_weights_profile=PROFILE, **kwargs)

        emitted = render_typed_cpp(
            exact, exact.key, source_hash,
            smooth_edge_luma_weights_profile=PROFILE)
        helper = emitted[emitted.index("double luminance(",
                                       emitted.index("double luminance(") + 1):
                         emitted.index("\n}\n\nvoid pixel(")]
        local = ("const glsl::Vec3 LUMA_WEIGHTS = glsl::FloatExpr<3>("
                 "static_cast<float>(0.299), static_cast<float>(0.587), "
                 "static_cast<float>(0.114));")
        self.assertEqual(1, emitted.count(local))
        self.assertEqual(1, helper.count(local))
        self.assertLess(helper.index(local),
                        helper.index("glsl::dot(rgb, LUMA_WEIGHTS)"))
        self.assertNotRegex(
            emitted,
            r"(?:static|thread_local).*LUMA_WEIGHTS|"
            r"LUMA_WEIGHTS.*(?:new|alloca)|"
            r"std::(?:array|vector|map).*LUMA_WEIGHTS|"
            r"\[.*LUMA_WEIGHTS.*\]")

    def test_task26_generation_driver_rejects_identity_forgery_after_profile_apply(self) -> None:
        import dataclasses
        from tools.glslcpp import generate_typed_slice

        real_apply = generate_typed_slice.apply_smooth_edge_luma_weights
        def forged_apply(program, source_hash, profile):
            authenticated = real_apply(program, source_hash, profile)
            return dataclasses.replace(authenticated)

        with mock.patch.object(
                generate_typed_slice, "apply_smooth_edge_luma_weights",
                side_effect=forged_apply), self.assertRaisesRegex(
                    generate_typed_slice.GeneratorError,
                    "Smooth Edge LUMA weights identity profile mutated program"):
            generate_typed_slice.generate_outputs(REPOSITORY)

    def test_task26_cpp_native_oracle_table_is_exact_frozen_transcription(self) -> None:
        import hashlib
        import struct

        oracle_path = pathlib.Path(
            REPOSITORY / "tests/oracles/task-26-oracles.json")
        self.assertTrue(oracle_path.is_file(), "Task 26 frozen oracle JSON is required")
        oracle_bytes = oracle_path.read_bytes()
        self.assertEqual(
            "7975cbe59733df0178956b7f145e03c2e872e269327d9f8dd1126c3bb9c3ccf9",
            hashlib.sha256(oracle_bytes).hexdigest())
        oracle = json.loads(oracle_bytes)

        cpp = (REPOSITORY / "tests/test_generated_kernels.cpp").read_text()
        executable = _task26_parse_executable_tables(cpp)
        self.assertEqual(
            (8, 11, 88),
            (len(executable["cases"]), len(executable["names"]),
             len(executable["results"])))
        begin = "// TASK26_NATIVE_ORACLE_TABLE_BEGIN"
        end = "// TASK26_NATIVE_ORACLE_TABLE_END"
        self.assertEqual(1, cpp.count(begin))
        self.assertEqual(1, cpp.count(end))
        table_source = cpp[cpp.index(begin) + len(begin):cpp.index(end)]
        chunks = re.findall(
            r'R"TASK26\((.*?)\)TASK26"', table_source, re.DOTALL)
        self.assertGreaterEqual(len(chunks), 2)
        embedded_bytes = "".join(chunks).encode()
        self.assertEqual(oracle_bytes, embedded_bytes)
        self.assertEqual(oracle, json.loads(embedded_bytes))
        self.assertEqual(8, len(oracle["cases"]))
        self.assertEqual(11, len(oracle["mutations"]))
        self.assertEqual(88, sum(len(item["case_results"])
                                 for item in oracle["mutations"]))

        def f32_bits(value):
            return int.from_bytes(struct.pack("<f", float(value)), "little")

        def probes(items):
            return [component
                    for probe in items
                    for component in (
                        *probe["at_top_down_xy"],
                        *(int(bits, 16) for bits in probe["f32_bits_le"]))]

        expected_cases = []
        for index, case in enumerate(oracle["cases"]):
            expected_cases.append([
                index,
                case["name"],
                case["dimensions"]["width"],
                case["dimensions"]["height"],
                case["smooth_type"],
                int(case["threshold"]["f32_bits_le"], 16),
                [f32_bits(value) for value in case["tile_offset"]],
                [f32_bits(value) for value in case["full_resolution"]],
                case["input"]["f32_sha256"],
                probes(case["input"]["probes"]),
                case["output"]["f32_sha256"],
                case["output"]["rgba8_sha256"],
                probes(case["output"]["probes"]),
                case["output"]["finite_lanes"],
                case["output"]["nonfinite_lanes"],
            ])
        expected_names = [item["id"] for item in oracle["mutations"]]
        case_indices = {case["name"]: index
                        for index, case in enumerate(oracle["cases"])}
        expected_results = []
        for mutation_index, mutation in enumerate(oracle["mutations"]):
            for result in mutation["case_results"]:
                expected_results.append([
                    mutation_index,
                    case_indices[result["case"]],
                    result["same_f32_bytes"],
                    result["same_rgba8_bytes"],
                    result["different_f32_bytes"],
                    result["different_f32_lanes"],
                    result["different_rgba8_bytes"],
                    result["max_absolute_f32_difference"],
                    result["candidate_f32_sha256"],
                    result["candidate_rgba8_sha256"],
                ])
        expected_enum_names = [
            "red_value",
            "green_value",
            "blue_value",
            "red_blue_swap",
            "scalar",
            "vec4_extra",
            "cross_call_mutation",
            "rgb_self_dot",
            "helper_local_exact_f32",
            "helper_local_source_double",
            "main_owned_exact_f32",
        ]

        def enforce_executable_transcription(source):
            parsed = _task26_parse_executable_tables(source)
            self.assertEqual(expected_cases, parsed["cases"])
            self.assertEqual(expected_names, parsed["names"])
            self.assertEqual(expected_results, parsed["results"])
            self.assertEqual(expected_enum_names, parsed["enum_names"])
            self.assertEqual(expected_enum_names, parsed["dispatch_names"])
            self.assertEqual(len(expected_enum_names),
                             len(set(parsed["dispatch_names"])))

        enforce_executable_transcription(cpp)

        def replace_after(source, marker, old, new):
            start = source.index(marker)
            offset = source.index(old, start)
            return source[:offset] + new + source[offset + len(old):]

        executable_tampers = (
            replace_after(
                cpp, "kTask26NativeCases",
                '"pass-through-modular-tile"',
                '"pass-through-modular-tilE"'),
            replace_after(
                cpp, "kTask26MutationNames",
                '"red-value-0.299-to-0.3"',
                '"red-value-0.299-to-0.4"'),
            replace_after(
                cpp, "kTask26MutationResults",
                '"ffaf80acb8db7b255eaf329399e44b5a562a19e82125b19317d436bb07f8fa4b"',
                '"0faf80acb8db7b255eaf329399e44b5a562a19e82125b19317d436bb07f8fa4b"'),
        )
        for table, tampered in zip(("cases", "names", "results"),
                                   executable_tampers):
            with self.subTest(executable_table=table), \
                    self.assertRaises(AssertionError):
                enforce_executable_transcription(tampered)

        self.assertTrue(oracle["provenance"]["canonical_identity"])
        self.assertTrue(oracle["provenance"]["adapter_entry_absent"])
        self.assertEqual(
            "732feb5a9bb518cb46c38b59efb7f2901467fa74ae341f640822d22c20f2380e",
            oracle["program"]["canonical_factory_to_string_sha256"])
        self.assertEqual("sources/filter/smooth/smoothEdge.glsl",
                         oracle["program"]["source"])
        self.assertEqual("smooth-edge-luma-weights-v1",
                         oracle["program"]["profile"])
        self.assertFalse(oracle["program"]["generic_const_vec3_capability"])


class Task27PerlinTests(unittest.TestCase):
    @staticmethod
    def exact_program():
        import hashlib
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program

        key = "synth/perlin:perlin"
        raw = (REPOSITORY / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/perlin/perlin.glsl").read_text()
        return (raw, hashlib.sha256(raw.encode()).hexdigest(),
                analyze_program(parse_program(raw, key, {"DIMENSIONS": 2}), key))

    def test_task27_profile_authenticates_only_exact_nested_scalar_uint_xor(self) -> None:
        import dataclasses
        from tools.glslcpp.frontend.perlin_scalar_uint_xor_profile import (
            PROFILE, apply_perlin_scalar_uint_xor,
            authenticate_perlin_scalar_uint_xor)

        _, source_hash, typed = self.exact_program()
        outer, inner = authenticate_perlin_scalar_uint_xor(
            typed, source_hash, PROFILE)
        self.assertIs(outer.children[0], inner)
        self.assertEqual(("^", "uint", "uint", "uint"),
                         (outer.operator, outer.children[0].type.display(),
                          outer.children[1].type.display(), outer.type.display()))
        self.assertIs(typed, apply_perlin_scalar_uint_xor(
            typed, source_hash, PROFILE))
        for bad_hash, bad_profile in (("0" * 64, PROFILE),
                                      (source_hash, "wrong"),
                                      (source_hash, None)):
            with self.assertRaises(ValueError):
                authenticate_perlin_scalar_uint_xor(typed, bad_hash, bad_profile)
        forged = dataclasses.replace(typed, key="synth/perlin:foreign")
        with self.assertRaises(ValueError):
            authenticate_perlin_scalar_uint_xor(forged, source_hash, PROFILE)

    def test_task27_slice_schema_has_exact_single_perlin_carrier_and_census(self) -> None:
        import hashlib
        from tools.glslcpp import generate_typed_slice

        spec = generate_typed_slice.load_slice(REPOSITORY)
        keys = [item["program_key"] for item in spec["programs"]
                if item["program_key"] not in {
                    "filter/rotate:rot", "mixer/focusBlur:focusBlur",
                    "filter/extrude:extrude", "synth/curl:curl",
                    "filter/grade:creative", "filter/grade:hslSecondary",
                    "filter/grade:lut", "filter/grade:primary",
                    "filter/grade:vignette", "filter/grade:wheels"}]
        self.assertEqual(127, len(keys))
        self.assertEqual(123, keys.index("synth/perlin:perlin"))
        self.assertEqual(
            "ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72",
            hashlib.sha256(("\n".join(keys) + "\n").encode()).hexdigest())
        rows = [item for item in spec["programs"]
                if "perlin_scalar_uint_xor_profile" in item]
        self.assertEqual([{
            "defines": {"DIMENSIONS": 2},
            "perlin_scalar_uint_xor_profile": "perlin-scalar-uint-xor-v1",
            "program_key": "synth/perlin:perlin",
        }], rows)

    def test_task27_validator_admits_only_authenticated_scalar_xor_objects(self) -> None:
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.perlin_scalar_uint_xor_profile import PROFILE

        _, source_hash, typed = self.exact_program()
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash, perlin_scalar_uint_xor_profile=PROFILE)
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                typed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)

    def test_task27_emitter_uses_direct_left_nested_scalar_uint_xor_only(self) -> None:
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.perlin_scalar_uint_xor_profile import PROFILE

        _, source_hash, typed = self.exact_program()
        emitted = render_typed_cpp(
            typed, typed.key, source_hash,
            perlin_scalar_uint_xor_profile=PROFILE)
        start = emitted.index("double hash3(", emitted.index("double hash3(") + 1)
        hash3 = emitted[start:emitted.index("\n}\n", start)]
        self.assertIn(
            "((glsl::swizzle<0>(q) ^ glsl::swizzle<1>(q)) ^ glsl::swizzle<2>(q))",
            hash3)
        self.assertEqual(2, hash3.count(" ^ "))
        self.assertEqual(1, hash3.count("glsl::bitwise_xor"))
        self.assertNotRegex(hash3, r"bitwise_xor\([^\n]*swizzle<0>")
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(typed, typed.key, source_hash)

    def test_task27_generation_wires_exact_profile_manifest_and_catalog(self) -> None:
        import copy
        from tools.glslcpp import generate_typed_slice

        task27_spec = copy.deepcopy(generate_typed_slice.load_slice(REPOSITORY))
        task27_spec["programs"] = [item for item in task27_spec["programs"]
                                   if item["program_key"] not in {
                                       "filter/rotate:rot",
                                       "mixer/focusBlur:focusBlur",
                                       "filter/extrude:extrude",
                                       "synth/curl:curl",
                                       "filter/grade:creative",
                                       "filter/grade:hslSecondary",
                                       "filter/grade:lut",
                                       "filter/grade:primary",
                                       "filter/grade:vignette",
                                       "filter/grade:wheels"}]
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=task27_spec):
            outputs = generate_typed_slice.generate_outputs(REPOSITORY)
        cpp = outputs["src/typed_generated/typed_slice.cpp"].decode()
        manifest = json.loads(outputs["src/typed_generated/typed_manifest.json"])
        header = generate_typed_slice.render_catalog_header(task27_spec).decode()
        self.assertEqual(1, cpp.count(
            "// Typed IR program: synth/perlin:perlin"))
        self.assertIn("bind_synth_perlin_perlin", cpp)
        row = next(item for item in manifest["programs"]
                   if item["program_key"] == "synth/perlin:perlin")
        self.assertEqual("perlin-scalar-uint-xor-v1",
                         row["perlin_scalar_uint_xor_profile"])
        self.assertIn("bind_synth_perlin_perlin", header)

    def test_task27_generation_is_exact_single_program_delta_from_task26(self) -> None:
        import copy
        import hashlib
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.perlin_scalar_uint_xor_profile import (
            PERLIN_KEY, PROFILE)

        spec = generate_typed_slice.load_slice(REPOSITORY)
        spec["programs"] = [item for item in spec["programs"]
                            if item["program_key"] not in {
                                "filter/rotate:rot",
                                "mixer/focusBlur:focusBlur",
                                "filter/extrude:extrude",
                                "synth/curl:curl",
                                "filter/grade:creative",
                                "filter/grade:hslSecondary",
                                "filter/grade:lut",
                                "filter/grade:primary",
                                "filter/grade:vignette",
                                "filter/grade:wheels"}]
        with mock.patch.object(generate_typed_slice, "load_slice", return_value=spec):
            current = generate_typed_slice.generate_outputs(REPOSITORY)
        current_header = generate_typed_slice.render_catalog_header(spec)
        prior_spec = copy.deepcopy(spec)
        prior_spec["programs"] = [
            item for item in prior_spec["programs"]
            if item["program_key"] != PERLIN_KEY]
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=prior_spec):
            prior = generate_typed_slice.generate_outputs(REPOSITORY)
        prior_header = generate_typed_slice.render_catalog_header(prior_spec)

        expected_task26_hashes = {
            "src/typed_generated/typed_slice.cpp":
                "df4aa212f312dcaf12bc348df1b1449a25db52542c97d0bc0350a7a2162b2d38",
            "src/typed_generated/typed_manifest.json":
                "e7f7acd56c96951d5610276cb72ad2df19637f142ae08022b92c2c718a7e7def",
            "include/noisemaker/generated/catalog.hpp":
                "557ccdbee5a58ff6129269ad4a4dfdc25486b8a9f8c455da2bf2c8663d55527d",
        }
        prior_with_header = {**prior,
            "include/noisemaker/generated/catalog.hpp": prior_header}
        for path, expected in expected_task26_hashes.items():
            with self.subTest(task26_artifact=path):
                self.assertEqual(
                    expected, hashlib.sha256(prior_with_header[path]).hexdigest())

        marker = re.compile(r"(?m)^// Typed IR program: ([^\n]+)\n")
        def blocks(payload):
            source = payload.decode()
            starts = list(marker.finditer(source))
            catalog = source.index(
                "\nnamespace {\nconstexpr std::array<KernelFactory")
            return {
                match.group(1): source[
                    match.start():(starts[index + 1].start()
                                   if index + 1 < len(starts) else catalog)]
                for index, match in enumerate(starts)
            }

        current_blocks = blocks(current["src/typed_generated/typed_slice.cpp"])
        prior_blocks = blocks(prior["src/typed_generated/typed_slice.cpp"])
        self.assertEqual((127, 126),
                         (len(current_blocks), len(prior_blocks)))
        self.assertEqual({PERLIN_KEY}, set(current_blocks) - set(prior_blocks))
        ordinal = re.compile(r"typed_[0-9]+")
        for key, block in prior_blocks.items():
            with self.subTest(historical_block=key):
                self.assertEqual(
                    ordinal.sub("typed_SENTINEL", block),
                    ordinal.sub("typed_SENTINEL", current_blocks[key]))
                self.assertNotRegex(block, r"(?<!:) \^ ")
                self.assertNotIn("perlin_scalar_uint_xor_profile", block)

        perlin = current_blocks[PERLIN_KEY]
        self.assertIn("namespace typed_123 {", perlin)
        self.assertEqual(2, perlin.count(" ^ "))
        self.assertEqual(2, perlin.count("double hash3("))
        hash3_start = perlin.index(
            "double hash3(", perlin.index("double hash3(") + 1)
        hash3 = perlin[hash3_start:perlin.index("\n}\n", hash3_start)]
        self.assertEqual(2, hash3.count(" ^ "))
        self.assertEqual(1, hash3.count("glsl::bitwise_xor("))
        self.assertEqual(1, perlin.count("bind_synth_perlin_perlin"))

        current_manifest = json.loads(
            current["src/typed_generated/typed_manifest.json"])
        prior_manifest = json.loads(
            prior["src/typed_generated/typed_manifest.json"])
        current_rows = {item["program_key"]: item
                        for item in current_manifest["programs"]}
        prior_rows = {item["program_key"]: item
                      for item in prior_manifest["programs"]}
        self.assertEqual((127, 126),
                         (len(current_rows), len(prior_rows)))
        self.assertEqual({PERLIN_KEY}, set(current_rows) - set(prior_rows))
        for key, row in prior_rows.items():
            with self.subTest(historical_manifest_row=key):
                self.assertEqual(
                    {name: value for name, value in row.items()
                     if name != "output_sha256"},
                    {name: value for name, value in current_rows[key].items()
                     if name != "output_sha256"})
                self.assertNotIn("perlin_scalar_uint_xor_profile", row)
        self.assertEqual(
            PROFILE,
            current_rows[PERLIN_KEY]["perlin_scalar_uint_xor_profile"])
        self.assertEqual(1, sum(
            "perlin_scalar_uint_xor_profile" in row
            for row in current_rows.values()))

        declaration = (
            "[[nodiscard]] BoundKernel bind_synth_perlin_perlin("
            "const glsl::Bindings& bindings);\n")
        self.assertEqual(1, current_header.decode().count(declaration))
        self.assertEqual(prior_header.decode(),
                         current_header.decode().replace(declaration, ""))

        def catalog_rows(payload):
            source = payload.decode()
            return re.findall(
                r'^    \{"([^"]+)", &(bind_[A-Za-z0-9_]+)\},$',
                source, re.MULTILINE)
        current_catalog = catalog_rows(
            current["src/typed_generated/typed_slice.cpp"])
        prior_catalog = catalog_rows(
            prior["src/typed_generated/typed_slice.cpp"])
        self.assertEqual((129, 128),
                         (len(current_catalog), len(prior_catalog)))
        self.assertEqual(
            {(PERLIN_KEY, "bind_synth_perlin_perlin")},
            set(current_catalog) - set(prior_catalog))
        self.assertEqual(set(prior_catalog),
                         set(current_catalog) - {(PERLIN_KEY,
                                                  "bind_synth_perlin_perlin")})

        current_typed_keys = [item["program_key"] for item in spec["programs"]]
        prior_typed_keys = [item["program_key"]
                            for item in prior_spec["programs"]]
        self.assertEqual(
            "ed2b5d24ac3fb80520b2036acfc13c18df294c1583f76fe2957d00a6282fdd72",
            hashlib.sha256(("\n".join(current_typed_keys) + "\n").encode()).hexdigest())
        self.assertEqual(
            "01b1dd9d0ec83e375275bc3928ee0f652d1495666616e5280e4b878a71b5db76",
            hashlib.sha256(("\n".join(prior_typed_keys) + "\n").encode()).hexdigest())
        self.assertEqual(
            "37e41894bc62b658a3454e13ab60fe814baf2492fa2a74b0f4305e05480a7883",
            hashlib.sha256(("\n".join(key for key, _ in current_catalog) + "\n").encode()).hexdigest())
        self.assertEqual(
            "d46ed864c5ed1795201981b7fc4aeec8fd330caa54c09d890235e5023c91e6e3",
            hashlib.sha256(("\n".join(key for key, _ in prior_catalog) + "\n").encode()).hexdigest())

    def test_task27_cpp_tables_are_exact_executable_frozen_transcription(self) -> None:
        import hashlib
        import struct

        oracle_bytes = pathlib.Path(
            REPOSITORY / "tests/oracles/task-27-oracles.json").read_bytes()
        self.assertEqual(
            "27e12edfdec79a9f1ad9c07d3d076da2553e36f63d8c9a5ac43c1bc1592bcc54",
            hashlib.sha256(oracle_bytes).hexdigest())
        oracle = json.loads(oracle_bytes)
        cpp = (REPOSITORY / "tests/test_generated_kernels.cpp").read_text()
        parsed = _task27_parse_executable_tables(cpp)
        f32_bits = lambda value: int.from_bytes(
            struct.pack("<f", float(value)), "little")
        expected_cases = []
        for case in oracle["cases"]:
            uniforms = case["uniforms"]
            probes = [value for probe in case["output"]["probes"]
                      for value in (*probe["at_top_down_xy"],
                                    *(int(bits, 16) for bits in probe["f32_bits_le"]))]
            expected_cases.append([
                case["name"], case["dimensions"]["width"],
                case["dimensions"]["height"], f32_bits(case["time"]),
                case["seed"], uniforms["octaves"], uniforms["colorMode"],
                uniforms["ridges"], uniforms["warpIterations"],
                f32_bits(uniforms["scale"]), f32_bits(uniforms["warpScale"]),
                f32_bits(uniforms["warpIntensity"]), f32_bits(uniforms["speed"]),
                [f32_bits(value) for value in case["tile_offset"]],
                [f32_bits(value) for value in case["full_resolution"]],
                case["name"] == "full-resolution-fallback",
                case["output"]["f32_sha256"], case["output"]["rgba8_sha256"],
                probes, case["output"]["finite_lanes"],
            ])
        expected_words = []
        mutation_order = ("outer_or", "inner_or", "outer_and", "inner_and",
                          "right_associated_xor")
        for item in oracle["direct_unsigned_word_cases"]:
            expected_words.append([
                *(int(value, 16) for value in item["inputs_hex"]),
                int(item["inner_u32_hex"], 16), int(item["result_u32_hex"], 16),
                int(item["source_unsigned_numerator_f32_bits_le"], 16),
                int(item["canonical_js_signed_numerator_f32_bits_le"], 16),
                int(item["source_typed_ratio_f64_bits_le"], 16),
                [int(item["mutations"][name], 16) for name in mutation_order],
            ])
        self.assertEqual(expected_cases, parsed["cases"])
        self.assertEqual(expected_words, parsed["words"])
        modes = ["exact_left_xor", "outer_or", "inner_or", "outer_and",
                 "inner_and", "right_associated_xor"]
        self.assertEqual(modes, parsed["enum_names"])
        self.assertEqual(modes, parsed["dispatch_names"])
        self.assertEqual(len(modes), len(set(parsed["dispatch_names"])))

        for marker, old, new in (
                ("kTask27NativeCases", "mono-default-shape", "mono-default-shapE"),
                ("kTask27WordCases", "0xdeadbeefU", "0xdeadbeeeU"),
                ("kTask27WordCases", "0x4f1ffef4U", "0x4f1ffef5U"),
                ("kTask27WordCases", "0xcec00217U", "0xcec00218U"),
                ("enum class Task27WordMode", "outer_or", "outer_orr")):
            offset = cpp.index(old, cpp.index(marker))
            tampered = cpp[:offset] + new + cpp[offset + len(old):]
            altered = _task27_parse_executable_tables(tampered)
            with self.subTest(marker=marker):
                self.assertNotEqual(parsed, altered)

    def test_task27_exhaustive_profile_validator_and_emitter_negative_closure(self) -> None:
        import dataclasses
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.semantic_types import INT, UINT, vector
        from tools.glslcpp.frontend.typed_ir import PreprocessorDefine
        from tools.glslcpp.frontend.perlin_scalar_uint_xor_profile import (
            PROFILE, authenticate_perlin_scalar_uint_xor)

        raw, source_hash, exact = self.exact_program()
        function = exact.functions[4]
        returned = function.body[10]
        division = returned.expressions[0]
        constructor = division.children[0]
        outer = constructor.children[0]
        inner = outer.children[0]
        operands = (*inner.children, outer.children[1])

        def replace_expression(program, target, replacement):
            def expression(value):
                if value is target:
                    return replacement
                return dataclasses.replace(
                    value, children=tuple(expression(child)
                                          for child in value.children))
            def statement(value):
                return dataclasses.replace(
                    value,
                    expressions=tuple(expression(item)
                                      for item in value.expressions),
                    children=tuple(statement(child)
                                   for child in value.children))
            return dataclasses.replace(
                program, functions=tuple(dataclasses.replace(
                    item, body=tuple(statement(value) for value in item.body))
                    for item in program.functions))

        def expressions(program):
            found = []
            def expression(value):
                found.append(value)
                for child in value.children:
                    expression(child)
            def statement(value):
                for item in value.expressions:
                    expression(item)
                for child in value.children:
                    statement(child)
            for item in program.functions:
                for value in item.body:
                    statement(value)
            return found

        def scalar_xors(program):
            return [value for value in expressions(program)
                    if value.kind == "binary" and value.operator == "^" and
                    value.type.display() in ("int", "uint")]

        def candidate_with_outer(replacement):
            return replace_expression(exact, outer, replacement)

        right_inner = dataclasses.replace(
            inner, children=(inner.children[1], outer.children[1]))
        right_associated = dataclasses.replace(
            outer, children=(inner.children[0], right_inner))
        signed_operands = tuple(dataclasses.replace(item, type=INT)
                                for item in operands)
        signed_inner = dataclasses.replace(
            inner, type=INT, children=signed_operands[:2])
        signed_outer = dataclasses.replace(
            outer, type=INT, children=(signed_inner, signed_operands[2]))
        mixed_outer = dataclasses.replace(
            outer, children=(inner, dataclasses.replace(operands[2], type=INT)))
        vector_outer = dataclasses.replace(outer, type=vector("uint", 3))

        call_to_hash3 = next(
            value for value in expressions(exact)
            if value.kind == "call" and value.signature_id == function.id)
        moved_return = dataclasses.replace(
            exact,
            functions=(*exact.functions[:4],
                       dataclasses.replace(function, body=function.body[:10]),
                       dataclasses.replace(
                           exact.functions[5],
                           body=(*exact.functions[5].body, returned)),
                       *exact.functions[6:]))
        third_statement = dataclasses.replace(
            returned, kind="expr", expressions=(dataclasses.replace(inner),))
        third_site = dataclasses.replace(
            exact, functions=(*exact.functions[:4], dataclasses.replace(
                function, body=(*function.body, third_statement)),
                              *exact.functions[5:]))
        define = exact.preprocessor_defines[0]
        dimensions_three = analyze_program(
            parse_program(raw, exact.key, {"DIMENSIONS": 3}), exact.key)

        mutations = {
            "program-key": dataclasses.replace(exact, key="synth/perlin:other"),
            "normalized-source": dataclasses.replace(exact, source=exact.source + "\n"),
            "raw-source": dataclasses.replace(exact, raw_source=exact.raw_source + "\n"),
            "define-name": dataclasses.replace(
                exact, preprocessor_defines=(dataclasses.replace(
                    define, name="DIMENSION"),)),
            "define-value": dataclasses.replace(
                exact, preprocessor_defines=(dataclasses.replace(
                    define, canonical_value="3"),)),
            "define-kind": dataclasses.replace(
                exact, preprocessor_defines=(dataclasses.replace(
                    define, kind="uint"),)),
            "define-count": dataclasses.replace(
                exact, preprocessor_defines=(*exact.preprocessor_defines,
                    PreprocessorDefine("UNUSED", "int", "1"))),
            "define-order": dataclasses.replace(
                exact, preprocessor_defines=(
                    PreprocessorDefine("UNUSED", "int", "1"), define)),
            "dimensions-three-analyzed": dimensions_three,
            "body-status": dataclasses.replace(exact, body_status="not analyzed"),
            "declaration-order": dataclasses.replace(
                exact, declarations=(exact.declarations[1], exact.declarations[0],
                                     *exact.declarations[2:])),
            "declaration-name": dataclasses.replace(
                exact, declarations=(dataclasses.replace(
                    exact.declarations[0], symbol=dataclasses.replace(
                        exact.declarations[0].symbol, name="other")),
                                     *exact.declarations[1:])),
            "declaration-count": dataclasses.replace(
                exact, declarations=exact.declarations[:-1]),
            "interface-symbol": dataclasses.replace(
                exact, interface_symbols=(exact.builtin_symbols[0],)),
            "builtin-interface": dataclasses.replace(exact, builtin_symbols=()),
            "resource-uniform-order": dataclasses.replace(
                exact, resources=dataclasses.replace(
                    exact.resources,
                    uniforms=tuple(reversed(exact.resources.uniforms)))),
            "resource-sampler": dataclasses.replace(
                exact, resources=dataclasses.replace(
                    exact.resources, samplers=("foreignTex",),
                    uses_texture=True)),
            "resource-output": dataclasses.replace(
                exact, resources=dataclasses.replace(
                    exact.resources, outputs=("otherColor",))),
            "function-count": dataclasses.replace(
                exact, functions=exact.functions[:-1]),
            "function-order": dataclasses.replace(
                exact, functions=(exact.functions[1], exact.functions[0],
                                  *exact.functions[2:])),
            "function-id": dataclasses.replace(
                exact, functions=(*exact.functions[:4], dataclasses.replace(
                    function, signature=dataclasses.replace(
                        function.signature, id=900)), *exact.functions[5:])),
            "function-name": dataclasses.replace(
                exact, functions=(*exact.functions[:4], dataclasses.replace(
                    function, signature=dataclasses.replace(
                        function.signature, name="hash4")), *exact.functions[5:])),
            "function-return": dataclasses.replace(
                exact, functions=(*exact.functions[:4], dataclasses.replace(
                    function, signature=dataclasses.replace(
                        function.signature, return_type=UINT)), *exact.functions[5:])),
            "parameter-name": dataclasses.replace(
                exact, functions=(*exact.functions[:4], dataclasses.replace(
                    function, signature=dataclasses.replace(
                        function.signature, parameters=(dataclasses.replace(
                            function.parameters[0], name="other"),))),
                                  *exact.functions[5:])),
            "body-count": dataclasses.replace(
                exact, functions=(*exact.functions[:4], dataclasses.replace(
                    function, body=function.body[:10]), *exact.functions[5:])),
            "owner-function": moved_return,
            "outer-operator": candidate_with_outer(
                dataclasses.replace(outer, operator="|")),
            "inner-operator": candidate_with_outer(dataclasses.replace(
                outer, children=(dataclasses.replace(inner, operator="|"),
                                 outer.children[1]))),
            "right-associated": candidate_with_outer(right_associated),
            "swapped-operands": candidate_with_outer(dataclasses.replace(
                outer, children=(dataclasses.replace(
                    inner, children=tuple(reversed(inner.children))),
                                 outer.children[1]))),
            "source-path": candidate_with_outer(dataclasses.replace(
                outer, span=dataclasses.replace(
                    outer.span, program_key="foreign/source:path"))),
            "source-span": candidate_with_outer(dataclasses.replace(
                outer, span=dataclasses.replace(
                    outer.span, start_column=outer.span.start_column + 1))),
            "category": candidate_with_outer(dataclasses.replace(
                outer, category="lvalue")),
            "parent-role": replace_expression(exact, constructor, outer),
            "signed-xor": candidate_with_outer(signed_outer),
            "mixed-xor": candidate_with_outer(mixed_outer),
            "vector-scalar-xor": candidate_with_outer(vector_outer),
            "third-scalar-site": third_site,
            "call-graph": replace_expression(
                exact, call_to_hash3,
                dataclasses.replace(call_to_hash3, signature_id=57)),
            "loop-proof-count": dataclasses.replace(
                exact, counted_loop_proof=dataclasses.replace(
                    exact.counted_loop_proof, loop_count=3)),
            "loop-proof-charge": dataclasses.replace(
                exact, counted_loop_proof=dataclasses.replace(
                    exact.counted_loop_proof, entrypoint_charge=29)),
            "loop-proof-recursion": dataclasses.replace(
                exact, counted_loop_proof=dataclasses.replace(
                    exact.counted_loop_proof, call_graph_acyclic=False)),
            "unrelated-proof": dataclasses.replace(
                exact, fixed_nine_table_proof=object()),
        }

        def hash3_site(program):
            return (program.functions[4].body[10].expressions[0]
                    .children[0].children[0])

        preconditions = {
            "program-key": lambda p: p.key == "synth/perlin:other",
            "normalized-source": lambda p: p.source.endswith("\n\n"),
            "raw-source": lambda p: p.raw_source.endswith("\n\n"),
            "define-name": lambda p: p.preprocessor_defines[0].name == "DIMENSION",
            "define-value": lambda p: p.preprocessor_defines[0].canonical_value == "3",
            "define-kind": lambda p: p.preprocessor_defines[0].kind == "uint",
            "define-count": lambda p: len(p.preprocessor_defines) == 2,
            "define-order": lambda p: tuple(item.name for item in p.preprocessor_defines) == ("UNUSED", "DIMENSIONS"),
            "dimensions-three-analyzed": lambda p: p.body_status == "analyzed" and p.preprocessor_defines[0].canonical_value == "3",
            "body-status": lambda p: p.body_status == "not analyzed",
            "declaration-order": lambda p: p.declarations[:2] == (exact.declarations[1], exact.declarations[0]),
            "declaration-name": lambda p: p.declarations[0].symbol.name == "other",
            "declaration-count": lambda p: len(p.declarations) == 16,
            "interface-symbol": lambda p: len(p.interface_symbols) == 1,
            "builtin-interface": lambda p: not p.builtin_symbols,
            "resource-uniform-order": lambda p: p.resources.uniforms == tuple(reversed(exact.resources.uniforms)),
            "resource-sampler": lambda p: p.resources.samplers == ("foreignTex",) and p.resources.uses_texture,
            "resource-output": lambda p: p.resources.outputs == ("otherColor",),
            "function-count": lambda p: len(p.functions) == 12,
            "function-order": lambda p: p.functions[:2] == (exact.functions[1], exact.functions[0]),
            "function-id": lambda p: p.functions[4].id == 900,
            "function-name": lambda p: p.functions[4].name == "hash4",
            "function-return": lambda p: p.functions[4].return_type == UINT,
            "parameter-name": lambda p: p.functions[4].parameters[0].name == "other",
            "body-count": lambda p: len(p.functions[4].body) == 10,
            "owner-function": lambda p: len(p.functions[4].body) == 10 and p.functions[5].body[-1] == returned,
            "outer-operator": lambda p: hash3_site(p).operator == "|",
            "inner-operator": lambda p: hash3_site(p).children[0].operator == "|",
            "right-associated": lambda p: hash3_site(p).children[1].operator == "^",
            "swapped-operands": lambda p: hash3_site(p).children[0].children == tuple(reversed(inner.children)),
            "source-path": lambda p: hash3_site(p).span.program_key == "foreign/source:path",
            "source-span": lambda p: hash3_site(p).span.start_column == outer.span.start_column + 1,
            "category": lambda p: hash3_site(p).category == "lvalue",
            "parent-role": lambda p: p.functions[4].body[10].expressions[0].children[0].kind == "binary",
            "signed-xor": lambda p: hash3_site(p).type == INT and hash3_site(p).children[0].type == INT,
            "mixed-xor": lambda p: hash3_site(p).children[1].type == INT,
            "vector-scalar-xor": lambda p: p.functions[4].body[10].expressions[0].children[0].children[0].type.display() == "uvec3",
            "third-scalar-site": lambda p: len(scalar_xors(p)) == 3,
            "call-graph": lambda p: sum(value.kind == "call" and value.signature_id == 57 for value in expressions(p)) == sum(value.kind == "call" and value.signature_id == 57 for value in expressions(exact)) + 1,
            "loop-proof-count": lambda p: p.counted_loop_proof.loop_count == 3,
            "loop-proof-charge": lambda p: p.counted_loop_proof.entrypoint_charge == 29,
            "loop-proof-recursion": lambda p: not p.counted_loop_proof.call_graph_acyclic,
            "unrelated-proof": lambda p: p.fixed_nine_table_proof is not None,
        }
        self.assertEqual(set(mutations), set(preconditions))
        self.assertGreaterEqual(len(mutations), 40)

        for label, candidate in mutations.items():
            self.assertNotEqual(exact, candidate, label)
            with self.subTest(case=label, boundary="structural-precondition"):
                self.assertTrue(preconditions[label](candidate), label)
            with self.subTest(case=label, boundary="profile"), \
                    self.assertRaises(ValueError):
                authenticate_perlin_scalar_uint_xor(candidate, source_hash, PROFILE)
            with self.subTest(case=label, boundary="validator"), \
                    self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash,
                    perlin_scalar_uint_xor_profile=PROFILE)
            with self.subTest(case=label, boundary="emitter"), \
                    self.assertRaises(TypedEmissionError):
                render_typed_cpp(
                    candidate, candidate.key, source_hash,
                    perlin_scalar_uint_xor_profile=PROFILE)

        foreign = analyze_program(parse_program(
            "out vec4 color; void main() { color = vec4(1.0); }",
            "task27:foreign", {}), "task27:foreign")
        modes = (
            (exact, None, source_hash, False, False, "exact-absent"),
            (exact, PROFILE, source_hash, True, True, "exact-exact"),
            (exact, "foreign-profile", source_hash, False, False, "exact-foreign"),
            (mutations["outer-operator"], PROFILE, source_hash, False, False, "mutated-exact"),
            (foreign, PROFILE, source_hash, False, False, "foreign-exact"),
            (foreign, None, None, False, True, "foreign-absent"),
            (exact, PROFILE, "0" * 64, False, False, "wrong-caller-hash"),
        )
        for candidate, carrier, caller_hash, profile_ok, pipeline_ok, label in modes:
            if profile_ok:
                authenticate_perlin_scalar_uint_xor(candidate, caller_hash, carrier)
            else:
                with self.subTest(mode=label, boundary="profile"), \
                        self.assertRaises(ValueError):
                    authenticate_perlin_scalar_uint_xor(candidate, caller_hash, carrier)
            for boundary, invoke, error in (
                    ("validator", lambda: generate_typed_slice.validate_capabilities(
                        candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=caller_hash,
                        perlin_scalar_uint_xor_profile=carrier),
                     generate_typed_slice.GeneratorError),
                    ("emitter", lambda: render_typed_cpp(
                        candidate, candidate.key, caller_hash,
                        perlin_scalar_uint_xor_profile=carrier),
                     TypedEmissionError)):
                if pipeline_ok:
                    invoke()
                else:
                    with self.subTest(mode=label, boundary=boundary), \
                            self.assertRaises(error):
                        invoke()

        combined_carriers = (
            {"compatibility_transform": "coalesce-uv-alias-v1"},
            {"custom_comparer_profile": "lens-comparer-v1"},
            {"numeric_literal_contract": "source-double"},
            {"source_global_literal_int_profile": "source-global-literal-int-v1"},
            {"gather_sorted_round_profile": "gather-round-v1"},
            {"literal_vec3_lane_index_profile": "literal-vec3-v1"},
            {"smooth_edge_luma_weights_profile": "smooth-edge-luma-weights-v1"},
        )
        for kwargs in combined_carriers:
            with self.subTest(carrier=tuple(kwargs), boundary="validator"), \
                    self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    exact, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash,
                    perlin_scalar_uint_xor_profile=PROFILE, **kwargs)
            with self.subTest(carrier=tuple(kwargs), boundary="emitter"), \
                    self.assertRaises(TypedEmissionError):
                render_typed_cpp(
                    exact, exact.key, source_hash,
                    perlin_scalar_uint_xor_profile=PROFILE, **kwargs)

        def reconstruct(program):
            def expression(value):
                return dataclasses.replace(
                    value, children=tuple(expression(child)
                                          for child in value.children))
            def statement(value):
                return dataclasses.replace(
                    value,
                    expressions=tuple(expression(item)
                                      for item in value.expressions),
                    children=tuple(statement(child)
                                   for child in value.children))
            return dataclasses.replace(
                program, functions=tuple(dataclasses.replace(
                    item, body=tuple(statement(value) for value in item.body))
                    for item in program.functions))

        equal_reconstructed = reconstruct(exact)
        self.assertEqual(exact, equal_reconstructed)
        rebuilt_outer = equal_reconstructed.functions[4].body[10].expressions[0].children[0].children[0]
        self.assertIsNot(outer, rebuilt_outer)
        authenticate_perlin_scalar_uint_xor(
            equal_reconstructed, source_hash, PROFILE)
        with mock.patch.object(
                generate_typed_slice, "authenticate_perlin_scalar_uint_xor",
                return_value=(outer, inner)), self.assertRaises(
                    generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                equal_reconstructed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                perlin_scalar_uint_xor_profile=PROFILE)
        with mock.patch(
                "tools.glslcpp.emit_typed_cpp.authenticate_perlin_scalar_uint_xor",
                return_value=(outer, inner)), self.assertRaises(TypedEmissionError):
            render_typed_cpp(
                equal_reconstructed, equal_reconstructed.key, source_hash,
                perlin_scalar_uint_xor_profile=PROFILE)


class Task28RotateMat2ReturnTests(unittest.TestCase):
    @staticmethod
    def exact_program():
        import hashlib
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.rotate_mat2_return_profile import ROTATE_KEY
        source = (REPOSITORY / "tools/glslcpp/corpus/"
                  "a024dc3a960cc44af454abc7aebce50456c194e6/"
                  "sources/filter/rotate/rot.glsl").read_text()
        return (source, hashlib.sha256(source.encode()).hexdigest(),
                analyze_program(parse_program(source, ROTATE_KEY, {}), ROTATE_KEY))

    def test_task28_profile_validator_and_emitter_exact_identity(self) -> None:
        import dataclasses
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend.rotate_mat2_return_profile import (
            PROFILE, apply_rotate_mat2_return, authenticate_rotate_mat2_return)
        _, source_hash, typed = self.exact_program()
        helper, constructor, call, parent = authenticate_rotate_mat2_return(
            typed, source_hash, PROFILE)
        self.assertIs(helper, typed.functions[1])
        self.assertIs(constructor, helper.body[2].expressions[0])
        self.assertIs(parent, typed.functions[0].body[8].expressions[0].children[1])
        self.assertIs(call, parent.children[0])
        self.assertIs(typed, apply_rotate_mat2_return(typed, source_hash, PROFILE))
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                typed, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)
        with self.assertRaises(ValueError):
            render_typed_cpp(typed, typed.key, source_hash)
        generate_typed_slice.validate_capabilities(
            typed, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash, rotate_mat2_return_profile=PROFILE)
        emitted = render_typed_cpp(
            typed, typed.key, source_hash, rotate_mat2_return_profile=PROFILE)
        self.assertEqual(2, emitted.count("glsl::Mat2 rotate2D("))
        self.assertEqual(1, emitted.count(
            "return glsl::Mat2(glsl::Vec2(c, (-s)), glsl::Vec2(s, c));"))
        self.assertEqual(1, emitted.count("rotate2D(state, context,"))
        self.assertNotRegex(emitted, r"Mat2\s*[&*]\s*rotate2D|sret|new\s+glsl::Mat2")
        from tools.glslcpp.emit_typed_cpp import _Emitter
        forged = object.__new__(_Emitter)
        forged.program = typed
        forged.source_hash = source_hash
        with self.assertRaisesRegex(ValueError,
                                    "unauthenticated matrix expression"):
            forged.expression(constructor)

        def reconstruct(value):
            if dataclasses.is_dataclass(value):
                return dataclasses.replace(value, **{
                    field.name: reconstruct(getattr(value, field.name))
                    for field in dataclasses.fields(value)})
            if isinstance(value, tuple):
                return tuple(reconstruct(item) for item in value)
            return value
        rebuilt = reconstruct(typed)
        rebuilt_objects = authenticate_rotate_mat2_return(rebuilt, source_hash, PROFILE)
        self.assertEqual(typed, rebuilt)
        self.assertTrue(all(new is not old for new, old in zip(
            rebuilt_objects, (helper, constructor, call, parent))))

    def test_task28_emitter_rejects_foreign_matrix_programs_for_every_carrier(self) -> None:
        """A foreign key must never inherit Rotate's matrix-emission capability."""
        import dataclasses
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.rotate_mat2_return_profile import PROFILE

        source, source_hash, exact = self.exact_program()
        foreign_key = "filter/rotate:foreign"
        candidates = {
            "rekeyed-exact-tree": dataclasses.replace(exact, key=foreign_key),
            "independently-analyzed-foreign-tree": analyze_program(
                parse_program(source, foreign_key, {}), foreign_key),
        }
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                "unsupported matrix return type"):
            generate_typed_slice.validate_capabilities(
                candidates["independently-analyzed-foreign-tree"],
                generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)
        for candidate_name, candidate in candidates.items():
            for carrier_name, carrier in {
                    "absent": None,
                    "exact": PROFILE,
                    "foreign": "rotate-mat2-return-foreign",
            }.items():
                with self.subTest(candidate=candidate_name, carrier=carrier_name):
                    with self.assertRaises(TypedEmissionError):
                        render_typed_cpp(
                            candidate, candidate.key, source_hash,
                            rotate_mat2_return_profile=carrier)

    def test_task28_exhaustive_single_axis_negative_closure(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.rotate_mat2_return_profile import (
            PROFILE, authenticate_rotate_mat2_return)
        _, source_hash, exact = self.exact_program()

        def at(value, path):
            for part in path:
                value = value[part] if isinstance(part, int) else getattr(value, part)
            return value
        def replaced(value, path, replacement):
            if len(path) == 1:
                part = path[0]
                if isinstance(part, int):
                    items = list(value); items[part] = replacement
                    return tuple(items)
                return dataclasses.replace(value, **{part: replacement})
            part = path[0]
            child = value[part] if isinstance(part, int) else getattr(value, part)
            updated = replaced(child, path[1:], replacement)
            if isinstance(part, int):
                items = list(value); items[part] = updated
                return tuple(items)
            return dataclasses.replace(value, **{part: updated})

        axes = {
            "program-key": (("key",), "filter/rotate:foreign"),
            "normalized-source": (("source",), exact.source + " "),
            "raw-source": (("raw_source",), exact.raw_source + " "),
            "body-status": (("body_status",), "task28-mutated"),
            "resource-uniform-0": (("resources", "uniforms", 0), "otherTex"),
            "resource-uniform-1": (("resources", "uniforms", 1), "otherRotation"),
            "resource-sampler": (("resources", "samplers", 0), "otherTex"),
            "resource-output": (("resources", "outputs", 0), "otherColor"),
            "resource-texture-use": (("resources", "uses_texture"), False),
            "resource-derivatives": (("resources", "uses_derivatives"), True),
            "loop-count": (("counted_loop_proof", "loop_count"), 1),
            "loop-unproved": (("counted_loop_proof", "unproved_loop_count"), 1),
            "loop-depth": (("counted_loop_proof", "max_effective_depth"), 1),
            "loop-product": (("counted_loop_proof", "max_lexical_product"), 1),
            "loop-charge": (("counted_loop_proof", "entrypoint_charge"), 1),
            "call-graph-cycle": (("counted_loop_proof", "call_graph_acyclic"), False),
            "declaration-order": (("declarations",), tuple(reversed(exact.declarations))),
            "declaration-count": (("declarations",), exact.declarations[:-1]),
            "input-id": (("declarations", 0, "symbol", "id"), 101),
            "input-name": (("declarations", 0, "symbol", "name"), "otherTex"),
            "input-storage": (("declarations", 0, "symbol", "storage"), "local"),
            "input-writable": (("declarations", 0, "symbol", "writable"), True),
            "input-direction": (("declarations", 0, "symbol", "direction"), "out"),
            "input-type-base": (("declarations", 0, "type", "base"), "samplerCube"),
            "input-span-line": (("declarations", 0, "span", "start_line"), 404),
            "builtin-id": (("builtin_symbols", 0, "id"), 111),
            "builtin-name": (("builtin_symbols", 0, "name"), "gl_OtherCoord"),
            "builtin-type-base": (("builtin_symbols", 0, "type", "base"), "int"),
            "builtin-storage": (("builtin_symbols", 0, "storage"), "uniform"),
            "builtin-direction": (("builtin_symbols", 0, "direction"), "out"),
            "output-id": (("declarations", 5, "symbol", "id"), 106),
            "output-name": (("declarations", 5, "symbol", "name"), "otherColor"),
            "tau-id": (("declarations", 6, "symbol", "id"), 107),
            "tau-name": (("declarations", 6, "symbol", "name"), "OTHER_TAU"),
            "tau-storage": (("declarations", 6, "symbol", "storage"), "uniform"),
            "tau-literal": (("declarations", 6, "initializer", "literal"), "6.283186"),
            "main-signature-id": (("functions", 0, "signature", "id"), 109),
            "main-name": (("functions", 0, "signature", "name"), "otherMain"),
            "main-return-base": (("functions", 0, "signature", "return_type", "base"), "float"),
            "main-span-line": (("functions", 0, "span", "start_line"), 120),
            "helper-signature-id": (("functions", 1, "signature", "id"), 110),
            "helper-name": (("functions", 1, "signature", "name"), "rotateOther"),
            "helper-return-kind": (("functions", 1, "signature", "return_type", "kind"), "vector"),
            "helper-return-width": (("functions", 1, "signature", "return_type", "width"), 3),
            "helper-span-line": (("functions", 1, "span", "start_line"), 114),
            "function-order": (("functions",), tuple(reversed(exact.functions))),
            "function-count": (("functions",), exact.functions[:1]),
            "parameter-id": (("functions", 1, "signature", "parameters", 0, "id"), 108),
            "parameter-name": (("functions", 1, "signature", "parameters", 0, "name"), "theta"),
            "parameter-storage": (("functions", 1, "signature", "parameters", 0, "storage"), "local"),
            "parameter-direction": (("functions", 1, "signature", "parameters", 0, "direction"), "inout"),
            "parameter-writable": (("functions", 1, "signature", "parameters", 0, "writable"), False),
            "local-c-id": (("functions", 1, "body", 0, "expressions", 0, "symbol", "id"), 117),
            "local-c-name": (("functions", 1, "body", 0, "expressions", 0, "symbol", "name"), "otherC"),
            "local-c-storage": (("functions", 1, "body", 0, "expressions", 0, "symbol", "storage"), "uniform"),
            "local-c-type": (("functions", 1, "body", 0, "expressions", 0, "type", "base"), "int"),
            "local-c-initializer-kind": (("functions", 1, "body", 0, "expressions", 0, "children", 0, "kind"), "call"),
            "local-c-initializer-callee": (("functions", 1, "body", 0, "expressions", 0, "children", 0, "callee"), "sin"),
            "cos-statement-kind": (("functions", 1, "body", 0, "kind"), "expr"),
            "sin-statement-kind": (("functions", 1, "body", 1, "kind"), "expr"),
            "return-statement-kind": (("functions", 1, "body", 2, "kind"), "expr"),
            "return-expression-count": (("functions", 1, "body", 2, "expressions"), ()),
            "constructor-kind": (("functions", 1, "body", 2, "expressions", 0, "kind"), "call"),
            "constructor-category": (("functions", 1, "body", 2, "expressions", 0, "category"), "lvalue"),
            "constructor-span": (("functions", 1, "body", 2, "expressions", 0, "span", "start_column"), 13),
            "constructor-type-kind": (("functions", 1, "body", 2, "expressions", 0, "constructor_type", "kind"), "vector"),
            "constructor-result-kind": (("functions", 1, "body", 2, "expressions", 0, "type", "kind"), "vector"),
            "constructor-arity": (("functions", 1, "body", 2, "expressions", 0, "children"),
                                  exact.functions[1].body[2].expressions[0].children[:3]),
            "constructor-order": (("functions", 1, "body", 2, "expressions", 0, "children"),
                                  tuple(reversed(exact.functions[1].body[2].expressions[0].children))),
            "constructor-child0-symbol": (("functions", 1, "body", 2, "expressions", 0, "children", 0, "symbol_id"), 18),
            "constructor-child1-sign": (("functions", 1, "body", 2, "expressions", 0, "children", 1, "operator"), "+"),
            "constructor-child2-symbol": (("functions", 1, "body", 2, "expressions", 0, "children", 2, "symbol_id"), 17),
            "constructor-child3-symbol": (("functions", 1, "body", 2, "expressions", 0, "children", 3, "symbol_id"), 18),
            "call-kind": (("functions", 0, "body", 8, "expressions", 0, "children", 1, "children", 0, "kind"), "builtin"),
            "call-callee": (("functions", 0, "body", 8, "expressions", 0, "children", 1, "children", 0, "callee"), "otherRotate"),
            "call-arity": (("functions", 0, "body", 8, "expressions", 0, "children", 1, "children", 0, "children"), ()),
            "call-argument-operator": (("functions", 0, "body", 8, "expressions", 0, "children", 1, "children", 0, "children", 0, "operator"), "*"),
            "call-signature": (("functions", 0, "body", 8, "expressions", 0, "children", 1, "children", 0, "signature_id"), 999),
            "call-span": (("functions", 0, "body", 8, "expressions", 0, "children", 1, "children", 0, "span", "start_column"), 11),
            "parent-operator": (("functions", 0, "body", 8, "expressions", 0, "children", 1, "operator"), "+"),
            "parent-category": (("functions", 0, "body", 8, "expressions", 0, "children", 1, "category"), "lvalue"),
            "parent-result-base": (("functions", 0, "body", 8, "expressions", 0, "children", 1, "type", "base"), "int"),
            "parent-child-order": (("functions", 0, "body", 8, "expressions", 0, "children", 1, "children"),
                                   tuple(reversed(exact.functions[0].body[8].expressions[0].children[1].children))),
        }
        candidates = {name: replaced(exact, path, value)
                      for name, (path, value) in axes.items()}
        preconditions = {name: (lambda candidate, p=path, v=value:
                                at(candidate, p) == v)
                         for name, (path, value) in axes.items()}
        self.assertEqual(set(candidates), set(preconditions))
        self.assertEqual(83, len(candidates))
        self.assertEqual(
            "5f6d408f883906d19fdd2c8de10c19ba57291f1821d00cbdfb4a9486de70ecb8",
            hashlib.sha256(("\n".join(sorted(candidates)) + "\n").encode()).hexdigest())
        self.assertEqual(len(candidates), len(set(candidates)))
        for name, candidate in candidates.items():
            self.assertNotEqual(exact, candidate, name)
            self.assertTrue(preconditions[name](candidate), name)
            selected_path = axes[name][0]
            for protected_name, (protected_path, _) in axes.items():
                if protected_name == name:
                    continue
                overlap = (selected_path == protected_path[:len(selected_path)]
                           or protected_path == selected_path[:len(protected_path)])
                if not overlap:
                    self.assertEqual(
                        at(exact, protected_path), at(candidate, protected_path),
                        f"{name} changed protected coordinate {protected_name}")
            with self.subTest(axis=name, layer="profile"), self.assertRaises(ValueError):
                authenticate_rotate_mat2_return(candidate, source_hash, PROFILE)
            with self.subTest(axis=name, layer="validator"), self.assertRaises(generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash, rotate_mat2_return_profile=PROFILE)
            with self.subTest(axis=name, layer="emitter"), self.assertRaises(TypedEmissionError):
                render_typed_cpp(candidate, candidate.key, source_hash,
                                 rotate_mat2_return_profile=PROFILE)

    def test_task28_full_carrier_caller_numeric_define_and_identity_matrix(self) -> None:
        import dataclasses
        import hashlib
        from itertools import product
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.rotate_mat2_return_profile import (
            PROFILE, authenticate_rotate_mat2_return)
        from tools.glslcpp.frontend.typed_ir import PreprocessorDefine

        _, source_hash, exact = self.exact_program()
        define_variants = {
            "empty": (),
            "name": (PreprocessorDefine("TASK28_NAME", "int", "1"),),
            "value": (PreprocessorDefine("TASK28_VALUE", "int", "2"),),
            "count": (PreprocessorDefine("TASK28_A", "int", "1"),
                      PreprocessorDefine("TASK28_B", "int", "2")),
            "order": (PreprocessorDefine("TASK28_B", "int", "2"),
                      PreprocessorDefine("TASK28_A", "int", "1")),
        }
        carriers = {"exact": PROFILE, "absent": None,
                    "foreign": "rotate-mat2-return-foreign"}
        caller_hashes = {"exact": source_hash, "wrong": "0" * 64}
        numeric_modes = {"exact": "glsl-f32", "wrong": "source-double"}
        accepted = 0
        for (define_name, defines), (carrier_name, carrier), (
                hash_name, caller_hash), (numeric_name, numeric) in product(
                    define_variants.items(), carriers.items(),
                    caller_hashes.items(), numeric_modes.items()):
            candidate = dataclasses.replace(exact, preprocessor_defines=defines)
            should_accept = (define_name, carrier_name, hash_name, numeric_name) == (
                "empty", "exact", "exact", "exact")
            label = (define_name, carrier_name, hash_name, numeric_name)
            profile_should_accept = (define_name, carrier_name, hash_name) == (
                "empty", "exact", "exact")
            if profile_should_accept:
                authenticate_rotate_mat2_return(candidate, caller_hash, carrier)
            else:
                with self.subTest(layer="profile", coordinates=label), self.assertRaises(ValueError):
                    authenticate_rotate_mat2_return(candidate, caller_hash, carrier)
            if should_accept:
                accepted += 1
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=caller_hash, numeric_literal_contract=numeric,
                    rotate_mat2_return_profile=carrier)
                render_typed_cpp(
                    candidate, candidate.key, caller_hash,
                    numeric_literal_contract=numeric,
                    rotate_mat2_return_profile=carrier)
                continue
            with self.subTest(layer="validator", coordinates=label), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=caller_hash, numeric_literal_contract=numeric,
                    rotate_mat2_return_profile=carrier)
            with self.subTest(layer="emitter", coordinates=label), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    candidate, candidate.key, caller_hash,
                    numeric_literal_contract=numeric,
                    rotate_mat2_return_profile=carrier)
        self.assertEqual(1, accepted)
        self.assertEqual(60, len(define_variants) * len(carriers)
                         * len(caller_hashes) * len(numeric_modes))

        coexistence = {
            "compatibility_transform": generate_typed_slice.CRT_COMPATIBILITY_TRANSFORM,
            "custom_comparer_profile": generate_typed_slice.LENS_CUSTOM_COMPARER_PROFILE,
            "source_global_literal_int_profile": generate_typed_slice.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
            "gather_sorted_round_profile": generate_typed_slice.GATHER_SORTED_ROUND_PROFILE,
            "literal_vec3_lane_index_profile": generate_typed_slice.LITERAL_VEC3_LANE_INDEX_PROFILE,
            "smooth_edge_luma_weights_profile": generate_typed_slice.SMOOTH_EDGE_LUMA_WEIGHTS_PROFILE,
            "perlin_scalar_uint_xor_profile": generate_typed_slice.PERLIN_SCALAR_UINT_XOR_PROFILE,
        }
        self.assertEqual(7, len(coexistence))
        for name, value in coexistence.items():
            kwargs = {name: value, "rotate_mat2_return_profile": PROFILE}
            with self.subTest(layer="validator", coexistence=name), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    exact, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash, **kwargs)
            with self.subTest(layer="emitter", coexistence=name), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(exact, exact.key, source_hash, **kwargs)

        def reconstruct(value):
            if dataclasses.is_dataclass(value):
                return dataclasses.replace(value, **{
                    field.name: reconstruct(getattr(value, field.name))
                    for field in dataclasses.fields(value)})
            if isinstance(value, tuple):
                return tuple(reconstruct(item) for item in value)
            return value

        old_objects = authenticate_rotate_mat2_return(exact, source_hash, PROFILE)
        rebuilt = reconstruct(exact)
        own_objects = authenticate_rotate_mat2_return(rebuilt, source_hash, PROFILE)
        self.assertEqual(exact, rebuilt)
        self.assertTrue(all(old is not own for old, own in zip(old_objects, own_objects)))
        with mock.patch.object(
                generate_typed_slice, "authenticate_rotate_mat2_return",
                return_value=old_objects), self.assertRaises(
                    generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                rebuilt, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash, rotate_mat2_return_profile=PROFILE)
        with mock.patch(
                "tools.glslcpp.emit_typed_cpp.authenticate_rotate_mat2_return",
                return_value=old_objects), self.assertRaises(TypedEmissionError):
            render_typed_cpp(
                rebuilt, rebuilt.key, source_hash,
                rotate_mat2_return_profile=PROFILE)

    def test_task28_analyzer_produced_code_shape_alternatives_reject_every_boundary(self) -> None:
        import hashlib
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.semantic import analyze_program
        from tools.glslcpp.frontend.rotate_mat2_return_profile import (
            PROFILE, authenticate_rotate_mat2_return)

        source, _, exact = self.exact_program()
        alternatives = {
            "alternate-constructor-order": source.replace(
                "mat2(c, -s, s, c)", "mat2(c, s, -s, c)"),
            "helper-local-return": source.replace(
                "return mat2(c, -s, s, c);",
                "mat2 result = mat2(c, -s, s, c);\n    return result;"),
            "second-call": source.replace(
                "rotate2D(-angle * TAU / 360.0) * uv",
                "rotate2D(-angle * TAU / 360.0) * "
                "(rotate2D(-angle * TAU / 360.0) * uv)"),
            "stored-result": source.replace(
                "uv = rotate2D(-angle * TAU / 360.0) * uv;",
                "mat2 rotationMatrix = rotate2D(-angle * TAU / 360.0);\n"
                "    uv = rotationMatrix * uv;"),
            "vector-matrix": source.replace(
                "rotate2D(-angle * TAU / 360.0) * uv",
                "uv * rotate2D(-angle * TAU / 360.0)"),
            "row-major-custom-lowering": source.replace(
                "return mat2(c, -s, s, c);", "return mat2(c, s, -s, c);").replace(
                    "rotate2D(-angle * TAU / 360.0) * uv",
                    "uv * rotate2D(-angle * TAU / 360.0)"),
            "generic-matrix-helper": source.replace("rotate2D", "matrixHelper"),
        }
        self.assertEqual(7, len(alternatives))
        self.assertEqual(7, len(set(alternatives.values())))
        for name, candidate_source in alternatives.items():
            self.assertNotEqual(source, candidate_source, name)
            candidate_hash = hashlib.sha256(candidate_source.encode()).hexdigest()
            candidate = analyze_program(
                parse_program(candidate_source, exact.key, {}), exact.key)
            self.assertNotEqual(exact, candidate, name)
            with self.subTest(layer="profile", shape=name), self.assertRaises(ValueError):
                authenticate_rotate_mat2_return(candidate, candidate_hash, PROFILE)
            with self.subTest(layer="validator", shape=name), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=candidate_hash,
                    rotate_mat2_return_profile=PROFILE)
            with self.subTest(layer="emitter", shape=name), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    candidate, candidate.key, candidate_hash,
                    rotate_mat2_return_profile=PROFILE)

    def test_task28_schema_generation_and_task27_reconstruction(self) -> None:
        import copy
        import hashlib
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.rotate_mat2_return_profile import PROFILE, ROTATE_KEY
        spec = generate_typed_slice.load_slice(REPOSITORY)
        spec["programs"] = [item for item in spec["programs"]
                            if item["program_key"] not in {
                                "mixer/focusBlur:focusBlur",
                                "filter/extrude:extrude",
                                "synth/curl:curl",
                                "filter/grade:creative",
                                "filter/grade:hslSecondary",
                                "filter/grade:lut",
                                "filter/grade:primary",
                                "filter/grade:vignette",
                                "filter/grade:wheels"}]
        keys = [item["program_key"] for item in spec["programs"]]
        self.assertEqual((128, 67, "30f0333cfd995ba1b866fcbd9589507151255204088675bae6575e42d7328c55"),
                         (len(keys), keys.index(ROTATE_KEY), hashlib.sha256(
                             ("\n".join(keys) + "\n").encode()).hexdigest()))
        self.assertEqual(("filter/ridge:ridge", ROTATE_KEY, "filter/scale:scale"),
                         tuple(keys[66:69]))
        self.assertEqual([{"defines": {}, "program_key": ROTATE_KEY,
                           "rotate_mat2_return_profile": PROFILE}],
                         [item for item in spec["programs"]
                          if "rotate_mat2_return_profile" in item])
        current = generate_typed_slice.generate_outputs(REPOSITORY)
        manifest = json.loads(current["src/typed_generated/typed_manifest.json"])
        rotate = next(item for item in manifest["programs"]
                      if item["program_key"] == ROTATE_KEY)
        self.assertEqual(PROFILE, rotate["rotate_mat2_return_profile"])
        prior_spec = copy.deepcopy(spec)
        prior_spec["programs"] = [item for item in prior_spec["programs"]
                                  if item["program_key"] != ROTATE_KEY]
        with mock.patch.object(generate_typed_slice, "load_slice", return_value=prior_spec):
            prior = generate_typed_slice.generate_outputs(REPOSITORY)
        prior["include/noisemaker/generated/catalog.hpp"] = (
            generate_typed_slice.render_catalog_header(prior_spec))
        expected = {
            "src/typed_generated/typed_slice.cpp": "aa15e469d2283ac4f919a3f61edf85f5046f414674ff3cebdb85e5c06d2327c5",
            "src/typed_generated/typed_manifest.json": "f25401d49121ad6dcda189730b6e99ca5946fb0fafd2fbac83c637740ea1cd58",
            "include/noisemaker/generated/catalog.hpp": "b82abfa09c224185a4152d487d290d9b6bc475bb15ae744ddc3550c86ded1da5",
        }
        for path, digest in expected.items():
            self.assertEqual(digest, hashlib.sha256(prior[path]).hexdigest())

    def test_task28_cpp_tables_are_exact_executable_frozen_transcription(self) -> None:
        import hashlib
        import struct
        oracle_bytes = pathlib.Path(
            REPOSITORY / "tests/oracles/task-28-oracles.json").read_bytes()
        self.assertEqual(
            "db74b7e1883c1d9f71ec00caa80451793c404039bfd26943be4844faaeef3b44",
            hashlib.sha256(oracle_bytes).hexdigest())
        oracle = json.loads(oracle_bytes)
        cpp = (REPOSITORY / "tests/test_generated_kernels.cpp").read_text()
        parsed = _task28_parse_executable_tables(cpp)
        f32 = lambda value: int.from_bytes(struct.pack("<f", value), "little")
        cases = []
        for item in oracle["cases"]:
            probes = [value for probe in item["output"]["probes"]
                      for value in (*probe["at_top_down_xy"],
                                    *(int(bits, 16) for bits in probe["f32_bits_le"]))]
            cases.append([item["name"], item["dimensions"]["width"],
                          item["dimensions"]["height"], item["phase"],
                          f32(item["time"]), f32(item["uniforms"]["rotation"]),
                          item["uniforms"]["wrap"], item["uniforms"]["speed"],
                          item["input"]["f32_sha256"], item["output"]["f32_sha256"],
                          item["output"]["rgba8_sha256"], probes,
                          item["output"]["finite_lanes"]])
        rows = []
        for item in oracle["direct_matrix_cases"]:
            rows.append([int(item["input"]["angle_f32_bits_le"], 16),
                         [int(value, 16) for value in item["input"]["vector_f32_bits_le"]],
                         int(item["cos_f32_bits_le"], 16),
                         int(item["sin_f32_bits_le"], 16),
                         [[int(value, 16) for value in mode["matrix_lane_f32_bits_le"]]
                          for mode in item["modes"]],
                         [[int(value, 16) for value in mode["product_f32_bits_le"]]
                          for mode in item["modes"]]])
        self.assertEqual(cases, parsed["cases"])
        parsed_rows = [[*row[:4], row[4][0], row[5][0]]
                       for row in parsed["matrices"]]
        self.assertEqual(rows, parsed_rows)
        self.assertEqual([item["name"] for item in oracle["direct_matrix_modes"]],
                         parsed["names"])
        mode_names = ["exact_direct", "transposed", "row_major", "diagonal",
                      "wrong_sine_sign", "helper_local"]
        self.assertEqual([[name, ordinal] for ordinal, name in enumerate(mode_names)],
                         parsed["mode_enum"])
        self.assertEqual([["direct_return", 0], ["local_return", 1]],
                         parsed["return_shape_enum"])
        self.assertEqual(mode_names, parsed["dispatch"])
        self.assertEqual([[name, "local_return" if name == "helper_local"
                           else "direct_return"] for name in mode_names],
                         parsed["shape_by_mode"])
        self.assertEqual(
            "[[nodiscard]]noisemaker::glsl::Mat2task28_local(floatc,floats)"
            "{constnoisemaker::glsl::Mat2local(noisemaker::glsl::Vec2(c,-s),"
            "noisemaker::glsl::Vec2(s,c));returnlocal;}", parsed["helper"])
        expected_arms = {
            "exact_direct": "matrix=noisemaker::glsl::Mat2(noisemaker::glsl::Vec2(c,-s),noisemaker::glsl::Vec2(s,c));product=matrix*v;break;",
            "transposed": "matrix=noisemaker::glsl::Mat2(noisemaker::glsl::Vec2(c,s),noisemaker::glsl::Vec2(-s,c));product=matrix*v;break;",
            "row_major": "matrix=noisemaker::glsl::Mat2(noisemaker::glsl::Vec2(c,-s),noisemaker::glsl::Vec2(s,c));product=noisemaker::glsl::Vec2(noisemaker::f32(static_cast<double>(matrix[0][0])*v[0]+static_cast<double>(matrix[0][1])*v[1]),noisemaker::f32(static_cast<double>(matrix[1][0])*v[0]+static_cast<double>(matrix[1][1])*v[1]));break;",
            "diagonal": "matrix=noisemaker::glsl::Mat2(noisemaker::glsl::Vec2(c,0.0f),noisemaker::glsl::Vec2(0.0f,c));product=matrix*v;break;",
            "wrong_sine_sign": "matrix=noisemaker::glsl::Mat2(noisemaker::glsl::Vec2(c,s),noisemaker::glsl::Vec2(s,c));product=matrix*v;break;",
            "helper_local": "matrix=task28_local(c,s);product=matrix*v;shape=Task28ReturnShape::local_return;break;",
        }
        self.assertEqual([[name, expected_arms[name]] for name in mode_names],
                         parsed["arms"])
        self.assertEqual(
            'throwstd::invalid_argument("unhandledTask28matrixmode");',
            parsed["default"])
        self.assertEqual(
            "conststd::size_tid=static_cast<std::size_t>(mode);return{mode,"
            "kTask28ModeNames[id],shape,{noisemaker::float_bits_to_uint(matrix[0][0]),"
            "noisemaker::float_bits_to_uint(matrix[0][1]),noisemaker::float_bits_to_uint(matrix[1][0]),"
            "noisemaker::float_bits_to_uint(matrix[1][1])},{noisemaker::float_bits_to_uint(product[0]),"
            "noisemaker::float_bits_to_uint(product[1])}};",
            parsed["witness_epilogue"])
        helper_tampered = cpp.replace(
            "matrix=task28_local(c,s);product=matrix*v;shape=Task28ReturnShape::local_return;break;",
            "matrix=noisemaker::glsl::Mat2(noisemaker::glsl::Vec2(c,-s),noisemaker::glsl::Vec2(s,c));product=matrix*v;shape=Task28ReturnShape::local_return;break;",
            1)
        self.assertNotEqual(parsed, _task28_parse_executable_tables(helper_tampered))
        executable_begin = cpp.index(
            "[[nodiscard]] noisemaker::glsl::Mat2 task28_local")
        witness_begin = cpp.index(
            "[[nodiscard]] Task28MatrixWitness task28_matrix_witness")
        witness_body = cpp.index("\n}\n", witness_begin) + 2
        executable = cpp[executable_begin:witness_body]
        executable_tokens = list(re.finditer(
            r'"[^"\n]*"|::|==|!=|<=|>=|&&|\|\||'
            r'\b(?:0x[0-9a-fA-F]+|[0-9]+(?:\.[0-9]+)?f?)\b|'
            r'\b[A-Za-z_][A-Za-z0-9_]*\b|[{}()\[\],;:+\-*/=<>]',
            executable))
        self.assertGreater(len(executable_tokens), 250)
        for ordinal, token in enumerate(executable_tokens):
            old = token.group(0)
            if old.startswith('"'):
                new = old[:-1] + 'X"'
            elif re.match(r"[A-Za-z_]", old):
                new = old + "X"
            elif re.match(r"(?:0x|[0-9])", old):
                new = "7" if old != "7" else "8"
            else:
                new = "@"
            changed_region = (executable[:token.start()] + new
                              + executable[token.end():])
            tampered = (cpp[:executable_begin] + changed_region
                        + cpp[witness_body:])
            try:
                changed = _task28_parse_executable_tables(tampered)
            except (AssertionError, SyntaxError, ValueError):
                continue
            self.assertNotEqual(parsed, changed,
                                f"switch/witness token {ordinal}: {old}")
        begin = cpp.index("// TASK28_NATIVE_ORACLE_TABLE_BEGIN")
        end = cpp.index("// TASK28_NATIVE_ORACLE_TABLE_END")
        table = cpp[begin:end]
        tokens = list(re.finditer(r'"[^"\n]+"|\b(?:0x[0-9a-f]+|[0-9]+)U\b', table))
        self.assertGreater(len(tokens), 300)
        for ordinal, token in enumerate(tokens):
            old = token.group(0)
            new = (old[:-1] + ("X\"" if old.startswith('"') else "1U"))
            tampered_table = table[:token.start()] + new + table[token.end():]
            tampered = cpp[:begin] + tampered_table + cpp[end:]
            try:
                changed = _task28_parse_executable_tables(tampered)
            except (AssertionError, SyntaxError, ValueError):
                continue
            self.assertNotEqual(parsed, changed, f"executable token {ordinal}: {old}")
        self.assertEqual(
            "db74b7e1883c1d9f71ec00caa80451793c404039bfd26943be4844faaeef3b44",
            hashlib.sha256(oracle_bytes).hexdigest())


class Task29FocusBlurBorrowedSamplerTests(unittest.TestCase):
    @staticmethod
    def exact_program():
        import hashlib
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.focus_blur_borrowed_sampler_profile import (
            FOCUS_BLUR_KEY)
        from tools.glslcpp.frontend.semantic import analyze_program

        source = (REPOSITORY / "tools/glslcpp/corpus/"
                  "a024dc3a960cc44af454abc7aebce50456c194e6/"
                  "sources/mixer/focusBlur/focusBlur.glsl").read_text()
        return (source, hashlib.sha256(source.encode()).hexdigest(),
                analyze_program(parse_program(source, FOCUS_BLUR_KEY, {}),
                                FOCUS_BLUR_KEY))

    def test_task29_exact_profile_owns_complete_candidate_ancestry_and_emits_narrow_abi(self) -> None:
        import dataclasses
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.focus_blur_borrowed_sampler_profile import (
            PROFILE, apply_focus_blur_borrowed_sampler_parameters,
            authenticate_focus_blur_borrowed_sampler_parameters)

        _, source_hash, exact = self.exact_program()
        proof = authenticate_focus_blur_borrowed_sampler_parameters(
            exact, source_hash, PROFILE)
        helper = exact.functions[0]
        main = exact.functions[3]
        conditional = main.body[3]
        self.assertIs(helper, proof.helper)
        self.assertEqual((helper.parameters[0], helper.parameters[1]),
                         proof.sampler_parameters)
        self.assertEqual((14, 14, 13, 13),
                         tuple(item.symbol_id for item in proof.sampler_uses))
        self.assertEqual((57, 59),
                         tuple(item.span.start_line for item in proof.calls))
        self.assertEqual(((2, 1, 33), (1, 2, 33)), tuple(
            tuple(child.symbol_id for child in call.children)
            for call in proof.calls))
        self.assertIs(conditional, proof.conditional)
        self.assertIs(conditional.expressions[0], proof.predicate)
        self.assertEqual(conditional.children, proof.branches)
        self.assertEqual((3, 3), tuple(map(len, proof.statement_parent_chains)))
        for ordinal, chain in enumerate(proof.statement_parent_chains):
            self.assertIs(conditional, chain[0])
            self.assertIs(proof.branches[ordinal], chain[1])
            self.assertIs(proof.calls[ordinal],
                          chain[2].expressions[0].children[1])
        self.assertEqual(25, len(proof.consumed_objects))
        self.assertEqual(25, len({id(item) for item in proof.consumed_objects}))
        self.assertIs(exact, apply_focus_blur_borrowed_sampler_parameters(
            exact, source_hash, PROFILE))

        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                exact, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(exact, exact.key, source_hash)
        generate_typed_slice.validate_capabilities(
            exact, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash,
            focus_blur_borrowed_sampler_profile=PROFILE)
        emitted = render_typed_cpp(
            exact, exact.key, source_hash,
            focus_blur_borrowed_sampler_profile=PROFILE)
        signature = (
            "glsl::Vec4 applyFocusBlur([[maybe_unused]] const State& state, "
            "[[maybe_unused]] const glsl::PixelContext& context, "
            "[[maybe_unused]] const Surface& sceneTex, "
            "[[maybe_unused]] const Surface& depthTex, "
            "[[maybe_unused]] glsl::Vec2 uv) noexcept")
        self.assertEqual(2, emitted.count(signature))
        self.assertEqual(1, emitted.count(
            "applyFocusBlur(state, context, *state.tex, *state.inputTex, uv)"))
        self.assertEqual(1, emitted.count(
            "applyFocusBlur(state, context, *state.inputTex, *state.tex, uv)"))
        helper_start = emitted.index(signature, emitted.index(signature) + 1)
        helper_end = emitted.index("\n}\n\nvoid pixel(", helper_start)
        helper_cpp = emitted[helper_start:helper_end]
        self.assertEqual(2, helper_cpp.count("sample_texture("))
        self.assertEqual(2, helper_cpp.count("texture_size("))
        self.assertRegex(emitted, r"const Surface\* inputTex;")
        self.assertRegex(emitted, r"const Surface\* tex;")
        self.assertNotRegex(
            helper_cpp,
            r"(?:Surface\s+[A-Za-z_]|Surface\s*\*|(?<!const )Surface\s*&|"
            r"reference_wrapper|shared_ptr|unique_ptr|std::span|new\s+Surface|"
            r"delete|alloca|throw|try\s*\{|dynamic_cast|const_cast)")

        def reconstruct(value):
            if dataclasses.is_dataclass(value):
                return dataclasses.replace(value, **{
                    field.name: reconstruct(getattr(value, field.name))
                    for field in dataclasses.fields(value)})
            if isinstance(value, tuple):
                return tuple(reconstruct(item) for item in value)
            return value

        rebuilt = reconstruct(exact)
        rebuilt_proof = authenticate_focus_blur_borrowed_sampler_parameters(
            rebuilt, source_hash, PROFILE)
        self.assertEqual(exact, rebuilt)
        self.assertTrue(all(not any(old is own for old in proof.consumed_objects)
                            for own in rebuilt_proof.consumed_objects))
        generate_typed_slice.validate_capabilities(
            rebuilt, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash,
            focus_blur_borrowed_sampler_profile=PROFILE)
        render_typed_cpp(
            rebuilt, rebuilt.key, source_hash,
            focus_blur_borrowed_sampler_profile=PROFILE)
        with mock.patch.object(
                generate_typed_slice,
                "authenticate_focus_blur_borrowed_sampler_parameters",
                return_value=proof), self.assertRaises(
                    generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                rebuilt, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                focus_blur_borrowed_sampler_profile=PROFILE)
        with mock.patch(
                "tools.glslcpp.emit_typed_cpp."
                "authenticate_focus_blur_borrowed_sampler_parameters",
                return_value=proof), self.assertRaises(TypedEmissionError):
            render_typed_cpp(
                rebuilt, rebuilt.key, source_hash,
                focus_blur_borrowed_sampler_profile=PROFILE)

    def test_task29_exhaustive_single_axis_protected_coordinate_negative_closure(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.focus_blur_borrowed_sampler_profile import (
            PROFILE, authenticate_focus_blur_borrowed_sampler_parameters)
        from tools.glslcpp.frontend.semantic_types import FLOAT, INT, array, vector
        from tools.glslcpp.frontend.typed_ir import PreprocessorDefine

        _, source_hash, exact = self.exact_program()

        def at(value, path):
            for part in path:
                value = value[part] if isinstance(part, int) else getattr(value, part)
            return value

        def replaced(value, path, replacement):
            if len(path) == 1:
                part = path[0]
                if isinstance(part, int):
                    items = list(value); items[part] = replacement
                    return tuple(items)
                return dataclasses.replace(value, **{part: replacement})
            part = path[0]
            child = value[part] if isinstance(part, int) else getattr(value, part)
            updated = replaced(child, path[1:], replacement)
            if isinstance(part, int):
                items = list(value); items[part] = updated
                return tuple(items)
            return dataclasses.replace(value, **{part: updated})

        helper = exact.functions[0]
        main = exact.functions[3]
        then_call = main.body[3].children[0].children[0].expressions[0].children[1]
        else_call = main.body[3].children[1].children[0].expressions[0].children[1]
        depth_use = helper.body[0].expressions[0].children[0].children[0]
        depth_size_use = helper.body[0].expressions[0].children[0].children[1].children[1].children[0].children[0]
        scene_use = helper.body[5].children[1].children[3].expressions[0].children[1].children[0]
        scene_size_use = helper.body[5].children[1].children[3].expressions[0].children[1].children[1].children[1].children[0].children[0]
        axes = {
            "program-key": (("key",), "mixer/focusBlur:foreign"),
            "normalized-source": (("source",), exact.source + " "),
            "raw-source": (("raw_source",), exact.raw_source + " "),
            "body-status": (("body_status",), "task29-mutated"),
            "define-name": (("preprocessor_defines",),
                            (PreprocessorDefine("TASK29", "int", "1"),)),
            "local-type": (("local_type_names",), ("Task29Sampler",)),
            "struct": (("structs",), (object(),)),
            "uniform-block": (("uniform_blocks",), (object(),)),
            "resource-uniform-order": (("resources", "uniforms"),
                                       tuple(reversed(exact.resources.uniforms))),
            "resource-uniform-count": (("resources", "uniforms"),
                                       exact.resources.uniforms[:-1]),
            "resource-sampler-order": (("resources", "samplers"),
                                       tuple(reversed(exact.resources.samplers))),
            "resource-sampler-count": (("resources", "samplers"),
                                       exact.resources.samplers[:1]),
            "resource-output": (("resources", "outputs", 0), "otherColor"),
            "resource-texture": (("resources", "uses_texture"), False),
            "resource-derivative": (("resources", "uses_derivatives"), True),
            "interface-count": (("interface_symbols",),
                                (exact.declarations[0].symbol,)),
            "builtin-count": (("builtin_symbols",), ()),
            "declaration-order": (("declarations",),
                                  tuple(reversed(exact.declarations))),
            "declaration-count": (("declarations",), exact.declarations[:-1]),
            "input-symbol-id": (("declarations", 0, "symbol", "id"), 101),
            "input-symbol-name": (("declarations", 0, "symbol", "name"), "otherTex"),
            "input-storage": (("declarations", 0, "symbol", "storage"), "local"),
            "input-writable": (("declarations", 0, "symbol", "writable"), True),
            "input-direction": (("declarations", 0, "symbol", "direction"), "out"),
            "input-type": (("declarations", 0, "type"), FLOAT),
            "input-span": (("declarations", 0, "span", "start_column"), 2),
            "loop-count": (("counted_loop_proof", "loop_count"), 2),
            "loop-unproved": (("counted_loop_proof", "unproved_loop_count"), 1),
            "loop-depth": (("counted_loop_proof", "max_effective_depth"), 2),
            "loop-product": (("counted_loop_proof", "max_lexical_product"), 63),
            "loop-charge": (("counted_loop_proof", "entrypoint_charge"), 65),
            "call-graph-cycle": (("counted_loop_proof", "call_graph_acyclic"), False),
            "function-order": (("functions",), tuple(reversed(exact.functions))),
            "function-count": (("functions",), exact.functions[:-1]),
            "helper-id": (("functions", 0, "signature", "id"), 116),
            "helper-name": (("functions", 0, "signature", "name"), "otherFocusBlur"),
            "helper-return": (("functions", 0, "signature", "return_type"), FLOAT),
            "helper-span": (("functions", 0, "span", "start_line"), 28),
            "helper-body-count": (("functions", 0, "body"), helper.body[:-1]),
            "parameter-count": (("functions", 0, "signature", "parameters"),
                                helper.parameters[:-1]),
            "parameter-order": (("functions", 0, "signature", "parameters"),
                                (helper.parameters[1], helper.parameters[0],
                                 helper.parameters[2])),
            "scene-parameter-id": (("functions", 0, "signature", "parameters", 0, "id"), 113),
            "scene-parameter-name": (("functions", 0, "signature", "parameters", 0, "name"), "sceneOther"),
            "scene-parameter-storage": (("functions", 0, "signature", "parameters", 0, "storage"), "local"),
            "scene-parameter-direction": (("functions", 0, "signature", "parameters", 0, "direction"), "inout"),
            "scene-parameter-writable": (("functions", 0, "signature", "parameters", 0, "writable"), False),
            "scene-parameter-scalar": (("functions", 0, "signature", "parameters", 0, "type"), FLOAT),
            "scene-parameter-vector": (("functions", 0, "signature", "parameters", 0, "type"), vector("float", 4)),
            "scene-parameter-array": (("functions", 0, "signature", "parameters", 0, "type"), array(helper.parameters[0].type, 2)),
            "scene-parameter-span": (("functions", 0, "signature", "parameters", 0, "span", "start_column"), 20),
            "depth-parameter-id": (("functions", 0, "signature", "parameters", 1, "id"), 114),
            "depth-parameter-name": (("functions", 0, "signature", "parameters", 1, "name"), "depthOther"),
            "depth-parameter-direction": (("functions", 0, "signature", "parameters", 1, "direction"), "out"),
            "depth-parameter-type": (("functions", 0, "signature", "parameters", 1, "type"), INT),
            "uv-parameter-type": (("functions", 0, "signature", "parameters", 2, "type"), vector("float", 3)),
            "depth-use-id": (("functions", 0, "body", 0, "expressions", 0, "children", 0, "children", 0, "symbol_id"), 13),
            "depth-use-name": (("functions", 0, "body", 0, "expressions", 0, "children", 0, "children", 0, "symbol", "name"), "sceneTex"),
            "depth-use-span": (("functions", 0, "body", 0, "expressions", 0, "children", 0, "children", 0, "span", "start_column"), 31),
            "depth-size-use-id": (("functions", 0, "body", 0, "expressions", 0, "children", 0, "children", 1, "children", 1, "children", 0, "children", 0, "symbol_id"), 13),
            "scene-use-id": (("functions", 0, "body", 5, "children", 1, "children", 3, "expressions", 0, "children", 1, "children", 0, "symbol_id"), 14),
            "scene-size-use-id": (("functions", 0, "body", 5, "children", 1, "children", 3, "expressions", 0, "children", 1, "children", 1, "children", 1, "children", 0, "children", 0, "symbol_id"), 14),
            "loop-trip": (("functions", 0, "body", 5, "loop_proof", "trip_count"), 63),
            "loop-bound": (("functions", 0, "body", 5, "loop_proof", "bound_value"), 65),
            "loop-comparison": (("functions", 0, "body", 5, "loop_proof", "comparison"), "<="),
            "loop-update": (("functions", 0, "body", 5, "loop_proof", "update"), "--"),
            "main-id": (("functions", 3, "signature", "id"), 119),
            "main-body-count": (("functions", 3, "body"), main.body[:-1]),
            "if-kind": (("functions", 3, "body", 3, "kind"), "block"),
            "if-span": (("functions", 3, "body", 3, "span", "start_line"), 55),
            "predicate-operator": (("functions", 3, "body", 3, "expressions", 0, "operator"), "!="),
            "predicate-kind": (("functions", 3, "body", 3, "expressions", 0, "kind"), "builtin"),
            "predicate-symbol": (("functions", 3, "body", 3, "expressions", 0, "children", 0, "symbol_id"), 8),
            "predicate-literal": (("functions", 3, "body", 3, "expressions", 0, "children", 1, "literal_value"), 1),
            "predicate-span": (("functions", 3, "body", 3, "expressions", 0, "span", "start_column"), 8),
            "branch-order": (("functions", 3, "body", 3, "children"),
                             tuple(reversed(main.body[3].children))),
            "then-kind": (("functions", 3, "body", 3, "children", 0, "kind"), "expr"),
            "else-kind": (("functions", 3, "body", 3, "children", 1, "kind"), "expr"),
            "then-statement-count": (("functions", 3, "body", 3, "children", 0, "children"), ()),
            "else-statement-count": (("functions", 3, "body", 3, "children", 1, "children"), ()),
            "then-parent-operator": (("functions", 3, "body", 3, "children", 0, "children", 0, "expressions", 0, "operator"), "+="),
            "else-parent-operator": (("functions", 3, "body", 3, "children", 1, "children", 0, "expressions", 0, "operator"), "+="),
            "then-call-kind": (("functions", 3, "body", 3, "children", 0, "children", 0, "expressions", 0, "children", 1, "kind"), "builtin"),
            "then-call-signature": (("functions", 3, "body", 3, "children", 0, "children", 0, "expressions", 0, "children", 1, "signature_id"), 999),
            "then-call-span": (("functions", 3, "body", 3, "children", 0, "children", 0, "expressions", 0, "children", 1, "span", "start_column"), 16),
            "then-call-arity": (("functions", 3, "body", 3, "children", 0, "children", 0, "expressions", 0, "children", 1, "children"), then_call.children[:-1]),
            "then-scene-argument": (("functions", 3, "body", 3, "children", 0, "children", 0, "expressions", 0, "children", 1, "children", 0), then_call.children[1]),
            "then-depth-argument": (("functions", 3, "body", 3, "children", 0, "children", 0, "expressions", 0, "children", 1, "children", 1), then_call.children[0]),
            "else-scene-argument": (("functions", 3, "body", 3, "children", 1, "children", 0, "expressions", 0, "children", 1, "children", 0), else_call.children[1]),
            "else-depth-argument": (("functions", 3, "body", 3, "children", 1, "children", 0, "expressions", 0, "children", 1, "children", 1), else_call.children[0]),
        }
        candidates = {name: replaced(exact, path, value)
                      for name, (path, value) in axes.items()}
        self.assertEqual(len(axes), len(candidates))
        self.assertEqual(89, len(candidates))
        self.assertEqual(
            "30f64470c71e4b2b5a6626e40b3f3a5a329384b9328b6d5dc74719e47ad95499",
            hashlib.sha256(("\n".join(sorted(candidates)) + "\n").encode()).hexdigest())
        self.assertEqual(len(candidates), len(set(candidates.values())))
        for name, candidate in candidates.items():
            selected_path, expected = axes[name]
            self.assertNotEqual(exact, candidate, name)
            self.assertEqual(expected, at(candidate, selected_path), name)
            for protected_name, (protected_path, _) in axes.items():
                if protected_name == name:
                    continue
                overlap = (selected_path == protected_path[:len(selected_path)]
                           or protected_path == selected_path[:len(protected_path)])
                if not overlap:
                    self.assertEqual(
                        at(exact, protected_path), at(candidate, protected_path),
                        f"{name} changed protected coordinate {protected_name}")
            with self.subTest(axis=name, layer="profile"), self.assertRaises(ValueError):
                authenticate_focus_blur_borrowed_sampler_parameters(
                    candidate, source_hash, PROFILE)
            with self.subTest(axis=name, layer="validator"), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash,
                    focus_blur_borrowed_sampler_profile=PROFILE)
            with self.subTest(axis=name, layer="emitter"), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    candidate, candidate.key, source_hash,
                    focus_blur_borrowed_sampler_profile=PROFILE)

        self.assertEqual((14, 14, 13, 13),
                         (depth_use.symbol_id, depth_size_use.symbol_id,
                          scene_use.symbol_id, scene_size_use.symbol_id))

    def test_task29_complete_call_ancestry_move_copy_swap_and_predicate_controls_reject(self) -> None:
        import dataclasses
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.focus_blur_borrowed_sampler_profile import (
            PROFILE, authenticate_focus_blur_borrowed_sampler_parameters)

        _, source_hash, exact = self.exact_program()
        main = exact.functions[3]
        conditional = main.body[3]
        then_branch, else_branch = conditional.children
        then_statement = then_branch.children[0]
        else_statement = else_branch.children[0]
        then_call = then_statement.expressions[0].children[1]
        else_call = else_statement.expressions[0].children[1]

        def with_conditional(value, *, before=(), after=()):
            changed_main = dataclasses.replace(
                main, body=(*main.body[:3], *before, value, *after,
                            *main.body[4:]))
            return dataclasses.replace(
                exact, functions=(*exact.functions[:3], changed_main))

        reconstructed_predicate = dataclasses.replace(
            conditional.expressions[0], children=tuple(dataclasses.replace(child)
                                                        for child in conditional.expressions[0].children))
        controls = {
            "predicate-replacement": with_conditional(dataclasses.replace(
                conditional, expressions=(dataclasses.replace(
                    conditional.expressions[0], operator="!="),))),
            "branch-swap": with_conditional(dataclasses.replace(
                conditional, children=(else_branch, then_branch))),
            "call-slot-swap": with_conditional(dataclasses.replace(
                conditional, children=(dataclasses.replace(
                    then_branch, children=(else_statement,)),
                    dataclasses.replace(else_branch, children=(then_statement,))))),
            "call-copy-then": with_conditional(dataclasses.replace(
                conditional, children=(dataclasses.replace(
                    then_branch, children=(then_statement, then_statement)),
                    else_branch))),
            "call-copy-else": with_conditional(dataclasses.replace(
                conditional, children=(then_branch, dataclasses.replace(
                    else_branch, children=(else_statement, else_statement))))),
            "both-calls-then": with_conditional(dataclasses.replace(
                conditional, children=(dataclasses.replace(
                    then_branch, children=(then_statement, else_statement)),
                    else_branch))),
            "call-move-outside-before": with_conditional(dataclasses.replace(
                conditional, children=(dataclasses.replace(
                    then_branch, children=()), else_branch)), before=(then_statement,)),
            "call-move-outside-after": with_conditional(dataclasses.replace(
                conditional, children=(then_branch, dataclasses.replace(
                    else_branch, children=()))), after=(else_statement,)),
            "call-removed": with_conditional(dataclasses.replace(
                conditional, children=(dataclasses.replace(
                    then_branch, children=()), else_branch))),
        }
        self.assertEqual(9, len(controls))
        for name, candidate in controls.items():
            self.assertNotEqual(exact, candidate, name)
            for layer, invoke, error in (
                    ("profile", lambda c=candidate:
                     authenticate_focus_blur_borrowed_sampler_parameters(
                         c, source_hash, PROFILE), ValueError),
                    ("validator", lambda c=candidate:
                     generate_typed_slice.validate_capabilities(
                         c, generate_typed_slice.APPROVED_CAPABILITIES,
                         source_hash=source_hash,
                         focus_blur_borrowed_sampler_profile=PROFILE),
                     generate_typed_slice.GeneratorError),
                    ("emitter", lambda c=candidate: render_typed_cpp(
                         c, c.key, source_hash,
                         focus_blur_borrowed_sampler_profile=PROFILE),
                     TypedEmissionError)):
                with self.subTest(control=name, layer=layer), self.assertRaises(error):
                    invoke()

        rebuilt = dataclasses.replace(
            exact, functions=(*exact.functions[:3], dataclasses.replace(
                main, body=(*main.body[:3], dataclasses.replace(
                    conditional, expressions=(reconstructed_predicate,)),
                            *main.body[4:]))))
        rebuilt_proof = authenticate_focus_blur_borrowed_sampler_parameters(
            rebuilt, source_hash, PROFILE)
        self.assertEqual(exact, rebuilt)
        self.assertIs(reconstructed_predicate, rebuilt_proof.predicate)
        old_proof = authenticate_focus_blur_borrowed_sampler_parameters(
            exact, source_hash, PROFILE)
        with mock.patch.object(
                generate_typed_slice,
                "authenticate_focus_blur_borrowed_sampler_parameters",
                return_value=old_proof), self.assertRaises(
                    generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                rebuilt, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                focus_blur_borrowed_sampler_profile=PROFILE)
        self.assertIsNot(then_call, else_call)

    def test_task29_full_carrier_caller_numeric_defines_and_coexistence_matrix(self) -> None:
        import dataclasses
        from itertools import product
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.focus_blur_borrowed_sampler_profile import (
            PROFILE, authenticate_focus_blur_borrowed_sampler_parameters)
        from tools.glslcpp.frontend.typed_ir import PreprocessorDefine

        _, source_hash, exact = self.exact_program()
        define_variants = {
            "empty": (),
            "name": (PreprocessorDefine("TASK29_NAME", "int", "1"),),
            "value": (PreprocessorDefine("TASK29_VALUE", "int", "2"),),
            "count": (PreprocessorDefine("TASK29_A", "int", "1"),
                      PreprocessorDefine("TASK29_B", "int", "2")),
            "order": (PreprocessorDefine("TASK29_B", "int", "2"),
                      PreprocessorDefine("TASK29_A", "int", "1")),
        }
        carriers = {"exact": PROFILE, "absent": None,
                    "foreign": "focus-blur-borrowed-sampler-foreign"}
        caller_hashes = {"exact": source_hash, "absent": None,
                         "wrong": "0" * 64}
        numerics = {"exact": "glsl-f32", "wrong": "source-double"}
        accepted = 0
        matrix_count = 0
        for (define_name, defines), (carrier_name, carrier), (
                hash_name, caller_hash), (numeric_name, numeric) in product(
                    define_variants.items(), carriers.items(),
                    caller_hashes.items(), numerics.items()):
            matrix_count += 1
            candidate = dataclasses.replace(exact, preprocessor_defines=defines)
            label = (define_name, carrier_name, hash_name, numeric_name)
            profile_ok = (define_name, carrier_name, hash_name) == (
                "empty", "exact", "exact")
            pipeline_ok = profile_ok and numeric_name == "exact"
            if profile_ok:
                authenticate_focus_blur_borrowed_sampler_parameters(
                    candidate, caller_hash, carrier)
            else:
                with self.subTest(layer="profile", coordinates=label), self.assertRaises(ValueError):
                    authenticate_focus_blur_borrowed_sampler_parameters(
                        candidate, caller_hash, carrier)
            if pipeline_ok:
                accepted += 1
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=caller_hash, numeric_literal_contract=numeric,
                    focus_blur_borrowed_sampler_profile=carrier)
                render_typed_cpp(
                    candidate, candidate.key, caller_hash,
                    numeric_literal_contract=numeric,
                    focus_blur_borrowed_sampler_profile=carrier)
            else:
                with self.subTest(layer="validator", coordinates=label), self.assertRaises(
                        generate_typed_slice.GeneratorError):
                    generate_typed_slice.validate_capabilities(
                        candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=caller_hash, numeric_literal_contract=numeric,
                        focus_blur_borrowed_sampler_profile=carrier)
                with self.subTest(layer="emitter", coordinates=label), self.assertRaises(
                        TypedEmissionError):
                    render_typed_cpp(
                        candidate, candidate.key, caller_hash,
                        numeric_literal_contract=numeric,
                        focus_blur_borrowed_sampler_profile=carrier)
        self.assertEqual((90, 1), (matrix_count, accepted))

        coexistence = {
            "compatibility_transform": generate_typed_slice.CRT_COMPATIBILITY_TRANSFORM,
            "custom_comparer_profile": generate_typed_slice.LENS_CUSTOM_COMPARER_PROFILE,
            "source_global_literal_int_profile": generate_typed_slice.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
            "gather_sorted_round_profile": generate_typed_slice.GATHER_SORTED_ROUND_PROFILE,
            "literal_vec3_lane_index_profile": generate_typed_slice.LITERAL_VEC3_LANE_INDEX_PROFILE,
            "smooth_edge_luma_weights_profile": generate_typed_slice.SMOOTH_EDGE_LUMA_WEIGHTS_PROFILE,
            "perlin_scalar_uint_xor_profile": generate_typed_slice.PERLIN_SCALAR_UINT_XOR_PROFILE,
            "rotate_mat2_return_profile": generate_typed_slice.ROTATE_MAT2_RETURN_PROFILE,
        }
        self.assertEqual(8, len(coexistence))
        for name, value in coexistence.items():
            kwargs = {name: value, "focus_blur_borrowed_sampler_profile": PROFILE}
            with self.subTest(layer="validator", coexistence=name), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    exact, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash, **kwargs)
            with self.subTest(layer="emitter", coexistence=name), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(exact, exact.key, source_hash, **kwargs)

    def test_task29_analyzer_produced_sampler_and_call_shape_alternatives_reject_every_boundary(self) -> None:
        import hashlib
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.focus_blur_borrowed_sampler_profile import (
            PROFILE, authenticate_focus_blur_borrowed_sampler_parameters)
        from tools.glslcpp.frontend.semantic import analyze_program

        source, _, exact = self.exact_program()
        canonical_conditional = (
            "if (depthSource == 0) {\n"
            "        color = applyFocusBlur(tex, inputTex, uv);\n"
            "    } else {\n"
            "        color = applyFocusBlur(inputTex, tex, uv);\n"
            "    }")
        alternatives = {
            "helper-rename": source.replace("applyFocusBlur", "otherFocusBlur"),
            "third-sampler": source.replace(
                "sampler2D depthTex, vec2 uv)",
                "sampler2D depthTex, sampler2D extraTex, vec2 uv)").replace(
                    "applyFocusBlur(tex, inputTex, uv)",
                    "applyFocusBlur(tex, inputTex, tex, uv)").replace(
                    "applyFocusBlur(inputTex, tex, uv)",
                    "applyFocusBlur(inputTex, tex, inputTex, uv)"),
            "second-sampler-helper": source.replace(
                "void main() {",
                "vec4 passFocus(sampler2D s, vec2 uv) { return texture(s, uv); }\n\nvoid main() {"),
            "then-swapped": source.replace(
                "applyFocusBlur(tex, inputTex, uv)",
                "applyFocusBlur(inputTex, tex, uv)"),
            "else-duplicated-input": source.replace(
                "applyFocusBlur(inputTex, tex, uv)",
                "applyFocusBlur(inputTex, inputTex, uv)"),
            "predicate-replaced": source.replace("depthSource == 0", "depthSource != 0"),
            "branches-swapped": source.replace(
                canonical_conditional,
                "if (depthSource == 0) {\n"
                "        color = applyFocusBlur(inputTex, tex, uv);\n"
                "    } else {\n"
                "        color = applyFocusBlur(tex, inputTex, uv);\n"
                "    }"),
            "call-copied-then": source.replace(
                "color = applyFocusBlur(tex, inputTex, uv);",
                "color = applyFocusBlur(tex, inputTex, uv);\n"
                "        color += applyFocusBlur(tex, inputTex, uv);"),
            "call-moved-outside": source.replace(
                canonical_conditional,
                "color = applyFocusBlur(tex, inputTex, uv);"),
            "depth-read-from-scene": source.replace(
                "texture(depthTex,", "texture(sceneTex,", 1),
            "scene-read-from-depth": source.replace(
                "texture(sceneTex,", "texture(depthTex,", 1),
            "loop-63": source.replace("i < 64", "i < 63"),
            "loop-65": source.replace("i < 64", "i < 65"),
            "alpha-input-twice": source.replace(
                "texture(tex, gl_FragCoord.xy / vec2(textureSize(tex, 0))).a",
                "texture(inputTex, gl_FragCoord.xy / vec2(textureSize(inputTex, 0))).a"),
        }
        self.assertEqual(14, len(alternatives))
        self.assertEqual(14, len(set(alternatives.values())))
        for name, candidate_source in alternatives.items():
            self.assertNotEqual(source, candidate_source, name)
            candidate_hash = hashlib.sha256(candidate_source.encode()).hexdigest()
            candidate = analyze_program(
                parse_program(candidate_source, exact.key, {}), exact.key)
            self.assertNotEqual(exact, candidate, name)
            with self.subTest(layer="profile", shape=name), self.assertRaises(ValueError):
                authenticate_focus_blur_borrowed_sampler_parameters(
                    candidate, candidate_hash, PROFILE)
            with self.subTest(layer="validator", shape=name), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=candidate_hash,
                    focus_blur_borrowed_sampler_profile=PROFILE)
            with self.subTest(layer="emitter", shape=name), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    candidate, candidate.key, candidate_hash,
                    focus_blur_borrowed_sampler_profile=PROFILE)

    def test_task29_schema_counts_hashes_and_real_task28_reconstruction_isolation(self) -> None:
        import copy
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.frontend.curl_vector_math_profile import CURL_KEY
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
            EXTRUDE_KEY)
        from tools.glslcpp.frontend.focus_blur_borrowed_sampler_profile import (
            FOCUS_BLUR_KEY, PROFILE)

        spec = generate_typed_slice.load_slice(REPOSITORY)
        typed = tuple(item["program_key"] for item in spec["programs"])
        public = tuple(sorted((*typed, "filter/invert:inv", "synth/solid:solid")))
        corpus = json.loads((check_corpus._corpus_root(REPOSITORY) /
                             "manifest.json").read_text())
        unported = tuple(sorted(
            {item["program_key"] for item in corpus["programs"]} - set(public)))
        # Live current state (post-Task32): six filter/grade:* programs have
        # landed on top of Task31, so this is no longer the Task29-era
        # 129/131/81 census, nor the pre-Task32 131/133/79 census.
        self.assertEqual((137, 139, 73, 212),
                         (len(typed), len(public), len(unported),
                          len(corpus["programs"])))
        self.assertEqual(
            "dfb7c7c43d7fd118c4a1b9a266d6957a90b189ec63ac6b0d49538bd853a360d7",
            hashlib.sha256(("\n".join(typed) + "\n").encode()).hexdigest())
        self.assertEqual(
            "a873c537d3d8ffb872859389812ae7c1e68954c9fcd381334eca4998195f319f",
            hashlib.sha256(("\n".join(public) + "\n").encode()).hexdigest())
        self.assertEqual(117, typed.index(FOCUS_BLUR_KEY))
        self.assertEqual(("mixer/channelCombine:channelCombine", FOCUS_BLUR_KEY,
                          "mixer/mashup:mashup"), typed[116:119])
        self.assertEqual([{
            "defines": {},
            "focus_blur_borrowed_sampler_profile": PROFILE,
            "program_key": FOCUS_BLUR_KEY,
        }], [item for item in spec["programs"]
             if "focus_blur_borrowed_sampler_profile" in item])

        current = generate_typed_slice.generate_outputs(REPOSITORY)
        current_header = generate_typed_slice.render_catalog_header(spec)
        manifest = json.loads(current[
            "src/typed_generated/typed_manifest.json"])
        focus_row = next(item for item in manifest["programs"]
                         if item["program_key"] == FOCUS_BLUR_KEY)
        self.assertEqual(PROFILE,
                         focus_row["focus_blur_borrowed_sampler_profile"])
        self.assertEqual({}, focus_row["defines"])

        task28_spec = copy.deepcopy(spec)
        task28_spec["programs"] = [item for item in task28_spec["programs"]
                                   if item["program_key"] not in
                                   (FOCUS_BLUR_KEY, EXTRUDE_KEY, CURL_KEY,
                                    "filter/grade:creative",
                                    "filter/grade:hslSecondary",
                                    "filter/grade:lut",
                                    "filter/grade:primary",
                                    "filter/grade:vignette",
                                    "filter/grade:wheels")]
        task28_keys = tuple(item["program_key"] for item in task28_spec["programs"])
        task28_public = tuple(sorted((*task28_keys, "filter/invert:inv",
                                     "synth/solid:solid")))
        task28_unported = tuple(sorted(
            {item["program_key"] for item in corpus["programs"]}
            - set(task28_public)))
        self.assertEqual((128, 130, 82),
                         (len(task28_keys), len(task28_public),
                          len(task28_unported)))
        self.assertEqual(
            "30f0333cfd995ba1b866fcbd9589507151255204088675bae6575e42d7328c55",
            hashlib.sha256(("\n".join(task28_keys) + "\n").encode()).hexdigest())
        self.assertEqual(
            "102f5436a5416399f2601879c7d5219706111bc64b93989acbb67d973a01b6c5",
            hashlib.sha256(("\n".join(task28_public) + "\n").encode()).hexdigest())
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=task28_spec):
            task28 = generate_typed_slice.generate_outputs(REPOSITORY)
        task28["include/noisemaker/generated/catalog.hpp"] = (
            generate_typed_slice.render_catalog_header(task28_spec))
        expected_task28 = {
            "src/typed_generated/typed_slice.cpp":
                "b53e020b990a88d17de7fcaaa29965c1304cad510e2888cdd4e54ca98900763e",
            "src/typed_generated/typed_manifest.json":
                "612d35229abf0580932cfaf11785311359afe29f20f1ebef5fb925cc91de044e",
            "include/noisemaker/generated/catalog.hpp":
                "372d1f69e1e7db772ddebc05945a714527b22b35f87ca3160bbb8eb85135a4ac",
        }
        for path, expected in expected_task28.items():
            self.assertEqual(expected, hashlib.sha256(task28[path]).hexdigest(), path)

        marker = re.compile(r"(?m)^// Typed IR program: ([^\n]+)\n")
        def blocks(payload):
            source = payload.decode()
            starts = list(marker.finditer(source))
            catalog = source.index(
                "\nnamespace {\nconstexpr std::array<KernelFactory")
            return {match.group(1): source[
                match.start():(starts[index + 1].start()
                               if index + 1 < len(starts) else catalog)]
                for index, match in enumerate(starts)}

        current_blocks = blocks(current["src/typed_generated/typed_slice.cpp"])
        task28_blocks = blocks(task28["src/typed_generated/typed_slice.cpp"])
        self.assertEqual((137, 128), (len(current_blocks), len(task28_blocks)))
        self.assertEqual({FOCUS_BLUR_KEY, EXTRUDE_KEY, CURL_KEY,
                          "filter/grade:creative", "filter/grade:hslSecondary",
                          "filter/grade:lut", "filter/grade:primary",
                          "filter/grade:vignette", "filter/grade:wheels"},
                         set(current_blocks) - set(task28_blocks))
        ordinal = re.compile(r"typed_[0-9]+")
        for key, block in task28_blocks.items():
            with self.subTest(historical_task28_block=key):
                self.assertEqual(
                    ordinal.sub("typed_SENTINEL", block),
                    ordinal.sub("typed_SENTINEL", current_blocks[key]))
        focus = current_blocks[FOCUS_BLUR_KEY]
        self.assertIn("namespace typed_117 {", focus)
        self.assertEqual(2, focus.count("const Surface& sceneTex"))
        self.assertEqual(2, focus.count("const Surface& depthTex"))
        helper_start = focus.index("glsl::Vec4 applyFocusBlur(",
                                   focus.index("glsl::Vec4 applyFocusBlur(") + 1)
        helper_end = focus.index("\n}\n\nvoid pixel(", helper_start)
        helper = focus[helper_start:helper_end]
        self.assertEqual(2, helper.count("sample_texture("))
        self.assertEqual(2, helper.count("texture_size("))
        self.assertIn(
            "for ([[maybe_unused]] std::int32_t i = std::int32_t(0); "
            "(i < std::int32_t(64)); ++i)", helper)
        self.assertNotIn("focus_blur_borrowed_sampler_profile", current_header.decode())

    def test_task29_cpp_tables_switch_helpers_and_witnesses_are_exact_frozen_transcription(self) -> None:
        import hashlib
        import struct

        oracle_bytes = pathlib.Path(
            REPOSITORY / "tests/oracles/task-29-oracles.json").read_bytes()
        self.assertEqual(
            "b16c120e2331d87b61b98154d63954ad52ff328f149ebeb67b66321b73bde0a3",
            hashlib.sha256(oracle_bytes).hexdigest())
        oracle = json.loads(oracle_bytes)
        cpp = (REPOSITORY / "tests/test_generated_kernels.cpp").read_text()
        parsed = _task29_parse_executable_tables(cpp)
        f32 = lambda value: int.from_bytes(struct.pack("<f", float(value)), "little")

        cases = []
        for item in oracle["cases"]:
            probes = [value for probe in item["output"]["probes"]
                      for value in (*probe["at_top_down_xy"],
                                    *(int(bits, 16) for bits in
                                      probe["f32_bits_le"]))]
            cases.append([
                item["name"], item["dimensions"]["width"],
                item["dimensions"]["height"],
                item["source_phases"]["inputTex"],
                item["source_phases"]["tex"],
                float(item["uniforms"]["focalDistance"]),
                float(item["uniforms"]["aperture"]),
                float(item["uniforms"]["sampleBias"]),
                item["uniforms"]["depthSource"],
                [float(value) for value in item["tile_offset"]],
                [float(value) for value in item["full_resolution"]],
                item["borrowed_alias"], item["output"]["f32_sha256"],
                item["output"]["rgba8_sha256"], probes,
                item["output"]["finite_lanes"],
            ])
        self.assertEqual(cases, parsed["cases"])

        modes = oracle["direct_borrow_modes"]
        enum_names = ["exact_depth_a", "exact_depth_b", "exact_alias",
                      "owning_value_copies", "mutable_references",
                      "nullable_nonnull", "wrong_order_depth_a",
                      "nullable_null_depth"]
        self.assertEqual([[name, ordinal] for ordinal, name in enumerate(enum_names)],
                         parsed["mode_enum"])
        expected_ids = list(range(8))
        self.assertEqual(expected_ids, parsed["declared_ids"])
        self.assertEqual(expected_ids, parsed["switch_ids"])
        self.assertEqual(expected_ids,
                         oracle["direct_borrow_harness"]["declared_mode_ids"])
        self.assertEqual(expected_ids,
                         oracle["direct_borrow_harness"]["handled_mode_ids"])
        self.assertEqual(expected_ids,
                         oracle["direct_borrow_harness"]["observed_mode_ids"])
        self.assertEqual(enum_names, parsed["dispatch"])
        self.assertEqual([item["name"] for item in modes], parsed["names"])
        self.assertEqual([int(item["result"]["mixed_f32_bits_le"], 16)
                          for item in modes], parsed["results"])

        branch = {"depthSource==0/then": "then_slot",
                  "depthSource!=0/else": "else_slot"}
        abi = {"const Surface&": "const_reference", "Surface": "value",
               "Surface&": "mutable_reference",
               "const Surface*": "nullable_pointer"}
        role = {None: "none", "inputTex": "input", "tex": "tex"}
        self.assertEqual([branch[item["observed"]["branch_slot"]]
                          for item in modes], parsed["branches"])
        self.assertEqual([abi[item["observed"]["abi_spelling"]]
                          for item in modes], parsed["abis"])
        self.assertEqual([role[item["observed"]["scene_source"]]
                          for item in modes], parsed["scene_roles"])
        self.assertEqual([role[item["observed"]["depth_source"]]
                          for item in modes], parsed["depth_roles"])
        for parsed_name, oracle_name in (
                ("scene_input", "scene_aliases_input"),
                ("scene_tex", "scene_aliases_tex"),
                ("depth_input", "depth_aliases_input"),
                ("depth_tex", "depth_aliases_tex"),
                ("scene_depth", "scene_depth_alias")):
            self.assertEqual([item["observed"][oracle_name] for item in modes],
                             parsed[parsed_name])

        counter_names = (
            "const_ref_bindings", "value_copy_bindings",
            "mutable_ref_bindings", "nullable_pointer_bindings",
            "pointer_null_checks", "pointer_dereferences",
            "surface_copy_allocations", "copied_f32_lanes",
            "writable_probes", "scene_lane_reads", "depth_lane_reads",
            "mix_calls")
        counters = []
        for item in modes:
            observed = item["observed"]["counters"]
            sampled = 0 if observed["mix_calls"] == 0 else 67
            counters.append([*(observed[name] for name in counter_names),
                             sampled, sampled])
        self.assertEqual(counters, parsed["counters"])

        expected_arms = {
            "exact_depth_a": "++counters.arm_dispatches[0];++counters.dispatch;counters.const_refs+=2U;execution={Task29BranchSlot::then_slot,Task29AbiKind::const_reference,&tex,&input,true,0U};break;",
            "exact_depth_b": "++counters.arm_dispatches[1];++counters.dispatch;counters.const_refs+=2U;execution={Task29BranchSlot::else_slot,Task29AbiKind::const_reference,&input,&tex,true,1U};break;",
            "exact_alias": "++counters.arm_dispatches[2];++counters.dispatch;counters.const_refs+=2U;execution={Task29BranchSlot::then_slot,Task29AbiKind::const_reference,&input,&tex,true,2U};break;",
            "owning_value_copies": "++counters.arm_dispatches[3];++counters.dispatch;counters.copies+=2U;scene_copy.emplace(tex.clone());++counters.allocations;counters.copied_lanes+=static_cast<std::uint32_t>(scene_copy->data().size());depth_copy.emplace(input.clone());++counters.allocations;counters.copied_lanes+=static_cast<std::uint32_t>(depth_copy->data().size());execution={Task29BranchSlot::then_slot,Task29AbiKind::value,&*scene_copy,&*depth_copy,true,3U};break;",
            "wrong_order_depth_a": "++counters.arm_dispatches[6];++counters.dispatch;counters.const_refs+=2U;execution={Task29BranchSlot::then_slot,Task29AbiKind::const_reference,&input,&tex,true,6U};break;",
        }
        arms = dict(parsed["arms"])
        for name, body in expected_arms.items():
            self.assertEqual(body, arms[name])
        self.assertEqual(8, len(set(body for _, body in parsed["arms"])))
        self.assertTrue(parsed["alias_setup"])
        self.assertTrue(parsed["copy_implementation"])
        self.assertTrue(parsed["invalid_guard"])
        self.assertIn("Task29AbiKind::mutable_reference", arms["mutable_references"])
        self.assertIn("++counters.write_probes", arms["mutable_references"])
        self.assertIn("Task29AbiKind::nullable_pointer", arms["nullable_nonnull"])
        self.assertIn("++counters.null_checks", arms["nullable_nonnull"])
        self.assertIn("depth_pointer=nullptr", arms["nullable_null_depth"])
        self.assertIn("execution.depth==nullptr", parsed["dispatch_suffix"])
        self.assertIn("task29_trace_selected_focus_path", parsed["dispatch_suffix"])

        excluded = {"witness.mode", "witness.name", "witness.accepted",
                    "witness.result", "witness.resource_checksum",
                    "witness.handled_id", "witness.counters.arm_dispatches"}
        signature = parsed["semantic_signature"]
        self.assertEqual(31, len(signature))
        self.assertFalse(any(any(token in field for token in excluded)
                             for field in signature))
        self.assertEqual(8,
                         oracle["direct_borrow_harness"]
                               ["semantic_signature_unique_count"])

        begin = cpp.index("// TASK29_NATIVE_ORACLE_TABLE_BEGIN")
        end = cpp.index("// TASK29_DIRECT_ABI_HARNESS_END") + len(
            "// TASK29_DIRECT_ABI_HARNESS_END")
        executable = cpp[begin:end]
        tokens = list(re.finditer(
            r'"[^"\n]*"|::|==|!=|<=|>=|&&|\|\||'
            r'\b(?:0x[0-9a-fA-F]+|[0-9]+(?:\.[0-9]+)?f?)(?:U)?\b|'
            r'\b[A-Za-z_][A-Za-z0-9_]*\b|[{}()\[\],;:+\-*/=<>]',
            executable))
        self.assertGreater(len(tokens), 1600)
        baseline = parsed
        for ordinal, token in enumerate(tokens):
            old = token.group(0)
            if old.startswith('"'):
                new = old[:-1] + 'X"'
            elif re.match(r"[A-Za-z_]", old):
                new = old + "X"
            elif re.match(r"(?:0x|[0-9])", old):
                new = "7" if old != "7" else "8"
            else:
                new = "@"
            tampered = (cpp[:begin] + executable[:token.start()] + new
                        + executable[token.end():] + cpp[end:])
            try:
                changed = _task29_parse_executable_tables(tampered)
            except (AssertionError, SyntaxError, ValueError):
                continue
            self.assertNotEqual(baseline, changed,
                                f"Task29 executable token {ordinal}: {old}")
        self.assertEqual(
            "b16c120e2331d87b61b98154d63954ad52ff328f149ebeb67b66321b73bde0a3",
            hashlib.sha256(oracle_bytes).hexdigest())


class Task30ExtrudeBvec2RelationalReductionTests(unittest.TestCase):
    @staticmethod
    def exact_program():
        import hashlib
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
            EXTRUDE_KEY)
        from tools.glslcpp.frontend.semantic import analyze_program

        source = (REPOSITORY / "tools/glslcpp/corpus/"
                  "a024dc3a960cc44af454abc7aebce50456c194e6/"
                  "sources/filter/extrude/extrude.glsl").read_text()
        return (source, hashlib.sha256(source.encode()).hexdigest(),
                analyze_program(parse_program(
                    source, EXTRUDE_KEY, {"DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0}),
                    EXTRUDE_KEY))

    def test_task30_exact_profile_authenticates_frozen_closure_and_narrow_abi_emission(self) -> None:
        import dataclasses
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
            PROFILE, apply_extrude_bvec2_relational_reduction,
            authenticate_extrude_bvec2_relational_reduction)

        _, source_hash, exact = self.exact_program()
        proof = authenticate_extrude_bvec2_relational_reduction(
            exact, source_hash, PROFILE)
        main = exact.functions[5]
        self.assertIs(main, proof.main)
        self.assertEqual(36, main.id)
        self.assertEqual((2, 2), (len(proof.reductions), len(proof.relationals)))
        self.assertEqual(("bool", "bool"),
                         tuple(item.type.display() for item in proof.reductions))
        self.assertEqual(("bvec2", "bvec2"),
                         tuple(item.type.display() for item in proof.relationals))
        self.assertEqual(("all", "all"),
                         tuple(item.callee for item in proof.reductions))
        self.assertEqual(("lessThanEqual", "lessThanEqual"),
                         tuple(item.callee for item in proof.relationals))

        def span(value):
            return (f"{value.span.start_line}:{value.span.start_column}-"
                    f"{value.span.end_line}:{value.span.end_column}")

        self.assertEqual(("159:23-159:72", "160:37-160:81"),
                         tuple(span(item) for item in proof.reductions))
        self.assertEqual(("159:27-159:71", "160:41-160:80"),
                         tuple(span(item) for item in proof.relationals))
        for reduction, relational in zip(proof.reductions, proof.relationals):
            self.assertEqual(1, len(reduction.children))
            self.assertIs(relational, reduction.children[0])
            self.assertEqual(2, len(relational.children))
        self.assertEqual(("declaration", "binary"),
                         tuple(item.kind for item in proof.reduction_parents))
        self.assertEqual((3, 3), tuple(map(len, proof.statement_parent_chains)))
        for chain in proof.statement_parent_chains:
            self.assertEqual(("for", "block", "decl"),
                             tuple(item.kind for item in chain))
        self.assertEqual(11, len(proof.consumed_objects))
        self.assertEqual(11, len({id(item) for item in proof.consumed_objects}))
        self.assertIs(exact, apply_extrude_bvec2_relational_reduction(
            exact, source_hash, PROFILE))

        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                exact, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(exact, exact.key, source_hash)
        generate_typed_slice.validate_capabilities(
            exact, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash,
            extrude_bvec2_relational_reduction_profile=PROFILE)
        emitted = render_typed_cpp(
            exact, exact.key, source_hash,
            extrude_bvec2_relational_reduction_profile=PROFILE)

        # Narrow-ABI lowering: exactly the two authenticated
        # all(lessThanEqual(...)) nests, nothing wider (no `any`, no
        # strict-relational, no named bvec2 intermediate).
        self.assertEqual(2, emitted.count("glsl::all("))
        self.assertEqual(2, emitted.count("glsl::lessThanEqual("))
        self.assertEqual(2, emitted.count("glsl::all(glsl::lessThanEqual("))
        self.assertEqual(0, emitted.count("glsl::any("))
        self.assertEqual(0, emitted.count("glsl::lessThan("))
        self.assertEqual(0, emitted.count("glsl::greaterThan("))
        self.assertEqual(0, emitted.count("glsl::greaterThanEqual("))
        self.assertEqual(0, emitted.count("glsl::BVec2"))
        self.assertIn(
            "bool topHit = glsl::all(glsl::lessThanEqual(glsl::abs("
            "(P - faceCenter)), faceHalf));", emitted)
        self.assertIn(
            "bool sideHit = ((!topHit) && glsl::all(glsl::lessThanEqual("
            "glsl::abs((P - cellC)), halfCell)));", emitted)

        # Independent reconstruction: a distinct-object, structurally equal
        # tree still authenticates on its own authority, sharing no object
        # identity with the original candidate's proof.
        def reconstruct(value):
            if dataclasses.is_dataclass(value):
                return dataclasses.replace(value, **{
                    field.name: reconstruct(getattr(value, field.name))
                    for field in dataclasses.fields(value)})
            if isinstance(value, tuple):
                return tuple(reconstruct(item) for item in value)
            return value

        rebuilt = reconstruct(exact)
        self.assertEqual(exact, rebuilt)
        self.assertIsNot(exact, rebuilt)
        rebuilt_proof = authenticate_extrude_bvec2_relational_reduction(
            rebuilt, source_hash, PROFILE)
        self.assertEqual(len(proof.consumed_objects), len(rebuilt_proof.consumed_objects))
        self.assertTrue(all(not any(old is own for old in proof.consumed_objects)
                            for own in rebuilt_proof.consumed_objects))
        generate_typed_slice.validate_capabilities(
            rebuilt, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash,
            extrude_bvec2_relational_reduction_profile=PROFILE)
        render_typed_cpp(
            rebuilt, rebuilt.key, source_hash,
            extrude_bvec2_relational_reduction_profile=PROFILE)

        # Neither authority trusts a forged/stale proof: even if the
        # authenticate function is mocked to hand back a proof built from a
        # DIFFERENT (the original, not `rebuilt`) tree, the surrounding
        # pipeline independently re-derives node identity by walking the
        # actual candidate, and rejects the mismatch.
        with mock.patch.object(
                generate_typed_slice,
                "authenticate_extrude_bvec2_relational_reduction",
                return_value=proof), self.assertRaises(
                    generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                rebuilt, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                extrude_bvec2_relational_reduction_profile=PROFILE)
        with mock.patch(
                "tools.glslcpp.emit_typed_cpp."
                "authenticate_extrude_bvec2_relational_reduction",
                return_value=proof), self.assertRaises(TypedEmissionError):
            render_typed_cpp(
                rebuilt, rebuilt.key, source_hash,
                extrude_bvec2_relational_reduction_profile=PROFILE)

    def test_task30_exhaustive_single_axis_structural_mutations_reject_at_all_three_authorities(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
            PROFILE, authenticate_extrude_bvec2_relational_reduction)
        from tools.glslcpp.frontend.semantic_types import FLOAT, vector
        from tools.glslcpp.frontend.typed_ir import PreprocessorDefine

        _, source_hash, exact = self.exact_program()

        def at(value, path):
            for part in path:
                value = value[part] if isinstance(part, int) else getattr(value, part)
            return value

        def replaced(value, path, replacement):
            if len(path) == 1:
                part = path[0]
                if isinstance(part, int):
                    items = list(value); items[part] = replacement
                    return tuple(items)
                return dataclasses.replace(value, **{part: replacement})
            part = path[0]
            child = value[part] if isinstance(part, int) else getattr(value, part)
            updated = replaced(child, path[1:], replacement)
            if isinstance(part, int):
                items = list(value); items[part] = updated
                return tuple(items)
            return dataclasses.replace(value, **{part: updated})

        main_index = 5
        main = exact.functions[main_index]
        self.assertEqual(36, main.id)
        top_all_path = ("functions", main_index, "body", 12, "children", 1,
                        "children", 8, "expressions", 0, "children", 0)
        top_rel_path = top_all_path + ("children", 0)
        side_all_path = ("functions", main_index, "body", 12, "children", 1,
                         "children", 9, "expressions", 0, "children", 0,
                         "children", 1)
        side_rel_path = side_all_path + ("children", 0)
        top_rel = at(exact, top_rel_path)

        axes = {
            "program-key": (("key",), "filter/extrude:foreign"),
            "normalized-source": (("source",), exact.source + " "),
            "raw-source": (("raw_source",), exact.raw_source + " "),
            "body-status": (("body_status",), "task30-mutated"),
            "define-name": (("preprocessor_defines",),
                            (PreprocessorDefine("TASK30", "int", "1"),
                             PreprocessorDefine("EXTRUDE_TYPE", "int", "0"))),
            "define-order": (("preprocessor_defines",),
                             tuple(reversed(exact.preprocessor_defines))),
            "struct-presence": (("structs",), (object(),)),
            "uniform-block-presence": (("uniform_blocks",), (object(),)),
            "loop-count": (("counted_loop_proof", "loop_count"), 4),
            "loop-depth": (("counted_loop_proof", "max_effective_depth"), 4),
            "loop-product": (("counted_loop_proof", "max_lexical_product"), 10),
            "loop-charge": (("counted_loop_proof", "entrypoint_charge"), 91),
            "call-graph-cycle": (("counted_loop_proof", "call_graph_acyclic"), False),
            "resource-uniform-order": (("resources", "uniforms"),
                                       tuple(reversed(exact.resources.uniforms))),
            "resource-uniform-count": (("resources", "uniforms"),
                                       exact.resources.uniforms[:-1]),
            "resource-sampler-count": (("resources", "samplers"), ()),
            "resource-output": (("resources", "outputs", 0), "otherColor"),
            "resource-texture": (("resources", "uses_texture"), False),
            "resource-derivative": (("resources", "uses_derivatives"), True),
            "function-count": (("functions",), exact.functions[:-1]),
            "function-order": (("functions",), tuple(reversed(exact.functions))),
            "main-id": (("functions", main_index, "signature", "id"), 999),
            "main-return": (("functions", main_index, "signature", "return_type"), FLOAT),
            "main-body-count": (("functions", main_index, "body"), main.body[:-1]),
            "main-span": (("functions", main_index, "span", "start_line"), 128),
            "for-kind": (("functions", main_index, "body", 12, "kind"), "block"),
            "for-span": (("functions", main_index, "body", 12, "span", "start_line"), 144),
            "block-kind": (("functions", main_index, "body", 12, "children", 1, "kind"), "decl"),
            "block-span": (("functions", main_index, "body", 12, "children", 1,
                           "span", "start_line"), 144),
            "decl8-span": (("functions", main_index, "body", 12, "children", 1,
                          "children", 8, "span", "start_line"), 144),
            "decl9-span": (("functions", main_index, "body", 12, "children", 1,
                          "children", 9, "span", "start_line"), 144),
            "decl8-kind": (("functions", main_index, "body", 12, "children", 1,
                          "children", 8, "kind"), "block"),
            "top-all-span": (top_all_path + ("span", "start_column"), 24),
            "top-all-callee": (top_all_path + ("callee",), "any"),
            "top-all-type": (top_all_path + ("type",), FLOAT),
            "top-all-children-order": (top_all_path + ("children",), (top_rel, top_rel)),
            "top-rel-span": (top_rel_path + ("span", "start_column"), 28),
            "top-rel-type": (top_rel_path + ("type",), vector("bool", 3)),
            "top-rel-callee": (top_rel_path + ("callee",), "lessThan"),
            "top-rel-children-order": (top_rel_path + ("children",),
                                       tuple(reversed(top_rel.children))),
            "top-rel-children-count": (top_rel_path + ("children",), top_rel.children[:1]),
            "side-all-span": (side_all_path + ("span", "start_column"), 38),
            "side-all-callee": (side_all_path + ("callee",), "any"),
            "side-all-type": (side_all_path + ("type",), FLOAT),
            "side-rel-span": (side_rel_path + ("span", "start_column"), 42),
            "side-rel-type": (side_rel_path + ("type",), vector("bool", 3)),
            "side-rel-callee": (side_rel_path + ("callee",), "lessThan"),
        }
        candidates = {name: replaced(exact, path, value)
                      for name, (path, value) in axes.items()}
        self.assertEqual(len(axes), len(candidates))
        self.assertEqual(47, len(candidates))
        self.assertEqual(
            "2919cf0225ab23a5e10247e9625c74fb40fb158a8ab910aad577b17bbfd35a0d",
            hashlib.sha256(("\n".join(sorted(candidates)) + "\n").encode()).hexdigest())

        for name, candidate in candidates.items():
            # Each candidate must assert its own structural precondition —
            # that it genuinely changed the program — before rejection is
            # meaningful; a no-op mutation would prove nothing.
            self.assertNotEqual(exact, candidate, name)
            with self.subTest(axis=name, layer="profile"), self.assertRaises(ValueError):
                authenticate_extrude_bvec2_relational_reduction(
                    candidate, source_hash, PROFILE)
            with self.subTest(axis=name, layer="validator"), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash,
                    extrude_bvec2_relational_reduction_profile=PROFILE)
            with self.subTest(axis=name, layer="emitter"), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    candidate, candidate.key, source_hash,
                    extrude_bvec2_relational_reduction_profile=PROFILE)

    def test_task30_validator_and_emitter_authenticate_independently_without_trusting_each_other(self) -> None:
        import dataclasses
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
            EXTRUDE_KEY, PROFILE)

        _, source_hash, exact = self.exact_program()
        foreign = dataclasses.replace(exact, key="filter/extrude:foreignvariant")

        # The emitter fails closed on its own authority: no profile, a wrong
        # profile string, and a foreign (differently-keyed) program carrying
        # the identical closure — none of these ever invoke the validator.
        with self.assertRaisesRegex(TypedEmissionError, r"exact .* carrier required"):
            render_typed_cpp(exact, exact.key, source_hash)
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(
                exact, exact.key, source_hash,
                extrude_bvec2_relational_reduction_profile="wrong")
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(
                foreign, foreign.key, source_hash,
                extrude_bvec2_relational_reduction_profile=PROFILE)
        # The deepest-reachable rejection on the foreign program, with no
        # carrier at all, is exactly the live-verified builtin-level message —
        # the emitter walks into the closure and rejects the first offending
        # node, never having consulted the validator.
        with self.assertRaisesRegex(
                TypedEmissionError,
                r"filter/extrude:foreignvariant:159:27: unsupported builtin lessThanEqual"):
            render_typed_cpp(foreign, foreign.key, source_hash)

        # The validator fails closed on its own authority, symmetrically,
        # without ever invoking the emitter.
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError, r"exact .* carrier required"):
            generate_typed_slice.validate_capabilities(
                exact, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                exact, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                extrude_bvec2_relational_reduction_profile="wrong")
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash,
                extrude_bvec2_relational_reduction_profile=PROFILE)
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                r"filter/extrude:foreignvariant:159:23: unsupported builtin all"):
            generate_typed_slice.validate_capabilities(
                foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)

        # Widening the validator's generic type vocabulary alone does not
        # rescue an unauthenticated candidate: bvec2/all/lessThanEqual
        # admission is identity-scoped to the four authenticated nodes, not a
        # table a wider program could opt into. Snapshot and restore under
        # try/finally so no other test observes the widened state.
        snapshot = tuple(generate_typed_slice.APPROVED_TYPES)
        try:
            with mock.patch.object(
                    generate_typed_slice, "APPROVED_TYPES",
                    (*generate_typed_slice.APPROVED_TYPES, "bvec2")):
                with self.assertRaises(generate_typed_slice.GeneratorError):
                    generate_typed_slice.validate_capabilities(
                        foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                        source_hash=source_hash)
        finally:
            self.assertEqual(snapshot, generate_typed_slice.APPROVED_TYPES)

    def test_task30_capability_and_type_vocabulary_are_identity_scoped_not_widened(self) -> None:
        from tools.glslcpp import emit_typed_cpp, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import render_typed_cpp
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import PROFILE

        # bvec2 is never a globally-approved type, and all/lessThanEqual are
        # never globally-approved builtins or capability names — exactly like
        # `round` before it (Task 24).
        self.assertNotIn("bvec2", generate_typed_slice.APPROVED_TYPES)
        self.assertNotIn("all", generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertNotIn("lessThanEqual", generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertNotIn("all", emit_typed_cpp._BUILTIN_NAMES)
        self.assertNotIn("lessThanEqual", emit_typed_cpp._BUILTIN_NAMES)
        self.assertNotIn("bvec2", emit_typed_cpp._TYPES)

        # The capability vocabulary is still exactly the 44 entries frozen
        # before this task; the two-node relational/reduction closure never
        # widened it.
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        spec = generate_typed_slice.load_slice(REPOSITORY)
        self.assertEqual(44, len(spec["capabilities"]))
        self.assertEqual(tuple(spec["capabilities"]),
                         generate_typed_slice.APPROVED_CAPABILITIES)

        # Behavioral proof, not just a static list check: validate_capabilities
        # raises "missing capabilities" if ANYTHING reaches its internal
        # bookkeeping (`used`) that is absent from the declared 44-entry
        # vocabulary — see generate_typed_slice.py's `missing = used -
        # set(capabilities)` gate. `all`/`lessThanEqual` are deliberately
        # skipped from `used.add`, exactly like `round`
        # (`if value.callee not in {"round", "all", "lessThanEqual"}:
        # used.add(value.callee)`). Since this call succeeds against the
        # UNMODIFIED 44-entry tuple that itself excludes `all`/`lessThanEqual`,
        # it is direct evidence that neither builtin ever entered `used` —
        # had they, this call would have raised "missing capabilities all,
        # lessThanEqual".
        _, source_hash, exact = self.exact_program()
        generate_typed_slice.validate_capabilities(
            exact, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash,
            extrude_bvec2_relational_reduction_profile=PROFILE)
        render_typed_cpp(
            exact, exact.key, source_hash,
            extrude_bvec2_relational_reduction_profile=PROFILE)

    def test_task30_history_coexistence_and_live_schema_matches_130_program_state(self) -> None:
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
            EXTRUDE_KEY, PROFILE)

        spec = generate_typed_slice.load_slice(REPOSITORY)
        typed = tuple(item["program_key"] for item in spec["programs"])
        public = tuple(sorted((*typed, "filter/invert:inv", "synth/solid:solid")))
        corpus = json.loads((check_corpus._corpus_root(REPOSITORY) /
                             "manifest.json").read_text())
        unported = tuple(sorted(
            {item["program_key"] for item in corpus["programs"]} - set(public)))
        self.assertEqual((137, 139, 73, 212),
                         (len(typed), len(public), len(unported),
                          len(corpus["programs"])))
        self.assertEqual(
            "dfb7c7c43d7fd118c4a1b9a266d6957a90b189ec63ac6b0d49538bd853a360d7",
            hashlib.sha256(("\n".join(typed) + "\n").encode()).hexdigest())
        self.assertEqual(
            "a873c537d3d8ffb872859389812ae7c1e68954c9fcd381334eca4998195f319f",
            hashlib.sha256(("\n".join(public) + "\n").encode()).hexdigest())
        self.assertEqual(25, typed.index(EXTRUDE_KEY))
        self.assertEqual(("filter/directionalBlur:directionalBlur", EXTRUDE_KEY,
                          "filter/fibers:fibersBlend"), typed[24:27])
        self.assertEqual([{
            "defines": {"DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0},
            "extrude_bvec2_relational_reduction_profile": PROFILE,
            "program_key": EXTRUDE_KEY,
        }], [item for item in spec["programs"]
             if "extrude_bvec2_relational_reduction_profile" in item])

        current_outputs = generate_typed_slice.generate_outputs(REPOSITORY)
        manifest = json.loads(
            current_outputs["src/typed_generated/typed_manifest.json"])
        extrude_row = next(item for item in manifest["programs"]
                           if item["program_key"] == EXTRUDE_KEY)
        self.assertEqual(PROFILE,
                         extrude_row["extrude_bvec2_relational_reduction_profile"])
        self.assertEqual({"DEPTH_SOURCE": 0, "EXTRUDE_TYPE": 0},
                         extrude_row["defines"])
        # The live ordinal (25) is baked into the generated namespace name.
        current_cpp = current_outputs["src/typed_generated/typed_slice.cpp"].decode()
        extrude_start = current_cpp.index(f"// Typed IR program: {EXTRUDE_KEY}")
        extrude_end = current_cpp.index("// Typed IR program:", extrude_start + 1)
        self.assertIn("namespace typed_25 {",
                     current_cpp[extrude_start:extrude_end])

        # Coexistence: this identity profile carries no relationship to any
        # earlier task's profile/capability, so declaring both at once is a
        # metadata-mismatch at every prior task's carrier — proving a fresh
        # APPROVED_CAPABILITIES/APPROVED_TYPES tuple import-cycle collision
        # never occurs.
        _, source_hash, exact = self.exact_program()
        coexistence = {
            "compatibility_transform": generate_typed_slice.CRT_COMPATIBILITY_TRANSFORM,
            "custom_comparer_profile": generate_typed_slice.LENS_CUSTOM_COMPARER_PROFILE,
            "source_global_literal_int_profile":
                generate_typed_slice.SOURCE_GLOBAL_LITERAL_INT_CAPABILITY,
            "gather_sorted_round_profile": generate_typed_slice.GATHER_SORTED_ROUND_PROFILE,
            "literal_vec3_lane_index_profile":
                generate_typed_slice.LITERAL_VEC3_LANE_INDEX_PROFILE,
            "smooth_edge_luma_weights_profile":
                generate_typed_slice.SMOOTH_EDGE_LUMA_WEIGHTS_PROFILE,
            "perlin_scalar_uint_xor_profile":
                generate_typed_slice.PERLIN_SCALAR_UINT_XOR_PROFILE,
            "rotate_mat2_return_profile": generate_typed_slice.ROTATE_MAT2_RETURN_PROFILE,
            "focus_blur_borrowed_sampler_profile":
                generate_typed_slice.FOCUS_BLUR_BORROWED_SAMPLER_PROFILE,
        }
        self.assertEqual(9, len(coexistence))
        for name, value in coexistence.items():
            kwargs = {name: value,
                     "extrude_bvec2_relational_reduction_profile": PROFILE}
            with self.subTest(layer="validator", coexistence=name), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    exact, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash, **kwargs)
            with self.subTest(layer="emitter", coexistence=name), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(exact, exact.key, source_hash, **kwargs)

        # Module import + a fresh APPROVED_CAPABILITIES/APPROVED_TYPES tuple
        # check: importing the profile module standalone must not mutate
        # either module-level tuple, and both must still equal the frozen
        # 44/16-entry vocabularies after import.
        from tools.glslcpp.frontend import extrude_bvec2_relational_reduction_profile as profile_module
        self.assertEqual(PROFILE, profile_module.PROFILE)
        self.assertEqual(EXTRUDE_KEY, profile_module.EXTRUDE_KEY)
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        self.assertEqual(16, len(generate_typed_slice.APPROVED_TYPES))

    def test_task30_removing_only_extrude_regenerates_task29_outputs_byte_for_byte(self) -> None:
        import copy
        import hashlib
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.curl_vector_math_profile import CURL_KEY
        from tools.glslcpp.frontend.extrude_bvec2_relational_reduction_profile import (
            EXTRUDE_KEY)

        spec = generate_typed_slice.load_slice(REPOSITORY)
        task29_spec = copy.deepcopy(spec)
        task29_spec["programs"] = [item for item in task29_spec["programs"]
                                   if item["program_key"] not in (
                                       EXTRUDE_KEY, CURL_KEY,
                                       "filter/grade:creative",
                                       "filter/grade:hslSecondary",
                                       "filter/grade:lut",
                                       "filter/grade:primary",
                                       "filter/grade:vignette",
                                       "filter/grade:wheels")]
        task29_keys = tuple(item["program_key"] for item in task29_spec["programs"])
        self.assertEqual(129, len(task29_keys))
        self.assertEqual(
            "c2561c5937ba5f11f5d2e86d729ff90b617aff738cb4de53dbf3cd8b76dbbff9",
            hashlib.sha256(("\n".join(task29_keys) + "\n").encode()).hexdigest())

        # load_slice hard-pins the live 130-program count/hash, so the Task29
        # reconstruction must go through the mocked loader, exactly as the
        # Task29 test reconstructs Task28.
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=task29_spec):
            task29 = generate_typed_slice.generate_outputs(REPOSITORY)
        task29["include/noisemaker/generated/catalog.hpp"] = (
            generate_typed_slice.render_catalog_header(task29_spec))
        expected_task29 = {
            "src/typed_generated/typed_slice.cpp":
                "358847db37675afd7f173341c66f71527af04c8ac817efddcc7d4b7cf31551aa",
            "src/typed_generated/typed_manifest.json":
                "01bfe3c139e8352ad04ac87ed5817715166dff371e983361f8cbb7fefe650351",
            "include/noisemaker/generated/catalog.hpp":
                "2d32511c858a5caeedb7c4fe1b2d985191e639a9e4ed1d98ca9219a60b668304",
        }
        for path, expected in expected_task29.items():
            self.assertEqual(expected, hashlib.sha256(task29[path]).hexdigest(), path)

        marker = re.compile(r"(?m)^// Typed IR program: ([^\n]+)\n")
        def blocks(payload):
            source = payload.decode()
            starts = list(marker.finditer(source))
            catalog = source.index(
                "\nnamespace {\nconstexpr std::array<KernelFactory")
            return {match.group(1): source[
                match.start():(starts[index + 1].start()
                               if index + 1 < len(starts) else catalog)]
                for index, match in enumerate(starts)}

        task29_blocks = blocks(task29["src/typed_generated/typed_slice.cpp"])
        self.assertEqual(129, len(task29_blocks))
        self.assertNotIn(EXTRUDE_KEY, task29_blocks)

    def test_task30_native_executable_tables_are_exact_frozen_transcription_and_tamper_sensitive(self) -> None:
        import hashlib

        oracle_path = REPOSITORY / "tests/oracles/task-30-oracles.json"
        self.assertTrue(oracle_path.is_file(), "Task 30 frozen oracle JSON is required")
        oracle_bytes = oracle_path.read_bytes()
        self.assertEqual(
            "bf8c4c165846eb116d2afb4f78b7c1de78f70f104ac714e09395ceffbe51c758",
            hashlib.sha256(oracle_bytes).hexdigest())
        oracle = json.loads(oracle_bytes)

        kernels_path = REPOSITORY / "tests/test_generated_kernels.cpp"
        cpp = kernels_path.read_text()
        for marker in ("// TASK30_NATIVE_ORACLE_TABLE_BEGIN",
                       "// TASK30_NATIVE_ORACLE_TABLE_END",
                       "// TASK30_DIRECT_ABI_HARNESS_BEGIN",
                       "// TASK30_DIRECT_ABI_SWITCH_BEGIN",
                       "// TASK30_DIRECT_ABI_SWITCH_END",
                       "// TASK30_DIRECT_ABI_HARNESS_END"):
            self.assertIn(marker, cpp,
                         "native Task30 fixtures/tables are pending in "
                         "tests/test_generated_kernels.cpp")
        parsed = _task30_parse_executable_tables(cpp)

        # Only the 3 direct define-map {EXTRUDE_TYPE:0, DEPTH_SOURCE:0} cases
        # are authorized for the native port (see the brief and the comment
        # immediately preceding kTask30NativeCases); the other 3 oracle cases
        # use a different define map and are excluded here on purpose.
        authorized_cases = [item for item in oracle["cases"]
                            if item["defines"] == {"EXTRUDE_TYPE": 0, "DEPTH_SOURCE": 0}]
        self.assertEqual(3, len(authorized_cases))
        self.assertEqual(6, len(oracle["cases"]))
        expected_cases = []
        for item in authorized_cases:
            output = item["output"]
            probes = []
            for probe in output["probes"][:5]:
                probes.extend(probe["at_top_down_xy"])
                probes.extend(int(bits, 16) for bits in probe["f32_bits_le"])
            expected_cases.append([
                item["name"], item["dimensions"]["width"], item["dimensions"]["height"],
                item["phase"], float(item["uniforms"]["size"]),
                float(item["uniforms"]["depth"]), item["uniforms"]["solidFront"],
                item["input"]["f32_sha256"], output["f32_sha256"], output["rgba8_sha256"],
                probes, output["finite_lanes"], output["nonfinite_lanes"],
            ])
        self.assertEqual(expected_cases, parsed["cases"])

        # The 7 direct_relational_cases rows, transcribed verbatim.
        direct = oracle["direct_relational_cases"]
        self.assertEqual(7, len(direct))
        expected_rows = [[
            [int(bits, 16) for bits in item["left_bits"]],
            [int(bits, 16) for bits in item["right_bits"]],
            item["less_than_equal_lanes"], item["all_result"], item["any_result"],
            item["strict_less_lanes"],
        ] for item in direct]
        self.assertEqual(expected_rows, parsed["relational_rows"])

        # Independently recomputed public-factory mutation divergence counts
        # (out of the oracle's full 6 cases per mutation, across both
        # authorized and sensitivity-only define maps), cross-checked against
        # the brief's claimed 3/6, 2/6, 4/6, 2/6.
        mutations = {item["id"]: item for item in oracle["public_factory_mutations"]}
        self.assertEqual(
            {"top-lane-any", "side-lane-any", "top-strict-less",
             "side-strict-less"},
            set(mutations))
        divergence = {mutation_id: sum(
            1 for row in item["case_results"] if not row["same_f32_bytes"])
            for mutation_id, item in mutations.items()}
        self.assertEqual({
            "top-lane-any": 3, "side-lane-any": 2,
            "top-strict-less": 4, "side-strict-less": 2,
        }, divergence)

        # Mode enum / dispatch table: five structurally distinct native modes
        # (never a disguised shared code path, unlike 3 of Task 26's 11).
        enum_names = ["exact_inclusive_all", "inclusive_any", "strict_exclusive_all",
                     "strict_exclusive_any", "mirrored_inclusive_all"]
        self.assertEqual([[name, ordinal] for ordinal, name in enumerate(enum_names)],
                         parsed["mode_enum"])
        self.assertEqual(enum_names, parsed["dispatch"])
        self.assertEqual([
            "exact-inclusive-le-all-reduction", "inclusive-le-any-reduction",
            "strict-exclusive-lt-all-reduction", "strict-exclusive-lt-any-reduction",
            "mirrored-inclusive-ge-all-reduction"], parsed["names"])
        self.assertEqual(5, len(parsed["arms"]))
        self.assertEqual(5, len(set(body for _, body in parsed["arms"])))
        arms = dict(parsed["arms"])
        self.assertIn("noisemaker::glsl::lessThanEqual<2>", arms["exact_inclusive_all"])
        self.assertIn("noisemaker::glsl::all<2>", arms["exact_inclusive_all"])
        self.assertNotIn("noisemaker::glsl::all<2>", arms["inclusive_any"])
        self.assertIn("any=any||le[lane]", arms["inclusive_any"])
        self.assertIn("lx<rx", arms["strict_exclusive_all"])
        self.assertIn("all_true=all_true&&lane[l]", arms["strict_exclusive_all"])
        self.assertIn("lx<rx", arms["strict_exclusive_any"])
        self.assertIn("any=any||lane[l]", arms["strict_exclusive_any"])
        self.assertIn("rx<=lx", arms["mirrored_inclusive_all"])
        # The mirrored arm's body text carries an explanatory comment that
        # mentions lessThanEqual by name; what matters structurally is that
        # it never actually CALLS the builtin (the comment is stripped before
        # the negative check so a prose mention can't hide a real call).
        mirrored_without_comments = re.sub(
            r"//[^\n]*", "", cpp[cpp.index(
                "case Task30RelationalMode::mirrored_inclusive_all"):])
        mirrored_arm_source = mirrored_without_comments[
            :mirrored_without_comments.index("break;") + len("break;")]
        self.assertNotIn("lessThanEqual", re.sub(r"\s+", "", mirrored_arm_source))
        self.assertIn("invalidTask30relationalmode", parsed["guard"])
        self.assertEqual(10, len(parsed["signature_fields"]))

        # Token-level tamper sensitivity over the whole authenticated region:
        # every single-token mutation that still parses must change the
        # parsed structure. Catches source tampering, not just JSON tampering.
        begin = cpp.index("// TASK30_NATIVE_ORACLE_TABLE_BEGIN")
        end = cpp.index("// TASK30_DIRECT_ABI_HARNESS_END") + len(
            "// TASK30_DIRECT_ABI_HARNESS_END")
        region = cpp[begin:end]
        tokens = list(re.finditer(
            r'"[^"\n]*"|::|==|!=|<=|>=|&&|\|\||'
            r'\b(?:0x[0-9a-fA-F]+|[0-9]+(?:\.[0-9]+)?f?)(?:U)?\b|'
            r'\b[A-Za-z_][A-Za-z0-9_]*\b|[{}()\[\],;:+\-*/=<>]',
            region))
        self.assertGreater(len(tokens), 3000)
        baseline = parsed
        for ordinal, token in enumerate(tokens):
            old = token.group(0)
            if old.startswith('"'):
                new = old[:-1] + 'X"'
            elif re.match(r"[A-Za-z_]", old):
                new = old + "X"
            elif re.match(r"(?:0x|[0-9])", old):
                new = "7" if old != "7" else "8"
            else:
                new = "@"
            tampered_region = region[:token.start()] + new + region[token.end():]
            tampered = cpp[:begin] + tampered_region + cpp[end:]
            try:
                changed = _task30_parse_executable_tables(tampered)
            except (AssertionError, SyntaxError, ValueError):
                continue
            self.assertNotEqual(baseline, changed,
                                f"Task30 executable token {ordinal}: {old}")
        self.assertEqual(
            "bf8c4c165846eb116d2afb4f78b7c1de78f70f104ac714e09395ceffbe51c758",
            hashlib.sha256(oracle_bytes).hexdigest())

    def test_task30_node_level_closure_logic_rejects_past_the_coarse_hash_gate(self) -> None:
        """The profile's node-walk/pairing/typing logic must itself reject.

        The sibling single-axis mutation test proves the profile is closed, but
        every one of its axes is absorbed by the coarse
        "source, define, function, whole-program, or interface mismatch" gate,
        because any tree edit perturbs the whole-program hash. That leaves the
        module's *novel* logic — closure-site census, reduction/relational
        pairing, arity and result typing — unexercised.

        Here the coarse gate is deliberately re-frozen to match each mutated
        tree, so the node-level checks actually run. Each mutation must then be
        rejected by a SPECIFIC node-level message, never by the coarse one.
        """
        import hashlib
        from unittest import mock
        from tools.glslcpp.frontend import (
            extrude_bvec2_relational_reduction_profile as profile)

        COARSE = ("source, define, function, whole-program, "
                  "or interface mismatch")

        def walk_expression(value):
            yield value
            for child in value.children:
                yield from walk_expression(child)

        def walk_statement(statement):
            yield statement
            for child in statement.children:
                yield from walk_statement(child)

        def sites(program, callee):
            main = next(f for f in program.functions if f.id == 36)
            return [node
                    for statement in main.body
                    for owner in walk_statement(statement)
                    for expression in owner.expressions
                    for node in walk_expression(expression)
                    if node.kind == "builtin" and node.callee == callee]

        def retarget_reduction(program):
            object.__setattr__(sites(program, "all")[1], "callee", "any")

        def retarget_relational(program):
            object.__setattr__(
                sites(program, "lessThanEqual")[0], "callee", "lessThan")

        def orphan_reduction(program):
            object.__setattr__(sites(program, "all")[0], "children", ())

        def cross_paired_reduction(program):
            first, second = sites(program, "all")
            object.__setattr__(first, "children", (second.children[0],))

        def widened_relational_arity(program):
            node = sites(program, "lessThanEqual")[0]
            object.__setattr__(
                node, "children", (*node.children, node.children[0]))

        def retyped_relational(program):
            node = sites(program, "lessThanEqual")[0]
            object.__setattr__(node, "type", sites(program, "all")[0].type)

        cases = (
            ("reduction all -> any", retarget_reduction,
             "closure site cardinality mismatch"),
            ("relational lessThanEqual -> lessThan", retarget_relational,
             "closure site cardinality mismatch"),
            ("reduction loses its only child", orphan_reduction,
             "closure site cardinality mismatch"),
            ("reduction consumes the other relational", cross_paired_reduction,
             "closure node identity mismatch"),
            ("relational gains a third argument", widened_relational_arity,
             "closure node identity mismatch"),
            ("relational result retyped to bool", retyped_relational,
             "closure node identity mismatch"),
        )

        _, source_hash, baseline = self.exact_program()
        baseline_functions = profile._sha(baseline.functions)

        for label, mutate, expected in cases:
            with self.subTest(node_axis=label):
                _, _, candidate = self.exact_program()
                mutate(candidate)
                # The mutation must genuinely change the tree, or the case is
                # vacuous regardless of what the profile then reports.
                self.assertNotEqual(baseline_functions,
                                    profile._sha(candidate.functions), label)

                normalized = candidate.source.encode("utf-8")
                proof = candidate.counted_loop_proof
                with mock.patch.multiple(
                        profile,
                        _FUNCTIONS_SHA256=profile._sha(candidate.functions),
                        _WHOLE_SHA256=profile._whole(candidate),
                        _INTERFACE_SHA256=profile._interface(candidate),
                        _NORMALIZED_SHA256=hashlib.sha256(normalized).hexdigest(),
                        _NORMALIZED_BYTES=len(normalized),
                        _LOOP_PROOF=(proof.loop_count, proof.unproved_loop_count,
                                     proof.max_effective_depth,
                                     proof.max_lexical_product,
                                     proof.entrypoint_charge,
                                     proof.call_graph_acyclic)):
                    with self.assertRaises(ValueError) as raised:
                        profile.authenticate_extrude_bvec2_relational_reduction(
                            candidate, source_hash, profile.PROFILE)
                message = str(raised.exception)
                self.assertNotIn(COARSE, message,
                                 f"{label} was absorbed by the coarse gate")
                self.assertIn(expected, message, label)

        # The patched constants must be restored, or later tests inherit a
        # profile that authenticates the wrong program.
        _, source_hash, exact = self.exact_program()
        profile.authenticate_extrude_bvec2_relational_reduction(
            exact, source_hash, profile.PROFILE)


class Task31CurlVectorMathTests(unittest.TestCase):
    @staticmethod
    def exact_program():
        import hashlib
        from tools.glslcpp.frontend import parse_program
        from tools.glslcpp.frontend.curl_vector_math_profile import CURL_KEY
        from tools.glslcpp.frontend.semantic import analyze_program

        source = (REPOSITORY / "tools/glslcpp/corpus/"
                  "a024dc3a960cc44af454abc7aebce50456c194e6/"
                  "sources/synth/curl/curl.glsl").read_text()
        return (source, hashlib.sha256(source.encode()).hexdigest(),
                analyze_program(parse_program(
                    source, CURL_KEY, {"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True}),
                    CURL_KEY))

    def test_task31_exact_profile_authenticates_frozen_closure_and_narrow_abi_emission(self) -> None:
        import dataclasses
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.curl_vector_math_profile import (
            PROFILE, apply_curl_vector_math, authenticate_curl_vector_math)

        _, source_hash, exact = self.exact_program()
        proof = authenticate_curl_vector_math(exact, source_hash, PROFILE)

        # Exactly the frozen four-node closure: one tanh(vec3) in main, three
        # vec3/vec4-by-scalar mod calls across permute's two overloads and
        # simplex3D. Ordered by owning function id, per the profile's own
        # census order.
        self.assertEqual(4, len(proof.nodes))
        self.assertEqual(("tanh", "mod", "mod", "mod"),
                         tuple(item.callee for item in proof.nodes))
        self.assertEqual(("vec3", "vec3", "vec4", "vec3"),
                         tuple(item.type.display() for item in proof.nodes))
        self.assertEqual((18, 19, 20, 21), tuple(item.id for item in proof.owners))
        self.assertEqual(("main", "permute", "permute", "simplex3D"),
                         tuple(item.name for item in proof.owners))

        def span(value):
            return (f"{value.span.start_line}:{value.span.start_column}-"
                    f"{value.span.end_line}:{value.span.end_column}")

        self.assertEqual(
            ("196:12-196:34", "32:12-32:47", "35:12-35:47", "65:9-65:22"),
            tuple(span(item) for item in proof.nodes))
        self.assertEqual((1, 3), (1, len(proof.mod_sites)))
        self.assertEqual(4, len(proof.statement_parent_chains))
        for chain in proof.statement_parent_chains:
            self.assertEqual(1, len(chain))
        self.assertEqual(
            ("expr", "return", "return", "expr"),
            tuple(chain[0].kind for chain in proof.statement_parent_chains))
        self.assertEqual(12, len(proof.consumed_objects))
        self.assertEqual(12, len({id(item) for item in proof.consumed_objects}))
        self.assertIs(exact, apply_curl_vector_math(exact, source_hash, PROFILE))

        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                exact, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(exact, exact.key, source_hash)
        generate_typed_slice.validate_capabilities(
            exact, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash, curl_vector_math_profile=PROFILE)
        emitted = render_typed_cpp(
            exact, exact.key, source_hash, curl_vector_math_profile=PROFILE)

        # Narrow-ABI lowering: the one authenticated tanh site lowers to the
        # lane-wise, non-narrowing overload -- never plain glsl::tanh (which
        # would narrow the argument and cost bit-exact parity with the JS
        # transpiler's scalarised emission) -- and the three mod sites lower
        # to plain glsl::mod, nothing wider.
        self.assertEqual(1, emitted.count("glsl::tanh_lanewise("))
        self.assertEqual(0, emitted.count("glsl::tanh("))
        self.assertEqual(3, emitted.count("glsl::mod("))

        # Independent reconstruction: a distinct-object, structurally equal
        # tree still authenticates on its own authority, sharing no object
        # identity with the original candidate's proof.
        def reconstruct(value):
            if dataclasses.is_dataclass(value):
                return dataclasses.replace(value, **{
                    field.name: reconstruct(getattr(value, field.name))
                    for field in dataclasses.fields(value)})
            if isinstance(value, tuple):
                return tuple(reconstruct(item) for item in value)
            return value

        rebuilt = reconstruct(exact)
        self.assertEqual(exact, rebuilt)
        self.assertIsNot(exact, rebuilt)
        rebuilt_proof = authenticate_curl_vector_math(rebuilt, source_hash, PROFILE)
        self.assertEqual(len(proof.consumed_objects), len(rebuilt_proof.consumed_objects))
        self.assertTrue(all(not any(old is own for old in proof.consumed_objects)
                            for own in rebuilt_proof.consumed_objects))
        generate_typed_slice.validate_capabilities(
            rebuilt, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash, curl_vector_math_profile=PROFILE)
        render_typed_cpp(
            rebuilt, rebuilt.key, source_hash, curl_vector_math_profile=PROFILE)

        # Neither authority trusts a forged/stale proof: even if the
        # authenticate function is mocked to hand back a proof built from a
        # DIFFERENT (the original, not `rebuilt`) tree, the surrounding
        # pipeline independently re-derives node identity by walking the
        # actual candidate, and rejects the mismatch.
        with mock.patch.object(
                generate_typed_slice, "authenticate_curl_vector_math",
                return_value=proof), self.assertRaises(
                    generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                rebuilt, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash, curl_vector_math_profile=PROFILE)
        with mock.patch(
                "tools.glslcpp.emit_typed_cpp.authenticate_curl_vector_math",
                return_value=proof), self.assertRaises(TypedEmissionError):
            render_typed_cpp(
                rebuilt, rebuilt.key, source_hash, curl_vector_math_profile=PROFILE)

    def test_task31_exhaustive_single_axis_structural_mutations_reject_at_all_three_authorities(self) -> None:
        import dataclasses
        import hashlib
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.curl_vector_math_profile import (
            PROFILE, authenticate_curl_vector_math)
        from tools.glslcpp.frontend.semantic_types import vector
        from tools.glslcpp.frontend.typed_ir import PreprocessorDefine

        _, source_hash, exact = self.exact_program()

        def at(value, path):
            for part in path:
                value = value[part] if isinstance(part, int) else getattr(value, part)
            return value

        def replaced(value, path, replacement):
            if len(path) == 1:
                part = path[0]
                if isinstance(part, int):
                    items = list(value); items[part] = replacement
                    return tuple(items)
                return dataclasses.replace(value, **{part: replacement})
            part = path[0]
            child = value[part] if isinstance(part, int) else getattr(value, part)
            updated = replaced(child, path[1:], replacement)
            if isinstance(part, int):
                items = list(value); items[part] = updated
                return tuple(items)
            return dataclasses.replace(value, **{part: updated})

        # Paths to the four authenticated sites, verified against the live
        # parsed/analyzed tree (function index within `exact.functions`, then
        # statement/expression/child indices down to the node itself): tanh
        # in main (functions[2]), the dead mod in permute's vec3 overload
        # (functions[3]), the reachable mod in permute's vec4 overload
        # (functions[4]), and the mod in simplex3D (functions[5]).
        tanh_path = ("functions", 2, "body", 6, "expressions", 0,
                    "children", 1, "children", 0, "children", 0)
        mod_dead_path = ("functions", 3, "body", 0, "expressions", 0)
        mod_v4_path = ("functions", 4, "body", 0, "expressions", 0)
        mod_simplex_path = ("functions", 5, "body", 12, "expressions", 0, "children", 1)
        mod_dead_node = at(exact, mod_dead_path)
        mod_v4_node = at(exact, mod_v4_path)
        mod_simplex_node = at(exact, mod_simplex_path)
        self.assertEqual(("tanh", "mod", "mod", "mod"),
                         (at(exact, tanh_path).callee, mod_dead_node.callee,
                          mod_v4_node.callee, mod_simplex_node.callee))

        axes = {
            "program-key": (("key",), "synth/curl:foreign"),
            "normalized-source": (("source",), exact.source + " "),
            "raw-source": (("raw_source",), exact.raw_source + " "),
            "body-status": (("body_status",), "task31-mutated"),
            "define-name": (("preprocessor_defines",),
                            (PreprocessorDefine("TASK31", "int", "1"),
                             PreprocessorDefine("OUTPUT_MODE", "int", "3"),
                             PreprocessorDefine("RIDGES", "bool", "true"))),
            "define-order": (("preprocessor_defines",),
                             tuple(reversed(exact.preprocessor_defines))),
            "struct-presence": (("structs",), (object(),)),
            "uniform-block-presence": (("uniform_blocks",), (object(),)),
            "loop-count": (("counted_loop_proof", "loop_count"), 2),
            "loop-unproved-count": (("counted_loop_proof", "unproved_loop_count"), 1),
            "loop-depth": (("counted_loop_proof", "max_effective_depth"), 2),
            "loop-product": (("counted_loop_proof", "max_lexical_product"), 4),
            "loop-charge": (("counted_loop_proof", "entrypoint_charge"), 13),
            "call-graph-cycle": (("counted_loop_proof", "call_graph_acyclic"), False),
            "resource-uniform-order": (("resources", "uniforms"),
                                       tuple(reversed(exact.resources.uniforms))),
            "resource-uniform-count": (("resources", "uniforms"),
                                       exact.resources.uniforms[:-1]),
            "resource-sampler-count": (("resources", "samplers"), (object(),)),
            "resource-output": (("resources", "outputs", 0), "otherColor"),
            "resource-texture": (("resources", "uses_texture"), True),
            "resource-derivative": (("resources", "uses_derivatives"), True),
            "function-count": (("functions",), exact.functions[:-1]),
            "function-order": (("functions",), tuple(reversed(exact.functions))),
            "tanh-span": (tanh_path + ("span", "start_column"), 99),
            "tanh-callee": (tanh_path + ("callee",), "sin"),
            "tanh-type": (tanh_path + ("type",), vector("float", 4)),
            "tanh-children-count": (tanh_path + ("children",), ()),
            "mod-dead-span": (mod_dead_path + ("span", "start_column"), 99),
            "mod-dead-callee": (mod_dead_path + ("callee",), "min"),
            "mod-dead-type": (mod_dead_path + ("type",), vector("float", 4)),
            "mod-dead-children-order": (mod_dead_path + ("children",),
                                        tuple(reversed(mod_dead_node.children))),
            "mod-dead-children-count": (mod_dead_path + ("children",),
                                        mod_dead_node.children[:1]),
            "mod-v4-span": (mod_v4_path + ("span", "start_column"), 99),
            "mod-v4-callee": (mod_v4_path + ("callee",), "max"),
            "mod-v4-type": (mod_v4_path + ("type",), vector("float", 3)),
            "mod-v4-children-order": (mod_v4_path + ("children",),
                                      tuple(reversed(mod_v4_node.children))),
            "mod-v4-children-count": (mod_v4_path + ("children",), mod_v4_node.children[:1]),
            "mod-simplex-span": (mod_simplex_path + ("span", "start_column"), 99),
            "mod-simplex-callee": (mod_simplex_path + ("callee",), "clamp"),
            "mod-simplex-type": (mod_simplex_path + ("type",), vector("float", 4)),
            "mod-simplex-children-order": (mod_simplex_path + ("children",),
                                           tuple(reversed(mod_simplex_node.children))),
            "mod-simplex-children-count": (mod_simplex_path + ("children",),
                                           mod_simplex_node.children[:1]),
        }
        candidates = {name: replaced(exact, path, value)
                      for name, (path, value) in axes.items()}
        self.assertEqual(len(axes), len(candidates))
        self.assertEqual(41, len(candidates))
        self.assertEqual(
            "837c53da8a74f122028e9a892d69fc3f03215bcbaca99de40bb10d667f08cf15",
            hashlib.sha256(("\n".join(sorted(candidates)) + "\n").encode()).hexdigest())

        for name, candidate in candidates.items():
            # Each candidate must assert its own structural precondition --
            # that it genuinely changed the program -- before rejection is
            # meaningful; a no-op mutation would prove nothing.
            self.assertNotEqual(exact, candidate, name)
            with self.subTest(axis=name, layer="profile"), self.assertRaises(ValueError):
                authenticate_curl_vector_math(candidate, source_hash, PROFILE)
            with self.subTest(axis=name, layer="validator"), self.assertRaises(
                    generate_typed_slice.GeneratorError):
                generate_typed_slice.validate_capabilities(
                    candidate, generate_typed_slice.APPROVED_CAPABILITIES,
                    source_hash=source_hash, curl_vector_math_profile=PROFILE)
            with self.subTest(axis=name, layer="emitter"), self.assertRaises(
                    TypedEmissionError):
                render_typed_cpp(
                    candidate, candidate.key, source_hash,
                    curl_vector_math_profile=PROFILE)

    def test_task31_validator_and_emitter_authenticate_independently_without_trusting_each_other(self) -> None:
        import dataclasses
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
        from tools.glslcpp.frontend.curl_vector_math_profile import PROFILE

        _, source_hash, exact = self.exact_program()
        foreign = dataclasses.replace(exact, key="synth/curl:foreignvariant")

        # The emitter fails closed on its own authority: no profile, a wrong
        # profile string, and a foreign (differently-keyed) program carrying
        # the identical closure -- none of these ever invoke the validator.
        with self.assertRaisesRegex(TypedEmissionError, r"exact .* carrier required"):
            render_typed_cpp(exact, exact.key, source_hash)
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(
                exact, exact.key, source_hash, curl_vector_math_profile="wrong")
        with self.assertRaises(TypedEmissionError):
            render_typed_cpp(
                foreign, foreign.key, source_hash, curl_vector_math_profile=PROFILE)
        # With no carrier at all, the emitter walks into the closure and
        # rejects the first offending node on its OWN traversal order, never
        # having consulted the validator. The emitter's rendering visits
        # permute (the mod overloads) before main (the tanh site), so its
        # deepest-reachable rejection differs from the validator's below --
        # itself evidence the two authorities do not share traversal state.
        with self.assertRaisesRegex(
                TypedEmissionError,
                r"synth/curl:foreignvariant:32:12: unsupported builtin mod overload"):
            render_typed_cpp(foreign, foreign.key, source_hash)

        # The validator fails closed on its own authority, symmetrically,
        # without ever invoking the emitter.
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError, r"exact .* carrier required"):
            generate_typed_slice.validate_capabilities(
                exact, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                exact, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash, curl_vector_math_profile="wrong")
        with self.assertRaises(generate_typed_slice.GeneratorError):
            generate_typed_slice.validate_capabilities(
                foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash, curl_vector_math_profile=PROFILE)
        # The validator walks program.functions in stored tuple order, so it
        # reaches main's tanh before permute's mod -- the opposite of the
        # emitter's order above.
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                r"synth/curl:foreignvariant:196:12: unsupported builtin tanh"):
            generate_typed_slice.validate_capabilities(
                foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)

    def test_task31_capability_and_type_vocabulary_are_identity_scoped_not_widened(self) -> None:
        from tools.glslcpp import emit_typed_cpp, generate_typed_slice

        # tanh is absent from the 44-entry vocabulary and from both
        # authorities' builtin-name tables everywhere -- it follows the
        # identity-scoped skip pattern used by round/all/lessThanEqual/
        # floatBitsToUint, never a bare vocabulary addition.
        self.assertNotIn("tanh", generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertNotIn("tanh", generate_typed_slice._BUILTINS)
        self.assertNotIn("tanh", emit_typed_cpp._BUILTIN_NAMES)
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        spec = generate_typed_slice.load_slice(REPOSITORY)
        self.assertEqual(44, len(spec["capabilities"]))
        self.assertEqual(tuple(spec["capabilities"]),
                         generate_typed_slice.APPROVED_CAPABILITIES)

        # mod's shared overload-shape gate is an identical inline literal in
        # both authorities and must stay untouched -- Curl's three wider
        # (vec3/vec4, float) calls are admitted only by node identity, so no
        # other program gains vec3/vec4 mod. Assert both the profile's own
        # frozen copy of the set AND the literal text of both authorities'
        # source, so a future widening of the shared tuple itself (not just
        # the profile's copy) is caught.
        from tools.glslcpp.frontend.curl_vector_math_profile import _GENERAL_MOD_OVERLOADS
        self.assertEqual(
            frozenset({("float", "float"), ("vec2", "float"), ("vec2", "vec2")}),
            _GENERAL_MOD_OVERLOADS)
        literal = '{("float", "float"), ("vec2", "float"), ("vec2", "vec2")}'
        generator_source = (REPOSITORY / "tools/glslcpp/generate_typed_slice.py").read_text()
        emitter_source = (REPOSITORY / "tools/glslcpp/emit_typed_cpp.py").read_text()
        self.assertEqual(1, generator_source.count(literal))
        self.assertEqual(1, emitter_source.count(literal))

        # Behavioral proof, not just a static list check: validate_capabilities
        # succeeds against the UNMODIFIED 44-entry tuple (which itself
        # excludes tanh) when authenticating Curl -- direct evidence tanh
        # never enters `used`, mirroring round/all/lessThanEqual.
        _, source_hash, exact = self.exact_program()
        from tools.glslcpp.frontend.curl_vector_math_profile import PROFILE
        generate_typed_slice.validate_capabilities(
            exact, generate_typed_slice.APPROVED_CAPABILITIES,
            source_hash=source_hash, curl_vector_math_profile=PROFILE)
        emit_typed_cpp.render_typed_cpp(
            exact, exact.key, source_hash, curl_vector_math_profile=PROFILE)

        # Identity scoping proven behaviorally: a foreign (differently-keyed)
        # program carrying the identical tanh/mod closure is rejected at both
        # authorities -- the widened mod overload gate never opens for
        # anyone but the exact authenticated Curl nodes.
        import dataclasses
        foreign = dataclasses.replace(exact, key="synth/curl:foreignvariant")
        with self.assertRaisesRegex(
                generate_typed_slice.GeneratorError,
                r"unsupported builtin (tanh|mod overload)"):
            generate_typed_slice.validate_capabilities(
                foreign, generate_typed_slice.APPROVED_CAPABILITIES,
                source_hash=source_hash)
        from tools.glslcpp.emit_typed_cpp import TypedEmissionError
        with self.assertRaisesRegex(
                TypedEmissionError, r"unsupported builtin (tanh|mod overload)"):
            emit_typed_cpp.render_typed_cpp(foreign, foreign.key, source_hash)

    def test_task31_node_level_closure_logic_rejects_past_the_coarse_hash_gate(self) -> None:
        """The profile's node-walk/typing logic must itself reject.

        The sibling single-axis mutation test proves the profile is closed,
        but every one of its axes is absorbed by the coarse "source, define,
        function, whole-program, or interface mismatch" gate, because any
        tree edit perturbs the whole-program hash. That leaves the module's
        *novel* logic -- closure-site census and node-identity comparison --
        unexercised.

        Here the coarse gate is deliberately re-frozen to match each mutated
        tree, so the node-level checks actually run. Each mutation must then
        be rejected by a SPECIFIC node-level message, never by the coarse
        one.
        """
        import hashlib
        from tools.glslcpp.frontend import (
            curl_vector_math_profile as profile)

        COARSE = ("source, define, function, whole-program, "
                  "or interface mismatch")

        def walk_expression(value):
            yield value
            for child in value.children:
                yield from walk_expression(child)

        def walk_statement(statement):
            yield statement
            for child in statement.children:
                yield from walk_statement(child)

        def function_by_id(program, function_id):
            return next(item for item in program.functions if item.id == function_id)

        def sites(program, function_id, callee):
            function = function_by_id(program, function_id)
            return [node
                    for statement in function.body
                    for owner in walk_statement(statement)
                    for expression in owner.expressions
                    for node in walk_expression(expression)
                    if node.kind == "builtin" and node.callee == callee]

        def rename_tanh(program):
            object.__setattr__(sites(program, 18, "tanh")[0], "callee", "sin")

        def rename_mod_v4(program):
            object.__setattr__(sites(program, 20, "mod")[0], "callee", "min")

        def orphan_tanh_child(program):
            object.__setattr__(sites(program, 18, "tanh")[0], "children", ())

        def widen_mod_simplex_arity(program):
            node = sites(program, 21, "mod")[0]
            object.__setattr__(node, "children", (*node.children, node.children[0]))

        def retype_mod_dead_argument(program):
            from tools.glslcpp.frontend.semantic_types import vector
            node = sites(program, 19, "mod")[0]
            object.__setattr__(node.children[0], "type", vector("float", 2))

        def collide_simplex_function_id(program):
            function = function_by_id(program, 21)
            object.__setattr__(function.signature, "id", 20)

        cases = (
            ("tanh renamed to sin at the one authorized site",
             rename_tanh, "closure site cardinality mismatch"),
            ("permute(vec4)'s mod renamed to min",
             rename_mod_v4, "closure site cardinality mismatch"),
            ("tanh loses its only child",
             orphan_tanh_child, "closure node identity mismatch"),
            ("simplex3D's mod gains a third argument",
             widen_mod_simplex_arity, "closure node identity mismatch"),
            ("the dead permute(vec3) mod's vec3 argument retyped to vec2",
             retype_mod_dead_argument, "closure node identity mismatch"),
            ("simplex3D's function id perturbed to collide with permute(vec4)",
             collide_simplex_function_id, "function inventory mismatch"),
        )

        _, source_hash, baseline = self.exact_program()
        baseline_functions = profile._sha(baseline.functions)

        for label, mutate, expected in cases:
            with self.subTest(node_axis=label):
                _, _, candidate = self.exact_program()
                mutate(candidate)
                # The mutation must genuinely change the tree, or the case is
                # vacuous regardless of what the profile then reports.
                self.assertNotEqual(baseline_functions,
                                    profile._sha(candidate.functions), label)

                normalized = candidate.source.encode("utf-8")
                loop_proof = candidate.counted_loop_proof
                with mock.patch.multiple(
                        profile,
                        _FUNCTIONS_SHA256=profile._sha(candidate.functions),
                        _WHOLE_SHA256=profile._whole(candidate),
                        _INTERFACE_SHA256=profile._interface(candidate),
                        _NORMALIZED_SHA256=hashlib.sha256(normalized).hexdigest(),
                        _NORMALIZED_BYTES=len(normalized),
                        _LOOP_PROOF=(loop_proof.loop_count,
                                     loop_proof.unproved_loop_count,
                                     loop_proof.max_effective_depth,
                                     loop_proof.max_lexical_product,
                                     loop_proof.entrypoint_charge,
                                     loop_proof.call_graph_acyclic)):
                    with self.assertRaises(ValueError) as raised:
                        profile.authenticate_curl_vector_math(
                            candidate, source_hash, profile.PROFILE)
                message = str(raised.exception)
                self.assertNotIn(COARSE, message,
                                 f"{label} was absorbed by the coarse gate")
                self.assertIn(expected, message, label)

        # The patched constants must be restored, or later tests inherit a
        # profile that authenticates the wrong program.
        _, source_hash, exact = self.exact_program()
        profile.authenticate_curl_vector_math(exact, source_hash, profile.PROFILE)

    def test_task31_history_live_schema_ordinal_and_vendored_oracle_match_131_program_state(self) -> None:
        import hashlib
        from tools.glslcpp import check_corpus, generate_typed_slice
        from tools.glslcpp.frontend.curl_vector_math_profile import CURL_KEY, PROFILE

        spec = generate_typed_slice.load_slice(REPOSITORY)
        typed = tuple(item["program_key"] for item in spec["programs"])
        public = tuple(sorted((*typed, "filter/invert:inv", "synth/solid:solid")))
        corpus = json.loads((check_corpus._corpus_root(REPOSITORY) /
                             "manifest.json").read_text())
        unported = tuple(sorted(
            {item["program_key"] for item in corpus["programs"]} - set(public)))
        self.assertEqual((137, 139, 73, 212),
                         (len(typed), len(public), len(unported),
                          len(corpus["programs"])))
        self.assertEqual(
            "dfb7c7c43d7fd118c4a1b9a266d6957a90b189ec63ac6b0d49538bd853a360d7",
            hashlib.sha256(("\n".join(typed) + "\n").encode()).hexdigest())
        self.assertEqual(
            "a873c537d3d8ffb872859389812ae7c1e68954c9fcd381334eca4998195f319f",
            hashlib.sha256(("\n".join(public) + "\n").encode()).hexdigest())
        self.assertEqual(126, typed.index(CURL_KEY))
        self.assertEqual(("synth/cell:cell", CURL_KEY, "synth/gradient:gradient"),
                         typed[125:128])
        self.assertEqual([{
            "curl_vector_math_profile": PROFILE,
            "defines": {"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True},
            "program_key": CURL_KEY,
        }], [item for item in spec["programs"] if "curl_vector_math_profile" in item])

        current_outputs = generate_typed_slice.generate_outputs(REPOSITORY)
        manifest = json.loads(
            current_outputs["src/typed_generated/typed_manifest.json"])
        curl_row = next(item for item in manifest["programs"]
                        if item["program_key"] == CURL_KEY)
        self.assertEqual(PROFILE, curl_row["curl_vector_math_profile"])
        self.assertEqual({"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True},
                         curl_row["defines"])
        # The live ordinal (120) is baked into the generated namespace name.
        current_cpp = current_outputs["src/typed_generated/typed_slice.cpp"].decode()
        curl_start = current_cpp.index(f"// Typed IR program: {CURL_KEY}")
        curl_end = current_cpp.index("// Typed IR program:", curl_start + 1)
        self.assertIn("namespace typed_126 {", current_cpp[curl_start:curl_end])
        # tanh_lanewise is Curl's alone -- no other program's block emits it.
        self.assertEqual(1, current_cpp.count("tanh_lanewise"))
        self.assertIn("tanh_lanewise", current_cpp[curl_start:curl_end])

        # The oracle vendored for the native fixture (not this Python job's
        # concern to bind, but its identity claims are cross-checked here so
        # a future native-test author inherits a verified artifact).
        oracle_path = REPOSITORY / "tests/oracles/task-31-oracles.json"
        self.assertTrue(oracle_path.is_file(), "Task 31 frozen oracle JSON is required")
        oracle_bytes = oracle_path.read_bytes()
        self.assertEqual(
            "dc992d217dda4e908b33826dde6da744347a9ff5c5a7a7befd3a43c96949001c",
            hashlib.sha256(oracle_bytes).hexdigest())
        oracle = json.loads(oracle_bytes)
        self.assertEqual(CURL_KEY, oracle["program"]["key"])
        self.assertEqual({"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True},
                         oracle["program"]["defines"])
        self.assertEqual("33d1f2bd0215d6439b51a0aa8d50b5c3637abc0b5cade8f3e451b8d258d0afce",
                         oracle["program"]["source_sha256"])
        # Eligibility rule: only cases whose define map equals exactly the
        # authorized one are eligible for native binding/parity comparison.
        self.assertEqual({"total_cases": 9, "eligible_cases": 6, "ineligible_cases": 3},
                         oracle["eligibility_summary"])
        self.assertEqual(6, len(oracle["eligible_render_cases"]))
        self.assertTrue(all(
            item["defines"] == {"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True}
            and item["eligible_for_native_binding"]
            for item in oracle["eligible_render_cases"]))
        self.assertEqual(3, len(oracle["ineligible_render_cases"]))
        self.assertTrue(all(
            item["defines"] != {"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True}
            for item in oracle["ineligible_render_cases"]))

    def test_task31_removing_only_curl_regenerates_task30_outputs_byte_for_byte(self) -> None:
        import copy
        import hashlib
        from tools.glslcpp import generate_typed_slice
        from tools.glslcpp.frontend.curl_vector_math_profile import CURL_KEY

        spec = generate_typed_slice.load_slice(REPOSITORY)
        task30_spec = copy.deepcopy(spec)
        task30_spec["programs"] = [item for item in task30_spec["programs"]
                                   if item["program_key"] not in (
                                       CURL_KEY,
                                       "filter/grade:creative",
                                       "filter/grade:hslSecondary",
                                       "filter/grade:lut",
                                       "filter/grade:primary",
                                       "filter/grade:vignette",
                                       "filter/grade:wheels")]
        task30_keys = tuple(item["program_key"] for item in task30_spec["programs"])
        self.assertEqual(130, len(task30_keys))
        self.assertEqual(
            "d31014f538686245f09fefe57ffccf9f2b8d36bdcaf65b0ae423be7476ab5904",
            hashlib.sha256(("\n".join(task30_keys) + "\n").encode()).hexdigest())

        # load_slice hard-pins the live 131-program count/hash, so the
        # Task30 reconstruction must go through the mocked loader, exactly
        # as the Task30 test reconstructs Task29.
        with mock.patch.object(generate_typed_slice, "load_slice",
                               return_value=task30_spec):
            task30 = generate_typed_slice.generate_outputs(REPOSITORY)
        task30["include/noisemaker/generated/catalog.hpp"] = (
            generate_typed_slice.render_catalog_header(task30_spec))
        expected_task30 = {
            "src/typed_generated/typed_slice.cpp":
                "5765f8637fd08711cb665c295b7f1488f76fc2c19515b22d72c476e51808b5f3",
            "src/typed_generated/typed_manifest.json":
                "3a6b52895f4a4f4e25a3bafb67d84a40e194e11d157508fc1dc9763cb304c87e",
            "include/noisemaker/generated/catalog.hpp":
                "16ebd7b1c7908fcad87e4a0c1890b2eabc87a0ce09fa6ded961ce68162315b42",
        }
        for path, expected in expected_task30.items():
            self.assertEqual(expected, hashlib.sha256(task30[path]).hexdigest(), path)

        marker = re.compile(r"(?m)^// Typed IR program: ([^\n]+)\n")
        def blocks(payload):
            source = payload.decode()
            starts = list(marker.finditer(source))
            catalog = source.index(
                "\nnamespace {\nconstexpr std::array<KernelFactory")
            return {match.group(1): source[
                match.start():(starts[index + 1].start()
                               if index + 1 < len(starts) else catalog)]
                for index, match in enumerate(starts)}

        task30_blocks = blocks(task30["src/typed_generated/typed_slice.cpp"])
        self.assertEqual(130, len(task30_blocks))
        self.assertNotIn(CURL_KEY, task30_blocks)
        self.assertEqual(0, sum(block.count("tanh_lanewise")
                                for block in task30_blocks.values()))


if __name__ == "__main__":
    unittest.main()
