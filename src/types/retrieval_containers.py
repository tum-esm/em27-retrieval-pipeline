import os
from typing import Literal, Optional

import em27_metadata
import pydantic
import tum_esm_utils

from .config import RetrievalJobSettingsConfig, RetrievalConfig, GeneralConfig


class RetrievalContainerBase(pydantic.BaseModel):
    container_dir: str = tum_esm_utils.files.rel_to_abs_path("../../data/containers")
    container_id: str

    @property
    def container_path(self) -> str:
        return os.path.join(
            self.container_dir,
            f"retrieval-container-{self.container_id}",
        )

    @property
    def data_input_path(self) -> str:
        return os.path.join(
            self.container_dir,
            f"retrieval-container-{self.container_id}-inputs",
        )

    @property
    def data_output_path(self) -> str:
        return os.path.join(
            self.container_dir,
            f"retrieval-container-{self.container_id}-outputs",
        )


class Proffast10Container(RetrievalContainerBase):
    pass


class Proffast22Container(RetrievalContainerBase):
    @property
    def pylot_config_path(self) -> str:
        return os.path.join(
            self.container_dir,
            f"retrieval-container-{self.container_id}-inputs",
            "pylot_config.yml",
        )

    @property
    def pylot_log_format_path(self) -> str:
        return os.path.join(
            self.container_dir,
            f"retrieval-container-{self.container_id}-inputs",
            "pylot_log_format.yml",
        )


class Proffast23Container(Proffast22Container):
    """No difference to `Proffast22Container`."""


class Proffast24Container(Proffast22Container):
    """No difference to `Proffast22Container`."""


class Proffast241Container(Proffast22Container):
    """No difference to `Proffast22Container`."""


RetrievalContainer = (
    Proffast10Container
    | Proffast22Container
    | Proffast23Container
    | Proffast24Container
    | Proffast241Container
)


class Proffast1RetrievalSession(pydantic.BaseModel):
    """This combines a `SensorDataContext` with a `Proffast10Container`"""

    retrieval_algorithm: Literal["proffast-1.0"] = "proffast-1.0"
    atmospheric_profile_model: Literal["GGG2014"] = "GGG2014"
    job_settings: RetrievalJobSettingsConfig
    ctx: em27_metadata.types.SensorDataContext
    ctn: Proffast10Container


class Proffast2RetrievalSession(pydantic.BaseModel):
    """This combines a `SensorDataContext` with a `Proffast22Container`/
    `Proffast23Container`/`Proffast24Container`/`Proffast24Container`"""

    retrieval_algorithm: Literal["proffast-2.2", "proffast-2.3", "proffast-2.4", "proffast-2.4.1"]
    atmospheric_profile_model: Literal["GGG2014", "GGG2020"]
    job_settings: RetrievalJobSettingsConfig
    ctx: em27_metadata.types.SensorDataContext
    ctn: Proffast22Container | Proffast23Container | Proffast24Container | Proffast241Container


RetrievalSession = Proffast1RetrievalSession | Proffast2RetrievalSession


class AboutRetrievalConfig(pydantic.BaseModel):
    general: GeneralConfig
    retrieval: RetrievalConfig


class AboutRetrieval(pydantic.BaseModel):
    automationVersion: str
    automationCommitSha: Optional[str]
    generationTime: str
    config: AboutRetrievalConfig
    session: RetrievalSession
