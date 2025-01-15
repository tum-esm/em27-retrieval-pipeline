import os
from typing import Optional
import h5py
import tum_esm_utils
import polars as pl
from src import types, bundle


MIN_SZA: float = 0
MIN_XAIR: Optional[float] = None
MAX_XAIR: Optional[float] = None
PARSE_DC_TIMESERIES: bool = True


class GEOMSWriter:
    @staticmethod
    def generate_geoms_file(results_folder: str) -> None:
        about = types.AboutRetrieval.model_validate_json(
            tum_esm_utils.files.load_json_file(os.path.join(results_folder, "about.json"))
        )
        sensor_id = about.session.ctx.sensor_id
        serial_number = about.session.ctx.serial_number
        from_dt, to_dt = about.session.ctx.from_datetime, about.session.ctx.to_datetime
        assert from_dt.date() == to_dt.date()
        label = from_dt.strftime("%Y%m%dT%H%M%S") + "-" + to_dt.strftime("%Y%m%dT%H%M%S")

        filename = f"geoms.groundbased_ftir.em27_tum_{sensor_id}_SN{serial_number:03d}_{label}.h5"
        filepath = os.path.join(results_folder, filename)
        hdf_file = h5py.File(filepath, "w")

        comb_invparms_df = GEOMSWriter.load_comb_invparms_df(results_folder, sensor_id)

    @staticmethod
    def load_comb_invparms_df(results_folder: str, sensor_id: str) -> pl.DataFrame:
        df = bundle.load_results.load_results_directory(
            results_folder, sensor_id, parse_dc_timeseries=PARSE_DC_TIMESERIES
        )

        # convert altim from m to km
        df = df.with_columns(pl.col("altim").div(1000).alias("altim"))

        # fill out of bounds values
        fill_value = -900_000
        for gas, max_value in [
            ("XCO2", 10_000),
            ("XCH4", 10),
            ("XCO", 10_000),
            ("XH2O", 10_000),
        ]:
            df = df.with_columns(
                pl.when(pl.col(gas).lt(0.0) | pl.col(gas).gt(max_value))
                .then(fill_value)
                .otherwise(pl.col(gas))
                .alias(gas)
            )

        # filter based on DC amplitude
        if PARSE_DC_TIMESERIES:
            df = df.with_columns(
                pl.col("ch1_fwd_dc_mean")
                .add(pl.col("ch1_bwd_dc_mean"))
                .mul(0.5)
                .ge(0.05)
                .alias("ch1_valid"),
                pl.col("ch2_fwd_dc_mean")
                .add(pl.col("ch2_bwd_dc_mean"))
                .mul(0.5)
                .ge(0.01)
                .alias("ch2_valid"),
            )
            df = df.with_columns(
                pl.when("ch1_valid").then(pl.col("XCO2")).otherwise(fill_value).alias("XCO2"),
                pl.when("ch1_valid").then(pl.col("XCH4")).otherwise(fill_value).alias("XCH4"),
                pl.when("ch1_valid").then(pl.col("XH2O")).otherwise(fill_value).alias("XH2O"),
                pl.when("ch2_valid").then(pl.col("XCO")).otherwise(fill_value).alias("XCO"),
            )
            df = df.filter(pl.col("ch1_valid") | pl.col("ch2_valid"))
            df = df.drop("ch1_valid", "ch2_valid")

        # filter based on SZA and XAIR
        if MIN_SZA is not None:
            df = df.filter(pl.col("appSZA").ge(MIN_SZA))
        if MIN_XAIR is not None:
            df = df.filter(pl.col("XAIR").ge(MIN_XAIR))
        if MAX_XAIR is not None:
            df = df.filter(pl.col("XAIR").le(MAX_XAIR))

        return df
