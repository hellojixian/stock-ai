
from .base_strategy import BaseStrategy

class MACD(BaseStrategy):
    NAME = 'macd'
    # Feature,   Bias,   Scaler
    FEATURES = [
        ['rsi_3',       -50,  0.02],
        ['rsi_7',       -50,  0.02],
        ['rsi_14',      -50,  0.02],
        ['rsi_diff',    0,  0.01],
        ['rsi_diff_pre',0,  0.01],
        ['rsi_bias',    0,  0.01],
        ['change',      0,  10],
        ['amp_0105',    0,  2],
        ['amp_0510',    0,  1],
    ]
    DNA_LEN = len(FEATURES)*2

    def __init__(self, dna):
        super().__init__()
        self.dna = dna
        return
