# AYON Photoshop Plugin

This plugin integrates Adobe Photoshop with AYON.

## Changes for ARM Architecture Support

- Updated build process to produce universal binaries for macOS (x86_64 and arm64).
- Added architecture detection in the Python module to load the correct native library.
- CI updated to build both architectures and merge them using `lipo`.

## Building

Run `./build.sh` to build the universal binary. Requires Xcode command line tools.
