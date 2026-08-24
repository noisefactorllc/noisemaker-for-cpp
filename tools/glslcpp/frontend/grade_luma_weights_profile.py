"""Exact identity profiles for the five grade-cluster LUMA_WEIGHTS globals."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedDeclaration, TypedExpression, TypedProgram, TypedStatement


KEYS = (
    'filter/grade:creative',
    'filter/grade:hslSecondary',
    'filter/grade:primary',
    'filter/grade:vignette',
    'filter/grade:wheels',
)
PROFILES = {
    'filter/grade:creative': 'grade-creative-luma-weights-v1',
    'filter/grade:hslSecondary': 'grade-hslsecondary-luma-weights-v1',
    'filter/grade:primary': 'grade-primary-luma-weights-v1',
    'filter/grade:vignette': 'grade-vignette-luma-weights-v1',
    'filter/grade:wheels': 'grade-wheels-luma-weights-v1',
}
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof",
    "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof",
    "fixed_affine_centers13_proof",
)

__all__ = ("KEYS", "PROFILES", "authenticate_grade_luma_weights", "apply_grade_luma_weights")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _whole_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


_LOCKS = {
    'filter/grade:creative': {
        "profile": 'grade-creative-luma-weights-v1',
        "raw_bytes": 4230,
        "raw_sha256": 'b043aa43d17e098ffb736f16e6c81a5ca422ecdd6fc37fef03c39b01cc939bd3',
        "normalized_bytes": 3231,
        "normalized_sha256": '0a690075dd6e709f41978baecc5106689637648fe4fa7ccad203ccc890f5f48f',
        "whole_sha256": '8a5fb6c925dae811442b04f549109f71155db4eb45ced227ac1f7f83bef0ea41',
        "interface_sha256": 'd484112887f0a77bedd887b8e7bc5a038497d196bcac8d7924b9937372b87366',
        "functions_sha256": '383755f2cf32faa3b0e848bca74ebcdf48405911391862d4781489a35a9461ec',
        "num_declarations": 10,
        "declaration_index": 9,
        "symbol_id": 10,
        "declaration_span": '15:1-15:56',
        "declaration_sha256": '570658142d8113df455df8f84dd0c60d767e2564a0b1c78a605e5b9204dbbe14',
        "initializer_span": '15:27-15:55',
        "initializer_sha256": '0552b0c3bd0a249fe18c5d17c3d1221d6889c433e8e3fc8c3901348ec58c6750',
        "lanes": (
            ('0.2126', 0.2126, '15:32-15:38', '60bf20eee862d51bbba5fca93636e3d3005276c83d91b0e07d7fb69514a56d40'),
            ('0.7152', 0.7152, '15:40-15:46', '68a51c71d62856e03511ce138da911c566dddee60dc63731eb1d924520e0cd16'),
            ('0.0722', 0.0722, '15:48-15:54', '3f9f577bc5785b5148ed0c8cd087e6761df3e12ab079b1e384236325f6335b6c'),
        ),
        "reads": (
            (21, 'applyFadedFilm', '81:30-81:42', '07584292c8092f3becf5ad211d3abddf3a3759dcc3bb5fbd67b1fb9828231a49'),
            (22, 'applySplitTone', '102:27-102:39', '8fa9450643f5672ee129b1a94587f6f5db30dc29c5b0e815f78995bc06a515bf'),
            (23, 'applyVibrance', '47:27-47:39', '89e50adda12ac106e2f85320ea34efa26645d06b636cf026839267d4ea04416f'),
        ),
    },
    'filter/grade:hslSecondary': {
        "profile": 'grade-hslsecondary-luma-weights-v1',
        "raw_bytes": 4975,
        "raw_sha256": '2f2c54a6d977ccc0ba8657c02f1fc2fecfb576ad85f6d03ea16468fc9cbd095a',
        "normalized_bytes": 4260,
        "normalized_sha256": 'e2e2faa0484d7d8bce8d786bee19ef30ae258d9910f3691efd31d7c4f00469d5',
        "whole_sha256": 'fab6e7a4d97ceeb8dae400465b2efc034521c58fd04d1ab229606fe90c908874',
        "interface_sha256": 'ad58e18b0a04a1069ad381d78e534541a80ec5c6c70bf97b0ed00818a90a6f08',
        "functions_sha256": '5e36bba6ffb8fecee6c1f293c282f52de8a583045e4e6e469d7422be5ca77910',
        "num_declarations": 17,
        "declaration_index": 15,
        "symbol_id": 16,
        "declaration_span": '21:1-21:56',
        "declaration_sha256": 'c854652ded68a20becb5e62d6192bd8e3653681b57e2410de8caff6e5ee3ab23',
        "initializer_span": '21:27-21:55',
        "initializer_sha256": 'a21804beed7e2680203cdafddefe7ed9bfb5f40b039e3a171c1fe2e48d8e7215',
        "lanes": (
            ('0.2126', 0.2126, '21:32-21:38', 'c42b84dc28deafcb658d6a36e94534927704044b8ef182ce93b2820bc028d0eb'),
            ('0.7152', 0.7152, '21:40-21:46', 'a475ba62d53aabbaaf430155eee49257853e839e0e12990c13c25cbd776b32f2'),
            ('0.0722', 0.0722, '21:48-21:54', '984f6f1a6604abdbc839f159e43dbe96cb3906b44f863d6f1120579f06700dc6'),
        ),
        "reads": (
        ),
    },
    'filter/grade:primary': {
        "profile": 'grade-primary-luma-weights-v1',
        "raw_bytes": 5839,
        "raw_sha256": '008521bf82834ef55383a492adacb259964170831c92d6c9ddc6368acc850cc2',
        "normalized_bytes": 4149,
        "normalized_sha256": '6ce48b1dfd729e61d6f36a929a361b2597cd2989fde7bce75e488d18332af4f1',
        "whole_sha256": '8c86ac4c453be44b558d423b93b172d1f1c0b8310c1574a8c9d79ef17a67dcbc',
        "interface_sha256": '6716f9f839199c7ccaccdf6c0d94f617bf3167014a44b6400b52b6e0f2f963ed',
        "functions_sha256": '91aba72dac52ee0ba63b532e28f67c3194f483704446508d5c39d74092bc0163',
        "num_declarations": 17,
        "declaration_index": 16,
        "symbol_id": 17,
        "declaration_span": '22:1-22:56',
        "declaration_sha256": '105d7ec786df6db38cf0ad98d31250d818361d33a169cb059966af66bb13a8ac',
        "initializer_span": '22:27-22:55',
        "initializer_sha256": '4461b1da004c8387277bac6daa4ddc978cd6a2099d504876cd172cfae9671e18',
        "lanes": (
            ('0.2126', 0.2126, '22:32-22:38', '227160d62ebf98ce2744f27964ba3b76ed122a4ac3ba30aa0e6f1a49b64b25dd'),
            ('0.7152', 0.7152, '22:40-22:46', '78604562f2701a4df8b69571eda6968f4045d5f5c0b2b490fd300bfa7e2e4f9c'),
            ('0.0722', 0.0722, '22:48-22:54', 'bbdea57479e3b43fbeff8f4fb9dff9e62edf50b5fda987ba96161af988260e74'),
        ),
        "reads": (
            (41, 'applyContrast', '119:27-119:39', '4006547d150c39b4bacb66247ef96b84965fa7b1b2d2b7d0df4a880f2d593712'),
            (42, 'applyCurve', '136:27-136:39', '75fc8b53ab8847661853daf4fa3db75e94a7352ab052dbef760576f093bf8485'),
            (43, 'applySaturation', '158:27-158:39', '546e71c54667eaa3d76e97245336946a27273b8176f5bdeb8b7d5d40adc06a5c'),
            (44, 'applyTonalRanges', '92:27-92:39', '0c6a2b04eb6d18504aa9e12bc09ab4e25d80c9705ec82c80f296ffd04c5c9739'),
        ),
    },
    'filter/grade:vignette': {
        "profile": 'grade-vignette-luma-weights-v1',
        "raw_bytes": 4133,
        "raw_sha256": '740ad849a37c99d87962a376c2e618b24248dc4b2799066aaf6364861727c1fa',
        "normalized_bytes": 3158,
        "normalized_sha256": 'da1e995c43c079d01112112d7fcc82db19e0720567637351bb1fa5f777caf82b',
        "whole_sha256": 'd8265fbf3722040699e064bfc24120d8f33dc42d8699e7055d91c4f3f0dc9a77',
        "interface_sha256": '0439b9b58f6275497cc9967f8187a2c9d729d892fa660ce1d2faf170c94a4a32',
        "functions_sha256": 'cdc48970399ad47c9075348c1e103edda1caa3776b3b0afc7b0211188608dd53',
        "num_declarations": 10,
        "declaration_index": 9,
        "symbol_id": 10,
        "declaration_span": '15:1-15:56',
        "declaration_sha256": '77a43c66e6bf41c5a8976abece1b50c5612191c0c89b5ac5d32fdef8c7514098',
        "initializer_span": '15:27-15:55',
        "initializer_sha256": '29dcba44cb4c504bd9b1088d6e90a756d8907576dd839a3a64c37524bccce385',
        "lanes": (
            ('0.2126', 0.2126, '15:32-15:38', 'd57fd8743521bc743290b122971caf467a90c8d80ad6804213b866ab214cdcc8'),
            ('0.7152', 0.7152, '15:40-15:46', 'f408e468628fc0988a99b1817f4d604092d25a79fe0324ce9f398463dcb2a5ed'),
            ('0.0722', 0.0722, '15:48-15:54', '3c6cf64646f83261b05f467a688a8cc2e3e56f88d21898493c47e6a0cf590775'),
        ),
        "reads": (
            (22, 'applyVignette', '81:31-81:43', '628fc3163edeeccf08c332c8d215d0d4e952ebe56796b17aae456553e2326ef2'),
        ),
    },
    'filter/grade:wheels': {
        "profile": 'grade-wheels-luma-weights-v1',
        "raw_bytes": 3529,
        "raw_sha256": 'fa9c411096816263985e8d5ef82ade976667a6cadecf8929ecd185edbc71f479',
        "normalized_bytes": 2789,
        "normalized_sha256": 'cc34a0287290b7084fdb8d5611b7aacb6bdcfec5a229770823b5e2891cb27efc',
        "whole_sha256": '3bdd83a3c201f78d00b04bc8360bd1ea670f046f81fcadde8aa6989f0d3ed7e6',
        "interface_sha256": '52983f7002275735864a8837e14cd67c6ac2621efe2fff644643c0e34845bed9',
        "functions_sha256": '65b54adce4a12f67aa82dac71df1a2889ce23b83b4919ec0c1f3f4b1b7c8948b',
        "num_declarations": 9,
        "declaration_index": 8,
        "symbol_id": 9,
        "declaration_span": '14:1-14:56',
        "declaration_sha256": '04adf0103445aa05df16e6855f6e425da475be6ba9f7c0c1cdf8207bf5883ddd',
        "initializer_span": '14:27-14:55',
        "initializer_sha256": 'f69bedc6100c29cfe8a607427b43217bcdac3fbb1517ffb1cdb5f4b387e41f8e',
        "lanes": (
            ('0.2126', 0.2126, '14:32-14:38', '0c88beb5f4f2792f7bc1b53db0002d796bc4d72c421c67929ae2813a542da52e'),
            ('0.7152', 0.7152, '14:40-14:46', '4ad394877086a9e7fecd08dece5aafb731e2a34ae643d97ea9f343ce0b0293e0'),
            ('0.0722', 0.0722, '14:48-14:54', '8c32d054335dfddacb64fb286d600fa4f44b16f3659be077cff3ee61c6dbc129'),
        ),
        "reads": (
            (23, 'applyWheels', '73:27-73:39', '73957fc44adc029e4991bc02b500c8fe072e4bcae1f04002b4fc55ce54603547'),
            (23, 'applyWheels', '96:33-96:45', '9d8a7ed8dd94ad5a84953cc1ec1a759db6727790283b17ee429087cc9c3d808e'),
        ),
    },
}

def _fail(message: str) -> ValueError:
    return ValueError(f"grade-luma-weights-v1: {message}")


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def authenticate_grade_luma_weights(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedDeclaration:
    """Authenticate and return only the exact grade-cluster LUMA_WEIGHTS
    declaration for ``program.key``.  Each of the five keys has its own
    frozen identity: own raw/whole/interface/function hashes, own
    declaration span, own initializer literal values (all five share the
    BT.709 constant text but at five different source positions), and own
    read-site census.  This never widens to "any const vec3" -- a foreign
    key or a profile string that does not match the frozen per-key value
    is rejected outright.
    """
    lock = _LOCKS.get(program.key)
    if lock is None:
        raise _fail("selected key is not in the grade LUMA weights cluster")
    if profile != lock["profile"]:
        raise _fail("exact profile carrier required")
    if source_hash != lock["raw_sha256"]:
        raise _fail("exact caller source hash required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    if (len(raw) != lock["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != lock["raw_sha256"]
            or len(normalized) != lock["normalized_bytes"]
            or hashlib.sha256(normalized).hexdigest() != lock["normalized_sha256"]
            or program.preprocessor_defines != ()
            or program.body_status != "analyzed"
            or _sha(program.functions) != lock["functions_sha256"]
            or _whole_fingerprint(program) != lock["whole_sha256"]
            or _interface_fingerprint(program) != lock["interface_sha256"]):
        raise _fail("source, define, function, whole-program, or interface mismatch")
    if any(getattr(program, field) is not None for field in _OPTIONAL_PROOF_FIELDS):
        raise _fail("unrelated proof carrier is not absent")
    proof = program.counted_loop_proof
    if proof is None or not proof.call_graph_acyclic:
        raise _fail("loop or call graph profile mismatch")

    if len(program.declarations) != lock["num_declarations"]:
        raise _fail("declaration cardinality mismatch")
    declaration = program.declarations[lock["declaration_index"]]
    symbol = declaration.symbol
    initializer = declaration.initializer
    if (symbol.id != lock["symbol_id"] or symbol.name != "LUMA_WEIGHTS"
            or symbol.storage != "const" or symbol.writable
            or symbol.direction != "in" or symbol.type.display() != "vec3"
            or declaration.type.display() != "vec3"
            or _span(declaration) != lock["declaration_span"]
            or _sha(declaration) != lock["declaration_sha256"]
            or initializer is None or initializer.kind != "construct"
            or initializer.type.display() != "vec3"
            or initializer.constructor_type is None
            or initializer.constructor_type.display() != "vec3"
            or initializer.category != "rvalue"
            or _span(initializer) != lock["initializer_span"]
            or _sha(initializer) != lock["initializer_sha256"]
            or len(initializer.children) != 3):
        raise _fail("declaration or initializer profile mismatch")
    for lane, expected in zip(initializer.children, lock["lanes"]):
        lexeme, value, span_text, digest = expected
        if (lane.kind != "literal" or lane.type.display() != "float"
                or lane.category != "rvalue" or lane.literal != lexeme
                or lane.literal_value != value or _span(lane) != span_text
                or _sha(lane) != digest):
            raise _fail("literal lane profile mismatch")

    reads: list[tuple[int, TypedExpression]] = []
    for function in program.functions:
        for statement in function.body:
            for value in _walk_statement(statement):
                if value.kind == "id" and value.symbol_id == symbol.id:
                    reads.append((function.id, value))
    expected_reads = lock["reads"]
    if len(reads) != len(expected_reads):
        raise _fail("resolved read cardinality mismatch")
    for (function_id, value), expected in zip(reads, expected_reads):
        expected_function_id, expected_function_name, expected_span, expected_sha = expected
        function_name = next(f.name for f in program.functions if f.id == function_id)
        if (function_id != expected_function_id
                or function_name != expected_function_name
                or value.symbol is not symbol
                or value.type.display() != "vec3"
                or value.category != "readonly lvalue"
                or _span(value) != expected_span
                or _sha(value) != expected_sha):
            raise _fail("resolved read profile mismatch")
    return declaration


def apply_grade_luma_weights(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the frozen identity profile without changing the tree."""
    authenticate_grade_luma_weights(program, source_hash, profile)
    return program
