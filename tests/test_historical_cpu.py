"""Historical environment isolation and filesystem simulation boundaries."""

import json
import os
import pathlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tests.historical_cpu import historical_cpu_root, historical_environment, historical_run
from tests.simulated_links import run_with_simulated_links, simulate_symlink


class HistoricalCpuTests(unittest.TestCase):
    def test_historical_authority_never_falls_back_to_current(self):
        with patch.dict(os.environ, {"NOISEMAKER_CPU_ROOT": "/current"}, clear=True):
            self.assertIsNone(historical_cpu_root())

    def test_child_rebind_preserves_parent_and_explicit_negative_inputs(self):
        environment = {"NOISEMAKER_CPU_ROOT": "/current",
                       "NOISEMAKER_HISTORICAL_CPU_ROOT": "/historical",
                       "NOISEMAKER_FOR_CPU": "/live"}
        with patch.dict(os.environ, environment, clear=True):
            child = historical_environment()
            self.assertEqual(child["NOISEMAKER_CPU_ROOT"], "/historical")
            self.assertEqual(child["NOISEMAKER_FOR_CPU"], "/live")
            self.assertEqual(os.environ["NOISEMAKER_CPU_ROOT"], "/current")
            self.assertNotIn("NOISEMAKER_CPU_ROOT", historical_environment({}))
            self.assertEqual(historical_environment({"NOISEMAKER_CPU_ROOT": "/forged"}),
                             {"NOISEMAKER_CPU_ROOT": "/forged"})

    def test_historical_node_child_receives_separate_authority(self):
        with patch.dict(os.environ, {"NOISEMAKER_CPU_ROOT": "/current",
                                     "NOISEMAKER_HISTORICAL_CPU_ROOT": "/historical"}):
            child = historical_run(["node", "-e", "console.log(process.env.NOISEMAKER_CPU_ROOT)"],
                                   capture_output=True, text=True, check=True)
            self.assertEqual(child.stdout.strip(), "/historical")
            self.assertEqual(os.environ["NOISEMAKER_CPU_ROOT"], "/current")

    def test_non_node_subprocess_is_not_rebound(self):
        with patch("tests.historical_cpu.subprocess.run") as run:
            historical_run(["python3.13", "script.py"], env={"NOISEMAKER_CPU_ROOT": "/current"})
            run.assert_called_once_with(["python3.13", "script.py"],
                                        env={"NOISEMAKER_CPU_ROOT": "/current"})

    def test_node_simulates_leaf_metadata_resolution_and_reads_only_registered_paths(self):
        with tempfile.TemporaryDirectory() as raw:
            base = pathlib.Path(raw).resolve()
            target = base / "target"
            target.mkdir()
            (target / "data").write_text("target bytes")
            link = base / "simulated"
            simulate_symlink(link, target, target_is_directory=True)
            self.assertTrue(link.is_dir())
            self.assertFalse(link.is_symlink())
            self.assertEqual(list(link.iterdir()), [])
            script = '''import {lstat, realpath, readFile, stat} from 'node:fs/promises';
import {lstatSync, realpathSync} from 'node:fs';
const [link, target] = process.argv.slice(1);
console.log(JSON.stringify({link: (await lstat(link)).isSymbolicLink(),
 syncLink: lstatSync(link).isSymbolicLink(), directory: (await stat(link)).isDirectory(),
 targetLink: (await lstat(target)).isSymbolicLink(), real: await realpath(link),
 syncReal: realpathSync(link), bytes: await readFile(link + '/data', 'utf8')}));'''
            result = run_with_simulated_links(["node", "--input-type=module", "-e", script,
                                               str(link), str(target)],
                                              capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout), {
                "link": True, "syncLink": True, "directory": True, "targetLink": False,
                "real": str(target), "syncReal": str(target), "bytes": "target bytes"})
            self.assertFalse(link.is_symlink())
            self.assertEqual(subprocess.run(["node", "-e",
                "console.log(require('fs').lstatSync(process.argv[1]).isSymbolicLink())", str(link)],
                capture_output=True, text=True, check=True).stdout.strip(), "false")

    def test_node_simulates_file_link_and_relative_resolution(self):
        with tempfile.TemporaryDirectory() as raw:
            base = pathlib.Path(raw).resolve()
            target = base / "target"
            target.write_text("data")
            link = base / "simulated"
            simulate_symlink(link, "target")
            self.assertTrue(link.is_file())
            self.assertFalse(link.is_symlink())
            result = run_with_simulated_links(["node", "-e",
                "const fs=require('fs');const p=process.argv[1];"
                "console.log(JSON.stringify([fs.lstatSync(p).isSymbolicLink(),fs.readFileSync(p,'utf8')]))",
                str(link)], capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout), [True, "data"])
