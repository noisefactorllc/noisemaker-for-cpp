"""Fail when the JavaScript authority has moved past the revision this port is pinned to.

CI pins one noisemaker-for-cpu commit and proves parity against it. That proof says nothing
about the authority's current behavior, so this check compares the pinned behavioral lock with
the behavioral lock of a live authority checkout (normally its default branch).
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from tools.dsl.generate_backend_compatibility import behavioral_lock

ROOT = pathlib.Path(__file__).resolve().parents[2]
AUTHORITY_MODULE = ROOT / "tools/dsl/corpus_authority.mjs"


def pinned() -> dict[str, str]:
    text = AUTHORITY_MODULE.read_text(encoding="utf-8")
    values = {}
    for name in ("behavioralLockSha256", "upstreamRevision"):
        match = re.search(rf"\b{name}: '([0-9a-f]+)'", text)
        if match is None:
            raise SystemExit(f"check_authority_drift: cannot read {name} from {AUTHORITY_MODULE}")
        values[name] = match.group(1)
    return values


def live(cpu_root: pathlib.Path) -> dict[str, str]:
    digest, _ = behavioral_lock(cpu_root)
    lock = (cpu_root / "scripts/upstream/source-lock.js").read_text(encoding="utf-8")
    match = re.search(r"PINNED_UPSTREAM_REVISION\s*=\s*'([0-9a-f]{40})'", lock)
    if match is None:
        raise SystemExit("check_authority_drift: live authority declares no upstream revision")
    return {"behavioralLockSha256": digest, "upstreamRevision": match.group(1)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu-root", type=pathlib.Path, required=True)
    arguments = parser.parse_args(argv)
    expected, actual = pinned(), live(arguments.cpu_root.resolve())
    if expected == actual:
        print(f"check_authority_drift: pinned authority is current (upstream {actual['upstreamRevision']})")
        return 0
    print("check_authority_drift: the authority has drifted from this port's pin", file=sys.stderr)
    for name in expected:
        print(f"  {name}: pinned {expected[name]}, live {actual[name]}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
