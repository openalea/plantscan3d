# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/arsouze/Documents/Modeles/Codes/OpenAlea/plantscan3d/src/openalea/plantscan3d/progress_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ProgressDialog(object):
    def setupUi(self, ProgressDialog):
        ProgressDialog.setObjectName("ProgressDialog")
        ProgressDialog.setWindowModality(QtCore.Qt.WindowModal)
        ProgressDialog.resize(420, 155)
        ProgressDialog.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        ProgressDialog.setModal(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(ProgressDialog)
        self.verticalLayout.setContentsMargins(15, 13, 15, 13)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setObjectName("verticalLayout")
        self.titeLabel = QtWidgets.QLabel(ProgressDialog)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.titeLabel.setFont(font)
        self.titeLabel.setObjectName("titeLabel")
        self.verticalLayout.addWidget(self.titeLabel, 0, QtCore.Qt.AlignTop)
        self.descLabel = QtWidgets.QLabel(ProgressDialog)
        self.descLabel.setText("")
        self.descLabel.setObjectName("descLabel")
        self.verticalLayout.addWidget(self.descLabel, 0, QtCore.Qt.AlignTop)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 6, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.progressBar = QtWidgets.QProgressBar(ProgressDialog)
        self.progressBar.setMinimumSize(QtCore.QSize(0, 26))
        self.progressBar.setMaximum(10000)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setObjectName("progressBar")
        self.horizontalLayout.addWidget(self.progressBar)
        self.progressLabel = QtWidgets.QLabel(ProgressDialog)
        self.progressLabel.setMinimumSize(QtCore.QSize(60, 0))
        self.progressLabel.setStyleSheet("margin-bottom: 1px;\n"
"margin-right: 0px;")
        self.progressLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.progressLabel.setObjectName("progressLabel")
        self.horizontalLayout.addWidget(self.progressLabel)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(-1, 5, -1, -1)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.cancelButton = QtWidgets.QPushButton(ProgressDialog)
        self.cancelButton.setMinimumSize(QtCore.QSize(120, 31))
        self.cancelButton.setMaximumSize(QtCore.QSize(120, 31))
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout_2.addWidget(self.cancelButton)
        self.closeButton = QtWidgets.QPushButton(ProgressDialog)
        self.closeButton.setMinimumSize(QtCore.QSize(120, 31))
        self.closeButton.setMaximumSize(QtCore.QSize(120, 31))
        self.closeButton.setObjectName("closeButton")
        self.horizontalLayout_2.addWidget(self.closeButton)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(ProgressDialog)
        QtCore.QMetaObject.connectSlotsByName(ProgressDialog)

    def retranslateUi(self, ProgressDialog):
        _translate = QtCore.QCoreApplication.translate
        ProgressDialog.setWindowTitle(_translate("ProgressDialog", "Please wait - PlantScan3D"))
        self.titeLabel.setText(_translate("ProgressDialog", "Processing..."))
        self.progressLabel.setText(_translate("ProgressDialog", "0.00%"))
        self.cancelButton.setText(_translate("ProgressDialog", "Cancel"))
        self.closeButton.setText(_translate("ProgressDialog", "Close"))
