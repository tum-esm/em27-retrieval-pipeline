#!/bin/bash

local=$(git -C $LOCAL rev-parse HEAD)
remote=$(git ls-remote --symref $REMOTE | awk 'NR==2{print $1}')
printf "Local : %s\nRemote: %s\n" $local $remote

if [[ $local == $remote ]]; then
    echo "Commit hashes match."
    return 0
else
    echo "Commit hashes do not match." >&2
    return 1
fi