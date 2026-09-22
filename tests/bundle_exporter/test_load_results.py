from pathlib import Path

import polars as pl

from src.bundle_exporter.load_results import load_proffast_242_preprocessing_log


def test_load_proffast_242_preprocessing_log(tmp_path: Path) -> None:
    logfile_path = tmp_path / "logfile.dat"
    logfile_path.write_text(
        "imeas,errflag,errflag2,astrelev,azimuth,UTh,cbfwd,cbbwd,cbfwd2,cbbwd2,"
        "DCraw,DCraw2,varraw,varraw2,NLC,NLC2,oob,oob2,DATUTC,DATLOC,TIMLOC,measfile,"
        "ch1fw_mean,ch1fw_min,ch1fw_max,ch1fw_var,ch1bw_mean,ch1bw_min,ch1bw_max,ch1bw_var,"
        "ch2fw_mean,ch2fw_min,ch2fw_max,ch2fw_var,ch2bw_mean,ch2bw_min,ch2bw_max,ch2bw_var\n"
        "1,0,20,19.97493,-101.3236,5.2443,0.1522,0.1498,0.0000,0.0000,"
        "0.1081,0.0218,0.005662,0.005535,0.000947,0.000000,0.000502,0.000000,"
        "220602,220602,051433,/input/ifg/220602/220602SN.4,"
        "-0.107083,-0.105724,-0.107856,0.020162,-0.107914,-0.107630,-0.108206,0.005352,"
        "-0.021668,-0.021440,-0.021797,0.016640,-0.021804,-0.021728,-0.021843,0.005286\n",
        encoding="utf-8",
    )

    df = load_proffast_242_preprocessing_log(str(logfile_path))

    assert df.shape == (1, 18)
    assert df["spectrum"].item() == "220602_051433SN.BIN"
    assert df["retrieval_filename"].item() == "220602SN.4"
    assert df["ch1_fwd_dc_mean"].dtype == pl.Float64
    assert df["ch1_fwd_dc_mean"].item() == -0.107083
    assert df["ch2_bwd_dc_var"].item() == 0.005286
