"""Focused RED/GREEN proof for `filter/normalMap`'s three const array globals.

Written before ``tools/glslcpp/frontend/const_global_table_profile.py`` was
wired into either authority; the module is exercised here directly, and Task 3
attaches it to the validator and the emitter.

``filter/normalMap:normalMap`` declares three ``const`` file-scope arrays::

    15|const ivec2 SOBEL_OFFSETS[9]  = ivec2[](...);
    21|const float SOBEL_X_KERNEL[9] = float[](...);
    27|const float SOBEL_Y_KERNEL[9] = float[](...);

literal-initialised, never written, and read exactly three times -- once each,
as ``TABLE[i]`` inside one ``for (int i = 0; i < 9; i++)`` loop in ``main``.

Four testing rules apply, three inherited from the preceding slices and one new:

1. ``Symbol`` embeds its declaration span and ``TypedDeclaration`` embeds its
   whole initializer, so a value-level mutation shifts every enclosing node
   hash. The production module evaluates storage, element type, the native
   contract and both initializer locks **ahead** of node identity, and each
   lock is proved load-bearing by *deleting the lock* in a scratch copy --
   never by mutating the input and watching something raise.
2. Every mutation test refreezes **only** the coarse hash fields (and, where
   noted, the two program-wide counters) and asserts that no coarse message
   fired. Semantic fields keep their frozen originals.
3. The census walks global declaration initializers as well as function
   bodies. Here that is not hygiene: the validator's generic ``expression()``
   walk and its write audit both iterate ``program.functions`` only, so this
   closure is the *sole* inspector of the three initializers.
4. **Every guard string this module raises gets a test asserting that exact
   message.** ``test_every_guard_message_is_asserted_somewhere_in_this_file``
   enforces it mechanically against the module's own source.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import importlib
import importlib.util
import json
import pathlib
import types
import unittest
from unittest import mock

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.semantic import analyze_program
from tools.glslcpp.frontend.semantic_types import array, vector


ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = (ROOT / "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6"
          / "sources")
MODULE = "tools.glslcpp.frontend.const_global_table_profile"

KEY = "filter/normalMap:normalMap"
PROFILE = "const-global-nine-table-v1"
SOURCE_PATH = "filter/normalMap/normalMap.glsl"
SOURCE = CORPUS / SOURCE_PATH
RAW_SHA256 = "384312e50972f75dbebd4080cd76d1c2554a439eb36746f2e351d63a03a271cb"
NORMALIZED_SHA256 = (
    "65a598d7765460203cf38a91883de40bedcb7e135dbbdac2cd90663353567025")

OFFSETS_ID = 9
X_KERNEL_ID = 10
Y_KERNEL_ID = 11
OFFSETS_ORDINAL = 8
X_KERNEL_ORDINAL = 9
Y_KERNEL_ORDINAL = 10
MAIN_ID = 28
LOOP_INDEX_SYMBOL = 47
LOOP_STATEMENT_INDEX = 13

# Every message the coarse gate can produce. A local lock that "fires" with one
# of these is not testing what its name claims.
COARSE = (
    "raw source drift",
    "normalized source drift",
    "typed function fingerprint drift",
    "whole-program fingerprint drift",
    "interface fingerprint drift",
)

# A foreign program that really carries the construct: a const, literal-
# initialised, file-scope `float[9]` read once through a nine-trip counted
# loop. The rejection at the widened boundary must be about IDENTITY, not
# about the shape being absent.
FOREIGN_SOURCE = (
    "out vec4 fragColor;\n"
    "const float TAPS[9] = float[](\n"
    "    0.0, 1.0, 2.0,\n"
    "    3.0, 4.0, 5.0,\n"
    "    6.0, 7.0, 8.0\n"
    ");\n"
    "void main() {\n"
    "    float total = 0.0;\n"
    "    for (int i = 0; i < 9; i++) {\n"
    "        total += TAPS[i];\n"
    "    }\n"
    "    fragColor = vec4(total, total, total, 1.0);\n"
    "}\n"
)


def _module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:  # pragma: no cover - guarded by the assertion below
        raise AssertionError("const-global nine-table profile module is absent")
    return importlib.import_module(MODULE)


def _scratch(module, *disable: str):
    """Re-exec the production module and *delete* the named lock predicates.

    A neutralized predicate always reports "holds", which is exactly what
    removing the lock from the module source would do. The live module object
    is never touched, so these tests cannot leak state into each other.
    """
    source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
    scratch = types.ModuleType(f"{module.__name__}__scratch")
    scratch.__dict__.update({
        "__file__": module.__file__,
        "__package__": module.__package__,
    })
    exec(compile(source, module.__file__, "exec"), scratch.__dict__)
    for name in disable:
        if not callable(getattr(scratch, name, None)):
            raise AssertionError(f"{name} is not a deletable lock predicate")
        setattr(scratch, name, lambda *args, **kwargs: True)
    return scratch


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _analyzed(raw: str | None = None, key: str = KEY,
              defines: dict | None = None, parse_key: str | None = None):
    raw = SOURCE.read_text(encoding="utf-8") if raw is None else raw
    defines = (generate_typed_slice._defaults(ROOT, KEY)
               if defines is None else defines)
    parse_key = key if parse_key is None else parse_key
    return analyze_program(parse_program(raw, parse_key, defines), key)


def _foreign():
    return analyze_program(
        parse_program(FOREIGN_SOURCE, "test:foreign", {}), "test:foreign")


def _main(program):
    return next(item for item in program.functions if item.name == "main")


def _fn(program, name):
    return next(item for item in program.functions if item.name == name)


def _declaration(program, name):
    return next(item for item in program.declarations
                if item.symbol.name == name)


def _walk(statement):
    """Every expression node under ``statement``, with its parent."""
    def expression(value, parent=None):
        yield value, parent
        for child in value.children:
            yield from expression(child, value)
    for item in statement.expressions:
        yield from expression(item)
    for child in statement.children:
        yield from _walk(child)


def _index_node(program, name):
    """The single ``TABLE[i]`` node for ``name``, and its parent."""
    symbol_id = _declaration(program, name).symbol.id
    found = [(node, parent)
             for statement in _main(program).body
             for node, parent in _walk(statement)
             if (node.kind == "index" and node.children
                 and node.children[0].symbol_id == symbol_id)]
    if len(found) != 1:
        raise AssertionError(f"expected one index site for {name}")
    return found[0]


def _replace_child(parent, old, new):
    object.__setattr__(parent, "children",
                       tuple(new if item is old else item
                             for item in parent.children))


# The coarse gate, in the order the module evaluates it.
_COARSE_ORDER = ("raw", "normalized", "functions", "whole", "interface")


def _coarse_values(module, candidate):
    raw = candidate.raw_source.encode("utf-8")
    normalized = candidate.source.encode("utf-8")
    return {
        "raw": {"raw_bytes": len(raw),
                "raw_sha256": hashlib.sha256(raw).hexdigest()},
        "normalized": {
            "normalized_bytes": len(normalized),
            "normalized_sha256": hashlib.sha256(normalized).hexdigest()},
        "functions": {"functions_sha256": module._sha(candidate.functions)},
        "whole": {"whole_sha256": module._whole(candidate)},
        "interface": {"interface_sha256": module._interface(candidate)},
    }


def _relocked(module, candidate, **overrides):
    """A fresh ``_LOCKS`` with only the *coarse hash* fields refrozen.

    Deliberately does **not** refreeze any semantic field: the binding table,
    the ordinals, the native contracts, the two censuses and every node hash
    keep their frozen originals. Refreezing those would hand the mutation to
    the very lock under test and make the experiment vacuous.
    """
    locks = copy.deepcopy(module._LOCKS)
    values = _coarse_values(module, candidate)
    for name in _COARSE_ORDER:
        locks[KEY].update(values[name])
    locks[KEY].update(overrides)
    return locks


def _relocked_partial(module, candidate, upto):
    """Refreeze only the coarse fields the module checks *before* ``upto``."""
    locks = copy.deepcopy(module._LOCKS)
    values = _coarse_values(module, candidate)
    for name in _COARSE_ORDER:
        if name == upto:
            return locks
        locks[KEY].update(values[name])
    raise AssertionError(f"{upto} is not a coarse gate stage")


def _recount(module, candidate):
    """Refreeze only the two program-wide *cardinality* counters."""
    total, assigns = module._node_census(candidate)
    return {"total_nodes": total, "total_assigns": assigns}


def _authenticate(module, candidate, locks, profile=PROFILE):
    with mock.patch.object(module, "_LOCKS", locks):
        return module.authenticate_const_global_tables(
            candidate, locks[KEY]["raw_sha256"], profile)


def _expect(test, module, candidate, locks, expected, profile=PROFILE):
    with test.assertRaises(ValueError) as raised:
        _authenticate(module, candidate, locks, profile)
    message = str(raised.exception)
    for coarse in COARSE:
        test.assertNotIn(coarse, message,
                         f"{expected!r} was absorbed by the coarse gate")
    test.assertIn(expected, message)
    return message


class ConstGlobalTablePublicSurfaceTests(unittest.TestCase):
    def test_module_exports_the_designed_public_surface(self):
        module = _module()
        self.assertEqual((KEY,), module.KEYS)
        self.assertEqual({KEY: PROFILE}, module.PROFILES)
        self.assertEqual(frozenset({KEY}), module.CONST_GLOBAL_TABLE_KEYS)
        self.assertIsInstance(module.CONST_GLOBAL_TABLE_KEYS, frozenset)
        self.assertEqual(KEY, module.NORMAL_MAP_KEY)
        self.assertEqual(PROFILE, module.PROFILE)
        for name in ("KEYS", "PROFILES", "CONST_GLOBAL_TABLE_KEYS", "PROFILE",
                     "NORMAL_MAP_KEY", "REQUIRED_COMPANION_PROFILES",
                     "ALLOWED_ROW_FIELDS", "allowed_row_fields",
                     "ConstGlobalTable", "ConstGlobalTableRead",
                     "table_contract",
                     "authenticate_const_global_tables",
                     "authenticate_const_global_table_reads",
                     "apply_const_global_tables"):
            with self.subTest(name=name):
                self.assertIn(name, module.__all__)
                self.assertTrue(hasattr(module, name))

    def test_the_frozen_source_path_names_the_authenticated_file(self):
        module = _module()
        path = module._LOCKS[KEY]["source_path"]
        self.assertEqual("sources/" + SOURCE_PATH, path)
        raw = (CORPUS.parent / path).read_bytes()
        self.assertEqual(len(raw), module._LOCKS[KEY]["raw_bytes"])
        self.assertEqual(RAW_SHA256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(RAW_SHA256, module._LOCKS[KEY]["raw_sha256"])
        self.assertEqual(NORMALIZED_SHA256,
                         module._LOCKS[KEY]["normalized_sha256"])

    def test_the_corpus_manifest_agrees_with_the_frozen_source_record(self):
        module = _module()
        manifest = json.loads(
            (CORPUS.parent / "manifest.json").read_text(encoding="utf-8"))
        entry = next(row for row in manifest["programs"]
                     if row["program_key"] == KEY)
        self.assertEqual(module._LOCKS[KEY]["source_path"], entry["source"])

    def test_companion_carrier_data_is_the_reused_as_u32_round_profile(self):
        module = _module()
        self.assertEqual(
            {KEY: (("as_u32_round_profile", "as-u32-round-admission-v1"),)},
            module.REQUIRED_COMPANION_PROFILES)
        carrier = importlib.import_module(
            "tools.glslcpp.frontend.as_u32_round_profile")
        self.assertEqual("as-u32-round-admission-v1", carrier.PROFILE)
        self.assertIn(KEY, carrier.AS_U32_ROUND_KEYS)

    def test_the_row_field_guard_is_an_exhaustive_allowlist(self):
        """An allowlist, not a denylist.

        `generate_typed_slice`'s allowed-field arm compares
        `set(item) != expected`, so equality with this set discharges "every
        other profile absent" by construction. The previous slice's review
        replaced a 5-entry denylist against a 25-field universe for exactly
        this reason.
        """
        module = _module()
        self.assertEqual(
            {"as_u32_round_profile", "const_global_table_profile", "defines",
             "program_key"},
            set(module.allowed_row_fields(KEY)))
        self.assertEqual({KEY: module.allowed_row_fields(KEY)},
                         module.ALLOWED_ROW_FIELDS)
        self.assertIsInstance(module.ALLOWED_ROW_FIELDS[KEY], frozenset)
        self.assertFalse(hasattr(module, "FORBIDDEN_COMPANION_FIELDS"),
                         "the denylist must not come back")
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.allowed_row_fields("synth/shape:shape")

    def test_the_allowlist_excludes_every_other_live_row_profile_field(self):
        """Checked against the REAL row-field universe, not a hand-list."""
        module = _module()
        spec = json.loads(
            (ROOT / "tools/glslcpp/typed_slice.json").read_text(
                encoding="utf-8"))
        universe = {field for row in spec["programs"] for field in row
                    if field.endswith("_profile")
                    and row["program_key"] != KEY}
        self.assertGreaterEqual(len(universe), 30, "universe looks truncated")
        allowed = module.allowed_row_fields(KEY)
        self.assertEqual({"as_u32_round_profile"}, universe & allowed)
        for field in sorted(universe - allowed):
            with self.subTest(field=field):
                self.assertNotIn(field, allowed)
        self.assertIn("as_u32_round_profile", allowed)
        self.assertIn("const_global_table_profile", allowed)
        self.assertNotIn("const_global_table_profile", universe,
                         "no other row may carry the const-table carrier")
        self.assertEqual(
            [], [row["program_key"] for row in spec["programs"]
                 if "const_global_table_profile" in row
                 and row["program_key"] != KEY])

    def test_table_contract_is_the_three_frozen_nine_element_tables(self):
        module = _module()
        contract = module.table_contract(KEY)
        self.assertEqual(3, len(contract))
        self.assertEqual(("SOBEL_OFFSETS", "SOBEL_X_KERNEL", "SOBEL_Y_KERNEL"),
                         tuple(item.name for item in contract))
        self.assertEqual((OFFSETS_ID, X_KERNEL_ID, Y_KERNEL_ID),
                         tuple(item.symbol_id for item in contract))
        self.assertEqual(("ivec2[9]", "float[9]", "float[9]"),
                         tuple(item.glsl_type for item in contract))
        self.assertEqual(("glsl::IVec2", "double", "double"),
                         tuple(item.native_element_type for item in contract))
        self.assertEqual(("SobelOffsets9", "SobelXKernel9", "SobelYKernel9"),
                         tuple(item.native_alias for item in contract))
        for item in contract:
            with self.subTest(table=item.name):
                self.assertEqual(9, item.element_count)
                self.assertEqual(72, item.native_sizeof)
                self.assertEqual(9, len(item.element_spans))
        self.assertEqual(3, len({item.native_alias for item in contract}),
                         "the three aliases must be distinct")
        with self.assertRaisesRegex(ValueError, "not an admitted"):
            module.table_contract("synth/shape:shape")

    def test_the_native_alias_set_does_not_collide_with_sibling_proofs(self):
        """`Kernel9` / `Offsets9` / `Centers13` are emitted for other programs
        into the same generated translation unit."""
        module = _module()
        aliases = {item.native_alias for item in module.table_contract(KEY)}
        self.assertEqual(set(), aliases & {"Kernel9", "Offsets9", "Centers13"})


class ConstGlobalTableMaterializationTests(unittest.TestCase):
    """The JS contract, and design amendment S15's pooling hazard."""

    def test_float_elements_are_doubles_because_the_js_array_holds_numbers(self):
        """`SOBEL_X_KERNEL` is `[0.5, 0, -0.5, ...]` -- a plain JS Array of
        Numbers, NOT a Float32Array. Reading the GLSL type (`float[9]`) is
        exactly how a port gets this wrong."""
        module = _module()
        self.assertEqual("double", module._NATIVE_ELEMENT_TYPE["float"])
        for table in module.table_contract(KEY)[1:]:
            with self.subTest(table=table.name):
                self.assertEqual("float[9]", table.glsl_type)
                self.assertEqual("double", table.native_element_type)
                self.assertNotEqual("float", table.native_element_type)

    def test_ivec2_elements_map_to_the_exact_integer_native_vector(self):
        module = _module()
        table = module.table_contract(KEY)[0]
        self.assertEqual("ivec2[9]", table.glsl_type)
        self.assertEqual("glsl::IVec2", table.native_element_type)
        self.assertEqual("glsl::IVec2", module._NATIVE_ELEMENT_TYPE["ivec2"])

    def test_the_frozen_mapping_agrees_with_the_emitter_type_tables(self):
        """`local_type()` is what makes the double contract correct by
        construction. The profile asserts the mapping instead of inheriting
        it, so a future change to `local_type()` turns this red."""
        module = _module()
        emit = importlib.import_module("tools.glslcpp.emit_typed_cpp")
        self.assertEqual("double", module._NATIVE_ELEMENT_TYPE["float"])
        self.assertIn('return "double" if value.display() == "float"',
                      pathlib.Path(emit.__file__).read_text(encoding="utf-8"))
        for name, native in module._NATIVE_ELEMENT_TYPE.items():
            if name == "float":
                continue
            with self.subTest(element=name):
                self.assertEqual(emit._TYPES[name], native)

    def test_the_element_type_check_is_an_allowlist_of_pool_safe_types(self):
        """Design amendment S15. `SOBEL_OFFSETS`'s elements are pooled
        `Int32Array`s that survive the render only because `beginPixel`
        restores the integer pool to a snapshotted base index. The float pool
        has no such base (`this.indices.fill(0)`), so a factory-scope
        `PooledFloat32Array` table is aliased and clobbered by the first
        per-pixel scratch allocation.
        """
        module = _module()
        self.assertEqual(
            {"float", "int", "uint", "ivec2", "ivec3", "ivec4",
             "uvec2", "uvec3", "uvec4"},
            set(module._POOL_SAFE_ELEMENT_TYPES))
        self.assertIsInstance(module._POOL_SAFE_ELEMENT_TYPES, frozenset)
        for hazard in ("vec2", "vec3", "vec4"):
            with self.subTest(element=hazard):
                self.assertNotIn(hazard, module._POOL_SAFE_ELEMENT_TYPES)
        self.assertEqual(set(module._POOL_SAFE_ELEMENT_TYPES),
                         set(module._NATIVE_ELEMENT_TYPE))
        self.assertEqual(set(module._POOL_SAFE_ELEMENT_TYPES),
                         set(module._ELEMENT_LANES))

    def test_a_float_vector_element_type_is_refused_by_the_allowlist(self):
        """A `vec2[9]` const global satisfies every other predicate and would
        silently disagree with the authority. Checked at the predicate."""
        module = _module()
        program = _analyzed()
        record = module._LOCKS[KEY]["admitted"][0]
        declaration = program.declarations[OFFSETS_ORDINAL]
        self.assertTrue(
            module._element_type_allowlisted_holds(declaration, record))
        for hazard, lanes in (("vec2", 2), ("vec3", 3), ("vec4", 4)):
            with self.subTest(element=hazard):
                candidate = _analyzed()
                target = candidate.declarations[OFFSETS_ORDINAL]
                object.__setattr__(
                    target, "type", array(vector("float", lanes), 9))
                self.assertEqual(f"{hazard}[9]", target.type.display())
                self.assertFalse(module._element_type_allowlisted_holds(
                    target, record._replace(element_type=hazard,
                                            glsl_type=f"{hazard}[9]")))

    def test_the_full_allowlist_is_accepted_by_the_predicate(self):
        """Every one of the nine really passes -- the allowlist is not eight
        dead entries plus `ivec2`."""
        module = _module()
        program = _analyzed()
        record = module._LOCKS[KEY]["admitted"][0]
        bases = {"float": ("scalar", "float"), "int": ("scalar", "int"),
                 "uint": ("scalar", "uint")}
        for element in sorted(module._POOL_SAFE_ELEMENT_TYPES):
            with self.subTest(element=element):
                candidate = _analyzed()
                target = candidate.declarations[OFFSETS_ORDINAL]
                if element in bases:
                    from tools.glslcpp.frontend.semantic_types import SCALARS
                    item = SCALARS[element]
                else:
                    prefix = {"i": "int", "u": "uint"}[element[0]]
                    item = vector(prefix, int(element[-1]))
                object.__setattr__(target, "type", array(item, 9))
                self.assertEqual(f"{element}[9]", target.type.display())
                self.assertTrue(module._element_type_allowlisted_holds(
                    target, record._replace(element_type=element,
                                            glsl_type=f"{element}[9]")))
        del program

    def test_the_module_records_the_pooling_argument_it_depends_on(self):
        """S15's reasoning is the load-bearing justification for the
        allowlist; it must be written down where the allowlist lives."""
        module = _module()
        source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
        for token in ("beginPixel", "signedBaseIndices", "indices.fill(0)",
                      "PooledFloat32Array", "necessary but"):
            with self.subTest(token=token):
                self.assertIn(token, source)


class ConstGlobalTableAdmissionTests(unittest.TestCase):
    def test_authenticates_all_three_declarations_in_declaration_order(self):
        module = _module()
        program = _analyzed()
        admitted = module.authenticate_const_global_tables(
            program, RAW_SHA256, PROFILE)
        self.assertIsInstance(admitted, tuple)
        self.assertEqual(3, len(admitted),
                         "the validator reports one site; there are three")
        self.assertIs(program.declarations[OFFSETS_ORDINAL], admitted[0])
        self.assertIs(program.declarations[X_KERNEL_ORDINAL], admitted[1])
        self.assertIs(program.declarations[Y_KERNEL_ORDINAL], admitted[2])
        self.assertEqual(["SOBEL_OFFSETS", "SOBEL_X_KERNEL", "SOBEL_Y_KERNEL"],
                         [item.symbol.name for item in admitted])
        self.assertEqual(["ivec2[9]", "float[9]", "float[9]"],
                         [item.type.display() for item in admitted])
        for item in admitted:
            self.assertEqual("const", item.symbol.storage)
            self.assertFalse(item.symbol.writable)
            self.assertIsNotNone(item.initializer)
            self.assertEqual("construct", item.initializer.kind)
            self.assertEqual(9, len(item.initializer.children))

    def test_apply_returns_the_same_object_it_was_given(self):
        """`generate_typed_slice` asserts `profiled is not typed` and raises
        "identity profile mutated program" for every sibling profile."""
        module = _module()
        program = _analyzed()
        self.assertIs(program, module.apply_const_global_tables(
            program, RAW_SHA256, PROFILE))

    def test_rejects_missing_wrong_and_foreign_carrier_names(self):
        module = _module()
        program = _analyzed()
        for carrier in (None, "", "wrong", "const-global-nine-table-v2",
                        "as-u32-round-admission-v1",
                        "mutable-global-frame-shape-v1",
                        "fixed-nine-local-literal-init-counted-read-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError, "exact profile carrier required"):
                module.authenticate_const_global_tables(
                    program, RAW_SHA256, carrier)

    def test_foreign_key_returns_empty_and_names_normalmap_when_supplied(self):
        module = _module()
        foreign = _foreign()
        self.assertEqual((), module.authenticate_const_global_tables(
            foreign, _hash(FOREIGN_SOURCE), None))
        for carrier in (PROFILE, "wrong", "as-u32-round-admission-v1"):
            with self.subTest(carrier=carrier), self.assertRaisesRegex(
                    ValueError,
                    "not an admitted const-global nine-table carrier"):
                module.authenticate_const_global_tables(
                    foreign, _hash(FOREIGN_SOURCE), carrier)

    def test_the_foreign_fixture_really_carries_the_construct(self):
        """The rejection at the widened boundary must be about identity, not
        about the construct being absent from the foreign program."""
        foreign = _foreign()
        arrays = [item for item in foreign.declarations
                  if item.type.kind == "array"]
        self.assertEqual(["TAPS"], [item.symbol.name for item in arrays])
        self.assertEqual("float[9]", arrays[0].type.display())
        self.assertEqual("const", arrays[0].symbol.storage)
        self.assertIsNotNone(arrays[0].initializer)
        self.assertEqual(9, len(arrays[0].initializer.children))

    def test_rejects_a_wrong_caller_source_hash(self):
        module = _module()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_const_global_tables(
                _analyzed(), "0" * 64, PROFILE)

    def test_source_drift_fails_the_caller_hash_lock(self):
        module = _module()
        original = SOURCE.read_text(encoding="utf-8")
        mutated = original + "\n// planted\n"
        self.assertNotEqual(original, mutated)
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_const_global_tables(
                _analyzed(raw=mutated), _hash(mutated), PROFILE)

    def test_source_drift_behind_a_correct_caller_hash_fails_the_raw_lock(self):
        module = _module()
        mutated = SOURCE.read_text(encoding="utf-8") + "\n// planted\n"
        with self.assertRaisesRegex(ValueError, "raw source drift"):
            module.authenticate_const_global_tables(
                _analyzed(raw=mutated), RAW_SHA256, PROFILE)

    def test_normalized_drift_fails_the_normalized_lock(self):
        module = _module()
        original = SOURCE.read_text(encoding="utf-8")
        mutated = original.replace("const uint CHANNEL_CAP = 4u;",
                                   "const uint CHANNEL_CAP =  4u;")
        self.assertNotEqual(original, mutated)
        candidate = _analyzed(raw=mutated)
        locks = _relocked_partial(module, candidate, "normalized")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError, "normalized source drift"):
            module.authenticate_const_global_tables(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_typed_function_drift_fails_the_function_fingerprint_lock(self):
        module = _module()
        candidate = _analyzed()
        host = _fn(candidate, "clamp01").body[0].expressions[0]
        object.__setattr__(host, "children",
                           (*host.children,
                            dataclasses.replace(host.children[0])))
        locks = _relocked_partial(module, candidate, "functions")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError,
                                       "typed function fingerprint drift"):
            module.authenticate_const_global_tables(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_declaration_drift_fails_the_whole_program_lock(self):
        module = _module()
        candidate = _analyzed()
        object.__setattr__(_declaration(candidate, "CHANNEL_CAP").initializer,
                           "literal", "5u")
        locks = _relocked_partial(module, candidate, "whole")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError,
                                       "whole-program fingerprint drift"):
            module.authenticate_const_global_tables(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_declaration_drift_also_fails_the_interface_lock(self):
        """The interface fingerprint is a subset of the whole-program one, so
        it can only be reached with the whole-program hash refrozen."""
        module = _module()
        candidate = _analyzed()
        object.__setattr__(_declaration(candidate, "CHANNEL_CAP").initializer,
                           "literal", "5u")
        locks = _relocked_partial(module, candidate, "interface")
        with mock.patch.object(module, "_LOCKS", locks), \
                self.assertRaisesRegex(ValueError,
                                       "interface fingerprint drift"):
            module.authenticate_const_global_tables(
                candidate, locks[KEY]["raw_sha256"], PROFILE)

    def test_unrelated_proof_carrier_is_rejected(self):
        module = _module()
        for field in module._OPTIONAL_PROOF_FIELDS:
            with self.subTest(field=field):
                candidate = dataclasses.replace(_analyzed(),
                                                **{field: object()})
                with self.assertRaisesRegex(
                        ValueError, "unrelated proof carrier is not absent"):
                    module.authenticate_const_global_tables(
                        candidate, RAW_SHA256, PROFILE)

    def test_define_drift_fails_the_exact_define_lock_not_the_coarse_gate(self):
        """normalMap has NO defines. The lock is per key, never a hardcoded
        `program.preprocessor_defines != ()`."""
        module = _module()
        self.assertEqual((), module._LOCKS[KEY]["defines"])
        self.assertEqual({}, generate_typed_slice._defaults(ROOT, KEY))
        for label, defines in (("one define", {"EXTRA": 7}),
                               ("two defines", {"A": 1, "B": 2})):
            with self.subTest(axis=label):
                candidate = _analyzed(defines=defines)
                self.assertNotEqual((), candidate.preprocessor_defines)
                _expect(self, module, candidate,
                        _relocked(module, candidate),
                        "exact preprocessor define lock mismatch")


class ConstGlobalTableReadAccessorTests(unittest.TestCase):
    """`authenticate_const_global_table_reads` -- node identity for authorities.

    The design requires both authorities to admit the three `TABLE[i]` reads
    the way `authorized_grade_index_sites` is admitted -- `any(value is item)`
    -- rather than re-deriving structure and relying on this census having
    run. These tests hold the accessor to that: the nodes it hands back must
    be the caller's own objects, located here **independently** of the
    module's census, and it must fail closed wherever the declaration
    accessor does.
    """

    def _reads(self, program=None):
        module = _module()
        program = _analyzed() if program is None else program
        return module, program, module.authenticate_const_global_table_reads(
            program, RAW_SHA256, PROFILE)

    def test_returns_three_reads_in_frozen_declaration_order(self):
        module, program, reads = self._reads()
        self.assertIsInstance(reads, tuple)
        self.assertEqual(3, len(reads))
        self.assertEqual(("SOBEL_OFFSETS", "SOBEL_X_KERNEL", "SOBEL_Y_KERNEL"),
                         tuple(item.name for item in reads))
        self.assertEqual((OFFSETS_ID, X_KERNEL_ID, Y_KERNEL_ID),
                         tuple(item.symbol_id for item in reads))
        self.assertEqual(("138:24-138:40", "144:23-144:40", "145:23-145:40"),
                         tuple(item.span for item in reads))
        # Read order IS declaration order, so an authority can zip the two.
        declarations = module.authenticate_const_global_tables(
            program, RAW_SHA256, PROFILE)
        self.assertEqual(tuple(item.symbol.id for item in declarations),
                         tuple(item.symbol_id for item in reads))
        self.assertEqual(tuple(module.table_contract(KEY)),
                         tuple(item.table for item in reads))

    def test_the_returned_nodes_are_the_real_nodes_by_object_identity(self):
        """Located independently by walking `main` here, not by trusting the
        module's own census -- span equality would not prove identity."""
        module, program, reads = self._reads()
        del module
        for item in reads:
            with self.subTest(table=item.name):
                located, _parent = _index_node(program, item.name)
                self.assertIs(located, item.node)
                self.assertIs(located.children[0], item.base)
                self.assertIs(located.children[1], item.index)

    def test_the_nodes_are_the_index_the_base_and_the_induction_variable(self):
        module, program, reads = self._reads()
        loop = _main(program).body[LOOP_STATEMENT_INDEX]
        for item in reads:
            with self.subTest(table=item.name):
                self.assertEqual("index", item.node.kind)
                self.assertEqual("readonly lvalue", item.node.category)
                self.assertEqual("id", item.base.kind)
                self.assertEqual(item.symbol_id, item.base.symbol_id)
                self.assertEqual(item.table.glsl_type,
                                 item.base.type.display())
                self.assertEqual("id", item.index.kind)
                self.assertEqual("int", item.index.type.display())
                self.assertEqual(loop.loop_proof.induction_symbol_id,
                                 item.index.symbol_id)
                self.assertEqual(LOOP_INDEX_SYMBOL, item.index.symbol_id)
        self.assertEqual(9, len({id(item.node) for item in reads}
                                | {id(item.base) for item in reads}
                                | {id(item.index) for item in reads}),
                         "nine distinct nodes, no aliasing between reads")
        del module

    def test_an_authority_can_admit_a_read_with_the_sibling_identity_idiom(self):
        """The exact shape `generate_typed_slice`'s index arm uses for
        `authorized_grade_index_sites`."""
        module, program, reads = self._reads()
        del module
        for name in ("SOBEL_OFFSETS", "SOBEL_X_KERNEL", "SOBEL_Y_KERNEL"):
            node, _ = _index_node(program, name)
            with self.subTest(table=name):
                self.assertTrue(any(node is item.node for item in reads))
        # And a node that is NOT an authenticated read is not admitted.
        other = _main(program).body[LOOP_STATEMENT_INDEX]
        self.assertFalse(any(other is item.node for item in reads))

    def test_a_foreign_key_yields_no_reads_and_names_normalmap_when_supplied(self):
        module = _module()
        foreign = _foreign()
        self.assertEqual((), module.authenticate_const_global_table_reads(
            foreign, _hash(FOREIGN_SOURCE), None))
        with self.assertRaisesRegex(
                ValueError, "not an admitted const-global nine-table carrier"):
            module.authenticate_const_global_table_reads(
                foreign, _hash(FOREIGN_SOURCE), PROFILE)

    def test_both_accessors_run_one_authentication_path(self):
        """Structural, not behavioural: neither public accessor may carry lock
        logic of its own, or the two authorities would be re-authenticating
        different things."""
        module = _module()
        tree = ast.parse(
            pathlib.Path(module.__file__).read_text(encoding="utf-8"))
        bodies = {node.name: node for node in tree.body
                  if isinstance(node, ast.FunctionDef)}
        for name in ("authenticate_const_global_tables",
                     "authenticate_const_global_table_reads"):
            with self.subTest(accessor=name):
                node = bodies[name]
                calls = [item.func.id for item in ast.walk(node)
                         if isinstance(item, ast.Call)
                         and isinstance(item.func, ast.Name)]
                self.assertEqual(["_authenticate"], calls)
                statements = [item for item in node.body
                              if not (isinstance(item, ast.Expr)
                                      and isinstance(item.value, ast.Constant))]
                self.assertEqual(1, len(statements),
                                 "the accessor must be a pure projection")

    def test_the_read_accessor_fails_closed_wherever_declarations_do(self):
        """Every lock, both entry points, byte-identical message."""
        module = _module()

        def respan(candidate):
            node, _ = _index_node(candidate, "SOBEL_X_KERNEL")
            object.__setattr__(node, "span",
                               dataclasses.replace(node.span, end_column=41))

        def storage(candidate):
            object.__setattr__(
                candidate.declarations[OFFSETS_ORDINAL].symbol,
                "storage", "global")

        def post_write(candidate):
            node, parent = _index_node(candidate, "SOBEL_Y_KERNEL")
            _replace_child(parent, node,
                           dataclasses.replace(node, kind="post",
                                               operator="++",
                                               children=(node,)))

        def trip_count(candidate):
            loop = _main(candidate).body[LOOP_STATEMENT_INDEX]
            object.__setattr__(
                loop, "loop_proof",
                dataclasses.replace(loop.loop_proof, trip_count=12,
                                    bound_value=12))

        def literal_only(candidate):
            initializer = candidate.declarations[
                X_KERNEL_ORDINAL].initializer
            original = initializer.children[0]
            channel = _declaration(candidate, "CHANNEL_COUNT")
            object.__setattr__(
                initializer, "children",
                (dataclasses.replace(original, kind="id", literal=None,
                                     literal_value=None,
                                     symbol_id=channel.symbol.id,
                                     symbol=channel.symbol),
                 *initializer.children[1:]))

        def resources(candidate):
            object.__setattr__(
                candidate, "resources",
                dataclasses.replace(candidate.resources,
                                    uses_derivatives=True))

        for label, mutate in (("respanned read", respan),
                              ("storage drift", storage),
                              ("postfix write", post_write),
                              ("overrunning loop", trip_count),
                              ("non-literal initializer", literal_only),
                              ("resource drift", resources)):
            with self.subTest(axis=label):
                candidate = _analyzed()
                mutate(candidate)
                locks = _relocked(module, candidate)
                locks[KEY].update(_recount(module, candidate))
                messages = []
                for accessor in (module.authenticate_const_global_tables,
                                 module.authenticate_const_global_table_reads,
                                 module.apply_const_global_tables):
                    with mock.patch.object(module, "_LOCKS", locks), \
                            self.assertRaises(ValueError) as raised:
                        accessor(candidate, locks[KEY]["raw_sha256"], PROFILE)
                    messages.append(str(raised.exception))
                self.assertEqual(1, len(set(messages)), messages)
                for coarse in COARSE:
                    self.assertNotIn(coarse, messages[0])

    def test_the_read_accessor_rejects_a_wrong_hash_and_a_wrong_carrier(self):
        module = _module()
        program = _analyzed()
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.authenticate_const_global_table_reads(
                program, "0" * 64, PROFILE)
        with self.assertRaisesRegex(ValueError,
                                    "exact profile carrier required"):
            module.authenticate_const_global_table_reads(
                program, RAW_SHA256, "const-global-nine-table-v2")

    def test_the_read_accessor_is_covered_by_the_visitation_ledger(self):
        module = _module()
        with mock.patch.object(module, "_CONSUMED_LEDGER", 19), \
                self.assertRaisesRegex(
                    ValueError,
                    "const-global-nine-table visitation ledger mismatch"):
            module.authenticate_const_global_table_reads(
                _analyzed(), RAW_SHA256, PROFILE)

    def test_apply_still_returns_the_same_object_and_still_authenticates(self):
        module = _module()
        program = _analyzed()
        self.assertIs(program, module.apply_const_global_tables(
            program, RAW_SHA256, PROFILE))
        with self.assertRaisesRegex(ValueError,
                                    "exact caller source hash required"):
            module.apply_const_global_tables(program, "0" * 64, PROFILE)


class ConstGlobalTableDeclarationTests(unittest.TestCase):
    """Identity, order, storage, element type, initializer -- per table."""

    def test_the_three_admitted_records_are_the_real_declarations(self):
        module = _module()
        program = _analyzed()
        records = module._LOCKS[KEY]["admitted"]
        self.assertEqual(3, len(records))
        for record in records:
            declaration = program.declarations[record.ordinal]
            self.assertEqual(record.symbol_id, declaration.symbol.id)
            self.assertEqual(record.name, declaration.symbol.name)
            self.assertEqual(record.glsl_type, declaration.type.display())
            self.assertEqual(record.element_type,
                             declaration.type.element.display())
            self.assertEqual(record.storage, declaration.symbol.storage)
            self.assertEqual(record.writable, declaration.symbol.writable)
            self.assertEqual(record.declaration_span, module._span(declaration))
            self.assertEqual(record.symbol_span,
                             module._span(declaration.symbol))
            self.assertEqual(record.declaration_sha256, module._sha(declaration))
            self.assertEqual(record.symbol_sha256,
                             module._sha(declaration.symbol))
            self.assertEqual(record.initializer_sha256,
                             module._sha(declaration.initializer))
            self.assertEqual(record.initializer_span,
                             module._span(declaration.initializer))
        self.assertEqual((OFFSETS_ORDINAL, X_KERNEL_ORDINAL, Y_KERNEL_ORDINAL),
                         tuple(item.ordinal for item in records))
        self.assertEqual((OFFSETS_ID, X_KERNEL_ID, Y_KERNEL_ID),
                         tuple(item.symbol_id for item in records))

    def test_the_element_spans_are_the_real_element_spans(self):
        module = _module()
        program = _analyzed()
        for record in module._LOCKS[KEY]["admitted"]:
            with self.subTest(table=record.name):
                initializer = program.declarations[record.ordinal].initializer
                self.assertEqual(
                    record.table.element_spans,
                    tuple(module._span(child)
                          for child in initializer.children))

    def test_the_three_tables_are_the_only_array_declarations(self):
        module = _module()
        program = _analyzed()
        self.assertEqual(11, len(program.declarations))
        self.assertEqual(11, module._LOCKS[KEY]["declaration_count"])
        arrays = [item.symbol.name for item in program.declarations
                  if item.type.kind == "array"]
        self.assertEqual(["SOBEL_OFFSETS", "SOBEL_X_KERNEL", "SOBEL_Y_KERNEL"],
                         arrays)
        self.assertEqual(module._LOCKS[KEY]["bindings"],
                         module._binding_table(program))

    def test_every_admitted_table_is_const_and_not_writable(self):
        program = _analyzed()
        for name in ("SOBEL_OFFSETS", "SOBEL_X_KERNEL", "SOBEL_Y_KERNEL"):
            with self.subTest(table=name):
                declaration = _declaration(program, name)
                self.assertEqual("const", declaration.symbol.storage)
                self.assertFalse(declaration.symbol.writable)

    def test_the_frozen_function_inventory_is_the_real_inventory(self):
        module = _module()
        program = _analyzed()
        self.assertEqual(10, len(program.functions))
        self.assertEqual(10, module._LOCKS[KEY]["function_count"])
        self.assertEqual(module._LOCKS[KEY]["function_inventory"],
                         module._function_inventory(program))
        self.assertIn((MAIN_ID, "main", "void", 0, 19, "113:1-154:2"),
                      module._LOCKS[KEY]["function_inventory"])


class ConstGlobalTableLiteralOnlyTests(unittest.TestCase):
    """Design S4.3.4 -- and why it is necessary but NOT sufficient."""

    def test_the_real_initializers_are_literal_only(self):
        module = _module()
        program = _analyzed()
        for record in module._LOCKS[KEY]["admitted"]:
            with self.subTest(table=record.name):
                self.assertTrue(module._literal_only_initializer_holds(
                    program.declarations[record.ordinal], record))

    def test_signed_literals_are_accepted_and_other_unary_operators_are_not(self):
        module = _module()
        program = _analyzed()
        offsets = program.declarations[OFFSETS_ORDINAL].initializer
        negatives = [node for node, _, _ in module._walk_expression(offsets)
                     if node.kind == "unary"]
        self.assertTrue(negatives, "the offsets table has unary minus nodes")
        for node in negatives:
            self.assertEqual("-", node.operator)
            self.assertTrue(module._literal_atom_holds(node))
        for operator in ("!", "~"):
            with self.subTest(operator=operator):
                self.assertFalse(module._literal_atom_holds(
                    dataclasses.replace(negatives[0], operator=operator)))

    def test_an_initializer_reading_an_earlier_admitted_global_is_rejected(self):
        """The const-float and const-vec3 global grammars elsewhere in the
        generator explicitly permit an `id` naming an earlier admitted const
        (`generate_typed_slice.py`: "global initializer dependency must name an
        earlier admitted const float"). This mechanism must not, because the
        emitter re-evaluates these tables once per pixel.
        """
        module = _module()
        generator_source = (
            ROOT / "tools/glslcpp/generate_typed_slice.py").read_text(
                encoding="utf-8")
        self.assertIn(
            "global initializer dependency must name an earlier admitted "
            "const float", generator_source,
            "the sibling grammar really does permit an id reference")

        candidate = _analyzed()
        initializer = candidate.declarations[X_KERNEL_ORDINAL].initializer
        original = initializer.children[0]
        channel_count = _declaration(candidate, "CHANNEL_COUNT")
        planted = dataclasses.replace(
            original, kind="id", literal=None, literal_value=None,
            symbol_id=channel_count.symbol.id, symbol=channel_count.symbol)
        self.assertEqual("id", planted.kind)
        object.__setattr__(initializer, "children",
                           (planted, *initializer.children[1:]))
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "const global table initializer is not literal-only")

    def test_binary_arithmetic_in_an_initializer_is_rejected(self):
        module = _module()
        candidate = _analyzed()
        initializer = candidate.declarations[Y_KERNEL_ORDINAL].initializer
        original = initializer.children[0]
        planted = dataclasses.replace(
            original, kind="binary", operator="+", literal=None,
            literal_value=None,
            children=(dataclasses.replace(original),
                      dataclasses.replace(original)))
        object.__setattr__(initializer, "children",
                           (planted, *initializer.children[1:]))
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "const global table initializer is not literal-only")

    def test_a_nested_ivec2_element_with_a_non_literal_lane_is_rejected(self):
        module = _module()
        candidate = _analyzed()
        initializer = candidate.declarations[OFFSETS_ORDINAL].initializer
        element = initializer.children[4]
        self.assertEqual("construct", element.kind)
        lane = element.children[0]
        planted = dataclasses.replace(
            lane, kind="binary", operator="*",
            children=(dataclasses.replace(lane), dataclasses.replace(lane)))
        object.__setattr__(element, "children",
                           (planted, *element.children[1:]))
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "const global table initializer is not literal-only")

    def test_a_wrong_lane_count_in_an_ivec2_element_is_rejected(self):
        module = _module()
        candidate = _analyzed()
        initializer = candidate.declarations[OFFSETS_ORDINAL].initializer
        element = initializer.children[4]
        object.__setattr__(element, "children",
                           (*element.children,
                            dataclasses.replace(element.children[0])))
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "const global table initializer is not literal-only")

    def test_an_initializer_that_is_not_a_nine_element_construct_is_rejected(self):
        module = _module()
        candidate = _analyzed()
        declaration = candidate.declarations[X_KERNEL_ORDINAL]
        object.__setattr__(declaration.initializer, "children",
                           declaration.initializer.children[:8])
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "const global table initializer is not a nine-element array "
                "construct")

    def test_literal_only_is_documented_as_necessary_but_not_sufficient(self):
        """Design amendment S15 retracts S3.1's reasoning. The module must not
        claim literal-only initializers prove per-pixel equivalence."""
        module = _module()
        source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
        self.assertIn("necessary but", source)
        self.assertIn("element materialization", source)


class ConstGlobalTableCensusTests(unittest.TestCase):
    def test_the_admitted_symbol_map_is_derived_per_key_not_at_import(self):
        module = _module()
        self.assertFalse(hasattr(module, "_ADMITTED_SYMBOLS"),
                         "no import-time global bound to NORMAL_MAP_KEY")
        self.assertEqual(
            {OFFSETS_ID: "SOBEL_OFFSETS", X_KERNEL_ID: "SOBEL_X_KERNEL",
             Y_KERNEL_ID: "SOBEL_Y_KERNEL"},
            module._admitted_symbols(module._LOCKS[KEY]))
        other = copy.deepcopy(module._LOCKS[KEY])
        other["admitted"] = (other["admitted"][0]._replace(symbol_id=77),)
        self.assertEqual({77: "SOBEL_OFFSETS"}, module._admitted_symbols(other))
        import inspect
        for name in ("_reference_census", "_no_write_holds"):
            with self.subTest(consumer=name):
                signature = inspect.signature(getattr(module, name))
                self.assertIn("symbols", signature.parameters)
                self.assertIs(inspect.Parameter.empty,
                              signature.parameters["symbols"].default)

    def test_the_frozen_program_wide_counts_are_the_real_counts(self):
        module = _module()
        program = _analyzed()
        total, assigns = module._node_census(program)
        self.assertEqual(401, total)
        self.assertEqual(6, assigns)
        self.assertEqual(total, module._LOCKS[KEY]["total_nodes"])
        self.assertEqual(assigns, module._LOCKS[KEY]["total_assigns"])

    def test_the_index_read_census_is_exactly_three_sites_in_main(self):
        module = _module()
        program = _analyzed()
        sites, references = module._reference_census(
            program, module._admitted_symbols(module._LOCKS[KEY]))
        self.assertEqual(3, len(sites))
        self.assertEqual([OFFSETS_ID, X_KERNEL_ID, Y_KERNEL_ID],
                         [item.symbol_id for item in sites])
        self.assertEqual(["138:24-138:40", "144:23-144:40", "145:23-145:40"],
                         [item.span for item in sites])
        self.assertEqual(["main", "main", "main"],
                         [item.record.owner_name for item in sites])
        self.assertEqual([LOOP_INDEX_SYMBOL] * 3,
                         [item.record.index_symbol_id for item in sites])
        self.assertEqual(module._LOCKS[KEY]["index_sites"],
                         tuple(item.record for item in sites))
        del references

    def test_the_index_site_category_is_readonly_lvalue_not_readonly(self):
        """Design amendment S16. `body_semantic.py:156` spells the category
        `"readonly lvalue"`; a predicate written `== "readonly"` fails closed
        but with the wrong message."""
        module = _module()
        program = _analyzed()
        sites, _ = module._reference_census(
            program, module._admitted_symbols(module._LOCKS[KEY]))
        for item in sites:
            with self.subTest(table=item.name):
                self.assertEqual("readonly lvalue", item.record.category)
                self.assertNotEqual("readonly", item.record.category)
        source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
        self.assertIn('== "readonly lvalue"', source)
        semantic = (ROOT / "tools/glslcpp/frontend/body_semantic.py").read_text(
            encoding="utf-8")
        self.assertIn('"lvalue" if symbol.writable else "readonly lvalue"',
                      semantic)

    def test_the_readonly_category_is_what_covers_out_and_inout_arguments(self):
        """`shape-design.md` Amendment 2's carried instruction. The coverage is
        predicate 6's category check, not the mutation-kind list:
        `body_semantic.py:325` requires `argument.category == "lvalue"` for an
        `out`/`inout` parameter, which `"readonly lvalue"` is not."""
        semantic = (ROOT / "tools/glslcpp/frontend/body_semantic.py").read_text(
            encoding="utf-8")
        self.assertIn(
            'if parameter.direction in {"out", "inout"} and '
            'argument.category != "lvalue": valid = False', semantic)

    def test_the_bare_reference_census_is_exactly_three_index_bases(self):
        module = _module()
        program = _analyzed()
        sites, references = module._reference_census(
            program, module._admitted_symbols(module._LOCKS[KEY]))
        self.assertEqual(3, len(references))
        self.assertEqual(["138:24-138:37", "144:23-144:37", "145:23-145:37"],
                         [item.span for item in references])
        self.assertEqual(["index"] * 3,
                         [item.record.parent_kind for item in references])
        self.assertEqual(module._LOCKS[KEY]["bare_references"],
                         tuple(item.record for item in references))
        self.assertEqual(sorted(id(item.node) for item in references),
                         sorted(id(item.base) for item in sites))

    def test_the_reads_sit_inside_the_real_nine_trip_counted_loop(self):
        module = _module()
        program = _analyzed()
        main = _main(program)
        loop = main.body[LOOP_STATEMENT_INDEX]
        self.assertEqual("for", loop.kind)
        proof = loop.loop_proof
        self.assertEqual(0, proof.start_value)
        self.assertEqual(9, proof.bound_value)
        self.assertEqual("<", proof.comparison)
        self.assertEqual("++", proof.update)
        self.assertEqual(9, proof.trip_count)
        self.assertEqual(LOOP_INDEX_SYMBOL, proof.induction_symbol_id)
        self.assertEqual(1, len([item for item in main.body
                                 if item.kind == "for"]))
        sites, _ = module._reference_census(
            program, module._admitted_symbols(module._LOCKS[KEY]))
        for item in sites:
            with self.subTest(table=item.name):
                self.assertIs(loop, item.chain[0])
                self.assertEqual(proof.induction_symbol_id,
                                 item.index.symbol_id)

    def test_the_census_walks_global_declaration_initializers(self):
        """The three initializers are the subject matter, and the validator's
        own walks never visit them, so a node planted in `CHANNEL_COUNT`'s
        initializer must be caught by the census rather than by a refreezable
        coarse hash."""
        module = _module()
        candidate = _analyzed()
        initializer = _declaration(candidate, "CHANNEL_COUNT").initializer
        object.__setattr__(initializer, "children",
                           (dataclasses.replace(initializer),))
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "global declaration initializer census mismatch")

    def test_a_reference_hidden_in_a_global_initializer_is_censused(self):
        """A table reference planted in `CHANNEL_CAP`'s initializer is outside
        every walker that only descends `function.body`. It must not escape."""
        module = _module()
        candidate = _analyzed()
        base, _ = _index_node(candidate, "SOBEL_X_KERNEL")
        planted = dataclasses.replace(base.children[0])
        self.assertEqual(X_KERNEL_ID, planted.symbol_id)
        target = _declaration(candidate, "CHANNEL_CAP")
        object.__setattr__(target.initializer, "children", (planted,))
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        message = _expect(self, module, candidate, locks,
                          "global declaration initializer census mismatch")
        # And with the initializer census deleted, the bare-reference census --
        # which also descends declarations -- still sees the fourth reference.
        scratch = _scratch(module, "_initializer_census_holds")
        with mock.patch.object(scratch, "_LOCKS", locks), \
                self.assertRaises(ValueError) as raised:
            scratch.authenticate_const_global_tables(
                candidate, locks[KEY]["raw_sha256"], PROFILE)
        self.assertIn("const global table bare reference census mismatch: 4",
                      str(raised.exception))
        del message

    def test_a_read_inside_a_global_initializer_records_no_statement_index(self):
        """The `function is None` branch of `_reference_census`, exercised.

        A global initializer has no enclosing statement, and `path[0]` there
        is an expression CHILD index -- so a read planted at depth one would
        record `statement_index=0`, a real statement position, if the branch
        were written `-1 if not path else path[0]`.
        """
        module = _module()
        candidate = _analyzed()
        node, _ = _index_node(candidate, "SOBEL_X_KERNEL")
        planted = dataclasses.replace(
            node, children=(dataclasses.replace(node.children[0]),
                            dataclasses.replace(node.children[1])))
        target = _declaration(candidate, "CHANNEL_CAP")
        object.__setattr__(target.initializer, "children", (planted,))
        sites, references = module._reference_census(
            candidate, module._admitted_symbols(module._LOCKS[KEY]))
        hosted = [item for item in sites if item.record.owner_id < 0]
        self.assertEqual(1, len(hosted), "the planted read must be censused")
        self.assertEqual("<global-initializer>", hosted[0].record.owner_name)
        self.assertEqual(-1, hosted[0].record.statement_index)
        self.assertNotEqual(0, hosted[0].record.statement_index)
        # The same field still carries the REAL statement index in a body.
        in_body = [item for item in sites if item.record.owner_id >= 0]
        self.assertEqual(3, len(in_body))
        self.assertEqual([LOOP_STATEMENT_INDEX] * 3,
                         [item.record.statement_index for item in in_body])
        self.assertEqual(
            ["<global-initializer>"],
            [item.record.owner_name for item in references
             if item.record.owner_id < 0])

    def test_the_validator_walks_only_function_bodies(self):
        """Design amendment S16: this closure is the SOLE authority on the
        three initializers, because the validator's generic walk and its write
        audit both iterate `program.functions` only."""
        source = (ROOT / "tools/glslcpp/generate_typed_slice.py").read_text(
            encoding="utf-8")
        self.assertIn("for function in typed.functions:\n"
                      "        for statement_value in function.body:\n"
                      "            audit_statement(statement_value)", source)


class ConstGlobalTableMutationBarrierTests(unittest.TestCase):
    """`post` is a distinct IR kind from `unary`, not an operator of it."""

    def _with_post_write(self, module, candidate):
        """Wrap `SOBEL_X_KERNEL[i]` in a postfix `++`.

        Deliberately invisible to both censuses: the index node and its base
        `id` survive unchanged with the same spans, hashes and parents, so only
        the mutation barrier can see the new node.
        """
        node, parent = _index_node(candidate, "SOBEL_X_KERNEL")
        post = dataclasses.replace(node, kind="post", operator="++",
                                   children=(node,))
        self.assertEqual("post", post.kind)
        _replace_child(parent, node, post)
        return post

    def test_the_ir_really_spells_postfix_increment_as_kind_post(self):
        semantic = (ROOT / "tools/glslcpp/frontend/body_semantic.py").read_text(
            encoding="utf-8")
        self.assertIn('return TypedExpression("post", x.type, loc, "rvalue", '
                      'children=(x,), operator=node["op"])', semantic)
        module = _module()
        self.assertEqual(("assign", "unary", "post"), module._MUTATION_KINDS)

    def test_a_postfix_write_SLIPS_THROUGH_a_barrier_that_omits_post(self):
        """Reproduce the miss before relying on the fix.

        The `synth/shape` closure shipped `("assign", "unary")` on its first
        draft. With that list this postfix write is invisible -- and, because
        it is also invisible to both censuses, the whole program authenticates.
        """
        module = _module()
        candidate = _analyzed()
        self._with_post_write(module, candidate)
        symbols = module._admitted_symbols(module._LOCKS[KEY])
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))

        pre_fix = _scratch(module)
        pre_fix._MUTATION_KINDS = ("assign", "unary")
        self.assertTrue(
            pre_fix._no_write_holds(candidate, symbols),
            "the pre-fix barrier must be shown to MISS the postfix write")
        with mock.patch.object(pre_fix, "_LOCKS", locks):
            admitted = pre_fix.authenticate_const_global_tables(
                candidate, locks[KEY]["raw_sha256"], PROFILE)
        self.assertEqual(3, len(admitted),
                         "the miss is total: nothing else catches it")

        self.assertFalse(module._no_write_holds(candidate, symbols))
        _expect(self, module, candidate, locks,
                "const global table write present")

    def test_a_prefix_increment_is_caught(self):
        module = _module()
        candidate = _analyzed()
        node, parent = _index_node(candidate, "SOBEL_Y_KERNEL")
        unary = dataclasses.replace(node, kind="unary", operator="--",
                                    children=(node,))
        _replace_child(parent, node, unary)
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "const global table write present")

    def test_a_plain_assignment_to_a_table_element_is_caught(self):
        module = _module()
        candidate = _analyzed()
        node, parent = _index_node(candidate, "SOBEL_OFFSETS")
        assignment = dataclasses.replace(
            node, kind="assign", operator="=",
            children=(node, dataclasses.replace(node.children[1])))
        _replace_child(parent, node, assignment)
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "const global table write present")

    def test_a_compound_assignment_to_a_table_element_is_caught(self):
        """Compound assignment needs no increment-operator entry: it is kind
        `assign` with a non-`=` operator."""
        module = _module()
        candidate = _analyzed()
        node, parent = _index_node(candidate, "SOBEL_X_KERNEL")
        assignment = dataclasses.replace(
            node, kind="assign", operator="*=",
            children=(node, dataclasses.replace(node.children[1])))
        _replace_child(parent, node, assignment)
        locks = _relocked(module, candidate)
        locks[KEY].update({**_recount(module, candidate),
                           "total_assigns": module._node_census(candidate)[1]})
        _expect(self, module, candidate, locks,
                "const global table write present")

    def test_a_write_planted_in_a_global_initializer_is_caught(self):
        """The barrier walks `program.declarations` too -- the validator's own
        write audit does not."""
        module = _module()
        candidate = _analyzed()
        node, _ = _index_node(candidate, "SOBEL_Y_KERNEL")
        planted = dataclasses.replace(
            node, kind="post", operator="++",
            children=(dataclasses.replace(node),))
        target = _declaration(candidate, "CHANNEL_CAP")
        object.__setattr__(target.initializer, "children", (planted,))
        symbols = module._admitted_symbols(module._LOCKS[KEY])
        self.assertFalse(module._no_write_holds(candidate, symbols))


class ConstGlobalTableLockDeletionTests(unittest.TestCase):
    """Every lock is proved load-bearing by DELETING THE LOCK.

    For each row: mutate the tree (or the frozen record the lock owns),
    refreeze only the coarse hashes and the two program-wide counters, show the
    real module rejects with that lock's own message, then re-exec the module
    with exactly that predicate neutralized and show the message is gone.

    Most rows delete a WHOLE predicate. The four `..._isolates_...` /
    `..._is_the_sole_guard_...` rows delete one **sub-clause** of a predicate
    by relocking every frozen field the other clauses own, so the clause under
    test is the only thing left that can fire. Those exist because a
    whole-predicate table cannot see a vacuous clause inside a live predicate.
    """

    def _delete_and_compare(self, mutate, predicate, expected, recount=False,
                            relock=None):
        module = _module()
        candidate = _analyzed()
        mutate(candidate)
        locks = _relocked(module, candidate)
        if recount:
            locks[KEY].update(_recount(module, candidate))
        if relock is not None:
            relock(locks, candidate)
        _expect(self, module, candidate, locks, expected)

        scratch = _scratch(module, predicate)
        with mock.patch.object(scratch, "_LOCKS", locks):
            try:
                scratch.authenticate_const_global_tables(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
                survived = None
            except ValueError as error:
                survived = str(error)
        if survived is not None:
            self.assertNotIn(
                expected, survived,
                f"deleting {predicate} did not remove its message")
        return survived

    def test_function_cardinality_lock(self):
        def mutate(candidate):
            object.__setattr__(candidate, "functions",
                               candidate.functions[:-1])
        survived = self._delete_and_compare(
            mutate, "_function_cardinality_holds",
            "function cardinality mismatch", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("typed function inventory mismatch", survived)

    def test_function_inventory_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "clamp01")
            object.__setattr__(host, "span",
                               dataclasses.replace(host.span, end_column=99))
        survived = self._delete_and_compare(
            mutate, "_function_inventory_holds",
            "typed function inventory mismatch")
        self.assertIsNone(survived)

    def test_resource_lock(self):
        def mutate(candidate):
            object.__setattr__(
                candidate, "resources",
                dataclasses.replace(candidate.resources,
                                    uses_derivatives=True))
        survived = self._delete_and_compare(
            mutate, "_resources_hold", "resource profile mismatch")
        self.assertIsNone(survived)

    def test_call_graph_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "clamp01").body[0].expressions[0]
            call = next(node for node, _ in _walk(_main(candidate).body[8])
                        if node.kind == "call")
            object.__setattr__(host, "children",
                               (*host.children, dataclasses.replace(call)))
        survived = self._delete_and_compare(
            mutate, "_call_graph_holds",
            "call graph or reachability profile mismatch", recount=True)
        self.assertIsNone(survived)

    def test_companion_carrier_lock(self):
        """The companion check consults the LIVE `as_u32_round_profile`, so a
        reverted Task 1 turns this red here rather than two layers up."""
        module = _module()
        candidate = _analyzed()
        locks = _relocked(module, candidate)
        carrier = module.as_u32_round_profile
        with mock.patch.object(carrier, "AS_U32_ROUND_KEYS", frozenset()):
            _expect(self, module, candidate, locks,
                    "as_u32 round companion carrier mismatch")
            scratch = _scratch(module, "_companion_carrier_holds")
            with mock.patch.object(scratch, "_LOCKS", locks):
                admitted = scratch.authenticate_const_global_tables(
                    candidate, locks[KEY]["raw_sha256"], PROFILE)
            self.assertEqual(3, len(admitted))
        # A renamed carrier profile is caught too.
        with mock.patch.object(carrier, "PROFILE", "as-u32-round-v2"):
            _expect(self, module, candidate, locks,
                    "as_u32 round companion carrier mismatch")

    def test_ordinal_and_order_lock(self):
        def mutate(candidate):
            declarations = list(candidate.declarations)
            declarations[X_KERNEL_ORDINAL], declarations[Y_KERNEL_ORDINAL] = (
                declarations[Y_KERNEL_ORDINAL],
                declarations[X_KERNEL_ORDINAL])
            object.__setattr__(candidate, "declarations",
                               tuple(declarations))
        survived = self._delete_and_compare(
            mutate, "_table_ordinal_order_holds",
            "const global table declaration order or ordinal mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("binding table mismatch", survived)

    def test_a_fourth_array_global_fails_the_order_lock(self):
        """The order lock also owns "these three are the ONLY arrays"."""
        def mutate(candidate):
            template = candidate.declarations[X_KERNEL_ORDINAL]
            symbol = dataclasses.replace(template.symbol, id=9001,
                                         name="PLANTED")
            object.__setattr__(
                candidate, "declarations",
                (*candidate.declarations,
                 dataclasses.replace(template, symbol=symbol)))
        survived = self._delete_and_compare(
            mutate, "_table_ordinal_order_holds",
            "const global table declaration order or ordinal mismatch",
            recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("binding table mismatch", survived)

    def test_const_storage_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[OFFSETS_ORDINAL]
            object.__setattr__(declaration.symbol, "storage", "global")
        survived = self._delete_and_compare(
            mutate, "_const_storage_holds",
            "const global table storage mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("const global table declaration identity mismatch",
                      survived)

    def test_writability_is_part_of_the_const_storage_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[Y_KERNEL_ORDINAL]
            object.__setattr__(declaration.symbol, "writable", True)
        survived = self._delete_and_compare(
            mutate, "_const_storage_holds",
            "const global table storage mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("const global table declaration identity mismatch",
                      survived)

    def test_element_type_allowlist_lock(self):
        """Design amendment S15's hazard, end to end: a `vec2[9]` table whose
        frozen record has been updated to match still has to be refused."""
        def mutate(candidate):
            declaration = candidate.declarations[OFFSETS_ORDINAL]
            object.__setattr__(declaration, "type",
                               array(vector("float", 2), 9))

        def relock(locks, candidate):
            record = locks[KEY]["admitted"][0]
            locks[KEY]["admitted"] = (
                record._replace(element_type="vec2", glsl_type="vec2[9]"),
                *locks[KEY]["admitted"][1:])
        survived = self._delete_and_compare(
            mutate, "_element_type_allowlisted_holds",
            "const global table element type is not pool-safe", relock=relock)
        self.assertIsNotNone(survived)
        self.assertIn("const global table native contract mismatch", survived,
                      "only the allowlist knows vec2 is a pooling hazard; the "
                      "native contract lock fires on the stale alias, not on "
                      "the aliasing risk")

    def test_native_contract_lock(self):
        def relock(locks, candidate):
            record = locks[KEY]["admitted"][1]
            locks[KEY]["admitted"] = (
                locks[KEY]["admitted"][0],
                record._replace(table=record.table._replace(native_sizeof=64)),
                locks[KEY]["admitted"][2])
        survived = self._delete_and_compare(
            lambda candidate: None, "_table_contract_holds",
            "const global table native contract mismatch", relock=relock)
        self.assertIsNone(survived)

    def test_native_element_type_is_part_of_the_native_contract_lock(self):
        def relock(locks, candidate):
            record = locks[KEY]["admitted"][1]
            locks[KEY]["admitted"] = (
                locks[KEY]["admitted"][0],
                record._replace(
                    table=record.table._replace(native_element_type="float")),
                locks[KEY]["admitted"][2])
        survived = self._delete_and_compare(
            lambda candidate: None, "_table_contract_holds",
            "const global table native contract mismatch", relock=relock)
        self.assertIsNone(
            survived,
            "typing the kernels `float` because GLSL says `float` is the "
            "divergence this lock exists to refuse")

    def test_initializer_construct_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[X_KERNEL_ORDINAL]
            object.__setattr__(declaration.initializer, "children",
                               declaration.initializer.children[:8])
        survived = self._delete_and_compare(
            mutate, "_initializer_construct_holds",
            "const global table initializer is not a nine-element array "
            "construct", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("const global table declaration identity mismatch",
                      survived)

    def test_literal_only_lock(self):
        def mutate(candidate):
            initializer = candidate.declarations[X_KERNEL_ORDINAL].initializer
            original = initializer.children[0]
            channel = _declaration(candidate, "CHANNEL_COUNT")
            object.__setattr__(
                initializer, "children",
                (dataclasses.replace(original, kind="id", literal=None,
                                     literal_value=None,
                                     symbol_id=channel.symbol.id,
                                     symbol=channel.symbol),
                 *initializer.children[1:]))
        survived = self._delete_and_compare(
            mutate, "_literal_only_initializer_holds",
            "const global table initializer is not literal-only", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("const global table declaration identity mismatch",
                      survived)

    def test_declaration_identity_lock(self):
        def mutate(candidate):
            declaration = candidate.declarations[Y_KERNEL_ORDINAL]
            object.__setattr__(declaration.symbol, "name", "SOBEL_Z_KERNEL")
        survived = self._delete_and_compare(
            mutate, "_declaration_identity_holds",
            "const global table declaration identity mismatch")
        self.assertIsNotNone(survived)
        self.assertIn("binding table mismatch", survived)

    def test_a_duplicated_symbol_id_fails_the_identity_lookup(self):
        module = _module()
        candidate = _analyzed()
        template = candidate.declarations[X_KERNEL_ORDINAL]
        object.__setattr__(
            candidate, "declarations",
            (*candidate.declarations, dataclasses.replace(template)))
        locks = _relocked(module, candidate)
        locks[KEY].update(_recount(module, candidate))
        _expect(self, module, candidate, locks,
                "const global table declaration identity mismatch")

    def test_binding_table_lock(self):
        def mutate(candidate):
            template = candidate.declarations[0]
            symbol = dataclasses.replace(template.symbol, id=9001,
                                         name="planted")
            object.__setattr__(
                candidate, "declarations",
                (*candidate.declarations,
                 dataclasses.replace(template, symbol=symbol)))
        survived = self._delete_and_compare(
            mutate, "_binding_table_holds", "binding table mismatch",
            recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("global declaration initializer census mismatch",
                      survived)

    def test_initializer_census_lock(self):
        def mutate(candidate):
            initializer = _declaration(candidate, "CHANNEL_COUNT").initializer
            object.__setattr__(initializer, "literal", "5u")
        survived = self._delete_and_compare(
            mutate, "_initializer_census_holds",
            "global declaration initializer census mismatch")
        self.assertIsNone(survived)

    def test_node_census_lock(self):
        def mutate(candidate):
            host = _fn(candidate, "clamp01").body[0].expressions[0]
            object.__setattr__(
                host, "children",
                (*host.children, dataclasses.replace(host.children[0])))
        survived = self._delete_and_compare(
            mutate, "_node_census_holds", "whole-program node census mismatch")
        self.assertIsNone(survived)

    def test_main_body_shape_lock(self):
        def mutate(candidate):
            statement = _main(candidate).body[0]
            object.__setattr__(statement, "span",
                               dataclasses.replace(statement.span,
                                                   end_column=54))
        survived = self._delete_and_compare(
            mutate, "_main_body_holds", "main body shape mismatch")
        self.assertIsNone(survived)

    def test_no_write_lock(self):
        """A postfix write on an existing read keeps both censuses intact, so
        only the mutation barrier can see it."""
        def mutate(candidate):
            node, parent = _index_node(candidate, "SOBEL_X_KERNEL")
            _replace_child(parent, node,
                           dataclasses.replace(node, kind="post",
                                               operator="++",
                                               children=(node,)))
        survived = self._delete_and_compare(
            mutate, "_no_write_holds", "const global table write present",
            recount=True)
        self.assertIsNone(
            survived,
            "the write is invisible to both censuses, which is exactly why "
            "the barrier has to exist")

    def test_index_read_census_lock(self):
        def mutate(candidate):
            node, parent = _index_node(candidate, "SOBEL_Y_KERNEL")
            object.__setattr__(parent, "children",
                               (*parent.children, dataclasses.replace(node)))
        survived = self._delete_and_compare(
            mutate, "_index_site_census_holds",
            "const global table index read census mismatch: 4", recount=True)
        self.assertIsNotNone(survived)
        self.assertIn("const global table bare reference census mismatch: 4",
                      survived)

    def test_loop_binding_lock_sees_a_trip_count_that_overruns_the_table(self):
        """Design amendment S13. `std::array::operator[]` is unchecked and the
        JavaScript returns `undefined` -> NaN, so a trip count of 12 reads out
        of bounds natively while satisfying every other predicate."""
        def mutate(candidate):
            loop = _main(candidate).body[LOOP_STATEMENT_INDEX]
            object.__setattr__(
                loop, "loop_proof",
                dataclasses.replace(loop.loop_proof, trip_count=12,
                                    bound_value=12))
        survived = self._delete_and_compare(
            mutate, "_loop_binding_holds",
            "const global table read is not bound to the nine-trip counted "
            "loop")
        self.assertIsNone(
            survived,
            "nothing else in the closure bounds the loop -- which is the "
            "vacuity S13 found in the original nine predicates")

    def test_loop_binding_lock_sees_loop_proof_drift(self):
        """Named for what it actually isolates: the frozen `loop_proof` tuple.

        The induction-symbol *binding* is a different clause and is isolated
        separately below -- with `loop_proof` mutated the tuple comparison
        fires first, so this row cannot speak for it.
        """
        def mutate(candidate):
            loop = _main(candidate).body[LOOP_STATEMENT_INDEX]
            object.__setattr__(
                loop, "loop_proof",
                dataclasses.replace(loop.loop_proof,
                                    induction_symbol_id=4242))
        survived = self._delete_and_compare(
            mutate, "_loop_binding_holds",
            "const global table read is not bound to the nine-trip counted "
            "loop")
        self.assertIsNone(survived)

    def test_loop_binding_lock_isolates_the_induction_symbol_binding(self):
        """SUB-CLAUSE: `site.index.symbol_id != proof.induction_symbol_id`.

        `loop_proof` keeps induction symbol 47 so its frozen tuple still
        matches, and `index_sites[0]` is relocked to the read's new index
        symbol so the census still matches. Only the binding between the two
        can fire -- a read indexed by some other counter inside a proved
        nine-trip loop.
        """
        def mutate(candidate):
            node, _ = _index_node(candidate, "SOBEL_OFFSETS")
            object.__setattr__(node.children[1], "symbol_id", 4242)

        def relock(locks, candidate):
            module = _module()
            sites, _ = module._reference_census(
                candidate, module._admitted_symbols(locks[KEY]))
            locks[KEY]["index_sites"] = (
                locks[KEY]["index_sites"][0]._replace(
                    index_symbol_id=4242,
                    node_sha256=sites[0].record.node_sha256),
                *locks[KEY]["index_sites"][1:])
        survived = self._delete_and_compare(
            mutate, "_loop_binding_holds",
            "const global table read is not bound to the nine-trip counted "
            "loop", relock=relock)
        self.assertIsNone(
            survived,
            "with the census relocked, only the induction binding is left")

    def test_loop_binding_lock_isolates_the_enclosing_loop_identity(self):
        """SUB-CLAUSE: `site.chain[0] is not loop`.

        Relocate the `SOBEL_Y_KERNEL` read out of `main.body[13]` into
        `main.body[14]`, keeping the index node object -- and therefore its
        span, hash, type and index symbol -- byte-identical, and relocking the
        census record's `statement_index` and `chain` to the new position. The
        read is then a perfectly well-formed nine-element table read that is
        NOT inside the proved loop, and only the identity clause says so.
        """
        def mutate(candidate):
            node, parent = _index_node(candidate, "SOBEL_Y_KERNEL")
            _replace_child(parent, node,
                           dataclasses.replace(node.children[1]))
            host = _main(candidate).body[14].expressions[0]
            object.__setattr__(host, "children", (*host.children, node))

        def relock(locks, candidate):
            locks[KEY]["index_sites"] = (
                *locks[KEY]["index_sites"][:2],
                locks[KEY]["index_sites"][2]._replace(
                    statement_index=14,
                    chain=(("decl", "148:5-148:53"),)))
        survived = self._delete_and_compare(
            mutate, "_loop_binding_holds",
            "const global table read is not bound to the nine-trip counted "
            "loop", recount=True, relock=relock)
        self.assertIsNone(
            survived,
            "the relocated read satisfies every census; only the identity "
            "of the enclosing loop object refuses it")

    def test_index_site_record_content_is_the_sole_guard_on_a_respan(self):
        """SUB-CLAUSE: `tuple(item.record ...) != lock["index_sites"]`.

        The cardinality and category clauses both still hold -- three sites,
        all `"readonly lvalue"` -- so the only thing that can notice a read
        node whose span (and therefore node hash) has moved is the frozen
        record comparison. Without this row the entire 3x15-field
        `_INDEX_SITES` table is proved by nothing.
        """
        def mutate(candidate):
            node, _ = _index_node(candidate, "SOBEL_X_KERNEL")
            object.__setattr__(node, "span",
                               dataclasses.replace(node.span, end_column=41))
        survived = self._delete_and_compare(
            mutate, "_index_site_census_holds",
            "const global table index read census mismatch: 3")
        self.assertIsNone(
            survived,
            "cardinality is still three and the category is unchanged, so "
            "nothing but the record comparison sees a respanned read")

    def test_index_site_lock_isolates_the_readonly_lvalue_category(self):
        """SUB-CLAUSE: `all(item.record.category == "readonly lvalue")`.

        Design amendment S16's clause. Relock the frozen record's own
        `category` field to the mutated value so the record comparison
        passes, leaving the explicit literal as the only refusal -- an
        indexed table read whose base symbol has become writable.
        """
        def mutate(candidate):
            node, _ = _index_node(candidate, "SOBEL_OFFSETS")
            object.__setattr__(node, "category", "lvalue")

        def relock(locks, candidate):
            module = _module()
            sites, _ = module._reference_census(
                candidate, module._admitted_symbols(locks[KEY]))
            locks[KEY]["index_sites"] = (
                locks[KEY]["index_sites"][0]._replace(
                    category="lvalue",
                    node_sha256=sites[0].record.node_sha256),
                *locks[KEY]["index_sites"][1:])
        survived = self._delete_and_compare(
            mutate, "_index_site_census_holds",
            "const global table index read census mismatch: 3", relock=relock)
        self.assertIsNone(survived)

    def test_bare_reference_record_content_is_the_sole_guard_on_a_respan(self):
        """SUB-CLAUSE: `tuple(item.record ...) != lock["bare_references"]`.

        Respan the `SOBEL_X_KERNEL` base `id` and relock only the enclosing
        index node's hash. The count is still three and every base is still an
        index base, so nothing but the frozen 3x9 reference table can notice.
        """
        def mutate(candidate):
            node, _ = _index_node(candidate, "SOBEL_X_KERNEL")
            base = node.children[0]
            object.__setattr__(base, "span",
                               dataclasses.replace(base.span, end_column=38))

        def relock(locks, candidate):
            module = _module()
            sites, _ = module._reference_census(
                candidate, module._admitted_symbols(locks[KEY]))
            locks[KEY]["index_sites"] = (
                locks[KEY]["index_sites"][0],
                locks[KEY]["index_sites"][1]._replace(
                    node_sha256=sites[1].record.node_sha256),
                locks[KEY]["index_sites"][2])
        survived = self._delete_and_compare(
            mutate, "_bare_reference_census_holds",
            "const global table bare reference census mismatch: 3",
            relock=relock)
        self.assertIsNone(
            survived,
            "without this row the 3x9 _BARE_REFERENCES table is proved by "
            "nothing")

    def test_bare_reference_lock_isolates_the_index_base_linkage(self):
        """SUB-CLAUSE: `sorted(id(node)) == sorted(bases)` -- design S4.3.7.

        Detach `SOBEL_OFFSETS`'s index base from the `id` grammar (a `member`
        node still carrying symbol id 9) and plant a real bare `id` elsewhere.
        The reference COUNT stays three and the records are relocked, so the
        cardinality and record clauses both hold -- but one reference is no
        longer the base of any index site, which is precisely the escape
        S4.3.7 exists to refuse.
        """
        def mutate(candidate):
            node, _ = _index_node(candidate, "SOBEL_OFFSETS")
            base = node.children[0]
            object.__setattr__(
                node, "children",
                (dataclasses.replace(base, kind="member", member="x"),
                 node.children[1]))
            host = _main(candidate).body[14].expressions[0]
            object.__setattr__(host, "children",
                               (*host.children, dataclasses.replace(base)))

        def relock(locks, candidate):
            module = _module()
            sites, references = module._reference_census(
                candidate, module._admitted_symbols(locks[KEY]))
            locks[KEY]["bare_references"] = tuple(item.record
                                                  for item in references)
            locks[KEY]["index_sites"] = tuple(
                record._replace(node_sha256=site.record.node_sha256)
                for record, site in zip(locks[KEY]["index_sites"], sites))
        survived = self._delete_and_compare(
            mutate, "_bare_reference_census_holds",
            "const global table bare reference census mismatch: 3",
            recount=True, relock=relock)
        self.assertIsNone(
            survived,
            "three references, three records, three index sites -- only the "
            "base-linkage clause refuses the escape")

    def test_bare_reference_census_lock(self):
        """A fourth bare `id` that is NOT under an index means the array
        escapes as a whole value. The index census cannot see it."""
        def mutate(candidate):
            node, _ = _index_node(candidate, "SOBEL_OFFSETS")
            host = _fn(candidate, "clamp01").body[0].expressions[0]
            object.__setattr__(
                host, "children",
                (*host.children, dataclasses.replace(node.children[0])))
        survived = self._delete_and_compare(
            mutate, "_bare_reference_census_holds",
            "const global table bare reference census mismatch: 4",
            recount=True)
        self.assertIsNone(survived)


class ConstGlobalTableLedgerTests(unittest.TestCase):
    def test_ledger_helper_rejects_duplicate_and_short_visitation(self):
        module = _module()
        marker = (object(), object())
        self.assertIsNone(module._check_ledger(list(marker), 2, "probe"))
        for broken in ([marker[0], marker[0]], [marker[0]],
                       [*marker, marker[1]]):
            with self.subTest(broken=len(broken)), \
                    self.assertRaisesRegex(ValueError,
                                           "probe visitation ledger mismatch"):
                module._check_ledger(broken, 2, "probe")

    def test_sabotaged_ledger_size_turns_a_valid_program_red(self):
        module = _module()
        self.assertEqual(20, module._CONSUMED_LEDGER)
        self.assertEqual(3, len(module.authenticate_const_global_tables(
            _analyzed(), RAW_SHA256, PROFILE)))
        for sabotage in (19, 21):
            with self.subTest(sabotage=sabotage), \
                    mock.patch.object(module, "_CONSUMED_LEDGER", sabotage), \
                    self.assertRaisesRegex(
                        ValueError,
                        "const-global-nine-table visitation ledger mismatch"):
                module.authenticate_const_global_tables(
                    _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(3, len(module.authenticate_const_global_tables(
            _analyzed(), RAW_SHA256, PROFILE)))


class ConstGlobalTableVocabularyTests(unittest.TestCase):
    def test_no_capability_or_type_vocabulary_growth(self):
        _module()
        frozen = {
            "capabilities": (
                44, generate_typed_slice.APPROVED_CAPABILITIES,
                "6ddb906dc859e45ee613b580dc6988c663d2aff22db9c365ece3097d126a4aea"),
            "types": (
                17, generate_typed_slice.APPROVED_TYPES,
                "aa4ab00ac3b34ece6681eaa55435817b7908c9b8ea421a6eca1931f6ab4791c7"),
            "binary": (
                17, generate_typed_slice.APPROVED_BINARY_OPERATORS,
                "cceb35790b79fa895906c57d7e81f0056fac404cf7448eec9b8d9dbb49b705b0"),
            "assignment": (
                6, generate_typed_slice.APPROVED_ASSIGNMENT_OPERATORS,
                "99a6ede7544a02082e0b72d83690c3b68d8c846e221078e3e90ac10463d498e2"),
        }
        for name, (size, value, digest) in frozen.items():
            with self.subTest(vocabulary=name):
                self.assertEqual(size, len(value))
                self.assertEqual(
                    digest,
                    hashlib.sha256(repr(value).encode()).hexdigest())
        # `float` and `ivec2` are already approved element types: it is the
        # ARRAY WRAPPER AT FILE SCOPE, not the element type, being admitted.
        self.assertIn("float", generate_typed_slice.APPROVED_TYPES)
        self.assertIn("ivec2", generate_typed_slice.APPROVED_TYPES)
        for token in ("ivec2[9]", "float[9]", PROFILE, "const-global",
                      "const-global-table", "nine-table"):
            with self.subTest(token=token):
                self.assertNotIn(
                    token, generate_typed_slice.APPROVED_CAPABILITIES)
                self.assertNotIn(token, generate_typed_slice.APPROVED_TYPES)

    def test_the_module_never_grows_the_vocabulary_by_import(self):
        before = (generate_typed_slice.APPROVED_CAPABILITIES,
                  generate_typed_slice.APPROVED_TYPES)
        module = _module()
        module.authenticate_const_global_tables(
            _analyzed(), RAW_SHA256, PROFILE)
        self.assertEqual(before[0], generate_typed_slice.APPROVED_CAPABILITIES)
        self.assertEqual(before[1], generate_typed_slice.APPROVED_TYPES)
        self.assertEqual(44, len(generate_typed_slice.APPROVED_CAPABILITIES))
        self.assertEqual(17, len(generate_typed_slice.APPROVED_TYPES))


def _literal_parts(node) -> list[str]:
    """Every constant string fragment of one expression.

    Adjacent string literals are already merged into a single `Constant` by
    the parser, so 79-column wrapping needs no special handling. **Every**
    fragment of an f-string is returned, not just the longest -- dropping the
    short ones would let half a guard go unasserted.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.JoinedStr):
        return [item.value for item in node.values
                if isinstance(item, ast.Constant)
                and isinstance(item.value, str)]
    return []


def _guard_messages(module) -> list[str]:
    """Every literal string fragment this module hands to `_fail`.

    Extracted from the module's own AST rather than a hand-list, so a new guard
    cannot be added without a test asserting it.
    """
    tree = ast.parse(
        pathlib.Path(module.__file__).read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_fail" and node.args):
            continue
        for part in _literal_parts(node.args[0]):
            if len(part.strip()) >= 10:
                found.append(part)
    return sorted(set(found))


def _call_argument_strings(path: pathlib.Path) -> list[str]:
    """Every string constant this file passes as an argument to a call.

    Deliberately NOT a raw text search: a guard string that appeared only in a
    docstring, a comment or a variable name would satisfy a text search while
    asserting nothing. Only strings that actually reach a call -- an
    `assertIn`, an `assertEqual`, an `assertRaisesRegex` -- count.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for argument in (*node.args, *(item.value for item in node.keywords)):
            for item in ast.walk(argument):
                found.extend(_literal_parts(item))
    return found


class ConstGlobalTableGuardMessageTests(unittest.TestCase):
    """Design S4.4, as amended by S16.

    The Shapes183 review found that Scanline Error, Caustic, Linear sRGB and
    Glyph Map have zero test references to their carrier-guard strings. Its
    universal claim was false -- `tests/test_edge_bvec3_contour.py:47,53` and
    `tests/test_gabor_effective_depth.py:93` do assert theirs -- but the
    prescription stands, and this module does not inherit the gap.
    """

    def test_every_guard_message_is_asserted_somewhere_in_this_file(self):
        module = _module()
        messages = _guard_messages(module)
        self.assertGreaterEqual(len(messages), 20,
                                "guard extraction looks broken")
        asserted = _call_argument_strings(pathlib.Path(__file__))
        self.assertGreaterEqual(len(asserted), 100,
                                "call-argument extraction looks broken")
        for message in messages:
            probe = message.strip()
            with self.subTest(message=probe):
                self.assertTrue(
                    any(probe in item for item in asserted),
                    f"guard string {probe!r} is not an argument to any call "
                    "in this file")

    def test_the_coverage_check_rejects_a_docstring_only_mention(self):
        """The loophole this replaced: a raw text search over the file would
        accept a guard string that lives only in this docstring, which
        asserts nothing at all."""
        probe = "a guard string that lives only in this docstring"
        here = pathlib.Path(__file__)
        self.assertIn(probe, here.read_text(encoding="utf-8"),
                      "the decoy has to really be in the file")
        self.assertFalse(
            any(probe in item for item in _call_argument_strings(here)),
            "prose must not be able to satisfy the coverage check")

    def test_the_non_carrier_guard_names_all_three_declarations(self):
        module = _module()
        foreign = _foreign()
        with self.assertRaises(ValueError) as raised:
            module.authenticate_const_global_tables(
                foreign, _hash(FOREIGN_SOURCE), PROFILE)
        self.assertEqual(
            f"{PROFILE}: program key is not an admitted const-global "
            f"nine-table carrier; {KEY} 15:1 SOBEL_OFFSETS, 21:1 "
            "SOBEL_X_KERNEL and 27:1 SOBEL_Y_KERNEL are the sole admitted "
            "declarations",
            str(raised.exception))

    def test_the_accessor_guards_name_the_rejected_key(self):
        module = _module()
        for accessor in (module.table_contract, module.allowed_row_fields):
            with self.subTest(accessor=accessor.__name__), \
                    self.assertRaises(ValueError) as raised:
                accessor("synth/shape:shape")
            self.assertEqual(
                f"{PROFILE}: synth/shape:shape is not an admitted "
                "const-global nine-table carrier", str(raised.exception))

    def test_every_guard_message_is_prefixed_with_the_profile_name(self):
        module = _module()
        program = _analyzed()
        with self.assertRaises(ValueError) as raised:
            module.authenticate_const_global_tables(program, "0" * 64, PROFILE)
        self.assertTrue(str(raised.exception).startswith(f"{PROFILE}: "))
        with self.assertRaises(ValueError) as raised:
            module.table_contract("synth/shape:shape")
        self.assertTrue(str(raised.exception).startswith(f"{PROFILE}: "))


if __name__ == "__main__":
    unittest.main()
