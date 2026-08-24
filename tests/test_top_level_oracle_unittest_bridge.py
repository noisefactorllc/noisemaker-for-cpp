"""Execute the legacy pytest-style oracle functions through unittest.

The five oracle modules below intentionally keep their zero-argument
top-level functions.  ``unittest`` discovery ignores those functions, so
this module provides one named method for each and preserves the function's
native assertion/``pytest.raises`` behavior by invoking it directly.
"""

from __future__ import annotations

import importlib
import inspect
import unittest

import pytest


_EXPECTED_MANIFEST = (
    ("tests.test_bitEffects_oracle", "test_bitEffects_oracle_package_is_authenticated_and_exact"),
    ("tests.test_bitEffects_oracle", "test_bitEffects_generator_check_and_self_test"),
    ("tests.test_bitEffects_oracle", "test_bitEffects_materializer_self_test_and_check"),
    ("tests.test_bitEffects_oracle", "test_bitEffects_include_is_valid_cxx20"),
    ("tests.test_bitEffects_oracle", "test_bitEffects_test_source_has_no_run_specific_paths"),
    ("tests.test_classic_noise_oracle", "test_classic_noise_oracle_package_exists"),
    ("tests.test_classic_noise_oracle", "test_schema_abi_cases_and_dead_binding_invariance"),
    ("tests.test_kaleido_oracle", "test_kaleido_oracle_package_is_self_consistent"),
    ("tests.test_kaleido_oracle", "test_kaleido_generator_check_requires_authority_snapshot"),
    ("tests.test_kaleido_oracle", "test_generator_rejects_modified_unpinned_runtime_dependency"),
    ("tests.test_kaleido_oracle", "test_generator_self_tests_cover_closure_and_pending_abi_contract"),
    ("tests.test_kaleido_oracle", "test_materializer_self_tests_and_check_are_standalone"),
    ("tests.test_kaleido_oracle", "test_generated_include_is_valid_cxx20_and_exposes_native_table"),
    ("tests.test_kaleido_oracle", "test_test_source_has_no_run_specific_paths"),
    ("tests.test_mandelbrot_oracle", "test_package_and_sidecars_are_exact_and_semantic"),
    ("tests.test_mandelbrot_oracle", "test_generator_check_self_test_and_materializer_contract"),
    ("tests.test_mandelbrot_oracle", "test_materializer_rejects_forged_semantic_fields_even_with_recomputed_payload"),
    ("tests.test_mandelbrot_oracle", "test_generated_include_compiles_as_cxx20"),
    ("tests.test_mandelbrot_oracle", "test_generator_rejects_transitive_mutation_and_nonliteral_import"),
    ("tests.test_mandelbrot_oracle", "test_generator_rejects_literal_extra_import_and_symlink_or_live_roots"),
    ("tests.test_testpattern_oracle", "test_package_files_and_contract"),
    ("tests.test_testpattern_oracle", "test_generator_and_materializer_smoke"),
    ("tests.test_testpattern_oracle", "test_authority_unset_and_live_checkout_rejected"),
    ("tests.test_testpattern_oracle", "test_parent_alias_acceptance_and_leaf_symlink_rejection"),
    ("tests.test_testpattern_oracle", "test_generator_rejects_configured_missing_and_symlink_live_checkout"),
    ("tests.test_testpattern_oracle", "test_generator_rejects_import_graph_and_closure_leaf_mutations"),
    ("tests.test_testpattern_oracle", "test_materializer_rejects_duplicate_scalar_huge_and_matching_sidecars"),
    ("tests.test_testpattern_oracle", "test_materializer_rejects_coordinated_payload_forgery"),
    ("tests.test_testpattern_oracle", "test_generator_anchor_rejects_materializer_and_manifest_forgery"),
    ("tests.test_testpattern_oracle", "test_coherence_anchor_rejects_coordinated_manifest_forgery"),
    ("tests.test_testpattern_oracle", "test_materializer_rejects_nonfinite_controls"),
    ("tests.test_testpattern_oracle", "test_materializer_rejects_path_spellings_recursively"),
    ("tests.test_testpattern_oracle", "test_coherence_rejects_coordinated_sidecar_forgery"),
    ("tests.test_testpattern_oracle", "test_include_cxx20_smoke"),
)


def _actual_manifest() -> tuple[tuple[str, str], ...]:
    """Return the source-order top-level test function manifest."""

    rows: list[tuple[str, str, int]] = []
    for module_name in dict.fromkeys(module for module, _ in _EXPECTED_MANIFEST):
        module = importlib.import_module(module_name)
        for name, value in vars(module).items():
            if (
                name.startswith("test_")
                and inspect.isfunction(value)
                and value.__module__ == module_name
            ):
                rows.append((module_name, name, value.__code__.co_firstlineno))
    rows.sort(key=lambda row: (row[0], row[2], row[1]))
    return tuple((module, name) for module, name, _ in rows)


def _assert_manifest() -> None:
    actual = _actual_manifest()
    if actual != _EXPECTED_MANIFEST:
        raise AssertionError(
            "top-level oracle manifest drifted; expected "
            f"{_EXPECTED_MANIFEST!r}, got {actual!r}"
        )
    for module_name, function_name in _EXPECTED_MANIFEST:
        function = getattr(importlib.import_module(module_name), function_name, None)
        if not inspect.isfunction(function):
            raise AssertionError(f"{module_name}.{function_name} is not a function")
        signature = inspect.signature(function)
        if signature.parameters:
            raise AssertionError(
                f"{module_name}.{function_name} must remain zero-argument; "
                f"got {signature}"
            )


def _run_top_level_test(module_name: str, function_name: str) -> None:
    function = getattr(importlib.import_module(module_name), function_name)
    try:
        function()
    except pytest.skip.Exception as exc:
        raise unittest.SkipTest(str(exc)) from None


class TopLevelOracleUnittestBridge(unittest.TestCase):
    """Named unittest methods generated from the pinned manifest."""


def _make_bridge_method(module_name: str, function_name: str):
    def bridge_method(self: unittest.TestCase) -> None:
        del self
        _run_top_level_test(module_name, function_name)

    bridge_method.__name__ = f"test_{module_name.rsplit('.', 1)[-1]}__{function_name}"
    bridge_method.__qualname__ = (
        f"TopLevelOracleUnittestBridge.{bridge_method.__name__}"
    )
    bridge_method.__doc__ = f"Run {module_name}.{function_name}."
    return bridge_method


_assert_manifest()
for _module_name, _function_name in _EXPECTED_MANIFEST:
    setattr(
        TopLevelOracleUnittestBridge,
        f"test_{_module_name.rsplit('.', 1)[-1]}__{_function_name}",
        _make_bridge_method(_module_name, _function_name),
    )

