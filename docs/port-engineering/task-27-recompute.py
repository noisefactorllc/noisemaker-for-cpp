from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('.')
sys.path.insert(0, str(ROOT))

from tools.glslcpp import generate_typed_slice as gen
from tools.glslcpp import emit_typed_cpp as emit
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program

CORPUS = ROOT / 'tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6'
MANIFEST = json.loads((CORPUS / 'manifest.json').read_text())
ENTRIES = {x['program_key']: x for x in MANIFEST['programs']}
KEYS = ('synth/perlin:perlin', 'mixer/focusBlur:focusBlur', 'filter/rotate:rot')

def digest(value): return hashlib.sha256(repr(value).encode()).hexdigest()
def span(value):
    x=value.span
    return f'{x.start_line}:{x.start_column}-{x.end_line}:{x.end_column}'
def whole(program):
    return digest((program.key, program.source, program.raw_source, program.declarations,
                   program.functions, program.resources, program.body_status,
                   program.local_type_names, program.structs, program.uniform_blocks,
                   program.interface_symbols, program.builtin_symbols,
                   program.counted_loop_proof, program.preprocessor_defines))
def interface(program):
    return digest((program.declarations, program.resources, program.local_type_names,
                   program.structs, program.uniform_blocks, program.interface_symbols,
                   program.builtin_symbols, program.preprocessor_defines))
def expr_nodes(value,path,parent=None,child_index=None):
    yield path,value,parent,child_index
    for i,child in enumerate(value.children): yield from expr_nodes(child,(*path,i),value,i)
def stmt_nodes(value,path):
    for i,x in enumerate(value.expressions): yield from expr_nodes(x,(*path,f'e{i}',0))
    for i,x in enumerate(value.children): yield from stmt_nodes(x,(*path,f's{i}'))
def nodes(function):
    for i,x in enumerate(function.body): yield from stmt_nodes(x,(i,))
def typed(key):
    entry=ENTRIES[key]; raw=(CORPUS/entry['source']).read_text(); defines=gen._defaults(ROOT,key)
    return analyze_program(parse_program(raw,key,defines),key),entry,raw,defines
def bindings(program):
    s={name:i+1 for i,name in enumerate(program.resources.samplers)}; out=[]
    for d in program.declarations:
        if d.symbol.storage=='uniform': out.append(f'{d.symbol.name}:{d.type.display()}@{d.symbol.id}'+(f'/S{s[d.symbol.name]}' if d.symbol.name in s else ''))
        elif d.symbol.storage=='output': out.append(f'{d.symbol.name}:{d.type.display()}@{d.symbol.id}/out')
    return out
def transform_xor_expression(value):
    children=tuple(transform_xor_expression(x) for x in value.children)
    current=dataclasses.replace(value,children=children) if children != value.children else value
    if current.kind=='binary' and current.operator=='^' and current.type.display()=='uint' and all(x.type.display()=='uint' for x in current.children):
        return dataclasses.replace(current,operator='+')
    return current
def transform_xor_statement(value):
    return dataclasses.replace(value,expressions=tuple(transform_xor_expression(x) for x in value.expressions),children=tuple(transform_xor_statement(x) for x in value.children))

results={}
for key in KEYS:
    program,entry,raw,defines=typed(key)
    row={'key':key,'source':entry['source'],'raw_bytes':len(raw.encode()),'raw_sha256':hashlib.sha256(raw.encode()).hexdigest(),'normalized_bytes':len(program.source.encode()),'normalized_sha256':hashlib.sha256(program.source.encode()).hexdigest(),'defines':defines,'function_count':len(program.functions),'function_tuple_sha256':digest(program.functions),'whole_sha256':whole(program),'interface_sha256':interface(program),'function_profiles':[[f.signature.id,f.name,len(f.body),digest(f),f.return_type.display(),[[p.id,p.name,p.type.display(),p.direction] for p in f.parameters]] for f in program.functions],'bindings':bindings(program),'resources':dataclasses.asdict(program.resources),'loop_proof':dataclasses.asdict(program.counted_loop_proof)}
    try:
        gen.validate_capabilities(program,tuple(gen.APPROVED_CAPABILITIES),source_hash=entry['raw_sha256'])
        row['validator']='pass'
    except Exception as e: row['validator']=str(e)
    try:
        emit.render_typed_cpp(program,key,entry['raw_sha256'],'typed_probe','bind_probe')
        row['emitter']='pass'
    except Exception as e: row['emitter']=str(e)
    results[key]=row

program,entry,raw,defines=typed('synth/perlin:perlin')
definitions={f.signature.id:f for f in program.functions if f.body}
main=next(f for f in program.functions if f.name=='main')
reachable={main.signature.id}; pending=[main.signature.id]
while pending:
    f=definitions[pending.pop()]
    for _,v,_,_ in nodes(f):
        if v.kind=='call' and v.signature_id in definitions and v.signature_id not in reachable:
            reachable.add(v.signature_id); pending.append(v.signature_id)
xors=[]
for f in program.functions:
    for path,v,parent,child_index in nodes(f):
        if v.kind=='binary' and v.operator=='^' and v.type.display()=='uint' and all(x.type.display()=='uint' for x in v.children):
            xors.append({'owner_id':f.signature.id,'owner':f.name,'owner_reachable':f.signature.id in reachable,'path':path,'span':span(v),'sha256':digest(v),'left_sha256':digest(v.children[0]),'right_sha256':digest(v.children[1]),'parent_kind':parent.kind if parent else None,'parent_type':parent.type.display() if parent else None,'parent_child_index':child_index,'parent_span':span(parent) if parent else None,'parent_sha256':digest(parent) if parent else None})
projected=dataclasses.replace(program,functions=tuple(dataclasses.replace(f,body=tuple(transform_xor_statement(x) for x in f.body)) for f in program.functions))
gen.validate_capabilities(projected,tuple(gen.APPROVED_CAPABILITIES),source_hash=entry['raw_sha256'])
cpp=emit.render_typed_cpp(projected,program.key,entry['raw_sha256'],'typed_projection','bind_synth_perlin_perlin')
results['synth/perlin:perlin']['scalar_uint_xor_sites']=xors
results['synth/perlin:perlin']['reachable_function_ids']=sorted(reachable)
results['synth/perlin:perlin']['hash3_id']=next(f.signature.id for f in program.functions if f.name=='hash3')
results['synth/perlin:perlin']['xor_bypass_later_blocker']=None
results['synth/perlin:perlin']['xor_bypass_cpp_bytes']=len(cpp.encode())
results['synth/perlin:perlin']['xor_bypass_cpp_sha256']=hashlib.sha256(cpp.encode()).hexdigest()

focus=results['mixer/focusBlur:focusBlur']
fp,_,_,_=typed('mixer/focusBlur:focusBlur')
apply=next(f for f in fp.functions if f.name=='applyFocusBlur')
calls=[]
for f in fp.functions:
    for path,v,parent,child_index in nodes(f):
        if v.kind=='call' and v.signature_id==apply.signature.id:
            calls.append({'owner_id':f.signature.id,'owner':f.name,'path':path,'span':span(v),'sha256':digest(v),'argument_symbols':[[x.symbol_id,x.symbol.name] if x.kind=='id' and x.symbol else None for x in v.children]})
focus['apply_focus_blur']={'id':apply.signature.id,'hash':digest(apply),'parameters':[[p.id,p.name,p.type.display(),p.direction,span(p)] for p in apply.parameters],'calls':calls}

print(json.dumps(results,indent=2))
