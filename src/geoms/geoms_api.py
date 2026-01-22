# pyright: basic
# type: ignore

"""Write data into GEOMS compliant HDF5 files.

This code has been adapted from the PROFFASTpylot (https://doi.org/10.21105/joss.06481)
which is licensed under the GNU General Public License version 3. The authors of the
original code are Lena Feld, Benedikt Herkommer, Darko Dubravica affiliated with the
Karlsruhe Institut of Technology (KIT)."""

from typing import Any, Callable, Literal
import math
import h5py
import pandas as pd
import numpy as np
import pydantic
from .utils import geoms_times_to_datetime, datetimes_to_geoms_times
import src


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


class GEOMSAPI:
    @staticmethod
    def _write_to_hdf5_file(
        hdf5_file: h5py.File,
        variable_name: str,
        data: Any,
        metadata: GEOMSAttributeMetadata | GEOMSSRCAttributeMetadata,
    ) -> None:
        """
        Helper method to write a dataset to the file.
        Params:
            data (np.array): The data to be stored
            dataset_name (string): The name of the dataset
            attributes (dict): The attributes to be stored
        """
        float_type = {
            "REAL": np.float32,
            "DOUBLE": np.float64,
            "STRING": np.bytes_,
        }[metadata.VAR_DATA_TYPE]
        dataset = hdf5_file.create_dataset(variable_name, data=np.array(data).astype(float_type))
        float_keys = [
            "VAR_FILL_VALUE",
            "VAR_VALID_MAX",
            "VAR_VALID_MIN",
            "_FillValue",
            "valid_range",
        ]
        metadata_dict = metadata.model_dump()
        metadata_dict["_FillValue"] = metadata.VAR_FILL_VALUE
        if isinstance(metadata, GEOMSAttributeMetadata):
            metadata_dict["units"] = metadata.VAR_UNITS
            metadata_dict["valid_range"] = [metadata.VAR_VALID_MIN, metadata.VAR_VALID_MAX]
        for key, value in metadata_dict.items():
            if key in float_keys:
                dataset.attrs[key] = float_type(value)
            else:
                dataset.attrs[key] = np.bytes_(value)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L705
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_source(hdf5_file: h5py.File) -> None:
        """Source information"""

        variable_name = GEOMSColumnNames.SOURCE_PRODUCT
        data = "Some Information."
        metadata = GEOMSSRCAttributeMetadata(
            VAR_DATA_TYPE="STRING",
            VAR_DEPEND="INDEPENDENT",
            VAR_DESCRIPTION="Information relevant to the source history of the Metadata and Data in the form Original_Archive;Original_Filename;Original_File_Generation_Date",
            VAR_NAME=variable_name,
            VAR_SIZE="1",
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L730
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_datetime(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Datetime information"""

        variable_name = GEOMSColumnNames.DATETIME
        data = [
            d / 86400.0
            for d in datetimes_to_geoms_times(
                geoms_times_to_datetime([(d - 2451544.5) * 86400.0 for d in df["JulianDate"]])
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
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L767
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_altitude(hdf5_file: h5py.File, df: pd.DataFrame, pt_df: pd.DataFrame) -> None:
        """Altitude information used in the a-priori profile matrix"""

        variable_name = GEOMSColumnNames.ALTITUDE
        data = np.zeros(df["JulianDate"].shape + pt_df["Altitude"].shape)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(pt_df["Altitude"].shape[0]):
                data[i][j] = pt_df["Altitude"][j] / 1000.0  # in km

        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME;ALTITUDE",
            VAR_DESCRIPTION="Altitude information used in the a-priori profile matrix",
            VAR_NAME=variable_name,
            VAR_NOTES="",
            VAR_SIZE=str(np.array(";".join(map(str, list(data.shape))))),
            VAR_SI_CONVERSION="0.0;1.0E3;m",
            VAR_UNITS="km",
            VAR_VALID_MAX=np.amax(data),
            VAR_VALID_MIN=np.amin(data),
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L802
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_solar_angle_zenith(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Solar zenith angle"""

        variable_name = GEOMSColumnNames.SOLAR_ZENITH_ANGLE
        data = df["sza"].to_numpy()
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
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L832
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_solar_angle_azimuth(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Solar azimuth angle"""

        variable_name = GEOMSColumnNames.SOLAR_AZIMUTH_ANGLE
        data = df["azi"].to_numpy() + 180.0

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
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L871
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_instrument_latitude(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Instrument latitude"""

        variable_name = GEOMSColumnNames.INSTRUMENT_LAT
        data = df["lat"].to_numpy()
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
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L900
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_instrument_longitude(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Instrument longitude"""

        variable_name = GEOMSColumnNames.INSTRUMENT_LON
        data = df["lon"].to_numpy()

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
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L929
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_instrument_altitude(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Instrument altitude"""

        variable_name = GEOMSColumnNames.INSTRUMENT_ALTITUDE
        data = df["alt"].to_numpy() / 1000

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
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L958
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_surface_pressure(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Surface pressure"""

        variable_name = GEOMSColumnNames.SURFACE_PRESSURE_INDEPENDENT
        data = df["ground_pressure"].to_numpy()

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
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L987
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_surface_pressure_source(
        hdf5_file: h5py.File, geoms_metadata: src.types.GEOMSMetadata, df: pd.DataFrame
    ) -> None:
        """Source of the surface pressure"""

        variable_name = GEOMSColumnNames.SURFACE_PRESSURE_INDEPENDENT_SOURCE
        data_size = df["lon"].to_numpy().size
        data = [geoms_metadata.general.pressure_sensor_name] * data_size

        metadata = GEOMSSRCAttributeMetadata(
            VAR_DATA_TYPE="STRING",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Surface pressure source (e.g. Mercury barometer etc.)",
            VAR_NAME=variable_name,
            VAR_SIZE=str(data_size),
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L1011
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_pressure(hdf5_file: h5py.File, df: pd.DataFrame, pt_df: pd.DataFrame) -> None:
        """Effective air pressure at each altitude"""

        variable_name = GEOMSColumnNames.PRESSURE_INDEPENDENT
        data = np.zeros(df["JulianDate"].shape + pt_df["Altitude"].shape)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(pt_df["Altitude"].shape[0]):
                data[i][j] = pt_df["Pre"][j] / 100.0  # hPa

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
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L1046
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_pressure_source(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
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

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L1071
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_temperature(hdf5_file: h5py.File, df: pd.DataFrame, pt_df: pd.DataFrame) -> None:
        """Effective air temperature"""

        variable_name = GEOMSColumnNames.TEMPERATURE_INDEPENDENT
        data = np.zeros(df["JulianDate"].shape + pt_df["Altitude"].shape)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(pt_df["Altitude"].shape[0]):
                data[i][j] = pt_df["Tem"][j]

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
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L1106
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_temperature_source(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
        """Source of the effective air temperature"""

        variable_name = GEOMSColumnNames.TEMPERATURE_INDEPENDENT_SOURCE
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

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L1131
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_column(
        hdf5_file: h5py.File,
        df: pd.DataFrame,
        species: Literal["CO2", "CH4", "CO", "H2O"],
    ) -> None:
        """Column average dry air mole fraction"""

        variable_name = GEOMSColumnNames.GAS_COLUMN(species)
        unit: Literal["ppmv", "ppbv"]

        # Convert data to numpy array.
        if species == "H2O":
            data = df["XH2O"].to_numpy(copy=True)
            data[data <= 0] = -900000.0  # default fill value
            unit = "ppmv"

        elif species == "CO2":
            data = df["XCO2"].to_numpy(copy=True)
            data[data <= 0] = -900000.0  # default fill value
            unit = "ppmv"

        elif species == "CH4":
            data = df["XCH4"].to_numpy(copy=True)
            data[data <= 0] = -900000.0  # default fill value
            unit = "ppmv"

        elif species == "CO":
            data = df["XCO"].to_numpy(copy=True) * 1000.0  # in ppbv
            data[data <= 0] = -900000.0  # default fill value
            unit = "ppbv"
        else:
            raise ValueError("Invalid variable_name")

        nonzero_data = data[data > 0]
        minval = 0
        maxval = 0
        if len(nonzero_data) > 0:
            minval = np.nanmin(nonzero_data)
            maxval = np.nanmax(nonzero_data)
        # print(f"{species}: min={minval}, max={maxval}")
        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Column average dry air mole fraction",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.size(data)),
            VAR_SI_CONVERSION="0.0;1.0E-9;1" if unit == "ppbv" else "0.0;1.0E-6;1",
            VAR_UNITS=unit,
            VAR_VALID_MIN=minval,
            VAR_VALID_MAX=maxval,
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L1183
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_column_uncertainty(
        hdf5_file: h5py.File,
        species: Literal["CO2", "CH4", "CO", "H2O"],
        column_uncertainty: np.ndarray[Any, Any],
    ) -> None:
        """Column average dry air mole fraction uncertainty"""

        variable_name = GEOMSColumnNames.GAS_UNCERTAINTY(species)

        unit: Literal["ppmv", "ppbv"]
        if species == "H2O":
            unit = "ppmv"
        elif species == "CO2":
            unit = "ppmv"
        elif species == "CH4":
            unit = "ppmv"
        elif species == "CO":
            column_uncertainty = column_uncertainty * 1000.0  # in ppbv
            unit = "ppbv"
        else:
            raise ValueError("Invalid variable_name")

        column_uncertainty[column_uncertainty <= 0] = -900000.0  # default fill value
        nonzero_values = column_uncertainty[column_uncertainty > 0]
        minval = 0
        maxval = 0
        if len(nonzero_values) > 0:
            minval = np.nanmin(nonzero_values)
            maxval = np.nanmax(nonzero_values)
        # print(f"{species} uncertainty: min={minval}, max={maxval}")
        metadata = GEOMSAttributeMetadata(
            VAR_DATA_TYPE="REAL",
            VAR_DEPEND="DATETIME",
            VAR_DESCRIPTION="Total random uncertainty on the retrieved total column (expressed in same units as the column)",
            VAR_NAME=variable_name,
            VAR_SIZE=str(np.size(column_uncertainty)),
            VAR_SI_CONVERSION="0.0;1.0E-9;1" if unit == "ppbv" else "0.0;1.0E-6;1",
            VAR_UNITS=unit,
            VAR_VALID_MIN=minval,
            VAR_VALID_MAX=maxval,
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, column_uncertainty, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L1247
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_apriori(
        hdf5_file: h5py.File,
        df: pd.DataFrame,
        pt_df: pd.DataFrame,
        vmr_df: pd.DataFrame,
        species: Literal["CO2", "CH4", "CO", "H2O"],
    ) -> None:
        """A-priori total vertical column of target gas"""

        variable_name = GEOMSColumnNames.GAS_APRIOR(species)
        data = np.zeros(df["JulianDate"].shape + pt_df["Altitude"].shape)
        unit: Literal["ppmv", "ppbv"]

        if species == "H2O":
            H2O_prior = pt_df["H2O"]  # VMR prior for H2O
            for i in range(df["JulianDate"].shape[0]):
                for j in range(pt_df["Altitude"].shape[0]):
                    data[i][j] = H2O_prior[j]  # in ppm
            unit = "ppmv"

        elif species == "CO2":
            CO2_prior = vmr_df["CO2"]  # VMR prior for CO2
            for i in range(df["JulianDate"].shape[0]):
                for j in range(pt_df["Altitude"].shape[0]):
                    data[i][j] = CO2_prior[j]  # in ppm
            unit = "ppmv"

        elif species == "CH4":
            CH4_prior = vmr_df["CH4"] * 1000.0  # VMR prior for CH4
            for i in range(df["JulianDate"].shape[0]):
                for j in range(pt_df["Altitude"].shape[0]):
                    data[i][j] = CH4_prior[j]  # in ppb
            unit = "ppbv"

        elif species == "CO":
            CO_prior = vmr_df["CO"] * 1000.0  # VMR prior for CO
            for i in range(df["JulianDate"].shape[0]):
                for j in range(pt_df["Altitude"].shape[0]):
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
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L1309
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_apriori_source(
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

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L1347
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_averaging_kernel(
        hdf5_file: h5py.File,
        df: pd.DataFrame,
        pt_df: pd.DataFrame,
        column_sensitivity: dict[str, list[list[float]]],
        species: Literal["CO2", "CH4", "CO", "H2O"],
    ) -> None:
        """Column sensitivities assosiated with the total vertical column"""

        variable_name = GEOMSColumnNames.GAS_AVK(species)
        data = np.zeros(df["JulianDate"].shape + pt_df["Altitude"].shape)

        # 0: H2O, 1: HDO, 2: CO2, 3: CO2_STR, 4: CH4, 5: CH4_S5P, 6: N2O, 7: CO, 8: O2, 9: HF
        if species == "H2O":
            for i in range(df["JulianDate"].shape[0]):
                for j in range(pt_df["Altitude"].shape[0]):
                    data[i][j] = column_sensitivity["H2O"][i][j]

        elif species == "CO2":
            for i in range(df["JulianDate"].shape[0]):
                for j in range(pt_df["Altitude"].shape[0]):
                    data[i][j] = column_sensitivity["CO2"][i][j]

        elif species == "CH4":
            for i in range(df["JulianDate"].shape[0]):
                for j in range(pt_df["Altitude"].shape[0]):
                    data[i][j] = column_sensitivity["CH4"][i][j]

        elif species == "CO":
            for i in range(df["JulianDate"].shape[0]):
                for j in range(pt_df["Altitude"].shape[0]):
                    data[i][j] = column_sensitivity["CO"][i][j]

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
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L1401
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_air_partial(hdf5_file: h5py.File, df: pd.DataFrame, pt_df: pd.DataFrame) -> None:
        """Partial pressure of dry air"""

        variable_name = GEOMSColumnNames.AIR_COLUMN
        data = np.zeros(df["JulianDate"].shape + pt_df["Altitude"].shape)

        k_B = 1.3807e-23  # 1.380649E-23 # k_boltz = 1.3807e-23

        T_prior = pt_df["Tem"]
        P_prior = pt_df["Pre"] / 100.0  # conversion Pa to hPa
        H2O_prior = pt_df["H2O"]  # / 10000.0 ???

        p_dry = P_prior * 1.0 / (1.0 + 1.0e-6 * H2O_prior)
        # / 100.0 for conversion Pa to hPa
        n_dry = p_dry / (k_B * T_prior)

        # Calcualtion of the vertical profile, i.e. the partial
        # columns of air number densities.
        # Each layer is obtained by an integration between two boundary layers.

        for i in range(df["JulianDate"].shape[0]):
            sum1 = 0.0
            sum2 = 0.0

            for j in range(pt_df["Altitude"].shape[0]):
                if j < len(pt_df["Altitude"]) - 1:
                    h1 = float(pt_df["Altitude"][j])
                    # * 1000.0 for conversion km to m
                    h2 = float(pt_df["Altitude"][j + 1])
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
                    sum2 += float(pt_df["DAC"][j])

                else:
                    data[i][j] = 0
                    # data[i][H_len-j] = 0
                    sum1 += data[i][j]
                    # sum1 += data[i][H_len-j]
                    sum2 += float(pt_df["DAC"][j])

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
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L1487
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_air_density(hdf5_file: h5py.File, df: pd.DataFrame, pt_df: pd.DataFrame) -> None:
        """Dry air number density profile"""

        variable_name = GEOMSColumnNames.AIR_DENSITY
        data = np.zeros(df["JulianDate"].shape + pt_df["Altitude"].shape)

        k_B = 1.3807e-23  # 1.380649E-23 # k_boltz = 1.3807e-23

        T_prior = pt_df["Tem"]
        P_prior = pt_df["Pre"] / 100.0  # conversion to hPa
        H2O_prior = pt_df["H2O"]  # / 10000.0 ???

        # Calculation of the dry air number density profile.

        p_dry = P_prior * 1.0 / (1.0 + 1.0e-6 * H2O_prior)
        # / 100.0 for conversion Pa to hPa
        n_dry = p_dry / (k_B * T_prior)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(pt_df["Altitude"].shape[0]):
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
        )
        GEOMSAPI._write_to_hdf5_file(hdf5_file, variable_name, data, metadata)

    # https://github.com/coccon/proffastpylot/blob/2.4.1-2/prfpylot/output/hdf_geoms_writer.py#L1537
    # identical to PROFFASTpylot 2.4.1-2
    @staticmethod
    def write_air_density_source(hdf5_file: h5py.File, df: pd.DataFrame) -> None:
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
