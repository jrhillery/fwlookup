# Find and save Moneydance securities price quotes
from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN

from com.infinitekind.moneydance.model import Account, AccountBook, CurrencySnapshot
from com.infinitekind.moneydance.model import CurrencyTable, CurrencyType
from com.leastlogic.moneydance.util import SnapshotList, MdUtil
from com.leastlogic.swing.util import HTMLPane
from typing import Dict, Iterable, Set

from Currency import Currency
from NbHolding import NbHolding
from SecurityHandler import SecurityHandler
from StagedInterface import StagedInterface
from WindowInterface import WindowInterface


def getCurrentBalance(account):
    # type: (Account) -> Decimal
    if account.getAccountType() == Account.AccountType.ASSET:
        centBalance = Decimal(account.getRecursiveUserCurrentBalance())
    else:
        centBalance = Decimal(account.getUserCurrentBalance())
    decimalPlaces = account.getCurrencyType().decimalPlaces

    return centBalance.scaleb(-decimalPlaces)
# end getCurrentBalance(Account)


def convRateToPrice(rate, exp):
    # type: (float, Decimal) -> Decimal
    """Return security price rounded to the same place past the decimal point as that of exp"""
    bd = Decimal(1 / rate)

    return bd.quantize(exp, ROUND_HALF_EVEN)
# end convRateToPrice(float, Decimal)


class NbImporter(StagedInterface):
    NB_ACCOUNT_NAME = "IBM 401k"

    def __init__(self, winCtl, accountBook):
        # type: (WindowInterface, AccountBook) -> None
        self.priceChanges = {}  # type: Dict[CurrencyType, SecurityHandler]
        self.numPricesSet = 0  # type: int
        self.winCtl = winCtl  # type: WindowInterface
        self.root = accountBook.getRootAccount()  # type: Account
        self.securities = accountBook.getCurrencies()  # type: CurrencyTable
    # end __init__(WindowInterface, AccountBook)

    def commitChanges(self):
        # type: () -> str
        for sHandler in self.priceChanges.values():
            sHandler.applyUpdate()

        numPricesSet = self.numPricesSet
        self.forgetChanges()

        return "FWIMP07: Changed {} security price{}.".format(
            numPricesSet, "" if numPricesSet == 1 else "s")
    # end commitChanges()

    def isModified(self):
        # type: () -> bool
        return bool(self.priceChanges)
    # end isModified()

    def verifyAccountBalance(self, account, holding):
        # type: (Account, NbHolding) -> None
        if account:
            balance = getCurrentBalance(account)  # type: Decimal

            if holding.bal != balance:
                self.winCtl.display(
                    "FWIMP02: Found a different balance in account {}: have {}, found {}. "
                    "Note: No Moneydance security {} for ticker symbol ({}).".format(
                        account.getAccountName(), Currency.format(balance, holding.bal),
                        Currency.format(holding.bal), holding.name, holding.ticker))
    # end verifyAccountBalance(Account, NbHolding)

    def addHandler(self, handler):
        # type: (SecurityHandler) -> None
        self.priceChanges[handler.security] = handler

    def storePriceQuoteIfDiff(self, security, holding):
        # type: (CurrencyType, NbHolding) -> None
        price = holding.getPrice()  # type: Decimal
        effectiveDate = holding.eDate.year * 10000 + holding.eDate.month * 100 + holding.eDate.day
        ssList = SnapshotList(security)
        snapshot = ssList.getSnapshotForDate(effectiveDate)  # type: CurrencySnapshot
        oldPrice = convRateToPrice(snapshot.getRate(), price) if snapshot else Decimal("1")

        # store this quote if it differs, and we don't already have this security
        if (not snapshot or effectiveDate != snapshot.getDateInt()
                or price != oldPrice) and security not in self.priceChanges:
            self.winCtl.display(
                "FWIMP03: Change {} ({}) price from {} to {} "
                "(<span class=\"{}\">{:+.2f}%</span>).".format(
                    security.getName(), holding.ticker,
                    Currency.format(oldPrice, price), Currency.format(price),
                    HTMLPane.getSpanCl(price, oldPrice),
                    (price / oldPrice - 1).scaleb(2)))

            self.addHandler(SecurityHandler(security, ssList.getLatestSnapshot())
                            .storeNewPrice(price, effectiveDate))
            self.numPricesSet += 1
    # end storePriceQuoteIfDiff(CurrencyType, NbHolding)

    def verifyShareBalance(self, account, security, foundShares):
        # type: (Account, CurrencyType, Decimal) -> None
        if account:
            secAccount = MdUtil.getSubAccountByName(account, security.getName())

            if not secAccount:
                self.winCtl.display(
                    "FWIMP06: Unable to obtain Moneydance security "
                    "[{} ({})] in account {}.".format(
                        security.getName(), security.getTickerSymbol(),
                        account.getAccountName()))
            else:
                balance = getCurrentBalance(secAccount)  # type: Decimal

                if foundShares != balance:
                    self.winCtl.display(
                        "FWIMP04: Found a different {} ({}) share balance "
                        "in account {}: have {}, found {}.".format(
                            secAccount.accountName, security.getTickerSymbol(),
                            account.getAccountName(), balance, foundShares))
    # end verifyShareBalance(Account, CurrencyType, Decimal)

    def forgetChanges(self):
        # type: () -> None
        self.priceChanges.clear()
        self.numPricesSet = 0
    # end forgetChanges()

    def obtainPrices(self, holdingsIter):
        # type: (Iterable[NbHolding]) -> None
        """Obtain price data from NetBenefits"""
        account = self.root.getAccountByName(NbImporter.NB_ACCOUNT_NAME)  # type: Account

        if not account:
            self.winCtl.display("FWIMP05: Unable to obtain Moneydance investment account named {}.".format(
                NbImporter.NB_ACCOUNT_NAME))
        dates = set()  # type: Set[date]

        for hldn in holdingsIter:  # type: NbHolding
            security = self.securities.getCurrencyByTickerSymbol(hldn.ticker)  # type: CurrencyType

            if security:
                self.storePriceQuoteIfDiff(security, hldn)
                self.verifyShareBalance(account, security, hldn.shares)
            else:
                self.verifyAccountBalance(account, hldn)
            dates.add(hldn.eDate)
        # end for
        self.winCtl.display("FWIMP09: Found effective date{} {}.".format(
            "" if len(dates) == 1 else "s",
            ", ".join(dt.strftime("%a %b %d, %Y") for dt in dates)))

        if not self.isModified():
            self.winCtl.display("FWIMP08: No new price data found.")
    # end obtainPrices(Iterable[NbHolding])

# end class NbImporter
