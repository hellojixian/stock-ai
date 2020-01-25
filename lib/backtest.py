class backtest:
    cash = 0
    positions = {}
    buy_commission = 0.00013
    sell_commission = 0.00135

    def __init__(self, init_fund=10000):
        self._init_fund = init_fund
        self.cash = init_fund
        return

    def buy(self, symbol, price, amount):
        cost = (price * amount * (1+self.buy_commission))
        if self.cash < cost:
            raise Exception('No enough cash')

        self.cash -= cost
        if symbol not in self.positions:
            self.positions[symbol]={
                'amount': amount,
                'cost': price
            }
        else:
            original_amount = self.positions[symbol]['amount']
            original_cost = self.positions[symbol]['cost']
            total_amount = original_amount + amount
            self.positions[symbol]['amount'] = total_amount
            self.positions[symbol]['cost'] = round((original_amount*original_cost + amount*price*(1+self.buy_commission)) / total_amount,3)
        return self.cash

    def sell(self, symbol, price, amount=None):
        if symbol not in self.positions:
            raise Exception('Not have the symbol in positions')

        if amount is None or \
           amount>self.positions[symbol]['amount']: amount = self.positions[symbol]['amount']

        value = price * amount
        commission = value * self.sell_commission

        self.cash -= commission
        self.cash += value
        if self.positions[symbol]['amount']==amount:
            del self.positions[symbol]
        else:
            original_amount = self.positions[symbol]['amount']
            original_cost = self.positions[symbol]['cost']
            new_amount = original_amount - amount
            new_cost = (original_amount*original_cost - price*amount) / new_amount
            self.positions[symbol]['amount'] = new_amount
            self.positions[symbol]['cost'] = new_cost
        self.cash = round(self.cash,2)
        return self.cash

    def getCash(self):
        return round(self.cash,3)

    def getValue(self):
        value = self.cash
        for symbol in self.positions:
            value += self.positions[symbol]['amount'] * self.positions[symbol]['cost']
        return round(value,2)
