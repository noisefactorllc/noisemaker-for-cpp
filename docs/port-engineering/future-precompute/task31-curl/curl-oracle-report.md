# Task31 Curl tanh(vec3) + mod(vecN,float) closure oracle report

Eligible full-render cases: **6**; ineligible full-render cases: **3**; direct tanh rows: **10**; direct mod rows: **8**.

Authorized define map: `{"OCTAVES":1,"OUTPUT_MODE":3,"RIDGES":true}`.

## Critical correction to the design brief

The brief expected all three *reachable* sites to discriminate via full-render mutation, unlike the one genuinely dead site. Investigation (mandated by this task's instructions whenever a reachable site shows 0/N) found that the two `mod(vecN,float)` sites are **structurally immune** to a naive-fmod full-render mutation, for two distinct, independently-proven algebraic reasons -- NOT a coverage gap. See `program.closure_sites` and `risks_and_rejected_designs` in the JSON, and the module header in `curl_oracle_generator.mjs`, for the full proof. Both sites are confirmed genuinely live (executed on every pixel, output reaches the image) via a supplementary "wrong-divisor" mutation that DOES discriminate (40/40 in an ad-hoc randomized sweep; captured formally below as `reachability_proof_mutations`).

## Closure sites

| Site | AST id | Corpus loc | Reachable | Naive-fmod discriminates via full render |
| --- | --- | --- | --- | --- |
| tanh_vec3_main | 18 | 196:12 | true | true |
| mod_vec4_permute | 20 | 35:12 | true | false |
| mod_vec3_simplex3D | 21 | 65:9 | true | false |
| mod_vec3_permute_dead | 19 | 32:12 | false | false |

corpus id:line:col numbers are offset by exactly -10 lines from this raw curl.glsl (all four sites) due to preprocessor stripping of the header comment/#ifndef guard block (lines 1-23 raw vs. 13 effective) before AST parsing; verified by direct anchor match against the raw source and the pinned public factory text.

## Eligible full-render cases (authorized defines only)

| Case | Size | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- |
| default-seed0-time0 | 6x5 | `38fb7d9ac469347a5d53b1d065550cec64923b8f8ed9792bd62d11773c95bb55` | `74304e9ef0601a4886a053299a16246b57113f1584f451109fc4dbcc95a33da9` |
| seed7-tiled-midtime | 5x6 | `e6f49b49ebee9b4bec0631e7209f2daf70a207a8f8a659044a40f7db8388c92f` | `0b0aeb879b6461fa23d192882dcce8a4d484821d6f638a6d2868911ec95cc81a` |
| negative-seed-drives-negative-mod-operands | 8x3 | `6325f2198d92d04b02b6ff0b5f8102709f280c176d4a008dc5d0ddafa2c183d0` | `ff92d82a215c70ea490077f882e342d3ba92cc9ffec70a69d4c59d527228230b` |
| negative-intensity-flips-tanh-sign | 4x4 | `311e9b9662461dac97a4b9f5a167707913aec4120bb63b8b590376128b237fcd` | `df8c2c90ccf93aff72894448dbe5292ece5fd24f3f2ce21fb68f4e23a4001e8b` |
| large-seed-negative-scale-negative-speed | 7x7 | `aa573876f73366853d5898cb9a7e97f920dbae298f41f4ba0811d75b44e3991a` | `38983169f7e627250c60981b9fcfec851a56521e1679eceae2c3ae657b0c2fff` |
| two-pi-time-near-identity-intensity | 10x2 | `7a006260356fcf49ebcc27ca9069f37cfa7ee935d0d94e5d3ea2c9649befe95d` | `6d92a8ea911d0d96dad7f2d76f2647e8b612e645140157668298db20a9412d4b` |

## Ineligible full-render cases (define-eligibility risk demonstration)

| Case | Defines | F32 SHA-256 |
| --- | --- | --- |
| octaves-2-diverges-loop-unroll | {"OCTAVES":2,"OUTPUT_MODE":3,"RIDGES":true} | `119d8853b24e70d19d8cab6094e568edd53a98e805882e1661ba9bd3e06cb024` |
| output-mode-0-flowx-channel | {"OCTAVES":1,"OUTPUT_MODE":0,"RIDGES":true} | `c449eec20237293e0ef773a6a5dddaa91ed2911730088261a3f777d0ddc21c53` |
| ridges-false-no-fold | {"OCTAVES":1,"OUTPUT_MODE":3,"RIDGES":false} | `b7d0ad4f8cca9f6e9e93ecb4ddc6dc8ec8359de7ba03a05cb3c1b330ed7a15f4` |

## Public-factory mutations (the four brief-specified mutations)

| Mutation | Site | Reachable | Expected | Eligible divergent | Ineligible-diag divergent | Result |
| --- | --- | --- | --- | ---: | ---: | --- |
| tanh-vec3-identity-passthrough | tanh_vec3_main | true | nonzero | 5/6 | 3/3 | matches expectation (machine-asserted at build time) |
| mod-vec4-permute-naive-fmod | mod_vec4_permute | true | zero-structural-invariant | 0/6 | 0/3 | matches expectation (machine-asserted at build time) |
| mod-vec3-simplex3D-naive-fmod | mod_vec3_simplex3D | true | zero-structural-invariant | 0/6 | 0/3 | matches expectation (machine-asserted at build time) |
| mod-vec3-permute-dead-naive-fmod | mod_vec3_permute_dead | false | zero-dead-code | 0/6 | 0/3 | matches expectation (machine-asserted at build time) |

Expectation legend: `nonzero` = must discriminate (genuine surprise if 0/N). `zero-structural-invariant` = reachable, executed on every pixel, but PROVABLY immune to this specific rounding-rule mutation (see proof in module header / `program.closure_sites`); a nonzero result here would be the surprise. `zero-dead-code` = never called at all, at any define map; 0/N for an entirely different reason than the structural-invariant sites.

## Reachability-proof mutations (supplementary, not the four primary mutations)

| Mutation | Site | Eligible divergent | Purpose |
| --- | --- | ---: | --- |
| mod-vec4-permute-wrong-divisor | mod_vec4_permute | 6/6 | supplementary -- proves the site is live/executed/influences output; NOT one of the four brief-specified mutations |
| mod-vec3-simplex3D-wrong-divisor | mod_vec3_simplex3D | 6/6 | supplementary -- proves the site is live/executed/influences output; NOT one of the four brief-specified mutations |

These wrong-divisor (288 instead of 289) mutations break both structural invariants and are machine-asserted to diverge on every eligible case -- proof the two mod sites above are genuinely live and their output reaches the rendered image; the naive-fmod 0/N above is specific to that one rounding-rule difference, not to the sites being inert.

## Direct tanh(vec3) rows (real runtime `stdlib.tanh`, not reimplemented)

| Input | Input bits | Result | Result bits |
| --- | --- | --- | --- |
| [0,0,0] | 0x00000000, 0x00000000, 0x00000000 | [0,0,0] | 0x00000000, 0x00000000, 0x00000000 |
| [0,0,0] | 0x80000000, 0x00000000, 0x00000000 | [0,0,0] | 0x80000000, 0x00000000, 0x00000000 |
| [1,-1,0.5] | 0x3f800000, 0xbf800000, 0x3f000000 | [0.7615941762924194,-0.7615941762924194,0.46211716532707214] | 0x3f42f7d6, 0xbf42f7d6, 0x3eec9a9f |
| [-1,1,-0.5] | 0xbf800000, 0x3f800000, 0xbf000000 | [-0.7615941762924194,0.7615941762924194,-0.46211716532707214] | 0xbf42f7d6, 0x3f42f7d6, 0xbeec9a9f |
| [3.4028234663852886e+38,-3.4028234663852886e+38,0] | 0x7f7fffff, 0xff7fffff, 0x00000000 | [1,-1,0] | 0x3f800000, 0xbf800000, 0x00000000 |
| [-3.4028234663852886e+38,3.4028234663852886e+38,3.4028234663852886e+38] | 0xff7fffff, 0x7f7fffff, 0x7f7fffff | [-1,1,1] | 0xbf800000, 0x3f800000, 0x3f800000 |
| [1.401298464324817e-45,-1.401298464324817e-45,0] | 0x00000001, 0x80000001, 0x00000000 | [1.401298464324817e-45,-1.401298464324817e-45,0] | 0x00000001, 0x80000001, 0x00000000 |
| [20,-20,0.00009999999747378752] | 0x41a00000, 0xc1a00000, 0x38d1b717 | [1,-1,0.00009999999747378752] | 0x3f800000, 0xbf800000, 0x38d1b717 |
| [3.141590118408203,-3.141590118408203,2.718280076980591] | 0x40490fd0, 0xc0490fd0, 0x402df84d | [0.996272087097168,-0.996272087097168,0.9913288950920105] | 0x3f7f0bb0, 0xbf7f0bb0, 0x3f7dc7bb |
| [1.000000013351432e-10,-1.000000013351432e-10,0] | 0x2edbe6ff, 0xaedbe6ff, 0x00000000 | [1.000000013351432e-10,-1.000000013351432e-10,0] | 0x2edbe6ff, 0xaedbe6ff, 0x00000000 |

## Direct mod(vecN, 289.0) rows (real runtime `stdlib.mod` vs. naive JS `%` fmod stand-in) -- AUTHORITATIVE closure-parity surface for the naive-fmod hazard

Note: `JSON.stringify(-0)` renders as `0` with the sign lost, so the `x bits` / `naive bits` columns (not the plain-value columns) are what actually distinguish +0.0 from -0.0 rows below.

| x | x bits | GLSL mod result | Naive fmod result | Naive bits | Diverges |
| --- | --- | --- | --- | --- | --- |
| [0,0,0,0] | 0x00000000, 0x00000000, 0x00000000, 0x00000000 | [0,0,0,0] | [0,0,0,0] | 0x00000000, 0x00000000, 0x00000000, 0x00000000 | false |
| [0,0,0,0] | 0x80000000, 0x00000000, 0x00000000, 0x00000000 | [0,0,0,0] | [0,0,0,0] | 0x80000000, 0x00000000, 0x00000000, 0x00000000 | true |
| [289,-289,578,-578] | 0x43908000, 0xc3908000, 0x44108000, 0xc4108000 | [0,0,0,0] | [0,0,0,0] | 0x00000000, 0x80000000, 0x00000000, 0x80000000 | true |
| [-1,-0.5,-289,-289] | 0xbf800000, 0xbf000000, 0xc3908000, 0xc3908000 | [288,288.5,0,0] | [-1,-0.5,0,0] | 0xbf800000, 0xbf000000, 0x80000000, 0x80000000 | true |
| [1,0.5,289,289] | 0x3f800000, 0x3f000000, 0x43908000, 0x43908000 | [1,0.5,0,0] | [1,0.5,0,0] | 0x3f800000, 0x3f000000, 0x00000000, 0x00000000 | false |
| [-59500,59500,-1,1] | 0xc7686c00, 0x47686c00, 0xbf800000, 0x3f800000 | [34,255,288,1] | [-255,255,-1,1] | 0xc37f0000, 0x437f0000, 0xbf800000, 0x3f800000 | true |
| [3.4028234663852886e+38,-3.4028234663852886e+38,1.401298464324817e-45,-1.401298464324817e-45] | 0x7f7fffff, 0xff7fffff, 0x00000001, 0x80000001 | [0,0,1.401298464324817e-45,289] | [187,-187,1.401298464324817e-45,-1.401298464324817e-45] | 0x433b0000, 0xc33b0000, 0x00000001, 0x80000001 | true |
| [-100000000,100000000,-0.12710000574588776,0.12710000574588776] | 0xccbebc20, 0x4cbebc20, 0xbe022681, 0x3e022681 | [69,220,288.8728942871094,0.12710000574588776] | [-220,220,-0.12710000574588776,0.12710000574588776] | 0xc35c0000, 0x435c0000, 0xbe022681, 0x3e022681 | true |

Every row with at least one negative lane is machine-asserted (at build time) to include at least one row where GLSL `mod` and naive `fmod`/`%` diverge -- this is the exact bug shape a C++ port using `std::fmod` instead of implementing `x - y*floor(x/y)` would exhibit. Because full-render cannot observe this hazard at either reachable mod site (see above), THESE direct rows -- not the full-render mutations -- are what a native test suite must bind against to catch a naive-fmod regression. The `[-0,0,0,0]` row additionally freezes a distinct hazard: GLSL's arithmetic mod formula collapses -0.0 to signless +0.0 (0x00000000), while naive JS `%` PRESERVES the -0.0 sign bit (0x80000000) -- so even the "does mod(-0, y) equal mod(0, y))" question has a naive-fmod-vs-GLSL-mod answer that differs at the bit level.

## Risks and rejected designs

- **brief-full-render-discrimination-expectation-corrected** (flag-for-operator-signoff): The design brief expected all 3 reachable sites to discriminate via full-render mutation, unlike the one dead site. Empirically (40-trial randomized stress sweep, seed in [-1e6,1e6]) and algebraically (see module header), the two reachable mod(vecN,float) sites are structurally IMMUNE to a naive-fmod full-render mutation -- for two distinct, independently-verified reasons (quadratic dominance at permute_vec4, period-289 absorption at simplex3D). Both sites are proven live via a supplementary wrong-divisor mutation (40/40 divergent). Direct component-level invocation of the real runtime mod() (direct_mod_rows) is therefore the authoritative surface for this hazard, not full-render diffing.

