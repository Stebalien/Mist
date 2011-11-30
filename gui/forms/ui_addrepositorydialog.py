# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/jonathan/Programming/Python/mist/gui/addRepositoryDialog.ui'
#
# Created: Sat Oct  1 18:45:06 2011
#      by: pyside-uic @pyside_tools_VERSION@ running on PySide 1.0.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_addRepositoryDialog(object):
    def setupUi(self, addRepositoryDialog):
        addRepositoryDialog.setObjectName("addRepositoryDialog")
        addRepositoryDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        addRepositoryDialog.resize(316, 145)
        self.verticalLayout = QtGui.QVBoxLayout(addRepositoryDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtGui.QLabel(addRepositoryDialog)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.nameInput = QtGui.QLineEdit(addRepositoryDialog)
        self.nameInput.setObjectName("nameInput")
        self.horizontalLayout.addWidget(self.nameInput)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtGui.QLabel(addRepositoryDialog)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.locationInput = QtGui.QLineEdit(addRepositoryDialog)
        self.locationInput.setObjectName("locationInput")
        self.horizontalLayout_2.addWidget(self.locationInput)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.managedInput = QtGui.QCheckBox(addRepositoryDialog)
        self.managedInput.setObjectName("managedInput")
        self.horizontalLayout_3.addWidget(self.managedInput)
        self.monitoredInput = QtGui.QCheckBox(addRepositoryDialog)
        self.monitoredInput.setObjectName("monitoredInput")
        self.horizontalLayout_3.addWidget(self.monitoredInput)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.buttonBox = QtGui.QDialogButtonBox(addRepositoryDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(addRepositoryDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), addRepositoryDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), addRepositoryDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(addRepositoryDialog)

    def retranslateUi(self, addRepositoryDialog):
        addRepositoryDialog.setWindowTitle(QtGui.QApplication.translate("addRepositoryDialog", "Add Repository", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("addRepositoryDialog", "Name", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("addRepositoryDialog", "Location", None, QtGui.QApplication.UnicodeUTF8))
        self.managedInput.setText(QtGui.QApplication.translate("addRepositoryDialog", "Managed", None, QtGui.QApplication.UnicodeUTF8))
        self.monitoredInput.setText(QtGui.QApplication.translate("addRepositoryDialog", "Monitored", None, QtGui.QApplication.UnicodeUTF8))

