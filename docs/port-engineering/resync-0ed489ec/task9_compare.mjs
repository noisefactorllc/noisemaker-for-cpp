// Diffs the live output of task9_oracle_regenerator.mjs (piped in on stdin,
// tab-separated `key\tfloats=..\trgba=..\tfirst=..\tprobes=..`) against the
// frozen fixture table in tests/test_typed_slice.cpp. Usage:
//   NOISEMAKER_CPU_ROOT=... node task9_oracle_regenerator.mjs | node task9_compare.mjs
const FROZEN = {
  'filter/celShading:celShadingBlend': ['3040fca866a32e77c2d5828672a9d983fd8b78c8f19e81030444b7f922cc144a', '998a939393905a859371711b5c971f0435ed757720ac5b5a9348e59d652a6409', '3e0a9e59'],
  'filter/chroma:chroma': ['efc59e60e7b127541dbb28cf18d5981144fc4a22f02d4f6d710be29ea0ac06fe', '72ef0585ff112ea147febd8ede9f8d3965215513c44ddf0feb188790f371c637', '3f4234f7'],
  'filter/chrome:chMap': ['5d0c6dd88fe0a39b97b994002b7431214d59760f9133c2ff40d1e3bebd8ec119', 'bc19edaad2c576252a6f9ea3420422d08286039b8cc15f88aa0e7a6734f18bf8', '3d70c7b5'],
  'filter/colorReplace:colorReplace': ['f672cb72086923fa32c34cc12915196bccd211ea450d6cac6dee39649b4d3814', '33c8b3e38c7d93521a58581c2b1bc0e56547d2afc8d5673aeddca4d2bf26d0ff', '3d9c2f9c'],
  'filter/deriv:deriv': ['43e591217a059e9a86f3e00e52a91b0539c2cc3783619dd0f45de04c292fd3a2', '6a3cbb07be0a133257bd1ca518d82c8269c5b47bd4abd975fe1cb530b70c900e', '3c88d638'],
  'filter/lensFlare:lensFlare': ['046d8dc804bf93f97533a85f05783b14a6dcedf09afede6a3660e600676d8599', '42d035c4d765ef017d27b641bb5a2a96f03122ca19032c1e02233b8d7915cbc4', '3d85d166'],
  'filter/mosaicTiles:mosaicTiles': ['b45240877494b59e366f9d9441bd2e125365bcd87f000ca363839cdc8bd725b0', 'bacfcc449e6470bfa16347c7b00cf9a2807ec433a060282b32358f2b39a273e1', '3c311fc9'],
  'filter/photocopy:pcCombine': ['5c30639723acd4eed15826649692300488800a81c4c20d0b9a2cdafb4bfb4405', '76d6b92b4fb7f0c8e4f465da28246117a0ad5ac0c9c45e43085d1280f0877c6f', '3da3d70a'],
  'filter/relief:rlShade': ['1dba0f21095568d3f62d27d313993dfaa6bae04c1fb0fc81156d583ea3a2d1d6', 'f5205caa03ccc976eefc1c41b9f535ea578a23510cf6154642b16634da32abe6', '3f078889'],
  'filter/ridge:ridge': ['14e083e0d2e604d0b5559ebbdd175316ae313160e5aca89c468678ef3932eff9', '5d220bfe0488a6b32a233b82932edee6b8b5e094c478b95f54289d6e0edc1b8b', '3eba3eaa'],
  'filter/scatter:scatterJitter': ['3894d5739e765cf71a39a082abb8315bfd5fac4a7d6be6c4f8a8cf9b87ae5c8c', 'd3425ff7218c66a0a0711e3ed96f3c343df410227e22cececf9ad51dc48c42be', '3df0f0f1'],
  'filter/simpleAberration:chromaticAberration': ['09c9d93ea78ddb0f877dd993f6af3f5b7d7ffd9c10d05fe4dc2f4b505f1af7e6', '42c44f9ac2cd9b55e1dc92abd18afa3960b6a7982d44e9463db03717b207b760', '3e30b0b1'],
  'filter/text:text': ['a6dba9bbe4b6dfeab15bfc45089f5255e359d292a1a7199ca76ce42da549b134', 'cde2a1348bc93ad9c33a91b3ae4c3c711af183490b365ffd967fd296f9e7e2de', '3f15f244'],
  'filter/unsharpMask:usmCombine': ['dcb8cd1ae6f41bba9ab35d807a4d89d158605be5a2fb5b8bd199def2d06970a5', 'c5c85cddd59a4e9c9c6e98e316ad8de4074dffbd4787c841a5cd1b6f80829630', '00000000'],
  'filter/watercolor:wcComposite': ['409c8f37bb8778750cedc218f2ca6d488ad6fffe1c090c786d7e3c582bde5a3b', '1bdc0c3ae9f57ef445f25fa3e3cac55cbcfbba28745b0a2af58c885a6d514bc4', '3d3f48c0'],
  'filter/watercolor:wcSeed': ['29f8cb0bcb53dac6c6c0f32405d5ee0670617a236c5b59c2aa9d3536637abe0a', 'b758a60117b29acbcaa0d2e74eaef9487d06f80d1cf5363df30967a981e0df2f', '3d50d0d1'],
}

let input = ''
process.stdin.on('data', (chunk) => { input += chunk })
process.stdin.on('end', () => {
  let matched = 0
  let total = 0
  for (const line of input.trim().split('\n')) {
    const [key, floatsPart, rgbaPart, firstPart] = line.split('\t')
    const floats = floatsPart.replace('floats=', '')
    const rgba = rgbaPart.replace('rgba=', '')
    const first = firstPart.replace('first=0x', '')
    const frozen = FROZEN[key]
    if (!frozen) { console.log(`${key}: NO FROZEN ENTRY`); continue }
    total += 1
    const [ffloats, frgba, ffirst] = frozen
    const floatsOk = floats === ffloats
    const rgbaOk = rgba === frgba
    const firstOk = first === ffirst
    if (floatsOk && rgbaOk && firstOk) { matched += 1; console.log(`${key}: MATCH`) }
    else console.log(`${key}: DIFF floats=${floatsOk} rgba=${rgbaOk} first=${firstOk} (mine first=${first} frozen first=${ffirst})`)
  }
  console.log(`\n${matched}/${total} matched`)
})
