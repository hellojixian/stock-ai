
from .base_strategy import BaseStrategy

class MACD(BaseStrategy):
    NAME = 'macd'
    # Feature,   Bias,   Scaler
    FEATURES = [
        ['macd_bar',        0,  2],
        ['macd_dif',        0,  1],
        ['macd_dea',        0,  1],
        ['macd_change',     0,  1],
        ['macd_price_c',    0,  1],
        ['change',      0,  10],
        ['amp_0105',    0,  2],
        ['amp_0510',    0,  1],
    ]
    DNA_LEN = len(FEATURES)*2

    def __init__(self, dna):
        super().__init__()
        self.dna = dna
        return
