#!/bin/bash
# Build script for Photoshop macOS plugin with universal binary (x86_64 + arm64)

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$PROJECT_DIR/build"
UNIVERSAL_DIR="$BUILD_DIR/universal"

# Clean previous builds
rm -rf "$BUILD_DIR"
mkdir -p "$UNIVERSAL_DIR"

# Build for x86_64
echo "Building for x86_64..."
xcodebuild -project "$PROJECT_DIR/AyonPhotoshop.xcodeproj" \
    -scheme "AyonPhotoshop" \
    -configuration Release \
    -arch x86_64 \
    -derivedDataPath "$BUILD_DIR/x86_64" \
    CONFIGURATION_BUILD_DIR="$BUILD_DIR/x86_64" \
    clean build

# Build for arm64
echo "Building for arm64..."
xcodebuild -project "$PROJECT_DIR/AyonPhotoshop.xcodeproj" \
    -scheme "AyonPhotoshop" \
    -configuration Release \
    -arch arm64 \
    -derivedDataPath "$BUILD_DIR/arm64" \
    CONFIGURATION_BUILD_DIR="$BUILD_DIR/arm64" \
    clean build

# Create universal binary
echo "Creating universal binary..."
# Locate the plugin bundle
PLUGIN_NAME="AyonPhotoshop.plugin"
X86_BUNDLE="$BUILD_DIR/x86_64/Release/$PLUGIN_NAME"
ARM_BUNDLE="$BUILD_DIR/arm64/Release/$PLUGIN_NAME"

if [ ! -d "$X86_BUNDLE" ] || [ ! -d "$ARM_BUNDLE" ]; then
    echo "Error: One of the builds is missing."
    exit 1
fi

# Copy arm64 bundle as base (both are identical except executable)
cp -R "$ARM_BUNDLE" "$UNIVERSAL_DIR/$PLUGIN_NAME"

# Use lipo to merge the executable
lipo -create \
    "$X86_BUNDLE/Contents/MacOS/AyonPhotoshop" \
    "$ARM_BUNDLE/Contents/MacOS/AyonPhotoshop" \
    -output "$UNIVERSAL_DIR/$PLUGIN_NAME/Contents/MacOS/AyonPhotoshop"

# Sign the universal binary (if required)
codesign --force --sign - --deep "$UNIVERSAL_DIR/$PLUGIN_NAME"

echo "Universal plugin created at: $UNIVERSAL_DIR/$PLUGIN_NAME"
