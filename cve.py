import os
import pickle
import nvdlib
import config

from tqdm import tqdm
from datetime import datetime
from requests import HTTPError
from concurrent.futures import ThreadPoolExecutor

NVD_URL = 'https://services.nvd.nist.gov/rest/json/cves/1.0/?'
MINIMUM_SCORE = 6.9
CVE_PATH = 'data/cve/'
PROCESSED_CVE_PATH = 'data/processed/cve/'
MAX_RESULTS = 2000
MAX_DAYS_AGO = 120


def check_processed_cves():
    cves = os.listdir(config.PROCESSED_CVE_PATH)
    if len(cves) == 0:
        return config.NO_FILES, None
    else:
        missing_cves = list((set(os.listdir(config.CVE_PATH)).difference(set(cves))))
        if len(missing_cves) > 0:
            return config.MISSING_CVES, missing_cves
        else:
            return config.FILES_OK, None


def retrieve_cves(cves):
    print("Fetching cves online...")
    files = os.listdir(CVE_PATH)
    with ThreadPoolExecutor() as executor:
        for cve_id in tqdm(cves):
            if cve_id not in files:
                try:
                    cve = nvdlib.searchCVE(cveId=cve_id)[0]
                    if len(cve.score) > 1:
                        if cve.score[1] > MINIMUM_SCORE:
                            executor.submit(collect_cve, cve)
                except HTTPError:
                    pass
                except AttributeError:
                    pass


def collect_cve(cve_result):
    cve = {'id': cve_result.id, 'published_date': cve_result.published, 'score': cve_result.score[1]}
    for des in cve_result.descriptions:
        if des.lang == 'en':
            cve['description'] = des.value

    f = open(CVE_PATH + cve_result.id, 'wb')
    pickle.dump(cve, f)


def import_local_cve(filename):
    f = open(CVE_PATH + filename, 'rb')
    return pickle.load(f)


def export_processed_cve(filename, cve):
    with open(PROCESSED_CVE_PATH + filename, mode='wb') as f:
        pickle.dump(cve, f)


# Method for constructing a regex to find a format of the type CVE-YEAR-ID (e.g., CVE-2022-1536) in tweets.
# Constructs a regex in which the maximum year is never greater than the actual year.
def build_regex():
    actual_year = [*datetime.now().strftime("%Y")]
    cve_regex = r"CVE[\-—–]"
    date_range_regex = r"(?:1999|2[0-{}][0-{}][0-{}])".format(actual_year[1], actual_year[2], actual_year[3])
    id_regex = r"[\-—–][0-9]{4,}"
    return cve_regex + date_range_regex + id_regex
