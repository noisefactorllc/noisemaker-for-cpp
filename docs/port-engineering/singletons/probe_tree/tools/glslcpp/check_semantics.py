"""Validate every pinned GLSL program through the immutable semantic frontier."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import Counter

if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from tools.glslcpp import check_corpus
    from tools.glslcpp.frontend import FrontendError, parse_program
    from tools.glslcpp.frontend.diagnostics import SemanticError
    from tools.glslcpp.frontend.semantic import analyze_program
else:
    from . import check_corpus
    from .frontend import FrontendError, parse_program
    from .frontend.diagnostics import SemanticError
    from .frontend.semantic import analyze_program


def _metadata_defaults(metadata: dict, program_key: str) -> dict[str, int | float | bool]:
    effect = metadata.get("effects", {}).get(program_key.split(":", 1)[0], {})
    result: dict[str, int | float | bool] = {}
    for parameter in effect.get("params", {}).values():
        define = parameter.get("define")
        default = parameter.get("default")
        if define and isinstance(default, (int, float, bool)):
            result[define] = default
    return result


def _define_variants(metadata: dict) -> tuple[tuple[str, str, str, int | float | bool], ...]:
    """Enumerate one static metadata define override at a time, deterministically."""
    variants: list[tuple[str, str, str, int | float | bool]] = []
    for effect_key, effect in sorted(metadata.get("effects", {}).items()):
        for parameter_name, parameter in sorted(effect.get("params", {}).items()):
            define = parameter.get("define")
            if not define: continue
            if "choices" in parameter:
                values = sorted({value for value in parameter["choices"].values()
                                 if isinstance(value, (int, float)) and not isinstance(value, bool)})
            elif parameter.get("type") in {"bool", "boolean"}:
                values = [False, True]
            elif all(key in parameter for key in ("min", "max")):
                step = parameter.get("step", 1)
                if not all(isinstance(value, (int, float)) and not isinstance(value, bool)
                           for value in (parameter["min"], parameter["max"], step)) or step <= 0:
                    raise ValueError(f"invalid define range {effect_key}/{parameter_name}")
                count = int(round((parameter["max"] - parameter["min"]) / step))
                values = [parameter["min"] + index * step for index in range(count + 1)]
            else:
                raise ValueError(f"unhandled define parameter {effect_key}/{parameter_name}")
            if not values: raise ValueError(f"empty define values {effect_key}/{parameter_name}")
            variants.extend((effect_key, parameter_name, define, value) for value in values)
    return tuple(variants)


def _validate_typed_ir(typed) -> None:
    """Fail closed if a successful IR contains a dangling identity or placeholder."""
    signature_ids = {function.signature.id for function in typed.functions}
    symbol_ids = {symbol.id for symbol in typed.interface_symbols + typed.builtin_symbols}
    symbol_ids.update(declaration.symbol.id for declaration in typed.declarations)

    def expression(value) -> None:
        if value.kind == "invalid": raise ValueError(f"invalid typed expression in {typed.key}")
        if value.symbol_id is not None:
            if value.symbol is None or value.symbol.id != value.symbol_id:
                raise ValueError(f"dangling symbol identity in {typed.key}")
            symbol_ids.add(value.symbol.id)
        if value.signature_id is not None:
            if value.signature_id > 0 and value.signature_id not in signature_ids:
                raise ValueError(f"dangling user signature in {typed.key}")
            if value.signature_id < 0 and not value.callee:
                raise ValueError(f"dangling builtin signature in {typed.key}")
        for child in value.children: expression(child)

    def statement(value) -> None:
        if value.kind == "invalid": raise ValueError(f"invalid typed statement in {typed.key}")
        for item in value.expressions: expression(item)
        for child in value.children: statement(child)

    for function in typed.functions:
        for statement_value in function.body: statement(statement_value)


def semantic_report(repository: pathlib.Path | None = None) -> dict:
    """Run corpus integrity first, then analyze all programs in manifest order."""
    repository = (repository or pathlib.Path(__file__).resolve().parents[2]).resolve()
    corpus = check_corpus.validate_corpus(repository)
    root = check_corpus._corpus_root(repository)
    manifest = check_corpus._load_json(root / "manifest.json", "manifest")
    metadata = check_corpus._load_json(root / "metadata.json", "metadata")
    programs = check_corpus._validate_manifest(manifest)
    diagnostics: list[str] = []
    types: Counter[str] = Counter()
    operators: Counter[str] = Counter()
    builtins: Counter[str] = Counter()
    overloads: Counter[str] = Counter()
    features: dict[str, dict] = {}
    global_initializer_success = 0

    def walk_expression(expression) -> None:
        if expression.kind == "builtin": builtins[expression.callee or "<builtin>"] += 1
        if expression.operator is not None: operators[expression.operator] += 1
        if expression.signature_id is not None: overloads[expression.callee or str(expression.signature_id)] += 1
        types[expression.type.display()] += 1
        for child in expression.children: walk_expression(child)

    def walk_statement(statement) -> None:
        for expression in statement.expressions: walk_expression(expression)
        for child in statement.children: walk_statement(child)

    for entry in programs:
        key = entry["program_key"]
        try:
            parsed = parse_program((root / entry["source"]).read_text(encoding="utf-8"), key,
                                   _metadata_defaults(metadata, key))
            typed = analyze_program(parsed, key)
            _validate_typed_ir(typed)
        except (FrontendError, SemanticError, OSError, UnicodeDecodeError) as error:
            diagnostics.append(str(error)); continue
        for declaration in typed.declarations: types[declaration.type.display()] += 1
        global_initializer_success += sum(declaration.initializer is not None for declaration in typed.declarations)
        for function in typed.functions:
            types[function.return_type.display()] += 1
            for parameter in function.parameters: types[parameter.type.display()] += 1
            for statement in function.body: walk_statement(statement)
        features[key] = {
            "body_status": typed.body_status,
            "functions": len(typed.functions),
            "globals": len(typed.declarations),
            "outputs": list(typed.resources.outputs),
            "samplers": list(typed.resources.samplers),
            "uniforms": list(typed.resources.uniforms),
            "uses_derivatives": typed.resources.uses_derivatives,
            "uses_texture": typed.resources.uses_texture,
        }
    variants = _define_variants(metadata)
    programs_by_effect: dict[str, list[dict]] = {}
    for entry in programs:
        programs_by_effect.setdefault(entry["program_key"].split(":", 1)[0], []).append(entry)
    variant_diagnostics: list[tuple[str, str, str, str, str]] = []
    variant_success = 0
    for effect_key, parameter_name, define, value in variants:
        for entry in programs_by_effect.get(effect_key, ()):
            key = entry["program_key"]
            defines = _metadata_defaults(metadata, key)
            defines[define] = value
            try:
                typed_variant = analyze_program(parse_program((root / entry["source"]).read_text(encoding="utf-8"), key, defines), key)
                _validate_typed_ir(typed_variant)
                variant_success += 1
            except (FrontendError, SemanticError, OSError, UnicodeDecodeError) as error:
                variant_diagnostics.append((key, parameter_name, define, repr(value), str(error)))
    if diagnostics:
        raise ValueError("\n".join(sorted(diagnostics)))
    if variant_diagnostics:
        raise ValueError("\n".join(
            f"{key}:{parameter}:{define}={value}: {message}"
            for key, parameter, define, value, message in sorted(variant_diagnostics)))
    return {
        "body_analysis": "complete",
        "body_success": len(features),
        "builtin_incidence": dict(sorted(builtins.items())),
        "compile": "not attempted",
        "corpus": corpus["counts"],
        "emission": "not attempted",
        "features": dict(sorted(features.items())),
        "global_initializer_success": global_initializer_success,
        "operator_incidence": dict(sorted(operators.items())),
        "overload_incidence": dict(sorted(overloads.items())),
        "revision": check_corpus.REVISION,
        "type_incidence": dict(sorted(types.items())),
        "variant_candidates": len(variants),
        "variant_success": variant_success,
    }


# Compatibility name retained for Task 7A callers; it now has the completed
# body contract rather than silently stopping at declarations.
declaration_report = semantic_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--report", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        report = semantic_report()
    except (check_corpus.CorpusError, FrontendError, SemanticError, ValueError) as error:
        print(f"check_semantics: {error}", file=sys.stderr)
        return 1
    if report["body_success"] != 212:
        print("check_semantics: body count drift", file=sys.stderr)
        return 1
    if report["variant_candidates"] != 622 or report["variant_success"] != 646:
        print("check_semantics: define-variant count drift", file=sys.stderr)
        return 1
    if arguments.report: print(json.dumps(report, indent=2, sort_keys=True))
    else: print("check_semantics: bodies ok (212 programs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
