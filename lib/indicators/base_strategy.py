

from lib.backtest import backtest as bt
import sys
import math

INIT_FUND = 100000
MIN_BUY_UNIT = 100
BUY_THRESHOLD = 1
SELL_THRESHOLD = 1


class BaseStrategy(object):    

    def __init__(self):
        self.test = bt(init_fund=INIT_FUND)
        self.reset()
        self.session_log = []
        return

    def reset(self):
        self.position = 0
        self.session = None
        return

    def backtest(self, symbol,dataset):
        self.dataset = dataset
        for idx,record in dataset.iterrows():
            price = record['close']
            if self.session is not None: self.session['days']+=1

            if record['symbol'] in self.test.positions and self.should_sell(record):
                self.test.sell(symbol, price=price)
                self.session['end_fund'] = self.test.get_cash()
                self.session['change'] = round((self.session['end_fund'] - self.session['init_fund'])/self.session['init_fund']*100,3)
                self.session['end_date'] = record['date']
                self.session['log'].append({"date":record['date'],
                                            "action":"sell",
                                            "symbol":symbol,
                                            "session": self.session['change'],
                                            "value":self.test.get_value()})
                self.session_log.append(self.session)
                self.reset()

            cash = self.test.get_cash()
            if cash > MIN_BUY_UNIT*price and self.should_buy(record):
                amount = (math.ceil(cash / (MIN_BUY_UNIT*price))-10) * MIN_BUY_UNIT
                if amount>0:
                    if record['symbol'] not in self.test.positions:
                        self.session = {
                            "init_fund": self.test.get_cash(),
                            "start_date": record['date'],
                            "days": 0,
                            "log": [] }
                    self.test.buy(symbol, price=price, amount=amount)
                    self.session['log'].append({"date":record['date'],
                                                "action":"buy ",
                                                "symbol":symbol,
                                                "value":self.test.get_value()})

        return self.evalute_result()

    def evalute_result(self):
        sessions = len(self.session_log)
        wins,continue_errs,max_continue_errs = 0,0,0
        holding_days = 0
        for session in self.session_log:
            holding_days += session['days']
            if session['change']>=0:
                wins+=1
                continue_errs=0
            else:
                continue_errs+=1
            if continue_errs>max_continue_errs:
                max_continue_errs=continue_errs

        win_rate = 0
        if sessions>0: win_rate = wins / sessions
        profit = (self.test.get_value() - self.test.get_init_fund()) / self.test.get_init_fund()
        baseline = (self.dataset.iloc[-1]['close'] - self.dataset.iloc[0]['close'])/self.dataset.iloc[0]['close']
        return {
            "max_continue_errs": max_continue_errs,
            "sessions": sessions,
            "win_rate": round(win_rate,3),
            "profit": round(profit,3),
            "baseline": round(baseline,3),
            "holding_days":holding_days,
            "holding_days_rate": round(holding_days/self.dataset.shape[0],3)
        }

    def should_sell(self, record):
        decsion = False
        if self.get_buy_score(record) >= BUY_THRESHOLD: decsion = True
        return decsion

    def should_buy(self, record):
        decsion = False
        if self.get_sell_score(record) >= SELL_THRESHOLD: decsion = True
        return decsion
