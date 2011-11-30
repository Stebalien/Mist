# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/jonathan/Programming/Python/mist/gui/forms/renameTagsDialog.ui'
#
# Created: Wed Nov 30 14:07:03 2011
#      by: pyside-uic @pyside_tools_VERSION@ running on PySide 1.0.6
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_renameTagsDialog(object):
    def setupUi(self, renameTagsDialog):
        renameTagsDialog.setObjectName("renameTagsDialog")
        renameTagsDialog.resize(329, 103)
        self.verticalLayout = QtGui.QVBoxLayout(renameTagsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tagNameLabel = QtGui.QLabel(renameTagsDialog)
        self.tagNameLabel.setObjectName("tagNameLabel")
        self.verticalLayout.addWidget(self.tagNameLabel)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtGui.QLabel(renameTagsDialog)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.tagValueInput = QtGui.QLineEdit(renameTagsDialog)
        self.tagValueInput.setObjectName("tagValueInput")
        self.horizontalLayout.addWidget(self.tagValueInput)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QtGui.QDialogButtonBox(renameTagsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(renameTagsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), renameTagsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), renameTagsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(renameTagsDialog)

    def retranslateUi(self, renameTagsDialog):
        renameTagsDialog.setWindowTitle(QtGui.QApplication.translate("renameTagsDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.tagNameLabel.setText(QtGui.QApplication.translate("renameTagsDialog", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("renameTagsDialog", "New Value", None, QtGui.QApplication.UnicodeUTF8))

