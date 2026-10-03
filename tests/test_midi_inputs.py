import json
import pathlib
import struct
import subprocess
import tempfile
import unittest

from tools.benchmark.corpus_lane import record_flags

ROOT = pathlib.Path(__file__).resolve().parents[1]


class MidiInputTests(unittest.TestCase):
    def test_grid_transport_preserves_words_and_clock(self):
        words = [0x80000000, 0x7F812345, 0x7FC12345, 0x3F800000] + [0] * 8188
        payload = struct.pack('<8192I', *words)
        state = {'noteGridRgba32f': payload.hex(), 'clockCount': 241.5}
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / 'case.dsl'
            record = {'sourceSha256': '0' * 64,
                      'options': dict(width=1, height=1, time=0.0, frame=0, seed=1.0),
                      'externalInputs': {'midiState': state}}
            flags = record_flags(record, source)
            self.assertIn('--midi-note-grid-file', flags)
            grid = pathlib.Path(flags[flags.index('--midi-note-grid-file') + 1])
            self.assertEqual(grid.read_bytes(), payload)
            self.assertEqual(flags[flags.index('--midi-clock') + 1], '241.5')
        script = '''
import {decodeMidiState} from './tools/benchmark/midi_inputs.mjs';
const input = JSON.parse(process.argv[1]);
const state = decodeMidiState(input);
console.log(JSON.stringify({clock:state.clockCount, words:Array.from(new Uint32Array(state.noteGrid.buffer)).slice(0,4)}));
'''
        result = subprocess.run(['node', '--input-type=module', '-e', script, json.dumps(state)],
                                cwd=ROOT, check=True, text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout), {'clock': 241.5, 'words': words[:4]})

    def test_partial_grid_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            record = {'sourceSha256': '0' * 64,
                      'options': dict(width=1, height=1, time=0.0, frame=0, seed=1.0),
                      'externalInputs': {'midiState': {'noteGridRgba32f': '00'}}}
            with self.assertRaisesRegex(ValueError, '128x16'):
                record_flags(record, pathlib.Path(directory) / 'case.dsl')


if __name__ == '__main__':
    unittest.main()
