from pathlib import Path

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

    Two things are checked:

    1. The active document did not change since the publisher was last
       reset (window opened, Refresh clicked, or previous publish attempt —
       see CollectRefreshCreateContext). AYON now silently re-syncs its
       session context whenever the active document changes, so this would
       otherwise go unnoticed even though the instances/report the artist
       is looking at may no longer reflect the document about to be
       published. Requires an explicit Refresh (or disabling the
       validator) to acknowledge the switch before publishing.
    2. The active document belongs to the current AYON context at all
       (project / folder / task), which catches documents opened directly
       (not through the AYON Workfiles tool) that never had any AYON
       context associated with them.

    Publishing in either state could file outputs under the wrong context
    or leave the artist confused about what was actually published. This
    validator catches both cases early and blocks the publish with a clear
    explanation.
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

        self._validate_no_document_switch(context, current_file)
        self._validate_document_in_context(current_file)

    def _validate_no_document_switch(
        self, context: pyblish.api.Context, current_file: str
    ):
        """Raise if the active document changed since the last refresh.

        Args:
            context (pyblish.api.Context): The context object.
            current_file (str): Path to the current active document.
        """
        reset_workfile_path = context.data.get("contextRefreshWorkfilePath")
        if not reset_workfile_path:
            return

        current_path = Path(current_file)
        reset_path = Path(reset_workfile_path)
        if reset_path.resolve() == current_path.resolve():
            return

        doc_name = current_path.name
        previous_doc_name = reset_path.name

        msg = (
            f"Active document changed from '{previous_doc_name}' to "
            f"'{doc_name}' since the publisher was last refreshed."
        )
        repair_msg = (
            "Click Refresh to acknowledge the new active document and its "
            "context, then re-publish.\n"
            "Alternatively, disable this validator if publishing right "
            "after switching documents is intentional.\n"
        )
        formatting_data = {
            "msg": msg,
            "repair_msg": repair_msg,
            "previous_doc_name": previous_doc_name,
            "doc_name": doc_name,
        }
        raise PublishXmlValidationError(
            self,
            msg,
            key="document_switched",
            formatting_data=formatting_data,
        )

    def _validate_document_in_context(self, current_file: str):
        """Raise if the active document isn't inside the current context's
        expected work directory.

        Args:
            current_file (str): Path to the current active document.
        """
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
        expected_work_root = Path(
            work_template["directory"].format_strict(data)
        ).resolve()

        current_path = Path(current_file).resolve()
        if current_path.is_relative_to(expected_work_root):
            return

        doc_name = current_path.name
        current_dir = current_path.parent.as_posix()

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
            "expected_work_root": expected_work_root.as_posix(),
            "current_dir": current_dir,
            "doc_name": doc_name,
        }
        raise PublishXmlValidationError(
            self, msg, formatting_data=formatting_data
        )
