docker run --rm -it \
    -v $(pwd):/data \
    -e GIT_SHA=$(git rev-parse HEAD) \
    -e JOURNAL=joss \
    openjournals/inara:latest \
    -o pdf paper.md