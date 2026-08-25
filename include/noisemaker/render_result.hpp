#pragma once

#include "noisemaker/surface.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace noisemaker {

class RenderResult final {
 public:
  [[nodiscard]] const Surface& surface() const& noexcept { return surface_; }
  [[nodiscard]] std::vector<std::uint8_t> to_rgba8() const { return surface_.to_rgba8(); }
  [[nodiscard]] std::size_t width() const noexcept { return surface_.width(); }
  [[nodiscard]] std::size_t height() const noexcept { return surface_.height(); }
  [[nodiscard]] std::size_t pass_count() const noexcept { return pass_count_; }
  [[nodiscard]] std::string_view final_route() const noexcept { return final_route_; }

 private:
  friend class Renderer;
  RenderResult(Surface surface, std::string final_route, std::size_t pass_count)
      : surface_(std::move(surface)), final_route_(std::move(final_route)), pass_count_(pass_count) {}

  Surface surface_;
  std::string final_route_;
  std::size_t pass_count_ = 0;
};

}  // namespace noisemaker
