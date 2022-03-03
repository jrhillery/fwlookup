
import logging
from collections import deque
from decimal import Decimal, ROUND_HALF_EVEN
from logging.config import dictConfig

from typing import Optional


class Currency(object):
    _CURRENCY_SYMBOL = "$"
    _DECIMAL_POINT = "."
    _NEGATIVE_SIGN = "-"
    _TRAILING_NEGATIVE_SIGN = ""
    _POSITIVE_SIGN = ""
    _THOUSANDS_SEP = ","

    @staticmethod
    def delocalize(st):
        # type: (str) -> str
        """Parses a string as a normalized number."""

        # first, get rid of any currency symbol
        st = st.replace(Currency._CURRENCY_SYMBOL, "")

        # next, get rid of any grouping
        st = st.replace(Currency._THOUSANDS_SEP, "")

        # next, replace the decimal point with a dot
        dp = Currency._DECIMAL_POINT

        return st if dp == "." else st.replace(dp, ".")
    # end delocalize(str)

    @staticmethod
    def format(value, model=None):
        # type: (Decimal, Optional[Decimal]) -> str
        """Format currency with the number of fraction digits in 'model'"""
        if model:
            value = value.quantize(model, ROUND_HALF_EVEN)
        valueParts = value.as_tuple()
        result = deque()

        if valueParts.sign:
            result.appendleft(Currency._TRAILING_NEGATIVE_SIGN)
        digits = map(str, valueParts.digits)
        i = valueParts.exponent

        while i < 0:
            result.appendleft(digits.pop() if digits else "0")
            i += 1
        result.appendleft(Currency._DECIMAL_POINT)

        if not digits:
            result.appendleft("0")
        i = 0

        while digits:
            result.appendleft(digits.pop())
            i += 1

            if i == 3 and digits:
                i = 0
                result.appendleft(Currency._THOUSANDS_SEP)
        # end while
        result.appendleft(Currency._CURRENCY_SYMBOL)
        result.appendleft(Currency._NEGATIVE_SIGN if valueParts.sign
                          else Currency._POSITIVE_SIGN)

        return "".join(result)
    # end format(Decimal, Optional[Decimal])

# end class Currency


if __name__ == "__main__":
    dictConfig({
        "version": 1,
        "formatters": {
            "simple": {
                "format": "%(asctime)s.%(msecs)03d %(message)s",
                "datefmt": "%H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            }
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console"]
        }
    })
    num = Decimal(".0004")
    logging.info("%s; %s", Currency.format(num), Currency.format(Decimal("-1234.56"), num))
    thou = Decimal("-123000.9876543210")
    logging.info("%s; %s", Currency.format(thou), Currency.format(thou, num))
    logging.info("%s", Currency.delocalize("-$22,345.123"))
