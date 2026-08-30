"""Byte-exact top-down RGBA8 comparison for CPU benchmark runs."""

from __future__ import annotations

import hashlib
from typing import Any


def compare_rgba8(width: int, height: int, expected: bytes, actual: bytes) -> dict[str, Any]:
    """Compare every byte and return bounded, machine-readable diagnostics."""
    expected_hash = hashlib.sha256(expected).hexdigest()
    actual_hash = hashlib.sha256(actual).hexdigest()
    required = width * height * 4
    if len(expected) != required or len(actual) != required:
        return {
            "ok": False,
            "width": width,
            "height": height,
            "expectedLength": len(expected),
            "actualLength": len(actual),
            "mismatchCount": 0,
            "maxDelta": 0,
            "expectedSha256": expected_hash,
            "actualSha256": actual_hash,
            "firstMismatch": None,
        }
    mismatch_count = 0
    max_delta = 0
    first = None
    for offset, (wanted, got) in enumerate(zip(expected, actual)):
        delta = abs(wanted - got)
        max_delta = max(max_delta, delta)
        if wanted != got:
            mismatch_count += 1
            if first is None:
                pixel, channel = divmod(offset, 4)
                first = {
                    "offset": offset,
                    "x": pixel % width,
                    "y": pixel // width,
                    "channel": "RGBA"[channel],
                    "expected": wanted,
                    "actual": got,
                }
    return {
        "ok": mismatch_count == 0 and max_delta == 0 and expected_hash == actual_hash,
        "width": width,
        "height": height,
        "expectedLength": len(expected),
        "actualLength": len(actual),
        "mismatchCount": mismatch_count,
        "maxDelta": max_delta,
        "expectedSha256": expected_hash,
        "actualSha256": actual_hash,
        "firstMismatch": first,
    }


def format_diagnostics(result: dict[str, Any]) -> str:
    first = result.get("firstMismatch")
    location = "none" if first is None else (
        f"offset={first['offset']} x={first['x']} y={first['y']} channel={first['channel']} "
        f"expected={first['expected']} actual={first['actual']}"
    )
    return " ".join([
        f"dimensions={result['width']}x{result['height']}",
        f"expectedLength={result['expectedLength']}",
        f"actualLength={result['actualLength']}",
        f"firstMismatch={location}",
        f"mismatchCount={result['mismatchCount']}",
        f"maxDelta={result['maxDelta']}",
        f"expectedSha256={result['expectedSha256']}",
        f"actualSha256={result['actualSha256']}",
    ])
