from typing import Literal
import pytest
import datetime

from src import profiles
from src.utils import utils
from tests.fixtures import provide_config_template


@pytest.mark.order(1)
@pytest.mark.ci_quick
@pytest.mark.ci_intensive
@pytest.mark.ci_complete
def test_get_date_suffixes(
    provide_config_template: utils.config.Config
) -> None:
    global_config = provide_config_template
    assert global_config.profiles is not None

    def call(
        config: utils.config.Config,
        query: utils.types.DownloadQuery,
        version: Literal["GGG2014", "GGG2020"],
    ) -> list[str]:
        return profiles.transfer_logic.get_date_suffixes(
            config,
            query,
            version,
            get_current_datetime=lambda: datetime.datetime(2000, 1, 10),
        )

    queries = [
        utils.types.DownloadQuery(
            from_date="2000-01-01", to_date="2000-01-01", lat=0, lon=0
        ),
        utils.types.DownloadQuery(
            from_date="2000-01-01", to_date="2000-01-03", lat=0, lon=0
        ),
        utils.types.DownloadQuery(
            from_date="2000-01-01", to_date="2000-01-04", lat=0, lon=0
        ),
        utils.types.DownloadQuery(
            from_date="2000-01-03", to_date="2000-01-06", lat=0, lon=0
        ),
        utils.types.DownloadQuery(
            from_date="2000-01-05", to_date="2000-01-06", lat=0, lon=0
        ),
    ]

    versions: list[Literal["GGG2014", "GGG2020"]] = ["GGG2014", "GGG2020"]
    max_days_delays: list[Literal[5, 7]] = [5, 7]

    # ex_re[max_days_delay][version][query_index]
    expected_responses: dict[Literal[5, 7],
                             dict[Literal["GGG2014", "GGG2020"],
                                  list[list[str]]]] = {
                                      5: {
                                          "GGG2014": [
                                              ["20000101_20000101"],
                                              ["20000101_20000103"],
                                              ["20000101_20000104"],
                                              [
                                                  "20000103_20000106",
                                                  "20000103_20000105",
                                                  "20000103_20000104"
                                              ],
                                              [
                                                  "20000105_20000106",
                                                  "20000105_20000105"
                                              ],
                                          ],
                                          "GGG2020": [
                                              ["20000101-20000102"],
                                              ["20000101-20000104"],
                                              ["20000101-20000105"],
                                              [
                                                  "20000103-20000107",
                                                  "20000103-20000106",
                                                  "20000103-20000105"
                                              ],
                                              [
                                                  "20000105-20000107",
                                                  "20000105-20000106"
                                              ],
                                          ],
                                      },
                                      7: {
                                          "GGG2014": [
                                              ["20000101_20000101"],
                                              [
                                                  "20000101_20000103",
                                                  "20000101_20000102"
                                              ],
                                              [
                                                  "20000101_20000104",
                                                  "20000101_20000103",
                                                  "20000101_20000102"
                                              ],
                                              [
                                                  "20000103_20000106",
                                                  "20000103_20000105",
                                                  "20000103_20000104",
                                                  "20000103_20000103",
                                              ],
                                              [
                                                  "20000105_20000106",
                                                  "20000105_20000105"
                                              ],
                                          ],
                                          "GGG2020": [
                                              ["20000101-20000102"],
                                              [
                                                  "20000101-20000104",
                                                  "20000101-20000103"
                                              ],
                                              [
                                                  "20000101-20000105",
                                                  "20000101-20000104",
                                                  "20000101-20000103"
                                              ],
                                              [
                                                  "20000103-20000107",
                                                  "20000103-20000106",
                                                  "20000103-20000105",
                                                  "20000103-20000104",
                                              ],
                                              [
                                                  "20000105-20000107",
                                                  "20000105-20000106"
                                              ],
                                          ],
                                      },
                                  }

    # careful: GGG2020 modifies the to_date
    for version in versions:
        for i, query in enumerate(queries):
            for max_days_delay in max_days_delays:
                global_config.profiles.ftp_server.max_day_delay = (
                    max_days_delay
                )
                print("trying", max_days_delay, version, i)
                print("  query", query)
                assert expected_responses[max_days_delay][version][i] == call(
                    global_config, query, version
                )
