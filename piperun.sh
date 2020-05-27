#!/bin/bash

if [[ $# -eq 0 ]]; then
    echo "$0: no pipe file specified" 1>&2
    exit 1
fi

while read -r cmd; do
    $cmd
done < $1

bash -i