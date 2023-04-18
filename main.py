import os
import config
import argparse
import analysis
import model
import hyperparameters_tuning as hp

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def check_valid_arguments(argument):
    if argument.days_ago < 0 and argument.months_ago < 0:
        print("ERROR! days and months have to be positive, exiting...")
        return False
    elif argument.days_ago < 0:
        print("ERROR! days have to be positive, exiting...")
        return False
    elif argument.months_ago < 0:
        print("ERROR! months have to be positive, exiting...")
        return False
    else:
        return True


def check_dates_format(inserted_dates):
    if len(inserted_dates) == 0:
        print("You must insert at least a starting date...")
        exit(0)
    elif len(inserted_dates) > 2:
        print("You must insert at least a starting date...")
        exit(0)
    elif len(inserted_dates) == 1:
        try:
            datetime.strptime(inserted_dates[0], config.DATE_FORMAT)
        except ValueError:
            print("Incorrect data format, should be DD-MM-YYYY, exiting...")
            exit(0)
    else:
        for date in inserted_dates:
            try:
                datetime.strptime(date, config.DATE_FORMAT)
            except ValueError:
                print("Incorrect data format, should be YYYY-MM-DD, exiting...")


def check_dates_order(inserted_dates):
    curr_date = datetime.now()
    if len(inserted_dates) > 1:
        if inserted_dates[0] > curr_date or inserted_dates[1] > curr_date:
            print("Wrong date, exiting...")
            exit(0)
        elif inserted_dates[0] > inserted_dates[1]:
            print("Wrong date order, exiting...")
            exit(0)
        else:
            s_date = inserted_dates[0]
            e_date = inserted_dates[1]
    else:
        if inserted_dates[0] > curr_date:
            print("Wrong date, exiting...")
            exit(0)
        else:
            s_date = inserted_dates[0]
            e_date = curr_date - timedelta(days=1)

    return s_date, e_date


def start_script(start, end):
    if not (os.path.exists('data')):
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

    print(f"Start analysis from: {start.strftime(config.DATE_FORMAT)} to {end.strftime(config.DATE_FORMAT)}")
    analysis.start_analysis(start_date, end)


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
    parser = set_parser()
    args = parser.parse_args()

    start_date = None
    end_date = None
    current_date = datetime.now()

    if args.start_analysis:
        check_dates_format(inserted_dates=args.start_analysis)
        start_date, end_date = check_dates_order(args.start_analysis)
        start_script(start_date, end_date)
    if args.hyperparameters_tuning:
        check_dates_format(inserted_dates=args.start_analysis)
        start_date, end_date = check_dates_order(args.start_analysis)
        hp.start_tuning(start_date, end_date)
    if args.create_model:
        check_dates_format(inserted_dates=args.start_analysis)
        start_date, end_date = check_dates_order(args.start_analysis)
        model.create_model(start_date, end_date)
    if args.find_similarity:
        check_dates_format(inserted_dates=args.start_analysis)
        start_date, end_date = check_dates_order(args.start_analysis)
        model.find_similarity(start_date, end_date)
