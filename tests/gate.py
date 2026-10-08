"""Push-gate selection for the Python suite.

CI runs the Python suite twice: the push gate (NOISEMAKER_PUSH_GATE=1) and the
full weekly or dispatched run. Tests marked `full_run_only` skip in the push
gate and run in the full suite: the measured slow ones (typed-slice
regenerations and historical milestone reconstructions, each 2 seconds or
more) and the ones that compile C++ probes or build the CMake package.
"""
from __future__ import annotations

import os
import unittest

PUSH_GATE = os.environ.get("NOISEMAKER_PUSH_GATE") == "1"

full_run_only = unittest.skipIf(PUSH_GATE, "full CI run only (weekly schedule or workflow_dispatch)")
