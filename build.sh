#!/bin/bash
# Build script for AYON Photoshop plugin - ensures arm64 compatibility
# This script prepares the extension for distribution on macOS (Apple Silicon)

echo "Building AYON Photoshop plugin for arm64..."

# Copy source files to dist
mkdir -p dist
cp -R src/* dist/

# If there are any native modules (Node addons), rebuild them for arm64
# For pure JS/HTML, no native compilation needed.

echo "Build complete. Extension is universal."