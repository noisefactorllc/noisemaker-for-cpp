# Task 16 proof-design review

## APPROVED

The proposed `filter/pixelSort:computeRank` slice is a genuinely minimal next
step after Task 15: it admits one discarded local-counter statement and does
not imply array, index, alias, parameter, or generic postfix support. The
brief's source/key/define/oracle boundary is sufficiently narrow. Approval is
for the following immutable-proof implementation contract; widening any part
of it requires a new review.

## Required proof shape

Use one frozen `DiscardedLocalCounterProof` attached to the exact expression
statement containing the body-level postfix. The builder should first clear
every existing counter proof, reconstruct the candidate solely from typed IR,
and attach no proof unless all conditions below hold. Both
`validate_capabilities()` and the C++ emitter must run the same pure
recomputation and require structural equality with the stored proof.

Record at least:

* proof kind; `main` function/signature identity; expression-statement and
  postfix-expression spans/identities;
* target symbol ID, exact signed `int` type, writable local storage, and its
  exact direct zero-literal declaration identity/span;
* the containing `for` statement identity and its pre-existing immutable
  `CountedLoopProof` identity: induction symbol `s`, start `0`, `<`, local
  const-literal bound `NUM_SAMPLES=32`, postfix loop-header update, 32 trips,
  and lexical/effective depth one;
* the direct enclosing conditional statement identity/control path, its
  one-branch/single-statement body shape, and the fact that there is no nested
  loop or second candidate along that path;
* number of permitted post-initialization writes (`1`), maximum updates per
  loop visit (`1`), visit bound (`32`), checked interval `[0,32]`, and target
  non-escape/read-only-after-loop facts.

This establishes `0 + 32 * 1` with checked arithmetic. `continue` is earlier
in the same loop body and can only skip the later conditional, so it reduces
the count. Do not attempt predicate satisfiability analysis; the syntactically
unique direct conditional statement is enough to prove at most one update per
visit for this source-locked slice.

## No generic postfix admission

Keep Task 15's loop-header update lowering separate. The generic expression
emitter must continue to reject `post`. Only the statement emitter may lower a
postfix, and only after exact counter-proof verification, as:

```cpp
++brighterCount;
```

The permitted AST shape is an expression statement whose sole expression is
`post ++` applied directly to the proved target ID. It is not an expression
value. Thus `(brighterCount++) + 1`, `f(brighterCount++)`, an assignment,
condition, constructor argument, swizzle/member/index target, prefix form,
or any other body post remains on the existing unsupported-expression path.

The proof scan must distinguish the already-admitted `s++` in the `for`
header from body postfixes; it must reject every body post except the one
proved statement, and reject all other writes to `brighterCount` (assignment,
compound assignment, prefix/postfix increment/decrement).

## Lock and recomputation boundary

Lock before candidate admission to exactly:

* key `filter/pixelSort:computeRank`;
* `TypedProgram.source` SHA-256
  `6ce61bb5cb69bb22ac51f48603d5b40755b1e3f700acad1bc685a1e8a4dea6a4`;
* manifest path `sources/filter/pixelSort/computeRank.glsl`, pinned revision,
  and exact empty define map;
* the typed structural control path/statement identities described above.

The generator already checks the corpus raw hash before parsing. For the
emitter's independent boundary, hash `program.source` itself and compare it
to both the supplied/generated source hash and the Task 16 expected constant;
do not trust only the `render_typed_cpp(..., source_hash)` argument. This
prevents a forged typed program from borrowing the expected external hash.

## Required negative matrix

Include all of the following at both validator and emitter boundaries where
applicable:

1. absent, stale, copied-from-another-statement, altered-span, target-ID,
   loop-ID, conditional-ID, proof-kind, interval, or multiplicity proof;
2. `brighterCount=1`, dynamic initializer, target write before/after the
   post, `brighterCount+=1`, decrement, prefix increment, and a second body
   post (same conditional, alternate branch, or nested loop);
3. changed local-constant/loop evidence, 33 trips, nonliteral/local bound,
   changed comparison/update, or forged visit/multiplicity values that
   overflow checked interval arithmetic;
4. every forbidden target class: float/uint/const/parameter/uniform/global,
   induction variable, member, swizzle, and index; and value-consuming post
   expressions;
5. wrong key, raw source digest, source path/revision, or non-empty define
   map.

Tests should mutate frozen typed IR after analysis, not only feed rejected
text, so equality-based proof validation is exercised. A second update in a
nested two-trip loop and two sequential updates in one visit are important:
they demonstrate the interval is a proof rather than an asserted `32`.

## Oracle and behavior review

The frozen oracle is valid and `--check` passes. Its artifact SHA is
`878959f2afb5d16889e546ba1ef0280b45c6cb6a7fbf4668c9a2c7310a4e5eee`; its
generator SHA is
`bf38cb756ab23c4d7a69b8f320bafe77481b251545fbe31585a6527196a98bab`.
Formula, flat-tie, and width-one together cover strict/equal predicates,
tie-breaking, continue skips, orientation, and the width-one `0/0` blue NaN.
Preserve the `0x7fc00000` lane and RGBA8 NaN-to-zero behavior; neither an
early return nor denominator guard belongs in this task.

The intended post-change accounting is exactly 108 typed / 110 public / 102
unported. Only `lumTex:sampler2D@1/S1` is bound, and only computeRank enters
the public catalog. The other pixel-sort passes and all six array-frontier
programs remain out of scope.

Reviewed artifacts: final brief SHA
`3e803c0b7748a79b19ec58784f4fd2085ad1f0375e93c3f04971b96f31bcbcbf`,
risk audit SHA
`9036ce534a4d7e853359a8a31d113272a9446040bbd7ddbcfa9e756eae7facc8`,
and scope/oracle review SHA
`7704438a0515b0a27470ddbbcdb559055355513f89164338f725374d3fc19c70`.

This review was read-only. No repository files or Git state were changed.
