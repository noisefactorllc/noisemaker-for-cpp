# Task31 Caustic floatBitsToUint + scalar uint XOR closure oracle report

Eligible full-render cases: **6**; ineligible full-render cases: **3**; direct closure-probe cases: **8** (all eligible); direct scalar rows: **12**.

## Critical correction to the design brief

The brief's Oracle Requirements section claims the XOR closure is "live, reachable, rendered code" at NOISE_TYPE=10, unlike Perlin's dead-code XORs. This is **contradicted** by direct, reproducible evidence: static call-graph analysis via `tools.glslcpp.generate_typed_slice` shows `randomFromLatticeWithOffset` is unreachable from `main()` at the one authorized define map `{"NOISE_TYPE": 10}` (only `simplexValue` is called), and dynamic mutation testing against the real, hash-pinned JS reference confirms zero output divergence for all 4 structural mutations across every eligible full-render case. See `program.reachability_finding` in the JSON for full evidence. This oracle uses direct invocation of the byte-for-byte-extracted public factory function as the authoritative closure-parity surface instead.

## Eligible full-render cases (NOISE_TYPE=10 only)

| Case | Size | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- |
| simplex-default-seed44 | 6x5 | `439bc0ab9c741bef0190b9bd9ab802644fa3d117eb60b830572343123fed9be2` | `54a0a2fb520578917435bd4312dc8af39ea0584f3d92d1c9176fe2a3c2f3fd85` |
| simplex-seed-zero-nowrap | 7x4 | `1a59b36b792ac130eec49bfc910f58099031f16d532018f7e1c16fbe640bebb4` | `c7d1dd8abae53d951910bcc0eb1c7cb5eb59dbcd952b7340c2e075ee5534eba8` |
| simplex-large-seed-tiled | 5x7 | `a389f7860dbcd2f5da1daa7de559afc4a10cebe5014bd794a67722a4f6ad8e85` | `7c6c9033558930821daf5fdb6eae35a32f14e90887df2a2e43d7a913cdee4638` |
| simplex-negative-intensity-full-hue | 8x3 | `17d58c1c11dd4a4775de0a52b21f4cb4b28e9961456aea5e305ca48c78d607c9` | `d52c2ac9fe2f27c2c08c17af9e24c08ca3772048c38e54cc7e2d480506729248` |
| simplex-min-scale-zero-speed | 4x4 | `2a18955e6761b3858ca5a68698aef270adf6129339532b86e2f6791edd5d66ab` | `cca8adddd7713c1a5aa46e309a1536d3f65b28b370a2b4a1169e883a42cc3f5a` |
| simplex-max-scale-large-canvas | 10x6 | `4b9128eb902d74d0c13e4fd44cd0a3c7a24edbbde129721b69cc3346be79ab19` | `57714528081646c2e13253cd995151f9d339b317403cb9bf438860c35a6fb802` |

## Ineligible full-render cases (define-eligibility risk demonstration)

| Case | Defines | closure_reachable | F32 SHA-256 |
| --- | --- | --- | --- |
| value-constant-interp0 | {"NOISE_TYPE":0} | true | `70a84c7d97568d35b36c6dae3732804ee0087a5c5230aada4263381d43764905` |
| value-linear-interp1 | {"NOISE_TYPE":1} | true | `d6c6dd7511ebc91826e21784eadf572831963a0df5ba9f3db356885f1264acb7` |
| sine-interp11 | {"NOISE_TYPE":11} | false | `edc797a7b21f907514d9d67f76bed6cee3a3ae1e091d7dd8a68328919da4699e` |

## Direct closure-probe cases (authoritative closure parity surface)

| Case | s | seedFrac | fracBits | result bits |
| --- | --- | --- | --- | --- |
| baseline-integer-seed-matches-full-render | 44 | 0 | 0x00000000 | 0x3eccc2e0, 0x3ebd974f, 0x3f14a6ab |
| fractional-seed-simple-half | 44.5 | 0.5 | 0x3f000000 | 0x3f081672, 0x3f0d937e, 0x3e6ee8ea |
| fractional-seed-float32-rounding-boundary | 44.1 | 0.10000000149011612 | 0x3dcccccd | 0x3ecac24f, 0x3e3ad5cb, 0x3e9e0bbb |
| negative-fractional-seed | -0.5 | 0.5 | 0x3f000000 | 0x3f0f19c1, 0x3f058f80, 0x3e56275a |
| near-one-fractional-seed-no-wrap | 100.999999 | 0.9999989867210388 | 0x3f7fffef | 0x3f4a77c1, 0x3f748791, 0x3f2bf1b3 |
| small-fractional-seed-large-offset | 7.000123 | 0.0001230000052601099 | 0x3900f990 | 0x3f35f9ec, 0x3f04bf02, 0x3f1ae99d |
| one-third-fractional-seed | 12.333333333333334 | 0.3333333432674408 | 0x3eaaaaab | 0x3d2f9b40, 0x3f59064d, 0x3e039b14 |
| wrap-toggle-otherwise-identical | 7.000123 | 0.0001230000052601099 | 0x3900f990 | 0x3f0b49f2, 0x3f6e1bc8, 0x3f0fbbab |

## Direct closure mutations (discriminate via non-integer s)

| Mutation | Discriminating cases |
| --- | ---: |
| floatbits-to-numeric-uint-conversion | 7/8 |
| xor-site-1-to-add | 7/8 |
| xor-site-2-to-or | 7/8 |
| xor-site-3-to-and | 8/8 |

## Full-render mutations (structurally non-discriminating at NOISE_TYPE=10, confirming dead code)

| Mutation | Eligible (NOISE_TYPE=10) divergent | Ineligible diagnostic divergent |
| --- | ---: | ---: |
| floatbits-to-numeric-uint-conversion | 0/6 | 0/3 |
| xor-site-1-to-add | 0/6 | 0/3 |
| xor-site-2-to-or | 0/6 | 0/3 |
| xor-site-3-to-and | 0/6 | 2/3 |

All 0/N eligible-case rows above are EXPECTED and machine-asserted (see `buildFullRenderMutations` in the generator) -- they demonstrate dead code, not a failed mutation design. All direct-closure-mutation rows are >0/N by construction (asserted at build time); a 0/N row there would abort generation.

## Risks and rejected designs

- **nan-bit-pattern-cross-engine-parity** (flag-for-operator-signoff): GLSL NaN bit-pattern behavior is implementation-defined. This oracle pins the exact bit pattern V8/Node produces for a plain `NaN` double routed through floatBitsToUint (Float32Array/Uint32Array alias): direct_scalar_rows entry with seedFrac_double_repr="NaN" freezes fracBits_hex=0x7fc00000 (a canonical quiet NaN, sign=0, all-mantissa-MSB-set). A C++ static_cast<double,NaN> -> float -> std::bit_cast<uint32_t> is NOT guaranteed to reproduce this exact payload/quiet-bit pattern on every platform/compiler. This is not exercised by any legitimate uniform-driven call path in this program (seedFrac is always fract() of a finite value in every real caller), so it is LOW practical risk for Caustic specifically, but is frozen here and flagged per the brief's explicit request rather than silently assumed to match.

- **xor-operand-order-swap-rejected** (rejected-non-discriminating): The brief suggests "swapping operand order where that changes results" as an XOR-site mutation. Rejected: binary ^ is commutative, so swapping (cpu_umul(fracBits, K) ^ MAGIC) to (MAGIC ^ cpu_umul(fracBits, K)) produces bit-identical results for every input -- a mutation that diverges in 0 cases by construction, exactly the Task 30 "useless mutation" trap. Replaced with genuinely non-commutative-preserving operator swaps (+, |, &) that do discriminate, verified per-case above.

- **plus-or-mutations-non-discriminating-at-any-full-render-uniform** (documented-not-a-flaw): The xor-site-1-to-add and xor-site-2-to-or mutations never discriminate via ANY full-kernel render (eligible or not), because 0 is the identity element for + and | and seedFrac is always exactly 0.0 on every legitimate call path (uniform int seed). This is not a defect in the mutation choice -- it is a genuine property of this program's uniform surface, independently confirmed by the AND mutation (0 & X = 0 != X = 0 ^ X) discriminating at the same reachable-but-ineligible NOISE_TYPE values where + and | do not. All four mutations DO discriminate via the direct-closure-probe surface, which is not restricted to integer s.

