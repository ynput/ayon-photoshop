# AYON Photoshop Plugin

## macOS Arm64 Support

This plugin is built to support both Intel (x86_64) and Apple Silicon (arm64) architectures on macOS.

### Requirements
- Adobe Photoshop 2020 or later
- macOS 11.0 or later (Apple Silicon or Intel)

### Installation
1. Copy the `src` folder to the Photoshop CEP extensions directory:
   - macOS: `~/Library/Application Support/Adobe/CEP/extensions/`
2. Restart Photoshop.
3. Enable the extension via Window > Extensions > AYON.

### Build
If you need to rebuild any native components, use the `build.sh` script. 
For pure JavaScript extensions, no build steps are required.

### Troubleshooting
If you encounter issues on Apple Silicon, ensure that:
- You are using the latest version of this plugin.
- Photoshop is running natively (not through Rosetta).
- No x86_64-only native dependencies are present.

### License
MIT