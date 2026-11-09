#include "test_harness.hpp"

#include "noisemaker/renderer.hpp"

#include <cstdint>
#include <string>
#include <vector>

// Mirror of noisemaker-for-cpu test/stateful-chain-instances.test.js at
// ae27c898ecbe (ba9b93d + 4925da3 + ae27c898). Each stateful effect instance
// in a chain keeps its own state and zoom size; upstream's
// shaders/tests/test_stateful_instances.js covers two instances of one
// stateful effect in one chain, and the port keeps stateful state in each
// step's own resources, so the same behavior is pinned through the DSL/render
// interface: a chain with repeated stateful instances renders the same RGBA
// bytes as the flattened program where each instance runs on its own surface.
// The range also scopes the loop accumulator by chain (src/graph/executor.cpp,
// renderer.js runChainSync/runIteratedGroupSync/finishGroupResources), so a
// chain's second loopBegin/loopEnd region continues the first region's
// feedback surface instead of a zeroed one.
namespace {
using namespace noisemaker;

constexpr std::size_t kSize = 8U;
constexpr double kTime = 0.25;

RenderOptions render_options() {
  RenderOptions result;
  result.width = kSize;
  result.height = kSize;
  result.time = kTime;
  result.frame = 0U;
  result.seed = 1.0;
  result.delta_time = 0.0;
  return result;
}

std::vector<std::uint8_t> render_bytes(const std::string& source) {
  const Renderer renderer;
  const auto result = renderer.render(source, render_options());
  return result.to_rgba8();
}

void require_same_bytes(const std::string& left, const std::string& right) {
  const auto left_bytes = render_bytes(left);
  const auto right_bytes = render_bytes(right);
  REQUIRE(left_bytes.size() == right_bytes.size());
  REQUIRE(left_bytes == right_bytes);
}

// Two reactionDiffusion instances in one chain, each with its own state
// texture and zoom size (256 vs 64 pixels in the authority's terms).
const char* const kPairs[][2] = {
    {"search synth, mixer\n"
     "reactionDiffusion(zoom: x4).blendMode(tex: reactionDiffusion(zoom: x16)).write(o0)\n"
     "render(o0)\n",
     "search synth, mixer\n"
     "reactionDiffusion(zoom: x16).write(o2)\n"
     "reactionDiffusion(zoom: x4).blendMode(tex: read(o2)).write(o0)\n"
     "render(o0)\n"},
    // Two reactionDiffusion instances behind a synth, as chain arguments.
    {"search synth, mixer\n"
     "noise(seed: 1).blendMode(tex: reactionDiffusion(zoom: x4)).blendMode(tex: reactionDiffusion(zoom: x16)).write(o0)\n"
     "render(o0)\n",
     "search synth, mixer\n"
     "reactionDiffusion(zoom: x4).write(o2)\n"
     "reactionDiffusion(zoom: x16).write(o3)\n"
     "noise(seed: 1).blendMode(tex: read(o2)).blendMode(tex: read(o3)).write(o0)\n"
     "render(o0)\n"},
    // Repeated state preserves each explicit or default zoom.
    {"search synth, mixer\n"
     "reactionDiffusion(zoom: x4).blendMode(tex: reactionDiffusion()).blendMode(tex: reactionDiffusion(zoom: x16)).write(o0)\n"
     "render(o0)\n",
     "search synth, mixer\n"
     "reactionDiffusion().write(o2)\n"
     "reactionDiffusion(zoom: x16).write(o3)\n"
     "reactionDiffusion(zoom: x4).blendMode(tex: read(o2)).blendMode(tex: read(o3)).write(o0)\n"
     "render(o0)\n"},
    // Repeated stateful filters keep independent ping-pong state.
    {"search synth, filter\n"
     "noise(seed: 1).watercolor().watercolor().write(o0)\n"
     "render(o0)\n",
     "search synth, filter\n"
     "noise(seed: 1).watercolor().write(o1)\n"
     "read(o1).watercolor().write(o0)\n"
     "render(o0)\n"},
    // Different stateful effects in one chain size from their own zoom: the
    // reactionDiffusion state keeps the chain-scoped size, the
    // cellularAutomata instance gets its own.
    {"search synth, mixer\n"
     "reactionDiffusion(zoom: x4).blendMode(tex: cellularAutomata(zoom: x16)).write(o0)\n"
     "render(o0)\n",
     "search synth, mixer\n"
     "cellularAutomata(zoom: x16).write(o2)\n"
     "reactionDiffusion(zoom: x4).blendMode(tex: read(o2)).write(o0)\n"
     "render(o0)\n"},
    {"search synth, mixer\n"
     "noise(seed: 1).blendMode(tex: reactionDiffusion(zoom: x4)).blendMode(tex: cellularAutomata(zoom: x16)).write(o0)\n"
     "render(o0)\n",
     "search synth, mixer\n"
     "cellularAutomata(zoom: x16).write(o2)\n"
     "reactionDiffusion(zoom: x4).write(o3)\n"
     "noise(seed: 1).blendMode(tex: read(o3)).blendMode(tex: read(o2)).write(o0)\n"
     "render(o0)\n"},
};

}  // namespace

TEST(repeated_stateful_instances_render_as_their_flattened_per_instance_programs) {
  for (const auto& [inline_source, flat_source] : kPairs) {
    require_same_bytes(inline_source, flat_source);
  }
}

TEST(two_loop_regions_in_one_chain_share_the_chain_scoped_accumulator) {
  // Adjacent loop regions share the chain-scoped accumulator, whose content
  // equals the region input there, so each region passes the image through.
  require_same_bytes(
      "search synth, render\n"
      "perlin(seed: 1).loopBegin().loopEnd().write(o0)\n"
      "render(o0)\n",
      "search synth, render\n"
      "perlin(seed: 1).loopBegin().loopEnd().loopBegin().loopEnd().write(o0)\n"
      "render(o0)\n");
  // A step between the two regions makes the shared feedback observable: the
  // second region reads the first region's accumulator, which still holds the
  // pre-invert image, so the chain is not the flattened fresh-per-region form.
  const std::string shared =
      "search synth, filter, render\n"
      "perlin(seed: 1).loopBegin(alpha: 100).loopEnd().invert().loopBegin(alpha: 100).loopEnd().write(o0)\n"
      "render(o0)\n";
  const std::string fresh =
      "search synth, filter, render\n"
      "perlin(seed: 1).loopBegin(alpha: 100).loopEnd().write(o1)\n"
      "read(o1).invert().loopBegin(alpha: 100).loopEnd().write(o0)\n"
      "render(o0)\n";
  const auto shared_bytes = render_bytes(shared);
  const auto fresh_bytes = render_bytes(fresh);
  REQUIRE(shared_bytes.size() == fresh_bytes.size());
  REQUIRE(shared_bytes != fresh_bytes);
}

TEST(repeated_mesh_renderers_keep_the_loader_mesh_and_work_with_the_loader_in_another_chain) {
  require_same_bytes(
      "search render\n"
      "meshLoader().meshRender().meshRender().write(o0)\n"
      "render(o0)\n",
      "search render\n"
      "meshLoader().meshRender().write(o1)\n"
      "read(o1).meshRender().write(o0)\n"
      "render(o0)\n");
  const auto bytes = render_bytes(
      "search render\n"
      "meshLoader().write(o0)\n"
      "read(o0).meshRender().meshRender().write(o1)\n"
      "render(o1)\n");
  REQUIRE(bytes.size() == kSize * kSize * 4U);
}
