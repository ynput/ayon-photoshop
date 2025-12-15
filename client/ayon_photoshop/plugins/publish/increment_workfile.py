import os

import pyblish.api

from ayon_core.lib import version_up
from ayon_core.host import IWorkfileHost
from ayon_core.pipeline import registered_host, OptionalPyblishPluginMixin
from ayon_core.pipeline.publish import get_errored_plugins_from_context


class IncrementWorkfile(pyblish.api.ContextPlugin, OptionalPyblishPluginMixin):
    """Increment the current workfile.

    Saves the current scene with an increased version number.
    """

    label = "Increment Workfile"
    order = pyblish.api.IntegratorOrder + 9.0
    hosts = ["photoshop"]
    optional = True

    def process(self, context: pyblish.api.Context):
        if not self.is_active(context.data):
            return

        errored_plugins = get_errored_plugins_from_context(context)
        if errored_plugins:
            raise RuntimeError(
                "Skipping incrementing current file because publishing failed."
            )

        current_filepath: str = context.data["currentFile"]
        host: IWorkfileHost = registered_host()
        try:
            from ayon_core.pipeline.workfile import save_next_version
            from ayon_core.host.interfaces import SaveWorkfileOptionalData

            current_filename = os.path.basename(current_filepath)
            save_next_version(
                description=(
                    f"Incremented by publishing from {current_filename}"
                ),
                # Optimize the save by reducing needed queries for context
                prepared_data=SaveWorkfileOptionalData(
                    project_entity=context.data["projectEntity"],
                    project_settings=context.data["project_settings"],
                    anatomy=context.data["anatomy"],
                )
            )
            new_scene_path = host.get_current_workfile()

        except ImportError:
            # Backwards compatibility before ayon-core 1.5.0
            self.log.debug(
                "Using legacy `version_up`. Update AYON core addon to "
                "use newer `save_next_version` function."
            )
            new_scene_path = version_up(current_filepath)
            host.save_workfile(new_scene_path)

        self.log.info(f"Incremented workfile to: {new_scene_path}")
