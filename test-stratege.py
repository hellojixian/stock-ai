#!/usr/bin/env python3
import pandas as pd
import numpy as np
import multiprocessing as mp

from lib.datasource import DataSource as ds
from lib.feature_extract import featureExtractor as fe
from lib.backtest import backtest as bt
from lib.strategy import strategy as stg

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

if __name__ == "__main__":
    mp.freeze_support()
    np.random.seed(0)
    securities = ds.loadSecuirtyList();
    sample = securities.sample(1).iloc[0]
    symbol, start_date, end_date = sample.name, sample.start_date, sample.end_date

    days    = ds.loadTradeDays()
    dataset = ds.loadFeaturedData(symbol, start_date, end_date)

    # print(dataset)
    dna=[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    mystg = stg(dna)
    report = mystg.backtest(symbol, dataset)
    for session in mystg.session_log:
        print("start: {}\t days: {}\t change: {}\t\t reason: {}\t fund:{}".format(
            session['start_date'],session['days'],session['change'],
            session['end_type'],session['end_fund']))
    print(report)
