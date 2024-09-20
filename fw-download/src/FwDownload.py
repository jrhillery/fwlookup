
import __main__
import locale
import logging
from pathlib import Path

from NbControl import NbControl
from util import Configure

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    Configure.logToFile()
    logging.info("Preparing to download price data from NetBenefits.")

    try:
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
