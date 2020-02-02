#!/usr/bin/env python3
import pandas as pd
import numpy as np
import multiprocessing as mp
import datetime, time

from lib.datasource import DataSource as ds
from lib.feature_extract import featureExtractor as fe

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def init_globals(arg1, arg2):
    global start_ts, counter, total
    start_ts = datetime.datetime.now(tz=None)
    counter,total = arg1,arg2
    return

def preload_data(data):
    symbol, start_date, end_date = data[0], data[1].start_date, data[1].end_date
    dataset = ds.loadFeaturedData(symbol, start_date, end_date)
    # time.sleep(0.1)
    # 观察数据
    with counter.get_lock():
        counter.value +=1
        progress = counter.value / total
        time_elapsed = datetime.datetime.now(tz=None) - start_ts
        time_eta = (time_elapsed/progress) * (1 - progress)
        bar_width = 25
        print("\rProgress: {:>5.2f}% ({:04d}/{:04d})\tSymbol: {:s}\t[{}{}]\tElapsed Time: {}  ETA: {}".format(
            round(progress*100,2), counter.value, total, symbol,
            "#"*int(progress*bar_width),"."*(bar_width-int(progress*bar_width)),
            str(time_elapsed).split(".")[0], str(time_eta).split(".")[0]
        ), end="")
    return

if __name__ == "__main__":
    mp.freeze_support()
    np.random.seed(5)
    # set output
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    securities = ds.loadSecuirtyList();
    days = ds.loadTradeDays()

    processed_counter = mp.Value('i',0)
    pool = mp.Pool(mp.cpu_count(), initializer=init_globals, initargs=(processed_counter, len(securities)))
    res = pool.map(preload_data, securities.iterrows())
    pool.close()
    print("")
