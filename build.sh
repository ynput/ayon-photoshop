#!/bin/bash
# Build script for cross-compiling Photoshop plugin for both x86_64 and arm64
set -e

cd "$(dirname "$0")"

# Build for arm64
export CFLAGS="-arch arm64"
export CXXFLAGS="-arch arm64"
export LDFLAGS="-arch arm64"
npm rebuild --arch=arm64 --target_arch=arm64

# Build for x86_64
export CFLAGS="-arch x86_64"
export CXXFLAGS="-arch x86_64"
export LDFLAGS="-arch x86_64"
npm rebuild --arch=x64 --target_arch=x64

# Combine into universal binary using lipo
lipo -create -output native/plugin.node native/plugin.arm64.node native/plugin.x86_64.node

echo "Universal plugin built successfully."