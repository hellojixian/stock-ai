
from .base_strategy import BaseStrategy

class BOLL(BaseStrategy):
    NAME = 'boll'
    # Feature,   Bias,   Scaler
    FEATURES = [
        ['bb_pos',      -0.5,  0.02],
        ['bb_diff',        0,  20],
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
