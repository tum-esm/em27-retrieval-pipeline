## Semantic Versioning

Read about "semantic versioning" here: https://semver.org/.

-   Major Release = `new.0.0`
-   Minor Release = `same.new.0`
-   Patch Release = `same.same.new`

<br/>

## Adding days to the manual queue

**`add-days-without-outputs-to-queue.py`: For _major_ and _minor_ releases.**

Days where the interferograms exist in the Proffast output, but there is no result for the currently configured version yet. Used, when upgrading to a newer Proffast version and recomputing things.

<br/>

**`add-failed-days-to-queue.py`: For _patch_ releases.**

Days where the interferograms exist in the Proffast output and the Proffast output for this version has failed. Used when a fix has been deployed in the Pylot or the Proffast.
