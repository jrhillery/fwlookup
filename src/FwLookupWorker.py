# properly use the event dispatch thread during lookup
from decimal import Decimal

from com.moneydance.apps.md.controller import FeatureModuleContext
from java.lang import Runnable
from java.text import DecimalFormat
from javax.swing import SwingUtilities, SwingWorker
from typing import List

from FwLookupWindow import FwLookupWindow
from NbControl import NbControl
from NbImporter import NbImporter
from WindowInterface import WindowInterface


class FwLookupWorker(SwingWorker, WindowInterface):

    def __init__(self, lookupWindow, fmContext):
        # type: (FwLookupWindow, FeatureModuleContext) -> None
        super(FwLookupWorker, self).__init__()
        self.lookupWindow = lookupWindow  # type: FwLookupWindow
        self.fmContext = fmContext  # type: FeatureModuleContext
    # end __init__(FwLookupWindow, FeatureModuleContext)

    def getCurrencyFormat(self, amount):
        # type: (Decimal) -> DecimalFormat
        return self.lookupWindow.getCurrencyFormat(amount)
    # end getCurrencyFormat(Decimal)

    def doInBackground(self):  # runs on worker thread
        # type: () -> bool
        """Long running routine to lookup Fidelity workplace account data"""
        nbCtrl = NbControl(self.lookupWindow, self)

        if nbCtrl.getHoldingsDriver() \
                and nbCtrl.navigateToHoldingsDetails():
            importer = NbImporter(self.lookupWindow, self, self.fmContext.getCurrentAccountBook())
            importer.obtainPrices(nbCtrl.getTitle(), nbCtrl.getHoldings())

            # return a boolean to get()
            return importer.isModified()
        else:
            return False
    # end doInBackground()

    def done(self):  # runs on event dispatch thread
        # type: () -> None
        # enable the commit button if we have changes
        self.lookupWindow.enableCommitButton(self.get())
    # end done()

    def display(self, *msgs):  # runs on worker thread
        # type: (*str) -> None
        super(FwLookupWorker, self).publish(msgs)
    # end display(str...)

    def process(self, msgs):  # runs on event dispatch thread
        # type: (List[str]) -> None
        for msg in msgs:
            self.lookupWindow.addText(msg)
    # end process(List[str])

    def showInFront(self):  # runs on worker thread
        # type: () -> None
        SwingUtilities.invokeLater(ShowInFront(self.lookupWindow))
    # end showInFront()

# end class FwLookupWorker


class ShowInFront(Runnable):
    def __init__(self, lookupWindow):
        # type: (FwLookupWindow) -> None
        self.lookupWindow = lookupWindow

    def run(self):  # runs on event dispatch thread
        # type: () -> None
        self.lookupWindow.showInFront()

# end class ShowInFront
