# Task 19 corrected scope/proof/ABI/oracle re-review

## Decision

**NOT APPROVED.** The corrected design substantively resolves both prior
findings, and the supplemented oracle is a valid eight-case direct-canonical
contract. However, the frozen brief retains one acceptance-count contradiction
and one false explanation inside the newly added compatibility clause. These
are narrow documentation defects, not failures of the proposed transform,
array ABI, stack design, or generated oracle, but they must be corrected before
the brief can be treated as an unambiguous frozen implementation contract.

This was a read-only repository review. I invoked no Git command and changed no
repository file. This `/tmp` report is the only file written.

## P2 - native oracle acceptance still says four cases, not eight

The corrected brief freezes eight direct canonical cases:

- the original three mode-one array cases and one mode-zero control; and
- four additional mode-one compatibility cases for `blendMode` 2, 3, 7, and
  15.

Lines 70 and 72 correctly require native tests to match the added canonical
cases and consume the recorded hashes/probes. But acceptance line 79 still
requires only **"Four native frozen oracle cases in strict Debug/Release."**
That directly conflicts with the eight-case contract and permits an
implementation to claim the enumerated acceptance bullet using only the
original four cases. This matters because those original cases use blend modes
5, 13, 17, and 10 and cannot detect a missing or scalarized four-site
compatibility transform.

Change line 79 to require **all eight native frozen oracle cases** in strict
Debug and Release (or explicitly enumerate four base plus four compatibility
cases). Keep the existing requirement that every compatibility case match the
canonical F32/RGBA8 hashes and probes and reject scalar `Vec ==` emission.

## P3 - compatibility rationale describes an assignment that canonical JavaScript does not perform

Brief line 20 says the typed-array condition is truthy, **"so each true arm
assigns the same operand already held by `middle`"**. That is not the pinned
runtime behavior and the operand is not already held by `middle`:

- authored source declares `vec4 middle;`, which canonical JavaScript realizes
  as a zero-filled `PooledFloat32Array`;
- `color1` and `color2` are separate copied input vectors and are generally
  nonzero; and
- at canonical runtime lines 6346, 6349, 6361, and 6385, the truthy true arm is
  a bare `color1`/`color2` expression. The `.reduce(..., middle)` write exists
  only in the false arm, so no assignment to `middle` occurs.

The remainder of line 20, proof item 10, oracle report, JSON contract, and
hashes all specify the correct result: the four selected branches leave
`middle` unchanged at zero. Therefore this does not invalidate the transform
design or oracle. Replace the quoted phrase with, for example, **"so each bare
true arm performs no write to `middle` and the authored assignment becomes a
canonical no-op."**

## Prior P1 transform design - resolved after the two wording fixes above

The corrected brief now requires exactly the missing compatibility boundary:

- one Refract-specific transform locked to key, source, `blend(vec4, vec4)`
  signature, assignment target, blend-mode control arms, vector operands,
  constants, true symbols, false expressions/builtins, and ancestry;
- exact sites for blend modes 2, 3, 7, and 15 only, with no generic change to
  vector equality or ternary semantics;
- zero/missing/duplicate/near-match rejection;
- transform execution before array proofing and before reconstruction of the
  hard-coded whole-program fingerprint; and
- independent validator and emitter authentication of the exact
  post-transform tree, rejecting untransformed, partial, altered, and forged
  variants.

That ordering closes the prior authentic-source/untransformed-IR hole. Proof
item 10 also explicitly requires all four sites already transformed and
forbids transformation of any other conditional or blend arm.

## Supplemented eight-case oracle - verified

`node docs/port-engineering/task-19-oracle-generator.mjs --check`
completed with `ok task-19-oracles.json`. The JSON has exactly eight uniquely
named cases and retains the pinned source, factory, runtime, binding, fixture,
orientation, F32-word, full-hash, probe, and repeat-identity provenance.

The four new direct-canonical mode-one cases select exactly blend modes 2, 3,
7, and 15 under a common repeat/29.9f/137.6f/exact-half context. Each freezes:

- F32 SHA-256
  `165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24`;
- RGBA8 SHA-256
  `13a15bd48e6f739c5ec9e3f08affe0fe2c115418341a3b2e1742d8d3868e03e0`;
- three probes with exact zero RGB words and preserved nonzero sampled-alpha
  words; and
- byte-identical repeated F32 and RGBA8 renders using fresh surfaces.

The report records a distinct scalar-all-lanes-boolean mutant hash for every
affected mode. The generator binds the pinned canonical factory directly and
does not reimplement blending or the array path. Thus the external contract
now detects the exact semantic failure identified in the first review.

## Prior P2 stack design - resolved

Acceptance line 82 now requires Debug and Release `.su` evidence for `pixel`,
`derivX`, `derivY`, `convolve`, and optimizer-created/inlined clones, with
static/dynamic classification. It separately requires the maximum non-inlined
mode-one call-chain sum and, when Release inlines, the containing-frame record
plus code/disassembly evidence. It explicitly keeps that maximum dynamic path
separate from the independently proved 144-byte raw live table payload.

This closes the prior loophole where an isolated `pixel` or `convolve` frame
could be reported without the simultaneously live caller `Kernel9` and callee
`Offsets9` path.

## Regression check

No additional P0-P3 issue was found in the corrected transform mechanics,
post-transform proof ordering, array ownership/liveness, const-reference ABI,
Number-versus-F32 storage, exact loop/index census, exclusions, provenance,
bindings, counts, or generated eight-case oracle. The two findings above are
confined to the frozen brief's wording and acceptance enumeration.

Verified current artifact hashes:

- corrected brief:
  `568918d50d5cdaacc4ade642f9af0d08666553fddf79f6462b9474319a84f462`
- oracle generator:
  `a9ff40af61e15c6a73c34a8b844ca2f41da5be1d2ae85e957d2805a8da0d7a30`
- oracle JSON:
  `169cb5607777051de3962fdbedd32d7dab4ac2095d6b356041c48bccc3c41c88`
- oracle report:
  `ad053999676b49e0c75907bf66c2ec12678d99934571bfde7d1ebdcd1a113b1d`
- unchanged risk audit:
  `cba1e6b5c9e8f5d95dda761b07c46798e9bdb9ee92a231cdff504e804f8b880e`
- pinned canonical runtime:
  `e605746c74e0e60e513724669f948b353caca4d3c427f339950d5dc98815ab56`
- pinned raw Refract source:
  `d9675b5de9c329aa619f4ef68129611faac8cbe515b6e80aa8528c593a49cfa2`
