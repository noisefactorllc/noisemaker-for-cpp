# Edge bvec3 and pixel-parity oracle

Frozen JavaScript ground truth for `filter/edge:edge`. Exact Float32 and RGBA8 hashes cover both convolution kernels, both channel modes, both contour sides, threshold/invert/mix, all nine blend modes, control boundaries, repeatability, and input immutability. The typed-frontend probe freezes the exact stored `bvec3` closure and canonical lane-sequential center self-splat.

## Frozen authority

- Upstream snapshot revision: `117a236679d1db3ab8f0e278230ece277b57564c`
- Corpus revision: `a024dc3a960cc44af454abc7aebce50456c194e6`
- GLSL source: 6530 bytes, SHA-256 `841f9f547d06aace8444953f401009abd02758f9dff271097b2799424c1db5d0`
- Canonical factory: `canonicalFactory49`, 9011 bytes, SHA-256 `57375f0b17f6b90c541fc264b4e5233674eef6e6a496307e6a047138db1a2bb8`
- Public catalog identity is exactly the canonical factory; no adapter override exists.

## Captured pre-admission C++ frontend boundary

- Validator first error: `filter/edge:edge:73:11: unsupported typed type bvec3`
- Emitter first error: `filter/edge:edge:73:38: unsupported builtin greaterThanEqual`
- Exactly 12 bvec3-typed nodes and 6 lane reads exist, all inside reachable `contourConv`.
- The historical in-process global-widening diagnostic rendered 14639 bytes, SHA-256 `fc9d8b6c220f5677136881ed304df6cb907f439e014864bdbd86b680fb938a23`; this frozen record is not current admission evidence.

## Current exact-profile C++ frontend boundary

- Without the profile, validator first error: `filter/edge:edge: exact Edge bvec3 contour profile carrier required`
- Without the profile, emitter first error: `filter/edge:edge:1:1: exact Edge bvec3 contour profile carrier required`
- The exact profile makes both independent authorities pass without widening global vocabularies; rendered C++ is 14774 bytes, SHA-256 `8855be067925a5eafad622f8bb6541be2e58671adb78a740c0c3275838a0ddab`.
- The center self-splat assignment is source-authenticated at `135:13-135:57`, SHA-256 `2559b7d881b9aaf4f425d0ab9df528e000fa3279a58a31ff839e4a5aaaf51064`, including its complete five-statement ancestry and target/constructor/dot child identities.
- Do not widen the global type or builtin vocabularies. The validator and emitter independently re-authenticate the key/hash/interface, all typed nodes and lane reads, the center-splat route, and the absence of any extra admitted site.

## Runtime shape

- `glsl::BVec3` already exists. Edge additionally needs exact-profile-only `greaterThanEqual(Vec3, FloatExpr<3>)` and `lessThan(Vec3, FloatExpr<3>)` lowering, constrained to width 3 rather than widening Extrude’s width-2 helpers.
- The FloatExpr right operand must first materialize through `glsl::Vec3`, narrowing every retained-double lane to Float32 exactly as canonical `new PooledFloat32Array([lvl, lvl, lvl])` does. Direct comparison against the retained double is observably wrong and explicitly rejected.
- Canonical JavaScript stores `dot(centerSample, LUMA)` into lanes 0, 1, and 2 sequentially; each later dot observes earlier Float32 stores. The C++ lowering is exactly three contiguous ordered `set_swizzle<0/1/2>` calls. A simultaneous whole-Vec splat is rejected.
- 9 general direct fixtures cover mixed/equal lanes, signed zero, infinities, NaNs, and adjacent Float32 values. Their relational/selection/construction bytes hash to `10711bcdfaa5d8b385bea12fa417b91d4191295078a3111f2e795f710a5fa243`.
- 3 native-style Vec3/FloatExpr fixtures require calls to the actual overload shape. Expected boolean bytes hash to `f24cd192230e518c01b9bc9500e541124193fd69c4785333666357a6f641ab7a`; the rejected raw-double comparison hashes to `18c31b960782f23b04be9c4e2531e4bee85cb47d1e022fb3ffdff3d23031a1ab`.

## Render cases

| Case | Size | Kernel | Channel | Side | Level | Blend | Float32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| fine-color-radius-two | 9x7 | 0 | 0 | 0 | 50 | 6 | `9bdc913e82fe60bcc33a4ac648931dba39cc9c5ed3c5da950717d7ae3c5ed0b7` | `2b8a923bcd69f3f76af214760c7ea95476afbe1b94f9080e5c0a4fe0213529a9` |
| bold-color-radius-three | 9x7 | 1 | 0 | 0 | 50 | 6 | `1bfcb17c50f4995dbd7b7a69e643e26c050fec3567552b4901bb916cd85be2ed` | `e55142c54cc2fd6ae26fc900fedef1cc179fc86d53fc3e4d603d57f2188c9811` |
| fine-luma-threshold-invert | 8x6 | 0 | 1 | 0 | 50 | 2 | `43d14ec8c38eee1c8b3c5fce2ae2ab67b98042c3fb40087d3b61191499ed2d7a` | `af85175b54cf35725ac3422ab182daa7ed0c0be1f56f62a184349ed0e47566cf` |
| radius-one-scale-zero | 6x5 | 1 | 0 | 0 | 50 | 6 | `ecae9908875b965929fed9b4843d923ef92b392b1ff2b3a0c51e4cfcda2acb5d` | `a458c8d9851ee8aa034a83b41c731ca060f3831d06d0ab53129c46272f3429b4` |
| amount-zero-normal | 6x5 | 1 | 0 | 0 | 50 | 6 | `64c5f118731fe83feb6639e7cf63c9a900b88579d5927ab89a414a5baf89f2bd` | `2bca1d79171282f6d9f10be2f677e3c020bcc9ceb0d2b0b85e1b2ddbb9acc6f4` |
| mix-zero-input-identity | 6x5 | 1 | 0 | 0 | 50 | 8 | `e859cd989a0632253c5907945d750eadf61d9c4eea58c7f40a708eff2e6c1b99` | `ebf4857f69d6f9912ad6fb6ecbdfb5658d88a22910a4601d2ff6538a957cafe1` |
| contour-color-lower | 7x7 | 2 | 0 | 0 | 50 | 6 | `23dbc27f71da7504aa77eebdc9b9e4582c3e77a47678815cb23a84ea38280357` | `74213fc2f8cc716c65e1d75bda55b3f27acbfff59434265d77255085ef2bc52d` |
| contour-color-upper | 7x7 | 2 | 0 | 1 | 50 | 6 | `433139bf9ee514a2e87eabdf64267bbb9ce3ea33945c1405e91f7fc3c976662a` | `45c09010b3c8b903b809fcd1549cca000d5f655d7b2eb6a09f4ef05876ac371d` |
| contour-color-lower-level57-f32-equality | 7x7 | 2 | 0 | 0 | 57 | 6 | `de2dad25d144c7f11f64b62d6e89be812e66d44e3344794751464bf8a55e7c2c` | `880f56b33a384574b37fdf146f9a0b121bd9e61373e5d9643bcd0dcfe677b84c` |
| contour-color-upper-level57-f32-equality | 7x7 | 2 | 0 | 1 | 57 | 6 | `cc9553f005eb5f4692891caf65e92d6c24bd49e1945618e2f99d243d4c5fdacb` | `80725d5e9adaaff2cb6c07f8f05e05d603821f66c222261de9e2662b98e43698` |
| contour-color-upper-level-zero | 7x7 | 2 | 0 | 1 | 0 | 6 | `2d162c2e67d9da328b56fd0e2c3c67b86afb47e4dc2c0adc678ea93bb2a90d51` | `a760f87160f0bec1de65c75230b0958ec1a272f5289138267d3ac897dd712ef2` |
| contour-color-lower-level-hundred | 7x7 | 2 | 0 | 0 | 100 | 6 | `68adab5f5048a75880de1bff341845272093f617bcf260276e4010a59ba63e32` | `d9b19470109ba436c8af9cfaf76d6acfc665e464dbff54510150703de5e7791e` |
| contour-luma-lower | 7x7 | 2 | 1 | 0 | 43 | 6 | `fdb8c70d0df49093c617414bf289c98ec74ef29f525a2373ccbc8f296b73b783` | `73cba512a2700ddfb4f18975668ed150ceac309eaa1d59e417c0496c60187ca6` |
| contour-luma-upper | 7x7 | 2 | 1 | 1 | 57 | 6 | `940dd932fbaa810359783a70f3ac944835e8c4922f0b6fca9c325f18b479a257` | `fd391208d91ab6bac9d159205ba396e908a8cdd52a4d1b6023a4ef8ec25a5b14` |
| blend-0 | 5x4 | 0 | 1 | 0 | 50 | 0 | `8a8b03d743853e34bcd9a11975c860aa25888c1a3c7f5272b00a44d74b9f9dd1` | `e7e0a9c04be65179e4bf11c5427ebb26b362035f0393fdaa44c13624e64b11c8` |
| blend-1 | 5x4 | 1 | 0 | 0 | 50 | 1 | `e256dff7e091bb45017e1314011d8e315fcdf20d7eb83051a9aa0cd8fc94eb7d` | `d1848e5103b7ec96ec4618946e248428b021efed7a55918eb14a4292ef9af08d` |
| blend-2 | 5x4 | 0 | 0 | 0 | 50 | 2 | `f6d83885968ccf8a861da4bbf8964a97e4b886a0764d01460f4cec43959f4296` | `8a0f78424e1739d7262be4c843c5f3300d5bff48fb3b2f92395daf56e2608c82` |
| blend-3 | 5x4 | 1 | 1 | 0 | 50 | 3 | `559ba7b503e76f3edb950d1080cab5769608dd838f3b98e518263580ecbcadf3` | `824fef9d490445780263e86c2a3f29f22f04d947583d26f9a42c547b380bb77b` |
| blend-4 | 5x4 | 0 | 0 | 0 | 50 | 4 | `cec42b1fea3dc977143de14c8e250095b001c66d3e1981a30c129841d35fc544` | `305951cd1a2b7bd7ccc43c047d6827ab4f9b46661be5a55ccec3b239fc14cab5` |
| blend-5 | 5x4 | 1 | 0 | 0 | 50 | 5 | `477835e29a7a8bc7bc41662f4a636c11330548372cd68036d34f7fe6c90e7d89` | `ba808de4275704cb050ccb3a0140288f372924bba80ee4b26b82d31518478e0c` |
| blend-6 | 5x4 | 0 | 1 | 0 | 50 | 6 | `991e436f4684851bc5122c76dd4428ba2cb43822223021cd89910ed8e8b2d1d9` | `bd69518a512f924723b76dadc4bd8b2df091561bcb85a06a9d64e48356a6027c` |
| blend-7 | 5x4 | 1 | 0 | 0 | 50 | 7 | `050adc9953c661a799e5cdc89abc710d6059f5c73b89f1c5617827a5e2b4100e` | `1e063cc897584d917015416effa3a4a9a7efd8e006796c3f3fcb95af699bd9af` |
| blend-8 | 5x4 | 0 | 0 | 0 | 50 | 8 | `745af9d1ed86f0ddde432621873be18d75fdadea4a6a773ff011492f206c68b9` | `7f5bb075b78111d281aea79b9abbcffade27e2ca9408f9bbcbf434e449d6378c` |
| external-context-base | 8x5 | 1 | 0 | 0 | 50 | 7 | `a17a831e563747209feb779d03aa22e717ab27b7275332b00896f87e889af97b` | `2d3c553f02d4fa5e0ff58ab4a1dd926d56252fd28b02634e60ba5653c1a201a2` |
| external-context-extreme | 8x5 | 1 | 0 | 0 | 50 | 7 | `a17a831e563747209feb779d03aa22e717ab27b7275332b00896f87e889af97b` | `2d3c553f02d4fa5e0ff58ab4a1dd926d56252fd28b02634e60ba5653c1a201a2` |

Every case requires exact repeated-render identity, exact input-bit immutability, finite output, and direct-canonical/public-catalog equality. The external-context pair must remain exactly identical.

## Mutation discrimination

| Mutation | Required witnesses | All divergent cases |
| --- | --- | --- |
| upper-relational-inverted | contour-color-upper | contour-color-upper, contour-color-upper-level57-f32-equality |
| lower-relational-inverted | contour-color-lower | contour-color-lower, contour-color-lower-level57-f32-equality, contour-color-lower-level-hundred |
| red-center-side-read-from-green | contour-color-lower, contour-color-upper | contour-color-lower, contour-color-upper, contour-color-lower-level57-f32-equality, contour-color-upper-level57-f32-equality, contour-color-lower-level-hundred |
| green-crossing-output-read-from-blue | contour-color-lower, contour-color-upper | contour-color-lower, contour-color-upper, contour-color-lower-level57-f32-equality, contour-color-upper-level57-f32-equality, contour-color-lower-level-hundred |
| contour-side-forced-lower | contour-color-upper | contour-color-upper, contour-color-upper-level57-f32-equality, contour-luma-upper |
| contour-level-divisor-changed | contour-color-lower, contour-color-upper | contour-color-lower, contour-color-upper, contour-color-lower-level57-f32-equality, contour-color-upper-level57-f32-equality, contour-color-lower-level-hundred |
| contour-rhs-f32-broadcast-bypassed | contour-color-lower-level57-f32-equality, contour-color-upper-level57-f32-equality | contour-color-lower-level57-f32-equality, contour-color-upper-level57-f32-equality |
| contour-dispatch-disabled | contour-color-lower, contour-luma-upper | contour-color-lower, contour-color-upper, contour-color-lower-level57-f32-equality, contour-color-upper-level57-f32-equality, contour-color-upper-level-zero, contour-color-lower-level-hundred, contour-luma-lower, contour-luma-upper |
| channel-branch-inverted | fine-color-radius-two, fine-luma-threshold-invert, contour-color-lower, contour-luma-lower | fine-color-radius-two, bold-color-radius-three, fine-luma-threshold-invert, contour-color-lower, contour-color-upper, contour-color-lower-level57-f32-equality, contour-color-upper-level57-f32-equality, contour-color-lower-level-hundred, contour-luma-lower, contour-luma-upper, blend-0, blend-1, blend-2, blend-3, blend-4, blend-5, blend-6, blend-7, blend-8, external-context-base, external-context-extreme |
| center-self-splat-simultaneous | fine-luma-threshold-invert, blend-0, blend-3, blend-6 | fine-luma-threshold-invert, blend-0, blend-3, blend-6 |

The simultaneous center-splat mutant diverges in exactly four cases. Its first frozen mismatch is lane 25, top-down (6,0), channel g: canonical 0x3ef9ec6f, simultaneous 0x3e69ed28.

Frontend negatives reject wrong profile/key/hash, both relational substitutions, two bvec lane-route changes, an extra stored bvec3 site, a reversed center-splat dot route, and an extra self-splat. The whole-program, interface, and exact node/ancestry hashes make unrelated source drift fail closed.

## Regeneration

From the repository root:

```sh
python3 docs/port-engineering/bvec/edge-parity/edge_frontend_probe.py --check
python3 docs/port-engineering/bvec/edge-parity/edge_frontend_probe.py --live-frontier
node docs/port-engineering/bvec/edge-parity/edge_parity_oracle_generator.mjs
node docs/port-engineering/bvec/edge-parity/edge_parity_oracle_generator.mjs --check
```

