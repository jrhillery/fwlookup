
# noinspection PyPackageRequirements
import __main__
import locale
import logging
from configparser import ConfigParser
from csv import DictWriter
from itertools import chain
from pathlib import Path

from NbControl import NbControl
from util import Configure


class FwDownload(object):

    def __init__(self):
        self.csvProps: dict[str, str] | None = None

    # end __init__()

    def getCsvProps(self) -> dict[str, str]:
        """Retrieve the CSV properties"""
        if not self.csvProps:
            props = Path("resources", "fw-import")
            cParser = ConfigParser()

            with open(props.with_suffix(".properties")) as lines:
                # Python 3.12 ConfigParser requires a section header, so prepend one named {}
                lines = chain(("[{}]", ), lines)
                cParser.read_file(lines)

            self.csvProps = dict(cParser.items("{}"))
        # end if no props

        return self.csvProps
    # end getCsvProps()

    def writeCsv(self, nbCtl: NbControl) -> None:
        cp = self.getCsvProps()
        outFn = Path.home().joinpath("Downloads",
                                     f"NbPosition{nbCtl.effectiveDate}").with_suffix(".csv")

        with open(outFn, "w", newline="") as csvFile:
            writer = DictWriter(csvFile, fieldnames=())

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
                    writer.fieldnames = row.keys()
                    writer.writeheader()
                writer.writerow(row)
            # end for each holding
        # end with csv file
        logging.info(f"Wrote {i + 1} holdings to {outFn.name}.")

    # end writeCsv(NbControl)

    def downloadHoldings(self) -> None:

        with NbControl() as nbCtl:
            nbCtl.getHoldingsDriver()

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

    logging.info(f"Exiting {Path(__main__.__file__).stem}.")
