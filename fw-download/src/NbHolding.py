# Represent Moneydance security holdings details
import locale
from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN


class NbHolding(object):
    """Houses details for a holding"""

    _currencySymbol: str | None = None
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

    @staticmethod
    def currencySymbol() -> str:
        if not NbHolding._currencySymbol:
            NbHolding._currencySymbol = locale.localeconv()["currency_symbol"]

        return NbHolding._currencySymbol
    # end currencySymbol()

    @staticmethod
    def asDecimal(valString: str) -> Decimal:
        stripedVal = locale.delocalize(valString)
        stripedVal = stripedVal.replace(NbHolding.currencySymbol(), "")

        return Decimal(stripedVal)
    # end asDecimal(str)

    def __init__(self, name: str, dataDict: dict[str, str], effDate: date) -> None:
        self.name: str = name
        self.ticker, self.prec = NbHolding._TICKR[name]
        self.bal = self.asDecimal(dataDict["Current Balance ($)"])
        self.shares = self.asDecimal(dataDict["Shares or Units"])
        self.eDate: date = effDate
    # end __init__(str, dict[str, str], date)

    def getPrice(self) -> Decimal:
        prc = self.bal / self.shares

        return prc.quantize(self.prec, ROUND_HALF_EVEN)
    # end getPrice()

    def __str__(self) -> str:
        return f"[{self.ticker:9} {self.getPrice():>10} as of {self.eDate}]"
    # end __str__()

# end class NbHolding
