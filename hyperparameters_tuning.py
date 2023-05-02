import os
import json
import random

import model
import pickle
import config
import itertools
import multiprocessing

from gensim.models.doc2vec import Doc2Vec
from concurrent.futures import ThreadPoolExecutor

train_data = {}
val_data = []
file_chunk = None


def set_parameters(f_chunk):
    global train_data, val_data

    try:
        h_file = open(config.HYPERPARAMETERS_PATH, 'rb')
        data = json.load(h_file)
        dbow_vector_size = data['dbow_vector_size']
        dm_vector_size = data['dm_vector_size']
        dbow_epochs = data['dbow_epochs']
        dm_epochs = data['dm_epochs']
        dbow_min_count = data['dbow_min_count']
        dm_min_count = data['dm_min_count']
        dbow_negative = data['dbow_negative']
        dm_negative = data['dm_negative']
        dbow_windows = data['dbow_windows']
        dm_windows = data['dm_windows']
        dbow_sample = data['dbow_sample']
        dm_sample = data['dm_sample']
        hs = data['hs']

        dbow_params = [{'vector_size': item[0],
                        'window': item[1],
                        'epochs': item[2],
                        'min_count': item[3],
                        'negative': item[4],
                        'hs': item[5],
                        'sample': item[6]
                        } for item in
                       list(itertools.product(*[dbow_vector_size,
                                                dbow_windows,
                                                dbow_epochs,
                                                dbow_min_count,
                                                dbow_negative,
                                                hs,
                                                dbow_sample]))
                       ]

        dm_params = [{'vector_size': item[0],
                      'window': item[1],
                      'epochs': item[2],
                      'min_count': item[3],
                      'negative': item[4],
                      'hs': item[5],
                      'sample': item[6]
                      } for item in
                     list(itertools.product(*[dm_vector_size,
                                              dm_windows,
                                              dm_epochs,
                                              dm_min_count,
                                              dm_negative,
                                              hs,
                                              dm_sample]))
                     ]

        train_data_file = os.path.join(config.TRAIN_DATA_PATH, f_chunk)
        file = open(train_data_file, 'rb')
        train_data = pickle.load(file)

        validation_data_file = os.path.join(config.VALIDATION_DATA_PATH, f_chunk)
        val_file = open(validation_data_file, 'rb')
        val_data = pickle.load(val_file)

        return dbow_params, dm_params
    except FileNotFoundError as e:
        print(e)
        exit(0)


def tuning_models(f_chunk):
    dbow_params, dm_params = set_parameters(f_chunk)
    dbow_results = []
    dm_results = []
    cores = multiprocessing.cpu_count()

    dbow_random_choices = random.sample(dbow_params, 10)
    dm_random_choices = random.sample(dm_params, 10)

    for dbow_param, dm_param in zip(dbow_random_choices, dm_random_choices):
        if dbow_param['hs'] == 1:
            dbow_param['negative'] = 0
        if dm_param['hs'] == 1:
            dm_param['negative'] = 0

        print(dbow_param, dm_param)

        model_dbow = Doc2Vec([x['document'] for x in train_data.values()],
                             dm=0,
                             vector_size=dbow_param['vector_size'],
                             window=dbow_param['window'],
                             epochs=dbow_param['epochs'],
                             min_count=dbow_param['min_count'],
                             negative=dbow_param['negative'],
                             hs=dbow_param['hs'], workers=cores)

        model_dm = Doc2Vec([x['document'] for x in train_data.values()],
                           dm=1,
                           dm_mean=1,
                           vector_size=dm_param['vector_size'],
                           window=dm_param['window'],
                           epochs=dm_param['epochs'],
                           min_count=dm_param['min_count'],
                           negative=dm_param['negative'],
                           hs=dm_param['hs'], workers=cores)

        dbow, dm = model.evaluate_models(f_chunk, print_results=False, dbow_model=model_dbow, dm_model=model_dm)
        dbow['params'] = dbow_param
        dm['params'] = dm_param

        dbow_results.append(dbow)
        dm_results.append(dm)

        with open(os.path.join(config.HYPERPARAMETERS_RESULTS_PATH, "dbow_" + f_chunk + ".json"), "w") as dbow_file:
            json.dump(dbow_results, dbow_file, indent=2)

        with open(os.path.join(config.HYPERPARAMETERS_RESULTS_PATH, "dm_" + f_chunk + ".json"), "w") as dm_file:
            json.dump(dm_results, dm_file, indent=2)

    return dbow_results, dm_results


def hyperparameters_tuning(start, end):
    global file_chunk
    file_chunk = config.filename_chunk.format(start.strftime(config.DATE_FORMAT),
                                                end.strftime(config.DATE_FORMAT))

    try:
        os.mkdir(config.HYPERPARAMETERS_RESULTS_PATH)
    except FileExistsError:
        pass

    with ThreadPoolExecutor() as executor:
        dbow_res, dm_res = executor.submit(tuning_models, file_chunk).result()

    dbow_best = max(range(len(dbow_res)), key=lambda index: dbow_res[index]['accuracy'])
    dm_best = max(range(len(dm_res)), key=lambda index: dm_res[index]['accuracy'])

    best_res = {}
    if dbow_res[dbow_best]['accuracy'] > dm_res[dm_best]['accuracy']:
        best_res['model'] = 'dbow'
        best_res['params'] = dbow_res[dbow_best]['params']
    else:
        best_res['model'] = 'dm'
        best_res['params'] = dm_res[dm_best]['params']

    with open(config.HYPERPARAMETERS_FOUND, "wb") as f:
        pickle.dump(best_res, f)

    print(f"BEST DBOW ACCURACY: {dbow_res[dbow_best]['accuracy']}, PARAMS: {dbow_res[dbow_best]['params']}")
    print(f"BEST DM ACCURACY: {dm_res[dm_best]['accuracy']}, PARAMS: {dm_res[dm_best]['params']}")
