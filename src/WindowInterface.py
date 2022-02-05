from abc import ABCMeta, abstractmethod
from decimal import Decimal

from java.text import DecimalFormat


class WindowInterface(object):
    """An interface to control our Swing window"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def getCurrencyFormat(self, amount):
        # type: (Decimal) -> DecimalFormat
        """Get a currency number format with the number of fraction digits in 'amount'"""
        pass
    # end getCurrencyFormat(Decimal)

    @abstractmethod
    def display(self, *msgs):
        # type: (*str) -> None
        """Display the given text messages"""
        pass
    # end display(str...)

    @abstractmethod
    def showInFront(self):
        # type: () -> None
        """Show our window in front of all others"""
        pass
    # end showInFront()

    @abstractmethod
    def isCancelled(self):
        # type: () -> bool
        """Returns true if this task was cancelled before completing normally"""
        pass
    # end isCancelled()

# end class WindowInterface
