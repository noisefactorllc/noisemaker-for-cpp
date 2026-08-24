# Final focused re-review: Shapes183 design

## Verdict

**GO for implementation.**

The stable final design closes all three Important execution-contract findings and both precision findings from the previous review. This is approval of the implementation design, not a claim that the port, parity suite, sanitizer/assembly gates, independent code review, or publication work is complete.

Reviewed design snapshot:

- Path: `/private/tmp/noisemaker-shapes183-design.md`
- Size: 31,516 bytes
- SHA-256: `e40ad1c0bb62c6797a270060498765823f072284b1b0a505f59644fe7bd4425f`

This focused re-review was read-only with respect to both repositories. It performed no builds, generation, Git actions, repository edits, or temporary-tree creation.

## Closed findings

1. **Frozen CPU oracle invocation: closed.** The design now defines `CPP_ROOT` and the immutable `CPU_ROOT` under the owned run root, invokes the checked-in C++-repository generator by absolute path with `--cpu-root "$CPU_ROOT"`, resolves every CPU import by real path, requires it to remain beneath the snapshot, and rejects live-checkout or foreign cache/import hits.

2. **Crop binding contract: closed.** The full route now binds full-sized `resolution`/`fullResolution` with zero `tileOffset`; the tile route binds tile-sized `resolution`, the same full-sized `fullResolution`, and the exact bottom-left translation. Only the other 15 runtime bindings are held identical before exact top-down crop comparison.

3. **Repository no-changed-byte audit: closed.** The design now records deterministic full pre/post manifests outside the retained-product allowlist with path, kind, size, full regular-file SHA-256, and symlink target, including dotfiles and pre-existing build/cache/scratch artifacts. Byte-for-byte equality makes modifications to existing non-transient files observable; the focused transient manifest remains an additional diagnostic gate.

4. **Non-empty define census wording: closed.** Every relevant count now explicitly says rows with non-empty `defines` maps; the authenticated census remains 25 -> 26.

5. **Current-versus-required numeric proof wording: closed.** The closure now relies on the runtime bit-pattern test *as extended in section 5*, including the exact controlled NaN-payload round trip, plus profile mutation tests. It no longer overclaims the current test.

## Final gate status

All original review areas are now design-complete: exact key/order/source/defines/resources, profile composition and censuses, scalar-XOR reuse, linear-sRGB and float-bits closures, canonical JS provenance, one-axis external/bound controls, custom exact comparer, full-array f32/RGBA8 parity, native ABI and immutability, mutation discrimination, exact alpha, historical 183-to-182 reconstruction, singular artifact ownership, generator freshness, Python/Debug/Release/sanitizer gates, ARM64/x86_64 assembly audit, bounded storage, and cleanup.

Implementation should proceed without widening these authorities. Any reproduced need for a new capability, tolerance, runtime primitive, alternate oracle, or repository cleanup outside the owned run root remains a stop-and-redesign condition.
