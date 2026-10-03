// Decode upload-order RGBA32F words without passing float lanes through JS Number.
export function decodeMeshData(packed) {
  const texWidth = packed.texWidth ?? 256
  const texHeight = packed.texHeight ?? 256
  if (!Number.isSafeInteger(texWidth) || !Number.isSafeInteger(texHeight) || texWidth <= 0 || texHeight <= 0) throw new Error('mesh texture dimensions must be positive integers')
  const nativeLittleEndian = new Uint8Array(new Uint32Array([1]).buffer)[0] === 1
  const decode = (field) => {
    const hex = packed[field]
    if (typeof hex !== 'string' || hex.length % 8 !== 0 || !/^[0-9a-f]*$/i.test(hex)) throw new Error('mesh data must contain whole float32 words')
    const bytes = Buffer.from(hex, 'hex')
    const buffer = new ArrayBuffer(bytes.length)
    const view = new DataView(buffer)
    for (let offset = 0; offset < bytes.length; offset += 4) {
      view.setUint32(offset, bytes.readUInt32LE(offset), nativeLittleEndian)
    }
    return new Float32Array(buffer)
  }
  return { texWidth, texHeight, positionData: decode('positionRgba32f'), normalData: decode('normalRgba32f') }
}
