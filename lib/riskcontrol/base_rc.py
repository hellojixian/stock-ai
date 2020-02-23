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

import sys
import math, os, json
import numpy as np

from lib.backtest import backtest as bt

INIT_FUND = 100000
MIN_BUY_UNIT = 100
BUY_THRESHOLD = 1
SELL_THRESHOLD = 1

class BaseRiskControl(object):
    NAME = 'riskcontrol'
    # Feature,   min,   max
    FEATURES = [
        ['max_stoploss_rate',      -0.10,   0.01],
        ['max_backdraw_rate',       0.01,   0.10],
        ['max_drop_hold',          -0.05,  -0.10],
        ['max_recover_rate',        0.01,   0.08],
        ['init_fund_rate',           0.1,    0.5],
        ['ongoing_fund_rate_loss',   0.1,    0.4],
        ['ongoing_fund_rate_win',    0.1,    0.4],
        ['ongoing_step_loss',       -0.05,  -0.01],
        ['ongoing_step_win',       -0.05,  -0.01],
    ]
    DNA_LEN = len(FEATURES)*2

    def __init__(self, strategy, dna=None):
        self.strategy = strategy()
        self.settings_filename = os.path.join('data','knowledgebase','{}-settings.json'.format(self.NAME))
        if dna is not None:
            self.dna=dna
        else:
            self.load_best_dna()
        self.parse_dna(dna)
        self.test = bt(init_fund=INIT_FUND)
        self.reset()
        self.session_log = []
        self.strategy_result = None
        self.baseline_result = None
        self.last_stoploss_price = None
        self.continue_loss = 0
        return

    def load_best_dna(self):
        if os.path.isfile(self.settings_filename):
            with open(self.settings_filename) as json_file:
                data = json.load(json_file)
                self.dna = np.array(data['learning']['latest_best_dna'])
        return

    def reset(self):
        self.position = 0
        self.session = None
        self.lowest_price = None
        self.last_catch_buy_profit = 0
        self.last_catch_buy_loss = 0
        self.allowed_cash_loss = None
        self.allowed_cash_win = None
        return

    def parse_dna(self,dna):
        self.settings = {}
        for i in range(len(self.FEATURES)):
            setting,vmin,vmax = self.FEATURES[i][0],\
                                self.FEATURES[i][1],\
                                self.FEATURES[i][2]
            self.settings[setting] = vmax - (1-self.dna[i]) * (vmax-vmin)
        return

    def should_keep_hold(self,record):
        decision = False
        # 瞬间大绿柱下跌 等一下反弹再走
        symbol = record['symbol']
        price = record['close']
        if symbol in self.test.positions:
            # max stoploss rate
            if record['change'] <= self.settings['max_drop_hold']:
                self.lowest_price = price
                decision = True

            if self.lowest_price is not None:
                if price < self.lowest_price:
                    self.lowest_price = price

                recover_rate = (price - self.lowest_price)/self.lowest_price
                if recover_rate <= self.settings['max_recover_rate']:
                    decision = True

        return decision

    def should_force_sell(self,record):
        decision = False
        symbol = record['symbol']
        price = record['close']
        if symbol in self.test.positions:
            # max stoploss rate
            cost = self.test.positions[symbol]['cost']
            profit = (price - cost) / cost
            if profit <= self.settings['max_stoploss_rate']:
                decision = True
                self.last_stoploss_price = price
                self.last_stoploss_days = 0

            # max backdraw logic
            backdraw = 0
            if profit > self.session['max_profit']:
                self.session['max_profit'] += profit
            else:
                backdraw = self.session['max_profit'] - profit
            if self.settings['max_backdraw_rate']>0 and backdraw >= self.settings['max_backdraw_rate']:
                decision = True
                self.last_stoploss_price = price
                self.last_stoploss_days = 0
        return decision

    def should_catch_buy(self, record):
        decision = False
        symbol = record['symbol']
        price = record['close']
        if symbol in self.test.positions:
            cost = self.test.positions[symbol]['cost']
            profit = (price - cost) / cost
            if (profit - self.last_catch_buy_loss) < self.settings['ongoing_step_loss']:
                self.last_catch_buy_loss = profit
                decision = True
            if (profit - self.last_catch_buy_profit) > self.settings['ongoing_step_win']:
                self.last_catch_buy_profit = profit
                decision = True
        return decision

    def max_allowed_buy_amount(self, record):
        total_cash = self.test.get_cash()
        symbol = record['symbol']
        price = record['close']
        amount = 0
        if symbol not in self.test.positions:
            #建仓
            allowed_cash = total_cash * self.settings['init_fund_rate']
        else:
            #追仓
            if self.allowed_cash_loss is None:
                self.allowed_cash_loss = total_cash * self.settings['ongoing_fund_rate_loss']
                self.allowed_cash_win = total_cash * self.settings['ongoing_fund_rate_win']

            cost = self.test.positions[symbol]['cost']
            profit = (price - cost) / cost
            if profit > 0:
                allowed_cash = self.allowed_cash_win
            else:
                allowed_cash = self.allowed_cash_loss

            if allowed_cash>total_cash:
                amount = (math.ceil(allowed_cash / (MIN_BUY_UNIT*price))-10) * MIN_BUY_UNIT
        return amount

    def should_ignore_buy(self,record):
        decision = False
        # 忽略买入信号逻辑
        return decision

    def backtest(self, symbol, dataset, baseline_result=None):
        '''
        回测一套既定的止损策略
        返回回测得分
        '''
        self.strategy.backtest(symbol, dataset)
        self.baseline_result = baseline_result
        if self.baseline_result is None:
            self.baseline_result = self.strategy.evalute_result()

        self.dataset = dataset
        self.session_log = []
        self.symbol = dataset.iloc[0]['symbol']
        for idx,record in dataset.iterrows():
            price = record['close']
            if self.session is not None: self.session['days']+=1

            if self.last_stoploss_price is not None:
                self.last_stoploss_days += 1

            if record['symbol'] in self.test.positions \
            and (self.strategy.should_sell(record) or self.should_force_sell(record)) \
            and self.should_keep_hold(record)==False:
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
                    if self.session['change']>0:
                        self.last_stoploss_price = None
                        self.last_stoploss_days = None
                        self.continue_loss = 0
                    else:
                        self.continue_loss += 1
                    self.reset()

            cash = self.test.get_cash()
            if cash > MIN_BUY_UNIT*price and self.strategy.should_buy(record) \
            and self.should_ignore_buy(record)==False or self.should_catch_buy(record):
                amount = self.max_allowed_buy_amount(record)
                if amount>0:
                    if record['symbol'] not in self.test.positions:
                        self.session = {
                            "init_fund": self.test.get_cash(),
                            "start_date": record['date'],
                            "days": 0,
                            "max_profit": 0,
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
        win_p = 0
        loss_p = 1
        for session in self.session_log:
            holding_days += session['days']
            if session['change']>=0:
                wins+=1
                win_p += session['change']
                continue_errs=0
            else:
                loss_p += -session['change']
                continue_errs+=1
            if continue_errs>max_continue_errs:
                max_continue_errs=continue_errs

        win_rate = 0
        if sessions>0:
            win_rate = wins / sessions

        total_days = self.dataset.shape[0]
        sess_rate = sessions / total_days

        wl_rate = 0
        if sess_rate>0.005:
            wl_rate = win_p/loss_p
        profit = (self.test.get_value() - self.test.get_init_fund()) / self.test.get_init_fund()
        baseline = (self.dataset.iloc[-1]['close'] - self.dataset.iloc[0]['close'])/self.dataset.iloc[0]['close']

        self.strategy_result = {
            "symbol": self.symbol,
            "errs": max_continue_errs,
            "sess": sessions,
            "sess_r": sess_rate,
            "win_r": win_rate,
            "wl_rate": wl_rate,
            "profit": profit,
            "baseline": baseline,
            "pb_diff": profit-baseline,
            "hold_days":holding_days,
            "days/sess": holding_days/(sessions+0.01)
        }

        result = {
            "errs_dif":     self.strategy_result["errs"] - self.baseline_result["errs"],
            "winr_dif":     self.strategy_result["win_r"] - self.baseline_result["win_r"],
            "wlr_dif":      self.strategy_result["wl_rate"] - self.baseline_result["wl_rate"],
            "profit_dif":   self.strategy_result["profit"] - self.baseline_result["profit"],
            "daysess_dif":   self.strategy_result["days/sess"] - self.baseline_result["days/sess"],
            "baseline_profit": self.baseline_result["profit"],
            "strategy_profit": self.strategy_result["profit"],
        }

        return result
