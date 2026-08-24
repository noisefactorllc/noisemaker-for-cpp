#!/usr/bin/env python3
"""Fail-closed materializer for the synth/noise exact oracle."""
from __future__ import annotations
import argparse, copy, hashlib, json, math, pathlib, re, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[2]
PACKAGE=ROOT/'docs/port-engineering/noise-parity'; ORACLE=PACKAGE/'noise-oracles.json'; GENERATOR=PACKAGE/'noise_oracle_generator.mjs'; REPORT=PACKAGE/'noise-oracle-report.md'; TARGET=ROOT/'tests/oracles/noise_expected.inc'
SCHEMA='noisemaker-for-cpp.synth-noise.pixel-parity.v1'; KEY='synth/noise:noise'; WORD=re.compile(r'^0x[0-9a-f]{8}$'); SHA=re.compile(r'^[0-9a-f]{64}$')
EXPECTED_CLOSURE={
'src/csl/glsl-kernel.js':'a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa','src/csl/glsl-runtime.js':'a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072','src/csl/runtime.js':'a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee','src/effects/adapters/bit-effects.js':'5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7','src/effects/adapters/crt.js':'c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc','src/effects/adapters/f32-color.js':'b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046','src/effects/adapters/fractal.js':'0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29','src/effects/adapters/index.js':'40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267','src/effects/adapters/julia.js':'0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5','src/effects/adapters/median.js':'e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583','src/effects/adapters/palette.js':'8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452','src/effects/adapters/snow.js':'202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366','src/effects/catalog.js':'d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4','src/effects/definition.js':'fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02','src/effects/generated/canonical-adapter-data.js':'ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab','src/effects/generated/canonical-kernels.js':'66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe','src/effects/generated/kernels.js':'b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01','src/effects/generated/upstream-snapshot.js':'e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090','src/effects/registry.js':'8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618','src/runtime/pass-runner.js':'fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa','src/runtime/sampler.js':'1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328','src/runtime/surface.js':'0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59'}
EXPECTED_BINDINGS={'NOISE_TYPE':'int32','LOOP_OFFSET':'int32','time':'number','seed':'int32','resolution':'Vec2','tileOffset':'Vec2','fullResolution':'Vec2','scaleX':'number','scaleY':'number','octaves':'int32','ridges':'bool','loopScale':'number','speed':'number','colorMode':'int32','wrap':'bool'}
EXPECTED_SOURCE_ABI={'time':'float','seed':'int','resolution':'vec2','tileOffset':'vec2','fullResolution':'vec2','scaleX':'float','scaleY':'float','octaves':'int','ridges':'bool','loopScale':'float','speed':'float','colorMode':'int','wrap':'bool'}
EXPECTED_MECHANISMS=[{'name':'mutable_global_frame_profile','profile':'mutable-global-frame-noise-v1','status':'prepared_not_admitted','reason':'typed slice row is not admitted in this oracle-only task'},{'name':'runtime_loop_bound_profile','profile':'runtime-loop-bound-v1','status':'prepared_not_admitted','reason':'runtime profile integration remains outside oracle scope'},{'name':'scalar_uint_xor_profile','profile':'scalar-uint-xor-v1','status':'prepared_not_admitted','reason':'profile integration remains outside oracle scope'},{'name':'owner_speed_control','profile':'owner-speed-control-noise-v1','status':'executed_behavioral_mutant','reason':'owner/control anchor is executed in the exact mutation ledger'}]
EXPECTED_CASES=[{'name':'mono-hermite','width':5,'height':4,'time':.25,'seed':7,'noiseType':2,'octaves':3,'scaleX':22,'scaleY':17,'wrap':False,'ridges':False,'loopOffset':35,'loopScale':8,'speed':11,'colorMode':0},{'name':'rgb-simplex-wrapped','width':4,'height':5,'time':1.5,'seed':19,'noiseType':10,'octaves':4,'scaleX':75,'scaleY':61,'wrap':True,'ridges':True,'loopOffset':300,'loopScale':42,'speed':-25,'colorMode':1},{'name':'rgb-sine-live','width':6,'height':3,'time':2,'seed':23,'noiseType':11,'octaves':2,'scaleX':91,'scaleY':33,'wrap':True,'ridges':False,'loopOffset':300,'loopScale':20,'speed':60,'colorMode':1},{'name':'constant-short','width':3,'height':3,'time':0,'seed':3,'noiseType':0,'octaves':1,'scaleX':8,'scaleY':8,'wrap':False,'ridges':True,'loopOffset':10,'loopScale':1,'speed':0,'colorMode':0}]
EXPECTED_SELECTOR_CASES=[('mono-hermite',5,4,2,35),('rgb-simplex-wrapped',4,5,10,300),('rgb-sine-live',6,3,11,300),('constant-short',3,3,0,10),('linear-offset20',3,2,1,20),('catmull3-offset30',3,2,3,30),('catmull4-offset40',4,3,4,40),('cubic-offset50',2,3,5,50),('bicubic-offset60',4,2,6,60),('hermite-offset70',3,2,2,70),('hermite-offset80',2,4,2,80),('hermite-offset90',4,2,2,90),('hermite-offset100',3,3,2,100),('hermite-offset110',2,3,2,110),('hermite-offset120',4,3,2,120),('hermite-offset200',3,2,2,200),('hermite-offset210',2,4,2,210),('hermite-offset400',4,2,2,400),('hermite-offset410',3,3,2,410)]
EXPECTED_HASHES={'mono-hermite':('997eaad8ea2ef6524bfef66b8ecc10cc453f524f39a9aa1913c72a138bd1b67b','d936a2997d4848208cf363fa79e60277fb2dbbe83d0f270aa8bfb3bb3afb1255','cc93e5d0e903fb6b03cdd9dca57c68554d8d3822da747379de713292edf53dea'),'rgb-simplex-wrapped':('875bd55792b8efe1db40b25e913d9d469686868d8b6bc4fb8335e7d4b7e0f7bc','9baea6701f07fe45f3d8af59a07388a27074fe90b377fa2406eaf587f289451b','cb27d6815d90cd9207d353aa3c76ae1c52db210938c7189c733d314d265379c6'),'rgb-sine-live':('09ec5559024a833eaba630b0e349582bf1e10cf5656789ee2b6dcb77cd78dd04','4282baa58947ebc6713e508f9952f8dde8cb8c75b84d0f5ff78e9317c70933da','3600dcde68d91b98f77282bc8ed55964489a1dd2dc5feca7c1182369a4ad4c14'),'constant-short':('84151aed4e6e15a5f54720bed0cc850447e15f115a6c396b6cc6348fdd29bdd4','e692745c0634c2ed18788594c23166389e2942decb206544269cfb98dfde6ae2','f49f33da576b785c19268591786d32d309f6b8e291cb91e0caaf73266630ebd3'),'linear-offset20':('4e077e91c974b4a8a10f77e44b8b634c5f6fc6d77ddb903c52ec60119d5a490d','5fb3c9911a1f69c010ed9ad6e1466c75e8c2504f413d891d3cc57b2ba2a1d2e1','1899687e7b8578b78a29c106d22419e64aad80ba0db7a578c60d9559c0781f96'),'catmull3-offset30':('e71ae508c2a020883f42816fb7419ad5636b25c95bc2f96f42154bdde3fcfd29','a1b7eed065f85002190d1cdb7bd49022f710e4cfd86d4c9e3d83a41ff634d91f','20bbabddf058e4e9e59b8c2b02a43bb2a35fdcf8a018f9a10c48504ebb3c8cbc'),'catmull4-offset40':('5182068f29bf85e06067132cc749935db3217652d8044052edc01bcd9b305ad2','cfc7b02d04095eddf8128e0553fcb5a2dfe44396e6b0773b34b95f10721e7b5f','94257633920a029fef03931961cefefe64576cfbc0cadc53efa5d4c29fa9417d'),'cubic-offset50':('1abfbaaf81717955f9a39c5fb5413fad649fc12e03f73d1ed0a0cafee7f1588e','94dc5370979404736ee765358956f212337832e2f3db29f5b079568e4298406e','2d02aad626af452f13569f4d0b1b039ae14e00e477e28ebf685ce8ee4f801b47'),'bicubic-offset60':('5b261a4da9455474b19ee7dd14589ff23d118fab95e069d160cd893304fba3df','134f4cdfb08e13e164fb515a9d01db4efda955a15fe698e193557985e3bcdf15','f0e337e474e47c473746e7bd3c9496f3e3acabf3bf77970f4025f1a31d630b96'),'hermite-offset70':('e71ae508c2a020883f42816fb7419ad5636b25c95bc2f96f42154bdde3fcfd29','8336fdf35d52f5e05a7c503afe122f300543d169ab0c9650de0512f383833f35','89c362f66e51db39cbd89d46f563fe38da13c22586edc5d1f3a0854f7dee2032'),'hermite-offset80':('c56e2340063f4578dbda5227e023179c6c7a61d7e063ef46162f3ed9638e5791','cb9e19e6449664c92bed4cc644f42d169751f18136ea2c8f0aae8644e4d43281','89632d73a277d5a475739a77912865a0b16c10626fd5f10db084437fee85fc00'),'hermite-offset90':('da951edcaee7dc10d2cb47139658fe8a25550b6a399440094782439456b699cd','2a68d4512f4484d359e6e61cc00b68712913f3f9b5f7adfdbf3b8e08d5ba286d','84b982295d095403f6f88caeea84635b263dedc643f96ea69472b59f42a9ddb3'),'hermite-offset100':('84151aed4e6e15a5f54720bed0cc850447e15f115a6c396b6cc6348fdd29bdd4','a58994259ad1c8bababbc9850bd4df15f3b565e3f810510330ddf0249b39e008','e637d59ad3d1b2e2effac244fd1c37076086c7ac19c1789fb0eeb79d7f04df29'),'hermite-offset110':('308890b08af1dd6297cad627d270e0d065ab8d184f751dd62bc30ebe2ef5ec71','160c9ed99fe4add8351f383d92fe888eb03bdd3ebe8639ca81d840b895cd7a39','9ab825c0925d46a1943e570947e329ff4f645e01871224287978b24a59b05840'),'hermite-offset120':('5182068f29bf85e06067132cc749935db3217652d8044052edc01bcd9b305ad2','8c6015b8359ec82205375cdd196bd16ee27f099f150e8fb47a877b4beca74d0f','64f66403ff167541382b474e46dba8b6172ba9b438f7205a2b0e614f9b06972f'),'hermite-offset200':('4e077e91c974b4a8a10f77e44b8b634c5f6fc6d77ddb903c52ec60119d5a490d','ae8414926d4c1a3269068569a0a07e3e0c14004e514cbcca48ffbed4c0c8c9a7','797ed4b5d271ba127b4ab198aa8e53e37e81b06cbf37781e5a787c5b09a6eeb7'),'hermite-offset210':('863122d984155dfa6b094845c6ec1cef368e51460aa5b61cf287d1db3b5436e5','251a922ddf71c78eeaf16bd72f06c0ccd8e805d081b9bb862ce3fd9eb617d489','73f1df273cd4e2471deacb5e274c7b81d71cec8ecb4f5accb523ed422042218b'),'hermite-offset400':('1f09154f803bba6ad96460c2513a546c9f72717c0252401c3ec64253ef94a3b7','96bf37577d74af11fb4b9247ba780c8478c19d1d2c51bb09455e23c78ef4c6c4','c39a5626c50bec62a47f600c8dcc66ee877cbc30a6936002561a057fd14fa763'),'hermite-offset410':('10573219028e874a6aaf26cde9ee04bdefbedb6ba795e8f8b0023c9891973713','080f40a3f8fce88013cdb74c691a3d3c11fd1463ed65e57969945b3477493531','ff376e0de1dc61d33b5d722f9395e7bb6d1f7067e4d90d385dc84b88f9b517bc')}
EXPECTED_MUTATION_TEXT={'mutable-global-frame':('(globalCoord[0] = gl_FragCoord[0] + tileOffset[0], globalCoord[1] = gl_FragCoord[1] + tileOffset[1], globalCoord);','(globalCoord[0] = gl_FragCoord[0] + tileOffset[0], globalCoord[1] = gl_FragCoord[1] + tileOffset[1] + 1, globalCoord);'),'runtime-loop-bound':('for (var i = 1; i <= oct; i++) {','for (var i = 1; i < oct; i++) {'),'scalar-uint-xor':('floatBitsToUint(sFrac)','floatBitsToUint(sFrac + 0.125)'),'owner-speed-control':('var speed = $bindings["speed"];','var speed = $bindings["speed"] * 2;')}
EXPECTED_MUTATION_ROWS={
'mutable-global-frame':[(True,60,60,0,0),(True,60,60,0,0),(True,54,54,0,0),(True,27,27,0,0),(True,18,18,0,0),(True,18,16,0,0),(True,36,36,0,0),(True,18,18,0,0),(True,24,24,0,0),(True,18,18,0,0),(True,24,24,0,0),(True,24,24,0,0),(True,27,27,0,0),(True,18,18,0,0),(True,36,36,0,0),(True,18,18,0,0),(True,24,24,0,0),(True,24,24,0,0),(True,27,27,0,0)],
'runtime-loop-bound':[(True,60,57,0,0),(True,60,55,0,0),(True,54,47,0,0),(True,27,24,0,0),(True,18,18,0,0),(True,18,18,0,0),(True,36,36,0,0),(True,18,18,0,0),(True,24,22,0,0),(True,18,18,0,0),(True,24,22,0,0),(True,24,24,0,0),(True,27,25,0,0),(True,18,18,0,0),(True,36,36,0,0),(True,18,17,0,0),(True,24,24,0,0),(True,24,22,0,0),(True,27,24,0,0)],
'scalar-uint-xor':[(True,60,60,0,0),(False,0,0,-1,-1),(False,0,0,-1,-1),(True,27,27,0,0),(True,18,18,0,0),(True,18,18,0,0),(True,36,36,0,0),(True,18,18,0,0),(True,24,24,0,0),(True,18,18,0,0),(True,24,24,0,0),(True,24,21,0,4),(True,27,27,0,0),(True,18,18,0,0),(True,36,36,0,0),(True,18,18,0,0),(True,24,24,0,0),(True,24,24,0,0),(True,27,27,0,0)],
'owner-speed-control':[(True,60,60,0,0),(True,60,50,0,0),(True,54,42,0,4),(False,0,0,-1,-1),(True,18,15,0,0),(True,18,14,0,1),(True,36,35,0,0),(True,18,18,0,0),(True,24,23,0,0),(True,18,18,0,0),(True,24,24,0,0),(True,24,24,0,0),(True,27,27,0,0),(True,18,18,0,0),(True,36,28,0,0),(True,18,17,0,0),(True,24,24,0,0),(True,24,21,0,0),(True,27,27,0,0)]}
EXPECTED_MUTATIONS={'mutable-global-frame':('6c61d1d9c538263fb40b160bdac65d060dc64748197b866f99a2260d84d918bf','9982c75d15a5cf8c1328acf6b621531d9f8c71c11e06ff2020e65a5f134c7f8f','4ca2f9194aa0ec93237c408edc8f1e9bf3524dd349175b5a79e44ef0a9382f45'),'runtime-loop-bound':('7dca0229b063ecd50fb6dda61cc202d99f3d036da2a6e46223255650a0e11adb','7d3c4aa1d382c224e07a00ac2f591072b3edeaa4c20f7364fc5c7e59cad75c84','67ead442cf8c65d9ca47c463f50bd8f25d7029618b742abfcc5a5931e75aa845'),'scalar-uint-xor':('8eeab152f20e4e83c0c8091e649b85d3eafec7b98868f119c4a525ce5d100662','028c473cf8ed4eae00c330f7c68f0c13cf3cf226d52024901bfdc3a6a783ab29','e982ad518d46377ad6d831e861cdebe2aff8f95aaa975f6b075111bced84b19e'),'owner-speed-control':('d5773b533941651b0dcb30546a6d1bc4d1648f61f51058a0610f93cc9293e949','3cfb6c567f23b6ee56ca6e028f219de34f54050bcea85ef424a4502e1c9ddc43','3f52538913c93143fedabccc0554fb51d994f0a42db4d78f2654a6f3f8f6008e')}
class OracleError(RuntimeError): pass
def strict_json(payload):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise OracleError(f'duplicate JSON key: {key}')
            result[key]=value
        return result
    def parse_int(text):
        try: return int(text)
        except ValueError as error: raise OracleError(f'integer literal rejected: {error}') from error
    def parse_float(text):
        try: value=float(text)
        except (OverflowError,ValueError) as error: raise OracleError(f'number literal rejected: {error}') from error
        if not math.isfinite(value): raise OracleError('number literal must be finite')
        return value
    def reject_constant(text): raise OracleError(f'non-finite JSON constant rejected: {text}')
    try:
        return json.loads(payload, object_pairs_hook=pairs, parse_int=parse_int, parse_float=parse_float, parse_constant=reject_constant)
    except OracleError:
        raise
    except (json.JSONDecodeError,ValueError,TypeError) as error:
        raise OracleError(f'invalid JSON: {error}') from error
def _string(value,label):
    if type(value) is not str: raise OracleError(f'{label}: expected string')
    return value
def _bool(value,label):
    if type(value) is not bool: raise OracleError(f'{label}: expected bool')
    return value
def _int(value,label,low=None,high=None):
    if type(value) is not int: raise OracleError(f'{label}: expected integer')
    if low is not None and value<low or high is not None and value>high: raise OracleError(f'{label}: integer out of range')
    return value
def _number(value,label):
    if isinstance(value,bool) or not isinstance(value,(int,float)): raise OracleError(f'{label}: expected finite number')
    try: finite=math.isfinite(float(value))
    except (OverflowError,ValueError) as error: raise OracleError(f'{label}: expected finite number') from error
    if not finite: raise OracleError(f'{label}: expected finite number')
    return value
def _hash(value,label):
    value=_string(value,label)
    if not SHA.fullmatch(value): raise OracleError(f'{label}: malformed SHA-256')
    return value
def digest(b): return hashlib.sha256(b).hexdigest()
def pack_words(values):
    out=bytearray()
    for value in values: out.extend(int(value,16).to_bytes(4,'little'))
    return bytes(out)
def sidecar(p,b): return f'{digest(b)}  {p.name}\n'
def checked(p):
    s=p.with_name(p.name+'.sha256')
    if not p.is_file() or not s.is_file(): raise OracleError(f'missing checked asset or sidecar: {p.name}')
    b=p.read_bytes()
    if s.read_text()!=sidecar(p,b): raise OracleError(f'checksum sidecar drift: {p.name}')
    return b
def exact(v,keys,label):
    if not isinstance(v,dict): raise OracleError(f'{label}: expected object')
    if set(v)!=set(keys): raise OracleError(f'{label}: field set drift')
    return v
def reject_abs(v,label='document'):
    if isinstance(v,str) and (re.match(r'^(?:[A-Za-z]:[\\/]|\\\\|/)',v) or re.search(r'(?:^|[\\/])(?:Users|private|tmp|home)[\\/]',v)): raise OracleError(f'{label}: absolute-looking string')
    if isinstance(v,list):
        for i,x in enumerate(v): reject_abs(x,f'{label}[{i}]')
    elif isinstance(v,dict):
        for k,x in v.items(): reject_abs(x,f'{label}.{k}')
def words(v,n,label):
    if not isinstance(v,list) or len(v)!=n or any(type(x) is not str or not WORD.fullmatch(x) for x in v): raise OracleError(f'{label}: malformed word array')
def bytes_(v,n,label):
    if not isinstance(v,list) or len(v)!=n or any(type(x) is not int or not 0<=x<=255 for x in v): raise OracleError(f'{label}: malformed byte array')
def controls(value,expected,label):
    if not isinstance(value,dict) or set(value)!=set(expected): raise OracleError(f'{label}: control schema drift')
    for name,want in expected.items():
        actual=value[name]; kind=CONTROL_TYPES[name]
        if kind=='string': _string(actual,f'{label}.{name}')
        elif kind=='int32': _int(actual,f'{label}.{name}',-2147483648,2147483647)
        elif kind=='number': _number(actual,f'{label}.{name}')
        else: _bool(actual,f'{label}.{name}')
    if value!=expected: raise OracleError(f'{label}: fixed controls drift')
def validate(d):
    reject_abs(d)
    top=exact(d,{'schema','schema_version','program_key','effect_key','runtime_key','corpus_revision','upstream_revision','defines','binding_names','binding_abi','source_uniform_abi','factory','exactness_contract','comparer_self_tests','authority','provenance','native_binding_contract','render_cases','mutation_ledger','prepared_mechanisms','claim_boundaries','repeatability','output_storage_control','control_group'},'document')
    if (_string(top['schema'],'schema'),_int(top['schema_version'],'schema_version'),_string(top['program_key'],'program_key'),_string(top['effect_key'],'effect_key'),_string(top['runtime_key'],'runtime_key')) != (SCHEMA,1,KEY,'synth/noise',KEY): raise OracleError('noise identity drift')
    if _string(top['corpus_revision'],'corpus_revision')!='a024dc3a960cc44af454abc7aebce50456c194e6' or _string(top['upstream_revision'],'upstream_revision')!='117a236679d1db3ab8f0e278230ece277b57564c': raise OracleError('revision drift')
    defines=exact(top['defines'],{'NOISE_TYPE','LOOP_OFFSET'},'defines'); _int(defines['NOISE_TYPE'],'defines.NOISE_TYPE',-2147483648,2147483647); _int(defines['LOOP_OFFSET'],'defines.LOOP_OFFSET',-2147483648,2147483647)
    if defines != {'NOISE_TYPE':10,'LOOP_OFFSET':300}: raise OracleError('define drift')
    if type(top['binding_names']) is not list or any(type(x) is not str for x in top['binding_names']): raise OracleError('binding names type drift')
    if top['binding_names'] != list(EXPECTED_BINDINGS) or top['binding_abi'] != EXPECTED_BINDINGS or top['source_uniform_abi'] != EXPECTED_SOURCE_ABI: raise OracleError('binding/source ABI drift')
    factory=exact(top['factory'],{'name','text_sha256','public_factory_is_canonical_identity'},'factory'); _string(factory['name'],'factory.name'); _hash(factory['text_sha256'],'factory.text_sha256'); _bool(factory['public_factory_is_canonical_identity'],'factory.public_factory_is_canonical_identity')
    if factory != {'name':'canonicalFactory265','text_sha256':'392c3be9936855debc0956bc41e4b658896ccdd673674a2ad983101aac521e14','public_factory_is_canonical_identity':True}: raise OracleError('factory identity drift')
    exactness=exact(top['exactness_contract'],{'float32','rgba8','tolerance','comparison_order'},'exactness_contract')
    for k,v in exactness.items(): _string(v,f'exactness_contract.{k}')
    if exactness != {'float32':'raw little-endian uint32 words; signed zero and NaN payloads significant','rgba8':'complete independent RGBA8 byte arrays','tolerance':'none','comparison_order':'dimensions, counts, every float32 word, every RGBA8 byte'}: raise OracleError('exactness contract drift')
    authority=exact(top['authority'],{'node_version','oracle','live_checkout_rejected','symlink_rejected','adapter_override_absent','import_closure'},'authority'); _string(authority['node_version'],'authority.node_version'); _string(authority['oracle'],'authority.oracle'); _bool(authority['live_checkout_rejected'],'authority.live_checkout_rejected'); _bool(authority['symlink_rejected'],'authority.symlink_rejected'); _bool(authority['adapter_override_absent'],'authority.adapter_override_absent')
    if authority['node_version']!='v24.7.0' or authority['oracle']!='unmodified public canonical factory from immutable CPU snapshot' or authority['live_checkout_rejected'] is not True or authority['symlink_rejected'] is not True or authority['adapter_override_absent'] is not True: raise OracleError('authority semantics drift')
    closure=authority['import_closure'];
    if type(closure) is not list: raise OracleError('authority.import_closure: expected list')
    for index,item in enumerate(closure):
        item=exact(item,{'relative_path','sha256'},f'authority.import_closure[{index}]'); _string(item['relative_path'],f'authority.import_closure[{index}].relative_path'); _hash(item['sha256'],f'authority.import_closure[{index}].sha256')
    pairs=[(item['relative_path'],item['sha256']) for item in closure]
    if pairs != sorted(EXPECTED_CLOSURE.items()): raise OracleError('exact 22-file closure drift')
    provenance=exact(top['provenance'],{'source','generator','materializer','cpu_root'},'provenance'); source=exact(provenance['source'],{'relative_path','bytes','sha256'},'provenance.source'); _string(source['relative_path'],'provenance.source.relative_path'); _int(source['bytes'],'provenance.source.bytes',0); _hash(source['sha256'],'provenance.source.sha256'); gen=exact(provenance['generator'],{'relative_path','sha256'},'provenance.generator'); _string(gen['relative_path'],'provenance.generator.relative_path'); _hash(gen['sha256'],'provenance.generator.sha256'); mat=exact(provenance['materializer'],{'relative_path','sha256'},'provenance.materializer'); _string(mat['relative_path'],'provenance.materializer.relative_path'); _hash(mat['sha256'],'provenance.materializer.sha256'); _string(provenance['cpu_root'],'provenance.cpu_root')
    if provenance['cpu_root']!='<immutable-cpu-snapshot-root>': raise OracleError('absolute CPU root serialized')
    if source != {'relative_path':'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/noise/noise.glsl','bytes':18131,'sha256':'410a98f0d4ec80acde225cb5366a3bbaf752e5743f99bcd651a2c3cbb6cc3274'}: raise OracleError('source provenance drift')
    if gen != {'relative_path':'docs/port-engineering/noise-parity/noise_oracle_generator.mjs','sha256':digest(GENERATOR.read_bytes())}: raise OracleError('generator provenance drift')
    if mat != {'relative_path':'tools/glslcpp/generate_noise_native_oracle_include.py','sha256':digest(pathlib.Path(__file__).read_bytes())}: raise OracleError('materializer provenance drift')
    cmp=exact(top['comparer_self_tests'],{'good','dim','short','long','rgba','signedzero','nan','first_mismatch'},'comparer_self_tests')
    for k,v in cmp.items(): _bool(v,f'comparer_self_tests.{k}')
    if any(cmp[x] is not True for x in cmp): raise OracleError('comparer contract drift')
    native=exact(top['native_binding_contract'],{'status','required_bindings','abi'},'native_binding_contract'); _string(native['status'],'native_binding_contract.status');
    if type(native['required_bindings']) is not list or any(type(x) is not str for x in native['required_bindings']): raise OracleError('native binding names type drift')
    if native != {'status':'pending_shared_native_integration','required_bindings':list(EXPECTED_BINDINGS),'abi':EXPECTED_BINDINGS}: raise OracleError('native ABI contract drift')
    repeat=exact(top['repeatability'],{'same_case','independent_output_storage','input_immutable'},'repeatability'); [ _bool(repeat[k],f'repeatability.{k}') for k in repeat]
    storage=exact(top['output_storage_control'],{'independent_buffers'},'output_storage_control'); _bool(storage['independent_buffers'],'output_storage_control.independent_buffers')
    if repeat != {'same_case':True,'independent_output_storage':True,'input_immutable':True} or storage != {'independent_buffers':True}: raise OracleError('runtime controls drift')
    group=exact(top['control_group'],{'repeatability','input_immutability','input_lifetime','independent_output_storage','public_direct_identity','canonical_own_key','adapter_own_key'},'control_group'); gr=exact(group['repeatability'],{'case','identical_float32','identical_rgba8'},'control_group.repeatability'); _string(gr['case'],'control_group.repeatability.case'); _bool(gr['identical_float32'],'control_group.repeatability.identical_float32'); _bool(gr['identical_rgba8'],'control_group.repeatability.identical_rgba8'); gi=exact(group['input_immutability'],{'case','unchanged'},'control_group.input_immutability'); _string(gi['case'],'control_group.input_immutability.case'); _bool(gi['unchanged'],'control_group.input_immutability.unchanged'); gl=exact(group['input_lifetime'],{'case','stable_after_independent_render'},'control_group.input_lifetime'); _string(gl['case'],'control_group.input_lifetime.case'); _bool(gl['stable_after_independent_render'],'control_group.input_lifetime.stable_after_independent_render'); go=exact(group['independent_output_storage'],{'case','distinct_data_objects','distinct_backing_buffers'},'control_group.independent_output_storage'); _string(go['case'],'control_group.independent_output_storage.case'); _bool(go['distinct_data_objects'],'control_group.independent_output_storage.distinct_data_objects'); _bool(go['distinct_backing_buffers'],'control_group.independent_output_storage.distinct_backing_buffers'); [ _bool(group[k],f'control_group.{k}') for k in ('public_direct_identity','canonical_own_key','adapter_own_key')]
    if group != {'repeatability':{'case':'rgb-simplex-wrapped','identical_float32':True,'identical_rgba8':True},'input_immutability':{'case':'rgb-simplex-wrapped','unchanged':True},'input_lifetime':{'case':'rgb-simplex-wrapped','stable_after_independent_render':True},'independent_output_storage':{'case':'rgb-simplex-wrapped','distinct_data_objects':True,'distinct_backing_buffers':True},'public_direct_identity':True,'canonical_own_key':True,'adapter_own_key':False}: raise OracleError('runtime control group drift')
    render_cases=top['render_cases'];
    if type(render_cases) is not list or len(render_cases) != len(EXPECTED_SELECTOR_CASES): raise OracleError('case count drift')
    for case_index,(case,selector) in enumerate(zip(render_cases,EXPECTED_SELECTOR_CASES)):
        expected_name,expected_width,expected_height,expected_noise_type,expected_loop_offset=selector
        exact(case,{'name','width','height','controls','input','expected','input_immutability','alpha_f32_word','alpha_rgba8_byte'},f'case {case.get("name")}'); _string(case['name'],'case.name'); _int(case['width'],'case.width',1,2**32-1); _int(case['height'],'case.height',1,2**32-1)
        if case_index < len(EXPECTED_CASES): controls(case['controls'],EXPECTED_CASES[case_index],f'case {case["name"]}.controls')
        else:
            if not isinstance(case['controls'],dict) or set(case['controls']) != set(CONTROL_TYPES): raise OracleError(f'case {case["name"]}.controls: control schema drift')
            for control_name,control_value in case['controls'].items():
                kind=CONTROL_TYPES[control_name]
                if kind=='string': _string(control_value,f'case {case["name"]}.controls.{control_name}')
                elif kind=='int32': _int(control_value,f'case {case["name"]}.controls.{control_name}',-2147483648,2147483647)
                elif kind=='number': _number(control_value,f'case {case["name"]}.controls.{control_name}')
                else: _bool(control_value,f'case {case["name"]}.controls.{control_name}')
        if case['name'] != expected_name or case['width'] != expected_width or case['height'] != expected_height: raise OracleError(f'fixed selector matrix drift: {case.get("name")}')
        if case['controls'].get('name') != expected_name or case['controls'].get('width') != expected_width or case['controls'].get('height') != expected_height or case['controls'].get('noiseType') != expected_noise_type or case['controls'].get('loopOffset') != expected_loop_offset: raise OracleError(f'fixed selector controls drift: {case.get("name")}')
        _bool(case['input_immutability'],f'case {case["name"]}.input_immutability'); _string(case['alpha_f32_word'],f'case {case["name"]}.alpha_f32_word'); _int(case['alpha_rgba8_byte'],f'case {case["name"]}.alpha_rgba8_byte',0,255)
        if case['input_immutability'] is not True or case['alpha_f32_word']!='0x3f800000' or case['alpha_rgba8_byte']!=255: raise OracleError('case alpha/immutability drift')
        inp=exact(case['input'],{'width','height','f32_words_le','f32_sha256'},'case input'); out=exact(case['expected'],{'width','height','f32_words_le','f32_sha256','rgba8_bytes','rgba8_sha256'},'case output'); _int(inp['width'],'case input.width',1,2**32-1); _int(inp['height'],'case input.height',1,2**32-1); words(inp['f32_words_le'],case['width']*case['height']*4,'input words'); words(out['f32_words_le'],case['width']*case['height']*4,'output words'); bytes_(out['rgba8_bytes'],case['width']*case['height']*4,'output bytes'); _hash(inp['f32_sha256'],'input f32 hash'); _hash(out['f32_sha256'],'output f32 hash'); _hash(out['rgba8_sha256'],'output rgba8 hash')
        if inp['width']!=case['width'] or inp['height']!=case['height']: raise OracleError('case dimensions drift')
        ih,fh,bh=EXPECTED_HASHES[case['name']]
        if inp['f32_sha256']!=ih or digest(pack_words(inp['f32_words_le']))!=ih or out['f32_sha256']!=fh or digest(pack_words(out['f32_words_le']))!=fh or out['rgba8_sha256']!=bh or digest(bytes(out['rgba8_bytes']))!=bh: raise OracleError(f'fixed payload/hash drift: {case["name"]}')
        if any(w != '0x3f800000' for w in out['f32_words_le'][3::4]) or any(v != 255 for v in out['rgba8_bytes'][3::4]): raise OracleError('alpha lane drift')
    expected_names=['mutable-global-frame','runtime-loop-bound','scalar-uint-xor','owner-speed-control']
    mutation_ledger=top['mutation_ledger'];
    if type(mutation_ledger) is not list or len(mutation_ledger) != 4: raise OracleError('mutation count drift')
    for m,name in zip(mutation_ledger,expected_names):
        exact(m,{'name','anchor_text','replacement_text','anchor_sha256','replacement_sha256','mutated_factory_sha256','rows'},'mutation'); _string(m['name'],'mutation.name'); _string(m['anchor_text'],'mutation.anchor_text'); _string(m['replacement_text'],'mutation.replacement_text'); [_hash(m[k],f'mutation.{k}') for k in ('anchor_sha256','replacement_sha256','mutated_factory_sha256')]
        if m['name']!=name or (m['anchor_sha256'],m['replacement_sha256'],m['mutated_factory_sha256']) != EXPECTED_MUTATIONS[name] or (m['anchor_text'],m['replacement_text']) != EXPECTED_MUTATION_TEXT[name]: raise OracleError(f'mutation provenance drift: {name}')
        rows=m['rows'];
        if type(rows) is not list or len(rows) != len(EXPECTED_SELECTOR_CASES): raise OracleError('mutation row count drift')
        any_diff=False
        for row_index,(row,case) in enumerate(zip(rows,render_cases)):
            exact(row,{'case','differs','changed_float32_lanes','changed_rgba8_bytes','witness'},'mutation row'); exact(row['witness'],{'first_float32_mismatch','first_rgba8_mismatch'},'mutation witness'); _string(row['case'],'mutation row.case'); _bool(row['differs'],'mutation row.differs'); _int(row['changed_float32_lanes'],'mutation row.changed_float32_lanes',0); _int(row['changed_rgba8_bytes'],'mutation row.changed_rgba8_bytes',0); _int(row['witness']['first_float32_mismatch'],'mutation witness.float32',-1); _int(row['witness']['first_rgba8_mismatch'],'mutation witness.rgba8',-1)
            if row['case']!=case['name'] or row['differs'] != (row['changed_float32_lanes']>0 and row['changed_rgba8_bytes']>0): raise OracleError('mutation witness fields drift')
            if row['differs']: any_diff=True
            expected_row=EXPECTED_MUTATION_ROWS[name][row_index]
            if (row['differs'],row['changed_float32_lanes'],row['changed_rgba8_bytes'],row['witness']['first_float32_mismatch'],row['witness']['first_rgba8_mismatch']) != expected_row: raise OracleError(f'mutation row witness drift: {name}')
        if not any_diff: raise OracleError(f'mutation has no behavioral witness: {name}')
    mechanisms=top['prepared_mechanisms'];
    if type(mechanisms) is not list: raise OracleError('prepared mechanisms type drift')
    for i,item in enumerate(mechanisms):
        item=exact(item,{'name','profile','status','reason'},f'prepared_mechanisms[{i}]'); [_string(item[k],f'prepared_mechanisms[{i}].{k}') for k in item]
    if mechanisms != EXPECTED_MECHANISMS: raise OracleError('prepared mechanism status drift')
    claims=top['claim_boundaries'];
    if type(claims) is not dict or any(type(k) is not str or type(v) is not str for k,v in claims.items()): raise OracleError('claim boundary type drift')
    if claims != {'mutable_global_frame':'exact canonical factory anchor/output witness only','runtime_loop_bound':'exact canonical factory loop anchor/output witness only','scalar_uint_xor':'exact canonical floatBitsToUint anchor/output witness only','owner_speed_control':'exact canonical speed-owner/control anchor/output witness only'}: raise OracleError('claim boundary drift')
    return top
CONTROL_TYPES={'name':'string','width':'int32','height':'int32','time':'number','seed':'int32','noiseType':'int32','octaves':'int32','scaleX':'number','scaleY':'number','wrap':'bool','ridges':'bool','loopOffset':'int32','loopScale':'number','speed':'number','colorMode':'int32'}
def emit(d):
    import json as _json
    q=lambda x: _json.dumps(str(x))
    u32=lambda arr: ', '.join(f'0x{int(x,16):08x}u' for x in arr)
    u8=lambda arr: ', '.join(str(int(x)) for x in arr)
    def control(name,value):
        kind=CONTROL_TYPES[name]
        if kind=='string': return f'{{{q(name)}, ControlKind::String, {q(value)}, 0, 0.0, false}}'
        if kind=='int32': return f'{{{q(name)}, ControlKind::Int32, nullptr, {int(value)}, 0.0, false}}'
        if kind=='number': return f'{{{q(name)}, ControlKind::Number, nullptr, 0, {float(value)!r}f, false}}'
        return f'{{{q(name)}, ControlKind::Bool, nullptr, 0, 0.0, {str(value).lower()}}}'
    cg=d['control_group']; rg=cg['repeatability']; gi=cg['input_immutability']; gl=cg['input_lifetime']; go=cg['independent_output_storage']
    control_init=f'inline constexpr ControlGroup kControlGroup{{{q(rg["case"])}, {str(rg["identical_float32"]).lower()}, {str(rg["identical_rgba8"]).lower()}, {q(gi["case"])}, {str(gi["unchanged"]).lower()}, {q(gl["case"])}, {str(gl["stable_after_independent_render"]).lower()}, {q(go["case"])}, {str(go["distinct_data_objects"]).lower()}, {str(go["distinct_backing_buffers"]).lower()}, {str(cg["public_direct_identity"]).lower()}, {str(cg["canonical_own_key"]).lower()}, {str(cg["adapter_own_key"]).lower()}}};'
    lines=['// Generated by generate_noise_native_oracle_include.py; exact JSON authority.','#pragma once','#include <cstdint>','#include <string>','#include <vector>','namespace noisemaker_noise_oracle {','enum class ControlKind : std::uint8_t { String, Int32, Number, Bool };','struct Control { const char* name; ControlKind kind; const char* string_value; std::int32_t int32_value; float number_value; bool bool_value; };','struct Binding { const char* name; const char* runtime_abi; const char* source_abi; };','struct Case { const char* name; std::uint32_t width,height; std::vector<Control> controls; std::vector<std::uint32_t> input_f32; const char* input_f32_sha256; std::vector<std::uint32_t> output_f32; const char* output_f32_sha256; std::vector<std::uint8_t> output_rgba8; const char* output_rgba8_sha256; const char* alpha_f32_word; std::uint8_t alpha_rgba8_byte; bool input_immutable; };','struct MutationRow { const char* case_name; bool differs; std::uint32_t changed_float32_lanes,changed_rgba8_bytes; int first_float32_mismatch,first_rgba8_mismatch; };','struct Mutation { const char* name; const char* anchor_text; const char* replacement_text; const char* anchor_sha256; const char* replacement_sha256; const char* mutated_factory_sha256; std::vector<MutationRow> rows; };','struct Mechanism { const char* name; const char* profile; const char* status; const char* reason; };','struct ControlGroup { const char* repeatability_case; bool identical_float32, identical_rgba8; const char* input_immutability_case; bool input_unchanged; const char* input_lifetime_case; bool input_lifetime_stable; const char* storage_case; bool distinct_data_objects, distinct_backing_buffers; bool public_direct_identity, canonical_own_key, adapter_own_key; };',f'inline constexpr const char* kSchema = {q(d["schema"])};',f'inline constexpr const char* kProgramKey = {q(KEY)};',f'inline constexpr const char* kFactorySha256 = {q(d["factory"]["text_sha256"])};',control_init,'inline const std::vector<Binding> kRuntimeBindings = {']
    for n in d['binding_names']: lines.append(f'  {{{q(n)}, {q(d["binding_abi"][n])}, {q(d["source_uniform_abi"].get(n,"compile-time"))}}},')
    lines+=['};','inline const std::vector<Binding> kSourceBindings = {']
    for n,a in d['source_uniform_abi'].items(): lines.append(f'  {{{q(n)}, {q("source")}, {q(a)}}},')
    lines+=['};','inline const std::vector<Case> kCases = {']
    for c in d['render_cases']:
        controls=', '.join(control(k,v) for k,v in c['controls'].items())
        o=c['expected']; lines.append(f'  {{{q(c["name"])}, {c["width"]}u, {c["height"]}u, {{{controls}}}, {{{u32(c["input"]["f32_words_le"])} }}, {q(c["input"]["f32_sha256"])}, {{{u32(o["f32_words_le"])} }}, {q(o["f32_sha256"])}, {{{u8(o["rgba8_bytes"])} }}, {q(o["rgba8_sha256"])}, {q(c["alpha_f32_word"])}, {c["alpha_rgba8_byte"]}u, {str(c["input_immutability"]).lower()}}},')
    lines+=['};','inline const std::vector<Mutation> kMutations = {']
    for m in d['mutation_ledger']:
        rows=', '.join(f'{{{q(r["case"])}, {str(r["differs"]).lower()}, {r["changed_float32_lanes"]}u, {r["changed_rgba8_bytes"]}u, {r["witness"]["first_float32_mismatch"]}, {r["witness"]["first_rgba8_mismatch"]}}}' for r in m['rows'])
        lines.append(f'  {{{q(m["name"])}, {q(m["anchor_text"])}, {q(m["replacement_text"])}, {q(m["anchor_sha256"])}, {q(m["replacement_sha256"])}, {q(m["mutated_factory_sha256"])}, {{{rows}}}}},')
    lines+=['};','inline const std::vector<Mechanism> kPreparedMechanisms = {']
    for m in d['prepared_mechanisms']: lines.append(f'  {{{q(m["name"])}, {q(m["profile"])}, {q(m["status"])}, {q(m["reason"])}}},')
    lines+=['};','} // namespace noisemaker_noise_oracle','']; return '\n'.join(lines)
def materialize():
    payload=checked(ORACLE); d=validate(strict_json(payload)); checked(REPORT); checked(GENERATOR); checked(pathlib.Path(__file__))
    rendered=emit(d); TARGET.write_text(rendered); TARGET.with_name(TARGET.name+'.sha256').write_text(sidecar(TARGET,rendered.encode())); return rendered
def selftest():
    d=validate(strict_json(checked(ORACLE))); checked(GENERATOR); checked(pathlib.Path(__file__)); tests=[]
    def reject_raw(raw,label):
        with tempfile.TemporaryDirectory(prefix='noise-oracle-forgery-') as td:
            q=pathlib.Path(td)/'forged.json'; q.write_bytes(raw); q.with_name(q.name+'.sha256').write_text(sidecar(q,raw))
            try:
                validate(strict_json(checked(q)))
            except OracleError as error:
                if str(error).startswith('forgery accepted'): raise OracleError(f'sentinel failure: {label}')
                tests.append(label); return
        raise OracleError(f'forgery accepted: {label}')
    def reject(candidate,label):
        reject_raw(json.dumps(candidate,sort_keys=True,separators=(',',':')).encode(),label)
    fields=['schema','schema_version','program_key','effect_key','runtime_key','corpus_revision','upstream_revision','defines','binding_names','binding_abi','source_uniform_abi','factory','exactness_contract','comparer_self_tests','authority','provenance','native_binding_contract','render_cases','mutation_ledger','prepared_mechanisms','claim_boundaries','repeatability','output_storage_control','control_group']
    for field in fields:
        x=copy.deepcopy(d); x.pop(field); reject(x,f'missing-{field}')
    for field in ('f32_words_le','rgba8_bytes'):
        x=copy.deepcopy(d); x['render_cases'][0]['expected'][field]=x['render_cases'][0]['expected'][field][:-1]; reject(x,f'truncated-{field}')
    canonical=checked(ORACLE)
    reject_raw(canonical.replace(b'"schema_version": 1,', b'"schema_version": 999,\n  "schema_version": 1,', 1), 'duplicate-top-level-final-valid')
    reject_raw(canonical.replace(b'"width": 5,\n      "height": 4', b'"width": 5,\n      "width": 5,\n      "height": 4', 1), 'duplicate-nested-case')
    reject_raw(canonical.replace(b'"f32_sha256": "997eaad8ea2ef6524bfef66b8ecc10cc453f524f39a9aa1913c72a138bd1b67b"', b'"f32_sha256": "0000000000000000000000000000000000000000000000000000000000000000",\n        "f32_sha256": "997eaad8ea2ef6524bfef66b8ecc10cc453f524f39a9aa1913c72a138bd1b67b"', 1), 'duplicate-nested-final-valid')
    for label, mutate in (
        ('case-width', lambda x: x['render_cases'][0].__setitem__('width', 99)),('case-name', lambda x: x['render_cases'][0].__setitem__('name', 'forged')),('input-hash', lambda x: x['render_cases'][0]['input'].__setitem__('f32_sha256', '0'*64)),('output-hash', lambda x: x['render_cases'][0]['expected'].__setitem__('f32_sha256', '0'*64)),('rgba-hash', lambda x: x['render_cases'][0]['expected'].__setitem__('rgba8_sha256', '0'*64)),('alpha-word', lambda x: x['render_cases'][0].__setitem__('alpha_f32_word', '0x00000000')),('alpha-byte', lambda x: x['render_cases'][0].__setitem__('alpha_rgba8_byte', 0)),('closure-path', lambda x: x['authority']['import_closure'][0].__setitem__('relative_path', '../escape.js')),('closure-hash', lambda x: x['authority']['import_closure'][0].__setitem__('sha256', '0'*64)),('closure-extra', lambda x: x['authority']['import_closure'].append({'relative_path':'extra.js','sha256':'0'*64})),('factory-name', lambda x: x['factory'].__setitem__('name', 'foreign')),('factory-hash', lambda x: x['factory'].__setitem__('text_sha256', '0'*64)),('binding-name', lambda x: x['binding_names'].__setitem__(0, 'foreign')),('binding-abi', lambda x: x['binding_abi'].__setitem__('time', 'Vec2')),('uniform-abi', lambda x: x['source_uniform_abi'].__setitem__('time', 'int')),('mutation-name', lambda x: x['mutation_ledger'][0].__setitem__('name', 'foreign')),('mutation-anchor', lambda x: x['mutation_ledger'][0].__setitem__('anchor_text', '')),('mutation-hash', lambda x: x['mutation_ledger'][0].__setitem__('anchor_sha256', '0'*64)),('mutation-row', lambda x: x['mutation_ledger'][0]['rows'][0].__setitem__('changed_float32_lanes', 0)),('prepared-mechanism', lambda x: x['prepared_mechanisms'].__setitem__(0, {'name':'foreign'})),('native-status', lambda x: x['native_binding_contract'].__setitem__('status', 'accepted')),('schema-version-float', lambda x: x.__setitem__('schema_version', 1.0)),('schema-version-bool', lambda x: x.__setitem__('schema_version', True)),('case-width-float', lambda x: x['render_cases'][0].__setitem__('width', 5.0)),('input-width-float', lambda x: x['render_cases'][0]['input'].__setitem__('width', 5.0)),('control-int-float', lambda x: x['render_cases'][0]['controls'].__setitem__('seed', 7.0)),('control-bool-int', lambda x: x['render_cases'][0]['controls'].__setitem__('wrap', 0)),('repeat-bool-int', lambda x: x['repeatability'].__setitem__('same_case', 1)),('control-nonfinite', lambda x: x['render_cases'][0]['controls'].__setitem__('time', float('inf'))),
    ):
        x=copy.deepcopy(d); mutate(x); reject(x,label)
    huge=checked(ORACLE).replace(b'"schema_version": 1',b'"schema_version": '+b'1'*4301,1)
    reject_raw(huge,'huge-integer')
    if len(tests)<50: raise OracleError(f'self-test census too small: {len(tests)}')
    print(f'noise materializer self-test: {len(tests)}/{len(tests)} JSON forgeries rejected with matching-sidecar probes; sidecars verified')
def main():
    p=argparse.ArgumentParser(); p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--self-test',action='store_true'); a=p.parse_args();
    if sum((a.write,a.check,a.self_test))!=1: raise SystemExit('choose --write, --check, or --self-test')
    if a.self_test:selftest();return
    if a.write: print(f'noise native include written ({len(materialize())} bytes)');return
    d=validate(strict_json(checked(ORACLE))); checked(REPORT); checked(GENERATOR); checked(pathlib.Path(__file__)); checked(TARGET); print('noise native oracle include: ok')
if __name__=='__main__': main()
