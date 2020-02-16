#!/usr/bin/env python3
'''
从最原始的数据中提取出交易日和股票代码信息
这是最初级别的数据预处理
'''
import pandas as pd
import warnings
import multiprocessing as mp

from lib.datasource import DataSource as ds

warnings.simplefilter(action='ignore', category=FutureWarning)

if __name__ == "__main__":
    mp.freeze_support()

    # set output
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    ds.preload()
