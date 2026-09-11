# Use Selenium web driver to launch and control a browser session
from pathlib import Path

import logging
import re
from contextlib import AbstractContextManager
from datetime import date, datetime, timedelta
from http.client import HTTPConnection
from selenium import webdriver
from selenium.common import NoSuchWindowException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import (
    any_of, element_to_be_clickable, presence_of_element_located, visibility_of_element_located)
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from typing import Iterator

from NbHolding import NbHolding


class NbException(Exception):
    """Class for handled exceptions"""

    @classmethod
    def fromXcp(cls, unableMsg: str, xcption: Exception):
        """Factory method with special logic for WebDriverExceptions"""
        msg = xcption.msg if isinstance(xcption, WebDriverException) else str(xcption)

        return cls(f"Unable to {unableMsg}, {xcption.__class__.__name__}: {msg}")
    # end fromXcp(str, Exception)

# end class NbException


class NbControl(AbstractContextManager["NbControl"]):
    """Controls browsing NetBenefits web pages"""
    CHROME_USER_DATA = f"user-data-dir={Path.home().joinpath(".local", "Chrome", "User Data")}"
    CHROME_DEBUGGER_ADDRESS = "localhost:14001"
    NB_LOG_IN = "https://nb.fidelity.com/public/nb/default/home"
    PLUS_PLAN_LINK = By.LINK_TEXT, "IBM 401(K) PLAN"
    SUBHEADING_LOCATOR = By.ID, "page_subheading"
    HOLDINGS_LINK = By.ID, "investments-holdings"
    DETAILS_LINK = By.ID, "investments-holdings-details-launcher-btn"
    SELECT_LOCATOR = By.CSS_SELECTOR, "select[aria-label=\"Select the investment data you'd like to see:\"]"
    AS_OF_DATE_LOCATOR = By.ID, "investments-holdings-details-modal-asofdate"
    HOLDINGS_TABLE_LOCATOR = By.ID, "holdings-modal-table-container"
    FIDELITY_LOGOUT_LOCATOR = By.CSS_SELECTOR, "h1#content-body-top-heading-tcm\\:526-223203"
    NETBENEFITS_LOGOUT_LOCATOR = By.CSS_SELECTOR, "h1#dom-login-header"

    def __init__(self):
        self.autoStartBrowser = False
        self.webDriver = self.getHoldingsDriver()
        self.loginWait = WebDriverWait(self.webDriver, timedelta(minutes=5).seconds)
        self.pageDrawWait = WebDriverWait(self.webDriver, 12)
        self.logoutWait = WebDriverWait(self.webDriver, timedelta(minutes=45).seconds)
        self.loggedIn = False
        self.planId = "unknown"
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

            return webdriver.Chrome(options=crOpts)
        except WebDriverException as e:
            raise NbException.fromXcp("open browser with " + NbControl.CHROME_USER_DATA, e) from e
    # end getHoldingsDriver()

    def robustLogin(self) -> WebElement:
        while True:
            try:
                return self.loginWait.until(element_to_be_clickable(NbControl.PLUS_PLAN_LINK),
                                            "Timed out waiting to log-in")
            except StaleElementReferenceException as e:
                logging.info(f"Retrying log-in due to {e.__class__.__name__}.")
        # end while trying to log-in
    # end robustLogin()

    def navigateToHoldingsDetails(self) -> bool:
        ifXcptionMsg = "open log-in page " + NbControl.NB_LOG_IN
        try:
            # wait for browser to open
            self.pageDrawWait.until(lambda d: d.current_url is not None,
                                    "Timed out waiting for browser to open")

            # open NetBenefits log-in page
            self.webDriver.get(NbControl.NB_LOG_IN)

            # wait for user to log-in
            ifXcptionMsg = "log-in"
            link = self.robustLogin()
            self.loggedIn = True

            ifXcptionMsg = "select 401(k) Plus Plan link"
            self.webDriver.execute_script("arguments[0].click();", link)

            ifXcptionMsg = "reading plan id"
            subhead = self.pageDrawWait.until(visibility_of_element_located(NbControl.SUBHEADING_LOCATOR),
                                              "Timed out waiting to read plan id").text
            logging.info(f"Obtaining price data from {self.webDriver.title}.")
            if subhead and (match := re.search(r"\((\d+)\)$", subhead)): # IBM 401(K) PLAN (30200)
                self.planId = match.group(1)
            else:
                logging.error(f"Unable to determine plan id from [{subhead}].")

            ifXcptionMsg = "render holdings summary"
            link = self.pageDrawWait.until(element_to_be_clickable(NbControl.HOLDINGS_LINK),
                                           "Timed out waiting for holdings summary")
            self.webDriver.execute_script("arguments[0].click();", link)

            ifXcptionMsg = "render holdings details"
            link = self.pageDrawWait.until(element_to_be_clickable(NbControl.DETAILS_LINK),
                                           "Timed out waiting for holdings details")
            self.webDriver.execute_script("arguments[0].click();", link)

            ifXcptionMsg = "select share details"
            dropdown = Select(self.pageDrawWait.until(presence_of_element_located(NbControl.SELECT_LOCATOR),
                                                      "Timed out waiting to select share details"))
            dropdown.select_by_value("sharesUnitsLabel")

            ifXcptionMsg = "find effective date"
            dateShown = self.webDriver.find_element(*NbControl.AS_OF_DATE_LOCATOR).text
            self.effectiveDate = datetime.strptime(dateShown, "As of %b-%d-%Y").date() # As of Sep-09-2026

            return True
        except NoSuchWindowException:
            logging.info(f"Browser gone ({ifXcptionMsg}).")

            return False
        except WebDriverException as e:
            raise NbException.fromXcp(ifXcptionMsg, e) from e
    # end navigateToHoldingDetails()

    def getHoldings(self) -> Iterator[NbHolding]:
        """Generate NetBenefits holdings and their current values"""
        ifXcptionMsg = "find holdings table"
        try:
            # lookup data for holdings
            hTbl = self.webDriver.find_element(*NbControl.HOLDINGS_TABLE_LOCATOR)
            tHdrs = [hdr.text for hdr in
                hTbl.find_elements(By.CSS_SELECTOR, "table > thead > tr > th")]
            bodyRows = hTbl.find_elements(By.CSS_SELECTOR, "table > tbody > tr")

            ifXcptionMsg = "find holdings data"
            for bRow in bodyRows:
                dataDict = {ky: dat.text for ky, dat in
                    zip(tHdrs, bRow.find_elements(By.TAG_NAME, "td"))}

                if dataDict[NbHolding.NAME] != "Total":
                    yield NbHolding(dataDict, self.effectiveDate)
            # end for bRow
        except Exception as e:
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
