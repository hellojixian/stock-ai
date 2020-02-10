from .dropdays import DropDays
from .trend import Trend
from .rsi import RSI
from .ma import MA
from .kdj import KDJ

indicators = {
    'rsi':RSI,
    'kdj':KDJ,
    'ma':MA,
    'trend':Trend,
    'dropdays':DropDays
}
