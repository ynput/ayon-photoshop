#!/bin/bash
# Build script for macOS universal binary
set -e

# Clean previous build
rm -rf build
mkdir build && cd build

# Configure CMake for universal binary
cmake .. \
    -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64" \
    -DCMAKE_BUILD_TYPE=Release \
    -DADOBE_SDK_DIR="/Applications/Adobe Photoshop 2023/Adobe Photoshop 2023.app/Contents" \
    -GXcode

# Build the plugin
xcodebuild -configuration Release -target ALL_BUILD

# Verify architectures
lipo -info Release/ayon_photoshop_plugin.bundle/Contents/MacOS/ayon_photoshop_plugin

echo "Universal plugin built successfully."