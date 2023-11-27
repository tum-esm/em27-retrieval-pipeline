import json
import os
import tum_esm_utils
import sys
import jsonref
import re

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)
CONFIG_JSON_TARGET = os.path.join(
    PROJECT_DIR, "docs", "components", "config-schema-object.ts"
)
MANUAL_QUEUE_JSON_TARGET = os.path.join(
    PROJECT_DIR, "docs", "components", "manual-queue-schema-object.ts"
)
MD_FILE_TARGET = os.path.join(
    PROJECT_DIR, "docs", "pages", "docs", "api-reference",
    "configuration-files.mdx"
)
sys.path.append(PROJECT_DIR)

from src import custom_types

# ---------------------------------------------------------
# Update the config schema object in the documentation

config_schema_str = custom_types.Config.schema_json(indent=2)
dereferenced_config_schema = jsonref.loads(config_schema_str)
with open(CONFIG_JSON_TARGET, "w") as f:
    f.write(
        "/* prettier-ignore */\n" + "const CONFIG_SCHEMA_OBJECT: any = " +
        json.dumps(dereferenced_config_schema, indent=2) +
        ";\n\nexport default CONFIG_SCHEMA_OBJECT;"
    )

# ---------------------------------------------------------
# Update the manual queue schema object in the documentation

manual_queue_schema_str = custom_types.ManualQueue.schema_json(indent=2)
dereferenced_manual_queue_schema = jsonref.loads(manual_queue_schema_str)
with open(MANUAL_QUEUE_JSON_TARGET, "w") as f:
    f.write(
        "/* prettier-ignore */\n" + "const MANUAL_QUEUE_SCHEMA_OBJECT: any = " +
        json.dumps(dereferenced_manual_queue_schema, indent=2) +
        ";\n\nexport default MANUAL_QUEUE_SCHEMA_OBJECT;"
    )

# ---------------------------------------------------------
# Update the example files in the documentation

with open(MD_FILE_TARGET) as f:
    md_file_content = f.read()

example_file_blocks = re.findall(
    r"Example File\n\n```[\s\S]*?```", md_file_content
)
assert len(example_file_blocks) == 2
assert len(example_file_blocks[0]) > len(example_file_blocks[1])

with open(os.path.join(PROJECT_DIR, "config", "config.template.json")) as f:
    config_template_content = f.read()

with open(
    os.path.join(PROJECT_DIR, "config", "manual-queue.template.json")
) as f:
    manual_queue_template_content = f.read()

assert len(config_template_content) > len(manual_queue_template_content)

md_file_content = md_file_content.replace(
    example_file_blocks[0],
    f"Example File\n\n```json\n{config_template_content.strip()}\n```",
)
md_file_content = md_file_content.replace(
    example_file_blocks[1],
    f"Example File\n\n```json\n{manual_queue_template_content.strip()}\n```",
)

with open(MD_FILE_TARGET, "w") as f:
    f.write(md_file_content)
