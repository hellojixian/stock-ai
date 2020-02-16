
from .base_strategy import BaseStrategy

class CCI(BaseStrategy):
    NAME = 'cci'
    # Feature,   Bias,   Scaler
    FEATURES = [
        ['cci_bias',      0,   100],
        ['cci_7',         0,   100],
        ['cci_7_diff',    0,   100],
        ['cci_14',        0,   100],
        ['cci_14_diff',   0,   100],
        ['cci_25',        0,     2],
        ['change',        0,    10],
        ['amp_0105',      0,     2],
        ['amp_0510',      0,     1],
    ]
    DNA_LEN = len(FEATURES)*2

    def __init__(self, dna):
        super().__init__()
        self.dna = dna
        return
