# Task 30 Extrude: integration-owner parity and boundary evidence

Date: 2026-08-12
Author: integration owner. All results first-hand from the live tree.

## Pixel parity — full-surface, bit-exact

The generated C++ kernel was rendered through the real public binder
(`noisemaker::generated::bind_filter_extrude_extrude` + `run_pass`) using the
oracle's exact input fixture, and compared against the frozen JavaScript
oracle `future-precompute/task30/extrude-oracles.json`
(`bf8c4c165846eb116d2afb4f78b7c1de78f70f104ac714e09395ceffbe51c758`).

**Eligibility.** The oracle carries six cases, but only the three whose define
map equals the slice's authorized default `{EXTRUDE_TYPE: 0, DEPTH_SOURCE: 0}`
are valid for the native port. The other three (`blocks-random-solid-tiled`,
`pyramids-luminance-solid`, `pyramids-random-window-tiled`) use
`EXTRUDE_TYPE: 1` and/or `DEPTH_SOURCE: 1`; binding them natively would
silently render a different program. They remain public-source sensitivity
evidence only.

Full-surface F32 SHA-256, C++ versus oracle:

| Case | SHA-256 | Result |
|---|---|---|
| `blocks-default-luminance-solid` (13×9) | `47dee1b5c5d290f510a1c43f81f41bb19782b6f9f7d389e7be6701d0c8a01ac5` | MATCH |
| `blocks-depth-zero-window` (11×7) | `f8b901fde60223c9a3068ad5320295eed1098070d882978be5e5d6e3d4693106` | MATCH |
| `blocks-max-depth-luminance-window` (15×10) | `04ea7d2c0abee1daed54b97dcf1b1efb3c05cd828d23b8d2ac7c65d04d19ef73` | MATCH |

All fifteen per-case probes (four corners plus centre, four lanes each) also
matched bit-for-bit, and input immutability held in every case.

This is whole-surface equality, not a sampled comparison.

## Generated lowering

```cpp
[[maybe_unused]] bool topHit =
    glsl::all(glsl::lessThanEqual(glsl::abs((P - faceCenter)), faceHalf));
[[maybe_unused]] bool sideHit =
    ((!topHit) && glsl::all(glsl::lessThanEqual(glsl::abs((P - cellC)), halfCell)));
```

## The capability-vocabulary constraint (discovered, not assumed)

`src/typed_generated/typed_manifest.json` records the **full global**
capability vocabulary in every program row — all 130 rows carry an identical
44-entry list. Adding a 45th capability would therefore change every row and
invalidate the frozen Task 27/28 historical-reconstruction hashes.

The existing `round` gate already solves this: it is admitted by node identity
and then explicitly excluded from `used.add`. Extrude follows the same rule:

```python
if value.callee not in {"round", "all", "lessThanEqual"}:
    used.add(value.callee)
```

Verified post-implementation: vocabulary length is still **44**, and neither
`all` nor `lessThanEqual` appears in any program's capability list.

## Boundary verification

| Property | Result |
|---|---|
| `bvec2` in `generate_typed_slice.APPROVED_TYPES` | absent |
| `bvec2` in `emit_typed_cpp._TYPES` | absent |
| `all` / `lessThanEqual` in `emit_typed_cpp._BUILTIN_NAMES` | absent |
| capability vocabulary length | 44, unchanged |
| 3-lane reduction (`bvec3`) | **compile error**: `candidate template ignored: constraints not satisfied [with N = 3]` |

### Independent authentication, both authorities

| Attack | Validator | Emitter |
|---|---|---|
| no profile carrier | rejected | rejected |
| wrong profile string | rejected | rejected |
| profile applied to foreign program (`filter/waves`) | rejected | rejected |
| top/side `lessThanEqual` → `lessThan` | rejected | rejected |
| top/side `all` → `any` | rejected | rejected |

The emitter was invoked directly, bypassing the validator entirely, and still
failed closed. Neither authority trusts the other's result.

Leak control: with Extrude fully supported, `filter/waves:waves` still fails
at `filter/waves:waves:41:9: unsupported builtin any` — the admission did not
generalize to any other program.

## Regeneration is surgical

Comparing generated `typed_slice.cpp` before and after:

```text
before blocks: 129   after blocks: 130
added:   ['filter/extrude:extrude']
removed: []
existing blocks CHANGED (modulo ordinal renumbering): NONE
```

Every manifest row's only delta is the shared `output_sha256` field, which is
the hash of the whole regenerated `typed_slice.cpp` and is identical across all
rows by construction.

## Gates at this point

```text
check_corpus --check            exit=0 PASS
check_semantics --check         exit=0 PASS   (212 programs)
generate_typed_slice --check    exit=0 PASS   (130 programs)
generate_kernels --check        exit=0 PASS
oracle task-15 … task-30        exit=0 PASS   (16 of 16)
failures=0

native (Debug, -Werror):        144/144 PASS, exit 0
```

Python discovery and the Task 30 native/Python fixtures are owned by the two
test owners and are not yet included here.
