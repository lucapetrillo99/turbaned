import os
import json
import pickle
import tarfile
import subprocess
from operator import itemgetter

import requests

from tqdm import tqdm
from datetime import datetime, timedelta
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor

TWEET_URL = 'https://martellone.iit.cnr.it/index.php/s/godwgTnKeA2dxKi/download?path=%2F&files='
TWEET_PATH = 'data/tweets/'
FILTERED_TWEET_PATH = 'data/filtered_tweets/'
PROCESSED_TWEET_CVE = 'data/processed/tweets_cve/'
PROCESSED_TWEET = 'data/processed/tweet/'
TEMP_TWEET = 'data/temp/'

PROCESSED_DATA_FOUND = 1
NO_PROCESSED_DATA = -2
NO_TWEETS_PROCESSED = 0
NO_TWEETS_CVES_PROCESSED = -1


def get_tweets(initial_date):
    os.mkdir(TEMP_TWEET)
    print("Fetching tweets online...")
    current_date = datetime.today() - timedelta(days=1)

    if initial_date.month == current_date.month:
        monthly_dates = [dt for dt in rrule(MONTHLY, dtstart=initial_date, until=current_date)]
    else:
        monthly_dates = [dt for dt in
                         rrule(MONTHLY, dtstart=initial_date, until=current_date + relativedelta(months=1))]
    with ThreadPoolExecutor() as executor:
        for idx, date in tqdm(enumerate(monthly_dates)):
            monthly_tweet_url = TWEET_URL + date.strftime('%m-%Y') + '.tar.gz'
            try:
                response = requests.get(monthly_tweet_url, stream=True)
                if response.status_code == 200:
                    executor.submit(collect_tweets(date.strftime('%m-%Y'), response))
            except ConnectionError:
                print("Connection error while getting tweets from database. Try later")


def collect_tweets(folder_name, response):
    files = os.listdir(TWEET_PATH)
    if folder_name not in files:
        try:
            file = tarfile.open(fileobj=response.raw, mode="r|gz")
            file.extractall(path=TEMP_TWEET)
            subprocess.call(['sh', './collect_tweets.sh'])
        except ConnectionError:
            print("Connection error while getting tweets from database. Try later")


def get_temp_window_files(start_date):
    tweets_directory = os.listdir(TWEET_PATH)
    tweets_directory.sort()
    return list(filter(lambda x: is_date_valid(x.split('.')[0], start_date, 0), tweets_directory))


# TODO this is useless, can be incorporated in previous function
def get_temp_window_tweets(start_date):
    tweets_directory = os.listdir(FILTERED_TWEET_PATH)
    tweets_directory.sort()
    return list(filter(lambda x: is_date_valid(x.split('.')[0], start_date, 0), tweets_directory))


def is_date_valid(filename, date, operator):
    filename_to_date = datetime.strptime(filename, '%d-%m-%Y')
    if operator == 0:
        return filename_to_date.strftime('%d-%m-%Y') >= date.strftime('%d-%m-%Y')
    elif operator == 1:
        return filename_to_date.strftime('%d-%m-%Y') <= date.strftime('%d-%m-%Y')
    elif operator == 2:
        current_date = datetime.today() - timedelta(days=1)
        return date.strftime('%d-%m-%Y') <= filename_to_date.strftime('%d-%m-%Y') <= current_date.strftime('%d-%m-%Y')


def import_local_tweets(filename):
    with open(TWEET_PATH + filename, "rb") as fp:
        return json.load(fp)


def export_filtered_tweets(filename, filtered_tweets):
    files = os.listdir(FILTERED_TWEET_PATH)

    if filename not in files:
        with open(FILTERED_TWEET_PATH + filename, "wb") as f:
            pickle.dump(filtered_tweets, f)
    else:
        with open(FILTERED_TWEET_PATH + filename, "rb") as f:
            data = pickle.load(f)
            if filtered_tweets[0]['id'] not in map(itemgetter('id'), data):
                data += filtered_tweets
                file = open(FILTERED_TWEET_PATH + filename, "wb")
                pickle.dump(data, file)


def import_filtered_tweets(filename):
    with open(FILTERED_TWEET_PATH + filename, 'rb') as file:
        return pickle.load(file)


def check_tweet_date(file_date, date):
    return file_date >= date.strftime('%d-%m-%Y')


def check_filtered_tweets(start_date):
    filtered_tweets = os.listdir(FILTERED_TWEET_PATH)
    filtered_tweets.sort()
    current_date = datetime.today() - timedelta(days=1)
    if len(filtered_tweets) > 0:
        if is_date_valid(filtered_tweets[0], start_date, 0) and \
                is_date_valid(filtered_tweets[len(filtered_tweets) - 1], current_date, 1):
            return True
        else:
            return False
    else:
        return False


def check_processed_tweets(start_date):
    processed_tweets_cve = os.listdir(PROCESSED_TWEET_CVE)
    processed_tweets = os.listdir(PROCESSED_TWEET)

    if (len(processed_tweets_cve) > 0) and (len(processed_tweets) > 0):
        if start_date.strftime('%d-%m-%Y') + '.json' in processed_tweets:
            return PROCESSED_DATA_FOUND
    elif len(processed_tweets_cve) > 0 and len(processed_tweets) == 0:
        return NO_TWEETS_PROCESSED
    elif len(processed_tweets) > 0 and len(processed_tweets_cve) == 0:
        if start_date.strftime('%d-%m-%Y') + '.json' in processed_tweets:
            return NO_TWEETS_CVES_PROCESSED
    else:
        return NO_PROCESSED_DATA


def export_processed_tweets(filename, processed_tweets, cve=None):
    if cve is not None:
        with open(PROCESSED_TWEET_CVE + str(filename), "wb") as file:
            pickle.dump(processed_tweets, file)
    else:
        with open(PROCESSED_TWEET + str(filename), mode='wb') as f:
            pickle.dump(processed_tweets, f)


def import_processed_tweet_cve():
    return os.listdir(PROCESSED_TWEET_CVE)


def import_processed_tweet_cve_content(filename):
    with open(PROCESSED_TWEET_CVE + filename, 'rb') as f:
        return pickle.load(f)


def import_processed_tweet(start_date):
    tweet_files = os.listdir(PROCESSED_TWEET)
    return list(filter(lambda x: check_tweet_date(x, start_date), tweet_files))


def import_processed_tweet_content(filename):
    with open(PROCESSED_TWEET + filename) as f:
        return json.load(f)


def reorder_tweets(tweets_found):
    res = {}
    for tweet in tweets_found:
        for indexes in tweet:
            if indexes in res:
                res[indexes] += (tweet[indexes])
            else:
                res[indexes] = tweet[indexes]
    return res


def remove_tweets_with_cve(tweets):
    print("Removing found tweets...")
    for filename, tweet_indexes in tqdm(reorder_tweets(tweets).items()):
        print(filename)
        tweet_indexes = sorted(tweet_indexes, reverse=True)
        file = open(TWEET_PATH + filename, "r")
        data = json.load(file)
        for index in tweet_indexes:
            if index < len(data):
                data.pop(index)

        with open(TWEET_PATH + filename, "w") as f:
            f.write(json.dumps(data))
