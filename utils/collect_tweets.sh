#!/bin/bash

WORKING_PATH=$(pwd)
WORK_DIR="data/downloads/"
TEMP_TWEET_PATH="data/temp/"
DATA_PATH="data/temp/tweeterCrawler/json_db/"
url=$1
filename=$2

mkdir -p "$WORK_DIR"
mkdir -p "$TEMP_TWEET_PATH"
curl -s "$url" -o "$WORK_DIR/${filename}"
tar -xzf "$WORK_DIR/$filename" -C $TEMP_TWEET_PATH

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

rm -rf $WORK_DIR
rm -rf $TEMP_TWEET_PATH
