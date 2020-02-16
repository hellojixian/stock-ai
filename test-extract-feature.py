#!/usr/bin/env python3
'''
测试特征提取并且观察每个关键测正指标的值域范围
'''
import pandas as pd
import numpy as np
import multiprocessing as mp
import datetime, time
import argparse

from lib.datasource import DataSource as ds
from lib.feature_extract import featureExtractor as fe
from lib.indicators import indicators

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

if __name__ == "__main__":
    mp.freeze_support()

    parser = argparse.ArgumentParser(description='Machine Learning.')
    parser.add_argument('--indicator','-i',
                        required=True,
                        type=str, choices=indicators.keys(),
                        help='which module that you want to improve')
    args = vars(parser.parse_args())

    StrategyClass = indicators[args['indicator']]
    np.random.seed(5)
    # set output
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    securities = ds.loadSecuirtyList();
    days = ds.loadTradeDays()

    sample = securities.sample(1).iloc[0]
    symbol, start_date, end_date = sample.name, sample.start_date, sample.end_date
    dataset = ds.loadFeaturedData(symbol, start_date, end_date)

    features = []
    for param in StrategyClass.FEATURES: features.append(param[0])
    print(dataset[features].describe(percentiles=[0.01,0.05,0.25,0.50,0.75,0.95,0.99]))
