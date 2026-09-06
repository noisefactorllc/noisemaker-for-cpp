# {{NM_PROGRAM_NAME}}

A Noisedeck program packaged with the C++20 CPU renderer.

## Build and render

Install CMake 3.20 or newer, a C++20 compiler, and the zlib development headers
and library (on Debian/Ubuntu: `cmake g++ zlib1g-dev`). From this folder:

```sh
cmake -S engine -B build -DCMAKE_BUILD_TYPE=Release -DNOISEMAKER_BUILD_DEVELOPMENT_TOOLS=OFF
cmake --build build --config Release --target noisemaker-render --parallel 2
./build/noisemaker-render program.dsl --width 64 --height 64 --output out.png
```

For a multi-configuration generator, the executable is in `build/Release/`
(with `.exe` on Windows). The first build compiles the included source; later
renders reuse the binary. Once the compiler, CMake and zlib are installed,
building and rendering require no network, Python, GPU or shader compiler.

Increase `--width` and `--height` for larger output. `--seed`, `--time` and
`--frame` control the render; `--help` lists all options. Paths are relative to
the directory you run the command from. The program itself is `program.dsl`.

## Contents

- `engine/`: the C++ renderer, public headers and generated effect kernels.
- `program.dsl`: your program's source.
- `noisedeck-export.json`: export and kit provenance.
- `LICENSES/`: the Noisemaker and C++ port licenses.

The engine can also be used as a CMake library. Its
`NoisemakerForCpp::noisemaker-cpu` target propagates C++20 and the floating-point
flags required by the renderer. See the
[port documentation](https://github.com/noisefactorllc/noisemaker-for-cpp).

## Compatibility

Noisedeck exported this program against Noisemaker `{{NM_ENGINE_VERSION}}`.
This port is still in progress. Effects with unavailable or scatter passes, plus Snow and
Test Pattern's measured parity exclusions, are excluded from the kit's
compatibility list. Media input is also excluded because this CLI cannot bind
external images. Other parameter or graph combinations can also be refused
by the renderer. Fibers, Scratches and Stray Hair need an unavailable overlay
adapter and are excluded too. A refusal reports a reason and writes no image. The kit does
not guarantee pixel parity with the current browser engine.

## Effects used by this program

{{NM_EFFECT_LIST}}

## License

The engine and port are MIT licensed; see `LICENSES/`. zlib is installed
separately under its own license. Your program and rendered imagery are yours.
