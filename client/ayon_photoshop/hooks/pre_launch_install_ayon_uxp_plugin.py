from pathlib import Path

from ayon_applications import PreLaunchHook, LaunchTypes

from ayon_photoshop import PHOTOSHOP_ADDON_ROOT
from ayon_photoshop.uxp_installer import (
    Upia,
    ensure_plugin_installed,
    find_upia,
    read_package,
)


class InstallAyonUxpPluginToPhotoshop(PreLaunchHook):
    """Install the AYON UXP plugin into Photoshop before it starts.

    Runs only when the 'install_uxp_plugin' setting is enabled.

    The plugin is installed with Adobe's own command line installer from the
    packaged .ccx. A missing installer or a failed install never blocks the
    launch of Photoshop, it only logs a warning.
    """

    app_groups = {"photoshop"}

    # Same slot as the CEP extension hook, no dependency between the two.
    order = 1
    launch_types = {LaunchTypes.local}

    CCX_PATH = Path(PHOTOSHOP_ADDON_ROOT, "api", "com.ayon.photoshop_PS.ccx")

    def execute(self):
        settings = self.data["project_settings"]["photoshop"]
        if not settings.get("install_uxp_plugin", False):
            return

        executable = find_upia()
        if executable is None:
            self.log.warning(
                "Adobe's plugin installer (UnifiedPluginInstallerAgent) was "
                "not found, is Creative Cloud installed? The AYON UXP plugin "
                f"can be installed by hand from {self.CCX_PATH}"
            )
            return

        package = read_package(self.CCX_PATH)
        if ensure_plugin_installed(
            Upia(executable), package
        ):
            self.log.info(f"UXP plugin {package.name} {package.version} is up to date.")
        else:
            self.log.warning(f"UXP plugin {package.name} {package.version} failed to install.")
