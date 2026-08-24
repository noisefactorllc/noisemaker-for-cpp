# Task 22 CRT implementation design

> **Status:** implementation-ready design only. This document makes no
> repository change and authorizes no Git operation. Implement exactly the
> reviewed one-key scope below, stopping at every stated gate on drift.

**Goal:** publish exactly `filter/crt:crt` as the 116th typed factory and the
118th public factory while reproducing the pinned public CPU `crtFactory`
adapter's float32 reduced-turn sine semantics at six authenticated scalar
sites.

**Core decision:** add one typed-tree compatibility module,
`crt-metal-sine-v1`. It rewrites the six exact original `sin` expressions into
an inline tree composed solely of the existing float constructor, `floor`,
arithmetic, and outer `sin`. The generator validator and direct emitter each
invoke the same pure post-tree authenticator independently; neither boundary
trusts that the other ran. There is no carrier token in the typed IR and no new
proof record.

## 1. Frozen entry gate

Implementation begins only if all of these remain true from
`.`:

- Task 22 brief SHA-256:
  `e4cd4f75959d61d4114187cd033a16d7a11a5a723cf068303312e00fa8fcfc10`.
- Accepted Task 21 report SHA-256:
  `bfe301743399f25af45dfd14b0350d0effc0f0510b6e7f3371b69be2ec3883c1`.
- Task 22 frontier/oracle artifacts retain the four hashes in the brief:
  `c3d006f3...`, `dc2044ee...`, `c927f467...`, and `36ac4f8b...`.
- Accepted Task 21 counts remain 115 typed / 117 public / 95 unported / 212
  corpus.
- The Task 21 hashes of all Task 22 existing/generated files are exactly:

| Path | Accepted SHA-256 |
| --- | --- |
| `tools/glslcpp/typed_slice.json` | `e01050bd3e71df32df522da741a7087896fea500548bebe988f181bee4bfb802` |
| `tools/glslcpp/generate_typed_slice.py` | `ea51119950c7e7262282e57a85db895583125cc76d174d7acff51c57cea4dad1` |
| `tools/glslcpp/emit_typed_cpp.py` | `f8c9c21a8bc0590e2af78b892dc7504a55aafd8987a41e367a73f66a8de4ea11` |
| `tests/test_typed_generator.py` | `ea1b490eb75285e8fee77d24776725c37937d69db1c38e3bb15b8c3d5b99bb9b` |
| `tests/test_typed_slice.cpp` | `150dcd25ff794648299a9dcc83d875e9a29820784f13890aba276435e3640d61` |
| `tests/test_generated_kernels.cpp` | `143b9b290ec135e7018af7b53c9fccc4183ec1f4f7fe1848e6f135c557120df5` |
| `src/typed_generated/typed_slice.cpp` | `986d6d3116497282e468440a6786be5728ee53f0558ea8c5a553831e353aa5ba` |
| `src/typed_generated/typed_manifest.json` | `53e8c04374876a26a4ed0cec47587ebe998eccc7ce33b817b8d6ef0a6d73a124` |
| `include/noisemaker/generated/catalog.hpp` | `bb3d7f78ac49eb026ebccb8a14fd2a23d94fb43f200a98245d271168499748d4` |

Run and retain the output of:

```sh
shasum -a 256 docs/port-engineering/task-22-{brief,frontier-audit,oracle-generator.mjs,oracles.json,oracle-report.md}
shasum -a 256 docs/port-engineering/task-21-report.md
node docs/port-engineering/task-22-oracle-generator.mjs --check
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
```

Copy the three accepted generated outputs to a fresh, explicit temporary
baseline directory for the later byte-isolation comparison. Do not alter or
delete the accepted files. Any mismatch stops implementation for renewed
scope review.

## 2. Exact ownership and non-goals

The only repository paths allowed to change are:

1. create `tools/glslcpp/frontend/crt_compatibility.py`;
2. modify `tools/glslcpp/generate_typed_slice.py`;
3. modify `tools/glslcpp/emit_typed_cpp.py`;
4. modify `tools/glslcpp/typed_slice.json`;
5. modify `tests/test_typed_generator.py`;
6. modify `tests/test_typed_slice.cpp`;
7. modify `tests/test_generated_kernels.cpp`;
8. regenerate `src/typed_generated/typed_slice.cpp`;
9. regenerate `src/typed_generated/typed_manifest.json`;
10. regenerate `include/noisemaker/generated/catalog.hpp`.

Do not change typed IR records, semantic analysis, proof modules, runtime
headers or sources, sampler/Surface behavior, CMake, corpus inputs, public
binding APIs, Degauss, another program, or an oracle artifact. In particular:

- no global `glsl::sin` or `cos` behavior change;
- no helper function in generated C++ or the runtime;
- no new capability, proof, type, operator, builtin, literal mode, resource,
  binding, loop, or stage ABI;
- no dead-code removal: `simplex_random`, `clamp_index`, and local `alpha@205`
  remain;
- no use of `../noisemaker-for-cpu` at build, test, or
  generation time. It remains provenance for the already frozen JSON only.

## 3. Compatibility module design

Create `tools/glslcpp/frontend/crt_compatibility.py`. It is a pure immutable
typed-tree module patterned after `sacred_geometry_compatibility.py`, without
adding a typed proof carrier.

### 3.1 Public module surface

Expose exactly these public names for the generator and emitter:

```python
TRANSFORM = "crt-metal-sine-v1"
CRT_KEY = "filter/crt:crt"

def apply_crt_metal_sine(program: TypedProgram) -> TypedProgram: ...

def authenticate_crt_metal_sine(
        program: TypedProgram, source_hash: str | None) -> None: ...

def interface_fingerprint(program: TypedProgram) -> str: ...

def whole_program_fingerprint(program: TypedProgram) -> str: ...
```

`authenticate_crt_metal_sine` returns no proof and mutates nothing. A failure
is a `ValueError` prefixed with `crt-metal-sine-v1:`. The two boundary callers
translate it to their existing `GeneratorError` or `TypedEmissionError`.

### 3.2 Frozen constants

The module owns these locks:

```text
RAW_SOURCE_BYTES = 19560
RAW_SOURCE_SHA256 = 62d915eda8e20a458b1df91198cee3e85f0f0b9676cd4d0777264e9cd8b99b7c
NORMALIZED_SOURCE_SHA256 = acd1c3f05c6d02052592aeb46bbbc49d23e18f4e83530498687903e00b4623fe
INTERFACE_SHA256 = 9336d2b596c0efd955af699a27c788938c99d0e1e5c6438f66054e15fc135490
PRE_FUNCTIONS_SHA256 = f6ab50374732b058fa2a5cd33e87bbe35654682b7125593d7451871194b2ba72
PRE_WHOLE_PROGRAM_SHA256 = f70fc78da6c3579fa3237fbbfa3712229b88f0a93b8d556181f9bad2ed74b6fc
POST_FUNCTIONS_SHA256 = 1b67fa6d01135e98434bc9e6a4627f0d23565c81fa1e17cbdba10082e23e37a3
POST_WHOLE_PROGRAM_SHA256 = 7aa853a51316b1122750af1155411a5ca8c1e11cf02688a33d9ef6fcace5f6a2
```

Implement `_sha(value)` as SHA-256 of UTF-8 `repr(value)`. Implement the
interface and whole-program tuples exactly as frozen in the brief. The whole
tuple ends with `counted_loop_proof, preprocessor_defines` and deliberately
does not include the four optional Task 17-20 proof fields. Independently
require all four fields to be `None` in both apply and authenticate.

`_source_ok(program)` requires the exact key, empty `preprocessor_defines`, raw
byte length/hash, normalized source hash, and interface hash. The public
authenticator additionally requires `source_hash == RAW_SOURCE_SHA256`; a
caller-recomputed hash is never authority.

### 3.3 Site table and path grammar

Represent each site with a frozen module-local tuple containing function ID,
function name, path, span, pre-expression hash, argument hash, and
post-expression hash. Use the six rows verbatim:

| ID/name | Path | Span | Pre | Argument | Post |
| --- | --- | --- | --- | --- | --- |
| 98 `compute_lens_offsets` | `(11,"e0",0,0,0,0,1)` | `(257,37,257,47)` | `eb792d3743d971b034cad3305939edd164f35d7391b0e956e0ded09f9ab2edca` | `dfad6ec8408b05020688cf666dd8314a0d5e962d18d258ef05e4c7cbf1d17ab4` | `fee8d1478892ff364e1f2222fbe484ec9c2821fde88981ac3411c7f460b0c991` |
| 105 `hash3` | `(2,"e0",0,0,0,0)` | `(278,18,278,32)` | `ec1ed0047c1fb4fd715375e00874a32e8f9e41ab9f74a3bac5ea23b3f1983150` | `ba9137a74af006428cd1b19f03d169de8b0889ff1d4aa38dd775e9f85f389ad5` | `7b805551b3f93876e1bd5ecf76a76efea15276160a8aa7bad7a570ba5da70457` |
| 111 `normalized_sine` | `(0,"e0",0,0,0,0)` | `(61,12,61,22)` | `06d6918e656846d23db8b766f298e3158cc09f466cead68bbdb792a95157ffeb` | `f77149906598a9a158df24b332c186f1cb526dacbfe87bad03262af0a6def1ab` | `37e92090742c393c51e58b0e243ed94b7c496d81713c72f50a81965ab65d0906` |
| 114 `random_scalar` | `(0,"e0",0,0,0,0)` | `(32,18,32,27)` | `42946f9e07f8dbde14695fd889212e33322f6b0b21073f150c104dbdae0207dc` | `1625e24c6a465e2a1aff50c738539bf101926b078a4a14e617d12daa25efd07b` | `ebf5806ccb5844082b4824ae98be478a0ccbbedcc446d11e1f782a05a5259fb7` |
| 118 `simplex_random` | `(2,"e0",0,0,0,0)` | `(38,15,38,25)` | `528dcb92903e79bdc9b9c3fa9da9d798ff560617e6bfc10d3c0eea8cd3a840fb` | `385a6b97e9699eb5c2a7b2a2dd223de9794d92452b1ab6061f3bf8e53f8662a0` | `d86ca37ad7e92a214a0aa669208b860c8c2691623ef830abe7275b6f83a99034` |
| 118 `simplex_random` | `(3,"e0",0,0,0,0)` | `(39,18,39,44)` | `ee17c06d50c446e45ea053d72191298f632721fe4daa3a01aad593095bf78367` | `3c38672a718c912c5748397deb0abcf049c36dd979e9ca9a164f7437d5e2a6d9` | `13a34f969f04eca11820a7aadee45a56f11e5ae369dfac59e02cb88e78673746` |

Define the path grammar, rather than relying on incidental recursive-search
order: the first integer selects `function.body[index]`; `"eN"` selects that
statement's `expressions[N]`; the following required `0` is the expression-root
sentinel; remaining integers select successive `TypedExpression.children`.
Nested statement descent, if ever encountered, must be encoded and rejected
unless it equals one of the six frozen paths. This reconciles the brief's paths
with the ordinary walker, which otherwise omits the root sentinel.

Before rewrite, enumerate every builtin named `sin` across every function and
require its complete `(function ID/name, path, span, pre hash, argument hash)`
multiset to equal the six-site table in table order. Each must be kind
`builtin`, callee `sin`, signature `-40`, scalar `FLOAT`, category `rvalue`,
and have exactly one child. Require five arguments to be direct identifiers.
Require the sixth to be exactly the authenticated pure
`z*157.0 + w*113.0` binary tree. Reject any call, builtin, assignment, post or
unary update, lvalue write, index, fetch, or additional node in an argument.
Do not match `cos`; the four existing cosine sites remain untouched through
the whole/function locks. Pin them independently because a sine-only site
census does not prove that cosine was left alone. Raw-source lines are one
greater than normalized typed-source lines for these sites:

| ID/name | Raw line | Normalized typed span | Pre/post expression SHA-256 | Argument SHA-256 |
| --- | ---: | --- | --- | --- |
| 118 `simplex_random` | 38 | `37:15-37:25` | `d73adbb7e0f3b9c5cb4eb121ac454f08d16cd19bb651b9b3bfb6ddf352fae17a` | `a07aef30bd37a38aa61216b37a41d239fb2e4c15d11c8e482e4d375443773048` |
| 91 `animated_simplex_value` | 199 | `198:20-198:30` | `aa8a39a243601c48cdaa3b328c2aeb5ee045908c55f154e1c7ba69058d29966e` | `c2f34dcdc8a5568dc56401f25a5efa331f0e8249102791bbc31b6c53c496fa6c` |
| 98 `compute_lens_offsets` | 258 | `257:25-257:35` | `9c88ea057347d9c9f968a43c5b9d0a289a689cf6166b8f19a8c7ff1586e64bd9` | `f5411ea9b54ceb2177a5dad5b00aa01be5ee2b51b3de5fd31b4c200981ea4169` |
| 94 `blend_cosine` | 330 | `329:27-329:44` | `f9a0165495911c862940e37195b8d97eba9709c3b6e42ce42b5822e4f152c95d` | `12f0dd4d11b4959aa15e80b6e3448aad888cc6252076d53195c0def86d51d240` |

Every row is kind `builtin`, callee `cos`, signature `-8`, scalar `FLOAT`,
category `rvalue`, with one child. Pre and post expression hashes and argument
object identities are equal. Require the exact four-row set in raw and post
trees; zero, three, five, a changed site, or a transformed cosine rejects.

### 3.4 Exact rewrite constructor

For each original outer `site`, retain `arg = site.children[0]` by Python
object identity and use `span = site.span` for every injected node:

```python
inv_tau = TypedExpression(
    "literal", FLOAT, span, "rvalue",
    literal="0.15915493667125702",
    literal_value=0.15915493667125702)
scaled = TypedExpression(
    "binary", FLOAT, span, "rvalue",
    children=(arg, inv_tau), operator="*")
turns = TypedExpression(
    "construct", FLOAT, span, "rvalue",
    children=(scaled,), constructor_type=FLOAT)
wrapped = TypedExpression(
    "builtin", FLOAT, span, "rvalue",
    signature_id=-17, children=(turns,), callee="floor")
phase = TypedExpression(
    "binary", FLOAT, span, "rvalue",
    children=(turns, wrapped), operator="-")
tau = TypedExpression(
    "literal", FLOAT, span, "rvalue",
    literal="6.2831854820251465",
    literal_value=6.2831854820251465)
reduced = TypedExpression(
    "binary", FLOAT, span, "rvalue",
    children=(phase, tau), operator="*")
replacement = dataclasses.replace(site, children=(reduced,))
```

The same `turns` object occurs twice: `phase.children[0] is
wrapped.children[0]`. This is intentional. It duplicates evaluation in emitted
C++ while retaining a shared immutable AST node. `repr` hashes cannot detect a
clone with equal fields, so both the post authenticator and exact transform
test must perform this `is` check explicitly. Also require
`scaled.children[0] is arg` while applying.

Rewrite all six in one path-indexed walk. Preserve each untouched expression,
statement, and function object when its descendants did not change. Exactly
five functions change; the other 30 are at least dataclass-equal, preferably
object-identical. After replacement, authenticate all post sites, their DAG
identity, the post function tuple, post whole program, unchanged interface,
and empty proof fields before returning.

The five changed full-function hashes are:

| ID/name | Pre | Post |
| --- | --- | --- |
| 98 `compute_lens_offsets` | `c589ae1542160f189e9db5a125719da57ed72ae35357f3aad88a3fd452c0b66d` | `47332fcd4c91de0b794ebed756eb93e469c6d418e612e6abea0673ad93c62258` |
| 105 `hash3` | `0d2944ce4196702c0d0e35dc030866446477ae9f71aea71cb628f3d176fe301c` | `498c7c564d712125c5d86a6371fc8033ab07499b579291c7fd04eb10066cadf2` |
| 111 `normalized_sine` | `931ad72e976380fba0139d37370fc61179a088831a4ec18f6080b978e85cd39c` | `c18a96221435819ea0d4de84dd9702765f1439d0e93309146631d83291f6f5a8` |
| 114 `random_scalar` | `ee5cf37c4b4ded3fc55b076b8ad168f21ac240df34ece9e93bfdb9a0b7dda3e8` | `9af506d4fd1b6092bc8e5eb5985333598e3e4cfd6a5133c33cb762d635f0a74d` |
| 118 `simplex_random` | `f501ca9995ca26e7ffc32dec1f3d20c102fce4083bd5b03e4d9fd4d0168a468f` | `eef49ca4ef3414fc4140bd7ecfcca4d487c02a9c5416b410659d0486c3553819` |

`authenticate_crt_metal_sine` repeats the exact post-site structural walk; it
does not merely compare the two aggregate hashes. It rejects raw, partial,
duplicate, reordered, twice-transformed, span-shifted, cloned-turns,
wrong-literal, structurally changed argument, extra-sine, foreign-proof,
source, interface, or unrelated-tree drift.

Raw-to-post `arg` object identity is deliberately narrower than post-tree
authentication. During transform application, capture each of the six raw
arguments and require the corresponding generated `scaled.children[0] is
arg`; the exact transform test repeats all six checks and uses a test-local
equal-field clone as a negative control. A standalone validator or emitter
receives only the post tree and cannot reconstruct raw object provenance.
Accordingly, those boundaries require exact structural/site/hash equivalence
and shared-`turns` DAG identity, but do not claim to reject a semantically and
codegen-identical cloned argument node. Adding provenance state, a token, or a
proof field solely to make that impossible claim is forbidden.

## 4. Generator integration and exact CRT publication profile

Modify both import branches in `tools/glslcpp/generate_typed_slice.py` to
import `CRT_KEY`, `TRANSFORM as CRT_COMPATIBILITY_TRANSFORM`,
`apply_crt_metal_sine`, and `authenticate_crt_metal_sine`.

### 4.1 Compatibility registry

In `apply_compatibility_transform`, add one exact dispatch before the generic
string modes:

```python
if transform_name == CRT_COMPATIBILITY_TRANSFORM:
    try:
        return apply_crt_metal_sine(typed)
    except ValueError as error:
        raise GeneratorError(f"{typed.key}: {error}") from error
```

No other transform behavior changes.

Update `load_slice`'s exact compatibility dictionary by adding only:

```python
CRT_KEY: CRT_COMPATIBILITY_TRANSFORM
```

Keep the existing six entries byte-for-byte. Keep numeric contracts exactly
`{"filter/scatter:scatterJitter": "source-double"}`. Change the allowlist
count from 115 to 116 and require both `CRT_KEY` and `DEGAUSS_KEY` exactly
once. The sorted neighborhood is Craquelure, CRT, Degauss, Deriv. The error
should describe a CRT/Task22 publication-boundary drift, not preserve the old
assertion that CRT is absent.

### 4.2 Boundary authentication

At the start of `validate_capabilities`, adjacent to and independent of the
Sacred carrier block, add:

```text
if typed.key == CRT_KEY:
    require compatibility_transform == CRT_COMPATIBILITY_TRANSFORM
    require numeric_literal_contract == "glsl-f32"
    authenticate_crt_metal_sine(typed, source_hash)
elif compatibility_transform == CRT_COMPATIBILITY_TRANSFORM:
    reject foreign key
```

This block must execute before generic capability walking. It produces the
four-mode behavior:

| Tree | Carrier | Validator |
| --- | --- | --- |
| authentic raw | `None` | reject carrier mismatch |
| authentic raw | exact | reject post authenticator |
| authentic post | `None` | reject carrier mismatch |
| authentic post | exact | accept |

Do not turn the current-vocabulary profile into the validator's authority;
direct calls to `validate_capabilities` must be safe without generator setup.

### 4.3 `validate_current_vocabulary_crt`

Add a generator-only source/publication profile analogous to Degauss, invoked
for `CRT_KEY` after compatibility transformation and the existing proof
attachment calls, before `validate_capabilities` and emission. Its signature
is:

```python
def validate_current_vocabulary_crt(
        typed, entry: dict[str, Any], declared_defines: dict[str, int], *,
        compatibility_transform: str | None,
        numeric_literal_contract: str,
        metadata_effect: dict[str, Any]) -> None: ...
```

Freeze constants for corpus revision, `CRT_ENTRY`, `CRT_METADATA_EFFECT`,
`canonicalFactory44` and its text hash, `crtFactory`, adapter file/factory
hashes, canonical runtime hash, the pre/post/interface hashes, and PI/TAU/
INV_THREE/INV_TAU F32 words. These provenance constants are asserted by tests;
the generator must not read the external CPU repository.

The profile requires:

- the exact manifest entry: effect `filter/crt`, program `crt`, status
  `generated`, path `sources/filter/crt/crt.glsl`, 19,560 raw bytes and both
  frozen hashes, output `fragColor`, no varying, pass 0 `main`, runtime key
  `filter/crt:crt`;
- exact key, raw and normalized embedded text, `{}` defines, exact transform,
  and `glsl-f32`;
- exact metadata object, including alpha `0.5/[0,1]/zero=0`, speed `1/[0,5]`,
  seed `1/[1,100]`, identity aliases, one input and one output; `renderScale`
  is intentionally absent from public params;
- exact post authenticator success and the complete 35-function profile;
- exact declarations, resources, zero-loop proof, and all four foreign proofs
  absent;
- exact local shadow declarations by symbol identity, not spelling:
  `time@193 <- uniform time@8`, `speed@194 <- uniform speed@9`, and
  `alpha@205 <- base_sample@203.w`; local alpha is not the uniform;
- four exact main-owned level-zero `texelFetch` typed sites and no helper
  fetch; exact resource tuple and flags from the brief.

The exact post function profile is the following `(id, name, body_count,
sha256(repr(function)))` tuple. Use the observed unchanged hashes for all rows
except the five post hashes above:

```text
89 adjust_hue 5 e48700fa4c4e07b3f55826d5b45cc919ea3e3ed5c520d0fb762f388892d607d3
90 adjust_saturation 4 05d846a08395fe65bc96437ce61acb012ba42f905f8b82eed6e4c41cfc4bbe9e
91 animated_simplex_value 8 352197ac3de92c0139a70f84075bf77cbf585cdbaf7920d9fd5635a4562500e7
92 apply_vignette 2 f2be0a5b59234e10cb6403d7fa881740929c6a120bba24f54cfabf0364d3eff3
93 as_u32 1 52db13ad3a1814e7408c7afb86ea6b875af0b89ec4cefbaf9b6078ba7b70cd6f
94 blend_cosine 3 4dba47b2ab19f66ba1c2e7cb7824e93951ead432702e77ac44e1375d771a6860
95 blend_linear 1 3c55bf9e312fceaa81ee58684251eb71e53dd972b51ea28c2ead7e65f40d6b2c
96 clamp01 1 5d20dd2c183bed0c13746cb3ca3b1340aeeefb280a82223bb73e9df82393a7fb
97 clamp_index 3 f180eb54bf36b9bda58df0be4f5520ec321af37952ffc3372fdd075ed8ac22cf
98 compute_lens_offsets 13 47332fcd4c91de0b794ebed756eb93e469c6d418e612e6abea0673ad93c62258
99 compute_singularity 5 51d8463de86bad652cedd483550364be941996653ce3417113620f45bad04c31
100 fade 1 e292a88053f33c4eadd9bfbe7ede0df78a45922f4f10134574beed4ff119714f
101 fade_vec3 1 649a934deb2e66089979eadcc97ff9732e0c3617c505707d07f72cdcbacc6cf8
102 freq_for_shape 7 dad7778bd028bfb3f898099751b2337e45f8254b79f2dede38e8d1fd0a660448
103 get_scanline_base_values 5 f172e85e6ba08b699b6753cda6e6b1d3a82591c88f7266efd94e22e6a46ac072
104 get_scanline_value_interpolated 3 1f3f67102c445c517df6e5f0f6e3ac2865cc5a0bad6dfbe24477664c61535667
105 hash3 3 498c7c564d712125c5d86a6371fc8033ab07499b579291c7fd04eb10066cadf2
106 hsv_to_rgb 15 43873d4b1e9fa8682543ecb3f4f562c747b49beeae64fbe5e281ec9d6bb98cb0
107 lerp 1 9d9ecb55ef978a8f50aa2664d1e753245d279ce25810b674f7e4ee1d32714f98
108 main 31 da62c05d1a013b993bcf4820fd84fb4b7eee640e30fa8df4c226d717fd4fb1e2
109 mod289_vec3 1 9eef4a5ee9d393857c69b44f28b32f697ba7adf253d8d2bbfcfe08554b3a03b3
110 mod289_vec4 1 2eadd7753b5e226b3c7e18c91462fb0b56c641203c8e1cafdca9b08a36485fb0
111 normalized_sine 1 c18a96221435819ea0d4de84dd9702765f1439d0e93309146631d83291f6f5a8
112 periodic_value 1 8869f721c8c67579e0a669f21dea07cec5352a3a053c6ba28edb655e2522ab52
113 permute 1 bd33a4e74b18f065bbf132ed4c6d40c137e29fe246ae8577f17bb552c35a0f98
114 random_scalar 1 9af506d4fd1b6092bc8e5eb5985333598e3e4cfd6a5133c33cb762d635f0a74d
115 rgb_to_hsv 7 7fddfbe7b05e204b136e5a18150cda42252fc39d9b762f00df8fdb05902a9f47
116 sample_scanline_bilinear 19 37225bab20e4eca1744dd30dd529de0c5930613d4c7073b354c49abfbc99fcd4
117 simplex_noise 46 c6fb1af5432cf0cbbf4e2812dca9b1d0935aa4532d23c70a0cf545d4d988a8b5
118 simplex_random 4 eef49ca4ef3414fc4140bd7ecfcca4d487c02a9c5416b410659d0486c3553819
119 singularity_mask 9 95b752c42a2327d3a4acc983892aaf9ed8a8c651fcc69b34f87d51023dd128e9
120 taylor_inv_sqrt 1 e04f914557a482d00efaa82d837e3357aeab07514b8aabecf2ca8ad60ad96ab1
121 value_noise_3d 19 2cc121f41b402b9c6594f6b02d9fa481ce61ba8573031426aee848f0af5933b1
122 wrap_float 4 06faad9ae9e7d10ebe30997326fb11ebd0d4a3a77e5358ae750aab25ec2ad8a2
123 wrap_unit 3 7b081cf2d2412e6c5fe636f06acdb6c47028c38965553c3b606e30a6602f3ef8
```

Declarations are exactly PI/TAU/INV_THREE constants at IDs 1-3, uniforms
`inputTex,resolution,tileOffset,fullResolution,time,speed,seed,alpha,renderScale`
at IDs 4-12, and writable output `fragColor@88`. Preserve the source literal
spellings `3.14159265358979323846`, `6.28318530717958647692`, and
`0.3333333333333333`; assert their F32 words `0x40490fdb`, `0x40c90fdb`, and
`0x3eaaaaab`. The injected INV_TAU word is `0x3e22f983`.

## 5. Direct emitter boundary

Modify only imports and `_Emitter.__post_init__` in
`tools/glslcpp/emit_typed_cpp.py`. Import the CRT key, transform, and
authenticator. Immediately after the existing body/numeric checks and beside
the Sacred block:

```text
if program.key == CRT_KEY:
    require compatibility_transform == CRT_COMPATIBILITY_TRANSFORM
    require numeric_literal_contract == "glsl-f32"
    authenticate_crt_metal_sine(program, source_hash)
elif compatibility_transform == CRT_COMPATIBILITY_TRANSFORM:
    reject foreign key
```

Translate the authenticator `ValueError` with `_error`, retaining source
location formatting. Do not change expression emission, `_BUILTIN_NAMES`,
literal rendering, `glsl::sin`, `glsl::floor`, function rendering, State,
bindings, or catalog code. The direct emitter must reproduce the same
four-mode matrix as the validator without depending on a validator side
effect.

## 6. Slice and generated carriers

In `tools/glslcpp/typed_slice.json`:

- add exactly `"filter/crt:crt": "crt-metal-sine-v1"` to the exact
  compatibility map;
- insert exactly `{"defines": {}, "program_key": "filter/crt:crt"}` between
  Craquelure and Degauss;
- change nothing else.

The generated manifest entry must be exactly one record with key/source/hash,
factory `bind_filter_crt_crt`, transform `crt-metal-sine-v1`, numeric contract
`glsl-f32`, define contract `none`, defines `{}`, and unchanged capability
list. The generated namespace is `typed_19`; Degauss and later namespaces
shift by one.

The isolated exact CRT block, starting at its `// Typed IR program:` marker and
rendered with namespace `typed_19`, is 56,865 bytes and has SHA-256
`c2cad7e88fb817c311abb0041fec98d14c28ae3c3bd731b67944c745b8c295ec`.
After replacing only `typed_[0-9]+` with `typed_SENTINEL`, its digest is
`36410c4f25e2a0d53bba3bdc7164c18f74cc7f06de8f7589186da182b7246922`.
If the preflight emitter hash was exact and these fail, stop; do not update the
locks.

Generate through only:

```sh
python3 tools/glslcpp/generate_typed_slice.py --check   # expected RED drift
python3 tools/glslcpp/generate_typed_slice.py --write
python3 tools/glslcpp/generate_typed_slice.py --check   # required GREEN
```

## 7. Python TDD design

Add the five required focused test methods to `TypedGeneratorTests` before
implementation. Use exact AST mutation helpers that assert one intended
replacement; source-string mutation is not sufficient.

### 7.1 `test_task22_crt_transform_is_exact`

Parse/analyze raw CRT from the pinned corpus and assert all pre locks. Apply
the transform and assert:

- all source/interface/function/whole locks and the full ordered 35-function
  profile;
- exactly six sites and exact site table order;
- every outer field equals its pre-site field except `children`;
- exact literal strings, Python values, types, categories, spans, constructor
  type, floor signature/callee, and operator grouping;
- retained raw-to-post `arg` object identity at transform application, a
  test-local equal-field clone negative control, and shared `turns` object
  identity in the post tree;
- exactly IDs 98,105,111,114,118 change, with the other 30 functions
  dataclass-equal;
- exactly six post outer `sin`, the four original `cos` matching the frozen
  identity/hash table and retaining their argument objects, and no helper/new
  builtin;
- applying again, applying a partial tree, or applying with a foreign proof
  raises `ValueError`;
- the post authenticator accepts only the exact post tree and pinned source
  hash.

Observe RED as an unknown transform/module before adding production code.

### 7.2 `test_task22_crt_four_mode_forgery_matrix`

Build raw and exact post once. Define two independent boundary calls:

```text
validator := validate_capabilities(candidate, APPROVED_CAPABILITIES,
    source_hash=hash_arg, compatibility_transform=carrier,
    numeric_literal_contract=numeric)
emitter := render_typed_cpp(candidate, candidate.key, hash_arg,
    numeric_literal_contract=numeric, compatibility_transform=carrier)
```

Assert baseline modes 1-4 at both calls. Then run raw-state and post-state
mutation tables through the exact-carrier modes. For every candidate, run once
with the authentic pinned source-hash argument and once with
`sha256(candidate.raw_source)`; neither may rescue it.

The mutation table must cover at least:

- wrong key/raw/normalized text/defines; function reorder, ID/name/signature,
  body count, span, interface/declaration/resource/loop proof; each foreign
  proof field;
- missing/duplicate/seventh/partial/already/twice-transformed sites and each
  of six function/path/span/pre/argument/post locks;
- INV_TAU and TAU spelling/value/type/category/span, construct kind/type/
  constructor type, floor kind/signature/callee/order, all three operators and
  grouping, outer sin fields, cloned rather than shared turns, structurally
  changed argument, impure compound argument, and an unrelated node in each
  of the 30 unchanged functions. Raw-to-post argument identity is tested at
  transform application and is not asserted as a post-only boundary property;
- carrier `None`, `"none"`, wrong string, Sacred transform, exact CRT carrier
  on a foreign key, and numeric `None`/`source-double`/wrong string.

For structural mutations, assert the helper matched exactly one node. The
post aggregate hash catches unrelated changes; explicit site checks catch DAG
identity and exact local structure.

### 7.3 `test_task22_crt_profile_rejects_identity_interface_and_tree_drift`

Exercise `validate_current_vocabulary_crt` with every `CRT_ENTRY` field
changed one at a time, wrong corpus/runtime/factory provenance constant
expectations, nonempty defines, transform/numeric drift, and deep-copied
metadata mutations for every param default/range/zero/alias and pass route.
Mutate declarations/constants/F32 words, each local shadow source, local alpha
use, output alpha route, resources, fetch owner/count/LOD, function order/hash,
and loop proof. Prove generic current-vocabulary validation would accept a
representative semantic mutation while the exact CRT profile rejects it.

### 7.4 `test_task22_adds_only_exact_transform_no_capability_proof_or_numeric_mode`

Assert accepted Task21 capability/type/operator/assignment/builtin tuples are
unchanged. Assert the numeric map is still the one Scatter exception. Assert
the compatibility map equals the previous six exact entries plus only CRT.
Assert raw/post CRT carry no Task17-20 proof and no new typed field. Assert
emitter `_BUILTIN_NAMES`, runtime files, and relevant accepted hashes outside
owned files are unchanged by the implementation evidence.

### 7.5 `test_task22_crt_exclusions_remain_closed`

Assert exact sorted 116 typed keys and explicit exact 118 public keys, not only
counts. Assert SHA-256 of newline-terminated lists:

```text
typed:  76c81945ef992ed258900815335a23ae4f36d8756b7763ebd5e03d8562fde8e3
public: 019a80df52192e3c898af58a5e3a2a9da654896eadde78097ce4a818579328f9
```

Assert 116/118/94/212, CRT exactly once, Degauss exactly once, sorted
Craquelure/CRT/Degauss/Deriv neighborhood, and all 94 remaining corpus keys
absent. Mutated slice tests reject missing/duplicate CRT, another admitted key,
foreign CRT transform assignment, extra transform entry, schema/key shape
drift, and manifest carrier disagreement.

### 7.6 Deterministic generation and isolation

Extend deterministic-CWD and transactional output tests naturally; do not
weaken their owned-tree rules. For isolation:

1. split the accepted Task21 baseline and Task22 output only at
   `^// Typed IR program: (.+)$`;
2. require raw equality for all 19 pre-CRT blocks;
3. require all 115 prior keys to match after replacing only
   `typed_[0-9]+` with a fixed sentinel;
4. do not normalize whitespace, comments, literals, factories, keys, or code;
5. additionally generate an in-memory no-CRT slice by patching `load_slice`,
   as Task21's isolation test did, and apply the same comparisons;
6. require the CRT block size/hash, manifest fields, generated catalog entry,
   and absence of generated C++ `main`.

Brace-extract `pixel`, `compute_lens_offsets`, `hash3`, `normalized_sine`,
`random_scalar`, `simplex_random`, `animated_simplex_value`, and
`blend_cosine`. Across the five transformed functions, require exactly six
`glsl::sin` calls, two occurrences of the INV_TAU literal per site, one TAU
literal per site, and the paired float/floor reduced-turn shape. Across the
complete CRT namespace require exactly four `glsl::cos` calls, located in the
four frozen functions with no reduced-turn wrapper or other change. Require
four static `fetch_texel` calls in `pixel`, none in helpers, and exact helper
routing. Scope forbidden-allocation scans to the CRT namespace.

## 8. Binding and catalog native tests

In `tests/test_generated_kernels.cpp`, add
`typed_task22_crt_binding_abi_is_exact`, using the established Degauss helper
pattern. The exact required names/types are:

| Binding | Type |
| --- | --- |
| `inputTex` | texture |
| `resolution` | `Vec2` |
| `tileOffset` | `Vec2` |
| `fullResolution` | `Vec2` |
| `time` | number/double binding |
| `speed` | number/double binding |
| `seed` | `int32_t` |
| `alpha` | number/double binding |
| `renderScale` | number/double binding |

For each of nine names, omit it once and provide a wrong alternative type
once; both must throw `KernelBindingError`. Exact bindings produce a non-null
pixel. Add unrelated uniform and texture entries and require success. There is
no binding for PI, TAU, INV_THREE, or `fragColor`.

Rename/update the catalog test to 118 entries and paste the full explicit list
with CRT between Craquelure and Degauss. Assert sortedness, uniqueness, one
CRT, one invert, one solid, direct CRT factory declaration, dispatch success
with exact bindings, and rejection of a still-unported adjacent key. Remove
only the old assertion that CRT dispatch is absent.

## 9. Native public-adapter oracle test

In `tests/test_typed_slice.cpp`, add a `Task22Case` and one test named
`typed_task22_crt_public_adapter_oracles_are_exact_repeatable_and_nonmutating`.
Mirror the Task21 F32 input and validation machinery, with seven probes per
case (`std::array<uint32_t,42>`: x, y, four lane words). Do not assume eight
probes; the frozen CRT JSON has seven.

`task22_input(width,height)` computes each lane through an explicit float
boundary:

```text
R=((17*x+31*y+13)%101)/100
G=((7*x+19*y+23)%97)/96
B=((29*x+11*y+5)%89)/88
A=(((5*x+7*y+3)%23)-5)/12
```

`render_task22` binds the nine exact values, calls
`bind_filter_crt_crt`, and passes the fixture dimensions plus time, runtime
seed `29.0f` (`0x41e80000`), frame 17, and delta `0x3c888889` to `run_pass`.
Use top-down storage coordinates exactly as the JSON records them.

Mechanically transcribe all 11 cases from
`docs/port-engineering/task-22-oracles.json`; do not derive expected
native output from repository code. The required output hashes are:

| Case | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- |
| alpha-zero-exact-copy-tiled | `daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687` | `5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3` |
| alpha-negative-clamps-zero-copy | `5036ac34df07a6e89f8ae9cd5ee4fa3250a1962bdbda6bc4e29dc4ce512fb8a8` | `6b56cc6c2f780b54a655f04ba7deae8e61e8330ca84b5d5056e8c352dd16885c` |
| default-landscape-untiled | `3134189c0654121a560abf3f8f102873b3395937ae244eaf1d6de7d03e6c8192` | `c9a7375db6ae12c5dc1f0b2fa49669892d405c55ab587cc0a054d75d9d66eeb9` |
| alpha-above-one-clamps-and-preserves-input-alpha | `e6d5a0788f2a23100ee9968186ac1f1a05175ecf6972e8503bd92cd8130a4bfd` | `b971437eec882ffd958b151216992caad58a8a681211f161ec60480820d52fee` |
| landscape-tiled-render-scale-two | `7e9a4e738ad67051674ea5d8e7e2333585e943bbe45fcdbdf3c9e59635c359ec` | `2ed1841d5be9df1f576fecf81bab403ad848fb96d4e33055525a1520e905d75c` |
| portrait-tiled-fractional-render-scale | `cdc080912dc354a6052447427814040e552d7c38edf4e1c499d8f7c80bd196be` | `ecfb38a778ba9e40d9bacfb5a8f1f62a810cd929d14b83c2bf5d4abc6bc0d079` |
| speed-zero-nonzero-time | `f83304619eda688e29c3ae34b4c913535919c3505c2f59f5100b587ddf52ddd8` | `16727fe42c77a453e47d0dcfcc14b079b39a84d06683ac8d0f689749611ec70e` |
| time-zero-positive-speed | `bc5ed1803bb52ee4d075d4c9ff6e5cc62ca2ba6f60f7d5aed93d1c237ad81b98` | `59a3fef349d5457d514174dba0e328bcd1723f97d0d8fdf82649ed217265f5d0` |
| full-resolution-zero-fallback | `19b91bedac3685b2c368a1c8da9eb89ae6e57e8deeee513b4151cf12dad3896f` | `fc49c1f7a2ea1c69db968ceabfaa4293ba8b193e13a5634b51ef763d0fea50d6` |
| square-large-time-max-metadata | `5169bfe5072efd935eafd52f13b413c7b4f5f9834e9991f5a6207a877a6bfc48` | `3a0f86f1aac14e290bbc2d22675f4af5bfa1a08fc68cbfc59c92331f5daf59a5` |
| render-scale-below-one-clamps | `d963390a996552ce28b3f8f5c7b7971072a60566ebad0bf29beb329fa4a24de2` | `65e933fe048522db9d4b8eae08057c6ca56f3d4b53510181fb2e288f25546716` |

For every fixture assert input and output F32/RGBA8 hashes, all seven output
probe coordinate/word records, exact metric fields from JSON, all lanes finite,
input bytes unchanged after each render, and two fresh renders byte-identical
in both formats. The first two cases must be exact full-F32 copies. The nine
normal cases must change all pixels in RGB while preserving every alpha bit,
including alpha outside `[0,1]`. The asymmetric copy/probe cases lock top-down
storage and bottom-left shader orientation.

The 18 factory mutation experiments remain owned by the frozen MJS generator:
run its `--check` before the native test, after native edits, and at final
acceptance. Native C++ consumes only the 11 canonical records. Do not add a
runtime dependency on the JSON or CPU repository. Acceptance explicitly checks
that `public-metal-sine-disabled` changes all nine normal cases but neither copy
case; eager-local-mean F32 changes nine F32 cases and zero RGBA8 cases; and the
renderScale/fullResolution branch mutations each change only the one dedicated
case and match all ten controls, directly from the JSON's full per-case lists.

## 10. Ordered RED/GREEN execution

1. **Preflight gate:** authenticate every artifact, baseline hash, count, and
   check in section 1. Save generated baselines outside the repo.
2. **RED transform gate:** add the five focused Python tests and observe the
   missing module/unknown transform/absent CRT failures. Do not add native
   expectations yet if they obscure the transform RED.
3. **GREEN compatibility gate:** add only `crt_compatibility.py`, generator
   imports/dispatch/profile/boundary, and emitter boundary. Run the five
   focused tests against in-memory raw/post CRT, before slice admission.
4. **Slice/generation gate:** insert the single slice entry/map carrier. Run
   generator `--check` to see exactly three generated files drift, then
   `--write` and `--check`. Verify CRT block locks and manifest carrier.
5. **Isolation gate:** compare saved Task21 output to Task22 output exactly as
   section 7.6 specifies. Stop on any non-ordinal prior-block drift.
6. **Bindings/catalog gate:** add exact CRT binding test and explicit 118-key
   catalog. Run targeted generated-kernel tests.
7. **Native oracle gate:** mechanically add all 11 records/probes/metrics.
   Run Debug and Release exact F32/RGBA8 tests and the frozen MJS `--check`.
8. **Full acceptance gate:** run all commands and inspections below; record
   final before/after hashes and unrelated-file identity.

## 11. Full verification and bounded stack/code-shape proof

Run the five focused tests exactly as listed in the brief, then full Python,
corpus, generator, and all accepted Task15-21 oracle commands from their
reports. Configure fresh Debug, Release, and sanitize directories with
`-ffp-contract=off` and stack usage flags.

Attempt the brief's Ninja commands first. If and only if Ninja is still absent
in the same environment, record that fact and use fresh Unix Makefiles build
directories with identical build type and compiler/linker flags. Do not reuse
an old configure. On Apple platforms, first try
`ASAN_OPTIONS=detect_leaks=1`; if the runtime reports leak detection unsupported,
record that diagnostic and rerun only with `detect_leaks=0`. Any actual ASan or
UBSan finding fails.

Extract the CRT namespace with the brief's exact `awk`, then require:

- one namespace and nonempty extraction;
- exact six reduced-turn `glsl::sin` routes and no raw site;
- four static pixel fetch calls, LOD zero, none in helpers;
- no generated `main`, helper/runtime sine, allocation, container, callback,
  exception, indirect dispatch, recursion, or dynamic stack route;
- exact red/blue coordinate order and raw-versus-clamped renderScale use;
- `-ffp-contract=off` in all configurations.

Preserve `.su` records for `pixel` and every reachable helper. Calculate and
report static frame sizes and maximum non-inlined chain sums for at least:

```text
pixel -> compute_lens_offsets -> animated_simplex_value
      -> simplex_noise -> permute -> mod289_vec4

pixel -> get_scanline_base_values -> value_noise_3d -> fade_vec3 -> fade
```

Use Release disassembly (`llvm-objdump -d` or `otool -tvV`) to resolve inlined
or missing `.su` entries and prove no allocator or indirect call and presence
of reduced-turn float/floor/sine calculations. Dynamic execution must show a
maximum of one fetch on copy paths and three on normal paths; static generated
pixel has four sites. Binder State allocation is outside the per-pixel
namespace and is not misclassified.

Finally run:

```sh
node docs/port-engineering/task-22-oracle-generator.mjs --check
python3 tools/glslcpp/check_corpus.py --check
python3 tools/glslcpp/generate_typed_slice.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
ctest --test-dir /tmp/noisemaker-task22-debug --output-on-failure
ctest --test-dir /tmp/noisemaker-task22-release --output-on-failure
ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=1 \
  ctest --test-dir /tmp/noisemaker-task22-sanitize --output-on-failure
```

Record exact final hashes of all ten owned/generated paths, counts
116/118/94/212, zero failed tests, prior-oracle results, catalog digests,
generated isolation, CRT block digests, stack/disassembly/fetch evidence, and
an exact list of changed paths. Stop after Task 22. No Git operation or next
port is part of this design.
