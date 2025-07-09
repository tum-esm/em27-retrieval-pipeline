import os
import shutil

from src import types, utils


def run(
    config: types.Config,
    session: types.RetrievalSession,
) -> None:
    coordinates_slug = utils.text.get_coordinates_slug(
        lat=session.ctx.atmospheric_profile_location.lat,
        lon=session.ctx.atmospheric_profile_location.lon,
    )
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")

    files_to_copy: list[tuple[str, str]] = []
    if session.atmospheric_profile_model == "GGG2014":
        files_to_copy = [
            (f"{date_string}_{coordinates_slug}.map", f"{session.ctx.sensor_id}{date_string}.map"),
        ]
    if session.atmospheric_profile_model == "GGG2020":
        files_to_copy = [
            (
                f"{date_string}{t:02d}_{coordinates_slug}.map",
                (
                    f"{session.ctx.sensor_id}_{coordinates_slug[:3]}_"
                    + f"{coordinates_slug[3:]}_{date_string}{t:02d}Z.map"
                ),
            )
            for t in range(0, 22, 3)
        ]
    try:
        for src, dst in files_to_copy:
            src_path_1 = os.path.join(
                config.general.data.atmospheric_profiles.root,
                session.atmospheric_profile_model,
                src,
            )
            src_path_2 = os.path.join(
                config.general.data.atmospheric_profiles.root,
                session.atmospheric_profile_model,
                src[:4],
                src[4:6],
                src,
            )
            dst_path = os.path.join(
                session.ctn.data_input_path,
                "map",
                dst,
            )
            if os.path.isfile(src_path_1):
                shutil.copy(src_path_1, dst_path)
            elif os.path.isfile(src_path_2):
                shutil.copy(src_path_2, dst_path)
            else:
                raise FileNotFoundError(f"File not found: {src_path_1} or {src_path_2}")
    except FileNotFoundError as e:
        raise AssertionError(f"map file does not exist: {e}")
