#!/usr/bin/env python3
"""Materialize the checked LightLeak192 pixel oracle for native tests."""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import math
import pathlib
import re
import struct
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/port-engineering/counted-for-parity/lightleak192-oracle"
ORACLE = PACKAGE / "lightleak192-oracles.json"
OUTPUT = ROOT / "tests/oracles/lightleak192_expected.inc"
SCHEMA = "noisemaker-for-cpp.lightleak192.pixel-parity.v1"
PROGRAM_KEY = "filter/lightLeak:lightLeak"
WORD = re.compile(r"0x[0-9a-f]{8}\Z")
HEX256 = re.compile(r"[0-9a-f]{64}\Z")
EXPECTED_ABI = {"inputTex": "sampler2D", "resolution": "Vec2", "tileOffset": "Vec2", "fullResolution": "Vec2", "alpha": "number", "color": "Vec3", "speed": "number", "seed": "int32", "time": "number"}
EXPECTED_CLOSURE = [
    ("src/csl/glsl-kernel.js", "a684b1bc16f095c550e488d1db35b9cea9c69b761db6ad3af175110e6a2e2baa"), ("src/csl/glsl-runtime.js", "a20421c56aa3274746f6887555445b8c7f7bb8318921fe6f75f6aa8ffe71c072"), ("src/csl/runtime.js", "a34ac04d63bb0865081ad3964b1ff5a427664a80e35f43c1761d91b0ea8e7dee"),
    ("src/effects/adapters/bit-effects.js", "5044fc318e69deb1e03330f977af1f8a76376c69936ebf0a6d33fe350379d7c7"), ("src/effects/adapters/crt.js", "c424c45169894e1d39eb11dc97c1835991fa9e990f3dd7c1aeefafbfe9f3a5cc"), ("src/effects/adapters/f32-color.js", "b0d2562969029701f44b049dbfa17fc7a13f97758c3750f05ad57a836269b046"), ("src/effects/adapters/fractal.js", "0c90d859a589d4bfd0f9a82b2f601675b6116671e20b2dfba9bab2b98fc72a29"), ("src/effects/adapters/index.js", "40c690ff6ef58619006d0819c5f0f4d419cdfd59a08db55e2276aa9f61430267"), ("src/effects/adapters/julia.js", "0f9cc65f966a358bc4671399e8de49d144d0272a07ef2ae15a0bfb57048eadd5"), ("src/effects/adapters/median.js", "e82f18d820533993f74c3436addd8bb271a3ef0db8a53c6771ba4eb1e90b0583"), ("src/effects/adapters/palette.js", "8b7c83ea52c3be218866570517335141f9203905115fc90d2e69b1d8cba54452"), ("src/effects/adapters/snow.js", "202e0dbf9b1b8e0e7278c87527d6e2b740eb0a23385115c4805a389caab96366"),
    ("src/effects/catalog.js", "d8cf312294ccd915892a4a668432ca2533ab255fb24664d89dee8456331e4ea4"), ("src/effects/definition.js", "fdade0a1f2ab0773b08b9778807d9901583a540c409a9a275cf2fc1c67f6af02"), ("src/effects/generated/canonical-adapter-data.js", "ca0b139d776f9433b72534f58df9ff182ec55369e85ce37d422990dc0184baab"), ("src/effects/generated/canonical-kernels.js", "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe"), ("src/effects/generated/kernels.js", "b535b989f0f130c44261815d90678deb9996ab30998bb8d1cb5591a8f8d8d3c01"), ("src/effects/generated/upstream-snapshot.js", "e8f8a421f08b0f5cb495f845a97da321038300b7d0dd41392a60653ce2a82090"), ("src/effects/registry.js", "8b3eac7fd4df8699bf27995987eb534625adbce5fe7aa432649a83f278af9618"), ("src/runtime/pass-runner.js", "fbfd53470735a07dca317c384b9985bb55383961199815e67aee9adda7e881aa"), ("src/runtime/sampler.js", "1e7dc92a20de983ce8b4afd03f3ea83bc86c010e622c4edc4a0aa702027ed328"), ("src/runtime/surface.js", "0cd69c920a710f636a5208e05b49633fc2747cdc2f5fc61113433ceb9ec8ba59"),
]
EXPECTED_CLOSURE[16] = ("src/effects/generated/kernels.js", "b535b989f0f130c44261815d90678deb9996ab3098bb8d1cb5591a8f8d8d3c01")
EXPECTED_MUTATIONS = [("out-cell-color-materialization", 1, ["color-blue"]), ("out-cell-dist-materialization", 1, ["default-nonsquare"]), ("base-bare-call-site", 1, ["default-nonsquare"]), ("warp-bare-call-site", 1, ["default-nonsquare"]), ("source-global-POINT_COUNT", 1, ["default-nonsquare"]), ("loop-bound-POINT_COUNT", 1, ["speed-high"]), ("alpha-control-axis", 1, ["alpha-half"]), ("speed-control-axis", 1, ["speed-high"]), ("seed-control-axis", 1, ["seed-axis"]), ("color-control-axis", 1, ["color-blue"]), ("time-control-axis", 1, ["time-negative"])]
EXPECTED_STRUCTURAL = ["unused-resolution-axis", "globalCoord-dead-value"]
EXPECTED_STRUCTURAL_DETAILS = {"unused-resolution-axis": "structurally authenticated binding retained; no pixel witness claimed", "globalCoord-dead-value": "structurally authenticated source mutation; no pixel witness claimed"}
EXPECTED_CASES = [
    ("alpha-zero-corner", 1, 1, {"alpha": 0, "color": [1, 0.800000011920929, 0.30000001192092896], "speed": 0.5, "seed": 1, "time": 0, "resolution": [1, 1], "tile_offset": [0, 0], "full_resolution": [1, 1]}),
    ("default-nonsquare", 7, 5, {"alpha": 1, "color": [1, 0.800000011920929, 0.30000001192092896], "speed": 0.5, "seed": 1, "time": 0, "resolution": [7, 5], "tile_offset": [0, 0], "full_resolution": [7, 5]}),
    ("alpha-half", 8, 6, {"alpha": 0.5, "color": [0.20000000298023224, 0.699999988079071, 1], "speed": 0.5, "seed": 7, "time": 0.125, "resolution": [8, 6], "tile_offset": [0, 0], "full_resolution": [8, 6]}),
    ("alpha-clamped-high", 5, 5, {"alpha": 2, "color": [1, 0, 0], "speed": 1.75, "seed": 17, "time": 0.75, "resolution": [5, 5], "tile_offset": [0, 0], "full_resolution": [5, 5]}),
    ("speed-zero", 6, 4, {"alpha": 0.800000011920929, "color": [0.800000011920929, 0.20000000298023224, 0.10000000149011612], "speed": 0, "seed": 3, "time": 1.25, "resolution": [6, 4], "tile_offset": [0, 0], "full_resolution": [6, 4]}),
    ("speed-high", 9, 7, {"alpha": 0.8999999761581421, "color": [0.10000000149011612, 0.8999999761581421, 0.30000001192092896], "speed": 5, "seed": 99, "time": 0.33000001311302185, "resolution": [9, 7], "tile_offset": [0, 0], "full_resolution": [9, 7]}),
    ("seed-axis", 7, 6, {"alpha": 0.6499999761581421, "color": [0.4000000059604645, 0.5, 0.8999999761581421], "speed": 1.2000000476837158, "seed": 64, "time": 0.625, "resolution": [7, 6], "tile_offset": [0, 0], "full_resolution": [7, 6]}),
    ("time-negative", 8, 5, {"alpha": 0.699999988079071, "color": [1, 0.10000000149011612, 0.6000000238418579], "speed": 2.25, "seed": 12, "time": -0.4000000059604645, "resolution": [8, 5], "tile_offset": [0, 0], "full_resolution": [8, 5]}),
    ("tiled-full-resolution", 6, 4, {"alpha": 0.75, "color": [0.8999999761581421, 0.800000011920929, 0.10000000149011612], "speed": 0.75, "seed": 23, "time": 0.4399999976158142, "resolution": [6, 4], "tile_offset": [7, 11], "full_resolution": [19, 17]}),
    ("color-blue", 4, 8, {"alpha": 0.550000011920929, "color": [0, 0.10000000149011612, 1], "speed": 1.5, "seed": 5, "time": 0.9100000262260437, "resolution": [4, 8], "tile_offset": [0, 0], "full_resolution": [4, 8]}),
    ("fullresolution-fallback", 5, 3, {"alpha": 0.8500000238418579, "color": [0.6000000238418579, 0.6000000238418579, 0.6000000238418579], "speed": 1, "seed": 8, "time": 0.20000000298023224, "resolution": [5, 3], "tile_offset": [1, 2], "full_resolution": [0, 0]}),
]
EXPECTED_INPUT_FIXTURE = {
    "schema": "noisemaker-for-cpp.lightleak192.input-texture.v1",
    "source_function": "inputSurface",
    "source_function_sha256": "31ca4a008de6ab3cfaafc0e0a1ed863153ddf6855d8f43aeb80b76963cc5a990",
    "coordinate_order": "x-fastest row-major",
    "component_order": ["r", "g", "b", "a"],
    "formulas": [
        "f(((x * 17 + y * 11 + phase) % 23) / 22)",
        "f(((x * 7 + y * 19 + phase * 2) % 29) / 28)",
        "f(((x * 13 + y * 5 + phase * 3) % 31) / 30)",
        "f(.4 + ((x + y + phase) % 5) / 10)",
    ],
}
EXPECTED_INPUT_CASES = [
    ("alpha-zero-corner", 1, "ed039d7f319e8306c6eb4be39a6b724ddc1ad61a8c57dc76f3dd18a485c79dfc", "df73bf99901c6c69913e77b9b56102cca3f42202b040d31e89b5589382d8a6ef"),
    ("default-nonsquare", 2, "4fb64a526cbb765bea0884dc46cc4f1bcca8c910061d6cbd2202657221a84a55", "cb85a2832f92c97b078d74998bf2041fb9a6e037cc8ed517cf998d2fd51afbe5"),
    ("alpha-half", 3, "e87d32690ffa12186440ebc6db1df5ac51dab928b9c2ef920817350d3f8479c3", "20218ddfabef6ada0db5689ce33bce3afc866595c2354cc6c8f27901e1c142eb"),
    ("alpha-clamped-high", 4, "09ac63b79d65d9a6c9c99471872a46e4113406ae9614ad521a99bf59d5c23915", "ed7a92f2156c9269f2a88136a2240f2bcdb03933f3746903b5adebfc9167f118"),
    ("speed-zero", 5, "cb126b7414aabf466843e761adda99ec1db4546b0e4a520ae7cae5a89e2f6601", "70931400f201335fe4ed446bfd9ef560a8ed8cd425e72b260f3124b55d74f026"),
    ("speed-high", 6, "da7ad02f0b3d6ae64d07164d824c768bac0ca690a84bbbaeef5e9f813c935406", "2bfeded7b6ab71885c19362a1fa259427178a0381d6f281035fef190d934fdd8"),
    ("seed-axis", 7, "55670a4fa3f91ed31071635be1049e2292722dc2e81b494dd786d2186c2de9fd", "a0de200f556331d66eff21af8186b758c8523c9199d5d40f8a7fe64e7ad51eea"),
    ("time-negative", 8, "c897bd33e47b014d61ec2fea344e3c6b4b66c61431ab2a1a849cb3f63de38ad5", "922758316b38882708c3742e7408ccd8ee4d9f70e5343cdd3d1465b562cca1db"),
    ("tiled-full-resolution", 9, "07f0b14d566e8ecbb521301f927e1c993dec028d8b0bc1d064f71cd9b8d45e9b", "8b9afafc15f6d27b9a641f5d5ffa8b9bbccc71b03f5c8a4034066b892e4365f7"),
    ("color-blue", 10, "a28638ac2e81bcbb0a907250a1de044b17a719b808ce093172bc7293475a31e5", "1a2b8bdeb671abe91d743e6a8965f67a31800b162352f0f97fbbbef1a2b833bf"),
    ("fullresolution-fallback", 11, "4220816a55d7a426a13aa647368de07431c0131f175ae9daf394270e7919d655", "c07a77ed2272e5894801655a02f95c40825a72409854079209a55e3227f82325"),
]
EXPECTED_OUTPUT_PAYLOADS = {
    'alpha-zero-corner': (
        'jC46PSVJkj3NzMw9AAAAPw==',
        'DBIagA==',
        'ed039d7f319e8306c6eb4be39a6b724ddc1ad61a8c57dc76f3dd18a485c79dfc',
        'df73bf99901c6c69913e77b9b56102cca3f42202b040d31e89b5589382d8a6ef',
    ),
    'default-nonsquare': (
        'PFbDPlOS5z52g7c+mpkZP0hFOD/HVwo/5VUlPzMzMz/Qzwk/jbcZP6BTqT7NzEw/kzMVP10aMj8XlBU/zczMPhJuuj5lpeQ+GGQyPwAAAD8WZz8/890WP4AZ9z6amRk/ooEZPyMWLz8L5DY/MzMzP8vdDD9Dfx0/8IbkPjMzMz92mQI/FNOjPggvHz/NzEw/UtV+PjkrAj86tGg+zczMPigkHz8WTv4+n0UoPwAAAD+GV7Q+KiL4PiYZpD6amRk/eL3OPn7gYz6HdhM/MzMzP8mlBz9/LBc/zoEzP83MTD8Y4qw+XVsiP3yTEj/NzEw/qpcpP+kz/z7tbEM/zczMPj8S1T5WmDQ/LRu8PgAAAD+ji84+AADgPry7Kz+amRk/pzmHPlAzDz/B+Kg+MzMzP3DVLz+x8ig/FqMWP83MTD8BbQw/JApAP4uziD7NzMw+QgMFP2gEBD/2FDI/zczMPphW8T6GNqg+vw3UPgAAAD+VS1c+Jw3LPoXtAz+amRk/8wcVP6PtJD+FCTA/MzMzP4buEj9wqsQ+i3yyPs3MTD+Pj/0+6iL7Psx+Oj/NzMw+o4s+PzVDAT/Y1cs+AAAAP31Zoj4ChTY/olRTPwAAAD9EdSg/HDnAPl4EAD+amRk/QKsbP6krET/OkjI/MzMzP6SaBT+OqAY/IfbePs3MTD+jiz4/E8AcP3YXDT/NzMw+huwwP0mSTD8mAj8/AAAAPyFeKz+/ng8/7hbpPpqZGT8=',
        'YXNbmbiKpbKJmVTMlbGVZl1ysoC/lnuZma62soydcrKCUp/MP4I6Zp9/qIBafFKZZzmTsoeXs8xWopLMqX/DZmq0XoBncKuZQ49Usq+olsyMv0RmhISxZnhUaoA2ZYOZlKSvspJiWcx+fbpmvoFmgFG204CoYICZm5GysoWGb8y+nI1msMy+gKuPdJk=',
        '6bff35a173c852fc5d94bb2619b6ea5f6dc7698dd5bec7cfe09cb5b7302d5bff',
        '35b9d6d6544070c88d4ebde30b156c89ebcb2ab2616eeb5c5bf2635c24fc15fd',
    ),
    'alpha-half': (
        'r1yEPqxIwT4X7No+MzMzP+CbXz+54As/1K09P83MTD+GOSE/THUxP95bqj7NzMw+sYbhPso4aj9qiCc/AAAAP2EBVT6uaao+IiJyP5qZGT8YqVc/930MPy7YBD8zMzM/9mUbPx5MOD9QKVM/zcxMP4k11j5itWY/TbPMPs3MzD7KziU/pvBZP/xPDz/NzEw/oLvWPliTUD6qIVw/zczMPvbnFz7Cc9c+q6qkPgAAAD+Rs1A/nhQaPx5fNj+amRk/tYELP2iySD+qNGQ+MzMzPyTpvz7AyRA+AAAVP83MTD/BfAg+dnzJPlZVbT/NzMw+kAVPP4BvJD9XPQg/AAAAP13IYj6E0hY/9K0zP83MzD4ybFM/R7s8PyLGKj4AAAA/UDwPPzyBjj1W9fA+mpkZPzKwsz6aOaE+w99VPzMzMz9+TaA9VwcAP688qj7NzEw/hkdJP+zNLz8S+TM/zczMPjoOCT+3bW0/zJRvPgAAAD/X0MM+Dy3EPrTqKD+amRk/YNsfPwAVsj56PE0/AAAAPwdktz4U8+k+rWeUPpqZGT/k2aU9Fs8lP+jLIj8zMzM/mBhJP6QlXT8VE8k9zcxMPz5KAz9MwlQ+KgPvPs3MzD5a2J0+9IDbPncOVj8AAAA/l6DVPUqYJj+8Pcg+mpkZP9YOST/AXFw/FEhCPzMzMz8igjA+zqhYP7xobj+amRk/WBJEPw02TD4AjtI+MzMzP+lWAD+sd8E+aqFMP83MTD9omKg+HLsGP7y7ez7NzMw+x31yPfx6RT8AACM/AAAAP50ROj/gWQY+RUTsPZqZGT/4kgE/YuzHPu++Aj8zMzM/8Fm0PoFaED9Umlo/zcxMP0xzEz/Qlxo/Eo+xPjMzMz/ll7Y+MPxAP+6rFj/NzEw/92zYPZIkdT/4DW4/zczMPu8hQj/WeMg+vgrxPgAAAD/Xxwk/PMARP4JkUz+amRk/NFCmPguWNz+QrLs+MzMzP3TRcT9CgWs/rvksP83MTD8GuT0/BmXDPom6iz7NzMw+',
        'QmBtst+LvcyhsVVmcOmngDVV8ZnXjISym7jSzGvmZmal2Y/MazTbZiZrUoDQmbaZi8g5smAklMwiZOxmzqSIgDiWs2bTvCuAjxJ4mVlQ1bIUgFXMyK+zZontPIBiYqiZn1nMgFt1SpkVpaKyyNwZzIM1d2ZPbdWAG6ZkmcjcwrIs2O2ZwzNpsoBgzMxUhj9mD8WigLkhHZmBZIKyWpDazJOaWLJbwJbMG/TtZsFkeICJkdOZU7ddsvHrrMy9YUZm',
        '50239ad9fa16b442bc81251b0ad51902a6faade542daf815c36642ba83a08804',
        '61352e5aa0d2a2237d4c506df926c2de40a1e09d65b03fdf2912dd8a7b83a989',
    ),
    'alpha-clamped-high': (
        'GWHOPp9ayj5nW/M+zcxMP04bSz/PpAE/fs8vP83MzD55URw/27oTP32TsD4AAAA/2Z0NP979bD5zXS8/mpkZP22Btj7mqdg+TPpXPjMzMz8+6Bs/7Do5PwQXGz/NzMw+DmQTPwZs2j4SEVE/AAAAP3s4rT4ydiU/mQvYPpqZGT8y0D4/3b0aP/H3Kz8zMzM/84kTPwNRMT+Fgq8+zcxMP5Dwtj7HOgs/UBwbPwAAAD/fxj4/glwhP/8X5T6amRk/XXQBP5IkqT4RERE/MzMzPwTZzj7+6tg+AAAwP83MTD9e6ak+m1IDP+Is8j7NzMw+VVwPP6r8DT9saDs/mpkZP+/cCD/lE+Y+VXbtPjMzMz9nH5k+zYgJP2uHNj/NzEw/fM80P5IkQT9oTqQ+zczMPvrKCT9w2gU/uIwaPwAAAD8Wsac+KXVSP9mInz4zMzM/VoM7P7y53D5FOMg+zcxMP36aCz8xywk/OAU9P83MzD47Mvo+B6caP762Bj8AAAA//4qUPvqpTD8GSjw/mpkZPw==',
        'Z2V5zMqBr2ack1iAjTuvmVtsNrKbuZpmk23QgFalbJm+mquyk7FXzFuLm4C+oXKZgVSQsmdsr8xVg3lmj427mYhzdrJMibbMtMBSZomFmoBU0k+yu25kzIuJvGZ9moaASsy8mQ==',
        '65d5177542142949f07f5e38444a9ec020557ddc90230f4e4e7b927e2a404fe2',
        '93ed8d704db14a0f363253c738f87e78bf3681ece1de85b127238c62f8922a3e',
    ),
    'speed-zero': (
        'Eu3WPq7c8z6KFw8/zczMPp4SZD9JiBs/0DNVPwAAAD99Ziw/yPs6P+zEyT6amRk/FPUXP7zXcj4VfTk/MzMzPz7qvj5WcOc+pSKVPs3MTD9oP2s/KYwfP/SgLT/NzMw+NXkwPw8YgT58/DI/AAAAP48dEj8RMqo+pQuVPpqZGT+sDp0+PfsNP3aBAz8zMzM/NcxTP/NPDj+6CEg/zcxMPzxkFT+SJEk/1EXOPs3MzD4oLhc/zkvFPmNeOz8AAAA/R1LPPsgcIT+LeFI/mpkZP2FfTz8fC1A/APWvPjMzMz9xAQ8/AhytPmlMJz/NzEw/24UJP8wE2D5rpmA+zczMPtHlmz6bsRI/A2sKPwAAAD+7OVg/vIhQP30yRj+amRk/t90yP68V2z6PwnU/MzMzPz1PDD+/7wU/2sXgPs3MTD9rb68+E1A4P3feUT/NzMw+lQJXP152hj4gvac+AAAAP+WEHz+XVd0+BxshP5qZGT9fSgQ/xaAJP2NWYj4zMzM/',
        'a3mPZuOb1ICsumSZlzy5sl9zSszqn61msECygJJVSplOjYOy047HzJXIZ2aXYruAZ6DSmc/PWLKOVqfMiWw4Zk6SioDX0MWZsm31soyFcMxXuNFm1kNUgJ9uoJmEiTiy',
        '01e9a26bbe1da956157359bc3d914890e6ef969d9ae607d94ca139f85d76316f',
        '31e9f93b440b8f28ee9d825344341b7d46ee8fd2bc6d87c7d0c8e185fa4cbb83',
    ),
    'speed-high': (
        '64TaPjk2MD8APy4/AAAAP+ShnD76lzc/b8GiPpqZGT/oBTE/cj1FP5yXCz8zMzM/SBAPP5xgAj/YlTU/zcxMPwH34T7+RjE/HfHQPs3MzD5AuWM/X3wqPyaoLD8AAAA/tvMnPz+KPj8Ju7w+mpkZP/iABj+xLtA+N5QxPzMzMz/bDLQ+kRskP0ExUD/NzEw/deoxP1wy8T6hszI/mpkZPxWtCz8UlPU+lRyJPjMzMz8iV84+9cgOP1qoID/NzEw/fsNWPy6mFT8ZEIE+zczMPhXnEj+B5YQ+kK/uPgAAAD/FaSA/uHT+PpCZLT+amRk/Vy65PqUoBj9c95s+MzMzPymVUj8KIAg/5KEVP83MTD9DyBs/sa68PiYDxj7NzMw+hJG1PlhYJj/NilI/MzMzPwy8Qj/fyVA/wPrQPs3MTD8+sR8/OWTgPmgKKj/NzMw+BKsPP4IfEj+Gk4s+AAAAP4Ptkz6QXQE/hdAZP5qZGT+dSFk//TBBP214WD4zMzM/rfgTPwlSzT7A4OA+zcxMP2iy6T5j8A0/MuoeP83MzD4TVI8+DvQ0P+FOAj8AAAA/EBczP2j7Fj/aGtI+zcxMP+u/DD+Y9BY/CqrtPs3MzD7cvJU+/GQvPy1/OT8AAAA/DkVZP+THoj4D1ao+mpkZP4FyEz9wjOw+kHspPzMzMz9B6gM/ybAAP/w/iz7NzEw/WTmAPgBeJj8D8ho/zczMPr10VT/6Oag+LCBfPgAAAD+chR8/AR8LP49PCz+amRk//RqrPslC4j5xpNw+zczMPs+nUj/yIfM+wf4ePwAAAD/87hM/fy/hPgsJkT6amRk/MPsDP+ShEz+YLAA/MzMzP2L2eD69JFo+o2M5P83MTD9hp00/SabsPtYlqz7NzMw+YWQIP+N4Aj9M+ik/AAAAP9DV1z4RLSQ/7AHGPpqZGT/ex3E+vDFYPy4iLj8zMzM/x/cdP5JbKz9EV+k+AAAAP3UeET8rs1E/U31DP5qZGT+7HqI+9CLtPr15rj4zMzM/JA1BP1ti/T7LMig/zcxMP/zE+D51nwU/awmPPs3MzD7wEgk/vT5CP98U/T4AAAA/gOSIPrYz3j6gbTU/mpkZP/ssPT+RF+0+/AXPPjMzMz+zmgo/M1YePx38TD/NzEw/Iq6bPkR7DT9YzBQ/mpkZP6hvSj9YpRc/2c5nPzMzMz9I2BM/MWFBP6f95D7NzEw/1/ULP+m88j7mUlI/zczMPrjomz4qqg4/2DvPPgAAAD8RLkg/SWwMPxpXLj+amRk/fusMP6tSOz+1bcM+MzMzPw+p2j6LrNU+looXP83MTD/X/24+WQAeP/N6Uj/NzMw+',
        'bbCugE63UZmwxIuyj4K1zHGxaGbjqqyAp75emYZosbJao8/MsXiymYt6RLJnjqDM1pVAZpJCd4Cgf62ZXIZOstKIlcybXmNmWqbSssLQaMyfcKlmj5JGgEqBmZnYwDayk2ZwzHSNnmZHtIKAspZpzIyWdmZLr7mA2FFVmZN2qbKDgEXMQKaaZtVUOICfi4uZVXFuZtJ5noCTcEiZg5OAsj42uczNdlVmiIKpgGukY5k8162ynat0gJHRw5lRdleywH6ozHyFR2aJwX6ARG+1mbx2Z7KKnszMTo2UmcqX57KTwXLMi3nSZk6OZ4DHjK6ZjLthsm1ql8w8ndJm',
        'ab7c9a9a97441c4540825a34da8392f5efcf8bc545e93ac2186f630ac9879629',
        '42cff95df4a84cd3ee600218cf3a8165292c744d17f8d48e0f97e211958420a3',
    ),
    'seed-axis': (
        'mJrnPtQiJD+s1Tc/mpkZP1KMLj5ycTM/W6W5PjMzMz/MOUc/C1doP+YZIj/NzEw/KfoMP+9nzj5RZGE/zczMPqjLzD7XpB8/RN31PgAAAD+2z4g+hKM2P4Q/Rz+amRk/HABIP2ZCaD8EtMw+MzMzP7hVSj9mJcA+G0dXPzMzMz9q6gI/2pLqPilFqD7NzEw/xfS5Pjg4IT+nKik/zczMPiXJGT6rUkQ/0WVxPgAAAD8iEzE/MaBdPjYcDT+amRk/FN/hPv6v6T6oMFg/MzMzP7m20j5rNjI/kigGP83MTD8tLdM+UaRFPwwsnD7NzEw/yxHsPTdHOz64+Ng+zczMPvLCNz9mEss+Df5BPwAAAD8/BQA/MVf2PjeQpD6amRk/ZTCRPqNCLT+VYyU/MzMzPw5rZz9upQQ+VTxbPs3MTD/Kgz4/A0L0Pm/DIz/NzMw+bSJHPytKFj+FKsA+zczMPrE6DT9E4iA/CYkVPwAAAD/nMJE+hd9aP+7U5D2amRk/HbtjP2WPkz4L9d0+MzMzPwsmLD/fJvg+SwRCP83MTD/mWPY+/GstP10RxD7NzMw+mtWZPvkiXD/14TM/AAAAP5GTtz55saU++QPmPgAAAD+cSFk/ts6zPjJIPD+amRk/LzsmP9GLBj/ty24+MzMzP2nKCz8HGkU/i/IZP83MTD8Ft40+4+lhPs7l/z3NzMw+3oZjP//b0D7uwPU+AAAAP7MAKj97iBY/4cRIP5qZGT/QIT4/67RHP0D/Ej+amRk/D0MMP+aOaT6Qi2U/MzMzPz3eoj5UdeA+zBrdPs3MTD+Ib2g/m4kOP50sST/NzMw+TAQtP04ROT+NK7s+AAAAPwWoAz98RWo/pnojP5qZGT9LJ5o+G5TaPrGqfj4zMzM/',
        'c6O3mSuzXLLG56HMjGfhZmafeoBEtsaZx+dmsspg1rKCdVTMXaGpZibEPICwN42ZcHTXsmmyhsxpxU7MHS9sZrdlwYCAe1KZSK2lsuchN8y+eqNmxpZgZo2glYBI2hyZ40lvsqt8wcx7rWJmTduzgFtTc4DYWryZpoY7sovEmcxHOCBm42h6gKmWyJm9x5KZjDrlslFwbszojshmrLhdgIPpo5lNbT+y',
        '334678f05527a44a00b5f6e28300cfa70307e4057e79b1c27d85acd52792f70d',
        'a2670fd61be4c3df3feefee69c99dab575cc46cfcff50484159912d9f7dc2b26',
    ),
    'time-negative': (
        'CasPP/PtGD8DN0s/MzMzPzkZnD5DdT8/FLDCPs3MTD8TeVI/rn03Ph5cNj/NzMw+mqYXP1IQ5j43WXw+AAAAP5Y5/D7fRQs/xN8OP5qZGT9At5E+pUIzPxBsTz8zMzM/z0xNP/duMD4F1PM+zcxMP4keIj9v9tM+499DP83MzD5iU1Q/cI/TPg7maD/NzEw/93oQPxxYCD/gm94+zczMPon61j6eSRE/gaI/PwAAAD8Fvxk+itdQP8UmXj6amRk/evk4P6cKlD5UgCU/MzMzPxl/5z6LGAk/HvU1Ps3MTD9HUbk+G/MlP8o+Cj/NzMw+hRKxPiKEUT/RA1A/AAAAPwPhAz8onk4/ELqwPs3MzD6kuhQ+ShiJPkbHBD8AAAA/YW9BP74e2T7AHVc/mpkZP4qC9j74MQs/OMK7PjMzMz/9daw+OfM6P7mZPD/NzEw/08wLPldETj4L1Ig+zczMPtn+PD+MiMQ+augfPwAAAD8I+xg/3ZYVP7iRgD6amRk/4XlNP/MCBz8Mu/Q+AAAAP3GaBT/1RjM/yqQqP5qZGT/CqcE+pjQcPvdiZj4zMzM/kKrePWHfzT4etAY/zcxMP2c+Lj9B3es+DYFUP83MzD5I8gk/62UlPxaSuD4AAAA/10rJPjMzYT96B0Y/mpkZP2LtXz+ritE+dVTBPjMzMz8oBwA/VL6/PrL6CT+amRk/PyhyPmZN9j6it1Q/MzMzPz77QD9xsx0/omPcPs3MTD+3Sxg/vf1YP0jXOD/NzMw+ZDvdPl8wjT7356g+AAAAP2LtXz/MZv4+fnMWP5qZGT/Xwzs/rWgeP/91XD8zMzM/mAohP1zdWD9/2PU+zcxMPw==',
        'j5jKsk6/YczSLrZml3M/gH6LjplJs8+yzCx5zKFqw2bTaejMkIhvZmuRv4Am0DeZuEqlsnOJLcxcpYpmWNHPgIPOWGYlRISAwWzWmXuLXrJWurzMIzNEZrxin4CYlUCZzYZ6gIWzqplgJzmyHGeGzK511GaJpVyAZODFmd9oYLKAX4mZPHvUssCdbsyY2LhmbkZUgN9/lpm7ntyyoNh6zA==',
        '35cad887c80ce3b1c85155bd39fc12a42fb167b6883903342f9c56db36c815ac',
        'e3ca807698433e7eb2a71e0c330251400f158fc04cc11d0cf690cd4dfea3f642',
    ),
    'tiled-full-resolution': (
        '7f7/PgsRKT8yy1c/zcxMPy//iz4yEkw/ehbDPs3MzD5sAFc/bBmUPpvmMT8AAAA/Ou4WP2DeAz+Ke4c+mpkZPw4I3T6KciY/ZFomPzMzMz/60Ug+jeRIP8zMYz/NzEw/ZS9WP7p4zD7nKUk+zczMPsqMGD9OUww/8FrkPgAAAD9ddv4+jPEfP1mxRD+amRk/ZoxwPnd0Kj7vgaY+MzMzPwa3Rj+eRcY+E6UlP83MTD/CSwg/gL4IPy1Lez7NzMw+hvHlPlooYT8qo4I+AAAAP1lkSj77hsM+yw4VP5qZGT+90EE/8abtPtqaMj4zMzM/Qiv6PlBeED85Des+zcxMP47HxT4esUo/HJk2P83MzD643RI+9NGVPnBrwj4AAAA/SktUP3uJDD+He6o+mpkZPyqvEz/utEc/ih88PzMzMz/u3Ms+SIpMPp6WgD7NzEw/Zc0BPnZCwD4nXBw/zczMPtmxRD8ClAg/JusCPgAAAD+kSgQ/T75DP9HR6T6amRk/',
        'f6jXzEbLYWbWSrGAloNDmW6mprIyyOPM1WYyZpiMcoB/n8SZPCpTssZjpcyIiD9mc+BBgDJhlJnBdiyyfZB1zGPKtmYlS2GA04xVmZPHu7JmM0DMIGCcZsSIIYCEw3SZ',
        '72e91e950d96baded0b18977518650868dae24df10d44ee37ea01b36261cd26f',
        '7b46999074364e0fa67d4151f2cc4e7002db0aa4a629e80bdb77734b36407b2f',
    ),
    'color-blue': (
        '6Aj2Pp3MLT9VnHc/zczMPtRYkD4z72g/SrkRPwAAAD8FfG0/ZoaMPuhVVD+amRk/yJcqP4No+D5Hb8o+MzMzP1rnaT/a49Q+LqyVPgAAAD9UgCg/yhgcPyafEz+amRk/VW/nPtEfQj/QaWk/MzMzP7LQOz41eg0+kyTxPs3MTD9Xoeg+3ci6Pc+Y1z6amRk/qSAsPlu3mT4Ddiw/MzMzP91QYT9nt/s+KcZOPs3MTD9jOyI/bUIzPxatID/NzMw+539kP5RJKz9PFAc/MzMzP7lSID83F1w/E6FWP83MTD9dpb8+vC1ZPpPHuT7NzMw+LB0oPmME2j5ZTTo/AAAAP8amxj7VzbU+EyMpP83MTD/XEPc9wbkKP6V5BD7NzMw+FqBVP6HTOz8f4/o+AAAAPz6yGD9C+Ow947hWP5qZGT/bHFg/4MlwPzkMRj/NzMw+udwUP6A6mz7ri4U+AAAAPxWNqT7CLv4+CpoeP5qZGT+rZ/09vI8pPzvOOj4zMzM/bzW6PnnkGj89Fms/AAAAPy138D1g3VY/NqDUPpqZGT8GiUY/XGJiPgXIST8zMzM/fj0JP5lQuz48Sqg+zcxMPytgTT88X7k+hoqoPpqZGT/98BA/2mcDP8EJFz8zMzM/6SazPtEyPT+JCWg/zcxMP+G4Dj6+i7Q9gIz8Ps3MzD4=',
        'e633ZkjokYDtRtSZqnxlsulqS4Com5OZc8Hpsi8jeMx0F2uZK02ssuB9M8yis6Bm5KuHsqDb1sxfNl1mKm26gGNbqMwfiiFm1bt9gJge1pnX8MVmlE1DgFR/npkgqS+yXZrqgB7WapnGOMmyiV1UzM1cVJmQg5ayWbznzCQWfmY=',
        '6e36d473b699b0d3ada89c4000913c7aa9396b54347a305e5e96e5de24c0d652',
        '42a0c75c83a23393e985b297893594d4a3b021a6dbc565708d60d3194f867af9',
    ),
    'fullresolution-fallback': (
        'QOs1P/a8Pj86JNQ+AAAAP5zo+j4+Fe8+zQ8mP5qZGT83x2Y/LGYeP0jgTD8zMzM/GWc+P7rSKz+BwhU/zcxMP6krMD+a6Dk/XINHP83MzD7bN1s/Qds1P9zxBz+amRk/5VAvP+gtJz9EIUE/MzMzP+LHST/x90M/MycXP83MTD8Thyo/rJgGP7dmQD/NzMw+O7BUP/EuMT9oZUc/AAAAPxGCCj/PL4M+qizFPjMzMz+PFpk+CV+9PocnQz/NzEw/KcxdP6Ra9z6FX6o+zczMPtRJJj/CSTU/vNUhPwAAAD/XhSs/MHn4PhC1yD6amRk/',
        'tb5qgH13pZnmnsyyvquVzK+5x2batYeZr6fAssnDl8yqhsBm1LDHgIpBYrJMXsLM3XtVZqa1oYCrfGSZ',
        'e3bb2b0dd471ffab8a2f50b4e306394907e62e849dbcbaaa9e32780f963827b4',
        'eef16e203d410260366641eb7798613640ed68c7738b34e3bfcf3e24f3628ee7',
    ),
}

_DIVERGENCE_A = ["default-nonsquare", "alpha-half", "alpha-clamped-high", "speed-zero", "speed-high", "seed-axis", "time-negative", "tiled-full-resolution", "color-blue", "fullresolution-fallback"]
_DIVERGENCE_B = ["alpha-zero-corner", "alpha-half", "speed-zero", "speed-high", "seed-axis", "time-negative", "tiled-full-resolution", "color-blue", "fullresolution-fallback"]
_DIVERGENCE_C = ["alpha-half", "alpha-clamped-high", "speed-zero", "speed-high", "seed-axis", "time-negative", "tiled-full-resolution", "color-blue"]
_DIVERGENCE_D = ["alpha-half", "alpha-clamped-high", "speed-high", "seed-axis", "time-negative", "tiled-full-resolution", "color-blue", "fullresolution-fallback"]
_DIVERGENCE_E = ["alpha-half", "alpha-clamped-high", "speed-zero", "speed-high", "seed-axis", "time-negative", "tiled-full-resolution", "color-blue", "fullresolution-fallback"]
EXPECTED_MUTATION_DETAILS = {
    "out-cell-color-materialization": ("a1bc8f2141307b814b54a9879ec5c9299d0ab907abe4b97d5d047874b11dc718", _DIVERGENCE_A, [{"case": "color-blue", "mismatched_lanes": 92, "first_mismatch": {"lane_index": 0, "top_down_xy": [0, 0], "channel": "r", "reference_bits_le": "0x3ef608e8", "candidate_bits_le": "0x3f1883fe"}}]),
    "out-cell-dist-materialization": ("f4195b0ac1905567146b18d55f5767d5aa4056290a633dcb79f88d666a3d9294", _DIVERGENCE_A, [{"case": "default-nonsquare", "mismatched_lanes": 97, "first_mismatch": {"lane_index": 0, "top_down_xy": [0, 0], "channel": "r", "reference_bits_le": "0x3ec3563c", "candidate_bits_le": "0x3ec3015f"}}]),
    "base-bare-call-site": ("2bb11f4d347c2e621dc9a05479130d9c943c3b5e6706a984fbc2f03824664bc2", _DIVERGENCE_A, [{"case": "default-nonsquare", "mismatched_lanes": 96, "first_mismatch": {"lane_index": 0, "top_down_xy": [0, 0], "channel": "r", "reference_bits_le": "0x3ec3563c", "candidate_bits_le": "0x3eb96fcd"}}]),
    "warp-bare-call-site": ("04d93bcce5c36f9f3e1613fcdbe529f2a1d53d589793c6c0ebb7a9a439034eec", _DIVERGENCE_A, [{"case": "default-nonsquare", "mismatched_lanes": 96, "first_mismatch": {"lane_index": 0, "top_down_xy": [0, 0], "channel": "r", "reference_bits_le": "0x3ec3563c", "candidate_bits_le": "0x3ec941ba"}}]),
    "source-global-POINT_COUNT": ("537bb3dd75b09bad1b00b22cbd2569e33a471bb757eef4801f2d583ea636e121", _DIVERGENCE_A, [{"case": "default-nonsquare", "mismatched_lanes": 36, "first_mismatch": {"lane_index": 64, "top_down_xy": [2, 2], "channel": "r", "reference_bits_le": "0x3ed5123f", "candidate_bits_le": "0x3ed5028e"}}]),
    "loop-bound-POINT_COUNT": ("2147226a38833360194e3af0d2eaa050ee52d03b55fadfc9e28f0a282c438b63", _DIVERGENCE_A, [{"case": "speed-high", "mismatched_lanes": 49, "first_mismatch": {"lane_index": 80, "top_down_xy": [2, 2], "channel": "r", "reference_bits_le": "0x3f1fb13e", "candidate_bits_le": "0x3f1fb0ee"}}]),
    "alpha-control-axis": ("fd68715b20b29d8ba7f6c9f7a1e3cb0f8daddf85a45af4811de1177137c91925", _DIVERGENCE_B, [{"case": "alpha-half", "mismatched_lanes": 144, "first_mismatch": {"lane_index": 0, "top_down_xy": [0, 0], "channel": "r", "reference_bits_le": "0x3e845caf", "candidate_bits_le": "0x3eac9a9c"}}]),
    "speed-control-axis": ("4028d4b05dc6c52b7092af75a207a4df044e3894bcc2f36f7352d49aa94328f1", _DIVERGENCE_C, [{"case": "speed-high", "mismatched_lanes": 175, "first_mismatch": {"lane_index": 0, "top_down_xy": [0, 0], "channel": "r", "reference_bits_le": "0x3eda84eb", "candidate_bits_le": "0x3ec98e59"}}]),
    "seed-control-axis": ("04ddc63725c5fc53130a7ace86f71e1d3f31f3820676ffe46f1b2be26e630958", _DIVERGENCE_E, [{"case": "seed-axis", "mismatched_lanes": 121, "first_mismatch": {"lane_index": 0, "top_down_xy": [0, 0], "channel": "r", "reference_bits_le": "0x3ee79a98", "candidate_bits_le": "0x3ee48365"}}]),
    "color-control-axis": ("50a438493d54951e9425cec901978401e8d5e8de5c7273003ee29993f5e07a99", ["default-nonsquare", "alpha-half", "alpha-clamped-high", "speed-zero", "speed-high", "seed-axis", "time-negative", "tiled-full-resolution", "color-blue"], [{"case": "color-blue", "mismatched_lanes": 93, "first_mismatch": {"lane_index": 0, "top_down_xy": [0, 0], "channel": "r", "reference_bits_le": "0x3ef608e8", "candidate_bits_le": "0x3f0fe9ba"}}]),
    "time-control-axis": ("f1453e261a4954544cecb3feef9692de18e37116902cf44812293ead2e7ce3ee", _DIVERGENCE_D, [{"case": "time-negative", "mismatched_lanes": 116, "first_mismatch": {"lane_index": 0, "top_down_xy": [0, 0], "channel": "r", "reference_bits_le": "0x3f0fab09", "candidate_bits_le": "0x3f08a9e0"}}]),
}
EXPECTED_MUTATION_ANCHORS = {
    "out-cell-color-materialization": ("mix(hash33(s), color, 0.6000000238418579)", "mix(hash33(s), new $runtime.PooledFloat32Array([1, 1, 1]), 0.6000000238418579)", "433f04a5bfc4f79b830e6265c9b8906ed3319d93e4f3bba03afaf5db737b7069", "00e70b0adb73bc4c93ff294d545623a634f445d361582df2fac9767096de977e"),
    "out-cell-dist-materialization": ("voronoiCell.__out__ = [cell_color, cell_dist];", "voronoiCell.__out__ = [cell_color, cell_dist + 0.01];", "7ee38ff535aacbcd6ec0de1fb103a7fc73b0085fb243a0e1574077055fd567d2", "09581aee41866049af735501539d5b06ff9999c3064e65708e6872d1a53a8883"),
    "base-bare-call-site": ("seed_f, t, base_cell", "seed_f + 1, t, base_cell", "df047d8739f8adff0add7437790becd8447f3f54ff92124bdb42403d6ebffe36", "64ab66080dcaac85435378c32d7f6ab3e6b97452dbc92e218e4853985cab3165"),
    "warp-bare-call-site": ("seed_f, t, warp_cell", "seed_f + 1, t, warp_cell", "763e97aa4a248be5930ff1368b585d43146360f17b2dcd87d3762528e4d2c779", "951b86e80970a4db5e457ffe3b63536b39c332f6ff9ea7337f4d8002811d97b4"),
    "source-global-POINT_COUNT": ("var POINT_COUNT = 6;", "var POINT_COUNT = 5;", "19f8c9c9bf24f1f51ec34badd04d650ebae0ad2c88579c9c9a951d32869499fc", "66cf45aab4ccdeb316ea9a036c0f2b9c46ddcc716d6ed6f3377c96232d75eda2"),
    "loop-bound-POINT_COUNT": ("i < POINT_COUNT", "i < 5", "d0c105eb94bea46e6c3e4c98272fa2ec904aa9e2ba417875e0a7c69c717e716d", "421d89772125e9af801bdf6c4dedf15f0d9ef7a9e02437459c86da2fc5675694"),
    "alpha-control-axis": ("var blend_alpha = clamp(alpha, 0, 1);", "var blend_alpha = 1;", "da505e3ea4dde1ad042e106b61b64f96c06262bce9b9a8267d73a798a86e4057", "7ef0f7a9324f9035e97c8ceb63ce971a68fb00a6681f5b08de590ed3ca275540"),
    "speed-control-axis": ("var t = time * speed;", "var t = time;", "c0ad52e48c15c95d9056325acd6f0ea90071b590822d6384925571431939581e", "d3813242ed8e241ddc318846417c6816448ab4cfbafb6a4d378c7c7e1e0ac2d1"),
    "seed-control-axis": ("var seed_f = (seed);", "var seed_f = 1;", "fb68f43d90cfeafe7dbcef72ef45a82eff29a45a6992f9ce7052ac7fcf1963c1", "5cf32c41d895de9d5816b3d8c13ed1eb949544b376a9fa6b38d2204f71dca98f"),
    "color-control-axis": ("mix(hash33(s), color, 0.6000000238418579)", "mix(hash33(s), new $runtime.PooledFloat32Array([color[2], color[1], color[0]]), 0.6000000238418579)", "433f04a5bfc4f79b830e6265c9b8906ed3319d93e4f3bba03afaf5db737b7069", "9858acba8e30c75db68b26f81cc5c58b919d7ae5a7e5831156a5fb7797510c52"),
    "time-control-axis": ("var t = time * speed;", "var t = -time * speed;", "c0ad52e48c15c95d9056325acd6f0ea90071b590822d6384925571431939581e", "48c346594ace3720177c4e16aa06fc4860bf1a6e2d697c747d8a7b3db3ebc056"),
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sidecar_text(target: pathlib.Path, payload: bytes) -> str:
    return f"{sha256(payload)}  {target.name}\n"


def verify_sidecar(target: pathlib.Path) -> bytes:
    sidecar = target.with_suffix(target.suffix + ".sha256")
    if not target.is_file() or not sidecar.is_file():
        raise RuntimeError(f"missing sidecar: {target}")
    payload = target.read_bytes()
    if sidecar.read_text() != sidecar_text(target, payload):
        raise RuntimeError(f"sidecar drift: {target}")
    return payload


def reject_absolute(value: object, label: str = "oracle") -> None:
    if isinstance(value, str):
        if value.startswith(("/", "\\\\")) or re.match(r"^[A-Za-z]:[\\/]", value) or re.search(r"(?:^|[\\/])(Users|private|tmp|home)[\\/]", value):
            raise RuntimeError(f"{label}: absolute path serialized")
    elif isinstance(value, list):
        for index, entry in enumerate(value):
            reject_absolute(entry, f"{label}[{index}]")
    elif isinstance(value, dict):
        for key, entry in value.items():
            reject_absolute(entry, f"{label}.{key}")


def words_bytes(words: list[str]) -> bytes:
    return b"".join(struct.pack("<I", int(word, 16)) for word in words)


def reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise RuntimeError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value: object) -> bool:
    return (isinstance(value, (int, float)) and
            not isinstance(value, bool) and math.isfinite(float(value)))


def _require(value: object, predicate: bool, label: str, expected: str) -> None:
    if not predicate:
        raise RuntimeError(f"LightLeak {label} must be {expected}")


def _string(value: object, label: str) -> None:
    _require(value, type(value) is str, label, "a string")


def _bool(value: object, label: str) -> None:
    _require(value, type(value) is bool, label, "a boolean")


def _int(value: object, label: str) -> None:
    _require(value, type(value) is int, label, "an integer (not bool)")


def _number(value: object, label: str) -> None:
    valid = type(value) in (int, float)
    if valid:
        try:
            valid = math.isfinite(float(value))
        except (OverflowError, ValueError):
            valid = False
    _require(value, valid, label, "a finite number (not bool)")


def _dict(value: object, label: str) -> dict:
    _require(value, type(value) is dict, label, "an object")
    return value  # type: ignore[return-value]


def _list(value: object, label: str) -> list:
    _require(value, type(value) is list, label, "an array")
    return value  # type: ignore[return-value]


def _strings(values: object, label: str) -> None:
    for index, value in enumerate(_list(values, label)):
        _string(value, f"{label}[{index}]")


def _ints(values: object, label: str) -> None:
    for index, value in enumerate(_list(values, label)):
        _int(value, f"{label}[{index}]")


def _validate_scalar_types(oracle: dict) -> None:
    """Reject JSON scalar type substitutions before Python equality checks.

    In particular, Python considers ``True == 1`` and ``False == 0``.  This
    walk is deliberately schema-specific so every fixed scalar is checked
    with its intended JSON type before the frozen-value comparisons below.
    """
    for key in ("schema", "program_key", "corpus_revision", "upstream_revision",
                "oracle_authority"):
        _string(oracle.get(key), key)

    fixture = _dict(oracle.get("input_fixture"), "input_fixture")
    for key in ("schema", "source_function", "source_function_sha256",
                "coordinate_order"):
        _string(fixture.get(key), f"input_fixture.{key}")
    _strings(fixture.get("component_order"), "input_fixture.component_order")
    _strings(fixture.get("formulas"), "input_fixture.formulas")

    provenance = _dict(oracle.get("provenance"), "provenance")
    for key in ("authority_commit", "node_version"):
        _string(provenance.get(key), f"provenance.{key}")
    _bool(provenance.get("authority_checkout_clean"),
          "provenance.authority_checkout_clean")
    _int(provenance.get("point_count"), "provenance.point_count")
    factory = _dict(provenance.get("factory"), "provenance.factory")
    _string(factory.get("name"), "provenance.factory.name")
    _int(factory.get("bytes"), "provenance.factory.bytes")
    _string(factory.get("sha256"), "provenance.factory.sha256")
    source = _dict(provenance.get("source"), "provenance.source")
    _string(source.get("relative_path_from_noisemaker_for_cpp"),
            "provenance.source.relative_path_from_noisemaker_for_cpp")
    _int(source.get("bytes"), "provenance.source.bytes")
    _string(source.get("sha256"), "provenance.source.sha256")
    closure = _list(provenance.get("import_closure"), "provenance.import_closure")
    for index, entry in enumerate(closure):
        entry = _dict(entry, f"provenance.import_closure[{index}]")
        _string(entry.get("relative_path"),
                f"provenance.import_closure[{index}].relative_path")
        _string(entry.get("sha256"),
                f"provenance.import_closure[{index}].sha256")
    binding = _dict(provenance.get("binding_abi"), "provenance.binding_abi")
    for key, value in binding.items():
        _string(key, "provenance.binding_abi key")
        _string(value, f"provenance.binding_abi.{key}")
    _bool(provenance.get("canonical_public_identity"),
          "provenance.canonical_public_identity")
    _bool(provenance.get("adapter_override_absent"),
          "provenance.adapter_override_absent")

    comparer = _dict(oracle.get("comparer_self_tests"), "comparer_self_tests")
    for key, value in comparer.items():
        _string(key, "comparer_self_tests key")
        _bool(value, f"comparer_self_tests.{key}")

    contract = _dict(oracle.get("mutation_contract"), "mutation_contract")
    _strings(contract.get("behavioral_names"),
             "mutation_contract.behavioral_names")
    _strings(contract.get("structural_names"),
             "mutation_contract.structural_names")
    witnesses = _dict(contract.get("witnesses"), "mutation_contract.witnesses")
    for name, values in witnesses.items():
        _string(name, "mutation_contract.witnesses key")
        _strings(values, f"mutation_contract.witnesses.{name}")

    cases = _list(oracle.get("render_cases"), "render_cases")
    for index, case_value in enumerate(cases):
        case = _dict(case_value, f"render_cases[{index}]")
        _string(case.get("name"), f"render_cases[{index}].name")
        _int(case.get("width"), f"render_cases[{index}].width")
        _int(case.get("height"), f"render_cases[{index}].height")
        controls = _dict(case.get("controls"), f"render_cases[{index}].controls")
        for key in ("alpha", "speed", "time"):
            _number(controls.get(key), f"render_cases[{index}].controls.{key}")
        _int(controls.get("seed"), f"render_cases[{index}].controls.seed")
        for key, size in (("color", 3), ("resolution", 2),
                          ("tile_offset", 2), ("full_resolution", 2)):
            values = _list(controls.get(key),
                           f"render_cases[{index}].controls.{key}")
            _require(values, len(values) == size,
                     f"render_cases[{index}].controls.{key}",
                     f"an array of {size} numbers")
            for component, value in enumerate(values):
                _number(value, f"render_cases[{index}].controls.{key}[{component}]")
        case_binding = _dict(case.get("binding_abi"),
                             f"render_cases[{index}].binding_abi")
        for key, value in case_binding.items():
            _string(key, f"render_cases[{index}].binding_abi key")
            _string(value, f"render_cases[{index}].binding_abi.{key}")
        texture = _dict(case.get("input_texture"),
                        f"render_cases[{index}].input_texture")
        _int(texture.get("phase"), f"render_cases[{index}].input_texture.phase")
        _strings(texture.get("f32_words_le"),
                 f"render_cases[{index}].input_texture.f32_words_le")
        _string(texture.get("f32_sha256"),
                f"render_cases[{index}].input_texture.f32_sha256")
        _ints(texture.get("rgba8_bytes"),
              f"render_cases[{index}].input_texture.rgba8_bytes")
        _string(texture.get("rgba8_sha256"),
                f"render_cases[{index}].input_texture.rgba8_sha256")
        for key in ("output_f32_sha256", "output_rgba8_sha256"):
            _string(case.get(key), f"render_cases[{index}].{key}")
        _strings(case.get("output_f32_words_le"),
                 f"render_cases[{index}].output_f32_words_le")
        _ints(case.get("output_rgba8_bytes"),
              f"render_cases[{index}].output_rgba8_bytes")
        for identity_name in ("repeat_identity", "public_identity"):
            identity = _dict(case.get(identity_name),
                             f"render_cases[{index}].{identity_name}")
            for key in ("exact", "dimensions_match", "lane_count_match",
                        "exact_f32_bits", "rgba8_count_match",
                        "exact_rgba8_bytes"):
                _bool(identity.get(key),
                      f"render_cases[{index}].{identity_name}.{key}")
            for key in ("reference_lane_count", "candidate_lane_count",
                        "reference_rgba8_byte_count", "candidate_rgba8_byte_count",
                        "mismatched_lanes", "mismatched_bytes"):
                _int(identity.get(key),
                     f"render_cases[{index}].{identity_name}.{key}")
            for key in ("first_mismatch", "first_rgba8_mismatch"):
                value = identity.get(key)
                if value is not None:
                    _dict(value, f"render_cases[{index}].{identity_name}.{key}")
        _bool(case.get("input_immutable_exact_bits"),
              f"render_cases[{index}].input_immutable_exact_bits")

    ledger = _list(oracle.get("behavioral_mutation_ledger"),
                   "behavioral_mutation_ledger")
    for index, item_value in enumerate(ledger):
        item = _dict(item_value, f"behavioral_mutation_ledger[{index}]")
        for key in ("name", "source_anchor_text", "replacement_text",
                    "source_anchor_sha256", "replacement_sha256",
                    "mutated_factory_sha256"):
            _string(item.get(key), f"behavioral_mutation_ledger[{index}].{key}")
        _int(item.get("anchor_count"),
             f"behavioral_mutation_ledger[{index}].anchor_count")
        _strings(item.get("required_witnesses"),
                 f"behavioral_mutation_ledger[{index}].required_witnesses")
        _strings(item.get("divergent_cases"),
                 f"behavioral_mutation_ledger[{index}].divergent_cases")
        results = _list(item.get("required_witness_results"),
                        f"behavioral_mutation_ledger[{index}].required_witness_results")
        for result_index, result_value in enumerate(results):
            result = _dict(result_value,
                           f"behavioral_mutation_ledger[{index}].required_witness_results[{result_index}]")
            _string(result.get("case"), "mutation result case")
            _int(result.get("mismatched_lanes"), "mutation result mismatched_lanes")
            first = _dict(result.get("first_mismatch"), "mutation result first_mismatch")
            _int(first.get("lane_index"), "mutation first_mismatch.lane_index")
            xy = _list(first.get("top_down_xy"), "mutation first_mismatch.top_down_xy")
            _require(xy, len(xy) == 2, "mutation first_mismatch.top_down_xy", "two integers")
            _ints(xy, "mutation first_mismatch.top_down_xy")
            for key in ("channel", "reference_bits_le", "candidate_bits_le"):
                _string(first.get(key), f"mutation first_mismatch.{key}")

    structural = _list(oracle.get("structural_only_mutation_ledger"),
                       "structural_only_mutation_ledger")
    for index, item_value in enumerate(structural):
        item = _dict(item_value, f"structural_only_mutation_ledger[{index}]")
        _string(item.get("name"), f"structural_only_mutation_ledger[{index}].name")
        _string(item.get("pixel_expectation"),
                f"structural_only_mutation_ledger[{index}].pixel_expectation")


def expected_identity(case: dict) -> dict:
    lanes = case["width"] * case["height"] * 4
    return {"exact": True, "dimensions_match": True, "reference_lane_count": lanes, "candidate_lane_count": lanes, "lane_count_match": True, "exact_f32_bits": True, "reference_rgba8_byte_count": lanes, "candidate_rgba8_byte_count": lanes, "rgba8_count_match": True, "exact_rgba8_bytes": True, "mismatched_lanes": 0, "mismatched_bytes": 0, "first_mismatch": None, "first_rgba8_mismatch": None}


def load(oracle_path: pathlib.Path = ORACLE, verify_assets: bool = True) -> tuple[dict, str]:
    if verify_assets:
        for asset in (pathlib.Path(__file__), PACKAGE / "lightleak192_oracle_generator.mjs", PACKAGE / "lightleak192-oracle-report.md"):
            verify_sidecar(asset)
    payload = verify_sidecar(oracle_path)
    oracle = json.loads(payload, object_pairs_hook=reject_duplicate_pairs)
    _validate_scalar_types(oracle)
    top = {"schema", "program_key", "corpus_revision", "upstream_revision", "oracle_authority", "input_fixture", "provenance", "comparer_self_tests", "render_cases", "mutation_contract", "behavioral_mutation_ledger", "structural_only_mutation_ledger"}
    if set(oracle) != top or oracle["schema"] != SCHEMA or oracle["program_key"] != PROGRAM_KEY or oracle["corpus_revision"] != "a024dc3a960cc44af454abc7aebce50456c194e6" or oracle["upstream_revision"] != "117a236679d1db3ab8f0e278230ece277b57564c" or oracle["oracle_authority"] != "canonicalFactory77 from immutable noisemaker-for-cpu snapshot; no C++ output participates":
        raise RuntimeError("LightLeak frozen document schema/program mismatch")
    provenance = oracle["provenance"]
    provenance_keys = {"authority_commit", "authority_checkout_clean", "node_version", "factory", "source", "import_closure", "binding_abi", "canonical_public_identity", "adapter_override_absent", "point_count"}
    if set(provenance) != provenance_keys or (provenance["authority_commit"], provenance["authority_checkout_clean"], provenance["node_version"], provenance["point_count"]) != ("4834b0144ee0524588144a482cca0067b15f68ec", True, "v24.7.0", 6):
        raise RuntimeError("LightLeak authority provenance mismatch")
    if provenance["factory"] != {"name": "canonicalFactory77", "bytes": 7818, "sha256": "9cf716594f8d25347737104d2ec0658276ac5a11405eb878706dc8f429c9055f"} or provenance["source"] != {"relative_path_from_noisemaker_for_cpp": "tools/glslcpp/corpus/a024dc3a960cc44af454abc7aebce50456c194e6/sources/filter/lightLeak/lightLeak.glsl", "bytes": 5047, "sha256": "61bcb2989992c109dcf73ac5b34bb4dfa7f6603b54c111a84e69b6f73a9501bb"}:
        raise RuntimeError("LightLeak factory/source provenance mismatch")
    if provenance["binding_abi"] != EXPECTED_ABI or provenance["canonical_public_identity"] is not True or provenance["adapter_override_absent"] is not True:
        raise RuntimeError("LightLeak binding/identity provenance mismatch")
    if oracle["input_fixture"] != EXPECTED_INPUT_FIXTURE:
        raise RuntimeError("LightLeak input fixture contract mismatch")
    closure = provenance["import_closure"]
    actual_closure = [(entry.get("relative_path"), entry.get("sha256")) for entry in closure] if isinstance(closure, list) else []
    if actual_closure != EXPECTED_CLOSURE or any(set(entry) != {"relative_path", "sha256"} for entry in closure):
        raise RuntimeError("LightLeak complete import closure mismatch")
    comparer = oracle["comparer_self_tests"]
    expected_comparer = {"good_equal", "dimensions_mismatch", "short_lane_count", "long_lane_count", "rgba8_mismatch", "rgba8_byte_count", "signed_zero_rejected", "nan_payload_rejected"}
    if set(comparer) != expected_comparer or any(value is not True for value in comparer.values()):
        raise RuntimeError("LightLeak comparer self-tests incomplete")
    cases = oracle["render_cases"]
    if not isinstance(cases, list) or len(cases) != 11:
        raise RuntimeError("LightLeak fixture count mismatch")
    case_keys = {"name", "width", "height", "controls", "binding_abi", "input_texture", "output_f32_words_le", "output_rgba8_bytes", "output_f32_sha256", "output_rgba8_sha256", "repeat_identity", "public_identity", "input_immutable_exact_bits"}
    control_keys = {"alpha", "color", "speed", "seed", "time", "resolution", "tile_offset", "full_resolution"}
    for index, case in enumerate(cases):
        if (not isinstance(case, dict) or
                not is_int(case.get("width")) or
                not is_int(case.get("height")) or
                case["width"] <= 0 or case["height"] <= 0 or
                not isinstance(case.get("controls"), dict) or
                not isinstance(case.get("input_texture"), dict)):
            raise RuntimeError(f"LightLeak case {index} scalar/container types mismatch")
        controls = case["controls"]
        if set(controls) != control_keys:
            raise RuntimeError(f"LightLeak case {index} controls schema mismatch")
        if (not is_number(controls["alpha"]) or
                not is_number(controls["speed"]) or
                not is_int(controls["seed"]) or
                not is_number(controls["time"])):
            raise RuntimeError(f"LightLeak case {index} scalar control types mismatch")
        for control_name, expected_length in (("color", 3), ("resolution", 2),
                                              ("tile_offset", 2), ("full_resolution", 2)):
            values = controls[control_name]
            if (not isinstance(values, list) or len(values) != expected_length or
                    not all(is_number(value) for value in values)):
                raise RuntimeError(f"LightLeak case {index} {control_name} types mismatch")
        expected_name, expected_width, expected_height, expected_controls = EXPECTED_CASES[index]
        if (case.get("name"), case.get("width"), case.get("height"), case.get("controls")) != (expected_name, expected_width, expected_height, expected_controls):
            raise RuntimeError(f"LightLeak case {index} frozen name/dimensions/controls mismatch")
        if set(case) != case_keys or case["binding_abi"] != EXPECTED_ABI:
            raise RuntimeError(f"LightLeak case {index} contract mismatch")
        if controls["resolution"] != [case["width"], case["height"]]:
            raise RuntimeError(f"LightLeak case {index} binding controls mismatch")
        expected_input_name, expected_phase, expected_input_f32_sha256, expected_input_rgba8_sha256 = EXPECTED_INPUT_CASES[index]
        input_texture = case["input_texture"]
        if not is_int(input_texture.get("phase")):
            raise RuntimeError(f"LightLeak case {index} input phase type mismatch")
        if (case["name"], input_texture.get("phase")) != (expected_input_name, expected_phase) or set(input_texture) != {"phase", "f32_words_le", "f32_sha256", "rgba8_bytes", "rgba8_sha256"}:
            raise RuntimeError(f"LightLeak case {index} input fixture mismatch")
        input_words = input_texture["f32_words_le"]
        input_rgba = input_texture["rgba8_bytes"]
        if (not isinstance(input_words, list) or
                not all(isinstance(word, str) and WORD.fullmatch(word)
                        for word in input_words) or
                not isinstance(input_rgba, list) or
                not all(is_int(value) and 0 <= value <= 255
                        for value in input_rgba) or
                len(input_words) != case["width"] * case["height"] * 4 or
                len(input_rgba) != len(input_words) or
                input_texture["f32_sha256"] != expected_input_f32_sha256 or
                input_texture["rgba8_sha256"] != expected_input_rgba8_sha256 or
                input_texture["f32_sha256"] != sha256(words_bytes(input_words)) or
                input_texture["rgba8_sha256"] != sha256(bytes(input_rgba))):
            raise RuntimeError(f"LightLeak case {index} input payload mismatch")
        words = case["output_f32_words_le"]
        rgba = case["output_rgba8_bytes"]
        output_alpha_words = words[3::4]
        output_alpha_bytes = rgba[3::4]
        if not isinstance(words, list) or not all(isinstance(word, str) and WORD.fullmatch(word) for word in words) or not isinstance(rgba, list) or not all(is_int(value) and 0 <= value <= 255 for value in rgba) or len(words) != case["width"] * case["height"] * 4 or len(rgba) != len(words):
            raise RuntimeError(f"LightLeak case {index} payload mismatch")
        expected_f32_b64, expected_rgba_b64, expected_f32_sha256, expected_rgba_sha256 = EXPECTED_OUTPUT_PAYLOADS[case["name"]]
        if (not isinstance(case["output_f32_sha256"], str) or
                not isinstance(case["output_rgba8_sha256"], str) or
                not HEX256.fullmatch(case["output_f32_sha256"]) or
                not HEX256.fullmatch(case["output_rgba8_sha256"]) or
                case["output_f32_sha256"] != expected_f32_sha256 or
                case["output_rgba8_sha256"] != expected_rgba_sha256 or
                case["output_f32_sha256"] != sha256(words_bytes(words)) or
                case["output_rgba8_sha256"] != sha256(bytes(rgba)) or
                words_bytes(words) != base64.b64decode(expected_f32_b64, validate=True) or
                bytes(rgba) != base64.b64decode(expected_rgba_b64, validate=True)):
            raise RuntimeError(f"LightLeak case {index} payload hash mismatch")
        identity = expected_identity(case)
        if case["repeat_identity"] != identity or case["public_identity"] != identity or case["input_immutable_exact_bits"] is not True:
            raise RuntimeError(f"LightLeak case {index} repeat/public/immutability contract mismatch")
    names = [name for name, _, _ in EXPECTED_MUTATIONS]
    witnesses = {name: required for name, _, required in EXPECTED_MUTATIONS}
    contract = oracle["mutation_contract"]
    if contract != {"behavioral_names": names, "witnesses": witnesses, "structural_names": EXPECTED_STRUCTURAL}:
        raise RuntimeError("LightLeak mutation contract mismatch")
    ledger = oracle["behavioral_mutation_ledger"]
    if len(ledger) != len(EXPECTED_MUTATIONS):
        raise RuntimeError("LightLeak behavioral mutation ledger count mismatch")
    for item, (name, anchors, required) in zip(ledger, EXPECTED_MUTATIONS):
        digest, divergent, expected_results = EXPECTED_MUTATION_DETAILS[name]
        source_text, replacement_text, source_hash, replacement_hash = EXPECTED_MUTATION_ANCHORS[name]
        if set(item) != {"name", "anchor_count", "source_anchor_text", "replacement_text", "source_anchor_sha256", "replacement_sha256", "required_witnesses", "required_witness_results", "divergent_cases", "mutated_factory_sha256"} or item["name"] != name or item["anchor_count"] != anchors or item["source_anchor_text"] != source_text or item["replacement_text"] != replacement_text or item["source_anchor_sha256"] != source_hash or item["replacement_sha256"] != replacement_hash or item["required_witnesses"] != required or item["mutated_factory_sha256"] != digest or item["divergent_cases"] != divergent or item["required_witness_results"] != expected_results:
            raise RuntimeError(f"LightLeak mutation {name} contract mismatch")
    structural = oracle["structural_only_mutation_ledger"]
    if [item.get("name") for item in structural] != EXPECTED_STRUCTURAL or any(set(item) != {"name", "pixel_expectation"} or item["pixel_expectation"] != EXPECTED_STRUCTURAL_DETAILS[item["name"]] for item in structural):
        raise RuntimeError("LightLeak structural mutation ledger mismatch")
    reject_absolute(oracle)
    return oracle, sha256(payload)


def self_test_forged_documents() -> None:
    baseline, _ = load()

    def recompute_output_f32(value: dict) -> None:
        case = value["render_cases"][0]
        case["output_f32_words_le"][0] = "0x00000000"
        case["output_f32_sha256"] = sha256(words_bytes(case["output_f32_words_le"]))

    def recompute_output_rgba(value: dict) -> None:
        case = value["render_cases"][0]
        case["output_rgba8_bytes"][0] ^= 1
        case["output_rgba8_sha256"] = sha256(bytes(case["output_rgba8_bytes"]))

    mutations = {
        "input-contract": lambda value: value["input_fixture"].update(source_function_sha256="0" * 64),
        "input-phase": lambda value: value["render_cases"][0]["input_texture"].update(phase=99),
        "input-word": lambda value: value["render_cases"][0]["input_texture"]["f32_words_le"].__setitem__(0, "0x00000000"),
        "input-word-hash": lambda value: value["render_cases"][0]["input_texture"].update(f32_sha256="0" * 64),
        "input-rgba": lambda value: value["render_cases"][0]["input_texture"]["rgba8_bytes"].__setitem__(0, 0),
        "input-rgba-hash": lambda value: value["render_cases"][0]["input_texture"].update(rgba8_sha256="0" * 64),
        "case-name": lambda value: value["render_cases"][0].update(name="forged-case"),
        "case-dimensions": lambda value: value["render_cases"][0].update(width=2),
        "case-controls": lambda value: value["render_cases"][0]["controls"].update(alpha=0.25),
        "output-word-hash": lambda value: value["render_cases"][0]["output_f32_words_le"].__setitem__(0, "0x00000000"),
        "output-payload-recomputed-digest": recompute_output_f32,
        "output-rgba-recomputed-digest": recompute_output_rgba,
        "reordered-cases": lambda value: value["render_cases"].reverse(),
        "unknown-field": lambda value: value.update(unknown_field=True),
        "source-function": lambda value: value["input_fixture"].update(source_function="forgedInputSurface"),
        "dimension-bool": lambda value: value["render_cases"][0].update(width=True),
        "dimension-float": lambda value: value["render_cases"][0].update(width=1.0),
        "phase-bool": lambda value: value["render_cases"][0]["input_texture"].update(phase=False),
        "phase-float": lambda value: value["render_cases"][0]["input_texture"].update(phase=1.0),
        "seed-bool": lambda value: value["render_cases"][0]["controls"].update(seed=True),
        "seed-float": lambda value: value["render_cases"][0]["controls"].update(seed=1.0),
        "alpha-bool": lambda value: value["render_cases"][0]["controls"].update(alpha=False),
        "alpha-string": lambda value: value["render_cases"][0]["controls"].update(alpha="1"),
        "speed-bool": lambda value: value["render_cases"][0]["controls"].update(speed=True),
        "time-bool": lambda value: value["render_cases"][0]["controls"].update(time=False),
        "color-bool": lambda value: value["render_cases"][0]["controls"]["color"].__setitem__(0, True),
        "color-string": lambda value: value["render_cases"][0]["controls"]["color"].__setitem__(0, "1"),
        "resolution-bool": lambda value: value["render_cases"][0]["controls"]["resolution"].__setitem__(0, True),
        "resolution-string": lambda value: value["render_cases"][0]["controls"]["resolution"].__setitem__(0, "1"),
        "tile-offset-bool": lambda value: value["render_cases"][0]["controls"]["tile_offset"].__setitem__(0, True),
        "tile-offset-null": lambda value: value["render_cases"][0]["controls"].update(tile_offset=None),
        "full-resolution-bool": lambda value: value["render_cases"][0]["controls"]["full_resolution"].__setitem__(0, False),
        "full-resolution-string": lambda value: value["render_cases"][0]["controls"]["full_resolution"].__setitem__(0, "1"),
        "input-rgba-bool": lambda value: value["render_cases"][0]["input_texture"]["rgba8_bytes"].__setitem__(0, True),
        "output-rgba-bool": lambda value: value["render_cases"][0]["output_rgba8_bytes"].__setitem__(0, True),
        "mutation-anchor-text": lambda value: value["behavioral_mutation_ledger"][0].update(source_anchor_text="forged-anchor"),
        "mutation-anchor-hash": lambda value: value["behavioral_mutation_ledger"][0].update(source_anchor_sha256="0" * 64),
        "mutation-digest": lambda value: value["behavioral_mutation_ledger"][0].update(mutated_factory_sha256="0" * 64),
        "mutation-divergence": lambda value: value["behavioral_mutation_ledger"][0]["required_witness_results"][0].update(mismatched_lanes=0),
        "mutation-witness": lambda value: value["behavioral_mutation_ledger"][0].update(required_witnesses=["missing-case"]),
        "structural-expectation": lambda value: value["structural_only_mutation_ledger"][0].update(pixel_expectation="pixels accepted"),
        "import-closure": lambda value: value["provenance"]["import_closure"].pop(),
        "provenance": lambda value: value["provenance"].update(authority_commit="0" * 40),
        "authority-clean-bool": lambda value: value["provenance"].update(authority_checkout_clean=1),
        "repeat-exact-number": lambda value: value["render_cases"][0]["repeat_identity"].update(exact=1),
        "repeat-count-bool": lambda value: value["render_cases"][0]["repeat_identity"].update(reference_lane_count=False),
        "repeat-count-float": lambda value: value["render_cases"][0]["repeat_identity"].update(candidate_rgba8_byte_count=4.0),
        "public-exact-string": lambda value: value["render_cases"][0]["public_identity"].update(exact="true"),
        "input-immutable-number": lambda value: value["render_cases"][0].update(input_immutable_exact_bits=1),
        "factory-bytes-bool": lambda value: value["provenance"]["factory"].update(bytes=True),
        "factory-bytes-float": lambda value: value["provenance"]["factory"].update(bytes=7818.0),
        "source-bytes-string": lambda value: value["provenance"]["source"].update(bytes="5047"),
        "point-count-bool": lambda value: value["provenance"].update(point_count=False),
        "comparer-value-number": lambda value: value["comparer_self_tests"].update(good_equal=1),
        "binding-abi-number": lambda value: value["render_cases"][0]["binding_abi"].update(alpha=1),
        "control-nan": lambda value: value["render_cases"][0]["controls"].update(alpha=float("nan")),
        "control-huge-int": lambda value: value["render_cases"][0]["controls"].update(alpha=10 ** 1000),
        "color-nan": lambda value: value["render_cases"][0]["controls"]["color"].__setitem__(0, float("nan")),
        "output-hash-bool": lambda value: value["render_cases"][0].update(output_f32_sha256=True),
        "mutation-anchor-count-bool": lambda value: value["behavioral_mutation_ledger"][0].update(anchor_count=True),
        "mutation-anchor-count-float": lambda value: value["behavioral_mutation_ledger"][0].update(anchor_count=1.0),
        "mutation-witness-lane-bool": lambda value: value["behavioral_mutation_ledger"][0]["required_witness_results"][0].update(mismatched_lanes=True),
        "mutation-witness-xy-float": lambda value: value["behavioral_mutation_ledger"][0]["required_witness_results"][0]["first_mismatch"].update(top_down_xy=[0.0, 0]),
    }
    expected_forgery_checks = 73
    if len(mutations) != 63:
        raise RuntimeError(f"LightLeak forgery census source drift: {len(mutations)}")
    with tempfile.TemporaryDirectory(prefix="lightleak192-materializer-") as temp:
        forgery_checks = 0
        for label, mutate in mutations.items():
            forged = copy.deepcopy(baseline)
            mutate(forged)
            target = pathlib.Path(temp) / f"{label}.json"
            forged_payload = (json.dumps(forged, indent=2) + "\n").encode()
            target.write_bytes(forged_payload)
            target.with_suffix(target.suffix + ".sha256").write_text(sidecar_text(target, forged_payload))
            try:
                load(target, verify_assets=False)
            except (RuntimeError, ValueError, KeyError, TypeError):
                forgery_checks += 1
                continue
            raise RuntimeError(f"forged-document self-test accepted {label}")
        duplicate_lines = {
            "duplicate-top-schema": f'  "schema": "{SCHEMA}",\n',
            "duplicate-provenance": '    "authority_commit": "4834b0144ee0524588144a482cca0067b15f68ec",\n',
            "duplicate-fixture": '    "source_function": "inputSurface",\n',
            "duplicate-case-dimension": '      "width": 1,\n',
            "duplicate-control": '        "alpha": 0,\n',
            "duplicate-input-phase": '        "phase": 1,\n',
            "duplicate-identity": '        "exact": true,\n',
            "duplicate-mutation-count": '      "anchor_count": 1,\n',
            "duplicate-witness-case": '          "case": "color-blue",\n',
            "duplicate-structural": '      "pixel_expectation": "structurally authenticated binding retained; no pixel witness claimed"\n',
        }
        serialized = json.dumps(baseline, indent=2) + "\n"
        for label, marker in duplicate_lines.items():
            if marker not in serialized:
                raise RuntimeError(f"LightLeak duplicate probe marker missing: {label}")
            duplicate = serialized.replace(marker, marker + marker, 1).encode()
            target = pathlib.Path(temp) / f"{label}.json"
            target.write_bytes(duplicate)
            target.with_suffix(target.suffix + ".sha256").write_text(sidecar_text(target, duplicate))
            try:
                load(target, verify_assets=False)
            except (RuntimeError, ValueError, KeyError, TypeError):
                forgery_checks += 1
                continue
            raise RuntimeError(f"forged-document self-test accepted {label}")
        if forgery_checks != expected_forgery_checks:
            raise RuntimeError(
                f"LightLeak forgery census mismatch: {forgery_checks}/{expected_forgery_checks}")


def f32_word(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def cpp_float(value: float) -> str:
    rendered = repr(float(value))
    if rendered == "-0.0":
        rendered = "-0.0"
    return f"{rendered}f"


def cpp_words(values: list[float]) -> str:
    return ", ".join(f"0x{f32_word(value):08x}U" for value in values)


def cpp_values(values: list[float]) -> str:
    return ", ".join(cpp_float(value) for value in values)


def cpp_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


MUTATION_GROUPS = {
    "out-cell-color-materialization": "out-inout materialization",
    "out-cell-dist-materialization": "out-inout materialization",
    "base-bare-call-site": "bare call site",
    "warp-bare-call-site": "bare call site",
    "source-global-POINT_COUNT": "source global",
    "loop-bound-POINT_COUNT": "loop bound",
    "alpha-control-axis": "control axis",
    "speed-control-axis": "control axis",
    "seed-control-axis": "control axis",
    "color-control-axis": "control axis",
    "time-control-axis": "control axis",
}
MUTATION_MECHANISMS = {
    "out-cell-color-materialization": "replace canonical out-cell color owner",
    "out-cell-dist-materialization": "replace canonical out-cell distance owner",
    "base-bare-call-site": "alter canonical base-cell call arguments",
    "warp-bare-call-site": "alter canonical warp-cell call arguments",
    "source-global-POINT_COUNT": "alter canonical source global point count",
    "loop-bound-POINT_COUNT": "alter canonical loop point-count bound",
    "alpha-control-axis": "remove canonical alpha control from blend",
    "speed-control-axis": "remove canonical speed control from time",
    "seed-control-axis": "remove canonical seed control from hash",
    "color-control-axis": "alter canonical color control order",
    "time-control-axis": "reverse canonical time control",
}


def render_include(oracle: dict, oracle_hash: str) -> bytes:
    cases = oracle["render_cases"]
    input_fixture = oracle["input_fixture"]
    abi = [("inputTex", "Sampler2D"), ("resolution", "Vec2"), ("tileOffset", "Vec2"), ("fullResolution", "Vec2"), ("alpha", "Number"), ("color", "Vec3"), ("speed", "Number"), ("seed", "Int32"), ("time", "Number")]
    runtime_types = [("inputTex", "sampler2D"), ("resolution", "Vec2"), ("tileOffset", "Vec2"), ("fullResolution", "Vec2"), ("alpha", "number"), ("color", "Vec3"), ("speed", "number"), ("seed", "int32"), ("time", "number")]
    source_types = [("inputTex", "sampler2D"), ("resolution", "vec2"), ("tileOffset", "vec2"), ("fullResolution", "vec2"), ("alpha", "float"), ("color", "vec3"), ("speed", "float"), ("seed", "int"), ("time", "float")]
    lines = [
        "// Generated from the checked LightLeak192 canonical JavaScript oracle.",
        "// Do not edit; C++ output never participates in expected arrays.",
        "#include <array>",
        "#include <cstddef>",
        "#include <cstdint>",
        "#include <span>",
        "#include <string_view>",
        "#pragma once", "", "namespace lightleak192_oracle {", "",
        f'inline constexpr std::string_view kOracleSha256 = "{oracle_hash}";',
        f'inline constexpr std::string_view kProgramKey = "{PROGRAM_KEY}";',
        f"inline constexpr std::size_t kCaseCount = {len(cases)}U;",
        f"inline constexpr std::size_t kBindingCount = {len(abi)}U;", "",
        f"inline constexpr std::string_view kInputFixtureSchema = \"{input_fixture['schema']}\";",
        f"inline constexpr std::string_view kInputFixtureSourceFunction = \"{input_fixture['source_function']}\";",
        f"inline constexpr std::string_view kInputFixtureSourceFunctionSha256 = \"{input_fixture['source_function_sha256']}\";",
        f"inline constexpr std::string_view kInputFixtureCoordinateOrder = \"{input_fixture['coordinate_order']}\";",
        f"inline constexpr std::array<std::string_view, {len(input_fixture['formulas'])}> kInputFixtureFormulas{{{{",
    ]
    lines.extend(f'  "{formula}",' for formula in input_fixture["formulas"])
    lines.extend([
        "}};", "",
        "enum class BindingAbi { Sampler2D, Vec2, Vec3, Number, Int32 };",
        "struct BindingView { std::string_view name; BindingAbi abi; std::string_view runtime_abi; std::string_view source_abi; }; using BindingAbiView = BindingView;",
        f"inline constexpr std::array<BindingView, {len(abi)}> kBindingAbi{{{{",
    ])
    lines.extend(
        f'  BindingView{{{cpp_string(name)}, BindingAbi::{kind}, {cpp_string(runtime)}, {cpp_string(source)}}},'
        for (name, kind), (_, runtime), (_, source) in zip(abi, runtime_types, source_types))
    lines.extend([
        "}};", "",
        "struct SourceBindingView { std::string_view name; std::string_view source_abi; }; using SourceBindingAbiView = SourceBindingView;",
        f"inline constexpr std::array<SourceBindingView, {len(source_types)}> kSourceBindingAbi{{{{",
    ])
    lines.extend(f'  SourceBindingView{{{cpp_string(name)}, {cpp_string(source)}}},' for name, source in source_types)
    lines.extend([
        "}};", "", "struct ScalarControl { float value; std::uint32_t word; };", "struct Vec2Control { std::array<float, 2> values; std::array<std::uint32_t, 2> words; };", "struct Vec3Control { std::array<float, 3> values; std::array<std::uint32_t, 3> words; };", ""])
    for index, case in enumerate(cases):
        controls = case["controls"]
        input_texture = case["input_texture"]
        input_words = input_texture["f32_words_le"]
        input_rgba = input_texture["rgba8_bytes"]
        words = case["output_f32_words_le"]
        rgba = case["output_rgba8_bytes"]
        output_alpha_words = words[3::4]
        output_alpha_bytes = rgba[3::4]
        lines.extend([f"inline constexpr std::array<std::uint32_t, {len(input_words)}> kCase{index}InputFloatWords{{{{"])
        lines.extend("    " + ", ".join(input_words[i:i + 8]) + "," for i in range(0, len(input_words), 8))
        lines.extend(["}};", f"inline constexpr std::array<std::uint8_t, {len(input_rgba)}> kCase{index}InputRgbaBytes{{{{"])
        lines.extend("    " + ", ".join(f"{value}U" for value in input_rgba[i:i + 16]) + "," for i in range(0, len(input_rgba), 16))
        lines.extend(["}};", ""])
        lines.extend([f"inline constexpr std::array<std::uint32_t, {len(words)}> kCase{index}FloatWords{{{{"])
        lines.extend("    " + ", ".join(words[i:i + 8]) + "," for i in range(0, len(words), 8))
        lines.extend(["}};", f"inline constexpr std::array<std::uint8_t, {len(rgba)}> kCase{index}RgbaBytes{{{{"])
        lines.extend("    " + ", ".join(f"{value}U" for value in rgba[i:i + 16]) + "," for i in range(0, len(rgba), 16))
        lines.extend(["}};", f"inline constexpr std::array<std::uint32_t, {len(output_alpha_words)}> kCase{index}OutputAlphaFloatWords{{{{"])
        lines.extend("    " + ", ".join(output_alpha_words[i:i + 8]) + "," for i in range(0, len(output_alpha_words), 8))
        lines.extend(["}};", f"inline constexpr std::array<std::uint8_t, {len(output_alpha_bytes)}> kCase{index}OutputAlphaRgbaBytes{{{{"])
        lines.extend("    " + ", ".join(f"{value}U" for value in output_alpha_bytes[i:i + 16]) + "," for i in range(0, len(output_alpha_bytes), 16))
        lines.extend(["}};", ""])
    lines.extend([
        "struct CaseView {",
        "  std::string_view name; std::size_t width; std::size_t height;",
        "  std::size_t input_phase;",
        "  std::string_view input_f32_sha256; std::string_view input_rgba8_sha256;",
        "  std::span<const std::uint32_t> input_float_words; std::span<const std::uint8_t> input_rgba8_bytes;",
        "  std::string_view f32_sha256; std::string_view rgba8_sha256;",
        "  std::span<const std::uint32_t> float_words; std::span<const std::uint8_t> rgba8_bytes;",
        "  ScalarControl alpha; Vec3Control color; ScalarControl speed; std::int32_t seed; ScalarControl time;",
        "  Vec2Control resolution; Vec2Control tileOffset; Vec2Control fullResolution;",
        "  std::span<const std::uint32_t> output_alpha_f32_words; std::span<const std::uint8_t> output_alpha_rgba8_bytes;",
        "};", "",
        f"inline constexpr std::array<CaseView, {len(cases)}> kCases{{{{",
    ])
    for index, case in enumerate(cases):
        controls = case["controls"]
        input_texture = case["input_texture"]
        lines.append(
            f'  CaseView{{{cpp_string(case["name"])}, {case["width"]}U, {case["height"]}U, '
            f'{input_texture["phase"]}U, {cpp_string(input_texture["f32_sha256"])}, {cpp_string(input_texture["rgba8_sha256"])}, '
            f"kCase{index}InputFloatWords, kCase{index}InputRgbaBytes, "
            f'{cpp_string(case["output_f32_sha256"])}, {cpp_string(case["output_rgba8_sha256"])}, '
            f"kCase{index}FloatWords, kCase{index}RgbaBytes, "
            f"ScalarControl{{{cpp_float(controls['alpha'])}, 0x{f32_word(controls['alpha']):08x}U}}, "
            f"Vec3Control{{{{{cpp_values(controls['color'])}}}, {{{cpp_words(controls['color'])}}}}}, "
            f"ScalarControl{{{cpp_float(controls['speed'])}, 0x{f32_word(controls['speed']):08x}U}}, "
            f"{controls['seed']}, ScalarControl{{{cpp_float(controls['time'])}, 0x{f32_word(controls['time']):08x}U}}, "
            f"Vec2Control{{{{{cpp_values(controls['resolution'])}}}, {{{cpp_words(controls['resolution'])}}}}}, "
            f"Vec2Control{{{{{cpp_values(controls['tile_offset'])}}}, {{{cpp_words(controls['tile_offset'])}}}}}, "
            f"Vec2Control{{{{{cpp_values(controls['full_resolution'])}}}, {{{cpp_words(controls['full_resolution'])}}}}}, "
            f"kCase{index}OutputAlphaFloatWords, kCase{index}OutputAlphaRgbaBytes}},")
    lines.extend(["}};", ""])
    lines.extend([
        "struct MutationDivergentRowView { std::string_view case_name; bool required_witness; };",
        "struct MutationResultView { std::string_view case_name; std::size_t mismatched_lanes; std::size_t lane_index; std::array<std::size_t, 2> top_down_xy; std::string_view channel; std::uint32_t reference_bits_le; std::uint32_t candidate_bits_le; };",
    ])
    for index, item in enumerate(oracle["behavioral_mutation_ledger"]):
        required = item["required_witnesses"]
        divergent = item["divergent_cases"]
        results = item["required_witness_results"]
        lines.extend([
            f"inline constexpr std::array<std::string_view, {len(required)}> kMutation{index}RequiredWitnesses{{{{",
        ])
        lines.extend(f"  {cpp_string(case_name)}," for case_name in required)
        lines.extend([
            "}};",
            f"inline constexpr std::array<MutationDivergentRowView, {len(divergent)}> kMutation{index}DivergentRows{{{{",
        ])
        lines.extend(
            f"  MutationDivergentRowView{{{cpp_string(case_name)}, {str(case_name in required).lower()}}},"
            for case_name in divergent)
        lines.extend([
            "}};",
            f"inline constexpr std::array<MutationResultView, {len(results)}> kMutation{index}Results{{{{",
        ])
        for result in results:
            first = result["first_mismatch"]
            lines.append(
                f"  MutationResultView{{{cpp_string(result['case'])}, {result['mismatched_lanes']}U, "
                f"{first['lane_index']}U, {{{first['top_down_xy'][0]}U, {first['top_down_xy'][1]}U}}, "
                f"{cpp_string(first['channel'])}, {first['reference_bits_le']}U, {first['candidate_bits_le']}U}},")
        lines.extend(["}};", ""])
    lines.extend([
        "struct MutationView { std::string_view name; std::string_view group; std::string_view mechanism; std::string_view source_anchor; std::string_view replacement; std::string_view source_anchor_sha256; std::string_view replacement_sha256; std::string_view mutated_factory_sha256; std::size_t anchor_count; std::span<const std::string_view> required_witnesses; std::span<const MutationDivergentRowView> divergent_rows; std::span<const MutationResultView> required_results; };",
        f"inline constexpr std::array<MutationView, {len(oracle['behavioral_mutation_ledger'])}> kMutations{{{{",
    ])
    for index, item in enumerate(oracle["behavioral_mutation_ledger"]):
        name = item["name"]
        lines.append(
            f"  MutationView{{{cpp_string(name)}, {cpp_string(MUTATION_GROUPS[name])}, "
            f"{cpp_string(MUTATION_MECHANISMS[name])}, {cpp_string(item['source_anchor_text'])}, "
            f"{cpp_string(item['replacement_text'])}, {cpp_string(item['source_anchor_sha256'])}, "
            f"{cpp_string(item['replacement_sha256'])}, {cpp_string(item['mutated_factory_sha256'])}, "
            f"{item['anchor_count']}U, kMutation{index}RequiredWitnesses, "
            f"kMutation{index}DivergentRows, kMutation{index}Results}},")
    lines.extend(["}};", "", "struct MutationWitnessView { std::string_view mutation; std::string_view case_name; std::size_t mismatched_lanes; std::size_t lane_index; std::array<std::size_t, 2> top_down_xy; std::string_view channel; std::uint32_t reference_bits_le; std::uint32_t candidate_bits_le; };", f"inline constexpr std::array<MutationWitnessView, {sum(len(item['required_witness_results']) for item in oracle['behavioral_mutation_ledger'])}> kMutationWitnesses{{{{"])
    for item in oracle["behavioral_mutation_ledger"]:
        for result in item["required_witness_results"]:
            first = result["first_mismatch"]
            lines.append(
                f"  MutationWitnessView{{{cpp_string(item['name'])}, {cpp_string(result['case'])}, "
                f"{result['mismatched_lanes']}U, {first['lane_index']}U, "
                f"{{{first['top_down_xy'][0]}U, {first['top_down_xy'][1]}U}}, "
                f"{cpp_string(first['channel'])}, {first['reference_bits_le']}U, {first['candidate_bits_le']}U}},")
    lines.extend(["}};", "", "struct StructuralMutationView { std::string_view name; std::string_view pixel_expectation; };", f"inline constexpr std::array<StructuralMutationView, {len(oracle['structural_only_mutation_ledger'])}> kStructuralMutations{{{{"])
    lines.extend(f'  StructuralMutationView{{"{item["name"]}", "{item["pixel_expectation"]}"}},' for item in oracle["structural_only_mutation_ledger"])
    lines.extend(["}};", "", "static_assert(kBindingAbi.size() == 9U);", "static_assert(kCases.size() == kCaseCount);", "static_assert(kMutations.size() == 11U);", "static_assert(kMutationWitnesses.size() == 11U);", "}  // namespace lightleak192_oracle", ""])
    return "\n".join(lines).encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    oracle, oracle_hash = load()
    payload = render_include(oracle, oracle_hash)
    if args.self_test:
        self_test_forged_documents()
        if (payload.count(b"kCase") != 136 or
                payload.count(b"kBindingAbi") < 2 or
                payload.count(b"kMutations") < 2 or
                payload.count(b"kMutationWitnesses") < 2 or
                b"kCase0InputFloatWords" not in payload or
                b"input_phase" not in payload or
                b"kInputFixtureSchema" not in payload or
                b"kCaseControls" in payload):
            raise RuntimeError("LightLeak typed include self-test census failed")
        print("LightLeak192 native oracle self-test ok (11 cases, 73 matching-sidecar forgery probes)")
        return 0
    if args.write:
        OUTPUT.write_bytes(payload)
        OUTPUT.with_suffix(OUTPUT.suffix + ".sha256").write_text(sidecar_text(OUTPUT, payload))
    elif verify_sidecar(OUTPUT) != payload:
        raise RuntimeError("LightLeak192 native include is stale")
    print("LightLeak192 native oracle ok (11 cases)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"lightleak192: {error}", file=sys.stderr)
        raise SystemExit(1)
