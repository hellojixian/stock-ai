import talib

class featureExtractor:
    def processData(dataset):
        dataset = featureExtractor.calculateKDJ(dataset)
        dataset = featureExtractor.calculateBBands(dataset)
        dataset = featureExtractor.calculateMACD(dataset)
        dataset = featureExtractor.calculateDrop(dataset)
        dataset = featureExtractor.calculateSupport(dataset)
        # 清理数据
        dataset = dataset.dropna()
        return dataset

    def calculateDrop(dataset):
        dataset['drop_score'] = dataset['drop_days']/10
        return dataset

    def calculateKDJ(dataset):
        #计算KDJ的J值和移动方向
        dataset = dataset.copy()
        slowk, slowd = talib.STOCH(dataset['high'], dataset['low'], dataset['close'],
                                fastk_period=5, slowk_period=3,
                                slowk_matype=0, slowd_period=3,
                                slowd_matype=0)
        j = slowk*3 - slowd*2
        dataset.loc[:,'kdj_j'] = j
        dataset.loc[:,'kdj_j_move'] = (dataset['kdj_j'] - dataset['kdj_j'].shift(periods=1))/dataset['kdj_j'].shift(periods=1)
        dataset.loc[:,'kdj_j_move_prev'] = dataset['kdj_j_move'].shift(periods=1)
        vmin, vmax = -15, 115
        dataset.loc[:,'kdj_score'] = (j-vmin)/(vmax-vmin)
        return dataset


    def calculateBBands(dataset):
        # 计算布林带
        dataset = dataset.copy()
        upper, middle, lower = talib.BBANDS(
                        dataset['close'],
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
        dataset.loc[:,'bb_score'] = score
        return dataset

    def calculateMACD(dataset):
        dataset = dataset.copy()
        dif, dea, hist = talib.MACD(dataset['close'],
                                    fastperiod=12,
                                    slowperiod=26,
                                    signalperiod=9)
        dataset.loc[:,'macd_dif'] = round(dif,3)
        dataset.loc[:,'macd_dea'] = round(dea,3)
        dataset.loc[:,'macd_bar'] = round(hist*2,3)
        vmin, vmax = -0.5, 0.5
        dataset.loc[:,'macd_score'] = (dataset['macd_bar'] - vmin) / (vmax-vmin)
        return dataset

    def calculateSupport(dataset):
        dataset['mid_price'] = dataset[['open','close','high','low']].mean(axis=1)
        lookback_size = 120

        def _calculate(close,subset):
            pressure_price,support_price = 0,0
            subset = subset.copy()
            close = round(close,3)
            price_min, price_max = subset['mid_price'].min(),subset['mid_price'].max()
            step = (price_max - price_min) / 20
            subset['price_tier'] = round(subset['mid_price']/step)*step
            stats = subset[['price_tier','volume']].groupby(['price_tier']).sum()
            stats['price'] = stats.index
            support  = stats[stats.eval('price<={}'.format(close))].sort_values(by=['volume'])
            pressure = stats[stats.eval('price>={}'.format(close))].sort_values(by=['volume'])
            if len(support)>0:
                support_price   = round(support.iloc[0]['price'],3)
            if len(pressure)>0:
                pressure_price  = round(pressure.iloc[0]['price'],3)

            if support_price==0:
                support_pos=0
            elif pressure_price==0:
                support_pos=1
            else:
                support_pos = (pressure_price-close) / (pressure_price-support_price)
            pressure_pos = 1-support_pos
            return support_pos, pressure_pos

        for i in range(lookback_size-1, dataset.shape[0]):
            subset = dataset[i-lookback_size+1:i+1]
            loc = dataset.iloc[i].name
            dataset.loc[loc,'support_score'],_ \
                =  _calculate(subset.iloc[-1]['close'],subset[['date','mid_price','volume']])

        dataset = dataset.dropna()
        return dataset
