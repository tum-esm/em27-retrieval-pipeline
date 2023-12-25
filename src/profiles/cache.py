from __future__ import annotations
import datetime
import pydantic
import tum_esm_utils
from src import types

_CACHE_FILE = tum_esm_utils.files.rel_to_abs_path(
    "../../data/profiles_query_cache.json"
)


class DownloadQueryCacheEntry(pydantic.BaseModel):
    atmospheric_profile_model: types.AtmosphericProfileModel
    download_query: types.DownloadQuery
    request_time: datetime.datetime


class DownloadQueryCache(pydantic.RootModel[list[DownloadQueryCacheEntry]]):
    root: list[DownloadQueryCacheEntry]

    @staticmethod
    def load() -> DownloadQueryCache:
        try:
            with open(_CACHE_FILE, "r") as f:
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
        with open(_CACHE_FILE, "w") as f:
            f.write(self.model_dump_json(indent=4))

    """    def get_already_requested_dates(
        self,
        location: profiles.generate_queries.ProfilesQueryLocation,
    ) -> set[datetime.date]:
        already_requested_dates: set[datetime.date] = set()
        for entry in self.root:
            if entry.location == location:
                already_requested_dates.update(
                    tum_esm_utils.time.date_range(
                        entry.from_date, entry.to_date
                    )
                )
        return already_requested_dates"""

    def get_active_queries(
        self,
        atmospheric_profile_model: types.AtmosphericProfileModel,
    ) -> list[types.DownloadQuery]:
        return sorted(
            [
                e.download_query for e in self.root
                if e.atmospheric_profile_model == atmospheric_profile_model
            ],
            key=lambda q: q.from_date,
        )

    def add_queries(
        self,
        atmospheric_profile_model: types.AtmosphericProfileModel,
        download_queries: list[types.DownloadQuery],
    ) -> None:
        self.root.extend([
            DownloadQueryCacheEntry(
                atmospheric_profile_model=atmospheric_profile_model,
                download_query=q,
                request_time=datetime.datetime.now()
            ) for q in download_queries
        ])

    def remove_queries(
        self,
        atmospheric_profile_model: types.AtmosphericProfileModel,
        download_queries: list[types.DownloadQuery],
    ) -> None:
        self.root = [
            e for e in self.root
            if not ((e.download_query in download_queries) and
                    (e.atmospheric_profile_model == atmospheric_profile_model))
        ]
