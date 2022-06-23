import os

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))


def write_pylot_config(pylot_slug: str):
    yaml_src = f"{PROJECT_DIR}/src/config/{pylot_slug}_config_template.yml"
    yaml_dst = f"{PROJECT_DIR}/example/{pylot_slug}_config.yml"
    with open(yaml_src, "r") as f:
        yaml_content = "".join(f.readlines())
    replacements = {
        "%PROJECT_DIR%/src": f"{PROJECT_DIR}/src",
        "%PROJECT_DIR%/inputs": f"{PROJECT_DIR}/example",
        "%PROJECT_DIR%/outputs": f"{PROJECT_DIR}/example/{pylot_slug}_outputs",
        "%SERIAL_NUMBER%": "115",
        "%SENSOR%": "mc",
        "%COORDINATES_LAT%": "48.148",
        "%COORDINATES_LON%": "16.438",
        "%COORDINATES_ALT%": "0.18",
    }
    for r_from, r_to in replacements.items():
        yaml_content = yaml_content.replace(r_from, r_to)
    with open(yaml_dst, "w") as f:
        f.write(yaml_content)

    return yaml_dst
