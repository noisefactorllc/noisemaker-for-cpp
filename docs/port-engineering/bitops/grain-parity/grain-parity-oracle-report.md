# Grain scalar-XOR and pixel-parity oracle

Frozen JavaScript ground truth for `filter/grain:grain`. The oracle combines direct unsigned-word recomputation of the three scalar XOR sites with canonical/public pixel renders. Float32 hashes and RGBA8 hashes are exact byte contracts; the custom comparer adds diagnostics without weakening those contracts.

## Frozen identities

- Upstream snapshot revision: `117a236679d1db3ab8f0e278230ece277b57564c`
- Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`
- GLSL source SHA-256: `6edf8deec35e2fa3a32fc150c2be8cb6d71a9356c1c7a3cff5bd3c6c7df764f0`
- Canonical factory: `canonicalFactory65`, 9702 bytes, SHA-256 `36a15bacaf42ebe94dc587fdc77cb56a5c714cae51fd40c7f7a6a187794ef44f`
- Public catalog identity is exactly the canonical factory; no adapter override exists.

## Semantic contract

- Exactly three reachable scalar XOR sites are frozen, at GLSL spans `52:9-52:28`, `53:9-53:58`, and `54:9-54:58`.
- JavaScript scalar `^` produces a signed int32 number. The immediate `cpu_uvec3` parent then applies `>>> 0` lane-wise, so the observable word is exact unsigned 32-bit XOR.
- Unsigned multiplies are `Math.imul(... ) >>> 0`; the direct fixtures independently recompute the lane words with BigInt modulo 2^32 and require exact agreement.
- `Math.round` and `as_u32` intermediates are frozen explicitly, including positive ties, negative half, and negative zero. Negative distinctions are not render-reachable after the canonical clamps.
- `alpha` is the effect-level amount. `renderScale` is the closest noise-scale control but is an infrastructure binding, not an effect parameter. Grain has no colored control: it broadcasts one scalar noise value to RGB.

## Render cases

| Case | Size | Alpha | Pause | Time | Frame | External seed | Render scale | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| amount-zero-input-identity | 5x3 | 0 | 0 | 0 | 0 | 0 | 1 | `95a7ebb654bb186109154e45ac3bf1233a5a4e2e20d71da5bf5f8bab99ae8875` | `30b0721ef5ed78f832c967d85942d3b8d8a5e0c65d53188142b81275555f8002` |
| base-time0-frame0-seed0 | 7x5 | 0.25 | 0 | 0 | 0 | 0 | 1 | `fb65138f528771de306e7b5c76d1639938c445a4e037da2c9ea7bbeeb34bfb01` | `23616559bcb6201ceeaae29d945df294808bc1970c3f9d783b6b4f4eddda888d` |
| base-time0-frame-max-seed-max | 7x5 | 0.25 | 0 | 0 | 4294967295 | 4294967295 | 1 | `fb65138f528771de306e7b5c76d1639938c445a4e037da2c9ea7bbeeb34bfb01` | `23616559bcb6201ceeaae29d945df294808bc1970c3f9d783b6b4f4eddda888d` |
| animated-time-eighth | 7x5 | 1 | 0 | 0.125 | 17 | 2147483648 | 1 | `7ba3af181c974d7e262c1497805395c85d9cd9804afca3e0de1bf53ea1d26d9e` | `3549094e134e1862be09fdb98e1c6287756190e011c68c9296edabbc8ba1644c` |
| pause-reference-time0 | 7x5 | 1 | 0 | 0 | 17 | 2147483648 | 1 | `a89e2a94cebfb770e7d5c8b9f2c213c342aeb38946f614dda5626da5b7770b5e` | `3312c51e1f2f78318c3ae72cb39cf769efaa88c8de86abcc26efd1cb523d7767` |
| paused-nonzero-time | 7x5 | 1 | 1 | 0.125 | 99 | 1 | 1 | `a89e2a94cebfb770e7d5c8b9f2c213c342aeb38946f614dda5626da5b7770b5e` | `3312c51e1f2f78318c3ae72cb39cf769efaa88c8de86abcc26efd1cb523d7767` |
| scale-clamped-zero | 4x9 | 0.75 | 0 | 0.03125 | 3 | 4660 | 0 | `a6385a82c7538b9481bd73c3f963e8db6269de0282bfcb890d09a6283337cfa0` | `2b3d851bc9dfb2f57fca01accaf079083ce6374d9234abe973244eb80f6011a3` |
| scale-one-control | 4x9 | 0.75 | 0 | 0.03125 | 3 | 4660 | 1 | `a6385a82c7538b9481bd73c3f963e8db6269de0282bfcb890d09a6283337cfa0` | `2b3d851bc9dfb2f57fca01accaf079083ce6374d9234abe973244eb80f6011a3` |
| scale-noninteger | 11x3 | 0.5 | 0 | 0.375 | 4 | 305419896 | 1.5 | `29e5204eeae50950f5fb97dddcdecbe20ffc49a3fd032f22abd592e93c507bf2` | `7d44ab2126d8744405b28e6930364f892c917561154a09400c578c99f1d7123e` |
| scale-large-tiled-round-half | 3x4 | 1 | 0 | 0.625 | 5 | 4294967295 | 50 | `19a4bceed4b4f16e78abf543f6be891d3b239685f9fac6ffbf2a3771c2d909da` | `448963a3eba52b152b447b5b6fab3b2967d2fa5c6bd3c73726ac0b56fb04e1bc` |
| carry-in-bounds-then-oob | 3x1 | 1 | 0 | 0 | 0 | 0 | 1 | `70d24bc683fff5973d2a076021b337424e002d4417aba50a9cc5f1c709f7f1ed` | `1f63d21dbaaf8db69e92896ea505af92b417a48e07e2437b9fbbdd2ff3c6732d` |
| fresh-first-pixel-oob | 3x1 | 1 | 0 | 0 | 0 | 0 | 1 | `17b0761f87b081d5cf10757ccc89f12be355c70e2e29df288b65b30710dcbcd1` | `15ec7bf0b50732b49f8228e07d24365338f9e3ab994b00af08e5a3bffe55fd8b` |
| full-resolution-x-zero-fallback | 4x2 | 0.625 | 0 | 0.0625 | 0 | 0 | 1 | `096b4406e3964ac8d422fb77f61faac6b31020c7a80531f24710dfcbba8f7ca1` | `16ede65e02c57b9cd1db5f6158cd13d7d92de2e53b76822494c022d2ba3a3d5c` |
| repeated-bound-kernel-first-pixel-oob | 1x2 | 1 | 0 | 0 | 0 | 0 | 1 | `2849f879f9c23d992285ff8dd0cd653095fc34bff7014cd6fdb8cca7eea74412` | `4d47f70e067655ed1dbbb3b16ef19e1442eac9a7c3e7f4498a9636e61c00d48f` |

Every case requires exact repeat identity, exact input-bit immutability, finite output, and direct-canonical/public-catalog equality. Declared frame/seed, pause/time, and renderScale-clamp identity pairs are checked bit-for-bit.

## Mutation discrimination

| Mutation | Required witness cases | All divergent cases |
| --- | --- | --- |
| xor-lane0-seed-omitted | base-time0-frame0-seed0, animated-time-eighth | base-time0-frame0-seed0, base-time0-frame-max-seed-max, animated-time-eighth, pause-reference-time0, paused-nonzero-time, scale-clamped-zero, scale-one-control, scale-noninteger, scale-large-tiled-round-half, carry-in-bounds-then-oob, full-resolution-x-zero-fallback, repeated-bound-kernel-first-pixel-oob |
| xor-lane1-replaced-by-add | base-time0-frame0-seed0, animated-time-eighth | base-time0-frame0-seed0, base-time0-frame-max-seed-max, animated-time-eighth, pause-reference-time0, paused-nonzero-time, scale-clamped-zero, scale-one-control, scale-noninteger, scale-large-tiled-round-half, full-resolution-x-zero-fallback |
| xor-lane2-replaced-by-or | base-time0-frame0-seed0, animated-time-eighth | base-time0-frame0-seed0, base-time0-frame-max-seed-max, animated-time-eighth, pause-reference-time0, paused-nonzero-time, scale-clamped-zero, scale-one-control, scale-noninteger, scale-large-tiled-round-half, carry-in-bounds-then-oob, full-resolution-x-zero-fallback, repeated-bound-kernel-first-pixel-oob |
| wrong-round-positive-ties-truncate | scale-large-tiled-round-half | scale-large-tiled-round-half |
| base-seed-omitted | base-time0-frame0-seed0 | base-time0-frame0-seed0, base-time0-frame-max-seed-max, animated-time-eighth, pause-reference-time0, paused-nonzero-time, scale-clamped-zero, scale-one-control, scale-noninteger, scale-large-tiled-round-half, carry-in-bounds-then-oob, full-resolution-x-zero-fallback, repeated-bound-kernel-first-pixel-oob |
| time-omitted-when-running | animated-time-eighth | animated-time-eighth, scale-clamped-zero, scale-one-control, scale-noninteger, scale-large-tiled-round-half, full-resolution-x-zero-fallback |
| monochrome-channel-coupling-broken | animated-time-eighth | base-time0-frame0-seed0, base-time0-frame-max-seed-max, animated-time-eighth, pause-reference-time0, paused-nonzero-time, scale-clamped-zero, scale-one-control, scale-noninteger, scale-large-tiled-round-half, carry-in-bounds-then-oob, full-resolution-x-zero-fallback, repeated-bound-kernel-first-pixel-oob |

The direct scalar corpus separately rejects letting the signed XOR intermediate escape into arithmetic shifts, seed narrowing, coalescing wrapped multiplication into ordinary Number multiplication, and reordering the sequential PCG mix stage. Each rejection is an exact `Uint32Array` word comparison.

## Deliberate unreachable traps

- External seed and frame omission cannot be a pixel mutation witness because this canonical program does not read either binding; paired renders prove identity.
- A signed scalar XOR result and its immediate cpu_uvec3 unsigned materialization have identical low 32 bits; the authenticated parent role is structural, not pixel-observable.
- Negative-half and negative-zero round distinctions are erased by max(..., 0), integer materialization, and max(as_u32(...), 1) before any render coordinate uses them; direct round evidence freezes the intermediate behavior.
- There is no colored/monochrome branch to toggle. A mutation that breaks the fixed scalar-to-RGB broadcast is required to diverge instead.

These are reported as unreachable instead of manufacturing a false pixel witness. Structural authentication must still freeze the immediate unsigned constructor parent and the fact that the owner is reachable from `main`.

## Regeneration

From `/Users/aayars/platform/noisemaker-for-cpp`:

```sh
node docs/port-engineering/bitops/grain-parity/grain_parity_oracle_generator.mjs
node docs/port-engineering/bitops/grain-parity/grain_parity_oracle_generator.mjs --check
```

