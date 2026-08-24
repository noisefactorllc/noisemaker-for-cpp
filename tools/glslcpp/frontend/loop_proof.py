"""Immutable proof construction for the deliberately narrow counted-for subset."""

from __future__ import annotations

from collections import deque
from dataclasses import replace
import hashlib
import math
import re

from .typed_ir import (CountedLoopProgramProof, CountedLoopProof, TypedExpression,
                       TypedFunction, TypedProgram, TypedStatement)


_MAX_CHARGE = (1 << 63) - 1
SOURCE_GLOBAL_LITERAL_INT_CAPABILITY = "source-global-literal-int-v1"

# Counted-for-v1 safety-charge caps, shared by the validator
# (generate_typed_slice.py) and the emitter (emit_typed_cpp.py) so the two
# independent checks can never drift apart. Raised once, deliberately, from
# the original 128/4096/4096 to admit filter/reindex:nmReindexReduce's tile
# reduction (landed alongside this widening): MAX_TILE_DIM=512 is the exact
# per-loop trip count of both its nested loops; 512*512=262144 is the exact
# nested lexical product (ceil(width/8)*ceil(height/8) for statsTex axes up
# to the source's own 4096px design limit, capped by MAX_TILE_DIM -- the
# identical hard cap already baked into the shipped JS transpiled from the
# same GLSL source, so no larger trip count is ever reachable without also
# diverging from the JS reference); 262656 is that same loop's exact
# whole-program entrypoint charge (the product plus the per-iteration
# min/max/texelFetch body work). These are the exact values this one
# program needs, not a round number picked for headroom -- a future program
# needing a larger loop still requires its own deliberate, argued cap change
# plus a new near-miss rejection at the new boundary (see
# test_counted_for_v1_rejects_header_and_control_near_misses's "trip-513"
# and test_counted_for_v1_rejects_effective_depth_product_charge_and_call_
# cycles's "nested-product-over-reindex-reduce"/"entry-charge-over-reindex-
# reduce" in tests/test_typed_generator.py).
COUNTED_FOR_V1_MAX_TRIP_COUNT = 512
COUNTED_FOR_V1_MAX_LEXICAL_PRODUCT = 262144
COUNTED_FOR_V1_MAX_ENTRYPOINT_CHARGE = 262656


_SOURCE_GLOBAL_LITERAL_INT_PROFILES = {
    "filter/bloom:ntapGather": {
        "raw": "f11c983976cb8450d611e8d888bd151a4c2cfdda8d9d772f906608dedb99d237",
        "source": "1d20c3bccadf30a1f6c3c6f8903ed805287933fcc1257d3ae6d4b98c5d0b9f81",
        "defines": (), "integer": ("MAX_TAPS", 8, "64", 64),
        "globals": (("MAX_TAPS", 8, "int", "64"),
                    ("GOLDEN_ANGLE", 9, "float", "2.39996323"),
                    ("PI", 10, "float", "3.14159265359")),
        "reads": (("main", 11, 30, 35, 30, 43), ("main", 11, 37, 25, 37, 33)),
        "pre_functions": "a000425b8ae57882a6877bf2c390f3d1fb3ce226d0181f0fa76d8851d7a79163",
        "post_functions": "66138a890082a6185afea09a5f9a169114193bf0134b6153737a663b27a86270",
        "pre_whole": "915a83f7673ec52fd79e8ed7a0a02094f720fbaa575db63318227f14c3aa2f51",
        "post_whole": "ff1fa1ba17abb3bdcd8daf7059b517609db49cfc62c10836b86ea86a1d4c696c",
        "interface": "b1bbe45469447847e91fbb66b6ee1b0cfc5a5a07cdac53cb322a728e295b8fb8",
    },
    "filter/directionalBlur:directionalBlur": {
        "raw": "1e4a9d6371683b75a1dbefa968e1536e0017e921fe02f80e600e8f1482e8691c",
        "source": "587b19df3989bf8bb649a86265f4210561077ccadcec30f0a92077510bcbf668",
        "defines": (), "integer": ("N", 6, "32", 32),
        "globals": (("N", 6, "int", "32"),),
        "reads": (("main", 9, 22, 42, 22, 43), ("main", 9, 26, 25, 26, 26),
                  ("main", 9, 27, 37, 27, 38), ("main", 9, 31, 29, 31, 30)),
        "pre_functions": "8c0e81f16787bce2ab63a414b9774702ce3ceac9be71f7bad46c9bccde14ddfa",
        "post_functions": "6e57feabe450d500b7ac2ddf328e855d72e0eb2c764c89b94c6c6f9afa184f96",
        "pre_whole": "30011a8fd6f15943857b5d978a5383cbf0408becbfcdd2a8e9fd08eddab11153",
        "post_whole": "21e4cc0784b7bbffa453e549776e3ed332df1219bf77d1c42bf32d650f8c1f7b",
        "interface": "3934c143ad58175d44458d78b2641badf31363c0f8438b1b5f656cbf6e269858",
    },
    "filter/spinBlur:spinBlur": {
        "raw": "a5ee242e189066b55d4d5c3140e957418bdff582b367d1f6d4cdfee4c333b405",
        "source": "b829271f6c58fccde0e5723cd2bc7d7d3f47acfeb4cf1ce157bc996fb04ff1ee",
        "defines": (), "integer": ("N", 9, "32", 32),
        "globals": (("N", 9, "int", "32"),),
        "reads": (("main", 16, 45, 37, 45, 38), ("main", 16, 54, 25, 54, 26),
                  ("main", 16, 55, 41, 55, 42), ("main", 16, 60, 29, 60, 30)),
        "pre_functions": "f9563d0e1e160ac48d4f6b0becdcb4ced10342039f0ef8c0a09f822e0c8cc8e8",
        "post_functions": "974b46a9db569acad639c8fd500c839f48f15b9bd42baac27374e204ca1d9e51",
        "pre_whole": "5d3e1a5f3907bc1678620013f2a5e6854c386d12af60a1e92bc196c06ee7e6bc",
        "post_whole": "af920749f40d2f9eafcfa3bf9d1ffccf3164571475e1b9162053cba5b3e43bff",
        "interface": "4b4d07b3a0cd718e48c976ef202de9dff5e7c35d422c371f6243ff0fbf9fa723",
    },
    "filter/strokes:stkSmear": {
        "raw": "dac057232a650f3c9eb56829aa12507b639d8632f6fc132cbd067a28996fa4db",
        "source": "796bad6231e640aec7c6f471465f57112f77394d921bff9902833955e1e20f15",
        "defines": (("MODE", "int", "0"),), "integer": ("MAX_TAPS", 8, "24", 24),
        "globals": (("MAX_TAPS", 8, "int", "24"),),
        "reads": (("smear", 39, 156, 26, 156, 34),),
        "pre_functions": "5e5e0bb5091f6d4221e5396f3ed5dc73854543281ef519fbaddb0fdcd5c3fbc9",
        "post_functions": "0ee608091d09aece9a1eba08224b1980be15e2c1eb288b206fe47f95c2cfb344",
        "pre_whole": "b7b6c65e3275843bd141f9b0c1fcf40daad671dcbeebef2db6a4684ec750790c",
        "post_whole": "5ac93407e6a52ef895a887b3817c781d58ac9b974afe30415f31c6b4a9e8cbbf",
        "interface": "8fe812a5bdfa275782969cb6146b0e8005e8dc521af9e5b10926bc49d2b89fef",
    },
    "filter/vaseline:upsample": {
        "raw": "39055a214903d09a9b2dd8db9ec5b2023a920c22707ec424ae90d5fb90ebf461",
        "source": "1785f58af7b191e5a4f1a55223476d12372c97f87c062d34ecefe07550b05c93",
        "defines": (), "integer": ("TAP_COUNT", 8, "32", 32),
        "globals": (("TAP_COUNT", 8, "int", "32"),
                    ("RADIUS", 9, "float", "48.0"),
                    ("GOLDEN_ANGLE", 10, "float", "2.39996323"),
                    ("BRIGHTNESS_ADJUST", 11, "float", "0.15")),
        "reads": (("main", 16, 49, 25, 49, 34), ("main", 16, 50, 36, 50, 45)),
        "pre_functions": "9f2f11099585a38441157f4e4bb847808c4fd81df1c69cc79d1b651b0fe90374",
        "post_functions": "2e86ae95c587a74560e8cdd1d72bdf3f1d5cc9a14183ed136dc1950a590b2389",
        "pre_whole": "5771c7b74d9e30e47f0b84438bc40e16d4c0da36346325862bef6516c5f0d60d",
        "post_whole": "831676d46152cd861a4f658fb6bfe75c06c3a8275d2b9acaae00ae8038cc39a6",
        "interface": "fc9fd33b3e14a9808c66c17f3b358d79be3b97c11c6fd6ea281ce51118e0de9e",
    },
    "filter/wind:wind": {
        "raw": "68eb0f4deca51ab5352307fa06509b153cf19a29cea4820d054adafa42655f22",
        "source": "665e842850e766cbf988212669457fb9fd76dff59e52a2f7b2cedd242e490fa4",
        "defines": (("METHOD", "int", "1"),), "integer": ("MAX_STEPS", 8, "128", 128),
        "globals": (("MAX_STEPS", 8, "int", "128"),
                    ("STEP_PX", 9, "float", "1.0"),
                    ("MAX_REACH", 10, "float", "128.0")),
        "reads": (("main", 13, 46, 26, 46, 35),),
        "pre_functions": "214d03b9c58da73392e8b05200035b6e81244dbec06705302a237da23081ef6d",
        "post_functions": "70e4d4612ed144e0beb110e8fbbaf5d02b60e27e23fbf6961a30ac8d43bbb8e4",
        "pre_whole": "b08edc234c42aa039867a7c549eff408e7c3c51cfa28d0951a437a00043a2dc0",
        "post_whole": "6a5cb2724a9dfa61aaf5f7879a65fe9ec3cd353b7e815f20eb0915e4a103f9e0",
        "interface": "455e2e5350b3a027556adc181e5ce3099ca395f801add229956b750d31acdf85",
    },
    # Task 34/35 -- clean fingerprint-only reuse, no budget change. Verified
    # per-program against the loop-proof study (loopproof-oracles.json):
    # each const is a bare int literal (initializer.kind == "literal"), each
    # trip/product/charge is well inside the 128/4096/4096 caps.
    # Fingerprint-only reuse of source-global-literal-int-v1: a bare int
    # literal const with trip/product/charge well inside the 128/4096/4096
    # caps. Raw SHA-256 verified against the pinned corpus before landing.
    #
    # LightLeak phase-1 landing -- this is the exact
    # `counted_for_seed_contract()._asdict()` entry from
    # out_inout_admission_profile. It closes the source-global bound rung;
    # the next independent gate remains the out-parameter direction at
    # 60:50. The typed row is intentionally a separate integration slice.
    "filter/lightLeak:lightLeak": {
        "raw": "61bcb2989992c109dcf73ac5b34bb4dfa7f6603b54c111a84e69b6f73a9501bb",
        "source": "4568d0dd53883cfc1cb1ba8237a894e9c5740c4f1a045dff377221722f3eef72",
        "defines": (), "integer": ("POINT_COUNT", 2, "6", 6),
        "globals": (("TAU", 1, "float", "6.28318530717958647692"),
                    ("POINT_COUNT", 2, "int", "6")),
        "reads": (("voronoiCell", 29, 65, 25, 65, 36),),
        "pre_functions": "f7274c863e2c65b6aa80160bb4d42ea06cd26a3a68e8508e4fc13bc1350fb9a3",
        "post_functions": "72db52007f289ea5cff3ef10cc2b5245a7bac958f1067729fdfd75d82515bf0d",
        "pre_whole": "9fc72ea8a4105bdfd38e58240bd0a1e4ae448c1f6ff954a31fd7967edfd991ae",
        "post_whole": "8f78928336444c53847458cb908ae2c3eeda6ae93c0ab0090fbf87207846397a",
        "interface": "e8032324cde699ade81d0920220709d5087d576f3dbaee828da74f6152719ec0",
    },
    "filter/reindex:nmReindexStats": {
        "raw": "06525e054fc4910e7bc53345ad656071d2fcb33fc897f4aa35e8fc59b6f0b951",
        "source": "f78e6cb9d0b37d6cc7eb14ee7d3e27ebcd10d4620e2097d1c8fb3a0af97299c2",
        "defines": (), "integer": ("TILE_SIZE", 3, "8", 8),
        "globals": (("F32_MAX", 1, "float", "3.402823466e38"),
                    ("F32_MIN", 2, "float", None),
                    ("TILE_SIZE", 3, "int", "8")),
        "reads": (("main", 13, 57, 32, 57, 41), ("main", 13, 58, 32, 58, 41),
                  ("main", 13, 72, 27, 72, 36), ("main", 13, 75, 31, 75, 40)),
        "pre_functions": "3ee365cc270cdb512ce58607e893d588b8f80fbfe8a5670e70eca5d55dc651c2",
        "post_functions": "ff12685deabe6f8e16ba8cb6bbddcf7f96e37127038e68c00fcb079f8a7bb72a",
        "pre_whole": "5bcf97ac36739a5af7a73d9ea226e55fc01183ad60c52a6fdb58619a4a25a16b",
        "post_whole": "70241166858cc27123c6a27f35b130d83d6e8f79aa3fb49e2de0aadb7077baad",
        "interface": "08976a0c50e3d17702966ae80fec5035ee021bc5b95ee3f55dcb90a6e77a4b40",
    },
    # Task 36 -- deliberate cap widening, not a fingerprint-only reuse like
    # the entries above. MAX_TILE_DIM=512 admits a global const bound whose
    # nested product (512*512=262144) and whole-program charge (262656)
    # exceed the original 4096/4096/128 caps; see the
    # COUNTED_FOR_V1_MAX_*_PRODUCT/CHARGE/TRIP_COUNT constants above for the
    # exact justification. The source's own MAX_TILE_DIM guard (identical to
    # the cap already baked into the shipped JS transpiled from this same
    # GLSL) makes 512 the true worst case, not an underestimate -- no
    # texture-size preflight is required for bit-exact parity.
    "filter/reindex:nmReindexReduce": {
        "raw": "5e9701125522aaa1f838858a7892ac1312f1161608a5f94b494ae64c7db8b7ff",
        "source": "7523752eeccea1c2a5241cd2d8a5467e78cf7365abe2d91b7a9615a2644a7631",
        "defines": (),
        # Plural schema (see authenticate_source_global_literal_int): the
        # loop-bound global (MAX_TILE_DIM) AND a second global used only in
        # ordinary arithmetic (TILE_SIZE, the tile pitch multiplier) both
        # need admission -- the first six profiles above only ever needed one.
        "integers": (("TILE_SIZE", 3, "8", 8), ("MAX_TILE_DIM", 4, "512", 512)),
        "globals": (("F32_MAX", 1, "float", "3.402823466e38"),
                    ("F32_MIN", 2, "float", None),
                    ("TILE_SIZE", 3, "int", "8"),
                    ("MAX_TILE_DIM", 4, "int", "512")),
        "reads": ((("main", 7, 25, 27, 25, 36), ("main", 7, 25, 44, 25, 53),
                   ("main", 7, 26, 27, 26, 36), ("main", 7, 26, 44, 26, 53),
                   ("main", 7, 36, 44, 36, 53), ("main", 7, 36, 60, 36, 69)),
                  (("main", 7, 32, 27, 32, 39), ("main", 7, 34, 31, 34, 43))),
        "pre_functions": "a5e80eaa2a20255b6abf509eee6325e0dd20f25d04aa8b6a4eaa842a6351a217",
        "post_functions": "cca3dfdd81357d652390b9d531732dd6ddee78b4be5d34ff9057f09b8d66c49e",
        "pre_whole": "6d5b0432cd66776eb9af6a7dc450df2b74d42d54c4bff818e1ffa6eeac389c38",
        "post_whole": "e20198172c0cb696a55f259485231dccd2d01dcd292a0df419da68dac8c4d929",
        "interface": "39c05c717b26d3c99ab069bd35d458523d7dcd8f0bc11909ba831d783616609e",
    },
    # Row 190 (filter/parallax:parallax) -- the counted-for bucket's cheapest
    # program, landed with the textureLod identity admission
    # (the admission profile module's `texture-lod-admission-parallax-v1`).
    # This entry is that module's frozen `counted_for_seed_contract()._asdict()`
    # EXACTLY, copied field-for-field: patching it in and passing the capability
    # through `analyze_program` closes rung 1 (the march loop's
    # source-global-const-literal bound, MARCH_STEPS = 32, trip/product/charge
    # 32/32/32 -- well inside every cap) and surfaces rung 2 at exactly
    # `24:26: unsupported builtin textureLod`, verified live before landing.
    "filter/parallax:parallax": {
        "raw": "5ce5dce2ec8e8d7ebd3024c6a5bd5dcb068d0cf322bfd105c4fb3546e1b97642",
        "source": "281c8163d7f5fd47dc2ebd258003b04e1d41f7687c52e3c99e5aa56c911bd5f0",
        "defines": (), "integer": ("MARCH_STEPS", 8, "32", 32),
        "globals": (("MARCH_STEPS", 8, "int", "32"),
                    ("SHIFT_SCALE", 9, "float", "0.15")),
        "reads": (("main", 16, 58, 38, 58, 49),
                  ("main", 16, 59, 30, 59, 41)),
        "pre_functions": "39bfbb083f4383209661da6248eecff353f3f1ff7257c828bc1ce62bcf821808",
        "post_functions": "7b13f5ae2cd5f75f179c601d57d5ea818919841a700c3400d3ccb40f8ab4b9d0",
        "pre_whole": "920fe71bb122690f2169d2ee27ab6a4f908a18bf55b6031cb44fe51ba50c5eff",
        "post_whole": "30e996fec218dfd0c92f0f706d1cde5b0da84b25421fedf6d9f08479421d8a16",
        "interface": "9ff15dc1fd4f97bd0d392bd40d1cab39a4c1fcb988c2d79d595f933235d39314",
    },
    # Mandelbrot phase-1 seed registration.  This is the exact
    # counted_for_seed_contract() record owned by log_admission_profile; the
    # separate out/inout and sequential-dz carriers authenticate the other
    # source mechanisms and do not duplicate this MAX_ITER lock.
    "synth/mandelbrot:mandelbrot": {
        "raw": "0587dbc29f2dc8c186d7c47ebe6182e89dfe0387fc29a23826cac15499fba615",
        "source": "c062ee7852d0bfab69ca1e2ead6ad68d95dfa5fda9cff8232254b38b34c311a9",
        "defines": (), "integer": ("MAX_ITER", 24, "500", 500),
        "globals": (("PI", 20, "float", "3.14159265359"),
                    ("TAU", 21, "float", "6.28318530718"),
                    ("BAILOUT", 22, "float", "256.0"),
                    ("LOG2", 23, "float", "0.6931471805599453"),
                    ("MAX_ITER", 24, "int", "500")),
        "reads": (("main", 110, 368, 35, 368, 43),
                  ("mandelbrot_df64", 111, 226, 25, 226, 33)),
        "pre_functions": "5b24f4c4818b8ffee46ca02f752e4e19223ac97e677cccce310510af9a274a3d",
        "post_functions": "8240975403a5fe23b71b16799b7617dece132599ccfea69b24e717710f76f39b",
        "pre_whole": "d6a5840667d7293fa428a88eef00f8bcf4612a733958e738628c876ed210ebd3",
        "post_whole": "1ca045076337edb3bfcb5e618e0eb83f9633858eafb91176a2e713b4be28314e",
        "interface": "2f497a1fb59406d16decbd6bb2c0a5e4e7e5536774fa7ec56a34de12de657c43",
    },
}
SOURCE_GLOBAL_LITERAL_INT_KEYS = frozenset(_SOURCE_GLOBAL_LITERAL_INT_PROFILES)


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _walk_expression(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _walk_expression(child)


def _walk_statement_expressions(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement_expressions(child)


def clear_counted_loop_proofs(
        functions: tuple[TypedFunction, ...]) -> tuple[TypedFunction, ...]:
    """Return the exact submitted tree with only counted-loop proofs cleared."""
    return tuple(replace(function, body=tuple(_clear_proofs(statement)
                                               for statement in function.body))
                 for function in functions)


def authenticate_source_global_literal_int(
        *, key: str, raw_source: str, source: str,
        preprocessor_defines: tuple[object, ...], declarations: tuple[object, ...],
        functions: tuple[TypedFunction, ...], profile: str | None,
) -> tuple[tuple[int, int, str, object], ...]:
    """Authenticate the closed Task 23 pre-proof profile and return one bound seed."""
    expected = _SOURCE_GLOBAL_LITERAL_INT_PROFILES.get(key)
    if expected is None:
        if profile is not None:
            raise ValueError(f"{key}: source-global literal-int profile is not admitted")
        return ()
    if profile is None:
        return ()
    if profile != SOURCE_GLOBAL_LITERAL_INT_CAPABILITY:
        raise ValueError(f"{key}: exact source-global literal-int profile required")
    if _text_sha(raw_source) != expected["raw"] or _text_sha(source) != expected["source"]:
        raise ValueError(f"{key}: source-global literal-int source digest mismatch")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in preprocessor_defines)
    if defines != expected["defines"]:
        raise ValueError(f"{key}: source-global literal-int define profile mismatch")
    if functions != attach_counted_loop_proofs(functions, key):
        raise ValueError(f"{key}: source-global literal-int authentication requires canonical pre-proof functions")
    if _sha(functions) != expected["pre_functions"]:
        raise ValueError(f"{key}: source-global literal-int pre-function profile mismatch")

    source_globals = tuple(item for item in declarations
                           if item.symbol.storage not in {"uniform", "output"})
    actual_globals = tuple((item.symbol.name, item.symbol.id, item.type.display(),
                            item.initializer.literal if item.initializer is not None else None)
                           for item in source_globals)
    if actual_globals != expected["globals"]:
        raise ValueError(f"{key}: source-global literal-int declaration profile mismatch")

    # Two schema shapes coexist. The original six profiles admit exactly one
    # designated global int (singular "integer"/"reads" keys, unchanged so
    # their frozen hashes never move). A profile needing more than one --
    # e.g. filter/reindex:nmReindexReduce, which has both a loop-bound global
    # (MAX_TILE_DIM) and a second global used only in ordinary arithmetic
    # (TILE_SIZE) -- carries a plural "integers" key: a tuple of the same
    # 4-tuple shape, paired positionally with a tuple of per-integer "reads"
    # tuples. Every admitted integer is independently authenticated by the
    # identical checks below; nothing about the singular path changes.
    if "integers" in expected:
        integer_specs = expected["integers"]
        reads_specs = expected["reads"]
        if len(integer_specs) != len(reads_specs):
            raise ValueError(f"{key}: source-global literal-int integer/reads cardinality mismatch")
    else:
        integer_specs = (expected["integer"],)
        reads_specs = (expected["reads"],)

    seeds: list[tuple[int, int, str, object]] = []
    for (integer_name, integer_id, integer_literal, integer_value), expected_reads in zip(
            integer_specs, reads_specs):
        integer = next((item for item in source_globals if item.symbol.id == integer_id), None)
        if (integer is None or integer.symbol.name != integer_name
                or integer.symbol.storage != "const" or integer.symbol.writable
                or integer.symbol.direction != "in" or integer.type.display() != "int"
                or integer.initializer is None or integer.initializer.kind != "literal"
                or integer.initializer.type.display() != "int"
                or integer.initializer.category != "rvalue"
                or integer.initializer.children
                or integer.initializer.literal != integer_literal
                or integer.initializer.literal_value != integer_value
                or re.fullmatch(r"[1-9][0-9]*", integer_literal) is None):
            raise ValueError(f"{key}: malformed source-global literal-int declaration")

        reads: list[tuple[object, ...]] = []
        for function in functions:
            for statement in function.body:
                for expression in _walk_statement_expressions(statement):
                    if expression.kind == "id" and expression.symbol_id == integer_id:
                        span = expression.span
                        if (expression.symbol != integer.symbol
                                or expression.category != "readonly lvalue"):
                            raise ValueError(f"{key}: malformed source-global literal-int read")
                        reads.append((function.name, function.signature.id,
                                      span.start_line, span.start_column,
                                      span.end_line, span.end_column))
        if tuple(reads) != expected_reads:
            raise ValueError(f"{key}: source-global literal-int read profile mismatch")
        seeds.append((integer_id, integer_value, "source-global-const-literal", integer.symbol))
    return tuple(seeds)


def _checked_add(left: int, right: int) -> int:
    value = left + right
    return value if 0 <= value <= _MAX_CHARGE else _MAX_CHARGE + 1


def _checked_mul(left: int, right: int) -> int:
    if left < 0 or right < 0 or (left and right > _MAX_CHARGE // left):
        return _MAX_CHARGE + 1
    return left * right


def _integer_literal(value: TypedExpression) -> int | None:
    if value.kind == "literal" and value.type.display() == "int" and isinstance(value.literal_value, int):
        return value.literal_value
    if (value.kind == "unary" and value.operator == "-" and len(value.children) == 1
            and (operand := _integer_literal(value.children[0])) is not None):
        return -operand
    return None


def _integer_valued_float_literal(value: TypedExpression) -> int | None:
    """Exact-integer-valued float literal, e.g. ``0.0`` or ``40.0``.

    Only literals whose value is an exact integer are admitted (no rounding
    is ever performed), so the returned int is bit-exact to the GLSL source.
    """
    if (value.kind == "literal" and value.type.display() == "float"
            and isinstance(value.literal_value, float)
            and value.literal_value.is_integer()):
        return int(value.literal_value)
    if (value.kind == "unary" and value.operator == "-" and len(value.children) == 1
            and (operand := _integer_valued_float_literal(value.children[0])) is not None):
        return -operand
    return None


def _float_literal(value: TypedExpression) -> float | None:
    if value.kind == "literal" and value.type.display() == "float" and isinstance(value.literal_value, (int, float)):
        return float(value.literal_value)
    if (value.kind == "unary" and value.operator == "-" and len(value.children) == 1
            and (operand := _float_literal(value.children[0])) is not None):
        return -operand
    return None


def _loop_products(value: TypedStatement) -> tuple[int, ...]:
    result: list[int] = []
    if value.loop_proof is not None:
        result.append(value.loop_proof.lexical_product)
    for child in value.children:
        result.extend(_loop_products(child))
    return tuple(result)


def _clamp_float_upper_bound(value: TypedStatement) -> tuple[int, float, object] | None:
    """Recognize ``float X = clamp(<anything>, <lo-literal>, <hi-literal>);``.

    ``clamp()``'s result is mathematically <= hi for ANY value of the first
    argument (and any finite lo <= hi), independent of whether that first
    argument is itself bounded -- so this is sound regardless of what is
    being clamped. Generalizes the existing single-program
    ``reverb-clamp-1-8`` precedent to any source-level float clamp.
    """
    if value.kind != "decl" or len(value.expressions) != 1:
        return None
    declaration = value.expressions[0]
    if (declaration.kind != "declaration" or declaration.type.display() != "float"
            or declaration.symbol is None or declaration.symbol.storage != "local"
            or len(declaration.children) != 1):
        return None
    initializer = declaration.children[0]
    if (initializer.kind != "builtin" or initializer.callee != "clamp"
            or len(initializer.children) != 3):
        return None
    _source, minimum, maximum = initializer.children
    lo = _float_literal(minimum)
    hi = _float_literal(maximum)
    if lo is None or hi is None or lo > hi:
        return None
    return declaration.symbol_id or 0, hi, declaration.symbol


def _ceil_cast_int_bound(value: TypedStatement,
                         float_bounded: dict[int, tuple[float, object]]
                         ) -> tuple[int, int, str, object] | None:
    """Recognize ``int Z = int(ceil(W));`` where ``W`` is a proved-bounded
    float local (see ``_clamp_float_upper_bound``).

    ``ceil`` is monotonic non-decreasing, so ``ceil(W) <= ceil(bound)``
    whenever ``W <= bound``; converting a non-negative exact-integer float
    to ``int`` is exact, so the bound transfers losslessly.
    """
    if value.kind != "decl" or len(value.expressions) != 1:
        return None
    declaration = value.expressions[0]
    if (declaration.kind != "declaration" or declaration.type.display() != "int"
            or declaration.symbol is None or declaration.symbol.storage != "local"
            or len(declaration.children) != 1):
        return None
    cast = declaration.children[0]
    if cast.kind != "construct" or cast.type.display() != "int" or len(cast.children) != 1:
        return None
    ceiling = cast.children[0]
    if ceiling.kind != "builtin" or ceiling.callee != "ceil" or len(ceiling.children) != 1:
        return None
    operand = ceiling.children[0]
    if (operand.kind != "id" or operand.symbol_id is None
            or operand.symbol_id not in float_bounded):
        return None
    bound_value, bound_symbol = float_bounded[operand.symbol_id]
    if operand.symbol != bound_symbol:
        return None
    return declaration.symbol_id or 0, math.ceil(bound_value), "ceil-clamp-float-cast", declaration.symbol


def _local_bound(value: TypedStatement, key: str,
                 float_bounded: dict[int, tuple[float, object]]) -> tuple[int, int, str, object] | None:
    if value.kind != "decl" or len(value.expressions) != 1:
        return None
    declaration = value.expressions[0]
    if (declaration.kind != "declaration" or declaration.type.display() != "int"
            or declaration.symbol is None
            or len(declaration.children) != 1):
        return None
    initializer = declaration.children[0]
    literal = _integer_literal(initializer)
    if declaration.symbol.storage == "const" and literal is not None:
        return declaration.symbol_id or 0, literal, "local-const-literal", declaration.symbol
    ceil_bound = _ceil_cast_int_bound(value, float_bounded)
    if ceil_bound is not None:
        return ceil_bound
    if (key != "filter/reverb:reverb" or declaration.symbol.name != "iters"
            or declaration.symbol.storage != "local"):
        return None
    if (initializer.kind != "builtin" or initializer.callee != "clamp"
            or len(initializer.children) != 3):
        return None
    source, minimum, maximum = initializer.children
    if (source.kind != "id" or source.symbol is None or source.symbol.storage != "uniform"
            or source.symbol.name != "iterations" or source.type.display() != "int"
            or _integer_literal(minimum) != 1 or _integer_literal(maximum) != 8):
        return None
    return declaration.symbol_id or 0, 8, "reverb-clamp-1-8", declaration.symbol


def _start_value(value: TypedExpression, bounded: dict[int, tuple[int, str, object]]) -> int | None:
    """Loop start: an int literal, or ``-B`` for a proved-upper-bounded local B.

    The symmetric-window shape ``for (int i = -radius; i <= radius; i++)``
    needs a start that is not itself a literal. Since ``bounded[id]`` always
    stores a genuine upper bound on the local's runtime value, ``-bound`` is
    a genuine LOWER bound on ``-local`` (the local can never be more
    negative than ``-bound``), which is exactly the worst case the trip-count
    formula below needs -- sound independent of whether the same symbol is
    also used for the loop's upper bound.
    """
    literal = _integer_literal(value)
    if literal is not None:
        return literal
    if value.kind == "unary" and value.operator == "-" and len(value.children) == 1:
        operand = value.children[0]
        if operand.kind == "id" and operand.symbol_id in bounded:
            candidate_bound, _kind, candidate_symbol = bounded[operand.symbol_id]
            if operand.symbol == candidate_symbol:
                return -candidate_bound
    return None


def _annotate_sequence(values: tuple[TypedStatement, ...], key: str, depth: int,
                       ancestor_product: int,
                       bounded: dict[int, tuple[int, str, object]],
                       lane_bounded: tuple[object, ...] = ()) -> tuple[TypedStatement, ...]:
    result: list[TypedStatement] = []
    active = dict(bounded)
    float_active: dict[int, tuple[float, object]] = {}
    for value in values:
        annotated = _annotate_statement(
            value, key, depth, ancestor_product, active, lane_bounded)
        result.append(annotated)
        bound = _local_bound(annotated, key, float_active)
        if bound is not None:
            symbol_id, maximum, kind, symbol = bound
            active[symbol_id] = (maximum, kind, symbol)
        clamp_bound = _clamp_float_upper_bound(annotated)
        if clamp_bound is not None:
            symbol_id, maximum, symbol = clamp_bound
            float_active[symbol_id] = (maximum, symbol)
    return tuple(result)


def _annotate_statement(value: TypedStatement, key: str, depth: int,
                        ancestor_product: int,
                        bounded: dict[int, tuple[int, str, object]],
                        lane_bounded: tuple[object, ...] = ()) -> TypedStatement:
    if value.kind == "block":
        return replace(value, children=_annotate_sequence(
            value.children, key, depth, ancestor_product, bounded, lane_bounded))
    if value.kind == "if":
        return replace(value, children=tuple(
            _annotate_statement(child, key, depth, ancestor_product,
                                dict(bounded), lane_bounded)
            for child in value.children))
    if value.kind != "for":
        return replace(value, children=tuple(
            _annotate_statement(child, key, depth, ancestor_product,
                                dict(bounded), lane_bounded)
            for child in value.children))

    # Every admitted form has an initializer statement and body, then exact
    # condition/update expressions. Anything else remains ordinary unproved IR.
    if len(value.children) != 2 or len(value.expressions) != 2:
        return value
    initializer, body = value.children
    if (initializer.kind != "decl" or len(initializer.expressions) != 1
            or initializer.expressions[0].kind != "declaration"):
        return value
    declaration = initializer.expressions[0]
    induction_type = declaration.type.display()
    # `float` induction is admitted only for the narrow, mechanically-exact
    # shape verified by the loop-proof study: an integer-valued literal
    # start/bound and a unit `++` step, which is bit-exact for the small
    # ranges seen in the corpus (e.g. `for (float t = 0.0; t <= 40.0; t++)`)
    # -- the trip count is computed exactly the same way as the int case.
    # Float induction is admitted ONLY for an exact-integer-valued literal
    # start and bound with a unit `++` step -- the shape filter/zoomBlur uses.
    # This is a deliberate capability widening, landed with that program and
    # with the near-miss barrier re-armed one step out: a start or bound that
    # is a float literal but NOT exactly integer-valued stays rejected
    # (`float-fractional-start` / `float-fractional-bound` in
    # test_counted_for_v1_rejects_header_and_control_near_misses). Widening
    # this guard without that barrier update silently removes a rejection the
    # suite asserts, which is how it slipped through once before.
    if (induction_type not in {"int", "float"} or declaration.symbol is None
            or declaration.symbol.storage != "local" or len(declaration.children) != 1):
        return value
    if induction_type == "int":
        start = _start_value(declaration.children[0], bounded)
    else:
        start = _integer_valued_float_literal(declaration.children[0])
    condition, update = value.expressions
    if (start is None or condition.kind != "binary" or condition.operator not in {"<", "<="}
            or len(condition.children) != 2):
        return value
    induction, bound_expression = condition.children
    symbol_id = declaration.symbol_id
    if (symbol_id is None or declaration.symbol.id != symbol_id
            or induction.kind != "id" or induction.symbol_id != symbol_id
            or induction.symbol != declaration.symbol):
        return value
    if (update.kind not in {"post", "unary"} or update.operator != "++"
            or len(update.children) != 1 or update.children[0].kind != "id"
            or update.children[0].symbol_id != symbol_id
            or update.children[0].symbol != declaration.symbol):
        return value

    bound_kind = "literal"
    if induction_type == "int":
        bound = _integer_literal(bound_expression)
        if bound is None and bound_expression.kind == "id" and bound_expression.symbol_id in bounded:
            bound, bound_kind, bound_symbol = bounded[bound_expression.symbol_id]
            if bound_expression.symbol != bound_symbol:
                return value
        if bound is None and bound_expression.kind == "swizzle":
            matches = tuple(seed for seed in lane_bounded
                            if seed.expression == bound_expression)
            if len(matches) != 1:
                return value
            seed = matches[0]
            child = bound_expression.children[0] if len(bound_expression.children) == 1 else None
            if (child is None or child.kind != "id"
                    or child.symbol_id != seed.symbol_id
                    or child.symbol != seed.symbol
                    or bound_expression.member != ("x" if seed.lane == 0 else "y")):
                return value
            bound = seed.maximum
            bound_kind = seed.provenance
    else:
        bound = _integer_valued_float_literal(bound_expression)
    if bound is None:
        return value
    # A `return` inside an otherwise-fully-canonical loop can only shorten
    # the number of iterations actually executed relative to the proved
    # upper bound -- it can never extend it -- so the trip-count proof below
    # remains a sound upper bound whether or not the body returns early.
    trips = max(0, bound - start + (1 if condition.operator == "<=" else 0))
    current_product = _checked_mul(ancestor_product, trips)
    annotated_body = _annotate_statement(
        body, key, depth + 1, current_product, dict(bounded), lane_bounded)
    descendant_products = _loop_products(annotated_body)
    product = max((current_product, *descendant_products))
    proof = CountedLoopProof(symbol_id, start, bound, condition.operator,
                             update.operator, bound_kind, trips, depth + 1,
                             depth + 1, product, 0)
    return replace(value, children=(initializer, annotated_body), loop_proof=proof)


def _expressions(value: TypedExpression):
    yield value
    for child in value.children:
        yield from _expressions(child)


def _statement_calls(value: TypedStatement, depth: int = 0):
    for expression in value.expressions:
        for item in _expressions(expression):
            if item.kind == "call" and item.signature_id is not None:
                yield item.signature_id, depth
    child_depth = depth + 1 if value.kind == "for" and value.loop_proof is not None else depth
    for child in value.children:
        yield from _statement_calls(child, child_depth)


def _expression_charge(value: TypedExpression, function_charge) -> int:
    result = 0
    for child in value.children:
        result = _checked_add(result, _expression_charge(child, function_charge))
    if value.kind == "call" and value.signature_id is not None:
        result = _checked_add(result, function_charge(value.signature_id))
    return result


def _statement_charge(value: TypedStatement, function_charge) -> int:
    expression_charge = sum((_expression_charge(item, function_charge)
                             for item in value.expressions), 0)
    if value.kind == "if":
        arms = tuple(_statement_charge(child, function_charge) for child in value.children)
        return _checked_add(expression_charge, max(arms, default=0))
    if value.kind == "for" and value.loop_proof is not None:
        body = _statement_charge(value.children[1], function_charge)
        return _checked_mul(value.loop_proof.trip_count, _checked_add(1, body))
    result = expression_charge
    for child in value.children:
        result = _checked_add(result, _statement_charge(child, function_charge))
    return result


def _replace_metrics(value: TypedStatement, base_depth: int, entry_charge: int) -> TypedStatement:
    proof = value.loop_proof
    if proof is not None:
        proof = replace(proof, effective_depth=base_depth + proof.lexical_depth,
                        entrypoint_charge=entry_charge)
    return replace(value, loop_proof=proof,
                   children=tuple(_replace_metrics(child, base_depth, entry_charge)
                                  for child in value.children))


def _clear_proofs(value: TypedStatement) -> TypedStatement:
    return replace(value, loop_proof=None,
                   children=tuple(_clear_proofs(child) for child in value.children))


def attach_counted_loop_proofs(
        functions: tuple[TypedFunction, ...], key: str, *,
        source_global_bounds: tuple[tuple[int, int, str, object], ...] = (),
        runtime_scalar_bounds: tuple[object, ...] = (),
        runtime_lane_bounds: tuple[object, ...] = (),
) -> tuple[TypedFunction, ...]:
    """Attach local and whole-entrypoint loop evidence without consulting source text."""
    clean = clear_counted_loop_proofs(functions)
    initial_bounds = {symbol_id: (maximum, kind, symbol)
                      for symbol_id, maximum, kind, symbol in source_global_bounds}
    if len(initial_bounds) != len(source_global_bounds):
        raise ValueError(f"{key}: duplicate source-global counted-loop seed")
    runtime_bounds = {
        seed.symbol_id: (seed.maximum, seed.provenance, seed.symbol)
        for seed in runtime_scalar_bounds
    }
    if len(runtime_bounds) != len(runtime_scalar_bounds):
        raise ValueError(f"{key}: duplicate runtime counted-loop seed")
    if set(initial_bounds).intersection(runtime_bounds):
        raise ValueError(f"{key}: colliding counted-loop seed")
    lane_identities = tuple((seed.symbol_id, seed.lane, seed.expression)
                            for seed in runtime_lane_bounds)
    if len(set(lane_identities)) != len(lane_identities):
        raise ValueError(f"{key}: duplicate runtime lane counted-loop seed")
    initial_bounds.update(runtime_bounds)
    annotated = tuple(replace(function, body=_annotate_sequence(
        function.body, key, 0, 1, dict(initial_bounds), runtime_lane_bounds))
                      for function in clean)
    definitions = {function.signature.id: function for function in annotated if function.body}
    main = next((function for function in annotated if function.name == "main" and function.body), None)
    if main is None:
        return annotated

    # Maximum loop depth already active at each function entry. A growing
    # value after |functions| passes denotes an interprocedural cycle.
    base_depth = {signature_id: 0 for signature_id in definitions}
    queue = deque([main.signature.id])
    reachable = {main.signature.id}
    relaxations = 0
    while queue:
        signature_id = queue.popleft()
        function = definitions[signature_id]
        for statement in function.body:
            for callee, local_depth in _statement_calls(statement):
                if callee not in definitions:
                    continue
                newly_reachable = callee not in reachable
                reachable.add(callee)
                candidate = base_depth[signature_id] + local_depth
                if candidate > base_depth[callee] or newly_reachable:
                    base_depth[callee] = candidate
                    queue.append(callee)
                    relaxations += 1
                    if relaxations > max(1, len(definitions) * len(definitions)):
                        base_depth[callee] = _MAX_CHARGE
                        queue.clear()
                        break

    charging: set[int] = set()
    charge_cache: dict[int, int] = {}

    def function_charge(signature_id: int) -> int:
        if signature_id not in definitions:
            return 0
        if signature_id in charge_cache:
            return charge_cache[signature_id]
        if signature_id in charging:
            return _MAX_CHARGE + 1
        charging.add(signature_id)
        result = 0
        for statement in definitions[signature_id].body:
            result = _checked_add(result, _statement_charge(statement, function_charge))
        charging.remove(signature_id)
        charge_cache[signature_id] = result
        return result

    entry_charge = function_charge(main.signature.id)
    return tuple(replace(function, body=tuple(
        _replace_metrics(statement, base_depth.get(function.signature.id, 0), entry_charge)
        for statement in function.body)) for function in annotated)


def summarize_counted_loop_proofs(functions: tuple[TypedFunction, ...]) -> CountedLoopProgramProof:
    proofs: list[CountedLoopProof] = []
    unproved = 0
    definitions = {function.signature.id: function for function in functions if function.body}
    graph: dict[int, set[int]] = {signature_id: set() for signature_id in definitions}

    def statement(value: TypedStatement, owner: int) -> None:
        nonlocal unproved
        if value.kind in {"for", "while", "dowhile"}:
            if value.loop_proof is None:
                unproved += 1
            else:
                proofs.append(value.loop_proof)
        for expression in value.expressions:
            for item in _expressions(expression):
                if item.kind == "call" and item.signature_id in definitions:
                    graph[owner].add(item.signature_id)
        for child in value.children:
            statement(child, owner)

    for signature_id, function in definitions.items():
        for item in function.body:
            statement(item, signature_id)

    visiting: set[int] = set()
    visited: set[int] = set()

    def acyclic(node: int) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        result = all(acyclic(child) for child in graph[node])
        visiting.remove(node)
        visited.add(node)
        return result

    graph_acyclic = all(acyclic(node) for node in graph)
    return CountedLoopProgramProof(
        len(proofs), unproved,
        max((proof.effective_depth for proof in proofs), default=0),
        max((proof.lexical_product for proof in proofs), default=0),
        max((proof.entrypoint_charge for proof in proofs), default=0),
        graph_acyclic,
    )


def _whole_program_identity(program: TypedProgram, functions: tuple[TypedFunction, ...],
                            summary: CountedLoopProgramProof) -> tuple[object, ...]:
    return (
        program.key, program.source, program.raw_source, program.declarations,
        functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        summary, program.preprocessor_defines,
    )


def _interface_identity(program: TypedProgram) -> tuple[object, ...]:
    return (
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    )


def rebuild_authenticated_counted_loop_proofs(
        program: TypedProgram, profile: str | None,
        runtime_loop_bound_profile: str | None = None,
) -> tuple[tuple[TypedFunction, ...], CountedLoopProgramProof]:
    """Rebuild counted-loop proof only from the authenticated proof-free tree."""
    cleared = clear_counted_loop_proofs(program.functions)
    pre_functions = attach_counted_loop_proofs(cleared, program.key)
    seed = authenticate_source_global_literal_int(
        key=program.key, raw_source=program.raw_source, source=program.source,
        preprocessor_defines=program.preprocessor_defines,
        declarations=program.declarations, functions=pre_functions, profile=profile)
    # The runtime profile authenticates the exact proof-cleared program and
    # returns a single immutable record shared by proof construction and the
    # generated binding guard.  Import locally to keep the profile independent
    # of this proof builder.
    from .runtime_loop_bound_profile import (
        authenticate_runtime_loop_bound, validate_runtime_loop_contract)
    runtime_contract = authenticate_runtime_loop_bound(
        program, _text_sha(program.raw_source), runtime_loop_bound_profile)
    if runtime_contract is not None:
        validate_runtime_loop_contract(runtime_contract)
    expected = _SOURCE_GLOBAL_LITERAL_INT_PROFILES.get(program.key)
    pre_summary = summarize_counted_loop_proofs(pre_functions)
    if expected is not None:
        if _sha(_whole_program_identity(program, pre_functions, pre_summary)) != expected["pre_whole"]:
            raise ValueError(f"{program.key}: source-global literal-int pre-program profile mismatch")
        if _sha(_interface_identity(program)) != expected["interface"]:
            raise ValueError(f"{program.key}: source-global literal-int interface profile mismatch")
    attached = attach_counted_loop_proofs(
        pre_functions, program.key, source_global_bounds=seed,
        runtime_scalar_bounds=(() if runtime_contract is None
                               or runtime_contract.seed is None
                               else (runtime_contract.seed,)),
        runtime_lane_bounds=(() if runtime_contract is None
                             else runtime_contract.lane_seeds))
    return attached, summarize_counted_loop_proofs(attached)


def validate_source_global_literal_int_program(
        program: TypedProgram, profile: str | None) -> None:
    """Require the submitted Task 23 tree to equal independently rebuilt proof."""
    if program.key not in _SOURCE_GLOBAL_LITERAL_INT_PROFILES and profile is None:
        return
    attached, summary = rebuild_authenticated_counted_loop_proofs(program, profile)
    expected = _SOURCE_GLOBAL_LITERAL_INT_PROFILES[program.key]
    if program.functions != attached or program.counted_loop_proof != summary:
        raise ValueError(f"{program.key}: source-global literal-int post-proof mismatch")
    if _sha(attached) != expected["post_functions"]:
        raise ValueError(f"{program.key}: source-global literal-int post-function profile mismatch")
    if _sha(_whole_program_identity(program, attached, summary)) != expected["post_whole"]:
        raise ValueError(f"{program.key}: source-global literal-int post-program profile mismatch")
