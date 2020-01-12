import datetime
import pandas as pd
import numpy as np
import multiprocessing as mp
import math, sys, os

DEFAULT_DATAFILE = "data/stock_data/cn_prices.csv"
DEFAULT_TRADEDATE = "data/cache/trade_date.csv"
DEFAULT_SECURITYLIST = "data/cache/security_list.csv"
DEFAULT_FEATURED_DATA = "data/cache/featured_data.csv"
DATASET = None

class DataSource(object):
    def preload(datafile=DEFAULT_DATAFILE):
        def _loadDataset():
            global DATASET
            print("Loading data file: \t",end="")
            types_dict={"symbol":str}
            headers = ["symbol","date","open","high","low","close","volume","amount"]
            DATASET = pd.read_csv(datafile, header=None,
                                            skiprows=1,
                                            names=headers,
                                            dtype=types_dict,
                                            parse_dates=True)
            print("{:d} records".format(DATASET.shape[0]))
            return DATASET

        def _loadTradeDays():
            # generate date list
            if os.path.isfile(DEFAULT_TRADEDATE):
                print("Loading trading days: \t",end="")
                trade_days = pd.read_csv(DEFAULT_TRADEDATE,parse_dates=True,
                                                           index_col='date')
            else:
                print("Extract trading days: \t",end="")
                trade_days=DATASET[['date','symbol']].groupby(['date']).count()
                trade_days['symbols'] = trade_days['symbol']
                trade_days['processed'] = 0
                trade_days = trade_days[['symbols']]
                trade_days = trade_days.sort_index(ascending=True)
                trade_days.to_csv(DEFAULT_TRADEDATE)
            print("{:d} days".format(trade_days.shape[0]))
            return trade_days

        def _loadSecuirtyList():
            # generate security list
            if os.path.isfile(DEFAULT_SECURITYLIST):
                print("Loading security list: \t",end="")
                types_dict={"symbol":str}
                security_list = pd.read_csv(DEFAULT_SECURITYLIST,parse_dates=True,
                                                              dtype=types_dict)
                security_list = security_list.set_index('symbol')
            else:
                print("Extract security list: \t",end="")
                security_list = DATASET[['date','symbol']].groupby(['symbol']).count()
                security_list.index = security_list.index.astype('str')
                security_list['days'] = security_list['date']
                security_list['start_date'] = ""
                security_list['end_date'] = ""
                security_list['processed'] = 0
                security_list = security_list[['days']]
                print("")
                i=0
                for symbol in security_list.index:
                    i+=1
                    subset = DATASET[DATASET.eval("symbol=='{}'".format(symbol))]
                    subset = subset.sort_values(by=['date'],ascending=True)
                    start_date = subset['date'].iloc[0]
                    end_date = subset['date'].iloc[-1]
                    security_list.loc[symbol,'start_date']=start_date
                    security_list.loc[symbol,'end_date']=end_date
                    print("\rProgress: {:>5.2f}% ({:04d}/{})  Symbol: {}   Start: {}   End: {}".format(
                        round(i/security_list.shape[0]*100,2),i,security_list.shape[0],
                        symbol, start_date, end_date), end="")
                security_list.to_csv(DEFAULT_SECURITYLIST)
                print("")
            print("{:d} securities".format(security_list.shape[0]))
            return security_list

        def _extractSecurityFeatures(security_list):
            #Extract features
            if os.path.isfile(DEFAULT_FEATURED_DATA):
                print("Loading featured data: \t",end="")
                types_dict={"symbol":str}
                featured_dataset = pd.read_csv(DEFAULT_FEATURED_DATA,
                                                parse_dates=True,
                                                index_col=0,
                                                dtype=types_dict)
                print("{} Records".format(featured_dataset.shape[0]))
            else:
                featured_dataset = pd.DataFrame()

            if "processed" not in security_list.columns: security_list["processed"]=0
            # hard reset processed state
            # security_list["processed"]=0

            prev_completed = security_list[security_list.eval("processed==1")].shape[0]
            remaining_list = security_list[security_list.eval("processed==0")]
            if remaining_list.shape[0]>0:
                print("Extracting features: \t",end="\n")
                global processed_secuirties,total_secuirties
                processed_secuirties = mp.Value('i', prev_completed)
                total_secuirties = security_list.shape[0]

                chunks = 30
                remaining_list_split = np.array_split(remaining_list,chunks)

                pool = mp.Pool(mp.cpu_count())
                for chunk in remaining_list_split:
                    data_list = []
                    for symbol,rec in chunk.iterrows():
                        security_list.loc[symbol,'processed']=1
                        subset = DATASET[DATASET.eval("symbol=='{}'".format(symbol))]
                        data_list.append(subset)

                    res = pool.map(_processExtractFeatures, data_list)
                    chunk_res = pd.concat(res)
                    featured_dataset = featured_dataset.append(chunk_res,sort=False)
                    featured_dataset = featured_dataset.drop_duplicates()

                    security_list.to_csv(DEFAULT_SECURITYLIST)
                    featured_dataset.to_csv(DEFAULT_FEATURED_DATA)
                    print("\nSave Progress: {} Records".format(featured_dataset.shape[0]))

            print("{} Records".format(featured_dataset.shape[0]))

        dataset = _loadDataset()
        trade_days = _loadTradeDays()
        security_list = _loadSecuirtyList()
        featured_dataset = _extractSecurityFeatures(security_list)
        return trade_days, security_list

def _processExtractFeatures(subset):
    def _find_trend(values):
        values = list(values)
        p_min, p_max = np.min(values), np.max(values)
        p_min_idx, p_max_idx = values.index(p_min), values.index(p_max)
        # down trend
        trend = math.nan
        if p_max_idx >= p_min_idx:
            # up trend
            trend = 1
        elif p_max_idx < p_min_idx:
            trend = 0
        return trend

    def _find_pos(values):
        values = list(values)
        close = values[-1]
        p_min, p_max = np.min(values), np.max(values)
        pos = (close - p_min) / (p_max - p_min) * 100
        pos = np.round(pos,2)
        return pos

    subset = subset.copy()
    subset['bar'] = round((subset['close'] - subset['open']) / subset['open'] * 100, 2)
    subset['change'] = round((subset['close'] - subset['close'].shift(periods=1))/subset['close'].shift(periods=1) * 100,2)
    subset['amp'] = round((subset['high'] - subset['low']) / subset['open'] * 100, 2)
    for i in [5,10,30,60]:
        subset['trend_{}'.format(i)] = subset['close'].rolling(window=i).apply(_find_trend,raw=True)
    for i in [250]:
        subset['pos_{}'.format(i)] = subset['close'].rolling(window=i).apply(_find_pos,raw=True)

    subset = subset.dropna()

    # print progress
    global processed_secuirties,total_secuirties
    processed_secuirties.value+=1
    print("\rProgress: {:>5.2f}% ({:04d}/{})  Symbol: {}   Records: {}".format(
            round(processed_secuirties.value/total_secuirties*100,2),
            processed_secuirties.value, total_secuirties,
            subset['symbol'].iloc[0], subset.shape[0]), end="")
    return subset
