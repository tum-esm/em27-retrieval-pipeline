# EM27 Retrieval Pipeline

![GitHub License](https://img.shields.io/github/license/tum-esm/em27-retrieval-pipeline?style=flat&label=License&labelColor=%230f172a&color=%23fef08a)
![GitHub Tag](https://img.shields.io/github/v/tag/tum-esm/em27-retrieval-pipeline?sort=semver&style=flat&label=Latest%20Pipeline%20Version&color=%23fef08a&cacheSeconds=60&labelColor=%230f172a)<br/>
![Static Badge](https://img.shields.io/badge/Proffast%201.0%20%7C%20Proffast%202.2%20%7C%20Proffast%202.3%20-%20whydoineedthis?style=flat&label=Supported%20Retrieval%20Algorithms&labelColor=%230f172a&color=%2399f6e4)<br/>
![Static Badge](https://img.shields.io/badge/GGG2014%20%7C%20GGG2020%20-%20whydoineedthis?style=flat&label=Supported%20Atmospheric%20Profiles&labelColor=%230f172a&color=%2399f6e4)

Due to operating [MUCCnet (Dietrich et al., 2021)](https://doi.org/10.5194/amt-14-1111-2021), we retrieve a lot of EM27/SUN data and have used this pipeline since early 2022 (release date of Proffast 2.0).

This codebase provides an automated data pipeline for Proffast 1 and 2.X (https://www.imk-asf.kit.edu/english/3225.php). Under the hood, it uses the Proffast Pylot (https://gitlab.eudat.eu/coccon-kit/proffastpylot.git, Commit b9f5d7040dfeb8be5dba9c9a314fe7ab6dd98a9f) to interact with Proffast 2 and an in-house connector to interact with Proffast 1. Whenever using this pipeline for Proffast retrievals, please make sure to also cite [Proffast](https://www.imk-asf.kit.edu/english/3225.php) and the [Proffast Pylot](https://gitlab.eudat.eu/coccon-kit/proffastpylot) (for Proffast 2.X retrievals).

📚 Read the documentation at [em27-retrieval-pipeline.netlify.app](https://em27-retrieval-pipeline.netlify.app).<br/>
💾 Get the source code at [github.com/tum-esm/em27-retrieval-pipeline](https://github.com/tum-esm/em27-retrieval-pipeline).<br/>
🐝 Report Issues or discuss enhancements using [issues on GitHub](https://github.com/tum-esm/em27-retrieval-pipeline/issues).

**Related Projects:**

⚙️ Many of our projects use a lot of functionality from the `tum-esm-utils` package: [github.com/tum-esm/utils](https://github.com/tum-esm/utils).<br/>
🤖 Our EM27/SUN systems are running autonomously with the help of Pyra: [github.com/tum-esm/pyra](https://github.com/tum-esm/pyra).
