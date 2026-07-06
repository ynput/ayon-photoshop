cmake_minimum_required(VERSION 3.10)
project(ayon-photoshop-native)

set(CMAKE_CXX_STANDARD 11)

# Build universal binary for macOS (x86_64 + arm64)
if(APPLE)
    set(CMAKE_OSX_ARCHITECTURES "x86_64;arm64" CACHE STRING "Build architectures for macOS")
endif()

# Sources
file(GLOB_RECURSE SOURCES "src/*.cpp" "src/*.mm")

add_library(ayon-photoshop-native SHARED ${SOURCES})

# Target properties
set_target_properties(ayon-photoshop-native PROPERTIES
    MACOSX_BUNDLE FALSE
    BUNDLE ${BUNDLE}
    OUTPUT_NAME "ayon-photoshop-native"
)

# Include directories
target_include_directories(ayon-photoshop-native PRIVATE "src")

# Link libraries (example: Adobe SDK) - adjust as needed
# target_link_libraries(ayon-photoshop-native PRIVATE ...)
