"""Task 7 authenticated generated factory-route contracts."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import unittest


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
        self.assertIn("constexpr std::array<KernelFactory, 213> kCatalog", self.generated)
        self.assertIn(
            "constexpr std::array<FactoryRoute, 211> kCanonicalRoutes",
            self.generated,
        )
        self.assertEqual(211, len(self.manifest["programs"]))
        self.assertEqual(
            211,
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


if __name__ == "__main__":
    unittest.main()
