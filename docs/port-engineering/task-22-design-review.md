# Final rereview of the amended Task 22 CRT brief and corrected implementation design

## Decision

**APPROVED.** The corrected Task 22 implementation design at SHA-256
`b2a22b5a0052464d6672e1817c93aed953d1c0f7c978fa1b27db2c81f7a71918`
fully resolves the sole prior cosine-census P1 and faithfully implements the
amended brief at SHA-256
`e4cd4f75959d61d4114187cd033a16d7a11a5a723cf068303312e00fa8fcfc10`.
There is no remaining P0, P1, P2, or P3 scope, semantic, oracle,
implementation-design, verification, or baseline finding.

This was a read-only review. I used no Git command, changed no repository file,
and updated only this requested review artifact outside the repository.

## Corrected cosine boundary

The design now freezes all four untouched cosine sites independently of the
six transformed sine sites:

| ID/name | Raw line | Normalized span | Expression SHA-256 | Argument SHA-256 |
| --- | ---: | --- | --- | --- |
| 118 `simplex_random` | 38 | `37:15-37:25` | `d73adbb7e0f3b9c5cb4eb121ac454f08d16cd19bb651b9b3bfb6ddf352fae17a` | `a07aef30bd37a38aa61216b37a41d239fb2e4c15d11c8e482e4d375443773048` |
| 91 `animated_simplex_value` | 199 | `198:20-198:30` | `aa8a39a243601c48cdaa3b328c2aeb5ee045908c55f154e1c7ba69058d29966e` | `c2f34dcdc8a5568dc56401f25a5efa331f0e8249102791bbc31b6c53c496fa6c` |
| 98 `compute_lens_offsets` | 258 | `257:25-257:35` | `9c88ea057347d9c9f968a43c5b9d0a289a689cf6166b8f19a8c7ff1586e64bd9` | `f5411ea9b54ceb2177a5dad5b00aa01be5ee2b51b3de5fd31b4c200981ea4169` |
| 94 `blend_cosine` | 330 | `329:27-329:44` | `f9a0165495911c862940e37195b8d97eba9709c3b6e42ce42b5822e4f152c95d` | `12f0dd4d11b4959aa15e80b6e3448aad888cc6252076d53195c0def86d51d240` |

Independent parsing of the pinned source reproduced every function ID, span,
expression hash, argument hash, signature `-8`, scalar `FLOAT` type, and
`rvalue` category. The design requires the exact four-row set in raw and post
trees, equal pre/post expression hashes, retained argument object identity,
and rejection of zero, three, five, changed, or transformed cosine sites.

The exact-transform test correspondingly requires four original cosines
matching the frozen identity/hash table. Generated-output inspection requires
exactly four `glsl::cos` calls in the complete CRT namespace, located in the
four frozen functions with no reduced-turn wrapper or other change. There is
no remaining stale three-site assertion.

## Amended brief and full design fit

The amended brief's earlier Ninja-only portability issue remains resolved:
Ninja is used only when present, with Unix Makefiles as the specified fallback
while retaining the same isolated directories, flags, builds, and CTest gates.

The corrected design also retains every reviewed fail-closed seam:

- validator and emitter independently invoke the same pure CRT post-tree
  authenticator;
- the transform retains each sine argument object and shares the same `turns`
  node between subtraction and `floor`, with explicit object-identity checks;
- transformation precedes proof attachment, pre-carried proof fields reject,
  and the post authenticator requires all four foreign proof fields absent;
- the exact expression path grammar includes the required root sentinel;
- all six sine sites, five changed functions, 35-function profile, pre/post
  whole/function fingerprints, and unchanged interface are frozen;
- the JS oracle owns all 18 semantic mutation sensitivities; the native test
  consumes only the 11 frozen cases, with exactly seven probes and 42 uint32
  probe words per case;
- `renderScale` remains a required runtime binding but is absent from public
  metadata parameters;
- the exact resource, alias, level-zero fetch, factory, metadata, binding,
  generated-isolation, stack, sanitizer, and disassembly gates remain closed;
  and
- the implementation inventory remains limited to the ten declared Task 22
  paths, with all accepted Task 21 anchors protected.

## Fresh verification

- `node docs/port-engineering/task-22-oracle-generator.mjs --check`
  completed with `ok task-22-oracles.json`.
- The pinned 19,560-byte CRT source still hashes to
  `62d915eda8e20a458b1df91198cee3e85f0f0b9676cd4d0777264e9cd8b99b7c`.
- Prior independent reconstruction remains valid: all six sine-site hashes,
  five changed-function hashes, aggregate profiles, projected inventories,
  generated CRT block/sentinel hashes, alias/resource/fetch surface, acyclic
  depth-six call graph, and static stack classification matched the design.
- The independently compiled projected CRT block reproduced all 11 frozen
  public-adapter F32 and RGBA8 hashes, 22 of 22.

## Reviewed identities

| Artifact | Recomputed SHA-256 |
| --- | --- |
| Amended `task-22-brief.md` | `e4cd4f75959d61d4114187cd033a16d7a11a5a723cf068303312e00fa8fcfc10` |
| Corrected `task-22-implementation-design.md` | `b2a22b5a0052464d6672e1817c93aed953d1c0f7c978fa1b27db2c81f7a71918` |
| `task-22-frontier-audit.md` | `c3d006f354f6ca9bb65c42b8e6f8bbdac194ddf1a6486ccbf890bfe818f16160` |
| `task-22-oracle-generator.mjs` | `dc2044ee2bf007f1888f958a09185445caef34c064a6e4b3eea340a09ad49a27` |
| `task-22-oracles.json` | `c927f467418f9ef154a817869228a0918c2fc222ef3bb64f2b0a6bab8a74e889` |
| `task-22-oracle-report.md` | `36ac4f8b85a0fefc47c403eef47bd11ceb40e9774fa709125f01bc4e2ea075aa` |

The amended brief and corrected implementation design are ready for Task 22
implementation on the accepted Task 21 baseline.
