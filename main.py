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


def check_valid_dates(inserted_dates):
    is_valid = True
    valid_dates = []
    if len(inserted_dates) > 2:
        is_valid = False
    elif len(inserted_dates) == 1:
        try:
            valid_dates.append(datetime.strptime(inserted_dates[0], config.DATE_FORMAT))
        except ValueError:
            print("Incorrect data format, should be YYYY-MM-DD, exiting...")
            is_valid = False
    else:
        for date in inserted_dates:
            try:
                valid_dates.append(datetime.strptime(date, config.DATE_FORMAT))
            except ValueError:
                print("Incorrect data format, should be YYYY-MM-DD, exiting...")
                is_valid = False

    if is_valid:
        return valid_dates
    else:
        return False


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
            os.mkdir(config.MODEL_PATH)
            os.mkdir(config.RESULTS_PATH)
        except FileExistsError:
            pass

    if end is None:
        end = current_date - timedelta(days=1)

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
        values = check_valid_dates(inserted_dates=dates)
        if values:
            if len(values) > 1:
                if values[0] > current_date or values[1] > current_date:
                    print("Wrong date, exiting...")
                    exit(0)
                elif values[0] > values[1]:
                    print("Wrong date order, exiting...")
                    exit(0)
                else:
                    start_date = values[0]
                    end_date = values[1]
            else:
                if values[0] > current_date:
                    print("Wrong date, exiting...")
                    exit(0)
                else:
                    start_date = values[0]
                    end_date = current_date
            start_script(start_date, end_date)
        else:
            exit(0)
    elif check_valid_arguments(args):
        if args.days_ago == 0 and args.months_ago == 0:
            start_date = current_date
        else:
            start_date = (current_date - relativedelta(days=args.days_ago, months=args.months_ago,
                                                       year=current_date.year))
        start_script(start_date, end_date)
    else:
        exit(0)
