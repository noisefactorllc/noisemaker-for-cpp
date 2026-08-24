# Task 25 Task 3 fresh independent review

Date: 2026-08-11

## Verdict

**CHANGES REQUESTED**

### Important

1. `tests/test_typed_generator.py:8154-8160,8185-8188` does not reconstruct the historical Task 22 slice required by approved design section 10. The fixture named `task22_spec` removes only the two Task 25 keys. It therefore retains Task 23's six additions (`filter/bloom:ntapGather`, `filter/directionalBlur:directionalBlur`, `filter/spinBlur:spinBlur`, `filter/strokes:stkSmear`, `filter/vaseline:upsample`, and `filter/wind:wind`) and Task 24's `filter/pixelSort:gatherSorted`. The asserted generated-isolation sizes are consequently 122 before CRT and 123 after CRT, which are Task 24-era sizes, not the historical Task 22 sizes. Reconstructing Task 22 from the current explicit slice by removing those nine later keys yields 116 typed entries after CRT (typed-list SHA-256 `76c81945ef992ed258900815335a23ae4f36d8756b7763ebd5e03d8562fde8e3`) and 115 before CRT; its public list has 118 entries (SHA-256 `019a80df52192e3c898af58a5e3a2a9da654896eadde78097ce4a818579328f9`). The Task 23 fixture correctly strips Task 24 and Task 25 additions, and the Task 24/Task 25 fixtures correctly strip their later additions, so this is isolated to the Task 22 historical reconstruction. Fix the Task 22 fixture to remove all Task 23-25 additions and retain/assert its historical counts/digests before accepting Task 3.

No Critical or Minor findings.

## Binding-input verification

- Amended brief: `193523a6e94642c7c1b6c4da86b08de8616d0d15a3edc0b3257e068ac930ddd2`
- Approved implementation design: `9900749a387a30c6f1db0e584d2382288d44c2f3b0d5670f3b1968f1312c357b`
- Task 3 report: `1f222453e269d3f8ed5b548d823aadae1f0a4861280c80a8f4753032b3c44a6d`
- `tests/test_typed_slice.cpp`: unchanged accepted SHA-256 `55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6`

## Verified compliant evidence

- The transitional exact-123/no-carrier loader acceptance path is absent. `load_slice` now requires one sorted unique 125-key list with typed-list SHA-256 `9b8f94754fc40e8f8701bb539d403d44343dbfc9c351809a6ca6dbbd468cdbd4` and exactly the two required lane-profile carriers.
- `tools/glslcpp/typed_slice.json` contains exactly two sorted carrier records, both with exact `{}` defines and `literal-vec3-lane-index-v1`.
- Current committed data is exactly 125 sorted typed keys and 127 sorted public keys. The public-list SHA-256 is `9d773dde79594d81d54b2d4cd1cab8b8929201eaa01ef276db38530c39edeaab`; the current tests derive 85 publicly unported keys from the frozen 212-program corpus.
- Final zero-based positions and neighbor triples are exact: Lens 2, Gather Sorted 52, Prismatic 59; the in-memory Task 24 reconstruction places Gather Sorted at 51.
- The Task 25 isolation test reconstructs the 123-program Task 24 slice and proves all prior generated blocks equal after only `typed_[0-9]+` ordinal normalization.
- The new normalized diagnostic projections are exact: Lens 27,446 bytes / `6cfa9d58cbc096b7372b00b17b4ed0b146236a4738acef7870cad05593a57fc5`; Prismatic 13,316 bytes / `8d6c98fed4ab2d2a2130566081386cdfb74d01ae84c11b198a1be08ae187155f`.
- Manifest, header, and catalog inventories contain one exact Lens row/declaration and one exact Prismatic row/declaration. The manifest contains no lane-profile field, and its `typed_slice_sha256` exactly matches the committed generated C++ bytes.
- The committed generated files are canonical current output: `python3 tools/glslcpp/generate_typed_slice.py --check` exited 0 with `generate_typed_slice: typed slice ok (125 programs)`.
- Focused Task 3 tests passed: 2 tests in 74.293 seconds, exit 0.

## Exact reviewed-file SHA-256 inventory

| File | SHA-256 |
| --- | --- |
| `tools/glslcpp/generate_typed_slice.py` | `4ef4203e80dd8beb78e65168c804234cdeb875436b1828ca9280c31bed138227` |
| `tools/glslcpp/typed_slice.json` | `1534c7a6d807bf58734da59aaa8b37f8dc8342ec5d744b936e2e6e079ad1bb49` |
| `tests/test_typed_generator.py` | `8269f5bf31b7b318bdcfad13667747f53f672d71028d0061b0fdfc16e4803825` |
| `src/typed_generated/typed_slice.cpp` | `b8fe5a45f3032a86185d0515d512a48c40ac37c689c18db0ecb43bf7108b1cc9` |
| `src/typed_generated/typed_manifest.json` | `618081cfc312bae9e219a20c0876a23e2066e8630796f9872ef495f440a63b81` |
| `include/noisemaker/generated/catalog.hpp` | `cb0a5785163273723e85c77b868b70beb92f5775f113117c4d246c6467f2b80f` |
| `tests/test_typed_slice.cpp` | `55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6` |

The review made no repository edit and used no Git, branch, worktree, pull request, or deployment operation. Current-byte canonicality is independently proven by `--check`; the report's historical claim that the generator writer was invoked exactly once is not independently observable from current bytes without prohibited repository-history inspection.
