"""Prepared, candidate-owned frontend admission for filter/spookyTicker."""
from __future__ import annotations
import hashlib
import re
from collections import Counter
from typing import NamedTuple
from .typed_ir import TypedExpression, TypedProgram

KEY = "filter/spookyTicker:spookyTicker"
PROFILE = "spooky-ticker-frontend-admission-v1"
KEYS: tuple[str, ...] = ()
PROFILES = {KEY: PROFILE}
PREPARED_KEYS = (KEY,)
PREPARED_PROFILES = {KEY: PROFILE}
SPOOKY_TICKER_FRONTEND_KEYS = frozenset(PREPARED_PROFILES)
ALLOWED_ROW_FIELDS = {KEY: frozenset({"defines", "program_key", "spooky_ticker_frontend_profile"})}
REQUIRED_COMPANION_PROFILES = {KEY: ()}
SOURCE_PATH = "filter/spookyTicker/spookyTicker.glsl"
RAW_BYTES = 4276
RAW_SHA256 = "d50ca880cd6c6c03dd01a7ae683316d42ed93baddaadce9f3b918be1c816d50f"
NORMALIZED_BYTES = 3393
NORMALIZED_SHA256 = "d63a565fa4a814fa2377cd82a464fb296ee566dbbb0c8a5c0763193a33094830"
FUNCTIONS_SHA256 = "85f513682946098d4cadc6e19b46db1d336a55ae9273e9154061396915cd99b6"
WHOLE_SHA256 = "4c8ac00d1365967229a412e4f6e6a5180a34842affc99014dd82314e22bea2fd"
INTERFACE_SHA256 = "3d84a19370581017b270e9ffd5a4a2794e4976e8047b1427955e38a8f6abf5ce"
SOURCE_UNIFORMS = (("inputTex","sampler2D"),("renderScale","float"),("time","float"),("speed","float"),("alpha","float"),("rows","int"),("seed","int"))
RUNTIME_UNIFORM_ABI = (("renderScale","float"),("time","float"),("speed","float"),("alpha","float"),("rows","int32"),("seed","int32"))
SAMPLER_RUNTIME_ABI = ("inputTex","sampler2D","const Surface&")
VARYING_RUNTIME_ABI = ("v_texCoord","vec2","context.uv","glsl::Vec2")
TEXTURE_SIZE_CONTRACT = ("textureSize","ivec2",0)
TEXTURE_SAMPLE_CONTRACT = ("texture","vec4","inputTex","v_texCoord")
GLOBAL_ARRAY_NATIVE_REQUIREMENT = ("int[80]","std::array<std::int32_t, 80>")
BITWISE_REQUIREMENT = ("^",">>","&")
_OPTIONAL_PROOF_FIELDS = ("fixed_nine_table_proof","fixed_grid_counter_store_proof","fixed_array_in_parameter_proof","fixed_affine_centers13_proof")
_EXPECTED_RESOURCE = (tuple(x[0] for x in SOURCE_UNIFORMS),("inputTex",),("fragColor",),True,False)
_EXPECTED_COUNTED_LOOP = (0,0,0,0,0,True)
_EXPECTED_EXPR_KINDS = {"id":121,"literal":117,"binary":69,"declaration":30,"construct":21,"assign":11,"builtin":10,"call":7,"swizzle":6,"index":1,"conditional":1}
_EXPECTED_OPERATORS = {"*":23,"=":11,"+":9,"-":6,">=":6,"/":6,"^":5,">>":4,"||":4,"<":3,"&":2,"%":1}
_GLYPHS = tuple(int(x,16) for x in "3C 42 42 42 42 42 3C 00 18 08 08 08 1C 1C 1C 00 1C 04 04 1C 10 10 1C 00 1C 04 04 1C 06 06 1E 00 60 60 60 60 66 7E 06 00 3C 20 20 3C 04 04 3C 00 78 48 40 40 7E 42 7E 00 3C 24 04 0C 08 08 08 00 3C 24 24 7E 66 66 7E 00 3E 22 22 3E 06 06 06 00".split())
_EXPECTED_BITWISE = (("^","uint","48:9-48:23",("uint","uint")),(">>","uint","48:14-48:22",("uint","uint")),("^","uint","50:9-50:23",("uint","uint")),(">>","uint","50:14-50:22",("uint","uint")),("^","uint","52:9-52:23",("uint","uint")),(">>","uint","52:14-52:22",("uint","uint")),("&","int","63:19-63:39",("int","int")),(">>","int","63:19-63:34",("int","int")),("&","uint","69:37-69:76",("uint","uint")),("^","uint","69:46-69:65",("uint","uint")),("^","uint","78:23-78:57",("uint","uint")))
_EXPECTED_BUILTINS = (("max","int","86:18-86:62"),("max","int","89:19-89:65"),("textureSize","ivec2","91:22-91:46"),("texture","vec4","92:16-92:45"),("floor","float","101:18-101:46"),("floor","float","102:28-102:64"),("max","int","126:21-126:51"),("max","vec3","137:14-137:45"),("clamp","vec3","139:22-139:45"),("floor","float","70:22-70:52"))
_EXPECTED_CALLS = (("hash_mix","95:21-95:49"),("hash_mix","119:23-119:56"),("ticker_row_mask","122:18-122:73"),("ticker_row_mask","129:18-129:91"),("hash_mix","69:37-69:66"),("hash_mix","78:14-78:58"),("sample_glyph","81:12-81:55"))
_NUMBER_PARAMETER_IDS = (14, 16, 17, 20)
_NUMBER_DECLARATION_IDS = (51, 52, 57, 58, 59, 43, 44, 49)
_NUMBER_DIVISION_SPANS = (
    "59:14-59:29", "60:14-60:29", "74:27-74:38",
    "74:42-74:67", "111:18-111:42",
)
_NUMBER_UMUL_SPANS = ("49:9-49:24", "51:9-51:24")
_NUMBER_REMAINDER_SPANS = ("79:21-79:28",)
_RAW_VARYING = re.compile(r"^[ \t]*in[ \t]+vec2[ \t]+v_texCoord[ \t]*;[ \t]*$", re.MULTILINE)

class ArrayRecord(NamedTuple):
    name:str; symbol_id:int; type_name:str; element_type:str; extent:int; storage:str; writable:bool; span:str; initializer_sha256:str
class VaryingReadRecord(NamedTuple):
    symbol_id:int; span:str; node_sha256:str; parent_kind:str; parent_operator:str|None; owner:str; node:TypedExpression
class FrontendProof(NamedTuple):
    program_key:str; varying_symbol:object; varying_reads:tuple[VaryingReadRecord,...]; global_array:ArrayRecord; array_index:TypedExpression; bitwise_nodes:tuple[TypedExpression,...]; closure_functions:tuple[object,...]; number_parameters:tuple[object,...]; number_declarations:tuple[TypedExpression,...]; number_divisions:tuple[TypedExpression,...]; number_umul_nodes:tuple[TypedExpression,...]; number_remainder_nodes:tuple[TypedExpression,...]; consumed_objects:tuple[object,...]

def _sha(x): return hashlib.sha256(repr(x).encode()).hexdigest()
def _span(x):
    s=x.span; return f"{s.start_line}:{s.start_column}-{s.end_line}:{s.end_column}"
def _whole(p): return _sha((p.key,p.source,p.raw_source,p.declarations,p.functions,p.resources,p.body_status,p.local_type_names,p.structs,p.uniform_blocks,p.interface_symbols,p.builtin_symbols,p.counted_loop_proof,p.preprocessor_defines))
def _interface(p): return _sha((p.declarations,p.resources,p.local_type_names,p.structs,p.uniform_blocks,p.interface_symbols,p.builtin_symbols,p.preprocessor_defines))
def _walk(x):
    yield x
    for c in x.children: yield from _walk(c)
def _walk_stmt(s):
    for e in s.expressions: yield from _walk(e)
    for c in s.children: yield from _walk_stmt(c)
def _expressions(p):
    out=[]
    for d in p.declarations:
        if d.initializer is not None: out.extend(_walk(d.initializer))
    for f in p.functions:
        for s in f.body: out.extend(_walk_stmt(s))
    return tuple(out)
def _nodes(x,parent=None):
    for e in x.expressions: yield e,parent; yield from _nodes_expr(e)
    for c in x.children: yield from _nodes(c,parent)
def _nodes_expr(e):
    for c in e.children:
        yield c,e; yield from _nodes_expr(c)
def _decl_lock(p): return tuple((d.symbol.id,d.symbol.name,d.type.display(),d.symbol.storage,d.symbol.writable,d.symbol.direction,_span(d)) for d in p.declarations)
def _read_records(p):
    return tuple(VaryingReadRecord(e.symbol_id,_span(e),_sha(e),parent.kind if parent else "",getattr(parent,"operator",None) if parent else None,f.name,e) for f in p.functions for s in f.body for e,parent in _nodes(s) if e.kind=="id" and e.symbol_id==30)

def _expected_functions(p):
    by_name={f.name:f for f in p.functions}
    names=("main","hash_mix","sample_glyph","ticker_row_mask")
    if tuple(f.name for f in p.functions) != ("hash_mix","main","sample_glyph","ticker_row_mask"):
        raise _fail("function identity inventory mismatch")
    if any(name not in by_name for name in names): raise _fail("candidate closure function missing")
    return tuple(by_name[name] for name in names)

def verify_spooky_ticker_frontend(program:TypedProgram, proof:FrontendProof)->FrontendProof:
    """Verify that a proof still names this exact typed program's live objects."""
    if program.key!=KEY or proof.program_key!=KEY: raise _fail("proof/program key mismatch")
    funcs=_expected_functions(program)
    if len(proof.closure_functions)!=len(funcs) or any(a is not b for a,b in zip(proof.closure_functions,funcs)):
        raise _fail("closure function identity mismatch")
    xs=_expressions(program)
    indexes=tuple(x for x in xs if x.kind=="index")
    bits=tuple(x for x in xs if x.kind=="binary" and x.operator in BITWISE_REQUIREMENT)
    reads=tuple(x for x in xs if x.kind=="id" and x.symbol_id==30)
    parameters=tuple(parameter for function in program.functions for parameter in function.parameters if parameter.id in _NUMBER_PARAMETER_IDS)
    declaration_map={x.symbol_id:x for x in xs if x.kind=="declaration" and x.symbol_id in _NUMBER_DECLARATION_IDS}
    declarations=tuple(declaration_map[symbol_id] for symbol_id in _NUMBER_DECLARATION_IDS)
    division_map={_span(x):x for x in xs if x.kind=="binary" and x.operator=="/" and _span(x) in _NUMBER_DIVISION_SPANS}
    divisions=tuple(division_map[item_span] for item_span in _NUMBER_DIVISION_SPANS)
    umuls=tuple(x for x in xs if x.kind=="binary" and x.operator=="*" and _span(x) in _NUMBER_UMUL_SPANS)
    remainders=tuple(x for x in xs if x.kind=="binary" and x.operator=="%" and _span(x) in _NUMBER_REMAINDER_SPANS)
    if proof.array_index is not indexes[0] or any(a is not b for a,b in zip(proof.bitwise_nodes,bits)):
        raise _fail("closure node identity mismatch")
    if tuple(r.node for r in proof.varying_reads)!=reads: raise _fail("varying read identity mismatch")
    if proof.varying_symbol is not program.interface_symbols[0]: raise _fail("varying symbol identity mismatch")
    for actual, expected, label in (
        (proof.number_parameters, parameters, "Number parameter"),
        (proof.number_declarations, declarations, "Number declaration"),
        (proof.number_divisions, divisions, "Number division"),
        (proof.number_umul_nodes, umuls, "Number umul"),
        (proof.number_remainder_nodes, remainders, "Number remainder"),
    ):
        if len(actual)!=len(expected) or any(a is not b for a,b in zip(actual,expected)):
            raise _fail(f"{label} identity mismatch")
    array=next(d for d in program.declarations if d.symbol.name=="GLYPHS")
    if proof.global_array.symbol_id!=array.symbol.id: raise _fail("global array identity mismatch")
    ledger=(*funcs,proof.array_index,*proof.bitwise_nodes,*reads,*parameters,*declarations,*divisions,*umuls,*remainders)
    if len(ledger)!=len({id(x) for x in ledger}): raise _fail("identity ledger is not disjoint")
    if any(sum(x is y for y in ledger)!=1 for x in ledger): raise _fail("identity ledger is not exact-once")
    if len(proof.consumed_objects)!=len(ledger) or any(a is not b for a,b in zip(proof.consumed_objects,ledger)):
        raise _fail("consumed object ledger is not program-bound")
    return proof

def authenticate_spooky_ticker_frontend(program:TypedProgram, source_hash:str|None, profile:str|None)->FrontendProof:
    fail=lambda m: _fail(m)
    if program.key!=KEY: raise fail("selected key is not filter/spookyTicker:spookyTicker")
    if profile!=PROFILE: raise fail("exact prepared profile required")
    raw=program.raw_source.encode(); norm=program.source.encode()
    if source_hash!=RAW_SHA256 or len(raw)!=RAW_BYTES or hashlib.sha256(raw).hexdigest()!=RAW_SHA256: raise fail("source hash or raw byte lock mismatch")
    if len(norm)!=NORMALIZED_BYTES or hashlib.sha256(norm).hexdigest()!=NORMALIZED_SHA256: raise fail("normalized source lock mismatch")
    if _sha(program.functions)!=FUNCTIONS_SHA256 or _whole(program)!=WHOLE_SHA256: raise fail("typed function or whole-program fingerprint mismatch")
    if _interface(program)!=INTERFACE_SHA256: raise fail("interface fingerprint mismatch")
    if program.preprocessor_defines or program.body_status!="analyzed": raise fail("preprocessor or body status mismatch")
    if any(getattr(program,x,None) is not None for x in _OPTIONAL_PROOF_FIELDS): raise fail("unrelated proof carrier is present")
    q=program.counted_loop_proof
    if q is None or tuple(getattr(q,x) for x in ("loop_count","unproved_loop_count","max_effective_depth","max_lexical_product","entrypoint_charge","call_graph_acyclic"))!=_EXPECTED_COUNTED_LOOP: raise fail("counted-loop proof mismatch")
    if (program.resources.uniforms,program.resources.samplers,program.resources.outputs,program.resources.uses_texture,program.resources.uses_derivatives)!=_EXPECTED_RESOURCE: raise fail("resource or sampler interface mismatch")
    expected=((1,"inputTex","sampler2D","uniform",False,"in","7:1-7:28"),(2,"renderScale","float","uniform",False,"in","8:1-8:27"),(3,"time","float","uniform",False,"in","9:1-9:20"),(4,"speed","float","uniform",False,"in","10:1-10:21"),(5,"alpha","float","uniform",False,"in","11:1-11:21"),(6,"rows","int","uniform",False,"in","12:1-12:18"),(7,"seed","int","uniform",False,"in","13:1-13:18"),(8,"fragColor","vec4","output",True,"in","15:1-15:16"),(9,"GLYPHS","int[80]","const",False,"in","19:1-40:3"),(10,"GLYPH_W","int","const",False,"in","42:1-42:23"),(11,"GLYPH_H","int","const",False,"in","43:1-43:23"),(12,"BASE_SCALE","int","const",False,"in","44:1-44:26"),(13,"BASE_ROW_GAP","int","const",False,"in","45:1-45:28"))
    if _decl_lock(program)!=expected: raise fail("global declaration inventory mismatch")
    xs=_expressions(program)
    if Counter(x.kind for x in xs)!=Counter(_EXPECTED_EXPR_KINDS): raise fail("expression-kind cardinality mismatch")
    if Counter(x.operator for x in xs if x.operator is not None)!=Counter(_EXPECTED_OPERATORS): raise fail("operator cardinality mismatch")
    if tuple((x.callee,x.type.display(),_span(x)) for x in xs if x.kind=="builtin")!=_EXPECTED_BUILTINS: raise fail("builtin census mismatch")
    if tuple((x.callee,_span(x)) for x in xs if x.kind=="call")!=_EXPECTED_CALLS: raise fail("candidate closure call census mismatch")
    array=next(d for d in program.declarations if d.symbol.name=="GLYPHS"); init=array.initializer
    if init is None or init.kind!="construct" or init.type.display()!="int[80]" or len(init.children)!=80 or tuple(int(x.literal,0) for x in init.children)!=_GLYPHS: raise fail("GLYPHS literal payload mismatch")
    indexes=tuple(x for x in xs if x.kind=="index")
    if len(indexes)!=1 or (_span(indexes[0]),indexes[0].type.display(),indexes[0].children[0].symbol_id,indexes[0].children[0].symbol.name,indexes[0].children[1].kind,indexes[0].children[1].type.display())!=("62:15-62:37","int",9,"GLYPHS","binary","int"): raise fail("GLYPHS index shape mismatch")
    bits=tuple(x for x in xs if x.kind=="binary" and x.operator in BITWISE_REQUIREMENT)
    if tuple((x.operator,x.type.display(),_span(x),tuple(c.type.display() for c in x.children)) for x in bits)!=_EXPECTED_BITWISE: raise fail("signed/unsigned bitwise census mismatch")
    sampler=tuple(x for x in xs if x.kind=="builtin" and x.callee in ("textureSize","texture"))
    if tuple(x.callee for x in sampler)!=("textureSize","texture") or sampler[0].children[0].symbol.name!="inputTex" or sampler[0].children[1].literal_value!=0 or sampler[1].children[0].symbol.name!="inputTex": raise fail("sampler contract mismatch")
    if len(program.interface_symbols)!=1: raise fail("varying interface cardinality mismatch")
    varying=program.interface_symbols[0]
    if (varying.name,varying.storage,varying.writable,varying.direction,varying.type.display())!=("v_texCoord","varying",False,"in","vec2") or _span(varying)!="1:1-141:1" or _sha(varying)!="1e991b5cbeb4ea7cc4886cd20dc1eaaeca92070627a04be7dcb6808850da5310": raise fail("varying identity mismatch")
    m=list(_RAW_VARYING.finditer(program.raw_source))
    if len(m)!=1 or program.raw_source.count("\n",0,m[0].start())+1!=16: raise fail("raw varying declaration site mismatch")
    reads=_read_records(program)
    if len(reads)!=3 or tuple(x.span for x in reads)!=("92:34-92:44","101:24-101:34","102:41-102:51"): raise fail("varying read census mismatch")
    functions=_expected_functions(program)
    parameters=tuple(parameter for function in program.functions for parameter in function.parameters if parameter.id in _NUMBER_PARAMETER_IDS)
    if tuple(parameter.id for parameter in parameters)!=_NUMBER_PARAMETER_IDS: raise fail("Number parameter census mismatch")
    declarations_by_id={x.symbol_id:x for x in xs if x.kind=="declaration" and x.symbol_id in _NUMBER_DECLARATION_IDS}
    if set(declarations_by_id)!=set(_NUMBER_DECLARATION_IDS): raise fail("Number declaration census mismatch")
    declarations=tuple(declarations_by_id[symbol_id] for symbol_id in _NUMBER_DECLARATION_IDS)
    divisions_by_span={_span(x):x for x in xs if x.kind=="binary" and x.operator=="/" and _span(x) in _NUMBER_DIVISION_SPANS}
    if set(divisions_by_span)!=set(_NUMBER_DIVISION_SPANS): raise fail("Number division census mismatch")
    divisions=tuple(divisions_by_span[item_span] for item_span in _NUMBER_DIVISION_SPANS)
    if tuple(_span(x) for x in divisions)!=_NUMBER_DIVISION_SPANS: raise fail("Number division census mismatch")
    umuls=tuple(x for x in xs if x.kind=="binary" and x.operator=="*" and _span(x) in _NUMBER_UMUL_SPANS)
    if tuple(_span(x) for x in umuls)!=_NUMBER_UMUL_SPANS: raise fail("Number umul census mismatch")
    remainders=tuple(x for x in xs if x.kind=="binary" and x.operator=="%" and _span(x) in _NUMBER_REMAINDER_SPANS)
    if tuple(_span(x) for x in remainders)!=_NUMBER_REMAINDER_SPANS: raise fail("Number remainder census mismatch")
    vids=[x for x in xs if x.kind=="id" and x.symbol_id==30]; consumed=(*functions,indexes[0],*bits,*vids)
    consumed=(*consumed,*parameters,*declarations,*divisions,*umuls,*remainders)
    if len(consumed)!=len({id(x) for x in consumed}): raise fail("candidate-owned identity ledger overlaps")
    result=FrontendProof(KEY,varying,reads,ArrayRecord("GLYPHS",array.symbol.id,array.type.display(),"int",80,array.symbol.storage,array.symbol.writable,_span(array),_sha(init)),indexes[0],bits,functions,parameters,declarations,divisions,umuls,remainders,consumed)
    return verify_spooky_ticker_frontend(program,result)
def apply_spooky_ticker_frontend(program,source_hash,profile): authenticate_spooky_ticker_frontend(program,source_hash,profile); return program
def _fail(message): return ValueError(f"{PROFILE}: {message}")
