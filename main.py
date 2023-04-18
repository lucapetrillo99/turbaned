import os
import config
import argparse
import analysis
import model
import hyperparameters_tuning as hp

from datetime import datetime, timedelta


def check_inserted_dates(inserted_dates):
    try:
        inserted_dates[0] = datetime.strptime(inserted_dates[0], config.DATE_FORMAT)
        inserted_dates[1] = datetime.strptime(inserted_dates[1], config.DATE_FORMAT)
    except ValueError:
        print("Incorrect data format, should be DD-MM-YYYY, exiting...")
        exit(0)

    curr_date = datetime.now()
    if inserted_dates[0] > curr_date or inserted_dates[1] > curr_date:
        print("The date cannot be bigger than today, exiting...")
        exit(0)
    elif inserted_dates[0] > inserted_dates[1]:
        print("Wrong date order, exiting...")
        exit(0)
    else:
        s_date = inserted_dates[0]
        if inserted_dates[1].strftime(config.DATE_FORMAT) == curr_date.strftime(config.DATE_FORMAT):
            print("entro")
            e_date = curr_date - timedelta(days=1)
        else:
            e_date = inserted_dates[1]

    return s_date, e_date


def set_script_folders():
    if not (os.path.exists(config.DATA_PATH)):
        try:
            os.mkdir(config.DATA_PATH)
            os.mkdir(config.CVE_PATH)
            os.mkdir(config.TWEET_PATH)
            os.mkdir(config.FILTERED_TWEET_PATH)
            os.mkdir(config.CVE_REFERENCES_PATH)
            os.makedirs(config.PROCESSED_CVE_PATH)
            os.makedirs(config.PROCESSED_TWEET_PATH)
            os.makedirs(config.PROCESSED_TWEET_CVE_PATH)
            os.mkdir(config.MODEL_DATA_PATH)
            os.makedirs(config.TRAIN_DATA_PATH)
            os.makedirs(config.TEST_DATA_PATH)
            os.makedirs(config.VALIDATION_DATA_PATH)
            os.makedirs(config.MODEL_PATH)
            os.mkdir(config.RESULTS_PATH)
        except FileExistsError:
            pass


def set_parser():
    args_parser = argparse.ArgumentParser()
    data_analysis_group = args_parser.add_argument_group('data analysis', config.DATA_ANALYSIS_DESCRIPTION)
    data_analysis_group.add_argument("-s", "--start-analysis", metavar=("start_date", "end_date"), required=False,
                                     type=str, nargs=2, default=None, help=config.START_ANALYSIS_HELP)

    models_management_group = args_parser.add_argument_group('models management', config.MODELS_MANAGEMENT_DESCRIPTION)
    models_management_group.add_argument("-hp", "--hyperparameters-tuning", metavar=("start_date", "end_date"),
                                         required=False, type=str, nargs=2, default=None, help=config.HP_TUNING_HELP)
    models_management_group.add_argument("-c", "--create-model", metavar=("start_date", "end_date"), required=False,
                                         type=str, nargs=2, default=None, help=config.CREATE_MODEL_HELP)
    models_management_group.add_argument("-m", "--model", type=str, choices=["dbow", "dm"], default=None,
                                         help=config.MODEL_HELP)

    results_group = args_parser.add_argument_group('results', config.RESULTS_DESCRIPTION)
    results_group.add_argument("-f", "--find-similarity", metavar=("start_date", "end_date"), required=False, type=str,
                               nargs=2, default=None, help=config.FIND_SIMILARITY_HELP)

    return args_parser


if __name__ == '__main__':
    set_script_folders()
    parser = set_parser()
    args = parser.parse_args()

    if args.start_analysis:
        start_date, end_date = check_inserted_dates(args.start_analysis)
        print(f"Start analysis from: {start_date.strftime(config.DATE_FORMAT)} to "
              f"{end_date.strftime(config.DATE_FORMAT)}")
        analysis.start_analysis(start_date, end_date)
    if args.hyperparameters_tuning:
        start_date, end_date = check_inserted_dates(args.hyperparameters_tuning)
        hp.start_tuning(start_date, end_date)
    if args.create_model:
        start_date, end_date = check_inserted_dates(args.create_model)
        if args.model:
            model.create_model(start_date, end_date, args.model)
        else:
            model.create_model(start_date, end_date)
    if args.find_similarity:
        start_date, end_date = check_inserted_dates(args.find_similarity)
        model.find_similarity(start_date, end_date)
