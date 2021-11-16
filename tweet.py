import os
import json
import pickle
import requests

from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime
from dateutil.rrule import rrule, MONTHLY
from concurrent.futures import ThreadPoolExecutor

TWEET_URL = 'http://146.48.99.30:9999/'
TWEET_PATH = 'data/tweets/'
FILTERED_TWEET_PATH = 'data/filtered_tweets/'
PROCESSED_TWEET_CVE = 'data/processed/tweets_cve/'
PROCESSED_TWEET = 'data/processed/tweet/'


def get_tweets(initial_date):
    print("Fetching tweets online...")
    current_date = datetime.now()
    monthly_dates = [dt for dt in rrule(MONTHLY, dtstart=initial_date, until=current_date)]
    with ThreadPoolExecutor() as executor:
        for idx, date in enumerate(monthly_dates):
            monthly_tweet_url = TWEET_URL + date.strftime('%m-%Y')
            try:
                resp = requests.get(url=TWEET_URL + date.strftime('%m-%Y'))
                soup = BeautifulSoup(resp.content, 'html.parser')
                for element in tqdm(soup.select('li')):
                    if idx == 0 or idx == len(monthly_dates):
                        if check_date(element.a['href'].split('.')[0], initial_date):
                            executor.submit(collect_tweets, element.a['href'], monthly_tweet_url)
                    else:
                        executor.submit(collect_tweets, element.a['href'], monthly_tweet_url)
            except ConnectionError:
                print("Connection error while getting tweets from database. Try later")


def collect_tweets(json_name, url):
    try:
        response = requests.get(url + '/' + json_name)
        data = response.json()
        f = open(TWEET_PATH + json_name, 'w')
        json.dump(data, f)
    except ConnectionError:
        print("Connection error while getting tweets from database. Try later")


def get_temp_window_files(start_date):
    tweets_directory = os.listdir(TWEET_PATH)
    tweets_directory.sort()
    return list(filter(lambda x: check_date(x.split('.')[0], start_date), tweets_directory))


def check_date(filename, date):
    filename_to_date = datetime.strptime(filename, '%d-%m-%Y')
    return filename_to_date.strftime('%Y-%m-%d') >= date.strftime('%Y-%m-%d')


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
    return file_date >= date.strftime('%Y-%m-%d')


def check_filtered_tweets(start_date):
    directory_files = os.listdir(FILTERED_TWEET_PATH)

    if len(directory_files) > 0:
        if start_date.strftime('%Y-%m-%d') in directory_files:
            return True
        else:
            return False
    else:
        return False


def check_processed_tweets(start_date):
    processed_tweets_cve = os.listdir(PROCESSED_TWEET_CVE)
    processed_tweets = os.listdir(PROCESSED_TWEET)

    if (len(processed_tweets_cve) > 0) and (len(processed_tweets) > 0):
        if start_date.strftime('%d%m%Y') + '.json' in processed_tweets:
            return 1
    elif len(processed_tweets_cve) > 0:
        return 0
    elif len(processed_tweets) > 0 and start_date.strftime('%d%m%Y') + '.json' in processed_tweets:
        return -1
    else:
        return 2


def export_processed_tweets(filename, processed_tweets, cve=None):
    if cve is not None:
        with open(PROCESSED_TWEET_CVE + str(filename), "wb") as file:
            pickle.dump(processed_tweets, file)
    else:
        f = open(PROCESSED_TWEET + str(filename), "a+")
        json.dump(processed_tweets, f)


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
