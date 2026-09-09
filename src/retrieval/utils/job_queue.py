from typing import Optional

import em27_metadata
import pydantic

from src import types


class RetrievalJob(pydantic.BaseModel):
    sensor_data_context: em27_metadata.types.SensorDataContext
    job_config: types.RetrievalSubConfigs.Job


class RetrievalJobQueue:
    def __init__(self) -> None:
        self.queue: list[RetrievalJob] = []
        self.current_job_index: int = 0

    def push(
        self,
        sensor_data_context: em27_metadata.types.SensorDataContext,
        job_config: types.RetrievalSubConfigs.Job,
    ) -> None:
        self.queue.append(
            RetrievalJob(
                sensor_data_context=sensor_data_context,
                job_config=job_config,
            )
        )

    def peek(self) -> Optional[RetrievalJob]:
        if self.current_job_index < len(self.queue):
            return self.queue[self.current_job_index]
        else:
            return None

    def pop(self) -> Optional[RetrievalJob]:
        if self.current_job_index < len(self.queue):
            self.current_job_index += 1
            return self.queue[self.current_job_index - 1]
        else:
            return None

    def __len__(self) -> int:
        return len(self.queue) - self.current_job_index

    def is_empty(self) -> bool:
        return len(self) == 0
