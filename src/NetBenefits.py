# get Fidelity NetBenefits current balances
from locale import LC_ALL, setlocale

from java.lang import System

from FwLookupWindow import FwLookupWindow
from NbControl import NbControl
from NbImporter import NbImporter

if __name__ == "__main__":
    # pick up user's default locale
    setlocale(LC_ALL, "")

    if 'moneydance' in globals():
        lookupWin = FwLookupWindow()
        nbCtrl = NbControl(lookupWin)
        lookupWin.visible = True

        if nbCtrl.getHoldingsDriver():
            if nbCtrl.navigateToHoldingsDetails():
                global moneydance
                importer = NbImporter(lookupWin, moneydance.currentAccountBook)
                importer.obtainPrices(nbCtrl.getTitle(), nbCtrl.getHoldings())
                lookupWin.enableCommitButton(importer.isModified())
    else:
        System.err.write("Not started via Moneydance, missing global variable.\n")
