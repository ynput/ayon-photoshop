cmake_minimum_required(VERSION 3.15)
project(ayon-photoshop-plugin)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Build universal binary for macOS (arm64 + x86_64)
if(APPLE)
    set(CMAKE_OSX_ARCHITECTURES "arm64;x86_64" CACHE STRING "Build architectures for macOS" FORCE)
    set(CMAKE_XCODE_ATTRIBUTE_CODE_SIGN_IDENTITY "")
    set(CMAKE_XCODE_ATTRIBUTE_CODE_SIGNING_REQUIRED "NO")
endif()

# Find Adobe Photoshop SDK (adjust path as needed)
find_path(ADOBE_SDK_DIR
    NAMES "Photoshop"
    PATHS "/Applications/Adobe Photoshop 2023/Adobe Photoshop 2023.app/Contents"
)

# Source files
set(SOURCES
    src/plugin.cpp
    src/entry.cpp
    src/utils.cpp
)

add_library(ayon_photoshop_plugin SHARED ${SOURCES})
target_include_directories(ayon_photoshop_plugin PRIVATE
    ${ADOBE_SDK_DIR}/Headers
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_link_libraries(ayon_photoshop_plugin PRIVATE
    ${ADOBE_SDK_DIR}/Libraries/libPICA.dylib
)

# Set output name and bundle properties
set_target_properties(ayon_photoshop_plugin PROPERTIES
    BUNDLE TRUE
    BUNDLE_EXTENSION "plugin"
    MACOSX_BUNDLE_INFO_PLIST "${CMAKE_CURRENT_SOURCE_DIR}/Info.plist"
    OUTPUT_NAME "AYONPhotoshop"
)

# Install to Adobe plugins directory
install(TARGETS ayon_photoshop_plugin BUNDLE DESTINATION "~/Library/Application Support/Adobe/Plug-Ins/CC/AYON")