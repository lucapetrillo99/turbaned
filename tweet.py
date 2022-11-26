import os
import json
import pickle
import tarfile
import subprocess
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
    return list(filter(lambda x: check_date(x.split('.')[0], start_date), tweets_directory))


def check_date(filename, date):
    filename_to_date = datetime.strptime(filename, '%d-%m-%Y')
    return filename_to_date.strftime('%d-%m-%Y') >= date.strftime('%d-%m-%Y')


def import_local_tweets(filename):
    with open(TWEET_PATH + filename, "rb") as fp:
        return json.load(fp)


def export_filtered_tweets(filename, filtered_tweets, path):
    files = os.listdir(FILTERED_TWEET_PATH)
    if not os.path.exists(FILTERED_TWEET_PATH + path):
        os.mkdir(FILTERED_TWEET_PATH + path)

    if filename not in files:
        with open(FILTERED_TWEET_PATH + path + '/' + filename, "wb") as f:
            pickle.dump(filtered_tweets, f)
    else:
        with open(FILTERED_TWEET_PATH + path + '/' + filename, "rb") as f:
            data = pickle.load(f)
            data += filtered_tweets
            file = open(FILTERED_TWEET_PATH + filename, "wb")
            pickle.dump(data, file)


def import_filtered_tweets(start_date):
    tweet_files = os.listdir(FILTERED_TWEET_PATH)
    tweets = list(filter(lambda x: check_tweet_date(x, start_date), tweet_files))
    tweets_cve = []
    for t in tweets:
        for f in os.listdir(FILTERED_TWEET_PATH + t):
            element = {'id': f}
            file = open(FILTERED_TWEET_PATH + t + '/' + f, 'rb')
            data = pickle.load(file)
            element['content'] = data
            tweets_cve.append(element)

    return tweets_cve


def check_tweet_date(file_date, date):
    return file_date >= date.strftime('%d-%m-%Y')


def check_filtered_tweets(start_date):
    directory_files = os.listdir(FILTERED_TWEET_PATH)

    if len(directory_files) > 0:
        if start_date.strftime('%d-%m-%Y') in directory_files:
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
        with open(PROCESSED_TWEET + str(filename), mode='w') as f:
            f.write(json.dumps(processed_tweets))


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
