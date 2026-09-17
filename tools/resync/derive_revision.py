"""Rewrite hardcoded corpus-revision string literals in Python tests to derive from check_corpus.REVISION.

usage: derive_revision.py <repo> <revision>
Every plain (non-bytes) string literal containing <revision> becomes an f-string that interpolates
CORPUS_REVISION; the module gains `from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION`.
"""
import io, pathlib, re, sys, tokenize

repo, revision = pathlib.Path(sys.argv[1]), sys.argv[2]
IMPORT = "from tools.glslcpp.check_corpus import REVISION as CORPUS_REVISION\n"
PREFIX = re.compile(r"^([rRuUfF]*)(['\"]{3}|['\"])")
changed = []
for path in sorted((repo / "tests").glob("*.py")):
    text = path.read_text(encoding="utf-8")
    if revision not in text:
        continue
    tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    edits = []
    fstring_start = None
    for tok in tokens:
        if getattr(tokenize, "FSTRING_START", None) == tok.type:
            fstring_start = tok.start
            continue
        if getattr(tokenize, "FSTRING_END", None) == tok.type:
            start = offsets[fstring_start[0] - 1] + fstring_start[1]
            end = offsets[tok.end[0] - 1] + tok.end[1]
            span = text[start:end]
            if revision in span:
                edits.append((start, end, span.replace(revision, "{CORPUS_REVISION}")))
            continue
        if tok.type != tokenize.STRING or revision not in tok.string:
            continue
        match = PREFIX.match(tok.string)
        prefix, quote = match.group(1), match.group(2)
        if "b" in prefix.lower():
            raise SystemExit(f"{path}: bytes literal carries the revision")
        body = tok.string[len(prefix) + len(quote):-len(quote)]
        start = offsets[tok.start[0] - 1] + tok.start[1]
        end = offsets[tok.end[0] - 1] + tok.end[1]
        if body == revision:
            edits.append((start, end, "CORPUS_REVISION"))
        elif "{" in body or "}" in body:
            parts = [prefix + quote + part + quote if part else None for part in body.split(revision)]
            pieces = []
            for index, part in enumerate(parts):
                if index:
                    pieces.append("CORPUS_REVISION")
                if part:
                    pieces.append(part)
            edits.append((start, end, "(" + " + ".join(pieces) + ")"))
        else:
            edits.append((start, end, "f" + prefix + quote + body.replace(revision, "{CORPUS_REVISION}") + quote))
    for start, end, replacement in reversed(edits):
        text = text[:start] + replacement + text[end:]
    if revision in text:
        raise SystemExit(f"{path}: revision survives outside string literals")
    if IMPORT not in text:
        tools_import = re.search(r"^(?:from tools[.\s]|import tools\b)", text, flags=re.M)
        if tools_import:
            anchor = tools_import.start()
        else:
            top = list(re.finditer(r"^(?:from \S+ import (?:\((?:.|\n)*?\)|[^\n]+)|import [^\n]+)\n", text, flags=re.M))
            anchor = top[-1].end() if top else 0
        text = text[:anchor] + IMPORT + text[anchor:]
    compile(text, str(path), "exec")
    path.write_text(text, encoding="utf-8")
    changed.append(path.name)
print(f"rewrote {len(changed)} files")
