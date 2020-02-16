
from .base_strategy import BaseStrategy

class MOM(BaseStrategy):
    NAME = 'mom'
    # Feature,   Bias,   Scaler
    FEATURES = [
        ['mom_adx',         0,    0.02],
        ['mom_adxr',        0,    0.02],
        ['mom_mdi',         0,    0.02],
        ['mom_mdm',         0,     0.2],
        ['mom_pdi',         0,    0.02],
        ['mom_pdm',         0,     0.2],
        ['change',          0,      10],
        ['amp_0105',        0,       2],
        ['amp_0510',        0,       1],
    ]
    DNA_LEN = len(FEATURES)*2

    def __init__(self, dna):
        super().__init__()
        self.dna = dna
        return
