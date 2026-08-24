cmake_minimum_required(VERSION 3.20)

project(noisemaker-for-cpp-package-consumer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(noisemaker-for-cpp CONFIG REQUIRED)
if (NOT TARGET NoisemakerForCpp::noisemaker-cpu)
  message(FATAL_ERROR
    "installed package did not provide NoisemakerForCpp::noisemaker-cpu")
endif()

add_executable(noisemaker-package-consumer main.cpp)
target_link_libraries(noisemaker-package-consumer PRIVATE
  NoisemakerForCpp::noisemaker-cpu
)
