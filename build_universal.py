#!/usr/bin/env python3
"""
Build script to create a universal binary for the AYON Photoshop plugin.
Assumes two separate builds for x86_64 and arm64 exist in build/x86_64 and build/arm64.
"""
import subprocess
import os
import shutil

def main():
    plugin_name = "AYONPhotoshop.plugin"
    build_dir = "build"
    universal_dir = os.path.join(build_dir, "universal")
    os.makedirs(universal_dir, exist_ok=True)

    # Paths to the two architecture builds
    x86_path = os.path.join(build_dir, "x86_64", plugin_name)
    arm_path = os.path.join(build_dir, "arm64", plugin_name)

    if not os.path.exists(x86_path) or not os.path.exists(arm_path):
        print("Error: Both architecture builds must exist.")
        print(f"Expected: {x86_path} and {arm_path}")
        exit(1)

    # Copy the x86_64 plugin as base, then lipo to add arm64
    universal_plugin = os.path.join(universal_dir, plugin_name)
    if os.path.exists(universal_plugin):
        shutil.rmtree(universal_plugin)
    shutil.copytree(x86_path, universal_plugin)

    # Locate the binary inside the plugin bundle
    binary_rel_path = "Contents/MacOS/AYONPhotoshop"
    binary_path = os.path.join(universal_plugin, binary_rel_path)
    if not os.path.exists(binary_path):
        print("Error: Binary not found inside plugin bundle.")
        exit(1)

    # Use lipo to create universal binary
    arm_binary = os.path.join(arm_path, binary_rel_path)
    subprocess.run(["lipo", "-create", "-output", binary_path, binary_path, arm_binary], check=True)
    print(f"Universal binary created at {binary_path}")

if __name__ == "__main__":
    main()
