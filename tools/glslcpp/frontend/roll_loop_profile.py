"""Source-bound MIDI Roll loop proof for positive full-resolution height."""

from __future__ import annotations

import hashlib

from .typed_ir import TypedStatement

KEY = "synth/roll:roll"
RAW_SHA256 = "92b426fa60df51c3db057b8f93ce3c6525cf087fd2398c6e038046f9ede1d8c9"


def authenticate(program, source_hash):
    from .runtime_loop_bound_profile import (
        RuntimeLoopBoundContract, RuntimeScalarBoundSeed, _cleared_functions,
        _fail, _sha, _span, _walk_statement, validate_runtime_loop_contract,
    )

    raw = program.raw_source.encode()
    if (program.key != KEY or source_hash != RAW_SHA256 or len(raw) != 2305
            or hashlib.sha256(raw).hexdigest() != RAW_SHA256
            or len(program.source.encode()) != 1989
            or hashlib.sha256(program.source.encode()).hexdigest()
            != "0510d1d997a1c0c79eeece4a59c9fe184be7f6bf9f1e49b400771c2986b7174a"
            or program.preprocessor_defines or program.body_status != "analyzed"):
        raise _fail("source or define profile mismatch")
    functions = _cleared_functions(program)
    whole = (program.key, program.source, program.raw_source,
             program.declarations, functions, program.resources,
             program.body_status, program.local_type_names, program.structs,
             program.uniform_blocks, program.interface_symbols,
             program.builtin_symbols, program.preprocessor_defines)
    interface = (program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines)
    if (_sha(functions) != "d5c316143bc3b9a8b8af246e64f83c0d7f7024810c17ea32adff0d37484bc962"
            or _sha(whole) != "6477ca0cd5ffdd66a44d7ac512195569fc896ebd6d958430c9265fe98952ee50"
            or _sha(interface) != "57bda2f873825d9287c4d4831d7d6a5ebf3457c090f66741ca22a13a02fbdd97"):
        raise _fail("interface, function, or call-graph profile mismatch")
    main, = functions
    # fullResolution.y >= 1 implies lanePixels >= 1/16 and
    # keysPerPixel <= 48/(1/16) = 768, including each f32 narrowing.
    # Therefore max(1, int(ceil(keysPerPixel))) lies in [1,768]. The
    # factory guard and this exact declaration chain are both required.
    declarations = {statement.expressions[0].symbol.name: statement
                    for statement in main.body if statement.kind == "decl"}
    expected = {
        "lanePixels": "d459d1b37d0c0286457e97545053dbabb866bd8fbf074eab7a6a05d42e94c5f2",
        "keysPerPixel": "fa58067ca95d9f73fcac468e23df35e5447acd4838e1eb2ff749f2889c292bab",
        "spread": "c3393a4762b26c9802435fd4181573d06f638c8e6102935c72d3054e8a04da50",
    }
    if any(name not in declarations or _sha(declarations[name]) != digest
           for name, digest in expected.items()):
        raise _fail("resolution-derived spread declaration mismatch")
    radius = declarations["spread"].expressions[0]
    loops = [value for statement in main.body for value in _walk_statement(statement)
             if isinstance(value, TypedStatement) and value.kind == "for"]
    if (len(loops) != 1 or _span(loops[0]) != "49:5-56:6"
            or _sha(loops[0]) != "f4b3972715cfb8ce9de8a40b52be0ace191011ac09948230c617f67c4a7aef99"):
        raise _fail("resolution-derived spread loop mismatch")
    seed = RuntimeScalarBoundSeed(radius.symbol.id, 768,
                                  "runtime-positive-height-spread", radius.symbol)
    return validate_runtime_loop_contract(RuntimeLoopBoundContract(
        KEY, seed, "positive-height-spread", "fullResolution", 1, float("inf"), 512,
        f"{KEY} fullResolution.y must be finite and at least 1",
        radius_declaration=radius))
