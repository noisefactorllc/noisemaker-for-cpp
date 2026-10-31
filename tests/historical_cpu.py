"""Select the frozen CPU authority only for historical oracle subprocesses."""

from __future__ import annotations

import os
import hashlib
import pathlib
import subprocess

from tests.simulated_links import run_with_simulated_links

HISTORICAL_CPU_ENV = "NOISEMAKER_HISTORICAL_CPU_ROOT"
CURRENT_CPU_ENV = "NOISEMAKER_CPU_ROOT"
ORACLE_NODE_ENV = "NOISEMAKER_ORACLE_NODE"


CPU_9B729482_ENV = "NOISEMAKER_CPU_9B729482_ROOT"


def cpu_9b729482_root() -> str:
    value = os.environ.get(CPU_9B729482_ENV)
    if not value:
        raise ValueError(f"{CPU_9B729482_ENV} is required for frozen CPU fixtures")
    root = pathlib.Path(value)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError(f"{CPU_9B729482_ENV} must name an absolute, non-symlink directory")
    identities = {
        "src/effects/generated/canonical-kernels.js": "2d2ad7a462d2f5e858d1ff339b0be48db097dbf3e7848bde08b90e7e3df1f869",
        "src/effects/generated/upstream-snapshot.js": "de72cda3ef1b8789b91d284682577be67fd638a2747cae60bea7b72f74ca988f",
    }
    for relative, expected in identities.items():
        source = root / relative
        if (source.is_symlink() or not source.is_file()
                or hashlib.sha256(source.read_bytes()).hexdigest() != expected):
            raise ValueError(f"{CPU_9B729482_ENV} frozen source identity mismatch: {relative}")
    return value


def current_cpu_root() -> str | None:
    return os.environ.get(CURRENT_CPU_ENV)


def current_run(args, *positional, **kwargs):
    """Run a current-authority command without historical environment rebinding."""
    if not isinstance(args, (str, bytes)) and pathlib.Path(args[0]).name == "node":
        environment = os.environ if kwargs.get("env") is None else kwargs["env"]
        if ORACLE_NODE_ENV in environment:
            executable = pathlib.Path(environment[ORACLE_NODE_ENV])
            if (not executable.is_absolute() or executable.is_symlink()
                    or not executable.is_file() or not os.access(executable, os.X_OK)):
                raise ValueError(f"{ORACLE_NODE_ENV} must name an absolute, regular executable file")
            args = [str(executable), *args[1:]]
        return run_with_simulated_links(args, *positional, **kwargs)
    return subprocess.run(args, *positional, **kwargs)


def historical_cpu_root() -> str | None:
    return os.environ.get(HISTORICAL_CPU_ENV)


def historical_environment(environment=None):
    """Translate the ambient current authority, preserving explicit negative inputs."""
    result = dict(os.environ if environment is None else environment)
    historical = historical_cpu_root()
    if historical and "NOISEMAKER_CPU_ROOT" in result:
        if result["NOISEMAKER_CPU_ROOT"] == os.environ.get("NOISEMAKER_CPU_ROOT"):
            result["NOISEMAKER_CPU_ROOT"] = historical
    elif historical and environment is None:
        result["NOISEMAKER_CPU_ROOT"] = historical
    return result


def historical_run(args, *positional, **kwargs):
    """Keep authority rebinding local to Node oracle children, never the test process."""
    if not isinstance(args, (str, bytes)) and pathlib.Path(args[0]).name == "node":
        kwargs["env"] = historical_environment(kwargs.get("env"))
    return current_run(args, *positional, **kwargs)
