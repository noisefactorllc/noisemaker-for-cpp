"""Exact dynamic read-side proof for the three mutable kernel-array programs."""
from __future__ import annotations
import hashlib
from tools.glslcpp.frontend import mutable_global_array_profile as array

# The complete analyzed dynamic trees are source-bound. Each row keeps the
# writer/read call order and the exact whole-array argument census independent
# of the frozen KERNEL=0/EFFECT=0 array-store proof.
ROWS = {
    'classicNoisedeck/kaleido:kaleido': (
        '2cf9e5528e3b19debec7e9761afbcf0f47452a124dd4bef74b907b2ee67f9642',
        'a8eee87d4b2b780a400425618bbc4e8e08006e91a0dcb71d2adceba6ad9d134b',
        (('DIRECTION','str','int'),('KERNEL','str','int'),('LOOP_OFFSET','str','int'),('METRIC','str','int')),
        45, 4, 'f0bc2b4256ba48e82e9012ba6c2e43cb4b73132b928b7cfcdaa0f588e56c107e',
        'convolutionKernel', 3, 10),
    'classicNoisedeck/effects:effects': (
        '1a5d9684bef39715572e85aa24419cd002e592b6192cd2dbc3b0f7d53d836a90',
        '6bb2f3c967c83ffb39823c0fc3c228f5380bbbb5284d1eed4ff70b368f9d78a1',
        (('EFFECT','str','int'),('FLIP','str','int')),
        63, 7, '9a2d52305cee708fca09e59879847d087975d96db28c5abc7a981bf8a5436fd2',
        'convolutionEffect', 20, 25),
    'classicNoisedeck/cellRefract:cellRefract': (
        'ada20a78762ccfa36b83995b7020f37e434e23da20650027ffa1784a8344430b',
        'c6af551b60bffcaadcd18ec21323b06b263382b0b0721b02747cfc75ad12b801',
        (('KERNEL','str','int'),('SHAPE','str','int')),
        45, 5, '95322e0029a70c14b9805461ffa2dd5cf06d871fb59301e173241ea61d81cad9',
        'convolutionKernel', 3, 15),
}

CURRENT_EFFECTS_ROW = (
    'ed942954001dc94c191bd617c462e63d68bd68e3e3d4545c8863b7228f64879d',
    'b7f653b09c80845559b8528519e51b347fd69441965681f0b5be74eefc8ae218',
    (('EFFECT','str','int'),('FLIP','str','int')),
    63, 7, '7b100d0cc31a4808f7374801f91bd0f83855304b25ca339790a14b40a2f31448',
    'convolutionEffect', 20, 25,
)

def authenticate(program, source_hash):
    row = ROWS.get(program.key)
    if (program.key == 'classicNoisedeck/effects:effects'
            and hashlib.sha256(program.raw_source.encode()).hexdigest()
            == CURRENT_EFFECTS_ROW[0]):
        row = CURRENT_EFFECTS_ROW
    if row is None:
        raise ValueError('dynamic array read-side program key mismatch')
    raw_sha, whole_sha, defines, store_count, ref_count, ref_sha, reader_name, writer_index, reader_index = row
    raw = program.raw_source.encode('utf-8')
    if (source_hash != raw_sha or hashlib.sha256(raw).hexdigest() != raw_sha
            or program.body_status != 'analyzed'
            or array._whole(program) != whole_sha
            or tuple((d.name,d.kind,d.canonical_value) for d in program.preprocessor_defines) != defines):
        raise ValueError('dynamic array read-side source or typed tree mismatch')
    symbols = {d.symbol.id:d.symbol.name for d in program.declarations
               if d.symbol.storage == 'global' and d.symbol.name in
               {'emboss','sharpen','blur','edge','edge2','edge3','sharpenBlur'}}
    stores, refs = array._reference_census(program, symbols)
    if (len(stores) != store_count or len(refs) != ref_count
            or array._sha(tuple(r.record for r in refs)) != ref_sha
            or {s.record.owner_name for s in stores} != {'loadKernels'}
            or {r.record.owner_name for r in refs} != {reader_name}
            or any(r.node.kind != 'id' or r.record.parent[:3] != ('call',None,'convolve')
                   for r in refs)):
        raise ValueError('dynamic array store or read census mismatch')
    mains = [f for f in program.functions if f.name == 'main']
    readers = [f for f in program.functions if f.name == reader_name]
    writers = [f for f in program.functions if f.name == 'loadKernels']
    if len(mains) != 1 or len(readers) != 1 or len(writers) != 1:
        raise ValueError('dynamic array reader/writer identity mismatch')
    main, reader, writer = mains[0], readers[0], writers[0]
    graph = array._call_graph(program)
    if ([(caller,callee) for caller,_,callee,_ in graph if callee == reader.signature.id]
            != [(main.id, reader.signature.id)]
            or [(caller,callee) for caller,_,callee,_ in graph if callee == writer.signature.id]
            != [(main.id, writer.signature.id)]):
        raise ValueError('dynamic array reader/writer call graph mismatch')
    calls = []
    for i, statement in enumerate(main.body):
        for node, _, _, _, chain in array._walk_statement(statement,(i,)):
            if node.kind == 'call' and node.signature_id in (reader.signature.id,writer.signature.id):
                calls.append((i,node.signature_id,statement,node,chain))
    if (len(calls) != 2 or (calls[0][0],calls[0][1]) != (writer_index,writer.signature.id)
            or (calls[1][0],calls[1][1]) != (reader_index,reader.signature.id)
            or writer_index >= reader_index):
        raise ValueError('dynamic array writer call does not dominate reader')
    writer_statement = calls[0][2]
    if (writer_statement.kind != 'expr' or len(writer_statement.expressions) != 1
            or writer_statement.expressions[0] is not calls[0][3]
            or len(calls[0][4]) != 1):
        raise ValueError('dynamic array writer call is conditional or nested')
    return tuple(r.node for r in refs)
