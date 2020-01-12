#!/usr/bin/env python3
import pandas as pd

from lib.datasource import DataSource as ds

# set output
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

ds.preload()
