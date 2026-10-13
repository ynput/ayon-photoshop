from ayon_applications import PreLaunchHook, LaunchTypes

from ayon_photoshop.panel_type import get_panel_type, get_websocket_url


class SetPhotoshopPanelWebsocket(PreLaunchHook):
    """Make the websocket server listen where the selected panel connects.

    The CEP panel reads its address from the 'WEBSOCKET_URL' environment
    variable, the UXP plugin can't read environment variables and always
    connects to its own port. The server (the 'launch_script.py' process
    started for Photoshop) reads the same variable to know the port to
    listen on, so it has to match the panel type of the project.

    This is a hook and not 'PhotoshopAddon.add_implementation_envs' because
    the panel type is a project setting, and that method has no access to it.

    Runs before the hooks that install the panels.
    """

    app_groups = {"photoshop"}

    order = 0
    # Farm and remote launches start Photoshop in other ways, and a headless
    #   publish has no panel to choose.
    launch_types = {LaunchTypes.local}

    def execute(self):
        settings = self.data["project_settings"]["photoshop"]
        panel_type = get_panel_type(settings)
        url = get_websocket_url(panel_type)

        # Not 'setdefault': the addon already put the CEP address there, and
        #   this is the one place that knows the real panel type. A user who
        #   set their own address in the app environment is respected for CEP
        #   only, UXP has no way to follow a custom address.
        current = self.launch_context.env.get("WEBSOCKET_URL")
        if panel_type == "uxp" or not current:
            self.launch_context.env["WEBSOCKET_URL"] = url

        self.log.debug(
            f"Photoshop panel type '{panel_type}', websocket "
            f"{self.launch_context.env['WEBSOCKET_URL']}"
        )
