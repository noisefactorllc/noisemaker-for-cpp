# Task 24 Gather Sorted public-canonical oracle report

Normative cases: **4**  
Normative mutations: **4**  
Exclusion controls: **3**

Public dispatch is the exact canonical factory and has no adapter. Every normative and exclusion case repeats byte-identically with immutable inputs and finite output.

## Normative cases

| Case | Size | Brightest rows | Output F32 SHA-256 | Output RGBA8 SHA-256 |
| --- | --- | --- | --- | --- |
| normalized-positive-zero | 9x4 | 0, 0, 0, 0 | `566cc3c05492199a3daf8bdcfffe9f610703f74e74defd5583b7e99f768f4390` | `cf0f9c006514afc91c0d06aa64053f5bab69a226385d6e15afe05f11786e4bf7` |
| normalized-negative-zero-control | 9x4 | 0(-0), 0(-0), 0(-0), 0(-0) | `566cc3c05492199a3daf8bdcfffe9f610703f74e74defd5583b7e99f768f4390` | `cf0f9c006514afc91c0d06aa64053f5bab69a226385d6e15afe05f11786e4bf7` |
| normalized-half-boundaries | 9x5 | 0.312375009059906, 0.3125, 0.312624990940094, 1, 0.125 | `66e27bbf10a8708b0fa12a5b3a37b98433cb27409e1b19d75477f026a9074381` | `e0e4181ebf3958dda73bc3f2d1e653d11a86cdcf457029d99875a10a07303f11` |
| normalized-wide-67 | 67x5 | 0, 0.25, 0.5, 0.75, 1 | `156bb977e833e4b09b51a83b2a357dec5baef1608224512c2920b78cd5dfbd43` | `67367ef5cae19cfb7c03d76d63f59e1b26a019531d23f15979c39629a6b57d3c` |

## Normative mutation sensitivity

| Mutation | Maximum changed F32 lanes | Maximum changed RGBA8 bytes |
| --- | ---: | ---: |
| round-replaced-by-floor | 512 | 490 |
| round-replaced-by-ceil | 36 | 36 |
| sample-loop-64-to-8 | 1161 | 1131 |
| native-floor-plus-half-with-int32-clamp | 0 | 0 |

## Exclusion controls

| Case | Purpose | Output F32 SHA-256 |
| --- | --- | --- |
| excluded-negative-half | outside-normalized-domain, Math.round-negative-zero, immediate-int-erases-sign | `795d16640209e8a06f4e3e8913233aca45bb519e3d457a5da130027c3af8609e` |
| excluded-out-of-range-wrap | outside-normalized-domain, JavaScript-ToInt32-wrap, native-int32-clamp-diverges | `795d16640209e8a06f4e3e8913233aca45bb519e3d457a5da130027c3af8609e` |

| Control mutation | Case | Same F32 | Changed F32 lanes | Changed RGBA8 bytes |
| --- | --- | --- | ---: | ---: |
| negative-half-native-floor-plus-half-control | excluded-negative-half | true | 0 | 0 |
| negative-half-std-round-away-from-zero-control | excluded-negative-half | false | 72 | 72 |
| out-of-range-native-int32-clamp-control | excluded-out-of-range-wrap | false | 64 | 61 |

The negative-half control proves immediate integer consumption erases JavaScript negative zero; an away-from-zero `std::round` model diverges. The out-of-range control proves JavaScript `|0` wrapping diverges from the native int32 clamp. Neither exclusion expands the normalized bounded native parity contract.

