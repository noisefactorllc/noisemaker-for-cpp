"""The pooled-array alias emission (DEFECTS-FOUND item 6).

The JavaScript authority materializes ``vecN`` locals as
``PooledFloat32Array``, and ``var a = b;`` over one of them binds a
**reference**, not a copy. Whole-vector assignment is materialized in place,
so a later write through either name is visible through both. A value copy
diverges the moment either name is written -- which is exactly how
``filter/parallax`` shipped wrong as typed row 190.

``emit_typed_cpp`` models that. This module holds the emission's GREEN facts
and, more importantly, the RED ones: every clause of the collector is
neutralized in turn and the emission is required to change. A clause that can
be removed without moving a byte is not protecting anything.

The neutralizations patch behaviour at runtime rather than deleting source
text, so no assertion string disappears from the module under test.
"""

from __future__ import annotations

import pathlib
import re
import sys
import unittest
from unittest import mock

REPOSITORY = pathlib.Path(__file__).resolve().parents[1]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from tools.glslcpp import emit_typed_cpp, generate_typed_slice  # noqa: E402

SLICE_CPP = REPOSITORY / "src/typed_generated/typed_slice.cpp"
PARALLAX_ALIAS = "[[maybe_unused]] glsl::Vec2& prevUV = rayUV;"
# One line per emitted alias: `[[maybe_unused]] glsl::VecN& name = source;`
ALIAS_DECLARATION = re.compile(
    r"\[\[maybe_unused\]\] glsl::Vec[234]& (\w+) = ([A-Za-z_]\w*);")

_COMMITTED_SLICE = SLICE_CPP.read_text(encoding="utf-8")


def _regenerate() -> str:
    """The emitted slice, regenerated in memory from the live spec."""
    outputs = generate_typed_slice.generate_outputs(REPOSITORY)
    return outputs["src/typed_generated/typed_slice.cpp"].decode("utf-8")


def _alias_sites(text: str) -> list[tuple[str, str]]:
    return [(match.group(1), match.group(2)) for match in ALIAS_DECLARATION.finditer(text)]


class CommittedEmissionTests(unittest.TestCase):
    """What the committed slice carries. Fast -- reads the file, renders nothing."""

    def test_parallax_declares_prev_uv_as_a_reference_not_a_copy(self) -> None:
        self.assertIn(PARALLAX_ALIAS, _COMMITTED_SLICE)
        # The copy form must be gone: its presence IS the defect.
        self.assertNotIn("[[maybe_unused]] glsl::Vec2 prevUV = rayUV;", _COMMITTED_SLICE)

    def test_alias_site_census_is_exact(self) -> None:
        sites = _alias_sites(_COMMITTED_SLICE)
        # 32 after the current live slice's later admitted rows.
        self.assertEqual(32, len(sites))
        # Every alias binds a bare identifier, never a state field or a call.
        for name, source in sites:
            self.assertNotIn(".", source)
            self.assertNotEqual(name, source)

    def test_no_alias_binds_a_state_field(self) -> None:
        # A binding-sourced alias cannot be expressed against `const State&`.
        # `synth/osc2d` and `synth/perlin` carry that shape in the authority
        # and are deliberately NOT aliased -- see DEFECTS-FOUND item 6.
        self.assertNotIn("glsl::Vec2& res = state.", _COMMITTED_SLICE)
        for match in ALIAS_DECLARATION.finditer(_COMMITTED_SLICE):
            self.assertFalse(match.group(2).startswith("state"))

    def test_the_committed_file_is_what_the_generator_produces(self) -> None:
        self.assertEqual(_COMMITTED_SLICE, _regenerate())


class NeutralizationTests(unittest.TestCase):
    """RED. Each clause is neutralized; the emission must change.

    Neutralizing behaviour rather than deleting text keeps every assertion
    string in the module under test, so a raw-text search for a guard message
    still finds it.
    """

    def test_collecting_no_aliases_at_all_removes_every_reference(self) -> None:
        with mock.patch.object(emit_typed_cpp._Emitter,
                               "_collect_pooled_vector_aliases",
                               lambda self, statement: None):
            text = _regenerate()
        self.assertEqual([], _alias_sites(text))
        self.assertNotIn(PARALLAX_ALIAS, text)
        # Exactly the 32 ampersands, and nothing else, distinguish the two.
        self.assertEqual(len(_COMMITTED_SLICE) - 32, len(text))

    def test_the_observability_condition_is_not_vacuous(self) -> None:
        # Alias every bare-identifier vector declaration, whether or not a
        # write makes it observable. If that produced the same file, the
        # condition would be dead weight.
        original = emit_typed_cpp._Emitter._collect_pooled_vector_aliases

        def alias_everything(self, statement):
            if statement.kind == "decl":
                for declaration in statement.expressions:
                    if (declaration.kind != "declaration"
                            or declaration.symbol_id is None
                            or len(declaration.children) != 1
                            or declaration.type.display() not in self._POOLED_VECTOR_TYPES):
                        continue
                    source = declaration.children[0]
                    if (source.kind != "id" or source.symbol_id is None
                            or source.type.display() != declaration.type.display()
                            or source.symbol_id in self.program_scope_symbol_ids):
                        continue
                    self.alias_declaration_symbol_ids.add(declaration.symbol_id)
                    self.alias_source_symbol_ids.add(source.symbol_id)
            for child in statement.children:
                alias_everything(self, child)

        with mock.patch.object(emit_typed_cpp._Emitter,
                               "_collect_pooled_vector_aliases", alias_everything):
            text = _regenerate()
        self.assertGreater(len(_alias_sites(text)), 32)
        self.assertNotEqual(_COMMITTED_SLICE, text)
        self.assertIs(original, emit_typed_cpp._Emitter._collect_pooled_vector_aliases)

    def test_dropping_the_program_scope_skip_reaches_the_emitter_guard(self) -> None:
        # `synth/osc2d` aliases the `fullResolution` BINDING and then writes
        # it. Without the skip the collector admits it and the emitter's
        # defence-in-depth guard must fire -- proving both that the class
        # exists in the corpus and that the guard is reachable.
        original_post_init = emit_typed_cpp._Emitter.__post_init__

        def forget_program_scope(self) -> None:
            original_post_init(self)
            # `__post_init__` RETURNS EARLY for programs emitted through a
            # dedicated frontend (`synth/julia:julia` today): those emitters
            # never reach the general setup and never collect pooled-vector
            # aliases at all, so their general state does not exist. Forcing a
            # collection there would fabricate a code path the emitter does
            # not run -- and it is what made this neutralization raise
            # AttributeError instead of reaching the guard.
            # Detected from the state itself, never from a list of which
            # frontends return early: such a list goes stale at the next one.
            # This fails closed -- if the general setup stopped running for
            # every program, nothing would be neutralized and the
            # `assertRaises` below would go red.
            if not hasattr(self, "mutated_symbol_ids"):
                return
            self.program_scope_symbol_ids = set()
            self.alias_declaration_symbol_ids = set()
            self.alias_source_symbol_ids = set()
            for function in self.program.functions:
                for statement in function.body:
                    self._collect_pooled_vector_aliases(statement)

        with mock.patch.object(emit_typed_cpp._Emitter,
                               "__post_init__", forget_program_scope):
            with self.assertRaises(generate_typed_slice.GeneratorError) as caught:
                _regenerate()
        self.assertIn("pooled vector alias source is not a local or parameter",
                      str(caught.exception))
        self.assertIn("synth/osc2d:osc2d", str(caught.exception))

    def test_the_float_expr_suppression_is_vacuous_today_and_stays_anyway(self) -> None:
        """A guard that protects nothing YET, recorded as such.

        An alias source emitted as the `glsl::FloatExpr<N>` proxy cannot have
        a `glsl::VecN&` bound to it -- the emission would not compile. The
        declaration arm therefore holds the proxy rewrite back for any symbol
        that is an alias source.

        Measured: across all 207 live programs, no alias source is currently
        FloatExpr-eligible, so removing the suppression changes nothing. That
        is a fact about today's corpus, NOT a reason to delete the clause: the
        two conditions are independent, and the first program that satisfies
        both would emit code the compiler rejects. This test exists so the
        vacuity is a recorded measurement that will flip to a real
        discriminator on its own, rather than an unexamined assumption.
        """
        original_post_init = emit_typed_cpp._Emitter.__post_init__

        def forget_alias_sources(self) -> None:
            original_post_init(self)
            self.alias_source_symbol_ids = set()

        with mock.patch.object(emit_typed_cpp._Emitter,
                               "__post_init__", forget_alias_sources):
            text = _regenerate()
        self.assertEqual(
            _COMMITTED_SLICE, text,
            "an alias source is now FloatExpr-eligible: the suppression has "
            "become load-bearing, and this test should be inverted to assert "
            "that removing it breaks the emission")

    def test_restricting_to_vec_types_is_recorded_and_exact(self) -> None:
        # The scope is measured, not assumed: only vec2/vec3/vec4 are known to
        # materialize as PooledFloat32Array.
        self.assertEqual(frozenset({"vec2", "vec3", "vec4"}),
                         emit_typed_cpp._Emitter._POOLED_VECTOR_TYPES)


class ParallaxSourceContractTests(unittest.TestCase):
    """The GLSL side of the contract, read from the pinned corpus."""

    SOURCE = (REPOSITORY / "tools/glslcpp/corpus"
              / "a024dc3a960cc44af454abc7aebce50456c194e6"
              / "sources/filter/parallax/parallax.glsl")

    def test_the_refinement_the_authority_makes_dead_is_present_in_the_glsl(self) -> None:
        text = self.SOURCE.read_text(encoding="utf-8")
        self.assertIn("vec2 prevUV = rayUV;", text)
        self.assertIn("rayUV = mix(rayUV, prevUV, w);", text)
        # The GLSL says interpolate; the JS materialization makes it a no-op.
        # Porting the GLSL rather than the materialization is the defect.
        self.assertEqual(1, text.count("prevUV = rayUV;"))


if __name__ == "__main__":
    unittest.main()
