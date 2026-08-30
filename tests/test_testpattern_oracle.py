from __future__ import annotations
import copy, hashlib, importlib.util, json, os, pathlib, re, shutil, subprocess, tempfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'docs/port-engineering/counted-for-parity/testpattern-oracle'
GENERATOR = PACKAGE / 'testPattern_oracle_generator.mjs'
MATERIALIZER = ROOT / 'tools/glslcpp/generate_testpattern_native_oracle_include.py'
ORACLE = PACKAGE / 'testPattern-oracles.json'
INCLUDE = ROOT / 'tests/oracles/testPattern_expected.inc'
COHERENCE = PACKAGE / 'testPattern-oracle-coherence.json'
EXPECTED_COHERENCE_SHA256 = 'cf188502dcdab8b4bee35fb18cb77dd2c54837ae22365d95abba58b9c4a51792'

def run_generator(*args, env=None):
    return subprocess.run(['node', str(GENERATOR), *args], cwd=ROOT, env=env or os.environ.copy(), text=True, capture_output=True)

def anchored_manifest_payload(payload):
    text=payload.decode('utf-8')
    redacted,count=re.subn(r'(\"generator_sha256\"\s*:\s*)\"[0-9a-f]{64}\"', r'\1"<generator-sha256>"', text, count=1)
    assert count==1
    return redacted.encode('utf-8')

def sidecar(path):
    assert pathlib.Path(f'{path}.sha256').read_text() == f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n'

def authority():
    value = os.environ.get('NOISEMAKER_CPU_ROOT')
    if not value or not pathlib.Path(value).is_dir(): pytest.skip('NOISEMAKER_CPU_ROOT unavailable')
    return pathlib.Path(value)

def live():
    value = os.environ.get('NOISEMAKER_FOR_CPU')
    if not value or not pathlib.Path(value).is_dir(): pytest.skip('NOISEMAKER_FOR_CPU unavailable')
    return pathlib.Path(value)

def materializer_module():
    spec = importlib.util.spec_from_file_location('testpattern_materializer', MATERIALIZER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def assert_forged_rejected(mod, candidate):
    payload=json.dumps(candidate, sort_keys=True, separators=(',',':'), allow_nan=True).encode()
    with tempfile.TemporaryDirectory() as d:
        path=pathlib.Path(d)/'forged.json'; path.write_bytes(payload)
        pathlib.Path(f'{path}.sha256').write_text(f'{hashlib.sha256(payload).hexdigest()}  {path.name}\n')
        with pytest.raises(mod.OracleError): mod.validate(mod.strict_json(mod.checked(path)))

def test_package_files_and_contract():
    for path in (GENERATOR, GENERATOR.with_name(GENERATOR.name+'.sha256'), MATERIALIZER, MATERIALIZER.with_name(MATERIALIZER.name+'.sha256'), ORACLE, ORACLE.with_name(ORACLE.name+'.sha256'), PACKAGE/'testPattern-oracle-report.md', PACKAGE/'testPattern-oracle-report.md.sha256', COHERENCE, COHERENCE.with_name(COHERENCE.name+'.sha256'), INCLUDE, INCLUDE.with_name(INCLUDE.name+'.sha256')):
        assert path.is_file(), path
    sidecar(GENERATOR); sidecar(MATERIALIZER); sidecar(ORACLE); sidecar(PACKAGE/'testPattern-oracle-report.md'); sidecar(COHERENCE); sidecar(INCLUDE)
    coherence=json.loads(COHERENCE.read_text())
    assert hashlib.sha256(anchored_manifest_payload(COHERENCE.read_bytes())).hexdigest()==EXPECTED_COHERENCE_SHA256
    assert set(coherence)=={'schema','generator_sha256','report_sha256','oracle_sha256','include_sha256'}
    assert coherence['schema']=='noisemaker-for-cpp.testPattern.oracle-coherence.v1'
    for key,path in {'generator':GENERATOR,'report':PACKAGE/'testPattern-oracle-report.md','oracle':ORACLE,'include':INCLUDE}.items(): assert coherence[f'{key}_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    doc=json.loads(ORACLE.read_text())
    assert doc['schema']=='noisemaker-for-cpp.testPattern.pixel-parity.v1'
    assert doc['program_key']=='synth/testPattern:testPattern'
    assert doc['input_contract']=={'kind':'source-only','runtime_input_path':'none','lifetime_claimed':False,'immutability_claimed':False,'reason':'Test Pattern has no sampler or input texture path'}
    assert all('input' not in c and 'input_lifetime_stable' not in c and 'input_immutable_exact_bits' not in c for c in doc['render_cases'])
    assert len(doc['authority']['import_closure'])==22
    assert len(doc['render_cases'])==9
    assert {c['pattern'] for c in doc['render_cases']} == set(range(7))
    assert len(doc['behavioral_mutation_ledger'])==9
    assert len({m['mutated_factory_sha256'] for m in doc['behavioral_mutation_ledger']})==9
    assert len(doc['structural_mutation_ledger'])==2
    assert all(m['required_witness_results'] and all(r['changed_float32_lanes']>0 and r['changed_rgba8_bytes']>0 for r in m['required_witness_results']) for m in doc['behavioral_mutation_ledger'])
    assert not any('/Users/' in json.dumps(doc) or '/private/' in json.dumps(doc) or '/tmp/' in json.dumps(doc) for _ in [0])

def test_generator_and_materializer_smoke():
    auth=authority()
    result=run_generator('--check', '--cpu-root', str(auth)); assert result.returncode==0, result.stderr
    result=subprocess.run(['python3', str(MATERIALIZER), '--self-test'], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode==0, result.stderr
    assert '9 cases, 9 behavioral mutations, 2 structural-only' in result.stdout
    assert 'coherence forgery probe verified' in result.stdout

def test_authority_unset_and_live_checkout_rejected():
    auth=authority(); env=os.environ.copy(); env.pop('NOISEMAKER_CPU_ROOT',None)
    result=run_generator('--check', env=env); assert result.returncode != 0
    env['NOISEMAKER_FOR_CPU']=str(auth)
    result=run_generator('--check','--cpu-root',str(auth),env=env); assert result.returncode != 0

def test_parent_alias_acceptance_and_leaf_symlink_rejection():
    auth=authority(); private=pathlib.Path('/private/tmp'); alias=pathlib.Path('/tmp')
    if private not in auth.parents or alias.resolve()!=private.resolve(): pytest.skip('canonical tmp alias unavailable')
    alias_path=alias/auth.relative_to(private)
    accepted=run_generator('--check','--cpu-root',str(alias_path)); assert accepted.returncode==0, accepted.stderr
    with tempfile.TemporaryDirectory() as d:
        link=pathlib.Path(d)/'cpu-link'; link.symlink_to(auth, target_is_directory=True)
        rejected=run_generator('--check','--cpu-root',str(link)); assert rejected.returncode != 0

def test_generator_rejects_configured_missing_and_symlink_live_checkout():
    auth=authority(); env=os.environ.copy(); env['NOISEMAKER_FOR_CPU']=str(pathlib.Path('/private/tmp/testpattern-no-such-live-root'))
    result=run_generator('--check','--cpu-root',str(auth),env=env); assert result.returncode != 0
    with tempfile.TemporaryDirectory() as d:
        link=pathlib.Path(d)/'live-link'; link.symlink_to(auth, target_is_directory=True); env['NOISEMAKER_FOR_CPU']=str(link)
        result=run_generator('--check','--cpu-root',str(auth),env=env); assert result.returncode != 0

def test_generator_rejects_import_graph_and_closure_leaf_mutations():
    auth=authority()
    for suffix in ('\nimport "./not-pinned.js";\n', '\n; import "./not-pinned.js";\n'):
        with tempfile.TemporaryDirectory() as d:
            copy=pathlib.Path(d)/'cpu'; shutil.copytree(auth, copy, symlinks=True)
            source=copy/'src/runtime/surface.js'; source.write_text(source.read_text()+suffix)
            (copy/'src/runtime/not-pinned.js').write_text('export const notPinned = true;\n')
            result=run_generator('--check','--cpu-root',str(copy)); assert result.returncode != 0
    for expression in ('"./surface.js" + ""', '`./surface.js`', 'String("./surface.js")'):
        with tempfile.TemporaryDirectory() as d:
            copy=pathlib.Path(d)/'cpu'; shutil.copytree(auth, copy, symlinks=True)
            source=copy/'src/runtime/surface.js'; source.write_text(source.read_text()+f'\nvoid import /*comment*/({expression});\n')
            result=run_generator('--check','--cpu-root',str(copy)); assert result.returncode != 0
    with tempfile.TemporaryDirectory() as d:
        copy=pathlib.Path(d)/'cpu'; shutil.copytree(auth, copy, symlinks=True)
        leaf=copy/'src/runtime/surface.js'; leaf.unlink(); leaf.symlink_to(auth/'src/runtime/surface.js')
        result=run_generator('--check','--cpu-root',str(copy)); assert result.returncode != 0

def test_materializer_rejects_duplicate_scalar_huge_and_matching_sidecars():
    mod=materializer_module(); raw=ORACLE.read_bytes()
    cases=[raw.replace(b'"schema_version": 1,',b'"schema_version": 1, "schema_version": 1,',1), raw.replace(b'"schema_version": 1,',b'"schema_version": 1.0,',1), raw.replace(b'"schema_version": 1,',b'"schema_version": '+b'1'*5000+b',',1), raw.replace(b'"schema_version": 1,',b'"schema_version": NaN,',1), raw + (b' ' * (8*1024*1024))]
    for index,payload in enumerate(cases):
        with tempfile.TemporaryDirectory() as d:
            path=pathlib.Path(d)/f'forged-{index}.json'; path.write_bytes(payload); pathlib.Path(f'{path}.sha256').write_text(f'{hashlib.sha256(payload).hexdigest()}  {path.name}\n')
            with pytest.raises(mod.OracleError): mod.validate(mod.strict_json(mod.checked(path)))

def test_materializer_rejects_coordinated_payload_forgery():
    mod=materializer_module(); original=json.loads(ORACLE.read_text())
    candidates=[]
    def add(path, value):
        candidate=copy.deepcopy(original); target=candidate
        for key in path[:-1]: target=target[key]
        target[path[-1]]=value; candidates.append(candidate)
    add(['render_cases',0,'name'],'forged-case')
    add(['render_cases',0,'controls','resolution'],[99,99])
    add(['render_cases',0,'tileOffset'],[19.0,27])
    add(['input_contract','kind'],'runtime-input')
    add(['input_contract','lifetime_claimed'],True)
    add(['input_contract','immutability_claimed'],1)
    add(['control_group','repeatability','identical_float32'],1)
    add(['render_cases',0,'output_f32_words_le',0],'0x80000000')
    add(['render_cases',0,'output_f32_sha256'],'0'*64)
    add(['render_cases',0,'alpha','rgba8_byte'],0)
    add(['render_cases',0,'repeat_identical_float32'],False)
    add(['behavioral_mutation_ledger',0,'group'],'forged-group')
    add(['behavioral_mutation_ledger',0,'mechanism'],'forged mechanism')
    add(['behavioral_mutation_ledger',0,'source_relative_path'],'forged.glsl')
    add(['behavioral_mutation_ledger',0,'source_anchor'],'forged anchor')
    add(['behavioral_mutation_ledger',0,'replacement'],'forged replacement')
    add(['behavioral_mutation_ledger',0,'anchor_occurrence_count'],2)
    add(['behavioral_mutation_ledger',0,'source_anchor_sha256'],'0'*64)
    add(['behavioral_mutation_ledger',0,'result_sha256'],'0'*64)
    add(['behavioral_mutation_ledger',0,'witness_cases'],['color-bars'])
    add(['behavioral_mutation_ledger',0,'results',0,'changed_float32_lanes'],0)
    add(['structural_mutation_ledger',0,'anchor'],'forged structural anchor')
    add(['structural_mutation_ledger',0,'replacement'],'forged structural replacement')
    add(['structural_mutation_ledger',0,'mechanism'],'forged structural mechanism')
    add(['structural_mutation_ledger',0,'source_relative_path'],'forged.glsl')
    add(['structural_mutation_ledger',0,'source_anchor_sha256'],'0'*64)
    add(['structural_mutation_ledger',0,'no_pixel_witness_claimed'],False)
    add(['structural_mutation_ledger',0,'no_pixel_witness_claimed'],1)
    add(['authority','import_closure',0,'sha256'],'0'*64)
    add(['factory','text_sha256'],'0'*64)
    add(['provenance','source','relative_path'],'forged.glsl')
    add(['control_group','repeatability','identical_float32'],False)
    add(['claim_boundaries','runtime'],'approximate')
    add(['claim_boundaries','input'],'input lifetime stable')
    for candidate in candidates: assert_forged_rejected(mod,candidate)

def test_generator_anchor_rejects_materializer_and_manifest_forgery():
    tracked=(PACKAGE/'testPattern-oracle-report.md', ORACLE, INCLUDE, COHERENCE, MATERIALIZER)
    originals={p:p.read_bytes() for p in tracked}; sidecars={p.with_name(p.name+'.sha256'):p.with_name(p.name+'.sha256').read_bytes() for p in tracked}
    try:
        forged_materializer=re.sub(rb"COHERENCE_SHA256 = '[0-9a-f]{64}'", b"COHERENCE_SHA256 = '"+b'0'*64+b"'", originals[MATERIALIZER], count=1)
        MATERIALIZER.write_bytes(forged_materializer)
        MATERIALIZER.with_name(MATERIALIZER.name+'.sha256').write_text(f'{hashlib.sha256(forged_materializer).hexdigest()}  {MATERIALIZER.name}\n')
        report=PACKAGE/'testPattern-oracle-report.md'; report.write_bytes(originals[report]+b'\ncoordinated materializer forge\n')
        ORACLE.write_bytes(originals[ORACLE]+b'\n')
        INCLUDE.write_bytes(originals[INCLUDE].replace(b'kSchemaVersion=1u',b'kSchemaVersion=2u',1))
        for path in (report, ORACLE, INCLUDE): path.with_name(path.name+'.sha256').write_text(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n')
        manifest=json.loads(originals[COHERENCE]); manifest['report_sha256']=hashlib.sha256(report.read_bytes()).hexdigest(); manifest['oracle_sha256']=hashlib.sha256(ORACLE.read_bytes()).hexdigest(); manifest['include_sha256']=hashlib.sha256(INCLUDE.read_bytes()).hexdigest()
        payload=(json.dumps(manifest,indent=2)+'\n').encode(); COHERENCE.write_bytes(payload); COHERENCE.with_name(COHERENCE.name+'.sha256').write_text(f'{hashlib.sha256(payload).hexdigest()}  {COHERENCE.name}\n')
        result=run_generator('--check','--cpu-root',str(authority()),env={**os.environ,'NOISEMAKER_FOR_CPU':str(live())})
        assert result.returncode != 0 and 'coherence content anchor drift' in result.stderr
    finally:
        for path,payload in originals.items(): path.write_bytes(payload)
        for path,payload in sidecars.items(): path.write_bytes(payload)

def test_coherence_anchor_rejects_coordinated_manifest_forgery():
    tracked=(GENERATOR, PACKAGE/'testPattern-oracle-report.md', INCLUDE, COHERENCE)
    originals={p:p.read_bytes() for p in tracked}; sidecars={p.with_name(p.name+'.sha256'):p.with_name(p.name+'.sha256').read_bytes() for p in tracked}
    try:
        GENERATOR.write_bytes(originals[GENERATOR]+b'\n// coordinated forge\n')
        report=PACKAGE/'testPattern-oracle-report.md'; report.write_bytes(originals[report]+b'\ncoordinated forge\n')
        INCLUDE.write_bytes(originals[INCLUDE].replace(b'kSchemaVersion=1u',b'kSchemaVersion=2u',1))
        for path in tracked[:3]: path.with_name(path.name+'.sha256').write_text(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n')
        manifest=json.loads(originals[COHERENCE]); manifest['generator_sha256']=hashlib.sha256(GENERATOR.read_bytes()).hexdigest(); manifest['report_sha256']=hashlib.sha256(report.read_bytes()).hexdigest(); manifest['include_sha256']=hashlib.sha256(INCLUDE.read_bytes()).hexdigest()
        payload=(json.dumps(manifest,indent=2)+'\n').encode(); COHERENCE.write_bytes(payload); COHERENCE.with_name(COHERENCE.name+'.sha256').write_text(f'{hashlib.sha256(payload).hexdigest()}  {COHERENCE.name}\n')
        materialized=subprocess.run(['python3',str(MATERIALIZER),'--check'],cwd=ROOT,text=True,capture_output=True)
        assert materialized.returncode != 0 and 'content anchor' in materialized.stderr
        forged_env={**os.environ,'NOISEMAKER_FOR_CPU':str(live())}
        generated=run_generator('--check','--cpu-root',str(authority()),env=forged_env)
        assert generated.returncode != 0 and ('coherence content anchor drift' in generated.stderr or 'anchored materializer coherence check failed' in generated.stderr)
    finally:
        for path,payload in originals.items(): path.write_bytes(payload)
        for path,payload in sidecars.items(): path.write_bytes(payload)

def test_materializer_rejects_nonfinite_controls():
    mod=materializer_module(); candidate=json.loads(ORACLE.read_text()); candidate['render_cases'][0]['tileOffset'][0]=float('nan'); assert_forged_rejected(mod,candidate)


def test_materializer_rejects_path_spellings_recursively():
    mod=materializer_module(); original=json.loads(ORACLE.read_text())
    for value in ('file:///private/tmp/x', '~/x', '$HOME/x', '${HOME}/x', {'$HOME':'bad-key'}, {'nested':['ok', {'path':'foo/$HOME/bar'}]}):
        candidate=copy.deepcopy(original); candidate['provenance']['cpu_root']=value
        assert_forged_rejected(mod,candidate)

def test_coherence_rejects_coordinated_sidecar_forgery():
    mod=materializer_module()
    original_generator=GENERATOR.read_bytes(); generator_side=GENERATOR.with_name(GENERATOR.name+'.sha256').read_bytes()
    original_materializer=MATERIALIZER.read_bytes(); materializer_side=MATERIALIZER.with_name(MATERIALIZER.name+'.sha256').read_bytes()
    try:
        GENERATOR.write_bytes(original_generator+b'\n// forged with matching sidecar\n'); GENERATOR.with_name(GENERATOR.name+'.sha256').write_text(f'{hashlib.sha256(GENERATOR.read_bytes()).hexdigest()}  {GENERATOR.name}\n')
        result=subprocess.run(['python3',str(MATERIALIZER),'--check'],cwd=ROOT,text=True,capture_output=True)
        assert result.returncode != 0
    finally:
        GENERATOR.write_bytes(original_generator); GENERATOR.with_name(GENERATOR.name+'.sha256').write_bytes(generator_side)
    try:
        forged_materializer=re.sub(rb"COHERENCE_SHA256 = '[0-9a-f]{64}'", b"COHERENCE_SHA256 = '"+b'0'*64+b"'", original_materializer, count=1)
        MATERIALIZER.write_bytes(forged_materializer); MATERIALIZER.with_name(MATERIALIZER.name+'.sha256').write_text(f'{hashlib.sha256(MATERIALIZER.read_bytes()).hexdigest()}  {MATERIALIZER.name}\n')
        result=run_generator('--check','--cpu-root',str(authority()))
        assert result.returncode != 0 and 'anchored materializer coherence check failed' in result.stderr
    finally:
        MATERIALIZER.write_bytes(original_materializer); MATERIALIZER.with_name(MATERIALIZER.name+'.sha256').write_bytes(materializer_side)
    with tempfile.TemporaryDirectory() as d:
        forged=pathlib.Path(d)/'report.md'; forged.write_text('forged report\n')
        # The real materializer checks the package report against the manifest; mutate both
        # package bytes and sidecar, then --check must fail on the manifest hash.
        report=PACKAGE/'testPattern-oracle-report.md'; original=report.read_bytes(); side=report.with_name(report.name+'.sha256').read_bytes()
        try:
            report.write_bytes(original+b'forged\n'); report.with_name(report.name+'.sha256').write_bytes(f'{hashlib.sha256(report.read_bytes()).hexdigest()}  {report.name}\n'.encode())
            result=subprocess.run(['python3',str(MATERIALIZER),'--check'],cwd=ROOT,text=True,capture_output=True)
            assert result.returncode != 0
        finally:
            report.write_bytes(original); report.with_name(report.name+'.sha256').write_bytes(side)
    with tempfile.TemporaryDirectory() as d:
        original=INCLUDE.read_bytes(); side=INCLUDE.with_name(INCLUDE.name+'.sha256').read_bytes()
        try:
            INCLUDE.write_bytes(original.replace(b'kSchemaVersion=1u',b'kSchemaVersion=2u',1)); INCLUDE.with_name(INCLUDE.name+'.sha256').write_text(f'{hashlib.sha256(INCLUDE.read_bytes()).hexdigest()}  {INCLUDE.name}\n')
            result=subprocess.run(['python3',str(MATERIALIZER),'--check'],cwd=ROOT,text=True,capture_output=True)
            assert result.returncode != 0
        finally:
            INCLUDE.write_bytes(original); INCLUDE.with_name(INCLUDE.name+'.sha256').write_bytes(side)

def test_include_cxx20_smoke():
    compiler=shutil.which('c++') or shutil.which('clang++')
    if compiler is None: pytest.skip('C++ compiler unavailable')
    with tempfile.TemporaryDirectory() as d:
        source=pathlib.Path(d)/'smoke.cpp'; binary=pathlib.Path(d)/'smoke'
        source.write_text(r'''#include "tests/oracles/testPattern_expected.inc"
#include <cassert>
int main(){using namespace noisemaker_testpattern_oracle;
 static_assert(kBindingAbi.size()==5); static_assert(kCases.size()==9); static_assert(kMutations.size()==9); static_assert(kMutationWitnesses.size()==9); static_assert(kStructuralMutations.size()==2);
 assert(kSchemaVersion==1 && kProgramKey=="synth/testPattern:testPattern"); assert(kSourceBytes==5919 && kSourceSha256.size()==64 && kFactorySha256.size()==64 && kFactoryClosureSha256.size()==64); assert(kInputContract.kind=="source-only" && kInputContract.runtime_input_path=="none" && !kInputContract.lifetime_claimed && !kInputContract.immutability_claimed); assert(kReportSha256.size()==64 && kOracleSha256.size()==64);
 for(const auto& b:kBindingAbi) assert(!b.name.empty()&&!b.runtime_abi.empty()&&!b.source_abi.empty());
 for(const auto& c:kCases){assert(!c.name.empty()&&c.width&&c.height&&c.phase); assert(c.grid_size==c.controls.grid_size&&c.pattern==c.controls.pattern); assert(c.controls.resolution.values[0]>0&&c.controls.full_resolution.values[0]>0); assert(c.output_float_words.size()==c.width*c.height*4&&c.output_rgba8.size()==c.output_float_words.size()); assert(c.output_f32_sha256.size()==64&&c.output_rgba8_sha256.size()==64&&c.alpha_f32_word.size()==10&&c.alpha_rgba8_byte==255); assert(c.repeat_float32&&c.repeat_rgba8&&c.distinct_data_objects&&c.distinct_backing_buffers);}
 for(const auto& m:kMutations){assert(!m.name.empty()&&!m.group.empty()&&!m.mechanism.empty()&&!m.source_relative_path.empty()&&!m.source_anchor.empty()&&!m.replacement.empty()); assert(m.source_anchor_sha256.size()==64&&m.replacement_sha256.size()==64&&m.canonical_factory_sha256.size()==64&&m.mutated_factory_sha256.size()==64&&m.result_sha256.size()==64); assert(m.results.size()==9&&!m.witness_cases.empty()&&!m.required_witness_results.empty()); for(const auto& r:m.results){assert(!r.case_name.empty()&&!r.reason.empty()); assert(r.differs==(r.changed_float32_lanes||r.changed_rgba8_bytes));}}
 for(const auto& w:kMutationWitnesses) assert(!w.mutation_name.empty()&&!w.case_name.empty()&&w.changed_float32_lanes&&w.changed_rgba8_bytes);
 for(const auto& s:kStructuralMutations) assert(!s.name.empty()&&!s.source_relative_path.empty()&&!s.anchor.empty()&&!s.replacement.empty()&&!s.mechanism.empty()&&s.source_anchor_sha256.size()==64&&s.replacement_sha256.size()==64&&s.no_pixel_witness_claimed);
 assert(kControlGroup.repeat_float32&&kControlGroup.repeat_rgba8&&kControlGroup.distinct_data_objects&&kControlGroup.distinct_backing_buffers&&kControlGroup.public_direct_identity&&kControlGroup.canonical_own_key&&!kControlGroup.adapter_own_key); assert(!kClaimBoundaries.authority.empty()&&!kClaimBoundaries.runtime.empty()&&!kClaimBoundaries.input.empty()&&!kClaimBoundaries.structural_mutations.empty());
 auto eq=compare_exact(kCases[0],kCases[0]); assert(eq.equal&&eq.dimensions_ok&&eq.float_count_ok&&eq.rgba8_count_ok&&eq.mismatch==MismatchKind::None); auto dimensions=kCases[0]; dimensions.width++; auto dim=compare_exact(kCases[0],dimensions); assert(!dim.equal&&!dim.dimensions_ok&&dim.mismatch==MismatchKind::Dimensions); auto float_count=kCases[0]; float_count.output_float_words.pop_back(); auto fc=compare_exact(kCases[0],float_count); assert(!fc.equal&&!fc.float_count_ok&&fc.mismatch==MismatchKind::FloatCount); auto rgba_count=kCases[0]; rgba_count.output_rgba8.pop_back(); auto rc=compare_exact(kCases[0],rgba_count); assert(!rc.equal&&!rc.rgba8_count_ok&&rc.mismatch==MismatchKind::Rgba8Count); auto diff=kCases[0]; diff.output_float_words[0]^=1; auto bad=compare_exact(kCases[0],diff); assert(!bad.equal&&bad.first_mismatch==0&&bad.mismatch==MismatchKind::Float32); auto signed_zero=kCases[0]; signed_zero.output_float_words[0]=0x80000000u; assert(compare_exact(kCases[0],signed_zero).mismatch==MismatchKind::Float32); auto nan_payload=kCases[0]; nan_payload.output_float_words[0]=0x7fc00001u; assert(compare_exact(kCases[0],nan_payload).mismatch==MismatchKind::Float32); auto rgba=kCases[0]; rgba.output_rgba8[0]^=1; auto rgba_bad=compare_exact(kCases[0],rgba); assert(!rgba_bad.equal&&rgba_bad.first_mismatch==0&&rgba_bad.mismatch==MismatchKind::Rgba8);}
''')
        result=subprocess.run([compiler,'-std=c++20','-I',str(ROOT),str(source),'-o',str(binary)],text=True,capture_output=True)
        assert result.returncode==0,result.stderr
        assert subprocess.run([str(binary)]).returncode==0
