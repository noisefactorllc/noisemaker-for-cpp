# Task 15 final independent review

## Verdict: findings — not approved

The completed artifacts, loop proof for admitted programs, bindings, counts,
defines, exclusions, and external oracle coverage are otherwise consistent
with the frozen Task 15 brief and implementation report.  One fail-closed
contract gap remains: recursive call graphs with no counted loop are accepted.
The brief requires call cycles to be rejected, without a no-loop exception.

## Finding F1 — no-loop recursion bypasses the cycle rejection

**Severity: P1 (fail-closed scope breach).**

`summarize_counted_loop_proofs()` detects any recursion and reports
`call_graph_acyclic = False` (`tools/glslcpp/frontend/loop_proof.py:292-312`).
However, `validate_capabilities()` only raises for that failed program proof
when `loop_count` or `unproved_loop_count` is nonzero
(`tools/glslcpp/generate_typed_slice.py:713-732`).  Thus a cyclic helper graph
with no loop is accepted by the same typed-generator validation entrypoint;
the emitter can then output directly recursive C++ functions.

Reproduction (read-only, current implementation):

```python
source = '''out vec4 fragColor;
float a(){return b();} float b(){return a();}
void main(){fragColor=vec4(a());}'''
typed = analyze_program(parse_program(source, "cycle_no_loop"), "cycle_no_loop")
generate_typed_slice.validate_capabilities(typed, generate_typed_slice.APPROVED_CAPABILITIES)
# accepted
```

The analogous graph containing an admitted loop is rejected, proving the
missing gate rather than a parser/semantic limitation.  The existing negative
matrix covers loop-header/control forms and charges but has no no-loop-cycle
fixture (`tests/test_typed_generator.py:1309-1344`).

Required correction: reject `not recomputed_program_proof.call_graph_acyclic`
unconditionally in both the generator validator and the emitter's independent
proof validation, and add a no-loop recursive helper rejection regression.
This does not require broadening support or changing the 36-key slice.

## Verified evidence

* Brief SHA-256 is `5c50686a46eec3860e39cc77e1765e0339dd74109df110b1c3042aa35870d0e8`;
  implementation report SHA-256 is
  `633ba2463b02d664134c4e1cad1fa281ad3247f963f10497864cc63e22462206`.
* Generated artifact hashes exactly match the report: typed C++
  `d4c33446716290f79a1d02749a6d0301ea35c1caf8e2a995ba64aae2591fac9b`,
  manifest `9eebfb8fb293e2acbfa6bb92d9e6fc96ece789ab67455707f459e93fd9e56bae`,
  slice declaration `d90f5018f6ed53373bf815f32412d750d113183ba8b04d4bc30f8740a916b5cb`,
  and catalog header
  `ea681d1d4c1781f90a0af7a675dcad286517581047074b2fb3d7a00f5d2a6cde`.
* `generate_typed_slice.py --check` reports exactly 107 programs.  Manifest
  inspection found 107 sorted unique keys, all 36 admitted Task 15 keys, the
  required non-empty define maps, and none of the eight explicitly deferred
  keys.  The public catalog test fixes 109 sorted factories; 212 corpus minus
  109 leaves 103.
* `task-15-oracle-generator.mjs --check` verified the pinned oracle SHA
  `e001c89f58ac970206a50dbf0974ce096e6fd71b5a3f2e389e315b0cfb16bdc8`
  with 38 vectors.  The current focused native executable reports all 95
  tests passing, including all 38 Task 15 exact/repeatable F32/RGBA oracles,
  235 binding checks (189 uniforms/46 samplers), reverb extrema, and the
  scalar-provenance assertion.
* The ordinary-array precision behavior is represented in the emitter's
  explicit provenance logic and dedicated generator/runtime tests.  The
  Task 15 table keeps authored `lowPoly.edgeStrength` as exact double `0.15`,
  while `mandala.aspect` is the correctly widened F32
  `1.2857142686843872`; the explicit regression is at
  `tests/test_typed_slice.cpp:2425-2436`.  Vector uniforms remain Float32,
  which is the review-approved limited scope.
* Focused checks completed successfully: `tests.test_semantic`,
  `tests.test_typed_generator`, `check_semantics.py --check`, and
  `check_corpus.py --check`.

## Scope conclusion

The requested eight deferred programs remain outside the 107-key typed slice:
the six global-`const int` cases, focusBlur's sampler helper parameter, and
gabor's effective depth four are absent.  No repository files or Git state
were changed during this review.
