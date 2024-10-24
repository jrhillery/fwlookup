# Use Selenium web driver to launch and control a browser session
import logging
from contextlib import AbstractContextManager
from datetime import date, datetime, timedelta
from http.client import HTTPConnection
from pathlib import Path
from typing import Iterator

from selenium import webdriver
from selenium.common import NoSuchWindowException, WebDriverException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import (
    any_of, element_to_be_clickable, visibility_of_element_located)
from selenium.webdriver.support.wait import WebDriverWait

from NbHolding import NbHolding


class NbException(Exception):
    """Class for handled exceptions"""

    @classmethod
    def fromXcp(cls, unableMsg: str, xcption: WebDriverException):
        """Factory method for WebDriverExceptions"""
        return cls(f"Unable to {unableMsg}, {xcption.__class__.__name__}: {xcption.msg}")
    # end fromXcp(str, WebDriverException)

# end class NbException


class NbControl(AbstractContextManager["NbControl"]):
    """Controls browsing NetBenefits web pages"""
    CHROME_USER_DATA = f"user-data-dir={Path.home().joinpath(".local", "Chrome", "User Data")}"
    CHROME_DEBUGGER_ADDRESS = "localhost:14001"
    NB_LOG_IN = "https://nb.fidelity.com/public/nb/default/home"
    PLUS_PLAN_LINK = By.LINK_TEXT, "IBM 401(K) PLAN"
    DETAILS_LINK = By.CSS_SELECTOR, "#holdings-section .show-details-link"
    HOLDINGS_HEADER_LOCATOR = By.ID, "modal-header--holdings"
    FOLLOWING_SIBLING_LOCATOR = By.XPATH, "./following-sibling::*"
    HOLDINGS_TABLE_LOCATOR = By.ID, "holdingsTable"
    FIDELITY_LOGOUT_LOCATOR = By.CSS_SELECTOR, "h1#content-body-top-heading-tcm\\:526-223203"
    NETBENEFITS_LOGOUT_LOCATOR = By.CSS_SELECTOR, "h1#dom-login-header"

    def __init__(self):
        self.autoStartBrowser = False
        self.webDriver: WebDriver | None = None
        self.loginWait: WebDriverWait | None = None
        self.pageDrawWait: WebDriverWait | None = None
        self.logoutWait: WebDriverWait | None = None
        self.loggedIn = False
        self.planId: str | None = None
        self.effectiveDate: date = date.today()
    # end __init__()

    def getHoldingsDriver(self) -> WebDriver:
        # determine if browser is already started
        conn = None
        try:
            conn = HTTPConnection(self.CHROME_DEBUGGER_ADDRESS)
            conn.connect()
            logging.info("Connecting to existing browser.")
        except IOError as e:
            msg: list[str] = ["Starting new browser"]

            if e.errno != 10061:  # Suppress common case details: Connection refused
                msg.append(f" (existing: {str(e)})")
            msg.append(".")
            logging.info("".join(msg))
            self.autoStartBrowser = True
        finally:
            if conn is not None:
                conn.close()

        # open browser instance
        try:
            crOpts = webdriver.ChromeOptions()

            if self.autoStartBrowser:
                crOpts.add_argument(NbControl.CHROME_USER_DATA)
                crOpts.add_experimental_option("excludeSwitches", ["enable-logging"])
            else:
                crOpts.add_experimental_option("debuggerAddress", self.CHROME_DEBUGGER_ADDRESS)
            self.webDriver = webdriver.Chrome(options=crOpts)
            self.loginWait = WebDriverWait(self.webDriver, timedelta(minutes=5).seconds)
            self.pageDrawWait = WebDriverWait(self.webDriver, 8)
            self.logoutWait = WebDriverWait(self.webDriver, timedelta(minutes=30).seconds)

            return self.webDriver
        except WebDriverException as e:
            raise NbException.fromXcp("open browser with " + NbControl.CHROME_USER_DATA, e) from e
    # end getHoldingsDriver()

    def navigateToHoldingsDetails(self) -> bool:
        ifXcptionMsg = "open log-in page " + NbControl.NB_LOG_IN
        try:
            # open NetBenefits log-in page
            self.webDriver.get(NbControl.NB_LOG_IN)

            # wait for user to log-in
            ifXcptionMsg = "log-in"
            link = self.loginWait.until(element_to_be_clickable(NbControl.PLUS_PLAN_LINK),
                                        "Timed out waiting to log-in")
            self.loggedIn = True

            ifXcptionMsg = "select 401(k) Plus Plan link"
            self.webDriver.execute_script("arguments[0].click();", link)

            ifXcptionMsg = "render holdings details"
            link = self.pageDrawWait.until(element_to_be_clickable(NbControl.DETAILS_LINK),
                                           "Timed out waiting for holdings page")
            logging.info(f"Obtaining price data from {self.webDriver.title}.")
            self.webDriver.execute_script("arguments[0].click();", link)

            # lookup plan identifier
            self.planId = self.webDriver.execute_script("return planId")

            ifXcptionMsg = "find effective date"
            dateShown = self.webDriver.find_element(*NbControl.HOLDINGS_HEADER_LOCATOR) \
                .find_element(*NbControl.FOLLOWING_SIBLING_LOCATOR).text
            self.effectiveDate = datetime.strptime(dateShown, "Data as of %m/%d/%y").date()

            return True
        except NoSuchWindowException:
            logging.info(f"Browser gone ({ifXcptionMsg})")

            return False
        except WebDriverException as e:
            raise NbException.fromXcp(ifXcptionMsg, e) from e
    # end navigateToHoldingDetails()

    def getHoldings(self) -> Iterator[NbHolding]:
        """Generate NetBenefits holdings and their current values"""
        ifXcptionMsg = "find holdings table"
        try:
            # lookup data for holdings
            hTbl: WebElement = self.webDriver.find_element(*NbControl.HOLDINGS_TABLE_LOCATOR)
            tHdrs: list[str] = [hdr.text for hdr in
                hTbl.find_elements(By.CSS_SELECTOR, "thead > tr > th")]
            bodyRows: Iterator[WebElement] = iter(
                hTbl.find_elements(By.CSS_SELECTOR, "tbody > tr"))

            # yield a holding for each pair of rows
            ifXcptionMsg = "find holdings data"
            nRow: WebElement | None = next(bodyRows, None)
            while nRow:
                hldnName: str = nRow.find_element(By.TAG_NAME, "a").text
                dataDict = {ky: dat.text for ky, dat in
                    zip(tHdrs, next(bodyRows).find_elements(By.TAG_NAME, "td"))}

                yield NbHolding(hldnName, dataDict, self.effectiveDate)
                nRow = next(bodyRows, None)
            # end while nRow
        except WebDriverException as e:
            raise NbException.fromXcp(ifXcptionMsg, e) from e
    # end getHoldings()

    def waitForLogout(self) -> None:
        doingMsg = "waiting for log-out"
        try:
            # wait for user to log-out
            logging.info(doingMsg.capitalize() + ".")
            self.logoutWait.until(any_of(
                visibility_of_element_located(NbControl.FIDELITY_LOGOUT_LOCATOR),
                visibility_of_element_located(NbControl.NETBENEFITS_LOGOUT_LOCATOR)),
                "Timed out waiting for log-out")
        except WebDriverException as e:
            raise NbException.fromXcp(doingMsg, e) from e

    # end waitForLogout()

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """Release any resources we acquired."""
        if self.webDriver:
            self.webDriver.quit()
            logging.info("%s WebDriver closed.", self.webDriver.name)

        return None
    # end __exit__(Type[BaseException] | None, BaseException | None, TracebackType | None)

# end class NbControl
