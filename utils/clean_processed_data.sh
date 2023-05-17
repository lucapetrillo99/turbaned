#!/bin/bash

PROCESSED_TWEET_CVE_PATH="$(pwd)/data/processed/tweets_cve/"
PROCESSED_TWEET_PATH="$(pwd)/data/processed/tweet/"
PROCESSED_CVE_PATH="$(pwd)/data/processed/cve/"
parameter=$1

case $parameter in
1)
  if [ -n "$(ls -A "$PROCESSED_TWEET_CVE_PATH")" ]; then
    for file in "$PROCESSED_TWEET_CVE_PATH"*; do
      rm "$file"
    done
  fi
  ;;

2)
  if [ -n "$(ls -A "$PROCESSED_TWEET_PATH")" ]; then
    for file in "$PROCESSED_TWEET_PATH"*; do
      rm "$file"
    done
  fi
  ;;

3)
  if [ -n "$(ls -A "$PROCESSED_TWEET_CVE_PATH")" ]; then
    for file in "$PROCESSED_TWEET_CVE_PATH"*; do
      rm "$file"
    done
  fi
  if [ -n "$(ls -A "$PROCESSED_TWEET_PATH")" ]; then
    for file in "$PROCESSED_TWEET_PATH"*; do
      rm "$file"
    done
  fi
  if [ -n "$(ls -A "$PROCESSED_CVE_PATH")" ]; then
    for file in "$PROCESSED_CVE_PATH"*; do
      rm "$file"
    done
  fi
  ;;
esac
