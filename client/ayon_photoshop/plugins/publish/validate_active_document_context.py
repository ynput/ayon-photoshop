import os

import pyblish.api

from ayon_core.pipeline import (
    get_current_project_name,
    get_current_folder_path,
    get_current_task_name,
    Anatomy,
)
from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    PublishXmlValidationError,
    OptionalPyblishPluginMixin,
)
from ayon_core.pipeline.template_data import get_template_data_with_names
from ayon_core.pipeline.workfile import get_workfile_template_key_from_context


class ValidateActiveDocumentContext(
    OptionalPyblishPluginMixin,
    pyblish.api.ContextPlugin,
):
    """Validate that the active document belongs to the current AYON context.

    When multiple Photoshop documents are open and the user switches between
    them outside of the AYON Workfiles tool, the AYON session context
    (project / folder / task) may no longer match the active document.

    Publishing in that state would file outputs under the wrong context.
    This validator catches the mismatch early and blocks the publish with a
    clear explanation, preventing silent mis-attribution of published data.
    """

    label = "Validate Active Document Context"
    hosts = ["photoshop"]
    order = ValidateContentsOrder - 0.1
    optional = True
    active = True

    def process(self, context):
        if not self.is_active(context.data):
            return

        current_file = context.data.get("currentFile", "")
        if not current_file:
            # Unsaved / no document open — let other validators handle this.
            return

        project_name = get_current_project_name()
        folder_path = get_current_folder_path()
        task_name = get_current_task_name()

        if not folder_path or not task_name:
            return

        template_key = get_workfile_template_key_from_context(
            project_name, folder_path, task_name, "photoshop"
        )
        anatomy = Anatomy(project_name)
        data = get_template_data_with_names(
            project_name, folder_path, task_name, "photoshop"
        )
        data["root"] = anatomy.roots
        work_template = anatomy.get_template_item("work", template_key)
        expected_work_root = os.path.normpath(
            work_template["directory"].format_strict(data)
        ).replace("\\", "/")

        current_file_norm = os.path.normpath(current_file).replace("\\", "/")

        if current_file_norm.startswith(expected_work_root):
            return

        doc_name = os.path.basename(current_file)
        current_dir = os.path.dirname(current_file_norm)

        msg = (
            f"Active document '{doc_name}' is outside the expected work "
            f"directory for the current AYON context."
        )
        repair_msg = (
            "Open the correct workfile via the AYON Workfiles tool to "
            "sync the context with the document, then re-publish.\n"
            "Alternatively, disable this validator if publishing to a "
            "different context is intentional.\n"
        )
        formatting_data = {
            "msg": msg,
            "repair_msg": repair_msg,
            "folder_path": folder_path,
            "task_name": task_name,
            "expected_work_root": expected_work_root,
            "current_dir": current_dir,
            "doc_name": doc_name,
        }
        raise PublishXmlValidationError(
            self, msg, formatting_data=formatting_data
        )
