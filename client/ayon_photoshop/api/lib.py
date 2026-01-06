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


@contextlib.contextmanager
def maintained_visibility(layers=None):
    """Maintain visibility during context.

    Args:
        layers (list) of PSItem (used for caching)
    """
    visibility = {}
    if not layers:
        layers = stub().get_layers()
    for layer in layers:
        visibility[layer.id] = layer.visible
    try:
        yield
    finally:
        for layer in layers:
            stub().set_visible(layer.id, visibility[layer.id])
            pass


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
def isolated_instance_visibility(stub, instance_id, all_layers=None):
    """Show only the instance and its ancestor path, hiding all siblings.
    
    Args:
        stub: PhotoshopServerStub
        instance_id: Layer ID of the instance LayerSet
        all_layers: Optional list of PSItem layers (fetched if not provided)
    
    Tracks original visibility and restores it on exit.
    """
    if all_layers is None:
        all_layers = stub.get_layers()
    
    layers_by_id = {l.id: l for l in all_layers}
    layers_by_parent = _get_layers_by_parent(all_layers)
    
    # Find instance layer
    instance_layer = layers_by_id.get(instance_id)
    if not instance_layer:
        yield  # No-op if instance not found
        return

    # Build ancestor path from instance to top-level
    path_ids = set()
    current = instance_layer
    while current:
        path_ids.add(current.id)
        current = layers_by_id.get(current.parents[-1]) if current.parents else None

    # Record original visibility and build change map
    original_visibility = {}
    visibility_changes = {}
    
    for layer_id in path_ids:
        layer = layers_by_id[layer_id]
        parent_id = layer.parents[-1] if layer.parents else None
        for sibling in layers_by_parent.get(parent_id, []):
            # Record original state before any changes
            original_visibility[sibling.id] = sibling.visible
            # Path layers visible, siblings hidden
            visibility_changes[sibling.id] = sibling.id in path_ids

    try:
        stub.set_layers_visibility(visibility_changes)
        yield
    finally:
        # Restore original visibility state
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
