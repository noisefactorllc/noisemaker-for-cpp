#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const here = path.dirname(fileURLToPath(import.meta.url));
const rootRepo = fs.realpathSync(path.resolve(here, "..", "..", ".."));
const out = path.join(here, "effects188-oracles.json");
const report = path.join(here, "effects188-oracle-report.md");
const generatorPath = fileURLToPath(import.meta.url);
const materializerPath = path.join(rootRepo, "tools/glslcpp/generate_effects_native_oracle_include.py");
const expectedIncludePath = path.join(rootRepo, "tests/oracles/effects188_expected.inc");
const key = "classicNoisedeck/effects:effects",
  effectKey = "classicNoisedeck/effects",
  rev = "a024dc3a960cc44af454abc7aebce50456c194e6",
  srcRel =
    "tools/glslcpp/corpus/" +
    rev +
    "/sources/classicNoisedeck/effects/effects.glsl",
  srcSha = "e3b742be53b6b1b0dd5e089a805ff02a931cd14643d0a0abe376bd8044e8ec6c",
  factoryName = "canonicalFactory7",
  nextFactory = "canonicalFactory8",
  factorySha =
    "ebf43ff45f4a3568854da02b41baf6b1a25efd2bc5bbf2d8cf78f0a11e3dd81a";
const names = [
    "inputTex",
    "resolution",
    "tileOffset",
    "fullResolution",
    "renderScale",
    "time",
    "effectAmt",
    "scaleAmt",
    "rotation",
    "offsetX",
    "offsetY",
    "intensity",
    "saturation",
  ],
  abi = {
    inputTex: "sampler2D",
    resolution: "Vec2",
    tileOffset: "Vec2",
    fullResolution: "Vec2",
    renderScale: "number",
    time: "number",
    effectAmt: "number",
    scaleAmt: "number",
    rotation: "number",
    offsetX: "number",
    offsetY: "number",
    intensity: "number",
    saturation: "number",
  };
const files = {
  canonical_kernels: [
    "src/effects/generated/canonical-kernels.js",
    "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe",
  ],
  public_catalog: [
    "src/effects/catalog.js",
    "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4",
  ],
  glsl_kernel: [
    "src/csl/glsl-kernel.js",
    "a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa",
  ],
  glsl_runtime: [
    "src/csl/glsl-runtime.js",
    "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072",
  ],
  pass_runner: [
    "src/runtime/pass-runner.js",
    "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa",
  ],
  surface: [
    "src/runtime/surface.js",
    "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59",
  ],
};
const closureExpected = {
  "src/csl/glsl-kernel.js": "a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa",
  "src/csl/glsl-runtime.js": "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072",
  "src/csl/runtime.js": "a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee",
  "src/effects/adapters/bit-effects.js": "5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7",
  "src/effects/adapters/crt.js": "c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc",
  "src/effects/adapters/f32-color.js": "b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046",
  "src/effects/adapters/fractal.js": "0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29",
  "src/effects/adapters/index.js": "40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267",
  "src/effects/adapters/julia.js": "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5",
  "src/effects/adapters/median.js": "e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583",
  "src/effects/adapters/palette.js": "8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452",
  "src/effects/adapters/snow.js": "202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366",
  "src/effects/catalog.js": "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4",
  "src/effects/definition.js": "fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02",
  "src/effects/generated/canonical-adapter-data.js": "ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab",
  "src/effects/generated/canonical-kernels.js": "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe",
  "src/effects/generated/kernels.js": "b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01",
  "src/effects/generated/upstream-snapshot.js": "e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090",
  "src/effects/registry.js": "8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618",
  "src/runtime/pass-runner.js": "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa",
  "src/runtime/sampler.js": "1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328",
  "src/runtime/surface.js": "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59",
};
const tables = {
  emboss: [-2, -1, 0, -1, 1, 1, 0, 1, 2],
  sharpen: [-1, 0, -1, 0, 5, 0, -1, 0, -1],
  blur: [1, 2, 1, 2, 4, 2, 1, 2, 1],
  edge: [-1, -1, -1, -1, 8, -1, -1, -1, -1],
  edge2: [-1, 0, -1, 0, 4, 0, -1, 0, -1],
  edge3: [-0.875, -0.75, -0.875, -0.75, 5, -0.75, -0.875, -0.75, -0.875],
  sharpenBlur: [-2, 2, -2, 2, 1, 2, -2, 2, -2],
};
const tableNames = Object.keys(tables);
const F = Math.fround,
  sha = (x) => crypto.createHash("sha256").update(x).digest("hex"),
  bytes = (x) => Buffer.from(x.buffer, x.byteOffset, x.byteLength),
  words = (x) => new Uint32Array(x.buffer, x.byteOffset, x.length),
  hex = (x) => "0x" + (x >>> 0).toString(16).padStart(8, "0"),
  bits = (x) => hex(words(new Float32Array([x]))[0]),
  side = (x) => x + ".sha256",
  sideText = (x, b) => sha(b) + "  " + path.basename(x) + "\n";
const av = process.argv.slice(2),
  write = av.includes("--write"),
  check = av.includes("--check"),
  self = av.includes("--self-test"),
  ix = av.indexOf("--cpu-root");
if ([write, check, self].filter(Boolean).length !== 1 || ix < 0)
  throw Error("usage: --write|--check|--self-test --cpu-root ROOT");
const arg = av[ix + 1];
const cpu = fs.realpathSync(arg);
const liveArg =
  process.env.NOISEMAKER_FOR_CPU ||
  (process.env.HOME &&
    path.join(process.env.HOME, "platform/noisemaker-for-cpu"));
if (!liveArg) throw Error("live checkout unresolved");
const live = fs.existsSync(liveArg) ? fs.realpathSync(liveArg) : null,
  beneath = (a, b) => b === a || b.startsWith(a + path.sep);
if (live && (cpu === live || beneath(live, cpu) || beneath(cpu, live)))
  throw Error("live checkout rejected");
if (beneath(rootRepo, cpu)) throw Error("snapshot inside C++ repo");
const conf = (p) => {
  const r = fs.realpathSync(p);
  if (!beneath(cpu, r) || (live && beneath(live, r)))
    throw Error("import escaped snapshot");
  return r;
};
const load = (r) => import(pathToFileURL(conf(path.join(cpu, r))).href);
function collectClosure() {
  const entries = [
    "src/effects/catalog.js",
    "src/effects/generated/upstream-snapshot.js",
    "src/csl/glsl-kernel.js",
    "src/csl/glsl-runtime.js",
    "src/runtime/pass-runner.js",
    "src/runtime/surface.js",
  ];
  const stack = [...entries], seen = new Map();
  const pattern = /\bfrom\s*["']([^"']+)["']|\bimport\s*\(\s*["']([^"']+)["']\)|^[ \t]*import\s+["']([^"']+)["']/gm;
  while (stack.length) {
    const relative = stack.pop();
    if (seen.has(relative)) continue;
    const absolute = conf(path.join(cpu, relative));
    const payload = fs.readFileSync(absolute);
    seen.set(relative, sha(payload));
    const sourceText = payload.toString("utf8");
    let match;
    pattern.lastIndex = 0;
    while ((match = pattern.exec(sourceText)) !== null) {
      const specifier = match[1] || match[2] || match[3];
      if (specifier && (specifier.startsWith("./") || specifier.startsWith("../"))) {
        stack.push(path.normalize(path.join(path.dirname(relative), specifier)));
      }
    }
  }
  const observed = Object.fromEntries([...seen.entries()].sort());
  if (JSON.stringify(observed) !== JSON.stringify(closureExpected)) throw Error("transitive ESM closure drift");
  return Object.entries(observed).map(([relative_path, sha256]) => ({ relative_path, sha256 }));
}
const closureRecords = collectClosure();
for (const [n, [r, d]] of Object.entries(files))
  if (sha(fs.readFileSync(path.join(cpu, r))) !== d)
    throw Error(n + " provenance drift");
const { canonicalKernelFactories, kernelFactories, canonicalAdapterFactories } =
  await load("src/effects/catalog.js");
const { effectRecords, UPSTREAM_REVISION } = await load(
  "src/effects/generated/upstream-snapshot.js",
);
const { bindCanonicalKernel } = await load("src/csl/glsl-kernel.js");
const { runPass } = await load("src/runtime/pass-runner.js");
const { Surface } = await load("src/runtime/surface.js");
if (
  process.version !== "v24.7.0" ||
  UPSTREAM_REVISION !== "117a236679d1db3ab8f0e278230ece277b57564c"
)
  throw Error("authority drift");
const factory = canonicalKernelFactories[key];
if (
  typeof factory !== "function" ||
  kernelFactories.get(key) !== factory ||
  Object.hasOwn(canonicalAdapterFactories, key) ||
  factory.name !== factoryName
)
  throw Error("factory identity drift");
const text = Function.prototype.toString.call(factory);
if (sha(text) !== factorySha) throw Error("factory text drift");
const source = fs.readFileSync(
    path.join(cpu, files.canonical_kernels[0]),
    "utf8",
  ),
  a = source.indexOf("function " + factoryName),
  b = source.indexOf("function " + nextFactory, a);
if (a < 0 || b < 0 || !source.slice(a, b).startsWith(text))
  throw Error("factory slice drift");
const glsl = fs.readFileSync(path.join(rootRepo, srcRel));
if (glsl.length !== 21087 || sha(glsl) !== srcSha) throw Error("GLSL drift");
const meta = effectRecords.find((x) => x.id === effectKey);
if (
  !meta ||
  meta.func !== "effects" ||
  meta.params.effect.default !== 0 ||
  meta.params.flip.default !== 0
)
  throw Error("metadata drift");
for (const n of tableNames) {
  const d = "var " + n + " = [0, 0, 0, 0, 0, 0, 0, 0, 0];";
  if (text.split(d).length - 1 !== 1) throw Error("declaration drift " + n);
  for (const [i, v] of tables[n].entries())
    if (text.split(n + "[" + i + "] = " + v + ";").length - 1 !== 1)
      throw Error("store drift " + n);
}
if (text.split("loadKernels();").length - 1 !== 1)
  throw Error("writer call drift");
function input(w, h, t) {
  const d = new Float32Array(w * h * 4);
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4;
      d[i] = ((3 * x + 5 * y + t) % 16) / 16;
      d[i + 1] = ((x + 2 * y + t) % 8) / 8;
      d[i + 2] = ((5 * x + y + t) % 32) / 32;
      d[i + 3] = 1;
    }
  return new Surface(w, h, d);
}
const cases = [
  {
    name: "rotation-scale",
    w: 7,
    h: 5,
    t: 2,
    rotation: 45,
    scaleAmt: 75,
    coverage: "rotate2D mat2",
  },
  {
    name: "offset-arms",
    w: 6,
    h: 6,
    t: 3,
    offsetX: 40,
    offsetY: -30,
    coverage: "offset maps",
  },
  {
    name: "intensity-negative",
    w: 6,
    h: 4,
    t: 5,
    intensity: -60,
    saturation: -40,
    coverage: "negative brightness/saturation",
  },
  {
    name: "intensity-positive",
    w: 6,
    h: 4,
    t: 4,
    intensity: 60,
    saturation: 40,
    coverage: "positive brightness/saturation",
  },
  {
    name: "time-witness",
    w: 8,
    h: 5,
    t: 6,
    time: 1.25,
    coverage: "periodic offsets",
  },
  {
    name: "tile-route",
    w: 4,
    h: 3,
    t: 7,
    iw: 9,
    ih: 8,
    tile: [2, 3],
    full: [9, 8],
    coverage: "tile route",
  },
];
class KernelBindingError extends TypeError {
  constructor(binding, category, detail) {
    super("" + binding + ": " + category + (detail ? ": " + detail : ""));
    this.name = "KernelBindingError";
    this.binding = binding;
    this.category = category;
  }
}
function bindingValues(c, tex, o) {
  return {
    inputTex: tex,
    resolution: new Float32Array([c.w, c.h]),
    tileOffset: o.tileOffset,
    fullResolution: o.fullResolution,
    renderScale: o.uniforms.renderScale,
    time: o.uniforms.time,
    effectAmt: o.uniforms.effectAmt,
    scaleAmt: o.uniforms.scaleAmt,
    rotation: o.uniforms.rotation,
    offsetX: o.uniforms.offsetX,
    offsetY: o.uniforms.offsetY,
    intensity: o.uniforms.intensity,
    saturation: o.uniforms.saturation,
  };
}
function validateBindings(values, c) {
  for (const name of names) {
    if (!Object.prototype.hasOwnProperty.call(values, name)) {
      throw new KernelBindingError(name, "missing");
    }
  }
  const sampler = values.inputTex;
  if (!(sampler instanceof Surface) || sampler.width !== (c.iw || c.w) || sampler.height !== (c.ih || c.h)) {
    throw new KernelBindingError("inputTex", "sampler2D", "Surface dimensions/digest required");
  }
  for (const name of ["resolution", "tileOffset", "fullResolution"]) {
    const value = values[name];
    if (!(value instanceof Float32Array) || value.length !== 2 || [...value].some((lane) => !Number.isFinite(lane))) {
      throw new KernelBindingError(name, "Vec2", "Float32Array[2] required");
    }
  }
  for (const name of names.slice(4)) {
    const value = values[name];
    if (typeof value !== "number" || !Number.isFinite(value) || F(value) !== value) {
      throw new KernelBindingError(name, "number", "finite exact Float32 scalar required");
    }
  }
  return true;
}
function render(f, c) {
  const tex = input(c.iw || c.w, c.ih || c.h, c.t),
    o = {
      width: c.w,
      height: c.h,
      time: c.time || 0,
      seed: 1,
      tileOffset: new Float32Array(c.tile || [0, 0]),
      fullResolution: new Float32Array(c.full || [c.w, c.h]),
      textures: { inputTex: tex },
      uniforms: {
        EFFECT: 0,
        FLIP: 0,
        renderScale: 1,
        time: c.time || 0,
        effectAmt: 1,
        scaleAmt: c.scaleAmt || 100,
        rotation: c.rotation || 0,
        offsetX: c.offsetX || 0,
        offsetY: c.offsetY || 0,
        intensity: c.intensity || 0,
        saturation: c.saturation || 0,
      },
    },
    before = words(tex.data).slice(),
    outp = new Surface(c.w, c.h);
  validateBindings(bindingValues(c, tex, o), c);
  runPass({
    kernel: bindCanonicalKernel(f, o),
    destination: outp,
    time: 0,
    seed: 1,
  });
  if (before.some((x, i) => x !== words(tex.data)[i]))
    throw Error("input mutation");
  return { out: outp, tex, o };
}
function expected(s) {
  return { words: words(s.data).slice(), bytes: new Uint8Array(s.toRgba8()) };
}
function compare(s, e) {
  const w = words(s.data),
    q = s.toRgba8();
  let l = 0,
    r = 0,
    first = null;
  for (let i = 0; i < w.length; i++) {
    if (w[i] !== e.words[i]) {
      l++;
      first ||= first = {
        index: i,
        channel: ["r", "g", "b", "a"][i % 4],
        expected: hex(e.words[i]),
        actual: hex(w[i]),
      };
    }
    if (q[i] !== e.bytes[i]) r++;
  }
  return {
    exact: l === 0 && r === 0,
    changed_lane_count: l,
    changed_rgba8_byte_count: r,
    first_mismatch: first,
  };
}
function surface(s) {
  const w = words(s.data),
    q = s.toRgba8();
  for (let i = 0; i < w.length; i += 4)
    if (w[i + 3] !== 0x3f800000 || q[i + 3] !== 255) throw Error("alpha drift");
  return {
    width: s.width,
    height: s.height,
    f32_words_le: Array.from(w, hex),
    f32_sha256: sha(bytes(s.data)),
    rgba8_bytes: Array.from(q),
    rgba8_sha256: sha(bytes(q)),
    finite_lane_count: w.length,
    nonfinite_lane_count: 0,
    alpha_f32_word: "0x3f800000",
    alpha_rgba8_byte: 255,
  };
}
const expectedMap = new Map();
const renderCases = cases.map((c) => {
  const x = render(factory, c),
    r = render(factory, c),
    p = render(kernelFactories.get(key), c),
    e = expected(x.out);
  if (!compare(r.out, e).exact || !compare(p.out, e).exact)
    throw Error("identity drift");
  if (x.out.data.buffer === r.out.data.buffer || x.out.data.buffer === p.out.data.buffer || r.out.data.buffer === p.out.data.buffer)
    throw Error("output storage is not independent");
  expectedMap.set(c.name, e);
  const bind = {
    inputTex: {
      abi: "sampler2D",
      width: x.tex.width,
      height: x.tex.height,
      f32_sha256: sha(bytes(x.tex.data)),
    },
    resolution: {
      abi: "Vec2",
      f32_values: [c.w, c.h],
      f32_words_le: [bits(c.w), bits(c.h)],
    },
    tileOffset: {
      abi: "Vec2",
      f32_values: Array.from(x.o.tileOffset),
      f32_words_le: Array.from(words(x.o.tileOffset), hex),
    },
    fullResolution: {
      abi: "Vec2",
      f32_values: Array.from(x.o.fullResolution),
      f32_words_le: Array.from(words(x.o.fullResolution), hex),
    },
  };
  for (const n of names.slice(4))
    bind[n] = {
      abi: "number",
      f32_value: x.o.uniforms[n],
      f32_word_le: bits(x.o.uniforms[n]),
    };
  return {
    name: c.name,
    coverage: c.coverage,
    route: c.tile ? "tile" : "full",
    width: c.w,
    height: c.h,
    input_texture: {
      width: x.tex.width,
      height: x.tex.height,
      f32_words_le: Array.from(words(x.tex.data), hex),
      f32_sha256: sha(bytes(x.tex.data)),
      row_order: "top-down storage; GLSL texture origin bottom-left",
    },
    bindings: bind,
    output_expected: surface(x.out),
    canonical_repeat: { exact: true },
    public_canonical: { exact: true },
  };
});
const caseSpecs = cases.map((c, index) => {
  const rendered = renderCases[index];
  const b = rendered.bindings;
  return {
    name: c.name,
    coverage: c.coverage,
    route: rendered.route,
    width: c.w,
    height: c.h,
    input_width: rendered.input_texture.width,
    input_height: rendered.input_texture.height,
    t: c.t,
    seed: 1,
    tileOffset: b.tileOffset.f32_values,
    fullResolution: b.fullResolution.f32_values,
    uniforms: Object.fromEntries(names.slice(4).map((name) => [name, b[name].f32_value])),
    input_f32_sha256: rendered.input_texture.f32_sha256,
    output_f32_sha256: rendered.output_expected.f32_sha256,
    output_rgba8_sha256: rendered.output_expected.rgba8_sha256,
  };
});
const nativeBindingPreflight = names.map((name) => ({
  binding: name,
  abi: abi[name],
  expected_category: name === "inputTex" ? "Sampler2D" : abi[name] === "Vec2" ? "Vec2" : "Number",
  wrong_category: name === "inputTex" || abi[name] === "Vec2" ? "Number" : "Vec2",
  wrong_value:
    name === "inputTex" || abi[name] === "Vec2"
      ? { category: "Number", number: 1, vec2: [0, 0] }
      : { category: "Vec2", number: 0, vec2: [1, 1] },
  missing_strategy: "omit texture/uniform binding",
  wrong_strategy: name === "inputTex" ? "set_uniform_same_name_and_omit_texture" : "set_uniform_same_name",
  missing_status: "pending_shared_native_integration",
  wrong_status: "pending_shared_native_integration",
}));
const abiMatrix = abiRejectionMatrix();

function abiRejectionMatrix() {
  const definition = cases[0];
  const made = optsForAbi(definition);
  const rows = [];
  for (const name of names) {
    const omitted = { ...made.values };
    delete omitted[name];
    let omission;
    try { validateBindings(omitted, definition); omission = { accepted: true }; }
    catch (error) { omission = { accepted: false, error_name: error.name, binding: error.binding, category: error.category }; }
    if (omission.accepted || omission.binding !== name || omission.category !== "missing") throw Error("ABI omit test failed for " + name);
    const wrong = { ...made.values, [name]: wrongVariant(name, definition) };
    let variant;
    try { validateBindings(wrong, definition); variant = { accepted: true }; }
    catch (error) { variant = { accepted: false, error_name: error.name, binding: error.binding, category: error.category }; }
    if (variant.accepted || variant.binding !== name || variant.category !== abi[name]) throw Error("ABI wrong-variant test failed for " + name);
    rows.push({ binding: name, omit: omission, wrong_variant: variant });
  }
  return { harness: "generator ABI preflight", case: definition.name, rows };
}
function optsForAbi(c) {
  const tex = input(c.iw || c.w, c.ih || c.h, c.t);
  const o = {
    tileOffset: new Float32Array(c.tile || [0, 0]),
    fullResolution: new Float32Array(c.full || [c.w, c.h]),
    uniforms: {
      renderScale: 1, time: c.time || 0, effectAmt: 1, scaleAmt: c.scaleAmt || 100,
      rotation: c.rotation || 0, offsetX: c.offsetX || 0, offsetY: c.offsetY || 0,
      intensity: c.intensity || 0, saturation: c.saturation || 0,
    },
  };
  return { tex, o, values: bindingValues(c, tex, o) };
}
function wrongVariant(name, c) {
  if (name === "inputTex") return new Surface(1, 1);
  if (name === "resolution" || name === "tileOffset" || name === "fullResolution") return new Float32Array([1]);
  return "not-a-f32-number";
}
function mutant(s) {
  let t = text;
  for (const [x, y] of s.anchors || [[s.anchor, s.replacement]]) {
    if (t.split(x).length - 1 !== 1) throw Error(s.name + " anchor drift");
    t = t.replace(x, y);
  }
  return Function('"use strict"; return (' + t + ");")();
}
function measure(f) {
  return cases.map((c) => {
    const z = compare(render(f, c).out, expectedMap.get(c.name));
    return {
      case: c.name,
      differs: !z.exact,
      changed_lane_count: z.changed_lane_count,
      changed_rgba8_byte_count: z.changed_rgba8_byte_count,
      first_mismatch: z.first_mismatch,
    };
  });
}
const specs = [
    {
      name: "ceil-dropped",
      output_live: false,
      anchor: "uv[0] -= ceil(",
      replacement: "uv[0] -= (",
    },
    {
      name: "rotate-angle-map-perturbed",
      output_live: false,
      anchor: "rot = map(rot, 0, 360, 0, 2);",
      replacement: "rot = map(rot, 0, 360, 0, 1);",
    },
    {
      name: "brightness-coefficient-perturbed",
      output_live: true,
      anchor: "-0.4000000059604645",
      replacement: "-0.2000000059604645",
    },
    {
      name: "saturation-map-perturbed",
      output_live: true,
      anchor: "map(saturation, -100, 100, -1, 1)",
      replacement: "map(saturation, -100, 100, -0.5, 1)",
    },
    {
      name: "aspect-ratio-inverted",
      output_live: false,
      anchor: "st[0] *= fullResolution[0] / fullResolution[1];",
      replacement: "fullResolution[1] / fullResolution[0]",
    },
  ],
  ledger = specs.map((s) => {
    const rows = measure(mutant(s));
    const witnesses = rows.filter((x) => x.differs);
    if (s.output_live !== (witnesses.length > 0)) throw Error("witness semantics failed for " + s.name);
    return {
      name: s.name,
      classification: s.output_live ? "output-live" : "measured-invariant",
      results: rows,
      witness_cases: rows.filter((x) => x.differs).map((x) => x.case),
      control_cases: rows.filter((x) => !x.differs).map((x) => x.case),
    };
  });
const tr = measure(
  mutant({
    name: "table-content-perturbed",
    anchor: "edge3[0] = -0.875;",
    replacement: "edge3[0] = -0.5;",
  }),
);
if (tr.some((x) => x.differs)) throw Error("write-only table mutant diverged");
const mr = measure(
  mutant({
    name: "bicubic-mat4-dead-mutated",
    anchor:
      "var S = new $runtime.PooledFloat32Array([1, 0, 0, 0, 0, 0, 1, 0, -3, 3, -2, -1, 2, -2, 1, 1]);",
    replacement:
      "var S = new $runtime.PooledFloat32Array([2, 0, 0, 0, 0, 0, 1, 0, -3, 3, -2, -1, 2, -2, 1, 1]);",
  }),
);
if (mr.some((x) => x.differs)) throw Error("mat4 mutant diverged");
function comparerSelfTest() {
  const plus = new Surface(1, 1, new Float32Array([0, 0, 0, 1]));
  const minus = new Surface(1, 1, new Float32Array([-0, 0, 0, 1]));
  const expectedPlus = expected(plus);
  const legacyAccepted = Array.from(minus.data).every((value, index) => value === plus.data[index]);
  if (!legacyAccepted) throw Error("RED setup no longer reproduces the signed-zero old comparer bug");
  const green = compare(minus, expectedPlus);
  if (green.exact || green.changed_lane_count !== 1) throw Error("GREEN comparer failed signed-zero behavioral assertion");
  return {
    red: { old_numeric_equality_accepted_signed_zero: legacyAccepted },
    green: { exact_word_comparer_rejected_signed_zero: !green.exact, changed_lane_count: green.changed_lane_count },
  };
}
const comparerTests = comparerSelfTest();
if (cases.length < 4 || new Set(cases.map((c) => c.w + "x" + c.h)).size < 3 || !cases.some((c) => c.tile) || !cases.some((c) => !c.tile)) throw Error("degenerate case matrix");
const fixture = {
  schema: "noisemaker-for-cpp.effects188.pixel-parity.v1",
  program_key: key,
  corpus_revision: rev,
  defines: { EFFECT: 0, FLIP: 0 },
  source: { relative_path: srcRel, bytes: 21087, sha256: srcSha },
  canonical_factory: {
    name: factoryName,
    text_sha256: factorySha,
    source_slice_sha256: sha(source.slice(a, b)),
  },
  authority: {
    node: "v24.7.0",
    oracle: "unmodified public canonical factory from immutable snapshot",
    pinned_files: files,
    cpu_root: "<immutable-cpu-snapshot-root>",
    live_checkout: "<live-noisemaker-for-cpu-checkout>",
    canonical_public_identity: true,
    adapter_override_absent: true,
    import_closure: closureRecords,
  },
  generator_provenance: {
    relative_path: "docs/port-engineering/effects-parity/effects188_oracle_generator.mjs",
    sha256: sha(fs.readFileSync(generatorPath)),
  },
  table_contract: {
    names: tableNames,
    values: tables,
    element_count: 63,
    reads_at_defines: [],
    write_only_at_defines: true,
  },
  comparer_self_tests: comparerTests,
  binding_names: names,
  binding_abi: abi,
  abi_rejection_matrix: abiMatrix,
  native_binding_preflight: nativeBindingPreflight,
  case_specs: caseSpecs,
  render_cases: renderCases,
  mutation_ledger: ledger,
  write_only_table_control: {
    mutant: "table-content-perturbed",
    rows: tr,
    changed_lanes: 0,
  },
  unreachable_mat4_control: {
    mutant: "bicubic-mat4-dead-mutated",
    rows: mr,
    changed_lanes: 0,
  },
  claim_boundaries: {
    tables:
      "Seven tables write-only at frozen defines; exact stores are structural.",
    mat4: "Bicubic mat4 unreachable; native closure structural.",
    defines: "Nonzero EFFECT/FLIP require separate oracle.",
    crop: "No crop identity asserted.",
  },
  output_storage_control: {
    distinct_buffers: true,
    cases: renderCases.map((x) => ({ case: x.name, independent: true })),
  },
};
const json = JSON.stringify(fixture, null, 2) + "\n",
  reportText =
    "Effects188 oracle; public canonical factory; frozen EFFECT=0 FLIP=0.\n" +
    renderCases
      .map((x) => x.name + " " + x.output_expected.f32_sha256)
      .join("\n") +
    "\nReachable mutants and invariant table/mat4 controls are measured per case.\nTDD comparer RED/GREEN and strict provenance/materialization gates are recorded.\n";
const absolutePattern = /(?:^|[\s"'])(?:\/|[A-Za-z]:[\\/]|file:\/\/|\\\\|~\/|\$HOME(?:[\\/]|$))/i;
function scanForAbsolute(value, label) {
  if (typeof value === "string") {
    if (absolutePattern.test(value)) throw Error("absolute-looking path leaked into " + label);
    if (value.includes(cpu) || value.includes(live || "__no_live__")) throw Error("snapshot path leaked into " + label);
  } else if (Array.isArray(value)) {
    value.forEach((item, index) => scanForAbsolute(item, label + "[" + index + "]"));
  } else if (value && typeof value === "object") {
    Object.entries(value).forEach(([key, item]) => scanForAbsolute(item, label + "." + key));
  }
}
scanForAbsolute(fixture, "fixture");
scanForAbsolute(reportText, "report");
const verify = (p) => {
  if (!fs.existsSync(p) || !fs.existsSync(side(p)) || fs.readFileSync(side(p), "utf8") !== sideText(p, fs.readFileSync(p))) throw Error("sidecar drift: " + p);
};
verify(generatorPath);
verify(materializerPath);
if (fs.existsSync(expectedIncludePath)) verify(expectedIncludePath);
if (!self) {
  if (write) {
    fs.writeFileSync(out, json);
    fs.writeFileSync(report, reportText);
    fs.writeFileSync(side(out), sideText(out, Buffer.from(json)));
    fs.writeFileSync(side(report), sideText(report, Buffer.from(reportText)));
  } else {
    verify(out);
    verify(report);
    if (
      fs.readFileSync(out, "utf8") !== json ||
      fs.readFileSync(report, "utf8") !== reportText
    )
      throw Error("oracle drift");
  }
}
if (self)
  console.log(
    "Effects188 comparer TDD: RED old_numeric_equality_accepted_signed_zero=" +
      comparerTests.red.old_numeric_equality_accepted_signed_zero +
      "; GREEN exact_word_comparer_rejected_signed_zero=" +
      comparerTests.green.exact_word_comparer_rejected_signed_zero +
      " changed_lane_count=" +
      comparerTests.green.changed_lane_count,
  );
console.log(
  "Effects188 oracle " +
    (self ? "self-tested" : write ? "written" : "checked") +
    ": " +
    cases.length +
    " cases, " +
    ledger.length +
    " mutants, 63 stores",
);
