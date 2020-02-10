from .dropdays import DropDays
from .trend import Trend
from .rsi import RSI
from .ma import MA

indicators = {
    'rsi':RSI,
    'ma':MA,
    'trend':Trend,
    'dropdays':DropDays
}
