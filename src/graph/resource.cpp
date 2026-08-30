#include "noisemaker/graph/resource.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <utility>

namespace noisemaker::graph {
namespace {

[[nodiscard]] bool is_alias(std::string_view value,
                            std::string_view first,
                            std::string_view second) noexcept {
  return value == first || value == second;
}

}  // namespace

GraphResource::GraphResource(std::string name, noisemaker::Surface surface,
                             noisemaker::TextureFormat format,
                             ResourceLifetime lifetime)
    : name_(std::move(name)),
      surface_(std::move(surface)),
      format_(format),
      lifetime_(lifetime) {}

GraphResource::GraphResource(GraphResource&&) noexcept = default;

GraphResource& GraphResource::operator=(GraphResource&&) noexcept = default;

std::string_view GraphResource::name() const noexcept {
  return name_;
}

const noisemaker::Surface& GraphResource::surface() const noexcept {
  return surface_;
}

noisemaker::TextureFormat GraphResource::format() const noexcept {
  return format_;
}

ResourceLifetime GraphResource::lifetime() const noexcept {
  return lifetime_;
}

std::size_t GraphResource::width() const noexcept {
  return surface_.width();
}

std::size_t GraphResource::height() const noexcept {
  return surface_.height();
}

ResourceArena::ResourceArena(ResourceArena&& other) noexcept
    : owned_(std::move(other.owned_)), named_(std::move(other.named_)) {
  // The index stores non-owning pointers. Moving unique_ptrs does not move the
  // pointees, so the map remains valid. Clear the source map to make the
  // moved-from arena a deterministic empty lookup domain.
  other.named_.clear();
}

ResourceArena& ResourceArena::operator=(ResourceArena&& other) noexcept {
  if (this == &other) {
    return *this;
  }
  owned_ = std::move(other.owned_);
  named_ = std::move(other.named_);
  other.named_.clear();
  return *this;
}

ResourceArena::~ResourceArena() = default;

std::size_t ResourceArena::size() const noexcept {
  return owned_.size();
}

const GraphResource& ResourceArena::require(std::string_view name) const {
  const auto* resource = find(name);
  if (resource == nullptr) {
    throw std::out_of_range("resource not found: " + std::string(name));
  }
  return *resource;
}

GraphResource& ResourceArena::insert(std::string name,
                                     noisemaker::Surface surface,
                                     noisemaker::TextureFormat format,
                                     ResourceLifetime lifetime) {
  if (name.empty()) {
    throw std::invalid_argument("resource name must not be empty");
  }
  GraphResource* previous = find(name);
  auto resource = std::unique_ptr<GraphResource>(new GraphResource(
      std::move(name), std::move(surface), format, lifetime));
  GraphResource& result = *resource;
  const std::string key(result.name());
  owned_.push_back(std::move(resource));
  try {
    named_[key] = &result;
  } catch (...) {
    // Do not leave a lookup entry pointing at a pointee that was rolled back.
    owned_.pop_back();
    throw;
  }
  // A superseded route does not by itself retire the pointee: another named
  // alias, or a pin held by the executor's effect scope, may still be the
  // executor's next input and must remain bindable.
  if (previous != nullptr && !is_referenced(*previous)) {
    previous->retired_ = true;
    collect_retired(*previous);
  }
  return result;
}

GraphResource& ResourceArena::allocate(std::string name, std::size_t width,
                                        std::size_t height,
                                        noisemaker::TextureFormat format,
                                        ResourceLifetime lifetime) {
  if (name.empty()) {
    throw std::invalid_argument("resource name must not be empty");
  }
  // Surface performs the shared cap check before any vector allocation.
  return insert(std::move(name), noisemaker::Surface(width, height), format,
                lifetime);
}

GraphResource& ResourceArena::copy(std::string name,
                                   const noisemaker::Surface& source,
                                   noisemaker::TextureFormat format,
                                   ResourceLifetime lifetime) {
  if (name.empty()) {
    throw std::invalid_argument("resource name must not be empty");
  }
  return insert(std::move(name), copy_surface_preserving_filter(source),
                format, lifetime);
}

void ResourceArena::alias(std::string name, GraphResource& resource) {
  if (name.empty()) {
    throw std::invalid_argument("resource name must not be empty");
  }
  if (!owns(resource)) {
    throw std::invalid_argument("resource does not belong to arena");
  }
  if (resource.retired_) {
    throw std::logic_error("cannot alias a retired resource");
  }
  GraphResource* previous = find(name);
  named_[name] = &resource;
  // Replacing one alias leaves the previous resource active whenever another
  // alias still names it; only its final alias removal makes it retireable.
  if (previous != nullptr && previous != &resource &&
      !is_referenced(*previous)) {
    previous->retired_ = true;
    collect_retired(*previous);
  }
}

void ResourceArena::remove_alias(std::string_view name) {
  const auto iterator = named_.find(std::string(name));
  if (iterator == named_.end()) {
    return;
  }
  GraphResource* resource = iterator->second;
  named_.erase(iterator);
  if (!is_referenced(*resource)) {
    resource->retired_ = true;
    collect_retired(*resource);
  }
}

GraphResource* ResourceArena::find(std::string_view name) {
  const auto iterator = named_.find(std::string(name));
  return iterator == named_.end() ? nullptr : iterator->second;
}

const GraphResource* ResourceArena::find(std::string_view name) const {
  const auto iterator = named_.find(std::string(name));
  return iterator == named_.end() ? nullptr : iterator->second;
}

void ResourceArena::retain(GraphResource& resource) {
  if (!owns(resource)) {
    throw std::invalid_argument("resource does not belong to arena");
  }
  if (resource.retired_) {
    throw std::logic_error("cannot bind a retired resource");
  }
  if (resource.borrow_count_ == std::numeric_limits<std::size_t>::max()) {
    throw std::overflow_error("resource binding count overflow");
  }
  ++resource.borrow_count_;
}

void ResourceArena::release(GraphResource& resource) noexcept {
  if (!owns(resource)) {
    return;
  }
  if (resource.borrow_count_ == 0U) {
    return;
  }
  --resource.borrow_count_;
  collect_retired(resource);
}

void ResourceArena::retire(GraphResource& resource) noexcept {
  if (!owns(resource)) {
    return;
  }
  resource.retired_ = true;
  for (auto iterator = named_.begin(); iterator != named_.end();) {
    if (iterator->second == &resource) {
      iterator = named_.erase(iterator);
    } else {
      ++iterator;
    }
  }
  collect_retired(resource);
}

void ResourceArena::pin(GraphResource& resource) {
  if (!owns(resource)) {
    throw std::invalid_argument("resource does not belong to arena");
  }
  if (resource.retired_) {
    throw std::logic_error("cannot pin a retired resource");
  }
  if (resource.pin_count_ == std::numeric_limits<std::size_t>::max()) {
    throw std::overflow_error("resource pin count overflow");
  }
  ++resource.pin_count_;
}

void ResourceArena::unpin(GraphResource& resource) noexcept {
  if (!owns(resource) || resource.pin_count_ == 0U) {
    return;
  }
  --resource.pin_count_;
  // Dropping the last pin is the loss of a reference, exactly as removing the
  // last alias is, so it retires an otherwise unreachable resource here rather
  // than leaving it owned until the arena dies.
  if (!is_referenced(resource)) {
    resource.retired_ = true;
  }
  collect_retired(resource);
}

ResourceArena::ScopedPin::ScopedPin(ResourceArena& arena,
                                    GraphResource* resource)
    : arena_(arena), resource_(resource) {
  if (resource_ != nullptr) arena_.pin(*resource_);
}

ResourceArena::ScopedPin::~ScopedPin() {
  if (resource_ != nullptr) arena_.unpin(*resource_);
}

void ResourceArena::collect_retired(GraphResource& resource) noexcept {
  if (!owns(resource) || !resource.retired_ || resource.borrow_count_ != 0U ||
      is_referenced(resource)) {
    return;
  }
  const auto iterator = std::find_if(
      owned_.begin(), owned_.end(),
      [&resource](const std::unique_ptr<GraphResource>& candidate) {
        return candidate.get() == &resource;
      });
  if (iterator != owned_.end()) {
    owned_.erase(iterator);
  }
}

bool ResourceArena::has_alias(const GraphResource& resource) const noexcept {
  return std::any_of(
      named_.begin(), named_.end(),
      [&resource](const auto& entry) { return entry.second == &resource; });
}

bool ResourceArena::is_referenced(const GraphResource& resource) const noexcept {
  return resource.pin_count_ != 0U || has_alias(resource);
}

bool ResourceArena::owns(const GraphResource& resource) const noexcept {
  return std::any_of(
      owned_.begin(), owned_.end(),
      [&resource](const std::unique_ptr<GraphResource>& candidate) {
        return candidate.get() == &resource;
      });
}

noisemaker::Surface ResourceArena::copy_surface_preserving_filter(
    const noisemaker::Surface& source) {
  auto result = source.clone();
  result.set_filter(source.filter());
  return result;
}

noisemaker::TextureFormat resolve_texture_format(
    std::optional<std::string_view> format) {
  if (!format.has_value()) {
    return noisemaker::TextureFormat::rgba16f;
  }
  if (is_alias(*format, "rgba8", "rgba8unorm")) {
    return noisemaker::TextureFormat::rgba8_unorm;
  }
  if (is_alias(*format, "rgba16f", "rgba16float")) {
    return noisemaker::TextureFormat::rgba16f;
  }
  if (is_alias(*format, "rgba32f", "rgba32float")) {
    return noisemaker::TextureFormat::rgba32f;
  }
  throw std::invalid_argument("unknown texture format: " + std::string(*format));
}

std::size_t checked_dimension(double value) {
  if (!std::isfinite(value) || value <= 0.0 || std::trunc(value) != value ||
      value > static_cast<double>(std::numeric_limits<std::size_t>::max())) {
    throw std::invalid_argument("surface dimension must be a positive safe integer");
  }
  // Number.MAX_SAFE_INTEGER is the authority's pre-cast bound. On platforms
  // with a wider size_t, keep the graph deterministic across JS/C++.
  constexpr double max_safe_integer = 9'007'199'254'740'991.0;
  if (value > max_safe_integer) {
    throw std::invalid_argument("surface dimension exceeds safe integer range");
  }
  return static_cast<std::size_t>(value);
}

}  // namespace noisemaker::graph
