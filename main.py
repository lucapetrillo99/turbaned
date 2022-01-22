import os
import argparse
import analysis

from datetime import datetime
from dateutil.relativedelta import relativedelta


def valid_argument(argument):
    if argument.daysAgo < 0 and argument.monthsAgo < 0:
        print("ERROR! days and months have to be positive, exiting...")
        return False
    elif argument.daysAgo < 0:
        print("ERROR! days have to be positive, exiting...")
        return False
    elif argument.monthsAgo < 0:
        print("ERROR! months have to be positive, exiting...")
        return False
    else:
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--daysAgo", type=int, default=0, help="Analyzed CVE of X days ago")
    parser.add_argument("-m", "--monthsAgo", type=int, default=0, help="And analyzed CVE of X months ago")
    args = parser.parse_args()

    if args is not None and valid_argument(args):
        current_date = datetime.now()
        current_date = datetime(year=current_date.year, month=current_date.month, day=current_date.day)
        if args.daysAgo == 0 and args.monthsAgo == 0:
            start_date = current_date
        else:
            start_date = (current_date - relativedelta(days=args.daysAgo, months=args.monthsAgo,
                                                       year=current_date.year))
        if not (os.path.exists('data')):
            try:
                os.mkdir('data')
                os.mkdir('data/cve')
                os.mkdir('data/tweets')
                os.mkdir('data/filtered_tweets')
                os.makedirs('data/processed/tweet')
                os.makedirs('data/processed/tweets_cve')
                os.mkdir('data/models')
                os.mkdir('data/results')
            except FileExistsError:
                pass
        analysis.start_analysis(start_date)
    else:
        exit(0)
