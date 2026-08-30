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
