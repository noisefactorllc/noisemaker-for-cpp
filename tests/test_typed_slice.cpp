#include "test_harness.hpp"
#include "fixtures/historical/authority_26d6f42_kernels.hpp"
#include "fixtures/historical/retired_kernels.hpp"
#include "fixtures/historical/reverb_kernel.hpp"

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
  return noisemaker::run_pass(noisemaker::historical_generated::bind_filter_bc_bc(bindings), 8U, 8U, 0.125f, 7.0f);
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
    uniform("edgeColor", noisemaker::glsl::DVec3(0.17, 0.63, 0.91)); uniform("mixAmount", 0.71f);
  } else if (key == "filter/chroma:chroma") {
    uniform("targetHue", 0.37f); uniform("range", 0.19f); uniform("feather", 0.07f);
  } else if (key == "filter/chrome:chMap") {
    texture("blurTex", blur); uniform("detail", 63.0f); uniform("distortion", 27.0f);
  } else if (key == "filter/colorReplace:colorReplace") {
    uniform("targetColor", noisemaker::glsl::DVec3(0.23, 0.51, 0.77));
    uniform("replaceColor", noisemaker::glsl::DVec3(0.88, 0.16, 0.42));
    uniform("sensitivity", 0.43f); uniform("smoothing", 0.18f);
    uniform("colorMix", 0.67f); uniform("replaceAlpha", 0.82f); uniform("keepAlpha", 0.31f);
  } else if (key == "filter/deriv:deriv") {
    uniform("amount", 1.7f); uniform("renderScale", 0.75f);
  } else if (key == "filter/lensFlare:lensFlare") {
    uniform("brightness", 137.0f); uniform("centerX", 0.29f); uniform("centerY", 0.61f);
    uniform("tint", noisemaker::glsl::DVec3(0.83, 0.94, 0.71));
    uniform("LENS_TYPE", std::int32_t(0));
  } else if (key == "filter/mosaicTiles:mosaicTiles") {
    uniform("tileSize", 4.7f); uniform("groutWidth", 22.0f); uniform("relief", 58.0f);
    uniform("maxOffset", 31.0f); uniform("gapFill", std::int32_t(2));
    uniform("backgroundColor", noisemaker::glsl::DVec3(0.12, 0.34, 0.56)); uniform("seed", std::int32_t(7));
    uniform("MODE", std::int32_t(0));
  } else if (key == "filter/photocopy:pcCombine") {
    texture("blurTex", blur); uniform("darkness", 68.0f);
    uniform("inkColor", noisemaker::glsl::DVec3(0.08, 0.17, 0.29));
    uniform("paperColor", noisemaker::glsl::DVec3(0.93, 0.84, 0.61));
  } else if (key == "filter/relief:rlShade") {
    texture("blurTex", blur); uniform("detail", 57.0f); uniform("lightAngle", 123.0f);
    uniform("balance", 44.0f); uniform("graininess", 36.0f);
    uniform("inkColor", noisemaker::glsl::DVec3(0.09, 0.18, 0.27));
    uniform("paperColor", noisemaker::glsl::DVec3(0.92, 0.79, 0.63));
    uniform("MODE", std::int32_t(0));
  } else if (key == "filter/ridge:ridge") {
    uniform("level", 0.42f);
  } else if (key == "filter/scatter:scatterJitter") {
    uniform("radius", 2.7f); uniform("seed", std::int32_t(11));
    uniform("MODE", std::int32_t(0));
  } else if (key == "filter/simpleAberration:chromaticAberration") {
    uniform("displacement", 0.037f);
  } else if (key == "filter/text:text") {
    texture("textTex", text); uniform("matteColor", noisemaker::glsl::DVec3(0.14, 0.35, 0.73));
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

// A deliberately translucent baseTex fixture (constant low alpha, distinct
// from every other fixture's near-opaque coverage) for the mixer/alphaMask
// mask-mode branch: `mix(background, color1, maskVal)` blends through the
// base's own coverage, so a fully-opaque base would never exercise that.
[[nodiscard]] noisemaker::Surface translucent_base_source() {
  constexpr std::size_t width = 4U;
  constexpr std::size_t height = 3U;
  std::vector<std::uint8_t> bytes(width * height * 4U);
  for (std::size_t y = 0; y < height; ++y) for (std::size_t x = 0; x < width; ++x) {
    const std::size_t i = (y * width + x) * 4U;
    bytes[i] = static_cast<std::uint8_t>(60U + 13U * x + 9U * y);
    bytes[i + 1U] = static_cast<std::uint8_t>(90U + 17U * x + 5U * y);
    bytes[i + 2U] = static_cast<std::uint8_t>(150U + 3U * x + 7U * y);
    bytes[i + 3U] = 96U;
  }
  return noisemaker::Surface::from_rgba8(width, height, bytes);
}

void populate_task10_bindings(noisemaker::glsl::Bindings& bindings, std::string_view key,
                              const noisemaker::Surface& input, const noisemaker::Surface& blur,
                              const noisemaker::Surface& tex, const noisemaker::Surface& base,
                              float polygon_smoothing = 0.12f, std::string_view skip = {}) {
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
    uniform("lightDirection", noisemaker::glsl::DVec3(0.31, 0.79, 0.43));
  } else if (key == "filter/seamless:seamless") {
    uniform("blend", 0.31f); uniform("repeat", 2.3f); uniform("curve", std::int32_t(1));
  } else if (key == "filter/sine:sine") {
    uniform("amount", 8.7f); uniform("colorMode", 1.0f);
  } else if (key == "filter/vignette:vignette") {
    uniform("vignetteBrightness", 0.21f); uniform("alpha", 0.81f);
  } else if (key == "mixer/alphaMask:alphaMask") {
    // baseTex is unconditionally required at bind time (the generated
    // typed-slice constructor resolves every declared sampler eagerly),
    // even though the pixel body only samples it inside the `maskMode`
    // branch. See mixer/alphaMask/glsl/alphaMask.glsl upstream commit
    // 0ed489ec46842bffba33ee2ec65a218b6dda51f5.
    texture("tex", tex); texture("baseTex", base);
    uniform("mixAmt", 47.0f); uniform("maskMode", false);
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
    // with the full-resolution aspect (13 / 11) after merging them.
    uniform("aspect", static_cast<float>(13.0 / 11.0)); uniform("sides", std::int32_t(3));
    uniform("radius", 0.4f); uniform("smoothing", polygon_smoothing); uniform("rotation", 23.0f);
    uniform("fgColor", noisemaker::glsl::DVec3(0.14, 0.73, 0.31)); uniform("fgAlpha", 0.83f);
    uniform("bgColor", noisemaker::glsl::DVec3(0.91, 0.22, 0.58)); uniform("bgAlpha", 0.47f);
  }
}

[[nodiscard]] noisemaker::Surface render_task10(std::string_view key, float polygon_smoothing = 0.12f,
                                                std::string_view variant = {}) {
  const noisemaker::Surface regular_input = source(5U, 3U, 1U);
  const noisemaker::Surface edge_input = glowing_edge_source();
  const noisemaker::Surface blur = source(3U, 5U, 11U);
  const noisemaker::Surface tex = source(7U, 2U, 23U);
  const noisemaker::Surface base = source(4U, 3U, 59U);
  const noisemaker::Surface translucent_base = translucent_base_source();
  const noisemaker::Surface& input = key == "filter/glowingEdge:glowingEdge" ? edge_input : regular_input;
  noisemaker::glsl::Bindings bindings;
  populate_task10_bindings(bindings, key, input, blur, tex, base, polygon_smoothing);
  if (variant == "channel0") bindings.set_uniform("channel", std::int32_t(0));
  else if (variant == "channel1") bindings.set_uniform("channel", std::int32_t(1));
  else if (variant == "channel3") bindings.set_uniform("channel", std::int32_t(3));
  else if (variant == "fullResolutionZero") bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(0.0f));
  else if (variant == "metric0") bindings.set_uniform("sobelMetric", 0.0f);
  else if (variant == "metric1") bindings.set_uniform("sobelMetric", 1.0f);
  else if (variant == "metric2") bindings.set_uniform("sobelMetric", 2.0f);
  else if (variant == "mono") bindings.set_uniform("mono", true);
  else if (variant == "earlyReturn") bindings.set_uniform("size", 0.75f);
  else if (variant == "zeroLightFallback") bindings.set_uniform("lightDirection", noisemaker::glsl::DVec3(0.0));
  else if (variant == "oppositeLightHalfFallback") bindings.set_uniform("lightDirection", noisemaker::glsl::DVec3(0.0, 0.0, -1.0));
  else if (variant == "linear") bindings.set_uniform("curve", std::int32_t(0));
  else if (variant == "sharp") bindings.set_uniform("curve", std::int32_t(2));
  else if (variant == "zeroBlend") bindings.set_uniform("blend", 0.0f);
  else if (variant == "luminance") bindings.set_uniform("colorMode", 0.0f);
  else if (variant == "maskReturn") bindings.set_uniform("maskMode", true);
  else if (variant == "maskTranslucentBase") {
    bindings.set_uniform("maskMode", true);
    bindings.set_texture("baseTex", translucent_base);
  }
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
  require_oracle("threshold", threshold, "665cd6cc51a1dcfe46f1382584060d093dbebdeee2d835f02a44723ce39f6da1", "63d3dc8653662baff87afd576ae73ecfc61d65c688cebfde7406153e6484ac65", {0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U}, true);
  const noisemaker::Surface smoothstep = render_smoothstep(a);
  require_oracle("smoothstep", smoothstep, "200eb65fed133e0640ed0165c4be24923e6fda1c236c3ea8b5d07f8747566b45", "340558b647177c7f72bbd4b2fcbecef4facfd780a5e6fbfaf7231961895058a7", {0x00000000U, 0x00000000U, 0x00000000U, 0x3f7afafbU}, false);
  const noisemaker::Surface channel = render_channel(r, g, b);
  require_oracle("channel", channel, "fc1400efc3cea802a1246dab60fbecc809bec633425c95295665d1c987bd1fb2", "a5ac13cccc6fdb4d53bd7fefc545b7fedcbf5cca1ec93b7ab51fe746438c342f", {0x3e8a45a7U, 0x3e9e90d8U, 0x3e9e8098U, 0x3f800000U}, true);
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
      {"filter/celShading:celShadingBlend", "7671df88873f629613721396fd759fa936b3ed6597d56dd3ebb56c7c9bad3273", "29dbb9378a3a71f980104464eb0b9a8e29e0580759e1256f49ac7ee9164b8900", 0x3e0a9e58U},
      {"filter/chroma:chroma", "efc59e60e7b127541dbb28cf18d5981144fc4a22f02d4f6d710be29ea0ac06fe", "72ef0585ff112ea147febd8ede9f8d3965215513c44ddf0feb188790f371c637", 0x3f4234f7U},
      {"filter/chrome:chMap", "c86f1178b3c10cdcfcfb20d794907a4ca394d79dfe0d002f054084e0f84e6887", "bc19edaad2c576252a6f9ea3420422d08286039b8cc15f88aa0e7a6734f18bf8", 0x3d70c7f3U},
      {"filter/colorReplace:colorReplace", "d07476f0cc1a36bb5c4e5f392ddb14b11f3987b0c842f065387313e7c2999206", "33c8b3e38c7d93521a58581c2b1bc0e56547d2afc8d5673aeddca4d2bf26d0ff", 0x3d9c2f9cU},
      {"filter/deriv:deriv", "43e591217a059e9a86f3e00e52a91b0539c2cc3783619dd0f45de04c292fd3a2", "6a3cbb07be0a133257bd1ca518d82c8269c5b47bd4abd975fe1cb530b70c900e", 0x3c88d638U},
      {"filter/lensFlare:lensFlare", "91ccb962621ee05e37733144f028658b8b9b8dde91accd5aff694aee27bb9a6e", "42d035c4d765ef017d27b641bb5a2a96f03122ca19032c1e02233b8d7915cbc4", 0x3d85d166U},
      {"filter/mosaicTiles:mosaicTiles", "2f670e03ed85d4ad59f178d46690cedbed1e268a693183b1885362359b9c1a88", "43b8098f9aac9737876d0a25191899a2232333c311fec4a2f09b6f12234d4037", 0x3c311790U},
      {"filter/photocopy:pcCombine", "84400e5def67011965258e40c5e84004f259e69a73e4804d29c22683bb61cad7", "76d6b92b4fb7f0c8e4f465da28246117a0ad5ac0c9c45e43085d1280f0877c6f", 0x3da3d70aU},
      {"filter/relief:rlShade", "0bf68c9b1d0203dae7999e0db9c041374f22cf2871aa35f8d960e38886924165", "f5205caa03ccc976eefc1c41b9f535ea578a23510cf6154642b16634da32abe6", 0x3f078889U},
      {"filter/ridge:ridge", "14e083e0d2e604d0b5559ebbdd175316ae313160e5aca89c468678ef3932eff9", "5d220bfe0488a6b32a233b82932edee6b8b5e094c478b95f54289d6e0edc1b8b", 0x3eba3eaaU},
      {"filter/scatter:scatterJitter", "6d7aa5f9e4f9c3af676f8e5cff6bb6a4f4aee2a5a0af1364920d26306d10be41", "2a2b7378b2d39c9ee639ac17c6bcf3e6d51632dc4422a02d4adbc920762d27fb", 0x3df0f0f1U},
      {"filter/simpleAberration:chromaticAberration", "09c9d93ea78ddb0f877dd993f6af3f5b7d7ffd9c10d05fe4dc2f4b505f1af7e6", "42c44f9ac2cd9b55e1dc92abd18afa3960b6a7982d44e9463db03717b207b760", 0x3e30b0b1U},
      {"filter/text:text", "660011a5b64c22eb297b38ed0843f1b68cff75977331dfad37f5f2be5135ea6f", "9a03fadce3dc09be280da2a0d8d89cbd14c822222893dd9fd38d8d71e780a223", 0x3d8faa52U},
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
      {"filter/glowingEdge:glowingEdge", "62b7e0394d19c04f9363d191fd553b5a881b2c34d2d4f265315290bc9d9b22f4", "8fd25b2c5bb1124cb6d1348c74355432625bd247128027ae4c7a7f6b3ce55c87", {0x3e6b9ca6U,0x3eb92b62U,0x3dec4187U,0x3f800000U,0x3f1c1552U,0x3f39792fU,0x3ec312aaU,0x3f6cecedU,0x3f1d149fU,0x3f29aeb1U,0x3ee296baU,0x3f56d6d7U}},
      {"filter/highPass:hpCombine", "b7d5dab26de4a4fe50a8cdc6439c52133a733625b9651abf31a4dc28bd37e40e", "37f0995e070ba207c0aac4722cabb5c78617281f23562193509956649577990d", {0x00000000U,0x3ebbbbbcU,0x3e66e6e6U,0x3f7afafbU,0x3d38b8b8U,0x3e66e6e6U,0x3ed3d3d4U,0x3f27a7a8U,0x3f800000U,0x3f800000U,0x3f1a1a1aU,0x3ea8a8a9U}},
      {"filter/pixels:pixels", "feb89b0e6a128d533471c06cac88fe82d78874442cfbd509204de736ad6bbc0d", "59adf71406e87307e5f915828cfce8b52ec0bb667bd62c853dc7181f413c9641", {0x3df0f0f1U,0x3e989899U,0x3dd0d0d1U,0x3f55d5d6U,0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
      {"filter/plasticWrap:pwSpec", "b59b84a82075ebafd04ed19e6a224be8e16a223898ffd776b19dcae17052e096", "9d1599d1124a34c34d246cf95de8de038e299917769d139057cd453d05449d3a", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3eb8b8b9U,0x3ec4c4c5U,0x3f20a0a1U,0x3f27a7a8U,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
      {"filter/seamless:seamless", "bb46aba7be87fa920d68614933afbb8034b19a14b3b6b9f36705a8822fbe1472", "90255d926242b26be8853e926acca831507d557afe72a00016c9e134a772dea2", {0x3e8f1222U,0x3eb5fd45U,0x3ee73c4fU,0x3f800000U,0x3ef0e421U,0x3eca1031U,0x3f607f03U,0x3f800000U,0x3eb91a12U,0x3ec4e750U,0x3f2040daU,0x3f800000U}},
      {"filter/sine:sine", "73b6f26c811b0a8676d475bd8eed36917f3ab0d914f87da8f50da49a0d197014", "6f09375716db998f9df1655f106383dde3444800b8e1242a5390f01be0b916d9", {0x3f36edbcU,0x3f6af852U,0x3f1e4797U,0x3f7afafbU,0x3e8af2fcU,0x3f6d7d57U,0x3f5cff8aU,0x3f35b5b6U,0x3e90dd22U,0x3e650b52U,0x3f7727f2U,0x3ea8a8a9U}},
      {"filter/vignette:vignette", "ec4c106f3bf2a3c0efd58b37d0d2fbcd27986d56de4a85939da391c1aa5cc168", "03f0b8e7644def6fbf6fa486b93646041c870baff6684fb98ff8171f3d56dab7", {0x3dc6ddf3U,0x3e110c83U,0x3da4a7caU,0x3f7afafbU,0x3eb7080eU,0x3e6f5ee4U,0x3f24f08eU,0x3f35b5b6U,0x3eeae795U,0x3ee690f7U,0x3e5e860dU,0x3ea8a8a9U}},
      {"mixer/alphaMask:alphaMask", "cd459701e88a9422cbf042e08013043760e6ef2d6566dde1f1d0c4fd0410cfb7", "b352155bb35bb1b39d427784164f2edfe75e8d9373161a2209d98feb4b967032", {0x3e3926fbU,0x3f22910dU,0x3f234fa2U,0x3f4889cbU,0x3f55704eU,0x3f628f41U,0x3f83c258U,0x3efcbb80U,0x3f818c4dU,0x3dbf284aU,0x3e94a2faU,0x3f63d371U}},
      {"mixer/applyMode:applyMode", "7aeee2945e2264b2706af1000de073f87afa3de89fb58b74d7d45c5e489fc462", "901503d50bab78d19f2bdd7f32efd5a6166653885a965813a1a12b735c9517e5", {0x3dc01c46U,0x3eaff106U,0x3eb6cb47U,0x3f7afafbU,0x3efb291fU,0x3f4760fbU,0x3ea6022bU,0x3f35b5b6U,0x3f4f0f0fU,0x3e0ff65cU,0x3e9cc8c2U,0x3f5ddddeU}},
      {"mixer/thresholdMix:thresholdMix", "f6e338ca581f3243524f124f3db407c3e0a56c42d9563eaba6901f48eb373712", "9499f26e19394e0bd91fad082d820362851877598640cfbdf87f9719ffa62b7e", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f088889U,0x3f3cbcbdU,0x3f50d0d1U,0x3ed82d83U,0x3f76f6f7U,0x3f27a7a8U,0x3e64e4e5U,0x3f022cd8U}},
      {"synth/polygon:shape", "6a0b2a8fcbf6b80c611e7ad9cf8fe0703ad1411617785c655d9c856d078a44b3", "efde74185f2fdeef07aec3de84b1442e65b4013f2e4ea85b7f027a6254498e02", {0x3edafb7fU,0x3dd3c361U,0x3e8b923aU,0x3ef0a3d7U,0x3dedfa44U,0x3f1b1c43U,0x3e83bcd3U,0x3f547ae1U,0x3edafb7fU,0x3dd3c361U,0x3e8b923aU,0x3ef0a3d7U}},
  }};
  const noisemaker::Surface polygon_nonzero_before = render_task10("synth/polygon:shape", 0.12f);
  const noisemaker::Surface polygon_zero = render_task10("synth/polygon:shape", 0.0f);
  const noisemaker::Surface polygon_nonzero_after = render_task10("synth/polygon:shape", 0.12f);
  const noisemaker::Surface polygon_zero_after = render_task10("synth/polygon:shape", 0.0f);
  REQUIRE(hex(sha256(little_endian_float_bytes(polygon_nonzero_before))) == "6a0b2a8fcbf6b80c611e7ad9cf8fe0703ad1411617785c655d9c856d078a44b3");
  REQUIRE(hex(sha256(polygon_nonzero_before.to_rgba8())) == "efde74185f2fdeef07aec3de84b1442e65b4013f2e4ea85b7f027a6254498e02");
  const std::string polygon_zero_float = hex(sha256(little_endian_float_bytes(polygon_zero)));
  if (polygon_zero_float != "14842e67934a7c529dab72fd6a3ddbdddcafc99ead7bf4ce2dd4a3692780743e") {
    std::ostringstream detail;
    detail << "polygon zero float oracle hash: " << polygon_zero_float << " foreground pixels:";
    for (std::size_t pixel = 0; pixel < 35U; ++pixel) {
      if (noisemaker::float_bits_to_uint(polygon_zero.data()[pixel * 4U]) == 0x3dedfa44U)
        detail << " (" << (pixel % 7U) << ',' << (pixel / 7U) << ')';
    }
    throw std::runtime_error(detail.str());
  }
  REQUIRE(hex(sha256(polygon_zero.to_rgba8())) == "908bdd2044e12e7a0a864920ca32bbcc5cb37bdeef163dfee4580c18175071f3");
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
  constexpr std::array<Fixture, 24> fixtures{{
      {"filter/channel:channel", "channel0", "f06aad98061e763aeaaeb3642a7c6f6193c325fa6ae2f718a8904358e5778d00", "f8956632116fec613352479918e6907d8735e45021a48503cc08bb2c773cc5f6"},
      {"filter/channel:channel", "channel1", "7188cfe8d07b5c3ecf55d2c2dd4f2e421d6bbc50c019b6132673a3363dfc9b6c", "c29398951217bef5ae55ea839afb45b41a80459ea27eb5fcc12807d36cb83361"},
      {"filter/channel:channel", "channel3", "05b55b15d8e517d4d2a0370f61a2a69338092d1228995929b7db7cadd4377677", "b4d9bf4bf793c1a8c0169e66f270a626162fe24aaaf59f8e5eb62027e09b58ab"},
      {"filter/chromaticAberration:chromaticAberration", "fullResolutionZero", "103f341ac27ebb92b3986b60a0b284f0aafece72559be1b889d98195acdbcdfc", "0853f39530090c34540be01998f924ed3772614d644c1641bc26ba1e7c42a2af"},
      {"filter/glowingEdge:glowingEdge", "metric0", "019ab0ef1020e05e5e901cb340e9a46f66529cefc054bc8a28886981b2ce4fde", "8f42b60bab0ab75aea84707043c8ae0afc3047b1fc1aa420a56b557d6abaaf3d"},
      {"filter/glowingEdge:glowingEdge", "metric1", "383c60189de282fadff8bdba44e57ef5641a73ba55382c0dca3d49d6e66ebd7b", "c361423fb4e4852699976ef7419619ac87aba5a98ca09e3ee673557d2d61b568"},
      {"filter/glowingEdge:glowingEdge", "metric2", "84b1e9202b2d144924c3ed00cf409c6f716f595254751a8206429919b82e3d04", "4fd31f9f94d8f89761bb05af87b02285ae12da1e2a89567da829f1746c47ed83"},
      {"filter/highPass:hpCombine", "mono", "6c1deb8eeabffeaf6e752635399c3e770b02cae2d3adf176ba096cb43c354c19", "3dea99c45113cd58157c0de11127d3df3404a909eb6a9e90681556c161cf4caf"},
      {"filter/pixels:pixels", "earlyReturn", "bde61fe2cc345cd2979280e465847046eec54926ac7a5569ab36b7c9d4fac749", "5f07b0549bb0b7480f9f9709f6e2d863b9e1f93ebe4a6147459092c931e38718"},
      {"filter/plasticWrap:pwSpec", "zeroLightFallback", "b59b84a82075ebafd04ed19e6a224be8e16a223898ffd776b19dcae17052e096", "9d1599d1124a34c34d246cf95de8de038e299917769d139057cd453d05449d3a"},
      {"filter/plasticWrap:pwSpec", "oppositeLightHalfFallback", "b59b84a82075ebafd04ed19e6a224be8e16a223898ffd776b19dcae17052e096", "9d1599d1124a34c34d246cf95de8de038e299917769d139057cd453d05449d3a"},
      {"filter/seamless:seamless", "linear", "b5ba0537a15d961c4d6a15d80cd212140cdbcf541f7811a87f5577463116f665", "625bf1a9f9c15319aacb8c2a366a08b7d02476b83f3f2d685c1bcc1f690d9f2c"},
      {"filter/seamless:seamless", "sharp", "2fb88ecf907dfaf2cbeb3c534ca6f1622dc26ab39105949ce80ae59878c5f959", "98ce2fb4c75815268e9fd8f8a5e4857dda251f1d85eb96310fbc759caf029837"},
      {"filter/seamless:seamless", "zeroBlend", "43633d6a9d949ac1d965090c18be1e4709a35cc680f0348e2ee0bf735c7f7672", "002a6dc460f3a727c0ed3cd108dcad1f1bb6bc925acdd86cba0006dbb834b862"},
      {"filter/sine:sine", "luminance", "1361edb9630997113f9d535468ef0caf947c86d7e6c57be87066cb6d384c8d3f", "ecc2703ea467bb15781f2d5f5688befde66441b5e2d0ac1972a206bc06129cbc"},
      {"filter/vignette:vignette", "fullResolutionZero", "49d0c54b98a32c28d244bee620a623b606522a254b34efcc4a192b1ac29434d9", "65daf291de28c048faf144e018b39b2ff6082c1c993b280154e961e1f02ece79"},
      {"mixer/alphaMask:alphaMask", "maskReturn", "6248f17d402205d7d9989d34c415d412253e104be2b18c954d6a8d868f617ce0", "f5ab5871ccab6489846aac701b44eee7efb15d1023abcede7ba5c0b5415b8722"},
      {"mixer/alphaMask:alphaMask", "maskTranslucentBase", "5c0155acf5d163fcd4c2e8441719f2d051ce18d885c99f566c7f0da639f07741", "33ddffd6c473b2acd0d067cc8d75648a911b8347a407d0534cab8fa95078b614"},
      {"mixer/alphaMask:alphaMask", "alphaNegative", "594438d9e093edc81819ed52ced98f6c35d7678b34298a2bf1e27b49447d264e", "290e9f41f11f4200c75792050f53987b7b0757246663b625602b9bd02c12abb8"},
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
  const noisemaker::Surface base = source(4U, 3U, 59U);
  for (const Fixture& fixture : fixtures) {
    noisemaker::glsl::Bindings bindings;
    populate_task10_bindings(bindings, fixture.key, input, blur, tex, base);
    bindings.set_uniform(std::string(fixture.uniform), fixture.wrong);
    REQUIRE_THROWS_AS(noisemaker::generated::bind(fixture.key, bindings), noisemaker::glsl::KernelBindingError);
  }
}

TEST(typed_control_flow_slice_secondary_samplers_are_required) {
  struct Fixture { std::string_view key; std::string_view sampler; };
  constexpr std::array<Fixture, 6> fixtures{{
      {"filter/highPass:hpCombine", "blurTex"}, {"filter/plasticWrap:pwSpec", "blurTex"},
      {"mixer/alphaMask:alphaMask", "tex"}, {"mixer/alphaMask:alphaMask", "baseTex"},
      {"mixer/applyMode:applyMode", "tex"},
      {"mixer/thresholdMix:thresholdMix", "tex"},
  }};
  const noisemaker::Surface input = source(5U, 3U, 1U);
  const noisemaker::Surface blur = source(3U, 5U, 11U);
  const noisemaker::Surface tex = source(7U, 2U, 23U);
  const noisemaker::Surface base = source(4U, 3U, 59U);
  for (const Fixture& fixture : fixtures) {
    noisemaker::glsl::Bindings bindings;
    populate_task10_bindings(bindings, fixture.key, input, blur, tex, base, 0.12f, fixture.sampler);
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
    uniform("splatColor", noisemaker::glsl::DVec3(0.81, 0.22, 0.63));
    uniform("mode", std::int32_t{2}); uniform("speckScale", 2.6f); uniform("speckCutoff", 38.0f);
    uniform("speckSpeed", 3.0f); uniform("speckSeed", 5.0f);
    uniform("speckColor", noisemaker::glsl::DVec3(0.17, 0.74, 0.39));
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
    texture("inputTex", input); uniform("color", noisemaker::glsl::DVec3(0.83, 0.19, 0.47));
    uniform("density", 1.5f); uniform("alpha", 0.83f); uniform("seed", std::int32_t{11});
    if (fixture.variant == "fallbackResolution") uniform("fullResolution", noisemaker::glsl::Vec2(0.0f));
  } else if (fixture.key == "filter/tint:colorize") {
    texture("inputTex", fixture.variant == "mode2" ? tint_hybrid : input);
    uniform("color", noisemaker::glsl::DVec3(0.16, 0.69, 0.83));
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
    uniform("imageSize", noisemaker::glsl::DVec2(17.0, 13.0)); uniform("position", std::int32_t{0});
    uniform("rotation", 0.0f); uniform("scaleAmt", 100.0f); uniform("offsetX", 0.0f);
    uniform("offsetY", 0.0f); uniform("tiling", std::int32_t{0}); uniform("flip", std::int32_t{0});
    uniform("bgColor", noisemaker::glsl::DVec3(0.12, 0.34, 0.56)); uniform("bgAlpha", 0.71f);
    if (fixture.variant.starts_with("position")) uniform("position", std::int32_t{task11_suffix(fixture.variant, "position")});
    else if (fixture.variant.starts_with("tiling")) {
      uniform("position", std::int32_t{4}); uniform("scaleAmt", 40.0f);
      uniform("tiling", std::int32_t{task11_suffix(fixture.variant, "tiling")});
    } else if (fixture.variant.starts_with("flip")) {
      uniform("position", std::int32_t{4});
      uniform("flip", std::int32_t{task11_suffix(fixture.variant, "flip")});
    } else if (fixture.variant == "outOfBounds") {
      uniform("scaleAmt", 15.0f); uniform("offsetX", 100.0f); uniform("offsetY", 100.0f);
      uniform("bgColor", noisemaker::glsl::DVec3(0.03, 0.57, 0.91)); uniform("bgAlpha", 0.63f);
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
  if (fixture.key == "filter/corrupt:corrupt") {
    return noisemaker::run_pass(noisemaker::historical_generated::bind_filter_corrupt_corrupt(bindings),
                               7U, 5U, 0.125f, 7.0f);
  }
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
    {"filter/flipMirror:flipMirror", "mode13", "94530fe46f0be26947f3a6a65f886ad256abe2f88ced2e7740249f597f7943eb", "701ff504f64f54e5915628896069f414aa71bd66731659fe34cb16cf0d2ecb47", {0x3df0f0f1U,0x3e989899U,0x3dd0d0d1U,0x3f55d5d6U,0x3ef6f6f7U,0x3edadadbU,0x3f63e3e4U,0x3f109091U,0x3e9c9c9dU,0x3f068687U,0x3ee0e0e1U,0x3f19999aU}},
    {"filter/flipMirror:flipMirror", "mode14", "78bb5263b566554cd1b657a78cbf7801056e781b5897595f125574bec39c66cc", "f384f18a85804e3898b7f575e41db5ef5a066d13c6fdc960760854e89db2b865", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3e9c9c9dU,0x3f068687U,0x3ee0e0e1U,0x3f19999aU}},
    {"filter/flipMirror:flipMirror", "mode15", "e51fedd8e508906c9b4b58af638d3509b9f03605ddd8ad8187399b4b9bee6cf0", "8cc2ee9f2991443b5afc9e88b4f468495c4fbdff4d7333416b5e9b189819d7c6", {0x3df0f0f1U,0x3e989899U,0x3dd0d0d1U,0x3f55d5d6U,0x3ef6f6f7U,0x3edadadbU,0x3f63e3e4U,0x3f109091U,0x3e3cbcbdU,0x3ef6f6f7U,0x3e34b4b5U,0x3f30b0b1U}},
    {"filter/flipMirror:flipMirror", "mode16", "805d52e217cf9be1d6cf40f0bf19b967586ce4fe0c6b8561497edf750b61f44d", "bed103fbaa2856ca2635775fafd33f8f851ccb18e2b61fd849fedf96333d5822", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3e3cbcbdU,0x3ef6f6f7U,0x3e34b4b5U,0x3f30b0b1U}},
    {"filter/flipMirror:flipMirror", "mode17", "add5bc60f389d32a8f60298df83293070708d8bef46b37465a579bab9d3f1915", "c3658b0c1350d0262eab797816b720931da7bf414ff84152865c965daec8fa37", {0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU,0x3ef6f6f7U,0x3edadadbU,0x3f63e3e4U,0x3f109091U,0x3e9c9c9dU,0x3f068687U,0x3ee0e0e1U,0x3f19999aU}},
    {"filter/flipMirror:flipMirror", "mode18", "2fd95f9588d3fca68235ab90eff6767aa40337de9f16bf74db9930ec5a0e8524", "13e1c98242807c2a5187f2627dfaaf0ee6b7fe07a88a776557259382b8f312ab", {0x3e30b0b1U,0x3e20a0a1U,0x3e949495U,0x3f63e3e4U,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3e9c9c9dU,0x3f068687U,0x3ee0e0e1U,0x3f19999aU}},
    {"filter/outline:outlineBlend", "blackOutline", "0cdc782ef48b86b3395bb211e750c986133655c15197aec8cf3451a8050af57e", "02c694a92b27a522f2f1ee42fa02a85786f3a68e0f1acaeb90f671440805439f", {0x3bc4884bU,0x3c5b358fU,0x3b53a679U,0x3f7afafbU,0x3ebaf530U,0x3e5ab48eU,0x3f376e25U,0x3f35b5b6U,0x3ea84df3U,0x3ea45e18U,0x3de067efU,0x3ea8a8a9U}},
    {"filter/outline:outlineBlend", "whiteOutline", "9dc53dc74ad565771aecb8d7fe693a9a6592816c54dcd6057b1983b19e0fe6f4", "6c31604c022103bfc3dd675a6158ce35552a97d55e27acf31cae7b6a738537c7", {0x3f636af3U,0x3f654eb8U,0x3f62b588U,0x3f7afafbU,0x3ef9336eU,0x3eab9885U,0x3f568d44U,0x3f35b5b6U,0x3f56a97dU,0x3f54b18fU,0x3f1e8f81U,0x3ea8a8a9U}},
    {"filter/outline:outlineValueMap", "colorOklab", "856c984b4d37fdded7e9e7cd117a64bbf218658cfb51dc572f92d7c9b0332306", "349d19d5f9238b64607c265a97cee2e57558f49b2254a613efb80f334e4fef88", {0x3e56cac9U,0x3e56cac9U,0x3e56cac9U,0x3f7afafbU,0x3f00d280U,0x3f00d280U,0x3f00d280U,0x3f35b5b6U,0x3f36081fU,0x3f36081fU,0x3f36081fU,0x3ea8a8a9U}},
    {"filter/outline:outlineValueMap", "grayscale", "17137e5da9dba3919e6fc1a42221ddfd166388e8059fc671b73e04ea354041f2", "c6ded0a7986409c32fd2cea123458989295584a3857f5e856a6ccc0870d40eb1", {0x3df8f8f9U,0x3df8f8f9U,0x3df8f8f9U,0x3f41c1c2U,0x3ed0d0d1U,0x3ed0d0d1U,0x3ed0d0d1U,0x3f189899U,0x3efcfcfdU,0x3efcfcfdU,0x3efcfcfdU,0x3f0a8a8bU}},
    {"filter/spatter:spatter", "primary", "5afbc539989e16c64c435c55983653137ac366e3b9b7b19d11195561c5ac4a02", "2270dc9fe831c33940eb09df5ac36a0d97d8cd9793449e21924298df6b599cd4", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3ed4d4d5U,0x3e78f8f9U,0x3f50d0d1U,0x3f35b5b6U,0x3f1372a8U,0x3e5bc317U,0x3e00341fU,0x3ea8a8a9U}},
    {"filter/spatter:spatter", "fallbackResolution", "9ff37b3d2e8a719547a206af8f0cbc2af51024a37014608bc5842ca867f0afa9", "4314515902999d5f9ae734fc41592f1e76cd9d909e17f8b06efaa072e7c7187c", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3eb6cd06U,0x3da32d37U,0x3ee9ea53U,0x3f35b5b6U,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
    {"filter/tint:colorize", "mode0", "4825064c3814ffa24b771e07ff09a2bde7a38c9bed2046095b24458d6c41bc24", "781d9cfac8befe7dd4fd2afa5fddc51a517a99043b6953877d66a0082796e87c", {0x3deeda60U,0x3eecdd81U,0x3f03d32fU,0x3f7afafbU,0x3e69dab3U,0x3ecac694U,0x3f228ebeU,0x3f35b5b6U,0x3e21a483U,0x3e883e1bU,0x3e82481eU,0x3ea8a8a9U}},
    {"filter/tint:colorize", "mode1", "c42697e555dd57590f98e2e39904c49715d9c47f61208e57e28b357c8bbce5fc", "82e38f492645d1a4b3d53548f6e13c3ea45e27635327942874668589c38e4d85", {0x3cc82103U,0x3dbc2500U,0x3cc92d1eU,0x3f7afafbU,0x3e4bfa43U,0x3e491ebbU,0x3f228ebeU,0x3f35b5b6U,0x3e21a483U,0x3e883e1bU,0x3e4cc4c7U,0x3ea8a8a9U}},
    {"filter/tint:colorize", "mode2", "04c9eef319ed883cc4c06e5aaf499f904cec0395b9f3d4d58638e63cd3ddfc96", "fba3769da35e84e822d6c232b6d06bcb5274f138d8fb1a5e03fad67a20e58aa1", {0x00000000U,0x00000000U,0x00000000U,0x3f800000U,0x3d4ada88U,0x3f4081ddU,0x3f277441U,0x3f5ededfU,0x3e9d0db1U,0x3e8cd122U,0x3ecacacbU,0x3ecacacbU}},
    {"mixer/blendMode:blendMode", "mode0", "ea87899c030cceb2e2528b0c46eaf985b625d711c702fe2f0de4825db5aac4c8", "c23eb08bea0f5b812986d86bbbfc1257bf646adc08687a154c98b245db6bc69b", {0x3e20fd26U,0x3ed78d29U,0x3ebace62U,0x3f7cb772U,0x3f1095adU,0x3eeb68c2U,0x3f5f842cU,0x3f42bdbeU,0x3f645150U,0x3efe7f58U,0x3ecafe32U,0x3f320fc2U}},
    {"mixer/blendMode:blendMode", "mode1", "b70cbf27de486eb9b87c1979cc58518bfa563fe56d64f82938eff15f172b3605", "1218c3992fa95593198d8a4db3d524560c053f9d9666d9c0d84ad702808e79b2", {0x3d111f47U,0x3e19d979U,0x3da03d81U,0x3f7cb772U,0x3f09b089U,0x3edb94b2U,0x3f62b377U,0x3f42bdbeU,0x3f87946cU,0x40714833U,0x3e5eac70U,0x3f320fc2U}},
    {"mixer/blendMode:blendMode", "mode2", "3af7eeb846845b8f2cf1679507e0b6253e01154c4a66508c73358f191ee0f910", "9b4e23c9ec307a2c2e236ab890216674439fdafc029c8f69c5ad07360312ac13", {0x3d59590cU,0x3df8499bU,0x3d10629bU,0x3f7cb772U,0x3f036090U,0x3ec17f5cU,0x3f64455fU,0x3f42bdbeU,0x3f6986b6U,0x3ea768f2U,0x3e8c813eU,0x3f320fc2U}},
    {"mixer/blendMode:blendMode", "mode3", "8824db7451cbded9bee6001a66efbe97d028bf6211084e10095ee5a19d07befd", "8ae7b1bca6a5198f3d96ac6960e9fc27e0d269d0d53fcd5735e85d143911e6bd", {0x3df9c088U,0x3ed6037fU,0x3ecffcddU,0x3f7cb772U,0x3f1b193cU,0x3f1f4faeU,0x3f4a99a1U,0x3f42bdbeU,0x3f60c0e3U,0x3f2a3e8bU,0x3e90a826U,0x3f320fc2U}},
    {"mixer/blendMode:blendMode", "mode4", "fc4ae699520cd0ccd377589210227166bed8d596a8829690427d2938464d163d", "037b749d306552bbddb2565476bc0f054b25fc469de7d11f8cada6699743f20d", {0x3d795d8bU,0x3ed78d29U,0x3ebace62U,0x3f7cb772U,0x3f1095adU,0x3eeb68c2U,0x3f5f842cU,0x3f42bdbeU,0x3f645150U,0x3efe7f58U,0x3ecacafaU,0x3f320fc2U}},
    {"mixer/blendMode:blendMode", "mode5", "6f3d116b4ff4a4a342e0c92b79fd3648a59a3b4019185f504a2589ab41af8737", "db6d030f893ffdd318d9cf28cffca1c981da72c279fa264b38df64762bd32c5d", {0x3e15e5a6U,0x3ed1b2aeU,0x3ece8784U,0x3f7cb772U,0x3ef1d738U,0x3ef6a7a0U,0x3f267cbeU,0x3f42bdbeU,0x3eed2ce8U,0x3f254db9U,0x3ea36861U,0x3f320fc2U}},
    {"mixer/blendMode:blendMode", "mode6", "1de7ab826f1c0c28ce4d4488fec35433daf2509ff363db4f3da54cd3e19bb981", "d8d668ba11b14c6e90437161e2be02a2b5a059e55fc9e5b9f671fb2306d9d14c", {0x3d3d7d48U,0x3ef8709eU,0x3eed6f00U,0x3f7cb772U,0x3f28c473U,0x3f3ac538U,0x3f5ad41dU,0x3f42bdbeU,0x3f598747U,0x3eb64aa7U,0x3e96ec09U,0x3f320fc2U}},
    {"mixer/blendMode:blendMode", "mode7", "1718cb0ae8942ff41c9fc7474764acef23fcb84bbed9b706b6af1a93e4624b9d", "7d3e840db438e5a5d2af59851d1bccc6236de77a7c9e7fd3f8e4a248ddcca755", {0x3e0eeeb5U,0x3eea274cU,0x3ed4d95eU,0x3f7cb772U,0x3f2dc3e0U,0x3f2a3abcU,0x3f6f3a96U,0x3f42bdbeU,0x3f8a00c2U,0x3f2cbe93U,0x3eadd32cU,0x3f320fc2U}},
    {"mixer/blendMode:blendMode", "mode8", "b006434458d85c96ee56d3766e2604b1f81481d1cab85cb21521fac181126769", "af16a25f92129f219a9b82bad47dfe3284b944f32041b4bf71b0a3d87de9bec9", {0x3dc322e9U,0x3e9230c3U,0x3e62e76cU,0x3f7bd937U,0x3f0c1725U,0x3ee878faU,0x3f6005b3U,0x3f3c39baU,0x3f4a9931U,0x3efb5c21U,0x3e7ef3b0U,0x3f03320bU}},
    {"mixer/blendMode:blendMode", "mode9", "9d6215d4b071514bad6c14ea429176b3519a6dbdfaf15334c7fac9c73dffd5ce", "97f1e3c6458e510b1c6c40845820240a4885445b45a2d0a7addd66209a8ac78a", {0x3d274e47U,0x3e00759eU,0x3d163802U,0x3f7cb772U,0x3f147760U,0x3ee57b3aU,0x3f7653d1U,0x3f42bdbeU,0x3f8f4df7U,0x3eac59c5U,0x3e832120U,0x3f320fc2U}},
    {"mixer/blendMode:blendMode", "mode10", "beccc72d0c3f72d55f161ff7edf2b36774d26e962a62fe44db24263c10d79f29", "f0b20b51188566289cd6ec7dcc3a7d102ba050d93b7e226c25811575b75ef48a", {0x3e20fd26U,0x3eb0cf3aU,0x3e9be6e6U,0x3f7cb772U,0x3ec179acU,0x3e590be2U,0x3f2b2ccdU,0x3f42bdbeU,0x3f01607dU,0x3e9e817aU,0x3ecafe32U,0x3f320fc2U}},
    {"mixer/blendMode:blendMode", "mode11", "ddc011e5e9345c123bfe4d645bf9b09efd8ae75674b3f599cf5c79d7df6f6acc", "39315f6c71ae14628393905df82e42199f5622cc5e3cda1926717584fca2cd8d", {0x3d3d7d48U,0x3e2d0e09U,0x3d42f171U,0x3f7cb772U,0x3f28c473U,0x3f0fa69aU,0x3f5ad41dU,0x3f42bdbeU,0x3f598747U,0x3f554ca8U,0x3ea2f9e5U,0x3f320fc2U}},
    {"mixer/blendMode:blendMode", "mode12", "79aabf069857c8d58b6438e1a88952398dfa847b962e2c5e038256e8e64cff31", "a47f7b85af947ed4d7a135cc28ded70a9e3ce96e276172b5fd387404dbafc9e5", {0x3e93763fU,0x3dade111U,0xbc7fd50dU,0x3f7cb772U,0x3ecc64bbU,0x3e30e54dU,0x3f548ef5U,0x3f42bdbeU,0x3f39d683U,0x3e18d648U,0x3eaa1abfU,0x3f320fc2U}},
    {"mixer/blendMode:blendMode", "mode13", "584798e9c39f7f4eddbbcd00947c903519446aeeaef17f9472b7402ddab2a5bd", "a60bdaea3e17c405810ccee64e62f8dfbc2262d13c4720ebef64ae0a5078c5fc", {0x3e1b7166U,0x3ee7fee4U,0x3ed41eb1U,0x3f7cb772U,0x3f1cad10U,0x3f183ccdU,0x3f5d2c24U,0x3f42bdbeU,0x3f5eec4cU,0x3f2a462aU,0x3eb73349U,0x3f320fc2U}},
    {"mixer/blendMode:blendMode", "mode14", "f6dc097b11600713b0536ab93fd8054422519723023d9c174e0c0685a972995c", "e1d3075fdd072cd4a8c7a6b2c52bdccfe37bb09fea813067c3f16b9baf045f3b", {0x3de842b7U,0x3ee88a75U,0x3ec02d63U,0x3f7dbc7bU,0x3f3f4bd0U,0x3f47caf2U,0x3f73c31fU,0x3f4a6500U,0x3f8a5570U,0x3f3122f2U,0x3eb1a58bU,0x3f691c50U}},
    {"mixer/blendMode:blendMode", "mode15", "81853c7f9fe824ff21789e7be5440ddbc64cfe0496deeaa0f7098a15b763b0e6", "eafac90c37b5acf6bedb8478d08951a02e148f2072669b91582da75f1d784d7d", {0x3d111f47U,0x3da7ba67U,0x3cd2fd27U,0x3f7cb772U,0x3ee16bd8U,0x3eaba940U,0x3f3fa46bU,0x3f42bdbeU,0x3f60c0e3U,0x3f2a3e8bU,0x3e90a826U,0x3f320fc2U}},
    {"mixer/centerMask:centerMask", "shape0", "e843455954b3d2032c3e93115e4a825d9ee1e42acb273a48b734e6723af5f471", "fb2f4443eee54ea948b457ce3649677221ec44f45953624cc15fddfba05b9373", {0x3e2a86acU,0x3f1ad27cU,0x3f20b166U,0x3f7afafbU,0x3f088855U,0x3f3cbc9cU,0x3ed4d52cU,0x3f27a7a8U,0x3f771314U,0x3d503fffU,0x3e887ee1U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "shape1", "31457c401fb8921e363e574d88fb09f1032cb9b24699ec3e9011f415cf536097", "fee8357930b2f502a39de599779e8c8bfd1ff84c8077850164c723f0fd634076", {0x3e2b6ebaU,0x3f1b2758U,0x3f2116c2U,0x3f7afafbU,0x3f088880U,0x3f3cbcb7U,0x3ed4d4e4U,0x3f27a7a8U,0x3f77138eU,0x3d50836aU,0x3e886d3fU,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "shape2", "2e126851c0249629d5090a583df03c7e937c203c1079da09fa88f54a66923a88", "7d623d76815a34177e50522b0e9bd68c715ebea5f1ee6653677ea59400881fb0", {0x3e264ee4U,0x3f1947a2U,0x3f1ed9c3U,0x3f7afafbU,0x3f0887b7U,0x3f3cbc35U,0x3ed4d636U,0x3f27a7a8U,0x3f770a46U,0x3d4b65d4U,0x3e89c3c8U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "shape-1", "2e126851c0249629d5090a583df03c7e937c203c1079da09fa88f54a66923a88", "7d623d76815a34177e50522b0e9bd68c715ebea5f1ee6653677ea59400881fb0", {0x3e264ee4U,0x3f1947a2U,0x3f1ed9c3U,0x3f7afafbU,0x3f0887b7U,0x3f3cbc35U,0x3ed4d636U,0x3f27a7a8U,0x3f770a46U,0x3d4b65d4U,0x3e89c3c8U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend0", "93ca501740d03119a314b82f7202ce5b156fbdd325ccf167c9aa187da6416855", "0d371efb1919497b67625ce723aacfda45dd312469e50af051fa2c6330fc62c1", {0x3e2f40a1U,0x3f1d0ba9U,0x3f21fa79U,0x3f7afafbU,0x3f088cccU,0x3f3cbfd8U,0x3ed4e2a3U,0x3f27a7a8U,0x3f776930U,0x3da29c21U,0x3e923360U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend1", "62c7a654f916063c5d51e1b45eec07fa2469517e1d81bc5402a90d7267580022", "9f6bf1b61974bc84ef1bbadaf130656a2c950e25956d5d2e4b2914268cf0801b", {0x3e2425c0U,0x3f13ec70U,0x3f19a650U,0x3f7afafbU,0x3f08823cU,0x3f3cb7c4U,0x3ed4cca3U,0x3f27a7a8U,0x3f76bedbU,0x3d373c00U,0x3e859bc0U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend2", "0ab1fb551e8d07aa0c7cf063221912a532a303827185b01fd0bbba0c7c5e3e34", "d29144363b8a1ffe0b89e900304dc43d9459cdbafa63f1c4da8d6ec2e07247d1", {0x3e26b9b4U,0x3f155c7dU,0x3f19ff27U,0x3f7afafbU,0x3f08867fU,0x3f3cb892U,0x3ed4d4d5U,0x3f27a7a8U,0x3f733f1cU,0x3d40c0c1U,0x3e8b4293U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend3", "100ce03583f600e09e3487801192405159ec4ac4f0ad5b6b6b5488f8985d1aca", "7f555ee9dfa1754d4780fdc3dcba531706a07eff85cab1dec4df8001480fa1fc", {0x3e2a18b9U,0x3f1a2b8fU,0x3f2148cbU,0x3f7afafbU,0x3f088446U,0x3f3cb833U,0x3ed4d004U,0x3f27a7a8U,0x3f6e7cbbU,0x3d991760U,0x3e86e5baU,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend4", "6aef359281906cf40de0253bf39e120e58e62c69264dd223d1d7b25ffcb6ee22", "71b5f35b1782baf78252f8a2ab797167bdc4e598c768213c1a7a0141ef969344", {0x3e2d21f1U,0x3f1c9809U,0x3f21db4fU,0x3f7afafbU,0x3f088c17U,0x3f3cbfd8U,0x3ed4e2a3U,0x3f27a7a8U,0x3f776930U,0x3d52d10dU,0x3e8e8c0eU,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend5", "bfedb2a4868257ffd7ea553de095318e87ae091d61bb54d9267b6545e9f981ca", "0d9061f0d9467b951487dbadea8b67250ac9d437d98e9c01c9d725f83c16df5f", {0x3e2e620fU,0x3f1b4c3aU,0x3f218a4aU,0x3f7afafbU,0x3f088840U,0x3f3cba96U,0x3ed4d755U,0x3f27a7a8U,0x3f6f15ecU,0x3d9c604bU,0x3e8f190aU,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend6", "22f0799976e5a0ac0caf19797d36b077755ea58943c58babdb995064e6ede5fd", "c8357caa22caa438fcec4c5d6a1b8243a2f1cb1c6c15642d245d165b74063761", {0x3e250453U,0x3f15abdfU,0x3f1a167fU,0x3f7afafbU,0x3f0886c8U,0x3f3cbab9U,0x3ed4d85aU,0x3f27a7a8U,0x3f771defU,0x3d7c77cfU,0x3e88b616U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend7", "dec0da4b476749a889c4ac7ef6aab6ce9a7ac079ec2739e46581d1c702eb902c", "e2876d73c116a87db47d3be34c0aabc19839d9590cda6625d698040fc5cd131f", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f088889U,0x3f3cbcbdU,0x3ed4d9d6U,0x3f27a7a8U,0x3f76f6f7U,0x3d9dd9c0U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend8", "8058cc3b16c84c3aa9f211777a36ef40593b8a056144316781d99df14bcce0e1", "9720d7113676d477e495ebbb81aadb880f9e61c22d7cc277fbb339b8ce2560b4", {0x3e26b9b4U,0x3f155c7dU,0x3f19ff27U,0x3f7afafbU,0x3f08867fU,0x3f3cb892U,0x3ed4d9d6U,0x3f27a7a8U,0x3f733f1cU,0x3d9dd9c0U,0x3e8b4293U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend9", "bf03c907a37a4f4ffb63895587dd8a4726a014c970df45991b1219c13b7952df", "378164bbd61ba9f4b1d4720fd91e97847dcafccb0b110cc3921f6c2a83eee2fb", {0x3e249509U,0x3f14cc28U,0x3f19de67U,0x3f7afafbU,0x3f088482U,0x3f3cb760U,0x3ed4d12cU,0x3f27a7a8U,0x3f72f283U,0x3d3d77d6U,0x3e8728ebU,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend10", "d217fd2e3e0a36ec5a394aa10cb8b5cc392aa61efd143704c17580a1d5cf8600", "9f5b3bd4ba66262bb30efa61e9240766ce010cd838ab313dd42efce82b76a547", {0x3e2f40a1U,0x3f1d0ba9U,0x3f21fa79U,0x3f7afafbU,0x3f088cccU,0x3f3cbe68U,0x3ed4e19eU,0x3f27a7a8U,0x3f6f612dU,0x3da29c21U,0x3e923360U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend11", "0fd84c512bd5ace94817de17727694699cefb494c7c850769ba6302111c4d247", "80527316f793005a4f0b9ab483fdd60a82f3eae5ec6deb1311c53e8a60ca10ef", {0x3e250453U,0x3f17c722U,0x3f1d3a23U,0x3f7afafbU,0x3f088700U,0x3f3cbc05U,0x3ed4d756U,0x3f27a7a8U,0x3f771defU,0x3d43b3acU,0x3e88b616U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend12", "b1f2cd9d4c34c6cea4f042e41c43408e8e4ae82e9c2b9e5022e00fa5e6286a64", "f8280e6463bfee3f320b3bee1f70778cc999c4d596a3fff991c503c803667297", {0x3e50c409U,0x3f1a51a2U,0x3f1ea826U,0x3f7afafbU,0x3f088c02U,0x3f3cbbacU,0x3ed4dda2U,0x3f27a7a8U,0x3f73b155U,0x3d834725U,0x3e9d9a67U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend13", "89adc880ea981f299a436d1ddb8ffc66287bb9e70790b62cf21b7bd850ec598e", "de9fe75087ade4eb6229b313f14f19f0c1627f0518601ef71106bbfc4d1beca4", {0x3e2ed158U,0x3f1c2bf1U,0x3f21c262U,0x3f7afafbU,0x3f088a86U,0x3f3cbdeeU,0x3ed4dd7eU,0x3f27a7a8U,0x3f774390U,0x3d9f7e36U,0x3e90a635U,0x3f5ddddeU}},
    {"mixer/centerMask:centerMask", "blend15", "c3805de05b17fee053bd510bbc7a5dcd45d0cd1e04bf1993cb10861cbc56a6e5", "6776de4da65e05bdf73267c3cea164f5820516df7be227ba8cf5d49c2da7a106", {0x3e2a18b9U,0x3f1a2b8fU,0x3f2148cbU,0x3f7afafbU,0x3f088446U,0x3f3cb833U,0x3ed4cb03U,0x3f27a7a8U,0x3f6e7cbbU,0x3d373c00U,0x3e86e5baU,0x3f5ddddeU}},
    {"synth/media:mediaInput", "position0", "28ddcf45d29a5a34caca321e4639e27ddd9061362c6d2c00d2befa5e12c27991", "4943747335a017fc908706cae2864f9a6e23f3b19f5ea1c729584a1b4ddf8081", {0x3e78d0a9U,0x3e332599U,0x3e44905dU,0x3e9e9e9fU,0x3b7dfb04U,0x3ddb9652U,0x3dabf743U,0x3ea8a8a8U,0x3dadcae7U,0x3cf6ac69U,0x3e9fc6ecU,0x3eb2b2b1U}},
    {"synth/media:mediaInput", "position1", "ed5a45450ebbc1d9a6acbc633a555bafe7eb9f62029eafdbca34110b0210c76c", "fe825ea63ffe458ecb589f996d47fa4c4a24378ddae225398bdf584d735aec2e", {0x3e821bb6U,0x3f33db02U,0x3f22a2a3U,0x3f73f3f4U,0x3ef7ff06U,0x3ef7ff07U,0x3e965c22U,0x3f78f8f8U,0x3f3943cfU,0x3e837a74U,0x3f6f0d24U,0x3f7dfdfdU}},
    {"synth/media:mediaInput", "position2", "db65b544e7dd6ed25fe19d85ad9e7ae2d2a62759405906bdffacad929f4a4589", "8d037480d30162ea2458bb3ed9ebf4ef5c3d7a6d3aeb0c1a0519e12e0b70b4ad", {0x3ee0c0a1U,0x3ef4e8deU,0x3efaf4f0U,0x3f008081U,0x3d59d2ceU,0x3ebe9873U,0x3ea35e1aU,0x3f058585U,0x3e38b8b9U,0x3e837a72U,0x3e08e94aU,0x3f0a8a8aU}},
    {"synth/media:mediaInput", "position3", "869861cc2022b37eed2b125497f34118a60ec630e6c5640146aac9cff2bdd045", "0ad0fb9049a115cd1bc0e7469f451b77ea6101e8b56b600743b8652d1ae57546", {0x3ec7fb2fU,0x3df0f0f2U,0x3e909091U,0x3f19999aU,0x3f0bf55fU,0x3f186634U,0x3d865c32U,0x3f1e9e9fU,0x3d8fbeefU,0x3eec2763U,0x3ef3dac3U,0x3f23a3a4U}},
    {"synth/media:mediaInput", "position4", "365f74819fcb7f75bb26d4275ea7217cb29ac8836c69c2c91c68e27eee109c23", "8908965b141611865971e4bea0e24e9dc0169c60d7854226a2ac3150e52ff5cb", {0x3d02a4c7U,0x3db4987dU,0x3dfd9a38U,0x3e74f4f5U,0x3dc151e3U,0x3d0931dcU,0x3d2223a6U,0x3e848485U,0x3e29f33eU,0x3e7eecdcU,0x3e61dad5U,0x3e8e8e8fU}},
    {"synth/media:mediaInput", "position5", "5facfd3e69f9152d624e5ef3651e68d103109ae19f7844c99d175ccf4e28a418", "b7a446e81a7630c4bb29b5366d0ce81315490cf833915b60179ecb89401ec498", {0x3f164e06U,0x3eecfd0eU,0x3f27ccf2U,0x3f4acacbU,0x3f4a1b6dU,0x3e8f6e4eU,0x3ec053e8U,0x3f4fcfd0U,0x3e2a43deU,0x3db447dcU,0x3da6ed34U,0x3f54d4d5U}},
    {"synth/media:mediaInput", "position6", "ccb8e44755b57644bd2d75756355615ad790672d3bc873baa44cc0a951a8ce29", "52cd7d49a0f7937b64cef671fa6f64ac283d24c7d50d7bed3f1a735b77919bae", {0x3defdecfU,0x3d33e71bU,0x3c33e71bU,0x3eeeeeefU,0x3e702f6fU,0x3ed5d2d0U,0x3ea5015eU,0x3ef8f8f9U,0x3dae7d56U,0x3e77318fU,0x3ecb923aU,0x3f35c28fU}},
    {"synth/media:mediaInput", "position7", "80ddaea3c05f47448467c8828c572a364d70fa30054a323e10071b90c8eb450f", "f9f67a594af5dadc97827184242d4c2119f2f014f8337a49cdacb13751c53364", {0x3d9fdf1fU,0x3ce74db5U,0x3bf4e8deU,0x3dd8d8d9U,0x3df8f0eaU,0x3b61c2a5U,0x3db66c23U,0x3e008081U,0x3dae7d56U,0x3e77318fU,0x3ecb923aU,0x3f35c28fU}},
    {"synth/media:mediaInput", "position8", "c2d5d15d0951a0df47fc7aef500a169d19c5c14bc541143b9e46fb570e8f4fee", "ce0c65440fb4de43fce82e67720de16785adc85274259ebd58c00cfe586fefe9", {0x3e662b72U,0x3ea2b4c7U,0x3e805020U,0x3f28a8a9U,0x3ec6e0fcU,0x3e28e92aU,0x3c2e5c0bU,0x3f2dadaeU,0x3dae7d56U,0x3e77318fU,0x3ecb923aU,0x3f35c28fU}},
    {"synth/media:mediaInput", "tiling1", "96f967a54663481cb8e74ebad034c9e9a67bb92c810fb0ed78c3c0c7ab1cca2f", "7f23d380e2919aae8f292f50c0720be729ff1047a48c459c15d98670afa66276", {0x3ec3b6aaU,0x3e1b9692U,0x3ea7df17U,0x3ed0d0d1U,0x3d36f538U,0x3d573da6U,0x3e0613a6U,0x3e34b4baU,0x3e4447b7U,0x3e25a69cU,0x3dd11145U,0x3e66e6cfU}},
    {"synth/media:mediaInput", "tiling2", "5c930e431110ffdb95260526b3d0cd4c988946426f62375e2deb505e066f1671", "5e74eefaa556a3311d7279d121281b767734d22fa513fa29158bca988d552065", {0x3efd4187U,0x3ec71565U,0x3eefb67eU,0x3f2cacadU,0x3d36f538U,0x3d573da6U,0x3e0613a6U,0x3e34b4baU,0x3e4447b7U,0x3e25a69cU,0x3dd11145U,0x3e66e6cfU}},
    {"synth/media:mediaInput", "tiling3", "2e1a732625238546435ebb9270d1f3f17729a3b8c55782565a14fcb19b32facb", "b74113e03a57da06b7cf89a65bcd269ea7ef795da81ea16623e9dd4104b2997e", {0x3dae7d56U,0x3e77318fU,0x3ecb923aU,0x3f35c28fU,0x3d36f538U,0x3d573da6U,0x3e0613a6U,0x3e34b4baU,0x3e4447b7U,0x3e25a69cU,0x3dd11145U,0x3e66e6cfU}},
    {"synth/media:mediaInput", "flip1", "6ee9b8136b5591585f0762b17bff2a94d443ee048de0aa25669795ba3c283d6f", "4313513ab6f7fb8f56fd9eb0df720fd0df127826672debe19755e8e0b5679226", {0x3e29f33eU,0x3e7eecdcU,0x3e61dad5U,0x3e8e8e8fU,0x3dc151e3U,0x3d0931dcU,0x3d2223a6U,0x3e848485U,0x3d02a4c7U,0x3db4987dU,0x3dfd9a38U,0x3e74f4f5U}},
    {"synth/media:mediaInput", "flip2", "4135ab81ead9024e1354077586b278334ab0178465e249c3a2dee4447662c570", "9ac9e7ec94b9756868055029793e34266a4641d4d62b699d76bce89b1a67ce54", {0x3f1b0978U,0x3ee18224U,0x3d780f27U,0x3f33b3b4U,0x3dc151e3U,0x3d0931dcU,0x3d2223a6U,0x3e848485U,0x3f36aa9fU,0x3f054c13U,0x3e384fe8U,0x3f51d1d2U}},
    {"synth/media:mediaInput", "flip3", "7df66cf87e4ed72620101bd022158760f5f0dc7407ee98adf919234fa06e3bf0", "d037da9dc014534adabb63edef333df1b8338a5e0ce374e6f544cdc7f6d89031", {0x3f36aa9fU,0x3f054c13U,0x3e384fe8U,0x3f51d1d2U,0x3dc151e3U,0x3d0931dcU,0x3d2223a6U,0x3e848485U,0x3f1b0978U,0x3ee18224U,0x3d780f27U,0x3f33b3b4U}},
    {"synth/media:mediaInput", "flip11", "bd26178a2b1cebecc40ba26873adddb5ee2466d8001d9169b5ba5f312fd71966", "eb969ec2d498fa7aaec87612447500fe15e29779c5c1fb7d372866d209bd82a3", {0x3d02a4c7U,0x3db4987dU,0x3dfd9a38U,0x3e74f4f5U,0x3dc151e3U,0x3d0931dcU,0x3d2223a6U,0x3e848485U,0x3f36aa9fU,0x3f054c13U,0x3e384fe8U,0x3f51d1d2U}},
    {"synth/media:mediaInput", "flip12", "46f2279d9f38acf148934c027f103b5d9e960a0ff45b7a383dc28d1710b99cf1", "84c1bb2dd76b89464282fb24544d769cb7039b0a52594824eec7a1ef0d9cc46c", {0x3f1b0978U,0x3ee18224U,0x3d780f27U,0x3f33b3b4U,0x3dc151e3U,0x3d0931dcU,0x3d2223a6U,0x3e848485U,0x3e29f33eU,0x3e7eecdcU,0x3e61dad5U,0x3e8e8e8fU}},
    {"synth/media:mediaInput", "flip13", "3da28f3249136b7fa3ca1b7a3e9b566e8025771ee815f330eedb0c4091c543c2", "169d45be3448219e3bafe9e117796f478b2a585e6258c2630c74d4ca6ee4e894", {0x3d02a4c7U,0x3db4987dU,0x3dfd9a38U,0x3e74f4f5U,0x3dc151e3U,0x3d0931dcU,0x3d2223a6U,0x3e848485U,0x3f1b0978U,0x3ee18224U,0x3d780f27U,0x3f33b3b4U}},
    {"synth/media:mediaInput", "flip14", "377c19b2bf4fb8a10de45f69bb2eb71d3a3318b5cabef8552061285eed10056e", "036f1ad0c443124e78760c1706cda5698cd1be03f10880b878649280d9294a90", {0x3f36aa9fU,0x3f054c13U,0x3e384fe8U,0x3f51d1d2U,0x3dc151e3U,0x3d0931dcU,0x3d2223a6U,0x3e848485U,0x3e29f33eU,0x3e7eecdcU,0x3e61dad5U,0x3e8e8e8fU}},
    {"synth/media:mediaInput", "flip15", "7c06fc3c58933f4d6afe671d4f9fa0490203e4d9635381755a24c39dd9f88028", "15e335c7d5f1fc8731818d6ae0e1539e63ebca0daf62e8cf5dc382af7530e2ae", {0x3d02a4c7U,0x3db4987dU,0x3dfd9a38U,0x3e74f4f5U,0x3dc151e3U,0x3d0931dcU,0x3d2223a6U,0x3e848485U,0x3d02a4c7U,0x3db4987dU,0x3dfd9a38U,0x3e74f4f5U}},
    {"synth/media:mediaInput", "flip16", "00c53bdbc854cadad72cffefb2706c524a942ffc027731be273b7b388e1e3a95", "da4fb289cdb043d5e5ec67142974b300d6867089a26cecafa510ae0c2a149221", {0x3f36aa9fU,0x3f054c13U,0x3e384fe8U,0x3f51d1d2U,0x3dc151e3U,0x3d0931dcU,0x3d2223a6U,0x3e848485U,0x3f36aa9fU,0x3f054c13U,0x3e384fe8U,0x3f51d1d2U}},
    {"synth/media:mediaInput", "flip17", "7a52f3cf2dd979e4c652f331a7439fc74029ca8b47de9f0d7e1c0d0fccbf3fac", "ee7922a21dd36cccb47ba5671d8d0c47d4ec9dc8ff3ca7e0d532ea2ce1446c3f", {0x3f1b0978U,0x3ee18224U,0x3d780f27U,0x3f33b3b4U,0x3dc151e3U,0x3d0931dcU,0x3d2223a6U,0x3e848485U,0x3f1b0978U,0x3ee18224U,0x3d780f27U,0x3f33b3b4U}},
    {"synth/media:mediaInput", "flip18", "5423167cf3752eb9901317b913f1605319f99f7becd39dd1be485228d0a98c29", "67585c6eb1f30b50fcd0b744c3ef074b869fab092538ae302e6b67f0d8aad2df", {0x3e29f33eU,0x3e7eecdcU,0x3e61dad5U,0x3e8e8e8fU,0x3dc151e3U,0x3d0931dcU,0x3d2223a6U,0x3e848485U,0x3e29f33eU,0x3e7eecdcU,0x3e61dad5U,0x3e8e8e8fU}},
    {"synth/media:mediaInput", "outOfBounds", "fbd8055e725662d2d4d00c10fc63ad326d5f090d155293283a980a561cbb2ff7", "3b0002e018b563c702998518b7ea94d251abf6181a0d2d94cf02b19dcef64ad2", {0x3c9ad42cU,0x3eb7dbf4U,0x3f12c3caU,0x3f2147aeU,0x3c9ad42cU,0x3eb7dbf4U,0x3f12c3caU,0x3f2147aeU,0x3c9ad42cU,0x3eb7dbf4U,0x3f12c3caU,0x3f2147aeU}},
    {"synth/media:mediaInput", "transparent", "738c079dff6c9b77a0891ac42db1cabcab933a672b14aed8ecfcf94c0e77bb40", "24045c10c12a89f4c11e3b88ea34558fcdf926a8c1008cd08cc33bc71407c774", {0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U,0x00000000U}},
    {"synth/media:mediaInput", "scaleZeroGuard", "79a63249576cf470127d6ac47cde2a7f9f6f48bb728eac3053d0bee9cd9d13b4", "8908965b141611865971e4bea0e24e9dc0169c60d7854226a2ac3150e52ff5cb", {0x3d02a4c6U,0x3db4987cU,0x3dfd9a36U,0x3e74f4f3U,0x3dc151e0U,0x3d0931dcU,0x3d2223a4U,0x3e848483U,0x3e29f33eU,0x3e7eecdcU,0x3e61dad5U,0x3e8e8e8fU}},
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
    if (fixture.variant.ends_with("Far")) uniform("inputColor", noisemaker::glsl::DVec3(0.0));
    else if (fixture.variant == "mode2Near") uniform("inputColor", noisemaker::glsl::DVec3(230.0 / 255.0, 77.0 / 255.0, 179.0 / 255.0));
    else uniform("inputColor", noisemaker::glsl::DVec3(0.2, 0.6, 26.0 / 255.0));
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
    // createCanonicalBindings derives aspect from fullResolution (17 / 13).
    uniform("aspect", static_cast<float>(17.0 / 13.0)); uniform("patternType", pattern); uniform("scale", 5.4f);
    uniform("thickness", 0.57f); uniform("smoothness", 0.046f); uniform("rotation", 29.0f);
    uniform("skew", -0.31f); uniform("animation", std::int32_t(pattern == 0 ? 2 : pattern == 2 ? 1 : 0));
    uniform("speed", 3.6f); uniform("fgColor", noisemaker::glsl::DVec3(0.91, 0.17, 0.63));
    uniform("bgColor", noisemaker::glsl::DVec3(0.08, 0.72, 0.34));
  }
}

[[nodiscard]] noisemaker::BoundKernel bind_task12(
    std::string_view key, const noisemaker::glsl::Bindings& bindings) {
  if (key == "filter/hs:hs") {
    return noisemaker::historical_generated::bind_filter_hs_hs(bindings);
  }
  // The coalesce captures predate the copied UVs (26d6f42) and the GLSL
  // vector equality (8ae8e2a); they stay exact against the kernel they recorded.
  if (key == "classicNoisedeck/coalesce:coalesce") {
    return noisemaker::historical_generated::bind_classicNoisedeck_coalesce_coalesce(bindings);
  }
  // Scale's captures predate its 5976b7a6 global-pixel tiling change.
  if (key == "filter/scale:scale") {
    return noisemaker::historical_generated::bind_filter_scale_scale(bindings);
  }
  return noisemaker::generated::bind(key, bindings);
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
  return noisemaker::run_pass(bind_task12(fixture.key, bindings), 9U, 7U, 0.375f, 7.0f);
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
    {"mixer/patternMix:patternMix", "pattern0", "55276dcbc9d71676af6da34a3bab8776c096ba520960f406fa04a3e5a07eb9c0", "af4025978e4b82393bd1effbcd50c76ca30f49d9bef390c692d466bee2cd2e23", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern1", "76e70fe264836b27e776fcbcd0b55ede234f71a7f6296f854541018df41be6ce", "dca0bf61d0f2da97eae9eb320a41f08e0ebbd7950aa29caadda56a3e3751c704", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f0d9557U,0x3eb48f50U,0x3e1f60c6U,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern2", "917162de6c786337393b687c7b40a32612e9ab092424a65ef3b588b589d6708b", "452797aed5e7f7321af7611f9956c3a102e64eff18af272f9049d6eb8af2a035", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern3", "3b57ef7f2e37522e7137374d2c014608da280c85fb6d3d44c3a6650e10efa60b", "7f69f7e87413570590b6b0a0a3e089133f54fab1f54170fae0e149d10ad8f5f8", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern4", "c3b790a8028b194c5fc4f8900aeadb9c15fd7b3b26ee83eda281a1b86ed2e77e", "4c485721ff0a5b95fdb3ac98fba79b781134f30eefbe1265dfa23d5af863adc7", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern5", "09c2de279084718e368dce626c2f14ff7bfb7af2c82ab8d77c2557632656d7f6", "de0fdcc06eabd77f24f74db2074616e44cb9034fa98a876a424e10d97f826bb9", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern6", "9c48f07c9db53dfd05d25075801afa44167a28d5a63f8369aaaa1bceb4cd4f7f", "1fe233e421c852824c745f5c5ccc3990bb0551dbe5ba14ad59d58c3728556c80", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f2156b3U,0x3f2d4091U,0x3f0d414eU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern7", "28eae5c6287f01547bc06e9235ebf85956dc528e332fe01efe61c52f6776d745", "f228808ec0b5b63148684debce98e6254156c15228b5ad376c2a6fb901aafeff", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "pattern8", "8567e6c32453fc1cb5244f8f0d14e2de4df5aba72c2d0e7b4d84796ab7d39bd6", "5ebc3fbe6badafe0c77d7abeda38aed7543059da851fc0608de1826aca894dbb", {0x3e2b3efeU,0x3f1a1ba4U,0x3f1fcc57U,0x3f7afafbU,0x3f0ceea7U,0x3eaf171fU,0x3e120214U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "invert", "40dda92b2362d68ec20545d1a3df74bd1683525b9213524edfa87d91adcb4d0a", "3ca0b85cace99fb54b3b967322354110092ee3fe0231ea1d26046ab71b2b5df3", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "fallback", "dcef139e5081337b2b0f0fda51806028caea30439b72b47fdc1bc277b3dbb387", "8d66b0def717df10f6a07fef8a12af4ef3b963869e04efa7b11950d5ed27563b", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/patternMix:patternMix", "fullResolutionFallback", "c483c5c5e8fd0a9d7ae3282df34e03350c80fede95db95c5b7f16ffae4d70ad5", "91c947bebf55fb99bb0fa5fb2b0094d71184045ce280145ac25e5714bd7c6698", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape0", "773baa412771fc9c31bfbd2952099efc68113b7801bdf467dc175581d87e76b3", "a6817588b18cf21097b92b4534dd2f78eaf36e3cb20a89b481341c18f7a7dcb7", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f3eabc5U,0x3f006330U,0x3e721156U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape1", "e9592b1d07072210b73170fde3759ed5a48de0682885d0a91b617eeae2785c65", "1f965f4fe806a71b90dddaf1455b9124fefcf4bb6b2e97643e6d743ebcf66e3f", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape2", "0901838250f24b52e77f5a4ea480bfd1679a0be416ab78ea973dadb90f7d34f3", "094fd718fc0faf90c17fc9567820718f699c2d028d5b37494425dc07a40e3fcc", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape3", "88ea3e35a3ca017aede56ced3da96ad55e13fc64b8a7603e861f8830d8438961", "88a4c390041dae9e19b869f5f4ab1efa47ec7afeddbf4fd094b8a485531fcc64", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape4", "b327b7a170cd1b7bc7be9cd3380c9f71aef4c3e024ee4abea519597d0628611a", "6bd5a7c3311875778c238ac9ef8f558012d042250b16f7de29bd2ac75319ad8c", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape5", "0eae9e8b4ba0dd0c8a0d22df6db100bd91f29bd5212ae8655babf6a37272a2f7", "54614a0eaf345755b27bb7fa0c1e5d7783c8e5f145772d18e2d7badcade18c20", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape6", "a9248aa34050baf09eab9011c8657935bae8f5997e7b8b8d2fbd63a55e52c268", "8a6fd852e92c7ac2d72bb09f7d10b849528ef166e805db1a2ce29872a625099e", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f30a4edU,0x3f1d6045U,0x3e6857afU,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "shape7", "25421fd65121a6c6c43a8d7e9e7df3a62c938b61fc73ecc573b93ddd38dd0a4f", "04aef2a8c2307bf605eba0d6e0bb33accf3bfe60bcd2b1d276feb14499a759b0", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "invert", "fa2812cd1d9359324b438f9492d38783d3b7f38337b5f63e34bef4bab9e920a5", "e03d0d9c441bf6a98cc8204878dbb2757bb1c60ba7d114c9d180267d8eae62e4", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "animated", "6304562c932e79971c3ecfaf838bba47bf78fe3dc105f7c25ec21cba24b3c30a", "259bad1f6bee680a7f144c9da1f799cfe0c096638439890ad20fc1090408d328", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "fallback", "6d8a054edf819f9936b707cacd93c3de7a337ccda6a133f53402b64fbcc0df8e", "40938e0ba396d44cc2b6500c045542ff57fac15481b3c0560dff5e15359c43cb", {0x3de0e0e1U,0x3eb8b8b9U,0x3ea8a8a9U,0x3f7afafbU,0x3f189899U,0x3f088889U,0x3ec0c0c1U,0x3f1e9e9fU,0x3f515152U,0x3eb3b3b4U,0x3e7eff00U,0x3f5ddddeU}},
    {"mixer/shapeMask:shapeMask", "fullResolutionFallback", "6e4a11d224050dc706b75b6d9385a93aac96bf199813fbf297945ed7bd29cc00", "4d5d9863f5d1ecaf2205e3db3b625ad5c7863dc43a658f6d9182ded96aee6ce7", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/split:split", "static", "1ae0a501c271e6d56aae84dd180da6403d7bb0484e930efb82fdb81669c58644", "8a1196a09d9b5af630415993fb98066ec76288792cace264963cac6b936c9930", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/split:split", "animatedEven", "b3322e68b8bc9bf821f73be520d19627ba783082dad580d1a0b0b819d3f295bf", "cc65fbc09c50cc74ca53d3e59f35121c069c5852b06ec13dafdc19041461992f", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/split:split", "animatedOdd", "6304562c932e79971c3ecfaf838bba47bf78fe3dc105f7c25ec21cba24b3c30a", "259bad1f6bee680a7f144c9da1f799cfe0c096638439890ad20fc1090408d328", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f7afafbU,0x3f27a7a8U,0x3f47c7c8U,0x3f2dadaeU,0x3f1e9e9fU,0x3f76f6f7U,0x3d40c0c1U,0x3e8c8c8dU,0x3f5ddddeU}},
    {"mixer/split:split", "invertOdd", "dcef139e5081337b2b0f0fda51806028caea30439b72b47fdc1bc277b3dbb387", "8d66b0def717df10f6a07fef8a12af4ef3b963869e04efa7b11950d5ed27563b", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3f5ddddeU}},
    {"mixer/split:split", "fullResolutionFallback", "62df7796fc16fd58588186327e2a1a42ee7eacdfd0296007698ba00aea08c41b", "16ec7fb4bfad43541c99cceedbeb1daf0e134de6ca72c0eab7746dacc2efcccc", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f0d2564U,0x3eb0e2f0U,0x3e166615U,0x3f1e9e9fU,0x3f4bc791U,0x3eca97bfU,0x3e7b2806U,0x3f5ddddeU}},
    {"mixer/uvRemap:uvRemap", "map0_channel0_wrap0", "b7e71a5dc6bfeda0631c1be0ee5dfb94bf07d056ecc9f5921c636df61a19d9b7", "23845dad9c0e8a851e035b4bf6bd060041355cbf1ec0685bdf8e8c4e9ecdb616", {0x3f088889U,0x3f3cbcbdU,0x3ed4d4d5U,0x3e8e8e8fU,0x3f088889U,0x3f3cbcbdU,0x3ed4d4d5U,0x3e8e8e8fU,0x3f19999aU,0x3f6bebecU,0x3efafafbU,0x3e088889U}},
    {"mixer/uvRemap:uvRemap", "map0_channel1_wrap1", "515d685ec70b8a9ec91275012474bf628925c9d20fe6842f40020a3b149562f3", "ed1b7eb0eaa84787acb482a8f4cd3fc665bf26bef8bedf5bdd4adfc885e3f3f1", {0x3eb6b6b7U,0x3f55d5d6U,0x3f77f7f8U,0x3ea0a0a1U,0x3e70f0f1U,0x3f4acacbU,0x3f34b4b5U,0x3ecececfU,0x3f088889U,0x3f3cbcbdU,0x3ed4d4d5U,0x3e8e8e8fU}},
    {"mixer/uvRemap:uvRemap", "map0_channel2_wrap2", "baac9f4e5080444ad9bdacbb315d558ab14f87e188ca179bed30fdea66e1a3d6", "afa14f24903e5c8001f363edb1a3ee28ab4f6afa0d0bf63a4c1af5d1435a1d2c", {0x3f38b8b9U,0x3f76f6f7U,0x3f40c0c1U,0x3d30b0b1U,0x3e70f0f1U,0x3f4acacbU,0x3f34b4b5U,0x3ecececfU,0x3f19999aU,0x3f6bebecU,0x3efafafbU,0x3e088889U}},
    {"mixer/uvRemap:uvRemap", "map1_channel0_wrap0", "d1e078c456e5774d18be2d6b9b0ee39f906865e2065dd99fe371c8127872a03d", "e9f79085664a8e718f3cbafa7e5b431c962ea17da5b474370c5ed2f2aae36e5f", {0x3edadadbU,0x3f119192U,0x3f33b3b4U,0x3f028283U,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3eb8b8b9U,0x3ec4c4c5U,0x3f20a0a1U,0x3f27a7a8U}},
    {"mixer/uvRemap:uvRemap", "map1_channel1_wrap1", "39d9bb2c0717cc20cd1964504550350e8e86620d6c34b76fbf03dd5084a55938", "2e560e492ccf4847b7106242a62ebb379d10836fbff435c29e5921c9ed412847", {0x3df0f0f1U,0x3e989899U,0x3dd0d0d1U,0x3f55d5d6U,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f1a9a9bU,0x3ef0f0f1U,0x3e189899U,0x3ef2f2f3U}},
    {"mixer/uvRemap:uvRemap", "map1_channel2_wrap2", "ffd02d6b8a3e7f6f4769c7d9b7de74dd8b4dba2fd4bfd3406eacbc6c3d01f7d7", "f23ab9c97dc35424722b2d5b9eea7d8b9c18111cfc4e0fb935a51204f896b120", {0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U,0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU}},
    {"mixer/uvRemap:uvRemap", "fallbacks", "ffd02d6b8a3e7f6f4769c7d9b7de74dd8b4dba2fd4bfd3406eacbc6c3d01f7d7", "f23ab9c97dc35424722b2d5b9eea7d8b9c18111cfc4e0fb935a51204f896b120", {0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U,0x3e74f4f5U,0x3eaeaeafU,0x3ebababbU,0x3f3ebebfU}},
    {"synth/modPattern:modPattern", "blend0Anim0", "b77cf5d7486042b6c7a01a3db441f378c151d209d096da91ff59b419f83ac0ba", "3bacdcce424e877fc88d12cadfe0c9cfa6421651b12a150b2d3580c83375496d", {0x3f0763f1U,0x3f0763f1U,0x3f0763f1U,0x3f800000U,0x3f5719a7U,0x3f5719a7U,0x3f5719a7U,0x3f800000U,0x3cb0513aU,0x3cb0513aU,0x3cb0513aU,0x3f800000U}},
    {"synth/modPattern:modPattern", "blend1Anim1", "6d257a7a086951835e9085c0696198980c5faecfe53125d2d32a936a1fedeaba", "04d8112f92d355d0eb6a9a09439cb8d208f679918e95452700456e02f2423b4e", {0x3f2d0ddeU,0x3f2d0ddeU,0x3f2d0ddeU,0x3f800000U,0x3f532a37U,0x3f532a37U,0x3f532a37U,0x3f800000U,0x3f2d0ddeU,0x3f2d0ddeU,0x3f2d0ddeU,0x3f800000U}},
    {"synth/modPattern:modPattern", "blend2Anim2", "fcbc52a7be125e2544fe7065be01063c6335680a9f2db9e5337bc96847eece87", "c8ebfb4e079211cb3aabbdefab4fa5604c8f5314741d7926baa0d53300c8a421", {0x3f258de2U,0x3f258de2U,0x3f258de2U,0x3f800000U,0x3ec64896U,0x3ec64896U,0x3ec64896U,0x3f800000U,0x3ea98b9aU,0x3ea98b9aU,0x3ea98b9aU,0x3f800000U}},
    {"synth/modPattern:modPattern", "blend3", "52034d63b98360f190a1251be71f5673edafefca022d94b493fd842e72218d61", "de2e3c5329b0b51c6fbb2be34c7562ca03c3c2542d5515e548c62a1022d68e83", {0x3f0973e4U,0x3f028f0cU,0x3ef6c200U,0x3f800000U,0x3f333334U,0x3f0cccf4U,0x3f17197eU,0x3f800000U,0x3f0fc10cU,0x3f2600d0U,0x3f4fc0b0U,0x3f800000U}},
    {"synth/pattern:pattern", "pattern0", "e1d32d01340b1f58464d1d98fa4094ad28ec39819d43853f4607c8b6640fe9b2", "ca1d04679ed8b368a7b29b5fbc531b764397b2a849408fdbd0e165ff0570f6aa", {0x3f3c726bU,0x3e920880U,0x3f11ba2dU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern1", "0734372feac864461db315ae90ed8b9e6eea2a196077f4f0c989c546d84b046b", "f4ee2440e3aa71facc4f025e0cba79e39dcd46dd541ace1ae97061626df6d1dd", {0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern2", "73dcea4760d850b9135c877072f30cad0ed91834c852fa484c67ff8687d64652", "7f8dadde66ba035a2cee0965e8284afb282cdc1a190a11d373b69311756b383d", {0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3f2ab044U,0x3ea99185U,0x3f0b85c3U,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern3", "5e75fd0800fbcbfbb00de5ecbe03675e75cd98b98898acab943b4b3e01e80b60", "26f6a2a673175ac76cbe62cf5ad156d2dd5b90766d047a5bb5a02d8550f64d19", {0x3da6b768U,0x3f3814edU,0x3eae54cdU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3f5f506dU,0x3e47a5b3U,0x3f1de8e7U,0x3f800000U}},
    {"synth/pattern:pattern", "pattern4", "c82226cac8d8c2e80cad73dd2a7778a1b620137d15bd19d536de8b1be7c8535e", "849016ff094cad49f0980bdcd5318b842a624c9aab677d541f963fdbad8148a5", {0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3f61c0c3U,0x3e412ed7U,0x3f1ec30bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern5", "9cbb62817bc703b716d58a004111c52516ef9d8fde76568de1602dc603b8d0dc", "b221779fa68eeff9aa260cdc603e8d98cddbc05f6bbedaa193448cb5b3901877", {0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern6", "42057c757d66845534951faf309c77d4d2ec3bc0a357931066d2d48d7508f7ca", "dff7cdcdae2efc78499056be846b37d5ff52e858b5284c3d943347d6a6ed9c27", {0x3dcda7bbU,0x3f34db3cU,0x3eb1bb87U,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern7", "62e3bd17d71e94ce1d1a9632960d103bdd02cfe283e9bb200a3b9452be3e86bc", "1ddddc6a9cc2236cb41082b5cf1664b519d92d2b496384ed28ea1d9b71990e22", {0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3f5f506dU,0x3e47a5b3U,0x3f1de8e7U,0x3f800000U}},
    {"synth/pattern:pattern", "pattern8", "9d67bcabd1df519bcaa2a0ee0e9d2c0151272d6bcc70fd44a687518fcb16aa4b", "34e187dc994c95c4bc896fe9085d3541b8c392f460544e6b1604c4e17fb0e555", {0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern9", "7b763e35adcfcd76471c8c22cd00aa2709098fa164006423068d9490a36f6e46", "ebd286e5c3f416fe198f3f860382c1eea30a1f881352f3fcf3ff7bfed961cd03", {0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3f68f5c3U,0x3e2e147bU,0x3f2147aeU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern10", "403f74029a604d59fe65c73c7e78867d06e50bad2904c8a7d1cf0d01f16c4184", "e6a072e7c8906a52da8e513ac8c3ebd0e397487a48bac7cf2644f14d499a91e9", {0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3ed6557cU,0x3efdc0f0U,0x3eeaa80cU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
    {"synth/pattern:pattern", "pattern11", "b39c715e7ea927fac94c7a06d3cbea676a252a9386eeb7185d3b473d026a1282", "a6b65a7cdd45fc2d6453865c52252e2e86eb6843d8d761743fdfa05b9c083d7c", {0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U,0x3ec6a90aU,0x3f0411e5U,0x3ee52e1bU,0x3f800000U,0x3da3d70aU,0x3f3851ecU,0x3eae147bU,0x3f800000U}},
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
    REQUIRE_THROWS_AS(bind_task12(item.key, missing), noisemaker::glsl::KernelBindingError);
    noisemaker::glsl::Bindings wrong;
    populate_task12_bindings(wrong, fixture, tag1, tag23, tag37, constant_a, constant_b, hue_negative);
    wrong.set_uniform(std::string(item.uniform), item.wrong);
    REQUIRE_THROWS_AS(bind_task12(item.key, wrong), noisemaker::glsl::KernelBindingError);
  }
  for (const SamplerFixture& item : samplers) {
    const Task12Case fixture{item.key, item.variant, "", "", {}};
    noisemaker::glsl::Bindings missing;
    populate_task12_bindings(missing, fixture, tag1, tag23, tag37, constant_a, constant_b, hue_negative, item.sampler);
    REQUIRE_THROWS_AS(bind_task12(item.key, missing), noisemaker::glsl::KernelBindingError);
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
                        ? noisemaker::glsl::DVec3(0.7, 0.2, 0.9)
                        : noisemaker::glsl::DVec3(0.31, 0.83, 0.52));
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
    {"filter/bloom:brightPass", "softKnee", "2d221272df93e9ec7179b70342cc90f899bb205d6c24fbdf97b55e4386c00ae2", "f37355d9e280dc7b56db4fb66868e9201c904b687333138c62c3ff5f7bda31ab", {0x00000000U,0x00000000U,0x00000000U,0x3e808081U,0x3f70f0f1U,0x3f61e1e2U,0x3f52d2d3U,0x3f40c0c1U,0x3f7afafbU,0x3f75f5f6U,0x3f6bebecU,0x3f5cdcddU}},
    {"filter/bloom:brightPass", "below", "39db1c2790da52b4ec7590014d7f438a3a2b4d4cc6ca5f6ed6c38fb60de27192", "17b3576fb2405e4d1dee78a343a9d8e473409056c8c1cd0fcb38b9659df20a6a", {0x00000000U,0x00000000U,0x00000000U,0x3e808081U,0x00000000U,0x00000000U,0x00000000U,0x3f40c0c1U,0x00000000U,0x00000000U,0x00000000U,0x3f5cdcddU}},
    {"filter/bloom:brightPass", "above", "e817cda4b3759b575fdb3778177564544800f2df625f2129ef3709001c6702ed", "48b6681702181716a45c4a1e76d1c0992208d454fb8825ebe107ac8adee4ccdb", {0x3d50d0d1U,0x3da0a0a1U,0x3df0f0f1U,0x3e808081U,0x3f70f0f1U,0x3f61e1e2U,0x3f52d2d3U,0x3f40c0c1U,0x3f7afafbU,0x3f75f5f6U,0x3f6bebecU,0x3f5cdcddU}},
    {"filter/bloom:composite", "zeroIntensity", "82dce1fda9a7c8bf9e8c8ac5e3e92804ed3d75a68246f705f9f37ed379526e66", "97b2a11438e374e306befe0d6d844374c576f5e68fd5723d282b7f13a92747ab", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
    {"filter/bloom:composite", "tintedHDR", "1406691b8909ecbdb4ec8601b8ed1d7f0af7838cb43c26995b382f4524bca398", "bcc786af67740040a8764308603f4e76ab20a6687b586698b12d42890b0ae944", {0x3e0f3412U,0x3f78ad29U,0x3f15e8dbU,0x3f7afafbU,0x3f637a86U,0x3edc3b77U,0x3f12dea6U,0x3f1e9e9fU,0x3f904c13U,0x3fca1ba6U,0x3f6b9ab6U,0x3ea8a8a9U}},
    {"filter/fibers:fibersBlend", "alpha0", "82dce1fda9a7c8bf9e8c8ac5e3e92804ed3d75a68246f705f9f37ed379526e66", "97b2a11438e374e306befe0d6d844374c576f5e68fd5723d282b7f13a92747ab", {0x3d50d0d1U,0x3de8e8e9U,0x3ce0e0e1U,0x3f7afafbU,0x3f09898aU,0x3e929293U,0x3d989899U,0x3f1e9e9fU,0x3f2babacU,0x3f27a7a8U,0x3e64e4e5U,0x3ea8a8a9U}},
    {"filter/fibers:fibersBlend", "alpha0p53", "ab16d60f5002784bf79c7ff1e69e8c4b88189962b491acdd8e1e6eda71f98022", "a914338ee1630fe92a0530dbd76ea90741b2fa9431f684ccaa1909af64be8996", {0x3ec22d18U,0x3e184f8cU,0x3e900843U,0x3f7afafbU,0x3f2f42b5U,0x3e83a1f4U,0x3e9f2995U,0x3f1e9e9fU,0x3f44b1eaU,0x3efa26f8U,0x3ecf131aU,0x3ea8a8a9U}},
    {"filter/fibers:fibersBlend", "alpha1", "2200817335871e52518207a88e870a097b77916b44cea500c8b67f42fdedda6a", "fdc4b4d6db28e6a43aab5821dae93bc181276e39bd129de2f409f56a725f0e7e", {0x3f2b9c8eU,0x3e381b7fU,0x3f01a5caU,0x3f7afafbU,0x3f50b69dU,0x3e6cc49dU,0x3f053cf5U,0x3f1e9e9fU,0x3f5ae2ebU,0x3eaea297U,0x3f109ba7U,0x3ea8a8a9U}},
    {"filter/normalize:apply", "range", "f356eaa3b7988d2ee755c2b8d817ff7b31b1ae9c5627759d02b8d6ad3794c7bb", "81c9865d59ee655b83ae4731bbef4176ed494ec0e2b80f664471af99787ed27d", {0x3d9c9c9eU,0x3f3c3c3dU,0x3f454546U,0x3f0c8c8dU,0x3f52d2d4U,0xbcc0c0c0U,0x3f2babacU,0x3f7dfdfeU,0x3f8fcfd0U,0x3f4e4e4fU,0x3f80c0c1U,0x3f0e8e8fU}},
    {"filter/normalize:apply", "flat", "02bf5200e916b1d1f11dacdfe211ada7f4fd4eb9dbdb002e5dc27e0595c202d6", "7b6336be201d130d239718d7929093ddb4208cb7da2c57abd59fb0882fea05ad", {0x3e2cacadU,0x3f1b9b9cU,0x3f21a1a2U,0x3f0c8c8dU,0x3f2aaaabU,0x3dd0d0d1U,0x3f109091U,0x3f7dfdfeU,0x3f5ddddeU,0x3f27a7a8U,0x3f49c9caU,0x3f0e8e8fU}},
    {"filter/pixelSort:luminance", "heterogeneous", "e27aaa19da93167411e82c57df61c1d2b88fc1e754653b57a399189410b030b1", "a812ed4c6e1a3b2ff090835d34580b04ff93e0cd63acc0fa2b1b20861d2464f7", {0x3e41f0bdU,0x00000000U,0x00000000U,0x3f800000U,0x3f6aee6dU,0x40000000U,0x00000000U,0x3f800000U,0x3f78a56eU,0x40800000U,0x00000000U,0x3f800000U}},
    {"filter/pixelSort:luminance", "nonSquareClamp", "f37457b79270b6ec6714eb637ac6909fd12bc229375ffd9fd9b5cfa4f83389a2", "3fa0c609edd0db5600997f03fe7c6c3a2dfc81bcca283f0d83018d2687160e51", {0x3f177e79U,0x00000000U,0x00000000U,0x3f800000U,0x3eed6c8cU,0x3f2aaaabU,0x00000000U,0x3f800000U,0x3f38f5f2U,0x3faaaaabU,0x00000000U,0x3f800000U}},
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
      {"filter/tetraCosine:tetraCosine", "hsv_backward", "7eee48c86ccf86c03421772eace072c3f2ad8e19f81786479a6a2b361b96b13a", "7cd16bb3a3519e49bdb849692905d104697ae4243da91fd0c2de6e622c389652",
       {0x3eda8cd7U,0x3f2f9d3dU,0x3f332b09U,0x3f0c8c8dU,0x3f1ba2bcU,0x3dd287d8U,0x3ecba875U,0x3f7dfdfeU,0x3f6bdc80U,0x3f4be05bU,0x3f6003dbU,0x3f0e8e8fU},
       {0.40999999642372131f,0.0f,0.0f,0.0f,0.0f}, {std::int32_t{1},std::int32_t{-1},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(11.0f, -4.0f), noisemaker::glsl::Vec2(29.0f, 17.0f), 0.875f, 23U, 0U},
      {"filter/tetraCosine:tetraCosine", "oklab_forward_alpha1", "de876f55185ae679ef08f64b378f3becfeb5d4116fd080cdf92d71a1298bfa5c", "997b17922a9430c278738815712c5397179782a4622c758689f60c8cd665ef4d",
       {0x3e07abccU,0x3e404c08U,0x00000000U,0x3e8c8c8dU,0x00000000U,0x3bffdbd5U,0x00000000U,0x3f6aeaebU,0x00000000U,0x3e6ae0deU,0x00000000U,0x3f179798U},
       {1.0f,0.0f,0.0f,0.0f,0.0f}, {std::int32_t{2},std::int32_t{1},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(-13.0f, 9.0f), noisemaker::glsl::Vec2(23.0f, 19.0f), 0.625f, 37U, 0U},
      {"filter/tetraCosine:tetraCosine", "oklch_static", "fbe8d47b9b36d3831a545c1202bfde0cbc2fa12cfbe7d586e7428e9a1f81a545", "37d73498ed162e762ad727491cf4e4c71b71ebf1082e6a18c74c100f97f94642",
       {0x3e1c5ef0U,0x3f47e69eU,0x3f611447U,0x3f76f6f7U,0x00000000U,0x3d775dc7U,0x3d5caab4U,0x3f23a3a4U,0x3ea0c83dU,0x3ee77551U,0x3ea8bbb5U,0x3e50d0d1U},
       {0.77999997138977051f,0.0f,0.0f,0.0f,0.0f}, {std::int32_t{3},std::int32_t{0},std::int32_t{0}}, false,
       noisemaker::glsl::Vec2(5.0f, -11.0f), noisemaker::glsl::Vec2(31.0f, 13.0f), 1.125f, 53U, 0U},
      {"filter/tetraCosine:tetraCosine", "fallback_rgb", "56ea9dc5efa1d68b26fabd685d8cebd27e1dc1f50f2af47d2ed106f6d1813251", "8d69403bfa852d5539953cee28bec937ba8e8ec7f76ab34eaae4ceebc4232550",
       {0x3d20c9c0U,0x3db3572eU,0x3e0b8e59U,0x3f7afafbU,0x3f08f3ceU,0x3e6564e2U,0x3e8295aaU,0x3f1e9e9fU,0x3f35966aU,0x3f2e7b90U,0x3ec70004U,0x3ea8a8a9U},
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
      {"synth/osc2d:osc2d", "sine", "a61c2e3162b18715155a00279875229f618222ef2e4dcb0c3d78f29193ff285a", "4bfec778c247090c5d41c9190ef0334ad8be400b9cfe2a3f70e6153f1e720614",
       {0x3f7fa3b9U,0x3f7fa3b9U,0x3f7fa3b9U,0x3f800000U,0x3f71d9fcU,0x3f71d9fcU,0x3f71d9fcU,0x3f800000U,0x3f40465aU,0x3f40465aU,0x3f40465aU,0x3f800000U},
       {0.0f,-137.0f,0.0f,0.0f,0.0f}, {std::int32_t{0},std::int32_t{3},std::int32_t{7}}, false,
       noisemaker::glsl::Vec2(-7.0f, 5.0f), noisemaker::glsl::Vec2(17.0f, 13.0f), 0.0f, 0U, 0U},
      {"synth/osc2d:osc2d", "linear", "7a485417e8ccef4600b83f86a835dcc3d8020f397a68b11d0c839bd6562098bc", "c2e38caaccb5587a1bc3cad4f4649eb3554f58d0f3f2e9145ef5dea5e204f780",
       {0x3f208ddcU,0x3f208ddcU,0x3f208ddcU,0x3f800000U,0x3e91a3b0U,0x3e91a3b0U,0x3e91a3b0U,0x3f800000U,0x3f4dce82U,0x3f4dce82U,0x3f4dce82U,0x3f800000U},
       {2.5f,-45.0f,0.0f,0.0f,0.0f}, {std::int32_t{1},std::int32_t{5},std::int32_t{19}}, false,
       noisemaker::glsl::Vec2(11.0f, -4.0f), noisemaker::glsl::Vec2(29.0f, 17.0f), 0.375f, 0U, 0U},
      {"synth/osc2d:osc2d", "saw", "9e6de7bafe1b231fb1aead2b29d51e0d56a3294e3b1e0249774a40b02e563514", "116f3bcee7193882d637f80e80b34d6d92a5f00a8378b485b2d56c44b8b0bb5a",
       {0x3f6de50cU,0x3f6de50cU,0x3f6de50cU,0x3f800000U,0x3f52f286U,0x3f52f286U,0x3f52f286U,0x3f800000U,0x3f380000U,0x3f380000U,0x3f380000U,0x3f800000U},
       {4.25f,0.0f,0.0f,0.0f,0.0f}, {std::int32_t{2},std::int32_t{7},std::int32_t{37}}, false,
       noisemaker::glsl::Vec2(-13.0f, 9.0f), noisemaker::glsl::Vec2(23.0f, 19.0f), 0.875f, 0U, 0U},
      {"synth/osc2d:osc2d", "saw_inverse", "0ee1dcff5b021bd61d9da61e9b8edd4bdcbb8bf7f09f1a9a989ff275b12e89a6", "90874942992564638fcce2eb5d18071d3fe0ec92bb272060e6f054c26caf083a",
       {0x3f3cfa26U,0x3f3cfa26U,0x3f3cfa26U,0x3f800000U,0x3f1d4f72U,0x3f1d4f72U,0x3f1d4f72U,0x3f800000U,0x3efb4950U,0x3efb4950U,0x3efb4950U,0x3f800000U},
       {1.5f,67.0f,0.0f,0.0f,0.0f}, {std::int32_t{3},std::int32_t{11},std::int32_t{61}}, false,
       noisemaker::glsl::Vec2(5.0f, -11.0f), noisemaker::glsl::Vec2(31.0f, 13.0f), 1.125f, 0U, 0U},
      {"synth/osc2d:osc2d", "square", "23b9c9abc5ed2ee739721091b7943a9b1ccae4afb25c3c4e7428cb5b4b7b00e5", "c93df3a479520043925f5e5599fa0fa88dd52897666cce725e9869d656bbf7ff",
       {0x3f800000U,0x3f800000U,0x3f800000U,0x3f800000U,0x00000000U,0x00000000U,0x00000000U,0x3f800000U,0x00000000U,0x00000000U,0x00000000U,0x3f800000U},
       {3.75f,179.0f,0.0f,0.0f,0.0f}, {std::int32_t{4},std::int32_t{13},std::int32_t{83}}, false,
       noisemaker::glsl::Vec2(-17.0f, -3.0f), noisemaker::glsl::Vec2(37.0f, 21.0f), 1.75f, 0U, 0U},
      {"synth/osc2d:osc2d", "noise1d_resolution_fallback", "8bd374ca709e7f920773c9d3ed4d23152f468bf9cd33e52837e7483e76a2e830", "dfd849d2041931900a7789de24b9ebb1455eef8b12f70d461c222238aac5ee47",
       {0x7fc00000U,0x7fc00000U,0x7fc00000U,0x3f800000U,0x7fc00000U,0x7fc00000U,0x7fc00000U,0x3f800000U,0x7fc00000U,0x7fc00000U,0x7fc00000U,0x3f800000U},
       {5.5f,-91.0f,0.0f,0.0f,0.0f}, {std::int32_t{5},std::int32_t{17},std::int32_t{101}}, false,
       noisemaker::glsl::Vec2(-19.0f, 7.0f), noisemaker::glsl::Vec2(0.0f, 0.0f), 0.625f, 0U, 0U},
      {"synth/osc2d:osc2d", "noise2d", "f168e2f7bf106b39e942d01670aaf1a1dda13d8739af905028d28c036023d469", "7c8248ee174fed8f16df9ca208c6ff6cb333d56dcc74d2b3cff731593d997582",
       {0x3e54e3a2U,0x3e54e3a2U,0x3e54e3a2U,0x3f800000U,0x3edfa807U,0x3edfa807U,0x3edfa807U,0x3f800000U,0x3f445678U,0x3f445678U,0x3f445678U,0x3f800000U},
       {7.25f,31.0f,0.0f,0.0f,0.0f}, {std::int32_t{6},std::int32_t{23},std::int32_t{251}}, false,
       noisemaker::glsl::Vec2(9.0f, -15.0f), noisemaker::glsl::Vec2(41.0f, 27.0f), 0.9375f, 0U, 0U},
      {"synth/osc2d:osc2d", "fallback_noise2d", "abd33859158ce69787a758d085ed0fa4cc146b8fe26441e56004ff7db2cc0e44", "4d1b274fc2d3ce198ff08813ee102af65afe6c7b2eb77c367a89794b5c7bf5a9",
       {0x3c783120U,0x3c783120U,0x3c783120U,0x3f800000U,0x3e942562U,0x3e942562U,0x3e942562U,0x3f800000U,0x3efed66bU,0x3efed66bU,0x3efed66bU,0x3f800000U},
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
    // createCanonicalBindings derives aspect from fullResolution (NaN for 0 / 0).
    uniform("aspect", static_cast<float>(static_cast<double>(fixture.full_resolution[0]) /
                                         static_cast<double>(fixture.full_resolution[1])));
    uniform("time", fixture.time);
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

constexpr std::array<Task15Binding, 241> kTask15Bindings{{
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
    {"filter/lowPoly:lowPoly", "LP_BORDER", Task15BindingType::integer},
    {"filter/lowPoly:lowPoly", "LP_LIGHT", Task15BindingType::integer},
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
    {"filter/morphology:morphA", "SHAPE", Task15BindingType::integer},
    {"filter/morphology:morphB", "inputTex", Task15BindingType::sampler},
    {"filter/morphology:morphB", "resolution", Task15BindingType::vec2},
    {"filter/morphology:morphB", "mode", Task15BindingType::integer},
    {"filter/morphology:morphB", "radius", Task15BindingType::scalar},
    {"filter/morphology:morphB", "SHAPE", Task15BindingType::integer},
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
    {"filter/relief:rlBlurH", "MODE", Task15BindingType::integer},
    {"filter/relief:rlBlurV", "inputTex", Task15BindingType::sampler},
    {"filter/relief:rlBlurV", "resolution", Task15BindingType::vec2},
    {"filter/relief:rlBlurV", "smoothness", Task15BindingType::scalar},
    {"filter/relief:rlBlurV", "MODE", Task15BindingType::integer},
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
        // Every vec3-tagged entry in kTask15Bindings (hatch's inkColor/
        // paperColor, lowPoly's edgeColor, mixer/shadow's color, gradient's
        // color1..4, mandala's fgColor/bgColor) is an ordinary
        // effect-parameter vec3 uniform, now a double-precision carrier
        // (see emit_typed_cpp.py's `_is_double_vector_uniform`); none is
        // the size/motion/solid-color exception.
        bindings.set_uniform(name, noisemaker::glsl::DVec3(0.2, 0.4, 0.6)); break;
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
  REQUIRE(kTask15Bindings.size() == 241U);
  REQUIRE(sampler_count == 46U);
  REQUIRE(uniform_count == 195U);
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
    {"filter/highPass:hpBlurH", "defaults", "8236b577387743872f6dd1be310704c5ce83261aab2015bbd2485a5045723480", "648317dbe4dca77d58f75f79aac80e1f37160c1ae3b1bd19a8b812fd4a103a9b",
     {0x3f0271deU,0x3f186d3eU,0x3e39df54U,0x3f0a1560U,0x3eb19d9aU,0x3ec55554U,0x3f254aafU,0x3f3f66f0U,0x3f2bce82U,0x3f4de936U,0x3eb668d9U,0x3f161f59U}, std::int32_t{-1}, false},
    {"filter/highPass:hpBlurV", "defaults", "252cb0e30920d389a8816e366333767a3db25c27ce6aa043d61ce08a5ac2da42", "95302c80b39de9fee85b33cfec93a9e83bb944efe07130c5b96dbc53594fa144",
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
    {"filter/relief:rlBlurH", "defaults", "4468ec5774718a8ebbcc18908b93f4df24be1f78fcc79e7bb4ae7bf3b8532f61", "6816f44a2cd8dbd703711c4be0912537b1a2e1b4fffd357dec013669035391d3",
     {0x3f05581dU,0x3f234643U,0x3e18ea96U,0x3f07dd5fU,0x3ed119abU,0x3ec55555U,0x3f194deeU,0x3f2a0afcU,0x3f2e4403U,0x3f63b806U,0x3ed865b0U,0x3f19b28eU}, std::int32_t{-1}, false},
    {"filter/relief:rlBlurV", "defaults", "522aa82273bd2a5398b05f0af9b42c6fb944829436245357d9820fac2d803858", "80e3532bb2f021143b3e12c1191266358d1e6b7d0e582e1e03d98d705ba087b0",
     {0x3f01cbc3U,0x3f2495eeU,0x3ea74154U,0x3f0755afU,0x3efb1b80U,0x3f02f0f8U,0x3edf39e9U,0x3f29bfa5U,0x3f1ccf72U,0x3f4463cfU,0x3ee871ceU,0x3f2dd50aU}, std::int32_t{-1}, false},
    {"filter/stamp:stBlurH", "defaults", "a5a2ea43e7d89e4ec741f3d3aea7586ff13d274fc05e2658c27b14704fb935bc", "69b2f914d0063d06ad3f002dfd7aac83fe8ac12f36ba57ca5dee57f482a0b229",
     {0x3f065561U,0x3f1b055dU,0x3e1b903eU,0x3f097536U,0x3ec9325cU,0x3ec55555U,0x3f1f0f3fU,0x3f3305a4U,0x3f313a67U,0x3f5cc812U,0x3ecb8693U,0x3f18d9abU}, std::int32_t{-1}, false},
    {"filter/stamp:stBlurV", "defaults", "182bc2b599d8082591a0a3cc70bae2e171a31fa72636343b8498a90ed90e2b36", "e78946cddeb62c71f1ae61066b73966b9c45895e216d3cdea8e4ca5c7a300046",
     {0x3efc693fU,0x3f21de95U,0x3e9726feU,0x3f060d1fU,0x3f07d0edU,0x3efcd94bU,0x3efda2e4U,0x3f2324e3U,0x3f1fedffU,0x3f450761U,0x3ee515ceU,0x3f296798U}, std::int32_t{-1}, false},
    {"filter/unsharpMask:usmBlurH", "defaults", "4f07a9f646cb81e24baf26660ca378582a17d8c1518eb62e072b6fd7342ee8a0", "c458991c4a0563af25a7a92b763588b18bc873fa6e48be699e0c32e164a387c5",
     {0x3f084ca8U,0x3f2980a7U,0x3e0f4b36U,0x3f083e34U,0x3ec8b62fU,0x3ec55556U,0x3f1591f1U,0x3f270375U,0x3f2f8135U,0x3f662c9cU,0x3ede23c9U,0x3f19299eU}, std::int32_t{-1}, false},
    {"filter/unsharpMask:usmBlurV", "defaults", "5b748a0bf419a5dbecdb0971ee9c4044a2447af9bf5884d75e72df139775b0dc", "17b430222bf4782f5adbe55b253015a83358bef8899216c10d6df9ba5ede23dd",
     {0x3f038e1dU,0x3f26c351U,0x3ea83487U,0x3f07ec81U,0x3ef422bcU,0x3f02b2a0U,0x3ecdd7c8U,0x3f2bfdf3U,0x3f1e897bU,0x3f4174bcU,0x3ee006a2U,0x3f2de2edU}, std::int32_t{-1}, false},
    {"filter/craquelure:craquelure", "defaults", "51a1bc27355d0f8f973fd7ba742e798c85e8ad952a262a8353b137d828dee124", "7af2e319b78f42ef180cb59272c39b58a58db94a10d761c22f2de047e40bf84a",
     {0x3f170a3dU,0x3f500000U,0x3d3a2e8cU,0x3ee66666U,0x3e4ccccdU,0x3ec55555U,0x3e3a2e8cU,0x3f59999aU,0x3f51eb85U,0x3f780000U,0x3ea2e8baU,0x3f19999aU}, std::int32_t{-1}, false},
    {"filter/lowPoly:lowPoly", "defaults", "43c45e40b8f770940d9989296dd41368a007ecd8ee034d328ccf25c3f07c3e9e", "36a4a1b0fa710f1ed0e24270052867b6ecad5b7ca3e43380769b6cdec9f278c3",
     {0x3f01b0c3U,0x3f329964U,0x3d1fdd71U,0x3ee66666U,0x3e9c8b32U,0x3eeb01e8U,0x3f639867U,0x3f733333U,0x3db77fa5U,0x3e5461f5U,0x3f6a9617U,0x3f4ccccdU}, std::int32_t{-1}, false},
    {"filter/patchwork:patchwork", "defaults", "8283e14b801c4ba84b43bb894bbe76ac7dfe100f08d8e99b689a3ed2b5bf199b", "535bcf36616037e578dd181e2947159bfd5724dd221c51057b07af49372e19ba",
     {0x3f0e462cU,0x3f43eda7U,0x3d2f605eU,0x3ee66666U,0x3e581416U,0x3ed493c2U,0x3e758b31U,0x3f59999aU,0x3f33e715U,0x3f548995U,0x3e8b9d30U,0x3f19999aU}, std::int32_t{-1}, false},
    {"filter/scatter:scatterSmooth", "defaults", "51a1bc27355d0f8f973fd7ba742e798c85e8ad952a262a8353b137d828dee124", "7af2e319b78f42ef180cb59272c39b58a58db94a10d761c22f2de047e40bf84a",
     {0x3f170a3dU,0x3f500000U,0x3d3a2e8cU,0x3ee66666U,0x3e4ccccdU,0x3ec55555U,0x3e3a2e8cU,0x3f59999aU,0x3f51eb85U,0x3f780000U,0x3ea2e8baU,0x3f19999aU}, std::int32_t{-1}, false},
    {"filter/strokes:stkPost", "defaults", "9c5de62be0ea11267af98db82bce047b319e9b3586c31f1ab5858880cbf6c24b", "e43b0b43ccd24d27e217b04e88a13f2e0d194dc8e10d08d87a3cd7c678d3228c",
     {0x3f407729U,0x00000000U,0x00000000U,0x3ee66666U,0x3e8b9405U,0x3f1fffffU,0x3d87ab60U,0x3f59999aU,0x3f800000U,0x3e2d9365U,0x3ed7cd39U,0x3f19999aU}, std::int32_t{-1}, false},
    {"filter/clouds:clouds", "defaults", "941a69f8f961549ea3f3391a0212a96024a88abddf910012f705716ed90128f4", "bddba5d9807cf197eb6c14bc9b6475217f93a8a9b680676a3b41008ec2945d81",
     {0x3f170a3dU,0x3f500000U,0x3d3a2e8cU,0x3ee66666U,0x3eae147bU,0x3f02aaabU,0x3f7d1746U,0x3f733333U,0x3db851ecU,0x3e555555U,0x3f6ba2e9U,0x3f4ccccdU}, std::int32_t{-1}, false},
    {"filter/hatch:hatch", "defaults", "02e85cbb0464ed82e250ed79c6b05efeb0c56953acf81530cbe31bf77e08e331", "549d3a7401e3e03c135beacf64b894cc7ea83d279df5fcfdf54ad35f55b8152c",
     {0x3dcccccdU,0x3dcccccdU,0x3dcccccdU,0x3ee66666U,0x3dcccccdU,0x3dcccccdU,0x3dcccccdU,0x3f59999aU,0x3f75c28fU,0x3f70a3d7U,0x3f6147aeU,0x3f19999aU}, std::int32_t{-1}, false},
    {"filter/oilPaint:oilPost", "defaults", "5c2a418670625998c1e46b0f9d9585307c3c0ac58e33ac542311cfb3f196db98", "527648c717ed3085055c027c784ced4afcff3639fd937d13d94a2fcf58d752f0",
     {0x3f4a6526U,0x00000000U,0x00000000U,0x3ee66666U,0x3e51e43fU,0x3f20f5b1U,0x00000000U,0x3f59999aU,0x3f800000U,0x3e0bf3d4U,0x3ef6a127U,0x3f19999aU}, std::int32_t{-1}, false},
    {"synth/gradient:gradient", "defaults", "441cbbd95a4b7185328ccc465aa0e02e7ff6989788bc7c9f65c9376112e39208", "082236aa2c57fa8f6f761c99b291f46f3ea058e6e1e34dddf42fc112bc5806a4",
     {0x3f800000U,0x3f000001U,0x00000000U,0x3f800000U,0x3f800000U,0x3f800000U,0x00000000U,0x3f800000U,0x00000000U,0x3f346fecU,0x3e972028U,0x3f800000U}, std::int32_t{-1}, false},
    {"synth/mandala:mandala", "defaults", "61203cf6017f695337b436376ab005ea559b4d79290a63d1f67e2191830c574b", "aee70c04bdb39b7c718a3a3fa2d9c4cc9ba01c669df38516a7a95be64b7704b6",
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
    {"synth/cell:cell", "defaults", "1b5839437c4585a322978027decd3ac1af3cc0a1ad3ae11b790e18b6e63b7f6b", "54106eec3b30630ae72ad785a67938716556cc76d39d62d66655aea1732c1cb8",
     {0x3d2726a1U,0x3d2726a1U,0x3d2726a1U,0x3f800000U,0x3e79af64U,0x3e79af64U,0x3e79af64U,0x3f800000U,0x3f2d6c0fU,0x3f2d6c0fU,0x3f2d6c0fU,0x3f800000U}, std::int32_t{-1}, false},
    {"mixer/mashup:mashup", "defaults", "51a1bc27355d0f8f973fd7ba742e798c85e8ad952a262a8353b137d828dee124", "7af2e319b78f42ef180cb59272c39b58a58db94a10d761c22f2de047e40bf84a",
     {0x3f170a3dU,0x3f500000U,0x3d3a2e8cU,0x3ee66666U,0x3e4ccccdU,0x3ec55555U,0x3e3a2e8cU,0x3f59999aU,0x3f51eb85U,0x3f780000U,0x3ea2e8baU,0x3f19999aU}, std::int32_t{-1}, false},
    {"mixer/cellSplit:cellSplit", "defaults", "34413d4fe5576274eb3c31679ff89268574d99d91c4ee74ed7b687a8ce0ec9a2", "de3b3fd0f60e1fb86fda2413627de0074b65320c475255804e64e34e9d27ca50",
     {0x3f3851ecU,0x3d2aaaabU,0x3dd1745dU,0x3f000000U,0x3eae147bU,0x3f02aaabU,0x3f7d1746U,0x3f733333U,0x3db851ecU,0x3e555555U,0x3f6ba2e9U,0x3f59999aU}, std::int32_t{-1}, false},
    {"filter/pixelSort:findBrightest", "defaults", "c86ebfc4ba413a9f55f1e8710068c20001d7705c6c6ac24596a42058d66440e8", "0f3687723815d0d20951679825a22d160146cc12b9e17d47318ca202df70ed7f",
     {0x3f4ccccdU,0x3f70a3d7U,0x00000000U,0x3f800000U,0x3f333333U,0x3f59999aU,0x00000000U,0x3f800000U,0x3f333333U,0x3f6e147bU,0x00000000U,0x3f800000U}, std::int32_t{-1}, false},
    {"filter/reverb:reverb", "defaults", "392176332a679e14b60d180fffd6e719575ae51b8e9ba3614098b1e5f302b07f", "23e160d68e899ebb0ac6488ae42faf279057b138e504cc908bcf04e2217225a3",
     {0x3f008313U,0x3f288889U,0x3e7523afU,0x3f800000U,0x3e98ead7U,0x3eb9f4a0U,0x3f28253dU,0x3f800000U,0x3e1db22dU,0x3eeeeeefU,0x3f5e412aU,0x3f800000U}, std::int32_t{-1}, false},
    {"filter/reverb:reverb", "iterations_1", "6914316cb3a784f9d495c8ceec00fc192a707c91295ab728e56564106ec58859", "c8ac6db5a8d835ef048c04e14e965b047685a483f886eacecb76f16d534b693a",
     {0x3f0da741U,0x3f40e38fU,0x3e955555U,0x3f800000U,0x3e8a3d71U,0x3ed71c73U,0x3f2d9365U,0x3f800000U,0x3db17e4bU,0x3ecc71c7U,0x3f6f83e1U,0x3f800000U}, std::int32_t{1}, false},
    {"filter/reverb:reverb", "iterations_8", "74774415d7b661166635c063716a565599c245b2146cacddb6344d6e8fe04c3d", "f579ef2f1152e2f06570bf78854a998d7cef3219bca820341ed569ce18b21c2c",
     {0x3f483dbaU,0x3f0391c9U,0x3e46b4ceU,0x3f800000U,0x3f1a8ab7U,0x3f33399dU,0x3e27824cU,0x3f800000U,0x3e85e6caU,0x3ed8fc7dU,0x3e861a53U,0x3f800000U}, std::int32_t{8}, true},
}};

struct Task15OracleUniform {
  std::string_view key;
  std::string_view name;
  Task15BindingType type;
  std::array<double, 3> value;
};

constexpr std::array<Task15OracleUniform, 199> kTask15OracleUniforms{{
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
    {"filter/hatch:hatch", "MODE", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"filter/highPass:hpBlurH", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/highPass:hpBlurH", "radius", Task15BindingType::scalar, {10.0, 0.0, 0.0}},
    {"filter/highPass:hpBlurV", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/highPass:hpBlurV", "radius", Task15BindingType::scalar, {10.0, 0.0, 0.0}},
    {"filter/lowPoly:lowPoly", "LP_BORDER", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"filter/lowPoly:lowPoly", "LP_LIGHT", Task15BindingType::integer, {0.0, 0.0, 0.0}},
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
    {"filter/morphology:morphA", "SHAPE", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"filter/morphology:morphB", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/morphology:morphB", "mode", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"filter/morphology:morphB", "radius", Task15BindingType::scalar, {4.0, 0.0, 0.0}},
    {"filter/morphology:morphB", "SHAPE", Task15BindingType::integer, {0.0, 0.0, 0.0}},
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
    {"filter/oilPaint:oilPost", "MODE", Task15BindingType::integer, {1.0, 0.0, 0.0}},
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
    {"filter/relief:rlBlurH", "MODE", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"filter/relief:rlBlurV", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/relief:rlBlurV", "smoothness", Task15BindingType::scalar, {30.0, 0.0, 0.0}},
    {"filter/relief:rlBlurV", "MODE", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"filter/reverb:reverb", "tileOffset", Task15BindingType::vec2, {2.0, 1.0, 0.0}},
    {"filter/reverb:reverb", "fullResolution", Task15BindingType::vec2, {13.0, 11.0, 0.0}},
    {"filter/reverb:reverb", "iterations", Task15BindingType::integer, {3.0, 0.0, 0.0}},
    {"filter/reverb:reverb", "ridges", Task15BindingType::boolean, {0.0, 0.0, 0.0}},
    {"filter/reverb:reverb", "alpha", Task15BindingType::scalar, {1.0, 0.0, 0.0}},
    {"filter/reverb:reverb", "wrap", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"filter/scatter:scatterSmooth", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/scatter:scatterSmooth", "smoothness", Task15BindingType::scalar, {0.0, 0.0, 0.0}},
    {"filter/scatter:scatterSmooth", "MODE", Task15BindingType::integer, {0.0, 0.0, 0.0}},
    {"filter/stamp:stBlurH", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/stamp:stBlurH", "smoothness", Task15BindingType::scalar, {30.0, 0.0, 0.0}},
    {"filter/stamp:stBlurV", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/stamp:stBlurV", "smoothness", Task15BindingType::scalar, {30.0, 0.0, 0.0}},
    {"filter/strokes:stkPost", "resolution", Task15BindingType::vec2, {9.0, 7.0, 0.0}},
    {"filter/strokes:stkPost", "sharpness", Task15BindingType::scalar, {30.0, 0.0, 0.0}},
    {"filter/strokes:stkPost", "MODE", Task15BindingType::integer, {0.0, 0.0, 0.0}},
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
    {"synth/mandala:mandala", "aspect", Task15BindingType::scalar, {1.1818181276321411, 0.0, 0.0}},
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
          static_cast<double>(static_cast<float>(13.0 / 11.0)));
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
        // Every vec3-tagged kTask15OracleUniforms entry (hatch's
        // inkColor/paperColor, lowPoly's edgeColor, mixer/shadow's color,
        // gradient's color1..4, mandala's fgColor/bgColor) is an ordinary
        // effect-parameter vec3 uniform, now a double-precision carrier.
        bindings.set_uniform(name, noisemaker::glsl::DVec3(
            static_cast<double>(uniform.value[0]),
            static_cast<double>(uniform.value[1]),
            static_cast<double>(uniform.value[2]))); break;
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
  const noisemaker::BoundKernel kernel = fixture.key == "filter/reverb:reverb"
      ? noisemaker::historical_generated::bind_filter_reverb_reverb(bindings)
      : noisemaker::generated::bind(fixture.key, bindings);
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

namespace {

// filter/pixelSort:computeRank writes `float(x) / float(width - 1)` into the
// blue lane; at width 1 that is 0.0/0.0 -- a NaN MANUFACTURED BY HARDWARE.
// Its sign is an ISA property: AArch64 `fdiv` yields the positive default NaN
// 0x7fc00000, x86-64 SSE2 `divsd` yields the "QNaN indefinite" 0xffc00000.
// V8 does NOT canonicalize NaN, so the JS authority inherits the same split --
// measured on both architectures with the same node v24.7.0 / V8
// 13.6.233.10-node.26. Parity is therefore per-architecture here, and each
// constant below is a SAME-ARCHITECTURE JS authority capture, recorded with
// its provenance in docs/port-engineering/task-16-oracles.json (schema v2,
// `arch_captures` + `arch_divergence`). Root cause and the full dual-arch
// measurement:
// docs/port-engineering/x86-64-divergences/x86-64-divergences-report.md.
//
// The rgba8 hash below is deliberately NOT arch-keyed: to_rgba8() maps any NaN
// to 0 regardless of sign, so one value is correct on every architecture.
//
// The test below is named for what it actually asserts: the blue lane matches
// the SAME-ARCHITECTURE authority's NaN, which is the positive quiet NaN on
// arm64 and the negative one on x86-64. It deliberately does not claim a
// canonical quiet NaN is preserved -- that is true on arm64 only, and a green
// test whose name states a false invariant gets cited later as evidence the
// invariant holds.
#if defined(__aarch64__)
// arm64 authority capture.
constexpr std::string_view kTask16WidthOneFloatHash =
    "24f56616adaf6242697f97e5d9420c4bafa1529c99e8e053b9dc0cb6bc87341c";
constexpr std::uint32_t kTask16WidthOneBlueBits = 0x7fc00000U;
#elif defined(__x86_64__)
// x86_64 authority capture.
constexpr std::string_view kTask16WidthOneFloatHash =
    "79d1c1af5c1c16157179b44c4a5c04320924e03c6748cbb0eeb40ae4cb8a5582";
constexpr std::uint32_t kTask16WidthOneBlueBits = 0xffc00000U;
#else
#error "typed_task16 width-one: no JS-authority capture is recorded for this architecture. This fixture pins the bytes of a hardware-manufactured NaN whose sign is ISA-specific, so neither recorded capture may be inherited. Capture the authority on this architecture, add it to docs/port-engineering/task-16-oracles.json via the generator, then extend this switch."
#endif

}  // namespace

TEST(typed_task16_compute_rank_width_one_matches_same_arch_authority_nan) {
  const noisemaker::Surface input = task16_flat_surface(1U, 1U);
  const noisemaker::Surface first = render_task16(input, 1U, 1U);
  const noisemaker::Surface second = render_task16(input, 1U, 1U);
  REQUIRE(hex(sha256(little_endian_float_bytes(first))) == kTask16WidthOneFloatHash);
  REQUIRE(hex(sha256(first.to_rgba8())) ==
          "1f71b62d981be40a6adc0ccd7ef62b6bc47317c7a1de96d4b934f761b67b135e");
  REQUIRE(noisemaker::float_bits_to_uint(first.data()[0]) == 0x00000000U);
  REQUIRE(noisemaker::float_bits_to_uint(first.data()[1]) == 0x3f000000U);
  REQUIRE(std::isnan(first.data()[2]));
  REQUIRE(noisemaker::float_bits_to_uint(first.data()[2]) == kTask16WidthOneBlueBits);
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
       "891443c519cf988ba5eea5acdb4e84759160ac1a992f9f8fcac2824e331e8483",
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
       "6c54f6fc55aecddb68b4c6d90ab5e6e871d2358bf28d319c5e5023fd2fcf7593",
       "966ca81461240fb6c35316537f631f3b74b6d0a33a7b538d05ddd12e241347e9",
       {0x3f074202U,0x3f074202U,0x3f074202U,0x3f800000U,
        0x3d038551U,0x3d038551U,0x3d038551U,0x3f800000U,
        0x00000000U,0x00000000U,0x00000000U,0x3f800000U}},
      {"cel-threshold-0.6f", "filter/celShading:celShadingEdges",
       noisemaker::uint_bits_to_float(0x3f19999aU),
       "bec7dfa0806d4cf153699f79427479ac1ade2bf10d1b4ab688be49d9eedae6b6",
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
  // Captured before 8ae8e2a's vector equality; exact against the kernel it recorded.
  return noisemaker::run_pass(
      noisemaker::historical_generated::bind_classicNoisedeck_refract_refract(bindings),
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

// Current-authority captures (noisemaker-for-cpu 9f3bd6a) for every program the
// 8ae8e2a / 5976b7a6 sync changed, through the public factory route. Inputs are
// asymmetric with white and all-zero pixels and a nonzero tile offset, so both
// vector-equality arms, Coalesce's refracted UVs and the tiled displacement
// paths are observable. tests/fixtures/authority_8ae8e2a holds the cases, the
// authenticated reference and its capture; the table below is materialized
// from them and checked by tests/test_authority_8ae8e2a_captures.py.
struct Authority8ae8e2aCase {
  std::string_view name;
  std::string_view key;
  std::uint32_t width;
  std::uint32_t height;
  std::uint32_t time_bits;
  std::int32_t seed;
  std::uint32_t frame;
  std::array<float, 2> tile_offset;
  std::array<float, 2> full_resolution;
  std::string_view float_hash;
  std::string_view rgba_hash;
};

struct Authority8ae8e2aUniform {
  std::uint32_t case_index;
  std::string_view name;
  char kind;
  std::array<std::uint32_t, 3> words;
};

struct Authority8ae8e2aTexture {
  std::uint32_t case_index;
  std::string_view name;
  std::uint32_t width;
  std::uint32_t height;
  std::uint32_t tag;
};

// AUTHORITY_8AE8E2A_CASES_BEGIN
constexpr std::array<Authority8ae8e2aCase, 30> kAuthority8ae8e2aCases{{
    {"coalesce-blend0", "classicNoisedeck/coalesce:coalesce", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "d9b5b1d81aa71c1b56c9825d1db8b07d2643b1ae6f644b85a9390752437bb6fe",
     "a3b8ac14238de0bf7e2a169b35465d651b2c5f70423dada86445e415e28842fe"},
    {"coalesce-blend2", "classicNoisedeck/coalesce:coalesce", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "0c85d41c33124e5fe5346891c07abb9fea731dc76dc2919d37a96934ceddcbfd",
     "8898594256e31e6c4027d9d63ce9f9b809b621af59c3d4e878df5483253f1a20"},
    {"coalesce-blend3", "classicNoisedeck/coalesce:coalesce", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "3c649e079a0b817cc07bc6e24492916728bafa65195d0f9cb2f321e0c2063080",
     "92fcd6a64f45741a176a9ced679e76101516a4632032028923f9b11be1b556d8"},
    {"coalesce-blend7", "classicNoisedeck/coalesce:coalesce", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "237ba190f774af4d62f5b8a4b302b289ef8eca11eb4fa6ccc5fc9605600aaa81",
     "87f2a9cc6a987cbff81c132fcfc8029cc71ba96a89848af17ab992eb56450304"},
    {"coalesce-blend10", "classicNoisedeck/coalesce:coalesce", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "f9fc2c7670140b2dd00b081772294ac4c819db7ad1f6fc9ae43ef9252441264c",
     "698ddc19057270dee9fa4b1fd6421b12220e9c8f383c7dd85e353933a705b24a"},
    {"coalesce-blend15", "classicNoisedeck/coalesce:coalesce", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "20ac235bd05d31f2e62e95ff141922333a4768851e84fbe81923026f9914f83b",
     "0baef5483e76c78c48c478d8f6f00405e6b4c6ec357f5d5aa7c220b97add7b43"},
    {"coalesce-blend100", "classicNoisedeck/coalesce:coalesce", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "b166e84e2a02e7fd8a28a87af73849d84454d40276c17b5e05f139d12a83db8f",
     "706393002296569ce58963ee1fa4a1244577b7e67a8c88da828f0e6c95742570"},
    {"coalesce-blend1000", "classicNoisedeck/coalesce:coalesce", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "1e66624c95d7a591017d7d4e0202f418705acbbc66231e01fb81c04762db3a5a",
     "57947ee9ce45411c2dd07819991bef25f3d656dbac21924a64cbedfbe7cc4007"},
    {"refract-mode1-blend2-wrap1", "classicNoisedeck/refract:refract", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "5a50f1f7e976f0c87b16a12d5a774c5eaaef4077be440e757c2276f4173b9277",
     "d8620c2d9651841b2d70e4a3f7bdc60f0d3bfc3e14b3967f6ecd995476086d8d"},
    {"refract-mode1-blend3-wrap0", "classicNoisedeck/refract:refract", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "11cc74e118a1dcca9b572939cb6c422ccc36ee2cd945baa36f52fcd0df90da65",
     "ade3d6e2e08dfa18cfdc8f1aa16bc51b9a695c253b7eb1cd127139b771a3a105"},
    {"refract-mode1-blend7-wrap2", "classicNoisedeck/refract:refract", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "f4165825a71571a71bd9c8913e6492a51799943a24a39c772f58a603c5b79bb3",
     "391770cdeac75964fd31b1f5bb6a99d15ffbcdf1fa01f33196fc1dc6b7e1d200"},
    {"refract-mode1-blend15-wrap1", "classicNoisedeck/refract:refract", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "f2022577c26addd7c03412e9f051fadb4743f16ca328681dc67c4bb19fdd7fe0",
     "0b62be9b3d853aaf8f6b6164fd7b07506290d583c5da2f27c5f77548d13af57d"},
    {"refract-mode0-blend2-wrap0", "classicNoisedeck/refract:refract", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "1da6a6203ea39f93f949a3beb00be23b6f1105a696b030702b381d355b62cff1",
     "7741630872c8743504f7eab26bd04ddd05ad0ed25a97d97fb5123e23637c2d83"},
    {"refract-mode1-blend13-wrap1", "classicNoisedeck/refract:refract", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "a80c8a5eaac05b4557d3c0bd43d9ead32016a0ddc5958a490a039f33964917f3",
     "38592158917942fba4deadb3b3150355381c10e333c7c505e756f628b20d2ae8"},
    {"lens-shape0-mode0", "classicNoisedeck/lensDistortion:lensDistortion", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "a0b361e445f822501e81cb7ba5aa95a77daaf9aab7b962fdc57347784973095f",
     "23b451a050e768616d0e28e2ba676e0513d620631ba7b76d3e44bb4083ed9b48"},
    {"lens-shape2-mode1", "classicNoisedeck/lensDistortion:lensDistortion", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "fa7687a41e93cef29e0760b958087dc31a1cca9bda916edca0cadc95189c95d0",
     "bcd11f67667e1a31e73229e777f705f75ad86c0811c5a786b9c0111fc682a3cf"},
    {"lens-shape10-mode0", "classicNoisedeck/lensDistortion:lensDistortion", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "7cc2f55256a4debca5d3cdc0660f36cfb20bb83dc41e9e5ea6f2ac5c9004ef48",
     "5da27eeaf93b663c4684be150cc5b000e216ef0d11cea78a2d6ece8a1cdd5282"},
    {"colorLab-dither4-invert1-mode2", "classicNoisedeck/colorLab:colorLab", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "1b364631c57e5af6733aa20654f6e21037152eba5543b4bcfcde5cca7c0b0488",
     "e2a031b1a43a177bfbb65df5f73e5c837151de09777a5cd03b661aaac174a778"},
    {"colorLab-dither1-invert0-mode1", "classicNoisedeck/colorLab:colorLab", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "88e0c0220d2c5292b580395ca62b8e5963ea1667548f10b8dacce605a7b50074",
     "f10ea936b3261204af8ccbe98d1cd3e2fef0a33912a0041cd05e41a12dd2f0fe"},
    {"colorLab-dither3-invert1-mode3", "classicNoisedeck/colorLab:colorLab", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "c7931e6e951b171ebda0e3f14ee308a711614c4b1b1461176b081a40577e7426",
     "9c702004e0084318d48ca7e401e550114409ba39885f330dc4022f3eb115ddf2"},
    {"colorLab-dither2-invert0-mode4", "classicNoisedeck/colorLab:colorLab", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "9615a989326ebb2302efbf83726f047235749255e9c89f863e62aac070ae2720",
     "d7192bbfe66af0159e7cd2148093f095085b01b41780fbd1ffc79368b1a5b3ac"},
    {"cellSplit-mode0-invert0", "mixer/cellSplit:cellSplit", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "1cf209f1f3c309b99a860c064eb2653b9f246e0331300a47be9ee8b7c4e8458c",
     "eb0557f29460996956210a848c4322322ddc44c032b2a08760e73f2fd24c37ae"},
    {"cellSplit-mode1-invert1", "mixer/cellSplit:cellSplit", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "3c2f19b1d65663b92cbc1060c379ae32a3617f746c4af2116a9ee3d978ba766d",
     "189bd2706bfe6ab5b54b19589b9d8e6a7be813037772b759d0fa3fc3289e5f3a"},
    {"degauss-tiled", "filter/degauss:degauss", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "5bb8bef6dd6fc370542b5a0d94e89bcf59f4dd85a9b948fe08d41068b8e0e972",
     "011446692211d31ba8baf5c4a726825b837fa654b992a6cf6cc0d25b760f470f"},
    {"degauss-untiled", "filter/degauss:degauss", 9U, 7U, 0x3ec00000U, 7, 7U, {0.0f, 0.0f}, {9.0f, 7.0f},
     "c8a7d8485a7dfff01aff6c9f5e44905b103ddb961292a4ddb5d206bd15998d60",
     "5bc53cadc7c33d428bb697cb8bd656ad0e97ded10fa9ae8f26e52c31725c1a7c"},
    {"effects-tiled", "classicNoisedeck/effects:effects", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "aa9489e9658ff4bf9906af1d91fb62a1c1060c91159c59c84aa5bf4e78836fda",
     "4aaba60cb7df678d8dfe4037100332ab2f2f574eb8c6d2dfcf9b7b5e6698e933"},
    {"effects-untiled", "classicNoisedeck/effects:effects", 9U, 7U, 0x3ec00000U, 7, 7U, {0.0f, 0.0f}, {9.0f, 7.0f},
     "cfe27ffaf3e4e1f23b66dd5c28a46d77f7782a025d6f7e7458b1de9b5eae40f7",
     "b50091de1f1cdc395bb8c7a0b9ca5bef80942f6463e05070dc1bc4b3bdeabe77"},
    {"scale-wrap0", "filter/scale:scale", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "d69ca61cabf7f8b93e266f286b358e3d969b8401e2eabe55ea4fe546deb98118",
     "3fef42f9da3a39a380f5c180a45677c03be66e760417675810d78d61444f2107"},
    {"scale-wrap1", "filter/scale:scale", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "c3fb28bf7b6606b3bbe4f82348391102f0c25ec393c0f4febaedee4de9a21692",
     "8ba3641c1620e66eba2bca6ba9642fcd932d88a0422440dfa538aefb4cef337a"},
    {"scale-wrap2", "filter/scale:scale", 9U, 7U, 0x3ec00000U, 7, 7U, {-5.0f, 3.0f}, {17.0f, 13.0f},
     "abefbab45323e8db85ebcd0bed1f1362318a0485009f55cca8b9e27677bdceb2",
     "dc6a17c9570845b5667fe6faa1361f05e471f5ab033213aec9b26acc0aab8849"},
}};
constexpr std::array<Authority8ae8e2aUniform, 249> kAuthority8ae8e2aUniforms{{
    {0U, "blendMode", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {0U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {0U, "refractAAmt", 'f', {0x422c0000U, 0x00000000U, 0x00000000U}},
    {0U, "refractBAmt", 'f', {0x42740000U, 0x00000000U, 0x00000000U}},
    {0U, "refractADir", 'f', {0xc3090000U, 0x00000000U, 0x00000000U}},
    {0U, "refractBDir", 'f', {0x43530000U, 0x00000000U, 0x00000000U}},
    {1U, "blendMode", 'i', {0x00000002U, 0x00000000U, 0x00000000U}},
    {1U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {1U, "refractAAmt", 'f', {0x422c0000U, 0x00000000U, 0x00000000U}},
    {1U, "refractBAmt", 'f', {0x42740000U, 0x00000000U, 0x00000000U}},
    {1U, "refractADir", 'f', {0xc3090000U, 0x00000000U, 0x00000000U}},
    {1U, "refractBDir", 'f', {0x43530000U, 0x00000000U, 0x00000000U}},
    {2U, "blendMode", 'i', {0x00000003U, 0x00000000U, 0x00000000U}},
    {2U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {2U, "refractAAmt", 'f', {0x422c0000U, 0x00000000U, 0x00000000U}},
    {2U, "refractBAmt", 'f', {0x42740000U, 0x00000000U, 0x00000000U}},
    {2U, "refractADir", 'f', {0xc3090000U, 0x00000000U, 0x00000000U}},
    {2U, "refractBDir", 'f', {0x43530000U, 0x00000000U, 0x00000000U}},
    {3U, "blendMode", 'i', {0x00000007U, 0x00000000U, 0x00000000U}},
    {3U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {3U, "refractAAmt", 'f', {0x422c0000U, 0x00000000U, 0x00000000U}},
    {3U, "refractBAmt", 'f', {0x42740000U, 0x00000000U, 0x00000000U}},
    {3U, "refractADir", 'f', {0xc3090000U, 0x00000000U, 0x00000000U}},
    {3U, "refractBDir", 'f', {0x43530000U, 0x00000000U, 0x00000000U}},
    {4U, "blendMode", 'i', {0x0000000aU, 0x00000000U, 0x00000000U}},
    {4U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {4U, "refractAAmt", 'f', {0x422c0000U, 0x00000000U, 0x00000000U}},
    {4U, "refractBAmt", 'f', {0x42740000U, 0x00000000U, 0x00000000U}},
    {4U, "refractADir", 'f', {0xc3090000U, 0x00000000U, 0x00000000U}},
    {4U, "refractBDir", 'f', {0x43530000U, 0x00000000U, 0x00000000U}},
    {5U, "blendMode", 'i', {0x0000000fU, 0x00000000U, 0x00000000U}},
    {5U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {5U, "refractAAmt", 'f', {0x422c0000U, 0x00000000U, 0x00000000U}},
    {5U, "refractBAmt", 'f', {0x42740000U, 0x00000000U, 0x00000000U}},
    {5U, "refractADir", 'f', {0xc3090000U, 0x00000000U, 0x00000000U}},
    {5U, "refractBDir", 'f', {0x43530000U, 0x00000000U, 0x00000000U}},
    {6U, "blendMode", 'i', {0x00000064U, 0x00000000U, 0x00000000U}},
    {6U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {6U, "refractAAmt", 'f', {0x422c0000U, 0x00000000U, 0x00000000U}},
    {6U, "refractBAmt", 'f', {0x42740000U, 0x00000000U, 0x00000000U}},
    {6U, "refractADir", 'f', {0xc3090000U, 0x00000000U, 0x00000000U}},
    {6U, "refractBDir", 'f', {0x43530000U, 0x00000000U, 0x00000000U}},
    {7U, "blendMode", 'i', {0x000003e8U, 0x00000000U, 0x00000000U}},
    {7U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {7U, "refractAAmt", 'f', {0x422c0000U, 0x00000000U, 0x00000000U}},
    {7U, "refractBAmt", 'f', {0x42740000U, 0x00000000U, 0x00000000U}},
    {7U, "refractADir", 'f', {0xc3090000U, 0x00000000U, 0x00000000U}},
    {7U, "refractBDir", 'f', {0x43530000U, 0x00000000U, 0x00000000U}},
    {8U, "mode", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {8U, "amount", 'f', {0x41ef3333U, 0x00000000U, 0x00000000U}},
    {8U, "direction", 'f', {0x4309999aU, 0x00000000U, 0x00000000U}},
    {8U, "blendMode", 'i', {0x00000002U, 0x00000000U, 0x00000000U}},
    {8U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {8U, "wrap", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {9U, "mode", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {9U, "amount", 'f', {0x41ef3333U, 0x00000000U, 0x00000000U}},
    {9U, "direction", 'f', {0x4309999aU, 0x00000000U, 0x00000000U}},
    {9U, "blendMode", 'i', {0x00000003U, 0x00000000U, 0x00000000U}},
    {9U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {9U, "wrap", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {10U, "mode", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {10U, "amount", 'f', {0x41ef3333U, 0x00000000U, 0x00000000U}},
    {10U, "direction", 'f', {0x4309999aU, 0x00000000U, 0x00000000U}},
    {10U, "blendMode", 'i', {0x00000007U, 0x00000000U, 0x00000000U}},
    {10U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {10U, "wrap", 'i', {0x00000002U, 0x00000000U, 0x00000000U}},
    {11U, "mode", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {11U, "amount", 'f', {0x41ef3333U, 0x00000000U, 0x00000000U}},
    {11U, "direction", 'f', {0x4309999aU, 0x00000000U, 0x00000000U}},
    {11U, "blendMode", 'i', {0x0000000fU, 0x00000000U, 0x00000000U}},
    {11U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {11U, "wrap", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {12U, "mode", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {12U, "amount", 'f', {0x41ef3333U, 0x00000000U, 0x00000000U}},
    {12U, "direction", 'f', {0x4309999aU, 0x00000000U, 0x00000000U}},
    {12U, "blendMode", 'i', {0x00000002U, 0x00000000U, 0x00000000U}},
    {12U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {12U, "wrap", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {13U, "mode", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {13U, "amount", 'f', {0x41ef3333U, 0x00000000U, 0x00000000U}},
    {13U, "direction", 'f', {0x4309999aU, 0x00000000U, 0x00000000U}},
    {13U, "blendMode", 'i', {0x0000000dU, 0x00000000U, 0x00000000U}},
    {13U, "mixAmt", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {13U, "wrap", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {14U, "aspectLens", 'b', {0x00000000U, 0x00000000U, 0x00000000U}},
    {14U, "shape", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {14U, "tint", '3', {0x3f800000U, 0x3f800000U, 0x3f800000U}},
    {14U, "alpha", 'f', {0x42740000U, 0x00000000U, 0x00000000U}},
    {14U, "vignetteAmt", 'f', {0x41b80000U, 0x00000000U, 0x00000000U}},
    {14U, "distortion", 'f', {0x42140000U, 0x00000000U, 0x00000000U}},
    {14U, "speed", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {14U, "loopScale", 'f', {0x42c80000U, 0x00000000U, 0x00000000U}},
    {14U, "aberration", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {14U, "hueRotation", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {14U, "hueRange", 'f', {0x42200000U, 0x00000000U, 0x00000000U}},
    {14U, "mode", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {14U, "modulate", 'b', {0x00000000U, 0x00000000U, 0x00000000U}},
    {14U, "blendMode", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {14U, "saturation", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {14U, "passthru", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {15U, "aspectLens", 'b', {0x00000000U, 0x00000000U, 0x00000000U}},
    {15U, "shape", 'i', {0x00000002U, 0x00000000U, 0x00000000U}},
    {15U, "tint", '3', {0x3e800000U, 0x3f000000U, 0x3f400000U}},
    {15U, "alpha", 'f', {0x42740000U, 0x00000000U, 0x00000000U}},
    {15U, "vignetteAmt", 'f', {0x41b80000U, 0x00000000U, 0x00000000U}},
    {15U, "distortion", 'f', {0x42140000U, 0x00000000U, 0x00000000U}},
    {15U, "speed", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {15U, "loopScale", 'f', {0x42c80000U, 0x00000000U, 0x00000000U}},
    {15U, "aberration", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {15U, "hueRotation", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {15U, "hueRange", 'f', {0x42200000U, 0x00000000U, 0x00000000U}},
    {15U, "mode", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {15U, "modulate", 'b', {0x00000000U, 0x00000000U, 0x00000000U}},
    {15U, "blendMode", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {15U, "saturation", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {15U, "passthru", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {16U, "aspectLens", 'b', {0x00000000U, 0x00000000U, 0x00000000U}},
    {16U, "shape", 'i', {0x0000000aU, 0x00000000U, 0x00000000U}},
    {16U, "tint", '3', {0x3f800000U, 0x00000000U, 0x3f800000U}},
    {16U, "alpha", 'f', {0x42740000U, 0x00000000U, 0x00000000U}},
    {16U, "vignetteAmt", 'f', {0x41b80000U, 0x00000000U, 0x00000000U}},
    {16U, "distortion", 'f', {0x42140000U, 0x00000000U, 0x00000000U}},
    {16U, "speed", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {16U, "loopScale", 'f', {0x42c80000U, 0x00000000U, 0x00000000U}},
    {16U, "aberration", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {16U, "hueRotation", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {16U, "hueRange", 'f', {0x42200000U, 0x00000000U, 0x00000000U}},
    {16U, "mode", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {16U, "modulate", 'b', {0x00000000U, 0x00000000U, 0x00000000U}},
    {16U, "blendMode", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {16U, "saturation", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {16U, "passthru", 'f', {0x42480000U, 0x00000000U, 0x00000000U}},
    {17U, "levels", 'f', {0x40800000U, 0x00000000U, 0x00000000U}},
    {17U, "dither", 'i', {0x00000004U, 0x00000000U, 0x00000000U}},
    {17U, "hueRotation", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {17U, "hueRange", 'f', {0x42c80000U, 0x00000000U, 0x00000000U}},
    {17U, "invert", 'b', {0x00000001U, 0x00000000U, 0x00000000U}},
    {17U, "brightness", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {17U, "contrast", 'f', {0x427c0000U, 0x00000000U, 0x00000000U}},
    {17U, "saturation", 'f', {0x41880000U, 0x00000000U, 0x00000000U}},
    {17U, "colorMode", 'i', {0x00000002U, 0x00000000U, 0x00000000U}},
    {17U, "paletteMode", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {17U, "paletteOffset", '3', {0x3f547ae1U, 0x3f19999aU, 0x3f2147aeU}},
    {17U, "paletteAmp", '3', {0x3f000000U, 0x3f000000U, 0x3f000000U}},
    {17U, "paletteFreq", '3', {0x3f800000U, 0x3f800000U, 0x3f800000U}},
    {17U, "palettePhase", '3', {0x3e99999aU, 0x3dcccccdU, 0x00000000U}},
    {17U, "cyclePalette", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {17U, "rotatePalette", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {17U, "repeatPalette", 'f', {0x3f800000U, 0x00000000U, 0x00000000U}},
    {18U, "levels", 'f', {0x40800000U, 0x00000000U, 0x00000000U}},
    {18U, "dither", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {18U, "hueRotation", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {18U, "hueRange", 'f', {0x42c80000U, 0x00000000U, 0x00000000U}},
    {18U, "invert", 'b', {0x00000000U, 0x00000000U, 0x00000000U}},
    {18U, "brightness", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {18U, "contrast", 'f', {0x427c0000U, 0x00000000U, 0x00000000U}},
    {18U, "saturation", 'f', {0x41880000U, 0x00000000U, 0x00000000U}},
    {18U, "colorMode", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {18U, "paletteMode", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {18U, "paletteOffset", '3', {0x3f547ae1U, 0x3f19999aU, 0x3f2147aeU}},
    {18U, "paletteAmp", '3', {0x3f000000U, 0x3f000000U, 0x3f000000U}},
    {18U, "paletteFreq", '3', {0x3f800000U, 0x3f800000U, 0x3f800000U}},
    {18U, "palettePhase", '3', {0x3e99999aU, 0x3dcccccdU, 0x00000000U}},
    {18U, "cyclePalette", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {18U, "rotatePalette", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {18U, "repeatPalette", 'f', {0x3f800000U, 0x00000000U, 0x00000000U}},
    {19U, "levels", 'f', {0x40800000U, 0x00000000U, 0x00000000U}},
    {19U, "dither", 'i', {0x00000003U, 0x00000000U, 0x00000000U}},
    {19U, "hueRotation", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {19U, "hueRange", 'f', {0x42c80000U, 0x00000000U, 0x00000000U}},
    {19U, "invert", 'b', {0x00000001U, 0x00000000U, 0x00000000U}},
    {19U, "brightness", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {19U, "contrast", 'f', {0x427c0000U, 0x00000000U, 0x00000000U}},
    {19U, "saturation", 'f', {0x41880000U, 0x00000000U, 0x00000000U}},
    {19U, "colorMode", 'i', {0x00000003U, 0x00000000U, 0x00000000U}},
    {19U, "paletteMode", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {19U, "paletteOffset", '3', {0x3f547ae1U, 0x3f19999aU, 0x3f2147aeU}},
    {19U, "paletteAmp", '3', {0x3f000000U, 0x3f000000U, 0x3f000000U}},
    {19U, "paletteFreq", '3', {0x3f800000U, 0x3f800000U, 0x3f800000U}},
    {19U, "palettePhase", '3', {0x3e99999aU, 0x3dcccccdU, 0x00000000U}},
    {19U, "cyclePalette", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {19U, "rotatePalette", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {19U, "repeatPalette", 'f', {0x3f800000U, 0x00000000U, 0x00000000U}},
    {20U, "levels", 'f', {0x40800000U, 0x00000000U, 0x00000000U}},
    {20U, "dither", 'i', {0x00000002U, 0x00000000U, 0x00000000U}},
    {20U, "hueRotation", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {20U, "hueRange", 'f', {0x42c80000U, 0x00000000U, 0x00000000U}},
    {20U, "invert", 'b', {0x00000000U, 0x00000000U, 0x00000000U}},
    {20U, "brightness", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {20U, "contrast", 'f', {0x427c0000U, 0x00000000U, 0x00000000U}},
    {20U, "saturation", 'f', {0x41880000U, 0x00000000U, 0x00000000U}},
    {20U, "colorMode", 'i', {0x00000004U, 0x00000000U, 0x00000000U}},
    {20U, "paletteMode", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {20U, "paletteOffset", '3', {0x3f547ae1U, 0x3f19999aU, 0x3f2147aeU}},
    {20U, "paletteAmp", '3', {0x3f000000U, 0x3f000000U, 0x3f000000U}},
    {20U, "paletteFreq", '3', {0x3f800000U, 0x3f800000U, 0x3f800000U}},
    {20U, "palettePhase", '3', {0x3e99999aU, 0x3dcccccdU, 0x00000000U}},
    {20U, "cyclePalette", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {20U, "rotatePalette", 'f', {0x00000000U, 0x00000000U, 0x00000000U}},
    {20U, "repeatPalette", 'f', {0x3f800000U, 0x00000000U, 0x00000000U}},
    {21U, "mode", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {21U, "scale", 'f', {0x40400000U, 0x00000000U, 0x00000000U}},
    {21U, "edgeWidth", 'f', {0x3e4ccccdU, 0x00000000U, 0x00000000U}},
    {21U, "seed", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {21U, "invert", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {21U, "speed", 'f', {0x3f800000U, 0x00000000U, 0x00000000U}},
    {22U, "mode", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {22U, "scale", 'f', {0x40400000U, 0x00000000U, 0x00000000U}},
    {22U, "edgeWidth", 'f', {0x3e4ccccdU, 0x00000000U, 0x00000000U}},
    {22U, "seed", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {22U, "invert", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {22U, "speed", 'f', {0x3f800000U, 0x00000000U, 0x00000000U}},
    {23U, "displacement", 'f', {0x3e4ccccdU, 0x00000000U, 0x00000000U}},
    {23U, "speed", 'f', {0x3fc00000U, 0x00000000U, 0x00000000U}},
    {23U, "seed", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {23U, "direction", 'f', {0x42040000U, 0x00000000U, 0x00000000U}},
    {24U, "displacement", 'f', {0x3e4ccccdU, 0x00000000U, 0x00000000U}},
    {24U, "speed", 'f', {0x3fc00000U, 0x00000000U, 0x00000000U}},
    {24U, "seed", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {24U, "direction", 'f', {0x42040000U, 0x00000000U, 0x00000000U}},
    {25U, "effectAmt", 'f', {0x428c0000U, 0x00000000U, 0x00000000U}},
    {25U, "scaleAmt", 'f', {0x42f00000U, 0x00000000U, 0x00000000U}},
    {25U, "rotation", 'f', {0x41c80000U, 0x00000000U, 0x00000000U}},
    {25U, "offsetX", 'f', {0x3e99999aU, 0x00000000U, 0x00000000U}},
    {25U, "offsetY", 'f', {0xbe4ccccdU, 0x00000000U, 0x00000000U}},
    {25U, "intensity", 'f', {0x42700000U, 0x00000000U, 0x00000000U}},
    {25U, "saturation", 'f', {0x41f00000U, 0x00000000U, 0x00000000U}},
    {26U, "effectAmt", 'f', {0x428c0000U, 0x00000000U, 0x00000000U}},
    {26U, "scaleAmt", 'f', {0x42f00000U, 0x00000000U, 0x00000000U}},
    {26U, "rotation", 'f', {0x41c80000U, 0x00000000U, 0x00000000U}},
    {26U, "offsetX", 'f', {0x3e99999aU, 0x00000000U, 0x00000000U}},
    {26U, "offsetY", 'f', {0xbe4ccccdU, 0x00000000U, 0x00000000U}},
    {26U, "intensity", 'f', {0x42700000U, 0x00000000U, 0x00000000U}},
    {26U, "saturation", 'f', {0x41f00000U, 0x00000000U, 0x00000000U}},
    {27U, "scaleX", 'f', {0xbfd9999aU, 0x00000000U, 0x00000000U}},
    {27U, "scaleY", 'f', {0x40133333U, 0x00000000U, 0x00000000U}},
    {27U, "centerX", 'f', {0x3f3ae148U, 0x00000000U, 0x00000000U}},
    {27U, "centerY", 'f', {0xbf1c28f6U, 0x00000000U, 0x00000000U}},
    {27U, "wrap", 'i', {0x00000000U, 0x00000000U, 0x00000000U}},
    {28U, "scaleX", 'f', {0xbfd9999aU, 0x00000000U, 0x00000000U}},
    {28U, "scaleY", 'f', {0x40133333U, 0x00000000U, 0x00000000U}},
    {28U, "centerX", 'f', {0x3f3ae148U, 0x00000000U, 0x00000000U}},
    {28U, "centerY", 'f', {0xbf1c28f6U, 0x00000000U, 0x00000000U}},
    {28U, "wrap", 'i', {0x00000001U, 0x00000000U, 0x00000000U}},
    {29U, "scaleX", 'f', {0xbfd9999aU, 0x00000000U, 0x00000000U}},
    {29U, "scaleY", 'f', {0x40133333U, 0x00000000U, 0x00000000U}},
    {29U, "centerX", 'f', {0x3f3ae148U, 0x00000000U, 0x00000000U}},
    {29U, "centerY", 'f', {0xbf1c28f6U, 0x00000000U, 0x00000000U}},
    {29U, "wrap", 'i', {0x00000002U, 0x00000000U, 0x00000000U}},
}};
constexpr std::array<Authority8ae8e2aTexture, 40> kAuthority8ae8e2aTextures{{
    {0U, "inputTex", 5U, 3U, 1U},
    {0U, "tex", 7U, 2U, 23U},
    {1U, "inputTex", 5U, 3U, 1U},
    {1U, "tex", 7U, 2U, 23U},
    {2U, "inputTex", 5U, 3U, 1U},
    {2U, "tex", 7U, 2U, 23U},
    {3U, "inputTex", 5U, 3U, 1U},
    {3U, "tex", 7U, 2U, 23U},
    {4U, "inputTex", 5U, 3U, 1U},
    {4U, "tex", 7U, 2U, 23U},
    {5U, "inputTex", 5U, 3U, 1U},
    {5U, "tex", 7U, 2U, 23U},
    {6U, "inputTex", 5U, 3U, 1U},
    {6U, "tex", 7U, 2U, 23U},
    {7U, "inputTex", 5U, 3U, 1U},
    {7U, "tex", 7U, 2U, 23U},
    {8U, "inputTex", 11U, 9U, 38U},
    {9U, "inputTex", 11U, 9U, 37U},
    {10U, "inputTex", 11U, 9U, 37U},
    {11U, "inputTex", 11U, 9U, 37U},
    {12U, "inputTex", 11U, 9U, 38U},
    {13U, "inputTex", 11U, 9U, 37U},
    {14U, "inputTex", 11U, 9U, 37U},
    {15U, "inputTex", 11U, 9U, 37U},
    {16U, "inputTex", 11U, 9U, 37U},
    {17U, "inputTex", 11U, 9U, 37U},
    {18U, "inputTex", 11U, 9U, 37U},
    {19U, "inputTex", 11U, 9U, 37U},
    {20U, "inputTex", 11U, 9U, 37U},
    {21U, "inputTex", 5U, 3U, 1U},
    {21U, "tex", 7U, 2U, 23U},
    {22U, "inputTex", 5U, 3U, 1U},
    {22U, "tex", 7U, 2U, 23U},
    {23U, "inputTex", 11U, 9U, 37U},
    {24U, "inputTex", 11U, 9U, 37U},
    {25U, "inputTex", 11U, 9U, 37U},
    {26U, "inputTex", 11U, 9U, 37U},
    {27U, "inputTex", 11U, 9U, 37U},
    {28U, "inputTex", 11U, 9U, 37U},
    {29U, "inputTex", 11U, 9U, 37U},
}};
// AUTHORITY_8AE8E2A_CASES_END

// Top-down RGBA8: every fifth pixel (counting from the tag) is opaque white and
// every seventh is all-zero; the rest is the asymmetric formula.
[[nodiscard]] noisemaker::Surface authority_8ae8e2a_texture(const Authority8ae8e2aTexture& spec) {
  std::vector<std::uint8_t> bytes(static_cast<std::size_t>(spec.width) * spec.height * 4U);
  for (std::uint32_t y = 0; y < spec.height; ++y) for (std::uint32_t x = 0; x < spec.width; ++x) {
    const std::uint32_t index = y * spec.width + x;
    const std::size_t lane = static_cast<std::size_t>(index) * 4U;
    if ((index + spec.tag) % 5U == 0U) {
      bytes[lane] = bytes[lane + 1U] = bytes[lane + 2U] = bytes[lane + 3U] = 255U;
    } else if ((index + spec.tag) % 7U == 0U) {
      bytes[lane] = bytes[lane + 1U] = bytes[lane + 2U] = bytes[lane + 3U] = 0U;
    } else {
      bytes[lane] = static_cast<std::uint8_t>((31U * x + 17U * y + 13U * spec.tag) % 256U);
      bytes[lane + 1U] = static_cast<std::uint8_t>((11U * x + 47U * y + 29U * spec.tag) % 256U);
      bytes[lane + 2U] = static_cast<std::uint8_t>((67U * x + 19U * y + 7U * spec.tag) % 256U);
      bytes[lane + 3U] = static_cast<std::uint8_t>(
          static_cast<std::int64_t>(255) - 23 * x - 37 * y - 5 * spec.tag);
    }
  }
  return noisemaker::Surface::from_rgba8(spec.width, spec.height, bytes);
}

[[nodiscard]] noisemaker::Surface render_authority_8ae8e2a(std::uint32_t index) {
  const Authority8ae8e2aCase& fixture = kAuthority8ae8e2aCases[index];
  std::vector<noisemaker::Surface> surfaces;
  surfaces.reserve(kAuthority8ae8e2aTextures.size());
  noisemaker::glsl::Bindings bindings;
  const float width = static_cast<float>(fixture.width);
  const float height = static_cast<float>(fixture.height);
  // Match current createCanonicalBindings derived uniforms for the full image.
  bindings.set_uniform("resolution", noisemaker::glsl::Vec2(width, height));
  bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(fixture.tile_offset[0], fixture.tile_offset[1]));
  bindings.set_uniform("fullResolution",
                       noisemaker::glsl::Vec2(fixture.full_resolution[0], fixture.full_resolution[1]));
  bindings.set_uniform("time", noisemaker::uint_bits_to_float(fixture.time_bits));
  const double aspect = static_cast<double>(fixture.full_resolution[0]) / fixture.full_resolution[1];
  bindings.set_uniform("aspect", static_cast<float>(aspect));
  bindings.set_uniform("aspectRatio", static_cast<float>(aspect));
  bindings.set_uniform("aspectInv", static_cast<float>(1.0 / aspect));
  bindings.set_uniform("invFullResolution", noisemaker::glsl::Vec2(
      static_cast<float>(1.0 / fixture.full_resolution[0]),
      static_cast<float>(1.0 / fixture.full_resolution[1])));
  bindings.set_uniform("renderScale", 1.0f);
  if (fixture.key == "classicNoisedeck/effects:effects") {
    // These captures use the authority defaults; the current route binds
    // both defines at runtime.
    bindings.set_uniform("EFFECT", std::int32_t(0));
    bindings.set_uniform("FLIP", std::int32_t(0));
  }
  for (const Authority8ae8e2aUniform& uniform : kAuthority8ae8e2aUniforms) {
    if (uniform.case_index != index) continue;
    const std::string name(uniform.name);
    switch (uniform.kind) {
      case 'i': bindings.set_uniform(name, static_cast<std::int32_t>(uniform.words[0])); break;
      case 'f': bindings.set_uniform(name, noisemaker::uint_bits_to_float(uniform.words[0])); break;
      case 'b': bindings.set_uniform(name, uniform.words[0] != 0U); break;
      case '3':
        bindings.set_uniform(name, noisemaker::glsl::DVec3(
            noisemaker::uint_bits_to_float(uniform.words[0]),
            noisemaker::uint_bits_to_float(uniform.words[1]),
            noisemaker::uint_bits_to_float(uniform.words[2])));
        break;
      default: throw std::logic_error("unknown capture uniform kind");
    }
  }
  for (const Authority8ae8e2aTexture& texture : kAuthority8ae8e2aTextures) {
    if (texture.case_index != index) continue;
    surfaces.push_back(authority_8ae8e2a_texture(texture));
    bindings.set_texture(std::string(texture.name), surfaces.back());
  }
  return noisemaker::run_pass(
      noisemaker::generated::bind(fixture.key, bindings), fixture.width, fixture.height,
      noisemaker::uint_bits_to_float(fixture.time_bits), static_cast<float>(fixture.seed),
      fixture.frame, 1.0f / 60.0f);
}

TEST(typed_authority_8ae8e2a_captures_are_exact_and_repeatable) {
  for (std::uint32_t index = 0; index < kAuthority8ae8e2aCases.size(); ++index) {
    const Authority8ae8e2aCase& fixture = kAuthority8ae8e2aCases[index];
    const noisemaker::Surface first = render_authority_8ae8e2a(index);
    const noisemaker::Surface second = render_authority_8ae8e2a(index);
    require_repeat(first, second);
    if (hex(sha256(little_endian_float_bytes(first))) != fixture.float_hash ||
        hex(sha256(first.to_rgba8())) != fixture.rgba_hash) {
      throw std::runtime_error(std::string(fixture.name) + ": 8ae8e2a capture mismatch");
    }
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
  bindings.set_uniform("aspect", noisemaker::uint_bits_to_float(0x3fa576a2U));
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
  bindings.set_uniform("fgColor", noisemaker::glsl::DVec3(
      noisemaker::uint_bits_to_float(fixture.fg_bits[0]),
      noisemaker::uint_bits_to_float(fixture.fg_bits[1]),
      noisemaker::uint_bits_to_float(fixture.fg_bits[2])));
  bindings.set_uniform("bgColor", noisemaker::glsl::DVec3(
      noisemaker::uint_bits_to_float(fixture.bg_bits[0]),
      noisemaker::uint_bits_to_float(fixture.bg_bits[1]),
      noisemaker::uint_bits_to_float(fixture.bg_bits[2])));
  return noisemaker::run_pass(
      noisemaker::generated::bind_synth_sacredGeometry_sacredGeometry(bindings),
      37U, 23U, noisemaker::uint_bits_to_float(fixture.time_bits), 23.0f,
      11U, noisemaker::uint_bits_to_float(0x3c888889U));
}

TEST(typed_task20_sacred_geometry_external_oracles_are_exact_and_repeatable) {
  const std::array<Task20Case, 11> fixtures{{
      {"geometry-0-flower-default-control", 0x3eaccccdU, 0x41200000U,
       0x00000000U, 0x3e4ccccdU, 0x3ca3d70aU,
       0, 3, 5, 0,
       0x3f800000U, 0x3e19999aU, {0x3f800000U, 0x3f800000U, 0x3f800000U}, {0x00000000U, 0x00000000U, 0x00000000U},
       "fc5265d3605f4fea4fdcda273bdd06e683cb9786673f1dba7f3294c6e084c0b8",
       "839c10ec3273b8bc4fc9c3245b49fc513803e1fe58c4c3bd89e70f6464a8fb11",
       {0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3e63d62eU, 0x3e63d62eU, 0x3e63d62eU, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x3f410051U, 0x3f410051U, 0x3f410051U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U, 0x00000000U, 0x00000000U, 0x00000000U, 0x3f800000U},
       0U, 433U,
       249U, 169U},
      {"geometry-1-fruit-animation-off", 0x3eaccccdU, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       1, 4, 7, 0,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "f11ad8eb98bce19933227fb38ab0c4888df7ea876a38f911f508db88a6089a62",
       "52a90288985c5e7cb3c455b58ffb64b6c365335aecc7200d8f8bfe5bbb9f6b6e",
       {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f696b8bU, 0x3f2a4293U, 0x3e580737U, 0x3f800000U},
       0U, 616U,
       132U, 103U},
      {"geometry-3-metatron-animation-off", 0x3eaccccdU, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       3, 4, 7, 0,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "7b29aafc75000b7da82a15ad30b77e1046340451ec9ad8be93c69db397dcd36c",
       "116f61afd10ccf1dba02786e751ea58399b278a66766ca242b2f6b63aefc9dee",
       {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3e17cac2U, 0x3e53e83fU, 0x3e9a01edU, 0x3f800000U, 0x3f0f8368U, 0x3ee8a1c9U, 0x3e812b2bU, 0x3f800000U, 0x3e2da37eU, 0x3e6103e3U, 0x3e98b8f1U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f696b8bU, 0x3f2a4293U, 0x3e580737U, 0x3f800000U},
       0U, 120U,
       290U, 441U},
      {"geometry-1-fruit-ripple", 0x3eaccccdU, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       1, 4, 7, 4,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "0530845ee4f2637154a532cd32668da5cf9560ecd6e7396c24fba2a2f975d970",
       "3c8fd01ab01d1a258ca14115f9816810d4d3ebd35e08c4fa4dba2880f90fb3b0",
       {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3dbc1461U, 0x3e314181U, 0x3e9d679cU, 0x3f800000U, 0x3f32d1dcU, 0x3f097ff7U, 0x3e71b8f3U, 0x3f800000U},
       0U, 460U,
       223U, 168U},
      {"geometry-3-metatron-unfold", 0x3ed33333U, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       3, 4, 7, 5,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "7684e6eb202d4ad871d475f4634fae90208090eeb88475c8fce32f89a65c6fed",
       "9411d0e41a6081c706b5ad6f7e0cfdfc33dc306f51416fdbe2b6203b84c244da",
       {0x3f53cd94U, 0x3f1d4a32U, 0x3e62336fU, 0x3f800000U, 0x3f53cd94U, 0x3f1d4a32U, 0x3e62336fU, 0x3f800000U, 0x3e0f0f72U, 0x3e4eab0fU, 0x3e9a856bU, 0x3f800000U, 0x3f01d310U, 0x3ed83493U, 0x3e8463b9U, 0x3f800000U, 0x3e22869dU, 0x3e5a58f5U, 0x3e99604aU, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3f53cd94U, 0x3f1d4a32U, 0x3e62336fU, 0x3f800000U, 0x3f53cd94U, 0x3f1d4a32U, 0x3e62336fU, 0x3f800000U, 0x3e3b4a58U, 0x3e6934ccU, 0x3e97eb5dU, 0x3f800000U},
       0U, 134U,
       0U, 717U},
      {"geometry-4-seed-rotate", 0x3eaccccdU, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       4, 4, 7, 1,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "9e34c924e1f3877083934d62aac1d722e53cd979307641d0b63f858cb10c0497",
       "8d3e2cd198ebe8257530c38512354b19116ca879fa27eceeea1665cc24970a71",
       {0x3f187a71U, 0x3ef363d3U, 0x3e7e1e53U, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f69c275U, 0x3f2a76b9U, 0x3e57de51U, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3f58b82eU, 0x3f203d5bU, 0x3e5fe327U, 0x3f800000U, 0x3edec421U, 0x3ec21360U, 0x3e88ba8bU, 0x3f800000U},
       0U, 74U,
       489U, 288U},
      {"geometry-5-vesica-pulse", 0x3eaccccdU, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       5, 4, 7, 2,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "32992d8b303d92fefb2d5e7383bde606e53d6dec07a0fa12b4ca49c2f0659b83",
       "683413061c05ef1c86080fb336366ccf444ffcc36af68492b5a355a222d8b381",
       {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U},
       0U, 851U,
       0U, 0U},
      {"geometry-5-vesica-pulse-visible-scale-16", 0x3eaccccdU, 0x41800000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       5, 4, 7, 2,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "b7f5cda337223fc06bd2f6e95d50266fdb4b41565b6bab3dfa574652592c0cba",
       "29a84ec3bfb586b33ed25b67a3306468bbaac9b25f0725fc40504688847352f7",
       {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3e7ed5b0U, 0x3e88ddcdU, 0x3e93f23aU, 0x3f800000U},
       0U, 696U,
       73U, 82U},
      {"geometry-6-borromean-ripple", 0x3eaccccdU, 0x41920000U,
       0x418b0000U, 0x3eae147bU, 0x3ce147aeU,
       6, 4, 7, 4,
       0x40300000U, 0x3e9eb852U, {0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU}, {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U},
       "5fc17595d0d0a1f82a2792e73486691370a8b0ca8402f61c8c14dadbacf41961",
       "2e10fb5660e04c7523c7bf29df18c0d39dd9e9e3be8ea925db194ab2978832c5",
       {0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3e7d79d1U, 0x3e887571U, 0x3e9406b0U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3ed0057dU, 0x3eb93a97U, 0x3e8a769fU, 0x3f800000U, 0x3f6b851fU, 0x3f2b851fU, 0x3e570a3dU, 0x3f800000U, 0x3ea769c6U, 0x3ea0dd29U, 0x3e8f3da5U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U},
       0U, 542U,
       174U, 135U},
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
       "10c62c72cc22fdbffd860bd02913473826c46b8d4be9d216fa7ceb38d7219c0a",
       "290bff21210403c0b559f347a081b0e58e88d1e904dee1f85d528248f1fc3f1f",
       {0x3e825562U, 0x3e8a9dbaU, 0x3e939a66U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U, 0x3d8f5c29U, 0x3e23d70aU, 0x3e9eb852U, 0x3f800000U},
       0U, 848U,
       0U, 3U},
  }};
  for (const Task20Case& fixture : fixtures) {
    const noisemaker::Surface first = render_task20(fixture);
    const noisemaker::Surface second = render_task20(fixture);
    require_repeat(first, second);
    REQUIRE(first.width() == 37U); REQUIRE(first.height() == 23U);
    const std::string float_hash = hex(sha256(little_endian_float_bytes(first)));
    if (float_hash != fixture.float_hash)
      throw std::runtime_error(std::string(fixture.name) + " float oracle hash: " + float_hash);
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
      "f866f3855885250a78169a56f32f59b15379152d47eebf1d4e6cec20a0e53b6f", "9e02468af87d81a5d0a558ac965dd9e4f78b07a768b855e157d5769bcbd3ee98",
      {0U, 0U, 0x3ec74910U, 0x3e11ae50U, 0x3e472d44U, 0x00000000U, 12U, 0U, 0x3eec3e5dU, 0x3de52221U, 0x3f38f888U, 0x3f800000U, 0U, 8U, 0x3eab3907U, 0x3f2dc06fU, 0x3e9cd86fU, 0x3f2aaaabU, 12U, 8U, 0x3ef0eccfU, 0x3ef4e2e4U, 0x3f355a29U, 0x00000000U, 6U, 4U, 0x3ebd70a4U, 0x3eeaaaabU, 0x3f02e8baU, 0x3f555555U, 1U, 1U, 0x3f40a309U, 0x3ec5c41dU, 0x3f024884U, 0x3f555555U, 11U, 7U, 0x3e95ed77U, 0x3f05876aU, 0x3f160f7aU, 0x3f555555U, 9U, 2U, 0x3ed800e0U, 0x3ecb2413U, 0x3f03da96U, 0x3f6aaaabU},
      117U, 468U, 0U, 398U, 116U, 1U, 67U, 117U, 0U, 0x00000000U, 0x3f800000U
    },
    {
      "nondefault-landscape-tiled-negative-direction", 13U, 9U, {0x40e00000U, 0x41300000U}, {0x42240000U, 0x41e80000U},
      0x3ee00000U, 0x3e400000U, 0x3fe00000U, 37, 0xc3094000U,
      "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3",
      "361ac1ef7266451f4e3a4b74f9c1360c4dd9055ca9114877de0d5197614c1dda", "5dced19d2b93c865bee67ba5833da21085b56d27070dc0c996933582892166ec",
      {0U, 0U, 0x3eae6aaaU, 0x3eb6ad7fU, 0x3e02f7eeU, 0x00000000U, 12U, 0U, 0x3f3b0ed0U, 0x3f528f7bU, 0x3f34ea46U, 0x3f800000U, 0U, 8U, 0x3ec3c29cU, 0x3e625a81U, 0x3e76e398U, 0x3f2aaaabU, 12U, 8U, 0x3f0f3192U, 0x3f0a2582U, 0x3f20855eU, 0x00000000U, 6U, 4U, 0x3ef338b9U, 0x3edd9a52U, 0x3ed53157U, 0x3f555555U, 1U, 1U, 0x3f1221dcU, 0x3ed04270U, 0x3f4a44dbU, 0x3f555555U, 11U, 7U, 0x3f1f729dU, 0x3e8a0f62U, 0x3e733eebU, 0x3f555555U, 9U, 2U, 0x3f2cbd96U, 0x3f4b78bcU, 0x3f1f44adU, 0x3f6aaaabU},
      117U, 468U, 0U, 401U, 117U, 0U, 67U, 117U, 0U, 0x00000000U, 0x3f800000U
    },
    {
      "nondefault-portrait-tiled-positive-direction", 9U, 13U, {0x40a00000U, 0x40400000U}, {0x41b80000U, 0x42140000U},
      0x3f1ccccdU, 0x3e800000U, 0x40000000U, 100, 0x43340000U,
      "7ea6ac4f0ccd3f585245fab99613afd1a39cdeff0a484320f7dd1e4dabd83396", "d553b7ab55a780eb5bbc32c77103af6bf3660fc4046e6b3eeba8dbf45a2e9880",
      "cb1aa9143d7f05a1d3992467b343d2ff5da4fa546946b4ac33728dca22e3a21c", "02e75af7adc002d125c875129923831a3db7fbaede316260a3f12176b7b6a5b6",
      {0U, 0U, 0x3f34c216U, 0x3f250803U, 0x3f192b80U, 0x00000000U, 8U, 0U, 0x3ef2b68aU, 0x3edaba8bU, 0x3f1da687U, 0x3f800000U, 0U, 12U, 0x3ee8cf4dU, 0x3f3a431bU, 0x3f2a5227U, 0x3f800000U, 8U, 12U, 0x3ef4a6a1U, 0x3f3322b6U, 0x3efd9c33U, 0x3f155555U, 4U, 6U, 0x3f09b611U, 0x3e7f88f0U, 0x3ddeb0f5U, 0x3f800000U, 1U, 1U, 0x3f0dfd96U, 0x3f5367cdU, 0x3edc8b4bU, 0x3f555555U, 7U, 11U, 0x3e9b2d8cU, 0x3f3a0587U, 0x3f004d34U, 0x00000000U, 6U, 3U, 0x3eca409aU, 0x3ed326a4U, 0x3e93026bU, 0x3e800000U},
      117U, 468U, 0U, 403U, 117U, 0U, 65U, 117U, 0U, 0x00000000U, 0x3f800000U
    },
    {
      "speed-zero-nonzero-time", 13U, 9U, {0x40800000U, 0x40c00000U}, {0x41f80000U, 0x41c80000U},
      0x3f600000U, 0x3dc00000U, 0x00000000U, 19, 0x42050000U,
      "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3",
      "bfe2405b610d0a83dde7ac8a767936da729a0fc404d24b5c5e7f0e125f8e684f", "3d9e5456a005805257dc4d9dd34d02b25b3278da12abeb67c3066316edcda8d6",
      {0U, 0U, 0x3f0cc372U, 0x3f430a84U, 0x3f21b82cU, 0x00000000U, 12U, 0U, 0x3f28f1c6U, 0x3f4c0679U, 0x3ee1a6baU, 0x3f800000U, 0U, 8U, 0x3f0cc749U, 0x3f044a5cU, 0x3ef2c939U, 0x3f2aaaabU, 12U, 8U, 0x3eb81b0fU, 0x3f263f82U, 0x3e978426U, 0x00000000U, 6U, 4U, 0x3e91c080U, 0x3e84f814U, 0x3ebecbbfU, 0x3f555555U, 1U, 1U, 0x3e0b8a35U, 0x3d8463d2U, 0x3dbc3087U, 0x3f555555U, 11U, 7U, 0x3f350242U, 0x3eba243bU, 0x3edeb6cbU, 0x3f555555U, 9U, 2U, 0x3f01a1a2U, 0x3e0f29d0U, 0x3f289efeU, 0x3f6aaaabU},
      117U, 468U, 0U, 397U, 116U, 1U, 68U, 116U, 1U, 0xbe2aaaabU, 0x3f800000U
    },
    {
      "time-zero-positive-speed", 13U, 9U, {0x40400000U, 0x40000000U}, {0x41e80000U, 0x41a80000U},
      0x00000000U, 0x3e100000U, 0x3fc00000U, 53, 0xc2760000U,
      "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3",
      "350d07667e2df6a2c3eb09b70e17e355072d114bd88a99b01160ffe1ae32974e", "8bc8e7027373b0ef49c9b26adffe1b6a4958402e50e62494247a12b913e2785d",
      {0U, 0U, 0x3f0d439fU, 0x3ebe9622U, 0x3eba7c50U, 0x00000000U, 12U, 0U, 0x3ec89d77U, 0x3eda4840U, 0x3f50daa1U, 0x3f800000U, 0U, 8U, 0x3e897591U, 0x3f152bceU, 0x3f122aacU, 0x3f2aaaabU, 12U, 8U, 0x3effe7f6U, 0x3f47ec6fU, 0x3f2f73faU, 0x00000000U, 6U, 4U, 0x3f2ca481U, 0x3e869809U, 0x3f0beab9U, 0x3f555555U, 1U, 1U, 0x3ea339c8U, 0x3e6afce9U, 0x3f2643fcU, 0x3f555555U, 11U, 7U, 0x3f2a244eU, 0x3f0bf6c1U, 0x3e683ab0U, 0x3f555555U, 9U, 2U, 0x3f310ba7U, 0x3e1c99a7U, 0x3eac61c4U, 0x3f6aaaabU},
      117U, 468U, 0U, 398U, 116U, 1U, 67U, 117U, 0U, 0x00000000U, 0x3f800000U
    },
    {
      "full-resolution-zero-fallback-landscape", 13U, 9U, {0x40000000U, 0x3f800000U}, {0x00000000U, 0x00000000U},
      0x3ea00000U, 0x3e000000U, 0x3fa00000U, 11, 0x42910000U,
      "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3",
      "d14147fa42ecf04d6bcfe69421629d139b0da9e733a0d9bdaee19dc6c86bb534", "21887cecda8086b36c4f4de752944d228f5abb50f677745a17cb79d82957394f",
      {0U, 0U, 0x3f077310U, 0x3f0467a6U, 0x3ddc7d5bU, 0x00000000U, 12U, 0U, 0x3edc5254U, 0x3ed876c2U, 0x3f4fc3c4U, 0x3f800000U, 0U, 8U, 0x3f006c71U, 0x3f6527efU, 0x3e9f4dfcU, 0x3f2aaaabU, 12U, 8U, 0x3e6e3e87U, 0x3ed2d5c3U, 0x3d9213c6U, 0x00000000U, 6U, 4U, 0x3ef70e06U, 0x3e7059adU, 0x3f116522U, 0x3f555555U, 1U, 1U, 0x3f0c2bbfU, 0x3ed74a6bU, 0x3e2cf67dU, 0x3f555555U, 11U, 7U, 0x3f6178abU, 0x3f20c7a9U, 0x3f521007U, 0x3f555555U, 9U, 2U, 0x3f0803c1U, 0x3f07c5c7U, 0x3ece51f0U, 0x3f6aaaabU},
      117U, 468U, 0U, 398U, 116U, 1U, 67U, 117U, 0U, 0x00000000U, 0x3f800000U
    },
    {
      "square-frequency-equality", 11U, 11U, {0x40400000U, 0x40000000U}, {0x41f80000U, 0x41f80000U},
      0x3f0ccccdU, 0x3e600000U, 0x3f400000U, 71, 0xc3340000U,
      "b0f13bbfbca20ea2b40d7e19d75796f70ca2b641f564f26471869dbcd4c58da3", "c43c7e0c9248875f403f003073c29e69dd7f368a59223e01927d177b6f610acc",
      "bba736cff27c6ad6dadd18a954a08c4b4369032feb596d064f57f1751ab86e8d", "cb38bf280658b38f4826f8315f6d56c6459d9ab4108d44b875ca72115d8c1ca5",
      {0U, 0U, 0x3f397617U, 0x3e66476eU, 0x3f0e3590U, 0x00000000U, 10U, 0U, 0x3f3547ccU, 0x3eeec41eU, 0x3e1e3ab3U, 0x3e2aaaabU, 0U, 10U, 0x3ebcc9a9U, 0x3da315ceU, 0x3ef96b00U, 0x00000000U, 10U, 10U, 0x3ef8086cU, 0x3f1b6543U, 0x3f42e86bU, 0x3e800000U, 5U, 5U, 0x3f1c6ec5U, 0x3e9b9bcfU, 0x3f24d4b2U, 0x3f800000U, 1U, 1U, 0x3f4583a0U, 0x3e4fe19aU, 0x3f384f9dU, 0x3f555555U, 9U, 9U, 0x3ea8d417U, 0x3e3c86cdU, 0x3e6bf9baU, 0x3f800000U, 7U, 3U, 0x3f3f6136U, 0x3ef3c8f6U, 0x3ee7acecU, 0x3f2aaaabU},
      121U, 484U, 0U, 416U, 121U, 0U, 68U, 121U, 0U, 0x00000000U, 0x3f800000U
    },
    {
      "untiled-over-cap-binding-domain-diagnostic", 13U, 9U, {0x00000000U, 0x00000000U}, {0x41500000U, 0x41100000U},
      0x3ef00000U, 0x3fe00000U, 0x3fa00000U, 29, 0x42b40000U,
      "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3",
      "8f70a5e03d90c93dbc18ff768108a638b938781cd464418b5d07dff674a1e55f", "ee597e5fc86137977db87fc32f06b81e8423820457b5a96f7d8efe5f918bb412",
      {0U, 0U, 0x3f260621U, 0x3f3dd26cU, 0x3f2a18ebU, 0x00000000U, 12U, 0U, 0x3ee7811bU, 0x3f1c2147U, 0x3f052828U, 0x3f800000U, 0U, 8U, 0x3f004161U, 0x3f60967cU, 0x3eca43f0U, 0x3f2aaaabU, 12U, 8U, 0x3e55cd47U, 0x3edd5954U, 0x3f354e85U, 0x00000000U, 6U, 4U, 0x3ebd70a4U, 0x3eeaaaabU, 0x3f02e8baU, 0x3f555555U, 1U, 1U, 0x3f3ee3feU, 0x3eed0e16U, 0x3f3a5fe9U, 0x3f555555U, 11U, 7U, 0x3f1531f2U, 0x3f0ebe82U, 0x3eeb9b51U, 0x3f555555U, 9U, 2U, 0x3e818330U, 0x3f489cf2U, 0x3e879613U, 0x3f6aaaabU},
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
    const std::string float_hash = hex(sha256(little_endian_float_bytes(first)));
    if (float_hash != fixture.output_float_hash)
      throw std::runtime_error(std::string(fixture.name) + " float oracle hash: " + float_hash);
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
    {"default-landscape-untiled", 13U, 9U, {0x00000000U, 0x00000000U}, {0x41500000U, 0x41100000U}, 0x3ec00000U, 0x3f000000U, 0x3f800000U, 1, 0x3f800000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "8d79ffbb89906ab3ac639254ad939a80b700609c11b3052da69d7d1b308a1ead", "b119d07a2c71836c7ae0ae8fb26deb0942ba5254c50b8f10e1a57983e4abc80d", {0U, 0U, 0x3e6f3c09U, 0x3eb2cacbU, 0x3e1d97c7U, 0xbe2aaaabU, 12U, 0U, 0x3e656566U, 0x3e3bdbdcU, 0x3f556f9eU, 0x3f800000U, 0U, 8U, 0x3f26e07aU, 0x3f637b7cU, 0x3d9af810U, 0x3f2aaaabU, 12U, 8U, 0x3f1fe64dU, 0x3f3b0f0fU, 0x3f5b82c8U, 0xbdaaaaabU, 6U, 4U, 0x3eea43deU, 0x3f0dfdfeU, 0x3f1ccfb8U, 0x3f555555U, 1U, 1U, 0x3eff8c5aU, 0x3eccf4f6U, 0x3e8ff5c7U, 0x3f555555U, 11U, 7U, 0x3dc15af4U, 0x3ea84040U, 0x3e97fdcfU, 0x3f555555U}, 117U, 468U, 0U, 351U, 117U, 0U, 117U, 50U},
    {"alpha-above-one-clamps-and-preserves-input-alpha", 13U, 9U, {0x00000000U, 0x00000000U}, {0x41500000U, 0x41100000U}, 0x3ee00000U, 0x3fe00000U, 0x3f800000U, 11, 0x3f800000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "db6a4c4b1828da7def9818c90a04156914cc1fb57dd4fd6e8fc471e625a67203", "b971437eec882ffd958b151216992caad58a8a681211f161ec60480820d52fee", {0U, 0U, 0x3e40c0c1U, 0x3e989899U, 0x3de8e8e9U, 0xbe2aaaabU, 12U, 0U, 0x3f38b8b9U, 0x00000000U, 0x3ed8d8d9U, 0x3f800000U, 0U, 8U, 0x3f078788U, 0x3f40c0c1U, 0x00000000U, 0x3f2aaaabU, 12U, 8U, 0x3ef0f0f1U, 0x3ea6a6a7U, 0x3ee4e4e5U, 0xbdaaaaabU, 6U, 4U, 0x3eb4b4b5U, 0x3ee2e2e3U, 0x3efefeffU, 0x3f555555U, 1U, 1U, 0x3ecccccdU, 0x3e0c8c8dU, 0x3d70f0f1U, 0x3f555555U, 11U, 7U, 0x3da0a0a1U, 0x3de8e8e9U, 0x3df0f0f1U, 0x3f555555U}, 117U, 468U, 0U, 351U, 117U, 0U, 117U, 50U},
    {"landscape-tiled-render-scale-two", 13U, 9U, {0x40e00000U, 0x41300000U}, {0x423c0000U, 0x41b80000U}, 0x3ee00000U, 0x3f400000U, 0x3fe00000U, 37, 0x40000000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "d93238b6ab384881dc5bfb5d6e51e33db46b6f8430068d62bd30d5cd7e7b10af", "8b01630d856e5de5c694addc6bb8f3aecdfe561d18d777cbb773b99e983d113c", {0U, 0U, 0x3e83164aU, 0x3ec14d4dU, 0x3e312e46U, 0xbe2aaaabU, 12U, 0U, 0x3f02d2d3U, 0x3e132323U, 0x3f1e2b43U, 0x3f800000U, 0U, 8U, 0x3f14713eU, 0x3f4fdbdcU, 0x3c3a2e8cU, 0x3f2aaaabU, 12U, 8U, 0x3f076a9eU, 0x3f194344U, 0x3f65b95cU, 0xbdaaaaabU, 6U, 4U, 0x3ed3804dU, 0x3ecfbfc0U, 0x3eac5f48U, 0x3f555555U, 1U, 1U, 0x3f379aceU, 0x3ef78b8cU, 0x3ea65942U, 0x3f555555U, 11U, 7U, 0x3e04ab12U, 0x3ed39fa0U, 0x3f059f14U, 0x3f555555U}, 117U, 468U, 0U, 351U, 117U, 0U, 117U, 50U},
    {"portrait-tiled-fractional-render-scale", 9U, 13U, {0x40a00000U, 0x40400000U}, {0x41b80000U, 0x42140000U}, 0x3f1ccccdU, 0x3f200000U, 0x40000000U, 100, 0x3fc00000U, "7ea6ac4f0ccd3f585245fab99613afd1a39cdeff0a484320f7dd1e4dabd83396", "d553b7ab55a780eb5bbc32c77103af6bf3660fc4046e6b3eeba8dbf45a2e9880", "df4de8296c90676f60025d0fff1869d001d5835343fba8e59f0ac2edc49fdbf9", "8c55dd1ea14b3cf06413cc902253ee1d7c674ff33776ca2c937c9992b22f56a9", {0U, 0U, 0x3dd74a7eU, 0x3e4f7374U, 0x3d1d8c18U, 0xbe2aaaabU, 8U, 0U, 0x3edfecbaU, 0x3f368788U, 0x3eded84dU, 0x3fa00000U, 0U, 12U, 0x3f14fe98U, 0x3ecb1919U, 0x3eb687fdU, 0x3f8aaaabU, 8U, 12U, 0x3de94fb6U, 0x3e428283U, 0x3ec0c17cU, 0x3f155555U, 4U, 6U, 0x3ee8b8b9U, 0x3f22bebfU, 0x3ed3a2e9U, 0x3f955555U, 1U, 1U, 0x3ef51eb9U, 0x3eb39192U, 0x3e64fdb8U, 0x3f555555U, 7U, 11U, 0x3f256094U, 0x3f475050U, 0x3ec88713U, 0xbed55555U}, 117U, 468U, 0U, 350U, 117U, 0U, 117U, 52U},
    {"speed-zero-nonzero-time", 13U, 9U, {0x40800000U, 0x40c00000U}, {0x41f80000U, 0x41c80000U}, 0x3f600000U, 0x3f600000U, 0x00000000U, 19, 0x3f800000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "50e355ebf7f615c611b33ba28a0ea4ba39ea15ef7f1abcfc7e1bc57e43d3bd84", "7fc20e14302c8dd5b1abd2561fc5f0749e1e7b014b5feb583f5cc734bc6e2e19", {0U, 0U, 0x3e8dd771U, 0x3ecd1313U, 0x3e45038fU, 0xbe2aaaabU, 12U, 0U, 0x3e34d4d5U, 0x3e01494aU, 0x3f7f45d2U, 0x3f800000U, 0U, 8U, 0x3ef511dfU, 0x3f303636U, 0x3bba2e8cU, 0x3f2aaaabU, 12U, 8U, 0x3eed90c4U, 0x3f1b3030U, 0x3f0cb688U, 0xbdaaaaabU, 6U, 4U, 0x3e7eab78U, 0x3edcd4d5U, 0x3e356851U, 0x3f555555U, 1U, 1U, 0x3f2e1fbaU, 0x3f2e7374U, 0x3e86a014U, 0x3f555555U, 11U, 7U, 0x3dd0f75eU, 0x3eeb1111U, 0x3ea80176U, 0x3f555555U}, 117U, 468U, 0U, 348U, 117U, 0U, 117U, 50U},
    {"time-zero-positive-speed", 13U, 9U, {0x40400000U, 0x40000000U}, {0x41e80000U, 0x41a80000U}, 0x00000000U, 0x3f600000U, 0x3fc00000U, 53, 0x3f800000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "e8c211553f7fb1a7398cc4ce4f1dd9c1ff5c14b02fe24c4e097f9de8d418fa16", "9c9a2e5f1c63dde9de72bebded827b52339bad6d06fcb035da5c7f2286aad86d", {0U, 0U, 0x3de60c73U, 0x3e58e4e5U, 0x3d45bfefU, 0xbe2aaaabU, 12U, 0U, 0x3cb5b5b6U, 0x3c555555U, 0x3f3ba22eU, 0x3f800000U, 0U, 8U, 0x3ec21eecU, 0x3f0df3f4U, 0x3bba2e8cU, 0x3f2aaaabU, 12U, 8U, 0x3eb1d509U, 0x3f08bdbeU, 0x3ee83bdfU, 0xbdaaaaabU, 6U, 4U, 0x3e15420fU, 0x3eb9b1b2U, 0x3e07baa3U, 0x3f555555U, 1U, 1U, 0x3f247610U, 0x3f38fdfeU, 0x3e99f368U, 0x3f555555U, 11U, 7U, 0x3dc2e950U, 0x3ecef4f5U, 0x3ee90277U, 0x3f555555U}, 117U, 468U, 0U, 348U, 117U, 0U, 117U, 50U},
    {"full-resolution-zero-fallback", 13U, 9U, {0x40000000U, 0x3f800000U}, {0x00000000U, 0x00000000U}, 0x3ea00000U, 0x3f400000U, 0x3fa00000U, 11, 0x3f800000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "70e7b389149a2d86cb8771d9c2cbf6324a3d4132433946157674b82a7703f69a", "6503af699c4bbefc4dda800dfdb455b397b05165486e6866de4ebc0f474b5377", {0U, 0U, 0x3dbb07d5U, 0x3e3bd3d4U, 0x3cecd590U, 0xbe2aaaabU, 12U, 0U, 0x3f12a2a3U, 0x3cd55555U, 0x3f0f1c34U, 0x3f800000U, 0U, 8U, 0x3ed30ca6U, 0x3f18e4e5U, 0x3c3a2e8cU, 0x3f2aaaabU, 12U, 8U, 0x3f016498U, 0x3ed3a7a8U, 0x3f13a74aU, 0xbdaaaaabU, 6U, 4U, 0x3e83b07dU, 0x3eab9b9cU, 0x3ec2f5dfU, 0x3f555555U, 1U, 1U, 0x3f09ace0U, 0x3e8fa3a4U, 0x3e5a4011U, 0x3f555555U, 11U, 7U, 0x3dbb07d5U, 0x3e3f5757U, 0x3e5d4314U, 0x3f555555U}, 117U, 468U, 0U, 351U, 117U, 0U, 117U, 50U},
    {"square-large-time-max-metadata", 11U, 11U, {0x40400000U, 0x40000000U}, {0x41f80000U, 0x41f80000U}, 0x4640e680U, 0x3f800000U, 0x40a00000U, 100, 0x3fc00000U, "b0f13bbfbca20ea2b40d7e19d75796f70ca2b641f564f26471869dbcd4c58da3", "c43c7e0c9248875f403f003073c29e69dd7f368a59223e01927d177b6f610acc", "b358b073881dd9e560052bf8204bb9b4fb2baf36d6914a67560252f4bf8682d5", "3123832208dc84924af2cae7b1f93e7cf959f72f4df0087f909f7697daca57cd", {0U, 0U, 0x3e848485U, 0x3ec2c2c3U, 0x3e34b4b5U, 0xbe2aaaabU, 10U, 0U, 0x3f2dadaeU, 0x3f800000U, 0x3f71f1f2U, 0x3e2aaaabU, 0U, 10U, 0x3e9e9e9fU, 0x3e9e9e9fU, 0x3ed4d4d5U, 0xbdaaaaabU, 10U, 10U, 0x3f74f4f5U, 0x3f68e8e9U, 0x3e38b8b9U, 0x3e800000U, 5U, 5U, 0x3eeaeaebU, 0x3f44c4c5U, 0x3f800000U, 0x3f800000U, 1U, 1U, 0x3f32b2b3U, 0x3efcfcfdU, 0x3e60e0e1U, 0x3f555555U, 9U, 9U, 0x3e868687U, 0x3f52d2d3U, 0x3f53d3d4U, 0x3f955555U}, 121U, 484U, 0U, 361U, 121U, 0U, 121U, 53U},
    {"render-scale-below-one-clamps", 13U, 9U, {0x00000000U, 0x00000000U}, {0x41500000U, 0x41100000U}, 0x3ef00000U, 0x3f000000U, 0x3fa00000U, 29, 0x3f000000U, "daa97cd0ed2558e4b8535a8eb0443bb9aecd825b805ae6ba16a69c632ed72687", "5c5880004ebaa8f69183c50af07a663bf27b04d63dae0bff24d6fc1d015a37d3", "4af92d87e04669063f3cdad9601ad08a57b5d64e9aa0bd4c5da4270ea0ee0381", "442879a307d31f079e3279360b68cf9fb95fd949f47e6ad266caf939386d3ed3", {0U, 0U, 0x3ddd7710U, 0x3e570707U, 0x3d2c9550U, 0xbe2aaaabU, 12U, 0U, 0x3e87c7c8U, 0x3e29c9caU, 0x3f46e110U, 0x3f800000U, 0U, 8U, 0x3eed6094U, 0x3f284040U, 0x3cba2e8cU, 0x3f2aaaabU, 12U, 8U, 0x3ef17e4cU, 0x3f1beff0U, 0x3f3be329U, 0xbdaaaaabU, 6U, 4U, 0x3ef24be6U, 0x3ebb9b9cU, 0x3eea5022U, 0x3f555555U, 1U, 1U, 0x3ec04d1aU, 0x3ed3fbfcU, 0x3e92f8caU, 0x3f555555U, 11U, 7U, 0x3d952ec8U, 0x3eb95152U, 0x3eb116e8U, 0x3f555555U}, 117U, 468U, 0U, 351U, 117U, 0U, 117U, 50U}
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

// Captured directly from the unmodified JS authority 5b686a45b5c56329adf0c63cbcf572eb6f23fad1,
// canonicalKernelFactories["points/life:matrix"], with the bindings below.
// compile-glsl.js routes hash_uint by its GLSL body: this LCG-seeded body maps
// to stdlib.hashUintLcg (before 5b686a4 every body took the murmur finalizer).
TEST(typed_life_matrix_uses_the_authority_lcg_hash) {
  noisemaker::glsl::Bindings bindings;
  bindings.set_uniform("resolution", noisemaker::glsl::Vec2(17.0f, 11.0f));
  bindings.set_uniform("typeCount", std::int32_t(16));
  bindings.set_uniform("matrixSeed", 1.23456789);
  bindings.set_uniform("symmetricForces", true);
  const auto surface = noisemaker::run_pass(
      noisemaker::generated::bind_points_life_matrix(bindings), 17U, 11U);
  REQUIRE(hex(sha256(little_endian_float_bytes(surface))) ==
          "247562648768305a8ced53e4937c8309881dfda144e43f453665b015ee34bde5");
  REQUIRE(hex(sha256(surface.to_rgba8())) ==
          "4f1e94b2f3839e30ea668a3b3240890c15788ba7123de3cbb6e62b7c1ba44b58");
}

// Same unmodified authority and direct pass runner as the Life capture above.
// Alive agents with zero stored seeds execute Hydraulic's hash2 path.
TEST(typed_hydraulic_preserves_authority_signed_number_hash) {
  constexpr std::size_t width = 17U, height = 11U;
  noisemaker::Surface input(width, height), xyz(width, height), vel(width, height), rgba(width, height);
  input.clear({0.2f, 0.3f, 0.4f, 1.0f});
  xyz.clear({0.25f, 0.75f, 0.0f, 1.0f});
  vel.clear({0.05f, 0.025f, 0.0f, 0.0f});
  rgba.clear({0.2f, 0.4f, 0.6f, 1.0f});
  noisemaker::glsl::Bindings bindings;
  bindings.set_uniform("resolution", noisemaker::glsl::Vec2(17.0f, 11.0f));
  bindings.set_uniform("time", 0.25);
  bindings.set_uniform("stride", 10.0);
  bindings.set_uniform("quantize", 0.0);
  bindings.set_uniform("inverse", 0.0);
  bindings.set_uniform("inputWeight", 100.0);
  bindings.set_texture("inputTex", input);
  bindings.set_texture("xyzTex", xyz);
  bindings.set_texture("velTex", vel);
  bindings.set_texture("rgbaTex", rgba);
  const auto surfaces = noisemaker::run_mrt_pass(
      noisemaker::generated::bind_points_hydraulic_agent(bindings), width, height, 0.25f);
  const std::array<std::string_view, 3> float_hashes = {
      "cb0a9ce2ea7e3a86fc4973648c2bc38b0b713bab28c192a3aa032e97a0c3620b",
      "571f549cf889f7476ce1ad5655172b6c1a1fc34c060366970f1bbe6fa4fb8bb5",
      "77a3411ccfd8928e76ef86d655a49ffe95310c4175a764c35a6f74130ea60f1e"};
  const std::array<std::string_view, 3> rgba_hashes = {
      "faed21f9654262da7d570c76ef77c8d5e846389070c8ba8072e324529318a0b7",
      "d34851c99fe5c1ee08b304d55fca9ea1a49f6fb77db6e51086c25db95045a673",
      "874fd948f07d2d313d58d88bbb4dcb4e3eeab3717a11f7225b1974a4d1042a13"};
  REQUIRE(surfaces.size() == 3U);
  for (std::size_t i = 0; i < surfaces.size(); ++i) {
    REQUIRE(hex(sha256(little_endian_float_bytes(surfaces[i]))) == float_hashes[i]);
    REQUIRE(hex(sha256(surfaces[i].to_rgba8())) == rgba_hashes[i]);
  }
}

// Unmodified CPU 9f3bd6a canonical Noise3D MRT captures, with defaults
// OCTAVES=1, COLOR_MODE=0 and RIDGES=0. The current authority uses unsigned
// 32-bit products and XOR before conversion to a Float32 noise value.
TEST(typed_noise3d_preserves_authority_hash4_number_rounding) {
  struct Case { std::int32_t volume, seed; double scale, time; };
  const std::array<Case, 3> cases = {{{2, 0, 1.3, 0.25}, {2, 42, 1.3, 0.25}, {3, 42, 2.7, 0.375}}};
  const std::array<std::array<std::string_view, 2>, 6> hashes = {{
      {"52488951ee237a096966529945fb8a126f5de036f24307f66b4ff35836389614", "b73670efc24f122726eec3436ae92a937e0a7365df30aba1d527a93ba1960f9a"},
      {"556157a402108b9913bd168209eadafb2af0597e0918c420577dcb4d86f34727", "59fcdde9b8682e4b007ef84f3f24bd74062ae30cb99b2f4bfba51d31629362e7"},
      {"3032c7d8ca0e7f875c5c63499363121fa70cbc832fdcbf0a0ae08d2986ffe61c", "dc43f2dda7a3c4610e9bda7fd1dd1f4d4f8d59e07f2f20d579513e0aad1f8825"},
      {"9948c67bfa7e1bd28a4bcb9f7bd7a9c8cdb1d40287a96d4e3236ce614911fa5d", "7af56a1a02102559b9e709ee21893a1ae922dc6d0a164d8f0674a2ac95383a7b"},
      {"53ccf34d0fc83e3400f3c8b1a93bd4f5db8ca17c9fb3e2d2051ff361c5a4e99d", "cdc6258f27b880ac4497c6ab3a0aac106422a13c1e39bc4ab39db216be7a0ab2"},
      {"5c6d84c7032349996eaa8aa844f29b4a3af99e22fbac356e5ae7e5022038768b", "d88dffe2cb77826e743661b5dc18c9236ae98351f3a79235cf70267ab0dfa0db"}}};
  std::size_t capture = 0;
  for (const auto& item : cases) {
    const auto width = static_cast<std::size_t>(item.volume);
    const auto height = width * width;
    noisemaker::glsl::Bindings bindings;
    bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(0.0f, 0.0f));
    bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(static_cast<float>(width), static_cast<float>(height)));
    bindings.set_uniform("time", item.time);
    bindings.set_uniform("scale", item.scale);
    bindings.set_uniform("seed", static_cast<double>(item.seed));
    bindings.set_uniform("volumeSize", item.volume);
    bindings.set_uniform("speed", 1.0);
    bindings.set_uniform("OCTAVES", std::int32_t{1});
    bindings.set_uniform("COLOR_MODE", std::int32_t{0});
    bindings.set_uniform("RIDGES", false);
    const auto surfaces = noisemaker::run_mrt_pass(
        noisemaker::generated::bind_synth3d_noise3d_precompute(bindings), width, height, static_cast<float>(item.time));
    REQUIRE(surfaces.size() == 2U);
    for (const auto& surface : surfaces) {
      const auto float_hash = hex(sha256(little_endian_float_bytes(surface)));
      const auto rgba_hash = hex(sha256(surface.to_rgba8()));
      if (float_hash != hashes[capture][0] || rgba_hash != hashes[capture][1]) {
        throw std::runtime_error("Noise3D capture " + std::to_string(capture) +
                                 " float=" + float_hash + " rgba=" + rgba_hash +
                                 " first=" + std::to_string(noisemaker::float_bits_to_uint(surface.data()[0])));
      }
      ++capture;
    }
  }
}

// Authenticated CPU 9f3bd6a canonical MRT, measured with the full Number
// render seed before hash4's Float32 lanes and JavaScript ToInt32 conversion.
TEST(typed_noise3d_large_seed_number_and_int32_wrap_match_cpu) {
  struct Case {
    std::int32_t volume;
    double seed, scale, time;
    std::array<std::string_view, 2> f32;
    std::array<std::string_view, 2> rgba;
  };
  const std::array<Case, 8> cases = {{
      {3, 0.0, 2.7, 0.375,
       {"3ada7df17298b44752bed96c6b5060f1082a4d64d013828de89c2cd7bd7d66b0", "1cfd31412bf3c30d4ac50eb4f03467ac487c1127139d5f7bc68715de62acd35a"},
       {"06860629591fc306f3a51d9d835d7d0a45cfbd05c70a5b3f159350140ef63cb6", "9ab25a6c7820dae5d3391127fefd35899ab8fb6f50a49b4dcbbdbe85978ad809"}},
      {3, 31576719.0, 2.7, 0.375,
       {"1bd27b58d0e53f465977d0058d60fd2bf9431e8859bc5e5fdb80d496dc69380d", "4944f68da13cb749132dda76c0164e62de8f2f619005dada27f4a7ab8404a92a"},
       {"edbc2720d7548cdccd964a59bc56b8eb6fc550a695a810d0c537dc2ba30688b6", "2600cc337342b60fea205d69be8a338c117cefe46a8131ead6e6457d73b10006"}},
      {3, 1512140165.0, 2.7, 0.375,
       {"1f25b3f87342bfc8dc30d1670fac126acbe7a09fb0a727fd011171138e046e6e", "2bb710e8e9afabd4666abb6062163d0e598f8270348e3f4e353904fba9bca25e"},
       {"8de4419743e7dd1139cf1508de97bdf9a6fb1a93554ba43ef48e21e622dc7573", "0e225a5a32dc3e3f1f9728804217ed7ebac1ec4eeab5d7edef8ff674468dccd7"}},
      {3, 2687862216.0, 2.7, 0.375,
       {"aff11200f979721f69d5e79d647385fa4f1844070f3a21955d4441493f5acb9d", "243130a0e04f0f846679e51f346990b0f57549f9103d526c8606e98c6ecbae90"},
       {"2249dbd1d68146e77e0f8176b0f5fc7f9333c7c83552887ed451cecf4ac9835e", "ed607d066af0d05a8c7f944a892a83e0f54b8be8139d13f145d93177d7fd728b"}},
      {3, 4294967295.0, 2.7, 0.375,
       {"0183b4416a48aa932b97e780d8298232c63ee2a3f024938572ae5afc8cf592b9", "f7b0e0da49bfcb4f7100a97f895a83ef2a6e8a1ef552e3346da1e02b3189120e"},
       {"85a5dab36f26a3beb8c56b26a9dd033bb2f6822362719d64e54d413cc537e331", "aa516fa9eedc5cf707dcca5c76793517f2550e765ede2b8b222105b9c61edacb"}},
      {3, 2147483647.0, 2.7, 0.375,
       {"c00be0d109049e19497111c7483abceed4e766138f6fb6ce6cfeee75390feb47", "118a6745fbcdfdb256e3e11ed3c1d1ac84328364eb39dd60ff5b4bace4dd5be0"},
       {"e709d62173a56a460d6064de4f811bffdf580e316c61f6b8effb57641d0812d6", "a8b1aa05ba5e50b10524afae268c9f2f0a2e3dbed903fc176515a96f07dad5bc"}},
      {3, 2147483648.0, 2.7, 0.375,
       {"c00be0d109049e19497111c7483abceed4e766138f6fb6ce6cfeee75390feb47", "118a6745fbcdfdb256e3e11ed3c1d1ac84328364eb39dd60ff5b4bace4dd5be0"},
       {"e709d62173a56a460d6064de4f811bffdf580e316c61f6b8effb57641d0812d6", "a8b1aa05ba5e50b10524afae268c9f2f0a2e3dbed903fc176515a96f07dad5bc"}},
      {16, 1512140165.0, 3, 0.25,
       {"3199a12a4fdcd0aa293ba6469c06ba04e27260431fd240854094453a7e937760", "3edf97a190438b6b05c0cbe6680632b76687a270247378d577dbf55a8ce9db2d"},
       {"a3cca49e77c13bc7bf43c6711b825b96904a0374d2d716d5df37f59ab332d955", "5986d41ae8ba7758c75e6684b0587fc80676a254fa8508ef1d5a89e258e96eac"}},
  }};
  for (const auto& item : cases) {
    const auto width = static_cast<std::size_t>(item.volume);
    const auto height = width * width;
    const noisemaker::glsl::Vec2 tile(0.0f, 0.0f);
    const noisemaker::glsl::Vec2 full(static_cast<float>(width), static_cast<float>(height));
    const auto render = [&]() {
      noisemaker::glsl::Bindings bindings;
      bindings.set_uniform("tileOffset", tile);
      bindings.set_uniform("fullResolution", full);
      bindings.set_uniform("time", item.time);
      bindings.set_uniform("scale", item.scale);
      bindings.set_uniform("seed", item.seed);
      bindings.set_uniform("volumeSize", item.volume);
      bindings.set_uniform("speed", 1.0);
      bindings.set_uniform("OCTAVES", std::int32_t{1});
      bindings.set_uniform("COLOR_MODE", std::int32_t{0});
      bindings.set_uniform("RIDGES", false);
      return noisemaker::run_mrt_pass(
          noisemaker::generated::bind_synth3d_noise3d_precompute(bindings),
          width, height, static_cast<float>(item.time));
    };
    const auto first = render();
    const auto second = render();
    REQUIRE(first.size() == 2U);
    REQUIRE(second.size() == 2U);
    for (std::size_t output = 0; output < 2U; ++output) {
      REQUIRE(hex(sha256(little_endian_float_bytes(first[output]))) == item.f32[output]);
      REQUIRE(hex(sha256(first[output].to_rgba8())) == item.rgba[output]);
      REQUIRE(hex(sha256(little_endian_float_bytes(second[output]))) == item.f32[output]);
      REQUIRE(hex(sha256(second[output].to_rgba8())) == item.rgba[output]);
    }
    REQUIRE(tile[0] == 0.0f);
    REQUIRE(tile[1] == 0.0f);
    REQUIRE(full[0] == static_cast<float>(width));
    REQUIRE(full[1] == static_cast<float>(height));
  }
}

// CPU 9f3bd6a canonical Noise3D variant captures; source/factory hashes
// de04e9370d3e946afea3420ffe7cb10fd4e8395677bf89e3fe0b960ee0048863
// and 32ed506195ba526dde0193af2ca79edc9b4e2052fb34c39711fb064ee907e4df.
TEST(typed_noise3d_runtime_defines_match_authority_mrt) {
  struct Case {
    std::int32_t octaves, color_mode;
    bool ridges;
    std::string_view color_hash, geo_hash;
  };
  const std::array<Case, 12> cases = {{
      {1, 0, false, "53ccf34d0fc83e3400f3c8b1a93bd4f5db8ca17c9fb3e2d2051ff361c5a4e99d", "5c6d84c7032349996eaa8aa844f29b4a3af99e22fbac356e5ae7e5022038768b"},
      {1, 0, true, "402ccdcd242b4d95d186bcbc8b3427790ed0e42e70b6de18a9da6b7470068366", "70ac94e4d507ddb3e48f2d92977d65643b9ed5467638a405dda6ea9698c9524b"},
      {1, 1, false, "225c8989d59eff0042bb81a462f5ded319f4ce1e696a5001aeff5dd93dcf33af", "5c6d84c7032349996eaa8aa844f29b4a3af99e22fbac356e5ae7e5022038768b"},
      {1, 1, true, "bb2055ea9b0d0ce73046f87b36e0e1821079ad687cd31867d8cdafa7252b7e5c", "70ac94e4d507ddb3e48f2d92977d65643b9ed5467638a405dda6ea9698c9524b"},
      {3, 0, false, "4775bff7e099d061cb8b95a66083d40366a9b84516ab13695760bdf9d3715d3f", "5d4316a05ca0e8f17ce6687db597be3f3c0f1e49f46b741c097cfb8de41620bd"},
      {3, 0, true, "a2e72a0b86d9ac8f59bee2fa75f229b629e096c9a9d036b50b7118fb29ece77a", "855bc6f7b80644b0c1288721bf664d6b79fad63856a09fb198106f1cb38b4591"},
      {3, 1, false, "a0a6a5bb2a454670850abc688daad80df8324093abdd61d518b1184709233bc9", "5d4316a05ca0e8f17ce6687db597be3f3c0f1e49f46b741c097cfb8de41620bd"},
      {3, 1, true, "ea3e125a3f5b4f73f4c1e58570851f2f33b7ec769fd69e723ba4045f93b8d9b7", "855bc6f7b80644b0c1288721bf664d6b79fad63856a09fb198106f1cb38b4591"},
      {6, 0, false, "6422bef2357f651b87a41ffcdc60e740061f278527ce7b8c985b956bd401906c", "7877609a612c04bf65509c828a2a447ddd858492eba340dfa1e56167f7cec977"},
      {6, 0, true, "982aaf6ad89e6e8dd4a10c8f98211cc42d377920f75b4d18e4e48c9ba4504ad7", "89822f7dcc3f829d0442276635d81a9895cedc74062d35d66953261d33bd2463"},
      {6, 1, false, "b60c00e233bf84528a28dd9769604f1722138a65877b5c37e3f7849b1c23100f", "7877609a612c04bf65509c828a2a447ddd858492eba340dfa1e56167f7cec977"},
      {6, 1, true, "ded336b612ac2eec30c4383d3fd293497323d5a8500dec6cd058b0f8fcb6b327", "89822f7dcc3f829d0442276635d81a9895cedc74062d35d66953261d33bd2463"},
  }};
  for (const auto& item : cases) {
    noisemaker::glsl::Bindings bindings;
    bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(0.0f, 0.0f));
    bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(3.0f, 9.0f));
    bindings.set_uniform("time", 0.375);
    bindings.set_uniform("scale", 2.7);
    bindings.set_uniform("seed", 42.0);
    bindings.set_uniform("volumeSize", std::int32_t{3});
    bindings.set_uniform("speed", 1.0);
    bindings.set_uniform("OCTAVES", item.octaves);
    bindings.set_uniform("COLOR_MODE", item.color_mode);
    bindings.set_uniform("RIDGES", item.ridges);
    const auto surfaces = noisemaker::run_mrt_pass(
        noisemaker::generated::bind_synth3d_noise3d_precompute(bindings),
        3U, 9U, 0.375f);
    REQUIRE(surfaces.size() == 2U);
    REQUIRE(hex(sha256(little_endian_float_bytes(surfaces[0]))) == item.color_hash);
    REQUIRE(hex(sha256(little_endian_float_bytes(surfaces[1]))) == item.geo_hash);
    for (const std::int32_t invalid : {0, 7}) {
      bindings.set_uniform("OCTAVES", invalid);
      REQUIRE_THROWS_AS(
          noisemaker::generated::bind_synth3d_noise3d_precompute(bindings),
          noisemaker::glsl::KernelBindingError);
    }
    bindings.set_uniform("OCTAVES", item.octaves);
    bindings.set_uniform("COLOR_MODE", std::int32_t{2});
    REQUIRE_THROWS_AS(
        noisemaker::generated::bind_synth3d_noise3d_precompute(bindings),
        noisemaker::glsl::KernelBindingError);
  }
}

// CPU 9f3bd6a Flythrough3D MRT captures from the exact canonical factory.
// Both fractal branches use the same 16-by-256 volume layout and bindings.
TEST(typed_flythrough3d_preserves_authority_mrt_outputs) {
  struct Case { std::int32_t noise_type, seed; };
  const std::array<Case, 2> cases = {{{0, 3}, {1, 11}}};
  const std::array<std::array<std::string_view, 2>, 4> hashes = {{
      {"adef3376fa9a909d1dc1ff7564d83858b449b997f152e0328c762ecf4e4a05b4", "94f9f7b4c9d734be9af5f3fe7a68e9cf7906a33e500f0a33ee2ff78a4b3d8c7b"},
      {"932003ef0e9c720a1c803e1dc19f45c18182fce1fce153df8317beec8432fefb", "15a1d13f6e51975bf378dd4a137768cbbd5ce41e16e70c48fa7f37ebb4b8b231"},
      {"b9a6e017dffc8c8f7f38aaa25878608d8d78cd1ec63bb0efb6d64362b9959030", "f61f623e39ba2e8d42cca47e9d944fff9cbd709169df30647a7fa3fa83bccf92"},
      {"18c9b82004343c0c792990ea8dd7afc2ddd5b708b017462c42618e42ff6ded84", "2b32d86449a16aaeb1e94e5a52fb294ed1cd29d8be460d899bcf9e7f40dbdbae"}}};
  std::size_t capture = 0;
  for (const auto& item : cases) {
    noisemaker::glsl::Bindings bindings;
    bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(0.0f, 0.0f));
    bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(16.0f, 256.0f));
    bindings.set_uniform("time", 0.375);
    bindings.set_uniform("volumeSize", std::int32_t(16));
    bindings.set_uniform("noiseType", item.noise_type);
    bindings.set_uniform("power", 8.0);
    bindings.set_uniform("iterations", std::int32_t(12));
    bindings.set_uniform("bailout", 4.0);
    bindings.set_uniform("speed", 0.2);
    bindings.set_uniform("voiSize", 0.5);
    bindings.set_uniform("seed", static_cast<double>(item.seed));
    const auto surfaces = noisemaker::run_mrt_pass(
        noisemaker::generated::bind_synth3d_flythrough3d_precompute(bindings), 16U, 256U, 0.375f);
    REQUIRE(surfaces.size() == 2U);
    for (const auto& surface : surfaces) {
      const auto float_hash = hex(sha256(little_endian_float_bytes(surface)));
      const auto rgba_hash = hex(sha256(surface.to_rgba8()));
      if (float_hash != hashes[capture][0] || rgba_hash != hashes[capture][1]) {
        throw std::runtime_error("Flythrough3D capture " + std::to_string(capture) +
                                 " float=" + float_hash + " rgba=" + rgba_hash +
                                 " first=" + std::to_string(noisemaker::float_bits_to_uint(surface.data()[0])));
      }
      ++capture;
    }
  }
}

// CPU 9f3bd6a measures both Physical branches without the unused inputTex.
TEST(typed_physical_agent_needs_only_the_three_state_textures) {
  const std::array<std::array<std::string_view, 2>, 6> hashes = {{
      {"6bd212b6fc82c237da31785d2b0fd3f5df656f43773139dba8b28a9c8e0fcac3", "7b81f9241951cdaa4e64a9574d9bd75017ddd74c8ba3a0a6a90f4c60e1a1e120"},
      {"e2f12d2cf4e51f9697483f6b611e570c24dd2e5e1d1d57ad1d3427c7b7b08f26", "c2534ecf83c71e0c5f192eacec428adbc0f3417b3b4847d7cf5fb04777042b6b"},
      {"71aab86faa2c77d3f56e0f1f5e7d20a834e8ad649953420677cce6083fc60b16", "c6cef49f90ad59b7f2267cb6769f2a445064092391c0a666c2651fcb37b93229"},
      {"a21abdbae8268dcb440f1705bc149cff2ab65d892a80974a6742261fc893959c", "a432ddbc5913396b27d3065ddc047599e50cfa89162403b472c8ecc3d1ecf09e"},
      {"ce14ceb7a6d37c52d3a35f0cbd772b73ff144d671beabf1f147942967d330dc8", "304eeff9fa4fa5633a4e121bd60a0eaac1a3e1c8ef1d9edb90e77eb0b4041d65"},
      {"71aab86faa2c77d3f56e0f1f5e7d20a834e8ad649953420677cce6083fc60b16", "c6cef49f90ad59b7f2267cb6769f2a445064092391c0a666c2651fcb37b93229"}}};
  std::size_t capture = 0;
  for (const float alive : {0.0f, 1.0f}) {
    noisemaker::Surface xyz(4U, 3U), vel(4U, 3U), rgba(4U, 3U);
    xyz.clear({0.25f, 0.75f, 0.125f, alive});
    vel.clear({0.05f, 0.025f, 0.01f, 0.375f});
    rgba.clear({0.2f, 0.4f, 0.6f, 1.0f});
    noisemaker::glsl::Bindings bindings;
    bindings.set_uniform("resolution", noisemaker::glsl::Vec2(4.0f, 3.0f));
    bindings.set_uniform("time", 0.25);
    bindings.set_uniform("gravity", 0.2);
    bindings.set_uniform("wind", 0.3);
    bindings.set_uniform("energy", 1.1);
    bindings.set_uniform("drag", 0.05);
    bindings.set_uniform("deviation", 0.2);
    bindings.set_uniform("wander", 0.4);
    bindings.set_texture("xyzTex", xyz);
    bindings.set_texture("velTex", vel);
    bindings.set_texture("rgbaTex", rgba);
    const auto surfaces = noisemaker::run_mrt_pass(
        noisemaker::generated::bind_points_physical_agent(bindings), 4U, 3U, 0.25f);
    REQUIRE(surfaces.size() == 3U);
    for (const auto& surface : surfaces) {
      REQUIRE(hex(sha256(little_endian_float_bytes(surface))) == hashes[capture][0]);
      REQUIRE(hex(sha256(surface.to_rgba8())) == hashes[capture][1]);
      ++capture;
    }
  }
}

// Replay tests/fixtures/palette3d_reference.mjs against CPU 9f3bd6a.
// The OkLab authority has non-finite lanes in three cases. Check their exact
// bytes and counts, as well as every finite RGB/HSV/OkLab and boundary case.
TEST(typed_palette3d_matches_all_authority_palettes) {
  constexpr std::size_t width = 3U, height = 9U;
  noisemaker::Surface input(width, height);
  for (std::size_t i = 0; i < input.data().size(); ++i) {
    input.data()[i] = static_cast<float>(static_cast<double>((i * 17U + 3U) % 101U) / 100.0);
  }
  REQUIRE(hex(sha256(little_endian_float_bytes(input))) == "439a7a7d771020b875eca113b34d308b5a5a534d98103f17b5c3fa702430f01a");
  const std::array<std::array<std::string_view, 2>, 58> hashes = {{
      {"439a7a7d771020b875eca113b34d308b5a5a534d98103f17b5c3fa702430f01a", "2363297bd649b1892d2a5a70f7e713b9fcb17e4d0b7758d0f3e4d51ba7cbc1a1"},
      {"439a7a7d771020b875eca113b34d308b5a5a534d98103f17b5c3fa702430f01a", "2363297bd649b1892d2a5a70f7e713b9fcb17e4d0b7758d0f3e4d51ba7cbc1a1"},
      {"1369a2f7f628a234098afb897ee57b6eb7635af4ce8818aaf9d6b1d652ab6eb9", "475d6ef918c1be2692b61ae490123447f8af7da5efcdc7dfad467278613cd6df"},
      {"2be17400c5d5c37af1718bad3ffc3bd9644a4e888c9978a117ad1cadb77d75b6", "a986a528aefaf9efd36be4dce3568aa3729025d762778fe2fabfe51e9ff45a70"},
      {"dfe0b31905ddbb8e40517ec8f13e386030408e1ad527a05d1ba3d998e83df6ed", "0e505a24759b8fa26db271479b78d3ef82aa0af3c1eacde76d6daca52db2a627"},
      {"8c941f987f34a3e1cd93be2d0dbfa2d613a54f4c2a5c1978de3b1f89fe2fc363", "682594c9130296dde41a6751c81b3e06d7dde4457d6fd4df9224aa2c6241c166"},
      {"7ea1002c114c2cac3b11fd141f848464ff42dcfd2954ca33c615aaed01c5961b", "0c6923db181caf30eda40ad0a1c3a4b72566b5364d39fec8fa71e9ce32905a8c"},
      {"54592bf25580b963caaf8eb978918029c14b5d846fccc1f948bb6799c22a91cd", "bed305a3df8b819baa341372157fbd75c2de5c79384945919cd60d5a96cc4049"},
      {"519f998619324fa96f25530a4070c25bee5ae213d39a0e05f9ab44c1edafe5b6", "b3b8195c506224e55dc4ad2442ced0df986810b23d80b15aa74d02c474c633e2"},
      {"25afbc2621eddf95e853102a33a2f86b6df0a259c7bd2dab338d46e6b58b3c21", "71d97bc22196053dfbcd19428d151efcf185e7c85eed4ec599da16f3f468306f"},
      {"a2bbc7af6755e8da995a81848dd9c95435349cc15f6699ff26ed449a12e0cc6a", "869d07d907a19d0ecf825e673e713046197e9c375bf9f0b54acc12ad38013838"},
      {"151bf63c26dc47dd4cbb74a5ac1e3a02da10047b26e22df41945b90ad152d772", "790836edec6fa4a8fb120d232b9c1fe7add7070a090c03788a5405f93b027d5a"},
      {"9af60dda1c3160869fb2d51584c0b4469e254a7ebeb1b0d04df190fadcc5345c", "c0f88957c7465b01cff68177c1217b1b85fe6b6a693c548b52c0ff262d32b05c"},
      {"5129dcad8cd0844fe63762b09f6cb9a6675ad6b4668d1f653b63832a2f12fe47", "469e0475f2d204e4bfdae31447f14fa647ba2facc53a1912e38ba4325f3a1ec2"},
      {"e3341bf2194851f679a4d83132365e5be96b8c42b1283eb84e98abc1161137bc", "95fbada369e2b30b1c0e314cf270414ce013b3e8e5267beee662f3210358b5ec"},
      {"68eac3b1e6814d1ccdd1416db9572bb032348d209d79616b45cb580a9a6645f6", "1ef4ebedacd34f125ef0e8def29db10af304889f0ded6d58581a686f5c967fd4"},
      {"3ec5cdba8dc4b877f992542c467bd99a57fb1a2f8759c7fc0081e03412512e6e", "10568f461a5f64b6a464a528e3fd930623f750058157512b1afe20f42363b156"},
      {"a750f61691d9ab7af522330895eb1b3e46a1cbcbc8d9001b9ca3a5fa015d4d4a", "dfe5bd2696511b4a596fdcfedf081cd5bcf8bbb0b15fde25559ad76e38e15f8f"},
      {"44ba53832bb73692a83e80d6213296d287c6d63c50c11197373af2518e792aab", "8bbfb06196e8658a0813f427c19cf6053ece5e610ca8b31fc117202a08515ebc"},
      {"f1b0cd71e391ba39f33695b64a53837ea51592341c07a66473a30eae0ca3bdf9", "eac42575d1e08d426de027418bdeeecbca40138846d6ae5e2461f0a5d5466c31"},
      {"409dc817797535ecb16e914e0e6750d8ab4e15f4bfeea7cb1c142c77f2714c35", "beaa01431c6b6263cd08445056ab2c2495b7299b78616b7172ce93dc2062f439"},
      {"f78c5684ac8163065e3b8d040edaebfce97e60ba8936f79b11765105b6305f47", "94a894776462746197f57ab87a781685cdf5832fd364f5269a23c9de7c71f6ed"},
      {"effff57013b85a8ee6c72facd3245b6a7718152939232dd98fedc9ee092fad59", "34c47122d51b71651f3491f1004a923d5df563dedce9b946a2cf345585fd056f"},
      {"a826d90cce755e1c3402cf3be8a60bef1d08ccfb5c377b4f24233f406639158c", "62513e44e7b450ec5c22145e5ebd82b121164159be2a7d61a154ea8214d6b475"},
      {"dbcb6a5b1dd2e579ffebaaa13dc5a2e3e114fd44b8dfd7b24b43dee91d604caf", "b9fb3d3324ae143c4f5d2ad300ecbab1802e813c2b7e2d79df81d5614ec4bfb1"},
      {"a8c76222dcb20f3f4747922f9ff3dc96436f7f58dd0ae4a4e79f8bce8e8c28a7", "d278523e897f82c9f692e74e3587333b064e12969298b57a895b33fa7c2b9219"},
      {"d435aea6cbe9cbf20cc4b135fcb07194cdd348a01a145b260d0e6c657c41d63c", "3396c2896ececcb024a9ea1cd2ec277fe5c54674892a173858a0c056b3f6e73b"},
      {"60fe2078b477a8eb8a8314cc1ce0e657f38160951280b27a30e6e7c4b572f04f", "8535629d22a0ea1660c320ff7559dfa5db4a6b89d23ca691b482707deed7a12a"},
      {"f2c2606eb47726c221fc3a80c4d92f7419d40a0f0ea8960fe9cff837afa056c6", "196b4f77b03bb15192f972efdf84442b7cb22e61277ba8c269fc578de7d532e6"},
      {"758b58e39f78dc0aff44c5e1468bf6ff59376ddf140870097b0becfb03589c57", "dd7a02d949457a194065c6a418fec0ca9b49d9a0c28c4db8e10867aa78233b18"},
      {"46712b4f7db5d370d2eafa57a994e596809e601d2506a50b8653a85170a8457b", "d9534798bc290f62d5bba6ed11be5e5b02b3c5d917b17a0dbf9787ac29b0593d"},
      {"1413a755c3264121f4311644470c8dc027c0c48e66fe234542d2ea1b10410099", "2fc95549774634971335f56cd505a04c7b0cae0336985cec0e82ba2b81116ded"},
      {"c08fa7b97b2ff587224feb05d540b86e42b47710ab47e68adc89429b02715552", "1396ff6f0db7ad9237852be68c26156d6aae6c177dd4236f443603d45f52bfb1"},
      {"b8e8e82d62e8ca601412747b2b918ab9e4a6d7e6d803c0a9fddc8e07c5bc48fc", "6d23d560bee673058d57f0f74d9c9bf8ae1380929f3aa324a412df53b77cf586"},
      {"603bb2224acce078483d6f910c2865cf71d98ab004ab2915c691caf23875365a", "93a98bc330cc9f2d128fbc86cd0f4f54a831fc4743f05aca2db68e53dc75fe75"},
      {"064da20369906e3e9f48dfebcba0287b51487b661552c21f0bf279edff7d11ef", "d330fb3c03bdb191512ee0938aa14d9f59825c94fd5736b09e10f2591fa326d6"},
      {"1b1c0cf76aedbc8503f2275128b31fee2ba17a753c94194f6a2deb82f5fa1243", "0c9f1fe8a9f7772ba324744d98d35ff2d3f4ac63680de6320a9ec6c61acb9d4f"},
      {"2b2171049c2447dec2b079ae7a808d0c1301a5cb7d7148da9e7f57e0172a37b7", "3db1fd592c75d7ba6e7ed349fd872eadf3ebf97c1d2ff4e6334f693fae22d195"},
      {"f29e612f2b908875624b1563459fec4f25deda736e30384fb26bb40ac43efd83", "b9a9b9fa2569891b6da0b3febb6c98631f592dc73b4108faa3fce6663a7670fb"},
      {"0d5322cdce32b68b7ca3605a45819c717d6e8e461e24e41b297f59ceeda84b3a", "9a1f3990738748aaa0c4fcbb9a859b1e2296e3add77c9cac640a574ae365008d"},
      {"983fdf564134e6f1df8b9c49867085fd90407b4a4e8564059f4c476ef7f88ba2", "9781f7844d85176e3904267cff72a4640b6960e4bcbd0073148bb35ac5c7bd8d"},
      {"8f13b0763c9cc72f5c3191aa33124a7ccd063226f2d9534df0408b551970d832", "290801c8b6651a5d3c626e58dec067770fce74e1a030b293daa5c79911509c42"},
      {"b1b9f3c78b0a04ccd271cc472427148467483b4987beaf362788a0c0c9f34942", "13f1dae654edb743dde7e6eed30114ef474185f0757d4506e612b87a02f1635d"},
      {"b1bfb8c58662bd443135f1329c1fea681cfa9cea426627f0cbb47fe5efe56baf", "1a0b84a3cba0a8c603ae72b3c15ea99fb4422555108f49d7bfd792c68abd0e6f"},
      {"4002fc9430d0321ebb1542d3f88a362e1bb4b03bc915b94cbd46ffa4dc6200c9", "3659de411fd2e0a2ec1ce6251196aaeb38385f26874caf4653bdc293ed4be688"},
      {"a9d1a0ed57166ae0bb4218e91498e70d5ed7daaf214275a18801f044da3e8ef7", "549afccf75b11948b255f6012605b15ffe1fb559d30e01f3e781a00046755a6c"},
      {"fc0c7407be36294719fdd5e52291a678fc5cb7e87c694f10dd3f5f03ad945128", "ce2ce4de5127c0cac49fee5131abb3224a055d79d7705febc6f36d60f89857c4"},
      {"f1c38a8cfc793d19d06e0828afa78839f161726f8247b556c9a8c19a14d18bda", "7ff5766de9b6a9918ee9da11a17d000b59a897aa24ecd91edb4dc3e7186a397a"},
      {"068cce246cfa79769147f02c5d393c1cb69bf8d4a4595076ffcb24860be6a393", "2cbaba44b8357a707af52417d1436fccc06de4e085e1e25ed9615d7025716260"},
      {"db39a6c7b3ba5b24579fb46de84e746f1448c5d2264c45484c2f29a049460a69", "b5111ad8c5f69b30054d4480dbae7e2d8602bf9a6deabcc7790686db927a0972"},
      {"18f061b491eff097ebe2134746d811834767b6d2013903c7c7c91c3fb0b2f885", "157d96fa692ea7dbd0d23ced9c81ebc15a29b124c89559b4d786ba002344779b"},
      {"4c4c04ced09d7271533d77b51981881ea02a93b8d583407255677f25064a6368", "79b545708f7f6b06c702d28f71aec32ce43a3b08cbd31db76d5f5a79646fd1d7"},
      {"79b751567fc4daeb57aa5a749091485a49f4f6c1fbaab0e1a3a132628a63da69", "b450ca84510840510b02d17d30af1a1f7402904246abe1b94ab87be470262ee1"},
      {"4c2765ec667ff2a36166115e9977434d304c1a6c33475eab0e3858a224bed3e3", "a396ba57305eb15567d17ea198b46f135fef31529c8d0a6b5a3989e4f52cef76"},
      {"b1d1ec08ba27e349e4e3b3008d24528ca48c9c71792add3ce0951c67a70ddf16", "e8c9a0dc4a2a02bd3fde38fd3afc74c0a56665beef1ea0eb532b0317777abb40"},
      {"6cf29cee9ca10eb61829b1b0bc7d46529b780c8a3485f83267b026bbc0ae5984", "43e99a55444d8e3001a377ac6b28d1e68ff15d82b37df079475d116788074cde"},
      {"f74ebf5b1038d83632168da96a57e8ec05cc518c44f1c435e0a3e5bef1ece616", "932fd50d39af2358ce8b05de3e41ef98c4b44c411801b05c1c8a10848554dd6c"},
      {"439a7a7d771020b875eca113b34d308b5a5a534d98103f17b5c3fa702430f01a", "2363297bd649b1892d2a5a70f7e713b9fcb17e4d0b7758d0f3e4d51ba7cbc1a1"},
  }};
  const std::array<std::size_t, 58> nonfinite = {0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 4U, 0U, 0U, 23U, 0U, 0U, 0U, 0U, 0U, 0U, 19U, 0U, 0U, 0U, 0U, 0U, 0U};
  for (std::int32_t index = -1; index <= 56; ++index) {
    noisemaker::glsl::Bindings bindings;
    bindings.set_uniform("paletteIndex", index);
    bindings.set_uniform("rotation", index % 3 - 1);
    bindings.set_uniform("offset", 13.5);
    bindings.set_uniform("repeat", 1.7);
    bindings.set_uniform("alpha", 0.65);
    bindings.set_uniform("time", 0.375);
    bindings.set_texture("inputTex3d", input);
    const auto surface = noisemaker::run_pass(
        noisemaker::generated::bind_filter3d_palette3d_palette3d(bindings), width, height, 0.375f);
    const auto capture = static_cast<std::size_t>(index + 1);
    const auto float_hash = hex(sha256(little_endian_float_bytes(surface)));
    const auto rgba_hash = hex(sha256(surface.to_rgba8()));
    if (float_hash != hashes[capture][0] || rgba_hash != hashes[capture][1]) {
      throw std::runtime_error("Palette3D index " + std::to_string(index) +
                               " float=" + float_hash + " rgba=" + rgba_hash);
    }
    const auto count = std::count_if(surface.data().begin(), surface.data().end(),
                                    [](float value) { return !std::isfinite(value); });
    REQUIRE(static_cast<std::size_t>(count) == nonfinite[capture]);
    REQUIRE(hex(sha256(little_endian_float_bytes(input))) == "439a7a7d771020b875eca113b34d308b5a5a534d98103f17b5c3fa702430f01a");
  }
}

// CPU 9f3bd6a reference: tests/fixtures/local_vec4_reference.mjs.
TEST(typed_local_vec4_arrays_match_authority) {
  struct Case {
    std::size_t width, height;
    bool temporal, empty;
    std::int32_t smoothing;
    double red, green, blue;
    std::string_view f32, rgba8;
  };
  const std::array<Case, 53> cases = {{
      {4U, 3U, true, false, 0, -2.0, 10.0, -0.625, "d1041bc8f1731c20ce2371478c898daf3dafc2c01958dcc353d1c95f9edfadc0", "964f32a6b02a624b0cb403d6af89f0578ca55b19b57f2f97717f1fe3c845fef5"},
      {4U, 3U, true, false, 0, 0.0, 8.0, 0.375, "f18ac3889d12e6065e66603ea5d963cc3aaeb7c32d1cd2ab829ef89cc6fe148e", "8bb3c465f73457e3c7cfc5d2e6ad37eab593f7fbcdc7780b7908d5764bd8cb77"},
      {4U, 3U, true, false, 0, 0.25, 7.75, 0.5, "11a692ab8ee8e6e73db1edcd3ee27c5358239c26932ab2e6ad81cafb07e1e285", "f4c06e3337ea2491cc1a53827887b661da37e6c8e65a7c30b712011f88aaadd3"},
      {4U, 3U, true, false, 0, 1.0, 7.0, 0.875, "d885195e74da615ceb13b55e6cd4884ff8da7071188ea8a83342aac37917a973", "d2208b3f923c27a4ec04691ed68041df9bf3529b9f43e88abcda1c73ef3e6485"},
      {4U, 3U, true, false, 0, 2.0, 6.0, 1.375, "74a5b0e9c0d39bf2941211a0f46d721dfca10fa128d281dafd5b4e145701d90c", "c380f1da2a9f53fef97dabbaf35b8dd2608984fe7a8edbd661dabf7b997eb599"},
      {4U, 3U, true, false, 0, 3.0, 5.0, 1.875, "9cf54fb119f3ffa4e160e45c1e834c62b6a42035794fef18ca0d5c845e42e2ad", "a8599a0e2e4dc232c4d939c3ae32df6dc7bae2fecd2c15f6bad54077baec3a68"},
      {4U, 3U, true, false, 0, 4.0, 4.0, 2.375, "ef55898c54e21989cb9e41c5730b797a0e59943d5d09607dc7bfb234a49a155e", "e1326daa0ad935b9e5e5af6c6f91d07a05d9ee41e3a4524c0e0aac3b8d09cd00"},
      {4U, 3U, true, false, 0, 5.0, 3.0, 2.875, "b511533af66eda2a9e2e218b0adb282d7a66caa9bc678c3ac3cf57d06593d5ae", "cc9e8365e3e710dfb922cad362d95a8f70b8e83f5a22e2a2d6c44146ed3d12e5"},
      {4U, 3U, true, false, 0, 6.0, 2.0, 3.375, "4f338e1e1210b53f0de239438f113e2221b060c1031d7c3c87766039432c1b94", "d8f519fad2cdcf357113e778e76876039c9bf8590efc0ca71512c32a2b0876ad"},
      {4U, 3U, true, false, 0, 7.0, 1.0, 3.875, "0f17eab94418f5bf8b27a4c24e2ba8495d9141665900578e65f375ad438fa518", "2c2149e69d331bbef34020f7fbd863b353c343a2e5d8b003343b8bdfd618f7bc"},
      {4U, 3U, true, false, 0, 7.75, 0.25, 4.25, "f9c738551f2614da41d6661b5bcaf836028f82e3f639a49763c5257587b5dc18", "327912a05961a2b4fd2900bf80b445e45d2c5f0613885e72c6cfb50b09a36012"},
      {4U, 3U, true, false, 0, 8.0, 0.0, 4.375, "d102ce6deb0aa3a92d8b13a6a9af9dbc056a8b4fe9de79300be51e28845e80d8", "a151691179c20feb9dd0a7ce390820973aa8c4eb9c15f5876929dea6919b35cc"},
      {4U, 3U, true, false, 0, 20.0, -12.0, 10.375, "488f72ae059e14d2b83ddf600aab00a5f2b14495bb78b00678377e4fbb555900", "08468cb006df18e7e558086d2ccc48a8aed01b77876b4100a8c499362d97f146"},
      {4U, 3U, true, true, 0, -2.0, 10.0, -0.625, "a572d308560e48a72d1a6e91e2e41565679dc7633af724e48fa6cd626dbe167c", "7e2a877b43aeb09f1c3f4fb16512a9b44756fdc8fef86ab417d29062849024c9"},
      {4U, 3U, true, true, 0, 0.0, 8.0, 0.375, "9228306a69bba1a924e689db3dbd398698e0a67d9025acdb3c3c66cf13aba9a8", "aad1e2b5fd757cad4aa2ecc62194f2fc7519bbf0e17108a2a5da50cd673468c5"},
      {4U, 3U, true, true, 0, 0.25, 7.75, 0.5, "1737e5b5055f4a17d95d3c8823ae9897f94e769088ec2c5d6c8e7a7e72dfadb6", "9abecbaa845c7c4b418b3417f952f343dc26b84314f3042ccbd77cbfff5071f3"},
      {4U, 3U, true, true, 0, 1.0, 7.0, 0.875, "5428eb6fea3c6e814a86a167af4c1d25b07560688edf6dc7ea3395a7c70e8b51", "7f9d50ea42c039996af28d19fbab558d3c1131f1c3131f142b5f194fde65097d"},
      {4U, 3U, true, true, 0, 2.0, 6.0, 1.375, "9b4a7951c488f11161de13b7a462a979df385c11eb4cb6e1ea4aefac9ede64e0", "fdf24715eea6be035d5bb47fa81b4ab860d543b58a0eaac4e59f923278e6601f"},
      {4U, 3U, true, true, 0, 3.0, 5.0, 1.875, "c014fd658b4ded6e8ae7c965e1aba4a521a5d69ee9459637ba12aaca8cea635d", "9f4198fc961a7e05272387f8990a9efb424aed84400c36e500e7acd0a3c4010f"},
      {4U, 3U, true, true, 0, 4.0, 4.0, 2.375, "50632694ad46d79e70b0e406ba9faa62f267824540828d280be08501749aef51", "43b3469dd91b4083b9773c6940ac7b77cd63feea5480f4121ab26aca82bee03e"},
      {4U, 3U, true, true, 0, 5.0, 3.0, 2.875, "e535f138f9666662d1ef184f53b70cd50b6df38e5035c7b4d3942ad1257ec824", "66bd4b54d5de859420f9c69a8056b853ed524cedc25345dc9cdc8317c7aba9bd"},
      {4U, 3U, true, true, 0, 6.0, 2.0, 3.375, "a181a4ab0336477e635df03667a247c471d2f8eb66babb412da1a7c8507bce76", "304e2e452de6f4445e0942d2d9c2ac30c20af790ec0bdddd950c0ad13d689ceb"},
      {4U, 3U, true, true, 0, 7.0, 1.0, 3.875, "6a3ff30727b8b9b5bb940ef493536bfc8a86efe04526e7a91966020f5f110a52", "05b6ad4a2e396dcb18ecd9f682ee763d370f053ce64ad3198e555e5ba22d0111"},
      {4U, 3U, true, true, 0, 7.75, 0.25, 4.25, "c68f3f9efbeb3ce79d591ac020e70c276fa751b5ebe704a1369a05175ac60b8e", "fa5ba821dfd76c164897baa3cf0a88ff3a0612d602cb1c9bf03f0c08fad84bfa"},
      {4U, 3U, true, true, 0, 8.0, 0.0, 4.375, "79a9c962ebea3962ad3aad47ddb269dfe53502e215e931dd93305986e5f99696", "9f35346e2426edc3a0de274bad2174dfaa4a55fc7b4d959dc27ea93980015824"},
      {4U, 3U, true, true, 0, 20.0, -12.0, 10.375, "873a0bc1dcc70ee25ff265d3e7dea901b6797757e846de715890cd514511f5a6", "2c1c9ac6a52ef030ae901e987f98014a75f651ed0cb1993677022a21aba0c2eb"},
      {13U, 11U, false, false, -1, 0.0, 0.0, 0.0, "d954756d500315986be8ff51c41d1f2e887597ce3290909733bb5382014c8672", "dd108804d4efde0184db42b45fbf30bb0456fdabf880aee253ca1ff7801cdc24"},
      {13U, 11U, false, false, 0, 0.0, 0.0, 0.0, "89bf3ebbb2b3e4f9315d5c7cdf7c4d7078b877f8649fccb53dcb45b1119a776d", "e1b9228c36d72cdf44c12345af680cdb0d540e93e34b743e4d1fcf8338a3c9d9"},
      {13U, 11U, false, false, 1, 0.0, 0.0, 0.0, "d954756d500315986be8ff51c41d1f2e887597ce3290909733bb5382014c8672", "dd108804d4efde0184db42b45fbf30bb0456fdabf880aee253ca1ff7801cdc24"},
      {13U, 11U, false, false, 2, 0.0, 0.0, 0.0, "d5ce7472309d2f4f3abb4abc474582aa57d862603043f82e832e2953e2e86a69", "c7478aaeebadcc4ca6371abcec64acaf0a7bd944cea7ba43107abfa43b741de9"},
      {13U, 11U, false, false, 3, 0.0, 0.0, 0.0, "0f21338d7ca55c1a085f5665479ff690a6713e2b961cccf2c382abc66a9651a3", "00af164bc2055153045c2f0441a791e3fb00b4586c0407e35c8568dc7a73ba3f"},
      {13U, 11U, false, false, 4, 0.0, 0.0, 0.0, "f6c4389f1a4d7e5b964543b4c54cc4ea1fd27fb90d0fceda4a5b7ae561e41673", "86f63df80322b5b1e41e58f73413687f24d0859797d77954acab2be7d34cec67"},
      {13U, 11U, false, false, 5, 0.0, 0.0, 0.0, "438bfd04d2e68d2a7fda649e791e317e8d4872a37da309bc9c0e629510b3aacf", "562aaabcaaf066b36f100cc7bcb87bc99c1b5ff1cc35e950c218e547c99730a3"},
      {13U, 11U, false, false, 6, 0.0, 0.0, 0.0, "aae87cf24562d62a7643f4cde50c10d00acc838e8e23c3a78eeceb24e059ce08", "b878cf8ce102109971570d6624c505574123988a4c3f6a0d35b49b59df78d596"},
      {13U, 11U, false, false, 7, 0.0, 0.0, 0.0, "d954756d500315986be8ff51c41d1f2e887597ce3290909733bb5382014c8672", "dd108804d4efde0184db42b45fbf30bb0456fdabf880aee253ca1ff7801cdc24"},
      {3U, 2U, false, false, -1, 0.0, 0.0, 0.0, "d24b539372990fc6ef3190e82cd0645b80b6c7aafaf4c738f216d5975b018a05", "016631275b9d7f1fc01aed9ccc90b125005d9f847435692aa00e78d05b13cca9"},
      {3U, 2U, false, false, 0, 0.0, 0.0, 0.0, "c68ec85ffc53bc8d18ed7f217a6c689a9673389ebbc9a133ab2207b602a1182c", "f8572dbf4e34cde9579031938167f3179e321bf6e9bfb777aace9b8bc63c4956"},
      {3U, 2U, false, false, 1, 0.0, 0.0, 0.0, "d24b539372990fc6ef3190e82cd0645b80b6c7aafaf4c738f216d5975b018a05", "016631275b9d7f1fc01aed9ccc90b125005d9f847435692aa00e78d05b13cca9"},
      {3U, 2U, false, false, 2, 0.0, 0.0, 0.0, "d5cc8556eaff21081ac761b841ff40b30780b5948bbcc3b84ef03c6f30e7a5f2", "8fd8f369a83a4db03945a6c259d480a87cece45500207dc2df103fce8bb856da"},
      {3U, 2U, false, false, 3, 0.0, 0.0, 0.0, "a2de4b5db08a5aad5fb68c95231a1852dbbd7bbb8122e3cc0a45e6e5102a118f", "b2fdac28bd59d93e7f9f95786fd16d4dae8d20c08a38a641e654c3ab1659c7ab"},
      {3U, 2U, false, false, 4, 0.0, 0.0, 0.0, "a64db4e8a04562f39acfef5633ce4c5f7b19b64a17b836b59287aeab52261453", "0b257502f18df01e60a54854e693bd96497395a4ea64163d47636c328988bc55"},
      {3U, 2U, false, false, 5, 0.0, 0.0, 0.0, "7fc4a9ed2d6d38155a0eda69259991649620861ecb74dd86cd7faa611d759066", "dbd495dd7ace2fd8264ce61bc12b235c25d09bbc244c099c9e665811b3901a9b"},
      {3U, 2U, false, false, 6, 0.0, 0.0, 0.0, "e57eb15e383bc930b343c95e551b3e34c7c39df9c4cc2bcc9b4363bff123cda4", "3c4af1cbfc9e74c9a10bc9f207a2c1cc674c4ea5f727803fbd4b739b026b30c9"},
      {3U, 2U, false, false, 7, 0.0, 0.0, 0.0, "d24b539372990fc6ef3190e82cd0645b80b6c7aafaf4c738f216d5975b018a05", "016631275b9d7f1fc01aed9ccc90b125005d9f847435692aa00e78d05b13cca9"},
      {5U, 3U, false, false, -1, 0.0, 0.0, 0.0, "1e5641939a7fe5a8820756c494832716f6e81d0665713fee6a4e4c9bdacedb47", "bd7f7360ca293e83e1ff6075c477956c79a2f66661e9b9acdb92109d825fe06e"},
      {5U, 3U, false, false, 0, 0.0, 0.0, 0.0, "7ab38275ab8380b745bd01bf4a5ecb9acf627c3103d60e57240b828b1267c6d4", "bd7f7360ca293e83e1ff6075c477956c79a2f66661e9b9acdb92109d825fe06e"},
      {5U, 3U, false, false, 1, 0.0, 0.0, 0.0, "1e5641939a7fe5a8820756c494832716f6e81d0665713fee6a4e4c9bdacedb47", "bd7f7360ca293e83e1ff6075c477956c79a2f66661e9b9acdb92109d825fe06e"},
      {5U, 3U, false, false, 2, 0.0, 0.0, 0.0, "771541bfe5382733959a1b8b0d6770f1121459a42e028a6514ac3f810d9afa8d", "bd7f7360ca293e83e1ff6075c477956c79a2f66661e9b9acdb92109d825fe06e"},
      {5U, 3U, false, false, 3, 0.0, 0.0, 0.0, "f22ad4aff22b3936dcdbdf652f456c22dde32b0da98814600d108a647dda631e", "bd7f7360ca293e83e1ff6075c477956c79a2f66661e9b9acdb92109d825fe06e"},
      {5U, 3U, false, false, 4, 0.0, 0.0, 0.0, "df25bcd37eaa5a929f08d35b0168989ab5e00af374cd3f3b68c10939311df36d", "bd7f7360ca293e83e1ff6075c477956c79a2f66661e9b9acdb92109d825fe06e"},
      {5U, 3U, false, false, 5, 0.0, 0.0, 0.0, "17dc76a53c0835cdc445c1366034b327b38ab56174f12450c419a10f53ee68aa", "f540f81b6fa6134c1157b849c9a5af30249f885db30bbd0a231ffedf0107af03"},
      {5U, 3U, false, false, 6, 0.0, 0.0, 0.0, "857ab004b47baf372dee0a6b596acb6d3acb0c193c3b7e0b9739350f89a987fe", "62c86bbe163b6748362737a43e24a99f943e9da4124122562f36c76b5b84da4a"},
      {5U, 3U, false, false, 7, 0.0, 0.0, 0.0, "1e5641939a7fe5a8820756c494832716f6e81d0665713fee6a4e4c9bdacedb47", "bd7f7360ca293e83e1ff6075c477956c79a2f66661e9b9acdb92109d825fe06e"},
  }};
  auto fill = [](noisemaker::Surface& surface, std::size_t frame, bool empty) {
    for (std::size_t i = 0; i < surface.data().size(); ++i) {
      surface.data()[i] = i % 4U == 3U
          ? ((empty && (i / 4U + frame) % 3U == 0U) ? 0.0f : 1.0f)
          : static_cast<float>(static_cast<double>((i * 17U + frame * 11U + 3U) % 101U) / 100.0);
    }
  };
  std::size_t capture = 0;
  for (const auto& item : cases) {
    noisemaker::glsl::Bindings bindings;
    bindings.set_uniform("resolution", noisemaker::glsl::Vec2(
        static_cast<float>(item.width), static_cast<float>(item.height)));
    std::vector<noisemaker::Surface> textures;
    textures.reserve(9U);
    noisemaker::Surface output(item.width, item.height);
    if (item.temporal) {
      bindings.set_uniform("redDelay", item.red);
      bindings.set_uniform("greenDelay", item.green);
      bindings.set_uniform("blueDelay", item.blue);
      for (std::size_t frame = 0; frame <= 8U; ++frame) {
        textures.emplace_back(4U, 3U);
        fill(textures.back(), frame, frame > 0U && item.empty);
        std::string texture_name = frame == 0U ? "inputTex" : "h";
        if (frame != 0U) texture_name += std::to_string(frame);
        bindings.set_texture(texture_name, textures.back());
      }
      output = noisemaker::run_pass(
          noisemaker::generated::bind_filter_temporalAberration_temporalAberration(bindings), item.width, item.height);
    } else {
      bindings.set_uniform("smoothing", item.smoothing);
      textures.emplace_back(5U, 3U);
      fill(textures.back(), 2U, false);
      bindings.set_texture("canvasTex", textures.back());
      output = noisemaker::run_pass(
          noisemaker::generated::bind_synth_navierStokes_nsSmooth(bindings), item.width, item.height);
    }
    const auto float_hash = hex(sha256(little_endian_float_bytes(output)));
    const auto rgba_hash = hex(sha256(output.to_rgba8()));
    if (float_hash != item.f32 || rgba_hash != item.rgba8) {
      throw std::runtime_error("Local vec4 array capture " + std::to_string(capture) +
                               " float=" + float_hash + " rgba=" + rgba_hash);
    }
    REQUIRE(std::all_of(output.data().begin(), output.data().end(), [](float value) { return std::isfinite(value); }));
    ++capture;
  }
}

// CPU9f3 reference: tests/fixtures/depth_merge_reference.mjs.
TEST(typed_depth_merge_matches_authority_sorted_runs) {
  struct Case { std::size_t width, height, run; std::string_view f32, rgba; };
  const std::array<Case, 22> cases = {{
      {1U, 1U, 1U, "09203f82f606913691c5a5dc9ddef3e00f634842cc2f5584fd0f8dc58368c728", "e3820096cb82366b860b8a4e668453a7aaaf423af03bdf289fa308ea03a79332"},
      {5U, 1U, 1U, "33a876f4e452576182846b2519a790e246628b3c31cc572b6354598dd1be9301", "62fa7fcd8442dfaca80b482623cba3425c4309a3944829ce71ad15b4f848fb76"},
      {5U, 1U, 2U, "ee64a254146c8e05d72ed04916b0679e0524b36ed0ddbf388473e637e09d9570", "49cec0146ea98572242694ef630c20227a6ae28edccf32649c60fd1daa21d618"},
      {5U, 1U, 4U, "0f5681039ac846ce306c876a1871da53b800d34cff0a6d06fd3bc02d07e58e0e", "49cec0146ea98572242694ef630c20227a6ae28edccf32649c60fd1daa21d618"},
      {5U, 1U, 8U, "0f5681039ac846ce306c876a1871da53b800d34cff0a6d06fd3bc02d07e58e0e", "49cec0146ea98572242694ef630c20227a6ae28edccf32649c60fd1daa21d618"},
      {3U, 3U, 1U, "db6691f67e1b8b349f61931568a3981e4c846d248eb3ddcf71a6eee3e56d78c8", "533467ad2626f132cd4f4d347614bbcc3d12092cacc451eb551c6048d42713ac"},
      {3U, 3U, 2U, "03b8aeb3c0a00dd06d6522691e098cc60da7c9b783a67aa471328797a819d45d", "8b173198596317aeac65938ab9688830fe51c560416b751251fdfd7c243938f0"},
      {3U, 3U, 4U, "b045d76f1bdaf5fcdbea52a49bbcfbd2878abafce62aa0ab2053a72549cd004d", "e1920b44d90fc3c35b2f32e7021c4e5b080860060977933563dbd38a524b2aa1"},
      {3U, 3U, 8U, "6ea2ad63fb2b07837c634768bc05f7de9e288ba25e178fb9d2dc1b172863a252", "e11f1f71c67819b04f4c92cd95a95143eb113f04c481dbdbcc492120f66c8a01"},
      {3U, 3U, 16U, "6ea2ad63fb2b07837c634768bc05f7de9e288ba25e178fb9d2dc1b172863a252", "e11f1f71c67819b04f4c92cd95a95143eb113f04c481dbdbcc492120f66c8a01"},
      {4U, 3U, 1U, "22642f7af9ba8bd68a9fedcc7bfba8aad3d1a15e631d570e5f667fa4bdf5b6c7", "63524cb8248c879014c2099c98c85b9cc992529dea997cce2aac9949676f7432"},
      {4U, 3U, 2U, "b583f767ea3e2c4ca71b5999dd7577fb012dd559ec0b83661bec7fe8ad4bbaa5", "4442dae295bf8e6c067bd3693ea9ed81c7087fe5705cc4d1ad36d1b483a1958c"},
      {4U, 3U, 4U, "c85ebea91672a629ecbdb2fd4c4298f65474503481c06dd164fcad9dae49da4e", "a9304a0a51aaa80ca9851797dff15f21a91432675511d5e0c75651a1794b8f74"},
      {4U, 3U, 8U, "b6556574eb1e2abc88aad6e632f84f4bc74cee9859d6d38576daa22c46173f4e", "b8ad0036398a7b1fdd5d2cf36ec456b1bfe6e85ed89c1a9d904ae069acbbcab5"},
      {4U, 3U, 16U, "b6556574eb1e2abc88aad6e632f84f4bc74cee9859d6d38576daa22c46173f4e", "b8ad0036398a7b1fdd5d2cf36ec456b1bfe6e85ed89c1a9d904ae069acbbcab5"},
      {7U, 5U, 1U, "e822cb923f92fd21823c533e4f75613555496c440d6c2a5aefef4bdd893b630a", "04d983e1bb3d5cd4239da55ac0e89f4a1772fb0749fad275c433585ade05eac6"},
      {7U, 5U, 2U, "50d752d0847edcc450fd75de26b7bca9990e91d0ef734e5310db783c012c4534", "ca89e78727980e2fdae40f7b9c1523ef2110d95936aeed217e70b7ee09522331"},
      {7U, 5U, 4U, "4e3ffe35a0654b5cffa65daa4a2a6c45ac1f41c94c8c417ffa06dacbc584342a", "e46e7dbff0c655e9ba1b8a0b10879b1ffd03b8454d626adbf504385e96401ae7"},
      {7U, 5U, 8U, "60abd85df2c9c93b96e6fc01584c206fee0f0c688a54fe92433c5c09930fc65a", "a1cb2544f4575a4bd071cd089c48f55c6a3eccb1968506f13fe48b1e223471c5"},
      {7U, 5U, 16U, "d45e694b393efd202ac8011acfe0724a2c0a1e65a044bb8c7d1b30ae9981b712", "3b466d87f31f92d973e712503824b19c4842e5870e03b9ae95cf53080870256f"},
      {7U, 5U, 32U, "de8cc3ec84337c1a839e86c95707ba46bbbe1610fa5efd9d1d5360ce844633b6", "8016cacbcb00feb964390ccb4a870007cd4de39fc9e7930e60df672266bd518c"},
      {7U, 5U, 64U, "de8cc3ec84337c1a839e86c95707ba46bbbe1610fa5efd9d1d5360ce844633b6", "8016cacbcb00feb964390ccb4a870007cd4de39fc9e7930e60df672266bd518c"},
  }};
  for (const auto& item : cases) {
    const auto count = item.width * item.height;
    std::vector<std::pair<float, float>> records;
    for (std::size_t i = 0; i < count; ++i) {
      records.emplace_back(static_cast<float>(static_cast<int>((i * 7U + 3U) % 11U) - 6), static_cast<float>(i));
    }
    for (std::size_t start = 0; start < count; start += item.run) {
      std::sort(records.begin() + static_cast<std::ptrdiff_t>(start),
                records.begin() + static_cast<std::ptrdiff_t>(std::min(start + item.run, count)));
    }
    noisemaker::Surface input(item.width, item.height);
    for (std::size_t i = 0; i < count; ++i) {
      const auto offset = ((item.height - 1U - i / item.width) * item.width + i % item.width) * 4U;
      input.data()[offset] = records[i].first;
      input.data()[offset + 1U] = records[i].second;
      input.data()[offset + 2U] = 0.0f;
      input.data()[offset + 3U] = 1.0f;
    }
    noisemaker::glsl::Bindings bindings;
    bindings.set_texture("orderTex", input);
    bindings.set_uniform("runLength", static_cast<std::int32_t>(item.run));
    const auto output = noisemaker::run_pass(
        noisemaker::generated::bind_render_pointsBillboardRender_depthMerge(bindings), item.width, item.height);
    REQUIRE(hex(sha256(little_endian_float_bytes(output))) == item.f32);
    REQUIRE(hex(sha256(output.to_rgba8())) == item.rgba);
  }
}

TEST(typed_landscape_matches_authority_volume_mrt) {
  constexpr std::int32_t side = 4;
  constexpr std::size_t width = 7U, height = 5U;
  noisemaker::Surface volume_cache(side, side * side), analytical_geo(side, side * side);
  for (std::int32_t z = 0; z < side; ++z) {
    for (std::int32_t y = 0; y < side; ++y) {
      for (std::int32_t x = 0; x < side; ++x) {
        const auto offset = static_cast<std::size_t>((z * side + y) * side + x) * 4U;
        for (auto* surface : {&volume_cache, &analytical_geo}) {
          surface->data()[offset] = noisemaker::f32(static_cast<double>(x + 1) / 5.0);
          surface->data()[offset + 1U] = noisemaker::f32(static_cast<double>(y + 1) / 5.0);
          surface->data()[offset + 2U] = noisemaker::f32(static_cast<double>(z + 1) / 5.0);
        }
        volume_cache.data()[offset + 3U] = 1.0f;
        analytical_geo.data()[offset + 3U] = (x + y + z) >= 4 ? noisemaker::f32(0.8) : noisemaker::f32(0.1);
      }
    }
  }
  struct Case { std::int32_t view_mode, filtering; std::string_view frag, geo; };
  const std::array<Case, 4> cases = {{{
      1, 0, "ff6ca499d5871ca0a8dc4bd990abdd28ce6425b06d1a16b73f033688f2eeb845",
            "4c82c45d10554c12ee104bdffa015a1fcb8429ef7a4ae905258a6e94819abc5a"},
      {1, 1, "18b882bb672820dc647241b8ba33fb71351a6161b5d592a9f8893fa696560393",
             "640241b79a285dadf6544c89259c13716a2368c9822d1e531624c9349b61dd2a"},
      {2, 0, "37fea4f943bc8ef3d998ea424ad14c988026a32e1667af5aa36858e4a7e093dc",
             "9dc03ceec883d5f0651731cb614b7738da9808f08bab9fab9e3d2d5c1ecd1889"},
      {2, 1, "68a0a39edb47917ad77640ef7a62a29b10c615cc6b874300ef49c069af44a79f",
             "546c57cdd3bf8b84161ba5856096182dff3805f5ac8e7a0bafba228a5dbd7300"}}};
  for (const auto& item : cases) {
    noisemaker::glsl::Bindings bindings;
    bindings.set_uniform("FILTERING", item.filtering);
    bindings.set_uniform("VIEW_MODE", item.view_mode);
    bindings.set_texture("volumeCache", volume_cache);
    bindings.set_texture("analyticalGeo", analytical_geo);
    bindings.set_uniform("resolution", noisemaker::glsl::Vec2(width, height));
    bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(width, height));
    bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(0.0));
    bindings.set_uniform("volumeSize", side);
    bindings.set_uniform("threshold", 0.4);
    bindings.set_uniform("zoom", 1.0);
    bindings.set_uniform("panX", 0.05);
    bindings.set_uniform("panY", -0.03);
    bindings.set_uniform("lightDirection", noisemaker::glsl::DVec3(
        noisemaker::f32(-0.4), noisemaker::f32(0.85), noisemaker::f32(0.6)));
    bindings.set_uniform("ambient", 0.35);
    bindings.set_uniform("diffuseIntensity", 0.85);
    bindings.set_uniform("specularIntensity", 0.12);
    bindings.set_uniform("bgColor", noisemaker::glsl::DVec3(
        noisemaker::f32(0.025), noisemaker::f32(0.045), noisemaker::f32(0.075)));
    bindings.set_uniform("bgAlpha", 1.0);
    bindings.set_uniform("rotateX", 0.3);
    bindings.set_uniform("rotateY", 0.2);
    bindings.set_uniform("rotateZ", 0.1);
    bindings.set_uniform("viewScale", 0.8);
    bindings.set_uniform("posX", 0.0);
    bindings.set_uniform("posY", 0.0);
    bindings.set_uniform("posZ", 0.0);
    bindings.set_uniform("fieldOfView", 60.0);
    const auto outputs = noisemaker::run_mrt_pass(
        noisemaker::generated::bind_render_renderLandscape3d_landscape(bindings), width, height);
    REQUIRE(outputs.size() == 2U);
    REQUIRE(hex(sha256(little_endian_float_bytes(outputs[0]))) == item.frag);
    REQUIRE(hex(sha256(little_endian_float_bytes(outputs[1]))) == item.geo);
  }
}

TEST(typed_halftone_runtime_modes_preserve_cpu_color_arity) {
  constexpr std::size_t width = 8U, height = 8U;
  std::vector<float> data(width * height * 4U);
  for (std::size_t i = 0; i < width * height; ++i) {
    data[4U * i] = static_cast<float>(static_cast<double>(i % 7U + 1U) / 9.0);
    data[4U * i + 1U] = static_cast<float>(static_cast<double>(i % 11U + 1U) / 13.0);
    data[4U * i + 2U] = static_cast<float>(static_cast<double>(i % 13U + 1U) / 15.0);
    data[4U * i + 3U] = static_cast<float>(static_cast<double>(i % 5U + 1U) / 7.0);
  }
  const noisemaker::Surface input(width, height, data);
  struct ArityCase {
    bool ink_alpha, paper_alpha;
    std::array<std::string_view, 4> f32;
    std::array<std::string_view, 4> rgba;
  };
  const std::array<ArityCase, 4> cases = {{
      {false, false,
       {"33dd974b4ac7e959fda9f7dfb17d61294a070cabb622e1474df1f239281af8d4",
        "365de37b0950c9f010eaaa0e387ea67251b082ba189d9a3e267953afae139515",
        "319d9f51b46e2b346f2b9b7f62d60a296125c059d1f62d75de322494934705ad",
        "2eef4014439c0d36c31fa04fbfb633e3da59b15371f72bf7be24dc4371bac401"},
       {"57e9b92289c9852a7bf777c263280b3a81df4b2c9ca7f2b1cb7a2abb91619ebd",
        "088767a2d1b399b6f1e80e67476b47c57e325dcec6f82e388f894110414c1cdc",
        "87acbd77c982406d224ff04c8587998be1de60052fb5a66540071eeddf37ed4f",
        "150ad578c505e948ba392032ae9753cd1feece3780f6b62bf6f0c38883f3c6e9"}},
      {false, true,
       {"33dd974b4ac7e959fda9f7dfb17d61294a070cabb622e1474df1f239281af8d4",
        "365de37b0950c9f010eaaa0e387ea67251b082ba189d9a3e267953afae139515",
        "319d9f51b46e2b346f2b9b7f62d60a296125c059d1f62d75de322494934705ad",
        "2eef4014439c0d36c31fa04fbfb633e3da59b15371f72bf7be24dc4371bac401"},
       {"57e9b92289c9852a7bf777c263280b3a81df4b2c9ca7f2b1cb7a2abb91619ebd",
        "088767a2d1b399b6f1e80e67476b47c57e325dcec6f82e388f894110414c1cdc",
        "87acbd77c982406d224ff04c8587998be1de60052fb5a66540071eeddf37ed4f",
        "150ad578c505e948ba392032ae9753cd1feece3780f6b62bf6f0c38883f3c6e9"}},
      {true, false,
       {"33dd974b4ac7e959fda9f7dfb17d61294a070cabb622e1474df1f239281af8d4",
        "f9519c1043e6972dbcac3a124b7832cff5553c5a0466f1a54db0852dd522bb4f",
        "84f8256d5a7cab749d2ba425dd1668e79b4e166305c603a5a6a1287ee8191c7b",
        "19c498dd86360fd67b3702b9735e3e87426ab4fa46f631855b372885865c48bd"},
       {"57e9b92289c9852a7bf777c263280b3a81df4b2c9ca7f2b1cb7a2abb91619ebd",
        "4626721916f71e92124197f676570b451f194bd4889b93d5c98b4791ea5304e3",
        "2c91d0f2e9b49ea345d4c241b27f55150ca8b7293d5d83e3d9a08e87736f8cb6",
        "b2b4047ceafa6514114e176a05f6c3f5d65f44668901fecbe49c31182f1339e4"}},
      {true, true,
       {"33dd974b4ac7e959fda9f7dfb17d61294a070cabb622e1474df1f239281af8d4",
        "79c535c79c497dd99dcfec38933d71d50f601d8db74e00205abe44f76162d9bd",
        "ba7a4cf2f173ce765df33a3232e2bed8a22b1c87fbdb512e848e5f360c1be016",
        "8b1a5a2044d41dc74e3c7731f1b1d7c1891876798631cfaccf9538729b99c7fa"},
       {"57e9b92289c9852a7bf777c263280b3a81df4b2c9ca7f2b1cb7a2abb91619ebd",
        "5661ef970534edeee9923b653270db2a6bfd3ab06aa6f11cd042fa264d7c0774",
        "0419413b275dd27719de5aea1516417222b48d43184ca360b80cb297187943fd",
        "141e987386c8ca9397f89ef1fa58a199ebbf8c6fbec8ac6a79c1532b2035cf8c"}},
  }};
  for (const auto& item : cases) {
    for (std::int32_t mode : {0, 1}) {
      for (std::int32_t pattern : {0, 1, 2}) {
        noisemaker::glsl::Bindings bindings;
        bindings.set_texture("inputTex", input);
        bindings.set_uniform("MODE", mode);
        bindings.set_uniform("PATTERN", pattern);
        bindings.set_uniform("resolution", noisemaker::glsl::Vec2(8.0f, 8.0f));
        bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(0.0f, 0.0f));
        bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(8.0f, 8.0f));
        bindings.set_uniform("frequency", 6.0);
        bindings.set_uniform("cyanAngle", 108.0);
        bindings.set_uniform("magentaAngle", 162.0);
        bindings.set_uniform("yellowAngle", 90.0);
        bindings.set_uniform("blackAngle", 45.0);
        bindings.set_uniform("monoAngle", 45.0);
        bindings.set_uniform("sharpness", 80.0);
        bindings.set_uniform("inkColor", noisemaker::glsl::DVec3(0.1, 0.2, 0.3));
        bindings.set_uniform("paperColor", noisemaker::glsl::DVec3(0.8, 0.7, 0.6));
        bindings.set_uniform("__cpuColorHasAlpha_inkColor", item.ink_alpha);
        bindings.set_uniform("__cpuColorAlpha_inkColor", 0.25);
        bindings.set_uniform("__cpuColorHasAlpha_paperColor", item.paper_alpha);
        bindings.set_uniform("__cpuColorAlpha_paperColor", 0.75);
        const auto image = noisemaker::run_pass(
            noisemaker::generated::bind_filter_halftone_halftone(bindings), width, height);
        const std::size_t index = mode == 0 ? 0U : static_cast<std::size_t>(pattern + 1);
        REQUIRE(hex(sha256(little_endian_float_bytes(image))) == item.f32[index]);
        REQUIRE(hex(sha256(image.to_rgba8())) == item.rgba[index]);
      }
    }
  }
}

// CPU9f3 reference: tests/fixtures/hatch_reference.mjs.
TEST(typed_hatch_matches_authority_modes_and_color_widths) {
  struct Case { std::size_t width, height; int mode, colors; std::size_t nonfinite; std::string_view f32, rgba; };
  const std::array<Case, 48> cases = {{
      {7U, 5U, 0, 0, 0U, "1b0530324e4b3deca38fcdc29ca437d7939e8d8f90374b3c378e51162df25ff0", "f960de40881139a81fa25a4e3247a03c10fc34095834188b92563b158b2caf74"},
      {7U, 5U, 0, 1, 0U, "1b0530324e4b3deca38fcdc29ca437d7939e8d8f90374b3c378e51162df25ff0", "f960de40881139a81fa25a4e3247a03c10fc34095834188b92563b158b2caf74"},
      {7U, 5U, 0, 2, 0U, "1b0530324e4b3deca38fcdc29ca437d7939e8d8f90374b3c378e51162df25ff0", "f960de40881139a81fa25a4e3247a03c10fc34095834188b92563b158b2caf74"},
      {7U, 5U, 0, 3, 0U, "1b0530324e4b3deca38fcdc29ca437d7939e8d8f90374b3c378e51162df25ff0", "f960de40881139a81fa25a4e3247a03c10fc34095834188b92563b158b2caf74"},
      {7U, 5U, 1, 0, 0U, "d2d9351280d2b71ef9edfc9e9d3e6ee32ab0240a78406fe2420c38d69ef3d4af", "f2e2d8682f01c2334a1168991ffd3c97fc256ece9d805b46c257570e501eba7b"},
      {7U, 5U, 1, 1, 0U, "d2d9351280d2b71ef9edfc9e9d3e6ee32ab0240a78406fe2420c38d69ef3d4af", "f2e2d8682f01c2334a1168991ffd3c97fc256ece9d805b46c257570e501eba7b"},
      {7U, 5U, 1, 2, 0U, "d2d9351280d2b71ef9edfc9e9d3e6ee32ab0240a78406fe2420c38d69ef3d4af", "f2e2d8682f01c2334a1168991ffd3c97fc256ece9d805b46c257570e501eba7b"},
      {7U, 5U, 1, 3, 0U, "d2d9351280d2b71ef9edfc9e9d3e6ee32ab0240a78406fe2420c38d69ef3d4af", "f2e2d8682f01c2334a1168991ffd3c97fc256ece9d805b46c257570e501eba7b"},
      {7U, 5U, 2, 0, 0U, "263285eaef32d85b1f209f9095f0ee41b5aeed9f6b1beb0a8139f7e49047f2e9", "a2443529397d9133eb9a440992fa48eb49defbbebab675351376a7c98bf015b7"},
      {7U, 5U, 2, 1, 0U, "263285eaef32d85b1f209f9095f0ee41b5aeed9f6b1beb0a8139f7e49047f2e9", "a2443529397d9133eb9a440992fa48eb49defbbebab675351376a7c98bf015b7"},
      {7U, 5U, 2, 2, 0U, "263285eaef32d85b1f209f9095f0ee41b5aeed9f6b1beb0a8139f7e49047f2e9", "a2443529397d9133eb9a440992fa48eb49defbbebab675351376a7c98bf015b7"},
      {7U, 5U, 2, 3, 0U, "263285eaef32d85b1f209f9095f0ee41b5aeed9f6b1beb0a8139f7e49047f2e9", "a2443529397d9133eb9a440992fa48eb49defbbebab675351376a7c98bf015b7"},
      {7U, 5U, 3, 0, 0U, "bb28c8141749834b6f997db2dfd989c303667d1e1587548c7db7d5e82ec51b2f", "1eae360aa37593f62c1e4c298fe8df0c39a1b04515af7db34d6fcbb85664791f"},
      {7U, 5U, 3, 1, 0U, "bb28c8141749834b6f997db2dfd989c303667d1e1587548c7db7d5e82ec51b2f", "1eae360aa37593f62c1e4c298fe8df0c39a1b04515af7db34d6fcbb85664791f"},
      {7U, 5U, 3, 2, 0U, "bb28c8141749834b6f997db2dfd989c303667d1e1587548c7db7d5e82ec51b2f", "1eae360aa37593f62c1e4c298fe8df0c39a1b04515af7db34d6fcbb85664791f"},
      {7U, 5U, 3, 3, 0U, "bb28c8141749834b6f997db2dfd989c303667d1e1587548c7db7d5e82ec51b2f", "1eae360aa37593f62c1e4c298fe8df0c39a1b04515af7db34d6fcbb85664791f"},
      {7U, 5U, 4, 0, 0U, "6e32196ddb57ad701de09c19acf61f0c71b659bd06d06533c5cb9f3808ca1ad3", "5eee3c9f52d7c67fbe442e5c313968715fb9a4ce229b99481c570f5fc6db5d96"},
      {7U, 5U, 4, 1, 0U, "6e32196ddb57ad701de09c19acf61f0c71b659bd06d06533c5cb9f3808ca1ad3", "5eee3c9f52d7c67fbe442e5c313968715fb9a4ce229b99481c570f5fc6db5d96"},
      {7U, 5U, 4, 2, 0U, "6e32196ddb57ad701de09c19acf61f0c71b659bd06d06533c5cb9f3808ca1ad3", "5eee3c9f52d7c67fbe442e5c313968715fb9a4ce229b99481c570f5fc6db5d96"},
      {7U, 5U, 4, 3, 0U, "6e32196ddb57ad701de09c19acf61f0c71b659bd06d06533c5cb9f3808ca1ad3", "5eee3c9f52d7c67fbe442e5c313968715fb9a4ce229b99481c570f5fc6db5d96"},
      {7U, 5U, 5, 0, 0U, "0dc607e9c6958ef9361221c51f926685c83602bc51f05e58b9e62076be0bd4d9", "523bcea7c8fa2068b03edeb15acd36dfade4d5835c38c487e8b1980fa87b4ca2"},
      {7U, 5U, 5, 1, 0U, "0dc607e9c6958ef9361221c51f926685c83602bc51f05e58b9e62076be0bd4d9", "523bcea7c8fa2068b03edeb15acd36dfade4d5835c38c487e8b1980fa87b4ca2"},
      {7U, 5U, 5, 2, 0U, "0dc607e9c6958ef9361221c51f926685c83602bc51f05e58b9e62076be0bd4d9", "523bcea7c8fa2068b03edeb15acd36dfade4d5835c38c487e8b1980fa87b4ca2"},
      {7U, 5U, 5, 3, 0U, "0dc607e9c6958ef9361221c51f926685c83602bc51f05e58b9e62076be0bd4d9", "523bcea7c8fa2068b03edeb15acd36dfade4d5835c38c487e8b1980fa87b4ca2"},
      {11U, 3U, 0, 0, 0U, "1483a5fc7f5a199c9b13fb737b76f139a38927ea603e568e06013de2afb10796", "22d9170b82fbc7e0dc19591ffdb500544024e3fd234b81e5fb977b06bf9ac08a"},
      {11U, 3U, 0, 1, 0U, "1483a5fc7f5a199c9b13fb737b76f139a38927ea603e568e06013de2afb10796", "22d9170b82fbc7e0dc19591ffdb500544024e3fd234b81e5fb977b06bf9ac08a"},
      {11U, 3U, 0, 2, 0U, "1483a5fc7f5a199c9b13fb737b76f139a38927ea603e568e06013de2afb10796", "22d9170b82fbc7e0dc19591ffdb500544024e3fd234b81e5fb977b06bf9ac08a"},
      {11U, 3U, 0, 3, 0U, "1483a5fc7f5a199c9b13fb737b76f139a38927ea603e568e06013de2afb10796", "22d9170b82fbc7e0dc19591ffdb500544024e3fd234b81e5fb977b06bf9ac08a"},
      {11U, 3U, 1, 0, 0U, "9545a4a35aff4fcc43bd5ef0af3eac97cf9d82a9ae4ccb5c476945649b994196", "fe9e3497abfba4de7055c1324313f056971263bb49bb7436cdd7e3850a542c28"},
      {11U, 3U, 1, 1, 0U, "9545a4a35aff4fcc43bd5ef0af3eac97cf9d82a9ae4ccb5c476945649b994196", "fe9e3497abfba4de7055c1324313f056971263bb49bb7436cdd7e3850a542c28"},
      {11U, 3U, 1, 2, 0U, "9545a4a35aff4fcc43bd5ef0af3eac97cf9d82a9ae4ccb5c476945649b994196", "fe9e3497abfba4de7055c1324313f056971263bb49bb7436cdd7e3850a542c28"},
      {11U, 3U, 1, 3, 0U, "9545a4a35aff4fcc43bd5ef0af3eac97cf9d82a9ae4ccb5c476945649b994196", "fe9e3497abfba4de7055c1324313f056971263bb49bb7436cdd7e3850a542c28"},
      {11U, 3U, 2, 0, 0U, "c44670ae0aee24ebfd99c76616de2046dd574b2c72784fc9cea3c5e4185b336e", "e4d7da77438cfe2ccc0a628e654220f7cae27be51a1a432148efcf6195d87ebd"},
      {11U, 3U, 2, 1, 0U, "c44670ae0aee24ebfd99c76616de2046dd574b2c72784fc9cea3c5e4185b336e", "e4d7da77438cfe2ccc0a628e654220f7cae27be51a1a432148efcf6195d87ebd"},
      {11U, 3U, 2, 2, 0U, "c44670ae0aee24ebfd99c76616de2046dd574b2c72784fc9cea3c5e4185b336e", "e4d7da77438cfe2ccc0a628e654220f7cae27be51a1a432148efcf6195d87ebd"},
      {11U, 3U, 2, 3, 0U, "c44670ae0aee24ebfd99c76616de2046dd574b2c72784fc9cea3c5e4185b336e", "e4d7da77438cfe2ccc0a628e654220f7cae27be51a1a432148efcf6195d87ebd"},
      {11U, 3U, 3, 0, 0U, "71e2a1b4566bd575937488a1101ebb5810c68870f62b3256d38251cbdc5ad3f1", "e3becfc53f5c224db3baed323e741573ef5e61a22ca02e244239aed3510278f9"},
      {11U, 3U, 3, 1, 0U, "71e2a1b4566bd575937488a1101ebb5810c68870f62b3256d38251cbdc5ad3f1", "e3becfc53f5c224db3baed323e741573ef5e61a22ca02e244239aed3510278f9"},
      {11U, 3U, 3, 2, 0U, "71e2a1b4566bd575937488a1101ebb5810c68870f62b3256d38251cbdc5ad3f1", "e3becfc53f5c224db3baed323e741573ef5e61a22ca02e244239aed3510278f9"},
      {11U, 3U, 3, 3, 0U, "71e2a1b4566bd575937488a1101ebb5810c68870f62b3256d38251cbdc5ad3f1", "e3becfc53f5c224db3baed323e741573ef5e61a22ca02e244239aed3510278f9"},
      {11U, 3U, 4, 0, 0U, "ab750df25aa9475ac4d6af99f070dcde38bce5c40fc6f04e3faf00cc2868b217", "2de224678f3d5b4a5ac7c297d7cde8ed9f13ada2469d8332ba27c19274efc401"},
      {11U, 3U, 4, 1, 0U, "ab750df25aa9475ac4d6af99f070dcde38bce5c40fc6f04e3faf00cc2868b217", "2de224678f3d5b4a5ac7c297d7cde8ed9f13ada2469d8332ba27c19274efc401"},
      {11U, 3U, 4, 2, 0U, "ab750df25aa9475ac4d6af99f070dcde38bce5c40fc6f04e3faf00cc2868b217", "2de224678f3d5b4a5ac7c297d7cde8ed9f13ada2469d8332ba27c19274efc401"},
      {11U, 3U, 4, 3, 0U, "ab750df25aa9475ac4d6af99f070dcde38bce5c40fc6f04e3faf00cc2868b217", "2de224678f3d5b4a5ac7c297d7cde8ed9f13ada2469d8332ba27c19274efc401"},
      {11U, 3U, 5, 0, 0U, "735f4eaa2e0aa5e21ca1c1e2df5785b945885277cfcf359347c8d131d40046a8", "f89afbc6c1e75c7410c21a7cd8ec68da95ed3d96fdd5649183f93d87888f1470"},
      {11U, 3U, 5, 1, 0U, "735f4eaa2e0aa5e21ca1c1e2df5785b945885277cfcf359347c8d131d40046a8", "f89afbc6c1e75c7410c21a7cd8ec68da95ed3d96fdd5649183f93d87888f1470"},
      {11U, 3U, 5, 2, 0U, "735f4eaa2e0aa5e21ca1c1e2df5785b945885277cfcf359347c8d131d40046a8", "f89afbc6c1e75c7410c21a7cd8ec68da95ed3d96fdd5649183f93d87888f1470"},
      {11U, 3U, 5, 3, 0U, "735f4eaa2e0aa5e21ca1c1e2df5785b945885277cfcf359347c8d131d40046a8", "f89afbc6c1e75c7410c21a7cd8ec68da95ed3d96fdd5649183f93d87888f1470"},
  }};
  std::size_t failures = 0;
  for (const auto& item : cases) {
    noisemaker::Surface input(item.width, item.height);
    for (std::size_t i=0; i<input.data().size(); ++i) input.data()[i]=static_cast<float>(static_cast<double>((i*17U+3U)%101U)/100.0);
    noisemaker::glsl::Bindings bindings;
    bindings.set_texture("inputTex", input);
    bindings.set_uniform("MODE", static_cast<std::int32_t>(item.mode));
    bindings.set_uniform("resolution", noisemaker::glsl::Vec2(static_cast<float>(item.width),static_cast<float>(item.height)));
    bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(-3.0f,2.0f));
    bindings.set_uniform("strokeLength", 37.5);
    bindings.set_uniform("direction", static_cast<std::int32_t>(item.mode%4));
    bindings.set_uniform("balance",43.25);
    bindings.set_uniform("pressure",67.75);
    bindings.set_uniform("inkColor", noisemaker::glsl::DVec3(0.073,0.191,0.337));
    bindings.set_uniform("paperColor", noisemaker::glsl::DVec3(0.923,0.817,0.711));
    const auto output=noisemaker::run_pass(noisemaker::generated::bind_filter_hatch_hatch(bindings),item.width,item.height);
    const auto actual=hex(sha256(little_endian_float_bytes(output)));
    const auto rgba=hex(sha256(output.to_rgba8()));
    const auto nonfinite=static_cast<std::size_t>(std::count_if(output.data().begin(),output.data().end(),[](float x){return !std::isfinite(x);}));
    if(actual!=item.f32 || rgba!=item.rgba || nonfinite!=item.nonfinite) {
      std::cerr << "Hatch mismatch " << item.width << 'x' << item.height << " mode=" << item.mode << " colors=" << item.colors << " f32=" << actual << " expected=" << item.f32 << " nonfinite=" << nonfinite << '/' << item.nonfinite << '\n';
      ++failures;
    }
  }
  REQUIRE(failures==0U);
}

TEST(typed_render3d_runtime_defines_match_current_cpu_mrt) {
  struct Case {
    int program;
    int filtering;
    bool invert;
    std::string_view color_hash;
    std::string_view depth_hash;
  };
  // CPU9f3 canonical factories 247 and 248; measured with the same volume
  // atlas, dimensions, and both output attachments.
  const std::array<Case, 8> cases = {{
      {0, 0, false, "a5feb4c4517a0a5fc3d11ebb5e9bc705fd221abb999334849d6fea35181be7a4", "b27355af533604ef912577ab66a8e781a25b360ed26fdd10ffd31ce3abaebfd5"},
      {0, 0, true, "a4de152876a02e7be97fda4bbae97e8968b4f25fb3470fe05a9f502958a3f452", "901db088193ab2460c63fbbf633568a20f8915b3641b39ae7be010f8e2a66340"},
      {0, 1, false, "88e13c8a7ff07ec653c7de01ed2c09b4150d3406ec27a87d66029af6a92ebfdc", "830cfd162d1b00866459682f3558e304b846d6ecb41005b8405ed8eb23fa368d"},
      {0, 1, true, "aad74deb9561a84ba39ebfd8df44ea0384951194cbb059cb5f4b3d3d6d6a889f", "8e09b9eee234c0fe5718a8a46ef2151cf4bea2f55513583b9cd55587d0c65abf"},
      {1, 0, false, "a8853820a417f7a5411e90fa858f12ce365176262f1a1ba71faba9e86387d731", "9c62f8840a1fc9c248c9cfe6e288e0238da341b864d49cb9d411a264f086a647"},
      {1, 0, true, "ed6a94441eb99b49a69f07a118b1ef50790d15cfea6829e70764aead3da964e9", "ce3ca5bf5bc0e3d050e1581df02ec1ae04308cce22eab6ad687c1c47b9d518eb"},
      {1, 1, false, "a8853820a417f7a5411e90fa858f12ce365176262f1a1ba71faba9e86387d731", "9c62f8840a1fc9c248c9cfe6e288e0238da341b864d49cb9d411a264f086a647"},
      {1, 1, true, "a8853820a417f7a5411e90fa858f12ce365176262f1a1ba71faba9e86387d731", "9c62f8840a1fc9c248c9cfe6e288e0238da341b864d49cb9d411a264f086a647"},
  }};
  constexpr std::int32_t n = 8;
  constexpr std::size_t width = 13U;
  constexpr std::size_t height = 11U;
  noisemaker::Surface volume(n, n * n);
  for (std::int32_t z = 0; z < n; ++z) {
    for (std::int32_t y = 0; y < n; ++y) {
      for (std::int32_t x = 0; x < n; ++x) {
        const auto index = static_cast<std::size_t>((z * n + y) * n + x) * 4U;
        volume.data()[index] = noisemaker::f32(static_cast<double>(x + 2*y + 3*z + 1) / (6*n));
        volume.data()[index + 1U] = noisemaker::f32(static_cast<double>(x + 1) / n);
        volume.data()[index + 2U] = noisemaker::f32(static_cast<double>(y + 1) / n);
        volume.data()[index + 3U] = 1.0f;
      }
    }
  }
  for (const auto& item : cases) {
    noisemaker::glsl::Bindings bindings;
    bindings.set_texture("volumeCache", volume);
    bindings.set_uniform("FILTERING", static_cast<std::int32_t>(item.filtering));
    bindings.set_uniform("INVERT", item.invert);
    bindings.set_uniform("resolution", noisemaker::glsl::Vec2(width, height));
    bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(width, height));
    bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(0.0f));
    bindings.set_uniform("time", 0.125);
    bindings.set_uniform("threshold", 0.6);
    bindings.set_uniform("volumeSize", n);
    bindings.set_uniform("orbitSpeed", std::int32_t(1));
    noisemaker::glsl::DMat3 cube_basis;
    for (std::size_t axis = 0; axis < 3U; ++axis) cube_basis[axis][axis] = 1.0;
    bindings.set_uniform("cubeBasis", cube_basis);
    bindings.set_uniform("bgColor", noisemaker::glsl::DVec3(
        noisemaker::f32(0.025), noisemaker::f32(0.045), noisemaker::f32(0.075)));
    bindings.set_uniform("bgAlpha", 0.7);
    const auto kernel = item.program == 0
        ? noisemaker::generated::bind_render_render3d_render3d(bindings)
        : noisemaker::generated::bind_render_renderCubemap3d_renderCubemap3d(bindings);
    const auto outputs = noisemaker::run_mrt_pass(kernel, width, height, 0.125f);
    REQUIRE(outputs.size() == 2U);
    REQUIRE(hex(sha256(little_endian_float_bytes(outputs[0]))) == item.color_hash);
    REQUIRE(hex(sha256(little_endian_float_bytes(outputs[1]))) == item.depth_hash);
  }
}

// CPU9f3 reference: tests/fixtures/flow3d_behavior_reference.mjs.
TEST(typed_flow3d_agent_matches_all_runtime_behaviors) {
  struct Case { int scenario, behavior; std::array<std::array<std::string_view,2>,3> hashes; };
  const std::array<Case,24> cases = {{
      {0, 0, {{{"8a83634f0466f908d08f38bd37eb2f3e9ccef8807201861e3e2b309d45c7cd1d", "a2dc5ff4d4e1541ea2d28d9683d139369a530534dc2667978356229f1bc54bb0"}, {"1ac901e4f1b073abdb9b977c70bf88f830fa360c8951ea4031382d2c9a55850f", "a1f9913ee2e33396d8fee88a4a98c4154fb2d8e4b9ce481fd5ac8ea09c4fecc7"}, {"8ea4dd76789c57ae32c30153758f93e054417a51fdcac7d693b663e612da6162", "781339240328f608a50cb05dbb01a9b7440d5ab7ed237eb727d8b98c7ce72687"}}}},
      {0, 1, {{{"1972da8710d178176d55b0781a0a07127915daa9c0d9dd96895b25dfae4e8612", "b429dd1bacbebf898a75f84a69cf9cc730c2ba03360829cb25ec59e7cd584304"}, {"1ac901e4f1b073abdb9b977c70bf88f830fa360c8951ea4031382d2c9a55850f", "a1f9913ee2e33396d8fee88a4a98c4154fb2d8e4b9ce481fd5ac8ea09c4fecc7"}, {"8ea4dd76789c57ae32c30153758f93e054417a51fdcac7d693b663e612da6162", "781339240328f608a50cb05dbb01a9b7440d5ab7ed237eb727d8b98c7ce72687"}}}},
      {0, 2, {{{"868d6906bda81c937623af20bd5577f739a662ca1d5962c66a0183339ebe2208", "8920762d7a4b4648b8f500db6bf8304d0cd294ae2b0c3ff30388dec939f6c502"}, {"1ac901e4f1b073abdb9b977c70bf88f830fa360c8951ea4031382d2c9a55850f", "a1f9913ee2e33396d8fee88a4a98c4154fb2d8e4b9ce481fd5ac8ea09c4fecc7"}, {"8ea4dd76789c57ae32c30153758f93e054417a51fdcac7d693b663e612da6162", "781339240328f608a50cb05dbb01a9b7440d5ab7ed237eb727d8b98c7ce72687"}}}},
      {0, 3, {{{"48709b7ab80ec03eb517e59f07452481397770959e164f2cc4d7075a0dd3f957", "1cc904d8401cc1498a8d809411676cdb379e043b9a69281a57b89023de500dd0"}, {"1ac901e4f1b073abdb9b977c70bf88f830fa360c8951ea4031382d2c9a55850f", "a1f9913ee2e33396d8fee88a4a98c4154fb2d8e4b9ce481fd5ac8ea09c4fecc7"}, {"8ea4dd76789c57ae32c30153758f93e054417a51fdcac7d693b663e612da6162", "781339240328f608a50cb05dbb01a9b7440d5ab7ed237eb727d8b98c7ce72687"}}}},
      {0, 4, {{{"abb2217d3563510fe605387255fdd62eee94b0b83a6cd2542f19e8e22312d1b9", "49817d9fc541060a87b0f804ca3bf40e446cfca0ec6abb87204dac6936eec709"}, {"1ac901e4f1b073abdb9b977c70bf88f830fa360c8951ea4031382d2c9a55850f", "a1f9913ee2e33396d8fee88a4a98c4154fb2d8e4b9ce481fd5ac8ea09c4fecc7"}, {"8ea4dd76789c57ae32c30153758f93e054417a51fdcac7d693b663e612da6162", "781339240328f608a50cb05dbb01a9b7440d5ab7ed237eb727d8b98c7ce72687"}}}},
      {0, 5, {{{"8b44a7ed10d6ecb64dccc4d6325065e1cf8f4c51811fd4de08f3141b5361bac2", "1cc904d8401cc1498a8d809411676cdb379e043b9a69281a57b89023de500dd0"}, {"1ac901e4f1b073abdb9b977c70bf88f830fa360c8951ea4031382d2c9a55850f", "a1f9913ee2e33396d8fee88a4a98c4154fb2d8e4b9ce481fd5ac8ea09c4fecc7"}, {"8ea4dd76789c57ae32c30153758f93e054417a51fdcac7d693b663e612da6162", "781339240328f608a50cb05dbb01a9b7440d5ab7ed237eb727d8b98c7ce72687"}}}},
      {0, 10, {{{"e22317b49bd9e32a70f655e132e6b6e205de5315d401316b0fa439dd9cd3ff49", "357e270f0b8418cb0e5b657d20bcfddfcae6f6f51af8569dec416fb7c693ca9d"}, {"1ac901e4f1b073abdb9b977c70bf88f830fa360c8951ea4031382d2c9a55850f", "a1f9913ee2e33396d8fee88a4a98c4154fb2d8e4b9ce481fd5ac8ea09c4fecc7"}, {"8ea4dd76789c57ae32c30153758f93e054417a51fdcac7d693b663e612da6162", "781339240328f608a50cb05dbb01a9b7440d5ab7ed237eb727d8b98c7ce72687"}}}},
      {0, 11, {{{"abb2217d3563510fe605387255fdd62eee94b0b83a6cd2542f19e8e22312d1b9", "49817d9fc541060a87b0f804ca3bf40e446cfca0ec6abb87204dac6936eec709"}, {"1ac901e4f1b073abdb9b977c70bf88f830fa360c8951ea4031382d2c9a55850f", "a1f9913ee2e33396d8fee88a4a98c4154fb2d8e4b9ce481fd5ac8ea09c4fecc7"}, {"8ea4dd76789c57ae32c30153758f93e054417a51fdcac7d693b663e612da6162", "781339240328f608a50cb05dbb01a9b7440d5ab7ed237eb727d8b98c7ce72687"}}}},
      {1, 0, {{{"d7c5c16268a633fbf979dba84fdf04b6e31bd489c0aa66194d0baa07b0e76024", "88d67d4ca403985b55c5df6c8f19ebc3c5a65cd085f4628a3ba69195eae09358"}, {"3afe2abfc4084bf1115873e5810bc7073847d73f414df8f350e20f4e09fafeb2", "17f7fd57d2e5cb2741c7e95474eabe0fc9b494e774f5d94991f224828a96015e"}, {"a0a9cde3962208600166b519211890ee4adc7d842036a8601ea07ca7c6fcd64d", "32ef8aaec94959b9f9cfcfbea406d493e9dcb65f02819ced1781d96f717ac9c0"}}}},
      {1, 1, {{{"2481c40a2c3fd9476b4a37bd871eb8439db140ada0edd7ad86952f72db8ea4e5", "952541d53285b4b95c12f25856b4f7ff7c6c57d955949ca18e5278f091e4d47f"}, {"3afe2abfc4084bf1115873e5810bc7073847d73f414df8f350e20f4e09fafeb2", "17f7fd57d2e5cb2741c7e95474eabe0fc9b494e774f5d94991f224828a96015e"}, {"a0a9cde3962208600166b519211890ee4adc7d842036a8601ea07ca7c6fcd64d", "32ef8aaec94959b9f9cfcfbea406d493e9dcb65f02819ced1781d96f717ac9c0"}}}},
      {1, 2, {{{"c63bc04658a53ef5011c517e389a3c97968e0a926890a2bb9b35a6ecc7c0c04a", "4efeb2f84e5e9ede6d1584e3f4536a08b4d93992a88d97b0b7f3317c636f108f"}, {"3afe2abfc4084bf1115873e5810bc7073847d73f414df8f350e20f4e09fafeb2", "17f7fd57d2e5cb2741c7e95474eabe0fc9b494e774f5d94991f224828a96015e"}, {"a0a9cde3962208600166b519211890ee4adc7d842036a8601ea07ca7c6fcd64d", "32ef8aaec94959b9f9cfcfbea406d493e9dcb65f02819ced1781d96f717ac9c0"}}}},
      {1, 3, {{{"5872848fb8225814c82e8385699b29c7caddca4f7bfef175cd943a02a96690da", "76b99424000541ecc62206df0f1b39646de7b5811d335cfa89a54fa7a841f124"}, {"3afe2abfc4084bf1115873e5810bc7073847d73f414df8f350e20f4e09fafeb2", "17f7fd57d2e5cb2741c7e95474eabe0fc9b494e774f5d94991f224828a96015e"}, {"a0a9cde3962208600166b519211890ee4adc7d842036a8601ea07ca7c6fcd64d", "32ef8aaec94959b9f9cfcfbea406d493e9dcb65f02819ced1781d96f717ac9c0"}}}},
      {1, 4, {{{"01d2b2a65eaa6ac630be149a536701b05d43f2f0b30a4779c5df788ce18e8ec6", "22a4f97a8f7e69f15b880a601c180b7a77f2dff4091f0601cd65f20e6383a2ca"}, {"3afe2abfc4084bf1115873e5810bc7073847d73f414df8f350e20f4e09fafeb2", "17f7fd57d2e5cb2741c7e95474eabe0fc9b494e774f5d94991f224828a96015e"}, {"a0a9cde3962208600166b519211890ee4adc7d842036a8601ea07ca7c6fcd64d", "32ef8aaec94959b9f9cfcfbea406d493e9dcb65f02819ced1781d96f717ac9c0"}}}},
      {1, 5, {{{"e05a9096c2aba71a074fa5a545c990f88f7339aee1679e40c0f55044311d69bc", "7e39754df2fc4067a0269694378e331bb406fd0ccb1e2dab795223466121ed64"}, {"3afe2abfc4084bf1115873e5810bc7073847d73f414df8f350e20f4e09fafeb2", "17f7fd57d2e5cb2741c7e95474eabe0fc9b494e774f5d94991f224828a96015e"}, {"a0a9cde3962208600166b519211890ee4adc7d842036a8601ea07ca7c6fcd64d", "32ef8aaec94959b9f9cfcfbea406d493e9dcb65f02819ced1781d96f717ac9c0"}}}},
      {1, 10, {{{"69e09317bf34469773c184f5c9be158ea469643269987f4998abe33263e2c524", "b2decde58a2c8c199df5d597f701810adb0d70f4dc8dcd1efe209ee8a8d63bce"}, {"3afe2abfc4084bf1115873e5810bc7073847d73f414df8f350e20f4e09fafeb2", "17f7fd57d2e5cb2741c7e95474eabe0fc9b494e774f5d94991f224828a96015e"}, {"a0a9cde3962208600166b519211890ee4adc7d842036a8601ea07ca7c6fcd64d", "32ef8aaec94959b9f9cfcfbea406d493e9dcb65f02819ced1781d96f717ac9c0"}}}},
      {1, 11, {{{"01d2b2a65eaa6ac630be149a536701b05d43f2f0b30a4779c5df788ce18e8ec6", "22a4f97a8f7e69f15b880a601c180b7a77f2dff4091f0601cd65f20e6383a2ca"}, {"3afe2abfc4084bf1115873e5810bc7073847d73f414df8f350e20f4e09fafeb2", "17f7fd57d2e5cb2741c7e95474eabe0fc9b494e774f5d94991f224828a96015e"}, {"a0a9cde3962208600166b519211890ee4adc7d842036a8601ea07ca7c6fcd64d", "32ef8aaec94959b9f9cfcfbea406d493e9dcb65f02819ced1781d96f717ac9c0"}}}},
      {2, 0, {{{"92d961d860b78835670d46f2a69b90119da80c227c3097d40ad246ddaa146eab", "a49d55d0ae4eb896116c8f3e44204cbf72855a8b7ea3294fae8df13ae55918cd"}, {"730ae87999dbfbf43e1bfdf29715bf53f469732d8db76fb52162c86c3b4a108e", "162eb88aa96da8dfb089ec02a98534230fcde72ef5431c3f580a2cea66cc37eb"}, {"5443419c7a02b6a0365daaef5e6f8a93c5396f970df3b0964e019a4faf1a8d11", "431e72cf3cde7cc2d277e122d74ae99f1bb213cdee686551588809ddded390ff"}}}},
      {2, 1, {{{"5bed4484549259f3145eb6c15f1bdd44f5281d8d4fb3def69ca532b76a90b56d", "7330244d0014a0991b6a96b1a4356901b01e7a4d20da449e4da4ab07f3bbefcc"}, {"730ae87999dbfbf43e1bfdf29715bf53f469732d8db76fb52162c86c3b4a108e", "162eb88aa96da8dfb089ec02a98534230fcde72ef5431c3f580a2cea66cc37eb"}, {"5443419c7a02b6a0365daaef5e6f8a93c5396f970df3b0964e019a4faf1a8d11", "431e72cf3cde7cc2d277e122d74ae99f1bb213cdee686551588809ddded390ff"}}}},
      {2, 2, {{{"2dee9491488a360182a980ecb7a164cdefde7dd7e894070462db0f35efea39a7", "ba6393af80da557ff63e2105081c5e18604f0388b81da50fde05126ab4f2b064"}, {"730ae87999dbfbf43e1bfdf29715bf53f469732d8db76fb52162c86c3b4a108e", "162eb88aa96da8dfb089ec02a98534230fcde72ef5431c3f580a2cea66cc37eb"}, {"5443419c7a02b6a0365daaef5e6f8a93c5396f970df3b0964e019a4faf1a8d11", "431e72cf3cde7cc2d277e122d74ae99f1bb213cdee686551588809ddded390ff"}}}},
      {2, 3, {{{"2948fde295c4014945af4cce2591efb0e2d57911e0673e3e7a660efee6e9c881", "7a0b0795ef9a3ea690f11202f255004732fa0188a25e9a17780e09f57cbe7190"}, {"730ae87999dbfbf43e1bfdf29715bf53f469732d8db76fb52162c86c3b4a108e", "162eb88aa96da8dfb089ec02a98534230fcde72ef5431c3f580a2cea66cc37eb"}, {"5443419c7a02b6a0365daaef5e6f8a93c5396f970df3b0964e019a4faf1a8d11", "431e72cf3cde7cc2d277e122d74ae99f1bb213cdee686551588809ddded390ff"}}}},
      {2, 4, {{{"f8ba84faaccad580cd515735a3c5e2b92ebd92ee6e3d773fb441e5d97055bde2", "24dcf64e7e31a8b3c46f147032fe89ceda48773410785651010a79d865b9c962"}, {"730ae87999dbfbf43e1bfdf29715bf53f469732d8db76fb52162c86c3b4a108e", "162eb88aa96da8dfb089ec02a98534230fcde72ef5431c3f580a2cea66cc37eb"}, {"5443419c7a02b6a0365daaef5e6f8a93c5396f970df3b0964e019a4faf1a8d11", "431e72cf3cde7cc2d277e122d74ae99f1bb213cdee686551588809ddded390ff"}}}},
      {2, 5, {{{"99218a2b315206fe385f1f2daf97a04fee5470801e0a0e56bf5bff3d9cd36dac", "7330244d0014a0991b6a96b1a4356901b01e7a4d20da449e4da4ab07f3bbefcc"}, {"730ae87999dbfbf43e1bfdf29715bf53f469732d8db76fb52162c86c3b4a108e", "162eb88aa96da8dfb089ec02a98534230fcde72ef5431c3f580a2cea66cc37eb"}, {"5443419c7a02b6a0365daaef5e6f8a93c5396f970df3b0964e019a4faf1a8d11", "431e72cf3cde7cc2d277e122d74ae99f1bb213cdee686551588809ddded390ff"}}}},
      {2, 10, {{{"d84cceeca745ae14b166c1b437553ca202e8be55dcdb1136723881e9cc67a0c4", "d629fe7285d7c1e5ed2ad06992404756bf94f791f77e273598651ad9c7efca52"}, {"730ae87999dbfbf43e1bfdf29715bf53f469732d8db76fb52162c86c3b4a108e", "162eb88aa96da8dfb089ec02a98534230fcde72ef5431c3f580a2cea66cc37eb"}, {"5443419c7a02b6a0365daaef5e6f8a93c5396f970df3b0964e019a4faf1a8d11", "431e72cf3cde7cc2d277e122d74ae99f1bb213cdee686551588809ddded390ff"}}}},
      {2, 11, {{{"f8ba84faaccad580cd515735a3c5e2b92ebd92ee6e3d773fb441e5d97055bde2", "24dcf64e7e31a8b3c46f147032fe89ceda48773410785651010a79d865b9c962"}, {"730ae87999dbfbf43e1bfdf29715bf53f469732d8db76fb52162c86c3b4a108e", "162eb88aa96da8dfb089ec02a98534230fcde72ef5431c3f580a2cea66cc37eb"}, {"5443419c7a02b6a0365daaef5e6f8a93c5396f970df3b0964e019a4faf1a8d11", "431e72cf3cde7cc2d277e122d74ae99f1bb213cdee686551588809ddded390ff"}}}},
  }};
  std::size_t failures=0;
  for(const auto& item:cases) {
    noisemaker::Surface state1(2U,2U),state2(2U,2U),state3(2U,2U),mixer(4U,16U);
    for(std::size_t i=0;i<4U;++i) {
      const std::array<float,4> a={static_cast<float>(static_cast<double>(i)*0.5+0.25),1.5f,2.25f,static_cast<float>(static_cast<double>(i)*0.2+0.1)};
      const std::array<float,4> b={0.2f,0.4f,0.6f,static_cast<float>(i)};
      const std::array<float,4> c={item.scenario==2?3.0f:0.2f,item.scenario==0?0.0f:1.0f,-0.15f,0.0f};
      for(std::size_t j=0;j<4U;++j){state1.data()[4U*i+j]=a[j];state2.data()[4U*i+j]=b[j];state3.data()[4U*i+j]=c[j];}
    }
    for(std::size_t i=0;i<mixer.data().size();++i)mixer.data()[i]=static_cast<float>(static_cast<double>((i*17U+3U)%101U)/100.0);
    noisemaker::glsl::Bindings bindings;
    bindings.set_texture("stateTex1",state1);bindings.set_texture("stateTex2",state2);
    bindings.set_texture("stateTex3",state3);bindings.set_texture("mixerTex",mixer);
    bindings.set_uniform("BEHAVIOR",static_cast<std::int32_t>(item.behavior));
    bindings.set_uniform("volumeSize",std::int32_t(4));bindings.set_uniform("stride",1.25);
    bindings.set_uniform("strideDeviation",0.2);bindings.set_uniform("kink",1.1);
    bindings.set_uniform("time",0.375);bindings.set_uniform("lifetime",1.25);bindings.set_uniform("density",100.0);
    const auto outputs=noisemaker::run_mrt_pass(noisemaker::generated::bind_filter3d_flow3d_agent(bindings),2U,2U,0.375f);
    REQUIRE(outputs.size()==3U);
    for(std::size_t j=0;j<3U;++j) {
      const auto f32=hex(sha256(little_endian_float_bytes(outputs[j])));
      const auto rgba=hex(sha256(outputs[j].to_rgba8()));
      if(f32!=item.hashes[j][0] || rgba!=item.hashes[j][1]) {
        std::cerr << "Flow3D mismatch scenario=" << item.scenario << " behavior=" << item.behavior << " output=" << j << " f32=" << f32 << " expected=" << item.hashes[j][0] << '\n';++failures;
      }
    }
  }
  REQUIRE(failures==0U);
}

TEST(perlin_runtime_current_authority) {
 struct Case {std::size_t width,height;int dimensions,warp,octaves,color;double aspect;std::string_view f32,rgba;};
 const std::array<Case,32> cases={{
{7U, 5U, 2, 0, 1, 0, 1.399999976158142, "4dfc6678bc6bf5121d31107e868cf43c3a3467bd99bc525009da0e3fce489c1c", "f6dbd220dc51bb0b877a9f785bbd84722028219fd6aa4a155da005e6a90ed564"},
{7U, 5U, 2, 0, 1, 1, 1.399999976158142, "bea5e12ef5824ed51d9cbd45776c523b8e06d784ff1af81161cc5d70ec765b8e", "88357d6135ea8ff39a4e928ccc6faff1baf080cd77e5593f026081e71fc5a412"},
{7U, 5U, 2, 0, 6, 0, 1.399999976158142, "45791da7d04d7a92cafc84476e5be8d237b0bdb92d5035d24baa7abdec0c7564", "985f3bc02b1226cf374709364a1e1666d83d2689aab6ff0e0ddf2ccdaa42ded4"},
{7U, 5U, 2, 0, 6, 1, 1.399999976158142, "c4a0f9998d5adae982fb38e8a11e3c906fcbf4c27745ee316271c1b0a4120ffd", "f53986bd342aa69ffd7f97412bfb73dbc101110a07206529c08363c869973f0a"},
{7U, 5U, 2, 2, 1, 0, 1.399999976158142, "10803aeebf903fc1ef1303c934a19cbff086923e413c719d7b5dee739fab731e", "c0a2d2c7a1f819f3c20d0d0aef78ae9d07ad362f1977886186e82018c84bd961"},
{7U, 5U, 2, 2, 1, 1, 1.399999976158142, "0fc52524ad4d5dbd3fd44d675353f072dc46e3f806cc554ce64293460f350179", "6644916cadeea7fbb39541e6d9192fa1535fb7194de200a53ed8253c8a95e5ca"},
{7U, 5U, 2, 2, 6, 0, 1.399999976158142, "f3d93d20961a2390f5b74cb008a007b4f0f04b2e1a09d88a4eedcc5ca2cb2b7f", "9d7fdce942abd2bd946f705cdadda1cd28b7052cc3be4e7c35e14c1e2fd0ab50"},
{7U, 5U, 2, 2, 6, 1, 1.399999976158142, "22d9c3aac52f255a52688b74e9c48c18c0ceb7ab045cebbec968562518385ffa", "54b312abe446c05df741286cc7a83564c9fbfd1c762246485e8b34e4edeb2295"},
{7U, 5U, 3, 0, 1, 0, 1.399999976158142, "82485a9041d441ba04984219578154365d418ce0143abb9e55d3a8d371cf45c7", "033cc63f4076c2ac0058087ab6dc4a73d8332b2dfcdb79e69fd5aa14366e99fe"},
{7U, 5U, 3, 0, 1, 1, 1.399999976158142, "eb24ccf83803580eab74ed7051bd1407d505b5c8913ff91e15d2182dc63982cb", "d52debad1c5956152d6b26c35b022aef01523549ad36fc5c4821161e7ff5ecef"},
{7U, 5U, 3, 0, 6, 0, 1.399999976158142, "abbc54dbbe54ef494accaa38642105a99c8ec6ff6e69036a8b38fa9325d29161", "0fdcaaa9757e2a86fd31c825226a4408e073d4413630af6f6138ac23d729a637"},
{7U, 5U, 3, 0, 6, 1, 1.399999976158142, "f756d2ab8b0c90f18832332b3cadda0c417cf672e040f577e266ad9b6e9a63d5", "6df5c3cc01128e03151aa1ed6bb6fde6702e45fe05cd63515c075404be9dd8d4"},
{7U, 5U, 3, 2, 1, 0, 1.399999976158142, "290aacb857a9a2cdcb5eaf538ab25e57febc66ed86523d1e6c4621257467e0ae", "f1555a2f331dcf13679044685f2aebcc0c9a8e608a009edc82a499d86e233f9e"},
{7U, 5U, 3, 2, 1, 1, 1.399999976158142, "23e22a4a131d0629cdb8260c867e30ed62c7b5addf2b5d474c93262dd7672cab", "55774f0688d43ddb8d0f3de4d48773ef4e18eafe94a12f25fedbf61e2cacb685"},
{7U, 5U, 3, 2, 6, 0, 1.399999976158142, "d32732fe16d8e8ef0062922b04a95b3ebe94275b119586f11e3e9a2f4ec6cbb2", "00c6396bee78c153a86a52676305a1a0e71e853b54507c99a4ea17aba7df5866"},
{7U, 5U, 3, 2, 6, 1, 1.399999976158142, "fd8ae2551f65f42e84928c64ca9a01bf418551eaeebddb076aa535b6f1d12a61", "9687af235b1cdc4f7b96d28395c60b30c84ccb1ad99286af87e810585d2800f3"},
{11U, 3U, 2, 0, 1, 0, 3.6666667461395264, "870046120376c1de6ba7383511adab72e81f4a4bd498fcdffc4f6303aba712da", "073f1480c5e9e029ff7cb9177443c022454e98a4bd50fbf96c5b2e8f0fa77fce"},
{11U, 3U, 2, 0, 1, 1, 3.6666667461395264, "9e13a73d179e2505b840347d4dc202b6331bf28cae5859b47509170eb039db74", "490e040314d234e62927ee4a4e34e63182fcb3430ae0d42c8e2c0e2e70d8cc7e"},
{11U, 3U, 2, 0, 6, 0, 3.6666667461395264, "6d3b0a7ee8a44471834a24cf10ba21df9bc0bc9078d23a52f7de6559aab926a5", "a995e8a0bb84d5bcb76802c6cedf47db07d2b176fe77d365adbb76781969b1be"},
{11U, 3U, 2, 0, 6, 1, 3.6666667461395264, "8058fbb24824c521d8345ff1c65221ba8f930e8c05b9a17deaedc47fefb2aeb8", "0c2da877f345fc980b025a2b5da1dfd1584e5b27fd3a8a7df8d239138709fded"},
{11U, 3U, 2, 2, 1, 0, 3.6666667461395264, "0bdf8e6fe174c28d6da0f0eccf0568c6c0f5d9134df0179ea3b72b372e721504", "27028dacc3c32d5be2337607cbabc9ad9c0d9912fa96274d5f88d58d348227ec"},
{11U, 3U, 2, 2, 1, 1, 3.6666667461395264, "7ed6cd547d8e817b3c1ab9781bad0937294b15b07c2b15ff64713cefb2d32b51", "a9f6e9de9aeff6891fd3c07704a7eaab532ccb4eb8f11d529eeb421de7168a25"},
{11U, 3U, 2, 2, 6, 0, 3.6666667461395264, "0044da1b75094ce6c1938791137cba193130c0f2c27c0e4a4100a8d5b312dad5", "cd29e404638667658dbb780c4fb7a938370f75e27fde7bec5ecca841a35fd67a"},
{11U, 3U, 2, 2, 6, 1, 3.6666667461395264, "33e27fad79b138c3ba50952b35e03b72a8ee4b72bcfd3fbd608470e3ad2b7794", "da88af1649c4d1c17b982989800a28679b6499bc7986f6e0dc83480c415a1369"},
{11U, 3U, 3, 0, 1, 0, 3.6666667461395264, "26cf2b9f561efb74a3482fdc792b7705677f6b677e9eb0fa68f9447f98aaa9fa", "753402930dd4bc4445cf3d1effaeef60852068365eb919598d79e1ff1b970524"},
{11U, 3U, 3, 0, 1, 1, 3.6666667461395264, "d352a92d6d42e4eb77e472392e95013def97ca066ce7d0a4ee5b359b9fa1a143", "1f2b4ebc02bc60c9aa0e81b432a1191a1908268f5156d494408c8789c0356460"},
{11U, 3U, 3, 0, 6, 0, 3.6666667461395264, "a730a557159a4c2eb83b19648cf2d0cc6d38d2c76c90c42c05327632404ecd31", "1abd7996a37a57f23f92460f739e37dc5afe2846893fa8449cc28a3bba265510"},
{11U, 3U, 3, 0, 6, 1, 3.6666667461395264, "48e0dc7b34f2751149aa7b53008db9c5a5ba107eff03db491456d83139b2e385", "b6ba206c90dbf41644ad9fd7b409e8b4ec2d8ef3c2ab8ca5d9f4f9fe17c0255a"},
{11U, 3U, 3, 2, 1, 0, 3.6666667461395264, "54faa5a9404b5c05b17eff9a0648171e6a06126f8568421f99793d9ccf6473a5", "8a7ca688c11fba6cf1ed8f3eccf4f5d2e85c5bc41a9d8ffa26670430e45f0ab8"},
{11U, 3U, 3, 2, 1, 1, 3.6666667461395264, "d91083093294a4234d218de87d78ab87ed545da4f0ce05f50aa8bb0d3c04956e", "480e2e56d6b0b3f79cd12b969acc6babbe92384aab96bd8fec633f1599c22e96"},
{11U, 3U, 3, 2, 6, 0, 3.6666667461395264, "34fea1865824449584c66716e8abfe5147b14c3dca92dcac0086dd1b8f6ce5c7", "a46d8a3bcd3e0f549c5fd95e2862c65f42a4c7420c43db6d3dcbd790ead8d6fd"},
{11U, 3U, 3, 2, 6, 1, 3.6666667461395264, "9a826e6c1644d9b979d6c426d1f0825bb91dbec62ffb09ee274147525b6a76b2", "1116f8db7a49321e2431f027be1b78e6dc70dafbf052a6e69425b49239ce7968"},
 }};
 std::size_t failures=0;
 for(const auto& c:cases){
  noisemaker::glsl::Bindings b;
  b.set_uniform("resolution",noisemaker::glsl::Vec2(c.width,c.height));
  b.set_uniform("fullResolution",noisemaker::glsl::Vec2(c.width+6,c.height+4));
  b.set_uniform("tileOffset",noisemaker::glsl::Vec2(-3.0f,2.0f));
  b.set_uniform("DIMENSIONS",std::int32_t(c.dimensions));
  b.set_uniform("aspect",c.aspect);
  b.set_uniform("time",.375);b.set_uniform("scale",25.5);b.set_uniform("seed",std::int32_t(17));
  b.set_uniform("octaves",std::int32_t(c.octaves));b.set_uniform("colorMode",std::int32_t(c.color));
  b.set_uniform("ridges",std::int32_t(c.warp?1:0));b.set_uniform("warpIterations",std::int32_t(c.warp));
  b.set_uniform("warpScale",37.25);b.set_uniform("warpIntensity",62.5);b.set_uniform("speed",1.75);
  const auto out=noisemaker::run_pass(noisemaker::generated::bind_synth_perlin_perlin(b),c.width,c.height);
  const auto f32=hex(sha256(little_endian_float_bytes(out))),rgba=hex(sha256(out.to_rgba8()));
  if(f32!=c.f32 || rgba!=c.rgba){++failures;std::cerr<<"FAIL "<<c.width<<"x"<<c.height<<" dim="<<c.dimensions<<" warp="<<c.warp<<" oct="<<c.octaves<<" color="<<c.color<<" f32="<<f32<<" expected="<<c.f32<<" rgba="<<rgba<<" expected="<<c.rgba<<"\n";}
 }
 REQUIRE(failures==0);
}

TEST(runtime_lowpoly_matches_cpu) {
  constexpr std::size_t width=7U, height=5U;
  std::vector<float> data(width*height*4U);
  for (std::size_t y=0; y<height; ++y) for (std::size_t x=0; x<width; ++x) {
    const auto i=(y*width+x)*4U;
    data[i]=static_cast<float>(static_cast<double>((37*x+17*y+11)%127+1)/129.0);
    data[i+1U]=static_cast<float>(static_cast<double>((19*x+43*y+7)%113+2)/117.0);
    data[i+2U]=static_cast<float>(static_cast<double>((61*x+29*y+3)%109+3)/115.0);
    data[i+3U]=static_cast<float>(static_cast<double>((7*x+5*y+2)%23+8)/31.0);
  }
  const noisemaker::Surface input(width,height,data);
  struct Case { int border, light, mode; std::string_view f32, rgba; };
  const std::array<Case,7> cases={{
      {0, 0, 0, "d7ce5f86fa1ebc1b491105172eb46457e43dd3d1ecf20f48ebe876310eebe1f8", "1811158a2848eab6855b50706da29d025d0b9ae34732c4c89f6796903333edf9"},
      {1, 0, 1, "261869165dc8e2f5727315bc6b3fe68b075c3345eb15c97db98738a01b576fac", "7544de57779d31cb47b87e17f663f75684ec59d5c59cface1ac1ed8de591a756"},
      {100, 0, 2, "91edf51a92025572671d174d96cf5782339f5b8f1debc1d576068ea988979181", "8df6643664a284ee130a65283bbe6345b3c37c024a1af30891982039ed16aabd"},
      {0, 1, 3, "784126976b5a65ede5422947cf7ef4ff0270394b6ecdcc9b87fe384a61dbf760", "35068faa5e953f6a17cd9d9d724f88c7a7f5672e11d972dafd1695b9a1d0dd5f"},
      {0, 100, 0, "aee82eb3090877c6e485dd5b1ef3ab50930b2472b43012876b9f01c0a300e671", "20f679a82428d6ff8b08361f02760aa2c4789c6400e70998b5c39ccd2e97a291"},
      {33, 67, 1, "e00e12e9f011ba86a5eba8594c04424a293b2b442c911fdbd3449495f314528e", "294127de546701c158e1da38462416e8f5eb35bebdd5bbe329896ddc947a4d74"},
      {100, 100, 3, "ac109bcb8bcc43692b8c0074133979afcff48bdca071c896c19f73d9229dedc3", "60cc2a21a3cacdaab57a199e48c35d6aabd6d6a1cc1d6771b3320d7fcc83a7e6"},
  }};
  for (const auto& item:cases) {
    noisemaker::glsl::Bindings bindings;
    bindings.set_texture("inputTex",input);
    bindings.set_uniform("tileOffset",noisemaker::glsl::Vec2(2.0f,1.0f));
    bindings.set_uniform("fullResolution",noisemaker::glsl::Vec2(11.0f,9.0f));
    bindings.set_uniform("LP_BORDER",std::int32_t{item.border});
    bindings.set_uniform("LP_LIGHT",std::int32_t{item.light});
    bindings.set_uniform("scale",35.0);
    bindings.set_uniform("seed",17.0);
    bindings.set_uniform("mode",std::int32_t{item.mode});
    bindings.set_uniform("edgeStrength",0.42);
    bindings.set_uniform("edgeColor",noisemaker::glsl::DVec3(static_cast<double>(0.13f),static_cast<double>(0.67f),static_cast<double>(0.29f)));
    bindings.set_uniform("speed",2.0);
    bindings.set_uniform("time",0.375);
    bindings.set_uniform("alpha",0.83);
    const auto kernel=noisemaker::generated::bind_filter_lowPoly_lowPoly(bindings);
    for (int repeat=0; repeat<2; ++repeat) {
      const auto image=noisemaker::run_pass(kernel,width,height,0.375f,43.0f);
      const auto fh=hex(sha256(little_endian_float_bytes(image)));
      const auto rh=hex(sha256(image.to_rgba8()));
      if (fh!=item.f32 || rh!=item.rgba)
        throw std::runtime_error("case mode="+std::to_string(item.mode)+" f32="+fh+" rgba="+rh);
      REQUIRE(std::equal(input.data().begin(), input.data().end(), data.begin()));
    }
  }
}


TEST(runtime_strokes_matches_cpu) {
  constexpr std::size_t width=7U, height=5U;
  std::vector<float> data(width*height*4U);
  for (std::size_t y=0; y<height; ++y) for (std::size_t x=0; x<width; ++x) {
    const auto i=(y*width+x)*4U;
    data[i]=static_cast<float>(static_cast<double>((37*x+17*y+11)%127+1)/129.0);
    data[i+1U]=static_cast<float>(static_cast<double>((19*x+43*y+7)%113+2)/117.0);
    data[i+2U]=static_cast<float>(static_cast<double>((61*x+29*y+3)%109+3)/115.0);
    data[i+3U]=static_cast<float>(static_cast<double>((7*x+5*y+2)%23+8)/31.0);
  }
  const noisemaker::Surface input(width,height,data);
  struct Case { int mode; std::string_view f32, rgba; };
  const std::array<Case,5> cases={{
      {0, "22237989054a795dc185f386530eceea80d15cc660ffee65b2ea1879792f205e", "71404eeefc445bab19aa8e19282e049b59d3d77fc7948e5b7f67f881c928f619"},
      {1, "e0aa4eb29d0dbc79fdf3ac5cffb7970e66b11e180831b431daf41a57e6e46899", "9ab7cb9a8486e3c4f9fea1b20ad0a3902773f7d01dc228332ed54b4d42f2b0a7"},
      {2, "d04ab5400398c8efba136aacc3cada5137e679e810ef648c7ab7dc593f87b50a", "7425e3883d66c482367cf3739a92546e97779590e69eab4f0a1226082151f20e"},
      {3, "b7c59a507648c0eb192e7af9d13ae5b02a3009f20ab59e3911aa6a0a7b707a5b", "0c01c5a388a811ffcc52e542879e46cdb8e5ab0f1f6866d6b0472870e0f3d556"},
      {4, "9078560d1833f6f6f8f5876dcabdbe868f39e9d98e366745cf493d7b5adf0472", "5efa62932cc63d2e88ce3d8a5ecf90d8afbb93701de845297550a6224f9edfe8"},
  }};
  for (const auto& item:cases) {
    noisemaker::glsl::Bindings bindings;
    bindings.set_texture("inputTex",input);
    bindings.set_uniform("tileOffset",noisemaker::glsl::Vec2(2.0f,1.0f));
    bindings.set_uniform("resolution",noisemaker::glsl::Vec2(7.0f,5.0f));
    bindings.set_uniform("MODE",std::int32_t{item.mode});
    bindings.set_uniform("strokeLength",18.0);
    bindings.set_uniform("balance",44.0);
    bindings.set_uniform("intensity",66.0);
    const auto kernel=noisemaker::generated::bind_filter_strokes_stkSmear(bindings);
    for (int repeat=0; repeat<2; ++repeat) {
      const auto image=noisemaker::run_pass(kernel,width,height,0.375f,43.0f);
      const auto fh=hex(sha256(little_endian_float_bytes(image)));
      const auto rh=hex(sha256(image.to_rgba8()));
      if (fh!=item.f32 || rh!=item.rgba)
        throw std::runtime_error("case mode="+std::to_string(item.mode)+" f32="+fh+" rgba="+rh);
      REQUIRE(std::equal(input.data().begin(), input.data().end(), data.begin()));
    }
  }
}


// CPU9f3 Caustic and Texture runtime reference cases.
TEST(typed_caustic_runtime_noise_modes_match_current_cpu) {
  struct Case { const char* name; int mode; bool wrap; float noise_scale; float speed; int seed;
    float hue_rotation; float hue_range; float intensity; float time; noisemaker::glsl::Vec2 tile;
    noisemaker::glsl::Vec2 full; const char* float_hash; const char* rgba_hash; };
  const std::array<Case, 18> cases{{
    {"constant-default-wrap", 0, true, 85.0f, 25.0f, 44, 180.0f, 25.0f, 0.0f, 0.375f, noisemaker::glsl::Vec2(0.0f, 0.0f), noisemaker::glsl::Vec2(8.0f, 8.0f), "367fb4c04be302e268c958bc12d6889d07bf417c1fdd03510b8b063d28c43713", "6006c27ae98dc7a3f51d54dd73d2a402ac3f62e5af9928ba8c9259c326b31e10"},
    {"constant-offset-no-wrap", 0, false, 37.0f, 63.0f, 17, 37.0f, 74.0f, 22.0f, 0.625f, noisemaker::glsl::Vec2(3.0f, -2.0f), noisemaker::glsl::Vec2(13.0f, 11.0f), "30dbbfd52156e09041bb40b20d1b107e3a28cb9bc5b541a68873dacd7e16d511", "4dacea4407014b1ad1668ae7d50e5bc83c03076de3a6963f7ec25a59d8dcdc74"},
    {"linear-default-wrap", 1, true, 85.0f, 25.0f, 44, 180.0f, 25.0f, 0.0f, 0.375f, noisemaker::glsl::Vec2(0.0f, 0.0f), noisemaker::glsl::Vec2(8.0f, 8.0f), "f80a57025f3e3069dee835b90e8e8108f37e393eea4bae86c7b8b4dc178615c0", "65c86e175add45d5aecb2b8e3bf752058f534e11eecb6ced4ad17510f6e8dd7d"},
    {"linear-offset-no-wrap", 1, false, 37.0f, 63.0f, 17, 37.0f, 74.0f, 22.0f, 0.625f, noisemaker::glsl::Vec2(3.0f, -2.0f), noisemaker::glsl::Vec2(13.0f, 11.0f), "8ee97a02aca7f3eac5f23319049031f4815a5efcb242be7135c0a03b625ea39d", "8385e18ca10f2dc9b8d7bef7d2e99f110731c9f256b37cf1f49331b009e9e9f8"},
    {"hermite-default-wrap", 2, true, 85.0f, 25.0f, 44, 180.0f, 25.0f, 0.0f, 0.375f, noisemaker::glsl::Vec2(0.0f, 0.0f), noisemaker::glsl::Vec2(8.0f, 8.0f), "cfab1393958f97871bedf689734f48507203104d58b5e8cdfd4b73a53b57b300", "5a1c400641024dd810b31ce7b3014b8068a5e322601be5d6cda1c3cc369eee63"},
    {"hermite-offset-no-wrap", 2, false, 37.0f, 63.0f, 17, 37.0f, 74.0f, 22.0f, 0.625f, noisemaker::glsl::Vec2(3.0f, -2.0f), noisemaker::glsl::Vec2(13.0f, 11.0f), "a831c1ea4e535e1819383e560201ee4ee52d01dfb0b63a1b5f43ff513c094a62", "fc7d643ef5013b214d8b7b6596d1a1bc37e5536cac7bb4fa12fbdf1192d629c1"},
    {"catmullRom3x3-default-wrap", 3, true, 85.0f, 25.0f, 44, 180.0f, 25.0f, 0.0f, 0.375f, noisemaker::glsl::Vec2(0.0f, 0.0f), noisemaker::glsl::Vec2(8.0f, 8.0f), "97f0fb0f63862d31c74cddf560a7d395ae6e538bd99b742ea211b98241b5501d", "418ecd27b1fb6ec7ce905070d9dc976d232372b5e3e339549b85d13a769ea4e0"},
    {"catmullRom3x3-offset-no-wrap", 3, false, 37.0f, 63.0f, 17, 37.0f, 74.0f, 22.0f, 0.625f, noisemaker::glsl::Vec2(3.0f, -2.0f), noisemaker::glsl::Vec2(13.0f, 11.0f), "cfd10801161c934badb4a005498e45a4031662d64ba351c9612e67a8fd73084e", "f55b284b6abb187d88ce15747ca79a4973f16c3be57594ad0a6f5672bcb224c3"},
    {"catmullRom4x4-default-wrap", 4, true, 85.0f, 25.0f, 44, 180.0f, 25.0f, 0.0f, 0.375f, noisemaker::glsl::Vec2(0.0f, 0.0f), noisemaker::glsl::Vec2(8.0f, 8.0f), "70b1b02575a47b587af2ee8108fff0028da002704468626c1ff259118b04deaf", "5a1c400641024dd810b31ce7b3014b8068a5e322601be5d6cda1c3cc369eee63"},
    {"catmullRom4x4-offset-no-wrap", 4, false, 37.0f, 63.0f, 17, 37.0f, 74.0f, 22.0f, 0.625f, noisemaker::glsl::Vec2(3.0f, -2.0f), noisemaker::glsl::Vec2(13.0f, 11.0f), "7c3f32f59c3e61ff037a2b1ab12c4af9beb20e97fd49c313d3a2c2618273b054", "dae0fe089e249dcd232fb78a8b57ddcad0c1080340e603c4bee2cdb782537b20"},
    {"bSpline3x3-default-wrap", 5, true, 85.0f, 25.0f, 44, 180.0f, 25.0f, 0.0f, 0.375f, noisemaker::glsl::Vec2(0.0f, 0.0f), noisemaker::glsl::Vec2(8.0f, 8.0f), "c4c8192d517781e593781ead10bd82d2636c4f810212f351ef73ed1b60f349bc", "271c8d006e03274f7c2e39e4caf6a7de3df4cc577eb480bb188af271cf825cd7"},
    {"bSpline3x3-offset-no-wrap", 5, false, 37.0f, 63.0f, 17, 37.0f, 74.0f, 22.0f, 0.625f, noisemaker::glsl::Vec2(3.0f, -2.0f), noisemaker::glsl::Vec2(13.0f, 11.0f), "060be3d597ee2858324f3c474fe0adb0eb78c2d7aaa80c158c5ec8b91fe4e900", "75b2321bfd627ce0a8475d1b6868670aae7e005c4d3f6de1988fad3d6a601667"},
    {"bSpline4x4-default-wrap", 6, true, 85.0f, 25.0f, 44, 180.0f, 25.0f, 0.0f, 0.375f, noisemaker::glsl::Vec2(0.0f, 0.0f), noisemaker::glsl::Vec2(8.0f, 8.0f), "c17042af26b73ee946726693428df8cbc671b7fb7eb518ea721822240cc3195d", "e9ab9b2e185b7b642ba042702ac937f7168d64937a4ee9197813fb87c7eec446"},
    {"bSpline4x4-offset-no-wrap", 6, false, 37.0f, 63.0f, 17, 37.0f, 74.0f, 22.0f, 0.625f, noisemaker::glsl::Vec2(3.0f, -2.0f), noisemaker::glsl::Vec2(13.0f, 11.0f), "90546ffc53d6d878e58cbaf880a5b8902f08cbc7747652bf3afea77306bcf5c5", "f2bd44f783bdc5f6c541cec65cacc3db2af80ff3de8bfe8eaa407c24d441df5a"},
    {"simplex-default-wrap", 10, true, 85.0f, 25.0f, 44, 180.0f, 25.0f, 0.0f, 0.375f, noisemaker::glsl::Vec2(0.0f, 0.0f), noisemaker::glsl::Vec2(8.0f, 8.0f), "23fbe21e1de1c0f51b430a2d24265500198766882fc2c905c7345ef7cb80d05b", "225acd3a22c7fc6c0348d7efa13a641f1c002b23c8e304516bad7783949eadd4"},
    {"simplex-offset-no-wrap", 10, false, 37.0f, 63.0f, 17, 37.0f, 74.0f, 22.0f, 0.625f, noisemaker::glsl::Vec2(3.0f, -2.0f), noisemaker::glsl::Vec2(13.0f, 11.0f), "525403784280500aa429826bab9787ce5ced9eceedf7d5fcc180a4332c70f7bc", "ac2ff8b9cda7a9c668c7253b6bd993efdae22c445760a608f40e4ee881459701"},
    {"sine-default-wrap", 11, true, 85.0f, 25.0f, 44, 180.0f, 25.0f, 0.0f, 0.375f, noisemaker::glsl::Vec2(0.0f, 0.0f), noisemaker::glsl::Vec2(8.0f, 8.0f), "141eaf1619677e73ab7ec75bffbd3859ebd0fb7d8dbc57c3ad13284444a2fe73", "a48893a259330a68e04dd6fe23763491eab14eedbb1531ef3ffd7867d8bcd8d2"},
    {"sine-offset-no-wrap", 11, false, 37.0f, 63.0f, 17, 37.0f, 74.0f, 22.0f, 0.625f, noisemaker::glsl::Vec2(3.0f, -2.0f), noisemaker::glsl::Vec2(13.0f, 11.0f), "f146debfc80c31d2dc9b999c35c5deda2c0044cc8eb2b8a2b5d6812431cafa2f", "db2aeddd773dbbb6cfd28312ceca6ad4ea9130d3a3079b11025045dc36258abb"},
  }};
  for (const auto& item : cases) {
    noisemaker::glsl::Bindings bindings;
    bindings.set_uniform("NOISE_TYPE", static_cast<std::int32_t>(item.mode));
    bindings.set_uniform("wrap", item.wrap);
    bindings.set_uniform("noiseScale", item.noise_scale);
    bindings.set_uniform("speed", item.speed);
    bindings.set_uniform("seed", static_cast<std::int32_t>(item.seed));
    bindings.set_uniform("hueRotation", item.hue_rotation);
    bindings.set_uniform("hueRange", item.hue_range);
    bindings.set_uniform("intensity", item.intensity);
    bindings.set_uniform("time", item.time);
    bindings.set_uniform("resolution", noisemaker::glsl::Vec2(8.0f, 8.0f));
    bindings.set_uniform("tileOffset", item.tile);
    bindings.set_uniform("fullResolution", item.full);
    const auto kernel = noisemaker::generated::bind_classicNoisedeck_caustic_caustic(bindings);
    const auto first = noisemaker::run_pass(kernel, 8U, 8U, item.time,
                                           static_cast<float>(item.seed));
    const auto second = noisemaker::run_pass(kernel, 8U, 8U, item.time,
                                            static_cast<float>(item.seed));
    require_repeat(first, second);
    const auto float_hash = hex(sha256(little_endian_float_bytes(first)));
    if (float_hash != item.float_hash) throw std::runtime_error(std::string(item.name) +
        " float oracle hash: " + float_hash);
    REQUIRE(hex(sha256(first.to_rgba8())) == item.rgba_hash);
  }
}

TEST(typed_texture_runtime_modes_match_current_cpu_without_mutating_input) {
  struct Spec { const char* name; std::size_t width; std::size_t height; int phase;
    float time; float alpha; float scale; float intensity; float contrast; bool mono;
    noisemaker::glsl::Vec2 tile; noisemaker::glsl::Vec2 full; };
  const std::array<Spec, 2> specs{{
    {"paper-center", 4U, 3U, 2, 0.25f, 1.0f, 1.2f, 65.0f, 35.0f, false, noisemaker::glsl::Vec2(1.0f, 2.0f), noisemaker::glsl::Vec2(16.0f, 12.0f)},
    {"paper-wide-tile", 8U, 3U, 6, 0.41f, 0.8f, 1.8f, 55.0f, 55.0f, false, noisemaker::glsl::Vec2(-2.0f, 5.0f), noisemaker::glsl::Vec2(32.0f, 12.0f)},
  }};
  struct Case { std::size_t spec; int mode; const char* input_float; const char* input_rgba;
    const char* output_float; const char* output_rgba; };
  const std::array<Case, 30> cases{{
    {0U, 0, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "1498a43d593339a26ee782c98183ed3d85adc4dce7826dd43843ee1a972778e1", "712f535e5f0d86052e43c890ddcebe6ac72c13f88515bda573beb56697fd887d"},
    {0U, 1, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "9fb724b253d475737eabe4e546c3b8f1966f65e5a209d66a7319407372783397", "703b5da8dd2fc5b79efb856c711fbde0c1da14d1d1eda9903a2e4219873a5dcd"},
    {0U, 2, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "fce277a683bc448b5f6694a4a2b246ebcd43d464a8de0a87fe6ba39e447fdafe", "d20db9a7485cf822d354c824d70bb2a656980ee80efba4e3afcd45393deb100b"},
    {0U, 3, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "bc13c403dcd1e13342610351369eebc6443f0eb7c4484cf98a073560bf3fc294", "2477b883d7efdedbd0c16d22befea2603fe8059d8f7d0cbd7fff8c8326c15326"},
    {0U, 4, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "ad36b4d4b1e1c1959d82a6d8a0271e944bb54f2ec12b148f90e98632187d3656", "fc92f5f0073d1e353f08d0f619bec10133ac646fb0c76de7efee7d7f1f95f9b9"},
    {0U, 5, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "73accd095219799d84d0a47aa3b07aaf951ac2e7e26d3cd31984be60821abb7f", "417c1f7f2b0aaaee7d3c4a8f72cd977f0e69904c3ab34d1238b240b9a17a24eb"},
    {0U, 6, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "f837d3d2bb2215961b39d72952917356816e009126285a8e82fbfd93da1f840b", "7c66a553d7ba214429d81e4d2d0291206226f43f69ab1d00bd2763722e994cfe"},
    {0U, 7, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "53184491db93a3ffb6ef6016a744458bd1b24268e03ffd9f72649fcddc84715d", "9cd1c6ba1b8513d81e0f811e71040f7414bb19d5f3acd1a89300a2a8a3e6e9a5"},
    {0U, 8, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "368847d6f779e76e89691086158f31e2803b5dc420f6fe5e48d095c3e6a116c8", "4757d7d0d52f10aeb6a5bf622fc56a1bb84608011c85f7b8af02c709484ff7a8"},
    {0U, 9, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "6a2fca58b5747c57c6eecfb7268609cde89c109e70b50ebd7bca9a992a367045", "55d1e50713cb2d4aa6b5cb5df4db35885c1fa5b652e2b9b71f631d491dc0bd75"},
    {0U, 10, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "e7d699396e3ee99d9172cd7850207549d5d5da60c8241e59eb5a7b362641e5d9", "6235c3ee71d306be8a8d2756669975529443d9ff30b8052048ca127cfda910b3"},
    {0U, 11, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "63e7d025cced7198d627248b6d08583637ec3f2323128acd093227ef97cd4ee8", "e53b869355731664ce838d3bf6ec6776a7a465b0f93c6020f0540decb1e134ad"},
    {0U, 12, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "b84e261908c428c3314df752b6b5d8d9c64b5347d649825cb53a6ce435e3f341", "aa347b5ac4230eca797bf558c5f548c104d345f2ed97f3985ef489707f45d2c6"},
    {0U, 13, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "da6d5d9e2ddb3fea4ee862b64952bba02bc7a3a70f02107432b9a3d6ee97774d", "588bbfe74adc89207e53ea9fb9104fee5a8d014782539ddcae4e11940d42e854"},
    {0U, 14, "d031e3c00beaec93a6b5b015b6d158c02cb7b2d360cd4b4b759aeeef010cf38c", "44a82fb3485fc94cce81a3d674a16e427387ff1c885c1aaa672a4803f389ca82", "72ee4a4b13f57ca2b518fdde6866393293bd445cb6a06ccf5eb1be392bca717b", "456914d18d7f78912e83a913ea52dda59da475872d9cc2c50a0b22d3a2ecd736"},
    {1U, 0, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "6b0c4fe01e0dcbe96712cf57b2bf3d344294e7280dab6043bbd6c8f9a8603106", "1e64b063a606d861950079817971e2c9cb6d36ded6721b243df3f17178712c18"},
    {1U, 1, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "2ec6efdf64d85f8d166f92391f0440a0192b4d0292ad9abd062401525ba8022d", "6139605c3b04d3716ecef0a23863457474610a7c64d95244563766294bb3c94b"},
    {1U, 2, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "84711da24121eda61d646c14c5bb00c6855a81d4bfdbca971ef359a68582b9fa", "ca4022f1a45a4a2412c1b6f86085ac035da02740962fba74ff2f393a2de363d1"},
    {1U, 3, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "f0685126fcf35dd974a4d03733bf44a29995ae992802d777e506a27a0a3c0ea2", "44db9547bad15e1a05cd86d7dce4547217a0c3e231d274c5874d24464fa96ca1"},
    {1U, 4, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "315d49acbc6df227ee72938cbad3b215e23085ea98ae7d483ca5b53fd8b0aa0a", "360acefdce0466516f4a74060afe3fe0ce4144aac8d07ad75caf437e7ad4a747"},
    {1U, 5, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "7382e5b2456e2f37b236643aa68ece4adfcc883aaeddfb8965350b8c5ba64065", "19480e9e82ec09e7ff9ed21ba8bf5aed6aca26f9744e311628370d79ce86fa3c"},
    {1U, 6, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "55e03f8a9475515426f8e358ef82c55bb124bf4f811fa1c0e480aeac44fe167e", "4cfdf42cac019cafbc5dd2250cd36730100910650feb7e5589bc00b1b1048f13"},
    {1U, 7, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "bed61b51a6d3506df73fce2475aace7cfaa4e52df3fc705a03b80b6ae55b4965", "be7910dc68f9555c236d613744d11036cc06dd792b4ccf43434791b9f83169de"},
    {1U, 8, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "5e8ba88df29927ad4b513646915fbe35ef8d08d342948929cf153adf5e6451ce", "35ac47bbb53634666bcad87032d38201077a30cdc8c4d9c09814e4fddcf99543"},
    {1U, 9, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "bfdd237516b7fc27ed2b70009479f9830b42bb114ba9fa2bbefa6637b71f27df", "0fcf157e38d8eb5a61278702c41e505ff519d57a06114b08c89c95f7ddb77e79"},
    {1U, 10, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "3359c53f1679e9376803798daa4e6e5083d3c0f8f7f7d5ba041fd89b5916a16a", "5ba845f8d9d2e06de010203fa0ca04c6e8e25a3731d1236c773fc6620a3188f2"},
    {1U, 11, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "c684b100075db8de530256f285fd20674c44c8793a0d9767741bf35bc32e7ee1", "3cf49c6ca6bf4bddeb6278f1c40bf6f8b854974eb58fcf3a9baa87f13238df2f"},
    {1U, 12, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "cc8816a67c1fa1ff2eda61d13635ee7a276f4ea0b0d6e0e2d933bc98edfb5e74", "1a6d41eb031c432301145a78c500c04efdaf18e5babdff2a09f480b7c55d6a06"},
    {1U, 13, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "b7dda7c3aef446346793212283cdad545112d831be33380e5c6ca1d2701ba56b", "55787ce11de5aca726c80caa2f43c4386d3fdd2ab50467fd7db340c9e136a002"},
    {1U, 14, "0b3d946ca5827471a6ef59cbf3c9adeb099b19ee6f0c0ec68e4090c9a1201b14", "d06621c8ce2f653d4278f60fae9267c35c7aadc914cc15c907ee70f445ee4e07", "8f05ad5a00836a9cf833975719e648e8d228e9f274830b55ed1f3421ce3e4b3c", "1b0c5cd98f92ad74afb566628cb232c16d4e6096a71ed5054fb3a77eb1e7565c"},
  }};
  const auto make_input = [](const Spec& spec) {
    noisemaker::Surface input(spec.width, spec.height);
    for (std::size_t y = 0; y < spec.height; ++y) for (std::size_t x = 0; x < spec.width; ++x) {
      const std::size_t i = (y * spec.width + x) * 4U;
      input.data()[i] = static_cast<float>(static_cast<double>((x * 17U + y * 11U + spec.phase) % 29U) / 28.0);
      input.data()[i + 1U] = static_cast<float>(static_cast<double>((x * 7U + y * 19U + spec.phase * 2) % 31U) / 30.0);
      input.data()[i + 2U] = static_cast<float>(static_cast<double>((x * 13U + y * 5U + spec.phase * 3) % 37U) / 36.0);
      input.data()[i + 3U] = static_cast<float>(0.2 + static_cast<double>((x + y + spec.phase) % 8U) / 10.0);
    }
    return input;
  };
  for (const auto& item : cases) {
    const auto& spec = specs[item.spec];
    const noisemaker::Surface input = make_input(spec);
    const auto input_floats = little_endian_float_bytes(input);
    const auto input_rgba = input.to_rgba8();
    REQUIRE(hex(sha256(input_floats)) == item.input_float);
    REQUIRE(hex(sha256(input_rgba)) == item.input_rgba);
    noisemaker::glsl::Bindings bindings;
    bindings.set_texture("inputTex", input);
    bindings.set_uniform("MODE", static_cast<std::int32_t>(item.mode));
    bindings.set_uniform("time", spec.time);
    bindings.set_uniform("alpha", spec.alpha);
    bindings.set_uniform("scale", spec.scale);
    bindings.set_uniform("intensity", spec.intensity);
    bindings.set_uniform("contrast", spec.contrast);
    bindings.set_uniform("mono", spec.mono);
    bindings.set_uniform("tileOffset", spec.tile);
    bindings.set_uniform("fullResolution", spec.full);
    const auto kernel = noisemaker::generated::bind_filter_texture_texture(bindings);
    const auto first = noisemaker::run_pass(kernel, spec.width, spec.height, spec.time,
                                           static_cast<float>(spec.phase));
    const auto second = noisemaker::run_pass(kernel, spec.width, spec.height, spec.time,
                                            static_cast<float>(spec.phase));
    require_repeat(first, second);
    REQUIRE(little_endian_float_bytes(input) == input_floats);
    REQUIRE(input.to_rgba8() == input_rgba);
    const auto float_hash = hex(sha256(little_endian_float_bytes(first)));
    if (float_hash != item.output_float) throw std::runtime_error(std::string(spec.name) +
        " MODE " + std::to_string(item.mode) + " float oracle hash: " + float_hash);
    REQUIRE(hex(sha256(first.to_rgba8())) == item.output_rgba);
  }
}

// CPU9f3 Classic Noise and Moodscape runtime reference cases.

TEST(typed_noise_cpu9f3_dynamic_enum_values_exact) {
  struct Case {
    std::string_view name;
    bool alternate;
    std::int32_t color_mode;
    std::int32_t loop_offset;
    std::int32_t metric;
    std::int32_t noise_type;
    std::int32_t refract_mode;
    std::string_view float_sha256;
    std::string_view rgba_sha256;
  };
  constexpr std::array<Case, 45> cases{{
      {"base-default", false, 6, 300, 0, 10, 2, "c3f57c55dadee9446a65280c103ec8ef673eca60b6f2a9a458f2edfbacbd0f0e", "5806d404588da9b8f591eb482e50bb450a791d100fba2173ea13473725b071bc"},
      {"COLOR_MODE-0", false, 0, 300, 0, 10, 2, "9a3a02e146e739dfe5ecb6149e6a806d9ae3d8dea91a80d4a136c79d262f2259", "4d32bbfaa981a9d29c80bcd6e5c2d8d2ad0bfff8a31c523da1034f5736e50207"},
      {"COLOR_MODE-1", false, 1, 300, 0, 10, 2, "c95f75fb0611a7afd922e398197e8c95e180924c956c96c1d48782e89bf16636", "3af156409a55a8334dcbb382e9e9580952dd38b78840aeaca810046d51c84fbf"},
      {"COLOR_MODE-2", false, 2, 300, 0, 10, 2, "edab093a0798dc812cf4b2f01a3106476ff959942c5d1d5bf9c6c9953c29528b", "c17b0a8ef20065514f28335c04ef19105e59a253aedac90af4dd7950421d9eab"},
      {"COLOR_MODE-3", false, 3, 300, 0, 10, 2, "77266c3a178808c04d35e3aad6bcc5ff9c5844b76579b075a9ee615a6c262601", "c65a5e93f8a47cb9e2e67a469e1d84a3d34e8453b2755d58883d6f8f8ef1d80a"},
      {"COLOR_MODE-4", false, 4, 300, 0, 10, 2, "acfbd7d74ead64a0078885ddca88f9ace3d61d3a96f7a9ca77f0dbbf2475bf8a", "90be583d23a9d274804dc4f593c183dce31afde0e07ca67cb8994fe5bc5e84f7"},
      {"COLOR_MODE-6", false, 6, 300, 0, 10, 2, "c3f57c55dadee9446a65280c103ec8ef673eca60b6f2a9a458f2edfbacbd0f0e", "5806d404588da9b8f591eb482e50bb450a791d100fba2173ea13473725b071bc"},
      {"LOOP_OFFSET-10", false, 6, 10, 0, 10, 2, "048f0cd377eec5f088e262835ac663684e4c100a92c051faba37cf148def10b2", "0efe5e02d57059bfbb5c5f68e54aeeb8966ef4590bf336752b5c74adeb7e9bd9"},
      {"LOOP_OFFSET-20", false, 6, 20, 0, 10, 2, "869d3d0bccc6c07a67b97be7a04f0f6a77065f22da6e641ede21a4a2c542728b", "9fb423f15766c5dfd0c6a61a11d3e512f1a28159b6d7ddcf61c08a0e048aaf25"},
      {"LOOP_OFFSET-30", false, 6, 30, 0, 10, 2, "7d579b874d468b1909a2b3cf0bc2ead34252c0068c6ba3cb0a6fb5fc87a8af1e", "b4eaba5b61f0af7fe0dfbc7f581e8895610c901a0eea3c8cda345d3cb3bd0a80"},
      {"LOOP_OFFSET-40", false, 6, 40, 0, 10, 2, "ca327f664d6d0b18b5a2de9a88edbad78ade1ec182c655c53171dcec0a90f989", "506908df35fcb0a38842602ea4d6e2012f54875f6804448a3313249f7b867889"},
      {"LOOP_OFFSET-50", false, 6, 50, 0, 10, 2, "a188cde087e964fd37e59075ac84d0a029c2e4e2bcbe9b6626a578f42eaa4c63", "173af45d5a1a968e9010e0c1cce00d4771b59e1a70c5e4b75cfd8dd7644c492d"},
      {"LOOP_OFFSET-60", false, 6, 60, 0, 10, 2, "32103a57013158d44c5f3e5c4c9d721d8ce61e586bc26437d3f0e56d9d81d52a", "bcf497fa1d58280248a34e015dde7c8f37c986c0134aec053b117b86a97a026e"},
      {"LOOP_OFFSET-70", false, 6, 70, 0, 10, 2, "3f5680656fb534213412a5c97f241b23746f08211ebdfbf292cb49a5a5b790e5", "953fe7d313892648d7ad7944adb5ea56ee3decfab1c8f576273f537548f633b9"},
      {"LOOP_OFFSET-80", false, 6, 80, 0, 10, 2, "e79e94998f80cf69f3e35afadef1dcacf54f5d85bc30bf1de45a7f65c835818d", "39439664e8348cc9d17b31e49cf3870a96faf6d6cdcbcdf8662c154e35b7606d"},
      {"LOOP_OFFSET-90", false, 6, 90, 0, 10, 2, "9669c89acc6201a8d3c33ed2f7488c641e47ccc5a568f86b54f27a09a03b680d", "5949b08f51cbddb0482db3de31830abe716249cf5d8900bc83dc78a456a0fe06"},
      {"LOOP_OFFSET-100", false, 6, 100, 0, 10, 2, "319a8268bc1881699b80e35754e3cac28fec67e81ce4cf137f4b1e068b0ca8c9", "b0ccee26e281ed47203846038f40851c3d5c7f5ac3200c21da3933dcc542c825"},
      {"LOOP_OFFSET-110", false, 6, 110, 0, 10, 2, "4013af85937b124820f6dc2280612b6958380507a40122202489bc0f72a62078", "817ba96e7468e77a3ab1a5d576c82eb1db6101d8e6168572d95db0c4eecbdca4"},
      {"LOOP_OFFSET-120", false, 6, 120, 0, 10, 2, "909722e8edcfbfd8594ba69ef480c882a49df67e7d4e58ff4b56978e90533091", "69490b846c7f5a4571b4fc18b3182732d9ddc81e152de41aa42cf01b8c37934a"},
      {"LOOP_OFFSET-200", false, 6, 200, 0, 10, 2, "a0ece66a57a1533234e2222b84d8c713096048a26c0e06acad81b891f6c3de0c", "d8200dcab6aa7749d3c6776e8420755e5c035a4b7e80251c141fb008ff3dde93"},
      {"LOOP_OFFSET-210", false, 6, 210, 0, 10, 2, "91aa743c2e5f76343ae4b14ed353b179f424edbf601329c1cd762fe7855eeca3", "d542ad6a5770f266ea641a6bcb8ff7264d62d44007d175e21fa1fd68ab327838"},
      {"LOOP_OFFSET-300", false, 6, 300, 0, 10, 2, "c3f57c55dadee9446a65280c103ec8ef673eca60b6f2a9a458f2edfbacbd0f0e", "5806d404588da9b8f591eb482e50bb450a791d100fba2173ea13473725b071bc"},
      {"LOOP_OFFSET-400", false, 6, 400, 0, 10, 2, "c9e6539e2a5265fd521414ab560297d08ba316e8354d5b8b3b3c2de8180505f5", "69d8ad3815e2bcc4d62f7a9d6a375626783dd9e96d4f0a9091fe82895976c704"},
      {"LOOP_OFFSET-410", false, 6, 410, 0, 10, 2, "108187a384b649de627fbf6bd29fb519bd67acdaa28d77f947c72a8859e8a777", "09a2445993f52922726ed375980d419cd354c602ba50418aa4f1196eb162e296"},
      {"METRIC-0", false, 6, 300, 0, 10, 2, "c3f57c55dadee9446a65280c103ec8ef673eca60b6f2a9a458f2edfbacbd0f0e", "5806d404588da9b8f591eb482e50bb450a791d100fba2173ea13473725b071bc"},
      {"METRIC-1", false, 6, 300, 1, 10, 2, "ee09f77e547a4e7d784d886c1f1c02beaad47a3a0c64d1142a026717e8801d51", "c4cc6a273420e33d287c801208e35aa1c2ef4e04bfb1820f04df2c2470318a5c"},
      {"METRIC-2", false, 6, 300, 2, 10, 2, "083b7eccaf3c812642f65b66ac35556a2f652ec2b593cc39619c5afef86dd2c9", "1e1aeb3ac8da2f54536b068188f81056aec22ab499a96cb1283e361c77046321"},
      {"METRIC-3", false, 6, 300, 3, 10, 2, "b646d4f042cb6290dbf315e15ec8ce040d986a394437ab3a08be337ffc205247", "4a40038f79dda624fbe1f1435b07ac2ae3413bd6aff4b03c7e116c1031d9385a"},
      {"METRIC-4", false, 6, 300, 4, 10, 2, "1e540400eed0ebf4492622e5574bcabd244b831b02c01988de675450c909fb49", "e9b0520edefb6ef4cde9806ce1357a1d3c77d8d893158adaea6a0eab26a4e6ee"},
      {"METRIC-5", false, 6, 300, 5, 10, 2, "3c732d73afc32b684aab5f8bbcbe81432ecfbd0115a26a7d4e47db7227cc51ec", "23b8508f0f31fe84d9b0034d578679809f3a88307afceeb0291cc43aea910fa6"},
      {"REFRACT_MODE-0", false, 6, 300, 0, 10, 0, "bbbe197d0e7a794ec9fe16dc04deae31f2e31880051499ef2a788fb4a99808f2", "d837a65919db3a7e616b9f7343f283a6c9895f2c252e8e9bb0a99e76043676f6"},
      {"REFRACT_MODE-1", false, 6, 300, 0, 10, 1, "d995c92fd1ba2d58f9125fe2c41c14b30b8723a911d1d49d4aa2a71ae4e6cfa3", "f01df030373eb69ae80d2f307d6fd1bfcc42f4b573c8e077f380bf5206f05827"},
      {"REFRACT_MODE-2", false, 6, 300, 0, 10, 2, "c3f57c55dadee9446a65280c103ec8ef673eca60b6f2a9a458f2edfbacbd0f0e", "5806d404588da9b8f591eb482e50bb450a791d100fba2173ea13473725b071bc"},
      {"NOISE_TYPE-0", false, 6, 300, 0, 0, 2, "cfa2afc5f6a0825ad70b0d252e7e44e2d20acd40eef0f67163288510ffe27ea7", "3cacc0d76fc91dae60b92ad029d2615cc8efec7b37c06b38e03be69bcf50444a"},
      {"NOISE_TYPE-1", false, 6, 300, 0, 1, 2, "02b67895acafb800b9879141caf236899ede37903ab5c5aecf1596c9b0337b23", "0a3bdff122fb3dc440da34754e85c1e77a57a72d706d22fb78f13bb70be3a2ba"},
      {"NOISE_TYPE-2", false, 6, 300, 0, 2, 2, "684588a84844c3bf4a61f78d62be1f38011601e59cd537c814ffbf9eadaea681", "cd93f4e97895701c90d9e5499edb202f8e96ec7a1afc26034ef0dc4a1e2c6428"},
      {"NOISE_TYPE-3", false, 6, 300, 0, 3, 2, "a45659d2c1ac6934c1d0f0e9f1a11f7d77e4deb7b146841ee1786fd0ddddeb17", "142afc0119eefb5043636174c19a7191432bf0b4507264d4ec02068db31ea548"},
      {"NOISE_TYPE-4", false, 6, 300, 0, 4, 2, "27f9b9a0d1e4b4579b5b22efdc7f460287eff0823f251eaf2730d245a0cda686", "55843b15795cb6fc4b8a0929acd967a37eb404d8ed87112a27a225fd4563a261"},
      {"NOISE_TYPE-5", false, 6, 300, 0, 5, 2, "3d3995279b634a29d23baa126ae04ec5df073845d71cd47c791a3fd74dc03122", "e3aa7a906485b15e90d4b46de2b56ac03c756c62af7bbdd9d323b60f0c47c427"},
      {"NOISE_TYPE-6", false, 6, 300, 0, 6, 2, "b9ce1287f59226396a18e64e2d179b7898d3223e629609e955aa829e8e3bc057", "192863a5168d759e6d4b3cd6ccaf3523f4bd9313152376b25d502cabaf3179eb"},
      {"NOISE_TYPE-10", false, 6, 300, 0, 10, 2, "c3f57c55dadee9446a65280c103ec8ef673eca60b6f2a9a458f2edfbacbd0f0e", "5806d404588da9b8f591eb482e50bb450a791d100fba2173ea13473725b071bc"},
      {"NOISE_TYPE-11", false, 6, 300, 0, 11, 2, "27975f7d6dd018f2b645c4616f31ad541ea9661725ca848342136e8e2c1cfaf2", "853411a40ae40dca000c3fc2f356241e4266e38e8c8bc5434b98ec319da95277"},
      {"cross-constant-oklab", true, 3, 300, 0, 0, 2, "3ef9f3a1c840ae2c0c76627e638630062f6983ee486faad0666a413ab6d2db7b", "bb9c7c4c9940f0a4ccd78780064254e3eb0cacc5b088b28917436eb2fddb5478"},
      {"cross-spline-palette", true, 4, 300, 0, 6, 1, "3e836789957ccd79eeeb26bf25306c47988625a8233c5aa2d84f442aafeeb9ca", "977276f1df0c6db66a8b82726cbdd48c7ce5464f64a199a568945a74e5219619"},
      {"cross-hash-metric", true, 2, 120, 5, 11, 0, "007e8370e591db52b6c15956dea19fb9f9063dd000d41c61299cc243130d6aa8", "b1afc3dbe46c96d9627c89a90caea13bd4d5768cdc9929dcddb759fc39b5d1fa"},
  }};
  for (const auto& item : cases) {
    const bool alternate = item.alternate;
    const auto render = [&]() {
      noisemaker::glsl::Bindings bindings;
      bindings.set_uniform("COLOR_MODE", item.color_mode);
      bindings.set_uniform("LOOP_OFFSET", item.loop_offset);
      bindings.set_uniform("METRIC", item.metric);
      bindings.set_uniform("NOISE_TYPE", item.noise_type);
      bindings.set_uniform("REFRACT_MODE", item.refract_mode);
      bindings.set_uniform("time", (alternate ? static_cast<double>(static_cast<float>(3.25)) : static_cast<double>(static_cast<float>(-2.5))));
      bindings.set_uniform("seed", (alternate ? std::int32_t{100} : std::int32_t{37}));
      bindings.set_uniform("resolution", (alternate ? noisemaker::glsl::Vec2(static_cast<float>(5), static_cast<float>(4)) : noisemaker::glsl::Vec2(static_cast<float>(4), static_cast<float>(5))));
      bindings.set_uniform("tileOffset", (alternate ? noisemaker::glsl::Vec2(static_cast<float>(0), static_cast<float>(0)) : noisemaker::glsl::Vec2(static_cast<float>(2), static_cast<float>(1))));
      bindings.set_uniform("fullResolution", (alternate ? noisemaker::glsl::Vec2(static_cast<float>(5), static_cast<float>(4)) : noisemaker::glsl::Vec2(static_cast<float>(11), static_cast<float>(9))));
      bindings.set_uniform("xScale", (alternate ? static_cast<double>(static_cast<float>(100)) : static_cast<double>(static_cast<float>(17))));
      bindings.set_uniform("yScale", (alternate ? static_cast<double>(static_cast<float>(100)) : static_cast<double>(static_cast<float>(83))));
      bindings.set_uniform("octaves", (alternate ? std::int32_t{8} : std::int32_t{3}));
      bindings.set_uniform("ridges", (alternate ? true : false));
      bindings.set_uniform("refractAmt", (alternate ? static_cast<double>(static_cast<float>(100)) : static_cast<double>(static_cast<float>(33))));
      bindings.set_uniform("kaleido", (alternate ? static_cast<double>(static_cast<float>(32)) : static_cast<double>(static_cast<float>(7))));
      bindings.set_uniform("loopScale", (alternate ? static_cast<double>(static_cast<float>(100)) : static_cast<double>(static_cast<float>(42))));
      bindings.set_uniform("speed", (alternate ? static_cast<double>(static_cast<float>(100)) : static_cast<double>(static_cast<float>(-100))));
      bindings.set_uniform("paletteMode", std::int32_t{3});
      bindings.set_uniform("paletteOffset", noisemaker::glsl::DVec3(static_cast<float>(0.5), static_cast<float>(0.5), static_cast<float>(0.5)));
      bindings.set_uniform("paletteAmp", noisemaker::glsl::DVec3(static_cast<float>(0.5), static_cast<float>(0.5), static_cast<float>(0.5)));
      bindings.set_uniform("paletteFreq", noisemaker::glsl::DVec3(static_cast<float>(1), static_cast<float>(1), static_cast<float>(1)));
      bindings.set_uniform("palettePhase", noisemaker::glsl::DVec3(static_cast<float>(0.3), static_cast<float>(0.2), static_cast<float>(0.2)));
      bindings.set_uniform("cyclePalette", std::int32_t{1});
      bindings.set_uniform("rotatePalette", static_cast<double>(static_cast<float>(0)));
      bindings.set_uniform("repeatPalette", static_cast<double>(static_cast<float>(1)));
      bindings.set_uniform("hueRange", (alternate ? static_cast<double>(static_cast<float>(100)) : static_cast<double>(static_cast<float>(25))));
      bindings.set_uniform("hueRotation", (alternate ? static_cast<double>(static_cast<float>(360)) : static_cast<double>(static_cast<float>(180))));
      bindings.set_uniform("wrap", true);
      return noisemaker::run_pass(noisemaker::generated::bind_classicNoisedeck_noise_noise(bindings),
          static_cast<std::size_t>((alternate ? static_cast<double>(static_cast<float>(5)) : static_cast<double>(static_cast<float>(4)))), static_cast<std::size_t>((alternate ? static_cast<double>(static_cast<float>(4)) : static_cast<double>(static_cast<float>(5)))),
          static_cast<float>((alternate ? static_cast<double>(static_cast<float>(3.25)) : static_cast<double>(static_cast<float>(-2.5)))), static_cast<float>((alternate ? std::int32_t{100} : std::int32_t{37})));
    };
    const auto first = render();
    const auto second = render();
    const auto actual_float = hex(sha256(little_endian_float_bytes(first)));
    const auto actual_rgba = hex(sha256(first.to_rgba8()));
    if (actual_float != item.float_sha256 || actual_rgba != item.rgba_sha256) {
      throw std::runtime_error(std::string(item.name) + " float=" + actual_float + " rgba=" + actual_rgba);
    }
    require_repeat(first, second);
  }
}

TEST(typed_moodscape_cpu9f3_dynamic_enum_values_exact) {
  struct Case {
    std::string_view name;
    bool alternate;
    std::int32_t color_mode;
    std::int32_t noise_type;
    std::string_view float_sha256;
    std::string_view rgba_sha256;
  };
  constexpr std::array<Case, 17> cases{{
      {"base-default", false, 2, 10, "5dc7a1e74cd47703061f3875100e3ea362d693d13b10557e3d4e03a9277f317c", "465edf2027a381e310a747525d5f38db0a8428842cfd12708ea644c80bb23d59"},
      {"COLOR_MODE-0", false, 0, 10, "37d244344a118408484fc91194289a5d0f5529e37e7d05fe20ce642825cbfe0f", "1ddd546f60cad9aec615479f464f297e496231ccaee14d764f49dd1eeb9f7c41"},
      {"COLOR_MODE-1", false, 1, 10, "584dc98aa174d71d80b5d4c19185de79b063f2c62af2f53dde15219aec67da9b", "c42ff5b7856840edd681d70e3b50b33b9ee5ec8c055b4fbd773a9de460991ab8"},
      {"COLOR_MODE-2", false, 2, 10, "5dc7a1e74cd47703061f3875100e3ea362d693d13b10557e3d4e03a9277f317c", "465edf2027a381e310a747525d5f38db0a8428842cfd12708ea644c80bb23d59"},
      {"COLOR_MODE-3", false, 3, 10, "1819006e46330c0d58155e6b144bba727eb6c27704a8b0901abc6f2a0d4883ae", "6aeeae8cadec3973edbea14af21769b80e09e23265812b7696da9a741c5d02c0"},
      {"NOISE_TYPE-0", false, 2, 0, "c704d706181cb6c2d8fe305c6fddd81e662ef6d50f2ddbde7424350b20193f6a", "bb75b33fd8bc0df6031462239955f3ed233c6cc0f236bd18345ea5e6703c0e51"},
      {"NOISE_TYPE-1", false, 2, 1, "fb863114d3394e081db75abc9c9c552fcf144884280c91265d7cbd5b50dcf45e", "6873a5def9e0a43f8fba76bf033d8b65aafdfffbcda9af157733ff160d647946"},
      {"NOISE_TYPE-2", false, 2, 2, "a394fc6bb91a7901f1e36e7cf3804197c7cd4544e2c01d4f781631f4e9b8d8ee", "17927fca3d5cae06d145a080e3073912ab12378eb4b8be6d1ff8b089cd62490b"},
      {"NOISE_TYPE-3", false, 2, 3, "1cb5a05b7ece9475b2b2ee5169aac8fb2e0bcfc41a5cc494b064c2ff29f963cf", "5a45c734aabb59c5b6081da3b33f204691a611ac58a739230e34480dd5471d7e"},
      {"NOISE_TYPE-4", false, 2, 4, "c0eeefc16b560e035f8d336d9f14a59b1486432014c7e2855636b545a292921f", "f76f83aa24943275120e95b49eb7dd0d86c8bfeb79280188799be8b94ef55b7d"},
      {"NOISE_TYPE-5", false, 2, 5, "bdbc9d1886f77dcfa79930d770c1a70962899884cb18ed852e09053310d65d70", "7a5208170bbe66bd3050a4a22508b634dcc04f5b481a2a0c533a2e6d754e9f40"},
      {"NOISE_TYPE-6", false, 2, 6, "05ffb3cb988b1ff9c5ba84c9dee185b63d159964f8585cbb483d6d5e72d12911", "ce57978099d81291936509b751bc1e96d50daf8685fd70034182a99371a249a5"},
      {"NOISE_TYPE-10", false, 2, 10, "5dc7a1e74cd47703061f3875100e3ea362d693d13b10557e3d4e03a9277f317c", "465edf2027a381e310a747525d5f38db0a8428842cfd12708ea644c80bb23d59"},
      {"NOISE_TYPE-11", false, 2, 11, "5612070da4c77fa8e45c51428a998f7fc05b5376d159074619a0778a0972dc01", "af403b585849aea9ef44a67590d69cf0faf6139521f18e1bd4a4d8738c961694"},
      {"cross-constant-oklab", true, 3, 0, "be92b82a0a642f6a132ffdbd98d583803e5aed8e96259e44dc9b016634aa3686", "bc9ac496a799335fe4020e2e2153a9b4567dd84a6ea940429c0a29e45100dcb0"},
      {"cross-spline-mono", true, 0, 6, "bfb6599baa91850fa3c114d03495669e55c4e4ebd1f5940dad62f6ef27e2e579", "94fcc68673ad4a604c179d1a9f99b384999f4aba84896369912480ae2380a918"},
      {"cross-linear-rgb", true, 1, 1, "d335c0e8c3f542148e647ae1f8fb1c150da8c571ac4355235798ea3b01134a34", "76f95ee2d2eabbba2d35b24cdc73c0d149946078600248c032512c536650c343"},
  }};
  for (const auto& item : cases) {
    const bool alternate = item.alternate;
    const auto render = [&]() {
      noisemaker::glsl::Bindings bindings;
      bindings.set_uniform("COLOR_MODE", item.color_mode);
      bindings.set_uniform("NOISE_TYPE", item.noise_type);
      bindings.set_uniform("resolution", noisemaker::glsl::Vec2(
          static_cast<float>(alternate ? 6 : 5), static_cast<float>(alternate ? 5 : 4)));
      bindings.set_uniform("time", (alternate ? static_cast<double>(static_cast<float>(-1.5)) : static_cast<double>(static_cast<float>(2.75))));
      bindings.set_uniform("seed", (alternate ? std::int32_t{7} : std::int32_t{91}));
      bindings.set_uniform("tileOffset", (alternate ? noisemaker::glsl::Vec2(static_cast<float>(0), static_cast<float>(0)) : noisemaker::glsl::Vec2(static_cast<float>(2), static_cast<float>(1))));
      bindings.set_uniform("fullResolution", (alternate ? noisemaker::glsl::Vec2(static_cast<float>(6), static_cast<float>(5)) : noisemaker::glsl::Vec2(static_cast<float>(11), static_cast<float>(9))));
      bindings.set_uniform("noiseScale", (alternate ? static_cast<double>(static_cast<float>(42)) : static_cast<double>(static_cast<float>(100))));
      bindings.set_uniform("refractAmt", (alternate ? static_cast<double>(static_cast<float>(67)) : static_cast<double>(static_cast<float>(33))));
      bindings.set_uniform("speed", (alternate ? static_cast<double>(static_cast<float>(100)) : static_cast<double>(static_cast<float>(13))));
      bindings.set_uniform("hueRotation", (alternate ? static_cast<double>(static_cast<float>(35)) : static_cast<double>(static_cast<float>(270))));
      bindings.set_uniform("hueRange", (alternate ? static_cast<double>(static_cast<float>(90)) : static_cast<double>(static_cast<float>(55))));
      bindings.set_uniform("intensity", (alternate ? static_cast<double>(static_cast<float>(-75)) : static_cast<double>(static_cast<float>(40))));
      bindings.set_uniform("ridges", (alternate ? true : false));
      bindings.set_uniform("wrap", (alternate ? false : true));
      return noisemaker::run_pass(noisemaker::generated::bind_classicNoisedeck_moodscape_moodscape(bindings),
          static_cast<std::size_t>((alternate ? static_cast<double>(static_cast<float>(6)) : static_cast<double>(static_cast<float>(5)))), static_cast<std::size_t>((alternate ? static_cast<double>(static_cast<float>(5)) : static_cast<double>(static_cast<float>(4)))),
          static_cast<float>((alternate ? static_cast<double>(static_cast<float>(-1.5)) : static_cast<double>(static_cast<float>(2.75)))), static_cast<float>((alternate ? std::int32_t{7} : std::int32_t{91})));
    };
    const auto first = render();
    const auto second = render();
    const auto actual_float = hex(sha256(little_endian_float_bytes(first)));
    const auto actual_rgba = hex(sha256(first.to_rgba8()));
    if (actual_float != item.float_sha256 || actual_rgba != item.rgba_sha256) {
      throw std::runtime_error(std::string(item.name) + " float=" + actual_float + " rgba=" + actual_rgba);
    }
    require_repeat(first, second);
  }
}

TEST(typed_shapes3d_runtime_enum_values_match_current_cpu) {
 using namespace noisemaker;
 struct Case { const char* name; int blend, shape_a, shape_b; bool variant;
               const char* f32; const char* rgba; };
 const std::array<Case,28> cases{{
    {"default", 10, 30, 10, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"parameter", 10, 30, 10, true, "cc607f450679ad60fdf9c19b6dbeeb54d34870b54f7f7d1740061fcee35360f5", "5926466c10205be14fcc6f15722a7f312b02533913460aca9ba3d8d559faec31"},
    {"blend-51", 51, 30, 10, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"blend-50", 50, 30, 10, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"blend-40", 40, 30, 10, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"blend-26", 26, 30, 10, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"blend-25", 25, 30, 10, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"blend-20", 20, 30, 10, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"blend-10", 10, 30, 10, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"blend-30", 30, 30, 10, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"a-70", 10, 70, 10, false, "60f51d108b624bd4f1cc6dd5aa5b922a84db659cb737c4b2a5e1700b6b97c431", "e83ea9560ea3d976c90a17808a0af4b165632c61bf5cddb55151fe0d9792da55"},
    {"a-60", 10, 60, 10, false, "420535a1acf9668ea325df92a74c886c88364dc489677268524158af86644e1f", "cf4164f3cff5997433e98c04655124cbd7d64c95e0db3188f313ccb843e2f5f0"},
    {"a-10", 10, 10, 10, false, "0d60c1f4d8c66e614fdbd975922da2dcb83bb6e98a189b67ca4477cf05d95732", "6eacf6bbb60bbd41bc99906da2650c47794bdb4dbd9ac9c1d8f04b43df9fed30"},
    {"a-50", 10, 50, 10, false, "fe7c35631ad7cf906d67895b05c75f98184bd222b04f26efa10c5fda1dba8b02", "5577ca96b3cd5b8661969fedaf16771e84b29e8762f8030beeb81a1b6fcab742"},
    {"a-40", 10, 40, 10, false, "29bf0ecd8663541a971aec301e5feb93d3933e6b9d747b60cc18f1d896fcad74", "a22ccbbb307feb46f47c13dab5ff47b0c41594943378bb1d120c873b6ce93305"},
    {"a-80", 10, 80, 10, false, "a75aa0e4f0122cd8809a38a155f3a9b484e0b038a08f17eb9ef2f118ae64f51f", "5a227a2f7e521ce02ef8cff095440a0257a11dbe4680abf60606b9ce79c9f5a7"},
    {"a-20", 10, 20, 10, false, "c07cabcae9a39e42a1c16e1da1a37107dcf2a4380a6c0345579a590473f745ad", "e52350f806fa69d4be152a2254affc055982aebcdc22107ba82418a73717e623"},
    {"a-31", 10, 31, 10, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"a-30", 10, 30, 10, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"b-70", 10, 30, 70, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"b-60", 10, 30, 60, false, "201c7b5344f621c1bf2223829aba6e4b3c9aeb0bf78b8c848a1faf324b751b4d", "05a1df6e7f693b2d3028926587059a16582e61a196dac2366276ac17310e6653"},
    {"b-10", 10, 30, 10, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"b-50", 10, 30, 50, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"b-40", 10, 30, 40, false, "ead24ef66e57c6a89e6c9b96748c2b4f37c3c3bb72fb622131ce91ad4c5932e2", "ace14771c5806d73a42869302bd7bfcd36933c4681eeec1ad8b3e0f7de6c8833"},
    {"b-80", 10, 30, 80, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"b-20", 10, 30, 20, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"b-31", 10, 30, 31, false, "affaf610706831bee77b5210c0927dcf5a562acaa139e5cb8f81ba25b5230959", "c49fa31670eefde18354c6335fb3db86732db4a55f42653dd53bd000b76f9ff7"},
    {"b-30", 10, 30, 30, false, "6ed8c0b522ec55a2ae8f4902e2f0f4cb4f9de562bdecfdb68d6597d0d5324cb1", "5ec4c1d31460abb6b852729c1d402a6d45c170ec48354bcd4868cacb55e09b61"},
 }};
 for(const auto& item : cases) {
 const int blend=item.blend, shapeA=item.shape_a, shapeB=item.shape_b;
 const bool variant=item.variant;
 constexpr std::size_t width=5,height=4;
 Surface input(width,height);
 for(std::size_t i=0;i<width*height;++i){input.data()[i*4]=f32(static_cast<double>((i*11+3)%23)/23);input.data()[i*4+1]=f32(static_cast<double>((i*7+5)%29)/29);input.data()[i*4+2]=f32(static_cast<double>((i*13+1)%31)/31);input.data()[i*4+3]=f32(.4+static_cast<double>(i%4)*.15);}
 const auto original = little_endian_float_bytes(input);
 glsl::Bindings b;
 b.set_uniform("BLEND_MODE",std::int32_t(blend));b.set_uniform("SHAPE_A",std::int32_t(shapeA));b.set_uniform("SHAPE_B",std::int32_t(shapeB));
 b.set_uniform("resolution",glsl::Vec2(width,height));b.set_uniform("fullResolution",glsl::Vec2(width,height));b.set_uniform("tileOffset",glsl::Vec2(0));
 b.set_uniform("time",double(f32(.375)));b.set_uniform("shapeAScale",variant?45.0:64.0);b.set_uniform("shapeBScale",variant?36.0:27.0);
 b.set_uniform("shapeAThickness",variant?9.0:5.0);b.set_uniform("shapeBThickness",variant?7.0:5.0);b.set_uniform("smoothness",variant?12.0:1.0);
 b.set_uniform("spin",variant?35.0:0.0);b.set_uniform("flip",variant?-25.0:0.0);b.set_uniform("spinSpeed",2.0);b.set_uniform("flipSpeed",2.0);
 b.set_uniform("repetition",variant);b.set_uniform("animation",std::int32_t(1));b.set_uniform("flythroughSpeed",0.0);b.set_uniform("spacing",10.0);
 b.set_uniform("cameraDist",8.0);b.set_uniform("bgColor",glsl::DVec3(f32(.1),f32(.3),f32(.6)));b.set_uniform("bgAlpha",15.0);
 b.set_uniform("colorMode",std::int32_t(variant?1:10));b.set_uniform("paletteMode",std::int32_t(0));
 b.set_uniform("paletteOffset",glsl::DVec3(f32(.83),f32(.6),f32(.63)));b.set_uniform("paletteAmp",glsl::DVec3(f32(.5),f32(.5),f32(.5)));
 b.set_uniform("paletteFreq",glsl::DVec3(f32(1),f32(1),f32(1)));b.set_uniform("palettePhase",glsl::DVec3(f32(.3),f32(.1),f32(0)));
 b.set_uniform("cyclePalette",std::int32_t(1));b.set_uniform("rotatePalette",0.0);b.set_uniform("repeatPalette",1.0);b.set_uniform("weight",variant?35.0:0.0);
 b.set_texture("inputTex",input);

 const auto kernel=generated::bind_classicNoisedeck_shapes3d_shapes3d(b);
 const auto first=run_pass(kernel,width,height,f32(.375),17);
 const auto second=run_pass(kernel,width,height,f32(.375),17);
 REQUIRE(little_endian_float_bytes(input)==original);
 REQUIRE(little_endian_float_bytes(first)==little_endian_float_bytes(second));
 const auto actual=hex(sha256(little_endian_float_bytes(first)));
 if(actual!=item.f32) throw std::runtime_error(std::string(item.name)+" float32 hash: "+actual);
 REQUIRE(hex(sha256(first.to_rgba8()))==item.rgba);
 }
}

TEST(typed_emboss_runtime_cpu9f3_exact) {
  struct Case { const char* name; std::size_t width, height; int phase, style;
    float tile_x, tile_y, full_x, full_y; double amount, angle, emboss_height, color_amount, render_scale;
    const char* f32; const char* rgba; };
  const std::array<Case, 4> cases{{
    {"wide-STYLE0", 9U, 6U, 3, 0, 0.0f, 0.0f, 9.0f, 6.0f, 1.399999976158142, 135.0, 2.0, 70.0, 1.0, "75ace6771f2c1d16ac9f44f72e492cef21f94a28af88289fa97a0ac7a1dabf13", "ada59f9a595ccf9b0c5d7c6707050cec9065ac0e568af8c2adeee6b173e53337"},
    {"wide-STYLE1", 9U, 6U, 3, 1, 0.0f, 0.0f, 9.0f, 6.0f, 1.399999976158142, 135.0, 2.0, 70.0, 1.0, "b9c9417d8b00517933b6082a1616164ed99e6d27b0cb3e83812acfdabcd1c6d4", "42b2a9a9d6bc018330bfa03b662f3effdeb1c232249b8c71c7622c321bc065ea"},
    {"tiled-STYLE0", 13U, 9U, 4, 0, 3.0f, 2.0f, 20.0f, 15.0f, 4.5, -215.0, 7.0, 35.0, 0.75, "cb84fd30becef8ea48c3a0f2f4a56d6aadc1f40e31d8c5b98660eef0b00e9a9f", "73cf6cb0da76cb1afc241d5b25f7fabca7059efe1eb946d0602bf831d38eac2d"},
    {"tiled-STYLE1", 13U, 9U, 4, 1, 3.0f, 2.0f, 20.0f, 15.0f, 4.5, -215.0, 7.0, 35.0, 0.75, "6e055f23260976e660cac1c4265375dfd9db5a90c1e8acfcdf5f0002749b5a02", "176a426fa72ae20af4aa000a0eb9174c440279c63ed850725cce64c72b054d3d"},
  }};
  for (const auto& item : cases) {
    std::vector<float> pattern(item.width * item.height * 4U);
    for (std::size_t y = 0; y < item.height; ++y) for (std::size_t x = 0; x < item.width; ++x) {
      const auto i = (y * item.width + x) * 4U;
      pattern[i] = static_cast<float>(static_cast<double>(((31U*x+17U*y+7U+19U*item.phase)%97U)+1U)/101.0);
      pattern[i+1U] = static_cast<float>(static_cast<double>(((13U*x+37U*y+11U+23U*item.phase)%89U)+2U)/97.0);
      pattern[i+2U] = static_cast<float>(static_cast<double>(((43U*x+5U*y+3U+29U*item.phase)%83U)+3U)/91.0);
      pattern[i+3U] = static_cast<float>(static_cast<double>(((7U*x+11U*y+item.phase)%29U)+5U)/37.0);
    }
    const noisemaker::Surface input(item.width, item.height, pattern);
    const auto render = [&]() {
      noisemaker::glsl::Bindings bindings;
      bindings.set_texture("inputTex", input);
      bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(item.tile_x, item.tile_y));
      bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(item.full_x, item.full_y));
      bindings.set_uniform("STYLE", std::int32_t{item.style});
      bindings.set_uniform("amount", item.amount);
      bindings.set_uniform("angle", item.angle);
      bindings.set_uniform("height", item.emboss_height);
      bindings.set_uniform("colorAmount", item.color_amount);
      bindings.set_uniform("renderScale", item.render_scale);
      return noisemaker::run_pass(noisemaker::generated::bind_filter_emboss_emboss(bindings), item.width, item.height);
    };
    const auto first = render();
    const auto second = render();
    const auto first_f32 = hex(sha256(little_endian_float_bytes(first)));
    const auto first_rgba = hex(sha256(first.to_rgba8()));
    if (first_f32 != item.f32 || first_rgba != item.rgba) {
      throw std::runtime_error(std::string(item.name) + " f32=" + first_f32 + " rgba=" + first_rgba);
    }
    REQUIRE(hex(sha256(little_endian_float_bytes(second))) == first_f32);
    REQUIRE(hex(sha256(second.to_rgba8())) == first_rgba);
    REQUIRE(std::equal(input.data().begin(), input.data().end(), pattern.begin()));
  }
}

TEST(typed_extrude_runtime_cpu9f3_exact) {
  struct Case { const char* name; std::size_t width, height; int phase, depth_source, extrude_type;
    float tile_x, tile_y, full_x, full_y; double size, depth; bool solid_front;
    const char* f32; const char* rgba; };
  const std::array<Case, 8> cases{{
    {"wide-DEPTH_SOURCE0,EXTRUDE_TYPE0", 13U, 9U, 1, 0, 0, 0.0f, 0.0f, 13.0f, 9.0f, 4.0, 60.0, true, "2769823da76429112ad41c40349a720a4e5ece03b6dafa0ea541d30ba8004071", "31c4ea799aa9bf5fea7ea1de9532133a60466135db6f65dcff41871b1b259658"},
    {"wide-DEPTH_SOURCE0,EXTRUDE_TYPE1", 13U, 9U, 1, 0, 1, 0.0f, 0.0f, 13.0f, 9.0f, 4.0, 60.0, true, "c6f8fee6dc46e4b91d4009b0ea553e8d18f328d7bcdb811e8c85e184127b7f40", "3c64aee6f85a05ebc7314bd66ce68ca7ea16ead1548177147593e2406bfe3fe5"},
    {"wide-DEPTH_SOURCE1,EXTRUDE_TYPE0", 13U, 9U, 1, 1, 0, 0.0f, 0.0f, 13.0f, 9.0f, 4.0, 60.0, true, "6921bbfe7bc6f319592eff66128024b51925c4003cad17c8b9dc879794dfbaf3", "d3049815432eabb87d143d555f9e91d7d04579bab5290e158532bee90271e05e"},
    {"wide-DEPTH_SOURCE1,EXTRUDE_TYPE1", 13U, 9U, 1, 1, 1, 0.0f, 0.0f, 13.0f, 9.0f, 4.0, 60.0, true, "e07bde6e68a3675e59f76b7bfad10cbf9e07650e705ba857d93fa2042030e3d5", "898566d1a73ec7101491780019bb3886d37dd34fea1986e3904eeae845d4b682"},
    {"tiled-DEPTH_SOURCE0,EXTRUDE_TYPE0", 9U, 6U, 4, 0, 0, 3.0f, 2.0f, 17.0f, 13.0f, 5.0, 85.0, false, "10facb6d9139a28cfffb23bc8be0434342793362c3b8e177baf594832661859e", "f206a9ee9540263d5343efd82e88ba575b9af2ee0233d3ca2f89279844d5fc34"},
    {"tiled-DEPTH_SOURCE0,EXTRUDE_TYPE1", 9U, 6U, 4, 0, 1, 3.0f, 2.0f, 17.0f, 13.0f, 5.0, 85.0, false, "ff978d49a691d22e54a07ae3ddb1b67b89895a155fd678341da7edef07e9c502", "490f4f7dd6aff54e7be2e4e3727392a52154a1010e82b84f8797bc67e2d8d02b"},
    {"tiled-DEPTH_SOURCE1,EXTRUDE_TYPE0", 9U, 6U, 4, 1, 0, 3.0f, 2.0f, 17.0f, 13.0f, 5.0, 85.0, false, "6de04778bfa7aa14b19565701ffbcd7664b443c1666c7a900b0205730f6922ac", "ffba9516c69a317c3020a435824ecc6c5ed806fd3d0aced33b94993dde6726b2"},
    {"tiled-DEPTH_SOURCE1,EXTRUDE_TYPE1", 9U, 6U, 4, 1, 1, 3.0f, 2.0f, 17.0f, 13.0f, 5.0, 85.0, false, "fcb31ac06b6b1ede3a41581f530200af233b763ec2de2f9cbf34f31ef65e24c4", "0f1ff4d35b8c776198fba0fc25558b8d1d4ec115ef341d6ecb5731a752789335"},
  }};
  for (const auto& item : cases) {
    std::vector<float> pattern(item.width * item.height * 4U);
    for (std::size_t y = 0; y < item.height; ++y) for (std::size_t x = 0; x < item.width; ++x) {
      const auto i = (y * item.width + x) * 4U;
      pattern[i] = static_cast<float>(static_cast<double>(((31U*x+17U*y+7U+19U*item.phase)%97U)+1U)/101.0);
      pattern[i+1U] = static_cast<float>(static_cast<double>(((13U*x+37U*y+11U+23U*item.phase)%89U)+2U)/97.0);
      pattern[i+2U] = static_cast<float>(static_cast<double>(((43U*x+5U*y+3U+29U*item.phase)%83U)+3U)/91.0);
      pattern[i+3U] = static_cast<float>(static_cast<double>(((7U*x+11U*y+item.phase)%29U)+5U)/37.0);
    }
    const noisemaker::Surface input(item.width, item.height, pattern);
    const auto render = [&]() {
      noisemaker::glsl::Bindings bindings;
      bindings.set_texture("inputTex", input);
      bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(item.tile_x, item.tile_y));
      bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(item.full_x, item.full_y));
      bindings.set_uniform("DEPTH_SOURCE", std::int32_t{item.depth_source});
      bindings.set_uniform("EXTRUDE_TYPE", std::int32_t{item.extrude_type});
      bindings.set_uniform("resolution", noisemaker::glsl::Vec2(static_cast<float>(item.width), static_cast<float>(item.height)));
      bindings.set_uniform("size", item.size);
      bindings.set_uniform("depth", item.depth);
      bindings.set_uniform("solidFront", item.solid_front);
      return noisemaker::run_pass(noisemaker::generated::bind_filter_extrude_extrude(bindings), item.width, item.height);
    };
    const auto first = render();
    const auto second = render();
    const auto first_f32 = hex(sha256(little_endian_float_bytes(first)));
    const auto first_rgba = hex(sha256(first.to_rgba8()));
    if (first_f32 != item.f32 || first_rgba != item.rgba) {
      throw std::runtime_error(std::string(item.name) + " f32=" + first_f32 + " rgba=" + first_rgba);
    }
    REQUIRE(hex(sha256(little_endian_float_bytes(second))) == first_f32);
    REQUIRE(hex(sha256(second.to_rgba8())) == first_rgba);
    REQUIRE(std::equal(input.data().begin(), input.data().end(), pattern.begin()));
  }
}

// CPU9f3 Synth Shape runtime enum witnesses from attention-cpp-shape-runtime-oracles.json.
TEST(typed_shape_runtime_cpu9f3_exact) {
  struct Case { const char* name; int loop_a, loop_b; bool alternate;
    const char* f32; const char* rgba; };
  const std::array<Case, 55> cases{{
    {"default", 40, 30, false, "52de2cc43f3526e3cf24b8d55fefd065e240796caa2aceeba800970d1adc8e46", "85893d70f9189e286166b4195a7a9807fbf3fa0799d19327c759f596b131a035"},
    {"A-10", 10, 30, false, "2ac5385440000c0fc75144175b5fc7c53c81fdffd5162e6b033d5ba6d37aecbf", "edc149ddfec55e8ceba990181cbc5ce7bc290d36d42e0ed36cda91df6e7a2539"},
    {"A-20", 20, 30, false, "9c1eadfb3eb316517e585e4a2905291633bc17cd0df5e4ca9afd069e282c3292", "89e5a2bd5a2062962eee1513040476ea362381b01687f8856f8e1f14ca66bf6d"},
    {"A-30", 30, 30, false, "374aea7685484a60d9310edf6e202e388bd3645d496fd137b9b53b2986ff6968", "b1e272d950c6c8008239ec459216c2153b4434421551be94f0ae8ae9bd04c014"},
    {"A-40", 40, 30, false, "52de2cc43f3526e3cf24b8d55fefd065e240796caa2aceeba800970d1adc8e46", "85893d70f9189e286166b4195a7a9807fbf3fa0799d19327c759f596b131a035"},
    {"A-50", 50, 30, false, "a0d1b4d27aa6accd437d9ddde2868556a6a5513e56f5807619ba25fddb5e6acb", "80ceaa95a85b1b3ea4fefb42d46f4874cfffca1f126101ba3d8d635f8142cb98"},
    {"A-60", 60, 30, false, "4d0c856ac3d1894eca0d5ad350b995054c9916dad54991cb8e6246f5d2395df7", "24c5ed247c632961e086fc65cc86532f8a9e8a4462c719f600bf65a164caa180"},
    {"A-70", 70, 30, false, "b98d0a5e7d2e0e78707eba4a004e5c75a0ca955d3596ff71e70d330321783ee1", "a28b65f745c04af4a6fee74de175212007e05540275248aebb26c6835dd306de"},
    {"A-80", 80, 30, false, "678fe44cb0a5dfab0456e853870995e1f8ee236dbba372a4fce360ccbd3720b0", "94a912a37b72f5dbc58b28949ace19f1f978f2dab869835e8ac4de3b56e8de33"},
    {"A-90", 90, 30, false, "fb461a4d9b7c020e6a659893be72b98f01d466b71cc8d3340a6bcbdae1919680", "0f6ae458379f3ae7a20685886fad4d8ba6587b82bdc97e89e321f26f678a5f3b"},
    {"A-100", 100, 30, false, "d800beb96859a03a88ab3af9b6078a6d9b33b6402847ee3b87ed5835cebfeee5", "cfc077c01012386ed5b2718650d5d9a9eec94a2004f57f4a2a217975c1d0b64f"},
    {"A-110", 110, 30, false, "0c5cf75f7358b8117d6531f397a55aee6e782f663546b55cc8885632a493e707", "45164afc3f1a7917fc36a89e36c98c14597a705dccbd5d4b7bdeb0b5ab787db6"},
    {"A-120", 120, 30, false, "f77df82e2170536750e69adc70317c8bfe303893b7f78a8e5febe160b78f3ea8", "9b26f38bd8edbf0d882ef69aea56db035fa1511f8da8cdb801d62948a2fd195e"},
    {"A-200", 200, 30, false, "6f29fdd56e9939c87aa05cb01f07623afb53d442b794b0c1b21ca6631c3eff54", "36d6b0bd5f7a5c653252e84d50cbf75c392f73698fe2b8df371a90fd43da7b90"},
    {"A-210", 210, 30, false, "09ab1e0718de7f6f8710194c8132f4a4582b75701adce5e7bca6856859d95e5d", "c345e6d7d9d6883fc92426ff499054b98bde6c5102d699cba0edef0a2ab3e9c6"},
    {"A-300", 300, 30, false, "7e76be71ccbe8f83ce00daf2f3fd1d5312eb744d0702f4dc5397d7f3836cfb0f", "bcc9e9b42f2064b4908c743edd55ee231b3324269acd1eef25db1c431b4e888a"},
    {"A-310", 310, 30, false, "7e76be71ccbe8f83ce00daf2f3fd1d5312eb744d0702f4dc5397d7f3836cfb0f", "bcc9e9b42f2064b4908c743edd55ee231b3324269acd1eef25db1c431b4e888a"},
    {"A-320", 320, 30, false, "7e76be71ccbe8f83ce00daf2f3fd1d5312eb744d0702f4dc5397d7f3836cfb0f", "bcc9e9b42f2064b4908c743edd55ee231b3324269acd1eef25db1c431b4e888a"},
    {"A-330", 330, 30, false, "7e76be71ccbe8f83ce00daf2f3fd1d5312eb744d0702f4dc5397d7f3836cfb0f", "bcc9e9b42f2064b4908c743edd55ee231b3324269acd1eef25db1c431b4e888a"},
    {"A-340", 340, 30, false, "7e76be71ccbe8f83ce00daf2f3fd1d5312eb744d0702f4dc5397d7f3836cfb0f", "bcc9e9b42f2064b4908c743edd55ee231b3324269acd1eef25db1c431b4e888a"},
    {"A-350", 350, 30, false, "7e76be71ccbe8f83ce00daf2f3fd1d5312eb744d0702f4dc5397d7f3836cfb0f", "bcc9e9b42f2064b4908c743edd55ee231b3324269acd1eef25db1c431b4e888a"},
    {"A-360", 360, 30, false, "7e76be71ccbe8f83ce00daf2f3fd1d5312eb744d0702f4dc5397d7f3836cfb0f", "bcc9e9b42f2064b4908c743edd55ee231b3324269acd1eef25db1c431b4e888a"},
    {"A-370", 370, 30, false, "c449685e49434e984ce7e90c6f4353fc85430f66d007013805b8b4abae06a793", "187191cdd8b0d7964d2b5861c316bb129910fe244db086cdebcae1dfaca52c80"},
    {"A-380", 380, 30, false, "cc866a4b90f8fe3dedb3c9ab78dbcdaf7df71a6c295e80b6b8ad502fee405e29", "4281c62cf44f30c828e8483231bc23dae6db7db37b0f6511fe205e0bf25ac68c"},
    {"A-400", 400, 30, false, "d2dffebe8d367236c44c263348059f6f1958b28b9bad0738b194bd987cd4a5ef", "a6d0c9f0ccd64f6aae0e74a3326cac4672b88e76e2f64d06a6981ec2e2a2a4f1"},
    {"A-410", 410, 30, false, "b667630b7170ec434b3316144882885616cef8e24fac036548ea09a3b5a76da0", "970ae452ab0db82730053b90f51483804c2fe401058060988e00385e09d4263f"},
    {"B-10", 40, 10, false, "9e2f7941a0c5b97af11594f53f1c99009402bef6165fc66c534fb6a78ff1b76e", "3d08e0559d09512eff82b1bdd99c9141b776ccff3fcab00e75ca6e35d8514a38"},
    {"B-20", 40, 20, false, "9f7db26436c4d66c9eb4588200e953a53d3eb963af3d6e462c74ba3e6662bfe8", "2c1f847050e2f11ce7b2e43b970c25553c46d256d89cdd2f43f44baabbf02a14"},
    {"B-30", 40, 30, false, "52de2cc43f3526e3cf24b8d55fefd065e240796caa2aceeba800970d1adc8e46", "85893d70f9189e286166b4195a7a9807fbf3fa0799d19327c759f596b131a035"},
    {"B-40", 40, 40, false, "babc5a414e121daf99b7ecd44529cb90d91fea97e14d088f9344502f415ce767", "e952d5c43159e63e3f6de9c0f68096a07b7911454323b7d0622832504d0a4f91"},
    {"B-50", 40, 50, false, "39ed4e955e71b3693f620ef87bd15c300547b9dbd7a163a6aeed00703eff79d3", "54c78acb1724fa9c8d3806a47ebf52e4200ddba12f556f7f3a85667148f51c4e"},
    {"B-60", 40, 60, false, "27462f01ad8cfb77bac094c06bc8f04378e8613edbe48eed069d8c328a292e63", "0716816239c831cab5f252d4896bc578bb12869a1bd1a5f209d3fc8c87cf6d84"},
    {"B-70", 40, 70, false, "2d46bbebc994a7dfe730930cf69f204dfdcb234e95c0c2c6000ba48cc07b8e1b", "8c3a47866a2bbffef0a9ea07293414e894e433f88185568f5ef471fb1ac2fe51"},
    {"B-80", 40, 80, false, "e1ac5bfe4e271e7e190e3b9f62ecabeb6c9e51c5756ff57cfe48bafd41180322", "e39924dfd5ec9fa7cc9bb60cbadd2829a858f9002333c5e46b8bcdda0dce62a4"},
    {"B-90", 40, 90, false, "744201f3e10c9dcbb26d6a6bf9865a0c632150078447f7cd31f6d97583e0d73e", "623ae3a8090be160a56ff0afc1759661805b7579e29054ad62e959cab5337072"},
    {"B-100", 40, 100, false, "5b4b21239c3097825074f244cd6824a79820c70ec443beb39d4f00a2a14f2933", "13e4a7ea0a08f607f0eb833aa0cc04a1777fb66ba64f25b552b76545ec99673b"},
    {"B-110", 40, 110, false, "cb6fd41120dc5d33afa08835dfdec1bc9352e261506b9258b9596786a6788607", "b24e28332799c91b0fe06cf8c2f47bb7a3cf7eeb6b0e7d9eb8a47c04c2de31df"},
    {"B-120", 40, 120, false, "9dcb51cff361e4dbc65455e27e006d4957f53b0a219052bf18af32062b8155fa", "d13d640e15b12bfbc3cd15add00503ed009463d10a7cd02d054042c39a77e9d5"},
    {"B-200", 40, 200, false, "5b23b490c287f96af14b9a45ed96b99536c0112c981f329cc25d54c283bde87f", "525b68fbd10f32eef635c41313dd546bcf0957cce92bde7846949746e9e02b8c"},
    {"B-210", 40, 210, false, "db744486435cdb21b0c854538b9d93f7175dd6d797a9e10e9827e6877b647b8c", "3d57edc5fb26582519fa7c63a71a9b9065550009fff1eed6d2b6f25909356d35"},
    {"B-300", 40, 300, false, "9fe3a9ccb9540ef30bc7cd8308afbb87878c6604c117049308e73a0b3c8c246e", "bb95f8cfcbd0f8158f3dc66823a0dd7a7f1faafd1a4a1dcf3dd0bb5ead1b44bd"},
    {"B-310", 40, 310, false, "55d70c7ba835fedb41ba02531b358965c2db2ff69aaa1b99300cac169ba0540b", "bb95f8cfcbd0f8158f3dc66823a0dd7a7f1faafd1a4a1dcf3dd0bb5ead1b44bd"},
    {"B-320", 40, 320, false, "55d70c7ba835fedb41ba02531b358965c2db2ff69aaa1b99300cac169ba0540b", "bb95f8cfcbd0f8158f3dc66823a0dd7a7f1faafd1a4a1dcf3dd0bb5ead1b44bd"},
    {"B-330", 40, 330, false, "9fe3a9ccb9540ef30bc7cd8308afbb87878c6604c117049308e73a0b3c8c246e", "bb95f8cfcbd0f8158f3dc66823a0dd7a7f1faafd1a4a1dcf3dd0bb5ead1b44bd"},
    {"B-340", 40, 340, false, "9fe3a9ccb9540ef30bc7cd8308afbb87878c6604c117049308e73a0b3c8c246e", "bb95f8cfcbd0f8158f3dc66823a0dd7a7f1faafd1a4a1dcf3dd0bb5ead1b44bd"},
    {"B-350", 40, 350, false, "9fe3a9ccb9540ef30bc7cd8308afbb87878c6604c117049308e73a0b3c8c246e", "bb95f8cfcbd0f8158f3dc66823a0dd7a7f1faafd1a4a1dcf3dd0bb5ead1b44bd"},
    {"B-360", 40, 360, false, "9fe3a9ccb9540ef30bc7cd8308afbb87878c6604c117049308e73a0b3c8c246e", "bb95f8cfcbd0f8158f3dc66823a0dd7a7f1faafd1a4a1dcf3dd0bb5ead1b44bd"},
    {"B-370", 40, 370, false, "191be6b5eee8e1736cc488987ae919e5cf5742388789b298fef22b9413bc1b79", "53d2211722dd68db85751403e2c0c8b7f03426652faea43210b3841b486ac382"},
    {"B-380", 40, 380, false, "c67aa6f75ce222c50b3abca39a313a6e40cc857a646e97153ed7a53ea06b02d2", "3e02e42f8671140fec258e5d476554e6238f630b851dbef1a9346c797dd5e892"},
    {"B-400", 40, 400, false, "ea65133c5062fb34c7671acf37b32775accacd994e81c37f5b84cbd32257b527", "58b3615fd934fd6564c00b52107d60f7d80d62111f05f44c09f67b396be815a5"},
    {"B-410", 40, 410, false, "90491a1fcd489447c2d7065846a3c3a5ed3ce941028c1335816d5352db989b5a", "79b4a70a11c64016ad8e528f11aa5f3f2e20e5c35fafb8b1d429a03f0f1d5b7e"},
    {"cross-300-350", 300, 350, true, "8c03c7a19a599363fd1405efa35472cc570c834d600796fe02f811fa4b7d5ff6", "bed606f5a08966780efef737001d64558c71cad03cb71ba79556c7567e5fef7f"},
    {"cross-370-400", 370, 400, true, "892508f8b348d9a34ce1329830b33bc6ff37dccf6e669ad827aa04c3a2634897", "a46fb02bb6cfabd395bac4407f8a99aed8ec5b9698f969bb65688e0f8ad287c6"},
    {"cross-200-210", 200, 210, true, "edff2a1b95f3947931b8e671297dca7cfb42849e1d0a41db1bd9b1271bc3003f", "cf9cde6366acf89f2ef4f6b3e36adc2c83f993f1f207bccafddce2c4980461e0"},
    {"cross-410-110", 410, 110, true, "086428c421f77a9288246f34b50cb9d5ed93ad6d5c3cc380176b7541901bcf5a", "b3e2d94908a99636b793aaab4f2fe907ff06e74d668918117e1b54c58f3a1dfb"},
  }};
  for (const auto& item : cases) {
    const auto width = item.alternate ? 11U : 16U;
    const auto height = item.alternate ? 7U : 9U;
    const noisemaker::glsl::Vec2 tile = item.alternate ? noisemaker::glsl::Vec2(0.0f, 0.0f) : noisemaker::glsl::Vec2(2.0f, 1.0f);
    const noisemaker::glsl::Vec2 full = item.alternate ? noisemaker::glsl::Vec2(11.0f, 7.0f) : noisemaker::glsl::Vec2(22.0f, 15.0f);
    const auto render = [&]() {
      noisemaker::glsl::Bindings bindings;
      bindings.set_uniform("LOOP_A_OFFSET", std::int32_t{item.loop_a});
      bindings.set_uniform("LOOP_B_OFFSET", std::int32_t{item.loop_b});
      bindings.set_uniform("resolution", noisemaker::glsl::Vec2(static_cast<float>(width), static_cast<float>(height)));
      bindings.set_uniform("tileOffset", tile);
      bindings.set_uniform("fullResolution", full);
      bindings.set_uniform("time", item.alternate ? -1.25 : 0.375);
      bindings.set_uniform("seed", item.alternate ? std::int32_t{13} : std::int32_t{7});
      bindings.set_uniform("wrap", !item.alternate);
      bindings.set_uniform("loopAScale", item.alternate ? 20.0 : 37.0);
      bindings.set_uniform("loopBScale", item.alternate ? 75.0 : 61.0);
      bindings.set_uniform("speedA", item.alternate ? -60.0 : 50.0);
      bindings.set_uniform("speedB", item.alternate ? 80.0 : -25.0);
      return noisemaker::run_pass(noisemaker::generated::bind_synth_shape_shape(bindings), width, height);
    };
    const auto first = render();
    const auto second = render();
    const auto f32 = hex(sha256(little_endian_float_bytes(first)));
    const auto rgba = hex(sha256(first.to_rgba8()));
    if (f32 != item.f32 || rgba != item.rgba) {
      throw std::runtime_error(std::string(item.name) + " f32=" + f32 + " rgba=" + rgba);
    }
    REQUIRE(hex(sha256(little_endian_float_bytes(second))) == f32);
    REQUIRE(hex(sha256(second.to_rgba8())) == rgba);
    REQUIRE(tile[0] == (item.alternate ? 0.0f : 2.0f));
    REQUIRE(full[0] == (item.alternate ? 11.0f : 22.0f));
  }
}

TEST(typed_fractal3d_power_zero_and_one_match_current_cpu_mrt) {
  // CPU 9f3 authority, factory 293 SHA-256 49002fa4a818f25ad59921a1ad4020723b7240a326b4fdbae1f8334220bbc7c5:
  // power 0 preserves Math.pow(NaN, 0) == 1; power 1 checks the NaN payload path.
  struct Case {
    int noise_type;
    double power;
    const char* color_f32;
    const char* geometry_f32;
    const char* color_rgba;
    const char* geometry_rgba;
  };
  const std::array<Case, 8> cases{{
      {0, 0.0, "ec2b545039e21a5101d407c78e457a6e2f1580ab98bcb9e6fc8ece90aa1b98af", "08fcc5e51a6f858b5b7972410fdbda914f07098851fcc7bd7c860353cb79d3df", "86fb4b02dc95d4d233f4e67a5bfb8ba5a9698ba0cb21d939d5dd0f9ab198f38a", "968b36740064676046a4f8d5e4c8f8026c731b589deb1bfea5aa40b92ddb5194"},
      {0, 1.0, "242359ed227333d1d648b7a3e7a2b77306817b2345127922c96512d95b52c225", "b444a92a5492052e52e1f326660c2c3aa6473786ab2aa55f31118a1b1006f842", "934d51bee47609abb02424515f938edd56f4ce470040778e1742d57831e3e888", "8e6221691a54f8297c08c1baf018ee73628965f5ab061e3bf33f6773674cdc6a"},
      {1, 0.0, "4d37fc81727d18e6aeadc48813c1849d48e7bff0784daf969b313323d9835957", "b86369c7bee089c0aa63065bb6129564ca1a1533344b40f65425864c3ab090b0", "1ee93cb79f87a8cc04161f45d5ce2c791cac48eb4abdfd8fe347f961b35b46d2", "247b77a151c77e71ddb096c926714ad57554d1e4ecf15d329149bdb7c6894285"},
      {1, 1.0, "63b03619882ff737444dc45e7f8e5fc4699f444f981b08cbe6ccfaeef41c91e8", "58dd7a779ef721fb935d9e44fd66f887fcef35699588b53e3d0a4dceb6ffd9bb", "13b2e3b29e258ca2ce0804729c3434819f1096e7f2d2747bd88f25b611c415c4", "4ca55d300bad98d94e5bc32cfd58100a51ad9ba2157e309200c5718d558a3574"},
      {2, 0.0, "2533eeacc5373359604c2ceb664baf72635fa6047122a70f2f7f7867df6b3df7", "9e18d8f9fec2bd0d299210db3c59fa0b652e0bb05224b89c5691a1c34045d503", "f538c19dc932cc998936e6daad3e659dd8c03d4875d1757e2a5f7f96ce562380", "296697a2dd7e32e1d981b42f09278e4f7a9f651bc87e0300af025ffd91d2cbfb"},
      {2, 1.0, "7d9ce0cb2f082701be8a33d6b2679bbb30eda8f78385fbf0c186d9ee89e2481b", "2fd3fb88cccff5a80a22e7ba0b7cccdb1a2d99e12e1c8e36d19ed3b8286590eb", "50f2c6cf697bed4c390202b803b869901356bd924a8d1b7fd3eb257a1a4db53c", "abe21df81c3b29fcbb52660eaf81089ee1590eeec148c6fd93d548b862a64b7c"},
      {3, 0.0, "b7ed47dbd53ae47b8874134278290d194b9db1d5deab023888fc207152501463", "b837100ad7a284d5ef7389776f4e013d729ed10be530fa908cecab52eb8ddc8a", "f8cea85141f962be3b9643a906db53a669476d830f1c36e76af13f666babe7c3", "1cff87476511d694a4b466395e8784423c10d6fd3fcefb6687eb3dc455be6f47"},
      {3, 1.0, "e8842a707581e10e47e91958826dc87f7da106e6c1c98ae6457706cc85079ffd", "6d711bd2b72e6a253d257eb6fac377d836f981a59231dc5e4c1895a6ab233ba9", "c0d40cb203c2bd8b87ec0882502d72ad6e46b92721d8913058b502a8a2877f14", "5addffc85fa337c088cab29f47eb54b0a8961ae680130971f396120b0ed4086c"},
  }};
  for (const auto& item : cases) {
    const auto render = [&]() {
      noisemaker::glsl::Bindings bindings;
      bindings.set_uniform("volumeSize", std::int32_t{3});
      bindings.set_uniform("noiseType", std::int32_t{item.noise_type});
      bindings.set_uniform("power", item.power);
      bindings.set_uniform("iterations", std::int32_t{6});
      bindings.set_uniform("bailout", 2.0);
      bindings.set_uniform("juliaX", 17.0);
      bindings.set_uniform("juliaY", -13.0);
      bindings.set_uniform("juliaZ", 11.0);
      bindings.set_uniform("colorMode", std::int32_t{1});
      return noisemaker::run_mrt_pass(noisemaker::generated::bind_synth3d_fractal3d_precompute(bindings), 3U, 9U);
    };
    const auto first = render();
    const auto repeated = render();
    REQUIRE(first.size() == 2U);
    REQUIRE(repeated.size() == 2U);
    const std::array<const char*, 2> expected_f32{item.color_f32, item.geometry_f32};
    const std::array<const char*, 2> expected_rgba{item.color_rgba, item.geometry_rgba};
    for (std::size_t output = 0; output < first.size(); ++output) {
      const auto f32 = hex(sha256(little_endian_float_bytes(first[output])));
      const auto rgba = hex(sha256(first[output].to_rgba8()));
      if (f32 != expected_f32[output] || rgba != expected_rgba[output]) {
        throw std::runtime_error("fractal3d type=" + std::to_string(item.noise_type) +
                                 " power=" + std::to_string(item.power) +
                                 " output=" + std::to_string(output) + " f32=" + f32 + " rgba=" + rgba);
      }
      REQUIRE(hex(sha256(little_endian_float_bytes(repeated[output]))) == f32);
      REQUIRE(hex(sha256(repeated[output].to_rgba8())) == rgba);
    }
  }
}
