#!/bin/bash
# Script to build universal binary for Photoshop macOS plugin
# Assumes source code is in src/ and builds for both architectures

set -e

PROJECT_NAME="PhotoshopPlugin"
BUILD_DIR="build"
UNIVERSAL_DIR="universal"

# Build for x86_64
echo "Building for x86_64..."
mkdir -p "${BUILD_DIR}/x86_64"
cd src
xcodebuild -project "${PROJECT_NAME}.xcodeproj" -scheme "${PROJECT_NAME}" -configuration Release -arch x86_64 SYMROOT="${PWD}/${BUILD_DIR}/x86_64"
cd ..

# Build for arm64
echo "Building for arm64..."
mkdir -p "${BUILD_DIR}/arm64"
cd src
xcodebuild -project "${PROJECT_NAME}.xcodeproj" -scheme "${PROJECT_NAME}" -configuration Release -arch arm64 SYMROOT="${PWD}/${BUILD_DIR}/arm64"
cd ..

# Create universal binary
echo "Creating universal binary..."
mkdir -p "${UNIVERSAL_DIR}"
lipo -create "${BUILD_DIR}/x86_64/Release/${PROJECT_NAME}.bundle" \
             "${BUILD_DIR}/arm64/Release/${PROJECT_NAME}.bundle" \
     -output "${UNIVERSAL_DIR}/${PROJECT_NAME}.bundle"

echo "Universal binary created at ${UNIVERSAL_DIR}/${PROJECT_NAME}.bundle"
