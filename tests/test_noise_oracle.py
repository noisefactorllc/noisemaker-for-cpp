from __future__ import annotations
import hashlib, importlib.util, json, os, pathlib, shutil, subprocess, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
CPU=pathlib.Path(os.environ['NOISEMAKER_CPU_ROOT']) if os.environ.get('NOISEMAKER_CPU_ROOT') else None
HAS_AUTH=CPU is not None and CPU.is_dir()
LIVE=pathlib.Path(os.environ['NOISEMAKER_FOR_CPU']) if os.environ.get('NOISEMAKER_FOR_CPU') else None
GEN=ROOT/'docs/port-engineering/noise-parity/noise_oracle_generator.mjs'; MAT=ROOT/'tools/glslcpp/generate_noise_native_oracle_include.py'; ORACLE=ROOT/'docs/port-engineering/noise-parity/noise-oracles.json'
def run(*args,env=None): return subprocess.run(args,text=True,capture_output=True,env=env or os.environ.copy(),cwd=ROOT)
class NoiseOracleTests(unittest.TestCase):
 @unittest.skipUnless(HAS_AUTH, 'NOISEMAKER_CPU_ROOT is unavailable')
 def test_generator_self_test(self):
  r=run('node',str(GEN),'--self-test','--cpu-root',str(CPU)); self.assertEqual(r.returncode,0,r.stderr); self.assertIn('22-file closure',r.stdout); self.assertIn('8 comparer flags',r.stdout)
 def test_materializer_self_test(self):
  r=run('python3',str(MAT),'--self-test'); self.assertEqual(r.returncode,0,r.stderr); self.assertIn('JSON forgeries rejected with matching-sidecar probes',r.stdout); self.assertGreaterEqual(int(r.stdout.split('/',1)[0].rsplit(' ',1)[-1]),50)
 @unittest.skipUnless(HAS_AUTH, 'NOISEMAKER_CPU_ROOT is unavailable')
 def test_authority_unset_is_rejected(self):
  e=os.environ.copy(); e['NOISEMAKER_FOR_CPU']=str(ROOT/'does-not-exist'); e['HOME']=str(ROOT/'also-no-home'); r=run('node',str(GEN),'--self-test','--cpu-root',str(CPU),env=e); self.assertNotEqual(r.returncode,0); self.assertIn('existing live checkout',r.stderr)
 @unittest.skipUnless(HAS_AUTH and LIVE is not None and LIVE.is_dir(), 'live checkout is unavailable')
 def test_live_checkout_is_rejected(self):
  live=LIVE; r=run('node',str(GEN),'--self-test','--cpu-root',str(live)); self.assertNotEqual(r.returncode,0); self.assertIn('live checkout',r.stderr)
 @unittest.skipUnless(HAS_AUTH, 'NOISEMAKER_CPU_ROOT is unavailable')
 def test_symlink_snapshot_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'cpu-link'; p.symlink_to(CPU, target_is_directory=True); r=run('node',str(GEN),'--self-test','--cpu-root',str(p)); self.assertNotEqual(r.returncode,0); self.assertIn('symlink',r.stderr)
 @unittest.skipUnless(HAS_AUTH and LIVE is not None and LIVE.is_dir(), 'authority/live checkout is unavailable')
 def test_parent_alias_is_accepted_and_live_leaf_symlink_is_rejected(self):
  private=pathlib.Path('/private/tmp'); alias=pathlib.Path('/tmp')
  if not private.is_dir() or alias.resolve()!=private.resolve() or private not in CPU.parents:
   self.skipTest('canonical /tmp parent alias is unavailable')
  alias_cpu=alias/CPU.relative_to(private)
  accepted=run('node',str(GEN),'--check','--cpu-root',str(alias_cpu)); self.assertEqual(accepted.returncode,0,accepted.stderr)
  with tempfile.TemporaryDirectory() as d:
   live_link=pathlib.Path(d)/'live-link'; live_link.symlink_to(LIVE, target_is_directory=True)
   rejected=run('node',str(GEN),'--check','--cpu-root',str(CPU),env={**os.environ,'NOISEMAKER_FOR_CPU':str(live_link)})
   self.assertNotEqual(rejected.returncode,0); self.assertIn('live checkout must not be a symlink',rejected.stderr)
 @unittest.skipUnless(HAS_AUTH, 'NOISEMAKER_CPU_ROOT is unavailable')
 def test_dynamic_import_forms_are_rejected(self):
  forms=('"./catalog.js" + ""','`./catalog.js`','String("./catalog.js")')
  with tempfile.TemporaryDirectory() as d:
   forged=pathlib.Path(d)/'cpu'; shutil.copytree(CPU,forged,symlinks=False); forged=pathlib.Path(os.path.realpath(forged))
   target=forged/'src/effects/adapters/bit-effects.js'; original=target.read_text()
   for index,expression in enumerate(forms):
    target.write_text(original+f'\nconst oracle_sabotage_{index} = import({expression});\n')
    r=run('node',str(GEN),'--self-test','--cpu-root',str(forged))
    self.assertNotEqual(r.returncode,0); self.assertIn('nonliteral dynamic import',r.stderr); target.write_text(original)
 def test_json_contains_no_absolute_strings(self):
  d=json.loads(ORACLE.read_text()); text=json.dumps(d); self.assertNotRegex(text,r'/(?:Users|private|tmp|home)/'); self.assertEqual(len(d['authority']['import_closure']),22); self.assertEqual(d['control_group']['public_direct_identity'],True); self.assertEqual(d['control_group']['canonical_own_key'],True); self.assertEqual(d['control_group']['adapter_own_key'],False); self.assertEqual(d['control_group']['input_lifetime']['stable_after_independent_render'],True); self.assertEqual(d['control_group']['independent_output_storage']['distinct_data_objects'],True); self.assertEqual(d['control_group']['independent_output_storage']['distinct_backing_buffers'],True); self.assertIn('owner_speed_control',d['claim_boundaries']); self.assertEqual(len(d['prepared_mechanisms']),4)
 def test_selector_matrix_covers_all_runtime_noise_branches(self):
  d=json.loads(ORACLE.read_text()); cases=d['render_cases']; self.assertEqual(len(cases),19)
  controls=[case['controls'] for case in cases]
  self.assertEqual({control['noiseType'] for control in controls},{0,1,2,3,4,5,6,10,11})
  self.assertEqual({control['loopOffset'] for control in controls},{10,20,30,40,50,60,70,80,90,100,110,120,200,210,300,400,410,35})
  self.assertEqual(sum(control['loopOffset']==35 for control in controls),1)
  self.assertEqual({len(mutation['rows']) for mutation in d['mutation_ledger']},{len(cases)})
 def test_materializer_check(self):
  r=run('python3',str(MAT),'--check'); self.assertEqual(r.returncode,0,r.stderr)
 def test_duplicate_json_with_matching_sidecar_is_rejected(self):
  spec=importlib.util.spec_from_file_location('noise_materializer',MAT); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
  raw=ORACLE.read_bytes().replace(b'"schema_version": 1,', b'"schema_version": 999,\n  "schema_version": 1,', 1)
  with tempfile.TemporaryDirectory() as d:
   q=pathlib.Path(d)/'duplicate.json'; q.write_bytes(raw); q.with_name(q.name+'.sha256').write_text(f'{hashlib.sha256(raw).hexdigest()}  {q.name}\n')
   with self.assertRaises(module.OracleError): module.validate(module.strict_json(module.checked(q)))
 def test_matching_sidecar_scalar_and_huge_integer_forgery_is_rejected(self):
  spec=importlib.util.spec_from_file_location('noise_scalar_materializer',MAT); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
  original=json.loads(ORACLE.read_text())
  mutations=(
   ('schema-float',lambda x:x.__setitem__('schema_version',1.0)),
   ('schema-bool',lambda x:x.__setitem__('schema_version',True)),
   ('case-width-float',lambda x:x['render_cases'][0].__setitem__('width',5.0)),
   ('input-width-float',lambda x:x['render_cases'][0]['input'].__setitem__('width',5.0)),
   ('control-int-float',lambda x:x['render_cases'][0]['controls'].__setitem__('seed',7.0)),
   ('control-bool-int',lambda x:x['render_cases'][0]['controls'].__setitem__('wrap',0)),
   ('repeat-bool-int',lambda x:x['repeatability'].__setitem__('same_case',1)),
  )
  for label,mutate in mutations:
   candidate=json.loads(json.dumps(original)); mutate(candidate); raw=json.dumps(candidate,sort_keys=True,separators=(',',':')).encode()
   with tempfile.TemporaryDirectory() as d:
    q=pathlib.Path(d)/f'{label}.json'; q.write_bytes(raw); q.with_name(q.name+'.sha256').write_text(f'{hashlib.sha256(raw).hexdigest()}  {q.name}\n')
    with self.assertRaises(module.OracleError,msg=label): module.validate(module.strict_json(module.checked(q)))
  huge=ORACLE.read_bytes().replace(b'"schema_version": 1',b'"schema_version": '+b'1'*4301,1)
  with tempfile.TemporaryDirectory() as d:
   q=pathlib.Path(d)/'huge.json'; q.write_bytes(huge); q.with_name(q.name+'.sha256').write_text(f'{hashlib.sha256(huge).hexdigest()}  {q.name}\n')
   with self.assertRaises(module.OracleError): module.validate(module.strict_json(module.checked(q)))
 def test_include_compile_smoke(self):
  d=json.loads(ORACLE.read_text()); kind={'name':'String','width':'Int32','height':'Int32','time':'Number','seed':'Int32','noiseType':'Int32','octaves':'Int32','scaleX':'Number','scaleY':'Number','wrap':'Bool','ridges':'Bool','loopOffset':'Int32','loopScale':'Number','speed':'Number','colorMode':'Int32'}; q=lambda value: json.dumps(str(value))
  def controls(case):
   lines=[]
   for name,value in case['controls'].items():
    k=kind[name]
    if k=='String': args=f'{q(value)}, 0, 0.0, false'
    elif k=='Int32': args=f'nullptr, {int(value)}, 0.0, false'
    elif k=='Number': args=f'nullptr, 0, {float(value)!r}, false'
    else: args=f'nullptr, 0, 0.0, {str(value).lower()}'
    lines.append(f'  check_control(c, {q(name)}, ControlKind::{k}, {args});')
   return '\n'.join(lines)
  def u32(values): return ', '.join(f'0x{int(value,16):08x}u' for value in values)
  def u8(values): return ', '.join(str(int(value)) for value in values)
  source='''#include "tests/oracles/noise_expected.inc"
#include <cassert>
#include <cstdint>
#include <cstring>
#include <vector>
using namespace noisemaker_noise_oracle;
static const Control* find_control(const Case& c, const char* name) { for (const auto& control : c.controls) if (std::strcmp(control.name, name)==0) return &control; return nullptr; }
static void check_control(const Case& c, const char* name, ControlKind kind, const char* string_value, std::int32_t int32_value, float number_value, bool bool_value) { const auto* control=find_control(c,name); assert(control); assert(control->kind==kind); assert((control->string_value==nullptr)==(string_value==nullptr)); if (string_value) assert(std::strcmp(control->string_value,string_value)==0); assert(control->int32_value==int32_value); assert(control->number_value==number_value); assert(control->bool_value==bool_value); }
static void check_binding(const Binding& b, const char* name, const char* runtime_abi, const char* source_abi) { assert(std::strcmp(b.name,name)==0); assert(std::strcmp(b.runtime_abi,runtime_abi)==0); assert(std::strcmp(b.source_abi,source_abi)==0); }
static void check_hash(const char* actual, const char* expected) { assert(actual); assert(std::strlen(actual)==64); assert(std::strcmp(actual,expected)==0); }
int main() {
'''
  source+=f'  assert(std::strcmp(kSchema,{q(d["schema"])})==0); assert(std::strcmp(kProgramKey,{q(d["program_key"])})==0); assert(std::strcmp(kFactorySha256,{q(d["factory"]["text_sha256"])})==0); assert(std::strcmp(kControlGroup.repeatability_case,{q(d["control_group"]["repeatability"]["case"])})==0); assert(kControlGroup.identical_float32 && kControlGroup.identical_rgba8 && kControlGroup.input_unchanged && kControlGroup.input_lifetime_stable && kControlGroup.distinct_data_objects && kControlGroup.distinct_backing_buffers && kControlGroup.public_direct_identity && kControlGroup.canonical_own_key && !kControlGroup.adapter_own_key);\n'
  source+=f'  assert(kRuntimeBindings.size()=={len(d["binding_names"])}); assert(kSourceBindings.size()=={len(d["source_uniform_abi"])});\n'
  for index,name in enumerate(d['binding_names']): source+=f'  check_binding(kRuntimeBindings[{index}], {q(name)}, {q(d["binding_abi"][name])}, {q(d["source_uniform_abi"].get(name,"compile-time"))});\n'
  for index,(name,abi) in enumerate(d['source_uniform_abi'].items()): source+=f'  check_binding(kSourceBindings[{index}], {q(name)}, "source", {q(abi)});\n'
  source+=f'  assert(kCases.size()=={len(d["render_cases"])});\n'
  for index,case in enumerate(d['render_cases']):
   inp=case['input']; out=case['expected']
   source+=f'  {{ const auto& c=kCases[{index}]; assert(std::strcmp(c.name,{q(case["name"])})==0); assert(c.width=={case["width"]}u && c.height=={case["height"]}u); assert(c.controls.size()=={len(case["controls"])});\n'
   source+=controls(case)+'\n'
   source+=f'    assert((c.input_f32==std::vector<std::uint32_t>{{{u32(inp["f32_words_le"])}}})); check_hash(c.input_f32_sha256,{q(inp["f32_sha256"])});\n'
   source+=f'    assert((c.output_f32==std::vector<std::uint32_t>{{{u32(out["f32_words_le"])}}})); check_hash(c.output_f32_sha256,{q(out["f32_sha256"])});\n'
   source+=f'    assert((c.output_rgba8==std::vector<std::uint8_t>{{{u8(out["rgba8_bytes"])}}})); check_hash(c.output_rgba8_sha256,{q(out["rgba8_sha256"])});\n'
   source+=f'    assert(std::strcmp(c.alpha_f32_word,{q(case["alpha_f32_word"])})==0); assert(c.alpha_rgba8_byte=={case["alpha_rgba8_byte"]}u); assert(c.input_immutable);\n'
   source+='    for (std::size_t i=3;i<c.output_f32.size();i+=4) assert(c.output_f32[i]==0x3f800000u); for (std::size_t i=3;i<c.output_rgba8.size();i+=4) assert(c.output_rgba8[i]==255u); }\n'
  source+=f'  assert(kMutations.size()=={len(d["mutation_ledger"])}); assert(kPreparedMechanisms.size()=={len(d["prepared_mechanisms"])});\n'
  for index,mutation in enumerate(d['mutation_ledger']):
   source+=f'  {{ const auto& m=kMutations[{index}]; assert(std::strcmp(m.name,{q(mutation["name"])})==0); assert(std::strcmp(m.anchor_text,{q(mutation["anchor_text"])})==0); assert(std::strcmp(m.replacement_text,{q(mutation["replacement_text"])})==0); assert(std::strcmp(m.anchor_sha256,{q(mutation["anchor_sha256"])})==0); assert(std::strcmp(m.replacement_sha256,{q(mutation["replacement_sha256"])})==0); assert(std::strcmp(m.mutated_factory_sha256,{q(mutation["mutated_factory_sha256"])})==0); assert(m.rows.size()=={len(mutation["rows"])});\n'
   for rid,row in enumerate(mutation['rows']):
    w=row['witness']; source+=f'    assert(std::strcmp(m.rows[{rid}].case_name,{q(row["case"])})==0); assert(m.rows[{rid}].differs=={str(row["differs"]).lower()}); assert(m.rows[{rid}].changed_float32_lanes=={row["changed_float32_lanes"]}u); assert(m.rows[{rid}].changed_rgba8_bytes=={row["changed_rgba8_bytes"]}u); assert(m.rows[{rid}].first_float32_mismatch=={w["first_float32_mismatch"]}); assert(m.rows[{rid}].first_rgba8_mismatch=={w["first_rgba8_mismatch"]});\n'
   source+='  }\n'
  source+='  return 0;\n}\n'
  with tempfile.TemporaryDirectory() as d:
   c=pathlib.Path(d)/'smoke.cpp'; b=pathlib.Path(d)/'smoke'; c.write_text(source); r=subprocess.run(['c++','-std=c++20','-I',str(ROOT),str(c),'-o',str(b)],text=True,capture_output=True); self.assertEqual(r.returncode,0,r.stderr); self.assertEqual(subprocess.run([str(b)]).returncode,0)
if __name__=='__main__': unittest.main()
