
#include "noisemaker/numeric.hpp"
#include <cmath>
#include <cstdio>
#include <cstdint>

int main() {
    double test_values[] = {
        -3.5, -2.5, -1.5, -0.5, -0.0, 0.0, 0.5, 1.5, 2.5, 3.5,
        -0.4999999, -0.5000001, 0.5000001, 0.4999999,
        100.5, 1920.0, 1080.0, 0.0, 4.0, 3.0, 1.0
    };
    int n = sizeof(test_values) / sizeof(test_values[0]);
    std::printf("[\n");
    for (int i = 0; i < n; ++i) {
        double x = test_values[i];
        double glsl_r = noisemaker::glsl_round(x);
        double std_r = std::round(x);
        std::printf("  {\"x\": %.7f, \"glsl_round\": %.3f, \"std_round\": %.3f, "
                    "\"floor_x_plus_half\": %.3f, \"diverges\": %s}%s\n",
                    x, glsl_r, std_r, std::floor(x + 0.5),
                    (glsl_r != std_r) ? "true" : "false",
                    (i + 1 < n) ? "," : "");
    }
    std::printf("]\n");
    return 0;
}
