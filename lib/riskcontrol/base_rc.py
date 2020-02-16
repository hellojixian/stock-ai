'''
基础风险控制模块
可配置参数有哪些：
- 最大利润回撤止损
- 浮动止损点
- 最大止损点
- 最大止盈点
'''

class BaseRiskControl(object):
    def __init__(self, strategy):
        self.strategy = strategy
        return

    def reset(self):
        return

    def should_keep_hold(self):
        decision = False
        return decision

    def should_force_sell(self):
        decision = False
        return decision

    def backtest(self, symbol, dataset):
        '''
        回测一套既定的止损策略
        返回回测得分
        '''


        return




class RiskControl(BaseRiskControl):
    NAME = 'risk_control'
    # Feature,   Bias,   Scaler
    FEATURES = [
        ['ma5_diff',    0,  35],
        ['ma5_bias',    0,  10],
        ['ma10_bias',   0,  10],
        ['ma20_bias',   0,  15],
        ['ma30_bias',   0,  20],
        ['ma_0510',     0,  20],
        ['change',      0,  10],
        ['amp_0105',    0,  2],
        ['amp_0510',    0,  1],
    ]
    DNA_LEN = len(FEATURES)*2

    def __init__(self, dna):
        super().__init__()
        self.dna = dna
        return
