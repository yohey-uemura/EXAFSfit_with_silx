# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'guessMinMax.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(368, 201)
        self.pB_set = QtWidgets.QPushButton(Form)
        self.pB_set.setGeometry(QtCore.QRect(230, 150, 110, 40))
        self.pB_set.setObjectName("pB_set")
        self.splitter = QtWidgets.QSplitter(Form)
        self.splitter.setGeometry(QtCore.QRect(80, 20, 187, 111))
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.widget = QtWidgets.QWidget(self.splitter)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.widget)
        self.label.setMinimumSize(QtCore.QSize(50, 20))
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.lE_value = QtWidgets.QLineEdit(self.widget)
        self.lE_value.setMinimumSize(QtCore.QSize(110, 20))
        self.lE_value.setObjectName("lE_value")
        self.horizontalLayout.addWidget(self.lE_value)
        self.widget1 = QtWidgets.QWidget(self.splitter)
        self.widget1.setObjectName("widget1")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.widget1)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.widget1)
        self.label_2.setMinimumSize(QtCore.QSize(50, 20))
        self.label_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.lE_min = QtWidgets.QLineEdit(self.widget1)
        self.lE_min.setMinimumSize(QtCore.QSize(110, 20))
        self.lE_min.setObjectName("lE_min")
        self.horizontalLayout_2.addWidget(self.lE_min)
        self.widget2 = QtWidgets.QWidget(self.splitter)
        self.widget2.setObjectName("widget2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.widget2)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(self.widget2)
        self.label_3.setMinimumSize(QtCore.QSize(50, 20))
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.lE_max = QtWidgets.QLineEdit(self.widget2)
        self.lE_max.setMinimumSize(QtCore.QSize(110, 20))
        self.lE_max.setObjectName("lE_max")
        self.horizontalLayout_3.addWidget(self.lE_max)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pB_set.setText(_translate("Form", "OK"))
        self.label.setText(_translate("Form", "Value:"))
        self.label_2.setText(_translate("Form", "Min:"))
        self.label_3.setText(_translate("Form", "Max:"))

