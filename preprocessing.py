import re
import nltk
import tweet
import gensim

from tqdm import tqdm
from datetime import datetime
from nltk.corpus import stopwords
from nltk.tokenize import TweetTokenizer
from concurrent.futures import ThreadPoolExecutor
from langdetect import detect, LangDetectException

MAX_TWEET = 1000
URL_REGEX = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
lemmatizer = nltk.stem.WordNetLemmatizer()
w_tokenizer = TweetTokenizer()


def preprocess_data(start_date, tweet_cve_analysis=False, tweet_analysis=False):
    try:
        nltk.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet')
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

    if tweet_cve_analysis:
        preprocess_tweets_cve(start_date)
    if tweet_analysis:
        preprocess_tweets(start_date)


def preprocess_tweets_cve(start_date):
    print('Cleaning text of tweets with cve...')
    tweets_with_cve = []
    tweet_cve_files = tweet.get_temp_window_tweets(start_date)
    tweet_cve_files.sort(key=lambda date: datetime.strptime(date.split('.')[0], '%d-%m-%Y'))
    with ThreadPoolExecutor() as pool:
        for idx, file in enumerate(tweet_cve_files):
            for content in tqdm(tweet.import_filtered_tweets(file)):
                content['parsed_text'] = pool.submit(clean_tweet_text, content['text']).result()
                if len(content['parsed_text']) > 0:
                    tweets_with_cve.append(content)
            tweet.export_processed_tweets(tweet_cve_files[idx], tweets_with_cve, cve=True)
            tweets_with_cve = []


def preprocess_tweets(start_date):
    print('Cleaning text of tweets...')
    tweets = []
    tweet_files = tweet.get_temp_window_files(start_date)
    tweet_files.sort(key=lambda date: datetime.strptime(date.split('.')[0], '%d-%m-%Y'))
    with ThreadPoolExecutor() as pool:
        for file in tweet_files:
            for index, content in enumerate(tqdm(tweet.import_local_tweets(file))):
                actual_tweet = {'index': index,
                                'id': content['id'],
                                'parsed_text': pool.submit(clean_tweet_text, content['text']).result()}
                if len(actual_tweet['parsed_text']) > 0:
                    tweets.append(actual_tweet)
                if len(tweets) > MAX_TWEET:
                    tweet.export_processed_tweets(file.split('.')[0], tweets, cve=None)
                    tweets = []
            if len(tweets) > 0:
                tweet.export_processed_tweets(file.split('.')[0], tweets, cve=None)
                tweets = []


def clean_tweet_text(text):
    all_words = []
    try:
        language = detect(text)
        if language == 'en':
            processed_text = text.lower()

            # remove the url present in the text
            processed_text = re.sub(URL_REGEX, '', processed_text)

            # remove mentions of Twitter accounts (eg. @username)
            processed_text = re.sub(r'@\w+', '', processed_text)

            processed_text = re.sub('[^a-zA-Z]', ' ', processed_text)
            processed_text = re.sub(r'\s+', ' ', processed_text)

            # remove duplicate consecutive words
            processed_text = re.sub(r'\b(\w+)( \1\b)+', r'\1', processed_text)
            all_words = [word for word in w_tokenizer.tokenize(processed_text)]
            stop_words = set(stopwords.words('english'))
            for i, word in enumerate(all_words):
                if word not in stop_words:
                    all_words[i] = word
    except LangDetectException:
        pass

    return all_words


def clean_cve_text(text):
    words = gensim.utils.simple_preprocess(text)
    return sorted(set(words), key=words.index)
