from pathlib import Path

from ayon_applications import PreLaunchHook, LaunchTypes

from ayon_photoshop import PHOTOSHOP_ADDON_ROOT
from ayon_photoshop.plugin_type import PLUGIN_UXP, get_plugin_type
from ayon_photoshop.uxp_installer import (
    Upia,
    find_upia,
    read_package,
)


class InstallAyonUxpPluginToPhotoshop(PreLaunchHook):
    """Install the AYON UXP plugin into Photoshop before it starts.

    Runs only when 'auto_install_extension' is enabled. The plugin is
    installed when the project's 'plugin_type' is 'uxp'. For 'cep' it is
    removed instead, so that the CEP extension is the only panel.

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
        if not settings.get("auto_install_extension", False):
            return
        
        want_uxp = get_plugin_type(settings) == PLUGIN_UXP
        executable = find_upia()
        if executable is None:
            if want_uxp:
                self.log.warning(
                    "Adobe's plugin installer (UnifiedPluginInstallerAgent) "
                    "was not found, is Creative Cloud installed? The AYON "
                    f"UXP plugin can be installed by hand from {self.CCX_PATH}"
                )
            return

        try:
            package = read_package(self.CCX_PATH)
        except BaseException as err:
            self.log.warning(
                "Error encountered during attempt at reading .ccx file: "
                f"{err}"
            )

        upia = Upia(executable)

        if not want_uxp:
            try:
                removed = upia.ensure_plugin_removed(package.name)
            
                if removed:
                    removed_list = f"({', '.join(removed)})."
                    self.log.info(f"Removed UXP plugin {package.name}: {removed_list}")
                return
            except RuntimeError as err:
                self.log.warning(
                    "Error encountered removing UXP plugin: "
                    f"{err}"
                )
                return


        if upia.ensure_plugin_installed(package):
            self.log.info(
                f"UXP plugin {package.name} {package.version} is up to date."
            )
        else:
            self.log.warning(
                f"UXP plugin {package.name} {package.version} failed to "
                "install."
            )