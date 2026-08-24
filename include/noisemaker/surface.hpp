#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace noisemaker {

enum class TextureFilter { nearest, linear };

class Surface {
 public:
  Surface(std::size_t width, std::size_t height);
  Surface(std::size_t width, std::size_t height, std::vector<float> data);

  static Surface from_rgba8(std::size_t width, std::size_t height,
                            std::span<const std::uint8_t> bytes);
  [[nodiscard]] std::size_t width() const noexcept;
  [[nodiscard]] std::size_t height() const noexcept;
  [[nodiscard]] std::span<float> data() noexcept;
  [[nodiscard]] std::span<const float> data() const noexcept;
  [[nodiscard]] TextureFilter filter() const noexcept;
  void set_filter(TextureFilter filter) noexcept;
  [[nodiscard]] Surface clone() const;
  Surface& clear(const std::array<float, 4>& color = {0, 0, 0, 0});
  [[nodiscard]] std::vector<std::uint8_t> to_rgba8() const;

 private:
  std::size_t width_;
  std::size_t height_;
  std::vector<float> data_;
  TextureFilter filter_{TextureFilter::nearest};
};

}  // namespace noisemaker
