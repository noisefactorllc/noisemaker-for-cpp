import copy
import dataclasses
from pathlib import Path
import unittest

from tools.glslcpp import check_corpus, emit_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend import moodscape_frontend_profile as old

from tools.glslcpp.frontend import moodscape_dynamic_profile as dynamic
SOURCE = (Path(check_corpus.__file__).resolve().parents[2]
          / 'tools/glslcpp/corpus' / check_corpus.REVISION
          / 'sources/classicNoisedeck/moodscape/moodscape.glsl').read_text()

RAW_SHA256 = "2b020887bfb1a4dd366b1583e4ff68fd47193bd4993ba1052170de0981aabfa1"


def program(source=SOURCE, defines=None):
    if defines is None:
        defines = {'COLOR_MODE': 'int', 'NOISE_TYPE': 'int'}
    return analyze_program(parse_program(source, old.KEY, defines), old.KEY)


class DynamicMoodscapeProofTests(unittest.TestCase):
    def test_exact_dynamic_source_projects_only_dead_inverse_closure(self):
        raw = program()
        projected, sites = dynamic.apply(raw, RAW_SHA256, dynamic.PROFILE)
        self.assertEqual(29, len(projected.functions))
        self.assertEqual(['fwdA', 'fwdB'], [d.symbol.name for d in projected.declarations if d.type.display() == 'mat3'])
        self.assertEqual(5, len(sites.lane_indexes))
        self.assertEqual(3, len(sites.scalar_xors))
        self.assertEqual(1, len(sites.float_bits))
        self.assertTrue(all(any(node is member for member in old._expressions(projected)) for node in (*sites.lane_indexes, *sites.scalar_xors, *sites.float_bits)))
        dynamic.authenticate_projection(projected, RAW_SHA256, dynamic.PROFILE)

    def test_source_bound_hue_array_order_and_adjacent_pair_mutation(self):
        projected, sites = dynamic.apply(program(), RAW_SHA256,
                                         dynamic.PROFILE)
        pairs = dynamic.authenticate_hue_pairs(
            projected, RAW_SHA256, dynamic.PROFILE)
        self.assertEqual(2, len(pairs))
        self.assertEqual(dynamic._SOURCE_LOCKS[RAW_SHA256]["HUE_PAIR_LEDGER"], tuple(
            (old._span(pair.addition), old._sha(pair.addition),
             old._span(pair.fract), old._sha(pair.fract))
            for pair in pairs))
        rendered = emit_typed_cpp.render_typed_cpp(
            projected, old.KEY, RAW_SHA256,
            moodscape_frontend_profile=dynamic.PROFILE,
            prng_boolean_mix_select_profile="prng-boolean-mix-select-v1")
        self.assertEqual(2, rendered.count(
            "glsl::set_swizzle<0>(color, glsl::fract((static_cast<double>("
            "glsl::swizzle<0>(color)) + static_cast<double>("))
        self.assertNotIn(
            "glsl::set_swizzle<0>(color, glsl::fract(glsl::swizzle<0>(color)));",
            rendered)
        main_index = next(index for index, function in enumerate(projected.functions)
                          if function.name == "main")
        main = projected.functions[main_index]
        branch = main.body[13].children[1].children[0]
        children = list(branch.children)
        children[2], children[3] = children[3], children[2]
        altered_branch = dataclasses.replace(branch, children=tuple(children))
        second = dataclasses.replace(main.body[13].children[1], children=(
            altered_branch, *main.body[13].children[1].children[1:]))
        outer = dataclasses.replace(main.body[13], children=(
            main.body[13].children[0], second))
        changed_body = (*main.body[:13], outer, *main.body[14:])
        changed_main = dataclasses.replace(main, body=changed_body)
        changed = dataclasses.replace(projected, functions=(
            *projected.functions[:main_index], changed_main,
            *projected.functions[main_index + 1:]))
        with self.assertRaises(ValueError):
            dynamic.authenticate_projection(changed, RAW_SHA256,
                                            dynamic.PROFILE)

    def test_foreign_source_and_define_contract_are_rejected(self):
        for candidate, sha in (
            (program(SOURCE + '\n'), RAW_SHA256),
            (program(), '0' * 64),
            (program(defines={'COLOR_MODE': 2, 'NOISE_TYPE': 10}), RAW_SHA256),
        ):
            with self.subTest(candidate=sha):
                with self.assertRaises(ValueError):
                    dynamic.apply(candidate, sha, dynamic.PROFILE)

    def test_forged_tree_and_projection_are_rejected(self):
        raw = program()
        bad_function = dataclasses.replace(raw.functions[0], body=())
        with self.assertRaises(ValueError):
            dynamic.apply(dataclasses.replace(raw, functions=(bad_function,) + raw.functions[1:]), RAW_SHA256, dynamic.PROFILE)
        projected, _ = dynamic.apply(raw, RAW_SHA256, dynamic.PROFILE)
        with self.assertRaises(ValueError):
            dynamic.authenticate_projection(dataclasses.replace(projected, functions=projected.functions[:-1]), RAW_SHA256, dynamic.PROFILE)
        with self.assertRaises(ValueError):
            dynamic.authenticate_projection(dataclasses.replace(projected, declarations=projected.declarations[:-1]), RAW_SHA256, dynamic.PROFILE)
        with self.assertRaises(ValueError):
            dynamic.authenticate_projection(copy.deepcopy(projected), RAW_SHA256, 'wrong-profile')


if __name__ == '__main__':
    unittest.main()
