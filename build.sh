#!/bin/bash
set -e

BUILD_DIR=build
UNIVERSAL_OUTPUT=ayon_photoshop_plugin.universal.dylib

# Build for x86_64
echo "Building for x86_64..."
xcodebuild -project AyonPhotoshop.xcodeproj -scheme AyonPhotoshop -configuration Release -arch x86_64 -derivedDataPath $BUILD_DIR/x86_64

# Build for arm64
echo "Building for arm64..."
xcodebuild -project AyonPhotoshop.xcodeproj -scheme AyonPhotoshop -configuration Release -arch arm64 -derivedDataPath $BUILD_DIR/arm64

# Create universal binary
echo "Creating universal binary..."
lipo -create \
  $BUILD_DIR/x86_64/Build/Products/Release/AyonPhotoshop.framework/Versions/A/AyonPhotoshop \
  $BUILD_DIR/arm64/Build/Products/Release/AyonPhotoshop.framework/Versions/A/AyonPhotoshop \
  -output $UNIVERSAL_OUTPUT

echo "Done: $UNIVERSAL_OUTPUT"
