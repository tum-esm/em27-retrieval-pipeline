import os
import shutil
from src import custom_types, utils


def run(
    config: custom_types.Config,
    pylot_session: custom_types.PylotSession,
) -> None:
    # TODO: add switch to use either GGG2014 or GGG2020

    coordinates_slug = utils.functions.get_coordinates_slug(
        lat=pylot_session.ctx.location.lat, lon=pylot_session.ctx.location.lon
    )
    date_string = pylot_session.ctx.from_datetime.strftime("%Y%m%d")

    try:
        shutil.copy(
            os.path.join(
                config.general.data_src_dirs.vertical_profiles,
                "GGG2014",
                f"{date_string}_{coordinates_slug}.map",
            ),
            os.path.join(
                pylot_session.ctn.data_input_path,
                "map",
                f"{pylot_session.ctx.sensor_id}{date_string}.map",
            ),
        )
    except FileNotFoundError:
        raise AssertionError("map file does not exist")
