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
import sys
import math

INIT_FUND = 100000
MIN_BUY_UNIT = 100
DNA_LEN = 26
MAX_BUY_DELAY_DAYS = 5
MAX_SELL_DELAY_DAYS = 5

class strategy:
    def __init__(self, dna):
        if len(dna)!=DNA_LEN:
            raise Exception("DNA Length mismatched, expected {} got {}".format(DNA_LEN, len(dna)))
        self.test = bt(init_fund=INIT_FUND)
        self.parse_dna(dna)
        self.reset()
        self.session_log = []
        return

    def parse_dna(self,dna):
        batch_settings = [
            [1],
            [0.8],
            [0.3,0.7],
            [0.4,0.6],
            [0.5,0.5],
            [0.1,0.2,0.5],
            [0.1,0.3,0.6],
            [0.2,0.3,0.5],
            [0.2,0.5,0.3],
            [0.3,0.3,0.4]
        ]

        self.buy_batch_id           = int(dna[0]*0.5*len(batch_settings)-1)
        self.buy_bbands_weight      = dna[1]
        self.buy_drop_weight        = dna[2]
        self.buy_trend5_weight      = dna[3]
        self.buy_trend10_weight     = dna[4]
        self.buy_trend30_weight     = dna[5]
        self.buy_trend60_weight     = dna[6]
        self.buy_pos10_weight       = dna[7]
        self.buy_pos30_weight       = dna[8]
        self.buy_pos250_weight      = dna[9]
        self.buy_support_weight     = dna[10]
        self.buy_kdj_weight         = dna[11]
        self.buy_macd_weight        = dna[12]
        self.buy_delay              = dna[13]

        self.sell_bbands_weight     = dna[14]
        self.sell_drop_weight       = dna[15]
        self.sell_trend5_weight     = dna[16]
        self.sell_trend10_weight    = dna[17]
        self.sell_pos10_weight      = dna[18]
        self.sell_support_weight    = dna[19]
        self.sell_kdj_weight        = dna[20]
        self.sell_macd_weight       = dna[21]
        self.sell_delay             = dna[22]

        self.stop_loss_rate         = dna[23]*0.05
        self.stop_win_rate          = dna[24]*0.05
        self.stop_win_days          = int(dna[25]*10)
        # self.patch_buy_rate         = -0.1

        self.buy_batchs = batch_settings[self.buy_batch_id]
        self.buy_threshold  = 6
        self.sell_threshold = 4
        return

    def reset(self):
        self.position = 0 #当前仓位
        self.buy_current_batch = 0
        self.session = None

        self.reset_buy_delay()
        self.reset_sell_delay()
        return

    def reset_buy_delay(self):
        self.buy_delay_observing = False
        self.buy_cheaper_than = 0
        self.buy_delay_days = 0
        return

    def reset_sell_delay(self):
        self.sell_delay_observing = False
        self.sell_higher_than = 0
        self.sell_delay_days = 0
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

            if self.test.get_cash() > MIN_BUY_UNIT*price and self.should_buy(record):
                amount = self.buy_amount(price)
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

        win_rate = wins / sessions
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

    def buy_amount(self, price):
        if self.buy_current_batch >= len(self.buy_batchs): return 0
        ratio = self.buy_batchs[self.buy_current_batch]
        limited_cash = self.test.get_value() * ratio
        available_cash = self.test.get_cash()*0.95
        amount = (math.ceil(limited_cash / (price*100)))*100 - 1000
        if amount * price >= available_cash:
            amount = math.ceil(available_cash / price) - 1000
        if amount * price >= available_cash:
            raise Exception('{} * {}={} > {}'.format(amount, price,amount* price,available_cash))
        self.buy_current_batch+=1
        return amount

    def should_buy(self, record):
        # 补仓逻辑
        symbol = record['symbol']
        if symbol in self.test.positions:
            cost = self.test.positions[symbol]['cost']
            price = record['close']
            change = ( price - cost ) / cost
            if change>=0: return True
            # if change< self.patch_buy_rate: return True

        decsion = False
        if self.buy_delay_observing:
            self.buy_delay_days +=1
            if self.buy_delay_days > MAX_BUY_DELAY_DAYS: self.reset_buy_delay()
            if record['close'] <= self.buy_cheaper_than:
                decsion = True
                self.reset_buy_delay()
        else:
            score = 0
            score += record['bb_score']     *  self.buy_bbands_weight
            score += record['drop_score']   *  self.buy_drop_weight
            score += record['trend_5']      *  self.buy_trend5_weight
            score += record['trend_10']     *  self.buy_trend10_weight
            score += record['trend_30']     *  self.buy_trend30_weight
            score += record['trend_60']     *  self.buy_trend60_weight
            score += record['pos_10']/100   *  self.buy_pos10_weight
            score += record['pos_30']/100   *  self.buy_pos30_weight
            score += record['pos_250']/100  *  self.buy_pos250_weight
            score += record['support_score']*  self.buy_support_weight
            score += record['kdj_score']    *  self.buy_kdj_weight
            score += record['macd_score']   *  self.buy_macd_weight


            if score>= self.buy_threshold:
                if self.buy_delay==1:
                    self.buy_delay_observing = True
                    self.buy_delay_days = 0
                    self.buy_cheaper_than = record['close']
                    decsion = False
                else:
                    decsion = True
        return decsion

    def should_sell(self, record):
        decsion = False

        symbol = record['symbol']
        if symbol in self.test.positions:
            # 处理止盈止损
            if self.session is None:
                print(self.test.positions)
                raise Exception("Session is NONE")
            if self.session['days']>=self.stop_win_days:
                self.session['end_type'] = 'stop_holding'
                return True
            cost = self.test.positions[symbol]['cost']
            price = record['close']
            change = ( price - cost ) / cost
            if change >= self.stop_win_rate:
                self.session['end_type'] = 'stop_win'
                return True
            if change <= -self.stop_loss_rate:
                self.session['end_type'] = 'stop_loss'
                return True


        if self.sell_delay_observing:
            self.sell_delay_days +=1
            if self.sell_delay_days > MAX_SELL_DELAY_DAYS: self.reset_sell_delay()
            if record['close'] >= self.sell_higher_than:
                decsion = True
                self.reset_sell_delay()
        else:
            score = 0
            score += (1-record['bb_score'])     *  self.sell_bbands_weight
            score += (1-record['drop_score'])   *  self.sell_drop_weight
            score += (1-record['trend_5'])      *  self.sell_trend5_weight
            score += (1-record['trend_10'])     *  self.sell_trend10_weight
            score += (1-record['pos_10']/100)   *  self.sell_pos10_weight
            score += (1-record['support_score'])*  self.sell_support_weight
            score += (1-record['kdj_score'])    *  self.sell_kdj_weight
            score += (1-record['macd_score'])   *  self.sell_macd_weight

            if score>= self.sell_threshold:
                self.session['end_type'] = 'regular'
                if self.sell_delay==1:
                    self.sell_delay_observing = True
                    self.sell_delay_days = 0
                    self.sell_cheaper_than = record['close']
                    decsion = False
                else:
                    decsion = True
        return decsion
