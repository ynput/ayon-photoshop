#!/bin/bash
# Build universal binary for Photoshop plugin (x86_64 + arm64)

set -e

BUILD_DIR="build"
OUTPUT_DIR="plugin"

# Clean previous builds
rm -rf "$BUILD_DIR" "$OUTPUT_DIR"
mkdir -p "$BUILD_DIR/x86_64" "$BUILD_DIR/arm64" "$OUTPUT_DIR"

# Build for x86_64
cd "$BUILD_DIR/x86_64"
cmake -DCMAKE_OSX_ARCHITECTURES=x86_64 ../..
make
cd ../..

# Build for arm64
cd "$BUILD_DIR/arm64"
cmake -DCMAKE_OSX_ARCHITECTURES=arm64 ../..
make
cd ../..

# Create universal binary using lipo
lipo -create "$BUILD_DIR/x86_64/libPluginCore.dylib" "$BUILD_DIR/arm64/libPluginCore.dylib" -output "$OUTPUT_DIR/libPluginCore.dylib"

# Verify architectures
lipo -info "$OUTPUT_DIR/libPluginCore.dylib"

echo "Universal plugin built successfully in $OUTPUT_DIR"
