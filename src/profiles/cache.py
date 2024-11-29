from __future__ import annotations

import datetime

import pydantic
import tum_esm_utils

from src import types

_CACHE_FILE = tum_esm_utils.files.rel_to_abs_path("../../data/profiles_query_cache.json")


class DownloadQueryCacheEntry(pydantic.BaseModel):
    atmospheric_profile_model: types.AtmosphericProfileModel
    download_query: types.DownloadQuery
    request_time: datetime.datetime


class DownloadQueryCache(pydantic.RootModel[list[DownloadQueryCacheEntry]]):
    root: list[DownloadQueryCacheEntry]

    @staticmethod
    def load() -> DownloadQueryCache:
        """Load the cache from disk."""

        try:
            with open(_CACHE_FILE, "r") as f:
                c = DownloadQueryCache.model_validate_json(f.read())
            return c
        except (FileNotFoundError, pydantic.ValidationError):
            return DownloadQueryCache(root=[])

    def dump(self) -> None:
        """Save the cache to disk."""

        with open(_CACHE_FILE, "w") as f:
            f.write(self.model_dump_json(indent=4))

    def get_active_queries(
        self,
        atmospheric_profile_model: types.AtmosphericProfileModel,
    ) -> list[types.DownloadQuery]:
        """Return all queries that are currently being processed for a given model."""

        return sorted(
            [
                e.download_query
                for e in self.root
                if e.atmospheric_profile_model == atmospheric_profile_model
            ],
            key=lambda q: q.from_date,
        )

    def get_timed_out_queries(
        self,
        atmospheric_profile_model: types.AtmosphericProfileModel,
    ) -> list[types.DownloadQuery]:
        """Returne all queries that have been issues more than 7 days ago."""

        return sorted(
            [
                e.download_query
                for e in self.root
                if (
                    (e.atmospheric_profile_model == atmospheric_profile_model)
                    and (e.request_time < (datetime.datetime.now() - datetime.timedelta(days=7)))
                )
            ],
            key=lambda q: q.from_date,
        )

    def add_query(
        self,
        atmospheric_profile_model: types.AtmosphericProfileModel,
        download_query: types.DownloadQuery,
    ) -> None:
        """Add a query to the cache."""

        self.root.append(
            DownloadQueryCacheEntry(
                atmospheric_profile_model=atmospheric_profile_model,
                download_query=download_query,
                request_time=datetime.datetime.now(),
            )
        )

    def remove_queries(
        self,
        atmospheric_profile_model: types.AtmosphericProfileModel,
        download_queries: list[types.DownloadQuery],
    ) -> None:
        """Remove queries from the cache."""

        self.root = [
            e
            for e in self.root
            if not (
                (e.download_query in download_queries)
                and (e.atmospheric_profile_model == atmospheric_profile_model)
            )
        ]
