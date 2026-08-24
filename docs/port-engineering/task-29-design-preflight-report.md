# Task 29 design preflight report

## Verdict

**DESIGN COMPLETE; IMPLEMENTATION READY. No known blocker.** The frozen target
is exactly `mixer/focusBlur:focusBlur` with two exact `const Surface&` helper
parameters under `focus-blur-borrowed-sampler-parameters-v1`.

Fresh recomputation reproduced accepted Task28 at 212/128/130/82 and projected
Focus alone to 129/131/81 with exact hashes/ordinal. Source, normalized tree,
interface, helper/body/parameters/uses, two branch-owned calls, their complete
ancestry, exact predicate/if/then/else objects and argument IDs, public
canonical identity/no adapter, loop proof, four static
sample and four static size-query sites all authenticate. The maximum path is
exactly 67 texture samples plus separately 67 textureSize evaluations.

The prior six-case oracle was not trusted blindly: it was rerun against pinned
provenance and reproduced byte-for-byte. The refreshed oracle adds eight
genuinely executed ABI modes with named-branch wrong-order discrimination,
real owned copies, execution-derived counters/witnesses, exact switch coverage,
semantic signature uniqueness, and invalid-enum rejection. The
adversarial audit independently compiled the `const Surface&` projection at
O0/O2 and found no downstream blocker. Its lifetime/alias/no-concurrent-write
contract, canonical frontend `writable=True` fact, recursive use census,
consumed-object counts, and non-vacuous mutation rules are incorporated into
the brief/design.

Baseline corpus and generator checks pass. A fresh Debug warnings-as-errors
configure/build and CTest pass 1/1 in 3.91 seconds; no repository or Git state
was changed by this design task.

Implementation must use strict TDD and the exact owned-file allowlist, recreate
the real Task28 tree for isolation, and finish with full parity, bindings,
lifetime, sanitizers, stack/disassembly, prior-oracle, and independent-review
gates. Generic sampler types, ownership, nullable/mutable references, retained
borrows, runtime changes, and vacuous mutation modes are explicit stop
conditions.
