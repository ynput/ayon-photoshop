# AYON Photoshop Plugin - macOS Universal Binary

This plugin has been updated to support both Intel (x86_64) and Apple Silicon (arm64) architectures.

## Build Instructions

1. Ensure you have Xcode command line tools installed.
2. Build the plugin for each architecture separately:
   - For x86_64: `xcodebuild -arch x86_64`
   - For arm64: `xcodebuild -arch arm64`
3. Run `python3 build_universal.py` to combine them into a universal binary.

## Changes Made

- Added build script `build_universal.py` to create a universal binary using `lipo`.
- Updated CI configuration to build for both architectures.
- Verified compatibility with macOS 10.15+.

## Support

For issues, please refer to the AYON support channels. See [discord link].
