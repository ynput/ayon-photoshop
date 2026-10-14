"""Which Photoshop panel the addon uses, and where that panel connects.

Standard library only, so the addon and the launch hooks share it without
importing anything from AYON.

Photoshop has two panels that talk to the addon over a websocket:

- the CEP extension (`api/extension`), which reads the address from the
  `WEBSOCKET_URL` environment variable
- the UXP plugin (`extension_uxp`), which can NOT read environment variables,
  so its address is written into the plugin itself

Both must never be active at once. The CEP panel also connects to whatever
`WEBSOCKET_URL` says, so with both installed they would end up on the same
server and requests would go to whichever connected first.
"""

import socket
from typing import List

# Set by a launch hook, only while a Photoshop session is already open. It
#   holds the plugin type that session was started with.
RUNNING_PLUGIN_TYPE_ENV = "AYON_PHOTOSHOP_RUNNING_PLUGIN_TYPE"

PANEL_CEP = "cep"
PANEL_UXP = "uxp"
PLUGIN_TYPES = (PANEL_CEP, PANEL_UXP)
DEFAULT_PLUGIN_TYPE = PANEL_CEP

# Port the server listens on for the CEP panel, used when the environment
#   does not say otherwise.
CEP_WEBSOCKET_PORT = 8099

# Port the UXP plugin connects to. Changing it means rebuilding the .ccx.
UXP_WEBSOCKET_PORT = 8101

_PORTS = {
    PANEL_CEP: CEP_WEBSOCKET_PORT,
    PANEL_UXP: UXP_WEBSOCKET_PORT,
}


def get_plugin_type(photoshop_settings: dict) -> str:
    """Get the plugin type selected in the Photoshop project settings.

    Args:
        photoshop_settings (Optional[dict]): The 'photoshop' project
            settings, None or empty when there are none.

    Returns:
        str: 'cep' or 'uxp'. An unknown or missing value gives the default,
            so a typo in the settings never leaves Photoshop without a panel.
    """
    value = (photoshop_settings or {}).get("plugin_type")
    return value if value in PLUGIN_TYPES else DEFAULT_PLUGIN_TYPE


def get_websocket_url(plugin_type: str) -> str:
    """Get the websocket address the server must listen on for a panel.

    Args:
        plugin_type (str): 'cep' or 'uxp'.

    Returns:
        str: Address like 'ws://localhost:8101/ws/'.
    """
    return f"ws://localhost:{_PORTS[plugin_type]}/ws/"


def is_port_in_use(port: int, host="localhost", timeout=0.5) -> bool:
    """Check if something listens on a local port.

    Args:
        port (int): Port to check.
        host (str): Host to check.
        timeout (float): Seconds to wait for the connection.

    Returns:
        bool: True if a connection was accepted.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def get_running_plugin_types() -> List[str]:
    """Find the plugin types of Photoshop sessions that are running now.

    A running session holds the websocket port of its panel (the server is
    started by the launcher process before Photoshop starts), so an occupied
    port means a session with that panel is open.

    Returns:
        list[str]: Plugin types with an occupied port, usually zero or one.
    """
    return [
        plugin_type for plugin_type, port in _PORTS.items()
        if is_port_in_use(port)
    ]
