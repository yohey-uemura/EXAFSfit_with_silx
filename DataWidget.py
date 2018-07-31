# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'DataWidget.ui'
#
# Created by: PyQt5 UI code generator 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(320, 700)
        self.toolBox = QtWidgets.QToolBox(Form)
        self.toolBox.setGeometry(QtCore.QRect(20, 30, 280, 621))
        self.toolBox.setToolTip("")
        self.toolBox.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.toolBox.setFrameShadow(QtWidgets.QFrame.Plain)
        self.toolBox.setObjectName("toolBox")
        self.page_3 = QtWidgets.QWidget()
        self.page_3.setGeometry(QtCore.QRect(0, 0, 280, 559))
        self.page_3.setObjectName("page_3")
        self.listWidget = QtWidgets.QListWidget(self.page_3)
        self.listWidget.setGeometry(QtCore.QRect(10, 50, 260, 331))
        self.listWidget.setObjectName("listWidget")
        self.progressBar = QtWidgets.QProgressBar(self.page_3)
        self.progressBar.setGeometry(QtCore.QRect(10, 460, 260, 40))
        self.progressBar.setMinimumSize(QtCore.QSize(260, 40))
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.cB_use_previous = QtWidgets.QCheckBox(self.page_3)
        self.cB_use_previous.setGeometry(QtCore.QRect(90, 510, 181, 30))
        self.cB_use_previous.setMinimumSize(QtCore.QSize(120, 30))
        self.cB_use_previous.setObjectName("cB_use_previous")
        self.cB_ploteach = QtWidgets.QCheckBox(self.page_3)
        self.cB_ploteach.setGeometry(QtCore.QRect(150, 0, 120, 40))
        self.cB_ploteach.setMinimumSize(QtCore.QSize(120, 40))
        self.cB_ploteach.setObjectName("cB_ploteach")
        self.pB_Open = QtWidgets.QPushButton(self.page_3)
        self.pB_Open.setGeometry(QtCore.QRect(0, 0, 120, 40))
        self.pB_Open.setMinimumSize(QtCore.QSize(120, 40))
        self.pB_Open.setMaximumSize(QtCore.QSize(160, 40))
        self.pB_Open.setObjectName("pB_Open")
        self.lineEdit = QtWidgets.QLineEdit(self.page_3)
        self.lineEdit.setGeometry(QtCore.QRect(10, 420, 260, 30))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setBold(True)
        font.setWeight(75)
        self.lineEdit.setFont(font)
        self.lineEdit.setStyleSheet("background-color: rgb(230, 230, 230);\n"
"color: rgb(252, 1, 7);")
        self.lineEdit.setAlignment(QtCore.Qt.AlignCenter)
        self.lineEdit.setObjectName("lineEdit")
        self.label = QtWidgets.QLabel(self.page_3)
        self.label.setGeometry(QtCore.QRect(10, 390, 171, 30))
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.toolBox.addItem(self.page_3, "")
        self.page_4 = QtWidgets.QWidget()
        self.page_4.setGeometry(QtCore.QRect(0, 0, 280, 559))
        self.page_4.setObjectName("page_4")
        self.listWidget_2 = QtWidgets.QListWidget(self.page_4)
        self.listWidget_2.setGeometry(QtCore.QRect(10, 10, 260, 461))
        self.listWidget_2.setMinimumSize(QtCore.QSize(260, 450))
        self.listWidget_2.setObjectName("listWidget_2")
        self.show_TableView = QtWidgets.QCheckBox(self.page_4)
        self.show_TableView.setGeometry(QtCore.QRect(10, 490, 121, 20))
        self.show_TableView.setObjectName("show_TableView")
        self.toolBox.addItem(self.page_4, "")

        self.retranslateUi(Form)
        self.toolBox.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.cB_use_previous.setText(_translate("Form", "Use the previous result"))
        self.cB_ploteach.setText(_translate("Form", "Plot each data"))
        self.pB_Open.setText(_translate("Form", "Open data"))
        self.lineEdit.setText(_translate("Form", "ALL"))
        self.label.setText(_translate("Form", "Fit Data(ex: 1-3,5,6 or \'ALL\')"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_3), _translate("Form", "EXAFS Data"))
        self.show_TableView.setText(_translate("Form", "Table View"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_4), _translate("Form", "Fit Results"))

