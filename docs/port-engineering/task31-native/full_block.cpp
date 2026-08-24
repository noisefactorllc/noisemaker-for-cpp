// TASK31_NATIVE_ORACLE_TABLE_BEGIN
// synth/curl:curl, profile curl-vector-math-tanh-wide-mod-v1. The oracle
// (tests/oracles/task-31-oracles.json) records 9 total render cases but only
// 6 carry eligible_for_native_binding: true -- the ones whose compile-time
// defines are exactly {OCTAVES:1, OUTPUT_MODE:3, RIDGES:true}, the sole
// profile bind_synth_curl_curl was generated against. The other 3
// (octaves-2-diverges-loop-unroll, output-mode-0-flowx-channel,
// ridges-false-no-fold) vary OCTAVES/OUTPUT_MODE/RIDGES and are
// public-source sensitivity evidence only; they are deliberately excluded
// from this table so it can never silently bind the wrong program. See
// eligibility_summary in the oracle: 6 eligible / 3 ineligible of 9 total.
struct Task31Case {
  std::string_view name;
  std::size_t width, height;
  std::uint32_t time_bits, scale_bits;
  std::int32_t seed;
  std::uint32_t speed_bits, intensity_bits;
  std::array<std::uint32_t, 2> tile_offset_bits;
  std::array<std::uint32_t, 2> full_resolution_bits;
  std::string_view f32_hash, rgba8_hash;
  std::array<std::uint32_t, 30> probes;
  std::size_t finite_lanes, nonfinite_lanes;
};
constexpr std::array<Task31Case, 6> kTask31NativeCases{{
    {"default-seed0-time0", 6U, 5U,
     0x00000000U, 0x41200000U, 0, 0x42480000U, 0x3f800000U,
     {0x00000000U, 0x00000000U}, {0x40c00000U, 0x40a00000U},
     "38fb7d9ac469347a5d53b1d065550cec64923b8f8ed9792bd62d11773c95bb55",
     "74304e9ef0601a4886a053299a16246b57113f1584f451109fc4dbcc95a33da9",
     {0U,0U,0x3f3d7224U,0x3f35a327U,0x3f22bfe4U,0x3f800000U, 5U,0U,0x3f5e4b9cU,0x3ec855a8U,0x3f3bff83U,0x3f800000U, 0U,4U,0x3edc8714U,0x3f7914b0U,0x3ef464bcU,0x3f800000U, 5U,4U,0x3f423dd3U,0x3f42aa52U,0x3eed8a9eU,0x3f800000U, 3U,2U,0x3f23a326U,0x3f3f9115U,0x3f71088aU,0x3f800000U},
     120U, 0U},
    {"seed7-tiled-midtime", 5U, 6U,
     0x40600000U, 0x41700000U, 7, 0x42a00000U, 0x40200000U,
     {0x40400000U, 0x40000000U}, {0x41500000U, 0x41300000U},
     "e6f49b49ebee9b4bec0631e7209f2daf70a207a8f8a659044a40f7db8388c92f",
     "0b0aeb879b6461fa23d192882dcce8a4d484821d6f638a6d2868911ec95cc81a",
     {0U,0U,0x3d3deb00U,0x3f658d32U,0x3f544168U,0x3f800000U, 4U,0U,0x3f455f7fU,0x3f11d188U,0x3e65835cU,0x3f800000U, 0U,5U,0x3f40e116U,0x3e9e5e30U,0x3f402514U,0x3f800000U, 4U,5U,0x3f714b76U,0x3e9e81dcU,0x3eef7070U,0x3f800000U, 2U,3U,0x3ec63ab8U,0x3e0042a0U,0x3f405580U,0x3f800000U},
     120U, 0U},
    {"negative-seed-drives-negative-mod-operands", 8U, 3U,
     0x41400000U, 0x00000000U, -13, 0x00000000U, 0x3f400000U,
     {0x00000000U, 0x00000000U}, {0x41000000U, 0x40400000U},
     "6325f2198d92d04b02b6ff0b5f8102709f280c176d4a008dc5d0ddafa2c183d0",
     "ff92d82a215c70ea490077f882e342d3ba92cc9ffec70a69d4c59d527228230b",
     {0U,0U,0x3f13b318U,0x3f323b7cU,0x3f060378U,0x3f800000U, 7U,0U,0x3f1eeef0U,0x3f7ad428U,0x3f605329U,0x3f800000U, 0U,2U,0x3f7c861cU,0x3f32614eU,0x3f6875d2U,0x3f800000U, 7U,2U,0x3f6c7cb8U,0x3f6d8ce8U,0x3f7fcc4dU,0x3f800000U, 4U,1U,0x3f4eb8aaU,0x3f03dfc6U,0x3f1ad600U,0x3f800000U},
     96U, 0U},
    {"negative-intensity-flips-tanh-sign", 4U, 4U,
     0x42c88000U, 0x41a73333U, 99, 0x43480000U, 0xc0800000U,
     {0x00000000U, 0x00000000U}, {0x40800000U, 0x40800000U},
     "311e9b9662461dac97a4b9f5a167707913aec4120bb63b8b590376128b237fcd",
     "df8c2c90ccf93aff72894448dbe5292ece5fd24f3f2ce21fb68f4e23a4001e8b",
     {0U,0U,0x3d1aa980U,0x3971c000U,0x3d53a490U,0x3f800000U, 3U,0U,0x3c16d300U,0x3984a000U,0x3cf9cb00U,0x3f800000U, 0U,3U,0x3dd51ee0U,0x3a23d000U,0x3e29a1e4U,0x3f800000U, 3U,3U,0x3cd63d80U,0x39ed4000U,0x3dc672a8U,0x3f800000U, 2U,2U,0x3cd09c00U,0x39b0b000U,0x3d979860U,0x3f800000U},
     64U, 0U},
    {"large-seed-negative-scale-negative-speed", 7U, 7U,
     0x3a83126fU, 0xc0a00000U, 1000000, 0xc1f00000U, 0x42480000U,
     {0x00000000U, 0x00000000U}, {0x40e00000U, 0x40e00000U},
     "aa573876f73366853d5898cb9a7e97f920dbae298f41f4ba0811d75b44e3991a",
     "38983169f7e627250c60981b9fcfec851a56521e1679eceae2c3ae657b0c2fff",
     {0U,0U,0x00000000U,0x00000000U,0x377e0000U,0x3f800000U, 6U,0U,0x3d920150U,0x00000000U,0x37000000U,0x3f800000U, 0U,6U,0x00000000U,0x00000000U,0x00000000U,0x3f800000U, 6U,6U,0x00000000U,0x00000000U,0x37070000U,0x3f800000U, 3U,3U,0x00000000U,0x3e804b10U,0x00000000U,0x3f800000U},
     196U, 0U},
    {"two-pi-time-near-identity-intensity", 10U, 2U,
     0x40c90fdbU, 0x412fffffU, 0, 0x3f800000U, 0x3a83126fU,
     {0x00000000U, 0x00000000U}, {0x41200000U, 0x40000000U},
     "7a006260356fcf49ebcc27ca9069f37cfa7ee935d0d94e5d3ea2c9649befe95d",
     "6d92a8ea911d0d96dad7f2d76f2647e8b612e645140157668298db20a9412d4b",
     {0U,0U,0x3f7fdb26U,0x3f7fda8aU,0x3f7fd94aU,0x3f800000U, 9U,0U,0x3f7fe91eU,0x3f7ff49cU,0x3f7fdab4U,0x3f800000U, 0U,1U,0x3f7ffbdaU,0x3f7fe4d7U,0x3f7ff7feU,0x3f800000U, 9U,1U,0x3f7ff0e0U,0x3f7fe1d6U,0x3f7fffb4U,0x3f800000U, 5U,1U,0x3f7fc7fdU,0x3f7febe0U,0x3f7feb84U,0x3f800000U},
     80U, 0U},
}};

// The 10 direct_tanh_rows from the oracle, transcribed verbatim: {input_bits,
// result_bits} for the one authenticated tanh(vec3) call site
// (tanh_vec3_main), each a real GLSL tanh() applied lane-wise.
struct Task31TanhRow {
  std::array<std::uint32_t, 3> input_bits;
  std::array<std::uint32_t, 3> result_bits;
};
constexpr std::array<Task31TanhRow, 10> kTask31DirectTanhRows{{
    {{0x00000000U,0x00000000U,0x00000000U}, {0x00000000U,0x00000000U,0x00000000U}},
    {{0x80000000U,0x00000000U,0x00000000U}, {0x80000000U,0x00000000U,0x00000000U}},
    {{0x3f800000U,0xbf800000U,0x3f000000U}, {0x3f42f7d6U,0xbf42f7d6U,0x3eec9a9fU}},
    {{0xbf800000U,0x3f800000U,0xbf000000U}, {0xbf42f7d6U,0x3f42f7d6U,0xbeec9a9fU}},
    {{0x7f7fffffU,0xff7fffffU,0x00000000U}, {0x3f800000U,0xbf800000U,0x00000000U}},
    {{0xff7fffffU,0x7f7fffffU,0x7f7fffffU}, {0xbf800000U,0x3f800000U,0x3f800000U}},
    {{0x00000001U,0x80000001U,0x00000000U}, {0x00000001U,0x80000001U,0x00000000U}},
    {{0x41a00000U,0xc1a00000U,0x38d1b717U}, {0x3f800000U,0xbf800000U,0x38d1b717U}},
    {{0x40490fd0U,0xc0490fd0U,0x402df84dU}, {0x3f7f0bb0U,0xbf7f0bb0U,0x3f7dc7bbU}},
    {{0x2edbe6ffU,0xaedbe6ffU,0x00000000U}, {0x2edbe6ffU,0xaedbe6ffU,0x00000000U}},
}};

// The 8 direct_mod_rows from the oracle, transcribed verbatim: {x_bits (the
// vec4 dividend lanes), y_bits (the scalar divisor, always 289.0), the real
// GLSL floor-mod result, the naive (C/std::fmod, sign-of-dividend) result,
// and whether the two diverge}. GLSL mod(x,y) is x - y*floor(x/y) (sign
// follows the divisor); these rows -- negative operands, +-0.0, and
// near-float32 extremes -- are exactly where a naive std::fmod substitution
// (sign follows the dividend) breaks.
struct Task31ModRow {
  std::array<std::uint32_t, 4> x_bits;
  std::uint32_t y_bits;
  std::array<std::uint32_t, 4> real_result_bits;
  std::array<std::uint32_t, 4> naive_result_bits;
  bool diverges_from_naive_fmod;
};
constexpr std::array<Task31ModRow, 8> kTask31DirectModRows{{
    {{0x00000000U,0x00000000U,0x00000000U,0x00000000U}, 0x43908000U, {0x00000000U,0x00000000U,0x00000000U,0x00000000U}, {0x00000000U,0x00000000U,0x00000000U,0x00000000U}, false},
    {{0x80000000U,0x00000000U,0x00000000U,0x00000000U}, 0x43908000U, {0x00000000U,0x00000000U,0x00000000U,0x00000000U}, {0x80000000U,0x00000000U,0x00000000U,0x00000000U}, true},
    {{0x43908000U,0xc3908000U,0x44108000U,0xc4108000U}, 0x43908000U, {0x00000000U,0x00000000U,0x00000000U,0x00000000U}, {0x00000000U,0x80000000U,0x00000000U,0x80000000U}, true},
    {{0xbf800000U,0xbf000000U,0xc3908000U,0xc3908000U}, 0x43908000U, {0x43900000U,0x43904000U,0x00000000U,0x00000000U}, {0xbf800000U,0xbf000000U,0x80000000U,0x80000000U}, true},
    {{0x3f800000U,0x3f000000U,0x43908000U,0x43908000U}, 0x43908000U, {0x3f800000U,0x3f000000U,0x00000000U,0x00000000U}, {0x3f800000U,0x3f000000U,0x00000000U,0x00000000U}, false},
    {{0xc7686c00U,0x47686c00U,0xbf800000U,0x3f800000U}, 0x43908000U, {0x42080000U,0x437f0000U,0x43900000U,0x3f800000U}, {0xc37f0000U,0x437f0000U,0xbf800000U,0x3f800000U}, true},
    {{0x7f7fffffU,0xff7fffffU,0x00000001U,0x80000001U}, 0x43908000U, {0x00000000U,0x00000000U,0x00000001U,0x43908000U}, {0x433b0000U,0xc33b0000U,0x00000001U,0x80000001U}, true},
    {{0xccbebc20U,0x4cbebc20U,0xbe022681U,0x3e022681U}, 0x43908000U, {0x428a0000U,0x435c0000U,0x43906fbbU,0x3e022681U}, {0xc35c0000U,0x435c0000U,0xbe022681U,0x3e022681U}, true},
}};
// TASK31_NATIVE_ORACLE_TABLE_END

[[nodiscard]] noisemaker::glsl::Bindings task31_bindings(
    const Task31Case& fixture, std::string_view omit = {},
    std::string_view wrong = {}) {
  noisemaker::glsl::Bindings bindings;
  const auto f32 = [](std::uint32_t bits) {
    return noisemaker::uint_bits_to_float(bits);
  };
  const auto vector = [&](std::string_view name, noisemaker::glsl::Vec2 value) {
    if (name == omit) return;
    if (name == wrong)
      bindings.set_uniform(std::string(name), std::int32_t{1});
    else
      bindings.set_uniform(std::string(name), value);
  };
  const auto number = [&](std::string_view name, float value) {
    if (name == omit) return;
    if (name == wrong)
      bindings.set_uniform(std::string(name), true);
    else
      bindings.set_uniform(std::string(name), value);
  };
  const auto seed_int = [&](std::string_view name, std::int32_t value) {
    if (name == omit) return;
    // seed is std::int32_t, NOT float -- binding it as float must throw.
    if (name == wrong)
      bindings.set_uniform(std::string(name), 0.0f);
    else
      bindings.set_uniform(std::string(name), value);
  };
  vector("resolution", {static_cast<float>(fixture.width),
                        static_cast<float>(fixture.height)});
  vector("tileOffset", {f32(fixture.tile_offset_bits[0]),
                        f32(fixture.tile_offset_bits[1])});
  vector("fullResolution", {f32(fixture.full_resolution_bits[0]),
                            f32(fixture.full_resolution_bits[1])});
  number("time", f32(fixture.time_bits));
  number("scale", f32(fixture.scale_bits));
  seed_int("seed", fixture.seed);
  number("speed", f32(fixture.speed_bits));
  number("intensity", f32(fixture.intensity_bits));
  return bindings;
}

TEST(typed_task31_curl_public_oracles_are_exact_repeatable_finite_and_match_both_binders) {
  for (const auto& fixture : kTask31NativeCases) {
    const auto first = noisemaker::run_pass(
        noisemaker::generated::bind_synth_curl_curl(task31_bindings(fixture)),
        fixture.width, fixture.height);
    const auto second = noisemaker::run_pass(
        noisemaker::generated::bind("synth/curl:curl", task31_bindings(fixture)),
        fixture.width, fixture.height);
    const auto repeated = noisemaker::run_pass(
        noisemaker::generated::bind_synth_curl_curl(task31_bindings(fixture)),
        fixture.width, fixture.height);

    REQUIRE(first.width() == fixture.width);
    REQUIRE(first.height() == fixture.height);
    REQUIRE(second.width() == fixture.width);
    REQUIRE(second.height() == fixture.height);
    const auto f32_bytes = task23_float_bytes(first);
    REQUIRE(f32_bytes == task23_float_bytes(second));
    REQUIRE(f32_bytes == task23_float_bytes(repeated));
    REQUIRE(task23_hex(task23_sha256(f32_bytes)) == fixture.f32_hash);
    REQUIRE(task23_hex(task23_sha256(first.to_rgba8())) == fixture.rgba8_hash);
    REQUIRE(first.to_rgba8() == second.to_rgba8());

    std::size_t finite = 0U;
    for (float value : first.data()) {
      if (std::isfinite(value)) ++finite;
    }
    REQUIRE(finite == fixture.finite_lanes);
    REQUIRE((first.data().size() - finite) == fixture.nonfinite_lanes);

    for (std::size_t probe = 0; probe < 5U; ++probe) {
      const std::size_t x = fixture.probes[probe * 6U];
      const std::size_t y = fixture.probes[probe * 6U + 1U];
      const std::size_t offset = (y * fixture.width + x) * 4U;
      for (std::size_t lane = 0; lane < 4U; ++lane) {
        REQUIRE(noisemaker::float_bits_to_uint(first.data()[offset + lane]) ==
                fixture.probes[probe * 6U + 2U + lane]);
      }
    }
  }
}

TEST(typed_task31_curl_binding_abi_rejects_every_missing_and_wrong_input_and_accepts_extras) {
  constexpr std::array<std::string_view, 8> names{
      "resolution", "tileOffset", "fullResolution", "time",
      "scale",      "seed",       "speed",          "intensity"};
  const auto& fixture = kTask31NativeCases[0];
  for (std::string_view name : names) {
    REQUIRE_THROWS_AS(
        noisemaker::generated::bind_synth_curl_curl(
            task31_bindings(fixture, name)),
        noisemaker::glsl::KernelBindingError);
    REQUIRE_THROWS_AS(
        noisemaker::generated::bind_synth_curl_curl(
            task31_bindings(fixture, {}, name)),
        noisemaker::glsl::KernelBindingError);
    REQUIRE_THROWS_AS(
        noisemaker::generated::bind("synth/curl:curl",
                                    task31_bindings(fixture, name)),
        noisemaker::glsl::KernelBindingError);
  }

  // seed is std::int32_t, not float. Binding it as float must throw, called
  // out explicitly (not just covered incidentally by the loop above).
  noisemaker::glsl::Bindings seed_as_float = task31_bindings(fixture);
  seed_as_float.set_uniform("seed", 0.0f);
  REQUIRE_THROWS_AS(
      noisemaker::generated::bind_synth_curl_curl(seed_as_float),
      noisemaker::glsl::KernelBindingError);
  REQUIRE_THROWS_AS(
      noisemaker::generated::bind("synth/curl:curl", seed_as_float),
      noisemaker::glsl::KernelBindingError);

  auto with_extras = task31_bindings(fixture);
  with_extras.set_uniform("unrelated", true);
  with_extras.set_uniform("unrelatedNumber", 7.0f);
  const auto output = noisemaker::run_pass(
      noisemaker::generated::bind_synth_curl_curl(with_extras), fixture.width,
      fixture.height);
  REQUIRE(task23_hex(task23_sha256(task23_float_bytes(output))) ==
          fixture.f32_hash);
}

TEST(typed_task31_direct_tanh_rows_match_real_glsl_tanh_vec3) {
  for (const auto& row : kTask31DirectTanhRows) {
    const noisemaker::glsl::Vec3 input(
        noisemaker::uint_bits_to_float(row.input_bits[0]),
        noisemaker::uint_bits_to_float(row.input_bits[1]),
        noisemaker::uint_bits_to_float(row.input_bits[2]));
    const noisemaker::glsl::Vec3 result = noisemaker::glsl::tanh(input);
    for (std::size_t lane = 0; lane < 3U; ++lane) {
      REQUIRE(noisemaker::float_bits_to_uint(result[lane]) ==
              row.result_bits[lane]);
    }
  }
}

TEST(typed_task31_direct_mod_rows_match_real_glsl_floor_mod_not_fmod) {
  for (const auto& row : kTask31DirectModRows) {
    const noisemaker::glsl::Vec4 x(
        noisemaker::uint_bits_to_float(row.x_bits[0]),
        noisemaker::uint_bits_to_float(row.x_bits[1]),
        noisemaker::uint_bits_to_float(row.x_bits[2]),
        noisemaker::uint_bits_to_float(row.x_bits[3]));
    const double y =
        static_cast<double>(noisemaker::uint_bits_to_float(row.y_bits));
    const noisemaker::glsl::Vec4 result = noisemaker::glsl::mod(x, y);
    bool any_lane_diverges = false;
    for (std::size_t lane = 0; lane < 4U; ++lane) {
      REQUIRE(noisemaker::float_bits_to_uint(result[lane]) ==
              row.real_result_bits[lane]);
      const float naive = std::fmod(x[lane], static_cast<float>(y));
      REQUIRE(noisemaker::float_bits_to_uint(naive) ==
              row.naive_result_bits[lane]);
      if (row.real_result_bits[lane] != row.naive_result_bits[lane])
        any_lane_diverges = true;
    }
    REQUIRE(any_lane_diverges == row.diverges_from_naive_fmod);
  }
}

// TASK31_DIRECT_ABI_HARNESS_BEGIN
// Two structurally distinct modes per closure-hazard site -- the real
// production math and the exact mutation the oracle's public_factory_
// mutations table names for that site (tanh-vec3-identity-passthrough,
// mod-vec4-permute-naive-fmod) -- each computed by its own independent code
// path (neither delegates to the other), proven pairwise-unique below by an
// aggregate signature over the computed numeric payload only (mode id, mode
// name, and the one-hot arm_dispatches array are excluded from the
// signature, per the Task 26 anti-vacuity rule).
enum class Task31TanhMode : std::uint32_t {
  real_saturating_tanh = 0,
  naive_identity_passthrough = 1,
};
constexpr std::array<std::string_view, 2> kTask31TanhModeNames{{
    "real-saturating-tanh-vec3",
    "naive-identity-passthrough-vec3",
}};
struct Task31TanhWitness {
  Task31TanhMode mode;
  std::string_view name;
  std::array<noisemaker::glsl::Vec3, 10> results;
  std::array<std::uint32_t, 2> arm_dispatches{};
};

enum class Task31ModMode : std::uint32_t {
  real_floor_mod = 0,
  naive_truncating_fmod = 1,
};
constexpr std::array<std::string_view, 2> kTask31ModModeNames{{
    "real-floor-mod-vec4-scalar",
    "naive-truncating-fmod-vec4-scalar",
}};
struct Task31ModWitness {
  Task31ModMode mode;
  std::string_view name;
  std::array<noisemaker::glsl::Vec4, 8> results;
  std::array<std::uint32_t, 2> arm_dispatches{};
};

// TASK31_DIRECT_ABI_SWITCH_BEGIN
[[nodiscard]] Task31TanhWitness task31_dispatch_tanh_mode(Task31TanhMode mode) {
  Task31TanhWitness witness{};
  witness.mode = mode;
  switch (mode) {
    case Task31TanhMode::real_saturating_tanh: {
      witness.name = kTask31TanhModeNames[0];
      witness.arm_dispatches[0] = 1U;
      for (std::size_t i = 0; i < kTask31DirectTanhRows.size(); ++i) {
        const auto& row = kTask31DirectTanhRows[i];
        const noisemaker::glsl::Vec3 input(
            noisemaker::uint_bits_to_float(row.input_bits[0]),
            noisemaker::uint_bits_to_float(row.input_bits[1]),
            noisemaker::uint_bits_to_float(row.input_bits[2]));
        witness.results[i] = noisemaker::glsl::tanh(input);
      }
      return witness;
    }
    case Task31TanhMode::naive_identity_passthrough: {
      witness.name = kTask31TanhModeNames[1];
      witness.arm_dispatches[1] = 1U;
      for (std::size_t i = 0; i < kTask31DirectTanhRows.size(); ++i) {
        const auto& row = kTask31DirectTanhRows[i];
        witness.results[i] = noisemaker::glsl::Vec3(
            noisemaker::uint_bits_to_float(row.input_bits[0]),
            noisemaker::uint_bits_to_float(row.input_bits[1]),
            noisemaker::uint_bits_to_float(row.input_bits[2]));
      }
      return witness;
    }
  }
  throw std::invalid_argument(
      "invalid Task31 tanh mode " +
      std::to_string(static_cast<std::uint32_t>(mode)));
}

[[nodiscard]] Task31ModWitness task31_dispatch_mod_mode(Task31ModMode mode) {
  Task31ModWitness witness{};
  witness.mode = mode;
  switch (mode) {
    case Task31ModMode::real_floor_mod: {
      witness.name = kTask31ModModeNames[0];
      witness.arm_dispatches[0] = 1U;
      for (std::size_t i = 0; i < kTask31DirectModRows.size(); ++i) {
        const auto& row = kTask31DirectModRows[i];
        const noisemaker::glsl::Vec4 x(
            noisemaker::uint_bits_to_float(row.x_bits[0]),
            noisemaker::uint_bits_to_float(row.x_bits[1]),
            noisemaker::uint_bits_to_float(row.x_bits[2]),
            noisemaker::uint_bits_to_float(row.x_bits[3]));
        const double y =
            static_cast<double>(noisemaker::uint_bits_to_float(row.y_bits));
        witness.results[i] = noisemaker::glsl::mod(x, y);
      }
      return witness;
    }
    case Task31ModMode::naive_truncating_fmod: {
      witness.name = kTask31ModModeNames[1];
      witness.arm_dispatches[1] = 1U;
      for (std::size_t i = 0; i < kTask31DirectModRows.size(); ++i) {
        const auto& row = kTask31DirectModRows[i];
        const float y = noisemaker::uint_bits_to_float(row.y_bits);
        noisemaker::glsl::Vec4 result;
        for (std::size_t lane = 0; lane < 4U; ++lane) {
          result[lane] =
              std::fmod(noisemaker::uint_bits_to_float(row.x_bits[lane]), y);
        }
        witness.results[i] = result;
      }
      return witness;
    }
  }
  throw std::invalid_argument(
      "invalid Task31 mod mode " +
      std::to_string(static_cast<std::uint32_t>(mode)));
}
// TASK31_DIRECT_ABI_SWITCH_END

[[nodiscard]] std::array<std::uint32_t, 30> task31_tanh_signature(
    const Task31TanhWitness& witness) {
  std::array<std::uint32_t, 30> signature{};
  std::size_t cursor = 0U;
  for (const auto& result : witness.results) {
    for (std::size_t lane = 0; lane < 3U; ++lane)
      signature[cursor++] = noisemaker::float_bits_to_uint(result[lane]);
  }
  return signature;
}

[[nodiscard]] std::array<std::uint32_t, 32> task31_mod_signature(
    const Task31ModWitness& witness) {
  std::array<std::uint32_t, 32> signature{};
  std::size_t cursor = 0U;
  for (const auto& result : witness.results) {
    for (std::size_t lane = 0; lane < 4U; ++lane)
      signature[cursor++] = noisemaker::float_bits_to_uint(result[lane]);
  }
  return signature;
}
// TASK31_DIRECT_ABI_HARNESS_END

TEST(typed_task31_direct_tanh_mode_switch_two_distinct_paths_match_oracle_and_named_mutation) {
  std::array<Task31TanhWitness, 2> witnesses{
      task31_dispatch_tanh_mode(Task31TanhMode::real_saturating_tanh),
      task31_dispatch_tanh_mode(Task31TanhMode::naive_identity_passthrough),
  };
  for (std::size_t index = 0; index < witnesses.size(); ++index) {
    const auto mode = static_cast<Task31TanhMode>(index);
    REQUIRE(witnesses[index].mode == mode);
    REQUIRE(witnesses[index].name == kTask31TanhModeNames[index]);
    REQUIRE(witnesses[index].arm_dispatches[index] == 1U);
    REQUIRE(std::count(witnesses[index].arm_dispatches.begin(),
                       witnesses[index].arm_dispatches.end(), 1U) == 1);
  }
  // Mode 0 is the exact production capability: it must match every oracle
  // direct_tanh_rows result bit-for-bit.
  for (std::size_t i = 0; i < kTask31DirectTanhRows.size(); ++i) {
    const auto& row = kTask31DirectTanhRows[i];
    for (std::size_t lane = 0; lane < 3U; ++lane) {
      REQUIRE(noisemaker::float_bits_to_uint(witnesses[0].results[i][lane]) ==
              row.result_bits[lane]);
      // Mode 1 (the named tanh-vec3-identity-passthrough mutation) must
      // reproduce the *input*, not the tanh result.
      REQUIRE(noisemaker::float_bits_to_uint(witnesses[1].results[i][lane]) ==
              row.input_bits[lane]);
    }
  }
  // The saturating-compression hazard the oracle names as "expected:
  // nonzero" must actually be observed: real tanh must diverge from identity
  // passthrough bit-for-bit on exactly the rows where the oracle's own
  // result_bits differ from its input_bits (rows with |x| large enough to
  // saturate, or non-tiny enough for tanh's curvature to show up in the
  // rounded float32 result) -- 6 of the 10 rows -- and agree exactly on the
  // remaining 4 (the true zero, negative-zero, and two subnormal rows where
  // tanh(x) rounds back to x bit-for-bit).
  std::size_t diverging_rows = 0U;
  for (std::size_t i = 0; i < kTask31DirectTanhRows.size(); ++i) {
    if (task31_tanh_signature(witnesses[0])[i * 3U] !=
            task31_tanh_signature(witnesses[1])[i * 3U] ||
        task31_tanh_signature(witnesses[0])[i * 3U + 1U] !=
            task31_tanh_signature(witnesses[1])[i * 3U + 1U] ||
        task31_tanh_signature(witnesses[0])[i * 3U + 2U] !=
            task31_tanh_signature(witnesses[1])[i * 3U + 2U]) {
      ++diverging_rows;
    }
  }
  REQUIRE(diverging_rows == 6U);

  const std::array<std::array<std::uint32_t, 30>, 2> signatures{
      task31_tanh_signature(witnesses[0]), task31_tanh_signature(witnesses[1])};
  REQUIRE(signatures[0] != signatures[1]);

  REQUIRE_THROWS_AS(task31_dispatch_tanh_mode(static_cast<Task31TanhMode>(2U)),
                    std::invalid_argument);
  try {
    (void)task31_dispatch_tanh_mode(static_cast<Task31TanhMode>(2U));
    REQUIRE(false);
  } catch (const std::invalid_argument& error) {
    REQUIRE(std::string_view(error.what()) ==
            "invalid Task31 tanh mode 2");
  }
}

TEST(typed_task31_direct_mod_mode_switch_two_distinct_paths_match_oracle_and_named_mutation) {
  std::array<Task31ModWitness, 2> witnesses{
      task31_dispatch_mod_mode(Task31ModMode::real_floor_mod),
      task31_dispatch_mod_mode(Task31ModMode::naive_truncating_fmod),
  };
  for (std::size_t index = 0; index < witnesses.size(); ++index) {
    const auto mode = static_cast<Task31ModMode>(index);
    REQUIRE(witnesses[index].mode == mode);
    REQUIRE(witnesses[index].name == kTask31ModModeNames[index]);
    REQUIRE(witnesses[index].arm_dispatches[index] == 1U);
    REQUIRE(std::count(witnesses[index].arm_dispatches.begin(),
                       witnesses[index].arm_dispatches.end(), 1U) == 1);
  }
  bool any_divergence = false;
  bool any_agreement = false;
  for (std::size_t i = 0; i < kTask31DirectModRows.size(); ++i) {
    const auto& row = kTask31DirectModRows[i];
    bool row_diverges = false;
    for (std::size_t lane = 0; lane < 4U; ++lane) {
      REQUIRE(noisemaker::float_bits_to_uint(witnesses[0].results[i][lane]) ==
              row.real_result_bits[lane]);
      REQUIRE(noisemaker::float_bits_to_uint(witnesses[1].results[i][lane]) ==
              row.naive_result_bits[lane]);
      if (row.real_result_bits[lane] != row.naive_result_bits[lane])
        row_diverges = true;
    }
    // Cross-check the named mutation's per-row divergence against the
    // oracle's own diverges_from_naive_fmod flag -- this is the row set
    // where a naive port silently breaks (negative operands, +-0.0, and
    // near-float32 extremes), so the flag must hold exactly as recorded.
    REQUIRE(row_diverges == row.diverges_from_naive_fmod);
    if (row_diverges) any_divergence = true; else any_agreement = true;
  }
  REQUIRE(any_divergence);
  REQUIRE(any_agreement);

  const std::array<std::array<std::uint32_t, 32>, 2> signatures{
      task31_mod_signature(witnesses[0]), task31_mod_signature(witnesses[1])};
  REQUIRE(signatures[0] != signatures[1]);

  REQUIRE_THROWS_AS(task31_dispatch_mod_mode(static_cast<Task31ModMode>(2U)),
                    std::invalid_argument);
  try {
    (void)task31_dispatch_mod_mode(static_cast<Task31ModMode>(2U));
    REQUIRE(false);
  } catch (const std::invalid_argument& error) {
    REQUIRE(std::string_view(error.what()) == "invalid Task31 mod mode 2");
  }
}

// Width policy for Task 31's two closure-hazard call sites (mod at N==3||4
// with a scalar divisor, tanh at N==3 only) is already exhaustively proven
// at compile time by HasGlslMod/HasGlslTanh in tests/test_glsl_runtime.cpp
// (N==2/3/4 mod, both vector- and scalar-divisor forms; N==3 tanh only,
// N==2/4 rejected). Duplicating that static_assert battery here would add
// no signal, per this task's brief -- the runtime truth-table coverage
// above (direct_tanh_rows / direct_mod_rows, both real and named-mutation
// paths) is Curl-value-specific and is where the actual new signal lives.
