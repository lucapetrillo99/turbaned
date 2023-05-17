#!/bin/bash

FILTERED_TWEET_PATH="$(pwd)/data/filtered_tweets/"
CVE_REFERENCES_PATH="$(pwd)/data/cve_references/"
CVE_PATH="$(pwd)/data/cve/"

if [ -n "$(ls -A "$FILTERED_TWEET_PATH")" ]; then
  for file in "$FILTERED_TWEET_PATH"*; do
    rm "$file"
  done
fi


if [ -n "$(ls -A "$CVE_REFERENCES_PATH")" ]; then
  for file in "$CVE_REFERENCES_PATH"*; do
    rm "$file"
  done
fi

if [ -n "$(ls -A "$CVE_PATH")" ]; then
  for file in "$CVE_PATH"*; do
    rm "$file"
  done
fi
