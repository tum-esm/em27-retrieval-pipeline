
# Generate the EM27 plot data for atmosphere.ei.tum.de

Full documentation coming soon! Until then, ask Moritz Makowski (moritz.makowski@tum.de).

The repository https://gitlab.lrz.de/esm/em27-plot-data-upload will soon be integrated in this repository. This repository also includes some of the code of https://gitlab.lrz.de/esm/columnmeasurementautomation .

The reason for having a standalone repository is to have an isolated environment for generating plot data. No other automation or changes to other pipelines should interfere with this automation.

<br/>

## Set up

```
git clone https://gitlab.lrz.de/esm/em27-plot-data-upload upload_website_data
cd upload_website_data
git checkout switch-to-firebase
cd ..
```

Example `config.json`:
```json
{
    "mysql": {
        "host": "...",
        "user": "...",
        "passwd": "...",
        "database": "...",
    },
    "startDate": "20210727",
    "locations": ["ROS", "..."],
    "gases": ["co2", "ch4"],
    "strapi": {
        "identifier": "...",
        "password": "...",
        "url": "..."
    }
}
```