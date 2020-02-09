
from .base_strategy import BaseStrategy

class Trend(BaseStrategy):
    '''
     trend_5 - 5日趋势数值
     trend_10 - 10日趋势数值
     trend_30 - 30日趋势数值
     trend_60 - 60日趋势数值
     pos_10 - 10日价格位置
     pos_30 - 30日价格位置
     pos_250 - 250日价格位置
     last_change - 最后一日价格变动
     amp_0105 - 近期振幅变化
     amp_0510 - 远期振幅变化
    '''

    NAME = 'trend'
    # Feature,   Bias,   Scaler
    FEATURES = [
        ['pos_10',      0,  1],
        ['pos_30',      0,  1],
        ['pos_250',     0,  1],
        ['trend_5',     0,  1],
        ['trend_10',    0,  1],
        ['trend_30',    0,  1],
        ['trend_60',    0,  1],
        ['change',      0,  10],
        ['amp_0105',    0,  2],
        ['amp_0510',    0,  1],
    ]
    DNA_LEN = len(FEATURES)*2

    def __init__(self, dna):
        super().__init__()
        self.dna = dna
        return

    def get_buy_score(self, record):
        return super
