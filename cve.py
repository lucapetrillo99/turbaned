import os
import time
import pickle
import requests

from tqdm import tqdm
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

NVD_URL = 'https://services.nvd.nist.gov/rest/json/cves/1.0/?'
MINIMUM_SCORE = 6.9
CVE_PATH = 'data/cve/'
MAX_RESULTS = 2000
MAX_DAYS_AGO = 120


def check_cves(initial_date):
    directory_files = os.listdir(CVE_PATH)
    return len(directory_files) > 0


def get_cves(initial_date):
    current_date = datetime.now()
    days_ago = (current_date - initial_date).days

    # fetch cves from NVD API in chuck of 120 days
    index = 0
    end_date = None
    if days_ago > MAX_DAYS_AGO:
        while days_ago > 0:
            if index == 0:
                end_date = initial_date + timedelta(days=MAX_DAYS_AGO)
                days_ago = days_ago - MAX_DAYS_AGO
                index += 1
                retrieve_cves(initial_date, end_date)
            else:

                if days_ago > MAX_DAYS_AGO:
                    start_date = end_date
                    end_date = start_date + timedelta(days=MAX_DAYS_AGO)
                    days_ago = days_ago - MAX_DAYS_AGO
                    retrieve_cves(start_date, end_date)
                else:
                    start_date = end_date
                    end_date = start_date + timedelta(days=days_ago)
                    days_ago = 0
                    retrieve_cves(start_date, end_date)
    else:
        retrieve_cves(initial_date, current_date)


def retrieve_cves(start_date, end_date):
    print("Fetching cves online...")
    pub_start_date, pub_end_date = create_date(start_date, end_date)
    starting_index = 0
    remaining_cve = 1

    # fetch cves from NVD API in slot of max 2000 cves
    with ThreadPoolExecutor() as executor:
        while remaining_cve > 0:
            params = dict(
                pubStartDate=pub_start_date,
                pubEndDate=pub_end_date,
                resultsPerPage=MAX_RESULTS,
                startIndex=starting_index
            )

            try:
                resp = requests.get(url=NVD_URL, params=params)
                data = resp.json()
                executor.submit(collect_cves, data)

                if starting_index == 0:
                    total_results = data['totalResults']
                    remaining_cve = total_results

                if remaining_cve <= MAX_RESULTS:
                    break
                else:
                    starting_index = starting_index + MAX_RESULTS
                    remaining_cve = remaining_cve - MAX_RESULTS

            except ConnectionError:
                print("Connection error while getting cve from database")
                break


def collect_cves(cve_result):
    for idx, element in tqdm(enumerate(cve_result['result']['CVE_Items'])):
        cve = {'id': element['cve']['CVE_data_meta']['ID'], 'published_date': element['publishedDate'][:10],
               'description': element['cve']['description']['description_data'][0]['value']}

        if element['impact']:
            score = element['impact']['baseMetricV3']['cvssV3']['baseScore']
            if score > MINIMUM_SCORE:
                cve['score'] = score

        f = open(CVE_PATH + cve['id'], 'wb')
        pickle.dump(cve, f)


def import_local_cves(cve_files):
    print("Importing cves...")
    cve_files.sort()
    cves = []
    for cve in tqdm(cve_files):
        f = open(CVE_PATH + cve, 'rb')
        cves.append(pickle.load(f))

    return cves


def create_date(begin, end):
    # build date for NVD API in format YYYY-MM-DDTHH:MM:SS:000 UTC-HH:MM
    start_date = begin.strftime('%Y-%m-%d')
    start_time = begin.strftime('%H:%M:%S') + ':000'
    utc = 'UTC' + time.strftime("%z")[:3] + ':' + time.strftime("%z")[-2:]
    end_date = end.strftime("%Y-%m-%d")
    end_time = str(end.strftime("%H:%M:%S:%f"))[:-3]
    return start_date + 'T' + start_time + ' ' + utc, end_date + 'T' + end_time + ' ' + utc
