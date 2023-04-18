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
from langdetect import detect, LangDetectException
from gensim.models.doc2vec import Doc2Vec, TaggedDocument

MINIMUM_SCORE = 0.85
MAX_VALUES = 10000


def check_results(start_date, end_date):
    results = os.listdir(config.RESULTS_PATH)
    f_name_chunk = config.filename_chunk.format(start_date.strftime(config.DATE_FORMAT),
                                                end_date.strftime(config.DATE_FORMAT))
    return f_name_chunk + '.json' in results


def check_data(start, end):
    filename = config.filename_chunk.format(start.strftime(config.DATE_FORMAT),
                                            end.strftime(config.DATE_FORMAT))
    try:
        open(os.path.join(config.TRAIN_DATA_PATH, filename), "rb")
        return True
    except FileNotFoundError:
        return False


def check_model(start_date, end_date):
    filename = config.filename_chunk.format(start_date.strftime(config.DATE_FORMAT),
                                            end_date.strftime(config.DATE_FORMAT))
    try:
        Doc2Vec.load(os.path.join(config.MODEL_PATH, config.MODEL_DBOW_BASE.format(filename)))
        Doc2Vec.load(os.path.join(config.MODEL_PATH, config.MODEL_DM_BASE.format(filename)))
        return True
    except FileNotFoundError:
        return False


def split_dataset(start_date, end_date):
    cve_index = {}
    train = []
    test_data = []
    validation_data = []

    for file in tweet.get_temp_window_files(start_date, end_date, config.PROCESSED_TWEET_CVE_PATH):
        for index, content in enumerate(tweet.import_data(config.PROCESSED_TWEET_CVE_PATH, file)):
            element = {"type": "t", "file": file, 'index': index, 'tag': content['tag'],
                       'parsed_text': content['parsed_text']}

            if content['tag'] in cve_index:
                cve_index[content['tag']].append(element)
            else:
                cve_index[content['tag']] = [element]

    for f_name in cve.import_cve_files():
        cve_content = cve.import_cve_data(config.PROCESSED_CVE_PATH, f_name)
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

    filename = config.filename_chunk.format(start_date.strftime(config.DATE_FORMAT),
                                            end_date.strftime(config.DATE_FORMAT))
    export_dataset(config.TRAIN_DATA_PATH, filename, train_data)
    export_dataset(config.TEST_DATA_PATH, filename, test_data)
    export_dataset(config.VALIDATION_DATA_PATH, filename, validation_data)


def create_models(start_date, end_date):
    print('Creating models ...')

    split_dataset(start_date, end_date)
    filename_chunk = config.filename_chunk.format(start_date.strftime(config.DATE_FORMAT),
                                                  end_date.strftime(config.DATE_FORMAT))
    filename = os.path.join(config.TRAIN_DATA_PATH, filename_chunk)
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

    model_dbow.save(os.path.join(config.MODEL_PATH, config.MODEL_DBOW_BASE.format(filename_chunk)))
    model_dm.save(os.path.join(config.MODEL_PATH, config.MODEL_DM_BASE.format(filename_chunk)))

    file.close()

    evaluate_models(filename_chunk, print_results=True)


def evaluate_models(f_name_chunk, print_results, dbow_model=None, dm_model=None):
    if dbow_model is None and dm_model is None:
        model_dbow = Doc2Vec.load(os.path.join(config.MODEL_PATH, config.MODEL_DBOW_BASE.format(f_name_chunk)))
        model_dmm = Doc2Vec.load(os.path.join(config.MODEL_PATH, config.MODEL_DM_BASE.format(f_name_chunk)))
    else:
        model_dbow = dbow_model
        model_dmm = dm_model

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
        print("DBOW ACCURACY: {:.1%}".format(dbow_positives / len(data)))
        print("DM ACCURACY: {:.1%}".format(dbow_positives / len(data)))
        print(f"DBOW POSITIVES: {dbow_positives}")
        print(f"DM POSITIVES: {dm_positives}")
        print(f"TOTAL: {len(data)}")
        print(f"DBOW MEAN SCORE: {np.mean(dbow_scores)}")
        print(f"DM MEAN SCORE: {np.mean(dm_scores)}")
    else:
        dbow = {"accuracy": dbow_positives / len(data), "positives": dbow_positives, "mean_score": np.mean(dbow_scores)}
        dm = {"accuracy": dm_positives / len(data), "positives": dm_positives, "mean_score": np.mean(dm_scores)}

        return dbow, dm


def get_results(f_chunk, dbow_results, dm_results=None):
    filename = os.path.join(config.TRAIN_DATA_PATH, f_chunk)
    file = open(filename, 'rb')
    train_data = pickle.load(file)

    if dm_results:
        dbow_positives = 0
        dm_positives = 0
        for db_res, dm_res in zip(dbow_results, dm_results):
            if db_res['source_tag'] == train_data[db_res['predicted_tweet_id']]['tag']:
                dbow_positives += 1

            if dm_res['source_tag'] == train_data[dm_res['predicted_tweet_id']]['tag']:
                dm_positives += 1

        return dbow_positives, dm_positives

    else:
        positives = 0
        for res in dbow_results:
            if res['source_tag'] == train_data[res['predicted_tweet_id']]['tag']:
                positives += 1

        return positives


def create_model(start_date, end_date, target_model=None):
    model = None
    cores = multiprocessing.cpu_count()
    print('Creating model ...')

    try:
        filename_chunk = config.filename_chunk.format(start_date.strftime(config.DATE_FORMAT),
                                                      end_date.strftime(config.DATE_FORMAT))
        filename = os.path.join(config.TRAIN_DATA_PATH, filename_chunk)
        file = open(filename, 'rb')
        train_data = pickle.load(file)
    except FileNotFoundError as e:
        print(e)
        exit(0)

    if target_model:
        if target_model == 'dbow':
            model = Doc2Vec(dm=0, workers=cores, **config.common_kwargs)
        else:
            model = Doc2Vec(dm=1, dm_mean=1, workers=cores, **config.common_kwargs)
    else:
        try:
            with open(os.path.join(config.MODEL_PATH, "hyperparameters"), "rb") as f:
                results = pickle.load(f)

            if results['model'] == 'dbow':
                model = Doc2Vec(dm=0, workers=cores, **results['params'])
            else:
                model = Doc2Vec(dm=1, dm_mean=1, workers=cores, **results['params'])
        except FileNotFoundError as e:
            print(e)

    model.build_vocab([x['document'] for x in train_data.values()])
    model.train([x['document'] for x in train_data.values()], total_examples=model.corpus_count,
                epochs=model.epochs, report_delay=30 * 60)

    model.save(os.path.join(config.MODEL_PATH, config.FINAL_MODEL.format(filename_chunk)))
    file.close()

    evaluate_model(filename_chunk, model)


def evaluate_model(f_name_chunk, model):
    try:
        filename = os.path.join(config.TEST_DATA_PATH, f_name_chunk)
        file = open(filename, 'rb')
        data = pickle.load(file)
    except FileNotFoundError as e:
        print(e)
        exit(0)

    results = []
    scores = []

    for d in data:
        vector = model.infer_vector(d['parsed_text'])
        result = model.dv.most_similar(vector, topn=1)
        dbow_element = {'predicted_tweet_id': result[0][0], 'source_tag': d['tag'],
                        'score': result[0][1]}
        results.append(dbow_element)
        scores.append(result[0][1])

    positives = get_results(f_name_chunk, results)

    print("MODEL ACCURACY {:.1%}".format(positives / len(data)))
    print(f"POSITIVES: {positives}")
    print(f"TOTAL: {len(data)}")
    print(f"MODEL MEAN SCORE: {np.mean(scores)}")


# search for all the most similar tweets on which the model was trained
def find_similarity(start_date, end_date):
    if check_results(start_date, end_date):
        print("The results for the dates entered can be found in data/results folder")
    else:
        filename_chunk = config.filename_chunk.format(start_date.strftime(config.DATE_FORMAT),
                                                      end_date.strftime(config.DATE_FORMAT))
        model = Doc2Vec.load(os.path.join(config.MODEL_PATH, config.FINAL_MODEL.format(filename_chunk)))

        results = []
        for file in tweet.get_temp_window_files(start_date, end_date, config.PROCESSED_TWEET_PATH):
            print(file)
            for content in tqdm(tweet.import_data(config.PROCESSED_TWEET_PATH, file)):
                try:
                    language = detect(" ".join(content['parsed_text']))
                    if language == 'en':
                        infer_vector = model.infer_vector(content['parsed_text'])
                        model_result = model.dv.most_similar(infer_vector, topn=1)

                        # select all tweets above a threshold
                        if model_result[0][1] >= MINIMUM_SCORE:
                            result = {'predicted_tweet': model_result[0][0],
                                      'target_tweet': tweet.import_local_tweets(content['file'])[content['index']],
                                      'score': model_result[0][1]}
                            results.append(result)

                except LangDetectException:
                    pass

                if len(results) >= MAX_VALUES:
                    export_results(results, filename_chunk)
                    results = []

        if len(results) > 0:
            export_results(results, filename_chunk)

        print("Process finished. You can consult outputs in data/results folder")


def export_dataset(path, filename, data):
    with open(os.path.join(path, filename), mode='wb') as f:
        pickle.dump(data, f)


def export_results(results, filename_chunk):
    try:
        filename = os.path.join(config.TRAIN_DATA_PATH, filename_chunk)
        file = open(filename, 'rb')
        data = pickle.load(file)
    except FileNotFoundError as e:
        print(e)
        exit(0)

    for result in results:
        predicted_tweet = data[result['predicted_tweet']]
        result['CVE-ID'] = predicted_tweet['tag']
        if predicted_tweet['type'] == 't':
            result['predicted_tweet'] = tweet.import_data(config.PROCESSED_TWEET_CVE_PATH,
                                                          predicted_tweet['file'])[predicted_tweet['index']]
            del result['predicted_tweet']['parsed_text']
        else:
            result['predicted_tweet'] = cve.import_cve_data(config.PROCESSED_CVE_PATH, predicted_tweet['file'])
            del result['predicted_tweet']['parsed_text']

    filename = os.path.join(config.RESULTS_PATH, filename_chunk + '.json')
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                existing_data = json.load(f)
            except ValueError:
                existing_data = []
    else:
        existing_data = []

    with open(filename, 'w') as f:
        existing_data.extend(results)
        json.dump(existing_data, f, indent=2)
