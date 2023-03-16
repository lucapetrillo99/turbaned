import os
import re

import cve
import nltk
import tweet
import config
import gensim

from tqdm import tqdm
from datetime import datetime
from nltk.tokenize import TweetTokenizer
from concurrent.futures import ThreadPoolExecutor
from langdetect import detect, LangDetectException

MAX_TWEET = 1000
URL_REGEX = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
CVE_PATH = 'data/cve/'
lemmatizer = nltk.stem.WordNetLemmatizer()
w_tokenizer = TweetTokenizer()
cve_regex = cve.build_regex()


def preprocess_tweets_cve(start_date, end_date):
    print('Cleaning text of tweets with cve...')
    tweets_with_cve = []
    tweet_cve_files = tweet.get_temp_window_files(start_date, end_date, config.FILTERED_TWEET_PATH)
    tweet_cve_files.sort(key=lambda date: datetime.strptime(date.split('.')[0], config.DATE_FORMAT))
    with ThreadPoolExecutor() as pool:
        for idx, file in enumerate(tweet_cve_files):
            for content in tqdm(tweet.import_data(config.FILTERED_TWEET_PATH, file)):
                content['parsed_text'] = pool.submit(clean_tweet_text, content['text']).result()
                if len(content['parsed_text']) > 0:
                    tweets_with_cve.append(content)
            tweet.export_processed_tweets(tweet_cve_files[idx], tweets_with_cve, cve=True)
            tweets_with_cve = []


def preprocess_tweets(start_date, end_date):
    print('Cleaning text of tweets...')
    tweets = []
    tweet_files = tweet.get_temp_window_files(start_date, end_date, config.TWEET_PATH)
    tweet_files.sort(key=lambda date: datetime.strptime(date.split('.')[0], '%d-%m-%Y'))
    with ThreadPoolExecutor() as pool:
        for file in tweet_files:
            for index, content in enumerate(tqdm(tweet.import_local_tweets(file))):
                actual_tweet = {'file': file, 'index': index, 'id': content['id'],
                                'parsed_text': pool.submit(clean_tweet_text, content['text']).result()}
                if len(actual_tweet['parsed_text']) > 0:
                    tweets.append(actual_tweet)
                if len(tweets) > MAX_TWEET:
                    tweet.export_processed_tweets(file.split('.')[0], tweets, cve=None)
                    tweets = []
            if len(tweets) > 0:
                tweet.export_processed_tweets(file.split('.')[0], tweets, cve=None)
                tweets = []


def preprocess_cves(cve_files=None):
    if cve_files is None:
        cve_files = os.listdir(config.CVE_PATH)

    with ThreadPoolExecutor() as pool:
        for file in tqdm(cve_files):
            content = cve.import_cve_data(config.CVE_PATH, file)
            content['parsed_text'] = pool.submit(clean_cve_text, content['description']).result()
            cve.export_processed_cve(content['id'], content)


def clean_tweet_text(text):
    final_words = []
    try:
        language = detect(text)
        if language == 'en':

            # remove the url present in the text
            text = re.sub(URL_REGEX, '', text)

            # remove mentions of Twitter accounts (eg. @username)
            text = re.sub(r'@\w+', '', text)

            text = re.sub(cve_regex, '', text)
            text = re.sub('[^a-zA-Z]', ' ', text)
            text = re.sub(r'\s+', ' ', text)

            # remove duplicate consecutive words
            text = re.sub(r'\b(\w+)( \1\b)+', r'\1', text)

            final_words = gensim.utils.simple_preprocess(text)

    except LangDetectException:
        pass

    return final_words


def clean_cve_text(text):
    new_text = ""
    for w in gensim.utils.simple_preprocess(text):
        new_text += w + " "

    # remove duplicate consecutive words
    new_text = re.sub(r'\b(\w+)( \1\b)+', r'\1', new_text)
    return [word for word in w_tokenizer.tokenize(new_text)]
