# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 14:20:47 2022

@author: Hongseok Oh
"""

# For Qt layout (GUI)
from PyQt5.QtWidgets import (QLineEdit, QComboBox, QTextEdit, QGroupBox, QGridLayout)
from PyQt5.QtWidgets import (QPushButton, QRadioButton, QLabel, QWidget, QFileDialog)
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QSizePolicy, QFrame, QCheckBox)
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import QTimer, QTime, QDate, Qt
from PyQt5.QtCore import QObject
# pyqtSignal, 
from PyQt5.QtGui import QFont, QColor
import time
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
import os
import json

sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)


# For dialog
import tkinter as tk # for the dialog of opening file
from tkinter import filedialog # for the dialog of opening file
import os
from datetime import datetime

# For VISA control
import pyvisa as visa
import numpy as np

class ConnectionManagementUnit(QObject):
    def __init__(self, title = "SMU 0 Connection Setup"):
        super().__init__()
        self.rm = visa.ResourceManager()   

        self.groupbox = QGroupBox(title)
        self.groupbox.setCheckable(True)
        self.groupbox.setChecked(True)  # default checked
        self.vbox = QVBoxLayout()
        self.hbox_connection = QHBoxLayout()
        self.hbox_info = QHBoxLayout()
        self.hbox_config_01 = QHBoxLayout()
        self.hbox_config_02 = QHBoxLayout()
        self.hbox_config_03 = QHBoxLayout()
        self.hbox_config_04 = QHBoxLayout()
        self.hbox_config_05 = QHBoxLayout()

        # Connection UI
        self.lbl_test = QLabel("Port: ")
        self.cb = QComboBox()
        self.btn = QPushButton('Check')

        self.cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.hbox_connection.addWidget(self.lbl_test)
        self.hbox_connection.addWidget(self.cb)
        self.hbox_connection.addWidget(self.btn)

        # Info UI
        self.lbl_info_title = QLabel("Status:")
        self.lbl_info = QLabel("-")
        self.lbl_info.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.hbox_info.addWidget(self.lbl_info_title)
        self.hbox_info.addWidget(self.lbl_info)

        # Config 01: Autozero, NPLC
        self.lbl_autozero = QLabel('Auto Zero:')
        self.cb_autozero = QComboBox()
        self.cb_autozero.addItems(['Yes', 'No'])

        self.lbl_nplc = QLabel('NPLC')
        self.cb_nplc = QComboBox()
        self.cb_nplc.addItems(['1', '0.1', '0.01'])

        self.hbox_config_01.addWidget(self.lbl_autozero)
        self.hbox_config_01.addWidget(self.cb_autozero)
        self.hbox_config_01.addWidget(self.lbl_nplc)
        self.hbox_config_01.addWidget(self.cb_nplc)
        self.hbox_config_01.addStretch()

        # Config 02: V source, 
        self.lbl_vsourrang = QLabel('Voltage Source Range (V)')
        self.cb_vsourrang = QComboBox()
        self.cb_vsourrang.addItems(['AUTO', '200', '20', '2'])

        self.hbox_config_02.addWidget(self.lbl_vsourrang)
        self.hbox_config_02.addWidget(self.cb_vsourrang)
        self.hbox_config_02.addStretch()

        # Config 03 :I sense, 
        self.lbl_isensrang = QLabel('Current Sense Range (A)')
        self.cb_isensrang = QComboBox()
        self.cb_isensrang.addItems(['AUTO ON', '100E-3', '10E-3', '1E-3', '100E-6', '10E-6', '1E-6'])

        self.hbox_config_03.addWidget(self.lbl_isensrang)
        self.hbox_config_03.addWidget(self.cb_isensrang)
        self.hbox_config_03.addStretch()

        # Config 03: I protect range
        self.lbl_iprotrang = QLabel('Current Compliance (A)')
        self.cb_iprotrang = QComboBox()
        self.cb_iprotrang.addItems(['100E-3', '10E-3', '1E-3', '100E-6', '10E-6', '1E-6'])
        self.hbox_config_04.addWidget(self.lbl_iprotrang)
        self.hbox_config_04.addWidget(self.cb_iprotrang)
        self.hbox_config_04.addStretch()

        # Config 05: Trigger delay, Source delay
        self.lbl_trg_delay = QLabel('Trigger delay (s)')
        self.le_trg_delay = QLineEdit('0.0')

        self.lbl_sour_delay = QLabel('Source delay (s)')
        self.le_sour_delay = QLineEdit('0.0')

        self.hbox_config_05.addWidget(self.lbl_trg_delay)
        self.hbox_config_05.addWidget(self.le_trg_delay)
        self.hbox_config_05.addWidget(self.lbl_sour_delay)
        self.hbox_config_05.addWidget(self.le_sour_delay)
        self.hbox_config_05.addStretch()

        # Config 06: Manual initialization
        self.btn_init_smu = QPushButton("Initialize")
        self.hbox_config_06 = QHBoxLayout()
        self.hbox_config_06.addStretch()
        self.hbox_config_06.addWidget(self.btn_init_smu)

        # Assemble all layouts in the vertical layout
        self.vbox.addLayout(self.hbox_connection)
        self.vbox.addLayout(self.hbox_info)
        self.vbox.addLayout(self.hbox_config_01)
        self.vbox.addLayout(self.hbox_config_02)
        self.vbox.addLayout(self.hbox_config_03)
        self.vbox.addLayout(self.hbox_config_04)
        self.vbox.addLayout(self.hbox_config_05)
        self.vbox.addLayout(self.hbox_config_06)

        self.groupbox.setLayout(self.vbox)

        # Internal variables
        self.SMU_parameters = {
            'smu' : None,
            'in_use' : True,
            'type_source' : "voltage",
            'autozero': None,
            'nplc': None,
            'vsourrang': None,
            'isensrang': None,
            'iprotrang': None,
            'isourrang' : None,
            'vsensrang' : None,
            'vprotrang' : None,
            'trg_delay': None,
            'sour_delay': None            
        }
        print('Internal variables ready')

        self.connection_refresh()
        # When 'Check' pushbutton is clicked
        self.btn.clicked.connect(self.check_connection)
        self.btn_init_smu.clicked.connect(self.initialize_SMU)
        # Auto update the internal variables
        self.groupbox.toggled.connect(self.update_SMU_parameters)
        self.cb_autozero.currentIndexChanged.connect(self.update_SMU_parameters)
        self.cb_nplc.currentIndexChanged.connect(self.update_SMU_parameters)
        self.cb_vsourrang.currentIndexChanged.connect(self.update_SMU_parameters)
        self.cb_isensrang.currentIndexChanged.connect(self.update_SMU_parameters)
        self.cb_iprotrang.currentIndexChanged.connect(self.update_SMU_parameters)
        self.le_trg_delay.textChanged.connect(self.update_SMU_parameters)
        self.le_sour_delay.textChanged.connect(self.update_SMU_parameters)
        # When the checkbox is toggled to define use the SMU or not
        self.groupbox.toggled.connect(self.set_enabled_state)
        
        self.update_SMU_parameters
        print('Connection complete')

    def is_enabled(self):
        return self.groupbox.isChecked()

    def set_enabled_state(self, enabled):
        # Disable all sub-layout widgets
        for layout in [
            self.hbox_connection, self.hbox_info,
            self.hbox_config_01, self.hbox_config_02,
            self.hbox_config_03, self.hbox_config_04,
            self.hbox_config_05
        ]:
            for i in range(layout.count()):
                item = layout.itemAt(i).widget()
                if item is not None:
                    item.setEnabled(enabled)
    
    def connection_refresh(self): #""" Refresh the connection with SMUs (Find available GPIB signals)"""
        # Clear the current items
        self.conn_list = self.rm.list_resources()
        self.cb.clear()
        self.cb.addItems(self.conn_list)   
        self.update_status('-')
        # Add items available
        # Leave a log
        #self.update_log('Find available connections...\n')

    def update_SMU_parameters(self):
        self.SMU_parameters['in_use'] = self.groupbox.isChecked()
        self.SMU_parameters['autozero'] = self.cb_autozero.currentText()
        self.SMU_parameters['nplc'] = float(self.cb_nplc.currentText())
        self.SMU_parameters['vsourrang'] = self.cb_vsourrang.currentText()
        self.SMU_parameters['isensrang'] = self.cb_isensrang.currentText()
        self.SMU_parameters['iprotrang'] = self.cb_iprotrang.currentText()
        self.SMU_parameters['trg_delay'] = float(self.le_trg_delay.text())
        self.SMU_parameters['sour_delay'] = float(self.le_sour_delay.text())
        self.print_SMU_parameters()
    
    def print_SMU_parameters(self):
        print("=== SMU Parameters ===")
        for key, value in self.SMU_parameters.items():
            print(f"{key}: {value}")

    def update_status(self, text):
        self.lbl_info.setText(text)

    def check_connection(self):
        selected_resource = self.cb.currentText()
        if not selected_resource:
            print('No device found')
            self.update_status('No device found')
            return
        try:
            smu = self.rm.open_resource(selected_resource)
            text_update = smu.query("*IDN?")
            self.SMU_parameters['smu'] = smu
            self.update_status(text_update.strip()[:50])
            self.update_SMU_parameters
            print("Connected:", text_update)
        except Exception as e:
            self.SMU_parameters['smu'] = None
            self.update_status('No device found')
            print("Connection failed:", str(e))

    def save_settings(self, filepath):
        dirpath = os.path.dirname(filepath)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        settings = {
            'in_use': self.groupbox.isChecked(),
            'autozero': self.cb_autozero.currentText(),
            'nplc': self.cb_nplc.currentText(),
            'vsourrang': self.cb_vsourrang.currentText(),
            'isensrang': self.cb_isensrang.currentText(),
            'iprotrang': self.cb_iprotrang.currentText(),
            'trg_delay': self.le_trg_delay.text(),
            'sour_delay': self.le_sour_delay.text()
        }
        try:
            with open(filepath, 'w') as f:
                json.dump(settings, f, indent=4)
            print(f"[INFO] Settings saved to {filepath}")
        except Exception as e:
            print(f"[ERROR] Could not save settings to {filepath}: {e}")

    def load_settings(self, filepath):
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            print(f"[WARN] Settings file '{filepath}' does not exist or is empty.")
            return
        try:
            with open(filepath, 'r') as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print(f"[ERROR] Failed to decode JSON from '{filepath}'. Skipping load.")
            return
        
        print(f"[INFO] Settings loaded")
        self.groupbox.setChecked(settings.get('in_use', True))
        self.cb_autozero.setCurrentText(settings.get('autozero', 'Yes'))
        self.cb_nplc.setCurrentText(settings.get('nplc', '1'))
        self.cb_vsourrang.setCurrentText(settings.get('vsourrang', 'AUTO'))
        self.cb_isensrang.setCurrentText(settings.get('isensrang', 'AUTO ON'))
        self.cb_iprotrang.setCurrentText(settings.get('iprotrang', '1E-3'))
        self.le_trg_delay.setText(settings.get('trg_delay', '0.0'))
        self.le_sour_delay.setText(settings.get('sour_delay', '0.0'))

    def initialize_SMU(self):
        self.update_SMU_parameters()
        smu = self.SMU_parameters.get('smu')
        if smu is None:
            print("SMU not connected.")
            return

        try:
            smu.write("*RST")
            smu.write(":SOUR:FUNC VOLT")
            smu.write(":SOUR:VOLT:MODE FIXED")

            # Voltage source range
            vsour_range = self.SMU_parameters['vsourrang']
            if vsour_range != 'AUTO':
                smu.write(f":SOUR:VOLT:RANG {vsour_range}")
            else:
                smu.write(":SOUR:VOLT:RANG:AUTO ON")

            # Current sense range
            isens_range = self.SMU_parameters['isensrang']
            if isens_range != 'AUTO ON':
                smu.write(f":SENS:CURR:RANG {isens_range}")
            else:
                smu.write(":SENS:CURR:RANG:AUTO ON")

            # Compliance limit
            smu.write(f":SENS:CURR:PROT {self.SMU_parameters['iprotrang']}")
            smu.write(f":TRIG:DEL {self.SMU_parameters['trg_delay']}")
            smu.write(f":SOUR:DEL {self.SMU_parameters['sour_delay']}")
            smu.write(f":SENS:CURR:NPLC {self.SMU_parameters['nplc']}")

            # Autozero setting
            autozero_cmd = "ON" if self.SMU_parameters['autozero'] == 'Yes' else "OFF"
            smu.write(f":SYST:AZER:STAT {autozero_cmd}")

            print(f"SMU {smu} initialized.")

        except Exception as e:
            print("SMU initialization failed:", str(e))


class CreateConnectionControlBox:
    def __init__(self, title='Connection Control Box', num_equipment=3):
        self.groupbox = QGroupBox(title)
        self.vbox = QVBoxLayout()
        self.num_equipment = num_equipment
        self.unit_list = []
        
        for i in range (num_equipment):
            self.unit_list.append(ConnectionManagementUnit(title = f'SMU {i} Connection Setup'))        
            self.vbox.addWidget(self.unit_list[i].groupbox)
        self.groupbox.setLayout(self.vbox)

    def makeFunc(self, x):
        # return (lambda: self.check_connection(x)) #Ref: https://stackoverflow.com/questions/19837486/lambda-in-a-loop
        print(f'makeFunc: {x}')

    def get_SMU_list(self):        
        self.smu_list = []
        for i in range (self.num_equipment):
            self.smu_list.append(self.unit_list[i].SMU_parameters)
            print(f'SMU{i}: {self.smu_list[i]}')            
        return(self.smu_list)  

    def initialize_SMU(self):
        print('Initialize SMU called')
        for unit in self.unit_list:
            unit.initialize_SMU()
        

class CreateParameterSettingsBox:
    def __init__(self, title = 'Parameter Settings Box', num_parameter = 5):
        self.groupbox = QGroupBox(title)
        self.vbox = QVBoxLayout()
        self.grid = QGridLayout()
                   
        self.lbl_param_list = [None]*num_parameter
        self.le_list = [None]*num_parameter
        self.lbl_unit_list = [None]*num_parameter
        self.hbox_list = [None]*num_parameter
        
        for i in range (num_parameter):
            self.lbl_param_list[i] = QLabel('%s%d%s' %('Parameter',i,':'))
            self.le_list[i] = QLineEdit('0')
            self.le_list[i].setAlignment(QtCore.Qt.AlignRight)
            self.lbl_unit_list[i] = QLabel('%s%d' %('Unit',i))
            
            self.hbox_list[i] = QHBoxLayout()
            self.hbox_list[i].addWidget(self.lbl_param_list[i])
            self.hbox_list[i].addWidget(self.le_list[i])
            self.hbox_list[i].addWidget(self.lbl_unit_list[i])
            self.vbox.addLayout(self.hbox_list[i])
            
        self.groupbox.setLayout(self.vbox)
        
    def set_item(self, index, name, value, unit):
        self.lbl_param_list[index].setText(name)
        self.le_list[index].setText(value)
        self.lbl_unit_list[index].setText(unit)
        
    def get_value(self, index):
        return(self.le_list[index].text())
    
    def show_only_name(self, index):
        self.hbox_list[index].removeWidget(self.le_list[index])
        self.hbox_list[index].removeWidget(self.lbl_unit_list[index])
        self.le_list[index].setHidden(True)
        self.lbl_unit_list[index].setHidden(True)
        
class CreateParameterSettingsBoxWithToggle:
    def __init__(self, title = 'Parameter Settings Box', num_parameter = 5, num_toggle = 2, **kwargs):
        self.groupbox = QGroupBox(title)
        self.rbtn_layout = kwargs.get("layout")
        if self.rbtn_layout == "vertical":
            self.hbox_toggle = QVBoxLayout()
        else:
            self.hbox_toggle = QHBoxLayout()

        self.vbox = QVBoxLayout()        
        
        self.rbtn_list = [None]*num_toggle
        for i in range (num_toggle):
            self.rbtn_list[i] = QRadioButton('%s%d' %('Item', i))
            self.rbtn_list[i].setChecked(False)
            self.hbox_toggle.addWidget(self.rbtn_list[i])
            
                    
        self.lbl_param_list = [None]*num_parameter
        self.le_list = [None]*num_parameter
        self.lbl_unit_list = [None]*num_parameter
        self.hbox_list = [None]*num_parameter
        
        self.vbox.addLayout(self.hbox_toggle)
        
        for i in range (num_parameter):
            self.lbl_param_list[i] = QLabel('%s%d%s' %('Parameter',i,':'))
            self.le_list[i] = QLineEdit('0')
            self.le_list[i].setAlignment(QtCore.Qt.AlignRight)
            self.lbl_unit_list[i] = QLabel('%s%d' %('Unit',i))
            
            self.hbox_list[i] = QHBoxLayout()
            self.hbox_list[i].addWidget(self.lbl_param_list[i])
            self.hbox_list[i].addWidget(self.le_list[i])
            self.hbox_list[i].addWidget(self.lbl_unit_list[i])
            
            self.vbox.addLayout(self.hbox_list[i])
            
        self.groupbox.setLayout(self.vbox)
        
        
        
    def set_item(self, index, name, value, unit):
        self.lbl_param_list[index].setText(name)
        self.le_list[index].setText(value)
        self.lbl_unit_list[index].setText(unit)
        
    def set_toggle_item(self, index, name, checked):
        self.rbtn_list[index].setText(name)
        self.rbtn_list[index].setChecked(checked)
        
    def get_value(self, index):
        return(self.le_list[index].text())
    
    def show_only_name(self, index):
        self.hbox_list[index].removeWidget(self.le_list[index])
        self.hbox_list[index].removeWidget(self.lbl_unit_list[index])
        self.le_list[index].setHidden(True)
        self.lbl_unit_list[index].setHidden(True)
               
        
class CreateGraphBox():
    def __init__(self, title = 'Graph plots', num_graph = 2, placement_orientation = 'horizontal'):
        # Setup the plot screen
        self.groupbox = QGroupBox(title)
        self.vbox_all = QVBoxLayout()
        if placement_orientation == 'horizontal':
            self.hbox_plot = QHBoxLayout()
        else:
            self.hbox_plot = QVBoxLayout()
        self.canvas = []
        self.plot = []
        self.subplot_container = []
        self.num_graph = num_graph
        for i in range (num_graph):
            self.canvas.append(pg.GraphicsLayoutWidget())
            self.plot.append(self.canvas[i].addPlot())
            self.hbox_plot.addWidget(self.canvas[i])
                            
            self.plot[i].setTitle("%s%d" %('Graph',i), color='k', bold = True)
            self.plot[i].setLabel('left', "%s%d%s" %('Y-Axis',i,'(Unit)'))
            self.plot[i].setLabel('bottom', "%s%d%s" %('X-Axis',i,'(Unit)'))
            
            self.subplot_container.append([])
        
        # Setup background color and axis
        # Set grey color
        color_grey = [230,230,230]
        for i in range (num_graph):     
            self.canvas[i].setBackground(color_grey)
            self.plot[i].getAxis('left').setTextPen('k')
            self.plot[i].getAxis('right').setTextPen('k')
            self.plot[i].getAxis('bottom').setTextPen('k')
            self.plot[i].getAxis('top').setTextPen('k')
            self.plot[i].showAxis('right')
            self.plot[i].showAxis('top')
        
        self.hbox_display_options = QHBoxLayout()
        self.ckbx_flip_yaxis = QCheckBox('Flip y-axis for all plots')
        self.hbox_display_options.addWidget(self.ckbx_flip_yaxis)
        self.hbox_display_options.addSpacing(1)
        self.vbox_all.addLayout(self.hbox_plot)
        self.vbox_all.addLayout(self.hbox_display_options)
        self.groupbox.setLayout(self.vbox_all)         
        
    def update_plot(self, index, x_data, y_data, graph_num = 9999):
        if graph_num == 9999:
            if self.ckbx_flip_yaxis.isChecked():
                print("y-axis flipped plot")
                self.subplot_container[index][-1].setData(x_data, -1*y_data)
            else:
                self.subplot_container[index][-1].setData(x_data, y_data)
        else:
            if self.ckbx_flip_yaxis.isChecked():
                print("y-axis flipped plot")
                self.subplot_container[index][-(1+graph_num)].setData(x_data, -1*y_data)
            else:
                self.subplot_container[index][-1].setData(x_data, y_data)
    def clear_plot(self, index):
        self.plot[index].clear()
        
    def addnew_plot(self, index, **kwargs):
        self.graph_type = kwargs.get("type")
        if self.graph_type == "symbol":
            self.subplot_container[index].append(self.plot[index].plot(pen = 'b', symbol='o', symbolPen='r'))
            if len(self.subplot_container[index])>1:
                self.subplot_container[index][-2].setPen('k')
                self.subplot_container[index][-2].setSymbolBrush(QColor(10, 130, 3))
                
        elif self.graph_type == "symbol_only":
            self.subplot_container[index].append(self.plot[index].plot(pen = None, symbol='o', symbolPen='r'))
            if len(self.subplot_container[index])>1:
                self.subplot_container[index][-2].setPen('k')
                self.subplot_container[index][-2].setSymbolBrush(QColor(10, 130, 3))
            
        else:
            self.subplot_container[index].append(self.plot[index].plot(pen = pg.mkPen('r', width = 3)))
            if len(self.subplot_container[index])>1:
                self.subplot_container[index][-2].setPen('b')
        
    def reset_plot(self):
        for i in range(self.num_graph):
            self.plot[i].clear()
            self.subplot_container[i] = []
            
    def set_titles(self, index, title_name, x_axis_label, y_axis_label):
        self.plot[index].setTitle(title_name)
        self.plot[index].setLabel('left', y_axis_label)
        self.plot[index].setLabel('bottom', x_axis_label)

class CreateVerticalGraphBox():
    def __init__(self, title = 'Graph plots', num_graph = 8, col_num = 2):
        # Setup the plot screen
        self.groupbox = QGroupBox(title)
        self.hbox = QHBoxLayout()
        self.vbox_container = []
        self.num_graph = num_graph
        self.col_num = col_num
        
        for i in range (col_num):
            self.vbox_container.append(QVBoxLayout())
            
        for i in range (col_num):
            self.hbox.addLayout(self.vbox_container[i])
        
        self.canvas = []
        self.plot = []
        self.subplot_container = []
        
        for i in range (num_graph):
            self.canvas.append(pg.GraphicsLayoutWidget())
            self.plot.append(self.canvas[i].addPlot())
            self.vbox_container[i%col_num].addWidget(self.canvas[i])
            self.subplot_container.append([])
            
        
        # Setup background color and axis
        # Set grey color
        color_grey = [230,230,230]
        for i in range (num_graph):     
            self.canvas[i].setBackground(color_grey)
            self.plot[i].getAxis('left').setTextPen('k')
            self.plot[i].getAxis('right').setTextPen('k')
            self.plot[i].getAxis('bottom').setTextPen('k')
            self.plot[i].getAxis('top').setTextPen('k')
            self.plot[i].setLabel('left', "%s%d" %('Graph',i))
            # self.plot[i].setTitle("%s%d" %('Graph',i), color='k', bold = True, size='6pt')
            # self.plot[i].showAxis('right')
            # self.plot[i].showAxis('top')

        
        self.groupbox.setLayout(self.hbox)         
        
    def update_plot(self, index, x_data, y_data, graph_num = 9999):
        if graph_num == 9999:
            self.subplot_container[index][-1].setData(x_data, y_data)
        else:
            self.subplot_container[index][-(1+graph_num)].setData(x_data, y_data)
        
    def clear_plot(self, index):
        self.plot[index].clear()
        
    def addnew_plot(self, index, **kwargs):
        self.graph_type = kwargs.get("type")
        if self.graph_type == "symbol":
            self.subplot_container[index].append(self.plot[index].plot(pen = 'b', symbol='o', symbolPen='r'))
            if len(self.subplot_container[index])>1:
                self.subplot_container[index][-2].setPen('k')
                self.subplot_container[index][-2].setSymbolBrush(QColor(10, 130, 3))
        else:
            self.subplot_container[index].append(self.plot[index].plot(pen = pg.mkPen('r', width = 3)))
            if len(self.subplot_container[index])>1:
                self.subplot_container[index][-2].setPen('b')
            
        
    def reset_plot(self):
        for i in range(self.num_graph):
            self.plot[i].clear()
            self.subplot_container[i] = []
            
    def reset_plot_index(self, index):
        self.plot[index].clear()
        self.subplot_container[index] = []

            
    def set_titles(self, index, title_name, x_axis_label, y_axis_label):
        self.plot[index].setTitle(title_name)
        self.plot[index].setLabel('left', y_axis_label)
        self.plot[index].setLabel('bottom', x_axis_label)
        
        
        
class CreateLiveValueBox(): # Execute the measurement 
    def __init__(self, title = 'Live Values', num_values = 3):
        self.num_values = num_values
        self.groupbox = QGroupBox('Live status') # Object to be returned
        # Outline layouts
        self.grid = QGridLayout() 
        self.lbl_status_value = QLabel('Idle')
        self.lbl_status_value.setStyleSheet("background-color: lightgreen;"
                                            "color: black;"
                                            "font: bold 12px")
        self.lbl_status_value.setAlignment(QtCore.Qt.AlignCenter)
        
        self.grid.addWidget(self.lbl_status_value, 0,0,2,1)
        self.lbl_title_list = [None]*num_values
        self.lbl_value_list = [None]*num_values
        for i in range (num_values):
            self.lbl_title_list[i] = QLabel('%s%d' %('Value',i))
            self.lbl_title_list[i].setStyleSheet("color: black;"
                                                 "font: bold 12px")
            self.lbl_title_list[i].setAlignment(QtCore.Qt.AlignCenter)
            self.lbl_value_list[i] = QLabel('%d %s' %(0,'Unit'))
            self.lbl_value_list[i].setStyleSheet("background-color: black;"
                                                 "color: lightgreen;"
                                                 "font: bold 12px")
            self.lbl_value_list[i].setAlignment(QtCore.Qt.AlignCenter)
            self.grid.addWidget(self.lbl_title_list[i],0,i+1)
            self.grid.addWidget(self.lbl_value_list[i],1,i+1)
            
        self.groupbox.setLayout(self.grid)
        
    def set_titles(self, title_list):
        for i in range(self.num_values):
            self.lbl_title_list[i].setText(title_list[i])
            
    def set_values(self, value_list):
        for i in range(self.num_values):
            self.lbl_value_list[i].setText(value_list[i])
            
    def set_status_idle(self):
        self.lbl_status_value.setText('Idle')
        self.lbl_status_value.setStyleSheet("background-color: lightgreen;"
                                            "color: black;"
                                            "font: bold 12px")
        
    def set_status_run(self):
        self.lbl_status_value.setText('Running...')
        self.lbl_status_value.setStyleSheet("background-color: blue;"
                                            "color: white;"
                                            "font: bold 12px")
        
    def set_status_abort(self):
        self.lbl_status_value.setText('Abort')
        self.lbl_status_value.setStyleSheet("background-color: yellow;"
                                            "color: black;"
                                            "font: bold 12px")
            

class CreateDataSettingsBox:
    def __init__(self):
        # Settings for raw data save, folder and filename settings
        self.groupbox = QGroupBox('Data location and filename')  # Object to be returned

        # Outline layouts
        self.vbox_settings = QVBoxLayout()
        self.hbox_settings_subbox_folder = QHBoxLayout()
        self.hbox_settings_subbox_filename = QHBoxLayout()

        # Widgets
        self.lbl_location = QLabel('Location:')
        self.le_location = QLineEdit('D:/Data')
        self.btn_location = QPushButton('Select folder')

        self.lbl_filename = QLabel('Filename:')
        self.le_filename = QLineEdit('noname')

        self.vbox_settings.addLayout(self.hbox_settings_subbox_folder)
        self.vbox_settings.addLayout(self.hbox_settings_subbox_filename)

        self.hbox_settings_subbox_folder.addWidget(self.lbl_location)
        self.hbox_settings_subbox_folder.addWidget(self.le_location)
        self.hbox_settings_subbox_folder.addWidget(self.btn_location)

        self.hbox_settings_subbox_filename.addWidget(self.lbl_filename)
        self.hbox_settings_subbox_filename.addWidget(self.le_filename)

        self.groupbox.setLayout(self.vbox_settings)

        self.btn_location.clicked.connect(self.select_folder)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            None, "Select Folder", self.le_location.text()
        )
        if folder:
            self.le_location.setText(folder)

    def file_name_check(self, folderpath, filename):
        # uniq = 1
        # outputpath = os.path.join(folderpath, f"{filename}.dat")
        # newfilename = filename

        # while os.path.exists(outputpath):
        #     newfilename = f"{filename}({uniq})"
        #     outputpath = os.path.join(folderpath, f"{newfilename}.dat")
        #     uniq += 1

        # return newfilename
        uniq = 1
        existing_names = [os.path.splitext(f)[0] for f in os.listdir(folderpath)]
        
        newfilename = filename
        while newfilename in existing_names:
            newfilename = f"{filename}({uniq})"
            uniq += 1

        return newfilename

    def save_recording(self, data):
        folder = self.le_location.text()
        filename = self.le_filename.text()
        os.makedirs(folder, exist_ok=True) #create the folde if not exist

        newfilename = self.file_name_check(folder, filename)
        outputpath = os.path.join(folder, f"{newfilename}.dat")
        np.savetxt(outputpath, data, fmt='%.6E', delimiter=',', newline='\n')

        return filename

    def get_save_path_only(self, extension = 'npz'):
        folder = self.le_location.text()
        filename = self.le_filename.text()
        newfilename = self.file_name_check(folder, filename)
        outputpath = os.path.join(folder, f"{newfilename}.{extension}")
        return outputpath

    def save_settings(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        settings = {
            'location': self.le_location.text(),
            'filename': self.le_filename.text()
        }
        try:
            with open(filepath, 'w') as f:
                json.dump(settings, f, indent=4)
            print(f"[INFO] Settings saved to {filepath}")
        except Exception as e:
            print(f"[ERROR] Could not save settings to {filepath}: {e}")

    def load_settings(self, filepath):
        if not os.path.exists(filepath):
            return
        with open(filepath, 'r') as f:
            settings = json.load(f)
        self.le_location.setText(settings.get('location', 'D:/Data'))
        self.le_filename.setText(settings.get('filename', 'noname'))

    
class CreateRunBox(): # Execute the measurement 
    def __init__(self):        
        self.groupbox = QGroupBox('Measurement') # Object to be returned
        # Outline layouts
        self.vbox_run = QVBoxLayout() 
        
        # Widgets
        self.btn_run = QPushButton('RUN')
        self.btn_abort = QPushButton('ABORT')
        # Draw widgets and layouts
        self.vbox_run.addWidget(self.btn_run)
        self.vbox_run.addWidget(self.btn_abort)
    
        self.groupbox.setLayout(self.vbox_run)
        


class CreateLogBox(): # Execute the measurement 
    def __init__(self):
        self.groupbox = QGroupBox('System log') # Object to be returned
        # Outline layouts
        self.vbox_status = QVBoxLayout() 
        
        # Widgets
        self.te_status_panel = QTextEdit()
        
        # Draw widgets and layouts
        self.vbox_status.addWidget(self.te_status_panel)
    
        self.groupbox.setLayout(self.vbox_status)
        
    def update_log(self, update_text):
        now = datetime.now()
        dt_string = now.strftime("[%Y-%m-%d %H:%M:%S]")
        self.te_status_panel.append('%s %s' %(dt_string, update_text))
        
    def remove_last_sentence(self):
        self.te_status_panel.undo()
        
class CreateSWInfoBox():
    def __init__(self, sw_text = None, date_text = None, name_text = None, aff_text = None, contact_text = None):
        self.groupbox = QGroupBox('SW Information')
        self.vbox = QVBoxLayout()
        self.lbl_sw = QLabel(sw_text)
        self.lbl_sw.setAlignment(QtCore.Qt.AlignCenter)
        # self.lbl_date = QLabel(date_text)
        # self.lbl_date.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_name = QLabel(name_text)
        self.lbl_name.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_aff= QLabel(aff_text)
        self.lbl_aff.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_contact = QLabel(contact_text)
        self.lbl_contact.setAlignment(QtCore.Qt.AlignCenter)
        self.vbox.addWidget(self.lbl_sw)
        # self.vbox.addWidget(self.lbl_date)
        self.vbox.addWidget(self.lbl_name)
        self.vbox.addWidget(self.lbl_aff)
        self.vbox.addWidget(self.lbl_contact)
        self.groupbox.setLayout(self.vbox)
        
class TimeDisplayBox():
    def __init__(self):        
        font = QFont('Arial', 12, QFont.Bold)
        font_medium = QFont('Arial', 12, QFont.Bold)
        self.groupbox = QGroupBox('Time Display:')
        self.hbox_time_display = QHBoxLayout()
        self.vbox_current_time = QVBoxLayout()
        self.vbox_recording_time = QVBoxLayout()
        self.lbl_current_time_label = QLabel('Current date & time')
        self.lbl_current_time = QLabel('00:00:00')
        self.lbl_recording_time_label = QLabel('Time elapsed for the current measurment:')
        self.lbl_recording_time = QLabel('00:00:00.00')
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(100)
        self.vbox_current_time.addWidget(self.lbl_current_time_label)
        self.vbox_current_time.addWidget(self.lbl_current_time)
        self.vbox_recording_time.addWidget(self.lbl_recording_time_label)
        self.vbox_recording_time.addWidget(self.lbl_recording_time)
        self.hbox_time_display.addLayout(self.vbox_current_time)
        self.hbox_time_display.addLayout(self.vbox_recording_time)
        self.groupbox.setLayout(self.hbox_time_display)
        self.lbl_current_time.setFont(font_medium)
        self.lbl_recording_time.setFont(font_medium)
        self.lbl_current_time_label.setAlignment(Qt.AlignCenter)
        self.lbl_current_time.setAlignment(Qt.AlignCenter)
        self.lbl_recording_time_label.setAlignment(Qt.AlignCenter)
        self.lbl_recording_time.setAlignment(Qt.AlignCenter)
        
        
    def refresh(self):
        current_time = QTime.currentTime()
        current_date = QDate.currentDate()
        label_date = current_date.toString('yyyy/MM/dd')
        label_time = current_time.toString('hh:mm:ss')
        label = ('%s %s' %(label_date, label_time))
        self.lbl_current_time.setText(label)
        
    def update_time_elapsed(self):
        self.current_time = time.time()
        self.time_elapsed = self.current_time - self.start_time
        self.lbl_recording_time.setText(self.convert_time(self.time_elapsed))
        
    def convert_time(self, time_second):
        hours = time_second // 3600.0
        time_second = time_second - hours*3600.0
        minutes = time_second // 60.0
        time_second = time_second - minutes*60.0
        
        return('%02.0f:%02.0f:%05.2f'%(hours, minutes, time_second))
    def check_start_time(self):
        self.start_time = time.time()
        
        
    