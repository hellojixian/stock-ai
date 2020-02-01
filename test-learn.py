#!/usr/bin/env python3
import pandas as pd
import numpy as np
import argparse
from lib.datasource import DataSource as ds
from lib.feature_extract import featureExtractor as fe
from lib.backtest import backtest as bt
from lib.strategy import strategy as stg
from lib.learn import learn as ln

parser = argparse.ArgumentParser(description='Machine Learning.')
parser.add_argument('--batch-size',
                    default=100, type=int,
                    help='how many batch of samples for learning')

parser.add_argument('--step-size',
                    default=30, type=int,
                    help='how many generations for each batch of learning')

parser.add_argument('--training-set-size',
                    default=5, type=int,
                    help='how many data samples for each batch of learning')
args = vars(parser.parse_args())

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

np.random.seed(0)
securities = ds.loadSecuirtyList();

for i in range(args['batch_size']):
    print("Learning batch :{}".format(i))

    print("Generating training sets:\t",end="")
    # prepare datasets
    training_sets = []
    while len(training_sets)<args['training_set_size']:
        sample = securities.sample(1).iloc[0]
        symbol, start_date, end_date = sample.name, sample.start_date, sample.end_date
        dataset = ds.loadFeaturedData(symbol, start_date, end_date)
        if dataset.shape[0]>0: training_sets.append(dataset)
    print("[DONE]")

    print("Generating validation sets:\t",end="")
    validation_sets = []
    while len(validation_sets)<args['training_set_size']:
        sample = securities.sample(1).iloc[0]
        symbol, start_date, end_date = sample.name, sample.start_date, sample.end_date
        dataset = ds.loadFeaturedData(symbol, start_date, end_date)
        if dataset.shape[0]>0: validation_sets.append(dataset)
    print("[DONE]")

    ml = ln()
    for _ in range(args['step_size']):
        print("GA Learning step: {}".format(_))
        report = ml.evolve(training_sets=training_sets, validation_sets=validation_sets)
        print(report)
    ml.save()

    print("-"*100)
    print("\n")
