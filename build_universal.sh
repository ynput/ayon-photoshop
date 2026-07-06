#!/bin/bash
# Build script to create universal binary for Photoshop plugin (x86_64 and arm64)

set -e

PLUGIN_NAME="AYONPhotoshop"
SOURCE_DIR="src"
BUILD_DIR="build"
X86_64_DIR="$BUILD_DIR/x86_64"
ARM64_DIR="$BUILD_DIR/arm64"
UNIVERSAL_DIR="$BUILD_DIR/universal"

# Clean previous builds
rm -rf "$BUILD_DIR"
mkdir -p "$X86_64_DIR" "$ARM64_DIR" "$UNIVERSAL_DIR"

# Build for x86_64
echo "Building for x86_64..."
cd "$SOURCE_DIR"
# Assume use of adobe plugin SDK and cmake/make; adjust as needed
cmake -DCMAKE_OSX_ARCHITECTURES=x86_64 -B "../$X86_64_DIR" .
cmake --build "../$X86_64_DIR" --config Release
cd ..

# Build for arm64
echo "Building for arm64..."
cd "$SOURCE_DIR"
cmake -DCMAKE_OSX_ARCHITECTURES=arm64 -B "../$ARM64_DIR" .
cmake --build "../$ARM64_DIR" --config Release
cd ..

# Create universal binary
echo "Creating universal binary..."
# Assume the resulting plugin is a bundle (e.g., .plugin) with executable inside
# Adjust path based on actual output
if [ -d "$X86_64_DIR/$PLUGIN_NAME.plugin" ] && [ -d "$ARM64_DIR/$PLUGIN_NAME.plugin" ]; then
    cp -R "$X86_64_DIR/$PLUGIN_NAME.plugin" "$UNIVERSAL_DIR/"
    # Find executable inside bundle (example path)
    EXEC="$UNIVERSAL_DIR/$PLUGIN_NAME.plugin/Contents/MacOS/$PLUGIN_NAME"
    lipo -create "$X86_64_DIR/$PLUGIN_NAME.plugin/Contents/MacOS/$PLUGIN_NAME" \
                 "$ARM64_DIR/$PLUGIN_NAME.plugin/Contents/MacOS/$PLUGIN_NAME" \
                 -output "$EXEC"
    # Merge any other binaries if present
    echo "Universal plugin created at $UNIVERSAL_DIR/$PLUGIN_NAME.plugin"
else
    echo "Error: Plugin bundles not found. See build logs."
    exit 1
fi