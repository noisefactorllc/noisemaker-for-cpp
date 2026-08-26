#pragma once

#include "noisemaker/graph/execution_plan.hpp"
#include "noisemaker/graph/resource.hpp"
#include "noisemaker/glsl_runtime.hpp"
#include "noisemaker/kernel.hpp"

#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <span>
#include <string>
#include <string_view>
#include <variant>
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

// Generated typed dispatch supplies these descriptors.  The executor
// intentionally keys the lookup by both fields: program_key alone is
// ambiguous for the two duplicate legacy rows in the generated catalog.
struct FactoryRouteDescriptor {
  std::string_view program_key;
  std::string_view canonical_factory;
  std::string_view emitted_factory;
  std::string_view route_kind;
  std::string_view source_sha256;
  std::string_view typed_abi_sha256;
  // The compile-define contract and the values baked into the emitted kernel,
  // as `NAME=VALUE;NAME=VALUE` ordered by name. A `default-only` program was
  // compiled around these values and cannot honour any other.
  std::string_view define_contract;
  std::string_view defines;
  // Out-of-plan anchors for the ordered binding ABI. The executor re-derives
  // each section from the value-owned admission and compares it here, so a
  // reordered or retyped ABI inside a plan cannot authenticate.
  std::string_view sampler_abi_sha256;
  std::string_view uniform_abi_sha256;
  std::string_view output_abi_sha256;
  std::string_view output_extent_sha256;
  std::string_view compile_define_abi_sha256;
  noisemaker::BoundKernel (*bind)(const glsl::Bindings&) = nullptr;
};

[[nodiscard]] const FactoryRouteDescriptor* find_factory_route(
    std::span<const FactoryRouteDescriptor> routes,
    std::string_view program_key,
    std::string_view canonical_factory) noexcept;

// The authenticated canonical view of `generated::canonical_routes()`: one
// descriptor per unique program key, selecting the canonical duplicate
// factory rather than the first physical row.  The projection is validated
// once and is the default dispatch table for every execution.
[[nodiscard]] std::span<const FactoryRouteDescriptor> canonical_factory_routes();

// Selects the descriptor for an admission and proves it is the authenticated
// route: exact (program key, canonical factory) pair, emitted symbol, route
// kind, upstream source hash, typed ABI hash, and each ordered-ABI section
// against the generated out-of-plan anchor.  An empty route span uses
// `canonical_factory_routes()`.  Throws GraphError on every mismatch.
[[nodiscard]] const FactoryRouteDescriptor* authenticate_factory_route(
    const EffectStep& step, const PassAdmission& admission,
    std::span<const FactoryRouteDescriptor> routes = {});

// Proves that every compile-define-backed parameter of the owned definition
// still requests the value baked into the selected route.  A `default-only`
// program cannot honour any other value, so a mismatch fails closed naming the
// parameter, the requested value, and the baked value.
void authenticate_compile_define_parameters(
    const EffectStep& step, const PassAdmission& admission,
    const effects::EffectDefinition& definition,
    const FactoryRouteDescriptor& route);

// Returns a bound kernel only after the exact route has been authenticated and
// every guard has passed: no compile-define-backed parameter may request a
// value the route did not bake, no unported palette override may be in play,
// and no measured parity exclusion may apply. There is deliberately no
// definition-free overload -- a caller must supply the owned definition so the
// guards cannot be bypassed.
[[nodiscard]] noisemaker::BoundKernel bind_factory_route(
    const EffectStep& step, const PassAdmission& admission,
    const effects::EffectDefinition& definition, const glsl::Bindings& bindings,
    std::span<const FactoryRouteDescriptor> routes = {});

struct BindingMaterializationContext {
  const ExecutionInputs* inputs = nullptr;
  // The owned snapshot definition for this step.  Compile-define bindings are
  // resolved from its parameter list, never from a live registry.
  const effects::EffectDefinition* definition = nullptr;
  std::size_t destination_width = 0;
  std::size_t destination_height = 0;

  using SurfaceLookup = const noisemaker::Surface* (*)(
      void* context, std::string_view route);
  SurfaceLookup lookup_surface = nullptr;
  void* lookup_context = nullptr;

  // Pass-derived values are supplied through one narrow seam.  A null
  // resolver selects the authenticated built-in resolver below; the executor
  // never infers a value from a factory name or a live registry, and an
  // unknown source name always fails closed.
  using DerivedResolver = bool (*)(
      void* context, std::string_view source_name,
      std::string_view binding_name, const EffectStep& step,
      const PassAdmission& admission, const effects::PassDefinition& pass,
      const BindingMaterializationContext& binding_context,
      glsl::UniformValue& value);
  DerivedResolver resolve_derived = nullptr;
  void* derived_context = nullptr;
};

// The authenticated pass-derived resolver.  It covers exactly the source
// names the compatibility document declares and returns false for anything
// else, so an unrecognized source is rejected before any factory call.
[[nodiscard]] bool resolve_authenticated_pass_derived(
    void* context, std::string_view source_name, std::string_view binding_name,
    const EffectStep& step, const PassAdmission& admission,
    const effects::PassDefinition& pass,
    const BindingMaterializationContext& binding_context,
    glsl::UniformValue& value);

// Validate all admission-owned ABI relationships and all value shapes before
// a caller surface is copied or a destination is allocated.
void preflight_pass_abi(const EffectStep& step, const PassAdmission& admission,
                        const effects::PassDefinition& pass,
                        const BindingMaterializationContext& context);

// Materialize uniforms in the exact ordered admission ABI.  Samplers are
// materialized separately so the executor can retain arena lifetimes around
// the bound kernel.
[[nodiscard]] glsl::Bindings materialize_uniform_bindings(
    const EffectStep& step, const PassAdmission& admission,
    const effects::PassDefinition& pass,
    const BindingMaterializationContext& context);

void materialize_sampler_bindings(
    glsl::Bindings& bindings, const PassAdmission& admission,
    const BindingMaterializationContext& context, const EffectStep& step,
    const effects::PassDefinition& pass);

class GraphExecutor final {
 public:
  GraphExecutor() = default;
  // The inputs are observed through a const reference so the complete
  // plan/input/route/ABI/resource preflight runs before any caller-owned
  // surface is copied or any destination is allocated.
  [[nodiscard]] ExecutionResult execute(const ExecutionPlan& plan,
                                        const ExecutionInputs& inputs) const;
};

}  // namespace noisemaker::graph
