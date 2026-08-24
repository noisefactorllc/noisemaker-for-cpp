import dataclasses
import hashlib
import pathlib
import sys

sys.path.insert(0, ".")
REPOSITORY = pathlib.Path(".")

from tools.glslcpp import generate_typed_slice
from tools.glslcpp.emit_typed_cpp import TypedEmissionError, render_typed_cpp
from tools.glslcpp.frontend import parse_program
from tools.glslcpp.frontend.curl_vector_math_profile import CURL_KEY, PROFILE
from tools.glslcpp.frontend.semantic import analyze_program

source = (REPOSITORY / "tools/glslcpp/corpus/"
          "a024dc3a960cc44af454abc7aebce50456c194e6/"
          "sources/synth/curl/curl.glsl").read_text()
source_hash = hashlib.sha256(source.encode()).hexdigest()
exact = analyze_program(parse_program(
    source, CURL_KEY, {"OCTAVES": 1, "OUTPUT_MODE": 3, "RIDGES": True}), CURL_KEY)

foreign = dataclasses.replace(exact, key="synth/curl:foreignvariant")

for label, fn in (
    ("emitter no profile", lambda: render_typed_cpp(exact, exact.key, source_hash)),
    ("emitter wrong profile", lambda: render_typed_cpp(
        exact, exact.key, source_hash, curl_vector_math_profile="wrong")),
    ("emitter foreign with profile", lambda: render_typed_cpp(
        foreign, foreign.key, source_hash, curl_vector_math_profile=PROFILE)),
    ("emitter foreign no carrier", lambda: render_typed_cpp(foreign, foreign.key, source_hash)),
):
    try:
        fn()
        print(label, "ACCEPTED (bug)")
    except TypedEmissionError as error:
        print(label, "->", error)

for label, fn in (
    ("validator no profile", lambda: generate_typed_slice.validate_capabilities(
        exact, generate_typed_slice.APPROVED_CAPABILITIES, source_hash=source_hash)),
    ("validator wrong profile", lambda: generate_typed_slice.validate_capabilities(
        exact, generate_typed_slice.APPROVED_CAPABILITIES, source_hash=source_hash,
        curl_vector_math_profile="wrong")),
    ("validator foreign with profile", lambda: generate_typed_slice.validate_capabilities(
        foreign, generate_typed_slice.APPROVED_CAPABILITIES, source_hash=source_hash,
        curl_vector_math_profile=PROFILE)),
    ("validator foreign no carrier", lambda: generate_typed_slice.validate_capabilities(
        foreign, generate_typed_slice.APPROVED_CAPABILITIES, source_hash=source_hash)),
):
    try:
        fn()
        print(label, "ACCEPTED (bug)")
    except generate_typed_slice.GeneratorError as error:
        print(label, "->", error)
