"""Install the AYON UXP plugin (.ccx) into Photoshop.

Uses Adobe's Unified Plugin Installer Agent (UPIA), which ships with the
Creative Cloud desktop app. Standard library only, so it can be used and
tested without any AYON module.

Behaviour of the tool that this module is built around:

- The exit code is 0 even when an operation fails. A failure is only visible
  in the output as "Failed to install, status = -204!".
- Installing a newer version over an older one replaces it cleanly.
- Installing an OLDER version over a newer one registers both, and both show
  up as enabled.
- "--remove" takes the plugin display name and removes only some of the
  registered versions per call, so it has to be repeated until none is left.
- Installing the version that is already installed is harmless.
"""
from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

# Environment variable that points to a UPIA executable, for installs of
#   Creative Cloud in a non-standard location.
UPIA_ENV = "AYON_PHOTOSHOP_UPIA_PATH"

# Seconds to wait for a single UPIA call before giving up.
UPIA_TIMEOUT = 120

# UPIA reports failures like "Failed to install, status = -204!".
_FAILURE_RE = re.compile(r"Failed to (?P<action>\w+)[^\n]*?status = (?P<status>-?\d+)")
# "1 extension installed for Photoshop 2024 (ver 25.12.1)"
_SECTION_RE = re.compile(
    r"^\d+ extensions? installed for (?P<product>.+?)"
    r"(?: \(ver (?P<host_version>[^)]+)\))?\s*$"
)
# " Enabled    AYON      1.1.11" - columns are separated by two or more spaces.
_ROW_RE = re.compile(
    r"^\s*(?P<status>[A-Za-z]+)\s{2,}(?P<name>.+?)\s{2,}(?P<version>\S+)\s*$"
)

# UPIA Path
_MAC_UPIA = Path(
    "/Library/Application Support/Adobe/Adobe Desktop Common/RemoteComponents"
    "/UPI/UnifiedPluginInstallerAgent/UnifiedPluginInstallerAgent.app"
    "/Contents/MacOS/UnifiedPluginInstallerAgent"
)
_WINDOWS_UPIA_RELATIVE = Path(
    "Adobe/Adobe Desktop Common/RemoteComponents/UPI"
    "/UnifiedPluginInstallerAgent/UnifiedPluginInstallerAgent.exe"
)

Logger = Callable[[str], None]


@dataclass(frozen=True)
class PluginPackage:
    """Identity of a .ccx file, read from the manifest inside it."""

    path: Path
    plugin_id: str
    name: str
    version: str


@dataclass(frozen=True)
class InstalledPlugin:
    """One row of "UnifiedPluginInstallerAgent --list"."""

    product: str
    status: str
    name: str
    version: str


def read_package(ccx_path: str) -> PluginPackage:
    """Read name and version of a plugin from the manifest inside a .ccx.

    Args:
        ccx_path (Union[str, Path]): Path to the .ccx file.

    Returns:
        PluginPackage: Identity of the package.
    """
    # UPIA fails with "status = -160" (file not found) on a relative path,
    #   so the package always carries an absolute one.
    path = Path(ccx_path).resolve()

    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    return PluginPackage(
        path=path,
        plugin_id=manifest["id"],
        name=manifest["name"],
        version=str(manifest["version"]),
    )


def find_upia(env: Optional[Dict[str, str]] = None) -> Optional[Path]:
    """Find the Unified Plugin Installer Agent executable.

    Args:
        env (Optional[dict[str, str]]): Environment to read, defaults to
            os.environ.

    Returns:
        Optional[Path]: Executable, None if it is not installed. When the
            override variable is set but wrong, None is returned too, instead
            of silently using another installation.
    """
    env = os.environ if env is None else env
    override = env.get(UPIA_ENV)
    if override:
        path = Path(override)
        return path if path.is_file() else None

    system = platform.system().lower()
    candidates: List[Path] = []
    if system == "darwin":
        candidates.append(_MAC_UPIA)
    elif system == "windows":
        for variable in ("CommonProgramFiles", "CommonProgramFiles(x86)"):
            root = env.get(variable)
            if root:
                candidates.append(Path(root) / _WINDOWS_UPIA_RELATIVE)

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def parse_list_output(output: str) -> List[InstalledPlugin]:
    """Parse the text printed by "UnifiedPluginInstallerAgent --list all".

    Args:
        output (str): Text printed by the tool.

    Returns:
        list[InstalledPlugin]: One item per listed plugin, for every product.
    """
    plugins: List[InstalledPlugin] = []
    product = None
    for line in output.splitlines():
        section = _SECTION_RE.match(line.strip())
        if section:
            product = section.group("product")
            continue
        if product is None or line.lstrip().startswith("="):
            continue
        row = _ROW_RE.match(line)
        if not row or row.group("status") == "Status":
            continue  # blank line or the column titles
        plugins.append(InstalledPlugin(
            product=product,
            status=row.group("status"),
            name=row.group("name"),
            version=row.group("version"),
        ))
    return plugins


class Upia:
    """Thin wrapper around the Unified Plugin Installer Agent."""

    def __init__(self, executable, timeout: float = UPIA_TIMEOUT):
        self.executable = Path(executable)
        self.timeout = timeout

    def _run(self, *args: str) -> str:
        """Run the tool and return its output."""
        completed = subprocess.run(
            [str(self.executable), *args],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=self.timeout,
        )

        return completed.stdout.decode("utf-8", errors="replace")

    def list_plugins(self) -> List[InstalledPlugin]:
        """Return the plugins installed for every Adobe product."""
        return parse_list_output(self._run("--list", "all"))

    def install(self, ccx_path) -> None:
        """Install a .ccx file."""
        self._run("--install", str(ccx_path))

    def remove(self, name: str) -> None:
        """Remove a plugin by display name."""
        self._run("--remove", name)


def _photoshop_versions(
    upia: Upia, package: PluginPackage
) -> List[InstalledPlugin]:
    """Return the installed entries of this plugin for Photoshop."""
    return [
        plugin for plugin in upia.list_plugins()
        if plugin.name == package.name and plugin.product.startswith("Photoshop")
    ]


def ensure_plugin_installed(
    upia: Upia,
    package: PluginPackage,
) -> bool:
    """Make exactly the packaged version of the plugin installed.

    A plugin that was disabled by the user is left disabled: only versions
    are compared. Any other state (missing, other version, duplicates) is
    cleaned up by removing every registered version and installing the
    packaged one, then the result is read back to verify it.

    Args:
        upia (Upia): Installer to use.
        package (PluginPackage): Plugin that should end up installed.

    Returns:
        bool: Installed or up-to-date
    """
    present = _photoshop_versions(upia, package)
    if present and {item.version for item in present} == {package.version}:
        return True

    # One call does not remove every registered version, so repeat.
    for _ in range(len(present) + 2):
        if not present:
            break
        upia.remove(package.name)
        present = _photoshop_versions(upia, package)

    upia.install(package.path)
    return False
