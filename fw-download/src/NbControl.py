# Use Selenium web driver to launch and control a browser session
import logging
from datetime import date, datetime, timedelta
from http.client import HTTPConnection
from typing import Iterator, List, Optional, Self

from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from NbHolding import NbHolding


class NbControl(object):
    """Controls browsing NetBenefits web pages"""
    CHROME_USER_DATA = "user-data-dir=C:/Users/John/.local/Chrome/User Data"
    CHROME_DEBUGGER_ADDRESS = "localhost:14001"
    NB_LOG_IN = "https://nb.fidelity.com/public/nb/default/home"

    def __init__(self):
        self.webDriver: WebDriver | None = None
    # end __init__()

    def getHoldingsDriver(self) -> WebDriver:
        # determine if browser is already started
        conn = None
        try:
            conn = HTTPConnection(self.CHROME_DEBUGGER_ADDRESS)
            conn.connect()
            logging.error("Connecting to existing browser")
            autoStartBrowser = False
        except IOError as e:
            msg: list[str] = ["Starting new browser"]

            if e.errno != 10061:  # Suppress common case details: Connection refused
                msg.append(" (existing: ")
                msg.append(str(e))
                msg.append(")")
            logging.error("".join(msg))
            autoStartBrowser = True
        finally:
            if conn is not None:
                conn.close()

        # open browser instance
        try:
            crOpts = webdriver.ChromeOptions()

            if autoStartBrowser:
                crOpts.add_argument(NbControl.CHROME_USER_DATA)
            else:
                crOpts.add_experimental_option("debuggerAddress", self.CHROME_DEBUGGER_ADDRESS)
            self.webDriver = webdriver.Chrome(options=crOpts)

            return self.webDriver
        except WebDriverException as e:
            self.reportError("Unable to open browser with " + NbControl.CHROME_USER_DATA, e)
    # end getHoldingsDriver()

    def navigateToHoldingsDetails(self) -> bool:
        ifXcptionMsg = "Unable to open log-in page " + NbControl.NB_LOG_IN
        try:
            # open NetBenefits log-in page
            self.webDriver.get(NbControl.NB_LOG_IN)

            # wait for user to log-in
            ifXcptionMsg = "Timed out waiting for log-in"
            plusPlanLink = By.LINK_TEXT, "IBM 401(K) PLAN"
            link = WebDriverWait(self.webDriver, timeout=timedelta(minutes=5).seconds) \
                .until(expected_conditions.element_to_be_clickable(plusPlanLink))

            # select 401(k) Plus Plan link
            ifXcptionMsg = "Unable to select 401(k) Plus Plan"
            self.webDriver.execute_script("arguments[0].click();", link)

            # render holdings details
            ifXcptionMsg = "Timed out waiting for holdings page"
            link = WebDriverWait(self.webDriver, timeout=8) \
                .until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR,
                    "#holdings-section .show-details-link")))
            logging.info(f"FWIMP01: Obtaining price data from {self.webDriver.title}.")
            self.webDriver.execute_script("arguments[0].click();", link)

            return True
        except WebDriverException as e:
            self.reportError(ifXcptionMsg, e)
    # end navigateToHoldingDetails()

    def getHoldings(self) -> Iterator[NbHolding]:
        """Generate NetBenefits holdings and their current values"""
        ifXcptionMsg = "Unable to find effective date"
        try:
            # lookup effective date
            dateShown = self.webDriver.find_element(By.ID, "modal-header--holdings") \
                .find_element(By.XPATH, "./following-sibling::*").text
            eDate: date = datetime.strptime(dateShown, "Data as of %m/%d/%y").date()

            # lookup data for holdings
            ifXcptionMsg = "Unable to find holdings table"
            hTbl: WebElement = self.webDriver.find_element(By.ID, "holdingsTable")
            tHdrs: List[str] = [hdr.text for hdr in hTbl.find_elements(By.CSS_SELECTOR,
                "thead > tr > th")]
            bodyRows: Iterator[WebElement] = iter(hTbl.find_elements(By.CSS_SELECTOR,
                "tbody > tr"))

            # yield a holding for each pair of rows
            ifXcptionMsg = "Unable to find holdings data"
            nRow: Optional[WebElement] = next(bodyRows, None)
            while nRow:
                hldnName: str = nRow.find_element(By.TAG_NAME, "a").text
                dataDict = {ky: dat.text for ky, dat in
                            zip(tHdrs, next(bodyRows).find_elements(By.TAG_NAME, "td"))}

                yield NbHolding(hldnName, dataDict, eDate)
                nRow = next(bodyRows, None)
            # end while nRow
        except WebDriverException as e:
            self.reportError(ifXcptionMsg, e)
    # end getHoldings()

    def __enter__(self) -> Self:
        return self
    # end __enter__()

    def __exit__(self, exc_type, exc_val, exc_tb) -> Optional[bool]:
        """Release any resources we acquired."""
        if self.webDriver:
            self.webDriver.quit()
            logging.info("%s closed.", self.webDriver.name)

        return None
    # end __exit__(Type[BaseException] | None, BaseException | None, TracebackType | None)

    @staticmethod
    def reportError(txtMsg: str, xcption: WebDriverException) -> None:
        logging.error(f"{txtMsg}:/n{xcption}")
        logging.debug(f"{xcption.__class__.__name__} suppressed:", exc_info=xcption)
    # end reportError(str, WebDriverException)

    def main(self) -> None:
        logging.info("Downloading quote data from NetBenefits.")

        with self.getHoldingsDriver(), self:
            if self.navigateToHoldingsDetails():
                for hldn in self.getHoldings():
                    logging.info(str(hldn))
                # end for each holding
        # end with
    # end main()

# end class NbControl
