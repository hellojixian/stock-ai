
from .base_strategy import BaseStrategy

class KDJ(BaseStrategy):
    NAME = 'kdj'
    # Feature,   Bias,   Scaler
    FEATURES = [
        ['kdj_j_scaled',  -0.5,  2],
        ['kdj_j_diff',       0,  3],
        ['kdj_j_diff_prev',  0,  3],
        ['kdj_j_bias',       0,  0.02],
        ['change',      0,  10],
        ['amp_0105',    0,  2],
        ['amp_0510',    0,  1],
    ]
    DNA_LEN = len(FEATURES)*2
