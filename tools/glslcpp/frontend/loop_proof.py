"""Immutable proof construction for the deliberately narrow counted-for subset."""

from __future__ import annotations

from collections import deque
from dataclasses import replace
import hashlib
import math
import re

from .typed_ir import (CountedLoopProgramProof, CountedLoopProof, PreprocessorDefine, TypedExpression,
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
        "raw": "bd83ef6a8fb02370d51c333e63285c13406ad9ef4bafa64513b2018e61050a4e",
        "source": "59b88206d89357582820fb6da5c4ee43c2a57ed9cbfba9676bb441fceb477f04",
        "defines": (), "integer": ("N", 9, "32", 32),
        "globals": (("N", 9, "int", "32"),),
        "reads": (("main", 16, 45, 37, 45, 38), ("main", 16, 52, 25, 52, 26),
                  ("main", 16, 53, 41, 53, 42), ("main", 16, 58, 29, 58, 30)),
        "pre_functions": "d99d37c65d0e13b943da42d43913c27e60e969c974729378ceb4f889ce01b3d4",
        "post_functions": "3739290914b415422318656c5809fe10566698f72cf4cb3a483cbed8233f1fa4",
        "pre_whole": "8499872620c60fd294292bbc4b4211b29d0a9389488d7bddf8e6b294e6fac160",
        "post_whole": "6a25de57261c5ffc5ece64e2060f34f751d9673399e513c04559a998dd0b340e",
        "interface": "c37de59496abc0f87e9f304c31bcbd71695b720c40b3bbaeacbc9ccc4aa9d561",
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
    # Relocked for the generic runtime-define contract: METHOD moved from a
    # literal int define to a dynamic uniform, so normalize() prepends one
    # `uniform int METHOD;` declaration line ahead of everything else in the
    # source. That is the entire cause of every field below that moved: every
    # symbol id after it (MAX_STEPS 8->9, STEP_PX 9->10, MAX_REACH 10->11)
    # shifts by exactly +1, the read site's line/column shift by the same one
    # prepended line, and every hash that folds in the source text, the
    # define tuple, or a declaration/read touching those ids changes with it.
    # No other declaration, read, or loop shape moved -- recomputed
    # mechanically with this module's own helpers
    # (rebuild_authenticated_counted_loop_proofs /
    # validate_source_global_literal_int_program) against the dynamic tree,
    # then round-trip verified through validate_source_global_literal_int_program
    # before landing.
    "filter/wind:wind": {
        "raw": "68eb0f4deca51ab5352307fa06509b153cf19a29cea4820d054adafa42655f22",
        "source": "f459c408a2f76df8398a961f2e7aeaa33429b7e96f4182149cfba6debe7f1efa",
        "defines": (("METHOD", "str", "int"),), "integer": ("MAX_STEPS", 9, "128", 128),
        "globals": (("MAX_STEPS", 9, "int", "128"),
                    ("STEP_PX", 10, "float", "1.0"),
                    ("MAX_REACH", 11, "float", "128.0")),
        "reads": (("main", 14, 53, 26, 53, 35),),
        "pre_functions": "c9739b5aee98d2f0055be755dbe8976d9f0a98ca3b0482b0d69c9cb2729ace99",
        "post_functions": "dcd8b41bdc9b7b3063d9b976fa2602a64a62dcc14981d7b544cc5e1902e6b204",
        "pre_whole": "98396b66f7ee8a78ad489a6f1174e629bbed89986a74ed65123fceb7d7fcd7d3",
        "post_whole": "80ad69e1f215d2ae84db10834d5c58aa5dd311ea30366721c2580f766cea9c3a",
        "interface": "0eb70d16be69494a13ca856356a467bc8391e9bed0e3347fae04400c9061e1df",
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
        "raw": "6e6f740356f7ced1cbd40b3a991dd0ef654e39ecaeec8c52e091a08f68e3b3bd",
        "source": "4a28158eff2b0f94d9568c6a06aa61a924e51b4901cb59698a8a4498dd782986",
        "defines": (), "integer": ("MAX_ITER", 24, "2048", 2048),
        "globals": (("PI", 20, "float", "3.14159265359"),
                    ("TAU", 21, "float", "6.28318530718"),
                    ("BAILOUT", 22, "float", "256.0"),
                    ("LOG2", 23, "float", "0.6931471805599453"),
                    ("MAX_ITER", 24, "int", "2048")),
        "reads": (("main", 110, 369, 35, 369, 43),
                  ("mandelbrot_df64", 111, 227, 25, 227, 33)),
        "pre_functions": "071753fc9985b4c09c1cb247522106ecc8a814b4e7a9a05f28acd302c3e6985e",
        "post_functions": "9df77469d8caf1799a6092f2f581aa2ad1516d715ab8737a1fb2f8e33d3bea70",
        "pre_whole": "48a5b1c3f5fc6238a469521c8da9337e2683c3d9b371b5150c1810427aceb78b",
        "post_whole": "673a127ed44de1e7fa0ce7ea88db6a575035c58265f9f21323f9edf821a2b44d",
        "interface": "e8c746cd6e89dddbcc041f4498036036b171f9b3f9b24e2fd480f631ce92e124",
    },
    # classicNoisedeck/shapes3d:shapes3d -- the pending corpus's one counted-for
    # blocker whose loop bounds are already inside the proven Task-23 mechanism:
    # `for (int i = 0; i < MAX_STEPS; i++)` in `rayMarch` (a break-aware march
    # that can only shorten against the proved 100-trip upper bound, exactly
    # like the renderCubemapSurface entry below) plus a literal `for i < 3`
    # orientation loop. Entry computed mechanically with this module's own
    # helpers (rebuild/attach + validate round-trip), then verified to advance
    # the program's recorded first blocker to its next authentic frontier
    # (`54:1: unsupported struct declaration`) without promoting it.
    "classicNoisedeck/shapes3d:shapes3d": {
        "raw": "818badfbadcf295d1863d208c0d0582a1349ff64f44dbf43f905a92fcfd4c5ad",
        "source": "2f2b40281c84c67297a466a42f7780c8b21b2b037a41bcf7d9c9fb6a98b03617",
        "defines": (("BLEND_MODE", "int", "10"),
                    ("SHAPE_A", "int", "30"),
                    ("SHAPE_B", "int", "10")),
        "integer": ("MAX_STEPS", 37, "100", 100),
        "globals": (("MIN_DIST", 35, "float", "0.01"),
                    ("MAX_DIST", 36, "float", "200.0"),
                    ("MAX_STEPS", 37, "int", "100"),
                    ("fwdA", 61, "mat3", None),
                    ("fwdB", 62, "mat3", None),
                    ("invB", 63, "mat3", None),
                    ("invA", 64, "mat3", None)),
        "reads": (("rayMarch", 118, 367, 25, 367, 34),),
        "pre_functions": "9d16cfdf81910e96d30e7b91e6ece36985ecca22bb04dc72448ef4bf7badcf5e",
        "post_functions": "4d4046d9448e38c67aab440872deb681ccb03fb632f02c1e25fdd303df5285da",
        "pre_whole": "87b2d56ef1f6db7e70e407069e17d95ff3e384ff685358075a52b2fde2e1497b",
        "post_whole": "fdd41134212bfb343a643861cd2fed235e5d83c13da7f81aeb27f0ec2a980316",
        "interface": "e347814a67a9611866fcb8c923c5f32e3e96a850ab08116dd23471e3b66fc24a",
    },
    # The three render-family march programs. renderLit3d's single march loop
    # is a plain MAX_STEPS read; render3d and renderCubemap3d additionally
    # bound their DDA traversal with `MAX_STEPS * 2` (the sound product bound
    # in _annotate_statement: 256*2=512, exactly the trip cap). The two cross
    # carriers' cross-builtin profiles are re-locked to these seed-attached
    # post-proof trees (same pre_functions as the profile's frozen
    # functions_sha256 -- proof the profile was locked pre-proof).
    "render/render3d:render3d": {
        "raw": "138d3e0daa247100fe3553b2699bce3f302e77fce25d9d4fb507868d31a84a30",
        "source": "a211ec112f89ccea8cabeee2bd7f45a896b9c54812b49ff4a6091e9629aa3f53",
        "defines": (("FILTERING", "int", "0"), ("INVERT", "bool", "false")),
        "integer": ("MAX_STEPS", 17, "256", 256),
        "globals": (("TAU", 15, "float", "6.283185307179586"),
                    ("PI", 16, "float", "3.141592653589793"),
                    ("MAX_STEPS", 17, "int", "256"),
                    ("MAX_DIST", 18, "float", "10.0")),
        "reads": (("isosurfaceTrace", 48, 281, 25, 281, 34),
                  ("voxelTrace", 55, 161, 25, 161, 34)),
        "pre_functions": "1bd80d666ba4aa91256d70d6168627a72859f740f7196d8e41f3c047f99a9294",
        "post_functions": "f658d31e5a1ba348713e862f9016ece193419831f58da04b035a4c7bb0faba37",
        "pre_whole": "b575936e63deaa050942c3deb8e2ade6a979c4ae3a0e27cffe76a390ff722d91",
        "post_whole": "8de2584a45895b30fec34b527112c52c3b0688f041c299a42bdeac879e493838",
        "interface": "4f1eb4b5aea7ad075a5756dfa748d88f83705993085f1446c427d9d4e09cb3fe",
    },
    "render/renderLit3d:renderLit3d": {
        "raw": "ea309e7e9c4bcb13fd96bf05f0e587bfd25557b7184872b32aabc160df49b627",
        "source": "436cdf22da60272b948b145b0dabc113d65bc1b9006659517e07dcd80ba48b62",
        "defines": (),
        "integer": ("MAX_STEPS", 28, "256", 256),
        "globals": (("TAU", 26, "float", "6.283185307179586"),
                    ("PI", 27, "float", "3.141592653589793"),
                    ("MAX_STEPS", 28, "int", "256"),
                    ("MAX_DIST", 29, "float", "10.0"),
                    ("NEAR_CLIP", 30, "float", "0.01")),
        "reads": (("raymarch", 66, 227, 25, 227, 34),),
        "pre_functions": "a9b40ebce520c2e194ee9eb60f03527b288c359ac73e3599ecda0c5c26d6a1e2",
        "post_functions": "d6c4f6bbf5a4cd19ca2006fd1b997fde798c280a51039246be9e1c423cc41e38",
        "pre_whole": "cb31cbfb6ffd1f480797291308316c4175d0c7c157471f5730c81d3b4025c4bb",
        "post_whole": "2688f3be3bed47ff1facee122dd2e7da11501f21044bda9206c847efaf077ac0",
        "interface": "e3f61fcd73cd0441cf76d4a119f618bd6fad0515ec6b588d074ccc2751e87b86",
    },
    "render/renderCubemap3d:renderCubemap3d": {
        "raw": "bcebff481c2d945e140870b50ce3e32e12bc3f198f75a53dc6d2450d5777db26",
        "source": "57a7ef1b4ac2174dbd69fecc64f46259a82c2b55cc0e493373e9b6ac11f82b0e",
        "defines": (("FILTERING", "int", "0"), ("INVERT", "bool", "false")),
        "integer": ("MAX_STEPS", 16, "256", 256),
        "globals": (("TAU", 14, "float", "6.283185307179586"),
                    ("PI", 15, "float", "3.141592653589793"),
                    ("MAX_STEPS", 16, "int", "256"),
                    ("MAX_DIST", 17, "float", "10.0")),
        "reads": (("isosurfaceTrace", 47, 280, 25, 280, 34),
                  ("voxelTrace", 54, 160, 25, 160, 34)),
        "pre_functions": "b6d1371705e73f9b5d7a6635c107b023b0012c465e9235317ed2d965dbbfaaf9",
        "post_functions": "97abf4cd61079737e7ee7a5e3166ca7973b7cac65482ad79773916d5427ddd75",
        "pre_whole": "5c75a95c6c97407d073a2f4059c49b3c292f99cd8cd10f64dccadea5b48b69bf",
        "post_whole": "b0abe54e4d65256ddebe7496c9842158eb75a67f9b949e061e1bc5087cc82e8f",
        "interface": "d17ef2b2ff37f039f346057c9545147f5f865975399678017d66237332938dc1",
    },
    "render/renderCubemapSurface:renderCubemapSurface": {
        "raw": "ce467e742120b8a2ec9c34898a2fd1e2f56a85cbe5d27774bcbb1b7f204511fc",
        "source": "0c1460653b347fcf2c27eebc51424190bf186648d23a348b34736ec8469f2c05",
        "defines": (), "integer": ("MAX_STEPS", 14, "256", 256),
        "globals": (("MAX_STEPS", 14, "int", "256"),),
        "reads": (("main", 22, 98, 40, 98, 49), ("main", 22, 100, 29, 100, 38)),
        "pre_functions": "9ee121b07ce12454fffa970c2bc8db914fbfcb2272db204ed757f0defbc19c01",
        "post_functions": "026bc9c817b14f2360e6bf53cda08d2cfa8ff41979388bd9f6ca02967377df98",
        "pre_whole": "ed655994b18e0c07d6349e506f8a2491f2ae398fbfc2d27580ed76dbfc68b9dc",
        "post_whole": "e231d8537589aceb772d0053cb37f9f109cbe26a04fcaac4db53277acd023d86",
        "interface": "dae25c3eaef96bcdabf93ba0681b2b2978d4da0e534ee05bd42aa397cda31cb9",
    },
    # The parameter-bound counted-for program: synth3d/fractal3d:precompute
    # (2026-10-01 leg). Third schema shape, authenticated by
    # _authenticate_parameter_uniform_int below: the loop bound is a function
    # parameter (`int maxIter`), and the proof is INTERPROCEDURAL -- every call
    # site of each carrier function (exactly one, inside computeFractal) binds
    # the parameter to the runtime value of the `iterations` int uniform, so
    # the frozen authority metadata maximum (20) is a genuine upper bound
    # wherever the loop can execute. Fail-closed against: a second call site
    # for any carrier function, a call argument that is not exactly the
    # uniform symbol, any rewrite of the parameter inside its function, a
    # parameter-identity mismatch, and read-span drift. The corpus ratchet
    # additionally authenticates the pending.json metadata record through
    # authenticate_parameter_uniform_metadata, binding the frozen maximum to
    # the authority record. The schema returns the same 4-tuple seed shape as
    # the const-global path, so attach/rebuild/validate machinery is shared
    # unchanged and no generated artifact moves.
    "synth3d/fractal3d:precompute": {
        "raw": "4bc39fb7920cf0829cc6a6fc4670cdac9f5ea68c5438f569050a4732c1e6de19",
        "source": "3dd80cd8f5a01004ace3df4e3dea95b0861b8e1f191b66958ceabe36f3a8be93",
        "defines": (),
        "parameter_uniform": (
            "iterations", 4, "int",
            {"default": 10, "max": 20, "min": 1, "type": "int", "uniform": "iterations"},
        ),
        "parameters": (
            ("mandelbulb", 40, 15, "maxIter", 2),
            ("juliaBulb", 37, 20, "maxIter", 3),
            ("mandelcube", 41, 26, "maxIter", 2),
            ("juliaCube", 38, 31, "maxIter", 3),
        ),
        "reads": (
            (("mandelbulb", 40, 28, 25, 28, 32), ("mandelbulb", 40, 55, 42, 55, 49)),
            (("juliaBulb", 37, 66, 25, 66, 32), ("juliaBulb", 37, 92, 42, 92, 49)),
            (("mandelcube", 41, 111, 25, 111, 32), ("mandelcube", 41, 140, 42, 140, 49)),
            (("juliaCube", 38, 154, 25, 154, 32), ("juliaCube", 38, 183, 42, 183, 49)),
        ),
        "pre_functions": "12e274f8dbf497961ff11160898d060106eac4e5f478af2aeb8694da9752d2f3",
        "post_functions": "f7b555f7d7e13a719e70c922d943b7948d7cbf4f4af39d1e563cf2c3e3edb432",
        "pre_whole": "010e849e6f0200c60386d2e534fff888d30337d006d87842378212014773b493",
        "post_whole": "a245a18602b73ead28931d4625cc43be8107ded0b7055dca174da22097c49560",
        "interface": "cd93a4bff583a921ca02539c2f537dde9b8151efd5f298f0bd3ae9dae831cbb7",
    },
    # The second parameter-bound counted-for program:
    # synth3d/flythrough3d:precompute (2026-10-05 leg). Same third schema
    # shape as fractal3d: the two fractal carriers' march loops are bounded
    # by the function parameter `int maxIter` (argument index 2 in both),
    # and the proof is INTERPROCEDURAL -- each carrier has exactly one call
    # site (inside computeFractal) whose maxIter argument is the `iterations`
    # int uniform by object identity, so the frozen authority metadata
    # maximum (24) is a genuine upper bound wherever a loop can execute.
    # Fail-closed against: a second call site for either carrier, a call
    # argument that is not exactly the uniform symbol, any rewrite of the
    # parameter inside its function, a parameter-identity/type/direction
    # mismatch, and read-span drift. The corpus ratchet additionally
    # authenticates the pending.json metadata record through
    # authenticate_parameter_uniform_metadata. The cross-builtin carrier
    # composes deliberately: this program's cross profile is re-locked to
    # the seed-attached post-proof tree (pre-re-lock values functions
    # 6f3edced… / whole 250d2cb9… are exactly this entry's pre digests), so
    # the two authentications cannot bind different trees. The seed reuses
    # the const-global 4-tuple shape; attach/rebuild/validate machinery is
    # shared unchanged and no generated artifact moves.
    "synth3d/flythrough3d:precompute": {
        "raw": "e4288dfc3384f76e63eda968ad4ce3219a9b96989d8e6ff38755dbcf44f788f3",
        "source": "b8ae9dac1d40943d7bd023fbd6bc26494c686fe62fecd2e26551367ea82eaa58",
        "defines": (),
        "parameter_uniform": (
            "iterations", 8, "int",
            {"default": 12, "max": 24, "min": 4, "type": "int", "uniform": "iterations"},
        ),
        "parameters": (
            ("mandelbulb", 62, 38, "maxIter", 2),
            ("mandelbox", 61, 44, "maxIter", 2),
        ),
        "reads": (
            (("mandelbulb", 62, 186, 25, 186, 32), ("mandelbulb", 62, 213, 37, 213, 44)),
            (("mandelbox", 61, 236, 25, 236, 32), ("mandelbox", 61, 264, 37, 264, 44)),
        ),
        "pre_functions": "6f3edced834a17851390e18356b9a4b6a5fb72edde48d69b50f95b8594b0e93a",
        "post_functions": "7de221d4edf58a01ab203317ccca1cda66915a846e55798d1e12f161482d4375",
        "pre_whole": "250d2cb9a66ad470c67489ba4e5af1f9036b9e21d5b0f8be39174df601e29258",
        "post_whole": "0408c95a2a47cc03302de544b4f68cf50b6b607d2e77291d0c53c3f906424717",
        "interface": "45e03760bdc51c6217d746b5fb329fe8c67e9f2b5301fb88660c79db93f32c8a",
    },
}
SOURCE_GLOBAL_LITERAL_INT_KEYS = frozenset(_SOURCE_GLOBAL_LITERAL_INT_PROFILES)

_RENDER_RUNTIME_DEFINES = (("FILTERING", "str", "int"),
                           ("INVERT", "str", "bool"))
_RENDER_DYNAMIC_SOURCE_GLOBAL_LITERAL_INT_PROFILES = {
    "render/render3d:render3d": {
        **_SOURCE_GLOBAL_LITERAL_INT_PROFILES["render/render3d:render3d"],
        "source": "001cda0e746f30bfd3c0d407ebc5b057cbbca5f7d359cae71bec196e37292b57",
        "defines": _RENDER_RUNTIME_DEFINES,
        "integer": ("MAX_STEPS", 19, "256", 256),
        "globals": (("TAU", 17, "float", "6.283185307179586"),
                    ("PI", 18, "float", "3.141592653589793"),
                    ("MAX_STEPS", 19, "int", "256"),
                    ("MAX_DIST", 20, "float", "10.0")),
        "reads": (("isosurfaceTrace", 50, 283, 25, 283, 34),
                  ("voxelTrace", 57, 163, 25, 163, 34)),
        "pre_functions": "ff300c17577db76c376dd3a08c13f3407bf66db00b05e9c4f10c1de340a380fe",
        "post_functions": "5dcdd99853125e9f83aab78cd0fb2bfbeef19488832897e0d5d9f7bb0d735af9",
        "pre_whole": "3986d950cfdae31d53bfc34d3a1e53cd62bdfc410432e991b3579d34900d318e",
        "post_whole": "1bc8d1107edcc33329aac2d5ff524f9ddc26a1e98fd1eb3486bfb438caff5a86",
        "interface": "7a3699a10686d022f30a5b40aac40f164b022bc7203508f875949f8f5c87cf31",
    },
    "render/renderCubemap3d:renderCubemap3d": {
        **_SOURCE_GLOBAL_LITERAL_INT_PROFILES["render/renderCubemap3d:renderCubemap3d"],
        "source": "4e85f68b66a23f5eaf3a945469a5276ae42b6f00c8f8dc525db381e8fad33924",
        "defines": _RENDER_RUNTIME_DEFINES,
        "integer": ("MAX_STEPS", 18, "256", 256),
        "globals": (("TAU", 16, "float", "6.283185307179586"),
                    ("PI", 17, "float", "3.141592653589793"),
                    ("MAX_STEPS", 18, "int", "256"),
                    ("MAX_DIST", 19, "float", "10.0")),
        "reads": (("isosurfaceTrace", 49, 282, 25, 282, 34),
                  ("voxelTrace", 56, 162, 25, 162, 34)),
        "pre_functions": "f9b7e61f2cd23797fd947d177e95c94f75a9c6f92c6f9e1d9230596beb0507be",
        "post_functions": "eb2d4805c0129b09ca4af87bb243873f50694a2d6c1566e24290fe8bc4a1963e",
        "pre_whole": "93b61a46387564da36d7cd0d0fe476b4076328dfe323ead6a320c62c6da4431d",
        "post_whole": "ce339d9a868be249323e8b515139dfdd89fb89008f06160fe0c236e43413338f",
        "interface": "e28d67288dcc7fa6ee07865836f19cb8956614595616b5d2f147baa044e14635",
    },
}

# Keep the default Strokes proof unchanged. The runtime MODE tree adds one
# uniform before MAX_TAPS and changes the exact read and whole-tree identities.
_STROKES_RUNTIME_DEFINES = (("MODE", "str", "int"),)
_STROKES_DYNAMIC_SOURCE_GLOBAL_LITERAL_INT_PROFILE = {
    **_SOURCE_GLOBAL_LITERAL_INT_PROFILES["filter/strokes:stkSmear"],
    "source": "ef71bff7e3d7867eb526cfddd51651760df59a885bed93a6d863c4597d52f336",
    "defines": _STROKES_RUNTIME_DEFINES,
    "integer": ("MAX_TAPS", 9, "24", 24),
    "globals": (("MAX_TAPS", 9, "int", "24"),),
    "reads": (("smear", 40, 173, 26, 173, 34),),
    "pre_functions": "fd06bed6754e7ca9fa227a68c74c18eb9f9cbfeddec40add4212478b624086d0",
    "post_functions": "00cfe44379387000f2882c259ae8a0acbbf23a28c3df69063c96b489b3d39244",
    "pre_whole": "f25baf8e39413c97a187469da685b4548976f9341aaaece9a3dfe39b1377b75c",
    "post_whole": "3be4df5ec3865bab5a5e7061c4296ecd0e077643a937bab0b51e4d69bcef4256",
    "interface": "64da3eb5d6499d4d405499a32fb65f0dee64dc97dfc714b5f1614554af79323a",
}


def _source_global_profile(key: str, defines: tuple[object, ...]) -> dict | None:
    if not isinstance(defines, tuple) or any(
            not isinstance(item, PreprocessorDefine) for item in defines):
        raise ValueError(f"{key}: malformed source-global define profile")
    shape = tuple((item.name, item.kind, item.canonical_value) for item in defines)
    if key == "filter/strokes:stkSmear" and shape == _STROKES_RUNTIME_DEFINES:
        return _STROKES_DYNAMIC_SOURCE_GLOBAL_LITERAL_INT_PROFILE
    if key in _RENDER_DYNAMIC_SOURCE_GLOBAL_LITERAL_INT_PROFILES and shape == _RENDER_RUNTIME_DEFINES:
        return _RENDER_DYNAMIC_SOURCE_GLOBAL_LITERAL_INT_PROFILES[key]
    if key == "classicNoisedeck/shapes3d:shapes3d":
        from .shapes3d_runtime_profile import DEFINES, SOURCE_GLOBAL
        if shape == DEFINES:
            return SOURCE_GLOBAL
    return _SOURCE_GLOBAL_LITERAL_INT_PROFILES.get(key)


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
    expected = _source_global_profile(key, preprocessor_defines)
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

    # Third schema shape: parameter-bound loops (see the entry comment). The
    # bound is a function parameter whose every call site binds it to the
    # runtime value of an int uniform; the seed reuses the const-global
    # 4-tuple shape so all downstream attach/rebuild/validate machinery is
    # shared unchanged.
    if "parameter_uniform" in expected:
        return _authenticate_parameter_uniform_int(key, expected, declarations, functions)

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


def _authenticate_parameter_uniform_int(
        key: str, expected: dict, declarations: tuple[object, ...],
        functions: tuple[TypedFunction, ...],
) -> tuple[tuple[int, int, str, object], ...]:
    """Authenticate the parameter-bound schema and return one seed per carrier.

    The proof is interprocedural: each carrier function's counted loop is
    bounded by its ``maxIter`` parameter, and the authentication proves that
    every call site of the function binds that parameter to the runtime value
    of the exact int uniform frozen in the entry (exactly one call site per
    carrier exists in the whole program, and its argument at the frozen
    position is that uniform symbol). The seed's maximum is the frozen
    authority metadata maximum, which ``authenticate_parameter_uniform_metadata``
    binds to the live authority record in the ratchet path.
    """
    uniform_name, uniform_id, uniform_type, metadata = expected["parameter_uniform"]
    uniform = next((item for item in declarations if item.symbol.id == uniform_id), None)
    if (uniform is None or uniform.symbol.name != uniform_name
            or uniform.symbol.storage != "uniform" or uniform.symbol.writable
            or uniform.type.display() != uniform_type):
        raise ValueError(f"{key}: malformed parameter-uniform declaration")
    maximum = metadata["max"]
    if not isinstance(maximum, int) or maximum < 0:
        raise ValueError(f"{key}: malformed parameter-uniform maximum")

    # Rewrite barrier: an assignment (plain or compound) or ++/-- whose
    # TARGET operand tree is the parameter, or a call actual that could
    # rewrite it (an out/inout formal), would detach the runtime value from
    # the authenticated call-site binding -- fail closed. A read of the
    # parameter inside an assigned value is not a rewrite and is sound: the
    # bound value is unchanged, and every read inside a carrier function is
    # enumerated and frozen by the read profile below (any additional read
    # aborts the authentication).
    rewrite_kinds = {"assign", "inc", "dec"}
    parameter_ids = {item[2] for item in expected["parameters"]}
    callee_forms = {function.signature.id: function
                    for function in functions if function.body}
    call_sites: dict[int, list] = {}
    for function in functions:
        for statement in function.body:
            for expression in _walk_statement_expressions(statement):
                if expression.kind in rewrite_kinds and expression.children and any(
                        child.kind == "id" and child.symbol_id in parameter_ids
                        for child in _walk_expression(expression.children[0])):
                    raise ValueError(
                        f"{key}: parameter-uniform carrier parameter is rewritten")
                if expression.kind == "call" and expression.signature_id is not None:
                    callee = callee_forms.get(expression.signature_id)
                    if callee is None:
                        raise ValueError(
                            f"{key}: parameter-uniform callee identity missing")
                    if (len(expression.children) == len(callee.parameters)
                            and any(child.kind == "id"
                                    and child.symbol_id in parameter_ids
                                    and callee.parameters[index].direction != "in"
                                    for index, child in enumerate(expression.children))):
                        raise ValueError(
                            f"{key}: parameter-uniform carrier parameter is rewritten")
                    call_sites.setdefault(expression.signature_id, []).append(expression)

    seeds: list[tuple[int, int, str, object]] = []
    for spec, expected_reads in zip(expected["parameters"], expected["reads"]):
        function_name, signature_id, parameter_id, parameter_name, argument_index = spec
        function = next((item for item in functions
                         if item.name == function_name
                         and item.signature.id == signature_id and item.body), None)
        if function is None:
            raise ValueError(f"{key}: parameter-uniform carrier function missing")
        if (argument_index >= len(function.parameters)
                or function.parameters[argument_index].id != parameter_id
                or function.parameters[argument_index].name != parameter_name
                or function.parameters[argument_index].type.display() != "int"
                or function.parameters[argument_index].direction != "in"):
            raise ValueError(f"{key}: malformed parameter-uniform carrier parameter")
        parameter = function.parameters[argument_index]
        reads = []
        for statement in function.body:
            for expression in _walk_statement_expressions(statement):
                if expression.kind == "id" and expression.symbol_id == parameter_id:
                    span = expression.span
                    if expression.symbol != parameter:
                        raise ValueError(f"{key}: malformed parameter-uniform read")
                    reads.append((function.name, function.signature.id,
                                  span.start_line, span.start_column,
                                  span.end_line, span.end_column))
        if tuple(reads) != expected_reads:
            raise ValueError(f"{key}: parameter-uniform read profile mismatch")
        sites = call_sites.get(signature_id, ())
        if len(sites) != 1 or argument_index >= len(sites[0].children):
            raise ValueError(
                f"{key}: parameter-uniform call-site cardinality mismatch")
        argument = sites[0].children[argument_index]
        if (argument.kind != "id" or argument.symbol_id != uniform_id
                or argument.symbol != uniform.symbol):
            raise ValueError(
                f"{key}: parameter-uniform call-site argument mismatch")
        seeds.append((parameter_id, maximum,
                      "parameter-uniform-argument-bound", parameter))
    return tuple(seeds)


def authenticate_parameter_uniform_metadata(effect: object, key: str) -> None:
    """Bind the frozen parameter-uniform maximum to the authority metadata record.

    Called from the corpus ratchet with the pending.json effect projection so
    the seed maximum can never drift from the record the authority actually
    declares (a raised maximum would silently unsound every bound loop).
    """
    expected = _SOURCE_GLOBAL_LITERAL_INT_PROFILES.get(key)
    if expected is None or "parameter_uniform" not in expected:
        return
    uniform_name, _uniform_id, _uniform_type, metadata = expected["parameter_uniform"]
    try:
        record = effect["params"][uniform_name]  # type: ignore[index]
    except (KeyError, TypeError):
        raise ValueError(f"{key}: parameter-uniform metadata record missing") from None
    if record != metadata:
        raise ValueError(f"{key}: parameter-uniform metadata record mismatch")


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


def _root_id(value: TypedExpression) -> TypedExpression | None:
    while value.kind in {"swizzle", "member", "index"} and value.children:
        value = value.children[0]
    return value if value.kind == "id" else None


def _never_rewritten_literal_locals(
        body: tuple[TypedStatement, ...]) -> frozenset[int]:
    """Symbol ids of non-const local ``int`` literal declarations that are
    provably never rewritten anywhere in the enclosing function.

    This is the sound write-proof behind the ``local-literal-never-rewritten``
    counted-for bound provenance: a non-const local declared with a plain int
    literal keeps that exact value for the whole function when no statement
    can ever store to it, so it may bound a counted-for loop exactly like a
    ``const`` local (classicNoisedeck/noise3d:noise3d's
    ``int maxSteps = 100;`` march bound). A write is any of: an
    assignment/compound-assignment target chain, a ``++``/``--`` operand
    (prefix or postfix), or -- conservatively, because callee parameter
    directions are not available at proof time -- ANY occurrence inside a
    call's argument list (an out/inout actual is a write; failing closed on
    ordinary read arguments only narrows admission, never loosens it).
    """
    candidates: set[int] = set()
    written: set[int] = set()

    def scan_expression(value: TypedExpression) -> None:
        if value.kind == "assign":
            root = _root_id(value.children[0]) if value.children else None
            if root is not None and root.symbol_id is not None:
                written.add(root.symbol_id)
        elif (value.kind in {"unary", "post"} and value.operator in {"++", "--"}
                and value.children):
            root = _root_id(value.children[0])
            if root is not None and root.symbol_id is not None:
                written.add(root.symbol_id)
        elif value.kind == "call":
            for argument in value.children:
                for item in _expressions(argument):
                    if item.kind == "id" and item.symbol_id is not None:
                        written.add(item.symbol_id)
        for child in value.children:
            scan_expression(child)

    def scan_statement(value: TypedStatement) -> None:
        if value.kind == "decl":
            for declaration in value.expressions:
                if (declaration.kind == "declaration"
                        and declaration.type.display() == "int"
                        and declaration.symbol is not None
                        and declaration.symbol.storage == "local"
                        and len(declaration.children) == 1
                        and _integer_literal(declaration.children[0]) is not None
                        and declaration.symbol_id is not None):
                    candidates.add(declaration.symbol_id)
        for expression in value.expressions:
            scan_expression(expression)
        for child in value.children:
            scan_statement(child)

    for statement in body:
        scan_statement(statement)
    return frozenset(candidates - written)


def _local_bound(value: TypedStatement, key: str,
                 float_bounded: dict[int, tuple[float, object]],
                 literal_locals: frozenset[int] = frozenset()
                 ) -> tuple[int, int, str, object] | None:
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
    if (literal is not None and declaration.symbol.storage == "local"
            and (declaration.symbol_id or 0) in literal_locals):
        return (declaration.symbol_id or 0, literal,
                "local-literal-never-rewritten", declaration.symbol)
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
                       lane_bounded: tuple[object, ...] = (),
                       tile_bounded: tuple[object, ...] = (),
                       literal_locals: frozenset[int] = frozenset()
                       ) -> tuple[TypedStatement, ...]:
    result: list[TypedStatement] = []
    active = dict(bounded)
    float_active: dict[int, tuple[float, object]] = {}
    for value in values:
        annotated = _annotate_statement(
            value, key, depth, ancestor_product, active, lane_bounded, tile_bounded,
            literal_locals)
        result.append(annotated)
        bound = _local_bound(annotated, key, float_active, literal_locals)
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
                        lane_bounded: tuple[object, ...] = (),
                        tile_bounded: tuple[object, ...] = (),
                        literal_locals: frozenset[int] = frozenset()
                        ) -> TypedStatement:
    if value.kind == "block":
        return replace(value, children=_annotate_sequence(
            value.children, key, depth, ancestor_product, bounded, lane_bounded,
            tile_bounded, literal_locals))
    if value.kind == "if":
        return replace(value, children=tuple(
            _annotate_statement(child, key, depth, ancestor_product,
                                dict(bounded), lane_bounded, tile_bounded,
                                literal_locals)
            for child in value.children))
    if value.kind != "for":
        return replace(value, children=tuple(
            _annotate_statement(child, key, depth, ancestor_product,
                                dict(bounded), lane_bounded, tile_bounded,
                                literal_locals)
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
        if start is None and tile_bounded:
            if any(seed.start_expression == declaration.children[0] for seed in tile_bounded):
                start = 0
    else:
        start = _integer_valued_float_literal(declaration.children[0])
    condition, update = value.expressions
    # A side-effect-free scalar comparison can only shorten a counted loop.
    # Keep the original conjunction in the IR and emitted loop. Use its left
    # comparison only to derive the upper bound. Calls, writes, disjunctions
    # and compound right operands remain outside this proof.
    if (condition.kind == "binary" and condition.operator == "&&"
            and len(condition.children) == 2):
        left, guard = condition.children
        if (guard.kind != "binary" or guard.operator not in {"<", "<=", ">", ">=", "==", "!="}
                or len(guard.children) != 2
                or any(node.kind not in {"id", "literal"}
                       or node.type.display() not in {"int", "uint", "float"}
                       for node in guard.children)):
            return value
        condition = left
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
        # Sound product bound: `A * B` where each factor is an int literal or
        # an id with a proved upper bound. A proved bound B on the runtime
        # value of the id makes B * |literal| a genuine upper bound on the
        # product, so the seed's own provenance carries over unchanged; a
        # non-positive literal factor only shortens the loop (the trip formula
        # clamps at 0). Anything else (an unbounded id, a float, another
        # operator) stays rejected -- fail closed.
        if bound is None and bound_expression.kind == "binary" \
                and bound_expression.operator == "*" and len(bound_expression.children) == 2:
            left, right = bound_expression.children
            factors = []
            for first, second in ((left, right), (right, left)):
                factor = _integer_literal(first)
                other = second
                if factor is not None and other.kind == "id" \
                        and other.symbol_id in bounded:
                    break
                factor = None
            if factor is not None:
                seed_bound, seed_kind, seed_symbol = bounded[other.symbol_id]
                if other.symbol != seed_symbol:
                    return value
                bound = _checked_mul(seed_bound, factor)
                bound_kind = seed_kind
                bound_symbol = seed_symbol
        if bound is None and bound_expression.kind == "swizzle" and lane_bounded:
            matches = tuple(seed for seed in lane_bounded
                            if seed.expression == bound_expression)
            if len(matches) == 1:
                seed = matches[0]
                child = bound_expression.children[0] if len(bound_expression.children) == 1 else None
                if (child is None or child.kind != "id"
                        or child.symbol_id != seed.symbol_id
                        or child.symbol != seed.symbol
                        or bound_expression.member != ("x" if seed.lane == 0 else "y")):
                    return value
                bound = seed.maximum
                bound_kind = seed.provenance
            elif len(matches) > 1:
                return value
        if bound is None and tile_bounded:
            matches = tuple(seed for seed in tile_bounded
                            if seed.start_expression == declaration.children[0]
                            and seed.end_expression == bound_expression)
            if len(matches) == 1:
                seed = matches[0]
                start = 0
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
        body, key, depth + 1, current_product, dict(bounded), lane_bounded,
        tile_bounded, literal_locals)
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
        runtime_tile_bounds: tuple[object, ...] = (),
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
    tile_identities = tuple((seed.start_symbol_id, seed.end_symbol_id, seed.lane)
                            for seed in runtime_tile_bounds)
    if len(set(tile_identities)) != len(tile_identities):
        raise ValueError(f"{key}: duplicate runtime tile counted-loop seed")
    initial_bounds.update(runtime_bounds)
    annotated = tuple(replace(function, body=_annotate_sequence(
        function.body, key, 0, 1, dict(initial_bounds), runtime_lane_bounds,
        runtime_tile_bounds, _never_rewritten_literal_locals(function.body)))
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
    expected = _source_global_profile(program.key, program.preprocessor_defines)
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
                             else runtime_contract.lane_seeds),
        runtime_tile_bounds=(() if runtime_contract is None
                             else runtime_contract.tile_seeds))
    return attached, summarize_counted_loop_proofs(attached)


def validate_source_global_literal_int_program(
        program: TypedProgram, profile: str | None) -> None:
    """Require the submitted Task 23 tree to equal independently rebuilt proof."""
    if program.key not in _SOURCE_GLOBAL_LITERAL_INT_PROFILES and profile is None:
        return
    attached, summary = rebuild_authenticated_counted_loop_proofs(program, profile)
    expected = _source_global_profile(program.key, program.preprocessor_defines)
    assert expected is not None
    if program.functions != attached or program.counted_loop_proof != summary:
        raise ValueError(f"{program.key}: source-global literal-int post-proof mismatch")
    if _sha(attached) != expected["post_functions"]:
        raise ValueError(f"{program.key}: source-global literal-int post-function profile mismatch")
    if _sha(_whole_program_identity(program, attached, summary)) != expected["post_whole"]:
        raise ValueError(f"{program.key}: source-global literal-int post-program profile mismatch")
