# -*- coding: utf-8 -*-
"""
Created on Fri Sep 15 16:05:31 2023

@author: Hongseok
"""
import UI_all as ui
# For Qt layout (GUI)
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout)

# from pyqtgraph.Qt import QtCore
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer

# General
import time
import numpy as np

# General

""" Round digit for converting float to int """
ROUNDNUM = 4
TIMER_INTERVAL = 10

class CreateClass_Super:
    def __init__(self, main_ui):
        self.main = main_ui
        self.tab_setup()
        
    def tab_setup(self):        
        print("tab_setup called, override this method")
        """ Override this method"""
    
    def update_plot(self, array):
        print("update_plot called, override this method")
        """ Override this method"""
        
    def run_measurement(self):        
        self.measurement_timer = QTimer()
        self.measurement_timer.setInterval(TIMER_INTERVAL)
        self.main.TimeDisplayBox.check_start_time()
        self.measurement_timer.timeout.connect(self.main.TimeDisplayBox.update_time_elapsed)
        self.measurement_timer.start(TIMER_INTERVAL)
        print("QTimer initialized")
        
        self.SMU_list = self.main.ConnectionControlBox.get_SMU_list()
        self.main.ConnectionControlBox.initialize_SMU()
        
        # self.SMU_list = self.main.ConnectionControlBox.get_SMU_list()
        print("Run Measurement: %s" %(self.scan_type))
        self.main.LogBox.update_log("Run Measurement: %s" %(self.scan_type))
        
        for i in range(self.main.tabtotalnum):
            if i != self.main.tabs.currentIndex():
                self.main.tabs.setTabEnabled(i, False)
                
        print("Preparing tables of biasing values...")
        # self.main.ConnectionControlBox.initialize_SMU()
        self.run_measurement_start()
        
    def run_measurement_start(self):     
        print("run_measurement_start called, override this method")
        """ Override this method"""

    def stop_measurement(self):
        self.main.LogBox.update_log("Measurement done!")
        self.measurement_timer.stop()
        self.result_data = self.result_data[0:self.N,:]
        print(self.result_data)
        if self.measurement_done_flag == True:
            self.main.LiveBox.set_status_idle()
        else:
            self.main.LiveBox.set_status_abort()
        
        self.main.LiveBox.set_values(['- V',' - A', '- V', '- A'])
        self.measurement_done_flag = False
        
        self.main.DataSettingsBox.save_recording(self.result_data)
                
        outputpath_jpg = '%s%s%s%s' %(self.main.DataSettingsBox.root.dirName, '/', self.main.DataSettingsBox.newfilename, '.jpg')
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(self.main.winId())
        screenshot.save(outputpath_jpg, 'jpg')
        self.main.LogBox.update_log("Data saved to: %s%s%s%s" %(self.main.DataSettingsBox.root.dirName, '/', self.main.DataSettingsBox.newfilename, '.dat'))
        
        self.enable_tab_all()

    def abort_measurement(self):
        self.IO_Thread.abort()
        self.enable_tab_all()
            
    def enable_tab_all(self):
        for i in range(self.main.tabtotalnum):
            self.main.tabs.setTabEnabled(i, True)

class IO_Thread_Super(QtCore.QThread):
    signal = QtCore.pyqtSignal(object)
    def __init__(self, smu_list = None, parent = None, **kwargs):
        # Assume smu_list is an array, and the element is a dictionary for smu
        QtCore.QThread.__init__(self, parent)
        print("IO Thread start")
        
        self.SMU_list = smu_list
        print(self.SMU_list)
        self.flag = 1
        for key, value in kwargs.items():
                    setattr(self, key, value)
                
    def run(self):
        print("run(IO thread) called, override this method")
        """ Override this method"""

    def stop(self):  
        self.signal.emit([99999999,99999999,99999999,99999999,99999999,99999999])  

        print("IO_Thread stop called") 
        self.SMU_DRAIN.write("OUTP OFF")
        self.SMU_GATE.write("OUTP OFF")
        
        self.quit()
        
    def abort(self):
        self.flag = 0
        
    def take_positive(self, value):
        if value > 0:
            return value
        else:
            return 0