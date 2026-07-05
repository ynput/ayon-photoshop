#!/usr/bin/env python3
"""
AYON Photoshop Plugin - Main entry point.
Detects macOS architecture and configures the environment accordingly.
"""
import platform
import sys
import os

def get_architecture():
    """Return the architecture of the current macOS system."""
    machine = platform.machine()
    if machine in ('x86_64', 'i386'):
        return 'x86_64'
    elif machine in ('arm64', 'aarch64'):
        return 'arm64'
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")

def configure_plugin():
    """Configure plugin paths based on architecture."""
    arch = get_architecture()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    lib_dir = os.path.join(base_dir, 'lib', arch)
    if not os.path.exists(lib_dir):
        raise FileNotFoundError(f"Library directory not found: {lib_dir}")
    sys.path.insert(0, lib_dir)

def main():
    """Main entry for the AYON Photoshop plugin."""
    try:
        configure_plugin()
        # Import and run the actual plugin logic
        from ayon_photoshop import plugin
        plugin.run()
    except Exception as e:
        print(f"Error initializing AYON Photoshop plugin: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
