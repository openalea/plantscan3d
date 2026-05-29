# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/arsouze/Documents/Modeles/Codes/OpenAlea/plantscan3d/src/openalea/plantscan3d/slider_widget.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Slider(object):
    def setupUi(self, Slider):
        Slider.setObjectName("Slider")
        self.verticalLayout = QtWidgets.QVBoxLayout(Slider)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(5, -1, 5, 5)
        self.horizontalLayout.setSpacing(5)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.titleLabel = QtWidgets.QLabel(Slider)
        self.titleLabel.setObjectName("titleLabel")
        self.horizontalLayout.addWidget(self.titleLabel)
        spacerItem = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.valueLineEdit = QtWidgets.QLineEdit(Slider)
        self.valueLineEdit.setMinimumSize(QtCore.QSize(45, 19))
        self.valueLineEdit.setMaximumSize(QtCore.QSize(45, 19))
        self.valueLineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.valueLineEdit.setObjectName("valueLineEdit")
        self.horizontalLayout.addWidget(self.valueLineEdit)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.sliderLayout = QtWidgets.QVBoxLayout()
        self.sliderLayout.setSpacing(0)
        self.sliderLayout.setObjectName("sliderLayout")
        self.sliderBar = QtWidgets.QWidget(Slider)
        self.sliderBar.setMinimumSize(QtCore.QSize(0, 3))
        self.sliderBar.setMaximumSize(QtCore.QSize(16777215, 3))
        self.sliderBar.setStyleSheet("QWidget {\n"
"    background-color: rgb(176, 176, 176);\n"
"    margin-left: 5px;\n"
"    margin-right: 5px;\n"
"}\n"
"\n"
"QWidget:disabled {\n"
"    background-color: rgb(194, 194, 194);\n"
"}")
        self.sliderBar.setObjectName("sliderBar")
        self.sliderLayout.addWidget(self.sliderBar)
        self.handleLayout = QtWidgets.QHBoxLayout()
        self.handleLayout.setSpacing(0)
        self.handleLayout.setObjectName("handleLayout")
        spacerItem1 = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Minimum)
        self.handleLayout.addItem(spacerItem1)
        self.handleImage = QtWidgets.QLabel(Slider)
        self.handleImage.setMinimumSize(QtCore.QSize(12, 11))
        self.handleImage.setMaximumSize(QtCore.QSize(12, 11))
        self.handleImage.setObjectName("handleImage")
        self.handleLayout.addWidget(self.handleImage)
        spacerItem2 = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.handleLayout.addItem(spacerItem2)
        self.sliderLayout.addLayout(self.handleLayout)
        self.verticalLayout.addLayout(self.sliderLayout)

        self.retranslateUi(Slider)
        QtCore.QMetaObject.connectSlotsByName(Slider)

    def retranslateUi(self, Slider):
        _translate = QtCore.QCoreApplication.translate
        self.titleLabel.setText(_translate("Slider", "Value :"))
        self.valueLineEdit.setText(_translate("Slider", "0"))
