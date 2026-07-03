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

    def _stamp_context_on_active_document(self):
        """Persist the current session context into the active document.

        Writes folder_path and task_name (from the current session /
        environment) into the active document's own DOC_CONTEXT_METADATA_ID
        File Info entry — kept separate from ayon-core's 'publish_context'
        entry (see get_context_data/update_context_data below) — so that
        later, when this document is re-activated among several open
        documents, the correct AYON context can be restored from it by
        launch_logic._update_context_from_active_document.

        Called after a workfile is opened or saved, when the relevant document
        is guaranteed to be the active one. Skipped when there is no active
        document or when the stored value already matches.
        """
        stub = _get_stub()
        if stub is None:
            return

        folder_path = self.get_current_folder_path()
        task_name = self.get_current_task_name()

        stored = None
        other_meta = []
        for item in stub.get_layers_metadata():
            if item.get("id") == DOC_CONTEXT_METADATA_ID:
                stored = item
            else:
                other_meta.append(item)

        if (stored
                and stored.get("folder_path") == folder_path
                and stored.get("task_name") == task_name):
            return

        doc_context = {
            "id": DOC_CONTEXT_METADATA_ID,
            "folder_path": folder_path,
            "task_name": task_name,
        }
        stub.imprint(doc_context["id"], doc_context, items_meta=other_meta)

    def get_context_data(self):
        """Get stored values for context (validation enable/disable etc)

        Merges every 'publish_context' entry found (later ones win) so that
        the returned data is correct even if a document accidentally holds
        more than one entry from older versions.

        Must only ever hold the data ayon-core itself round-trips here
        (currently 'publish_attributes') — never add extra keys, or
        ayon-core's change-detection in CreateContext will always consider
        the context "changed" and re-save (and re-imprint) on every publish
        action. Document-specific context (folder_path/task_name) is stored
        separately, see _stamp_context_on_active_document.
        """
        stub = _get_stub()
        if stub is None:
            return {}

        data = {}
        found = False
        for item in stub.get_layers_metadata():
            if item.get("id") == "publish_context":
                found = True
                data.update(item)
        if not found:
            return {}
        data.pop("id", None)
        return data

    def update_context_data(self, data, changes=None):
        """Store value needed for context.

        Args:
            data (dict): Data to update.
            changes (TrackChangesItem): Unused, kept for compatibility with
                the HostBase interface signature.
        """
        stub = _get_stub()
        if stub is None:
            return

        context_data = dict(data)
        context_data["id"] = "publish_context"

        items_meta = [
            meta for meta in stub.get_layers_metadata()
            if meta.get("id") != "publish_context"
        ]
        stub.imprint(context_data["id"], context_data, items_meta=items_meta)

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
        host._stamp_context_on_active_document()


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
