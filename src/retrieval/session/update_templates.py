import os
import tum_esm_utils
from src import types


def run(session: types.RetrievalSession) -> None:
    templates_path = os.path.join(
        session.ctn.container_path,
        "prfpylot",
        "templates",
    )
    for filename in os.listdir(templates_path):
        filepath = os.path.join(templates_path, filename)
        if os.path.isfile(filepath) and filename.endswith(".inp"):
            with open(filepath, "r") as f:
                template_content = f.read()
            new_template_content = tum_esm_utils.text.insert_replacements(
                template_content,
                {
                    "DC_MIN_THRESHOLD":
                        str(session.job_settings.dc_min_threshold),
                    "DC_VAR_THRESHOLD":
                        str(session.job_settings.dc_var_threshold),
                },
            )
            with open(filepath, "w") as f:
                f.write(new_template_content)
