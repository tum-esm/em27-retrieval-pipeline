# Frequently Asked Questions

## In the Proffast 2.X preprocessing, how to interpret `errflag` and `errflag_CO`?

The errflags are added up in the following way:

- `errflag` &nbsp;= `0`: no error
- `errflag` += `0.000.000.001` or `0.000.000.002`: solar elevation below 1 deg
- `errflag` += `0.000.000.010` or `0.000.000.020`: DC mean too low (below `DCmin`)
- `errflag` += `0.000.000.100` or `0.000.000.200`: DC variance too high (above `DCvar`)
- `errflag` += `0.000.001.000` or `0.000.002.000`: DC correction failed
- `errflag` += `0.000.010.000` or `0.000.020.000`: Not enough ifg points available on any side of the ifg for requested resolution
- `errflag` += `0.000.100.000` or `0.000.200.000`: Out-of-band artefacts are too strong
- `errflag` += `0.001.000.000` or `0.002.000.000`: Not enough points available for calculating phase spectrum
- `errflag` += `0.010.000.000` or `0.020.000.000`: Invalid spectral calibration
- `errflag` += `0.100.000.000` or `0.200.000.000`: Check consistency of fwd and bwd pair of spectra
- `errflag` += `1.000.000.000` or `2.000.000.000`: Phase error > 0.005

The numeric values are the same for `errflag_CO`, but some of the steps/checks are not performed on the CO band.
