from .dropdays import DropDays
from .trend import Trend
from .rsi import RSI
from .ma import MA
from .kdj import KDJ
from .macd import MACD
from .boll import BOLL
from .sar import SAR

indicators = {
    'rsi':      RSI,
    'kdj':      KDJ,
    'ma':       MA,
    'macd':     MACD,
    'boll':     BOLL,
    'sar':     SAR,
    'trend':    Trend,
    'dropdays': DropDays
}
