import os
import tum_esm_utils
from src import types, retrieval


def run(
    logger: retrieval.utils.logger.Logger,
    session: types.RetrievalSession,
) -> None:
    pcxs_pressure_value: float = 9999.9
    if session.job_settings.use_local_pressure_in_pcxs:
        logger.info("Computing mean pressure around solarnoon")
        solar_noon_datetime = retrieval.utils.pressure_averaging.compute_solar_noon_time(
            session.ctx.location.lat, session.ctx.location.lon,
            session.ctx.from_datetime.date()
        )
        logger.debug(f"Solar noon time: {solar_noon_datetime.time()} (UTC)")
        pcxs_pressure_value = retrieval.utils.pressure_averaging.compute_mean_pressure_around_noon(
            solar_noon_datetime,
            os.path.join(
                session.ctn.data_input_path,
                "log",
                (
                    f"datalogger-{session.ctx.pressure_data_source}-" +
                    f"{session.ctx.from_datetime.date().strftime('%Y%m%d')}.csv"
                ),
            ),
            logger,
        )

    logger.info(
        "Writing the following values to the templates: " +
        f"DC_MIN_THRESHOLD={session.job_settings.dc_min_threshold}, " +
        f"DC_VAR_THRESHOLD={session.job_settings.dc_var_threshold}, " +
        f"MEAN_PRESSURE_AT_NOON={pcxs_pressure_value}"
    )
    templates_path = os.path.join(
        session.ctn.container_path,
        "prfpylot",
        "templates",
    )
    for filename in os.listdir(templates_path):
        filepath = os.path.join(templates_path, filename)
        if os.path.isfile(filepath) and filename.endswith(".inp"):
            with open(filepath, "r") as f:
                template_content = f.read()
            new_template_content = tum_esm_utils.text.insert_replacements(
                template_content,
                {
                    "DC_MIN_THRESHOLD":
                        str(session.job_settings.dc_min_threshold),
                    "DC_VAR_THRESHOLD":
                        str(session.job_settings.dc_var_threshold),
                    "MEAN_PRESSURE_AT_NOON":
                        str(pcxs_pressure_value),
                },
            )
            with open(filepath, "w") as f:
                f.write(new_template_content)
