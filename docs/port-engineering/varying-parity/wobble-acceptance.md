# wobble189 — acceptance record

`filter/wobble:wobble` landed as typed row 189 (2026-08-19), insertion index
155 between `filter/wind:wind` and `filter/wormhole:blend`. First program of
the **varying-uv admission** mechanism (`varying-uv-admission-v1`,
`tools/glslcpp/frontend/varying_uv_profile.py` — wobble its landed key, grime
its prepared second). Pure expression lowering: `v_texCoord → context.uv`,
no ABI change, no kernel-signature change — the JS authority never
interpolates varyings on the CPU path (the runtime's three-slot alias map).
Design `varying-design.md` + its 2026-08-18 implementation amendment
(reviewed GO-WITH-CORRECTIONS, corrections folded).

## Slice row

```json
{
  "defines": {},
  "program_key": "filter/wobble:wobble",
  "varying_profile": "varying-uv-admission-v1"
}
```

## Post-slice artifacts (quoted from the generated files)

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tools/glslcpp/typed_slice.json` | 24,216 | `d950efd9b79306bf0e02c79592e0887b7aee23b68c5067213e933cf57ae00806` |
| `src/typed_generated/typed_slice.cpp` | 2,069,112 | `a2da68ff595006b239098d129b374e87405be3b43aad2b99bb5bfd8e841d3faf` |
| `src/typed_generated/typed_manifest.json` | 302,565 | `12f352d2ad7924f10838cedbc5ddd175d15b1f75c188ee93e34a1c686aab8bf3` |
| `include/noisemaker/generated/catalog.hpp` | 17,483 | `37ae5bff677f977a59dc3c4a3c9946469fc739374bd61ddd6450a3c15b7ca2d6` |

Census: 189 typed rows; 191 catalog binds; corpus keys absent 23; genuinely
unported 22; sorted 189-key SHA-256 (trailing newline)
`b341c0761af4b038f290961d870a9a5a2df07183c3d948a95b6a9fb1536f55fd`;
`factories.size()` 190U → 191U; shared expected-keys array carries wobble.

## Gates

- **Generator gates**: all four `--check` exit 0 at 189 programs.
- **Focused battery** (12 modules, controller-run after the repair lane):
  **643 tests / 0 failures** — including the lane's integration tests
  (189→188 reconstruction), the milestone repair pass (18 classified
  repairs: the taskNN exclusion family + live pins; no frozen count or hash
  altered), and the varying/struct/bit-family module suites.
- **Native**: Debug, Release, and ASan+UBSan each **268 PASS / 0 FAIL** on
  the 189-row state (ctest 0; zero sanitizer diagnostics; the +6 over 262
  are wobble's native tests). x86_64 and the wave-1 assembly sweep: see the
  wave-1 record.
- **Native parity**: six `typed_wobble189_*`-style tests — exact float32-word
  + RGBA8 parity on all four JS oracle cases (public/direct/repeat,
  independent buffers, input textures bound verbatim), the crop case
  asserting parity with the stored tile surface ONLY (the measured
  non-identity on both arms), binding ABI, and the inert-defaults axes.

## Controller corrections of record (the repair lane caught these)

- grain sits at index **53** (effects moved it 52→53; wobble sorts behind
  grain), and wobble's insertion index is **155**, not the design-era 153 —
  earlier controller prose quoted pre-effects values; the pins were measured
  from the live artifacts.
- A concurrent synth/noise prep lane had landed its runtime-loop-bound key
  LIVE, reddening the whole-suite census (the `load_slice` key-census trap).
  Corrected by applying the family's prepared split to
  `runtime_loop_bound_profile.py` (`PREPARED_RUNTIME_LOOP_BOUND_KEYS`), with
  the module's authenticator admitting prepared keys under their exact
  profile — the same semantics kaleido's array module established.

## Process record — the fourth kill and recovery

The wobble integration lane was killed by the platform's 5-hour usage limit
during verification (its relaunch predecessor had died of a model-stream
stall before touching the tree). The land-early checkpoint order worked as
designed: row, registry, regeneration, factories/keys updates, integration
tests, native block, and most milestone repairs were all landed; the
controller diagnosed the one census break (the synth/noise live-key issue
above), ran the three native configurations, dispatched the milestone
repair lane for the remaining 18, and re-quoted every figure from the
artifacts.

## Claim boundaries

The tile route is a measured non-crop on BOTH arms (the design amendment;
wobble has no `tileOffset`/`fullResolution` bindings — `v_texCoord` is
purely destination-local). At shipped defaults every scalar binding is
output-inert (measured structural bound: max offset 0.0275 < half-texel
margin 0.03125); `range` wakes the warp. The uv-identity (Python-side
exhaustive 1..1024 + 2048/4096, both lanes including y-flip) is frozen in
the varying module; the native `make_context` equality rides the existing
`PixelContext` construction. Mutant witnesses intentionally overlap (they
pin different reachable functions); the 1e-7 uv-subtexel perturbation is
measured-invariant and recorded, not budgeted.
