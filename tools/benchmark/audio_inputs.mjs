// Packed LE float32 words preserve AudioState samples, including NaN payloads.
export function decodeAudioState(packed) {
  const nativeLittleEndian = new Uint8Array(new Uint32Array([1]).buffer)[0] === 1
  const decode = field => {
    const hex = packed[field]
    if (hex === undefined) return new Float32Array(128)
    if (typeof hex !== 'string' || !/^[0-9a-f]{1024}$/i.test(hex)) throw new Error('audio data requires exactly 128 float32 samples')
    const bytes = Buffer.from(hex, 'hex')
    const buffer = new ArrayBuffer(512)
    const view = new DataView(buffer)
    for (let offset = 0; offset < 512; offset += 4) view.setUint32(offset, bytes.readUInt32LE(offset), nativeLittleEndian)
    return new Float32Array(buffer)
  }
  return { waveform: decode('waveformFloat32'), spectrum: decode('spectrumFloat32') }
}
