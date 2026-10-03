"""Select the frozen CPU authority only for historical oracle subprocesses."""

from __future__ import annotations

import os
import pathlib
import subprocess

from tests.simulated_links import run_with_simulated_links

HISTORICAL_CPU_ENV = "NOISEMAKER_HISTORICAL_CPU_ROOT"


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
        return run_with_simulated_links(args, *positional, **kwargs)
    return subprocess.run(args, *positional, **kwargs)
