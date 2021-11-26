from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN
from locale import localeconv

from typing import Dict


def delocalize(st):
    # type: (str) -> str
    """Parses a string as a normalized number according to the locale settings."""

    conv = localeconv()

    # First, get rid of the currency symbol
    cs = conv["currency_symbol"]
    st = st.strip(cs if cs else "$")

    # next, get rid of the grouping
    ts = conv["thousands_sep"]
    st = st.replace(ts if ts else ",", "")

    # next, replace the decimal point with a dot
    dp = conv["decimal_point"]

    return st.replace(dp, ".") if dp else st
# end delocalize(str)


_PREC2 = Decimal("0.00")
_PREC6 = Decimal("0.000000")
_PREC7 = Decimal("0.0000000")
# noinspection SpellCheckingInspection
_TICKR = {"HI YLD EMG MKT BOND" : ("NON40OJFI", _PREC7),
          "INFL PROTECTED BOND" : ("NON40OJFB", _PREC7),
          "INTEREST INCOME FUND": ("NON40OJFA", _PREC7),
          "PIM INTL BD US$H I"  : ("PFORX"    , _PREC2),
          "TARGETRETIREMENT2040": ("NON40OJGZ", _PREC7),
          "TOTAL BOND MARKET"   : ("NON40OJFC", _PREC6)}


class NbHolding(object):
    """Houses details for a holding"""

    def __init__(self, name, dataDict, effDate):
        # type: (str, Dict[str, str], date) -> None
        self.name = name  # type: str
        self.ticker, self.prec = _TICKR[name]
        self.bal = Decimal(delocalize(dataDict["Current Balance ($)"]))
        self.shares = Decimal(delocalize(dataDict["Shares or Units"]))
        self.eDate = effDate  # type: date

    def getPrice(self):
        # type: () -> Decimal
        prc = self.bal / self.shares

        return prc.quantize(self.prec, ROUND_HALF_EVEN)

    def __str__(self):
        # type: () -> str
        return "[{:9} {:>10} as of {}]".format(
            self.ticker, self.getPrice(), self.eDate)

# end class NbHolding
