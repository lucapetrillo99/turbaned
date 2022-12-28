import os
import json
import pickle
import config
import tarfile
import requests
import subprocess

from tqdm import tqdm
from datetime import datetime
from operator import itemgetter
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor

TWEET_PATH = 'data/tweets/'
FILTERED_TWEET_PATH = 'data/filtered_tweets/'
PROCESSED_TWEET_CVE = 'data/processed/tweets_cve/'
PROCESSED_TWEET = 'data/processed/tweet/'
TEMP_TWEET = 'data/temp/'

PROCESSED_DATA_FOUND = 1
NO_PROCESSED_DATA = -2
NO_TWEETS_PROCESSED = 0
NO_TWEETS_CVES_PROCESSED = -1


def get_tweets(initial_date, final_date):
    print("Fetching tweets online...")
    try:
        os.mkdir(TEMP_TWEET)
    except FileExistsError:
        pass

    if type(initial_date) is str:
        initial_date = datetime.strptime(initial_date, config.DATE_FORMAT)
    if type(final_date) is str:
        final_date = datetime.strptime(final_date, config.DATE_FORMAT)

    if initial_date.month == final_date.month:
        monthly_dates = [dt for dt in rrule(MONTHLY, dtstart=initial_date, until=final_date)]
    else:
        monthly_dates = [dt for dt in
                         rrule(MONTHLY, dtstart=initial_date, until=final_date + relativedelta(months=1))]
    with ThreadPoolExecutor() as executor:
        for idx, date in tqdm(enumerate(monthly_dates)):
            monthly_tweet_url = 'url' + date.strftime('%m-%Y') + '.tar.gz'
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


def get_temp_window_files(start_date, end_date, path):
    tweets_directory = os.listdir(path)
    tweets_directory.sort(key=lambda filename: datetime.strptime(filename.split(".")[0], config.DATE_FORMAT))
    if path == config.TWEET_PATH:
        return list(filter(lambda x: is_date_valid(x.split('.')[0], 2, start_date=start_date, end_date=end_date),
                           tweets_directory))
    else:
        return list(filter(lambda x: is_date_valid(x, 2, start_date=start_date, end_date=end_date),
                           tweets_directory))


def is_date_valid(filename, operator, start_date=None, end_date=None):
    filename_to_date = datetime.strptime(filename, config.DATE_FORMAT)
    if operator == 0:
        return filename_to_date >= start_date
    elif operator == 1:
        return filename_to_date <= end_date
    elif operator == 2:
        return start_date <= filename_to_date <= end_date
    elif operator == 3:
        if start_date is not None:
            return filename_to_date == start_date
        else:
            return filename_to_date == end_date


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


def check_filtered_tweets(start_date, end_date):
    return check_files_dates(start_date, end_date, config.FILTERED_TWEET_PATH)


def check_processed_tweets_cve(start_date, end_date):
    return check_files_dates(start_date, end_date, config.PROCESSED_TWEET_CVE_PATH)


def check_processed_tweets(start_date, end_date):
    return check_files_dates(start_date, end_date, config.PROCESSED_TWEET_PATH)


def check_files_dates(start_date, end_date, files_path):
    files = os.listdir(files_path)
    files.sort(key=lambda filename: datetime.strptime(filename.split(".")[0], config.DATE_FORMAT))
    if len(files) > 0:
        tweet_start_date_check = is_date_valid(files[0], 3, start_date=start_date)
        tweet_end_date_check = is_date_valid(files[len(files) - 1], 3, start_date=end_date)
        if tweet_start_date_check and tweet_end_date_check:
            return config.FILES_OK, None, None
        elif not tweet_start_date_check and tweet_end_date_check:
            return config.WRONG_S_DATE, start_date, files[0]
        elif tweet_start_date_check and not tweet_end_date_check:
            return config.WRONG_E_DATE, files[len(files) - 1], end_date
        else:
            return config.WRONG__DATES, None, None
    else:
        return config.NO_FILES, None, None


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
        tweet_indexes = sorted(tweet_indexes, reverse=True)
        file = open(TWEET_PATH + filename, "r")
        data = json.load(file)
        for index in tweet_indexes:
            if index < len(data):
                data.pop(index)

        with open(TWEET_PATH + filename, "w") as f:
            f.write(json.dumps(data))
