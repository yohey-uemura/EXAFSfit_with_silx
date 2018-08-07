import PyQt5.QtCore as QtCore # Importing PyQt5 will force silx to use it
from silx.gui import qt
from silx.gui import widgets as silxwidgets
from silx.gui.plot import Plot1D, PlotWidget, PlotWindow
from silx.gui.plot.actions.control import ZoomBackAction, CrosshairAction
from ControlWidget import Ui_Form as Form_ControlW
from DataWidget import Ui_Form as Form_DataW
from OutputWidget import Ui_Form as Form_ButtomW
from dialog_Fit import Ui_Dialog as ui_tableview
from dialog_FEFF import Ui_Dialog as dialogFEFF
from dialog_Text import Ui_Dialog as ui_Text
from guessMinMax import Ui_Form as uiSetRange
import os
import sys
import natsort
import pandas as pd
import h5py
import fileinput
import re
import use_larch as LarchF
import larch
from larch_plugins.xafs import autobk, xftf, xftr, feffit, _ff2chi, feffrunner
from larch_plugins.xafs.feffit import feffit_transform, feffit_dataset, feffit_report
from larch_plugins.xafs.feffdat import feffpath
from larch_plugins.io import read_ascii
import larch.builtins as larch_builtins
import larch.fitting as larchfit

import numpy as np
import math
import yaml


import matplotlib

matplotlib.use('Qt5Agg')


from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


# qapp = qt.QApplication([])
#
# plot = Plot1D()  # Create the plot widget
# plot.show()  # Make the plot widget visible
#
# qapp.exec_()

class params:
    dir = ""
    current_dfile = ""
    outdir = ""
    if sys.platform == 'win32':
        homestr = 'HOMEPATH'
    else:
        homestr = 'HOME'
    colors = ["Red", "Blue", "Green", "DeepPink", "Orange", "Brown", "OrangeRed",
              "DarkRed", "Crimson", "DarkBlue", "DarkGreen", "Hotpink", "Coral",
              "DarkMagenta", "FireBrick", "GoldenRod", "Grey",
              "Indigo", "MediumBlue", "MediumVioletRed", "Black"]
    colors_in_rgb = ["#FF0000", "#0000FF", "#00FF00", "#FF1493", "#FFA500", "#A52A2A", "#FF4500",
                     "#8B0000", "#DC143C", "#00008B", "#006400", "#FF69B4", "#FF7F50",
                     "#8B008B", "#B22222", "#DAA520", "#BEBEBE",
                     "#00416A", "#0000CD", "#C71585", "#000000"]
    dict_color = {}
    for i in range(len(colors)):
        dict_color[colors[i]] = colors_in_rgb[i]

    dict_FitConditions = {}
    feffdir = ''

class Plot1DWithContextMenu(Plot1D):
    """This class adds a custom context menu to PlotWidget's plot area."""

    def __init__(self, *args, **kwargs):
        super(Plot1DWithContextMenu, self).__init__(*args, **kwargs)

        customAction = qt.QAction(qt.QIcon('Save-icon.png'),
                                  "Save Current Data",
                                  parent=self)

        # Create QAction for the context menu once for all
        self._zoomBackAction = ZoomBackAction(plot=self, parent=self)
        self._myAction = customAction

        # Retrieve PlotWidget's plot area widget
        plotArea = self.getWidgetHandle()

        # Set plot area custom context menu
        plotArea.setContextMenuPolicy(qt.Qt.CustomContextMenu)
        plotArea.customContextMenuRequested.connect(self._contextMenu)

    def _contextMenu(self, pos):
        """Handle plot area customContextMenuRequested signal.

        :param QPoint pos: Mouse position relative to plot area
        """
        # Create the context menu
        menu = qt.QMenu(self)
        menu.addAction(self._zoomBackAction)
        menu.addSeparator()
        menu.addAction(self._myAction)

        # Displaying the context menu at the mouse position requires
        # a global position.
        # The position received as argument is relative to PlotWidget's
        # plot area, and thus needs to be converted.
        plotArea = self.getWidgetHandle()
        globalPosition = plotArea.mapToGlobal(pos)
        menu.exec_(globalPosition)

class MainWindow(qt.QMainWindow):
    wSignal = qt.Signal()
    wS_trendplot = qt.Signal()
    wS_canvasdraw = qt.Signal()
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle('PlotWidget with spinboxes')
        self.datdir = os.environ[params.homestr]
        self.timer = qt.QBasicTimer()
        self.mylarch = larch.Interpreter(with_plugins=False)
        print (self.datdir)
        MainWidget = qt.QWidget(parent=self.centralWidget())
        LeftWidget = qt.QDockWidget(parent=self)
        LeftWidget.setMinimumWidth(320)
        LeftWidget.setFeatures(qt.QDockWidget.DockWidgetFloatable |
                                qt.QDockWidget.DockWidgetMovable)

        self.uiform_data = Form_DataW()
        self.uiform_data.setupUi(LeftWidget)
        self.uiform_data.progressBar.setValue(0)

        self.CenterWidget = qt.QTabWidget()

        self.CenterWidget.setMinimumWidth(700)
        self.CenterWidget.setMinimumHeight(550)

        # CenterWidget = qt.QWidget(parent=MainWidget)
        # CenterWidget.setMinimumWidth(700)
        # CenterWidget.setMinimumHeight(550)
        RightWidget = qt.QDockWidget(parent=self)
        RightWidget.setMinimumWidth(320)
        RightWidget.setFeatures(qt.QDockWidget.DockWidgetFloatable |
                 qt.QDockWidget.DockWidgetMovable)

        BottomWidget = qt.QWidget(parent=self)
        BottomWidget.setMinimumHeight(100)
        BottomWidget.setMinimumWidth(720)
        # BottomWidget.setFeatures(qt.QDockWidget.DockWidgetFloatable |
        #          qt.QDockWidget.DockWidgetMovable)
        self.uiform_bottom = Form_ButtomW()
        self.uiform_bottom.setupUi(BottomWidget)
        # CtrlWidget = qt.loadUi('ControlWidget.ui',qt.QDockWidget(parent=self))
        # self.resize(1000,600)
        self.uiform_ctrl = Form_ControlW()
        self.uiform_ctrl.setupUi(RightWidget)

        self.buttonGroup = qt.QButtonGroup()
        self.buttonGroup.addButton(self.uiform_ctrl.rB_plot_k)
        self.buttonGroup.addButton(self.uiform_ctrl.rB_plot_r)
        self.buttonGroup.addButton(self.uiform_ctrl.rB_plot_q)

        self.addDockWidget(qt.Qt.LeftDockWidgetArea, LeftWidget)
        self.addDockWidget(qt.Qt.RightDockWidgetArea,RightWidget)
        # self.addDockWidget(qt.Qt.BottomDockWidgetArea,BottomWidget)

        HLayout = qt.QGridLayout()
        MainWidget.setLayout(HLayout)
        self.setCentralWidget(MainWidget)

        HLayout.addWidget(self.CenterWidget, 0, 0)
        HLayout.addWidget(BottomWidget,1,0)

        #plt = Plot1D()
        plt = Plot1DWithContextMenu()
        def SaveCurrentDataSets():
            if self.uiform_data.listWidget.count() and plt.getAllCurves():
                dict_Curves = {}
                xlabel = self.buttonGroup.checkedButton().text()
                dataOrder = []
                for l in plt.getAllCurves():
                    dict_Curves[l.getLegend().split(':')[0]+':'+xlabel] = l.getData()[0]
                    dataOrder.append(l.getLegend().split(':')[0]+':'+xlabel)
                    dict_Curves[l.getLegend()] = l.getData()[1]
                    dataOrder.append(l.getLegend())

                maxL = 0
                for i in range(len(dataOrder)):
                    if i == 0:
                        maxL = len(dict_Curves[dataOrder[i]])
                    elif i >=1:
                        if maxL < len(dict_Curves[dataOrder[i]]):
                            maxL = len(dict_Curves[dataOrder[i]])

                for i in range(len(dataOrder)):
                    if len(dict_Curves[dataOrder[i]]) < maxL:
                        tarray = dict_Curves[dataOrder[i]].tolist()
                        for j in range(maxL-len(tarray)):
                            tarray.append(float("nan"))
                        print (len(tarray))
                        dict_Curves[dataOrder[i]] = tarray[:]
                for i in range(len(dataOrder)):
                    print (dataOrder[i] +':' + str(len(dict_Curves[dataOrder[i]])))

                FO_dialog = qt.QFileDialog(self)
                file = FO_dialog.getSaveFileName(None, 'Set the output file',
                                                 params.dir, "csv files(*.csv *.CSV)")
                if file[0]:
                    pd.DataFrame(dict_Curves)[dataOrder].to_csv(os.path.abspath(file[0]),
                                                                sep=" ",
                                                                index=False
                                                                )
                    #print (l.getData())
                    #print (l.getLegend())
        plt._myAction.triggered.connect(SaveCurrentDataSets)
        plt.getLegendsDockWidget().setMaximumHeight(150)


        self.childWidget_Tab1 = qt.QWidget()
        self.childWidget_Tab1.setLayout(qt.QGridLayout())
        self.childWidget_Tab1.layout().addWidget(plt)

        self.CenterWidget.addTab(self.childWidget_Tab1,'EXAFS plot')

        self.childWidget_Tab2 = qt.QWidget()

        self.childWidget_Tab2.setLayout(qt.QGridLayout())
        self.CenterWidget.addTab(self.childWidget_Tab2, 'Trend plot')

        self.fig = Figure(figsize=(320, 320), dpi=72, facecolor=(1, 1, 1), edgecolor=(0, 0, 0))
        self.canvas = FigureCanvas(self.fig)

        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("data")
        self.ax.set_ylabel("Param")
        self.ax_r = self.ax.twinx()
        self.ax_r.set_ylabel("R-factor")

        # navibar = NavigationToolbar(canvas, widget)
        navibar = NavigationToolbar(self.canvas, parent=None)
        self.childWidget_Tab2.layout().addWidget(self.canvas,0,0)
        self.childWidget_Tab2.layout().addWidget(navibar, 1, 0)
        # self.CenterWidget.setCurrentIndex(1)
        # self.CenterWidget.addTab('Trend plot')

        self.dialog_suffix = qt.QDialog()
        self.suffix_d = ui_Text()
        self.suffix_d.setupUi(self.dialog_suffix)

        self.dialog_SetRange = qt.QDialog()
        self.uiSetRange = uiSetRange()
        self.uiSetRange.setupUi(self.dialog_SetRange)

        self.tableview = qt.QDialog()
        self.uiTableView = ui_tableview()
        self.uiTableView.setupUi(self.tableview)

        self.TableW = silxwidgets.TableWidget.TableWidget()

        self.uiTableView.scrollArea.setWidget(self.TableW)

        self.TableW.setContextMenuPolicy(qt.Qt.CustomContextMenu)

        def openMenu(position):
            num_of_row = self.TableW.currentRow()
            num_of_collumn = self.TableW.currentColumn()
            menu = qt.QMenu()
            actionChangeSubscript = menu.addAction("Change Subscripts of this row")
            # actionSetRange = menu.addAction("Guess with max and min")
            action = menu.exec_(self.TableW.viewport().mapToGlobal(position))
            if action == actionChangeSubscript:
                if self.TableW.item(num_of_row, 2).text() != 'EMPTY':
                    self.dialog_suffix.exec_()
            # elif action == actionSetRange:
            #     if self.TableW.item(num_of_row, 2).text() != 'EMPTY' and \
            #         any([num_of_collumn == x for x in [5, 8, 11, 14,17] ]):
            #         for term in ['lE_value', 'lE_min', 'lE_max']:
            #             getattr(self.uiSetRange, term).clear()
            #         self.uiSetRange.lE_value.setText(self.TableW.item(num_of_row, num_of_collumn).text())
            #         combobox = self.TableW.cellWidget(num_of_row, num_of_collumn-1)
            #         if ':' in self.TableW.item(num_of_row, num_of_collumn).text():
            #             A = self.TableW.item(num_of_row, num_of_collumn).text().split(':')
            #             self.uiSetRange.lE_value.setText(A[0])
            #             l = ''
            #             for term in A[1]:
            #                 l += term
            #             # l.replace('[','').replace(']','')
            #             self.uiSetRange.lE_min.setText(l[1:-1].split(',')[0])
            #             self.uiSetRange.lE_max.setText(l[1:-1].split(',')[1])
            #         # print (combobox.currentText())
            #         if combobox.currentIndex() !=0:
            #             combobox.setCurrentIndex(3)
            #         self.dialog_SetRange.exec_()

        def change_suffix():
            num_of_row = self.TableW.currentRow()
            # print num_of_row
            for i in [3, 6, 9, 12,15]:
                if self.TableW.item(num_of_row, 2).text() != 'EMPTY':
                    suffix = self.suffix_d.lineEdit.text().replace(" ", '')
                    name = self.TableW.item(num_of_row, i).text()
                    if re.match(r"(.+)_\w+", name) != None:
                        name_1 = re.match(r"(.+)_\w+", name).group(1)
                        self.TableW.setItem(num_of_row, i, qt.QTableWidgetItem(name_1 + '_' + suffix))
                    elif re.match(r"(.+)_$", name) != None:
                        self.TableW.setItem(num_of_row, i, qt.QTableWidgetItem(name + suffix))
            self.dialog_suffix.done(1)

        def guessWithRange():

            def isfloat(value):
                try:
                    float(value)
                    return True
                except ValueError:
                    return False

            num_of_row = self.TableW.currentRow()
            num_of_collumn = self.TableW.currentColumn()
            txt = ''
            if isfloat(self.uiSetRange.lE_value.text()):
                txt += self.uiSetRange.lE_value.text()+':'
            else:
                txt += ','
            if isfloat(self.uiSetRange.lE_min.text()):
                txt +='['+self.uiSetRange.lE_min.text()+','
            else:
                txt += '['+'float("nan"),'
            if isfloat(self.uiSetRange.lE_max.text()):
                txt += self.uiSetRange.lE_max.text() + ']'
            else:
                txt += 'float("nan")'+']'

            if not isfloat(txt.split(':')[0]):
                pass
            elif isfloat(txt.split(':')[0]) and any([not math.isnan(x) for x in eval(txt.split(':')[1])]):
                self.TableW.setItem(num_of_row, num_of_collumn, qt.QTableWidgetItem(txt.replace('float("nan")','')))
            elif isfloat(txt.split(':')[0]) and all([not math.isnan(x) for x in eval(txt.split(':')[1])]):\
                self.TableW.setItem(num_of_row, num_of_collumn, qt.QTableWidgetItem(txt))

            self.dialog_SetRange.done(1)



        self.suffix_d.pushButton.clicked.connect(change_suffix)
        self.uiSetRange.pB_set.clicked.connect(guessWithRange)

        self.TableW.customContextMenuRequested.connect(openMenu)

        self.TableW.setRowCount(20)
        self.TableW.setColumnCount(18)
        for i in range(0,20):
            # params.FitConditions['FEFF file'].append('')
            self.TableW.setItem(i,2,qt.QTableWidgetItem("EMPTY"))
            self.TableW.item(i,2).setForeground(qt.QColor('gray'))
        labels = ['Use?','SetFEFF','PATH']
        for term in ['N','dE','dR','ss','C3']:
            paramName = 'Name: '+term
            paramValue = 'Val.: '+term
            paramState = 'State: '+term
            labels+= [paramName,paramState,paramValue]
        for i in range(3,18):
            if i%3 == 0:
                self.TableW.setColumnWidth(i, 70)
            elif i%3 == 1:
                self.TableW.setColumnWidth(i,80)
            elif i%3 == 2:
                self.TableW.setColumnWidth(i,70)

        self.GroupBox = qt.QButtonGroup()
        self.GroupCheckBox = qt.QButtonGroup()
        self.GroupCheckBox.setExclusive(False)

        self.TableW.setHorizontalHeaderLabels(labels)

        self.dialog_resultTable = qt.QDialog()
        self.dialog_resultTable.setLayout(qt.QGridLayout())
        self.ui_resultTable = silxwidgets.TableWidget.TableView()
        self.dialog_resultTable.layout().addWidget(self.ui_resultTable)

        def show_and_hide_tableView(boolean):
            if boolean:
                self.dialog_resultTable.show()
            else:
                self.dialog_resultTable.hide()
        # def checkstate():
        #     sign = 0
        #     # print ("L840")
        #     for cB in self.GroupCheckBox.buttons():
        #         if params.FitConditions['FEFF file'][self.GroupCheckBox.buttons().index(cB)] != '':
        #             sign = 1
        #             break
        #     if self.u.textBrowser.toPlainText() != '' and len(self.exafs_cB.buttons()) != 0 and sign:
        #         self.u.pB_Fit.setEnabled(True)


        self.uiFEFFdialog = qt.QDialog()
        uiFEFF = dialogFEFF()
        uiFEFF.setupUi(self.uiFEFFdialog)

        def add_FEFF_path(button):
            pathn = self.GroupBox.buttons().index(button)+1
            params.dict_FitConditions['PATH:' + str(pathn - 1)]["FilePATH"] = ""
            uiFEFF.lcdNumber.display(pathn)
            uiFEFF.comboBox.clear()
            # params.index_ = params.FitConditions['pB'].index(button)
            dat_dir = os.environ[params.homestr]
            if dir != "":
                dat_dir = params.feffdir
            FO_dialog = qt.QFileDialog()
            # print (FO_dialog.filters())
            # file = FO_dialog.getOpenFileName(parent=None,filter = "FEFF input(feff.inp)",caption="Open feff.inp",dir=dat_dir)
            file = FO_dialog.getOpenFileName(None, "Open feff.inp",
                                             dat_dir, "FEFF input(feff.inp)")
            mylarch = larch.Interpreter(with_plugins=False)
            if file[0] != '':
                uiFEFF.textBrowser_2.clear()
                params.feffdir = os.path.dirname(os.path.abspath(file[0]))
                uiFEFF.textBrowser_2.append(params.feffdir)
                uiFEFF.textBrowser.clear()
                str_ = "{:16s}{:16s}{:16s}{:16s}{:16s}".format('PATH:', 'Route:', 'Distance:', 'Relative AMP',
                                                               'Degeneracy')
                uiFEFF.textBrowser.append(str_)
                self.uiFEFFdialog.show()
                if not os.path.isfile(os.path.dirname(file[0]) + '/paths.dat'):
                    rFEFF = feffrunner.feffrunner(file[0], _larch=mylarch)
                    rFEFF.run()
                txt_array = LarchF.read_FEFF(file[0])
                list = []
                for key in natsort.natsorted(txt_array.keys()):
                    uiFEFF.textBrowser.append(txt_array[key])
                    t_array = txt_array[key].split(':')
                    list.append(t_array[0] + ':' + t_array[1] + ':' + t_array[2])
                uiFEFF.comboBox.addItems(list)
                uiFEFF.textBrowser.verticalScrollBar().setValue(0)
            else:
                pB_index = self.GroupBox.buttons().index(button)
                self.GroupCheckBox.buttons()[pB_index].toggle()


        def close_dialog_f():
            tfont = qt.QFont('Arial', 11)
            pathn = uiFEFF.lcdNumber.intValue()-1
            item = self.TableW.item(pathn,3)
            # print item
            if self.TableW.item(pathn,2).text() == "EMPTY":
                for i in range(3,18):
                    self.TableW.removeCellWidget(pathn,i)
                title = re.sub("\s+",'',uiFEFF.comboBox.currentText())
                self.TableW.setItem(pathn,2,qt.QTableWidgetItem(title))
                self.TableW.item(pathn,2).setForeground(qt.QColor('black'))
                num_of_feffpath = "{:04d}".format(uiFEFF.comboBox.currentIndex() + 1)
                params.dict_FitConditions['PATH:'+str(pathn)]['FilePATH'] =\
                    uiFEFF.textBrowser_2.toPlainText()+'/'+'feff'+num_of_feffpath+'.dat'
                # print (os.path.basename(params.FitConditions['FEFF file'][params.index_]))
                for term in ['N','dE','dR','ss','C3']:
                    i = 0
                    while i < 3:
                        if i == 0:
                            name = term+'_'+str(pathn+1)
                            self.TableW.setItem(pathn,3+3*['N','dE','dR','ss','C3'].index(term)+i,qt.QTableWidgetItem(name))
                            self.TableW.item(pathn,3+3*['N','dE','dR','ss','C3'].index(term)+i).setFont(tfont)
                            self.TableW.item(pathn,3+3*['N','dE','dR','ss','C3'].index(term)+i).setForeground(qt.QColor('blue'))
                        elif i == 1:
                            comboBox = qt.QComboBox()
                            comboBox.addItems(['guess','set','def','guess_wRange'])
                            if term == 'C3':
                                comboBox.setCurrentIndex(1)
                            self.TableW.setCellWidget(pathn,3+3*['N','dE','dR','ss','C3'].index(term)+i,comboBox)
                        elif i == 2:
                            value = 0.0
                            if term == 'N':
                                value = 1.0
                                string = "{:.1f}".format(value)
                                self.TableW.setItem(pathn,3+3*['N','dE','dR','ss','C3'].index(term)+i,qt.QTableWidgetItem(string))
                                self.TableW.item(pathn,3+3*['N','dE','dR','ss','C3'].index(term)+i).setFont(tfont)
                            elif term == 'dR':
                                value = 0.00
                                string = "{:.2f}".format(value)
                                self.TableW.setItem(pathn,3+3*['N','dE','dR','ss','C3'].index(term)+i,qt.QTableWidgetItem(string))
                                self.TableW.item(pathn,3+3*['N','dE','dR','ss','C3'].index(term)+i).setFont(tfont)
                            elif term == 'ss':
                                value = 0.003
                                string = "{:.3f}".format(value)
                                self.TableW.setItem(pathn,3+3*['N','dE','dR','ss','C3'].index(term)+i,qt.QTableWidgetItem(string))
                                self.TableW.item(pathn,3+3*['N','dE','dR','ss','C3'].index(term)+i).setFont(tfont)
                            elif term == 'C3':
                                value = 0.0
                                string = "{:.3f}".format(value)
                                self.TableW.setItem(pathn, 3 + 3 * ['N', 'dE', 'dR', 'ss', 'C3'].index(term) + i,qt.QTableWidgetItem(string))
                                self.TableW.item(pathn,3 + 3 * ['N', 'dE', 'dR', 'ss', 'C3'].index(term) + i).setFont(tfont)
                            else:
                                string = "{:.1f}".format(value)
                                self.TableW.setItem(pathn,3+3*['N','dE','dR','ss'].index(term)+i,qt.QTableWidgetItem(string))
                                self.TableW.item(pathn,3+3*['N','dE','dR','ss'].index(term)+i).setFont(tfont)
                        i += 1
            else:
                title = re.sub("\s+", '', uiFEFF.comboBox.currentText())
                self.TableW.setItem(pathn, 2, qt.QTableWidgetItem(title))
                num_of_feffpath = "{:04d}".format(uiFEFF.comboBox.currentIndex() + 1)
                params.dict_FitConditions['PATH:' + str(pathn)]['FilePATH'] = params.feffdir + '/' + 'feff' + num_of_feffpath + '.dat'
            ###Make params####
            self.uiFEFFdialog.done(1)
            self.tableview.setFocus()
        #     checkstate()

        for i in range(0,self.TableW.rowCount()):
            pB = qt.QPushButton('Open')
            pB.setObjectName('pB_'+'PATH_'+str(i))
            self.TableW.setCellWidget(i,1,pB)
            # params.FitConditions['pB'] += [pB]
            pB.setEnabled(False)
            self.GroupBox.addButton(pB)
            cB = qt.QCheckBox(str(i+1),self)
            cB.setObjectName('cB_'+'PATH_'+str(i))
            params.dict_FitConditions['PATH:'+str(i)] = {}
            self.TableW.setCellWidget(i,0,cB)
            cB.toggled.connect(pB.setEnabled)

            # params.FitConditions['cB'] +=[cB]
            self.GroupCheckBox.addButton(cB)
        self.TableW.setColumnWidth(0,50)
        self.TableW.setColumnWidth(1,80)

        self.GroupBox.buttonClicked[qt.QAbstractButton].connect(add_FEFF_path)


        # RightWidget = qt.loadUi("ControlWidget.ui")

        def plot_each(widget):

            k, chi = LarchF.read_chi_file(self.datdir+'/'+widget.text().split(':')[1])

            # print (k)
            dk_wind = self.uiform_ctrl.dB_window_dk.value()
            dr_wind = self.uiform_ctrl.dB_window_dr.value()
            wind = self.uiform_ctrl.cB_WindowType.currentText()
            kweight = float(self.uiform_ctrl.cB_kweight.currentText())
            k_min = self.uiform_ctrl.dB_kmin.value()
            k_max = self.uiform_ctrl.dB_kmax.value()
            r_min = self.uiform_ctrl.dB_rmin.value()
            r_max = self.uiform_ctrl.dB_rmax.value()

            r, chir, chir_mag, chir_im = LarchF.calcFT(k, chi, kweight,
                                                       k_min, k_max, wind, dk_wind)
            kwindow = LarchF.calcFTwindow(k, k_min, k_max, dk_wind, wind)
            rwindow = LarchF.calcFTwindow(r, r_min, r_max, dr_wind, wind)
            q, chi_q = LarchF.calc_rFT(r, chir, r_min, r_max,
                                       k_max + 2.0, wind, dr_wind)
            if self.uiform_ctrl.rB_plot_k.isChecked():
                plt.addCurve(k,chi*(k**kweight),legend=widget.text().split(':')[1]+':chi(k)*k^'+str(int(kweight)),
                             linewidth=1.5, color="blue")
                # chik_max = np.max(np.abs(chi*(k**kweight)))
                # plt.addCurve(k,kwindow*chik_max*1.25,legend='window')
            elif self.uiform_ctrl.rB_plot_r.isChecked():
                plt.addCurve(r, chir_mag,legend=widget.text().split(':')[1]+':chir_mag',
                             linewidth=1.5, color="black")
                plt.addCurve(r,chir_im,legend=widget.text().split(':')[1]+':chir_im',
                             linewidth=1.5, color="blue")
                # plt.addCurve(r, rwindow)
            elif self.uiform_ctrl.rB_plot_q.isChecked():
                plt.addCurve(q, chi_q,legend=widget.text().split(':')[1]+":chiq",linewidth=1.5, color="blue")
                # plt.addCurve(k, kwindow)
            plt.getLegendsDockWidget().show()

        def dialog_for_OpenFiles(dir, str_caption, str_filter):

            dat_dir = os.environ[params.homestr]
            if dir == "":
                dat_dir = os.environ[params.homestr]
            elif dir != "":
                dat_dir = dir
            FO_dialog = qt.QFileDialog(self)
            files = FO_dialog.getOpenFileNames(None, str_caption,
                                             dat_dir, str_filter)
            print (files)
            if files[0]:
                return files[0], os.path.abspath(os.path.dirname(files[0][0]))
            else:
                return [], ''

        self.uiform_data.listWidget.setSelectionMode(qt.QAbstractItemView.SingleSelection)
        self.uiform_data.listWidget_2.setSelectionMode(qt.QAbstractItemView.MultiSelection)
        self.uiform_data.cB_ploteach.setCheckState(qt.Qt.Checked)

        def plotFitResults(cB):
            result_file = os.path.dirname(self.uiform_bottom.textBrowser.toPlainText())+'/Log/'+ \
                      'result_'+os.path.basename(self.uiform_bottom.textBrowser.toPlainText()).replace('csv','h5').replace('CSV','h5')
            PlotSpace = self.buttonGroup.checkedButton().text()

            k_weight = float(self.uiform_ctrl.cB_kweight.currentText())
            wind = self.uiform_ctrl.cB_WindowType.currentText()
            dk_wind = self.uiform_ctrl.dB_window_dk.value()
            dr_wind = self.uiform_ctrl.dB_window_dr.value()
            k_min = self.uiform_ctrl.dB_kmin.value()
            k_max = self.uiform_ctrl.dB_kmax.value()
            r_min = self.uiform_ctrl.dB_rmin.value()
            r_max = self.uiform_ctrl.dB_rmax.value()

            if os.path.isfile(result_file):
                result = h5py.File(result_file, 'r')
                if cB.text() in result:
                    if PlotSpace == 'k':
                        k_fit = result[cB.text()]['chi_fit'][:, 0]
                        chi_fit = result[cB.text()]['chi_fit'][:, 1]
                        plt.addCurve(k_fit,chi_fit * k_fit ** float(self.uiform_ctrl.cB_kweight.currentText()),
                                     color=params.dict_color["Red"],legend="fit",linewidth=1.5)
                    elif PlotSpace == 'r':
                        k_fit = result[cB.text()]['chi_fit'][:, 0]
                        chi_fit = result[cB.text()]['chi_fit'][:, 1]
                        r_fit, chir_fit, chir_mag_fit, chir_im_fit = LarchF.calcFT(k_fit, chi_fit,
                                                                                   k_weight,
                                                                                   k_min,
                                                                                   k_max,
                                                                                   wind, dk_wind)
                        plt.addCurve(r_fit, chir_mag_fit, color=params.dict_color["Red"], legend='fit: mag', linewidth=1.5)
                        plt.addCurve(r_fit, chir_im_fit, color=params.dict_color["DeepPink"], legend='fit: img', linewidth=1.5)
                    elif PlotSpace == 'q':
                        k_fit = result[cB.text()]['chi_fit'][:, 0]
                        chi_fit = result[cB.text()]['chi_fit'][:, 1]
                        r_fit, chir_fit, chir_mag_fit, chir_im_fit = LarchF.calcFT(k_fit, chi_fit,k_weight,k_min,k_max,wind, dk_wind)
                        q_fit, chiq_fit = LarchF.calc_rFT(r_fit, chir_fit, r_min,r_max, k_max + 0.5,wind, dr_wind)
                        plt.addCurve(q_fit, chiq_fit, color=params.dict_color["Red"], legend='fit', linewidth=1.5)
                else:
                    msgBox = qt.QMessageBox()
                    msgBox.setText("The fitting results doesn't exist in this file.\nPlease choose another file")
                    msgBox.exec_()
            else:
                msgBox = qt.QMessageBox()
                msgBox.setText("The result filw could not be found.\nPlease choose the correct file")
                msgBox.exec_()

        def plotData():
            if plt.getAllCurves():
                plt.clear()
            dk_wind = self.uiform_ctrl.dB_window_dk.value()
            dr_wind = self.uiform_ctrl.dB_window_dr.value()
            wind = self.uiform_ctrl.cB_WindowType.currentText()
            kweight = float(self.uiform_ctrl.cB_kweight.currentText())
            k_min = self.uiform_ctrl.dB_kmin.value()
            k_max = self.uiform_ctrl.dB_kmax.value()
            r_min = self.uiform_ctrl.dB_rmin.value()
            r_max = self.uiform_ctrl.dB_rmax.value()
            for cb in self.uiform_data.listWidget.selectedItems():
                # print (cb)
                plot_each(cb)
                if self.uiform_ctrl.rB_wFit.isChecked() and self.uiform_data.cB_ploteach.isChecked():
                    plotFitResults(cb)
                if self.uiform_ctrl.rB_wModel.isChecked() and self.uiform_data.cB_ploteach.isChecked() and\
                        any([cb.isChecked() for cb in self.GroupCheckBox.buttons()]):
                    plot_ModelEXAFS()
            if self.uiform_data.listWidget.selectedItems():
                if self.uiform_ctrl.rB_plot_k.isChecked():
                    xmin, xmax = plt.getGraphXLimits()
                    ymin, ymax = plt.getGraphYLimits()
                    l = plt.getAllCurves()[0]
                    # x = np.arange(xmin,xmax,0.05)
                    x = l.getData()[0]
                    FTwindow = LarchF.calcFTwindow(x,k_min,k_max,dr_wind,wind)
                    plt.addCurve(x,FTwindow*ymax*1.05,legend="window",
                                 linewidth=1.5,color=params.dict_color["DarkGreen"])
                    plt.setGraphXLimits(0, 16.0)
                    plt.setGraphYLimits(ymin * 1.1, ymax * 1.1)
                    plt.setGraphYLabel(label="chi(k)"+"*"+"k^"+str(kweight))
                    plt.setGraphXLabel(label='k /A^-1')
                elif self.uiform_ctrl.rB_plot_r.isChecked():
                    xmin, xmax = plt.getGraphXLimits()
                    ymin, ymax = plt.getGraphYLimits()
                    l = plt.getAllCurves()[0]
                    # x = np.arange(xmin,xmax,0.05)
                    x = l.getData()[0]
                    FTwindow = LarchF.calcFTwindow(x,r_min,r_max,dr_wind,wind)
                    plt.addCurve(x,FTwindow*ymax*1.05,legend="window",
                                 linewidth=1.5, color=params.dict_color["DarkGreen"])
                    plt.setGraphXLimits(0, 6)
                    plt.setGraphYLimits(ymin * 1.1, ymax * 1.1)
                    plt.setGraphYLabel(label="FT[chi(k)" + "*" + "k^" + str(kweight)+"]")
                    plt.setGraphXLabel(label='R /A')
                elif self.uiform_ctrl.rB_plot_q.isChecked():

                    xmin, xmax = plt.getGraphXLimits()
                    ymin, ymax = plt.getGraphYLimits()
                    l = plt.getAllCurves()[0]
                    # x = np.arange(xmin,xmax,0.05)
                    x = l.getData()[0]
                    FTwindow = LarchF.calcFTwindow(x, k_min, k_max, dk_wind, wind)
                    plt.addCurve(x, FTwindow * ymax * 1.05, legend="window",
                                 linewidth=1.5,color=params.dict_color["DarkGreen"])
                    plt.setGraphXLimits(0, 16.0)
                    plt.setGraphYLimits(ymin*1.1,ymax*1.1)
                    plt.setGraphYLabel(label="chi(q)")
                    plt.setGraphXLabel(label='q /A^-1')
            # plt.addCurve()

        self.plotlines =[]

        def plotFittingTrends():
            if self.uiform_data.listWidget_2.count():
                datNames = self.Reserver.index.tolist()
                A_params = self.Reserver.keys().tolist()[:-1]
                if not self.timer.isActive():
                    self.fig.delaxes(self.ax_r)
                    self.fig.delaxes(self.ax)
                    self.ax = self.fig.add_subplot(111)
                    self.ax.set_xlabel("data")
                    self.ax.set_ylabel("Param")
                    self.ax_r = self.ax.twinx()
                    self.ax_r.set_ylabel("R-factor")
                xticsLabels = ['#'+x.split(':')[0] for x in self.Reserver.index.tolist()]
                for param in self.uiform_data.listWidget_2.selectedItems():
                    # if param.text() != 'R-factor':
                    xticsLabels.append('#'+param.text().split(':')[0])
                    dat = self.Reserver[param.text()].values
                    error = self.Reserver['delta('+param.text()+')']
                    i = A_params.index(param.text())
                    l = self.ax.errorbar(range(len(dat)),dat,yerr=error,
                                     label=param.text(), marker='o', color=params.colors[i], markersize=10
                                     )
                    self.plotlines.append(l)
                    # plt.addCurve(range(1,len(datNames)+1),dat,legend=param.text(),
                    #              symbol='o',color=params.dict_color[params.colors[i+1]],
                    #              yerror=error,yaxis='left')
                    # i+=1
                dat = self.Reserver['R-factor'].values
                self.ax_r.plot(range(len(dat)), dat,
                                 label='R-factor', marker='o', color="k", markersize=10
                                 )
                self.ax.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
                                ncol=2, mode="expand", borderaxespad=0.)
                self.ax_r.legend(loc=3)
                self.ax.relim(visible_only=True)
                self.ax.autoscale_view()
                self.ax_r.relim(visible_only=True)
                self.ax_r.autoscale_view()
                self.ax.set_xticks(range(len(dat)))
                self.ax.set_xticklabels(xticsLabels)


        def trendPlot_change_items():
            plotFittingTrends()
            if not self.timer.isActive():
                self.canvas.draw()
            # self.wS_canvasdraw.emit()
            # self.canvas.draw()
            # plt.setGraphYLabel(label="Params",axis='left')
            # xmin, xmax = plt.getGraphXLimits()
            # xwidth = abs(xmax-xmin)/2.0
            # xcenter = (xmin+xmax)/2.0
            # plt.setGraphXLimits(xcenter - xwidth * 1.1, xcenter + xwidth * 1.1)
            # ymin, ymax = plt.getGraphYLimits(axis='left')
            # ywidth = abs(ymax-ymin)/2.0
            # ycenter = (ymin + ymax) / 2.0
            # plt.setGraphYLimits(ycenter - ywidth * 1.25,
            #                     ycenter + ywidth * 1.25,
            #                     axis='left')
            # ymin, ymax = plt.getGraphYLimits(axis='right')
            # plt.setGraphYLimits(ymin * 1.1, ymax * 1.1, axis='right')
            #              ,
            #              )
        def plot_ModelEXAFS():
            fitParams = larch_builtins._group(self.mylarch)
            PlotSpace = self.buttonGroup.checkedButton().text()
            fitParams.s0_2 = larchfit.param(self.uiTableView.doubleSpinBox.value())
            if self.uiTableView.cB_use_anotherParams.isChecked() and self.uiTableView.lE_params.text() != '':
                tlist = self.uiTableView.lE_params.text().split(';')
                for term in tlist:
                    t_array = term.split('=')
                    param_name = t_array[0].replace(" ", "")
                    param_condition = t_array[1][1:-1].replace(" ", "").replace('(', "").replace(')', "").split(',')
                    setattr(fitParams, param_name, larchfit.guess(float(param_condition[0])))
            feffpathlist = []
            for cB in self.GroupCheckBox.buttons():
                if cB.isChecked():
                    index_ = self.GroupCheckBox.buttons().index(cB)
                    feffinp = params.dict_FitConditions['PATH:'+str(index_)]["FilePATH"]
                    path = feffpath(feffinp, _larch=self.mylarch)
                    # s02 = Name_for_N+'*'+'s0_2', e0 = Name_for_dE,sigma2 = Name_for_ss, deltar  = Name_for_dR,
                    Name_for_N = self.TableW.item(index_, 3).text()
                    State_for_N = self.TableW.cellWidget(index_, 4)
                    Value_for_N = self.TableW.item(index_, 5).text()
                    if State_for_N.currentText() == 'def':
                        setattr(fitParams, Name_for_N, larchfit.param(expr=Value_for_N))
                    else:
                        setattr(fitParams, Name_for_N, larchfit.param(float(Value_for_N)))

                    setattr(fitParams, 'degen_path_' + str(index_), path.degen)
                    # setattr(self.fitParams,'net_'+Name_for_N,larchfit.param(expr=Value_for_N+'*'+str(self.fit_dialog.doubleSpinBox.value())))
                    Name_for_dE = self.TableW.item(index_, 6).text()
                    State_for_dE = self.TableW.cellWidget(index_, 7)
                    Value_for_dE = self.TableW.item(index_, 8).text()
                    if State_for_dE.currentText() == 'def':
                        setattr(fitParams, Name_for_dE, larchfit.param(expr=Value_for_dE))
                    else:
                        setattr(fitParams, Name_for_dE, larchfit.param(float(Value_for_dE)))
                    Name_for_dR = self.TableW.item(index_, 9).text()
                    State_for_dR = self.TableW.cellWidget(index_, 10)
                    Value_for_dR = self.TableW.item(index_, 11).text()
                    if State_for_dR.currentText() == 'def':
                        setattr(fitParams, Name_for_dR, larchfit.param(expr=Value_for_dR))
                    else:
                        setattr(fitParams, Name_for_dR, larchfit.param(float(Value_for_dR)))
                    Name_for_ss = self.TableW.item(index_, 12).text()
                    State_for_ss = self.TableW.cellWidget(index_, 13)
                    Value_for_ss = self.TableW.item(index_, 14).text()
                    if State_for_ss.currentText() == 'def':
                        setattr(fitParams, Name_for_ss, larchfit.param(expr=Value_for_ss))
                    else:
                        setattr(fitParams, Name_for_ss, larchfit.param(float(Value_for_ss)))
                    Name_for_C3 = self.TableW.item(index_, 15).text()
                    State_for_C3 = self.TableW.cellWidget(index_, 16)
                    Value_for_C3 = self.TableW.item(index_, 17).text()
                    if State_for_C3.currentText() == 'def':
                        setattr(fitParams, Name_for_C3, larchfit.param(expr=Value_for_C3))
                    else:
                        setattr(fitParams, Name_for_C3, larchfit.param(float(Value_for_C3)))
                    path.s02 = Name_for_N + '*' + 's0_2' + '/' + 'degen_path_' + str(index_)
                    path.e0 = Name_for_dE
                    path.sigma2 = Name_for_ss
                    path.deltar = Name_for_dR
                    path.third = Name_for_C3
                    feffpathlist.append(path)
            FeffitTransform = feffit_transform(fitspace=self.uiform_ctrl.cB_FitSpace.currentText(),
                                               kmin=self.uiform_ctrl.dB_kmin.value(),
                                               kmax=self.uiform_ctrl.dB_kmax.value(),
                                               kw=float(self.uiform_ctrl.cB_kweight.currentText()),
                                               dk=self.uiform_ctrl.dB_window_dk.value(),
                                               window=self.uiform_ctrl.cB_WindowType.currentText(),
                                               rmin=self.uiform_ctrl.dB_rmin.value(),
                                               rmax=self.uiform_ctrl.dB_rmax.value(),
                                               _larch=self.mylarch,
                                               dr=self.uiform_ctrl.dB_window_dr.value())
            xafsdat = larch_builtins._group(self.mylarch)
            fname = self.datdir+'/'+ self.uiform_data.listWidget.item(0).text().split(':')[1]
            xafsdat.k, xafsdat.chi = LarchF.read_chi_file(fname)
            dset = feffit_dataset(data=xafsdat, pathlist=feffpathlist, transform=FeffitTransform,
                                  _larch=self.mylarch)
            out = feffit(fitParams, dset, _larch=self.mylarch)
            # _ff2chi(feffpathlist,fitParams,xas,_larch=self.mylarch)

            if PlotSpace == 'k':
                k_fit = dset.model.k
                chi_fit = dset.model.chi
                plt.addCurve(k_fit, chi_fit * k_fit ** float(self.uiform_ctrl.cB_kweight.currentText()),
                        linestyle='--', color=params.dict_color["Red"], legend='model',linewidth=1.5)
            elif PlotSpace == 'r':
                k_fit = dset.model.k
                chi_fit = dset.model.chi
                wind = self.uiform_ctrl.cB_WindowType.currentText()
                dk_wind = self.uiform_ctrl.dB_window_dk.value()
                r_fit, chir_fit, chir_mag_fit, chir_im_fit = LarchF.calcFT(k_fit, chi_fit,
                                                                           float(self.uiform_ctrl.cB_kweight.currentText()),
                                                                           self.uiform_ctrl.dB_kmin.value(),
                                                                           self.uiform_ctrl.dB_kmax.value(),
                                                                           wind, dk_wind)
                plt.addCurve(r_fit, chir_mag_fit, linestyle='--', color=params.dict_color["Red"], legend='FT:mag:model',linewidth=1.5)
                plt.addCurve(r_fit, chir_im_fit, linestyle='--', color=params.dict_color["DeepPink"], legend='FT:img:model',linewidth=1.5)
            elif PlotSpace == 'q':
                k_fit = dset.model.k
                chi_fit = dset.model.chi
                wind = self.uiform_ctrl.cB_WindowType.currentText()
                dk_wind = self.uiform_ctrl.dB_window_dk.value()
                dr_wind = self.uiform_ctrl.dB_window_dr.value()
                r_fit, chir_fit, chir_mag_fit, chir_im_fit = LarchF.calcFT(k_fit, chi_fit,
                                                                           float(self.uiform_ctrl.cB_kweight.currentText()),
                                                                           self.uiform_ctrl.dB_kmin.value(),
                                                                           self.uiform_ctrl.dB_kmax.value(),
                                                                           wind, dk_wind)
                q_fit, chiq_fit = LarchF.calc_rFT(r_fit, chir_fit,
                                                  self.uiform_ctrl.dB_rmin.value(),
                                                  self.uiform_ctrl.dB_rmax.value(),
                                                  self.uiform_ctrl.dB_kmax.value() + 0.5,
                                                  wind,
                                                  dr_wind)
                plt.addCurve(q_fit, chiq_fit,
                             linestyle='--', color=params.dict_color["Red"], legend='model',linewidth=1.5)

        def openFiles():
            while self.uiform_data.listWidget.count():
                item = self.uiform_data.listWidget.takeItem(0)
                del item
            files, self.datdir = dialog_for_OpenFiles(params.dir,
                                                     'Open chi files',
                                                     "chi files(*.xi *.chi *chik *.rex)")
            if files:
                for i in range(len(files)):
                    f = natsort.natsorted(files)[i]
                    cb = qt.QListWidgetItem(str(i + 1) + ':' + os.path.basename(f))
                    # cb = qt.QCheckBox(str(i + 1) + ':' + os.path.basename(f))
                    # cb.setObjectName(os.path.abspath(f))
                    self.uiform_data.listWidget.addItem(cb)
                self.uiform_data.listWidget.setCurrentRow(0)
            self.wSignal.emit()
            # print (self.uiform_data.listWidget.count())

        def changeSelectionMode():
            if  self.uiform_data.cB_ploteach.isChecked():
                self.uiform_data.listWidget.setSelectionMode(qt.QAbstractItemView.SingleSelection)
            else:
                self.uiform_data.listWidget.setSelectionMode(qt.QAbstractItemView.MultiSelection)

        def show_hide_tableview():
            if self.uiform_ctrl.cB_showParams.isChecked():
                self.tableview.show()
            else:
                self.tableview.hide()

        def close_tableview():
            self.tableview.hide()
            self.uiform_ctrl.cB_showParams.setCheckState(qt.Qt.Unchecked)

        def setOutput():
            self.uiform_bottom.textBrowser.clear()
            dat_dir = os.environ[params.homestr]
            if self.datdir == "":
                dat_dir = os.environ[params.homestr]
            elif self.datdir != "":
                dat_dir = self.datdir
            FO_dialog = qt.QFileDialog(self)
            file = FO_dialog.getSaveFileName(None,'Set the output file',
                                               dat_dir, "csv files(*.csv *.CSV)")

            self.uiform_bottom.textBrowser.append(os.path.abspath(file[0]))

        def reloadConditions():
            dat_dir = os.environ[params.homestr]
            if params.dir == "":
               pass
            else:
                dat_dir = params.dir
            FO_dialog = qt.QFileDialog(self)
            # file = FO_dialog.getOpenFileName(parent=None, caption='set output file name', filter='YAML File(*.yaml)',dir=dat_dir)
            file = FO_dialog.getOpenFileName(None, 'set output file name',
                                                            dat_dir, 'YAML File(*.yaml)')
            if os.path.isfile(file[0]):
                f = open(file[0],'r')
                Dict = yaml.load(f)
                f.close()
                self.uiTableView.doubleSpinBox.setValue(float(Dict['S02']))
                if self.uiTableView.lE_params.isEnabled() and self.uiTableView.lE_params.text() != '':
                    self.uiTableView.lE_params.clear()
                self.uiTableView.lE_params.insert(Dict['extra_param'])
                if self.uiTableView.lE_params.text() != '':
                    self.uiTableView.cB_use_anotherParams.setCheckState(QtCore.Qt.Checked)
                for key in ['dB_kmin','dB_kmax','dB_rmin','dB_rmax','dB_window_dk','dB_window_dr']:
                    getattr(self.uiform_ctrl,key).setValue(Dict[key])
                if Dict['plotSpace'] == 'k':
                    self.buttonGroup.buttons()[0].toggle()
                elif Dict['plotSpace'] == 'r':
                    self.buttonGroup.buttons()[1].toggle()
                elif Dict['plotSpace'] == 'q':
                    self.buttonGroup.buttons()[2].toggle()
                self.uiform_ctrl.cB_FitSpace.setCurrentIndex(['k','r','q'].index(Dict['fitSpace']))
                self.uiform_ctrl.cB_kweight.setCurrentIndex(['3','2','1','0'].index(Dict['kweight']))
                self.uiform_ctrl.cB_WindowType.setCurrentIndex(['kaiser','hanning','welch'].index(Dict['window']))
                array_path =[]
                for key in natsort.natsorted(Dict.keys()):
                    if 'path' in key:
                        array_path.append(key)
                for path_n in natsort.natsorted(array_path):
                    i = natsort.natsorted(array_path).index(path_n)
                    self.GroupCheckBox.buttons()[i].setCheckState(qt.Qt.Checked)
                    params.dict_FitConditions["PATH:"+str(i)]["FilePATH"] = Dict[path_n]['path_to_feff']
                    self.TableW.setItem(i,2,qt.QTableWidgetItem(Dict[array_path[i]]['discription']))
                    for term in ['N','dE','dR','ss','C3']:
                        num = 3+3*['N','dE','dR','ss','C3'].index(term)
                        self.TableW.setItem(i,num,qt.QTableWidgetItem(Dict[array_path[i]][term]['name']))
                        # self.TableW.item(i,num).setFont(self.font)
                        self.TableW.item(i,num).setForeground(qt.QColor('blue'))
                        comboBox = qt.QComboBox()
                        comboBox.addItems(['guess','set','def','guess_wRange'])
                        comboBox.setCurrentIndex(['guess','set','def','guess_wRange'].index(Dict[array_path[i]][term]['state']))
                        self.TableW.setCellWidget(i,num+1,comboBox)
                        self.TableW.setItem(i,num+2,qt.QTableWidgetItem(Dict[array_path[i]][term]['value']))

        def execSaveConditions():
            dat_dir = os.environ[params.homestr]
            if params.dir == "":
                pass
            else:
                dat_dir = params.dir
            FO_dialog = qt.QFileDialog(self)
            # file = FO_dialog.getSaveFileName(parent=None, caption='set output file name',
            #                                  filter='YAML File(*.yaml)',
            #                                  dir=dat_dir)
            file = FO_dialog.getSaveFileName(None, 'set output file name',
                                             dat_dir, 'YAML File(*.yaml)')
            if file[0] != '':
                self.SaveConditions(file[0])

        def calcDegreeFreedom():
            k_min = self.uiform_ctrl.dB_kmin.value()
            k_max = self.uiform_ctrl.dB_kmax.value()
            r_min = self.uiform_ctrl.dB_rmin.value()
            r_max = self.uiform_ctrl.dB_rmax.value()
            degreeF = 2*(k_max-k_min)*(r_max-r_min)/math.pi
            self.uiform_ctrl.lcdNumber.display(int(degreeF))

        def refresh_Plots():
            print (self.uiform_data.toolBox.currentIndex())
            if self.uiform_data.toolBox.currentIndex() == 0:
                plotData()
            elif self.uiform_data.toolBox.currentIndex() == 1:
                trendPlot_change_items()

        self.uiform_data.pB_Open.clicked.connect(openFiles)
        self.uiform_data.cB_ploteach.toggled.connect(changeSelectionMode)
        self.uiform_data.listWidget.itemClicked.connect(plotData)
        for name_rb in ['k','r','q']:
            getattr(self.uiform_ctrl,'rB_plot_'+name_rb).clicked.connect(plotData)
        self.uiform_ctrl.pB_refresh.clicked.connect(refresh_Plots)
        self.wSignal.connect(plotData)
        self.uiform_ctrl.cB_showParams.clicked.connect(show_hide_tableview)
        self.uiTableView.pushButton.clicked.connect(close_tableview)
        uiFEFF.pushButton.clicked.connect(close_dialog_f)
        self.uiTableView.cB_use_anotherParams.toggled.connect(self.uiTableView.lE_params.setEnabled)
        self.uiform_ctrl.pB_Fit.clicked.connect(self.DoAction)
        self.uiform_bottom.pushButton.clicked.connect(setOutput)
        self.uiTableView.pB_savecondtion.clicked.connect(execSaveConditions)
        self.uiTableView.pB_reload.clicked.connect(reloadConditions)
        # self.wS_trendplot.connect(plotFittingTrends)
        self.uiform_data.listWidget_2.itemClicked.connect(trendPlot_change_items)
        # self.uiform_data.listWidget_2.currentItemChanged.connect(trendPlot_change_items)
        self.uiform_data.show_TableView.toggled.connect(show_and_hide_tableView)
        self.uiform_data.toolBox.currentChanged.connect(self.CenterWidget.setCurrentIndex)
        self.wS_canvasdraw.connect(trendPlot_change_items)
        for dSB in [self.uiform_ctrl.dB_kmin,
                    self.uiform_ctrl.dB_kmax,
                    self.uiform_ctrl.dB_rmin,
                    self.uiform_ctrl.dB_rmax]:
            dSB.valueChanged.connect(calcDegreeFreedom)
        self.uiform_ctrl.dB_kmin.setValue(3.05)
        self.uiform_ctrl.dB_kmin.setValue(3.00)



    def timerEvent(self, e):
        if self.uiform_data.progressBar.value() < self.uiform_data.progressBar.maximum():
            xafsdat = larch_builtins._group(self.mylarch)
            item_index = self.array_index[self.uiform_data.progressBar.value()] - 1
            cb = self.uiform_data.listWidget.item(item_index)
            # cb = self.GroupCheckBox.buttons()[self.array_index[self.uiform_data.progressBar.value()] - 1]
            k, chi = LarchF.read_chi_file(self.datdir + '/' + cb.text().split(':')[1])
            xafsdat.k = k[:]
            xafsdat.chi = chi[:]
            dset = feffit_dataset(data=xafsdat, pathlist=self.pathlist,
                                  transform=self.FeffitTransform,_larch=self.mylarch)
            out = feffit(self.fitParams, dset, _larch=self.mylarch)
            line = feffit_report(out, _larch=self.mylarch)
            # for term in self.extra_params:
            #     if re.match("delta.*", term) != None:
            #         pass
            #     elif getattr(self.fitParams, term).vary == True:
            #         #t_array = str(getattr(self.fitParams, term).uvalue).split('+/-')
            #         self.Reserver.loc[cb.text(), term] = getattr(self.fitParams, term).value
            #         self.Reserver.loc[cb.text(), 'delta(' + term + ')'] = getattr(self.fitParams, term).stderr
            #     else:
            #         self.Reserver.loc[cb.text(), term] = str(getattr(self.fitParams, term).value)
            #         self.Reserver.loc[cb.text(), 'delta(' + term + ')'] = 0.000
            A_s02 = ['s0_2','delta(s0_2)']*self.uiTableView.checkBox.isChecked()
            for term in self.extra_params[:]+A_s02[:]+\
                    self.params_for_N[:]+self.params_for_dE[:]+\
                    self.params_for_dR[:]+self.params_for_ss[:]+self.params_for_C3[:]+['R-factor','log'][:]:
                # print (term)
                if re.match("delta.*", term) != None:
                    pass
                elif term == 'R-factor':
                    self.Reserver.loc[cb.text(), term] = float(re.search("r\-factor\s+\=\s+(\d+\.\d+)", line).group(1))
                elif term == 'log':
                    self.Reserver.loc[cb.text(), term] = line
                else:
                    if getattr(self.fitParams, term).vary == True:
                        if getattr(self.fitParams, term).uvalue is None:
                            if term in self.params_for_dR:
                                for i in range(0, 20):
                                    if term == self.TableW.item(i, 9).text():
                                        # print self.TableW.item(i,9).text()
                                        print(self.TableW.item(i, 2).text())
                                        self.Reserver.loc[cb.text(), 'Ro_'+str(i+1)+'+'+term] = getattr(self.fitParams, term).value +\
                                                                             float(re.search("\w+\=(\d+\.\d+)", self.TableW.item(i, 2).text()).group(1))
                                        self.Reserver.loc[cb.text(), term] = getattr(self.fitParams, term).value
                                        break
                                self.Reserver.loc[cb.text(), 'delta(' + term + ')'] = 0.000
                                self.Reserver.loc[cb.text(), 'delta(' + 'Ro_'+str(i+1)+'+'+term + ')'] = 0.000
                                # self.Reserver.loc[key,term] = str(getattr(self.fitParams,term).value)
                            else:
                                self.Reserver.loc[cb.text(), term] = getattr(self.fitParams, term).value
                                self.Reserver.loc[cb.text(), 'delta(' + term + ')'] = 0.000

                        else:
                            if term in self.params_for_dR:
                                # t_array = str(getattr(self.fitParams, term).uvalue).split('+/-')
                                # self.Reserver.loc[cb.text(), term] = float(t_array[0])
                                for i in range(0, 20):
                                    if term == self.TableW.item(i, 9).text():
                                        # print self.TableW.item(i,9).text()
                                        # print(self.TableW.item(i, 2).text())
                                        # self.Reserver.loc[cb.text(), term] = float(t_array[0]) + float(re.search("\w+\=(\d+\.\d+)", self.TableW.item(i, 2).text()).group(1))
                                        self.Reserver.loc[cb.text(), 'Ro_' + str(i+1) + '+' + term] = getattr(self.fitParams, term).value +\
                                                                                                    float(re.search("\w+\=(\d+\.\d+)", self.TableW.item(i, 2).text()).group(1))
                                        self.Reserver.loc[cb.text(), term] = getattr(self.fitParams, term).value
                                        break
                                    else:
                                        pass
                                self.Reserver.loc[cb.text(), 'delta(' + term + ')'] = getattr(self.fitParams, term).stderr
                                self.Reserver.loc[cb.text(), 'delta(' + 'Ro_' + str(i+1) + '+' + term + ')'] = getattr(self.fitParams, term).stderr
                            else:
                                # print(str(getattr(self.fitParams, term).uvalue))
                                # t_array = str(getattr(self.fitParams, term).uvalue).split('+/-')
                                # if 'e' in str(getattr(self.fitParams, term).uvalue):
                                #     t_array0 = str(getattr(self.fitParams, term).uvalue).replace('(','' ).split(')')
                                #     t_array = [t_array0.split('+/-')[0] + t_array0[1],
                                #                t_array0.split('+/-')[1] + t_array0[1]]

                                self.Reserver.loc[cb.text(), term] = getattr(self.fitParams, term).value
                                self.Reserver.loc[cb.text(), 'delta(' + term + ')'] = getattr(self.fitParams, term).stderr
                    elif getattr(self.fitParams, term).vary == False:
                        if getattr(self.fitParams, term).expr != None:
                            # print ('constraint:'+term +': '+str(getattr(self.fitParams, term).value))
                            # print('constraint:' + term + ': ' + str(getattr(self.fitParams, term).stderr))
                            # str_eqn = getattr(self.fitParams, term).expr
                            # for nval in self.extra_params[:] + self.params_for_N[:] + self.params_for_dE[:] + \
                            #             self.params_for_dR[:] + self.params_for_ss[:] + self.params_for_C3[:]:
                            #     if not "delta" in nval and getattr(self.fitParams, nval).expr == None:
                            #         if getattr(self.fitParams, nval).uvalue is None:
                            #             str_eqn = str_eqn.replace(nval, "self.fitParams." + nval + '.value')
                            #         else:
                            #             str_eqn = str_eqn.replace(nval, "self.fitParams." + nval + '.uvalue')

                            if term in self.params_for_dR:
                                # t_array = str(getattr(self.fitParams,term).uvalue).split('+/-')
                                # self.Reserver.loc[key,term] = t_array[0]
                                self.Reserver.loc[cb.text(), term] = getattr(self.fitParams, term).value
                                self.Reserver.loc[cb.text(), 'Ro_' + str(i + 1) + '+' + term] = getattr(self.fitParams, term).value + \
                                                                                                float(re.search("\w+\=(\d+\.\d+)",self.TableW.item(i,2).text()).group(1))
                                self.Reserver.loc[cb.text(), 'delta(' + term + ')'] = getattr(self.fitParams,term).stderr
                                self.Reserver.loc[cb.text(), 'delta(' + 'Ro_' + str(i + 1) + '+' + term + ')'] = getattr(self.fitParams,term).stderr
                                # for i in range(0, 20):
                                #     if term == self.TableW.item(i, 9).text():
                                #         # eval(str_eqn)
                                #         if '+/-' in str(eval(str_eqn)):
                                #             self.Reserver.loc[cb.text(), term] = float(
                                #                 re.search("\w+\=(\d+\.\d+)", self.TableW.item(i, 2).text()).group(1)) + \
                                #                                            float(str(eval(str_eqn)).split('+/-')[0])
                                #             self.Reserver.loc[cb.text(), 'delta(' + term + ')'] = float(str(eval(str_eqn)).split('+/-')[1])
                                #         else:
                                #             self.Reserver.loc[cb.text(), term] = float(
                                #                 re.search("\w+\=(\d+\.\d+)", self.TableW.item(i, 2).text()).group(1)) + \
                                #                                            float(str(eval(str_eqn)).split('+/-')[0])
                                #             self.Reserver.loc[cb.text(), 'delta(' + term + ')'] = 0.000
                                #         break
                                #     else:
                                #         pass
                            else:
                                self.Reserver.loc[cb.text(), term] = getattr(self.fitParams, term).value
                                self.Reserver.loc[cb.text(), 'delta(' + term + ')'] = getattr(self.fitParams, term).stderr
                                # print(str_eqn)
                                # print(eval(str_eqn))
                                # self.Reserver.loc[cb.text(), term] = float(str(eval(str_eqn)).split('+/-')[0])
                                # self.Reserver.loc[cb.text(), 'delta(' + term + ')'] = float(
                                #     str(eval(str_eqn)).split('+/-')[1])
                        else:
                            if term in self.params_for_dR:
                                t_array = str(getattr(self.fitParams, term).uvalue).split('+/-')
                                self.Reserver.loc[cb.text(), term] = float(t_array[0])
                                for i in range(0, 20):
                                    if term == self.TableW.item(i, 9).text():
                                        # print(re.search("\w+\=(\d+\.\d+)", self.TableW.item(i, 2).text()).group(1))
                                        self.Reserver.loc[cb.text(), 'Ro_' + str(i+1) + '+' + term] = float(re.search("\w+\=(\d+\.\d+)",self.TableW.item(i, 2).text()).group(1)) +\
                                                                                                    getattr(self.fitParams, term).value
                                        self.Reserver.loc[cb.text(), term] = getattr(self.fitParams, term).value
                                        self.Reserver.loc[cb.text(), 'delta(' + 'Ro_' + str(i+1) + '+' + term + ')'] = 0.000
                                        self.Reserver.loc[cb.text(), 'delta(' + term + ')'] = 0.000
                                        break
                                    else:
                                        pass
                            else:
                                self.Reserver.loc[cb.text(), term] = getattr(self.fitParams, term).value
                                self.Reserver.loc[cb.text(), 'delta(' + term + ')'] = 0.000
            # logfile = open(self.path_to_log + re.search("\d+\:(.+)\.\w+$", cb.text()).group(1) + '.log', 'w')
            # logfile.write(line)
            # # print type(line)
            # logfile.close()
            self.uiform_data.progressBar.setValue(self.uiform_data.progressBar.value() + 1)
            # self.hdf5.create_group("Hello")
            self.hdf5.create_group(cb.text())
            self.hdf5.create_dataset('/' + cb.text() + ':log', data=np.string_(line))
            self.hdf5.create_dataset('/' + cb.text() + '/chi_dat', data=np.array([dset.data.k, dset.data.chi]).T)
            self.hdf5.create_dataset('/' + cb.text() + '/chi_fit', data=np.array([dset.model.k, dset.model.chi]).T)
            self.hdf5.create_dataset('/' + cb.text() + '/chir_dat',
                                     data=np.array([dset.data.r, dset.data.chir_mag, dset.data.chir_im]).T)
            self.hdf5.create_dataset('/' + cb.text() + '/chir_fit',
                                     data=np.array([dset.model.r, dset.model.chir_mag, dset.model.chir_im]).T)
            if not self.uiform_data.cB_use_previous.isChecked():
                if self.uiTableView.cB_use_anotherParams.isChecked() and self.uiTableView.lE_params.text() != '':
                    tlist = self.uiTableView.lE_params.text().split(';')
                    for term in tlist:
                        t_array = term.split('=')
                        param_name = t_array[0].replace(" ", "").replace("'", "")
                        param_condition = t_array[1].replace(" ", "").replace('[', "").replace(']', "").replace('(',"").replace(')', "").split(',')
                        if len(param_condition) == 3:
                            p_min = param_condition[2].split(':')[0]
                            p_max = param_condition[2].split(':')[1]
                            if p_min != '' and p_max != '':
                                setattr(self.fitParams, param_name,
                                        larchfit.guess(float(param_condition[0]), min=float(p_min),
                                                       max=float(p_max)))
                            elif p_min != '' and p_max == '':
                                setattr(self.fitParams, param_name, larchfit.guess(float(param_condition[0]),
                                                                                   min=float(p_min)))
                            elif p_min == '' and p_max != '':
                                setattr(self.fitParams, param_name, larchfit.guess(float(param_condition[0]),
                                                                                   min=float(p_max)))
                            else:
                                setattr(self.fitParams, param_name, larchfit.guess(float(param_condition[0])))
                            print(getattr(self.fitParams, param_name).value)
                            # self.extra_params.append(param_name)
                            # self.extra_params.append('delta(' + param_name + ')')
                        else:
                            if param_condition[1].replace("'", "") == 'guess' and len(param_condition) == 2:
                                setattr(self.fitParams, param_name, larchfit.guess(float(param_condition[0])))
                                print(getattr(self.fitParams, param_name).value)
                                # self.extra_params.append(param_name)
                                # self.extra_params.append('delta(' + param_name + ')')
                            elif param_condition[1].replace("'", "") == 'set':
                                setattr(self.fitParams, param_name, larchfit.param(float(param_condition[0])))
                                # self.extra_params.append(param_name)
                for cB in self.GroupCheckBox.buttons():
                    if cB.isChecked():
                        index_ = self.GroupCheckBox.buttons().index(cB)
                        if self.uiTableView.checkBox.isChecked():
                            self.fitParams.s0_2 = larchfit.guess(self.uiTableView.doubleSpinBox.value())
                        Name_for_N = self.TableW.item(index_, 3).text()
                        # print Name_for_N
                        State_for_N = self.TableW.cellWidget(index_, 4)
                        # print State_for_N
                        Value_for_N = self.TableW.item(index_, 5).text()
                        # print Value_for_N
                        if State_for_N.currentText() == 'guess':
                            setattr(self.fitParams, Name_for_N, larchfit.guess(float(Value_for_N)))
                        elif State_for_N.currentText() == 'set':
                            setattr(self.fitParams, Name_for_N, larchfit.param(float(Value_for_N)))
                        elif State_for_N.currentText() == 'def':
                            setattr(self.fitParams, Name_for_N, larchfit.param(expr=Value_for_N))
                        Name_for_dE = self.TableW.item(index_, 6).text()
                        State_for_dE = self.TableW.cellWidget(index_, 7)
                        Value_for_dE = self.TableW.item(index_, 8).text()
                        if State_for_dE.currentText() == 'guess':
                            setattr(self.fitParams, Name_for_dE, larchfit.guess(float(Value_for_dE)))
                        elif State_for_dE.currentText() == 'set':
                            setattr(self.fitParams, Name_for_dE, larchfit.param(float(Value_for_dE)))
                        elif State_for_dE.currentText() == 'def':
                            setattr(self.fitParams, Name_for_dE, larchfit.param(expr=Value_for_dE))
                        Name_for_dR = self.TableW.item(index_, 9).text()
                        State_for_dR = self.TableW.cellWidget(index_, 10)
                        Value_for_dR = self.TableW.item(index_, 11).text()
                        if State_for_dR.currentText() == 'guess':
                            setattr(self.fitParams, Name_for_dR, larchfit.guess(float(Value_for_dR)))
                        elif State_for_dR.currentText() == 'set':
                            setattr(self.fitParams, Name_for_dR, larchfit.param(float(Value_for_dR)))
                        elif State_for_dR.currentText() == 'def':
                            setattr(self.fitParams, Name_for_dR, larchfit.param(expr=Value_for_dR))
                        Name_for_ss = self.TableW.item(index_, 12).text()
                        State_for_ss = self.TableW.cellWidget(index_, 13)
                        Value_for_ss = self.TableW.item(index_, 14).text()
                        if State_for_ss.currentText() == 'guess':
                            setattr(self.fitParams, Name_for_ss, larchfit.guess(float(Value_for_ss)))
                        elif State_for_ss.currentText() == 'set':
                            setattr(self.fitParams, Name_for_ss, larchfit.param(float(Value_for_ss)))
                        elif State_for_ss.currentText() == 'def':
                            setattr(self.fitParams, Name_for_ss, larchfit.param(expr=Value_for_ss))
                        Name_for_C3 = self.TableW.item(index_, 15).text()
                        State_for_C3 = self.TableW.cellWidget(index_, 16)
                        Value_for_C3 = self.TableW.item(index_, 17).text()
                        if State_for_C3.currentText() == 'guess':
                            setattr(self.fitParams, Name_for_C3, larchfit.guess(float(Value_for_C3)))
                        elif State_for_C3.currentText() == 'set':
                            setattr(self.fitParams, Name_for_C3, larchfit.param(float(Value_for_C3)))
                        elif State_for_C3.currentText() == 'def':
                            setattr(self.fitParams, Name_for_C3, larchfit.param(expr=Value_for_C3))
            else:
                pass
        else:
            self.timer.stop()
            # self.uiform_ctrl.pB_Fit.setText("Fit")
            # self.uiform_ctrl.pB_Fit.setStyleSheet("color: rgb(252, 1, 7);")
            # print ('Timer stopped')
            self.hdf5.close()
            # print (self.Reserver.keys())
            # print (self.paramNames[:-1])
            # print (self.extra_params[:])
            self.Reserver.loc[:, self.paramNames[:-1] + self.extra_params[:]].to_csv(
                path_or_buf=self.uiform_bottom.textBrowser.toPlainText(),
                header=self.paramNames[:-1] + self.extra_params[:], index_label='data', sep=' ')
            file = fileinput.FileInput(self.uiform_bottom.textBrowser.toPlainText(), inplace=True, backup='.bak')
            for line in file:
                print(line.rstrip().replace('"', ''))
            file.close()
            targets = [x for x in self.paramNames[:-2] if not re.match(r"delta.*", x)]
            for i in range(len(targets)):
                cb = qt.QListWidgetItem(targets[i])
                self.uiform_data.listWidget_2.addItem(cb)
            self.uiform_data.listWidget_2.setCurrentRow(0)

            model = qt.QStandardItemModel()
            horizontalLabels = self.Reserver.keys().tolist()
            horizontalLabels.remove('log')
            model.setHorizontalHeaderLabels(horizontalLabels)
            vertivalLabels = self.Reserver.index.tolist()
            model.setVerticalHeaderLabels(vertivalLabels)
            for i in range(len(vertivalLabels)):
                for j in range(len(horizontalLabels)):
                    Index = vertivalLabels[i]
                    Name = horizontalLabels[j]
                    model.setItem(i, j, qt.QStandardItem(str(self.Reserver.loc[Index,Name])))
            self.ui_resultTable.setModel(model)

            self.uiform_data.toolBox.setCurrentIndex(1)
            # self.wS_canvasdraw.emit()

            # self.wS_trendplot.emit()
            #self.wS_canvasdraw.emit()



    def SaveConditions(self, fname):
        Dict = {}
        Dict['S02'] = self.uiTableView.doubleSpinBox.value()
        Dict['extra_param'] = self.uiTableView.lE_params.text()
        # print(self.GroupCheckBox.buttons())
        for cB in self.GroupCheckBox.buttons():
            if cB.isChecked():
                index_ = self.GroupCheckBox.buttons().index(cB)
                Dict['path' + str(index_ + 1)] = {}
                Dict['path' + str(index_ + 1)]['discription'] = self.TableW.item(index_, 2).text()
                Dict['path' + str(index_ + 1)]['N'] = {'name': self.TableW.item(index_, 3).text(),
                                                       'state': self.TableW.cellWidget(index_, 4).currentText(),
                                                       'value': self.TableW.item(index_, 5).text()}
                Dict['path' + str(index_ + 1)]['dE'] = {'name': self.TableW.item(index_, 6).text(),
                                                        'state': self.TableW.cellWidget(index_, 7).currentText(),
                                                        'value': self.TableW.item(index_, 8).text()}
                Dict['path' + str(index_ + 1)]['dR'] = {'name': self.TableW.item(index_, 9).text(),
                                                        'state': self.TableW.cellWidget(index_, 10).currentText(),
                                                        'value': self.TableW.item(index_, 11).text()}
                Dict['path' + str(index_ + 1)]['ss'] = {'name': self.TableW.item(index_, 12).text(),
                                                        'state': self.TableW.cellWidget(index_, 13).currentText(),
                                                        'value': self.TableW.item(index_, 14).text()}
                Dict['path' + str(index_ + 1)]['C3'] = {'name': self.TableW.item(index_, 15).text(),
                                                        'state': self.TableW.cellWidget(index_, 16).currentText(),
                                                        'value': self.TableW.item(index_, 17).text()}
                Dict['path' + str(index_ + 1)]['path_to_feff'] = params.dict_FitConditions["PATH:"+str(index_)]["FilePATH"]
        #'dB_kmin', 'dB_kmax', 'dB_rmin', 'dB_rmax', 'dB_window_dk', 'dB_window_dr'
        Dict['dB_kmin'] = self.uiform_ctrl.dB_kmin.value()
        Dict['dB_kmax'] = self.uiform_ctrl.dB_kmax.value()
        Dict['dB_rmin'] = self.uiform_ctrl.dB_rmin.value()
        Dict['dB_rmax'] = self.uiform_ctrl.dB_rmax.value()
        Dict['plotSpace'] = self.buttonGroup.checkedButton().text()
        Dict['fitSpace'] = self.uiform_ctrl.cB_FitSpace.currentText()
        Dict['kweight'] = self.uiform_ctrl.cB_kweight.currentText()
        Dict['window'] = self.uiform_ctrl.cB_WindowType.currentText()
        Dict['dB_window_dk'] = self.uiform_ctrl.dB_window_dk.value()
        Dict['dB_window_dr'] = self.uiform_ctrl.dB_window_dr.value()
        print(yaml.safe_dump(Dict, default_flow_style=False))
        f = open(fname, 'w')
        f.write(yaml.safe_dump(Dict, default_flow_style=False))
        f.close()

    def DoAction(self):
        # print ("Hello")
        # self.uiform_data = Form_DataW()
        self.fig.delaxes(self.ax_r)
        self.fig.delaxes(self.ax)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("data")
        self.ax.set_ylabel("Param")
        self.ax_r = self.ax.twinx()
        self.ax_r.set_ylabel("R-factor")
        while self.uiform_data.listWidget_2.count():
            item = self.uiform_data.listWidget_2.takeItem(0)
            del item
        del self.mylarch
        self.mylarch = larch.Interpreter(with_plugins=False)
        if self.timer.isActive():
            self.timer.stop()
            self.uiform_ctrl.pB_Fit.setText("Fit")
            self.uiform_ctrl.pB_Fit.setStyleSheet("color: rgb(252, 1, 7);")
        else:
            A_checkstates = []
            # A_filePATH = []
            for i in range(len(self.GroupCheckBox.buttons())):
                if self.GroupCheckBox.buttons()[i].isChecked():
                    A_checkstates.append(params.dict_FitConditions['PATH:'+str(i)]["FilePATH"]!="")
                else:
                    A_checkstates.append(False)
            outfile = self.uiform_bottom.textBrowser.toPlainText()
            if any(A_checkstates) and self.uiform_data.listWidget.count() and outfile != "":
                # msgBox = qt.QMessageBox()
                # msgBox.setText("Goed!")
                # msgBox.exec_()
                self.fitParams = larch_builtins._group(self.mylarch)
                self.fitParams.s0_2 = larchfit.param(self.uiTableView.doubleSpinBox.value())
                self.extra_params = []
                if self.uiTableView.checkBox.isChecked():
                    self.fitParams.s0_2 = larchfit.guess(self.uiTableView.doubleSpinBox.value())
                    # self.extra_params.append('s0_2')
                    # self.extra_params.append('delta(' + 's0_2' + ')')
                if self.uiTableView.cB_use_anotherParams.isChecked() and self.uiTableView.lE_params.text() != '':
                    tlist = self.uiTableView.lE_params.text().split(';')
                    # txt = ''
                    # for term in string.split(';'):
                    #     txt += '(' + term +'),'
                    # or_dict = OrderedDict(eval('['+txt+']'))
                    for term in tlist:
                        t_array = term.split('=')
                        param_name = t_array[0].replace(" ", "")
                        param_condition = t_array[1][1:-1].replace(" ", "").replace('(', "").replace(')', "").split(',')
                        print(param_condition)
                        print(param_condition)
                        if len(param_condition) == 3:
                            p_min = param_condition[2].split(':')[0]
                            p_max = param_condition[2].split(':')[1]
                            if p_min != '' and p_max != '':
                                setattr(self.fitParams, param_name,
                                        larchfit.guess(float(param_condition[0]), min=float(p_min), max=float(p_max)))
                            elif p_min != '' and p_max == '':
                                setattr(self.fitParams, param_name, larchfit.guess(float(param_condition[0]),
                                                                                   min=float(p_min)))
                            elif p_min == '' and p_max != '':
                                setattr(self.fitParams, param_name, larchfit.guess(float(param_condition[0]),
                                                                                   min=float(p_max)))
                            else:
                                setattr(self.fitParams, param_name, larchfit.guess(float(param_condition[0])))
                            print(getattr(self.fitParams, param_name).value)
                            self.extra_params.append(param_name)
                            self.extra_params.append('delta(' + param_name + ')')
                        else:
                            if param_condition[1].replace("'", "") == 'guess' and len(param_condition) == 2:
                                setattr(self.fitParams, param_name, larchfit.guess(float(param_condition[0])))
                                print(getattr(self.fitParams, param_name).value)
                                self.extra_params.append(param_name)
                                self.extra_params.append('delta(' + param_name + ')')
                            elif param_condition[1].replace("'", "") == 'set':
                                setattr(self.fitParams, param_name, larchfit.param(float(param_condition[0])))
                                self.extra_params.append(param_name)
                                self.extra_params.append('delta(' + param_name + ')')
                # print(self.extra_params)
                self.pathlist = []
                self.paramNames = []
                self.params_for_N = []
                self.params_for_dE = []
                self.params_for_dR = []
                self.params_for_ss = []
                self.params_for_C3 = []
                for cB in self.GroupCheckBox.buttons():
                    if cB.isChecked():
                        index_ = self.GroupCheckBox.buttons().index(cB)
                        feffinp = params.dict_FitConditions["PATH:"+str(index_)]["FilePATH"]
                        path = feffpath(feffinp, _larch=self.mylarch)
                        # s02 = Name_for_N+'*'+'s0_2', e0 = Name_for_dE,sigma2 = Name_for_ss, deltar  = Name_for_dR,
                        Name_for_N = self.TableW.item(index_, 3).text()
                        self.params_for_N.append(Name_for_N)
                        # print Name_for_N
                        State_for_N = self.TableW.cellWidget(index_, 4)
                        # print State_for_N
                        Value_for_N = self.TableW.item(index_, 5).text()
                        # self.paramNames += [Name_for_N, 'delta(' + Name_for_N + ')']
                        # print Value_for_N
                        if State_for_N.currentText() == 'guess':
                            setattr(self.fitParams, Name_for_N, larchfit.guess(float(Value_for_N)))
                            self.paramNames += [Name_for_N, 'delta(' + Name_for_N + ')']
                        elif State_for_N.currentText() == 'set':
                            setattr(self.fitParams, Name_for_N, larchfit.param(float(Value_for_N)))
                            self.paramNames += [Name_for_N, 'delta(' + Name_for_N + ')']
                        elif State_for_N.currentText() == 'def':
                            setattr(self.fitParams, Name_for_N, larchfit.param(expr=Value_for_N))
                            self.paramNames += [Name_for_N, 'delta(' + Name_for_N + ')']
                        setattr(self.fitParams, 'degen_path_' + str(index_), path.degen)
                        # setattr(self.fitParams,'net_'+Name_for_N,larchfit.param(expr=Value_for_N+'*'+str(self.fit_dialog.doubleSpinBox.value())))
                        Name_for_dE = self.TableW.item(index_, 6).text()
                        self.params_for_dE.append(Name_for_dE)
                        State_for_dE = self.TableW.cellWidget(index_, 7)
                        Value_for_dE = self.TableW.item(index_, 8).text()
                        if State_for_dE.currentText() == 'guess':
                            setattr(self.fitParams, Name_for_dE, larchfit.guess(float(Value_for_dE)))
                            self.paramNames += [Name_for_dE, 'delta(' + Name_for_dE + ')']
                        elif State_for_dE.currentText() == 'set':
                            setattr(self.fitParams, Name_for_dE, larchfit.param(float(Value_for_dE)))
                            self.paramNames += [Name_for_dE, 'delta(' + Name_for_dE + ')']
                        elif State_for_dE.currentText() == 'def':
                            setattr(self.fitParams, Name_for_dE, larchfit.param(expr=Value_for_dE))
                            self.paramNames += [Name_for_dE, 'delta(' + Name_for_dE + ')']
                        Name_for_dR = self.TableW.item(index_, 9).text()
                        self.params_for_dR.append(Name_for_dR)
                        State_for_dR = self.TableW.cellWidget(index_, 10)
                        Value_for_dR = self.TableW.item(index_, 11).text()
                        if State_for_dR.currentText() == 'guess':
                            setattr(self.fitParams, Name_for_dR, larchfit.guess(float(Value_for_dR)))
                            self.paramNames += ['Ro_' + str(index_+1) + '+' + Name_for_dR,
                                                'delta(' + 'Ro_' + str(index_+1) + '+' + Name_for_dR + ')', Name_for_dR,
                                                'delta(' + Name_for_dR + ')']
                        elif State_for_dR.currentText() == 'set':
                            setattr(self.fitParams, Name_for_dR, larchfit.param(float(Value_for_dR)))
                            self.paramNames += ['Ro_' + str(index_+1) + '+' + Name_for_dR,
                                                'delta(' + 'Ro_' + str(index_+1) + '+' + Name_for_dR + ')', Name_for_dR,
                                                'delta(' + Name_for_dR + ')']
                        elif State_for_dR.currentText() == 'def':
                            setattr(self.fitParams, Name_for_dR, larchfit.param(expr=Value_for_dR))
                            self.paramNames += ['Ro_'+str(index_+1)+'+'+Name_for_dR,
                                                'delta(' + 'Ro_'+str(index_+1)+'+'+Name_for_dR + ')', Name_for_dR,
                                                'delta(' + Name_for_dR + ')']
                        Name_for_ss = self.TableW.item(index_, 12).text()
                        self.params_for_ss.append(Name_for_ss)
                        State_for_ss = self.TableW.cellWidget(index_, 13)
                        Value_for_ss = self.TableW.item(index_, 14).text()
                        if State_for_ss.currentText() == 'guess':
                            setattr(self.fitParams, Name_for_ss, larchfit.guess(float(Value_for_ss)))
                            self.paramNames += [Name_for_ss, 'delta(' + Name_for_ss + ')']
                        elif State_for_ss.currentText() == 'set':
                            setattr(self.fitParams, Name_for_ss, larchfit.param(float(Value_for_ss)))
                            self.paramNames += [Name_for_ss, 'delta(' + Name_for_ss + ')']
                        elif State_for_ss.currentText() == 'def':
                            setattr(self.fitParams, Name_for_ss, larchfit.param(expr=Value_for_ss))
                            self.paramNames += [Name_for_ss, 'delta(' + Name_for_ss + ')']
                        Name_for_C3 = self.TableW.item(index_, 15).text()
                        self.params_for_C3.append(Name_for_C3)
                        State_for_C3 = self.TableW.cellWidget(index_, 16)
                        Value_for_C3 = self.TableW.item(index_, 17).text()
                        if State_for_C3.currentText() == 'guess':
                            setattr(self.fitParams, Name_for_C3, larchfit.guess(float(Value_for_C3)))
                            self.paramNames += [Name_for_C3, 'delta(' + Name_for_C3 + ')']
                        elif State_for_C3.currentText() == 'set':
                            setattr(self.fitParams, Name_for_C3, larchfit.param(float(Value_for_C3)))
                            self.paramNames += [Name_for_C3, 'delta(' + Name_for_C3 + ')']
                        elif State_for_C3.currentText() == 'def':
                            setattr(self.fitParams, Name_for_C3, larchfit.param(expr=Value_for_C3))
                            self.paramNames += [Name_for_C3, 'delta(' + Name_for_C3 + ')']
                        path.s02 = Name_for_N + '*' + 's0_2' + '/' + 'degen_path_' + str(index_)
                        path.e0 = Name_for_dE
                        path.sigma2 = Name_for_ss
                        path.deltar = Name_for_dR
                        path.third = Name_for_C3
                        if self.uiTableView.cB_use_anotherParams.isChecked():
                            condition_dict = {Name_for_N: 'path.s02', Name_for_dE: 'path.e0',
                                              Name_for_dR: 'path.deltar', Name_for_ss: 'path.sigma2',
                                              Name_for_C3: 'path.third'}
                            for term in condition_dict.keys():
                                if getattr(self.fitParams, term).expr != None:
                                    for extParam in self.extra_params:
                                        if extParam in getattr(self.fitParams, term).expr:
                                            if term == Name_for_N:
                                                path.s02 = '(' + getattr(self.fitParams,
                                                                         term).expr + ')' + '*' + 's0_2' + '/' + 'degen_path_' + str(
                                                    index_)
                                            elif term == Name_for_dE:
                                                path.e0 = getattr(self.fitParams, term).expr
                                            elif term == Name_for_dR:
                                                path.deltar = getattr(self.fitParams, term).expr
                                            elif term == Name_for_ss:
                                                path.sigma2 = getattr(self.fitParams, term).expr
                                            elif term == Name_for_C3:
                                                path.third = getattr(self.fitParams, term).expr
                        self.pathlist.append(path)
                if self.uiTableView.checkBox.isChecked():
                    self.paramNames.insert(0, 's0_2')
                    self.paramNames.insert(1, 'delta(s0_2)')
                self.paramNames += ['R-factor', 'log']
                self.Reserver = pd.DataFrame(columns=self.paramNames + self.extra_params)
                array_index = []
                if re.search('ALL', self.uiform_data.lineEdit.text()):
                    array_index = range(1, self.uiform_data.listWidget.count() + 1)
                elif self.uiform_data.lineEdit.text() == re.match(r"(\d+\-?\d*\,?\s*)+", self.uiform_data.text()).group(0):
                    array = self.uiform_data.text().split(',')
                    for term in array:
                        if re.search('\d+\-\d+', term):
                            t_array = term.split('-')
                            array_index += range(int(t_array[0]), int(t_array[1]) + 1)[:]
                        else:
                            array_index.append(int(term))
                self.array_index = list(set(array_index))
                print(self.array_index)
                self.uiform_data.progressBar.setRange(0, len(self.array_index))
                self.FeffitTransform = feffit_transform(fitspace=self.uiform_ctrl.cB_FitSpace.currentText(),
                                                        kmin=self.uiform_ctrl.dB_kmin.value(),
                                                        kmax=self.uiform_ctrl.dB_kmax.value(),
                                                        kw=float(self.uiform_ctrl.cB_kweight.currentText()),
                                                        dk=self.uiform_ctrl.dB_window_dk.value(),
                                                        window=self.uiform_ctrl.cB_WindowType.currentText(),
                                                        rmin=self.uiform_ctrl.dB_rmin.value(),
                                                        rmax=self.uiform_ctrl.dB_rmax.value(),
                                                        _larch=self.mylarch,
                                                        dr=self.uiform_ctrl.dB_window_dr.value())
                self.ext = re.search("\.\w+$", self.uiform_bottom.textBrowser.toPlainText()).group(0)
                if not os.path.isdir(os.path.dirname(self.uiform_bottom.textBrowser.toPlainText()) + '/Log'):
                    os.mkdir(os.path.dirname(self.uiform_bottom.textBrowser.toPlainText()) + '/Log')
                self.path_to_log = os.path.dirname(self.uiform_bottom.textBrowser.toPlainText()) + '/Log/'
                if os.path.isfile(
                        self.path_to_log + 'result_' + os.path.basename(self.uiform_bottom.textBrowser.toPlainText()).replace(self.ext, '.h5')):
                    os.rename(self.path_to_log + 'result_' + os.path.basename(self.uiform_bottom.textBrowser.toPlainText()).replace(self.ext, '.h5'),
                              self.path_to_log + 'result_' + os.path.basename(self.uiform_bottom.textBrowser.toPlainText()).replace(self.ext, '.h5~'))
                self.hdf5 = h5py.File(self.path_to_log + 'result_' + os.path.basename(self.uiform_bottom.textBrowser.toPlainText()).replace(self.ext,'.h5'),'a')
                # self.hdf5.create_group("Hello")
                self.SaveConditions(self.path_to_log + os.path.basename(self.uiform_bottom.textBrowser.toPlainText()).replace(self.ext, '.yaml'))
                self.params_guess = []
                self.params_set = []
                self.params_def = []

                for term in self.params_for_N[:] + self.params_for_dE[:] +\
                            self.params_for_dR[:] + self.params_for_ss[:] + self.extra_params[:]:
                    if re.match("delta.*", term) != None:
                        pass
                    elif getattr(self.fitParams, term).expr == None:
                        if getattr(self.fitParams, term).vary == True:
                            self.params_guess.append(term)
                        else:
                            self.params_set.append(term)
                    else:
                        self.params_def.append(term)
                self.uiform_data.progressBar.setValue(0)
                if len(self.params_guess) > self.uiform_ctrl.lcdNumber.value():
                    msgBox = qt.QMessageBox()
                    msgBox.setText("Error: the number of free parameters exceeds the maximum allowed number.")
                    msgBox.exec_()
                else:
                    self.timer.start(1, self)
                    # self.uiform_ctrl.pB_Fit.setText("Stop")
                    # self.uiform_ctrl.pB_Fit.setStyleSheet("color: rgb(255, 0, 0);")
            elif not any(A_checkstates) and self.uiform_data.listWidget.count() and outfile != "":
                msgBox = qt.QMessageBox()
                msgBox.setText("Error: you did not set any FEFF paths.")
                msgBox.exec_()
            elif any(A_checkstates) and not self.uiform_data.listWidget.count() and outfile != "":
                msgBox = qt.QMessageBox()
                msgBox.setText("Error: you did not select any data files.")
                msgBox.exec_()
            elif not any(A_checkstates) and not self.uiform_data.listWidget.count() and outfile != "":
                msgBox = qt.QMessageBox()
                msgBox.setText("Error: you did not anything.")
                msgBox.exec_()
            elif any(A_checkstates) and self.uiform_data.listWidget.count() and outfile == "":
                msgBox = qt.QMessageBox()
                msgBox.setText("Error: you did not set the output file.")
                msgBox.exec_()



if __name__ == '__main__':

    import sys
    app = qt.QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
