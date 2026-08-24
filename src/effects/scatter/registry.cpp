#include "noisemaker/effects/scatter/registry.hpp"

#include <stdexcept>
#include <string>
#include <unordered_map>

namespace noisemaker::scatter {
namespace {

std::unordered_map<std::string, ScatterAdapter>& registry() {
  static std::unordered_map<std::string, ScatterAdapter> instance;
  return instance;
}

}  // namespace

void register_scatter_adapter(std::string_view key, ScatterAdapter adapter) {
  if (key.empty()) throw std::invalid_argument("register_scatter_adapter requires a non-empty key");
  if (adapter == nullptr) throw std::invalid_argument("register_scatter_adapter requires a non-null adapter");
  auto [it, inserted] = registry().emplace(std::string(key), adapter);
  if (!inserted) throw std::invalid_argument("register_scatter_adapter: key already registered: " + std::string(key));
}

ScatterAdapter resolve_scatter_adapter(std::string_view key) noexcept {
  const auto it = registry().find(std::string(key));
  return it == registry().end() ? nullptr : it->second;
}

}  // namespace noisemaker::scatter
