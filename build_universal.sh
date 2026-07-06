#!/bin/bash
# Script to build a universal macOS binary for the AYON Photoshop plugin native component
# Assumes source files are in src/ and produces a universal binary in dist/

set -e

ARCHS=("x86_64" "arm64")
OUTPUT_DIR="dist"
SOURCE_DIR="src"
PLUGIN_NAME="ayon_photoshop_plugin"

mkdir -p "$OUTPUT_DIR"

for arch in "${ARCHS[@]}"; do
    # Compile for specific architecture (example using gcc, adjust for your language)
    gcc -arch "$arch" -o "${OUTPUT_DIR}/${PLUGIN_NAME}_${arch}" "${SOURCE_DIR}/main.c"
done

# Create universal binary using lipo
lipo -create -output "${OUTPUT_DIR}/${PLUGIN_NAME}" \
    "${OUTPUT_DIR}/${PLUGIN_NAME}_x86_64" \
    "${OUTPUT_DIR}/${PLUGIN_NAME}_arm64"

# Clean up intermediate files
rm "${OUTPUT_DIR}/${PLUGIN_NAME}_x86_64" "${OUTPUT_DIR}/${PLUGIN_NAME}_arm64"

echo "Universal binary created at ${OUTPUT_DIR}/${PLUGIN_NAME}"
