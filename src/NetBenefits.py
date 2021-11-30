# get Fidelity NetBenefits current balances
from locale import LC_ALL, setlocale
from site import getsitepackages, getusersitepackages

from com.moneydance.apps.md.controller import FeatureModule, FeatureModuleContext
from java.lang import System
from typing import Optional

from FwLookupWindow import FwLookupWindow
from NbControl import NbControl
from NbImporter import NbImporter


class NetBenefits(object):
    name = "FW Lookup"

    def __init__(self):
        # type: () -> None
        self.lookupWindow = None  # type: Optional[FwLookupWindow]
        self.fmContext = None  # type: Optional[FeatureModuleContext]
    # end __init__()

    # initialize is called when the extension is loaded and provides the extension's
    # context. The context implements the methods defined in the FeatureModuleContext:
    # http://infinitekind.com/dev/apidoc/com/moneydance/apps/md/controller/FeatureModuleContext.html
    def initialize(self, extension_context, extension_object):
        # type: (FeatureModuleContext, FeatureModule) -> None
        self.fmContext = extension_context
        extension_context.registerFeature(extension_object, "do:fw:lookup",
                                          None, NetBenefits.name)
    # end initialize(FeatureModuleContext, FeatureModule)

    # invoke(uri) is called when we receive a callback for
    # the feature that we registered in the initialize method
    def invoke(self, uri):
        # type: (str) -> None
        System.err.println(NetBenefits.name + " invoked with uri [{}].".format(uri))
        self.showWindow()
        nbCtrl = NbControl(self.lookupWindow)

        if nbCtrl.getHoldingsDriver() \
                and nbCtrl.navigateToHoldingsDetails():
            importer = NbImporter(self.lookupWindow, self.fmContext.getCurrentAccountBook())
            importer.obtainPrices(nbCtrl.getTitle(), nbCtrl.getHoldings())
            self.lookupWindow.enableCommitButton(importer.isModified())
    # end invoke(str)

    def handle_event(self, eventString):
        # type: (str) -> None
        pass

    def unload(self):
        # type: () -> None
        if self.lookupWindow:
            self.lookupWindow.closeWindow()
            self.lookupWindow = None
        self.fmContext = None
    # end unload()

    def __str__(self):
        # type: () -> str
        return NetBenefits.name

    def showWindow(self):
        # type: () -> None
        if self.lookupWindow:
            self.lookupWindow.visible = True
            self.lookupWindow.toFront()
            self.lookupWindow.requestFocus()
        else:
            self.lookupWindow = FwLookupWindow()
            self.lookupWindow.visible = True
    # end showWindow()

# end class NetBenefits


System.err.println("Python site packages = {}; user site packages = {}.".format(
    ", ".join(getsitepackages()), getusersitepackages()))

if "__file__" in globals():
    # running in MoneyBot console
    # pick up user's default locale
    setlocale(LC_ALL, "")

    if "moneydance" in globals():
        global moneydance
        nb = NetBenefits()
        nb.fmContext = moneydance
        nb.invoke("bot:run")
    else:
        System.err.println("Not started via Moneydance, missing global variable.")
else:
    # setting the "moneydance_extension" variable tells
    # Moneydance to register that object as an extension
    moneydance_extension = NetBenefits()
