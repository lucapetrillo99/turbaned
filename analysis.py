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
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor

cve_regex = cve.build_regex()


def start_analysis(start_date, end_date):
    filtered_check, new_start_date, new_end_date = tweet.check_files_dates(start_date, end_date,
                                                                           config.FILTERED_TWEET_PATH)
    if filtered_check == config.FILES_OK:
        check_files_consistency(start_date, end_date)
        processed_tweet_cve_check, new_proc_t_start_date, new_proc_t_end_date = \
            tweet.check_files_dates(start_date, end_date, config.PROCESSED_TWEET_CVE_PATH)
        processed_tweet_check, new_proc_start_date, new_proc_end_date = tweet.check_files_dates(start_date, end_date,
                                                                                                config.PROCESSED_TWEET_PATH)
        processed_cve_check, missing_cves = cve.check_processed_cves()
        if processed_tweet_cve_check != config.FILES_OK:
            if processed_tweet_cve_check == config.WRONG_S_DATE:
                preprocessing.preprocess_tweets_cve(start_date, new_proc_t_end_date)
            elif processed_tweet_cve_check == config.WRONG_E_DATE:
                preprocessing.preprocess_tweets_cve(new_proc_t_start_date, end_date)
            else:
                subprocess.run([config.CLEAN_PROCESSED_DATA, config.TWEET_CVE])
                preprocessing.preprocess_tweets_cve(start_date, end_date)

        if processed_tweet_check != config.FILES_OK:
            if processed_tweet_check == config.WRONG_S_DATE:
                preprocessing.preprocess_tweets(start_date, new_proc_end_date)
            elif processed_tweet_check == config.WRONG_E_DATE:
                preprocessing.preprocess_tweets(new_proc_start_date, end_date)
            else:
                subprocess.run([config.CLEAN_PROCESSED_DATA, config.TWEET])
                preprocessing.preprocess_tweets(start_date, end_date)

        if processed_cve_check == config.NO_FILES:
            preprocessing.preprocess_cves()
        elif processed_cve_check == config.MISSING_CVES:
            preprocessing.preprocess_cves(cve_files=missing_cves)

        if model.check_data(start_date, end_date):
            if model.check_model(start_date, end_date):
                print("All set! Proceed with the hyperparameters tuning step.")
            else:
                model.create_models(start_date, end_date)
        else:
            model.split_dataset(start_date, end_date)
            if model.check_model(start_date, end_date):
                print("All set! Proceed with the hyperparameters tuning step.")
            else:
                model.create_models(start_date, end_date)
    else:

        # set the analysis start and end date based on which file is present
        if filtered_check == config.WRONG_S_DATE:
            get_tweets_with_cve(start_date, new_end_date)
        elif filtered_check == config.WRONG_E_DATE:
            get_tweets_with_cve(new_start_date, end_date)
        else:

            # if there are no filtered tweets based on the given dates remove all files
            subprocess.run(config.CLEAN_DATA)
            subprocess.run([config.CLEAN_PROCESSED_DATA, config.ALL_PROCESSED_DATA])
            get_tweets_with_cve(start_date, end_date)


def get_tweets_with_cve(start_date, end_date):
    files = check_files(start_date, end_date)
    if len(files) > 0:
        print("Analyzing tweets...")
        tweets_cves = []
        tweets_found = []
        tweets_indexes = []
        cve_ref = {}
        cve_index = 0
        with ThreadPoolExecutor() as pool:
            for f in files:
                for index, t in enumerate(tqdm(tweet.import_local_tweets(f))):

                    # check if tweet contains the keyword: CVE-ID (eg. CVE-2022-1536)
                    result = re.findall(cve_regex, t['text'], re.I)
                    if len(result) == 1:
                        if result[0] not in cve_ref:
                            cve_ref[result[0]] = cve_index
                            cve_index += 1
                        tweets_indexes.append(index)
                        t['tag'] = result[0]
                        tweets_cves.append(t)
                if len(tweets_indexes) > 0:
                    tweets_found.append({f: tweets_indexes})
                    tweets_indexes = []
                if len(tweets_cves) > 0:
                    pool.submit(tweet.export_filtered_tweets(filename=f.split(".")[0], filtered_tweets=tweets_cves))
                    tweets_cves = []
        if len(tweets_found) > 0:
            cve.export_cve_references(cve_ref, start_date, end_date)
            tweet.remove_tweets_with_cve(tweets_found)
            cve.retrieve_cves(start_date, end_date)
            preprocessing.preprocess_tweets(start_date, end_date)
            preprocessing.preprocess_tweets_cve(start_date, end_date)
            preprocessing.preprocess_cves()
            model.create_models(start_date, end_date)
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
        if len(files) > 0:

            # check for tweets that match an end date, otherwise download tweets from the last available date to the
            # tweets with the indicated end date
            if not tweet.is_date_valid(files[0].split('.')[0], config.EQUAL, start_date=start_date):
                tweet.get_tweets(start_date, datetime.strptime(files[0].split('.')[0], config.DATE_FORMAT))
                files = tweet.get_temp_window_files(start_date, end_date, config.TWEET_PATH)

            # check for tweets that match an end date, otherwise download tweets from the last available date to the
            # tweets with the indicated end date
            if not tweet.is_date_valid(files[len(files) - 1].split('.')[0], config.EQUAL, start_date=end_date):
                new_start_date = datetime.strptime(files[len(files) - 1].split('.')[0], config.DATE_FORMAT) \
                                 + relativedelta(days=1)
                tweet.get_tweets(new_start_date, end_date)
                files = tweet.get_temp_window_files(start_date, end_date, config.TWEET_PATH)
        else:
            subprocess.run(config.CLEAN_TWEETS)
            tweet.get_tweets(start_date, end_date)
            files = tweet.get_temp_window_files(start_date, end_date, config.TWEET_PATH)
    else:
        tweet.get_tweets(start_date, end_date)
        files = tweet.get_temp_window_files(start_date, end_date, config.TWEET_PATH)

    return files


# check if any cve have been downloaded, if they are present check the last available cve and if so download
# the missing ones, otherwise the process starts from scratch
def check_files_consistency(start_date, end_date):
    cve_ref_filename = start_date.strftime(config.DATE_FORMAT) + "_" + end_date.strftime(config.DATE_FORMAT)

    if cve_ref_filename in os.listdir(config.CVE_REFERENCES_PATH):
        cve_files = os.listdir(config.CVE_PATH)
        cves = list(cve.import_cve_references(start_date, end_date).keys())
        if len(cve_files) == 0:
            cve.retrieve_cves(start_date, end_date, cves=cves)
        else:
            missing_cves = list(set(cves).difference(set(cve_files)))
            if len(missing_cves) > 0:
                cve.retrieve_cves(start_date, end_date, cves=missing_cves)
    else:
        subprocess.run(config.CLEAN_DATA)
        subprocess.run(config.CLEAN_TWEETS)
        get_tweets_with_cve(start_date, end_date)
