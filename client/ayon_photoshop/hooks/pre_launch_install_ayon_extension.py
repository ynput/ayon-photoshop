from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from shutil import rmtree

import platformdirs

from ayon_photoshop import PHOTOSHOP_ADDON_ROOT
from ayon_applications import PreLaunchHook, LaunchTypes


class InstallAyonExtensionToPhotoshop(PreLaunchHook):
    """
    Automatically 'installs' the AYON Photoshop extension.

    Checks if Photoshop already has the extension in the relevant folder,
    will try to create that folder and unzip the extension if not.
    """

    app_groups = {"photoshop"}

    order = 1
    launch_types = {LaunchTypes.local}

    def execute(self):
        try:
            settings = self.data["project_settings"]["photoshop"]
            if not settings["auto_install_extension"]:
                return
            self.inner_execute()

        except Exception:
            self.log.warning(
                "Processing of {} crashed.".format(self.__class__.__name__),
                exc_info=True,
            )

    def inner_execute(self):
        self.log.info("Installing AYON Photoshop extension.")

        target_path = Path(
            platformdirs.user_data_dir("Adobe", roaming=True),  # roaming is useful for windows
            "CEP/extensions/io.ynput.PS.panel"
        )

        extension_path = Path(
            PHOTOSHOP_ADDON_ROOT,
            "api",
            "extension.zxp",
        )

        # Extension already installed, compare the versions
        if target_path.is_dir():
            self.log.info(
                f"The extension already exists at: {target_path}. "
                f"Comparing versions.."
            )
            if not self._compare_extension_versions(
                target_path, extension_path
            ):
                return

        try:
            self.log.debug(f"Creating directory: {target_path}")
            target_path.mkdir(parents=True, exist_ok=True)

            with ZipFile(extension_path, "r") as archive:
                archive.extractall(path=target_path)
            self.log.info("Successfully installed AYON extension")

        except OSError as error:
            self.log.warning(f"OS error has occured: {error}")

        except PermissionError as error:
            self.log.warning(f"Permissions error has occured: {error}")

        except Exception as error:
            self.log.warning(f"An unexpected error occured: {error}")

    def _compare_extension_versions(
        self, target_path: Path, extension_path: Path
    ) -> bool:
        try:
            # opens the existing extension manifest to get the Version attr
            with target_path.joinpath("CSXS", "manifest.xml").open("rb") as xml_file:
                installed_version = (
                    ET.parse(xml_file)
                    .getroot()
                    .attrib.get("ExtensionBundleVersion")
                )
            self.log.debug(
                f"Current extension version found: {installed_version}"
            )

            if not installed_version:
                self.log.warning(
                    "Unable to resolve the currently installed extension "
                    "version. Cancelling.."
                )
                return False

            # opens the .zxp manifest to get the Version attribute.
            with ZipFile(extension_path, "r") as archive:
                xml_file = archive.open("CSXS/manifest.xml")
                new_version = (
                    ET.parse(xml_file)
                    .getroot()
                    .attrib.get("ExtensionBundleVersion")
                )
                if not new_version:
                    self.log.warning(
                        "Unable to resolve the new extension version. "
                        "Cancelling.."
                    )
                self.log.debug(f"New extension version found: {new_version}")

                # compare the two versions, a simple == is enough since
                # we don't care if the version increments or decrements
                # if they match nothing happens.
                if installed_version == new_version:
                    self.log.info("Versions matched. Cancelling..")
                    return False

                # remove the existing addon
                self.log.info(
                    "Version mismatch found. Removing old extensions.."
                )
                rmtree(target_path)
                return True

        except PermissionError as error:
            self.log.warning(
                "Permissions error has occurred while comparing "
                f"versions: {error}"
            )
            return False

        except OSError as error:
            self.log.warning(
                f"OS error has occured while comparing versions: {error}"
            )
            return False

        except Exception as error:
            self.log.warning(
                f"An unexpected error occured when comparing version: {error}"
            )
            return False