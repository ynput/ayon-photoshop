# AYON Photoshop Plugin for macOS

This plugin integrates Adobe Photoshop with AYON pipeline.

## Building for macOS (Universal Binary)

The plugin now supports both Intel (x86_64) and Apple Silicon (arm64) architectures.
To build a universal binary that works on both:

```bash
bash scripts/build_universal.sh
```

Output will be in `dist/universal/`.

## Requirements
- Python 3.11+
- py2app
- macOS SDK (Xcode)

## Troubleshooting
If you encounter issues with architecture mismatch, ensure you are using the universal build or the correct architecture-specific build.
