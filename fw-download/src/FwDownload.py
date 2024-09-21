
import __main__
import locale
import logging
from configparser import ConfigParser
from itertools import chain
from pathlib import Path

from NbControl import NbControl
from util import Configure


class FwDownload(object):

    def __init__(self):
        self.csvProps: dict[str, str] | None = None

    def getCsvProps(self) -> dict[str, str]:
        """Retrieve the CSV properties"""
        if not self.csvProps:
            rp = Path("resources")
            cParser = ConfigParser()

            with open(rp.joinpath("fw-import").with_suffix(".properties")) as lines:
                # Python 3.12 ConfigParser requires a section header, so prepend one named {}
                lines = chain(("[{}]", ), lines)
                cParser.read_file(lines)

            self.csvProps = dict(cParser.items("{}"))
        # end if no props

        return self.csvProps
    # end getCsvProps()

# end class FwDownload


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    Configure.logToFile()
    logging.info("Preparing to download price data from NetBenefits.")

    try:
        fw = FwDownload()

        with NbControl() as nbCtl:
            nbCtl.getHoldingsDriver()

            if nbCtl.navigateToHoldingsDetails():
                for hldn in nbCtl.getHoldings():
                    logging.info(str(hldn))
                # end for each holding
        # end with
    except Exception as xcption:
        logging.error(xcption)
        logging.debug(f"{xcption.__class__.__name__} suppressed:", exc_info=xcption)

    logging.info(f"Exiting {Path(__main__.__file__).stem}.")
