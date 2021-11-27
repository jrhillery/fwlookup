# get Fidelity NetBenefits current balances
from locale import LC_ALL, setlocale

from FwLookupWindow import FwLookupWindow
from NbControl import NbControl

if __name__ == "__main__":
    # pick up user's default locale
    setlocale(LC_ALL, "")

    lookupWin = FwLookupWindow()
    nbCtrl = NbControl(lookupWin)
    lookupWin.visible = True

    if nbCtrl.getHoldingsDriver():
        if 'moneydance' in globals():
            from com.moneydance.apps.md.controller import FeatureModuleContext
            from NbImporter import NbImporter

            if nbCtrl.navigateToHoldingsDetails():
                global moneydance  # type: FeatureModuleContext
                importer = NbImporter(lookupWin, moneydance.currentAccountBook)
                importer.obtainPrices(nbCtrl.getTitle(), nbCtrl.getHoldings())
                lookupWin.enableCommitButton(importer.isModified())
        else:
            lookupWin.addText("Not started via Moneydance, close this window to clean up")
            nbCtrl.showInFront()
