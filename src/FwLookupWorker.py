# properly use the event dispatch thread during lookup
import logging
from threading import Event

from com.moneydance.apps.md.controller import FeatureModuleContext
from java.lang import AutoCloseable, InterruptedException, Runnable, System, Throwable
from java.util.concurrent import CancellationException, ExecutionException
from javax.swing import SwingUtilities, SwingWorker
from javax.swing.SwingWorker.StateValue import DONE
from typing import List

from FwLookupConsole import FwLookupConsole
from NbControl import NbControl
from NbImporter import NbImporter
from WindowInterface import WindowInterface


class FwLookupWorker(SwingWorker, WindowInterface, AutoCloseable):

    def __init__(self, lookupConsole, extensionName, fmContext):
        # type: (FwLookupConsole, str, FeatureModuleContext) -> None
        super(FwLookupWorker, self).__init__()
        self.lookupConsole = lookupConsole  # type: FwLookupConsole
        self.extensionName = extensionName  # type: str
        self.fmContext = fmContext  # type: FeatureModuleContext
        self.nbCtrl = NbControl(self)
        self.finishedLatch = Event()
        lookupConsole.addCloseableResource(self)
    # end __init__(FwLookupConsole, str, FeatureModuleContext)

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
                if self.fmContext:
                    importer = NbImporter(self, self.fmContext.getCurrentAccountBook())
                    self.lookupConsole.staged = importer
                    importer.obtainPrices(self.nbCtrl.getHoldings())

                    # return a boolean to get()
                    return importer.isModified()
                else:
                    # Running test w/o Moneydance
                    for hldn in self.nbCtrl.getHoldings():
                        self.display(hldn.__str__())

                    return True
        except Throwable as e:
            self.handleException(e)
        finally:
            self.finishedLatch.set()

        return False
    # end doInBackground()

    def done(self):  # runs on event dispatch thread after doInBackground finishes
        # type: () -> None
        """Enable the commit button if we have changes"""
        try:
            # enable the commit button if we have changes
            self.lookupConsole.enableCommitButton(self.get())
        except CancellationException:
            pass  # ignore
        except Throwable as e:
            self.lookupConsole.addText(e.toString())
            e.printStackTrace(System.err)
    # end done()

    def display(self, *msgs):  # runs on worker thread
        # type: (*str) -> None
        # without super(), I get: AttributeError: 'FwLookupWorker' object has no attribute 'publish'
        super(FwLookupWorker, self).publish(msgs)
    # end display(str...)

    def process(self, msgs):  # runs on event dispatch thread
        # type: (List[str]) -> None
        if not self.isCancelled():
            for msg in msgs:
                self.lookupConsole.addText(msg)
    # end process(List[str])

    def showInFront(self):  # runs on worker thread
        # type: () -> None
        SwingUtilities.invokeLater(ShowInFront(self.lookupConsole))
    # end showInFront()

    def stopExecute(self):
        # type: () -> None
        """Stop a running execution"""
        self.close()

        # we no longer need closing
        self.lookupConsole.removeCloseableResource(self)
    # end stopExecute()

    def close(self):
        # type: () -> None
        """Cancel this worker, wait for it to complete, discard its results and close nbCtrl"""
        with self.nbCtrl:  # make sure we close nbCtrl
            if self.getState() != DONE:
                logging.info("Cancelling running %s invocation.", self.extensionName)
                self.cancel(True)

                # wait for worker to complete
                self.finishedLatch.wait()

                # discard results and some exceptions
                try:
                    self.get()
                except (CancellationException, InterruptedException, ExecutionException):
                    pass  # ignore
        # end with w/context
    # end close()

# end class FwLookupWorker


class ShowInFront(Runnable):
    def __init__(self, lookupConsole):
        # type: (FwLookupConsole) -> None
        self.lookupConsole = lookupConsole

    def run(self):  # runs on event dispatch thread
        # type: () -> None
        self.lookupConsole.showInFront()

# end class ShowInFront
