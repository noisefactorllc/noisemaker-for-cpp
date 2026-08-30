cmake_minimum_required(VERSION 3.20)

project(noisemaker-for-cpp-package-consumer LANGUAGES CXX)

# Deliberately no `set(CMAKE_CXX_STANDARD 20)`. This project compiles at the
# compiler's default standard, so it only builds if the imported target itself
# carries `cxx_std_20`. That makes this consumer the regression test for the
# package declaring its own language requirement: adding a standard here would
# hide the exact failure an outside adopter hits first.

find_package(noisemaker-for-cpp CONFIG REQUIRED)
if (NOT TARGET NoisemakerForCpp::noisemaker-cpu)
  message(FATAL_ERROR
    "installed package did not provide NoisemakerForCpp::noisemaker-cpu")
endif()

add_executable(noisemaker-package-consumer main.cpp)
target_link_libraries(noisemaker-package-consumer PRIVATE
  NoisemakerForCpp::noisemaker-cpu
)
