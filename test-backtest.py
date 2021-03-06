#!/usr/bin/env python3
'''
测试回测核心模块是否可用，回测模块应该能支持买入卖出的基本操作
'''
import pandas as pd
import numpy as np
import warnings
import multiprocessing as mp
from lib.datasource import DataSource as ds
from lib.feature_extract import featureExtractor as fe
from lib.backtest import backtest as bt


if __name__ == "__main__":
    mp.freeze_support()
    test = bt(init_fund=100000)
    test.buy(symbol='600001', price=10, amount=1000)
    print(test.positions, test.get_cash(), test.get_value())

    test.buy(symbol='600001', price=8, amount=500)
    print(test.positions, test.get_cash(), test.get_value())

    test.buy(symbol='600002', price=80, amount=500)
    print(test.positions, test.get_cash(), test.get_value())

    test.sell(symbol='600001', price=12, amount=700)
    print(test.positions, test.get_cash(), test.get_value())

    test.sell(symbol='600001', price=11)
    print(test.positions, test.get_cash(), test.get_value())
