from pathlib import Path

# Go up twice. Assumes paths.py is not moved
ROOT_PATH = Path(__file__).parent.parent

# Top Level
ASSETS_PATH = ROOT_PATH / 'assets'
CONFIG_PATH = ROOT_PATH / 'config'
DATASETS_PATH = ROOT_PATH / 'datasets'
OUTPUT_PATH = ROOT_PATH / 'output'
PKG_ROOT_PATH = ROOT_PATH / 'skactiveml_annotation'
DOCS_PATH = ROOT_PATH / 'docs'

# config
EMBEDDING_CONFIG_PATH = CONFIG_PATH / 'embedding'
DATA_CONFIG_PATH = CONFIG_PATH / 'dataset'
MODEL_CONFIG_PATH = CONFIG_PATH / 'model'
QS_CONFIG_PATH = CONFIG_PATH / 'query_strategy'

# output/user
USER_OUTPUT_PATH = OUTPUT_PATH / 'user'
ANNOTATED_PATH = USER_OUTPUT_PATH / 'annotated'
AUTO_ANNOTATED_PATH = USER_OUTPUT_PATH / 'auto-annotated'
EMBEDDED_PATH = USER_OUTPUT_PATH / 'embedded'
OVERRIDE_CONFIG_PATH = USER_OUTPUT_PATH / 'override_config'
# output/user/override_config
OVERRIDE_CONFIG_DATASET_PATH = OVERRIDE_CONFIG_PATH / 'dataset'

# output/internal
TOOL_OUTPUT_PATH = OUTPUT_PATH / 'internal'
CACHE_PATH = TOOL_OUTPUT_PATH / 'cache'
PROFILER_PATH = TOOL_OUTPUT_PATH / 'profiler'
HISTORY_IDX_PATH = TOOL_OUTPUT_PATH / 'annotation_history_idx'
# output/internal/cache
BACKGROUND_CALLBACK_CACHE_PATH = CACHE_PATH / 'background_callback_cache'

# skactiveml_annotation
UI_PATH = PKG_ROOT_PATH / 'ui'

# skactiveml_annotation/ui
PAGES_PATH = UI_PATH / 'pages'
