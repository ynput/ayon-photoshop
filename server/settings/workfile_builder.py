from ayon_server.settings import (
    BaseSettingsModel,
    SettingsField,
    MultiplatformPathModel,
    task_types_enum,
)


class CustomBuilderTemplate(BaseSettingsModel):
    _layout = "expanded"
    task_types: list[str] = SettingsField(
        default_factory=list,
        title="Task types",
        enum_resolver=task_types_enum
    )

    path: MultiplatformPathModel = SettingsField(
        default_factory=MultiplatformPathModel,
        title="Template path"
    )


class WorkfileBuilderPlugin(BaseSettingsModel):
    _title = "Workfile Builder"
    create_first_version: bool = SettingsField(
        False,
        title="Create first workfile"
    )

    custom_templates: list[CustomBuilderTemplate] = SettingsField(
        default_factory=CustomBuilderTemplate,
        title="Template profiles"
    )
