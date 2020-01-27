'''
策略包含什么？
-进入时机策略
-出场时机
-止损设定

布林带，连绿，支撑位，KDJ，MACD 均具有买入和卖出信号，动态调整的是每种信号的阈值和权重
通过累和来得到每刻股票的得分，设定总得分触发点作为反馈

到达心动点以后等待二次确认


'''

from lib.backtest import backtest as bt

INIT_FUND = 100000
MIN_BUY_UNIT = 100

class strategy:
    def __init__(self, dna):
        self.test = bt(init_fund=INIT_FUND)
        self.parse_dna(dna)
        self.reset()
        return

    def parse_dna(self,dna):
        batch_settings = [
            [1],
            [0.3,0.7],
            [0.4,0.6],
            [0.5,0.5],
            [0.1,0.3,0.6],
            [0.2,0.3,0.5],
            [0.2,0.5,0.3],
            [0.3,0.3,0.4]
        ]

        self.buy_batch_id       = dna[0]
        self.bug_bbands_weight  = dna[1]
        self.bug_drop_weight    = dna[2]
        self.bug_trend_weight   = dna[3]
        self.bug_support_weight = dna[4]
        self.bug_kdj_weight     = dna[5]
        self.bug_macd_weight    = dna[6]
        self.buy_delay          = dna[7]

        self.sell_bbands_weight  = dna[8]
        self.sell_drop_weight    = dna[9]
        self.sell_trend_weight   = dna[10]
        self.sell_support_weight = dna[11]
        self.sell_kdj_weight     = dna[12]
        self.sell_macd_weight    = dna[13]
        self.sell_delay          = dna[14]

        self.stop_loss_rate      = dna[15]
        self.stop_win_rate       = dna[16]
        self.stop_win_days       = dna[17]

        self.buy_batchs = batch_settings[self.buy_batch_id]
        self.buy_threshold  = 10
        self.sell_threshold = 10
        return

    def reset(self):
        self.position = 0 #当前仓位
        self.buy_current_batch = 0
        return

    def backtest(self, symbol,dataset):
        for idx,record in dataset.iterrows():
            price = record['close']

            if self.should_sell(record):
                self.test.sell(symbol, price=price)
                self.reset()

            if self.test.get_cash() > MIN_BUY_UNIT*price and self.should_buy(record):
                amount = self.buy_amount(price)
                self.position = 0.5
                self.test.buy(symbol, price=price, amount=amount)
        return

    def buy_amount(self, price):
        if self.buy_current_batch+1 >= len(self.buy_batchs): return 0
        self.buy_current_batch+=1
        ratio = self.buy_batchs[self.buy_current_batch]
        limited_cash = self.test.get_value() * ratio
        amount = int(limited_cash / (price*100))
        return amount

    def should_buy(self, record):
        return

    def should_sell(self, record):
        return
