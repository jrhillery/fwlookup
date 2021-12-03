from decimal import Decimal

from java.text import DecimalFormat


class WindowInterface(object):
    """An informal interface to control our Swing window"""

    def getCurrencyFormat(self, amount):
        # type: (Decimal) -> DecimalFormat
        """Get a currency number format with the number of fraction digits in 'amount'"""
        pass
    # end getCurrencyFormat(Decimal)

    def display(self, *msgs):
        # type: (*str) -> None
        """Display the given text messages"""
        pass
    # end display(str...)

    def showInFront(self):
        # type: () -> None
        """Show our window in front of all others"""
        pass
    # end showInFront()

# end class WindowInterface
