# Task 28 implementation report

Date: 2026-08-11

## Result

Task 28 is implemented for the exact `filter/rotate:rot` target using carrier
`rotate-mat2-return-v1`.  The generated slice now contains 128 typed programs
and the public catalog contains 130 programs; the remaining unported set is 82.
No parser, semantic matrix logic, runtime, `glsl_types.hpp`, CMake, corpus, or
non-Task28 public-test behavior was changed.

The exception is fail closed and identity bound: the validator and emitter each
independently authenticate the exact Rotate source, declarations, functions,
interface, `mat2` constructor, sole helper return, sole call, and exact AST
object identities.  Only the authenticated `rotate2D` helper may return a
matrix.  An equal recursively rebuilt tree authenticates only its own objects;
borrowed or substituted objects fail.

## TDD and adversarial evidence

- Initial RED: the new profile import did not exist.  Subsequent REDs proved
  validator and emitter rejection when the required carrier/authentication was
  absent.  The catalog test also failed at the historical 129 count before the
  Task28 expectation was advanced to 130.
- GREEN: 59 distinct one-axis mutations, each checked at the profile,
  validator, and emitter boundaries (177 rejection assertions).  The test also
  proves exactly 59 named preconditions with no duplicate mutation keys.
- Task27 reconstruction remained exact: typed C++
  `aa15e...`, manifest `f254...`, and catalog `b82ab...` as frozen by the design.
- Six public Rotate cases authenticate F32 output, RGBA8 output, five pixel
  probes, input hash and immutability, repeatability, and generic/direct binder
  identity.
- Every one of five bindings is tested missing and wrong-type.
- Six explicit native `Mat2`/`Vec2` modes are executed across six rows (36
  executions): exact direct return, transpose, row-major multiply, diagonal,
  wrong sine sign, and helper-local by-value return.  Four wrong modes diverge;
  exact and local-return agree bit-for-bit while retaining distinct return-shape
  witnesses.  Invalid enum dispatch throws.
- Python parses and authenticates the native tables and dispatch, and
  single-token/literal tampering is rejected while the oracle JSON remains
  unchanged.

## Verification

- `python3 -m unittest discover -s tests -p 'test_*.py' -q`: 176 tests,
  1866.153 seconds, OK.
- Focused Task27 validator plus Task28 exact-safety tests: 2 tests, OK.
- Fresh warnings-as-errors Debug CMake build/CTest: 1/1 passed (3.03 s).
- Fresh warnings-as-errors Release CMake build/CTest: 1/1 passed (0.54 s).
- Fresh ASan+UBSan build/CTest: first Apple run reported only
  `AddressSanitizer: detect_leaks is not supported on this platform`; the
  prescribed retry with leak detection disabled passed 1/1 (10.29 s), with
  halt-on-error enabled.
- Task28 oracle check, corpus check, canonical generator check, and every Task15
  through Task28 oracle-generator check passed.  The frozen preimplementation
  `task-28-recompute.py --check` is intentionally no longer applicable after
  Rotate leaves the remaining frontier (it now reaches `StopIteration`); its
  bytes and sidecar were not changed, and its preflight check passed before RED.

## Stack and AArch64 ABI

Measured with AppleClang 16 `-fstack-usage -fno-inline`:

| build | `rotate2D` | `pixel` | maximum Rotate runtime helper |
|---|---:|---:|---:|
| Debug | 96 B static | 496 B static | 496 B (`pixel`) |
| Release | 64 B static | 144 B static | 144 B (`pixel`) |
| ASan+UBSan Debug | 288 B dynamic | 1408 B dynamic | 1408 B (`pixel`) |

The Release object is Mach-O arm64.  `rotate2D` occupies `0x37dd4..0x37e18`
with a fixed 32-byte machine frame, calls `___sincos_stret` directly, performs
the required negation/lane moves, and returns the four floats in `s0`-`s3`
without a hidden sret pointer.  `pixel` occupies `0x37e18..0x381d0` with a fixed
144-byte frame; the optimizer inlines the matrix application (its own direct
`___sincos_stret` relocation and multiply/add/subtract lane sequence prove the
path).  The two symbol ranges contain no indirect `br`/`blr`, heap allocation,
VLA/alloca, exception, virtual, or callback relocation.  Binder allocation is
outside the pixel path.

## Owned-file SHA-256

```
a0ca34a312a0f610c9acb1f6b009ee534f52fc6e1eb1fe1fa2da707e8beba454  tools/glslcpp/frontend/rotate_mat2_return_profile.py
ed1538426717f47a9feea1f58268c2b3a8d7316f5fd581a46e6f237a40c50c56  tools/glslcpp/generate_typed_slice.py
4e80ce5fe0de3cfd451ba9fb1146c963dd08cd001dcd7893a8e09061808a9511  tools/glslcpp/emit_typed_cpp.py
b42a0b0c46daf7959f1b404ce4d0c3a28e81adb60cd9d250384d7e2e1564db73  tools/glslcpp/typed_slice.json
5fc49abdb192c86ab6ba82d26507ef638ef0a1b67e268a3b53237494c6fc90ab  tests/test_typed_generator.py
5a8c0ac8447391478d204480bf2999a8d8077e5e3c8af6775b57f5ee91be2d55  tests/test_generated_kernels.cpp
b53e020b990a88d17de7fcaaa29965c1304cad510e2888cdd4e54ca98900763e  src/typed_generated/typed_slice.cpp
612d35229abf0580932cfaf11785311359afe29f20f1ebef5fb925cc91de044e  src/typed_generated/typed_manifest.json
372d1f69e1e7db772ddebc05945a714527b22b35f87ca3160bbb8eb85135a4ac  include/noisemaker/generated/catalog.hpp
```

Isolation hashes remained exact:

```
55fee138f1477d183cc1e007e89b104cb4b4d126de9b1688844879e73be121d6  tests/test_typed_slice.cpp
37e71f566d5b8d5e1abf68fee1b27338898e4afacb116764824274dfda6780d8  include/noisemaker/glsl_types.hpp
bca6b4ab77d26c72449ef8d7a66d5832fdc939ebb35a85211b7684dde62216d5  CMakeLists.txt
```

No Git action was performed.  The implementation is ready for independent
code review.
