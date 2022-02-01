# Use Selenium web driver to launch and control a browser session
from datetime import date, datetime
from decimal import Decimal

from java.lang import AutoCloseable, System
from java.text import DecimalFormat
from org.openqa.selenium import By, WebDriverException, WebElement
from org.openqa.selenium.chrome import ChromeDriver, ChromeOptions
from org.openqa.selenium.support.ui import ExpectedConditions, WebDriverWait
from typing import Iterator, List, Optional

from FwLookupWindow import FwLookupWindow
from NbHolding import NbHolding
from WindowInterface import WindowInterface


class NbControl(AutoCloseable):
    """Controls browsing NetBenefits web pages"""
    CHROME_USER_DATA = "user-data-dir=C:/Users/John/AppData/Local/VSCode/Chrome/User Data"
    NB_LOG_IN = "https://nb.fidelity.com/public/nb/default/home"
    # CALCULATOR_PAGE = "http://www.calculator.net"  # By.linkText("Math Calculators")

    def __init__(self, winCtl):
        # type: (WindowInterface) -> None
        self.webDriver = None  # type: Optional[ChromeDriver]
        self.winCtl = winCtl  # type: WindowInterface
        winCtl.registerClosableResource(self)
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

            # wait for user to log-in
            ifXcptionMsg = "Timed out waiting for log-in"
            plusPlanLink = By.cssSelector(
                "#client-employer a[aria-Label='IBM 401(K) PLUS PLAN Summary.']")  # type: By
            link = WebDriverWait(self.webDriver, 35) \
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

    def close(self):
        # type: () -> None
        """Release any resources we acquired."""
        if self.webDriver:
            self.webDriver.quit()
    # end close()

    def reportError(self, txtMsg, xcption):
        # type: (str, WebDriverException) -> None
        self.winCtl.showInFront()
        self.winCtl.display(txtMsg + ":<br/>" + xcption.toString())
        xcption.printStackTrace(System.err)
    # end reportError(str, WebDriverException)

# end class NbControl


if __name__ == "__main__":
    class TestWindow(WindowInterface):
        def __init__(self):
            # type: () -> None
            self.lookupWin = FwLookupWindow("NB Control Title")

        def registerClosableResource(self, closable):
            # type: (AutoCloseable) -> None
            self.lookupWin.closeableResource = closable

        def getCurrencyFormat(self, amount):
            # type: (Decimal) -> DecimalFormat
            return self.lookupWin.getCurrencyFormat(amount)

        def display(self, *msgs):
            # type: (*str) -> None
            for msg in msgs:
                self.lookupWin.addText(msg)

        def showInFront(self):
            # type: () -> None
            self.lookupWin.showInFront()
    # end class TestWindow

    win = TestWindow()
    nbCtrl = NbControl(win)

    if nbCtrl.getHoldingsDriver():
        win.display("Starting.")

        if nbCtrl.navigateToHoldingsDetails():
            for hldn in nbCtrl.getHoldings():
                win.display(hldn.__str__())
