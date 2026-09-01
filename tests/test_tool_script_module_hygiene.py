"""No runnable tool directory may shadow a standard-library module.

Running `python3 tools/glslcpp/check_corpus.py` puts *that directory* at the
head of sys.path, so a sibling module named after a standard-library module
wins over the standard library for the whole process -- including for the
imports CPython itself performs while loading `argparse`.

Whether it detonates depends on whether the interpreter happened to import the
shadowed module during startup, which differs by interpreter build and by
what is installed in site-packages. `tools/glslcpp/types.py` was invisible on
a Homebrew CPython 3.14 (its site setup imports `types` before user code runs)
and fatal on the hosted-runner CPython 3.13 that first ran the whole suite on
Linux: fifteen of the twenty red tests were this one file. The invariant is
structural, so test it structurally rather than waiting for an interpreter
that trips over it.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
# The standard-library surface the tool entry points reach through, plus the
# transitive imports those pull in. Importing these with a tool directory at
# the head of sys.path is exactly what a shadowing module breaks.
PROBE_IMPORTS = (
    "argparse", "ast", "copy", "dataclasses", "hashlib", "json", "math",
    "pathlib", "re", "struct", "subprocess", "tempfile", "textwrap", "types",
)


def runnable_tool_directories() -> list[pathlib.Path]:
    """Directories that become sys.path[0] when a tool is run as a script."""
    directories = {path.parent for path in (ROOT / "tools").rglob("*.py")}
    directories.update(
        path.parent for path in
        (ROOT / "docs/port-engineering").rglob(
            "generate_*_native_oracle_include.py"))
    directories.update(
        path.parent for path in
        (ROOT / "docs/port-engineering").rglob("*_frontend_probe.py"))
    return sorted(directories)


class ToolScriptModuleHygieneTests(unittest.TestCase):
    def test_no_tool_directory_shadows_a_standard_library_module(self) -> None:
        standard = sys.stdlib_module_names
        offenders = sorted(
            str(path.relative_to(ROOT))
            for directory in runnable_tool_directories()
            for path in directory.glob("*.py")
            if path.stem in standard)
        self.assertEqual([], offenders, "\n".join((
            "tool modules shadow the standard library for every script run "
            "from their own directory; rename them:", *offenders)))

    def test_tool_directories_admit_the_standard_library_on_a_bare_start(
            self) -> None:
        # -S reproduces the hosted-runner condition on any interpreter: no
        # site-packages, so nothing has pre-imported the standard-library
        # modules a shadowing sibling would otherwise be hiding.
        program = (
            "import sys\n"
            f"sys.path.insert(0, {'{!r}'})\n"
            f"import {', '.join(PROBE_IMPORTS)}\n")
        for directory in runnable_tool_directories():
            with self.subTest(directory=str(directory.relative_to(ROOT))):
                completed = subprocess.run(
                    [sys.executable, "-S", "-B", "-c",
                     program.format(str(directory))],
                    cwd=ROOT, text=True, capture_output=True, check=False)
                self.assertEqual(
                    0, completed.returncode,
                    f"{directory}:\n{completed.stderr}")


if __name__ == "__main__":
    unittest.main()
