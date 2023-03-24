import os
import config
import argparse
import analysis

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

    print(
        "Start analysis from: {0} to {1}".format(start.strftime(config.DATE_FORMAT), end.strftime(config.DATE_FORMAT)))
    analysis.start_analysis(start_date, end)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage=config.SCRIPT_USAGE,
                                     description=config.SCRIPT_DESCRIPTION)
    parser.add_argument("-d", "--days-ago", required=False, type=int, default=0, help="Analyzed tweets of X days ago")
    parser.add_argument("-m", "--months-ago", required=False, type=int, default=0,
                        help="Analyzed tweets of X months ago")
    args, dates = parser.parse_known_args()
    start_date = None
    end_date = None
    current_date = datetime.now()

    if dates and (args.days_ago != 0 or args.months_ago != 0):
        print("Too many arguments, exiting...")
        exit(0)
    elif dates:
        check_dates_format(inserted_dates=dates)
        start_date, end_date = check_dates_order(dates)
        start_script(start_date, end_date)

    elif check_valid_arguments(args):
        if args.days_ago == 0 and args.months_ago == 0:
            start_date = current_date
        else:
            start_date = (current_date - relativedelta(days=args.days_ago, months=args.months_ago,
                                                       year=current_date.year))
        start_script(start_date, end_date)
    else:
        exit(0)
