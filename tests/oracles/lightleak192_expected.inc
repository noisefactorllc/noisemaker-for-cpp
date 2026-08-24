// Generated from the checked LightLeak192 canonical JavaScript oracle.
// Do not edit; C++ output never participates in expected arrays.
#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string_view>
#pragma once

namespace lightleak192_oracle {

inline constexpr std::string_view kOracleSha256 = "49d9d6718d7d659011890255202dc183dedd09a4db0706e9591b4ed94a73af22";
inline constexpr std::string_view kProgramKey = "filter/lightLeak:lightLeak";
inline constexpr std::size_t kCaseCount = 11U;
inline constexpr std::size_t kBindingCount = 9U;

inline constexpr std::string_view kInputFixtureSchema = "noisemaker-for-cpp.lightleak192.input-texture.v1";
inline constexpr std::string_view kInputFixtureSourceFunction = "inputSurface";
inline constexpr std::string_view kInputFixtureSourceFunctionSha256 = "31ca4a008de6ab3cfaafc0e0a1ed863153ddf6855d8f43aeb80b76963cc5a990";
inline constexpr std::string_view kInputFixtureCoordinateOrder = "x-fastest row-major";
inline constexpr std::array<std::string_view, 4> kInputFixtureFormulas{{
  "f(((x * 17 + y * 11 + phase) % 23) / 22)",
  "f(((x * 7 + y * 19 + phase * 2) % 29) / 28)",
  "f(((x * 13 + y * 5 + phase * 3) % 31) / 30)",
  "f(.4 + ((x + y + phase) % 5) / 10)",
}};

enum class BindingAbi { Sampler2D, Vec2, Vec3, Number, Int32 };
struct BindingView { std::string_view name; BindingAbi abi; std::string_view runtime_abi; std::string_view source_abi; }; using BindingAbiView = BindingView;
inline constexpr std::array<BindingView, 9> kBindingAbi{{
  BindingView{"inputTex", BindingAbi::Sampler2D, "sampler2D", "sampler2D"},
  BindingView{"resolution", BindingAbi::Vec2, "Vec2", "vec2"},
  BindingView{"tileOffset", BindingAbi::Vec2, "Vec2", "vec2"},
  BindingView{"fullResolution", BindingAbi::Vec2, "Vec2", "vec2"},
  BindingView{"alpha", BindingAbi::Number, "number", "float"},
  BindingView{"color", BindingAbi::Vec3, "Vec3", "vec3"},
  BindingView{"speed", BindingAbi::Number, "number", "float"},
  BindingView{"seed", BindingAbi::Int32, "int32", "int"},
  BindingView{"time", BindingAbi::Number, "number", "float"},
}};

struct SourceBindingView { std::string_view name; std::string_view source_abi; }; using SourceBindingAbiView = SourceBindingView;
inline constexpr std::array<SourceBindingView, 9> kSourceBindingAbi{{
  SourceBindingView{"inputTex", "sampler2D"},
  SourceBindingView{"resolution", "vec2"},
  SourceBindingView{"tileOffset", "vec2"},
  SourceBindingView{"fullResolution", "vec2"},
  SourceBindingView{"alpha", "float"},
  SourceBindingView{"color", "vec3"},
  SourceBindingView{"speed", "float"},
  SourceBindingView{"seed", "int"},
  SourceBindingView{"time", "float"},
}};

struct ScalarControl { float value; std::uint32_t word; };
struct Vec2Control { std::array<float, 2> values; std::array<std::uint32_t, 2> words; };
struct Vec3Control { std::array<float, 3> values; std::array<std::uint32_t, 3> words; };

inline constexpr std::array<std::uint32_t, 4> kCase0InputFloatWords{{
    0x3d3a2e8c, 0x3d924925, 0x3dcccccd, 0x3f000000,
}};
inline constexpr std::array<std::uint8_t, 4> kCase0InputRgbaBytes{{
    12U, 18U, 26U, 128U,
}};

inline constexpr std::array<std::uint32_t, 4> kCase0FloatWords{{
    0x3d3a2e8c, 0x3d924925, 0x3dcccccd, 0x3f000000,
}};
inline constexpr std::array<std::uint8_t, 4> kCase0RgbaBytes{{
    12U, 18U, 26U, 128U,
}};
inline constexpr std::array<std::uint32_t, 1> kCase0OutputAlphaFloatWords{{
    0x3f000000,
}};
inline constexpr std::array<std::uint8_t, 1> kCase0OutputAlphaRgbaBytes{{
    128U,
}};

inline constexpr std::array<std::uint32_t, 140> kCase1InputFloatWords{{
    0x3dba2e8c, 0x3e124925, 0x3e4ccccd, 0x3f19999a, 0x3f5d1746, 0x3ec92492, 0x3f222222, 0x3f333333,
    0x3f1745d1, 0x3f249249, 0x3d088889, 0x3f4ccccd, 0x3ea2e8ba, 0x3f649249, 0x3eeeeeef, 0x3ecccccd,
    0x3d3a2e8c, 0x3ddb6db7, 0x3f666666, 0x3f000000, 0x3f51745d, 0x3eb6db6e, 0x3e99999a, 0x3f19999a,
    0x3f0ba2e9, 0x3f1b6db7, 0x3f3bbbbc, 0x3f333333, 0x3f1745d1, 0x3f524925, 0x3ebbbbbc, 0x3f333333,
    0x3ea2e8ba, 0x3d124925, 0x3f4ccccd, 0x3f4ccccd, 0x3d3a2e8c, 0x3e924925, 0x3e4ccccd, 0x3ecccccd,
    0x3f51745d, 0x3f092492, 0x3f222222, 0x3f000000, 0x3f0ba2e9, 0x3f492492, 0x3d088889, 0x3f19999a,
    0x3e8ba2e9, 0x00000000, 0x3eeeeeef, 0x3f333333, 0x00000000, 0x3e800000, 0x3f666666, 0x3f4ccccd,
    0x3d3a2e8c, 0x3eedb6db, 0x3f088889, 0x3f4ccccd, 0x3f51745d, 0x3f36db6e, 0x3f777777, 0x3ecccccd,
    0x3f0ba2e9, 0x3f76db6e, 0x3ebbbbbc, 0x3f000000, 0x3e8ba2e9, 0x3e36db6e, 0x3f4ccccd, 0x3f19999a,
    0x00000000, 0x3edb6db7, 0x3e4ccccd, 0x3f333333, 0x3f45d174, 0x3f2db6db, 0x3f222222, 0x3f4ccccd,
    0x3f000000, 0x3f6db6db, 0x3d088889, 0x3ecccccd, 0x3f0ba2e9, 0x3ddb6db7, 0x3f333333, 0x3ecccccd,
    0x3e8ba2e9, 0x3eb6db6e, 0x3dcccccd, 0x3f000000, 0x00000000, 0x3f1b6db7, 0x3f088889, 0x3f19999a,
    0x3f45d174, 0x3f5b6db7, 0x3f777777, 0x3f333333, 0x3f000000, 0x3d924925, 0x3ebbbbbc, 0x3f4ccccd,
    0x3e68ba2f, 0x3ea49249, 0x3f4ccccd, 0x3ecccccd, 0x3f800000, 0x3f124925, 0x3e4ccccd, 0x3f000000,
    0x00000000, 0x3f492492, 0x3f5dddde, 0x3f000000, 0x3f45d174, 0x00000000, 0x3e888889, 0x3f19999a,
    0x3f000000, 0x3e800000, 0x3f333333, 0x3f333333, 0x3e68ba2f, 0x3f000000, 0x3dcccccd, 0x3f4ccccd,
    0x3f800000, 0x3f400000, 0x3f088889, 0x3ecccccd, 0x3f3a2e8c, 0x3f800000, 0x3f777777, 0x3f000000,
    0x3ee8ba2f, 0x3e5b6db7, 0x3ebbbbbc, 0x3f19999a,
}};
inline constexpr std::array<std::uint8_t, 140> kCase1InputRgbaBytes{{
    23U, 36U, 51U, 153U, 220U, 100U, 161U, 178U, 151U, 164U, 9U, 204U, 81U, 228U, 119U, 102U,
    12U, 27U, 229U, 128U, 209U, 91U, 77U, 153U, 139U, 155U, 187U, 178U, 151U, 209U, 94U, 178U,
    81U, 9U, 204U, 204U, 12U, 73U, 51U, 102U, 209U, 137U, 161U, 128U, 139U, 200U, 9U, 153U,
    70U, 0U, 119U, 178U, 0U, 64U, 229U, 204U, 12U, 118U, 136U, 204U, 209U, 182U, 246U, 102U,
    139U, 246U, 94U, 128U, 70U, 46U, 204U, 153U, 0U, 109U, 51U, 178U, 197U, 173U, 161U, 204U,
    128U, 237U, 9U, 102U, 139U, 27U, 178U, 102U, 70U, 91U, 26U, 128U, 0U, 155U, 136U, 153U,
    197U, 219U, 246U, 178U, 128U, 18U, 94U, 204U, 58U, 82U, 204U, 102U, 255U, 146U, 51U, 128U,
    0U, 200U, 221U, 128U, 197U, 0U, 68U, 153U, 128U, 64U, 178U, 178U, 58U, 128U, 26U, 204U,
    255U, 191U, 136U, 102U, 185U, 255U, 246U, 128U, 116U, 55U, 94U, 153U,
}};

inline constexpr std::array<std::uint32_t, 140> kCase1FloatWords{{
    0x3ec3563c, 0x3ee79253, 0x3eb78376, 0x3f19999a, 0x3f384548, 0x3f0a57c7, 0x3f2555e5, 0x3f333333,
    0x3f09cfd0, 0x3f19b78d, 0x3ea953a0, 0x3f4ccccd, 0x3f153393, 0x3f321a5d, 0x3f159417, 0x3ecccccd,
    0x3eba6e12, 0x3ee4a565, 0x3f326418, 0x3f000000, 0x3f3f6716, 0x3f16ddf3, 0x3ef71980, 0x3f19999a,
    0x3f1981a2, 0x3f2f1623, 0x3f36e40b, 0x3f333333, 0x3f0cddcb, 0x3f1d7f43, 0x3ee486f0, 0x3f333333,
    0x3f029976, 0x3ea3d314, 0x3f1f2f08, 0x3f4ccccd, 0x3e7ed552, 0x3f022b39, 0x3e68b43a, 0x3ecccccd,
    0x3f1f2428, 0x3efe4e16, 0x3f28459f, 0x3f000000, 0x3eb45786, 0x3ef8222a, 0x3ea41926, 0x3f19999a,
    0x3ecebd78, 0x3e63e07e, 0x3f137687, 0x3f333333, 0x3f07a5c9, 0x3f172c7f, 0x3f3381ce, 0x3f4ccccd,
    0x3eace218, 0x3f225b5d, 0x3f12937c, 0x3f4ccccd, 0x3f2997aa, 0x3eff33e9, 0x3f436ced, 0x3ecccccd,
    0x3ed5123f, 0x3f349856, 0x3ebc1b2d, 0x3f000000, 0x3ece8ba3, 0x3ee00000, 0x3f2bbbbc, 0x3f19999a,
    0x3e8739a7, 0x3f0f3350, 0x3ea8f8c1, 0x3f333333, 0x3f2fd570, 0x3f28f2b1, 0x3f16a316, 0x3f4ccccd,
    0x3f0c6d01, 0x3f400a24, 0x3e88b38b, 0x3ecccccd, 0x3f050342, 0x3f040468, 0x3f3214f6, 0x3ecccccd,
    0x3ef15698, 0x3ea83686, 0x3ed40dbf, 0x3f000000, 0x3e574b95, 0x3ecb0d27, 0x3f03ed85, 0x3f19999a,
    0x3f1507f3, 0x3f24eda3, 0x3f300985, 0x3f333333, 0x3f12ee86, 0x3ec4aa70, 0x3eb27c8b, 0x3f4ccccd,
    0x3efd8f8f, 0x3efb22ea, 0x3f3a7ecc, 0x3ecccccd, 0x3f3e8ba3, 0x3f014335, 0x3ecbd5d8, 0x3f000000,
    0x3ea2597d, 0x3f368502, 0x3f5354a2, 0x3f000000, 0x3f287544, 0x3ec0391c, 0x3f00045e, 0x3f19999a,
    0x3f1bab40, 0x3f112ba9, 0x3f3292ce, 0x3f333333, 0x3f059aa4, 0x3f06a88e, 0x3edef621, 0x3f4ccccd,
    0x3f3e8ba3, 0x3f1cc013, 0x3f0d1776, 0x3ecccccd, 0x3f30ec86, 0x3f4c9249, 0x3f3f0226, 0x3f000000,
    0x3f2b5e21, 0x3f0f9ebf, 0x3ee916ee, 0x3f19999a,
}};
inline constexpr std::array<std::uint8_t, 140> kCase1RgbaBytes{{
    97U, 115U, 91U, 153U, 184U, 138U, 165U, 178U, 137U, 153U, 84U, 204U, 149U, 177U, 149U, 102U,
    93U, 114U, 178U, 128U, 191U, 150U, 123U, 153U, 153U, 174U, 182U, 178U, 140U, 157U, 114U, 178U,
    130U, 82U, 159U, 204U, 63U, 130U, 58U, 102U, 159U, 127U, 168U, 128U, 90U, 124U, 82U, 153U,
    103U, 57U, 147U, 178U, 135U, 151U, 179U, 204U, 86U, 162U, 146U, 204U, 169U, 127U, 195U, 102U,
    106U, 180U, 94U, 128U, 103U, 112U, 171U, 153U, 67U, 143U, 84U, 178U, 175U, 168U, 150U, 204U,
    140U, 191U, 68U, 102U, 132U, 132U, 177U, 102U, 120U, 84U, 106U, 128U, 54U, 101U, 131U, 153U,
    148U, 164U, 175U, 178U, 146U, 98U, 89U, 204U, 126U, 125U, 186U, 102U, 190U, 129U, 102U, 128U,
    81U, 182U, 211U, 128U, 168U, 96U, 128U, 153U, 155U, 145U, 178U, 178U, 133U, 134U, 111U, 204U,
    190U, 156U, 141U, 102U, 176U, 204U, 190U, 128U, 171U, 143U, 116U, 153U,
}};
inline constexpr std::array<std::uint32_t, 35> kCase1OutputAlphaFloatWords{{
    0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f333333,
    0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3f4ccccd, 0x3ecccccd,
    0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a,
    0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd,
    0x3ecccccd, 0x3f000000, 0x3f19999a,
}};
inline constexpr std::array<std::uint8_t, 35> kCase1OutputAlphaRgbaBytes{{
    153U, 178U, 204U, 102U, 128U, 153U, 178U, 178U, 204U, 102U, 128U, 153U, 178U, 204U, 204U, 102U,
    128U, 153U, 178U, 204U, 102U, 102U, 128U, 153U, 178U, 204U, 102U, 128U, 128U, 153U, 178U, 204U,
    102U, 128U, 153U,
}};

inline constexpr std::array<std::uint32_t, 192> kCase2InputFloatWords{{
    0x3e0ba2e9, 0x3e5b6db7, 0x3e99999a, 0x3f333333, 0x3f68ba2f, 0x3eedb6db, 0x3f3bbbbc, 0x3f4ccccd,
    0x3f22e8ba, 0x3f36db6e, 0x3e088889, 0x3ecccccd, 0x3eba2e8c, 0x3f76db6e, 0x3f111111, 0x3f000000,
    0x3dba2e8c, 0x3e36db6e, 0x3f800000, 0x3f19999a, 0x3f5d1746, 0x3edb6db7, 0x3ecccccd, 0x3f333333,
    0x3f1745d1, 0x3f2db6db, 0x3f555555, 0x3f4ccccd, 0x3ea2e8ba, 0x3f6db6db, 0x3e6eeeef, 0x3ecccccd,
    0x3f22e8ba, 0x3f649249, 0x3eeeeeef, 0x3f4ccccd, 0x3eba2e8c, 0x3ddb6db7, 0x3f666666, 0x3ecccccd,
    0x3dba2e8c, 0x3eb6db6e, 0x3e99999a, 0x3f000000, 0x3f5d1746, 0x3f1b6db7, 0x3f3bbbbc, 0x3f19999a,
    0x3f1745d1, 0x3f5b6db7, 0x3e088889, 0x3f333333, 0x3ea2e8ba, 0x3d924925, 0x3f111111, 0x3f4ccccd,
    0x3d3a2e8c, 0x3ea49249, 0x3f800000, 0x3ecccccd, 0x3f51745d, 0x3f124925, 0x3ecccccd, 0x3f000000,
    0x3dba2e8c, 0x3f092492, 0x3f222222, 0x3ecccccd, 0x3f5d1746, 0x3f492492, 0x3d088889, 0x3f000000,
    0x3f1745d1, 0x00000000, 0x3eeeeeef, 0x3f19999a, 0x3ea2e8ba, 0x3e800000, 0x3f666666, 0x3f333333,
    0x3d3a2e8c, 0x3f000000, 0x3e99999a, 0x3f4ccccd, 0x3f51745d, 0x3f400000, 0x3f3bbbbc, 0x3ecccccd,
    0x3f0ba2e9, 0x3f800000, 0x3e088889, 0x3f000000, 0x3e8ba2e9, 0x3e5b6db7, 0x3f111111, 0x3f19999a,
    0x3f1745d1, 0x3e36db6e, 0x3f4ccccd, 0x3f000000, 0x3ea2e8ba, 0x3edb6db7, 0x3e4ccccd, 0x3f19999a,
    0x3d3a2e8c, 0x3f2db6db, 0x3f222222, 0x3f333333, 0x3f51745d, 0x3f6db6db, 0x3d088889, 0x3f4ccccd,
    0x3f0ba2e9, 0x3e124925, 0x3eeeeeef, 0x3ecccccd, 0x3e8ba2e9, 0x3ec92492, 0x3f666666, 0x3f000000,
    0x00000000, 0x3f249249, 0x3e99999a, 0x3f19999a, 0x3f45d174, 0x3f649249, 0x3f3bbbbc, 0x3f333333,
    0x3d3a2e8c, 0x3f5b6db7, 0x3f777777, 0x3f19999a, 0x3f51745d, 0x3d924925, 0x3ebbbbbc, 0x3f333333,
    0x3f0ba2e9, 0x3ea49249, 0x3f4ccccd, 0x3f4ccccd, 0x3e8ba2e9, 0x3f124925, 0x3e4ccccd, 0x3ecccccd,
    0x00000000, 0x3f524925, 0x3f222222, 0x3f000000, 0x3f45d174, 0x3d124925, 0x3d088889, 0x3f19999a,
    0x3f000000, 0x3e924925, 0x3eeeeeef, 0x3f333333, 0x3e68ba2f, 0x3f092492, 0x3f666666, 0x3f4ccccd,
    0x3f0ba2e9, 0x3f000000, 0x3dcccccd, 0x3f333333, 0x3e8ba2e9, 0x3f400000, 0x3f088889, 0x3f4ccccd,
    0x00000000, 0x3f800000, 0x3f777777, 0x3ecccccd, 0x3f45d174, 0x3e5b6db7, 0x3ebbbbbc, 0x3f000000,
    0x3f000000, 0x3eedb6db, 0x3f4ccccd, 0x3f19999a, 0x3e68ba2f, 0x3f36db6e, 0x3e4ccccd, 0x3f333333,
    0x3f800000, 0x3f76db6e, 0x3f222222, 0x3f4ccccd, 0x3f3a2e8c, 0x3e36db6e, 0x3d088889, 0x3ecccccd,
}};
inline constexpr std::array<std::uint8_t, 192> kCase2InputRgbaBytes{{
    35U, 55U, 77U, 178U, 232U, 118U, 187U, 204U, 162U, 182U, 34U, 102U, 93U, 246U, 144U, 128U,
    23U, 46U, 255U, 153U, 220U, 109U, 102U, 178U, 151U, 173U, 212U, 204U, 81U, 237U, 60U, 102U,
    162U, 228U, 119U, 204U, 93U, 27U, 229U, 102U, 23U, 91U, 77U, 128U, 220U, 155U, 187U, 153U,
    151U, 219U, 34U, 178U, 81U, 18U, 144U, 204U, 12U, 82U, 255U, 102U, 209U, 146U, 102U, 128U,
    23U, 137U, 161U, 102U, 220U, 200U, 9U, 128U, 151U, 0U, 119U, 153U, 81U, 64U, 229U, 178U,
    12U, 128U, 77U, 204U, 209U, 191U, 187U, 102U, 139U, 255U, 34U, 128U, 70U, 55U, 144U, 153U,
    151U, 46U, 204U, 128U, 81U, 109U, 51U, 153U, 12U, 173U, 161U, 178U, 209U, 237U, 9U, 204U,
    139U, 36U, 119U, 102U, 70U, 100U, 229U, 128U, 0U, 164U, 77U, 153U, 197U, 228U, 187U, 178U,
    12U, 219U, 246U, 153U, 209U, 18U, 94U, 178U, 139U, 82U, 204U, 204U, 70U, 146U, 51U, 102U,
    0U, 209U, 161U, 128U, 197U, 9U, 9U, 153U, 128U, 73U, 119U, 178U, 58U, 137U, 229U, 204U,
    139U, 128U, 26U, 178U, 70U, 191U, 136U, 204U, 0U, 255U, 246U, 102U, 197U, 55U, 94U, 128U,
    128U, 118U, 204U, 153U, 58U, 182U, 51U, 178U, 255U, 246U, 161U, 204U, 185U, 46U, 9U, 102U,
}};

inline constexpr std::array<std::uint32_t, 192> kCase2FloatWords{{
    0x3e845caf, 0x3ec148ac, 0x3edaec17, 0x3f333333, 0x3f5f9be0, 0x3f0be0b9, 0x3f3dadd4, 0x3f4ccccd,
    0x3f213986, 0x3f31754c, 0x3eaa5bde, 0x3ecccccd, 0x3ee186b1, 0x3f6a38ca, 0x3f27886a, 0x3f000000,
    0x3e550161, 0x3eaa69ae, 0x3f722222, 0x3f19999a, 0x3f57a918, 0x3f0c7df7, 0x3f04d82e, 0x3f333333,
    0x3f1b65f6, 0x3f384c1e, 0x3f532950, 0x3f4ccccd, 0x3ed63589, 0x3f66b562, 0x3eccb34d, 0x3ecccccd,
    0x3f25ceca, 0x3f59f0a6, 0x3f0f4ffc, 0x3f4ccccd, 0x3ed6bba0, 0x3e509358, 0x3f5c21aa, 0x3ecccccd,
    0x3e17e7f6, 0x3ed773c2, 0x3ea4aaab, 0x3f000000, 0x3f50b391, 0x3f1a149e, 0x3f365f1e, 0x3f19999a,
    0x3f0b81b5, 0x3f48b268, 0x3e6434aa, 0x3f333333, 0x3ebfe924, 0x3e10c9c0, 0x3f150000, 0x3f4ccccd,
    0x3e087cc1, 0x3ec97c76, 0x3f6d5556, 0x3ecccccd, 0x3f4f0590, 0x3f246f80, 0x3f083d57, 0x3f000000,
    0x3e62c85d, 0x3f16d284, 0x3f33adf4, 0x3ecccccd, 0x3f536c32, 0x3f3cbb47, 0x3e2ac622, 0x3f000000,
    0x3f0f3c50, 0x3d8e813c, 0x3ef0f556, 0x3f19999a, 0x3eb3b032, 0x3ea1399a, 0x3f55dfc3, 0x3f333333,
    0x3da04d7e, 0x3f000757, 0x3eaa3caf, 0x3f4ccccd, 0x3f494786, 0x3f2fcdec, 0x3f33f912, 0x3ecccccd,
    0x3f090e3a, 0x3f6d6db7, 0x3e6f94cc, 0x3f000000, 0x3ec3d0d7, 0x3ec42d0f, 0x3f28eab4, 0x3f19999a,
    0x3f1fdb60, 0x3eb21500, 0x3f4d3c7a, 0x3f000000, 0x3eb76407, 0x3ee9f314, 0x3e9467ad, 0x3f19999a,
    0x3da5d9e4, 0x3f25cf16, 0x3f22cbe8, 0x3f333333, 0x3f491898, 0x3f5d25a4, 0x3dc91315, 0x3f4ccccd,
    0x3f034a3e, 0x3e54c24c, 0x3eef032a, 0x3ecccccd, 0x3e9dd85a, 0x3edb80f4, 0x3f560e77, 0x3f000000,
    0x3dd5a097, 0x3f26984a, 0x3ec83dbc, 0x3f19999a, 0x3f490ed6, 0x3f5c5cc0, 0x3f424814, 0x3f333333,
    0x3e308222, 0x3f58a8ce, 0x3f6e68bc, 0x3f19999a, 0x3f441258, 0x3e4c360d, 0x3ed28e00, 0x3f333333,
    0x3f0056e9, 0x3ec177ac, 0x3f4ca16a, 0x3f4ccccd, 0x3ea89868, 0x3f06bb1c, 0x3e7bbbbc, 0x3ecccccd,
    0x3d727dc7, 0x3f457afc, 0x3f230000, 0x3f000000, 0x3f3a119d, 0x3e0659e0, 0x3dec4445, 0x3f19999a,
    0x3f0192f8, 0x3ec7ec62, 0x3f02beef, 0x3f333333, 0x3eb459f0, 0x3f105a81, 0x3f5a9a54, 0x3f4ccccd,
    0x3f13734c, 0x3f1a97d0, 0x3eb18f12, 0x3f333333, 0x3eb697e5, 0x3f40fc30, 0x3f16abee, 0x3f4ccccd,
    0x3dd86cf7, 0x3f752492, 0x3f6e0df8, 0x3ecccccd, 0x3f4221ef, 0x3ec878d6, 0x3ef10abe, 0x3f000000,
    0x3f09c7d7, 0x3f11c03c, 0x3f536482, 0x3f19999a, 0x3ea65034, 0x3f37960b, 0x3ebbac90, 0x3f333333,
    0x3f71d174, 0x3f6b8142, 0x3f2cf9ae, 0x3f4ccccd, 0x3f3db906, 0x3ec36506, 0x3e8bba89, 0x3ecccccd,
}};
inline constexpr std::array<std::uint8_t, 192> kCase2RgbaBytes{{
    66U, 96U, 109U, 178U, 223U, 139U, 189U, 204U, 161U, 177U, 85U, 102U, 112U, 233U, 167U, 128U,
    53U, 85U, 241U, 153U, 215U, 140U, 132U, 178U, 155U, 184U, 210U, 204U, 107U, 230U, 102U, 102U,
    165U, 217U, 143U, 204U, 107U, 52U, 219U, 102U, 38U, 107U, 82U, 128U, 208U, 153U, 182U, 153U,
    139U, 200U, 57U, 178U, 96U, 36U, 148U, 204U, 34U, 100U, 236U, 102U, 206U, 164U, 136U, 128U,
    56U, 150U, 179U, 102U, 211U, 188U, 43U, 128U, 143U, 18U, 120U, 153U, 89U, 80U, 213U, 178U,
    20U, 128U, 85U, 204U, 200U, 175U, 179U, 102U, 137U, 237U, 60U, 128U, 98U, 98U, 168U, 153U,
    159U, 89U, 204U, 128U, 91U, 117U, 74U, 153U, 21U, 165U, 162U, 178U, 200U, 220U, 25U, 204U,
    131U, 53U, 119U, 102U, 79U, 109U, 213U, 128U, 27U, 166U, 100U, 153U, 200U, 220U, 194U, 178U,
    44U, 216U, 237U, 153U, 195U, 51U, 105U, 178U, 128U, 96U, 204U, 204U, 84U, 134U, 63U, 102U,
    15U, 197U, 162U, 128U, 185U, 33U, 29U, 153U, 129U, 100U, 130U, 178U, 90U, 144U, 218U, 204U,
    147U, 154U, 88U, 178U, 91U, 192U, 150U, 204U, 27U, 244U, 237U, 102U, 193U, 100U, 120U, 128U,
    137U, 145U, 211U, 153U, 83U, 183U, 93U, 178U, 241U, 235U, 172U, 204U, 189U, 97U, 70U, 102U,
}};
inline constexpr std::array<std::uint32_t, 48> kCase2OutputAlphaFloatWords{{
    0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd,
    0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000,
    0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a,
    0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333,
    0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd,
    0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd,
}};
inline constexpr std::array<std::uint8_t, 48> kCase2OutputAlphaRgbaBytes{{
    178U, 204U, 102U, 128U, 153U, 178U, 204U, 102U, 204U, 102U, 128U, 153U, 178U, 204U, 102U, 128U,
    102U, 128U, 153U, 178U, 204U, 102U, 128U, 153U, 128U, 153U, 178U, 204U, 102U, 128U, 153U, 178U,
    153U, 178U, 204U, 102U, 128U, 153U, 178U, 204U, 178U, 204U, 102U, 128U, 153U, 178U, 204U, 102U,
}};

inline constexpr std::array<std::uint32_t, 100> kCase3InputFloatWords{{
    0x3e3a2e8c, 0x3e924925, 0x3ecccccd, 0x3f4ccccd, 0x3f745d17, 0x3f092492, 0x3f555555, 0x3ecccccd,
    0x3f2e8ba3, 0x3f492492, 0x3e6eeeef, 0x3f000000, 0x3ed1745d, 0x00000000, 0x3f2aaaab, 0x3f19999a,
    0x3e0ba2e9, 0x3e800000, 0x3d888889, 0x3f333333, 0x3f2e8ba3, 0x3f76db6e, 0x3f111111, 0x3ecccccd,
    0x3ed1745d, 0x3e36db6e, 0x3f800000, 0x3f000000, 0x3e0ba2e9, 0x3edb6db7, 0x3ecccccd, 0x3f19999a,
    0x3f68ba2f, 0x3f2db6db, 0x3f555555, 0x3f333333, 0x3f22e8ba, 0x3f6db6db, 0x3e6eeeef, 0x3f4ccccd,
    0x3e0ba2e9, 0x3f1b6db7, 0x3f3bbbbc, 0x3f000000, 0x3f68ba2f, 0x3f5b6db7, 0x3e088889, 0x3f19999a,
    0x3f22e8ba, 0x3d924925, 0x3f111111, 0x3f333333, 0x3eba2e8c, 0x3ea49249, 0x3f800000, 0x3f4ccccd,
    0x3dba2e8c, 0x3f124925, 0x3ecccccd, 0x3ecccccd, 0x3f22e8ba, 0x3e800000, 0x3f666666, 0x3f19999a,
    0x3eba2e8c, 0x3f000000, 0x3e99999a, 0x3f333333, 0x3dba2e8c, 0x3f400000, 0x3f3bbbbc, 0x3f4ccccd,
    0x3f5d1746, 0x3f800000, 0x3e088889, 0x3ecccccd, 0x3f1745d1, 0x3e5b6db7, 0x3f111111, 0x3f000000,
    0x3dba2e8c, 0x3f6db6db, 0x3d088889, 0x3f333333, 0x3f5d1746, 0x3e124925, 0x3eeeeeef, 0x3f4ccccd,
    0x3f1745d1, 0x3ec92492, 0x3f666666, 0x3ecccccd, 0x3ea2e8ba, 0x3f249249, 0x3e99999a, 0x3f000000,
    0x3d3a2e8c, 0x3f649249, 0x3f3bbbbc, 0x3f19999a,
}};
inline constexpr std::array<std::uint8_t, 100> kCase3InputRgbaBytes{{
    46U, 73U, 102U, 204U, 243U, 137U, 212U, 102U, 174U, 200U, 60U, 128U, 104U, 0U, 170U, 153U,
    35U, 64U, 17U, 178U, 174U, 246U, 144U, 102U, 104U, 46U, 255U, 128U, 35U, 109U, 102U, 153U,
    232U, 173U, 212U, 178U, 162U, 237U, 60U, 204U, 35U, 155U, 187U, 128U, 232U, 219U, 34U, 153U,
    162U, 18U, 144U, 178U, 93U, 82U, 255U, 204U, 23U, 146U, 102U, 102U, 162U, 64U, 229U, 153U,
    93U, 128U, 77U, 178U, 23U, 191U, 187U, 204U, 220U, 255U, 34U, 102U, 151U, 55U, 144U, 128U,
    23U, 237U, 9U, 178U, 220U, 36U, 119U, 204U, 151U, 100U, 229U, 102U, 81U, 164U, 77U, 128U,
    12U, 228U, 187U, 153U,
}};

inline constexpr std::array<std::uint32_t, 100> kCase3FloatWords{{
    0x3ece6119, 0x3eca5a9f, 0x3ef35b67, 0x3f4ccccd, 0x3f4b1b4e, 0x3f01a4cf, 0x3f2fcf7e, 0x3ecccccd,
    0x3f1c5179, 0x3f13badb, 0x3eb0937d, 0x3f000000, 0x3f0d9dd9, 0x3e6cfdde, 0x3f2f5d73, 0x3f19999a,
    0x3eb6816d, 0x3ed8a9e6, 0x3e57fa4c, 0x3f333333, 0x3f1be83e, 0x3f393aec, 0x3f1b1704, 0x3ecccccd,
    0x3f13640e, 0x3eda6c06, 0x3f511112, 0x3f000000, 0x3ead387b, 0x3f257632, 0x3ed80b99, 0x3f19999a,
    0x3f3ed032, 0x3f1abddd, 0x3f2bf7f1, 0x3f333333, 0x3f1389f3, 0x3f315103, 0x3eaf8285, 0x3f4ccccd,
    0x3eb6f090, 0x3f0b3ac7, 0x3f1b1c50, 0x3f000000, 0x3f3ec6df, 0x3f215c82, 0x3ee517ff, 0x3f19999a,
    0x3f01745d, 0x3ea92492, 0x3f111111, 0x3f333333, 0x3eced904, 0x3ed8eafe, 0x3f300000, 0x3f4ccccd,
    0x3ea9e95e, 0x3f03529b, 0x3ef22ce2, 0x3ecccccd, 0x3f0f5c55, 0x3f0dfcaa, 0x3f3b686c, 0x3f19999a,
    0x3f08dcef, 0x3ee613e5, 0x3eed7655, 0x3f333333, 0x3e991f67, 0x3f0988cd, 0x3f36876b, 0x3f4ccccd,
    0x3f34cf7c, 0x3f412492, 0x3ea44e68, 0x3ecccccd, 0x3f09cafa, 0x3f05da70, 0x3f1a8cb8, 0x3f000000,
    0x3ea7b116, 0x3f527529, 0x3e9f88d9, 0x3f333333, 0x3f3b8356, 0x3edcb9bc, 0x3ec83845, 0x3f4ccccd,
    0x3f0b9a7e, 0x3f09cb31, 0x3f3d0538, 0x3ecccccd, 0x3efa323b, 0x3f1aa707, 0x3f06b6be, 0x3f000000,
    0x3e948aff, 0x3f4ca9fa, 0x3f3c4a06, 0x3f19999a,
}};
inline constexpr std::array<std::uint8_t, 100> kCase3RgbaBytes{{
    103U, 101U, 121U, 204U, 202U, 129U, 175U, 102U, 156U, 147U, 88U, 128U, 141U, 59U, 175U, 153U,
    91U, 108U, 54U, 178U, 155U, 185U, 154U, 102U, 147U, 109U, 208U, 128U, 86U, 165U, 108U, 153U,
    190U, 154U, 171U, 178U, 147U, 177U, 87U, 204U, 91U, 139U, 155U, 128U, 190U, 161U, 114U, 153U,
    129U, 84U, 144U, 178U, 103U, 108U, 175U, 204U, 85U, 131U, 121U, 102U, 143U, 141U, 187U, 153U,
    136U, 115U, 118U, 178U, 76U, 137U, 182U, 204U, 180U, 192U, 82U, 102U, 137U, 133U, 154U, 128U,
    84U, 210U, 79U, 178U, 187U, 110U, 100U, 204U, 139U, 137U, 188U, 102U, 125U, 154U, 134U, 128U,
    74U, 204U, 188U, 153U,
}};
inline constexpr std::array<std::uint32_t, 25> kCase3OutputAlphaFloatWords{{
    0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3ecccccd, 0x3f000000, 0x3f19999a,
    0x3f333333, 0x3f4ccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f19999a,
    0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000,
    0x3f19999a,
}};
inline constexpr std::array<std::uint8_t, 25> kCase3OutputAlphaRgbaBytes{{
    204U, 102U, 128U, 153U, 178U, 102U, 128U, 153U, 178U, 204U, 128U, 153U, 178U, 204U, 102U, 153U,
    178U, 204U, 102U, 128U, 178U, 204U, 102U, 128U, 153U,
}};

inline constexpr std::array<std::uint32_t, 96> kCase4InputFloatWords{{
    0x3e68ba2f, 0x3eb6db6e, 0x3f000000, 0x3ecccccd, 0x3f800000, 0x3f1b6db7, 0x3f6eeeef, 0x3f000000,
    0x3f3a2e8c, 0x3f5b6db7, 0x3eaaaaab, 0x3f19999a, 0x3ee8ba2f, 0x3d924925, 0x3f444444, 0x3f333333,
    0x3e3a2e8c, 0x3ea49249, 0x3e2aaaab, 0x3f4ccccd, 0x3f745d17, 0x3f124925, 0x3f19999a, 0x3ecccccd,
    0x3f3a2e8c, 0x00000000, 0x3f2aaaab, 0x3f000000, 0x3ee8ba2f, 0x3e800000, 0x3d888889, 0x3f19999a,
    0x3e3a2e8c, 0x3f000000, 0x3f000000, 0x3f333333, 0x3f745d17, 0x3f400000, 0x3f6eeeef, 0x3f4ccccd,
    0x3f2e8ba3, 0x3f800000, 0x3eaaaaab, 0x3ecccccd, 0x3ed1745d, 0x3e5b6db7, 0x3f444444, 0x3f000000,
    0x3e3a2e8c, 0x3f2db6db, 0x3f555555, 0x3f19999a, 0x3f745d17, 0x3f6db6db, 0x3e6eeeef, 0x3f333333,
    0x3f2e8ba3, 0x3e124925, 0x3f2aaaab, 0x3f4ccccd, 0x3ed1745d, 0x3ec92492, 0x3d888889, 0x3ecccccd,
    0x3e0ba2e9, 0x3f249249, 0x3f000000, 0x3f000000, 0x3f68ba2f, 0x3f649249, 0x3f6eeeef, 0x3f19999a,
    0x3f2e8ba3, 0x3ea49249, 0x3f800000, 0x3f333333, 0x3ed1745d, 0x3f124925, 0x3ecccccd, 0x3f4ccccd,
    0x3e0ba2e9, 0x3f524925, 0x3f555555, 0x3ecccccd, 0x3f68ba2f, 0x3d124925, 0x3e6eeeef, 0x3f000000,
    0x3f22e8ba, 0x3e924925, 0x3f2aaaab, 0x3f19999a, 0x3eba2e8c, 0x3f092492, 0x3d888889, 0x3f333333,
}};
inline constexpr std::array<std::uint8_t, 96> kCase4InputRgbaBytes{{
    58U, 91U, 128U, 102U, 255U, 155U, 238U, 128U, 185U, 219U, 85U, 153U, 116U, 18U, 195U, 178U,
    46U, 82U, 43U, 204U, 243U, 146U, 153U, 102U, 185U, 0U, 170U, 128U, 116U, 64U, 17U, 153U,
    46U, 128U, 128U, 178U, 243U, 191U, 238U, 204U, 174U, 255U, 85U, 102U, 104U, 55U, 195U, 128U,
    46U, 173U, 212U, 153U, 243U, 237U, 60U, 178U, 174U, 36U, 170U, 204U, 104U, 100U, 17U, 102U,
    35U, 164U, 128U, 128U, 232U, 228U, 238U, 153U, 174U, 82U, 255U, 178U, 104U, 146U, 102U, 204U,
    35U, 209U, 212U, 102U, 232U, 9U, 60U, 128U, 162U, 73U, 170U, 153U, 93U, 137U, 17U, 178U,
}};

inline constexpr std::array<std::uint32_t, 96> kCase4FloatWords{{
    0x3ed6ed12, 0x3ef3dcae, 0x3f0f178a, 0x3ecccccd, 0x3f64129e, 0x3f1b8849, 0x3f5533d0, 0x3f000000,
    0x3f2c667d, 0x3f3afbc8, 0x3ec9c4ec, 0x3f19999a, 0x3f17f514, 0x3e72d7bc, 0x3f397d15, 0x3f333333,
    0x3ebeea3e, 0x3ee77056, 0x3e9522a5, 0x3f4ccccd, 0x3f6b3f68, 0x3f1f8c29, 0x3f2da0f4, 0x3ecccccd,
    0x3f307935, 0x3e81180f, 0x3f32fc7c, 0x3f000000, 0x3f121d8f, 0x3eaa3211, 0x3e950ba5, 0x3f19999a,
    0x3e9d0eac, 0x3f0dfb3d, 0x3f038176, 0x3f333333, 0x3f53cc35, 0x3f0e4ff3, 0x3f4808ba, 0x3f4ccccd,
    0x3f15643c, 0x3f492492, 0x3ece45d4, 0x3ecccccd, 0x3f172e28, 0x3ec54bce, 0x3f3b5e63, 0x3f000000,
    0x3ecf5247, 0x3f211cc8, 0x3f52788b, 0x3f19999a, 0x3f4f5f61, 0x3f500b1f, 0x3eaff500, 0x3f333333,
    0x3f0f0171, 0x3ead1c02, 0x3f274c69, 0x3f4ccccd, 0x3f0985db, 0x3ed804cc, 0x3e60a66b, 0x3ecccccd,
    0x3e9be5d1, 0x3f12b19b, 0x3f0a6b03, 0x3f000000, 0x3f5839bb, 0x3f5088bc, 0x3f46327d, 0x3f19999a,
    0x3f32ddb7, 0x3edb15af, 0x3f75c28f, 0x3f333333, 0x3f0c4f3d, 0x3f05efbf, 0x3ee0c5da, 0x3f4ccccd,
    0x3eaf6f6b, 0x3f385013, 0x3f51de77, 0x3ecccccd, 0x3f570295, 0x3e86765e, 0x3ea7bd20, 0x3f000000,
    0x3f1f84e5, 0x3edd5597, 0x3f211b07, 0x3f19999a, 0x3f044a5f, 0x3f09a0c5, 0x3e625663, 0x3f333333,
}};
inline constexpr std::array<std::uint8_t, 96> kCase4RgbaBytes{{
    107U, 121U, 143U, 102U, 227U, 155U, 212U, 128U, 172U, 186U, 100U, 153U, 151U, 60U, 185U, 178U,
    95U, 115U, 74U, 204U, 234U, 159U, 173U, 102U, 176U, 64U, 178U, 128U, 146U, 85U, 74U, 153U,
    78U, 141U, 131U, 178U, 211U, 142U, 199U, 204U, 149U, 200U, 103U, 102U, 151U, 98U, 187U, 128U,
    103U, 160U, 210U, 153U, 207U, 207U, 88U, 178U, 142U, 86U, 167U, 204U, 137U, 108U, 56U, 102U,
    78U, 146U, 138U, 128U, 215U, 208U, 197U, 153U, 178U, 109U, 245U, 178U, 140U, 133U, 112U, 204U,
    87U, 184U, 209U, 102U, 214U, 67U, 84U, 128U, 159U, 110U, 160U, 153U, 132U, 137U, 56U, 178U,
}};
inline constexpr std::array<std::uint32_t, 24> kCase4OutputAlphaFloatWords{{
    0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a,
    0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd,
    0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333,
}};
inline constexpr std::array<std::uint8_t, 24> kCase4OutputAlphaRgbaBytes{{
    102U, 128U, 153U, 178U, 204U, 102U, 128U, 153U, 178U, 204U, 102U, 128U, 153U, 178U, 204U, 102U,
    128U, 153U, 178U, 204U, 102U, 128U, 153U, 178U,
}};

inline constexpr std::array<std::uint32_t, 252> kCase5InputFloatWords{{
    0x3e8ba2e9, 0x3edb6db7, 0x3f19999a, 0x3f000000, 0x00000000, 0x3f2db6db, 0x00000000, 0x3f19999a,
    0x3f45d174, 0x3f6db6db, 0x3eddddde, 0x3f333333, 0x3f000000, 0x3e124925, 0x3f5dddde, 0x3f4ccccd,
    0x3e68ba2f, 0x3ec92492, 0x3e888889, 0x3ecccccd, 0x3f800000, 0x3f249249, 0x3f333333, 0x3f000000,
    0x3f3a2e8c, 0x3f649249, 0x3dcccccd, 0x3f19999a, 0x3ee8ba2f, 0x3ddb6db7, 0x3f088889, 0x3f333333,
    0x3e3a2e8c, 0x3eb6db6e, 0x3f777777, 0x3f4ccccd, 0x3f45d174, 0x3d924925, 0x3f444444, 0x3f19999a,
    0x3f000000, 0x3ea49249, 0x3e2aaaab, 0x3f333333, 0x3e68ba2f, 0x3f124925, 0x3f19999a, 0x3f4ccccd,
    0x3f800000, 0x3f524925, 0x00000000, 0x3ecccccd, 0x3f3a2e8c, 0x3d124925, 0x3eddddde, 0x3f000000,
    0x3ee8ba2f, 0x3e924925, 0x3f5dddde, 0x3f19999a, 0x3e3a2e8c, 0x3f092492, 0x3e888889, 0x3f333333,
    0x3f745d17, 0x3f492492, 0x3f333333, 0x3f4ccccd, 0x3f2e8ba3, 0x00000000, 0x3dcccccd, 0x3ecccccd,
    0x3e68ba2f, 0x3f400000, 0x3f6eeeef, 0x3f333333, 0x3f800000, 0x3f800000, 0x3eaaaaab, 0x3f4ccccd,
    0x3f3a2e8c, 0x3e5b6db7, 0x3f444444, 0x3ecccccd, 0x3ee8ba2f, 0x3eedb6db, 0x3e2aaaab, 0x3f000000,
    0x3e3a2e8c, 0x3f36db6e, 0x3f19999a, 0x3f19999a, 0x3f745d17, 0x3f76db6e, 0x00000000, 0x3f333333,
    0x3f2e8ba3, 0x3e36db6e, 0x3eddddde, 0x3f4ccccd, 0x3ed1745d, 0x3edb6db7, 0x3f5dddde, 0x3ecccccd,
    0x3e0ba2e9, 0x3f2db6db, 0x3e888889, 0x3f000000, 0x3f3a2e8c, 0x3ec92492, 0x3d888889, 0x3f4ccccd,
    0x3ee8ba2f, 0x3f249249, 0x3f000000, 0x3ecccccd, 0x3e3a2e8c, 0x3f649249, 0x3f6eeeef, 0x3f000000,
    0x3f745d17, 0x3ddb6db7, 0x3eaaaaab, 0x3f19999a, 0x3f2e8ba3, 0x3eb6db6e, 0x3f444444, 0x3f333333,
    0x3ed1745d, 0x3f1b6db7, 0x3e2aaaab, 0x3f4ccccd, 0x3e0ba2e9, 0x3f5b6db7, 0x3f19999a, 0x3ecccccd,
    0x3f68ba2f, 0x3d924925, 0x00000000, 0x3f000000, 0x3f22e8ba, 0x3ea49249, 0x3eddddde, 0x3f19999a,
    0x3e3a2e8c, 0x3d124925, 0x3e6eeeef, 0x3ecccccd, 0x3f745d17, 0x3e924925, 0x3f2aaaab, 0x3f000000,
    0x3f2e8ba3, 0x3f092492, 0x3d888889, 0x3f19999a, 0x3ed1745d, 0x3f492492, 0x3f000000, 0x3f333333,
    0x3e0ba2e9, 0x00000000, 0x3f6eeeef, 0x3f4ccccd, 0x3f68ba2f, 0x3e800000, 0x3eaaaaab, 0x3ecccccd,
    0x3f22e8ba, 0x3f000000, 0x3f444444, 0x3f000000, 0x3eba2e8c, 0x3f400000, 0x3e2aaaab, 0x3f19999a,
    0x3dba2e8c, 0x3f800000, 0x3f19999a, 0x3f333333, 0x3f2e8ba3, 0x3f36db6e, 0x3ecccccd, 0x3f000000,
    0x3ed1745d, 0x3f76db6e, 0x3f555555, 0x3f19999a, 0x3e0ba2e9, 0x3e36db6e, 0x3e6eeeef, 0x3f333333,
    0x3f68ba2f, 0x3edb6db7, 0x3f2aaaab, 0x3f4ccccd, 0x3f22e8ba, 0x3f2db6db, 0x3d888889, 0x3ecccccd,
    0x3eba2e8c, 0x3f6db6db, 0x3f000000, 0x3f000000, 0x3dba2e8c, 0x3e124925, 0x3f6eeeef, 0x3f19999a,
    0x3f5d1746, 0x3ec92492, 0x3eaaaaab, 0x3f333333, 0x3f1745d1, 0x3f249249, 0x3f444444, 0x3f4ccccd,
    0x3e0ba2e9, 0x3eb6db6e, 0x3f111111, 0x3f19999a, 0x3f68ba2f, 0x3f1b6db7, 0x3f800000, 0x3f333333,
    0x3f22e8ba, 0x3f5b6db7, 0x3ecccccd, 0x3f4ccccd, 0x3eba2e8c, 0x3d924925, 0x3f555555, 0x3ecccccd,
    0x3dba2e8c, 0x3ea49249, 0x3e6eeeef, 0x3f000000, 0x3f5d1746, 0x3f124925, 0x3f2aaaab, 0x3f19999a,
    0x3f1745d1, 0x3f524925, 0x3d888889, 0x3f333333, 0x3ea2e8ba, 0x3d124925, 0x3f000000, 0x3f4ccccd,
    0x3d3a2e8c, 0x3e924925, 0x3f6eeeef, 0x3ecccccd,
}};
inline constexpr std::array<std::uint8_t, 252> kCase5InputRgbaBytes{{
    70U, 109U, 153U, 128U, 0U, 173U, 0U, 153U, 197U, 237U, 111U, 178U, 128U, 36U, 221U, 204U,
    58U, 100U, 68U, 102U, 255U, 164U, 178U, 128U, 185U, 228U, 26U, 153U, 116U, 27U, 136U, 178U,
    46U, 91U, 246U, 204U, 197U, 18U, 195U, 153U, 128U, 82U, 43U, 178U, 58U, 146U, 153U, 204U,
    255U, 209U, 0U, 102U, 185U, 9U, 111U, 128U, 116U, 73U, 221U, 153U, 46U, 137U, 68U, 178U,
    243U, 200U, 178U, 204U, 174U, 0U, 26U, 102U, 58U, 191U, 238U, 178U, 255U, 255U, 85U, 204U,
    185U, 55U, 195U, 102U, 116U, 118U, 43U, 128U, 46U, 182U, 153U, 153U, 243U, 246U, 0U, 178U,
    174U, 46U, 111U, 204U, 104U, 109U, 221U, 102U, 35U, 173U, 68U, 128U, 185U, 100U, 17U, 204U,
    116U, 164U, 128U, 102U, 46U, 228U, 238U, 128U, 243U, 27U, 85U, 153U, 174U, 91U, 195U, 178U,
    104U, 155U, 43U, 204U, 35U, 219U, 153U, 102U, 232U, 18U, 0U, 128U, 162U, 82U, 111U, 153U,
    46U, 9U, 60U, 102U, 243U, 73U, 170U, 128U, 174U, 137U, 17U, 153U, 104U, 200U, 128U, 178U,
    35U, 0U, 238U, 204U, 232U, 64U, 85U, 102U, 162U, 128U, 195U, 128U, 93U, 191U, 43U, 153U,
    23U, 255U, 153U, 178U, 174U, 182U, 102U, 128U, 104U, 246U, 212U, 153U, 35U, 46U, 60U, 178U,
    232U, 109U, 170U, 204U, 162U, 173U, 17U, 102U, 93U, 237U, 128U, 128U, 23U, 36U, 238U, 153U,
    220U, 100U, 85U, 178U, 151U, 164U, 195U, 204U, 35U, 91U, 144U, 153U, 232U, 155U, 255U, 178U,
    162U, 219U, 102U, 204U, 93U, 18U, 212U, 102U, 23U, 82U, 60U, 128U, 220U, 146U, 170U, 153U,
    151U, 209U, 17U, 178U, 81U, 9U, 128U, 204U, 12U, 73U, 238U, 102U,
}};

inline constexpr std::array<std::uint32_t, 252> kCase5FloatWords{{
    0x3eda84eb, 0x3f303639, 0x3f2e3f00, 0x3f000000, 0x3e9ca1e4, 0x3f3797fa, 0x3ea2c16f, 0x3f19999a,
    0x3f3105e8, 0x3f453d72, 0x3f0b979c, 0x3f333333, 0x3f0f1048, 0x3f02609c, 0x3f3595d8, 0x3f4ccccd,
    0x3ee1f701, 0x3f3146fe, 0x3ed0f11d, 0x3ecccccd, 0x3f63b940, 0x3f2a7c5f, 0x3f2ca826, 0x3f000000,
    0x3f27f3b6, 0x3f3e8a3f, 0x3ebcbb09, 0x3f19999a, 0x3f0680f8, 0x3ed02eb1, 0x3f319437, 0x3f333333,
    0x3eb40cdb, 0x3f241b91, 0x3f503141, 0x3f4ccccd, 0x3f31ea75, 0x3ef1325c, 0x3f32b3a1, 0x3f19999a,
    0x3f0bad15, 0x3ef59414, 0x3e891c95, 0x3f333333, 0x3ece5722, 0x3f0ec8f5, 0x3f20a85a, 0x3f4ccccd,
    0x3f56c37e, 0x3f15a62e, 0x3e811019, 0x3ecccccd, 0x3f12e715, 0x3e84e581, 0x3eeeaf90, 0x3f000000,
    0x3f2069c5, 0x3efe74b8, 0x3f2d9990, 0x3f19999a, 0x3eb92e57, 0x3f0628a5, 0x3e9bf75c, 0x3f333333,
    0x3f529529, 0x3f08200a, 0x3f15a1e4, 0x3f4ccccd, 0x3f1bc843, 0x3ebcaeb1, 0x3ec60326, 0x3ecccccd,
    0x3eb59184, 0x3f265858, 0x3f528acd, 0x3f333333, 0x3f42bc0c, 0x3f50c9df, 0x3ed0fac0, 0x3f4ccccd,
    0x3f1fb13e, 0x3ee06439, 0x3f2a0a68, 0x3ecccccd, 0x3f0fab04, 0x3f121f82, 0x3e8b9386, 0x3f000000,
    0x3e93ed83, 0x3f015d90, 0x3f19d085, 0x3f19999a, 0x3f59489d, 0x3f4130fd, 0x3e58786d, 0x3f333333,
    0x3f13f8ad, 0x3ecd5209, 0x3ee0e0c0, 0x3f4ccccd, 0x3ee9b268, 0x3f0df063, 0x3f1eea32, 0x3ecccccd,
    0x3e8f5413, 0x3f34f40e, 0x3f024ee1, 0x3f000000, 0x3f331710, 0x3f16fb68, 0x3ed21ada, 0x3f4ccccd,
    0x3f0cbfeb, 0x3f16f498, 0x3eedaa0a, 0x3ecccccd, 0x3e95bcdc, 0x3f2f64fc, 0x3f397f2d, 0x3f000000,
    0x3f59450e, 0x3ea2c7e4, 0x3eaad503, 0x3f19999a, 0x3f137281, 0x3eec8c70, 0x3f297b90, 0x3f333333,
    0x3f03ea41, 0x3f00b0c9, 0x3e8b3ffc, 0x3f4ccccd, 0x3e803959, 0x3f265e00, 0x3f1af203, 0x3ecccccd,
    0x3f5574bd, 0x3ea839fa, 0x3e5f202c, 0x3f000000, 0x3f1f859c, 0x3f0b1f01, 0x3f0b4f8f, 0x3f19999a,
    0x3eab1afd, 0x3ee242c9, 0x3edca471, 0x3ecccccd, 0x3f52a7cf, 0x3ef321f2, 0x3f1efec1, 0x3f000000,
    0x3f13eefc, 0x3ee12f7f, 0x3e91090b, 0x3f19999a, 0x3f03fb30, 0x3f13a1e4, 0x3f002c98, 0x3f333333,
    0x3e78f662, 0x3e5a24bd, 0x3f3963a3, 0x3f4ccccd, 0x3f4da761, 0x3eeca649, 0x3eab25d6, 0x3ecccccd,
    0x3f086461, 0x3f0278e3, 0x3f29fa4c, 0x3f000000, 0x3ed7d5d0, 0x3f242d11, 0x3ec601ec, 0x3f19999a,
    0x3e71c7de, 0x3f5831bc, 0x3f2e222e, 0x3f333333, 0x3f1df7c7, 0x3f2b5b92, 0x3ee95744, 0x3f000000,
    0x3f111e75, 0x3f51b32b, 0x3f437d53, 0x3f19999a, 0x3ea21ebb, 0x3eed22f4, 0x3eae79bd, 0x3f333333,
    0x3f410d24, 0x3efd625b, 0x3f2832cb, 0x3f4ccccd, 0x3ef8c4fc, 0x3f059f75, 0x3e8f096b, 0x3ecccccd,
    0x3f0912f0, 0x3f423ebd, 0x3efd14df, 0x3f000000, 0x3e88e480, 0x3ede33b6, 0x3f356da0, 0x3f19999a,
    0x3f3d2cfb, 0x3eed1791, 0x3ecf05fc, 0x3f333333, 0x3f0a9ab3, 0x3f1e5633, 0x3f4cfc1d, 0x3f4ccccd,
    0x3e9bae22, 0x3f0d7b44, 0x3f14cc58, 0x3f19999a, 0x3f4a6fa8, 0x3f17a558, 0x3f67ced9, 0x3f333333,
    0x3f13d848, 0x3f416131, 0x3ee4fda7, 0x3f4ccccd, 0x3f0bf5d7, 0x3ef2bce9, 0x3f5252e6, 0x3ecccccd,
    0x3e9be8b8, 0x3f0eaa2a, 0x3ecf3bd8, 0x3f000000, 0x3f482e11, 0x3f0c6c49, 0x3f2e571a, 0x3f19999a,
    0x3f0ceb7e, 0x3f3b52ab, 0x3ec36db5, 0x3f333333, 0x3edaa90f, 0x3ed5ac8b, 0x3f178a96, 0x3f4ccccd,
    0x3e6effd7, 0x3f1e0059, 0x3f527af3, 0x3ecccccd,
}};
inline constexpr std::array<std::uint8_t, 252> kCase5RgbaBytes{{
    109U, 176U, 174U, 128U, 78U, 183U, 81U, 153U, 176U, 196U, 139U, 178U, 143U, 130U, 181U, 204U,
    113U, 177U, 104U, 102U, 227U, 170U, 172U, 128U, 167U, 190U, 94U, 153U, 134U, 104U, 177U, 178U,
    90U, 163U, 207U, 204U, 177U, 120U, 178U, 153U, 139U, 122U, 68U, 178U, 103U, 142U, 160U, 204U,
    214U, 149U, 64U, 102U, 146U, 66U, 119U, 128U, 160U, 127U, 173U, 153U, 92U, 134U, 78U, 178U,
    210U, 136U, 149U, 204U, 155U, 94U, 99U, 102U, 90U, 166U, 210U, 178U, 194U, 208U, 104U, 204U,
    159U, 112U, 169U, 102U, 143U, 146U, 70U, 128U, 74U, 129U, 153U, 153U, 216U, 192U, 54U, 178U,
    147U, 102U, 112U, 204U, 116U, 141U, 158U, 102U, 71U, 180U, 130U, 128U, 178U, 150U, 105U, 204U,
    140U, 150U, 118U, 102U, 75U, 175U, 185U, 128U, 216U, 81U, 85U, 153U, 147U, 118U, 169U, 178U,
    131U, 128U, 69U, 204U, 64U, 166U, 154U, 102U, 213U, 84U, 56U, 128U, 159U, 139U, 139U, 153U,
    85U, 113U, 110U, 102U, 210U, 121U, 158U, 128U, 147U, 112U, 72U, 153U, 131U, 147U, 128U, 178U,
    62U, 54U, 185U, 204U, 205U, 118U, 85U, 102U, 136U, 130U, 169U, 128U, 107U, 164U, 99U, 153U,
    60U, 215U, 173U, 178U, 157U, 171U, 116U, 128U, 145U, 209U, 195U, 153U, 81U, 118U, 87U, 178U,
    192U, 126U, 168U, 204U, 124U, 133U, 71U, 102U, 137U, 193U, 126U, 128U, 68U, 111U, 181U, 153U,
    188U, 118U, 103U, 178U, 138U, 158U, 204U, 204U, 78U, 141U, 148U, 153U, 202U, 151U, 231U, 178U,
    147U, 193U, 114U, 204U, 139U, 121U, 210U, 102U, 78U, 142U, 103U, 128U, 199U, 140U, 174U, 153U,
    140U, 187U, 97U, 178U, 109U, 106U, 151U, 204U, 60U, 157U, 210U, 102U,
}};
inline constexpr std::array<std::uint32_t, 63> kCase5OutputAlphaFloatWords{{
    0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333,
    0x3f4ccccd, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333,
    0x3f4ccccd, 0x3ecccccd, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333,
    0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333,
    0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333,
    0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f000000, 0x3f19999a, 0x3f333333,
    0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3f19999a, 0x3f333333,
    0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd,
}};
inline constexpr std::array<std::uint8_t, 63> kCase5OutputAlphaRgbaBytes{{
    128U, 153U, 178U, 204U, 102U, 128U, 153U, 178U, 204U, 153U, 178U, 204U, 102U, 128U, 153U, 178U,
    204U, 102U, 178U, 204U, 102U, 128U, 153U, 178U, 204U, 102U, 128U, 204U, 102U, 128U, 153U, 178U,
    204U, 102U, 128U, 153U, 102U, 128U, 153U, 178U, 204U, 102U, 128U, 153U, 178U, 128U, 153U, 178U,
    204U, 102U, 128U, 153U, 178U, 204U, 153U, 178U, 204U, 102U, 128U, 153U, 178U, 204U, 102U,
}};

inline constexpr std::array<std::uint32_t, 168> kCase6InputFloatWords{{
    0x3ea2e8ba, 0x3f000000, 0x3f333333, 0x3f19999a, 0x3d3a2e8c, 0x3f400000, 0x3dcccccd, 0x3f333333,
    0x3f51745d, 0x3f800000, 0x3f088889, 0x3f4ccccd, 0x3f0ba2e9, 0x3e5b6db7, 0x3f777777, 0x3ecccccd,
    0x3e8ba2e9, 0x3eedb6db, 0x3ebbbbbc, 0x3f000000, 0x00000000, 0x3f36db6e, 0x3f4ccccd, 0x3f19999a,
    0x3f45d174, 0x3f76db6e, 0x3e4ccccd, 0x3f333333, 0x3f51745d, 0x3e124925, 0x3f5dddde, 0x3f333333,
    0x3f0ba2e9, 0x3ec92492, 0x3e888889, 0x3f4ccccd, 0x3e8ba2e9, 0x3f249249, 0x3f333333, 0x3ecccccd,
    0x00000000, 0x3f649249, 0x3dcccccd, 0x3f000000, 0x3f45d174, 0x3ddb6db7, 0x3f088889, 0x3f19999a,
    0x3f000000, 0x3eb6db6e, 0x3f777777, 0x3f333333, 0x3e68ba2f, 0x3f1b6db7, 0x3ebbbbbc, 0x3f4ccccd,
    0x3e8ba2e9, 0x3f524925, 0x00000000, 0x3f4ccccd, 0x00000000, 0x3d124925, 0x3eddddde, 0x3ecccccd,
    0x3f45d174, 0x3e924925, 0x3f5dddde, 0x3f000000, 0x3f000000, 0x3f092492, 0x3e888889, 0x3f19999a,
    0x3e68ba2f, 0x3f492492, 0x3f333333, 0x3f333333, 0x3f800000, 0x00000000, 0x3dcccccd, 0x3f4ccccd,
    0x3f3a2e8c, 0x3e800000, 0x3f088889, 0x3ecccccd, 0x3f45d174, 0x3eedb6db, 0x3e2aaaab, 0x3ecccccd,
    0x3f000000, 0x3f36db6e, 0x3f19999a, 0x3f000000, 0x3e68ba2f, 0x3f76db6e, 0x00000000, 0x3f19999a,
    0x3f800000, 0x3e36db6e, 0x3eddddde, 0x3f333333, 0x3f3a2e8c, 0x3edb6db7, 0x3f5dddde, 0x3f4ccccd,
    0x3ee8ba2f, 0x3f2db6db, 0x3e888889, 0x3ecccccd, 0x3e3a2e8c, 0x3f6db6db, 0x3f333333, 0x3f000000,
    0x3e68ba2f, 0x3ddb6db7, 0x3eaaaaab, 0x3f000000, 0x3f800000, 0x3eb6db6e, 0x3f444444, 0x3f19999a,
    0x3f3a2e8c, 0x3f1b6db7, 0x3e2aaaab, 0x3f333333, 0x3ee8ba2f, 0x3f5b6db7, 0x3f19999a, 0x3f4ccccd,
    0x3e3a2e8c, 0x3d924925, 0x00000000, 0x3ecccccd, 0x3f745d17, 0x3ea49249, 0x3eddddde, 0x3f000000,
    0x3f2e8ba3, 0x3f124925, 0x3f5dddde, 0x3f19999a, 0x3f3a2e8c, 0x3f492492, 0x3f000000, 0x3f19999a,
    0x3ee8ba2f, 0x00000000, 0x3f6eeeef, 0x3f333333, 0x3e3a2e8c, 0x3e800000, 0x3eaaaaab, 0x3f4ccccd,
    0x3f745d17, 0x3f000000, 0x3f444444, 0x3ecccccd, 0x3f2e8ba3, 0x3f400000, 0x3e2aaaab, 0x3f000000,
    0x3ed1745d, 0x3f800000, 0x3f19999a, 0x3f19999a, 0x3e0ba2e9, 0x3e5b6db7, 0x00000000, 0x3f333333,
}};
inline constexpr std::array<std::uint8_t, 168> kCase6InputRgbaBytes{{
    81U, 128U, 178U, 153U, 12U, 191U, 26U, 178U, 209U, 255U, 136U, 204U, 139U, 55U, 246U, 102U,
    70U, 118U, 94U, 128U, 0U, 182U, 204U, 153U, 197U, 246U, 51U, 178U, 209U, 36U, 221U, 178U,
    139U, 100U, 68U, 204U, 70U, 164U, 178U, 102U, 0U, 228U, 26U, 128U, 197U, 27U, 136U, 153U,
    128U, 91U, 246U, 178U, 58U, 155U, 94U, 204U, 70U, 209U, 0U, 204U, 0U, 9U, 111U, 102U,
    197U, 73U, 221U, 128U, 128U, 137U, 68U, 153U, 58U, 200U, 178U, 178U, 255U, 0U, 26U, 204U,
    185U, 64U, 136U, 102U, 197U, 118U, 43U, 102U, 128U, 182U, 153U, 128U, 58U, 246U, 0U, 153U,
    255U, 46U, 111U, 178U, 185U, 109U, 221U, 204U, 116U, 173U, 68U, 102U, 46U, 237U, 178U, 128U,
    58U, 27U, 85U, 128U, 255U, 91U, 195U, 153U, 185U, 155U, 43U, 178U, 116U, 219U, 153U, 204U,
    46U, 18U, 0U, 102U, 243U, 82U, 111U, 128U, 174U, 146U, 221U, 153U, 185U, 200U, 128U, 153U,
    116U, 0U, 238U, 178U, 46U, 64U, 85U, 204U, 243U, 128U, 195U, 102U, 174U, 191U, 43U, 128U,
    104U, 255U, 153U, 153U, 35U, 55U, 0U, 178U,
}};

inline constexpr std::array<std::uint32_t, 168> kCase6FloatWords{{
    0x3ee79a98, 0x3f2422d4, 0x3f37d5ac, 0x3f19999a, 0x3e2e8c52, 0x3f337172, 0x3eb9a55b, 0x3f333333,
    0x3f4739cc, 0x3f68570b, 0x3f2219e6, 0x3f4ccccd, 0x3f0cfa29, 0x3ece67ef, 0x3f616451, 0x3ecccccd,
    0x3ecccba8, 0x3f1fa4d7, 0x3ef5dd44, 0x3f000000, 0x3e88cfb6, 0x3f36a384, 0x3f473f84, 0x3f19999a,
    0x3f48001c, 0x3f684266, 0x3eccb404, 0x3f333333, 0x3f4a55b8, 0x3ec02566, 0x3f57471b, 0x3f333333,
    0x3f02ea6a, 0x3eea92da, 0x3ea84529, 0x3f4ccccd, 0x3eb9f4c5, 0x3f213838, 0x3f292aa7, 0x3ecccccd,
    0x3e19c925, 0x3f4452ab, 0x3e7165d1, 0x3f000000, 0x3f311322, 0x3e5da031, 0x3f0d1c36, 0x3f19999a,
    0x3ee1df14, 0x3ee9affe, 0x3f5830a8, 0x3f333333, 0x3ed2b6b9, 0x3f32366b, 0x3f062892, 0x3f4ccccd,
    0x3ed32d2d, 0x3f45a451, 0x3e9c2c0c, 0x3f4ccccd, 0x3dec11cb, 0x3e3b4737, 0x3ed8f8b8, 0x3ecccccd,
    0x3f37c2f2, 0x3ecb1266, 0x3f41fe0d, 0x3f000000, 0x3f00053f, 0x3ef65731, 0x3ea49037, 0x3f19999a,
    0x3e913065, 0x3f2d42a3, 0x3f256395, 0x3f333333, 0x3f676b0e, 0x3e04a56e, 0x3e5b3c55, 0x3f4ccccd,
    0x3f3e83ca, 0x3ef44203, 0x3f23c36f, 0x3ecccccd, 0x3f47226d, 0x3f164a2b, 0x3ec02a85, 0x3ecccccd,
    0x3f0d3ab1, 0x3f20e244, 0x3f158909, 0x3f000000, 0x3e9130e7, 0x3f5adf85, 0x3de4d4ee, 0x3f19999a,
    0x3f63bb1d, 0x3e938f65, 0x3eddf50b, 0x3f333333, 0x3f2c260b, 0x3ef826df, 0x3f42044b, 0x3f4ccccd,
    0x3ef658e6, 0x3f2d6bfc, 0x3ec4115d, 0x3ecccccd, 0x3e99d59a, 0x3f5c22f9, 0x3f33e1f5, 0x3f000000,
    0x3eb79391, 0x3ea5b179, 0x3ee603f9, 0x3f000000, 0x3f59489c, 0x3eb3ceb6, 0x3f3c4832, 0x3f19999a,
    0x3f263b2f, 0x3f068bd1, 0x3e6ecbed, 0x3f333333, 0x3f0bca69, 0x3f451a07, 0x3f19f28b, 0x3f4ccccd,
    0x3e8db705, 0x3e61e9e3, 0x3dffe5ce, 0x3ecccccd, 0x3f6386de, 0x3ed0dbff, 0x3ef5c0ee, 0x3f000000,
    0x3f2a00b3, 0x3f16887b, 0x3f48c4e1, 0x3f19999a, 0x3f3e21d0, 0x3f47b4eb, 0x3f12ff40, 0x3f19999a,
    0x3f0c430f, 0x3e698ee6, 0x3f658b90, 0x3f333333, 0x3ea2de3d, 0x3ee07554, 0x3edd1acc, 0x3f4ccccd,
    0x3f686f88, 0x3f0e899b, 0x3f492c9d, 0x3ecccccd, 0x3f2d044c, 0x3f39114e, 0x3ebb2b8d, 0x3f000000,
    0x3f03a805, 0x3f6a457c, 0x3f237aa6, 0x3f19999a, 0x3e9a274b, 0x3eda941b, 0x3e7eaab1, 0x3f333333,
}};
inline constexpr std::array<std::uint8_t, 168> kCase6RgbaBytes{{
    115U, 163U, 183U, 153U, 43U, 179U, 92U, 178U, 198U, 231U, 161U, 204U, 140U, 103U, 225U, 102U,
    102U, 159U, 122U, 128U, 68U, 182U, 198U, 153U, 199U, 231U, 102U, 178U, 202U, 96U, 214U, 178U,
    130U, 117U, 84U, 204U, 93U, 161U, 169U, 102U, 38U, 196U, 60U, 128U, 176U, 55U, 141U, 153U,
    112U, 116U, 215U, 178U, 105U, 178U, 134U, 204U, 105U, 197U, 78U, 204U, 29U, 47U, 108U, 102U,
    183U, 101U, 193U, 128U, 128U, 123U, 82U, 153U, 72U, 173U, 165U, 178U, 231U, 33U, 55U, 204U,
    190U, 122U, 163U, 102U, 198U, 150U, 96U, 102U, 141U, 160U, 149U, 128U, 72U, 218U, 28U, 153U,
    227U, 73U, 111U, 178U, 171U, 124U, 193U, 204U, 123U, 173U, 98U, 102U, 77U, 219U, 179U, 128U,
    91U, 83U, 115U, 128U, 216U, 90U, 188U, 153U, 166U, 134U, 59U, 178U, 139U, 196U, 153U, 204U,
    71U, 56U, 32U, 102U, 227U, 104U, 122U, 128U, 169U, 150U, 200U, 153U, 189U, 199U, 146U, 153U,
    140U, 58U, 229U, 178U, 81U, 112U, 110U, 204U, 232U, 142U, 200U, 102U, 172U, 184U, 93U, 128U,
    131U, 233U, 163U, 153U, 77U, 109U, 63U, 178U,
}};
inline constexpr std::array<std::uint32_t, 42> kCase6OutputAlphaFloatWords{{
    0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f333333,
    0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3f4ccccd, 0x3ecccccd,
    0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a,
    0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd,
    0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000,
    0x3f19999a, 0x3f333333,
}};
inline constexpr std::array<std::uint8_t, 42> kCase6OutputAlphaRgbaBytes{{
    153U, 178U, 204U, 102U, 128U, 153U, 178U, 178U, 204U, 102U, 128U, 153U, 178U, 204U, 204U, 102U,
    128U, 153U, 178U, 204U, 102U, 102U, 128U, 153U, 178U, 204U, 102U, 128U, 128U, 153U, 178U, 204U,
    102U, 128U, 153U, 153U, 178U, 204U, 102U, 128U, 153U, 178U,
}};

inline constexpr std::array<std::uint32_t, 160> kCase7InputFloatWords{{
    0x3eba2e8c, 0x3f124925, 0x3f4ccccd, 0x3f333333, 0x3dba2e8c, 0x3f524925, 0x3e4ccccd, 0x3f4ccccd,
    0x3f5d1746, 0x3d124925, 0x3f222222, 0x3ecccccd, 0x3f1745d1, 0x3e924925, 0x3d088889, 0x3f000000,
    0x3ea2e8ba, 0x3f092492, 0x3eeeeeef, 0x3f19999a, 0x3d3a2e8c, 0x3f492492, 0x3f666666, 0x3f333333,
    0x3f51745d, 0x00000000, 0x3e99999a, 0x3f4ccccd, 0x3f0ba2e9, 0x3e800000, 0x3f3bbbbc, 0x3ecccccd,
    0x3f5d1746, 0x3e5b6db7, 0x3f777777, 0x3f4ccccd, 0x3f1745d1, 0x3eedb6db, 0x3ebbbbbc, 0x3ecccccd,
    0x3ea2e8ba, 0x3f36db6e, 0x3f4ccccd, 0x3f000000, 0x3d3a2e8c, 0x3f76db6e, 0x3e4ccccd, 0x3f19999a,
    0x3f51745d, 0x3e36db6e, 0x3f222222, 0x3f333333, 0x3f0ba2e9, 0x3edb6db7, 0x3d088889, 0x3f4ccccd,
    0x3e8ba2e9, 0x3f2db6db, 0x3eeeeeef, 0x3ecccccd, 0x00000000, 0x3f6db6db, 0x3f666666, 0x3f000000,
    0x3ea2e8ba, 0x3f649249, 0x3dcccccd, 0x3ecccccd, 0x3d3a2e8c, 0x3ddb6db7, 0x3f088889, 0x3f000000,
    0x3f51745d, 0x3eb6db6e, 0x3f777777, 0x3f19999a, 0x3f0ba2e9, 0x3f1b6db7, 0x3ebbbbbc, 0x3f333333,
    0x3e8ba2e9, 0x3f5b6db7, 0x3f4ccccd, 0x3f4ccccd, 0x00000000, 0x3d924925, 0x3e4ccccd, 0x3ecccccd,
    0x3f45d174, 0x3ea49249, 0x3f222222, 0x3f000000, 0x3f000000, 0x3f124925, 0x3d088889, 0x3f19999a,
    0x3f51745d, 0x3f092492, 0x3e888889, 0x3f000000, 0x3f0ba2e9, 0x3f492492, 0x3f333333, 0x3f19999a,
    0x3e8ba2e9, 0x00000000, 0x3dcccccd, 0x3f333333, 0x00000000, 0x3e800000, 0x3f088889, 0x3f4ccccd,
    0x3f45d174, 0x3f000000, 0x3f777777, 0x3ecccccd, 0x3f000000, 0x3f400000, 0x3ebbbbbc, 0x3f000000,
    0x3e68ba2f, 0x3f800000, 0x3f4ccccd, 0x3f19999a, 0x3f800000, 0x3e5b6db7, 0x3e4ccccd, 0x3f333333,
    0x3e8ba2e9, 0x3e36db6e, 0x3eddddde, 0x3f19999a, 0x00000000, 0x3edb6db7, 0x3f5dddde, 0x3f333333,
    0x3f45d174, 0x3f2db6db, 0x3e888889, 0x3f4ccccd, 0x3f000000, 0x3f6db6db, 0x3f333333, 0x3ecccccd,
    0x3e68ba2f, 0x3e124925, 0x3dcccccd, 0x3f000000, 0x3f800000, 0x3ec92492, 0x3f088889, 0x3f19999a,
    0x3f3a2e8c, 0x3f249249, 0x3f777777, 0x3f333333, 0x3ee8ba2f, 0x3f649249, 0x3ebbbbbc, 0x3f4ccccd,
}};
inline constexpr std::array<std::uint8_t, 160> kCase7InputRgbaBytes{{
    93U, 146U, 204U, 178U, 23U, 209U, 51U, 204U, 220U, 9U, 161U, 102U, 151U, 73U, 9U, 128U,
    81U, 137U, 119U, 153U, 12U, 200U, 229U, 178U, 209U, 0U, 77U, 204U, 139U, 64U, 187U, 102U,
    220U, 55U, 246U, 204U, 151U, 118U, 94U, 102U, 81U, 182U, 204U, 128U, 12U, 246U, 51U, 153U,
    209U, 46U, 161U, 178U, 139U, 109U, 9U, 204U, 70U, 173U, 119U, 102U, 0U, 237U, 229U, 128U,
    81U, 228U, 26U, 102U, 12U, 27U, 136U, 128U, 209U, 91U, 246U, 153U, 139U, 155U, 94U, 178U,
    70U, 219U, 204U, 204U, 0U, 18U, 51U, 102U, 197U, 82U, 161U, 128U, 128U, 146U, 9U, 153U,
    209U, 137U, 68U, 128U, 139U, 200U, 178U, 153U, 70U, 0U, 26U, 178U, 0U, 64U, 136U, 204U,
    197U, 128U, 246U, 102U, 128U, 191U, 94U, 128U, 58U, 255U, 204U, 153U, 255U, 55U, 51U, 178U,
    70U, 46U, 111U, 153U, 0U, 109U, 221U, 178U, 197U, 173U, 68U, 204U, 128U, 237U, 178U, 102U,
    58U, 36U, 26U, 128U, 255U, 100U, 136U, 153U, 185U, 164U, 246U, 178U, 116U, 228U, 94U, 204U,
}};

inline constexpr std::array<std::uint32_t, 160> kCase7FloatWords{{
    0x3f0fab09, 0x3f18edf3, 0x3f4b3703, 0x3f333333, 0x3e9c1939, 0x3f3f7543, 0x3ec2b014, 0x3f4ccccd,
    0x3f527913, 0x3e377dae, 0x3f365c1e, 0x3ecccccd, 0x3f17a69a, 0x3ee61052, 0x3e7c5937, 0x3f000000,
    0x3efc3996, 0x3f0b45df, 0x3f0edfc4, 0x3f19999a, 0x3e91b740, 0x3f3342a5, 0x3f4f6c10, 0x3f333333,
    0x3f4d4ccf, 0x3e306ef7, 0x3ef3d405, 0x3f4ccccd, 0x3f221e89, 0x3ed3f66f, 0x3f43dfe3, 0x3ecccccd,
    0x3f545362, 0x3ed38f70, 0x3f68e60e, 0x3f4ccccd, 0x3f107af7, 0x3f08581c, 0x3ede9be0, 0x3ecccccd,
    0x3ed6fa89, 0x3f11499e, 0x3f3fa281, 0x3f000000, 0x3e19bf05, 0x3f50d78a, 0x3e5e26c5, 0x3f19999a,
    0x3f38f97a, 0x3e940aa7, 0x3f258054, 0x3f333333, 0x3ee77f19, 0x3f09188b, 0x3e35f51e, 0x3f4ccccd,
    0x3eb95147, 0x3f25f31b, 0x3f0a3eca, 0x3ecccccd, 0x3eb11285, 0x3f518422, 0x3f5003d1, 0x3f000000,
    0x3f03e103, 0x3f4e9e28, 0x3eb0ba10, 0x3ecccccd, 0x3e14baa4, 0x3e89184a, 0x3f04c746, 0x3f000000,
    0x3f416f61, 0x3ed91ebe, 0x3f571dc0, 0x3f19999a, 0x3ef6828a, 0x3f0b31f8, 0x3ebbc238, 0x3f333333,
    0x3eac75fd, 0x3f3af339, 0x3f3c99b9, 0x3f4ccccd, 0x3e0bccd3, 0x3e4e4457, 0x3e88d40b, 0x3ecccccd,
    0x3f3cfed9, 0x3ec4888c, 0x3f1fe86a, 0x3f000000, 0x3f18fb08, 0x3f1596dd, 0x3e8091b8, 0x3f19999a,
    0x3f4d79e1, 0x3f0702f3, 0x3ef4bb0c, 0x3f000000, 0x3f059a71, 0x3f3346f5, 0x3f2aa4ca, 0x3f19999a,
    0x3ec1a9c2, 0x3e1c34a6, 0x3e6662f7, 0x3f333333, 0x3ddeaa90, 0x3ecddf61, 0x3f06b41e, 0x3f4ccccd,
    0x3f2e3e67, 0x3eebdd41, 0x3f54810d, 0x3ecccccd, 0x3f09f248, 0x3f2565eb, 0x3eb89216, 0x3f000000,
    0x3ec94ad7, 0x3f613333, 0x3f46077a, 0x3f19999a, 0x3f5fed62, 0x3ed18aab, 0x3ec15475, 0x3f333333,
    0x3f000728, 0x3ebfbe54, 0x3f09fab2, 0x3f19999a, 0x3e72283f, 0x3ef64d66, 0x3f54b7a2, 0x3f333333,
    0x3f40fb3e, 0x3f1db371, 0x3edc63a2, 0x3f4ccccd, 0x3f184bb7, 0x3f58fdbd, 0x3f38d748, 0x3ecccccd,
    0x3edd3b64, 0x3e8d305f, 0x3ea8e7f7, 0x3f000000, 0x3f5fed62, 0x3efe66cc, 0x3f16737e, 0x3f19999a,
    0x3f3bc3d7, 0x3f1e68ad, 0x3f5c75ff, 0x3f333333, 0x3f210a98, 0x3f58dd5c, 0x3ef5d87f, 0x3f4ccccd,
}};
inline constexpr std::array<std::uint8_t, 160> kCase7RgbaBytes{{
    143U, 152U, 202U, 178U, 78U, 191U, 97U, 204U, 210U, 46U, 182U, 102U, 151U, 115U, 63U, 128U,
    126U, 139U, 142U, 153U, 73U, 179U, 207U, 178U, 204U, 44U, 121U, 204U, 161U, 106U, 195U, 102U,
    211U, 105U, 232U, 204U, 144U, 136U, 111U, 102U, 107U, 145U, 191U, 128U, 38U, 208U, 55U, 153U,
    184U, 74U, 165U, 178U, 115U, 137U, 45U, 204U, 92U, 165U, 138U, 102U, 88U, 209U, 207U, 128U,
    131U, 206U, 88U, 102U, 37U, 68U, 132U, 128U, 193U, 108U, 214U, 153U, 123U, 139U, 94U, 178U,
    86U, 186U, 188U, 204U, 35U, 51U, 68U, 102U, 188U, 98U, 159U, 128U, 152U, 149U, 64U, 153U,
    205U, 134U, 122U, 128U, 133U, 179U, 170U, 153U, 96U, 39U, 57U, 178U, 28U, 103U, 134U, 204U,
    174U, 117U, 212U, 102U, 137U, 165U, 92U, 128U, 100U, 224U, 197U, 153U, 223U, 104U, 96U, 178U,
    128U, 95U, 137U, 153U, 60U, 123U, 212U, 178U, 192U, 157U, 110U, 204U, 152U, 216U, 184U, 102U,
    110U, 70U, 84U, 128U, 223U, 127U, 150U, 153U, 187U, 158U, 220U, 178U, 160U, 216U, 122U, 204U,
}};
inline constexpr std::array<std::uint32_t, 40> kCase7OutputAlphaFloatWords{{
    0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd,
    0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000,
    0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a,
    0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333,
    0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd,
}};
inline constexpr std::array<std::uint8_t, 40> kCase7OutputAlphaRgbaBytes{{
    178U, 204U, 102U, 128U, 153U, 178U, 204U, 102U, 204U, 102U, 128U, 153U, 178U, 204U, 102U, 128U,
    102U, 128U, 153U, 178U, 204U, 102U, 128U, 153U, 128U, 153U, 178U, 204U, 102U, 128U, 153U, 178U,
    153U, 178U, 204U, 102U, 128U, 153U, 178U, 204U,
}};

inline constexpr std::array<std::uint32_t, 96> kCase8InputFloatWords{{
    0x3ed1745d, 0x3f249249, 0x3f666666, 0x3f4ccccd, 0x3e0ba2e9, 0x3f649249, 0x3e99999a, 0x3ecccccd,
    0x3f68ba2f, 0x3ddb6db7, 0x3f3bbbbc, 0x3f000000, 0x3f22e8ba, 0x3eb6db6e, 0x3e088889, 0x3f19999a,
    0x3eba2e8c, 0x3f1b6db7, 0x3f111111, 0x3f333333, 0x3dba2e8c, 0x3f5b6db7, 0x3f800000, 0x3f4ccccd,
    0x3f68ba2f, 0x3e924925, 0x3d088889, 0x3ecccccd, 0x3f22e8ba, 0x3f092492, 0x3eeeeeef, 0x3f000000,
    0x3eba2e8c, 0x3f492492, 0x3f666666, 0x3f19999a, 0x3dba2e8c, 0x00000000, 0x3e99999a, 0x3f333333,
    0x3f5d1746, 0x3e800000, 0x3f3bbbbc, 0x3f4ccccd, 0x3f1745d1, 0x3f000000, 0x3e088889, 0x3ecccccd,
    0x3eba2e8c, 0x3f76db6e, 0x3e4ccccd, 0x3f000000, 0x3dba2e8c, 0x3e36db6e, 0x3f222222, 0x3f19999a,
    0x3f5d1746, 0x3edb6db7, 0x3d088889, 0x3f333333, 0x3f1745d1, 0x3f2db6db, 0x3eeeeeef, 0x3f4ccccd,
    0x3ea2e8ba, 0x3f6db6db, 0x3f666666, 0x3ecccccd, 0x3d3a2e8c, 0x3e124925, 0x3e99999a, 0x3f000000,
    0x3f5d1746, 0x3f1b6db7, 0x3ebbbbbc, 0x3f19999a, 0x3f1745d1, 0x3f5b6db7, 0x3f4ccccd, 0x3f333333,
    0x3ea2e8ba, 0x3d924925, 0x3e4ccccd, 0x3f4ccccd, 0x3d3a2e8c, 0x3ea49249, 0x3f222222, 0x3ecccccd,
    0x3f51745d, 0x3f124925, 0x3d088889, 0x3f000000, 0x3f0ba2e9, 0x3f524925, 0x3eeeeeef, 0x3f19999a,
}};
inline constexpr std::array<std::uint8_t, 96> kCase8InputRgbaBytes{{
    104U, 164U, 229U, 204U, 35U, 228U, 77U, 102U, 232U, 27U, 187U, 128U, 162U, 91U, 34U, 153U,
    93U, 155U, 144U, 178U, 23U, 219U, 255U, 204U, 232U, 73U, 9U, 102U, 162U, 137U, 119U, 128U,
    93U, 200U, 229U, 153U, 23U, 0U, 77U, 178U, 220U, 64U, 187U, 204U, 151U, 128U, 34U, 102U,
    93U, 246U, 51U, 128U, 23U, 46U, 161U, 153U, 220U, 109U, 9U, 178U, 151U, 173U, 119U, 204U,
    81U, 237U, 229U, 102U, 12U, 36U, 77U, 128U, 220U, 155U, 94U, 153U, 151U, 219U, 204U, 178U,
    81U, 18U, 51U, 204U, 12U, 82U, 161U, 102U, 209U, 146U, 9U, 128U, 139U, 209U, 119U, 153U,
}};

inline constexpr std::array<std::uint32_t, 96> kCase8FloatWords{{
    0x3efffeed, 0x3f29110b, 0x3f57cb32, 0x3f4ccccd, 0x3e8bff2f, 0x3f4c1232, 0x3ec3167a, 0x3ecccccd,
    0x3f57006c, 0x3e94196c, 0x3f31e69b, 0x3f000000, 0x3f16ee3a, 0x3f03de60, 0x3e877b8a, 0x3f19999a,
    0x3edd080e, 0x3f26728a, 0x3f265a64, 0x3f333333, 0x3e48d1fa, 0x3f48e48d, 0x3f63cccc, 0x3f4ccccd,
    0x3f562f65, 0x3ecc78ba, 0x3e4929e7, 0x3ecccccd, 0x3f188cca, 0x3f0c534e, 0x3ee45af0, 0x3f000000,
    0x3efe765d, 0x3f1ff18c, 0x3f44b159, 0x3f19999a, 0x3e708c66, 0x3e2a7477, 0x3ea681ef, 0x3f333333,
    0x3f46b706, 0x3ec6459e, 0x3f25a513, 0x3f4ccccd, 0x3f084bc2, 0x3f08be80, 0x3e7b4b2d, 0x3ecccccd,
    0x3ee5f186, 0x3f61285a, 0x3e82a32a, 0x3f000000, 0x3e4a6459, 0x3ec386fb, 0x3f150ecb, 0x3f19999a,
    0x3f41d0bd, 0x3eeda6f1, 0x3e329ada, 0x3f333333, 0x3efa2b42, 0x3f105e50, 0x3eeb0d39, 0x3f4ccccd,
    0x3ec5c78e, 0x3f4ab11e, 0x3f36991c, 0x3ecccccd, 0x3e12ddb8, 0x3e95d1f4, 0x3ec26b70, 0x3f000000,
    0x3f544b4a, 0x3f0c897b, 0x3eaa7b87, 0x3f19999a, 0x3f13af2a, 0x3f47b4ee, 0x3f3c1f8a, 0x3f333333,
    0x3ecbdcee, 0x3e4c8a48, 0x3e80969e, 0x3f4ccccd, 0x3e01cd65, 0x3ec04276, 0x3f1c5c27, 0x3ecccccd,
    0x3f44b1d9, 0x3f089402, 0x3e02eb26, 0x3f000000, 0x3f044aa4, 0x3f43be4f, 0x3ee9d1d1, 0x3f19999a,
}};
inline constexpr std::array<std::uint8_t, 96> kCase8RgbaBytes{{
    127U, 168U, 215U, 204U, 70U, 203U, 97U, 102U, 214U, 74U, 177U, 128U, 150U, 131U, 67U, 153U,
    110U, 166U, 166U, 178U, 50U, 200U, 227U, 204U, 213U, 102U, 50U, 102U, 152U, 140U, 114U, 128U,
    127U, 159U, 196U, 153U, 60U, 42U, 83U, 178U, 198U, 99U, 165U, 204U, 136U, 136U, 63U, 102U,
    115U, 224U, 65U, 128U, 50U, 97U, 148U, 153U, 193U, 118U, 44U, 178U, 125U, 144U, 117U, 204U,
    99U, 202U, 182U, 102U, 37U, 75U, 97U, 128U, 211U, 140U, 85U, 153U, 147U, 199U, 187U, 178U,
    102U, 51U, 64U, 204U, 32U, 96U, 156U, 102U, 196U, 136U, 33U, 128U, 132U, 195U, 116U, 153U,
}};
inline constexpr std::array<std::uint32_t, 24> kCase8OutputAlphaFloatWords{{
    0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000,
    0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd,
    0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a,
}};
inline constexpr std::array<std::uint8_t, 24> kCase8OutputAlphaRgbaBytes{{
    204U, 102U, 128U, 153U, 178U, 204U, 102U, 128U, 153U, 178U, 204U, 102U, 128U, 153U, 178U, 204U,
    102U, 128U, 153U, 178U, 204U, 102U, 128U, 153U,
}};

inline constexpr std::array<std::uint32_t, 128> kCase9InputFloatWords{{
    0x3ee8ba2f, 0x3f36db6e, 0x3f800000, 0x3ecccccd, 0x3e3a2e8c, 0x3f76db6e, 0x3ecccccd, 0x3f000000,
    0x3f745d17, 0x3e36db6e, 0x3f555555, 0x3f19999a, 0x3f2e8ba3, 0x3edb6db7, 0x3e6eeeef, 0x3f333333,
    0x3f745d17, 0x3eb6db6e, 0x3e088889, 0x3f000000, 0x3f2e8ba3, 0x3f1b6db7, 0x3f111111, 0x3f19999a,
    0x3ed1745d, 0x3f5b6db7, 0x3f800000, 0x3f333333, 0x3e0ba2e9, 0x3d924925, 0x3ecccccd, 0x3f4ccccd,
    0x3ed1745d, 0x00000000, 0x3e99999a, 0x3f19999a, 0x3e0ba2e9, 0x3e800000, 0x3f3bbbbc, 0x3f333333,
    0x3f68ba2f, 0x3f000000, 0x3e088889, 0x3f4ccccd, 0x3f22e8ba, 0x3f400000, 0x3f111111, 0x3ecccccd,
    0x3f68ba2f, 0x3f2db6db, 0x3eeeeeef, 0x3f333333, 0x3f22e8ba, 0x3f6db6db, 0x3f666666, 0x3f4ccccd,
    0x3eba2e8c, 0x3e124925, 0x3e99999a, 0x3ecccccd, 0x3dba2e8c, 0x3ec92492, 0x3f3bbbbc, 0x3f000000,
    0x3eba2e8c, 0x3ea49249, 0x3f222222, 0x3f4ccccd, 0x3dba2e8c, 0x3f124925, 0x3d088889, 0x3ecccccd,
    0x3f5d1746, 0x3f524925, 0x3eeeeeef, 0x3f000000, 0x3f1745d1, 0x3d124925, 0x3f666666, 0x3f19999a,
    0x3f5d1746, 0x3f800000, 0x3f4ccccd, 0x3ecccccd, 0x3f1745d1, 0x3e5b6db7, 0x3e4ccccd, 0x3f000000,
    0x3ea2e8ba, 0x3eedb6db, 0x3f222222, 0x3f19999a, 0x3d3a2e8c, 0x3f36db6e, 0x3d088889, 0x3f333333,
    0x3ea2e8ba, 0x3f249249, 0x3f777777, 0x3f000000, 0x3d3a2e8c, 0x3f649249, 0x3ebbbbbc, 0x3f19999a,
    0x3f51745d, 0x3ddb6db7, 0x3f4ccccd, 0x3f333333, 0x3f0ba2e9, 0x3eb6db6e, 0x3e4ccccd, 0x3f4ccccd,
    0x3f51745d, 0x3e924925, 0x3dcccccd, 0x3f19999a, 0x3f0ba2e9, 0x3f092492, 0x3f088889, 0x3f333333,
    0x3e8ba2e9, 0x3f492492, 0x3f777777, 0x3f4ccccd, 0x00000000, 0x00000000, 0x3ebbbbbc, 0x3ecccccd,
}};
inline constexpr std::array<std::uint8_t, 128> kCase9InputRgbaBytes{{
    116U, 182U, 255U, 102U, 46U, 246U, 102U, 128U, 243U, 46U, 212U, 153U, 174U, 109U, 60U, 178U,
    243U, 91U, 34U, 128U, 174U, 155U, 144U, 153U, 104U, 219U, 255U, 178U, 35U, 18U, 102U, 204U,
    104U, 0U, 77U, 153U, 35U, 64U, 187U, 178U, 232U, 128U, 34U, 204U, 162U, 191U, 144U, 102U,
    232U, 173U, 119U, 178U, 162U, 237U, 229U, 204U, 93U, 36U, 77U, 102U, 23U, 100U, 187U, 128U,
    93U, 82U, 161U, 204U, 23U, 146U, 9U, 102U, 220U, 209U, 119U, 128U, 151U, 9U, 229U, 153U,
    220U, 255U, 204U, 102U, 151U, 55U, 51U, 128U, 81U, 118U, 161U, 153U, 12U, 182U, 9U, 178U,
    81U, 164U, 246U, 128U, 12U, 228U, 94U, 153U, 209U, 27U, 204U, 178U, 139U, 91U, 51U, 204U,
    209U, 73U, 26U, 153U, 139U, 137U, 136U, 178U, 70U, 200U, 246U, 204U, 0U, 0U, 94U, 102U,
}};

inline constexpr std::array<std::uint32_t, 128> kCase9FloatWords{{
    0x3ef608e8, 0x3f2dcc9d, 0x3f779c55, 0x3ecccccd, 0x3e9058d4, 0x3f68ef33, 0x3f11b94a, 0x3f000000,
    0x3f6d7c05, 0x3e8c8666, 0x3f5455e8, 0x3f19999a, 0x3f2a97c8, 0x3ef86883, 0x3eca6f47, 0x3f333333,
    0x3f69e75a, 0x3ed4e3da, 0x3e95ac2e, 0x3f000000, 0x3f288054, 0x3f1c18ca, 0x3f139f26, 0x3f19999a,
    0x3ee76f55, 0x3f421fd1, 0x3f6969d0, 0x3f333333, 0x3e3bd0b2, 0x3e0d7a35, 0x3ef12493, 0x3f4ccccd,
    0x3ee8a157, 0x3dbac8dd, 0x3ed798cf, 0x3f19999a, 0x3e2c20a9, 0x3e99b75b, 0x3f2c7603, 0x3f333333,
    0x3f6150dd, 0x3efbb767, 0x3e4ec629, 0x3f4ccccd, 0x3f223b63, 0x3f33426d, 0x3f20ad16, 0x3ecccccd,
    0x3f647fe7, 0x3f2b4994, 0x3f07144f, 0x3f333333, 0x3f2052b9, 0x3f5c1737, 0x3f56a113, 0x3f4ccccd,
    0x3ebfa55d, 0x3e592dbc, 0x3eb9c793, 0x3ecccccd, 0x3e281d2c, 0x3eda0463, 0x3f3a4d59, 0x3f000000,
    0x3ec6a6c6, 0x3eb5cdd5, 0x3f292313, 0x3f4ccccd, 0x3df710d7, 0x3f0ab9c1, 0x3e0479a5, 0x3ecccccd,
    0x3f55a016, 0x3f3bd3a1, 0x3efae31f, 0x3f000000, 0x3f18b23e, 0x3decf842, 0x3f56b8e3, 0x3f19999a,
    0x3f581cdb, 0x3f70c9e0, 0x3f460c39, 0x3ecccccd, 0x3f14dcb9, 0x3e9b3aa0, 0x3e858beb, 0x3f000000,
    0x3ea98d15, 0x3efe2ec2, 0x3f1e9a0a, 0x3f19999a, 0x3dfd67ab, 0x3f298fbc, 0x3e3ace3b, 0x3f333333,
    0x3eba356f, 0x3f1ae479, 0x3f6b163d, 0x3f000000, 0x3df0772d, 0x3f56dd60, 0x3ed4a036, 0x3f19999a,
    0x3f468906, 0x3e62625c, 0x3f49c805, 0x3f333333, 0x3f093d7e, 0x3ebb5099, 0x3ea84a3c, 0x3f4ccccd,
    0x3f4d602b, 0x3eb95f3c, 0x3ea88a86, 0x3f19999a, 0x3f10f0fd, 0x3f0367da, 0x3f1709c1, 0x3f333333,
    0x3eb326e9, 0x3f3d32d1, 0x3f680989, 0x3f4ccccd, 0x3e0eb8e1, 0x3db48bbe, 0x3efc8c80, 0x3ecccccd,
}};
inline constexpr std::array<std::uint8_t, 128> kCase9RgbaBytes{{
    123U, 173U, 247U, 102U, 72U, 232U, 145U, 128U, 237U, 70U, 212U, 153U, 170U, 124U, 101U, 178U,
    233U, 106U, 75U, 128U, 168U, 155U, 147U, 153U, 115U, 193U, 233U, 178U, 47U, 35U, 120U, 204U,
    116U, 23U, 107U, 153U, 43U, 77U, 172U, 178U, 224U, 125U, 51U, 204U, 162U, 179U, 160U, 102U,
    228U, 171U, 135U, 178U, 160U, 219U, 214U, 204U, 95U, 54U, 93U, 102U, 42U, 109U, 186U, 128U,
    99U, 91U, 168U, 204U, 31U, 138U, 33U, 102U, 213U, 187U, 125U, 128U, 152U, 30U, 214U, 153U,
    215U, 240U, 197U, 102U, 148U, 77U, 67U, 128U, 84U, 127U, 158U, 153U, 32U, 169U, 47U, 178U,
    93U, 154U, 234U, 128U, 30U, 214U, 106U, 153U, 198U, 56U, 201U, 178U, 137U, 93U, 84U, 204U,
    205U, 92U, 84U, 153U, 144U, 131U, 150U, 178U, 89U, 188U, 231U, 204U, 36U, 22U, 126U, 102U,
}};
inline constexpr std::array<std::uint32_t, 32> kCase9OutputAlphaFloatWords{{
    0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd,
    0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000,
    0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3ecccccd, 0x3f000000, 0x3f19999a, 0x3f333333,
    0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd,
}};
inline constexpr std::array<std::uint8_t, 32> kCase9OutputAlphaRgbaBytes{{
    102U, 128U, 153U, 178U, 128U, 153U, 178U, 204U, 153U, 178U, 204U, 102U, 178U, 204U, 102U, 128U,
    204U, 102U, 128U, 153U, 102U, 128U, 153U, 178U, 128U, 153U, 178U, 204U, 153U, 178U, 204U, 102U,
}};

inline constexpr std::array<std::uint32_t, 60> kCase10InputFloatWords{{
    0x3f000000, 0x3f492492, 0x3d888889, 0x3f000000, 0x3e68ba2f, 0x00000000, 0x3f000000, 0x3f19999a,
    0x3f800000, 0x3e800000, 0x3f6eeeef, 0x3f333333, 0x3f3a2e8c, 0x3f000000, 0x3eaaaaab, 0x3f4ccccd,
    0x3ee8ba2f, 0x3f400000, 0x3f444444, 0x3ecccccd, 0x3f800000, 0x3edb6db7, 0x3e6eeeef, 0x3f19999a,
    0x3f3a2e8c, 0x3f2db6db, 0x3f2aaaab, 0x3f333333, 0x3ee8ba2f, 0x3f6db6db, 0x3d888889, 0x3f4ccccd,
    0x3e3a2e8c, 0x3e124925, 0x3f000000, 0x3ecccccd, 0x3f745d17, 0x3ec92492, 0x3f6eeeef, 0x3f000000,
    0x3ee8ba2f, 0x3d924925, 0x3ecccccd, 0x3f333333, 0x3e3a2e8c, 0x3ea49249, 0x3f555555, 0x3f4ccccd,
    0x3f745d17, 0x3f124925, 0x3e6eeeef, 0x3ecccccd, 0x3f2e8ba3, 0x3f524925, 0x3f2aaaab, 0x3f000000,
    0x3ed1745d, 0x3d124925, 0x3d888889, 0x3f19999a,
}};
inline constexpr std::array<std::uint8_t, 60> kCase10InputRgbaBytes{{
    128U, 200U, 17U, 128U, 58U, 0U, 128U, 153U, 255U, 64U, 238U, 178U, 185U, 128U, 85U, 204U,
    116U, 191U, 195U, 102U, 255U, 109U, 60U, 153U, 185U, 173U, 170U, 178U, 116U, 237U, 17U, 204U,
    46U, 36U, 128U, 102U, 243U, 100U, 238U, 128U, 116U, 18U, 102U, 178U, 46U, 82U, 212U, 204U,
    243U, 146U, 60U, 102U, 174U, 209U, 170U, 128U, 104U, 9U, 17U, 153U,
}};

inline constexpr std::array<std::uint32_t, 60> kCase10FloatWords{{
    0x3f35eb40, 0x3f3ebcf6, 0x3ed4243a, 0x3f000000, 0x3efae89c, 0x3eef153e, 0x3f260fcd, 0x3f19999a,
    0x3f66c737, 0x3f1e662c, 0x3f4ce048, 0x3f333333, 0x3f3e6719, 0x3f2bd2ba, 0x3f15c281, 0x3f4ccccd,
    0x3f302ba9, 0x3f39e89a, 0x3f47835c, 0x3ecccccd, 0x3f5b37db, 0x3f35db41, 0x3f07f1dc, 0x3f19999a,
    0x3f2f50e5, 0x3f272de8, 0x3f412144, 0x3f333333, 0x3f49c7e2, 0x3f43f7f1, 0x3f172733, 0x3f4ccccd,
    0x3f2a8713, 0x3f0698ac, 0x3f4066b7, 0x3ecccccd, 0x3f54b03b, 0x3f312ef1, 0x3f476568, 0x3f000000,
    0x3f0a8211, 0x3e832fcf, 0x3ec52caa, 0x3f333333, 0x3e99168f, 0x3ebd5f09, 0x3f432787, 0x3f4ccccd,
    0x3f5dcc29, 0x3ef75aa4, 0x3eaa5f85, 0x3ecccccd, 0x3f2649d4, 0x3f3549c2, 0x3f21d5bc, 0x3f000000,
    0x3f2b85d7, 0x3ef87930, 0x3ec8b510, 0x3f19999a,
}};
inline constexpr std::array<std::uint8_t, 60> kCase10RgbaBytes{{
    181U, 190U, 106U, 128U, 125U, 119U, 165U, 153U, 230U, 158U, 204U, 178U, 190U, 171U, 149U, 204U,
    175U, 185U, 199U, 102U, 218U, 181U, 135U, 153U, 175U, 167U, 192U, 178U, 201U, 195U, 151U, 204U,
    170U, 134U, 192U, 102U, 212U, 176U, 199U, 128U, 138U, 65U, 98U, 178U, 76U, 94U, 194U, 204U,
    221U, 123U, 85U, 102U, 166U, 181U, 161U, 128U, 171U, 124U, 100U, 153U,
}};
inline constexpr std::array<std::uint32_t, 15> kCase10OutputAlphaFloatWords{{
    0x3f000000, 0x3f19999a, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f19999a, 0x3f333333, 0x3f4ccccd,
    0x3ecccccd, 0x3f000000, 0x3f333333, 0x3f4ccccd, 0x3ecccccd, 0x3f000000, 0x3f19999a,
}};
inline constexpr std::array<std::uint8_t, 15> kCase10OutputAlphaRgbaBytes{{
    128U, 153U, 178U, 204U, 102U, 153U, 178U, 204U, 102U, 128U, 178U, 204U, 102U, 128U, 153U,
}};

struct CaseView {
  std::string_view name; std::size_t width; std::size_t height;
  std::size_t input_phase;
  std::string_view input_f32_sha256; std::string_view input_rgba8_sha256;
  std::span<const std::uint32_t> input_float_words; std::span<const std::uint8_t> input_rgba8_bytes;
  std::string_view f32_sha256; std::string_view rgba8_sha256;
  std::span<const std::uint32_t> float_words; std::span<const std::uint8_t> rgba8_bytes;
  ScalarControl alpha; Vec3Control color; ScalarControl speed; std::int32_t seed; ScalarControl time;
  Vec2Control resolution; Vec2Control tileOffset; Vec2Control fullResolution;
  std::span<const std::uint32_t> output_alpha_f32_words; std::span<const std::uint8_t> output_alpha_rgba8_bytes;
};

inline constexpr std::array<CaseView, 11> kCases{{
  CaseView{"alpha-zero-corner", 1U, 1U, 1U, "ed039d7f319e8306c6eb4be39a6b724ddc1ad61a8c57dc76f3dd18a485c79dfc", "df73bf99901c6c69913e77b9b56102cca3f42202b040d31e89b5589382d8a6ef", kCase0InputFloatWords, kCase0InputRgbaBytes, "ed039d7f319e8306c6eb4be39a6b724ddc1ad61a8c57dc76f3dd18a485c79dfc", "df73bf99901c6c69913e77b9b56102cca3f42202b040d31e89b5589382d8a6ef", kCase0FloatWords, kCase0RgbaBytes, ScalarControl{0.0f, 0x00000000U}, Vec3Control{{1.0f, 0.800000011920929f, 0.30000001192092896f}, {0x3f800000U, 0x3f4ccccdU, 0x3e99999aU}}, ScalarControl{0.5f, 0x3f000000U}, 1, ScalarControl{0.0f, 0x00000000U}, Vec2Control{{1.0f, 1.0f}, {0x3f800000U, 0x3f800000U}}, Vec2Control{{0.0f, 0.0f}, {0x00000000U, 0x00000000U}}, Vec2Control{{1.0f, 1.0f}, {0x3f800000U, 0x3f800000U}}, kCase0OutputAlphaFloatWords, kCase0OutputAlphaRgbaBytes},
  CaseView{"default-nonsquare", 7U, 5U, 2U, "4fb64a526cbb765bea0884dc46cc4f1bcca8c910061d6cbd2202657221a84a55", "cb85a2832f92c97b078d74998bf2041fb9a6e037cc8ed517cf998d2fd51afbe5", kCase1InputFloatWords, kCase1InputRgbaBytes, "6bff35a173c852fc5d94bb2619b6ea5f6dc7698dd5bec7cfe09cb5b7302d5bff", "35b9d6d6544070c88d4ebde30b156c89ebcb2ab2616eeb5c5bf2635c24fc15fd", kCase1FloatWords, kCase1RgbaBytes, ScalarControl{1.0f, 0x3f800000U}, Vec3Control{{1.0f, 0.800000011920929f, 0.30000001192092896f}, {0x3f800000U, 0x3f4ccccdU, 0x3e99999aU}}, ScalarControl{0.5f, 0x3f000000U}, 1, ScalarControl{0.0f, 0x00000000U}, Vec2Control{{7.0f, 5.0f}, {0x40e00000U, 0x40a00000U}}, Vec2Control{{0.0f, 0.0f}, {0x00000000U, 0x00000000U}}, Vec2Control{{7.0f, 5.0f}, {0x40e00000U, 0x40a00000U}}, kCase1OutputAlphaFloatWords, kCase1OutputAlphaRgbaBytes},
  CaseView{"alpha-half", 8U, 6U, 3U, "e87d32690ffa12186440ebc6db1df5ac51dab928b9c2ef920817350d3f8479c3", "20218ddfabef6ada0db5689ce33bce3afc866595c2354cc6c8f27901e1c142eb", kCase2InputFloatWords, kCase2InputRgbaBytes, "50239ad9fa16b442bc81251b0ad51902a6faade542daf815c36642ba83a08804", "61352e5aa0d2a2237d4c506df926c2de40a1e09d65b03fdf2912dd8a7b83a989", kCase2FloatWords, kCase2RgbaBytes, ScalarControl{0.5f, 0x3f000000U}, Vec3Control{{0.20000000298023224f, 0.699999988079071f, 1.0f}, {0x3e4ccccdU, 0x3f333333U, 0x3f800000U}}, ScalarControl{0.5f, 0x3f000000U}, 7, ScalarControl{0.125f, 0x3e000000U}, Vec2Control{{8.0f, 6.0f}, {0x41000000U, 0x40c00000U}}, Vec2Control{{0.0f, 0.0f}, {0x00000000U, 0x00000000U}}, Vec2Control{{8.0f, 6.0f}, {0x41000000U, 0x40c00000U}}, kCase2OutputAlphaFloatWords, kCase2OutputAlphaRgbaBytes},
  CaseView{"alpha-clamped-high", 5U, 5U, 4U, "09ac63b79d65d9a6c9c99471872a46e4113406ae9614ad521a99bf59d5c23915", "ed7a92f2156c9269f2a88136a2240f2bcdb03933f3746903b5adebfc9167f118", kCase3InputFloatWords, kCase3InputRgbaBytes, "65d5177542142949f07f5e38444a9ec020557ddc90230f4e4e7b927e2a404fe2", "93ed8d704db14a0f363253c738f87e78bf3681ece1de85b127238c62f8922a3e", kCase3FloatWords, kCase3RgbaBytes, ScalarControl{2.0f, 0x40000000U}, Vec3Control{{1.0f, 0.0f, 0.0f}, {0x3f800000U, 0x00000000U, 0x00000000U}}, ScalarControl{1.75f, 0x3fe00000U}, 17, ScalarControl{0.75f, 0x3f400000U}, Vec2Control{{5.0f, 5.0f}, {0x40a00000U, 0x40a00000U}}, Vec2Control{{0.0f, 0.0f}, {0x00000000U, 0x00000000U}}, Vec2Control{{5.0f, 5.0f}, {0x40a00000U, 0x40a00000U}}, kCase3OutputAlphaFloatWords, kCase3OutputAlphaRgbaBytes},
  CaseView{"speed-zero", 6U, 4U, 5U, "cb126b7414aabf466843e761adda99ec1db4546b0e4a520ae7cae5a89e2f6601", "70931400f201335fe4ed446bfd9ef560a8ed8cd425e72b260f3124b55d74f026", kCase4InputFloatWords, kCase4InputRgbaBytes, "01e9a26bbe1da956157359bc3d914890e6ef969d9ae607d94ca139f85d76316f", "31e9f93b440b8f28ee9d825344341b7d46ee8fd2bc6d87c7d0c8e185fa4cbb83", kCase4FloatWords, kCase4RgbaBytes, ScalarControl{0.800000011920929f, 0x3f4ccccdU}, Vec3Control{{0.800000011920929f, 0.20000000298023224f, 0.10000000149011612f}, {0x3f4ccccdU, 0x3e4ccccdU, 0x3dcccccdU}}, ScalarControl{0.0f, 0x00000000U}, 3, ScalarControl{1.25f, 0x3fa00000U}, Vec2Control{{6.0f, 4.0f}, {0x40c00000U, 0x40800000U}}, Vec2Control{{0.0f, 0.0f}, {0x00000000U, 0x00000000U}}, Vec2Control{{6.0f, 4.0f}, {0x40c00000U, 0x40800000U}}, kCase4OutputAlphaFloatWords, kCase4OutputAlphaRgbaBytes},
  CaseView{"speed-high", 9U, 7U, 6U, "da7ad02f0b3d6ae64d07164d824c768bac0ca690a84bbbaeef5e9f813c935406", "2bfeded7b6ab71885c19362a1fa259427178a0381d6f281035fef190d934fdd8", kCase5InputFloatWords, kCase5InputRgbaBytes, "ab7c9a9a97441c4540825a34da8392f5efcf8bc545e93ac2186f630ac9879629", "42cff95df4a84cd3ee600218cf3a8165292c744d17f8d48e0f97e211958420a3", kCase5FloatWords, kCase5RgbaBytes, ScalarControl{0.8999999761581421f, 0x3f666666U}, Vec3Control{{0.10000000149011612f, 0.8999999761581421f, 0.30000001192092896f}, {0x3dcccccdU, 0x3f666666U, 0x3e99999aU}}, ScalarControl{5.0f, 0x40a00000U}, 99, ScalarControl{0.33000001311302185f, 0x3ea8f5c3U}, Vec2Control{{9.0f, 7.0f}, {0x41100000U, 0x40e00000U}}, Vec2Control{{0.0f, 0.0f}, {0x00000000U, 0x00000000U}}, Vec2Control{{9.0f, 7.0f}, {0x41100000U, 0x40e00000U}}, kCase5OutputAlphaFloatWords, kCase5OutputAlphaRgbaBytes},
  CaseView{"seed-axis", 7U, 6U, 7U, "55670a4fa3f91ed31071635be1049e2292722dc2e81b494dd786d2186c2de9fd", "a0de200f556331d66eff21af8186b758c8523c9199d5d40f8a7fe64e7ad51eea", kCase6InputFloatWords, kCase6InputRgbaBytes, "334678f05527a44a00b5f6e28300cfa70307e4057e79b1c27d85acd52792f70d", "a2670fd61be4c3df3feefee69c99dab575cc46cfcff50484159912d9f7dc2b26", kCase6FloatWords, kCase6RgbaBytes, ScalarControl{0.6499999761581421f, 0x3f266666U}, Vec3Control{{0.4000000059604645f, 0.5f, 0.8999999761581421f}, {0x3ecccccdU, 0x3f000000U, 0x3f666666U}}, ScalarControl{1.2000000476837158f, 0x3f99999aU}, 64, ScalarControl{0.625f, 0x3f200000U}, Vec2Control{{7.0f, 6.0f}, {0x40e00000U, 0x40c00000U}}, Vec2Control{{0.0f, 0.0f}, {0x00000000U, 0x00000000U}}, Vec2Control{{7.0f, 6.0f}, {0x40e00000U, 0x40c00000U}}, kCase6OutputAlphaFloatWords, kCase6OutputAlphaRgbaBytes},
  CaseView{"time-negative", 8U, 5U, 8U, "c897bd33e47b014d61ec2fea344e3c6b4b66c61431ab2a1a849cb3f63de38ad5", "922758316b38882708c3742e7408ccd8ee4d9f70e5343cdd3d1465b562cca1db", kCase7InputFloatWords, kCase7InputRgbaBytes, "35cad887c80ce3b1c85155bd39fc12a42fb167b6883903342f9c56db36c815ac", "e3ca807698433e7eb2a71e0c330251400f158fc04cc11d0cf690cd4dfea3f642", kCase7FloatWords, kCase7RgbaBytes, ScalarControl{0.699999988079071f, 0x3f333333U}, Vec3Control{{1.0f, 0.10000000149011612f, 0.6000000238418579f}, {0x3f800000U, 0x3dcccccdU, 0x3f19999aU}}, ScalarControl{2.25f, 0x40100000U}, 12, ScalarControl{-0.4000000059604645f, 0xbecccccdU}, Vec2Control{{8.0f, 5.0f}, {0x41000000U, 0x40a00000U}}, Vec2Control{{0.0f, 0.0f}, {0x00000000U, 0x00000000U}}, Vec2Control{{8.0f, 5.0f}, {0x41000000U, 0x40a00000U}}, kCase7OutputAlphaFloatWords, kCase7OutputAlphaRgbaBytes},
  CaseView{"tiled-full-resolution", 6U, 4U, 9U, "07f0b14d566e8ecbb521301f927e1c993dec028d8b0bc1d064f71cd9b8d45e9b", "8b9afafc15f6d27b9a641f5d5ffa8b9bbccc71b03f5c8a4034066b892e4365f7", kCase8InputFloatWords, kCase8InputRgbaBytes, "72e91e950d96baded0b18977518650868dae24df10d44ee37ea01b36261cd26f", "7b46999074364e0fa67d4151f2cc4e7002db0aa4a629e80bdb77734b36407b2f", kCase8FloatWords, kCase8RgbaBytes, ScalarControl{0.75f, 0x3f400000U}, Vec3Control{{0.8999999761581421f, 0.800000011920929f, 0.10000000149011612f}, {0x3f666666U, 0x3f4ccccdU, 0x3dcccccdU}}, ScalarControl{0.75f, 0x3f400000U}, 23, ScalarControl{0.4399999976158142f, 0x3ee147aeU}, Vec2Control{{6.0f, 4.0f}, {0x40c00000U, 0x40800000U}}, Vec2Control{{7.0f, 11.0f}, {0x40e00000U, 0x41300000U}}, Vec2Control{{19.0f, 17.0f}, {0x41980000U, 0x41880000U}}, kCase8OutputAlphaFloatWords, kCase8OutputAlphaRgbaBytes},
  CaseView{"color-blue", 4U, 8U, 10U, "a28638ac2e81bcbb0a907250a1de044b17a719b808ce093172bc7293475a31e5", "1a2b8bdeb671abe91d743e6a8965f67a31800b162352f0f97fbbbef1a2b833bf", kCase9InputFloatWords, kCase9InputRgbaBytes, "6e36d473b699b0d3ada89c4000913c7aa9396b54347a305e5e96e5de24c0d652", "42a0c75c83a23393e985b297893594d4a3b021a6dbc565708d60d3194f867af9", kCase9FloatWords, kCase9RgbaBytes, ScalarControl{0.550000011920929f, 0x3f0ccccdU}, Vec3Control{{0.0f, 0.10000000149011612f, 1.0f}, {0x00000000U, 0x3dcccccdU, 0x3f800000U}}, ScalarControl{1.5f, 0x3fc00000U}, 5, ScalarControl{0.9100000262260437f, 0x3f68f5c3U}, Vec2Control{{4.0f, 8.0f}, {0x40800000U, 0x41000000U}}, Vec2Control{{0.0f, 0.0f}, {0x00000000U, 0x00000000U}}, Vec2Control{{4.0f, 8.0f}, {0x40800000U, 0x41000000U}}, kCase9OutputAlphaFloatWords, kCase9OutputAlphaRgbaBytes},
  CaseView{"fullresolution-fallback", 5U, 3U, 11U, "4220816a55d7a426a13aa647368de07431c0131f175ae9daf394270e7919d655", "c07a77ed2272e5894801655a02f95c40825a72409854079209a55e3227f82325", kCase10InputFloatWords, kCase10InputRgbaBytes, "e3bb2b0dd471ffab8a2f50b4e306394907e62e849dbcbaaa9e32780f963827b4", "eef16e203d410260366641eb7798613640ed68c7738b34e3bfcf3e24f3628ee7", kCase10FloatWords, kCase10RgbaBytes, ScalarControl{0.8500000238418579f, 0x3f59999aU}, Vec3Control{{0.6000000238418579f, 0.6000000238418579f, 0.6000000238418579f}, {0x3f19999aU, 0x3f19999aU, 0x3f19999aU}}, ScalarControl{1.0f, 0x3f800000U}, 8, ScalarControl{0.20000000298023224f, 0x3e4ccccdU}, Vec2Control{{5.0f, 3.0f}, {0x40a00000U, 0x40400000U}}, Vec2Control{{1.0f, 2.0f}, {0x3f800000U, 0x40000000U}}, Vec2Control{{0.0f, 0.0f}, {0x00000000U, 0x00000000U}}, kCase10OutputAlphaFloatWords, kCase10OutputAlphaRgbaBytes},
}};

struct MutationDivergentRowView { std::string_view case_name; bool required_witness; };
struct MutationResultView { std::string_view case_name; std::size_t mismatched_lanes; std::size_t lane_index; std::array<std::size_t, 2> top_down_xy; std::string_view channel; std::uint32_t reference_bits_le; std::uint32_t candidate_bits_le; };
inline constexpr std::array<std::string_view, 1> kMutation0RequiredWitnesses{{
  "color-blue",
}};
inline constexpr std::array<MutationDivergentRowView, 10> kMutation0DivergentRows{{
  MutationDivergentRowView{"default-nonsquare", false},
  MutationDivergentRowView{"alpha-half", false},
  MutationDivergentRowView{"alpha-clamped-high", false},
  MutationDivergentRowView{"speed-zero", false},
  MutationDivergentRowView{"speed-high", false},
  MutationDivergentRowView{"seed-axis", false},
  MutationDivergentRowView{"time-negative", false},
  MutationDivergentRowView{"tiled-full-resolution", false},
  MutationDivergentRowView{"color-blue", true},
  MutationDivergentRowView{"fullresolution-fallback", false},
}};
inline constexpr std::array<MutationResultView, 1> kMutation0Results{{
  MutationResultView{"color-blue", 92U, 0U, {0U, 0U}, "r", 0x3ef608e8U, 0x3f1883feU},
}};

inline constexpr std::array<std::string_view, 1> kMutation1RequiredWitnesses{{
  "default-nonsquare",
}};
inline constexpr std::array<MutationDivergentRowView, 10> kMutation1DivergentRows{{
  MutationDivergentRowView{"default-nonsquare", true},
  MutationDivergentRowView{"alpha-half", false},
  MutationDivergentRowView{"alpha-clamped-high", false},
  MutationDivergentRowView{"speed-zero", false},
  MutationDivergentRowView{"speed-high", false},
  MutationDivergentRowView{"seed-axis", false},
  MutationDivergentRowView{"time-negative", false},
  MutationDivergentRowView{"tiled-full-resolution", false},
  MutationDivergentRowView{"color-blue", false},
  MutationDivergentRowView{"fullresolution-fallback", false},
}};
inline constexpr std::array<MutationResultView, 1> kMutation1Results{{
  MutationResultView{"default-nonsquare", 97U, 0U, {0U, 0U}, "r", 0x3ec3563cU, 0x3ec3015fU},
}};

inline constexpr std::array<std::string_view, 1> kMutation2RequiredWitnesses{{
  "default-nonsquare",
}};
inline constexpr std::array<MutationDivergentRowView, 10> kMutation2DivergentRows{{
  MutationDivergentRowView{"default-nonsquare", true},
  MutationDivergentRowView{"alpha-half", false},
  MutationDivergentRowView{"alpha-clamped-high", false},
  MutationDivergentRowView{"speed-zero", false},
  MutationDivergentRowView{"speed-high", false},
  MutationDivergentRowView{"seed-axis", false},
  MutationDivergentRowView{"time-negative", false},
  MutationDivergentRowView{"tiled-full-resolution", false},
  MutationDivergentRowView{"color-blue", false},
  MutationDivergentRowView{"fullresolution-fallback", false},
}};
inline constexpr std::array<MutationResultView, 1> kMutation2Results{{
  MutationResultView{"default-nonsquare", 96U, 0U, {0U, 0U}, "r", 0x3ec3563cU, 0x3eb96fcdU},
}};

inline constexpr std::array<std::string_view, 1> kMutation3RequiredWitnesses{{
  "default-nonsquare",
}};
inline constexpr std::array<MutationDivergentRowView, 10> kMutation3DivergentRows{{
  MutationDivergentRowView{"default-nonsquare", true},
  MutationDivergentRowView{"alpha-half", false},
  MutationDivergentRowView{"alpha-clamped-high", false},
  MutationDivergentRowView{"speed-zero", false},
  MutationDivergentRowView{"speed-high", false},
  MutationDivergentRowView{"seed-axis", false},
  MutationDivergentRowView{"time-negative", false},
  MutationDivergentRowView{"tiled-full-resolution", false},
  MutationDivergentRowView{"color-blue", false},
  MutationDivergentRowView{"fullresolution-fallback", false},
}};
inline constexpr std::array<MutationResultView, 1> kMutation3Results{{
  MutationResultView{"default-nonsquare", 96U, 0U, {0U, 0U}, "r", 0x3ec3563cU, 0x3ec941baU},
}};

inline constexpr std::array<std::string_view, 1> kMutation4RequiredWitnesses{{
  "default-nonsquare",
}};
inline constexpr std::array<MutationDivergentRowView, 10> kMutation4DivergentRows{{
  MutationDivergentRowView{"default-nonsquare", true},
  MutationDivergentRowView{"alpha-half", false},
  MutationDivergentRowView{"alpha-clamped-high", false},
  MutationDivergentRowView{"speed-zero", false},
  MutationDivergentRowView{"speed-high", false},
  MutationDivergentRowView{"seed-axis", false},
  MutationDivergentRowView{"time-negative", false},
  MutationDivergentRowView{"tiled-full-resolution", false},
  MutationDivergentRowView{"color-blue", false},
  MutationDivergentRowView{"fullresolution-fallback", false},
}};
inline constexpr std::array<MutationResultView, 1> kMutation4Results{{
  MutationResultView{"default-nonsquare", 36U, 64U, {2U, 2U}, "r", 0x3ed5123fU, 0x3ed5028eU},
}};

inline constexpr std::array<std::string_view, 1> kMutation5RequiredWitnesses{{
  "speed-high",
}};
inline constexpr std::array<MutationDivergentRowView, 10> kMutation5DivergentRows{{
  MutationDivergentRowView{"default-nonsquare", false},
  MutationDivergentRowView{"alpha-half", false},
  MutationDivergentRowView{"alpha-clamped-high", false},
  MutationDivergentRowView{"speed-zero", false},
  MutationDivergentRowView{"speed-high", true},
  MutationDivergentRowView{"seed-axis", false},
  MutationDivergentRowView{"time-negative", false},
  MutationDivergentRowView{"tiled-full-resolution", false},
  MutationDivergentRowView{"color-blue", false},
  MutationDivergentRowView{"fullresolution-fallback", false},
}};
inline constexpr std::array<MutationResultView, 1> kMutation5Results{{
  MutationResultView{"speed-high", 49U, 80U, {2U, 2U}, "r", 0x3f1fb13eU, 0x3f1fb0eeU},
}};

inline constexpr std::array<std::string_view, 1> kMutation6RequiredWitnesses{{
  "alpha-half",
}};
inline constexpr std::array<MutationDivergentRowView, 9> kMutation6DivergentRows{{
  MutationDivergentRowView{"alpha-zero-corner", false},
  MutationDivergentRowView{"alpha-half", true},
  MutationDivergentRowView{"speed-zero", false},
  MutationDivergentRowView{"speed-high", false},
  MutationDivergentRowView{"seed-axis", false},
  MutationDivergentRowView{"time-negative", false},
  MutationDivergentRowView{"tiled-full-resolution", false},
  MutationDivergentRowView{"color-blue", false},
  MutationDivergentRowView{"fullresolution-fallback", false},
}};
inline constexpr std::array<MutationResultView, 1> kMutation6Results{{
  MutationResultView{"alpha-half", 144U, 0U, {0U, 0U}, "r", 0x3e845cafU, 0x3eac9a9cU},
}};

inline constexpr std::array<std::string_view, 1> kMutation7RequiredWitnesses{{
  "speed-high",
}};
inline constexpr std::array<MutationDivergentRowView, 8> kMutation7DivergentRows{{
  MutationDivergentRowView{"alpha-half", false},
  MutationDivergentRowView{"alpha-clamped-high", false},
  MutationDivergentRowView{"speed-zero", false},
  MutationDivergentRowView{"speed-high", true},
  MutationDivergentRowView{"seed-axis", false},
  MutationDivergentRowView{"time-negative", false},
  MutationDivergentRowView{"tiled-full-resolution", false},
  MutationDivergentRowView{"color-blue", false},
}};
inline constexpr std::array<MutationResultView, 1> kMutation7Results{{
  MutationResultView{"speed-high", 175U, 0U, {0U, 0U}, "r", 0x3eda84ebU, 0x3ec98e59U},
}};

inline constexpr std::array<std::string_view, 1> kMutation8RequiredWitnesses{{
  "seed-axis",
}};
inline constexpr std::array<MutationDivergentRowView, 9> kMutation8DivergentRows{{
  MutationDivergentRowView{"alpha-half", false},
  MutationDivergentRowView{"alpha-clamped-high", false},
  MutationDivergentRowView{"speed-zero", false},
  MutationDivergentRowView{"speed-high", false},
  MutationDivergentRowView{"seed-axis", true},
  MutationDivergentRowView{"time-negative", false},
  MutationDivergentRowView{"tiled-full-resolution", false},
  MutationDivergentRowView{"color-blue", false},
  MutationDivergentRowView{"fullresolution-fallback", false},
}};
inline constexpr std::array<MutationResultView, 1> kMutation8Results{{
  MutationResultView{"seed-axis", 121U, 0U, {0U, 0U}, "r", 0x3ee79a98U, 0x3ee48365U},
}};

inline constexpr std::array<std::string_view, 1> kMutation9RequiredWitnesses{{
  "color-blue",
}};
inline constexpr std::array<MutationDivergentRowView, 9> kMutation9DivergentRows{{
  MutationDivergentRowView{"default-nonsquare", false},
  MutationDivergentRowView{"alpha-half", false},
  MutationDivergentRowView{"alpha-clamped-high", false},
  MutationDivergentRowView{"speed-zero", false},
  MutationDivergentRowView{"speed-high", false},
  MutationDivergentRowView{"seed-axis", false},
  MutationDivergentRowView{"time-negative", false},
  MutationDivergentRowView{"tiled-full-resolution", false},
  MutationDivergentRowView{"color-blue", true},
}};
inline constexpr std::array<MutationResultView, 1> kMutation9Results{{
  MutationResultView{"color-blue", 93U, 0U, {0U, 0U}, "r", 0x3ef608e8U, 0x3f0fe9baU},
}};

inline constexpr std::array<std::string_view, 1> kMutation10RequiredWitnesses{{
  "time-negative",
}};
inline constexpr std::array<MutationDivergentRowView, 8> kMutation10DivergentRows{{
  MutationDivergentRowView{"alpha-half", false},
  MutationDivergentRowView{"alpha-clamped-high", false},
  MutationDivergentRowView{"speed-high", false},
  MutationDivergentRowView{"seed-axis", false},
  MutationDivergentRowView{"time-negative", true},
  MutationDivergentRowView{"tiled-full-resolution", false},
  MutationDivergentRowView{"color-blue", false},
  MutationDivergentRowView{"fullresolution-fallback", false},
}};
inline constexpr std::array<MutationResultView, 1> kMutation10Results{{
  MutationResultView{"time-negative", 116U, 0U, {0U, 0U}, "r", 0x3f0fab09U, 0x3f08a9e0U},
}};

struct MutationView { std::string_view name; std::string_view group; std::string_view mechanism; std::string_view source_anchor; std::string_view replacement; std::string_view source_anchor_sha256; std::string_view replacement_sha256; std::string_view mutated_factory_sha256; std::size_t anchor_count; std::span<const std::string_view> required_witnesses; std::span<const MutationDivergentRowView> divergent_rows; std::span<const MutationResultView> required_results; };
inline constexpr std::array<MutationView, 11> kMutations{{
  MutationView{"out-cell-color-materialization", "out-inout materialization", "replace canonical out-cell color owner", "mix(hash33(s), color, 0.6000000238418579)", "mix(hash33(s), new $runtime.PooledFloat32Array([1, 1, 1]), 0.6000000238418579)", "433f04a5bfc4f79b830e6265c9b8906ed3319d93e4f3bba03afaf5db737b7069", "00e70b0adb73bc4c93ff294d545623a634f445d361582df2fac9767096de977e", "a1bc8f2141307b814b54a9879ec5c9299d0ab907abe4b97d5d047874b11dc718", 1U, kMutation0RequiredWitnesses, kMutation0DivergentRows, kMutation0Results},
  MutationView{"out-cell-dist-materialization", "out-inout materialization", "replace canonical out-cell distance owner", "voronoiCell.__out__ = [cell_color, cell_dist];", "voronoiCell.__out__ = [cell_color, cell_dist + 0.01];", "7ee38ff535aacbcd6ec0de1fb103a7fc73b0085fb243a0e1574077055fd567d2", "09581aee41866049af735501539d5b06ff9999c3064e65708e6872d1a53a8883", "f4195b0ac1905567146b18d55f5767d5aa4056290a633dcb79f88d666a3d9294", 1U, kMutation1RequiredWitnesses, kMutation1DivergentRows, kMutation1Results},
  MutationView{"base-bare-call-site", "bare call site", "alter canonical base-cell call arguments", "seed_f, t, base_cell", "seed_f + 1, t, base_cell", "df047d8739f8adff0add7437790becd8447f3f54ff92124bdb42403d6ebffe36", "64ab66080dcaac85435378c32d7f6ab3e6b97452dbc92e218e4853985cab3165", "2bb11f4d347c2e621dc9a05479130d9c943c3b5e6706a984fbc2f03824664bc2", 1U, kMutation2RequiredWitnesses, kMutation2DivergentRows, kMutation2Results},
  MutationView{"warp-bare-call-site", "bare call site", "alter canonical warp-cell call arguments", "seed_f, t, warp_cell", "seed_f + 1, t, warp_cell", "763e97aa4a248be5930ff1368b585d43146360f17b2dcd87d3762528e4d2c779", "951b86e80970a4db5e457ffe3b63536b39c332f6ff9ea7337f4d8002811d97b4", "04d93bcce5c36f9f3e1613fcdbe529f2a1d53d589793c6c0ebb7a9a439034eec", 1U, kMutation3RequiredWitnesses, kMutation3DivergentRows, kMutation3Results},
  MutationView{"source-global-POINT_COUNT", "source global", "alter canonical source global point count", "var POINT_COUNT = 6;", "var POINT_COUNT = 5;", "19f8c9c9bf24f1f51ec34badd04d650ebae0ad2c88579c9c9a951d32869499fc", "66cf45aab4ccdeb316ea9a036c0f2b9c46ddcc716d6ed6f3377c96232d75eda2", "537bb3dd75b09bad1b00b22cbd2569e33a471bb757eef4801f2d583ea636e121", 1U, kMutation4RequiredWitnesses, kMutation4DivergentRows, kMutation4Results},
  MutationView{"loop-bound-POINT_COUNT", "loop bound", "alter canonical loop point-count bound", "i < POINT_COUNT", "i < 5", "d0c105eb94bea46e6c3e4c98272fa2ec904aa9e2ba417875e0a7c69c717e716d", "421d89772125e9af801bdf6c4dedf15f0d9ef7a9e02437459c86da2fc5675694", "2147226a38833360194e3af0d2eaa050ee52d03b55fadfc9e28f0a282c438b63", 1U, kMutation5RequiredWitnesses, kMutation5DivergentRows, kMutation5Results},
  MutationView{"alpha-control-axis", "control axis", "remove canonical alpha control from blend", "var blend_alpha = clamp(alpha, 0, 1);", "var blend_alpha = 1;", "da505e3ea4dde1ad042e106b61b64f96c06262bce9b9a8267d73a798a86e4057", "7ef0f7a9324f9035e97c8ceb63ce971a68fb00a6681f5b08de590ed3ca275540", "fd68715b20b29d8ba7f6c9f7a1e3cb0f8daddf85a45af4811de1177137c91925", 1U, kMutation6RequiredWitnesses, kMutation6DivergentRows, kMutation6Results},
  MutationView{"speed-control-axis", "control axis", "remove canonical speed control from time", "var t = time * speed;", "var t = time;", "c0ad52e48c15c95d9056325acd6f0ea90071b590822d6384925571431939581e", "d3813242ed8e241ddc318846417c6816448ab4cfbafb6a4d378c7c7e1e0ac2d1", "4028d4b05dc6c52b7092af75a207a4df044e3894bcc2f36f7352d49aa94328f1", 1U, kMutation7RequiredWitnesses, kMutation7DivergentRows, kMutation7Results},
  MutationView{"seed-control-axis", "control axis", "remove canonical seed control from hash", "var seed_f = (seed);", "var seed_f = 1;", "fb68f43d90cfeafe7dbcef72ef45a82eff29a45a6992f9ce7052ac7fcf1963c1", "5cf32c41d895de9d5816b3d8c13ed1eb949544b376a9fa6b38d2204f71dca98f", "04ddc63725c5fc53130a7ace86f71e1d3f31f3820676ffe46f1b2be26e630958", 1U, kMutation8RequiredWitnesses, kMutation8DivergentRows, kMutation8Results},
  MutationView{"color-control-axis", "control axis", "alter canonical color control order", "mix(hash33(s), color, 0.6000000238418579)", "mix(hash33(s), new $runtime.PooledFloat32Array([color[2], color[1], color[0]]), 0.6000000238418579)", "433f04a5bfc4f79b830e6265c9b8906ed3319d93e4f3bba03afaf5db737b7069", "9858acba8e30c75db68b26f81cc5c58b919d7ae5a7e5831156a5fb7797510c52", "50a438493d54951e9425cec901978401e8d5e8de5c7273003ee29993f5e07a99", 1U, kMutation9RequiredWitnesses, kMutation9DivergentRows, kMutation9Results},
  MutationView{"time-control-axis", "control axis", "reverse canonical time control", "var t = time * speed;", "var t = -time * speed;", "c0ad52e48c15c95d9056325acd6f0ea90071b590822d6384925571431939581e", "48c346594ace3720177c4e16aa06fc4860bf1a6e2d697c747d8a7b3db3ebc056", "f1453e261a4954544cecb3feef9692de18e37116902cf44812293ead2e7ce3ee", 1U, kMutation10RequiredWitnesses, kMutation10DivergentRows, kMutation10Results},
}};

struct MutationWitnessView { std::string_view mutation; std::string_view case_name; std::size_t mismatched_lanes; std::size_t lane_index; std::array<std::size_t, 2> top_down_xy; std::string_view channel; std::uint32_t reference_bits_le; std::uint32_t candidate_bits_le; };
inline constexpr std::array<MutationWitnessView, 11> kMutationWitnesses{{
  MutationWitnessView{"out-cell-color-materialization", "color-blue", 92U, 0U, {0U, 0U}, "r", 0x3ef608e8U, 0x3f1883feU},
  MutationWitnessView{"out-cell-dist-materialization", "default-nonsquare", 97U, 0U, {0U, 0U}, "r", 0x3ec3563cU, 0x3ec3015fU},
  MutationWitnessView{"base-bare-call-site", "default-nonsquare", 96U, 0U, {0U, 0U}, "r", 0x3ec3563cU, 0x3eb96fcdU},
  MutationWitnessView{"warp-bare-call-site", "default-nonsquare", 96U, 0U, {0U, 0U}, "r", 0x3ec3563cU, 0x3ec941baU},
  MutationWitnessView{"source-global-POINT_COUNT", "default-nonsquare", 36U, 64U, {2U, 2U}, "r", 0x3ed5123fU, 0x3ed5028eU},
  MutationWitnessView{"loop-bound-POINT_COUNT", "speed-high", 49U, 80U, {2U, 2U}, "r", 0x3f1fb13eU, 0x3f1fb0eeU},
  MutationWitnessView{"alpha-control-axis", "alpha-half", 144U, 0U, {0U, 0U}, "r", 0x3e845cafU, 0x3eac9a9cU},
  MutationWitnessView{"speed-control-axis", "speed-high", 175U, 0U, {0U, 0U}, "r", 0x3eda84ebU, 0x3ec98e59U},
  MutationWitnessView{"seed-control-axis", "seed-axis", 121U, 0U, {0U, 0U}, "r", 0x3ee79a98U, 0x3ee48365U},
  MutationWitnessView{"color-control-axis", "color-blue", 93U, 0U, {0U, 0U}, "r", 0x3ef608e8U, 0x3f0fe9baU},
  MutationWitnessView{"time-control-axis", "time-negative", 116U, 0U, {0U, 0U}, "r", 0x3f0fab09U, 0x3f08a9e0U},
}};

struct StructuralMutationView { std::string_view name; std::string_view pixel_expectation; };
inline constexpr std::array<StructuralMutationView, 2> kStructuralMutations{{
  StructuralMutationView{"unused-resolution-axis", "structurally authenticated binding retained; no pixel witness claimed"},
  StructuralMutationView{"globalCoord-dead-value", "structurally authenticated source mutation; no pixel witness claimed"},
}};

static_assert(kBindingAbi.size() == 9U);
static_assert(kCases.size() == kCaseCount);
static_assert(kMutations.size() == 11U);
static_assert(kMutationWitnesses.size() == 11U);
}  // namespace lightleak192_oracle
