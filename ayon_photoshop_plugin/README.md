# AYON Photoshop Plugin (macOS Universal)

This plugin integrates Adobe Photoshop with AYON pipeline.

## Requirements
- macOS 11.0+ (Big Sur or later)
- Python 3.9+
- Adobe Photoshop 2021+

## Installation
1. Copy the `ayon_photoshop_plugin` folder to your Photoshop plugin directory.
2. Ensure Python dependencies are installed (see `requirements.txt`).
3. Restart Photoshop and enable the plugin.

## Architecture Support
- The plugin supports both Intel (x86_64) and Apple Silicon (arm64) architectures.
- The `build.sh` script creates a universal binary using PyInstaller and lipo.

## Building
Run `./build.sh` to generate the universal binary.
