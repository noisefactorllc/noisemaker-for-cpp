"""Authenticate the exact current Shapes3D dynamic define tree."""
import hashlib
from . import loop_proof as lp
from . import struct_frontier_profile as sf
from . import shapes3d_round_profile as sr

KEY='classicNoisedeck/shapes3d:shapes3d'
RAW='818badfbadcf295d1863d208c0d0582a1349ff64f44dbf43f905a92fcfd4c5ad'
DEFINES=(('BLEND_MODE','str','int'),('SHAPE_A','str','int'),('SHAPE_B','str','int'))
SOURCE_GLOBAL={
    **lp._SOURCE_GLOBAL_LITERAL_INT_PROFILES[KEY],
    'source':'9d7172e600232078e3a839062211078a010916500c9fa28eca1ee93e4defd027',
    'defines':DEFINES,
    'integer':('MAX_STEPS',40,'100',100),
    'globals':(('MIN_DIST',38,'float','0.01'),('MAX_DIST',39,'float','200.0'),('MAX_STEPS',40,'int','100'),('fwdA',64,'mat3',None),('fwdB',65,'mat3',None),('invB',66,'mat3',None),('invA',67,'mat3',None)),
    'reads':(('rayMarch',121,454,25,454,34),),
    'pre_functions':'2de010ae09ba5471fd58470d24b9697b6a3154ded2513d771532333650638e81',
    'post_functions':'19b8390e3a1c9b27e6d1e1426dbb95764bebbe252c9ae16b613bdbdf84cf4638',
    'pre_whole':'5b16e972999ae8b0ac81002c950d3ece1bddba6626a4c3a210a200b8db67eb54',
    'post_whole':'1de623422c24594d21eb07c601f36a4bb90de73cca1cfe68b5b85ef34e14f698',
    'interface':'f480aac072fc94a3dd049f9d9f05ed209776179d9621e5f8496bdf5ec247d752',
}
STRUCT={
    'normalized_bytes':13223,
    'normalized_sha256':SOURCE_GLOBAL['source'],
    'functions_sha256':SOURCE_GLOBAL['post_functions'],
    'whole_sha256':'6ce6fb8e611d09f1ff4a1beefcaea63ef660cd872e21a4ac1853bb40c0cfa559',
    'interface_sha256':'77805614c9db5abd2ee111507102145485fbc8e340daba9307bdb2659f195731',
    'structs_sha256':'31dcf4e9341576df7031ffffec3f88958eeb0937829c923618a6ec342ab48713',
    'returns_sha256':'d21f32f11f838feb6173bdee13332a7b479ba0d5e7774cbe57e54eada03572cd',
    'parameters_sha256':'9f6fb0b9e33347f408ab375ba7b10d0e357680ba2885608558adc64a93c15f7f',
    'locals_sha256':'572adecfd4d50a8e3d2d6568c71fbc64c0881c69c95cc069a5b337d6fbcf4bb4',
    'members_sha256':'f7941b803cd6baffeaf88deb6c10940677d2a9e1575539f0f4f26c033b55a548',
    'census':(2,4,29,0,1509,94),
}
ROUND_SITES=((415,35,'7d40b6f5fc9fcc824dd8053e11c6b8927be850de8701e57c427df747171be1e1','c248789f7c90824ad79323c01b97d6aa911942223f8795acfd1acbbd05811b30'),(422,35,'04279fccbbd836ca62baf1712e51ed33fcbe0e9f463366ec4efa244ceced5912','f44847f2f0ca7d8fc916a0531741a320960052be8d7a3682e115fde548aa285e'))
INDEX_SITES=((195,13,63,'9e9b6c8971eaf4272a3e0ff1f00b407dc5e5cdb7e55093fd05fc4d06bf16f24c'),(196,13,152,'22a6d3db207e4bafbe7a4009f9d6c5fa97b216969004592b73188b6e6793aa33'),(196,23,63,'94b1cab7b22430ce3c26962a5b4a48a2f57a06b697a54b2ca30ed95dc43bb1a5'),(198,13,152,'781f3c52b6842939f63717257d7a9e706a926ed2c146d6b05264947afb16fcf2'),(198,35,63,'d13a69b85082c313dad26a75d27d4d5f7517e8a6687787dc86f57844e6321126'))

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
