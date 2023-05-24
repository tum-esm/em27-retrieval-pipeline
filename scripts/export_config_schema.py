import json
import os
import tum_esm_utils
import sys
import jsonref

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)
CONFIG_JSON_TARGET = os.path.join(
    PROJECT_DIR, "docs", "components", "config-schema-object.ts"
)
MANUAL_QUEUE_JSON_TARGET = os.path.join(
    PROJECT_DIR, "docs", "components", "manual-queue-schema-object.ts"
)
sys.path.append(PROJECT_DIR)

from src import custom_types

config_schema_str = custom_types.Config.schema_json(indent=2)
dereferenced_config_schema = jsonref.loads(config_schema_str)
with open(CONFIG_JSON_TARGET, "w") as f:
    f.write(
        "/* prettier-ignore */\n"
        + "const CONFIG_SCHEMA_OBJECT: any = "
        + json.dumps(dereferenced_config_schema, indent=2)
        + ";\n\nexport default CONFIG_SCHEMA_OBJECT;"
    )

manual_queue_schema_str = custom_types.ManualQueue.schema_json(indent=2)
dereferenced_manual_queue_schema = jsonref.loads(manual_queue_schema_str)
with open(MANUAL_QUEUE_JSON_TARGET, "w") as f:
    f.write(
        "/* prettier-ignore */\n"
        + "const MANUAL_QUEUE_SCHEMA_OBJECT: any = "
        + json.dumps(dereferenced_manual_queue_schema, indent=2)
        + ";\n\nexport default MANUAL_QUEUE_SCHEMA_OBJECT;"
    )
