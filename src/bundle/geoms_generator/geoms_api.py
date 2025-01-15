import math
from typing import Literal
import polars as pl
import pandas as pd
import numpy as np
import pydantic


# fmt: off
class GEOMSColumnNames:
    SOURCE_PRODUCT = "SOURCE.PRODUCT"
    DATETIME = "DATETIME"
    ALTITUDE = "ALTITUDE"
    SOLAR_ZENITH_ANGLE = "ANGLE.SOLAR_ZENITH.ASTRONOMICAL"
    SOLAR_AZIMUTH_ANGLE = "ANGLE.SOLAR_AZIMUTH"

    INSTRUMENT_LAT = "LATITUDE.INSTRUMENT"
    INSTRUMENT_LON = "LONGITUDE.INSTRUMENT"
    INSTRUMENT_ALTITUDE = "ALTITUDE.INSTRUMENT"

    SURFACE_PRESSURE_INDEPENDENT = "SURFACE.PRESSURE_INDEPENDENT"
    SURFACE_PRESSURE_INDEPENDENT_SOURCE = "SURFACE.PRESSURE_INDEPENDENT_SOURCE"
    PRESSURE_INDEPENDENT = "PRESSURE_INDEPENDENT"
    PRESSURE_INDEPENDENT_SOURCE = "PRESSURE_INDEPENDENT_SOURCE"
    TEMPERATURE_INDEPENDENT = "TEMPERATURE_INDEPENDENT"
    TEMPERATURE_INDEPENDENT_SOURCE = "TEMPERATURE_INDEPENDENT_SOURCE"

    AIR_COLUMN = "DRY.AIR.COLUMN.PARTIAL_INDEPENDENT"
    AIR_DENSITY = "DRY.AIR.NUMBER.DENSITY_INDEPENDENT"
    AIR_DENSITY_SOURCE = "DRY.AIR.NUMBER.DENSITY_INDEPENDENT_SOURCE"

    H2O_APRIORI = "H2O.MIXING.RATIO.VOLUME.DRY_APRIORI"
    H2O_APRIORI_SOURCE = "H2O.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"
    H2O_COLUMN = "H2O.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
    H2O_UNCERTAINTY = "H2O.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
    H2O_AVK = "H2O.COLUMN_ABSORPTION.SOLAR_AVK"

    CO2_APRIORI = "CO2.MIXING.RATIO.VOLUME.DRY_APRIORI"
    CO2_APRIORI_SOURCE = "CO2.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"
    CO2_COLUMN = "CO2.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
    CO2_UNCERTAINTY = "CO2.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
    CO2_AVK = "CO2.COLUMN_ABSORPTION.SOLAR_AVK"

    CH4_APRIORI = "CH4.MIXING.RATIO.VOLUME.DRY_APRIORI"
    CH4_APRIORI_SOURCE = "CH4.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"
    CH4_COLUMN = "CH4.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
    CH4_UNCERTAINTY = "CH4.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
    CH4_AVK = "CH4.COLUMN_ABSORPTION.SOLAR_AVK"

    CO_APRIORI = "CO.MIXING.RATIO.VOLUME.DRY_APRIORI"
    CO_APRIORI_SOURCE = "CO.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"
    CO_COLUMN = "CO.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
    CO_UNCERTAINTY = "CO.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
    CO_AVK = "CO.COLUMN_ABSORPTION.SOLAR_AVK"

# fmt: on


class GEOMSAttributeMetadata(pydantic.BaseModel):
    VAR_DATA_TYPE: Literal["REAL", "DOUBLE", "STRING"]
    VAR_DEPEND: str
    VAR_DESCRIPTION: str
    VAR_FILL_VALUE: float = -900000.0
    VAR_NAME: str
    VAR_NOTES: str = ""
    VAR_SIZE: str
    VAR_SI_CONVERSION: str
    VAR_UNITS: str
    VAR_VALID_MAX: float
    VAR_VALID_MIN: float
    _FillValue: float = -900000.0
    units: str
    valid_range: list[float] = pydantic.Field(..., min_length=2, max_length=2)


class GEOMSSRCAttributeMetadata(pydantic.BaseModel):
    VAR_DATA_TYPE: Literal["REAL", "DOUBLE", "STRING"]
    VAR_DEPEND: str
    VAR_DESCRIPTION: str
    VAR_FILL_VALUE: str | float = ""
    VAR_NAME: str
    VAR_NOTES: str = ""
    VAR_SIZE: str
    VAR_SI_CONVERSION: str = ""
    VAR_UNITS: str = ""
    VAR_VALID_MAX: str | float = ""
    VAR_VALID_MIN: str | float = ""
    _FillValue: str | float = ""


class GEOMSAPI:
    def write_datetime(self, df, variable_name: str = "DAT_TIM"):
        # "DAT_TIM": "DATETIME"

        # Write DateTime to the HDF5 file
        # (MJD2K is 0.0 on January 1, 2000 at 00:00:00 UTC).

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        datetime_notes = self.input_args["DATETIME_NOTES"]

        data = df["JulianDate"].to_numpy()

        data = self._GEOMStoDateTime((data - 2451544.5) * 86400.0)
        # data = self._GEOMStoDateTime(np.round((data - 2451544.5) * 86400.0))
        # ???
        data = self._DateTimeToGEOMS(data) / 86400.0

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="DOUBLE",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="MJD2K is 0.0 on January 1, 2000 at 00:00:00 UTC",
            VAR_NAME=dataset_name,
            VAR_NOTES=datetime_notes,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;86400.0;s",
            VAR_UNITS="MJD2K",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="MJD2K",
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset_dt(data, dataset_name, metadata)

    def write_altitude(self, df, ptf, variable_name: str = "ALT") -> None:
        # "ALT": "ALTITUDE"

        # Write altitude information used in the a-priori profile matrix.

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(ptf["Altitude"].shape[0]):
                data[i][j] = ptf["Altitude"][j] / 1000.0  # in km

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Altitude information used in the a-priori profile matrix",
            VAR_NAME=dataset_name,
            VAR_NOTES="",
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.0E3;m",
            VAR_UNITS="km",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="km",
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_solar_angle_zenith(self, df, variable_name: str = "SOL_ZEN") -> None:
        # "SOL_ZEN": "ANGLE.SOLAR_ZENITH.ASTRONOMICAL"

        # Write solar zenith angle to the HDF5 file
        # (solar astronomical zenith angle).

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = df["appSZA"].to_numpy()

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="The solar astronomical zenith angle at which the measurement was taken",
            VAR_NAME=dataset_name,
            VAR_NOTES="",
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.74533E-2;rad",
            VAR_UNITS="deg",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="deg",
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_solar_angle_azimuth(self, df, variable_name: str = "SOL_AZI") -> None:
        # "SOL_AZI": "ANGLE.SOLAR_AZIMUTH"

        # Write solar azimuth angle to the HDF5 file.

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = df["azimuth"].to_numpy() + 180.0

        # To avoid values lower than 0.0° or higher than 360.0°
        # causing an error message
        # in the quality checks of the HDF5 files, a small numer is
        # added or subtracted.

        for i in range(len(data)):
            if data[i] <= 0.0 + 1.0e-5 or data[i] >= 360.0 - 1.0e-5:
                data[i] = 0.0 + 1.0e-5

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="The azimuth viewing direction of the sun using north as the reference plane and increasing clockwise (0 for north 90 for east and so on)",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.74533E-2;rad",
            VAR_UNITS="deg",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="deg",
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_instr_latitude(self, df, variable_name: str = "INST_LAT") -> None:
        # "INST_LAT": "LATITUDE.INSTRUMENT"

        # Write the instrument's latitude to the HDF5 file
        # (i.e. the geolocation with + for north and - for south).

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = df["latdeg"].to_numpy()

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Instrument geolocation (+ for north; - for south)",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.74533E-2;rad",
            VAR_UNITS="deg",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="deg",
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_instr_longitude(self, df, variable_name: str = "INST_LON") -> None:
        # "INST_LON": "LONGITUDE.INSTRUMENT"

        # Write the instrument's longitude to the HDF5 file
        # (i.e. the geolocation with + for east and - for west).

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = df["londeg"].to_numpy()

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Instrument geolocation (+ for east; - for west)",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.74533E-2;rad",
            VAR_UNITS="deg",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="deg",
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_instr_altitude(self, df, variable_name: str = "INST_ALT") -> None:
        # "INST_ALT": "ALTITUDE.INSTRUMENT"

        # Write the instrument's altitude to the HDF5 file
        # (i.e. the geolocation).

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = df["altim"].to_numpy()

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Instrument geolocation",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.0E3;m",
            VAR_UNITS="km",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="km",
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_surface_pressure(self, df, variable_name: str = "SUR_IND") -> None:
        # "SUR_IND": "SURFACE.PRESSURE_INDEPENDENT"

        #  Write the surface pressure (i.e. the ground pressure)
        # to the HDF5 file.

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = df["gndP"].to_numpy()

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Surface/ground pressure",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.0E2;kg m-1 s-2",
            VAR_UNITS="hPa",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="hPa",
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_surface_pressure_src(self, df, variable_name: str = "SUR_SRC") -> None:
        # "SUR_SRC": "SURFACE.PRESSURE_INDEPENDENT_SOURCE"

        # Write the source of the surface pressure
        # (i.e. the ground pressure) to the HDF5 file.

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = df["londeg"].to_numpy()
        data_size = data.size
        data_src = [f"{self.input_args['PRESSURE_SOURCE']}"] * data_size

        metadata = GEOMSSRCAttributeMetadata(
            VAR_DATA_TYPE="STRING",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Surface pressure source (e.g. Mercury barometer etc.)",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(data_size),
        )

        self.SRC_dtst = self._write_dataset_src(data_src, dataset_name, metadata)

    def write_pressure(self, df, ptf, variable_name: str = "PRE_IND") -> None:
        # "PRE_IND": "PRESSURE_INDEPENDENT"

        # Write the effective air pressure at each
        # altitude level to the HDF5 file.

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(ptf["Altitude"].shape[0]):
                data[i][j] = ptf["Pre"][j] / 100.0  # hPa

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME;ALTITUDE",
            VAR_DESCRIPTION="Effective air pressure at each altitude",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.0E2;kg m-1 s-2",
            VAR_UNITS="hPa",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="hPa",
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_pressure_src(self, df, variable_name: str = "PRE_SRC") -> None:
        # "PRE_SRC": "PRESSURE_INDEPENDENT_SOURCE"

        # Write the source of the effective air pressure
        # for each altitude to the HDf5 file.

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data_src = []

        for i in range(df["JulianDate"].shape[0]):
            data_src.append("Pressure profile from NCEP at local noon")

        metadata = GEOMSSRCAttributeMetadata(
            VAR_DATA_TYPE="STRING",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Pressure profile source (hydrostatic)",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.size(data_src)),
        )

        self.SRC_dtst = self._write_dataset_src(data_src, dataset_name, metadata)

    def write_temperature(self, df, ptf, variable_name: str = "TEM_IND") -> None:
        # "TEM_IND": "TEMPERATURE_INDEPENDENT"

        # Write the effective air temperature at each
        # altitude to the HDF5 file.

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(ptf["Altitude"].shape[0]):
                data[i][j] = ptf["Tem"][j]

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME;ALTITUDE",
            VAR_DESCRIPTION="Effective air temperature at each altitude",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.0;K",
            VAR_UNITS="K",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="K",
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_temperature_src(self, df, variable_name: str = "TEM_SRC") -> None:
        # "TEM_SRC": "TEMPERATURE_INDEPENDENT_SOURCE"

        # Write the source of the effective air pressure for
        # each altitude to the HDF5 file.

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data_src = []

        for i in range(df["JulianDate"].shape[0]):
            data_src.append("Temperature profile from NCEP at local noon")

        self.hdf5_atts_src["VAR_DATA_TYPE"] = "STRING"
        self.hdf5_atts_src["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts_src["VAR_DESCRIPTION"] = (
            "Temperature profile source (e.g. Lidar NCEP Sonde ECMWF etc.)"
        )
        self.hdf5_atts_src["VAR_NAME"] = dataset_name
        # self.hdf5_atts_src["VAR_NOTES"] = ""
        self.hdf5_atts_src["VAR_SIZE"] = str(np.size(data_src))

        self.SRC_dtst = self._write_dataset_src(data_src, dataset_name, self.hdf5_atts_src)

    def write_col(
        self,
        df,
        variable_name: Literal["CO2_COL", "CH4_COL", "CO_COL", "H2O_COL"],
    ) -> None:
        # "XXX_COL": "XXX.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"

        # Write column average dry air mole fractions for
        # each trace gas to HDF5 file.

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        unit: Literal["ppmv", "ppbv"]

        # Convert data to numpy array.
        if variable_name == "H2O_COL":
            # "H2O_COL": "H2O.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
            data = df["XH2O"].to_numpy()
            unit = "ppmv"
        elif variable_name == "CO2_COL":
            # "CO2_COL": "CO2.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
            data = df["XCO2"].to_numpy()
            unit = "ppmv"
        elif variable_name == "CH4_COL":
            # "CH4_COL": "CH4.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
            data = df["XCH4"].to_numpy()
            unit = "ppmv"
        elif variable_name == "CO_COL":
            # "CO_COL":  "CO.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
            data = df["XCO"].to_numpy() * 1000.0  # in ppbv
            data[data < 0] = -900000.0  # default fill value
            unit = "ppbv"
        else:
            raise ValueError("Invalid variable_name")

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Column average dry air mole fraction",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.0E-9;1" if unit == "ppbv" else "0.0;1.0E-6;1",
            VAR_UNITS=unit,
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units=unit,
            valid_range=[np.amin(data), np.amax(data)],
        )
        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_col_unc(
        self,
        df,
        variable_name: Literal["CO2_UNC", "CH4_UNC", "CO_UNC", "H2O_UNC"],
    ) -> None:
        # "XXX_UNC":
        # "XXX.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"

        # Write uncertainty on the retrieved total column
        # for each trace gas to HDF5 file.

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape)

        h2o_unc, co2_unc, ch4_unc, co_unc = self.get_col_unc(df)
        unit: Literal["ppmv", "ppbv"]

        if variable_name == "H2O_UNC":
            # "H2O_UNC":
            # "H2O.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
            data = h2o_unc
            unit = "ppmv"
        elif variable_name == "CO2_UNC":
            # "CO2_UNC":
            # "CO2.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
            data = co2_unc  # uncertainty for CO2
            unit = "ppmv"
        elif variable_name == "CH4_UNC":
            # "CH4_UNC":
            # "CH4.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
            data = ch4_unc  # uncertainty for CH4
            unit = "ppmv"
        elif variable_name == "CO_UNC":
            # "CO_UNC":
            # "CO.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
            data = co_unc  # uncertainty for CO
            unit = "ppbv"
        else:
            raise ValueError("Invalid variable_name")

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Total random uncertainty on the retrieved total column (expressed in same units as the column)",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.0E-9;1" if unit == "ppbv" else "0.0;1.0E-6;1",
            VAR_UNITS=unit,
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units=unit,
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_apr(
        self,
        df,
        ptf,
        vmr,
        variable_name: Literal["CO2_APR", "CH4_APR", "CO_APR", "H2O_APR"],
    ) -> None:
        """Write prior total vertical column for each trace gas to the HDF5 file.
        "XXX_APR": "XXX.MIXING.RATIO.VOLUME.DRY_APRIORI"""
        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        unit: Literal["ppmv", "ppbv"]

        if variable_name == "H2O_APR":
            # "H2O_APR": "H2O.MIXING.RATIO.VOLUME.DRY_APRIORI"
            H2O_prior = ptf["H2O"]  # VMR prior for H2O
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = H2O_prior[j]  # in ppm
            unit = "ppmv"
        elif variable_name == "CO2_APR":
            # "CO2_APR": "CO2.MIXING.RATIO.VOLUME.DRY_APRIORI"
            CO2_prior = vmr["CO2"]  # VMR prior for CO2
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = CO2_prior[j]  # in ppm
            unit = "ppmv"
        elif variable_name == "CH4_APR":
            # "CH4_APR": "CH4.MIXING.RATIO.VOLUME.DRY_APRIORI"
            CH4_prior = vmr["CH4"] * 1000.0  # VMR prior for CH4
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = CH4_prior[j]  # in ppb
            unit = "ppbv"
        elif variable_name == "CO_APR":
            # "CO_APR": "CO.MIXING.RATIO.VOLUME.DRY_APRIORI"
            CO_prior = vmr["CO"] * 1000.0  # VMR prior for CO
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = CO_prior[j]  # in ppb
            unit = "ppbv"

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME;ALTITUDE",
            VAR_DESCRIPTION="A-priori total vertical column of target gas",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.0E-9;1" if unit == "ppbv" else "0.0;1.0E-6;1",
            VAR_UNITS=unit,
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units=unit,
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_apr_src(
        self,
        df,
        variable_name: Literal["CO2_SRC", "CH4_SRC", "CO_SRC", "H2O_SRC"],
    ) -> None:
        # "XXX_SRC": "XXX.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"

        # Write source of the a-prior total vertical column for each
        # trace gas to the HDF5 file.

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data_src = []
        ggg_ver = self.input_args["APRIORI_SOURCE"]

        for i in range(df["JulianDate"].shape[0]):
            if variable_name == "H2O_SRC":
                # "H2O_SRC": "H2O.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"
                data_src.append("Total vertical column of H2O from NCEP at local noon")
            elif variable_name == "CO2_SRC":
                # "CO2_SRC": "CO2.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"
                data_src.append("Map file GFIT Code ({})".format(ggg_ver))
            elif variable_name == "CH4_SRC":
                # "CH4_SRC": "CH4.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"
                data_src.append("Map file GFIT Code ({})".format(ggg_ver))
            elif variable_name == "CO_SRC":
                # "CO_SRC":  "CO.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"
                data_src.append("Map file GFIT Code ({})".format(ggg_ver))

        metadata = GEOMSSRCAttributeMetadata(
            VAR_DATA_TYPE="STRING",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Source of the vertical profile of a-priori per layer",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.size(data_src)),
        )
        self.SRC_dtst = self._write_dataset_src(data_src, dataset_name, metadata)

    def write_avk(
        self,
        df: pl.DataFrame | pd.DataFrame,
        ptf,
        sen,
        variable_name: Literal["CO2_AVK", "CH4_AVK", "CO_AVK", "H2O_AVK"],
    ) -> None:
        # "XXX_AVK": "XXX.COLUMN_ABSORPTION.SOLAR_AVK"

        # Write column sensitivities assosiated with the total vertical column
        # for each trace gas to the HDF5 file.

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        if variable_name == "H2O_AVK":
            # "H2O_APR": "H2O.MIXING.RATIO.VOLUME.DRY_APRIORI"
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = sen[0][i][j]  # 0: "CO2_int"
        elif variable_name == "CO2_AVK":
            # "CO2_APR": "CO2.MIXING.RATIO.VOLUME.DRY_APRIORI"
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = sen[2][i][j]  # 1: "CH4_int"
        elif variable_name == "CH4_AVK":
            # "CH4_APR": "CH4.MIXING.RATIO.VOLUME.DRY_APRIOR"
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = sen[3][i][j]  # 2: "CO_int"
        elif variable_name == "CO_AVK":
            # "CO_APR": "CO.MIXING.RATIO.VOLUME.DRY_APRIORI"
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = sen[5][i][j]  # 3: "H2O_int"

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME;ALTITUDE",
            VAR_DESCRIPTION="Column sensitivity associated with the total vertical column of the target gas",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.0;1",
            VAR_UNITS="1",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="1",
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_air_partial(self, df, ptf, variable_name: str = "AIR_COL") -> None:
        # "AIR_COL": "DRY.AIR.COLUMN.PARTIAL_INDEPENDENT"

        # Write vertical profile of partial columns of air number densities
        # (for conversion between VMR and partial column profile).
        # 0: "Index", 1: "Altitude", 2: "Tem", 3: "Pre", 4: "DAC",
        # 5: "H2O", 6: "HDO"
        # 0: "Index", 1: "Altitude", 2: "Temperature", 3: "Pressure",
        # 4: "Column", 5: "H2O", 6: "HDO"

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        k_B = 1.3807e-23  # 1.380649E-23 # k_boltz = 1.3807e-23

        T_prior = ptf["Tem"]
        P_prior = ptf["Pre"] / 100.0  # conversion Pa to hPa
        H2O_prior = ptf["H2O"]  # / 10000.0 ???

        p_dry = P_prior * 1.0 / (1.0 + 1.0e-6 * H2O_prior)
        # / 100.0 for conversion Pa to hPa
        n_dry = p_dry / (k_B * T_prior)

        # Calcualtion of the vertical profile, i.e. the partial
        # columns of air number densities.
        # Each layer is obtained by an integration between two boundary layers.

        for i in range(df["JulianDate"].shape[0]):
            sum1 = 0.0
            sum2 = 0.0

            for j in range(ptf["Altitude"].shape[0]):
                if j < len(ptf["Altitude"]) - 1:
                    h1 = float(ptf["Altitude"][j])
                    # * 1000.0 for conversion km to m
                    h2 = float(ptf["Altitude"][j + 1])
                    # * 1000.0 for conversion km to m

                    n1_dry = float(n_dry[j])
                    n2_dry = float(n_dry[j + 1])
                    sc_dry = (h2 - h1) / math.log(n1_dry / n2_dry)
                    n0_dry = n1_dry * math.exp(h1 / sc_dry)

                    Col1 = n0_dry * sc_dry * math.exp(-(h1 / sc_dry))
                    Col2 = n0_dry * sc_dry * math.exp(-(h2 / sc_dry))

                    data[i][j] = 100.0 * (Col1 - Col2)
                    # data[i][H_len-j] = 100.0 * (Col1 - Col2)

                    sum1 += data[i][j]
                    # sum1 += data[i][H_len-j]
                    sum2 += float(ptf["DAC"][j])

                else:
                    data[i][j] = 0
                    # data[i][H_len-j] = 0
                    sum1 += data[i][j]
                    # sum1 += data[i][H_len-j]
                    sum2 += float(ptf["DAC"][j])

        data = data / 1.0e25

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME;ALTITUDE",
            VAR_DESCRIPTION="Vertical profile of partial columns of air number densities (for conversion between VMR and partial column profile)",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.66054E1;mol m-2",
            VAR_UNITS="Zmolec cm-2",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="Zmolec cm-2",
            valid_range=[np.amin(data), np.amax(data)],
        )

        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_air_density(self, df, ptf, variable_name: str = "AIR_DEN") -> None:
        # "AIR_DEN": "DRY.AIR.NUMBER.DENSITY_INDEPENDENT"

        # Write the dry air number density profile to the HDF5 file.
        # 0: "Index", 1: "Altitude", 2: "Tem", 3: "Pre", 4: "DAC", 5:
        # "H2O", 6: "HDO"
        # 0: "Index", 1: "Altitude", 2: "Temperature", 3: "Pressure",
        # 4: "Column", 5: "H2O", 6: "HDO"

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        k_B = 1.3807e-23  # 1.380649E-23 # k_boltz = 1.3807e-23

        T_prior = ptf["Tem"]
        P_prior = ptf["Pre"] / 100.0  # conversion to hPa
        H2O_prior = ptf["H2O"]  # / 10000.0 ???

        # Calculation of the dry air number density profile.

        p_dry = P_prior * 1.0 / (1.0 + 1.0e-6 * H2O_prior)
        # / 100.0 for conversion Pa to hPa
        n_dry = p_dry / (k_B * T_prior)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(ptf["Altitude"].shape[0]):
                data[i][j] = n_dry[j]

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME;ALTITUDE",
            VAR_DESCRIPTION="Dry air number density profile",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.66054E-18;mol m-3",
            VAR_UNITS="molec cm-3",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="molec cm-3",
            valid_range=[np.amin(data), np.amax(data)],
        )
        self.SRC_dtst = self._write_dataset(data, dataset_name, metadata)

    def write_air_density_src(self, df, variable_name: str = "AIR_SRC") -> None:
        # "AIR_SRC": "DRY.AIR.NUMBER.DENSITY_INDEPENDENT_SOURCE"

        # Write source of the dry air number density profile
        # (hydrostatic) to the HDF5 file.

        dataset_name = self.hdf5_vars[variable_name]
        self.variables.append(dataset_name)

        data_src = []

        for i in range(df["JulianDate"].shape[0]):
            data_src.append("Dry air number density profile from NCEP at local noon")

        metadata = GEOMSSRCAttributeMetadata(
            VAR_DATA_TYPE="STRING",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Dry air number density profile source (hydrostatic)",
            VAR_NAME=dataset_name,
            VAR_SIZE=str(np.size(data_src)),
        )
        self.SRC_dtst = self._write_dataset_src(data_src, dataset_name, metadata)
