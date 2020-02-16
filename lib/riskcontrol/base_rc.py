'''
基础风险控制模块
可配置参数有哪些：
- 最大利润回撤止损
- 浮动止损点步长
- N日最高价止盈点
- N日最低价止损点
- 最高价的浮动边界 +/- 双向性
- 最低价的浮动边界 +/- 双向性
- 仓位调动逻辑
'''

class BaseRiskControl(object):
    NAME = 'risk_control'
    # Feature,   Bias,   Scaler
    FEATURES = [
        ['max_backdraw',            0,  35],
        ['float_stoploss_step',     0,   1],
        ['stoploss_ndays_low',      0,   1],
        ['stopwin_ndays_high',      0,   1],
        ['stoploss_margin',         0,   1],
        ['stopwin_margin',          0,   1],
    ]
    DNA_LEN = len(FEATURES)*2

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
