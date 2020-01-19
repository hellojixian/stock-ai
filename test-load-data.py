#!/usr/bin/env python3
import pandas as pd
import numpy as np
import warnings
from lib.datasource import DataSource as ds
warnings.simplefilter(action='ignore', category=FutureWarning)

np.random.seed(0)
# set output
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

securities = ds.loadSecuirtyList();
sample = securities.sample(1).iloc[0]
symbol, start_date, end_date = sample.name, sample.start_date, sample.end_date

dataset = ds.loadFeaturedData(symbol, start_date, end_date)
print(dataset, start_date, end_date)
