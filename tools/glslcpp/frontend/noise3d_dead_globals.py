"""Authenticate the unused rhash closure in the current Noise3D source."""

from collections import Counter
from dataclasses import dataclass
import hashlib


KEY = "classicNoisedeck/noise3d:noise3d"
SOURCE_SHA256 = "f359a11d4a3799686a554ee4dbaca725235ef38781a7b91e37628537cebb220f"
NORMALIZED_SHA256 = "e5969f15ec8adf7fb0d10093633f45becae08302cf93ba92b422eabad5678e5b"
WHOLE_SHA256 = "9c48917690fe910e322301fbc4c2243319eab7a1bde48f2de141ea696f3494a3"
RUNTIME_WHOLE_SHA256 = "8348352a69c8ac6915dd925412e7f04c7cb70c57274b68e7b8b7b77ab97f7a3a"
RUNTIME_NORMALIZED_SHA256 = "3bd62af87372489e66e6755ed994fd23036726f6080b23f58bfa13e0fb2cb9c0"
DEAD_NAMES = frozenset({
    "cellular", "cubes", "mod7", "pcg", "prng", "random", "rgb2hsv",
    "rhash", "rotate2D", "sine3D", "smax", "smin", "spheres", "voronoi3d",
})
RUNTIME_DEAD_NAMES = frozenset({
    "random", "rgb2hsv", "rhash", "rotate2D", "smax", "smin",
})
RUNTIME_ROUNDS = (
    ("cubes", 445, 17, "dad0dd319be1f44e8c9456a1a46430b35dd166cf5a07e9c12346cb3d0c52df16",
     "cc105f31eeb95a7a498d845f71dc2651a0e612c545c688dc7a4383fe0fb26504"),
    ("spheres", 433, 13, "ad8d457a3630bacef74a00a117e0ab2481d7af7b8350e8cc36670f3e49380b56",
     "21f0736f431599d1b7a60babedfac2fb8e2ac8529c8f7d77e86414cf5f1dda06"),
)
RUNTIME_CELLULAR_DISTANCES = (
    ("d11", 243, "daf3810c69dcf908575bb37df0837ef5ae0b369bbdbe16643212e21bee75c5a7"),
    ("d12", 244, "0518095008c36cec0ad1f9cc37d95d494c9e0728aa76a3613dd79dc33ab14d2b"),
    ("d13", 245, "96968637e5e6bc896081f45eb5adc3e1a859a06c40e53a0d0625edd200bfe3d7"),
    ("d21", 246, "af5284b7349e806ed7a64eae6edbfea7895934c252a3bb3f73d0a85511e67970"),
    ("d22", 247, "84e54db3cfecdf25427f597658c39da777bdcb408ada0c5ad6083e02ea256f60"),
    ("d23", 248, "a92ce591948be39cc7bc20c4e9350b86bde2a04940821624297e96c0ec65dfd8"),
    ("d31", 249, "2d5de278f63918103342a86a58575e6e8f98bbd74487683fca6ea90037a8a1d2"),
    ("d32", 250, "e091c867acc0766208bdee09f989140a12ae53eb2ff2b15b865271adca9e6734"),
    ("d33", 251, "8d909b67459ce598edf435c747fe37d27af13e499e07c3939e18410f65b1316a"),
)
RUNTIME_CELLULAR_OY = (
    ("oy11", 172, "5f866849cd222ef9121bed916124c620c2a765da20e37ae3825ac38de3c492f4"),
    ("oy12", 176, "dde600272fdc56b55e1f833f17180d1ce7f615e0da9455cb81e7ea64d9ab3158"),
    ("oy13", 180, "2348945db3e97e13b8a7d694aa35e3962b13f770cc66f8518b2dd16fb9ba8d6d"),
    ("oy21", 184, "61bec15d51ab052dd2ba9327557b00a5876d8087844ed95f8ec6de15fb3fcf7b"),
    ("oy22", 188, "32bfe239a8d1755bbea2708c54f024ec2067790be5bdebda17be134db7cf1909"),
    ("oy23", 192, "e541ba452559495d30de5d84db97f271691a327d28cd35f92085136b3caadf34"),
    ("oy31", 196, "48bedfe7434fefa9b1f850cbd3908d49bf8a0d3341c02213fbc2de70b5519d0c"),
    ("oy32", 200, "d20233bff81b3b1518b591ad8779d53ddba851a0ae34d62d572a6d135d6c8b01"),
    ("oy33", 204, "aef4c430cf0df65b0cf115e08a10ae95c7618c58ffeb75f5d972b3a1579707d2"),
)


@dataclass(frozen=True, slots=True)
class Noise3DDeadGlobalsProof:
    globals: tuple
    dead_functions: tuple
    rounds: tuple = ()
    max_effective_depth: int = 3
    max_entrypoint_charge: int = 2048
    value_copies: tuple = ()
    cellular_distances: tuple = ()
    cellular_oy: tuple = ()


def _expressions(value):
    yield value
    for child in value.children:
        yield from _expressions(child)


def _statements(statement):
    for expression in statement.expressions:
        yield from _expressions(expression)
    for child in statement.children:
        yield from _statements(child)


def _whole(program):
    payload = (
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    )
    return hashlib.sha256(repr(payload).encode()).hexdigest()


def authenticate_noise3d_dead_globals(program, source_hash):
    if program.key != KEY:
        return None
    runtime = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines) == (("NOISE_TYPE", "str", "int"),)
    if (source_hash != SOURCE_SHA256
            or hashlib.sha256(program.raw_source.encode()).hexdigest() != SOURCE_SHA256
            or hashlib.sha256(program.source.encode()).hexdigest()
            != (RUNTIME_NORMALIZED_SHA256 if runtime else NORMALIZED_SHA256)):
        raise ValueError("Noise3D source identity mismatch")
    if _whole(program) != (RUNTIME_WHOLE_SHA256 if runtime else WHOLE_SHA256):
        raise ValueError("Noise3D typed program identity mismatch")
    globals_ = tuple(item for item in program.declarations
                     if item.symbol.storage == "const")
    if (tuple((item.symbol.name, item.type.display(), item.symbol.writable)
              for item in globals_)
            != (("myt", "mat2", False), ("mys", "vec2", False))
            or any(item.initializer is None or item.initializer.kind != "construct"
                   or item.initializer.type.display() != item.type.display()
                   for item in globals_)):
        raise ValueError("Noise3D dead global declaration mismatch")
    functions = tuple(item for item in program.functions if item.name == "rhash")
    if (len(functions) != 1 or functions[0].return_type.display() != "vec2"
            or tuple(item.type.display() for item in functions[0].parameters) != ("vec2",)):
        raise ValueError("Noise3D rhash signature mismatch")
    rhash = functions[0]
    ids = {item.symbol.id: item.symbol.name for item in globals_}
    references = Counter()
    names = {function.name for function in program.functions}
    edges = {}
    for function in program.functions:
        nodes = tuple(node for statement in function.body for node in _statements(statement))
        edges.setdefault(function.name, set()).update(
            node.callee for node in nodes
            if node.kind == "call" and node.callee in names)
        used = Counter(ids[node.symbol_id] for node in nodes
                       if node.kind == "id" and node.symbol_id in ids)
        if function is rhash:
            references.update(used)
        elif used:
            raise ValueError("Noise3D dead global is referenced outside rhash")
    if references != Counter({"myt": 1, "mys": 2}):
        raise ValueError("Noise3D rhash global reads mismatch")
    reachable = {"main"}
    while True:
        expanded = reachable | set().union(*(edges[name] for name in reachable))
        if expanded == reachable:
            break
        reachable = expanded
    dead_names = RUNTIME_DEAD_NAMES if runtime else DEAD_NAMES
    if names - reachable != dead_names or edges["rhash"]:
        raise ValueError("Noise3D dead function graph mismatch")
    dead_functions = tuple(function for function in program.functions
                           if function.name in dead_names)
    rounds = ()
    value_copies = ()
    cellular_distances = ()
    cellular_oy = ()
    if runtime:
        rounds = tuple((function.name, value) for function in program.functions
                       for statement in function.body for value in _statements(statement)
                       if value.kind == "builtin" and value.callee == "round")
        if len(rounds) != len(RUNTIME_ROUNDS):
            raise ValueError("Noise3D runtime round census mismatch")
        for (function_name, value), (expected_name, line, column, digest, argument_digest) in zip(
                rounds, RUNTIME_ROUNDS):
            if (function_name != expected_name or value.span.start_line != line
                    or value.span.start_column != column or value.signature_id != -38
                    or value.type.display() != "vec3" or len(value.children) != 1
                    or value.children[0].type.display() != "vec3"
                    or hashlib.sha256(repr(value).encode()).hexdigest() != digest
                    or hashlib.sha256(repr(value.children[0]).encode()).hexdigest()
                    != argument_digest):
                raise ValueError("Noise3D runtime round identity mismatch")
        summary = program.counted_loop_proof
        if (summary.loop_count != 4 or summary.unproved_loop_count != 0
                or summary.max_effective_depth != 4
                or summary.max_lexical_product != 100
                or summary.entrypoint_charge != 4156
                or not summary.call_graph_acyclic):
            raise ValueError("Noise3D runtime loop proof mismatch")
        spheres = next((function for function in program.functions
                        if function.name == "spheres"), None)
        value_copies = tuple(
            expression for statement in (spheres.body if spheres is not None else ())
            for expression in statement.expressions
            if expression.kind == "declaration" and expression.symbol.name == "q")
        if (len(value_copies) != 1
                or value_copies[0].span.start_line != 432
                or value_copies[0].type.display() != "vec3"
                or len(value_copies[0].children) != 1
                or value_copies[0].children[0].kind != "id"
                or value_copies[0].children[0].symbol.name != "p"
                or hashlib.sha256(repr(value_copies[0]).encode()).hexdigest()
                != "7248973a166527c4b46c6ad65da5af2bf9af5f395421f2769e2c5778d9aded85"):
            raise ValueError("Noise3D spheres value-copy identity mismatch")
        cellular = next((function for function in program.functions
                         if function.name == "cellular"), None)
        cellular_distances = tuple(
            expression for statement in (cellular.body if cellular is not None else ())
            for expression in statement.expressions
            if expression.kind == "declaration"
            and expression.symbol.name in {name for name, _, _ in RUNTIME_CELLULAR_DISTANCES})
        if len(cellular_distances) != len(RUNTIME_CELLULAR_DISTANCES):
            raise ValueError("Noise3D cellular distance census mismatch")
        for expression, (name, line, digest) in zip(
                cellular_distances, RUNTIME_CELLULAR_DISTANCES):
            if (expression.symbol.name != name
                    or expression.span.start_line != line
                    or expression.type.display() != "vec3"
                    or hashlib.sha256(repr(expression).encode()).hexdigest() != digest):
                raise ValueError("Noise3D cellular distance identity mismatch")
        cellular_oy = tuple(
            expression for statement in cellular.body
            for expression in statement.expressions
            if expression.kind == "declaration"
            and expression.symbol.name in {name for name, _, _ in RUNTIME_CELLULAR_OY})
        if len(cellular_oy) != len(RUNTIME_CELLULAR_OY):
            raise ValueError("Noise3D cellular oy census mismatch")
        for expression, (name, line, digest) in zip(cellular_oy, RUNTIME_CELLULAR_OY):
            if (expression.symbol.name != name
                    or expression.span.start_line != line
                    or expression.type.display() != "vec3"
                    or hashlib.sha256(repr(expression).encode()).hexdigest() != digest):
                raise ValueError("Noise3D cellular oy identity mismatch")
    return Noise3DDeadGlobalsProof(
        globals_, dead_functions, tuple(value for _, value in rounds),
        4 if runtime else 3, 4156 if runtime else 2048, value_copies,
        cellular_distances, cellular_oy)
