#!/bin/bash
# Build universal binary for Photoshop plugin (x86_64 + arm64)

set -e

BUILD_DIR="build"
PLUGIN_NAME="ayon_photoshop"
SRC_DIR="src"

# Clean
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Compile for both architectures
clang -arch x86_64 -arch arm64 -bundle -o "$BUILD_DIR/$PLUGIN_NAME.bundle" \
    "$SRC_DIR/main.c" \
    -framework CoreFoundation \
    -framework ApplicationServices \
    -isysroot $(xcrun --sdk macosx --show-sdk-path) \
    -mmacosx-version-min=10.13 \
    -Wno-deprecated-declarations

# Verify universal binary
lipo -info "$BUILD_DIR/$PLUGIN_NAME.bundle"

echo "Universal binary built successfully."