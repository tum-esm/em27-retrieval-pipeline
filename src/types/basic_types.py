from typing import Literal

RetrievalAlgorithm = Literal["proffast-1.0", "proffast-2.2", "proffast-2.3",
                             "proffast-2.4"]
AtmosphericProfileModel = Literal["GGG2014", "GGG2020"]
SamplingRate = Literal["10m", "5m", "2m", "1m", "30s", "15s", "10s", "5s", "2s",
                       "1s"]
OutputTypes = Literal["gnd_p", "gnd_t", "app_sza", "azimuth", "xh2o", "xair",
                      "xco2", "xch4", "xco", "xch4_s5p"]
