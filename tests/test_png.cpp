#include "test_harness.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <initializer_list>
#include <stdexcept>
#include <string_view>
#include <vector>

#include <zlib.h>

#include "noisemaker/png.hpp"

namespace {

constexpr std::array<std::uint8_t, 8> signature{137, 80, 78, 71, 13, 10, 26, 10};

std::uint32_t read_u32(const std::vector<std::uint8_t>& bytes, std::size_t offset) {
  return (static_cast<std::uint32_t>(bytes[offset]) << 24U) |
         (static_cast<std::uint32_t>(bytes[offset + 1U]) << 16U) |
         (static_cast<std::uint32_t>(bytes[offset + 2U]) << 8U) |
         static_cast<std::uint32_t>(bytes[offset + 3U]);
}

std::vector<std::uint8_t> inflate_independently(const std::vector<std::uint8_t>& input) {
  std::vector<std::uint8_t> output(64U);
  uLongf output_size = static_cast<uLongf>(output.size());
  const int result = uncompress(output.data(), &output_size, input.data(), static_cast<uLong>(input.size()));
  REQUIRE(result == Z_OK);
  output.resize(static_cast<std::size_t>(output_size));
  return output;
}

void append_u32(std::vector<std::uint8_t>& bytes, std::uint32_t value) {
  bytes.push_back(static_cast<std::uint8_t>(value >> 24U));
  bytes.push_back(static_cast<std::uint8_t>(value >> 16U));
  bytes.push_back(static_cast<std::uint8_t>(value >> 8U));
  bytes.push_back(static_cast<std::uint8_t>(value));
}

void append_chunk(std::vector<std::uint8_t>& png, std::string_view type,
                  std::span<const std::uint8_t> data) {
  append_u32(png, static_cast<std::uint32_t>(data.size()));
  const std::size_t start = png.size();
  png.insert(png.end(), type.begin(), type.end());
  png.insert(png.end(), data.begin(), data.end());
  append_u32(png, static_cast<std::uint32_t>(crc32(0L, png.data() + static_cast<std::ptrdiff_t>(start),
                                                   type.size() + data.size())));
}

void append_chunk(std::vector<std::uint8_t>& png, std::string_view type,
                  std::initializer_list<std::uint8_t> data) {
  append_chunk(png, type, std::span<const std::uint8_t>(data.begin(), data.size()));
}

std::vector<std::uint8_t> deflate_independently(std::span<const std::uint8_t> input) {
  uLongf size = compressBound(static_cast<uLong>(input.size()));
  std::vector<std::uint8_t> output(static_cast<std::size_t>(size));
  REQUIRE(compress2(output.data(), &size, input.data(), static_cast<uLong>(input.size()), Z_BEST_COMPRESSION) == Z_OK);
  output.resize(static_cast<std::size_t>(size));
  return output;
}

std::vector<std::uint8_t> deflate_independently(std::initializer_list<std::uint8_t> input) {
  return deflate_independently(std::span<const std::uint8_t>(input.begin(), input.size()));
}

std::vector<std::uint8_t> make_ihdr(std::uint32_t width, std::uint32_t height, std::uint8_t depth,
                                    std::uint8_t color_type, std::uint8_t interlace = 0U) {
  std::vector<std::uint8_t> header;
  append_u32(header, width);
  append_u32(header, height);
  header.push_back(depth);
  header.push_back(color_type);
  header.push_back(0U);
  header.push_back(0U);
  header.push_back(interlace);
  return header;
}

std::vector<std::uint8_t> make_png(std::uint32_t width, std::uint32_t height, std::uint8_t color_type,
                                   std::span<const std::uint8_t> scanlines,
                                   std::span<const std::uint8_t> palette = {},
                                   std::span<const std::uint8_t> transparency = {},
                                   bool has_transparency = false) {
  std::vector<std::uint8_t> png(signature.begin(), signature.end());
  append_chunk(png, "IHDR", make_ihdr(width, height, 8U, color_type));
  if (!palette.empty()) append_chunk(png, "PLTE", palette);
  if (has_transparency || !transparency.empty()) append_chunk(png, "tRNS", transparency);
  const auto compressed = deflate_independently(scanlines);
  append_chunk(png, "IDAT", compressed);
  append_chunk(png, "IEND", {});
  return png;
}

std::vector<std::uint8_t> make_png(std::uint32_t width, std::uint32_t height, std::uint8_t color_type,
                                   std::initializer_list<std::uint8_t> scanlines,
                                   std::initializer_list<std::uint8_t> palette = {},
                                   std::initializer_list<std::uint8_t> transparency = {},
                                   bool has_transparency = false) {
  return make_png(width, height, color_type,
                  std::span<const std::uint8_t>(scanlines.begin(), scanlines.size()),
                  std::span<const std::uint8_t>(palette.begin(), palette.size()),
                  std::span<const std::uint8_t>(transparency.begin(), transparency.size()), has_transparency);
}

std::vector<std::uint8_t> forward_filter(std::span<const std::uint8_t> raw, std::size_t width,
                                         std::size_t height, std::size_t bytes_per_pixel, std::uint8_t filter) {
  const std::size_t stride = width * bytes_per_pixel;
  std::vector<std::uint8_t> output((stride + 1U) * height);
  for (std::size_t y = 0; y < height; ++y) {
    output[y * (stride + 1U)] = filter;
    for (std::size_t x = 0; x < stride; ++x) {
      const std::uint8_t current = raw[y * stride + x];
      const std::uint8_t left = x >= bytes_per_pixel ? raw[y * stride + x - bytes_per_pixel] : 0U;
      const std::uint8_t up = y > 0U ? raw[(y - 1U) * stride + x] : 0U;
      const std::uint8_t upper_left = y > 0U && x >= bytes_per_pixel ? raw[(y - 1U) * stride + x - bytes_per_pixel] : 0U;
      std::uint8_t predictor = 0U;
      if (filter == 1U) predictor = left;
      if (filter == 2U) predictor = up;
      if (filter == 3U) predictor = static_cast<std::uint8_t>((static_cast<unsigned int>(left) + up) / 2U);
      if (filter == 4U) {
        const int estimate = static_cast<int>(left) + static_cast<int>(up) - static_cast<int>(upper_left);
        const int left_distance = std::abs(estimate - static_cast<int>(left));
        const int up_distance = std::abs(estimate - static_cast<int>(up));
        const int upper_left_distance = std::abs(estimate - static_cast<int>(upper_left));
        predictor = left_distance <= up_distance && left_distance <= upper_left_distance ? left
                    : up_distance <= upper_left_distance ? up : upper_left;
      }
      output[y * (stride + 1U) + x + 1U] = static_cast<std::uint8_t>(current - predictor);
    }
  }
  return output;
}

void require_rgba(const noisemaker::Surface& surface, std::size_t width, std::size_t height,
                  const std::vector<std::uint8_t>& expected) {
  REQUIRE(surface.width() == width);
  REQUIRE(surface.height() == height);
  REQUIRE(surface.to_rgba8() == expected);
}

}  // namespace

TEST(png_encoder_writes_deterministic_valid_rgba_png) {
  const std::vector<std::uint8_t> rgba{255, 0, 0, 255, 0, 128, 255, 64};
  const auto surface = noisemaker::Surface::from_rgba8(2, 1, rgba);
  const auto first = noisemaker::encode_png(surface);
  const auto second = noisemaker::encode_png(surface);

  REQUIRE(first == second);
  REQUIRE(first.size() > signature.size());
  for (std::size_t index = 0; index < signature.size(); ++index) REQUIRE(first[index] == signature[index]);

  std::size_t offset = signature.size();
  const std::array<const char*, 3> expected_types{"IHDR", "IDAT", "IEND"};
  std::vector<std::uint8_t> idat;
  for (const char* expected_type : expected_types) {
    const std::uint32_t length = read_u32(first, offset);
    REQUIRE(offset + 12U + length <= first.size());
    REQUIRE(std::memcmp(first.data() + offset + 4U, expected_type, 4U) == 0);
    const std::uint32_t expected_crc = read_u32(first, offset + 8U + length);
    const auto actual_crc = static_cast<std::uint32_t>(crc32(0L, first.data() + offset + 4U, length + 4U));
    REQUIRE(actual_crc == expected_crc);
    if (std::memcmp(expected_type, "IHDR", 4U) == 0) {
      REQUIRE(length == 13U);
      REQUIRE(read_u32(first, offset + 8U) == 2U);
      REQUIRE(read_u32(first, offset + 12U) == 1U);
      REQUIRE(first[offset + 16U] == 8U);
      REQUIRE(first[offset + 17U] == 6U);
      REQUIRE(first[offset + 18U] == 0U);
      REQUIRE(first[offset + 19U] == 0U);
      REQUIRE(first[offset + 20U] == 0U);
    }
    if (std::memcmp(expected_type, "IDAT", 4U) == 0) {
      idat.assign(first.begin() + static_cast<std::ptrdiff_t>(offset + 8U),
                  first.begin() + static_cast<std::ptrdiff_t>(offset + 8U + length));
    }
    if (std::memcmp(expected_type, "IEND", 4U) == 0) REQUIRE(length == 0U);
    offset += 12U + length;
  }
  REQUIRE(offset == first.size());
  const std::vector<std::uint8_t> expected_scanlines{0, 255, 0, 0, 255, 0, 128, 255, 64};
  REQUIRE(inflate_independently(idat) == expected_scanlines);
}

TEST(png_decoder_round_trips_literal_rgba_surface) {
  const std::vector<std::uint8_t> expected{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
                                           13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24};
  const auto original = noisemaker::Surface::from_rgba8(3, 2, expected);
  require_rgba(noisemaker::decode_png(noisemaker::encode_png(original)), 3, 2, expected);
}

TEST(png_decoder_decodes_each_standard_rgba_filter) {
  const std::vector<std::uint8_t> expected{10, 20, 30, 40, 50, 60, 70, 80,
                                           90, 100, 110, 120, 130, 140, 150, 160};
  for (std::uint8_t filter = 0U; filter <= 4U; ++filter) {
    const auto scanlines = forward_filter(expected, 2U, 2U, 4U, filter);
    require_rgba(noisemaker::decode_png(make_png(2U, 2U, 6U, scanlines)), 2U, 2U, expected);
  }
}

TEST(png_decoder_converts_each_supported_color_type_and_transparency) {
  require_rgba(noisemaker::decode_png(make_png(1U, 1U, 0U, {0U, 7U})), 1, 1, {7, 7, 7, 255});
  require_rgba(noisemaker::decode_png(make_png(1U, 1U, 0U, {0U, 7U}, {}, {0U, 7U})), 1, 1, {7, 7, 7, 0});
  require_rgba(noisemaker::decode_png(make_png(1U, 1U, 2U, {0U, 1U, 2U, 3U})), 1, 1, {1, 2, 3, 255});
  require_rgba(noisemaker::decode_png(make_png(1U, 1U, 2U, {0U, 1U, 2U, 3U}, {}, {0U, 1U, 0U, 2U, 0U, 3U})),
               1, 1, {1, 2, 3, 0});
  require_rgba(noisemaker::decode_png(make_png(1U, 1U, 3U, {0U, 0U}, {10U, 20U, 30U}, {40U})), 1, 1, {10, 20, 30, 40});
  require_rgba(noisemaker::decode_png(make_png(1U, 1U, 4U, {0U, 7U, 9U})), 1, 1, {7, 7, 7, 9});
  require_rgba(noisemaker::decode_png(make_png(1U, 1U, 6U, {0U, 1U, 2U, 3U, 4U})), 1, 1, {1, 2, 3, 4});
}

TEST(png_decoder_rejects_present_invalid_transparency_and_nonfirst_header) {
  REQUIRE_THROWS_AS(noisemaker::decode_png(make_png(1U, 1U, 0U, {0U, 7U}, {}, {}, true)), noisemaker::PngError);
  REQUIRE_THROWS_AS(noisemaker::decode_png(make_png(1U, 1U, 6U, {0U, 1U, 2U, 3U, 4U}, {}, {}, true)), noisemaker::PngError);
  REQUIRE_THROWS_AS(noisemaker::decode_png(make_png(1U, 1U, 0U, {0U, 7U}, {}, {1U, 7U})), noisemaker::PngError);
  REQUIRE_THROWS_AS(noisemaker::decode_png(make_png(1U, 1U, 2U, {0U, 1U, 2U, 3U}, {}, {1U, 1U, 0U, 2U, 0U, 3U})),
                    noisemaker::PngError);

  const auto header = make_ihdr(1U, 1U, 8U, 2U);
  const auto compressed = deflate_independently({0U, 1U, 2U, 3U});
  std::vector<std::uint8_t> transparency_before_palette(signature.begin(), signature.end());
  append_chunk(transparency_before_palette, "IHDR", header);
  append_chunk(transparency_before_palette, "tRNS", {0U, 1U, 0U, 2U, 0U, 3U});
  append_chunk(transparency_before_palette, "PLTE", {10U, 20U, 30U});
  append_chunk(transparency_before_palette, "IDAT", compressed);
  append_chunk(transparency_before_palette, "IEND", {});
  REQUIRE_THROWS_AS(noisemaker::decode_png(transparency_before_palette), noisemaker::PngError);

  std::vector<std::uint8_t> nonfirst_header(signature.begin(), signature.end());
  append_chunk(nonfirst_header, "aBcD", {});
  append_chunk(nonfirst_header, "IHDR", header);
  REQUIRE_THROWS_AS(noisemaker::decode_png(nonfirst_header), noisemaker::PngError);
}

TEST(png_decoder_rejects_malformed_png_structure_and_format) {
  const auto valid = make_png(1U, 1U, 6U, {0U, 1U, 2U, 3U, 4U});
  auto wrong_signature = valid;
  wrong_signature[0] = 0U;
  REQUIRE_THROWS_AS(noisemaker::decode_png(wrong_signature), noisemaker::PngError);
  auto truncated = valid;
  truncated.pop_back();
  REQUIRE_THROWS_AS(noisemaker::decode_png(truncated), noisemaker::PngError);
  auto corrupt_crc = valid;
  corrupt_crc[29] ^= 1U;
  REQUIRE_THROWS_AS(noisemaker::decode_png(corrupt_crc), noisemaker::PngError);
  auto trailing = valid;
  trailing.push_back(0U);
  REQUIRE_THROWS_AS(noisemaker::decode_png(trailing), noisemaker::PngError);

  std::vector<std::uint8_t> duplicate(signature.begin(), signature.end());
  const auto header = make_ihdr(1U, 1U, 8U, 6U);
  append_chunk(duplicate, "IHDR", header);
  append_chunk(duplicate, "IHDR", header);
  REQUIRE_THROWS_AS(noisemaker::decode_png(duplicate), noisemaker::PngError);
  std::vector<std::uint8_t> unknown(signature.begin(), signature.end());
  append_chunk(unknown, "IHDR", header);
  append_chunk(unknown, "ABCD", {});
  REQUIRE_THROWS_AS(noisemaker::decode_png(unknown), noisemaker::PngError);

  for (const auto& invalid_header : {make_ihdr(1U, 1U, 4U, 6U), make_ihdr(1U, 1U, 8U, 1U), make_ihdr(1U, 1U, 8U, 6U, 1U)}) {
    std::vector<std::uint8_t> png(signature.begin(), signature.end());
    append_chunk(png, "IHDR", invalid_header);
    append_chunk(png, "IDAT", deflate_independently({0U, 1U, 2U, 3U, 4U}));
    append_chunk(png, "IEND", {});
    REQUIRE_THROWS_AS(noisemaker::decode_png(png), noisemaker::PngError);
  }
}

TEST(png_decoder_rejects_chunk_order_palette_scanline_and_size_violations) {
  const auto header = make_ihdr(1U, 1U, 8U, 6U);
  const auto compressed = deflate_independently({0U, 1U, 2U, 3U, 4U});
  std::vector<std::uint8_t> nonconsecutive(signature.begin(), signature.end());
  append_chunk(nonconsecutive, "IHDR", header);
  append_chunk(nonconsecutive, "IDAT", compressed);
  append_chunk(nonconsecutive, "aBcD", {});
  append_chunk(nonconsecutive, "IDAT", compressed);
  append_chunk(nonconsecutive, "IEND", {});
  REQUIRE_THROWS_AS(noisemaker::decode_png(nonconsecutive), noisemaker::PngError);
  std::vector<std::uint8_t> nonempty_end(signature.begin(), signature.end());
  append_chunk(nonempty_end, "IHDR", header);
  append_chunk(nonempty_end, "IDAT", compressed);
  append_chunk(nonempty_end, "IEND", {0U});
  REQUIRE_THROWS_AS(noisemaker::decode_png(nonempty_end), noisemaker::PngError);
  std::vector<std::uint8_t> missing_end(signature.begin(), signature.end());
  append_chunk(missing_end, "IHDR", header);
  append_chunk(missing_end, "IDAT", compressed);
  REQUIRE_THROWS_AS(noisemaker::decode_png(missing_end), noisemaker::PngError);
  REQUIRE_THROWS_AS(noisemaker::decode_png(make_png(1U, 1U, 3U, {0U, 1U})), noisemaker::PngError);
  REQUIRE_THROWS_AS(noisemaker::decode_png(make_png(1U, 1U, 3U, {0U, 1U}, {1U, 2U})), noisemaker::PngError);
  REQUIRE_THROWS_AS(noisemaker::decode_png(make_png(1U, 1U, 3U, {0U, 1U}, {1U, 2U, 3U})), noisemaker::PngError);
  REQUIRE_THROWS_AS(noisemaker::decode_png(make_png(1U, 1U, 4U, {0U, 1U, 2U}, {}, {0U})), noisemaker::PngError);
  REQUIRE_THROWS_AS(noisemaker::decode_png(make_png(1U, 1U, 6U, {5U, 1U, 2U, 3U, 4U})), noisemaker::PngError);
  REQUIRE_THROWS_AS(noisemaker::decode_png(make_png(1U, 1U, 6U, {0U, 1U, 2U, 3U})), noisemaker::PngError);
  REQUIRE_THROWS_AS(noisemaker::decode_png(make_png(1U, 1U, 3U, {0U, 1U}, {10U, 20U, 30U})), noisemaker::PngError);

  std::vector<std::uint8_t> too_large(signature.begin(), signature.end());
  append_chunk(too_large, "IHDR", make_ihdr(16'777'217U, 1U, 8U, 6U));
  REQUIRE_THROWS_AS(noisemaker::decode_png(too_large), std::overflow_error);
  std::vector<std::uint8_t> overinflated(signature.begin(), signature.end());
  append_chunk(overinflated, "IHDR", header);
  std::vector<std::uint8_t> megabyte(1024U * 1024U, 0U);
  append_chunk(overinflated, "IDAT", deflate_independently(megabyte));
  append_chunk(overinflated, "IEND", {});
  REQUIRE_THROWS_AS(noisemaker::decode_png(overinflated), std::overflow_error);
}

TEST(png_decoder_reports_corrupt_input_as_a_runtime_error) {
  // Corrupt *input bytes* are a runtime condition, not a caller logic error.
  // A consumer's natural `catch (const std::runtime_error&)` must catch every
  // way decode_png can reject its input, and no rejection may arrive as a
  // std::logic_error.
  const std::vector<std::uint8_t> garbage{1U, 2U, 3U, 4U};
  const std::vector<std::uint8_t> empty{};
  auto valid = make_png(1U, 1U, 6U, {0U, 1U, 2U, 3U, 4U});
  auto corrupt_crc = valid;
  corrupt_crc[29] ^= 1U;
  std::vector<std::uint8_t> too_large(signature.begin(), signature.end());
  append_chunk(too_large, "IHDR", make_ihdr(16'777'217U, 1U, 8U, 6U));

  for (const auto& input : {garbage, empty, corrupt_crc, too_large}) {
    bool runtime_caught = false;
    bool logic_caught = false;
    try {
      const auto decoded = noisemaker::decode_png(input);
      static_cast<void>(decoded);
    } catch (const std::logic_error&) {
      logic_caught = true;
    } catch (const std::runtime_error&) {
      runtime_caught = true;
    }
    REQUIRE(runtime_caught);
    REQUIRE(!logic_caught);
  }

  REQUIRE_THROWS_AS(noisemaker::decode_png(garbage), noisemaker::PngError);
  REQUIRE_THROWS_AS(noisemaker::decode_png(empty), noisemaker::PngError);
}
