
from .base_strategy import BaseStrategy

class BOLL(BaseStrategy):
    NAME = 'boll'
    # Feature,   Bias,   Scaler
    FEATURES = [
        ['bb_pos',      -0.5,     1],
        ['bb_diff',        0,   100],
        ['bb_diff_prev',   0,   100],
        ['bb_scope',       0,    20],
        ['change',         0,    10],
        ['amp_0105',       0,     2],
        ['amp_0510',       0,     1],
    ]
    DNA_LEN = len(FEATURES)*2

    def __init__(self, dna):
        super().__init__()
        self.dna = dna
        return
