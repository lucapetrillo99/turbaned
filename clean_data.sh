#!/bin/bash

FILTERED_TWEET_PATH='data/filtered_tweets/'
CVE_PATH='data/cve/'

if [ -n "$(ls -A "$FILTERED_TWEET_PATH")" ]; then
  for file in "$FILTERED_TWEET_PATH"*; do
    rm "$file"
  done
fi

if [ -n "$(ls -A "$CVE_PATH")" ]; then
  for file in "$CVE_PATH"*; do
    rm "$file"
  done
fi
