import os
import platform
import subprocess

from ayon_core.lib import (
    get_ayon_launcher_args,
    is_using_ayon_console,
)
from ayon_applications import PreLaunchHook, LaunchTypes
from ayon_photoshop import get_launch_script_path


def get_launch_kwargs(kwargs):
    """Explicit setting of kwargs for Popen for Photoshop.

    Expected behavior
    - ayon_console opens window with logs
    - ayon has stdout/stderr available for capturing

    Args:
        kwargs (Union[dict, None]): Current kwargs or None.

    """
    if kwargs is None:
        kwargs = {}

    if platform.system().lower() != "windows":
        return kwargs

    if is_using_ayon_console():
        kwargs.update({
            "creationflags": subprocess.CREATE_NEW_CONSOLE
        })
    else:
        kwargs.update({
            "creationflags": subprocess.CREATE_NO_WINDOW,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL
        })
    return kwargs


class PhotoshopPrelaunchHook(PreLaunchHook):
    """Launch arguments preparation.

    Hook add python executable and script path to Photoshop implementation
    before Photoshop executable and add last workfile path to launch arguments.

    Last workfile path would be added to self.launch_context.launch_args by
    global `pre_add_last_workfile_arg`.
    """
    app_groups = {"photoshop"}

    order = 20
    launch_types = {LaunchTypes.local}

    def execute(self):
        # Pop executable
        executable_path = self.launch_context.launch_args.pop(0)

        args = []
        while self.launch_context.launch_args:
            args.append(self.launch_context.launch_args.pop(0))

        script_path = get_launch_script_path()

        new_launch_args = get_ayon_launcher_args(
            "run", script_path, executable_path
        )

        workfile_startup = self.data.get("workfile_startup", False)
        self.launch_context.env["AYON_PHOTOSHOP_WORKFILES_ON_LAUNCH"] = (
            str(workfile_startup).lower()
        )
        # Append as whole list as these arguments should not be separated
        self.launch_context.launch_args.append(new_launch_args)

        for arg in args:
            if os.path.isfile(arg):
                arg = os.path.realpath(arg)
            self.launch_context.launch_args.append(arg)

        self.launch_context.kwargs = get_launch_kwargs(
            self.launch_context.kwargs
        )
