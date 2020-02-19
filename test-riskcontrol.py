#!/usr/bin/env python3
'''
测试风险控制模块
一个好的风险控制模块应当可以做到如下
- 正向扩大基差
- 减小最大回撤
- 降低最大连续出错
- 正向扩大盈亏比

对于同一组测试数据逐个测试各项指标，
先测试基础数据数据值，然后动态调整参数来回测对各项指标的影响

这个脚本负责提出用于迭代测试的数据集合
'''

import pandas as pd
import numpy as np
import multiprocessing as mp
import datetime, time, sys
import argparse

from lib.feature_extract import featureExtractor as fe
from lib.datasource import DataSource as ds
from lib.indicators.strategy_learner import StrategyLearner as learner
from lib.indicators import indicators

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
        print("\rProgress: {:>5.2f}% ({:04d}/{:04d}) Symbol: {:s}\t[{}{}]\tElapsed Time: {}  ETA: {}".format(
            round(progress*100,2), counter.value, total, symbol,
            "#"*int(progress*bar_width),"."*(bar_width-int(progress*bar_width)),
            str(time_elapsed).split(".")[0], str(time_eta).split(".")[0]
        ), end="")
    return

if __name__ == "__main__":
    mp.freeze_support()

    parser = argparse.ArgumentParser(description='Machine Learning.')

    parser.add_argument('--batch-size',
                        default=100, type=int,
                        help='how many batch of samples for learning')

    parser.add_argument('--skip-batch',
                        default=0, type=int,
                        help='skip first N of batch')

    parser.add_argument('--step-size',
                        default=30, type=int,
                        help='how many generations for each batch of learning')

    parser.add_argument('--training-set-size',
                        default=10, type=int,
                        help='how many data samples for each batch of learning')

    parser.add_argument('--early-stop',
                        default=3, type=int,
                        help='Stop learning if N batch of improving the result')

    parser.add_argument('--random','-r',
                        default=1, type=int,
                        help='By default using random data samples for learning')

    args = vars(parser.parse_args())


    if args['random']!=1:
        print('pseudo random')
        np.random.seed(0)
    securities = ds.loadSecuirtyList()

    for i in range(args['batch_size']):
        if i < args['skip_batch']: continue
        print("Learning batch :{}".format(i))

        print("Preloading datasets: {}".format(args['training_set_size']*2))
        processed_counter = mp.Value('i',0)
        pool = mp.Pool(min(args['training_set_size'],mp.cpu_count()), initializer=init_globals, initargs=(processed_counter, args['training_set_size']*2))

        # prepare datasets
        training_sets = []
        samples = securities.sample(args['training_set_size']*2)
        res = pool.map(preload_data, samples.iterrows())
        pool.close()
        print("\n[DONE]")

        print("Generating training sets:\t",end="")
        for symbol,sample in samples[:(args['training_set_size'])].iterrows():
            start_date, end_date = sample.start_date, sample.end_date
            dataset = ds.loadFeaturedData(symbol, start_date, end_date)
            if dataset.shape[0]>0: training_sets.append(dataset)
        print("[DONE]")

        print("Generating validation sets:\t",end="")
        validation_sets = []
        for symbol,sample in samples[args['training_set_size']:].iterrows():
            start_date, end_date = sample.start_date, sample.end_date
            dataset = ds.loadFeaturedData(symbol, start_date, end_date)
            if dataset.shape[0]>0: validation_sets.append(dataset)
        print("[DONE]")

        dataset = validation_sets[0]
        symbol = dataset.iloc[0]['symbol']
        stg = indicators['macd']
        from lib.riskcontrol.base_rc import BaseRiskControl
        rc = BaseRiskControl(stg)
        rc.backtest(symbol, dataset)
        print(symbol)
        sys.exit(0)

        print("-"*100)
        print("\n")
