#!/bin/bash

WORKING_PATH=$(pwd)
DATA_PATH="$(pwd)/data/temp/tweeterCrawler/json_db/"

cd "$DATA_PATH" || {
  echo "Tweet folder does not exist"
  exit 1
}

for i in *; do
  cd "$i" || exit

  for file in *; do
    mv "$file" "$WORKING_PATH"/data/tweets/
  done
  cd ..
done

cd "$WORKING_PATH" || exit
rm -rf data/temp/
