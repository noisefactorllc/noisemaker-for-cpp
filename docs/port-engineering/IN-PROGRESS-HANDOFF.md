# Handoff — tree is GREEN

**Superseded the earlier "mid-edit" warning: the tree builds and passes.**

- **170 typed of 212** (171 ported, counting the wormhole scatter pass)
- All four generator gates exit 0
- Native **176 PASS / 0 FAIL**
- Snapshot: `~/platform/.noisemaker-cpp-snapshots/green-170.tar.gz`
- Full Python suite: running on a copy at `/Users/aayars/platform/.nm-validate/v171/`
  (log `v171.log`) — **check it before trusting this state completely.**

## What landed most recently

`filter/fxaa`, `filter/oilPaint:oilFlatten`, `filter/smooth:smoothBlend`, plus
three reusable mechanisms:

1. **`ceil_admission_profile.py`** — dict-keyed node-identity profile, both
   authorities, in the skip-list so the frozen 44-entry vocabulary is untouched.
   Documents why it needs NO narrowing shim where `round` does: `Math.ceil` and
   `std::ceil` agree on every finite double, while the reference `round` is
   `Math.round` (half-toward-+inf), matching neither the GLSL spec nor
   `std::round`.
2. **Lane-wise `uvec >> uvec`** — runtime overload masking each count mod 32
   per lane, plus both gates widened. Stays inside the existing
   `uint-vector-bitwise` capability.
3. **Loop-return admission** — widened in BOTH authorities, each carrying the
   soundness note (an early return can only shorten iterations relative to the
   proved upper bound, never extend them). The near-miss barrier was **re-armed
   one step out**, not removed: `unproved-loop-return` and `unproved-do-return`
   now hold the boundary and were verified still rejecting.

## Two traps worth carrying forward

**Slice rows must be inserted in sorted position.** Putting `smoothBlend` after
`smoothEdge` tripped `keys != sorted(set(keys))` — and that condition is a
14-clause `or` chain that raises ONE generic message naming its last clause
(`literal vec3 lane profile drift`). The message will point at profiles when the
real fault is ordering. Check `ks == sorted(ks)` first; it finds it in one step.

**Both authorities enforce independently.** Widening a gate in the validator is
half the job — the emitter has its own copy. Loop-return had to be widened in
both, and each now carries the same justification.

## Next steps

`docs/port-engineering/FRONTIER-2026-08-13.md` has the live blocker probe for
all remaining programs plus the eight-step profile-authoring recipe. Re-run that
probe before planning anything — the census is stale and seven batches have
broken on it.
