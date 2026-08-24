# Task30 Extrude relational/reduction oracle report

Cases: **6**; public mutations: **4**; direct rows: **7**.

| Case | Size | Defines | F32 SHA-256 | RGBA8 SHA-256 |
| --- | --- | --- | --- | --- |
| blocks-default-luminance-solid | 13x9 | 0/0 | `47dee1b5c5d290f510a1c43f81f41bb19782b6f9f7d389e7be6701d0c8a01ac5` | `e4ebeebc17816ae9ca551c6a3c50ac250db9a04fee5b695a199dee420a07ec53` |
| blocks-depth-zero-window | 11x7 | 0/0 | `f8b901fde60223c9a3068ad5320295eed1098070d882978be5e5d6e3d4693106` | `aec6cc989aecad5bdc5b9c68f8ea13b4dd45f62abbd02851c35da8dbc729257a` |
| blocks-max-depth-luminance-window | 15x10 | 0/0 | `04ea7d2c0abee1daed54b97dcf1b1efb3c05cd828d23b8d2ac7c65d04d19ef73` | `c92a0ebc4b993ee019ac158f8803aa01ce6c21964e45695db14026a9f22e942d` |
| blocks-random-solid-tiled | 9x6 | 0/1 | `ae2facc61397f37864e00db0527c85fdcaab68ddfe6aa3a4f15b966850ad50b4` | `aea603f04f36c55d22b030c151cc312240ac4f28d64ff8188db1390746dcd247` |
| pyramids-luminance-solid | 12x8 | 1/0 | `9ce5cc08dbae5c256d4d3d52e2ae477bfbdc3c9244fd99f65fbcf2f8419e13cb` | `667cf0b76ea63ed5148e437b9475ca5c68c75cc4d3ff7d190c5f52a9d88bbbc4` |
| pyramids-random-window-tiled | 10x7 | 1/1 | `79ce9568db4351b9065475aff67840b6cc3a06b18c27ab4b889b21c0dbff5249` | `139dc9ffdacb79f31df4b32bd786bdf4ba809d5116520fa57ad58fd05811fa4b` |

| Mutation | Divergent cases |
| --- | ---: |
| top-lane-any | 3/6 |
| side-lane-any | 2/6 |
| top-strict-less | 4/6 |
| side-strict-less | 2/6 |

All factory mutations are output-discriminating. Native tests must also execute and transcribe all direct relational rows lane-by-lane; equality-boundary rows distinguish `<=` from `<`, and mixed-lane rows distinguish `all` from `any`.

