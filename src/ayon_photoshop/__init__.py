"""AYON Photoshop plugin entry point."""

import platform
import os
import ctypes

# Determine architecture
def get_arch():
    machine = platform.machine()
    if machine in ('x86_64', 'AMD64'):
        return 'x86_64'
    elif machine in ('arm64', 'aarch64'):
        return 'arm64'
    else:
        return machine

# Load appropriate library
def load_native_lib():
    arch = get_arch()
    lib_dir = os.path.join(os.path.dirname(__file__), 'native', arch)
    if not os.path.exists(lib_dir):
        raise ImportError(f"No native library for architecture {arch} at {lib_dir}")
    lib_path = os.path.join(lib_dir, 'ayon_photoshop.dylib')
    try:
        lib = ctypes.CDLL(lib_path)
    except OSError as e:
        raise ImportError(f"Failed to load native library {lib_path}: {e}")
    return lib

# Initialize native library on import
native_lib = load_native_lib()
