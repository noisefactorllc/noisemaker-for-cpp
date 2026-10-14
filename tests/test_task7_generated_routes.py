"""Task 7 authenticated generated factory-route contracts."""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import re
import unittest
from tests import corpus_census
from tests.gate import full_run_only


REPOSITORY = pathlib.Path(__file__).resolve().parents[1]


# The compile-define contract, the baked define list, and the five
# ordered-ABI anchors that every generated route row now carries.
ANCHOR_FIELDS = r'"[^"]*", "[^"]*", ' + r'"[0-9a-f]{64}", ' * 5

class GeneratedFactoryRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generated = (
            REPOSITORY / "src/typed_generated/typed_slice.cpp"
        ).read_text(encoding="utf-8")
        self.manifest = json.loads(
            (REPOSITORY / "src/typed_generated/typed_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.compatibility = json.loads(
            (
                REPOSITORY
                / "src/effects/generated/backend_compatibility.json"
            ).read_text(encoding="utf-8")
        )
        self.header = (
            REPOSITORY / "include/noisemaker/generated/catalog.hpp"
        ).read_text(encoding="utf-8")
        start = self.generated.index("kCanonicalRoutes{{")
        self.canonical_block = self.generated[
            start:self.generated.index("std::span<const KernelFactory> catalog()", start)
        ]

    def test_public_descriptor_contains_authenticated_identity_fields(self) -> None:
        self.assertIn("std::string_view canonical_factory;", self.header)
        self.assertIn("std::string_view emitted_factory;", self.header)
        self.assertIn("std::string_view route_kind;", self.header)
        self.assertIn("std::string_view source_sha256;", self.header)
        self.assertIn("std::string_view typed_abi_sha256;", self.header)
        self.assertIn("std::string_view define_contract;", self.header)
        self.assertIn("std::string_view defines;", self.header)
        for section in ("sampler_abi_sha256", "uniform_abi_sha256", "output_abi_sha256",
                        "output_extent_sha256", "compile_define_abi_sha256"):
            self.assertIn(f"std::string_view {section};", self.header)
        self.assertIn("canonical_routes() noexcept", self.header)
        self.assertIn("find_canonical(std::string_view key,", self.header)

    def test_physical_catalog_retains_rows_and_canonical_catalog_deduplicates(self) -> None:
        self.assertIn(f"constexpr std::array<KernelFactory, {corpus_census.catalog_row_count()}> kCatalog",
                      self.generated)
        self.assertIn(
            f"constexpr std::array<FactoryRoute, {corpus_census.single_output_route_row_count()}> kCanonicalRoutes",
            self.generated,
        )
        self.assertIn(
            f"constexpr std::array<FactoryRouteMrt, {len(corpus_census.mrt_keys())}> kCanonicalRoutesMrt",
            self.generated,
        )
        self.assertEqual(corpus_census.typed_count(), len(self.manifest["programs"]))
        self.assertEqual(
            corpus_census.typed_count(),
            len({item["program_key"] for item in self.manifest["programs"]}),
        )

    def test_duplicate_keys_use_authenticated_canonical_pairs(self) -> None:
        # Both physical rows of each duplicate key are retained in the
        # KernelFactory catalog, which is what proves the duplicate exists...
        for key, legacy, canonical in (
            ("filter/invert:inv", "bind_filter_invert", "bind_filter_invert_inv"),
            ("synth/solid:solid", "bind_synth_solid", "bind_synth_solid_solid"),
        ):
            self.assertIn(f'{{"{key}", &{legacy}}},', self.generated)
            self.assertIn(f'{{"{key}", &{canonical}}},', self.generated)

        # ...and the dispatched canonical view carries exactly one row per key,
        # selecting the canonical factory rather than the legacy duplicate.
        for key, legacy, canonical in (
            ("filter/invert:inv", "bind_filter_invert", "bind_filter_invert_inv"),
            ("synth/solid:solid", "bind_synth_solid", "bind_synth_solid_solid"),
        ):
            rows = re.findall(
                r'\{"' + re.escape(key) + r'", "([^"]+)", "([^"]+)", "([^"]+)", '
                r'"([0-9a-f]{64})", "([0-9a-f]{64})", ' + ANCHOR_FIELDS + r'&([^}]+)\}',
                self.canonical_block,
            )
            self.assertEqual(len(rows), 1, key)
            self.assertEqual(rows[0][0], canonical)
            self.assertEqual(rows[0][1], canonical)
            self.assertEqual(rows[0][2], "typed_emitter")
            self.assertEqual(rows[0][5], canonical)
            self.assertNotIn(f'&{legacy}}}', self.canonical_block)

        # The physical FactoryRoute table is deliberately not emitted: nothing
        # dispatches through it, so its authenticated anchors could drift
        # unnoticed.
        self.assertNotIn("kRoutes", self.generated)
        self.assertNotIn("std::span<const FactoryRoute> routes() noexcept;", self.header)

    def test_custom_and_incompatible_routes_remain_explicit(self) -> None:
        self.assertRegex(
            self.generated,
            r'\{"classicNoisedeck/bitEffects:bitEffects", '
            r'"noisemaker::effects::bind_bit_effects", '
            r'"bind_classicNoisedeck_bitEffects_bitEffects", "custom_adapter", '
            r'"[0-9a-f]{64}", "[0-9a-f]{64}", ' + ANCHOR_FIELDS +
            r'&noisemaker::effects::bind_bit_effects\}',
        )
        self.assertRegex(
            self.generated,
            r'\{"filter/text:text", "bind_filter_text_text", '
            r'"bind_filter_text_text", "typed_emitter", "[0-9a-f]{64}", '
            r'"[0-9a-f]{64}", ' + ANCHOR_FIELDS + r'&bind_filter_text_text\}',
        )

    def test_descriptor_hashes_are_bound_to_manifest_source_and_typed_abi(self) -> None:
        compatibility = {
            row["program_key"]: row
            for row in self.compatibility["canonical_programs"]
        }
        for row in self.manifest["programs"]:
            typed_abi_sha256 = hashlib.sha256(
                (json.dumps(row["typed_abi"], indent=2) + "\n").encode("utf-8")
            ).hexdigest()
            descriptor = (
                f'"{row["program_key"]}", "{row["factory"]}", '
                f'"{row["emitted_factory"]}", '
            )
            self.assertIn(descriptor, self.generated)
            self.assertIn(
                f'"{compatibility[row["program_key"]]["new_raw_sha256"]}", '
                f'"{typed_abi_sha256}"',
                self.generated,
            )


    def test_route_row_extras_counts_distinct_binding_projections(self) -> None:
        # The current authority reuses identical binding projections. The
        # generated table must count distinct routes rather than pass bindings.
        doc = self.compatibility
        mrt = set(corpus_census.mrt_keys())
        per_binding = sum(
            len(row["binding_outputs"]) - 1
            for row in doc["canonical_programs"]
            if row["program_key"] not in mrt and row.get("binding_outputs"))
        self.assertGreater(per_binding, 0)
        extras = corpus_census._route_row_extras(doc)
        self.assertLess(extras, per_binding)
        table = re.search(r"std::array<FactoryRoute, (\d+)> kCanonicalRoutes",
                          self.generated)
        self.assertIsNotNone(table)
        self.assertEqual(extras, int(table.group(1)) -
                         corpus_census.single_output_typed_count())

        # Synthetic byte-identical bindings collapse: N identical bindings
        # contribute one row (zero extras), and each distinct projection
        # contributes its own extra row.
        # temporalAberration:delayShift carries the live multi-binding data
        # (eight bindings).
        row = next(row for row in doc["canonical_programs"]
                   if row["program_key"] == "filter/temporalAberration:delayShift")
        binding = row["binding_outputs"][0]
        # The live extent is {"width": "input", "height": "input",
        # "format": ...}; a distinct projection changes the format token.
        distinct = {**binding,
                    "extent": {**binding["extent"], "format": "rgba16float"}}
        duplicated = {**row, "binding_outputs": [binding, copy.deepcopy(binding),
                                                 copy.deepcopy(binding)]}
        split = {**row, "binding_outputs": [binding, copy.deepcopy(binding), distinct]}
        self.assertEqual(0, corpus_census._route_row_extras(
            {"canonical_programs": [duplicated]}))
        self.assertEqual(1, corpus_census._route_row_extras(
            {"canonical_programs": [split]}))

    @full_run_only
    def test_route_table_ships_no_byte_identical_descriptor_duplicate(self) -> None:
        """One route row per DISTINCT binding projection, never a duplicate.

        The executor refuses a byte-identical duplicate of a whole route
        descriptor as a generation defect, so the generator shares one row
        among bindings whose projections coincide (ping-pong bindings that
        reuse the same sampler set, output routes and extent) while a binding
        that differs anywhere keeps its own row.
        """
        from unittest import mock

        from tools.glslcpp import generate_typed_slice

        rows = generate_typed_slice._compatibility_canonical_rows(REPOSITORY)
        row = rows["filter/temporalAberration:delayShift"]
        binding = row["binding_outputs"][0]
        distinct = {**binding,
                    "extent": {**binding["extent"], "format": "rgba16float"}}
        mocked = dict(rows)
        mocked["filter/temporalAberration:delayShift"] = {
            **row,
            "binding_outputs": [binding, copy.deepcopy(binding), distinct],
        }
        with mock.patch.object(generate_typed_slice, "_compatibility_canonical_rows",
                               return_value=mocked):
            outputs = generate_typed_slice.generate_outputs(REPOSITORY)
        cpp = outputs["src/typed_generated/typed_slice.cpp"].decode()
        start = cpp.index("kCanonicalRoutes{{")
        block = cpp[start:cpp.index("std::span<const KernelFactory> catalog()", start)]
        pattern = (r'\{"([^"]+)", "([^"]+)", "([^"]+)", "([^"]+)", "([0-9a-f]{64})", '
                   r'"([0-9a-f]{64})", "([^"]*)", "([^"]*)", "([0-9a-f]{64})", '
                   r'"([0-9a-f]{64})", "([0-9a-f]{64})", "([0-9a-f]{64})", '
                   r'"([0-9a-f]{64})", &([^}]+)\}')
        entries = re.findall(pattern, block)
        self.assertGreater(len(entries), 0)
        # No two emitted rows are byte-identical: the executor's generation
        # defect must be unreachable by construction.
        self.assertEqual(len(entries), len({tuple(entry) for entry in entries}))
        delayed_rows = [entry for entry in entries
                        if entry[0] == "filter/temporalAberration:delayShift"]
        # The mocked row carries three bindings: two byte-identical (they
        # collapse to the first row) and one with a distinct output extent
        # (it keeps its own row).
        self.assertEqual(2, len(delayed_rows))
        self.assertEqual(2, len({tuple(entry) for entry in delayed_rows}))
        # The two rows differ exactly in the binding's output-extent anchor.
        self.assertEqual(2, len({entry[11] for entry in delayed_rows}))


if __name__ == "__main__":
    unittest.main()
