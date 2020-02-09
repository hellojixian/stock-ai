
from .base_strategy import BaseStrategy

class DropDays(BaseStrategy):
    '''
     lossrate - 最近7日内几天是下跌的
     drop_days - 连续下跌天数
     last_change - 最后一只的涨跌
     change_diff - 两日涨跌差今天减去昨天 正数增量上涨 否则下跌
     amp_0105 - 近期振幅变化
     amp_0510 - 远期振幅变化
    '''

    NAME = 'dropdays'
    FEATURES = [
        ['lossrate',    0,  1],
        ['drop_days',   0,  1],
        ['change_diff', 0,  10],
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
        return super().get_buy_score(record)

    def get_sell_score(self, record):
        return super().get_sell_score(record)
