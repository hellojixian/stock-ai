import datetime
import pandas as pd
import numpy as np
import multiprocessing as mp
import itertools
from .feature_extract import featureExtractor as fe
import math, sys, os

DEFAULT_DATAFILE = "data/stock_data/cn_prices.csv"
DEFAULT_TRADEDATE = "data/cache/trade_date.csv"
DEFAULT_SECURITYLIST = "data/cache/security_list.csv"
DEFAULT_FEATURED_DATA = "data/cache/featured_data.csv"
DATASET = None
MAX_PROCESSES=16

class DataSource(object):
    def loadTradeDays():
        global DATASET
        # generate date list
        if os.path.isfile(DEFAULT_TRADEDATE):
            print("Loading trading days: \t",end="")
            trade_days = pd.read_csv(DEFAULT_TRADEDATE,parse_dates=False,
                                                       index_col='date')
        else:
            if DATASET is None: DATASET = DataSource.loadDataset()
            print("Extract trading days: \t",end="")
            trade_days=DATASET[['date','symbol']].groupby(['date']).count()
            trade_days['symbols'] = trade_days['symbol']
            trade_days['processed'] = 0
            trade_days = trade_days[['symbols']]
            trade_days = trade_days.sort_index(ascending=True)
            trade_days.to_csv(DEFAULT_TRADEDATE)
        print("{:d} days".format(trade_days.shape[0]))
        return trade_days

    def loadSecuirtyList():
        global DATASET
        # generate security list
        if os.path.isfile(DEFAULT_SECURITYLIST):
            print("Loading security list: \t",end="")
            types_dict={"symbol":str}
            security_list = pd.read_csv(DEFAULT_SECURITYLIST,parse_dates=False,
                                                          dtype=types_dict)
            security_list = security_list.set_index('symbol')
        else:
            if DATASET is None: DATASET = DataSource.loadDataset()

            print("Extract security list: \t",end="")
            security_list = DATASET[['date','symbol']].groupby(['symbol']).count()
            security_list.index = security_list.index.astype('str')
            security_list['days'] = security_list['date']
            security_list['start_date'] = ""
            security_list['end_date'] = ""
            security_list['processed'] = 0
            security_list = security_list[['days']]
            print("")

            processed_secuirties = mp.Value('i', 0)
            total_secuirties = security_list.shape[0]

            pool = mp.Pool(mp.cpu_count(),initializer=_init_globals, initargs=(DATASET,processed_secuirties,total_secuirties))
            res  = pool.map(_processExtractSecurityData, security_list.iterrows())
            security_list = pd.DataFrame(res)
            security_list = security_list.dropna()
            security_list = security_list.sort_index(ascending=True)
            security_list.index.name = 'symbol'
            security_list.to_csv(DEFAULT_SECURITYLIST)
            pool.close()
            print("")

        print("{:d} securities".format(security_list.shape[0]))
        return security_list

    def loadDataset(datafile=None):
        global DATASET
        if datafile is None: datafile = DEFAULT_DATAFILE

        print("Loading data file: \t",end="")
        types_dict={"symbol":str}
        headers = ["symbol","date","open","high","low","close","volume","amount"]
        DATASET = pd.read_csv(datafile, header=None,
                                        skiprows=1,
                                        names=headers,
                                        dtype=types_dict,
                                        parse_dates=False)
        print("{:d} records".format(DATASET.shape[0]))
        return DATASET

    def preload(datafile=DEFAULT_DATAFILE):
        def _extractSecurityFeatures(security_list):
            global DATASET
            if DATASET is None: DATASET = DataSource.loadDataset()

            #Extract features
            if os.path.isfile(DEFAULT_FEATURED_DATA):
                # print("Loading featured data: \t",end="")
                types_dict={"symbol":str}
                featured_dataset = pd.read_csv(DEFAULT_FEATURED_DATA,
                                                parse_dates=False,
                                                index_col=0,
                                                dtype=types_dict)
                # print("{} records".format(featured_dataset.shape[0]))
            else:
                featured_dataset = pd.DataFrame()

            if "processed" not in security_list.columns: security_list["processed"]=0
            # hard reset processed state
            # security_list["processed"]=0

            prev_completed = security_list[security_list.eval("processed==1")].shape[0]
            remaining_list = security_list[security_list.eval("processed==0")]
            if remaining_list.shape[0]>0:
                print("Extracting features: \t",end="\n")
                processed_secuirties = mp.Value('i', prev_completed)
                total_secuirties = security_list.shape[0]

                chunk_size = 800
                remaining_list_split = np.array_split(remaining_list,
                                    round(remaining_list.shape[0] / chunk_size))

                pool = mp.Pool(mp.cpu_count(),initializer=_init_globals, initargs=(DATASET, processed_secuirties, total_secuirties))
                for chunk in remaining_list_split:
                    symbol_list = []
                    idx = 0
                    for symbol,rec in chunk.iterrows():
                        idx+=1
                        print("\rPreparing dataset: {:5.2f}% ({:03d}/{})  Symbol: {}".format(
                            round(idx/chunk.shape[0]*100,2), idx,
                            chunk.shape[0],
                            symbol), end="")
                        security_list.loc[symbol,'processed']=1
                        symbol_list.append(symbol)
                    print("")

                    res = pool.map(_processExtractFeatures, symbol_list)
                    chunk_res = pd.concat(res)
                    featured_dataset = featured_dataset.append(chunk_res,sort=False)
                    featured_dataset = featured_dataset.drop_duplicates()

                    # if the computer is fast enough, there is no need to save progress at all
                    # print("\nSaving Progress: {} records".format(featured_dataset.shape[0]))
                    # featured_dataset.to_csv(DEFAULT_FEATURED_DATA)
                    # security_list.to_csv(DEFAULT_SECURITYLIST)
                featured_dataset.to_csv(DEFAULT_FEATURED_DATA)
                security_list.to_csv(DEFAULT_SECURITYLIST)
                pool.close()
                print("{} records".format(featured_dataset.shape[0]))
            return featured_dataset

        def _extractTradeDaysFeatrues(dataset,trade_days):
            processed_days   = mp.Value('i', 0)
            total_trade_days = trade_days.shape[0]
            featured_dataset = dataset

            days = trade_days.index
            pool = mp.Pool(min(mp.cpu_count(),MAX_PROCESSES),initializer=_init_globals2, initargs=(featured_dataset, processed_days, total_trade_days))
            res  = pool.map(_processExtractTradeDaysFeatures, trade_days.iterrows())
            print("")
            trade_days = pd.DataFrame(res)
            trade_days = trade_days.dropna()
            trade_days = trade_days.sort_index(ascending=True)
            trade_days.index.name = 'date'
            trade_days.to_csv(DEFAULT_TRADEDATE)
            pool.close()
            return trade_days

        dataset = DataSource.loadDataset()
        trade_days = DataSource.loadTradeDays()
        security_list = DataSource.loadSecuirtyList()
        featured_dataset = _extractSecurityFeatures(security_list)
        trade_days = _extractTradeDaysFeatrues(featured_dataset,trade_days)
        return trade_days, security_list

    def loadFeaturedData(symbol, start_date=None, end_date=None):
        global featured_dataset
        types_dict={"symbol":str}
        subset = None
        cache_file = "data/cache/featured/{}_{}_{}.csv".format(symbol,start_date,end_date)
        if os.path.isfile(cache_file):
            subset = pd.read_csv(cache_file,parse_dates=False,
                                            index_col=0,
                                            dtype=types_dict)
        else:
            if not os.path.isfile(DEFAULT_FEATURED_DATA):
                DataSource.preload()

            # print("Loading featured data: \t",end="")
            featured_dataset = pd.read_csv(DEFAULT_FEATURED_DATA,
                                            parse_dates=False,
                                            index_col=0,
                                            dtype=types_dict)
            # print("{} records".format(featured_dataset.shape[0]))

            query = "symbol=='{}'".format(symbol)
            if start_date is not None:
                query = query + " and date>='{}'".format(start_date)
            if end_date is not None:
                query = query + " and date<='{}'".format(end_date)

            subset = featured_dataset[featured_dataset.eval(query)]
            if len(subset)>0: subset = fe.processData(subset)
            subset.to_csv(cache_file)
        return subset

def _init_globals(arg1,arg2,arg3):
    global DATASET,processed_secuirties, total_secuirties
    DATASET,processed_secuirties, total_secuirties = arg1,arg2,arg3
    return

def _init_globals2(arg1,arg2,arg3):
    global featured_dataset, processed_days, total_trade_days
    featured_dataset, processed_days, total_trade_days = arg1,arg2,arg3
    return

def _processExtractSecurityData(data):
    symbol = data[0]
    rec = data[1]

    subset = DATASET[DATASET.eval("symbol=='{}'".format(symbol))]
    subset = subset.sort_values(by=['date'],ascending=True)
    rec['start_date'] = subset['date'].iloc[0]
    rec['end_date'] = subset['date'].iloc[-1]

    with processed_secuirties.get_lock():
        processed_secuirties.value+=1
        print("\rProgress: {:>5.2f}% ({:04d}/{})  Symbol: {}   Start: {}   End: {}".format(
            round(processed_secuirties.value/total_secuirties*100,2),processed_secuirties.value,total_secuirties,
            symbol, rec['start_date'], rec['end_date']), end="")
    return rec

def _processExtractTradeDaysFeatures(data):
    trade_date = data[0]
    rec = data[1]
    subset = featured_dataset[featured_dataset.eval("date=='{}'".format(trade_date))]
    if subset.shape[0]>0:
        rec['price_mid']  = round(subset['close'].quantile(0.5),2)
        rec['price_avg']  = round(subset['close'].mean(),2)
        rec['change_mid'] = round(subset['change'].quantile(0.5),2)
        rec['change_avg'] = round(subset['change'].mean(),2)
        rec['max_grow'] = subset[subset.eval('change> 9')].shape[0]
        rec['max_drop'] = subset[subset.eval('change<-9')].shape[0]
        rec['win_rate'] = round(subset[subset.eval('change>=0')].shape[0] / subset.shape[0],2)
    with processed_days.get_lock():
        processed_days.value += 1
        print("\rExtract trade days feature: {:>5.2f}% ({:04d}/{})  Date: {}".format(
            round(processed_days.value/total_trade_days*100,2),
            processed_days.value, total_trade_days, trade_date
        ), end="")
    return rec

def _processExtractFeatures(symbol):
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

    def _find_dropdays(values):
        values = list(values)
        values.reverse()
        days=0
        for v in values:
            if v<=0:
                days +=1
            else:
                break
        return days

    def _find_lossrate(values):
        values = list(values)
        total = len(values)
        days = 0
        for v in values:
            if v<=0: days+=1
        return round(days/total,2)

    subset = DATASET[DATASET.eval("symbol=='{}'".format(symbol))].copy()
    subset['bar'] = round((subset['close'] - subset['open']) / subset['open'] * 100, 2)
    subset['change'] = round((subset['close'] - subset['close'].shift(periods=1))/subset['close'].shift(periods=1) * 100,2)
    subset['open_jump'] = round((subset['open'] - subset['close'].shift(periods=1))/subset['close'].shift(periods=1) * 100,2)
    subset['down_line'] = round((subset['close'] - subset['low']) / subset['close'] * 100, 2)
    subset['up_line']   = round((subset['close'] - subset['high']) / subset['close'] * 100, 2)
    subset['amp'] = round((subset['high'] - subset['low']) / subset['open'] * 100, 2)
    for i in [5,10,30,60]:
        subset['trend_{}'.format(i)] = subset['close'].rolling(window=i).apply(_find_trend,raw=True)
    for i in [10,30,250]:
        subset['pos_{}'.format(i)] = subset['close'].rolling(window=i).apply(_find_pos,raw=True)
    for i in [10]:
        subset['drop_days'.format(i)] = subset['change'].rolling(window=i).apply(_find_dropdays,raw=True)
        subset['lossr_{}'.format(i)] = subset['change'].rolling(window=i).apply(_find_lossrate,raw=True)
    subset = subset.dropna()

    # print progress
    with processed_secuirties.get_lock():
        processed_secuirties.value+=1
        if len(subset)>0:
            print("\rProgress: {:>5.2f}% ({:04d}/{})  Symbol: {}   Records: {}".format(
                    round(processed_secuirties.value/total_secuirties*100,2),
                    processed_secuirties.value, total_secuirties,
                    subset['symbol'].iloc[0], subset.shape[0]), end="")
    return subset
