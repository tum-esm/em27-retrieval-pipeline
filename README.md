# Download `.map` and `.mod` Files from Caltech

## What is it?

This tool can be used to download `.map` and `.mod` files from `ccycle.gps.caltech.edu`. These files contain the vertical distribution of pressure, temperature, and many other meteorological parameters for a certain location and date. The underlying accessing method is described on https://tccon-wiki.caltech.edu/Main/CentralizedModMaker.

Here are the first few rows for a sample `.map` file:

```
 11 12
 xx20220323.map
 GSETUP                   Version 3.92     2013-12-20    GCT
 WRITE_AUX                Version 1.11     27-May-2013    DW
 Please see https://tccon-wiki.caltech.edu for a complete description of this file and its usage.
 Avogadro (molecules/mole): 6.0221415E+23
 Mass_Dry_Air (kg/mole): 28.9644E-03
 Mass_H2O (kg/mole): 18.01534E-03
 Latitude (degrees):  48.000
 Height,Temp,Pressure,Density,h2o,hdo,co2,n2o,co,ch4,hf,gravity
 km,K,hPa,molecules_cm3,parts,parts,ppm,ppb,ppb,ppb,ppt,m_s2
   0.00, 288.35, 1.030E+03, 2.589E+19, 1.048E-02, 1.010E-02, 427.284, 3.264E+02, 142.400, 1948.0,    0.10, 9.809
   1.00, 281.72, 9.142E+02, 2.350E+19, 5.480E-03, 5.031E-03, 421.344, 3.264E+02, 139.200, 1935.0,    0.11, 9.806
   2.00, 275.70, 8.088E+02, 2.125E+19, 1.044E-03, 8.385E-04, 418.770, 3.264E+02, 136.600, 1924.0,    0.12, 9.803
   3.00, 269.38, 7.135E+02, 1.919E+19, 9.405E-04, 7.484E-04, 417.384, 3.264E+02, 134.100, 1915.0,    0.13, 9.800
   4.00, 262.31, 6.276E+02, 1.733E+19, 6.475E-04, 4.984E-04, 416.493, 3.264E+02, 131.600, 1908.0,    0.17, 9.797
```

<br/>

Here are the first few rows for a sample `.mod` file:

```
4  5
6378.137  6.0000e-05  48.000 9.810    0.254 1013.250  236.764
 mbar        Kelvin         km      g/mole      vmr
Pressure  Temperature     Height     MMW        H2O
1.000e+03    286.645      0.254    28.9640    9.275e-03
9.250e+02    282.285      0.905    28.9640    6.193e-03
8.500e+02    278.249      1.599    28.9640    1.086e-03
7.000e+02    268.427      3.157    28.9640    9.249e-04
6.000e+02    259.839      4.350    28.9640    5.352e-04
```

<br/>
<br/>

## How to set it up?

Dependency management with poetry: https://python-poetry.org/docs/#installation

Set up the project interpreter:

```bash
# Create a virtual python environment
python3.9 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
poetry install
```

<br/>
<br/>

## How to run it?

1. Use the file `config.example.json` to create a `config.json` file in your project directory for your setup

2. Run the script and wait for the result

```bash
python3.9 run.py
```

<br/>

**Responses from Caltech will be cached** in the `cache/` directory. If you want your duplicate requests to be faster and use fewer computing resources, do not remove or empty this directory.
