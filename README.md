# EM27 Retrieval Pipeline

Due to operating [MUCCnet (Dietrich et al., 2021)](https://doi.org/10.5194/amt-14-1111-2021) we retrieve a lot of EM27/SUN data and have used this pipeline since early 2022 (release date of Proffast 2.0).

This codebase provides an automated data pipeline for Proffast 1 and 2.X (https://www.imk-asf.kit.edu/english/3225.php). Under the hood, it uses the Proffast Pylot (https://gitlab.eudat.eu/coccon-kit/proffastpylot.git, Commit b9f5d7040dfeb8be5dba9c9a314fe7ab6dd98a9f) to interact with Proffast 2 and an in-house connector to interact with Proffast 1. Whenever using this pipeline for Proffast retrievals, please make sure to also cite [Proffast](https://www.imk-asf.kit.edu/english/3225.php) and the [Proffast Pylot](https://gitlab.eudat.eu/coccon-kit/proffastpylot) (for Proffast 2.X retrievals).

📚 Read the documentation at [em27-retrieval-pipeline.netlify.app](https://em27-retrieval-pipeline.netlify.app).<br/>
💾 Get the source code at [github.com/tum-esm/em27-retrieval-pipeline](https://github.com/tum-esm/em27-retrieval-pipeline).<br/>
🐝 Report Issues or discuss enhancements using [issues on GitHub](https://github.com/tum-esm/em27-retrieval-pipeline/issues)
