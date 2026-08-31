# noisemaker-for-cpp

A C++20 CPU port of the [Noisemaker](https://noisemaker.app) shader engine.

This renders Noisemaker's GLSL effect catalog on the CPU, with no GPU, no
GLSL driver, and no runtime shader compilation. It is a sibling of
`noisemaker-for-cpu` (JavaScript) and targets bit-level parity with it.

The library has no dependencies beyond a C++20 compiler and zlib.

## How it works

Effects are **not** hand-written C++. The pinned GLSL corpus is compiled ahead
of time into C++20 by a typed generator in `tools/glslcpp/`:

1. Each GLSL program is parsed and semantically analyzed into a typed IR.
2. A per-program structural profile authenticates the exact AST closure that
   program uses.
3. A validator admits **only** that authenticated closure and independently
   rejects nearby unsupported shapes.
4. An emitter — which re-authenticates from scratch rather than trusting the
   validator — lowers the typed AST to C++20.

The generated output is committed to the tree, so building this repository
requires no Python and no code generation:

- `src/typed_generated/typed_slice.cpp`
- `src/typed_generated/typed_manifest.json`
- `include/noisemaker/generated/catalog.hpp`

Generation is deterministic. `python -m tools.glslcpp.generate_typed_slice
--check` regenerates everything in memory and fails if the committed output
differs by a single byte. CI runs that check on every push.

## Coverage

This port is **in progress**. Coverage against the pinned corpus revision
`a024dc3a960cc44af454abc7aebce50456c194e6`:

| | Count | Derived from |
|---|---:|---|
| Corpus programs | 212 | the `programs` array in `tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/manifest.json` |
| Ported into the typed slice | 211 | the `programs` array in `src/typed_generated/typed_manifest.json` |
| Corpus programs outside the typed slice | 1 | set difference of the two arrays above: `filter/wormhole:deposit`, which is ported separately as a scatter pass in `src/effects/scatter/wormhole.cpp` |
| Catalog entries | 213 | `kCatalog` in `src/typed_generated/typed_slice.cpp`: the 211 typed program keys, plus a second, earlier-generation factory registered under `filter/invert:inv` and under `synth/solid:solid` |

The corpus and typed counts are re-derivable from a clean checkout without
external state: `python -m tools.glslcpp.check_semantics --check` prints the
corpus count and `python -m tools.glslcpp.generate_typed_slice --check` prints
the typed count.

Every program in the pinned corpus is therefore compiled and bound, but the
port is not finished: parity verification, the DSL graph executor, and a
standing queue of open defects are still in flight. The live list of remaining
work is the top block of
[`docs/port-engineering/NEXT_CODING_AGENT_HANDOFF.md`](docs/port-engineering/NEXT_CODING_AGENT_HANDOFF.md).

The corpus itself is vendored, not authored here. Its GLSL sources under
`tools/glslcpp/corpus/` come from
[`noisefactorllc/noisemaker`](https://github.com/noisefactorllc/noisemaker) at
revision `a024dc3a960cc44af454abc7aebce50456c194e6`, and are MIT-licensed
there.

### Parity and its documented exceptions

Ported programs are checked against the JavaScript reference implementation
with pixel-level fixtures, not merely compiled, and capabilities are admitted
one authenticated closure at a time.

Where a program's emitted kernel has been *measured* divergent from the
reference, the project records that in code rather than leaving it implicit:
each such program is listed in `kMeasuredParityExclusions` in
`src/graph/executor.cpp`, together with the measured divergence. The DSL graph
executor refuses to run an excluded program, raising `unavailable_pass`.

Read that list before treating any kernel's output as authority-exact, and
note its scope: the guard lives in the graph executor. The generated catalog
still exposes an excluded program's `bind_*` factory, so a direct
`noisemaker::generated::bind()` call by key is not gated by it.

## Build

Requires CMake 3.20+, a C++20 compiler, and zlib.

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build --output-on-failure
```

The project compiles with `-Wall -Wextra -Wpedantic -Werror
-ffp-contract=off`. Floating-point contraction is disabled deliberately:
fused multiply-add would silently change results and break parity with the
reference.

## Use

### Render a DSL program

`noisemaker-render` is the command-line front end. Build it, point it at a DSL
program, and you get a PNG:

```bash
cmake --build build --target noisemaker-render

./build/noisemaker-render tests/fixtures/dsl/blur.dsl   # writes blur.png
```

`cmake --install build --prefix <prefix>` also installs it to
`<prefix>/bin/noisemaker-render`, so the build-tree path below is a
convenience, not the only way to run it. The install is optional: a
library-only build (`cmake --build build --target noisemaker-cpu`) still
installs cleanly, without the executable.

With no options it renders 512x512 at time 0, frame 0, seed 1, and writes the
program's own name with a `.png` extension into the current directory. Every
option is optional and paths may be relative:

```bash
./build/noisemaker-render program.dsl -o out.png
./build/noisemaker-render program.dsl --width 512 --height 512 --seed 7 \
    --time 0.5 --frame 3
```

| option | default | meaning |
|---|---|---|
| `-o`, `--output PATH` | the program's basename + `.png` | PNG to write |
| `--width N` | 512 | pixels across |
| `--height N` | 512 | pixels down |
| `--time D` | 0 | animation time in seconds |
| `--frame N` | 0 | frame counter |
| `--seed D` | 1 | seed |
| `--raw-rgba8 PATH` | — | also write raw top-down RGBA8 bytes |
| `--metadata PATH` | — | also write a JSON document describing the render |

**No environment variables are needed to render.** The renderer reads nothing
but the program file you name. (The parity lane in
[Tests](#tests) is the only thing that needs the external JS authority.)

A DSL program names effects from the catalog. To see what is available:

```bash
./build/noisemaker-render --list-effects   # every catalog key, sorted
```

Rendering is fail-closed. A program the executor will not run is refused with
the executor's own reason and a nonzero exit status, and nothing is written:

```
$ ./build/noisemaker-render snow.dsl
noisemaker-render: snow.dsl cannot be rendered, so nothing was written.
  reason: the authority executes a hand-written CPU adapter for this program and the emitted typed kernel is measured divergent (499 of 748 RGBA8 bytes at 17x11)
  code:   unavailable_pass (7)
  effect: filter/snow, pass 0 "main" (filter/snow:snow)
```

`--help` prints the full option list and the exit codes (`0` rendered, `2`
unusable command line, `4` refused, `5` plan authentication failure, `6` output
could not be written).

`noisemaker-render` renders through the same compile/execute/export path as the
corpus parity driver `noisemaker-dsl-cpu-case`, so the bytes it produces are the
bytes that lane validates. That driver is a *harness* tool: it demands absolute
paths and a `--source-sha256` of its input because a corpus record must prove
which bytes it ran. Reach for it only when running the parity lane; for
rendering a program, use `noisemaker-render`.

### Use the library directly

Much of this library is header-inline — every `noisemaker::glsl::` helper, and
the matrix and vector operators — so it compiles in *your* translation unit
under *your* flags. `-ffp-contract=off` is therefore part of the public
contract, not just this project's build: without it the compiler may fuse a
multiply and an add into a single FMA and silently change results.

The exported CMake target carries the flag for you. Consuming the package with
`find_package(noisemaker-for-cpp CONFIG REQUIRED)` and linking
`NoisemakerForCpp::noisemaker-cpu` propagates both `-ffp-contract=off` and the
C++20 requirement to your targets. If you build without CMake, pass
`-std=c++20 -ffp-contract=off` yourself.

Bind a kernel by name, run a pass, encode the result:

```cpp
#include "noisemaker/generated/catalog.hpp"
#include "noisemaker/pass_runner.hpp"
#include "noisemaker/png.hpp"

noisemaker::glsl::Bindings bindings;
bindings.set_uniform("resolution", noisemaker::glsl::Vec2(256.0f, 256.0f));
bindings.set_uniform("scale", 4.0f);
bindings.set_uniform("seed", std::int32_t{7});
// ... remaining uniforms for this kernel

const noisemaker::BoundKernel kernel =
    noisemaker::generated::bind_synth_perlin_perlin(bindings);
const noisemaker::Surface surface =
    noisemaker::run_pass(kernel, 256, 256);
const std::vector<std::uint8_t> png = noisemaker::encode_png(surface);
```

Kernels can also be looked up dynamically:

```cpp
const noisemaker::BoundKernel kernel =
    noisemaker::generated::bind("synth/perlin:perlin", bindings);

for (const auto& factory : noisemaker::generated::catalog()) {
  // factory.key, factory.bind
}
```

Binding is fail-closed with respect to uniforms: a missing or wrongly-typed
uniform throws `noisemaker::glsl::KernelBindingError` rather than rendering
something plausible. It does not consult the measured-parity exclusion list
described under [Coverage](#parity-and-its-documented-exceptions).

`BoundKernel` is a stateful execution handle, matching the JavaScript bound
factory it ports. It retains fragment output state across pixels and repeated
passes, and copies of one `BoundKernel` share that same state. Do not render
through the same bound instance, or any of its copies, concurrently. Bind a
fresh kernel for each concurrent worker instead. Both `run_pass` and the
lower-level `run_pixel` preserve this stateful contract; the raw generated
callback and its state are intentionally not exposed.

`Bindings::set_texture` does **not** take ownership. The caller must keep the
`Surface` alive, at a stable address, and unmodified for the lifetime of any
kernel bound from it.

A complete, buildable example is in [`examples/perlin.cpp`](examples/perlin.cpp):

```bash
cmake --build build --target noisemaker-cpu-example-perlin
./build/noisemaker-cpu-example-perlin   # writes perlin.png
```

## Tests

Native tests (fixtures, parity, binding ABI, fail-closed behavior):

```bash
ctest --test-dir build --output-on-failure
```

Generator tests (parser, validator, emitter, mutation barriers, historical
reconstruction, determinism) require Python 3.12+:

```bash
python -m unittest discover -s tests -p 'test_*.py' -q
```

The Python suite is slow by design — it regenerates the entire typed slice
many times to prove reconstruction and determinism properties.

## Layout

```
include/noisemaker/     public headers, plus the generated catalog
src/                    runtime (surface, sampler, PNG, GLSL runtime)
src/typed_generated/    generated effect kernels — do not edit by hand
tools/glslcpp/          the GLSL -> C++ generator and the pinned corpus
tests/                  native and generator tests, plus frozen oracles
examples/               buildable usage examples
docs/port-engineering/  design record: briefs, reviews, corpus censuses,
                        and the JS-golden oracle generators
```

The parity oracles are the load-bearing part of `docs/port-engineering/`: each
generator drives the real, unmodified JavaScript reference and emits a
`--check`-deterministic fixture, so a drifted oracle fails loudly instead of
quietly re-baselining. See `docs/port-engineering/README.md`.

## License

MIT. See [LICENSE](LICENSE).

The vendored GLSL corpus under `tools/glslcpp/corpus/` is MIT-licensed source
from [`noisefactorllc/noisemaker`](https://github.com/noisefactorllc/noisemaker),
pinned at revision `a024dc3a960cc44af454abc7aebce50456c194e6`.
