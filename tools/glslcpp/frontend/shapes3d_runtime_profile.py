"""Authenticate the exact current Shapes3D dynamic define tree."""
import hashlib
from . import loop_proof as lp
from . import struct_frontier_profile as sf
from . import shapes3d_round_profile as sr

KEY='classicNoisedeck/shapes3d:shapes3d'
RAW='e17550180972bf97883c33eb4b280bfb3456d9212162c91e76cc8befbae941dc'
DEFINES=(('BLEND_MODE','str','int'),('SHAPE_A','str','int'),('SHAPE_B','str','int'))
SOURCE_GLOBAL={
    **lp._SOURCE_GLOBAL_LITERAL_INT_PROFILES[KEY],
    'source':'686b78a3907e7ca7e3e54540e33872cf69290c0dcc49be57d22940db55e5fbc0',
    'defines':(('BLEND_MODE', 'str', 'int'), ('SHAPE_A', 'str', 'int'), ('SHAPE_B', 'str', 'int')),
    'integer':('MAX_STEPS', 40, '100', 100),
    'globals':(('MIN_DIST', 38, 'float', '0.01'),
 ('MAX_DIST', 39, 'float', '200.0'),
 ('MAX_STEPS', 40, 'int', '100'),
 ('fwdA', 64, 'mat3', None),
 ('fwdB', 65, 'mat3', None),
 ('invB', 66, 'mat3', None),
 ('invA', 67, 'mat3', None)),
    'reads':(('rayMarch', 121, 452, 25, 452, 34),),
    'pre_functions':'5067e298d11a66e13ed4a75272695ad948ec9e7c88824dd18b78343d794ad4b3',
    'post_functions':'72c61beb04a80246634aa433fa7ef0065a47a47dfed7688844fb308319bf0bb3',
    'pre_whole':'6ea2a2a8641b6cecd71134196a21f7de9297292dc3b253fa9f0fe7c47a8c1e97',
    'post_whole':'573042d824cb84682c0cda3eaf07a59c0b53de425ce053a6a0e33c4611e80cce',
    'interface':'87fbe0cfc5754b191c8c85a892a77d2b20ff2145907fe8fb8c5b04e6fe194a9b',
}
STRUCT={
    'normalized_bytes':13146,
    'normalized_sha256':SOURCE_GLOBAL['source'],
    'functions_sha256':SOURCE_GLOBAL['post_functions'],
    'whole_sha256':'c6ae975864a68e553bb0fbb4e793a932a4707605121fed1adfbb2078b3903507',
    'interface_sha256':'82c5020cb65855377f2cfea181166c94779b7a14b631bd349e9b6cfa4f5475b2',
    'structs_sha256':'31dcf4e9341576df7031ffffec3f88958eeb0937829c923618a6ec342ab48713',
    'returns_sha256':'d21f32f11f838feb6173bdee13332a7b479ba0d5e7774cbe57e54eada03572cd',
    'parameters_sha256':'9f6fb0b9e33347f408ab375ba7b10d0e357680ba2885608558adc64a93c15f7f',
    'locals_sha256':'0df6de8e0c7e0aedb934d808c81d99d8a9bb4cc05eccf3ce0363e6947dde9f26',
    'members_sha256':'6331c1cd2620f73632a5efeed1b6374da8e594f4ee7dc8d5d5c8680e67ed94d7',
    'census':(2, 4, 29, 0, 1494, 93),
}
ROUND_SITES=((413,
  35,
  '544a0fae68a0ebca773f0b127268362cf7c8bcc37c0f19915fdd0a17e31e7491',
  '5fa874d640cb48927b455398bcb8ef9cd41a75d84d2e4918449383eb23a02b63'),
 (420,
  35,
  '85f3bb68b483d6e5e5d743daaf2b5d66e2f84ad6a8e4b1f104f22050ebbc3fb9',
  '78daf1c7263e2582491890a35137e588d6a09149f8ba8e5d08ac3c0f2d6dc7c1'))
INDEX_SITES=((193, 13, 63, 'cc544821fcfa3a932b4ec1bd5e0685911ee53f487139eafa2a2c2ef842894e65'),
 (194, 13, 152, 'bdf1c983219388eb8231132c3cafaf9086baed85407908ea70898b72327fb08a'),
 (194, 23, 63, 'bf729da7f9878f6ff0d1da73726e06c1de809e29c4d9111984e414a2915ad267'),
 (196, 13, 152, '69a5720fe9d9af41fdcb11dd39a01b2eb6e4892a3aa35d6e0602d13b4c199fa1'),
 (196, 35, 63, 'f048529c762f325f8736620668d5092d1e7a7996854dec2697a6d1d66ca6994a'))
def authenticate(program, source_hash):
    if program.key != KEY or source_hash != RAW or hashlib.sha256(program.raw_source.encode()).hexdigest()!=RAW:
        raise ValueError('dynamic Shapes3D raw source drift')
    if len(program.source.encode())!=STRUCT['normalized_bytes'] or hashlib.sha256(program.source.encode()).hexdigest()!=STRUCT['normalized_sha256']:
        raise ValueError('dynamic Shapes3D normalized source drift')
    if tuple((d.name,d.kind,d.canonical_value) for d in program.preprocessor_defines)!=DEFINES:
        raise ValueError('dynamic Shapes3D define drift')
    if (program.body_status!='analyzed' or sf._sha(program.functions)!=STRUCT['functions_sha256'] or sf._sha(sf._whole(program))!=STRUCT['whole_sha256'] or sf._sha(sf._interface(program))!=STRUCT['interface_sha256']):
        raise ValueError('dynamic Shapes3D typed tree drift')
    if program.counted_loop_proof.loop_count!=2 or program.counted_loop_proof.unproved_loop_count!=0 or program.counted_loop_proof.max_lexical_product!=100 or program.counted_loop_proof.entrypoint_charge!=103:
        raise ValueError('dynamic Shapes3D counted-loop drift')
    structs=sf._derive_structs(program)
    returns=sf._derive_return_functions(program)
    parameters=sf._derive_parameters(program)
    locals_,members,constructors,nodes,assigns=sf._derive_census(program)
    sl,sm=sf._sort_census(locals_,members)
    checks={'structs_sha256':structs,'returns_sha256':returns,'parameters_sha256':parameters,'locals_sha256':sl,'members_sha256':sm}
    if any(sf._sha(value)!=STRUCT[name] for name,value in checks.items()) or (len(program.structs),len(sl),len(sm),len(constructors),nodes,assigns)!=STRUCT['census']:
        raise ValueError('dynamic Shapes3D struct census drift')
    locals_by_symbol={item.symbol.id:(function,item,item.symbol,statement) for function,statement,item,_parent in sf._program_nodes(program) if item.kind=='declaration' and item.symbol is not None and item.symbol.type.kind=='struct'}
    ordered_locals=tuple(locals_by_symbol[record[1]] for record in sl)
    ordered_members=tuple(next(item for _function,_statement,item,_parent in sf._program_nodes(program) if item.kind=='member' and sf._span(item)==record[8] and sf._sha(item)==record[9]) for record in sm)
    consumed=tuple((*program.structs,*(field for item in program.structs for field in item.fields),*(item for item in program.functions if item.return_type.kind=='struct'),*(item for _function,item,_symbol,_statement in ordered_locals),*(symbol for _function,_item,symbol,_statement in ordered_locals),*ordered_members))
    if len(consumed)!=54 or len({id(x) for x in consumed})!=54:
        raise ValueError('dynamic Shapes3D struct consumption drift')
    owner=next((f for f in program.functions if f.id==105 and f.name=='applyTransform'),None)
    rounds=tuple(v for f in program.functions for st in f.body for v in sr._statements(st) if v.kind=='builtin' and v.callee=='round')
    owned=tuple(v for st in owner.body for v in sr._statements(st) if v.kind=='builtin' and v.callee=='round') if owner else ()
    if len(rounds)!=2 or any(a is not b for a,b in zip(rounds,owned)):
        raise ValueError('dynamic Shapes3D round owner drift')
    for node,(line,column,digest,arg) in zip(owned,ROUND_SITES):
        if node.span.start_line!=line or node.span.start_column!=column or node.signature_id!=-38 or node.type.display()!='vec3' or node.category!='rvalue' or len(node.children)!=1 or node.children[0].type.display()!='vec3' or sr._sha(node)!=digest or sr._sha(node.children[0])!=arg:
            raise ValueError('dynamic Shapes3D round site drift')
    owner=next((f for f in program.functions if f.id==112 and f.name=='linearToSrgb'),None)
    if owner is None or owner.return_type.display()!='vec3' or tuple((p.id,p.name,p.type.display(),p.direction) for p in owner.parameters)!=((63,'linear','vec3','in'),) or tuple(x.kind for x in owner.body)!=('decl','for','return'):
        raise ValueError('dynamic Shapes3D lane owner drift')
    decl,loop,returned=owner.body
    p=loop.loop_proof
    if p is None or (p.induction_symbol_id,p.start_value,p.bound_value,p.comparison,p.update,p.bound_kind,p.trip_count,p.lexical_depth,p.effective_depth,p.lexical_product,p.entrypoint_charge)!=(153,0,3,'<','++','literal',3,1,1,3,103) or decl.expressions[0].symbol_id!=152 or returned.expressions[0].symbol_id!=152:
        raise ValueError('dynamic Shapes3D lane loop drift')
    indices=tuple(v for f in program.functions for st in f.body for v in sr._statements(st) if v.kind=='index')
    owned=tuple(v for st in owner.body for v in sr._statements(st) if v.kind=='index')
    if len(indices)!=5 or any(a is not b for a,b in zip(indices,owned)):
        raise ValueError('dynamic Shapes3D lane census drift')
    for node,(line,column,base,digest) in zip(owned,INDEX_SITES):
        if node.span.start_line!=line or node.span.start_column!=column or node.type.display()!='float' or len(node.children)!=2 or node.children[0].symbol_id!=base or node.children[1].symbol_id!=153 or sr._sha(node)!=digest:
            raise ValueError('dynamic Shapes3D lane site drift')
    if len(loop.children)!=2 or loop.children[1].kind!='block' or len(loop.children[1].children)!=1 or loop.children[1].children[0].kind!='if':
        raise ValueError('dynamic Shapes3D lane branch drift')
    conditional=loop.children[1].children[0]
    if len(conditional.children)!=2 or any(branch.kind!='block' or len(branch.children)!=1 or branch.children[0].kind!='expr' or branch.children[0].expressions[0].kind!='assign' or branch.children[0].expressions[0].operator!='=' for branch in conditional.children) or any(branch.children[0].expressions[0].children[0] is not index for branch,index in zip(conditional.children,(owned[1],owned[3]))):
        raise ValueError('dynamic Shapes3D lane write path drift')
    for sid,count in ((63,3),(152,4),(153,8)):
        refs=tuple(v for f in program.functions for st in f.body for v in sr._statements(st) if v.symbol_id==sid)
        if len(refs)!=count:raise ValueError('dynamic Shapes3D lane reference drift')
    struct_record=sf.StructFrontierRecord(tuple(program.structs),
        tuple(item.type for item in program.structs), ordered_locals,
        ordered_members, consumed)
    return struct_record,owned,rounds
