import os

import tum_esm_utils

from src import retrieval, types


def run(
    logger: "retrieval.utils.logger.Logger",
    session: types.RetrievalSession,
) -> None:
    pcxs_pressure_value: float = 9999.9
    if session.job_settings.use_local_pressure_in_pcxs:
        logger.info("Computing mean pressure around solarnoon")
        solar_noon_datetime = retrieval.utils.pressure_averaging.compute_solar_noon_time(
            session.ctx.location.lat, session.ctx.location.lon, session.ctx.from_datetime.date()
        )
        logger.debug(f"Solar noon time: {solar_noon_datetime.time()} (UTC)")
        date_string = session.ctx.from_datetime.date().strftime("%Y%m%d")

        pressure_calibration_factor = session.job_settings.pressure_calibration_factors.get(
            session.ctx.sensor_id, 1.0
        )
        pressure_calibration_offset = session.job_settings.pressure_calibration_offsets.get(
            session.ctx.sensor_id, 0.0
        )
        pcxs_pressure_value = (
            retrieval.utils.pressure_averaging.compute_mean_pressure_around_noon(
                solar_noon_datetime,
                os.path.join(
                    session.ctn.data_input_path,
                    "log",
                    f"ground-pressure-{session.ctx.pressure_data_source}-{date_string}.csv",
                ),
                logger,
            )
            * pressure_calibration_factor
            + pressure_calibration_offset
        )

    replacements = {
        "DC_MIN_THRESHOLD": str(session.job_settings.dc_min_threshold),
        "DC_VAR_THRESHOLD": str(session.job_settings.dc_var_threshold),
        "MEAN_PRESSURE_AT_NOON": str(pcxs_pressure_value),
    }
    if session.ctx.sensor_id in session.job_settings.custom_ils:
        logger.info("Using custom ILS values")
        ils = session.job_settings.custom_ils[session.ctx.sensor_id]
        replacements["ILS_Channel1"] = f"{ils.channel1_me} {ils.channel1_pe}"
        replacements["ILS_Channel2"] = f"{ils.channel2_me} {ils.channel2_pe}"

    logger.info(f"Writing values to templates: {replacements}")
    templates_path = os.path.join(session.ctn.container_path, "prfpylot", "templates")
    for filename in os.listdir(templates_path):
        filepath = os.path.join(templates_path, filename)
        if os.path.isfile(filepath) and filename.endswith(".inp"):
            with open(filepath, "r") as f:
                template_content = f.read()
            new_template_content = tum_esm_utils.text.insert_replacements(
                template_content, replacements
            )
            with open(filepath, "w") as f:
                f.write(new_template_content)
