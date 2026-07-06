# AYON Photoshop Plugin - macOS Universal Binary Support

## Changes Made

- Updated `native/CMakeLists.txt` to build both x86_64 and arm64 architectures when targeting macOS.
- Added `native/build_universal.sh` script to compile for each architecture separately and merge them into a single universal dynamic library using `lipo`.

## Build Instructions

1. Navigate to the `native` directory.
2. Run `./build_universal.sh`.
3. The universal binary will be placed in `build/universal/libayon-photoshop-native.dylib`.
4. Copy the resulting `.dylib` to the appropriate extension location (e.g., `CEP/extensions/`).

## Compatibility

- The native library now supports both Intel (x86_64) and Apple Silicon (arm64) Macs.
- No changes to the JavaScript/CEP code were necessary.
- The implementation uses CMake which is already present in the repository.

## Notes

- Ensure you have CMake (>=3.10) and Xcode Command Line Tools installed.
- For Adobe Photoshop CEP extensions, the native binary must be placed in the correct subfolder (e.g., `host` or `lib`). Adjust the copy path in the script accordingly.
