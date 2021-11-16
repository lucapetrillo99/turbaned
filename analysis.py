import os
import cve
import tweet
import model
import preprocessing

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

CVE_PATH = 'data/cve/'
TWEET_PATH = 'data/tweets/'
FILTERED_TWEET_PATH = 'data/filtered_tweets/'


def start_analysis(start_date):
    if tweet.check_filtered_tweets(start_date):
        result = tweet.check_processed_tweets(start_date)
        if result == 1:
            tweet_cve = tweet.import_processed_tweet_cve()
            if model.check_model(tweet_cve):
                model.find_similarity(tweet_cve, start_date)
            else:
                model.create_model(tweet_cve)
        elif result == 0:
            preprocessing.preprocess_data(start_date, tweet_analysis=True)
        elif result == -1:
            preprocessing.preprocess_data(start_date, tweet_cve_analysis=True)
        else:
            preprocessing.preprocess_data(start_date, tweet_cve_analysis=True, tweet_analysis=True)
    else:
        get_tweets_from_cve(start_date)


def check_cve(cve_id, tweet_text):
    return cve_id.lower() in tweet_text.lower()


def get_tweets_from_cve(start_date):
    cves_directory = os.listdir(CVE_PATH)
    cves_directory.sort()
    if len(cves_directory) > 0:
        cves = cve.import_local_cves(cves_directory)
    else:
        cve.get_cves(start_date)
        cves_directory = os.listdir(CVE_PATH)
        cves_directory.sort()
        cves = cve.import_local_cves(cves_directory)

    tweet_directory = os.listdir(TWEET_PATH)
    tweet_directory.sort()
    if len(tweet_directory) > 0:
        files = tweet.get_temp_window_files(start_date)
        current_date = datetime.now()
        if not tweet.check_date(files[0].split('.')[0], start_date) and not \
                tweet.check_date(files[len(files) - 1].split('.')[0], current_date):
            files = tweet.get_tweets(start_date)
        elif not tweet.check_date(files[len(files) - 1].split('.')[0], current_date):
            new_start_date = datetime.strptime(files[len(files) - 1].split('.')[0], '%d-%m-%Y')
            files = tweet.get_tweets(new_start_date)
        else:
            tweet_directory = os.listdir(CVE_PATH)
            tweet_directory.sort()
            files = tweet.get_temp_window_files(start_date)
    else:
        tweet.get_tweets(start_date)
        tweet_directory = os.listdir(CVE_PATH)
        tweet_directory.sort()
        files = tweet.get_temp_window_files(start_date)

    if len(files) > 0:
        print("Analyzing cves in tweets...")
        tweets_cves = []
        with ThreadPoolExecutor() as pool:
            for idx, (c, f) in enumerate(zip(cves, files)):
                if idx == 0:
                    prev_id = c['id']
                for t in tweet.import_local_tweets(f):
                    if pool.submit(check_cve, cve_id=c['id'], tweet_text=t['text']).result():
                        tweets_cves.append(t)
                if c['id'] != prev_id:
                    print('Found {} tweets with {}'.format(len(tweets_cves), prev_id))
                    if len(tweets_cves) > 0:
                        tweet.export_filtered_tweets(prev_id, tweets_cves, start_date.strftime('%Y-%m-%d'))
                        tweets_cves.clear()
                    prev_id = c['id']
                if idx == len(cves) - 1:
                    print('Found {} tweets with {}'.format(len(tweets_cves), prev_id))
                    if len(tweets_cves) > 0:
                        tweet.export_filtered_tweets(c['id'], tweets_cves, start_date.strftime("%Y-%m-%d"))

        if tweet.check_filtered_tweets(start_date):
            preprocessing.preprocess_data(start_date, tweet_cve_analysis=True, tweet_analysis=True)
            print('Creating model for cve...')
            tweet_cve = tweet.import_processed_tweet_cve()
            model.create_model(tweet_cve)
            model.find_similarity(tweet_cve, start_date)
        else:
            current_date = datetime.now()
            print('No cve founds in tweets from {} to {}'.format(start_date.strftime("%d-%m-%Y"),
                                                                 current_date.strftime("%d-%m-%Y")))

    else:
        print("There aren't tweets to analyze with {}".format(start_date.strftime("%d-%m-%Y")))
