import os
import shutil
import src
from src import utils


def run(
    config: src.types.Config,
    session: src.types.RetrievalSession,
) -> None:
    coordinates_slug = utils.text.get_coordinates_slug(
        lat=session.ctx.atmospheric_profile_location.lat,
        lon=session.ctx.atmospheric_profile_location.lon
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
            f"{date_string}{t:02d}_{coordinates_slug}.map", (
                f"{session.ctx.sensor_id}_{coordinates_slug[:3]}_" +
                f"{coordinates_slug[3:]}_{date_string}{t:02d}Z.map"
            )
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
