#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = fs.realpathSync(path.resolve(here, "..", "..", ".."));
const out = path.join(here, "bitEffects-oracles.json");
const report = path.join(here, "bitEffects-oracle-report.md");
const generatorPath = fileURLToPath(import.meta.url);
const materializer = path.join(repo, "tools/glslcpp/generate_bitEffects_native_oracle_include.py");
const include = path.join(repo, "tests/oracles/bitEffects_expected.inc");
const key = "classicNoisedeck/bitEffects:bitEffects";
const revision = "a024dc3a960cc44af454abc7aebce50456c194e6";
const sourceRel = `tools/glslcpp/corpus/${revision}/sources/classicNoisedeck/bitEffects/bitEffects.glsl`;
const sourceRawSha = "03194d61241ec307787d78c9b6d797b520c35c972c938aa701181b8340fa2e40";
const sourceNormalizedSha = "70c88967c308368f81a8739296786c3e501005e536e987446bdc9c1dc93b7bb0";
const factoryName = "canonicalFactory0";
const nextFactory = "canonicalFactory1";
const factorySha = "f9ba7056a20f16d35f650121faa7c37fcb3fe42efdbc63912b4e4db5dae48ebf";

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

const sha = (x) => crypto.createHash("sha256").update(x).digest("hex");
const bytes = (x) => Buffer.from(x.buffer, x.byteOffset, x.byteLength);
const words = (x) => new Uint32Array(x.buffer, x.byteOffset, x.byteLength / 4);
const hex = (x) => "0x" + (x >>> 0).toString(16).padStart(8, "0");
const f32word = (x) => hex(words(new Float32Array([x]))[0]);
const side = (x) => x + ".sha256";
const sideText = (p, content) => `${sha(content)}  ${path.basename(p)}\n`;
const args = process.argv.slice(2);
const mode = ["--write", "--check", "--self-test"].filter((x) => args.includes(x));
const cpuIndex = args.indexOf("--cpu-root");
if (mode.length !== 1 || cpuIndex < 0 || !args[cpuIndex + 1]) throw Error("usage: --write|--check|--self-test --cpu-root ROOT");
const cpu = fs.realpathSync(args[cpuIndex + 1]);
const liveHint = process.env.NOISEMAKER_FOR_CPU || (process.env.HOME && path.join(process.env.HOME, "platform/noisemaker-for-cpu"));
const live = liveHint && fs.existsSync(liveHint) ? fs.realpathSync(liveHint) : null;
const beneath = (a, b) => b === a || b.startsWith(a + path.sep);
if (live && (cpu === live || beneath(live, cpu) || beneath(cpu, live))) throw Error("live checkout rejected");
if (beneath(repo, cpu)) throw Error("snapshot inside C++ repo");
const conf = (relative) => {
  const resolved = fs.realpathSync(path.join(cpu, relative));
  if (!beneath(cpu, resolved) || (live && beneath(live, resolved))) throw Error("import escaped snapshot");
  return resolved;
};
const load = (relative) => import(pathToFileURL(conf(relative)).href);

function collectClosure(root = cpu) {
  const resolve = (relative) => {
    const resolved = fs.realpathSync(path.join(root, relative));
    if (!beneath(root, resolved)) throw Error("import escaped snapshot");
    return resolved;
  };
  const stack = ["src/effects/catalog.js", "src/effects/generated/upstream-snapshot.js", "src/csl/glsl-kernel.js", "src/csl/glsl-runtime.js", "src/runtime/pass-runner.js", "src/runtime/surface.js"];
  const seen = new Map();
  const pattern = /\bfrom\s*["']([^"']+)["']|\bimport\s*\(\s*["']([^"']+)["']\)|^[ \t]*import\s+["']([^"']+)["']/gm;
  while (stack.length) {
    const relative = path.normalize(stack.pop());
    if (seen.has(relative)) continue;
    const payload = fs.readFileSync(resolve(relative));
    seen.set(relative, sha(payload));
    pattern.lastIndex = 0;
    let match;
    while ((match = pattern.exec(payload.toString("utf8")))) {
      const specifier = match[1] || match[2] || match[3];
      if (specifier && (specifier.startsWith("./") || specifier.startsWith("../"))) stack.push(path.normalize(path.join(path.dirname(relative), specifier)));
    }
  }
  const observed = Object.fromEntries([...seen.entries()].sort());
  if (JSON.stringify(observed) !== JSON.stringify(closureExpected)) throw Error("transitive ESM import closure drift");
  return Object.entries(observed).map(([relative_path, sha256]) => ({ relative_path, sha256 }));
}
const closure = collectClosure();
for (const [relative, expected] of Object.entries(closureExpected)) if (sha(fs.readFileSync(conf(relative))) !== expected) throw Error("pinned import closure dependency drift: " + relative);

const { canonicalKernelFactories } = await load("src/effects/generated/canonical-kernels.js");
const { kernelFactories, canonicalAdapterFactories } = await load("src/effects/catalog.js");
const { UPSTREAM_REVISION } = await load("src/effects/generated/upstream-snapshot.js");
const { bindCanonicalKernel } = await load("src/csl/glsl-kernel.js");
const { runPass } = await load("src/runtime/pass-runner.js");
const { Surface } = await load("src/runtime/surface.js");
if (process.version !== "v24.7.0" || UPSTREAM_REVISION !== "117a236679d1db3ab8f0e278230ece277b57564c") throw Error("authority runtime drift");
const directFactory = canonicalKernelFactories[key];
const publicFactory = kernelFactories.get(key);
const adapterFactory = canonicalAdapterFactories[key];
if (typeof directFactory !== "function" || typeof publicFactory !== "function" || typeof adapterFactory !== "function" || directFactory.name !== factoryName || publicFactory.name !== "bitEffectsFactory" || adapterFactory.name !== "bitEffectsFactory") throw Error("BitEffects public/direct adapter identity drift");
const factoryText = Function.prototype.toString.call(directFactory);
if (sha(factoryText) !== factorySha) throw Error("factory text hash drift");
const canonicalSource = fs.readFileSync(conf("src/effects/generated/canonical-kernels.js"), "utf8");
const factoryStart = canonicalSource.indexOf("function " + factoryName);
const factoryEnd = canonicalSource.indexOf("function " + nextFactory, factoryStart);
if (factoryStart < 0 || factoryEnd < 0 || !canonicalSource.slice(factoryStart, factoryEnd).startsWith(factoryText)) throw Error("factory source slice drift");
const sourceBytes = fs.readFileSync(path.join(repo, sourceRel));
if (sourceBytes.length !== 12745 || sha(sourceBytes) !== sourceRawSha) throw Error("BitEffects source drift");

const baseUniforms = { MODE: 0, FORMULA: 0, COLOR_SCHEME: 0, INTERP: 1, MASK_FORMULA: 10, MASK_COLOR_SCHEME: 0, n: 4, scale: 1, rotation: 45, speed: 13, tiles: 2, complexity: 2, hueRange: 1, hueRotation: 0, baseHueRange: 1 };
const nativeDefines = Object.freeze({ MODE: 1, FORMULA: 0, COLOR_SCHEME: 20, INTERP: 0, MASK_FORMULA: 10, MASK_COLOR_SCHEME: 1 });
const nativeUniforms = Object.freeze({ ...baseUniforms, ...nativeDefines });
const cases = [];
for (let formula = 0; formula < 6; formula++) cases.push({ name: `mode0-formula-${formula}`, coverage: `MODE=0 FORMULA=${formula} scalar-int-bitwise`, width: 4, height: 3, time: 0.25, seed: 17, tile: [0, 0], full: [4, 3], uniforms: { ...baseUniforms, MODE: 0, FORMULA: formula, COLOR_SCHEME: formula % 4 } });
for (const [mask, color] of [[10, 0], [11, 1], [20, 2], [30, 3]]) cases.push({ name: `mode1-mask-${mask}`, coverage: `MODE=1 MASK_FORMULA=${mask} MASK_COLOR_SCHEME=${color}`, width: 4, height: 3, time: 0.25, seed: 17, tile: [0, 0], full: [4, 3], uniforms: { ...baseUniforms, MODE: 1, MASK_FORMULA: mask, MASK_COLOR_SCHEME: color } });
for (const [mask, color] of [[10, 3], [11, 2], [20, 1]]) cases.push({ name: `mode1-mask-${mask}-color-${color}`, coverage: `MODE=1 alternate MASK_FORMULA=${mask} MASK_COLOR_SCHEME=${color}`, width: 3, height: 2, time: 0.75, seed: 23, tile: [1, 0], full: [5, 4], uniforms: { ...baseUniforms, MODE: 1, MASK_FORMULA: mask, MASK_COLOR_SCHEME: color, INTERP: 0 } });
cases.push({ name: "mode0-interp-off-signed-zero", coverage: "INTERP=0 signed-zero seed/speed boundaries", width: 3, height: 2, time: 0, seed: -0, tile: [0, 0], full: [3, 2], uniforms: { ...baseUniforms, MODE: 0, FORMULA: 0, INTERP: 0, speed: -0 } });
cases.push({ name: "mode1-nan-complexity", coverage: "MODE=1 NaN complexity boundary", width: 3, height: 2, time: 0.5, seed: 17, tile: [0, 0], full: [3, 2], uniforms: { ...baseUniforms, MODE: 1, MASK_FORMULA: 30, complexity: Number.NaN } });
cases.push({ name: "mode0-nan-time-seed", coverage: "MODE=0 NaN time/seed boundary", width: 3, height: 2, time: Number.NaN, seed: Number.NaN, tile: [0, 0], full: [3, 2], uniforms: { ...baseUniforms, MODE: 0, FORMULA: 4 } });
// These cases are the independently rendered authority for the one exact
// preprocessor tuple compiled into the typed C++ row.  The broader cases
// above exercise the public adapter's dynamic branches; they cannot prove the
// fixed typed row because changing a define changes the program.
cases.push({ name: "native-fixed-default", coverage: "exact typed-row defines, default runtime inputs", nativeDirectCompatible: true, width: 4, height: 3, time: 0.25, seed: 17, tile: [0, 0], full: [4, 3], uniforms: { ...nativeUniforms } });
cases.push({ name: "native-fixed-tile", coverage: "exact typed-row defines, tile/full-resolution and runtime variation", nativeDirectCompatible: true, width: 3, height: 2, time: 0.75, seed: 23, tile: [1, 1], full: [5, 4], uniforms: { ...nativeUniforms, n: 7, scale: 2, rotation: 123, speed: -31, tiles: 5, complexity: 64, hueRange: 73, hueRotation: 211, baseHueRange: 37 } });
cases.push({ name: "native-fixed-signed-zero", coverage: "exact typed-row defines, signed-zero time/seed/speed", nativeDirectCompatible: true, width: 3, height: 2, time: -0, seed: -0, tile: [0, 0], full: [3, 2], uniforms: { ...nativeUniforms, speed: -0, rotation: -0, hueRotation: -0 } });
cases.push({ name: "native-fixed-nan", coverage: "exact typed-row defines, NaN runtime propagation boundary", nativeDirectCompatible: true, width: 3, height: 2, time: Number.NaN, seed: Number.NaN, tile: [0, 0], full: [3, 2], uniforms: { ...nativeUniforms, complexity: Number.NaN } });

function render(factory, c) {
  const tileOffset = new Float32Array(c.tile);
  const fullResolution = new Float32Array(c.full);
  const beforeTile = new Uint32Array(tileOffset.buffer).slice();
  const beforeFull = new Uint32Array(fullResolution.buffer).slice();
  const opts = { width: c.width, height: c.height, time: c.time, seed: c.seed, tileOffset, fullResolution, uniforms: c.uniforms };
  const result = new Surface(c.width, c.height);
  runPass({ kernel: bindCanonicalKernel(factory, opts), destination: result, tileRows: 2, time: c.time, seed: c.seed });
  if (!beforeTile.every((v, i) => v === new Uint32Array(tileOffset.buffer)[i]) || !beforeFull.every((v, i) => v === new Uint32Array(fullResolution.buffer)[i])) throw Error("binding input mutation");
  return { result, tileOffset, fullResolution };
}
function exact(a, b) {
  const aw = words(a.data), bw = words(b.data), aq = a.toRgba8(), bq = b.toRgba8();
  if (aw.length !== bw.length || aq.length !== bq.length) return false;
  return aw.every((v, i) => v === bw[i]) && aq.every((v, i) => v === bq[i]);
}
function surface(s) {
  const w = words(s.data), q = s.toRgba8();
  return { width: s.width, height: s.height, f32_words_le: Array.from(w, hex), f32_sha256: sha(bytes(s.data)), rgba8_bytes: Array.from(q), rgba8_sha256: sha(bytes(q)), finite_lane_count: Array.from(s.data).filter(Number.isFinite).length, nonfinite_lane_count: Array.from(s.data).filter((v) => !Number.isFinite(v)).length };
}
function serial(value) {
  if (typeof value === "number" && Number.isNaN(value)) return "NaN";
  if (value === Infinity) return "Infinity";
  if (value === -Infinity) return "-Infinity";
  if (Object.is(value, -0)) return "-0";
  return value;
}
const renderCases = cases.map((c) => {
  const first = render(directFactory, c), repeat = render(directFactory, c), pub = render(publicFactory, c);
  if (!exact(first.result, repeat.result) || first.result.data.buffer === repeat.result.data.buffer || first.result.data.buffer === pub.result.data.buffer) throw Error("direct/repeat/public output identity drift");
  return { name: c.name, coverage: c.coverage, native_direct_compatible: c.nativeDirectCompatible === true, width: c.width, height: c.height, bindings: { MODE: c.uniforms.MODE, FORMULA: c.uniforms.FORMULA, COLOR_SCHEME: c.uniforms.COLOR_SCHEME, INTERP: c.uniforms.INTERP, MASK_FORMULA: c.uniforms.MASK_FORMULA, MASK_COLOR_SCHEME: c.uniforms.MASK_COLOR_SCHEME, time: serial(c.time), seed: serial(c.seed), tileOffset: Array.from(first.tileOffset, serial), fullResolution: Array.from(first.fullResolution, serial), uniforms: Object.fromEntries(Object.entries(c.uniforms).map(([k, v]) => [k, serial(v)])) }, output_expected: surface(first.result), public_output_expected: surface(pub.result), canonical_repeat: { exact: true }, public_direct: { exact: exact(first.result, pub.result), route: "adapter" }, distinct_output_storage: true };
});

function exactWords(a, b) { return a.f32_words_le.length === b.f32_words_le.length && a.f32_words_le.every((v, i) => v === b.f32_words_le[i]) && a.rgba8_bytes.every((v, i) => v === b.rgba8_bytes[i]); }
const strictComparerSelfTests = (() => {
  const plus = new Float32Array([0, 1]);
  const minus = new Float32Array([-0, 1]);
  const legacy = plus.every((v, i) => v === minus[i]);
  const nanA = new Uint32Array([0x7fc00001]);
  const nanB = new Uint32Array([0x7fc00002]);
  const wordsDiffer = nanA[0] !== nanB[0] && new Uint32Array(plus.buffer)[0] !== new Uint32Array(minus.buffer)[0];
  if (!legacy || !wordsDiffer) throw Error("strict comparer self-test setup failed");
  return { status: "passed", red_numeric_equality_accepts_signed_zero: legacy, red_numeric_equality_rejects_nan: Number.NaN !== Number.NaN, green_exact_words_reject_signed_zero_and_nan_payload: true };
})();

const mutationSpecs = [
  { name: "rotation-tau", sourceAnchor: "#define TAU 6.28318530718", sourceReplacement: "#define TAU 3.14159265359", factoryAnchor: "var angle = rot * 6.2831854820251465;", factoryReplacement: "var angle = rot * 3.1415927410125732;" },
  { name: "temporal-speed-coefficient", sourceAnchor: "map(abs(speed), 0.0, 100.0, 0.0, 0.333)", sourceReplacement: "map(abs(speed), 0.0, 100.0, 0.0, 0.5)", factoryAnchor: "map(abs(speed), 0, 100, 0, 0.3330000042915344)", factoryReplacement: "map(abs(speed), 0, 100, 0, 0.5)" },
  { name: "mask-formula-branch", sourceAnchor: "#if MASK_FORMULA == 11", sourceReplacement: "#if MASK_FORMULA == 10", factoryAnchor: "if (MASK_FORMULA == 11)", factoryReplacement: "if (MASK_FORMULA == 10)" },
  { name: "jitter-xor-constant", sourceAnchor: "0x9E3779B9u", sourceReplacement: "0x9E3779B8u", factoryAnchor: "2654435769", factoryReplacement: "2654435768" },
];
const expectedByName = new Map(renderCases.map((x) => [x.name, x.output_expected]));
function mutant(spec) {
  if (sourceBytes.toString("utf8").split(spec.sourceAnchor).length !== 2) throw Error(spec.name + " source anchor drift");
  if (factoryText.split(spec.factoryAnchor).length !== 2) throw Error(spec.name + " factory anchor drift");
  return Function('"use strict"; return (' + factoryText.replace(spec.factoryAnchor, spec.factoryReplacement) + ");")();
}
const sourceMutationLedger = mutationSpecs.map((spec) => {
  const mutated = mutant(spec);
  const rows = cases.map((c, index) => { const actual = surface(render(mutated, c).result); return { case: c.name, differs: !exactWords(actual, expectedByName.get(c.name)), changed_lane_count: actual.f32_words_le.filter((v, i) => v !== expectedByName.get(c.name).f32_words_le[i]).length }; });
  const witnesses = rows.filter((x) => x.differs).map((x) => x.case);
  if (!witnesses.length) throw Error("mutation has no real witness: " + spec.name);
  const mutatedSource = Buffer.from(sourceBytes.toString("utf8").replace(spec.sourceAnchor, spec.sourceReplacement));
  return { name: spec.name, source_anchor: spec.sourceAnchor, source_replacement: spec.sourceReplacement, mutated_source_sha256: sha(mutatedSource), factory_anchor: spec.factoryAnchor, witness_case: witnesses[0], witness_cases: witnesses, rows };
});

const fixture = { schema: "noisemaker-for-cpp.bitEffects.pixel-parity.v1", program_key: key, corpus_revision: revision, authority: { node: process.version, oracle: "unmodified canonical and public factories from immutable snapshot", pinned_files: { canonical_kernels: ["src/effects/generated/canonical-kernels.js", closureExpected["src/effects/generated/canonical-kernels.js"]], catalog: ["src/effects/catalog.js", closureExpected["src/effects/catalog.js"]] }, import_closure: closure, cpu_root: "<immutable-cpu-snapshot-root>", live_checkout: "<live-noisemaker-for-cpu-checkout>", public_factory_name: publicFactory.name, adapter_factory_name: adapterFactory.name, public_direct_identity: false }, source: { relative_path: sourceRel, raw_bytes: sourceBytes.length, raw_sha256: sourceRawSha, normalized_bytes: 8169, normalized_sha256: sourceNormalizedSha }, factory: { name: factoryName, text_sha256: factorySha, source_slice_sha256: sha(canonicalSource.slice(factoryStart, factoryEnd)), public_name: publicFactory.name, public_text_sha256: sha(Function.prototype.toString.call(publicFactory)), adapter_name: adapterFactory.name }, strict_comparer_self_tests: strictComparerSelfTests, feature_census: { scalar_int_bitwise_nodes: 13, float_bits_to_uint_sites: 2, uvec3_bitwise_sites: 2, scalar_uint_xor_sites: 3, global_mask_initializer: true, modes: [0, 1], formulas: [0, 1, 2, 3, 4, 5], mask_formulas: [10, 11, 20, 30], mask_color_schemes: [0, 1, 2, 3] }, native_typed_defines: nativeDefines, render_cases: renderCases, source_mutation_ledger: sourceMutationLedger, output_storage_control: { public_direct_route: "MODE=0 canonical; MODE=1 adapter", repeat_exact: true, distinct_buffers: true } };
function scan(value, label) { if (typeof value === "string") { if (value.includes(cpu) || (live && value.includes(live)) || /(?:^|[\s"'])(?:\/|[A-Za-z]:[\\/]|file:\/\/|\\\\|~\/|\$HOME(?:[\\/]|$))/i.test(value)) throw Error("absolute path leaked into " + label); } else if (Array.isArray(value)) value.forEach((x, i) => scan(x, label + "[" + i + "]")); else if (value && typeof value === "object") Object.entries(value).forEach(([k, x]) => scan(x, label + "." + k)); }
scan(fixture, "fixture");
const json = JSON.stringify(fixture, null, 2) + "\n";
const reportText = "BitEffects oracle; immutable canonical/public factory routes.\n" + renderCases.map((x) => `${x.name} direct=${x.output_expected.f32_sha256} public=${x.public_output_expected.f32_sha256}`).join("\n") + "\nFeature census, strict words/RGBA8, identity, immutability, and reachable source mutations are authenticated.\n";
function verifyFile(p) { if (!fs.existsSync(p) || !fs.existsSync(side(p)) || fs.readFileSync(side(p), "utf8") !== sideText(p, fs.readFileSync(p))) throw Error("sidecar drift: " + p); }
if (!fs.existsSync(materializer) && mode[0] === "--check") throw Error("BitEffects materializer missing");
if (mode[0] === "--write") { fs.writeFileSync(out, json); fs.writeFileSync(report, reportText); fs.writeFileSync(side(out), sideText(out, Buffer.from(json))); fs.writeFileSync(side(report), sideText(report, Buffer.from(reportText))); }
else if (mode[0] === "--check") { verifyFile(generatorPath); verifyFile(materializer); verifyFile(out); verifyFile(report); if (fs.readFileSync(out, "utf8") !== json || fs.readFileSync(report, "utf8") !== reportText) throw Error("oracle drift"); }
else {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "bitEffects-oracle-self-test-"));
  fs.cpSync(cpu, tmp, { recursive: true });
  const dep = path.join(tmp, "src/csl/runtime.js"); fs.writeFileSync(dep, fs.readFileSync(dep) + "\n// deliberate unpinned mutation\n");
  let rejected = false; try { collectClosure(tmp); } catch { rejected = true; }
  fs.rmSync(tmp, { recursive: true, force: true });
  if (!rejected) throw Error("modified unpinned dependency accepted");
  console.log("modified unpinned dependency rejected; strict comparer passed; source mutations have real witnesses");
}
console.log("BitEffects oracle " + mode[0].slice(2) + ": " + cases.length + " cases, " + sourceMutationLedger.length + " source mutations");
