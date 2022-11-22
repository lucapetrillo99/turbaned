#!/bin/bash

WORKING_PATH=$(pwd)
DATA_PATH='data/temp/tweeterCrawler/json_db/'

cd $DATA_PATH

for i in * ; do
    cd $i

    for file in $(ls); do
    mv $file $WORKING_PATH/data/tweets/
    done
    cd ..
done

cd $WORKING_PATH
rm -rf temp/
