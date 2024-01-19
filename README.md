# TURBANED: Tweet clUsteRization BAsed oN cvE Description

This tool analyze and create clusters of tweets based on the vulnerability they are talking about.

## Getting started

### Run in a Docker container

You can run ***turbaned*** in a container using the following instructions.

#### Build

```
docker build -t turbaned .
```

#### Run

You can run the created container as a non-root user using the `run.sh` file.

```
 ./run.sh --help
```

### Run in a Virtualenv

Install all the required libraries using the `requirements.txt` file by running in your environment.

```
pip3 install -r requirements.txt
```

## Preliminary step

This tool collects tweets based on the indicated start and end dates using a private endpoint. To obtain it, 
send an [email](mailto:lucapetrillo99@gmail.com).

In addition, the CVEs needed for analysis are retrieved from the
official [NVD API](https://nvd.nist.gov/developers/vulnerabilities). To make up for the request limits it is possible to
specify an API KEY (you can get it on the [official site](https://nvd.nist.gov/developers/request-an-api-key)).

For this information create an `.env` file as below.

```
TWEET_URL=""
API_KEY=""
```

## Usage

See further information on the arguments required with:

```
usage: main.py [-h] [-s start_date end_date] [-hp start_date end_date]
               [-c start_date end_date] [-m {dbow,dm}]
               [-f start_date end_date]

options:
  -h, --help            show this help message and exit

data analysis:
  Download and process tweets based on dates entered to create Doc2Vec
  models

  -s start_date end_date, --start-analysis start_date end_date
                        start the analysis of the tweets

models management:
  Allows to manage models and choose the best one to use

  -hp start_date end_date, --hyperparameters-tuning start_date end_date
                        performs hyperparameters tuning of the models created
                        in the 'data analysis' phase
  -c start_date end_date, --create-model start_date end_date
                        creates model using the hyperparameters found in the
                        'hyperparameters tuning'. In case you did not perform
                        this last step, you can create the model using the
                        default parameters by specifying which one to train
                        using the --model parameter
  -m {dbow,dm}, --model {dbow,dm}
                        specifies which model to create using the --create-
                        model parameter

results:
  Allows to obtain the results using the best model previously chosen

  -f start_date end_date, --find-similarity start_date end_date
                        use the created model (--create-model) to find similar
                        tweets above a threshold (default >= 0.85)

```

### Prepare the dataset

When the parameter `-s` is given, the script is started and the tweets corresponding to the given dates are collected. In addition, the CVEs identified in the tweets are collected, a preprocessing of the data is performed, and two Doc2Vec models are created.
```
data analysis:
  Download and process tweets based on dates entered to create Doc2Vec
  models

  -s start_date end_date, --start-analysis start_date end_date
                        start the analysis of the tweets
```

You can consult and modify the default parameters of the templates in the `config.py` file.

```
common_kwargs = dict(vector_size=50, negative=5, hs=0, epochs=15, min_count=5)
```

### Model creation and assessment

At this stage, hyperparameters tuning can be carried out and the model with the best combination of hyperparameters can be created. Alternatively with the `--model` parameter it is possible to specify which model to create.

To change the hyperparameters to be tested during this step, you can consult the `utils/hyperparameters.json` hyperparameters.json file.

```
models management:
  Allows to manage models and choose the best one to use

  -hp start_date end_date, --hyperparameters-tuning start_date end_date
                        performs hyperparameters tuning of the models created
                        in the 'data analysis' phase
  -c start_date end_date, --create-model start_date end_date
                        creates model using the hyperparameters found in the
                        'hyperparameters tuning'. In case you did not perform
                        this last step, you can create the model using the
                        default parameters by specifying which one to train
                        using the --model parameter
  -m {dbow,dm}, --model {dbow,dm}
                        specifies which model to create using the --create-
                        model parameter
```

### Results

Clusters can be obtained at this stage, using a threshold (cosine similarity) to discard tweets less similar to those with which the model was trained.

```
results:
  Allows to obtain the results using the best model previously chosen

  -f start_date end_date, --find-similarity start_date end_date
                        use the created model (--create-model) to find similar
                        tweets above a threshold (default >= 0.85)
```


The default threshold value (0.85) can be changed in the `config.py` file.

```
MINIMUM_SCORE = 0.85
```

## Project structure

During execution, a few directories are created where data are collected and saved.

```
├── data
│    ├── cve
│    ├── cve_references
│    ├── filtered_tweets
│    ├── model_data
│    │   ├── model
│    │   ├── test
│    │   ├── train
│    │   └── validation
│    ├── processed
│    │   ├── cve
│    │   ├── tweet
│    │   └── tweets_cve
│    ├── results
│    └── tweets
...
```