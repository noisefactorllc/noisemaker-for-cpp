"""Audit how a corpus/authority bump moved historical typed-slice reconstructions.

usage: reconstruction_audit.py <old-cache> <new-cache> <old-corpus-manifest> <new-corpus-manifest> [allowed-extra-keys...]
Pairs regen-cache entries by spec (revision ignored). Both artifacts are normalized: old corpus
revision -> new, changed programs' old raw/normalized sha -> new, then every remaining 64-hex
digest is masked (derived hashes are recomputed by the generator and checked by --check).
typed_slice.cpp is split into per-program blocks at "// Typed IR program: <key>"; typed_manifest.json
is compared per program record. Every normalized difference must belong to a semantically changed
program (or an explicitly allowed key); otherwise it is UNEXPLAINED and the exit code is 1.
Both caches must contain the same nonempty set of specs, each with both generated artifacts.
Missing comparisons fail the audit, including when their programs are allowed to change.
"""
import json, pathlib, re, sys

old_cache, new_cache = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
om = {e["program_key"]: e for e in json.loads(pathlib.Path(sys.argv[3]).read_text())["programs"]}
nm = {e["program_key"]: e for e in json.loads(pathlib.Path(sys.argv[4]).read_text())["programs"]}
allowed = set(sys.argv[5:])
semantic = {k for k in om if om[k]["normalized_sha256"] != nm[k]["normalized_sha256"]} | allowed
REV_OLD, REV_NEW = "a024dc3a960cc44af454abc7aebce50456c194e6", "0ed489ec46842bffba33ee2ec65a218b6dda51f5"
subs = [(REV_OLD, REV_NEW)]
for k in om:
    for f in ("raw_sha256", "normalized_sha256"):
        if om[k][f] != nm[k][f]:
            subs.append((om[k][f], nm[k][f]))
HEX = re.compile(r"\b[0-9a-f]{64}\b")


def norm(text):
    for a, b in subs:
        text = text.replace(a, b)
    return HEX.sub("<H>", text)


def entries(root):
    out = {}
    for index in root.glob("*/*/index.json"):
        spec = json.loads((index.parent / "spec.json").read_text())
        spec.pop("revision", None)
        names = json.loads(index.read_text())
        out[json.dumps(spec, sort_keys=True)] = {k: (index.parent / v).read_bytes().decode() for k, v in names.items()}
    for spec_path in root.glob("*/spec.json"):
        spec = json.loads(spec_path.read_text())
        spec.pop("revision", None)
        artifacts = {f.name.replace("__", "/"): f.read_bytes().decode() for f in spec_path.parent.iterdir() if f.name != "spec.json"}
        out[json.dumps(spec, sort_keys=True)] = artifacts
    return out


def slice_blocks(text):
    # The catalog and route tables belong to the translation unit, not the
    # final shader. Match their generator-owned opener, rather than arbitrary
    # const/static declarations that can occur inside a program namespace.
    tail = re.search(r"^namespace \{\nconstexpr std::array<KernelFactory, \d+> kCatalog\{\{", text, flags=re.M)
    program_text = text[:tail.start()] if tail else text
    parts = re.split(r"^// Typed IR program: (\S+)$", program_text, flags=re.M)
    blocks = {"<preamble>": parts[0]}
    for i in range(1, len(parts), 2):
        blocks[parts[i]] = parts[i + 1]
    if tail:
        blocks["<tail>"] = text[tail.start():]
    return blocks


def manifest_records(text):
    doc = json.loads(norm(text))
    records = {}
    for name, value in doc.items():
        if isinstance(value, list) and value and isinstance(value[0], dict) and "program_key" in value[0]:
            for item in value:
                records[f"{name}:{item['program_key']}"] = json.dumps(item, sort_keys=True)
        else:
            records[f"<top>:{name}"] = json.dumps(value, sort_keys=True)
    return records


old, new = entries(old_cache), entries(new_cache)
paired = sorted(set(old) & set(new))
unpaired = sorted(set(old) ^ set(new))
for key in unpaired:
    missing = "new" if key in old else "old"
    print(f"missing {missing} comparison for spec: {key}")
if not paired:
    print("no paired reconstruction evidence")
bad = 0
for key in paired:
    required = {"src/typed_generated/typed_slice.cpp", "src/typed_generated/typed_manifest.json"}
    missing_artifacts = False
    for side, artifacts in (("old", old[key]), ("new", new[key])):
        missing = required - artifacts.keys()
        if missing:
            print(f"missing reconstruction artifact in {side} spec {key}: {sorted(missing)}")
            bad += len(missing)
            missing_artifacts = True
    if missing_artifacts:
        continue
    moved = {}
    for artifact in sorted(set(old[key]) | set(new[key])):
        a, b = old[key].get(artifact, ""), new[key].get(artifact, "")
        if artifact.endswith("typed_slice.cpp"):
            ba, bb = slice_blocks(a), slice_blocks(b)
            diff = {k for k in set(ba) | set(bb) if norm(ba.get(k, "")) != norm(bb.get(k, ""))}
        else:
            ra, rb = manifest_records(a), manifest_records(b)
            diff = {k.split(":", 1)[1] if ":" in k and "/" in k else k for k in set(ra) | set(rb) if ra.get(k) != rb.get(k)}
        moved[artifact] = sorted(diff)
    unexplained = {art: [k for k in ks if k not in semantic] for art, ks in moved.items()}
    n_unexplained = sum(len(v) for v in unexplained.values())
    bad += n_unexplained
    programs = len(json.loads(key).get("programs", []))
    print(f"spec(programs={programs}): moved={ {a: len(v) for a, v in moved.items()} } unexplained={ {a: v for a, v in unexplained.items() if v} }")
print(f"paired={len(paired)} of old={len(old)} new={len(new)}; semantic set={sorted(semantic)}; unexplained={bad}; unpaired={len(unpaired)}")
sys.exit(1 if bad or unpaired or not paired else 0)
