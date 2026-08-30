# Cheap-unlocks cluster 2 -- `synth/bitwise:bitwise` oracle report

Hermetic JS oracle for the one program in the corpus blocked purely on bitwise operators. Ground truth for the future C++20 port's bit-exact parity tests.

Total cases: **6** (5 closure-exercising + 1 structural-negative-control diagnostic).

## Defines axis

synth/bitwise:bitwise authorizes the empty define map {} -- confirmed live via tools.glslcpp.generate_typed_slice._defaults(repo, 'synth/bitwise:bitwise') -> {} in this session, and independently by reading the source: bitwise.glsl has NO preprocessor directive at all (starts `#version 300 es` directly, no #ifdef/#define anywhere). The defines-as-uniforms hazard from the grade/derivative clusters cannot arise here.

## Shift-semantics finding (load-bearing)

**Claim**: synth/bitwise:bitwise has ZERO shift-operator (<<, >>) sites -- the bitops-precompute.md headline "JS emits signed >> for uint>>uint" hazard does NOT apply to this program.

**Evidence**:

- grep -n '<<\\|>>' sources/synth/bitwise/bitwise.glsl -- zero matches across all 90 lines of the pinned corpus source (verified live in this session).
- canonicalFactory244's compiled JS body (the actual JS-golden reference this oracle freezes) contains no '<<' or '>>' substring anywhere -- verified live via a regex scan of canonical.toString() in loadProgram(), which throws if this claim is ever wrong.
- bitOp() contains only r = a^b, r = a&b, r = a|b, r = ~(a&b), r = ~(a^b) (plus the pre-existing *; +; - arithmetic branches, already admitted); main() has two more scalar ^ sites (x ^= seed; y ^= seed*3) and nothing else touches a bit operator.

**Consequence**: This program's entire new-capability surface is scalar signed-int &, |, ^, unary ~ (and their op=3/op=4 nand/xnor combinations) -- governed only by bitops-precompute.md Hazard #2 (JS ToInt32-based bitwise ops already match C++20 two's-complement int32_t bit-for-bit) and NOT Hazard #1 (signed-vs-logical shift) or Hazard #3 (shift-count masking), both of which are structurally inapplicable: there is no shift op, so there is no shift semantics to get wrong and no shift count to mask. Stated explicitly rather than fabricating a shift test this program's compiled JS does not exercise.

## High-bit-operand confirmation

Every non-diagnostic case supplies at least one operand with the int32 sign bit set: mask values at/near INT32_MIN/INT32_MAX or with only bit 31 set (-2147483648, 2147483647, -65536, -3), and/or seed/offset values at or near INT32_MIN/INT32_MAX (-1, -2000000000, 2147483647, +-1500000000/+-2000000000) that XOR directly into the per-pixel integer coordinates before every bitOp() call. This matches the discriminating-test intent stated for the shift hazard (operands with the high bit set), applied here to the hazard that actually governs this program: a naive reimplementation that widens to float, or uses unsigned-only arithmetic, or gets two's-complement NOT wrong would diverge on exactly these operands while a small-positive-only suite would never catch it.

## Cases

| Case | Size | Op | ColorMode | Diagnostic | Nonfinite lanes | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | ---: | --- | ---: | --- | --- |
| xor-mono-seed-negative-one-signbit-mask | 6x5 | xor | 0 | false | 0 | `6b974a31a2eb50d7...` | `a867f774a9b52de6...` |
| and-rgb-int32min-offsets-near-max-mask | 5x6 | and | 1 | false | 0 | `35d4755eb6b88c0a...` | `02bc6717b1256d97...` |
| or-hsv-negative-offsets-large-seed | 7x4 | or | 2 | false | 0 | `9a7907811e4db580...` | `03fe3364206e61a0...` |
| nand-mono-int32-extremes-tiled | 4x7 | nand | 0 | false | 0 | `18df6df90284225e...` | `d583aef59874543a...` |
| xnor-rgb-high-bit-mixed-signs | 6x6 | xnor | 1 | false | 0 | `5ab11529ca24e34b...` | `218be6c5703006d7...` |
| mask-zero-divide-by-zero-diagnostic | 3x3 | xor | 0 | true | 27 | arm64 `720415a4af3de87c...`<br>x64 `72f71c0a368a60c1...` | `d574fbbbc44a56d8...` |

## Mutations

| Mutation | Op | Reaching | Divergent (reaching) | Non-reaching | Divergent (non-reaching) |
| --- | --- | ---: | ---: | ---: | ---: |
| bitwise-xor-and-confusion | xor | 1 | 1 | 5 | 0 |
| bitwise-and-or-confusion | and | 1 | 1 | 5 | 0 |
| bitwise-or-xor-confusion | or | 1 | 1 | 5 | 0 |
| bitwise-nand-nor-confusion | nand | 1 | 1 | 5 | 0 |
| bitwise-xnor-nand-confusion | xnor | 1 | 1 | 5 | 0 |

- **bitwise-xor-and-confusion**: op=0 (xor) mutated to `a & b` -- the classic XOR/AND confusion bug.
- **bitwise-and-or-confusion**: op=1 (and) mutated to `a | b` -- the classic AND/OR confusion bug.
- **bitwise-or-xor-confusion**: op=2 (or) mutated to `a ^ b` -- OR/XOR confusion, plausible when an implementer conflates "combine" operators.
- **bitwise-nand-nor-confusion**: op=3 (nand) mutated to `~(a | b)` (nor) -- the classic NAND/NOR confusion, and exercises the unary ~ interacting with a differently-computed pre-image, per the task's ~(a&b)/~(a^b) discriminating-test callout.
- **bitwise-xnor-nand-confusion**: op=4 (xnor) mutated to `~(a & b)` (nand) -- XNOR/NAND confusion, same unary-~ interaction as above for the other combinator pair.

## Negative closure

- **shift_semantics_test_fabricated**: refused -- loadProgram() asserts, live, that neither the pinned source nor the compiled factory text contains a shift operator; a shift-count-masking test was not constructed because there is no shift to test. See shift_semantics_finding.
- **small_positive_only_operands_used**: refused -- see high_bit_operand_confirmation; every non-diagnostic case has at least one sign-bit-set operand.
- **mask_zero_case_silently_dropped**: refused -- included, documented as a structural (not coverage-gap) zero-reach case for every operator mutation, with its own independent NaN-propagation assertion in the render output.
- **mul_add_sub_ops_covered**: not applicable -- op=5/6/7 (mul/add/sub) are pre-existing, already-admitted int arithmetic, not part of this unlock; out of scope for this oracle by design.

