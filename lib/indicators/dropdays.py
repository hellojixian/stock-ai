
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
    DNA_LEN = 12

    def __init__(self, dna):
        super().__init__()
        self.dna = dna
        self.parse_dna(dna)
        return

    def parse_dna(self, dna):
        self.buy_lossrate_weight           = dna[0]
        self.buy_drop_days_weight          = dna[1]
        self.buy_last_change_weight        = dna[2]
        self.buy_change_diff_weight        = dna[3]
        self.buy_amp0105_weight            = dna[4]
        self.buy_amp0510_weight            = dna[5]

        self.sell_lossrate_weight          = dna[6]
        self.sell_drop_days_weight         = dna[7]
        self.sell_last_change_weight       = dna[8]
        self.sell_change_diff_weight       = dna[9]
        self.sell_amp0105_weight           = dna[10]
        self.sell_amp0510_weight           = dna[11]
        return

    def dump_dna(self):
        print("DNA: {}".format(self.dna))
        return

    def get_buy_score(self, record):
        score = 0
        score += record['lossrate']         * self.buy_lossrate_weight
        score += record['change']*10        * self.buy_last_change_weight
        score += record['change_diff']*10   * self.buy_change_diff_weight
        score += record['drop_days']        * self.buy_drop_days_weight
        score += record['amp_0105']         * self.buy_amp0105_weight
        score += record['amp_0510']*2       * self.buy_amp0510_weight
        return score

    def get_sell_score(self, record):
        score = 0
        score += record['lossrate']         * self.sell_lossrate_weight
        score += record['change']*10        * self.sell_last_change_weight
        score += record['change_diff']*10   * self.sell_change_diff_weight
        score += record['drop_days']        * self.sell_drop_days_weight
        score += record['amp_0105']         * self.sell_amp0105_weight
        score += record['amp_0510']*2       * self.sell_amp0510_weight
        return score
