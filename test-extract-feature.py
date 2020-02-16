#!/usr/bin/env python3
import pandas as pd
import numpy as np
import multiprocessing as mp
import datetime, time
import argparse

from lib.datasource import DataSource as ds
from lib.feature_extract import featureExtractor as fe

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

if __name__ == "__main__":
    mp.freeze_support()
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

    # features = ['amp_0105','amp_0510','change','drop_days','lossrate','change_diff']
    # features = ['rsi_7','rsi_14']
    # features = ['ma5_bias','ma10_bias','ma_0510','ma5_diff']
    # features = ['kdj_j_scaled','kdj_j_diff','kdj_j_diff_prev','kdj_j_bias']
    # features = ['macd_bar','macd_dea','macd_dif','macd_change','macd_price_c']

    # features = ['bb_pos','bb_scope','bb_diff','bb_diff_prev']
    features = ['close','sar','sar_bias','sar_diff','sar_diff_pre']
    print(dataset[features].describe(percentiles=[0.01,0.05,0.25,0.50,0.75,0.95,0.99]))
    print(dataset[features][:5])
