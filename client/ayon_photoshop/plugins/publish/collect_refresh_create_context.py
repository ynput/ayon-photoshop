import pyblish.api


class CollectRefreshCreateContext(pyblish.api.ContextPlugin):
    """Refresh CreateContext's cached current context before it is used.

    Photoshop can have several documents open at once and the active one can
    change (and its AYON context along with it, see
    launch_logic._update_context_from_active_document) without the publisher
    window being explicitly refreshed. In that case CreateContext still holds
    a stale cached context (only updated by CreateContext.reset(), i.e. the
    Refresh button).

    Must run before CollectFromCreateContext. Because later it copies the 
    cached context back into AYON_FOLDER_PATH/AYON_TASK_NAME env vars, 
    so a stale cache would overwrite the correct live context. 
    Refresh the cache here, before that happens, so it reflects the active 
    document.

    NB: ``reset_current_context()`` could be added in ayon-core's own
    CollectFromCreateContext instead, fixing this for every host, but the
    fix is kept Photoshop-only here to avoid touching shared ayon-core
    behavior.

    Also stashes the workfile path that was active *before* this refresh
    (i.e. as of the publisher's last full reset or previous publish
    attempt) onto ``context.data["contextRefreshWorkfilePath"]``, so
    ValidateActiveDocumentContext can detect that the active document
    changed since then, even if the new document has valid context of its
    own.
    """

    # Before CollectFromCreateContext
    order = pyblish.api.CollectorOrder - 0.51
    label = "Refresh Create Context"
    hosts = ["photoshop"]

    def process(self, context):
        create_context = context.data.get("create_context")
        if create_context is None:
            return

        context.data["contextRefreshWorkfilePath"] = (
            create_context.get_current_workfile_path()
        )

        create_context.reset_current_context()
