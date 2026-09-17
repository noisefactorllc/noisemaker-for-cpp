// Shared helpers for the six remaining scatter-adapter oracle generators
// (dla, lenia, physarum, points_render, points_billboard_render, flow3d).
// Every generator imports the REAL, unmodified adapter function from the
// pinned authority snapshot below and calls it directly -- nothing here
// reimplements any adapter's algorithm; this file only builds fuzzed
// inputs and serializes cases for the C++ differential harness.
//
// AUTHORITY SNAPSHOT: this is a fixed local path to the read-only
// noisemaker-for-cpu checkout at commit 61aa869, per the campaign's lane
// contract. Adjust here (only) if the snapshot ever moves.
export const AUTHORITY_ROOT = '/Users/alex/platform/.nm-cpp-work/authority/61aa869'

import fs from 'node:fs'

// Deterministic PRNG (mulberry32) -- NOT required to match any C++ RNG bit
// for bit, because every case's inputs are serialized as literal bytes into
// the binary fuzz file and the C++ side only ever REPLAYS those bytes; it
// never regenerates them independently. Determinism here just means "the
// same seed reproduces the same oracle file," which the `--check` mode of
// each generator verifies.
export function mulberry32(seed) {
  let a = seed >>> 0
  return function next() {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const SPECIAL_FLOATS = [0, -0, 1, -1, 0.5, -0.5, 2, -2, 1e6, -1e6, 1e-6, NaN, Infinity, -Infinity]

// A value suitable for storing into a Float32Array slot (texture data,
// destination pre-seed): sometimes a "special" edge value, sometimes a
// plain random value across a broad range (including >1 and negative, as
// the task brief requires), sometimes deliberately large.
export function randomTexel(rng) {
  const r = rng()
  if (r < 0.12) return SPECIAL_FLOATS[Math.floor(rng() * SPECIAL_FLOATS.length)]
  if (r < 0.2) return (rng() * 2 - 1) * 1000 // large-magnitude stress
  return rng() * 3 - 1 // broad range, includes negatives and >1
}

// A value suitable for a plain (never float32-narrowed) uniform double.
export function randomUniform(rng, { min = -3, max = 3, allowSpecial = true } = {}) {
  const r = rng()
  if (allowSpecial && r < 0.08) return SPECIAL_FLOATS[Math.floor(rng() * SPECIAL_FLOATS.length)]
  return min + rng() * (max - min)
}

export function randomInt(rng, min, max) {
  return min + Math.floor(rng() * (max - min + 1))
}

export function makeSurfaceData(rng, width, height) {
  const data = new Float32Array(width * height * 4)
  for (let i = 0; i < data.length; i += 1) data[i] = randomTexel(rng)
  return data
}

// ---------------------------------------------------------------------------
// Binary fuzz-case writer. One shared, adapter-agnostic record format so a
// single generic C++ reader (tools/scatter_fuzz_verify.cpp) can replay
// every adapter's sweep. See that file's header comment for the exact
// layout; this writer and that reader are hand-kept in sync (both are
// short and reviewed together).
// ---------------------------------------------------------------------------
export class CaseWriter {
  constructor(path) {
    this.path = path
    this.fd = fs.openSync(path, 'w')
    this.count = 0
    // Placeholder header (magic + count); patched by `finalizeCaseCount`
    // after `close()`.
    this._writeRaw(Buffer.from('SCA1'))
    this._writeRaw(this._u32(0))
  }

  _u8(v) {
    const b = Buffer.alloc(1)
    b.writeUInt8(v, 0)
    return b
  }
  _u32(v) {
    const b = Buffer.alloc(4)
    b.writeUInt32LE(v, 0)
    return b
  }
  _f64(v) {
    const b = Buffer.alloc(8)
    b.writeDoubleLE(v, 0)
    return b
  }
  _name(name) {
    const bytes = Buffer.from(name, 'ascii')
    if (bytes.length > 255) throw new RangeError('name too long')
    return Buffer.concat([this._u8(bytes.length), bytes])
  }
  _f32Array(floatArray) {
    const b = Buffer.alloc(floatArray.length * 4)
    for (let i = 0; i < floatArray.length; i += 1) b.writeFloatLE(floatArray[i], i * 4)
    return b
  }

  _writeRaw(buf) {
    fs.writeSync(this.fd, buf)
  }

  // `caseRecord`:
  //   textures: [{ name, surface: {width,height,data}, filterLinear }]
  //   uniforms: { name: doubleValue, ... }   (absent key == JS `undefined`)
  //   blend: null | [srcFactor, dstFactor]   (null == not an array; matches
  //     every JS shape other than a 2-element array: `true`, `false`,
  //     absent)
  //   count: null | doubleValue              (null == JS `undefined`)
  //   destWidth, destHeight
  //   destSeedData: Float32Array (pre-seed content, length destW*destH*4)
  //   expectedData: Float32Array (post-adapter-call content, same length)
  //   expectedPixels: integer
  writeCase(caseRecord) {
    const parts = []
    parts.push(this._u32(caseRecord.textures.length))
    for (const tex of caseRecord.textures) {
      parts.push(this._name(tex.name))
      parts.push(this._u32(tex.surface.width))
      parts.push(this._u32(tex.surface.height))
      parts.push(this._u8(tex.filterLinear ? 1 : 0))
      parts.push(this._f32Array(tex.surface.data))
    }
    const uniformNames = Object.keys(caseRecord.uniforms)
    parts.push(this._u32(uniformNames.length))
    for (const name of uniformNames) {
      parts.push(this._name(name))
      parts.push(this._f64(caseRecord.uniforms[name]))
    }
    if (caseRecord.blend) {
      parts.push(this._u8(1))
      parts.push(this._name(String(caseRecord.blend[0])))
      parts.push(this._name(String(caseRecord.blend[1])))
    } else {
      parts.push(this._u8(0))
    }
    if (caseRecord.count !== null && caseRecord.count !== undefined) {
      parts.push(this._u8(1))
      parts.push(this._f64(caseRecord.count))
    } else {
      parts.push(this._u8(0))
    }
    parts.push(this._u32(caseRecord.destWidth))
    parts.push(this._u32(caseRecord.destHeight))
    parts.push(this._f32Array(caseRecord.destSeedData))
    parts.push(this._f32Array(caseRecord.expectedData))
    parts.push(this._u32(caseRecord.expectedPixels))
    this._writeRaw(Buffer.concat(parts))
    this.count += 1
  }

  close() {
    fs.closeSync(this.fd)
    finalizeCaseCount(this.path, this.count)
  }
}

// Patches the case count into the 4-byte slot right after the "SCA1" magic
// (offset 4), since `CaseWriter` only ever appends while writing.
export function finalizeCaseCount(path, count) {
  const fd = fs.openSync(path, 'r+')
  const b = Buffer.alloc(4)
  b.writeUInt32LE(count, 0)
  fs.writeSync(fd, b, 0, 4, 4)
  fs.closeSync(fd)
}
