"""Exact live Kernel9 call proof for the three dynamic convolution programs."""
from __future__ import annotations

import hashlib

from .typed_ir import (FixedArrayInParameterProof, FixedArrayParameterProof,
                       TypedExpression, TypedProgram)
from . import fixed_array_in_parameter_proof as base
from . import dynamic_array_reads_profile

LOCKS = {'classicNoisedeck/cellRefract:cellRefract': {'raw': 'aa93167faa07ee22ff0be9c653b5602ac88b1b962e405548cafab43b9e867a70',
                                              'norm': '9819cf76efd248190df8fa9686bb77babdac1a34ef2a1e35cce9f7ef532f546d',
                                              'functions': '943d955bb06aa106b80162aa0f2ca45b739de232ba9859f80db3f0f87a20a86e',
                                              'interface': '82826c9e55d437e72c144c9ab4923c85678960764100e9f64172710072da74e5',
                                              'whole': 'f793d46c9317b959cd71d99f8656f31f435aa70beafbf6218585bcd77ad8947e',
                                              'defines': [['KERNEL', 'str', 'int'],
                                                          ['SHAPE', 'str', 'int']],
                                              'bindings': ['KERNEL:int',
                                                           'SHAPE:int',
                                                           'inputTex:sampler2D',
                                                           'time:float',
                                                           'seed:int',
                                                           'resolution:vec2',
                                                           'tileOffset:vec2',
                                                           'fullResolution:vec2',
                                                           'scale:float',
                                                           'cellScale:float',
                                                           'cellSmooth:float',
                                                           'variation:float',
                                                           'speed:float',
                                                           'refractAmt:float',
                                                           'direction:float',
                                                           'wrap:int',
                                                           'effectWidth:float'],
                                              'array_ids': [19,
                                                            20,
                                                            21,
                                                            22,
                                                            23,
                                                            25,
                                                            103,
                                                            109,
                                                            110,
                                                            133,
                                                            134,
                                                            154,
                                                            155,
                                                            164,
                                                            165],
                                              'census': [1,
                                                         9,
                                                         151,
                                                         142,
                                                         126,
                                                         3,
                                                         129,
                                                         8,
                                                         13],
                                              'convolve': [68,
                                                           16,
                                                           [[24, 'localUV', 'vec2', 'in'],
                                                            [25,
                                                             'kernel',
                                                             'float[9]',
                                                             'in'],
                                                            [26, 'divide', 'bool', 'in']]],
                                              'main': [73, 17],
                                              'dispatch': [67, 1],
                                              'loop': [[106, 9, 48]],
                                              'reach': ['cells',
                                                        'convolutionKernel',
                                                        'convolve',
                                                        'derivatives',
                                                        'desaturate',
                                                        'hsv2rgb',
                                                        'loadKernels',
                                                        'main',
                                                        'map',
                                                        'outline',
                                                        'pcg',
                                                        'pixellate',
                                                        'polarShape',
                                                        'posterize',
                                                        'prng',
                                                        'rgb2hsv',
                                                        'shadow',
                                                        'shapeDistance',
                                                        'smin',
                                                        'sobel'],
                                              'local_calls': [('derivatives',
                                                               109,
                                                               'deriv_x'),
                                                              ('derivatives',
                                                               110,
                                                               'deriv_y'),
                                                              ('outline', 133, 'sobel_x'),
                                                              ('outline', 134, 'sobel_y'),
                                                              ('shadow', 154, 'sobel_x'),
                                                              ('shadow', 155, 'sobel_y'),
                                                              ('sobel', 164, 'sobel_x'),
                                                              ('sobel', 165, 'sobel_y')],
                                              'global_calls': [('convolutionKernel',
                                                                21,
                                                                'blur'),
                                                               ('convolutionKernel',
                                                                23,
                                                                'edge2'),
                                                               ('convolutionKernel',
                                                                19,
                                                                'emboss'),
                                                               ('convolutionKernel',
                                                                20,
                                                                'sharpen'),
                                                               ('convolutionKernel',
                                                                23,
                                                                'edge2')]},
 'classicNoisedeck/kaleido:kaleido': {'raw': '18a201e5189430578a2cd1d03cea911957a08f3bd7f3e74e78b97eb9f946ed52',
                                      'norm': '3a3edec1e90b4645103803645313361358d1e628cd174715edf81b52ff6edd5a',
                                      'functions': 'b3352eb881128fbacdb9361df1c91a7d59297c7643fe2ea5b53034cd3f9e31ae',
                                      'interface': '2a120b047f44fe99652f5ad47bb46ea6e545a50adadeb4ff1a43e1fa42b1baab',
                                      'whole': '4cdecc27fc3c26c2da67448d49468e02dabf85f963affecab2935499026a0db5',
                                      'defines': [['DIRECTION', 'str', 'int'],
                                                  ['KERNEL', 'str', 'int'],
                                                  ['LOOP_OFFSET', 'str', 'int'],
                                                  ['METRIC', 'str', 'int']],
                                      'bindings': ['DIRECTION:int',
                                                   'KERNEL:int',
                                                   'LOOP_OFFSET:int',
                                                   'METRIC:int',
                                                   'inputTex:sampler2D',
                                                   'resolution:vec2',
                                                   'tileOffset:vec2',
                                                   'fullResolution:vec2',
                                                   'time:float',
                                                   'wrap:bool',
                                                   'seed:int',
                                                   'speed:float',
                                                   'loopScale:float',
                                                   'kaleido:float',
                                                   'effectWidth:float'],
                                      'array_ids': [17,
                                                    18,
                                                    19,
                                                    20,
                                                    21,
                                                    86,
                                                    247,
                                                    253,
                                                    254,
                                                    278,
                                                    279,
                                                    336,
                                                    337,
                                                    366,
                                                    367],
                                      'census': [1, 9, 150, 141, 126, 3, 129, 8, 12],
                                      'convolve': [123,
                                                   16,
                                                   [[85, 'uv', 'vec2', 'in'],
                                                    [86, 'kernel', 'float[9]', 'in'],
                                                    [87, 'divide', 'bool', 'in']]],
                                      'main': [131, 12],
                                      'dispatch': [122, 1],
                                      'loop': [[250, 9, 18]],
                                      'reach': ['bicubicValue',
                                                'blendBicubic',
                                                'blendLinearOrCosine',
                                                'catmullRom3',
                                                'catmullRom3x3Value',
                                                'catmullRom4',
                                                'catmullRom4x4Value',
                                                'circles',
                                                'constant',
                                                'convolutionKernel',
                                                'convolve',
                                                'derivatives',
                                                'desaturate',
                                                'diamonds',
                                                'getMetric',
                                                'hsv2rgb',
                                                'kaleidoscope',
                                                'loadKernels',
                                                'main',
                                                'map',
                                                'mod289_2',
                                                'mod289_3',
                                                'offset',
                                                'outline',
                                                'pcg',
                                                'periodicFunction',
                                                'permute3',
                                                'pixellate',
                                                'positiveModulo',
                                                'posterize',
                                                'quadratic3',
                                                'quadratic3x3Value',
                                                'randomFromLatticeWithOffset',
                                                'rgb2hsv',
                                                'rings',
                                                'shadow',
                                                'shape',
                                                'simplexValue',
                                                'sineNoise',
                                                'sobel',
                                                'value'],
                                      'local_calls': [('derivatives', 253, 'deriv_x'),
                                                      ('derivatives', 254, 'deriv_y'),
                                                      ('outline', 278, 'sobel_x'),
                                                      ('outline', 279, 'sobel_y'),
                                                      ('shadow', 336, 'sobel_x'),
                                                      ('shadow', 337, 'sobel_y'),
                                                      ('sobel', 366, 'sobel_x'),
                                                      ('sobel', 367, 'sobel_y')],
                                      'global_calls': [('convolutionKernel', 19, 'blur'),
                                                       ('convolutionKernel', 21, 'edge2'),
                                                       ('convolutionKernel', 17, 'emboss'),
                                                       ('convolutionKernel',
                                                        18,
                                                        'sharpen')]},
 'classicNoisedeck/effects:effects': {'raw': '1a5d9684bef39715572e85aa24419cd002e592b6192cd2dbc3b0f7d53d836a90',
                                      'norm': '8e2724f35c3dba9c2531ebcdc114de42332fe7d74388a3a70e12aed8347fcbd1',
                                      'functions': 'f923d9dd61809af656d1879474fde47f7199f320e1f1e739fd357c3a72563726',
                                      'interface': '48953cbfbdcc9c65d4c357c0346ee64f682d5a7f77a130fcc14923b7b44d0a77',
                                      'whole': '3e4c0399ac190cbeb0d47c8d5115d50acf20260c08d3c8483856a8877576a974',
                                      'defines': [['EFFECT', 'str', 'int'],
                                                  ['FLIP', 'str', 'int']],
                                      'bindings': ['EFFECT:int',
                                                   'FLIP:int',
                                                   'inputTex:sampler2D',
                                                   'resolution:vec2',
                                                   'tileOffset:vec2',
                                                   'fullResolution:vec2',
                                                   'invFullResolution:vec2',
                                                   'aspectInv:float',
                                                   'renderScale:float',
                                                   'time:float',
                                                   'effectAmt:float',
                                                   'scaleAmt:float',
                                                   'rotation:float',
                                                   'offsetX:float',
                                                   'offsetY:float',
                                                   'intensity:float',
                                                   'saturation:float'],
                                      'array_ids': [19,
                                                    20,
                                                    21,
                                                    22,
                                                    23,
                                                    24,
                                                    25,
                                                    46,
                                                    155,
                                                    161,
                                                    162,
                                                    190,
                                                    191,
                                                    220,
                                                    221,
                                                    228,
                                                    229,
                                                    241],
                                      'census': [1, 10, 174, 164, 144, 3, 149, 8, 15],
                                      'convolve': [74,
                                                   16,
                                                   [[45, 'uv', 'vec2', 'in'],
                                                    [46, 'kernel', 'float[9]', 'in'],
                                                    [47, 'divide', 'bool', 'in']]],
                                      'main': [80, 29],
                                      'dispatch': [73, 1],
                                      'loop': [[158, 9, 82]],
                                      'reach': ['bloom',
                                                'brightnessContrast',
                                                'cga',
                                                'convolutionEffect',
                                                'convolve',
                                                'derivatives',
                                                'desaturate',
                                                'hsv2rgb',
                                                'loadKernels',
                                                'main',
                                                'map',
                                                'offsets',
                                                'outline',
                                                'pcg',
                                                'periodicFunction',
                                                'pixellate',
                                                'posterize',
                                                'prng',
                                                'rgb2hsv',
                                                'rotate2D',
                                                'saturate',
                                                'shadow',
                                                'sobel',
                                                'subpixel',
                                                'zoomBlur'],
                                      'local_calls': [('derivatives', 161, 'deriv_x'),
                                                      ('derivatives', 162, 'deriv_y'),
                                                      ('outline', 190, 'sobel_x'),
                                                      ('outline', 191, 'sobel_y'),
                                                      ('shadow', 220, 'sobel_x'),
                                                      ('shadow', 221, 'sobel_y'),
                                                      ('sobel', 228, 'sobel_x'),
                                                      ('sobel', 229, 'sobel_y')],
                                      'global_calls': [('convolutionEffect', 21, 'blur'),
                                                       ('convolutionEffect', 23, 'edge2'),
                                                       ('convolutionEffect', 19, 'emboss'),
                                                       ('convolutionEffect', 20, 'sharpen'),
                                                       ('convolutionEffect', 23, 'edge2'),
                                                       ('convolutionEffect',
                                                        25,
                                                        'sharpenBlur'),
                                                       ('convolutionEffect', 24, 'edge3')]}}

_LOCAL_BODY_LENGTHS = {'derivatives': 25, 'sobel': 25,
                       'outline': 26, 'shadow': 29}
_LOCAL_VALUES = {
    'deriv_x': (0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0, 0.0),
    'deriv_y': (0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0),
    'sobel_x': base._SOBEL_X,
    'sobel_y': base._SOBEL_Y,
}


CURRENT_EFFECTS_SHA256 = 'b4f4279698ce60bd3c0c45f8339a4869cd6c2f0714f219ee6b2e997328057316'
CURRENT_EFFECTS_LOCK = {**LOCKS[base.EFFECTS_KEY],
    'raw': 'b4f4279698ce60bd3c0c45f8339a4869cd6c2f0714f219ee6b2e997328057316',
    'norm': '681ded19ebe739c5ec7b017f0125f59fbb7b0e63378b86555c1bb0db5cf868e8',
    'functions': '017de8e3224b22c9cddcb24fedcbdf10bd1347cd5e6caef90f08c2162e6e08a7',
    'interface': '73d2db3b08da42881fd2c52d2f15054d0a747cc465b5f64ca0f37c1192c53254',
    'whole': '149cdfbac71a70cb0016b66b299b196b79e76f0b2c977008272c8118488847e0',
}


def row_for(program: TypedProgram):
    if (program.key == base.EFFECTS_KEY
            and hashlib.sha256(program.raw_source.encode()).hexdigest()
            == CURRENT_EFFECTS_SHA256):
        return CURRENT_EFFECTS_LOCK
    return LOCKS.get(program.key)


def is_dynamic(program: TypedProgram) -> bool:
    row = row_for(program)
    return row is not None and tuple(
        (item.name, item.kind, item.canonical_value)
        for item in program.preprocessor_defines) == tuple(
            tuple(item) for item in row['defines'])


def source_provenance_error(program: TypedProgram,
                            source_hash: str | None) -> str | None:
    row = row_for(program)
    if row is None:
        return None
    if not is_dynamic(program):
        return 'dynamic Kernel9 define contract mismatch'
    if (source_hash != row['raw']
            or hashlib.sha256(program.raw_source.encode()).hexdigest() != row['raw']
            or hashlib.sha256(program.source.encode()).hexdigest() != row['norm']):
        return 'dynamic Kernel9 source provenance mismatch'
    return None


def _effects_current_tile_route(program: TypedProgram) -> bool:
    """Authenticate the current zoomBlur tile budget and sample coordinate."""
    matches = tuple(function for function in program.functions
                    if function.name == 'zoomBlur' and function.body)
    if len(matches) != 1 or matches[0].signature.id != 96 or len(matches[0].body) != 12:
        return False
    loop = matches[0].body[5]
    if (loop.kind != 'for' or len(loop.children) != 2
            or loop.children[1].kind != 'block'
            or len(loop.children[1].children) != 11):
        return False
    body = loop.children[1].children
    branch, sample_statement = body[7], body[8]
    if (branch.kind != 'if' or len(branch.expressions) != 1
            or len(branch.children) != 1
            or branch.children[0].kind != 'block'
            or len(branch.children[0].children) != 2
            or sample_statement.kind != 'decl'
            or len(sample_statement.expressions) != 1):
        return False
    condition = branch.expressions[0]
    budget_statement, clamp_statement = branch.children[0].children
    if (budget_statement.kind != 'decl' or len(budget_statement.expressions) != 1
            or clamp_statement.kind != 'expr' or len(clamp_statement.expressions) != 1):
        return False
    budget = budget_statement.expressions[0]
    clamp = clamp_statement.expressions[0]
    sample = sample_statement.expressions[0]
    if (budget.kind != 'declaration' or budget.symbol_id != 250
            or budget.symbol is None or budget.symbol.name != 'tapBudget'
            or clamp.kind != 'assign' or clamp.operator != '='
            or len(clamp.children) != 2
            or clamp.children[0].kind != 'id'
            or clamp.children[0].symbol_id != 249
            or sample.kind != 'declaration' or sample.symbol_id != 251
            or sample.symbol is None or sample.symbol.name != 'tex'):
        return False
    return (base._sha(condition)
            == '892e1660fd223697602419322324d1c391b9b1f93cc03be943269efab60733a9'
            and base._sha(budget)
            == 'ea51458c49c76af9a47f9dc9ac38b53a1bb552f41f137eb2646bea8c9419d481'
            and base._sha(clamp)
            == '606b7b4ba528cb6d2bfe15947d4573384abda3115e737cdb2ba6a999cd49b4aa'
            and base._sha(sample)
            == '57b83844586971723915d1caa6ec74158366455544fd2ea53730a29cf55cc1a2')


def prove(program: TypedProgram) -> FixedArrayInParameterProof | None:
    row = row_for(program)
    if row is None or not is_dynamic(program):
        return None
    if (source_provenance_error(program, row['raw']) is not None
            or base._sha(program.functions) != row['functions']
            or base._interface_fingerprint(program) != row['interface']
            or base._whole_program_fingerprint(program) != row['whole']
            or program.body_status != 'analyzed'
            or program.fixed_nine_table_proof is not None
            or program.fixed_grid_counter_store_proof is not None
            or program.structs or program.uniform_blocks
            or program.resources.samplers != ('inputTex',)
            or program.resources.outputs != ('fragColor',)
            or not program.resources.uses_texture
            or program.resources.uses_derivatives):
        return None
    if (row is CURRENT_EFFECTS_LOCK
            and not _effects_current_tile_route(program)):
        return None
    bindings = tuple(f'{decl.symbol.name}:{decl.type.display()}'
                     for decl in program.declarations
                     if decl.symbol.storage == 'uniform')
    if (bindings != tuple(row['bindings'])
            or program.resources.uniforms != tuple(x.split(':')[0]
                                                   for x in row['bindings'])):
        return None
    convolve_id, body_count, parameters = row['convolve']
    main_id, main_body_count = row['main']
    dispatch_id, dispatch_body_count = row['dispatch']
    dispatch_name = ('convolutionEffect' if program.key == base.EFFECTS_KEY
                     else 'convolutionKernel')
    convolve = base._definition(program, convolve_id, 'convolve', body_count)
    main = base._definition(program, main_id, 'main', main_body_count)
    dispatch = base._definition(program, dispatch_id, dispatch_name,
                                dispatch_body_count)
    if convolve is None or main is None or dispatch is None:
        return None
    if (convolve.return_type.display() != 'vec3'
            or tuple((x.id, x.name, x.type.display(), x.direction)
                     for x in convolve.parameters)
            != tuple(tuple(x) for x in parameters)):
        return None
    loop = convolve.body[13]
    induction, trip_count, charge = row['loop'][0]
    if (loop.kind != 'for' or loop.loop_proof is None
            or loop.loop_proof.induction_symbol_id != induction
            or loop.loop_proof.trip_count != trip_count
            or loop.loop_proof.entrypoint_charge != charge
            or loop.loop_proof.bound_value != 9
            or loop.loop_proof.start_value != 0
            or loop.loop_proof.comparison != '<'
            or loop.loop_proof.update != '++'
            or loop.loop_proof.lexical_product != 9
            or len(loop.children) != 2 or len(loop.expressions) != 2):
        return None
    initializer, condition, update = loop.children[0], *loop.expressions
    if (initializer.kind != 'decl' or len(initializer.expressions) != 1
            or initializer.expressions[0].kind != 'declaration'
            or initializer.expressions[0].symbol_id != induction
            or len(initializer.expressions[0].children) != 1
            or not base._literal_int(initializer.expressions[0].children[0], 0)
            or condition.kind != 'binary' or condition.operator != '<'
            or len(condition.children) != 2
            or condition.children[0].kind != 'id'
            or condition.children[0].symbol_id != induction
            or not base._literal_int(condition.children[1], 9)
            or update.kind != 'post' or update.operator != '++'
            or len(update.children) != 1
            or update.children[0].kind != 'id'
            or update.children[0].symbol_id != induction):
        return None
    offset_id = {base.CELLREFRACT_KEY: 103, base.KALEIDO_KEY: 247,
                 base.EFFECTS_KEY: 155}[program.key]
    offset = base._cellrefract_offset_table(
        convolve, owner_signature_id=convolve_id, symbol_id=offset_id,
        steps_id=offset_id - 1, induction_id=induction)
    if offset is None:
        return None
    local_tables = []
    local_calls = []
    for owner_name, symbol_id, role in row['local_calls']:
        owner = next((f for f in program.functions
                      if f.name == owner_name and f.body), None)
        if (owner is None or len(owner.body) != _LOCAL_BODY_LENGTHS[owner_name]):
            return None
        call_index = 21 if role.endswith('_x') else 22
        result = base._cellrefract_caller_table(
            program, owner, symbol_id, role, call_index,
            _LOCAL_VALUES[role], convolve_signature_id=convolve_id)
        if result is None:
            return None
        table, call = result
        local_tables.append(table)
        local_calls.append(call)
    all_calls = tuple((function.name, node)
                      for function in program.functions for statement in function.body
                      for node in base._walk_statement(statement)
                      if isinstance(node, TypedExpression) and node.kind == 'call'
                      and node.callee == 'convolve')
    observed = tuple((owner, node.children[1].symbol_id,
                      node.children[1].symbol.name,
                      node.children[1].symbol.storage)
                     for owner, node in all_calls
                     if len(node.children) == 3
                     and node.children[1].kind == 'id'
                     and node.children[1].symbol is not None)
    expected = (tuple((*item, 'global') for item in row['global_calls'])
                + tuple((*item, 'local') for item in row['local_calls']))
    if len(observed) != len(all_calls) or observed != expected:
        return None
    if any(node.signature_id != convolve_id
           or node.children[1].type.display() != 'float[9]'
           or node.children[0].type.display() != 'vec2'
           or node.children[2].type.display() != 'bool'
           for _, node in all_calls):
        return None
    try:
        global_reads = dynamic_array_reads_profile.authenticate(
            program, row['raw'])
    except ValueError:
        return None
    global_call_args = tuple(node.children[1] for owner, node in all_calls
                             if owner == dispatch_name)
    if (len(global_reads) != len(global_call_args)
            or any(read is not arg
                   for read, arg in zip(global_reads, global_call_args))):
        return None
    if (len(dispatch.body) != 1 or dispatch.body[0].kind != 'if'
            or base._cellrefract_reachable_names(program, main_id)
            != tuple(row['reach'])):
        return None
    parameter_id = parameters[1][0]
    parameter_reads = tuple(node.span for statement in convolve.body
        for node in base._walk_statement(statement)
        if isinstance(node, TypedExpression) and node.kind == 'index'
        and len(node.children) == 2 and node.children[0].kind == 'id'
        and node.children[0].symbol_id == parameter_id
        and node.children[1].kind == 'id'
        and node.children[1].symbol_id == induction)
    parameter_references = tuple(node for statement in convolve.body
        for node in base._walk_statement(statement)
        if isinstance(node, TypedExpression) and node.kind == 'id'
        and node.symbol_id == parameter_id)
    if len(parameter_reads) != 2 or len(parameter_references) != 2:
        return None
    array_ids = frozenset(row['array_ids'])
    census = base._array_census(program, array_ids, induction,
                                tuple(local_calls))
    if (tuple(len(values) for values in census) != tuple(row['census'])
            or {item.symbol_id for item in census[2]
                if item.symbol_id is not None} != array_ids
            or {item.symbol_id for item in census[3]} != array_ids):
        return None
    parameter = FixedArrayParameterProof(
        owner_signature_id=convolve_id, parameter_ordinal=1,
        symbol_id=parameter_id, symbol_name='kernel', array_type='float[9]',
        element_type='float', extent=9, direction='in',
        native_abi='const Kernel9&', induction_read_spans=parameter_reads,
        reads_per_iteration=2,
        direct_call_spans=tuple(node.span for _, node in all_calls),
        direct_argument_spans=tuple(node.children[1].span for _, node in all_calls))
    return FixedArrayInParameterProof(
        proof_kind=base.CAPABILITY, source_profile='dynamic-kernel9-live-v1',
        raw_source_sha256=row['raw'], normalized_source_sha256=row['norm'],
        canonical_factory_sha256=base.PROFILES[program.key].canonical_factory_sha256,
        define_contract=program.preprocessor_defines,
        binding_signature=bindings, compatibility_sites=(),
        kernel_alias='Kernel9', offsets_alias='Offsets9',
        caller_tables=tuple(local_tables), parameter=parameter,
        offset_table=offset, convolve_loop_span=loop.span,
        induction_symbol_id=induction, loop_trip_count=9,
        lexical_product=9, entrypoint_charge=charge,
        main_signature_id=main_id, mode_one_span=dispatch.body[0].span,
        main_derivative_call_spans=(),
        array_parameter_count=len(census[0]),
        array_declaration_count=len(census[1]),
        array_typed_expression_count=len(census[2]),
        array_identifier_reference_count=len(census[3]),
        literal_store_count=len(census[4]),
        induction_read_count=len(census[5]),
        index_expression_count=len(census[6]),
        whole_array_argument_count=len(census[7]),
        array_call_count=len(census[8]),
        no_alias_copy_escape_return_or_post_call_use=True,
        complete_initialization_dominates_reads=True,
        caller_tables_never_simultaneously_live=False,
        parameter_read_only_and_synchronous=True,
        mode_zero_array_free=False,
        raw_simultaneous_payload_bytes=(144 + (252 if program.key == base.EFFECTS_KEY
                                           else 180)),
        interface_sha256=row['interface'], typed_ir_sha256=row['functions'],
        whole_program_sha256=row['whole'])

KALEIDO_OFFSET_ARMS = (10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110,
                       120, 200, 210, 300, 310, 320, 330, 340, 350,
                       360, 370, 380, 400, 410)
KALEIDO_OFFSET_FUNCTION_SHA256 = (
    '8b3b9477bbab087abbec16533c992cc52a7d3b3c29628d21199ba33082f8cfe3')


def authenticate_kaleido_offset_terminal(program: TypedProgram,
                                         source_hash: str | None):
    """Prove the exact live LOOP_OFFSET chain can fall through without a return."""
    if (program.key != base.KALEIDO_KEY
            or source_provenance_error(program, source_hash) is not None
            or prove(program) is None):
        raise ValueError('dynamic Kaleido source/tree proof mismatch')
    candidates = tuple(function for function in program.functions
                       if function.name == 'offset' and function.body)
    if (len(candidates) != 1 or candidates[0].id != 135
            or candidates[0].signature.id != 135
            or candidates[0].return_type.display() != 'float'
            or len(candidates[0].body) != 1
            or base._sha(candidates[0]) != KALEIDO_OFFSET_FUNCTION_SHA256):
        raise ValueError('dynamic Kaleido offset function identity mismatch')
    function = candidates[0]
    branch = function.body[0]
    for ordinal, value in enumerate(KALEIDO_OFFSET_ARMS):
        if (branch.kind != 'if' or len(branch.expressions) != 1
                or len(branch.children) != (1 if ordinal == 24 else 2)):
            raise ValueError('dynamic Kaleido offset branch shape mismatch')
        condition = branch.expressions[0]
        if (condition.kind != 'binary' or condition.operator != '=='
                or len(condition.children) != 2
                or condition.children[0].kind != 'id'
                or condition.children[0].symbol_id != 3
                or condition.children[0].symbol.name != 'LOOP_OFFSET'
                or condition.children[1].kind != 'literal'
                or condition.children[1].literal_value != value):
            raise ValueError('dynamic Kaleido offset branch value mismatch')
        taken = branch.children[0]
        if (taken.kind != 'block' or len(taken.children) != 1
                or taken.children[0].kind != 'return'
                or len(taken.children[0].expressions) != 1):
            raise ValueError('dynamic Kaleido offset return mismatch')
        if ordinal < 24:
            branch = branch.children[1]
    return function


EFFECTS_SUBPIXEL_FUNCTION_SHA256 = (
    'fe6384b19151d8405849654f8f14814af24d3f1210154bafbc277905580b40d6')


def authenticate_effects_subpixel_value_copy(program: TypedProgram,
                                             source_hash: str | None
                                             ) -> TypedExpression:
    """Prove CPU9f3 copies subpixel's orig vector before color is changed."""
    if (program.key != base.EFFECTS_KEY
            or source_provenance_error(program, source_hash) is not None
            or prove(program) is None):
        raise ValueError('dynamic Effects source/tree proof mismatch')
    candidates = tuple(function for function in program.functions
                       if function.name == 'subpixel' and function.body)
    if (len(candidates) != 1 or candidates[0].signature.id != 95
            or base._sha(candidates[0]) != (
                '8bcd1625b7deadd4e73cf6753240d08a9e8ec117fb276977edb11ed3cd583f1d' if source_hash == CURRENT_EFFECTS_SHA256
                else EFFECTS_SUBPIXEL_FUNCTION_SHA256)):
        raise ValueError('dynamic Effects subpixel function identity mismatch')
    declarations = tuple(expression for statement in candidates[0].body
                         for expression in statement.expressions
                         if expression.kind == 'declaration'
                         and expression.symbol is not None
                         and expression.symbol.name == 'color')
    if (len(declarations) != 1
            or declarations[0].symbol_id != 234
            or declarations[0].type.display() != 'vec3'
            or len(declarations[0].children) != 1
            or declarations[0].children[0].kind != 'id'
            or declarations[0].children[0].symbol_id != 233
            or declarations[0].children[0].symbol.name != 'orig'):
        raise ValueError('dynamic Effects subpixel copy site mismatch')
    return declarations[0]
