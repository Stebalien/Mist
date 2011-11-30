# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/jonathan/Programming/Python/mist/gui/addPlaylistDialog.ui'
#
# Created: Sat Oct  1 18:44:54 2011
#      by: pyside-uic @pyside_tools_VERSION@ running on PySide 1.0.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_addPlaylistDialog(object):
    def setupUi(self, addPlaylistDialog):
        addPlaylistDialog.setObjectName("addPlaylistDialog")
        addPlaylistDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        addPlaylistDialog.resize(348, 78)
        self.gridLayout = QtGui.QGridLayout(addPlaylistDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtGui.QLabel(addPlaylistDialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.nameInput = QtGui.QLineEdit(addPlaylistDialog)
        self.nameInput.setObjectName("nameInput")
        self.gridLayout.addWidget(self.nameInput, 0, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(addPlaylistDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 2)

        self.retranslateUi(addPlaylistDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), addPlaylistDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), addPlaylistDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(addPlaylistDialog)

    def retranslateUi(self, addPlaylistDialog):
        addPlaylistDialog.setWindowTitle(QtGui.QApplication.translate("addPlaylistDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("addPlaylistDialog", "Name", None, QtGui.QApplication.UnicodeUTF8))

