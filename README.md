# Ayon Photoshop Plugin - Universal macOS Build

This plugin has been updated to support both Intel (x86_64) and Apple Silicon (arm64) architectures.

## Building

Run `./build_universal.sh` to create a universal binary. The output will be in `build/universal/`.

## Installation

Copy the `.plugin` bundle from `build/universal/` to the Adobe Photoshop plugins directory:
- `/Applications/Adobe Photoshop [version]/Plug-ins/`

## Notes

- Requires macOS 11.0 or later.
- Ensure Adobe Photoshop is closed during installation.