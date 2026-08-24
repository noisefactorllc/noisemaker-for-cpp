# Task 18 independent final acceptance review

## Decision

**APPROVED.** No P0, P1, P2, or P3 findings.

I reviewed the frozen Task 18 implementation against the ratified brief, implementation design, risk audit, scope-proof reviews, oracle artifacts, and final implementation report. I independently inspected the semantic proof, both validation boundaries, C++ lowering, generated output, Python tests, native oracle tests, catalog/binding coverage, and compiler stack records. The implementation is narrowly confined to `fixed-grid-counter-store-v1` for:

- `filter/celShading:celShadingEdges`
- `filter/outline:outlineSobel`

The final stable implementation report is SHA-256 `a7d482bfa0f60e58f737ead746ca9ba6a55fa562d874d01eff3b2323c233cdef`.

## Frozen review inputs

- Brief: `11628e7d2aa25450e2988e35614c931094d4254f216f374e23a78b2401aa0684`
- Brief ratification: `982f00ca27705de97fa662395d5000e4d9dffdce127c110b8bb8aae12ca4299d`
- Implementation design: `6f8cba1e383ba5fb1d6054d46cee9ee8e0d1e93241e6df1a7773d8fc1512a0af`
- Risk audit: `45e7efad86d2b390068052bdec914a413bf3540ac8f5af6cf53ed1290a28cbda`
- Scope-proof review: `bc27eaa3db334e6912574429d94f1d6a50f7ed5995170881a6ba67f70ba3edc7`
- Scope-proof rereview: `9f67a898fe99302f1f1f92fe409c089f775c22e45cb19d52dc9ec756e357ec5f`
- Oracle generator: `ef9ec7303f2e610af7384e3c681935be725bce8019498e3f2b49f9e6ec6489c8`
- Oracle JSON: `6bfefcf7891f55896e1ff5be6cd67db94c21853f90073a851eacc8ff18da9c1b`
- Oracle report: `16199e11d4ec8af8c4c5ecf86748d16573c2f53c61ed4e3bd4c79acec8a710f3`
- Implementation report: `a7d482bfa0f60e58f737ead746ca9ba6a55fa562d874d01eff3b2323c233cdef`

## Acceptance analysis

### Proof and authorization boundary

`fixed_grid_counter_store_proof.py` hard-locks the two accepted keys, normalized and raw source hashes, empty defines, typed-function hashes, and whole-program hashes. Its fingerprint covers declarations, functions, resources, body, local types, structs, uniform blocks, interfaces, built-ins, counted-loop proof, and inherited Task 17 proof. The validator and emitter each clear and independently reconstruct the counted-loop, Task 16, Task 17, and Task 18 proof state before authorizing a site.

The structural matcher requires the exact zero-dimension early return; nested `ky`/`kx` loops from -1 through 1 with prefix `++`; a zero-initialized `float[9]`; fresh `int idx = 0`; the exact dynamic store followed immediately by the discarded postfix update; interval/finality proof 0..8 and 9; and the twelve exact authored literal reads. Authorization is per-site rather than capability-wide: only the proved array declaration, dynamic lvalue store, update statement, and literal rvalue reads are accepted.

### Independent tamper matrix

I exercised 13 mutation classes for both accepted keys, at both the validator and emitter boundaries, under three proof-state modes: retained proof, cleared proof, and attacker-updated `typed_ir_sha256` plus `whole_program_sha256`. All 156 boundary checks rejected as required:

`2 keys x 13 mutations x 3 proof modes x 2 boundaries = 156 rejections`

The mutations covered early-return removal and reordering, prefix-to-postfix loop updates, changed loop bounds, changed loop nesting, store/update reordering, changed `idx` initialization, changed `idx` use, dynamic store-target substitution, literal-read substitution, top-level resource addition, top-level global addition, and an additional array site. This confirms that recomputing exposed hashes is not sufficient to forge authorization and that both boundaries independently enforce the same frozen shape.

The final checked-in focused tests additionally reject changed early predicates/assignments/return values, changed array extent or initialization, declaration reorder, postfix loops, literal store indices, changed RHS, duplicate stores or updates, prefix counter updates, dynamic reads, and post-grid counter/store uses. The five exact Task 18 Python tests pass on the stable bytes.

### Lowering and generated-code dominance

The emitter lowers the local table to `std::array<double, 9> samples{}`. This provides value-initialized numeric zeroes, not merely default-initialized indeterminate storage. The dynamic store is a direct lvalue `samples[static_cast<std::size_t>(idx)]`; the twelve Sobel reads are direct literal indices; and the counter update remains `++idx` as the lowered effect of the authenticated discarded postfix source update.

Inspection of both generated namespaces (`typed_7` and `typed_37`) confirms the zero-dimension guard dominates all output-dimension division and table work, there is no zero-sized execution seam, and the loop/store/update/read ordering matches the authenticated source. Repository searches found no newly introduced runtime or test seam that could inject a zero-sized public surface.

### Oracles, bindings, and catalog

The six frozen Task 18 cases cover both kernels in F32 and RGBA output modes. Debug and Release native runs reproduce every frozen full-surface hash, all twelve probe words per case, 9x7 shape, top-down orientation, and fresh double-render identity. The Task 18 oracle checker passes, as do the unchanged Task 15 checker and Task 16/17 checkers.

Binding tests require every documented field, reject wrong field types, and preserve the established extra-key behavior. The generated corpus and manifests confirm 212 corpus programs, 112 typed programs, 114 public programs, and 98 publicly unported programs. The catalog remains sorted and unique, and Refract plus Sacred Geometry remain rejected at both boundaries.

### Stack and execution properties

Fresh AppleClang 16 Debug and Release builds used strict project warnings, C++20, `-ffp-contract=off`, and `-fstack-usage -fstack-size-section`. Both `.su` records are static:

| Kernel | Namespace | Raw table | Debug frame | Release frame |
| --- | --- | ---: | ---: | ---: |
| Cel edges | `typed_7::pixel` | 72 bytes | 688 bytes | 272 bytes |
| Outline Sobel | `typed_37::pixel` | 72 bytes | 640 bytes | 176 bytes |

No allocation, callback, virtual dispatch, exception, `.at()`, runtime ABI, or `Surface` seam was added. The generated pixel functions remain `noexcept`.

## Verification evidence

- Stable-byte focused Task 18 Python tests: 5/5 passed in 0.613 seconds.
- Final complete Python discovery: 101/101 passed in 247.956 seconds.
- Corpus check: passed.
- Semantic body check: 212 programs passed.
- Generated-kernel drift check: passed.
- Typed-slice drift check: 112 programs passed.
- Task 15 oracle check: 38 vectors passed with frozen SHA unchanged.
- Task 16, Task 17, and Task 18 oracle checks: passed.
- Debug native executable and CTest: all cases passed, 1/1.
- Release native executable and CTest: all cases passed, 1/1.

## Final repository-scope hashes

- `include/noisemaker/generated/catalog.hpp` `0e43446f32f9ec121901f728819e25aabda2c84e9a7d28a8438a84cc4b37a79d`
- `src/typed_generated/typed_manifest.json` `4bd7470b0db62c9971bf79a94b771270405ae674075a477369cee143c19ed112`
- `src/typed_generated/typed_slice.cpp` `0a4fd8992ebbc4e143f1de4b911ee70399ad17b2aa3d6fee188ac210f83e109b`
- `tests/test_generated_kernels.cpp` `0a1247db251ab467b5caddf9f9d1ccd769ea4b2cc02724a223fe78762da8940c`
- `tests/test_semantic.py` `627c1dffaefac2fd944c1c2de322870f464414685c75183c8337e3028e77a179`
- `tests/test_typed_generator.py` `39d473b75278840fe9b8bb1dcc641ff3d6a8cd17b8094e6436537b0016a08df0`
- `tests/test_typed_slice.cpp` `88915e2b7e5f568686280b5a26a9bc5b585a4afa5e22e424158e9d7c2db221d4`
- `tools/glslcpp/emit_typed_cpp.py` `14203c862a8aa1ee480d3316acaddf0669772eace17ddb4b528def73ea4c0c6b`
- `tools/glslcpp/frontend/fixed_grid_counter_store_proof.py` `2bada0deacf426f29a85a1d747eba6e62ff5c37b4d428a4a4ab40fc44aa3ffa1`
- `tools/glslcpp/frontend/semantic.py` `01c772aae5732d048c11c28b93d18d00fce63f6373ecb294324773f5e8817f2b`
- `tools/glslcpp/frontend/typed_ir.py` `39d834a483bd1f45985a1af14c68281034f7e4fa23b33097d2443547bfa73acd`
- `tools/glslcpp/generate_typed_slice.py` `f414800b4d983c17e8f487043d0298b4ebf0ec18431aceb9c25750067598216d`
- `tools/glslcpp/typed_slice.json` `163a714fa7369d91405fb9b14614005b9c6c9d6ed550a8916bd43a2edb4513bc`

## Residual assessment

No Task 18 correctness, proof-authentication, scope, determinism, allocation, ABI, or stack residual remains. The authored zero-dimension branch is intentionally unreachable through the public API; its safety is adequately established by exact proof reconstruction, emitted dominance/order assertions, and absence of an unauthorized runtime seam.
