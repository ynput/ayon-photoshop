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

PANEL_CEP = "cep"
PANEL_UXP = "uxp"
PANEL_TYPES = (PANEL_CEP, PANEL_UXP)
DEFAULT_PANEL_TYPE = PANEL_CEP

# Port the server listens on for the CEP panel, used when the environment
#   does not say otherwise.
CEP_WEBSOCKET_PORT = 8099

# Port the UXP plugin connects to. It is written into the plugin in three
#   places that have to agree with this number and with each other:
#   extension_uxp/ayon_uxp/main.js (WS_URL),
#   extension_uxp/ayon_uxp/client_RPC.js (default_url) and
#   extension_uxp/ayon_uxp/manifest.json (network permission, "ws://" needs
#   its own entry, "all" only covers http and https).
# Changing it means rebuilding the .ccx.
UXP_WEBSOCKET_PORT = 8101

_PORTS = {
    PANEL_CEP: CEP_WEBSOCKET_PORT,
    PANEL_UXP: UXP_WEBSOCKET_PORT,
}


def get_panel_type(photoshop_settings: dict) -> str:
    """Get the panel type selected in the Photoshop project settings.

    Args:
        photoshop_settings (Optional[dict]): The 'photoshop' project
            settings, None or empty when there are none.

    Returns:
        str: 'cep' or 'uxp'. An unknown or missing value gives the default,
            so a typo in the settings never leaves Photoshop without a panel.
    """
    value = (photoshop_settings or {}).get("panel_type")
    return value if value in PANEL_TYPES else DEFAULT_PANEL_TYPE


def get_websocket_url(panel_type: str) -> str:
    """Get the websocket address the server must listen on for a panel.

    Args:
        panel_type (str): 'cep' or 'uxp'.

    Returns:
        str: Address like 'ws://localhost:8101/ws/'.
    """
    return f"ws://localhost:{_PORTS[panel_type]}/ws/"


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


def get_running_panel_types() -> List[str]:
    """Find the panel types of Photoshop sessions that are running now.

    A running session holds the websocket port of its panel (the server is
    started by the launcher process before Photoshop starts), so an occupied
    port means a session with that panel is open.

    Returns:
        list[str]: Panel types with an occupied port, usually zero or one.
    """
    return [
        panel_type for panel_type, port in _PORTS.items()
        if is_port_in_use(port)
    ]
