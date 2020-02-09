
from .base_strategy import BaseStrategy

class RSI(BaseStrategy):
    NAME = 'rsi'
    # Feature,   Bias,   Scaler
    FEATURES = [
        ['rsi_7',       0,  0.1],
        ['rsi_14',      0,  0.1],
        ['rsi_diff',    0,  0.1],
        ['rsi_bias',    0,  0.1],        
        ['change',      0,  10],
        ['amp_0105',    0,  2],
        ['amp_0510',    0,  1],
    ]
    DNA_LEN = len(FEATURES)*2

    def __init__(self, dna):
        super().__init__()
        self.dna = dna
        return
