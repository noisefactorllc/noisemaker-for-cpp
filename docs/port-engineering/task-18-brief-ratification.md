# Task 18 current-brief byte ratification

## Decision

**APPROVED AND RATIFIED.** Current `task-18-brief.md` SHA-256 is
`11628e7d2aa25450e2988e35614c931094d4254f216f374e23a78b2401aa0684`.
Relative to the independently approved corrected design at SHA-256
`8ea81afc0f9488c533bafc372ea92565f2237ee0e473ebef313503b940d8719b`,
the current bytes differ only by the two claimed administrative edits. No
substantive proof, oracle, implementation, test, acceptance, scope, count,
provenance, ABI, or authorization requirement changed. No P0-P3 issue remains.

This was a read-only repository review. I invoked no Git command and changed no
repository file. This `/tmp` ratification is the only file written.

## Exact byte comparison

The recorded post-approval patch contains exactly these two hunks:

1. Status replacement:

   ```diff
   -Status: corrected frozen design after pre-implementation P1/P2 review; implementation may begin only after Task 17 acceptance and independent re-review.
   +Status: corrected design independently APPROVED with no remaining P0-P3; implementation remains gated on Task 17 acceptance.
   ```

2. One added artifact line immediately after the unchanged oracle-report hash:

   ```diff
   +- Corrected scope/proof rereview SHA-256: `9f67a898fe99302f1f1f92fe409c089f775c22e45cb19d52dc9ec756e357ec5f`.
   ```

I independently reversed exactly those two edits in a byte stream generated
from the current file: restored the former status line and deleted the exact
rereview-hash line. The resulting stream hashes to:

```text
8ea81afc0f9488c533bafc372ea92565f2237ee0e473ebef313503b940d8719b  -
```

That exactly equals the corrected brief hash named by the approving re-review.
There is therefore no unaccounted byte difference between the approved design
and the current design body.

## Substantive contract check

The unchanged current body still requires:

- exactly the two source-locked Cel-edge and Outline-Sobel keys and projected
  counts 112 typed / 114 public / 98 publicly unported;
- independent raw/normalized-source and empty immutable-define provenance at
  both validation and emission boundaries;
- the exact `float[9] samples`/`idx` whole-program census, prefix-unary
  `++ky`/`++kx` headers, nine bounded dynamic stores followed by discarded
  `idx++`, exact literal Sobel reads, early-return dominance, and forged-tree
  rejection;
- source-specific zero-initialized `std::array<double, 9>` lowering, direct
  proved indexing, `noexcept`, fixed hot-path operations, and no generic array,
  postfix, allocation, ABI, resource, callback, or dispatch expansion;
- the unchanged six-case direct-canonical F32/RGBA8 oracle contract, exact F32
  uniform/divisor boundaries, probes, orientation, repeat identity, and
  `--check` gate;
- structural both-boundary and emitted-code verification of the public-API-
  unreachable zero-dimension early return, with no unauthorized sampler/test
  seam; and
- strict Debug/Release native verification, CTest, hot-loop inspection,
  `-fstack-usage` evidence, complete tamper/binding matrices, and the explicit
  no-Git/no-branch/no-worktree/no-publication boundary.

The new status text only records the already-issued approval while preserving
the Task 17 gate. The added SHA line correctly names the current approving
re-review artifact, whose independently verified SHA-256 is
`9f67a898fe99302f1f1f92fe409c089f775c22e45cb19d52dc9ec756e357ec5f`.

## Ratified hashes

- Current Task 18 brief:
  `11628e7d2aa25450e2988e35614c931094d4254f216f374e23a78b2401aa0684`
- Approved corrected-design brief before administrative edits:
  `8ea81afc0f9488c533bafc372ea92565f2237ee0e473ebef313503b940d8719b`
- Corrected scope/proof re-review:
  `9f67a898fe99302f1f1f92fe409c089f775c22e45cb19d52dc9ec756e357ec5f`
