import os

from qtpy import QtWidgets

import pyblish.api

from ayon_core.lib import register_event_callback, Logger
from ayon_core.pipeline import (
    register_loader_plugin_path,
    register_creator_plugin_path,
    registered_host,
    AVALON_CONTAINER_ID,
    AYON_INSTANCE_ID,
    AVALON_INSTANCE_ID,
)

from ayon_core.host import (
    HostBase,
    IWorkfileHost,
    ILoadHost,
    IPublishHost
)

from ayon_core.pipeline.load import any_outdated_containers
from ayon_core.tools.utils import get_ayon_qt_app
from ayon_photoshop import PHOTOSHOP_ADDON_ROOT

from . import lib
from .launch_logic import ConnectionNotEstablishedYet, DOC_CONTEXT_METADATA_ID

log = Logger.get_logger(__name__)

PLUGINS_DIR = os.path.join(PHOTOSHOP_ADDON_ROOT, "plugins")
PUBLISH_PATH = os.path.join(PLUGINS_DIR, "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "create")
INVENTORY_PATH = os.path.join(PLUGINS_DIR, "inventory")


class PhotoshopHost(HostBase, IWorkfileHost, ILoadHost, IPublishHost):
    name = "photoshop"

    def install(self):
        """Install Photoshop-specific functionality needed for integration.

        This function is called automatically on calling
        `api.install(photoshop)`.
        """
        log.info("Installing OpenPype Photoshop...")
        pyblish.api.register_host("photoshop")

        pyblish.api.register_plugin_path(PUBLISH_PATH)
        register_loader_plugin_path(LOAD_PATH)
        register_creator_plugin_path(CREATE_PATH)

        register_event_callback("application.launched", on_application_launch)

    def work_root(self, session):
        return os.path.normpath(session["AYON_WORKDIR"]).replace("\\", "/")

    def open_workfile(self, filepath):
        lib.stub().open(filepath)

        # Stamp the freshly opened document with the current context so it can
        # be restored later when switching between multiple open documents.
        self._stamp_context_on_active_document()

        return True

    def save_workfile(self, filepath=None):
        _, ext = os.path.splitext(filepath)
        lib.stub().saveAs(filepath, ext.lstrip("."), False)

        # Stamp the saved document with the current context.
        self._stamp_context_on_active_document()

    def get_current_workfile(self):
        try:
            full_name = lib.stub().get_active_document_full_name()
            if full_name and full_name != "null":
                return os.path.normpath(full_name).replace("\\", "/")
        except Exception:
            pass

        return None

    def workfile_has_unsaved_changes(self):
        if self.get_current_workfile():
            return not lib.stub().is_saved()

        return False

    def get_workfile_extensions(self):
        return [".psd", ".psb"]

    def get_containers(self):
        return ls()

    def _get_doc_context_metadata(self):
        """Read project/folder/task stored in the active documen.

        Returns:
            dict: With keys 'project_name'/'folder_path'/'task_name' if the
                active document was stamped with a context, empty dict
                otherwise (no active document, or never stamped yet).
        """
        stub = _get_stub()
        if stub is None:
            return {}

        try:
            layers_meta = stub.get_layers_metadata()
        except Exception:
            log.warning(
                "Failed to read doc-context metadata", exc_info=True
            )
            return {}

        for item in layers_meta:
            if item.get("id") == DOC_CONTEXT_METADATA_ID:
                return item

        return {}

    def get_current_project_name(self):
        context = self.get_current_context()
        return context["project_name"]

    def get_current_folder_path(self):
        context = self.get_current_context()
        return context["folder_path"]

    def get_current_task_name(self):
        context = self.get_current_context()
        return context["task_name"]

    def get_current_context(self):
        doc_context = self._get_doc_context_metadata()
        project_name = doc_context.get("project_name")
        if project_name:
            return {
                "project_name": project_name,
                "folder_path": doc_context["folder_path"],
                "task_name": doc_context["task_name"],
            }
        # Older workfiles might not have stored the context
        # - can happen if workfile was not opened using
        #   AYON workfile api
        return super().get_current_context()

    def _stamp_context_on_active_document(self, only_if_unstamped=False):
        """Persist the current session context into the active document.

        Writes project_name/folder_path/task_name into the active
        document's own DOC_CONTEXT_METADATA_ID File Info entry — kept
        separate from ayon-core's 'publish_context'.

        Called after a workfile is opened or saved, when the relevant
        document is guaranteed to be the active one. Skipped when there is
        no active document or when the stored value already matches.

        Args:
            only_if_unstamped (bool): When True, never overwrite an existing
                stamp — only write one if the active document has none yet.
                Meant to avoid overwriting a document's own context with the
                wrong Environment variables values.
        """
        stub = _get_stub()
        if stub is None:
            return

        stored = None
        other_meta = []
        for item in stub.get_layers_metadata():
            if item.get("id") == DOC_CONTEXT_METADATA_ID:
                stored = item
            else:
                other_meta.append(item)

        if only_if_unstamped and stored:
            return

        project_name = super().get_current_project_name()
        folder_path = super().get_current_folder_path()
        task_name = super().get_current_task_name()

        if (stored
                and stored.get("project_name") == project_name
                and stored.get("folder_path") == folder_path
                and stored.get("task_name") == task_name):
            return

        doc_context = {
            "id": DOC_CONTEXT_METADATA_ID,
            "project_name": project_name,
            "folder_path": folder_path,
            "task_name": task_name,
        }
        stub.imprint(doc_context["id"], doc_context, items_meta=other_meta)

    def get_context_data(self):
        """Get stored values for context (validation enable/disable etc)"""
        meta = _get_stub().get_layers_metadata()
        for item in meta:
            if item.get("id") == "publish_context":
                item.pop("id")
                return item
        return {}

    def update_context_data(self, data, changes):
        """Store value needed for context"""
        item = data
        item["id"] = "publish_context"
        _get_stub().imprint(item["id"], item)

    def list_instances(self):
        """List all created instances to publish from current workfile.

        Pulls from File > File Info

        Returns:
            (list) of dictionaries matching instances format
        """
        stub = _get_stub()

        if not stub:
            return []

        instances = []
        layers_meta = stub.get_layers_metadata()
        if layers_meta:
            for instance in layers_meta:
                if instance.get("id") in {
                    AYON_INSTANCE_ID, AVALON_INSTANCE_ID
                }:
                    instances.append(instance)

        return instances

    def remove_instance(self, instance):
        """Remove instance from current workfile metadata.

        Updates metadata of current file in File > File Info and removes
        icon highlight on group layer.

        Args:
            instance (dict): instance representation from subsetmanager model
        """
        stub = _get_stub()

        if not stub:
            return

        inst_id = instance.get("instance_id") or instance.get("uuid")  # legacy
        if not inst_id:
            log.warning("No instance identifier for {}".format(instance))
            return

        stub.remove_instance(inst_id)

        if instance.get("members"):
            item = stub.get_layer(instance["members"][0])
            if item:
                stub.rename_layer(item.id,
                                  item.name.replace(stub.PUBLISH_ICON, ''))


def check_inventory():
    if not any_outdated_containers():
        return

    # Warn about outdated containers.
    _app = get_ayon_qt_app()

    message_box = QtWidgets.QMessageBox()
    message_box.setIcon(QtWidgets.QMessageBox.Warning)
    msg = "There are outdated containers in the scene."
    message_box.setText(msg)
    message_box.exec_()


def on_application_launch():
    check_inventory()

    # The very first document at Photoshop startup is opened natively via a
    # command-line argument (see pre_launch_args.py), before the CEP
    # extension even connects. It never goes through PhotoshopHost's
    # open_workfile()/set_context route, so it is otherwise never stamped
    # with a doc-context entry. At this point the environment already
    # holds the correct folder_path/task_name (set by AYON before Photoshop
    # was launched), so stamp it now that the connection is established.
    host = registered_host()
    if hasattr(host, "_stamp_context_on_active_document"):
        host._stamp_context_on_active_document(only_if_unstamped=True)


def ls():
    """Yields containers from active Photoshop document

    This is the host-equivalent of api.ls(), but instead of listing
    assets on disk, it lists assets already loaded in Photoshop; once loaded
    they are called 'containers'

    Yields:
        dict: container

    """
    try:
        stub = lib.stub()  # only after Photoshop is up
    except ConnectionNotEstablishedYet:
        print("Not connected yet, ignoring")
        return

    if not stub.get_active_document_name():
        return

    layers_meta = stub.get_layers_metadata()  # minimalize calls to PS
    for layer in stub.get_layers():
        data = stub.read(layer, layers_meta)

        # Skip non-tagged layers.
        if not data:
            continue

        # Filter to only containers.
        if "container" not in data["id"]:
            continue

        # Append transient data
        data["objectName"] = layer.name.replace(stub.LOADED_ICON, '')
        data["layer"] = layer

        yield data


def _get_stub():
    """Handle pulling stub from PS to run operations on host

    Returns:
        (PhotoshopServerStub) or None
    """
    try:
        stub = lib.stub()  # only after Photoshop is up
    except ConnectionNotEstablishedYet:
        print("Not connected yet, ignoring")
        return

    if not stub.get_active_document_name():
        return

    return stub


def containerise(
    name, namespace, layer, context, loader=None, suffix="_CON"
):
    """Imprint layer with metadata

    Containerisation enables a tracking of version, author and origin
    for loaded assets.

    Arguments:
        name (str): Name of resulting assembly
        namespace (str): Namespace under which to host container
        layer (PSItem): Layer to containerise
        context (dict): Asset information
        loader (str, optional): Name of loader used to produce this container.
        suffix (str, optional): Suffix of container, defaults to `_CON`.

    Returns:
        container (str): Name of container assembly
    """
    layer.name = name + suffix

    data = {
        "schema": "openpype:container-2.0",
        "id": AVALON_CONTAINER_ID,
        "name": name,
        "namespace": namespace,
        "loader": str(loader),
        "representation": context["representation"]["id"],
        "members": [str(layer.id)]
    }
    stub = lib.stub()
    stub.imprint(layer.id, data)

    return layer


def cache_and_get_instances(creator):
    """Cache instances in shared data.

    Storing all instances as a list as legacy instances might be still present.
    Args:
        creator (Creator): Plugin which would like to get instances from host.
    Returns:
        List[]: list of all instances stored in metadata
    """
    shared_key = "openpype.photoshop.instances"
    if shared_key not in creator.collection_shared_data:
        creator.collection_shared_data[shared_key] = \
            creator.host.list_instances()
    return creator.collection_shared_data[shared_key]
