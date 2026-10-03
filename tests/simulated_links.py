"""Path-specific link metadata for rejection tests without filesystem symlinks."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess

_LINKS: dict[pathlib.Path, pathlib.Path] = {}
_PRELOAD = pathlib.Path(__file__).with_name("simulated_links.cjs")


def simulate_symlink(path, target, *, target_is_directory=False):
    """Create an ordinary placeholder and register the link's metadata/target."""
    path = pathlib.Path(path).absolute()
    target = pathlib.Path(target)
    if not target.is_absolute():
        target = path.parent / target
    target = target.absolute()
    if target_is_directory:
        path.mkdir()
    else:
        path.write_bytes(b"")
    _LINKS[path] = target


def run_with_simulated_links(args, *positional, **kwargs):
    """Inject the simulation into this child only; ordinary paths retain native behavior."""
    mappings = {}
    for path, target in list(_LINKS.items()):
        if not path.exists():
            del _LINKS[path]
            continue
        mappings[str(path)] = str(target)
        mappings[os.path.realpath(path)] = os.path.realpath(target)
    if mappings:
        environment = dict(os.environ if kwargs.get("env") is None else kwargs["env"])
        environment["NOISEMAKER_TEST_LINKS"] = json.dumps(mappings)
        kwargs["env"] = environment
        args = [args[0], "--require", str(_PRELOAD), *args[1:]]
    return subprocess.run(args, *positional, **kwargs)
