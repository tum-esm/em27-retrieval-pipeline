CREATE TABLE IF NOT EXISTS measurements
(
    sensor             varchar(16)                 not null,
    utc                timestamp without time zone not null,
    gnd_p              decimal,
    gnd_t              decimal,
    app_sza            decimal,
    azimuth            decimal,
    xh2o               double precision,
    xair               double precision,
    xco2               double precision,
    xch4               double precision,
    xco                double precision,
    xch4_s5p           double precision,
    h2o                double precision,
    o2                 double precision,
    co2                double precision,
    ch4                double precision,
    co                 double precision,
    ch4_s5p            double precision,
    retrieval_software varchar(4)                  not null,

    PRIMARY KEY (sensor, utc, retrieval_software)
)
