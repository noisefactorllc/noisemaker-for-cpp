#pragma once

#include "noisemaker/surface.hpp"
#include "noisemaker/texture_format.hpp"

#include <cstddef>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

namespace noisemaker::graph {

enum class ResourceLifetime { seed, external, declared, transient, published };

// This is the normative value aggregate used by graph::ExecutionInputs. It
// owns the caller-provided copy; it intentionally has no pointer-taking
// constructor, callbacks, or resource-arena access.
struct NamedSurface {
  std::string name;
  noisemaker::Surface surface;
};

// A graph-owned surface. The public view is deliberately const: sampler
// bindings may borrow it, but callers cannot mutate a resource behind the
// arena's back or retain a raw pointer to its storage.
class GraphResource final {
 public:
  GraphResource(GraphResource&&) noexcept;
  GraphResource& operator=(GraphResource&&) noexcept;
  GraphResource(const GraphResource&) = delete;
  GraphResource& operator=(const GraphResource&) = delete;

  [[nodiscard]] std::string_view name() const noexcept;
  [[nodiscard]] const noisemaker::Surface& surface() const noexcept;
  [[nodiscard]] noisemaker::TextureFormat format() const noexcept;
  [[nodiscard]] ResourceLifetime lifetime() const noexcept;
  [[nodiscard]] std::size_t width() const noexcept;
  [[nodiscard]] std::size_t height() const noexcept;

 private:
  friend class ResourceArena;
  friend class GraphExecutor;
  friend class ResourceArenaTestAccess;

  GraphResource(std::string name, noisemaker::Surface surface,
                noisemaker::TextureFormat format, ResourceLifetime lifetime);

  std::string name_;
  noisemaker::Surface surface_;
  noisemaker::TextureFormat format_;
  ResourceLifetime lifetime_;
  std::size_t borrow_count_ = 0;
  // A pin is an unnamed alias: it holds a reference that no route publication
  // can take away, so a pinned resource stays both alive and bindable even
  // after the last name that reached it has moved to a newer pointee.
  std::size_t pin_count_ = 0;
  bool retired_ = false;
};

class ResourceArena final {
 public:
  ResourceArena() = default;
  ResourceArena(ResourceArena&&) noexcept;
  ResourceArena& operator=(ResourceArena&&) noexcept;
  ResourceArena(const ResourceArena&) = delete;
  ResourceArena& operator=(const ResourceArena&) = delete;
  ~ResourceArena();

  [[nodiscard]] std::size_t size() const noexcept;
  [[nodiscard]] const GraphResource& require(std::string_view name) const;

 private:
  friend class GraphExecutor;
  friend class ResourceArenaTestAccess;

  // Each insertion owns a fresh pointee. Replacing a route updates the private
  // lookup index and retires the old pointee. A resource retained by a live
  // Binding/BoundKernel remains in owned_ until its final release; otherwise
  // retirement erases it immediately, keeping repeated publication bounded.
  GraphResource& insert(std::string name, noisemaker::Surface surface,
                        noisemaker::TextureFormat format,
                        ResourceLifetime lifetime);
  GraphResource& allocate(std::string name, std::size_t width,
                          std::size_t height, noisemaker::TextureFormat format,
                          ResourceLifetime lifetime);
  GraphResource& copy(std::string name, const noisemaker::Surface& source,
                      noisemaker::TextureFormat format,
                      ResourceLifetime lifetime);
  void alias(std::string name, GraphResource& resource);
  void remove_alias(std::string_view name);
  [[nodiscard]] GraphResource* find(std::string_view name);
  [[nodiscard]] const GraphResource* find(std::string_view name) const;
  void retain(GraphResource& resource);
  void release(GraphResource& resource) noexcept;
  void retire(GraphResource& resource) noexcept;
  // Add or drop an unnamed reference. A borrow is not a substitute: a borrowed
  // resource whose route was republished is retired, and retiring it makes the
  // next `retain` throw, so the executor could not re-bind an effect input it
  // is still contractually holding. A pin keeps the resource unretired for as
  // long as it is held, and dropping the last pin retires and collects exactly
  // as removing the last alias does.
  void pin(GraphResource& resource);
  void unpin(GraphResource& resource) noexcept;
  void collect_retired(GraphResource& resource) noexcept;
  [[nodiscard]] bool has_alias(const GraphResource& resource) const noexcept;
  // Any name or any pin still reaching this resource. Retirement is exactly
  // the loss of the last reference of either kind.
  [[nodiscard]] bool is_referenced(const GraphResource& resource) const noexcept;
  [[nodiscard]] bool owns(const GraphResource& resource) const noexcept;
  static noisemaker::Surface copy_surface_preserving_filter(
      const noisemaker::Surface& source);

  // A pin held for a lexical scope. The executor's effect scope has one normal
  // exit and several throwing ones, so the pin is released by destruction
  // rather than by a statement a later edit could route around. Holding a null
  // resource is a no-op, which is the executor's first-effect case.
  class ScopedPin final {
   public:
    ScopedPin(ResourceArena& arena, GraphResource* resource);
    ~ScopedPin();
    ScopedPin(const ScopedPin&) = delete;
    ScopedPin& operator=(const ScopedPin&) = delete;
    ScopedPin(ScopedPin&&) = delete;
    ScopedPin& operator=(ScopedPin&&) = delete;

   private:
    ResourceArena& arena_;
    GraphResource* resource_ = nullptr;
  };

  std::vector<std::unique_ptr<GraphResource>> owned_;
  std::unordered_map<std::string, GraphResource*> named_;
};

// Graph-local format authority. An omitted format is distinct from an
// explicitly empty/unknown value and uses the CPU authority's rgba16f default.
[[nodiscard]] noisemaker::TextureFormat resolve_texture_format(
    std::optional<std::string_view> format);

// Validate a dimension after graph expression resolution, before conversion
// to size_t or Surface construction. This intentionally does not perform the
// authority's expression-specific rounding; that belongs to the plan/executor
// parameter context.
[[nodiscard]] std::size_t checked_dimension(double value);

}  // namespace noisemaker::graph
