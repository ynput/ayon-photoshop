import os
import sys
import contextlib
import traceback
import functools
import pyblish

from ayon_core.lib import env_value_to_bool, Logger, is_in_tests
from ayon_core.addon import AddonsManager
from ayon_core.pipeline import install_host
from ayon_core.tools.utils import host_tools
from ayon_core.tools.utils import get_ayon_qt_app

from .launch_logic import ProcessLauncher, stub

log = Logger.get_logger(__name__)


def safe_excepthook(*args):
    traceback.print_exception(*args)


def main(*subprocess_args):
    from ayon_photoshop.api import PhotoshopHost

    host = PhotoshopHost()
    install_host(host)

    sys.excepthook = safe_excepthook

    # coloring in StdOutBroker
    os.environ["AYON_LOG_NO_COLORS"] = "0"
    app = get_ayon_qt_app()
    app.setQuitOnLastWindowClosed(False)

    launcher = ProcessLauncher(subprocess_args)
    launcher.start()

    env_workfiles_on_launch = os.getenv(
        "AYON_PHOTOSHOP_WORKFILES_ON_LAUNCH",
        # Backwards compatibility
        os.getenv("AVALON_PHOTOSHOP_WORKFILES_ON_LAUNCH", True)
    )
    workfiles_on_launch = env_value_to_bool(value=env_workfiles_on_launch)

    if is_in_tests():
        manager = AddonsManager()
        photoshop_addon = manager["photoshop"]

        launcher.execute_in_main_thread(
            functools.partial(
                photoshop_addon.publish_in_test,
                log,
                "ClosePS",
            )
        )
    elif env_value_to_bool("HEADLESS_PUBLISH"):
        manager = AddonsManager()
        webpublisher_addon = manager["webpublisher"]
        launcher.execute_in_main_thread(
            webpublisher_addon.headless_publish,
            log,
            "ClosePS",
            is_in_tests()
        )
    elif workfiles_on_launch:

        launcher.execute_in_main_thread(
            host_tools.show_workfiles,
            save=env_value_to_bool("WORKFILES_SAVE_AS")
        )

    sys.exit(app.exec_())


@contextlib.contextmanager
def maintained_selection():
    """Maintain selection during context."""
    selection = stub().get_selected_layers()
    try:
        yield selection
    finally:
        stub().select_layers(selection)


def _get_layers_by_parent(all_layers):
    """Group layers by their immediate parent ID."""
    by_parent = {None: []}
    for layer in all_layers:
        parent_id = layer.parents[-1] if layer.parents else None
        if parent_id not in by_parent:
            by_parent[parent_id] = []
        by_parent[parent_id].append(layer)
    return by_parent


@contextlib.contextmanager
def isolated_layers_visibility(stub, layer_ids, all_layers=None):
    """Show only the specified layers and their ancestor paths, hiding all siblings.
    
    Similar to isolated_instance_visibility but supports multiple layer IDs.
    All specified layers and their ancestors will be visible simultaneously.
    
    Args:
        stub: PhotoshopServerStub
        layer_ids: List of layer IDs to show (can be single layer or multiple)
        all_layers: Optional list of PSItem layers (fetched if not provided)
    
    Tracks original visibility and restores it on exit.
    """
    if all_layers is None:
        all_layers = stub.get_layers()
    
    # Normalize to list if single ID provided
    if not isinstance(layer_ids, (list, tuple, set)):
        layer_ids = [layer_ids]
    
    layers_by_id = {layer.id: layer for layer in all_layers}
    layers_by_parent = _get_layers_by_parent(all_layers)
    
    # Build paths from all target layers to top-level
    path_ids = set()
    for layer_id in layer_ids:
        current = layers_by_id.get(layer_id)
        if not current:
            continue  # Skip if layer not found
        while current:
            path_ids.add(current.id)
            current = layers_by_id.get(current.parents[-1]) if current.parents else None

    if not path_ids:
        yield  # No-op if no valid layers found
        return

    # Record original visibility and build change map
    original_visibility = {}
    visibility_changes = {}
    
    for layer_id in path_ids:
        layer = layers_by_id.get(layer_id)
        if not layer:
            continue
        parent_id = layer.parents[-1] if layer.parents else None
        for sibling in layers_by_parent.get(parent_id, []):
            # Record original state before any changes
            if sibling.id not in original_visibility:
                original_visibility[sibling.id] = sibling.visible
            # Path layers visible, siblings hidden
            visibility_changes[sibling.id] = sibling.id in path_ids

    try:
        if visibility_changes:
            stub.set_layers_visibility(visibility_changes)
        yield
    finally:
        # Restore original visibility state
        if original_visibility:
            stub.set_layers_visibility(original_visibility)


def find_close_plugin(close_plugin_name, log):
    if close_plugin_name:
        plugins = pyblish.api.discover()
        for plugin in plugins:
            if plugin.__name__ == close_plugin_name:
                return plugin

    log.debug("Close plugin not found, app might not close.")


def publish_in_test(log, close_plugin_name=None):
    """Loops through all plugins, logs to console. Used for tests.
    Args:
        log (Logger)
        close_plugin_name (Optional[str]): Name of plugin with responsibility
            to close application.
    """

    # Error exit as soon as any error occurs.
    error_format = "Failed {plugin.__name__}: {error} -- {error.traceback}"
    close_plugin = find_close_plugin(close_plugin_name, log)

    for result in pyblish.util.publish_iter():
        for record in result["records"]:
            # Why do we log again? pyblish logger is logging to stdout...
            log.info("{}: {}".format(result["plugin"].label, record.msg))

        if not result["error"]:
            continue

        # QUESTION We don't break on error?
        error_message = error_format.format(**result)
        log.error(error_message)
        if close_plugin:  # close host app explicitly after error
            context = pyblish.api.Context()
            try:
                close_plugin().process(context)
            except Exception as exp:
                print(exp)
