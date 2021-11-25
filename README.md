# Download Pressure Map Files from Caltech

## What is it?

This tool can be used to download map-files from `ccycle.gps.caltech.edu`. These map files contain the vertical distribution of pressure, temperature and many other meteorological parameters for a certain location. Here are the first few rows for a sample map-file:

```
 11 12
 L120210601.map
 GSETUP                   Version 3.92     2013-12-20    GCT    
 WRITE_AUX                Version 1.11     27-May-2013    DW  
 Please see https://tccon-wiki.caltech.edu for a complete description of this file and its usage.
 Avogadro (molecules/mole): 6.0221415E+23
 Mass_Dry_Air (kg/mole): 28.9644E-03
 Mass_H2O (kg/mole): 18.01534E-03
 Latitude (degrees):  48.151
 Height,Temp,Pressure,Density,h2o,hdo,co2,n2o,co,ch4,hf,gravity
 km,K,hPa,molecules_cm3,parts,parts,ppm,ppb,ppb,ppb,ppt,m_s2
   0.00, 293.70, 1.017E+03, 2.508E+19, 1.548E-02, 1.533E-02, 404.514, 3.262E+02, 113.900, 1943.0,    0.10, 9.809
   1.00, 285.30, 9.036E+02, 2.294E+19, 1.035E-02, 9.963E-03, 410.850, 3.262E+02, 111.700, 1931.0,    0.11, 9.806
   2.00, 278.20, 8.003E+02, 2.084E+19, 6.033E-03, 5.580E-03, 412.929, 3.262E+02, 110.000, 1919.0,    0.12, 9.803
   3.00, 272.95, 7.070E+02, 1.876E+19, 2.040E-03, 1.733E-03, 413.919, 3.262E+02, 108.200, 1911.0,    0.13, 9.800
   4.00, 266.24, 6.229E+02, 1.695E+19, 1.555E-03, 1.292E-03, 414.315, 3.261E+02, 106.400, 1904.0,    0.17, 9.797
```

<br/>
<br/>

## How to set it up?

Dependency management with poetry: https://python-poetry.org/docs/#installation

Set up project interpreter:

```bash
# Create virtual environment (a local copy of python)
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

**Request will be cached** in the `cache/` directory. Please do not remove or empty this directory.
