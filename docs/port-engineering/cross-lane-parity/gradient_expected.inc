#pragma once
namespace gradient_oracle {
inline constexpr char kOracleJsonSha256[] = "47c6203099a692c88698ff4e3d64b360d04b50d7e723b83f6048555d11d9f1da";
inline constexpr char kCanonicalFactorySourceSha256[] = "66adc01c7df07298b40eaf74fddb7226fdf87bb18dea75b527640c88d0f40ebe";
inline constexpr unsigned kWidth = 6U;
inline constexpr unsigned kHeight = 5U;
inline constexpr std::array<std::uint32_t, 120> kWords{
    0x3f4e5084, 0x3f4e5084, 0x3f4e5084, 0x3f800000, 0x3eca1710, 0x3eca1710, 0x3eca1710, 0x3f800000,
    0x3c872e40, 0x3c872e40, 0x3c872e40, 0x3f800000, 0x3c8b5680, 0x3c8b5680, 0x3c8b5680, 0x3f800000,
    0x3ecfcf38, 0x3ecfcf38, 0x3ecfcf38, 0x3f800000, 0x3f4b7490, 0x3f4b7490, 0x3f4b7490, 0x3f800000,
    0x3ed57cf0, 0x3ed57cf0, 0x3ed57cf0, 0x3f800000, 0x3bbcbf00, 0x3bbcbf00, 0x3bbcbf00, 0x3f800000,
    0x3ecf96f6, 0x3ecf96f6, 0x3ecf96f6, 0x3f800000, 0x3ec9ded2, 0x3ec9ded2, 0x3ec9ded2, 0x3f800000,
    0x3bb13f00, 0x3bb13f00, 0x3bb13f00, 0x3f800000, 0x3ec454e4, 0x3ec454e4, 0x3ec454e4, 0x3f800000,
    0x3ce3f522, 0x3ce3f522, 0x3ce3f522, 0x3f800000, 0x3ed55938, 0x3ed55938, 0x3ed55938, 0x3f800000,
    0x3f4e398a, 0x3f4e398a, 0x3f4e398a, 0x3f800000, 0x3f4e3986, 0x3f4e3986, 0x3f4e3986, 0x3f800000,
    0x3ed55938, 0x3ed55938, 0x3ed55938, 0x3f800000, 0x3ce3f522, 0x3ce3f522, 0x3ce3f522, 0x3f800000,
    0x3ec454e4, 0x3ec454e4, 0x3ec454e4, 0x3f800000, 0x3bb13f00, 0x3bb13f00, 0x3bb13f00, 0x3f800000,
    0x3ec9deda, 0x3ec9deda, 0x3ec9deda, 0x3f800000, 0x3ecf96ee, 0x3ecf96ee, 0x3ecf96ee, 0x3f800000,
    0x3bbcbf00, 0x3bbcbf00, 0x3bbcbf00, 0x3f800000, 0x3ed57cf0, 0x3ed57cf0, 0x3ed57cf0, 0x3f800000,
    0x3f4b748c, 0x3f4b748c, 0x3f4b748c, 0x3f800000, 0x3ecfcf30, 0x3ecfcf30, 0x3ecfcf30, 0x3f800000,
    0x3c8b5580, 0x3c8b5580, 0x3c8b5580, 0x3f800000, 0x3c872e40, 0x3c872e40, 0x3c872e40, 0x3f800000,
    0x3eca1708, 0x3eca1708, 0x3eca1708, 0x3f800000, 0x3f4e5080, 0x3f4e5080, 0x3f4e5080, 0x3f800000,
};
inline constexpr std::array<std::uint8_t, 120> kBytes{
    206U, 206U, 206U, 255U, 101U, 101U, 101U, 255U,
    4U, 4U, 4U, 255U, 4U, 4U, 4U, 255U,
    103U, 103U, 103U, 255U, 203U, 203U, 203U, 255U,
    106U, 106U, 106U, 255U, 1U, 1U, 1U, 255U,
    103U, 103U, 103U, 255U, 101U, 101U, 101U, 255U,
    1U, 1U, 1U, 255U, 98U, 98U, 98U, 255U,
    7U, 7U, 7U, 255U, 106U, 106U, 106U, 255U,
    205U, 205U, 205U, 255U, 205U, 205U, 205U, 255U,
    106U, 106U, 106U, 255U, 7U, 7U, 7U, 255U,
    98U, 98U, 98U, 255U, 1U, 1U, 1U, 255U,
    101U, 101U, 101U, 255U, 103U, 103U, 103U, 255U,
    1U, 1U, 1U, 255U, 106U, 106U, 106U, 255U,
    203U, 203U, 203U, 255U, 103U, 103U, 103U, 255U,
    4U, 4U, 4U, 255U, 4U, 4U, 4U, 255U,
    101U, 101U, 101U, 255U, 206U, 206U, 206U, 255U,
};
}  // namespace gradient_oracle
