#!/usr/bin/env python3
import datetime
import pandas as pd
import numpy as np
import math, sys, os
import scipy.stats as stats


df = pd.DataFrame()
df = df.append(pd.Series([-1,1,0,1,1,1],name='stock1'))
df = df.append(pd.Series([-1,1,0,1,0,0],name='stock2'))

a=[0,1.2,0,1,1,1]
b=[-1.2,1.9,0,1,1,2]
c=[1,1,0,0,1,1]
# print(df)
# print(df.corr())
print(stats.spearmanr(b,a))
print(stats.spearmanr(a,c))
print(stats.spearmanr(b,c))

# d 5864  5962  5904   5974
# z 5512  5602  5508   5578
# d 352   360   396    396
