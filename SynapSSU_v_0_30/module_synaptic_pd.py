# -*- coding: utf-8 -*-
"""
Created on Fri Sep 15 16:05:31 2023

@author: Hongseok
"""

from module_common import *

class CreateClass(CreateClass_Super):        
    def tab_setup(self):
        self.tab = QWidget()   
        self.scan_type = "PD"
        
        """PD Tab Setup"""            
        self.PD_General_ParamBox = ui.CreateParameterSettingsBox('PD General Parameters', 3)
        self.PD_General_ParamBox.set_item(0, 'Total # of cycles', '3', 'cycles')
        self.PD_General_ParamBox.set_item(1, 'Internal trigger refresh time', '50', 'ms')
        self.PD_General_ParamBox.set_item(2, 'Delay before start', '1', 's')
        
        self.PD_Pot_Pulse_ParamBox = ui.CreateParameterSettingsBoxWithToggle('Potentiation Pulse Parameters', 3, 3, layout = "vertical")
        self.PD_Pot_Pulse_ParamBox.set_toggle_item(0, "Gate (Synaptic Transistor)", 1)
        self.PD_Pot_Pulse_ParamBox.set_toggle_item(1, "Drain (Memristor/Memtransistor)", 0)
        self.PD_Pot_Pulse_ParamBox.set_toggle_item(2, "External (Photonic Synaptic Transistor)", 0)
        self.PD_Pot_Pulse_ParamBox.set_item(0, 'Number of pulses', '100', 'times')
        self.PD_Pot_Pulse_ParamBox.set_item(1, 'Pulse amplitude', '-5', 'V')
        self.PD_Pot_Pulse_ParamBox.set_item(2, 'Pulse width', '100', 'ms')
        
        self.PD_Dep_Pulse_ParamBox = ui.CreateParameterSettingsBoxWithToggle('Depression Pulse Parameters', 3, 3, layout = "vertical")
        self.PD_Dep_Pulse_ParamBox.set_toggle_item(0, "Gate (Synaptic Transistor)", 1)
        self.PD_Dep_Pulse_ParamBox.set_toggle_item(1, "Drain (Memristor/Memtransistor)", 0)
        self.PD_Dep_Pulse_ParamBox.set_toggle_item(2, "External (Photonic Synaptic Transistor)", 0)   
        self.PD_Dep_Pulse_ParamBox.set_item(0, 'Number of pulses', '100', 'times')
        self.PD_Dep_Pulse_ParamBox.set_item(1, 'Pulse amplitude', '5', 'V')
        self.PD_Dep_Pulse_ParamBox.set_item(2, 'Pulse width', '100', 'ms')

        self.PD_Read_ParamBox = ui.CreateParameterSettingsBox('PD Read Parameters', 5)
        self.PD_Read_ParamBox.set_item(0, 'Read Drain bias', '1', 'V')
        self.PD_Read_ParamBox.set_item(1, 'Read Gate bias', '1', 'V')
        self.PD_Read_ParamBox.set_item(2, 'Before-read delay', '250', 'ms')
        self.PD_Read_ParamBox.set_item(3, 'After-read delay', '250', 'ms')
        self.PD_Read_ParamBox.set_item(4, 'Turn off bias while waiting', '0', '0:OFF/1:ON')       
                       
        
        self.PD_GraphBox = ui.CreateGraphBox('PD characteristics', 1)
        self.PD_GraphBox.set_titles(0, 'PD Curves', 'Pulse number (#)', 'Ids (A)')        
        
        
        # tab setup
        self.tab_hbox = QHBoxLayout()  
        self.tab_vbox = QVBoxLayout()
        self.tab_vbox.addWidget(self.PD_Pot_Pulse_ParamBox.groupbox)
        self.tab_vbox.addWidget(self.PD_Dep_Pulse_ParamBox.groupbox)
        self.tab_vbox.addWidget(self.PD_Read_ParamBox.groupbox)
        self.tab_vbox.addWidget(self.PD_General_ParamBox.groupbox)
        self.tab_vbox.addStretch(1)
           
        self.tab_hbox.addLayout(self.tab_vbox)
        self.tab_hbox.addWidget(self.PD_GraphBox.groupbox)
        self.tab_hbox.setStretch(0,1)
        self.tab_hbox.setStretch(1,3)
        self.tab.setLayout(self.tab_hbox)
        
        #main ui communication test
        self.main.LogBox.update_log("PD module loaded")
      
    def update_plot(self, array):
        print(array)
        if array[0] == 99999999:
            self.measurement_done_flag = True
            self.stop_measurement()
        else:
            if np.isnan(array)[0] == True:
                self.PD_GraphBox.addnew_plot(0, type = "symbol")
                self.count = 1
                self.start = self.N
    
            else:
                self.result_data[self.N] = array
                self.PD_GraphBox.update_plot(0, self.result_data[self.start:self.start+self.count,0], self.result_data[self.start:self.start+self.count,2])
                
                # Update the plot    
                self.N = self.N+1
                self.count = self.count + 1
                
                self.main.LiveBox.set_status_run()
                self.main.LiveBox.set_values(['%.4e%s' %(array[1], 'V'), '%.4e%s' %(array[2], 'A'), '%.4e%s' %(array[3], 'V'), '%.4e%s' %(array[4], 'A')])

    def run_measurement_start(self):      
        # Calculate sweep points  
        
        print ("Table prepared")
        
        print ("Preparing bias parameters")
        
        self.vds_list = []
        self.vgs_list = []
        
        # Calculate list for drain biases
        for i in range (3):
            if self.PD_Pot_Pulse_ParamBox.rbtn_list[i].isChecked():
                self.pot_pulse_target = i
        
        print("Potentiation Pulse SMU index = %d" %(self.pot_pulse_target))
        
        for i in range (3):
            if self.PD_Dep_Pulse_ParamBox.rbtn_list[i].isChecked():
                self.dep_pulse_target = i
       
        print("Depression Pulse SMU index = %d" %(self.dep_pulse_target))
        
        self.total_num_cycles = round(float(self.PD_General_ParamBox.le_list[0].text()), ROUNDNUM)
        self.time_step = round(float(self.PD_General_ParamBox.le_list[1].text()), ROUNDNUM)       
        self.start_delay = round(float(self.PD_General_ParamBox.le_list[2].text()), ROUNDNUM)      
        self.wait_time = self.start_delay
        
        self.pot_pulse_num = round(float(self.PD_Pot_Pulse_ParamBox.le_list[0].text()), ROUNDNUM)
        self.pot_pulse_amp = round(float(self.PD_Pot_Pulse_ParamBox.le_list[1].text()), ROUNDNUM)
        self.pot_pulse_width = round(float(self.PD_Pot_Pulse_ParamBox.le_list[2].text()), ROUNDNUM)
        
        self.dep_pulse_num = round(float(self.PD_Dep_Pulse_ParamBox.le_list[0].text()), ROUNDNUM)
        self.dep_pulse_amp = round(float(self.PD_Dep_Pulse_ParamBox.le_list[1].text()), ROUNDNUM)
        self.dep_pulse_width = round(float(self.PD_Dep_Pulse_ParamBox.le_list[2].text()), ROUNDNUM)
                
        self.vds_list.append(round(float(self.PD_Read_ParamBox.le_list[0].text()), ROUNDNUM))
        self.vgs_list.append(round(float(self.PD_Read_ParamBox.le_list[1].text()), ROUNDNUM))
        self.before_read_delay = round(float(self.PD_Read_ParamBox.le_list[2].text()), ROUNDNUM)
        self.after_read_delay = round(float(self.PD_Read_ParamBox.le_list[3].text()), ROUNDNUM)
        self.read_bias_off = round(float(self.PD_Read_ParamBox.le_list[4].text()), ROUNDNUM)       
                
        print ("Prepare measurement...")
        self.tot_num_measure_points = (int(self.pot_pulse_num) + int(self.dep_pulse_num))*int(self.total_num_cycles)
        # Prepare data array for save
        
        self.result_data = np.empty((self.tot_num_measure_points, 5)) # No SMU EXT is used
            
            
        self.result_data[:] = np.nan
        self.N = 0
        self.start = 0
        
        #Reset graph
        self.PD_GraphBox.reset_plot()   
        
        # Initiate IO_Thread thread
        self.main.LogBox.update_log("SMU_list: %s" %(self.SMU_list))
        self.IO_Thread = IO_Thread(self.SMU_list,
                                   scan_type = self.scan_type, 
                                   pot_pulse_target = self.pot_pulse_target,
                                   dep_pulse_target = self.dep_pulse_target,
                                   time_step = self.time_step,
                                   pot_pulse_num = self.pot_pulse_num,
                                   pot_pulse_amp = self.pot_pulse_amp,
                                   pot_pulse_width = self.pot_pulse_width,
                                   dep_pulse_num = self.dep_pulse_num,
                                   dep_pulse_amp = self.dep_pulse_amp,
                                   dep_pulse_width = self.dep_pulse_width,
                                   vds_list = self.vds_list, 
                                   vgs_list = self.vgs_list,
                                   before_read_delay = self.before_read_delay,
                                   after_read_delay = self.after_read_delay,
                                   read_bias_off = self.read_bias_off,
                                   start_delay = self.start_delay,
                                   total_num_cycles = self.total_num_cycles,
                                   wait_time = self.wait_time
                                   ) 
        self.IO_Thread.signal.connect(self.update_plot)
        self.main.LogBox.update_log("Measurement start!")
        self.IO_Thread.start()  

class IO_Thread(IO_Thread_Super):  
    def __init__(self, smu_list = None, parent = None, **kwargs):
        # Assume smu_list is an array, and the element is a dictionary for smu
        QtCore.QThread.__init__(self, parent)
        print("IO Thread start")
        
        self.SMU_list = smu_list
        print(self.SMU_list)
        self.flag = 1
        for key, value in kwargs.items():
                    setattr(self, key, value)
        
        self.flag = 1 # If measurment is done (or aborted)
        self.flag_pot_dep = 1 # 1: potentiation, 0: depression
        self.cycle_count = 1 # current cycle 
        self.pd_cycle_count = 1
        self.flag_status = 1 # current pulsation stage
        self.cycle_count_abs = 1
    
    def is_pulse_rightnow(self, current_time, time_seg_01, time_seg_02, time_seg_03):
       if current_time < time_seg_01:
           return 1
       elif current_time >= time_seg_01 and current_time < time_seg_02:
           return 2
       elif current_time >= time_seg_02 and current_time < time_seg_03:
           return 3
       else:
           return 4
                
    def run(self):
        def repeating_measurement():
            if self.flag == 1:
                CURRENT_TIME = time.time()-self.start_time
                flag_status = self.is_pulse_rightnow(CURRENT_TIME, self.time_seg_01, self.time_seg_02, self.time_seg_03)
                print("Current pulse number: %d" %(self.cycle_count))
                if flag_status == 1:
                    print("Time seg 01: Current: after read delay")
                    if self.read_bias_off == 1:
                        self.SMU_DRAIN.write(":SOUR:VOLT:LEV ", str(0))
                        self.SMU_GATE.write(":SOUR:VOLT:LEV ", str(0))
                        if self.is_SMU_EXT_used:
                            self.SMU_EXT.write(":SOUR:VOLT:LEV ", str(0))
                            self.SMU_EXT.query_ascii_values(":READ?") 
                        self.SMU_DRAIN.query_ascii_values(":READ?")
                        self.SMU_GATE.query_ascii_values(":READ?")                        
                    else:
                        self.SMU_DRAIN.write(":SOUR:VOLT:LEV ", str(self.vds))
                        self.SMU_GATE.write(":SOUR:VOLT:LEV ", str(self.vgs))
                        if self.is_SMU_EXT_used:
                            self.SMU_EXT.write(":SOUR:VOLT:LEV ", str(self.ext))
                            self.SMU_EXT.query_ascii_values(":READ?") 
                        self.SMU_DRAIN.query_ascii_values(":READ?")
                        self.SMU_GATE.query_ascii_values(":READ?")
                elif flag_status == 2:
                    print("Time seg 02: Apply pulse")
                    self.SMU_DRAIN.write(":SOUR:VOLT:LEV ", str(self.vdsamp))
                    self.SMU_GATE.write(":SOUR:VOLT:LEV ", str(self.vgsamp))
                    if self.is_SMU_EXT_used:
                        self.SMU_EXT.write(":SOUR:VOLT:LEV ", str(self.extamp))
                        self.SMU_EXT.query_ascii_values(":READ?") 
                    print((self.SMU_GATE.query_ascii_values(":READ?")))
                    print((self.SMU_DRAIN.query_ascii_values(":READ?"))) 
                elif flag_status == 3:
                    print("Time seg 03: Turn off pulse")
                    if self.read_bias_off == 1:
                        self.SMU_DRAIN.write(":SOUR:VOLT:LEV ", str(0))
                        self.SMU_GATE.write(":SOUR:VOLT:LEV ", str(0))
                        if self.is_SMU_EXT_used:
                            self.SMU_EXT.write(":SOUR:VOLT:LEV ", str(0))
                            self.SMU_EXT.query_ascii_values(":READ?") 
                        self.SMU_GATE.query_ascii_values(":READ?")
                        self.SMU_DRAIN.query_ascii_values(":READ?")                        
                    else:
                        self.SMU_DRAIN.write(":SOUR:VOLT:LEV ", str(self.vds))
                        self.SMU_GATE.write(":SOUR:VOLT:LEV ", str(self.vgs))
                        if self.is_SMU_EXT_used:
                            self.SMU_EXT.write(":SOUR:VOLT:LEV ", str(self.ext))
                            self.SMU_EXT.query_ascii_values(":READ?") 
                        self.SMU_GATE.query_ascii_values(":READ?")
                        self.SMU_DRAIN.query_ascii_values(":READ?")
                else:
                    print("Time seg 04: read")
                    self.SMU_DRAIN.write(":SOUR:VOLT:LEV ", str(self.vds))
                    self.SMU_GATE.write(":SOUR:VOLT:LEV ", str(self.vgs))
                    CURRENT_DRAIN = (self.SMU_DRAIN.query_ascii_values(":READ?"))
                    CURRENT_GATE = (self.SMU_GATE.query_ascii_values(":READ?"))
                    print(CURRENT_GATE)
                    print(CURRENT_DRAIN)
                    temp = np.array([self.cycle_count_abs, CURRENT_DRAIN[0], CURRENT_DRAIN[1], CURRENT_GATE[0], CURRENT_GATE[1]])
                    self.signal.emit(temp)  
                    print("Pulse cycle done")
                    self.start_time = time.time() #reset start time
                    self.cycle_count = self.cycle_count + 1
                    self.cycle_count_abs = self.cycle_count_abs + 1
                    
                    """ When the cycle reaches maximum """
                    if self.cycle_count > self.cycle_count_max:
                        
                        # reset amp(under pulse) voltages
                        self.vgsamp = self.vgs
                        self.vdsamp = self.vds
                        self.extamp = self.ext
                        
                        if self.flag_pot_dep == 1: # transition from potentiation to depression
                            print("Transition from potentiation to depression")
                            self.flag_pot_dep = 0
                            self.cycle_count = 1
                            self.cycle_count_max = self.dep_pulse_num
                            if self.dep_pulse_target == 0:
                                self.vgsamp = self.vgs + self.dep_pulse_amp                                
                            elif self.dep_pulse_target == 1:
                                self.vdsamp = self.vds + self.dep_pulse_amp
                            else:
                                self.extamp = self.ext + self.dep_pulse_amp
                        else: # a cycle is done
                            self.pd_cycle_count = self.pd_cycle_count + 1
                            if self.pd_cycle_count <= self.total_num_cycles: # start next pd cycle
                                print("Start new PD cycle, transition from depression to potentiation")
                                self.flag_pot_dep = 1
                                self.cycle_count = 1
                                self.cycle_count_max = self.pot_pulse_num
                                if self.pot_pulse_target == 0:
                                    self.vgsamp = self.vgs + self.pot_pulse_amp                                  
                                elif self.pot_pulse_target == 1:
                                    self.vdsamp = self.vds + self.pot_pulse_amp
                                else:
                                    self.extamp = self.ext + self.pot_pulse_amp
                            else: # measurment is done
                                print("All PD cycle is done")
                                self.flag = 0  
            else:
                timer.stop()
                self.stop()  
        
        print("Scan type: %s" %(self.scan_type))
        
        self.SMU_DRAIN = self.SMU_list[0]['smu']
        self.SMU_GATE = self.SMU_list[1]['smu']    
        
        if self.pot_pulse_target == 2 or self.dep_pulse_target == 2:
            self.SMU_EXT = self.SMU_list[2]['smu']
        
        self.time_seg_01 = self.after_read_delay/1000.0
        if self.flag_pot_dep == 1:
            self.time_seg_02 = round(float((self.after_read_delay+self.pot_pulse_width)/1000.0), ROUNDNUM)
        else:
            self.time_seg_02 = round(float((self.after_read_delay+self.dep_Pulse_width)/1000.0), ROUNDNUM)            
        self.time_seg_03 = round(float(self.time_seg_02 + self.before_read_delay/1000.0), ROUNDNUM)
        self.cycle_count_max = self.pot_pulse_num
           
        self.vds = self.vds_list[0]
        self.vgs = self.vgs_list[0]
        self.ext = 0.0

        self.vgsamp = self.vgs
        self.vdsamp = self.vds
        self.extamp = self.ext
        
        if self.pot_pulse_target == 0:
            self.vgsamp = self.vgs + self.pot_pulse_amp
        elif self.pot_pulse_target == 1:
            self.vdsamp = self.vds + self.pot_pulse_amp
        else:
            self.extamp = self.ext + self.pot_pulse_amp
        
        if self.pot_pulse_target == 2 or self.dep_pulse_target == 2:
            self.is_SMU_EXT_used = True
        else:
            self.is_SMU_EXT_used = False
        
        timer = QTimer()
        timer.setTimerType(QtCore.Qt.PreciseTimer)
        timer.timeout.connect(repeating_measurement)
        
        new_curve = np.empty(5)
        new_curve[:] = np.nan
        self.time_step = int(self.time_step)
        self.signal.emit(new_curve)
        
        self.SMU_GATE.write(":SOUR:VOLT:LEV ", str(self.vgs))
        self.SMU_GATE.write(":OUTP ON")
        
        self.SMU_DRAIN.write(":SOUR:VOLT:LEV ", str(self.vds))
        self.SMU_DRAIN.write(":OUTP ON")        
        
        if self.pot_pulse_target == 2 or self.dep_pulse_target == 2:
            self.SMU_EXT.write(":SOUR:VOLT:LEV ", str(self.ext))
            self.SMU_EXT.write(":OUTP ON")    

        time.sleep(self.wait_time)
        self.start_time = time.time()
        timer.start(self.time_step)
        self.exec_()
        
    
            
    def stop(self):  # Override the original stop method to ensure turn off SMU_EXT
        self.signal.emit([99999999,99999999,99999999,99999999,99999999,99999999])  

        print("IO_Thread stop called") 
        self.SMU_DRAIN.write("OUTP OFF")
        self.SMU_GATE.write("OUTP OFF")
        if self.pot_pulse_target == 2 or self.dep_pulse_target == 2:
            self.SMU_EXT.write("OUTP OFF")
            
        self.quit()
        