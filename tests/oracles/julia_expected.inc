// Generated from the authenticated Julia JSON oracle.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string_view>

namespace julia_oracle {
inline constexpr std::string_view kProgramKey = "synth/julia:julia";
inline constexpr std::string_view kFactoryTextSha256 = "ed39921d1b85c59d7c86caa715c50987525bc9bcc6903a885810f133480545d6";
inline constexpr std::array<std::string_view, 21> kBindingNames{{
  "resolution", "tileOffset", "fullResolution", "time", "cReal", "cImag", "poi", "outputMode", "centerX", "centerY", "rotation", "iterations", "stripeFreq", "trapShape", "lightAngle", "cPath", "cSpeed", "cRadius", "invert", "zoomSpeed", "zoomDepth"
}};
struct BindingView { std::string_view name; std::string_view runtime_abi; std::string_view source_abi; }; using BindingAbiView = BindingView;
inline constexpr std::array<BindingView, 21> kBindingAbi{{
  BindingView{"resolution", "Vec2", "vec2"},
  BindingView{"tileOffset", "Vec2", "vec2"},
  BindingView{"fullResolution", "Vec2", "vec2"},
  BindingView{"time", "number", "float"},
  BindingView{"cReal", "number", "float"},
  BindingView{"cImag", "number", "float"},
  BindingView{"poi", "int32", "int"},
  BindingView{"outputMode", "int32", "int"},
  BindingView{"centerX", "number", "float"},
  BindingView{"centerY", "number", "float"},
  BindingView{"rotation", "number", "float"},
  BindingView{"iterations", "int32", "int"},
  BindingView{"stripeFreq", "number", "float"},
  BindingView{"trapShape", "int32", "int"},
  BindingView{"lightAngle", "number", "float"},
  BindingView{"cPath", "int32", "int"},
  BindingView{"cSpeed", "number", "float"},
  BindingView{"cRadius", "number", "float"},
  BindingView{"invert", "bool", "bool"},
  BindingView{"zoomSpeed", "number", "float"},
  BindingView{"zoomDepth", "number", "float"},
}};
struct SourceBindingView { std::string_view name; std::string_view source_abi; }; using SourceBindingAbiView = SourceBindingView;
inline constexpr std::array<SourceBindingView, 21> kSourceBindingAbi{{
  SourceBindingView{"resolution", "vec2"},
  SourceBindingView{"tileOffset", "vec2"},
  SourceBindingView{"fullResolution", "vec2"},
  SourceBindingView{"time", "float"},
  SourceBindingView{"cReal", "float"},
  SourceBindingView{"cImag", "float"},
  SourceBindingView{"poi", "int"},
  SourceBindingView{"outputMode", "int"},
  SourceBindingView{"centerX", "float"},
  SourceBindingView{"centerY", "float"},
  SourceBindingView{"rotation", "float"},
  SourceBindingView{"iterations", "int"},
  SourceBindingView{"stripeFreq", "float"},
  SourceBindingView{"trapShape", "int"},
  SourceBindingView{"lightAngle", "float"},
  SourceBindingView{"cPath", "int"},
  SourceBindingView{"cSpeed", "float"},
  SourceBindingView{"cRadius", "float"},
  SourceBindingView{"invert", "bool"},
  SourceBindingView{"zoomSpeed", "float"},
  SourceBindingView{"zoomDepth", "float"},
}};
struct BindingControl { std::array<float,2> resolution; std::array<float,2> tileOffset; std::array<float,2> fullResolution; double time; double cReal; double cImag; std::int32_t poi; std::int32_t outputMode; double centerX; double centerY; double rotation; std::int32_t iterations; double stripeFreq; std::int32_t trapShape; double lightAngle; std::int32_t cPath; double cSpeed; double cRadius; bool invert; double zoomSpeed; double zoomDepth; };
inline constexpr BindingControl kCase0Bindings{{5.0F, 4.0F}, {0.0F, 0.0F}, {5.0F, 4.0F}, 0.25, -0.123, 0.745, 0, 0, -0.1, 0.05, 0.0, 80, 0.0, 0, 30.0, 0, 0.0, 0.5, false, 0.0, 1.0};
inline constexpr std::array<std::uint32_t, 80> kCase0Input{{
  0x3d800000U, 0x3d638e39U, 0x3d3a2e8cU, 0x3f800000U, 0x3e800000U, 0x3ee38e39U, 0x3f0ba2e9U, 0x3f800000U, 0x3ee00000U, 0x3f555555U, 0x00000000U, 0x3f800000U, 0x3f200000U, 0x3e2aaaabU, 0x3f000000U, 0x3f800000U, 0x3f500000U, 0x3f0e38e4U, 0x3f800000U, 0x3f800000U, 0x3ec00000U, 0x3e2aaaabU, 0x3f22e8baU, 0x3f800000U, 0x3f100000U, 0x3f0e38e4U, 0x3dba2e8cU, 0x3f800000U, 0x3f400000U, 0x3f71c71cU, 0x3f1745d1U, 0x3f800000U, 0x3f700000U, 0x3e8e38e4U, 0x3d3a2e8cU, 0x3f800000U, 0x3d800000U, 0x3f2aaaabU, 0x3f0ba2e9U, 0x3f800000U, 0x3f300000U, 0x3e8e38e4U, 0x3e3a2e8cU, 0x3f800000U, 0x3f600000U, 0x3f2aaaabU, 0x3f2e8ba3U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x3e0ba2e9U, 0x3f800000U, 0x3e400000U, 0x3ec71c72U, 0x3f22e8baU, 0x3f800000U, 0x3ec00000U, 0x3f471c72U, 0x3dba2e8cU, 0x3f800000U, 0x3f800000U, 0x3ec71c72U, 0x3f45d174U, 0x3f800000U, 0x3e000000U, 0x3f471c72U, 0x3e68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3de38e39U, 0x3f3a2e8cU, 0x3f800000U, 0x3f000000U, 0x3f000000U, 0x3e3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3f638e39U, 0x3f2e8ba3U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 80> kCase0Expected{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 80> kCase0Rgba8{{
  0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U
}};
inline constexpr BindingControl kCase1Bindings{{4.0F, 5.0F}, {0.5F, -0.25F}, {4.0F, 5.0F}, 0.75, 0.28, 0.008, 0, 1, 0.0, 0.0, 12.0, 120, 0.0, 0, 60.0, 0, 0.0, 0.5, false, 0.0, 1.0};
inline constexpr std::array<std::uint32_t, 80> kCase1Input{{
  0x3e000000U, 0x3de38e39U, 0x3dba2e8cU, 0x3f800000U, 0x3ea00000U, 0x3f000000U, 0x3f1745d1U, 0x3f800000U, 0x3f000000U, 0x3f638e39U, 0x3d3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3e638e39U, 0x3f0ba2e9U, 0x3f800000U, 0x3ee00000U, 0x3e638e39U, 0x3f2e8ba3U, 0x3f800000U, 0x3f200000U, 0x3f1c71c7U, 0x3e0ba2e9U, 0x3f800000U, 0x3f500000U, 0x3f800000U, 0x3f22e8baU, 0x3f800000U, 0x3f800000U, 0x3eaaaaabU, 0x3dba2e8cU, 0x3f800000U, 0x3f400000U, 0x3eaaaaabU, 0x3e68ba2fU, 0x3f800000U, 0x3f700000U, 0x3f38e38eU, 0x3f3a2e8cU, 0x3f800000U, 0x3d800000U, 0x3d638e39U, 0x3e3a2e8cU, 0x3f800000U, 0x3e800000U, 0x3ee38e39U, 0x3f2e8ba3U, 0x3f800000U, 0x00000000U, 0x3ee38e39U, 0x3f51745dU, 0x3f800000U, 0x3e400000U, 0x3f555555U, 0x3e8ba2e9U, 0x3f800000U, 0x3ec00000U, 0x3e2aaaabU, 0x3f45d174U, 0x3f800000U, 0x3f100000U, 0x3f0e38e4U, 0x3e68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3f0e38e4U, 0x3eba2e8cU, 0x3f800000U, 0x3f000000U, 0x3f71c71cU, 0x3f5d1746U, 0x3f800000U, 0x3f300000U, 0x3e8e38e4U, 0x3ea2e8baU, 0x3f800000U, 0x3f600000U, 0x3f2aaaabU, 0x3f51745dU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 80> kCase1Expected{{
  0x3e01ca12U, 0x3e01ca12U, 0x3e01ca12U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3a02883aU, 0x3a02883aU, 0x3a02883aU, 0x3f800000U, 0x3ce51b89U, 0x3ce51b89U, 0x3ce51b89U, 0x3f800000U, 0x3bfa12b3U, 0x3bfa12b3U, 0x3bfa12b3U, 0x3f800000U, 0x3dbdc006U, 0x3dbdc006U, 0x3dbdc006U, 0x3f800000U, 0x3dcb2451U, 0x3dcb2451U, 0x3dcb2451U, 0x3f800000U, 0x3cc73571U, 0x3cc73571U, 0x3cc73571U, 0x3f800000U, 0x3d7792edU, 0x3d7792edU, 0x3d7792edU, 0x3f800000U, 0x3e90d2b4U, 0x3e90d2b4U, 0x3e90d2b4U, 0x3f800000U, 0x3c387e18U, 0x3c387e18U, 0x3c387e18U, 0x3f800000U, 0x3a34011aU, 0x3a34011aU, 0x3a34011aU, 0x3f800000U, 0x3d35bdb6U, 0x3d35bdb6U, 0x3d35bdb6U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3d8b0064U, 0x3d8b0064U, 0x3d8b0064U, 0x3f800000U, 0x3e149028U, 0x3e149028U, 0x3e149028U, 0x3f800000U, 0x3c9014a2U, 0x3c9014a2U, 0x3c9014a2U, 0x3f800000U, 0x37863802U, 0x37863802U, 0x37863802U, 0x3f800000U, 0x3e3d0b7dU, 0x3e3d0b7dU, 0x3e3d0b7dU, 0x3f800000U, 0x3e94a491U, 0x3e94a491U, 0x3e94a491U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 80> kCase1Rgba8{{
  32U, 32U, 32U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 7U, 7U, 7U, 255U, 2U, 2U, 2U, 255U, 24U, 24U, 24U, 255U, 25U, 25U, 25U, 255U, 6U, 6U, 6U, 255U, 15U, 15U, 15U, 255U, 72U, 72U, 72U, 255U, 3U, 3U, 3U, 255U, 0U, 0U, 0U, 255U, 11U, 11U, 11U, 255U, 0U, 0U, 0U, 255U, 17U, 17U, 17U, 255U, 37U, 37U, 37U, 255U, 4U, 4U, 4U, 255U, 0U, 0U, 0U, 255U, 47U, 47U, 47U, 255U, 74U, 74U, 74U, 255U
}};
inline constexpr BindingControl kCase2Bindings{{6.0F, 3.0F}, {0.0F, 0.0F}, {6.0F, 3.0F}, 1.5, 0.28, 0.008, 0, 2, 0.0, 0.0, 0.0, 90, 2.75, 1, 120.0, 0, 0.0, 0.5, false, 0.0, 1.0};
inline constexpr std::array<std::uint32_t, 72> kCase2Input{{
  0x3e400000U, 0x3e2aaaabU, 0x3e0ba2e9U, 0x3f800000U, 0x3ec00000U, 0x3f0e38e4U, 0x3f22e8baU, 0x3f800000U, 0x3f100000U, 0x3f71c71cU, 0x3dba2e8cU, 0x3f800000U, 0x3f400000U, 0x3e8e38e4U, 0x3f1745d1U, 0x3f800000U, 0x3f700000U, 0x3f2aaaabU, 0x3d3a2e8cU, 0x3f800000U, 0x3d800000U, 0x00000000U, 0x3f0ba2e9U, 0x3f800000U, 0x3f000000U, 0x3e8e38e4U, 0x3f3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3f2aaaabU, 0x3e3a2e8cU, 0x3f800000U, 0x3f600000U, 0x00000000U, 0x3f2e8ba3U, 0x3f800000U, 0x00000000U, 0x3ec71c72U, 0x3e0ba2e9U, 0x3f800000U, 0x3e400000U, 0x3f471c72U, 0x3f22e8baU, 0x3f800000U, 0x3ec00000U, 0x3de38e39U, 0x3dba2e8cU, 0x3f800000U, 0x3f500000U, 0x3ec71c72U, 0x3e8ba2e9U, 0x3f800000U, 0x3f800000U, 0x3f471c72U, 0x3f45d174U, 0x3f800000U, 0x3e000000U, 0x3de38e39U, 0x3e68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3f000000U, 0x3f3a2e8cU, 0x3f800000U, 0x3f000000U, 0x3f638e39U, 0x3e3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3e638e39U, 0x3f2e8ba3U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 72> kCase2Expected{{
  0x3f21db1aU, 0x3f21db1aU, 0x3f21db1aU, 0x3f800000U, 0x3f23e2c7U, 0x3f23e2c7U, 0x3f23e2c7U, 0x3f800000U, 0x3f0b44cfU, 0x3f0b44cfU, 0x3f0b44cfU, 0x3f800000U, 0x3f1e29a1U, 0x3f1e29a1U, 0x3f1e29a1U, 0x3f800000U, 0x3f25aa90U, 0x3f25aa90U, 0x3f25aa90U, 0x3f800000U, 0x3f191266U, 0x3f191266U, 0x3f191266U, 0x3f800000U, 0x3f151447U, 0x3f151447U, 0x3f151447U, 0x3f800000U, 0x3f1962fcU, 0x3f1962fcU, 0x3f1962fcU, 0x3f800000U, 0x3ef0267aU, 0x3ef0267aU, 0x3ef0267aU, 0x3f800000U, 0x3ef0267aU, 0x3ef0267aU, 0x3ef0267aU, 0x3f800000U, 0x3f1962fcU, 0x3f1962fcU, 0x3f1962fcU, 0x3f800000U, 0x3f151447U, 0x3f151447U, 0x3f151447U, 0x3f800000U, 0x3f191266U, 0x3f191266U, 0x3f191266U, 0x3f800000U, 0x3f25aa90U, 0x3f25aa90U, 0x3f25aa90U, 0x3f800000U, 0x3f1e29a1U, 0x3f1e29a1U, 0x3f1e29a1U, 0x3f800000U, 0x3f0b44cfU, 0x3f0b44cfU, 0x3f0b44cfU, 0x3f800000U, 0x3f23e2c7U, 0x3f23e2c7U, 0x3f23e2c7U, 0x3f800000U, 0x3f21db1aU, 0x3f21db1aU, 0x3f21db1aU, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 72> kCase2Rgba8{{
  161U, 161U, 161U, 255U, 163U, 163U, 163U, 255U, 139U, 139U, 139U, 255U, 158U, 158U, 158U, 255U, 165U, 165U, 165U, 255U, 152U, 152U, 152U, 255U, 148U, 148U, 148U, 255U, 153U, 153U, 153U, 255U, 120U, 120U, 120U, 255U, 120U, 120U, 120U, 255U, 153U, 153U, 153U, 255U, 148U, 148U, 148U, 255U, 152U, 152U, 152U, 255U, 165U, 165U, 165U, 255U, 158U, 158U, 158U, 255U, 139U, 139U, 139U, 255U, 163U, 163U, 163U, 255U, 161U, 161U, 161U, 255U
}};
inline constexpr BindingControl kCase3Bindings{{5.0F, 5.0F}, {-0.375F, 0.625F}, {5.0F, 5.0F}, 2.0, 0.0, 0.0, 7, 3, 0.1, -0.1, 0.0, 150, 0.0, 2, 210.0, 0, 0.0, 0.5, false, 1.25, 8.0};
inline constexpr std::array<std::uint32_t, 100> kCase3Input{{
  0x3e800000U, 0x3e638e39U, 0x3e3a2e8cU, 0x3f800000U, 0x3ee00000U, 0x3f1c71c7U, 0x3f2e8ba3U, 0x3f800000U, 0x3f200000U, 0x3f800000U, 0x3e0ba2e9U, 0x3f800000U, 0x3f500000U, 0x3eaaaaabU, 0x3f22e8baU, 0x3f800000U, 0x3f800000U, 0x3f38e38eU, 0x3dba2e8cU, 0x3f800000U, 0x3f100000U, 0x3eaaaaabU, 0x3f45d174U, 0x3f800000U, 0x3f400000U, 0x3f38e38eU, 0x3e68ba2fU, 0x3f800000U, 0x3f700000U, 0x3d638e39U, 0x3f3a2e8cU, 0x3f800000U, 0x3d800000U, 0x3ee38e39U, 0x3e3a2e8cU, 0x3f800000U, 0x3e800000U, 0x3f555555U, 0x3f2e8ba3U, 0x3f800000U, 0x3f600000U, 0x3ee38e39U, 0x3ea2e8baU, 0x3f800000U, 0x00000000U, 0x3f555555U, 0x3f51745dU, 0x3f800000U, 0x3e400000U, 0x3e2aaaabU, 0x3e8ba2e9U, 0x3f800000U, 0x3ec00000U, 0x3f0e38e4U, 0x3f45d174U, 0x3f800000U, 0x3f100000U, 0x3f71c71cU, 0x3e68ba2fU, 0x3f800000U, 0x3e000000U, 0x3f0e38e4U, 0x3f68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3f71c71cU, 0x3eba2e8cU, 0x3f800000U, 0x3f000000U, 0x3e8e38e4U, 0x3f5d1746U, 0x3f800000U, 0x3f300000U, 0x3f2aaaabU, 0x3ea2e8baU, 0x3f800000U, 0x3f600000U, 0x00000000U, 0x3f51745dU, 0x3f800000U, 0x3ee00000U, 0x3f2aaaabU, 0x3ee8ba2fU, 0x3f800000U, 0x3f200000U, 0x00000000U, 0x3f745d17U, 0x3f800000U, 0x3f500000U, 0x3ec71c72U, 0x3ed1745dU, 0x3f800000U, 0x3f800000U, 0x3f471c72U, 0x3f68ba2fU, 0x3f800000U, 0x3e000000U, 0x3de38e39U, 0x3eba2e8cU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 100> kCase3Expected{{
  0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f7ff7daU, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 100> kCase3Rgba8{{
  255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U
}};
inline constexpr BindingControl kCase4Bindings{{4.0F, 4.0F}, {0.0F, 0.0F}, {4.0F, 4.0F}, 3.25, -0.8, 0.156, 0, 4, -0.25, 0.01, -18.0, 64, 0.0, 0, 300.0, 0, 0.0, 0.5, false, 0.0, 2.0};
inline constexpr std::array<std::uint32_t, 64> kCase4Input{{
  0x3ea00000U, 0x3e8e38e4U, 0x3e68ba2fU, 0x3f800000U, 0x3f000000U, 0x3f2aaaabU, 0x3f3a2e8cU, 0x3f800000U, 0x3f300000U, 0x00000000U, 0x3e3a2e8cU, 0x3f800000U, 0x3f600000U, 0x3ec71c72U, 0x3f2e8ba3U, 0x3f800000U, 0x3f200000U, 0x3ec71c72U, 0x3f51745dU, 0x3f800000U, 0x3f500000U, 0x3f471c72U, 0x3e8ba2e9U, 0x3f800000U, 0x3f800000U, 0x3de38e39U, 0x3f45d174U, 0x3f800000U, 0x3e000000U, 0x3f000000U, 0x3e68ba2fU, 0x3f800000U, 0x3f700000U, 0x3f000000U, 0x3eba2e8cU, 0x3f800000U, 0x3d800000U, 0x3f638e39U, 0x3f5d1746U, 0x3f800000U, 0x3e800000U, 0x3e638e39U, 0x3ea2e8baU, 0x3f800000U, 0x3ee00000U, 0x3f1c71c7U, 0x3f51745dU, 0x3f800000U, 0x3e400000U, 0x3f1c71c7U, 0x3f745d17U, 0x3f800000U, 0x3ec00000U, 0x3f800000U, 0x3ed1745dU, 0x3f800000U, 0x3f100000U, 0x3eaaaaabU, 0x3f68ba2fU, 0x3f800000U, 0x3f400000U, 0x3f38e38eU, 0x3eba2e8cU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 64> kCase4Expected{{
  0x3f0e1ac1U, 0x3f0e1ac1U, 0x3f0e1ac1U, 0x3f800000U, 0x3f0ed7d6U, 0x3f0ed7d6U, 0x3f0ed7d6U, 0x3f800000U, 0x3f0f8befU, 0x3f0f8befU, 0x3f0f8befU, 0x3f800000U, 0x3f1032efU, 0x3f1032efU, 0x3f1032efU, 0x3f800000U, 0x3f0e934bU, 0x3f0e934bU, 0x3f0e934bU, 0x3f800000U, 0x3f0f8a2cU, 0x3f0f8a2cU, 0x3f0f8a2cU, 0x3f800000U, 0x3f1091c2U, 0x3f1091c2U, 0x3f1091c2U, 0x3f800000U, 0x3f11ad6dU, 0x3f11ad6dU, 0x3f11ad6dU, 0x3f800000U, 0x3f0f1303U, 0x3f0f1303U, 0x3f0f1303U, 0x3f800000U, 0x3f1043d8U, 0x3f1043d8U, 0x3f1043d8U, 0x3f800000U, 0x3f1199e0U, 0x3f1199e0U, 0x3f1199e0U, 0x3f800000U, 0x3f131c12U, 0x3f131c12U, 0x3f131c12U, 0x3f800000U, 0x3f0f9598U, 0x3f0f9598U, 0x3f0f9598U, 0x3f800000U, 0x3f110378U, 0x3f110378U, 0x3f110378U, 0x3f800000U, 0x3f12ac44U, 0x3f12ac44U, 0x3f12ac44U, 0x3f800000U, 0x3f149ac9U, 0x3f149ac9U, 0x3f149ac9U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 64> kCase4Rgba8{{
  142U, 142U, 142U, 255U, 142U, 142U, 142U, 255U, 143U, 143U, 143U, 255U, 144U, 144U, 144U, 255U, 142U, 142U, 142U, 255U, 143U, 143U, 143U, 255U, 144U, 144U, 144U, 255U, 145U, 145U, 145U, 255U, 143U, 143U, 143U, 255U, 144U, 144U, 144U, 255U, 145U, 145U, 145U, 255U, 147U, 147U, 147U, 255U, 143U, 143U, 143U, 255U, 144U, 144U, 144U, 255U, 146U, 146U, 146U, 255U, 148U, 148U, 148U, 255U
}};
inline constexpr BindingControl kCase5Bindings{{4.0F, 3.0F}, {0.0F, 0.0F}, {4.0F, 3.0F}, 0.5, 0.0, 0.0, 0, 0, 0.3, 0.4, 0.0, 64, 0.0, 0, 45.0, 2, 0.75, 0.55, false, 0.0, 1.0};
inline constexpr std::array<std::uint32_t, 48> kCase5Input{{
  0x3ec00000U, 0x3eaaaaabU, 0x3e8ba2e9U, 0x3f800000U, 0x3f100000U, 0x3f38e38eU, 0x3f45d174U, 0x3f800000U, 0x3f400000U, 0x3d638e39U, 0x3e68ba2fU, 0x3f800000U, 0x3f700000U, 0x3ee38e39U, 0x3f3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3ee38e39U, 0x3f5d1746U, 0x3f800000U, 0x3f600000U, 0x3f555555U, 0x3ea2e8baU, 0x3f800000U, 0x00000000U, 0x3e2aaaabU, 0x3f51745dU, 0x3f800000U, 0x3e400000U, 0x3f0e38e4U, 0x3e8ba2e9U, 0x3f800000U, 0x3f800000U, 0x3f0e38e4U, 0x3ed1745dU, 0x3f800000U, 0x3e000000U, 0x3f71c71cU, 0x3f68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3e8e38e4U, 0x3eba2e8cU, 0x3f800000U, 0x3f000000U, 0x3f2aaaabU, 0x3f5d1746U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 48> kCase5Expected{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3db4ccd1U, 0x3db4ccd1U, 0x3db4ccd1U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3e435eaaU, 0x3e435eaaU, 0x3e435eaaU, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 48> kCase5Rgba8{{
  0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 23U, 23U, 23U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 49U, 49U, 49U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U
}};
inline constexpr BindingControl kCase6Bindings{{3.0F, 4.0F}, {0.0F, 0.0F}, {3.0F, 4.0F}, 1.1, -0.7455, 0.113, 0, 1, 0.0, 0.0, 25.0, 96, 0.0, 0, 90.0, 0, 0.0, 0.5, true, 0.0, 2.0};
inline constexpr std::array<std::uint32_t, 48> kCase6Input{{
  0x3ee00000U, 0x3ec71c72U, 0x3ea2e8baU, 0x3f800000U, 0x3f200000U, 0x3f471c72U, 0x3f51745dU, 0x3f800000U, 0x3f500000U, 0x3de38e39U, 0x3e8ba2e9U, 0x3f800000U, 0x3f400000U, 0x3f000000U, 0x3f68ba2fU, 0x3f800000U, 0x3f700000U, 0x3f638e39U, 0x3eba2e8cU, 0x3f800000U, 0x3d800000U, 0x3e638e39U, 0x3f5d1746U, 0x3f800000U, 0x00000000U, 0x3f1c71c7U, 0x3ee8ba2fU, 0x3f800000U, 0x3e400000U, 0x3f800000U, 0x3f745d17U, 0x3f800000U, 0x3ec00000U, 0x3eaaaaabU, 0x3ed1745dU, 0x3f800000U, 0x3ea00000U, 0x3f38e38eU, 0x00000000U, 0x3f800000U, 0x3f000000U, 0x3d638e39U, 0x3f000000U, 0x3f800000U, 0x3f300000U, 0x3ee38e39U, 0x3f800000U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 48> kCase6Expected{{
  0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 48> kCase6Rgba8{{
  255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U
}};
inline constexpr BindingControl kCase7Bindings{{3.0F, 3.0F}, {0.25F, -0.5F}, {3.0F, 3.0F}, 0.9, 0.0, 0.0, 0, 3, 0.0, 0.0, -12.0, 72, 0.0, 1, 180.0, 1, 1.1, 0.4, false, 0.8, 3.0};
inline constexpr std::array<std::uint32_t, 36> kCase7Input{{
  0x3f000000U, 0x3ee38e39U, 0x3eba2e8cU, 0x3f800000U, 0x3f300000U, 0x3f555555U, 0x3f5d1746U, 0x3f800000U, 0x3f600000U, 0x3e2aaaabU, 0x3ea2e8baU, 0x3f800000U, 0x3f500000U, 0x3f0e38e4U, 0x3f745d17U, 0x3f800000U, 0x3f800000U, 0x3f71c71cU, 0x3ed1745dU, 0x3f800000U, 0x3e000000U, 0x3e8e38e4U, 0x3f68ba2fU, 0x3f800000U, 0x3d800000U, 0x3f2aaaabU, 0x3f000000U, 0x3f800000U, 0x3e800000U, 0x00000000U, 0x3f800000U, 0x3f800000U, 0x3ee00000U, 0x3ec71c72U, 0x3ee8ba2fU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 36> kCase7Expected{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 36> kCase7Rgba8{{
  0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U
}};
inline constexpr BindingControl kCase8Bindings{{1.0F, 1.0F}, {0.0F, 0.0F}, {1.0F, 1.0F}, 0.0, 0.0, 0.0, 0, 0, 0.0, 0.0, 0.0, 1, 0.0, 0, 45.0, 0, 0.0, 0.5, false, 0.0, 1.0};
inline constexpr std::array<std::uint32_t, 4> kCase8Input{{
  0x3f100000U, 0x3f000000U, 0x3ed1745dU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 4> kCase8Expected{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 4> kCase8Rgba8{{
  0U, 0U, 0U, 255U
}};
inline constexpr BindingControl kCase9Bindings{{1.0F, 1.0F}, {0.0F, 0.0F}, {1.0F, 1.0F}, 6.4456087906019786, 0.7145556327222278, 0.18602843191149376, 0, 3, -0.5526962232665849, -0.20907021993982378, -24.482864887566052, 1000, 0.0, 0, 284.247223381942, 3, 1.1909674250499735, 0.8099422763590567, false, 0.0, 4.561745525235716};
inline constexpr std::array<std::uint32_t, 4> kCase9Input{{
  0x3f700000U, 0x3f555555U, 0x3f2e8ba3U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 4> kCase9Expected{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 4> kCase9Rgba8{{
  0U, 0U, 0U, 255U
}};
inline constexpr BindingControl kCase10Bindings{{1.0F, 1.0F}, {0.0F, 0.0F}, {1.0F, 1.0F}, 6.4456087906019786, 0.7145556327222278, 0.18602843191149376, 0, 3, -0.5526962232665849, -0.20907021993982378, -24.482864887566052, 1001, 0.0, 0, 284.247223381942, 3, 1.1909674250499735, 0.8099422763590567, false, 0.0, 4.561745525235716};
inline constexpr std::array<std::uint32_t, 4> kCase10Input{{
  0x3f700000U, 0x3f555555U, 0x3f2e8ba3U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 4> kCase10Expected{{
  0x3f56a8efU, 0x3f56a8efU, 0x3f56a8efU, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 4> kCase10Rgba8{{
  214U, 214U, 214U, 255U
}};
inline constexpr BindingControl kCase11Bindings{{2.0F, 2.0F}, {0.0F, 0.0F}, {2.0F, 2.0F}, 0.25, 0.0, 0.0, 0, 1, 0.0, 0.0, 0.0, 64, 0.0, 0, 45.0, 3, 0.5, 0.5, false, 0.0, 1.0};
inline constexpr std::array<std::uint32_t, 16> kCase11Input{{
  0x3f300000U, 0x3f1c71c7U, 0x3f000000U, 0x3f800000U, 0x3f600000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f38e38eU, 0x3d3a2e8cU, 0x3f800000U, 0x3e000000U, 0x3d638e39U, 0x3f0ba2e9U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 16> kCase11Expected{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 16> kCase11Rgba8{{
  0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U
}};
inline constexpr BindingControl kCase12Bindings{{2.0F, 2.0F}, {0.0F, 0.0F}, {2.0F, 2.0F}, 0.5, 0.2, -0.3, 99, 1, 0.0, 0.0, 0.0, 64, 0.0, 0, 45.0, 0, 0.0, 0.5, false, 0.0, 1.0};
inline constexpr std::array<std::uint32_t, 16> kCase12Input{{
  0x3f400000U, 0x3f2aaaabU, 0x3f0ba2e9U, 0x3f800000U, 0x3f700000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x3f471c72U, 0x3dba2e8cU, 0x3f800000U, 0x3e400000U, 0x3de38e39U, 0x3f1745d1U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 16> kCase12Expected{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 16> kCase12Rgba8{{
  0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U
}};
inline constexpr BindingControl kCase13Bindings{{1.0F, 1.0F}, {0.0F, 0.0F}, {1.0F, 1.0F}, 0.0, 0.0, 0.0, 0, 3, 0.0, 0.0, 0.0, 50, 0.0, 0, 45.0, 0, 0.0, 0.5, false, 0.0, 1.0};
inline constexpr std::array<std::uint32_t, 4> kCase13Input{{
  0x3f500000U, 0x3f38e38eU, 0x3f1745d1U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 4> kCase13Expected{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 4> kCase13Rgba8{{
  0U, 0U, 0U, 255U
}};
inline constexpr BindingControl kCase14Bindings{{5.0F, 4.0F}, {0.0F, 0.0F}, {5.0F, 4.0F}, 0.25, -0.123, 0.745, 0, 5, -0.1, 0.05, 0.0, 80, 0.0, 0, 30.0, 0, 0.0, 0.5, false, 0.0, 1.0};
inline constexpr std::array<std::uint32_t, 80> kCase14Input{{
  0x3d800000U, 0x3d638e39U, 0x3d3a2e8cU, 0x3f800000U, 0x3e800000U, 0x3ee38e39U, 0x3f0ba2e9U, 0x3f800000U, 0x3ee00000U, 0x3f555555U, 0x00000000U, 0x3f800000U, 0x3f200000U, 0x3e2aaaabU, 0x3f000000U, 0x3f800000U, 0x3f500000U, 0x3f0e38e4U, 0x3f800000U, 0x3f800000U, 0x3ec00000U, 0x3e2aaaabU, 0x3f22e8baU, 0x3f800000U, 0x3f100000U, 0x3f0e38e4U, 0x3dba2e8cU, 0x3f800000U, 0x3f400000U, 0x3f71c71cU, 0x3f1745d1U, 0x3f800000U, 0x3f700000U, 0x3e8e38e4U, 0x3d3a2e8cU, 0x3f800000U, 0x3d800000U, 0x3f2aaaabU, 0x3f0ba2e9U, 0x3f800000U, 0x3f300000U, 0x3e8e38e4U, 0x3e3a2e8cU, 0x3f800000U, 0x3f600000U, 0x3f2aaaabU, 0x3f2e8ba3U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x3e0ba2e9U, 0x3f800000U, 0x3e400000U, 0x3ec71c72U, 0x3f22e8baU, 0x3f800000U, 0x3ec00000U, 0x3f471c72U, 0x3dba2e8cU, 0x3f800000U, 0x3f800000U, 0x3ec71c72U, 0x3f45d174U, 0x3f800000U, 0x3e000000U, 0x3f471c72U, 0x3e68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3de38e39U, 0x3f3a2e8cU, 0x3f800000U, 0x3f000000U, 0x3f000000U, 0x3e3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3f638e39U, 0x3f2e8ba3U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 80> kCase14Expected{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 80> kCase14Rgba8{{
  0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U
}};
inline constexpr BindingControl kCase15Bindings{{4.0F, 3.0F}, {0.0F, 0.0F}, {4.0F, 3.0F}, 1.5, 0.28, 0.008, 0, 3, 0.0, 0.0, 0.0, 90, 0.0, 9, 120.0, 0, 0.0, 0.5, false, 0.0, 1.0};
inline constexpr std::array<std::uint32_t, 48> kCase15Input{{
  0x3e400000U, 0x3e2aaaabU, 0x3e0ba2e9U, 0x3f800000U, 0x3ec00000U, 0x3f0e38e4U, 0x3f22e8baU, 0x3f800000U, 0x3f100000U, 0x3f71c71cU, 0x3dba2e8cU, 0x3f800000U, 0x3f400000U, 0x3e8e38e4U, 0x3f1745d1U, 0x3f800000U, 0x3f000000U, 0x3e8e38e4U, 0x3f3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3f2aaaabU, 0x3e3a2e8cU, 0x3f800000U, 0x3f600000U, 0x00000000U, 0x3f2e8ba3U, 0x3f800000U, 0x00000000U, 0x3ec71c72U, 0x3e0ba2e9U, 0x3f800000U, 0x3f500000U, 0x3ec71c72U, 0x3e8ba2e9U, 0x3f800000U, 0x3f800000U, 0x3f471c72U, 0x3f45d174U, 0x3f800000U, 0x3e000000U, 0x3de38e39U, 0x3e68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3f000000U, 0x3f3a2e8cU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 48> kCase15Expected{{
  0x3f6f5fecU, 0x3f6f5fecU, 0x3f6f5fecU, 0x3f800000U, 0x3f7d7166U, 0x3f7d7166U, 0x3f7d7166U, 0x3f800000U, 0x3f7abb76U, 0x3f7abb76U, 0x3f7abb76U, 0x3f800000U, 0x3f7eaf3dU, 0x3f7eaf3dU, 0x3f7eaf3dU, 0x3f800000U, 0x3f7ec631U, 0x3f7ec631U, 0x3f7ec631U, 0x3f800000U, 0x3f7fa01aU, 0x3f7fa01aU, 0x3f7fa01aU, 0x3f800000U, 0x3f7fa01aU, 0x3f7fa01aU, 0x3f7fa01aU, 0x3f800000U, 0x3f7ec631U, 0x3f7ec631U, 0x3f7ec631U, 0x3f800000U, 0x3f7eaf3dU, 0x3f7eaf3dU, 0x3f7eaf3dU, 0x3f800000U, 0x3f7abb76U, 0x3f7abb76U, 0x3f7abb76U, 0x3f800000U, 0x3f7d7166U, 0x3f7d7166U, 0x3f7d7166U, 0x3f800000U, 0x3f6f5fecU, 0x3f6f5fecU, 0x3f6f5fecU, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 48> kCase15Rgba8{{
  238U, 238U, 238U, 255U, 252U, 252U, 252U, 255U, 250U, 250U, 250U, 255U, 254U, 254U, 254U, 255U, 254U, 254U, 254U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 255U, 254U, 254U, 254U, 255U, 254U, 254U, 254U, 255U, 250U, 250U, 250U, 255U, 252U, 252U, 252U, 255U, 238U, 238U, 238U, 255U
}};
inline constexpr BindingControl kCase16Bindings{{4.0F, 3.0F}, {0.0F, 0.0F}, {4.0F, 3.0F}, 0.5, 0.0, 0.0, 0, 0, 0.3, 0.4, 0.0, 64, 0.0, 0, 45.0, 9, 0.75, 0.55, false, 0.0, 1.0};
inline constexpr std::array<std::uint32_t, 48> kCase16Input{{
  0x3ec00000U, 0x3eaaaaabU, 0x3e8ba2e9U, 0x3f800000U, 0x3f100000U, 0x3f38e38eU, 0x3f45d174U, 0x3f800000U, 0x3f400000U, 0x3d638e39U, 0x3e68ba2fU, 0x3f800000U, 0x3f700000U, 0x3ee38e39U, 0x3f3a2e8cU, 0x3f800000U, 0x3f300000U, 0x3ee38e39U, 0x3f5d1746U, 0x3f800000U, 0x3f600000U, 0x3f555555U, 0x3ea2e8baU, 0x3f800000U, 0x00000000U, 0x3e2aaaabU, 0x3f51745dU, 0x3f800000U, 0x3e400000U, 0x3f0e38e4U, 0x3e8ba2e9U, 0x3f800000U, 0x3f800000U, 0x3f0e38e4U, 0x3ed1745dU, 0x3f800000U, 0x3e000000U, 0x3f71c71cU, 0x3f68ba2fU, 0x3f800000U, 0x3ea00000U, 0x3e8e38e4U, 0x3eba2e8cU, 0x3f800000U, 0x3f000000U, 0x3f2aaaabU, 0x3f5d1746U, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 48> kCase16Expected{{
  0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 48> kCase16Rgba8{{
  0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U, 0U, 0U, 0U, 255U
}};
inline constexpr BindingControl kCase17Bindings{{7.0F, 3.0F}, {0.375F, -0.125F}, {7.0F, 3.0F}, 1.25, -0.4, 0.6, 0, 4, 0.125, -0.2, 33.0, 73, 0.0, 0, 271.0, 0, 0.0, 0.5, false, 0.0, 2.5};
inline constexpr std::array<std::uint32_t, 84> kCase17Input{{
  0x3f600000U, 0x3f471c72U, 0x3f22e8baU, 0x3f800000U, 0x00000000U, 0x3de38e39U, 0x3dba2e8cU, 0x3f800000U, 0x3e400000U, 0x3f000000U, 0x3f1745d1U, 0x3f800000U, 0x3ec00000U, 0x3f638e39U, 0x3d3a2e8cU, 0x3f800000U, 0x3f100000U, 0x3e638e39U, 0x3f0ba2e9U, 0x3f800000U, 0x3f400000U, 0x3f1c71c7U, 0x00000000U, 0x3f800000U, 0x3f700000U, 0x3f800000U, 0x3f000000U, 0x3f800000U, 0x3e000000U, 0x3f638e39U, 0x3e3a2e8cU, 0x3f800000U, 0x3ea00000U, 0x3e638e39U, 0x3f2e8ba3U, 0x3f800000U, 0x3f000000U, 0x3f1c71c7U, 0x3e0ba2e9U, 0x3f800000U, 0x3f300000U, 0x3f800000U, 0x3f22e8baU, 0x3f800000U, 0x3f600000U, 0x3eaaaaabU, 0x3dba2e8cU, 0x3f800000U, 0x00000000U, 0x3f38e38eU, 0x3f1745d1U, 0x3f800000U, 0x3e400000U, 0x3d638e39U, 0x3d3a2e8cU, 0x3f800000U, 0x3ee00000U, 0x3f800000U, 0x3f45d174U, 0x3f800000U, 0x3f200000U, 0x3eaaaaabU, 0x3e68ba2fU, 0x3f800000U, 0x3f500000U, 0x3f38e38eU, 0x3f3a2e8cU, 0x3f800000U, 0x3f800000U, 0x3d638e39U, 0x3e3a2e8cU, 0x3f800000U, 0x3e000000U, 0x3ee38e39U, 0x3f2e8ba3U, 0x3f800000U, 0x3ea00000U, 0x3f555555U, 0x3e0ba2e9U, 0x3f800000U, 0x3f000000U, 0x3e2aaaabU, 0x3f22e8baU, 0x3f800000U
}};
inline constexpr std::array<std::uint32_t, 84> kCase17Expected{{
  0x3f2c9ba5U, 0x3f2c9ba5U, 0x3f2c9ba5U, 0x3f800000U, 0x3f2935e8U, 0x3f2935e8U, 0x3f2935e8U, 0x3f800000U, 0x3f273cecU, 0x3f273cecU, 0x3f273cecU, 0x3f800000U, 0x3f260337U, 0x3f260337U, 0x3f260337U, 0x3f800000U, 0x3f2523b5U, 0x3f2523b5U, 0x3f2523b5U, 0x3f800000U, 0x3f2459b4U, 0x3f2459b4U, 0x3f2459b4U, 0x3f800000U, 0x3f236348U, 0x3f236348U, 0x3f236348U, 0x3f800000U, 0x3f31c389U, 0x3f31c389U, 0x3f31c389U, 0x3f800000U, 0x3f2bdf58U, 0x3f2bdf58U, 0x3f2bdf58U, 0x3f800000U, 0x3f28e0bdU, 0x3f28e0bdU, 0x3f28e0bdU, 0x3f800000U, 0x3f272323U, 0x3f272323U, 0x3f272323U, 0x3f800000U, 0x3f25fe8aU, 0x3f25fe8aU, 0x3f25fe8aU, 0x3f800000U, 0x3f251bb1U, 0x3f251bb1U, 0x3f251bb1U, 0x3f800000U, 0x3f2447aeU, 0x3f2447aeU, 0x3f2447aeU, 0x3f800000U, 0x3f364193U, 0x3f364193U, 0x3f364193U, 0x3f800000U, 0x3f2e38afU, 0x3f2e38afU, 0x3f2e38afU, 0x3f800000U, 0x3f2a4fd5U, 0x3f2a4fd5U, 0x3f2a4fd5U, 0x3f800000U, 0x3f282f73U, 0x3f282f73U, 0x3f282f73U, 0x3f800000U, 0x3f26de62U, 0x3f26de62U, 0x3f26de62U, 0x3f800000U, 0x3f25f56cU, 0x3f25f56cU, 0x3f25f56cU, 0x3f800000U, 0x3f254d26U, 0x3f254d26U, 0x3f254d26U, 0x3f800000U
}};
inline constexpr std::array<std::uint8_t, 84> kCase17Rgba8{{
  172U, 172U, 172U, 255U, 169U, 169U, 169U, 255U, 167U, 167U, 167U, 255U, 165U, 165U, 165U, 255U, 164U, 164U, 164U, 255U, 164U, 164U, 164U, 255U, 163U, 163U, 163U, 255U, 177U, 177U, 177U, 255U, 171U, 171U, 171U, 255U, 168U, 168U, 168U, 255U, 166U, 166U, 166U, 255U, 165U, 165U, 165U, 255U, 164U, 164U, 164U, 255U, 164U, 164U, 164U, 255U, 182U, 182U, 182U, 255U, 174U, 174U, 174U, 255U, 170U, 170U, 170U, 255U, 168U, 168U, 168U, 255U, 166U, 166U, 166U, 255U, 165U, 165U, 165U, 255U, 165U, 165U, 165U, 255U
}};
struct CaseView { std::string_view name; std::size_t width; std::size_t height; BindingControl bindings; std::span<const std::uint32_t> input; std::string_view input_f32_sha256; std::span<const std::uint32_t> expected; std::string_view expected_f32_sha256; std::span<const std::uint8_t> rgba8; std::string_view expected_rgba8_sha256; std::string_view alpha_f32_word; std::uint8_t alpha_rgba8_byte; std::string_view output_alpha_f32_word; std::uint8_t output_alpha_rgba8_byte; bool input_immutable_exact_bits; };
inline constexpr std::array<CaseView, 18> kCases{{
  CaseView{"manual-smooth", 5U, 4U, kCase0Bindings, kCase0Input, "04ec1b2e75cba0252250ddb7c2015a6866b7b62c6073d4fbf00edda49a77a1cb", kCase0Expected, "68ce3ccc4770b082b0ca69e38a2dff21faf781a4627e582ab05cc611e6ad5508", kCase0Rgba8, "b1afc3dbe46c96d9627c89a90caea13bd4d5768cdc9929dcddb759fc39b5d1fa", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"manual-distance-tile", 4U, 5U, kCase1Bindings, kCase1Input, "e0f86664cee61f34fcde6f54e7f5409e68d9383f86fbdd328df64321f537f05c", kCase1Expected, "2420f5e9856fb635232e4025ed4d56c7ff00f46a9ff392992883f9db311a0e6a", kCase1Rgba8, "6350bb261836336ff3b357cbeb7a1c3438c0ffa2c093efe1316ce3d1e8b98a04", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"manual-stripe", 6U, 3U, kCase2Bindings, kCase2Input, "696e64435afb893bf92064201a0a8317209ec4e05cc93d73931087777bc23847", kCase2Expected, "1194a269b70b781d38398a4f2c46e4dbf18061dfe8d9e4a1c26fc401a7b76f85", kCase2Rgba8, "cc4cb3f21a2715c0383b0a024d1b613eff3354f064dd5d763e61c57ea93589f3", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"poi-trap", 5U, 5U, kCase3Bindings, kCase3Input, "ac3df82128d83e2e89260464cfbb004457912bb155a5eb972f74717e3907c7e5", kCase3Expected, "75352c0017ab1e77ff8eb69b000c8758e33ea992d501ee74b15034f5a84a997f", kCase3Rgba8, "da6f14970ce356ce01a5b340291e9d8b2652eb63fbf8f328ca6a87a727fde4d9", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"manual-normal", 4U, 4U, kCase4Bindings, kCase4Input, "0cf32eaaf33b72ee8475938c52a05f7a3b757296f4532fb63743948faf9fec50", kCase4Expected, "a48b5c5dfb26c1525ec288ea6dd6f09734e204437fde85b0d1681ac4733c1dca", kCase4Rgba8, "7db70c0ff3cb9d1760bcbe349ff2f3cd4e374680720d96dffaf52b65fb48ac7a", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"animated-circle", 4U, 3U, kCase5Bindings, kCase5Input, "354b8e6e312ddf00b3d4bc2f734c506ad24a9c0c48df6ba6f23890443119040f", kCase5Expected, "e24ee7903037973363d2ac465310ae2ad5f67321352811f8a40e03904c69bb83", kCase5Rgba8, "f5656fbf77f179e0b98440ab8e06bd87debbc5bdddf60d661e395bef58ee1899", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"invert-output", 3U, 4U, kCase6Bindings, kCase6Input, "58ab9329ff6a09a1179c3580f8a787da461583678ecc6dee47f24c000fed568d", kCase6Expected, "c90489868a1a64a74239d5331b18d608ef69e28579f36f3ae1949cfe7354907a", kCase6Rgba8, "80a76a18acf8cb64fec3a659ffc4bab4a87cd9a6fde4dab2161a8751d136c9d2", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"animated-lissajous", 3U, 3U, kCase7Bindings, kCase7Input, "a0c51cd0aa9ad8a182b9d62fd6205b2339e03f1430b49cb37e56a6d70fec75e3", kCase7Expected, "8657f768505e95acfcb2802903768a6bf4e72e408ddea917bc9780784ffd2c44", kCase7Rgba8, "d574fbbbc44a56d8ec9bf06a4221e0c975b101e434c87e030572be6660dfb538", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"iterations-min", 1U, 1U, kCase8Bindings, kCase8Input, "9ab27ec849e1d15f5c1b80a7c88f41b3be7c10af6e8fdf00649fd5a45f183c76", kCase8Expected, "7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e", kCase8Rgba8, "e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"iterations-max", 1U, 1U, kCase9Bindings, kCase9Input, "3e528f72f53b49516bb6c44bdd3db8f688f2c0105fa1120e8ea941ca5d88ead2", kCase9Expected, "7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e", kCase9Rgba8, "e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"iterations-clamp-1001", 1U, 1U, kCase10Bindings, kCase10Input, "3e528f72f53b49516bb6c44bdd3db8f688f2c0105fa1120e8ea941ca5d88ead2", kCase10Expected, "e59c766c5f4c4faface8b7b5e30bafb20c6d10c89c12aba22784010e24fd1b67", kCase10Rgba8, "118a1615c6cfc6ba1f8f9c5f3a4c07e4f79edd70d13f56c086d7f0c2a655e66b", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"bulb-path", 2U, 2U, kCase11Bindings, kCase11Input, "eaa3484acd7fa41d0ad4941309bab6374f222c210b17764fb521d5cf4eefcb7f", kCase11Expected, "9ba3b531624710dece54456c2e5cb1cb31d7df8cfb6fee2b1180d0cb791ea049", kCase11Rgba8, "cc0fa51d4d0a97b664030be5052f3b2b69a1267f89ace4c9bbc65007566725df", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"poi-fallback", 2U, 2U, kCase12Bindings, kCase12Input, "7b8fcf38d596b67f0caf52ff4ba76e5a14213cae87d9ee2d7ba8ea354aa19b2d", kCase12Expected, "9ba3b531624710dece54456c2e5cb1cb31d7df8cfb6fee2b1180d0cb791ea049", kCase12Rgba8, "cc0fa51d4d0a97b664030be5052f3b2b69a1267f89ace4c9bbc65007566725df", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"period-convergence", 1U, 1U, kCase13Bindings, kCase13Input, "df5b7da9a846298cb6d8132039eef63d490145aec049791b61256d076cde4877", kCase13Expected, "7ab8f6c26e4f9862c95a18c8e5c50403eeb64d8869fbbf9a7a6397d9a63b7b0e", kCase13Rgba8, "e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"fallback-output-mode", 5U, 4U, kCase14Bindings, kCase14Input, "04ec1b2e75cba0252250ddb7c2015a6866b7b62c6073d4fbf00edda49a77a1cb", kCase14Expected, "68ce3ccc4770b082b0ca69e38a2dff21faf781a4627e582ab05cc611e6ad5508", kCase14Rgba8, "b1afc3dbe46c96d9627c89a90caea13bd4d5768cdc9929dcddb759fc39b5d1fa", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"fallback-trap-shape", 4U, 3U, kCase15Bindings, kCase15Input, "a099727fbe3dc3ca104ec1229bf5ad6d2c537046798fd6a199a6f4db641e9fe3", kCase15Expected, "e1b2ea7b0afff299f71fe14a7e7030191d30ae0b6aa94d6247c0d9480ee37cc3", kCase15Rgba8, "7b40c20788a3091bcce9e5ad651c7629b9302cfc25d9f35063b62bb8121e311d", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"fallback-c-path", 4U, 3U, kCase16Bindings, kCase16Input, "354b8e6e312ddf00b3d4bc2f734c506ad24a9c0c48df6ba6f23890443119040f", kCase16Expected, "8cea1b2ba74e80909c56b26a87e7d02eee4517266ae0ab2f34d8fa601d4e2ba8", kCase16Rgba8, "937d497ff9439479f9a77994b703e6ebced8ca0b9b3c66640567d267c5387a75", "0x3f800000", 255U, "0x3f800000", 255U, true},
  CaseView{"non-square-f32-transform", 7U, 3U, kCase17Bindings, kCase17Input, "6347d28706b4fa2aaa32f7e6ffb6ad011ee58c9937806df40040149fe5dc2a8f", kCase17Expected, "d87a4033d8f1c820c25ea77bf66190fe4cead0a837704e9eb2acd2942dcdbf59", kCase17Rgba8, "7f71dc59b8540f092d688fd38421ef3d240c09f4490fd47e175f3cce8d171117", "0x3f800000", 255U, "0x3f800000", 255U, true},
}};
inline constexpr std::array<std::uint32_t, 4> kDiagnosticCanonicalF32{{0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U}};
inline constexpr std::array<std::uint32_t, 4> kDiagnosticInstrumentedF32{{0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U}};
inline constexpr std::array<std::uint8_t, 4> kDiagnosticCanonicalRgba8{{0U, 0U, 0U, 255U}};
inline constexpr std::array<std::uint8_t, 4> kDiagnosticInstrumentedRgba8{{0U, 0U, 0U, 255U}};
// diagnostic_witnesses are authenticated below.
struct DiagnosticWitnessView { std::string_view name; std::string_view source_anchor; std::string_view replacement; std::string_view anchor_sha256; std::string_view replacement_sha256; std::string_view instrumented_factory_sha256; std::size_t anchor_occurrence_count; std::size_t period_hit_count; std::span<const std::uint32_t> canonical_f32; std::span<const std::uint32_t> instrumented_f32; std::span<const std::uint8_t> canonical_rgba8; std::span<const std::uint8_t> instrumented_rgba8; };
inline constexpr std::array<DiagnosticWitnessView, 1> kDiagnosticWitnesses{{
  DiagnosticWitnessView{"period-convergence", "else if (Math.hypot(reHigh - slowX, imHigh - slowY) < 1e-10) {", "else if (Math.hypot(reHigh - slowX, imHigh - slowY) < 1e-10) {\n        $bindings.__juliaDiagnostic.periodHits += 1", "fc8f0c37a014b2f996687589bf96d3fd9a70c2d82392e90d27b91ffdd03d71dc", "4b07de3f6020508a97bd3a436a1d6111651703fcbc4a75010b281e4895171f12", "e64f2eadd238f437ed23f0812e35b8b145fbb8c96f4fa3cd38c19adde16bf40c", 1U, 1U, kDiagnosticCanonicalF32, kDiagnosticInstrumentedF32, kDiagnosticCanonicalRgba8, kDiagnosticInstrumentedRgba8},
}};
struct RelationView { std::string_view name; std::string_view kind; std::string_view candidate_case; std::string_view control_case; bool identical_float32; bool identical_rgba8; std::size_t mutant_changed_float32_lanes; std::size_t mutant_changed_rgba8_bytes; std::size_t canonical_1000_loop_entries; std::size_t canonical_1001_loop_entries; std::size_t no_clamp_mutant_loop_entries; bool instrumented_canonical_1000_pixel_identical; bool instrumented_canonical_1001_pixel_identical; bool instrumented_mutant_pixel_identical; };
inline constexpr std::array<RelationView, 4> kRelations{{
  RelationView{"iterations-clamp-1001-vs-1000", "runtime-loop-clamp-observation", "iterations-clamp-1001", "iterations-max", false, false, 3U, 3U, 1000U, 1000U, 1001U, true, true, true},
  RelationView{"fallback-output-mode", "outputMode-default", "fallback-output-mode", "outputMode=0", true, true, 0U, 0U, 0U, 0U, 0U, true, true, true},
  RelationView{"fallback-trap-shape", "trapShape-else", "fallback-trap-shape", "trapShape=2", true, true, 0U, 0U, 0U, 0U, 0U, true, true, true},
  RelationView{"fallback-c-path", "cPath-explicit-default", "fallback-c-path", "cPath=0", true, true, 0U, 0U, 0U, 0U, 0U, true, true, true},
}};
struct RuntimeControlView { bool repeat_float32; bool repeat_rgba8; bool input_immutable; bool input_lifetime_stable; bool distinct_output_objects; bool distinct_backing_buffers; bool public_direct_identity; bool adapter_own_key; };
inline constexpr RuntimeControlView kControlGroup{true, true, true, true, true, true, true, true};
struct MixedPrecisionResultView { std::string_view field; std::string_view js_number_boundary; std::string_view f32_boundary; bool f32_applied_at_out_parameter; };
inline constexpr MixedPrecisionResultView kResultTrapNumberBoundary{"trapMin", "JS Number accumulator", "Math.fround only at the declared output boundary", false};
inline constexpr BindingControl kResultTrapSearchBindings{{1.0F, 1.0F}, {0.0F, 0.0F}, {1.0F, 1.0F}, 3.7923567490168746, -0.3738171601141377, 0.4634542822519909, 6, 3, 0.44228784680419775, -0.3502212589025081, 77.56369656360795, 992, 0.0, 0, 237.31254449982956, 0, 1.9575383979728302, 0.13296835996046857, false, 0.0, 4.020128862238519};
inline constexpr std::array<std::uint32_t, 4> kResultTrapSearchCanonicalF32{{0x3f3d3d3dU, 0x3f3d3d3dU, 0x3f3d3d3dU, 0x3f800000U}};
inline constexpr std::array<std::uint32_t, 4> kResultTrapSearchMutatedF32{{0x3f3d3d3eU, 0x3f3d3d3eU, 0x3f3d3d3eU, 0x3f800000U}};
inline constexpr std::array<std::uint8_t, 4> kResultTrapSearchCanonicalRgba8{{188U, 188U, 188U, 255U}};
inline constexpr std::array<std::uint8_t, 4> kResultTrapSearchMutatedRgba8{{189U, 189U, 189U, 255U}};
struct WitnessView { int index; std::string_view expected; std::string_view actual; };
struct ResultTrapSearchView { std::string_view selection_rule; std::string_view binding_name; std::size_t width; std::size_t height; BindingControl bindings; std::size_t order_index; std::size_t tested_candidates; std::size_t limit; std::size_t changed_float32_lanes; std::size_t changed_rgba8_bytes; WitnessView float32_witness; WitnessView rgba8_witness; std::span<const std::uint32_t> canonical_f32; std::span<const std::uint32_t> mutated_f32; std::span<const std::uint8_t> canonical_rgba8; std::span<const std::uint8_t> mutated_rgba8; };
inline constexpr ResultTrapSearchView kResultTrapNumberSearch{"poi-trap-first, then trap-search-000000 through trap-search-199999", "trap-search-152217", 1U, 1U, kResultTrapSearchBindings, 152235U, 152236U, 200000U, 3U, 3U, WitnessView{0, "0x3f3d3d3d", "0x3f3d3d3e"}, WitnessView{0, "188", "189"}, kResultTrapSearchCanonicalF32, kResultTrapSearchMutatedF32, kResultTrapSearchCanonicalRgba8, kResultTrapSearchMutatedRgba8};
struct MutationResultView { std::string_view case_name; bool differs; std::size_t changed_float32_lanes; std::size_t changed_rgba8_bytes; WitnessView float32_witness; WitnessView rgba8_witness; };
inline constexpr std::array<MutationResultView, 18> kMutation0Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", true, 54U, 45U, WitnessView{0, "0x3e01ca12", "0x3d458f5c"}, WitnessView{0, "32", "12"} },
  MutationResultView{"manual-stripe", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation1Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", true, 54U, 45U, WitnessView{0, "0x3e01ca12", "0x00000000"}, WitnessView{0, "32", "0"} },
  MutationResultView{"manual-stripe", true, 54U, 54U, WitnessView{0, "0x3f21db1a", "0x00000000"}, WitnessView{0, "161", "0"} },
  MutationResultView{"poi-trap", true, 75U, 75U, WitnessView{0, "0x3f7ff7da", "0x3f6f502f"}, WitnessView{0, "255", "238"} },
  MutationResultView{"manual-normal", true, 48U, 42U, WitnessView{0, "0x3f0e1ac1", "0x3f0d8dff"}, WitnessView{0, "142", "141"} },
  MutationResultView{"animated-circle", true, 27U, 27U, WitnessView{0, "0x00000000", "0x3dbcfe4d"}, WitnessView{0, "0", "24"} },
  MutationResultView{"invert-output", true, 36U, 36U, WitnessView{0, "0x3f800000", "0x00000000"}, WitnessView{0, "255", "0"} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", true, 3U, 3U, WitnessView{0, "0x3f56a8ef", "0x00000000"}, WitnessView{0, "214", "0"} },
  MutationResultView{"bulb-path", true, 12U, 12U, WitnessView{0, "0x00000000", "0x3f800000"}, WitnessView{0, "0", "255"} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", true, 36U, 36U, WitnessView{0, "0x3f6f5fec", "0x00000000"}, WitnessView{0, "238", "0"} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", true, 63U, 63U, WitnessView{0, "0x3f2c9ba5", "0x3f12ce6e"}, WitnessView{0, "172", "146"} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation2Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", true, 60U, 60U, WitnessView{0, "0x3e01ca12", "0x3f2d9e2a"}, WitnessView{0, "32", "173"} },
  MutationResultView{"manual-stripe", true, 54U, 54U, WitnessView{0, "0x3f21db1a", "0x3f24768c"}, WitnessView{0, "161", "164"} },
  MutationResultView{"poi-trap", true, 75U, 75U, WitnessView{0, "0x3f7ff7da", "0x00000000"}, WitnessView{0, "255", "0"} },
  MutationResultView{"manual-normal", true, 48U, 45U, WitnessView{0, "0x3f0e1ac1", "0x3f12ce6e"}, WitnessView{0, "142", "146"} },
  MutationResultView{"animated-circle", true, 6U, 6U, WitnessView{12, "0x3db4ccd1", "0x00000000"}, WitnessView{12, "23", "0"} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", true, 3U, 3U, WitnessView{0, "0x3f56a8ef", "0x00000000"}, WitnessView{0, "214", "0"} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", true, 36U, 36U, WitnessView{0, "0x3f6f5fec", "0x3f70f225"}, WitnessView{0, "238", "240"} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", true, 63U, 63U, WitnessView{0, "0x3f2c9ba5", "0x3f12ce6e"}, WitnessView{0, "172", "146"} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation3Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", true, 60U, 60U, WitnessView{0, "0x3e01ca12", "0x3f800000"}, WitnessView{0, "32", "255"} },
  MutationResultView{"manual-stripe", true, 54U, 54U, WitnessView{0, "0x3f21db1a", "0x3f044dc6"}, WitnessView{0, "161", "132"} },
  MutationResultView{"poi-trap", true, 75U, 75U, WitnessView{0, "0x3f7ff7da", "0x00000000"}, WitnessView{0, "255", "0"} },
  MutationResultView{"manual-normal", true, 48U, 45U, WitnessView{0, "0x3f0e1ac1", "0x3f12ce6e"}, WitnessView{0, "142", "146"} },
  MutationResultView{"animated-circle", true, 6U, 6U, WitnessView{12, "0x3db4ccd1", "0x00000000"}, WitnessView{12, "23", "0"} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", true, 3U, 3U, WitnessView{0, "0x3f56a8ef", "0x00000000"}, WitnessView{0, "214", "0"} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", true, 36U, 36U, WitnessView{0, "0x3f6f5fec", "0x3f710295"}, WitnessView{0, "238", "240"} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", true, 63U, 63U, WitnessView{0, "0x3f2c9ba5", "0x3f12ce6e"}, WitnessView{0, "172", "146"} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation4Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", true, 54U, 45U, WitnessView{0, "0x3e01ca12", "0x00000000"}, WitnessView{0, "32", "0"} },
  MutationResultView{"manual-stripe", true, 54U, 54U, WitnessView{0, "0x3f21db1a", "0x00000000"}, WitnessView{0, "161", "0"} },
  MutationResultView{"poi-trap", true, 75U, 75U, WitnessView{0, "0x3f7ff7da", "0x00000000"}, WitnessView{0, "255", "0"} },
  MutationResultView{"manual-normal", true, 48U, 45U, WitnessView{0, "0x3f0e1ac1", "0x3f12ce6e"}, WitnessView{0, "142", "146"} },
  MutationResultView{"animated-circle", true, 6U, 6U, WitnessView{12, "0x3db4ccd1", "0x00000000"}, WitnessView{12, "23", "0"} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", true, 3U, 3U, WitnessView{0, "0x3f56a8ef", "0x00000000"}, WitnessView{0, "214", "0"} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", true, 36U, 36U, WitnessView{0, "0x3f6f5fec", "0x00000000"}, WitnessView{0, "238", "0"} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", true, 63U, 63U, WitnessView{0, "0x3f2c9ba5", "0x3f12ce6e"}, WitnessView{0, "172", "146"} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation5Results{{
  MutationResultView{"manual-smooth", true, 60U, 0U, WitnessView{0, "0x00000000", "0x7fe00000"}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-stripe", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", true, 48U, 45U, WitnessView{0, "0x3f0e1ac1", "0x3f12ce6e"}, WitnessView{0, "142", "146"} },
  MutationResultView{"animated-circle", true, 36U, 6U, WitnessView{0, "0x00000000", "0x7fe00000"}, WitnessView{12, "23", "0"} },
  MutationResultView{"invert-output", true, 6U, 6U, WitnessView{0, "0x3f800000", "0x3f7e81c6"}, WitnessView{0, "255", "254"} },
  MutationResultView{"animated-lissajous", true, 27U, 27U, WitnessView{0, "0x00000000", "0x3f7ff4eb"}, WitnessView{0, "0", "255"} },
  MutationResultView{"iterations-min", true, 3U, 0U, WitnessView{0, "0x00000000", "0x7fe00000"}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", true, 3U, 3U, WitnessView{0, "0x00000000", "0x3f56a8ef"}, WitnessView{0, "0", "214"} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", true, 6U, 0U, WitnessView{0, "0x00000000", "0x7fe00000"}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", true, 3U, 3U, WitnessView{0, "0x00000000", "0x3f800000"}, WitnessView{0, "0", "255"} },
  MutationResultView{"fallback-output-mode", true, 60U, 0U, WitnessView{0, "0x00000000", "0x7fe00000"}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", true, 36U, 0U, WitnessView{0, "0x00000000", "0x7fe00000"}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", true, 63U, 63U, WitnessView{0, "0x3f2c9ba5", "0x3f12ce6e"}, WitnessView{0, "172", "146"} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation6Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", true, 54U, 45U, WitnessView{0, "0x3e01ca12", "0x7fc00000"}, WitnessView{0, "32", "0"} },
  MutationResultView{"manual-stripe", true, 54U, 54U, WitnessView{0, "0x3f21db1a", "0x7fe00000"}, WitnessView{0, "161", "0"} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", true, 48U, 48U, WitnessView{0, "0x3f0e1ac1", "0x7fe00000"}, WitnessView{0, "142", "0"} },
  MutationResultView{"animated-circle", true, 6U, 6U, WitnessView{12, "0x3db4ccd1", "0x7fe00000"}, WitnessView{12, "23", "0"} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", true, 63U, 63U, WitnessView{0, "0x3f2c9ba5", "0x7fe00000"}, WitnessView{0, "172", "0"} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation7Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", true, 54U, 45U, WitnessView{0, "0x3e01ca12", "0x00000000"}, WitnessView{0, "32", "0"} },
  MutationResultView{"manual-stripe", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation8Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-stripe", true, 54U, 54U, WitnessView{0, "0x3f21db1a", "0x00000000"}, WitnessView{0, "161", "0"} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation9Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-stripe", true, 54U, 54U, WitnessView{0, "0x3f21db1a", "0x3f19b2ee"}, WitnessView{0, "161", "153"} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation10Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-stripe", true, 54U, 36U, WitnessView{0, "0x3f21db1a", "0x3f237eee"}, WitnessView{0, "161", "163"} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation11Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-stripe", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-trap", true, 75U, 75U, WitnessView{0, "0x3f7ff7da", "0x00000000"}, WitnessView{0, "255", "0"} },
  MutationResultView{"manual-normal", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", true, 3U, 3U, WitnessView{0, "0x3f56a8ef", "0x00000000"}, WitnessView{0, "214", "0"} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", true, 36U, 36U, WitnessView{0, "0x3f6f5fec", "0x00000000"}, WitnessView{0, "238", "0"} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation12Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", true, 60U, 57U, WitnessView{0, "0x3e01ca12", "0x00000000"}, WitnessView{0, "32", "0"} },
  MutationResultView{"manual-stripe", true, 54U, 48U, WitnessView{0, "0x3f21db1a", "0x3f1ec5d5"}, WitnessView{0, "161", "158"} },
  MutationResultView{"poi-trap", true, 75U, 75U, WitnessView{0, "0x3f7ff7da", "0x00000000"}, WitnessView{0, "255", "0"} },
  MutationResultView{"manual-normal", true, 48U, 45U, WitnessView{0, "0x3f0e1ac1", "0x3f12ce6e"}, WitnessView{0, "142", "146"} },
  MutationResultView{"animated-circle", true, 6U, 6U, WitnessView{12, "0x3db4ccd1", "0x00000000"}, WitnessView{12, "23", "0"} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", true, 3U, 3U, WitnessView{0, "0x3f56a8ef", "0x3f7e8396"}, WitnessView{0, "214", "254"} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", true, 36U, 24U, WitnessView{0, "0x3f6f5fec", "0x3f7d45b8"}, WitnessView{0, "238", "252"} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", true, 63U, 63U, WitnessView{0, "0x3f2c9ba5", "0x3f12ce6e"}, WitnessView{0, "172", "146"} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation13Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", true, 60U, 60U, WitnessView{0, "0x3e01ca12", "0x3ca2a71a"}, WitnessView{0, "32", "5"} },
  MutationResultView{"manual-stripe", true, 36U, 36U, WitnessView{0, "0x3f21db1a", "0x3f151447"}, WitnessView{0, "161", "148"} },
  MutationResultView{"poi-trap", true, 75U, 0U, WitnessView{0, "0x3f7ff7da", "0x3f7f9b35"}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", true, 48U, 48U, WitnessView{0, "0x3f0e1ac1", "0x3f15cdf7"}, WitnessView{0, "142", "149"} },
  MutationResultView{"animated-circle", true, 6U, 6U, WitnessView{12, "0x3db4ccd1", "0x00000000"}, WitnessView{12, "23", "0"} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", true, 3U, 3U, WitnessView{0, "0x00000000", "0x3ef0a5ce"}, WitnessView{0, "0", "120"} },
  MutationResultView{"iterations-clamp-1001", true, 3U, 3U, WitnessView{0, "0x3f56a8ef", "0x3ef0a5ce"}, WitnessView{0, "214", "120"} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", true, 24U, 18U, WitnessView{0, "0x3f6f5fec", "0x3f7ec631"}, WitnessView{0, "238", "254"} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", true, 63U, 63U, WitnessView{0, "0x3f2c9ba5", "0x3f184d7d"}, WitnessView{0, "172", "152"} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation14Results{{
  MutationResultView{"manual-smooth", true, 60U, 0U, WitnessView{0, "0x00000000", "0x7fe00000"}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", true, 60U, 45U, WitnessView{0, "0x3e01ca12", "0x7fe00000"}, WitnessView{0, "32", "0"} },
  MutationResultView{"manual-stripe", true, 54U, 54U, WitnessView{0, "0x3f21db1a", "0x7fe00000"}, WitnessView{0, "161", "0"} },
  MutationResultView{"poi-trap", true, 75U, 75U, WitnessView{0, "0x3f7ff7da", "0x3f4fbd00"}, WitnessView{0, "255", "207"} },
  MutationResultView{"manual-normal", true, 48U, 48U, WitnessView{0, "0x3f0e1ac1", "0x7fe00000"}, WitnessView{0, "142", "0"} },
  MutationResultView{"animated-circle", true, 36U, 6U, WitnessView{0, "0x00000000", "0x7fe00000"}, WitnessView{12, "23", "0"} },
  MutationResultView{"invert-output", true, 36U, 36U, WitnessView{0, "0x3f800000", "0x7fe00000"}, WitnessView{0, "255", "0"} },
  MutationResultView{"animated-lissajous", true, 27U, 27U, WitnessView{0, "0x00000000", "0x3f7ff1cf"}, WitnessView{0, "0", "255"} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", true, 3U, 3U, WitnessView{0, "0x00000000", "0x3e19f5f7"}, WitnessView{0, "0", "38"} },
  MutationResultView{"iterations-clamp-1001", true, 3U, 3U, WitnessView{0, "0x3f56a8ef", "0x3e19f5f7"}, WitnessView{0, "214", "38"} },
  MutationResultView{"bulb-path", true, 12U, 0U, WitnessView{0, "0x00000000", "0x7fe00000"}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", true, 12U, 0U, WitnessView{0, "0x00000000", "0x7fe00000"}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", true, 60U, 0U, WitnessView{0, "0x00000000", "0x7fe00000"}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", true, 36U, 36U, WitnessView{0, "0x3f6f5fec", "0x3e93f34f"}, WitnessView{0, "238", "74"} },
  MutationResultView{"fallback-c-path", true, 36U, 0U, WitnessView{0, "0x00000000", "0x7fe00000"}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", true, 63U, 63U, WitnessView{0, "0x3f2c9ba5", "0x7fe00000"}, WitnessView{0, "172", "0"} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation15Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-stripe", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", true, 3U, 3U, WitnessView{0, "0x3f56a8ef", "0x00000000"}, WitnessView{0, "214", "0"} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation16Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", true, 27U, 18U, WitnessView{8, "0x3a02883a", "0x00000000"}, WitnessView{12, "7", "0"} },
  MutationResultView{"manual-stripe", true, 18U, 18U, WitnessView{16, "0x3f25aa90", "0x00000000"}, WitnessView{16, "165", "0"} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", true, 48U, 45U, WitnessView{0, "0x3f0e1ac1", "0x3f12ce6e"}, WitnessView{0, "142", "146"} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", true, 3U, 3U, WitnessView{0, "0x3f56a8ef", "0x00000000"}, WitnessView{0, "214", "0"} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", true, 12U, 12U, WitnessView{12, "0x3f7eaf3d", "0x00000000"}, WitnessView{12, "254", "0"} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation17Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-stripe", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", true, 48U, 42U, WitnessView{0, "0x3f0e1ac1", "0x3f108c2b"}, WitnessView{0, "142", "144"} },
  MutationResultView{"animated-circle", true, 6U, 6U, WitnessView{12, "0x3db4ccd1", "0x3dea6668"}, WitnessView{12, "23", "29"} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", true, 63U, 63U, WitnessView{0, "0x3f2c9ba5", "0x3f36ad71"}, WitnessView{0, "172", "182"} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation18Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", true, 54U, 39U, WitnessView{0, "0x3e01ca12", "0x3e0bcee9"}, WitnessView{0, "32", "35"} },
  MutationResultView{"manual-stripe", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation19Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-stripe", true, 54U, 36U, WitnessView{0, "0x3f21db1a", "0x3f214823"}, WitnessView{4, "163", "164"} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation20Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-stripe", true, 54U, 12U, WitnessView{0, "0x3f21db1a", "0x3f219098"}, WitnessView{12, "158", "157"} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation21Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-stripe", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", true, 48U, 48U, WitnessView{0, "0x3f0e1ac1", "0x3f1252c3"}, WitnessView{0, "142", "146"} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", true, 63U, 63U, WitnessView{0, "0x3f2c9ba5", "0x3f229e44"}, WitnessView{0, "172", "162"} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation22Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-stripe", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", true, 48U, 48U, WitnessView{0, "0x3f0e1ac1", "0x3f0909cd"}, WitnessView{0, "142", "137"} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", true, 63U, 9U, WitnessView{0, "0x3f2c9ba5", "0x3f2d0f3a"}, WitnessView{28, "177", "178"} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation23Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-stripe", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", true, 48U, 48U, WitnessView{0, "0x3f0e1ac1", "0x3f17ddfd"}, WitnessView{0, "142", "151"} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", true, 63U, 63U, WitnessView{0, "0x3f2c9ba5", "0x3f126349"}, WitnessView{0, "172", "146"} },
}};
inline constexpr std::array<MutationResultView, 18> kMutation24Results{{
  MutationResultView{"manual-smooth", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-distance-tile", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-stripe", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-trap", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"manual-normal", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-circle", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"invert-output", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"animated-lissajous", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-min", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-max", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"iterations-clamp-1001", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"bulb-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"poi-fallback", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"period-convergence", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-output-mode", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-trap-shape", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"fallback-c-path", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
  MutationResultView{"non-square-f32-transform", false, 0U, 0U, WitnessView{-1, {}, {}}, WitnessView{-1, {}, {}} },
}};
inline constexpr std::array<std::string_view, 1> kMutation0WitnessCases{{
  "manual-distance-tile"
}};
inline constexpr std::array<std::string_view, 17> kMutation0ControlCases{{
  "manual-smooth", "manual-stripe", "poi-trap", "manual-normal", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 10> kMutation1WitnessCases{{
  "manual-distance-tile", "manual-stripe", "poi-trap", "manual-normal", "animated-circle", "invert-output", "iterations-clamp-1001", "bulb-path", "fallback-trap-shape", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 8> kMutation1ControlCases{{
  "manual-smooth", "animated-lissajous", "iterations-min", "iterations-max", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-c-path"
}};
inline constexpr std::array<std::string_view, 8> kMutation2WitnessCases{{
  "manual-distance-tile", "manual-stripe", "poi-trap", "manual-normal", "animated-circle", "iterations-clamp-1001", "fallback-trap-shape", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 10> kMutation2ControlCases{{
  "manual-smooth", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-c-path"
}};
inline constexpr std::array<std::string_view, 8> kMutation3WitnessCases{{
  "manual-distance-tile", "manual-stripe", "poi-trap", "manual-normal", "animated-circle", "iterations-clamp-1001", "fallback-trap-shape", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 10> kMutation3ControlCases{{
  "manual-smooth", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-c-path"
}};
inline constexpr std::array<std::string_view, 8> kMutation4WitnessCases{{
  "manual-distance-tile", "manual-stripe", "poi-trap", "manual-normal", "animated-circle", "iterations-clamp-1001", "fallback-trap-shape", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 10> kMutation4ControlCases{{
  "manual-smooth", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-c-path"
}};
inline constexpr std::array<std::string_view, 12> kMutation5WitnessCases{{
  "manual-smooth", "manual-normal", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "bulb-path", "period-convergence", "fallback-output-mode", "fallback-c-path", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 6> kMutation5ControlCases{{
  "manual-distance-tile", "manual-stripe", "poi-trap", "iterations-clamp-1001", "poi-fallback", "fallback-trap-shape"
}};
inline constexpr std::array<std::string_view, 5> kMutation6WitnessCases{{
  "manual-distance-tile", "manual-stripe", "manual-normal", "animated-circle", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 13> kMutation6ControlCases{{
  "manual-smooth", "poi-trap", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path"
}};
inline constexpr std::array<std::string_view, 1> kMutation7WitnessCases{{
  "manual-distance-tile"
}};
inline constexpr std::array<std::string_view, 17> kMutation7ControlCases{{
  "manual-smooth", "manual-stripe", "poi-trap", "manual-normal", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 1> kMutation8WitnessCases{{
  "manual-stripe"
}};
inline constexpr std::array<std::string_view, 17> kMutation8ControlCases{{
  "manual-smooth", "manual-distance-tile", "poi-trap", "manual-normal", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 1> kMutation9WitnessCases{{
  "manual-stripe"
}};
inline constexpr std::array<std::string_view, 17> kMutation9ControlCases{{
  "manual-smooth", "manual-distance-tile", "poi-trap", "manual-normal", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 1> kMutation10WitnessCases{{
  "manual-stripe"
}};
inline constexpr std::array<std::string_view, 17> kMutation10ControlCases{{
  "manual-smooth", "manual-distance-tile", "poi-trap", "manual-normal", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 3> kMutation11WitnessCases{{
  "poi-trap", "iterations-clamp-1001", "fallback-trap-shape"
}};
inline constexpr std::array<std::string_view, 15> kMutation11ControlCases{{
  "manual-smooth", "manual-distance-tile", "manual-stripe", "manual-normal", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-c-path", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 8> kMutation12WitnessCases{{
  "manual-distance-tile", "manual-stripe", "poi-trap", "manual-normal", "animated-circle", "iterations-clamp-1001", "fallback-trap-shape", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 10> kMutation12ControlCases{{
  "manual-smooth", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-c-path"
}};
inline constexpr std::array<std::string_view, 9> kMutation13WitnessCases{{
  "manual-distance-tile", "manual-stripe", "poi-trap", "manual-normal", "animated-circle", "iterations-max", "iterations-clamp-1001", "fallback-trap-shape", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 9> kMutation13ControlCases{{
  "manual-smooth", "invert-output", "animated-lissajous", "iterations-min", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-c-path"
}};
inline constexpr std::array<std::string_view, 16> kMutation14WitnessCases{{
  "manual-smooth", "manual-distance-tile", "manual-stripe", "poi-trap", "manual-normal", "animated-circle", "invert-output", "animated-lissajous", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 2> kMutation14ControlCases{{
  "iterations-min", "period-convergence"
}};
inline constexpr std::array<std::string_view, 1> kMutation15WitnessCases{{
  "iterations-clamp-1001"
}};
inline constexpr std::array<std::string_view, 17> kMutation15ControlCases{{
  "manual-smooth", "manual-distance-tile", "manual-stripe", "poi-trap", "manual-normal", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 5> kMutation16WitnessCases{{
  "manual-distance-tile", "manual-stripe", "manual-normal", "iterations-clamp-1001", "fallback-trap-shape"
}};
inline constexpr std::array<std::string_view, 13> kMutation16ControlCases{{
  "manual-smooth", "poi-trap", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-c-path", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 3> kMutation17WitnessCases{{
  "manual-normal", "animated-circle", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 15> kMutation17ControlCases{{
  "manual-smooth", "manual-distance-tile", "manual-stripe", "poi-trap", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path"
}};
inline constexpr std::array<std::string_view, 1> kMutation18WitnessCases{{
  "manual-distance-tile"
}};
inline constexpr std::array<std::string_view, 17> kMutation18ControlCases{{
  "manual-smooth", "manual-stripe", "poi-trap", "manual-normal", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 1> kMutation19WitnessCases{{
  "manual-stripe"
}};
inline constexpr std::array<std::string_view, 17> kMutation19ControlCases{{
  "manual-smooth", "manual-distance-tile", "poi-trap", "manual-normal", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 1> kMutation20WitnessCases{{
  "manual-stripe"
}};
inline constexpr std::array<std::string_view, 17> kMutation20ControlCases{{
  "manual-smooth", "manual-distance-tile", "poi-trap", "manual-normal", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 2> kMutation21WitnessCases{{
  "manual-normal", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 16> kMutation21ControlCases{{
  "manual-smooth", "manual-distance-tile", "manual-stripe", "poi-trap", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path"
}};
inline constexpr std::array<std::string_view, 2> kMutation22WitnessCases{{
  "manual-normal", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 16> kMutation22ControlCases{{
  "manual-smooth", "manual-distance-tile", "manual-stripe", "poi-trap", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path"
}};
inline constexpr std::array<std::string_view, 2> kMutation23WitnessCases{{
  "manual-normal", "non-square-f32-transform"
}};
inline constexpr std::array<std::string_view, 16> kMutation23ControlCases{{
  "manual-smooth", "manual-distance-tile", "manual-stripe", "poi-trap", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path"
}};
inline constexpr std::array<std::string_view, 0> kMutation24WitnessCases{{
  }};
inline constexpr std::array<std::string_view, 18> kMutation24ControlCases{{
  "manual-smooth", "manual-distance-tile", "manual-stripe", "poi-trap", "manual-normal", "animated-circle", "invert-output", "animated-lissajous", "iterations-min", "iterations-max", "iterations-clamp-1001", "bulb-path", "poi-fallback", "period-convergence", "fallback-output-mode", "fallback-trap-shape", "fallback-c-path", "non-square-f32-transform"
}};
struct MutationView { std::string_view name; std::string_view group; std::string_view mechanism; std::string_view source_anchor; std::string_view source_span; std::string_view replacement; std::string_view anchor_sha256; std::string_view replacement_sha256; std::string_view mutated_factory_sha256; std::string_view result_sha256; bool independent; std::size_t anchor_occurrence_count; std::span<const std::string_view> witness_cases; std::span<const std::string_view> control_cases; std::span<const MutationResultView> results; };
inline constexpr std::array<MutationView, 25> kMutations{{
  MutationView{"cross-lane-dz-assignment", "cross-lane-assignment", "replace next-derivative temporary with source-order aliasing", "const nextDerivativeX = F32(2 * F32(F32(reHigh * derivativeX) - F32(imHigh * derivativeY)))\n      derivativeY = F32(2 * F32(F32(reHigh * derivativeY) + F32(imHigh * derivativeX)))\n      derivativeX = nextDerivativeX", "", "derivativeX = F32(2 * F32(F32(reHigh * derivativeX) - F32(imHigh * derivativeY)))\n      derivativeY = F32(2 * F32(F32(reHigh * derivativeY) + F32(imHigh * derivativeX)))", "c83c5e436be035614cc98e1b8e96d71c5a31804e1c543c8e9001b9052ff4e44a", "60737b08ed7eb5909a883d8c0fba2abf6ffe477ffe7fc747d15e84e3de2cddd1", "9fdd53914591d4bb4209094359c1450847beef8bf0426bf737c872de286d081e", "4acdbcb21f93a80e55b86b5146a1de0ae96b576d7b23889e01fdca7f7bbd77cf", true, 1U, kMutation0WitnessCases, kMutation0ControlCases, kMutation0Results},
  MutationView{"df64-re2-carrier", "df64-carrier", "replace df64 real-square carrier owner", "const re2High = scratchHigh\n      const re2Low = scratchLow", "", "const re2High = 0\n      const re2Low = 0", "8179e52b0d81507ebe5ea947187d17e13369707e41a6724a1c3e9c4718d46333", "7aff87de41586aa57188e9fadaed79afddb149412e1f898a9a2c2ba583b8f1eb", "94c4d51c7c00b1ae740f57b0bc783c4d60a30aba5dc35312e3796069f16f4480", "15a47a2e97e32935c2851c33c16a79f73bfffcf07570f8b571e865b756f82ae2", true, 1U, kMutation1WitnessCases, kMutation1ControlCases, kMutation1Results},
  MutationView{"df64-im2-carrier", "df64-carrier", "replace df64 imaginary-square carrier owner", "const im2High = scratchHigh\n      const im2Low = scratchLow", "", "const im2High = 0\n      const im2Low = 0", "869cd06339a147e9cb452afdaded26b2cc082b17ff9d2e05d5fbdd0e60296d08", "f728fc3c75861ac1908f3c99d0ea01a573cd339d8690a2d89f4b082b48bff44d", "5b81a2db3058cfab7595b182f445bfa32fa143279a8dc1ddf1e32f1416b54194", "6df249c1c71abb6262030b8425d4d37628c629dc7fc44ff38aa7f6a6b5f3bad7", true, 1U, kMutation2WitnessCases, kMutation2ControlCases, kMutation2Results},
  MutationView{"df64-product-carrier", "df64-carrier", "replace df64 product carrier owner", "const productHigh = scratchHigh\n      const productLow = scratchLow", "", "const productHigh = 0\n      const productLow = 0", "bf08c13264b7df9f6d350909bf4fbaee0ec152b327f508c9c971c80dedbc8e40", "76695fed4c1fa0e89f85bc1ca8703292489b39d3bf317152ee53cfc328a0fbce", "78904c52122d5ab142be1628ff4290dac7d143b529f4116dd4df4ad1927ad0fc", "77da401b37b415f8286e8599265f3035a8d9ded0091b0c1e1cf0348121270afa", true, 1U, kMutation3WitnessCases, kMutation3ControlCases, kMutation3Results},
  MutationView{"df64-next-re-carrier", "df64-carrier", "replace df64 next-real carrier owner", "const nextReHigh = scratchHigh\n      const nextReLow = scratchLow", "", "const nextReHigh = 0\n      const nextReLow = 0", "d6589040e2a74df6e07a87fde42351b2fd29cc93550947d1106b23f6d8c0fc4d", "3a1ab0e1e7a77817560db1257ff5e1d0a782e99ae4e0c09512501a932b87b84d", "900bf690c575f4fdc517db041aac51ef59f78051ff257616e1750fe3dbbd1813", "3251bfa71d38c3b48b52ec497f7ef4c4bf1335ba79cfc880058ffa1cb41de247", true, 1U, kMutation4WitnessCases, kMutation4ControlCases, kMutation4Results},
  MutationView{"out-iteration", "out-materialization", "mutate iteration result owner materialization", "result.iteration = iteration", "", "result.iteration = 0", "30c8fb06d7d4f895e14cb9b022ff7c4192e3ca90fe8780cc4de9ffb8b2610d4e", "7c4cfbe45467c7ae34c862d91ea3a57fca56ae082223347c90bebf83c421e206", "c8f88c760fad861bfb6dbc4cd63f2f9a2c127daa35d2645e21418a8d8258ea3d", "f50656a389d4bbd9370f9d19a61822df479dfe125386d8b083e34cdd2b90bc1d", true, 1U, kMutation5WitnessCases, kMutation5ControlCases, kMutation5Results},
  MutationView{"out-z-magnitude2", "out-materialization", "mutate zMagnitude2 result owner materialization", "result.zMagnitude2 = F32(F32(reHigh * reHigh) + F32(imHigh * imHigh))", "", "result.zMagnitude2 = 0", "7ba3eacc7b9b8b8da2605660a467a5bce50d9e9b6e07c19454d550a2b66e8f66", "d36ed37ea88cc317e08d4c3ac1e323f95b964662c0462e1a851a0a3cf133a0e5", "69507160fcd2f53af070bd4db5c14749f09a7475339f72f498d5495993613427", "e9ec50a9e509fa3847ba149892528d5320aa08418a98fa566e697f3badde58a9", true, 1U, kMutation6WitnessCases, kMutation6ControlCases, kMutation6Results},
  MutationView{"out-derivative-magnitude2", "out-materialization", "mutate derivativeMagnitude2 result owner materialization", "result.derivativeMagnitude2 = F32(F32(derivativeX * derivativeX) + F32(derivativeY * derivativeY))", "", "result.derivativeMagnitude2 = 0", "0aa48418f5c21ee957c609cdf0331624a843282cfb70eb70183de6d0870c9504", "4938e9681edd141d48686819c27b08698980e07efc1757c4e65917c5e470bec6", "d836409e43fa5c3b1a222303b8a40dcba144eff89a813720ac5ee2773fe86541", "bda52bbbf81c7ae6324de92efa8ed6031d752b00bfadee8a72261d62e28ce8cf", true, 1U, kMutation7WitnessCases, kMutation7ControlCases, kMutation7Results},
  MutationView{"out-stripe-sum", "out-materialization", "mutate stripeSum result owner materialization", "result.stripeSum = stripeSum", "", "result.stripeSum = 0", "66392efe93e894248bac6c6bca7ae0d8f8549199289356b51b8ee66e1cfe7eb6", "fd870248bb90468d89ea28efe5c0c9d53ecc29b04edcf28bc48e9de75de94471", "c1e17b234f588162749c5a8766c48af04fd231af2ff24b7f439a580326fbbd33", "29d37266e62062713a9f57016275b0d427adeb2171aed6ce08e70f0ff061a209", true, 1U, kMutation8WitnessCases, kMutation8ControlCases, kMutation8Results},
  MutationView{"out-stripe-count", "out-materialization", "mutate stripeCount result owner materialization", "result.stripeCount = stripeCount", "", "result.stripeCount = stripeCount + 1", "d79ff37e0390f4091a72fe78876b0caa2f92347cf4eefff5bbbeca74a5b765fe", "0f9d1fbd21929c819e18d9ac761c6492b874dfed91d452c17baf867baea78651", "0bb332675454140bf47a02c53d47d18a8667500a0c6a642a616919b75c204a66", "42ab9d6e31b8f9b24a2c257d5564337d00b3e0f89ae62ed5d1eb5c5a2f8c65b7", true, 1U, kMutation9WitnessCases, kMutation9ControlCases, kMutation9Results},
  MutationView{"out-stripe-last", "out-materialization", "mutate stripeLast result owner materialization", "result.stripeLast = stripeLast", "", "result.stripeLast = 0", "69a85b0ccde99c3821f03dde06cb9e4ec3c94d7cbd1aae65306f3c75d6e65b4a", "e6b5d74c85d2c2ee381cb0302783776b2a008732775233d75d870d4a63f6ede5", "bf00af11ec4f923f4c29890f8b53f55eaab6aaf36667dbd835513871fbf02018", "399c49689696fbb38060af8b5ca33c2f50c9f595a6df829859ff49013d22a5b3", true, 1U, kMutation10WitnessCases, kMutation10ControlCases, kMutation10Results},
  MutationView{"out-trap-min", "out-materialization", "mutate trapMin result owner materialization", "result.trapMin = trapMin", "", "result.trapMin = 1", "1a01779573462d720c6ae74e6bb10083ad6a9c3209ca508c262088f3903b1df2", "5648290fd2fc4f963aed60553d5e08eb31bd05d7e9dc77c6853fcb4612e58ae9", "0c18b2a9a2d2e2989e1bcc8f53ffbfb34606726710dc03b2f64d4358faef04aa", "52e45382437e15a0004b2c25fea5b1dcbb522ec8f08c15ef10be2dfd85fc5997", true, 1U, kMutation11WitnessCases, kMutation11ControlCases, kMutation11Results},
  MutationView{"transform-re-owner", "out-materialization", "mutate transform real coordinate owner", "coordinates[0] = scratchHigh", "", "coordinates[0] = 0", "04cd174c201170ba87b4cc0f4c8e3a832aba6cff09ffcd6a884156ca9d4d627e", "8826e0fbf5c6623a03a15cfe86306fa89e8ad1df362be765d151b390b26a0a51", "e0db5ab13c82c1a50b6a2538bd97aaff2317d0f8a45345e21675abe6760d0e4b", "e99ceaec06045d872d591a097cac99c40fd34aab391271c90bb029d1456bbdc6", true, 1U, kMutation12WitnessCases, kMutation12ControlCases, kMutation12Results},
  MutationView{"transform-im-owner", "out-materialization", "mutate transform imaginary coordinate owner", "coordinates[2] = scratchHigh", "", "coordinates[2] = 0", "7d323b5bac250bf655fecb32049b8754f5f65b9f5e2f2edac90caf7a993d2444", "6b85f53f990d823afdd18bd215c236941a89c26d9b5be1365d8b57daad46bcfc", "7d4ac5cb76054fa93bfa948bd867b32343ff171ab19d37308219c78db8156292", "f7af78218f8f7d1f4b3e71f2970da9c6bbe5d1487fb2a716dce795a9ec5924f3", true, 1U, kMutation13WitnessCases, kMutation13ControlCases, kMutation13Results},
  MutationView{"loop-bound", "iteration-loop", "shorten Julia outer iteration bound", "Math.min(maxIterations, 1000)", "", "Math.min(maxIterations, 1)", "d7827a7823840b51b49c31a86c8e2653bb2d14e2b28d599205c61f29ce05d461", "848242238dd18b61ae89a14eebdf9ce4857f349e446cf4f62907e58e715f5c1f", "dc56981c1d347992b9c390393acd073b9640afc653b476027230b2c437f8f4fb", "b7e2fad5e0b22d15dac9c45cb2e259aca69928363111918be8aefb5348634e18", true, 1U, kMutation14WitnessCases, kMutation14ControlCases, kMutation14Results},
  MutationView{"loop-clamp-1001", "iteration-loop", "remove the runtime maxIterations clamp at the direct 1001 boundary", "Math.min(maxIterations, 1000)", "", "maxIterations", "d7827a7823840b51b49c31a86c8e2653bb2d14e2b28d599205c61f29ce05d461", "825df14610cc75d3e2a1e1e35276bce9686d82063e3d66f9c449100bc1e74f7b", "a5c1e3fe9530d06a8d6ccfaafd3f1b29c2221a35a7a874b6d48881281d9a9a18", "8d2097f509bb15eb75a1f3d7e4c184ef8a55d303c1c80585eec4cec8b2fcb796", true, 1U, kMutation15WitnessCases, kMutation15ControlCases, kMutation15Results},
  MutationView{"period-loop-bound", "iteration-loop", "widen period detection convergence bound", "Math.hypot(reHigh - slowX, imHigh - slowY) < 1e-10", "", "Math.hypot(reHigh - slowX, imHigh - slowY) < 1e-1", "447482a148196100135bf5d27c8fa26cf758afd687b5207a377a0ae10395c3cd", "f65b14b1826bb113e75206d47e8644461c4cd4feeb9a24718d557a1b1134c16a", "1fb47da10ab8baa42ee7fd469724eb7d282b8c37d8ec02ba767f23cbd47a5c5e", "ea095a58e3b6d5df72611ca9dfbd20f602979362bf390b78da3cc5fb8b6c82a2", true, 1U, kMutation16WitnessCases, kMutation16ControlCases, kMutation16Results},
  MutationView{"log-smoothing", "log-sites", "mutate smooth iteration logarithm", "const nu = Math.log(logMagnitude / LOG2) / LOG2\n    return clamp((iterationResult.iteration + 1 - nu) / maxIterations)", "", "const nu = Math.log(logMagnitude / LOG2) / (LOG2 * 2)\n    return clamp((iterationResult.iteration + 1 - nu) / maxIterations)", "d3bdfef870e6dc5fd8912686b44441d8441f6ad793f0caff514c9f46752e1f3a", "cd6ca2a350c60483ae4e939d5283d448a9c577b3d79d39454e7af1dfcd665603", "9937f3ecb41404f1c3f4a90763f31c75435c0baf0e88740eec6f539be5ccf0fc", "ed124e272782a8e08152fca66b52c5c26e42310cd1e384244392c2edaf247086", true, 1U, kMutation17WitnessCases, kMutation17ControlCases, kMutation17Results},
  MutationView{"log-distance", "log-sites", "mutate distance estimation logarithm", "Math.log(2 * magnitude * Math.log(magnitude) / derivative + 1) * 2", "", "Math.log(2 * magnitude * Math.log(magnitude * 2) / derivative + 1) * 2", "b25f59f85a9fc1f67ab9871f119ece6223efe996d84d10e4713a050cd6f88b20", "23792fe1424127784d6fbbdcbf39cbb0929ed9248a0a75def3f46d265839f78d", "e7b841834a4022189633c1374841a638b0e1c5dbc567059d0e3b7b84461fa50b", "d7c742fe96564afc28cb5d863d1b24119c0ef8ae4ed0e60feca4fe2e9cfe918c", true, 1U, kMutation18WitnessCases, kMutation18ControlCases, kMutation18Results},
  MutationView{"log-stripe", "log-sites", "mutate stripe logarithm", "const logMagnitude = Math.log(r.zMagnitude2) * 0.5", "", "const logMagnitude = Math.log(r.zMagnitude2) * 5", "a8ab022104954ba54031d07439b3370f16a0429130ef09ee0077c44782d3238d", "e25fa0a0c4a95a122b863167b47c6b43cd7c01ac8aa96371d8341a3a16c48500", "c2da8e6fccffc9ae07940766e80c928d88e4641d7a6c23eae259d53c69c983f8", "fa98057c765a6f6901336ba44627a27efab51397e85fc694cc608c2e677a0292", true, 1U, kMutation19WitnessCases, kMutation19ControlCases, kMutation19Results},
  MutationView{"log-stripe-normalization", "log-sites", "mutate stripe normalization logarithm", "const nu = Math.log(logMagnitude / LOG2) / LOG2\n          value = clamp(mix(previous, average", "", "const nu = Math.log(logMagnitude / LOG2) / (LOG2 * 10)\n          value = clamp(mix(previous, average", "c9a5e600d8ac570b5a455d0abe636b41250288e4c2dd9e539de3d89cd310566f", "a73eaca2557ae94a9f8c1a9012d0f0a901df7f728417738a426d9604438f94a4", "328117479d486f509a70358ae46b8beda46b311f70084e0998f01c3d06f2d1a9", "b0088d0eaaf30bcc4f15841d75b8e3b4abcd1b540dc177a68d041ea155df9eab", true, 1U, kMutation20WitnessCases, kMutation20ControlCases, kMutation20Results},
  MutationView{"normal-base", "normal-three-sample", "mutate normal base sample coordinate", "const base = iterateSmooth(globalX, globalY, constant[0], constant[1], $bindings.iterations, zoom)", "", "const base = iterateSmooth(globalX + 1, globalY, constant[0], constant[1], $bindings.iterations, zoom)", "ce8cafa48121a9466b05c1f0af84d75f2519ab4db210237cc85ac291fc403d76", "3e04065cbf9c389094b96442deb9efd72d584a8880ab25b33582377cc472db88", "66c65e0b35b23b2d1f045ebc4b9526ff9f34c4ad8f387deddebbc142cec3ccb3", "8520a894a1cdd89832fb2750eb673c9c9ca354e64137ab7b2f98953a1bc5e565", true, 1U, kMutation21WitnessCases, kMutation21ControlCases, kMutation21Results},
  MutationView{"normal-right", "normal-three-sample", "mutate normal right sample coordinate", "const right = iterateSmooth(globalX + 1, globalY, constant[0], constant[1], $bindings.iterations, zoom)", "", "const right = iterateSmooth(globalX, globalY, constant[0], constant[1], $bindings.iterations, zoom)", "ad0e24dfb436b1d9a353c9f662a29c736ff41e054eb09bd846ba6cc0576f264a", "5ba5243c6744df3cc79bdf3c3c7c6a000cbb804e3d0936b9101fe3f7632ba490", "c124fce8fea05b2c9f75ce6d3e5f6c9bbe9aa1b2b1de4bdb79a11f98e4b3c8f9", "fa3cb216ac0941e39827719196c4166658bd8c6cf4cb1db3e5d3143f2296925c", true, 1U, kMutation22WitnessCases, kMutation22ControlCases, kMutation22Results},
  MutationView{"normal-up", "normal-three-sample", "mutate normal up sample coordinate", "const up = iterateSmooth(globalX, globalY + 1, constant[0], constant[1], $bindings.iterations, zoom)", "", "const up = iterateSmooth(globalX, globalY, constant[0], constant[1], $bindings.iterations, zoom)", "80ab37e7e4f95e706d4b5473d54d6704ec700dbc78e78462464dc3af644798fb", "59be8b2147353bae92cd1b09433f6d57c1bcd283d158fddf9a5eebff852ebe0e", "32d90bc43c3c826cedfa0bb03c268b34e53babd03187fb3d826ca3a45bf75797", "59e3cfc76f8f46b63c0d269912d1b036d0fa0bb062ace36dd7a46e450954a058", true, 1U, kMutation23WitnessCases, kMutation23ControlCases, kMutation23Results},
  MutationView{"result-trap-number", "out-materialization", "preserve the JS Number trap accumulator instead of forcing an unsafe Float32 result boundary", "trapMin = Math.min(trapMin, trapDistance)", "julia.js:158:7-47", "trapMin = F32(Math.min(trapMin, trapDistance))", "0705f06f3f6101e0f7990e839bd1c4aef343ee08dc7bafccd654669843890eb3", "68ec4220d8cf63fd98aa5a0c94a2ed59c776f3d5081c671ff1bc89f20eb1f358", "abd2a68d17ebff2e2390ab0645e60f7a582dc1f42690228db9e3ae286939eda5", "9115e939e6b95fb0dc42683155c5d69bc2038d15090387c90be7c114e01dac73", true, 1U, kMutation24WitnessCases, kMutation24ControlCases, kMutation24Results},
}};
}
