// The renderer consumes the current packed grid directly, without MIDI event processing.
export function decodeMidiState(packed) {
  const hex = packed.noteGridRgba32f ?? '00'.repeat(128 * 16 * 16)
  if (typeof hex !== 'string' || !/^[0-9a-f]{65536}$/i.test(hex)) {
    throw new Error('MIDI note grid requires 128x16 RGBA float32 texels')
  }
  const bytes = Buffer.from(hex, 'hex')
  const buffer = new ArrayBuffer(bytes.length)
  const view = new DataView(buffer)
  const littleEndian = new Uint8Array(new Uint32Array([1]).buffer)[0] === 1
  for (let offset = 0; offset < bytes.length; offset += 4) {
    view.setUint32(offset, bytes.readUInt32LE(offset), littleEndian)
  }
  return {noteGrid: new Float32Array(buffer), clockCount: packed.clockCount ?? 0}
}
