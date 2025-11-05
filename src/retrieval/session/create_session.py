import datetime
import os

import em27_metadata
import tum_esm_utils

from src import retrieval, types

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=4)
_RETRIEVAL_ALGORITHMS_DIR = os.path.join(_PROJECT_DIR, "src", "retrieval", "algorithms")


def _generate_pylot2_config(session: types.Proffast2RetrievalSession) -> None:
    file_content = tum_esm_utils.files.load_file(
        os.path.join(
            _RETRIEVAL_ALGORITHMS_DIR,
            session.retrieval_algorithm,
            "config",
            "pylot_config_template.yml",
        )
    )
    tum_esm_utils.files.dump_file(
        session.ctn.pylot_config_path,
        tum_esm_utils.text.insert_replacements(
            file_content,
            {
                "SERIAL_NUMBER": str(session.ctx.serial_number).zfill(3),
                "SENSOR_ID": session.ctx.sensor_id,
                "COORDINATES_LAT": str(round(session.ctx.location.lat, 6)),
                "COORDINATES_LON": str(round(session.ctx.location.lon, 6)),
                "COORDINATES_ALT": str(round(session.ctx.location.alt / 1000.0, 6)),
                "UTC_OFFSET": str(round(session.ctx.utc_offset, 9)),
                "CONTAINER_ID": session.ctn.container_id,
                "CONTAINER_PATH": session.ctn.container_path,
                "DATA_INPUT_PATH": session.ctn.data_input_path,
                "DATA_OUTPUT_PATH": session.ctn.data_output_path,
                "PYLOT_LOG_FORMAT_PATH": session.ctn.pylot_log_format_path,
            },
        ),
    )


def _generate_pylot2_log_format(session: types.Proffast2RetrievalSession) -> None:
    file_content = tum_esm_utils.files.load_file(
        os.path.join(
            _RETRIEVAL_ALGORITHMS_DIR,
            session.retrieval_algorithm,
            "config",
            "pylot_log_format_template.yml",
        )
    )
    tum_esm_utils.files.dump_file(
        session.ctn.pylot_log_format_path,
        tum_esm_utils.text.insert_replacements(
            file_content,
            {
                "SENSOR_ID": session.ctx.sensor_id,
                "UTC_OFFSET": "0.0",
                "PRESSURE_DATA_SOURCE": session.ctx.pressure_data_source,
            },
        ),
    )


def run(
    container_factory: retrieval.dispatching.container_factory.ContainerFactory,
    sensor_data_context: em27_metadata.types.SensorDataContext,
    retrieval_algorithm: types.RetrievalAlgorithm,
    atmospheric_profile_model: types.AtmosphericProfileModel,
    job_settings: types.config.RetrievalJobSettingsConfig,
) -> types.RetrievalSession:
    """Create a new container and the pylot config files"""
    new_session: types.RetrievalSession

    if retrieval_algorithm == "proffast-1.0":
        new_session = types.Proffast1RetrievalSession(
            job_settings=job_settings,
            ctx=sensor_data_context,
            ctn=container_factory.create_container(retrieval_algorithm),  # pyright: ignore[reportArgumentType]
        )
    elif retrieval_algorithm in ["proffast-2.2", "proffast-2.3", "proffast-2.4", "proffast-2.4.1"]:
        new_session = types.Proffast2RetrievalSession(
            retrieval_algorithm=retrieval_algorithm,
            atmospheric_profile_model=atmospheric_profile_model,
            job_settings=job_settings,
            ctx=sensor_data_context,
            ctn=container_factory.create_container(retrieval_algorithm),  # pyright: ignore[reportArgumentType]
        )
        _generate_pylot2_config(new_session)
        _generate_pylot2_log_format(new_session)
    else:
        raise NotImplementedError(f"Retrieval algorithm {retrieval_algorithm} not implemented")

    retrieval.utils.retrieval_status.RetrievalStatusList.update_item(
        retrieval_algorithm=retrieval_algorithm,
        atmospheric_profile_model=atmospheric_profile_model,
        sensor_id=sensor_data_context.sensor_id,
        from_datetime=sensor_data_context.from_datetime,
        output_suffix=job_settings.output_suffix,
        container_id=new_session.ctn.container_id,
        process_start_time=datetime.datetime.now(datetime.timezone.utc),
    )
    return new_session
