import re
import nltk
import tweet

from tqdm import tqdm
from datetime import datetime
from nltk.corpus import stopwords
from concurrent.futures import ThreadPoolExecutor
from langdetect import detect, LangDetectException

MAX_TWEET = 1000
URL_REGEX = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'


def preprocess_data(temp_window, tweet_cve_analysis=False, tweet_analysis=False):
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

    tweets_with_cve = []
    tweets = []
    tweets_id = []

    temp_id = None
    if tweet_cve_analysis:
        print('Cleaning text of tweets with cve...')
        filtered_tweets = tweet.import_filtered_tweets(temp_window)
        for idx, filtered_tweet in enumerate(filtered_tweets):
            for content in filtered_tweet['content']:
                if idx == 0:
                    temp_id = content['id']
                content['parsed_text'] = clean_text(content['text'])
                tweets_with_cve.append(content)
                tweets_id.append(content['id'])
                if filtered_tweet['id'] != temp_id:
                    if len(tweets_with_cve) > 0:
                        tweet.export_processed_tweets(filtered_tweet['id'], tweets_with_cve, cve=True)
                        tweets_with_cve.clear()

                if idx == len(filtered_tweets) - 1:
                    if len(tweets_with_cve) > 0:
                        tweet.export_processed_tweets(filtered_tweet['id'], tweets_with_cve, cve=True)

    if tweet_analysis:
        print('Cleaning text of tweets...')
        tweet_files = tweet.get_temp_window_files(temp_window)
        tweet_files.sort(key=lambda date: datetime.strptime(date.split('.')[0], '%d%m%Y'))
        with ThreadPoolExecutor() as pool:
            for idx, file in enumerate(tweet_files):
                for content in tqdm(tweet.import_local_tweets(file)):
                    if content['id'] not in tweets_id:
                        content['parsed_text'] = pool.submit(clean_text, content['text']).result()
                        if len(content['parsed_text']) > 0:
                            tweets.append(content)
                        if len(tweets) > MAX_TWEET:
                            tweet.export_processed_tweets(tweet_files[idx], tweets, cve=None)
                            tweets.clear()


def clean_text(text):
    all_words = []
    try:
        language = detect(text)
        if language == 'en':
            processed_text = text.lower()

            # check if tweet's text contain a url and removes it
            urls = re.findall(URL_REGEX, processed_text)
            if len(urls) > 0:
                temp = [word for word in processed_text.split() if word not in urls]
                processed_text = ' '.join(temp)

            processed_text = re.sub('[^a-zA-Z]', ' ', processed_text)
            processed_text = re.sub(r'\s+', ' ', processed_text)
            all_sentences = nltk.sent_tokenize(processed_text)

            all_words = [nltk.word_tokenize(sent) for sent in all_sentences]
            stop_words = set(stopwords.words('english'))
            for i in range(len(all_words)):
                all_words[i] = [w for w in all_words[i] if w not in stop_words]
    except LangDetectException:
        pass

    return all_words
