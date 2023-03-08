import os
import cve
import json
import pickle

import tweet
import config
import numpy as np
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
    train = []
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

    # division of data into train, test and validation set (80%, 10%, 10%)
    for k in cve_index.keys():
        if len(cve_index[k]) == 1:
            train += cve_index[k]
        else:
            cve_index[k] = utils.shuffle(cve_index[k])
            train_len = round(len(cve_index[k]) * 0.8)
            val_len = round(len(cve_index[k]) * 0.1)

            train += cve_index[k][:train_len]
            validation_data += cve_index[k][train_len:train_len + val_len]
            test_data += cve_index[k][train_len + val_len:]

    train_data = {}
    for i, tr in enumerate(train):
        tr['document'] = TaggedDocument(tr['parsed_text'], [i])
        train_data[i] = tr

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

    model_dbow.build_vocab([x['document'] for x in train_data.values()])

    # save some time by copying the vocabulary structures from the DBOW model to the DM model
    model_dm.reset_from(model_dbow)

    model_dbow.train([x['document'] for x in train_data.values()], total_examples=model_dbow.corpus_count,
                     epochs=model_dbow.epochs, report_delay=30 * 60)
    model_dm.train([x['document'] for x in train_data.values()], total_examples=model_dm.corpus_count,
                   epochs=model_dm.epochs, report_delay=30 * 60)

    filename = start_date.strftime(config.DATE_FORMAT) + "_" + end_date.strftime(config.DATE_FORMAT)
    model_dbow.save(os.path.join(config.MODEL_PATH, config.MODEL_DBOW_BASE + '_' + filename + '.model'))
    model_dm.save(os.path.join(config.MODEL_PATH, config.MODEL_DM_BASE + '_' + filename + '.model'))

    file.close()

    evaluate_models(filename, False, True)


def evaluate_models(f_name_chunk, test_eval, print_results, dbow_model=None, dm_model=None):
    if dbow_model is None and dm_model is None:
        model_dbow = Doc2Vec.load(os.path.join(config.MODEL_PATH, config.MODEL_DBOW_BASE + "_" + f_name_chunk
                                               + '.model'))
        model_dmm = Doc2Vec.load(os.path.join(config.MODEL_PATH, config.MODEL_DM_BASE + "_" + f_name_chunk + '.model'))
    else:
        model_dbow = dbow_model
        model_dmm = dm_model

    if test_eval:
        filename = os.path.join(config.TEST_DATA_PATH, f_name_chunk)
    else:
        filename = os.path.join(config.VALIDATION_DATA_PATH, f_name_chunk)

    file = open(filename, 'rb')
    data = pickle.load(file)

    dbow_results = []
    dm_results = []
    dbow_scores = []
    dm_scores = []

    for d in data:
        dbow_vector = model_dbow.infer_vector(d['parsed_text'])
        dmm_vector = model_dmm.infer_vector(d['parsed_text'])

        dbow_result = model_dbow.dv.most_similar(dbow_vector, topn=1)
        dmm_result = model_dmm.dv.most_similar(dmm_vector, topn=1)

        dbow_element = {'predicted_tweet_id': dbow_result[0][0], 'source_tag': d['tag'],
                        'score': dbow_result[0][1]}
        dbow_results.append(dbow_element)
        dbow_scores.append(dbow_result[0][1])

        dmm_element = {'predicted_tweet_id': dmm_result[0][0], 'source_tag': d['tag'],
                       'score': dmm_result[0][1]}
        dm_results.append(dmm_element)
        dm_scores.append(dmm_result[0][1])

    dbow_positives, dm_positives = get_results(f_name_chunk, dbow_results, dm_results)

    if print_results:
        print(f"DBOW ACCURACY: {dbow_positives / len(data)}")
        print(f"DM ACCURACY: {dm_positives / len(data)}")
        print(f"DBOW POSITIVES: {dbow_positives}")
        print(f"DM POSITIVES: {dbow_positives}")
        print(f"TOTAL: {len(data)}")
        print(f"DBOW MEAN SCORE: {np.mean(dbow_scores)}")
        print(f"DM MEAN SCORE: {np.mean(dm_scores)}")
    else:
        dbow = {"accuracy": dbow_positives / len(data), "positives": dbow_positives, "mean_score": np.mean(dbow_scores)}
        dm = {"accuracy": dm_positives / len(data), "positives": dm_positives, "mean_score": np.mean(dm_scores)}

        return dbow, dm


def get_results(f_chunk, dbow_results, dm_results):
    filename = os.path.join(config.TRAIN_DATA_PATH, f_chunk)
    file = open(filename, 'rb')
    train_data = pickle.load(file)

    dbow_positives = 0
    dm_positives = 0

    for db_res, dm_res in zip(dbow_results, dm_results):
        if db_res['source_tag'] == train_data[db_res['predicted_tweet_id']]['tag']:
            dbow_positives += 1

        if dm_res['source_tag'] == train_data[dm_res['predicted_tweet_id']]['tag']:
            dm_positives += 1

    return dbow_positives, dm_positives


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
