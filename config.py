import os.path

# SCRIPT INFO
DATA_ANALYSIS_DESCRIPTION = "Download and process tweets based on dates entered to create Doc2Vec models"
MODELS_MANAGEMENT_DESCRIPTION = "Allows to manage models and choose the best one to use"
RESULTS_DESCRIPTION = "Allows to obtain the results using the best model previously chosen"

START_ANALYSIS_HELP = "start the analysis of the tweets"
HP_TUNING_HELP = "performs hyperparameters tuning of the models created in the 'data analysis' phase"
CREATE_MODEL_HELP = "creates model using the hyperparameters found in the 'hyperparameters tuning'. In case you did " \
                    "not perform this last step, you can create the model using the default parameters by specifying " \
                    "which one to train using the --model parameter"
MODEL_HELP = "specifies which model to create using the --create-model parameter"
FIND_SIMILARITY_HELP = "use the created model (--create-model) to find similar tweets above a threshold (default >= " \
                       "0.85)"

# SCRIPT DIRECTORIES
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data/')
CVE_PATH = os.path.join(DATA_PATH, 'cve/')
TWEET_PATH = os.path.join(DATA_PATH, 'tweets/')
FILTERED_TWEET_PATH = os.path.join(DATA_PATH, 'filtered_tweets/')
CVE_REFERENCES_PATH = os.path.join(DATA_PATH, 'cve_references/')
PROCESSED_CVE_PATH = os.path.join(DATA_PATH, 'processed/cve/')
PROCESSED_TWEET_PATH = os.path.join(DATA_PATH, 'processed/tweet/')
PROCESSED_TWEET_CVE_PATH = os.path.join(DATA_PATH, 'processed/tweets_cve/')
MODEL_DATA_PATH = os.path.join(DATA_PATH, 'model_data/')
TRAIN_DATA_PATH = os.path.join(MODEL_DATA_PATH, 'train/')
TEST_DATA_PATH = os.path.join(MODEL_DATA_PATH, 'test/')
VALIDATION_DATA_PATH = os.path.join(MODEL_DATA_PATH, 'validation/')
MODEL_PATH = os.path.join(MODEL_DATA_PATH, 'model/')
HYPERPARAMETERS_RESULTS_PATH = os.path.join(MODEL_DATA_PATH, 'hyperparameter_results/')
RESULTS_PATH = os.path.join(DATA_PATH, 'results/')

# SCRIPT FILES
CLEAN_DATA = os.path.join('utils', 'clean_data.sh')
CLEAN_PROCESSED_DATA = os.path.join('utils', 'clean_processed_data.sh')
CLEAN_TWEETS = os.path.join('utils', 'clean_tweets.sh')
COLLECT_TWEETS = os.path.join('utils', 'collect_tweets.sh')


# SCRIPT DATA
DATE_FORMAT = '%d-%m-%Y'

# SCRIPT VALUES
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
HYPERPARAMETERS_FILE = os.path.join('utils', 'hyperparameters.json')
HYPERPARAMETERS_FOUND = os.path.join(MODEL_PATH, 'hyperparameters')
MINIMUM_SCORE = 0.85

# MODELS NAME
filename_chunk = "{0}_{1}"
MODEL_DBOW_BASE = "doc2vec_dbow_base_{}.model"
MODEL_DM_BASE = "doc2vec_dm_base_{}.model"
FINAL_MODEL = "final_model_{}.model"
