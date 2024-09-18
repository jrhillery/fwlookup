
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
    def delocalize(st: str) -> str:
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
    def format(value: Decimal, model: Optional[Decimal]=None) -> str:
        """Format currency with the number of fraction digits in 'model'"""
        if model:
            value = value.quantize(model, ROUND_HALF_EVEN)
        valueParts = value.as_tuple()
        result = deque()

        if valueParts.sign:
            result.appendleft(Currency._TRAILING_NEGATIVE_SIGN)
        digits = map(str, reversed(valueParts.digits))
        i = valueParts.exponent

        while i < 0:
            result.appendleft(next(digits, "0"))
            i += 1
        result.appendleft(Currency._DECIMAL_POINT)
        needsSep = False
        i = 0

        for digit in digits:
            if needsSep:
                result.appendleft(Currency._THOUSANDS_SEP)
            result.appendleft(digit)
            i += 1
            needsSep = i % 3 == 0
        # end for each digit

        if i == 0:
            result.appendleft("0")
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
