from __future__ import annotations
from .constants import (
    ValidatePipelineOrder,
    ValidateContentsOrder,
    ValidateSceneOrder,
    ValidateMeshOrder,
    FARM_JOB_ENV_DATA_KEY,
)

from .publish_plugins import (
    AbstractMetaInstancePlugin,
    AbstractMetaContextPlugin,

    KnownPublishError,
    PublishError,
    PublishValidationError,
    PublishXmlValidationError,

    AYONPyblishPluginMixin,
    OptionalPyblishPluginMixin,

    RepairAction,
    RepairContextAction,

    Extractor,
    ColormanagedPyblishPluginMixin
)

from .lib import (
    get_publish_template_name,

    publish_plugins_discover,
    filter_crashed_publish_paths,
    load_help_content_from_plugin,
    load_help_content_from_filepath,

    get_errored_instances_from_context,
    get_errored_plugins_from_context,

    filter_instances_for_context_plugin,
    context_plugin_should_run,
    get_instance_staging_dir,
    get_publish_repre_path,

    apply_plugin_settings_automatically,
    get_plugin_settings,
    get_publish_instance_label,
    get_publish_instance_families,

    main_cli_publish,

    add_trait_representations,
    get_trait_representations,
    has_trait_representations,
    set_trait_representations,

    get_default_reviewable_layers,
)

from .abstract_expected_files import ExpectedFiles
try:
    from .abstract_collect_render import (
        RenderInstance,
        AbstractCollectRender,
    )
except (ImportError, SyntaxError):
    # Python 3.7 (e.g. Nuke 13.0) cannot parse typing_extensions >= 4.x
    # which is a transitive dependency of attr used by abstract_collect_render.
    # Hosts on Python 3.7 do not use the abstract render collection pipeline.
    RenderInstance = None
    AbstractCollectRender = None


__all__ = (
    "ValidatePipelineOrder",
    "ValidateContentsOrder",
    "ValidateSceneOrder",
    "ValidateMeshOrder",
    "FARM_JOB_ENV_DATA_KEY",

    "AbstractMetaInstancePlugin",
    "AbstractMetaContextPlugin",

    "KnownPublishError",
    "PublishError",
    "PublishValidationError",
    "PublishXmlValidationError",

    "AYONPyblishPluginMixin",
    "OptionalPyblishPluginMixin",

    "RepairAction",
    "RepairContextAction",

    "Extractor",
    "ColormanagedPyblishPluginMixin",

    "get_publish_template_name",

    "publish_plugins_discover",
    "filter_crashed_publish_paths",
    "load_help_content_from_plugin",
    "load_help_content_from_filepath",

    "get_errored_instances_from_context",
    "get_errored_plugins_from_context",

    "filter_instances_for_context_plugin",
    "context_plugin_should_run",
    "get_instance_staging_dir",
    "get_publish_repre_path",

    "apply_plugin_settings_automatically",
    "get_plugin_settings",
    "get_publish_instance_label",
    "get_publish_instance_families",

    "main_cli_publish",

    "ExpectedFiles",

    "RenderInstance",
    "AbstractCollectRender",

    "add_trait_representations",
    "get_trait_representations",
    "has_trait_representations",
    "set_trait_representations",

    "get_default_reviewable_layers",
)
