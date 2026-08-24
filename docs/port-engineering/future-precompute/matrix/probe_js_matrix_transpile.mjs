// READ-ONLY diagnostic. Imports the glsl-transpiler package already vendored
// under noisemaker-for-cpu/node_modules (read-only import, no writes to that
// repo) and runs it, standalone, on two minimal GLSL snippets that reproduce
// the exact matrix-arithmetic shapes found in the 9 matrix-blocked programs:
//   1. the oklab_from_linear_srgb / linear_srgb_from_oklab mat3*vec3 pattern
//      (cellNoise, colorLab, moodscape, noise, shapes, adjust, colorspace)
//   2. the bicubic() mat4*mat4*mat4 / vec4*mat4 pattern (effects, glitch)
// Uses the SAME transpiler options as scripts/upstream/compile-glsl.js's
// transpile() function (version '300 es', preprocess, optimize:true,
// includes:false, uniform/varying renaming), to see whether `optimize:true`
// scalarizes the matrix multiply the way it scalarized Curl's tanh (the
// Task-31 narrowing hazard) or keeps it as a materialized Float32Array
// operation (which task-31-curl-SOLVED.md's narrowing analysis identified as
// the safe case).
//
// Writes ONLY under docs/port-engineering/future-precompute/matrix/.

import GLSL from '../noisemaker-for-cpu/node_modules/glsl-transpiler/index.js'
import { normalizeCanonicalGlsl } from '../noisemaker-for-cpu/src/csl/glsl-normalize.js'
import { writeFileSync } from 'node:fs'

// Mirrors scripts/upstream/compile-glsl.js's transpile(), but first runs the
// SAME normalizeCanonicalGlsl() pass the real pipeline runs before handing
// source to glsl-transpiler (strips `#ifdef GL_ES`/`precision`/`#version`,
// lowers `out vec4 fragColor;`, etc.) -- raw corpus GLSL is not directly
// parseable by glsl-transpiler without this step (confirmed: it fails with
// "parameter is not allowed here" on `precision highp float;` alone).
function transpile(rawSource) {
  const normalized = normalizeCanonicalGlsl(rawSource, { sourceName: 'probe' })
  const source = normalized.source
  const preprocess = source.split('\n').some((line) => /^\s*#/.test(line))
  const compile = GLSL({
    version: '300 es',
    preprocess,
    optimize: true,
    includes: false,
    uniform: (name) => `$bindings[${JSON.stringify(name)}]`,
    varying: (name) => `$varyings[${JSON.stringify(name)}]`,
  })
  return compile(source)
}

const oklabSource = `#ifdef GL_ES
precision highp float;
#endif
out vec4 fragColor;
uniform vec3 inputColor;

const mat3 fwdA = mat3(1.0, 1.0, 1.0,
                       0.3963377774, -0.1055613458, -0.0894841775,
                       0.2158037573, -0.0638541728, -1.2914855480);

const mat3 fwdB = mat3(4.0767245293, -1.2681437731, -0.0041119885,
                       -3.3072168827, 2.6093323231, -0.7034763098,
                       0.2307590544, -0.3411344290,  1.7068625689);

const mat3 invB = mat3(0.4121656120, 0.2118591070, 0.0883097947,
                       0.5362752080, 0.6807189584, 0.2818474174,
                       0.0514575653, 0.1074065790, 0.6302613616);

const mat3 invA = mat3(0.2104542553, 1.9779984951, 0.0259040371,
                       0.7936177850, -2.4285922050, 0.7827717662,
                       -0.0040720468, 0.4505937099, -0.8086757660);

vec3 oklab_from_linear_srgb(vec3 c) {
    vec3 lms = invB * c;
    return invA * (sign(lms) * pow(abs(lms), vec3(0.3333333333333)));
}

vec3 linear_srgb_from_oklab(vec3 c) {
    vec3 lms = fwdA * c;
    return fwdB * (lms * lms * lms);
}

void main() {
    vec3 lab = oklab_from_linear_srgb(inputColor);
    vec3 back = linear_srgb_from_oklab(lab);
    fragColor = vec4(back, 1.0);
}
`

const bicubicSource = `#ifdef GL_ES
precision highp float;
#endif
out vec4 fragColor;
uniform sampler2D tex;
uniform vec2 resolution;

float f(vec2 p) { return texture(tex, p / resolution).r; }

float bicubic(vec2 p) {
    float x = p.x;
    float y = p.y;
    float x1 = floor(x);
    float y1 = floor(y);
    float x2 = x1 + 1.;
    float y2 = y1 + 1.;
    float f11 = f(vec2(x1, y1));
    float f12 = f(vec2(x1, y2));
    float f21 = f(vec2(x2, y1));
    float f22 = f(vec2(x2, y2));
    float f11x = (f(vec2(x1 + 1., y1)) - f(vec2(x1 - 1., y1))) / 2.;
    float f12x = (f(vec2(x1 + 1., y2)) - f(vec2(x1 - 1., y2))) / 2.;
    float f21x = (f(vec2(x2 + 1., y1)) - f(vec2(x2 - 1., y1))) / 2.;
    float f22x = (f(vec2(x2 + 1., y2)) - f(vec2(x2 - 1., y2))) / 2.;
    float f11y = (f(vec2(x1, y1 + 1.)) - f(vec2(x1, y1 - 1.))) / 2.;
    float f12y = (f(vec2(x1, y2 + 1.)) - f(vec2(x1, y2 - 1.))) / 2.;
    float f21y = (f(vec2(x2, y1 + 1.)) - f(vec2(x2, y1 - 1.))) / 2.;
    float f22y = (f(vec2(x2, y2 + 1.)) - f(vec2(x2, y2 - 1.))) / 2.;
    float f11xy = (f(vec2(x1 + 1., y1 + 1.)) - f(vec2(x1 + 1., y1 - 1.)) - f(vec2(x1 - 1., y1 + 1.)) + f(vec2(x1 - 1., y1 - 1.))) / 4.;
    float f12xy = (f(vec2(x1 + 1., y2 + 1.)) - f(vec2(x1 + 1., y2 - 1.)) - f(vec2(x1 - 1., y2 + 1.)) + f(vec2(x1 - 1., y2 - 1.))) / 4.;
    float f21xy = (f(vec2(x2 + 1., y1 + 1.)) - f(vec2(x2 + 1., y1 - 1.)) - f(vec2(x2 - 1., y1 + 1.)) + f(vec2(x2 - 1., y1 - 1.))) / 4.;
    float f22xy = (f(vec2(x2 + 1., y2 + 1.)) - f(vec2(x2 + 1., y2 - 1.)) - f(vec2(x2 - 1., y2 + 1.)) + f(vec2(x2 - 1., y2 - 1.))) / 4.;
    mat4 Q = mat4(f11, f21, f11x, f21x, f12, f22, f12x, f22x, f11y, f21y, f11xy, f21xy, f12y, f22y, f12xy, f22xy);
    mat4 S = mat4(1., 0., 0., 0., 0., 0., 1., 0., -3., 3., -2., -1., 2., -2., 1., 1.);
    mat4 T = mat4(1., 0., -3., 2., 0., 0., 3., -2., 0., 1., -2., 1., 0., 0., -1., 1.);
    mat4 A = T * Q * S;
    float t = fract(p.x);
    float u = fract(p.y);
    vec4 tv = vec4(1., t, t * t, t * t * t);
    vec4 uv4 = vec4(1., u, u * u, u * u * u);
    float result = dot(tv * A, uv4);
    return result;
}

void main() {
    fragColor = vec4(bicubic(vec2(3.0, 4.0)));
}
`

let oklabOut, oklabErr
try { oklabOut = transpile(oklabSource) } catch (e) { oklabErr = e.stack || String(e) }
let bicubicOut, bicubicErr
try { bicubicOut = transpile(bicubicSource) } catch (e) { bicubicErr = e.stack || String(e) }

writeFileSync('docs/port-engineering/future-precompute/matrix/oklab-transpiled.js',
  oklabOut ?? `TRANSPILE ERROR:\n${oklabErr}`)
writeFileSync('docs/port-engineering/future-precompute/matrix/bicubic-transpiled.js',
  bicubicOut ?? `TRANSPILE ERROR:\n${bicubicErr}`)

console.log('oklab ok:', !!oklabOut, oklabErr ? `ERROR: ${oklabErr.split('\n')[0]}` : '')
console.log('bicubic ok:', !!bicubicOut, bicubicErr ? `ERROR: ${bicubicErr.split('\n')[0]}` : '')
