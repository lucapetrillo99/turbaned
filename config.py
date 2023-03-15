# SCRIPT INFO
SCRIPT_USAGE = 'main.py [-h] [START_DATE] [END_DATE] [-d DAYS_AGO] [-m MONTHS_AGO]\n'
SCRIPT_DESCRIPTION = 'You can enter a [START_DATE] of your choice and indicate an [END_DATE](optional). Otherwise you '\
                     'can enter the number of [-d DAYS_AGO] or [-m MONTHS_AGO] to be analyzed starting from today. '

# SCRIPT DIRECTORIES
DATA_PATH = 'data/'
CVE_PATH = DATA_PATH + 'cve/'
TWEET_PATH = DATA_PATH + 'tweets/'
FILTERED_TWEET_PATH = DATA_PATH + 'filtered_tweets/'
CVE_REFERENCES_PATH = DATA_PATH + 'cve_references/'
PROCESSED_CVE_PATH = DATA_PATH + 'processed/cve/'
PROCESSED_TWEET_PATH = DATA_PATH + 'processed/tweet/'
PROCESSED_TWEET_CVE_PATH = DATA_PATH + 'processed/tweets_cve/'
MODEL_DATA_PATH = DATA_PATH + 'model_data/'
TRAIN_DATA_PATH = MODEL_DATA_PATH + 'train/'
TEST_DATA_PATH = MODEL_DATA_PATH + 'test/'
VALIDATION_DATA_PATH = MODEL_DATA_PATH + 'validation/'
MODEL_PATH = MODEL_DATA_PATH + 'model/'
HYPERPARAMETERS_RESULTS_PATH = MODEL_DATA_PATH + 'hyperparameter_results/'
RESULTS_PATH = DATA_PATH + 'results/'

# SCRIPT DATA
DATE_FORMAT = '%d-%m-%Y'

# SCRIPT VALUE
FILES_OK = 1
WRONG_S_DATE = 0
WRONG_E_DATE = -1
WRONG__DATES = -2
NO_FILES = -3
MISSING_CVES = -1

TWEET_CVE = "1"
TWEET = "2"
ALL_PROCESSED_DATA = "3"

GREATER_EQUAL = 0
LESS_EQUAL = 1
INCLUDED = 2
EQUAL = 3

# MODELS DATA
common_kwargs = dict(
    vector_size=50, negative=5, hs=0, epochs=15, min_count=5
)
HYPERPARAMETERS_FILE = "hyperparameters.json"
HYPERPARAMETERS_PATH = DATA_PATH + HYPERPARAMETERS_FILE

# MODELS NAME
MODEL_DBOW_BASE = "doc2vec_dbow_base"
MODEL_DM_BASE = "doc2vec_dm_base"
FINAL_MODEL = "final_model"
