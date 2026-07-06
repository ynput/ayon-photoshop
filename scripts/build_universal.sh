#!/bin/bash
# Build universal binary for ayon-photoshop plugin (macOS)
# Supports both x86_64 and arm64 architectures

set -e

PLUGIN_NAME="ayon-photoshop"
BUILD_DIR="build"
DIST_DIR="dist"

# Clean previous builds
rm -rf "$BUILD_DIR" "$DIST_DIR"

# Build for x86_64
python3 -m venv "${BUILD_DIR}/venv_x86"
source "${BUILD_DIR}/venv_x86/bin/activate"
pip install --upgrade pip
pip install .
# Assuming plugin is packaged with py2app or similar
python setup.py py2app --arch x86_64 --dist-dir "${DIST_DIR}/x86_64"
deactivate

# Build for arm64
python3 -m venv "${BUILD_DIR}/venv_arm"
source "${BUILD_DIR}/venv_arm/bin/activate"
pip install --upgrade pip
pip install .
python setup.py py2app --arch arm64 --dist-dir "${DIST_DIR}/arm64"
deactivate

# Create universal binary using lipo
UNIVERSAL_DIR="${DIST_DIR}/universal"
mkdir -p "$UNIVERSAL_DIR"

# Assume the plugin bundle is at <plugin_name>.app
# We need to lipo the executable inside the bundle
X86_APP="${DIST_DIR}/x86_64/${PLUGIN_NAME}.app"
ARM_APP="${DIST_DIR}/arm64/${PLUGIN_NAME}.app"
UNIVERSAL_APP="${UNIVERSAL_DIR}/${PLUGIN_NAME}.app"

cp -R "$X86_APP" "$UNIVERSAL_APP"

# Find all binaries in the bundle and create universal versions
find "$UNIVERSAL_APP" -type f -perm +111 | while read -r file; do
    relpath="${file#$UNIVERSAL_APP/}"
    x86_file="${X86_APP}/${relpath}"
    arm_file="${ARM_APP}/${relpath}"
    if [ -f "$x86_file" ] && [ -f "$arm_file" ]; then
        lipo -create -output "$file" "$x86_file" "$arm_file"
        echo "Created universal binary: $relpath"
    fi
done

echo "Universal build complete: $UNIVERSAL_APP"
