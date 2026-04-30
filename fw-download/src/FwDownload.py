
# noinspection PyPackageRequirements
import __main__
from pathlib import Path

import locale
import logging
from configparser import ConfigParser
from csv import DictWriter
from itertools import chain

from NbControl import NbControl
from util import Configure


class FwDownload(object):

    def __init__(self):
        """Retrieve the CSV properties"""
        props = Path("..", "..", "MdHobby", "fwimport", "src", "main", "resources", "fw-import")
        cParser = ConfigParser()

        with open(props.with_suffix(".properties")) as lines:
            # Python 3.12 ConfigParser requires a section header, so prepend one named {}
            sectionHeader: tuple[str, ...] = ("[{}]", )
            lines = chain(sectionHeader, lines)
            cParser.read_file(lines)

        self.csvProps = dict(cParser.items("{}"))

    # end __init__()

    def writeCsv(self, nbCtl: NbControl) -> None:
        cp = self.csvProps
        outFn = Path.home().joinpath("Downloads",
                                     f"NbPosition{nbCtl.effectiveDate}").with_suffix(".csv")

        with open(outFn, "w", newline="") as csvFile:
            for i, hldn in enumerate(nbCtl.getHoldings()):
                logging.info(str(hldn))
                row = {cp["col.account.num"]: nbCtl.planId,
                       cp["col.ticker"]:      hldn.ticker,
                       cp["col.name"]:        hldn.name,
                       cp["col.shares"]:      hldn.shares,
                       cp["col.price"]:       hldn.getPrice(),
                       cp["col.value"]:       hldn.bal,
                       cp["col.date"]:        hldn.eDate}

                if i == 0:
                    writer = DictWriter(csvFile, row.keys())
                    writer.writeheader()
                writer.writerow(row)
            # end for each holding
        # end with csv file
        logging.info(f"Wrote {i + 1} holdings to {outFn.name}.")

    # end writeCsv(NbControl)

    def downloadHoldings(self) -> None:

        with NbControl() as nbCtl:
            if nbCtl.navigateToHoldingsDetails():
                self.writeCsv(nbCtl)

            if nbCtl.autoStartBrowser and nbCtl.loggedIn:
                nbCtl.waitForLogout()
        # end with nb control

    # end downloadHoldings()

# end class FwDownload


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    Configure.logToFile()
    logging.info("Preparing to download price data from NetBenefits.")

    try:
        fw = FwDownload()
        fw.downloadHoldings()
    except Exception as xcption:
        logging.error(xcption)
        logging.debug(f"{xcption.__class__.__name__} suppressed:", exc_info=xcption)

    logging.info(f"Exiting {Path(__main__.__file__ or "no file name").stem}.")
