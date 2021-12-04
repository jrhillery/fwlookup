from abc import ABCMeta, abstractmethod


class StagedInterface(object):
    """An interface to manage staged changes"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def commitChanges(self):
        # type: () -> int
        """Commit any changes to Moneydance and return the number of changes set"""
        pass
    # end commitChanges()

    @abstractmethod
    def isModified(self):
        # type: () -> bool
        """Return True when we have uncommitted changes in memory"""
        pass
    # end isModified()

# end class StagedInterface
