#!/usr/bin/env python3
"""Differential accept/refuse + byte-exact test over DSL LITERAL FORMS.

Complements ``tools/parity/sweep.py`` (which samples the *value domain* of
each parameter, always in its own canonical literal syntax) by instead
varying the *literal syntax* itself -- including deliberately invalid forms
-- for a representative sample of every parameter TYPE in the catalog:
float, int (plain and enum-like), boolean, color (every hex width, array,
vecN, and invalid forms), vec2/vec3/vec4/mat3 (correct width, wrong width,
scalar), member/palette/enum-like string (by name, by number, unknown name),
plain string, surface (o0..o7, out-of-range, none), and volume/geometry.

For each generated program this renders through both the JS authority
(``tools/benchmark/run_cpu_case.mjs``) and the C++ driver
(``noisemaker-dsl-cpu-case``, via ``tools.benchmark.corpus_lane.record_flags``
-- the same argv contract ``sweep.py`` and the frozen parity test use) and
requires: identical accept/refuse, and, when both accept, byte-exact RGBA8.
Reuses ``sweep.py``'s ``Job``/``run_job``/``RunConfig`` machinery directly so
the classification and comparison semantics are identical to the sweep.

Every case is a *single* literal substituted into ONE parameter of one
effect, wrapped exactly like ``sweep.py``'s ``source_for_single``: a filter
gets ``solid(color: #3a7).<call>``, a generator is the whole chain. Effects
whose domain needs an external texture or a volume/geometry chain still run
through the same wrapper (matching the domain's own required-input error
identically on both sides is itself a valid parity data point) rather than
being special-cased away.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

LANE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LANE_ROOT))
sys.path.insert(0, str(LANE_ROOT / "tools/parity"))

import sweep  # noqa: E402


def wrap(effect: dict, call_args: str) -> str:
    namespaces = [effect["namespace"]]
    if effect["kind"] != "generator" and "synth" not in namespaces:
        namespaces.append("synth")
    call = f"{effect['func']}({call_args})"
    chain = call if effect["kind"] == "generator" else f"solid(color: #3a7).{call}"
    lines = [f"search {', '.join(namespaces)}", f"{chain}.write(o0)", "render(o0)"]
    return "\n".join(lines) + "\n"


def default_args_with_override(effect: dict, param_name: str, literal: str) -> str:
    parts = []
    for name, param in effect["params"].items():
        if name == param_name:
            parts.append(f"{name}: {literal}")
            continue
        default = param.get("default")
        parts.append(f"{name}: {sweep.dsl_value(param, default)}")
    return ", ".join(parts)


CASES: list[tuple[str, str, str, str]] = []  # (case_tag, effect_id, param_name, literal)


def add(tag: str, effect_id: str, param_name: str, literal: str) -> None:
    CASES.append((tag, effect_id, param_name, literal))


def build_cases(catalog: list[dict]) -> None:
    by_id = {e["id"]: e for e in catalog}

    def first_param(effect_id: str, ptype: str) -> str:
        for name, p in by_id[effect_id]["params"].items():
            if p["type"] == ptype:
                return name
        raise KeyError((effect_id, ptype))

    # ---- color: every literal syntax the authority's parser/normalizer
    # accepts or refuses (parser.js parseColor / tokenize.js `#` rule /
    # definition.js colorValue+normalizeValue "color" case). ----
    color_targets = [
        ("filter/tint", "color"),
        ("classicNoisedeck/composite", "inputColor"),
        ("synth/gradient", "color1"),
        ("filter/tetraColorArray", "color0"),
    ]
    for eff, param in color_targets:
        add(f"color-short3-{eff}", eff, param, "#3a7")
        add(f"color-long6-{eff}", eff, param, "#3377ee")
        add(f"color-long8-alpha-{eff}", eff, param, "#3377eecc")
        add(f"color-array3-{eff}", eff, param, "[0.2, 0.4, 0.8]")
        add(f"color-array4-{eff}", eff, param, "[0.2, 0.4, 0.8, 0.7]")
        add(f"color-vec3lit-{eff}", eff, param, "vec3(0.2, 0.4, 0.8)")
        add(f"color-vec4lit-{eff}", eff, param, "vec4(0.2, 0.4, 0.8, 0.7)")
        add(f"color-badhex5-{eff}", eff, param, "#12345")
        add(f"color-array2-{eff}", eff, param, "[0.2, 0.4]")
        add(f"color-array5-{eff}", eff, param, "[0.2, 0.4, 0.8, 0.7, 0.1]")
        add(f"color-vec2lit-{eff}", eff, param, "vec2(0.2, 0.4)")
        add(f"color-scalar-{eff}", eff, param, "0.5")
        add(f"color-bool-{eff}", eff, param, "true")

    # ---- true vecN/mat3: correct width, wrong width, array vs vecN(), scalar.
    vec_targets = [
        ("classicNoisedeck/fractal", "vec3", "paletteAmp"),
        ("synth/remap", "vec4", "zone0_bounds"),
        ("synth/media", "vec2", "imageSize"),
    ]
    for eff, ptype, param in vec_targets:
        width = {"vec2": 2, "vec3": 3, "vec4": 4}[ptype]
        good = ", ".join(str(0.1 * (i + 1)) for i in range(width))
        add(f"vec-correct-litform-{eff}-{param}", eff, param, f"{ptype}({good})")
        add(f"vec-correct-array-{eff}-{param}", eff, param, f"[{good}]")
        short = ", ".join(str(0.1 * (i + 1)) for i in range(max(1, width - 1)))
        long = ", ".join(str(0.1 * (i + 1)) for i in range(width + 1))
        add(f"vec-short-litform-{eff}-{param}", eff, param, f"{ptype}({short})")
        add(f"vec-long-litform-{eff}-{param}", eff, param, f"{ptype}({long})")
        add(f"vec-short-array-{eff}-{param}", eff, param, f"[{short}]")
        add(f"vec-long-array-{eff}-{param}", eff, param, f"[{long}]")
        add(f"vec-scalar-{eff}-{param}", eff, param, "0.5")
        add(f"vec-bool-{eff}-{param}", eff, param, "true")
    mat3_effect = None
    for e in catalog:
        for name, p in e["params"].items():
            if p["type"] == "mat3":
                mat3_effect = (e["id"], name)
                break
        if mat3_effect:
            break
    if mat3_effect:
        eff, param = mat3_effect
        nine = ", ".join(str(0.1 * (i + 1)) for i in range(9))
        eight = ", ".join(str(0.1 * (i + 1)) for i in range(8))
        ten = ", ".join(str(0.1 * (i + 1)) for i in range(10))
        add(f"mat3-correct-{eff}", eff, param, f"[{nine}]")
        add(f"mat3-short-{eff}", eff, param, f"[{eight}]")
        add(f"mat3-long-{eff}", eff, param, f"[{ten}]")
        add(f"mat3-scalar-{eff}", eff, param, "0.5")

    # ---- float/int range boundaries + type mismatches. ----
    numeric_targets = [
        ("filter/tint", "alpha", "float"),
        ("filter/dither", "matrixScale", "int"),
        ("classicNoisedeck/lensDistortion", "distortion", "float"),
    ]
    for eff, param, ptype in numeric_targets:
        p = by_id[eff]["params"][param]
        lo, hi = p.get("min"), p.get("max")
        if lo is not None:
            add(f"num-below-min-{eff}-{param}", eff, param, sweep.dsl_number(lo - 1))
            add(f"num-at-min-{eff}-{param}", eff, param, sweep.dsl_number(lo))
        if hi is not None:
            add(f"num-above-max-{eff}-{param}", eff, param, sweep.dsl_number(hi + 1))
            add(f"num-at-max-{eff}-{param}", eff, param, sweep.dsl_number(hi))
        add(f"num-bool-for-{ptype}-{eff}-{param}", eff, param, "true")
        add(f"num-string-for-{ptype}-{eff}-{param}", eff, param, '"3"')
        if ptype == "int":
            add(f"num-fractional-for-int-{eff}-{param}", eff, param, "2.5")

    # ---- boolean: valid + type-mismatched numeric. ----
    bool_targets = [("classicNoisedeck/lensDistortion", "aspectLens")]
    for eff, param in bool_targets:
        add(f"bool-true-{eff}", eff, param, "true")
        add(f"bool-false-{eff}", eff, param, "false")
        add(f"bool-number0-{eff}", eff, param, "0")
        add(f"bool-number1-{eff}", eff, param, "1")

    # ---- enum-like: int-with-choices, member, palette, string-with-choices --
    # by name (bare identifier and dotted), by number (in-range and a huge
    # out-of-range code the authority's enumValue never range-checks), and an
    # unknown name. ----
    enum_targets = [
        ("classicNoisedeck/composite", "blendMode", "int"),
        ("filter/channel", "channel", "member"),
        ("classicNoisedeck/fractal", "palette", "palette"),
        ("filter/text", "justify", "string"),
    ]
    for eff, param, ptype in enum_targets:
        p = by_id[eff]["params"][param]
        choices = [k for k, v in (p.get("choices") or {}).items() if v is not None]
        if not choices:
            continue
        name = choices[0]
        code = p["choices"][name]
        add(f"enum-byname-bare-{eff}-{param}", eff, param, name)
        add(f"enum-byname-dotted-{eff}-{param}", eff, param, f"{param}.{name}")
        add(f"enum-unknown-name-{eff}-{param}", eff, param, "totallyBogusChoiceName")
        is_numeric_code = isinstance(code, (int, float)) and not isinstance(code, bool)
        if is_numeric_code:
            add(f"enum-bynumber-{eff}-{param}", eff, param, sweep.dsl_number(code))
            add(f"enum-bynumber-huge-{eff}-{param}", eff, param, sweep.dsl_number(code + 100000))
            add(f"enum-fractional-{eff}-{param}", eff, param, sweep.dsl_number(code + 0.5))

    # ---- plain string (no choices): valid + type mismatch. ----
    string_targets = [("filter/text", "text")]
    for eff, param in string_targets:
        add(f"string-valid-{eff}", eff, param, '"hello"')
        add(f"string-number-{eff}", eff, param, "42")
        add(f"string-bool-{eff}", eff, param, "true")

    # ---- surface: o0..o7 valid range, o8 out of range (lexer/parser level),
    # "none". ----
    surface_targets = [("classicNoisedeck/composite", "tex")]
    for eff, param in surface_targets:
        if param not in by_id[eff]["params"]:
            continue
        add(f"surface-o1-{eff}", eff, param, "o1")
        add(f"surface-o7-{eff}", eff, param, "o7")
        add(f"surface-o8-outofrange-{eff}", eff, param, "o8")
        add(f"surface-none-{eff}", eff, param, "none")

    # ---- volume/geometry: non-empty string (their only accepted literal
    # form) vs empty string vs number. ----
    vg_targets = [
        ("synth3d/cellularAutomata3d", "source", "volume"),
        ("synth3d/cellularAutomata3d", "geoSource", "geometry"),
    ]
    for eff, param, ptype in vg_targets:
        add(f"{ptype}-valid-{eff}-{param}", eff, param, '"vol0"')
        add(f"{ptype}-empty-{eff}-{param}", eff, param, '""')
        add(f"{ptype}-number-{eff}-{param}", eff, param, "1")


def main() -> int:
    cpu_root = Path(os.environ["NOISEMAKER_CPU_ROOT"]).resolve()
    ledger = Path(os.environ["NOISEMAKER_CPU_AUTHORITY_LEDGER"]).resolve()
    driver = Path(os.environ["NOISEMAKER_DSL_CPU_CASE"]).resolve()
    out_dir = Path(sys.argv[1]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    scratch_root = out_dir / "scratch"
    scratch_root.mkdir(parents=True, exist_ok=True)

    import shutil
    node = shutil.which("node")
    assert node

    catalog = sweep.load_catalog(cpu_root, ledger, out_dir, node)
    by_id = {e["id"]: e for e in catalog}
    build_cases(catalog)

    jobs = []
    for tag, effect_id, param_name, literal in CASES:
        effect = by_id[effect_id]
        args = default_args_with_override(effect, param_name, literal)
        source = wrap(effect, args)
        if tag.startswith("surface-") and literal in ("o1", "o7"):
            # o1/o7 must exist before composite's `tex` param can read them --
            # prepend a write so the case tests the surface-reference literal
            # itself, not an unrelated "read before write" refusal.
            source = f"solid(color: #654321).write({literal})\n" + source
        jobs.append(sweep.Job(
            case_id=tag, effect_id=effect_id, kind="literal_form", source=source,
            width=17, height=11, time=0.25, seed=sweep.stable_uint32(tag),
            note=literal,
        ))

    config = sweep.RunConfig(node=node, driver=str(driver), cpu_root=str(cpu_root),
                              ledger=str(ledger), scratch_root=str(scratch_root),
                              timeout=30.0)
    sweep._init_worker(config)  # noqa: SLF001 - reuse the sweep's own worker globals
    results = []
    for job in jobs:
        results.append(sweep.run_job(vars(job)))

    (out_dir / "results.jsonl").write_text(
        "\n".join(json.dumps(r) for r in results) + "\n", encoding="utf-8")

    from collections import Counter
    counts = Counter(r["classification"] for r in results)
    print(json.dumps(dict(counts), indent=2))
    problems = [r for r in results if r["classification"] in ("divergent", "cpp_refused_only", "harness_error")]
    print(f"\n{len(problems)} case(s) needing attention:\n")
    for r in problems:
        note = next(c[3] for c in CASES if c[0] == r["case_id"])
        print(f"- {r['case_id']} [{r['classification']}] literal={note!r}")
        if "diagnostics" in r:
            print(f"    {r['diagnostics']}")
        if "js_reason" in r:
            print(f"    js: {r['js_reason']}")
        if "cpp_reason" in r:
            print(f"    cpp: {r['cpp_reason']}")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
