#include "noisemaker/png.hpp"

#include <algorithm>
#include <array>
#include <cstdlib>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>

#include <zlib.h>

namespace noisemaker {
namespace {

constexpr std::array<std::uint8_t, 8> signature{137, 80, 78, 71, 13, 10, 26, 10};

void append_u32(std::vector<std::uint8_t>& output, std::uint32_t value) {
  output.push_back(static_cast<std::uint8_t>(value >> 24U));
  output.push_back(static_cast<std::uint8_t>(value >> 16U));
  output.push_back(static_cast<std::uint8_t>(value >> 8U));
  output.push_back(static_cast<std::uint8_t>(value));
}

void append_chunk(std::vector<std::uint8_t>& output, std::string_view type,
                  std::span<const std::uint8_t> data) {
  append_u32(output, static_cast<std::uint32_t>(data.size()));
  const std::size_t chunk_start = output.size();
  output.insert(output.end(), type.begin(), type.end());
  output.insert(output.end(), data.begin(), data.end());
  const auto crc = static_cast<std::uint32_t>(
      crc32(0L, output.data() + static_cast<std::ptrdiff_t>(chunk_start), type.size() + data.size()));
  append_u32(output, crc);
}

std::uint32_t read_u32(std::span<const std::uint8_t> bytes, std::size_t offset) {
  return (static_cast<std::uint32_t>(bytes[offset]) << 24U) |
         (static_cast<std::uint32_t>(bytes[offset + 1U]) << 16U) |
         (static_cast<std::uint32_t>(bytes[offset + 2U]) << 8U) |
         static_cast<std::uint32_t>(bytes[offset + 3U]);
}

std::uint8_t paeth(std::uint8_t left, std::uint8_t up, std::uint8_t upper_left) {
  const int estimate = static_cast<int>(left) + static_cast<int>(up) - static_cast<int>(upper_left);
  const int left_distance = std::abs(estimate - static_cast<int>(left));
  const int up_distance = std::abs(estimate - static_cast<int>(up));
  const int upper_left_distance = std::abs(estimate - static_cast<int>(upper_left));
  if (left_distance <= up_distance && left_distance <= upper_left_distance) return left;
  return up_distance <= upper_left_distance ? up : upper_left;
}

std::vector<std::uint8_t> inflate_scanlines(std::span<const std::uint8_t> compressed,
                                            std::size_t expected) {
  if (expected > max_png_decoded_bytes) {
    throw std::overflow_error("PNG size limit decoded scanlines exceed 96 MiB");
  }
  std::vector<std::uint8_t> output(expected);
  z_stream stream{};
  stream.next_in = const_cast<Bytef*>(reinterpret_cast<const Bytef*>(compressed.data()));
  stream.avail_in = static_cast<uInt>(compressed.size());
  stream.next_out = reinterpret_cast<Bytef*>(output.data());
  stream.avail_out = static_cast<uInt>(output.size());
  if (inflateInit(&stream) != Z_OK) throw PngError("PNG IDAT zlib inflate initialization failed");
  const int result = inflate(&stream, Z_FINISH);
  const uLong total_out = stream.total_out;
  const uInt remaining_input = stream.avail_in;
  inflateEnd(&stream);
  if (result == Z_BUF_ERROR && total_out == expected) {
    throw std::overflow_error("PNG size limit compressed data exceeds expected scanline length");
  }
  if (result != Z_STREAM_END) throw PngError("PNG IDAT zlib stream is invalid");
  if (remaining_input != 0U) throw PngError("PNG IDAT zlib stream has trailing compressed data");
  if (total_out != expected) throw PngError("PNG scanline length is invalid");
  return output;
}

}  // namespace

std::vector<std::uint8_t> encode_png(const Surface& surface) {
  if (surface.width() > max_png_pixels / surface.height()) {
    throw std::overflow_error("PNG size limit exceeds the 16,777,216 pixel limit");
  }
  if (surface.width() > std::numeric_limits<std::uint32_t>::max() ||
      surface.height() > std::numeric_limits<std::uint32_t>::max()) {
    throw std::overflow_error("PNG size limit exceeds IHDR dimensions");
  }
  const auto rgba = surface.to_rgba8();
  const std::size_t stride = surface.width() * 4U;
  std::vector<std::uint8_t> scanlines((stride + 1U) * surface.height());
  for (std::size_t row = 0; row < surface.height(); ++row) {
    const std::size_t destination = row * (stride + 1U);
    scanlines[destination] = 0U;
    std::copy_n(rgba.begin() + static_cast<std::ptrdiff_t>(row * stride), stride,
                scanlines.begin() + static_cast<std::ptrdiff_t>(destination + 1U));
  }

  uLongf compressed_size = compressBound(static_cast<uLong>(scanlines.size()));
  std::vector<std::uint8_t> compressed(static_cast<std::size_t>(compressed_size));
  const int result = compress2(compressed.data(), &compressed_size, scanlines.data(),
                               static_cast<uLong>(scanlines.size()), Z_BEST_COMPRESSION);
  if (result != Z_OK) throw std::runtime_error("PNG IDAT zlib compression failed");
  compressed.resize(static_cast<std::size_t>(compressed_size));

  std::array<std::uint8_t, 13> header{};
  header[0] = static_cast<std::uint8_t>(surface.width() >> 24U);
  header[1] = static_cast<std::uint8_t>(surface.width() >> 16U);
  header[2] = static_cast<std::uint8_t>(surface.width() >> 8U);
  header[3] = static_cast<std::uint8_t>(surface.width());
  header[4] = static_cast<std::uint8_t>(surface.height() >> 24U);
  header[5] = static_cast<std::uint8_t>(surface.height() >> 16U);
  header[6] = static_cast<std::uint8_t>(surface.height() >> 8U);
  header[7] = static_cast<std::uint8_t>(surface.height());
  header[8] = 8U;
  header[9] = 6U;

  std::vector<std::uint8_t> output(signature.begin(), signature.end());
  append_chunk(output, "IHDR", header);
  append_chunk(output, "IDAT", compressed);
  append_chunk(output, "IEND", {});
  return output;
}

Surface decode_png(std::span<const std::uint8_t> png) {
  if (png.size() > max_png_encoded_bytes) {
    throw std::overflow_error("PNG size limit encoded input exceeds 256 MiB");
  }
  if (png.size() < signature.size() || !std::equal(signature.begin(), signature.end(), png.begin())) {
    throw PngError("PNG signature is invalid");
  }

  bool seen_header = false;
  bool seen_palette = false;
  bool seen_transparency = false;
  bool seen_idat = false;
  bool idat_closed = false;
  bool seen_end = false;
  std::uint32_t width = 0U;
  std::uint32_t height = 0U;
  std::uint8_t bit_depth = 0U;
  std::uint8_t color_type = 0U;
  std::uint8_t interlace = 0U;
  std::vector<std::uint8_t> palette;
  std::vector<std::uint8_t> transparency;
  std::vector<std::uint8_t> idat;
  std::size_t offset = signature.size();

  while (offset < png.size()) {
    if (png.size() - offset < 12U) throw PngError("PNG chunk is truncated");
    const std::uint32_t length = read_u32(png, offset);
    const std::size_t data_length = static_cast<std::size_t>(length);
    if (data_length > png.size() - offset - 12U) throw PngError("PNG chunk is truncated");
    const std::size_t data_offset = offset + 8U;
    const std::size_t end = data_offset + data_length + 4U;
    const std::string_view type(reinterpret_cast<const char*>(png.data() + offset + 4U), 4U);
    const auto expected_crc = read_u32(png, data_offset + data_length);
    const auto actual_crc = static_cast<std::uint32_t>(crc32(0L, png.data() + offset + 4U, data_length + 4U));
    if (actual_crc != expected_crc) throw PngError("PNG chunk CRC mismatch in " + std::string(type));
    const auto data = png.subspan(data_offset, data_length);

    if (type == "IHDR") {
      if (seen_header || offset != signature.size() || length != 13U) {
        throw PngError("PNG IHDR chunk must appear exactly once and first");
      }
      seen_header = true;
      width = read_u32(data, 0U);
      height = read_u32(data, 4U);
      bit_depth = data[8U];
      color_type = data[9U];
      if (width == 0U || height == 0U) throw PngError("PNG size dimensions must be positive");
      if (height > max_png_pixels / width) throw std::overflow_error("PNG size limit exceeds 16,777,216 pixels");
      if (data[10U] != 0U || data[11U] != 0U) {
        throw PngError("PNG compression or filter method is unsupported");
      }
      interlace = data[12U];
    } else if (type == "PLTE") {
      if (!seen_header || seen_palette || seen_transparency || seen_idat || color_type == 0U || color_type == 4U ||
          length == 0U || length % 3U != 0U || length > 768U) {
        throw PngError("PNG palette chunk/order is invalid");
      }
      seen_palette = true;
      palette.assign(data.begin(), data.end());
    } else if (type == "tRNS") {
      if (!seen_header || seen_transparency || seen_idat || color_type == 4U || color_type == 6U ||
          (color_type == 3U && !seen_palette)) {
        throw PngError("PNG tRNS chunk/order is invalid");
      }
      seen_transparency = true;
      transparency.assign(data.begin(), data.end());
    } else if (type == "IDAT") {
      if (!seen_header || idat_closed) throw PngError("PNG IDAT chunks must be consecutive after IHDR");
      seen_idat = true;
      if (data.size() > max_png_encoded_bytes - idat.size()) {
        throw std::overflow_error("PNG size limit IDAT data exceeds 256 MiB");
      }
      idat.insert(idat.end(), data.begin(), data.end());
    } else if (type == "IEND") {
      if (!seen_idat || length != 0U) throw PngError("PNG IEND must be empty and follow IDAT");
      seen_end = true;
      offset = end;
      break;
    } else {
      if (seen_idat) idat_closed = true;
      if ((static_cast<unsigned char>(type[0]) & 0x20U) == 0U) {
        throw PngError("PNG critical chunk type is unsupported: " + std::string(type));
      }
    }
    offset = end;
  }

  if (!seen_header || !seen_idat || !seen_end) throw PngError("PNG requires IHDR, IDAT, and IEND chunks");
  if (offset != png.size()) throw PngError("PNG has trailing bytes after IEND");
  if (bit_depth != 8U) throw PngError("PNG bit depth must be 8");
  if (interlace != 0U) throw PngError("PNG interlace is unsupported");

  std::size_t components = 0U;
  switch (color_type) {
    case 0U: components = 1U; break;
    case 2U: components = 3U; break;
    case 3U: components = 1U; break;
    case 4U: components = 2U; break;
    case 6U: components = 4U; break;
    default: throw PngError("PNG color type is unsupported");
  }
  if (color_type == 3U && (palette.empty() || palette.size() % 3U != 0U)) {
    throw PngError("PNG indexed color requires a palette");
  }
  if (seen_transparency) {
    if ((color_type == 0U && (transparency.size() != 2U || transparency[0] != 0U)) ||
        (color_type == 2U && (transparency.size() != 6U || transparency[0] != 0U ||
                               transparency[2U] != 0U || transparency[4U] != 0U)) ||
        (color_type == 3U && (transparency.empty() || transparency.size() > palette.size() / 3U)) ||
        color_type == 4U || color_type == 6U) {
        throw PngError("PNG tRNS data is invalid for its color type");
      }
  }

  const std::size_t pixel_count = static_cast<std::size_t>(width) * static_cast<std::size_t>(height);
  const std::size_t stride = static_cast<std::size_t>(width) * components;
  const std::size_t expected = (stride + 1U) * static_cast<std::size_t>(height);
  auto filtered = inflate_scanlines(idat, expected);
  std::vector<std::uint8_t> decoded(stride * static_cast<std::size_t>(height));
  for (std::size_t y = 0U; y < height; ++y) {
    const std::size_t source_row = y * (stride + 1U);
    const std::size_t destination_row = y * stride;
    const std::uint8_t filter = filtered[source_row];
    if (filter > 4U) throw PngError("PNG scanline filter is invalid");
    for (std::size_t x = 0U; x < stride; ++x) {
      const std::uint8_t left = x >= components ? decoded[destination_row + x - components] : 0U;
      const std::uint8_t up = y > 0U ? decoded[destination_row - stride + x] : 0U;
      const std::uint8_t upper_left = y > 0U && x >= components ? decoded[destination_row - stride + x - components] : 0U;
      std::uint8_t predictor = 0U;
      if (filter == 1U) predictor = left;
      if (filter == 2U) predictor = up;
      if (filter == 3U) predictor = static_cast<std::uint8_t>((static_cast<unsigned int>(left) + up) / 2U);
      if (filter == 4U) predictor = paeth(left, up, upper_left);
      decoded[destination_row + x] = static_cast<std::uint8_t>(filtered[source_row + x + 1U] + predictor);
    }
  }

  std::vector<std::uint8_t> rgba(pixel_count * 4U);
  const std::uint16_t transparent_gray = transparency.size() == 2U ?
      static_cast<std::uint16_t>((static_cast<std::uint16_t>(transparency[0]) << 8U) | transparency[1]) : 0U;
  const std::array<std::uint16_t, 3> transparent_rgb{
      transparency.size() == 6U ? static_cast<std::uint16_t>((static_cast<std::uint16_t>(transparency[0]) << 8U) | transparency[1]) : static_cast<std::uint16_t>(0U),
      transparency.size() == 6U ? static_cast<std::uint16_t>((static_cast<std::uint16_t>(transparency[2]) << 8U) | transparency[3]) : static_cast<std::uint16_t>(0U),
      transparency.size() == 6U ? static_cast<std::uint16_t>((static_cast<std::uint16_t>(transparency[4]) << 8U) | transparency[5]) : static_cast<std::uint16_t>(0U)};
  for (std::size_t pixel = 0U; pixel < pixel_count; ++pixel) {
    const std::size_t source = pixel * components;
    const std::size_t target = pixel * 4U;
    if (color_type == 0U) {
      rgba[target] = decoded[source];
      rgba[target + 1U] = decoded[source];
      rgba[target + 2U] = decoded[source];
      rgba[target + 3U] = transparency.size() == 2U && decoded[source] == transparent_gray ? 0U : 255U;
    } else if (color_type == 2U) {
      std::copy_n(decoded.begin() + static_cast<std::ptrdiff_t>(source), 3U,
                  rgba.begin() + static_cast<std::ptrdiff_t>(target));
      rgba[target + 3U] = transparency.size() == 6U && decoded[source] == transparent_rgb[0] &&
          decoded[source + 1U] == transparent_rgb[1] && decoded[source + 2U] == transparent_rgb[2] ? 0U : 255U;
    } else if (color_type == 3U) {
      const std::size_t index = decoded[source];
      if (index >= palette.size() / 3U) throw PngError("PNG palette index is out of range");
      std::copy_n(palette.begin() + static_cast<std::ptrdiff_t>(index * 3U), 3U,
                  rgba.begin() + static_cast<std::ptrdiff_t>(target));
      rgba[target + 3U] = index < transparency.size() ? transparency[index] : 255U;
    } else if (color_type == 4U) {
      rgba[target] = decoded[source];
      rgba[target + 1U] = decoded[source];
      rgba[target + 2U] = decoded[source];
      rgba[target + 3U] = decoded[source + 1U];
    } else {
      std::copy_n(decoded.begin() + static_cast<std::ptrdiff_t>(source), 4U,
                  rgba.begin() + static_cast<std::ptrdiff_t>(target));
    }
  }
  return Surface::from_rgba8(width, height, rgba);
}

}  // namespace noisemaker
