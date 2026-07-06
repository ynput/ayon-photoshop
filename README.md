# AYON Photoshop Plugin for macOS

This plugin integrates AYON with Adobe Photoshop.

## Apple Silicon (ARM64) Support

The plugin now supports both Intel (x86_64) and Apple Silicon (ARM64) Macs via a universal binary.

### Building the Universal Binary

Run `./build_mac.sh` to compile the native component as a universal binary. You need Xcode command line tools installed.

### Installation

Copy the entire plugin folder to the appropriate Adobe CEP extensions directory:
- `/Library/Application Support/Adobe/CEP/extensions/` (system-wide) or
- `~/Library/Application Support/Adobe/CEP/extensions/` (user)

No additional steps are required; the universal binary works on both architectures.