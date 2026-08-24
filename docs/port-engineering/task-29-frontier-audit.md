# Task 29 fresh frontier audit: exact borrowed sampler helper ABI

## Result

Select exactly `mixer/focusBlur:focusBlur`; no known blocker. Fresh analysis of
the accepted post-Task28 tree found 212 corpus / 128 typed / 130 public / 82
publicly unported programs. The typed and public ordered-key SHA-256 values are
`30f0333cfd995ba1b866fcbd9589507151255204088675bae6575e42d7328c55`
and `102f5436a5416399f2601879c7d5219706111bc64b93989acbb67d973a01b6c5`.

Adding Focus Blur alone projects 129 typed / 131 public / 81 unported, typed
ordinal 110 between `mixer/channelCombine:channelCombine` and
`mixer/mashup:mashup`, with ordered hashes
`c2561c5937ba5f11f5d2e86d729ff90b617aff738cb4de53dbf3cd8b76dbbff9`
and `2325f8d06d182800af90cd1b0b67efe9d3058d3682f0ceb4d3f5168ff4af5e16`.

All 84 keys absent from the typed slice were freshly parsed/analyzed. Only the
two already-public manual programs pass the current emitter. Focus Blur passes
the validator and reaches exactly one emitter blocker:
`unsupported typed type sampler2D`. A warnings-as-errors C++20 projection using
`const Surface&` has no downstream blocker.

## Exact target

- corpus revision `a024dc3a960cc44af454abc7aebce50456c194e6`;
- raw 2,268 bytes, SHA `dff787c7de67122abe60ac14f0fc8995e8087fc4549626e6fe678d8f86b3d7d1`;
- normalized 1,685 bytes, SHA `8b3cfb07882d0e409f617b2f86b02fa54cd36db213a60881370306306306be9f`;
- defines `{}`, numeric contract `glsl-f32`;
- function tuple `95428219c60cd14910f90e572857773e22818bfaf17436f6a249a10b4364c6e3`;
- whole program `96468ba160d253f7d064c2caccd9db686d772a2af94d13ee836996dc488e037b`;
- interface `3158dcf83a1d13f84a2d8f3d374d464230ff24b1ed812603cc02fbc96e56be96`;
- direct public `canonicalFactory195`, factory-text SHA
  `fb4c02c763ef42000b13bba3945cf4fd15e177a2ab2827372ce3b96aa3a778ff`,
  canonical object identity, adapter absent.

The interface is `inputTex:sampler2D@1/S1`, `tex:sampler2D@2/S2`,
`resolution:vec2@3`, `tileOffset:vec2@4`, `fullResolution:vec2@5`,
`focalDistance:float@6`, `aperture:float@7`, `sampleBias:float@8`,
`depthSource:int@9`, `fragColor:vec4@10/out`.

## Exact capability gap

Only helper ID 16 is admitted:

```glsl
vec4 applyFocusBlur(in sampler2D sceneTex,
                    in sampler2D depthTex,
                    in vec2 uv)
```

Parameters are exact symbols 13/14/15. Although canonical frontend `in`
symbols record `writable=True`, the recursive body census proves neither
sampler symbol is written or escaped. Each appears exactly twice: once as the
sampler operand of `texture`, once as the sampler operand of `textureSize`.
No sampler is returned, retained, copied, aggregated, reassigned, converted,
or passed to another user helper.

`main#19` owns exactly two mutually exclusive calls. Recompute freezes each
complete expression/statement ancestry, the unique enclosing `if`, exact
`depthSource#9 == 0` predicate object/children/hash, ordered then/else branch
objects, one call per slot, and exactly one dynamic call:

```text
57:17-57:50  applyFocusBlur(tex#2, inputTex#1, uv#33)
59:17-59:50  applyFocusBlur(inputTex#1, tex#2, uv#33)
```

Select only `const Surface&` for the two authenticated parameter sites. This is
a synchronous, non-null, non-owning read borrow. Existing state remains two
setup-owned `const Surface*` fields. The caller must keep both surfaces alive,
at stable addresses, and unmodified for the bound-kernel lifetime; destroying
Bindings afterward is safe, moving/destroying a surface is not. Two references
may alias the same surface. Concurrent mutation remains outside the contract.

There are four static `texture` and four static `textureSize` sites. Each pixel
executes 67 texture reads and separately 67 size queries: one depth, 64 scene
loop iterations, and two alpha sites. Loop proof is 1/0/1/64/64/acyclic.

## Boundary

Do not add `sampler2D` to generic type tables. Do not support sampler return,
local/global/array/aggregate storage, mutable or nullable parameters, ownership,
retention, arbitrary helper samplers, dynamic lookup, adapters, runtime types,
or any second program. Validator and emitter independently authenticate exact
objects, and generation counts every admitted parameter/call/site exactly.

Complete evidence is frozen in `task-29-recompute.py/json`, the Task29 oracle,
and `task-29-adversarial-audit.md`. This audit changes no repository/Git state.
