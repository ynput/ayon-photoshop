#!/bin/bash
# Build universal binary for ayon-photoshop native component
# This script compiles for both x86_64 and arm64 and merges them

set -e

BUILD_DIR="build"
X86_BUILD="${BUILD_DIR}/x86_64"
ARM_BUILD="${BUILD_DIR}/arm64"
UNIVERSAL_BUILD="${BUILD_DIR}/universal"

# Clean previous builds
rm -rf ${BUILD_DIR}

# Build for x86_64
echo "Building for x86_64..."
cmake -B ${X86_BUILD} -DCMAKE_OSX_ARCHITECTURES="x86_64" .
cmake --build ${X86_BUILD} --config Release

# Build for arm64
echo "Building for arm64..."
cmake -B ${ARM_BUILD} -DCMAKE_OSX_ARCHITECTURES="arm64" .
cmake --build ${ARM_BUILD} --config Release

# Create universal binary
echo "Creating universal binary..."
mkdir -p ${UNIVERSAL_BUILD}
lipo -create \
    ${X86_BUILD}/libayon-photoshop-native.dylib \
    ${ARM_BUILD}/libayon-photoshop-native.dylib \
    -output ${UNIVERSAL_BUILD}/libayon-photoshop-native.dylib

echo "Universal binary created at ${UNIVERSAL_BUILD}/libayon-photoshop-native.dylib"

# Optionally copy to plugin directory
# cp ${UNIVERSAL_BUILD}/libayon-photoshop-native.dylib ../CEP/extensions/
