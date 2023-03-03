import os
import json
import pickle

import config
import cve
import tweet
import multiprocessing

from tqdm import tqdm
from sklearn import utils
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


def split_dataset(start_date, end_date):
    cve_index = {}
    train_data = []
    test_data = []
    validation_data = []

    for file in tweet.get_temp_window_files(start_date, end_date, config.PROCESSED_TWEET_CVE_PATH):
        for index, content in enumerate(tweet.import_processed_tweet_cve_content(file)):
            element = {"type": "t", "file": file, 'index': index, 'tag': content['tag'],
                       'parsed_text': content['parsed_text']}

            if content['tag'] in cve_index:
                cve_index[content['tag']].append(element)
            else:
                cve_index[content['tag']] = [element]

    for f_name in cve.import_cve_files():
        cve_content = cve.import_processed_cve(f_name)
        element = {"type": "c", "file": f_name, 'tag': cve_content['id'], 'parsed_text': cve_content['parsed_text']}

        if cve_content['id'] in cve_index:
            cve_index[cve_content['id']].append(element)
        else:
            cve_index[cve_content['id']] = [element]

    # division of data into train and test (80%, 10%, 10%)
    for k in cve_index.keys():
        if len(cve_index[k]) == 1:
            train_data += cve_index[k]
        else:
            cve_index[k] = utils.shuffle(cve_index[k])
            train_len = round(len(cve_index[k]) * 0.8)
            val_len = round(len(cve_index[k]) * 0.1)

            train_data += cve_index[k][:train_len]
            validation_data += cve_index[k][train_len:train_len + val_len]
            test_data += cve_index[k][train_len + val_len:]

    i = 0
    for tr in train_data:
        tr['id'] = i
        tr['document'] = TaggedDocument(tr['parsed_text'], [i])
        i += 1

    for te in test_data:
        te['id'] = i
        te['document'] = TaggedDocument(te['parsed_text'], [i])
        i += 1

    for v in validation_data:
        v['id'] = i
        v['document'] = TaggedDocument(v['parsed_text'], [i])
        i += 1

    filename = start_date.strftime(config.DATE_FORMAT) + "_" + end_date.strftime(config.DATE_FORMAT)
    export_dataset(config.TRAIN_DATA_PATH, filename, train_data)
    export_dataset(config.TEST_DATA_PATH, filename, test_data)
    export_dataset(config.VALIDATION_DATA_PATH, filename, validation_data)


def create_models(start_date, end_date):
    print('Creating models ...')

    split_dataset(start_date, end_date)
    filename = os.path.join(config.TRAIN_DATA_PATH,
                            start_date.strftime(config.DATE_FORMAT) + "_" + end_date.strftime(config.DATE_FORMAT))
    file = open(filename, 'rb')
    train_data = pickle.load(file)
    cores = multiprocessing.cpu_count()

    model_dbow = Doc2Vec(dm=0, window=4, workers=cores, **config.common_kwargs)
    model_dm = Doc2Vec(dm=1, dm_mean=1, window=1, workers=cores, **config.common_kwargs)

    model_dbow.build_vocab([x['document'] for x in train_data])

    # save some time by copying the vocabulary structures from the DBOW model to the DM model
    model_dm.reset_from(model_dbow)

    model_dbow.train([x['document'] for x in train_data], total_examples=model_dbow.corpus_count,
                     epochs=model_dbow.epochs, report_delay=30 * 60)
    model_dm.train([x['document'] for x in train_data], total_examples=model_dm.corpus_count,
                    epochs=model_dm.epochs, report_delay=30 * 60)

    filename = start_date.strftime(config.DATE_FORMAT) + "_" + end_date.strftime(config.DATE_FORMAT)
    model_dbow.save(os.path.join(config.MODEL_PATH, config.MODEL_DBOW_BASE + '_' + filename + '.model'))
    model_dm.save(os.path.join(config.MODEL_PATH, config.MODEL_DM_BASE + '_' + filename + '.model'))

    file.close()


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


def export_dataset(path, filename, data):
    with open(path + filename, mode='wb') as f:
        pickle.dump(data, f)
