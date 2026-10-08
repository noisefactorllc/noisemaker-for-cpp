// Port of the CPU authority's src/runtime/automation.js (itself upstream's
// Pipeline oscillator evaluation): `osc(...)` parameter values resolved per
// render at the normalized loop time. Every operation follows the JavaScript in
// order on doubles; sin/cos are V8's fdlibm, `%` is fmod, Math.round rounds
// halves toward +Infinity.
#include "noisemaker/graph/automation.hpp"

#include "noisemaker/fdlibm.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <vector>

namespace noisemaker::graph {
namespace {

constexpr double kPi = 3.141592653589793;
constexpr double kTau = kPi * 2;
constexpr int kMaxAutomationDepth = 8;

struct Range { double min; double max; };
constexpr Range kUnit{0, 1};
constexpr Range kOscillatorSpeed{-20, 20};
constexpr Range kOscillatorOffset{-1, 1};
constexpr Range kOscillatorSeed{1, 9999};

// Math.max(a, b): NaN if either is NaN; +0 beats -0.
double js_max(double a, double b) {
  if (std::isnan(a) || std::isnan(b)) return std::numeric_limits<double>::quiet_NaN();
  if (a == 0 && b == 0) return std::signbit(a) ? b : a;
  return a > b ? a : b;
}

// Math.round: the nearest integer, halves toward +Infinity, keeping -0.
double js_round(double x) {
  if (!std::isfinite(x) || x == 0) return x;
  if (x > 0 && x < 0.5) return 0.0;
  if (x < 0 && x >= -0.5) return -0.0;
  const double lower = std::floor(x);
  return x - lower >= 0.5 ? lower + 1 : lower;
}

double osc_sine(double t) { return (1.0 - fdlibm::cos(t * kTau)) * 0.5; }

double osc_tri(double t) {
  const double tf = t - std::floor(t);
  return 1.0 - std::fabs(tf * 2.0 - 1.0);
}

double osc_saw(double t) { return t - std::floor(t); }

double osc_saw_inv(double t) { return 1.0 - (t - std::floor(t)); }

double osc_square(double t) { return (t - std::floor(t)) >= 0.5 ? 1.0 : 0.0; }

double hash21(double px, double py, double s) {
  double x = std::fmod(px * 234.34 + s, 1);
  double y = std::fmod(py * 435.345 + s, 1);
  if (x < 0) x += 1;
  if (y < 0) y += 1;
  const double p = x + y + (x + y) * 34.23;
  return std::fmod(x * y * p, 1);
}

double noise_2d(double px, double py, double s) {
  const double ix = std::floor(px);
  const double iy = std::floor(py);
  double fx = px - ix;
  double fy = py - iy;
  fx = fx * fx * (3 - 2 * fx);
  fy = fy * fy * (3 - 2 * fy);
  const double a = hash21(ix, iy, s);
  const double b = hash21(ix + 1, iy, s);
  const double c = hash21(ix, iy + 1, s);
  const double d = hash21(ix + 1, iy + 1, s);
  return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy;
}

double osc_noise(double t, double seed) {
  const double temporal = std::fmod(t, 1);
  const double angle = temporal * kTau;
  const double radius = 2;
  const double loop_x = fdlibm::cos(angle) * radius;
  const double loop_y = fdlibm::sin(angle) * radius;
  const double n1 = noise_2d(loop_x + seed, loop_y + seed, seed);
  const double n2 = noise_2d(loop_x + seed * 2, loop_y + seed * 2, seed);
  return (n1 + n2) / 2;
}

double periodic_value(double x, double v) { return (fdlibm::sin((x - v) * kTau) + 1) * 0.5; }

double osc_noise_2d(double time, double speed, double seed) {
  const double px = (std::fabs(std::fmod(seed, 16)) + 0.5) / 16;
  const double py = (std::fabs(std::fmod(std::floor(seed / 16), 16)) + 0.5) / 16;
  const double time_noise = noise_2d(px, py, seed + 12345);
  const double value_noise = noise_2d(px, py, seed);
  const double scaled_time = periodic_value(time, time_noise) * speed;
  return periodic_value(scaled_time, value_noise);
}

// 16-point Gauss-Legendre nodes and weights on [-1, 1], then the 8-, 4- and
// 2-point rules the authority steps down to as rate modulators nest.
constexpr std::array<double, 16> kNodes16{
    -0.9894009349916499, -0.9445750230732326, -0.8656312023878318, -0.755404408355003,
    -0.6178762444026438, -0.4580167776572274, -0.2816035507792589, -0.0950125098376374,
    0.0950125098376374, 0.2816035507792589, 0.4580167776572274, 0.6178762444026438,
    0.755404408355003, 0.8656312023878318, 0.9445750230732326, 0.9894009349916499};
constexpr std::array<double, 16> kWeights16{
    0.0271524594117541, 0.0622535239386479, 0.0951585116824928, 0.1246289712555339,
    0.1495959888165767, 0.1691565193950025, 0.1826034150449236, 0.1894506104550685,
    0.1894506104550685, 0.1826034150449236, 0.1691565193950025, 0.1495959888165767,
    0.1246289712555339, 0.0951585116824928, 0.0622535239386479, 0.0271524594117541};
constexpr std::array<double, 8> kNodes8{
    -0.9602898564975363, -0.7966664774136267, -0.525532409916329, -0.1834346424956498,
    0.1834346424956498, 0.525532409916329, 0.7966664774136267, 0.9602898564975363};
constexpr std::array<double, 8> kWeights8{
    0.1012285362903763, 0.2223810344533745, 0.3137066458778873, 0.362683783378362,
    0.362683783378362, 0.3137066458778873, 0.2223810344533745, 0.1012285362903763};
constexpr std::array<double, 4> kNodes4{-0.8611363115940526, -0.3399810435848563, 0.3399810435848563,
                                        0.8611363115940526};
constexpr std::array<double, 4> kWeights4{0.3478548451374538, 0.6521451548625461, 0.6521451548625461,
                                          0.3478548451374538};
constexpr std::array<double, 2> kNodes2{-0.5773502691896257, 0.5773502691896257};
constexpr std::array<double, 2> kWeights2{1, 1};

bool is_automation(const PlanValue& value) { return value.kind == PlanValue::Kind::oscillator; }
int osc_type(const PlanValue& value) { return static_cast<int>(value.number); }
const PlanValue& field(const PlanValue& value, std::size_t index) { return value.array.at(index); }
enum Field : std::size_t { kMin = 0, kMax = 1, kSpeed = 2, kOffset = 3, kSeed = 4 };

using Stack = std::vector<const PlanValue*>;

double scale_automation_value(double value, const std::optional<Range>& range) {
  if (!range.has_value() || !std::isfinite(range->min) || !std::isfinite(range->max)) return value;
  return range->min + value * (range->max - range->min);
}

double evaluate_automation(const PlanValue& config, double normalized_time, const std::optional<Range>& range,
                           int depth, Stack& stack);
double evaluate_oscillator(const PlanValue& osc, double normalized_time, int depth, Stack& stack);

double resolve_automation_field(const PlanValue& value, double normalized_time, Range range, int depth,
                                Stack& stack, double fallback) {
  if (is_automation(value)) return evaluate_automation(value, normalized_time, range, depth + 1, stack);
  return value.kind == PlanValue::Kind::number && std::isfinite(value.number) ? value.number : fallback;
}

bool finite_number(const PlanValue& value) {
  return value.kind == PlanValue::Kind::number && std::isfinite(value.number);
}

bool can_integrate_oscillator_exactly(const PlanValue& config) {
  return osc_type(config) >= 0 && osc_type(config) <= 4 && finite_number(field(config, kMin)) &&
         finite_number(field(config, kMax)) && finite_number(field(config, kSpeed)) &&
         finite_number(field(config, kOffset)) && finite_number(field(config, kSeed));
}

double osc_primitive(int type, double x) {
  const double whole = std::floor(x);
  const double fraction = x - whole;
  switch (type) {
    case 0: return x * 0.5 - fdlibm::sin(x * kTau) / (2 * kTau);
    case 1: {
      const double partial = fraction < 0.5 ? fraction * fraction : 2 * fraction - fraction * fraction - 0.5;
      return whole * 0.5 + partial;
    }
    case 2: return whole * 0.5 + fraction * fraction * 0.5;
    case 3: return x - (whole * 0.5 + fraction * fraction * 0.5);
    case 4: return whole * 0.5 + js_max(0, fraction - 0.5);
    default: return std::numeric_limits<double>::quiet_NaN();
  }
}

double integrate_simple_oscillator(const PlanValue& config, double normalized_time) {
  const double min = field(config, kMin).number;
  const double max = field(config, kMax).number;
  const double speed = field(config, kSpeed).number;
  const double offset = field(config, kOffset).number;
  if (speed == 0) {
    Stack fresh;
    return evaluate_oscillator(config, 0, 0, fresh) * normalized_time;
  }
  const double start = osc_primitive(osc_type(config), offset);
  const double end = osc_primitive(osc_type(config), offset + speed * normalized_time);
  const double raw_integral = (end - start) / speed;
  return min * normalized_time + (max - min) * raw_integral;
}

template <std::size_t N>
double quadrature(const PlanValue& config, double normalized_time, int depth, Stack& stack,
                  const std::array<double, N>& nodes, const std::array<double, N>& weights) {
  const double midpoint = normalized_time * 0.5;
  const double half_width = normalized_time * 0.5;
  double sum = 0;
  for (std::size_t i = 0; i < N; ++i) {
    const double sample_time = midpoint + half_width * nodes[i];
    sum += weights[i] * evaluate_automation(config, sample_time, std::nullopt, depth + 1, stack);
  }
  return half_width * sum;
}

double integrate_automation(const PlanValue& config, double normalized_time, Range range, int depth,
                            Stack& stack) {
  double integral = 0;
  if (can_integrate_oscillator_exactly(config)) {
    integral = integrate_simple_oscillator(config, normalized_time);
  } else {
    // The quadrature order drops as rate modulators nest (16, 8, 4, then 2 points).
    switch (depth < 3 ? depth : 3) {
      case 0: integral = quadrature(config, normalized_time, depth, stack, kNodes16, kWeights16); break;
      case 1: integral = quadrature(config, normalized_time, depth, stack, kNodes8, kWeights8); break;
      case 2: integral = quadrature(config, normalized_time, depth, stack, kNodes4, kWeights4); break;
      default: integral = quadrature(config, normalized_time, depth, stack, kNodes2, kWeights2); break;
    }
  }
  return range.min * normalized_time + integral * (range.max - range.min);
}

double evaluate_oscillator(const PlanValue& osc, double normalized_time, int depth, Stack& stack) {
  const double min = resolve_automation_field(field(osc, kMin), normalized_time, kUnit, depth, stack, 0);
  const double max = resolve_automation_field(field(osc, kMax), normalized_time, kUnit, depth, stack, 1);
  const double offset =
      resolve_automation_field(field(osc, kOffset), normalized_time, kOscillatorOffset, depth, stack, 0);
  const double seed = resolve_automation_field(field(osc, kSeed), normalized_time, kOscillatorSeed, depth, stack, 1);

  // A modulated rate is frequency modulation, so phase is the integral of rate.
  const PlanValue& speed = field(osc, kSpeed);
  const double phase = is_automation(speed)
                           ? integrate_automation(speed, normalized_time, kOscillatorSpeed, depth, stack)
                           : normalized_time * (finite_number(speed) ? speed.number : 1);
  const double t = phase + offset;

  double value = 0;
  switch (osc_type(osc)) {
    case 0: value = osc_sine(t); break;
    case 1: value = osc_tri(t); break;
    case 2: value = osc_saw(t); break;
    case 3: value = osc_saw_inv(t); break;
    case 4: value = osc_square(t); break;
    case 5: value = osc_noise(t, seed); break;
    case 6: {
      const double resolved_speed =
          resolve_automation_field(speed, normalized_time, kOscillatorSpeed, depth, stack, 1);
      value = osc_noise_2d(normalized_time + offset, std::isfinite(resolved_speed) ? resolved_speed : 1, seed);
      break;
    }
    default: value = 0;
  }
  return min + value * (max - min);
}

double evaluate_automation(const PlanValue& config, double normalized_time, const std::optional<Range>& range,
                           int depth, Stack& stack) {
  if (!is_automation(config) || depth > kMaxAutomationDepth ||
      std::find(stack.begin(), stack.end(), &config) != stack.end()) {
    return scale_automation_value(0, range);
  }
  stack.push_back(&config);
  const double value = evaluate_oscillator(config, normalized_time, depth, stack);
  stack.pop_back();
  return scale_automation_value(value, range);
}

std::optional<double> declared_number(const std::optional<effects::Value>& value) {
  if (!value.has_value()) return std::nullopt;
  if (value->kind == effects::ValueKind::number) return value->number;
  return std::numeric_limits<double>::quiet_NaN();
}

}  // namespace

std::optional<AutomationSpec> automation_spec(const effects::ParameterDefinition* parameter) {
  if (parameter == nullptr) return std::nullopt;
  const bool has_choices = !parameter->choices.empty() || !parameter->enum_values.empty();
  if ((parameter->type == "float" || parameter->type == "int") && !has_choices) {
    return AutomationSpec{declared_number(parameter->min).value_or(0),
                          declared_number(parameter->max).value_or(100), false};
  }
  if (parameter->type == "int" && has_choices) {
    AutomationSpec spec;
    spec.integer = true;
    const auto min = declared_number(parameter->min);
    const auto max = declared_number(parameter->max);
    if (min.has_value() && max.has_value() && std::isfinite(*min) && std::isfinite(*max)) {
      spec.min = min;
      spec.max = max;
    }
    return spec;
  }
  return std::nullopt;
}

double resolve_automation(const PlanValue& value, double normalized_time, const std::optional<AutomationSpec>& spec) {
  std::optional<Range> range;
  if (spec.has_value() && spec->min.has_value() && spec->max.has_value()) range = Range{*spec->min, *spec->max};
  Stack stack;
  const double resolved = evaluate_automation(value, normalized_time, range, 0, stack);
  return spec.has_value() && spec->integer ? js_round(resolved) : resolved;
}

}  // namespace noisemaker::graph
