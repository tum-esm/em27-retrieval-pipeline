from pydantic import BaseModel


class PylotContainer(BaseModel):
    container_id: str
    container_path: str
    data_input_path: str
    data_output_path: str
    pylot_config_path: str
    pylot_log_format_path: str
