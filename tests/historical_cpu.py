"""Select the frozen CPU authority only for historical oracle subprocesses."""

from __future__ import annotations

import os
import pathlib
import subprocess

from tests.simulated_links import run_with_simulated_links

HISTORICAL_CPU_ENV = "NOISEMAKER_HISTORICAL_CPU_ROOT"
CURRENT_CPU_ENV = "NOISEMAKER_CPU_ROOT"
ORACLE_NODE_ENV = "NOISEMAKER_ORACLE_NODE"


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
