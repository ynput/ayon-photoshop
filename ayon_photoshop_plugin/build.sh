#!/bin/bash
# Build script to create universal binary (x86_64 + arm64) for macOS
# Assumes Python 3 and pyinstaller are installed.

set -e

ARCHS=("x86_64" "arm64")
APP_NAME="AYON Photoshop Plugin"

echo "Building universal plugin..."

for ARCH in "${ARCHS[@]}"; do
    echo "  Building for $ARCH..."
    # Create a temporary directory for the build
    BUILD_DIR="./build_$ARCH"
    DIST_DIR="./dist_$ARCH"
    
    # PyInstaller command for each architecture
    pyinstaller \
        --onefile \
        --name "$APP_NAME" \
        --distpath "$DIST_DIR" \
        --workpath "$BUILD_DIR" \
        --specpath "$BUILD_DIR" \
        --target-architecture "$ARCH" \
        main.py
    
    echo "  $ARCH build complete."
done

echo "Combining binaries with lipo..."
# Create output directory
mkdir -p ./dist
# Use lipo to create universal binary
lipo -create \
    "./dist_x86_64/$APP_NAME" \
    "./dist_arm64/$APP_NAME" \
    -output "./dist/$APP_NAME"

echo "Removing temporary builds..."
rm -rf ./build_x86_64 ./dist_x86_64 ./build_arm64 ./dist_arm64

echo "Universal plugin created at ./dist/$APP_NAME"
