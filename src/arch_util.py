import platform
import sys

def get_architecture():
    """Return the architecture of the current macOS system."""
    if sys.platform != 'darwin':
        return None
    machine = platform.machine()
    if machine in ('x86_64', 'AMD64'):
        return 'x86_64'
    elif machine in ('arm64', 'aarch64'):
        return 'arm64'
    else:
        return machine

def is_apple_silicon():
    """Check if running on Apple Silicon (ARM)."""
    return get_architecture() == 'arm64'

def get_binary_path(base_name, arch=None):
    """Return the path to the appropriate binary for the current architecture."""
    if arch is None:
        arch = get_architecture()
    if arch == 'arm64':
        suffix = '_arm64'
    elif arch == 'x86_64':
        suffix = '_x86_64'
    else:
        suffix = ''
    return f"{base_name}{suffix}{'.dylib' if sys.platform == 'darwin' else '.so'}"
