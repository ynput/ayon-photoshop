from typing import Optional


def get_macos_launch_args(
    subprocess_args: list[str],
    executable_arches: list[str],
    process_arches: set[str],
) -> tuple[list[str], Optional[str]]:
    """Prepare launch arguments for a macOS executable."""
    args = list(subprocess_args)
    if (
        executable_arches
        and process_arches
        and not process_arches.intersection(executable_arches)
    ):
        arch = executable_arches[0]
        args[:0] = ["arch", f"-{arch}"]
        return args, arch
    return args, None
