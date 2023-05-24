import json
import os
import tum_esm_utils
import sys
import jsonref

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)
JSON_TARGET = os.path.join(PROJECT_DIR, "docs", "components", "config-schema-object.ts")
sys.path.append(PROJECT_DIR)

from src import custom_types

schema_str = custom_types.Config.schema_json(indent=2)
dereferenced_schema = jsonref.loads(schema_str)
with open(JSON_TARGET, "w") as f:
    f.write(
        "import ZodConfigType from './config-schema-type';\n\n"
        + "/* prettier-ignore */\n"
        + "const CONFIG_SCHEMA_OBJECT: ZodConfigType = "
        + json.dumps(dereferenced_schema, indent=2)
        + ";\n\nexport default CONFIG_SCHEMA_OBJECT;"
    )
