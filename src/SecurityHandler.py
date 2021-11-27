# Persist and apply Moneydance securities price quotes
from decimal import Decimal

from com.infinitekind.moneydance.model import CurrencySnapshot, CurrencyType
from typing import Optional


class SecurityHandler(object):
    """This object handles deferred updates to a Moneydance security."""

    def __init__(self, security, latestSnapshot):
        # type: (CurrencyType, CurrencySnapshot) -> None
        self.security = security  # type: CurrencyType
        self.latestSnapshot = latestSnapshot  # type: CurrencySnapshot
        self.newPrice = None  # type: Optional[float]
        self.newDate = None  # type: Optional[int]
    # end __init__(CurrencyType, CurrencySnapshot)

    def storeNewPrice(self, newPrice, newDate):
        # type: (Decimal, int) -> SecurityHandler
        """Store a deferred price quote for a specified date integer."""
        self.newPrice = float(newPrice)
        self.newDate = newDate

        return self
    # end storeNewPrice(Decimal, int)

    def applyUpdate(self):
        # type: () -> None
        """Apply the stored update."""
        newSnapshot = self.security.setSnapshotInt(self.newDate, 1 / self.newPrice)
        newSnapshot.syncItem()

        if not self.latestSnapshot or self.newDate >= self.latestSnapshot.getDateInt():
            self.security.setRelativeRate(1 / self.newPrice)
    # end applyUpdate()

    def __str__(self):
        # type: () -> str
        return self.security.getTickerSymbol() + ':' + self.newPrice

# end class SecurityHandler
