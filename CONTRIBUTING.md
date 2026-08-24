# Contributing to Noisemaker for C++

Thanks for your interest in contributing.

## Getting set up

The project requires CMake 3.20+, a C++20 compiler, and zlib. Python 3.12+
is required for the generator test suite.

Run the project checks before submitting a change:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build --output-on-failure
python -m unittest discover -s tests -p 'test_*.py' -q
python -m tools.glslcpp.generate_typed_slice --check
```

Keep changes focused and include regression coverage for behavior changes. If
generated catalog or typed-IR files need to change, update their canonical
inputs and regenerate them instead of editing generated output by hand. Never
commit credentials, private source archives, built binaries, rendered media,
or Python cache files.

## Reporting issues

Open a GitHub issue with the operating system, compiler and version, CMake
version, project commit, and exact reproduction steps. Report suspected
vulnerabilities privately using [SECURITY.md](SECURITY.md).
