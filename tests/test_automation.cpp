#include "test_harness.hpp"

#include <array>
#include <bit>
#include <cstdint>
#include <optional>
#include <string_view>

#include "noisemaker/graph/automation.hpp"

namespace {

using noisemaker::graph::AutomationSpec;
using noisemaker::graph::PlanValue;

PlanValue n(double value) { return PlanValue::number_value(value); }

PlanValue osc(int type, PlanValue min = n(0), PlanValue max = n(1), PlanValue speed = n(1),
              PlanValue offset = n(0), PlanValue seed = n(1)) {
  return PlanValue::oscillator_value(type, std::move(min), std::move(max), std::move(speed),
                                     std::move(offset), std::move(seed));
}

AutomationSpec range(double min, double max) { return AutomationSpec{min, max, false}; }

struct AutomationCase {
  std::string_view name;
  PlanValue value;
  std::optional<AutomationSpec> spec;
  std::array<std::uint64_t, 3> bits;  // at t = 0, 0.37, 0.91
};

}  // namespace

// Bit patterns from the CPU authority's src/runtime/automation.js
// (resolveAutomationUniform) at noisemaker-for-cpu 8ae8e2a.
TEST(automation_matches_the_cpu_authority_bit_for_bit) {
  const std::array<AutomationCase, 9> cases{{
      {"sine", osc(0, n(0.2), n(0.8), n(2), n(0.1), n(7)), range(1, 20),
       {0x40178dedfabd54e2ULL, 0x401dc87c752ec78eULL, 0x4016052c54dd26f2ULL}},
      {"tri-fm", osc(1, n(0), n(1), osc(5, n(0.25), n(0.75))), range(-180, 180),
       {0xc066800000000000ULL, 0x404d3d1c96f66fe8ULL, 0xc06308d8174ed3f0ULL}},
      {"saw-nested", osc(2, n(0), osc(0), n(3), n(-0.3), n(9)), range(0, 100),
       {0x0000000000000000ULL, 0x40510e5899ea6b26ULL, 0x400ac68d834585edULL}},
      {"sawInv", osc(3, n(0.1), n(0.9), n(-3), n(0.5)), range(0, 1),
       {0x3fe0000000000000ULL, 0x3fe2d0e560418937ULL, 0x3fd22d0e56041894ULL}},
      {"square-int", osc(4), AutomationSpec{std::nullopt, std::nullopt, true},
       {0x0000000000000000ULL, 0x0000000000000000ULL, 0x3ff0000000000000ULL}},
      {"noise", osc(5, n(0.3), n(0.6), n(1), n(0), n(5)), range(1, 100),
       {0x4049b956d9ef138cULL, 0x4042ec99fa7466ddULL, 0x40458b4293015640ULL}},
      {"noise2d", osc(6, n(0), n(1), n(1.5), n(0), n(42)), range(-5, 5),
       {0xbfe9a8f93d948878ULL, 0x400db6c876e62d74ULL, 0x40113584736436d8ULL}},
      {"noise2d-fm", osc(6, n(0), n(1), osc(1, n(0.2), n(0.9), n(2)), n(0.25), n(3)),
       AutomationSpec{0, 7, true},
       {0x4008000000000000ULL, 0x4014000000000000ULL, 0x401c000000000000ULL}},
      {"deep-fm", osc(0, n(0), n(1), osc(1, n(0), n(1), osc(2, n(0), n(1), osc(3)))), std::nullopt,
       {0x0000000000000000ULL, 0x3fd45cc244814f0cULL, 0x3fd92699698c4d0aULL}},
  }};
  constexpr std::array<double, 3> times{0.0, 0.37, 0.91};
  for (const auto& item : cases) {
    for (std::size_t index = 0; index < times.size(); ++index) {
      const double resolved = noisemaker::graph::resolve_automation(item.value, times[index], item.spec);
      if (std::bit_cast<std::uint64_t>(resolved) != item.bits[index]) {
        throw std::runtime_error(std::string(item.name) + " diverges from the authority at t=" +
                                 std::to_string(times[index]));
      }
    }
  }
}

TEST(automation_spec_follows_the_parameter_declaration) {
  using noisemaker::effects::ParameterDefinition;
  using noisemaker::effects::Value;
  ParameterDefinition plain{};
  plain.type = "float";
  auto spec = noisemaker::graph::automation_spec(&plain);
  REQUIRE(spec.has_value() && spec->min == 0.0 && spec->max == 100.0 && !spec->integer);
  ParameterDefinition bounded{};
  bounded.type = "int";
  bounded.min = Value::number_value(-5);
  bounded.max = Value::number_value(5);
  spec = noisemaker::graph::automation_spec(&bounded);
  REQUIRE(spec.has_value() && spec->min == -5.0 && spec->max == 5.0 && !spec->integer);
  ParameterDefinition choices{};
  choices.type = "int";
  choices.choices = {{"a", Value::number_value(0)}, {"b", Value::number_value(1)}};
  spec = noisemaker::graph::automation_spec(&choices);
  REQUIRE(spec.has_value() && !spec->min.has_value() && !spec->max.has_value() && spec->integer);
  ParameterDefinition color{};
  color.type = "color";
  REQUIRE(!noisemaker::graph::automation_spec(&color).has_value());
  REQUIRE(!noisemaker::graph::automation_spec(nullptr).has_value());
}
