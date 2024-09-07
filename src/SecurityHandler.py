# Persist and apply Moneydance securities price quotes
from decimal import Decimal

from typing import Optional

from com.infinitekind.moneydance.model import CurrencyType
from com.leastlogic.moneydance.util import SnapshotList


class SecurityHandler(object):
    """This object handles deferred updates to a Moneydance security."""

    def __init__(self, snapshotList):
        # type: (SnapshotList) -> None
        self.snapshotList = snapshotList  # type: SnapshotList
        self.security = snapshotList.getSecurity()  # type: CurrencyType
        self.newPrice = None  # type: Optional[float]
        self.newDate = None  # type: Optional[int]
    # end __init__(SnapshotList)

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
        todaysSnapshot = self.snapshotList.getTodaysSnapshot()
        newSnapshot = self.security.setSnapshotInt(self.newDate, 1 / self.newPrice)
        newSnapshot.syncItem()

        if not todaysSnapshot or self.newDate >= todaysSnapshot.getDateInt():
            self.security.setRelativeRate(1 / self.newPrice)
    # end applyUpdate()

    def __str__(self):
        # type: () -> str
        return self.security.getTickerSymbol() + ':' + self.newPrice

# end class SecurityHandler
