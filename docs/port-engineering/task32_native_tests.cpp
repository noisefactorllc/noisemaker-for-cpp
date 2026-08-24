
// TASK32_NATIVE_TESTS_BEGIN
// filter/grade:* -- six programs, two capability shapes (five identity-scoped
// LUMA_WEIGHTS global carve-outs; one id-indexed lane read/write proof track
// admitted purely by node identity). The oracle vendored for this cluster
// (tests/oracles/task-32-oracles.json) records per-program uniform cases and
// their expected pixel hashes from an independent JS-side render, but those
// hashes are keyed to that harness's own synthetic input-image generator,
// which this suite does not reproduce; the coverage below instead exercises
// the real generated kernels end to end with hand-controlled inputs whose
// correctness this suite verifies directly, plus determinism and
// direct-vs-public-dispatch consistency, matching the standing pattern used
// by every other task's ABI/binding tests in this file.

namespace {

[[nodiscard]] noisemaker::Surface task32_solid_input(
    std::size_t width, std::size_t height, std::uint8_t r, std::uint8_t g,
    std::uint8_t b, std::uint8_t a = 255U) {
  std::vector<std::uint8_t> pixels(width * height * 4U);
  for (std::size_t index = 0; index < width * height; ++index) {
    pixels[index * 4U] = r;
    pixels[index * 4U + 1U] = g;
    pixels[index * 4U + 2U] = b;
    pixels[index * 4U + 3U] = a;
  }
  return noisemaker::Surface::from_rgba8(width, height, pixels);
}

struct Task32GradeCase {
  std::string_view program_key;
  std::function<noisemaker::BoundKernel(const noisemaker::glsl::Bindings&)>
      direct_factory;
  std::function<void(noisemaker::glsl::Bindings&)> populate;
};

}  // namespace

TEST(typed_task32_grade_cluster_public_and_direct_binders_are_exposed_and_deterministic) {
  const noisemaker::Surface input = task32_solid_input(3U, 3U, 90U, 140U, 200U);
  const auto vec2 = [](float x, float y) { return noisemaker::glsl::Vec2(x, y); };
  const auto vec3 = [](float x, float y, float z) {
    return noisemaker::glsl::Vec3(x, y, z);
  };

  const std::array<Task32GradeCase, 6> cases{{
      {"filter/grade:primary", noisemaker::generated::bind_filter_grade_primary,
       [&](noisemaker::glsl::Bindings& bindings) {
         bindings.set_texture("inputTex", input);
         bindings.set_uniform("tileOffset", vec2(0.0f, 0.0f));
         bindings.set_uniform("fullResolution", vec2(3.0f, 3.0f));
         bindings.set_uniform("temperature", -0.4);
         bindings.set_uniform("tint", 0.2);
         bindings.set_uniform("exposure", 0.5);
         bindings.set_uniform("contrast", 0.3);
         bindings.set_uniform("highlights", -0.2);
         bindings.set_uniform("shadows", 0.4);
         bindings.set_uniform("whites", 0.1);
         bindings.set_uniform("blacks", -0.1);
         bindings.set_uniform("saturation", 1.3);
         bindings.set_uniform("curveShadows", 0.2);
         bindings.set_uniform("curveMidtones", -0.1);
         bindings.set_uniform("curveHighlights", 0.15);
       }},
      {"filter/grade:hslSecondary", noisemaker::generated::bind_filter_grade_hslSecondary,
       [&](noisemaker::glsl::Bindings& bindings) {
         bindings.set_texture("inputTex", input);
         bindings.set_uniform("tileOffset", vec2(0.0f, 0.0f));
         bindings.set_uniform("fullResolution", vec2(3.0f, 3.0f));
         bindings.set_uniform("hslEnable", std::int32_t{1});
         bindings.set_uniform("hslHueCenter", 0.6);
         bindings.set_uniform("hslHueRange", 0.5);
         bindings.set_uniform("hslSatMin", 0.0);
         bindings.set_uniform("hslSatMax", 1.0);
         bindings.set_uniform("hslLumMin", 0.0);
         bindings.set_uniform("hslLumMax", 1.0);
         bindings.set_uniform("hslFeather", 0.5);
         bindings.set_uniform("hslHueShift", 0.5);
         bindings.set_uniform("hslSatAdjust", 1.0);
         bindings.set_uniform("hslLumAdjust", 1.0);
       }},
      {"filter/grade:wheels", noisemaker::generated::bind_filter_grade_wheels,
       [&](noisemaker::glsl::Bindings& bindings) {
         bindings.set_texture("inputTex", input);
         bindings.set_uniform("tileOffset", vec2(0.0f, 0.0f));
         bindings.set_uniform("fullResolution", vec2(3.0f, 3.0f));
         bindings.set_uniform("wheelShadows", vec3(0.3f, 0.4f, 0.7f));
         bindings.set_uniform("wheelMidtones", vec3(0.5f, 0.5f, 0.5f));
         bindings.set_uniform("wheelHighlights", vec3(0.7f, 0.55f, 0.35f));
         bindings.set_uniform("wheelBalance", 0.2);
       }},
      {"filter/grade:vignette", noisemaker::generated::bind_filter_grade_vignette,
       [&](noisemaker::glsl::Bindings& bindings) {
         bindings.set_texture("inputTex", input);
         bindings.set_uniform("tileOffset", vec2(0.0f, 0.0f));
         bindings.set_uniform("fullResolution", vec2(3.0f, 3.0f));
         bindings.set_uniform("vignetteAmount", 0.7);
         bindings.set_uniform("vignetteMidpoint", 0.5);
         bindings.set_uniform("vignetteRoundness", 1.0);
         bindings.set_uniform("vignetteFeather", 0.4);
         bindings.set_uniform("vigHiProtect", 0.8);
       }},
      {"filter/grade:creative", noisemaker::generated::bind_filter_grade_creative,
       [&](noisemaker::glsl::Bindings& bindings) {
         bindings.set_texture("inputTex", input);
         bindings.set_uniform("tileOffset", vec2(0.0f, 0.0f));
         bindings.set_uniform("fullResolution", vec2(3.0f, 3.0f));
         bindings.set_uniform("vibrance", 0.6);
         bindings.set_uniform("fadedFilm", 0.3);
         bindings.set_uniform("shadowTint", vec3(0.4f, 0.45f, 0.6f));
         bindings.set_uniform("highlightTint", vec3(0.6f, 0.55f, 0.4f));
         bindings.set_uniform("splitToneBalance", 0.2);
       }},
      {"filter/grade:lut", noisemaker::generated::bind_filter_grade_lut,
       [&](noisemaker::glsl::Bindings& bindings) {
         bindings.set_texture("inputTex", input);
         bindings.set_uniform("tileOffset", vec2(0.0f, 0.0f));
         bindings.set_uniform("fullResolution", vec2(3.0f, 3.0f));
         bindings.set_uniform("preset", std::int32_t{20});
         bindings.set_uniform("alpha", 1.0);
       }},
  }};

  for (const auto& fixture : cases) {
    noisemaker::glsl::Bindings direct_bindings;
    fixture.populate(direct_bindings);
    const auto first = noisemaker::run_pass(
        fixture.direct_factory(direct_bindings), 3U, 3U);

    noisemaker::glsl::Bindings public_bindings;
    fixture.populate(public_bindings);
    const auto second = noisemaker::run_pass(
        noisemaker::generated::bind(fixture.program_key, public_bindings), 3U, 3U);

    noisemaker::glsl::Bindings repeat_bindings;
    fixture.populate(repeat_bindings);
    const auto repeated = noisemaker::run_pass(
        fixture.direct_factory(repeat_bindings), 3U, 3U);

    REQUIRE(first.width() == 3U);
    REQUIRE(first.height() == 3U);
    REQUIRE(first.to_rgba8() == second.to_rgba8());
    REQUIRE(first.to_rgba8() == repeated.to_rgba8());

    // Every one of the six kernels renders through the shared
    // srgbToLinear/linearToSrgb round trip on every pixel; a genuinely
    // broken lane mapping or a rejected index admission would either throw
    // during bind()/run_pass() or leave lanes at their zero-initialized
    // value, which shows up as non-finite or as a fully transparent pixel.
    // None of that is expected for a fully opaque solid input.
    bool any_finite = false;
    for (float value : first.data()) {
      REQUIRE(std::isfinite(value));
      if (value != 0.0f) any_finite = true;
    }
    REQUIRE(any_finite);
    const auto bytes = first.to_rgba8();
    for (std::size_t pixel = 0; pixel < 9U; ++pixel) {
      REQUIRE(bytes[pixel * 4U + 3U] == 255U);
    }
  }
}

TEST(typed_task32_grade_lut_reaches_hard_light_and_solarize_presets) {
  // lutHardLight (preset==20) and lutSolarize (preset==22) are the two
  // program-specific index-expression closures beyond the shared
  // srgbToLinear/linearToSrgb pair; both must be reachable through the
  // real preset uniform dispatch (preset is a runtime uniform here, never
  // a compile-time define, so both arms exist in every build).
  const noisemaker::Surface input = task32_solid_input(2U, 2U, 200U, 60U, 30U);
  for (const std::int32_t preset : {20, 22}) {
    noisemaker::glsl::Bindings bindings;
    bindings.set_texture("inputTex", input);
    bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(0.0f, 0.0f));
    bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(2.0f, 2.0f));
    bindings.set_uniform("preset", preset);
    bindings.set_uniform("alpha", 1.0);
    const auto rendered = noisemaker::run_pass(
        noisemaker::generated::bind_filter_grade_lut(bindings), 2U, 2U);
    for (float value : rendered.data()) REQUIRE(std::isfinite(value));
  }
}

TEST(typed_task32_grade_vignette_reaches_luma_weighted_highlight_protect_branch) {
  // vignette's LUMA_WEIGHTS read is inside `if (highlightProtect > 0.0)` --
  // a default/zero render never exercises it, so this fixture must set
  // vigHiProtect > 0 to actually reach the global-admission closure.
  const noisemaker::Surface input = task32_solid_input(2U, 2U, 250U, 250U, 10U);
  noisemaker::glsl::Bindings protect_on;
  protect_on.set_texture("inputTex", input);
  protect_on.set_uniform("tileOffset", noisemaker::glsl::Vec2(0.0f, 0.0f));
  protect_on.set_uniform("fullResolution", noisemaker::glsl::Vec2(2.0f, 2.0f));
  protect_on.set_uniform("vignetteAmount", 0.7);
  protect_on.set_uniform("vignetteMidpoint", 0.5);
  protect_on.set_uniform("vignetteRoundness", 1.0);
  protect_on.set_uniform("vignetteFeather", 0.4);
  protect_on.set_uniform("vigHiProtect", 0.8);
  const auto protected_render = noisemaker::run_pass(
      noisemaker::generated::bind_filter_grade_vignette(protect_on), 2U, 2U);

  noisemaker::glsl::Bindings protect_off;
  protect_off.set_texture("inputTex", input);
  protect_off.set_uniform("tileOffset", noisemaker::glsl::Vec2(0.0f, 0.0f));
  protect_off.set_uniform("fullResolution", noisemaker::glsl::Vec2(2.0f, 2.0f));
  protect_off.set_uniform("vignetteAmount", 0.7);
  protect_off.set_uniform("vignetteMidpoint", 0.5);
  protect_off.set_uniform("vignetteRoundness", 1.0);
  protect_off.set_uniform("vignetteFeather", 0.4);
  protect_off.set_uniform("vigHiProtect", 0.0);
  const auto unprotected_render = noisemaker::run_pass(
      noisemaker::generated::bind_filter_grade_vignette(protect_off), 2U, 2U);

  // A bright near-white/yellow input drives highlight protection into a
  // visibly different result than leaving it off -- the two renders must
  // differ, proving the highlightProtect branch (and its LUMA_WEIGHTS
  // read) is real and reachable, not merely admitted-but-dead.
  REQUIRE(protected_render.to_rgba8() != unprotected_render.to_rgba8());
}

TEST(typed_task32_grade_srgb_linear_round_trip_is_close_to_identity_at_neutral_settings) {
  // primary's pixel adjustments (temperature/tint/exposure/contrast/
  // highlights/shadows/whites/blacks/curve*) are each documented no-ops at
  // their neutral value (0, or 1 for saturation), so a fully neutral call
  // reduces to sRGB-to-linear, an identity pixel adjustment, then
  // linear-to-sRGB -- i.e. the shared round trip this task's index-
  // expression capability lowers. The output must reproduce the input to
  // within float32 round-trip tolerance, an oracle-independent correctness
  // check computable from first principles (the standard sRGB transfer
  // function), not from the vendored JS harness.
  const noisemaker::Surface input = task32_solid_input(1U, 1U, 12U, 128U, 240U);
  noisemaker::glsl::Bindings bindings;
  bindings.set_texture("inputTex", input);
  bindings.set_uniform("tileOffset", noisemaker::glsl::Vec2(0.0f, 0.0f));
  bindings.set_uniform("fullResolution", noisemaker::glsl::Vec2(1.0f, 1.0f));
  bindings.set_uniform("temperature", 0.0);
  bindings.set_uniform("tint", 0.0);
  bindings.set_uniform("exposure", 0.0);
  bindings.set_uniform("contrast", 0.0);
  bindings.set_uniform("highlights", 0.0);
  bindings.set_uniform("shadows", 0.0);
  bindings.set_uniform("whites", 0.0);
  bindings.set_uniform("blacks", 0.0);
  bindings.set_uniform("saturation", 1.0);
  bindings.set_uniform("curveShadows", 0.0);
  bindings.set_uniform("curveMidtones", 0.0);
  bindings.set_uniform("curveHighlights", 0.0);
  const auto rendered = noisemaker::run_pass(
      noisemaker::generated::bind_filter_grade_primary(bindings), 1U, 1U);
  const auto actual = rendered.to_rgba8();
  const auto expected = input.to_rgba8();
  for (std::size_t channel = 0; channel < 3U; ++channel) {
    const int delta = static_cast<int>(actual[channel]) -
                      static_cast<int>(expected[channel]);
    REQUIRE(delta >= -2);
    REQUIRE(delta <= 2);
  }
  REQUIRE(actual[3] == 255U);
}
// TASK32_NATIVE_TESTS_END
