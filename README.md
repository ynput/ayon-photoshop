# AYON Photoshop Plugin - macOS ARM Support

## Overview
This update adds native support for Apple Silicon (arm64) to the AYON Photoshop plugin for macOS. The plugin now ships as a universal binary that runs natively on both Intel (x86_64) and Apple Silicon (arm64) architectures.

## Changes
- Updated build system to compile for both architectures using Xcode's `-arch` flag.
- Created a shell script `build_universal.sh` to automate the process of building and combining binaries with `lipo`.
- Updated the bundle's `Info.plist` to include `LSArchitecturePriority` ensuring the system prefers native architecture when available.

## Building
1. Ensure you have Xcode command line tools installed.
2. Run `./build_universal.sh` from the project root.
3. The universal binary will be output to the `universal` directory.

## Installation
Replace the existing plugin bundle with the newly built universal bundle.

## Notes
- The plugin must be compiled with a minimum macOS deployment target of 10.15 or later to support both architectures.
- Ensure all third-party libraries are also universal binaries.
