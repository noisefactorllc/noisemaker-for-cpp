"""Regenerate the fixed Task-5 C++ kernels from pinned local fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from tools.glslcpp.emit_cpp import render_cpp
    from tools.glslcpp.parser import GeneratorError, parse_program
else:
    from .emit_cpp import render_cpp
    from .parser import GeneratorError, parse_program


SCHEMA = 1
_ROOT = pathlib.Path(__file__).resolve().parents[2]
_FIXTURE_ROOT = _ROOT / "tools" / "glslcpp" / "fixtures"
_GENERATED_DIRECTORY = pathlib.PurePosixPath("src/generated")
_GENERATED_MANIFEST_NAME = "manifest.json"
_WINDOWS_RESERVED_DEVICE_BASENAMES = frozenset({
    "CON", "PRN", "AUX", "NUL", "CLOCK$",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
    *(f"COM{superscript}" for superscript in "¹²³"),
    *(f"LPT{superscript}" for superscript in "¹²³"),
})


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _stripped_bytes(content: bytes) -> bytes:
    return content.strip()


def load_fixture_manifest(repository: pathlib.Path = _ROOT) -> dict[str, Any]:
    fixture_root = repository / "tools" / "glslcpp" / "fixtures"
    candidates = sorted(fixture_root.glob("*/manifest.json"))
    if len(candidates) != 1:
        raise GeneratorError("fixture manifest count must be exactly one")
    try:
        manifest = json.loads(candidates[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GeneratorError(f"invalid fixture manifest: {error}") from error
    if manifest.get("schema") != SCHEMA or not isinstance(manifest.get("revision"), str):
        raise GeneratorError("unsupported fixture manifest schema")
    programs = manifest.get("programs")
    if not isinstance(programs, list) or not programs:
        raise GeneratorError("fixture manifest has no programs")
    required = {"program_key", "source", "output", "raw_sha256", "stripped_sha256", "pass_bindings"}
    keys: list[str] = []
    outputs: set[str] = set()
    for entry in programs:
        if not isinstance(entry, dict) or set(entry) != required:
            raise GeneratorError("fixture manifest program fields are invalid")
        if not all(isinstance(entry[field], str) for field in required - {"pass_bindings"}):
            raise GeneratorError("fixture manifest program values are invalid")
        if not isinstance(entry["pass_bindings"], dict) or not all(
                isinstance(name, str) and isinstance(type_name, str)
                for name, type_name in entry["pass_bindings"].items()):
            raise GeneratorError("fixture manifest pass bindings are invalid")
        _validate_output_name(entry["output"])
        if entry["output"] in outputs:
            raise GeneratorError("fixture manifest has duplicate output")
        outputs.add(entry["output"])
        keys.append(entry["program_key"])
    if len(set(keys)) != len(keys):
        raise GeneratorError("fixture manifest program keys must be unique")
    return {**manifest, "programs": sorted(programs, key=lambda entry: entry["program_key"])}


def _validate_output_name(output: str) -> None:
    windows = pathlib.PureWindowsPath(output)
    device = output.split(".", 1)[0].rstrip(" .").upper()
    if (not output or output == _GENERATED_MANIFEST_NAME or not output.endswith(".cpp")
            or "/" in output or "\\" in output or ":" in output or output in {".", ".."}
            or pathlib.PurePosixPath(output).name != output
            or windows.name != output or windows.is_absolute()
            or pathlib.PurePosixPath(output).is_absolute()
            or device in _WINDOWS_RESERVED_DEVICE_BASENAMES):
        raise GeneratorError("fixture manifest output must be a bare approved .cpp filename")


def verify_fixture_bytes(entry: dict[str, Any], content: bytes) -> None:
    if _sha256(content) != entry["raw_sha256"]:
        raise GeneratorError(f"{entry['program_key']}: fixture hash mismatch (raw)")
    if _sha256(_stripped_bytes(content)) != entry["stripped_sha256"]:
        raise GeneratorError(f"{entry['program_key']}: fixture hash mismatch (stripped)")


def _fixture_path(repository: pathlib.Path, manifest: dict[str, Any], entry: dict[str, Any]) -> pathlib.Path:
    path = repository / "tools" / "glslcpp" / "fixtures" / manifest["revision"] / entry["source"]
    if path.parent != repository / "tools" / "glslcpp" / "fixtures" / manifest["revision"]:
        raise GeneratorError(f"{entry['program_key']}: fixture path escapes pinned directory")
    return path


def _generated_path(repository: pathlib.Path, output: str) -> pathlib.Path:
    _validate_output_name(output)
    target = repository / _GENERATED_DIRECTORY
    if target.is_symlink() or (target.parent.exists() and target.parent.is_symlink()):
        raise GeneratorError("generated output directory must not be a symlink")
    target_resolved = target.resolve()
    final = (target / output).resolve()
    if final.parent != target_resolved:
        raise GeneratorError("generated output path escapes src/generated")
    return final


def _validate_pass_bindings(entry: dict[str, Any], program: Any) -> None:
    parsed = {uniform.name: uniform.type_name for uniform in program.uniforms}
    if entry["pass_bindings"] != parsed:
        raise GeneratorError(f"{entry['program_key']}: pass bindings do not match parsed uniforms")


def generate_outputs(repository: pathlib.Path = _ROOT) -> dict[str, bytes]:
    repository = repository.resolve()
    manifest = load_fixture_manifest(repository)
    rendered: dict[str, bytes] = {}
    manifest_programs: list[dict[str, str]] = []
    for entry in manifest["programs"]:
        fixture = _fixture_path(repository, manifest, entry)
        try:
            content = fixture.read_bytes()
        except OSError as error:
            raise GeneratorError(f"{entry['program_key']}: cannot read fixture: {error}") from error
        verify_fixture_bytes(entry, content)
        try:
            source = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise GeneratorError(f"{entry['program_key']}: fixture is not UTF-8") from error
        program = parse_program(source, entry["program_key"])
        _validate_pass_bindings(entry, program)
        rendered_source = render_cpp(
            program, manifest["revision"], entry["raw_sha256"], entry["pass_bindings"]
        ).encode("utf-8")
        output = str(_generated_path(repository, entry["output"]).relative_to(repository))
        rendered[output] = rendered_source
        manifest_programs.append({
            "program_key": entry["program_key"],
            "source": entry["source"],
            "raw_sha256": entry["raw_sha256"],
            "stripped_sha256": entry["stripped_sha256"],
            "output": entry["output"],
            "generated_sha256": _sha256(rendered_source),
        })
    generated_manifest = {
        "schema": SCHEMA,
        "revision": manifest["revision"],
        "programs": manifest_programs,
    }
    rendered[str(_GENERATED_DIRECTORY / "manifest.json")] = (
        json.dumps(generated_manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return dict(sorted(rendered.items()))


def _expected_generated_names(outputs: dict[str, bytes]) -> set[str]:
    return {pathlib.PurePosixPath(relative).name for relative in outputs}


def _validate_generated_tree(directory: pathlib.Path, expected: set[str]) -> None:
    if directory.is_symlink():
        raise GeneratorError("generated tree contains a symlink")
    if not directory.exists():
        return
    if not directory.is_dir():
        raise GeneratorError("generated output path is not a directory")
    actual: set[str] = set()
    unexpected_directories: list[pathlib.Path] = []

    def visit(current: pathlib.Path) -> None:
        with os.scandir(current) as entries:
            for entry in entries:
                path = pathlib.Path(entry.path)
                if entry.is_symlink():
                    raise GeneratorError("generated tree contains a symlink")
                if entry.is_dir(follow_symlinks=False):
                    unexpected_directories.append(path)
                    visit(path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    raise GeneratorError("generated tree contains an unexpected entry")
                actual.add(str(path.relative_to(directory)))

    visit(directory)
    if unexpected_directories:
        raise GeneratorError("generated tree contains an unexpected directory")
    if actual != expected:
        raise GeneratorError(f"generated file set drift: expected {sorted(expected)}, got {sorted(actual)}")


def _stage_outputs(parent: pathlib.Path, outputs: dict[str, bytes]) -> pathlib.Path:
    stage = pathlib.Path(tempfile.mkdtemp(prefix=".glslcpp-stage-", dir=parent))
    try:
        for relative, content in outputs.items():
            name = pathlib.PurePosixPath(relative).name
            (stage / name).write_bytes(content)
        return stage
    except BaseException:
        shutil.rmtree(stage)
        raise


def _remove_owned_directory(path: pathlib.Path, parent: pathlib.Path, prefix: str) -> None:
    if path.parent != parent or not path.name.startswith(prefix) or path.is_symlink():
        raise GeneratorError("refusing to remove an unowned generator temporary directory")
    if path.exists():
        shutil.rmtree(path)


def write_outputs(repository: pathlib.Path = _ROOT) -> None:
    repository = repository.resolve()
    outputs = generate_outputs(repository)
    expected = _expected_generated_names(outputs)
    target = repository / _GENERATED_DIRECTORY
    if target.is_symlink() or (target.parent.exists() and target.parent.is_symlink()):
        raise GeneratorError("generated output directory must not be a symlink")
    _validate_generated_tree(target, expected)
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = _stage_outputs(target.parent, outputs)
    backup = pathlib.Path(tempfile.mkdtemp(prefix=".glslcpp-backup-", dir=target.parent))
    _remove_owned_directory(backup, target.parent, ".glslcpp-backup-")
    had_target = target.exists()
    moved_target = False
    try:
        if had_target:
            os.replace(target, backup)
            moved_target = True
        os.replace(stage, target)
    except BaseException:
        if moved_target:
            try:
                os.replace(backup, target)
            except BaseException as restore_error:
                raise GeneratorError("generated tree swap failed and rollback could not restore backup") from restore_error
        raise
    else:
        if moved_target:
            _remove_owned_directory(backup, target.parent, ".glslcpp-backup-")
    finally:
        if stage.exists():
            _remove_owned_directory(stage, target.parent, ".glslcpp-stage-")
        if backup.exists() and not moved_target:
            _remove_owned_directory(backup, target.parent, ".glslcpp-backup-")


def check_outputs(repository: pathlib.Path = _ROOT) -> None:
    repository = repository.resolve()
    outputs = generate_outputs(repository)
    directory = repository / _GENERATED_DIRECTORY
    _validate_generated_tree(directory, _expected_generated_names(outputs))
    for relative, content in outputs.items():
        try:
            current = (repository / relative).read_bytes()
        except OSError as error:
            raise GeneratorError(f"missing generated output {relative}: {error}") from error
        if current != content:
            raise GeneratorError(f"generated output drift: {relative}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        if arguments.write:
            write_outputs(_ROOT)
        else:
            check_outputs(_ROOT)
    except GeneratorError as error:
        print(f"glslcpp: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
