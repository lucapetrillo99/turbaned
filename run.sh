#!/bin/bash

uid=$(id -u)
gid=$(id -g)

mkdir -p data
docker run --user "$uid":"$gid" -v "$(pwd)"/data:/app/data tca "$@"
