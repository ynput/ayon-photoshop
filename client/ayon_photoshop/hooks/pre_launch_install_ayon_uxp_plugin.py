from pathlib import Path

from ayon_applications import PreLaunchHook, LaunchTypes

from ayon_photoshop import PHOTOSHOP_ADDON_ROOT
from ayon_photoshop.plugin_type import (
    PLUGIN_UXP, 
    get_plugin_type, 
    AYON_UXP_PLUGIN_NAME,
)
from ayon_photoshop.uxp_installer import (
    Upia,
    find_upia,
    read_package,
)
from subprocess import TimeoutExpired

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
                    "UnifiedPluginInstallerAgent was not found; AYON UXP plugin "
                    f"can be installed manually from {self.CCX_PATH}"
                )
            return

        upia = Upia(executable)

        try:
            if not want_uxp:
                removed = upia.ensure_plugin_removed(AYON_UXP_PLUGIN_NAME)
                if removed:
                    self.log.info(
                        f"Removed UXP plugin {AYON_UXP_PLUGIN_NAME}: "
                        f"({', '.join(removed)})."
                    )
                return

            package = read_package(self.CCX_PATH)
            if upia.ensure_plugin_installed(package):
                self.log.info(
                    f"UXP plugin {package.name} {package.version} is installed"
                    " & up to date."
                )
            else:
                self.log.warning(
                    f"UXP plugin {package.name} {package.version} failed to install."
                )

        except TimeoutExpired:
            self.log.warning(
                "Adobe's plugin installer timed out; continuing Photoshop launch."
            )
        except Exception:
            self.log.warning(
                "Could not update AYON's UXP plugin; continuing Photoshop launch.",
                exc_info=True,
            )