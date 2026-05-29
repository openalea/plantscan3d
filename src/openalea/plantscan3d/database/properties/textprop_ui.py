# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/arsouze/Documents/Modeles/Codes/OpenAlea/plantscan3d/src/openalea/plantscan3d/database/properties/textprop.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(351, 136)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.propNameLabel = QtWidgets.QLabel(Form)
        self.propNameLabel.setObjectName("propNameLabel")
        self.horizontalLayout_2.addWidget(self.propNameLabel)
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
        self.horizontalLayout_2.addWidget(self.deleteButton)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.propValue = QtWidgets.QTextEdit(Form)
        self.propValue.setObjectName("propValue")
        self.verticalLayout.addWidget(self.propValue)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.propNameLabel.setText(_translate("Form", "TextLabel"))
        self.propValue.setHtml(_translate("Form", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
