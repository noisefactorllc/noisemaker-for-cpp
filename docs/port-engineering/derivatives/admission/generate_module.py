#!/usr/bin/env python3
"""Generate the frozen data payload for derivative_admission_profile.py from
admission-facts.json. Read-only: writes only to this /tmp directory. The
resulting text is meant to be reviewed and then hand-copied into the real
module under noisemaker-for-cpp/tools/glslcpp/frontend/.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

FACTS = pathlib.Path(__file__).resolve().parent / "admission-facts.json"


def tup(value):
    if isinstance(value, list):
        return tuple(tup(item) for item in value)
    return value


def main() -> None:
    data = json.loads(FACTS.read_text(encoding="utf-8"))
    records = []
    for key in sorted(data.keys()):
        row = data[key]
        record = (
            key,
            row["raw_bytes"], row["raw_sha256"],
            row["normalized_bytes"], row["normalized_sha256"],
            tup(row["preprocessor_defines"]),
            row["functions_sha256"], row["whole_sha256"], row["interface_sha256"],
            tup(row["loop_proof"]),
            tup(row["resources"]),
            tup(row["functions"]),
            tup(row["nodes"]),
            tup(row["ancestors"]),
        )
        records.append(record)
    frozen = tuple(records)
    repr_str = repr(frozen)
    sha = hashlib.sha256(repr_str.encode("utf-8")).hexdigest()
    out = pathlib.Path(__file__).resolve().parent / "frozen_payload.txt"
    out.write_text(repr_str + "\n" + sha + "\n", encoding="utf-8")
    print("sha256:", sha)
    print("len(repr):", len(repr_str))
    print("programs:", len(records))
    for record in records:
        print(" ", record[0], "nodes:", len(record[11]))


if __name__ == "__main__":
    main()
