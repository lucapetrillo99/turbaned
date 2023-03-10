import os
import json

import model
import pickle
import config
import multiprocessing

from gensim.models.doc2vec import Doc2Vec
from concurrent.futures import ThreadPoolExecutor

train_data = {}
val_data = []
file_chunk = None

vector_size = []
epochs = []
min_count = []
negative = []
dbow_windows = []
dm_windows = []


def set_parameters(f_chunk):
    global train_data, val_data, vector_size, epochs, min_count, negative, dbow_windows, dm_windows

    try:
        h_file = open(config.HYPERPARAMETERS_PATH, 'rb')
        data = json.load(h_file)
        vector_size = data['vector_size']
        epochs = data['epochs']
        min_count = data['min_count']
        negative = data['negative']
        dbow_windows = data['dbow_windows']
        dm_windows = data['dm_windows']

        train_data_file = os.path.join(config.TRAIN_DATA_PATH, f_chunk)
        file = open(train_data_file, 'rb')
        train_data = pickle.load(file)

        validation_data_file = os.path.join(config.VALIDATION_DATA_PATH, f_chunk)
        val_file = open(validation_data_file, 'rb')
        val_data = pickle.load(val_file)
    except FileNotFoundError as e:
        print(e)
        exit(0)


def tuning_models(f_chunk):
    set_parameters(f_chunk)
    dbow_results = []
    dm_results = []
    cores = multiprocessing.cpu_count()

    for i in range(len(vector_size)):
        dbow_params = {'vector_size': vector_size[i], 'window': dbow_windows[i], 'epochs': epochs[i],
                       'min_count': min_count[i], 'negative': negative[i]}

        dm_params = {'vector_size': vector_size[i], 'window': dm_windows[i], 'epochs': epochs[i],
                     'min_count': min_count[i], 'negative': negative[i]}

        model_dbow = Doc2Vec([x['document'] for x in train_data.values()],
                             dm=0,
                             vector_size=dbow_params['vector_size'],
                             window=dbow_params['window'],
                             epochs=dbow_params['epochs'],
                             min_count=dbow_params['min_count'],
                             negative=dbow_params['negative'],
                             hs=0, workers=cores)

        model_dmm = Doc2Vec([x['document'] for x in train_data.values()],
                            dm=1,
                            dm_mean=1,
                            vector_size=dm_params['vector_size'],
                            window=dm_params['window'],
                            epochs=dm_params['epochs'],
                            min_count=dm_params['min_count'],
                            negative=dm_params['negative'],
                            hs=0, workers=cores)

        dbow, dm = model.evaluate_models(f_chunk, print_results=False, dbow_model=model_dbow, dm_model=model_dmm)
        dbow['params'] = dbow_params
        dm['params'] = dm_params

        dbow_results.append(dbow)
        dm_results.append(dm)

        with open(os.path.join(config.HYPERPARAMETERS_RESULTS_PATH, "dbow_" + f_chunk + ".json"), "w") as dbow_file:
            json.dump(dbow_results, dbow_file, indent=2)

        with open(os.path.join(config.HYPERPARAMETERS_RESULTS_PATH, "dm_" + f_chunk + ".json"), "w") as dm_file:
            json.dump(dm_results, dm_file, indent=2)

    return dbow_results, dm_results


def start_tuning(start, end):
    global file_chunk
    file_chunk = start.strftime(config.DATE_FORMAT) + "_" + end.strftime(config.DATE_FORMAT)

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

    with open(os.path.join(config.MODEL_PATH, "hyperparameters"), "wb") as f:
        pickle.dump(best_res, f)

    print(f"BEST DBOW ACCURACY: {dbow_res[dbow_best]['accuracy']}, PARAMS: {dbow_res[dbow_best]['params']}")
    print(f"BEST DM ACCURACY: {dm_res[dm_best]['accuracy']}, PARAMS: {dm_res[dm_best]['params']}")
