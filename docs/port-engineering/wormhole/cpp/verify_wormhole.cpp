// Verification harness: reads wormhole-oracles.json (produced by
// wormhole_oracle_generator.mjs, driving the REAL runWormholeDeposit
// directly), runs the standalone C++ port in wormhole_deposit.hpp against
// every case, and reports exact bit-for-bit comparison results broken out
// per wrap mode, plus the direct-row function-level tables
// (wrapRepeat/wrapMirror/oklabLightness).
//
// This binary is self-contained: it depends only on json_min.hpp and
// wormhole_deposit.hpp in this same directory, and reads the oracle JSON by
// path given on argv[1]. It has no dependency on noisemaker-for-cpp's own
// build (CMake, its Surface/kernel headers, etc).
#include <bit>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <limits>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include "json_min.hpp"
#include "wormhole_deposit.hpp"

namespace {

std::string read_file(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) throw std::runtime_error("cannot open " + path);
  std::ostringstream ss;
  ss << in.rdbuf();
  return ss.str();
}

float bits_to_float(std::uint32_t bits) { return std::bit_cast<float>(bits); }
std::uint32_t float_to_bits(float value) { return std::bit_cast<std::uint32_t>(value); }

struct WrapModeStats {
  std::int64_t compared = 0;
  std::int64_t exact = 0;
  double max_abs_diff = 0.0;
  std::int64_t cases = 0;
};

wormhole::Surface surface_from_bits(std::size_t width, std::size_t height, const json_min::Array& bits) {
  wormhole::Surface s(width, height);
  if (bits.size() != s.data.size()) throw std::runtime_error("bits array size mismatch");
  for (std::size_t i = 0; i < bits.size(); ++i) {
    const auto u = static_cast<std::uint32_t>(bits[i].as_int64());
    s.data[i] = bits_to_float(u);
  }
  return s;
}

} // namespace

int run(int argc, char** argv);

int main(int argc, char** argv) {
  try {
    return run(argc, argv);
  } catch (const std::exception& e) {
    std::fprintf(stderr, "FATAL: %s\n", e.what());
    return 2;
  }
}

int run(int argc, char** argv) {
  const std::string oracle_path = argc > 1 ? argv[1] : "wormhole-oracles.json";
  const std::string text = read_file(oracle_path);
  const json_min::Value root = json_min::parse(text);

  std::printf("schema: %s\n", root.at("schema").as_string().c_str());
  std::printf("corpus_revision: %s\n", root.at("corpus_revision").as_string().c_str());

  // --- Direct-row checks: wrapRepeat / wrapMirror / oklabLightness --------
  int wrap_row_fail = 0;
  {
    const auto& wfr = root.at("wrap_function_rows");
    const auto& repeat_rows = wfr.at("wrap_repeat").as_array();
    const auto& mirror_rows = wfr.at("wrap_mirror").as_array();
    for (const auto& row : repeat_rows) {
      const auto value = row.at("value").as_int64();
      const auto size = row.at("size").as_int64();
      const auto expected = row.at("result").as_int64();
      const auto got = wormhole::wrap_repeat(value, size);
      if (got != expected) {
        wrap_row_fail += 1;
        std::printf("  MISMATCH wrap_repeat(%lld,%lld): expected %lld got %lld\n",
                    static_cast<long long>(value), static_cast<long long>(size),
                    static_cast<long long>(expected), static_cast<long long>(got));
      }
    }
    for (const auto& row : mirror_rows) {
      const auto value = row.at("value").as_int64();
      const auto size = row.at("size").as_int64();
      const auto expected = row.at("result").as_int64();
      const auto got = wormhole::wrap_mirror(value, size);
      if (got != expected) {
        wrap_row_fail += 1;
        std::printf("  MISMATCH wrap_mirror(%lld,%lld): expected %lld got %lld\n",
                    static_cast<long long>(value), static_cast<long long>(size),
                    static_cast<long long>(expected), static_cast<long long>(got));
      }
    }
    std::printf("wrap_function_rows: %zu wrapRepeat + %zu wrapMirror rows, %d mismatch(es)\n",
                repeat_rows.size(), mirror_rows.size(), wrap_row_fail);
  }

  int oklab_row_fail = 0;
  {
    const auto& rows = root.at("oklab_lightness_rows").as_array();
    for (const auto& row : rows) {
      const double r = row.at("r").as_number();
      const double g = row.at("g").as_number();
      const double b = row.at("b").as_number();
      const auto expected_bits = static_cast<std::uint32_t>(std::stoul(row.at("lightness_bits").as_string().substr(2), nullptr, 16));
      const double got = wormhole::oklab_lightness(r, g, b);
      const auto got_bits = float_to_bits(static_cast<float>(got));
      if (got_bits != expected_bits) {
        oklab_row_fail += 1;
        std::printf("  MISMATCH oklab_lightness(%g,%g,%g): expected bits 0x%08x got 0x%08x\n", r, g, b, expected_bits, got_bits);
      }
    }
    std::printf("oklab_lightness_rows: %zu rows, %d mismatch(es)\n", rows.size(), oklab_row_fail);
  }

  // --- Full-pass cases, broken out per resolved wrap mode -----------------
  std::map<std::int64_t, WrapModeStats> per_wrap;
  WrapModeStats overall;
  std::int64_t cases_with_any_mismatch = 0;
  std::vector<std::string> mismatch_report;

  const auto& cases = root.at("cases").as_array();
  for (const auto& c : cases) {
    const std::string name = c.at("name").as_string();
    const auto width = static_cast<std::size_t>(c.at("width").as_int64());
    const auto height = static_cast<std::size_t>(c.at("height").as_int64());
    const auto& u = c.at("uniforms");
    wormhole::WormholeUniforms uniforms;
    uniforms.kink = u.at("kink").as_number();
    uniforms.stride = u.at("stride").as_number();
    uniforms.rotation = u.at("rotation").as_number();
    uniforms.wrap = u.at("wrap").as_number();

    wormhole::Surface input = surface_from_bits(width, height, c.at("input_bits").as_array());
    wormhole::Surface destination;
    if (!c.at("seed_bits").is_null()) {
      destination = surface_from_bits(width, height, c.at("seed_bits").as_array());
    } else {
      destination = wormhole::Surface(width, height);
    }

    wormhole::run_wormhole_deposit(input, destination, uniforms);

    const auto& expected_bits = c.at("output_bits").as_array();
    if (expected_bits.size() != destination.data.size()) throw std::runtime_error(name + ": output size mismatch");

    const auto resolved_wrap = wormhole::to_int32_bitwise_or_zero(uniforms.wrap);
    auto& stats = per_wrap[resolved_wrap];
    stats.cases += 1;
    overall.cases += 1;

    std::int64_t case_compared = 0;
    std::int64_t case_exact = 0;
    double case_max_abs_diff = 0.0;
    for (std::size_t i = 0; i < destination.data.size(); ++i) {
      const auto expected_u = static_cast<std::uint32_t>(expected_bits[i].as_int64());
      const auto got_u = float_to_bits(destination.data[i]);
      case_compared += 1;
      if (expected_u == got_u) {
        case_exact += 1;
      } else {
        const float expected_f = bits_to_float(expected_u);
        const float got_f = destination.data[i];
        double diff = std::fabs(static_cast<double>(expected_f) - static_cast<double>(got_f));
        if (std::isnan(expected_f) || std::isnan(got_f)) diff = std::numeric_limits<double>::infinity();
        if (diff > case_max_abs_diff) case_max_abs_diff = diff;
      }
    }
    stats.compared += case_compared;
    stats.exact += case_exact;
    overall.compared += case_compared;
    overall.exact += case_exact;
    if (case_max_abs_diff > stats.max_abs_diff) stats.max_abs_diff = case_max_abs_diff;
    if (case_max_abs_diff > overall.max_abs_diff) overall.max_abs_diff = case_max_abs_diff;

    if (case_exact != case_compared) {
      cases_with_any_mismatch += 1;
      std::ostringstream line;
      line << "  MISMATCH case=" << name << " size=" << width << "x" << height
           << " wrap_uniform=" << uniforms.wrap << " resolved_wrap=" << resolved_wrap
           << " lanes_compared=" << case_compared << " lanes_exact=" << case_exact
           << " max_abs_diff=" << case_max_abs_diff;
      mismatch_report.push_back(line.str());
    }
  }

  std::printf("\n--- Per-wrap-mode comparison (0=mirror, 1=repeat, 2=clamp, other=repeat-branch) ---\n");
  for (const auto& [wrap_value, stats] : per_wrap) {
    std::printf("wrap=%lld: cases=%lld compared=%lld exact=%lld max_abs_diff=%.9g\n",
                static_cast<long long>(wrap_value), static_cast<long long>(stats.cases),
                static_cast<long long>(stats.compared), static_cast<long long>(stats.exact), stats.max_abs_diff);
  }
  std::printf("\n--- Overall ---\n");
  std::printf("cases=%lld compared=%lld exact=%lld max_abs_diff=%.9g\n",
              static_cast<long long>(overall.cases), static_cast<long long>(overall.compared),
              static_cast<long long>(overall.exact), overall.max_abs_diff);

  if (!mismatch_report.empty()) {
    std::printf("\n--- Mismatch detail (%lld case(s) with at least one differing lane) ---\n", static_cast<long long>(cases_with_any_mismatch));
    for (const auto& line : mismatch_report) std::printf("%s\n", line.c_str());
  }

  const bool ok = wrap_row_fail == 0 && oklab_row_fail == 0 && overall.exact == overall.compared;
  std::printf("\nRESULT: %s\n", ok ? "ALL BIT-EXACT" : "MISMATCHES FOUND (see detail above)");
  return ok ? 0 : 1;
}
