// Generated from the authenticated Mandelbrot JSON oracle.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string_view>

namespace mandelbrot_oracle {
inline constexpr std::string_view kProgramKey = "synth/mandelbrot:mandelbrot";
inline constexpr std::string_view kFactoryTextSha256 = "9233a268bfcdf5027a9a794591de9cddc99f09310f1bb5107638fe3ab6424af2";
inline constexpr std::array<std::string_view, 18> kBindingNames{{
  "resolution", "tileOffset", "fullResolution", "time", "poi", "outputMode", "iterations", "centerHiX", "centerHiY", "centerLoX", "centerLoY", "zoomSpeed", "zoomDepth", "invert", "stripeFreq", "trapShape", "lightAngle", "rotation"
}};
struct BindingAbiView { std::string_view name; std::string_view category; };
inline constexpr std::array<BindingAbiView, 18> kBindingAbi{{
  BindingAbiView{"resolution", "Vec2"},
  BindingAbiView{"tileOffset", "Vec2"},
  BindingAbiView{"fullResolution", "Vec2"},
  BindingAbiView{"time", "number"},
  BindingAbiView{"poi", "int32"},
  BindingAbiView{"outputMode", "int32"},
  BindingAbiView{"iterations", "int32"},
  BindingAbiView{"centerHiX", "number"},
  BindingAbiView{"centerHiY", "number"},
  BindingAbiView{"centerLoX", "number"},
  BindingAbiView{"centerLoY", "number"},
  BindingAbiView{"zoomSpeed", "number"},
  BindingAbiView{"zoomDepth", "number"},
  BindingAbiView{"invert", "number"},
  BindingAbiView{"stripeFreq", "number"},
  BindingAbiView{"trapShape", "int32"},
  BindingAbiView{"lightAngle", "number"},
  BindingAbiView{"rotation", "number"},
}};
struct BindingControl { std::array<float,2> resolution; std::array<float,2> tileOffset; std::array<float,2> fullResolution; float time; std::int32_t poi; std::int32_t outputMode; std::int32_t iterations; float centerHiX; float centerHiY; float centerLoX; float centerLoY; float zoomSpeed; float zoomDepth; float invert; float stripeFreq; std::int32_t trapShape; float lightAngle; float rotation; };
inline constexpr BindingControl kCase0Bindings{{5.0F, 4.0F}, {0.0F, 0.0F}, {5.0F, 4.0F}, 0.25F, 0, 0, 80, -0.75F, 0.0F, 0.0F, 0.0F, 0.0F, 1.0F, 0.0F, 0.0F, 0, 30.0F, 0.0F};
inline constexpr std::array<std::uint32_t, 80> kCase0InputWords{{
  0x3d800000U, 0x3d638e39U, 0x3d3a2e8cU, 0x3f800000U, 0x3e800000U, 0x3ee38e39U, 0x3f0ba2e9U, 0x3f800000U, 0x3ee00000U, 0x3f555555U, 0x00000000U, 0x3f800000U, 0x3f200000U, 0x3e2aaaabU, 0x3f000000U, 0x3f800000U, 0x3f500000U, 0x3f0e38e4U, 0x3f800000U, 0x3f800000U, 0x3ec00000U, 0x3e2aaaabU, 0x3f22e8baU, 0x3f800000U, 0x3f100000U, 0x3f0e38e4U, 0x3dba2e8cU, 0x3f800000U, 0x3f400000U, 0x3f71c71cU, 0x3f1745d1U, 0x3f800000U, 0x3f700000U, 0x3e8e38e4U, 0x3d3a2e8cU, 0x3f800000U, 0x3d800000U, 0x3f2aaaabU, 0x3f0ba2e9U, 0x3f800000U, 0x3f300000U, 0x3e8e38e4U, 0x3e3a2e8cU, 0x3f800000U, 0x3f600000U, 0x3f2aaaabU, 0x3f2e8ba3U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x3e0ba2e9U, 0x3f800000U, 0x3e400000U, 0x3ec71c72U, 0x3f22e8baU, 0x3f800000U, 0x3ec00000U, 0x3f471c72U, 0x3dba2e8cU, 0x3f800000U, 0x3f800000U, 0x3ec71c72U, 0x3f45d174U, 0x3f800000U, 0x3e000000U, 0x3f471c72U, 0x3e68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3de38e39U, 0x3f3a2e8cU, 0x3f800000U, 0x3f000000U, 0x3f000000U, 0x3e3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3f638e39U, 0x3f2e8ba3U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 80> kCase0ExpectedWords{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3edc08e7U, 0x3edc08e7U, 0x3edc08e7U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3edc08e7U, 0x3edc08e7U, 0x3edc08e7U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 80> kCase0Rgba8{{
  0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 110U, 110U, 110U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 110U, 110U, 110U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U
}};
inline constexpr BindingControl kCase1Bindings{{4.0F, 5.0F}, {0.5F, -0.25F}, {4.0F, 5.0F}, 0.75F, 0, 1, 120, -0.743643887F, 0.131825904F, 0.0F, 0.0F, 0.0F, 4.0F, 0.0F, 0.0F, 0, 60.0F, 12.0F};
inline constexpr std::array<std::uint32_t, 80> kCase1InputWords{{
  0x3e000000U, 0x3de38e39U, 0x3dba2e8cU, 0x3f800000U, 0x3ea00000U, 0x3f000000U, 0x3f1745d1U, 0x3f800000U, 0x3f000000U, 0x3f638e39U, 0x3d3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3e638e39U, 0x3f0ba2e9U, 0x3f800000U, 0x3ee00000U, 0x3e638e39U, 0x3f2e8ba3U, 0x3f800000U, 0x3f200000U, 0x3f1c71c7U, 0x3e0ba2e9U, 0x3f800000U, 0x3f500000U, 0x3f800000U, 0x3f22e8baU, 0x3f800000U, 0x3f800000U, 0x3eaaaaabU, 0x3dba2e8cU, 0x3f800000U, 0x3f400000U, 0x3eaaaaabU, 0x3e68ba2fU, 0x3f800000U, 0x3f700000U, 0x3f38e38eU, 0x3f3a2e8cU, 0x3f800000U, 0x3d800000U, 0x3d638e39U, 0x3e3a2e8cU, 0x3f800000U, 0x3e800000U, 0x3ee38e39U, 0x3f2e8ba3U, 0x3f800000U, 0x00000000U, 0x3ee38e39U, 0x3f51745dU, 0x3f800000U, 0x3e400000U, 0x3f555555U, 0x3e8ba2e9U, 0x3f800000U, 0x3ec00000U, 0x3e2aaaabU, 0x3f45d174U, 0x3f800000U, 0x3f100000U, 0x3f0e38e4U, 0x3e68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3f0e38e4U, 0x3eba2e8cU, 0x3f800000U, 0x3f000000U, 0x3f71c71cU, 0x3f5d1746U, 0x3f800000U, 0x3f300000U, 0x3e8e38e4U, 0x3ea2e8baU, 0x3f800000U, 0x3f600000U, 0x3f2aaaabU, 0x3f51745dU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 80> kCase1ExpectedWords{{
  0x3c21cc39U, 0x3c21cc39U, 0x3c21cc39U, 0x3f800000U, 0x3cf3f6f1U, 0x3cf3f6f1U, 0x3cf3f6f1U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3cc89f93U, 0x3cc89f93U, 0x3cc89f93U, 0x3f800000U, 0x3c952414U, 0x3c952414U, 0x3c952414U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3caf55bcU, 0x3caf55bcU, 0x3caf55bcU, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3cb484e5U, 0x3cb484e5U, 0x3cb484e5U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3cd9ffa2U, 0x3cd9ffa2U, 0x3cd9ffa2U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3bd7ae1dU, 0x3bd7ae1dU, 0x3bd7ae1dU, 0x3f800000U, 0x3d017104U, 0x3d017104U, 0x3d017104U, 0x3f800000U, 0x3d4130dbU, 0x3d4130dbU, 0x3d4130dbU, 0x3f800000U, 0x3ce916c0U, 0x3ce916c0U, 0x3ce916c0U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 80> kCase1Rgba8{{
  3U, 3U, 3U, 255U, 8U, 8U, 8U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 6U, 6U, 6U, 255U, 5U, 5U, 5U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 5U, 5U, 5U, 255U, 0U, 0U, 0U, 255U, 6U, 6U, 6U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 7U, 7U, 7U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 2U, 2U, 2U, 255U, 8U, 8U, 8U, 255U, 12U, 12U, 12U, 255U, 7U, 7U, 7U, 255U
}};
inline constexpr BindingControl kCase2Bindings{{6.0F, 3.0F}, {0.0F, 0.0F}, {6.0F, 3.0F}, 1.5F, 2, 2, 90, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 3.0F, 1.0F, 2.75F, 1, 120.0F, 0.0F};
inline constexpr std::array<std::uint32_t, 72> kCase2InputWords{{
  0x3e400000U, 0x3e2aaaabU, 0x3e0ba2e9U, 0x3f800000U, 0x3ec00000U, 0x3f0e38e4U, 0x3f22e8baU, 0x3f800000U, 0x3f100000U, 0x3f71c71cU, 0x3dba2e8cU, 0x3f800000U, 0x3f400000U, 0x3e8e38e4U, 0x3f1745d1U, 0x3f800000U, 0x3f700000U, 0x3f2aaaabU, 0x3d3a2e8cU, 0x3f800000U, 0x3d800000U, 0x00000000U, 0x3f0ba2e9U, 0x3f800000U, 0x3f000000U, 0x3e8e38e4U, 0x3f3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3f2aaaabU, 0x3e3a2e8cU, 0x3f800000U, 0x3f600000U, 0x00000000U, 0x3f2e8ba3U, 0x3f800000U, 0x00000000U, 0x3ec71c72U, 0x3e0ba2e9U, 0x3f800000U, 0x3e400000U, 0x3f471c72U, 0x3f22e8baU, 0x3f800000U, 0x3ec00000U, 0x3de38e39U, 0x3dba2e8cU, 0x3f800000U, 0x3f500000U, 0x3ec71c72U, 0x3e8ba2e9U, 0x3f800000U, 0x3f800000U, 0x3f471c72U, 0x3f45d174U, 0x3f800000U, 0x3e000000U, 0x3de38e39U, 0x3e68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3f000000U, 0x3f3a2e8cU, 0x3f800000U, 0x3f000000U, 0x3f638e39U, 0x3e3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3e638e39U, 0x3f2e8ba3U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 72> kCase2ExpectedWords{{
  0x3ee51650U, 0x3ee51650U, 0x3ee51650U, 0x3f800000U, 0x3ede5118U, 0x3ede5118U, 0x3ede5118U, 0x3f800000U, 0x3ed62866U, 0x3ed62866U, 0x3ed62866U, 0x3f800000U, 0x3efd8902U, 0x3efd8902U, 0x3efd8902U, 0x3f800000U, 0x3ef7542cU, 0x3ef7542cU, 0x3ef7542cU, 0x3f800000U, 0x3ef1d540U, 0x3ef1d540U, 0x3ef1d540U, 0x3f800000U, 0x3ede31e4U, 0x3ede31e4U, 0x3ede31e4U, 0x3f800000U, 0x3ed95f86U, 0x3ed95f86U, 0x3ed95f86U, 0x3f800000U, 0x3ed56a76U, 0x3ed56a76U, 0x3ed56a76U, 0x3f800000U, 0x3efcf4acU, 0x3efcf4acU, 0x3efcf4acU, 0x3f800000U, 0x3ef68484U, 0x3ef68484U, 0x3ef68484U, 0x3f800000U, 0x3ef01882U, 0x3ef01882U, 0x3ef01882U, 0x3f800000U, 0x3eeeaef6U, 0x3eeeaef6U, 0x3eeeaef6U, 0x3f800000U, 0x3eea6858U, 0x3eea6858U, 0x3eea6858U, 0x3f800000U, 0x3ee5e1ecU, 0x3ee5e1ecU, 0x3ee5e1ecU, 0x3f800000U, 0x3efeec90U, 0x3efeec90U, 0x3efeec90U, 0x3f800000U, 0x3efcc1b6U, 0x3efcc1b6U, 0x3efcc1b6U, 0x3f800000U, 0x3efa70fcU, 0x3efa70fcU, 0x3efa70fcU, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 72> kCase2Rgba8{{
  114U, 114U, 114U, 255U, 111U, 111U, 111U, 255U, 107U, 107U, 107U, 255U, 126U, 126U, 126U, 255U, 123U, 123U, 123U, 255U, 120U, 120U, 120U, 255U, 111U, 111U, 111U, 255U, 108U, 108U, 108U, 255U, 106U, 106U, 106U, 255U, 126U, 126U, 126U, 255U, 123U, 123U, 123U, 255U, 120U, 120U, 120U, 255U, 119U, 119U, 119U, 255U, 117U, 117U, 117U, 255U, 114U, 114U, 114U, 255U, 127U, 127U, 127U, 255U, 126U, 126U, 126U, 255U, 125U, 125U, 125U, 255U
}};
inline constexpr BindingControl kCase3Bindings{{5.0F, 5.0F}, {-0.375F, 0.625F}, {5.0F, 5.0F}, 2.0F, 7, 3, 150, 0.0F, 0.0F, 0.0F, 0.0F, 1.25F, 8.0F, 0.0F, 0.0F, 2, 210.0F, 0.0F};
inline constexpr std::array<std::uint32_t, 100> kCase3InputWords{{
  0x3e800000U, 0x3e638e39U, 0x3e3a2e8cU, 0x3f800000U, 0x3ee00000U, 0x3f1c71c7U, 0x3f2e8ba3U, 0x3f800000U, 0x3f200000U, 0x3f800000U, 0x3e0ba2e9U, 0x3f800000U, 0x3f500000U, 0x3eaaaaabU, 0x3f22e8baU, 0x3f800000U, 0x3f800000U, 0x3f38e38eU, 0x3dba2e8cU, 0x3f800000U, 0x3f100000U, 0x3eaaaaabU, 0x3f45d174U, 0x3f800000U, 0x3f400000U, 0x3f38e38eU, 0x3e68ba2fU, 0x3f800000U, 0x3f700000U, 0x3d638e39U, 0x3f3a2e8cU, 0x3f800000U, 0x3d800000U, 0x3ee38e39U, 0x3e3a2e8cU, 0x3f800000U, 0x3e800000U, 0x3f555555U, 0x3f2e8ba3U, 0x3f800000U, 0x3f600000U, 0x3ee38e39U, 0x3ea2e8baU, 0x3f800000U, 0x00000000U, 0x3f555555U, 0x3f51745dU, 0x3f800000U, 0x3e400000U, 0x3e2aaaabU, 0x3e8ba2e9U, 0x3f800000U, 0x3ec00000U, 0x3f0e38e4U, 0x3f45d174U, 0x3f800000U, 0x3f100000U, 0x3f71c71cU, 0x3e68ba2fU, 0x3f800000U, 0x3e000000U, 0x3f0e38e4U, 0x3f68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3f71c71cU, 0x3eba2e8cU, 0x3f800000U, 0x3f000000U, 0x3e8e38e4U, 0x3f5d1746U, 0x3f800000U, 0x3f300000U, 0x3f2aaaabU, 0x3ea2e8baU, 0x3f800000U, 0x3f600000U, 0x00000000U, 0x3f51745dU, 0x3f800000U, 0x3ee00000U, 0x3f2aaaabU, 0x3ee8ba2fU, 0x3f800000U, 0x3f200000U, 0x00000000U, 0x3f745d17U, 0x3f800000U, 0x3f500000U, 0x3ec71c72U, 0x3ed1745dU, 0x3f800000U, 0x3f800000U, 0x3f471c72U, 0x3f68ba2fU, 0x3f800000U, 0x3e000000U, 0x3de38e39U, 0x3eba2e8cU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 100> kCase3ExpectedWords{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 100> kCase3Rgba8{{
  0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U
}};
inline constexpr BindingControl kCase4Bindings{{4.0F, 4.0F}, {0.0F, 0.0F}, {4.0F, 4.0F}, 3.25F, 0, 4, 64, -1.4F, 0.01F, 2e-08F, -3e-08F, 0.0F, 2.0F, 0.0F, 0.0F, 0, 300.0F, -18.0F};
inline constexpr std::array<std::uint32_t, 64> kCase4InputWords{{
  0x3ea00000U, 0x3e8e38e4U, 0x3e68ba2fU, 0x3f800000U, 0x3f000000U, 0x3f2aaaabU, 0x3f3a2e8cU, 0x3f800000U, 0x3f300000U, 0x00000000U, 0x3e3a2e8cU, 0x3f800000U, 0x3f600000U, 0x3ec71c72U, 0x3f2e8ba3U, 0x3f800000U, 0x3f200000U, 0x3ec71c72U, 0x3f51745dU, 0x3f800000U, 0x3f500000U, 0x3f471c72U, 0x3e8ba2e9U, 0x3f800000U, 0x3f800000U, 0x3de38e39U, 0x3f45d174U, 0x3f800000U, 0x3e000000U, 0x3f000000U, 0x3e68ba2fU, 0x3f800000U, 0x3f700000U, 0x3f000000U, 0x3eba2e8cU, 0x3f800000U, 0x3d800000U, 0x3f638e39U, 0x3f5d1746U, 0x3f800000U, 0x3e800000U, 0x3e638e39U, 0x3ea2e8baU, 0x3f800000U, 0x3ee00000U, 0x3f1c71c7U, 0x3f51745dU, 0x3f800000U, 0x3e400000U, 0x3f1c71c7U, 0x3f745d17U, 0x3f800000U, 0x3ec00000U, 0x3f800000U, 0x3ed1745dU, 0x3f800000U, 0x3f100000U, 0x3eaaaaabU, 0x3f68ba2fU, 0x3f800000U, 0x3f400000U, 0x3f38e38eU, 0x3eba2e8cU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 64> kCase4ExpectedWords{{
  0x3e67b1c1U, 0x3e67b1c1U, 0x3e67b1c1U, 0x3f800000U, 0x3f23c38bU, 0x3f23c38bU, 0x3f23c38bU, 0x3f800000U, 0x3f4fb947U, 0x3f4fb947U, 0x3f4fb947U, 0x3f800000U, 0x3f419d3bU, 0x3f419d3bU, 0x3f419d3bU, 0x3f800000U, 0x3ececd75U, 0x3ececd75U, 0x3ececd75U, 0x3f800000U, 0x3f0002ecU, 0x3f0002ecU, 0x3f0002ecU, 0x3f800000U, 0x3ed633a4U, 0x3ed633a4U, 0x3ed633a4U, 0x3f800000U, 0x3f2862d5U, 0x3f2862d5U, 0x3f2862d5U, 0x3f800000U, 0x3f170928U, 0x3f170928U, 0x3f170928U, 0x3f800000U, 0x3f6b6c7cU, 0x3f6b6c7cU, 0x3f6b6c7cU, 0x3f800000U, 0x3f4d2edbU, 0x3f4d2edbU, 0x3f4d2edbU, 0x3f800000U, 0x3f12ce6dU, 0x3f12ce6dU, 0x3f12ce6dU, 0x3f800000U, 0x3f5dfed4U, 0x3f5dfed4U, 0x3f5dfed4U, 0x3f800000U, 0x3f0da3dfU, 0x3f0da3dfU, 0x3f0da3dfU, 0x3f800000U, 0x3f12ce6dU, 0x3f12ce6dU, 0x3f12ce6dU, 0x3f800000U, 0x3f12ce6dU, 0x3f12ce6dU, 0x3f12ce6dU, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 64> kCase4Rgba8{{
  58U, 58U, 58U, 255U, 163U, 163U, 163U, 255U, 207U, 207U, 207U, 255U, 193U, 193U, 193U, 255U, 103U, 103U, 103U, 255U, 128U, 128U, 128U, 255U, 107U, 107U, 107U, 255U, 168U, 168U, 168U, 255U, 150U, 150U, 150U, 255U, 235U, 235U, 235U, 255U, 204U, 204U, 204U, 255U, 146U, 146U, 146U, 255U, 221U, 221U, 221U, 255U, 141U, 141U, 141U, 255U, 146U, 146U, 146U, 255U, 146U, 146U, 146U, 255U
}};
inline constexpr BindingControl kCase5Bindings{{4.0F, 3.0F}, {0.0F, 0.0F}, {4.0F, 3.0F}, 0.5F, 0, 3, 64, 0.3F, 0.4F, 0.0F, 0.0F, 0.0F, 1.0F, 0.0F, 0.0F, 0, 45.0F, 0.0F};
inline constexpr std::array<std::uint32_t, 48> kCase5InputWords{{
  0x3ee00000U, 0x3ec71c72U, 0x3ea2e8baU, 0x3f800000U, 0x3f200000U, 0x3f471c72U, 0x3f51745dU, 0x3f800000U, 0x3f500000U, 0x3de38e39U, 0x3e8ba2e9U, 0x3f800000U, 0x3f800000U, 0x3f000000U, 0x3f45d174U, 0x3f800000U, 0x3f400000U, 0x3f000000U, 0x3f68ba2fU, 0x3f800000U, 0x3f700000U, 0x3f638e39U, 0x3eba2e8cU, 0x3f800000U, 0x3d800000U, 0x3e638e39U, 0x3f5d1746U, 0x3f800000U, 0x3e800000U, 0x3f1c71c7U, 0x3ea2e8baU, 0x3f800000U, 0x00000000U, 0x3f1c71c7U, 0x3ee8ba2fU, 0x3f800000U, 0x3e400000U, 0x3f800000U, 0x3f745d17U, 0x3f800000U, 0x3ec00000U, 0x3eaaaaabU, 0x3ed1745dU, 0x3f800000U, 0x3f100000U, 0x3f38e38eU, 0x3f68ba2fU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 48> kCase5ExpectedWords{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3f58a09eU, 0x3f58a09eU, 0x3f58a09eU, 0x3f800000U, 0x3f2d9e21U, 0x3f2d9e21U, 0x3f2d9e21U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3f63d079U, 0x3f63d079U, 0x3f63d079U, 0x3f800000U, 0x3f354b95U, 0x3f354b95U, 0x3f354b95U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3f4a918cU, 0x3f4a918cU, 0x3f4a918cU, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 48> kCase5Rgba8{{
  0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 216U, 216U, 216U, 255U, 173U, 173U, 173U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 227U, 227U, 227U, 255U, 181U, 181U, 181U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 202U, 202U, 202U, 255U
}};
inline constexpr BindingControl kCase6Bindings{{3.0F, 3.0F}, {0.0F, 0.0F}, {3.0F, 3.0F}, 0.0F, 0, 0, 32, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0, 0.0F, 0.0F};
inline constexpr std::array<std::uint32_t, 36> kCase6InputWords{{
  0x3ec00000U, 0x3eaaaaabU, 0x3e8ba2e9U, 0x3f800000U, 0x3f100000U, 0x3f38e38eU, 0x3f45d174U, 0x3f800000U, 0x3f400000U, 0x3d638e39U, 0x3e68ba2fU, 0x3f800000U, 0x3f300000U, 0x3ee38e39U, 0x3f5d1746U, 0x3f800000U, 0x3f600000U, 0x3f555555U, 0x3ea2e8baU, 0x3f800000U, 0x00000000U, 0x3e2aaaabU, 0x3f51745dU, 0x3f800000U, 0x3f800000U, 0x3f0e38e4U, 0x3ed1745dU, 0x3f800000U, 0x3e000000U, 0x3f71c71cU, 0x3f68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3e8e38e4U, 0x3eba2e8cU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 36> kCase6ExpectedWords{{
  0x3dc4718cU, 0x3dc4718cU, 0x3dc4718cU, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3d582c88U, 0x3d582c88U, 0x3d582c88U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3d8dbe0aU, 0x3d8dbe0aU, 0x3d8dbe0aU, 0x3f800000U, 0x3dc4718cU, 0x3dc4718cU, 0x3dc4718cU, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3d582c88U, 0x3d582c88U, 0x3d582c88U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 36> kCase6Rgba8{{
  24U, 24U, 24U, 255U, 0U, 0U, 0U, 255U, 13U, 13U, 13U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 18U, 18U, 18U, 255U, 24U, 24U, 24U, 255U, 0U, 0U, 0U, 255U, 13U, 13U, 13U, 255U
}};
struct CaseView { std::string_view name; std::size_t width; std::size_t height; BindingControl bindings; std::span<const std::uint32_t> input; std::span<const std::uint32_t> expected; std::span<const std::uint8_t> rgba8; };
inline constexpr std::array<CaseView, 7> kCases{{
  CaseView{"manual-smooth", 5U, 4U, kCase0Bindings, kCase0InputWords, kCase0ExpectedWords, kCase0Rgba8},
  CaseView{"manual-distance-tile", 4U, 5U, kCase1Bindings, kCase1InputWords, kCase1ExpectedWords, kCase1Rgba8},
  CaseView{"poi-stripe", 6U, 3U, kCase2Bindings, kCase2InputWords, kCase2ExpectedWords, kCase2Rgba8},
  CaseView{"poi-trap", 5U, 5U, kCase3Bindings, kCase3InputWords, kCase3ExpectedWords, kCase3Rgba8},
  CaseView{"manual-normal", 4U, 4U, kCase4Bindings, kCase4InputWords, kCase4ExpectedWords, kCase4Rgba8},
  CaseView{"manual-trap-escape", 4U, 3U, kCase5Bindings, kCase5InputWords, kCase5ExpectedWords, kCase5Rgba8},
  CaseView{"period-bulb-control", 3U, 3U, kCase6Bindings, kCase6InputWords, kCase6ExpectedWords, kCase6Rgba8},
}};
struct MutationView { std::string_view name; std::size_t anchor_occurrence_count; std::size_t witness_count; };
inline constexpr std::array<MutationView, 21> kMutations{{
  MutationView{"cross-lane-dz-assignment", 1U, 2U},
  MutationView{"df64-new-zr-carrier", 1U, 7U},
  MutationView{"df64-whole-vector-carrier", 1U, 6U},
  MutationView{"out-smoothIter", 1U, 3U},
  MutationView{"out-rawIter-cardioid", 1U, 2U},
  MutationView{"out-z-final", 1U, 5U},
  MutationView{"out-dz-final", 1U, 2U},
  MutationView{"out-stripeAcc", 1U, 1U},
  MutationView{"out-trapMin", 1U, 1U},
  MutationView{"out-getPOI-cX", 1U, 5U},
  MutationView{"out-getPOI-cY", 1U, 4U},
  MutationView{"out-transform-re", 2U, 6U},
  MutationView{"out-transform-im", 2U, 6U},
  MutationView{"max-iter-constant", 1U, 6U},
  MutationView{"runtime-loop-bound", 1U, 5U},
  MutationView{"log-magnitude", 1U, 3U},
  MutationView{"log-normalization", 1U, 3U},
  MutationView{"log-distance-magnitude", 1U, 2U},
  MutationView{"normal-h0", 1U, 1U},
  MutationView{"normal-hx", 1U, 1U},
  MutationView{"normal-hy", 1U, 1U},
}};
}
