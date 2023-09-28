import os
import polars as pl
import pydantic
import datetime

_ILS_PARAMS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "ils-parameters.csv"
)


class ILSParams(pydantic.BaseModel):
    channel1_me: float
    channel1_pe: float
    channel2_me: float
    channel2_pe: float


def get_ils_params(serial_number: int, date: datetime.date) -> ILSParams:
    df = pl.read_csv(
        _ILS_PARAMS_PATH,
        columns=[
            "SERIAL_NUMBER",
            "CHANNEL1_ME",
            "CHANNEL1_PE",
            "CHANNEL2_ME",
            "CHANNEL2_PE",
            "VALID_SINCE",
        ],
        dtypes={
            "SERIAL_NUMBER": pl.Int32,
            "CHANNEL1_ME": pl.Float64,
            "CHANNEL1_PE": pl.Float64,
            "CHANNEL2_ME": pl.Float64,
            "CHANNEL2_PE": pl.Float64,
            "VALID_SINCE": pl.Date,
        },
    )

    df = df.filter(pl.col("SERIAL_NUMBER") == serial_number)
    df = df.filter(pl.col("VALID_SINCE") <= date)
    df = df.sort("VALID_SINCE", descending=True)

    assert len(df) > 0, f"No ILS parameters found for {serial_number} at {date}"

    return ILSParams(
        channel1_me=df["CHANNEL1_ME"][0],
        channel1_pe=df["CHANNEL1_PE"][0],
        channel2_me=df["CHANNEL2_ME"][0],
        channel2_pe=df["CHANNEL2_PE"][0],
    )