import os
from typing import Literal
import pydantic
import em27_metadata
import tum_esm_utils

from src import types

_CONTAINERS_DIR = tum_esm_utils.files.rel_to_abs_path("../../data/containers")


class RetrievalContainerBase(pydantic.BaseModel):
    container_id: str

    @property
    def container_path(self) -> str:
        return os.path.join(
            _CONTAINERS_DIR,
            f"retrieval-container-{self.container_id}",
        )

    @property
    def data_input_path(self) -> str:
        return os.path.join(
            _CONTAINERS_DIR,
            f"retrieval-container-{self.container_id}-inputs",
        )

    @property
    def data_output_path(self) -> str:
        return os.path.join(
            _CONTAINERS_DIR,
            f"retrieval-container-{self.container_id}-outputs",
        )


class Proffast10Container(RetrievalContainerBase):
    pass


class Proffast22Container(RetrievalContainerBase):
    @property
    def pylot_config_path(self) -> str:
        return os.path.join(
            _CONTAINERS_DIR,
            f"retrieval-container-{self.container_id}-inputs",
            "pylot_config.yml",
        )

    @property
    def pylot_log_format_path(self) -> str:
        return os.path.join(
            _CONTAINERS_DIR,
            f"retrieval-container-{self.container_id}-inputs",
            "pylot_log_format.yml",
        )


class Proffast23Container(Proffast22Container):
    """No difference to `Proffast22Container`."""


RetrievalContainer = Proffast10Container | Proffast22Container | Proffast23Container


class Proffast1RetrievalSession(pydantic.BaseModel):
    """This combines a `SensorDataContext` with a `Proffast10Container`"""

    retrieval_algorithm: Literal["proffast-1.0"] = "proffast-1.0"
    atmospheric_profile_model: Literal["GGG2014"] = "GGG2014"
    ctx: em27_metadata.types.SensorDataContext
    ctn: Proffast10Container


class Proffast2RetrievalSession(pydantic.BaseModel):
    """This combines a `SensorDataContext` with a `Proffast22Container`/
    `Proffast23Container`."""

    retrieval_algorithm: Literal["proffast-2.2", "proffast-2.3"]
    atmospheric_profile_model: Literal["GGG2014", "GGG2020"]
    ctx: em27_metadata.types.SensorDataContext
    ctn: Proffast22Container | Proffast23Container


RetrievalSession = Proffast1RetrievalSession | Proffast2RetrievalSession
