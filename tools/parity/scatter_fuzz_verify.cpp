// Generic differential-sweep verifier for the six ported scatter adapters
// (dla, lenia, physarum, points_render, points_billboard_render, flow3d).
//
// Reads a binary case file written by
// docs/port-engineering/scatter-adapters/oracle/common.mjs's `CaseWriter`
// (see that file's header comment for the exact record layout -- kept in
// sync with this reader by hand, both short and reviewed together), builds
// a `glsl::Bindings` + `ScatterPass` + destination `Surface` from each
// case's bytes, calls the SAME adapter the real registry dispatches
// (`resolve_scatter_adapter(key)`, never a direct function call that could
// silently skip the registration path), and compares the resulting
// destination buffer to the JS-computed expected buffer BYTE FOR BYTE
// (`std::memcmp` over the raw float32 bytes -- distinguishes -0 from +0
// and preserves NaN-payload differences that a numeric `==` would hide).
//
// Usage:
//   scatter-fuzz-verify <adapter-key> <case-file.bin>
//
// Exit code 0 iff every case's destination buffer AND pixel count matched
// exactly. Prints a one-line summary either way.
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#include "noisemaker/effects/scatter/catalog.hpp"
#include "noisemaker/effects/scatter/registry.hpp"
#include "noisemaker/glsl_runtime.hpp"
#include "noisemaker/surface.hpp"

namespace {

std::uint8_t read_u8(std::istream& in) {
  char b;
  in.read(&b, 1);
  return static_cast<std::uint8_t>(b);
}
std::uint32_t read_u32(std::istream& in) {
  unsigned char b[4];
  in.read(reinterpret_cast<char*>(b), 4);
  return static_cast<std::uint32_t>(b[0]) | (static_cast<std::uint32_t>(b[1]) << 8) |
         (static_cast<std::uint32_t>(b[2]) << 16) | (static_cast<std::uint32_t>(b[3]) << 24);
}
double read_f64(std::istream& in) {
  unsigned char b[8];
  in.read(reinterpret_cast<char*>(b), 8);
  std::uint64_t bits = 0;
  for (int i = 7; i >= 0; --i) bits = (bits << 8) | b[i];
  double value;
  std::memcpy(&value, &bits, sizeof(value));
  return value;
}
std::string read_name(std::istream& in) {
  const std::uint8_t len = read_u8(in);
  std::string s(len, '\0');
  in.read(s.data(), len);
  return s;
}
std::vector<float> read_f32_array(std::istream& in, std::size_t count) {
  std::vector<float> out(count);
  in.read(reinterpret_cast<char*>(out.data()), static_cast<std::streamsize>(count * sizeof(float)));
  return out;
}

struct TextureCase {
  std::string name;
  std::uint32_t width = 0;
  std::uint32_t height = 0;
  bool filter_linear = false;
  std::vector<float> data;
};

}  // namespace

int main(int argc, char** argv) {
  if (argc != 3) {
    std::cerr << "usage: scatter-fuzz-verify <adapter-key> <case-file.bin>\n";
    return 2;
  }
  const std::string key = argv[1];
  const std::string path = argv[2];

  noisemaker::scatter::register_builtin_scatter_adapters();
  const noisemaker::scatter::ScatterAdapter adapter = noisemaker::scatter::resolve_scatter_adapter(key);
  if (adapter == nullptr) {
    std::cerr << "no such registered scatter adapter: " << key << "\n";
    return 2;
  }

  std::ifstream in(path, std::ios::binary);
  if (!in) {
    std::cerr << "cannot open case file: " << path << "\n";
    return 2;
  }
  char magic[4];
  in.read(magic, 4);
  if (std::memcmp(magic, "SCA1", 4) != 0) {
    std::cerr << "bad magic in case file: " << path << "\n";
    return 2;
  }
  const std::uint32_t case_count = read_u32(in);

  std::uint64_t divergent_cases = 0;
  std::uint64_t divergent_lanes = 0;
  std::uint64_t total_lanes = 0;
  std::uint64_t pixel_count_mismatches = 0;
  const std::uint64_t kMaxReportedDivergences = 20;

  for (std::uint32_t case_index = 0; case_index < case_count; ++case_index) {
    const std::uint32_t num_textures = read_u32(in);
    std::vector<TextureCase> textures(num_textures);
    for (std::uint32_t t = 0; t < num_textures; ++t) {
      textures[t].name = read_name(in);
      textures[t].width = read_u32(in);
      textures[t].height = read_u32(in);
      textures[t].filter_linear = read_u8(in) != 0;
      textures[t].data = read_f32_array(in, static_cast<std::size_t>(textures[t].width) * textures[t].height * 4U);
    }

    const std::uint32_t num_uniforms = read_u32(in);
    std::vector<std::pair<std::string, double>> uniforms(num_uniforms);
    for (std::uint32_t u = 0; u < num_uniforms; ++u) {
      uniforms[u].first = read_name(in);
      uniforms[u].second = read_f64(in);
    }

    noisemaker::scatter::ScatterPass pass;
    const std::uint8_t has_blend = read_u8(in);
    if (has_blend != 0) {
      const std::string src_factor = read_name(in);
      const std::string dst_factor = read_name(in);
      pass.blend_factors = std::make_pair(src_factor, dst_factor);
    }
    const std::uint8_t has_count = read_u8(in);
    if (has_count != 0) {
      pass.count = read_f64(in);
    }

    const std::uint32_t dest_width = read_u32(in);
    const std::uint32_t dest_height = read_u32(in);
    const std::size_t dest_lanes = static_cast<std::size_t>(dest_width) * dest_height * 4U;
    std::vector<float> dest_seed = read_f32_array(in, dest_lanes);
    std::vector<float> expected = read_f32_array(in, dest_lanes);
    const std::uint32_t expected_pixels = read_u32(in);

    // Build the Surfaces (kept alive for the whole case -- Bindings only
    // BORROWS pointers into these).
    std::vector<noisemaker::Surface> texture_surfaces;
    texture_surfaces.reserve(textures.size());
    for (const auto& tex : textures) {
      texture_surfaces.emplace_back(tex.width, tex.height, tex.data);
      if (tex.filter_linear) texture_surfaces.back().set_filter(noisemaker::TextureFilter::linear);
    }

    noisemaker::glsl::Bindings bindings;
    for (std::size_t t = 0; t < textures.size(); ++t) {
      bindings.set_texture(textures[t].name, texture_surfaces[t]);
    }
    for (const auto& [name, value] : uniforms) {
      bindings.set_uniform(name, value);
    }

    noisemaker::Surface destination(dest_width, dest_height, dest_seed);
    const std::size_t pixels = adapter(bindings, pass, destination);

    const auto got = destination.data();
    bool case_diverged = false;
    for (std::size_t lane = 0; lane < dest_lanes; ++lane) {
      total_lanes += 1;
      float got_v = got[lane];
      float expected_v = expected[lane];
      if (std::memcmp(&got_v, &expected_v, sizeof(float)) != 0) {
        divergent_lanes += 1;
        case_diverged = true;
        if (divergent_lanes <= kMaxReportedDivergences) {
          std::uint32_t got_bits = 0;
          std::uint32_t expected_bits = 0;
          std::memcpy(&got_bits, &got_v, sizeof(got_bits));
          std::memcpy(&expected_bits, &expected_v, sizeof(expected_bits));
          std::fprintf(stderr, "DIVERGENCE case=%u lane=%zu got=0x%08x expected=0x%08x (got=%g expected=%g)\n",
                       case_index, lane, got_bits, expected_bits, static_cast<double>(got_v),
                       static_cast<double>(expected_v));
        }
      }
    }
    if (pixels != expected_pixels) {
      pixel_count_mismatches += 1;
      case_diverged = true;
      if (pixel_count_mismatches <= kMaxReportedDivergences) {
        std::fprintf(stderr, "PIXEL COUNT MISMATCH case=%u got=%zu expected=%u\n", case_index, pixels,
                     expected_pixels);
      }
    }
    if (case_diverged) divergent_cases += 1;
  }

  std::printf(
      "scatter-fuzz-verify key=\"%s\" file=\"%s\" cases=%u total_lanes=%llu divergent_lanes=%llu "
      "divergent_cases=%llu pixel_count_mismatches=%llu\n",
      key.c_str(), path.c_str(), case_count, static_cast<unsigned long long>(total_lanes),
      static_cast<unsigned long long>(divergent_lanes), static_cast<unsigned long long>(divergent_cases),
      static_cast<unsigned long long>(pixel_count_mismatches));

  return (divergent_cases == 0 && pixel_count_mismatches == 0) ? 0 : 1;
}
