
from .base_strategy import BaseStrategy

class SAR(BaseStrategy):
    NAME = 'sar'
    # Feature,   Bias,   Scaler
    FEATURES = [
        ['sar_bias',        0,    5],
        ['sar_diff',        0,   30],
        ['sar_diff_pre',    0,   30],
        ['change',          0,   10],
        ['amp_0105',        0,    2],
        ['amp_0510',        0,    1],
    ]
    DNA_LEN = len(FEATURES)*2
