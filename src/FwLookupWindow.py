# show Fidelity NetBenefits balance updates
from decimal import Decimal

from com.leastlogic.swing.util import HTMLPane
from java.awt import AWTEvent, Dimension
from java.awt.event import ActionEvent, WindowEvent
from java.lang import System
from java.text import DecimalFormat, NumberFormat
from javax.swing import GroupLayout, JButton, JFrame, JPanel
from javax.swing import JScrollPane, LayoutStyle, WindowConstants
from javax.swing.border import EmptyBorder
from typing import Callable, Optional


class FwLookupWindow(JFrame):

	def __init__(self, title):
		# type: (str) -> None
		super(FwLookupWindow, self).__init__(title)
		self.commitChanges = None  # type: Optional[Callable[[], None]]
		self.isModified = None  # type: Optional[Callable[[], bool]]
		self.releaseResources = None  # type: Optional[Callable[[], None]]

		# Initialize the swing components.
		self.defaultCloseOperation = WindowConstants.DO_NOTHING_ON_CLOSE
		self.size = 596, 368
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
	# end __init__(str)

	def pressCommit(self, event):
		# type: (ActionEvent) -> None
		"""Invoked when Commit is selected."""

		if self.commitChanges:
			self.commitChanges()

		if self.isModified:
			self.enableCommitButton(self.isModified())
	# end pressCommit(ActionEvent)

	def addText(self, text):
		# type: (str) -> None
		"""append HTML text to the output log text area"""
		self.pnOutputLog.addText(text)
	# end addText(str)

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

	def getCurrencyFormat(self, amount):
		# type: (Decimal) -> DecimalFormat
		amtScale = -amount.as_tuple().exponent
		formatter = NumberFormat.getCurrencyInstance(self.getLocale())
		formatter.minimumFractionDigits = amtScale

		return formatter
	# end getCurrencyFormat(Decimal)

	def processEvent(self, event):
		# type: (AWTEvent) -> None
		"""Process events on this window."""
		if event.getID() == WindowEvent.WINDOW_CLOSING:
			self.closeWindow()
		else:
			super(FwLookupWindow, self).processEvent(event)
	# end processEvent(AWTEvent)

	def closeWindow(self):
		self.goAway()

		if self.releaseResources:
			# Release any resources we acquired.
			self.releaseResources()
	# end closeWindow()

	def goAway(self):
		# type: () -> None
		"""Remove this frame."""
		winSize = self.getSize()  # type: Dimension
		System.err.write("Closing {} with width={:.0f}, height={:.0f}.\n".format(
			self.getTitle(), winSize.width, winSize.height))
		self.setVisible(False)
		self.dispose()
	# end goAway()

# end class FwLookupWindow


if __name__ == "__main__":
	frame = FwLookupWindow("FW Lookup Title")  # type: FwLookupWindow
	frame.visible = True
	amt = Decimal("123.50")
	fmt = frame.getCurrencyFormat(amt)
	frame.addText(fmt.format(amt))
	frame.enableCommitButton(True)
