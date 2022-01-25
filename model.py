import os
import json
import tweet

from tqdm import tqdm
from scipy.spatial import distance
from gensim.models.doc2vec import Doc2Vec, TaggedDocument

MODEL_PATH = 'data/models/'
RESULTS_PATH = 'data/results/'
MINIMUM_SCORE = 0.042


def check_results(start_date):
    results = os.listdir(RESULTS_PATH)
    return start_date.strftime("%d-%m-%Y") + '.json' in results


def check_model(tweets_cve):
    if len(os.listdir(MODEL_PATH)) > 0:
        flag = True
        for file in os.listdir(MODEL_PATH):
            if file.split('.')[0] not in tweets_cve:
                flag = False

        if not flag:
            for file in os.listdir(MODEL_PATH):
                os.remove(os.path.join(MODEL_PATH, file))

        return flag
    else:
        return False


def create_model():
    tweets_cve = tweet.import_processed_tweet_cve()
    for tweet_cve in tweets_cve:
        model = Doc2Vec(min_count=1, epochs=30)
        for content in tweet.import_processed_tweet_cve_content(tweet_cve):
            documents = [TaggedDocument(doc, [i]) for i, doc in enumerate(content['parsed_text'])]
            model.build_vocab(documents)
            model.train(documents, total_examples=model.corpus_count, epochs=model.epochs)

        model.save(MODEL_PATH + tweet_cve + '.model')


# find similarity between tweets with cve and a tweet
def find_similarity(start_date):
    results = []
    tweets_cve = tweet.import_processed_tweet_cve()
    tweet_files = tweet.get_temp_window_files(start_date)
    for filename in tweet_files:
        for tweet_content in tqdm(tweet.import_processed_tweet_content(filename)):
            sample_tweet = tweet_content
            for parsed_text in tweet_content['parsed_text']:
                for tweet_cve in tweets_cve:
                    model = Doc2Vec.load(MODEL_PATH + tweet_cve + '.model')
                    for content in tweet.import_processed_tweet_cve_content(tweet_cve):
                        target_tweet = content
                        for text in content['parsed_text']:
                            vec1 = model.infer_vector(text)
                            vec2 = model.infer_vector(parsed_text)
                            vector_distance = distance.euclidean(vec1, vec2)
                            if vector_distance < MINIMUM_SCORE:
                                distance_dict = {'target_tweet': target_tweet,
                                                 'sample_tweet': sample_tweet, 'score': vector_distance}
                                results.append(distance_dict)

        print('Found {} with minimum score'.format(len(results)))
        if len(results) > 0:
            results.sort(key=lambda item: item['score'], reverse=False)
            with open(RESULTS_PATH + filename, 'w') as file:
                json.dump(results, file)
            results.clear()

    print("Process finished. You can consult outputs in data/results folder")
