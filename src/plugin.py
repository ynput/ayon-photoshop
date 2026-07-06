import sys
import os
from .arch_util import get_architecture, get_binary_path

def load_plugin():
    arch = get_architecture()
    if arch is None:
        raise RuntimeError("This plugin is only supported on macOS.")
    
    # Assume we have binaries in the 'bin' directory relative to this file
    bin_dir = os.path.join(os.path.dirname(__file__), '..', 'bin')
    binary_name = 'ps_plugin'
    binary_path = get_binary_path(binary_name)
    full_path = os.path.join(bin_dir, binary_path)
    
    if not os.path.exists(full_path):
        # Fallback to single binary
        fallback = os.path.join(bin_dir, f"{binary_name}.dylib")
        if os.path.exists(fallback):
            full_path = fallback
        else:
            raise FileNotFoundError(f"No suitable binary found for architecture {arch}")
    
    # Load the binary (example using ctypes)
    import ctypes
    try:
        lib = ctypes.cdll.LoadLibrary(full_path)
        return lib
    except Exception as e:
        raise RuntimeError(f"Failed to load plugin binary: {e}")

def main():
    print(f"Running on architecture: {get_architecture()}")
    lib = load_plugin()
    # Example call
    # lib.some_function()
    print("Plugin loaded successfully.")

if __name__ == "__main__":
    main()
