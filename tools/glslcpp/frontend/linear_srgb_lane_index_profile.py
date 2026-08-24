"""Exact identity profiles for the shared `linearToSrgb` loop-index closure.

`filter/adjust`, `filter/colorspace`, `classicNoisedeck/cellNoise`, and
`classicNoisedeck/shapes` each carry a byte-identical helper:

```glsl
vec3 linearToSrgb(vec3 linear) {
    vec3 srgb;
    for (int i = 0; i < 3; ++i) {
        if (linear[i] <= 0.0031308) {
            srgb[i] = linear[i] * 12.92;
        } else {
            srgb[i] = 1.055 * pow(linear[i], 1.0 / 2.4) - 0.055;
        }
    }
    return srgb;
}
```

`linear`/`srgb` are plain `vec3`s (a parameter and a local), never a proved
fixed-size array, and `i` is the loop's own induction variable. No existing
index track admits this shape: every prior track (`store_valid`,
`read_valid`, `grid_store_valid`/`grid_read_valid`, `task19_*`,
`task20_valid`) is gated by `base_valid`, which requires the base symbol to
be a member of `proved_array_declarations`/`proved_array_parameters` -- a
proved fixed-size array. This is the identical shape the Task 32 grade
cluster needed (`grade_index_expression_profile.py`), extended to the mat3
OKLab-transform family. This module follows that module's structure exactly.

This module authenticates by node identity from a frozen per-program proof
set (span + SHA-256 for every index site, tabulated below), never by
widening the array machinery and never by adding a new token to the 44-entry
`APPROVED_CAPABILITIES` vocabulary -- the caller must skip `used.add(...)`
entirely for a site admitted through this module, symmetric with the
existing `round`/`tanh`/`floatBitsToUint`/`all`+`lessThanEqual`/
grade-index-expression callee/index skip-lists in `generate_typed_slice.py`.

Beyond the five node identities, every carrier must additionally prove the
closure that makes those five indexes safe, uniformly for all four keys:

* the exact `linearToSrgb` owner, its one `vec3 linear` parameter, and its
  exact three-statement body shape;
* the `vec3 srgb` result local declared with **no** initializer;
* one `for (int i = 0; i < 3; ++i)` counted loop of trip count three;
* the exact read/write role, parent, expression path, and statement ancestry
  of each of the five sites;
* branch-complete result initialization -- the two write sites are the sole
  statements of the two distinct branches of one `if`, so every one of the
  three iterations writes exactly one lane and all three lanes are definitely
  initialized before `return srgb`;
* complete whole-program reference censuses for the result local, the
  parameter, and the induction variable, bound by object identity, so no
  other read or write of any of the three exists anywhere; and
* the exact per-key preprocessor define tuple -- `()` for the three original
  carriers, `LOOP_A_OFFSET=40`/`LOOP_B_OFFSET=30` for Shapes. Shapes has a
  byte-identical normalized source with the defines erased, so the define
  tuple is genuinely load-bearing and cannot be a hardcoded emptiness test.

Slice A only (`classicNoisedeck/colorLab` and `classicNoisedeck/moodscape`
are explicitly out of scope -- colorLab has additional index sites outside
this closure and moodscape's whole matrix+hash closure is dead code, each
needing its own, separate mechanism).
"""

from __future__ import annotations

import hashlib
from typing import NamedTuple

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


KEYS = (
    'classicNoisedeck/cellNoise:cellNoise',
    'classicNoisedeck/shapes:shapes',
    'filter/adjust:adjust',
    'filter/colorspace:colorspace',
)
PROFILES = {
    'classicNoisedeck/cellNoise:cellNoise': 'linear-srgb-cellnoise-lane-index-v1',
    'classicNoisedeck/shapes:shapes': 'linear-srgb-shapes-lane-index-v1',
    'filter/adjust:adjust': 'linear-srgb-adjust-lane-index-v1',
    'filter/colorspace:colorspace': 'linear-srgb-colorspace-lane-index-v1',
}
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)

# Exactly five index objects are authenticated and returned, each visited once.
_LANE_INDEX_LEDGER = 5
# `srgb` is referenced exactly four times program-wide (its declaration, the
# two write-site bases, and the `return srgb`); `linear` exactly three times
# (the three read-site bases); `i` exactly eight times (its declaration, the
# loop condition, the loop update, and the five index subscripts).
_RESULT_REFERENCES = 4
_PARAMETER_REFERENCES = 3
_INDUCTION_REFERENCES = 8

__all__ = ("KEYS", "PROFILES", "authenticate_linear_srgb_lane_index",
           "apply_linear_srgb_lane_index")


class _Site(NamedTuple):
    """One frozen `vec3[i]` identity: node, role, operands, and position."""

    function_id: int
    function_name: str
    span: str
    node_sha256: str
    role: str
    base_symbol_id: int
    base_name: str
    base_storage: str
    index_symbol_id: int
    index_name: str
    parent: tuple[str, str | None, str | None, str]
    child_index: int
    path: tuple[object, ...]
    chain: tuple[tuple[str, str], ...]


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _whole_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


_LOCKS = {
    'classicNoisedeck/cellNoise:cellNoise': {
        "profile": 'linear-srgb-cellnoise-lane-index-v1',
        "raw_bytes": 9643,
        "raw_sha256": '9fd76306b377ef501a5dd340263179f04e3e890cc05d5e82f524f7bdf793d3b8',
        "normalized_bytes": 9019,
        "normalized_sha256": 'a4ca159914f5a124e3a040a047c13deea57b2281602c0dcd5613ece6d39ce7e5',
        "whole_sha256": 'b2773cd52290ecb3b33b980b8265ecf2735798f99f4c88e387065111e4045bb5',
        "interface_sha256": 'fbe56605fd1a6c95fcf481bd9a1d6deeb617ae58e82eab75f789fadb82834f25',
        "functions_sha256": '8414eed368c037129518e8b7a6aa9b0b3a7cca7f9f288762d9049f730ed01779',
        "defines": (),
        "owner": (63, 'linearToSrgb', 'vec3', ((35, 'linear', 'vec3', 'in'),),
                  3, '122:1-132:2'),
        "body": (('decl', '123:5-123:15'), ('for', '124:5-130:6'),
                 ('return', '131:5-131:17')),
        "result": (99, 'srgb', 'local', 'vec3'),
        "loop": (100, 0, 3, '<', '++', 'literal', 3, 1, 1, 3, 33),
        "sites": (
            _Site(63, 'linearToSrgb', '125:13-125:22',
                  '48759f40bc8523a979f73da6b496943125d5a03c9d71b3306ce933c010acb063',
                  'read', 35, 'linear', 'parameter', 100, 'i',
                  ('binary', '<=', None, '125:13-125:35'), 0,
                  (1, 's1', 's0', 'e0', 0),
                  (('for', '124:5-130:6'), ('block', '124:33-130:6'),
                   ('if', '125:9-129:10'))),
            _Site(63, 'linearToSrgb', '126:13-126:20',
                  '04d04b611d26466debff9741c1b427de42bfad74327c15cf8201b6617deea901',
                  'write', 99, 'srgb', 'local', 100, 'i',
                  ('assign', '=', None, '126:13-126:40'), 0,
                  (1, 's1', 's0', 's0', 's0', 'e0', 0),
                  (('for', '124:5-130:6'), ('block', '124:33-130:6'),
                   ('if', '125:9-129:10'), ('block', '125:37-127:10'),
                   ('expr', '126:13-126:41'))),
            _Site(63, 'linearToSrgb', '126:23-126:32',
                  '372a2ced8091e576a5889a3c8aabf95487edada55155fe46f908ca306984892d',
                  'read', 35, 'linear', 'parameter', 100, 'i',
                  ('binary', '*', None, '126:23-126:40'), 0,
                  (1, 's1', 's0', 's0', 's0', 'e0', 1, 0),
                  (('for', '124:5-130:6'), ('block', '124:33-130:6'),
                   ('if', '125:9-129:10'), ('block', '125:37-127:10'),
                   ('expr', '126:13-126:41'))),
            _Site(63, 'linearToSrgb', '128:13-128:20',
                  '81f6aabee92ef8f3d02c9294b91a0b3656245077a362ae3c10b3f8e478390c05',
                  'write', 99, 'srgb', 'local', 100, 'i',
                  ('assign', '=', None, '128:13-128:64'), 0,
                  (1, 's1', 's0', 's1', 's0', 'e0', 0),
                  (('for', '124:5-130:6'), ('block', '124:33-130:6'),
                   ('if', '125:9-129:10'), ('block', '127:16-129:10'),
                   ('expr', '128:13-128:65'))),
            _Site(63, 'linearToSrgb', '128:35-128:44',
                  '0ac3877819736da77ccc128a52fa321166652583e31d332c300d77f8793cfa38',
                  'read', 35, 'linear', 'parameter', 100, 'i',
                  ('builtin', None, 'pow', '128:31-128:56'), 0,
                  (1, 's1', 's0', 's1', 's0', 'e0', 1, 0, 1, 0),
                  (('for', '124:5-130:6'), ('block', '124:33-130:6'),
                   ('if', '125:9-129:10'), ('block', '127:16-129:10'),
                   ('expr', '128:13-128:65'))),
        ),
    },
    'classicNoisedeck/shapes:shapes': {
        "profile": 'linear-srgb-shapes-lane-index-v1',
        "raw_bytes": 21289,
        "raw_sha256": '60bc6e76ac9d9f5bc83638fa934b279499559f7733806e462cea16a4cbe85eb0',
        "normalized_bytes": 18713,
        "normalized_sha256": '347d19f46adb59129ec2f5eb58910b1ea981be9ec03788a068ff6e884bb848e6',
        "whole_sha256": 'e072ec89fef6122ed3d581ea5efb6cec953d9b7492294ca9d8b0f011af5411f0',
        "interface_sha256": 'e27ca4581c14991de7a17e296353b1993e8f9c6e5a4ec48b170dde8f8d1b1b6c',
        "functions_sha256": 'dfd7220ab36ed03702afbc5e69e7e3a7346c60d488d9b3a2087d31214219943a',
        "defines": (('LOOP_A_OFFSET', 'int', '40'),
                    ('LOOP_B_OFFSET', 'int', '30')),
        "owner": (123, 'linearToSrgb', 'vec3', ((104, 'linear', 'vec3', 'in'),),
                  3, '573:1-583:2'),
        "body": (('decl', '574:5-574:15'), ('for', '575:5-581:6'),
                 ('return', '582:5-582:17')),
        "result": (245, 'srgb', 'local', 'vec3'),
        "loop": (246, 0, 3, '<', '++', 'literal', 3, 1, 1, 3, 3),
        "sites": (
            _Site(123, 'linearToSrgb', '576:13-576:22',
                  'ac134ab1d601cd414d6ec818cc3848d74ceee7739631cc15116bcf20a8bc213d',
                  'read', 104, 'linear', 'parameter', 246, 'i',
                  ('binary', '<=', None, '576:13-576:35'), 0,
                  (1, 's1', 's0', 'e0', 0),
                  (('for', '575:5-581:6'), ('block', '575:33-581:6'),
                   ('if', '576:9-580:10'))),
            _Site(123, 'linearToSrgb', '577:13-577:20',
                  '8d26175011299a13e5e1408b02d2ad1b32f36c1910e6488200ceedc734ff711a',
                  'write', 245, 'srgb', 'local', 246, 'i',
                  ('assign', '=', None, '577:13-577:40'), 0,
                  (1, 's1', 's0', 's0', 's0', 'e0', 0),
                  (('for', '575:5-581:6'), ('block', '575:33-581:6'),
                   ('if', '576:9-580:10'), ('block', '576:37-578:10'),
                   ('expr', '577:13-577:41'))),
            _Site(123, 'linearToSrgb', '577:23-577:32',
                  'fa4a5f7df5e12557efabd39a4a4765a47b3721bc6b35f2f6590527abeb2ff6fd',
                  'read', 104, 'linear', 'parameter', 246, 'i',
                  ('binary', '*', None, '577:23-577:40'), 0,
                  (1, 's1', 's0', 's0', 's0', 'e0', 1, 0),
                  (('for', '575:5-581:6'), ('block', '575:33-581:6'),
                   ('if', '576:9-580:10'), ('block', '576:37-578:10'),
                   ('expr', '577:13-577:41'))),
            _Site(123, 'linearToSrgb', '579:13-579:20',
                  '09fcf0808aef308fdb6d804bbff33e5f9697af9f5a92f72da6a6137e3c7aecfe',
                  'write', 245, 'srgb', 'local', 246, 'i',
                  ('assign', '=', None, '579:13-579:64'), 0,
                  (1, 's1', 's0', 's1', 's0', 'e0', 0),
                  (('for', '575:5-581:6'), ('block', '575:33-581:6'),
                   ('if', '576:9-580:10'), ('block', '578:16-580:10'),
                   ('expr', '579:13-579:65'))),
            _Site(123, 'linearToSrgb', '579:35-579:44',
                  'db6e4327d61b14c0699f587a546e1fe32653a537c289f8d9c3f06c841115c686',
                  'read', 104, 'linear', 'parameter', 246, 'i',
                  ('builtin', None, 'pow', '579:31-579:56'), 0,
                  (1, 's1', 's0', 's1', 's0', 'e0', 1, 0, 1, 0),
                  (('for', '575:5-581:6'), ('block', '575:33-581:6'),
                   ('if', '576:9-580:10'), ('block', '578:16-580:10'),
                   ('expr', '579:13-579:65'))),
        ),
    },
    'filter/adjust:adjust': {
        "profile": 'linear-srgb-adjust-lane-index-v1',
        "raw_bytes": 3786,
        "raw_sha256": 'dc1d8456ff2bb6d00ecc62af33ef3a730a990b18b7037d29a29a6e3a3b963ce8',
        "normalized_bytes": 3382,
        "normalized_sha256": '7810e4f14d8d63705bc392a415c1f606f604121dd6636d7fe6aef5c5a5e0a636',
        "whole_sha256": 'a4a7959d413ab77664e4583f9b9c0f1f56672c8ee85d73d70f36f4da9831dbe7',
        "interface_sha256": 'f4db93225b30954134f2891ec3b29f45180c458ca572ad7cfb91d7442aff56fe',
        "functions_sha256": 'ea26a44034a9fbd09c54dcc143ea5b8aff1b50d9573edad06dc1eb63e3858443',
        "defines": (),
        "owner": (24, 'linearToSrgb', 'vec3', ((22, 'linear', 'vec3', 'in'),),
                  3, '75:1-85:2'),
        "body": (('decl', '76:5-76:15'), ('for', '77:5-83:6'),
                 ('return', '84:5-84:17')),
        "result": (37, 'srgb', 'local', 'vec3'),
        "loop": (38, 0, 3, '<', '++', 'literal', 3, 1, 1, 3, 3),
        "sites": (
            _Site(24, 'linearToSrgb', '78:13-78:22',
                  'f6153646521062770ee659a3caed7a846745c92364462ae72fa321857088be99',
                  'read', 22, 'linear', 'parameter', 38, 'i',
                  ('binary', '<=', None, '78:13-78:35'), 0,
                  (1, 's1', 's0', 'e0', 0),
                  (('for', '77:5-83:6'), ('block', '77:33-83:6'),
                   ('if', '78:9-82:10'))),
            _Site(24, 'linearToSrgb', '79:13-79:20',
                  '57dbb47aa526472edd9ece1dade788882705b62fc6eb1586891d726d09669703',
                  'write', 37, 'srgb', 'local', 38, 'i',
                  ('assign', '=', None, '79:13-79:40'), 0,
                  (1, 's1', 's0', 's0', 's0', 'e0', 0),
                  (('for', '77:5-83:6'), ('block', '77:33-83:6'),
                   ('if', '78:9-82:10'), ('block', '78:37-80:10'),
                   ('expr', '79:13-79:41'))),
            _Site(24, 'linearToSrgb', '79:23-79:32',
                  '91fc8a87cabba5ae290110628b8f46e034ce186a036108f853245f52bbe4e28d',
                  'read', 22, 'linear', 'parameter', 38, 'i',
                  ('binary', '*', None, '79:23-79:40'), 0,
                  (1, 's1', 's0', 's0', 's0', 'e0', 1, 0),
                  (('for', '77:5-83:6'), ('block', '77:33-83:6'),
                   ('if', '78:9-82:10'), ('block', '78:37-80:10'),
                   ('expr', '79:13-79:41'))),
            _Site(24, 'linearToSrgb', '81:13-81:20',
                  '2577df551ea7ae2333d79f55a6084d5f00049b974f39e45c901836a40a31e25f',
                  'write', 37, 'srgb', 'local', 38, 'i',
                  ('assign', '=', None, '81:13-81:64'), 0,
                  (1, 's1', 's0', 's1', 's0', 'e0', 0),
                  (('for', '77:5-83:6'), ('block', '77:33-83:6'),
                   ('if', '78:9-82:10'), ('block', '80:16-82:10'),
                   ('expr', '81:13-81:65'))),
            _Site(24, 'linearToSrgb', '81:35-81:44',
                  'dd30b118dbe1897f417bf134dd8feb1205daaef0b773e461a5ef6641e502f415',
                  'read', 22, 'linear', 'parameter', 38, 'i',
                  ('builtin', None, 'pow', '81:31-81:56'), 0,
                  (1, 's1', 's0', 's1', 's0', 'e0', 1, 0, 1, 0),
                  (('for', '77:5-83:6'), ('block', '77:33-83:6'),
                   ('if', '78:9-82:10'), ('block', '80:16-82:10'),
                   ('expr', '81:13-81:65'))),
        ),
    },
    'filter/colorspace:colorspace': {
        "profile": 'linear-srgb-colorspace-lane-index-v1',
        "raw_bytes": 2711,
        "raw_sha256": '602f1a2ce0abd59e8e17753c8ec9b49d01fbe0f169d60ad290d294904e02f705',
        "normalized_bytes": 2274,
        "normalized_sha256": '0cafa73621116d2a639350f56678bf384b028830fd7674c64810e061d4de4adc',
        "whole_sha256": '912f5bcc8a34782d985947fcf6de1c23c586cae969386a854ee509314776af49',
        "interface_sha256": '8450fb56f2a26c1faac8758f0c016547f41246b01168889b9f376e08554bc7a0',
        "functions_sha256": '9b6d143abc0cdad48afb14c4687d1275fc96f46fae44e490e629bb5f046a7420',
        "defines": (),
        "owner": (13, 'linearToSrgb', 'vec3', ((11, 'linear', 'vec3', 'in'),),
                  3, '45:1-55:2'),
        "body": (('decl', '46:5-46:15'), ('for', '47:5-53:6'),
                 ('return', '54:5-54:17')),
        "result": (24, 'srgb', 'local', 'vec3'),
        "loop": (25, 0, 3, '<', '++', 'literal', 3, 1, 1, 3, 3),
        "sites": (
            _Site(13, 'linearToSrgb', '48:13-48:22',
                  'eb9e009353ece6a0d9b3c6e67a44cb147ee2941ce75c478682d07f5843b3d542',
                  'read', 11, 'linear', 'parameter', 25, 'i',
                  ('binary', '<=', None, '48:13-48:35'), 0,
                  (1, 's1', 's0', 'e0', 0),
                  (('for', '47:5-53:6'), ('block', '47:33-53:6'),
                   ('if', '48:9-52:10'))),
            _Site(13, 'linearToSrgb', '49:13-49:20',
                  '7e58f6b8efec078e1891620340de6b3d6aaaf6291c9828d697ba448e6fffe966',
                  'write', 24, 'srgb', 'local', 25, 'i',
                  ('assign', '=', None, '49:13-49:40'), 0,
                  (1, 's1', 's0', 's0', 's0', 'e0', 0),
                  (('for', '47:5-53:6'), ('block', '47:33-53:6'),
                   ('if', '48:9-52:10'), ('block', '48:37-50:10'),
                   ('expr', '49:13-49:41'))),
            _Site(13, 'linearToSrgb', '49:23-49:32',
                  'da8171adf83cfe93a974e6a8b977beed368d7d9660f35844d94d85b4de37b3ad',
                  'read', 11, 'linear', 'parameter', 25, 'i',
                  ('binary', '*', None, '49:23-49:40'), 0,
                  (1, 's1', 's0', 's0', 's0', 'e0', 1, 0),
                  (('for', '47:5-53:6'), ('block', '47:33-53:6'),
                   ('if', '48:9-52:10'), ('block', '48:37-50:10'),
                   ('expr', '49:13-49:41'))),
            _Site(13, 'linearToSrgb', '51:13-51:20',
                  '4c3d1d47a85b37b3c759db454ba9817095dd7ac38a4f0dd8dbc740f82f74c98b',
                  'write', 24, 'srgb', 'local', 25, 'i',
                  ('assign', '=', None, '51:13-51:64'), 0,
                  (1, 's1', 's0', 's1', 's0', 'e0', 0),
                  (('for', '47:5-53:6'), ('block', '47:33-53:6'),
                   ('if', '48:9-52:10'), ('block', '50:16-52:10'),
                   ('expr', '51:13-51:65'))),
            _Site(13, 'linearToSrgb', '51:35-51:44',
                  '23362b2df7da5485cd68f7101cdbcadd6924a94f63d9da7003db8d05d4bd2053',
                  'read', 11, 'linear', 'parameter', 25, 'i',
                  ('builtin', None, 'pow', '51:31-51:56'), 0,
                  (1, 's1', 's0', 's1', 's0', 'e0', 1, 0, 1, 0),
                  (('for', '47:5-53:6'), ('block', '47:33-53:6'),
                   ('if', '48:9-52:10'), ('block', '50:16-52:10'),
                   ('expr', '51:13-51:65'))),
        ),
    },
}


def _fail(message: str) -> ValueError:
    return ValueError(f"linear-srgb-lane-index-v1: {message}")


def _check_ledger(entries: list, expected: int, label: str) -> None:
    """Require ``entries`` to hold exactly ``expected`` distinct objects.

    The ledger is what proves each authenticated object was visited and
    consumed exactly once; a duplicate identity or a short/long visitation is
    a hard failure rather than a silently tolerated recount.
    """
    identities = [id(item) for item in entries]
    if len(identities) != expected or len(set(identities)) != expected:
        raise _fail(f"{label} visitation ledger mismatch")


def _walk_statement(statement: TypedStatement, results: list,
                    path: tuple[object, ...] = (),
                    ancestors: tuple[TypedStatement, ...] = ()) -> None:
    chain = (*ancestors, statement)
    for index, expression in enumerate(statement.expressions):
        _walk_expression(expression, statement, index, results,
                         (*path, f"e{index}"), chain)
    for index, child in enumerate(statement.children):
        _walk_statement(child, results, (*path, f"s{index}"), chain)


def _walk_expression(value: TypedExpression, parent: object,
                     child_index: int | None, results: list,
                     path: tuple[object, ...],
                     chain: tuple[TypedStatement, ...]) -> None:
    results.append((value, parent, child_index, path, chain))
    for index, child in enumerate(value.children):
        _walk_expression(child, value, index, results, (*path, index), chain)


def _parent_record(parent: object) -> tuple[str, str | None, str | None, str]:
    return (getattr(parent, "kind", ""), getattr(parent, "operator", None),
            getattr(parent, "callee", None), _span(parent))


def authenticate_linear_srgb_lane_index(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Authenticate and return only the exact frozen index-node identities
    for ``program.key``'s shared ``linearToSrgb`` lane-index closure.

    Every ``index``-kind node in the whole program is censused (not merely
    the frozen sites looked up) and the count must match the frozen per-key
    site count exactly -- this is the whole-program completeness proof: no
    stray, un-authenticated index node can exist anywhere in the program.
    """
    lock = _LOCKS.get(program.key)
    if lock is None:
        raise _fail("selected key is not in the linear-srgb lane index cluster")
    if profile != lock["profile"]:
        raise _fail("exact profile carrier required")
    if source_hash != lock["raw_sha256"]:
        raise _fail("exact caller source hash required")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if defines != lock["defines"]:
        raise _fail("exact preprocessor define lock mismatch")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != lock["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != lock["raw_sha256"]
            or len(normalized) != lock["normalized_bytes"]
            or hashlib.sha256(normalized).hexdigest() != lock["normalized_sha256"]
            or program.body_status != "analyzed"
            or _sha(program.functions) != lock["functions_sha256"]
            or _whole_fingerprint(program) != lock["whole_sha256"]
            or _interface_fingerprint(program) != lock["interface_sha256"]):
        raise _fail("source, define, function, whole-program, or interface mismatch")
    if any(getattr(program, field) is not None for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    proof = program.counted_loop_proof
    if proof is None or not proof.call_graph_acyclic:
        raise _fail("loop or call graph profile mismatch")

    (owner_id, owner_name, owner_return, owner_parameters, owner_body_length,
     owner_span) = lock["owner"]
    owners = [item for item in program.functions if item.id == owner_id]
    if len(owners) != 1:
        raise _fail("linearToSrgb owner identity mismatch")
    owner = owners[0]
    if ((owner.name, owner.return_type.display(),
         tuple((item.id, item.name, item.type.display(), item.direction)
               for item in owner.parameters),
         len(owner.body), _span(owner))
            != (owner_name, owner_return, owner_parameters, owner_body_length,
                owner_span)):
        raise _fail("linearToSrgb owner identity mismatch")
    if tuple((item.kind, _span(item)) for item in owner.body) != lock["body"]:
        raise _fail("linearToSrgb body shape mismatch")

    result_symbol_id, result_name, result_storage, result_type = lock["result"]
    declaration_statement, loop_statement, return_statement = owner.body
    if len(declaration_statement.expressions) != 1:
        raise _fail("srgb result local declaration mismatch")
    declaration = declaration_statement.expressions[0]
    if (declaration.kind != "declaration" or declaration.children != ()
            or declaration.symbol_id != result_symbol_id
            or declaration.symbol is None
            or declaration.symbol.id != result_symbol_id
            or declaration.symbol.name != result_name
            or declaration.symbol.storage != result_storage
            or not declaration.symbol.writable
            or declaration.type.display() != result_type):
        raise _fail("srgb result local declaration mismatch")

    loop_proof = loop_statement.loop_proof
    if (loop_statement.kind != "for" or loop_proof is None
            or (loop_proof.induction_symbol_id, loop_proof.start_value,
                loop_proof.bound_value, loop_proof.comparison,
                loop_proof.update, loop_proof.bound_kind,
                loop_proof.trip_count, loop_proof.lexical_depth,
                loop_proof.effective_depth, loop_proof.lexical_product,
                loop_proof.entrypoint_charge) != lock["loop"]
            or len(loop_statement.children) != 2
            or loop_statement.children[1].kind != "block"
            or len(loop_statement.children[1].children) != 1
            or loop_statement.children[1].children[0].kind != "if"):
        raise _fail("linearToSrgb counted loop profile mismatch")
    conditional = loop_statement.children[1].children[0]

    if (len(return_statement.expressions) != 1
            or return_statement.expressions[0].kind != "id"
            or return_statement.expressions[0].symbol_id != result_symbol_id
            or return_statement.expressions[0].type.display() != result_type):
        raise _fail("srgb return identity mismatch")
    returned = return_statement.expressions[0]

    census: list[tuple[TypedExpression, object, int | None,
                       tuple[object, ...], tuple[TypedStatement, ...],
                       int, str]] = []
    references: dict[int, list[TypedExpression]] = {
        result_symbol_id: [], lock["sites"][0].base_symbol_id: [],
        lock["sites"][0].index_symbol_id: []}
    for function in program.functions:
        for index, statement in enumerate(function.body):
            results: list = []
            _walk_statement(statement, results, (index,))
            for node, parent, child_index, path, chain in results:
                if node.symbol_id in references:
                    references[node.symbol_id].append(node)
                if node.kind == "index":
                    census.append((node, parent, child_index, path, chain,
                                   function.id, function.name))

    expected_sites = lock["sites"]
    if len(census) != len(expected_sites):
        raise _fail("index-node census cardinality mismatch")

    resolved: list[TypedExpression] = []
    ledger: list[TypedExpression] = []
    for (node, parent, child_index, path, chain, function_id,
         function_name), expected in zip(census, expected_sites):
        if (function_id != expected.function_id
                or function_name != expected.function_name
                or _span(node) != expected.span
                or _sha(node) != expected.node_sha256
                or node.type.display() != "float"
                or node.category != "lvalue"
                or len(node.children) != 2):
            raise _fail("index site node profile mismatch")
        role = ("write" if isinstance(parent, TypedExpression)
                and parent.kind == "assign" and parent.operator == "="
                and child_index == 0 else "read")
        if role != expected.role:
            raise _fail("index site role profile mismatch")
        base, index = node.children
        if (base.kind != "id" or base.symbol_id != expected.base_symbol_id
                or base.symbol is None
                or base.symbol.id != expected.base_symbol_id
                or base.symbol.name != expected.base_name
                or base.symbol.storage != expected.base_storage
                or not base.symbol.writable
                or base.type.display() != "vec3" or base.category != "lvalue"):
            raise _fail("index site base profile mismatch")
        if (index.kind != "id" or index.symbol_id != expected.index_symbol_id
                or index.symbol is None
                or index.symbol.id != expected.index_symbol_id
                or index.symbol.name != expected.index_name
                or index.symbol.storage != "local"
                or index.type.display() != "int"):
            raise _fail("index site induction-variable profile mismatch")
        if (parent is None or _parent_record(parent) != expected.parent
                or child_index != expected.child_index):
            raise _fail("index site parent profile mismatch")
        if (path != expected.path
                or tuple((item.kind, _span(item)) for item in chain)
                != expected.chain):
            raise _fail("index site ancestry profile mismatch")
        resolved.append(node)
        ledger.append(node)

    # Branch-complete lane initialization. Sites 1 and 3 are the two writes;
    # they must be the sole statements of the two distinct branches of the one
    # `if` inside the trip-count-three loop, so each iteration writes exactly
    # one lane of `srgb` and lanes 0/1/2 are all initialized before the return.
    condition_chain = census[0][4]
    write_chains = (census[1][4], census[3][4])
    if (len(conditional.children) != 2
            or len(conditional.expressions) != 1
            or condition_chain[-1] is not conditional
            or write_chains[0][2] is not conditional
            or write_chains[1][2] is not conditional
            or write_chains[0][3] is not conditional.children[0]
            or write_chains[1][3] is not conditional.children[1]
            or write_chains[0][3] is write_chains[1][3]
            or len(conditional.children[0].children) != 1
            or len(conditional.children[1].children) != 1
            or write_chains[0][4] is not conditional.children[0].children[0]
            or write_chains[1][4] is not conditional.children[1].children[0]
            or len(references[result_symbol_id]) != _RESULT_REFERENCES
            or {id(item) for item in references[result_symbol_id]}
            != {id(declaration), id(returned),
                id(resolved[1].children[0]), id(resolved[3].children[0])}):
        raise _fail("srgb lane initialization completeness mismatch")

    parameter_symbol_id = expected_sites[0].base_symbol_id
    if (len(references[parameter_symbol_id]) != _PARAMETER_REFERENCES
            or {id(item) for item in references[parameter_symbol_id]}
            != {id(resolved[0].children[0]), id(resolved[2].children[0]),
                id(resolved[4].children[0])}):
        raise _fail("linear parameter reference census mismatch")

    induction_symbol_id = expected_sites[0].index_symbol_id
    induction = references[induction_symbol_id]
    if (len(induction) != _INDUCTION_REFERENCES
            or not {id(item.children[1]) for item in resolved}
            <= {id(item) for item in induction}):
        raise _fail("induction variable reference census mismatch")

    _check_ledger(ledger, _LANE_INDEX_LEDGER, "lane-index")
    return tuple(resolved)


def apply_linear_srgb_lane_index(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_linear_srgb_lane_index(program, source_hash, profile)
    return program
