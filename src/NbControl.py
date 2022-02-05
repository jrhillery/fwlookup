# Use Selenium web driver to launch and control a browser session
from datetime import date, datetime
from decimal import Decimal
from types import TracebackType

from java.lang import AutoCloseable, System
from java.text import DecimalFormat
from org.openqa.selenium import By, WebDriverException, WebElement
from org.openqa.selenium.chrome import ChromeDriver, ChromeOptions
from org.openqa.selenium.support.ui import ExpectedConditions, WebDriverWait
from typing import Iterator, List, Optional

from FwLookupConsole import FwLookupConsole
from NbHolding import NbHolding
from WindowInterface import WindowInterface


class NbControl(object):
    """Controls browsing NetBenefits web pages"""
    CHROME_USER_DATA = "user-data-dir=C:/Users/John/AppData/Local/VSCode/Chrome/User Data"
    NB_LOG_IN = "https://nb.fidelity.com/public/nb/default/home"
    # CALCULATOR_PAGE = "http://www.calculator.net"  # By.linkText("Math Calculators")

    def __init__(self, winCtl):
        # type: (WindowInterface) -> None
        self.webDriver = None  # type: Optional[ChromeDriver]
        self.winCtl = winCtl  # type: WindowInterface
    # end __init__(WindowInterface)

    def getHoldingsDriver(self):
        # type: () -> Optional[ChromeDriver]
        # open browser instance
        try:
            crOpts = ChromeOptions()
            crOpts.addArguments(NbControl.CHROME_USER_DATA)
            self.webDriver = ChromeDriver(crOpts)

            return self.webDriver
        except WebDriverException as e:
            self.reportError("Unable to open browser with " + NbControl.CHROME_USER_DATA, e)
    # end getHoldingsDriver()

    def navigateToHoldingsDetails(self):
        # type: () -> bool
        ifXcptionMsg = "Unable to open log-in page " + NbControl.NB_LOG_IN  # type: str
        try:
            # open NetBenefits log-in page
            self.webDriver.get(NbControl.NB_LOG_IN)

            if self.winCtl.isCancelled():
                raise WebDriverException("after get()")

            # wait for user to log-in
            ifXcptionMsg = "Timed out waiting for log-in"
            plusPlanLink = By.cssSelector(
                "#client-employer a[aria-Label='IBM 401(K) PLUS PLAN Summary.']")  # type: By
            link = WebDriverWait(self.webDriver, 55) \
                .until(ExpectedConditions.elementToBeClickable(plusPlanLink))
            self.winCtl.showInFront()

            # select 401(k) Plus Plan link
            ifXcptionMsg = "Unable to select 401(k) Plus Plan"
            self.webDriver.executeScript("arguments[0].click();", link)

            # render holdings details
            ifXcptionMsg = "Timed out waiting for holdings page"
            link = WebDriverWait(self.webDriver, 8) \
                .until(ExpectedConditions.elementToBeClickable(By.cssSelector(
                    "#holdings-section .show-details-link")))
            self.winCtl.display("FWIMP01: Obtaining price data from {}.".format(
                self.webDriver.getTitle()))
            self.webDriver.executeScript("arguments[0].click();", link)

            return True
        except WebDriverException as e:
            if self.winCtl.isCancelled():
                System.err.println("{} - cancelled. {}".format(ifXcptionMsg, e.toString()))

                return False
            else:
                self.reportError(ifXcptionMsg, e)
    # end navigateToHoldingDetails()

    def getHoldings(self):
        # type: () -> Iterator[NbHolding]
        """Generate NetBenefits holdings and their current values"""
        ifXcptionMsg = "Unable to find effective date"
        try:
            # lookup effective date
            dateShown = self.webDriver.findElement(By.id("modal-header--holdings")) \
                .findElement(By.xpath("./following-sibling::*")).text
            eDate = datetime.strptime(dateShown, "Data as of %m/%d/%y").date()  # type: date

            # lookup data for holdings
            ifXcptionMsg = "Unable to find holdings table"
            hTbl = self.webDriver.findElement(By.id("holdingsTable"))  # type: WebElement
            tHdrs = [hdr.text for hdr in hTbl.findElements(By.cssSelector(
                "thead > tr > th"))]  # type: List[str]
            bodyRows = iter(hTbl.findElements(By.cssSelector(
                "tbody > tr")))  # type: Iterator[WebElement]

            # yield a holding for each pair of rows
            ifXcptionMsg = "Unable to find holdings data"
            nRow = next(bodyRows, None)  # type: Optional[WebElement]
            while nRow:
                hldnName = nRow.findElement(By.tagName("a")).text  # type: str
                dataDict = {ky: dat.text for ky, dat in
                            zip(tHdrs, next(bodyRows).findElements(By.tagName("td")))}

                yield NbHolding(hldnName, dataDict, eDate)
                nRow = next(bodyRows, None)
            # end while nRow
        except WebDriverException as e:
            self.reportError(ifXcptionMsg, e)
    # end getHoldings()

    def __enter__(self):
        # type: () -> NbControl
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # type: (Optional[type(BaseException)], Optional[BaseException], Optional[TracebackType]) -> Optional[bool]
        """Release any resources we acquired."""
        if self.webDriver:
            System.err.println("Quitting web driver {}.".format(
                self.webDriver.getWindowHandle()))
            self.webDriver.quit()

        return None
    # end __exit__(Type[BaseException] | None, BaseException | None, TracebackType | None)

    def reportError(self, txtMsg, xcption):
        # type: (str, WebDriverException) -> None
        self.winCtl.showInFront()
        self.winCtl.display(txtMsg + ":<br/>" + xcption.toString())
        xcption.printStackTrace(System.err)
    # end reportError(str, WebDriverException)

# end class NbControl


if __name__ == "__main__":
    class TestConsole(WindowInterface, AutoCloseable):
        def __init__(self):
            self.nbCtrl = None  # type: Optional[NbControl]
            self.lookupConsole = FwLookupConsole("NB Control Title")
            self.lookupConsole.closeableResource = self

        def getCurrencyFormat(self, amount):
            # type: (Decimal) -> DecimalFormat
            return self.lookupConsole.getCurrencyFormat(amount)

        def display(self, *msgs):
            # type: (*str) -> None
            for msg in msgs:
                self.lookupConsole.addText(msg)

        def showInFront(self):
            self.lookupConsole.showInFront()

        def close(self):
            with self.nbCtrl:  # make sure we close nbCtrl
                pass

        def isCancelled(self):
            return False
    # end class TestConsole

    win = TestConsole()
    win.nbCtrl = NbControl(win)

    if win.nbCtrl.getHoldingsDriver():
        win.display("Starting.")

        if win.nbCtrl.navigateToHoldingsDetails():
            for hldn in win.nbCtrl.getHoldings():
                win.display(hldn.__str__())
