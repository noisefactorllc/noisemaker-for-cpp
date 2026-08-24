"""Test-only legacy lowering for historical Gradient reconstructions.

The live Gradient row is authenticated and intentionally lowers its pooled
vector alias in source order.  Frozen milestones predate that carrier and
must continue to regenerate the old generic temporary assignment.  This
module provides an explicit, fail-closed test gate for that projection; it is
not imported by production tooling.
"""

from __future__ import annotations

import contextlib
import functools
import hashlib
import json
from collections.abc import Iterator
from typing import Any
from unittest import mock

from tools.glslcpp import emit_typed_cpp, generate_typed_slice


CROSS_LANE_KEY = "synth/gradient:gradient"
CROSS_LANE_PROFILE = "cross-lane-assignment-v1"
_EXPECTED_ROW_FIELDS = frozenset({
    "defines", "program_key", "cross_lane_assignment_profile",
})
_VALIDATE_SENTINEL = "__historical_cross_lane_validate_sentinel__"
_EMITTER_SENTINEL = "__historical_cross_lane_emitter_sentinel__"
_BIT_EFFECTS_INCLUDE = b'#include "noisemaker/effects/bit_effects.hpp"\n'
_CPP_ARTIFACT = "src/typed_generated/typed_slice.cpp"
_MANIFEST_ARTIFACT = "src/typed_generated/typed_manifest.json"


def _select_row(spec: dict[str, Any]) -> dict[str, Any]:
    """Select the one exact live Gradient row, or reject the projection."""
    programs = spec.get("programs")
    if not isinstance(programs, list):
        raise ValueError("historical cross-lane spec programs must be a list")
    rows = [row for row in programs
            if isinstance(row, dict) and
            row.get("program_key") == CROSS_LANE_KEY]
    if len(rows) != 1:
        raise ValueError(
            "historical cross-lane spec must contain exactly one Gradient row")
    row = rows[0]
    if (set(row) != _EXPECTED_ROW_FIELDS or row.get("defines") != {}
            or row.get("cross_lane_assignment_profile") != CROSS_LANE_PROFILE):
        raise ValueError(
            "historical cross-lane Gradient row must carry the exact carrier")
    return row


@contextlib.contextmanager
def historical_cross_lane(spec: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Project one exact live Gradient row to its pre-profile bytes.

    The carrier is removed only for the duration of this context and restored
    even when generation or the caller raises.  Both generator authorities are
    wrapped and their module-level key sentinels are patched for the full
    context, so the missing carrier selects the ordinary generic assignment
    path while the regen cache observes patched collaborators and bypasses all
    cache reads and writes.
    """
    row = _select_row(spec)
    original_profile = row["cross_lane_assignment_profile"]

    original_validate = generate_typed_slice.validate_capabilities

    @functools.wraps(original_validate)
    def validate_with_sentinel(*args: Any, **kwargs: Any) -> Any:
        with mock.patch.object(generate_typed_slice, "CROSS_LANE_KEY",
                               _VALIDATE_SENTINEL):
            return original_validate(*args, **kwargs)

    original_post_init = emit_typed_cpp._Emitter.__post_init__
    original_generate_outputs = generate_typed_slice.generate_outputs

    @functools.wraps(original_post_init)
    def post_init_with_sentinel(self: Any, *args: Any, **kwargs: Any) -> Any:
        with mock.patch.object(emit_typed_cpp, "CROSS_LANE_KEY",
                               _EMITTER_SENTINEL):
            return original_post_init(self, *args, **kwargs)

    @functools.wraps(original_generate_outputs)
    def generate_historical_outputs(repository=None, *args: Any,
                                     **kwargs: Any) -> dict[str, bytes]:
        outputs = original_generate_outputs(repository, *args, **kwargs)
        target = repository if repository is not None else generate_typed_slice._ROOT
        projected = generate_typed_slice.load_slice(target)
        if any(row.get("program_key") == "classicNoisedeck/bitEffects:bitEffects"
               for row in projected.get("programs", ())):
            return outputs
        cpp = outputs.get(_CPP_ARTIFACT)
        if cpp is None or _BIT_EFFECTS_INCLUDE not in cpp:
            return outputs
        cpp = cpp.replace(_BIT_EFFECTS_INCLUDE, b"", 1)
        outputs[_CPP_ARTIFACT] = cpp
        manifest = json.loads(outputs[_MANIFEST_ARTIFACT].decode("utf-8"))
        output_hash = hashlib.sha256(cpp).hexdigest()
        for row in manifest["programs"]:
            row["output_sha256"] = output_hash
        manifest["typed_slice_sha256"] = output_hash
        outputs[_MANIFEST_ARTIFACT] = (
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            .encode("utf-8"))
        return outputs

    try:
        del row["cross_lane_assignment_profile"]
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(
                generate_typed_slice, "CROSS_LANE_KEY", _VALIDATE_SENTINEL))
            stack.enter_context(mock.patch.object(
                emit_typed_cpp, "CROSS_LANE_KEY", _EMITTER_SENTINEL))
            stack.enter_context(mock.patch.object(
                generate_typed_slice, "validate_capabilities",
                validate_with_sentinel))
            stack.enter_context(mock.patch.object(
                emit_typed_cpp._Emitter, "__post_init__",
                post_init_with_sentinel))
            stack.enter_context(mock.patch.object(
                generate_typed_slice, "generate_outputs",
                generate_historical_outputs))
            yield spec
    finally:
        row["cross_lane_assignment_profile"] = original_profile


__all__ = [
    "CROSS_LANE_KEY",
    "CROSS_LANE_PROFILE",
    "historical_cross_lane",
]
