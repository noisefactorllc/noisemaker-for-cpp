# Task 28 design preflight report

## Verdict

**DESIGN COMPLETE; IMPLEMENTATION READY. No known blocker.** The frozen slice
is exactly `filter/rotate:rot` under `rotate-mat2-return-v1`. No repository or
Git state was changed by this design task; all new artifacts are under `/tmp`.

## Fresh selection evidence

Current state independently recomputed as 212 corpus / 127 typed / 129 public /
83 publicly unported, with the accepted Task27 ordered hashes. Adding only
Rotate projects 128 / 130 / 82, ordinal 67, typed/public hashes
`30f0333c...` / `102f5436...`.

A fresh pass over all 85 corpus entries absent from the typed spec (including
the already-public manual Invert and Solid) proved Rotate is the only new key
that passes the existing emitter. Its sole validator blocker is the blanket
matrix-return rejection. Focus Blur passes validation but has a later sampler-
parameter emitter blocker. No lower-risk, no-later-blocker candidate exists.

Fresh source/semantic analysis reproduced every frozen raw/normalized,
function, whole-program, interface, binding, helper, constructor-child, call,
parent, matrix cardinality, and profile-tuple hash in the brief. The exact
public CPU factory is `canonicalFactory127`, the public object is canonical
identity, and the adapter entry is absent.

## Oracle and projection evidence

`node task-28-oracle-generator.mjs --check` passes. Six non-square quadrant
cases cover all three wraps and stationary/positive/negative animation. Five
factory mutations prove constructor, child, matrix-layout, and return-shape
sensitivity. Six direct inputs crossed with six explicit modes freeze matrix
lanes and product bits; the four wrong value/layout modes diverge, while the
helper-local return is value-identical with a distinct structural witness.

The current emitter rendered the exact source without bypassing validation.
Wrapped as an isolated normal generated translation unit, it compiled under
C++20 with `-Wall -Wextra -Wpedantic -Werror -ffp-contract=off`. Release AArch64
disassembly of `rotate2D` showed a fixed 32-byte frame and direct four-float
return in `s0`-`s3`; no hidden sret pointer or indirect dispatch appeared.
This is projection evidence only and must be repeated on canonical final code.

## Baseline gates

- corpus `--check`: PASS;
- canonical generator `--check`: PASS at 127 programs;
- Task27 and Task28 frozen oracle `--check`: PASS;
- fresh `/tmp` Debug warnings-as-errors configure/build: PASS;
- fresh Debug CTest: 1/1 PASS in 3.42 seconds;
- focused accepted Task27 Python class rerun: PASS.

## Frozen artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| `task-28-frontier-audit.md` | `972e8e1d89ed9260674a040b60d639aa6c321e675ce20447b4126e52653385a9` |
| `task-28-recompute.py` | `44f556acf1c8e812ae8a1085f041b1cf8af3f3152d55f1731b6c76d736d9e28a` |
| `task-28-recomputed.json` | `38bd8b45d48e8da06c8b1f3bcd3e3162bbc48d6619ae960a2319bbbca08ca267` |
| `task-28-oracle-generator.mjs` | `b3f5f1b25989cb10c94922b9a0b4612fab3d8f360df697e79318438d6486a17a` |
| `task-28-oracles.json` | `db74b7e1883c1d9f71ec00caa80451793c404039bfd26943be4844faaeef3b44` |
| `task-28-oracle-report.md` | `8eea0603b37673ec50531f1b1bfe895f257286e839f4a75b5ea43066c3559b0f` |
| `task-28-brief.md` | `57291c23f8c42145efa25cda83efeb962ef82bb53849242aa1585d9224d3dbcd` |
| `task-28-implementation-design-final.md` | `6791164c2d85c66fe1a6a843bd275cbcb9b6f5d5e5b36fb77c071ef6a50450a5` |

## Implementation gate

Use the exact owned-file allowlist and TDD order in the final design. The
review-sensitive requirements are explicit: at least 45 named single-axis
candidates with matching preconditions; independent validator/emitter
authentication; actual post-Task28 removal and full Task27 regeneration;
distinct fail-closed executable mutation arms; authentication and tampering of
every C++ table field including both mode ID and name; final pixel/ABI/
sanitizer/stack/disassembly/prior-oracle gates. No blocker remains.
