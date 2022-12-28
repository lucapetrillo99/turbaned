#!/bin/bash

TWEET_PATH='data/tweets/'
CVE_PATH='data/cve/'

if [ -n "$(ls -A "$TWEET_PATH")" ]; then
  for file in "$TWEET_PATH"*; do
    rm "$file"
  done
fi

if [ -n "$(ls -A "$CVE_PATH")" ]; then
  for file in "$CVE_PATH"*; do
    rm "$file"
  done
fi
