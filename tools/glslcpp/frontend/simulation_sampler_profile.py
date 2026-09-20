"""Exact borrowed-sampler helper ABI profile for simulation shaders.

Authenticates the four simulation fragment programs whose interpolation and
filtering helpers take immutable ``sampler2D`` parameters:
- ``synth/cellularAutomata:ca``
- ``synth/mnca:mnca``
- ``synth/reactionDiffusion:rd``
- ``synth/reactionDiffusion:rdFb``

In each shader, the helper functions (e.g. ``quadratic``, ``bicubic``,
``catmullRom3x3``, ``catmullRom4x4``, or ``lp``) accept a borrowed texture
parameter which is emitted as ``const Surface&`` in C++. Inside each helper,
every reference to the sampler parameter is strictly consumed as the first
argument of ``texture(...)`` with zero escapes, writes, or arithmetic. At every
call site in ``main()``, the argument passed is an authenticated uniform sampler
(``fbTex`` or ``bufTex``).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .typed_ir import TypedExpression, TypedFunction, TypedProgram, TypedStatement


PROFILE = "simulation-sampler-parameters-v1"
CA_KEY = "synth/cellularAutomata:ca"
MNCA_KEY = "synth/mnca:mnca"
RD_KEY = "synth/reactionDiffusion:rd"
RD_FB_KEY = "synth/reactionDiffusion:rdFb"
SIMULATION_SAMPLER_KEYS = frozenset({CA_KEY, MNCA_KEY, RD_KEY, RD_FB_KEY})

_PROFILES = {
    CA_KEY: {
        "raw_bytes": 11253,
        "raw_sha256": "147eb021eb138adc47149edf9440b94e8c1128d2a35dfb236a9a76f091397e15",
        "norm_bytes": 9097,
        "norm_sha256": "53807e631ef4650c5aeb4e1d369b939b034fcccee146029caa4d9aa93ab7684e",
        "functions_sha256": "3c02e636665a0384be2e838bff2c74fcb0484b7e54398cb10c19af40a80f84ec",
        "whole_sha256": "b7aa6e3670a5fc300c05a97d932e50a6d35c0ea0577d8da0c2391d7572176cc5",
        "interface_sha256": "9829d870d1df76fa27aaf8fe7cd4af0e1d566d61a939ed3d3030e7739e6409a5",
        "helper_names": ("bicubic", "catmullRom3x3", "catmullRom4x4", "quadratic"),
        "expected_uniforms": ("time", "seed", "resolution", "tileOffset", "fullResolution", "fbTex", "smoothing", "prevFrameTex"),
        "expected_samplers": ("fbTex", "prevFrameTex"),
        "expected_outputs": ("fragColor",),
        "expected_uses": 50,
        "expected_calls": 4,
        "call_sampler_name": "fbTex",
    },
    MNCA_KEY: {
        "raw_bytes": 11142,
        "raw_sha256": "725c245f6f52a1629f7427b98a211b527c546fd3e0dcecbb9c5b65ecf3ee239a",
        "norm_bytes": 9051,
        "norm_sha256": "f7cfb28404d7ddb7d8191762c3869cbe93e54953a13e99b366cceaa132a7739c",
        "functions_sha256": "14ae1c0f1e2f4b54115e2286257b38e5e67a68a4a79996a5130c87b5e05aa0f6",
        "whole_sha256": "ebe721bdc81125ad8a98270ed7aa9fb6415e1db9c17579047a397c22f5eee95c",
        "interface_sha256": "f74a7b809dee7e9b324018aac2b8491810aa679668bff528b76c95fa4a24a068",
        "helper_names": ("bicubic", "catmullRom3x3", "catmullRom4x4", "quadratic"),
        "expected_uniforms": ("time", "seed", "resolution", "tileOffset", "fullResolution", "fbTex", "smoothing", "prevFrameTex"),
        "expected_samplers": ("fbTex", "prevFrameTex"),
        "expected_outputs": ("fragColor",),
        "expected_uses": 50,
        "expected_calls": 4,
        "call_sampler_name": "fbTex",
    },
    RD_KEY: {
        "raw_bytes": 12782,
        "raw_sha256": "2c7c242db938ea81fa738b4f5a4fff9f067afca63802e39689aec49d4955f53c",
        "norm_bytes": 10637,
        "norm_sha256": "e4a5cab341218630a4584494a197b88d39399c109c9d8cb3d7dbcc004b44fced",
        "functions_sha256": "3370d1a9b2e34a58d392c34367baf90c69e91ac1b887c398626cae52c0ca4e6e",
        "whole_sha256": "ef848d326bddec454e1172ebb3b5f9c643878307fbf4021fc5b3602313c142b5",
        "interface_sha256": "7e58fd0fb461fe166f5972f74958e137207d4420120a0abf0f96e7dc53a8e6c5",
        "helper_names": ("bicubic", "catmullRom3x3", "catmullRom4x4", "quadratic"),
        "expected_uniforms": ("time", "seed", "resolution", "tileOffset", "fullResolution", "fbTex", "inputTex", "smoothing", "inputIntensity"),
        "expected_samplers": ("fbTex", "inputTex"),
        "expected_outputs": ("fragColor",),
        "expected_uses": 50,
        "expected_calls": 4,
        "call_sampler_name": "fbTex",
    },
    RD_FB_KEY: {
        "raw_bytes": 5763,
        "raw_sha256": "1b0a2ce5b7594005e778b0487a14c1c83c081b7ce3d0db50f81809ac931be976",
        "norm_bytes": 4897,
        "norm_sha256": "d7102bf338474ad5c510bc647da43ef2a0e3531e6e4e1a98921beab3d219c2fd",
        "functions_sha256": "a4aff7526aa3695df324eb2cb0a42382686e0ae85b5351c09ee75255e8df522a",
        "whole_sha256": "b97c184e66f29aaf6609ea9bcbf32a64e9e6159429594ffef8cd35f86b0f5162",
        "interface_sha256": "3edb0c009e5bd8b80ae75e323bc131ba17f10aaa12052940d09b9101365f6411",
        "helper_names": ("lp",),
        "expected_uniforms": ("time", "seed", "resolution", "bufTex", "feed", "kill", "rate1", "rate2", "speed", "weight", "sourceF", "sourceK", "sourceR1", "sourceR2", "zoom", "inputTex", "resetState"),
        "expected_samplers": ("bufTex", "inputTex"),
        "expected_outputs": ("fragColor",),
        "expected_uses": 9,
        "expected_calls": 1,
        "call_sampler_name": "bufTex",
    },
}


@dataclass(frozen=True, slots=True)
class SimulationSamplerProof:
    program_key: str
    helper_functions: tuple[TypedFunction, ...]
    sampler_parameters: tuple[object, ...]
    sampler_uses: tuple[TypedExpression, ...]
    sampler_calls: tuple[TypedExpression, ...]
    sampler_actuals: tuple[TypedExpression, ...]

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        values: list[object] = [
            *self.helper_functions,
            *self.sampler_parameters,
            *self.sampler_uses,
            *self.sampler_calls,
            *self.sampler_actuals,
        ]
        unique: list[object] = []
        for value in values:
            if not any(value is item for item in unique):
                unique.append(value)
        return tuple(unique)


__all__ = (
    "PROFILE",
    "CA_KEY",
    "MNCA_KEY",
    "RD_KEY",
    "RD_FB_KEY",
    "SIMULATION_SAMPLER_KEYS",
    "SimulationSamplerProof",
    "authenticate_simulation_sampler_parameters",
)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _whole(program: TypedProgram) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def _interface(program: TypedProgram) -> str:
    return _sha((program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _walk_expression(value: TypedExpression, parent: TypedExpression | None = None):
    yield value, parent
    for child in value.children:
        yield from _walk_expression(child, value)


def _walk_statement(value: TypedStatement, ancestors: tuple[TypedStatement, ...] = ()):
    chain = (*ancestors, value)
    for expression in value.expressions:
        for item, parent in _walk_expression(expression):
            yield item, parent, chain
    for child in value.children:
        yield from _walk_statement(child, chain)


def authenticate_simulation_sampler_parameters(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> SimulationSamplerProof:
    """Authenticate simulation shader and return candidate-owned exact IR objects."""
    if profile != PROFILE:
        raise ValueError(f"{PROFILE}: exact profile carrier required")
    if program.key not in SIMULATION_SAMPLER_KEYS:
        raise ValueError(f"{PROFILE}: program key {program.key} not in {SIMULATION_SAMPLER_KEYS}")
    expected = _PROFILES[program.key]
    if source_hash != expected["raw_sha256"]:
        raise ValueError(f"{PROFILE}: {program.key} caller source hash mismatch")

    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != expected["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]
            or len(normalized) != expected["norm_bytes"]
            or hashlib.sha256(normalized).hexdigest() != expected["norm_sha256"]
            or program.preprocessor_defines != ()
            or program.body_status != "analyzed"
            or _sha(program.functions) != expected["functions_sha256"]
            or _whole(program) != expected["whole_sha256"]
            or _interface(program) != expected["interface_sha256"]):
        raise ValueError(f"{PROFILE}: {program.key} source, define, function, whole-program, or interface mismatch")

    if (program.resources.uniforms != expected["expected_uniforms"]
            or program.resources.samplers != expected["expected_samplers"]
            or program.resources.outputs != expected["expected_outputs"]):
        raise ValueError(f"{PROFILE}: {program.key} resources mismatch")

    # Locate helper functions
    helpers: list[TypedFunction] = []
    sampler_parameters: list[object] = []
    param_symbol_ids: set[int] = set()

    for fn in program.functions:
        if fn.name in expected["helper_names"]:
            helpers.append(fn)
            for param in fn.parameters:
                if param.type.kind == "sampler":
                    if param.type.display() != "sampler2D" or param.direction != "in":
                        raise ValueError(f"{PROFILE}: {program.key} helper parameter {param.name} not in sampler2D")
                    sampler_parameters.append(param)
                    param_symbol_ids.add(param.id)

    if len(helpers) != len(expected["helper_names"]):
        raise ValueError(f"{PROFILE}: {program.key} expected {len(expected['helper_names'])} helpers, found {len(helpers)}")
    if len(sampler_parameters) != len(expected["helper_names"]):
        raise ValueError(f"{PROFILE}: {program.key} expected {len(expected['helper_names'])} sampler parameters, found {len(sampler_parameters)}")

    # Collect sampler uses inside helpers
    sampler_uses: list[TypedExpression] = []
    for fn in helpers:
        for stmt in fn.body:
            for item, parent, chain in _walk_statement(stmt):
                if item.kind == "id" and item.symbol_id in param_symbol_ids:
                    if parent is None or parent.kind != "builtin" or parent.callee != "texture" or not parent.children or parent.children[0] is not item:
                        raise ValueError(f"{PROFILE}: {program.key} sampler parameter escape or non-texture use")
                    sampler_uses.append(item)

    if len(sampler_uses) != expected["expected_uses"]:
        raise ValueError(f"{PROFILE}: {program.key} expected {expected['expected_uses']} sampler uses, found {len(sampler_uses)}")

    # Collect call sites and actuals in main()
    main_fn = next((fn for fn in program.functions if fn.name == "main"), None)
    if main_fn is None:
        raise ValueError(f"{PROFILE}: {program.key} main function missing")

    sampler_calls: list[TypedExpression] = []
    sampler_actuals: list[TypedExpression] = []
    for stmt in main_fn.body:
        for item, parent, chain in _walk_statement(stmt):
            if item.kind == "call" and item.callee in expected["helper_names"]:
                sampler_calls.append(item)
                if not item.children or item.children[0].type.kind != "sampler":
                    raise ValueError(f"{PROFILE}: {program.key} call {item.callee} first argument is not a sampler")
                actual = item.children[0]
                if getattr(actual.symbol, "name", None) != expected["call_sampler_name"]:
                    raise ValueError(f"{PROFILE}: {program.key} call {item.callee} actual is not {expected['call_sampler_name']}")
                sampler_actuals.append(actual)

    if len(sampler_calls) != expected["expected_calls"]:
        raise ValueError(f"{PROFILE}: {program.key} expected {expected['expected_calls']} calls, found {len(sampler_calls)}")

    return SimulationSamplerProof(
        program_key=program.key,
        helper_functions=tuple(helpers),
        sampler_parameters=tuple(sampler_parameters),
        sampler_uses=tuple(sampler_uses),
        sampler_calls=tuple(sampler_calls),
        sampler_actuals=tuple(sampler_actuals),
    )
