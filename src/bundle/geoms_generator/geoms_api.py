import math
from typing import Any, Callable, Literal, Optional
import h5py
import polars as pl
import pandas as pd
import numpy as np
import pydantic
from utils import geoms_times_to_datetime, datetimes_to_geoms_times


# fmt: off
class GEOMSColumnNames:
    SOURCE_PRODUCT =      "SOURCE.PRODUCT"
    DATETIME =            "DATETIME"
    ALTITUDE =            "ALTITUDE"
    SOLAR_ZENITH_ANGLE =  "ANGLE.SOLAR_ZENITH.ASTRONOMICAL"
    SOLAR_AZIMUTH_ANGLE = "ANGLE.SOLAR_AZIMUTH"

    INSTRUMENT_LAT =      "LATITUDE.INSTRUMENT"
    INSTRUMENT_LON =      "LONGITUDE.INSTRUMENT"
    INSTRUMENT_ALTITUDE = "ALTITUDE.INSTRUMENT"

    SURFACE_PRESSURE_INDEPENDENT =        "SURFACE.PRESSURE_INDEPENDENT"
    SURFACE_PRESSURE_INDEPENDENT_SOURCE = "SURFACE.PRESSURE_INDEPENDENT_SOURCE"
    PRESSURE_INDEPENDENT =                "PRESSURE_INDEPENDENT"
    PRESSURE_INDEPENDENT_SOURCE =         "PRESSURE_INDEPENDENT_SOURCE"
    TEMPERATURE_INDEPENDENT =             "TEMPERATURE_INDEPENDENT"
    TEMPERATURE_INDEPENDENT_SOURCE =      "TEMPERATURE_INDEPENDENT_SOURCE"

    AIR_COLUMN =         "DRY.AIR.COLUMN.PARTIAL_INDEPENDENT"
    AIR_DENSITY =        "DRY.AIR.NUMBER.DENSITY_INDEPENDENT"
    AIR_DENSITY_SOURCE = "DRY.AIR.NUMBER.DENSITY_INDEPENDENT_SOURCE"
    
    GAS_APRIOR:        Callable[[str], str] = lambda gas: f"{gas}.MIXING.RATIO.VOLUME.DRY_APRIORI"
    GAS_APRIOR_SOURCE: Callable[[str], str] = lambda gas: f"{gas}.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"
    GAS_COLUMN:        Callable[[str], str] = lambda gas: f"{gas}.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
    GAS_UNCERTAINTY:   Callable[[str], str] = lambda gas: f"{gas}.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
    GAS_AVK:           Callable[[str], str] = lambda gas: f"{gas}.COLUMN_ABSORPTION.SOLAR_AVK"

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
    VAR_FILL_VALUE: str = ""
    VAR_NAME: str
    VAR_NOTES: str = ""
    VAR_SIZE: str
    VAR_SI_CONVERSION: str = ""
    VAR_UNITS: str = ""
    VAR_VALID_MAX: str = ""
    VAR_VALID_MIN: str = ""
    _FillValue: str = ""


class GEOMSAPI:
    def _write_to_hdf5_file(
        hdf5_file: h5py.File,
        variable_name: np.array,
        data: Any,
        metadata: GEOMSAttributeMetadata | GEOMSSRCAttributeMetadata,
        dtype: Optional[Any] = None,
    ) -> None:
        """
        Helper method to write a dataset to the file.
        Params:
            data (np.array): The data to be stored
            dataset_name (string): The name of the dataset
            attributes (dict): The attributes to be stored
        """
        dataset = hdf5_file.create_dataset(variable_name, data=data, dtype=dtype)
        for keys, values in metadata.model_dump().items():
            if isinstance(values, str):
                dataset.attrs[keys] = np.bytes_(values)
            else:
                dataset.attrs[keys] = np.float64(values)
        return dataset

    @staticmethod
    def write_datetime(hdf5_file: h5py.File, julian_dates: list[float]) -> None:
        """Datetime information"""

        variable_name = GEOMSColumnNames.DATETIME
        data = [
            d / 86400.0
            for d in datetimes_to_geoms_times(
                geoms_times_to_datetime([(d - 2451544.5) * 86400.0 for d in julian_dates])
            )
        ]
        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="DOUBLE",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="MJD2K is 0.h0 on January 1, 2000 at 00:00:00 UTC",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;86400.0;s",
            VAR_UNITS="MJD2K",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="MJD2K",
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_altitude(hdf5_file: h5py.File, df: pd.DataFrame, ptf: pd.DataFrame) -> None:
        """Altitude information used in the a-priori profile matrix"""

        variable_name = GEOMSColumnNames.ALTITUDE
        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(ptf["Altitude"].shape[0]):
                data[i][j] = ptf["Altitude"][j] / 1000.0  # in km

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Altitude information used in the a-priori profile matrix",
            VAR_NAME=variable_name,
            VAR_NOTES="",
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.0E3;m",
            VAR_UNITS="km",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="km",
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_solar_angle_zenith(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Solar zenith angle"""

        variable_name = GEOMSColumnNames.SOLAR_ZENITH_ANGLE
        data = df["appSZA"].to_numpy()
        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="The solar astronomical zenith angle at which the measurement was taken",
            VAR_NAME=variable_name,
            VAR_NOTES="",
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.74533E-2;rad",
            VAR_UNITS="deg",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="deg",
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_solar_angle_azimuth(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Solar azimuth angle"""

        variable_name = GEOMSColumnNames.SOLAR_AZIMUTH_ANGLE
        data = df["azimuth"].to_numpy() + 180.0

        for i in range(len(data)):
            if data[i] <= 0.0 + 1.0e-5 or data[i] >= 360.0 - 1.0e-5:
                data[i] = 0.0 + 1.0e-5

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="The azimuth viewing direction of the sun using north as the reference plane and increasing clockwise (0 for north 90 for east and so on)",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.74533E-2;rad",
            VAR_UNITS="deg",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="deg",
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_instr_latitude(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Instrument latitude"""

        variable_name = GEOMSColumnNames.INSTRUMENT_LAT
        data = df["latdeg"].to_numpy()
        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Instrument geolocation (+ for north; - for south)",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.74533E-2;rad",
            VAR_UNITS="deg",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="deg",
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_instr_longitude(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Instrument longitude"""

        variable_name = GEOMSColumnNames.INSTRUMENT_LON
        data = df["londeg"].to_numpy()

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Instrument geolocation (+ for east; - for west)",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.74533E-2;rad",
            VAR_UNITS="deg",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="deg",
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_instrument_altitude(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Instrument altitude"""

        variable_name = GEOMSColumnNames.INSTRUMENT_ALTITUDE
        data = df["altim"].to_numpy()

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Instrument geolocation",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.0E3;m",
            VAR_UNITS="km",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="km",
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_surface_pressure(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Surface pressure"""

        variable_name = GEOMSColumnNames.SURFACE_PRESSURE_INDEPENDENT
        data = df["gndP"].to_numpy()

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Surface/ground pressure",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.0E2;kg m-1 s-2",
            VAR_UNITS="hPa",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="hPa",
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_surface_pressure_src(
        hdf5_file: h5py.File, df: pd.DataFrame, pressure_source_name: str
    ) -> None:
        """Source of the surface pressure"""

        variable_name = GEOMSColumnNames.SURFACE_PRESSURE_INDEPENDENT_SOURCE
        data_size = df["londeg"].to_numpy().size
        data = [pressure_source_name] * data_size

        metadata = GEOMSSRCAttributeMetadata(
            VAR_DATA_TYPE="STRING",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Surface pressure source (e.g. Mercury barometer etc.)",
            VAR_NAME=variable_name,
            VAR_SIZE=str(data_size),
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_pressure(hdf5_file: h5py.File, df: pd.DataFrame, ptf: pd.DataFrame) -> None:
        """Effective air pressure at each altitude"""

        variable_name = GEOMSColumnNames.PRESSURE_INDEPENDENT.value
        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(ptf["Altitude"].shape[0]):
                data[i][j] = ptf["Pre"][j] / 100.0  # hPa

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME;ALTITUDE",
            VAR_DESCRIPTION="Effective air pressure at each altitude",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.0E2;kg m-1 s-2",
            VAR_UNITS="hPa",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="hPa",
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_pressure_src(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Source of the effective air pressure"""

        variable_name = GEOMSColumnNames.PRESSURE_INDEPENDENT_SOURCE
        data = []

        for i in range(df["JulianDate"].shape[0]):
            data.append("Pressure profile from NCEP at local noon")

        metadata = GEOMSSRCAttributeMetadata(
            VAR_DATA_TYPE="STRING",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Pressure profile source (hydrostatic)",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.size(data)),
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_temperature(hdf5_file: h5py.File, df: pd.DataFrame, ptf: pd.DataFrame) -> None:
        """Effective air temperature"""

        variable_name = GEOMSColumnNames.TEMPERATURE_INDEPENDENT.value
        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(ptf["Altitude"].shape[0]):
                data[i][j] = ptf["Tem"][j]

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME;ALTITUDE",
            VAR_DESCRIPTION="Effective air temperature at each altitude",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.0;K",
            VAR_UNITS="K",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="K",
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_temperature_src(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Source of the effective air temperature"""

        variable_name = GEOMSColumnNames.TEMPERATURE_INDEPENDENT_SOURCE.value
        data = []
        for i in range(df["JulianDate"].shape[0]):
            data.append("Temperature profile from NCEP at local noon")

        metadata = GEOMSSRCAttributeMetadata(
            VAR_DATA_TYPE="STRING",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Temperature profile source (NCEP)",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.size(data)),
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_col(
        hdf5_file: h5py.File,
        df: pd.DataFrame,
        species: Literal["CO2", "CH4", "CO", "H2O"],
    ) -> None:
        """Column average dry air mole fraction"""

        variable_name = GEOMSColumnNames.GAS_COLUMN(species)
        unit: Literal["ppmv", "ppbv"]

        # Convert data to numpy array.
        if species == "H2O":
            data = df["XH2O"].to_numpy()
            unit = "ppmv"

        elif species == "CO2":
            data = df["XCO2"].to_numpy()
            unit = "ppmv"

        elif species == "CH4":
            data = df["XCH4"].to_numpy()
            unit = "ppmv"

        elif species == "CO":
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
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_column_uncertainty(
        hdf5_file: h5py.File,
        df: pd.DataFrame,
        species: Literal["CO2", "CH4", "CO", "H2O"],
    ) -> None:
        """Column average dry air mole fraction uncertainty"""

        variable_name = GEOMSColumnNames.GAS_UNCERTAINTY(species)
        data = np.zeros(df["JulianDate"].shape)

        # TODO: replace with correct call
        h2o_unc, co2_unc, ch4_unc, co_unc = self.get_col_unc(df)
        unit: Literal["ppmv", "ppbv"]

        if species == "H2O":
            data = h2o_unc
            unit = "ppmv"
        elif species == "CO2":
            data = co2_unc  # uncertainty for CO2
            unit = "ppmv"
        elif species == "CH4":
            data = ch4_unc  # uncertainty for CH4
            unit = "ppmv"
        elif species == "CO":
            data = co_unc  # uncertainty for CO
            unit = "ppbv"
        else:
            raise ValueError("Invalid variable_name")

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Total random uncertainty on the retrieved total column (expressed in same units as the column)",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.0E-9;1" if unit == "ppbv" else "0.0;1.0E-6;1",
            VAR_UNITS=unit,
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units=unit,
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_apriori(
        hdf5_file: h5py.File,
        df: pd.DataFrame,
        ptf: pd.DataFrame,
        vmr: pd.DataFrame,
        species: Literal["CO2", "CH4", "CO", "H2O"],
    ) -> None:
        """A-priori total vertical column of target gas"""

        variable_name = GEOMSColumnNames.GAS_APRIOR(species)
        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)
        unit: Literal["ppmv", "ppbv"]

        if species == "H2O":
            H2O_prior = ptf["H2O"]  # VMR prior for H2O
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = H2O_prior[j]  # in ppm
            unit = "ppmv"

        elif species == "CO2":
            CO2_prior = vmr["CO2"]  # VMR prior for CO2
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = CO2_prior[j]  # in ppm
            unit = "ppmv"

        elif species == "CH4":
            CH4_prior = vmr["CH4"] * 1000.0  # VMR prior for CH4
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = CH4_prior[j]  # in ppb
            unit = "ppbv"

        elif species == "CO":
            CO_prior = vmr["CO"] * 1000.0  # VMR prior for CO
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = CO_prior[j]  # in ppb
            unit = "ppbv"

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME;ALTITUDE",
            VAR_DESCRIPTION="A-priori total vertical column of target gas",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.0E-9;1" if unit == "ppbv" else "0.0;1.0E-6;1",
            VAR_UNITS=unit,
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units=unit,
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_apriori_src(
        hdf5_file: h5py.File,
        df: pd.DataFrame,
        species: Literal["CO2", "CH4", "CO", "H2O"],
        variant: Literal["GGG2014", "GGG2020"],
    ) -> None:
        """A-priori source of the vertical profile of a-priori per layer"""

        variable_name = GEOMSColumnNames.GAS_APRIOR_SOURCE(species)
        data = []
        for i in range(df["JulianDate"].shape[0]):
            if species == "H2O":
                data.append("Total vertical column of H2O from NCEP at local noon")
            else:
                data.append(f"Map file GFIT Code ({variant})")

        metadata = GEOMSSRCAttributeMetadata(
            VAR_DATA_TYPE="STRING",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Source of the vertical profile of a-priori per layer",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.size(data)),
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_avk(
        hdf5_file: h5py.File,
        df: pd.DataFrame,
        ptf: pd.DataFrame,
        sen: Any,
        species: Literal["CO2", "CH4", "CO", "H2O"],
    ) -> None:
        """Column sensitivities assosiated with the total vertical column"""

        variable_name = GEOMSColumnNames.GAS_AVK(species)
        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        if species == "H2O":
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = sen[0][i][j]  # 0: "CO2_int"

        elif species == "CO2":
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = sen[2][i][j]  # 1: "CH4_int"

        elif species == "CH4":
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = sen[3][i][j]  # 2: "CO_int"

        elif species == "CO":
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = sen[5][i][j]  # 3: "H2O_int"

        else:
            raise ValueError("Invalid species")

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME;ALTITUDE",
            VAR_DESCRIPTION="Column sensitivity associated with the total vertical column of the target gas",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.0;1",
            VAR_UNITS="1",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="1",
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_air_partial(hdf5_file: h5py.File, df: pd.DataFrame, ptf: pd.DataFrame) -> None:
        """Partial pressure of dry air"""

        variable_name = GEOMSColumnNames.AIR_COLUMN
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
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.66054E1;mol m-2",
            VAR_UNITS="Zmolec cm-2",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="Zmolec cm-2",
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_air_density(hdf5_file: h5py.File, df, ptf) -> None:
        """Dry air number density profile"""

        variable_name = GEOMSColumnNames.AIR_DENSITY
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
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.66054E-18;mol m-3",
            VAR_UNITS="molec cm-3",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
            units="molec cm-3",
            valid_range=[np.amin(data), np.amax(data)],
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    @staticmethod
    def write_air_density_src(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Source of the dry air number density profile"""

        variable_name = GEOMSColumnNames.AIR_DENSITY_SOURCE
        data = []
        for i in range(df["JulianDate"].shape[0]):
            data.append("Dry air number density profile from NCEP at local noon")
        metadata = GEOMSSRCAttributeMetadata(
            VAR_DATA_TYPE="STRING",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Dry air number density profile source (hydrostatic)",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.size(data)),
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)
