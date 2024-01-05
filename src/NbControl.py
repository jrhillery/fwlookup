# Use Selenium web driver to launch and control a browser session
import logging
from datetime import date, datetime
from httplib import HTTPConnection
from types import TracebackType

from java.lang import System
from java.time import Duration
from org.openqa.selenium import By, WebDriverException, WebElement
from org.openqa.selenium.chrome import ChromeDriver, ChromeOptions
from org.openqa.selenium.support.ui import ExpectedConditions, WebDriverWait
from typing import Iterator, List, Optional

from NbHolding import NbHolding
from WindowInterface import WindowInterface


class NbControl(object):
    """Controls browsing NetBenefits web pages"""
    CHROME_USER_DATA = "user-data-dir=C:/Users/John/.local/Chrome/User Data"
    CHROME_DEBUGGER_ADDRESS = "localhost:14001"
    NB_LOG_IN = "https://nb.fidelity.com/public/nb/default/home"

    def __init__(self, winCtl):
        # type: (WindowInterface) -> None
        self.webDriver = None  # type: Optional[ChromeDriver]
        self.winCtl = winCtl  # type: WindowInterface
    # end __init__(WindowInterface)

    def getHoldingsDriver(self):
        # type: () -> Optional[ChromeDriver]
        # determine if browser is already started
        conn = None
        try:
            conn = HTTPConnection(self.CHROME_DEBUGGER_ADDRESS)
            conn.connect()
            logging.error("Connecting to existing browser")
            autoStartBrowser = False
        except IOError as e:
            logging.error("Starting new browser (existing: %s)", e)
            autoStartBrowser = True
        finally:
            if conn is not None:
                conn.close()

        # open browser instance
        try:
            crOpts = ChromeOptions()

            if autoStartBrowser:
                crOpts.addArguments(NbControl.CHROME_USER_DATA)
            else:
                crOpts.setExperimentalOption("debuggerAddress", self.CHROME_DEBUGGER_ADDRESS)
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
                "#client-employer a[aria-Label='IBM 401(K) PLAN Summary.']")  # type: By
            link = WebDriverWait(self.webDriver, Duration.ofMinutes(5)) \
                .until(ExpectedConditions.elementToBeClickable(plusPlanLink))
            self.winCtl.showInFront()

            # select 401(k) Plus Plan link
            ifXcptionMsg = "Unable to select 401(k) Plus Plan"
            self.webDriver.executeScript("arguments[0].click();", link)

            # render holdings details
            ifXcptionMsg = "Timed out waiting for holdings page"
            link = WebDriverWait(self.webDriver, Duration.ofSeconds(8)) \
                .until(ExpectedConditions.elementToBeClickable(By.cssSelector(
                    "#holdings-section .show-details-link")))
            self.winCtl.display("FWIMP01: Obtaining price data from {}.".format(
                self.webDriver.getTitle()))
            self.webDriver.executeScript("arguments[0].click();", link)

            return True
        except WebDriverException as e:
            if self.winCtl.isCancelled():
                logging.info("%s - cancelled. %s", ifXcptionMsg, e.toString())

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
            self.webDriver.quit()
            logging.info("%s closed.", self.webDriver.getClass().getSimpleName())

        return None
    # end __exit__(Type[BaseException] | None, BaseException | None, TracebackType | None)

    def reportError(self, txtMsg, xcption):
        # type: (str, WebDriverException) -> None
        self.winCtl.showInFront()
        self.winCtl.display(txtMsg + ":<br/>" + xcption.toString())
        logging.error(txtMsg)
        xcption.printStackTrace(System.err)
    # end reportError(str, WebDriverException)

# end class NbControl
