import talib

class featureExtractor:
    def processData(dataset):
        dataset = featureExtractor.calcuateKDJ(dataset)
        dataset = featureExtractor.calcuateBBands(dataset)
        # 清理数据
        dataset = dataset.dropna()
        return dataset

    def calcuateKDJ(dataset):
        #计算KDJ的J值和移动方向
        slowk, slowd = talib.STOCH(dataset['high'], dataset['low'], dataset['close'],
                                fastk_period=5, slowk_period=3,
                                slowk_matype=0, slowd_period=3,
                                slowd_matype=0)
        j = slowk*3 - slowd*2
        dataset['kdj_j'] = j
        dataset['kdj_j_move'] = (dataset['kdj_j'] - dataset['kdj_j'].shift(periods=1))/dataset['kdj_j'].shift(periods=1)
        dataset['kdj_j_move_prev'] = dataset['kdj_j_move'].shift(periods=1)
        return dataset

    def calcuateBBands(dataset):
        # 计算布林带
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
        dataset['bb_pos'] = bb_pos
        dataset['bb_scope'] = bb_scope
        return dataset
