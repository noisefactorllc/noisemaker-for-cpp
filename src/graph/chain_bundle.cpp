#include "noisemaker/graph/chain_bundle.hpp"

#include <cmath>
#include <stdexcept>
#include <string>

namespace noisemaker::graph::bundle {

bool is_volume_domain(std::string_view domain) noexcept {
  return domain != "image" && domain != "loop-begin" && domain != "loop-end";
}

bool is_passthrough_output_name(std::string_view name) noexcept {
  return name.empty() || name == "inputTex" || name == "inputTex3d" || name == "inputGeo";
}

std::optional<double> inherit_volume_size(std::string_view effect_id,
                                          std::string_view domain,
                                          bool step_declares_volume_size,
                                          std::size_t input_volume_width,
                                          std::size_t input_volume_height) {
  if (!step_declares_volume_size) return std::nullopt;
  if (domain != "volume-generator" && domain != "volume-filter" && domain != "volume-renderer") {
    return std::nullopt;
  }
  const auto expected_height = input_volume_width * input_volume_width;
  if (input_volume_height != expected_height) {
    throw std::invalid_argument(
        std::string(effect_id) + " input volume atlas expected " +
        std::to_string(input_volume_width) + "x" + std::to_string(expected_height) +
        ", received " + std::to_string(input_volume_width) + "x" +
        std::to_string(input_volume_height));
  }
  return static_cast<double>(input_volume_width);
}

std::optional<double> resolve_volume_size(std::string_view domain,
                                          std::optional<double> step_params_volume_size,
                                          std::optional<double> input_bundle_volume_size,
                                          std::optional<std::size_t> produced_volume_width) {
  const auto produced = produced_volume_width.has_value()
                             ? std::optional<double>(static_cast<double>(*produced_volume_width))
                             : std::nullopt;
  if (domain == "volume-generator") {
    return step_params_volume_size.has_value() ? step_params_volume_size : produced;
  }
  if (input_bundle_volume_size.has_value()) return input_bundle_volume_size;
  return step_params_volume_size.has_value() ? step_params_volume_size : produced;
}

void validate_volume_output_shape(std::string_view effect_id, std::string_view domain,
                                  bool produced_volume,
                                  std::optional<std::size_t> produced_volume_width,
                                  std::optional<std::size_t> produced_volume_height,
                                  std::optional<double> volume_size) {
  const bool is_volume = is_volume_domain(domain);
  if (is_volume && !produced_volume && domain != "volume-renderer") {
    throw std::invalid_argument(std::string(effect_id) + " did not produce outputTex3d");
  }
  if (produced_volume && (domain == "volume-generator" || domain == "volume-filter")) {
    const bool matches = volume_size.has_value() && produced_volume_width.has_value() &&
                         produced_volume_height.has_value() &&
                         static_cast<double>(*produced_volume_width) == *volume_size &&
                         static_cast<double>(*produced_volume_height) == (*volume_size) * (*volume_size);
    if (!matches) {
      const std::string expected_width =
          volume_size.has_value() ? std::to_string(static_cast<long long>(*volume_size)) : "?";
      const std::string expected_height =
          volume_size.has_value()
              ? std::to_string(static_cast<long long>((*volume_size) * (*volume_size)))
              : "?";
      const std::string received_width =
          produced_volume_width.has_value() ? std::to_string(*produced_volume_width) : "?";
      const std::string received_height =
          produced_volume_height.has_value() ? std::to_string(*produced_volume_height) : "?";
      throw std::invalid_argument(
          std::string(effect_id) + " volume atlas expected " + expected_width + "x" +
          expected_height + ", received " + received_width + "x" + received_height);
    }
  }
}

bool requires_output_image(std::string_view domain) noexcept {
  return domain != "volume-generator" && domain != "volume-filter";
}

}  // namespace noisemaker::graph::bundle
