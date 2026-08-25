#pragma once

#include "noisemaker/graph/execution_plan.hpp"
#include "noisemaker/graph/resource.hpp"

#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace noisemaker::graph {

enum class GraphErrorCode : std::uint32_t {
  invalid_options = 0,
  invalid_dimension = 1,
  allocation_limit = 2,
  invalid_format = 3,
  missing_resource = 4,
  read_before_write = 5,
  duplicate_output = 6,
  unavailable_pass = 7,
  invalid_snapshot = 8,
  missing_binding = 9,
  binding_type = 10,
  unsupported_blend = 11,
  unsupported_mrt = 12,
  unsupported_draw_mode = 13,
  unsupported_scatter = 14,
  execution_failure = 15,
};

class GraphError final : public std::runtime_error {
 public:
  GraphError(GraphErrorCode code, std::string detail,
             std::string effect_id = {}, std::size_t pass_index = 0,
             std::string pass_name = {}, std::string program_key = {});

  [[nodiscard]] GraphErrorCode code() const noexcept { return code_; }
  [[nodiscard]] std::string_view effect_id() const noexcept { return effect_id_; }
  [[nodiscard]] std::size_t pass_index() const noexcept { return pass_index_; }
  [[nodiscard]] std::string_view pass_name() const noexcept { return pass_name_; }
  [[nodiscard]] std::string_view program_key() const noexcept { return program_key_; }
  [[nodiscard]] std::string_view detail() const noexcept { return detail_; }

 private:
  static std::string make_what(GraphErrorCode code, std::string_view detail,
                               std::string_view effect_id,
                               std::size_t pass_index,
                               std::string_view pass_name,
                               std::string_view program_key);

  GraphErrorCode code_;
  std::string detail_;
  std::string effect_id_;
  std::size_t pass_index_;
  std::string pass_name_;
  std::string program_key_;
};

struct ExecutionInputs {
  std::size_t width = 512;
  std::size_t height = 512;
  double time = 0.0;
  std::uint32_t frame = 0;
  double seed = 1.0;
  double delta_time = 0.0;
  bool one_shot = true;
  std::vector<NamedSurface> seed_surfaces;
  std::vector<NamedSurface> external_textures;
};

struct ExecutionResult {
  noisemaker::Surface surface;
  std::string final_route;
  std::size_t pass_count = 0;
};

class GraphExecutor final {
 public:
  GraphExecutor() = default;
  [[nodiscard]] ExecutionResult execute(const ExecutionPlan& plan,
                                        ExecutionInputs inputs) const;
};

}  // namespace noisemaker::graph
