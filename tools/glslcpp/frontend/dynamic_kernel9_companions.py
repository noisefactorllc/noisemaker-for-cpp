"""Candidate-owned companion nodes for exact live convolution programs."""
from __future__ import annotations

import math

from . import dynamic_kernel9_profile as kernel
from .typed_ir import TypedExpression, TypedProgram


def _required(program: TypedProgram, source_hash: str | None, key: str):
    if (program.key != key or source_hash != kernel.row_for(program)['raw']
            or kernel.prove(program) is None):
        raise ValueError('dynamic Kernel9 companion source or tree mismatch')


def kaleido_xors(program: TypedProgram, source_hash: str | None):
    from . import scalar_uint_xor_profile as scalar
    key = 'classicNoisedeck/kaleido:kaleido'
    _required(program, source_hash, key)
    found = []
    for function in program.functions:
        for statement in function.body:
            for node, parent in scalar._walk_statement(statement):
                if (node.kind == 'binary' and node.operator == '^'
                        and node.type.display() == 'uint'):
                    found.append((function, node, parent))
    spans = ('162:10-162:46', '163:10-163:46', '164:10-164:47')
    if (len(found) != 3
            or tuple(scalar._span(node) for _, node, _ in found) != spans
            or any(function.name != 'randomFromLatticeWithOffset'
                   or function.id != 147
                   or parent is None or parent.kind != 'construct'
                   or parent.type.display() != 'uvec3'
                   or node not in parent.children
                   or len(node.children) != 2
                   or any(child.type.display() != 'uint'
                          for child in node.children)
                   for function, node, parent in found)):
        raise ValueError('dynamic Kaleido scalar XOR closure mismatch')
    return tuple(node for _, node, _ in found)


def kaleido_ingress(program: TypedProgram, source_hash: str | None):
    from . import scalar_uint_xor_profile as scalar
    xors = kaleido_xors(program, source_hash)
    found = []
    for function in program.functions:
        for statement in function.body:
            for node, parent in scalar._walk_statement(statement):
                if node.kind == 'builtin' and node.callee == 'floatBitsToUint':
                    found.append((function, node, parent))
    if len(found) != 1:
        raise ValueError('dynamic Kaleido float-bit ingress census mismatch')
    function, node, parent = found[0]
    if (function.id != 147 or function.name != 'randomFromLatticeWithOffset'
            or scalar._span(node) != '159:21-159:46'
            or node.type.display() != 'uint'
            or len(node.children) != 1
            or node.children[0].symbol is None
            or node.children[0].symbol.name != 'seedFrac'
            or parent is None or parent.kind != 'declaration'
            or parent.symbol is None or parent.symbol.name != 'fracBits'
            or parent.children != (node,)):
        raise ValueError('dynamic Kaleido float-bit ingress identity mismatch')
    seed = next((x for statement in function.body
                 for x, _ in scalar._walk_statement(statement)
                 if x.kind == 'declaration' and x.symbol is not None
                 and x.symbol.name == 'seedFrac'), None)
    if (seed is None or len(seed.children) != 1
            or seed.children[0].kind != 'literal'
            or seed.children[0].literal_value != 0.0
            or math.copysign(1.0, seed.children[0].literal_value) != 1.0):
        raise ValueError('dynamic Kaleido positive-zero ingress source mismatch')
    frac_id = parent.symbol_id
    if any(x.children[0].children[0].symbol_id != frac_id
           for x in xors):
        raise ValueError('dynamic Kaleido XOR does not consume float-bit ingress')
    return (node,)


def kaleido_narrowing(program: TypedProgram, source_hash: str | None):
    from . import scalar_uint_xor_profile as scalar
    kaleido_xors(program, source_hash)
    found = tuple(node for function in program.functions
                  for statement in function.body
                  for node, _ in scalar._walk_statement(statement)
                  if node.kind == 'construct'
                  and node.type.display() == 'float'
                  and len(node.children) == 1
                  and node.children[0].type.display() == 'uint')
    expected = ('106:31-106:54', '111:12-111:35', '111:38-111:61',
                '169:19-169:37', '171:9-171:27', '172:9-172:27',
                '173:9-173:27')
    if tuple(scalar._span(node) for node in found) != expected:
        raise ValueError('dynamic Kaleido float(uint) census mismatch')
    return ()


def effects_ceil(program: TypedProgram, source_hash: str | None):
    from . import ceil_admission_profile as ceil
    key = 'classicNoisedeck/effects:effects'
    _required(program, source_hash, key)
    found = tuple((function, node) for function in program.functions
                  for statement in function.body
                  for node in ceil._walk_statement(statement)
                  if isinstance(node, TypedExpression)
                  and node.kind == 'builtin' and node.callee == 'ceil')
    expected = (
        ('main', '683:13-683:70',
         '4c43c375a35c43b1ed24fce47e60a197a976c8c1082e6f3865a642161753f155',
         '4bf9971ce42036c79a693f8f444e3a2099a3a477cb144e5d34b2f2a386d0f9b6'),
        ('main', '684:13-684:80',
         '81ae1fcd06cf269bc3dab48efb3fff388b5578982361ee84f3fa84ce2689c9e9',
         'c6a8ed0fcca437f4827dba78ce44206bf6d70fa02868e46a03f3b5ad0343dc8a'))
    if source_hash == kernel.CURRENT_EFFECTS_SHA256:
        expected = (
            ('main', '713:13-713:70',
             '6f234644acbcdf94f298b012cdf087c30f280492fe0f171f8272b5c006bb2ba7',
             '8fcf99dca6424723c14f130b1f61f438660d480966476e2b31988b38eda3b8f2'),
            ('main', '714:13-714:80',
             'affa7b39b0f2447da5de5b5ef718405b7ef8166d9bf71ebe2edb3375126e8098',
             '2f01f581755a9db5977fb6cfa7dc3862c35d33e3647679c17d47e29f59adb677'))
    actual = tuple((function.name, ceil._span(node), ceil._sha(node),
                    ceil._sha(node.children[0]) if len(node.children) == 1 else None)
                   for function, node in found)
    if actual != expected:
        raise ValueError('dynamic Effects ceil node closure mismatch')
    return tuple(node for _, node in found)


def effects_matrix(program: TypedProgram, source_hash: str | None):
    from . import glitch_mat4_chain_profile as matrix
    key = 'classicNoisedeck/effects:effects'
    _required(program, source_hash, key)
    located = []
    for function in program.functions:
        for index, statement in enumerate(function.body):
            located.extend((function, *record) for record in
                           matrix._walk_statement(statement, (index,)))
    records = []
    for function, node, parent, path, chain in located:
        vector = (node.kind == 'binary' and node.operator == '*'
                  and node.type.display() == 'vec4'
                  and tuple(child.type.display() for child in node.children)
                  == ('vec4', 'mat4'))
        if node.type.display() == 'mat4' or vector:
            records.append((function, node, parent, chain))
    nodes = tuple(item[1] for item in records)
    if (len(nodes) != 14 or any(function.id != 69 or function.name != 'bicubic'
                                for function, *_ in records)):
        raise ValueError('dynamic Effects matrix owner or census mismatch')
    declarations = tuple(node for node in nodes if node.kind == 'declaration')
    constructors = tuple(node for node in nodes if node.kind == 'construct')
    products = tuple(node for node in nodes if node.kind == 'binary'
                     and node.type.display() == 'mat4')
    ids = tuple(node for node in nodes if node.kind == 'id')
    vectors = tuple(node for node in nodes if node.kind == 'binary'
                    and node.type.display() == 'vec4')
    if tuple(map(len, (declarations, constructors, products, ids, vectors))) != (4,3,2,4,1):
        raise ValueError('dynamic Effects matrix topology census mismatch')
    q,s,t,a=declarations; qc,sc,tc=constructors; outer,inner=products
    t_id,q_id,s_id,a_id=ids; vector=vectors[0]
    if (q.children!=(qc,) or s.children!=(sc,) or t.children!=(tc,)
            or a.children!=(outer,) or outer.children!=(inner,s_id)
            or inner.children!=(t_id,q_id) or vector.children[1] is not a_id
            or tuple(x.symbol.name for x in (q,s,t,a,t_id,q_id,s_id,a_id))
            != ('Q','S','T','A','T','Q','S','A')):
        raise ValueError('dynamic Effects matrix symbol route mismatch')
    vector_record = next(record for record in records if record[1] is vector)
    dot = vector_record[2]; chain = vector_record[3]
    if (dot is None or dot.kind != 'builtin' or dot.callee != 'dot'
            or dot.children[0] is not vector
            or len(chain) != 1 or chain[0].kind != 'return'):
        raise ValueError('dynamic Effects matrix dot route mismatch')
    host=next(function for function in program.functions
              if function.id==69 and function.name=='bicubic')
    proof=matrix.GlitchMat4ChainProof(program,host,declarations,constructors,
        products,ids,vectors,dot,chain[0],None,None,None)
    if proof.consumed_objects != nodes:
        raise ValueError('dynamic Effects matrix candidate ownership mismatch')
    return proof
