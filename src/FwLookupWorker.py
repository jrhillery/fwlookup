# properly use the event dispatch thread during lookup
from decimal import Decimal

from com.moneydance.apps.md.controller import FeatureModuleContext
from java.lang import Runnable, System, Throwable
from java.text import DecimalFormat
from javax.swing import SwingUtilities, SwingWorker
from typing import List

from FwLookupConsole import FwLookupConsole
from NbControl import NbControl
from NbImporter import NbImporter
from WindowInterface import WindowInterface


class FwLookupWorker(SwingWorker, WindowInterface):

    def __init__(self, lookupConsole, fmContext):
        # type: (FwLookupConsole, FeatureModuleContext) -> None
        super(FwLookupWorker, self).__init__()
        self.lookupConsole = lookupConsole  # type: FwLookupConsole
        self.fmContext = fmContext  # type: FeatureModuleContext
        self.nbCtrl = NbControl(self)
        lookupConsole.closeableResource = self.nbCtrl
    # end __init__(FwLookupConsole, FeatureModuleContext)

    def getCurrencyFormat(self, amount):
        # type: (Decimal) -> DecimalFormat
        return self.lookupConsole.getCurrencyFormat(amount)
    # end getCurrencyFormat(Decimal)

    def handleException(self, e):
        # type: (Throwable) -> None
        self.display(e.toString())
        e.printStackTrace(System.err)
    # end handleException(Throwable)

    def doInBackground(self):  # runs on worker thread
        # type: () -> bool
        """Long-running routine to lookup Fidelity workplace account data"""
        try:
            if self.nbCtrl.getHoldingsDriver() \
                    and self.nbCtrl.navigateToHoldingsDetails():
                importer = NbImporter(self, self.fmContext.getCurrentAccountBook())
                self.lookupConsole.staged = importer
                importer.obtainPrices(self.nbCtrl.getHoldings())

                # return a boolean to get()
                return importer.isModified()
        except Throwable as e:
            self.handleException(e)

        return False
    # end doInBackground()

    def done(self):  # runs on event dispatch thread
        # type: () -> None
        # enable the commit button if we have changes
        self.lookupConsole.enableCommitButton(self.get())
    # end done()

    def display(self, *msgs):  # runs on worker thread
        # type: (*str) -> None
        super(FwLookupWorker, self).publish(msgs)
    # end display(str...)

    def process(self, msgs):  # runs on event dispatch thread
        # type: (List[str]) -> None
        for msg in msgs:
            self.lookupConsole.addText(msg)
    # end process(List[str])

    def showInFront(self):  # runs on worker thread
        # type: () -> None
        SwingUtilities.invokeLater(ShowInFront(self.lookupConsole))
    # end showInFront()

# end class FwLookupWorker


class ShowInFront(Runnable):
    def __init__(self, lookupConsole):
        # type: (FwLookupConsole) -> None
        self.lookupConsole = lookupConsole

    def run(self):  # runs on event dispatch thread
        # type: () -> None
        self.lookupConsole.showInFront()

# end class ShowInFront
