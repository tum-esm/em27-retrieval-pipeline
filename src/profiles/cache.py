from __future__ import annotations
import datetime
import pydantic
import tum_esm_utils
import src

_CACHE_FILE = tum_esm_utils.files.rel_to_abs_path(
    "../../data/profiles_query_cache.json"
)


class DownloadQueryCacheEntry(pydantic.BaseModel):
    atmospheric_profile_model: src.types.AtmosphericProfileModel
    download_query: src.types.DownloadQuery
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
                    e.request_time >
                    (datetime.datetime.now() - datetime.timedelta(days=1))
                )
            ]
            return c
        except (FileNotFoundError, pydantic.ValidationError):
            return DownloadQueryCache(root=[])

    def dump(self) -> None:
        with open(_CACHE_FILE, "w") as f:
            f.write(self.model_dump_json(indent=4))

    def get_active_queries(
        self,
        atmospheric_profile_model: src.types.AtmosphericProfileModel,
    ) -> list[src.types.DownloadQuery]:
        return sorted(
            [
                e.download_query for e in self.root
                if e.atmospheric_profile_model == atmospheric_profile_model
            ],
            key=lambda q: q.from_date,
        )

    def add_query(
        self,
        atmospheric_profile_model: src.types.AtmosphericProfileModel,
        download_query: src.types.DownloadQuery,
    ) -> None:
        self.root.append(
            DownloadQueryCacheEntry(
                atmospheric_profile_model=atmospheric_profile_model,
                download_query=download_query,
                request_time=datetime.datetime.now()
            )
        )

    def remove_queries(
        self,
        atmospheric_profile_model: src.types.AtmosphericProfileModel,
        download_queries: list[src.types.DownloadQuery],
    ) -> None:
        self.root = [
            e for e in self.root
            if not ((e.download_query in download_queries) and
                    (e.atmospheric_profile_model == atmospheric_profile_model))
        ]
