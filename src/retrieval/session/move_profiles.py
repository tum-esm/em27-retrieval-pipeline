import os
import shutil
from src import types, utils


def run(
    config: types.Config,
    session: types.RetrievalSession,
) -> None:
    coordinates_slug = utils.text.get_coordinates_slug(
        lat=session.ctx.location.lat, lon=session.ctx.location.lon
    )
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")

    files_to_copy: list[tuple[str, str]] = []
    if session.atmospheric_profile_model == "GGG2014":
        files_to_copy = [
            (
                f"{date_string}_{coordinates_slug}.map",
                f"{session.ctx.sensor_id}{date_string}.map"
            ),
        ]
    if session.atmospheric_profile_model == "GGG2020":
        files_to_copy = [(
            f"{date_string}{t}_{coordinates_slug}.map",
            f"{session.ctx.sensor_id}{date_string}{t}.map"
        ) for t in range(0, 22, 3)]
    try:
        for src, dst in files_to_copy:
            shutil.copy(
                os.path.join(
                    config.general.data.atmospheric_profiles.root,
                    session.atmospheric_profile_model,
                    src,
                ),
                os.path.join(
                    session.ctn.data_input_path,
                    "map",
                    dst,
                ),
            )
    except FileNotFoundError as e:
        raise AssertionError(f"map file does not exist: {e}")
