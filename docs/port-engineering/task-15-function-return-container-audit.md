# Task 15 function-return container provenance audit

## Finding

The remaining `synth/cell:cell` one-ULP mismatch is an interprocedural container-provenance error, not a PCG, loop, or scalar-arithmetic error.

The canonical `prng` helper returns the result of a JavaScript `.map(...)` chain as an ordinary `Array`; its lane values therefore remain JavaScript Numbers.  At the caller, the scalar vector maps in

```glsl
prng(vec3(float(seed), wrap)) * 0.5 - 0.25
```

remain F64 until a genuine downstream GLSL consumption/storage boundary.  The debug trace identifies the first divergent neighborhood site as `(0,0)`: canonical `site-post` is `0.04080832330160025`, while the materialized native path is `0.04080832377076149`; the canonical final stored lane is Float32 bits `0x3d2726a1`.

The emitter already has the right conceptual hook: a signature-level ordinary-array return classification.  Its current return lowering defeats that classification by emitting an intermediate concrete vector:

```cpp
glsl::FloatExpr<3>(glsl::Vec3(return_expression))
```

`Vec3(...)` is an explicit Float32 storage boundary, so it rounds the helper's F64 return lanes before the caller can run `* 0.5` and `- 0.25`.

## Recommended narrow general rule

Add a **canonical return-container provenance summary** per user-function signature.  It is independent of the GLSL declared return type and answers only:

`Does this exact canonical helper return an ordinary JavaScript Array of float-vector lanes?`

For an admitted ordinary-array-return signature:

1. Emit the C++ helper return type as `glsl::FloatExpr<N>` rather than `glsl::VecN`.
2. Return the already-emitted expression directly as `FloatExpr<N>`; do not construct `VecN` at the return statement.
3. Treat a direct call of that signature as ordinary-array provenance.  Propagate it through vector-scalar arithmetic only, so chained `.map()`-equivalent operators remain F64.
4. When a GLSL vector local is initialized from that provenance, declare the local `FloatExpr<N>` only for the lifetime of the ordinary-array chain.  Materialize `VecN` exactly at existing consuming boundaries: an explicitly concrete vector assignment, vector builtin, texture/binding/output storage, or a consumer whose canonical path materializes a `Float32Array`.

The summary must be fail-closed.  A vector-returning function qualifies only when every reachable return expression has the same independently recognized ordinary-array provenance.  The classifier may begin with the current exact canonical shape—vector conversion of an integral-vector call followed by scalar map arithmetic—but it must be named and modeled as return-container provenance, not as a broad "integral call" feature.  Reject mixed return paths, a return of a parameter/local with unknown container species, recursive/unresolved summaries, indirect or overload-ambiguous calls, and any signature lacking an exact canonical lowering proof.

For the concrete `prng`, the required generated shape is conceptually:

```cpp
[[nodiscard]] glsl::FloatExpr<3> prng(...)
{
  return /* existing FloatExpr-producing mapped expression */;
}

[[maybe_unused]] glsl::FloatExpr<3> r1 =
    prng(...) * 0.5 - 0.25;
```

There must be no `glsl::Vec3(...)` between the helper return expression and the caller's scalar-map chain.

## Why this is the narrowest safe rule

- It preserves the typed GLSL surface (`vec3`) while adding only canonical execution-container information at direct helper boundaries.
- It does not make all vector function returns F64, nor does it reinterpret GLSL vector storage globally.
- It does not alter integer PCG, Float32 constructors, vector-vector operation boundaries, swizzle semantics, or final output storage.
- It uses stable signature IDs, so same-name overloads cannot inherit provenance accidentally.
- It introduces no heap allocation, shared state, changed ABI binding, or new loop/derivative behavior.

## Risks to guard against

1. **Return-site rematerialization:** wrapping the expression with `VecN` before `FloatExpr<N>` repeats the current bug.  The ordinary-array return must be direct.
2. **Over-promotion:** inferring F64 from the declared `vecN` return type, a function name, or merely any vector call would move Float32 boundaries for unrelated helpers.
3. **Mixed control flow:** `if`/`else` returns with different canonical container species must reject instead of selecting a convenient common C++ representation.
4. **Escaped provenance:** passing a `FloatExpr` into an arbitrary helper, storing it in a normal `VecN` local, or using it through an unsupported builtin must consume/materialize at the known boundary unless that exact callee has its own proven summary.
5. **Signature mismatch:** classification must key on `signature_id`, not helper spelling; invalidation must occur when the typed return expression or call graph changes.

## Required tests

- A focused `synth/cell` oracle reproduces the logged `(0,0)` neighborhood trace and requires the canonical final Float32 bit pattern `0x3d2726a1`, exact F32 hash, RGBA8 hash, and repeat render.
- Generated-source assertion for `prng`: declaration and definition return `glsl::FloatExpr<3>`; the return statement contains no `glsl::Vec3(`; the `r1` initializer/lifetime remains `FloatExpr<3>` across both scalar operations.
- A synthetic exact-shape helper verifies that integral-vector conversion has its established boundary, while subsequent scalar maps retain F64 through return and caller arithmetic.
- A contrasting ordinary vector helper that canonically returns a concrete `Float32Array` remains `VecN`; its caller scalar operation must materialize at the existing Float32 boundary.
- Negative semantic/emitter tests reject multiple return sites with mixed provenance, return of an unclassified parameter/local, recursive summary dependency, an overloaded same-name callee, and an attempted propagation through an unsupported builtin/callee.
- Boundary tests cover direct swizzle, builtin consumption, assignment to a concrete GLSL vector, and output storage, confirming each still performs exactly one Float32 materialization where canonical execution does.

## Evidence consulted

- `docs/port-engineering/task-15-debug-cell.log`: canonical and materialized values diverge at the `(0,0)` site before final output; canonical final bits are `0x3d2726a1`.
- `tools/glslcpp/emit_typed_cpp.py`: signature classification/provenance hooks and the return-site `FloatExpr(VecN(...))` materialization path.
- `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/synth/cell/cell.glsl`: `prng` source and caller scalar-map chain.

This is a read-only audit.  It makes no repository change and does not merge the active Task-15 correction or claim it is implemented.
