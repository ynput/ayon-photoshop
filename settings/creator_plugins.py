from pydantic import Field

from ayon_server.settings import BaseSettingsModel


class CreateImagePlugin(BaseSettingsModel):
    default_variants: list[str] = Field(default_factory=list,
                                        title="Default Variants")


class CreateFlattenImagePlugin(BaseSettingsModel):
    enabled: bool = Field(False, title="Enabled"),
    flatten_subset_template: str = Field(
        "",
        title="Subset template for flatten image"
    ),
    mark_for_review: bool = Field(False, title="Review"),


class CreateReviewPlugin(BaseSettingsModel):
    enabled: bool = Field(True, title="Enabled")


class CreateWorkfilelugin(BaseSettingsModel):
    enabled: bool = Field(True, title="Enabled"),


class PhotoshopCreatorPlugins(BaseSettingsModel):
    ImageCreator: CreateImagePlugin = Field(
        title="Create Image",
        default_factory=CreateImagePlugin,
    )
    AutoImageCreator: CreateFlattenImagePlugin = Field(
        title="Create Flatten Image",
        default_factory=CreateFlattenImagePlugin,
    )
    ReviewCreator: CreateReviewPlugin = Field(
        title="Create Review",
        default_factory=CreateReviewPlugin,
    )
    WorkfileCreator: CreateWorkfilelugin = Field(
        title="Create Workfile",
        default_factory=CreateWorkfilelugin,
    )