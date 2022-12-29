import os
import re
import subprocess

import cve
import tweet
import model
import config
import preprocessing

from tqdm import tqdm
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

cve_regex = cve.build_regex()


def start_analysis(start_date, end_date):
    filtered_check, new_start_date, new_end_date = tweet.check_filtered_tweets(start_date, end_date)
    if filtered_check == config.FILES_OK:
        check_files_consistency(start_date, end_date)
        processed_tweet_cve_check, new_proc_t_start_date, new_proc_t_end_date = \
            tweet.check_processed_tweets_cve(start_date, end_date)
        processed_tweet_check, new_proc_start_date, new_proc_end_date = tweet.check_processed_tweets(start_date,
                                                                                                     end_date)
        processed_cve_check, missing_cves = cve.check_processed_cves()
        if processed_tweet_cve_check != config.FILES_OK:
            if processed_tweet_cve_check == config.WRONG_S_DATE:
                preprocessing.preprocess_tweets_cve(start_date, new_proc_t_end_date)
            elif processed_tweet_cve_check == config.WRONG_E_DATE:
                preprocessing.preprocess_tweets_cve(new_proc_t_start_date, end_date)
            else:
                subprocess.call(['sh', './clean_processed_data.sh'] + [config.TWEET_CVE])
                preprocessing.preprocess_tweets_cve(start_date, end_date)

        if processed_tweet_check != config.FILES_OK:
            if processed_tweet_check == config.WRONG_S_DATE:
                preprocessing.preprocess_tweets(start_date, new_proc_end_date)
            elif processed_tweet_check == config.WRONG_E_DATE:
                preprocessing.preprocess_tweets(new_proc_start_date, end_date)
            else:
                subprocess.call(['sh', './clean_processed_data.sh'] + [config.TWEET])
                preprocessing.preprocess_tweets(start_date, end_date)

        if processed_cve_check == config.NO_FILES:
            preprocessing.preprocess_cves()
        elif processed_cve_check == config.MISSING_CVES:
            preprocessing.preprocess_cves(cve_files=missing_cves)

        tweet_cve = tweet.import_processed_tweet_cve()
        if model.check_model(tweet_cve):
            if model.check_results(start_date):
                print("Results for {} are in data/results".format(start_date.strftime("%d-%m-%Y")))
            else:
                model.find_similarity(start_date)
        else:
            model.create_model()
    else:

        # set the analysis start and end date based on which file is present
        if filtered_check == config.WRONG_S_DATE:
            get_tweets_with_cve(start_date, new_end_date)
        elif filtered_check == config.WRONG_E_DATE:
            get_tweets_with_cve(new_start_date, end_date)
        else:

            # if there are no filtered tweets based on the given dates remove all files
            subprocess.call(['sh', './clean_data.sh'])
            subprocess.call(['sh', './clean_processed_data.sh'] + [config.ALL_PROCESSED_DATA])
            get_tweets_with_cve(start_date, end_date)


def get_tweets_with_cve(start_date, end_date):
    files = check_files(start_date, end_date)
    if len(files) > 0:
        print("Analyzing tweets...")
        tweets_cves = []
        tweets_found = []
        tweets_indexes = []
        cves = []
        with ThreadPoolExecutor() as pool:
            for f in files:
                for index, t in tqdm(enumerate(tweet.import_local_tweets(f))):
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
            preprocessing.preprocess_tweets(start_date, end_date)
            preprocessing.preprocess_tweets_cve(start_date, end_date)
            print('Creating model for cve...')
            model.create_model()
            model.find_similarity(start_date)
        else:
            current_date = datetime.now()
            print('No cve founds in tweets from {} to {}'.format(start_date.strftime(config.DATE_FORMAT),
                                                                 current_date.strftime(config.DATE_FORMAT)))

    else:
        print("There aren't tweets to analyze with {}".format(start_date.strftime(config.DATE_FORMAT)))


def check_files(start_date, end_date):
    tweet_directory = os.listdir(config.TWEET_PATH)
    if len(tweet_directory) > 0:
        files = tweet.get_temp_window_files(start_date, end_date, config.TWEET_PATH)

        # check for tweets that match an end date, otherwise download tweets from the last available date to the
        # tweets with the indicated end date
        if not tweet.is_date_valid(files[0].split('.')[0], 3, start_date=start_date):
            tweet.get_tweets(start_date, datetime.strptime(files[0].split('.')[0], config.DATE_FORMAT))
            files = tweet.get_temp_window_files(start_date, end_date, config.TWEET_PATH)

        # check for tweets that match an end date, otherwise download tweets from the last available date to the
        # tweets with the indicated end date
        if not tweet.is_date_valid(files[len(files) - 1].split('.')[0], 3, start_date=end_date):
            tweet.get_tweets(datetime.strptime(files[len(files) - 1].split('.')[0], config.DATE_FORMAT), end_date)
            files = tweet.get_temp_window_files(start_date, end_date, config.TWEET_PATH)
    else:
        tweet.get_tweets(start_date, end_date)
        files = tweet.get_temp_window_files(start_date, end_date, config.TWEET_PATH)

    return files


# check if any cve have been downloaded, if they are present check the latest available cve and if so download
# the missing ones
def check_files_consistency(start_date, end_date):
    cve_files = os.listdir(config.CVE_PATH)

    cves_id = []
    files = tweet.get_temp_window_files(start_date, end_date, config.FILTERED_TWEET_PATH)
    for file in files:
        for t in tweet.import_filtered_tweets(file):
            result = re.findall(cve_regex, t['text'], re.I)
            if len(result) > 0:
                result = list(set(result))
                cves_id += result

    if len(cve_files) == 0:
        cve.retrieve_cves(cves_id)
    else:
        missing_cves = list(set(cves_id).difference(set(cve_files)))
        if len(missing_cves) > 0:
            cve.retrieve_cves(missing_cves)
