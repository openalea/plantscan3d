# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/arsouze/Documents/Modeles/Codes/OpenAlea/plantscan3d/src/openalea/plantscan3d/database/properties/dateprop.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(347, 50)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.propNameLabel = QtWidgets.QLabel(Form)
        self.propNameLabel.setObjectName("propNameLabel")
        self.horizontalLayout.addWidget(self.propNameLabel)
        self.propValue = QtWidgets.QDateEdit(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.propValue.sizePolicy().hasHeightForWidth())
        self.propValue.setSizePolicy(sizePolicy)
        self.propValue.setCalendarPopup(True)
        self.propValue.setObjectName("propValue")
        self.horizontalLayout.addWidget(self.propValue)
        self.deleteButton = QtWidgets.QToolButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.deleteButton.sizePolicy().hasHeightForWidth())
        self.deleteButton.setSizePolicy(sizePolicy)
        self.deleteButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("delete.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.deleteButton.setIcon(icon)
        self.deleteButton.setCheckable(False)
        self.deleteButton.setPopupMode(QtWidgets.QToolButton.DelayedPopup)
        self.deleteButton.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.deleteButton.setAutoRaise(False)
        self.deleteButton.setArrowType(QtCore.Qt.NoArrow)
        self.deleteButton.setObjectName("deleteButton")
        self.horizontalLayout.addWidget(self.deleteButton)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.propNameLabel.setText(_translate("Form", "TextLabel"))
