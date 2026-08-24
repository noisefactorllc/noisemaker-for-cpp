"""Closed exact-identity admission for seven scalar ``uint`` XOR carriers.

Each carried program has exactly three live scalar XOR nodes.  They are the
ordered children of one ``uvec3`` constructor, so JavaScript's signed scalar
``^`` is immediately materialized as the same unsigned 32-bit lane word that
C++ obtains from ``std::uint32_t ^ std::uint32_t``.  This module authenticates
that parent role and the complete surrounding program; it is not a general
scalar-bitwise capability.
"""

from __future__ import annotations

import hashlib
import math

from .typed_ir import TypedExpression, TypedProgram, TypedStatement


PROFILE = "scalar-uint-xor-v1"

# Generated from the pinned corpus by the checked read-only profile probe
# documented in docs/port-engineering/bitops/grain-parity.  Tuples named
# owner/site/parent deliberately retain hashes at every structural layer so a
# refrozen coarse program digest cannot absorb a node mutation.
_PROFILES: dict[str, dict[str, object]] = {
    "filter/grain:grain": {
        "raw_bytes": 8796,
        "raw_sha256": "6edf8deec35e2fa3a32fc150c2be8cb6d71a9356c1c7a3cff5bd3c6c7df764f0",
        "normalized_bytes": 8592,
        "normalized_sha256": "b667ff2a2ba0a9620220cd4821651fccfed930fd385dd1cadb3d1f91eb7ac09d",
        "functions_sha256": "3197ffd53c0eb8500732d7e9da6d5eacf159d363e05fbde1d66693372a406886",
        "whole_program_sha256": "5889e908ebe6309561c2c40d05258d033814c67ff18a5cef5ebcec5ce1e68c22",
        "interface_sha256": "1462c07fce4755c6862e77d5ae5c3795490d4408ab4287e4e1235299aff71672",
        "defines": (), "declaration_count": 18, "function_count": 12,
        "function_inventory_sha256": "da1d1102f3be0aa30ca29b3d704c5acd5da5f589571a07eff3dccf0a7b551538",
        "bindings_sha256": "f1064d3e1256e0e8cb94e13b40fa6dc0dc287502d6b9ded8a5ea3cc6adc694a4",
        "resources": (("inputTex", "resolution", "tileOffset", "fullResolution",
                       "renderScale", "alpha", "time", "pause"),
                      ("inputTex",), ("fragColor",), True, False),
        "loop": (0, 0, 0, 0, 0, True),
        "owner": (60, "random_from_cell_3d", "float", 2, 3, "50:1-58:2",
                  "8d1bed8fcd5a5a9f7e15c4773e96af849e0079fde6f7d9c77f03cda66532ff74",
                  "e5461ac2b097783d056509f1c764ec15fc3b68e513c84541fb8034ba3682b70d"),
        "parent": ("51:20-55:6", "2ac1cf7bd1b9a4cbc1c2d5eee2ec47b0bd395ec4977100a268cd095714739fdc"),
        "sites": (
            ("52:9-52:28", "8100d099ade3c7427e31bcc6b4c1822d85e30488125a7a6d797225ee82184d11", "c414ea511480f7e37c38f6c1760557e525343ee14202f670275beb66ace2e8b2", "3f3b0b4b05304f3b257c7d49ae595edb6150bb9df498753e6f3f5eac2bb4d8e0", 0),
            ("53:9-53:58", "e5192eea3ce29a2f70cbce14e54e8be3126f57aa33cfd15d13114a5e503a1d49", "04dff82e3298c9b7602de7ce98a849835c0e825384a21688ee5ec0baa61ce4a5", "51fc9296a0d88b9fdd06c4e3a9bd18960e7795b5e762fd260a83b6b7e0bf2b4a", 1),
            ("54:9-54:58", "efc0ca3f7acee72aa885b6d83d857d3a728a14c27f11de37db485f427e309b8a", "6dd4e6c55d0e2c6b40e5824cfea71fb6086d2584c72a04abf75a1ba4bf6bfa1f", "1a6222be66d8f8ab579b1edc97a1ce02a586e19b297eaee54b93170f61c0af46", 2)),
        "scalar_census_sha256": "7edbed4ebd764437c87c25db95b2941357fd2a77f8774c7c06c215c59d8fd092",
        "call_graph_sha256": "4c2c460e70564d0f66bbad71dd20d8acbe85110b3268a8025e696b8a83270d6b",
        "reachable": (53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64),
        "unreachable": (),
    },
    "classicNoisedeck/bitEffects:bitEffects": {
        "raw_bytes": 12745, "raw_sha256": "03194d61241ec307787d78c9b6d797b520c35c972c938aa701181b8340fa2e40",
        "normalized_bytes": 8169, "normalized_sha256": "70c88967c308368f81a8739296786c3e501005e536e987446bdc9c1dc93b7bb0",
        "functions_sha256": "c2ffa4525ea4f39ba9e2395e2e755f580d450b645dee628408ddb089281377f5",
        "whole_program_sha256": "5156fbfe252da7e0be21a216e420ca385aac31ab6d4e658a842a5baf4030a234",
        "interface_sha256": "22a5c8be48bbe78e87c503b1bbce3bdfeead3e452259dd46057ceccd1f2dc664",
        "defines": (("COLOR_SCHEME", "int", "20"), ("FORMULA", "int", "0"),
                    ("INTERP", "int", "0"), ("MASK_COLOR_SCHEME", "int", "1"),
                    ("MASK_FORMULA", "int", "10"), ("MODE", "int", "1")),
        "declaration_count": 17, "function_count": 30,
        "function_inventory_sha256": "d0f7f67f02c72ad86e06c9955c9a797adeae9b349e7a45fa807e59e2624fc428",
        "bindings_sha256": "730257aba4308e0b1c50795293d90d2ad4b5cbe8c64960aa3bad9ca6e728afbc",
        "resources": (("time", "seed", "resolution", "tileOffset", "fullResolution",
                       "n", "scale", "rotation", "speed", "tiles", "complexity",
                       "hueRange", "hueRotation", "baseHueRange"), (),
                      ("fragColor",), False, False),
        "loop": (0, 0, 0, 0, 0, True),
        "owner": (111, "randomFromLatticeWithOffset", "vec3", 5, 18, "80:1-112:2",
                  "0eee64bfb2c4aff2a2453b12c7b7d7155794254207aace27b033d187367ed466",
                  "3d9d0a24cd71683493d35655cdaa4c50edfc605c834e8b08ca723a49a0740540"),
        "parent": ("98:20-102:6", "7270a44c84d15e57b45452396e6d9f98a018b54bc68952b7dcfe6021e26dece4"),
        "sites": (
            ("99:10-99:46", "0beb3cdd2d124ab9ffe121b511113e638d3067682c3009c818362a61e9ddead9", "2c1c9982ebbae0d9b21bf38bbe51cf3afcfb046590d6bd54462bb984ce3614e6", "2ef6f0a578ea0374617c41386753bae797f1e0c8be25c7a9549828f9656f2622", 0),
            ("100:10-100:46", "052b8139537615dd7d5407e5f79835b6817d8347b5b6fd3cf86bf5aac214fe8f", "01406ca28dfedc2e0db2be3904b97ee89e06a864c76bdd9d34e80daebe1d7ccb", "5cc578159fc9a578f664deafc376b62fa3081e23974ae5b9e53f52ecfb7ef664", 1),
            ("101:10-101:47", "89c933e13eea0b6619023a7554bffb353eb1bd8c22890671cb91390823a66d8b", "963358d9f644949913dfe9a2ff1bbe226aa83bbffba8065f89aea8e6b95180ef", "abc3b98a346ae28191278ff397276506256705cdb61501533ce366c828c411e5", 2)),
        "scalar_census_sha256": "fd8b31ca66c1f6e53e3bd66b6d6d2ee31fd7e59443c5eb7b6ac0341106de3a19",
        "call_graph_sha256": "84cfb6a08e117ad0907eac1a6b7b58e4e58a74e330558a2d0380016bbd8b36d4",
        "reachable": (92, 93, 95, 97, 98, 99, 100, 101, 102, 108, 109, 111),
        "unreachable": (87, 88, 89, 90, 91, 94, 96, 103, 104, 105, 106, 107,
                        110, 112, 113, 114, 115, 116),
    },
    "classicNoisedeck/kaleido:kaleido": {
        "raw_bytes": 27567, "raw_sha256": "3a155a9bf64f9e700dd66a77c4195df113d9e85228bde56b1cf410944aaeb8b9",
        "normalized_bytes": 21817, "normalized_sha256": "d31299ee69dd0c41965209860ef60a4ad2abf762229cc340383dce2646c6cc1d",
        "functions_sha256": "2ffb48e5f118844d675f9741ccbf7e831ce2f7cfe4609b24777ddb5fb67887ff",
        "whole_program_sha256": "bae48e72088ee01b07a1c8cfcba2398df87e2baf64284eebe750665e2aebc749",
        "interface_sha256": "666586f65044abc1a147a7c3007f376fde3833c275f5f25bce9b6027b7eaa717",
        "defines": (("DIRECTION", "int", "2"), ("KERNEL", "int", "0"),
                    ("LOOP_OFFSET", "int", "10"), ("METRIC", "int", "0")),
        "declaration_count": 17, "function_count": 43,
        "function_inventory_sha256": "5022277586d80f23c4840e497004fdaf731084c73613428ffa797cc9516e77d4",
        "bindings_sha256": "b3a37e7c341a564b76143ae1c2ca39c1f017b18dee4babf02360dbf2b14eb7ea",
        "resources": (("inputTex", "resolution", "tileOffset", "fullResolution",
                       "time", "wrap", "seed", "speed", "loopScale", "kaleido",
                       "effectWidth"), ("inputTex",), ("fragColor",), True, False),
        "loop": (1, 0, 1, 9, 0, True),
        "owner": (143, "randomFromLatticeWithOffset", "vec3", 3, 19, "130:1-171:2",
                  "9c5b258076866d4780c1b96cdb4ac8daca5efd6044ce30cc6de3a629483213cd",
                  "434acf647abc11de5c45d2ca9a5b0ede50a887136d06623b80901ddd2b4c9cb3"),
        "parent": ("157:20-161:6", "cb3b5a2611d83c1f297127b149febc0389766a2414b4014969d5eb4a6a9db831"),
        "sites": (
            ("158:10-158:46", "7783633258eeda7ffc2f970b81add192ec047936fcb85b63d9fcb7f9eeef90dd", "275c9378bc37209791faff7b6b26a21ae96b77c768e5402245bf26cdc616cf78", "00239889f0be6bed76a7091655513dff1a4e8a77d82927eb3674bbd7f5fb9f33", 0),
            ("159:10-159:46", "feb05efc9a776a4cbb67ba494339c4d57621d37b28c2b1f0f55b2502ca7fd785", "482ea492395a2d140e9fae8055f1b475ae9e33a4467618ff5c8e7e0beb18d1a1", "7e5b16aeb04700a5d59632cb2d776767a717bd21f0739dd39f644852b18f1399", 1),
            ("160:10-160:47", "8f7c51037e46bdce1bd89c2522d6f5afcde4d4e86661ac44a7a406cb12c0d9c4", "b40ebfb6547c2f86e104cb3b607c200bd597f9434f700610f8131a3fd758ac5d", "6aa6b36bccd4ddd801cb41d3f02d9c35f8ca80120f44e415123c305b85bb561a", 2)),
        "scalar_census_sha256": "7c645260e974a1dcc0326dc7e236c6e57498c8a504223ef867d1fe4fbd9b2c89",
        "call_graph_sha256": "65dfcb0c679ecfe7bc0b22db22983db4e5511e78579c43c0c95efcde5810c941",
        "reachable": (109, 110, 111, 112, 113, 114, 115, 116, 117, 122, 123, 125,
                      126, 127, 128, 129, 130, 131, 133, 134, 135, 137, 141, 142,
                      143, 145, 147, 148, 149, 151),
        "unreachable": (118, 119, 120, 121, 124, 132, 136, 138, 139, 140, 144,
                        146, 150),
    },
    "classicNoisedeck/shapeMixer:shapeMixer": {
        "raw_bytes": 21718, "raw_sha256": "704157151a2aa7e0192bd5b3483d5f1a5532a15a6e3f6a3ee0ba93ce70f8a9e4",
        "normalized_bytes": 17664, "normalized_sha256": "afb1be09867bbbb02f63c115b84ef4fd813d72defc71e2cc7d8891db9113b1b8",
        "functions_sha256": "ccf3834882fdd6ff45744377d38bd0b729f3e39d6d58c41c14a43095d6c99bcd",
        "whole_program_sha256": "57ad82d28eb34f2ea014122b03d2333099123d7b51dfe91629035ef5f41634f9",
        "interface_sha256": "45782fb4605e8e140b66a4e6b462408f79488968895dc6e735d66f5de748a21d",
        "defines": (("LOOP_OFFSET", "int", "10"),),
        "declaration_count": 25, "function_count": 38,
        "function_inventory_sha256": "fd267bcb5cb3035f9a2174bfd29de118a6dca4d990f1d9eea65d432296a05f81",
        "bindings_sha256": "f7700f10ec7dd723ce09e8657e30d0e6aa5ce3a0e34b79cfe1d5bdbb4e3e5730",
        "resources": (("inputTex", "tex", "resolution", "tileOffset", "fullResolution",
                       "time", "seed", "blendMode", "loopScale", "paletteMode",
                       "paletteOffset", "paletteAmp", "paletteFreq", "palettePhase",
                       "animate", "cyclePalette", "rotatePalette", "repeatPalette",
                       "levels", "wrap"), ("inputTex", "tex"), ("fragColor",), True, False),
        "loop": (1, 0, 1, 3, 3, True),
        "owner": (130, "randomFromLatticeWithOffset", "vec3", 3, 19, "386:1-427:2",
                  "534f686001db15b2a002c5f8715da35f3c3c91a45796881b5e3a43dea742292f",
                  "89b5b6da39c72f0b3e52fb28a3daeaa481e8a96f2130716d90b948d4c735b22a"),
        "parent": ("413:20-417:6", "a5fdc9609cf2061effd0cd7716846eaeb09a0aa56da15e3269c7db53321cca1d"),
        "sites": (
            ("414:10-414:46", "d61ee5dedd34f41977635b787534b900ebd7b9416c9711f558b5ce6e5294162b", "9ff109f0727b5a05ca60ae883227a703b8b474328da588db17df5ae0bea480bc", "29883f036cac6ff68efe1338811ce57520d028ba05c40226b6386e3a68901c23", 0),
            ("415:10-415:46", "6f95ef7eee4ec54c0a31460816c193e4bc841b3a8622ed5d55610509b0c6113f", "b0cb483d126bc289f7c654259941d58432f5e065fcf83edd4d4e75161d65f418", "607f5bc320bd91ea351bbb878c4b640fc8a71ad2f73e61c149992500e0c3b34b", 1),
            ("416:10-416:47", "a97b2dc920fab9dbd9ca11068c0b7bafc214b61a7748059dcfd79bcb3d603bd4", "645b21f7576cf2976fead4e358f0db9747159fd68fd5bf4134df5a33e397d1a7", "420c348860e5899ecd9420225395cd6ea71629faeded6779e1c048359f0626df", 2)),
        "scalar_census_sha256": "928feb676c60b9f1668567811a38b7f4ecf873f62e5b7a78b36369eb5537a253",
        "call_graph_sha256": "3bdb7adbc622ac11f82f0f664ec124c0c0ee5d90a69906b04e60d260340b3224",
        "reachable": (99, 100, 101, 102, 103, 104, 106, 107, 108, 109, 110, 111,
                      112, 113, 114, 115, 116, 118, 119, 120, 121, 122, 123, 124,
                      125, 126, 127, 128, 130, 131, 132, 133, 134, 135, 136),
        "unreachable": (105, 117, 129),
    },
    "classicNoisedeck/shapes:shapes": {
        "raw_bytes": 21289, "raw_sha256": "60bc6e76ac9d9f5bc83638fa934b279499559f7733806e462cea16a4cbe85eb0",
        "normalized_bytes": 18713, "normalized_sha256": "347d19f46adb59129ec2f5eb58910b1ea981be9ec03788a068ff6e884bb848e6",
        "functions_sha256": "dfd7220ab36ed03702afbc5e69e7e3a7346c60d488d9b3a2087d31214219943a",
        "whole_program_sha256": "e072ec89fef6122ed3d581ea5efb6cec953d9b7492294ca9d8b0f011af5411f0",
        "interface_sha256": "e27ca4581c14991de7a17e296353b1993e8f9c6e5a4ec48b170dde8f8d1b1b6c",
        "defines": (("LOOP_A_OFFSET", "int", "40"), ("LOOP_B_OFFSET", "int", "30")),
        "declaration_count": 23, "function_count": 36,
        "function_inventory_sha256": "a18e1b6669aa69433a7eabe9f6a9304b7f72cd7e1e55690d555e110c8b9ff17e",
        "bindings_sha256": "1f399ee33123e3d44d96c3741701a2821e7296218a1fdde2c232b5d72249f2b2",
        "resources": (("time", "seed", "wrap", "resolution", "tileOffset",
                       "fullResolution", "loopAScale", "loopBScale", "speedA",
                       "speedB", "paletteMode", "paletteOffset", "paletteAmp",
                       "paletteFreq", "palettePhase", "cyclePalette", "rotatePalette",
                       "repeatPalette"), (), ("fragColor",), False, False),
        "loop": (1, 0, 1, 3, 3, True),
        "owner": (140, "randomFromLatticeWithOffset", "vec3", 3, 19, "94:1-135:2",
                  "32a322a4de40d740b502b02a7984e9a0a0ea8c6eba2dcd9baf055a8eb2be12f0",
                  "94daa8bfeb8af9cc6ea64dc6efa379454352547546a3c3f7d212b03957d660e2"),
        "parent": ("121:20-125:6", "b578a7d0aebab57c33a5ac8912f4da2eb21dea572fa2d83093e6ff1b00ae2ef8"),
        "sites": (
            ("122:10-122:46", "09edd0749ceb5c7b7e84508697cb3d98eeeac9943dd0e90c6248958bf0259114", "ef28ea123ca50ffe49405acff9abf5cffac98f0a5d8923f29000890f49d97832", "25099272fcf586c6b14c04eecf2451960c6adfa6a291458ee1a2f4e98fdc2250", 0),
            ("123:10-123:46", "893fd0bacf8143d189d5a12fcb4cc987dd0e0fba74156ecffb0215ee80dd3e34", "ae853fe2a64b5a16675079f5b3b3a395f14e63522f70ae0da2b782e2683b7966", "f8ea04719fa265c08afcec39a4797fb2958cd59ca95c687226e6b893bebd3810", 1),
            ("124:10-124:47", "a6a484322b826bfe4a93981d9c57ba7c10626236be8a1cfcc42b4fdc130f4bbb", "fff586effb00f9673514ef6c140bfe774f69cf2c8b68bf4f917d02612e3e832b", "d32b1c08830d2e223635bc0e71b558fca3eb7843afbc1455f29fe7f713fbdad0", 2)),
        "scalar_census_sha256": "8f37784de5b36230e1535ad67dcf6c4054e9825f3c3f681e2589bbab4f22de63",
        "call_graph_sha256": "cdecf94aab2a041d245737ed5be8a3d8db26bb945682f4720ac6ea01c1f6b8b3",
        "reachable": (112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123,
                      124, 125, 126, 127, 128, 129, 131, 132, 133, 134, 135, 136,
                      137, 138, 140, 142, 144, 145, 146, 147),
        "unreachable": (130, 139, 141, 143),
    },
    "synth/shape:shape": {
        "raw_bytes": 15986, "raw_sha256": "d917d2027c873f05bc4183277a2b1dffe158c13cfd1281461580a31e0cd7d67f",
        "normalized_bytes": 14805, "normalized_sha256": "83bf41728f8e10ed08ec04a9899f35d60b476700703d4db851f57289cf6f1b00",
        "functions_sha256": "9aea716238e075a431961c875f674c34b97ed44a5071be54de2a21f3cf94d7d3",
        "whole_program_sha256": "60d87d93ec58d1f4c1e25a70d011a83c65b1988bf337bfbbf28e0e8c99a7e1ea",
        "interface_sha256": "06d49ba68a175bf4f313fab9533e889b049fe6593af34b0d49b62da28d23f2fd",
        "defines": (("LOOP_A_OFFSET", "int", "40"), ("LOOP_B_OFFSET", "int", "30")),
        "declaration_count": 15, "function_count": 28,
        "function_inventory_sha256": "fcf04a159ea69ac0a26218bc4989483443dde63af065e0a4d5d2be1c7efe274d",
        "bindings_sha256": "38789169e303efeffe190721f27f1fbe1733c113155a958e2ced773f9785e954",
        "resources": (("resolution", "tileOffset", "fullResolution", "time", "seed",
                       "wrap", "loopAScale", "loopBScale", "speedA", "speedB"), (),
                      ("fragColor",), False, False),
        "loop": (0, 0, 0, 0, 0, True),
        "owner": (117, "randomFromLatticeWithOffset", "vec3", 3, 18, "71:1-110:2",
                  "a6a0692c4ef6b316e0eb70d41107a5e1997682b35aff4d61bf5c87cc7f66fc8c",
                  "0220a4553bc0d180844278faf3d8796c03c8762ac778dd804a58ff126592cc3b"),
        "parent": ("96:20-100:6", "d2411bb217910f6c3057393af4265994005f860ecee7f857b752ab9da2d9101c"),
        "sites": (
            ("97:10-97:46", "599ae9b26fabb42066ad499b50545dcd578d5f4555c4dd9d096207dbaa269447", "95f166c8d1577b22617332d0b81a6ff93971b2c09ac954d24f130767c72bd47a", "26a3aee1924b82e82506b42a59b54505db30a1214f896d3ff1cb8973d902dd26", 0),
            ("98:10-98:46", "c243c8536d7294ad420601b354a9f41b70b85dbf225164fc561480babccba5bc", "94ad08a229966f37f0a8b8c3e1983315415f0fa7d44063c14714d4d875466ad0", "37b7e8f47b9409ec9e432696f5c0ab4d25d4a47e7810cadf36ab6c5629eb4c4f", 1),
            ("99:10-99:47", "03407d28ed91bb2fe85e6457d68a436880060f65f6f0dfeb6d5d362bfa82273e", "6354f802669b96dfc3cdf22ee9936e025d4b9661c8b393a3311008e8166171a2", "4bfa3cbb25b21de284acb3eb6a1c25082f7ec4aeb4c8ca2c0eb4851186c8b5ed", 2)),
        "scalar_census_sha256": "119f2efbe7d87891f4c69d0d58ffbc64c6d917b18cc7589fd3ea33f5eff46a30",
        "call_graph_sha256": "cb4f6ddbfde8d3ac5358892ffbdd2ca8929c633606c1bb2914e115927e0244a3",
        "reachable": tuple(range(95, 123)), "unreachable": (),
    },
}

SCALAR_UINT_XOR_KEYS = frozenset(_PROFILES)

# --- seventh live record: synth/noise ---------------------------------------
#
# synth/noise's jitter block is byte-shape identical to the six frozen
# carriers (three scalar-uint `^` as the ordered children of one `uvec3`
# constructor inside `constantFromLatticeWithOffset`), but the record is
# the seventh live record. Two further figures diverge from the original six,
# both expected: the frozen `loop`
# tuple is the POST-runtime-loop-bound attachment state `(1, 0, 1, 8, 8,
# True)` -- the validator applies `runtime_loop_bound` before every other
# carrier, exactly as kaleido's row freezes its post-convolve-proof state --
# and the absent-proof set is the FULL four-field set: unlike kaleido, no
# auto-attached companion proof exists for this key (measured), so no carve.
#
# Emitter-side note for the landing lane: this program owns three
# `float(uint)` constructor sites (normalized `51:34`, `104:24`, `104:45`)
# that are NOT part of this record; if any needs a Grain-class narrowing
# skip it gets its own measurement then -- nothing here decides it.
NOISE_INGRESS_KEY = "synth/noise:noise"
_NOISE_PROFILES: dict[str, dict[str, object]] = {
    NOISE_INGRESS_KEY: {
        "raw_bytes": 18131,
        "raw_sha256": "410a98f0d4ec80acde225cb5366a3bbaf752e5743f99bcd651a2c3cbb6cc3274",
        "normalized_bytes": 8516,
        "normalized_sha256": "5a9c937c83b48e85335f1d69b7a364124a3bcd3e1ece1df85b0d6f7dee929205",
        "functions_sha256": "6391eaf2da0f033f5fb5f2b04211bd6e13788b31388dd974eee25ec15e7098f7",
        "whole_program_sha256": "7e7ff4474ef6bde8ab1a1f46bfb55bf7e5ba212dba79a31600c0e2a075e2b5b9",
        "interface_sha256": "8327df301a143416b03bdb757d3d287700b89bbf543e16294ec8d94f667bb69f",
        "defines": (("LOOP_OFFSET", "int", "300"), ("NOISE_TYPE", "int", "10")),
        "declaration_count": 15, "function_count": 30,
        "function_inventory_sha256": "453f03c591dfef91aac71c56e5ac2f065a5723d0d003fd4b4ed201e7ce15db5f",
        "bindings_sha256": "3bbed24483d40719ec3a69fe19eab11159eccad67689da5fe558ac741456f023",
        "resources": (("time", "seed", "resolution", "tileOffset",
                       "fullResolution", "scaleX", "scaleY", "octaves",
                       "ridges", "loopScale", "speed", "colorMode", "wrap"),
                      (), ("fragColor",), False, False),
        "loop": (1, 0, 1, 8, 8, True),
        "owner": (111, "constantFromLatticeWithOffset", "float", 5, 18,
                  "72:1-107:2",
                  "6c4ac0b295f0f621650433d2d554f930cae820fe853252c2c66afafb71fcae45",
                  "7d7c414e8b7346a5bd65792e13872b9650d0f12b4d446de87f4138bbefcb2229"),
        "parent": ("96:20-100:6",
                   "af4bd6072fdf5df11eccb77242df15bcf297eb6e5dd1e9e2bc3ae468f15d5d40"),
        "sites": (
            ("97:10-97:46", "a45e33e4b747f5b80a22ea6017c17bfea9b8ace2bbc9f8b27132e81373095ee4", "e3951a718363494be757949c3e8e710b7ea75656617f0f19d330a424c93883ee", "5ff9cb119a8f4431721694af7d89b0df6ccf46cf0a2225bc2631890257092f1d", 0),
            ("98:10-98:46", "466bfadfed41db40687fea32b63cd1067aee5f41f93f567073dc5c5ff374becc", "a5876f0d146c0f9223971b29f97ad15366350c30c34477ab6cb28d3aef0bef63", "336cf887e6811c86596b72683962769baffec8e78f366d3df6e85a5dcc9db9b2", 1),
            ("99:10-99:47", "907c965721a135faf6e48cbbd94d2dc5aae02986e38f74cd5bcb5888c0d712b0", "5919db779a17688938f9fe836e6fe52a9612c04e35211782360f05edb0afd480", "408652223c307aafff285f67a922a6c42f4013afe0cb996b6f762e38c7d27f92", 2)),
        "scalar_census_sha256": "e32c5dcd4f7bfdfc4d12143a6d3728e05f23b420e5c27edb459c1719dde4ac57",
        "call_graph_sha256": "967c512582f0706c7e1412580a0c63178feea2db47215e4d258b4e96da05b5a9",
        # The divergence that breaks the six-carrier mold: the XOR owner is
        # UNREACHABLE at the frozen defines (NOISE_TYPE=10 dispatches `value()`
        # to the simplex arm, bypassing the lattice path).  Dead code's
        # grammar still closes -- identity locks, not pixel tests.
        "owner_reachability": "unreachable",
        "reachable": (115, 117, 118, 119, 120, 121, 122, 124, 125, 132, 133),
        "unreachable": (104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
                        114, 116, 123, 126, 127, 128, 129, 130, 131),
    },
}
_PROFILES.update(_NOISE_PROFILES)
_PREPARED_PROFILES = {}
SCALAR_UINT_XOR_KEYS = frozenset(_PROFILES)
PREPARED_SCALAR_UINT_XOR_KEYS = frozenset()

# Complete `float(uint)` constructor census for the same six authenticated
# carriers.  The pinned canonical JavaScript compiler erases every scalar
# constructor below to a Number identity.  The complete census lets us prove
# which site actually needs a no-narrow exception without generalizing from a
# convenient local pattern.  This list is intentionally separate from the XOR
# sites: it is an emitter-only materialization contract and does not widen the
# validator's constructor vocabulary.
#
# Record fields: site span/hash, owner id/name, child kind/span/hash/member/
# category, child-base kind/symbol id/name, parent span/hash/kind/operator.
_UINT_TO_FLOAT_CENSUS_LOCKS = {
    'classicNoisedeck/bitEffects:bitEffects': (
        ('60:31-60:54', '3db1f4d94f0b3a17e907a4d9008b78c91ad3099e7643f00f78c13cf3859b4b92', 110, 'prng', 'construct', '60:37-60:53', '8e9657140a9aefdf2ccb5f23d9004b3146177dc0fdaffffb8b994423525a924c', None, 'rvalue', 'literal', None, None, '60:9-60:54', '81f308ed0a312a7ad8ac383a149643f669df9a57415dfe179f4dd78de982c9b6', 'binary', '/'),
        ('106:19-106:37', 'd4db09f32deb0fd914558bf09ce6793e0b92374768152439b27219d7ebb9a1a7', 111, 'randomFromLatticeWithOffset', 'literal', '106:25-106:36', '249835b4bf4e9797d171207b091d3f729da6e26a4aeb3ea3e46789f217c0ece9', None, 'rvalue', 'literal', None, None, '106:11-106:37', '4fb0d2bed246fae94c298a88b86fc595982fc97c9952e313f9535a4b61da3a50', 'declaration', None),
        ('108:9-108:27', '3a4d3acf582725b1530a6d12537cde37e5162d9fe2373a99b9aa098b63363f7f', 111, 'randomFromLatticeWithOffset', 'swizzle', '108:15-108:26', '40403d4fd50b8f83f5dd9c1ddde4040d7ab16116adee71d9ed7c08e9544acc9e', 'x', 'lvalue', 'id', 165, 'prngState', '108:9-108:35', 'f087a518ab62a35a5c922c9769683fe12d4188b5e3ae63aa343a2576c65281d5', 'binary', '/'),
        ('109:9-109:27', 'b1d6a3c698ceb4ee61469886fa82a2228c142f41e62f128bbac715571710784f', 111, 'randomFromLatticeWithOffset', 'swizzle', '109:15-109:26', 'a1d327d778e204944b58c5a6c1196749c8e202b9770ac498a38e3f7cc7bb1b12', 'y', 'lvalue', 'id', 165, 'prngState', '109:9-109:35', 'f9b392e6d59a451fe981defb52c4a94f07398bd483080b1145325dbc249fc16b', 'binary', '/'),
        ('110:9-110:27', '1b74e95154067d08eb19704f590adb826cc60b80d1b7c9225b4f6357ca855595', 111, 'randomFromLatticeWithOffset', 'swizzle', '110:15-110:26', 'ec99b097dd7302e919cd89317a18fa26bdbc6e545a37c09fa6fb293d43725baa', 'z', 'lvalue', 'id', 165, 'prngState', '110:9-110:35', 'aa45802aac6bfacccd89f92201792d7f02f06a11eef46f34df0f9b6b9c4808d3', 'binary', '/'),
    ),
    'classicNoisedeck/kaleido:kaleido': (
        ('102:31-102:54', 'f0da77e5ba8c17b6601532c37202976fcd533dac6f7da8b1d5d9a39bd8bfe82d', 139, 'prng', 'construct', '102:37-102:53', 'f32d58bc1955bc342aede81b1ca3abac2606fb5eadf8aa356d8c10a529c0e4ce', None, 'rvalue', 'literal', None, None, '102:9-102:54', '989b565698529c2278039df539408eae262b874005b0bafb53801d18c046fc85', 'binary', '/'),
        ('107:12-107:35', '670bdbdfbdaccdc70415822993ab09557792b8e9118e375e551773039038a13d', 140, 'prng2', 'swizzle', '107:18-107:34', '123017a98fac996d052b7f0f178869b18ac52fc582133f8db099ffe789270007', 'x', 'rvalue', 'call', None, None, '107:12-107:61', 'e416ec81eae17e4d1f48ccc604af92b145019b60c40770dcf5bcf43168135ce2', 'binary', '/'),
        ('107:38-107:61', 'f94a2a8795fa9d7c73f2e74bf892239040cc196fcec781c6d6400faf548b113c', 140, 'prng2', 'construct', '107:44-107:60', '728a42411dae1d9e132d2a2cc1a553a4b15846fd7abb2ec5d16047b8a7811945', None, 'rvalue', 'literal', None, None, '107:12-107:61', 'e416ec81eae17e4d1f48ccc604af92b145019b60c40770dcf5bcf43168135ce2', 'binary', '/'),
        ('165:19-165:37', 'd5c0a3c09f376640d919f2327c6d7861b503420ed1cebb34a1659d9ae3d0c396', 143, 'randomFromLatticeWithOffset', 'literal', '165:25-165:36', '13e63c377b14af97589c189b8f30e862fbae51b6478c5ae662f3f23487ce6f63', None, 'rvalue', 'literal', None, None, '165:11-165:37', '3ebe16c1c663d5653f2e7a3152814e9c7fdc033d64b144ee8111b4317d847960', 'declaration', None),
        ('167:9-167:27', '850228fa5cb8c427e1a4edbd17f799defd369d4381aafb656591b46102b8355b', 143, 'randomFromLatticeWithOffset', 'swizzle', '167:15-167:26', '436c202e12aa1d819847dc9e533612191b3af5e57063c09d4d04949303b0b071', 'x', 'lvalue', 'id', 320, 'prngState', '167:9-167:35', '4b780f6bcc3aecde5502439bfde247b64054ef894df0a5564169f523fddd46d8', 'binary', '/'),
        ('168:9-168:27', '501c99dec181ae8bd9f556782ab7c07bcbee8ef877a0c15f657f33a2f72dbe00', 143, 'randomFromLatticeWithOffset', 'swizzle', '168:15-168:26', '400b1a06563de6a1692a70e54466f45c19c41c060a676f3bcc2316ac8efcb62f', 'y', 'lvalue', 'id', 320, 'prngState', '168:9-168:35', 'a6a005cf3cca2ba553433e5fdd2df6bfbc7be1fd60787cd88ad78d068ecef75b', 'binary', '/'),
        ('169:9-169:27', '68115341d4e01d861eb126b8294607b2564cf710725c62ebb194f66fb8cceada', 143, 'randomFromLatticeWithOffset', 'swizzle', '169:15-169:26', '71df5b2a03a43de9d4b83e4bcaf6c60c3f8c9e33e4aec263fea4abdca42f2329', 'z', 'lvalue', 'id', 320, 'prngState', '169:9-169:35', '6c221435137f54c3d5604109ec61913720f5393126ede49893c5300c3c419f83', 'binary', '/'),
    ),
    'classicNoisedeck/shapeMixer:shapeMixer': (
        ('52:31-52:54', '4824d4f88c67d9ad9f817bd45ca190523688f2496f7b924dbd93970761d7600e', 126, 'prng', 'construct', '52:37-52:53', '9eb472f5246286e1335cb69dba9e6a27edf9815c1f9922cfd0dc04447711dcd5', None, 'rvalue', 'literal', None, None, '52:9-52:54', '2d494dc2511a65d989d0ffe65f96986f6a3065f08f4d213746bc66cd555e9a08', 'binary', '/'),
        ('421:19-421:37', '0b08ff022b1c5b7fc64db054d241cd894a18133a925038c5fb04da637542c142', 130, 'randomFromLatticeWithOffset', 'literal', '421:25-421:36', '96c78bdc280934a1fa5b09219d955cfe40bdd1fbb03a867bcc085c3925e84d18', None, 'rvalue', 'literal', None, None, '421:11-421:37', '5354ac324b4c7dee48bcf4573f7ba132ae4afab40361cb293b96f3c876f22644', 'declaration', None),
        ('423:9-423:27', '84ca341551004cf45ec3d8e58e9d0342a839fb56dc62092aa7db06b94f9ea410', 130, 'randomFromLatticeWithOffset', 'swizzle', '423:15-423:26', '94d6aea4f4c689cb2bdb7b208fb1b28ad2cc1d9c29227e61730182b52335564d', 'x', 'lvalue', 'id', 212, 'prngState', '423:9-423:35', 'c6b370c7d829e4227af59655e16fdff94e5b8fca1fcea1e969ea119c9584c777', 'binary', '/'),
        ('424:9-424:27', 'a74e560f58cd5df465ee35b4ff4d03bddb8cfc9730afaeae11eb778e1cdfff75', 130, 'randomFromLatticeWithOffset', 'swizzle', '424:15-424:26', 'f38b10aa8530e1fe5eb95b332c9f5cb79b0e38a2043a025d5de626899e5cfa49', 'y', 'lvalue', 'id', 212, 'prngState', '424:9-424:35', 'c5153e7a6490c5a01d9a54050d01fe183ea22792c37050935094e268540d6454', 'binary', '/'),
        ('425:9-425:27', '56e0f6dfbba76362613fc70ea586f7e3e308de6736fe50fc9ad6c2a53c9b3d43', 130, 'randomFromLatticeWithOffset', 'swizzle', '425:15-425:26', 'e6920403def68ff6c3e82eb70b93c52b724bf24399b38b9551d612b1d1512f8b', 'z', 'lvalue', 'id', 212, 'prngState', '425:9-425:35', '461e1ddc37afc1c89d0284c2c9bf62e1c7bb53071df491c49a94f733641b77c0', 'binary', '/'),
    ),
    'classicNoisedeck/shapes:shapes': (
        ('68:31-68:54', '8598be3e7bd6022bd80cbe4da148c94e92ba16b284c6b8ae7db2a6fb0a0a5658', 136, 'prng', 'construct', '68:37-68:53', '6534766e8a5812b1230883521f93270d8e82905c774b05788d6080ad5eacf0eb', None, 'rvalue', 'literal', None, None, '68:9-68:54', '2c56e1652acdbe0d5bab9a563a4083fc8e547fbf8a0463da2ff46e0b0b625d82', 'binary', '/'),
        ('129:19-129:37', 'cb3ac8f8dc6c03167a9eaeca10042ded8c68025803cdd24cc4c58f67e5aed5a5', 140, 'randomFromLatticeWithOffset', 'literal', '129:25-129:36', 'b3160f226ae2f99e3b543185e2e76f0a3414bd8e7453432320e21829842efd67', None, 'rvalue', 'literal', None, None, '129:11-129:37', 'f5d81436c5ab7ae1b695a81dee725ad0159a7d3b0321fd79823a5b27eda4f9de', 'declaration', None),
        ('131:9-131:27', '255f1ed1420ba5b1ba068920481beb238bc606389c38d88999bbeb671a6b3b67', 140, 'randomFromLatticeWithOffset', 'swizzle', '131:15-131:26', '0bc9f8f51cc681f2892223aa9ad8d227fc57d00cf4e96603ce3c1f8e42a8cb3e', 'x', 'lvalue', 'id', 305, 'prngState', '131:9-131:35', '29891a1cbb465ee93ae7e06e0b469146abc42dff7fd3c768f6708c6ef9707344', 'binary', '/'),
        ('132:9-132:27', 'f76b65e85aa5fd4cbe0df5bdf5a93733543e77192a7eb98e97a45a0c179e2ba9', 140, 'randomFromLatticeWithOffset', 'swizzle', '132:15-132:26', 'afbd84fd38a5f6f202eb33dfd080f4f7ee6601c5190e9170ea88ac1a768d94e5', 'y', 'lvalue', 'id', 305, 'prngState', '132:9-132:35', '7ec007ac3af4c043b4e00cde444f1473df73ed4bd764be819f19e9fee661e722', 'binary', '/'),
        ('133:9-133:27', 'ea8b98c89938f47800787e1e240b5a359c532a4e5c388f45030933ce8dea6a3b', 140, 'randomFromLatticeWithOffset', 'swizzle', '133:15-133:26', '9790d6476085601bca1093786312d46f44eff56a8370851ea900cbf7656d229b', 'z', 'lvalue', 'id', 305, 'prngState', '133:9-133:35', 'c167aeb08bbd18f37535a74afc82ae4a501916f15a02ff29a2f33159b6bbd63f', 'binary', '/'),
    ),
    'filter/grain:grain': (
        ('252:14-252:28', 'e249c27629372601ebfde6dc8522271a35d18570aabbd995204fe9746c3d4044', 57, 'main', 'id', '252:20-252:27', '5b51dcaca08ffc0bdffcc506bf43a0018dfa45ee318fffe9720cb3274498d254', None, 'lvalue', 'id', 81, 'u_width', '252:14-252:33', '9cce58bd31071b58152c016c0b7a9a7b840b8c7df52c1f8c8a1e3fb014994c3b', 'binary', '/'),
        ('252:35-252:50', '0a3ed4b3b341e8fcf546ede3817eddaac6a5255d106cee11db422fe411f787ca', 57, 'main', 'id', '252:41-252:49', '4d50f20ebff4a99f26ef7c3c3256361d1fea30d31cb56de30f6c922291e8e871', None, 'lvalue', 'id', 82, 'u_height', '252:35-252:55', '570364f244d26e4694aae0c6fb2145945b889cc787b3ce04ea58165c3854a24e', 'binary', '/'),
        ('57:12-57:26', '856c5c2a76233266795725167ed3d1c11f6c1a99bafdb2f1a5bd19e796c14d5a', 60, 'random_from_cell_3d', 'swizzle', '57:18-57:25', '37c3b4a5ff33325042ff7fe1d456da54d207fd8c31fd9fcd8c0f9122d023b1ad', 'x', 'lvalue', 'id', 94, 'noise', '57:12-57:44', 'e3fc5e13dacd449e7467c455c575e62f12273193d274be055c142c79a1041314', 'binary', '*'),
        ('221:20-221:41', '825689f4ae3036b38b3cbeeb3fd6ea5ecb46bcffdfd2a7c4799a1c8b03eb4fd5', 62, 'sample_grain_noise', 'swizzle', '221:26-221:40', 'b2e14ac413c889bab5eda75d3059e3cf238e1b4b70a773b1f411af763d1416bd', 'x', 'lvalue', 'id', 49, 'pixel_coords', '221:20-221:49', '89ae1688f17cd9f30971f6419dfecb48bcd91679aa05f38c2e0f30e1d74ddc47', 'binary', '/'),
        ('221:51-221:72', 'ba798536c63b2af096cb66781e76a8bb958ceb554b09f439ca2fd91d8a462234', 62, 'sample_grain_noise', 'swizzle', '221:57-221:71', 'b0779d263089d838f25fbd0192a3c0c38a05cd00a273906093236ada2fa58319', 'y', 'lvalue', 'id', 49, 'pixel_coords', '221:51-221:81', '83c8ac17eb307ce862a05b323807c241030409015ccbe08c1dec0a34acea63f9', 'binary', '/'),
    ),
    'synth/shape:shape': (
        ('63:22-63:40', '0d9546333f008ab2f75b309fe9f441f8fc9d86938c433e7a5d9da4b487f81e22', 114, 'prng', 'literal', '63:28-63:39', '038e4ce46541631a6ed663422cfed9a24efa5bdceff49aecdcd7533b3d1fc0a1', None, 'rvalue', 'literal', None, None, '63:12-63:40', 'aaf58dffb5584b3cffd19733f0e2d545e83ebf315ffe9b54d7637db08b62f74c', 'binary', '/'),
        ('104:19-104:37', 'dc5be68d15a22f3c482024bba55534d3406dab1e31fb09c0b2b60d54610d2740', 117, 'randomFromLatticeWithOffset', 'literal', '104:25-104:36', '3c903a15230339ad522d7505cd82a42644f9d0f616a7d01b6a9978d059686f0a', None, 'rvalue', 'literal', None, None, '104:11-104:37', 'a3ac3d170d9bcd79b65b19a5146572ed1b8b59de677b3920e8d29c1638ba9dd7', 'declaration', None),
        ('106:9-106:27', '4f91700a91a8fff316bd0e840bf20695175b14279d656306d90400ff1800cd00', 117, 'randomFromLatticeWithOffset', 'swizzle', '106:15-106:26', '5a60b066da1aeb561770466b52eaec7fb067c65c84cb5282ce75db70ae238e0d', 'x', 'lvalue', 'id', 263, 'prngState', '106:9-106:35', '50eb4af80409f02d397686fde2e63965586285873a106c0c8aa49efcaf020f78', 'binary', '/'),
        ('107:9-107:27', 'a13d0183ea48b8dbdcd542aa875494f182a327992f04b13f2b19a1e4da999677', 117, 'randomFromLatticeWithOffset', 'swizzle', '107:15-107:26', 'abde0c743ba775b34924bc80ec226456dbdf8d4a6d8c0b9b5eee27a35919edfc', 'y', 'lvalue', 'id', 263, 'prngState', '107:9-107:35', 'f67a2bd4f717517f7568e94bfd6c2e5eea075f0e96bb2757a60899912709d657', 'binary', '/'),
        ('108:9-108:27', '29a63bbff40517027a659fdde9796dac0932d5d6c3381f3a61f2262237e7e07c', 117, 'randomFromLatticeWithOffset', 'swizzle', '108:15-108:26', 'a3cbfa2457ec4501fafd42253ba7db4ab4334912784e2ab98d64e2217f074475', 'z', 'lvalue', 'id', 263, 'prngState', '108:9-108:35', 'a8ee74258fc31b07b3bed5768b8829a506d9dde89bde5ff325b27eee2a519298', 'binary', '/'),
    ),
}
_UINT_TO_FLOAT_NARROWING_SKIP_SPANS = {
    # Only this site consumes an unconstrained PCG uint and is observably
    # different under premature f32 narrowing in Grain's reviewed oracles.
    # The other 31 census members remain on the established emitter path.
    "filter/grain:grain": ("57:12-57:26",),
}

# kaleido's ONE `floatBitsToUint` ingress (integration-slice discovery,
# kaleido-design §10's anticipated class: the copy probe stopped at the
# fixed-array boundary `543:24`, and the third key moved the frontier to
# `155:21: unsupported builtin floatBitsToUint`).  The source shape is the
# Shapes family's lattice-hash ingress verbatim -- `float seedFrac = 0.0;`
# feeding `uint fracBits = floatBitsToUint(seedFrac);` whose three
# `fracBits * K` products are exactly the three authenticated scalar-XOR
# left operands.  This census rides the row's existing `scalar-uint-xor-v1`
# carrier exactly as `_UINT_TO_FLOAT_CENSUS_LOCKS` does -- no new row field,
# no capability token; both authorities admit the returned node by object
# identity on the Caustic/Scanline/Shapes skip-list precedent.
KALEIDO_INGRESS_KEY = "classicNoisedeck/kaleido:kaleido"
_KALEIDO_INGRESS_STATEMENT = (13, ("decl", "155:5-155:47"))
# Ingress: callee, span, result type, node hash, category.
_KALEIDO_INGRESS = ("floatBitsToUint", "155:21-155:46", "uint",
                    "98040f6d95fcb1a77867d06280645fc8d8370af83bffd846adc11009869ce5ea",
                    "rvalue")
# Operand: kind, span, type, category, symbol id/name/storage/writable, hash.
_KALEIDO_INGRESS_OPERAND = (
    "id", "155:37-155:45", "float", "lvalue", 309, "seedFrac", "local", True,
    "f19ab4829e1aa0815c2047b369ca54be5ddc952a0282fe59a56d77be4c838e9b")
# Declaration parent: kind, span, type, symbol id/name/storage/writable, hash.
_KALEIDO_INGRESS_PARENT = (
    "declaration", "155:10-155:46", "uint", 317, "fracBits", "local", True,
    "e03dd4bc7a9af6eeb8bf18102d207907799b3b27946a0564c8704b659ed6c0ca")
# `float seedFrac = 0.0;` -- statement index, declaration shape, and the
# exact POSITIVE-zero literal initializer (sign read off the bit pattern, so
# `-0.0` fails here and not on a coarse hash).
_KALEIDO_SEED_FRAC_STATEMENT_INDEX = 5
_KALEIDO_SEED_FRAC_DECLARATION = (
    "declaration", "137:11-137:25", "float", 309, "seedFrac", "local", True,
    "48b92162078ae0a2cfa4357240bda9e66aba78c3584a0ff1723855fe2e823fae")
_KALEIDO_SEED_FRAC_INITIALIZER = (
    "literal", "137:22-137:25", "float", "rvalue", "0.0",
    "eb6070660a116d9258c2188b9de508bcd7d64b810068c2739c67a8d4646c38c7")
# Complete whole-program reference censuses: `seedFrac` is its declaration,
# its one arithmetic read, and the ingress operand; `fracBits` is its
# declaration plus the three product consumers.
_KALEIDO_SEED_FRAC_REFERENCES = (
    ("declaration", "137:11-137:25",
     "48b92162078ae0a2cfa4357240bda9e66aba78c3584a0ff1723855fe2e823fae"),
    ("id", "139:32-139:40",
     "4db779a07d463d556af74ce9b652b8ebbd137e371ae81ec758314cb79d69ead8"),
    ("id", "155:37-155:45",
     "f19ab4829e1aa0815c2047b369ca54be5ddc952a0282fe59a56d77be4c838e9b"),
)
_KALEIDO_FRAC_BITS_REFERENCES = 4
# Downstream ancestry, one row per scalar-XOR lane: the XOR span, its
# `uint * uint` product (operator/span/hash), and the `fracBits` consumer id
# (span/hash) that product reads.
_KALEIDO_XOR_ANCESTRY = (
    ("158:10-158:46", "*", "158:10-158:31",
     "275c9378bc37209791faff7b6b26a21ae96b77c768e5402245bf26cdc616cf78",
     "158:10-158:18",
     "f01a83df039dc14298517736aaf48eabc9b68894d7c653db6a91e52c3225e47d"),
    ("159:10-159:46", "*", "159:10-159:31",
     "482ea492395a2d140e9fae8055f1b475ae9e33a4467618ff5c8e7e0beb18d1a1",
     "159:10-159:18",
     "4162259ff9bfa71ba30dee7ac9a31b4f6501882dd9ebd54f3c096e2ae7badc4d"),
    ("160:10-160:47", "*", "160:10-160:32",
     "b40ebfb6547c2f86e104cb3b607c200bd597f9434f700610f8131a3fd758ac5d",
     "160:10-160:18",
     "8eb2d309d911dba6749f7d2bc4eafe1846cb0431420b4f034f65842aa20af456"),
)
# Owner, ingress, operand, declaration parent, owning statement, the
# `seedFrac` declaration, and the three scalar-XOR nodes: nine distinct
# objects, each visited and consumed exactly once.
_KALEIDO_INGRESS_LEDGER = 9
_OPTIONAL_PROOF_FIELDS = (
    "fixed_nine_table_proof", "fixed_grid_counter_store_proof",
    "fixed_array_in_parameter_proof", "fixed_affine_centers13_proof",
)
# kaleido alone carries a second frozen carrier: its row wires this XOR
# profile as the required companion of the mutable-global array closure, and
# the generator auto-attaches `fixed_array_in_parameter_proof`
# (`kaleido-convolve-v1`) to EVERY program before validation -- so the
# strict "every optional proof absent" set would reject the authentic row at
# validation (measured: "unrelated proof carrier is not absent").  The
# carve is PER KEY (kaleido-design §4.4.2): the other six carriers keep
# the full absent set.  Exactness of the attached proof is not this
# module's concern; the fixed-array arms at both authorities own that
# equality lock (the Amendment 13.2 family split).
_FIXED_ARRAY_PROOF_COMPANION_KEYS = frozenset(
    {"classicNoisedeck/kaleido:kaleido"})

# synth/noise's ONE `floatBitsToUint` ingress (kaleido's in-module precedent
# shape, riding the live scalar-XOR record above).  The source
# shape is the family's lattice-hash ingress with one deliberate divergence
# from Shapes/kaleido: the operand's initializer is DYNAMIC --
# `float sFrac = fract(s);` (normalized 78:19, the `s` parameter) -- not the
# frozen positive-zero literal, so the +0.0 sign lock is replaced by an exact
# `fract(<s>)` builtin-initializer lock (callee, both node hashes).  Owner
# statement 12 declares `uint fracBits = floatBitsToUint(sFrac);` (94:5),
# whose three `fracBits * K` products are exactly the three authenticated
# scalar-XOR left operands; `sFrac`'s whole-program reference census is three
# (declaration, the `xCombined` arithmetic read at 80:32, the ingress
# operand) and `fracBits`'s is four (declaration + the three consumers).
_NOISE_INGRESS_STATEMENT = (12, ("decl", "94:5-94:44"))
_NOISE_INGRESS = ("floatBitsToUint", "94:21-94:43", "uint",
                  "aab81182ab1ddc1a4e9fe5a07e69fc32a62e3a64899de753a2f31d666bc6c4ac",
                  "rvalue")
_NOISE_INGRESS_OPERAND = (
    "id", "94:37-94:42", "float", "lvalue", 149, "sFrac", "local", True,
    "1aa7d94c119248eeacf1d4ed0e5dbe14eace9b4c93e0480e52852e2ebf126dcf")
_NOISE_INGRESS_PARENT = (
    "declaration", "94:10-94:43", "uint", 158, "fracBits", "local", True,
    "03cf2158b587d4c366da430ecdac35fb154df6da77a178ee50127af145585478")
_NOISE_SFRAC_STATEMENT_INDEX = 4
_NOISE_SFRAC_DECLARATION = (
    "declaration", "78:11-78:27", "float", 149, "sFrac", "local", True,
    "582df7658b117ea88e4487e61a68e8c02fe73cea4d858fe5c81d1c19cf2c3d07")
# The dynamic initializer, node by node: the `fract` builtin call and its
# sole child, the `s` parameter id.
_NOISE_SFRAC_INITIALIZER = (
    "builtin", "fract", "78:19-78:27", "float", "rvalue",
    "321fb1574fce7bfda59d21837c5733fd15a8a136ac6236caa1954f5392025ecc")
_NOISE_SFRAC_INITIALIZER_CHILD = (
    "id", "78:25-78:26", "float", "lvalue", 29, "s", "parameter",
    "c4e3137d05f65aa533312b77b7704140979bfdf8c0ff7838365c0c748a1c7e79")
_NOISE_SFRAC_REFERENCES = (
    ("declaration", "78:11-78:27",
     "582df7658b117ea88e4487e61a68e8c02fe73cea4d858fe5c81d1c19cf2c3d07"),
    ("id", "80:32-80:37",
     "fac86198e6ae3d4ced264aa7e30498383b9e450fa1ecd46953d74f3a8c5a389c"),
    ("id", "94:37-94:42",
     "1aa7d94c119248eeacf1d4ed0e5dbe14eace9b4c93e0480e52852e2ebf126dcf"),
)
_NOISE_FRAC_BITS_REFERENCES = 4
_NOISE_XOR_ANCESTRY = (
    ("97:10-97:46", "*", "97:10-97:31",
     "e3951a718363494be757949c3e8e710b7ea75656617f0f19d330a424c93883ee",
     "97:10-97:18",
     "fa01f03d86a69db42a1ff32a7611e90f4b89a381878864cd078be1bfe15d230f"),
    ("98:10-98:46", "*", "98:10-98:31",
     "a5876f0d146c0f9223971b29f97ad15366350c30c34477ab6cb28d3aef0bef63",
     "98:10-98:18",
     "2a1b4020ec7a04fb4e1e94d8861681ba7a7158018f0fcb20ad4121ac4b9f00cb"),
    ("99:10-99:47", "*", "99:10-99:32",
     "5919db779a17688938f9fe836e6fe52a9612c04e35211782360f05edb0afd480",
     "99:10-99:18",
     "c587590e8eff21a3931a1b449853a5ec6926703248c0d78ce5b1487bfd7804bb"),
)
# Owner, ingress, operand, declaration parent, owning statement, the `sFrac`
# declaration, and the three scalar-XOR nodes: nine distinct objects, each
# visited and consumed exactly once.
_NOISE_INGRESS_LEDGER = 9


def _absent_proof_fields(key: str) -> tuple[str, ...]:
    """The optional-proof fields that must be None for ``key``."""
    if key in _FIXED_ARRAY_PROOF_COMPANION_KEYS:
        return tuple(field for field in _OPTIONAL_PROOF_FIELDS
                     if field != "fixed_array_in_parameter_proof")
    return _OPTIONAL_PROOF_FIELDS

__all__ = ("PROFILE", "SCALAR_UINT_XOR_KEYS", "KALEIDO_INGRESS_KEY",
           "NOISE_INGRESS_KEY", "PREPARED_SCALAR_UINT_XOR_KEYS",
           "authenticate_scalar_uint_xor",
           "authenticate_scalar_uint_to_float_narrowing_skips",
           "authenticate_kaleido_float_bits_ingress",
           "authenticate_noise_float_bits_ingress",
           "authenticate_prepared_scalar_uint_xor",
           "authenticate_prepared_noise_float_bits_ingress",
           "apply_scalar_uint_xor")


def _sha(value: object) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def _span(value: object) -> str:
    span = getattr(value, "span")
    return (f"{span.start_line}:{span.start_column}-"
            f"{span.end_line}:{span.end_column}")


def _whole_program_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.key, program.source, program.raw_source, program.declarations,
        program.functions, program.resources, program.body_status,
        program.local_type_names, program.structs, program.uniform_blocks,
        program.interface_symbols, program.builtin_symbols,
        program.counted_loop_proof, program.preprocessor_defines,
    ))


def _interface_fingerprint(program: TypedProgram) -> str:
    return _sha((
        program.declarations, program.resources, program.local_type_names,
        program.structs, program.uniform_blocks, program.interface_symbols,
        program.builtin_symbols, program.preprocessor_defines,
    ))


def _walk_expression(value: TypedExpression, parent: TypedExpression | None = None):
    yield value, parent
    for child in value.children:
        yield from _walk_expression(child, value)


def _walk_statement(value: TypedStatement):
    for expression in value.expressions:
        yield from _walk_expression(expression)
    for child in value.children:
        yield from _walk_statement(child)


def _fail(message: str) -> ValueError:
    return ValueError(f"{PROFILE}: {message}")


def _collect(program: TypedProgram):
    parents: dict[int, TypedExpression] = {}
    owners: dict[int, object] = {}
    calls: dict[int, list[int]] = {
        function.signature.id: [] for function in program.functions}
    scalar_xors: list[TypedExpression] = []
    for function in program.functions:
        for statement in function.body:
            for value, parent in _walk_statement(statement):
                if parent is not None:
                    parents[id(value)] = parent
                owners[id(value)] = function
                if value.kind == "call" and value.signature_id is not None:
                    calls[function.signature.id].append(value.signature_id)
                if (value.kind == "binary" and value.operator == "^"
                        and value.type.display() == "uint"
                        and len(value.children) == 2
                        and all(child.type.display() == "uint"
                                for child in value.children)):
                    scalar_xors.append(value)
    return scalar_xors, parents, owners, calls


def _scalar_census_fingerprint(
        program: TypedProgram, parent: TypedExpression) -> str:
    scalar_xors, parents, owners, _ = _collect(program)
    return _sha(tuple(
        (owners[id(value)].signature.id, _span(value), _sha(value),
         parents.get(id(value)) is parent)
        for value in scalar_xors))


def authenticate_scalar_uint_xor(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Return the three exact nodes from the supplied tree, in lane order."""
    from .noise_runtime_define_profile import is_dynamic_program, authenticate_scalar_xor
    if is_dynamic_program(program):
        return authenticate_scalar_xor(program, source_hash, profile)
    expected = _PROFILES.get(program.key)
    if expected is None:
        if profile is not None:
            raise _fail("program key is not an admitted scalar uint XOR carrier")
        return ()
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    return _authenticate_xor_record(program, source_hash, profile, expected,
                                    _absent_proof_fields(program.key))


def authenticate_prepared_scalar_uint_xor(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Return the three exact prepared-record nodes, in lane order.

    The prepared record set is deliberately disjoint from ``_PROFILES`` so
    the live six-key census stays exactly as frozen; membership, profile
    exactness and the full four-field absent-proof set are checked here, and
    every structural lock is the very code the six live carriers run.
    """
    expected = _PREPARED_PROFILES.get(program.key)
    if expected is None:
        if profile is not None:
            raise _fail(
                "program key is not a prepared scalar uint XOR carrier")
        return ()
    if profile != PROFILE:
        raise _fail("exact profile carrier required")
    return _authenticate_xor_record(program, source_hash, profile, expected,
                                    _OPTIONAL_PROOF_FIELDS)


def _authenticate_xor_record(
        program: TypedProgram, source_hash: str | None, profile: str | None,
        expected: dict[str, object],
        absent_fields: tuple[str, ...]) -> tuple[TypedExpression, ...]:
    """The complete structural lock ladder, shared by live and prepared keys."""
    raw = program.raw_source.encode("utf-8")
    normalized = program.source.encode("utf-8")
    defines = tuple((item.name, item.kind, item.canonical_value)
                    for item in program.preprocessor_defines)
    inventory = tuple(
        (item.signature.id, item.name, item.return_type.display(),
         len(item.parameters), len(item.body), _span(item))
        for item in program.functions)
    bindings = tuple(
        (item.symbol.id, item.symbol.name, item.type.display(),
         item.symbol.storage, item.symbol.writable)
        for item in program.declarations)
    resources = program.resources
    resource_tuple = (resources.uniforms, resources.samplers, resources.outputs,
                      resources.uses_texture, resources.uses_derivatives)
    proof = program.counted_loop_proof
    loop_tuple = None if proof is None else (
        proof.loop_count, proof.unproved_loop_count, proof.max_effective_depth,
        proof.max_lexical_product, proof.entrypoint_charge,
        proof.call_graph_acyclic)
    if (source_hash != expected["raw_sha256"]
            or len(raw) != expected["raw_bytes"]
            or hashlib.sha256(raw).hexdigest() != expected["raw_sha256"]
            or len(normalized) != expected["normalized_bytes"]
            or hashlib.sha256(normalized).hexdigest()
            != expected["normalized_sha256"]
            or defines != expected["defines"]
            or program.body_status != "analyzed"
            or len(program.declarations) != expected["declaration_count"]
            or len(program.functions) != expected["function_count"]
            or _sha(program.functions) != expected["functions_sha256"]
            or _whole_program_fingerprint(program)
            != expected["whole_program_sha256"]
            or _interface_fingerprint(program) != expected["interface_sha256"]
            or _sha(inventory) != expected["function_inventory_sha256"]
            or _sha(bindings) != expected["bindings_sha256"]
            or resource_tuple != expected["resources"]
            or loop_tuple != expected["loop"]):
        raise _fail("source, define, function, whole-program, or interface mismatch")
    if any(getattr(program, field) is not None
           for field in absent_fields):
        raise _fail("unrelated proof carrier is not absent")

    scalar_xors, parents, owners, calls = _collect(program)
    owner_record = expected["owner"]
    owner_candidates = [function for function in program.functions
                        if function.signature.id == owner_record[0]]
    if len(owner_candidates) != 1:
        raise _fail("XOR owner identity mismatch")
    owner = owner_candidates[0]
    parameters = tuple((item.id, item.name, item.type.display(), item.direction)
                       for item in owner.parameters)
    if ((owner.signature.id, owner.name, owner.return_type.display(),
         len(owner.parameters), len(owner.body), _span(owner), _sha(owner),
         _sha(parameters)) != owner_record):
        raise _fail("XOR owner identity mismatch")

    parent_record = expected["parent"]
    parent_candidates = [
        value for statement in owner.body for value, _ in _walk_statement(statement)
        if _span(value) == parent_record[0]]
    if len(parent_candidates) != 1:
        raise _fail("uvec3 parent identity mismatch")
    parent = parent_candidates[0]
    if (parent.kind != "construct" or parent.type.display() != "uvec3"
            or parent.constructor_type is None
            or parent.constructor_type.display() != "uvec3"
            or len(parent.children) != 3
            or _sha(parent) != parent_record[1]):
        raise _fail("uvec3 parent identity mismatch")

    if (_scalar_census_fingerprint(program, parent)
            != expected["scalar_census_sha256"]
            or len(scalar_xors) != 3
            or any(owners[id(value)] is not owner for value in scalar_xors)
            or tuple(scalar_xors) != parent.children):
        raise _fail("scalar XOR cardinality, owner, parent, or order mismatch")
    for value, record in zip(scalar_xors, expected["sites"]):
        site_span, node_hash, left_hash, right_hash, lane = record
        if (value.kind != "binary" or value.operator != "^"
                or value.category != "rvalue" or value.type.display() != "uint"
                or len(value.children) != 2
                or any(child.type.display() != "uint" for child in value.children)
                or _span(value) != site_span or _sha(value) != node_hash
                or _sha(value.children[0]) != left_hash
                or _sha(value.children[1]) != right_hash
                or lane >= len(parent.children) or parent.children[lane] is not value):
            raise _fail("scalar XOR site mismatch")

    call_graph = tuple((function.signature.id,
                        tuple(calls[function.signature.id]))
                       for function in program.functions)
    main = [function for function in program.functions if function.name == "main"]
    if len(main) != 1:
        raise _fail("call graph or reachability mismatch")
    reachable: set[int] = set()
    pending = [main[0].signature.id]
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(calls.get(current, ()))
    unreachable = set(calls) - reachable
    # The six live carriers' owners are all conservative-call-graph
    # reachable, which stayed an unnamed hardcoded requirement until the
    # seventh synth/noise record: at NOISE_TYPE=10 the simplex arm of
    # `value()` bypasses the lattice path entirely, so
    # `constantFromLatticeWithOffset` is one of the 19 UNREACHABLE
    # functions -- the dead-code grammar class (cellRefract §17) whose
    # identity must still close.  The record therefore names which side of
    # the reachability split the owner must sit on, and the live default
    # stays "reachable" so the six frozen carriers behave byte-identically.
    owner_side = ("reachable" if owner.signature.id in reachable
                  else "unreachable")
    if (_sha(call_graph) != expected["call_graph_sha256"]
            or tuple(sorted(reachable)) != expected["reachable"]
            or tuple(sorted(unreachable)) != expected["unreachable"]
            or owner_side != expected.get("owner_reachability", "reachable")):
        raise _fail("call graph or reachability mismatch")
    return tuple(scalar_xors)


def authenticate_scalar_uint_to_float_narrowing_skips(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Return exact, observable JS-identity ``float(uint)`` constructs.

    The general typed emitter intentionally materializes scalar integral-to-
    float constructors as binary32.  The pinned canonical JavaScript erases
    all constructors in the complete six-carrier census below, but only
    Grain's unconstrained ``float(noise.x)`` is observably different in the
    admitted domains.  Reuse complete scalar-XOR program authentication,
    verify every census member, and return only the explicitly selected exact
    node.  This documents the blast radius without changing 31 safe sites.
    """
    authenticate_scalar_uint_xor(program, source_hash, profile)
    records = _UINT_TO_FLOAT_CENSUS_LOCKS.get(program.key)
    if records is None:
        raise _fail("scalar uint-to-float census carrier mismatch")
    _, parents, owners, _ = _collect(program)
    candidates = tuple(
        value for function in program.functions for statement in function.body
        for value, _ in _walk_statement(statement)
        if (value.kind == "construct" and value.constructor_type is not None
            and value.constructor_type.display() == "float"
            and len(value.children) == 1
            and value.children[0].type.display() == "uint"))
    if len(candidates) != len(records):
        raise _fail("scalar uint-to-float census cardinality mismatch")
    for value, record in zip(candidates, records):
        (site_span, site_hash, owner_id, owner_name, child_kind,
         child_span, child_hash, member, child_category, base_kind,
         symbol_id, symbol_name, parent_span, parent_hash, parent_kind,
         parent_operator) = record
        child = value.children[0]
        base = (child.children[0] if child.kind in {"swizzle", "construct"}
                and len(child.children) == 1 else child)
        parent = parents.get(id(value))
        owner = owners.get(id(value))
        if (owner is None or owner.signature.id != owner_id
                or owner.name != owner_name
                or value.category != "rvalue" or value.type.display() != "float"
                or _span(value) != site_span or _sha(value) != site_hash
                or child.kind != child_kind or child.type.display() != "uint"
                or _span(child) != child_span or _sha(child) != child_hash
                or child.member != member or child.category != child_category
                or base.kind != base_kind or base.symbol_id != symbol_id
                or ((base.symbol.name if base.symbol else None) != symbol_name)
                or parent is None or _span(parent) != parent_span
                or _sha(parent) != parent_hash or parent.kind != parent_kind
                or parent.operator != parent_operator):
            raise _fail("scalar uint-to-float census site mismatch")
    selected_spans = _UINT_TO_FLOAT_NARROWING_SKIP_SPANS.get(program.key, ())
    selected = tuple(value for value in candidates
                     if _span(value) in selected_spans)
    if tuple(_span(value) for value in selected) != selected_spans:
        raise _fail("scalar uint-to-float narrowing-skip identity mismatch")
    return selected


def apply_scalar_uint_xor(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> TypedProgram:
    """Authenticate the profile without transforming the frozen tree."""
    authenticate_scalar_uint_xor(program, source_hash, profile)
    return program


def authenticate_kaleido_float_bits_ingress(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Return kaleido's one exact ``floatBitsToUint`` node, or fail closed.

    Reuses the complete scalar-XOR program authentication (which already
    freezes kaleido's whole source, defines, functions, call graph and the
    three XOR sites -- and, per the per-key carve, tolerates the
    auto-attached fixed-array proof), then binds the ingress the same way
    the standalone Shapes ingress closure does: owner, statement ancestry,
    operand/parent identity, the positive-zero ``seedFrac`` initializer,
    complete reference censuses, a whole-program census of exactly ONE
    ``floatBitsToUint``, and downstream ancestry from each authenticated
    XOR lane's product to the declared ``fracBits``.  The row's existing
    ``scalar-uint-xor-v1`` carrier rides for this census -- no new row
    field; the caller admits the returned node by object identity on the
    Caustic/Scanline/Shapes skip-list precedent.
    """
    if program.key != KALEIDO_INGRESS_KEY:
        raise _fail("kaleido float-bit ingress carrier mismatch")
    xors = authenticate_scalar_uint_xor(program, source_hash, profile)

    owner_record = _PROFILES[KALEIDO_INGRESS_KEY]["owner"]
    owners = [function for function in program.functions
              if function.signature.id == owner_record[0]]
    if len(owners) != 1:
        raise _fail("kaleido float-bit ingress owner identity mismatch")
    owner = owners[0]

    located = []
    seed_frac_references = []
    frac_bits_references = []
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for value, _ in _walk_statement(statement):
                if value.symbol_id == _KALEIDO_INGRESS_OPERAND[4]:
                    seed_frac_references.append(value)
                if value.symbol_id == _KALEIDO_INGRESS_PARENT[3]:
                    frac_bits_references.append(value)
                if (value.kind == "builtin"
                        and value.callee == "floatBitsToUint"):
                    if function is not owner:
                        raise _fail("kaleido float-bit ingress outside the "
                                    "owner function")
                    located.append((index, statement, value))
    if len(located) != 1:
        raise _fail(
            f"kaleido float-bit ingress cardinality mismatch: {len(located)}")
    statement_index, statement, ingress = located[0]

    # The positive-zero initializer lock runs BEFORE the node hashes: the
    # operand's `Symbol` embeds the declaration span, so a coarser ordering
    # would let the node hash absorb the sign change.
    seed_frac_statement = owner.body[_KALEIDO_SEED_FRAC_STATEMENT_INDEX]
    if (seed_frac_statement.kind != "decl"
            or len(seed_frac_statement.expressions) != 1):
        raise _fail("kaleido seedFrac positive-zero initializer mismatch")
    seed_frac = seed_frac_statement.expressions[0]
    if ((seed_frac.kind, _span(seed_frac),
         seed_frac.type.display(), seed_frac.symbol_id,
         seed_frac.symbol.name, seed_frac.symbol.storage,
         seed_frac.symbol.writable, _sha(seed_frac))
            != _KALEIDO_SEED_FRAC_DECLARATION
            or len(seed_frac.children) != 1):
        raise _fail("kaleido seedFrac positive-zero initializer mismatch")
    initializer = seed_frac.children[0]
    if ((initializer.kind, _span(initializer),
         initializer.type.display(), initializer.category,
         initializer.literal, _sha(initializer))
            != _KALEIDO_SEED_FRAC_INITIALIZER
            or initializer.children != ()
            or not isinstance(initializer.literal_value, float)
            or initializer.literal_value != 0.0
            or math.copysign(1.0, initializer.literal_value) != 1.0):
        raise _fail("kaleido seedFrac positive-zero initializer mismatch")

    if ((statement_index, (statement.kind, _span(statement)))
            != _KALEIDO_INGRESS_STATEMENT
            or (ingress.callee, _span(ingress), ingress.type.display(),
                _sha(ingress), ingress.category) != _KALEIDO_INGRESS
            or len(ingress.children) != 1):
        raise _fail("kaleido float-bit ingress node identity mismatch")
    operand = ingress.children[0]
    if ((operand.kind, _span(operand), operand.type.display(),
         operand.category, operand.symbol_id, operand.symbol.name,
         operand.symbol.storage, operand.symbol.writable, _sha(operand))
            != _KALEIDO_INGRESS_OPERAND):
        raise _fail("kaleido float-bit ingress node identity mismatch")
    parent = None
    for function in program.functions:
        for walked in function.body:
            for value, upper in _walk_statement(walked):
                if value is ingress and upper is not None:
                    parent = upper
    if ((parent.kind, _span(parent), parent.type.display(),
         parent.symbol_id, parent.symbol.name, parent.symbol.storage,
         parent.symbol.writable, _sha(parent))
            != _KALEIDO_INGRESS_PARENT
            or len(parent.children) != 1
            or parent.children[0] is not ingress):
        raise _fail("kaleido float-bit ingress declaration parent mismatch")

    if (tuple((item.kind, _span(item), _sha(item))
              for item in seed_frac_references)
            != _KALEIDO_SEED_FRAC_REFERENCES
            or seed_frac_references[0] is not seed_frac
            or seed_frac_references[-1] is not operand):
        raise _fail("kaleido seedFrac reference census mismatch")

    owned_frac_bits = {id(item) for item in frac_bits_references}
    if len(xors) != len(_KALEIDO_XOR_ANCESTRY):
        raise _fail("kaleido downstream scalar XOR ancestry mismatch")
    consumers = []
    for node, record in zip(xors, _KALEIDO_XOR_ANCESTRY):
        (xor_span, product_operator, product_span, product_sha,
         consumer_span, consumer_sha) = record
        if _span(node) != xor_span or len(node.children) != 2:
            raise _fail("kaleido downstream scalar XOR ancestry mismatch")
        product = node.children[0]
        if (product.kind != "binary" or product.operator != product_operator
                or _span(product) != product_span
                or _sha(product) != product_sha
                or len(product.children) != 2):
            raise _fail("kaleido downstream scalar XOR ancestry mismatch")
        consumer = product.children[0]
        if (consumer.kind != "id"
                or consumer.symbol_id != parent.symbol_id
                or consumer.type.display() != "uint"
                or _span(consumer) != consumer_span
                or _sha(consumer) != consumer_sha
                or id(consumer) not in owned_frac_bits):
            raise _fail("kaleido downstream scalar XOR ancestry mismatch")
        consumers.append(consumer)
    if (len(frac_bits_references) != _KALEIDO_FRAC_BITS_REFERENCES
            or {id(item) for item in frac_bits_references}
            != {id(parent), *(id(item) for item in consumers)}):
        raise _fail("kaleido fracBits reference census mismatch")

    identities = [id(item) for item in (
        owner, ingress, operand, parent, statement, seed_frac, *xors)]
    if (len(identities) != _KALEIDO_INGRESS_LEDGER
            or len(set(identities)) != _KALEIDO_INGRESS_LEDGER):
        raise _fail("kaleido float-bit ingress visitation ledger mismatch")
    return (ingress,)


def authenticate_noise_float_bits_ingress(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Return synth/noise's one exact ``floatBitsToUint`` node, or fail closed.

    Reuses the complete live scalar-XOR record authentication (which
    already freezes synth/noise's whole source, defines, functions, call
    graph, the post-runtime-loop-bound summary and the three XOR sites),
    then binds the ingress exactly as the kaleido closure does: owner,
    statement ancestry, operand/parent identity, the -- here dynamic --
    ``fract(s)`` ``sFrac`` initializer (the Shapes/kaleido +0.0 literal lock
    does not apply to this program and is replaced by an exact two-node
    ``fract`` lock), complete reference censuses, a whole-program census of
    exactly ONE ``floatBitsToUint``, and downstream ancestry from each
    authenticated XOR lane's product to the declared ``fracBits``.  The
    landing lane admits the returned node by object identity on the
    Caustic/Scanline/Shapes skip-list precedent; no new row field exists
    until then.
    """
    from .noise_runtime_define_profile import is_dynamic_program, authenticate_noise_ingress
    if is_dynamic_program(program):
        return authenticate_noise_ingress(program, source_hash, profile)
    if program.key != NOISE_INGRESS_KEY:
        raise _fail("noise float-bit ingress carrier mismatch")
    xors = authenticate_scalar_uint_xor(program, source_hash, profile)

    owner_record = _PROFILES[NOISE_INGRESS_KEY]["owner"]
    owners = [function for function in program.functions
              if function.signature.id == owner_record[0]]
    if len(owners) != 1:
        raise _fail("noise float-bit ingress owner identity mismatch")
    owner = owners[0]

    located = []
    seed_frac_references = []
    frac_bits_references = []
    for function in program.functions:
        for index, statement in enumerate(function.body):
            for value, _ in _walk_statement(statement):
                if value.symbol_id == _NOISE_INGRESS_OPERAND[4]:
                    seed_frac_references.append(value)
                if value.symbol_id == _NOISE_INGRESS_PARENT[3]:
                    frac_bits_references.append(value)
                if (value.kind == "builtin"
                        and value.callee == "floatBitsToUint"):
                    if function is not owner:
                        raise _fail("noise float-bit ingress "
                                    "outside the owner function")
                    located.append((index, statement, value))
    if len(located) != 1:
        raise _fail(
            f"noise float-bit ingress cardinality mismatch: "
            f"{len(located)}")
    statement_index, statement, ingress = located[0]

    # The dynamic-initializer lock runs BEFORE the node hashes: the operand's
    # `Symbol` embeds the declaration span, so a coarser ordering would let
    # the node hash absorb an initializer mutation.  Where kaleido locks the
    # sign of a +0.0 literal, this program's `sFrac` starts life as
    # `fract(s)` -- the lock is the exact two-node `fract(<s>)` shape.
    seed_frac_statement = owner.body[_NOISE_SFRAC_STATEMENT_INDEX]
    if (seed_frac_statement.kind != "decl"
            or len(seed_frac_statement.expressions) != 1):
        raise _fail("noise sFrac fract-initializer mismatch")
    seed_frac = seed_frac_statement.expressions[0]
    if ((seed_frac.kind, _span(seed_frac),
         seed_frac.type.display(), seed_frac.symbol_id,
         seed_frac.symbol.name, seed_frac.symbol.storage,
         seed_frac.symbol.writable, _sha(seed_frac))
            != _NOISE_SFRAC_DECLARATION
            or len(seed_frac.children) != 1):
        raise _fail("noise sFrac fract-initializer mismatch")
    initializer = seed_frac.children[0]
    if ((initializer.kind, initializer.callee, _span(initializer),
         initializer.type.display(), initializer.category,
         _sha(initializer)) != _NOISE_SFRAC_INITIALIZER
            or len(initializer.children) != 1):
        raise _fail("noise sFrac fract-initializer mismatch")
    initializer_child = initializer.children[0]
    if ((initializer_child.kind, _span(initializer_child),
         initializer_child.type.display(), initializer_child.category,
         initializer_child.symbol_id, initializer_child.symbol.name,
         initializer_child.symbol.storage, _sha(initializer_child))
            != _NOISE_SFRAC_INITIALIZER_CHILD
            or initializer_child.children != ()
            or initializer_child.symbol.writable is not True):
        raise _fail("noise sFrac fract-initializer mismatch")

    if ((statement_index, (statement.kind, _span(statement)))
            != _NOISE_INGRESS_STATEMENT
            or (ingress.callee, _span(ingress), ingress.type.display(),
                _sha(ingress), ingress.category) != _NOISE_INGRESS
            or len(ingress.children) != 1):
        raise _fail("noise float-bit ingress node identity mismatch")
    operand = ingress.children[0]
    if ((operand.kind, _span(operand), operand.type.display(),
         operand.category, operand.symbol_id, operand.symbol.name,
         operand.symbol.storage, operand.symbol.writable, _sha(operand))
            != _NOISE_INGRESS_OPERAND):
        raise _fail("noise float-bit ingress node identity mismatch")
    parent = None
    for function in program.functions:
        for walked in function.body:
            for value, upper in _walk_statement(walked):
                if value is ingress and upper is not None:
                    parent = upper
    if ((parent.kind, _span(parent), parent.type.display(),
         parent.symbol_id, parent.symbol.name, parent.symbol.storage,
         parent.symbol.writable, _sha(parent))
            != _NOISE_INGRESS_PARENT
            or len(parent.children) != 1
            or parent.children[0] is not ingress):
        raise _fail("noise float-bit ingress declaration parent "
                    "mismatch")

    if (tuple((item.kind, _span(item), _sha(item))
              for item in seed_frac_references)
            != _NOISE_SFRAC_REFERENCES
            or seed_frac_references[0] is not seed_frac
            or seed_frac_references[-1] is not operand):
        raise _fail("noise sFrac reference census mismatch")

    owned_frac_bits = {id(item) for item in frac_bits_references}
    if len(xors) != len(_NOISE_XOR_ANCESTRY):
        raise _fail("noise downstream scalar XOR ancestry mismatch")
    consumers = []
    for node, record in zip(xors, _NOISE_XOR_ANCESTRY):
        (xor_span, product_operator, product_span, product_sha,
         consumer_span, consumer_sha) = record
        if _span(node) != xor_span or len(node.children) != 2:
            raise _fail("noise downstream scalar XOR ancestry "
                        "mismatch")
        product = node.children[0]
        if (product.kind != "binary" or product.operator != product_operator
                or _span(product) != product_span
                or _sha(product) != product_sha
                or len(product.children) != 2):
            raise _fail("noise downstream scalar XOR ancestry "
                        "mismatch")
        consumer = product.children[0]
        if (consumer.kind != "id"
                or consumer.symbol_id != parent.symbol_id
                or consumer.type.display() != "uint"
                or _span(consumer) != consumer_span
                or _sha(consumer) != consumer_sha
                or id(consumer) not in owned_frac_bits):
            raise _fail("noise downstream scalar XOR ancestry "
                        "mismatch")
        consumers.append(consumer)
    if (len(frac_bits_references) != _NOISE_FRAC_BITS_REFERENCES
            or {id(item) for item in frac_bits_references}
            != {id(parent), *(id(item) for item in consumers)}):
        raise _fail("noise fracBits reference census mismatch")

    identities = [id(item) for item in (
        owner, ingress, operand, parent, statement, seed_frac, *xors)]
    if (len(identities) != _NOISE_INGRESS_LEDGER
            or len(set(identities)) != _NOISE_INGRESS_LEDGER):
        raise _fail("noise float-bit ingress visitation ledger "
                    "mismatch")
    return (ingress,)


def authenticate_prepared_noise_float_bits_ingress(
        program: TypedProgram, source_hash: str | None,
        profile: str | None) -> tuple[TypedExpression, ...]:
    """Compatibility surface after the prepared Noise ingress landed."""
    if profile is not None:
        raise _fail("program key is not a prepared noise ingress carrier")
    return ()
