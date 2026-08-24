import re, ast, sys, pathlib

cpp = pathlib.Path("tests/test_generated_kernels.cpp").read_text()


def _task30_parse_executable_tables(cpp: str) -> dict:
    def braced_after(marker: str, offset: int = 0) -> str:
        start = cpp.index("{", cpp.index(marker, offset))
        depth = 0
        quoted = False
        escaped = False
        for index in range(start, len(cpp)):
            character = cpp[index]
            if quoted:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    quoted = False
            elif character == '"':
                quoted = True
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return cpp[start:index + 1]
        raise AssertionError(f"unterminated initializer after {marker}")

    def initializer(marker: str, offset: int = 0):
        source = braced_after(marker, offset)
        source = re.sub(r"\b(0[xX][0-9a-fA-F]+|[0-9]+)(?:ULL|U)\b", r"\1", source)
        source = re.sub(r"(?<![A-Za-z0-9_])([0-9]+\.[0-9]+)f\b", r"\1", source)
        source = re.sub(r"\bfalse\b", "False", source)
        source = re.sub(r"\btrue\b", "True", source)
        value = ast.literal_eval(source.replace("{", "[").replace("}", "]"))
        while isinstance(value, list) and len(value) == 1 and isinstance(value[0], list):
            value = value[0]
        return value

    def compact(source: str) -> str:
        return re.sub(r"\s+", "", source)

    def enum_values(marker: str):
        values = []
        for item in braced_after(marker)[1:-1].split(","):
            if not item.strip():
                continue
            name, numeric_id = item.strip().split("=", 1)
            values.append([name.strip(), int(numeric_id.strip())])
        return values

    table_start = cpp.index("// TASK30_NATIVE_ORACLE_TABLE_BEGIN")
    table_end_marker = "// TASK30_NATIVE_ORACLE_TABLE_END"
    table_end = cpp.index("\n", cpp.index(table_end_marker, table_start)) + 1
    harness_start = cpp.index("// TASK30_DIRECT_ABI_HARNESS_BEGIN")
    harness_end_marker = "// TASK30_DIRECT_ABI_HARNESS_END"
    harness_end = cpp.index("\n", cpp.index(harness_end_marker, harness_start)) + 1
    harness = cpp[harness_start:harness_end]
    switch_start = harness.index("// TASK30_DIRECT_ABI_SWITCH_BEGIN")
    switch_end = harness.index("// TASK30_DIRECT_ABI_SWITCH_END", switch_start)
    dispatch_region = harness[switch_start:switch_end]
    switch_source = braced_after("switch (mode)", harness_start)
    arm_matches = list(re.finditer(
        r"case\s+Task30RelationalMode::([a-z0-9_]+)\s*:(.*?)"
        r"(?=case\s+Task30RelationalMode::|\}\s*$)", switch_source, re.DOTALL))
    signature_start = cpp.index("task30_relational_signature", harness_end)
    signature_body = braced_after("{", cpp.index("{", signature_start))
    signature_fields = re.findall(
        r"signature\[cursor\+\+\]\s*=\s*(.*?);", signature_body)
    guard_source = compact(dispatch_region[dispatch_region.index(switch_source) + len(switch_source):])

    return {
        "cases": initializer("kTask30NativeCases"),
        "relational_rows": initializer("kTask30RelationalRows"),
        "mode_enum": enum_values("enum class Task30RelationalMode"),
        "names": initializer("kTask30RelationalModeNames"),
        "dispatch": [match.group(1) for match in arm_matches],
        "arms": [[match.group(1), compact(match.group(2))] for match in arm_matches],
        "signature_fields": [compact(item) for item in signature_fields],
        "guard": guard_source,
        "authenticated_source": compact(cpp[table_start:harness_end]),
    }


parsed = _task30_parse_executable_tables(cpp)
print("cases", len(parsed["cases"]))
print("rows", len(parsed["relational_rows"]))
print("modes", parsed["mode_enum"])
print("names", parsed["names"])
print("dispatch", parsed["dispatch"])
print("num distinct arms", len(set(b for _, b in parsed["arms"])))
print("signature_fields", parsed["signature_fields"])
print("guard", parsed["guard"][:200])
print("authenticated_source len", len(parsed["authenticated_source"]))

# Tamper sensitivity check over a sample of tokens
begin = cpp.index("// TASK30_NATIVE_ORACLE_TABLE_BEGIN")
end = cpp.index("// TASK30_DIRECT_ABI_HARNESS_END") + len("// TASK30_DIRECT_ABI_HARNESS_END")
region = cpp[begin:end]
tokens = list(re.finditer(
    r'"[^"\n]*"|::|==|!=|<=|>=|&&|\|\||'
    r'\b(?:0x[0-9a-fA-F]+|[0-9]+(?:\.[0-9]+)?f?)(?:U)?\b|'
    r'\b[A-Za-z_][A-Za-z0-9_]*\b|[{}()\[\],;:+\-*/=<>]',
    region))
print("num tokens", len(tokens))

baseline = parsed
vacuous = []
checked = 0
import random
random.seed(0)
sample = tokens if len(tokens) < 4000 else random.sample(tokens, 4000)
for m in sample:
    old = m.group(0)
    if old.startswith('"'):
        new = old[:-1] + 'X"'
    elif re.match(r"[A-Za-z_]", old):
        new = old + "X"
    elif re.match(r"(?:0x|[0-9])", old):
        new = "7" if old != "7" else "8"
    else:
        new = "@"
    tampered_region = region[:m.start()] + new + region[m.end():]
    tampered_cpp = cpp[:begin] + tampered_region + cpp[end:]
    checked += 1
    try:
        changed = _task30_parse_executable_tables(tampered_cpp)
    except Exception:
        continue
    if changed == baseline:
        vacuous.append((m.start(), old))

print("checked", checked, "vacuous", len(vacuous))
for v in vacuous[:30]:
    print("VACUOUS", v, region[max(0,v[0]-30):v[0]+30])
