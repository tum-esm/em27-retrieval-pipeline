# EM27 Retrieval Pipeline

<img alt="GitHub License" src="https://img.shields.io/github/license/tum-esm/em27-retrieval-pipeline?style=flat&label=License&labelColor=%230f172a&color=%23fef08a" className="inline p-0 m-px mt-4"/> <img alt="GitHub Tag" src="https://img.shields.io/github/v/tag/tum-esm/em27-retrieval-pipeline?sort=semver&style=flat&label=Latest%20Pipeline%20Version&color=%23fef08a&cacheSeconds=60&labelColor=%230f172a" className="inline p-0 m-px mt-4"/> <br/> <img alt="Static Badge" src="https://img.shields.io/badge/Proffast%201.0%20%7C%202.2%20%7C%202.3-whydoineedthis?style=flat&label=Retrieval%20Algorithms&labelColor=%230f172a&color=%2399f6e4" className="inline p-0 m-px "/> <br/> <img alt="Static Badge" src="https://img.shields.io/badge/GGG2014%20%7C%20GGG2020%20-%20whydoineedthis?style=flat&label=Atmospheric%20Profile%20Models&labelColor=%230f172a&color=%2399f6e4" className="inline p-0 m-px "/>

We retrieve a lot of EM27/SUN data, produced mainly by [MUCCnet (Dietrich et al., 2021)](https://doi.org/10.5194/amt-14-1111-2021), and have used this pipeline since end of 2021.

This codebase provides an automated data pipeline for [Proffast 1 and 2.X](https://www.imk-asf.kit.edu/english/3225.php). Under the hood, it uses the [Proffast Pylot](https://gitlab.eudat.eu/coccon-kit/proffastpylot.git) to interact with Proffast 2 and an in-house connector to interact with Proffast 1. Whenever using this pipeline for Proffast retrievals, please make sure to also cite [Proffast](https://www.imk-asf.kit.edu/english/3225.php) and the [Proffast Pylot](https://gitlab.eudat.eu/coccon-kit/proffastpylot) (for Proffast 2.X retrievals).

📚 Read the documentation at [em27-retrieval-pipeline.netlify.app](https://em27-retrieval-pipeline.netlify.app).<br/>
💾 Get the source code at [github.com/tum-esm/em27-retrieval-pipeline](https://github.com/tum-esm/em27-retrieval-pipeline).<br/>
🐝 Report Issues or discuss enhancements using [issues on GitHub](https://github.com/tum-esm/em27-retrieval-pipeline/issues).

**Related Projects:**

⚙️ Many of our projects use much functionality from the [`tum-esm-utils` package](https://github.com/tum-esm/utils).<br/>
🤖 Our EM27/SUN systems are running autonomously with the help of [Pyra](https://github.com/tum-esm/pyra).
