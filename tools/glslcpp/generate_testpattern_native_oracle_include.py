#!/usr/bin/env python3
"""Fail-closed materializer for the source-bound Test Pattern oracle."""
from __future__ import annotations
import argparse, hashlib, json, math, pathlib, re, struct, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'docs/port-engineering/counted-for-parity/testpattern-oracle'
ORACLE = PACKAGE / 'testPattern-oracles.json'
REPORT = PACKAGE / 'testPattern-oracle-report.md'
GENERATOR = PACKAGE / 'testPattern_oracle_generator.mjs'
TARGET = ROOT / 'tests/oracles/testPattern_expected.inc'
COHERENCE = PACKAGE / 'testPattern-oracle-coherence.json'
COHERENCE_SCHEMA = 'noisemaker-for-cpp.testPattern.oracle-coherence.v1'
# Canonical manifest anchor; generator_sha256 is redacted to avoid a self-hash cycle.
COHERENCE_SHA256 = 'cf188502dcdab8b4bee35fb18cb77dd2c54837ae22365d95abba58b9c4a51792'
SCHEMA = 'noisemaker-for-cpp.testPattern.pixel-parity.v1'
KEY = 'synth/testPattern:testPattern'
WORD = re.compile(r'^0x[0-9a-f]{8}$')
SHA = re.compile(r'^[0-9a-f]{64}$')
EXPECTED_BEHAVIORAL_NAMES = ['digit-extraction-trip-count','glyph-bit-sample','checker-grid-clamp','pattern-bars-dispatch','bars-upper-clamp','gradient-axis','uv-axis','color-grid-golden-ratio','dot-grid-threshold']
EXPECTED_FACTORY_SHA256 = '93db20150da0135c4169afbb013c6d86c5cb4d35a24c42358ad714e1d4a4ee15'
EXPECTED_MUTATION_HASHES = {'digit-extraction-trip-count':('a1057fa61f01858f306ab6dcf5b834e3bdbb903a31c463e4dc6db8339ae2588f','9c466f62670dd6c0fb92c58f15b924e8110d9b87270a4ee283397ec853cb66ee','42320d68ba7bd9937764460c1b059247ae55b15af3a6d131f10b9226bfb8059c'),'glyph-bit-sample':('0a4914cc9b5eb2a2cafff43a74b98de946f5c5cde5760b633cd87b6949216659','10e0fa08a73f0cd151617165a96e7df8c8d14ecfc63d6f1f343559f16198939f','e933087ec5eff804bd5f77de0cf04588a9afa62948a199e08fe5c2ffdc42ffec'),'checker-grid-clamp':('79cbacea2c8d1fe3cbedcc756b26b4d16578a7d7dce85a530574893136b4b8e9','97e03d7af108facfd831680b40a4f6fde2eb95e32ab88344dc6e30d358d046b3','3cf0616bf7c56f73239e23b3ff7060176424dd466de8037840b3a462729452ee'),'pattern-bars-dispatch':('14900d33a3cc3cfe6177563c778d4b6ddb92bbff17e97fe8e4c6707a2d8d8b58','17a205440af929e287fe4dc3861923ce3d4cdf41f3ae33fe3c4e0f5439767502','e567bb5b2875500f7c7b5473c8b81df692140c6b4d4ef6ea705ad33b339d36a7'),'bars-upper-clamp':('72a76b4cb5a241f4a57b8d6453c3a3e4446239c591b8d3152a1ade23a0aa3b90','cffdb70ad4615a8c0e71f534034cf1e13b9675c44af508be64599eb365d40d4a','0c6b9c6ac8bee389ac1c72f85257d26e2d4fa363b8476b2fc110377b76a47824'),'gradient-axis':('18df2315091eb491b49874a46ea3846f105c835076d6fcf30fb56e4974aed4ab','1cac07e96cbeaa5712d57839373b476094154075749c1afafcdac92874b5bb37','a7920cbd70384c44c7d9fc8d588786f18fb6a3cd8703920b4f115c79414f1974'),'uv-axis':('648fe4b6a0bdbcd218fab7001f67a7f37524fbcf7b71875a5be0ba3967370bd3','e1410da2b889b3b91d5b444ef4e428f03dcc14e3d3d7b13f04857f5c4635a71e','3827fbd1ec9b3ad502db795d9ef682dc54081a9cc1ef89e46dd049c5e08e1c9f'),'color-grid-golden-ratio':('65f8e0708d51cd479dc2481a3798d82b630985eddf1e266aba658ffe715affa3','d2cbad71ff333de67d07ec676e352ab7f38248eb69c942950157220607c55e84','5030bbc0bf4a38fe966e404711ac3616106df3dbcc3de64d8afb20a924742cdc'),'dot-grid-threshold':('6afb33eda84032aca64633c46e349f73c357a56fc8d9ea1ed2af16af9ea6a181','00a3de96b5a7d4c27856b1c161ceaad18153433f8c03ef53bc6a385dcc685a18','85c678351a4a1dfe2b7a3b13e9b971f75a6da02f762011d9924c84596086e6ce')}
EXPECTED_RESULT_SHA256 = {'digit-extraction-trip-count':'c7d8bf3ea711e25b5d13e9f7bf42cec7d0ee09a413cffd56c1d105260844fdc9','glyph-bit-sample':'73a6dd34db18c1d9b0b4fe49070814f83241b434e6a4f6df26dd86b2df453dcf','checker-grid-clamp':'7690b47cc3a6daa6d80eb5cad34ddaf9f4f5eee7ecd740251d5bc5d5ab8bb0aa','pattern-bars-dispatch':'70d752901be242540e767a9967e3e49ba01534d75b3b9e56ee582b6467753997','bars-upper-clamp':'2b1bbc0f8ac7799d45077ea033917141822e31c03b26cc0dbde5f65ed6a68389','gradient-axis':'4c9d0d9907794c0f56c0a5e3e55ad2b054fd3f0e4217bb20e0a241158ec4f819','uv-axis':'08ff87ea05cb0e1959a69242493f66d16a27fbc0c0015f5034882b46987db36d','color-grid-golden-ratio':'f1241e4ee9e6649b3530452cd72713a1229cde43283850321e4f5fbe39cbe8e7','dot-grid-threshold':'27f94a5dc0e900b6847e243a891ed48daff250accd8e58b018fb1ef8c94055ba'}
EXPECTED_STRUCTURAL_NAMES = ['dead-cpu-float-helper','source-comment-only']
EXPECTED_STRUCTURAL_HASHES = {
 'dead-cpu-float-helper': ('fa320fa55eca7b08958ff35a1a73587ab20b1aee88de373bbfa2db326ba5a602','9f1b8ad2adc324c8514b719fa85358727e039ecaceb1f3312525dd72271b7e81'),
 'source-comment-only': ('d050918c5c5b4b61b2b8b02472e0cfc7e66fcdab9a105bf65c85f641666d8aa7','cd7bbc75a0f111484a78846c1e21fef2d58b859f1e03f9aa0ffe84afc0b98097'),
}
EXPECTED_MUTATION_METADATA = {
 'digit-extraction-trip-count': ('digit','digit extraction trip-count off-by-one',['checker-hundreds-digit']),
 'glyph-bit-sample': ('glyph','glyph bit sample forced',['checker-hundreds-digit']),
 'checker-grid-clamp': ('checker','minimum grid-size clamp',['checker-grid-clamp']),
 'pattern-bars-dispatch': ('pattern','pattern branch dispatch',['color-bars']),
 'bars-upper-clamp': ('bars','SMPTE bar upper clamp',['color-bars']),
 'gradient-axis': ('gradient','gradient axis',['gradient-nonsquare']),
 'uv-axis': ('uv','UV axis swap',['uv-map-tile']),
 'color-grid-golden-ratio': ('color','cell hue progression',['color-grid']),
 'dot-grid-threshold': ('dot','dot radius threshold',['dot-grid']),
}
EXPECTED_STRUCTURAL_METADATA = {
 'dead-cpu-float-helper': ('dead-cpu-float-helper','function cpu_float (value)','function cpu_float_unused (value)','structural-only dead helper rename'),
 'source-comment-only': ('source-comment-only','Render a number at a position within a cell','Render a number at a position within a cell (authenticated)','structural-only comment mutation'),
}
EXPECTED_MUTATION_ANCHORS = {
 'digit-extraction-trip-count': ('for (var i = 0; i < 3; i++)','for (var i = 0; i < 2; i++)'),
 'glyph-bit-sample': ('return ((GLYPH[digit] >> bitIndex) & 1) == 1;','return true;'),
 'checker-grid-clamp': ('function checkerboard (uv) {\n  \tuv = $runtime.copy(uv);\n  \tvar n = max(gridSize, 1);','function checkerboard (uv) {\n  \tuv = $runtime.copy(uv);\n  \tvar n = max(gridSize, 2);'),
 'pattern-bars-dispatch': ('if (pattern == 1)','if (pattern == 9)'),
 'bars-upper-clamp': ('clamp(bar, 0, 7)','clamp(bar, 0, 6)'),
 'gradient-axis': ('globalCoord[0] / fullResolution[0]','globalCoord[1] / fullResolution[1]'),
 'uv-axis': ('[globalCoord[0] / fullResolution[0], globalCoord[1] / fullResolution[1]]','[globalCoord[1] / fullResolution[1], globalCoord[0] / fullResolution[0]]'),
 'color-grid-golden-ratio': ('0.6180340051651001','0.5'),
 'dot-grid-threshold': ('smoothstep(0.11999999731779099, 0.15000000596046448, dist)','smoothstep(0.5, 0.6000000238418579, dist)'),
}
EXPECTED_CLOSURE = {'src/csl/glsl-kernel.js': 'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa', 'src/csl/glsl-runtime.js': 'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072', 'src/csl/runtime.js': 'a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee', 'src/effects/adapters/bit-effects.js': '5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7', 'src/effects/adapters/crt.js': 'c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc', 'src/effects/adapters/f32-color.js': 'b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046', 'src/effects/adapters/fractal.js': '0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29', 'src/effects/adapters/index.js': '40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267', 'src/effects/adapters/julia.js': '0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5', 'src/effects/adapters/median.js': 'e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583', 'src/effects/adapters/palette.js': '8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452', 'src/effects/adapters/snow.js': '202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366', 'src/effects/catalog.js': 'd8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4', 'src/effects/definition.js': 'fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02', 'src/effects/generated/canonical-adapter-data.js': 'ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab', 'src/effects/generated/canonical-kernels.js': '66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe', 'src/effects/generated/kernels.js': 'b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01', 'src/effects/generated/upstream-snapshot.js': 'e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090', 'src/effects/registry.js': '8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618', 'src/runtime/pass-runner.js': 'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa', 'src/runtime/sampler.js': '1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328', 'src/runtime/surface.js': '0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'}
EXPECTED_CASES = [
    {'name': 'checker-hundreds-digit', 'width': 1, 'height': 1, 'gridSize': 12, 'pattern': 0, 'tileOffset': [19, 27], 'fullResolution': [1000, 1000], 'phase': 1, 'output_f32_sha256': 'f6bb1294da2f78cd935b01c7656280df5eaa0439e9d97bc03775825a41a508e4', 'output_rgba8_sha256': 'ad95131bc0b799c0b1af477fb14fcf26a6a9f76079e48bf090acb7e8367bfd0e', 'alpha': {'f32_word': '0x3f800000', 'rgba8_byte': 255}},
    {'name': 'checker-single-digit', 'width': 1, 'height': 1, 'gridSize': 3, 'pattern': 0, 'tileOffset': [499.5, 499.5], 'fullResolution': [1000, 1000], 'phase': 2, 'output_f32_sha256': '7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e', 'output_rgba8_sha256': 'e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332', 'alpha': {'f32_word': '0x3f800000', 'rgba8_byte': 255}},
    {'name': 'checker-grid-clamp', 'width': 2, 'height': 2, 'gridSize': 0, 'pattern': 0, 'tileOffset': [0, 0], 'fullResolution': [2, 2], 'phase': 3, 'output_f32_sha256': '9628e545ed3ac074e5a6cbf542a642b62482fbfca9b4cb3ea4743a1874256e37', 'output_rgba8_sha256': '5ac6a5945f16500911219129984ba8b387a06f24fe383ce4e81a73294065461b', 'alpha': {'f32_word': '0x3f800000', 'rgba8_byte': 255}},
    {'name': 'color-bars', 'width': 8, 'height': 1, 'gridSize': 4, 'pattern': 1, 'tileOffset': [0, 0], 'fullResolution': [8, 1], 'phase': 4, 'output_f32_sha256': '6db8f03150c8a0c7721300683cc43b5eae30cd2a528113f6bf127769c45f3b03', 'output_rgba8_sha256': '856c5f8dcc3ef73f3bae698cde3c0aa91d26a35638aae001fcc2ee1b08eaf5e0', 'alpha': {'f32_word': '0x3f800000', 'rgba8_byte': 255}},
    {'name': 'gradient-nonsquare', 'width': 4, 'height': 3, 'gridSize': 4, 'pattern': 2, 'tileOffset': [1, 0], 'fullResolution': [8, 3], 'phase': 5, 'output_f32_sha256': '28d6aa59331d654196bd4696252c3e81370e09a8dcac8a2e836e363adc345798', 'output_rgba8_sha256': 'b2e526d8f801cf1a080e4a54eaec499dfb9224e94e2d29c5961c9c1b89a414a2', 'alpha': {'f32_word': '0x3f800000', 'rgba8_byte': 255}},
    {'name': 'uv-map-tile', 'width': 3, 'height': 2, 'gridSize': 3, 'pattern': 3, 'tileOffset': [2, 1], 'fullResolution': [6, 4], 'phase': 6, 'output_f32_sha256': '462ac905c1671ec6cbbf7ff9817d6e57d88e24793d73a96126b8514e4dec0420', 'output_rgba8_sha256': '2b2c6c1decfe3f06f0be5e78e77d88a654933406e9214788d87fba15a3f8fe53', 'alpha': {'f32_word': '0x3f800000', 'rgba8_byte': 255}},
    {'name': 'grid-lines', 'width': 5, 'height': 4, 'gridSize': 3, 'pattern': 4, 'tileOffset': [0, 0], 'fullResolution': [5, 4], 'phase': 7, 'output_f32_sha256': 'eb66ad4ac07d220d72032a42d732cf266339da9c8566093c868b8285d4ec033c', 'output_rgba8_sha256': '89c7c79931afa67d559f7cf332ab5a65a379ebf5e4fa2d997535c364af2c24a8', 'alpha': {'f32_word': '0x3f800000', 'rgba8_byte': 255}},
    {'name': 'color-grid', 'width': 4, 'height': 3, 'gridSize': 4, 'pattern': 5, 'tileOffset': [0, 0], 'fullResolution': [4, 3], 'phase': 8, 'output_f32_sha256': 'a5fe647f7b56090d8fd56ad17be335977cc423f97c6fdba7a60c8d5d300aaf19', 'output_rgba8_sha256': 'e1396e97656f8095d998762f0c08d1f208067de33bad4d4c91ea8dc974bce0a1', 'alpha': {'f32_word': '0x3f800000', 'rgba8_byte': 255}},
    {'name': 'dot-grid', 'width': 5, 'height': 5, 'gridSize': 4, 'pattern': 6, 'tileOffset': [0, 0], 'fullResolution': [5, 5], 'phase': 9, 'output_f32_sha256': '45958e7de2b03e705d949058a74871b720c933b6690af3237dc550276121f3ff', 'output_rgba8_sha256': 'eec6872072e956535878ec2c0e3124d23b5ba54a2f7f172e1c2841eeee6b5be4', 'alpha': {'f32_word': '0x3f800000', 'rgba8_byte': 255}},
]

class OracleError(RuntimeError): pass

def strict_json(payload: bytes):
    if type(payload) is not bytes: raise OracleError('JSON payload must be bytes')
    if len(payload) > 8 * 1024 * 1024: raise OracleError('JSON payload exceeds strict size limit')
    def pairs(items):
        out = {}
        for k, v in items:
            if type(k) is not str: raise OracleError('JSON object key must be a string')
            if k in out: raise OracleError(f'duplicate JSON key: {k}')
            out[k] = v
        return out
    def constant(value):
        raise OracleError(f'nonfinite JSON scalar: {value}')
    try: return json.loads(payload, object_pairs_hook=pairs, parse_int=int, parse_float=float, parse_constant=constant)
    except (OracleError, json.JSONDecodeError, ValueError, UnicodeDecodeError, TypeError, RecursionError) as exc: raise OracleError(f'invalid JSON: {exc}') from exc

def sidecar(path: pathlib.Path, payload: bytes) -> str:
    return f'{hashlib.sha256(payload).hexdigest()}  {path.name}\n'

def checked(path: pathlib.Path) -> bytes:
    sc = pathlib.Path(f'{path}.sha256')
    if not path.is_file() or not sc.is_file(): raise OracleError(f'missing checked asset or sidecar: {path.name}')
    try:
        payload = path.read_bytes(); side = sc.read_text()
    except (OSError, UnicodeError) as exc:
        raise OracleError(f'unreadable checked asset: {path.name}') from exc
    if side != sidecar(path, payload): raise OracleError(f'checksum sidecar drift: {path.name}')
    return payload

def anchored_coherence_payload(payload: bytes) -> bytes:
    try:
        text = payload.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise OracleError('coherence manifest is not UTF-8') from exc
    redacted, count = re.subn(r'("generator_sha256"\s*:\s*)"[0-9a-f]{64}"', r'\1"<generator-sha256>"', text, count=1)
    if count != 1:
        raise OracleError('coherence generator hash field missing')
    return redacted.encode('utf-8')

def validate_coherence_payload(payload: bytes):
    if hashlib.sha256(anchored_coherence_payload(payload)).hexdigest() != COHERENCE_SHA256:
        raise OracleError('coherence content anchor drift')
    doc = strict_json(payload)
    reject_paths(doc, 'coherence')
    if obj(doc, {'schema','generator_sha256','report_sha256','oracle_sha256','include_sha256'}, 'coherence')['schema'] != COHERENCE_SCHEMA:
        raise OracleError('coherence schema drift')
    for field in ('generator_sha256','report_sha256','oracle_sha256','include_sha256'):
        digest(doc[field], f'coherence.{field}')
    return doc

def coherence(require_target=False):
    payload = checked(COHERENCE)
    doc = validate_coherence_payload(payload)
    files = {'generator':GENERATOR, 'report':REPORT, 'oracle':ORACLE}
    for name, path in files.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != doc[f'{name}_sha256']:
            raise OracleError(f'coherence hash drift: {name}')
    if require_target and hashlib.sha256(checked(TARGET)).hexdigest() != doc['include_sha256']:
        raise OracleError('coherence hash drift: include')
    return doc

def self_test_coherence_forgery():
    candidate = json.loads(checked(COHERENCE).decode('utf-8'))
    candidate['report_sha256'] = '0' * 64
    payload = (json.dumps(candidate, indent=2) + '\n').encode('utf-8')
    try:
        validate_coherence_payload(payload)
    except OracleError:
        return
    raise OracleError('coherence forgery probe unexpectedly accepted')

def reject_paths(value, label='document'):
    if isinstance(value, str):
        if value.lower().startswith('file://') or re.match(r'^(?:[A-Za-z]:[\\/]|\\\\|/)', value):
            raise OracleError(f'{label}: absolute or file URI path')
        if re.search(r'(?:^|[\\/])~(?=[\\/]|$)', value):
            raise OracleError(f'{label}: tilde path')
        if re.search(r'(?:^|[\\/])\$(?:\{[A-Za-z_][A-Za-z0-9_]*\}|[A-Za-z_][A-Za-z0-9_]*)(?=[\\/]|$)', value):
            raise OracleError(f'{label}: environment-looking path')
        if re.search(r'(?:^|[\\/])(Users|private|tmp|home)(?:[\\/]|$)', value):
            raise OracleError(f'{label}: reserved path segment')
    if isinstance(value, list):
        for i, x in enumerate(value): reject_paths(x, f'{label}[{i}]')
    elif isinstance(value, dict):
        for k, x in value.items():
            if isinstance(k, str): reject_paths(k, f'{label}.<key>')
            reject_paths(x, f'{label}.{k}')

def obj(value, keys, label):
    if type(value) is not dict or set(value) != set(keys): raise OracleError(f'{label}: exact field set')
    return value
def string(value, label):
    if type(value) is not str: raise OracleError(f'{label}: string required')
    return value
def boolean(value, label):
    if type(value) is not bool: raise OracleError(f'{label}: bool required')
    return value
def integer(value, label):
    if type(value) is not int: raise OracleError(f'{label}: exact integer required')
    return value
def finite(value, label):
    if type(value) not in (int, float) or not math.isfinite(float(value)): raise OracleError(f'{label}: finite number required')
    return value
def digest(value, label):
    value = string(value, label)
    if not SHA.fullmatch(value): raise OracleError(f'{label}: malformed SHA-256')
    return value
def words(value, count, label):
    if type(value) is not list or len(value) != count or any(type(x) is not str or not WORD.fullmatch(x) for x in value): raise OracleError(f'{label}: malformed uint32 words')
def bytes8(value, count, label):
    if type(value) is not list or len(value) != count or any(type(x) is not int or not 0 <= x <= 255 for x in value): raise OracleError(f'{label}: malformed RGBA8 bytes')
def pack_words(value): return b''.join(struct.pack('<I', int(x, 16)) for x in value)

def validate(doc):
    reject_paths(doc)
    top = obj(doc, {'schema','schema_version','program_key','effect_key','runtime_key','corpus_revision','upstream_revision','factory','binding_names','binding_abi','source_uniform_abi','input_contract','exactness_contract','comparer_self_tests','authority','provenance','render_cases','mutation_contract','behavioral_mutation_ledger','structural_mutation_ledger','control_group','claim_boundaries'}, 'document')
    if (top['schema'], top['schema_version'], top['program_key'], top['effect_key'], top['runtime_key'], top['corpus_revision'], top['upstream_revision']) != (SCHEMA, 1, KEY, 'synth/testPattern', KEY, 'a024dc3a960cc44af454abc7aebce50456c194e6', '117a236679d1db3ab8f0e278230ece277b57564c'): raise OracleError('identity drift')
    integer(top['schema_version'], 'schema_version'); string(top['corpus_revision'], 'corpus_revision'); string(top['upstream_revision'], 'upstream_revision')
    factory = obj(top['factory'], {'name','text_sha256','public_direct_identity','canonical_own_key','adapter_own_key'}, 'factory'); string(factory['name'],'factory.name'); digest(factory['text_sha256'],'factory.text_sha256');
    if factory['text_sha256'] != EXPECTED_FACTORY_SHA256: raise OracleError('factory text pin drift'); [boolean(factory[k],f'factory.{k}') for k in ('public_direct_identity','canonical_own_key','adapter_own_key')]
    if factory != {'name':'canonicalFactory277','text_sha256':factory['text_sha256'],'public_direct_identity':True,'canonical_own_key':True,'adapter_own_key':False}: raise OracleError('factory identity flags drift')
    if top['binding_names'] != ['resolution','tileOffset','fullResolution','gridSize','pattern']: raise OracleError('binding names drift')
    if top['binding_abi'] != {'resolution':'Vec2','tileOffset':'Vec2','fullResolution':'Vec2','gridSize':'int32','pattern':'int32'}: raise OracleError('runtime ABI drift')
    if top['source_uniform_abi'] != {'resolution':'vec2','tileOffset':'vec2','fullResolution':'vec2','gridSize':'int','pattern':'int'}: raise OracleError('source ABI drift')
    inp_contract = obj(top['input_contract'], {'kind','runtime_input_path','lifetime_claimed','immutability_claimed','reason'}, 'input_contract')
    [boolean(inp_contract[k], f'input_contract.{k}') for k in ('lifetime_claimed','immutability_claimed')]
    if inp_contract != {'kind':'source-only','runtime_input_path':'none','lifetime_claimed':False,'immutability_claimed':False,'reason':'Test Pattern has no sampler or input texture path'}: raise OracleError('input contract drift')
    ex = obj(top['exactness_contract'], {'float32','rgba8','tolerance','comparison_order'}, 'exactness_contract'); [string(ex[k],f'exactness_contract.{k}') for k in ex]
    if ex != {'float32':'raw little-endian uint32 words; signed zero and NaN payloads significant','rgba8':'complete independent RGBA8 byte arrays','tolerance':'none','comparison_order':'dimensions, counts, every float32 word, every RGBA8 byte'}: raise OracleError('exactness drift')
    cmp = obj(top['comparer_self_tests'], {'good_equal','dimensions_before_access','short_count','long_count','signed_zero','nan_payload','rgba8_independent','first_mismatch_reported'}, 'comparer_self_tests'); [boolean(v,f'comparer_self_tests.{k}') for k,v in cmp.items()]
    if not all(cmp.values()): raise OracleError('comparer self-test failure')
    auth = obj(top['authority'], {'oracle','live_checkout_rejected','leaf_symlink_rejected','parent_alias_accepted','import_closure'}, 'authority'); string(auth['oracle'],'authority.oracle'); [boolean(auth[k],f'authority.{k}') for k in ('live_checkout_rejected','leaf_symlink_rejected','parent_alias_accepted')]
    if auth['oracle'] != 'live canonical factory from immutable CPU snapshot' or auth['live_checkout_rejected'] is not True or auth['leaf_symlink_rejected'] is not True or auth['parent_alias_accepted'] is not True: raise OracleError('authority contract drift')
    closure = auth['import_closure']
    if type(closure) is not list or len(closure) != 22: raise OracleError('closure count drift')
    if [(x.get('relative_path'), x.get('sha256')) for x in closure] != sorted(EXPECTED_CLOSURE.items()): raise OracleError('exact closure pin drift')
    for i, item in enumerate(closure): item = obj(item, {'relative_path','sha256'}, f'closure[{i}]'); string(item['relative_path'],f'closure[{i}].relative_path'); digest(item['sha256'],f'closure[{i}].sha256')
    prov = obj(top['provenance'], {'source','factory','cpu_root'}, 'provenance'); string(prov['cpu_root'],'provenance.cpu_root')
    if prov['cpu_root'] != '<immutable-cpu-snapshot-root>': raise OracleError('CPU root must remain unset in JSON')
    source = obj(prov['source'], {'relative_path','bytes','sha256'}, 'provenance.source'); string(source['relative_path'],'source.relative_path'); integer(source['bytes'],'source.bytes'); digest(source['sha256'],'source.sha256')
    if source != {'relative_path':'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/testPattern/testPattern.glsl','bytes':5919,'sha256':'f913300a1312c6630d56fa1cc2faf2cb17fe0643d832473fdec7b66dd373cb20'}: raise OracleError('source pin drift')
    factory_pin = obj(prov['factory'], {'relative_path','sha256'}, 'provenance.factory'); string(factory_pin['relative_path'],'factory.relative_path'); digest(factory_pin['sha256'],'factory.sha256')
    if factory_pin != {'relative_path':'src/effects/generated/canonical-kernels.js','sha256':EXPECTED_CLOSURE['src/effects/generated/canonical-kernels.js']}: raise OracleError('factory provenance pin drift')
    cases = top['render_cases']
    if type(cases) is not list or len(cases) != 9: raise OracleError('case census drift')
    names = set()
    for i, case in enumerate(cases):
        case = obj(case, {'name','width','height','gridSize','pattern','tileOffset','fullResolution','phase','controls','output_f32_words_le','output_f32_sha256','output_rgba8_bytes','output_rgba8_sha256','alpha','repeat_identical_float32','repeat_identical_rgba8','repeat_distinct_data_objects','repeat_distinct_backing_buffers'}, f'case[{i}]')
        if case['name'] in names: raise OracleError('duplicate case')
        names.add(case['name']); integer(case['width'],f'case[{i}].width'); integer(case['height'],f'case[{i}].height'); integer(case['gridSize'],f'case[{i}].gridSize'); integer(case['pattern'],f'case[{i}].pattern'); integer(case['phase'],f'case[{i}].phase')
        expected = EXPECTED_CASES[i]
        for field in ('name','width','height','gridSize','pattern','tileOffset','fullResolution','phase'):
            if case[field] != expected[field]: raise OracleError(f'case[{i}].{field}: exact fixture drift')
        if case['width'] <= 0 or case['height'] <= 0 or not 0 <= case['pattern'] <= 6: raise OracleError('case dimensions/pattern drift')
        for k in ('tileOffset','fullResolution'):
            if type(case[k]) is not list or len(case[k]) != 2: raise OracleError(f'case.{k}: Vec2 required')
            [finite(x,f'case.{k}') for x in case[k]]
            if any(type(case[k][j]) is not type(expected[k][j]) for j in range(2)): raise OracleError(f'case.{i}.{k}: exact scalar fixture drift')
        controls = obj(case['controls'], {'resolution','tileOffset','fullResolution','gridSize','pattern'}, f'case[{i}].controls')
        if controls['resolution'] != [case['width'], case['height']] or controls['tileOffset'] != case['tileOffset'] or controls['fullResolution'] != case['fullResolution'] or controls['pattern'] != case['pattern'] or controls['gridSize'] != case['gridSize']: raise OracleError('control mismatch')
        integer(controls['gridSize'], f'case[{i}].controls.gridSize'); integer(controls['pattern'], f'case[{i}].controls.pattern')
        if type(controls['resolution']) is not list or len(controls['resolution']) != 2 or any(type(x) is not int for x in controls['resolution']): raise OracleError('control resolution type mismatch')
        for k in ('tileOffset','fullResolution'):
            if type(controls[k]) is not list or len(controls[k]) != 2 or any(type(x) not in (int,float) or not math.isfinite(float(x)) for x in controls[k]): raise OracleError(f'control {k} type mismatch')
            if any(type(controls[k][j]) is not type(case[k][j]) for j in range(2)): raise OracleError(f'control {k} scalar type mismatch')
        n=case['width']*case['height']*4
        words(case['output_f32_words_le'],n,'output.words'); bytes8(case['output_rgba8_bytes'],n,'output.rgba8'); digest(case['output_f32_sha256'],'output.f32_sha256'); digest(case['output_rgba8_sha256'],'output.rgba8_sha256')
        if case['output_f32_sha256'] != expected['output_f32_sha256'] or case['output_rgba8_sha256'] != expected['output_rgba8_sha256']: raise OracleError('output fixture pin drift')
        if hashlib.sha256(pack_words(case['output_f32_words_le'])).hexdigest() != case['output_f32_sha256'] or hashlib.sha256(bytes(case['output_rgba8_bytes'])).hexdigest() != case['output_rgba8_sha256']: raise OracleError('output hash mismatch')
        alpha=obj(case['alpha'], {'f32_word','rgba8_byte'}, f'case[{i}].alpha'); string(alpha['f32_word'], 'alpha.f32_word'); integer(alpha['rgba8_byte'],'alpha.rgba8_byte')
        if alpha != expected['alpha']: raise OracleError('alpha fixture pin drift')
        [boolean(case[k],f'case.{k}') for k in ('repeat_identical_float32','repeat_identical_rgba8','repeat_distinct_data_objects','repeat_distinct_backing_buffers')]
        if any(case[k] is not True for k in ('repeat_identical_float32','repeat_identical_rgba8','repeat_distinct_data_objects','repeat_distinct_backing_buffers')): raise OracleError('runtime control result drift')
    ledger = top['behavioral_mutation_ledger']; contract=obj(top['mutation_contract'], {'behavioral_names','structural_names','control_group'}, 'mutation_contract')
    if contract['behavioral_names'] != EXPECTED_BEHAVIORAL_NAMES or contract['structural_names'] != EXPECTED_STRUCTURAL_NAMES or contract['control_group'] != 'all patterns and source-specific branches': raise OracleError('mutation contract drift')
    ledger = top['behavioral_mutation_ledger']
    if len(ledger) != 9 or [m['name'] for m in ledger] != EXPECTED_BEHAVIORAL_NAMES: raise OracleError('mutation census drift')
    for i,m in enumerate(ledger):
        m=obj(m, {'name','group','mechanism','source_relative_path','source_anchor','replacement','anchor_occurrence_count','source_anchor_sha256','replacement_sha256','canonical_factory_sha256','mutated_factory_sha256','results','result_sha256','witness_cases','required_witness_results'}, f'mutation[{i}]'); [string(m[k],f'mutation.{k}') for k in ('name','group','mechanism','source_relative_path','source_anchor','replacement','canonical_factory_sha256','mutated_factory_sha256')]; integer(m['anchor_occurrence_count'],'mutation.anchor_occurrence_count'); [digest(m[k],f'mutation.{k}') for k in ('source_anchor_sha256','replacement_sha256','canonical_factory_sha256','mutated_factory_sha256')]
        if (m['source_anchor'], m['replacement']) != EXPECTED_MUTATION_ANCHORS[m['name']]: raise OracleError('mutation source anchor drift')
        metadata = EXPECTED_MUTATION_METADATA[m['name']]
        if (m['group'], m['mechanism'], m['source_relative_path'], m['anchor_occurrence_count'], m['witness_cases']) != (metadata[0], metadata[1], source['relative_path'], 1, metadata[2]): raise OracleError('mutation metadata drift')
        expected_hashes = EXPECTED_MUTATION_HASHES[m['name']]
        if (m['source_anchor_sha256'],m['replacement_sha256'],m['mutated_factory_sha256']) != expected_hashes: raise OracleError('mutation hash pin drift')
        if m['canonical_factory_sha256'] != EXPECTED_FACTORY_SHA256 or m['mutated_factory_sha256'] == '0'*64 or m['canonical_factory_sha256'] == m['mutated_factory_sha256'] or not m['witness_cases'] or not m['required_witness_results']: raise OracleError('mutation identity/witness drift')
        if m['result_sha256'] != EXPECTED_RESULT_SHA256[m['name']] or hashlib.sha256(json.dumps({'name':m['name'],'results':m['results']}, separators=(',', ':')).encode()).hexdigest() != m['result_sha256']: raise OracleError('mutation result hash mismatch')
        if len(m['results']) != 9 or len(set(r['case'] for r in m['results'])) != 9: raise OracleError('mutation result cardinality drift')
        if any(type(x) is not str for x in m['witness_cases']) or not m['witness_cases']: raise OracleError('mutation witness cases drift')
        for row in m['results']:
            row=obj(row, {'case','differs','reason','changed_float32_lanes','changed_rgba8_bytes','first_mismatch'}, 'mutation.result'); string(row['case'],'result.case'); boolean(row['differs'],'result.differs'); integer(row['changed_float32_lanes'],'result.float32'); integer(row['changed_rgba8_bytes'],'result.rgba8')
            if row['changed_float32_lanes'] < 0 or row['changed_rgba8_bytes'] < 0: raise OracleError('mutation witness result drift')
            if row['differs'] != (row['changed_float32_lanes'] > 0 or row['changed_rgba8_bytes'] > 0): raise OracleError('mutation witness result drift')
            if type(row['first_mismatch']) is not int and row['first_mismatch'] is not None: raise OracleError('mutation first mismatch type drift')
        if len(m['required_witness_results']) != len(m['witness_cases']): raise OracleError('required witness cardinality drift')
        result_by_case = {r['case']: r for r in m['results']}
        for witness in m['required_witness_results']:
            witness=obj(witness, {'case','differs','reason','changed_float32_lanes','changed_rgba8_bytes','first_mismatch'}, 'mutation.required_witness')
            if witness['case'] not in m['witness_cases'] or result_by_case.get(witness['case']) != witness or not witness['differs'] or witness['changed_float32_lanes'] <= 0 or witness['changed_rgba8_bytes'] <= 0: raise OracleError('missing dual-lane witness')
    if len(top['structural_mutation_ledger']) != 2 or [x.get('name') for x in top['structural_mutation_ledger']] != EXPECTED_STRUCTURAL_NAMES: raise OracleError('structural mutation contract drift')
    for x in top['structural_mutation_ledger']:
        x=obj(x, {'name','anchor','replacement','mechanism','source_relative_path','source_anchor_sha256','replacement_sha256','no_pixel_witness_claimed'}, 'structural mutation')
        expected_structural = EXPECTED_STRUCTURAL_METADATA[x['name']]
        if (x['name'], x['anchor'], x['replacement'], x['mechanism'], x['source_relative_path']) != (expected_structural[0], expected_structural[1], expected_structural[2], expected_structural[3], source['relative_path']): raise OracleError('structural mutation metadata drift')
        boolean(x['no_pixel_witness_claimed'], 'structural.no_pixel_witness_claimed')
        if not x['no_pixel_witness_claimed'] or not x['anchor'] or not x['replacement'] or not x['mechanism']: raise OracleError('structural mutation witness claim drift')
        if (x['source_anchor_sha256'], x['replacement_sha256']) != EXPECTED_STRUCTURAL_HASHES[x['name']]: raise OracleError('structural mutation hash drift')
    group=obj(top['control_group'], {'repeatability','independent_output_storage','public_direct_identity','canonical_own_key','adapter_own_key'}, 'control_group')
    repeatability=obj(group['repeatability'], {'case','identical_float32','identical_rgba8'}, 'control_group.repeatability')
    storage=obj(group['independent_output_storage'], {'case','distinct_data_objects','distinct_backing_buffers'}, 'control_group.independent_output_storage')
    [boolean(repeatability[k], f'control_group.repeatability.{k}') for k in ('identical_float32','identical_rgba8')]
    [boolean(storage[k], f'control_group.independent_output_storage.{k}') for k in ('distinct_data_objects','distinct_backing_buffers')]
    [boolean(group[k], f'control_group.{k}') for k in ('public_direct_identity','canonical_own_key','adapter_own_key')]
    expected_group={'repeatability':{'case':'color-bars','identical_float32':True,'identical_rgba8':True},'independent_output_storage':{'case':'color-bars','distinct_data_objects':True,'distinct_backing_buffers':True},'public_direct_identity':True,'canonical_own_key':True,'adapter_own_key':False}
    if group != expected_group: raise OracleError('control group drift')
    claims=obj(top['claim_boundaries'], {'authority','runtime','input','structural_mutations'}, 'claim_boundaries')
    if claims != {'authority':'immutable CPU snapshot only','runtime':'exact Float32 and RGBA8 bytes','input':'source-only kernel; no input lifetime or immutability claim','structural_mutations':'structure authenticated; no pixel witness claimed'}: raise OracleError('claim boundary drift')
    return doc

def cpp_string(x): return json.dumps(x, ensure_ascii=False)
def cpp_float(x):
    value = float(x)
    if value == 0.0: return '0.0f'
    text = format(value, '.17g')
    if '.' not in text and 'e' not in text and 'E' not in text: text += '.0'
    return text + 'f'
def cpp_words(values): return ','.join(f'{int(x, 16)}u' for x in values)
def cpp_bytes(values): return ','.join(f'{int(x)}u' for x in values)
def cpp_vec2(values): return 'Vec2Control{{{{{}, {}}}}}'.format(cpp_float(values[0]), cpp_float(values[1]))
def cpp_result(row):
    first = -1 if row['first_mismatch'] is None else row['first_mismatch']
    return 'MutationResult{' + ','.join([
        cpp_string(row['case']), cpp_string(row['reason']),
        str(row['changed_float32_lanes']) + 'u', str(row['changed_rgba8_bytes']) + 'u',
        str(row['differs']).lower(), str(first) + 'll']) + '}'

def materialize(doc):
    bindings = ', '.join('{'+cpp_string(k)+','+cpp_string(doc['binding_abi'][k])+','+cpp_string(doc['source_uniform_abi'][k])+'}' for k in doc['binding_names'])
    lines = [
        '// Generated by generate_testpattern_native_oracle_include.py; exact checked JSON authority.',
        '#pragma once', '#include <array>', '#include <cstddef>', '#include <cstdint>', '#include <string_view>', '#include <vector>',
        'namespace noisemaker_testpattern_oracle {',
        'enum class MismatchKind : std::uint8_t { None, Dimensions, FloatCount, Rgba8Count, Float32, Rgba8 };',
        'struct Binding { std::string_view name, runtime_abi, source_abi; };',
        'struct Vec2Control { std::array<float,2> values; };',
        'struct Controls { Vec2Control resolution, tile_offset, full_resolution; std::int32_t grid_size, pattern; };',
        'struct InputContract { std::string_view kind,runtime_input_path,reason; bool lifetime_claimed,immutability_claimed; };',
        'struct Case { std::string_view name; std::uint32_t width,height,phase; std::int32_t grid_size,pattern; Controls controls; std::vector<std::uint32_t> output_float_words; std::vector<std::uint8_t> output_rgba8; std::string_view output_f32_sha256,output_rgba8_sha256,alpha_f32_word; std::uint8_t alpha_rgba8_byte; bool repeat_float32,repeat_rgba8,distinct_data_objects,distinct_backing_buffers; };',
        'struct MutationResult { std::string_view case_name,reason; std::uint32_t changed_float32_lanes,changed_rgba8_bytes; bool differs; std::int64_t first_mismatch; };',
        'struct Mutation { std::string_view name,group,mechanism,source_relative_path,source_anchor,replacement,source_anchor_sha256,replacement_sha256,canonical_factory_sha256,mutated_factory_sha256,result_sha256; std::vector<MutationResult> results,required_witness_results; std::vector<std::string_view> witness_cases; };',
        'struct StructuralMutation { std::string_view name,source_relative_path,anchor,replacement,mechanism,source_anchor_sha256,replacement_sha256; bool no_pixel_witness_claimed; };',
        'inline constexpr std::string_view kSchema='+cpp_string(doc['schema'])+';',
        'inline constexpr std::uint32_t kSchemaVersion='+str(doc['schema_version'])+'u;',
        'inline constexpr std::string_view kProgramKey='+cpp_string(doc['program_key'])+';',
        'inline constexpr std::string_view kEffectKey='+cpp_string(doc['effect_key'])+';',
        'inline constexpr std::string_view kRuntimeKey='+cpp_string(doc['runtime_key'])+';',
        'inline constexpr std::string_view kCorpusRevision='+cpp_string(doc['corpus_revision'])+';',
        'inline constexpr std::string_view kUpstreamRevision='+cpp_string(doc['upstream_revision'])+';',
        'inline constexpr std::string_view kSourceRelativePath='+cpp_string(doc['provenance']['source']['relative_path'])+';',
        'inline constexpr std::size_t kSourceBytes='+str(doc['provenance']['source']['bytes'])+'U;',
        'inline constexpr std::string_view kSourceSha256='+cpp_string(doc['provenance']['source']['sha256'])+';',
        'inline constexpr std::string_view kFactoryName='+cpp_string(doc['factory']['name'])+';',
        'inline constexpr std::string_view kFactoryRelativePath='+cpp_string(doc['provenance']['factory']['relative_path'])+';',
        'inline constexpr std::string_view kFactorySha256='+cpp_string(doc['factory']['text_sha256'])+';',
        'inline constexpr std::string_view kFactoryClosureSha256='+cpp_string(doc['provenance']['factory']['sha256'])+';',
        'inline constexpr InputContract kInputContract{'+cpp_string(doc['input_contract']['kind'])+','+cpp_string(doc['input_contract']['runtime_input_path'])+','+cpp_string(doc['input_contract']['reason'])+','+str(doc['input_contract']['lifetime_claimed']).lower()+','+str(doc['input_contract']['immutability_claimed']).lower()+'};',
        'inline constexpr std::string_view kReportSha256='+cpp_string(coherence(False)['report_sha256'])+';',
        'inline constexpr std::string_view kOracleSha256='+cpp_string(coherence(False)['oracle_sha256'])+';',
        'inline constexpr std::array<Binding,5> kBindingAbi = {{'+bindings+'}};',
        'inline constexpr bool kExactFloat32=true, kExactRgba8=true, kSignedZeroSignificant=true, kNaNPayloadSignificant=true, kToleranceNone=true;',
        'inline constexpr std::string_view kComparisonOrder="dimensions, counts, every float32 word, every RGBA8 byte";',
        'inline constexpr bool kPublicDirectIdentity=true, kCanonicalOwnKey=true, kAdapterOwnKey=false;',
        'inline const std::array<Case,'+str(len(doc['render_cases']))+'> kCases = {',
    ]
    for c in doc['render_cases']:
        controls = c['controls']
        fields = [
            cpp_string(c['name']), f"{c['width']}u", f"{c['height']}u", f"{c['phase']}u", str(c['gridSize']), str(c['pattern']),
            'Controls{'+cpp_vec2(controls['resolution'])+','+cpp_vec2(controls['tileOffset'])+','+cpp_vec2(controls['fullResolution'])+','+str(controls['gridSize'])+','+str(controls['pattern'])+'}',
            '{'+cpp_words(c['output_f32_words_le'])+'}', '{'+cpp_bytes(c['output_rgba8_bytes'])+'}',
            cpp_string(c['output_f32_sha256']), cpp_string(c['output_rgba8_sha256']),
            cpp_string(c['alpha']['f32_word']), str(c['alpha']['rgba8_byte'])+'u',
            str(c['repeat_identical_float32']).lower(), str(c['repeat_identical_rgba8']).lower(),
            str(c['repeat_distinct_data_objects']).lower(), str(c['repeat_distinct_backing_buffers']).lower(),
        ]
        lines.append('Case{'+','.join(fields)+'},')
    lines.append('};')
    lines.extend(['', 'inline const std::array<Mutation,9> kMutations = {'])
    for m in doc['behavioral_mutation_ledger']:
        results = ','.join(cpp_result(row) for row in m['results'])
        required = ','.join(cpp_result(row) for row in m['required_witness_results'])
        witnesses = ','.join(cpp_string(x) for x in m['witness_cases'])
        fields = [cpp_string(m['name']), cpp_string(m['group']), cpp_string(m['mechanism']), cpp_string(m['source_relative_path']), cpp_string(m['source_anchor']), cpp_string(m['replacement']), cpp_string(m['source_anchor_sha256']), cpp_string(m['replacement_sha256']), cpp_string(m['canonical_factory_sha256']), cpp_string(m['mutated_factory_sha256']), cpp_string(m['result_sha256']), '{'+results+'}', '{'+required+'}', '{'+witnesses+'}']
        lines.append('Mutation{'+','.join(fields)+'},')
    lines.extend(['};', '', 'struct MutationWitnessView { std::string_view mutation_name,case_name; std::uint32_t changed_float32_lanes,changed_rgba8_bytes; std::int64_t first_mismatch; };'])
    lines.append('inline const std::array<MutationWitnessView,9> kMutationWitnesses = {')
    for m in doc['behavioral_mutation_ledger']:
        for row in m['required_witness_results']:
            first = -1 if row['first_mismatch'] is None else row['first_mismatch']
            lines.append('MutationWitnessView{'+','.join([cpp_string(m['name']),cpp_string(row['case']),str(row['changed_float32_lanes'])+'u',str(row['changed_rgba8_bytes'])+'u',str(first)+'ll'])+'},')
    lines.extend(['};', ''])
    structural = ','.join('StructuralMutation{'+','.join([cpp_string(x['name']),cpp_string(x['source_relative_path']),cpp_string(x['anchor']),cpp_string(x['replacement']),cpp_string(x['mechanism']),cpp_string(x['source_anchor_sha256']),cpp_string(x['replacement_sha256']),str(x['no_pixel_witness_claimed']).lower()])+'}' for x in doc['structural_mutation_ledger'])
    lines.extend([
        'inline constexpr std::array<StructuralMutation,2> kStructuralMutations = {{'+structural+'}};',
        '',
        'struct ControlGroup { std::string_view repeatability_case,storage_case; bool repeat_float32,repeat_rgba8,distinct_data_objects,distinct_backing_buffers,public_direct_identity,canonical_own_key,adapter_own_key; };',
        'inline constexpr ControlGroup kControlGroup{'+cpp_string(doc['control_group']['repeatability']['case'])+','+cpp_string(doc['control_group']['independent_output_storage']['case'])+','+str(doc['control_group']['repeatability']['identical_float32']).lower()+','+str(doc['control_group']['repeatability']['identical_rgba8']).lower()+','+str(doc['control_group']['independent_output_storage']['distinct_data_objects']).lower()+','+str(doc['control_group']['independent_output_storage']['distinct_backing_buffers']).lower()+','+str(doc['control_group']['public_direct_identity']).lower()+','+str(doc['control_group']['canonical_own_key']).lower()+','+str(doc['control_group']['adapter_own_key']).lower()+'};',
        'struct ClaimBoundaries { std::string_view authority,runtime,input,structural_mutations; };',
        'inline constexpr ClaimBoundaries kClaimBoundaries{'+cpp_string(doc['claim_boundaries']['authority'])+','+cpp_string(doc['claim_boundaries']['runtime'])+','+cpp_string(doc['claim_boundaries']['input'])+','+cpp_string(doc['claim_boundaries']['structural_mutations'])+'};',
        'struct CompareResult { bool equal,dimensions_ok,float_count_ok,rgba8_count_ok; MismatchKind mismatch; std::size_t first_mismatch; };',
        'inline CompareResult compare_exact(const Case& a, const Case& b) {',
        '  if (a.width != b.width || a.height != b.height) return {false,false,false,false,MismatchKind::Dimensions,0};',
        '  if (a.output_float_words.size() != b.output_float_words.size()) return {false,true,false,a.output_rgba8.size() == b.output_rgba8.size(),MismatchKind::FloatCount,0};',
        '  if (a.output_rgba8.size() != b.output_rgba8.size()) return {false,true,true,false,MismatchKind::Rgba8Count,0};',
        '  for (std::size_t i=0;i<a.output_float_words.size();++i) if (a.output_float_words[i] != b.output_float_words[i]) return {false,true,true,true,MismatchKind::Float32,i};',
        '  for (std::size_t i=0;i<a.output_rgba8.size();++i) if (a.output_rgba8[i] != b.output_rgba8[i]) return {false,true,true,true,MismatchKind::Rgba8,i};',
        '  return {true,true,true,true,MismatchKind::None,0};',
        '}',
        '',
        'static_assert(kBindingAbi.size() == 5U);',
        'static_assert(kCases.size() == 9U);',
        'static_assert(kMutations.size() == 9U);',
        'static_assert(kMutationWitnesses.size() == 9U);',
        'static_assert(kStructuralMutations.size() == 2U);',
        '} // namespace noisemaker_testpattern_oracle',
        '',
    ])
    TARGET.write_text('\n'.join(lines))
    TARGET.with_name(TARGET.name+'.sha256').write_text(sidecar(TARGET,TARGET.read_bytes()))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); parser.add_argument('--self-test',action='store_true'); args=parser.parse_args()
    if args.check and args.self_test: raise OracleError('choose one materializer mode')
    doc=validate(strict_json(checked(ORACLE)))
    if args.self_test: self_test_coherence_forgery()
    checked(GENERATOR); checked(REPORT); checked(pathlib.Path(__file__)); coherence(require_target=args.check or args.self_test)
    if args.self_test:
        materialize(doc)
        print(f"testPattern materializer self-test: {len(doc['render_cases'])} cases, {len(doc['behavioral_mutation_ledger'])} behavioral mutations, 2 structural-only, coherence forgery probe verified, strict comparer and sidecars verified")
    elif args.check:
        print('testPattern native oracle include ok (coherence, source contract, and sidecars verified)')
    else:
        print('testPattern native oracle include ok')
if __name__ == '__main__':
    try: main()
    except OracleError as exc: print(f'OracleError: {exc}', file=sys.stderr); raise SystemExit(1)
