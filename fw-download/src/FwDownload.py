
import logging

from NbControl import NbControl
from util import Configure

if __name__ == "__main__":
    Configure.logToFile()
    try:
        nbCtl = NbControl()
        nbCtl.main()
    except Exception as xcption:
        logging.error(xcption)
        logging.debug(f"{xcption.__class__.__name__} suppressed:", exc_info=xcption)
