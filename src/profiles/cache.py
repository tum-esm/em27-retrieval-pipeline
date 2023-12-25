from __future__ import annotations
import datetime
import pydantic
import tum_esm_utils
from src import profiles


class DownloadQueryCacheEntry(pydantic.BaseModel):
    location: profiles.generate_queries.ProfilesQueryLocation
    from_date: datetime.date
    to_date: datetime.date
    request_time: datetime.datetime


class DownloadQueryCache(pydantic.RootModel[list[DownloadQueryCacheEntry]]):
    root: list[DownloadQueryCacheEntry]

    @staticmethod
    def load() -> DownloadQueryCache:
        path = tum_esm_utils.files.rel_to_abs_path(
            "../../data/profiles_query_cache.json"
        )
        try:
            with open(path, "r") as f:
                c = DownloadQueryCache.model_validate_json(f.read())
            c.root = [
                e for e in c.root if (
                    e.request_time > datetime.datetime.now() -
                    datetime.timedelta(days=1)
                )
            ]
            return c
        except:
            return DownloadQueryCache(root=[])

    def dump(self) -> None:
        path = tum_esm_utils.files.rel_to_abs_path(
            "../../data/profiles_query_cache.json"
        )
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=4))

    def get_already_requested_dates(
        self, location: profiles.generate_queries.ProfilesQueryLocation
    ) -> set[datetime.date]:
        already_requested_dates: set[datetime.date] = set()
        for entry in self.root:
            if entry.location == location:
                already_requested_dates.update(
                    tum_esm_utils.time.date_range(
                        entry.from_date, entry.to_date
                    )
                )
        return already_requested_dates
