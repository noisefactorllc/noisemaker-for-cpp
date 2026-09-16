#!/usr/bin/env python3
"""Parameter/geometry sweep parity gate for noisemaker-for-cpp.

``tests/test_dsl_corpus_parity.py`` renders each admitted corpus effect ONCE,
at 17x11, with every parameter at its declared default. That is a single
point in a huge space and it demonstrably missed real divergences. This tool
renders every effect in the authenticated JS CPU authority's catalog through
BOTH the JS authority runner and the C++ driver many times each, varying
size, render seed, time, and every declared parameter across its domain
(numeric min/max/interior, every enum choice, both booleans, random
vectors/colors including translucent alpha, and generated secondary sources
for surface-typed parameters) -- plus a lower-rate set of chained
generator->filter->mixer programs -- and classifies every single render pair.

Design
------
1. ``dump_catalog.mjs`` authenticates the CPU root through the existing
   ``tools/dsl/corpus_authority.mjs`` trust path (the same one
   ``run_cpu_case.mjs`` and ``generate_executable_corpus.mjs`` use) and dumps
   the effect catalog to JSON once. Nothing here re-implements or bypasses
   that authentication.
2. This file is pure Python from there: it builds N deterministic variants
   per effect (a seeded RNG keyed on the effect id, so reruns with the same
   ``--seed`` reproduce byte-identical DSL programs), renders each variant
   through the JS runner (``tools/benchmark/run_cpu_case.mjs``) and the C++
   driver (via ``tools.benchmark.corpus_lane.record_flags`` -- the exact
   argv-building contract the frozen parity test already uses), and compares
   raw RGBA8 bytes with ``tools.benchmark.exact_compare.compare_rgba8``.
3. Work is farmed out to a process pool. Every completed variant is appended
   to a JSON-Lines results log immediately, so a killed or interrupted run
   can be resumed: rerunning the same ``--out`` directory skips any
   ``case_id`` already present in the log.
4. Both drivers additionally accept an opt-in ``--float32-output`` flag (added
   here) that dumps the pre-quantization RGBA float32 surface behind
   ``to_rgba8()``/``toRgba8()`` -- ``result.surface.data()`` in C++,
   ``result.surface.data`` in JS, both already existed, so this is a raw
   byte dump, not new rendering logic. When both lanes render, this tool
   compares BOTH the quantized RGBA8 bytes and the raw float32 bytes; a
   float32-only divergence (RGBA8 matched, the floats behind it did not) is
   reported distinctly from a plain RGBA8 mismatch.

DSL source generation mirrors ``tools/dsl/generate_executable_corpus.mjs``'s
``sourceFor``/``dslValue``/``defaultArgs`` exactly for the shape of a single
default-valued program, then generalizes it: parameter overrides, generated
secondary sources for surface-typed parameters (wired to a fresh
``solid(color: ...)`` write rather than always the literal ``o0`` the corpus
generator uses), and multi-effect chains.

Known, deliberate scope limits (see the final report for what these mean for
coverage):
- Numeric parameters with neither a declared ``min`` nor ``max`` (16 of 1011
  numeric parameters, e.g. ``paletteMode``, ``stateSize``) are left at their
  default in every variant. Nothing in the catalog gives this tool a safe
  domain to sample for them, and guessing one (e.g. a huge ``stateSize``) risks
  turning a parity question into a resource-exhaustion question.
- Only the JS lane can accept an external texture (via the already-supported
  ``record.seedSurfaces`` -> ``api.Surface.fromRgba8`` path in
  ``run_cpu_case.mjs``): ``filter/text`` and ``synth/media`` get a small
  synthetic checkerboard fed to the JS runner. Neither
  ``noisemaker-dsl-cpu-case`` nor ``noisemaker-render`` has ANY external-image
  input (no CLI flag, no wiring) -- adding real image decoding and texture
  wiring to the C++ engine is new engine capability, not a harness need, so
  this tool does not add it; the C++ side is expected to keep refusing these
  two (correctly reported as ``cpp_refused_only``, not ``both_refused``).
- A chain variant exercises the swept effect plus two deterministically
  chosen helper effects (for the two roles it doesn't itself occupy). A
  divergence or refusal in a chain is reported against the chain (all three
  effect ids), never folded into a single effect's byte-exact tally, because
  attributing a three-effect failure to one participant is a claim this tool
  cannot support.
- Chain variants never wire a surface-typed parameter to a generated
  secondary source (that coverage lives in the single-effect variants only);
  a surface-typed parameter on the swept effect is left at its default inside
  a chain, so a chain program never needs its own extra `search` namespace.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import fnmatch
import hashlib
import json
import os
import random
import re
import shutil
import struct
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LANE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LANE_ROOT))

from tools.benchmark.corpus_lane import record_flags  # noqa: E402
from tools.benchmark.exact_compare import compare_rgba8, format_diagnostics  # noqa: E402

DUMP_CATALOG = LANE_ROOT / "tools/parity/dump_catalog.mjs"
JS_RUNNER = LANE_ROOT / "tools/benchmark/run_cpu_case.mjs"

WIRE = "__WIRE_SURFACE__"

SIZE_POOL: list[tuple[int, int]] = [(1, 1), (17, 11), (97, 61), (64, 64), (128, 37)]
TIME_POOL: list[float] = [0.0, 0.25, 0.999]

ITERATION_CAP = 4
CHAIN_RATE = 0.15
MAX_CHAIN_VARIANTS = 4

CLASSIFICATIONS = (
    "byte_exact", "divergent", "both_refused", "cpp_refused_only", "timeout",
)


# ---------------------------------------------------------------------------
# Deterministic hashing / seeding helpers
# ---------------------------------------------------------------------------

def stable_uint32(label: str) -> int:
    value = int(hashlib.sha256(label.encode("utf-8")).hexdigest()[:8], 16) & 0xFFFFFFFF
    return value if value != 0 else 1


def rng_for(*parts: str) -> random.Random:
    return random.Random(stable_uint32(":".join(parts)))


# ---------------------------------------------------------------------------
# DSL value / source generation (ports generate_executable_corpus.mjs's
# sourceFor/dslValue/defaultArgs, generalized to accept per-parameter
# overrides and surface wiring).
# ---------------------------------------------------------------------------

def _clamp255(component: float) -> int:
    return max(0, min(255, round(component * 255)))


def color_hex(channels: list[float]) -> str:
    values = list(channels) if len(channels) == 4 else [*channels, 1]
    hexstr = "".join(f"{_clamp255(c):02x}" for c in values[:3])
    if len(values) == 4 and values[3] != 1:
        hexstr += f"{_clamp255(values[3]):02x}"
    return f"#{hexstr}"


def dsl_number(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer() and abs(value) < 1e15:
            return str(int(value))
        return repr(value)
    return str(value)


def dsl_value(param: dict, value: Any) -> str:
    ptype = param.get("type")
    if ptype == "color":
        if isinstance(value, (list, tuple)):
            return color_hex(list(value))
        return str(value)
    if ptype == "string":
        return json.dumps(value)
    if ptype in ("bool", "boolean"):
        return "true" if value else "false"
    if ptype == "surface":
        if value is None or value == "none":
            return "none"
        return str(value)  # a surface name, e.g. "o1", passed through raw
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(dsl_number(v) for v in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return dsl_number(value)
    return str(value)


def build_args(effect: dict, overrides: dict[str, Any]) -> str:
    parts = []
    for name, param in effect["params"].items():
        value = overrides[name] if name in overrides else param.get("default")
        parts.append(f"{name}: {dsl_value(param, value)}")
    return ", ".join(parts)


def is_iteration_like(name: str, param: dict) -> bool:
    return bool(re.search("iteration", name, re.IGNORECASE)) or param.get("cpuOnly") is True


# ---------------------------------------------------------------------------
# Per-parameter candidate lists ("declared domain" sampling).
# ---------------------------------------------------------------------------

def numeric_candidates(param: dict, count: int, rng: random.Random, name: str) -> list[Any]:
    lo, hi = param.get("min"), param.get("max")
    if lo is None or hi is None:
        # No declared domain: leave it at its default everywhere. See the
        # module docstring's "Known, deliberate scope limits".
        return [param.get("default")] * count
    is_int = param["type"] == "int" and not param.get("choices")
    if is_iteration_like(name, param):
        cap = ITERATION_CAP if is_int else float(ITERATION_CAP)
        hi = min(hi, cap)
        if hi < lo:
            hi = lo
    values = []
    for i in range(count):
        slot = i % 4
        if slot == 0:
            v = lo
        elif slot == 1:
            v = hi
        else:
            v = rng.randint(int(lo), int(hi)) if is_int else rng.uniform(lo, hi)
        values.append(v)
    return values


def enum_candidates(param: dict, count: int) -> list[Any]:
    choices = [v for v in param.get("choices", {}).values() if v is not None]
    if not choices:
        return [param.get("default")] * count
    return [choices[i % len(choices)] for i in range(count)]


def vector_candidates(param: dict, count: int, rng: random.Random) -> list[list[float]]:
    width = {"vec2": 2, "vec3": 3, "vec4": 4, "mat3": 9}[param["type"]]
    default = param.get("default")
    base = list(default) if isinstance(default, list) and len(default) == width else [0.0] * width
    out = []
    for _ in range(count):
        vec = []
        for component in base:
            spread = abs(component) * 2 + 1
            vec.append(rng.uniform(component - spread, component + spread))
        out.append(vec)
    return out


def color_candidates(count: int, rng: random.Random) -> list[list[float]]:
    out = []
    for i in range(count):
        rgb = [rng.random(), rng.random(), rng.random()]
        alpha = 0.5 if i == 0 else round(rng.uniform(0.05, 1.0), 4)
        out.append(rgb + [alpha])
    return out


def build_candidates(name: str, param: dict, count: int, rng: random.Random) -> list[Any]:
    ptype = param.get("type")
    if ptype in ("bool", "boolean"):
        return [i % 2 == 0 for i in range(count)]
    if ptype in ("enum", "member", "palette"):
        return enum_candidates(param, count)
    if ptype == "int" and param.get("choices"):
        return enum_candidates(param, count)
    if ptype == "string":
        if param.get("choices"):
            return enum_candidates(param, count)
        return [param.get("default")] * count
    if ptype in ("int", "float"):
        return numeric_candidates(param, count, rng, name)
    if ptype == "color":
        return color_candidates(count, rng)
    if ptype in ("vec2", "vec3", "vec4", "mat3"):
        return vector_candidates(param, count, rng)
    if ptype == "surface":
        return [None if i % 2 == 0 else WIRE for i in range(count)]
    if ptype in ("volume", "geometry"):
        return [param.get("default")] * count
    return [param.get("default")] * count


# ---------------------------------------------------------------------------
# Source assembly
# ---------------------------------------------------------------------------


# The DSL admits only o0 through o7 ("Surface reference must be o0 through
# o7"). mixer/mashup declares 9 surface-typed parameters and synth/remap
# declares 8 -- more than fit. The authority's own CLI
# (bin/noisemaker-cpu.js effectProgram) hits the identical ceiling and caps
# at 6 wired sources (`.slice(0, 6)`); this mirrors that cap exactly rather
# than inventing a different one.
MAX_WIRED_SURFACES = 6


def resolve_surface_overrides(effect: dict, overrides: dict[str, Any], aux_rng: random.Random) -> tuple[dict[str, Any], list[str], set[str]]:
    """Replaces WIRE sentinels with real surface names + preamble statements.

    A WIRE past ``MAX_WIRED_SURFACES`` falls back to ``None`` (the DSL
    ``none``) rather than allocating oN past the o0-o7 ceiling.
    """
    resolved: dict[str, Any] = {}
    aux_lines: list[str] = []
    namespaces: set[str] = set()
    next_surface = 1
    for name, value in overrides.items():
        if value == WIRE and next_surface <= MAX_WIRED_SURFACES:
            surface = f"o{next_surface}"
            next_surface += 1
            color = color_hex([aux_rng.random(), aux_rng.random(), aux_rng.random()])
            aux_lines.append(f"solid(color: {color}).write({surface})")
            namespaces.add("synth")
            resolved[name] = surface
        elif value == WIRE:
            resolved[name] = None
        else:
            resolved[name] = value
    return resolved, aux_lines, namespaces


def _dedupe_namespaces(primary: list[str], extra: set[str]) -> list[str]:
    ordered = list(primary)
    for ns in sorted(extra):
        if ns not in ordered:
            ordered.append(ns)
    return ordered


def _assemble(namespaces: list[str], aux_lines: list[str], chain: str) -> str:
    lines = [f"search {', '.join(namespaces)}"]
    lines.extend(aux_lines)
    lines.append(f"{chain}.write(o0)")
    lines.append("render(o0)")
    return "\n".join(lines) + "\n"


def source_for_single(effect: dict, overrides: dict[str, Any], aux_rng: random.Random) -> str:
    """Builds one complete DSL program exercising ``effect`` with ``overrides``.

    Dispatch mirrors noisemaker-for-cpu's own reference CLI
    (``bin/noisemaker-cpu.js``'s ``effectProgram``) exactly: a plain
    image-domain generator/filter/mixer gets the generic treatment (a
    ``solid()`` base for non-generators, surface-typed parameters wired to
    fresh generated sources); a particle-consuming effect
    (``needsParticlePipeline``), a loop-begin/loop-end marker, or a
    volume-domain effect (volume-generator/-filter/-renderer) instead gets
    the exact wiring the authority CLI uses to make that class of effect
    reachable at all -- a naive `.write(oN)` after any of these produces a
    guaranteed, uninformative refusal on BOTH lanes (confirmed by the first
    full sweep) rather than a real parity signal.
    """
    resolved, aux_lines, namespaces = resolve_surface_overrides(effect, overrides, aux_rng)
    args = build_args(effect, resolved)
    call = f"{effect['func']}({args})"

    if effect.get("needsParticlePipeline"):
        ns = _dedupe_namespaces(["points", "render", "synth"], namespaces | {effect["namespace"]})
        return _assemble(ns, aux_lines, f"solid().pointsEmit(stateSize: x64).{call}")

    if effect["domain"] in ("loop-begin", "loop-end"):
        ns = _dedupe_namespaces(["render", "synth"], namespaces | {effect["namespace"]})
        if effect["domain"] == "loop-begin":
            chain = f"solid().{call}.loopEnd()"
        else:
            chain = f"solid().loopBegin(iterationCount: 1).{call}"
        return _assemble(ns, aux_lines, chain)

    if effect["domain"].startswith("volume-"):
        ns = _dedupe_namespaces(["synth3d", "filter3d", "render"], namespaces)
        volume_size = (effect["params"].get("volumeSize") or {}).get("default", 16)
        if effect["domain"] == "volume-generator":
            chain = f"{call}.render3d()"
        elif effect["domain"] == "volume-filter":
            chain = f"noise3d(volumeSize: {dsl_number(volume_size)}).{call}.render3d()"
        else:  # volume-renderer
            chain = f"noise3d(volumeSize: {dsl_number(volume_size)}).{call}"
        return _assemble(ns, aux_lines, chain)

    namespaces.add(effect["namespace"])
    if effect["kind"] == "generator":
        chain = call
    else:
        chain = f"solid(color: #3a7).{call}"
        namespaces.add("synth")
    ordered = [effect["namespace"]] + sorted(n for n in namespaces if n != effect["namespace"])
    return _assemble(ordered, aux_lines, chain)


def source_for_chain(x_effect: dict, gen: dict, filt: dict, mix: dict, x_overrides: dict[str, Any]) -> str:
    def call_for(effect: dict) -> str:
        overrides = x_overrides if effect["id"] == x_effect["id"] else {}
        return f"{effect['func']}({build_args(effect, overrides)})"

    namespaces: list[str] = []
    for e in (gen, filt, mix):
        if e["namespace"] not in namespaces:
            namespaces.append(e["namespace"])
    chain = f"{call_for(gen)}.{call_for(filt)}.{call_for(mix)}"
    lines = [f"search {', '.join(namespaces)}", f"{chain}.write(o0)", "render(o0)"]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Variant / job construction
# ---------------------------------------------------------------------------

@dataclass
class Job:
    case_id: str
    effect_id: str
    kind: str  # 'default' | 'sampled' | 'chain'
    source: str
    width: int
    height: int
    time: float
    seed: int
    chain_effects: list[str] = field(default_factory=list)
    note: str = ""
    external_texture: str | None = None


def sanitize(effect_id: str) -> str:
    return effect_id.replace("/", "__")


# A small deterministic checkerboard fed to effects declaring
# ``externalTexture`` (filter/text, synth/media). Neither driver accepts a
# real image file (no CLI flag exists on either side for one -- see the
# module docstring); this uses the ALREADY-SUPPORTED `record.seedSurfaces`
# path in run_cpu_case.mjs (api.Surface.fromRgba8) so the JS lane renders
# instead of refusing. The C++ driver has no equivalent input at all, so it
# still refuses -- correctly reclassifying these two effects from
# both_refused (misleadingly implies neither lane can do this) to
# cpp_refused_only (the true shape: JS can given an image, C++ cannot accept
# one at all).
_EXTERNAL_TEXTURE_SIZE = 4


def synthetic_texture_rgba8_hex(size: int = _EXTERNAL_TEXTURE_SIZE) -> str:
    pixels = bytearray()
    for y in range(size):
        for x in range(size):
            v = 235 if (x + y) % 2 == 0 else 40
            pixels += bytes([v, v, v, 255])
    return pixels.hex()


def build_single_jobs(effect: dict, n_variants: int, global_seed: int) -> list[Job]:
    jobs: list[Job] = []
    eff_id = effect["id"]
    external_texture = effect.get("externalTexture")
    default_seed = stable_uint32(f"{global_seed}:{eff_id}#default")
    default_source = source_for_single(effect, {}, rng_for(str(global_seed), eff_id, "aux#default"))
    jobs.append(Job(
        case_id=f"{sanitize(eff_id)}__default", effect_id=eff_id, kind="default",
        source=default_source, width=17, height=11, time=0.25, seed=default_seed,
        note="all parameters at declared default; the corpus's own baseline point",
        external_texture=external_texture,
    ))
    remaining = n_variants - 1
    if remaining <= 0:
        return jobs
    candidate_map: dict[str, list[Any]] = {}
    for name, param in effect["params"].items():
        param_rng = rng_for(str(global_seed), eff_id, "param", name)
        candidate_map[name] = build_candidates(name, param, remaining, param_rng)
    for i in range(remaining):
        overrides = {name: values[i] for name, values in candidate_map.items()}
        aux_rng = rng_for(str(global_seed), eff_id, "aux", str(i))
        source = source_for_single(effect, overrides, aux_rng)
        size = SIZE_POOL[i % len(SIZE_POOL)]
        t = TIME_POOL[i % len(TIME_POOL)]
        seed = stable_uint32(f"{global_seed}:{eff_id}#{i}")
        jobs.append(Job(
            case_id=f"{sanitize(eff_id)}__v{i}", effect_id=eff_id, kind="sampled",
            source=source, width=size[0], height=size[1], time=t, seed=seed,
            external_texture=external_texture,
        ))
    return jobs


def build_chain_jobs(effect: dict, by_kind: dict[str, list[dict]], n_variants: int, global_seed: int) -> list[Job]:
    if effect["domain"] != "image" or effect.get("externalTexture") or effect.get("needsParticlePipeline"):
        return []
    count = max(1, min(MAX_CHAIN_VARIANTS, round(n_variants * CHAIN_RATE)))
    eff_id = effect["id"]
    jobs: list[Job] = []
    for ci in range(count):
        rng = rng_for(str(global_seed), eff_id, "chain", str(ci))
        roles: dict[str, dict] = {}
        for role in ("generator", "filter", "mixer"):
            if effect["kind"] == role:
                roles[role] = effect
                continue
            pool = [e for e in by_kind[role] if e["id"] != eff_id]
            if not pool:
                pool = by_kind[role]
            roles[role] = pool[rng.randrange(len(pool))]
        overrides: dict[str, Any] = {}
        for name, param in effect["params"].items():
            candidates = build_candidates(name, param, 1, rng_for(str(global_seed), eff_id, "chainparam", str(ci), name))
            value = candidates[0]
            if value == WIRE:
                value = None  # chains skip surface wiring; keep it simple and legal
            overrides[name] = value
        source = source_for_chain(effect, roles["generator"], roles["filter"], roles["mixer"], overrides)
        size = SIZE_POOL[ci % len(SIZE_POOL)]
        t = TIME_POOL[ci % len(TIME_POOL)]
        seed = stable_uint32(f"{global_seed}:{eff_id}#chain{ci}")
        jobs.append(Job(
            case_id=f"{sanitize(eff_id)}__chain{ci}", effect_id=eff_id, kind="chain",
            source=source, width=size[0], height=size[1], time=t, seed=seed,
            chain_effects=[roles["generator"]["id"], roles["filter"]["id"], roles["mixer"]["id"]],
        ))
    return jobs


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

@dataclass
class RunConfig:
    node: str
    driver: str
    cpu_root: str
    ledger: str
    scratch_root: str
    timeout: float


_CONFIG: RunConfig | None = None


def _init_worker(config: RunConfig) -> None:
    global _CONFIG
    _CONFIG = config


def _run_proc(cmd: list[str], timeout: float) -> tuple[int, str, str, bool, float]:
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr, False, time.monotonic() - start
    except subprocess.TimeoutExpired as error:
        return -1, error.stdout or "", error.stderr or "", True, time.monotonic() - start


def extract_js_reason(stderr: str) -> str:
    """Best-effort human reason from an uncaught Node exception.

    ``run_cpu_case.mjs`` has no structured refusal document (unlike the C++
    driver's JSON refusal record): a rejected program is an uncaught
    exception, and Node prints a multi-line stack trace ending in a
    ``Node.js vX.Y.Z`` trailer. Neither the first line (a ``file://`` path)
    nor the last line (that trailer) is the message; the message is the
    first line that looks like ``SomeError: ...``.
    """
    lines = [line for line in stderr.splitlines() if line.strip()]
    for line in lines:
        if re.match(r"^\w*Error:", line.strip()):
            return line.strip()[:300]
    return lines[0].strip()[:300] if lines else ""


def compare_float32(width: int, height: int, expected: bytes, actual: bytes) -> dict[str, Any]:
    """Byte-exact comparison of the pre-quantization RGBA float32 surface.

    Deliberately separate from ``tools.benchmark.exact_compare.compare_rgba8``
    (which assumes 1 byte/channel) rather than widening that shared,
    frozen-lane function's contract for a harness-only need.
    """
    expected_hash = hashlib.sha256(expected).hexdigest()
    actual_hash = hashlib.sha256(actual).hexdigest()
    required = width * height * 4 * 4
    if len(expected) != required or len(actual) != required:
        return {"ok": False, "expectedLength": len(expected), "actualLength": len(actual),
                "expectedSha256": expected_hash, "actualSha256": actual_hash,
                "mismatchCount": 0, "firstMismatch": None}
    mismatch_count = 0
    first = None
    for offset in range(0, required, 4):
        if expected[offset:offset + 4] != actual[offset:offset + 4]:
            mismatch_count += 1
            if first is None:
                float_index, channel = divmod(offset // 4, 4)
                pixel, ch = float_index, channel
                (ev,) = struct.unpack("<f", expected[offset:offset + 4])
                (av,) = struct.unpack("<f", actual[offset:offset + 4])
                first = {"x": pixel % width, "y": pixel // width, "channel": "RGBA"[ch],
                         "expected": ev, "actual": av}
    ok = mismatch_count == 0 and expected_hash == actual_hash
    return {"ok": ok, "expectedLength": len(expected), "actualLength": len(actual),
            "expectedSha256": expected_hash, "actualSha256": actual_hash,
            "mismatchCount": mismatch_count, "firstMismatch": first}


def _cpp_detail(stdout: str) -> tuple[str, str]:
    try:
        parsed = json.loads(stdout or "{}")
        return parsed.get("code", ""), parsed.get("detail", "")
    except json.JSONDecodeError:
        return "", stdout.strip()[:300]


def run_job(job_dict: dict) -> dict:
    assert _CONFIG is not None
    config = _CONFIG
    job = Job(**job_dict)
    scratch = Path(config.scratch_root) / job.case_id
    scratch.mkdir(parents=True, exist_ok=True)
    try:
        source_path = scratch / "case.dsl"
        source_path.write_text(job.source, encoding="utf-8")
        source_sha256 = hashlib.sha256(job.source.encode("utf-8")).hexdigest()
        options = {
            "width": job.width, "height": job.height, "time": job.time,
            "frame": 0, "seed": job.seed, "oneShot": "ready", "renderScale": 1,
        }
        record = {
            "recordKind": "admitted", "id": job.case_id, "source": job.source,
            "sourceSha256": source_sha256, "options": options, "plan": None,
        }
        if job.external_texture:
            # JS-only: run_cpp_case.cpp has no external-texture input at all
            # (no CLI flag, no wiring), so the C++ side still refuses. This
            # only changes the JS side from a matching refusal to a real
            # render, which reclassifies the case as cpp_refused_only
            # (accurate: JS can do this given an image, C++ cannot accept
            # one) instead of both_refused (implies neither can). Distinct
            # from `seedSurfaces` (named oN pre-seeding): externalTexture-
            # declared effects read `renderOptions.externalTextures` instead
            # (see run_cpu_case.mjs).
            record["externalTextures"] = [{
                "name": job.external_texture, "width": _EXTERNAL_TEXTURE_SIZE,
                "height": _EXTERNAL_TEXTURE_SIZE, "rgba8": synthetic_texture_rgba8_hex(),
            }]
        case_path = scratch / "case.json"
        case_path.write_text(json.dumps(record), encoding="utf-8")

        js_raw, js_meta = scratch / "js.rgba8", scratch / "js.json"
        js_f32 = scratch / "js.f32"
        js_cmd = [
            config.node, str(JS_RUNNER), "--cpu-root", config.cpu_root,
            "--authority-ledger", config.ledger, "--case", str(case_path),
            "--rgba8-output", str(js_raw), "--metadata-output", str(js_meta),
            "--float32-output", str(js_f32),
        ]
        js_rc, js_out, js_err, js_timed_out, js_elapsed = _run_proc(js_cmd, config.timeout)

        cpp_raw, cpp_meta = scratch / "cpp.rgba8", scratch / "cpp.json"
        cpp_f32 = scratch / "cpp.f32"
        cpp_cmd = [config.driver, *record_flags(record, source_path),
                   "--rgba8-output", str(cpp_raw), "--metadata-output", str(cpp_meta),
                   "--float32-output", str(cpp_f32)]
        cpp_rc, cpp_out, cpp_err, cpp_timed_out, cpp_elapsed = _run_proc(cpp_cmd, config.timeout)

        result: dict[str, Any] = {
            "case_id": job.case_id, "effect_id": job.effect_id, "kind": job.kind,
            "chain_effects": job.chain_effects, "note": job.note,
            "width": job.width, "height": job.height, "time": job.time, "seed": job.seed,
            "js_returncode": js_rc, "cpp_returncode": cpp_rc,
            "js_elapsed_s": round(js_elapsed, 3), "cpp_elapsed_s": round(cpp_elapsed, 3),
        }

        if js_timed_out or cpp_timed_out:
            result["classification"] = "timeout"
            result["js_timed_out"] = js_timed_out
            result["cpp_timed_out"] = cpp_timed_out
            return result

        js_ok = js_rc == 0
        cpp_ok = cpp_rc == 0
        cpp_code, cpp_detail = _cpp_detail(cpp_out)

        if not js_ok and not cpp_ok:
            result["classification"] = "both_refused"
            result["js_reason"] = extract_js_reason(js_err)
            result["cpp_code"] = cpp_code
            result["cpp_reason"] = cpp_detail
            return result

        if not js_ok and cpp_ok:
            result["classification"] = "divergent"
            result["divergence_reason"] = "authority refused this program but the executor rendered bytes"
            result["js_reason"] = extract_js_reason(js_err)
            return result

        if js_ok and not cpp_ok:
            result["classification"] = "cpp_refused_only"
            result["cpp_code"] = cpp_code
            result["cpp_reason"] = cpp_detail
            return result

        diff = compare_rgba8(job.width, job.height, js_raw.read_bytes(), cpp_raw.read_bytes())
        float_diff = None
        if js_f32.exists() and cpp_f32.exists():
            float_diff = compare_float32(job.width, job.height, js_f32.read_bytes(), cpp_f32.read_bytes())
            result["float32_ok"] = float_diff["ok"]

        result["classification"] = "byte_exact" if diff["ok"] and (float_diff is None or float_diff["ok"]) else "divergent"
        if not diff["ok"]:
            result["diagnostics"] = format_diagnostics(diff)
            result["first_mismatch"] = diff.get("firstMismatch")
            result["mismatch_count"] = diff.get("mismatchCount")
        elif float_diff is not None and not float_diff["ok"]:
            # The quantized RGBA8 output matched exactly, but the
            # pre-quantization float32 surface behind it did not -- a real,
            # more sensitive divergence signal that RGBA8 rounding hid.
            result["diagnostics"] = (
                f"rgba8 byte-exact; float32 surface diverges: "
                f"mismatchCount={float_diff['mismatchCount']} "
                f"firstMismatch={float_diff['firstMismatch']} "
                f"expectedSha256={float_diff['expectedSha256']} actualSha256={float_diff['actualSha256']}"
            )
            result["first_mismatch"] = float_diff.get("firstMismatch")
            result["mismatch_count"] = float_diff.get("mismatchCount")
            result["divergence_reason"] = "rgba8 matched; float32 pre-quantization surface differs"
        return result
    except Exception as error:  # noqa: BLE001 - a worker-side crash must still show up as a result row
        return {
            "case_id": job.case_id, "effect_id": job.effect_id, "kind": job.kind,
            "chain_effects": job.chain_effects, "classification": "harness_error",
            "error": f"{error}\n{traceback.format_exc()[-1000:]}",
        }
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


# ---------------------------------------------------------------------------
# Aggregation / reporting
# ---------------------------------------------------------------------------

def load_existing(results_path: Path) -> dict[str, dict]:
    existing: dict[str, dict] = {}
    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            existing[row["case_id"]] = row
    return existing


def write_summary(all_rows: list[dict], out_dir: Path, meta: dict) -> None:
    by_effect: dict[str, list[dict]] = {}
    chains: list[dict] = []
    for row in all_rows:
        if row["kind"] == "chain":
            chains.append(row)
        else:
            by_effect.setdefault(row["effect_id"], []).append(row)

    totals = {c: 0 for c in CLASSIFICATIONS}
    totals["harness_error"] = 0
    for row in all_rows:
        totals[row["classification"]] = totals.get(row["classification"], 0) + 1

    fully_exact: list[str] = []
    any_divergent: dict[str, list[dict]] = {}
    cpp_refused_effects: dict[str, list[dict]] = {}
    both_refused_effects: dict[str, list[dict]] = {}
    timeout_effects: dict[str, list[dict]] = {}

    for effect_id, rows in sorted(by_effect.items()):
        classes = {row["classification"] for row in rows}
        if classes == {"byte_exact"}:
            fully_exact.append(effect_id)
            continue
        if "divergent" in classes:
            any_divergent[effect_id] = [r for r in rows if r["classification"] == "divergent"]
        if "cpp_refused_only" in classes:
            cpp_refused_effects[effect_id] = [r for r in rows if r["classification"] == "cpp_refused_only"]
        if "both_refused" in classes:
            both_refused_effects[effect_id] = [r for r in rows if r["classification"] == "both_refused"]
        if "timeout" in classes:
            timeout_effects[effect_id] = [r for r in rows if r["classification"] == "timeout"]

    results = {
        "meta": meta,
        "totals": totals,
        "effect_count": len(by_effect),
        "fully_byte_exact_effect_count": len(fully_exact),
        "fully_byte_exact_effects": sorted(fully_exact),
        "divergent_effects": {k: v for k, v in sorted(any_divergent.items())},
        "cpp_refused_effects": {k: [r["cpp_reason"] for r in v] for k, v in sorted(cpp_refused_effects.items())},
        "both_refused_effects": {k: [{"js": r.get("js_reason"), "cpp": r.get("cpp_reason")} for r in v] for k, v in sorted(both_refused_effects.items())},
        "timeout_effects": sorted(timeout_effects.keys()),
        "chain_totals": {c: sum(1 for r in chains if r["classification"] == c) for c in CLASSIFICATIONS},
        "chain_divergent": [r for r in chains if r["classification"] == "divergent"],
        "chain_refused": [r for r in chains if r["classification"] in ("both_refused", "cpp_refused_only")],
    }
    (out_dir / "results.json").write_text(json.dumps(results, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    lines = []
    lines.append("# noisemaker-for-cpp DSL parameter/geometry sweep")
    lines.append("")
    lines.append(f"Generated: {meta.get('generated_at')}")
    lines.append(f"Effects swept: {results['effect_count']} / variants+chains: {len(all_rows)}")
    lines.append(f"Global seed: {meta.get('seed')}  Variants/effect: {meta.get('variants')}")
    lines.append("")
    lines.append("Comparison covers both RGBA8 (quantized) and float32 (pre-quantization surface) "
                 "bytes, via an additive `--float32-output` flag added to both drivers for this sweep. "
                 "A case is `byte_exact` only if both matched; a float32-only divergence (RGBA8 matched, "
                 "the floats behind it did not) is called out distinctly in its diagnostics.")
    lines.append("")
    lines.append("## Totals (single-effect variants, all effects)")
    lines.append("")
    for c in CLASSIFICATIONS:
        lines.append(f"- {c}: {totals.get(c, 0)}")
    if totals.get("harness_error"):
        lines.append(f"- harness_error: {totals['harness_error']}")
    lines.append("")
    lines.append(f"## Effects fully byte-exact across all their variants: {len(fully_exact)} / {results['effect_count']}")
    lines.append("")
    lines.append(", ".join(fully_exact) if fully_exact else "(none)")
    lines.append("")
    lines.append(f"## Effects with any divergence: {len(any_divergent)}")
    lines.append("")
    for effect_id, rows in sorted(any_divergent.items()):
        first = rows[0]
        lines.append(f"### {effect_id}")
        lines.append(f"- case `{first['case_id']}` ({first['width']}x{first['height']}, time={first['time']}, seed={first['seed']})")
        if "diagnostics" in first:
            lines.append(f"  - {first['diagnostics']}")
        else:
            lines.append(f"  - {first.get('divergence_reason', '')}")
        if len(rows) > 1:
            lines.append(f"  - ({len(rows)} divergent variants total for this effect)")
        lines.append("")
    lines.append(f"## Effects refused by C++ only (JS authority rendered): {len(cpp_refused_effects)}")
    lines.append("")
    for effect_id, rows in sorted(cpp_refused_effects.items()):
        lines.append(f"- {effect_id}: {rows[0].get('cpp_reason', '')!r}")
    lines.append("")
    lines.append(f"## Effects refused by BOTH lanes on every observed variant: {len(both_refused_effects)}")
    lines.append("")
    for effect_id, rows in sorted(both_refused_effects.items()):
        lines.append(f"- {effect_id}: cpp={rows[0].get('cpp_reason', '')!r} js={rows[0].get('js_reason', '')!r}")
    lines.append("")
    lines.append(f"## Timeouts: {len(timeout_effects)} effects had at least one variant exceed the per-case limit")
    lines.append("")
    lines.append(", ".join(sorted(timeout_effects.keys())) if timeout_effects else "(none)")
    lines.append("")
    lines.append(f"## Chained (generator -> filter -> mixer) programs: {len(chains)} run")
    lines.append("")
    for c in CLASSIFICATIONS:
        lines.append(f"- {c}: {results['chain_totals'].get(c, 0)}")
    if results["chain_divergent"]:
        lines.append("")
        lines.append("Divergent chains (all participating effect ids shown; not attributed to a single effect):")
        for row in results["chain_divergent"][:20]:
            lines.append(f"- {row['case_id']}: {row['chain_effects']}")
    lines.append("")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def load_catalog(cpu_root: Path, ledger: Path, out_dir: Path, node: str) -> list[dict]:
    catalog_path = out_dir / "catalog.json"
    subprocess.run(
        [node, str(DUMP_CATALOG), "--cpu-root", str(cpu_root), "--authority-ledger", str(ledger),
         "--output", str(catalog_path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(catalog_path.read_text(encoding="utf-8"))["effects"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu-root", default=os.environ.get("NOISEMAKER_CPU_ROOT"))
    parser.add_argument("--authority-ledger", default=os.environ.get("NOISEMAKER_CPU_AUTHORITY_LEDGER"))
    parser.add_argument("--cpp-driver", default=os.environ.get("NOISEMAKER_DSL_CPU_CASE"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--effects", default=None, help="comma-separated effect ids or glob patterns")
    parser.add_argument("--variants", type=int, default=24)
    parser.add_argument("--seed", type=int, default=20260916)
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4)))
    parser.add_argument("--max-seconds-per-case", type=float, default=45.0)
    parser.add_argument("--no-chains", action="store_true")
    parser.add_argument("--force", action="store_true", help="ignore existing results and rerun everything")
    args = parser.parse_args()

    if not args.cpu_root:
        parser.error("--cpu-root (or NOISEMAKER_CPU_ROOT) is required")
    if not args.cpp_driver:
        parser.error("--cpp-driver (or NOISEMAKER_DSL_CPU_CASE) is required")
    cpu_root = Path(args.cpu_root).resolve()
    driver = Path(args.cpp_driver).resolve()
    ledger = Path(args.authority_ledger).resolve() if args.authority_ledger else Path(f"{cpu_root}.ledger.sha256")
    if not ledger.is_file():
        parser.error(f"authority ledger not found: {ledger} (pass --authority-ledger explicitly)")
    node = shutil.which("node")
    if not node:
        parser.error("node is required")

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    scratch_root = out_dir / "scratch"
    scratch_root.mkdir(parents=True, exist_ok=True)

    full_catalog = load_catalog(cpu_root, ledger, out_dir, node)
    effects = full_catalog
    if args.effects:
        patterns = [p.strip() for p in args.effects.split(",") if p.strip()]
        effects = [e for e in full_catalog if any(fnmatch.fnmatch(e["id"], p) or e["id"] == p for p in patterns)]
    if not effects:
        parser.error("no effects matched --effects")

    # Chain helper pools always come from the FULL catalog, even when
    # --effects narrows the sweep target list, so a filtered run still picks
    # realistic chain partners rather than being limited to the filter.
    by_kind: dict[str, list[dict]] = {"generator": [], "filter": [], "mixer": []}
    for e in full_catalog:
        if (e.get("domain") == "image" and not e.get("externalTexture")
                and not e.get("needsParticlePipeline") and e["kind"] in by_kind):
            by_kind[e["kind"]].append(e)

    jobs: list[Job] = []
    for effect in effects:
        jobs.extend(build_single_jobs(effect, args.variants, args.seed))
        if not args.no_chains:
            jobs.extend(build_chain_jobs(effect, by_kind, args.variants, args.seed))

    results_path = out_dir / "results.jsonl"
    existing = {} if args.force else load_existing(results_path)
    pending = [j for j in jobs if j.case_id not in existing]

    print(f"[sweep] {len(effects)} effects, {len(jobs)} total cases "
          f"({len(existing)} already done, {len(pending)} to run), workers={args.workers}",
          file=sys.stderr)

    config = RunConfig(node=node, driver=str(driver), cpu_root=str(cpu_root), ledger=str(ledger),
                       scratch_root=str(scratch_root), timeout=args.max_seconds_per_case)

    mode = "a" if not args.force and results_path.exists() else "w"
    started = time.monotonic()
    completed = 0
    with open(results_path, mode, encoding="utf-8") as sink:
        if pending:
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=args.workers, initializer=_init_worker, initargs=(config,),
            ) as pool:
                for result in pool.map(run_job, [vars(j) for j in pending], chunksize=1):
                    sink.write(json.dumps(result) + "\n")
                    sink.flush()
                    completed += 1
                    if completed % 200 == 0 or completed == len(pending):
                        elapsed = time.monotonic() - started
                        print(f"[sweep] {completed}/{len(pending)} done ({elapsed:.1f}s elapsed)", file=sys.stderr)

    all_rows = list(load_existing(results_path).values())
    meta = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "seed": args.seed, "variants": args.variants, "effect_count_requested": len(effects),
        "cpu_root": str(cpu_root), "cpp_driver": str(driver),
        "elapsed_seconds": round(time.monotonic() - started, 1),
    }
    write_summary(all_rows, out_dir, meta)
    shutil.rmtree(scratch_root, ignore_errors=True)
    print(f"[sweep] wrote {out_dir / 'results.json'} and {out_dir / 'summary.md'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
