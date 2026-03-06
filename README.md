**SYNAPSSU: AN OPEN-SOURCE PYTHON SOFTWARE FOR SYNCHRONIZED AND PRECISION TIMING-CONTROLLED SYNAPTIC DEVICE CHARACTERIZATION**

SynapSSU is a specialized software tool designed for the characterization of artificial synaptic devices, which are essential for developing energy-efficient neuromorphic computing systems. The software allows for the control of multiple source-meter units (SMUs) to apply synchronized electrical or optical pulses and record the resulting device responses.

**CORE FEATURES**

The software supports the measurement of critical synaptic characteristics, including Excitatory Post-Synaptic Current (EPSC), Paired-Pulse Facilitation (PPF), and Long-Term Potentiation/Depression (PD). It is compatible with various device architectures, such as two-terminal memristors, three-terminal synaptic transistors, and optoelectronic synaptic devices that require external light stimulation. SynapSSU features an intuitive graphical user interface (GUI) for parameter tuning and real-time visualization.

**HARDWARE AND SOFTWARE REQUIREMENTS**

Hardware:
SMU instruments must be compatible with Keithley 2400 or 2450 series command sets.
Instruments must be connected to a PC via a GPIB interface or USB-GPIB converter supported by a driver such as NI-VISA.

Software:
The software is written in Python.
Required libraries include PyVISA for instrument communication, PyQt5 for the interface, NumPy for data processing, and pyqtgraph for visualization .

**OPERATIONAL WORKFLOW**

1. SMU Setup: Users select the SMU ports and configure parameters such as NPLC (default 0.1) and current compliance.
2. Location and Filename: Set the directory for saving the measurement results.
3. Method Selection: Choose the characterization type (EPSC/PPF or PD) and define pulse parameters like amplitude, duration, and time steps.
4. Run/Abort: Start the measurement with the RUN button; use ABORT to stop and save the current data at any time.
5. Real-time Plotting: Monitor data live as the software updates the current-time or pulse-current curves.
6. Data Saving: Results are automatically exported as .csv files and screenshot images.

**LICENSE**

SynapSSU is released under the MIT License.

**CONTACT**

Hongseok Oh, Department of Physics, Soongsil University.
Email: hoh@ssu.ac.kr 
