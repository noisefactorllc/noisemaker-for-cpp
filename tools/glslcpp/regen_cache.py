"""Content-addressed memo for ``generate_typed_slice.generate_outputs``.

Why this exists
---------------

Every historical-reconstruction test rebuilds a past milestone by deep-copying
the LIVE spec, removing rows and regenerating **all** programs in memory. One
regeneration costs ~29 s at 191 rows, and the count of such tests grows with
every landing, so the suite's cost is roughly quadratic in landings. Measured
2026-08-20 across the six milestone modules: 500.7 s wall, **98 % of it inside
`generate_outputs`**, 18 calls for only **10 distinct specs** — eight of those
regenerations recomputed bytes another test in the same run had already
produced, and every separate module process recomputed all of them again.

What makes memoizing safe here
------------------------------

`generate_outputs` is a pure function of (spec, pinned corpus, generator
source) **only while its collaborators are the real ones**. Verified by
measurement, not assumption: the same input twice yields byte-identical
outputs, and a one-row projection yields different ones. The key covers all
three inputs, so any change to any of them is a miss rather than a stale hit.

The purity claim has one hole, and it is not hypothetical -- it was caught by
the suite the first time this ran. Several tests forge a program by patching
`analyze_program`, `validate_capabilities`, `validate_corpus` or
`semantic_report` and then require `generate_outputs` to RAISE. The spec is
untouched, so a spec-keyed memo hands back the good bytes and the guard never
fires. `_collaborators_are_patched()` therefore bypasses the cache entirely --
read and write -- whenever any of them is a mock. `load_slice` is the
exception: patching it is how a historical projection is expressed, and its
result is already inside the key.

Deliberate properties, each guarding a way this could go wrong:

* **Off by default.** Without ``NOISEMAKER_REGEN_CACHE`` pointing at a
  directory, this module is inert and the generator behaves exactly as before.
  Publication and CI runs get the real thing unless they opt in.
* **Never inside the repository.** The cache root is rejected if it resolves
  inside the checkout — caches, like builds, do not belong in the tree.
* **The generator's own source is part of the key.** An emitter change
  invalidates every entry, so the cache cannot serve bytes from before a fix.
  This is the property that matters most: the 2026-08-19 alias fix moved 42
  frozen pins, and a cache keyed only on the spec would have hidden it.
* **Patched collaborators disable it.** A forged-program test must reach the
  real generator and its real guards; see `_collaborators_are_patched`.
* **`verify_all()` re-derives every entry** and reports mismatches, so the
  cache is auditable rather than trusted. Run it before believing a green
  suite that ran cached.

Usage::

    export NOISEMAKER_REGEN_CACHE="$RUN_ROOT/regen-cache"
    python3 -m unittest tests.test_typed_generator      # transparently cached
    python3 -m tools.glslcpp.regen_cache --verify        # re-derive and compare
    python3 -m tools.glslcpp.regen_cache --stats
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import pathlib
import pkgutil
import sys
from typing import Any, Callable

_ENV_VAR = "NOISEMAKER_REGEN_CACHE"
_TOOLS = pathlib.Path(__file__).resolve().parent
_REPOSITORY = _TOOLS.parents[1]
_SOURCE_FINGERPRINT: str | None = None


class RegenCacheError(RuntimeError):
    """The cache is configured in a way that could produce wrong bytes."""


def cache_root() -> pathlib.Path | None:
    """The configured cache directory, or ``None`` when caching is off."""
    raw = os.environ.get(_ENV_VAR)
    if not raw:
        return None
    root = pathlib.Path(raw).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    resolved = root.resolve()
    if resolved == _REPOSITORY or _REPOSITORY in resolved.parents:
        raise RegenCacheError(
            f"{_ENV_VAR} must not live inside the repository: {resolved}")
    return resolved


def _fresh_source_fingerprint() -> str:
    """Read and digest every generator source file right now."""
    parts = []
    for path in sorted(_TOOLS.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        parts.append(path.relative_to(_TOOLS).as_posix().encode())
        parts.append(hashlib.sha256(path.read_bytes()).digest())
    return hashlib.sha256(b"".join(parts)).hexdigest()


def source_fingerprint() -> str:
    """The generator-source digest loaded by this process.

    Any edit to the validator, the emitter or a frontend profile changes this,
    so cached bytes produced by older code can never be served.  The installed
    wrapper also compares this process baseline with a fresh on-disk digest on
    every cache use.  That second check matters when another process edits the
    shared checkout after this process imported the generator: its in-memory
    callables still implement the old source and must never populate a key for
    the new source bytes.
    """
    global _SOURCE_FINGERPRINT
    if _SOURCE_FINGERPRINT is None:
        _SOURCE_FINGERPRINT = _fresh_source_fingerprint()
    return _SOURCE_FINGERPRINT


def spec_fingerprint(slice_spec: dict[str, Any]) -> str:
    """A digest over the spec exactly as the generator will consume it."""
    return hashlib.sha256(
        json.dumps(slice_spec, sort_keys=True, separators=(",", ":"))
        .encode("utf-8")).hexdigest()


def entry_key(slice_spec: dict[str, Any]) -> str:
    return hashlib.sha256(
        f"{source_fingerprint()}:{spec_fingerprint(slice_spec)}"
        .encode("utf-8")).hexdigest()


def _entry_dir(root: pathlib.Path, key: str) -> pathlib.Path:
    return root / key[:2] / key


def load(root: pathlib.Path, key: str) -> dict[str, bytes] | None:
    directory = _entry_dir(root, key)
    index = directory / "index.json"
    if not index.is_file():
        return None
    try:
        names = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    outputs: dict[str, bytes] = {}
    for relative, stored in names.items():
        blob = directory / stored
        if not blob.is_file():
            return None
        outputs[relative] = blob.read_bytes()
    return outputs


def store(root: pathlib.Path, key: str, outputs: dict[str, bytes],
          slice_spec: dict[str, Any] | None = None) -> None:
    """Write an entry, including the spec that produced it.

    The spec is stored so `verify_all()` can re-derive the entry rather than
    take it on faith. An entry without one is reported as unverifiable, never
    as passing.
    """
    directory = _entry_dir(root, key)
    directory.mkdir(parents=True, exist_ok=True)
    if slice_spec is not None:
        temporary_spec = directory / "spec.json.partial"
        temporary_spec.write_text(
            json.dumps(slice_spec, sort_keys=True), encoding="utf-8")
        temporary_spec.replace(directory / "spec.json")
    names = {}
    for relative, payload in outputs.items():
        stored = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:16]
        names[relative] = stored
        # Write-then-rename so a killed run cannot leave a half-written blob
        # that a later run would serve as a hit.
        temporary = directory / f"{stored}.partial"
        temporary.write_bytes(payload)
        temporary.replace(directory / stored)
    temporary_index = directory / "index.json.partial"
    temporary_index.write_text(json.dumps(names, sort_keys=True), encoding="utf-8")
    temporary_index.replace(directory / "index.json")


# `load_slice` is the ONE patch the cache tolerates: patching it is the
# sanctioned way to express a historical projection, and the projection it
# returns is already inside the key. Everything else is a forgery as far as
# this cache is concerned.
# `generate_outputs` is excluded because `install` replaces it with the
# wrapper immediately after the snapshot is taken -- leaving it in would make
# the guard fire on every call. A test that patches it bypasses the wrapper
# entirely anyway, so nothing is lost.
_PATCHABLE_WITHOUT_BYPASS = frozenset({"load_slice", "generate_outputs"})

# Every module under this package is a collaborator: the generator reaches
# most of them through direct `from ... import name` bindings that leave no
# module attribute behind, so enumerating what it "holds" misses them. The
# package prefix is the only enumeration that cannot go stale as carriers are
# added.
_COLLABORATOR_PACKAGE = "tools.glslcpp"


def _collaborator_modules() -> dict[str, object]:
    """Every already-imported module under the generator's package."""
    return {name: value for name, value in sys.modules.items()
            if (name == _COLLABORATOR_PACKAGE
                or name.startswith(_COLLABORATOR_PACKAGE + "."))
            and value is not None}


def _import_collaborators() -> None:
    """Import the whole package so the snapshot is taken over all of it.

    The generator pulls most carriers in through `from ... import name`, and
    several tests import a frontend module for the first time themselves. If
    the baseline were only what happened to be loaded at install, those
    late arrivals would never be compared -- and a module cannot be snapshot
    on first sight either, because `mock.patch` imports its target before
    patching it, so first sight is already the patched value. Importing
    everything up front is what makes the baseline complete.

    A module that will not import is skipped: it cannot be a collaborator
    of a generator run that succeeds.
    """
    package = sys.modules.get(_COLLABORATOR_PACKAGE)
    if package is None or not hasattr(package, "__path__"):
        return
    for info in pkgutil.walk_packages(package.__path__,
                                      prefix=_COLLABORATOR_PACKAGE + "."):
        if info.name.endswith(".regen_cache"):
            continue
        try:
            importlib.import_module(info.name)
        except Exception:  # noqa: BLE001 -- see docstring
            continue


def _callable_snapshot(module) -> dict[tuple[str | None, str], object]:
    """Identity of every callable the generator might call.

    Callables only: module-level data legitimately mutates (memo slots and
    the like), and comparing it would bypass the cache for no reason.

    Class attributes are walked as well as module attributes. A method is a
    perfectly ordinary patch target -- `emit_typed_cpp._Emitter` has two that
    the alias suite neutralizes -- and a module-level-only scan cannot see
    one, so the memo served pre-patch bytes and three RED tests came back
    green. Anything reachable as `<module>.<name>` or `<module>.<class>.
    <name>` is in the snapshot.
    """
    snapshot: dict[tuple[str | None, str], object] = {}

    def record(owner: str | None, target: object) -> None:
        for name, value in vars(target).items():
            if owner is None and name in _PATCHABLE_WITHOUT_BYPASS:
                continue
            if callable(value):
                snapshot[(owner, name)] = value

    record(None, module)
    for module_name, collaborator in _collaborator_modules().items():
        if collaborator is module:
            continue  # already recorded, and with its exemptions applied
        record(module_name, collaborator)
        for name, value in vars(collaborator).items():
            if isinstance(value, type):
                record(f"{module_name}.{name}", value)
    return snapshot


def _collaborators_are_patched(module) -> bool:
    """True when anything the generator calls is not what it was at import.

    Compares **identity against a snapshot** rather than sniffing for
    `unittest.mock` types. Two earlier versions were weaker and each was
    caught by the suite:

    * a hand-written list of collaborator names missed
      `apply_smooth_edge_luma_weights`, one of an `apply_*` family that grows
      with every carrier;
    * an `isinstance(..., NonCallableMock)` scan missed
      `apply_const_global_tables`, because `mock.patch.object(target, name,
      a_lambda)` installs the lambda itself and no Mock ever exists. That one
      showed up as a FLAKY test -- it passed or failed depending on whether
      an earlier test had already populated the entry.

    Identity against a snapshot catches all three shapes and anything else,
    which is why the guard is written this way rather than as a check for
    "looks mocked".
    """
    baseline = getattr(module, "_regen_cache_baseline", None)
    if baseline is None:
        return False
    seen = getattr(module, "_regen_cache_baseline_modules", frozenset())
    if not seen >= _collaborator_modules().keys():
        # A collaborator module was imported after the snapshot, so nothing
        # in it was ever compared. Refuse the cache rather than guess.
        return True
    for key, original in baseline.items():
        owner, name = key
        target = module if owner is None else _resolve(owner)
        if target is None:
            return True
        # `vars`, not `getattr`: a classmethod or other descriptor hands back
        # a freshly bound object on every attribute access, so `getattr`
        # identity is unstable and would report every run as patched. The
        # `__dict__` entry is the thing `mock.patch.object` actually
        # replaces, and it is stable.
        if vars(target).get(name) is not original:
            return True
    return False


def _resolve(dotted: str) -> object | None:
    """The module, or the class inside it, that a snapshot key names."""
    target = sys.modules.get(dotted)
    if target is not None:
        return target
    module_name, _, attribute = dotted.rpartition(".")
    owner = sys.modules.get(module_name)
    return None if owner is None else getattr(owner, attribute, None)


def install(module) -> Callable[..., dict[str, bytes]]:
    """Wrap ``module.generate_outputs`` with the memo. Idempotent.

    The key is derived from the spec the generator would actually load, so a
    test that mocks ``load_slice`` to project a historical state keys on that
    projection -- which is the whole point.
    """
    if getattr(module.generate_outputs, "_regen_cached", False):
        return module.generate_outputs
    uncached = module.generate_outputs
    loaded_source_fingerprint = _fresh_source_fingerprint()
    # Snapshot BEFORE wrapping, so `generate_outputs` itself is not in it.
    _import_collaborators()
    module._regen_cache_baseline = _callable_snapshot(module)
    module._regen_cache_baseline_modules = frozenset(_collaborator_modules())

    def cached(repository=None, *args, **kwargs):
        root = cache_root()
        if (root is not None
                and _fresh_source_fingerprint() != loaded_source_fingerprint):
            # The Python objects in this process predate an on-disk edit.
            # Bypass both cache reads and writes: using the new disk digest as
            # a key for old in-memory behavior is exactly how a stale entry can
            # poison later, freshly imported processes.
            cached.source_drift_bypassed += 1
            root = None
        if root is not None and _collaborators_are_patched(module):
            cached.bypassed += 1
            root = None
        if root is None:
            return (uncached(repository, *args, **kwargs)
                    if repository is not None else uncached(*args, **kwargs))
        target = repository if repository is not None else module._ROOT
        slice_spec = module.load_slice(target)
        key = entry_key(slice_spec)
        hit = load(root, key)
        if hit is not None:
            cached.hits += 1
            return hit
        cached.misses += 1
        outputs = (uncached(repository, *args, **kwargs)
                   if repository is not None else uncached(*args, **kwargs))
        store(root, key, outputs, slice_spec)
        return outputs

    cached._regen_cached = True
    cached._uncached = uncached
    cached.hits = 0
    cached.misses = 0
    cached.bypassed = 0
    cached.source_drift_bypassed = 0
    cached.loaded_source_fingerprint = loaded_source_fingerprint
    module.generate_outputs = cached
    return cached


def verify_all() -> int:
    """Re-derive every cached entry and compare. Returns a process exit code.

    A cache you cannot audit is a cache you should not trust; this is the
    audit. It regenerates from the stored spec and requires byte equality.
    """
    root = cache_root()
    if root is None:
        print(f"regen_cache: {_ENV_VAR} is unset; nothing to verify")
        return 0
    sys.path.insert(0, str(_REPOSITORY))
    from tools.glslcpp import generate_typed_slice as module

    uncached = getattr(module.generate_outputs, "_uncached",
                       module.generate_outputs)
    entries = sorted(root.glob("*/*/index.json"))
    if not entries:
        print("regen_cache: cache is empty")
        return 0
    checked = mismatched = orphaned = 0
    for index in entries:
        directory = index.parent
        spec_path = directory / "spec.json"
        if not spec_path.is_file():
            orphaned += 1
            continue
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        stored = load(root, directory.name)
        if stored is None:
            orphaned += 1
            continue
        from unittest import mock
        checked += 1
        try:
            with mock.patch.object(module, "load_slice", return_value=spec):
                fresh = uncached(_REPOSITORY)
        except Exception as error:  # noqa: BLE001 -- an audit reports, never crashes
            # An entry whose spec no longer generates is POISONED, not merely
            # stale: it was almost certainly stored during a run with a forged
            # collaborator, before `_collaborators_are_patched` existed. Report
            # it and keep auditing the rest.
            mismatched += 1
            print(f"  POISONED {directory.name}: {str(error).splitlines()[0][:88]}")
            continue
        if {k: bytes(v) for k, v in stored.items()} != fresh:
            mismatched += 1
            print(f"  MISMATCH {directory.name}")
    print(f"regen_cache: verified {checked} entr{'y' if checked == 1 else 'ies'}, "
          f"{mismatched} bad, {orphaned} unverifiable (no stored spec)")
    if mismatched:
        print("regen_cache: DELETE THIS CACHE -- a bad entry can turn a real "
              "regression into a green suite")
    return 1 if mismatched else 0


def stats() -> int:
    root = cache_root()
    if root is None:
        print(f"regen_cache: {_ENV_VAR} is unset; caching is OFF")
        return 0
    entries = list(root.glob("*/*/index.json"))
    total = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
    print(f"regen_cache: {root}")
    print(f"  entries      : {len(entries)}")
    print(f"  on-disk bytes: {total:,}")
    print(f"  source key   : {source_fingerprint()[:16]}")
    return 0


def main(argv: list[str]) -> int:
    if "--verify" in argv:
        return verify_all()
    if "--stats" in argv:
        return stats()
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
