// Generated from the authenticated Newton JSON oracle.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string_view>

namespace newton_oracle {
inline constexpr std::string_view kProgramKey = "synth/newton:newton";
inline constexpr std::string_view kOracleSha256 = "4a5a109045fa1d57b928b135b752a034b821f5f3c10c3466637e3523e7ab69a8";
inline constexpr std::string_view kFactoryTextSha256 = "7e4e95cfd6afa9f89e24920dbb06cd3af6f90f0c83f4329e302f701b78bba7af";
inline constexpr std::array<std::string_view, 22> kBindingNames{{
  "resolution", "tileOffset", "fullResolution", "time", "degree", "relaxation", "iterations", "tolerance", "poi", "centerHiX", "centerHiY", "centerLoX", "centerLoY", "zoomSpeed", "zoomDepth", "degreeSpeed", "degreeRange", "relaxSpeed", "relaxRange", "rotation", "outputMode", "invert"
}};
struct BindingAbiView { std::string_view name; std::string_view category; };
inline constexpr std::array<BindingAbiView, 22> kBindingAbi{{
  BindingAbiView{"resolution", "Vec2"},
  BindingAbiView{"tileOffset", "Vec2"},
  BindingAbiView{"fullResolution", "Vec2"},
  BindingAbiView{"time", "number"},
  BindingAbiView{"degree", "number"},
  BindingAbiView{"relaxation", "number"},
  BindingAbiView{"iterations", "number"},
  BindingAbiView{"tolerance", "number"},
  BindingAbiView{"poi", "number"},
  BindingAbiView{"centerHiX", "number"},
  BindingAbiView{"centerHiY", "number"},
  BindingAbiView{"centerLoX", "number"},
  BindingAbiView{"centerLoY", "number"},
  BindingAbiView{"zoomSpeed", "number"},
  BindingAbiView{"zoomDepth", "number"},
  BindingAbiView{"degreeSpeed", "number"},
  BindingAbiView{"degreeRange", "number"},
  BindingAbiView{"relaxSpeed", "number"},
  BindingAbiView{"relaxRange", "number"},
  BindingAbiView{"rotation", "number"},
  BindingAbiView{"outputMode", "number"},
  BindingAbiView{"invert", "number"},
}};
struct BindingControl { std::array<float, 2> resolution; std::array<float, 2> tileOffset; std::array<float, 2> fullResolution; float time; float degree; float relaxation; float iterations; float tolerance; float poi; float centerHiX; float centerHiY; float centerLoX; float centerLoY; float zoomSpeed; float zoomDepth; float degreeSpeed; float degreeRange; float relaxSpeed; float relaxRange; float rotation; float outputMode; float invert; };
inline constexpr BindingControl kCase0Bindings{{4.0F, 4.0F}, {0.0F, 0.0F}, {4.0F, 4.0F}, 0.25F, 3.0F, 1.0F, 80.0F, 0.001F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 1.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F};
inline constexpr std::array<std::uint32_t, 64> kCase0InputWords{{
  0x3d800000U, 0x3d638e39U, 0x3d3a2e8cU, 0x3f800000U, 0x3e800000U, 0x3ee38e39U, 0x3f0ba2e9U, 0x3f800000U, 0x3ee00000U, 0x3f555555U, 0x00000000U, 0x3f800000U, 0x3f200000U, 0x3e2aaaabU, 0x3f000000U, 0x3f800000U, 0x3ec00000U, 0x3e2aaaabU, 0x3f22e8baU, 0x3f800000U, 0x3f100000U, 0x3f0e38e4U, 0x3dba2e8cU, 0x3f800000U, 0x3f400000U, 0x3f71c71cU, 0x3f1745d1U, 0x3f800000U, 0x3f700000U, 0x3e8e38e4U, 0x3d3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3e8e38e4U, 0x3e3a2e8cU, 0x3f800000U, 0x3f600000U, 0x3f2aaaabU, 0x3f2e8ba3U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x3e0ba2e9U, 0x3f800000U, 0x3e400000U, 0x3ec71c72U, 0x3f22e8baU, 0x3f800000U, 0x3f800000U, 0x3ec71c72U, 0x3f45d174U, 0x3f800000U, 0x3e000000U, 0x3f471c72U, 0x3e68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3de38e39U, 0x3f3a2e8cU, 0x3f800000U, 0x3f000000U, 0x3f000000U, 0x3e3a2e8cU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 64> kCase0ExpectedWords{{
  0x3dfd4501U, 0x3dfd4501U, 0x3dfd4501U, 0x3f800000U, 0x3e0d7183U, 0x3e0d7183U, 0x3e0d7183U, 0x3f800000U, 0x3e0d4081U, 0x3e0d4081U, 0x3e0d4081U, 0x3f800000U, 0x3dfd5f32U, 0x3dfd5f32U, 0x3dfd5f32U, 0x3f800000U, 0x3e173e39U, 0x3e173e39U, 0x3e173e39U, 0x3f800000U, 0x3e44082dU, 0x3e44082dU, 0x3e44082dU, 0x3f800000U, 0x3e440490U, 0x3e440490U, 0x3e440490U, 0x3f800000U, 0x3e171d56U, 0x3e171d56U, 0x3e171d56U, 0x3f800000U, 0x3e173e39U, 0x3e173e39U, 0x3e173e39U, 0x3f800000U, 0x3e440402U, 0x3e440402U, 0x3e440402U, 0x3f800000U, 0x3e4408bcU, 0x3e4408bcU, 0x3e4408bcU, 0x3f800000U, 0x3e171d56U, 0x3e171d56U, 0x3e171d56U, 0x3f800000U, 0x3dfd44deU, 0x3dfd44deU, 0x3dfd44deU, 0x3f800000U, 0x3e0d4cedU, 0x3e0d4cedU, 0x3e0d4cedU, 0x3f800000U, 0x3e0d6532U, 0x3e0d6532U, 0x3e0d6532U, 0x3f800000U, 0x3dfd5f44U, 0x3dfd5f44U, 0x3dfd5f44U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 64> kCase0Rgba8{{
  32U, 32U, 32U, 255U, 35U, 35U, 35U, 255U, 35U, 35U, 35U, 255U, 32U, 32U, 32U, 255U, 38U, 38U, 38U, 255U, 49U, 49U, 49U, 255U, 49U, 49U, 49U, 255U, 38U, 38U, 38U, 255U, 38U, 38U, 38U, 255U, 49U, 49U, 49U, 255U, 49U, 49U, 49U, 255U, 38U, 38U, 38U, 255U, 32U, 32U, 32U, 255U, 35U, 35U, 35U, 255U, 35U, 35U, 35U, 255U, 32U, 32U, 32U, 255U
}};
inline constexpr BindingControl kCase1Bindings{{4.0F, 3.0F}, {0.25F, -0.25F}, {4.0F, 3.0F}, 0.75F, 3.0F, 1.0F, 100.0F, 0.0001F, 2.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 5.0F, 0.0F, 0.0F, 0.0F, 0.0F, 11.0F, 0.0F, 0.0F};
inline constexpr std::array<std::uint32_t, 48> kCase1InputWords{{
  0x3e000000U, 0x3de38e39U, 0x3dba2e8cU, 0x3f800000U, 0x3ea00000U, 0x3f000000U, 0x3f1745d1U, 0x3f800000U, 0x3f000000U, 0x3f638e39U, 0x3d3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3e638e39U, 0x3f0ba2e9U, 0x3f800000U, 0x3ee00000U, 0x3e638e39U, 0x3f2e8ba3U, 0x3f800000U, 0x3f200000U, 0x3f1c71c7U, 0x3e0ba2e9U, 0x3f800000U, 0x3f500000U, 0x3f800000U, 0x3f22e8baU, 0x3f800000U, 0x3f800000U, 0x3eaaaaabU, 0x3dba2e8cU, 0x3f800000U, 0x3f400000U, 0x3eaaaaabU, 0x3e68ba2fU, 0x3f800000U, 0x3f700000U, 0x3f38e38eU, 0x3f3a2e8cU, 0x3f800000U, 0x3d800000U, 0x3d638e39U, 0x3e3a2e8cU, 0x3f800000U, 0x3e800000U, 0x3ee38e39U, 0x3f2e8ba3U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 48> kCase1ExpectedWords{{
  0xb9fe2bfaU, 0xb9fe2bfaU, 0xb9fe2bfaU, 0x3f800000U, 0xbab581e6U, 0xbab581e6U, 0xbab581e6U, 0x3f800000U, 0xba7bfb17U, 0xba7bfb17U, 0xba7bfb17U, 0x3f800000U, 0xb8a7f5ceU, 0xb8a7f5ceU, 0xb8a7f5ceU, 0x3f800000U, 0xba33ce4cU, 0xba33ce4cU, 0xba33ce4cU, 0x3f800000U, 0xbb22b1e4U, 0xbb22b1e4U, 0xbb22b1e4U, 0x3f800000U, 0xbab63d40U, 0xbab63d40U, 0xbab63d40U, 0x3f800000U, 0xb948cbb8U, 0xb948cbb8U, 0xb948cbb8U, 0x3f800000U, 0xb9433824U, 0xb9433824U, 0xb9433824U, 0x3f800000U, 0xba35c69dU, 0xba35c69dU, 0xba35c69dU, 0x3f800000U, 0xba002dffU, 0xba002dffU, 0xba002dffU, 0x3f800000U, 0x3b027a78U, 0x3b027a78U, 0x3b027a78U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 48> kCase1Rgba8{{
  0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 1U, 1U, 1U, 255U
}};
inline constexpr BindingControl kCase2Bindings{{3.0F, 4.0F}, {0.0F, 0.0F}, {3.0F, 4.0F}, 1.25F, 5.0F, 0.9F, 120.0F, 0.01F, 4.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 3.0F, 0.0F, 0.0F, 0.0F, 0.0F, -17.0F, 1.0F, 0.0F};
inline constexpr std::array<std::uint32_t, 48> kCase2InputWords{{
  0x3e400000U, 0x3e2aaaabU, 0x3e0ba2e9U, 0x3f800000U, 0x3ec00000U, 0x3f0e38e4U, 0x3f22e8baU, 0x3f800000U, 0x3f100000U, 0x3f71c71cU, 0x3dba2e8cU, 0x3f800000U, 0x3f000000U, 0x3e8e38e4U, 0x3f3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3f2aaaabU, 0x3e3a2e8cU, 0x3f800000U, 0x3f600000U, 0x00000000U, 0x3f2e8ba3U, 0x3f800000U, 0x3f500000U, 0x3ec71c72U, 0x3e8ba2e9U, 0x3f800000U, 0x3f800000U, 0x3f471c72U, 0x3f45d174U, 0x3f800000U, 0x3e000000U, 0x3de38e39U, 0x3e68ba2fU, 0x3f800000U, 0x3d800000U, 0x3f000000U, 0x3f5d1746U, 0x3f800000U, 0x3e800000U, 0x3f638e39U, 0x3ea2e8baU, 0x3f800000U, 0x3ee00000U, 0x3e638e39U, 0x3f51745dU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 48> kCase2ExpectedWords{{
  0x3f19999aU, 0x3f19999aU, 0x3f19999aU, 0x3f800000U, 0x3f19999aU, 0x3f19999aU, 0x3f19999aU, 0x3f800000U, 0x3f19999aU, 0x3f19999aU, 0x3f19999aU, 0x3f800000U, 0x3f19999aU, 0x3f19999aU, 0x3f19999aU, 0x3f800000U, 0x3f19999aU, 0x3f19999aU, 0x3f19999aU, 0x3f800000U, 0x3f19999aU, 0x3f19999aU, 0x3f19999aU, 0x3f800000U, 0x3f19999aU, 0x3f19999aU, 0x3f19999aU, 0x3f800000U, 0x3f19999aU, 0x3f19999aU, 0x3f19999aU, 0x3f800000U, 0x3f19999aU, 0x3f19999aU, 0x3f19999aU, 0x3f800000U, 0x3f19999aU, 0x3f19999aU, 0x3f19999aU, 0x3f800000U, 0x3f19999aU, 0x3f19999aU, 0x3f19999aU, 0x3f800000U, 0x3f19999aU, 0x3f19999aU, 0x3f19999aU, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 48> kCase2Rgba8{{
  153U, 153U, 153U, 255U, 153U, 153U, 153U, 255U, 153U, 153U, 153U, 255U, 153U, 153U, 153U, 255U, 153U, 153U, 153U, 255U, 153U, 153U, 153U, 255U, 153U, 153U, 153U, 255U, 153U, 153U, 153U, 255U, 153U, 153U, 153U, 255U, 153U, 153U, 153U, 255U, 153U, 153U, 153U, 255U, 153U, 153U, 153U, 255U
}};
inline constexpr BindingControl kCase3Bindings{{5.0F, 3.0F}, {-0.5F, 0.5F}, {5.0F, 3.0F}, 2.0F, 5.0F, 1.2F, 150.0F, 0.005F, 3.0F, 0.01F, -0.02F, 1e-07F, -2e-07F, 1.2F, 4.0F, 0.5F, 1.0F, 0.7F, 0.3F, 25.0F, 2.0F, 0.0F};
inline constexpr std::array<std::uint32_t, 60> kCase3InputWords{{
  0x3e800000U, 0x3e638e39U, 0x3e3a2e8cU, 0x3f800000U, 0x3ee00000U, 0x3f1c71c7U, 0x3f2e8ba3U, 0x3f800000U, 0x3f200000U, 0x3f800000U, 0x3e0ba2e9U, 0x3f800000U, 0x3f500000U, 0x3eaaaaabU, 0x3f22e8baU, 0x3f800000U, 0x3f800000U, 0x3f38e38eU, 0x3dba2e8cU, 0x3f800000U, 0x3f100000U, 0x3eaaaaabU, 0x3f45d174U, 0x3f800000U, 0x3f400000U, 0x3f38e38eU, 0x3e68ba2fU, 0x3f800000U, 0x3f700000U, 0x3d638e39U, 0x3f3a2e8cU, 0x3f800000U, 0x3d800000U, 0x3ee38e39U, 0x3e3a2e8cU, 0x3f800000U, 0x3e800000U, 0x3f555555U, 0x3f2e8ba3U, 0x3f800000U, 0x3f600000U, 0x3ee38e39U, 0x3ea2e8baU, 0x3f800000U, 0x00000000U, 0x3f555555U, 0x3f51745dU, 0x3f800000U, 0x3e400000U, 0x3e2aaaabU, 0x3e8ba2e9U, 0x3f800000U, 0x3ec00000U, 0x3f0e38e4U, 0x3f45d174U, 0x3f800000U, 0x3f100000U, 0x3f71c71cU, 0x3e68ba2fU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 60> kCase3ExpectedWords{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 60> kCase3Rgba8{{
  0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U
}};
inline constexpr BindingControl kCase4Bindings{{4.0F, 4.0F}, {0.0F, 0.0F}, {4.0F, 4.0F}, 0.5F, 3.0F, 1.0F, 70.0F, 0.002F, 1.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 2.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 1.0F};
inline constexpr std::array<std::uint32_t, 64> kCase4InputWords{{
  0x3ea00000U, 0x3e8e38e4U, 0x3e68ba2fU, 0x3f800000U, 0x3f000000U, 0x3f2aaaabU, 0x3f3a2e8cU, 0x3f800000U, 0x3f300000U, 0x00000000U, 0x3e3a2e8cU, 0x3f800000U, 0x3f600000U, 0x3ec71c72U, 0x3f2e8ba3U, 0x3f800000U, 0x3f200000U, 0x3ec71c72U, 0x3f51745dU, 0x3f800000U, 0x3f500000U, 0x3f471c72U, 0x3e8ba2e9U, 0x3f800000U, 0x3f800000U, 0x3de38e39U, 0x3f45d174U, 0x3f800000U, 0x3e000000U, 0x3f000000U, 0x3e68ba2fU, 0x3f800000U, 0x3f700000U, 0x3f000000U, 0x3eba2e8cU, 0x3f800000U, 0x3d800000U, 0x3f638e39U, 0x3f5d1746U, 0x3f800000U, 0x3e800000U, 0x3e638e39U, 0x3ea2e8baU, 0x3f800000U, 0x3ee00000U, 0x3f1c71c7U, 0x3f51745dU, 0x3f800000U, 0x3e400000U, 0x3f1c71c7U, 0x3f745d17U, 0x3f800000U, 0x3ec00000U, 0x3f800000U, 0x3ed1745dU, 0x3f800000U, 0x3f100000U, 0x3eaaaaabU, 0x3f68ba2fU, 0x3f800000U, 0x3f400000U, 0x3f38e38eU, 0x3eba2e8cU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 64> kCase4ExpectedWords{{
  0x3f32d431U, 0x3f32d431U, 0x3f32d431U, 0x3f800000U, 0x3f2ea2baU, 0x3f2ea2baU, 0x3f2ea2baU, 0x3f800000U, 0x3f2ea24bU, 0x3f2ea24bU, 0x3f2ea24bU, 0x3f800000U, 0x3f32d655U, 0x3f32d655U, 0x3f32d655U, 0x3f800000U, 0x3f2bd668U, 0x3f2bd668U, 0x3f2bd668U, 0x3f800000U, 0x3f1f0372U, 0x3f1f0372U, 0x3f1f0372U, 0x3f800000U, 0x3f1f0358U, 0x3f1f0358U, 0x3f1f0358U, 0x3f800000U, 0x3f2bd669U, 0x3f2bd669U, 0x3f2bd669U, 0x3f800000U, 0x3f2bd668U, 0x3f2bd668U, 0x3f2bd668U, 0x3f800000U, 0x3f1f034fU, 0x3f1f034fU, 0x3f1f034fU, 0x3f800000U, 0x3f1f037bU, 0x3f1f037bU, 0x3f1f037bU, 0x3f800000U, 0x3f2bd669U, 0x3f2bd669U, 0x3f2bd669U, 0x3f800000U, 0x3f32d62fU, 0x3f32d62fU, 0x3f32d62fU, 0x3f800000U, 0x3f2ea24bU, 0x3f2ea24bU, 0x3f2ea24bU, 0x3f800000U, 0x3f2ea2baU, 0x3f2ea2baU, 0x3f2ea2baU, 0x3f800000U, 0x3f32d456U, 0x3f32d456U, 0x3f32d456U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 64> kCase4Rgba8{{
  178U, 178U, 178U, 255U, 174U, 174U, 174U, 255U, 174U, 174U, 174U, 255U, 178U, 178U, 178U, 255U, 171U, 171U, 171U, 255U, 158U, 158U, 158U, 255U, 158U, 158U, 158U, 255U, 171U, 171U, 171U, 255U, 171U, 171U, 171U, 255U, 158U, 158U, 158U, 255U, 158U, 158U, 158U, 255U, 171U, 171U, 171U, 255U, 178U, 178U, 178U, 255U, 174U, 174U, 174U, 255U, 174U, 174U, 174U, 255U, 178U, 178U, 178U, 255U
}};
inline constexpr BindingControl kCase5Bindings{{3.0F, 3.0F}, {0.0F, 0.0F}, {3.0F, 3.0F}, 1.1F, 7.0F, 1.0F, 90.0F, 0.003F, 0.0F, -0.2F, 0.15F, 0.0F, 0.0F, 0.0F, 1.0F, 0.0F, 0.0F, 0.0F, 0.0F, 8.0F, 0.0F, 0.0F};
inline constexpr std::array<std::uint32_t, 36> kCase5InputWords{{
  0x3ec00000U, 0x3eaaaaabU, 0x3e8ba2e9U, 0x3f800000U, 0x3f100000U, 0x3f38e38eU, 0x3f45d174U, 0x3f800000U, 0x3f400000U, 0x3d638e39U, 0x3e68ba2fU, 0x3f800000U, 0x3f300000U, 0x3ee38e39U, 0x3f5d1746U, 0x3f800000U, 0x3f600000U, 0x3f555555U, 0x3ea2e8baU, 0x3f800000U, 0x00000000U, 0x3e2aaaabU, 0x3f51745dU, 0x3f800000U, 0x3f800000U, 0x3f0e38e4U, 0x3ed1745dU, 0x3f800000U, 0x3e000000U, 0x3f71c71cU, 0x3f68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3e8e38e4U, 0x3eba2e8cU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 36> kCase5ExpectedWords{{
  0x3ea7c051U, 0x3ea7c051U, 0x3ea7c051U, 0x3f800000U, 0x3ed44aa4U, 0x3ed44aa4U, 0x3ed44aa4U, 0x3f800000U, 0x3ee348a6U, 0x3ee348a6U, 0x3ee348a6U, 0x3f800000U, 0x3ec16a11U, 0x3ec16a11U, 0x3ec16a11U, 0x3f800000U, 0x3efd45c3U, 0x3efd45c3U, 0x3efd45c3U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3ef07010U, 0x3ef07010U, 0x3ef07010U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 36> kCase5Rgba8{{
  84U, 84U, 84U, 255U, 106U, 106U, 106U, 255U, 113U, 113U, 113U, 255U, 96U, 96U, 96U, 255U, 126U, 126U, 126U, 255U, 255U, 255U, 255U, 255U, 120U, 120U, 120U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U
}};
inline constexpr BindingControl kCase6Bindings{{3.0F, 5.0F}, {0.0F, 0.0F}, {3.0F, 5.0F}, 1.7F, 4.0F, 1.6F, 110.0F, 0.002F, 0.0F, 0.1F, -0.1F, 0.0F, 0.0F, 0.8F, 2.0F, 0.0F, 0.0F, 0.0F, 0.0F, 33.0F, 2.0F, 0.0F};
inline constexpr std::array<std::uint32_t, 60> kCase6InputWords{{
  0x3ee00000U, 0x3ec71c72U, 0x3ea2e8baU, 0x3f800000U, 0x3f200000U, 0x3f471c72U, 0x3f51745dU, 0x3f800000U, 0x3f500000U, 0x3de38e39U, 0x3e8ba2e9U, 0x3f800000U, 0x3f400000U, 0x3f000000U, 0x3f68ba2fU, 0x3f800000U, 0x3f700000U, 0x3f638e39U, 0x3eba2e8cU, 0x3f800000U, 0x3d800000U, 0x3e638e39U, 0x3f5d1746U, 0x3f800000U, 0x00000000U, 0x3f1c71c7U, 0x3ee8ba2fU, 0x3f800000U, 0x3e400000U, 0x3f800000U, 0x3f745d17U, 0x3f800000U, 0x3ec00000U, 0x3eaaaaabU, 0x3ed1745dU, 0x3f800000U, 0x3ea00000U, 0x3f38e38eU, 0x00000000U, 0x3f800000U, 0x3f000000U, 0x3d638e39U, 0x3f000000U, 0x3f800000U, 0x3f300000U, 0x3ee38e39U, 0x3f800000U, 0x3f800000U, 0x3f200000U, 0x3f555555U, 0x3f1745d1U, 0x3f800000U, 0x3f500000U, 0x3e2aaaabU, 0x3d3a2e8cU, 0x3f800000U, 0x3f800000U, 0x3f0e38e4U, 0x3f0ba2e9U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 60> kCase6ExpectedWords{{
  0x3f0f135eU, 0x3f0f135eU, 0x3f0f135eU, 0x3f800000U, 0x3d688a1aU, 0x3d688a1aU, 0x3d688a1aU, 0x3f800000U, 0x3e960820U, 0x3e960820U, 0x3e960820U, 0x3f800000U, 0x3f0d5783U, 0x3f0d5783U, 0x3f0d5783U, 0x3f800000U, 0x3d4bd68aU, 0x3d4bd68aU, 0x3d4bd68aU, 0x3f800000U, 0x3e961aa0U, 0x3e961aa0U, 0x3e961aa0U, 0x3f800000U, 0x3f0cc8b2U, 0x3f0cc8b2U, 0x3f0cc8b2U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3e973c6cU, 0x3e973c6cU, 0x3e973c6cU, 0x3f800000U, 0x3f0b94c9U, 0x3f0b94c9U, 0x3f0b94c9U, 0x3f800000U, 0x3d7ac9daU, 0x3d7ac9daU, 0x3d7ac9daU, 0x3f800000U, 0x3d39dff9U, 0x3d39dff9U, 0x3d39dff9U, 0x3f800000U, 0x3f0a72b5U, 0x3f0a72b5U, 0x3f0a72b5U, 0x3f800000U, 0x3f1a210bU, 0x3f1a210bU, 0x3f1a210bU, 0x3f800000U, 0x3e9861deU, 0x3e9861deU, 0x3e9861deU, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 60> kCase6Rgba8{{
  143U, 143U, 143U, 255U, 14U, 14U, 14U, 255U, 75U, 75U, 75U, 255U, 141U, 141U, 141U, 255U, 13U, 13U, 13U, 255U, 75U, 75U, 75U, 255U, 140U, 140U, 140U, 255U, 0U, 0U, 0U, 255U, 75U, 75U, 75U, 255U, 139U, 139U, 139U, 255U, 16U, 16U, 16U, 255U, 12U, 12U, 12U, 255U, 138U, 138U, 138U, 255U, 154U, 154U, 154U, 255U, 76U, 76U, 76U, 255U
}};
inline constexpr BindingControl kCase7Bindings{{5.0F, 4.0F}, {0.0F, 0.0F}, {5.0F, 4.0F}, 0.9F, 6.0F, 1.0F, 100.0F, 0.05F, 5.0F, 0.0F, 0.0F, 0.0F, 0.0F, 0.0F, 2.0F, 0.0F, 0.0F, 0.0F, 0.0F, -9.0F, 1.0F, 0.0F};
inline constexpr std::array<std::uint32_t, 80> kCase7InputWords{{
  0x3f000000U, 0x3ee38e39U, 0x3eba2e8cU, 0x3f800000U, 0x3f300000U, 0x3f555555U, 0x3f5d1746U, 0x3f800000U, 0x3f600000U, 0x3e2aaaabU, 0x3ea2e8baU, 0x3f800000U, 0x00000000U, 0x3f0e38e4U, 0x3f51745dU, 0x3f800000U, 0x3e400000U, 0x3f71c71cU, 0x3e8ba2e9U, 0x3f800000U, 0x3f500000U, 0x3f0e38e4U, 0x3f745d17U, 0x3f800000U, 0x3f800000U, 0x3f71c71cU, 0x3ed1745dU, 0x3f800000U, 0x3e000000U, 0x3e8e38e4U, 0x3f68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3f2aaaabU, 0x3eba2e8cU, 0x3f800000U, 0x3f000000U, 0x00000000U, 0x3f5d1746U, 0x3f800000U, 0x3d800000U, 0x3f2aaaabU, 0x3f000000U, 0x3f800000U, 0x3e800000U, 0x00000000U, 0x3f800000U, 0x3f800000U, 0x3ee00000U, 0x3ec71c72U, 0x3ee8ba2fU, 0x3f800000U, 0x3f200000U, 0x3f471c72U, 0x3f745d17U, 0x3f800000U, 0x3f500000U, 0x3de38e39U, 0x3ed1745dU, 0x3f800000U, 0x3ec00000U, 0x3f471c72U, 0x3d3a2e8cU, 0x3f800000U, 0x3f100000U, 0x3de38e39U, 0x3f0ba2e9U, 0x3f800000U, 0x3f400000U, 0x3f000000U, 0x00000000U, 0x3f800000U, 0x3f700000U, 0x3f638e39U, 0x3f000000U, 0x3f800000U, 0x3d800000U, 0x3e638e39U, 0x3f800000U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 80> kCase7ExpectedWords{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 80> kCase7Rgba8{{
  0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U
}};
struct CaseView { std::string_view name; std::size_t width; std::size_t height; BindingControl bindings; std::span<const std::uint32_t> input; std::span<const std::uint32_t> expected; std::span<const std::uint8_t> rgba8; };
inline constexpr std::array<CaseView, 8> kCases{{
  CaseView{"manual-baseline", 4U, 4U, kCase0Bindings, kCase0InputWords, kCase0ExpectedWords, kCase0Rgba8},
  CaseView{"poi-spiral", 4U, 3U, kCase1Bindings, kCase1InputWords, kCase1ExpectedWords, kCase1Rgba8},
  CaseView{"root-mode", 3U, 4U, kCase2Bindings, kCase2InputWords, kCase2ExpectedWords, kCase2Rgba8},
  CaseView{"combined-mode", 5U, 3U, kCase3Bindings, kCase3InputWords, kCase3ExpectedWords, kCase3Rgba8},
  CaseView{"invert-axis", 4U, 4U, kCase4Bindings, kCase4InputWords, kCase4ExpectedWords, kCase4Rgba8},
  CaseView{"degree-axis", 3U, 3U, kCase5Bindings, kCase5InputWords, kCase5ExpectedWords, kCase5Rgba8},
  CaseView{"relax-axis", 3U, 5U, kCase6Bindings, kCase6InputWords, kCase6ExpectedWords, kCase6Rgba8},
  CaseView{"tolerance-axis", 5U, 4U, kCase7Bindings, kCase7InputWords, kCase7ExpectedWords, kCase7Rgba8},
}};
struct MutationView { std::string_view name; std::string_view group; std::size_t anchor_occurrence_count; std::size_t witness_count; bool structural_only; bool structural_probe; };
inline constexpr std::array<MutationView, 16> kMutations{{
  MutationView{"cross-lane-assignment", "cross-lane-assignment", 1U, 5U, false, false},
  MutationView{"df64-cmul-rr-owner", "out-materialization", 1U, 6U, false, false},
  MutationView{"df64-cmul-ri-owner", "out-materialization", 1U, 6U, false, false},
  MutationView{"transform-re-owner", "out-materialization", 1U, 6U, false, false},
  MutationView{"transform-im-owner", "out-materialization", 1U, 6U, false, false},
  MutationView{"cmul-call-materialization", "out-materialization", 1U, 6U, false, false},
  MutationView{"znr-call-materialization", "out-materialization", 1U, 6U, false, false},
  MutationView{"transform-call-materialization", "out-materialization", 1U, 6U, false, false},
  MutationView{"iteration-outer-bound", "control-axis", 1U, 6U, false, false},
  MutationView{"iteration-power-bound", "control-axis", 1U, 8U, false, false},
  MutationView{"degree-control-axis", "control-axis", 1U, 3U, false, false},
  MutationView{"relaxation-control-axis", "control-axis", 1U, 5U, false, false},
  MutationView{"tolerance-control-axis", "control-axis", 1U, 5U, false, false},
  MutationView{"rotation-control-axis", "control-axis", 1U, 3U, false, false},
  MutationView{"invert-control-axis", "control-axis", 1U, 1U, false, false},
  MutationView{"struct-POIData-declaration", "struct-declaration", 1U, 1U, false, true},
}};
struct MutationWitnessView { std::string_view mutation; std::string_view case_name; std::size_t mismatched_lanes; std::size_t mismatched_bytes; };
inline constexpr std::array<MutationWitnessView, 79> kMutationWitnesses{{
  MutationWitnessView{"cross-lane-assignment", "manual-baseline", 36U, 24U},
  MutationWitnessView{"cross-lane-assignment", "poi-spiral", 33U, 0U},
  MutationWitnessView{"cross-lane-assignment", "invert-axis", 36U, 24U},
  MutationWitnessView{"cross-lane-assignment", "degree-axis", 24U, 24U},
  MutationWitnessView{"cross-lane-assignment", "relax-axis", 42U, 33U},
  MutationWitnessView{"df64-cmul-rr-owner", "manual-baseline", 48U, 48U},
  MutationWitnessView{"df64-cmul-rr-owner", "poi-spiral", 36U, 36U},
  MutationWitnessView{"df64-cmul-rr-owner", "root-mode", 36U, 36U},
  MutationWitnessView{"df64-cmul-rr-owner", "invert-axis", 48U, 48U},
  MutationWitnessView{"df64-cmul-rr-owner", "degree-axis", 27U, 27U},
  MutationWitnessView{"df64-cmul-rr-owner", "relax-axis", 42U, 42U},
  MutationWitnessView{"df64-cmul-ri-owner", "manual-baseline", 48U, 48U},
  MutationWitnessView{"df64-cmul-ri-owner", "poi-spiral", 36U, 36U},
  MutationWitnessView{"df64-cmul-ri-owner", "root-mode", 36U, 36U},
  MutationWitnessView{"df64-cmul-ri-owner", "invert-axis", 48U, 48U},
  MutationWitnessView{"df64-cmul-ri-owner", "degree-axis", 21U, 21U},
  MutationWitnessView{"df64-cmul-ri-owner", "relax-axis", 42U, 42U},
  MutationWitnessView{"transform-re-owner", "manual-baseline", 48U, 48U},
  MutationWitnessView{"transform-re-owner", "poi-spiral", 36U, 36U},
  MutationWitnessView{"transform-re-owner", "root-mode", 36U, 36U},
  MutationWitnessView{"transform-re-owner", "invert-axis", 48U, 48U},
  MutationWitnessView{"transform-re-owner", "degree-axis", 24U, 24U},
  MutationWitnessView{"transform-re-owner", "relax-axis", 45U, 45U},
  MutationWitnessView{"transform-im-owner", "manual-baseline", 48U, 48U},
  MutationWitnessView{"transform-im-owner", "poi-spiral", 36U, 36U},
  MutationWitnessView{"transform-im-owner", "root-mode", 36U, 36U},
  MutationWitnessView{"transform-im-owner", "invert-axis", 48U, 48U},
  MutationWitnessView{"transform-im-owner", "degree-axis", 21U, 21U},
  MutationWitnessView{"transform-im-owner", "relax-axis", 45U, 45U},
  MutationWitnessView{"cmul-call-materialization", "manual-baseline", 48U, 48U},
  MutationWitnessView{"cmul-call-materialization", "poi-spiral", 36U, 36U},
  MutationWitnessView{"cmul-call-materialization", "root-mode", 36U, 36U},
  MutationWitnessView{"cmul-call-materialization", "invert-axis", 48U, 48U},
  MutationWitnessView{"cmul-call-materialization", "degree-axis", 21U, 21U},
  MutationWitnessView{"cmul-call-materialization", "relax-axis", 45U, 45U},
  MutationWitnessView{"znr-call-materialization", "manual-baseline", 48U, 48U},
  MutationWitnessView{"znr-call-materialization", "poi-spiral", 36U, 3U},
  MutationWitnessView{"znr-call-materialization", "root-mode", 36U, 36U},
  MutationWitnessView{"znr-call-materialization", "invert-axis", 48U, 48U},
  MutationWitnessView{"znr-call-materialization", "degree-axis", 18U, 18U},
  MutationWitnessView{"znr-call-materialization", "relax-axis", 42U, 42U},
  MutationWitnessView{"transform-call-materialization", "manual-baseline", 48U, 48U},
  MutationWitnessView{"transform-call-materialization", "poi-spiral", 36U, 36U},
  MutationWitnessView{"transform-call-materialization", "root-mode", 36U, 36U},
  MutationWitnessView{"transform-call-materialization", "invert-axis", 48U, 48U},
  MutationWitnessView{"transform-call-materialization", "degree-axis", 21U, 21U},
  MutationWitnessView{"transform-call-materialization", "relax-axis", 45U, 45U},
  MutationWitnessView{"iteration-outer-bound", "manual-baseline", 48U, 48U},
  MutationWitnessView{"iteration-outer-bound", "poi-spiral", 3U, 3U},
  MutationWitnessView{"iteration-outer-bound", "root-mode", 36U, 36U},
  MutationWitnessView{"iteration-outer-bound", "invert-axis", 48U, 48U},
  MutationWitnessView{"iteration-outer-bound", "degree-axis", 27U, 27U},
  MutationWitnessView{"iteration-outer-bound", "relax-axis", 42U, 42U},
  MutationWitnessView{"iteration-power-bound", "manual-baseline", 48U, 48U},
  MutationWitnessView{"iteration-power-bound", "poi-spiral", 36U, 36U},
  MutationWitnessView{"iteration-power-bound", "root-mode", 36U, 36U},
  MutationWitnessView{"iteration-power-bound", "combined-mode", 45U, 45U},
  MutationWitnessView{"iteration-power-bound", "invert-axis", 48U, 48U},
  MutationWitnessView{"iteration-power-bound", "degree-axis", 18U, 18U},
  MutationWitnessView{"iteration-power-bound", "relax-axis", 45U, 45U},
  MutationWitnessView{"iteration-power-bound", "tolerance-axis", 30U, 30U},
  MutationWitnessView{"degree-control-axis", "manual-baseline", 48U, 48U},
  MutationWitnessView{"degree-control-axis", "degree-axis", 21U, 21U},
  MutationWitnessView{"degree-control-axis", "relax-axis", 45U, 45U},
  MutationWitnessView{"relaxation-control-axis", "manual-baseline", 48U, 48U},
  MutationWitnessView{"relaxation-control-axis", "poi-spiral", 36U, 36U},
  MutationWitnessView{"relaxation-control-axis", "invert-axis", 48U, 48U},
  MutationWitnessView{"relaxation-control-axis", "degree-axis", 18U, 18U},
  MutationWitnessView{"relaxation-control-axis", "relax-axis", 42U, 42U},
  MutationWitnessView{"tolerance-control-axis", "manual-baseline", 12U, 0U},
  MutationWitnessView{"tolerance-control-axis", "poi-spiral", 3U, 3U},
  MutationWitnessView{"tolerance-control-axis", "invert-axis", 24U, 0U},
  MutationWitnessView{"tolerance-control-axis", "degree-axis", 6U, 6U},
  MutationWitnessView{"tolerance-control-axis", "relax-axis", 42U, 33U},
  MutationWitnessView{"rotation-control-axis", "poi-spiral", 33U, 0U},
  MutationWitnessView{"rotation-control-axis", "degree-axis", 15U, 15U},
  MutationWitnessView{"rotation-control-axis", "relax-axis", 42U, 33U},
  MutationWitnessView{"invert-control-axis", "invert-axis", 48U, 48U},
  MutationWitnessView{"struct-POIData-declaration", "invert-axis", 48U, 48U},
}};
}
