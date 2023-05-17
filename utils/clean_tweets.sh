#!/bin/bash

TWEET_PATH="$(pwd)/data/tweets/"

if [ -n "$(ls -A "$TWEET_PATH")" ]; then
  for file in "$TWEET_PATH"*; do
    rm "$file"
  done
fi
