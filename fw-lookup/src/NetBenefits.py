# get Fidelity NetBenefits current balances
import logging
from site import getusersitepackages

from com.moneydance.apps.md.controller import FeatureModule, FeatureModuleContext
from java.lang import AutoCloseable, System, Throwable
from typing import Optional

from Configure import Configure
from FwLookupConsole import FwLookupConsole
from FwLookupWorker import FwLookupWorker


class NetBenefits(AutoCloseable):
    name = "FW Lookup"

    def __init__(self):
        # type: () -> None
        self.lookupConsole = None  # type: Optional[FwLookupConsole]
        self.lookupWorker = None  # type: Optional[FwLookupWorker]
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
        logging.info("%s invoked with uri [%s].", NetBenefits.name, uri)
        try:
            if self.lookupWorker:
                self.lookupWorker.stopExecute()
            self.showWindow()

            # SwingWorker instances are not reusable, so make a new one
            self.lookupWorker = FwLookupWorker(
                self.lookupConsole, NetBenefits.name, self.fmContext)
            self.lookupWorker.execute()
        except Throwable as e:
            self.handleException(e)
    # end invoke(str)

    def handle_event(self, eventString):
        # type: (str) -> None
        pass

    def handleException(self, e):
        # type: (Throwable) -> None
        e.printStackTrace(System.err)
        self.lookupConsole.addText(e.toString())
        self.lookupConsole.enableCommitButton(False)
    # end handleException(Throwable)

    def unload(self):
        # type: () -> None
        if self.lookupConsole:
            self.lookupConsole.goAway()
            self.lookupConsole = None

        if self.lookupWorker:
            self.lookupWorker.stopExecute()
            self.lookupWorker = None
        self.fmContext = None
    # end unload()

    def __str__(self):
        # type: () -> str
        return NetBenefits.name

    def showWindow(self):
        # type: () -> None
        """Show our console window."""
        if self.lookupConsole:
            self.lookupConsole.clearText()
            self.lookupConsole.showInFront()
        else:
            self.lookupConsole = FwLookupConsole(
                NetBenefits.name, self.fmContext.getCurrentAccountBook().getLocalStorage())
            self.lookupConsole.addCloseableResource(self)
    # end showWindow()

    def close(self):
        # type: () -> None
        """Closes this resource, relinquishing any underlying resources."""
        self.lookupConsole = None
        self.lookupWorker = None
    # end close()

# end class NetBenefits


Configure.logToSysErr()
logging.info("Python user site packages = %s.", getusersitepackages())

if "__file__" in globals():
    # running in MoneyBot console or IDE
    nb = NetBenefits()

    if "moneydance" in globals():
        global moneydance
        nb.fmContext = moneydance

    nb.invoke("bot:run")
else:
    # tell Moneydance to register our object as an extension
    moneydance_extension = NetBenefits()
