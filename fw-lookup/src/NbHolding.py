# Represent Moneydance security holdings details
from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN

from typing import Dict

from Currency import Currency


class NbHolding(object):
    """Houses details for a holding"""

    _PREC2 = Decimal("0.00")
    _PREC6 = Decimal("0.000000")
    _PREC7 = Decimal("0.0000000")
    # noinspection SpellCheckingInspection
    _TICKR = {"HI YLD EMG MKT BOND" : ("NON40OJFI", _PREC6),
              "INFL PROTECTED BOND" : ("NON40OJFB", _PREC7),
              "INTEREST INCOME FUND": ("NON40OJFA", _PREC7),
              "PIM INTL BD US$H I"  : ("PFORX"    , _PREC2),
              "TARGETRETIREMENT2040": ("NON40OJGZ", _PREC7),
              "TOTAL BOND MARKET"   : ("NON40OJFC", _PREC7)}

    def __init__(self, name, dataDict, effDate):
        # type: (str, Dict[str, str], date) -> None
        self.name = name  # type: str
        self.ticker, self.prec = NbHolding._TICKR[name]
        self.bal = Decimal(Currency.delocalize(dataDict["Current Balance ($)"]))
        self.shares = Decimal(Currency.delocalize(dataDict["Shares or Units"]))
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
