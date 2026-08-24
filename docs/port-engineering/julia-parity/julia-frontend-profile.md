# Julia typed-frontend admission

`synth/julia:julia` is the standalone Julia adapter. It is not the Julia
helper embedded in `classicNoisedeck/fractal`; the adapter owns its own
canonical factory and its own 21-uniform runtime ABI.

This prepared-only admission record is bound to corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6` and source SHA-256
`825e175c22fea086ad2860e16bcf0a79d797574a9dfad937a23baaadaffdeef0`.
The normalized frontend source is 9,423 bytes with SHA-256
`ea70d41e7eef508a0fcfb816b13132e771d2d09f706d8f6eec9668cfe593078c`.

The exact frontend census is:

- 19 functions, one `JuliaResult` struct with seven scalar fields, and 24
  member-access nodes;
- four `out` parameters: `df64_split.hi/lo` and
  `transformCoords.reDF/imDF`;
- two counted loops, each with literal bound 1000, effective depth 1, and
  entrypoint charge 3000;
- 1,089 identity-disjoint declaration/function/expression objects in the
  authenticated proof ledger.

The future typed row must carry both effect-specific companion contracts:
`struct_declaration_profile` and `out_inout_admission_profile`. The row is
deliberately not registered in `KEYS` until those shared emitter lanes are
implemented and the native pixel oracle is exercised by the full C++ matrix.

The exact-pixel authority package is in this directory:
`julia_oracle_generator.mjs`, `julia-oracles.json`, and the fail-closed
`generate_julia_native_oracle_include.py` materializer. It captures eight
Float32/RGBA8 cases and 23 independent source mutations with zero tolerance.
