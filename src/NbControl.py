# Use Selenium web driver to launch and control a browser session
from datetime import date, datetime

from java.lang import System
from org.openqa.selenium import By, WebDriverException, WebElement
from org.openqa.selenium.chrome import ChromeDriver, ChromeOptions
from org.openqa.selenium.support.ui import ExpectedConditions, WebDriverWait
from typing import Iterator, List, Optional

from FwLookupWindow import FwLookupWindow
from NbHolding import NbHolding


class NbControl(object):
    """Controls browsing NetBenefits web pages"""
    CHROME_USER_DATA = "user-data-dir=C:/Users/John/AppData/Local/VSCode/Chrome/User Data"
    NB_LOG_IN = "https://nb.fidelity.com/public/nb/default/home"

    def __init__(self, lookupWindow):
        # type: (FwLookupWindow) -> None
        self.webDriver = None  # type: Optional[ChromeDriver]
        lookupWindow.releaseResources = self.releaseResources
        self.lookupWindow = lookupWindow  # type: FwLookupWindow
    # end __init__(FwLookupWindow)

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
            WebDriverWait(self.webDriver, 35) \
                .until(ExpectedConditions.elementToBeClickable(plusPlanLink))
            self.showInFront()

            # select 401(k) Plus Plan link
            ifXcptionMsg = "Unable to select 401(k) Plus Plan"
            link = self.webDriver.findElement(plusPlanLink)
            self.webDriver.executeScript("arguments[0].click();", link)

            # render holdings details
            ifXcptionMsg = "Timed out waiting for holdings page"
            link = WebDriverWait(self.webDriver, 8) \
                .until(ExpectedConditions.elementToBeClickable(By.cssSelector(
                    "#holdings-section .show-details-link")))
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
            hTbl = self.webDriver.findElement(By.id("holdingsTable"))
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

    def getTitle(self):
        # type: () -> str
        return self.webDriver.getTitle()

    def releaseResources(self):
        # type: () -> None
        """Release any resources we acquired."""
        if self.webDriver:
            self.webDriver.quit()
    # end releaseResources()

    def reportError(self, txtMsg, xcption):
        # type: (str, WebDriverException) -> None
        if self.lookupWindow:
            self.lookupWindow.addText(txtMsg + ":<br/>" + xcption.toString())
            self.showInFront()
        xcption.printStackTrace(System.err)
    # end reportError(str, WebDriverException)

    def showInFront(self):
        # type: () -> None
        if self.lookupWindow:
            self.lookupWindow.setAlwaysOnTop(True)
            # self.lookupWindow.toFront()
            # self.lookupWindow.repaint()
            self.lookupWindow.setAlwaysOnTop(False)
    # end showInFront()

# end class NbControl


if __name__ == "__main__":
    lookupWin = FwLookupWindow("NB Control Title")
    nbCtrl = NbControl(lookupWin)
    lookupWin.visible = True

    if nbCtrl.getHoldingsDriver():
        lookupWin.addText("Starting.")

        if nbCtrl.navigateToHoldingsDetails():
            for hldn in nbCtrl.getHoldings():
                lookupWin.addText(hldn.__str__())
