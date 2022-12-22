import os
import re
import cve
import tweet
import model
import preprocessing

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

CVE_PATH = 'data/cve/'
TWEET_PATH = 'data/tweets/'
FILTERED_TWEET_PATH = 'data/filtered_tweets/'
PROCESSED_DATA_FOUND = 1
NO_PROCESSED_DATA = -2
NO_TWEETS_PROCESSED = 0
NO_TWEETS_CVES_PROCESSED = -1


def start_analysis(start_date, end_date):
    if tweet.check_filtered_tweets(start_date, end_date):
        result = tweet.check_processed_tweets(start_date)
        if result == PROCESSED_DATA_FOUND:
            tweet_cve = tweet.import_processed_tweet_cve()
            if model.check_model(tweet_cve):
                if model.check_results(start_date):
                    print("Results for {} are in data/results".format(start_date.strftime("%d-%m-%Y")))
                else:
                    model.find_similarity(start_date)
            else:
                model.create_model()
        elif result == NO_TWEETS_PROCESSED:
            preprocessing.preprocess_data(start_date, tweet_analysis=True)
        elif result == NO_TWEETS_CVES_PROCESSED:
            preprocessing.preprocess_data(start_date, tweet_cve_analysis=True)
        else:
            preprocessing.preprocess_data(start_date, tweet_cve_analysis=True, tweet_analysis=True)
    else:
        get_tweets_from_cve(start_date, end_date)


def get_tweets_from_cve(start_date, end_date):
    tweet_directory = os.listdir(TWEET_PATH)
    if len(tweet_directory) > 0:
        files = tweet.get_temp_window_files(start_date, end_date)

        # check for tweets that match an end date, otherwise download tweets from the last available date to the
        # tweets with the indicated end date
        if not tweet.is_date_valid(files[0].split('.')[0], 3, start_date=start_date):
            tweet.get_tweets(start_date, files[0].split('.')[0])
            files = tweet.get_temp_window_files(start_date, end_date)

        # check for tweets that match an end date, otherwise download tweets from the last available date to the
        # tweets with the indicated end date
        if not tweet.is_date_valid(files[len(files) - 1].split('.')[0], 3, start_date=end_date):
            tweet.get_tweets(files[len(files) - 1].split('.')[0], end_date)
            files = tweet.get_temp_window_files(start_date, end_date)
    else:
        tweet.get_tweets(start_date, end_date)
        tweet_directory = os.listdir(TWEET_PATH)
        tweet_directory.sort()
        files = tweet.get_temp_window_files(start_date, end_date)
    if len(files) > 0:
        print("Analyzing cves in tweets...")
        tweets_cves = []
        tweets_found = []
        tweets_indexes = []
        cves = []
        cve_regex = cve.build_regex()
        with ThreadPoolExecutor() as pool:
            for f in files:
                for index, t in enumerate(tweet.import_local_tweets(f)):
                    result = re.findall(cve_regex, t['text'], re.I)
                    if len(result) > 0:
                        result = list(set(result))
                        cves += result
                        tweets_indexes.append(index)
                        tweets_cves.append(t)
                if len(tweets_indexes) > 0:
                    tweets_found.append({f: tweets_indexes})
                    tweets_indexes = []
                if len(tweets_cves) > 0:
                    pool.submit(tweet.export_filtered_tweets(filename=f.split(".")[0], filtered_tweets=tweets_cves))
                    tweets_cves = []
        if len(tweets_found) > 0:
            tweet.remove_tweets_with_cve(tweets_found)
            cve.retrieve_cves(cves)
            preprocessing.preprocess_data(start_date, tweet_cve_analysis=True, tweet_analysis=True, cve_analysis=True)
            print('Creating model for cve...')
            model.create_model()
            model.find_similarity(start_date)
        else:
            current_date = datetime.now()
            print('No cve founds in tweets from {} to {}'.format(start_date.strftime("%d-%m-%Y"),
                                                                 current_date.strftime("%d-%m-%Y")))

    else:
        print("There aren't tweets to analyze with {}".format(start_date.strftime("%d-%m-%Y")))
