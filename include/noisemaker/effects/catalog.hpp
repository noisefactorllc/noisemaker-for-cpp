#pragma once

#include "noisemaker/effects/catalog_types.hpp"

#include <cstddef>
#include <mutex>
#include <string>
#include <optional>
#include <unordered_map>

namespace noisemaker::effects {

// The id -> position memo behind `EffectCatalog::find`.
//
// `effect_catalog()` returns one process-wide `const EffectCatalog&`, and
// `find` is a const member, so [res.on.data.races] promises callers that
// concurrent `find` is safe. The memo is what breaks that promise if it is a
// bare `mutable std::unordered_map`: one thread's insert rehashes the table
// while another thread reads a bucket.
//
// Every access here is therefore taken under one mutex, and a lookup hands
// back a value rather than an iterator -- an iterator would outlive the lock
// and could be invalidated by the next insert. There is no unsynchronized
// fast path to get wrong.
//
// Copying an `EffectCatalog` does not copy the memo. It is a cache of
// positions in `definitions`, it is rebuilt on demand from the definitions the
// copy owns, and a mutex is not copyable in any case.
class EffectIndex {
 public:
  struct Entry {
    std::size_t second = 0;
  };

  // A value-semantic lookup result shaped like the map iterator it replaces:
  // comparable against `end()`, dereferenceable to `->second`.
  class Cursor {
   public:
    constexpr Cursor() noexcept = default;
    explicit constexpr Cursor(std::size_t position) noexcept
        : entry_{position}, found_(true) {}
    [[nodiscard]] constexpr const Entry* operator->() const noexcept { return &entry_; }
    [[nodiscard]] friend constexpr bool operator==(const Cursor& left, const Cursor& right) noexcept {
      return left.found_ == right.found_ && left.entry_.second == right.entry_.second;
    }

   private:
    Entry entry_{};
    bool found_ = false;
  };

  EffectIndex() = default;
  // The constructors build nothing and can therefore promise `noexcept`. The
  // assignments cannot: they discard the memo, `clear()` takes the mutex, and
  // `std::mutex::lock` is specified to throw `std::system_error`. Marking them
  // `noexcept` would turn that into `std::terminate` -- an unreachable path
  // today, but a promise this class is not in a position to make.
  EffectIndex(const EffectIndex&) noexcept {}
  EffectIndex(EffectIndex&&) noexcept {}
  EffectIndex& operator=(const EffectIndex&) { return clear(); }
  EffectIndex& operator=(EffectIndex&&) { return clear(); }
  ~EffectIndex() = default;

  [[nodiscard]] Cursor find(const std::string& id) const {
    const std::lock_guard<std::mutex> guard(mutex_);
    const auto found = memo_.find(id);
    return found == memo_.end() ? Cursor{} : Cursor{found->second};
  }

  [[nodiscard]] static constexpr Cursor end() noexcept { return Cursor{}; }

  void emplace(const std::string& id, std::size_t position) const {
    const std::lock_guard<std::mutex> guard(mutex_);
    memo_.emplace(id, position);
  }

 private:
  EffectIndex& clear() {
    const std::lock_guard<std::mutex> guard(mutex_);
    memo_.clear();
    return *this;
  }

  mutable std::mutex mutex_;
  mutable std::unordered_map<std::string, std::size_t> memo_;
};

struct EffectCatalog {
  std::vector<EffectDefinition> definitions;
  std::vector<ProgramCompatibility> canonical_programs;
  std::vector<ReferencePassCompatibility> reference_passes;
  std::optional<ScatterCompatibility> scatter;
  CatalogProvenance provenance;

  // Safe to call concurrently on a shared catalog; see EffectIndex.
  const EffectDefinition* find(const std::string& id) const;

 private:
  EffectIndex index;
};

const EffectCatalog& effect_catalog();

}  // namespace noisemaker::effects
