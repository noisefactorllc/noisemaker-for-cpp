# Signed-arithmetic shift primitive: design and empirical verification

All work for this task was done under
`docs/port-engineering/shift-primitive/`. Nothing under
`.` or
`../noisemaker-for-cpu` was modified; both trees were
only read. No `git` command was run anywhere. Files depended on from those
trees were snapshotted (see "Sources read" below) because another agent is
actively editing the generator Python and could change them out from under
this analysis.

Toolchain: `clang++`/`g++` both resolve to Apple clang 16.0.0
(arm64-apple-darwin23.6.0) on this machine — see "What I could not verify"
for the portability implication. Node v24.7.0. All C++ built with the
mandated flags: `-std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off`,
zero warnings, zero errors, at every build in this task.

## 1. Verified JS semantics table

Produced by `probe_semantics.mjs` (run: `node probe_semantics.mjs >
probe_semantics_output.json`), which evaluates `>>`, `>>>`, `<<`, `&`, `|`,
`^`, `~` across negative values, values with the high bit set, values
≥2^31, values ≥2^32, non-integer inputs, and shift counts of
{0,1,15,16,31,32,33,63,64,-1,-31,-32,-33,1000000} and non-integer/huge
shift counts. Nothing below is asserted from memory; every cell is an
actual recorded Node v24.7.0 result.

**Right shift, `INT32_MIN` (`0x80000000`), by shift count `s`:**

| `s` | `v >> s` (signed) | `v >>> s` (unsigned) |
|---:|---|---|
| 0 | `0x80000000` | `0x80000000` |
| 1 | `0xc0000000` | `0x40000000` |
| 15 | `0xffff0000` | `0x00010000` |
| 16 | `0xffff8000` | `0x00008000` |
| 31 | `0xffffffff` | `0x00000001` |
| 32 | `0x80000000` (= s mod 32 = 0) | `0x80000000` |
| 33 | `0xc0000000` (= s mod 32 = 1) | `0x40000000` |

This is the load-bearing fact: JS's `>>` on a value with bit 31 set
sign-extends (fills with 1s), while `>>>` zero-fills. They diverge on
every such value at every nonzero shift count — this is exactly the
~50%-of-hash-outputs divergence `bitops-precompute.md` Hazard #1 describes.

**Shift-count masking (Section D of the probe):** for 5 representative
values (`1`, `-1`, `INT32_MAX`, `INT32_MIN`, `0x12345678`) and shift counts
swept from **-70 to 130**, `v >> s`, `v >>> s`, and `v << s` were each
compared against `v OP (((s % 32) + 32) % 32)` (i.e. `s` reduced mod 32
into `[0,32)`). **Zero mismatches found** across all 5×201×3 = 3015
comparisons — confirms JS's implicit `ToUint32(s) & 0x1F` shift-count
reduction empirically, including for negative `s` and `s` far outside
`[0,32)`.

**Non-integer / out-of-range operand coercion** (Section B, spot-checked,
all ToInt32/ToUint32-consistent — truncation is *toward zero*, not floor):

| expr | value | result |
|---|---|---|
| `3.7 >> 0` | truncates to 3 | `3` |
| `-3.7 >> 0` | truncates to -3 (toward zero, not -4) | `-3` |
| `-3.7 >>> 0` | | `4294967293` |
| `1e20 >> 0` | wraps mod 2^32 after truncation | `1661992960` |
| `NaN >> 0`, `Infinity >> 0` | ToInt32(NaN/Infinity) = 0 | `0` |
| `1 >> 2.9` (shift count) | ToUint32(2.9)=2, truncated toward zero | `1>>2 = 0` |
| `-1 >> -2.9` (shift count) | ToUint32(-2.9)=ToUint32(-2)=4294967294, `&31`=30 | `-1` (all-ones stays -1 at any shift ≤31) |

**Binary ops** (`&`,`|`,`^`) on adversarial pairs (both negative, both
high-bit-set, mixed) all behaved as plain two's-complement 32-bit
operations with no surprises — see `probe_semantics_output.json` section
C for the full pair list and results (13 pairs × 3 ops = 39 recorded
cases, all consistent with plain int32/uint32 bitwise arithmetic).

## 2. C++ expression per operator/signedness, and why the naive one is not what ships

| JS op | C++ expression that reproduces it bit-for-bit | Verified how |
|---|---|---|
| `v >>> s` (logical) | `static_cast<uint32_t>(v) >> (s & 31U)` | `verify_sweep.cpp` "uint32_t logical >>" column: 3,206,592/3,206,592 exact |
| `v << s` | `bit_cast<int32_t>(bit_cast<uint32_t>(v) << (s & 31U))` (unsigned domain throughout) | `verify_sweep.cpp` "shift_left" column: 3,206,592/3,206,592 exact |
| `a & b`, `a \| b`, `~a` | plain `int32_t`/`uint32_t` `&`/`\|`/`~` | `probe_semantics.mjs` Section C (spot-check); relied on for Hazard #2, corroborated by this codebase's already-shipped `bitwise_xor` |
| **`v >> s` (arithmetic/signed) — THE target** | **NOT** the naive `value >> masked` on `int32_t` by assumption — see below | `verify_sweep.cpp`, all 5 columns, see §4 |

**On the naive expression specifically:** C++20 mandates two's-complement
representation ([basic.fundamental]) and — per P0907R4 — gives
left-shift of a negative signed operand well-defined behavior. Whether
**right**-shift of a negative signed operand is *also* fully
well-defined (sign-propagating) in C++20, or still implementation-defined,
was flagged by this task as something to verify rather than assume. I did
not re-derive the exact current standard wording in this session (no
network access used); instead I **verified empirically** (`verify_sweep.cpp`,
"naive `value >> masked` on int32_t" column) that on this exact toolchain
(Apple clang 16, arm64) plain `value >> masked` on `std::int32_t` matches
the JS arithmetic-shift oracle bit-for-bit across the full sweep (3,206,592/
3,206,592 exact, 0 divergent). That is a real, positive data point for
*this* compiler, but the shipped primitive (§3) deliberately does not
depend on it — see the portability discussion in §5.

## 3. Recommended primitive

```cpp
// noisemaker::glsl namespace, matching existing house style
[[nodiscard]] constexpr std::int32_t shift_right_arithmetic(
    std::int32_t value, std::uint32_t amount) noexcept;

[[nodiscard]] constexpr std::uint32_t shift_right_arithmetic(
    std::uint32_t value, std::uint32_t amount) noexcept;  // overload
```

Full implementation, doc comments, and 4 small companion operators
(`bitwise_and`, `bitwise_or`, `bitwise_not`, `shift_left` — needed by the
same Task N+3 program family, verified via Hazard #2) are in
`shift_primitive.hpp`.

### New primitive, not a parameter on `shift_right` — reasoning

The existing `glsl::shift_right` (`include/noisemaker/glsl_types.hpp:196-204`)
is `Vec<N,uint32_t> shift_right(Vec<N,uint32_t> value, uint32_t amount)` —
**logical shift, `uint32_t`-typed, and must keep working unchanged**: it is
the correct, already-verified-against-131-shipped-programs lowering for the
canonical `pcg3d` idiom (the *only* idiom glsl-transpiler special-cases to
emit JS `>>>`, per `glsl-runtime.js:23-38`).

I recommend a **separately-named** primitive (`shift_right_arithmetic`)
rather than adding a `bool`/enum parameter to `shift_right`, for three
reasons:

1. **The two operations are not the same operation with a flag — they are
   defined on different representations.** Logical shift is meaningful on
   an unsigned bit pattern with no reference to sign. Arithmetic shift is
   *defined by* the operand's signed interpretation (it exists to
   preserve sign under shifting). A single function that takes a
   `uint32_t` and a `bool signed_shift` flag would be lying about its own
   domain — the "signed" case has to reinterpret the bits as `int32_t`
   internally regardless, so the type-level distinction is real, not
   decorative.
2. **Hazard #1's own finding is that this determination is per call
   site, driven by which JS idiom the transpiler recognized — never
   inferable from the GLSL operand's declared type.** A future implementer
   choosing which primitive to call for a new frontier program must
   re-derive the emitted JS for that exact call site (per
   `bitops-precompute.md`, "must be re-verified by reading the actual
   emitted JS for each new program before choosing which shift semantics
   to lower it to"). A **different function name** makes an accidental
   wrong choice a visible, greppable, compile-time fact (call site says
   `shift_right` when it should say `shift_right_arithmetic`, or vice
   versa) — exactly the class of mistake this task's own negative-control
   experiment (§4) demonstrates costs 87.5% of outputs. A boolean argument
   flipped at one of dozens of call sites is far easier to get wrong
   silently and far harder to `grep` for during review.
3. **The already-shipped call sites of `shift_right` must never change
   shape.** Adding a parameter — even a defaulted one — to a function that
   131 shipped programs' generated C++ already calls is exactly the kind
   of "regressive" surface-area change the project's fix-forward
   discipline warns against touching without necessity. A new, additive
   function has zero blast radius on existing emission.

The `uint32_t` overload exists because several frontier call sites
(`filter/median`'s `packedRg`, `filter/spookyTicker`'s `hash_mix` `v`,
`filter/osd`'s local `pcg` `state`) are GLSL-`uint`-typed but still need
arithmetic shift semantics per Hazard #1 — the overload lets such call
sites avoid an explicit cast at every use while remaining visibly a
different *name* than `shift_right`.

### Portability design of the implementation itself

`shift_right_arithmetic` does **not** write `value >> masked` on a
possibly-negative `int32_t`, even though §2 found that expression matches
JS on this toolchain. It instead derives the arithmetic-shift bit pattern
using only C++20 operations that are unconditionally well-defined for
every `int32_t` value regardless of toolchain: `std::bit_cast` to
`uint32_t` (defined given C++20's mandated two's-complement layout), an
unsigned logical `>>` (always well-defined), and an explicit sign-fill
built from an unsigned `<<` (well-defined for every masked count in
`[0,31]`, with the `masked == 0` case special-cased to avoid a would-be
`<< 32`, which is UB even in the unsigned domain). This makes the shipped
primitive's correctness independent of whichever way C++20 committee
prose ultimately resolved right-shift-of-negative — see §5 for why this
matters given only one toolchain was available to test here.

## 4. Sweep verification results

**Shared value population** (`gen_values.mjs` → `values.txt`, 100,206
values, one shared file so JS and C++ are guaranteed to test identical
inputs): 206 curated adversarial values (every power of two and
power-of-two-minus-one for k=0..31, both signs, ±1 of each boundary,
`INT32_MIN`/`MAX`, and 8 real hash constants seen in the frontier programs
e.g. `0x9E3779B9`) + 100,000 pseudorandom `int32_t` values from a
fixed-seed (`0xC0FFEE`) `mulberry32` PRNG, reproducible bit-for-bit on
rerun.

**Main sweep** (`gen_oracle.mjs` → `sweep_oracle.csv`, 130 MB, 3,206,592
rows = 100,206 values × 32 canonical shift amounts 0..31 — the amounts
≥32/negative case is separately covered by the masking proof in §1 and the
edge-amount sweep below, so this is the non-redundant part of the full
range): `verify_sweep.cpp`, built with the mandated flags, zero warnings:

| Column | N compared | N exact | N divergent |
|---|---:|---:|---:|
| **`shift_right_arithmetic(int32_t, uint32_t)` — THE PRIMITIVE** | 3,206,592 | 3,206,592 | **0** |
| `shift_right_arithmetic(uint32_t, uint32_t)` overload | 3,206,592 | 3,206,592 | **0** |
| naive `value >> masked` on int32_t (toolchain check) | 3,206,592 | 3,206,592 | **0** |
| `uint32_t` logical `>>` (corroborates `>>>` mapping) | 3,206,592 | 3,206,592 | **0** |
| `shift_left` (bonus primitive) | 3,206,592 | 3,206,592 | **0** |

Total: **16,032,960 comparisons, 16,032,960 exact, 0 divergent**, across 5
independently-checked columns.

**Edge-amount sweep** (`gen_edge_amounts.mjs` → `edge_amounts_oracle.csv`,
1,236 rows = 206 curated values × 6 out-of-canonical-range-but-`uint32_t`-
representable amounts `{32, 33, 63, 64, 1000000, 4294967295}`):
`verify_edge_amounts.cpp` — **N compared=1236, N exact=1236, N
divergent=0.**

Grand total across both sweeps: **16,034,196 compared / 16,034,196 exact /
0 divergent.**

## 5. Real-program cross-check

Target: `filter/spookyTicker`'s `hash_mix`, extracted verbatim from
**currently-live** shipped JS at
`../noisemaker-for-cpu/src/effects/generated/canonical-kernels.js:19970-19976`
(inside `canonicalFactory147`, lines 19948-20030+ snapshotted to
`real-program-crosscheck/snapshot_canonicalFactory147.js.excerpt`; full
source file sha256 recorded in
`real-program-crosscheck/canonical_kernels_source.sha256` =
`e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`, so this
snapshot is checkable against the live tree even if the other agent's
generator-Python edits later regenerate this file):

```js
function hash_mix (v) {
	v = v ^ (v >> 16);
	v = cpu_umul(v, 2146121005);
	v = v ^ (v >> 15);
	v = cpu_umul(v, 2221713035);
	v = v ^ (v >> 16);
	return v;
};
```

`cpu_umul` = `$runtime.stdlib.umul` = `(left,right) => Math.imul(left,right)
>>> 0` (`noisemaker-for-cpu/src/csl/glsl-runtime.js:319`). This is the same
function `bitops-precompute.md`'s Hazard #1 cites directly ("canonical-
kernels.js:19971,19973,19975 ... all plain `>>`"), confirming it as one of
the bespoke, non-canonical-idiom hash helpers that needs the new
arithmetic-shift primitive.

**Reference (JS):** `real-program-crosscheck/hash_mix_reference.mjs` —
byte-for-byte copy of the two functions above, run over the same
100,206-value shared population (each value passed through `|0` first,
mirroring every real call site: `(rowSeed|0) ^ 17`, `(seed|0) * 7919`,
etc.), output to `hash_mix_oracle.csv`.

**Port (C++):** `real-program-crosscheck/hash_mix_port.cpp` — structural
1:1 port using `glsl::shift_right_arithmetic` for every `>>` and plain
`uint32_t` multiplication for `cpu_umul` (verified separately, not part of
the shift primitive itself, that `Math.imul(a,b)>>>0` matches plain
`uint32_t` wraparound multiplication: `umul_oracle.csv`, 5,000 pairs, **N
compared=5000, N exact=5000, N divergent=0**).

**Result:**

```
hash_mix cross-check: N compared=100206 N exact=100206 N divergent=0
cpu_umul spot-check: N compared=5000 N exact=5000 N divergent=0
```

**Negative control** (`hash_mix_port_logical_control.cpp`): the identical
port with every `>>` replaced by **logical** shift (i.e. the mistake of
reusing the existing `glsl::shift_right`'s semantics for this bespoke
helper) — confirms the cross-check is actually discriminating and the
100,206/100,206 exact result above is not a coincidence of a
sign-bit-poor sample:

```
NEGATIVE CONTROL (logical shift, expected to diverge): N compared=100206 N exact=12527 N divergent=87679 (87.50% divergent)
```

87.5% of outputs would be wrong with the logical primitive — a decisive
confirmation that (a) the value population genuinely exercises bit 31
densely and (b) the arithmetic primitive is doing real, necessary work,
not passing by accident.

## What I could not verify

- **Only one real C++ toolchain was available on this machine.** `g++` and
  `clang++` both resolve to Apple clang 16.0.0 (arm64-apple-darwin23.6.0) —
  there is no independent second compiler here to test the "naive
  `value >> masked`" expression against. The §4 "naive" column's 0/3,206,592
  divergent result is real evidence for *this* compiler only. This is
  exactly why `shift_right_arithmetic`'s actual implementation (§3) avoids
  depending on that expression at all, using only `std::bit_cast` +
  unsigned-domain operations instead — so this gap affects only the
  corroborating "naive" data point, not the shipped primitive's
  correctness argument.
- **ECMAScript spec text** for `ToInt32`/`ToUint32` and the shift-count
  masking rule: not fetched from the spec in this session (no network
  access used) — reproduced here only as empirically re-derived behavior
  (§1), consistent with the general-knowledge claim `bitops-precompute.md`
  already flagged the same way.
- **C++20 `[expr.shift]` exact current wording** on right-shift of a
  negative signed operand: not quoted from the standard text in this
  session; resolved by empirical toolchain testing (§2/§4) plus a
  standard-independent portable implementation (§3) rather than by
  reading the normative text.
- **No existing `shift_right` (logical) call site was found to be wrong.**
  This task's negative-control experiment (§5) confirms *why* it would be
  wrong if misapplied to a bespoke hash helper like `hash_mix`, but
  nothing in this task's scope touched or re-audited the 131 already-shipped
  programs that legitimately use the canonical `pcg3d` idiom — no
  evidence was found, or looked for beyond `bitops-precompute.md`'s own
  citations, that any *already-shipped* path uses `shift_right` where
  arithmetic shift was actually required. If such a site existed it would
  be a critical, prominently-reportable finding; none was found in this
  task's scope.
- **`bitwise_and`/`bitwise_or`/`bitwise_not`/`shift_left`** (the bonus
  companions in `shift_primitive.hpp`) were verified with the same sweep
  rigor as the shift primitive (§4 table) for `shift_left`, but `&`/`|`/`~`
  were only spot-checked on the 13-pair adversarial set in
  `probe_semantics.mjs` Section C, not swept across the full 100,206-value
  population the way the shift primitive was — they were lower priority
  per this task's brief (which commissions the *shift* primitive) and per
  `bitops-precompute.md` Hazard #2's own lower-severity rating. A future
  task wiring these into the emitter should extend `verify_sweep.cpp`'s
  methodology to them before shipping.

## Files in this deliverable

- `shift-primitive-report.md` — this report
- `probe_semantics.mjs` / `probe_semantics_output.json` — Step 1, JS semantics probe
- `gen_values.mjs` / `values.txt` — shared adversarial+pseudorandom value population
- `gen_oracle.mjs` / `sweep_oracle.csv` — main sweep oracle (JS ground truth)
- `gen_edge_amounts.mjs` / `edge_amounts_oracle.csv` — out-of-range shift-amount oracle
- `shift_primitive.hpp` — the proposed primitive (Step 3)
- `sanity_check.cpp` — minimal `static_assert`-based smoke test
- `verify_sweep.cpp` / `verify_sweep_output.txt` — Step 4, main sweep verifier
- `verify_edge_amounts.cpp` / `verify_edge_amounts_output.txt` — Step 4, edge-amount verifier
- `real-program-crosscheck/` — Step 5:
  - `snapshot_canonicalFactory147.js.excerpt`, `canonical_kernels_source.sha256` — snapshotted source
  - `hash_mix_reference.mjs` / `hash_mix_oracle.csv` / `umul_oracle.csv` — JS ground truth
  - `hash_mix_port.cpp` / `hash_mix_port_output.txt` — C++ port using the new primitive (0 divergent)
  - `hash_mix_port_logical_control.cpp` / `hash_mix_port_logical_control_output.txt` — negative control (87.5% divergent, proving the test discriminates)

All build commands use the mandatory flags:
```
clang++ -std=c++20 -Wall -Wextra -Wpedantic -Werror -ffp-contract=off -O2 <file>.cpp -o <file>
```
Every build in this task produced zero warnings and zero errors.
