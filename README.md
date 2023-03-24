**Work in progress. Until then, ask Moritz Makowski ([moritz.makowski@tum.de](mailto:moritz.makowski@tum.de))**

This codebase provides an automated data pipeline for Proffast 2.2 (https://www.imk-asf.kit.edu/english/3225.php). Under the hood, it uses the Proffast Pylot (https://gitlab.eudat.eu/coccon-kit/proffastpylot.git, Commit b9f5d7040dfeb8be5dba9c9a314fe7ab6dd98a9f) to interact with Proffast

We decided to included a copy of the Fortran codebase of Proffast as well as the Python codebase of the Proffast Pylot inside this repository, so we can slightly modify it and have less complexity due to Git Submodules or on-demand downloads.

Our data pipeline provides:

-   Easy configuration of the pipeline using validated JSON files
-   Managing station metadata using GitHub
-   Filtering if interferogram files that Proffast cannot process
-   Parallelization of the Proffast Pylot execution
-   Comprehensive management of logs and output data
-   Download of vertical profiles
-   Merging of smoothed individual station outputs into daily output files
-   Documentation and full API reference

The three main parts of the pipeline are: Downloading input data, processing and merging the raw outputs:

![](docs/revised-retrieval-pipeline-architecture.png)
