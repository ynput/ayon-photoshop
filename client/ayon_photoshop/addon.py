import os
from ayon_core.addon import AYONAddon, IHostAddon

from .version import __version__

PHOTOSHOP_ADDON_ROOT = os.path.dirname(os.path.abspath(__file__))


class PhotoshopAddon(AYONAddon, IHostAddon):
    name = "photoshop"
    version = __version__
    host_name = "photoshop"

    def add_implementation_envs(self, env, _app):
        """Modify environments to contain all required for implementation."""
        defaults = {
            "AYON_LOG_NO_COLORS": "1",
            "WEBSOCKET_URL": "ws://localhost:8099/ws/"
        }
        for key, value in defaults.items():
            if not env.get(key):
                env[key] = value

    def get_workfile_extensions(self):
        return [".psd", ".psb"]

    def get_launch_hook_paths(self, app):
        if app.host_name != self.host_name:
            return []
        return [
            os.path.join(PHOTOSHOP_ADDON_ROOT, "hooks")
        ]

    def publish_in_test(self, log, close_plugin_name=None):
        """Runs publish in an opened host with a context.
        Close Python process at the end.
        """

        from ayon_photoshop.api.lib import publish_in_test

        publish_in_test(log, close_plugin_name)


def get_launch_script_path():
    return os.path.join(
        PHOTOSHOP_ADDON_ROOT, "api", "launch_script.py"
    )
