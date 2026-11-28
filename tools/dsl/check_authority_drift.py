"""Compare the CPU authority payload against this port's behavioral lock.

The live check detects drift from the lock. Pinned mode also requires the
checkout and corpus identities selected for the port's parity tests.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from tools.dsl.generate_backend_compatibility import CompatibilityError, behavioral_lock

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


def verify_cpu_checkout(cpu_root: pathlib.Path, revision: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(cpu_root), "rev-parse", "--show-toplevel", "HEAD"],
        capture_output=True,
        text=True,
    )
    identities = result.stdout.splitlines()
    if result.returncode or len(identities) != 2 or pathlib.Path(identities[0]).resolve() != cpu_root:
        raise SystemExit("check_authority_drift: expected the root of a CPU checkout")
    if identities[1] != revision:
        raise SystemExit(f"check_authority_drift: CPU revision {identities[1]} differs from pin {revision}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu-root", type=pathlib.Path, required=True)
    parser.add_argument("--pinned", nargs=2, metavar=("CPU_SHA", "CORPUS_SHA"),
                        help="require the reviewed CPU checkout and upstream corpus commits")
    arguments = parser.parse_args(argv)
    cpu_root = arguments.cpu_root.resolve()
    expected = pinned()
    if arguments.pinned:
        cpu_revision, corpus_revision = arguments.pinned
        if not all(re.fullmatch(r"[0-9a-f]{40}", revision) for revision in arguments.pinned):
            parser.error("--pinned requires full lowercase CPU and corpus Git SHAs")
        verify_cpu_checkout(cpu_root, cpu_revision)
        if corpus_revision != expected["upstreamRevision"]:
            raise SystemExit("check_authority_drift: corpus revision differs from the behavioral lock")

    try:
        actual = live(cpu_root)
    except (CompatibilityError, OSError) as error:
        print(f"check_authority_drift: {error}", file=sys.stderr)
        return 1
    if expected == actual:
        status = "pinned CPU authority verified" if arguments.pinned else "pinned authority is current"
        print(f"check_authority_drift: {status} (upstream {actual['upstreamRevision']})")
        return 0
    print("check_authority_drift: the authority has drifted from this port's pin", file=sys.stderr)
    for name in expected:
        print(f"  {name}: pinned {expected[name]}, live {actual[name]}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
