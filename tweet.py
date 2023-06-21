import os
import json
import pickle
import config
import subprocess

from tqdm import tqdm
from datetime import datetime
from operator import itemgetter
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta

TEMP_TWEET_PATH = os.path.join(config.DATA_PATH, "temp/")


def get_tweets(initial_date, final_date):
    print("Fetching tweets online...")

    # all months between the dates entered are extracted
    if initial_date.month == final_date.month:
        monthly_dates = [dt for dt in rrule(MONTHLY, dtstart=initial_date, until=final_date)]
    else:
        monthly_dates = [dt for dt in
                         rrule(MONTHLY, dtstart=initial_date, until=final_date + relativedelta(months=1))]

    for date in monthly_dates:
        filename = date.strftime('%m-%Y') + '.tar.gz'
        monthly_tweet_url = "url" + filename
        subprocess.run([config.COLLECT_TWEETS, monthly_tweet_url, filename])


# function that returns all tweets corresponding to a start and end date
def get_temp_window_files(start_date, end_date, path):
    tweets_directory = os.listdir(path)
    tweets_directory.sort(key=lambda filename: datetime.strptime(filename.split(".")[0], config.DATE_FORMAT))
    if path == config.TWEET_PATH:
        return list(
            filter(lambda x: is_date_valid(x.split('.')[0], config.INCLUDED, start_date=start_date, end_date=end_date),
                   tweets_directory))
    else:
        return list(filter(lambda x: is_date_valid(x, config.INCLUDED, start_date=start_date, end_date=end_date),
                           tweets_directory))


def is_date_valid(filename, operator, start_date=None, end_date=None):
    filename_to_date = datetime.strptime(filename, config.DATE_FORMAT)
    match operator:
        case config.GREATER_EQUAL:
            return filename_to_date >= start_date
        case config.LESS_EQUAL:
            return filename_to_date <= end_date
        case config.INCLUDED:
            return start_date <= filename_to_date <= end_date
        case config.EQUAL:
            if start_date is not None:
                return filename_to_date == start_date
            else:
                return filename_to_date == end_date


def export_filtered_tweets(filename, filtered_tweets):
    files = os.listdir(config.FILTERED_TWEET_PATH)

    if filename not in files:
        with open(config.FILTERED_TWEET_PATH + filename, 'wb') as f:
            pickle.dump(filtered_tweets, f)
    else:
        with open(config.FILTERED_TWEET_PATH + filename, 'rb') as f:
            data = pickle.load(f)
            if filtered_tweets[0]['id'] not in map(itemgetter('id'), data):
                data += filtered_tweets
                file = open(config.FILTERED_TWEET_PATH + filename, 'wb')
                pickle.dump(data, file)


def check_files_dates(start_date, end_date, files_path):
    files = os.listdir(files_path)
    files.sort(key=lambda filename: datetime.strptime(filename.split(".")[0], config.DATE_FORMAT))
    if len(files) > 0:
        tweet_start_date_check = is_date_valid(files[0], config.EQUAL, start_date=start_date)
        tweet_end_date_check = is_date_valid(files[len(files) - 1], config.EQUAL, start_date=end_date)
        if tweet_start_date_check and tweet_end_date_check:
            return config.FILES_OK, None, None
        elif not tweet_start_date_check and tweet_end_date_check:
            return config.WRONG_S_DATE, start_date, datetime.strptime(files[0], config.DATE_FORMAT)
        elif tweet_start_date_check and not tweet_end_date_check:
            return config.WRONG_E_DATE, datetime.strptime(files[len(files) - 1], config.DATE_FORMAT), end_date
        else:
            return config.WRONG__DATES, None, None
    else:
        return config.NO_FILES, None, None


def import_local_tweets(filename):
    with open(os.path.join(config.TWEET_PATH, filename), 'rb') as fp:
        return json.load(fp)


def import_data(path, filename):
    with open(os.path.join(path, filename), 'rb') as f:
        return pickle.load(f)


def export_processed_tweets(filename, processed_tweets, cve=None):
    if cve is not None:
        with open(config.PROCESSED_TWEET_CVE_PATH + str(filename), 'wb') as file:
            pickle.dump(processed_tweets, file)
    else:
        with open(config.PROCESSED_TWEET_PATH + str(filename), mode='wb') as f:
            pickle.dump(processed_tweets, f)


# aggregates together all indexes of tweets belonging to the same file
def reorder_tweets(tweets_found):
    res = {}
    for tweet in tweets_found:
        for indexes in tweet:
            if indexes in res:
                res[indexes] += (tweet[indexes])
            else:
                res[indexes] = tweet[indexes]
    return res


# function that removes all tweets that have a cve through the index
def remove_tweets_with_cve(tweets):
    print("Removing found tweets...")
    for filename, tweet_indexes in tqdm(reorder_tweets(tweets).items()):
        tweet_indexes = sorted(tweet_indexes, reverse=True)
        file = open(config.TWEET_PATH + filename, 'r')
        data = json.load(file)
        for index in tweet_indexes:
            if index < len(data):
                data.pop(index)

        with open(config.TWEET_PATH + filename, 'w') as f:
            f.write(json.dumps(data))
