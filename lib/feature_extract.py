import talib, math
import sys
import numpy as np

class featureExtractor:
    def processData(dataset):
        try:
            dataset = featureExtractor.extractSimpleFeatures(dataset)
            dataset = featureExtractor.calculateKDJ(dataset)
            dataset = featureExtractor.calculateBBands(dataset)
            dataset = featureExtractor.calculateMACD(dataset)
            dataset = featureExtractor.calculateDrop(dataset)
            dataset = featureExtractor.calculateMA(dataset)
            dataset = featureExtractor.calculateRSI(dataset)
            # 清理数据
            dataset = dataset.dropna()
        except:
            pass
        return dataset

    def extractSimpleFeatures(dataset):
        def _find_trend(values):
            values = list(values)
            p_min, p_max = np.min(values), np.max(values)
            p_min_idx, p_max_idx = values.index(p_min), values.index(p_max)
            total = len(values)
            trend = (p_max_idx-p_min_idx)/total
            return trend

        def _find_pos(values):
            values = list(values)
            close = values[-1]
            p_min, p_max = np.min(values), np.max(values)
            pos = (close - p_min) / (p_max - p_min) * 100
            pos = np.round(pos,2)
            return pos

        def _find_dropdays(values, total):
            values = list(values)
            values.reverse()
            days=0
            for v in values:
                if v<=0:
                    days +=1
                else:
                    break
            return days/total

        def _find_lossrate(values):
            values = list(values)
            total = len(values)
            days = 0
            for v in values:
                if v<=0: days+=1
            return round(days/total,2)

        subset = dataset.copy()
        subset.loc[:,'bar'] = (subset['close'] - subset['open']) / subset['open']
        subset.loc[:,'change'] = (subset['close'] - subset['close'].shift(periods=1))/subset['close'].shift(periods=1)
        subset.loc[:,'change_diff'] = subset['change'] - subset['change'].shift(periods=1)
        subset.loc[:,'open_jump'] = (subset['open'] - subset['close'].shift(periods=1))/subset['close'].shift(periods=1)
        subset.loc[:,'down_line'] = (subset['close'] - subset['low']) / subset['close']
        subset.loc[:,'up_line']   = (subset['close'] - subset['high']) / subset['close']
        subset.loc[:,'amp'] = (subset['high'] - subset['low']) / subset['open']
        for i in [5,10]:
            subset.loc[:,'amp_{}'.format(i)] = subset.loc[:,'amp'].rolling(window=i).mean()
        subset.loc[:,'amp_0105'] = (subset['amp'] - subset['amp_5']) / subset['amp_5']
        subset.loc[:,'amp_0510'] = (subset['amp_5'] - subset['amp_10']) / subset['amp_10']
        for i in [5,10,30,60]:
            subset.loc[:,'trend_{}'.format(i)] = subset['close'].rolling(window=i).apply(_find_trend,raw=True)
        for i in [10,30,250]:
            subset.loc[:,'pos_{}'.format(i)] = subset['close'].rolling(window=i).apply(_find_pos,raw=True)
        for i in [7]:
            subset.loc[:,'drop_days'.format(i)] = subset['change'].rolling(window=i).apply(_find_dropdays,args=(i,),raw=True)
            subset.loc[:,'lossrate'.format(i)] = subset['change'].rolling(window=i).apply(_find_lossrate,raw=True)
        subset = subset.dropna()
        return subset

    def calculateDrop(dataset):
        dataset.loc[:,'drop_score'] = np.tan(dataset['drop_days']/5)
        dataset.loc[:,'drop_score'] = dataset['drop_score'].clip(0,1)
        return dataset

    def calculateMA(dataset):
        # ma_bias + 为价格过高，  - 为价格过低
        settings = [ {'period':5,  'min':-0.08, 'max':0.08},
                     {'period':10, 'min':-0.10, 'max':0.10},
                     {'period':20, 'min':-0.15, 'max':0.15},
                     {'period':30, 'min':-0.20, 'max':0.20} ]
        for setting in settings:
            period, vmin, vmax = setting['period'], setting['min'], setting['max']
            dataset.loc[:,'ma{}'.format(period)] = talib.MA(dataset['close'].values, timeperiod=period, matype=0)
            dataset.loc[:,'ma{}_bias'.format(period)] = (dataset['ma{}'.format(period)] - dataset['close']) / dataset['close']
            dataset.loc[:,'ma{}_score'.format(period)] = np.tan((dataset.loc[:,'ma{}_bias'.format(period)]-vmin)/(vmax-vmin)-0.5)+0.5
            dataset.loc[:,'ma{}_score'.format(period)] = dataset['ma{}_score'.format(period)].clip(0,1)
        return dataset

    def calculateKDJ(dataset):
        #计算KDJ的J值和移动方向
        dataset = dataset.copy()
        slowk, slowd = talib.STOCH(dataset['high'].values,
                                    dataset['low'].values,
                                    dataset['close'].values,
                                fastk_period=5, slowk_period=3,
                                slowk_matype=0, slowd_period=3,
                                slowd_matype=0)
        j = slowk*3 - slowd*2
        dataset.loc[:,'kdj_j'] = j
        dataset.loc[:,'kdj_j_move'] = (dataset['kdj_j'] - dataset['kdj_j'].shift(periods=1))/dataset['kdj_j'].shift(periods=1)
        dataset.loc[:,'kdj_j_move_prev'] = dataset['kdj_j_move'].shift(periods=1)
        vmin, vmax = -15, 115
        dataset.loc[:,'kdj_score'] = np.tan((j-vmin)/(vmax-vmin)-0.5)+0.5
        dataset.loc[:,'kdj_score'] = dataset['kdj_score'].clip(0,1)
        return dataset


    def calculateBBands(dataset):
        # 计算布林带
        dataset = dataset.copy()
        upper, middle, lower = talib.BBANDS(
                        dataset['close'].values,
                        timeperiod=20,
                        # number of non-biased standard deviations from the mean
                        nbdevup=2,
                        nbdevdn=2,
                        # Moving average type: simple moving average here
                        matype=0)
        bb_pos = round((dataset['close'] - lower)/(upper - lower) ,3)
        bb_scope = round((upper - lower) / dataset['close'], 3)
        dataset.loc[:,'bb_pos'] = bb_pos
        dataset.loc[:,'bb_scope'] = bb_scope
        score = bb_pos * bb_scope
        vmin, vmax = 0, 0.35
        score = (score - vmin) / (vmax-vmin)
        dataset.loc[:,'bb_score'] = np.tan(bb_pos-0.5)+0.5
        dataset.loc[:,'bb_score'] = dataset['bb_score'].clip(0.1)
        return dataset

    def calculateMACD(dataset):
        dataset = dataset.copy()
        dif, dea, hist = talib.MACD(dataset['close'].values,
                                    fastperiod=12,
                                    slowperiod=26,
                                    signalperiod=9)
        dataset.loc[:,'macd_dif'] = np.round(dif,3)
        dataset.loc[:,'macd_dea'] = np.round(dea,3)
        dataset.loc[:,'macd_bar'] = np.round(hist*2,3)
        vmin, vmax = -0.5, 0.5
        dataset.loc[:,'macd_score'] = np.tan((dataset['macd_bar'] - vmin) / (vmax-vmin)-0.5)+0.5
        dataset.loc[:,'macd_score'] = dataset['macd_score'].clip(0.1)
        return dataset

    def calculateRSI(dataset):
        vmin, vmax = 15, 85
        dataset.loc[:,'rsi_7'] = talib.RSI(dataset['close'].values, timeperiod=7)
        dataset.loc[:,'rsi_14'] = talib.RSI(dataset['close'].values, timeperiod=14)
        dataset.loc[:,'rsi_diff'] = dataset['rsi_7'] - dataset['rsi_7'].shift(periods=1)
        dataset.loc[:,'rsi_bias'] = dataset['rsi_7'] - dataset['rsi_14']
        return dataset
