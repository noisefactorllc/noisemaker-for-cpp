# Task30 Extrude relational/reduction oracle report

Cases: **6**; public mutations: **4**; direct rows: **7**.

| Case | Size | Defines | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- |
| blocks-default-luminance-solid | 13x9 | 0/0 | `8d86661e6036c045791b5c4c8e284055838b44ae479903631c97405134e274e5` | `054594bfd42b605f9d5e860ffba16b364805eac5cd295296f1a7eace8c64ddee` |
| blocks-depth-zero-window | 11x7 | 0/0 | `f8b901fde60223c9a3068ad5320295eed1098070d882978be5e5d6e3d4693106` | `aec6cc989aecad5bdc5b9c68f8ea13b4dd45f62abbd02851c35da8dbc729257a` |
| blocks-max-depth-luminance-window | 15x10 | 0/0 | `d8757ab6a5685f58e89a8a17b92a335e0bba581c1156ea5c8b8bc03644a2c6c9` | `cfe0b56a504fb76c4e1d308e17fea6419bab745ebe5ba016ac1954787988c966` |
| blocks-random-solid-tiled | 9x6 | 0/1 | `ae2facc61397f37864e00db0527c85fdcaab68ddfe6aa3a4f15b966850ad50b4` | `aea603f04f36c55d22b030c151cc312240ac4f28d64ff8188db1390746dcd247` |
| pyramids-luminance-solid | 12x8 | 1/0 | `9270b9b7337e44f3473742c0e5fb42447c1589097c146ea636e9f68bb85d4017` | `dda87c0b80b52969deeb412d9ab553de20b274a430b7566652a032f8c59cf3ce` |
| pyramids-random-window-tiled | 10x7 | 1/1 | `f2c94cd4fe253d96a20141ea43fe97a703d6a9aa9f807807e4d9b31df6a0275c` | `139dc9ffdacb79f31df4b32bd786bdf4ba809d5116520fa57ad58fd05811fa4b` |

| Mutation | Divergent cases |
| --- | ---: |
| top-lane-any | 3/6 |
| side-lane-any | 1/6 |
| top-strict-less | 4/6 |
| side-strict-less | 1/6 |

All factory mutations are output-discriminating. Native tests must also execute and transcribe all direct relational rows lane-by-lane; equality-boundary rows distinguish `<=` from `<`, and mixed-lane rows distinguish `all` from `any`.

