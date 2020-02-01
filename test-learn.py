#!/usr/bin/env python3
import pandas as pd
import numpy as np
from lib.datasource import DataSource as ds
from lib.feature_extract import featureExtractor as fe
from lib.backtest import backtest as bt
from lib.strategy import strategy as stg
from lib.learn import learn as ln

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

np.random.seed(0)
securities = ds.loadSecuirtyList();

# prepare datasets
training_sets = []
while len(training_sets)<5:
    sample = securities.sample(1).iloc[0]
    symbol, start_date, end_date = sample.name, sample.start_date, sample.end_date
    dataset = ds.loadFeaturedData(symbol, start_date, end_date)
    if dataset.shape[0]>0: training_sets.append(dataset)

validation_sets = []
while len(validation_sets)<5:
    sample = securities.sample(1).iloc[0]
    symbol, start_date, end_date = sample.name, sample.start_date, sample.end_date
    dataset = ds.loadFeaturedData(symbol, start_date, end_date)
    if dataset.shape[0]>0: validation_sets.append(dataset)

ml = ln()
for _ in range(10):
    report = ml.evolve(training_sets=training_sets, validation_sets=validation_sets)
    print(report)
