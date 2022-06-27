
import logging
from logging.config import dictConfig

from com.infinitekind.moneydance.model import Account, CurrencySnapshot
from com.infinitekind.moneydance.model import CurrencyTable, CurrencyType
from com.moneydance.apps.md.controller import FeatureModuleContext
from java.lang import System
from typing import List


def configLogging():
    dictConfig({
        "version": 1,
        "formatters": {
            "simple": {
                "format": "%(asctime)s.%(msecs)03d %(message)s",
                "datefmt": "%H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": System.err
            }
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console"]
        }
    })
# end configLogging()


configLogging()

if "moneydance" in globals():
    global moneydance  # type: FeatureModuleContext
    accountBook = moneydance.getCurrentAccountBook()
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
