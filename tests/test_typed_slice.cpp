#include "test_harness.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <limits>
#include <span>
#include <sstream>
#include <string>
#include <vector>

#include "noisemaker/generated/catalog.hpp"
#include "noisemaker/numeric.hpp"
#include "noisemaker/pass_runner.hpp"

namespace {

[[nodiscard]] std::uint32_t rotate_right(std::uint32_t value, std::uint32_t count) {
  return std::rotr(value, static_cast<int>(count));
}

[[nodiscard]] std::array<std::uint8_t, 32> sha256(std::span<const std::uint8_t> input) {
  constexpr std::array<std::uint32_t, 64> constants{
      0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U, 0x3956c25bU, 0x59f111f1U, 0x923f82a4U, 0xab1c5ed5U,
      0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U, 0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U,
      0xe49b69c1U, 0xefbe4786U, 0x0fc19dc6U, 0x240ca1ccU, 0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
      0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U, 0xc6e00bf3U, 0xd5a79147U, 0x06ca6351U, 0x14292967U,
      0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U, 0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U,
      0xa2bfe8a1U, 0xa81a664bU, 0xc24b8b70U, 0xc76c51a3U, 0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
      0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U, 0x391c0cb3U, 0x4ed8aa4aU, 0x5b9cca4fU, 0x682e6ff3U,
      0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U, 0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U};
  std::vector<std::uint8_t> bytes(input.begin(), input.end());
  const std::uint64_t bits = static_cast<std::uint64_t>(bytes.size()) * 8U;
  bytes.push_back(0x80U);
  while ((bytes.size() % 64U) != 56U) bytes.push_back(0U);
  for (int shift = 56; shift >= 0; shift -= 8) bytes.push_back(static_cast<std::uint8_t>(bits >> shift));
  std::array<std::uint32_t, 8> hash{0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
                                    0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U};
  for (std::size_t offset = 0; offset < bytes.size(); offset += 64U) {
    std::array<std::uint32_t, 64> words{};
    for (std::size_t i = 0; i < 16U; ++i) {
      words[i] = (static_cast<std::uint32_t>(bytes[offset + 4U * i]) << 24U) |
                 (static_cast<std::uint32_t>(bytes[offset + 4U * i + 1U]) << 16U) |
                 (static_cast<std::uint32_t>(bytes[offset + 4U * i + 2U]) << 8U) | bytes[offset + 4U * i + 3U];
    }
    for (std::size_t i = 16U; i < words.size(); ++i) {
      const std::uint32_t s0 = rotate_right(words[i - 15U], 7U) ^ rotate_right(words[i - 15U], 18U) ^ (words[i - 15U] >> 3U);
      const std::uint32_t s1 = rotate_right(words[i - 2U], 17U) ^ rotate_right(words[i - 2U], 19U) ^ (words[i - 2U] >> 10U);
      words[i] = words[i - 16U] + s0 + words[i - 7U] + s1;
    }
    std::uint32_t a = hash[0]; std::uint32_t b = hash[1]; std::uint32_t c = hash[2]; std::uint32_t d = hash[3];
    std::uint32_t e = hash[4]; std::uint32_t f = hash[5]; std::uint32_t g = hash[6]; std::uint32_t h = hash[7];
    for (std::size_t i = 0; i < words.size(); ++i) {
      const std::uint32_t s1 = rotate_right(e, 6U) ^ rotate_right(e, 11U) ^ rotate_right(e, 25U);
      const std::uint32_t choice = (e & f) ^ (~e & g);
      const std::uint32_t temporary1 = h + s1 + choice + constants[i] + words[i];
      const std::uint32_t s0 = rotate_right(a, 2U) ^ rotate_right(a, 13U) ^ rotate_right(a, 22U);
      const std::uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
      const std::uint32_t temporary2 = s0 + majority;
      h = g; g = f; f = e; e = d + temporary1; d = c; c = b; b = a; a = temporary1 + temporary2;
    }
    hash[0] += a; hash[1] += b; hash[2] += c; hash[3] += d;
    hash[4] += e; hash[5] += f; hash[6] += g; hash[7] += h;
  }
  std::array<std::uint8_t, 32> output{};
  for (std::size_t i = 0; i < hash.size(); ++i) for (std::size_t lane = 0; lane < 4U; ++lane)
    output[i * 4U + lane] = static_cast<std::uint8_t>(hash[i] >> (24U - lane * 8U));
  return output;
}

[[nodiscard]] std::string hex(std::span<const std::uint8_t> bytes) {
  std::ostringstream output;
  for (std::uint8_t byte : bytes) output << std::hex << std::setfill('0') << std::setw(2) << static_cast<unsigned>(byte);
  return output.str();
}

[[nodiscard]] std::vector<std::uint8_t> little_endian_float_bytes(const noisemaker::Surface& surface) {
  static_assert(std::endian::native == std::endian::little, "oracle float-byte fixtures are little-endian");
  std::vector<std::uint8_t> bytes;
  bytes.reserve(surface.data().size() * 4U);
  for (float value : surface.data()) {
    const std::uint32_t bits = noisemaker::float_bits_to_uint(value);
    for (std::uint32_t shift = 0; shift < 32U; shift += 8U) bytes.push_back(static_cast<std::uint8_t>(bits >> shift));
  }
  return bytes;
}

[[nodiscard]] noisemaker::Surface source(std::size_t width, std::size_t height, std::uint32_t tag) {
  std::vector<std::uint8_t> bytes(width * height * 4U);
  for (std::size_t y = 0; y < height; ++y) for (std::size_t x = 0; x < width; ++x) {
    const std::size_t i = (y * width + x) * 4U;
    bytes[i] = static_cast<std::uint8_t>((31U * x + 17U * y + 13U * tag) % 256U);
    bytes[i + 1U] = static_cast<std::uint8_t>((11U * x + 47U * y + 29U * tag) % 256U);
    bytes[i + 2U] = static_cast<std::uint8_t>((67U * x + 19U * y + 7U * tag) % 256U);
    bytes[i + 3U] = static_cast<std::uint8_t>((255U - 23U * x - 37U * y - 5U * tag) & 255U);
  }
  return noisemaker::Surface::from_rgba8(width, height, bytes);
}

void require_oracle(std::string_view name, const noisemaker::Surface& image, std::string_view float_hash,
                    std::string_view rgba_hash, std::array<std::uint32_t, 4> probe, bool opaque) {
  REQUIRE(image.width() == 8U); REQUIRE(image.height() == 8U);
  const auto floats = little_endian_float_bytes(image);
  if (float_hash == "5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef") {
    REQUIRE(floats.size() == 1024U);
    for (std::uint8_t value : floats) REQUIRE(value == 0U);
  }
  if (hex(sha256(floats)) != float_hash) throw std::runtime_error(std::string(name) + " float oracle hash: " + hex(sha256(floats)));
  const auto rgba = image.to_rgba8();
  if (hex(sha256(rgba)) != rgba_hash) throw std::runtime_error(std::string(name) + " rgba oracle hash: " + hex(sha256(rgba)));
  if (opaque) for (std::size_t i = 3U; i < rgba.size(); i += 4U) REQUIRE(rgba[i] == 255U);
  for (std::size_t lane = 0; lane < probe.size(); ++lane)
    REQUIRE(noisemaker::float_bits_to_uint(image.data()[lane]) == probe[lane]);
}

void require_repeat(const noisemaker::Surface& first, const noisemaker::Surface& second) {
  REQUIRE(little_endian_float_bytes(first) == little_endian_float_bytes(second));
  REQUIRE(first.to_rgba8() == second.to_rgba8());
}

[[nodiscard]] noisemaker::Surface render_bc(const noisemaker::Surface& input) {
  noisemaker::glsl::Bindings bindings; bindings.set_texture("inputTex", input);
  bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(3.0f, -2.0f)); bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(17.0f, 13.0f));
  bindings.set_uniform("brightness", 1.3f); bindings.set_uniform("contrast", 0.72f);
  return noisemaker::run_pass(noisemaker::generated::bind_filter_bc_bc(bindings), 8U, 8U, 0.125f, 7.0f);
}

[[nodiscard]] noisemaker::Surface render_threshold(const noisemaker::Surface& input) {
  noisemaker::glsl::Bindings bindings; bindings.set_texture("inputTex", input);
  bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(3.0f, -2.0f)); bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(17.0f, 13.0f));
  bindings.set_uniform("level", 0.45f); bindings.set_uniform("sharpness", 0.18f);
  return noisemaker::run_pass(noisemaker::generated::bind_filter_threshold_thresh(bindings), 8U, 8U, 0.125f, 7.0f);
}

[[nodiscard]] noisemaker::Surface render_smoothstep(const noisemaker::Surface& input) {
  noisemaker::glsl::Bindings bindings; bindings.set_texture("inputTex", input);
  bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(3.0f, -2.0f)); bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(17.0f, 13.0f));
  bindings.set_uniform("edge0", 0.2f); bindings.set_uniform("edge1", 0.75f);
  return noisemaker::run_pass(noisemaker::generated::bind_filter_smoothstep_smoothstep(bindings), 8U, 8U, 0.125f, 7.0f);
}

[[nodiscard]] noisemaker::Surface render_channel(const noisemaker::Surface& red, const noisemaker::Surface& green, const noisemaker::Surface& blue) {
  noisemaker::glsl::Bindings bindings; bindings.set_texture("rTex", red); bindings.set_texture("gTex", green); bindings.set_texture("bTex", blue);
  bindings.set_uniform("resolution", noisemaker::glsl::Vec2(8.0f)); bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(3.0f, -2.0f));
  bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(17.0f, 13.0f)); bindings.set_uniform("rLevel", 85.0f); bindings.set_uniform("gLevel", 60.0f); bindings.set_uniform("bLevel", 95.0f);
  return noisemaker::run_pass(noisemaker::generated::bind_mixer_channelCombine_channelCombine(bindings), 8U, 8U, 0.125f, 7.0f);
}

void populate_task9_bindings(noisemaker::glsl::Bindings& bindings, std::string_view key,
                             const noisemaker::Surface& input, const noisemaker::Surface& blur,
                             const noisemaker::Surface& color, const noisemaker::Surface& edge,
                             const noisemaker::Surface& simplified, const noisemaker::Surface& text,
                             std::string_view skip = {}) {
  const auto uniform = [&](std::string_view name, noisemaker::glsl::UniformValue value) {
    if (name != skip) bindings.set_uniform(std::string(name), std::move(value));
  };
  const auto texture = [&](std::string_view name, const noisemaker::Surface& surface) {
    if (name != skip) bindings.set_texture(std::string(name), surface);
  };
  uniform("resolution", noisemaker::glsl::Vec2(7.0f, 5.0f));
  uniform("tileOffset", noisemaker::glsl::Vec2(3.0f, -2.0f));
  uniform("fullResolution", noisemaker::glsl::Vec2(17.0f, 13.0f));
  texture("inputTex", input);
  if (key == "filter/celShading:celShadingBlend") {
    texture("colorTex", color); texture("edgeTex", edge);
    uniform("edgeColor", noisemaker::glsl::Vec3(0.17f, 0.63f, 0.91f)); uniform("mixAmount", 0.71f);
  } else if (key == "filter/chroma:chroma") {
    uniform("targetHue", 0.37f); uniform("range", 0.19f); uniform("feather", 0.07f);
  } else if (key == "filter/chrome:chMap") {
    texture("blurTex", blur); uniform("detail", 63.0f); uniform("distortion", 27.0f);
  } else if (key == "filter/colorReplace:colorReplace") {
    uniform("targetColor", noisemaker::glsl::Vec3(0.23f, 0.51f, 0.77f));
    uniform("replaceColor", noisemaker::glsl::Vec3(0.88f, 0.16f, 0.42f));
    uniform("sensitivity", 0.43f); uniform("smoothing", 0.18f);
    uniform("colorMix", 0.67f); uniform("replaceAlpha", 0.82f); uniform("keepAlpha", 0.31f);
  } else if (key == "filter/deriv:deriv") {
    uniform("amount", 1.7f); uniform("renderScale", 0.75f);
  } else if (key == "filter/lensFlare:lensFlare") {
    uniform("brightness", 137.0f); uniform("centerX", 0.29f); uniform("centerY", 0.61f);
    uniform("tint", noisemaker::glsl::Vec3(0.83f, 0.94f, 0.71f));
  } else if (key == "filter/mosaicTiles:mosaicTiles") {
    uniform("tileSize", 4.7f); uniform("groutWidth", 22.0f); uniform("relief", 58.0f);
    uniform("maxOffset", 31.0f); uniform("gapFill", std::int32_t(2));
    uniform("backgroundColor", noisemaker::glsl::Vec3(0.12f, 0.34f, 0.56f)); uniform("seed", std::int32_t(7));
  } else if (key == "filter/photocopy:pcCombine") {
    texture("blurTex", blur); uniform("darkness", 68.0f);
    uniform("inkColor", noisemaker::glsl::Vec3(0.08f, 0.17f, 0.29f));
    uniform("paperColor", noisemaker::glsl::Vec3(0.93f, 0.84f, 0.61f));
  } else if (key == "filter/relief:rlShade") {
    texture("blurTex", blur); uniform("detail", 57.0f); uniform("lightAngle", 123.0f);
    uniform("balance", 44.0f); uniform("graininess", 36.0f);
    uniform("inkColor", noisemaker::glsl::Vec3(0.09f, 0.18f, 0.27f));
    uniform("paperColor", noisemaker::glsl::Vec3(0.92f, 0.79f, 0.63f));
  } else if (key == "filter/ridge:ridge") {
    uniform("level", 0.42f);
  } else if (key == "filter/scatter:scatterJitter") {
    uniform("radius", 2.7f); uniform("seed", std::int32_t(11));
  } else if (key == "filter/simpleAberration:chromaticAberration") {
    uniform("displacement", 0.037f);
  } else if (key == "filter/text:text") {
    texture("textTex", text); uniform("matteColor", noisemaker::glsl::Vec3(0.14f, 0.35f, 0.73f));
    uniform("matteOpacity", 0.38f);
  } else if (key == "filter/unsharpMask:usmCombine") {
    texture("blurTex", blur); uniform("amount", 173.0f); uniform("threshold", 14.0f);
  } else if (key == "filter/watercolor:wcComposite") {
    texture("simplifiedTex", simplified); uniform("shadowIntensity", 61.0f); uniform("paperTexture", 43.0f);
  }
}

[[nodiscard]] noisemaker::Surface render_task9(std::string_view key) {
  const noisemaker::Surface input = source(5U, 3U, 1U);
  const noisemaker::Surface blur = source(3U, 5U, 11U);
  const noisemaker::Surface color = source(7U, 2U, 23U);
  const noisemaker::Surface edge = source(4U, 6U, 37U);
  const noisemaker::Surface simplified = source(6U, 4U, 41U);
  const noisemaker::Surface text = source(2U, 7U, 53U);
  noisemaker::glsl::Bindings bindings;
  populate_task9_bindings(bindings, key, input, blur, color, edge, simplified, text);
  return noisemaker::run_pass(noisemaker::generated::bind(key, bindings), 7U, 5U, 0.125f, 7.0f);
}

[[nodiscard]] noisemaker::Surface glowing_edge_source() {
  constexpr std::size_t width = 6U;
  constexpr std::size_t height = 4U;
  std::vector<std::uint8_t> bytes(width * height * 4U);
  for (std::size_t y = 0; y < height; ++y) for (std::size_t x = 0; x < width; ++x) {
    const std::size_t i = (y * width + x) * 4U;
    bytes[i] = static_cast<std::uint8_t>(45U + 7U * x + 11U * y);
    bytes[i + 1U] = static_cast<std::uint8_t>(73U + 5U * x + 9U * y);
    bytes[i + 2U] = static_cast<std::uint8_t>(22U + 3U * x + 13U * y);
    bytes[i + 3U] = static_cast<std::uint8_t>(255U - 4U * x - 7U * y);
  }
  return noisemaker::Surface::from_rgba8(width, height, bytes);
}

void populate_task10_bindings(noisemaker::glsl::Bindings& bindings, std::string_view key,
                              const noisemaker::Surface& input, const noisemaker::Surface& blur,
                              const noisemaker::Surface& tex, float polygon_smoothing = 0.12f,
                              std::string_view skip = {}) {
  const auto uniform = [&](std::string_view name, noisemaker::glsl::UniformValue value) {
    if (name != skip) bindings.set_uniform(std::string(name), std::move(value));
  };
  const auto texture = [&](std::string_view name, const noisemaker::Surface& surface) {
    if (name != skip) bindings.set_texture(std::string(name), surface);
  };
  uniform("resolution", noisemaker::glsl::Vec2(7.0f, 5.0f));
  uniform("tileOffset", noisemaker::glsl::Vec2(3.0f, -2.0f));
  uniform("fullResolution", noisemaker::glsl::Vec2(17.0f, 13.0f));
  texture("inputTex", input);
  if (key == "filter/channel:channel") {
    uniform("channel", std::int32_t(2)); uniform("scale", 2.37f); uniform("offset", 0.19f);
  } else if (key == "filter/chromaticAberration:chromaticAberration") {
    uniform("aberrationAmt", 73.5f); uniform("passthru", 42.25f);
  } else if (key == "filter/glowingEdge:glowingEdge") {
    uniform("alpha", 0.73f); uniform("sobelMetric", 3.0f); uniform("width", 0.4f);
  } else if (key == "filter/highPass:hpCombine") {
    texture("blurTex", blur); uniform("mono", false);
  } else if (key == "filter/pixels:pixels") {
    uniform("size", 3.7f);
  } else if (key == "filter/plasticWrap:pwSpec") {
    texture("blurTex", blur); uniform("highlight", 77.3f); uniform("smoothness", 31.7f);
    uniform("lightDirection", noisemaker::glsl::Vec3(0.31f, 0.79f, 0.43f));
  } else if (key == "filter/seamless:seamless") {
    uniform("blend", 0.31f); uniform("repeat", 2.3f); uniform("curve", std::int32_t(1));
  } else if (key == "filter/sine:sine") {
    uniform("amount", 8.7f); uniform("colorMode", 1.0f);
  } else if (key == "filter/vignette:vignette") {
    uniform("vignetteBrightness", 0.21f); uniform("alpha", 0.81f);
  } else if (key == "mixer/alphaMask:alphaMask") {
    texture("tex", tex); uniform("mixAmt", 47.0f); uniform("maskMode", false);
  } else if (key == "mixer/applyMode:applyMode") {
    texture("tex", tex); uniform("mode", std::int32_t(1)); uniform("mixAmt", 47.0f);
  } else if (key == "mixer/thresholdMix:thresholdMix") {
    texture("tex", tex); uniform("mode", std::int32_t(1)); uniform("quantize", std::int32_t(3));
    uniform("mapSource", std::int32_t(1)); uniform("threshold", 0.41f); uniform("range", 0.19f);
    uniform("thresholdR", 0.22f); uniform("rangeR", 0.0f); uniform("thresholdG", 0.48f);
    uniform("rangeG", 0.17f); uniform("thresholdB", 0.69f); uniform("rangeB", 0.0f);
  } else if (key == "synth/polygon:shape") {
    uniform("tileOffset", noisemaker::glsl::Vec2(3.0f, 3.0f));
    uniform("fullResolution", noisemaker::glsl::Vec2(13.0f, 11.0f));
    // createCanonicalBindings owns this built-in and overwrites caller uniforms
    // with the output surface aspect (7 / 5) after merging them.
    uniform("aspect", 7.0f / 5.0f); uniform("sides", std::int32_t(3));
    uniform("radius", 0.4f); uniform("smoothing", polygon_smoothing); uniform("rotation", 23.0f);
    uniform("fgColor", noisemaker::glsl::Vec3(0.14f, 0.73f, 0.31f)); uniform("fgAlpha", 0.83f);
    uniform("bgColor", noisemaker::glsl::Vec3(0.91f, 0.22f, 0.58f)); uniform("bgAlpha", 0.47f);
  }
}

[[nodiscard]] noisemaker::Surface render_task10(std::string_view key, float polygon_smoothing = 0.12f,
                                                std::string_view variant = {}) {
  const noisemaker::Surface regular_input = source(5U, 3U, 1U);
  const noisemaker::Surface edge_input = glowing_edge_source();
  const noisemaker::Surface blur = source(3U, 5U, 11U);
  const noisemaker::Surface tex = source(7U, 2U, 23U);
  const noisemaker::Surface& input = key == "filter/glowingEdge:glowingEdge" ? edge_input : regular_input;
  noisemaker::glsl::Bindings bindings;
  populate_task10_bindings(bindings, key, input, blur, tex, polygon_smoothing);
  if (variant == "channel0") bindings.set_uniform("channel", std::int32_t(0));
  else if (variant == "channel1") bindings.set_uniform("channel", std::int32_t(1));
  else if (variant == "channel3") bindings.set_uniform("channel", std::int32_t(3));
  else if (variant == "fullResolutionZero") bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(0.0f));
  else if (variant == "metric0") bindings.set_uniform("sobelMetric", 0.0f);
  else if (variant == "metric1") bindings.set_uniform("sobelMetric", 1.0f);
  else if (variant == "metric2") bindings.set_uniform("sobelMetric", 2.0f);
  else if (variant == "mono") bindings.set_uniform("mono", true);
  else if (variant == "earlyReturn") bindings.set_uniform("size", 0.75f);
  else if (variant == "zeroLightFallback") bindings.set_uniform("lightDirection", noisemaker::glsl::Vec3(0.0f));
  else if (variant == "oppositeLightHalfFallback") bindings.set_uniform("lightDirection", noisemaker::glsl::Vec3(0.0f, 0.0f, -1.0f));
  else if (variant == "linear") bindings.set_uniform("curve", std::int32_t(0));
  else if (variant == "sharp") bindings.set_uniform("curve", std::int32_t(2));
  else if (variant == "zeroBlend") bindings.set_uniform("blend", 0.0f);
  else if (variant == "luminance") bindings.set_uniform("colorMode", 0.0f);
  else if (variant == "maskReturn") bindings.set_uniform("maskMode", true);
  else if (variant == "alphaNegative") bindings.set_uniform("mixAmt", -37.0f);
  else if (variant == "brightnessNegative") {
    bindings.set_uniform("mode", std::int32_t(0)); bindings.set_uniform("mixAmt", -47.0f);
  } else if (variant == "saturation") bindings.set_uniform("mode", std::int32_t(2));
  else if (variant == "luminanceHard" || variant == "luminanceSoft") {
    bindings.set_uniform("mode", std::int32_t(0)); bindings.set_uniform("quantize", std::int32_t(0));
    bindings.set_uniform("mapSource", std::int32_t(0)); bindings.set_uniform("range", variant == "luminanceHard" ? 0.0f : 0.19f);
    bindings.set_uniform("rangeG", 0.0f);
  } else if (variant == "sides5ZeroAlpha") {
    bindings.set_uniform("sides", std::int32_t(5)); bindings.set_uniform("fgAlpha", 0.0f);
    bindings.set_uniform("bgAlpha", 0.0f);
  }
  return noisemaker::run_pass(noisemaker::generated::bind(key, bindings), 7U, 5U, 0.125f, 7.0f);
}

TEST(typed_slice_five_kernel_external_oracles_are_repeatable_and_top_down) {
  const noisemaker::Surface a = source(5U, 3U, 1U);
  const noisemaker::Surface r = source(5U, 3U, 11U);
  const noisemaker::Surface g = source(3U, 5U, 23U);
  const noisemaker::Surface b = source(7U, 2U, 37U);
  noisemaker::glsl::Bindings clear_bindings;
  const noisemaker::Surface clear = noisemaker::run_pass(noisemaker::generated::bind_filter_wormhole_clear(clear_bindings), 8U, 8U, 0.125f, 7.0f);
  require_oracle("clear", clear, "5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef", "5341e6b2646979a70e57653007a1f310169421ec9bdd9f1a5648f75ade005af1", {0U, 0U, 0U, 0U}, false);
  const noisemaker::Surface bc = render_bc(a);
  require_oracle("bc", bc, "17e28b5ca13d1a21234aaaf6d3a2fc2f605f29413ad1baa1db1b6343010878e3", "a10774e92b60d5558b372d349fcac02f3424fd92cd880f2701d1d00f3154767e", {0xbdff1bcbU, 0xbbe8d8a1U, 0xbe2ca892U, 0x3f7afafbU}, false);
  const noisemaker::Surface threshold = render_threshold(a);
  require_oracle("threshold", threshold, "61f2a88622e0a75332fb6994f5ae82a21c6889df4296e9c64b58f2de9d41d45e", "63d3dc8653662baff87afd576ae73ecfc61d65c688cebfde7406153e6484ac65", {0U, 0U, 0U, 0x3f800000U}, true);
  const noisemaker::Surface smoothstep = render_smoothstep(a);
  require_oracle("smoothstep", smoothstep, "200eb65fed133e0640ed0165c4be24923e6fda1c236c3ea8b5d07f8747566b45", "340558b647177c7f72bbd4b2fcbecef4facfd780a5e6fbfaf7231961895058a7", {0U, 0U, 0U, 0x3f7afafbU}, false);
  const noisemaker::Surface channel = render_channel(r, g, b);
  require_oracle("channel", channel, "8bd32d6a3e760ed40d064c8671aec9e9ce7e491d666083c5cf2785224fb4a290", "a5ac13cccc6fdb4d53bd7fefc545b7fedcbf5cca1ec93b7ab51fe746438c342f", {0x3e8a45a8U, 0x3e9e90d8U, 0x3e9e8098U, 0x3f800000U}, true);
  noisemaker::glsl::Bindings clear_again_bindings;
  require_repeat(clear, noisemaker::run_pass(noisemaker::generated::bind_filter_wormhole_clear(clear_again_bindings), 8U, 8U, 0.125f, 7.0f));
  require_repeat(bc, render_bc(a)); require_repeat(threshold, render_threshold(a));
  require_repeat(smoothstep, render_smoothstep(a)); require_repeat(channel, render_channel(r, g, b));
}

TEST(typed_slice_test_sha256_has_standard_empty_and_zero_block_vectors) {
  const std::vector<std::uint8_t> empty;
  REQUIRE(hex(sha256(empty)) == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
  const std::vector<std::uint8_t> zeroes(1024U, 0U);
  REQUIRE(hex(sha256(zeroes)) == "5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef");
}

TEST(typed_math_slice_sixteen_external_oracles_are_repeatable) {
  struct Fixture { std::string_view key; std::string_view floats; std::string_view rgba; std::uint32_t first; };
  constexpr std::array<Fixture, 16> fixtures{{
      {"filter/celShading:celShadingBlend", "3040fca866a32e77c2d5828672a9d983fd8b78c8f19e81030444b7f922cc144a", "998a939393905a859371711b5c971f0435ed757720ac5b5a9348e59d652a6409", 0x3e0a9e59U},
      {"filter/chroma:chroma", "efc59e60e7b127541dbb28cf18d5981144fc4a22f02d4f6d710be29ea0ac06fe", "72ef0585ff112ea147febd8ede9f8d3965215513c44ddf0feb188790f371c637", 0x3f4234f7U},
      {"filter/chrome:chMap", "5d0c6dd88fe0a39b97b994002b7431214d59760f9133c2ff40d1e3bebd8ec119", "bc19edaad2c576252a6f9ea3420422d08286039b8cc15f88aa0e7a6734f18bf8", 0x3d70c7b5U},
      {"filter/colorReplace:colorReplace", "f672cb72086923fa32c34cc12915196bccd211ea450d6cac6dee39649b4d3814", "33c8b3e38c7d93521a58581c2b1bc0e56547d2afc8d5673aeddca4d2bf26d0ff", 0x3d9c2f9cU},
      {"filter/deriv:deriv", "43e591217a059e9a86f3e00e52a91b0539c2cc3783619dd0f45de04c292fd3a2", "6a3cbb07be0a133257bd1ca518d82c8269c5b47bd4abd975fe1cb530b70c900e", 0x3c88d638U},
      {"filter/lensFlare:lensFlare", "046d8dc804bf93f97533a85f05783b14a6dcedf09afede6a3660e600676d8599", "42d035c4d765ef017d27b641bb5a2a96f03122ca19032c1e02233b8d7915cbc4", 0x3d85d166U},
      {"filter/mosaicTiles:mosaicTiles", "b45240877494b59e366f9d9441bd2e125365bcd87f000ca363839cdc8bd725b0", "bacfcc449e6470bfa16347c7b00cf9a2807ec433a060282b32358f2b39a273e1", 0x3c311fc9U},
      {"filter/photocopy:pcCombine", "5c30639723acd4eed15826649692300488800a81c4c20d0b9a2cdafb4bfb4405", "76d6b92b4fb7f0c8e4f465da28246117a0ad5ac0c9c45e43085d1280f0877c6f", 0x3da3d70aU},
      {"filter/relief:rlShade", "1dba0f21095568d3f62d27d313993dfaa6bae04c1fb0fc81156d583ea3a2d1d6", "f5205caa03ccc976eefc1c41b9f535ea578a23510cf6154642b16634da32abe6", 0x3f078889U},
      {"filter/ridge:ridge", "14e083e0d2e604d0b5559ebbdd175316ae313160e5aca89c468678ef3932eff9", "5d220bfe0488a6b32a233b82932edee6b8b5e094c478b95f54289d6e0edc1b8b", 0x3eba3eaaU},
      {"filter/scatter:scatterJitter", "3894d5739e765cf71a39a082abb8315bfd5fac4a7d6be6c4f8a8cf9b87ae5c8c", "d3425ff7218c66a0a0711e3ed96f3c343df410227e22cececf9ad51dc48c42be", 0x3df0f0f1U},
      {"filter/simpleAberration:chromaticAberration", "09c9d93ea78ddb0f877dd993f6af3f5b7d7ffd9c10d05fe4dc2f4b505f1af7e6", "42c44f9ac2cd9b55e1dc92abd18afa3960b6a7982d44e9463db03717b207b760", 0x3e30b0b1U},
      {"filter/text:text", "a6dba9bbe4b6dfeab15bfc45089f5255e359d292a1a7199ca76ce42da549b134", "cde2a1348bc93ad9c33a91b3ae4c3c711af183490b365ffd967fd296f9e7e2de", 0x3f15f244U},
      {"filter/unsharpMask:usmCombine", "dcb8cd1ae6f41bba9ab35d807a4d89d158605be5a2fb5b8bd199def2d06970a5", "c5c85cddd59a4e9c9c6e98e316ad8de4074dffbd4787c841a5cd1b6f80829630", 0x00000000U},
      {"filter/watercolor:wcComposite", "409c8f37bb8778750cedc218f2ca6d488ad6fffe1c090c786d7e3c582bde5a3b", "1bdc0c3ae9f57ef445f25fa3e3cac55cbcfbba28745b0a2af58c885a6d514bc4", 0x3d3f48c0U},
      {"filter/watercolor:wcSeed", "29f8cb0bcb53dac6c6c0f32405d5ee0670617a236c5b59c2aa9d3536637abe0a", "b758a60117b29acbcaa0d2e74eaef9487d06f80d1cf5363df30967a981e0df2f", 0x3d50d0d1U},
  }};
  for (const Fixture& fixture : fixtures) {
    const noisemaker::Surface first = render_task9(fixture.key);
    const noisemaker::Surface second = render_task9(fixture.key);
    REQUIRE(first.width() == 7U); REQUIRE(first.height() == 5U);
    const std::string actual_float = hex(sha256(little_endian_float_bytes(first)));
    const std::string actual_rgba = hex(sha256(first.to_rgba8()));
    if (actual_float != fixture.floats) {
      std::ostringstream detail;
      detail << fixture.key << " float oracle hash: " << actual_float << " probes:";
      for (std::size_t index = 0; index < std::min<std::size_t>(12U, first.data().size()); ++index)
        detail << ' ' << std::hex << noisemaker::float_bits_to_uint(first.data()[index]);
      throw std::runtime_error(detail.str());
    }
    if (actual_rgba != fixture.rgba) throw std::runtime_error(std::string(fixture.key) + " rgba oracle hash: " + actual_rgba);
    REQUIRE(noisemaker::float_bits_to_uint(first.data()[0]) == fixture.first);
    require_repeat(first, second);
  }
}

TEST(typed_math_slice_all_sixteen_factories_fail_closed_on_empty_bindings) {
  constexpr std::array<std::string_view, 16> keys{{
      "filter/celShading:celShadingBlend", "filter/chroma:chroma", "filter/chrome:chMap",
      "filter/colorReplace:colorReplace", "filter/deriv:deriv", "filter/lensFlare:lensFlare",
      "filter/mosaicTiles:mosaicTiles", "filter/photocopy:pcCombine", "filter/relief:rlShade",
      "filter/ridge:ridge", "filter/scatter:scatterJitter", "filter/simpleAberration:chromaticAberration",
      "filter/text:text", "filter/unsharpMask:usmCombine", "filter/watercolor:wcComposite", "filter/watercolor:wcSeed"}};
  for (std::string_view key : keys) {
    noisemaker::glsl::Bindings empty;
    REQUIRE_THROWS_AS(noisemaker::generated::bind(key, empty), noisemaker::glsl::KernelBindingError);
  }
}

TEST(typed_control_flow_slice_external_oracles_are_repeatable) {
  struct Fixture {
    std::string_view key;
    std::string_view floats;
    std::string_view rgba;
    std::array<std::uint32_t, 12> probes;
  };
  constexpr std::array<Fixture, 13> fixtures{{
      {"filter/channel:channel", "757bbae80510cd028b6a64b02c19959d9c058b2b64dfc7273870e9fe219e6ebd", "c584bb267993197294a6fbdf101348d51797a91acac9eec19c5ebd23f5e47bde", {0x3e829712U,0x3e829712U,0x3e829712U,0x3f800000U,0x3dfc43e9U,0x3dfc43e9U,0x3dfc43e9U,0x3f800000U,0x3f384280U,0x3f384280U,0x3f384280U,0x3f800000U}},
      {"filter/chromaticAberration:chromaticAberration", "4ca788af3c142403813627704f6e68c9e961989a11323e2a10ec3bea01206125", "e25e1fa9f910c3cd439d465ce68a50f000eafaa4ed5d708ed399f0b1a2cea61e", {0x3d307303U,0x3dc4cf0dU,0x3cbe05b4U,0x3f7afafbU,0x3eb3d7afU,0x3e5261beU,0x3f307303U,0x3f35b5b6U,0x3f110fc8U,0x3f0dab1cU,0x3e416a60U,0x3ea8a8a9U}},
      {"filter/glowingEdge:glowingEdge", "d4ecd1b91848d86890b86d7611ebaeee5c753d388c9fe7a5e8212f193a313163", "8fd25b2c5bb1124cb6d1348c74355432625bd247128027ae4c7a7f6b3ce55c87", {0x3e6b9ca4U,0x3eb92b60U,0x3dec4186U,0x3f800000U,0x3f1c1552U,0x3f39792fU,0x3ec312aaU,0x3f6cecedU,0x3f1d14a1U,0x3f29aeb4U,0x3ee296beU,0x3f56d6d7U}},
      {"filter/highPass:hpCombine", "b7d5dab26de4a4fe50a8cdc6439c52133a733625b9651abf31a4dc28bd37e40e", "37f0995e070ba207c0aac4722cabb5c78617281f23562193509956649577990d", {0x00000000U,0x3ebbbbbcU,0x3e66e6e6U,0x3f7afafbU,0x3d38b8b8U,0x3e66e6e6U,0x3ed3d3d4U,0x3f27a7a8U,0x3f800000U,0x3f800000U,0x3f1a1a1aU,0x3ea8a8a9U}},
      {"filter/pixels:pixels", "feb89b0e6a128d533471c06cac88fe82d78874442cfbd509204de736ad6bbc0d", "59adf71406e87307e5f915828cfce8b52ec0bb667bd62c853dc7181f413c9641", {0x3df0f0f1U,0x3e989899U,0x3dd0d0d1U,0x3f55d5d6U,0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
      {"filter/plasticWrap:pwSpec", "f39c59c7f4aa4ba745d0d653b2b24d7bd77b4c5cfd9a74771fd45fd0e23eab3c", "9d1599d1124a34c34d246cf95de8de038e299917769d139057cd453d05449d3a", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3eb8b8b9U,0x3ec4c4c5U,0x3f20a0a1U,0x3f27a7a8U,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
      {"filter/seamless:seamless", "95627615549b377e800f657471499a978d7c445c1a35cfc9ac9915e4bdf73bf0", "90255d926242b26be8853e926acca831507d557afe72a00016c9e134a772dea2", {0x3e8f1222U,0x3eb5fd45U,0x3ee73c4fU,0x3f800000U,0x3ef0e420U,0x3eca102eU,0x3f607f02U,0x3f800000U,0x3eb91a13U,0x3ec4e750U,0x3f2040d9U,0x3f800000U}},
      {"filter/sine:sine", "73b6f26c811b0a8676d475bd8eed36917f3ab0d914f87da8f50da49a0d197014", "6f09375716db998f9df1655f106383dde3444800b8e1242a5390f01be0b916d9", {0x3f36edbcU,0x3f6af852U,0x3f1e4797U,0x3f7afafbU,0x3e8af2fcU,0x3f6d7d57U,0x3f5cff8aU,0x3f35b5b6U,0x3e90dd22U,0x3e650b52U,0x3f7727f2U,0x3ea8a8a9U}},
      {"filter/vignette:vignette", "94a2b6f3415386e718d1d3ba3922cb4126241a5797e426b2159e07385e042e75", "03f0b8e7644def6fbf6fa486b93646041c870baff6684fb98ff8171f3d56dab7", {0x3dc6ddf3U,0x3e110c83U,0x3da4a7caU,0x3f7afafbU,0x3eb7080eU,0x3e6f5ee4U,0x3f24f08eU,0x3f35b5b6U,0x3eeae795U,0x3ee690f7U,0x3e5e860dU,0x3ea8a8a9U}},
      {"mixer/alphaMask:alphaMask", "7d32bb110d9181320c62787b1014acc5dc4b163ce451503889fb796ca4852661", "bf47b573aca6724cdbcc77923827a042542265ed995f492904a4f3887923f92b", {0x3e0fe133U,0x3efabf1eU,0x3ef95b24U,0x3f7afafbU,0x3efa07e3U,0x3f0c5ca8U,0x3f1193a0U,0x3f35b5b6U,0x3f71a4d8U,0x3db858c6U,0x3e8ab45aU,0x3f5ddddeU}},
      {"mixer/applyMode:applyMode", "7aeee2945e2264b2706af1000de073f87afa3de89fb58b74d7d45c5e489fc462", "901503d50bab78d19f2bdd7f32efd5a6166653885a965813a1a12b735c9517e5", {0x3dc01c46U,0x3eaff106U,0x3eb6cb47U,0x3f7afafbU,0x3efb291fU,0x3f4760fbU,0x3ea6022bU,0x3f35b5b6U,0x3f4f0f0fU,0x3e0ff65cU,0x3e9cc8c2U,0x3f5ddddeU}},
      {"mixer/thresholdMix:thresholdMix", "f6e338ca581f3243524f124f3db407c3e0a56c42d9563eaba6901f48eb373712", "9499f26e19394e0bd91fad082d820362851877598640cfbdf87f9719ffa62b7e", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f088889U,0x3f3cbcbdU,0x3f50d0d1U,0x3ed82d83U,0x3f76f6f7U,0x3f27a7a8U,0x3e64e4e5U,0x3f022cd8U}},
      {"synth/polygon:shape", "17c3ee338cf903cacfcf422df124a54bc7d9b8497339fca260fe3b8e435b011f", "22dc2377820085ffdead0646a681390f2285f1dc2de1fba0283145cec687a69c", {0x3edafb7fU,0x3dd3c361U,0x3e8b923aU,0x3ef0a3d7U,0x3dedfa44U,0x3f1b1c43U,0x3e83bcd3U,0x3f547ae1U,0x3edafb7fU,0x3dd3c361U,0x3e8b923aU,0x3ef0a3d7U}},
  }};
  const noisemaker::Surface polygon_nonzero_before = render_task10("synth/polygon:shape", 0.12f);
  const noisemaker::Surface polygon_zero = render_task10("synth/polygon:shape", 0.0f);
  const noisemaker::Surface polygon_nonzero_after = render_task10("synth/polygon:shape", 0.12f);
  const noisemaker::Surface polygon_zero_after = render_task10("synth/polygon:shape", 0.0f);
  REQUIRE(hex(sha256(little_endian_float_bytes(polygon_nonzero_before))) == "17c3ee338cf903cacfcf422df124a54bc7d9b8497339fca260fe3b8e435b011f");
  REQUIRE(hex(sha256(polygon_nonzero_before.to_rgba8())) == "22dc2377820085ffdead0646a681390f2285f1dc2de1fba0283145cec687a69c");
  const std::string polygon_zero_float = hex(sha256(little_endian_float_bytes(polygon_zero)));
  if (polygon_zero_float != "1d15ee530fda3a6edcc2234b7c796461eab1b0156cba3916adec7e610313f850") {
    std::ostringstream detail;
    detail << "polygon zero float oracle hash: " << polygon_zero_float << " foreground pixels:";
    for (std::size_t pixel = 0; pixel < 35U; ++pixel) {
      if (noisemaker::float_bits_to_uint(polygon_zero.data()[pixel * 4U]) == 0x3dedfa44U)
        detail << " (" << (pixel % 7U) << ',' << (pixel / 7U) << ')';
    }
    throw std::runtime_error(detail.str());
  }
  REQUIRE(hex(sha256(polygon_zero.to_rgba8())) == "3968f2377d75bb572eebc82b4640e94594775758817197a5dae711f8426fb885");
  require_repeat(polygon_nonzero_before, polygon_nonzero_after);
  require_repeat(polygon_zero, polygon_zero_after);
  for (const Fixture& fixture : fixtures) {
    const noisemaker::Surface first = render_task10(fixture.key);
    const noisemaker::Surface second = render_task10(fixture.key);
    REQUIRE(first.width() == 7U); REQUIRE(first.height() == 5U);
    const std::string actual_float = hex(sha256(little_endian_float_bytes(first)));
    const std::string actual_rgba = hex(sha256(first.to_rgba8()));
    if (actual_float != fixture.floats) {
      std::ostringstream detail;
      detail << fixture.key << " float oracle hash: " << actual_float << " probes:";
      for (std::size_t pixel : {0U, 17U, 34U}) for (std::size_t lane = 0; lane < 4U; ++lane)
        detail << ' ' << std::hex << noisemaker::float_bits_to_uint(first.data()[pixel * 4U + lane]);
      throw std::runtime_error(detail.str());
    }
    if (actual_rgba != fixture.rgba) throw std::runtime_error(std::string(fixture.key) + " rgba oracle hash: " + actual_rgba);
    constexpr std::array<std::size_t, 3> probe_pixels{0U, 17U, 34U};
    for (std::size_t probe = 0; probe < probe_pixels.size(); ++probe)
      for (std::size_t lane = 0; lane < 4U; ++lane)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[probe_pixels[probe] * 4U + lane]) ==
                fixture.probes[probe * 4U + lane]);
    require_repeat(first, second);
  }

}

TEST(typed_control_flow_slice_external_branch_oracles_cover_every_arm) {
  struct Fixture { std::string_view key; std::string_view variant; std::string_view floats; std::string_view rgba; };
  constexpr std::array<Fixture, 23> fixtures{{
      {"filter/channel:channel", "channel0", "f06aad98061e763aeaaeb3642a7c6f6193c325fa6ae2f718a8904358e5778d00", "f8956632116fec613352479918e6907d8735e45021a48503cc08bb2c773cc5f6"},
      {"filter/channel:channel", "channel1", "7188cfe8d07b5c3ecf55d2c2dd4f2e421d6bbc50c019b6132673a3363dfc9b6c", "c29398951217bef5ae55ea839afb45b41a80459ea27eb5fcc12807d36cb83361"},
      {"filter/channel:channel", "channel3", "05b55b15d8e517d4d2a0370f61a2a69338092d1228995929b7db7cadd4377677", "b4d9bf4bf793c1a8c0169e66f270a626162fe24aaaf59f8e5eb62027e09b58ab"},
      {"filter/chromaticAberration:chromaticAberration", "fullResolutionZero", "d8a8c910968045fd854b6d28bae45cf531116d05ab93934560ffd8c8f49f35a0", "a5689109e8eb8c4d94b1ae4541dfb920d38ba23d866ed323220a24302f55690e"},
      {"filter/glowingEdge:glowingEdge", "metric0", "2f2df1917198e3d97062753223fef2edb44a29afa26aadebe7f51206b8a84f7f", "8f42b60bab0ab75aea84707043c8ae0afc3047b1fc1aa420a56b557d6abaaf3d"},
      {"filter/glowingEdge:glowingEdge", "metric1", "93a6f3e16620529b6674f42386898f61213e89a71a307ba5003b2a4298748774", "c361423fb4e4852699976ef7419619ac87aba5a98ca09e3ee673557d2d61b568"},
      {"filter/glowingEdge:glowingEdge", "metric2", "9d750577c54c98822192665221ffd620e8543936a490b7d983023072aac824a9", "4fd31f9f94d8f89761bb05af87b02285ae12da1e2a89567da829f1746c47ed83"},
      {"filter/highPass:hpCombine", "mono", "7eafa5965c9f8245f535a88d28f75de4a19ad186fb92afa7131ee5c9b3d7a358", "3dea99c45113cd58157c0de11127d3df3404a909eb6a9e90681556c161cf4caf"},
      {"filter/pixels:pixels", "earlyReturn", "bde61fe2cc345cd2979280e465847046eec54926ac7a5569ab36b7c9d4fac749", "5f07b0549bb0b7480f9f9709f6e2d863b9e1f93ebe4a6147459092c931e38718"},
      {"filter/plasticWrap:pwSpec", "zeroLightFallback", "f39c59c7f4aa4ba745d0d653b2b24d7bd77b4c5cfd9a74771fd45fd0e23eab3c", "9d1599d1124a34c34d246cf95de8de038e299917769d139057cd453d05449d3a"},
      {"filter/plasticWrap:pwSpec", "oppositeLightHalfFallback", "f39c59c7f4aa4ba745d0d653b2b24d7bd77b4c5cfd9a74771fd45fd0e23eab3c", "9d1599d1124a34c34d246cf95de8de038e299917769d139057cd453d05449d3a"},
      {"filter/seamless:seamless", "linear", "bf23e99fe10fa918184d272409eedc549341302a770bea6d1d1f6dd1d8454dd9", "625bf1a9f9c15319aacb8c2a366a08b7d02476b83f3f2d685c1bcc1f690d9f2c"},
      {"filter/seamless:seamless", "sharp", "67fb825c82e87193a565ffb6c9cb1c18081c20513690255ae4c714d37c821a03", "98ce2fb4c75815268e9fd8f8a5e4857dda251f1d85eb96310fbc759caf029837"},
      {"filter/seamless:seamless", "zeroBlend", "43633d6a9d949ac1d965090c18be1e4709a35cc680f0348e2ee0bf735c7f7672", "002a6dc460f3a727c0ed3cd108dcad1f1bb6bc925acdd86cba0006dbb834b862"},
      {"filter/sine:sine", "luminance", "1361edb9630997113f9d535468ef0caf947c86d7e6c57be87066cb6d384c8d3f", "ecc2703ea467bb15781f2d5f5688befde66441b5e2d0ac1972a206bc06129cbc"},
      {"filter/vignette:vignette", "fullResolutionZero", "2da1d72b224dac747a3cb700bceed7447e7843ce3b94a58c5bf5efff8f82e92c", "65daf291de28c048faf144e018b39b2ff6082c1c993b280154e961e1f02ece79"},
      {"mixer/alphaMask:alphaMask", "maskReturn", "32f419f5aa78ef7d141a55987830d63c2e54572b2186933f758d148914ca701e", "40ac299412b2a65053a0174a978036379495780ea1d38970bbf84c2d32633d93"},
      {"mixer/alphaMask:alphaMask", "alphaNegative", "46c4fde02a2fef009e5c3096c80ec118d87985e9110a8ae8b58c2790798a2809", "e8d9a5f791aab677a0fa458ec31ba9150664840298e469e93d015b30115d7277"},
      {"mixer/applyMode:applyMode", "brightnessNegative", "f423203707503dcc17cd0527109c103f90cc08445bf6ec59923c2634d99c6b24", "a06677e876ad65595f255ab53c23c6894f65ebba637d750459257a7b51b308c0"},
      {"mixer/applyMode:applyMode", "saturation", "437d09a1c541faa2e055b059738dfde5385b318fca5ad562aa8afbd4e1ab0fc8", "935faeac913cea75f60785751cdbdbfcde1a9b23b5d0cf493d5d14cb1fd31999"},
      {"mixer/thresholdMix:thresholdMix", "luminanceHard", "db401328e3c93cfb1de2e15d37f2164f3f8c6253a348fba2fbacb1a5bffa48ca", "8af374ab1f9d8e59a3642d59639a613fd32d0dbbcbbfbd81d56a8aca006e3683"},
      {"mixer/thresholdMix:thresholdMix", "luminanceSoft", "0b3c8ef646c70193f4b0531a0f8da5653d8703c03a9ccecf73911443131a5073", "4e22d25a7b54b744a022600f3daf358e83428e6c65d0be89b51818ae77be198b"},
      {"synth/polygon:shape", "sides5ZeroAlpha", "738c079dff6c9b77a0891ac42db1cabcab933a672b14aed8ecfcf94c0e77bb40", "24045c10c12a89f4c11e3b88ea34558fcdf926a8c1008cd08cc33bc71407c774"},
  }};
  for (const Fixture& fixture : fixtures) {
    const noisemaker::Surface first = render_task10(fixture.key, 0.12f, fixture.variant);
    const noisemaker::Surface second = render_task10(fixture.key, 0.12f, fixture.variant);
    const std::string actual_float = hex(sha256(little_endian_float_bytes(first)));
    const std::string actual_rgba = hex(sha256(first.to_rgba8()));
    if (actual_float != fixture.floats) throw std::runtime_error(std::string(fixture.key) + "/" + std::string(fixture.variant) + " float oracle hash: " + actual_float);
    if (actual_rgba != fixture.rgba) throw std::runtime_error(std::string(fixture.key) + "/" + std::string(fixture.variant) + " rgba oracle hash: " + actual_rgba);
    require_repeat(first, second);
  }
}

TEST(typed_control_flow_slice_each_signature_rejects_wrong_binding_type) {
  struct Fixture { std::string_view key; std::string_view uniform; noisemaker::glsl::UniformValue wrong; };
  const std::array<Fixture, 13> fixtures{{
      {"filter/channel:channel", "channel", 2.0f},
      {"filter/chromaticAberration:chromaticAberration", "aberrationAmt", std::int32_t(73)},
      {"filter/glowingEdge:glowingEdge", "sobelMetric", std::int32_t(3)},
      {"filter/highPass:hpCombine", "mono", std::int32_t(0)},
      {"filter/pixels:pixels", "size", std::int32_t(4)},
      {"filter/plasticWrap:pwSpec", "lightDirection", noisemaker::glsl::Vec2(0.31f, 0.79f)},
      {"filter/seamless:seamless", "curve", 1.0f},
      {"filter/sine:sine", "colorMode", std::int32_t(1)},
      {"filter/vignette:vignette", "alpha", false},
      {"mixer/alphaMask:alphaMask", "maskMode", std::int32_t(0)},
      {"mixer/applyMode:applyMode", "mode", 1.0f},
      {"mixer/thresholdMix:thresholdMix", "quantize", 3.0f},
      {"synth/polygon:shape", "sides", 3.0f},
  }};
  const noisemaker::Surface input = source(5U, 3U, 1U);
  const noisemaker::Surface blur = source(3U, 5U, 11U);
  const noisemaker::Surface tex = source(7U, 2U, 23U);
  for (const Fixture& fixture : fixtures) {
    noisemaker::glsl::Bindings bindings;
    populate_task10_bindings(bindings, fixture.key, input, blur, tex);
    bindings.set_uniform(std::string(fixture.uniform), fixture.wrong);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(fixture.key, bindings), noisemaker::glsl::KernelBindingError);
  }
}

TEST(typed_control_flow_slice_secondary_samplers_are_required) {
  struct Fixture { std::string_view key; std::string_view sampler; };
  constexpr std::array<Fixture, 5> fixtures{{
      {"filter/highPass:hpCombine", "blurTex"}, {"filter/plasticWrap:pwSpec", "blurTex"},
      {"mixer/alphaMask:alphaMask", "tex"}, {"mixer/applyMode:applyMode", "tex"},
      {"mixer/thresholdMix:thresholdMix", "tex"},
  }};
  const noisemaker::Surface input = source(5U, 3U, 1U);
  const noisemaker::Surface blur = source(3U, 5U, 11U);
  const noisemaker::Surface tex = source(7U, 2U, 23U);
  for (const Fixture& fixture : fixtures) {
    noisemaker::glsl::Bindings bindings;
    populate_task10_bindings(bindings, fixture.key, input, blur, tex, 0.12f, fixture.sampler);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(fixture.key, bindings), noisemaker::glsl::KernelBindingError);
  }
}

struct Task11Case {
  std::string_view key;
  std::string_view variant;
  std::string_view float_hash;
  std::string_view rgba_hash;
  std::array<std::uint32_t, 12> probes;
};

[[nodiscard]] noisemaker::Surface task11_grayscale() {
  std::vector<std::uint8_t> bytes(4U * 6U * 4U);
  for (std::size_t y = 0; y < 6U; ++y) for (std::size_t x = 0; x < 4U; ++x) {
    const std::size_t index = (y * 4U + x) * 4U;
    const auto value = static_cast<std::uint8_t>(20U + 17U * x + 11U * y);
    bytes[index] = value; bytes[index + 1U] = value; bytes[index + 2U] = value;
    bytes[index + 3U] = static_cast<std::uint8_t>(200U - 9U * x - 7U * y);
  }
  return noisemaker::Surface::from_rgba8(4U, 6U, bytes);
}

[[nodiscard]] noisemaker::Surface task11_transparent() {
  std::vector<std::uint8_t> bytes(17U * 13U * 4U);
  for (std::size_t index = 0; index < bytes.size(); index += 4U) {
    bytes[index] = 211U; bytes[index + 1U] = 37U; bytes[index + 2U] = 143U;
    bytes[index + 3U] = 0U;
  }
  return noisemaker::Surface::from_rgba8(17U, 13U, bytes);
}

[[nodiscard]] noisemaker::Surface task11_edges() {
  std::vector<std::uint8_t> bytes(4U * 6U * 4U);
  for (std::size_t y = 0; y < 6U; ++y) for (std::size_t x = 0; x < 4U; ++x) {
    const std::size_t index = (y * 4U + x) * 4U;
    bytes[index] = static_cast<std::uint8_t>((31U * x + 17U * y + 13U * 37U) % 256U);
    bytes[index + 1U] = static_cast<std::uint8_t>((11U * x + 47U * y + 29U * 37U) % 256U);
    bytes[index + 2U] = static_cast<std::uint8_t>((67U * x + 19U * y + 7U * 37U) % 256U);
    bytes[index + 3U] = static_cast<std::uint8_t>((255U - 23U * x - 37U * y - 5U * 37U) & 255U);
  }
  bytes[(5U * 4U + 3U) * 4U] = 255U;
  return noisemaker::Surface::from_rgba8(4U, 6U, bytes);
}

[[nodiscard]] noisemaker::Surface task11_tint_hybrid() {
  constexpr std::array<std::uint8_t, 60> bytes{
      0,0,0,255, 64,64,64,244, 230,30,80,233, 30,220,80,222, 40,70,230,211,
      96,96,96,200, 240,80,20,189, 20,240,100,178, 60,100,240,167, 200,30,160,156,
      17,17,17,145, 180,40,90,134, 50,180,210,123, 210,160,30,112, 90,30,180,101};
  return noisemaker::Surface::from_rgba8(5U, 3U, bytes);
}

[[nodiscard]] int task11_suffix(std::string_view value, std::string_view prefix) {
  int result = 0;
  for (char digit : value.substr(prefix.size())) result = result * 10 + (digit - '0');
  return result;
}

void populate_task11_bindings(noisemaker::glsl::Bindings& bindings, const Task11Case& fixture,
                              const noisemaker::Surface& input, const noisemaker::Surface& tex,
                              const noisemaker::Surface& edges, const noisemaker::Surface& grayscale,
                              const noisemaker::Surface& tint_hybrid,
                              const noisemaker::Surface& media,
                              const noisemaker::Surface& transparent, std::string_view skip = {}) {
  const auto uniform = [&](std::string_view name, noisemaker::glsl::UniformValue value) {
    if (name != skip) bindings.set_uniform(std::string(name), std::move(value));
  };
  const auto texture = [&](std::string_view name, const noisemaker::Surface& surface) {
    if (name != skip) bindings.set_texture(std::string(name), surface);
  };
  uniform("resolution", noisemaker::glsl::Vec2(7.0f, 5.0f));
  uniform("tileOffset", noisemaker::glsl::Vec2(3.0f, 2.0f));
  uniform("fullResolution", noisemaker::glsl::Vec2(13.0f, 11.0f));
  uniform("time", 0.125f);

  if (fixture.key == "classicNoisedeck/splat:splat") {
    texture("inputTex", input); uniform("seed", 7.0f); uniform("enabled", true);
    uniform("useSpecks", true); uniform("splatSource", std::int32_t{0}); uniform("scale", 3.7f);
    uniform("cutoff", 41.0f); uniform("speed", 2.0f);
    uniform("splatColor", noisemaker::glsl::Vec3(0.81f, 0.22f, 0.63f));
    uniform("mode", std::int32_t{2}); uniform("speckScale", 2.6f); uniform("speckCutoff", 38.0f);
    uniform("speckSpeed", 3.0f); uniform("speckSeed", 5.0f);
    uniform("speckColor", noisemaker::glsl::Vec3(0.17f, 0.74f, 0.39f));
    uniform("speckMode", std::int32_t{3});
    if (fixture.variant == "disabledNoSpecks") { uniform("enabled", false); uniform("useSpecks", false); }
    if (fixture.variant.starts_with("splatMode")) {
      uniform("useSpecks", false); uniform("mode", std::int32_t{task11_suffix(fixture.variant, "splatMode")});
    }
    if (fixture.variant.starts_with("speckMode")) {
      uniform("enabled", false); uniform("speckMode", std::int32_t{task11_suffix(fixture.variant, "speckMode")});
    }
  } else if (fixture.key == "filter/corrupt:corrupt") {
    texture("inputTex", input); uniform("seed", 7.0f); uniform("intensity", 0.0f); uniform("sort", 0.0f);
    uniform("shift", 0.0f); uniform("bits", 0.0f); uniform("channelShift", 0.0f); uniform("speed", 3.0f);
    uniform("melt", 0.0f); uniform("scatter", 0.0f); uniform("bandHeight", 3.0f); uniform("renderScale", 1.0f);
    if (fixture.variant != "clean") {
      if (fixture.variant == "mixedLowBits") {
        uniform("intensity", 50.0f); uniform("bits", 20.0f);
      } else {
      uniform("intensity", 100.0f); uniform("sort", 100.0f); uniform("shift", 100.0f);
      uniform("bits", fixture.variant == "bitsMid" ? 45.0f : 100.0f);
      uniform("channelShift", 100.0f);
      if (fixture.variant == "full") { uniform("melt", 100.0f); uniform("scatter", 100.0f); }
      }
    }
  } else if (fixture.key == "filter/flipMirror:flipMirror") {
    texture("inputTex", input); uniform("flipMode", std::int32_t{task11_suffix(fixture.variant, "mode")});
  } else if (fixture.key == "filter/outline:outlineBlend") {
    texture("inputTex", input); texture("edgesTexture", edges);
    uniform("invert", fixture.variant == "whiteOutline" ? 1.0f : 0.0f);
  } else if (fixture.key == "filter/outline:outlineValueMap") {
    texture("inputTex", fixture.variant == "grayscale" ? grayscale : input);
  } else if (fixture.key == "filter/spatter:spatter") {
    texture("inputTex", input); uniform("color", noisemaker::glsl::Vec3(0.83f, 0.19f, 0.47f));
    uniform("density", 1.5f); uniform("alpha", 0.83f); uniform("seed", std::int32_t{11});
    if (fixture.variant == "fallbackResolution") uniform("fullResolution", noisemaker::glsl::Vec2(0.0f));
  } else if (fixture.key == "filter/tint:colorize") {
    texture("inputTex", fixture.variant == "mode2" ? tint_hybrid : input);
    uniform("color", noisemaker::glsl::Vec3(0.16f, 0.69f, 0.83f));
    uniform("alpha", 0.62f); uniform("mode", static_cast<float>(task11_suffix(fixture.variant, "mode")));
  } else if (fixture.key == "mixer/blendMode:blendMode") {
    texture("inputTex", input); texture("tex", tex);
    const int mode = task11_suffix(fixture.variant, "mode");
    uniform("mode", std::int32_t{mode}); uniform("mixAmt", mode == 14 ? 47.0f : -37.0f);
  } else if (fixture.key == "mixer/centerMask:centerMask") {
    texture("inputTex", input); texture("tex", tex); uniform("shape", std::int32_t{0});
    uniform("power", -80.0f); uniform("hardness", 0.0f); uniform("blendMode", std::int32_t{14});
    if (fixture.variant == "shape-1") uniform("shape", std::int32_t{-1});
    else if (fixture.variant.starts_with("shape")) uniform("shape", std::int32_t{task11_suffix(fixture.variant, "shape")});
    else { uniform("shape", std::int32_t{2}); uniform("blendMode", std::int32_t{task11_suffix(fixture.variant, "blend")}); }
  } else if (fixture.key == "synth/media:mediaInput") {
    texture("imageTex", fixture.variant == "transparent" ? transparent : media);
    uniform("imageSize", noisemaker::glsl::Vec2(17.0f, 13.0f)); uniform("position", std::int32_t{0});
    uniform("rotation", 0.0f); uniform("scaleAmt", 100.0f); uniform("offsetX", 0.0f);
    uniform("offsetY", 0.0f); uniform("tiling", std::int32_t{0}); uniform("flip", std::int32_t{0});
    uniform("bgColor", noisemaker::glsl::Vec3(0.12f, 0.34f, 0.56f)); uniform("bgAlpha", 0.71f);
    if (fixture.variant.starts_with("position")) uniform("position", std::int32_t{task11_suffix(fixture.variant, "position")});
    else if (fixture.variant.starts_with("tiling")) {
      uniform("position", std::int32_t{4}); uniform("scaleAmt", 40.0f);
      uniform("tiling", std::int32_t{task11_suffix(fixture.variant, "tiling")});
    } else if (fixture.variant.starts_with("flip")) {
      uniform("position", std::int32_t{4});
      uniform("flip", std::int32_t{task11_suffix(fixture.variant, "flip")});
    } else if (fixture.variant == "outOfBounds") {
      uniform("scaleAmt", 15.0f); uniform("offsetX", 100.0f); uniform("offsetY", 100.0f);
      uniform("bgColor", noisemaker::glsl::Vec3(0.03f, 0.57f, 0.91f)); uniform("bgAlpha", 0.63f);
    } else {
      uniform("position", std::int32_t{4});
      if (fixture.variant == "scaleZeroGuard") uniform("scaleAmt", std::numeric_limits<float>::infinity());
    }
  }
}

[[nodiscard]] noisemaker::Surface render_task11(const Task11Case& fixture,
                                                 std::string_view skip = {}) {
  const noisemaker::Surface input = source(5U, 3U, 1U);
  const noisemaker::Surface tex = source(7U, 2U, 23U);
  const noisemaker::Surface edges = task11_edges();
  const noisemaker::Surface grayscale = task11_grayscale();
  const noisemaker::Surface tint_hybrid = task11_tint_hybrid();
  const noisemaker::Surface media = source(17U, 13U, 59U);
  const noisemaker::Surface transparent = task11_transparent();
  noisemaker::glsl::Bindings bindings;
  populate_task11_bindings(bindings, fixture, input, tex, edges, grayscale, tint_hybrid,
                           media, transparent, skip);
  return noisemaker::run_pass(noisemaker::generated::bind(fixture.key, bindings),
                              7U, 5U, 0.125f, 7.0f);
}

TEST(typed_task11_all_ninety_four_external_oracles_are_exact_and_repeatable) {
  constexpr std::array<Task11Case, 94> fixtures{{
    {"classicNoisedeck/splat:splat", "primary", "77fb7861a5efe9cca6f4a87c80107bfcab4b13ce5268d8eabda4a844d181024d", "471ba80050899bdbd3df48d182b63835d52498757538de99f466520369d11829", {0x3f800000U,0x3f800000U,0x3f800000U,0x3f7afafbU,0x00000000U,0x00000000U,0x00000000U,0x3f35b5b6U,0x00000000U,0x00000000U,0x00000000U,0x3ea8a8a9U}},
    {"classicNoisedeck/splat:splat", "disabledNoSpecks", "bde61fe2cc345cd2979280e465847046eec54926ac7a5569ab36b7c9d4fac749", "5f07b0549bb0b7480f9f9709f6e2d863b9e1f93ebe4a6147459092c931e38718", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
    {"classicNoisedeck/splat:splat", "splatMode0", "37feba56785adb2568f60167b7579a27110cbcc0d610171eeb4344eb37d74815", "bd183f92cc92ef33c45e7f2409a0399c555f28567fcebb6b34ed69317cccb497", {0x3f4f5c29U,0x3e6147aeU,0x3f2147aeU,0x3f7afafbU,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
    {"classicNoisedeck/splat:splat", "splatMode1", "73c09a29cfcb0de5dacd0afb9f2cbcda72af8cdabd2c92b84873af0f68b1d5b6", "ca3a227c5563a19fb603f9d4436009351938656f07286d9ef463b42e012560a0", {0x3e30b0b1U,0x3e20a0a1U,0x3e949495U,0x3f63e3e4U,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
    {"classicNoisedeck/splat:splat", "splatMode3", "5c76f624ece1f6d9b1a09fb0d94be63dd961cfd99ae7211e9cd8d808cbb164d3", "bf9cedbbfd750d46348f0c51bf368c9a79b191cb8e684cc6c317ec7f30e660be", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0xbed4d4d5U,0xbe78f8f9U,0xbf50d0d1U,0x3f35b5b6U,0xbf2babacU,0xbf27a7a8U,0xbe64e4e5U,0x3ea8a8a9U}},
    {"classicNoisedeck/splat:splat", "speckMode0", "f2e0515020598be5382aa29212fcbdc35f7f597469d8fa5a63032fc9300a4e97", "68f35d0e3e68d05d8d6da4e8786c9ea83dff024b3b9cc0f5327419a7cb474532", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
    {"classicNoisedeck/splat:splat", "speckMode1", "58d0e5f43b86d2c809b5b760fe708fd97e83de45bed964aee212dc0cfd858c23", "9c957b4db8b693f2e72fb23a4dd0786ca9baefd63e993a7cdbd77bab0984b33e", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
    {"classicNoisedeck/splat:splat", "speckMode2", "c2273fa0b5e338423b0e2ad732f9976c5f07467bc3bc333ad68f2ed88d03bf41", "5c1ac7c999fa5603fbd7715bbc6844d2252f300c7a1c7a4f9385b6def25fd826", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
    {"filter/corrupt:corrupt", "clean", "5385521f89dc3bd327884c1acc0427df1f73927f3c59fda35e36f315aabee201", "1e13cb21ecc9f33657c512001a706582b326ff762ea82cb71f96c97a119b3e28", {0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f800000U,0x3eb8b8b9U,0x3ec4c4c5U,0x3f20a0a1U,0x3f800000U,0x3f0c8c8dU,0x3f1c9c9dU,0x3f76f6f7U,0x3f800000U}},
    {"filter/corrupt:corrupt", "full", "dadcec28de46470b6abff92ed36b480e7dc9c776f4ff07847086b35c2ac9a3fb", "f9dac4c788d1e069268eb38aec9328925617aff12d1dc67c8755d37d276cfb66", {0x3f7ffffeU,0x3f7fffffU,0x3f7fffffU,0x3f800000U,0x3f7ffff8U,0x3f7ffff8U,0x3f7ffff8U,0x3f800000U,0x3f7ffff8U,0x3f7ffff8U,0x00000000U,0x3f800000U}},
    {"filter/corrupt:corrupt", "bitsMid", "4dc8b2479d94d4720439b3c8fa73ca9cd65ae54cd7b3157a28b65c99001263f3", "d90817e6767ecd683f59d04178dd89c834e2599d2fd69d6cca81f1c5a36d8617", {0x3e75480dU,0x3eaf3377U,0x3ebbb724U,0x3f800000U,0x3eb93668U,0x3f1d22f6U,0x3f202f0eU,0x3f800000U,0x3f0c292cU,0x3f1c6df3U,0x3f76886bU,0x3f800000U}},
    {"filter/corrupt:corrupt", "mixedLowBits", "4d167d6198b8566191bae0788be0c34b0fd4c891fee4a8b4b770d81a2bf8f372", "1e13cb21ecc9f33657c512001a706582b326ff762ea82cb71f96c97a119b3e28", {0x3e75c0dbU,0x3eaef16cU,0x3ebb7061U,0x3f800000U,0x3eb95b39U,0x3ec3c505U,0x3f205d4eU,0x3f800000U,0x3f0c8c8dU,0x3f1c9c9dU,0x3f76f6f7U,0x3f800000U}},
    {"filter/flipMirror:flipMirror", "mode0", "328f5db410ea63e4db4daccdfc9512006a8734c7467071ad31a87e3bf9e805fa", "b1f29e6195516c6556e95c5cc3e7b82498cd484458e693ee30fc255685973077", {0x3df0f0f1U,0x3e989899U,0x3dd0d0d1U,0x3f55d5d6U,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3e9c9c9dU,0x3f068687U,0x3ee0e0e1U,0x3f19999aU}},
    {"filter/flipMirror:flipMirror", "mode1", "61192595d3b576b6066b1a780b6f79b084b98aa360a9fee2a3525590407f5d5e", "57665f37c80fb363105581bd9def3d3a0db19a17e3e38dca53ba3db3c04d305b", {0x3e30b0b1U,0x3e20a0a1U,0x3e949495U,0x3f63e3e4U,0x3ef6f6f7U,0x3edadadbU,0x3f63e3e4U,0x3f109091U,0x3e3cbcbdU,0x3ef6f6f7U,0x3e34b4b5U,0x3f30b0b1U}},
    {"filter/flipMirror:flipMirror", "mode2", "ca29ed8e6fe6b70cd1f0c34005ea2a90d0870e600ab0ad553b030409cb816b18", "2811ae9a5195440ec0e9dfa6b3eb386ce8f164322c82ba4252b1aac5d42cd37d", {0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3e3cbcbdU,0x3ef6f6f7U,0x3e34b4b5U,0x3f30b0b1U}},
    {"filter/flipMirror:flipMirror", "mode3", "df7494bc0f9867902e62d5236cd2d329bcc561b7661c94cc0ae6c14b7ad2c9d8", "129a0e3849b93a62531a7b7ebfd63f09a001f81f1e9e4f98a1a8c4f89b9c27cd", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3ef6f6f7U,0x3edadadbU,0x3f63e3e4U,0x3f109091U,0x3e9c9c9dU,0x3f068687U,0x3ee0e0e1U,0x3f19999aU}},
    {"filter/flipMirror:flipMirror", "mode11", "1dd4a1e147bb3156ba5ce8640bb197ff8db4835def2968b29ea8ef3b596fc706", "16f24bcf6c1f3873ece584e5ab789dbc27c8348ea4acce76fd564c3a908e159c", {0x3df0f0f1U,0x3e989899U,0x3dd0d0d1U,0x3f55d5d6U,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3e3cbcbdU,0x3ef6f6f7U,0x3e34b4b5U,0x3f30b0b1U}},
    {"filter/flipMirror:flipMirror", "mode12", "0bfcbace47d4cbf80b37a9771171f91c2c9a0f97eb7c59ad29496f13fa6a1951", "6eb8d177280f0beaaab6bd1e90d16135c27b14d86b35a4ed15f17d8260b7b066", {0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3e9c9c9dU,0x3f068687U,0x3ee0e0e1U,0x3f19999aU}},
    {"filter/flipMirror:flipMirror", "mode13", "78bb5263b566554cd1b657a78cbf7801056e781b5897595f125574bec39c66cc", "f384f18a85804e3898b7f575e41db5ef5a066d13c6fdc960760854e89db2b865", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3e9c9c9dU,0x3f068687U,0x3ee0e0e1U,0x3f19999aU}},
    {"filter/flipMirror:flipMirror", "mode14", "94530fe46f0be26947f3a6a65f886ad256abe2f88ced2e7740249f597f7943eb", "701ff504f64f54e5915628896069f414aa71bd66731659fe34cb16cf0d2ecb47", {0x3df0f0f1U,0x3e989899U,0x3dd0d0d1U,0x3f55d5d6U,0x3ef6f6f7U,0x3edadadbU,0x3f63e3e4U,0x3f109091U,0x3e9c9c9dU,0x3f068687U,0x3ee0e0e1U,0x3f19999aU}},
    {"filter/flipMirror:flipMirror", "mode15", "805d52e217cf9be1d6cf40f0bf19b967586ce4fe0c6b8561497edf750b61f44d", "bed103fbaa2856ca2635775fafd33f8f851ccb18e2b61fd849fedf96333d5822", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3e3cbcbdU,0x3ef6f6f7U,0x3e34b4b5U,0x3f30b0b1U}},
    {"filter/flipMirror:flipMirror", "mode16", "e51fedd8e508906c9b4b58af638d3509b9f03605ddd8ad8187399b4b9bee6cf0", "8cc2ee9f2991443b5afc9e88b4f468495c4fbdff4d7333416b5e9b189819d7c6", {0x3df0f0f1U,0x3e989899U,0x3dd0d0d1U,0x3f55d5d6U,0x3ef6f6f7U,0x3edadadbU,0x3f63e3e4U,0x3f109091U,0x3e3cbcbdU,0x3ef6f6f7U,0x3e34b4b5U,0x3f30b0b1U}},
    {"filter/flipMirror:flipMirror", "mode17", "2fd95f9588d3fca68235ab90eff6767aa40337de9f16bf74db9930ec5a0e8524", "13e1c98242807c2a5187f2627dfaaf0ee6b7fe07a88a776557259382b8f312ab", {0x3e30b0b1U,0x3e20a0a1U,0x3e949495U,0x3f63e3e4U,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3e9c9c9dU,0x3f068687U,0x3ee0e0e1U,0x3f19999aU}},
    {"filter/flipMirror:flipMirror", "mode18", "add5bc60f389d32a8f60298df83293070708d8bef46b37465a579bab9d3f1915", "c3658b0c1350d0262eab797816b720931da7bf414ff84152865c965daec8fa37", {0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU,0x3ef6f6f7U,0x3edadadbU,0x3f63e3e4U,0x3f109091U,0x3e9c9c9dU,0x3f068687U,0x3ee0e0e1U,0x3f19999aU}},
    {"filter/outline:outlineBlend", "blackOutline", "a2aab4900a449027ed69993a88d7c968b929ba1d0a1c8d06a2eaf7232eb19317", "7d22be0b86afb76aca616b4edad9e24f726a8a8cc19ab39853297d3cb0a82804", {0x3bc4884bU,0x3c5b358fU,0x3b53a679U,0x3f7afafbU,0x3eacc4ddU,0x3e4a1b6dU,0x3f29825bU,0x3f35b5b6U,0x3ea84df3U,0x3ea45e18U,0x3de067efU,0x3ea8a8a9U}},
    {"filter/outline:outlineBlend", "whiteOutline", "6db4db090e13c80eaa2c8b5988712ed2d20e4d0afb506bbe26c7e4268da8d937", "239586e2a1ae6ba3046bfe13b4ba8c08c363c14468eff650e302da2ab33d9456", {0x3f636af3U,0x3f654eb8U,0x3f62b588U,0x3f7afafbU,0x3f06929fU,0x3ec56e17U,0x3f59b28cU,0x3f35b5b6U,0x3f56a97dU,0x3f54b18fU,0x3f1e8f81U,0x3ea8a8a9U}},
    {"filter/outline:outlineValueMap", "colorOklab", "856c984b4d37fdded7e9e7cd117a64bbf218658cfb51dc572f92d7c9b0332306", "349d19d5f9238b64607c265a97cee2e57558f49b2254a613efb80f334e4fef88", {0x3e56cac9U,0x3e56cac9U,0x3e56cac9U,0x3f7afafbU,0x3f00d280U,0x3f00d280U,0x3f00d280U,0x3f35b5b6U,0x3f36081fU,0x3f36081fU,0x3f36081fU,0x3ea8a8a9U}},
    {"filter/outline:outlineValueMap", "grayscale", "17137e5da9dba3919e6fc1a42221ddfd166388e8059fc671b73e04ea354041f2", "c6ded0a7986409c32fd2cea123458989295584a3857f5e856a6ccc0870d40eb1", {0x3df8f8f9U,0x3df8f8f9U,0x3df8f8f9U,0x3f41c1c2U,0x3ed0d0d1U,0x3ed0d0d1U,0x3ed0d0d1U,0x3f189899U,0x3efcfcfdU,0x3efcfcfdU,0x3efcfcfdU,0x3f0a8a8bU}},
    {"filter/spatter:spatter", "primary", "f106b4d60c9e1b0ce579b25adcadb918f220d94bf62ea73a615ccd06dc1c3143", "2270dc9fe831c33940eb09df5ac36a0d97d8cd9793449e21924298df6b599cd4", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3f1372a8U,0x3e5bc316U,0x3e00341fU,0x3ea8a8a9U}},
    {"filter/spatter:spatter", "fallbackResolution", "50439a305aa93b986840fe29f7732b31d4694adfc7addeaf64167d6cc4008f6c", "4314515902999d5f9ae734fc41592f1e76cd9d909e17f8b06efaa072e7c7187c", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3eb6cd06U,0x3da32d37U,0x3ee9ea53U,0x3f35b5b6U,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
    {"filter/tint:colorize", "mode0", "d943408565025ec93b59fed744cbc7407efe108776b650af43eb5f711093cdf0", "ea6d7456750550b923b42ac58699b43eb16ddf37f80e7e83ffff22532c211120", {0x3df2d62aU,0x3ef128f8U,0x3f066875U,0x3f7afafbU,0x3e83aa94U,0x3f052b50U,0x3f53166aU,0x3f35b5b6U,0x3eb54293U,0x3f2d39c5U,0x3f197b88U,0x3ea8a8a9U}},
    {"filter/tint:colorize", "mode1", "c449315bf1455a8d6f3e656564ccdd3076f2fd5a873307ca648cd38d20af73d3", "28957404e858969a8c81309e757c3db69c899c6b8d4693c18d79b924467b78af", {0x3cc82103U,0x3dbc2501U,0x3cc92d1eU,0x3f7afafbU,0x3e4bfa43U,0x3e491ebaU,0x3f3ace78U,0x3f35b5b6U,0x3ea48773U,0x3f076e80U,0x3e4cc4c8U,0x3ea8a8a9U}},
    {"filter/tint:colorize", "mode2", "ece4139d0a0a3b0e2f816c0340cb5edd7f639b9b5cde0113ce0393dfe152df8c", "9e00b953b553b6d83198b6b479dd0ee5e4e18c18ee3230404070cf10d818eab9", {0x00000000U,0x00000000U,0x00000000U,0x3f800000U,0x3df1eae3U,0x3f442d43U,0x3f277441U,0x3f5ededfU,0x3f0530ddU,0x3ef174ceU,0x3f34b4b5U,0x3ecacacbU}},
    {"mixer/blendMode:blendMode", "mode0", "5d67858d1b1300ee8c641358f85ea0800536206c19de4f3a109117da19fdb23c", "b952c8b2156aca097681a3f189985a521263a432841ea5b532b8dbe23160fab2", {0x3ddfdba5U,0x3ea5df19U,0x3e7bbb49U,0x3f7bd937U,0x3f025d81U,0x3ebeb323U,0x3f5917a6U,0x3f3c39baU,0x3f59b6e7U,0x3f2e3b8cU,0x3ebf2fd4U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode1", "eb9158e28951ccfa4703c72ce57280b889cea2407fc1a3d555f58f2badf0c537", "b21e0c6854707d9d7073cb7188006f998ba04ba7ac05670a77b6ba766f9e30b0", {0x3d08970cU,0x3d9859b4U,0x3c9318d1U,0x3f7bd937U,0x3eaf7f8dU,0x3e4d4cc2U,0x3f452e76U,0x3f3c39baU,0x3f29fc6eU,0x3e983b0cU,0x3dcfd5fbU,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode2", "e5eb5f978953a3bef31e0758369fea8480d07bab4fa45bb5eab6fe61979fac2b", "0662ddff5b427f2cf1a4c1f14eadb42389b2a7be3d06d4df1784c7f0f51ab795", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7bd937U,0x3ed4d4d5U,0x3e78f8f9U,0x3f3eda81U,0x3f3c39baU,0x3f2babacU,0x3ea562d4U,0x3e64e4e5U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode3", "b6081b8afc898213e2133a91f839f7a79b153bbd1957964c1496b5f908e4bb36", "841fe893c0fd61fa0e2b257cb098a0c2e410e8ecf9910621491eb82273c291a5", {0x3d97a1e0U,0x3e7b2efeU,0x3e684945U,0x3f7bd937U,0x3eba1071U,0x3e9306ecU,0x3f3e262dU,0x3f3c39baU,0x3eee191bU,0x3f2113c4U,0x3e046bd9U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode4", "3733abfe0f847632dd8da9f41fd6ebef98b7aee1e3405cb87053abda6b769dbe", "7825df965f3b4ef0f5a21d8cfb0667b797c670a7693404960504db36ddcdfb7a", {0x3d5f771aU,0x3e32e371U,0x3d330ccaU,0x3f7bd937U,0x3eff7f71U,0x3eb9c22aU,0x3f5917a6U,0x3f3c39baU,0x3f59b6e7U,0x3f2c2ce6U,0x3e8a1759U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode5", "a2cb5a0fa19cc0531ca2a75f28404f7b9bed85ff893c930636f24cdbc9e22506", "19158647faa4c4c03267a821a9c9c803591859e7948141400e2ded5d2443d364", {0x3dd3adc4U,0x3e8d6342U,0x3e6f744dU,0x3f7bd937U,0x3edce892U,0x3e9e8077U,0x3f4507b7U,0x3f3c39baU,0x3efb54b2U,0x3f259dfbU,0x3e9ce130U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode6", "4bdc0f6f4cb81ce45bffe2a7f85f4212090c62592e8478caaadf84e8e9fec033", "4385135c13f9824deeaa2a7cec4f019a02849db7df042320a15b10b360d02e31", {0x3d20f2d0U,0x3e3828e0U,0x3ded3affU,0x3f7bd937U,0x3ed85474U,0x3e9cbda7U,0x3f4aa39bU,0x3f3c39baU,0x3f5676dcU,0x3ea9762eU,0x3e2c8846U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode7", "cb79424d50498166da27202ddb6caa73a3280f25620c1e9caa5f6609735e9edf", "30b600e80768e1188ad59c115f7679d8b4f0e7b00e7b5dfb613a48758b33d68f", {0x3dbbbec3U,0x3e91bb4cU,0x3e720247U,0x3f7bd937U,0x3edf65b9U,0x3ea8dd07U,0x3f50d0d1U,0x3f3c39baU,0x3f54c7fbU,0x3f27a7a8U,0x3e80b2e0U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode8", "7faa43d7d4f60bc40b5bf80b9a0b5928e00c38ad48b12961bc54c2320612631f", "36b3da46e2b1988ccb0a2c510335ba042ce28616c46ebc2e6e1595e751d4f857", {0x3d921396U,0x3e4bf586U,0x3e070f31U,0x3f7bd937U,0x3eda1d47U,0x3e92acc2U,0x3f47d5a9U,0x3f3c39baU,0x3f4039d4U,0x3efa5912U,0x3e732553U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode9", "7d6b4a78f0e82da30a330dcd88cd8904c4e3fb30481ef9753e6397d0ea611f76", "8f6f04de7b7cbdc578b6d2f48c7ab3f6772bfbe134d006abe530de4b286a1b73", {0x3d14c4eeU,0x3dc95161U,0x3cc434bfU,0x3f7bd937U,0x3ec368c5U,0x3e6d7f6dU,0x3f3b69bcU,0x3f3c39baU,0x3f285cc7U,0x3ea0d89dU,0x3e0a39a2U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode10", "c356e1ebb6e5f0963f181e2651da9e2d3cbb8d1009a05139065ff8ff121a41fd", "ff1934c1b22ccc5eb117c862c7ea27ad5028121ec3b7cd9bff24fb30c2ee6a56", {0x3ddfdba5U,0x3ea5df19U,0x3e7bbb49U,0x3f7bd937U,0x3f025d81U,0x3ebeb323U,0x3f4eb3d6U,0x3f3c39baU,0x3f00ea63U,0x3f2e3b8cU,0x3ebf2fd4U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode11", "31e7d51b403e63d5f3a4a81144fca30dd6d0468941b9698b6267ce4897a65fb8", "2f314d43020e020e4723aafd0b8b5e18c2fec5897883301c768c8dfeddcceb81", {0x3d20f2d0U,0x3dfa490dU,0x3cf550acU,0x3f7bd937U,0x3ed751fcU,0x3e86d90cU,0x3f4f6b86U,0x3f3c39baU,0x3f5676dcU,0x3ef7eab2U,0x3e2c8846U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode12", "339fe5e2283dd5cf1d00be4b86d76af2b2ebf1f9232d889f9646f1da210b7217", "8364f89fe958a62a8d9bf69149eaf0fe76b737a8a15cc82787fb4ba2a377a7c5", {0x3ead54caU,0x3e7f59b4U,0x3e1eabecU,0x3f7bd937U,0x3efebe3bU,0x3e941568U,0x3f472155U,0x3f3c39baU,0x3f309a97U,0x3f02edf0U,0x3f1ea131U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode13", "376f3956dc379666f04a16542d10e32fbd21c0eb7660e95921514786d1ea5445", "f1d1678ec608592958197f302ff938bdf63b37c2bdc9cc4ab39c5ff67beb7341", {0x3dd9c4b4U,0x3e99a12eU,0x3e7597ccU,0x3f7bd937U,0x3ef0d1c9U,0x3eae99cdU,0x3f544196U,0x3f3c39baU,0x3f5816e1U,0x3f29ecc3U,0x3eae0882U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode14", "81f4a72f8177c7f9dbd5ca8c288b1e0372f1a090a52f832809531a587e7e061b", "07de88905801b6e02f4e0d13c426acc127f50f9390e38d7921fcc741ee177449", {0x3d9378d3U,0x3e82b0bcU,0x3e4681e1U,0x3f7d0186U,0x3eddde1fU,0x3ea68de1U,0x3f427526U,0x3f44e9bfU,0x3f5a8c73U,0x3ea06464U,0x3e555780U,0x3f41aeffU}},
    {"mixer/blendMode:blendMode", "mode15", "102a0276385bc6c1ead16eac4c0051cef0f0cda370db08cafdc81e9783a4c14a", "756247adbd61445b4c914e674005dcb0f401bb65e5975b4b21b1f1f07d764a1d", {0x3d08970cU,0x3d9859b4U,0x3c9318d1U,0x3f7bd937U,0x3eaf7f8dU,0x3e4d4cc2U,0x3f3e262dU,0x3f3c39baU,0x3e9be07cU,0x3f2113c4U,0x3dcfd5fbU,0x3f03320bU}},
    {"mixer/centerMask:centerMask", "shape0", "73b27171063874cb33dd4b58b71a34cb916cdd6103f11bd0a8818eec5cfe1ca8", "fb2f4443eee54ea948b457ce3649677221ec44f45953624cc15fddfba05b9373", {0x3e2a86acU,0x3f1ad27cU,0x3f20b166U,0x3f7afafbU,0x3f088855U,0x3f3cbc9cU,0x3ed4d52cU,0x3f27a7a8U,0x3f771314U,0x3d504000U,0x3e887ee1U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "shape1", "830d2f34232ce8fb7c0b5a8b1ca4a41139a469bb16fb8ff9648b653b6575a9bf", "fee8357930b2f502a39de599779e8c8bfd1ff84c8077850164c723f0fd634076", {0x3e2b6ebaU,0x3f1b2758U,0x3f2116c2U,0x3f7afafbU,0x3f088880U,0x3f3cbcb7U,0x3ed4d4e4U,0x3f27a7a8U,0x3f77138eU,0x3d50836aU,0x3e886d3fU,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "shape2", "53c985d87b0eac145c184c808732caf89a9bc050f10b0f085994e51bb5bad414", "7d623d76815a34177e50522b0e9bd68c715ebea5f1ee6653677ea59400881fb0", {0x3e264ee4U,0x3f1947a2U,0x3f1ed9c3U,0x3f7afafbU,0x3f0887b7U,0x3f3cbc35U,0x3ed4d636U,0x3f27a7a8U,0x3f770a46U,0x3d4b65d5U,0x3e89c3c8U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "shape-1", "53c985d87b0eac145c184c808732caf89a9bc050f10b0f085994e51bb5bad414", "7d623d76815a34177e50522b0e9bd68c715ebea5f1ee6653677ea59400881fb0", {0x3e264ee4U,0x3f1947a2U,0x3f1ed9c3U,0x3f7afafbU,0x3f0887b7U,0x3f3cbc35U,0x3ed4d636U,0x3f27a7a8U,0x3f770a46U,0x3d4b65d5U,0x3e89c3c8U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend0", "dff36bf5a9ecacb429fd9941dcd084304dd299e8b71ee7c892fa5c7392dc047c", "0d371efb1919497b67625ce723aacfda45dd312469e50af051fa2c6330fc62c1", {0x3e2f40a1U,0x3f1d0ba9U,0x3f21fa79U,0x3f7afafbU,0x3f088cccU,0x3f3cbfd8U,0x3ed4e2a3U,0x3f27a7a8U,0x3f776930U,0x3da29c22U,0x3e923360U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend1", "0a85606efc13d31c70c8b2bf34b22da7077ec644bf301fb67913fbc3ae9e8b9b", "9f6bf1b61974bc84ef1bbadaf130656a2c950e25956d5d2e4b2914268cf0801b", {0x3e2425c0U,0x3f13ec70U,0x3f19a650U,0x3f7afafbU,0x3f08823cU,0x3f3cb7c4U,0x3ed4cca3U,0x3f27a7a8U,0x3f76bedbU,0x3d373c00U,0x3e859bc0U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend2", "0e90c5216b68eee493391fab987d326157350800a55de2881316997e2aeca017", "d29144363b8a1ffe0b89e900304dc43d9459cdbafa63f1c4da8d6ec2e07247d1", {0x3e26b9b4U,0x3f155c7dU,0x3f19ff27U,0x3f7afafbU,0x3f08867fU,0x3f3cb892U,0x3ed4d4d5U,0x3f27a7a8U,0x3f733f1bU,0x3d40c0c1U,0x3e8b4293U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend3", "084acf7c48638f618667e0f367ce13c2aabcd627b01744f4481d9d01c710ddba", "7f555ee9dfa1754d4780fdc3dcba531706a07eff85cab1dec4df8001480fa1fc", {0x3e2a18b9U,0x3f1a2b8fU,0x3f2148cbU,0x3f7afafbU,0x3f088446U,0x3f3cb833U,0x3ed4d004U,0x3f27a7a8U,0x3f6e7cbbU,0x3d991761U,0x3e86e5baU,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend4", "d020f2a13faf9048042f2710eb45cc3e426eb96899d17bbf8ba44f503df91cbd", "71b5f35b1782baf78252f8a2ab797167bdc4e598c768213c1a7a0141ef969344", {0x3e2d21f1U,0x3f1c9809U,0x3f21db4fU,0x3f7afafbU,0x3f088c17U,0x3f3cbfd8U,0x3ed4e2a3U,0x3f27a7a8U,0x3f776930U,0x3d52d10dU,0x3e8e8c0eU,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend5", "feefe27e1fc8c5c25b629cfb0e24ed97f9918979550f267b6bea0edb0316293e", "0d9061f0d9467b951487dbadea8b67250ac9d437d98e9c01c9d725f83c16df5f", {0x3e2e620fU,0x3f1b4c3aU,0x3f218a4aU,0x3f7afafbU,0x3f088840U,0x3f3cba96U,0x3ed4d755U,0x3f27a7a8U,0x3f6f15ecU,0x3d9c604dU,0x3e8f190aU,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend6", "087d881674cadf6adf27fe4e896397613700772310d2482f956f98eb168b2c69", "c8357caa22caa438fcec4c5d6a1b8243a2f1cb1c6c15642d245d165b74063761", {0x3e250452U,0x3f15abdfU,0x3f1a167eU,0x3f7afafbU,0x3f0886c8U,0x3f3cbab9U,0x3ed4d85aU,0x3f27a7a8U,0x3f771defU,0x3d7c77d0U,0x3e88b616U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend7", "57bb22d38e903b6c2874e3280fc81c59439b9e44a4a919cdd5764135a6b994f6", "e2876d73c116a87db47d3be34c0aabc19839d9590cda6625d698040fc5cd131f", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f088889U,0x3f3cbcbdU,0x3ed4d9d6U,0x3f27a7a8U,0x3f76f6f7U,0x3d9dd9c2U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend8", "e1439cbf4124b4aa456fe453674e7fe5a27dfd0c6bc741f4412c0da7ed8b7e2a", "9720d7113676d477e495ebbb81aadb880f9e61c22d7cc277fbb339b8ce2560b4", {0x3e26b9b4U,0x3f155c7dU,0x3f19ff27U,0x3f7afafbU,0x3f08867fU,0x3f3cb892U,0x3ed4d9d6U,0x3f27a7a8U,0x3f733f1bU,0x3d9dd9c2U,0x3e8b4293U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend9", "8be8a270cfd54bda59386ec449e1975423e41f04e73cf56f6d72f2c5ef5f738b", "378164bbd61ba9f4b1d4720fd91e97847dcafccb0b110cc3921f6c2a83eee2fb", {0x3e249509U,0x3f14cc28U,0x3f19de67U,0x3f7afafbU,0x3f088482U,0x3f3cb760U,0x3ed4d12cU,0x3f27a7a8U,0x3f72f283U,0x3d3d77d6U,0x3e8728ebU,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend10", "25c4f0878f8e97627bd7c21b2d4ef0c95d2ae7b395d67f4e200de957a040be13", "9f5b3bd4ba66262bb30efa61e9240766ce010cd838ab313dd42efce82b76a547", {0x3e2f40a1U,0x3f1d0ba9U,0x3f21fa79U,0x3f7afafbU,0x3f088cccU,0x3f3cbe68U,0x3ed4e19eU,0x3f27a7a8U,0x3f6f612dU,0x3da29c22U,0x3e923360U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend11", "0bc082f57c71cace17c911e319064e76a167ac1d8b1a372ae3897b23e9ebb5ef", "80527316f793005a4f0b9ab483fdd60a82f3eae5ec6deb1311c53e8a60ca10ef", {0x3e250452U,0x3f17c722U,0x3f1d3a23U,0x3f7afafbU,0x3f088700U,0x3f3cbc05U,0x3ed4d756U,0x3f27a7a8U,0x3f771defU,0x3d43b3acU,0x3e88b616U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend12", "1aeda69548f51d92bd9977a6c15380ee0e6cdd96d6f757531f4bb6d4e2d00b5e", "f8280e6463bfee3f320b3bee1f70778cc999c4d596a3fff991c503c803667297", {0x3e50c40aU,0x3f1a51a2U,0x3f1ea826U,0x3f7afafbU,0x3f088c02U,0x3f3cbbacU,0x3ed4dda2U,0x3f27a7a8U,0x3f73b155U,0x3d834726U,0x3e9d9a68U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend13", "cefabaeffe378c100461868731f6b377e5f86839250633926aac9480ebd0285d", "de9fe75087ade4eb6229b313f14f19f0c1627f0518601ef71106bbfc4d1beca4", {0x3e2ed158U,0x3f1c2bf1U,0x3f21c262U,0x3f7afafbU,0x3f088a86U,0x3f3cbdeeU,0x3ed4dd7eU,0x3f27a7a8U,0x3f774390U,0x3d9f7e37U,0x3e90a635U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend15", "bffcfca7b3058ce9271326024127de295e50c5feb18407832a77fd22dfff7a91", "6776de4da65e05bdf73267c3cea164f5820516df7be227ba8cf5d49c2da7a106", {0x3e2a18b9U,0x3f1a2b8fU,0x3f2148cbU,0x3f7afafbU,0x3f088446U,0x3f3cb833U,0x3ed4cb03U,0x3f27a7a8U,0x3f6e7cbbU,0x3d373c00U,0x3e86e5baU,0x3f5ddddeU}},
    {"synth/media:mediaInput", "position0", "512025f5b5e2b16202acae068c540742c835e2738bfbae6f54fd64a865f90331", "de41efcd1fe37a46ee8a65eb1334935c0bd7be60d06a963efe9b30b9e5c46daf", {0x4022067bU,0x3fe95103U,0x40000000U,0x3e9e9e9fU,0x3d124924U,0x3f7cf3cfU,0x3f461862U,0x3ea8a8a9U,0x3f32564bU,0x3e7d1fa4U,0x4023f47eU,0x3eb2b2b3U}},
    {"synth/media:mediaInput", "position1", "5d54c7e0539377a8a47401951a0f44e2db6d3416c6a689d02dbb691e29feabbf", "fe312349954c70c1eb9f3934dab27944e4379a5aef79d543fbad20b9d5ec6789", {0x3e8f4696U,0x3f460ec0U,0x3f33183bU,0x3f73f3f4U,0x3f0318c6U,0x3f0318c6U,0x3e9ef7beU,0x3f78f8f9U,0x3f3c349eU,0x3e8590b3U,0x3f72d88aU,0x3f7dfdfeU}},
    {"synth/media:mediaInput", "position2", "a5f5785193c889dd233568f3c059ad0ab5b24e371418efbfb549cd39cadef9cc", "1e6a6e569fa19c868bcad1fad139d4c98746040ba63a545368d80caeccafb85f", {0x3fdeffffU,0x3ff2ffffU,0x3ff8ffffU,0x3f008081U,0x3e482e32U,0x3faf286bU,0x3f9622a5U,0x3f058586U,0x3f1dae60U,0x3f6076b9U,0x3ee9bd37U,0x3f0a8a8bU}},
    {"synth/media:mediaInput", "position3", "6682585c9bcee2860fc8a74684d79cffb0592e23d9d55a3cebf39c71eb9c01ea", "1cbc81d8e20096f7535f3c36fdc9ce82642e132c493a1a920a7bfe9f37af142b", {0x3f8ae035U,0x3ea751fcU,0x3f48c8c8U,0x3f19999aU,0x3fb6474aU,0x3fc67b23U,0x3e2efcc2U,0x3f1e9e9fU,0x3e2fe6dfU,0x3f907da5U,0x3f9533d4U,0x3f23a3a4U}},
    {"synth/media:mediaInput", "position4", "d265ac74abeb0174b8089a161abbb64310197a86b934cd4dbd36abaa57c2fd37", "d12699ea4e6b0fd408cffa9df747a63672f28379b54c6ec006571f10bbd55fd7", {0x3f0eb044U,0x3fc53ef4U,0x400a7de7U,0x3e74f4f5U,0x3fb45d17U,0x3f000000U,0x3f1745d1U,0x3e848485U,0x4009039bU,0x404d8568U,0x403615a2U,0x3e8e8e8fU}},
    {"synth/media:mediaInput", "position5", "6cd2cbb26c447feccd43a0e60de0e7901106fb7a7036c4aa0372358ebf429531", "d7bf04bdb038a4fb47b1e17aa68a2c05b4e7e7ba90c334926aa6debebe0eccec", {0x3f6f8656U,0x3f3cd4eaU,0x3f85b3f6U,0x3f4acacbU,0x3f995a48U,0x3ed9a96eU,0x3f11eeb0U,0x3f4fcfd0U,0x3e7656f2U,0x3e026a44U,0x3df1826aU,0x3f54d4d5U}},
    {"synth/media:mediaInput", "position6", "064eedf3dd82d71640df6244fe870690388a2e601454ae2a44a24ffb87718b34", "06265073c8a79fcc51684b1a89a3bc4e2a54c61432dd04cb40db1f2751921455", {0x3f09ae41U,0x3e4e8561U,0x3d4e8561U,0x3eeeeeefU,0x3f7def7cU,0x3fe21084U,0x3fae739dU,0x3ef8f8f9U,0x3df5c28fU,0x3eae147bU,0x3f0f5c29U,0x3f35c28fU}},
    {"synth/media:mediaInput", "position7", "dce268e662dedf47d4f5427bd310dbdc849ece9c071da9e2783d9e238dfbcd0b", "4a37e49739b5512f633ed3925d884bbe658a46e3a1e4bf38c0a84f7f947fb394", {0x40ded098U,0x40212f69U,0x3f2aaaabU,0x3dd8d8d9U,0x40f6ffffU,0x3e5fffffU,0x40b50000U,0x3e008081U,0x3df5c28fU,0x3eae147bU,0x3f0f5c29U,0x3f35c28fU}},
    {"synth/media:mediaInput", "position8", "d3ff133753bc2994ef73106a59788d90623bbbeab767b8d51b295cb615a0762e", "7270fddcdf5ef1c8bd2997dabcb16d7e487806aa7d4bbad2ab38946694793f1f", {0x3f049249U,0x3f3b6db7U,0x3f13cf3dU,0x3f28a8a9U,0x3f580bd7U,0x3eb77dc7U,0x3cbd6911U,0x3f2dadaeU,0x3df5c28fU,0x3eae147bU,0x3f0f5c29U,0x3f35c28fU}},
    {"synth/media:mediaInput", "tiling1", "271e439a5e5442f51af8603ecb70fc9195724b525c985ca7a31e8eacd2d127a2", "a82a2c5753240e23def8bdaee227e34fa1dce9be4326d3e30c57883ad3f77935", {0x3df5c28fU,0x3eae147bU,0x3f0f5c29U,0x3f35c28fU,0x3fc27628U,0x3fa9d89eU,0x40980000U,0x3e50d0d1U,0x40bb13b1U,0x40af96f9U,0x40520d21U,0x3e1c9c9dU}},
    {"synth/media:mediaInput", "tiling2", "37670cbf2ca6c53f0295daa65d7bf0aaa014bd8876974e8a596211661a62ce3e", "1bc50b99cd6e2fce4e7d25b52c3343f525dd3273241148f5b3dd7cf20fc82471", {0x3f8b29adU,0x3f5aca6bU,0x3f83b88fU,0x3f2cacadU,0x3fc27628U,0x3fa9d89eU,0x40980000U,0x3e50d0d1U,0x40bb13b1U,0x40af96f9U,0x40520d21U,0x3e1c9c9dU}},
    {"synth/media:mediaInput", "tiling3", "d53a6ab4a2203129fb92c74b29f808893a7132ebc2f52e8bf25918805e469589", "ca1537f642bce55f89dfb4e8e4ef7b7ca1eaf84e62dac490f30305b7ceb78bc8", {0x3df5c28fU,0x3eae147bU,0x3f0f5c29U,0x3f35c28fU,0x3fc27628U,0x3fa9d89eU,0x40980000U,0x3e50d0d1U,0x40bb13b1U,0x40af96f9U,0x40520d21U,0x3e1c9c9dU}},
    {"synth/media:mediaInput", "flip1", "a2d42c5904c8ed663ba030b9190508bc8b421f0dffea5279edcd2bad2b017a15", "207eb7434f4fe18dba9762dceb0cf4b617c9a763515ac0714c03c56e4dd58986", {0x4009039bU,0x404d8568U,0x403615a2U,0x3e8e8e8fU,0x3fb45d17U,0x3f000000U,0x3f1745d1U,0x3e848485U,0x3f0eb044U,0x3fc53ef4U,0x400a7de7U,0x3e74f4f5U}},
    {"synth/media:mediaInput", "flip2", "dd48034fe9bed59bcd2b260c3448a308ccb06b26da051409a54ce77ec4cfc801", "02bdba6820c9945a06ea0868df598b8d5916d4b3b43faac1417f3af643b9b3b8", {0x3f9d5185U,0x3f64d3aaU,0x3dfbb5a2U,0x3f33b3b4U,0x3fb45d17U,0x3f000000U,0x3f1745d1U,0x3e848485U,0x3f87f633U,0x3f466e3eU,0x3e892fc5U,0x3f51d1d2U}},
    {"synth/media:mediaInput", "flip3", "3c82bb5a87fc0a4dc7e4ef9e99841c3984303fd705ce60b4b1036179b5b0d408", "022cdf98d6efe10a996524bf294e1a7d7b8c87c19358c3feedd6e474d854ac77", {0x3f87f633U,0x3f466e3eU,0x3e892fc5U,0x3f51d1d2U,0x3fb45d17U,0x3f000000U,0x3f1745d1U,0x3e848485U,0x3f9d5185U,0x3f64d3aaU,0x3dfbb5a2U,0x3f33b3b4U}},
    {"synth/media:mediaInput", "flip11", "9f397166eca9f343d59760e2679017e5d716457f5f3c282ed5b15d496e5a3cb7", "278eeed0ebf765e7e0f0efb3aeddb1c8d1e560c0b493912c52b7b0582b3ec29b", {0x3f0eb044U,0x3fc53ef4U,0x400a7de7U,0x3e74f4f5U,0x3fb45d17U,0x3f000000U,0x3f1745d1U,0x3e848485U,0x3f87f633U,0x3f466e3eU,0x3e892fc5U,0x3f51d1d2U}},
    {"synth/media:mediaInput", "flip12", "cdf21fae85ca78a566719b978199bdb1b1738e069cdb75aaa9489e85e2f9ef97", "ab4fad538485f56fab55b0295b5bdc76097c10bd171870820030332cdc068107", {0x3f9d5185U,0x3f64d3aaU,0x3dfbb5a2U,0x3f33b3b4U,0x3fb45d17U,0x3f000000U,0x3f1745d1U,0x3e848485U,0x4009039bU,0x404d8568U,0x403615a2U,0x3e8e8e8fU}},
    {"synth/media:mediaInput", "flip13", "e5f39ee530b2477e427a9b87e23337674fa868bd7c92358cbf6fa956b8785413", "7c478aabebb382e0c000bc8d6dda59e614b4fa00dee577703411266ac2141520", {0x3f0eb044U,0x3fc53ef4U,0x400a7de7U,0x3e74f4f5U,0x3fb45d17U,0x3f000000U,0x3f1745d1U,0x3e848485U,0x3f9d5185U,0x3f64d3aaU,0x3dfbb5a2U,0x3f33b3b4U}},
    {"synth/media:mediaInput", "flip14", "54117880e55288379acb6eb906ae4f8e22a8c40d1a761e74402339bef9fde7a4", "fc4e5022caec541600f37d3c92b3018fce470ceb7d9c4f1d44f9a2b1a907f827", {0x3f87f633U,0x3f466e3eU,0x3e892fc5U,0x3f51d1d2U,0x3fb45d17U,0x3f000000U,0x3f1745d1U,0x3e848485U,0x4009039bU,0x404d8568U,0x403615a2U,0x3e8e8e8fU}},
    {"synth/media:mediaInput", "flip15", "b43299dae1f456731538fe936046efa98100367c5808beaf2224bb46d173969c", "2e2fb1bdb52d7a82ba35dbdc49f1e8a4b04b3eb632580a7e67ba718590cb41bd", {0x3f0eb044U,0x3fc53ef4U,0x400a7de7U,0x3e74f4f5U,0x3fb45d17U,0x3f000000U,0x3f1745d1U,0x3e848485U,0x3f0eb044U,0x3fc53ef4U,0x400a7de7U,0x3e74f4f5U}},
    {"synth/media:mediaInput", "flip16", "af74f97b4c18c12fc2dbb41dcde1812103755cdb504d71fd74364a147dbbfa03", "80d82ee5cef31b4011d6ff3d2e189e5231283a8ebb7cafb4f5a29d6a9b081d31", {0x3f87f633U,0x3f466e3eU,0x3e892fc5U,0x3f51d1d2U,0x3fb45d17U,0x3f000000U,0x3f1745d1U,0x3e848485U,0x3f87f633U,0x3f466e3eU,0x3e892fc5U,0x3f51d1d2U}},
    {"synth/media:mediaInput", "flip17", "b14b206a2bd7f92c99969b70c35a26b30149d05287e3a9bd9ca82be3a0f96585", "c06cc2c5c49ef97174fb2188378fbf6ca04322b10117a3394c93a772905ff3ef", {0x3f9d5185U,0x3f64d3aaU,0x3dfbb5a2U,0x3f33b3b4U,0x3fb45d17U,0x3f000000U,0x3f1745d1U,0x3e848485U,0x3f9d5185U,0x3f64d3aaU,0x3dfbb5a2U,0x3f33b3b4U}},
    {"synth/media:mediaInput", "flip18", "eef3575d2818f3d32e29665aa509ac8e80b4474e7c6705748d3b86642e9730f4", "fab5e43463e2562c0e744cec7c55c3e1065d0c19c62f50ff1e5d53e42c04da6d", {0x4009039bU,0x404d8568U,0x403615a2U,0x3e8e8e8fU,0x3fb45d17U,0x3f000000U,0x3f1745d1U,0x3e848485U,0x4009039bU,0x404d8568U,0x403615a2U,0x3e8e8e8fU}},
    {"synth/media:mediaInput", "outOfBounds", "dc332bda86b5c5f451ce3844867e9f62a2af15ab683b6e5da859165bab81b572", "12ef692d6c495ab4b84876af5c2ce27c1b5380afac731adb8c81dad74bcabf72", {0x3cf5c28fU,0x3f11eb85U,0x3f68f5c3U,0x3f2147aeU,0x3cf5c28fU,0x3f11eb85U,0x3f68f5c3U,0x3f2147aeU,0x3cf5c28fU,0x3f11eb85U,0x3f68f5c3U,0x3f2147aeU}},
    {"synth/media:mediaInput", "transparent", "255aa0eeba6b02ace941c1378f9260e4fca0327d50fc2fd68e66be10b8a262cf", "2d266b9690f8fca32871c0b04cf1df5d37c9216129b144c051ab11dee4a57bb5", {0x3f53d3d4U,0x3e149495U,0x3f0f8f90U,0x00000000U,0x3f53d3d4U,0x3e149495U,0x3f0f8f90U,0x00000000U,0x3f53d3d4U,0x3e149495U,0x3f0f8f90U,0x00000000U}},
    {"synth/media:mediaInput", "scaleZeroGuard", "d265ac74abeb0174b8089a161abbb64310197a86b934cd4dbd36abaa57c2fd37", "d12699ea4e6b0fd408cffa9df747a63672f28379b54c6ec006571f10bbd55fd7", {0x3f0eb044U,0x3fc53ef4U,0x400a7de7U,0x3e74f4f5U,0x3fb45d17U,0x3f000000U,0x3f1745d1U,0x3e848485U,0x4009039bU,0x404d8568U,0x403615a2U,0x3e8e8e8fU}},
  }};
  constexpr std::array<std::size_t, 3> pixels{0U, 17U, 34U};
  for (const Task11Case& fixture : fixtures) {
    const noisemaker::Surface first = render_task11(fixture);
    const noisemaker::Surface second = render_task11(fixture);
    require_repeat(first, second);
    const std::string name = std::string(fixture.key) + "/" + std::string(fixture.variant);
    const auto floats = little_endian_float_bytes(first);
    if (hex(sha256(floats)) != fixture.float_hash) {
      std::ostringstream detail;
      detail << name << " float oracle hash: " << hex(sha256(floats)) << " probes:";
      for (std::size_t pixel : pixels) for (std::size_t lane = 0; lane < 4U; ++lane)
        detail << ' ' << std::hex << noisemaker::float_bits_to_uint(first.data()[pixel * 4U + lane]);
      throw std::runtime_error(detail.str());
    }
    if (hex(sha256(first.to_rgba8())) != fixture.rgba_hash)
      throw std::runtime_error(name + " rgba oracle hash: " + hex(sha256(first.to_rgba8())));
    for (std::size_t probe = 0; probe < pixels.size(); ++probe)
      for (std::size_t lane = 0; lane < 4U; ++lane)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[pixels[probe] * 4U + lane]) ==
                fixture.probes[probe * 4U + lane]);
  }
}

TEST(typed_task11_each_distinct_signature_and_sampler_fails_closed) {
  struct UniformFixture {
    std::string_view key;
    std::string_view variant;
    std::string_view uniform;
    noisemaker::glsl::UniformValue wrong;
  };
  const std::array<UniformFixture, 9> uniforms{{
      {"classicNoisedeck/splat:splat", "primary", "enabled", 1.0f},
      {"filter/corrupt:corrupt", "clean", "intensity", noisemaker::glsl::Vec2(1.0f)},
      {"filter/flipMirror:flipMirror", "mode0", "flipMode", 1.0f},
      {"filter/outline:outlineBlend", "blackOutline", "invert", std::int32_t{1}},
      {"filter/spatter:spatter", "primary", "color", 1.0f},
      {"filter/tint:colorize", "mode0", "color", 1.0f},
      {"mixer/blendMode:blendMode", "mode0", "mode", 1.0f},
      {"mixer/centerMask:centerMask", "shape0", "shape", 1.0f},
      {"synth/media:mediaInput", "position0", "imageSize", 1.0f},
  }};
  struct SamplerFixture { std::string_view key; std::string_view variant; std::string_view sampler; };
  constexpr std::array<SamplerFixture, 13> samplers{{
      {"classicNoisedeck/splat:splat", "primary", "inputTex"},
      {"filter/corrupt:corrupt", "clean", "inputTex"},
      {"filter/flipMirror:flipMirror", "mode0", "inputTex"},
      {"filter/outline:outlineBlend", "blackOutline", "inputTex"},
      {"filter/outline:outlineBlend", "blackOutline", "edgesTexture"},
      {"filter/outline:outlineValueMap", "colorOklab", "inputTex"},
      {"filter/spatter:spatter", "primary", "inputTex"},
      {"filter/tint:colorize", "mode0", "inputTex"},
      {"mixer/blendMode:blendMode", "mode0", "inputTex"},
      {"mixer/blendMode:blendMode", "mode0", "tex"},
      {"mixer/centerMask:centerMask", "shape0", "inputTex"},
      {"mixer/centerMask:centerMask", "shape0", "tex"},
      {"synth/media:mediaInput", "position0", "imageTex"},
  }};
  const noisemaker::Surface input = source(5U, 3U, 1U);
  const noisemaker::Surface tex = source(7U, 2U, 23U);
  const noisemaker::Surface edges = task11_edges();
  const noisemaker::Surface grayscale = task11_grayscale();
  const noisemaker::Surface tint_hybrid = task11_tint_hybrid();
  const noisemaker::Surface media = source(17U, 13U, 59U);
  const noisemaker::Surface transparent = task11_transparent();
  for (const UniformFixture& item : uniforms) {
    const Task11Case fixture{item.key, item.variant, "", "", {}};
    noisemaker::glsl::Bindings missing;
    populate_task11_bindings(missing, fixture, input, tex, edges, grayscale, tint_hybrid,
                             media, transparent, item.uniform);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, missing), noisemaker::glsl::KernelBindingError);
    noisemaker::glsl::Bindings wrong;
    populate_task11_bindings(wrong, fixture, input, tex, edges, grayscale, tint_hybrid,
                             media, transparent);
    wrong.set_uniform(std::string(item.uniform), item.wrong);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, wrong), noisemaker::glsl::KernelBindingError);
  }
  for (const SamplerFixture& item : samplers) {
    const Task11Case fixture{item.key, item.variant, "", "", {}};
    noisemaker::glsl::Bindings missing;
    populate_task11_bindings(missing, fixture, input, tex, edges, grayscale, tint_hybrid,
                             media, transparent, item.sampler);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, missing), noisemaker::glsl::KernelBindingError);
  }
}

struct Task12Case {
  std::string_view key;
  std::string_view variant;
  std::string_view float_hash;
  std::string_view rgba_hash;
  std::array<std::uint32_t, 12> probes;
};

[[nodiscard]] noisemaker::Surface constant_surface(std::size_t width, std::size_t height,
                                                   std::array<std::uint8_t, 4> rgba) {
  std::vector<std::uint8_t> bytes(width * height * 4U);
  for (std::size_t i = 0; i < width * height; ++i)
    std::copy(rgba.begin(), rgba.end(), bytes.begin() + static_cast<std::ptrdiff_t>(i * 4U));
  return noisemaker::Surface::from_rgba8(width, height, bytes);
}

[[nodiscard]] std::int32_t task12_number(std::string_view value, std::string_view prefix,
                                         std::int32_t fallback = 0) {
  if (!value.starts_with(prefix)) return fallback;
  std::int32_t result = 0;
  bool found = false;
  for (const char character : value.substr(prefix.size())) {
    if (character < '0' || character > '9') break;
    found = true;
    result = result * 10 + static_cast<std::int32_t>(character - '0');
  }
  return found ? result : fallback;
}

void populate_task12_bindings(noisemaker::glsl::Bindings& bindings, const Task12Case& fixture,
                              const noisemaker::Surface& tag1, const noisemaker::Surface& tag23,
                              const noisemaker::Surface& tag37, const noisemaker::Surface& constant_a,
                              const noisemaker::Surface& constant_b, const noisemaker::Surface& hue_negative,
                              std::string_view skip = {}) {
  const auto uniform = [&](std::string_view name, noisemaker::glsl::UniformValue value) {
    if (name != skip) bindings.set_uniform(std::string(name), std::move(value));
  };
  const auto texture = [&](std::string_view name, const noisemaker::Surface& surface) {
    if (name != skip) bindings.set_texture(std::string(name), surface);
  };
  const bool full_resolution_fallback = fixture.variant == "fullResolutionFallback";
  uniform("resolution", noisemaker::glsl::Vec2(9.0f, 7.0f));
  uniform("tileOffset", noisemaker::glsl::Vec2(-5.0f, 3.0f));
  uniform("fullResolution", full_resolution_fallback ? noisemaker::glsl::Vec2(0.0f)
                                                     : noisemaker::glsl::Vec2(17.0f, 13.0f));
  uniform("time", 0.375f);

  if (fixture.key == "classicNoisedeck/coalesce:coalesce") {
    texture("inputTex", tag1); texture("tex", tag23);
    std::int32_t mode = task12_number(fixture.variant, "blend");
    if (fixture.variant.starts_with("hsv")) mode = task12_number(fixture.variant, "hsv");
    else if (fixture.variant == "cloak100") mode = 100;
    else if (fixture.variant == "factorHalf" || fixture.variant == "factorLow") mode = 10;
    else if (fixture.variant == "alphaNegative") mode = 1;
    uniform("blendMode", mode);
    uniform("mixAmt", fixture.variant == "factorHalf" ? 0.5f :
                      fixture.variant == "factorLow" ? 0.25f :
                      fixture.variant == "alphaNegative" ? -37.0f : 50.0f);
    uniform("refractAAmt", 43.0f); uniform("refractBAmt", 61.0f);
    uniform("refractADir", -137.0f); uniform("refractBDir", 211.0f);
  } else if (fixture.key == "classicNoisedeck/composite:composite") {
    texture("inputTex", constant_a); texture("tex", constant_b);
    std::int32_t mode = task12_number(fixture.variant, "mode");
    uniform("blendMode", mode); uniform("range", 1.0f); uniform("mixAmt", 63.0f);
    if (fixture.variant.ends_with("Far")) uniform("inputColor", noisemaker::glsl::Vec3(0.0f));
    else if (fixture.variant == "mode2Near") uniform("inputColor", noisemaker::glsl::Vec3(230.0f / 255.0f, 77.0f / 255.0f, 179.0f / 255.0f));
    else uniform("inputColor", noisemaker::glsl::Vec3(0.2f, 0.6f, 26.0f / 255.0f));
  } else if (fixture.key == "filter/hs:hs") {
    texture("inputTex", hue_negative);
    uniform("rotation", static_cast<float>(task12_number(fixture.variant, "sector")));
    uniform("hueRange", 100.0f); uniform("saturation", 73.0f);
  } else if (fixture.key == "filter/repeat:repeat") {
    texture("inputTex", tag37); uniform("aspect", 9.0f / 7.0f);
    uniform("x", -2.7f); uniform("y", 3.4f); uniform("offsetX", -0.83f); uniform("offsetY", 0.67f);
    uniform("wrap", task12_number(fixture.variant, "wrap"));
  } else if (fixture.key == "filter/scale:scale") {
    texture("inputTex", tag37); uniform("aspect", 9.0f / 7.0f);
    uniform("scaleX", -1.7f); uniform("scaleY", 2.3f); uniform("centerX", 0.73f); uniform("centerY", -0.61f);
    uniform("wrap", task12_number(fixture.variant, "wrap"));
  } else if (fixture.key == "filter/scroll:scroll") {
    texture("inputTex", tag37); uniform("aspect", 9.0f / 7.0f);
    uniform("x", -0.81f); uniform("y", 0.66f); uniform("speedX", 1.7f); uniform("speedY", -2.2f);
    uniform("wrap", task12_number(fixture.variant, "wrap"));
  } else if (fixture.key == "filter/translate:translate") {
    texture("inputTex", tag37); uniform("x", -0.91f); uniform("y", 0.78f);
    uniform("wrap", task12_number(fixture.variant, "wrap"));
  } else if (fixture.key == "mixer/patternMix:patternMix") {
    texture("inputTex", tag1); texture("tex", tag23);
    std::int32_t pattern = fixture.variant == "fallback" ? 99 :
                           fixture.variant == "fullResolutionFallback" ? 4 :
                           task12_number(fixture.variant, "pattern");
    uniform("patternType", pattern); uniform("scale", 5.7f); uniform("thickness", 0.58f);
    uniform("smoothness", 0.047f); uniform("rotation", 31.0f);
    uniform("invert", std::int32_t(fixture.variant == "invert"));
  } else if (fixture.key == "mixer/shapeMask:shapeMask") {
    texture("inputTex", tag1); texture("tex", tag23);
    std::int32_t shape = fixture.variant == "fallback" ? 99 :
                         (fixture.variant == "invert" || fixture.variant == "animated" ||
                          fixture.variant == "fullResolutionFallback") ? 5 :
                         task12_number(fixture.variant, "shape");
    uniform("shape", shape); uniform("radius", 0.57f); uniform("edgeSmooth", 0.083f);
    uniform("rotation", 27.0f); uniform("posX", -0.23f); uniform("posY", 0.19f);
    uniform("invert", std::int32_t(fixture.variant == "invert"));
    uniform("speed", std::int32_t(fixture.variant == "animated" ? 2 : 0));
  } else if (fixture.key == "mixer/split:split") {
    texture("inputTex", tag1); texture("tex", tag23);
    uniform("position", -0.17f); uniform("rotation", 38.0f); uniform("softness", 0.12f);
    uniform("invert", std::int32_t(fixture.variant == "invertOdd"));
    uniform("speed", fixture.variant == "animatedEven" ? 0.5f :
                     (fixture.variant == "animatedOdd" || fixture.variant == "invertOdd") ? 2.0f : 0.0f);
  } else if (fixture.key == "mixer/uvRemap:uvRemap") {
    texture("inputTex", tag1); texture("tex", tag23);
    const bool fallback = fixture.variant == "fallbacks";
    const std::int32_t map_source = fallback ? 9 : task12_number(fixture.variant, "map");
    const std::size_t channel_pos = fixture.variant.find("channel");
    const std::size_t wrap_pos = fixture.variant.find("wrap");
    const std::int32_t channel = fallback ? 9 : task12_number(fixture.variant.substr(channel_pos), "channel");
    const std::int32_t wrap = fallback ? 9 : task12_number(fixture.variant.substr(wrap_pos), "wrap");
    uniform("mapSource", map_source); uniform("channel", channel); uniform("scale", 260.0f);
    uniform("offset", -1.23f); uniform("wrap", wrap);
  } else if (fixture.key == "synth/modPattern:modPattern") {
    std::int32_t shape1 = 0, shape2 = 1, shape3 = 2, blend = 0, anim = 0;
    if (fixture.variant == "blend1Anim1") { shape1 = 1; shape2 = 2; shape3 = 0; blend = 1; anim = 1; }
    else if (fixture.variant == "blend2Anim2") { shape1 = 2; shape2 = 0; shape3 = 1; blend = 2; anim = 2; }
    else if (fixture.variant == "blend3") { shape1 = -1; blend = 3; }
    uniform("shape1", shape1); uniform("scale1", 5.3f); uniform("repeat1", 3.7f);
    uniform("shape2", shape2); uniform("scale2", 4.6f); uniform("repeat2", 5.1f);
    uniform("shape3", shape3); uniform("scale3", 3.2f); uniform("repeat3", 6.3f);
    uniform("blend", blend); uniform("smoothing", 12.0f); uniform("speed", 3.7f); uniform("animMode", anim);
  } else if (fixture.key == "synth/pattern:pattern") {
    const std::int32_t pattern = fixture.variant == "fallback" ? 99 : task12_number(fixture.variant, "pattern");
    uniform("aspect", 9.0f / 7.0f); uniform("patternType", pattern); uniform("scale", 5.4f);
    uniform("thickness", 0.57f); uniform("smoothness", 0.046f); uniform("rotation", 29.0f);
    uniform("skew", -0.31f); uniform("animation", std::int32_t(pattern == 0 ? 2 : pattern == 2 ? 1 : 0));
    uniform("speed", 3.6f); uniform("fgColor", noisemaker::glsl::Vec3(0.91f, 0.17f, 0.63f));
    uniform("bgColor", noisemaker::glsl::Vec3(0.08f, 0.72f, 0.34f));
  }
}

[[nodiscard]] noisemaker::Surface render_task12(const Task12Case& fixture, std::string_view skip = {}) {
  const noisemaker::Surface tag1 = source(5U, 3U, 1U);
  const noisemaker::Surface tag23 = source(7U, 2U, 23U);
  const noisemaker::Surface tag37 = source(4U, 6U, 37U);
  const noisemaker::Surface constant_a = constant_surface(5U, 3U, {51U, 153U, 26U, 102U});
  const noisemaker::Surface constant_b = constant_surface(7U, 2U, {230U, 77U, 179U, 204U});
  const noisemaker::Surface hue_negative = constant_surface(3U, 2U, {230U, 10U, 180U, 177U});
  noisemaker::glsl::Bindings bindings;
  populate_task12_bindings(bindings, fixture, tag1, tag23, tag37, constant_a, constant_b, hue_negative, skip);
  return noisemaker::run_pass(noisemaker::generated::bind(fixture.key, bindings), 9U, 7U, 0.375f, 7.0f);
}

TEST(typed_task12_all_one_hundred_twenty_external_oracles_are_exact_and_repeatable) {
  constexpr std::array<Task12Case, 120> fixtures{{
    {"classicNoisedeck/coalesce:coalesce", "blend0", "97dd85fd6dbce05a97547a57f6d635a5a709b41ba90f3a0daeaee122e462c0f6", "dced92b303abbead204edbe034f652745ba54202d0ba9c5e8fe5512f49c55401", {0x3f72f2f3U,0x3f6eeeefU,0x3e9f9fa0U,0x3ea8a8a9U,0x3f4d4d4eU,0x3f616162U,0x3f747474U,0x3f7afafbU,0x3f72f2f3U,0x3f6eeeefU,0x3f0d0d0dU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend1", "010e98b26d5f6d11f1718bc0c343f64a02539e74b0d251304370125e00f83360", "b9c4ca55c9be71fb6dc752539a6c85c580ec8e7dd7320f2a1e2e42e2641b4d2b", {0x3f49033eU,0x3f42f930U,0x3e58c0a8U,0x3ea8a8a9U,0x3ee6092dU,0x3f00e040U,0x3f07735fU,0x3f7afafbU,0x3f2a229bU,0x3f380451U,0x3ee5e4e4U,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend2", "e3e883d48f8eedf9f0aaccb4944d84b096bcf34b4a8a88657fd4b0741fdb462a", "b030e63c975c7d9f2b2a0b9afad4e93162c225ca396c9a5fc24c6ee25667ee5e", {0x3ee5e5e6U,0x3edddddeU,0x3dcccccdU,0x3ea8a8a9U,0x3ec6c6c7U,0x3ed2d2d3U,0x3ef0f0f1U,0x3f7afafbU,0x3ee5e5e6U,0x3edddddeU,0x3dcccccdU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend3", "e3e883d48f8eedf9f0aaccb4944d84b096bcf34b4a8a88657fd4b0741fdb462a", "b030e63c975c7d9f2b2a0b9afad4e93162c225ca396c9a5fc24c6ee25667ee5e", {0x3ee5e5e6U,0x3edddddeU,0x3dcccccdU,0x3ea8a8a9U,0x3ec6c6c7U,0x3ed2d2d3U,0x3ef0f0f1U,0x3f7afafbU,0x3ee5e5e6U,0x3edddddeU,0x3dcccccdU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend4", "16041dc80ee5178474a01ea40a8a505c5a45cb4c3df85c1450b345e3a055c1dc", "74b0dd10bc88d961544f04fba9e85638783b0f30f57004fdaf15a3dd5d6bb008", {0x3f48c8c9U,0x3f42c2c3U,0x3e4ccccdU,0x3ea8a8a9U,0x3ed3d3d4U,0x3eefeff0U,0x3ef7f7f8U,0x3f7afafbU,0x3f29a9aaU,0x3f37b7b8U,0x3e4ccccdU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend5", "1c25c866a2ba32469e9742c88f7e98279195d84a493ab37f0f4a73ce4538117c", "01a782720c33dc05beeeff915d29c5c940d1ec6b268c5503b60f3ff4077c3511", {0x3f101010U,0x3f0a0a0aU,0x3de4e4e5U,0x3ea8a8a9U,0x3f404040U,0x3f444444U,0x3f6d6d6eU,0x3f7afafbU,0x3f2f2f2fU,0x3f151515U,0x3eb3b3b4U,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend6", "d069ee7802684b68933c586e29ddf36f71b9aa20395cbcec669d2d57869dc482", "b16833853a09b7e3b15796cc07963aa64336484c5781e811d19f11f7934fc98e", {0x3f219100U,0x3f2064a9U,0x3e88bbefU,0x3ea8a8a9U,0x3f432b13U,0x3f496786U,0x3f6dd740U,0x3f7afafbU,0x3f3a5774U,0x3f287dd3U,0x3ed2389fU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend7", "e3e883d48f8eedf9f0aaccb4944d84b096bcf34b4a8a88657fd4b0741fdb462a", "b030e63c975c7d9f2b2a0b9afad4e93162c225ca396c9a5fc24c6ee25667ee5e", {0x3ee5e5e6U,0x3edddddeU,0x3dcccccdU,0x3ea8a8a9U,0x3ec6c6c7U,0x3ed2d2d3U,0x3ef0f0f1U,0x3f7afafbU,0x3ee5e5e6U,0x3edddddeU,0x3dcccccdU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend8", "8df042311d6246611c8943527d0680d66fb8bf3c53dde3e3397f1708ddd8a747", "8a41124d09c78487025fc06de361902e9965fa8321b6ee60288435449aa48065", {0x3f6a59caU,0x3f63276cU,0x3e142dc8U,0x3ea8a8a9U,0x3f2d14fdU,0x3f415f7eU,0x3f69d33cU,0x3f7afafbU,0x3f64011eU,0x3f60358bU,0x3e76295eU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend9", "54a4e6c5c2ac39904394ee80bc94c7b3268fb56bb0b40f7d3e53f0c4c9aebd19", "a30bfa597b2538c3e9000ddb0448f78b8253db4faa4e307562a928e219ac11fe", {0x3f65e5e6U,0x3f5ddddeU,0x3e58d8d9U,0x3ea8a8a9U,0x3f46c6c7U,0x3f52d2d3U,0x3f70f0f1U,0x3f7afafbU,0x3f65e5e6U,0x3f5ddddeU,0x3ee6e6e7U,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend10", "0eba4cb58aec5b8e28267fde3ea52621641b8e5a834ebd932980a852377b80bc", "e498b09ba8005d8111da2fdaeb2477b870d0c6f43525d701393d45a3de831dc7", {0x3f575758U,0x3f505050U,0x3e52d2d3U,0x3ea8a8a9U,0x3f185858U,0x3f256566U,0x3f367676U,0x3f7afafbU,0x3f47c7c8U,0x3f4acacbU,0x3ea6a6a7U,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend11", "aa08828b6905a370b6803e0994f0f7bbdcd37bd5f5c3b994b2d32e3db06a4c3f", "2ef61859ad040cde81da9715a9271396c630454fa45fbcb350611029c1b6d6c2", {0x3f400851U,0x3f379574U,0x3dfa942eU,0x3ea8a8a9U,0x3ed0e901U,0x3eeaccafU,0x3ef78e25U,0x3f7afafbU,0x3f241587U,0x3f2e0359U,0x3e2e47e2U,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend12", "5a9bdd243c8e3546d249355735adc77f4f027fc5c626fd08c898ba5b3d904643", "691c5bfa4bc802f45ec9325180891d76b3470973e4431da3aa5af7c7ad049471", {0x3f2a2a2aU,0x3f2c2c2cU,0x3e9f9f9fU,0x3ea8a8a9U,0x3f4d4d4eU,0x3f616162U,0x3f747474U,0x3f7afafbU,0x3f494949U,0x3f373737U,0x3f0d0d0dU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend13", "d8cf67de2bcb45a8601f54714e41932ce8516d7c9822bf2ddfa534b5d02ac73d", "6406114e5d74b570aad63f790b0cea9f9ff22c050e8cb2529e3de6faf990733a", {0x3f6a59caU,0x3f63276cU,0x3e142dc8U,0x3ea8a8a9U,0x3edb0b3cU,0x3f016345U,0x3efe2b59U,0x3f7afafbU,0x3f55381bU,0x3f60358bU,0x3eb91f86U,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend14", "2a72bc28555439f5cd50708f60c89507bb185ea9d301aea5db4156e12fe5c4fb", "6a048fb6988a59141173557055e70207fb0fde33e925837f79683d2334a536ad", {0x3f55d5d6U,0x3f53d3d4U,0x3f169697U,0x3ea8a8a9U,0x3f068686U,0x3f0e8e8eU,0x3f038384U,0x3f7afafbU,0x3f36b6b7U,0x3f48c8c9U,0x3eb2b2b2U,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend15", "e3e883d48f8eedf9f0aaccb4944d84b096bcf34b4a8a88657fd4b0741fdb462a", "b030e63c975c7d9f2b2a0b9afad4e93162c225ca396c9a5fc24c6ee25667ee5e", {0x3ee5e5e6U,0x3edddddeU,0x3dcccccdU,0x3ea8a8a9U,0x3ec6c6c7U,0x3ed2d2d3U,0x3ef0f0f1U,0x3f7afafbU,0x3ee5e5e6U,0x3edddddeU,0x3dcccccdU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend16", "3cd0b5d51880aa489c8aa57d5550162a12a410a7517bed4cd5d128bbebea4314", "814372e7e5f0295360b38b9de4b1e186d38d3eb393aa8aa93e5949049a5b850d", {0x3f6ea65eU,0x3f690b2eU,0x3e942dc7U,0x3ea8a8a9U,0x3f483c30U,0x3f556474U,0x3f7125daU,0x3f7afafbU,0x3f6b7a08U,0x3f67923dU,0x3ef6295dU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend17", "8544639f3c57b4baf86aba51f609fa581187de4d8f40de12f88d83e98fd3114e", "9be011e81b437f1306d2663e52328b1fbbc9260a3cada4d06d11bcf5a8d4ff1b", {0x3f57e57cU,0x3f513ff8U,0x3e238738U,0x3ea8a8a9U,0x3eec9271U,0x3f0a7af1U,0x3f0b98b0U,0x3f7afafbU,0x3f40ba1cU,0x3f491ff9U,0x3ec6c45cU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "blend18", "02d8fe233dd0b3f9d7e98e9ac9506d416171aaab8e48c574fefb63c6b6402559", "13ba700ea98744eea9def8c768fc677edd618494bd83c61402b5c14f36794140", {0x3f3bbbbcU,0x3f31b1b2U,0x3dcccccdU,0x3ea8a8a9U,0x3ec6c6c7U,0x3ed2d2d3U,0x3ef0f0f1U,0x3f7afafbU,0x3f1c9c9dU,0x3f26a6a7U,0x3dcccccdU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "hsv1000", "4f936dcacfa894d969837b80ccdef19599bba16b56ec905f6a0ab9732be3c8d4", "bfef8307b61ff2402cc8c0d1dacce10df0a840a4413bbe8bb2ea46504e271712", {0x3f48c8c9U,0x3f423260U,0x3e58d8d8U,0x3ea8a8a9U,0x3ecdcdceU,0x3ee0294eU,0x3f070707U,0x3f7afafbU,0x3f4ccccdU,0x3f473482U,0x3ea0a0a1U,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "hsv1001", "71faabeb22159fa0c80835a53babd0b281c7eecabdf9d490fe194aaed5b4acba", "2bacf96b0b99ea26c93091d05195fdad7ee35a948cac7c4a7045b8e0d83c2d8a", {0x3f65e5e6U,0x3f5ebf50U,0x3e4cccceU,0x3ea8a8a9U,0x3f4c86b6U,0x3f61e1e2U,0x3f5bdbdcU,0x3f7afafbU,0x3f0c8c8dU,0x3f367bfaU,0x3f0c8c8dU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "hsv1002", "79f2f32e9abcd657d696adc9c8cb7b3a04a1ee9ce012b8c6d900d12dc4dabad2", "ab31ff46412a6396ea0beee57f5d2d55bfefcd1b7c3295118bdbedb55a642c22", {0x3f48c8c9U,0x3f426d78U,0x3e32dd59U,0x3ea8a8a9U,0x3ee02f50U,0x3eefeff0U,0x3f047ae1U,0x3f7afafbU,0x3f06f5a2U,0x3f26dc9fU,0x3ee6e6e7U,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "hsv1003", "c56e4546631f9e9010bd997327ca1435bb8ec29f87167edfeb939a04b81d9950", "742664dadd912b3f14a79ab7cade9521752981edc8aebb86c18ad7b658c95dff", {0x3f65e5e6U,0x3f5e702dU,0x3e7faa54U,0x3ea8a8a9U,0x3f0077a4U,0x3f209a4cU,0x3f70f0f1U,0x3f7afafbU,0x3f65e5e6U,0x3f5fdcaeU,0x3ebf319bU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "hsv1004", "02a6c56b5401a2482fb8b60597c5a2516a738a0c5680b72110b1a151eac0e24c", "a172f7327e9024f0f6434f6309d158019c7ebeed50f647f3fa579ec429a045d6", {0x3f65e5e6U,0x3f5f3188U,0x3e7faa54U,0x3ea8a8a9U,0x3f19646dU,0x3f61e1e2U,0x3f158cb9U,0x3f7afafbU,0x3f38f227U,0x3f4c0c68U,0x3f0c8c8dU,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "hsv1005", "59dd13159cefe5d01861c0d21e749bd869eee9808990f28a5c1afc6feca42fa1", "bf9578683acb572624c98e6390178e00e87cd4179f1c076abca5f7728d17c665", {0x3f48c8c9U,0x3f41c520U,0x3e32dd59U,0x3ea8a8a9U,0x3edecb99U,0x3eec4c4cU,0x3f070707U,0x3f7afafbU,0x3f4ccccdU,0x3f45a53aU,0x3e367122U,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "cloak100", "06a4b6bdfeb87ebac2b8746d1cb87a653432a9be54d1e2bf14c787afb0f2ba4e", "06f3512c3e40857ecd5978e0c929f9ecc4269a0053ea9b7766678fbaae3d24aa", {0x3ec23535U,0x3f4d00e8U,0x3e53e4ecU,0x3e77f7f9U,0x3f077d94U,0x3f381bafU,0x3ec42070U,0x3e68d70aU,0x3f333334U,0x3f35cd18U,0x3ece5d85U,0x3e07953eU}},
    {"classicNoisedeck/coalesce:coalesce", "factorHalf", "175a02c6b6f312fe1e96e83046efac5df4caaacd09b0acc82d3c8d27c05d6528", "d31a5ee03d93287dc62c4b83b4f9fee5310a209faa0bfc53a642acebc9b1c092", {0x3f48c8c9U,0x3f42c2c3U,0x3e58d8d9U,0x3ea8a8a9U,0x3ed3d3d4U,0x3eefeff0U,0x3ef7f7f8U,0x3f7afafbU,0x3f29a9aaU,0x3f37b7b8U,0x3ee6e6e7U,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "factorLow", "5e993773b3e0f57325c1cddbe366977e60f785d01be1938b4def671914170b39", "c3687230c83f7c1b144ee5ecb1cfc9db9f98d8b5dee7151b37e470ad1903a372", {0x3f48db6bU,0x3f42d41cU,0x3e58d123U,0x3ea8a8a9U,0x3ed44ab1U,0x3ef0643bU,0x3ef88dacU,0x3f7afafbU,0x3f29d037U,0x3f37d022U,0x3ee694a9U,0x3f028283U}},
    {"classicNoisedeck/coalesce:coalesce", "alphaNegative", "9711c8c238fb1ce6a92a904618d0a66d5bd28e8dbed3f7f0bec06c2e8544c173", "158ff2f84e964bab7ea5553ad33e9cfa47f0833844948bb6227d991247f913b8", {0x3f44451dU,0x3f3e8ecbU,0x3e5ab70fU,0x3ea8a8a9U,0x3d758617U,0x3dfaddf4U,0x3d1eabecU,0x3f7afafbU,0x3f12a1b1U,0x3f29219bU,0x3f0c047dU,0x3f028283U}},
    {"classicNoisedeck/composite:composite", "mode0", "1c97ee807c26e716990d362cc0d80bf6ee69e0d1d5648617da5f71d0dd24adb4", "184fe3300052193070ee37ee5bc9901c499b29c378d665fe6c86a4bb788b0021", {0x3f246988U,0x3f4a4cdcU,0x3f1b203fU,0x3f26e979U,0x3f246988U,0x3f4a4cdcU,0x3f1b203fU,0x3f26e979U,0x3f246988U,0x3f4a4cdcU,0x3f1b203fU,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode1", "06b8dded3cb3f30524aacf8a8644808ee9d3142063030db2cbc195d0a2a99116", "4e419de20f12944324c0ad6ef9f7ef6ed7fef1936977905f0ed5e3c96f3b0f53", {0x3f66e6e7U,0x3e9a9a9bU,0x3f33b3b4U,0x3f26e979U,0x3f66e6e7U,0x3e9a9a9bU,0x3f33b3b4U,0x3f26e979U,0x3f66e6e7U,0x3e9a9a9bU,0x3f33b3b4U,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode2", "45d6f828e4ea8e0b1870f11ecc5c6c7d2663a9eb01c8f058a4885afc48274ded", "095a9894b8b9368ed433e9afe2ab6233153eba1e1d35171ce73fa78ac1163e34", {0x3eeb6124U,0x3efabd4dU,0x3ea5de31U,0x3f26e979U,0x3eeb6124U,0x3efabd4dU,0x3ea5de31U,0x3f26e979U,0x3eeb6124U,0x3efabd4dU,0x3ea5de31U,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode3", "c4e5526867dd5900e871968f69fbf817cd4e725ab2a3f41c4ae7415ff160a935", "83e8b74fb862d8d9d82bce1edaf28781f27dc2245c3170e11ca501c304cdaea8", {0x3e4ccccdU,0x3f19999aU,0x3dd0d0d1U,0x3f26e979U,0x3e4ccccdU,0x3f19999aU,0x3dd0d0d1U,0x3f26e979U,0x3e4ccccdU,0x3f19999aU,0x3dd0d0d1U,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode4", "c4e5526867dd5900e871968f69fbf817cd4e725ab2a3f41c4ae7415ff160a935", "83e8b74fb862d8d9d82bce1edaf28781f27dc2245c3170e11ca501c304cdaea8", {0x3e4ccccdU,0x3f19999aU,0x3dd0d0d1U,0x3f26e979U,0x3e4ccccdU,0x3f19999aU,0x3dd0d0d1U,0x3f26e979U,0x3e4ccccdU,0x3f19999aU,0x3dd0d0d1U,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode5", "f6bb7c19d94c08601d7515eb4fedf7a9a001851330a8390c55ddaad66f9ca89f", "8f6df0b1523ef39e74988a6a477411b46a389f578ce724cbd93f246387571586", {0x3e50d349U,0x3f192c38U,0x3dd7b26dU,0x3f26e979U,0x3e50d349U,0x3f192c38U,0x3dd7b26dU,0x3f26e979U,0x3e50d349U,0x3f192c38U,0x3dd7b26dU,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode6", "9268c15fb4ee01a292d0684b1a52c4ea676edb4c23ad34ec239746b8a074601c", "8f6df0b1523ef39e74988a6a477411b46a389f578ce724cbd93f246387571586", {0x3e4fcffbU,0x3f1947beU,0x3dd5f727U,0x3f26e979U,0x3e4fcffbU,0x3f1947beU,0x3dd5f727U,0x3f26e979U,0x3e4fcffbU,0x3f1947beU,0x3dd5f727U,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode7", "a8ed2b07653714ca34e1582ecabf785a538044ebaf145aa81c486ee6925e155e", "8f6df0b1523ef39e74988a6a477411b46a389f578ce724cbd93f246387571586", {0x3e50e270U,0x3f192a9dU,0x3dd7cc55U,0x3f26e979U,0x3e50e270U,0x3f192a9dU,0x3dd7cc55U,0x3f26e979U,0x3e50e270U,0x3f192a9dU,0x3dd7cc55U,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode8", "06b8dded3cb3f30524aacf8a8644808ee9d3142063030db2cbc195d0a2a99116", "4e419de20f12944324c0ad6ef9f7ef6ed7fef1936977905f0ed5e3c96f3b0f53", {0x3f66e6e7U,0x3e9a9a9bU,0x3f33b3b4U,0x3f26e979U,0x3f66e6e7U,0x3e9a9a9bU,0x3f33b3b4U,0x3f26e979U,0x3f66e6e7U,0x3e9a9a9bU,0x3f33b3b4U,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode9", "06b8dded3cb3f30524aacf8a8644808ee9d3142063030db2cbc195d0a2a99116", "4e419de20f12944324c0ad6ef9f7ef6ed7fef1936977905f0ed5e3c96f3b0f53", {0x3f66e6e7U,0x3e9a9a9bU,0x3f33b3b4U,0x3f26e979U,0x3f66e6e7U,0x3e9a9a9bU,0x3f33b3b4U,0x3f26e979U,0x3f66e6e7U,0x3e9a9a9bU,0x3f33b3b4U,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode10", "8ad251010e45694aa33d8b15cc373ec4ea939518fb0980d64565bd7d6192bfe5", "3d8ea2b6aea6301f4fc48637bff3288cfff2e8053f8d15aa471e607c2278b2c9", {0x3eec0f57U,0x3efa7357U,0x3ea67316U,0x3f26e979U,0x3eec0f57U,0x3efa7357U,0x3ea67316U,0x3f26e979U,0x3eec0f57U,0x3efa7357U,0x3ea67316U,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode11", "1d32ab11e44c649af34b0c02b9cd12176cf2bb11cbdf0aedc11c0d94c949e066", "8e8641d593f9a3f217b366635070c8c11e2673b6b3286bc5d2f4fe3f0454016a", {0x3eed4249U,0x3ef9f105U,0x3ea77973U,0x3f26e979U,0x3eed4249U,0x3ef9f105U,0x3ea77973U,0x3f26e979U,0x3eed4249U,0x3ef9f105U,0x3ea77973U,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode12", "f9a57fb222beb76f05b866c94460ad1ef19b24234b3e35cefba13f5877e6737c", "3d8ea2b6aea6301f4fc48637bff3288cfff2e8053f8d15aa471e607c2278b2c9", {0x3eecbceeU,0x3efa29a3U,0x3ea70776U,0x3f26e979U,0x3eecbceeU,0x3efa29a3U,0x3ea70776U,0x3f26e979U,0x3eecbceeU,0x3efa29a3U,0x3ea70776U,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode13", "2b66470c3293f8b8353678bcb2de80526ee766c1b4a371582c598ffc93370943", "8f6df0b1523ef39e74988a6a477411b46a389f578ce724cbd93f246387571586", {0x3e515418U,0x3f191e8cU,0x3dd88ea0U,0x3f26e979U,0x3e515418U,0x3f191e8cU,0x3dd88ea0U,0x3f26e979U,0x3e515418U,0x3f191e8cU,0x3dd88ea0U,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode14", "81f480969103a5beccbbc4bebf5be36d879ca79d77cec83bb8341c2e3be379d4", "49e4052901e2320afd0ed1313ce86b8320aeb36950009e15945185e47b5b0b31", {0x3f246988U,0x3ed31082U,0x3ef5bd6cU,0x3f26e979U,0x3f246988U,0x3ed31082U,0x3ef5bd6cU,0x3f26e979U,0x3f246988U,0x3ed31082U,0x3ef5bd6cU,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode15", "faf24b99534240f5903c0a1acd1c434d42e9078ef74bd588ba47c805fcd91aa1", "95fe0daf3fe4b585a15f7c2bd576b225fea408baafb54a8b40c500465ef81107", {0x00000000U,0x3f197dd3U,0x3f3e890dU,0x3f26e979U,0x00000000U,0x3f197dd3U,0x3f3e890dU,0x3f26e979U,0x00000000U,0x3f197dd3U,0x3f3e890dU,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode0Far", "c5682747a8aa283055f968e637ed58d2f474703fc81514ac1d3e555ab7069386", "679b80af8175ef1746d0c585ff6f011dd2bd7b636419ddb67b01a61c8b1f32a6", {0x3f4a4cdcU,0x3f4a4cdcU,0x3f4a4cdcU,0x3f26e979U,0x3f4a4cdcU,0x3f4a4cdcU,0x3f4a4cdcU,0x3f26e979U,0x3f4a4cdcU,0x3f4a4cdcU,0x3f4a4cdcU,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode1Far", "81f480969103a5beccbbc4bebf5be36d879ca79d77cec83bb8341c2e3be379d4", "49e4052901e2320afd0ed1313ce86b8320aeb36950009e15945185e47b5b0b31", {0x3f246988U,0x3ed31082U,0x3ef5bd6cU,0x3f26e979U,0x3f246988U,0x3ed31082U,0x3ef5bd6cU,0x3f26e979U,0x3f246988U,0x3ed31082U,0x3ef5bd6cU,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode2Near", "c4e5526867dd5900e871968f69fbf817cd4e725ab2a3f41c4ae7415ff160a935", "83e8b74fb862d8d9d82bce1edaf28781f27dc2245c3170e11ca501c304cdaea8", {0x3e4ccccdU,0x3f19999aU,0x3dd0d0d1U,0x3f26e979U,0x3e4ccccdU,0x3f19999aU,0x3dd0d0d1U,0x3f26e979U,0x3e4ccccdU,0x3f19999aU,0x3dd0d0d1U,0x3f26e979U}},
    {"classicNoisedeck/composite:composite", "mode2Far", "45d6f828e4ea8e0b1870f11ecc5c6c7d2663a9eb01c8f058a4885afc48274ded", "095a9894b8b9368ed433e9afe2ab6233153eba1e1d35171ce73fa78ac1163e34", {0x3eeb6124U,0x3efabd4dU,0x3ea5de31U,0x3f26e979U,0x3eeb6124U,0x3efabd4dU,0x3ea5de31U,0x3f26e979U,0x3eeb6124U,0x3efabd4dU,0x3ea5de31U,0x3f26e979U}},
    {"filter/hs:hs", "sector0", "23b828a89115e9673d5352bb2e3b531c3073e54c8667572579c04e8ac113d601", "724734ca08e9535d7894d7e471277daff7ba9444657c9ecef989274f311b84a7", {0x3f66e6d6U,0xc2785051U,0xc1569683U,0x3f31b1b2U,0x3f66e6d6U,0xc2785051U,0xc1569683U,0x3f31b1b2U,0x3f66e6d6U,0xc2785051U,0xc1569683U,0x3f31b1b2U}},
    {"filter/hs:hs", "sector60", "97ba221ba8c35588003fc8fa71fa869b2c84e8318caf8c9ca54e40946fdad34b", "724734ca08e9535d7894d7e471277daff7ba9444657c9ecef989274f311b84a7", {0x3f66e6d6U,0xc23f0f15U,0xc2785051U,0x3f31b1b2U,0x3f66e6d6U,0xc23f0f15U,0xc2785051U,0x3f31b1b2U,0x3f66e6d6U,0xc23f0f15U,0xc2785051U,0x3f31b1b2U}},
    {"filter/hs:hs", "sector120", "4ca720a4e2cadab0bf8f935693407e951381efbe27c43a259cc1e13583e77eeb", "0dec6ec68a855ff1eac848ab875b0a5bab6c3b1edb7de46a70fb6397a163906b", {0xc1569683U,0x3f66e6d6U,0xc2785051U,0x3f31b1b2U,0xc1569683U,0x3f66e6d6U,0xc2785051U,0x3f31b1b2U,0xc1569683U,0x3f66e6d6U,0xc2785051U,0x3f31b1b2U}},
    {"filter/hs:hs", "sector180", "4744261d950a958af5edc6efa1b8bec35ed9867811851c385ef5c83ce558a055", "0dec6ec68a855ff1eac848ab875b0a5bab6c3b1edb7de46a70fb6397a163906b", {0xc2785051U,0x3f66e6d6U,0xc23f0f15U,0x3f31b1b2U,0xc2785051U,0x3f66e6d6U,0xc23f0f15U,0x3f31b1b2U,0xc2785051U,0x3f66e6d6U,0xc23f0f15U,0x3f31b1b2U}},
    {"filter/hs:hs", "sector240", "0fa1d68e8824cd8655d14c97afe3ab84c4f2fdc71e1c071d2fb576865dc9a886", "2b0fee1e1ff67cd0d05845d9128b053e39dbb69457174eb04f0ef266f9dbf7fa", {0xc2785051U,0xc1569687U,0x3f66e6d6U,0x3f31b1b2U,0xc2785051U,0xc1569687U,0x3f66e6d6U,0x3f31b1b2U,0xc2785051U,0xc1569687U,0x3f66e6d6U,0x3f31b1b2U}},
    {"filter/hs:hs", "sector300", "7adc2e0002f94dbaf6f724f6e7cfe27a153a143c02a8249cdf0fa3839d0f8240", "2b0fee1e1ff67cd0d05845d9128b053e39dbb69457174eb04f0ef266f9dbf7fa", {0xc23f0f17U,0xc2785051U,0x3f66e6d6U,0x3f31b1b2U,0xc23f0f17U,0xc2785051U,0x3f66e6d6U,0x3f31b1b2U,0xc23f0f17U,0xc2785051U,0x3f66e6d6U,0x3f31b1b2U}},
    {"filter/repeat:repeat", "wrap0", "6bf0356ef1872be7e8bb65979a0b93ba25e45aefea915dcd1e766df0ec1a99a6", "023bd2ff84dab48219a952a4915d52107a3a3e1e2ff6c69f943473639af2b30c", {0x3d888889U,0x3ed6d6d7U,0x3eb2b2b3U,0x3f800000U,0x3e888889U,0x3f78f8f9U,0x3f129293U,0x3f800000U,0x3da0a0a1U,0x3f3ebebfU,0x3e70f0f1U,0x3f800000U}},
    {"filter/repeat:repeat", "wrap1", "fc09d55e6a6d247d0d8ada961bf67dcb11360901269c42dec55f2d073c8e7d82", "d62e8c43a065d34b3840c1535a2a77e750ad7d833f13a71ab10ff6646f3e31c4", {0x3f61e1e2U,0x3e44c4c5U,0x3c40c0c1U,0x3f800000U,0x3e888889U,0x3f78f8f9U,0x3f129293U,0x3f800000U,0x3e9e9e9fU,0x3f018182U,0x3f5fdfe0U,0x3f800000U}},
    {"filter/repeat:repeat", "wrap2", "e51124bccc9def1208fdf206091fd8a56ef928bd8f4c2c17a48678f5297c7d98", "1ade32a276bdaf67eef3ba09ee893235696431adc1d2da733dba8df545fad08d", {0x3e78f8f9U,0x3ea4a4a5U,0x3f4ccccdU,0x3f800000U,0x3e78f8f9U,0x3ea4a4a5U,0x3f4ccccdU,0x3f800000U,0x3e78f8f9U,0x3ea4a4a5U,0x3f4ccccdU,0x3f800000U}},
    {"filter/scale:scale", "wrap0", "de18e845862037a5f7c902c4616fa5f4e99d4041e2cfe65947236c02f8da3f4e", "3844ba13d472e7dd260da5ddbf3830054e8a14e8a3da515f471fe773feb6bbc7", {0x3ea4a4a5U,0x3f54d4d5U,0x3f42c2c3U,0x3f800000U,0x3e088889U,0x3f1a9a9bU,0x3ed8d8d9U,0x3f800000U,0x3f61e1e2U,0x3e44c4c5U,0x3c40c0c1U,0x3f800000U}},
    {"filter/scale:scale", "wrap1", "4e0f684dd96525d8b744af6ef355421da34fffbd583f1b8a9591f0ef23b0d464", "effa6aa74b0b276699ded0ba011762a5f3fb299e6583736a72d1bea8fb74fbd2", {0x3e828283U,0x3f25a5a6U,0x3f2fafb0U,0x3f800000U,0x3e4ccccdU,0x3f49c9caU,0x3efefeffU,0x3f800000U,0x3e58d8d9U,0x3de0e0e1U,0x3ec4c4c5U,0x3f800000U}},
    {"filter/scale:scale", "wrap2", "c7b08a7a3b9343f6cc84b88e3c2d2b6aa1461548923906a2cf4df9040593be44", "af4508d5d556374b0eb347da03b39a1a54b3a8ffb630095681145a15d189ac64", {0x3e58d8d9U,0x3de0e0e1U,0x3ec4c4c5U,0x3f800000U,0x3e58d8d9U,0x3de0e0e1U,0x3ec4c4c5U,0x3f800000U,0x3e58d8d9U,0x3de0e0e1U,0x3ec4c4c5U,0x3f800000U}},
    {"filter/scroll:scroll", "wrap0", "6e836e7f4050e3c466970b6bae715e7b631546d5dbe5fe31ed9bc7fea5b57ae3", "0cec4c7c2936ab9f924c13a991577b8ee90870fe66a7344479cfc5f3deb6eb39", {0x3e9e9e9fU,0x3f018182U,0x3f5fdfe0U,0x3f800000U,0x3e149495U,0x3f6dedeeU,0x3e9e9e9fU,0x3f800000U,0x3f028283U,0x3d60e0e1U,0x3dc0c0c1U,0x3f800000U}},
    {"filter/scroll:scroll", "wrap1", "632d0f93be85dd7f0b3fe93aa0ba1751a8b315ec4d4eb2e94a0597611f42517c", "6c951d3662fa309a47448b6b3b2cb0f77557b782cc2bc07e842c6d80a1aea6db", {0x3e9e9e9fU,0x3f018182U,0x3f5fdfe0U,0x3f800000U,0x3f028283U,0x3d60e0e1U,0x3dc0c0c1U,0x3f800000U,0x3e9e9e9fU,0x3f018182U,0x3f5fdfe0U,0x3f800000U}},
    {"filter/scroll:scroll", "wrap2", "b742e2d7dcdc1f604b1c9a6a8d7dcd686aa12b61e13b9376ece7dbf455f38a22", "dd9d698fd3a5e2f4e36c6ad8dea34942846844e9bbb73234f81922de4d6c854a", {0x3e9e9e9fU,0x3f018182U,0x3f5fdfe0U,0x3f800000U,0x3f028283U,0x3d60e0e1U,0x3dc0c0c1U,0x3f800000U,0x3f139394U,0x3e74f4f5U,0x3e2cacadU,0x3f800000U}},
    {"filter/translate:translate", "wrap0", "dd60b0d5bbb58c9463d4c29f8e3feb419655f9dd405b64770be07065ac60d383", "cdb61e7245873910218d0c6af9791cd18c59c228198222665a1f3b1c88216e46", {0x3f028283U,0x3d60e0e1U,0x3dc0c0c1U,0x3edadadbU,0x3e149495U,0x3f6dedeeU,0x3e9e9e9fU,0x3f32b2b3U,0x3e9e9e9fU,0x3f018182U,0x3f5fdfe0U,0x3f5cdcddU}},
    {"filter/translate:translate", "wrap1", "3d564b2d17c9db0fd0d0db02869cc1d331baa1fb5bcfeb18b19d160d254c5ceb", "880eb138435fd6d11cf4f5e27c8b299956ea5287ef84504fa5fc989b030674eb", {0x3e149495U,0x3f6dedeeU,0x3e9e9e9fU,0x3f32b2b3U,0x3f72f2f3U,0x3ec0c0c1U,0x3db0b0b1U,0x3e048485U,0x3e149495U,0x3f6dedeeU,0x3e9e9e9fU,0x3f32b2b3U}},
    {"filter/translate:translate", "wrap2", "57c71ffa3a242b459af2a91d8c7dc93834fd18fe10ce2a9aef7196797ac0fd8a", "5572bbffba8a4359705b4c98b89ff3148e6c98c25f672a9631b22724b88b1192", {0x3f028283U,0x3d60e0e1U,0x3dc0c0c1U,0x3edadadbU,0x3f139394U,0x3e74f4f5U,0x3e2cacadU,0x3e909091U,0x3f139394U,0x3e74f4f5U,0x3e2cacadU,0x3e909091U}},
    {"mixer/patternMix:patternMix", "pattern0", "213a3100c15275764c114f17f1df6584ca8559709e5cbb7bde1703aac9e00fd2", "af4025978e4b82393bd1effbcd50c76ca30f49d9bef390c692d466bee2cd2e23", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern1", "6a88d5832f7c7e867b1e578b7e8ad1c94d3012ad7c253a904a11ba92757b794a", "dca0bf61d0f2da97eae9eb320a41f08e0ebbd7950aa29caadda56a3e3751c704", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f0d952dU,0x3eb48debU,0x3e1f5d5cU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern2", "a8334dab60eabeffc17d8961d4f088f5d9445715fcf4f421d614729a0058f376", "452797aed5e7f7321af7611f9956c3a102e64eff18af272f9049d6eb8af2a035", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern3", "814b79f4be4d66ac5f1cc64bcfe609d5b4479b200da1c6c545046aeaf1349a5b", "7f69f7e87413570590b6b0a0a3e089133f54fab1f54170fae0e149d10ad8f5f8", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern4", "b045d35a387238c609326def9157bf761c436a652a503da18840bf255d8e301e", "4c485721ff0a5b95fdb3ac98fba79b781134f30eefbe1265dfa23d5af863adc7", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern5", "8647a1ca66e9499e089c020749627058526051a8baeac206e060b8d368523e2c", "de0fdcc06eabd77f24f74db2074616e44cb9034fa98a876a424e10d97f826bb9", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern6", "41af219be145d6a27b7c39133d91a59b34a47abe586fb1a9c07737220036b452", "1fe233e421c852824c745f5c5ccc3990bb0551dbe5ba14ad59d58c3728556c80", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f2156e5U,0x3f2d4163U,0x3f0d424fU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern7", "c9cbfb9c8ae7570bebab6ffc165348fa2ea1b3f0f70d5d4069dab244a4f3a8cd", "f228808ec0b5b63148684debce98e6254156c15228b5ad376c2a6fb901aafeff", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern8", "f30f70f8747348af843162054d084464b348cf8239385a0c435ce04263560f5c", "5ebc3fbe6badafe0c77d7abeda38aed7543059da851fc0608de1826aca894dbb", {0x3e2b3f55U,0x3f1a1bffU,0x3f1fccc6U,0x3f7afafbU,0x3f0ceecfU,0x3eaf186cU,0x3e120544U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "invert", "7560bd687b2aa0264b8b6729dcb7d6265fbd488145f2819a390138e16cfede92", "3ca0b85cace99fb54b3b967322354110092ee3fe0231ea1d26046ab71b2b5df3", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "fallback", "dcef139e5081337b2b0f0fda51806028caea30439b72b47fdc1bc277b3dbb387", "8d66b0def717df10f6a07fef8a12af4ef3b963869e04efa7b11950d5ed27563b", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "fullResolutionFallback", "8ad3928394e282b65ef29d89f7202f4b08091146c5708ad84471daed8700c6e4", "91c947bebf55fb99bb0fa5fb2b0094d71184045ce280145ac25e5714bd7c6698", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape0", "ccdd291caef9766a907360bd21e8f82563457ae5d2fd4c46908629e53db2ca5b", "a6817588b18cf21097b92b4534dd2f78eaf36e3cb20a89b481341c18f7a7dcb7", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f3eabc5U,0x3f006330U,0x3e721156U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape1", "d47636df56ef588e885bc074d075f10eb453c82d4b46b7b3a720b1c4cf18e1c2", "073603161a6a84c4c4398103b1055275351ea60ad2ec2aa3e38cce0791e3b5ab", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape2", "1341dae62a1c5856a0cbf4c32f9f86f07bdf14fd240600754a662c986ffd9926", "094fd718fc0faf90c17fc9567820718f699c2d028d5b37494425dc07a40e3fcc", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape3", "0ff005e314f6896264572d8643a731cb93a74fca0321e2deb486bee62507bddd", "88a4c390041dae9e19b869f5f4ab1efa47ec7afeddbf4fd094b8a485531fcc64", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape4", "e65832e83bf6b3bea3f2bf05fea56333b58511548af81aa5f5c7bf84a399b746", "6bd5a7c3311875778c238ac9ef8f558012d042250b16f7de29bd2ac75319ad8c", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape5", "0eae9e8b4ba0dd0c8a0d22df6db100bd91f29bd5212ae8655babf6a37272a2f7", "54614a0eaf345755b27bb7fa0c1e5d7783c8e5f145772d18e2d7badcade18c20", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape6", "4746cb91039cc8aa5e52163e7471c35e486d1cf38902bc9f261d31c456a024fd", "8a6fd852e92c7ac2d72bb09f7d10b849528ef166e805db1a2ce29872a625099e", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f30a4edU,0x3f1d6045U,0x3e6857afU,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape7", "ec8a7000eae5cfdf4fe509434537806381f221e7c96d4a1faf8dd8a0d23c0227", "04aef2a8c2307bf605eba0d6e0bb33accf3bfe60bcd2b1d276feb14499a759b0", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "invert", "fa2812cd1d9359324b438f9492d38783d3b7f38337b5f63e34bef4bab9e920a5", "e03d0d9c441bf6a98cc8204878dbb2757bb1c60ba7d114c9d180267d8eae62e4", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "animated", "6304562c932e79971c3ecfaf838bba47bf78fe3dc105f7c25ec21cba24b3c30a", "259bad1f6bee680a7f144c9da1f799cfe0c096638439890ad20fc1090408d328", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "fallback", "6d8a054edf819f9936b707cacd93c3de7a337ccda6a133f53402b64fbcc0df8e", "40938e0ba396d44cc2b6500c045542ff57fac15481b3c0560dff5e15359c43cb", {0x3de0e0e1U,0x3eb8b8b9U,0x3ea8a8a9U,0x3f7afafbU,0x3f189899U,0x3f088889U,0x3ec0c0c1U,0x3f1e9e9fU,0x3f515152U,0x3eb3b3b4U,0x3e7eff00U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "fullResolutionFallback", "81984d710da8b44362f46ba5be0b389c40e6a22234da1bd9a10cce2dd6c13fee", "4d5d9863f5d1ecaf2205e3db3b625ad5c7863dc43a658f6d9182ded96aee6ce7", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/split:split", "static", "410258ab438b771127022a1cf1cce9a6a6cb125153b91bddd363a8bd4cfac7d8", "8a1196a09d9b5af630415993fb98066ec76288792cace264963cac6b936c9930", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/split:split", "animatedEven", "34c7b544b45b5957287fcb0bad579fc5fd5f521e36ebccc176bdd943652c5e08", "cc65fbc09c50cc74ca53d3e59f35121c069c5852b06ec13dafdc19041461992f", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/split:split", "animatedOdd", "6304562c932e79971c3ecfaf838bba47bf78fe3dc105f7c25ec21cba24b3c30a", "259bad1f6bee680a7f144c9da1f799cfe0c096638439890ad20fc1090408d328", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/split:split", "invertOdd", "dcef139e5081337b2b0f0fda51806028caea30439b72b47fdc1bc277b3dbb387", "8d66b0def717df10f6a07fef8a12af4ef3b963869e04efa7b11950d5ed27563b", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/split:split", "fullResolutionFallback", "c07c651bcbf006819f852bf8d4a3da54e8c30870bf42b0f097780a925b7aec44", "16ec7fb4bfad43541c99cceedbeb1daf0e134de6ca72c0eab7746dacc2efcccc", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f0d2564U,0x3eb0e2eeU,0x3e166610U,0x3f1e9e9fU,0x3f4bc791U,0x3eca97bfU,0x3e7b2806U,0x3f5ddddeU}},
    {"mixer/uvRemap:uvRemap", "map0_channel0_wrap0", "b7e71a5dc6bfeda0631c1be0ee5dfb94bf07d056ecc9f5921c636df61a19d9b7", "23845dad9c0e8a851e035b4bf6bd060041355cbf1ec0685bdf8e8c4e9ecdb616", {0x3f088889U,0x3f3cbcbdU,0x3ed4d4d5U,0x3e8e8e8fU,0x3f088889U,0x3f3cbcbdU,0x3ed4d4d5U,0x3e8e8e8fU,0x3f19999aU,0x3f6bebecU,0x3efafafbU,0x3e088889U}},
    {"mixer/uvRemap:uvRemap", "map0_channel1_wrap1", "515d685ec70b8a9ec91275012474bf628925c9d20fe6842f40020a3b149562f3", "ed1b7eb0eaa84787acb482a8f4cd3fc665bf26bef8bedf5bdd4adfc885e3f3f1", {0x3eb6b6b7U,0x3f55d5d6U,0x3f77f7f8U,0x3ea0a0a1U,0x3e70f0f1U,0x3f4acacbU,0x3f34b4b5U,0x3ecececfU,0x3f088889U,0x3f3cbcbdU,0x3ed4d4d5U,0x3e8e8e8fU}},
    {"mixer/uvRemap:uvRemap", "map0_channel2_wrap2", "baac9f4e5080444ad9bdacbb315d558ab14f87e188ca179bed30fdea66e1a3d6", "afa14f24903e5c8001f363edb1a3ee28ab4f6afa0d0bf63a4c1af5d1435a1d2c", {0x3f38b8b9U,0x3f76f6f7U,0x3f40c0c1U,0x3d30b0b1U,0x3e70f0f1U,0x3f4acacbU,0x3f34b4b5U,0x3ecececfU,0x3f19999aU,0x3f6bebecU,0x3efafafbU,0x3e088889U}},
    {"mixer/uvRemap:uvRemap", "map1_channel0_wrap0", "d1e078c456e5774d18be2d6b9b0ee39f906865e2065dd99fe371c8127872a03d", "e9f79085664a8e718f3cbafa7e5b431c962ea17da5b474370c5ed2f2aae36e5f", {0x3edadadbU,0x3f119192U,0x3f33b3b4U,0x3f028283U,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3eb8b8b9U,0x3ec4c4c5U,0x3f20a0a1U,0x3f27a7a8U}},
    {"mixer/uvRemap:uvRemap", "map1_channel1_wrap1", "39d9bb2c0717cc20cd1964504550350e8e86620d6c34b76fbf03dd5084a55938", "2e560e492ccf4847b7106242a62ebb379d10836fbff435c29e5921c9ed412847", {0x3df0f0f1U,0x3e989899U,0x3dd0d0d1U,0x3f55d5d6U,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f1a9a9bU,0x3ef0f0f1U,0x3e189899U,0x3ef2f2f3U}},
    {"mixer/uvRemap:uvRemap", "map1_channel2_wrap2", "ffd02d6b8a3e7f6f4769c7d9b7de74dd8b4dba2fd4bfd3406eacbc6c3d01f7d7", "f23ab9c97dc35424722b2d5b9eea7d8b9c18111cfc4e0fb935a51204f896b120", {0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U,0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU}},
    {"mixer/uvRemap:uvRemap", "fallbacks", "ffd02d6b8a3e7f6f4769c7d9b7de74dd8b4dba2fd4bfd3406eacbc6c3d01f7d7", "f23ab9c97dc35424722b2d5b9eea7d8b9c18111cfc4e0fb935a51204f896b120", {0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U,0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU}},
    {"synth/modPattern:modPattern", "blend0Anim0", "904ff55a6f8b1fe38b1b6583f18ee418f3eb23cf797a7dc3655e768089df8ee5", "3bacdcce424e877fc88d12cadfe0c9cfa6421651b12a150b2d3580c83375496d", {0x3f076268U,0x3f076268U,0x3f076268U,0x3f800000U,0x3f5719a7U,0x3f5719a7U,0x3f5719a7U,0x3f800000U,0x3cb02ebaU,0x3cb02ebaU,0x3cb02ebaU,0x3f800000U}},
    {"synth/modPattern:modPattern", "blend1Anim1", "69ee857e22e397e6b539158bcd60f3d1f940a008569d5d8fa5842c9269cf2af6", "04d8112f92d355d0eb6a9a09439cb8d208f679918e95452700456e02f2423b4e", {0x3f2d1f44U,0x3f2d1f44U,0x3f2d1f44U,0x3f800000U,0x3f532a37U,0x3f532a37U,0x3f532a37U,0x3f800000U,0x3f2d1f44U,0x3f2d1f44U,0x3f2d1f44U,0x3f800000U}},
    {"synth/modPattern:modPattern", "blend2Anim2", "44d6f6df118c46a647903bb6f047df9f77302abef5b4067ebf2083c33e8a071b", "c8ebfb4e079211cb3aabbdefab4fa5604c8f5314741d7926baa0d53300c8a421", {0x3f258e0dU,0x3f258e0dU,0x3f258e0dU,0x3f800000U,0x3ec64896U,0x3ec64896U,0x3ec64896U,0x3f800000U,0x3ea98ba9U,0x3ea98ba9U,0x3ea98ba9U,0x3f800000U}},
    {"synth/modPattern:modPattern", "blend3", "423fc336468e9c2a851e7c27e593d092dff5619c8906c87f3bc60a59acbdcef5", "de2e3c5329b0b51c6fbb2be34c7562ca03c3c2542d5515e548c62a1022d68e83", {0x3f0973d4U,0x3f028f0cU,0x3ef6bf10U,0x3f800000U,0x3f333334U,0x3f0cccf4U,0x3f17197eU,0x3f800000U,0x3f0fc10cU,0x3f260134U,0x3f4fbf34U,0x3f800000U}},
    {"synth/pattern:pattern", "pattern0", "ffb6e9e731ce29aad4776feff178c40b9d962714ad1d326698aa43ca8ccd4dc9", "6e437bd47e0081c716da2ca80b8a1dab786b070db4005293c59c1ebe9be1480a", {0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern1", "44cb6680c69e14162cf803604e78a5f3748f268550101cea72197da5e02d49c0", "e792a79c71b16dc7622ccc75ceb37ff8ae5c6b55b375d5db062c44e728754320", {0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern2", "a8787a6049ab38853d29b7d9d7bf01af7206e6cc068d620075231020a4b1c251", "aec5160837e274cfdf9fca07d74d09287759ba415d86a13f311919d61a8d00b5", {0x3eaf13faU,0x3f0be221U,0x3edcf0c6U,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern3", "cf9885ae95b0b8d8d6846841434384f0964214ae12a29a2103e9f7082d2883d9", "3586262e902fdc56b201dfa657751d4e5242d00278cd385795ef0dc39cefe91a", {0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern4", "a0df7803e2d2748dec9e01cf0a13818c74939531d9f902bcf1faf5f06422da26", "be607ff90246e5ed1134fa43a064fca16afca154f29fad0df384c9fc5cd0f7a5", {0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern5", "eae1e338c6344e9c496b22e94bfc3f7e62df157d045bfdfa97010ad3cfdd1f82", "ca941d37c1c9dee500cc8054648069489100952097babe19b44f98cd069355b9", {0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3db1d5ecU,0x3f372926U,0x3eaf4d71U,0x3f800000U}},
    {"synth/pattern:pattern", "pattern6", "bcba4688612a3333276bcf32dfd7b4d7b110a0a770552097f7dff17be3d86435", "dde101746a2ba06fa562142f6930d20217543d5d4e44c52a7395ff8df81a9463", {0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern7", "c238e47ba18b83326b390d1c5193a5c8dfc9fb3b0309c1170690fcf6f52a2ab7", "16a65955ca902e6746842cde58580358407e7c8f5ade24b4606a3938759e6c60", {0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern8", "690d7381132717d81bbbbea19fc65ca30b99c382500fcc85e5ddf47f79130d40", "3f60c7d6f4d4febf7e728976c83a04928efdf31001100740b32815764bf3dd8c", {0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern9", "9795fd701bad6f566171ea1b92648632bebe57e6de83829e99e0ee59b6302169", "754b3d34ad15540a99be7501dea41c68ae9d4f0d28e6bba4e928614a53a6c6c0", {0x3dae5584U,0x3f377366U,0x3eaeff24U,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern10", "2bfca80c49c762e21d370eb6a284d36178e4060ce3d4b31141585c1a7b49f25d", "82de84498b417ac654ecce4e3aaad85ff791ceb5e864ccdab35c42f6ecabda3a", {0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern11", "d7889c848f8185abc1702c2c06d501ffdbf6a4e14f3453bd1ce6a8a2e10cea38", "84a1a385c3ddb42077c2d022faf1a1c68ef27bc37c9d1d61e82752ea1ea64c20", {0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3ee797f4U,0x3ef2510aU,0x3ef0afd9U,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "fallback", "e3b382913869fc4757fbf092c7c3c85f6c4db65c2d7e3ececc4e7880d1b66ab9", "86fff5aa9a92ed6f71b6cdcf4b96dfbc39c39bde3c0d66f0fa7ea0cc39fcaeba", {0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
  }};
  constexpr std::array<std::size_t, 3> pixels{0U, 31U, 62U};
  for (const Task12Case& fixture : fixtures) {
    const noisemaker::Surface first = render_task12(fixture);
    const noisemaker::Surface second = render_task12(fixture);
    require_repeat(first, second);
    const std::string name = std::string(fixture.key) + "/" + std::string(fixture.variant);
    const auto floats = little_endian_float_bytes(first);
    if (hex(sha256(floats)) != fixture.float_hash) {
      std::ostringstream detail;
      detail << name << " float oracle hash: " << hex(sha256(floats)) << " probes:";
      for (std::size_t pixel : pixels) for (std::size_t lane = 0; lane < 4U; ++lane)
        detail << ' ' << std::hex << noisemaker::float_bits_to_uint(first.data()[pixel * 4U + lane]);
      throw std::runtime_error(detail.str());
    }
    if (hex(sha256(first.to_rgba8())) != fixture.rgba_hash)
      throw std::runtime_error(name + " rgba oracle hash: " + hex(sha256(first.to_rgba8())));
    for (std::size_t probe = 0; probe < pixels.size(); ++probe)
      for (std::size_t lane = 0; lane < 4U; ++lane)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[pixels[probe] * 4U + lane]) ==
                fixture.probes[probe * 4U + lane]);
  }
}

TEST(typed_task12_each_distinct_signature_and_sampler_fails_closed) {
  struct UniformFixture { std::string_view key; std::string_view variant; std::string_view uniform; noisemaker::glsl::UniformValue wrong; };
  const std::array<UniformFixture, 13> uniforms{{
      {"classicNoisedeck/coalesce:coalesce", "blend0", "blendMode", 1.0f},
      {"classicNoisedeck/composite:composite", "mode0", "inputColor", 1.0f},
      {"filter/hs:hs", "sector0", "rotation", std::int32_t{0}},
      {"filter/repeat:repeat", "wrap0", "wrap", 0.0f},
      {"filter/scale:scale", "wrap0", "scaleX", std::int32_t{1}},
      {"filter/scroll:scroll", "wrap0", "speedX", std::int32_t{1}},
      {"filter/translate:translate", "wrap0", "x", std::int32_t{1}},
      {"mixer/patternMix:patternMix", "pattern0", "patternType", 0.0f},
      {"mixer/shapeMask:shapeMask", "shape0", "speed", 0.0f},
      {"mixer/split:split", "static", "speed", std::int32_t{0}},
      {"mixer/uvRemap:uvRemap", "map0_channel0_wrap0", "mapSource", 0.0f},
      {"synth/modPattern:modPattern", "blend0Anim0", "shape1", 0.0f},
      {"synth/pattern:pattern", "pattern0", "fgColor", 1.0f},
  }};
  struct SamplerFixture { std::string_view key; std::string_view variant; std::string_view sampler; };
  constexpr std::array<SamplerFixture, 17> samplers{{
      {"classicNoisedeck/coalesce:coalesce", "blend0", "inputTex"},
      {"classicNoisedeck/coalesce:coalesce", "blend0", "tex"},
      {"classicNoisedeck/composite:composite", "mode0", "inputTex"},
      {"classicNoisedeck/composite:composite", "mode0", "tex"},
      {"filter/hs:hs", "sector0", "inputTex"},
      {"filter/repeat:repeat", "wrap0", "inputTex"},
      {"filter/scale:scale", "wrap0", "inputTex"},
      {"filter/scroll:scroll", "wrap0", "inputTex"},
      {"filter/translate:translate", "wrap0", "inputTex"},
      {"mixer/patternMix:patternMix", "pattern0", "inputTex"},
      {"mixer/patternMix:patternMix", "pattern0", "tex"},
      {"mixer/shapeMask:shapeMask", "shape0", "inputTex"},
      {"mixer/shapeMask:shapeMask", "shape0", "tex"},
      {"mixer/split:split", "static", "inputTex"},
      {"mixer/split:split", "static", "tex"},
      {"mixer/uvRemap:uvRemap", "map0_channel0_wrap0", "inputTex"},
      {"mixer/uvRemap:uvRemap", "map0_channel0_wrap0", "tex"},
  }};
  const noisemaker::Surface tag1 = source(5U, 3U, 1U);
  const noisemaker::Surface tag23 = source(7U, 2U, 23U);
  const noisemaker::Surface tag37 = source(4U, 6U, 37U);
  const noisemaker::Surface constant_a = constant_surface(5U, 3U, {51U, 153U, 26U, 102U});
  const noisemaker::Surface constant_b = constant_surface(7U, 2U, {230U, 77U, 179U, 204U});
  const noisemaker::Surface hue_negative = constant_surface(3U, 2U, {230U, 10U, 180U, 177U});
  for (const UniformFixture& item : uniforms) {
    const Task12Case fixture{item.key, item.variant, "", "", {}};
    noisemaker::glsl::Bindings missing;
    populate_task12_bindings(missing, fixture, tag1, tag23, tag37, constant_a, constant_b, hue_negative, item.uniform);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, missing), noisemaker::glsl::KernelBindingError);
    noisemaker::glsl::Bindings wrong;
    populate_task12_bindings(wrong, fixture, tag1, tag23, tag37, constant_a, constant_b, hue_negative);
    wrong.set_uniform(std::string(item.uniform), item.wrong);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, wrong), noisemaker::glsl::KernelBindingError);
  }
  for (const SamplerFixture& item : samplers) {
    const Task12Case fixture{item.key, item.variant, "", "", {}};
    noisemaker::glsl::Bindings missing;
    populate_task12_bindings(missing, fixture, tag1, tag23, tag37, constant_a, constant_b, hue_negative, item.sampler);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, missing), noisemaker::glsl::KernelBindingError);
  }
}

struct Task13Case {
  std::string_view key;
  std::string_view variant;
  std::string_view float_hash;
  std::string_view rgba_hash;
  std::array<std::uint32_t, 12> probes;
};

[[nodiscard]] noisemaker::Surface task13_luma_steps() {
  return noisemaker::Surface::from_rgba8(3U, 3U, std::array<std::uint8_t, 36>{
      13U,20U,30U,64U, 128U,128U,128U,128U, 240U,225U,210U,192U,
      30U,40U,50U,70U, 110U,120U,130U,140U, 220U,230U,240U,200U,
      7U,8U,9U,30U, 160U,150U,140U,160U, 250U,245U,235U,220U,
  });
}

void populate_task13_bindings(noisemaker::glsl::Bindings& bindings,
                              const Task13Case& fixture,
                              const noisemaker::Surface& tag1,
                              const noisemaker::Surface& tag23,
                              const noisemaker::Surface& tag37,
                              const noisemaker::Surface& luma,
                              const noisemaker::Surface& stats_range,
                              const noisemaker::Surface& stats_flat,
                              const noisemaker::Surface& overlay,
                              std::string_view skip = {}) {
  const auto uniform = [&](std::string_view name, noisemaker::glsl::UniformValue value) {
    if (name != skip) bindings.set_uniform(std::string(name), std::move(value));
  };
  const auto texture = [&](std::string_view name, const noisemaker::Surface& surface) {
    if (name != skip) bindings.set_texture(std::string(name), surface);
  };
  if (fixture.key == "filter/bloom:brightPass") {
    uniform("tileOffset", noisemaker::glsl::Vec2(-7.0f, 5.0f));
    uniform("fullResolution", noisemaker::glsl::Vec2(17.0f, 13.0f));
    texture("inputTex", luma);
    uniform("threshold", fixture.variant == "below" ? 0.98f :
                         fixture.variant == "above" ? 0.01f : 0.5f);
    uniform("softKnee", fixture.variant == "softKnee" ? 0.21f : 0.01f);
  } else if (fixture.key == "filter/bloom:composite") {
    uniform("tileOffset", noisemaker::glsl::Vec2(-7.0f, 5.0f));
    uniform("fullResolution", noisemaker::glsl::Vec2(17.0f, 13.0f));
    texture("inputTex", tag1); texture("bloomTex", tag23);
    uniform("intensity", fixture.variant == "zeroIntensity" ? 0.0f : 1.7f);
    uniform("tint", fixture.variant == "zeroIntensity"
                        ? noisemaker::glsl::Vec3(0.7f, 0.2f, 0.9f)
                        : noisemaker::glsl::Vec3(0.31f, 0.83f, 0.52f));
  } else if (fixture.key == "filter/fibers:fibersBlend" ||
             fixture.key == "filter/scratches:scratchesBlend") {
    texture("inputTex", tag1); texture("overlayTex", overlay);
    uniform("alpha", fixture.variant == "alpha0" ? 0.0f :
                     fixture.variant == "alpha1" ? 1.0f : 0.53f);
  } else if (fixture.key == "filter/normalize:apply") {
    uniform("tileOffset", noisemaker::glsl::Vec2(-7.0f, 5.0f));
    uniform("fullResolution", noisemaker::glsl::Vec2(17.0f, 13.0f));
    texture("inputTex", tag23);
    texture("statsTex", fixture.variant == "flat" ? stats_flat : stats_range);
  } else if (fixture.key == "filter/pixelSort:luminance") {
    texture("inputTex", fixture.variant == "heterogeneous" ? luma : tag37);
  } else if (fixture.key == "filter/reindex:nmReindexApply") {
    uniform("tileOffset", noisemaker::glsl::Vec2(-7.0f, 5.0f));
    uniform("fullResolution", noisemaker::glsl::Vec2(17.0f, 13.0f));
    uniform("resolution", noisemaker::glsl::Vec2(9.0f, 7.0f));
    texture("inputTex", tag1);
    texture("statsTex", fixture.variant == "rangeFlat" ? stats_flat : stats_range);
    uniform("uDisplacement", fixture.variant == "rangePositive" ? 2.7f :
                             fixture.variant == "rangeFlat" ? -1.9f : 0.0f);
  } else if (fixture.key == "filter/strayHair:strayHairBlend") {
    texture("inputTex", tag1); texture("overlayTex", overlay);
    const bool alternate = fixture.variant == "integerSystemB";
    uniform("alpha", fixture.variant == "alphaOne" ? 1.0f : 0.47f);
    uniform("tileOffset", alternate ? noisemaker::glsl::IVec2(19, -11)
                                     : noisemaker::glsl::IVec2(-7, 5));
    uniform("fullResolution", alternate ? noisemaker::glsl::IVec2(29, 31)
                                         : noisemaker::glsl::IVec2(17, 13));
    uniform("renderScale", alternate ? 1.91f :
                           fixture.variant == "alphaOne" ? 1.0f : 0.73f);
  }
}

[[nodiscard]] noisemaker::Surface render_task13(const Task13Case& fixture,
                                                 std::string_view skip = {}) {
  const noisemaker::Surface tag1 = source(5U, 3U, 1U);
  const noisemaker::Surface tag23 = source(4U, 6U, 23U);
  const noisemaker::Surface tag37 = source(7U, 2U, 37U);
  const noisemaker::Surface luma = task13_luma_steps();
  const noisemaker::Surface stats_range = constant_surface(1U, 1U, {30U, 200U, 71U, 255U});
  const noisemaker::Surface stats_flat = constant_surface(1U, 1U, {99U, 99U, 71U, 255U});
  const noisemaker::Surface overlay = constant_surface(4U, 6U, {238U, 53U, 181U, 179U});
  noisemaker::glsl::Bindings bindings;
  populate_task13_bindings(bindings, fixture, tag1, tag23, tag37, luma,
                           stats_range, stats_flat, overlay, skip);
  return noisemaker::run_pass(noisemaker::generated::bind(fixture.key, bindings),
                              9U, 7U, 0.375f, 7.0f);
}

TEST(typed_task13_all_twenty_one_external_oracles_are_exact_and_repeatable) {
  constexpr std::array<Task13Case, 21> fixtures{{
    {"filter/bloom:brightPass", "softKnee", "637fab112bdd93f09722f42a2bcbe748cb73a1aa104294398fe579cfddf9e7e4", "f37355d9e280dc7b56db4fb66868e9201c904b687333138c62c3ff5f7bda31ab", {0x00000000U,0x00000000U,0x00000000U,0x3e808081U,0x3f70f0f1U,0x3f61e1e2U,0x3f52d2d3U,0x3f40c0c1U,0x3f7afafbU,0x3f75f5f6U,0x3f6bebecU,0x3f5cdcddU}},
    {"filter/bloom:brightPass", "below", "39db1c2790da52b4ec7590014d7f438a3a2b4d4cc6ca5f6ed6c38fb60de27192", "17b3576fb2405e4d1dee78a343a9d8e473409056c8c1cd0fcb38b9659df20a6a", {0x00000000U,0x00000000U,0x00000000U,0x3e808081U,0x00000000U,0x00000000U,0x00000000U,0x3f40c0c1U,0x00000000U,0x00000000U,0x00000000U,0x3f5cdcddU}},
    {"filter/bloom:brightPass", "above", "e817cda4b3759b575fdb3778177564544800f2df625f2129ef3709001c6702ed", "48b6681702181716a45c4a1e76d1c0992208d454fb8825ebe107ac8adee4ccdb", {0x3d50d0d1U,0x3da0a0a1U,0x3df0f0f1U,0x3e808081U,0x3f70f0f1U,0x3f61e1e2U,0x3f52d2d3U,0x3f40c0c1U,0x3f7afafbU,0x3f75f5f6U,0x3f6bebecU,0x3f5cdcddU}},
    {"filter/bloom:composite", "zeroIntensity", "82dce1fda9a7c8bf9e8c8ac5e3e92804ed3d75a68246f705f9f37ed379526e66", "97b2a11438e374e306befe0d6d844374c576f5e68fd5723d282b7f13a92747ab", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
    {"filter/bloom:composite", "tintedHDR", "88aed7c00ff073094ebb5dd35b7007448ad97e97dabd6310e566cf6fd20711aa", "60d5ab2cf84570f303bfe8e7dc5d80f81ed1bc21fc4eff0ccc3506fcb650ad5b", {0x3e0f3412U,0x3f78ad29U,0x3f15e8dbU,0x3f7afafbU,0x3f637a86U,0x3edc3b77U,0x3f12dea5U,0x3f1e9e9fU,0x3f904c13U,0x3fca1ba5U,0x3f6b9ab5U,0x3ea8a8a9U}},
    {"filter/fibers:fibersBlend", "alpha0", "82dce1fda9a7c8bf9e8c8ac5e3e92804ed3d75a68246f705f9f37ed379526e66", "97b2a11438e374e306befe0d6d844374c576f5e68fd5723d282b7f13a92747ab", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
    {"filter/fibers:fibersBlend", "alpha0p53", "ab16d60f5002784bf79c7ff1e69e8c4b88189962b491acdd8e1e6eda71f98022", "a914338ee1630fe92a0530dbd76ea90741b2fa9431f684ccaa1909af64be8996", {0x3ec22d18U,0x3e184f8cU,0x3e900843U,0x3f7afafbU,0x3f2f42b5U,0x3e83a1f4U,0x3e9f2995U,0x3f1e9e9fU,0x3f44b1eaU,0x3efa26f8U,0x3ecf131aU,0x3ea8a8a9U}},
    {"filter/fibers:fibersBlend", "alpha1", "2200817335871e52518207a88e870a097b77916b44cea500c8b67f42fdedda6a", "fdc4b4d6db28e6a43aab5821dae93bc181276e39bd129de2f409f56a725f0e7e", {0x3f2b9c8eU,0x3e381b7fU,0x3f01a5caU,0x3f7afafbU,0x3f50b69dU,0x3e6cc49dU,0x3f053cf5U,0x3f1e9e9fU,0x3f5ae2ebU,0x3eaea297U,0x3f109ba7U,0x3ea8a8a9U}},
    {"filter/normalize:apply", "range", "656715b86d5874a48375ee902a7ae03645763d0d7fcfffa6052a12bbd8a200c2", "81c9865d59ee655b83ae4731bbef4176ed494ec0e2b80f664471af99787ed27d", {0x3d9c9c9dU,0x3f3c3c3dU,0x3f454546U,0x3f0c8c8dU,0x3f52d2d3U,0xbcc0c0c0U,0x3f2babacU,0x3f7dfdfeU,0x3f8fcfd0U,0x3f4e4e4fU,0x3f80c0c1U,0x3f0e8e8fU}},
    {"filter/normalize:apply", "flat", "02bf5200e916b1d1f11dacdfe211ada7f4fd4eb9dbdb002e5dc27e0595c202d6", "7b6336be201d130d239718d7929093ddb4208cb7da2c57abd59fb0882fea05ad", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f0c8c8dU,0x3f2aaaabU,0x3dd0d0d1U,0x3f109091U,0x3f7dfdfeU,0x3f5ddddeU,0x3f27a7a8U,0x3f49c9caU,0x3f0e8e8fU}},
    {"filter/pixelSort:luminance", "heterogeneous", "e27aaa19da93167411e82c57df61c1d2b88fc1e754653b57a399189410b030b1", "a812ed4c6e1a3b2ff090835d34580b04ff93e0cd63acc0fa2b1b20861d2464f7", {0x3e41f0bdU,0x00000000U,0x00000000U,0x3f800000U,0x3f6aee6dU,0x40000000U,0x00000000U,0x3f800000U,0x3f78a56eU,0x40800000U,0x00000000U,0x3f800000U}},
    {"filter/pixelSort:luminance", "nonSquareClamp", "f00e254739f44d6444f874d463b499b862690e30fa6aa8de013c43139b4feb7a", "4fe3ba39772c0af69f6a1a2e5c241d7f477452a97d557be28077783653e8e07d", {0x3f177e79U,0x00000000U,0x00000000U,0x3f800000U,0x3eed6c8cU,0x3f2aaaabU,0x00000000U,0x3f800000U,0x3f38f5f2U,0x3faaaaabU,0x00000000U,0x3f800000U}},
    {"filter/reindex:nmReindexApply", "rangePositive", "4052d2f2b1baa048e90f1d52ad7fcad9261d66212a3ace983487d55d6f107f32", "dbfe551db48ea34406dcedb4f581f54ececf6de80b1d63a79aaa140c75ec6d5d", {0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U}},
    {"filter/reindex:nmReindexApply", "rangeFlat", "73160445a22bebf77b4954a8d59ea2ded6e2f1f84fb788ff4edb98d82073e7ab", "9b50758c016c30bce226b179d0f2b37c5a4fa88c3fb90e31297d1615e7eb38b6", {0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U}},
    {"filter/reindex:nmReindexApply", "zeroDisplacement", "dc13348216c58428ff1e89861dc3305d755c040b5ed4cf360941a72813456324", "56919a95415c7c3bc13d35a41a5ce8d606db8040170f2b03ae38c0457e5e9717", {0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U}},
    {"filter/scratches:scratchesBlend", "alpha0", "82dce1fda9a7c8bf9e8c8ac5e3e92804ed3d75a68246f705f9f37ed379526e66", "97b2a11438e374e306befe0d6d844374c576f5e68fd5723d282b7f13a92747ab", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
    {"filter/scratches:scratchesBlend", "alpha0p53", "2fc7f66e4d5f3d96f46fe8fe756ff4735ba8795e7864d5b03c1102fa099302ed", "f1fd830a768fa42239b1aa0e17df1db838eff7271f24c8b3eccadbe87cc30598", {0x3ebe7becU,0x3ebe7becU,0x3ebe7becU,0x3f7afafbU,0x3f09898aU,0x3ebe7becU,0x3ebe7becU,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3ebe7becU,0x3ea8a8a9U}},
    {"filter/scratches:scratchesBlend", "alpha1", "8fc2328d92e39ae882af3762ee938ee80665cd53c02e90548f5f4667c5239c2c", "afc55a6e9e676e7fd9f7a241b72132d6d678841f9326c14d9607615cdf9c1151", {0x3f33b3b4U,0x3f33b3b4U,0x3f33b3b4U,0x3f7afafbU,0x3f33b3b4U,0x3f33b3b4U,0x3f33b3b4U,0x3f1e9e9fU,0x3f33b3b4U,0x3f33b3b4U,0x3f33b3b4U,0x3ea8a8a9U}},
    {"filter/strayHair:strayHairBlend", "integerSystemA", "e3378dd37d7bc44eb5d52843d3d0f60a1042343b6c1682484e61a963031d3254", "f9d6f8ee67e27cbe4b8f2867f30df7ccb6fca490a0d6583b5a961ec3d0def2c3", {0x3eaf261dU,0x3e144068U,0x3e81515fU,0x3f7afafbU,0x3f2afd72U,0x3e8552eeU,0x3e91767bU,0x3f1e9e9fU,0x3f41dcaeU,0x3f01e577U,0x3ec496a6U,0x3ea8a8a9U}},
    {"filter/strayHair:strayHairBlend", "integerSystemB", "e3378dd37d7bc44eb5d52843d3d0f60a1042343b6c1682484e61a963031d3254", "f9d6f8ee67e27cbe4b8f2867f30df7ccb6fca490a0d6583b5a961ec3d0def2c3", {0x3eaf261dU,0x3e144068U,0x3e81515fU,0x3f7afafbU,0x3f2afd72U,0x3e8552eeU,0x3e91767bU,0x3f1e9e9fU,0x3f41dcaeU,0x3f01e577U,0x3ec496a6U,0x3ea8a8a9U}},
    {"filter/strayHair:strayHairBlend", "alphaOne", "2200817335871e52518207a88e870a097b77916b44cea500c8b67f42fdedda6a", "fdc4b4d6db28e6a43aab5821dae93bc181276e39bd129de2f409f56a725f0e7e", {0x3f2b9c8eU,0x3e381b7fU,0x3f01a5caU,0x3f7afafbU,0x3f50b69dU,0x3e6cc49dU,0x3f053cf5U,0x3f1e9e9fU,0x3f5ae2ebU,0x3eaea297U,0x3f109ba7U,0x3ea8a8a9U}},
  }};
  constexpr std::array<std::size_t, 3> pixels{0U, 31U, 62U};
  for (const Task13Case& fixture : fixtures) {
    const noisemaker::Surface first = render_task13(fixture);
    const noisemaker::Surface second = render_task13(fixture);
    require_repeat(first, second);
    const std::string name = std::string(fixture.key) + "/" + std::string(fixture.variant);
    const auto floats = little_endian_float_bytes(first);
    if (hex(sha256(floats)) != fixture.float_hash) {
      std::ostringstream detail;
      detail << name << " float oracle hash: " << hex(sha256(floats)) << " probes:";
      for (std::size_t pixel : pixels) for (std::size_t lane = 0; lane < 4U; ++lane)
        detail << ' ' << std::hex << noisemaker::float_bits_to_uint(first.data()[pixel * 4U + lane]);
      throw std::runtime_error(detail.str());
    }
    if (hex(sha256(first.to_rgba8())) != fixture.rgba_hash)
      throw std::runtime_error(name + " rgba oracle hash: " + hex(sha256(first.to_rgba8())));
    for (std::size_t probe = 0; probe < pixels.size(); ++probe)
      for (std::size_t lane = 0; lane < 4U; ++lane)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[pixels[probe] * 4U + lane]) ==
                fixture.probes[probe * 4U + lane]);
  }
}

TEST(typed_task13_each_required_binding_fails_closed) {
  struct UniformFixture {
    std::string_view key;
    std::string_view variant;
    std::string_view uniform;
    noisemaker::glsl::UniformValue wrong;
  };
  const std::array<UniformFixture, 20> uniforms{{
      {"filter/bloom:brightPass", "softKnee", "tileOffset", 1.0f},
      {"filter/bloom:brightPass", "softKnee", "fullResolution", 1.0f},
      {"filter/bloom:brightPass", "softKnee", "threshold", std::int32_t{1}},
      {"filter/bloom:brightPass", "softKnee", "softKnee", std::int32_t{1}},
      {"filter/bloom:composite", "tintedHDR", "tileOffset", 1.0f},
      {"filter/bloom:composite", "tintedHDR", "fullResolution", 1.0f},
      {"filter/bloom:composite", "tintedHDR", "intensity", std::int32_t{1}},
      {"filter/bloom:composite", "tintedHDR", "tint", 1.0f},
      {"filter/fibers:fibersBlend", "alpha0p53", "alpha", std::int32_t{1}},
      {"filter/normalize:apply", "range", "tileOffset", 1.0f},
      {"filter/normalize:apply", "range", "fullResolution", 1.0f},
      {"filter/reindex:nmReindexApply", "rangePositive", "tileOffset", 1.0f},
      {"filter/reindex:nmReindexApply", "rangePositive", "fullResolution", 1.0f},
      {"filter/reindex:nmReindexApply", "rangePositive", "resolution", 1.0f},
      {"filter/reindex:nmReindexApply", "rangePositive", "uDisplacement", std::int32_t{1}},
      {"filter/scratches:scratchesBlend", "alpha0p53", "alpha", std::int32_t{1}},
      {"filter/strayHair:strayHairBlend", "integerSystemA", "alpha", std::int32_t{1}},
      {"filter/strayHair:strayHairBlend", "integerSystemA", "tileOffset", noisemaker::glsl::Vec2(0.0f)},
      {"filter/strayHair:strayHairBlend", "integerSystemA", "fullResolution", noisemaker::glsl::Vec2(1.0f)},
      {"filter/strayHair:strayHairBlend", "integerSystemA", "renderScale", std::int32_t{1}},
  }};
  struct SamplerFixture { std::string_view key; std::string_view variant; std::string_view sampler; };
  constexpr std::array<SamplerFixture, 14> samplers{{
      {"filter/bloom:brightPass", "softKnee", "inputTex"},
      {"filter/bloom:composite", "tintedHDR", "inputTex"},
      {"filter/bloom:composite", "tintedHDR", "bloomTex"},
      {"filter/fibers:fibersBlend", "alpha0p53", "inputTex"},
      {"filter/fibers:fibersBlend", "alpha0p53", "overlayTex"},
      {"filter/normalize:apply", "range", "inputTex"},
      {"filter/normalize:apply", "range", "statsTex"},
      {"filter/pixelSort:luminance", "heterogeneous", "inputTex"},
      {"filter/reindex:nmReindexApply", "rangePositive", "inputTex"},
      {"filter/reindex:nmReindexApply", "rangePositive", "statsTex"},
      {"filter/scratches:scratchesBlend", "alpha0p53", "inputTex"},
      {"filter/scratches:scratchesBlend", "alpha0p53", "overlayTex"},
      {"filter/strayHair:strayHairBlend", "integerSystemA", "inputTex"},
      {"filter/strayHair:strayHairBlend", "integerSystemA", "overlayTex"},
  }};
  const noisemaker::Surface tag1 = source(5U, 3U, 1U);
  const noisemaker::Surface tag23 = source(4U, 6U, 23U);
  const noisemaker::Surface tag37 = source(7U, 2U, 37U);
  const noisemaker::Surface luma = task13_luma_steps();
  const noisemaker::Surface stats_range = constant_surface(1U, 1U, {30U, 200U, 71U, 255U});
  const noisemaker::Surface stats_flat = constant_surface(1U, 1U, {99U, 99U, 71U, 255U});
  const noisemaker::Surface overlay = constant_surface(4U, 6U, {238U, 53U, 181U, 179U});
  for (const UniformFixture& item : uniforms) {
    const Task13Case fixture{item.key, item.variant, "", "", {}};
    noisemaker::glsl::Bindings missing;
    populate_task13_bindings(missing, fixture, tag1, tag23, tag37, luma,
                             stats_range, stats_flat, overlay, item.uniform);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, missing), noisemaker::glsl::KernelBindingError);
    noisemaker::glsl::Bindings wrong;
    populate_task13_bindings(wrong, fixture, tag1, tag23, tag37, luma,
                             stats_range, stats_flat, overlay);
    wrong.set_uniform(std::string(item.uniform), item.wrong);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, wrong), noisemaker::glsl::KernelBindingError);
  }
  for (const SamplerFixture& item : samplers) {
    const Task13Case fixture{item.key, item.variant, "", "", {}};
    noisemaker::glsl::Bindings missing;
    populate_task13_bindings(missing, fixture, tag1, tag23, tag37, luma,
                             stats_range, stats_flat, overlay, item.sampler);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, missing), noisemaker::glsl::KernelBindingError);
  }
}


struct Task14Case {
  std::string_view key;
  std::string_view variant;
  std::string_view float_hash;
  std::string_view rgba_hash;
  std::array<std::uint32_t, 12> probes;
  std::array<float, 5> values;
  std::array<std::int32_t, 3> integers;
  bool flag;
  noisemaker::glsl::Vec2 tile_offset;
  noisemaker::glsl::Vec2 full_resolution;
  float time;
  std::uint32_t input_tag;
  std::uint32_t original_tag;
};

[[nodiscard]] std::array<Task14Case, 30> task14_cases() {
  return {{
      {"filter/pixelSort:prepare", "mirror_light", "0a8ceedcfccedaf760c957e4afa9bf479176af4bd7b7c6515a3a71954ce8718f", "c569eb38d5413cd4bc646aa5521ebf59665fe0de5353fb4aa0f2dcd17b768d13",
       {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3df0f0f1U,0x3e989899U,0x3dd0d0d1U,0x3f55d5d6U,0x3e9c9c9dU,0x3f068687U,0x3ee0e0e1U,0x3f19999aU},
       {-135.0f,0.0f,0.0f,0.0f,0.0f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(-7.0f, 5.0f), noisemaker::glsl::Vec2(17.0f, 13.0f), 0.375f, 1U, 0U},
      {"filter/pixelSort:prepare", "repeat_dark", "131e7dfef2a898a9f85031fcfff189289b1e01ea378ce866e71ea66ffc344e01", "7f209b7bfe08e1d0720fe5a61c6dffc4d6a5ff989dad1e8c11e92a6118c17150",
       {0x3f24a4a4U,0x3e28a8a8U,0x3d008080U,0x3ea0a0a1U,0x3e828282U,0x3ec6c6c6U,0x3ef2f2f2U,0x3f25a5a6U,0x3e888888U,0x3f36b6b6U,0x3eb8b8b8U,0x3f58d8d9U},
       {90.0f,1.0f,0.0f,0.0f,0.0f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, true,
       noisemaker::glsl::Vec2(11.0f, -4.0f), noisemaker::glsl::Vec2(29.0f, 17.0f), 0.375f, 23U, 0U},
      {"filter/pixelSort:prepare", "clamp_light", "b76c475bfa0e291e62f6b421b5285943916ab351f86d36908e332736085c8a25", "96fabba10b774bdc8a138284fa5d09dd26a4c7f327d1bf8d75d85cacd85563aa",
       {0x3f2cacadU,0x3f22a2a3U,0x3f28a8a9U,0x3f179798U,0x3e40c0c1U,0x3eececedU,0x3f1c9c9dU,0x3f73f3f4U,0x3f61e1e2U,0x3e44c4c5U,0x3c40c0c1U,0x3e8c8c8dU},
       {180.0f,2.0f,0.0f,0.0f,0.0f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(-13.0f, 9.0f), noisemaker::glsl::Vec2(23.0f, 19.0f), 0.375f, 37U, 0U},
      {"filter/pixelSort:prepare", "fallback_dark", "4b69f901c518105ff2d6798ed48047c67d41d992da41f2e79657fe480b96eac2", "b6c8779d542d7583f138d6e2ed0f9b90b68106ec2f3bab188f167fa69711ff27",
       {0x3d808080U,0x3f68e8e9U,0x3cc0c0c0U,0x3f48c8c9U,0x3f5ddddeU,0x3eb6b6b6U,0x3f4dcdceU,0x3eb2b2b3U,0x3f4ccccdU,0x3e30b0b0U,0x3f3ababaU,0x3e50d0d1U},
       {37.0f,9.0f,0.0f,0.0f,0.0f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, true,
       noisemaker::glsl::Vec2(5.0f, -11.0f), noisemaker::glsl::Vec2(31.0f, 13.0f), 0.375f, 53U, 0U},
      {"filter/pixelSort:finalize", "mirror_alpha0_light", "1b0593e51b28ab476dbf6a18b9604ddcf4c66a9195494217e159c8a3328a6a12", "3851d1e562a4c12e3488f64cfddda54a00e4d931fad15375531b3fd20d5f5f9f",
       {0x3edadadbU,0x3f119192U,0x3f33b3b4U,0x3f0c8c8dU,0x3eb8b8b9U,0x3ec4c4c5U,0x3f20a0a1U,0x3da0a0a1U,0x3e969697U,0x3e4ccccdU,0x3f0d8d8eU,0x3f0e8e8fU},
       {-135.0f,0.0f,0.0f,0.0f,0.0f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(-7.0f, 5.0f), noisemaker::glsl::Vec2(17.0f, 13.0f), 0.375f, 1U, 23U},
      {"filter/pixelSort:finalize", "repeat_alpha073_dark", "dc1826ca488bc3026577512a182f65dbccf1602916c05b828ed14dcbfe963b34", "a2f6d509c9aea159f0bc1a903d8ad0e8c9b3439438c4dca59da1487257e66799",
       {0x3f2dadaeU,0x3ed20f80U,0x3e8ea31eU,0x3e8c8c8dU,0x3e949494U,0x3f0136f9U,0x3f5a9fbeU,0x3b808081U,0x3e9a9a9cU,0x3f3bd801U,0x3f403daeU,0x3f179798U},
       {90.0f,1.0f,0.73000001907348633f,0.0f,0.0f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, true,
       noisemaker::glsl::Vec2(11.0f, -4.0f), noisemaker::glsl::Vec2(29.0f, 17.0f), 0.375f, 23U, 37U},
      {"filter/pixelSort:finalize", "clamp_alpha1_light", "24a09c07a4148595689bcf43c3902d74a2d2a9f014a8657cdf446837f2a4431b", "d152a2ba82e1c22dc6579791c346a22eacb26074a02956f155e519071790b4ed",
       {0x3f31b1b2U,0x3f22a2a3U,0x3f28a8a9U,0x3f76f6f7U,0x3f72f2f3U,0x3eececedU,0x3f5cdcddU,0x3f159596U,0x3f61e1e2U,0x3f53d3d4U,0x3e8a8a8bU,0x3e50d0d1U},
       {180.0f,2.0f,1.0f,0.0f,0.0f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(-13.0f, 9.0f), noisemaker::glsl::Vec2(23.0f, 19.0f), 0.375f, 37U, 53U},
      {"filter/pixelSort:finalize", "fallback_alpha027_dark", "ed8222b9f64a1583c92e0c53cdce173de882a96605c4c07c3f699027f2c5fb0d", "ed32b1962235fc45c5e990228d0894fef4eb4eee6de16bc0f45f512d903cd139",
       {0x3f31b1b2U,0x3b808080U,0x3ee6e6e8U,0x3f7afafbU,0x3f53d142U,0x3db8b8b8U,0x3f663fdaU,0x3f27a7a8U,0x3f693b27U,0x3db8b8b8U,0x3f4a5492U,0x3ea8a8a9U},
       {37.0f,9.0f,0.27000001072883606f,0.0f,0.0f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, true,
       noisemaker::glsl::Vec2(5.0f, -11.0f), noisemaker::glsl::Vec2(31.0f, 13.0f), 0.375f, 53U, 1U},
      {"filter/skew:skew", "clamp_negative_tile", "610b8ab6df51313714ba5612f5e8e2d040f4da2433e10bddc20f7eaa7ac7bda2", "756cc64824bb72e78e353e99ad88384594eec4f0b9cd3c02177b73848a01a45e",
       {0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U},
       {-0.37000000476837158f,-137.0f,0.0f,0.73000001907348633f,0.0f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(-7.0f, 5.0f), noisemaker::glsl::Vec2(17.0f, 13.0f), 0.375f, 1U, 0U},
      {"filter/skew:skew", "mirror_clamped_skew", "9cdb125d385482514889fa80be62770d785260b5006860270ffc069c9c670609", "c4297edeb35c615ed5270c22b4e4b3b0e504a55c4b29e788f5d1effc7982b0ff",
       {0x3ed2d2d3U,0x3f31b1b2U,0x3e1c9c9dU,0x3ebcbcbdU,0x3f2aaaabU,0x3dd0d0d1U,0x3f109091U,0x3f7dfdfeU,0x3f1f9fa0U,0x3f119192U,0x3e868687U,0x3f3cbcbdU},
       {100.0f,0.0f,1.0f,1.9099999666213989f,0.0f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(11.0f, -4.0f), noisemaker::glsl::Vec2(29.0f, 17.0f), 0.375f, 23U, 0U},
      {"filter/skew:skew", "repeat_positive", "1505e465f13ddc9afeef8fe9e8011b0190b59ca281d5d281988b080cb77dfcf4", "e97d9b0e849345ab1281c33308de4c81e4ed42609716f4c876bffc25a5126787",
       {0x3df8f8f9U,0x3e8e8e8fU,0x3f09898aU,0x3dc0c0c1U,0x3f1b9b9cU,0x3ee6e6e7U,0x3f159596U,0x3f3cbcbdU,0x3df8f8f9U,0x3e8e8e8fU,0x3f09898aU,0x3dc0c0c1U},
       {0.70999997854232788f,123.0f,2.0f,1.0f,0.0f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(-13.0f, 9.0f), noisemaker::glsl::Vec2(23.0f, 19.0f), 0.375f, 37U, 0U},
      {"filter/skew:skew", "fallback_repeat", "c3f866c545e8a92f0facfb07f3f39546b06a486951f6d6fdfce7b11579ffdaab", "e15c48c14eff1ddf40713be881260a1aa238cb9e6580498debd36c6bd1c586e5",
       {0x3f61e1e2U,0x3e6cecedU,0x3f49c9caU,0x3f3ababbU,0x3c40c0c1U,0x3f19999aU,0x3f6feff0U,0x3ee0e0e1U,0x3f6feff0U,0x3db8b8b9U,0x3f79f9faU,0x3f48c8c9U},
       {-100.0f,179.0f,-4.0f,0.5f,0.0f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(5.0f, -11.0f), noisemaker::glsl::Vec2(31.0f, 13.0f), 0.375f, 53U, 0U},
      {"filter/tetraCosine:tetraCosine", "rgb_static_alpha0", "82dce1fda9a7c8bf9e8c8ac5e3e92804ed3d75a68246f705f9f37ed379526e66", "97b2a11438e374e306befe0d6d844374c576f5e68fd5723d282b7f13a92747ab",
       {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U},
       {0.0f,0.0f,0.0f,0.0f,0.0f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(-7.0f, 5.0f), noisemaker::glsl::Vec2(17.0f, 13.0f), 0.375f, 1U, 0U},
      {"filter/tetraCosine:tetraCosine", "hsv_backward", "ea22015f2ef3c53edaddf5fa6a41a1e69b824dcea8aef61efa851fcbc633622d", "7cd16bb3a3519e49bdb849692905d104697ae4243da91fd0c2de6e622c389652",
       {0x3eda8cd7U,0x3f2f9d3dU,0x3f332b09U,0x3f0c8c8dU,0x3f1ba2bcU,0x3dd287d8U,0x3ecba875U,0x3f7dfdfeU,0x3f6bdc80U,0x3f4be05bU,0x3f6003dbU,0x3f0e8e8fU},
       {0.40999999642372131f,0.0f,0.0f,0.0f,0.0f}, {std::int32_t{1},std::int32_t{-1},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(11.0f, -4.0f), noisemaker::glsl::Vec2(29.0f, 17.0f), 0.875f, 23U, 0U},
      {"filter/tetraCosine:tetraCosine", "oklab_forward_alpha1", "2416059647cfb69c340dcb4c869f26a3f6dd92dc2164b4902691c572048b308a", "997b17922a9430c278738815712c5397179782a4622c758689f60c8cd665ef4d",
       {0x3e07abccU,0x3e404bf0U,0x00000000U,0x3e8c8c8dU,0x00000000U,0x3bffdbd5U,0x00000000U,0x3f6aeaebU,0x00000000U,0x3e6ae0deU,0x00000000U,0x3f179798U},
       {1.0f,0.0f,0.0f,0.0f,0.0f}, {std::int32_t{2},std::int32_t{1},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(-13.0f, 9.0f), noisemaker::glsl::Vec2(23.0f, 19.0f), 0.625f, 37U, 0U},
      {"filter/tetraCosine:tetraCosine", "oklch_static", "0754705dd4912ee71d140199748e39366c780cb1ee0d7f83ee4a811d7009d943", "37d73498ed162e762ad727491cf4e4c71b71ebf1082e6a18c74c100f97f94642",
       {0x3e1c5ef0U,0x3f47e69eU,0x3f611447U,0x3f76f6f7U,0x00000000U,0x3d775dc7U,0x3d5caab4U,0x3f23a3a4U,0x3ea0c83dU,0x3ee77551U,0x3ea8bbb5U,0x3e50d0d1U},
       {0.77999997138977051f,0.0f,0.0f,0.0f,0.0f}, {std::int32_t{3},std::int32_t{0},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(5.0f, -11.0f), noisemaker::glsl::Vec2(31.0f, 13.0f), 1.125f, 53U, 0U},
      {"filter/tetraCosine:tetraCosine", "fallback_rgb", "b8e795e4f93a59e0bc297f86b627f222196c82e3510249ae45815d4c1e518400", "8d69403bfa852d5539953cee28bec937ba8e8ec7f76ab34eaae4ceebc4232550",
       {0x3d20c9c0U,0x3db3572eU,0x3e0b8e59U,0x3f7afafbU,0x3f08f3ccU,0x3e6564edU,0x3e8295a7U,0x3f1e9e9fU,0x3f35966aU,0x3f2e7b90U,0x3ec70004U,0x3ea8a8a9U},
       {0.23000000417232513f,0.0f,0.0f,0.0f,0.0f}, {std::int32_t{9},std::int32_t{9},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(-17.0f, -3.0f), noisemaker::glsl::Vec2(37.0f, 21.0f), 1.75f, 1U, 0U},
      {"filter/tile:tile", "mirrorXY_aspect", "9bb196ff6cc417b80b7ab5ee02dc5c60e7188c2f139896d916e952f7eea838f4", "736b056673923560ba11232e57395da0d319ab941f3e03609ab11e32d92b27c8",
       {0x3f1a9a9bU,0x3ef0f0f1U,0x3e189899U,0x3f800000U,0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f800000U,0x3f1a9a9bU,0x3ef0f0f1U,0x3e189899U,0x3f800000U},
       {0.37000000476837158f,-0.61000001430511475f,0.43999999761581421f,17.0f,2.2999999523162842f}, {std::int32_t{0},std::int32_t{0},std::int32_t{0}}, true,
       noisemaker::glsl::Vec2(-7.0f, 5.0f), noisemaker::glsl::Vec2(17.0f, 13.0f), 0.375f, 1U, 0U},
      {"filter/tile:tile", "rotate2_noaspect", "bd86f4ab25bba960358076ef72d67f917536da4be08158fb0c947976c202b532", "c6981da919b1299640540d23a14068684ce343914fd50f6f18ee27ee3bebc90f",
       {0x3f19999aU,0x3f6bebecU,0x3efafafbU,0x3f800000U,0x3ef4f4f5U,0x3f60e0e1U,0x3e68e8e9U,0x3f800000U,0x3f088889U,0x3f3cbcbdU,0x3ed4d4d5U,0x3f800000U},
       {1.7100000381469727f,0.82999998331069946f,-0.28999999165534973f,113.0f,4.6999998092651367f}, {std::int32_t{1},std::int32_t{0},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(11.0f, -4.0f), noisemaker::glsl::Vec2(29.0f, 17.0f), 0.375f, 23U, 0U},
      {"filter/tile:tile", "rotate4_aspect", "bc56b006a97b321546ec6c0782df8456856b6fc737d486e5484d04c9eb52181c", "53394df61061b45f08fb139fbaa58c83aad888dc3cd5ee1e40388f7d2bdb7daa",
       {0x3ef8f8f9U,0x3ed0d0d1U,0x3ea4a4a5U,0x3f800000U,0x3e78f8f9U,0x3ea4a4a5U,0x3f4ccccdU,0x3f800000U,0x3ef8f8f9U,0x3ed0d0d1U,0x3ea4a4a5U,0x3f800000U},
       {0.92000001668930054f,-0.14000000059604645f,0.67000001668930054f,251.0f,6.0999999046325684f}, {std::int32_t{2},std::int32_t{0},std::int32_t{0}}, true,
       noisemaker::glsl::Vec2(-13.0f, 9.0f), noisemaker::glsl::Vec2(23.0f, 19.0f), 0.375f, 37U, 0U},
      {"filter/tile:tile", "hex_rotate6_noaspect", "160e93744880b320c3765a9b1b22c1749a7e7bc66db5ff78ed772950a5488976", "7a368244394c0fcc060b3802a4bad4b3caf228de7d545fb9feeb316ef9ff6459",
       {0x3f72f2f3U,0x3ed4d4d5U,0x3f5cdcddU,0x3f800000U,0x3d888889U,0x3eeaeaebU,0x3df8f8f9U,0x3f800000U,0x3f72f2f3U,0x3ed4d4d5U,0x3f5cdcddU,0x3f800000U},
       {2.2699999809265137f,0.37999999523162842f,-0.73000001907348633f,329.0f,3.4000000953674316f}, {std::int32_t{3},std::int32_t{0},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(5.0f, -11.0f), noisemaker::glsl::Vec2(31.0f, 13.0f), 0.375f, 53U, 0U},
      {"filter/tile:tile", "fallback_rotate4", "2c86df0be7b67a91f291a4559fd8d79f727b69da38faad5d4b527f9321541af6", "44a972f60fcb01e9691918fa792a1467b83391374c62f21d5e8867f1072806e0",
       {0x3f1a9a9bU,0x3ef0f0f1U,0x3e189899U,0x3f800000U,0x3f1a9a9bU,0x3ef0f0f1U,0x3e189899U,0x3f800000U,0x3f1a9a9bU,0x3ef0f0f1U,0x3e189899U,0x3f800000U},
       {0.57999998331069946f,0.9100000262260437f,0.11999999731779099f,71.0f,8.6000003814697266f}, {std::int32_t{9},std::int32_t{0},std::int32_t{0}}, true,
       noisemaker::glsl::Vec2(-17.0f, -3.0f), noisemaker::glsl::Vec2(37.0f, 21.0f), 0.375f, 1U, 0U},
      {"synth/osc2d:osc2d", "sine", "3d0bfb246f96bd368c74b278ac196caf115ba13ac604a256487992ada8b4fa03", "4c9320618debef0e689ff75c2c94d006987b22e71073698db7c02fc6292b261d",
       {0x3f7f5834U,0x3f7f5834U,0x3f7f5834U,0x3f800000U,0x3f692e4bU,0x3f692e4bU,0x3f692e4bU,0x3f800000U,0x3f361fa6U,0x3f361fa6U,0x3f361fa6U,0x3f800000U},
       {0.0f,-137.0f,0.0f,0.0f,0.0f}, {std::int32_t{0},std::int32_t{3},std::int32_t{7}}, false,
       noisemaker::glsl::Vec2(-7.0f, 5.0f), noisemaker::glsl::Vec2(17.0f, 13.0f), 0.0f, 0U, 0U},
      {"synth/osc2d:osc2d", "linear", "0a8f1f1176f3a08c13c391a4cb65a40ade56dfe8f37e23ab4a35374384fb9661", "c2c4520a15b3a63c7df06fc34d90ef86635296fd8c4397b9344beb75b2124570",
       {0x3ea3beecU,0x3ea3beecU,0x3ea3beecU,0x3f800000U,0x3e3a5ed0U,0x3e3a5ed0U,0x3e3a5ed0U,0x3f800000U,0x3f2f0ed4U,0x3f2f0ed4U,0x3f2f0ed4U,0x3f800000U},
       {2.5f,-45.0f,0.0f,0.0f,0.0f}, {std::int32_t{1},std::int32_t{5},std::int32_t{19}}, false,
       noisemaker::glsl::Vec2(11.0f, -4.0f), noisemaker::glsl::Vec2(29.0f, 17.0f), 0.375f, 0U, 0U},
      {"synth/osc2d:osc2d", "saw", "16bf15e0500ab4b685d92fe51a9f2301f44eaa56e8daabaa4f03fe1b875d6a6e", "116f3bcee7193882d637f80e80b34d6d92a5f00a8378b485b2d56c44b8b0bb5a",
       {0x3f6de50cU,0x3f6de50cU,0x3f6de50cU,0x3f800000U,0x3f52f286U,0x3f52f286U,0x3f52f286U,0x3f800000U,0x3f380000U,0x3f380000U,0x3f380000U,0x3f800000U},
       {4.25f,0.0f,0.0f,0.0f,0.0f}, {std::int32_t{2},std::int32_t{7},std::int32_t{37}}, false,
       noisemaker::glsl::Vec2(-13.0f, 9.0f), noisemaker::glsl::Vec2(23.0f, 19.0f), 0.875f, 0U, 0U},
      {"synth/osc2d:osc2d", "saw_inverse", "c3bf2586c7294ef362a06a46d5bbe3f1c099ce085d64cb7ca1e6dc6420db3b49", "589043f6e20d86f79963741190f30cc5fb7f6b5df661aba097a94f8a5f89f728",
       {0x3e186a58U,0x3e186a58U,0x3e186a58U,0x3f800000U,0x3eebf8eeU,0x3eebf8eeU,0x3eebf8eeU,0x3f800000U,0x3f45de58U,0x3f45de58U,0x3f45de58U,0x3f800000U},
       {1.5f,67.0f,0.0f,0.0f,0.0f}, {std::int32_t{3},std::int32_t{11},std::int32_t{61}}, false,
       noisemaker::glsl::Vec2(5.0f, -11.0f), noisemaker::glsl::Vec2(31.0f, 13.0f), 1.125f, 0U, 0U},
      {"synth/osc2d:osc2d", "square", "c415113794700179b9c794b7cba5572b16bc04b7ab7ad6fd4f9239d68b7687e7", "8953dc58857c436bae5206d5ddaac64fb40f70ae82e94dcb57ca4157de7f3ca5",
       {0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U,0x00000000U,0x00000000U,0x00000000U,0x3f800000U},
       {3.75f,179.0f,0.0f,0.0f,0.0f}, {std::int32_t{4},std::int32_t{13},std::int32_t{83}}, false,
       noisemaker::glsl::Vec2(-17.0f, -3.0f), noisemaker::glsl::Vec2(37.0f, 21.0f), 1.75f, 0U, 0U},
      {"synth/osc2d:osc2d", "noise1d_resolution_fallback", "4b54a28e78e2497e7992c9a04d31528bae33b1e55a050d56caa587bc0aaed6e7", "28daee9425522af780767abebb66850acbde072a7432a7f329fcfa34bef5eaa2",
       {0x3e6ff3aaU,0x3e6ff3aaU,0x3e6ff3aaU,0x3f800000U,0x3f687a52U,0x3f687a52U,0x3f687a52U,0x3f800000U,0x3f678264U,0x3f678264U,0x3f678264U,0x3f800000U},
       {5.5f,-91.0f,0.0f,0.0f,0.0f}, {std::int32_t{5},std::int32_t{17},std::int32_t{101}}, false,
       noisemaker::glsl::Vec2(-19.0f, 7.0f), noisemaker::glsl::Vec2(0.0f, 0.0f), 0.625f, 0U, 0U},
      {"synth/osc2d:osc2d", "noise2d", "ad76c4e9256f71d664e126e8ea4ee91dc3aee60f0b9ba2dd92d0c777bb64cb7b", "8666cb93f507308b60424089005b684b5d84214f7e6bd6ef83ef4802d961847c",
       {0x3f2a8491U,0x3f2a8491U,0x3f2a8491U,0x3f800000U,0x3f359a15U,0x3f359a15U,0x3f359a15U,0x3f800000U,0x3f4229e0U,0x3f4229e0U,0x3f4229e0U,0x3f800000U},
       {7.25f,31.0f,0.0f,0.0f,0.0f}, {std::int32_t{6},std::int32_t{23},std::int32_t{251}}, false,
       noisemaker::glsl::Vec2(9.0f, -15.0f), noisemaker::glsl::Vec2(41.0f, 27.0f), 0.9375f, 0U, 0U},
      {"synth/osc2d:osc2d", "fallback_noise2d", "203bd767c621c1255aa9f0a3eec757c7f01b105cc52f21e28b4dd2b34ba8c802", "874ae97afa8a6e16971eb36f6b12fd73555b8af8975b6eeff288b930761a6232",
       {0x3ec18727U,0x3ec18727U,0x3ec18727U,0x3f800000U,0x3f7ae1e1U,0x3f7ae1e1U,0x3f7ae1e1U,0x3f800000U,0x3b8269c0U,0x3b8269c0U,0x3b8269c0U,0x3f800000U},
       {9.75f,143.0f,0.0f,0.0f,0.0f}, {std::int32_t{9},std::int32_t{29},std::int32_t{503}}, false,
       noisemaker::glsl::Vec2(-23.0f, -9.0f), noisemaker::glsl::Vec2(43.0f, 31.0f), 1.375f, 0U, 0U},
  }};
}

[[nodiscard]] const noisemaker::Surface& task14_surface(
    std::uint32_t tag, const noisemaker::Surface& tag1,
    const noisemaker::Surface& tag23, const noisemaker::Surface& tag37,
    const noisemaker::Surface& tag53) {
  if (tag == 1U) return tag1;
  if (tag == 23U) return tag23;
  if (tag == 37U) return tag37;
  if (tag == 53U) return tag53;
  throw std::invalid_argument("unknown Task 14 formula surface tag");
}

void populate_task14_bindings(noisemaker::glsl::Bindings& bindings,
                              const Task14Case& fixture,
                              const noisemaker::Surface& tag1,
                              const noisemaker::Surface& tag23,
                              const noisemaker::Surface& tag37,
                              const noisemaker::Surface& tag53,
                              std::string_view skip = {}) {
  const auto uniform = [&](std::string_view name, noisemaker::glsl::UniformValue value) {
    if (name != skip) bindings.set_uniform(std::string(name), std::move(value));
  };
  const auto texture = [&](std::string_view name, std::uint32_t tag) {
    if (name != skip) bindings.set_texture(std::string(name),
        task14_surface(tag, tag1, tag23, tag37, tag53));
  };
  if (fixture.key == "filter/pixelSort:prepare") {
    texture("inputTex", fixture.input_tag);
    uniform("resolution", noisemaker::glsl::Vec2(9.0f, 7.0f));
    uniform("angled", fixture.values[0]); uniform("time", fixture.time);
    uniform("darkest", fixture.flag); uniform("wrap", fixture.values[1]);
  } else if (fixture.key == "filter/pixelSort:finalize") {
    texture("inputTex", fixture.input_tag); texture("originalTex", fixture.original_tag);
    uniform("resolution", noisemaker::glsl::Vec2(9.0f, 7.0f));
    uniform("angled", fixture.values[0]); uniform("darkest", fixture.flag);
    uniform("wrap", fixture.values[1]); uniform("alpha", fixture.values[2]);
  } else if (fixture.key == "filter/skew:skew") {
    texture("inputTex", fixture.input_tag);
    uniform("skewAmt", fixture.values[0]); uniform("rotation", fixture.values[1]);
    uniform("wrap", fixture.values[2]); uniform("tileOffset", fixture.tile_offset);
    uniform("fullResolution", fixture.full_resolution); uniform("renderScale", fixture.values[3]);
  } else if (fixture.key == "filter/tetraCosine:tetraCosine") {
    texture("inputTex", fixture.input_tag); uniform("tileOffset", fixture.tile_offset);
    uniform("fullResolution", fixture.full_resolution); uniform("colorMode", fixture.integers[0]);
    uniform("offsetR", 0.10999999940395355f); uniform("offsetG", 0.43000000715255737f);
    uniform("offsetB", 0.79000002145767212f); uniform("ampR", 0.87000000476837158f);
    uniform("ampG", 0.61000001430511475f); uniform("ampB", 0.28999999165534973f);
    uniform("freqR", 1.0f); uniform("freqG", 3.0f); uniform("freqB", 4.0f);
    uniform("phaseR", 0.070000000298023224f); uniform("phaseG", 0.33000001311302185f);
    uniform("phaseB", 0.81000000238418579f); uniform("repeat", 2.7000000476837158f);
    uniform("offset", 0.18999999761581421f); uniform("alpha", fixture.values[0]);
    uniform("rotation", fixture.integers[1]); uniform("time", fixture.time);
  } else if (fixture.key == "filter/tile:tile") {
    texture("inputTex", fixture.input_tag); uniform("tileOffset", fixture.tile_offset);
    uniform("fullResolution", fixture.full_resolution); uniform("symmetry", fixture.integers[0]);
    uniform("scale", fixture.values[0]); uniform("offsetX", fixture.values[1]);
    uniform("offsetY", fixture.values[2]); uniform("angle", fixture.values[3]);
    uniform("repeat", fixture.values[4]); uniform("aspectLens", fixture.flag);
  } else if (fixture.key == "synth/osc2d:osc2d") {
    uniform("resolution", noisemaker::glsl::Vec2(9.0f, 7.0f));
    uniform("tileOffset", fixture.tile_offset); uniform("fullResolution", fixture.full_resolution);
    uniform("aspect", 1.2857142686843872f); uniform("time", fixture.time);
    uniform("oscType", fixture.integers[0]); uniform("frequency", fixture.integers[1]);
    uniform("speed", fixture.values[0]); uniform("rotation", fixture.values[1]);
    uniform("seed", fixture.integers[2]);
  }
}

[[nodiscard]] noisemaker::Surface render_task14(const Task14Case& fixture,
                                                 std::string_view skip = {}) {
  const noisemaker::Surface tag1 = source(5U, 3U, 1U);
  const noisemaker::Surface tag23 = source(4U, 6U, 23U);
  const noisemaker::Surface tag37 = source(7U, 2U, 37U);
  const noisemaker::Surface tag53 = source(3U, 5U, 53U);
  noisemaker::glsl::Bindings bindings;
  populate_task14_bindings(bindings, fixture, tag1, tag23, tag37, tag53, skip);
  return noisemaker::run_pass(noisemaker::generated::bind(fixture.key, bindings),
                              9U, 7U, fixture.time,
                              static_cast<float>(fixture.integers[2]));
}

TEST(typed_task14_all_thirty_external_oracles_are_exact_repeatable_and_top_down) {
  const auto fixtures = task14_cases();
  constexpr std::array<std::size_t, 3> pixels{0U, 31U, 62U};
  for (const Task14Case& fixture : fixtures) {
    const noisemaker::Surface first = render_task14(fixture);
    const noisemaker::Surface second = render_task14(fixture);
    REQUIRE(first.width() == 9U); REQUIRE(first.height() == 7U);
    require_repeat(first, second);
    const std::string name = std::string(fixture.key) + "/" + std::string(fixture.variant);
    const auto floats = little_endian_float_bytes(first);
    if (hex(sha256(floats)) != fixture.float_hash) {
      std::ostringstream detail;
      detail << name << " float oracle hash: " << hex(sha256(floats)) << " probes:";
      for (std::size_t pixel : pixels) for (std::size_t lane = 0; lane < 4U; ++lane)
        detail << ' ' << std::hex << noisemaker::float_bits_to_uint(first.data()[pixel * 4U + lane]);
      throw std::runtime_error(detail.str());
    }
    if (hex(sha256(first.to_rgba8())) != fixture.rgba_hash)
      throw std::runtime_error(name + " rgba oracle hash: " + hex(sha256(first.to_rgba8())));
    for (std::size_t probe = 0; probe < pixels.size(); ++probe)
      for (std::size_t lane = 0; lane < 4U; ++lane)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[pixels[probe] * 4U + lane]) ==
                fixture.probes[probe * 4U + lane]);
    if (fixture.key == "filter/tile:tile" || fixture.key == "synth/osc2d:osc2d")
      for (std::size_t pixel = 0; pixel < 63U; ++pixel)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[pixel * 4U + 3U]) == 0x3f800000U);
  }
}

TEST(typed_task14_every_required_binding_fails_closed) {
  struct UniformFixture {
    std::string_view key;
    std::string_view uniform;
    noisemaker::glsl::UniformValue wrong;
  };
  const std::array<UniformFixture, 55> uniforms{{
      {"filter/pixelSort:prepare", "resolution", 1.0f},
      {"filter/pixelSort:prepare", "angled", std::int32_t{1}},
      {"filter/pixelSort:prepare", "time", std::int32_t{1}},
      {"filter/pixelSort:prepare", "darkest", std::int32_t{1}},
      {"filter/pixelSort:prepare", "wrap", std::int32_t{1}},
      {"filter/pixelSort:finalize", "resolution", 1.0f},
      {"filter/pixelSort:finalize", "angled", std::int32_t{1}},
      {"filter/pixelSort:finalize", "darkest", std::int32_t{1}},
      {"filter/pixelSort:finalize", "wrap", std::int32_t{1}},
      {"filter/pixelSort:finalize", "alpha", std::int32_t{1}},
      {"filter/skew:skew", "skewAmt", std::int32_t{1}},
      {"filter/skew:skew", "rotation", std::int32_t{1}},
      {"filter/skew:skew", "wrap", std::int32_t{1}},
      {"filter/skew:skew", "tileOffset", 1.0f},
      {"filter/skew:skew", "fullResolution", 1.0f},
      {"filter/skew:skew", "renderScale", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "tileOffset", 1.0f},
      {"filter/tetraCosine:tetraCosine", "fullResolution", 1.0f},
      {"filter/tetraCosine:tetraCosine", "colorMode", 1.0f},
      {"filter/tetraCosine:tetraCosine", "offsetR", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "offsetG", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "offsetB", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "ampR", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "ampG", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "ampB", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "freqR", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "freqG", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "freqB", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "phaseR", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "phaseG", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "phaseB", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "repeat", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "offset", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "alpha", std::int32_t{1}},
      {"filter/tetraCosine:tetraCosine", "rotation", 1.0f},
      {"filter/tetraCosine:tetraCosine", "time", std::int32_t{1}},
      {"filter/tile:tile", "tileOffset", 1.0f},
      {"filter/tile:tile", "fullResolution", 1.0f},
      {"filter/tile:tile", "symmetry", 1.0f},
      {"filter/tile:tile", "scale", std::int32_t{1}},
      {"filter/tile:tile", "offsetX", std::int32_t{1}},
      {"filter/tile:tile", "offsetY", std::int32_t{1}},
      {"filter/tile:tile", "angle", std::int32_t{1}},
      {"filter/tile:tile", "repeat", std::int32_t{1}},
      {"filter/tile:tile", "aspectLens", std::int32_t{1}},
      {"synth/osc2d:osc2d", "resolution", 1.0f},
      {"synth/osc2d:osc2d", "tileOffset", 1.0f},
      {"synth/osc2d:osc2d", "fullResolution", 1.0f},
      {"synth/osc2d:osc2d", "aspect", std::int32_t{1}},
      {"synth/osc2d:osc2d", "time", std::int32_t{1}},
      {"synth/osc2d:osc2d", "oscType", 1.0f},
      {"synth/osc2d:osc2d", "frequency", 1.0f},
      {"synth/osc2d:osc2d", "speed", std::int32_t{1}},
      {"synth/osc2d:osc2d", "rotation", std::int32_t{1}},
      {"synth/osc2d:osc2d", "seed", 1.0f},
  }};
  struct SamplerFixture { std::string_view key; std::string_view sampler; };
  constexpr std::array<SamplerFixture, 6> samplers{{
      {"filter/pixelSort:prepare", "inputTex"},
      {"filter/pixelSort:finalize", "inputTex"},
      {"filter/pixelSort:finalize", "originalTex"},
      {"filter/skew:skew", "inputTex"},
      {"filter/tetraCosine:tetraCosine", "inputTex"},
      {"filter/tile:tile", "inputTex"},
  }};
  const auto fixtures = task14_cases();
  const noisemaker::Surface tag1 = source(5U, 3U, 1U);
  const noisemaker::Surface tag23 = source(4U, 6U, 23U);
  const noisemaker::Surface tag37 = source(7U, 2U, 37U);
  const noisemaker::Surface tag53 = source(3U, 5U, 53U);
  const auto fixture_for = [&](std::string_view key) -> const Task14Case& {
    for (const Task14Case& fixture : fixtures) if (fixture.key == key) return fixture;
    throw std::invalid_argument("missing Task 14 fixture");
  };
  for (const UniformFixture& item : uniforms) {
    const Task14Case& fixture = fixture_for(item.key);
    noisemaker::glsl::Bindings missing;
    populate_task14_bindings(missing, fixture, tag1, tag23, tag37, tag53, item.uniform);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, missing),
                      noisemaker::glsl::KernelBindingError);
    noisemaker::glsl::Bindings wrong_bindings;
    populate_task14_bindings(wrong_bindings, fixture, tag1, tag23, tag37, tag53);
    wrong_bindings.set_uniform(std::string(item.uniform), item.wrong);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, wrong_bindings),
                      noisemaker::glsl::KernelBindingError);
  }
  for (const SamplerFixture& item : samplers) {
    const Task14Case& fixture = fixture_for(item.key);
    noisemaker::glsl::Bindings missing;
    populate_task14_bindings(missing, fixture, tag1, tag23, tag37, tag53, item.sampler);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, missing),
                      noisemaker::glsl::KernelBindingError);
  }
}

TEST(typed_pixel_sort_admits_compute_rank_but_still_excludes_gather_sorted) {
  noisemaker::glsl::Bindings empty;
  REQUIRE_THROWS_AS(noisemaker::generated::bind("filter/pixelSort:computeRank", empty),
                    noisemaker::glsl::KernelBindingError);
  noisemaker::glsl::Bindings wrong;
  wrong.set_uniform("lumTex", 0.5);
  REQUIRE_THROWS_AS(noisemaker::generated::bind("filter/pixelSort:computeRank", wrong),
                    noisemaker::glsl::KernelBindingError);
}

enum class Task15BindingType { sampler, scalar, integer, boolean, vec2, vec3 };

struct Task15Binding {
  std::string_view key;
  std::string_view name;
  Task15BindingType type;
};

constexpr std::array<Task15Binding, 235> kTask15Bindings{{
    {"filter/chrome:chBlurH", "inputTex", Task15BindingType::sampler},
    {"filter/chrome:chBlurH", "resolution", Task15BindingType::vec2},
    {"filter/chrome:chBlurH", "smoothness", Task15BindingType::scalar},
    {"filter/chrome:chBlurV", "inputTex", Task15BindingType::sampler},
    {"filter/chrome:chBlurV", "resolution", Task15BindingType::vec2},
    {"filter/chrome:chBlurV", "smoothness", Task15BindingType::scalar},
    {"filter/clouds:clouds", "inputTex", Task15BindingType::sampler},
    {"filter/clouds:clouds", "tileOffset", Task15BindingType::vec2},
    {"filter/clouds:clouds", "fullResolution", Task15BindingType::vec2},
    {"filter/clouds:clouds", "seed", Task15BindingType::scalar},
    {"filter/clouds:clouds", "scale", Task15BindingType::scalar},
    {"filter/clouds:clouds", "speed", Task15BindingType::integer},
    {"filter/clouds:clouds", "time", Task15BindingType::scalar},
    {"filter/craquelure:craquelure", "inputTex", Task15BindingType::sampler},
    {"filter/craquelure:craquelure", "resolution", Task15BindingType::vec2},
    {"filter/craquelure:craquelure", "tileOffset", Task15BindingType::vec2},
    {"filter/craquelure:craquelure", "spacing", Task15BindingType::scalar},
    {"filter/craquelure:craquelure", "depth", Task15BindingType::scalar},
    {"filter/craquelure:craquelure", "brightness", Task15BindingType::scalar},
    {"filter/craquelure:craquelure", "seed", Task15BindingType::integer},
    {"filter/hatch:hatch", "inputTex", Task15BindingType::sampler},
    {"filter/hatch:hatch", "resolution", Task15BindingType::vec2},
    {"filter/hatch:hatch", "tileOffset", Task15BindingType::vec2},
    {"filter/hatch:hatch", "strokeLength", Task15BindingType::scalar},
    {"filter/hatch:hatch", "direction", Task15BindingType::integer},
    {"filter/hatch:hatch", "balance", Task15BindingType::scalar},
    {"filter/hatch:hatch", "pressure", Task15BindingType::scalar},
    {"filter/hatch:hatch", "inkColor", Task15BindingType::vec3},
    {"filter/hatch:hatch", "paperColor", Task15BindingType::vec3},
    {"filter/highPass:hpBlurH", "inputTex", Task15BindingType::sampler},
    {"filter/highPass:hpBlurH", "resolution", Task15BindingType::vec2},
    {"filter/highPass:hpBlurH", "radius", Task15BindingType::scalar},
    {"filter/highPass:hpBlurV", "inputTex", Task15BindingType::sampler},
    {"filter/highPass:hpBlurV", "resolution", Task15BindingType::vec2},
    {"filter/highPass:hpBlurV", "radius", Task15BindingType::scalar},
    {"filter/lowPoly:lowPoly", "inputTex", Task15BindingType::sampler},
    {"filter/lowPoly:lowPoly", "tileOffset", Task15BindingType::vec2},
    {"filter/lowPoly:lowPoly", "fullResolution", Task15BindingType::vec2},
    {"filter/lowPoly:lowPoly", "scale", Task15BindingType::scalar},
    {"filter/lowPoly:lowPoly", "seed", Task15BindingType::scalar},
    {"filter/lowPoly:lowPoly", "mode", Task15BindingType::integer},
    {"filter/lowPoly:lowPoly", "edgeStrength", Task15BindingType::scalar},
    {"filter/lowPoly:lowPoly", "edgeColor", Task15BindingType::vec3},
    {"filter/lowPoly:lowPoly", "speed", Task15BindingType::scalar},
    {"filter/lowPoly:lowPoly", "time", Task15BindingType::scalar},
    {"filter/lowPoly:lowPoly", "alpha", Task15BindingType::scalar},
    {"filter/morphology:morphA", "inputTex", Task15BindingType::sampler},
    {"filter/morphology:morphA", "resolution", Task15BindingType::vec2},
    {"filter/morphology:morphA", "mode", Task15BindingType::integer},
    {"filter/morphology:morphA", "radius", Task15BindingType::scalar},
    {"filter/morphology:morphB", "inputTex", Task15BindingType::sampler},
    {"filter/morphology:morphB", "resolution", Task15BindingType::vec2},
    {"filter/morphology:morphB", "mode", Task15BindingType::integer},
    {"filter/morphology:morphB", "radius", Task15BindingType::scalar},
    {"filter/normalize:reduce", "tileOffset", Task15BindingType::vec2},
    {"filter/normalize:reduce", "fullResolution", Task15BindingType::vec2},
    {"filter/normalize:reduce", "inputTex", Task15BindingType::sampler},
    {"filter/normalize:reduceMinmax", "tileOffset", Task15BindingType::vec2},
    {"filter/normalize:reduceMinmax", "fullResolution", Task15BindingType::vec2},
    {"filter/normalize:reduceMinmax", "inputTex", Task15BindingType::sampler},
    {"filter/oilPaint:oilPost", "inputTex", Task15BindingType::sampler},
    {"filter/oilPaint:oilPost", "flatTex", Task15BindingType::sampler},
    {"filter/oilPaint:oilPost", "resolution", Task15BindingType::vec2},
    {"filter/oilPaint:oilPost", "tileOffset", Task15BindingType::vec2},
    {"filter/oilPaint:oilPost", "size", Task15BindingType::scalar},
    {"filter/oilPaint:oilPost", "detail", Task15BindingType::scalar},
    {"filter/oilPaint:oilPost", "textureAmount", Task15BindingType::scalar},
    {"filter/oilPaint:oilPost", "seed", Task15BindingType::integer},
    {"filter/patchwork:patchwork", "inputTex", Task15BindingType::sampler},
    {"filter/patchwork:patchwork", "resolution", Task15BindingType::vec2},
    {"filter/patchwork:patchwork", "tileOffset", Task15BindingType::vec2},
    {"filter/patchwork:patchwork", "fullResolution", Task15BindingType::vec2},
    {"filter/patchwork:patchwork", "squareSize", Task15BindingType::scalar},
    {"filter/patchwork:patchwork", "relief", Task15BindingType::scalar},
    {"filter/patchwork:patchwork", "lightAngle", Task15BindingType::scalar},
    {"filter/photocopy:pcBlurH", "inputTex", Task15BindingType::sampler},
    {"filter/photocopy:pcBlurH", "resolution", Task15BindingType::vec2},
    {"filter/photocopy:pcBlurH", "detail", Task15BindingType::scalar},
    {"filter/photocopy:pcBlurV", "inputTex", Task15BindingType::sampler},
    {"filter/photocopy:pcBlurV", "resolution", Task15BindingType::vec2},
    {"filter/photocopy:pcBlurV", "detail", Task15BindingType::scalar},
    {"filter/pixelSort:findBrightest", "lumTex", Task15BindingType::sampler},
    {"filter/plasticWrap:pwBlurH", "inputTex", Task15BindingType::sampler},
    {"filter/plasticWrap:pwBlurH", "resolution", Task15BindingType::vec2},
    {"filter/plasticWrap:pwBlurH", "detail", Task15BindingType::scalar},
    {"filter/plasticWrap:pwBlurV", "inputTex", Task15BindingType::sampler},
    {"filter/plasticWrap:pwBlurV", "resolution", Task15BindingType::vec2},
    {"filter/plasticWrap:pwBlurV", "detail", Task15BindingType::scalar},
    {"filter/relief:rlBlurH", "inputTex", Task15BindingType::sampler},
    {"filter/relief:rlBlurH", "resolution", Task15BindingType::vec2},
    {"filter/relief:rlBlurH", "smoothness", Task15BindingType::scalar},
    {"filter/relief:rlBlurV", "inputTex", Task15BindingType::sampler},
    {"filter/relief:rlBlurV", "resolution", Task15BindingType::vec2},
    {"filter/relief:rlBlurV", "smoothness", Task15BindingType::scalar},
    {"filter/reverb:reverb", "tileOffset", Task15BindingType::vec2},
    {"filter/reverb:reverb", "fullResolution", Task15BindingType::vec2},
    {"filter/reverb:reverb", "inputTex", Task15BindingType::sampler},
    {"filter/reverb:reverb", "iterations", Task15BindingType::integer},
    {"filter/reverb:reverb", "ridges", Task15BindingType::boolean},
    {"filter/reverb:reverb", "alpha", Task15BindingType::scalar},
    {"filter/reverb:reverb", "wrap", Task15BindingType::scalar},
    {"filter/scatter:scatterSmooth", "inputTex", Task15BindingType::sampler},
    {"filter/scatter:scatterSmooth", "resolution", Task15BindingType::vec2},
    {"filter/scatter:scatterSmooth", "smoothness", Task15BindingType::scalar},
    {"filter/stamp:stBlurH", "inputTex", Task15BindingType::sampler},
    {"filter/stamp:stBlurH", "resolution", Task15BindingType::vec2},
    {"filter/stamp:stBlurH", "smoothness", Task15BindingType::scalar},
    {"filter/stamp:stBlurV", "inputTex", Task15BindingType::sampler},
    {"filter/stamp:stBlurV", "resolution", Task15BindingType::vec2},
    {"filter/stamp:stBlurV", "smoothness", Task15BindingType::scalar},
    {"filter/strokes:stkPost", "inputTex", Task15BindingType::sampler},
    {"filter/strokes:stkPost", "smearTex", Task15BindingType::sampler},
    {"filter/strokes:stkPost", "resolution", Task15BindingType::vec2},
    {"filter/strokes:stkPost", "sharpness", Task15BindingType::scalar},
    {"filter/unsharpMask:usmBlurH", "inputTex", Task15BindingType::sampler},
    {"filter/unsharpMask:usmBlurH", "resolution", Task15BindingType::vec2},
    {"filter/unsharpMask:usmBlurH", "radius", Task15BindingType::scalar},
    {"filter/unsharpMask:usmBlurV", "inputTex", Task15BindingType::sampler},
    {"filter/unsharpMask:usmBlurV", "resolution", Task15BindingType::vec2},
    {"filter/unsharpMask:usmBlurV", "radius", Task15BindingType::scalar},
    {"filter/wormhole:blend", "inputTex", Task15BindingType::sampler},
    {"filter/wormhole:blend", "accumTex", Task15BindingType::sampler},
    {"filter/wormhole:blend", "resolution", Task15BindingType::vec2},
    {"filter/wormhole:blend", "tileOffset", Task15BindingType::vec2},
    {"filter/wormhole:blend", "fullResolution", Task15BindingType::vec2},
    {"filter/wormhole:blend", "alpha", Task15BindingType::scalar},
    {"mixer/cellSplit:cellSplit", "inputTex", Task15BindingType::sampler},
    {"mixer/cellSplit:cellSplit", "tex", Task15BindingType::sampler},
    {"mixer/cellSplit:cellSplit", "resolution", Task15BindingType::vec2},
    {"mixer/cellSplit:cellSplit", "tileOffset", Task15BindingType::vec2},
    {"mixer/cellSplit:cellSplit", "fullResolution", Task15BindingType::vec2},
    {"mixer/cellSplit:cellSplit", "mode", Task15BindingType::integer},
    {"mixer/cellSplit:cellSplit", "scale", Task15BindingType::scalar},
    {"mixer/cellSplit:cellSplit", "edgeWidth", Task15BindingType::scalar},
    {"mixer/cellSplit:cellSplit", "seed", Task15BindingType::integer},
    {"mixer/cellSplit:cellSplit", "invert", Task15BindingType::integer},
    {"mixer/cellSplit:cellSplit", "time", Task15BindingType::scalar},
    {"mixer/cellSplit:cellSplit", "speed", Task15BindingType::scalar},
    {"mixer/mashup:mashup", "resolution", Task15BindingType::vec2},
    {"mixer/mashup:mashup", "source", Task15BindingType::sampler},
    {"mixer/mashup:mashup", "layer0_tex", Task15BindingType::sampler},
    {"mixer/mashup:mashup", "layer1_tex", Task15BindingType::sampler},
    {"mixer/mashup:mashup", "layer2_tex", Task15BindingType::sampler},
    {"mixer/mashup:mashup", "layer3_tex", Task15BindingType::sampler},
    {"mixer/mashup:mashup", "layer4_tex", Task15BindingType::sampler},
    {"mixer/mashup:mashup", "layer5_tex", Task15BindingType::sampler},
    {"mixer/mashup:mashup", "layer6_tex", Task15BindingType::sampler},
    {"mixer/mashup:mashup", "layer7_tex", Task15BindingType::sampler},
    {"mixer/mashup:mashup", "layers", Task15BindingType::integer},
    {"mixer/mashup:mashup", "smoothness", Task15BindingType::scalar},
    {"mixer/mashup:mashup", "layer0_active", Task15BindingType::integer},
    {"mixer/mashup:mashup", "layer1_active", Task15BindingType::integer},
    {"mixer/mashup:mashup", "layer2_active", Task15BindingType::integer},
    {"mixer/mashup:mashup", "layer3_active", Task15BindingType::integer},
    {"mixer/mashup:mashup", "layer4_active", Task15BindingType::integer},
    {"mixer/mashup:mashup", "layer5_active", Task15BindingType::integer},
    {"mixer/mashup:mashup", "layer6_active", Task15BindingType::integer},
    {"mixer/mashup:mashup", "layer7_active", Task15BindingType::integer},
    {"mixer/shadow:shadow", "inputTex", Task15BindingType::sampler},
    {"mixer/shadow:shadow", "tex", Task15BindingType::sampler},
    {"mixer/shadow:shadow", "resolution", Task15BindingType::vec2},
    {"mixer/shadow:shadow", "tileOffset", Task15BindingType::vec2},
    {"mixer/shadow:shadow", "fullResolution", Task15BindingType::vec2},
    {"mixer/shadow:shadow", "renderScale", Task15BindingType::scalar},
    {"mixer/shadow:shadow", "maskSource", Task15BindingType::integer},
    {"mixer/shadow:shadow", "sourceChannel", Task15BindingType::integer},
    {"mixer/shadow:shadow", "threshold", Task15BindingType::scalar},
    {"mixer/shadow:shadow", "color", Task15BindingType::vec3},
    {"mixer/shadow:shadow", "offsetX", Task15BindingType::scalar},
    {"mixer/shadow:shadow", "offsetY", Task15BindingType::scalar},
    {"mixer/shadow:shadow", "blur", Task15BindingType::scalar},
    {"mixer/shadow:shadow", "spread", Task15BindingType::scalar},
    {"mixer/shadow:shadow", "wrap", Task15BindingType::integer},
    {"synth/cell:cell", "time", Task15BindingType::scalar},
    {"synth/cell:cell", "seed", Task15BindingType::integer},
    {"synth/cell:cell", "resolution", Task15BindingType::vec2},
    {"synth/cell:cell", "tileOffset", Task15BindingType::vec2},
    {"synth/cell:cell", "fullResolution", Task15BindingType::vec2},
    {"synth/cell:cell", "renderScale", Task15BindingType::scalar},
    {"synth/cell:cell", "metric", Task15BindingType::integer},
    {"synth/cell:cell", "scale", Task15BindingType::scalar},
    {"synth/cell:cell", "cellScale", Task15BindingType::scalar},
    {"synth/cell:cell", "cellSmooth", Task15BindingType::scalar},
    {"synth/cell:cell", "variation", Task15BindingType::scalar},
    {"synth/cell:cell", "speed", Task15BindingType::scalar},
    {"synth/gradient:gradient", "resolution", Task15BindingType::vec2},
    {"synth/gradient:gradient", "tileOffset", Task15BindingType::vec2},
    {"synth/gradient:gradient", "fullResolution", Task15BindingType::vec2},
    {"synth/gradient:gradient", "gradientType", Task15BindingType::integer},
    {"synth/gradient:gradient", "rotation", Task15BindingType::scalar},
    {"synth/gradient:gradient", "repeat", Task15BindingType::integer},
    {"synth/gradient:gradient", "colorCount", Task15BindingType::integer},
    {"synth/gradient:gradient", "color1", Task15BindingType::vec3},
    {"synth/gradient:gradient", "color2", Task15BindingType::vec3},
    {"synth/gradient:gradient", "color3", Task15BindingType::vec3},
    {"synth/gradient:gradient", "color4", Task15BindingType::vec3},
    {"synth/gradient:gradient", "seed", Task15BindingType::integer},
    {"synth/gradient:gradient", "time", Task15BindingType::scalar},
    {"synth/gradient:gradient", "speed", Task15BindingType::scalar},
    {"synth/mandala:mandala", "resolution", Task15BindingType::vec2},
    {"synth/mandala:mandala", "tileOffset", Task15BindingType::vec2},
    {"synth/mandala:mandala", "fullResolution", Task15BindingType::vec2},
    {"synth/mandala:mandala", "aspect", Task15BindingType::scalar},
    {"synth/mandala:mandala", "scale", Task15BindingType::scalar},
    {"synth/mandala:mandala", "rotation", Task15BindingType::scalar},
    {"synth/mandala:mandala", "thickness", Task15BindingType::scalar},
    {"synth/mandala:mandala", "smoothness", Task15BindingType::scalar},
    {"synth/mandala:mandala", "symmetry", Task15BindingType::integer},
    {"synth/mandala:mandala", "layers", Task15BindingType::integer},
    {"synth/mandala:mandala", "shape", Task15BindingType::integer},
    {"synth/mandala:mandala", "layerSpacing", Task15BindingType::scalar},
    {"synth/mandala:mandala", "twist", Task15BindingType::scalar},
    {"synth/mandala:mandala", "shapeGrowth", Task15BindingType::scalar},
    {"synth/mandala:mandala", "bindu", Task15BindingType::boolean},
    {"synth/mandala:mandala", "animation", Task15BindingType::integer},
    {"synth/mandala:mandala", "speed", Task15BindingType::scalar},
    {"synth/mandala:mandala", "pulseDepth", Task15BindingType::scalar},
    {"synth/mandala:mandala", "time", Task15BindingType::scalar},
    {"synth/mandala:mandala", "fgColor", Task15BindingType::vec3},
    {"synth/mandala:mandala", "bgColor", Task15BindingType::vec3},
    {"synth/subdivide:subdivide", "inputTex", Task15BindingType::sampler},
    {"synth/subdivide:subdivide", "resolution", Task15BindingType::vec2},
    {"synth/subdivide:subdivide", "tileOffset", Task15BindingType::vec2},
    {"synth/subdivide:subdivide", "fullResolution", Task15BindingType::vec2},
    {"synth/subdivide:subdivide", "renderScale", Task15BindingType::scalar},
    {"synth/subdivide:subdivide", "mode", Task15BindingType::scalar},
    {"synth/subdivide:subdivide", "depth", Task15BindingType::scalar},
    {"synth/subdivide:subdivide", "density", Task15BindingType::scalar},
    {"synth/subdivide:subdivide", "seed", Task15BindingType::scalar},
    {"synth/subdivide:subdivide", "fill", Task15BindingType::scalar},
    {"synth/subdivide:subdivide", "outline", Task15BindingType::scalar},
    {"synth/subdivide:subdivide", "inputMix", Task15BindingType::scalar},
    {"synth/subdivide:subdivide", "wrap", Task15BindingType::scalar},
    {"synth/subdivide:subdivide", "time", Task15BindingType::scalar},
    {"synth/subdivide:subdivide", "speed", Task15BindingType::scalar},
}};

void populate_task15_bindings(noisemaker::glsl::Bindings& bindings, std::string_view key,
                              const noisemaker::Surface& surface, std::string_view skip = {}) {
  for (const Task15Binding& item : kTask15Bindings) {
    if (item.key != key || item.name == skip) continue;
    const std::string name(item.name);
    switch (item.type) {
      case Task15BindingType::sampler: bindings.set_texture(name, surface); break;
      case Task15BindingType::scalar: bindings.set_uniform(name, 0.5f); break;
      case Task15BindingType::integer: bindings.set_uniform(name, std::int32_t{1}); break;
      case Task15BindingType::boolean: bindings.set_uniform(name, true); break;
      case Task15BindingType::vec2:
        bindings.set_uniform(name, noisemaker::glsl::Vec2(9.0f, 7.0f)); break;
      case Task15BindingType::vec3:
        bindings.set_uniform(name, noisemaker::glsl::Vec3(0.2f, 0.4f, 0.6f)); break;
    }
  }
}

TEST(typed_task15_every_required_uniform_and_sampler_fails_closed) {
  const noisemaker::Surface surface = source(1U, 1U, 1U);
  std::size_t sampler_count = 0U;
  std::size_t uniform_count = 0U;
  for (const Task15Binding& item : kTask15Bindings) {
    noisemaker::glsl::Bindings missing;
    populate_task15_bindings(missing, item.key, surface, item.name);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, missing),
                      noisemaker::glsl::KernelBindingError);
    if (item.type == Task15BindingType::sampler) {
      ++sampler_count;
      continue;
    }
    ++uniform_count;
    noisemaker::glsl::Bindings wrong;
    populate_task15_bindings(wrong, item.key, surface);
    if (item.type == Task15BindingType::integer)
      wrong.set_uniform(std::string(item.name), 1.0f);
    else
      wrong.set_uniform(std::string(item.name), std::int32_t{1});
    REQUIRE_THROWS_AS(noisemaker::generated::bind(item.key, wrong),
                      noisemaker::glsl::KernelBindingError);
  }
  REQUIRE(kTask15Bindings.size() == 235U);
  REQUIRE(sampler_count == 46U);
  REQUIRE(uniform_count == 189U);
}

struct Task15OracleCase {
  std::string_view key;
  std::string_view variant;
  std::string_view float_hash;
  std::string_view rgba_hash;
  std::array<std::uint32_t, 12> probes;
  std::int32_t iterations_override;
  bool ridges_override;
};

constexpr std::array<Task15OracleCase, 38> kTask15OracleCases{{
    {"filter/chrome:chBlurH", "defaults", "ae489640288e57d82db168c65719a0e9d3a37916cbb9b4659d21b7892b96f51b", "c2cd505e0b66b948282b7a2692637f80beb38a5a4041d714edad19daa5886cf9",
     {0x3f051fe7U,0x3f19975bU,0x3e2928dbU,0x3f09457cU,0x3ec43f1fU,0x3ec55555U,0x3f20c384U,0x3f362a0cU,0x3f30cb2cU,0x3f59861aU,0x3ec81391U,0x3f18ab36U}, std::int32_t{-1}, false},
    {"filter/chrome:chBlurV", "defaults", "1cf2a575ee71717e5c14f6d3a3b332d3a78b7ac379bcbe8781f517881372a881", "2ee7d28d0c1f81cd673588b5b396f05aba4ba51c89a176a8d16ac090ab0003e3",
     {0x3ef851cbU,0x3f2081c5U,0x3e8fca79U,0x3f04e06eU,0x3f0b6ab8U,0x3ef90caaU,0x3f03828eU,0x3f20d3a7U,0x3f1f8d64U,0x3f4539f0U,0x3ee29731U,0x3f2849ceU}, std::int32_t{-1}, false},
    {"filter/highPass:hpBlurH", "defaults", "70f6c8532ffaed51c05e534dfb85052a2949f59e728bd5db84e1c9b87dff1fce", "648317dbe4dca77d58f75f79aac80e1f37160c1ae3b1bd19a8b812fd4a103a9b",
     {0x3f0271deU,0x3f186d3fU,0x3e39df54U,0x3f0a155eU,0x3eb19d9aU,0x3ec55554U,0x3f254aafU,0x3f3f66f1U,0x3f2bce81U,0x3f4de936U,0x3eb668d9U,0x3f161f59U}, std::int32_t{-1}, false},
    {"filter/highPass:hpBlurV", "defaults", "f180a74dbbbc72b8210a367d012964fed99f2862ae0408cecf2f3203777f767b", "95302c80b39de9fee85b33cfec93a9e83bb944efe07130c5b96dbc53594fa144",
     {0x3eeb09ebU,0x3f1be97bU,0x3e6e433eU,0x3f00a1beU,0x3f160af7U,0x3eecd617U,0x3f104c9bU,0x3f19fd00U,0x3f1d91f0U,0x3f44fd6dU,0x3ed774b7U,0x3f25282eU}, std::int32_t{-1}, false},
    {"filter/morphology:morphA", "defaults", "939318d529b0eff6a29f4de386e357c676a76dc6e8cd6a3fa95ed53a4aaa3eb5", "3198d9ca32072dd62b25685105ae3890a98dc43b6a98cee1a2432cc66601f0ec",
     {0x3f428f5cU,0x3f62aaabU,0x3f2e8ba3U,0x3f666666U,0x3f6147aeU,0x3f400000U,0x3f62e8baU,0x3f733333U,0x3f7ae148U,0x3f780000U,0x3f800000U,0x3f4ccccdU}, std::int32_t{-1}, false},
    {"filter/morphology:morphB", "defaults", "9313582d03c1a78be481234fda46c33efced8936ce5da46144b75a8d87e7d73b", "bf83ad27ecbd2e9bd69298fd11dd8071b2e3dfc5c429116d94e0bfc5d6231d0e",
     {0x3f2b851fU,0x3f555555U,0x3f6e8ba3U,0x3f59999aU,0x3f7ae148U,0x3f7aaaabU,0x3f51745dU,0x3f733333U,0x3f51eb85U,0x3f780000U,0x3f71745dU,0x3f733333U}, std::int32_t{-1}, false},
    {"filter/photocopy:pcBlurH", "defaults", "658b22742d81b75fbe857a771ba3b00e1716ee28152b4f0713c5829f7196bde3", "4dadd1706d15509e6f5cbff5bc8ecdb3e22246d920f98671aad89bdd206478fa",
     {0x3f04ff12U,0x3f184df9U,0x3e2e6724U,0x3f09704bU,0x3ec13f77U,0x3ec55555U,0x3f21eb82U,0x3f3842feU,0x3f311164U,0x3f57a36bU,0x3ec568c7U,0x3f18a1edU}, std::int32_t{-1}, false},
    {"filter/photocopy:pcBlurV", "defaults", "3718d3a60598a8bbe180fa3beb27698d3df6bb5199b57f08fe671e5dc0158e09", "465df03c86c55e35f95bdadf0178a11a84d4ca60d18dc4fa236b2f31be8eb06a",
     {0x3ef5e079U,0x3f1fcd4dU,0x3e8b4fafU,0x3f044307U,0x3f0dd083U,0x3ef69001U,0x3f06af60U,0x3f1f48a4U,0x3f1f9b37U,0x3f456aa6U,0x3ee14fd2U,0x3f2770cdU}, std::int32_t{-1}, false},
    {"filter/plasticWrap:pwBlurH", "defaults", "0e4ddba9b687eafadac6ef64b45f8035562c3592ed202f84a221a9ca39b4caf5", "802c286d907d0399c4d6132e1f43adb4bfcea225cbc5f34b476fe2f97f5357b7",
     {0x3f04520bU,0x3f188156U,0x3e303972U,0x3f099548U,0x3ebdbd41U,0x3ec55555U,0x3f22a57dU,0x3f39d0d8U,0x3f2f97a1U,0x3f555d1eU,0x3ec1ca23U,0x3f17efe6U}, std::int32_t{-1}, false},
    {"filter/plasticWrap:pwBlurV", "defaults", "7da1aaf724a811230f16e74673a703f68ff2b181dd1723f3cc211259f6b2d38d", "dab4e46e7444990c948c6228426917a3a685f2e8f67e0427e5cd56729f3b2c56",
     {0x3ef36a9dU,0x3f1ee2d4U,0x3e86c549U,0x3f0369cfU,0x3f0f9b74U,0x3ef46d59U,0x3f08c2cfU,0x3f1e2147U,0x3f1f0e33U,0x3f454e23U,0x3edf0965U,0x3f26faceU}, std::int32_t{-1}, false},
    {"filter/relief:rlBlurH", "defaults", "9cc9009c89c7b4fdc9507ee1adf114f199dd5c15d243f9a6fdefb125f9782b0c", "6816f44a2cd8dbd703711c4be0912537b1a2e1b4fffd357dec013669035391d3",
     {0x3f05581dU,0x3f234643U,0x3e18ea96U,0x3f07dd5fU,0x3ed119acU,0x3ec55555U,0x3f194deeU,0x3f2a0afcU,0x3f2e4403U,0x3f63b806U,0x3ed865b0U,0x3f19b28eU}, std::int32_t{-1}, false},
    {"filter/relief:rlBlurV", "defaults", "bed26bd5eae076f5d60860c60b7336cb25553e4ce487bdf6094865c1218cf847", "80e3532bb2f021143b3e12c1191266358d1e6b7d0e582e1e03d98d705ba087b0",
     {0x3f01cbc4U,0x3f2495eeU,0x3ea74154U,0x3f0755afU,0x3efb1b80U,0x3f02f0f8U,0x3edf39e9U,0x3f29bfa5U,0x3f1ccf72U,0x3f4463d1U,0x3ee871cdU,0x3f2dd50aU}, std::int32_t{-1}, false},
    {"filter/stamp:stBlurH", "defaults", "dfbf2077278be421c8fd5b70650218753ebcb3bf97a59ec3cf5157719ab4eda2", "69b2f914d0063d06ad3f002dfd7aac83fe8ac12f36ba57ca5dee57f482a0b229",
     {0x3f065561U,0x3f1b055dU,0x3e1b903dU,0x3f097536U,0x3ec9325cU,0x3ec55555U,0x3f1f0f3fU,0x3f3305a4U,0x3f313a67U,0x3f5cc812U,0x3ecb8692U,0x3f18d9abU}, std::int32_t{-1}, false},
    {"filter/stamp:stBlurV", "defaults", "0365bd71e6450bcdaa62463e1b707ef8232e96d1b285621938bff21d2cd34ceb", "e78946cddeb62c71f1ae61066b73966b9c45895e216d3cdea8e4ca5c7a300046",
     {0x3efc693fU,0x3f21de95U,0x3e9726fdU,0x3f060d1fU,0x3f07d0edU,0x3efcd94bU,0x3efda2e4U,0x3f2324e2U,0x3f1fedffU,0x3f450761U,0x3ee515ceU,0x3f296798U}, std::int32_t{-1}, false},
    {"filter/unsharpMask:usmBlurH", "defaults", "4f07a9f646cb81e24baf26660ca378582a17d8c1518eb62e072b6fd7342ee8a0", "c458991c4a0563af25a7a92b763588b18bc873fa6e48be699e0c32e164a387c5",
     {0x3f084ca8U,0x3f2980a7U,0x3e0f4b36U,0x3f083e34U,0x3ec8b62fU,0x3ec55556U,0x3f1591f1U,0x3f270375U,0x3f2f8135U,0x3f662c9cU,0x3ede23c9U,0x3f19299eU}, std::int32_t{-1}, false},
    {"filter/unsharpMask:usmBlurV", "defaults", "5b748a0bf419a5dbecdb0971ee9c4044a2447af9bf5884d75e72df139775b0dc", "17b430222bf4782f5adbe55b253015a83358bef8899216c10d6df9ba5ede23dd",
     {0x3f038e1dU,0x3f26c351U,0x3ea83487U,0x3f07ec81U,0x3ef422bcU,0x3f02b2a0U,0x3ecdd7c8U,0x3f2bfdf3U,0x3f1e897bU,0x3f4174bcU,0x3ee006a2U,0x3f2de2edU}, std::int32_t{-1}, false},
    {"filter/craquelure:craquelure", "defaults", "51a1bc27355d0f8f973fd7ba742e798c85e8ad952a262a8353b137d828dee124", "7af2e319b78f42ef180cb59272c39b58a58db94a10d761c22f2de047e40bf84a",
     {0x3f170a3dU,0x3f500000U,0x3d3a2e8cU,0x3ee66666U,0x3e4ccccdU,0x3ec55555U,0x3e3a2e8cU,0x3f59999aU,0x3f51eb85U,0x3f780000U,0x3ea2e8baU,0x3f19999aU}, std::int32_t{-1}, false},
    {"filter/lowPoly:lowPoly", "defaults", "903342a6bb5b4af8568b84e93e6adca5ad2acf591d565e938620a3e432cf5ceb", "36a4a1b0fa710f1ed0e24270052867b6ecad5b7ca3e43380769b6cdec9f278c3",
     {0x3f01b0c4U,0x3f329965U,0x3d1fdd72U,0x3ee66666U,0x3e9c8b2eU,0x3eeb01e2U,0x3f639862U,0x3f733333U,0x3db77fbaU,0x3e54620cU,0x3f6a9631U,0x3f4ccccdU}, std::int32_t{-1}, false},
    {"filter/patchwork:patchwork", "defaults", "ba842643a73ab731a2a2df9860bd9bc444c361a86ad1ee259c1fb103f831ad29", "535bcf36616037e578dd181e2947159bfd5724dd221c51057b07af49372e19ba",
     {0x3f0e462cU,0x3f43eda7U,0x3d2f605eU,0x3ee66666U,0x3e581416U,0x3ed493c2U,0x3e758b31U,0x3f59999aU,0x3f33e715U,0x3f548995U,0x3e8b9d30U,0x3f19999aU}, std::int32_t{-1}, false},
    {"filter/scatter:scatterSmooth", "defaults", "51a1bc27355d0f8f973fd7ba742e798c85e8ad952a262a8353b137d828dee124", "7af2e319b78f42ef180cb59272c39b58a58db94a10d761c22f2de047e40bf84a",
     {0x3f170a3dU,0x3f500000U,0x3d3a2e8cU,0x3ee66666U,0x3e4ccccdU,0x3ec55555U,0x3e3a2e8cU,0x3f59999aU,0x3f51eb85U,0x3f780000U,0x3ea2e8baU,0x3f19999aU}, std::int32_t{-1}, false},
    {"filter/strokes:stkPost", "defaults", "9c5de62be0ea11267af98db82bce047b319e9b3586c31f1ab5858880cbf6c24b", "e43b0b43ccd24d27e217b04e88a13f2e0d194dc8e10d08d87a3cd7c678d3228c",
     {0x3f407729U,0x00000000U,0x00000000U,0x3ee66666U,0x3e8b9405U,0x3f1fffffU,0x3d87ab60U,0x3f59999aU,0x3f800000U,0x3e2d9365U,0x3ed7cd39U,0x3f19999aU}, std::int32_t{-1}, false},
    {"filter/clouds:clouds", "defaults", "8a6f9b457f9f86c99290ae4ea5be3eda6c9809cd4d6a701cd4c5ce6945475e0d", "bddba5d9807cf197eb6c14bc9b6475217f93a8a9b680676a3b41008ec2945d81",
     {0x3f170a3dU,0x3f500000U,0x3d3a2e8cU,0x3ee66666U,0x3eae147bU,0x3f02aaabU,0x3f7d1746U,0x3f733333U,0x3db851ecU,0x3e555555U,0x3f6ba2e9U,0x3f4ccccdU}, std::int32_t{-1}, false},
    {"filter/hatch:hatch", "defaults", "02e85cbb0464ed82e250ed79c6b05efeb0c56953acf81530cbe31bf77e08e331", "549d3a7401e3e03c135beacf64b894cc7ea83d279df5fcfdf54ad35f55b8152c",
     {0x3dcccccdU,0x3dcccccdU,0x3dcccccdU,0x3ee66666U,0x3dcccccdU,0x3dcccccdU,0x3dcccccdU,0x3f59999aU,0x3f75c28fU,0x3f70a3d7U,0x3f6147aeU,0x3f19999aU}, std::int32_t{-1}, false},
    {"filter/oilPaint:oilPost", "defaults", "40c4579926bd60c4c8d1d46bdd8791d9ab70824cbf7f0b48a70394d0ab273b63", "527648c717ed3085055c027c784ced4afcff3639fd937d13d94a2fcf58d752f0",
     {0x3f4a6526U,0x00000000U,0x00000000U,0x3ee66666U,0x3e51e43fU,0x3f20f5b1U,0x00000000U,0x3f59999aU,0x3f800000U,0x3e0bf34fU,0x3ef6a03cU,0x3f19999aU}, std::int32_t{-1}, false},
    {"synth/gradient:gradient", "defaults", "a9374d8727bf4a656de27ee91c484cc65972520b0200fe991c2a978b24586798", "f6f9bd835e10212131848e6f78775abb190e22bdfa6d10140bda8d69aac876ab",
     {0x3f800000U,0x3f000001U,0x00000000U,0x3f800000U,0x3f800000U,0x3f800000U,0x00000000U,0x3f800000U,0x00000000U,0x3f346fecU,0x3e972028U,0x3f800000U}, std::int32_t{-1}, false},
    {"synth/mandala:mandala", "defaults", "e67605e30b716c1b6b81d98bd0819ed972aece818bcd78def3bbca8ad988db42", "994cb289e38c2f53b864d11eff3017269aa9f7a3324924d1d2ca299515d33b37",
     {0x00000000U,0x00000000U,0x00000000U,0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U,0x00000000U,0x00000000U,0x00000000U,0x3f800000U}, std::int32_t{-1}, false},
    {"synth/subdivide:subdivide", "defaults", "5370b447933cbacda5c53022dc2bd0b31a531ea7565ae4b5f93b53fb17221380", "dfd849d2041931900a7789de24b9ebb1455eef8b12f70d461c222238aac5ee47",
     {0x00000000U,0x00000000U,0x00000000U,0x3f800000U,0x00000000U,0x00000000U,0x00000000U,0x3f800000U,0x00000000U,0x00000000U,0x00000000U,0x3f800000U}, std::int32_t{-1}, false},
    {"filter/normalize:reduce", "defaults", "cf936f188b739c699cb21ee509484d2eb41eb94264905393b3fdfbd20feb7300", "6e74e7ac2187487b43ce8bd59c161079b59e33d20b5c2bdf7520675c22445f4a",
     {0x00000000U,0x3f800000U,0x00000000U,0x3f800000U,0x47c35000U,0xc7c35000U,0x00000000U,0x3f800000U,0x47c35000U,0xc7c35000U,0x00000000U,0x3f800000U}, std::int32_t{-1}, false},
    {"filter/normalize:reduceMinmax", "defaults", "cf936f188b739c699cb21ee509484d2eb41eb94264905393b3fdfbd20feb7300", "6e74e7ac2187487b43ce8bd59c161079b59e33d20b5c2bdf7520675c22445f4a",
     {0x00000000U,0x3f800000U,0x00000000U,0x3f800000U,0x47c35000U,0xc7c35000U,0x00000000U,0x3f800000U,0x47c35000U,0xc7c35000U,0x00000000U,0x3f800000U}, std::int32_t{-1}, false},
    {"filter/wormhole:blend", "defaults", "d91d31862d635d205daef23aa24f2bf0ea3c0b076892e048866a03a3e3a1ad40", "24f4e12bf3136e81b3c9a37de0eec59a54617c4126c875bf9986dbccbe33e060",
     {0x3f1a39e2U,0x3e146776U,0x3e68812eU,0x3ee66666U,0x3ef93682U,0x3f1d6807U,0x3e063c91U,0x3f733333U,0x3eaa80ddU,0x3ef349aaU,0x3f33ae0fU,0x3f4ccccdU}, std::int32_t{-1}, false},
    {"mixer/shadow:shadow", "defaults", "267fc2f1f4cc2a6edc718685296515cc089202516b7276dee475bc12f1e4447b", "d16ecc878da6dea7a47b1a79db89a8b8a71f16236a7a84bc0a651ade0e06a531",
     {0x3f170a3dU,0x3f500000U,0x3d3a2e8cU,0x3f000000U,0x3e720564U,0x3ec11a16U,0x3c8c7011U,0x3eb33333U,0x3e168e0bU,0x3e994382U,0x3f27325fU,0x3f59999aU}, std::int32_t{-1}, false},
    {"synth/cell:cell", "defaults", "ddc70ccd74dd789480cea64b55078e74de1f6d9a2493529a871a83e3bd779ded", "54106eec3b30630ae72ad785a67938716556cc76d39d62d66655aea1732c1cb8",
     {0x3d2726a1U,0x3d2726a1U,0x3d2726a1U,0x3f800000U,0x3e79af52U,0x3e79af52U,0x3e79af52U,0x3f800000U,0x3f2d6c0fU,0x3f2d6c0fU,0x3f2d6c0fU,0x3f800000U}, std::int32_t{-1}, false},
    {"mixer/mashup:mashup", "defaults", "51a1bc27355d0f8f973fd7ba742e798c85e8ad952a262a8353b137d828dee124", "7af2e319b78f42ef180cb59272c39b58a58db94a10d761c22f2de047e40bf84a",
     {0x3f170a3dU,0x3f500000U,0x3d3a2e8cU,0x3ee66666U,0x3e4ccccdU,0x3ec55555U,0x3e3a2e8cU,0x3f59999aU,0x3f51eb85U,0x3f780000U,0x3ea2e8baU,0x3f19999aU}, std::int32_t{-1}, false},
    {"mixer/cellSplit:cellSplit", "defaults", "34413d4fe5576274eb3c31679ff89268574d99d91c4ee74ed7b687a8ce0ec9a2", "de3b3fd0f60e1fb86fda2413627de0074b65320c475255804e64e34e9d27ca50",
     {0x3f3851ecU,0x3d2aaaabU,0x3dd1745dU,0x3f000000U,0x3eae147bU,0x3f02aaabU,0x3f7d1746U,0x3f733333U,0x3db851ecU,0x3e555555U,0x3f6ba2e9U,0x3f59999aU}, std::int32_t{-1}, false},
    {"filter/pixelSort:findBrightest", "defaults", "1f4f512dae03a136e3a1ccaa6486ed5f9c465f81a794cd13e7ee52d436d987f6", "f6e1ee496ad46d8e9c3b28c220350220e10635506a9676b33d2eed49f141ac7d",
     {0x3f4ccccdU,0x3f70a3d7U,0x00000000U,0x3f800000U,0x3f333333U,0x3f59999aU,0x00000000U,0x3f800000U,0x3f333333U,0x3f6e147bU,0x00000000U,0x3f800000U}, std::int32_t{-1}, false},
    {"filter/reverb:reverb", "defaults", "4471c5992a9a981ea5e9d34040a7ff082152049faa66f8984a4e162882e20456", "2bfa7ed25be5f11576de12d05398e80a68215def7a1745dac5cc138fe38126f7",
     {0x3f20418aU,0x3f3cccccU,0x3e942b72U,0x3f800000U,0x3eb490baU,0x3efe38e3U,0x3f2aaaacU,0x3f800000U,0x3eb8a94dU,0x3e0eeeefU,0x3f3ddddeU,0x3f800000U}, std::int32_t{-1}, false},
    {"filter/reverb:reverb", "iterations_1", "77ad0c710f1fc3b7bd02a60608c45aee20afe8f888dc85657aa4da7e5d9ba715", "7fc4c3cb18fab21e36851ed8aa46417ffe9b4d2210c75bfc8bfb5f35dfc51898",
     {0x3f281b4fU,0x3f51c71cU,0x3eaaaaabU,0x3f800000U,0x3ebf258cU,0x3ef8e38fU,0x3f383e10U,0x3f800000U,0x3e7c9630U,0x3e1c71c7U,0x3f400000U,0x3f800000U}, std::int32_t{1}, false},
    {"filter/reverb:reverb", "iterations_8", "dca36a6caa2e4c8ee95d73b8c68149fe7443f71c6c935487f282bf344c7697b5", "b97e993c5c4a092eb4bcd2a4791f777dd83b35b6aad1fdfa923d81af32861d1c",
     {0x3f2148f6U,0x3ed0b304U,0x3e23ba96U,0x3f800000U,0x3f1d1debU,0x3f4de6f2U,0x3e6a3aedU,0x3f800000U,0x3ecffc7aU,0x3e9c6387U,0x3ed033bcU,0x3f800000U}, std::int32_t{8}, true},
}};

struct Task15OracleUniform {
  std::string_view key;
  std::string_view name;
  Task15BindingType type;
  std::array<double, 3> value;
};

constexpr std::array<Task15OracleUniform, 189> kTask15OracleUniforms{{
    {"filter/chrome:chBlurH", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/chrome:chBlurH", "smoothness", Task15BindingType::scalar, {40.0, 0.0, 0.0}},
    {"filter/chrome:chBlurV", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/chrome:chBlurV", "smoothness", Task15BindingType::scalar, {40.0, 0.0, 0.0}},
    {"filter/clouds:clouds", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"filter/clouds:clouds", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"filter/clouds:clouds", "seed", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"filter/clouds:clouds", "scale", Task15BindingType::scalar, {0.250000000, 0.0, 0.0}},
    {"filter/clouds:clouds", "speed", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"filter/clouds:clouds", "time", Task15BindingType::scalar, {0.375000000, 0.0, 0.0}},
    {"filter/craquelure:craquelure", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/craquelure:craquelure", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"filter/craquelure:craquelure", "spacing", Task15BindingType::scalar, {40.0, 0.0, 0.0}},
    {"filter/craquelure:craquelure", "depth", Task15BindingType::scalar, {50.0, 0.0, 0.0}},
    {"filter/craquelure:craquelure", "brightness", Task15BindingType::scalar, {50.0, 0.0, 0.0}},
    {"filter/craquelure:craquelure", "seed", Task15BindingType::integer, {1.0, 0.0, 0.0}},
    {"filter/hatch:hatch", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/hatch:hatch", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"filter/hatch:hatch", "strokeLength", Task15BindingType::scalar, {50.0, 0.0, 0.0}},
    {"filter/hatch:hatch", "direction", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"filter/hatch:hatch", "balance", Task15BindingType::scalar, {50.0, 0.0, 0.0}},
    {"filter/hatch:hatch", "pressure", Task15BindingType::scalar, {50.0, 0.0, 0.0}},
    {"filter/hatch:hatch", "inkColor", Task15BindingType::vec3, {0.1, 0.1, 0.1}},
    {"filter/hatch:hatch", "paperColor", Task15BindingType::vec3, {0.96, 0.94, 0.88}},
    {"filter/highPass:hpBlurH", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/highPass:hpBlurH", "radius", Task15BindingType::scalar, {10.0, 0.0, 0.0}},
    {"filter/highPass:hpBlurV", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/highPass:hpBlurV", "radius", Task15BindingType::scalar, {10.0, 0.0, 0.0}},
    {"filter/lowPoly:lowPoly", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"filter/lowPoly:lowPoly", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"filter/lowPoly:lowPoly", "scale", Task15BindingType::scalar, {50.0, 0.0, 0.0}},
    {"filter/lowPoly:lowPoly", "seed", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"filter/lowPoly:lowPoly", "mode", Task15BindingType::integer, {1.0, 0.0, 0.0}},
    {"filter/lowPoly:lowPoly", "edgeStrength", Task15BindingType::scalar, {0.15, 0.0, 0.0}},
    {"filter/lowPoly:lowPoly", "edgeColor", Task15BindingType::vec3, {0.0, 0.0, 0.0}},
    {"filter/lowPoly:lowPoly", "speed", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"filter/lowPoly:lowPoly", "time", Task15BindingType::scalar, {0.375000000, 0.0, 0.0}},
    {"filter/lowPoly:lowPoly", "alpha", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"filter/morphology:morphA", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/morphology:morphA", "mode", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"filter/morphology:morphA", "radius", Task15BindingType::scalar, {4.0, 0.0, 0.0}},
    {"filter/morphology:morphB", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/morphology:morphB", "mode", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"filter/morphology:morphB", "radius", Task15BindingType::scalar, {4.0, 0.0, 0.0}},
    {"filter/normalize:reduce", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"filter/normalize:reduce", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"filter/normalize:reduceMinmax", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"filter/normalize:reduceMinmax", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"filter/oilPaint:oilPost", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/oilPaint:oilPost", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"filter/oilPaint:oilPost", "size", Task15BindingType::scalar, {6.0, 0.0, 0.0}},
    {"filter/oilPaint:oilPost", "detail", Task15BindingType::scalar, {50.0, 0.0, 0.0}},
    {"filter/oilPaint:oilPost", "textureAmount", Task15BindingType::scalar, {20.0, 0.0, 0.0}},
    {"filter/oilPaint:oilPost", "seed", Task15BindingType::integer, {1.0, 0.0, 0.0}},
    {"filter/patchwork:patchwork", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/patchwork:patchwork", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"filter/patchwork:patchwork", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"filter/patchwork:patchwork", "squareSize", Task15BindingType::scalar, {16.0, 0.0, 0.0}},
    {"filter/patchwork:patchwork", "relief", Task15BindingType::scalar, {50.0, 0.0, 0.0}},
    {"filter/patchwork:patchwork", "lightAngle", Task15BindingType::scalar, {135.0, 0.0, 0.0}},
    {"filter/photocopy:pcBlurH", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/photocopy:pcBlurH", "detail", Task15BindingType::scalar, {30.0, 0.0, 0.0}},
    {"filter/photocopy:pcBlurV", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/photocopy:pcBlurV", "detail", Task15BindingType::scalar, {30.0, 0.0, 0.0}},
    {"filter/plasticWrap:pwBlurH", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/plasticWrap:pwBlurH", "detail", Task15BindingType::scalar, {40.0, 0.0, 0.0}},
    {"filter/plasticWrap:pwBlurV", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/plasticWrap:pwBlurV", "detail", Task15BindingType::scalar, {40.0, 0.0, 0.0}},
    {"filter/relief:rlBlurH", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/relief:rlBlurH", "smoothness", Task15BindingType::scalar, {30.0, 0.0, 0.0}},
    {"filter/relief:rlBlurV", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/relief:rlBlurV", "smoothness", Task15BindingType::scalar, {30.0, 0.0, 0.0}},
    {"filter/reverb:reverb", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"filter/reverb:reverb", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"filter/reverb:reverb", "iterations", Task15BindingType::integer, {3.0, 0.0, 0.0}},
    {"filter/reverb:reverb", "ridges", Task15BindingType::boolean, {0.0, 0.0, 0.0}},
    {"filter/reverb:reverb", "alpha", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"filter/reverb:reverb", "wrap", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"filter/scatter:scatterSmooth", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/scatter:scatterSmooth", "smoothness", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"filter/stamp:stBlurH", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/stamp:stBlurH", "smoothness", Task15BindingType::scalar, {30.0, 0.0, 0.0}},
    {"filter/stamp:stBlurV", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/stamp:stBlurV", "smoothness", Task15BindingType::scalar, {30.0, 0.0, 0.0}},
    {"filter/strokes:stkPost", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/strokes:stkPost", "sharpness", Task15BindingType::scalar, {30.0, 0.0, 0.0}},
    {"filter/unsharpMask:usmBlurH", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/unsharpMask:usmBlurH", "radius", Task15BindingType::scalar, {4.0, 0.0, 0.0}},
    {"filter/unsharpMask:usmBlurV", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/unsharpMask:usmBlurV", "radius", Task15BindingType::scalar, {4.0, 0.0, 0.0}},
    {"filter/wormhole:blend", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/wormhole:blend", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"filter/wormhole:blend", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"filter/wormhole:blend", "alpha", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"mixer/cellSplit:cellSplit", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"mixer/cellSplit:cellSplit", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"mixer/cellSplit:cellSplit", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"mixer/cellSplit:cellSplit", "mode", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"mixer/cellSplit:cellSplit", "scale", Task15BindingType::scalar, {15.0, 0.0, 0.0}},
    {"mixer/cellSplit:cellSplit", "edgeWidth", Task15BindingType::scalar, {0.08, 0.0, 0.0}},
    {"mixer/cellSplit:cellSplit", "seed", Task15BindingType::integer, {1.0, 0.0, 0.0}},
    {"mixer/cellSplit:cellSplit", "invert", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"mixer/cellSplit:cellSplit", "time", Task15BindingType::scalar, {0.375000000, 0.0, 0.0}},
    {"mixer/cellSplit:cellSplit", "speed", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"mixer/mashup:mashup", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"mixer/mashup:mashup", "layers", Task15BindingType::integer, {4.0, 0.0, 0.0}},
    {"mixer/mashup:mashup", "smoothness", Task15BindingType::scalar, {0.1, 0.0, 0.0}},
    {"mixer/mashup:mashup", "layer0_active", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"mixer/mashup:mashup", "layer1_active", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"mixer/mashup:mashup", "layer2_active", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"mixer/mashup:mashup", "layer3_active", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"mixer/mashup:mashup", "layer4_active", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"mixer/mashup:mashup", "layer5_active", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"mixer/mashup:mashup", "layer6_active", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"mixer/mashup:mashup", "layer7_active", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"mixer/shadow:shadow", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"mixer/shadow:shadow", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"mixer/shadow:shadow", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"mixer/shadow:shadow", "renderScale", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"mixer/shadow:shadow", "maskSource", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"mixer/shadow:shadow", "sourceChannel", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"mixer/shadow:shadow", "threshold", Task15BindingType::scalar, {0.500000000, 0.0, 0.0}},
    {"mixer/shadow:shadow", "color", Task15BindingType::vec3, {0.0, 0.0, 0.0}},
    {"mixer/shadow:shadow", "offsetX", Task15BindingType::scalar, {0.1, 0.0, 0.0}},
    {"mixer/shadow:shadow", "offsetY", Task15BindingType::scalar, {-0.1, 0.0, 0.0}},
    {"mixer/shadow:shadow", "blur", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"mixer/shadow:shadow", "spread", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"mixer/shadow:shadow", "wrap", Task15BindingType::integer, {1.0, 0.0, 0.0}},
    {"synth/cell:cell", "time", Task15BindingType::scalar, {0.375000000, 0.0, 0.0}},
    {"synth/cell:cell", "seed", Task15BindingType::integer, {1.0, 0.0, 0.0}},
    {"synth/cell:cell", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"synth/cell:cell", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"synth/cell:cell", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"synth/cell:cell", "renderScale", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"synth/cell:cell", "metric", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"synth/cell:cell", "scale", Task15BindingType::scalar, {75.0, 0.0, 0.0}},
    {"synth/cell:cell", "cellScale", Task15BindingType::scalar, {87.0, 0.0, 0.0}},
    {"synth/cell:cell", "cellSmooth", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"synth/cell:cell", "variation", Task15BindingType::scalar, {50.0, 0.0, 0.0}},
    {"synth/cell:cell", "speed", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"synth/gradient:gradient", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"synth/gradient:gradient", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"synth/gradient:gradient", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"synth/gradient:gradient", "gradientType", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"synth/gradient:gradient", "rotation", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"synth/gradient:gradient", "repeat", Task15BindingType::integer, {1.0, 0.0, 0.0}},
    {"synth/gradient:gradient", "colorCount", Task15BindingType::integer, {4.0, 0.0, 0.0}},
    {"synth/gradient:gradient", "color1", Task15BindingType::vec3, {1.0, 0.0, 0.0}},
    {"synth/gradient:gradient", "color2", Task15BindingType::vec3, {1.0, 1.0, 0.0}},
    {"synth/gradient:gradient", "color3", Task15BindingType::vec3, {0.0, 1.0, 0.0}},
    {"synth/gradient:gradient", "color4", Task15BindingType::vec3, {0.0, 0.0, 1.0}},
    {"synth/gradient:gradient", "seed", Task15BindingType::integer, {1.0, 0.0, 0.0}},
    {"synth/gradient:gradient", "time", Task15BindingType::scalar, {0.375000000, 0.0, 0.0}},
    {"synth/gradient:gradient", "speed", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"synth/mandala:mandala", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"synth/mandala:mandala", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"synth/mandala:mandala", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"synth/mandala:mandala", "aspect", Task15BindingType::scalar, {1.2857142686843872, 0.0, 0.0}},
    {"synth/mandala:mandala", "scale", Task15BindingType::scalar, {10.0, 0.0, 0.0}},
    {"synth/mandala:mandala", "rotation", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"synth/mandala:mandala", "thickness", Task15BindingType::scalar, {0.2, 0.0, 0.0}},
    {"synth/mandala:mandala", "smoothness", Task15BindingType::scalar, {0.02, 0.0, 0.0}},
    {"synth/mandala:mandala", "symmetry", Task15BindingType::integer, {12.0, 0.0, 0.0}},
    {"synth/mandala:mandala", "layers", Task15BindingType::integer, {6.0, 0.0, 0.0}},
    {"synth/mandala:mandala", "shape", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"synth/mandala:mandala", "layerSpacing", Task15BindingType::scalar, {1.50000000, 0.0, 0.0}},
    {"synth/mandala:mandala", "twist", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"synth/mandala:mandala", "shapeGrowth", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"synth/mandala:mandala", "bindu", Task15BindingType::boolean, {0.0, 0.0, 0.0}},
    {"synth/mandala:mandala", "animation", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"synth/mandala:mandala", "speed", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"synth/mandala:mandala", "pulseDepth", Task15BindingType::scalar, {0.15, 0.0, 0.0}},
    {"synth/mandala:mandala", "time", Task15BindingType::scalar, {0.375000000, 0.0, 0.0}},
    {"synth/mandala:mandala", "fgColor", Task15BindingType::vec3, {1.0, 1.0, 1.0}},
    {"synth/mandala:mandala", "bgColor", Task15BindingType::vec3, {0.0, 0.0, 0.0}},
    {"synth/subdivide:subdivide", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"synth/subdivide:subdivide", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"synth/subdivide:subdivide", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"synth/subdivide:subdivide", "renderScale", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"synth/subdivide:subdivide", "mode", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"synth/subdivide:subdivide", "depth", Task15BindingType::scalar, {5.0, 0.0, 0.0}},
    {"synth/subdivide:subdivide", "density", Task15BindingType::scalar, {75.0, 0.0, 0.0}},
    {"synth/subdivide:subdivide", "seed", Task15BindingType::scalar, {69.0, 0.0, 0.0}},
    {"synth/subdivide:subdivide", "fill", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"synth/subdivide:subdivide", "outline", Task15BindingType::scalar, {3.0, 0.0, 0.0}},
    {"synth/subdivide:subdivide", "inputMix", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"synth/subdivide:subdivide", "wrap", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"synth/subdivide:subdivide", "time", Task15BindingType::scalar, {0.375000000, 0.0, 0.0}},
    {"synth/subdivide:subdivide", "speed", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
}};

TEST(typed_task15_scalar_fixture_precision_tracks_binding_provenance) {
  const auto value = [](std::string_view key, std::string_view name) {
    for (const Task15OracleUniform& uniform : kTask15OracleUniforms)
      if (uniform.key == key && uniform.name == name) return uniform.value[0];
    throw std::invalid_argument("missing Task 15 scalar fixture");
  };
  // Effect metadata remains a JavaScript Number, while renderer context
  // scalars such as aspect are stored through a Float32Array first.
  REQUIRE(value("filter/lowPoly:lowPoly", "edgeStrength") == 0.15);
  REQUIRE(value("synth/mandala:mandala", "aspect") ==
          static_cast<double>(static_cast<float>(9.0 / 7.0)));
}

struct Task15SamplerRoute {
  std::string_view key;
  std::string_view name;
  std::size_t tag;
};

constexpr std::array<Task15SamplerRoute, 46> kTask15SamplerRoutes{{
    {"filter/chrome:chBlurH", "inputTex", 1U},
    {"filter/chrome:chBlurV", "inputTex", 1U},
    {"filter/highPass:hpBlurH", "inputTex", 1U},
    {"filter/highPass:hpBlurV", "inputTex", 1U},
    {"filter/morphology:morphA", "inputTex", 1U},
    {"filter/morphology:morphB", "inputTex", 1U},
    {"filter/photocopy:pcBlurH", "inputTex", 1U},
    {"filter/photocopy:pcBlurV", "inputTex", 1U},
    {"filter/plasticWrap:pwBlurH", "inputTex", 1U},
    {"filter/plasticWrap:pwBlurV", "inputTex", 1U},
    {"filter/relief:rlBlurH", "inputTex", 1U},
    {"filter/relief:rlBlurV", "inputTex", 1U},
    {"filter/stamp:stBlurH", "inputTex", 1U},
    {"filter/stamp:stBlurV", "inputTex", 1U},
    {"filter/unsharpMask:usmBlurH", "inputTex", 1U},
    {"filter/unsharpMask:usmBlurV", "inputTex", 1U},
    {"filter/craquelure:craquelure", "inputTex", 1U},
    {"filter/lowPoly:lowPoly", "inputTex", 1U},
    {"filter/patchwork:patchwork", "inputTex", 1U},
    {"filter/scatter:scatterSmooth", "inputTex", 1U},
    {"filter/strokes:stkPost", "inputTex", 1U},
    {"filter/strokes:stkPost", "smearTex", 2U},
    {"filter/clouds:clouds", "inputTex", 1U},
    {"filter/hatch:hatch", "inputTex", 1U},
    {"filter/oilPaint:oilPost", "inputTex", 1U},
    {"filter/oilPaint:oilPost", "flatTex", 2U},
    {"synth/subdivide:subdivide", "inputTex", 1U},
    {"filter/normalize:reduce", "inputTex", 1U},
    {"filter/normalize:reduceMinmax", "inputTex", 1U},
    {"filter/wormhole:blend", "inputTex", 1U},
    {"filter/wormhole:blend", "accumTex", 2U},
    {"mixer/shadow:shadow", "inputTex", 1U},
    {"mixer/shadow:shadow", "tex", 2U},
    {"mixer/mashup:mashup", "source", 1U},
    {"mixer/mashup:mashup", "layer0_tex", 2U},
    {"mixer/mashup:mashup", "layer1_tex", 3U},
    {"mixer/mashup:mashup", "layer2_tex", 4U},
    {"mixer/mashup:mashup", "layer3_tex", 5U},
    {"mixer/mashup:mashup", "layer4_tex", 6U},
    {"mixer/mashup:mashup", "layer5_tex", 7U},
    {"mixer/mashup:mashup", "layer6_tex", 8U},
    {"mixer/mashup:mashup", "layer7_tex", 9U},
    {"mixer/cellSplit:cellSplit", "inputTex", 1U},
    {"mixer/cellSplit:cellSplit", "tex", 2U},
    {"filter/pixelSort:findBrightest", "lumTex", 1U},
    {"filter/reverb:reverb", "inputTex", 1U},
}};

[[nodiscard]] noisemaker::Surface task15_formula_surface(std::size_t tag) {
  std::vector<float> data(11U * 9U * 4U);
  for (std::size_t y = 0; y < 9U; ++y) for (std::size_t x = 0; x < 11U; ++x) {
    const std::size_t lane = (y * 11U + x) * 4U;
    data[lane] = static_cast<float>(static_cast<double>((x * 17U + y * 31U + tag * 13U) % 101U) / 100.0);
    data[lane + 1U] = static_cast<float>(static_cast<double>((x * 7U + y * 19U + tag * 23U) % 97U) / 96.0);
    data[lane + 2U] = static_cast<float>(static_cast<double>((x * 29U + y * 11U + tag * 5U) % 89U) / 88.0);
    data[lane + 3U] = static_cast<float>(0.35 + static_cast<double>((x * 3U + y * 5U + tag) % 13U) / 20.0);
  }
  return noisemaker::Surface(11U, 9U, std::move(data));
}

void populate_task15_oracle_bindings(
    noisemaker::glsl::Bindings& bindings, const Task15OracleCase& fixture,
    const std::array<noisemaker::Surface, 9>& surfaces) {
  for (const Task15SamplerRoute& route : kTask15SamplerRoutes)
    if (route.key == fixture.key)
      bindings.set_texture(std::string(route.name), surfaces[route.tag - 1U]);
  for (const Task15OracleUniform& uniform : kTask15OracleUniforms) {
    if (uniform.key != fixture.key) continue;
    const std::string name(uniform.name);
    switch (uniform.type) {
      case Task15BindingType::scalar: bindings.set_uniform(name, uniform.value[0]); break;
      case Task15BindingType::integer:
        bindings.set_uniform(name, static_cast<std::int32_t>(uniform.value[0])); break;
      case Task15BindingType::boolean: bindings.set_uniform(name, uniform.value[0] != 0.0); break;
      case Task15BindingType::vec2:
        bindings.set_uniform(name, noisemaker::glsl::Vec2(uniform.value[0], uniform.value[1])); break;
      case Task15BindingType::vec3:
        bindings.set_uniform(name, noisemaker::glsl::Vec3(uniform.value[0], uniform.value[1], uniform.value[2])); break;
      case Task15BindingType::sampler: throw std::logic_error("sampler in Task 15 uniform table");
    }
  }
  if (fixture.iterations_override >= 0)
    bindings.set_uniform("iterations", fixture.iterations_override);
  if (fixture.ridges_override) bindings.set_uniform("ridges", true);
}

[[nodiscard]] noisemaker::Surface render_task15_oracle(
    const Task15OracleCase& fixture, const std::array<noisemaker::Surface, 9>& surfaces) {
  noisemaker::glsl::Bindings bindings;
  populate_task15_oracle_bindings(bindings, fixture, surfaces);
  const noisemaker::BoundKernel kernel = noisemaker::generated::bind(fixture.key, bindings);
  noisemaker::Surface result(9U, 7U);
  auto output = result.data();
  for (std::size_t y = 0; y < 7U; ++y) for (std::size_t x = 0; x < 9U; ++x) {
    const noisemaker::glsl::Vec4 frag_coord(static_cast<float>(x) + 0.5f,
                                             static_cast<float>(y) + 0.5f, 0.0f, 1.0f);
    const noisemaker::glsl::PixelContext context{
        .uv = noisemaker::glsl::Vec2(frag_coord[0] / 9.0f, frag_coord[1] / 7.0f),
        .frag_coord = frag_coord, .resolution = noisemaker::glsl::Vec2(9.0f, 7.0f),
        .time = 0.375f, .seed = 19.0f, .frame = 7U, .delta_time = 1.0f / 60.0f};
    noisemaker::glsl::Vec4 pixel;
    kernel.run_pixel(context, pixel);
    const std::size_t offset = (y * 9U + x) * 4U;
    for (std::size_t lane = 0; lane < 4U; ++lane) output[offset + lane] = pixel[lane];
  }
  return result;
}

TEST(typed_task15_all_thirty_eight_external_oracles_are_exact_and_repeatable) {
  const std::array surfaces{
      task15_formula_surface(1U), task15_formula_surface(2U), task15_formula_surface(3U),
      task15_formula_surface(4U), task15_formula_surface(5U), task15_formula_surface(6U),
      task15_formula_surface(7U), task15_formula_surface(8U), task15_formula_surface(9U)};
  constexpr std::array<std::size_t, 3> pixels{0U, 31U, 62U};
  for (const Task15OracleCase& fixture : kTask15OracleCases) {
    const noisemaker::Surface first = render_task15_oracle(fixture, surfaces);
    const noisemaker::Surface second = render_task15_oracle(fixture, surfaces);
    REQUIRE(first.width() == 9U); REQUIRE(first.height() == 7U);
    const std::string name = std::string(fixture.key) + "/" + std::string(fixture.variant);
    const std::string float_hash = hex(sha256(little_endian_float_bytes(first)));
    if (float_hash != fixture.float_hash) {
      std::ostringstream detail;
      detail << name << " float oracle hash: " << float_hash << " probes:";
      for (std::size_t pixel : pixels) for (std::size_t lane = 0; lane < 4U; ++lane)
        detail << ' ' << std::hex << noisemaker::float_bits_to_uint(first.data()[pixel * 4U + lane]);
      throw std::runtime_error(detail.str());
    }
    const std::string rgba_hash = hex(sha256(first.to_rgba8()));
    if (rgba_hash != fixture.rgba_hash)
      throw std::runtime_error(name + " rgba oracle hash: " + rgba_hash);
    for (std::size_t probe = 0; probe < pixels.size(); ++probe)
      for (std::size_t lane = 0; lane < 4U; ++lane)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[pixels[probe] * 4U + lane]) ==
                fixture.probes[probe * 4U + lane]);
    require_repeat(first, second);
  }
}

[[nodiscard]] noisemaker::Surface task16_formula_surface() {
  std::vector<float> data(11U * 9U * 4U);
  for (std::size_t y = 0; y < 9U; ++y) for (std::size_t x = 0; x < 11U; ++x) {
    const std::size_t lane = (y * 11U + x) * 4U;
    data[lane] = static_cast<float>(static_cast<double>((17U * x + 31U * y + 13U) % 101U) / 100.0);
    data[lane + 1U] = static_cast<float>(static_cast<double>((7U * x + 19U * y + 23U) % 97U) / 96.0);
    data[lane + 2U] = static_cast<float>(static_cast<double>((29U * x + 11U * y + 5U) % 89U) / 88.0);
    data[lane + 3U] = static_cast<float>(0.35 + static_cast<double>((3U * x + 5U * y + 1U) % 13U) / 20.0);
  }
  return noisemaker::Surface(11U, 9U, std::move(data));
}

[[nodiscard]] noisemaker::Surface task16_flat_surface(std::size_t width,
                                                       std::size_t height) {
  noisemaker::Surface result(width, height);
  auto data = result.data();
  for (std::size_t lane = 0; lane < data.size(); lane += 4U) {
    data[lane] = 0.5f; data[lane + 1U] = 0.25f;
    data[lane + 2U] = 0.75f; data[lane + 3U] = 1.0f;
  }
  return result;
}

[[nodiscard]] noisemaker::Surface render_task16(const noisemaker::Surface& input,
                                                 std::size_t width,
                                                 std::size_t height) {
  noisemaker::glsl::Bindings bindings;
  bindings.set_texture("lumTex", input);
  return noisemaker::run_pass(noisemaker::generated::bind(
      "filter/pixelSort:computeRank", bindings), width, height);
}

TEST(typed_task16_compute_rank_external_oracles_are_exact_and_repeatable) {
  struct Fixture {
    std::string_view name;
    noisemaker::Surface input;
    std::size_t width;
    std::size_t height;
    std::string_view float_hash;
    std::string_view rgba_hash;
    std::array<std::uint32_t, 12> probes;
  };
  std::array<Fixture, 2> fixtures{{
      {"formula", task16_formula_surface(), 9U, 7U,
       "b232b1b98b9d973eed9b21ffabfe2039974f4e431269fe05d1ed9741b0e06bf3",
       "f9021ce571b2f8234509a7df8f9ec2379cb91db4aa56c42dab39f3a0657cfce6",
       {0x3e900000U,0x3f400000U,0x00000000U,0x3f800000U,
        0x3f080000U,0x3eae147bU,0x3ecccccdU,0x3f800000U,
        0x00000000U,0x3f70a3d7U,0x3f4ccccdU,0x3f800000U}},
      {"flat-tie", task16_flat_surface(11U, 9U), 9U, 7U,
       "37826c52ed556af08540665ec5435fd99188af1aeb525900647b710f0ecf800f",
       "472adcee73849262e3cc7ce4a7bcfdfbb2e4191f7c51e6d49ab4e02404e8d753",
       {0x00000000U,0x3f000000U,0x00000000U,0x3f800000U,
        0x3ec00000U,0x3f000000U,0x3ecccccdU,0x3f800000U,
        0x3f400000U,0x3f000000U,0x3f4ccccdU,0x3f800000U}},
  }};
  constexpr std::array<std::size_t, 3> pixels{0U, 31U, 62U};
  for (const Fixture& fixture : fixtures) {
    const noisemaker::Surface first = render_task16(
        fixture.input, fixture.width, fixture.height);
    const noisemaker::Surface second = render_task16(
        fixture.input, fixture.width, fixture.height);
    REQUIRE(hex(sha256(little_endian_float_bytes(first))) == fixture.float_hash);
    REQUIRE(hex(sha256(first.to_rgba8())) == fixture.rgba_hash);
    for (std::size_t probe = 0; probe < pixels.size(); ++probe)
      for (std::size_t lane = 0; lane < 4U; ++lane)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[pixels[probe] * 4U + lane]) ==
                fixture.probes[probe * 4U + lane]);
    require_repeat(first, second);
  }
}

TEST(typed_task16_compute_rank_width_one_preserves_canonical_quiet_nan) {
  const noisemaker::Surface input = task16_flat_surface(1U, 1U);
  const noisemaker::Surface first = render_task16(input, 1U, 1U);
  const noisemaker::Surface second = render_task16(input, 1U, 1U);
  REQUIRE(hex(sha256(little_endian_float_bytes(first))) ==
          "24f56616adaf6242697f97e5d9420c4bafa1529c99e8e053b9dc0cb6bc87341c");
  REQUIRE(hex(sha256(first.to_rgba8())) ==
          "1f71b62d981be40a6adc0ccd7ef62b6bc47317c7a1de96d4b934f761b67b135e");
  REQUIRE(noisemaker::float_bits_to_uint(first.data()[0]) == 0x00000000U);
  REQUIRE(noisemaker::float_bits_to_uint(first.data()[1]) == 0x3f000000U);
  REQUIRE(std::isnan(first.data()[2]));
  REQUIRE(noisemaker::float_bits_to_uint(first.data()[2]) == 0x7fc00000U);
  REQUIRE(noisemaker::float_bits_to_uint(first.data()[3]) == 0x3f800000U);
  REQUIRE(first.to_rgba8()[2] == 0U);
  require_repeat(first, second);
}

struct Task17Case {
  std::string_view name;
  std::string_view key;
  float amount;
  float alpha;
  std::string_view float_hash;
  std::string_view rgba_hash;
  std::array<std::uint32_t, 12> probes;
};

[[nodiscard]] noisemaker::Surface render_task17(const Task17Case& fixture) {
  const noisemaker::Surface input = task16_formula_surface();
  noisemaker::glsl::Bindings bindings;
  bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(2.0f, 1.0f));
  bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(13.0f, 11.0f));
  bindings.set_texture("inputTex", input);
  bindings.set_uniform("amount", fixture.amount);
  bindings.set_uniform("renderScale", 1.0f);
  if (fixture.key == "filter/sobel:sobel") bindings.set_uniform("alpha", fixture.alpha);
  return noisemaker::run_pass(noisemaker::generated::bind(fixture.key, bindings),
                              9U, 7U, 0.375f, 19.0f, 7U, 1.0f / 60.0f);
}

TEST(typed_task17_sharpen_and_sobel_external_oracles_are_exact_and_repeatable) {
  const float amount_2_3 = noisemaker::uint_bits_to_float(0x40133333U);
  const std::array<Task17Case, 4> fixtures{{
      {"sharpen-default", "filter/sharpen:sharpen", 1.0f, 0.0f,
       "54bffb81920b79c85198238c2fcd4f52b94ae25ca208747fb0048f24a71b05ec",
       "d1bd7b35b2890258c385d294879556b4586d33f4af29feeeb7be5a4931ec2094",
       {0x3f800000U,0x3efaaab2U,0x00000000U,0x3f666666U,
        0x00000000U,0x3f02aaacU,0x3f800000U,0x3f733333U,
        0x3f800000U,0x3f47fffeU,0x3f68ba2eU,0x3eb33333U}},
      {"sharpen-amount-2.3f", "filter/sharpen:sharpen", amount_2_3, 0.0f,
       "53f12c6e6047f31edb9e157202674a405489df96dd995adcc3bf4aea5a20128f",
       "560e7225289764f8d2c108b3f0746859ceb38ce4dee47753710d6d18473101e3",
       {0x3f800000U,0x3f800000U,0x3dd1745cU,0x3f666666U,
        0x00000000U,0x3f02aaacU,0x3f800000U,0x3f733333U,
        0x3f800000U,0x00000000U,0x3f800000U,0x3eb33333U}},
      {"sobel-default-alpha-one", "filter/sobel:sobel", 1.0f, 1.0f,
       "df429cbfeb9dc04d3e5f9099ded0daae9ee7077a9121e325a11fb0cd9ac380dd",
       "6841efab285a153de30bebaad4a6550107a1de719c37337a159ef07667d76777",
       {0x401537a7U,0x3ffcd731U,0x3f742c86U,0x3f666666U,
        0x3fa25fdaU,0x3ff3c2b9U,0x406c128cU,0x3f733333U,
        0x405f7e1aU,0x3fb74597U,0x401cb446U,0x3eb33333U}},
      {"sobel-amount-2.3f-alpha-zero", "filter/sobel:sobel", amount_2_3, 0.0f,
       "f7e50759990c46d868b22bdf83241e3866b14a6406fee043b8cad46cbea6b1d8",
       "05f02465cc5eacd61320b5d1b304f4b8face9993f604f540466d9582075bb3e0",
       {0x3f400000U,0x3f22aaabU,0x3e9d1746U,0x3f666666U,
        0x3eae147bU,0x3f02aaabU,0x3f7d1746U,0x3f733333U,
        0x3f70a3d7U,0x3ec55555U,0x3f28ba2fU,0x3eb33333U}},
  }};
  constexpr std::array<std::size_t, 3> pixels{0U, 31U, 62U};
  for (const Task17Case& fixture : fixtures) {
    const noisemaker::Surface first = render_task17(fixture);
    const noisemaker::Surface second = render_task17(fixture);
    require_repeat(first, second);
    REQUIRE(first.width() == 9U); REQUIRE(first.height() == 7U);
    REQUIRE(hex(sha256(little_endian_float_bytes(first))) == fixture.float_hash);
    REQUIRE(hex(sha256(first.to_rgba8())) == fixture.rgba_hash);
    for (std::size_t probe = 0; probe < pixels.size(); ++probe)
      for (std::size_t lane = 0; lane < 4U; ++lane)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[pixels[probe] * 4U + lane]) ==
                fixture.probes[probe * 4U + lane]);
  }
}

[[nodiscard]] noisemaker::Surface task18_formula_surface() {
  std::vector<float> data(7U * 5U * 4U);
  for (std::size_t y = 0; y < 5U; ++y) for (std::size_t x = 0; x < 7U; ++x) {
    const std::size_t lane = (y * 7U + x) * 4U;
    data[lane] = static_cast<float>(
        0.035 + (static_cast<double>((17U * x + 31U * y + 13U) % 101U) / 100.0) * 0.22);
    data[lane + 1U] = static_cast<float>(
        0.020 + (static_cast<double>((7U * x + 19U * y + 23U) % 97U) / 96.0) * 0.26);
    data[lane + 2U] = static_cast<float>(
        0.010 + (static_cast<double>((29U * x + 11U * y + 5U) % 89U) / 88.0) * 0.20);
    data[lane + 3U] = static_cast<float>(
        0.350 + static_cast<double>((3U * x + 5U * y + 1U) % 13U) / 20.0);
  }
  return noisemaker::Surface(7U, 5U, std::move(data));
}

struct Task18Case {
  std::string_view name;
  std::string_view key;
  float parameter;
  std::string_view float_hash;
  std::string_view rgba_hash;
  std::array<std::uint32_t, 12> probes;
};

[[nodiscard]] noisemaker::Surface render_task18(const Task18Case& fixture) {
  const noisemaker::Surface input = task18_formula_surface();
  noisemaker::glsl::Bindings bindings;
  bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(3.0f, 2.0f));
  bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(12.0f, 10.0f));
  if (fixture.key == "filter/celShading:celShadingEdges") {
    bindings.set_texture("colorTex", input);
    bindings.set_uniform("edgeWidth", noisemaker::uint_bits_to_float(0x40133333U));
    bindings.set_uniform("edgeThreshold", fixture.parameter);
  } else {
    bindings.set_texture("valueTexture", input);
    bindings.set_uniform("sobelMetric", fixture.parameter);
    bindings.set_uniform("thickness", noisemaker::uint_bits_to_float(0x40133333U));
  }
  bindings.set_uniform("renderScale", 1.0f);
  return noisemaker::run_pass(noisemaker::generated::bind(fixture.key, bindings),
                              9U, 7U, 0.375f, 19.0f, 7U, 1.0f / 60.0f);
}

TEST(typed_task18_cel_edges_and_outline_sobel_external_oracles_are_exact_and_repeatable) {
  const std::array<Task18Case, 6> fixtures{{
      {"cel-threshold-0.18f", "filter/celShading:celShadingEdges",
       noisemaker::uint_bits_to_float(0x3e3851ecU),
       "d86694f5c5a05c094b1dc9d4302b0b98cbe3044e5ce22587fdf6dd80f77d27a7",
       "966ca81461240fb6c35316537f631f3b74b6d0a33a7b538d05ddd12e241347e9",
       {0x3f074202U,0x3f074202U,0x3f074202U,0x3f800000U,
        0x3d038558U,0x3d038558U,0x3d038558U,0x3f800000U,
        0x00000000U,0x00000000U,0x00000000U,0x3f800000U}},
      {"cel-threshold-0.6f", "filter/celShading:celShadingEdges",
       noisemaker::uint_bits_to_float(0x3f19999aU),
       "048acf6f8feb3be40c9be548bc64eaeadc6de78366a61b778c899eb463575ac0",
       "8d0418a7e7b046d582cafcfbbe95b1bf2c05478929a57719ab52a345de1091e5",
       {0x00000000U,0x00000000U,0x00000000U,0x3f800000U,
        0x00000000U,0x00000000U,0x00000000U,0x3f800000U,
        0x00000000U,0x00000000U,0x00000000U,0x3f800000U}},
      {"outline-metric-1", "filter/outline:outlineSobel", 1.0f,
       "2e62cf4918bb2da1def8b146c4e33ef009d6c6ef05f96bf2d0fd2be4e7679a7f",
       "a877af8b8229c67295f3c17123cbaa5a540e59e81a3f95af9db601be5b2eca90",
       {0x3f6dc0cdU,0x3f6dc0cdU,0x3f6dc0cdU,0x3f800000U,
        0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U,
        0x3f64f78aU,0x3f64f78aU,0x3f64f78aU,0x3f800000U}},
      {"outline-metric-2", "filter/outline:outlineSobel", 2.0f,
       "afac987ef587a22d89ed00f619edb97e29d321fb2cc57667ceea89c0d78744b0",
       "e01ac082638be9679283946c758e093c5ea966bc79b8acdf14d8ee1213f084f8",
       {0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U,
        0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U,
        0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U}},
      {"outline-metric-3", "filter/outline:outlineSobel", 3.0f,
       "33eb93deef5ea41a7f085c4d3e9d8f4d5c3b4353b8490f0b9e0bbd2466c1d1ff",
       "8c3a62bd220bf6321d1127ab2cb1823522ffe38e9e07f985af9aceb9e64a253c",
       {0x3f6809d4U,0x3f6809d4U,0x3f6809d4U,0x3f800000U,
        0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U,
        0x3f5f06f7U,0x3f5f06f7U,0x3f5f06f7U,0x3f800000U}},
      {"outline-metric-4", "filter/outline:outlineSobel", 4.0f,
       "a4293babe12252aa6e0f4c4b50f6242ef4a1060297a40a1da12a549ea9c77047",
       "db8a0a072ec1c5e85d8678100929a1ef5ecf5c6ffc88217536354d06f4a11f74",
       {0x3f6809d4U,0x3f6809d4U,0x3f6809d4U,0x3f800000U,
        0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U,
        0x3f5f06f7U,0x3f5f06f7U,0x3f5f06f7U,0x3f800000U}},
  }};
  constexpr std::array<std::size_t, 3> pixels{0U, 31U, 62U};
  for (const Task18Case& fixture : fixtures) {
    const noisemaker::Surface first = render_task18(fixture);
    const noisemaker::Surface second = render_task18(fixture);
    require_repeat(first, second);
    REQUIRE(first.width() == 9U); REQUIRE(first.height() == 7U);
    REQUIRE(hex(sha256(little_endian_float_bytes(first))) == fixture.float_hash);
    REQUIRE(hex(sha256(first.to_rgba8())) == fixture.rgba_hash);
    for (std::size_t probe = 0; probe < pixels.size(); ++probe)
      for (std::size_t lane = 0; lane < 4U; ++lane)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[pixels[probe] * 4U + lane]) ==
                fixture.probes[probe * 4U + lane]);
  }
}

[[nodiscard]] noisemaker::Surface task19_formula_surface() {
  std::vector<float> data(11U * 9U * 4U);
  for (std::size_t y = 0; y < 9U; ++y) for (std::size_t x = 0; x < 11U; ++x) {
    const std::size_t lane = (y * 11U + x) * 4U;
    data[lane] = static_cast<float>(
        static_cast<double>((17U * x + 31U * y + 13U) % 101U) / 100.0);
    data[lane + 1U] = static_cast<float>(
        static_cast<double>((7U * x + 19U * y + 23U) % 97U) / 96.0);
    data[lane + 2U] = static_cast<float>(
        static_cast<double>((29U * x + 11U * y + 5U) % 89U) / 88.0);
    data[lane + 3U] = static_cast<float>(
        0.25 + static_cast<double>((3U * x + 5U * y + 1U) % 13U) / 20.0);
  }
  return noisemaker::Surface(11U, 9U, std::move(data));
}

struct Task19Case {
  std::string_view name;
  std::int32_t mode;
  std::uint32_t amount_bits;
  std::uint32_t direction_bits;
  std::int32_t blend_mode;
  std::uint32_t mix_bits;
  std::int32_t wrap;
  std::string_view float_hash;
  std::string_view rgba_hash;
  std::array<std::uint32_t, 12> probes;
};

[[nodiscard]] noisemaker::Surface render_task19(const Task19Case& fixture) {
  const noisemaker::Surface input = task19_formula_surface();
  noisemaker::glsl::Bindings bindings;
  bindings.set_texture("inputTex", input);
  bindings.set_uniform("resolution", noisemaker::glsl::Vec2(9.0f, 7.0f));
  bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(128.0f, 64.0f));
  bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(1024.0f, 768.0f));
  bindings.set_uniform("time", 0.375f);
  bindings.set_uniform("mode", fixture.mode);
  bindings.set_uniform("amount", noisemaker::uint_bits_to_float(fixture.amount_bits));
  bindings.set_uniform("direction", noisemaker::uint_bits_to_float(fixture.direction_bits));
  bindings.set_uniform("blendMode", fixture.blend_mode);
  bindings.set_uniform("mixAmt", noisemaker::uint_bits_to_float(fixture.mix_bits));
  bindings.set_uniform("wrap", fixture.wrap);
  return noisemaker::run_pass(
      noisemaker::generated::bind_classicNoisedeck_refract_refract(bindings),
      9U, 7U, 0.375f, 19.0f, 7U, 1.0f / 60.0f);
}

TEST(typed_task19_refract_external_oracles_are_exact_and_repeatable) {
  const std::array<Task19Case, 8> fixtures{{
      {"mirror-difference-under-half", 1, 0x415b3333U, 0x42150000U, 5,
       0x41bb3333U, 0,
       "d173f4368e000081b9b3921caccfd02790284c025ad5bd69d605f7310a23e2e2",
       "9f345b48aafb6d69ec9d7757a161f86a103e92a7a2efdadd5eba5d3b8b7ad8c3",
       {0x3f306ccaU,0x3f05f672U,0x3e8f79f3U,0x3e99999aU,
        0x3e645a1dU,0x3eb07827U,0x3f3904a8U,0x3eb33333U,
        0x3f3721d5U,0x3ed1d037U,0x3eb63fadU,0x3f59999aU}},
      {"repeat-overlay-half", 1, 0x41ef3333U, 0x4309999aU, 13,
       0x42480000U, 1,
       "6e02e60356ea964074be3b941e5ef976eeb5dfd4ee12041b8ab5cae484f2dea2",
       "e71609cfd1cfba0c3977abceb360939d22638858df33e02b551783f87d0c0fc1",
       {0x3f10a3d7U,0x3ee41c73U,0x3d0ecf57U,0x3e99999aU,
        0x3f0d013bU,0x3f0a8000U,0x3f7c4c2bU,0x3e800000U,
        0x3f70068eU,0x3f22638eU,0x3f467ab6U,0x3f59999aU}},
      {"clamp-soft-light-over-half", 1, 0x4292cccdU, 0x43879000U, 17,
       0x429dcccdU, 2,
       "3d38aee57222eb8460953f2a1e86418992f60c220b668b357d63f260346db56b",
       "25152ac17ca38d55d15e1c7f02c5cea715f659e9f4d2bc04cffbd58b10d4aa86",
       {0x3eaa8a71U,0x3eb61f4dU,0x3da9812cU,0x3e99999aU,
        0x3da2c5dbU,0x3f312337U,0x3f644233U,0x3f59999aU,
        0x3f2c54bcU,0x3f33d3aeU,0x3f3008d5U,0x3f59999aU}},
      {"mode-zero-mirror-control", 0, 0x422ccccdU, 0x419e0000U, 10,
       0x42480000U, 0,
       "3d791dbae4d93b61ab31f06b88105678c751ea3d369be9705661ed3a29879a0e",
       "24841a3ec260bb15d549f066207c52a2e82be2fa22743d81feb1995201f28af9",
       {0x3ee147aeU,0x3ee00000U,0x3e3a2e8cU,0x3e99999aU,
        0x3eee147aU,0x3f295556U,0x3f045d17U,0x3eb33333U,
        0x3f43d70aU,0x3f195555U,0x3eb45d18U,0x3eb33333U}},
      {"truthy-typed-array-noop-mode-2", 1, 0x41ef3333U, 0x4309999aU, 2,
       0x42480000U, 1,
       "165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24",
       "13a15bd48e6f739c5ec9e3f08affe0fe2c115418341a3b2e1742d8d3868e03e0",
       {0x00000000U,0x00000000U,0x00000000U,0x3e99999aU,
        0x00000000U,0x00000000U,0x00000000U,0x3e800000U,
        0x00000000U,0x00000000U,0x00000000U,0x3f59999aU}},
      {"truthy-typed-array-noop-mode-3", 1, 0x41ef3333U, 0x4309999aU, 3,
       0x42480000U, 1,
       "165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24",
       "13a15bd48e6f739c5ec9e3f08affe0fe2c115418341a3b2e1742d8d3868e03e0",
       {0x00000000U,0x00000000U,0x00000000U,0x3e99999aU,
        0x00000000U,0x00000000U,0x00000000U,0x3e800000U,
        0x00000000U,0x00000000U,0x00000000U,0x3f59999aU}},
      {"truthy-typed-array-noop-mode-7", 1, 0x41ef3333U, 0x4309999aU, 7,
       0x42480000U, 1,
       "165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24",
       "13a15bd48e6f739c5ec9e3f08affe0fe2c115418341a3b2e1742d8d3868e03e0",
       {0x00000000U,0x00000000U,0x00000000U,0x3e99999aU,
        0x00000000U,0x00000000U,0x00000000U,0x3e800000U,
        0x00000000U,0x00000000U,0x00000000U,0x3f59999aU}},
      {"truthy-typed-array-noop-mode-15", 1, 0x41ef3333U, 0x4309999aU, 15,
       0x42480000U, 1,
       "165333c40d4760271f8c318c19ed8efc54b9162ab5eeb615921c2552b645be24",
       "13a15bd48e6f739c5ec9e3f08affe0fe2c115418341a3b2e1742d8d3868e03e0",
       {0x00000000U,0x00000000U,0x00000000U,0x3e99999aU,
        0x00000000U,0x00000000U,0x00000000U,0x3e800000U,
        0x00000000U,0x00000000U,0x00000000U,0x3f59999aU}},
  }};
  constexpr std::array<std::size_t, 3> pixels{0U, 31U, 62U};
  for (const Task19Case& fixture : fixtures) {
    const noisemaker::Surface first = render_task19(fixture);
    const noisemaker::Surface second = render_task19(fixture);
    require_repeat(first, second);
    REQUIRE(first.width() == 9U); REQUIRE(first.height() == 7U);
    REQUIRE(hex(sha256(little_endian_float_bytes(first))) == fixture.float_hash);
    REQUIRE(hex(sha256(first.to_rgba8())) == fixture.rgba_hash);
    for (std::size_t probe = 0; probe < pixels.size(); ++probe)
      for (std::size_t lane = 0; lane < 4U; ++lane)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[pixels[probe] * 4U + lane]) ==
                fixture.probes[probe * 4U + lane]);
  }
}

struct Task20Case {
  std::string_view name;
  std::uint32_t time_bits;
  std::uint32_t scale_bits;
  std::uint32_t rotation_bits;
  std::uint32_t thickness_bits;
  std::uint32_t smoothness_bits;
  std::int32_t geometry;
  std::int32_t rings;
  std::int32_t star_points;
  std::int32_t animation;
  std::uint32_t speed_bits;
  std::uint32_t pulse_depth_bits;
  std::array<std::uint32_t, 3> fg_bits;
  std::array<std::uint32_t, 3> bg_bits;
  std::string_view float_hash;
  std::string_view rgba_hash;
  std::array<std::uint32_t, 36> probes;
  std::size_t nonfinite_rgb;
  std::size_t exact_background;
  std::size_t exact_foreground;
  std::size_t mixed_rgb;
};

constexpr std::array<std::array<std::size_t, 2>, 9> task20_probe_coordinates{{
    {0U, 0U},
    {10U, 9U},
    {16U, 11U},
    {18U, 11U},
    {20U, 15U},
    {28U, 5U},
    {32U, 9U},
    {35U, 21U},
    {36U, 22U},
}};

[[nodiscard]] noisemaker::Surface render_task20(const Task20Case& fixture,
                                                std::int32_t star_points_override = -1) {
  noisemaker::glsl::Bindings bindings;
  bindings.set_uniform("resolution", noisemaker::glsl::Vec2(37.0f, 23.0f));
  bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(5.0f, 7.0f));
  bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(53.0f, 41.0f));
  bindings.set_uniform("aspect", noisemaker::uint_bits_to_float(0x3fcde9bdU));
  bindings.set_uniform("scale", noisemaker::uint_bits_to_float(fixture.scale_bits));
  bindings.set_uniform("rotation", noisemaker::uint_bits_to_float(fixture.rotation_bits));
  bindings.set_uniform("thickness", noisemaker::uint_bits_to_float(fixture.thickness_bits));
  bindings.set_uniform("smoothness", noisemaker::uint_bits_to_float(fixture.smoothness_bits));
  bindings.set_uniform("geometry", fixture.geometry);
  bindings.set_uniform("rings", fixture.rings);
  bindings.set_uniform("starPoints", star_points_override < 0 ? fixture.star_points : star_points_override);
  bindings.set_uniform("animation", fixture.animation);
  bindings.set_uniform("speed", noisemaker::uint_bits_to_float(fixture.speed_bits));
  bindings.set_uniform("pulseDepth", noisemaker::uint_bits_to_float(fixture.pulse_depth_bits));
  bindings.set_uniform("time", noisemaker::uint_bits_to_float(fixture.time_bits));
  bindings.set_uniform("fgColor", noisemaker::glsl::Vec3(
      noisemaker::uint_bits_to_float(fixture.fg_bits[0]),
      noisemaker::uint_bits_to_float(fixture.fg_bits[1]),
      noisemaker::uint_bits_to_float(fixture.fg_bits[2])));
  bindings.set_uniform("bgColor", noisemaker::glsl::Vec3(
      noisemaker::uint_bits_to_float(fixture.bg_bits[0]),
      noisemaker::uint_bits_to_float(fixture.bg_bits[1]),
      noisemaker::uint_bits_to_float(fixture.bg_bits[2])));
  return noisemaker::run_pass(
      noisemaker::generated::bind_synth_sacredGeometry_sacredGeometry(bindings),
      37U, 23U, noisemaker::uint_bits_to_float(fixture.time_bits), 23.0f,
      11U, noisemaker::uint_bits_to_float(0x3c888889U));
}

TEST(typed_task20_sacred_geometry_external_oracles_are_exact_and_repeatable) {
  const std::array<Task20Case, 10> fixtures{{
      {"geometry-0-flower-default-control", 0x3eaccccdU, 0x41200000U,
       0x00000000U, 0x3e4ccccdU, 0x3ca3d70aU,
       0, 3, 5, 0,
       0x3f800000U, 0x3e19999aU, {0x3f800000U, 0x3f800000U, 0x3f800000U}, {0x00000000U, 0x00000000U, 0x00000000U},
       "f21a1640b99f9261e057803162a58a10421ef8215e986ac32a5db139772e5fc7",
       "5924cef44fee78454a1b0de3ad2d6ee3f6e58a5781d33d6ada23a0f3ebd94695",
       {0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3ea9b964U, 0x3ea9b964U, 0x3ea9b964U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U},
       0U, 523U,
       195U, 133U},
      {"geometry-1-fruit-animation-off", 0x3eaccccdU, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       1, 4, 7, 0,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "53a248d64b3e0ddd6ec1e3b0cb464f0a34a7537b195b6101ae491ed5237527bd",
       "65c56e8163f4771fa4b84f9491683b268f3f690244da038aa159017491446418",
       {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3ef13a31U, 0x3ecd2703U, 0x3e868e8aU, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3ef13a8eU, 0x3ecd273aU, 0x3e868e7fU, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U},
       0U, 622U,
       120U, 109U},
      {"geometry-3-metatron-animation-off", 0x3eaccccdU, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       3, 4, 7, 0,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "a59f25d73a50ea89aaecef886f6716d0160e1daff66e2c2d0d903db4b78a9768",
       "1bcedeeb940061ff65ecd623ed9403bc7cb527f0aeb0aa109280d94377365b56",
       {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3ef13a31U, 0x3ecd2703U, 0x3e868e8aU, 0x3f800000U, 0x3f02f977U, 0x3ed995dbU, 0x3e841e73U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3efc0e4fU, 0x3ed3a648U, 0x3e854868U, 0x3f800000U, 0x3f68b428U, 0x3f29d48bU, 0x3e585d84U, 0x3f800000U, 0x3ef13a8eU, 0x3ecd273aU, 0x3e868e7fU, 0x3f800000U, 0x3ef84d5eU, 0x3ed165b7U, 0x3e85b975U, 0x3f800000U, 0x3ea1ad5aU, 0x3e9d6c1cU, 0x3e8fea67U, 0x3f800000U},
       0U, 125U,
       252U, 474U},
      {"geometry-1-fruit-ripple", 0x3eaccccdU, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       1, 4, 7, 4,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "4860d797929366c4653b781be06b0e1ff71e50536bb8ed520451d36696353b97",
       "6008029ea08dd02986f54f779201b757973456d8fe110b60c279e8f25ab2ceaf",
       {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3efce9beU, 0x3ed429f1U, 0x3e852e97U, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U},
       0U, 500U,
       192U, 159U},
      {"geometry-3-metatron-unfold", 0x3ed33333U, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       3, 4, 7, 5,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "b230927f646ca19eec5da4afd377b834bcfba868f6ee4ac2c4c9cd2ca704b6d9",
       "a8a85901eb46162d910c494f18d1d55ddd6f6c137fc01184e4502d8e6e6e00bf",
       {0x3f53cd94U, 0x3f1d4a32U, 0x3e62336fU, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3eed4df8U, 0x3ecacc7aU, 0x3e8704aeU, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3ee47d62U, 0x3ec58287U, 0x3e880e29U, 0x3f800000U, 0x3f514b32U, 0x3f1bc8c4U, 0x3e6361bcU, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3ee1252eU, 0x3ec380ceU, 0x3e8872e4U, 0x3f800000U, 0x3e93f635U, 0x3e95316bU, 0x3e91877aU, 0x3f800000U},
       0U, 139U,
       0U, 712U},
      {"geometry-4-seed-rotate", 0x3eaccccdU, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       4, 4, 7, 1,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "aefe8af6e96a502a31f955c69d048fb0b3ea6509fcb7cbc812fe3a858c17057a",
       "fb99a8983f2d2d8e7068a63741090d35687a42fac360e67c3e76398a311ff4cc",
       {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f68e380U, 0x3f29f0f3U, 0x3e58473dU, 0x3f800000U},
       0U, 124U,
       443U, 284U},
      {"geometry-5-vesica-pulse", 0x3eaccccdU, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       5, 4, 7, 2,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "0c64d5b84edde6e6c8ef3fb5a69a96c188cd0aa9a4061e27ace4d346d155ef11",
       "3eec9bdd7df95c1027b106df8cddf374f7301379d8c19f1c0093d13873fa96cb",
       {0x3f080c9dU, 0x3edfacd4U, 0x3e82ecc5U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U},
       0U, 845U,
       0U, 6U},
      {"geometry-6-borromean-ripple", 0x3eaccccdU, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       6, 4, 7, 4,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "0927349a467756276ad2818fad4726061093fbeada54bb67b5441c184948d368",
       "0b04d4b45240d9359b1aa049e791321be93f0512c42858d33f4d8460b2d87599",
       {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f43d187U, 0x3f13b2f7U, 0x3e69b91bU, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3f060a8dU, 0x3edd43f5U, 0x3e8365b9U, 0x3f800000U, 0x3eae3657U, 0x3ea4f180U, 0x3e8e70e0U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U},
       0U, 588U,
       143U, 120U},
      {"geometry-7-star-animation-off", 0x3eaccccdU, 0x412c0000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       7, 4, 7, 0,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "2582e12629310c9fbd4781a158fd7f77512709b7b081bfb5ca00f38efde57879",
       "0ca995365b120c89a3dbf0f3def90f25c768c1f6af5556f57d15ef2fda197ebe",
       {0x7fc00000U, 0x7fc00000U, 0x7fc00000U, 0x3f800000U, 0x7fc00000U, 0x7fc00000U, 0x7fc00000U, 0x3f800000U, 0x7fc00000U, 0x7fc00000U, 0x7fc00000U, 0x3f800000U, 0x7fc00000U, 0x7fc00000U, 0x7fc00000U, 0x3f800000U, 0x7fc00000U, 0x7fc00000U, 0x7fc00000U, 0x3f800000U, 0x7fc00000U, 0x7fc00000U, 0x7fc00000U, 0x3f800000U, 0x7fc00000U, 0x7fc00000U, 0x7fc00000U, 0x3f800000U, 0x7fc00000U, 0x7fc00000U, 0x7fc00000U, 0x3f800000U, 0x7fc00000U, 0x7fc00000U, 0x7fc00000U, 0x3f800000U},
       2553U, 0U,
       0U, 851U},
      {"geometry-8-triquetra-rotate", 0x3eaccccdU, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       8, 4, 7, 1,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "6b3b4a906ffa5238c87f3516f92c26f61d8a4e4b51ae0b33db8535ea2946eeaf",
       "dad1ab989e22377d728fee5d982a9f1f9186580e5e4227f6c313db218ce52905",
       {0x3f3080eeU, 0x3f081c35U, 0x3e72cffaU, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U},
       0U, 805U,
       22U, 24U},
  }};
  for (const Task20Case& fixture : fixtures) {
    const noisemaker::Surface first = render_task20(fixture);
    const noisemaker::Surface second = render_task20(fixture);
    require_repeat(first, second);
    REQUIRE(first.width() == 37U); REQUIRE(first.height() == 23U);
    REQUIRE(hex(sha256(little_endian_float_bytes(first))) == fixture.float_hash);
    REQUIRE(hex(sha256(first.to_rgba8())) == fixture.rgba_hash);
    std::size_t nonfinite_rgb = 0U;
    std::size_t exact_background = 0U;
    std::size_t exact_foreground = 0U;
    for (std::size_t pixel = 0; pixel < 851U; ++pixel) {
      const std::size_t lane = pixel * 4U;
      REQUIRE(noisemaker::float_bits_to_uint(first.data()[lane + 3U]) == 0x3f800000U);
      const bool background =
          noisemaker::float_bits_to_uint(first.data()[lane]) == fixture.bg_bits[0] &&
          noisemaker::float_bits_to_uint(first.data()[lane + 1U]) == fixture.bg_bits[1] &&
          noisemaker::float_bits_to_uint(first.data()[lane + 2U]) == fixture.bg_bits[2];
      const bool foreground =
          noisemaker::float_bits_to_uint(first.data()[lane]) == fixture.fg_bits[0] &&
          noisemaker::float_bits_to_uint(first.data()[lane + 1U]) == fixture.fg_bits[1] &&
          noisemaker::float_bits_to_uint(first.data()[lane + 2U]) == fixture.fg_bits[2];
      exact_background += background ? 1U : 0U;
      exact_foreground += foreground ? 1U : 0U;
      for (std::size_t rgb = 0; rgb < 3U; ++rgb)
        nonfinite_rgb += std::isfinite(first.data()[lane + rgb]) ? 0U : 1U;
    }
    REQUIRE(nonfinite_rgb == fixture.nonfinite_rgb);
    REQUIRE(exact_background == fixture.exact_background);
    REQUIRE(exact_foreground == fixture.exact_foreground);
    REQUIRE(851U - exact_background - exact_foreground == fixture.mixed_rgb);
    for (std::size_t probe = 0; probe < task20_probe_coordinates.size(); ++probe) {
      const auto [x, y] = task20_probe_coordinates[probe];
      const std::size_t base = (y * 37U + x) * 4U;
      for (std::size_t lane = 0; lane < 4U; ++lane)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[base + lane]) ==
                fixture.probes[probe * 4U + lane]);
    }
  }
}

TEST(typed_task20_star_points_five_through_twelve_are_canonical_qnan) {
  const Task20Case star{
      "star-range", 0x3eaccccdU, 0x412c0000U,
      0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
      7, 4, 7, 0, 0x40300000U,
      0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U}, "", "", {}, 2553U, 0U, 0U, 851U};
  for (std::int32_t points = 5; points <= 12; ++points) {
    const noisemaker::Surface image = render_task20(star, points);
    for (std::size_t pixel = 0; pixel < 851U; ++pixel) {
      const std::size_t lane = pixel * 4U;
      REQUIRE(noisemaker::float_bits_to_uint(image.data()[lane]) == 0x7fc00000U);
      REQUIRE(noisemaker::float_bits_to_uint(image.data()[lane + 1U]) == 0x7fc00000U);
      REQUIRE(noisemaker::float_bits_to_uint(image.data()[lane + 2U]) == 0x7fc00000U);
      REQUIRE(noisemaker::float_bits_to_uint(image.data()[lane + 3U]) == 0x3f800000U);
    }
  }
  const double canonical = 2.0 - (2.0 / 7.0) * 7.0;
  const std::int32_t intended_remainder = (0 + 2) % 7;
  REQUIRE(canonical == 0.0);
  REQUIRE(!std::signbit(canonical));
  REQUIRE(intended_remainder == 2);
}

struct Task21Case {
  std::string_view name;
  std::size_t width;
  std::size_t height;
  std::array<std::uint32_t, 2> tile_offset_bits;
  std::array<std::uint32_t, 2> full_resolution_bits;
  std::uint32_t time_bits;
  std::uint32_t displacement_bits;
  std::uint32_t speed_bits;
  std::int32_t seed;
  std::uint32_t direction_bits;
  std::string_view input_float_hash;
  std::string_view input_rgba_hash;
  std::string_view output_float_hash;
  std::string_view output_rgba_hash;
  std::array<std::uint32_t, 48> probes;
  std::size_t pixels;
  std::size_t finite_lanes;
  std::size_t nonfinite_lanes;
  std::size_t changed_f32_lanes;
  std::size_t changed_rgb_pixels;
  std::size_t exact_input_pixels;
  std::size_t alpha_preserved_pixels;
  std::size_t alpha_clamped_pixels;
  std::size_t alpha_out_of_range_pixels;
  std::uint32_t min_output_bits;
  std::uint32_t max_output_bits;
};

[[nodiscard]] noisemaker::Surface task21_input(std::size_t width, std::size_t height) {
  std::vector<float> data(width * height * 4U);
  for (std::size_t y = 0; y < height; ++y) {
    for (std::size_t x = 0; x < width; ++x) {
      const std::size_t lane = (y * width + x) * 4U;
      data[lane] = static_cast<float>(static_cast<double>((17U * x + 31U * y + 13U) % 101U) / 100.0);
      data[lane + 1U] = static_cast<float>(static_cast<double>((7U * x + 19U * y + 23U) % 97U) / 96.0);
      data[lane + 2U] = static_cast<float>(static_cast<double>((29U * x + 11U * y + 5U) % 89U) / 88.0);
      const std::int64_t alpha = static_cast<std::int64_t>((5U * x + 7U * y + 3U) % 23U) - 5;
      data[lane + 3U] = static_cast<float>(static_cast<double>(alpha) / 12.0);
    }
  }
  return noisemaker::Surface(width, height, std::move(data));
}

[[nodiscard]] noisemaker::Surface render_task21(const Task21Case& fixture,
                                                const noisemaker::Surface& input) {
  noisemaker::glsl::Bindings bindings;
  bindings.set_texture("inputTex", input);
  bindings.set_uniform("resolution", noisemaker::glsl::Vec2(
      static_cast<float>(fixture.width), static_cast<float>(fixture.height)));
  bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(
      noisemaker::uint_bits_to_float(fixture.tile_offset_bits[0]),
      noisemaker::uint_bits_to_float(fixture.tile_offset_bits[1])));
  bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(
      noisemaker::uint_bits_to_float(fixture.full_resolution_bits[0]),
      noisemaker::uint_bits_to_float(fixture.full_resolution_bits[1])));
  bindings.set_uniform("time", noisemaker::uint_bits_to_float(fixture.time_bits));
  bindings.set_uniform("displacement", noisemaker::uint_bits_to_float(fixture.displacement_bits));
  bindings.set_uniform("speed", noisemaker::uint_bits_to_float(fixture.speed_bits));
  bindings.set_uniform("seed", fixture.seed);
  bindings.set_uniform("direction", noisemaker::uint_bits_to_float(fixture.direction_bits));
  return noisemaker::run_pass(
      noisemaker::generated::bind_filter_degauss_degauss(bindings),
      fixture.width, fixture.height,
      noisemaker::uint_bits_to_float(fixture.time_bits), 29.0f, 17U,
      noisemaker::uint_bits_to_float(0x3c888889U));
}

TEST(typed_task21_degauss_external_oracles_are_exact_repeatable_and_nonmutating) {
  const std::array<Task21Case, 9> fixtures{{
    {
      "displacement-zero-exact-copy-tiled", 13U, 9U, {0x40e00000U, 0x41300000U}, {0x42240000U, 0x41e80000U},
      0x3ec00000U, 0x00000000U, 0x3f800000U, 1, 0x00000000U,
      "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3",
      "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3",
      {0U, 0U, 0x3e051eb8U, 0x3e755555U, 0x3d68ba2fU, 0xbe2aaaabU, 12U, 0U, 0x3e19999aU, 0x3dd55555U, 0x3f7a2e8cU, 0x3f800000U, 0U, 8U, 0x3f170a3dU, 0x3f500000U, 0x3d3a2e8cU, 0x3f2aaaabU, 12U, 8U, 0x3f1c28f6U, 0x3f2d5555U, 0x3f7745d1U, 0xbdaaaaabU, 6U, 4U, 0x3ebd70a4U, 0x3eeaaaabU, 0x3f02e8baU, 0x3f555555U, 1U, 1U, 0x3f1c28f6U, 0x3f02aaabU, 0x3f02e8baU, 0x3f555555U, 11U, 7U, 0x3e051eb8U, 0x3ed00000U, 0x3f02e8baU, 0x3f555555U, 9U, 2U, 0x3e851eb8U, 0x3e900000U, 0x3e745d17U, 0x3f6aaaabU},
      117U, 468U, 0U, 0U, 0U, 117U, 117U, 67U, 50U, 0xbed55555U, 0x3fb55555U
    },
    {
      "default-landscape-untiled-center-mask", 13U, 9U, {0x00000000U, 0x00000000U}, {0x41500000U, 0x41100000U},
      0x3ec00000U, 0x3d800000U, 0x3f800000U, 1, 0x00000000U,
      "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3",
      "c6bf433ea90b0c82d842724d8f633fefb8cded8e34ad83b9d3480d98a7051c71", "9e02468af87d81a5d0a558ac965dd9e4f78b07a768b855e157d5769bcbd3ee98",
      {0U, 0U, 0x3ec74900U, 0x3e11ae50U, 0x3e472d2cU, 0x00000000U, 12U, 0U, 0x3eec3e53U, 0x3de52221U, 0x3f38f8e5U, 0x3f800000U, 0U, 8U, 0x3eab380cU, 0x3f2ddefcU, 0x3e9cd86fU, 0x3f2aaaabU, 12U, 8U, 0x3ef0ecddU, 0x3ef4e2e4U, 0x3f355a2fU, 0x00000000U, 6U, 4U, 0x3ebd70a4U, 0x3eeaaaabU, 0x3f02e8baU, 0x3f555555U, 1U, 1U, 0x3f40a349U, 0x3ec5c41dU, 0x3f024889U, 0x3f555555U, 11U, 7U, 0x3e95ed77U, 0x3f05876aU, 0x3f160f7aU, 0x3f555555U, 9U, 2U, 0x3ed800e0U, 0x3ecb2407U, 0x3f03da96U, 0x3f6aaaabU},
      117U, 468U, 0U, 398U, 116U, 1U, 67U, 117U, 0U, 0x00000000U, 0x3f800000U
    },
    {
      "nondefault-landscape-tiled-negative-direction", 13U, 9U, {0x40e00000U, 0x41300000U}, {0x42240000U, 0x41e80000U},
      0x3ee00000U, 0x3e400000U, 0x3fe00000U, 37, 0xc3094000U,
      "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3",
      "08dbc2988787474877268f9661bbeccbdc88dbd9f43bbfc3240e58120cf363f1", "16267b09be48cdb9b967ad1e4c203cd2170b940639975ee1cbba75309765db2c",
      {0U, 0U, 0x3ebcd6fcU, 0x3e42a339U, 0x3ec768b2U, 0x00000000U, 12U, 0U, 0x3eb0d6feU, 0x3ea99ac9U, 0x3f14a127U, 0x3f800000U, 0U, 8U, 0x3edae64bU, 0x3de910daU, 0x3ead294cU, 0x3f2aaaabU, 12U, 8U, 0x3ec08a78U, 0x3ebbd455U, 0x3eebb5ffU, 0x00000000U, 6U, 4U, 0x3ee79840U, 0x3f319c0cU, 0x3f3cee68U, 0x3f555555U, 1U, 1U, 0x3eb0823fU, 0x3f4cd945U, 0x3eb38292U, 0x3f555555U, 11U, 7U, 0x3ef2f977U, 0x3f448a03U, 0x3f561a8fU, 0x3f555555U, 9U, 2U, 0x3ef31555U, 0x3ee3bb85U, 0x3f2a42aeU, 0x3f6aaaabU},
      117U, 468U, 0U, 401U, 117U, 0U, 67U, 117U, 0U, 0x00000000U, 0x3f800000U
    },
    {
      "nondefault-portrait-tiled-positive-direction", 9U, 13U, {0x40a00000U, 0x40400000U}, {0x41b80000U, 0x42140000U},
      0x3f1ccccdU, 0x3e800000U, 0x40000000U, 100, 0x43340000U,
      "7ea6ac4f0ccd3f585245fab99613afd1a39cdeff0a484320f7dd1e4dabd83396", "d553b7ab55a780eb5bbc32c77103af6bf3660fc4046e6b3eeba8dbf45a2e9880",
      "86b32d32e970fffccc7049bf9c091f5e8b5e9139af7afd6f7bee6d315636a37f", "d2aca58372b68e20691c89a7ab278aebf97ffe85ffa35eb3d4bb6414016803d7",
      {0U, 0U, 0x3ea2456dU, 0x3e8d4fb3U, 0x3eeefa17U, 0x00000000U, 8U, 0U, 0x3ebc6b73U, 0x3f2ac937U, 0x3e53153dU, 0x3f800000U, 0U, 12U, 0x3ee15be8U, 0x3eee483eU, 0x3f3b73c7U, 0x3f800000U, 8U, 12U, 0x3f54d993U, 0x3f2434deU, 0x3e9cf7d1U, 0x3f155555U, 4U, 6U, 0x3f3c1370U, 0x3e9a3769U, 0x3f1dbd6dU, 0x3f800000U, 1U, 1U, 0x3f0a5ceeU, 0x3f39d7f1U, 0x3f2098c1U, 0x3f555555U, 7U, 11U, 0x3f58aa6dU, 0x3ef23e76U, 0x3ef5b68eU, 0x00000000U, 6U, 3U, 0x3f08e011U, 0x3f40ec7fU, 0x3f142cb5U, 0x3e800000U},
      117U, 468U, 0U, 403U, 117U, 0U, 65U, 117U, 0U, 0x00000000U, 0x3f800000U
    },
    {
      "speed-zero-nonzero-time", 13U, 9U, {0x40800000U, 0x40c00000U}, {0x41f80000U, 0x41c80000U},
      0x3f600000U, 0x3dc00000U, 0x00000000U, 19, 0x42050000U,
      "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3",
      "2bd1aa43c71d4eaab6298492b9edafd35978cd439eeae2a270968f6210128f37", "7788b9151bca2f493a0af156b38cc636e14b5f27d4bbed16ed60c4942513dc22",
      {0U, 0U, 0x3f14434dU, 0x3f3b7dd0U, 0x3ebef218U, 0x00000000U, 12U, 0U, 0x3edff55eU, 0x3f202a5bU, 0x3d61a809U, 0x3f800000U, 0U, 8U, 0x3f2449d9U, 0x3f581f14U, 0x3ea988f7U, 0x3f2aaaabU, 12U, 8U, 0x3ec972eaU, 0x3f32eefeU, 0x3f27f43fU, 0x00000000U, 6U, 4U, 0x3eab41c2U, 0x3ec1e43dU, 0x3f3b1e67U, 0x3f555555U, 1U, 1U, 0x3efeb3b1U, 0x3ed7e97fU, 0x3f30343aU, 0x3f555555U, 11U, 7U, 0x3f484e92U, 0x3eb9f73aU, 0x3f428ee4U, 0x3f555555U, 9U, 2U, 0x3e6bbd22U, 0x3e637643U, 0x3efc2ed2U, 0x3f6aaaabU},
      117U, 468U, 0U, 397U, 116U, 1U, 68U, 116U, 1U, 0xbe2aaaabU, 0x3f800000U
    },
    {
      "time-zero-positive-speed", 13U, 9U, {0x40400000U, 0x40000000U}, {0x41e80000U, 0x41a80000U},
      0x00000000U, 0x3e100000U, 0x3fc00000U, 53, 0xc2760000U,
      "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3",
      "c2f6253b9491350f176470a5be560068fb634e31432d524360d58ee03ed0586f", "710ce156f4b71dae2d487ac6a78fee5e58ee044fe400eb24740764c1784039b6",
      {0U, 0U, 0x3f45986fU, 0x3f1f81d8U, 0x3f1fbbc2U, 0x00000000U, 12U, 0U, 0x3f215f99U, 0x3f0a4c3dU, 0x3e7be930U, 0x3f800000U, 0U, 8U, 0x3ecda1bdU, 0x3f0152bcU, 0x3eeff490U, 0x3f2aaaabU, 12U, 8U, 0x3ea4468bU, 0x3eaa9bb0U, 0x3e1c5670U, 0x00000000U, 6U, 4U, 0x3eff5afbU, 0x3f52f319U, 0x3eec0314U, 0x3f555555U, 1U, 1U, 0x3ea76c06U, 0x3f561aefU, 0x3f32ebadU, 0x3f555555U, 11U, 7U, 0x3eda247cU, 0x3ea7567cU, 0x3f5b2159U, 0x3f555555U, 9U, 2U, 0x3ebd1da2U, 0x3f29c158U, 0x3f3a9fe5U, 0x3f6aaaabU},
      117U, 468U, 0U, 398U, 116U, 1U, 67U, 117U, 0U, 0x00000000U, 0x3f800000U
    },
    {
      "full-resolution-zero-fallback-landscape", 13U, 9U, {0x40000000U, 0x3f800000U}, {0x00000000U, 0x00000000U},
      0x3ea00000U, 0x3e000000U, 0x3fa00000U, 11, 0x42910000U,
      "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3",
      "15401d32e6befb161651150f044f35496bf741be49872b3869716689131453ff", "96cbb763c8daf83c9ef99c2972993148a5c2e5231436ebe9c4d4cb581c473a32",
      {0U, 0U, 0x3f07ae2eU, 0x3f04189aU, 0x3ddc7f93U, 0x00000000U, 12U, 0U, 0x3edc5254U, 0x3ed85000U, 0x3f4fa761U, 0x3f800000U, 0U, 8U, 0x3f006caeU, 0x3f6527efU, 0x3e9f4e51U, 0x3f2aaaabU, 12U, 8U, 0x3e6e3e5bU, 0x3ed2d5c3U, 0x3d91b7f8U, 0x00000000U, 6U, 4U, 0x3ef70e83U, 0x3e7059adU, 0x3f116026U, 0x3f555555U, 1U, 1U, 0x3f0c2bc2U, 0x3ed74a62U, 0x3e2cf67dU, 0x3f555555U, 11U, 7U, 0x3f6178c7U, 0x3f20c7a7U, 0x3f520ed4U, 0x3f555555U, 9U, 2U, 0x3f07dfefU, 0x3f07c5caU, 0x3ece51efU, 0x3f6aaaabU},
      117U, 468U, 0U, 398U, 116U, 1U, 67U, 117U, 0U, 0x00000000U, 0x3f800000U
    },
    {
      "square-frequency-equality", 11U, 11U, {0x40400000U, 0x40000000U}, {0x41f80000U, 0x41f80000U},
      0x3f0ccccdU, 0x3e600000U, 0x3f400000U, 71, 0xc3340000U,
      "b0f13bbfbca20ea2b40d7e19d75796f70ca2b641f564f26471869dbcd4c58da3", "c43c7e0c9248875f403f003073c29e69dd7f368a59223e01927d177b6f610acc",
      "8c09129cc2a75ca01f8a3d774307128cb1c44721c884821f6b22b7cff67e2948", "8e456f5906aca7993075834d2f3ad09f358f9acaffbfcc4dbc0f113ed4fd94c6",
      {0U, 0U, 0x3efae5d7U, 0x3f5754b4U, 0x3eccb371U, 0x00000000U, 10U, 0U, 0x3ee7967dU, 0x3f4a5c9bU, 0x3f0dbe30U, 0x3e2aaaabU, 0U, 10U, 0x3f10e029U, 0x3e2d028dU, 0x3f2bc720U, 0x00000000U, 10U, 10U, 0x3f003d03U, 0x3ef0cc84U, 0x3e16679eU, 0x3e800000U, 5U, 5U, 0x3ece5a9aU, 0x3e30bd73U, 0x3f0ba2bbU, 0x3f800000U, 1U, 1U, 0x3e1fcfd8U, 0x3f49d8b7U, 0x3eedb922U, 0x3f555555U, 9U, 9U, 0x3f2cbc40U, 0x3efa38e8U, 0x3f012a0dU, 0x3f800000U, 7U, 3U, 0x3ead59d9U, 0x3f3db9daU, 0x3ed07117U, 0x3f2aaaabU},
      121U, 484U, 0U, 416U, 121U, 0U, 68U, 121U, 0U, 0x00000000U, 0x3f800000U
    },
    {
      "untiled-over-cap-binding-domain-diagnostic", 13U, 9U, {0x00000000U, 0x00000000U}, {0x41500000U, 0x41100000U},
      0x3ef00000U, 0x3fe00000U, 0x3fa00000U, 29, 0x42b40000U,
      "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3",
      "c7983e127a9bc4ed938cff5c316d71ed50f2dfb2126b54718901efd80aae705f", "40d20fde4f5aab0e0e42a0371d373dbfdb66f62644650bef511ff8ffa3592bda",
      {0U, 0U, 0x3f26053eU, 0x3f3dd299U, 0x3f2abd32U, 0x00000000U, 12U, 0U, 0x3ee7df96U, 0x3f1bd6aaU, 0x3f052828U, 0x3f800000U, 0U, 8U, 0x3ebb5433U, 0x3f61dbe9U, 0x3eca4392U, 0x3f2aaaabU, 12U, 8U, 0x3e55cd47U, 0x3edd5954U, 0x3f354dfaU, 0x00000000U, 6U, 4U, 0x3ebd70a4U, 0x3eeaaaabU, 0x3f02e8baU, 0x3f555555U, 1U, 1U, 0x3f3ee451U, 0x3eed0e16U, 0x3f3c752bU, 0x3f555555U, 11U, 7U, 0x3f155419U, 0x3f0ebed0U, 0x3eeb9b51U, 0x3f555555U, 9U, 2U, 0x3e818330U, 0x3f489cf2U, 0x3e87905cU, 0x3f6aaaabU},
      117U, 468U, 0U, 398U, 116U, 1U, 67U, 117U, 0U, 0x00000000U, 0x3f800000U
    },
  }};

  for (const Task21Case& fixture : fixtures) {
    noisemaker::Surface first_input = task21_input(fixture.width, fixture.height);
    noisemaker::Surface second_input = task21_input(fixture.width, fixture.height);
    const auto original_floats = little_endian_float_bytes(first_input);
    const auto original_rgba = first_input.to_rgba8();
    REQUIRE(hex(sha256(original_floats)) == fixture.input_float_hash);
    REQUIRE(hex(sha256(original_rgba)) == fixture.input_rgba_hash);
    const noisemaker::Surface first = render_task21(fixture, first_input);
    const noisemaker::Surface second = render_task21(fixture, second_input);
    require_repeat(first, second);
    REQUIRE(little_endian_float_bytes(first_input) == original_floats);
    REQUIRE(first_input.to_rgba8() == original_rgba);
    REQUIRE(little_endian_float_bytes(second_input) == original_floats);
    REQUIRE(second_input.to_rgba8() == original_rgba);
    REQUIRE(first.width() == fixture.width); REQUIRE(first.height() == fixture.height);
    REQUIRE(hex(sha256(little_endian_float_bytes(first))) == fixture.output_float_hash);
    REQUIRE(hex(sha256(first.to_rgba8())) == fixture.output_rgba_hash);

    std::size_t finite_lanes = 0U; std::size_t nonfinite_lanes = 0U;
    std::size_t changed_lanes = 0U; std::size_t changed_rgb_pixels = 0U;
    std::size_t exact_input_pixels = 0U; std::size_t alpha_preserved = 0U;
    std::size_t alpha_clamped = 0U; std::size_t alpha_out_of_range = 0U;
    float minimum = std::numeric_limits<float>::infinity();
    float maximum = -std::numeric_limits<float>::infinity();
    for (std::size_t pixel = 0; pixel < fixture.pixels; ++pixel) {
      const std::size_t base = pixel * 4U;
      bool exact = true; bool rgb_changed = false;
      for (std::size_t lane = 0; lane < 4U; ++lane) {
        const float value = first.data()[base + lane];
        const bool finite = std::isfinite(value);
        finite_lanes += finite ? 1U : 0U; nonfinite_lanes += finite ? 0U : 1U;
        minimum = std::min(minimum, value); maximum = std::max(maximum, value);
        const bool changed = noisemaker::float_bits_to_uint(value) !=
                             noisemaker::float_bits_to_uint(first_input.data()[base + lane]);
        changed_lanes += changed ? 1U : 0U; exact = exact && !changed;
        if (lane < 3U) rgb_changed = rgb_changed || changed;
      }
      exact_input_pixels += exact ? 1U : 0U;
      changed_rgb_pixels += rgb_changed ? 1U : 0U;
      const float input_alpha = first_input.data()[base + 3U];
      const float output_alpha = first.data()[base + 3U];
      alpha_preserved += noisemaker::float_bits_to_uint(input_alpha) ==
                         noisemaker::float_bits_to_uint(output_alpha) ? 1U : 0U;
      alpha_clamped += noisemaker::float_bits_to_uint(std::clamp(input_alpha, 0.0f, 1.0f)) ==
                       noisemaker::float_bits_to_uint(output_alpha) ? 1U : 0U;
      alpha_out_of_range += (output_alpha < 0.0f || output_alpha > 1.0f) ? 1U : 0U;
    }
    REQUIRE(first.data().size() == fixture.pixels * 4U);
    REQUIRE(finite_lanes == fixture.finite_lanes); REQUIRE(nonfinite_lanes == fixture.nonfinite_lanes);
    REQUIRE(changed_lanes == fixture.changed_f32_lanes);
    REQUIRE(changed_rgb_pixels == fixture.changed_rgb_pixels);
    REQUIRE(exact_input_pixels == fixture.exact_input_pixels);
    REQUIRE(alpha_preserved == fixture.alpha_preserved_pixels);
    REQUIRE(alpha_clamped == fixture.alpha_clamped_pixels);
    REQUIRE(alpha_out_of_range == fixture.alpha_out_of_range_pixels);
    REQUIRE(noisemaker::float_bits_to_uint(minimum) == fixture.min_output_bits);
    REQUIRE(noisemaker::float_bits_to_uint(maximum) == fixture.max_output_bits);
    for (std::size_t probe = 0; probe < 8U; ++probe) {
      const std::size_t expected = probe * 6U;
      const std::size_t actual = (fixture.probes[expected + 1U] * fixture.width +
                                  fixture.probes[expected]) * 4U;
      for (std::size_t lane = 0; lane < 4U; ++lane)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[actual + lane]) ==
                fixture.probes[expected + 2U + lane]);
    }
  }
}

struct Task22Case {
  std::string_view name;
  std::size_t width;
  std::size_t height;
  std::array<std::uint32_t, 2> tile_offset_bits;
  std::array<std::uint32_t, 2> full_resolution_bits;
  std::uint32_t time_bits;
  std::uint32_t alpha_bits;
  std::uint32_t speed_bits;
  std::int32_t seed;
  std::uint32_t render_scale_bits;
  std::string_view input_float_hash;
  std::string_view input_rgba_hash;
  std::string_view output_float_hash;
  std::string_view output_rgba_hash;
  std::array<std::uint32_t, 42> probes;
  std::size_t pixels;
  std::size_t finite_lanes;
  std::size_t nonfinite_lanes;
  std::size_t changed_f32_lanes;
  std::size_t changed_rgb_pixels;
  std::size_t exact_input_pixels;
  std::size_t alpha_preserved_pixels;
  std::size_t alpha_out_of_range_pixels;
};

[[nodiscard]] noisemaker::Surface render_task22(const Task22Case& fixture,
                                                const noisemaker::Surface& input) {
  noisemaker::glsl::Bindings bindings;
  bindings.set_texture("inputTex", input);
  bindings.set_uniform("resolution", noisemaker::glsl::Vec2(
      static_cast<float>(fixture.width), static_cast<float>(fixture.height)));
  bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(
      noisemaker::uint_bits_to_float(fixture.tile_offset_bits[0]),
      noisemaker::uint_bits_to_float(fixture.tile_offset_bits[1])));
  bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(
      noisemaker::uint_bits_to_float(fixture.full_resolution_bits[0]),
      noisemaker::uint_bits_to_float(fixture.full_resolution_bits[1])));
  bindings.set_uniform("time", noisemaker::uint_bits_to_float(fixture.time_bits));
  bindings.set_uniform("speed", noisemaker::uint_bits_to_float(fixture.speed_bits));
  bindings.set_uniform("seed", fixture.seed);
  bindings.set_uniform("alpha", noisemaker::uint_bits_to_float(fixture.alpha_bits));
  bindings.set_uniform("renderScale",
                       noisemaker::uint_bits_to_float(fixture.render_scale_bits));
  return noisemaker::run_pass(
      noisemaker::generated::bind_filter_crt_crt(bindings),
      fixture.width, fixture.height,
      noisemaker::uint_bits_to_float(fixture.time_bits), 29.0f, 17U,
      noisemaker::uint_bits_to_float(0x3c888889U));
}

TEST(typed_task22_crt_public_adapter_oracles_are_exact_repeatable_and_nonmutating) {
  const std::array<Task22Case, 11> fixtures{{
    {"alpha-zero-exact-copy-tiled", 13U, 9U, {0x40e00000U, 0x41300000U}, {0x42240000U, 0x41e80000U}, 0x3ec00000U, 0x00000000U, 0x40000000U, 37, 0x40000000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", {0U, 0U, 0x3e051eb8U, 0x3e755555U, 0x3d68ba2fU, 0xbe2aaaabU, 12U, 0U, 0x3e19999aU, 0x3dd55555U, 0x3f7a2e8cU, 0x3f800000U, 0U, 8U, 0x3f170a3dU, 0x3f500000U, 0x3d3a2e8cU, 0x3f2aaaabU, 12U, 8U, 0x3f1c28f6U, 0x3f2d5555U, 0x3f7745d1U, 0xbdaaaaabU, 6U, 4U, 0x3ebd70a4U, 0x3eeaaaabU, 0x3f02e8baU, 0x3f555555U, 1U, 1U, 0x3f1c28f6U, 0x3f02aaabU, 0x3f02e8baU, 0x3f555555U, 11U, 7U, 0x3e051eb8U, 0x3ed00000U, 0x3f02e8baU, 0x3f555555U}, 117U, 468U, 0U, 0U, 0U, 117U, 117U, 50U},
    {"alpha-negative-clamps-zero-copy", 9U, 7U, {0x40400000U, 0x40a00000U}, {0x41b80000U, 0x41980000U}, 0x3f200000U, 0xbe800000U, 0x3f800000U, 19, 0x3f800000U, "5036ac34df07a6e89f8ae9cd5ee4fa3250a1962bdbda6bc4e29dc4ce512fb8a8", "6b56cc6c2f780b54a655f04ba7deae8e61e8330ca84b5d5056e8c352dd16885c", "5036ac34df07a6e89f8ae9cd5ee4fa3250a1962bdbda6bc4e29dc4ce512fb8a8", "6b56cc6c2f780b54a655f04ba7deae8e61e8330ca84b5d5056e8c352dd16885c", {0U, 0U, 0x3e051eb8U, 0x3e755555U, 0x3d68ba2fU, 0xbe2aaaabU, 8U, 0U, 0x3ef5c28fU, 0x3f52aaabU, 0x3f2ba2e9U, 0x3fa00000U, 0U, 6U, 0x3f7ae148U, 0x3ed55555U, 0x3f4e8ba3U, 0x3fb55555U, 8U, 6U, 0x3ea3d70aU, 0x3f800000U, 0x3ed1745dU, 0x3f6aaaabU, 4U, 3U, 0x3f3ae148U, 0x3deaaaabU, 0x3f3d1746U, 0x3faaaaabU, 1U, 1U, 0x3f1c28f6U, 0x3f02aaabU, 0x3f02e8baU, 0x3f555555U, 7U, 5U, 0x3f59999aU, 0x3f3aaaabU, 0x3f7745d1U, 0xbdaaaaabU}, 63U, 252U, 0U, 0U, 0U, 63U, 63U, 28U},
    {"default-landscape-untiled", 13U, 9U, {0x00000000U, 0x00000000U}, {0x41500000U, 0x41100000U}, 0x3ec00000U, 0x3f000000U, 0x3f800000U, 1, 0x3f800000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "3134189c0654121a560abf3f8f102873b3395937ae244eaf1d6de7d03e6c8192", "c9a7375db6ae12c5dc1f0b2fa49669892d405c55ab587cc0a054d75d9d66eeb9", {0U, 0U, 0x3e6e4a4fU, 0x3eb2debfU, 0x3e1e84f4U, 0xbe2aaaabU, 12U, 0U, 0x3e65cda8U, 0x3e3b0955U, 0x3f55ab66U, 0x3f800000U, 0U, 8U, 0x3f26ed52U, 0x3f634822U, 0x3d99b8a3U, 0x3f2aaaabU, 12U, 8U, 0x3f1fcd19U, 0x3f3afae4U, 0x3f5b5584U, 0xbdaaaaabU, 6U, 4U, 0x3eea10aeU, 0x3f0df42aU, 0x3f1cea40U, 0x3f555555U, 1U, 1U, 0x3eff9f5cU, 0x3ecccc54U, 0x3e8fd093U, 0x3f555555U, 11U, 7U, 0x3dc01d51U, 0x3ea8b1f8U, 0x3e985952U, 0x3f555555U}, 117U, 468U, 0U, 351U, 117U, 0U, 117U, 50U},
    {"alpha-above-one-clamps-and-preserves-input-alpha", 13U, 9U, {0x00000000U, 0x00000000U}, {0x41500000U, 0x41100000U}, 0x3ee00000U, 0x3fe00000U, 0x3f800000U, 11, 0x3f800000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "e6d5a0788f2a23100ee9968186ac1f1a05175ecf6972e8503bd92cd8130a4bfd", "b971437eec882ffd958b151216992caad58a8a681211f161ec60480820d52fee", {0U, 0U, 0x3e4097faU, 0x3e98be04U, 0x3dea67efU, 0xbe2aaaabU, 12U, 0U, 0x3f38577cU, 0x00000000U, 0x3ed92ca3U, 0x3f800000U, 0U, 8U, 0x3f078940U, 0x3f40a8e9U, 0x00000000U, 0x3f2aaaabU, 12U, 8U, 0x3ef0ff88U, 0x3ea76765U, 0x3ee5680eU, 0xbdaaaaabU, 6U, 4U, 0x3eb45e5fU, 0x3ee2f7c5U, 0x3efef180U, 0x3f555555U, 1U, 1U, 0x3eccd465U, 0x3e0bde44U, 0x3d6c3339U, 0x3f555555U, 11U, 7U, 0x3d9f37d8U, 0x3deb8c6cU, 0x3df406d6U, 0x3f555555U}, 117U, 468U, 0U, 351U, 117U, 0U, 117U, 50U},
    {"landscape-tiled-render-scale-two", 13U, 9U, {0x40e00000U, 0x41300000U}, {0x423c0000U, 0x41b80000U}, 0x3ee00000U, 0x3f400000U, 0x3fe00000U, 37, 0x40000000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "7e9a4e738ad67051674ea5d8e7e2333585e943bbe45fcdbdf3c9e59635c359ec", "2ed1841d5be9df1f576fecf81bab403ad848fb96d4e33055525a1520e905d75c", {0U, 0U, 0x3e82b7eeU, 0x3ec0ed7dU, 0x3e325911U, 0xbe2aaaabU, 12U, 0U, 0x3f02d8f6U, 0x3e11e1d6U, 0x3f1e75b9U, 0x3f800000U, 0U, 8U, 0x3f14aa25U, 0x3f501cfaU, 0x3c4af539U, 0x3f2aaaabU, 12U, 8U, 0x3f07a8dcU, 0x3f195440U, 0x3f65679cU, 0xbdaaaaabU, 6U, 4U, 0x3ed34e4cU, 0x3ecfe1a6U, 0x3eac213aU, 0x3f555555U, 1U, 1U, 0x3f37c9a0U, 0x3ef6f475U, 0x3ea68536U, 0x3f555555U, 11U, 7U, 0x3e05323dU, 0x3ed414a6U, 0x3f05b7efU, 0x3f555555U}, 117U, 468U, 0U, 351U, 117U, 0U, 117U, 50U},
    {"portrait-tiled-fractional-render-scale", 9U, 13U, {0x40a00000U, 0x40400000U}, {0x41b80000U, 0x42140000U}, 0x3f1ccccdU, 0x3f200000U, 0x40000000U, 100, 0x3fc00000U, "7ea6ac4f0ccd3f585245fab99613afd1a39cdeff0a484320f7dd1e4dabd83396", "d553b7ab55a780eb5bbc32c77103af6bf3660fc4046e6b3eeba8dbf45a2e9880", "cdc080912dc354a6052447427814040e552d7c38edf4e1c499d8f7c80bd196be", "ecfb38a778ba9e40d9bacfb5a8f1f62a810cd929d14b83c2bf5d4abc6bc0d079", {0U, 0U, 0x3dd51251U, 0x3e4fec57U, 0x3d1b4a6cU, 0xbe2aaaabU, 8U, 0U, 0x3edfa98bU, 0x3f36ae8bU, 0x3edf12f2U, 0x3fa00000U, 0U, 12U, 0x3f150ebcU, 0x3ecb0f5eU, 0x3eb6c500U, 0x3f8aaaabU, 8U, 12U, 0x3deae944U, 0x3e414c71U, 0x3ec11e70U, 0x3f155555U, 4U, 6U, 0x3ee83d08U, 0x3f23042eU, 0x3ed3e145U, 0x3f955555U, 1U, 1U, 0x3ef55138U, 0x3eb308b5U, 0x3e64e4a6U, 0x3f555555U, 7U, 11U, 0x3f25a278U, 0x3f47843fU, 0x3ec83a59U, 0xbed55555U}, 117U, 468U, 0U, 350U, 117U, 0U, 117U, 52U},
    {"speed-zero-nonzero-time", 13U, 9U, {0x40800000U, 0x40c00000U}, {0x41f80000U, 0x41c80000U}, 0x3f600000U, 0x3f600000U, 0x00000000U, 19, 0x3f800000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "f83304619eda688e29c3ae34b4c913535919c3505c2f59f5100b587ddf52ddd8", "16727fe42c77a453e47d0dcfcc14b079b39a84d06683ac8d0f689749611ec70e", {0U, 0U, 0x3e8d4aa3U, 0x3ecc6028U, 0x3e46535dU, 0xbe2aaaabU, 12U, 0U, 0x3e35211dU, 0x3e02e0d1U, 0x3f7f45d2U, 0x3f800000U, 0U, 8U, 0x3ef4bf63U, 0x3f30590dU, 0x3bba2e8cU, 0x3f2aaaabU, 12U, 8U, 0x3eedfeeaU, 0x3f1b4257U, 0x3f0ccde8U, 0xbdaaaaabU, 6U, 4U, 0x3e7dceb1U, 0x3edd1352U, 0x3e371349U, 0x3f555555U, 1U, 1U, 0x3f2e8644U, 0x3f2edd2aU, 0x3e863253U, 0x3f555555U, 11U, 7U, 0x3dd2bef9U, 0x3eebad87U, 0x3ea8d238U, 0x3f555555U}, 117U, 468U, 0U, 348U, 117U, 0U, 117U, 50U},
    {"time-zero-positive-speed", 13U, 9U, {0x40400000U, 0x40000000U}, {0x41e80000U, 0x41a80000U}, 0x00000000U, 0x3f600000U, 0x3fc00000U, 53, 0x3f800000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "bc5ed1803bb52ee4d075d4c9ff6e5cc62ca2ba6f60f7d5aed93d1c237ad81b98", "59a3fef349d5457d514174dba0e328bcd1723f97d0d8fdf82649ed217265f5d0", {0U, 0U, 0x3de930eeU, 0x3e577c83U, 0x3d4b39b8U, 0xbe2aaaabU, 12U, 0U, 0x3cb6169dU, 0x3c555555U, 0x3f3bdd41U, 0x3f800000U, 0U, 8U, 0x3ec19630U, 0x3f0dd699U, 0x3bba2e8cU, 0x3f2aaaabU, 12U, 8U, 0x3eb220d3U, 0x3f0923dfU, 0x3ee7a609U, 0xbdaaaaabU, 6U, 4U, 0x3e13e2baU, 0x3eb8d139U, 0x3e095841U, 0x3f555555U, 1U, 1U, 0x3f242d17U, 0x3f38951cU, 0x3e9974d1U, 0x3f555555U, 11U, 7U, 0x3dc1cd54U, 0x3ecf2f42U, 0x3ee99571U, 0x3f555555U}, 117U, 468U, 0U, 348U, 117U, 0U, 117U, 50U},
    {"full-resolution-zero-fallback", 13U, 9U, {0x40000000U, 0x3f800000U}, {0x00000000U, 0x00000000U}, 0x3ea00000U, 0x3f400000U, 0x3fa00000U, 11, 0x3f800000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "19b91bedac3685b2c368a1c8da9eb89ae6e57e8deeee513b4151cf12dad3896f", "fc49c1f7a2ea1c69db968ceabfaa4293ba8b193e13a5634b51ef763d0fea50d6", {0U, 0U, 0x3db83107U, 0x3e3b226eU, 0x3ce50454U, 0xbe2aaaabU, 12U, 0U, 0x3f12b739U, 0x3cd55555U, 0x3f0f4f08U, 0x3f800000U, 0U, 8U, 0x3ed332c8U, 0x3f18dc46U, 0x3c3a2e8cU, 0x3f2aaaabU, 12U, 8U, 0x3f0137f7U, 0x3ed3f108U, 0x3f13a8a9U, 0xbdaaaaabU, 6U, 4U, 0x3e834fb7U, 0x3eab2bb4U, 0x3ec31999U, 0x3f555555U, 1U, 1U, 0x3f094ff5U, 0x3e8ffe92U, 0x3e599c26U, 0x3f555555U, 11U, 7U, 0x3db99834U, 0x3e4011e0U, 0x3e5e267bU, 0x3f555555U}, 117U, 468U, 0U, 351U, 117U, 0U, 117U, 50U},
    {"square-large-time-max-metadata", 11U, 11U, {0x40400000U, 0x40000000U}, {0x41f80000U, 0x41f80000U}, 0x4640e680U, 0x3f800000U, 0x40a00000U, 100, 0x3fc00000U, "b0f13bbfbca20ea2b40d7e19d75796f70ca2b641f564f26471869dbcd4c58da3", "c43c7e0c9248875f403f003073c29e69dd7f368a59223e01927d177b6f610acc", "5169bfe5072efd935eafd52f13b413c7b4f5f9834e9991f5a6207a877a6bfc48", "3a0f86f1aac14e290bbc2d22675f4af5bfa1a08fc68cbfc59c92331f5daf59a5", {0U, 0U, 0x3e844576U, 0x3ec2a7eaU, 0x3e35382eU, 0xbe2aaaabU, 10U, 0U, 0x3f2dd8d5U, 0x3f800000U, 0x3f71a330U, 0x3e2aaaabU, 0U, 10U, 0x3e9f275dU, 0x3e9df7c2U, 0x3ed57dfaU, 0xbdaaaaabU, 10U, 10U, 0x3f7508d2U, 0x3f68c905U, 0x3e375acfU, 0x3e800000U, 5U, 5U, 0x3eeb619fU, 0x3f44a975U, 0x3f800000U, 0x3f800000U, 1U, 1U, 0x3f324ecbU, 0x3efde7c3U, 0x3e61b5b3U, 0x3f555555U, 9U, 9U, 0x3e85d24fU, 0x3f528c3dU, 0x3f53bac2U, 0x3f955555U}, 121U, 484U, 0U, 361U, 121U, 0U, 121U, 53U},
    {"render-scale-below-one-clamps", 13U, 9U, {0x00000000U, 0x00000000U}, {0x41500000U, 0x41100000U}, 0x3ef00000U, 0x3f000000U, 0x3fa00000U, 29, 0x3f000000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "d963390a996552ce28b3f8f5c7b7971072a60566ebad0bf29beb329fa4a24de2", "65e933fe048522db9d4b8eae08057c6ca56f3d4b53510181fb2e288f25546716", {0U, 0U, 0x3ddf417eU, 0x3e56a58eU, 0x3d2b51f2U, 0xbe2aaaabU, 12U, 0U, 0x3e87d076U, 0x3e2ab859U, 0x3f46e578U, 0x3f800000U, 0U, 8U, 0x3eed87e5U, 0x3f284ba4U, 0x3cba2e8cU, 0x3f2aaaabU, 12U, 8U, 0x3ef1ba3eU, 0x3f1bdca0U, 0x3f3bc62eU, 0xbdaaaaabU, 6U, 4U, 0x3ef263baU, 0x3ebb45b4U, 0x3ee9e12eU, 0x3f555555U, 1U, 1U, 0x3ec042bdU, 0x3ed3f257U, 0x3e92d8cdU, 0x3f555555U, 11U, 7U, 0x3d942f25U, 0x3eb9906aU, 0x3eb12392U, 0x3f555555U}, 117U, 468U, 0U, 351U, 117U, 0U, 117U, 50U}
  }};

  for (const Task22Case& fixture : fixtures) {
    noisemaker::Surface first_input = task21_input(fixture.width, fixture.height);
    noisemaker::Surface second_input = task21_input(fixture.width, fixture.height);
    const auto original_floats = little_endian_float_bytes(first_input);
    const auto original_rgba = first_input.to_rgba8();
    REQUIRE(hex(sha256(original_floats)) == fixture.input_float_hash);
    REQUIRE(hex(sha256(original_rgba)) == fixture.input_rgba_hash);

    const noisemaker::Surface first = render_task22(fixture, first_input);
    const noisemaker::Surface second = render_task22(fixture, second_input);
    require_repeat(first, second);
    REQUIRE(little_endian_float_bytes(first_input) == original_floats);
    REQUIRE(first_input.to_rgba8() == original_rgba);
    REQUIRE(little_endian_float_bytes(second_input) == original_floats);
    REQUIRE(second_input.to_rgba8() == original_rgba);
    REQUIRE(first.width() == fixture.width);
    REQUIRE(first.height() == fixture.height);
    REQUIRE(hex(sha256(little_endian_float_bytes(first))) == fixture.output_float_hash);
    REQUIRE(hex(sha256(first.to_rgba8())) == fixture.output_rgba_hash);

    std::size_t finite_lanes = 0U;
    std::size_t nonfinite_lanes = 0U;
    std::size_t changed_lanes = 0U;
    std::size_t changed_rgb_pixels = 0U;
    std::size_t exact_input_pixels = 0U;
    std::size_t alpha_preserved = 0U;
    std::size_t alpha_out_of_range = 0U;
    for (std::size_t pixel = 0; pixel < fixture.pixels; ++pixel) {
      const std::size_t base = pixel * 4U;
      bool exact = true;
      bool rgb_changed = false;
      for (std::size_t lane = 0; lane < 4U; ++lane) {
        const float value = first.data()[base + lane];
        const bool finite = std::isfinite(value);
        finite_lanes += finite ? 1U : 0U;
        nonfinite_lanes += finite ? 0U : 1U;
        const bool changed = noisemaker::float_bits_to_uint(value) !=
                             noisemaker::float_bits_to_uint(first_input.data()[base + lane]);
        changed_lanes += changed ? 1U : 0U;
        exact = exact && !changed;
        if (lane < 3U) rgb_changed = rgb_changed || changed;
      }
      exact_input_pixels += exact ? 1U : 0U;
      changed_rgb_pixels += rgb_changed ? 1U : 0U;
      const float input_alpha = first_input.data()[base + 3U];
      const float output_alpha = first.data()[base + 3U];
      alpha_preserved += noisemaker::float_bits_to_uint(input_alpha) ==
                         noisemaker::float_bits_to_uint(output_alpha) ? 1U : 0U;
      alpha_out_of_range += (output_alpha < 0.0f || output_alpha > 1.0f) ? 1U : 0U;
    }
    REQUIRE(first.data().size() == fixture.pixels * 4U);
    REQUIRE(finite_lanes == fixture.finite_lanes);
    REQUIRE(nonfinite_lanes == fixture.nonfinite_lanes);
    REQUIRE(changed_lanes == fixture.changed_f32_lanes);
    REQUIRE(changed_rgb_pixels == fixture.changed_rgb_pixels);
    REQUIRE(exact_input_pixels == fixture.exact_input_pixels);
    REQUIRE(alpha_preserved == fixture.alpha_preserved_pixels);
    REQUIRE(alpha_out_of_range == fixture.alpha_out_of_range_pixels);
    for (std::size_t probe = 0; probe < 7U; ++probe) {
      const std::size_t expected = probe * 6U;
      const std::size_t actual = (fixture.probes[expected + 1U] * fixture.width +
                                  fixture.probes[expected]) * 4U;
      for (std::size_t lane = 0; lane < 4U; ++lane)
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[actual + lane]) ==
                fixture.probes[expected + 2U + lane]);
    }
  }
}


}  // namespace
