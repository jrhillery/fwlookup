# show Fidelity NetBenefits balance updates
from collections import deque

from typing import Optional

from StagedInterface import StagedInterface
from com.leastlogic.moneydance.util import MdStorageUtil
from com.leastlogic.swing.util import HTMLPane
from java.awt import AWTEvent
from java.awt.event import ActionEvent, WindowEvent
from java.lang import AutoCloseable, System, Throwable
from java.util import Map
from javax.swing import GroupLayout, JButton, JFrame, JPanel
from javax.swing import JScrollPane, LayoutStyle, WindowConstants
from javax.swing.border import EmptyBorder


class FwLookupConsole(JFrame):

    def __init__(self, title, storage):
        # type: (str, Optional[Map]) -> None
        super(FwLookupConsole, self).__init__(title)
        self.mdStorage = MdStorageUtil("fwlookup", storage)
        self.staged = None  # type: Optional[StagedInterface]
        self.closeableResources = deque()  # type: deque[AutoCloseable]

        # Initialize the swing components.
        self.defaultCloseOperation = WindowConstants.DO_NOTHING_ON_CLOSE
        self.mdStorage.setWindowCoordinates(self, 639, 395)
        contentPane = JPanel()
        contentPane.border = EmptyBorder(5, 5, 5, 5)
        self.contentPane = contentPane

        self.btnCommit = JButton("Commit")  # type: JButton
        self.btnCommit.enabled = False
        self.btnCommit.toolTipText = "Commit changes to Moneydance"
        self.btnCommit.actionPerformed = self.pressCommit
        HTMLPane.reduceHeight(self.btnCommit, 20)

        self.pnOutputLog = HTMLPane()  # type: HTMLPane
        scrollPane = JScrollPane(self.pnOutputLog)
        gl_contentPane = GroupLayout(contentPane)
        gl_contentPane.setHorizontalGroup(
            gl_contentPane.createParallelGroup(GroupLayout.Alignment.TRAILING)
                .addGroup(gl_contentPane.createSequentialGroup()
                    .addContainerGap(403, 0x7fff)
                    .addComponent(self.btnCommit))
                .addComponent(scrollPane, GroupLayout.DEFAULT_SIZE, 532, 0x7fff)
        )
        gl_contentPane.setVerticalGroup(
            gl_contentPane.createParallelGroup(GroupLayout.Alignment.LEADING)
                .addGroup(gl_contentPane.createSequentialGroup()
                    .addComponent(self.btnCommit)
                    .addPreferredGap(LayoutStyle.ComponentPlacement.RELATED)
                    .addComponent(scrollPane, GroupLayout.DEFAULT_SIZE, 271, 0x7fff))
        )
        contentPane.layout = gl_contentPane
        self.setIconImage(HTMLPane.readResourceImage(
            "/flat-funnel-32.png", self.pnOutputLog.getClass()))
        self.setVisible(True)
    # end __init__(str)

    # noinspection PyUnusedLocal
    def pressCommit(self, event):
        # type: (ActionEvent) -> None
        """Invoked when Commit is selected."""

        if self.staged:
            changeSummary = self.staged.commitChanges()

            if changeSummary:
                self.addText(changeSummary)
            self.enableCommitButton(self.staged.isModified())
    # end pressCommit(ActionEvent)

    def addText(self, text):
        # type: (str) -> None
        """append HTML-text to the output log text area"""
        self.pnOutputLog.addText(text)
    # end addText(str)

    def showInFront(self):
        # type: () -> None
        """Show our window in front of all others"""
        self.setVisible(True)
        self.setAlwaysOnTop(True)
        # self.toFront()
        self.setAlwaysOnTop(False)
        # self.requestFocus()
    # end showInFront()

    def clearText(self):
        # type: () -> None
        """Clear the output log text area."""
        self.pnOutputLog.clearText()
    # end clearText()

    def enableCommitButton(self, b):
        # type: (bool) -> None
        """true to enable the button, otherwise false"""
        self.btnCommit.enabled = b
    # end enableCommitButton(bool)

    def addCloseableResource(self, closeable):
        # type: (AutoCloseable) -> None
        """Store an object with resources to close."""
        self.closeableResources.appendleft(closeable)
    # end addCloseableResource(AutoCloseable)

    def removeCloseableResource(self, closeable):
        # type: (AutoCloseable) -> None
        """Remove an object that no longer has resources to close."""
        self.closeableResources.remove(closeable)
    # end removeCloseableResource(AutoCloseable)

    def processEvent(self, event):
        # type: (AWTEvent) -> None
        """Process events on this window."""
        if event.getID() == WindowEvent.WINDOW_CLOSING:
            self.goAway()
        else:
            super(FwLookupConsole, self).processEvent(event)
    # end processEvent(AWTEvent)

    def goAway(self):
        # type: () -> None
        """Remove this frame."""
        self.mdStorage.persistWindowCoordinates(self)
        self.setVisible(False)
        self.dispose()

        while len(self.closeableResources) > 0:
            # Release any resources we acquired.
            try:
                self.closeableResources.popleft().close()
            except Throwable as e:
                e.printStackTrace(System.err)
        # end while
    # end goAway()

# end class FwLookupConsole


if __name__ == "__main__":
    frame = FwLookupConsole("FW Lookup Title", None)  # type: FwLookupConsole
    # noinspection SpellCheckingInspection
    frame.addText("Change Eaton Vance Equity Inc (ETY) price for today from $14.00 to "
                  "$14.23 (<span class='incrs'>+1.64%</span>).")
    # noinspection SpellCheckingInspection
    frame.addText("Change IBM Common Stock (IBM) price for today from "
                  "$119.00 to $118.84 (<span class='decrs'>-0.13%</span>).")
    frame.enableCommitButton(True)
