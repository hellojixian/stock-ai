#!/usr/bin/env python3
import pandas as pd
import numpy as np
import warnings
from lib.datasource import DataSource as ds
from lib.feature_extract import featureExtractor as fe
from lib.backtest import backtest as bt
from lib.strategy import strategy as stg


securities = ds.loadSecuirtyList();
sample = securities.sample(1).iloc[0]
symbol, start_date, end_date = sample.name, sample.start_date, sample.end_date

days    = ds.loadTradeDays()
dataset = ds.loadFeaturedData(symbol, start_date, end_date)
dataset = fe.processData(dataset)

mystg = stg(dna)
mystg.backtest(symbol, dataset)
