import sys
import os

def launch(photoshop_path):
    # Check the system architecture
    if sys.platform == 'darwin':  # macOS
        if os.uname().machine == 'arm64':  # arm architecture
            # Use the arm plugin
            plugin_path = os.path.join(os.path.dirname(__file__), 'hosts', 'photoshop', 'api', 'arm', 'extension.zxp')
        else:  # x86_64 architecture
            # Use the x86_64 plugin
            plugin_path = os.path.join(os.path.dirname(__file__), 'hosts', 'photoshop', 'api', 'x86_64', 'extension.zxp')
    else:
        # Use the default plugin
        plugin_path = os.path.join(os.path.dirname(__file__), 'hosts', 'photoshop', 'api', 'extension.zxp')

    # Launch Photoshop with the correct plugin
    os.system(f'"{photoshop_path}" -extension "{plugin_path}"')