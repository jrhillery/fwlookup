
import logging

from com.infinitekind.moneydance.model import Account, AccountBook, CurrencySnapshot
from com.infinitekind.moneydance.model import CurrencyTable, CurrencyType
from typing import List

from Configure import Configure


Configure.logToSysErr()

if "moneydance" in globals():
    global moneydance
    accountBook = moneydance.getCurrentAccountBook()  # type: AccountBook
    root = accountBook.getRootAccount()  # type: Account
    securities = accountBook.getCurrencies()  # type: CurrencyTable
    sourceSecurity = securities.getCurrencyByTickerSymbol("FSPSX")  # type: CurrencyType
    destSecurity = securities.getCurrencyByTickerSymbol("FSIVX")  # type: CurrencyType
    logging.info("Copying price snapshots to %s (%s)",
                 destSecurity.getName(), destSecurity.getTickerSymbol())
    sourceSnapshots = sourceSecurity.getSnapshots()  # type: List[CurrencySnapshot]
    ssRate = 1.0

    for sourceSnapshot in sourceSnapshots:
        ssDateInt = sourceSnapshot.getDateInt()  # type: int
        ssRate = sourceSnapshot.getRate()
        logging.info("On %i %s (%s) closed at $%0.8f", ssDateInt,
                     sourceSecurity.getName(), sourceSecurity.getTickerSymbol(),
                     1 / ssRate)

        newSnapshot = destSecurity.setSnapshotInt(ssDateInt, ssRate)
        newSnapshot.syncItem()
    # end for

    if sourceSnapshots:
        destSecurity.setRelativeRate(ssRate)
        logging.info("Finished updating %s (%s)",
                     destSecurity.getName(), destSecurity.getTickerSymbol())
