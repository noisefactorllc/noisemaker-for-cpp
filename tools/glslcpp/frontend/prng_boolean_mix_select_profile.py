"""Authenticated admission for the shader prng() boolean-mix sign fold.

Upstream d0ed94ae rewrote each float ternary in prng() as a per-component
mix expression: mix(-p * 2.0 + 1.0, p * 2.0, greaterThanEqual(p, vec3(0.0))).  The
typed pipeline had no admission for the bvec3 selector result or for the
bool-amount mix overload, so this profile admits exactly those nodes, by
identity, for the programs whose vendored sources carry the construct.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

PROFILE = "prng-boolean-mix-select-v1"
KEYS = frozenset({'synth/noise:noise', 'synth/perlin:perlin', 'synth/shape:shape'})

_SITES = {
    'synth/noise:noise': {
        "raw_sha256": '607378cb929b309b826bca05580769c18e93000faa7afdc69d9b7d57dff6fb7e', "raw_bytes": 18200,
        "normalized_sha256": 'ba444df6355ab4716eaa3991a5c23cb05464d8fbd87d8287076c30eb38c00c64', "normalized_bytes": 17180,
        "functions_sha256": '2de416c61700a1eea1f39127eeec49e315213516c3295d041992e133a205a967',
        "whole_sha256": 'e3eaedcbef505ea5b92650e2b5f95c4438464715baed7da6fedceedfae28e357',
        "interface_sha256": '7088164c2eba12aa590b34b23f5e070f172440c086c5a926b86ded4edc1af080',
        "defines": (('LOOP_OFFSET', 'str', 'int'), ('NOISE_TYPE', 'str', 'int')),
        "mix_spans": ('52:9-52:69',),
        "rel_spans": ('52:38-52:68',),
    },
    'synth/perlin:perlin': {
        "raw_sha256": 'd36fe934e6f0833ba01862b14c11697cc1db9e6a1eaafc690ac9c70438b5ea05', "raw_bytes": 10951,
        "normalized_sha256": 'aa2c831be7adfdd7aec184da0130fae67a858b9592d931be09ec960a042a987b', "normalized_bytes": 7719,
        "functions_sha256": '5351a2562f59a3b5131605194e406bd4f283b7d5f5343015260cc9b5f6f7c766',
        "whole_sha256": '37184ebf8ffdc85205ad6f6b43615cdda6047e2e3941a6f02a91aa4d30b2f8a1',
        "interface_sha256": '854254133f9834f70ad991a07f82a4a77f8cb3f0e9e245fc9a395a66b8b3ab88',
        "defines": (('DIMENSIONS', 'str', 'int'),),
        "mix_spans": ('49:9-49:69',),
        "rel_spans": ('49:38-49:68',),
    },
}


_VARIANTS = {(key, site["defines"]): site for key, site in _SITES.items()}
for _key, _defines, _size, _normalized, _functions, _whole_hash, _interface_hash in (
    ('synth/perlin:perlin', (('DIMENSIONS', 'int', '2'),), 4796,
     'dd1082c7f0860ed2546a902e9e564f9ad5069022a05fadad6c3bb684d38324d3',
     'fad171539eeb1f223418d726163fd6383a823988ae05e096ea9a54be45fee6a6',
     '3c1843a6d9731a096703e0f97983d96596111997cbe0a65a4623f4903537139b',
     'a76eb3e72ae1e7e4c609d1adda3aaece51f5c3f09fd3334547efb20fce5d86a9'),
    ('synth/noise:noise', (('LOOP_OFFSET', 'int', '300'), ('NOISE_TYPE', 'int', '10')), 8437,
     '6e1d26c4ad7d9d7bce5880fd2e227ecf434ac6b877844fa52ec5456a28337180',
     'a515a07a864e8233017b64e4a7cea7b94bb98a4158fe7f24d94140d3b1ff071a',
     '60ac57e915da1e6b5869c59f54a5ac38600d220bfe36bf7b3f1aafb9c23cd073',
     '0992aff6784b95f771a8ea48cdbb40c5ef58286442d640b9f911a9dac3a79d46'),
):
    _VARIANTS[(_key, _defines)] = dict(
        _SITES[_key], defines=_defines, normalized_bytes=_size,
        normalized_sha256=_normalized, functions_sha256=_functions,
        whole_sha256=_whole_hash, interface_sha256=_interface_hash,
        mix_spans=(("48" if "perlin" in _key else "50") + ":9-" + ("48" if "perlin" in _key else "50") + ":69",),
        rel_spans=(("48" if "perlin" in _key else "50") + ":38-" + ("48" if "perlin" in _key else "50") + ":68",))


_VARIANTS.update({('classicNoisedeck/caustic:caustic', (('NOISE_TYPE', 'int', '10'),)): {'raw_sha256': '601d01e7ba6b3a9d97c760c14401541d6d37e03826a83bd3c492491a7abba5d0', 'raw_bytes': 15637, 'normalized_sha256': '6db450d824e81e49a099c2f4e7b1cdcd0e5b1bfcf9204e9da086a7c26c7c1c83', 'normalized_bytes': 7843, 'functions_sha256': '3a2721f36274d69f4a8e4760a4110a2927786d61626034b9a486fac4dde826ec', 'whole_sha256': '90d5be5c5ecf3f46170039cb473f027f48f9a63b759608b220e88e1ce16483a5', 'interface_sha256': '9ef50b877327debe0c933293d1a076f13adfea0dd9abbd128bcbdcf63b9ea1e1', 'defines': (('NOISE_TYPE', 'int', '10'),), 'mix_spans': ('51:9-51:69',), 'rel_spans': ('51:38-51:68',)}, ('classicNoisedeck/caustic:caustic', (('NOISE_TYPE', 'str', 'int'),)): {'raw_sha256': '601d01e7ba6b3a9d97c760c14401541d6d37e03826a83bd3c492491a7abba5d0', 'raw_bytes': 15637, 'normalized_sha256': 'caed95f93d292b25a5420c518d87d380684258abc2d4229bb035151cd53644d7', 'normalized_bytes': 14627, 'functions_sha256': 'b9fa30780bed7d29478782befdebb9fe4c061fb81a498960eb94fcc68acfc1e7', 'whole_sha256': 'e86be8df5622d739e4638ce8e878104f5224c9ba108f66ea5f50b3c0aff0d0ab', 'interface_sha256': '9039cfd719ad2d2cf420bd5095492b1cdbe71252e1995ce7e820fd31c4bd1cba', 'defines': (('NOISE_TYPE', 'str', 'int'),), 'mix_spans': ('52:9-52:69',), 'rel_spans': ('52:38-52:68',)}, ('classicNoisedeck/cellNoise:cellNoise', ()): {'raw_sha256': 'bd71605f96541f445e435ca5f65d5b80c5ee7b1e29b136cea4a63ec30431e651', 'raw_bytes': 9635, 'normalized_sha256': '6aaa3a294d76bd3c75d79849901eae1ee2cdef6f8c34e89704abc8995070d4ea', 'normalized_bytes': 8863, 'functions_sha256': '813ad0c8d741bfe38696430f76bee92da7175e969ca09430bbcde2a3ac298fc9', 'whole_sha256': 'ab13f405a8ebd21b17be38a08b348d695b465f5975fa41a134ead16c9e386447', 'interface_sha256': '63f0a123a2ecd2963b9b9c85e81fd6556d1221d4ca6a5fe737062b4b3eb40ec0', 'defines': (), 'mix_spans': ('61:9-61:69',), 'rel_spans': ('61:38-61:68',)}})
_VARIANTS.update({('classicNoisedeck/moodscape:moodscape', (('COLOR_MODE', 'str', 'int'), ('NOISE_TYPE', 'str', 'int'))): {'raw_sha256': 'c93cc8744c2368446fe6214a80cdc9e6fd8b36b1dee89f511812c7ba2f0145dc', 'raw_bytes': 19551, 'normalized_sha256': 'ed67a8bf8dd0f99d3b8ade11f670af73ecf67fef5fc70b841e3c5d6e8e575bce', 'normalized_bytes': 17707, 'functions_sha256': '7489b386e969e2ffcfa73c718893d1892c740a28eb669da30689c4b2dfc4244a', 'whole_sha256': '302feee7410f1a5ec460631f09a886df7bd527669c8bdfc41ef49d491c97a63b', 'interface_sha256': '2ef5b1630a6f7e612776ac94b5d606a67236c53e20bf1f081e1999bb0315303e', 'defines': (('COLOR_MODE', 'str', 'int'), ('NOISE_TYPE', 'str', 'int')), 'mix_spans': ('62:9-62:69',), 'rel_spans': ('62:38-62:68',)}})
_VARIANTS.update({('classicNoisedeck/splat:splat', ()): {'raw_sha256': '5e334703ddad3c16700adf20d2f1515303a5bef92a5b87bed92ff1a9928cfbf7', 'raw_bytes': 5138, 'normalized_sha256': '6f4f269f6290f39d266ff2ff45089ac23bf15ff7818da557701742fcdced4721', 'normalized_bytes': 4490, 'functions_sha256': '07186a5f13c2d1c78963184c0923b0254033903115b4c1769bcdf5cdf72145a5', 'whole_sha256': '6e05f16afb933a824b4d45b2f92b51f317238b1f16a41d235fb7404b5b202e94', 'interface_sha256': '8b49eada4080e81b2bdd6de71420c17bad578daca1b8a36910b97f5bc2614713', 'defines': (), 'mix_spans': ('56:9-56:69',), 'rel_spans': ('56:38-56:68',)}, ('filter/corrupt:corrupt', ()): {'raw_sha256': 'f5bfb791671606227e8ecb2641c4a28e345c1c951a5405bc9fb3f631354df086', 'raw_bytes': 7490, 'normalized_sha256': '446b01ecb44d020bf0a3ebfddd8f4d29a0b7b566cfff1a2a41dfc8e1b41f0ca7', 'normalized_bytes': 6085, 'functions_sha256': 'aa45e79dd524b7ff6e420487b19a2fe5b87cb3a067f95ba3bafa8bb82202fee9', 'whole_sha256': 'f59921550af0b25694553c64e25f0b0021c3370255756b206c3debf273d19dd0', 'interface_sha256': '76070f0117d763c09779a31acf64bc43f63e214f20f724f1bad7bbbcdfca203c', 'defines': (), 'mix_spans': ('39:9-39:69',), 'rel_spans': ('39:38-39:68',)}, ('filter/lensWarp:lensWarp', ()): {'raw_sha256': '88a3238756968229b41c0cb38266194a601bab9e6eef345ca79bbb271aba88c0', 'raw_bytes': 4102, 'normalized_sha256': '02b5c1b64a39c02c1182e3609a53b5e2effef0ba09e005027da8145c6f757c88', 'normalized_bytes': 3367, 'functions_sha256': '2db1d12a3fcff5d4b53d82663e77c3cad94457fa47113302c896b1afad3ad9e7', 'whole_sha256': 'f941482699cc0fa57783d84ffb39c7f4831204e6307b5b381b7637cd675d7b58', 'interface_sha256': 'b388ce2707dc6a3b4546b62584a97ec7cf48d60de67738af6a79e19c37ffdb18', 'defines': (), 'mix_spans': ('32:9-32:69',), 'rel_spans': ('32:38-32:68',)}, ('filter/warp:warp', ()): {'raw_sha256': '9f12ebb2a1b93f3e957db6f2ad5494f06975f9f711ffd6c2392fb3f2c18fcc83', 'raw_bytes': 3164, 'normalized_sha256': '698f6871b9c2167fe76b635a3d87766cf2e24d4a2e364d2740d584c3f444b14d', 'normalized_bytes': 2761, 'functions_sha256': 'aff46c15c38dd95b00bfb7206006601c2daf785b101d881dfaacdd2ddd0e9b78', 'whole_sha256': '75965f7b0d644761db5338e5dd34d445eb621a82dd19ebb91062800cc3165c84', 'interface_sha256': '5ccbee6841ee74999347daa2629d127d6d92bb7905d8e4a93b9cba5221e0bae9', 'defines': (), 'mix_spans': ('35:9-35:69',), 'rel_spans': ('35:38-35:68',)}, ('mixer/cellSplit:cellSplit', ()): {'raw_sha256': 'e11288bff92d1c26ea32d23ef1710cb5237d5666f7cabf846b80e21b9884a6b2', 'raw_bytes': 4127, 'normalized_sha256': 'c8bf3be87a2c59acef9965056e617ae925509e63adf6de0efcd866263b69ea74', 'normalized_bytes': 3371, 'functions_sha256': 'c469f7052c46db7d57f15ec67ddce2782494834259c296076eeb4613e4411b65', 'whole_sha256': '32cfeddf313bc9aa9647b4aab33724f28101eb63ac9aac688d7dca656a82937f', 'interface_sha256': '56270d5c0b1dc1358aa7e7c690a5686339f5b713575fdd2a571a551b49bcdc00', 'defines': (), 'mix_spans': ('38:9-38:69',), 'rel_spans': ('38:38-38:68',)}, ('synth/cell:cell', ()): {'raw_sha256': 'b16831bd6f84c798e6129f47ea81e0a8ab7041acd531c946fd75f353b0340d82', 'raw_bytes': 3882, 'normalized_sha256': '0aa24477d6b9a964f8bcf2498189ac7e2bdb7bf944818eb8d2715cf670d1c091', 'normalized_bytes': 3233, 'functions_sha256': 'cf4f173723f60ec5e56f991af901275f0f655e9aae2b4872b6344f2c530dbe9d', 'whole_sha256': 'd800a2fe004cb536b312cd56758d207463abbed49a959b23c0acce25ff3b9436', 'interface_sha256': 'a045ef59004708d2605bb0ffd076930afca1f31dea6622c9134edb686aac4d13', 'defines': (), 'mix_spans': ('48:9-48:69',), 'rel_spans': ('48:38-48:68',)}, ('synth/gradient:gradient', ()): {'raw_sha256': '05ad693f0c2d3cb590139c3cbd7cb5430843f36b09b9c2478d571a5aa0ec19a6', 'raw_bytes': 5508, 'normalized_sha256': '6afb5b6b702884b545265cad82ec39b7f1c4857daa55fc3f5f3c36a0adf8b04f', 'normalized_bytes': 4578, 'functions_sha256': '066ac9cccb6e2798ea65b30b7bf7fbfac2a2f9c53389f7e89366ee988d963422', 'whole_sha256': '1dc0c1bfdf6f43804c1f33c0e8b843ba298309a1182509a84b317787f8d68c6a', 'interface_sha256': '02af515fc3b874137faf3230c31b88339e81d27dbb55ca0150ceb70b6b9053ed', 'defines': (), 'mix_spans': ('69:9-69:69',), 'rel_spans': ('69:38-69:68',)}})
_VARIANTS.update({('classicNoisedeck/noise:noise', (('COLOR_MODE', 'str', 'int'), ('LOOP_OFFSET', 'str', 'int'), ('METRIC', 'str', 'int'), ('NOISE_TYPE', 'str', 'int'), ('REFRACT_MODE', 'str', 'int'))): {'raw_sha256': '276b5ca70973c57057adb389d8cb49946a0bdedb4486ffafbaa8e8e876d14a9a', 'raw_bytes': 32519, 'normalized_sha256': '5d8861de4028d839f446180867553db866a4f0663284e2d3ccfb1a04ed58311e', 'normalized_bytes': 25777, 'functions_sha256': 'a5952bf2444ece0632626f82bbcd9b4c11a658878df25cafd99cdf6028fd3360', 'whole_sha256': 'b8b40b218851cbc81ed7d359e6ad07d943a782e5797f8e9ecb17847854db4d17', 'interface_sha256': 'e4661d4261fef2a0d5758a0ca817ea53c4de7ff33de541a720fd29c417dd4edf', 'defines': (('COLOR_MODE', 'str', 'int'), ('LOOP_OFFSET', 'str', 'int'), ('METRIC', 'str', 'int'), ('NOISE_TYPE', 'str', 'int'), ('REFRACT_MODE', 'str', 'int')), 'mix_spans': ('71:9-71:69',), 'rel_spans': ('71:38-71:68',)}})
_VARIANTS.update({('classicNoisedeck/noise3d:noise3d', (('NOISE_TYPE', 'int', '12'),)): {'raw_sha256': 'ad1bbcfe511216aadec7d0bfbf53e1b1317a333bcc0d31cd29203c6a73b83cd3', 'raw_bytes': 19646, 'normalized_sha256': 'eaaf02a485965edee08a33fb9e441521a3c92268d779fdb12bb50c112bc6dbf0', 'normalized_bytes': 14181, 'functions_sha256': 'be22196a27de3743beb469dfe445d7487554655b2ef31c7e75b5af45093a4ba1', 'whole_sha256': 'ef8e54ce28095b6977aa3afe9a7912ac8203c5fcd7513ede5a26de02063c98cf', 'interface_sha256': 'ecff17479e5c80788bebd781b1500f74a8eb325ad17c60362ff4a03a168ffa7a', 'defines': (('NOISE_TYPE', 'int', '12'),), 'mix_spans': ('50:9-50:69',), 'rel_spans': ('50:38-50:68',)}, ('classicNoisedeck/noise3d:noise3d', (('NOISE_TYPE', 'str', 'int'),)): {'raw_sha256': 'ad1bbcfe511216aadec7d0bfbf53e1b1317a333bcc0d31cd29203c6a73b83cd3', 'raw_bytes': 19646, 'normalized_sha256': '2165dd92b09c9bec79d215cfcbbea2d7ab537f938f70b889432cd39708432664', 'normalized_bytes': 15275, 'functions_sha256': '4aeb2870430f9768fc902c45256a149038851c39745fee5da3355c456a3bacb3', 'whole_sha256': '823ec8777f28ae2075667f90126118aa4b1c2c2412b90af30d5e8b4946eb8389', 'interface_sha256': '269e1751ec847d4b86acc44ad65eb44fca4c702abe1f4362d8aca37f779c9a35', 'defines': (('NOISE_TYPE', 'str', 'int'),), 'mix_spans': ('51:9-51:69',), 'rel_spans': ('51:38-51:68',)}, ('synth/gabor:gabor', ()): {'raw_sha256': '52dbe8d5ef5ae2bebf89096f029d9f9074499bd025cbbff6e9085da95cec5da8', 'raw_bytes': 3939, 'normalized_sha256': '6d8817fff6dbb4679ec5a98c0d351baec0695239e29e107c2a1fe96a6c7e42eb', 'normalized_bytes': 3246, 'functions_sha256': '9945f2a70f4c77c4d6ff5508a0e45c75c0a1c1933d07b3868d48cafb90035dae', 'whole_sha256': 'a4b306dea09dea34136ea0d1c33c46c3868a3a5e35808fe71ec7daa0e10c53c8', 'interface_sha256': '0b3943f7173cc3b4ae66827781a689a0ed9ab5447607a61882accaf5f037c55b', 'defines': (), 'mix_spans': ('35:9-35:69',), 'rel_spans': ('35:38-35:68',)}})
_VARIANTS.update({('synth/shape:shape', (('LOOP_A_OFFSET', 'str', 'int'), ('LOOP_B_OFFSET', 'str', 'int'))): {'raw_sha256': '3e573dc301f56d326519ab42d6fa5b4edf50e98dda55c8d540425f61d8ce5ad7', 'raw_bytes': 15979, 'normalized_sha256': '18da24f2dc73b9b51e78ee6d0a835baa9e62418c29767a137a19fb7a56b5ada9', 'normalized_bytes': 14922, 'functions_sha256': '68cdb8e3d2ff2d5d8fb2e4075cfbba0bc1f0d0625f1b15bf5841afdc9e648fd8', 'whole_sha256': '12de9524bc33ee4fb40480ad959ae20fbe1281df80550ecf8644edcaf1d801a0', 'interface_sha256': 'aa2b83808726d400bf4d89e57df4e6c0a3bd85bc3efcb5a832d84e635a955609', 'defines': (('LOOP_A_OFFSET', 'str', 'int'), ('LOOP_B_OFFSET', 'str', 'int')), 'mix_spans': ('63:9-63:69',), 'rel_spans': ('63:38-63:68',)}})
_VARIANTS[('synth/shape:shape', (
    ('LOOP_A_OFFSET', 'int', '40'), ('LOOP_B_OFFSET', 'int', '30')))] = {
    'raw_sha256': '3e573dc301f56d326519ab42d6fa5b4edf50e98dda55c8d540425f61d8ce5ad7',
    'raw_bytes': 15979,
    'normalized_sha256': 'a662c6e864f59053524bc4e4e15a82009bebc244208e7148fc415cb775199bba',
    'normalized_bytes': 14678,
    'functions_sha256': 'a239f20714900d2df91a1acd5717bbe59688a510cd654ce61bc1fc367b69ba4c',
    'whole_sha256': 'e52daefb84c7e254f82e157779557d5549b1746da7ff20214ed5c928b89942b3',
    'interface_sha256': '82779e53f33621af6e3167a5ced7b0001047aba7a9d7a2fde881512fafbfa978',
    'defines': (('LOOP_A_OFFSET', 'int', '40'), ('LOOP_B_OFFSET', 'int', '30')),
    'mix_spans': ('61:9-61:69',),
    'rel_spans': ('61:38-61:68',),
}
_SITES.update({key: site for (key, _), site in _VARIANTS.items()})

# cf95f49c sync: recaptured variants for the hsv2rgb hue-wrap range.
_VARIANTS.update({
    ('classicNoisedeck/caustic:caustic', (('NOISE_TYPE', 'int', '10'),)): {'raw_sha256': '601d01e7ba6b3a9d97c760c14401541d6d37e03826a83bd3c492491a7abba5d0', 'raw_bytes': 15637, 'normalized_sha256': '6db450d824e81e49a099c2f4e7b1cdcd0e5b1bfcf9204e9da086a7c26c7c1c83', 'normalized_bytes': 7843, 'functions_sha256': '3a2721f36274d69f4a8e4760a4110a2927786d61626034b9a486fac4dde826ec', 'whole_sha256': '90d5be5c5ecf3f46170039cb473f027f48f9a63b759608b220e88e1ce16483a5', 'interface_sha256': '9ef50b877327debe0c933293d1a076f13adfea0dd9abbd128bcbdcf63b9ea1e1', 'defines': (('NOISE_TYPE', 'int', '10'),), 'mix_spans': ('51:9-51:69',), 'rel_spans': ('51:38-51:68',)},
    ('classicNoisedeck/caustic:caustic', (('NOISE_TYPE', 'str', 'int'),)): {'raw_sha256': '601d01e7ba6b3a9d97c760c14401541d6d37e03826a83bd3c492491a7abba5d0', 'raw_bytes': 15637, 'normalized_sha256': 'caed95f93d292b25a5420c518d87d380684258abc2d4229bb035151cd53644d7', 'normalized_bytes': 14627, 'functions_sha256': 'b9fa30780bed7d29478782befdebb9fe4c061fb81a498960eb94fcc68acfc1e7', 'whole_sha256': 'e86be8df5622d739e4638ce8e878104f5224c9ba108f66ea5f50b3c0aff0d0ab', 'interface_sha256': '9039cfd719ad2d2cf420bd5095492b1cdbe71252e1995ce7e820fd31c4bd1cba', 'defines': (('NOISE_TYPE', 'str', 'int'),), 'mix_spans': ('52:9-52:69',), 'rel_spans': ('52:38-52:68',)},
    ('classicNoisedeck/cellNoise:cellNoise', ()): {'raw_sha256': 'bd71605f96541f445e435ca5f65d5b80c5ee7b1e29b136cea4a63ec30431e651', 'raw_bytes': 9635, 'normalized_sha256': '6aaa3a294d76bd3c75d79849901eae1ee2cdef6f8c34e89704abc8995070d4ea', 'normalized_bytes': 8863, 'functions_sha256': '813ad0c8d741bfe38696430f76bee92da7175e969ca09430bbcde2a3ac298fc9', 'whole_sha256': 'ab13f405a8ebd21b17be38a08b348d695b465f5975fa41a134ead16c9e386447', 'interface_sha256': '63f0a123a2ecd2963b9b9c85e81fd6556d1221d4ca6a5fe737062b4b3eb40ec0', 'defines': (), 'mix_spans': ('61:9-61:69',), 'rel_spans': ('61:38-61:68',)},
    ('classicNoisedeck/moodscape:moodscape', (('COLOR_MODE', 'str', 'int'), ('NOISE_TYPE', 'str', 'int'))): {'raw_sha256': 'c93cc8744c2368446fe6214a80cdc9e6fd8b36b1dee89f511812c7ba2f0145dc', 'raw_bytes': 19551, 'normalized_sha256': 'ed67a8bf8dd0f99d3b8ade11f670af73ecf67fef5fc70b841e3c5d6e8e575bce', 'normalized_bytes': 17707, 'functions_sha256': '7489b386e969e2ffcfa73c718893d1892c740a28eb669da30689c4b2dfc4244a', 'whole_sha256': '302feee7410f1a5ec460631f09a886df7bd527669c8bdfc41ef49d491c97a63b', 'interface_sha256': '2ef5b1630a6f7e612776ac94b5d606a67236c53e20bf1f081e1999bb0315303e', 'defines': (('COLOR_MODE', 'str', 'int'), ('NOISE_TYPE', 'str', 'int')), 'mix_spans': ('62:9-62:69',), 'rel_spans': ('62:38-62:68',)},
    ('classicNoisedeck/noise:noise', (('COLOR_MODE', 'str', 'int'), ('LOOP_OFFSET', 'str', 'int'), ('METRIC', 'str', 'int'), ('NOISE_TYPE', 'str', 'int'), ('REFRACT_MODE', 'str', 'int'))): {'raw_sha256': '276b5ca70973c57057adb389d8cb49946a0bdedb4486ffafbaa8e8e876d14a9a', 'raw_bytes': 32519, 'normalized_sha256': '5d8861de4028d839f446180867553db866a4f0663284e2d3ccfb1a04ed58311e', 'normalized_bytes': 25777, 'functions_sha256': 'a5952bf2444ece0632626f82bbcd9b4c11a658878df25cafd99cdf6028fd3360', 'whole_sha256': 'b8b40b218851cbc81ed7d359e6ad07d943a782e5797f8e9ecb17847854db4d17', 'interface_sha256': 'e4661d4261fef2a0d5758a0ca817ea53c4de7ff33de541a720fd29c417dd4edf', 'defines': (('COLOR_MODE', 'str', 'int'), ('LOOP_OFFSET', 'str', 'int'), ('METRIC', 'str', 'int'), ('NOISE_TYPE', 'str', 'int'), ('REFRACT_MODE', 'str', 'int')), 'mix_spans': ('71:9-71:69',), 'rel_spans': ('71:38-71:68',)},
    ('classicNoisedeck/noise3d:noise3d', (('NOISE_TYPE', 'int', '12'),)): {'raw_sha256': 'ad1bbcfe511216aadec7d0bfbf53e1b1317a333bcc0d31cd29203c6a73b83cd3', 'raw_bytes': 19646, 'normalized_sha256': 'eaaf02a485965edee08a33fb9e441521a3c92268d779fdb12bb50c112bc6dbf0', 'normalized_bytes': 14181, 'functions_sha256': 'be22196a27de3743beb469dfe445d7487554655b2ef31c7e75b5af45093a4ba1', 'whole_sha256': 'ef8e54ce28095b6977aa3afe9a7912ac8203c5fcd7513ede5a26de02063c98cf', 'interface_sha256': 'ecff17479e5c80788bebd781b1500f74a8eb325ad17c60362ff4a03a168ffa7a', 'defines': (('NOISE_TYPE', 'int', '12'),), 'mix_spans': ('50:9-50:69',), 'rel_spans': ('50:38-50:68',)},
    ('classicNoisedeck/noise3d:noise3d', (('NOISE_TYPE', 'str', 'int'),)): {'raw_sha256': 'ad1bbcfe511216aadec7d0bfbf53e1b1317a333bcc0d31cd29203c6a73b83cd3', 'raw_bytes': 19646, 'normalized_sha256': '2165dd92b09c9bec79d215cfcbbea2d7ab537f938f70b889432cd39708432664', 'normalized_bytes': 15275, 'functions_sha256': '4aeb2870430f9768fc902c45256a149038851c39745fee5da3355c456a3bacb3', 'whole_sha256': '823ec8777f28ae2075667f90126118aa4b1c2c2412b90af30d5e8b4946eb8389', 'interface_sha256': '269e1751ec847d4b86acc44ad65eb44fca4c702abe1f4362d8aca37f779c9a35', 'defines': (('NOISE_TYPE', 'str', 'int'),), 'mix_spans': ('51:9-51:69',), 'rel_spans': ('51:38-51:68',)},
})
_SITES.update({key: site for (key, _), site in _VARIANTS.items() if key in ('classicNoisedeck/caustic:caustic', 'classicNoisedeck/cellNoise:cellNoise', 'classicNoisedeck/moodscape:moodscape', 'classicNoisedeck/noise3d:noise3d', 'classicNoisedeck/noise:noise',)})

KEYS = frozenset(_SITES)

def requires_profile(program: object) -> bool:
    site = _SITES.get(program.key)
    return site is not None and hashlib.sha256(
        program.raw_source.encode("utf-8")).hexdigest() == site["raw_sha256"]


@dataclass(frozen=True, slots=True)
class PrngBooleanMixSelectProof:
    key: str
    mix_nodes: tuple[object, ...]
    relationals: tuple[object, ...]
    omitted_nodes: tuple[object, ...] = ()

    @property
    def live_mix_nodes(self) -> tuple[object, ...]:
        return tuple(node for node in self.mix_nodes
                     if not any(node is omitted for omitted in self.omitted_nodes))

    @property
    def live_relationals(self) -> tuple[object, ...]:
        return tuple(node for node in self.relationals
                     if not any(node is omitted for omitted in self.omitted_nodes))

    @property
    def consumed_objects(self) -> tuple[object, ...]:
        return self.mix_nodes + self.relationals


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    item = value.span
    return (f"{item.start_line}:{item.start_column}-"
            f"{item.end_line}:{item.end_column}")


def _whole(program: object) -> str:
    return _sha((program.key, program.source, program.raw_source,
                 program.declarations, program.functions, program.resources,
                 program.body_status, program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.counted_loop_proof,
                 program.preprocessor_defines))


def _interface(program: object) -> str:
    return _sha((program.declarations, program.resources,
                 program.local_type_names, program.structs,
                 program.uniform_blocks, program.interface_symbols,
                 program.builtin_symbols, program.preprocessor_defines))


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _walk(value: object):
    yield value
    for expression in getattr(value, "expressions", ()) or ():
        yield from _walk(expression)
    for child in getattr(value, "children", ()) or ():
        yield from _walk(child)


def authenticate(program: object, source_hash: str | None,
                 profile: str | None) -> PrngBooleanMixSelectProof:
    """Authenticate the program and return only nodes it owns."""
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    site = _VARIANTS.get((program.key, defines))
    if site is None or source_hash != site["raw_sha256"]:
        raise _fail("unselected key or exact caller source hash required")
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    if (len(raw) != site["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != site["raw_sha256"]
            or len(normalized) != site["normalized_bytes"]
            or hashlib.sha256(normalized).hexdigest() != site["normalized_sha256"]
            or defines != site["defines"]
            or program.body_status != "analyzed"
            or any(getattr(program, field) is not None for field in (
                "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
                "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof"))
            or _sha(program.functions) != site["functions_sha256"]
            or _whole(program) != site["whole_sha256"]
            or _interface(program) != site["interface_sha256"]):
        raise _fail("source, define, or typed-tree fingerprint mismatch")
    mixes, relationals = [], []
    for function in program.functions:
        for statement in function.body:
            for expression in statement.expressions:
                for item in _walk(expression):
                    if (getattr(item, "kind", None) == "builtin"
                            and getattr(item, "callee", None) == "mix"):
                        children = item.children
                        if (len(children) == 3
                                and getattr(children[2], "callee", None)
                                == "greaterThanEqual"):
                            mixes.append(item)
                            relationals.append(children[2])
    if (tuple(_span(item) for item in mixes) != site["mix_spans"]
            or tuple(_span(item) for item in relationals)
            != site["rel_spans"]):
        raise _fail("mix-select site census mismatch")
    for mix_node, rel in zip(mixes, relationals):
        if (mix_node.type.display() != "vec3"
                or len(mix_node.children) != 3
                or tuple(child.type.display() for child in mix_node.children)
                != ("vec3", "vec3", "bvec3")
                or rel.type.display() != "bvec3"
                or len(rel.children) != 2
                or tuple(child.type.display() for child in rel.children)
                != ("vec3", "vec3")):
            raise _fail("mix-select shape mismatch")
    omitted_nodes = ()
    if program.key == "classicNoisedeck/noise3d:noise3d":
        from .noise3d_dead_globals import authenticate_noise3d_dead_globals
        dead = authenticate_noise3d_dead_globals(program, source_hash)
        dead_nodes = tuple(node for function in dead.dead_functions
                           for statement in function.body for node in _walk(statement))
        omitted_nodes = tuple(node for node in (*mixes, *relationals)
                              if any(node is item for item in dead_nodes))
    return PrngBooleanMixSelectProof(program.key, tuple(mixes),
                                     tuple(relationals), omitted_nodes)


__all__ = ["KEYS", "PROFILE", "PrngBooleanMixSelectProof", "authenticate"]
