# Task 31a: emitter reserved-identifier guard

Date: 2026-08-12
Author: integration owner

A latent emitter defect, discovered while implementing Task 31 and fixed as its
own self-contained change. It is a **prerequisite for ten unported programs**,
not a Caustic-specific workaround.

## The defect

The emitter binds `state`, `context`, `output`, and `kernel_base` inside every
generated pixel function and helper signature, but stored GLSL local and
parameter names raw, with no collision check. A GLSL local named `state`
therefore shadowed `const State& state`, and generated C++ failed to compile:

```text
src/typed_generated/typed_slice.cpp:241:32: error: redefinition of 'state' with
  a different type: 'glsl::UVec3' (aka 'Vec<3, unsigned int>') vs 'const State &'
src/typed_generated/typed_slice.cpp:242:44: error: no matching function for
  call to 'pcg'
```

```cpp
[[maybe_unused]] glsl::UVec3 state = glsl::bitwise_xor(...);
[[maybe_unused]] glsl::UVec3 prngState = pcg(state, context, state);
```

The helper received the local `UVec3` where a `const State&` was required.
This is a silent-shadowing class of bug: in a case where the types happened to
be compatible it would have compiled and produced wrong pixels.

## Scope — measured, not assumed

A census of all 212 corpus programs (parsing each and inspecting
`declaration`-kind expressions and function parameters) found:

- **0 of 130 currently-typed programs** declare a colliding name.
- **10 unported programs** declare a local named `state`:

| Program | Colliding local |
|---|---|
| `classicNoisedeck/bitEffects:bitEffects` | `state` in `randomFromLatticeWithOffset` |
| `classicNoisedeck/caustic:caustic` | `state` in `randomFromLatticeWithOffset` |
| `classicNoisedeck/kaleido:kaleido` | `state` in `randomFromLatticeWithOffset` |
| `classicNoisedeck/moodscape:moodscape` | `state` in `randomFromLatticeWithOffset` |
| `classicNoisedeck/noise:noise` | `state` in `constantFromLatticeWithOffset` |
| `classicNoisedeck/shapeMixer:shapeMixer` | `state` in `randomFromLatticeWithOffset` |
| `classicNoisedeck/shapes:shapes` | `state` in `randomFromLatticeWithOffset` |
| `filter/osd:osd` | `state` in `pcg` |
| `synth/noise:noise` | `state` in `constantFromLatticeWithOffset` |
| `synth/shape:shape` | `state` in `randomFromLatticeWithOffset` |

That is ten of the ~79 remaining programs — about 12% of the frontier — that
would each have hit this wall.

Because no typed program collides, the fix is **provably byte-neutral today**.

## The fix

`tools/glslcpp/emit_typed_cpp.py`:

```python
_RESERVED_IDENTIFIERS = frozenset({"state", "context", "output", "kernel_base"})


def _safe_identifier(name: str, symbol_id: object) -> str:
    """Mangle only names that would shadow an emitter-bound identifier."""
    if name in _RESERVED_IDENTIFIERS:
        return f"{name}_glsl_{symbol_id}"
    return name
```

Applied at all five naming sites: local declarations, the counted-for induction
variable, source-global closure locals, function-parameter registration, and
both function-signature spellings.

Mangling is keyed on the stable symbol id, so it is deterministic and cannot
collide with another mangled name. It follows the existing precedent for
shadowing locals (`{name}_{symbol_id}`), and only fires on the reserved set —
every other identifier is emitted unchanged.

## Verification

**Byte-neutrality for all 130 typed programs:**

```text
python3 -m tools.glslcpp.generate_typed_slice --check   exit 0 (130 programs)
src/typed_generated/typed_slice.cpp
  5765f8637fd08711cb665c295b7f1488f76fc2c19515b22d72c476e51808b5f3  (unchanged)
```

`--check` regenerates in memory and fails on a single differing byte, so this is
a proof, not a spot check.

**The guard resolves the collision.** Rendering Caustic now emits:

```cpp
[[maybe_unused]] glsl::UVec3 state_glsl_146 = glsl::bitwise_xor(...);
[[maybe_unused]] glsl::UVec3 prngState = pcg(state, context, state_glsl_146);
```

The kernel `State&` and the GLSL local are now distinct, and the helper call
resolves correctly.

**Gates:**

```text
native (Debug, -Werror)       149/149 PASS, exit 0
check_corpus --check          exit 0
check_semantics --check       exit 0
generate_typed_slice --check  exit 0
generate_kernels --check      exit 0
```

New native test
`glsl_reserved_emitter_identifiers_do_not_collide_with_mangled_locals`
(`tests/test_glsl_types.cpp`) pins the C++-side invariant that a kernel-state
binding and a mangled local coexist as distinct entities in one scope.

## Follow-up

The census covers `state`, `context`, `output`, `kernel_base`. If the emitter
ever binds additional identifiers, extend `_RESERVED_IDENTIFIERS` and re-run
the census; the byte-neutrality argument must be re-established each time,
since adding a name to the set could change output for an already-typed
program.

## Final acceptance

```text
Full Python discovery     Ran 194 tests in 1569.592s   OK   EXIT=0
Native (Debug, -Werror)   149/149 PASS, exit 0
generate_typed_slice --check   exit 0, typed_slice.cpp unchanged at 5765f863…
```

Python count is unchanged at 194 because the guard is byte-neutral for every
currently-typed program — there was nothing for the Python structural tests to
observe. The native count rose 148 → 149 for the new invariant test.

**Task 31a is accepted.**
