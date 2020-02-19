
from .base_strategy import BaseStrategy

class MA(BaseStrategy):
    NAME = 'ma'
    # Feature,   Bias,   Scaler
    FEATURES = [
        ['ma5_diff',    0,  35],
        ['ma5_bias',    0,  10],
        ['ma10_bias',   0,  10],
        ['ma20_bias',   0,  15],
        ['ma30_bias',   0,  20],
        ['ma_0510',     0,  20],
        ['change',      0,  10],
        ['amp_0105',    0,  2],
        ['amp_0510',    0,  1],
    ]
    DNA_LEN = len(FEATURES)*2
