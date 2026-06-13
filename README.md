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

**INSTALLATION**

Prerequisites:
1. Python 3.9 or later (a standard CPython distribution from python.org is recommended; the Windows Store build is not recommended).
2. A native VISA backend for GPIB communication. NI-VISA (Keithley/NI) is recommended and must be installed separately from the operating-system vendor. PyVISA-py is bundled as a fallback backend.

Steps:
1. Obtain the source, e.g.:
   `git clone <repository-url>`
2. (Recommended) Create and activate a virtual environment:
   `python -m venv .venv`
   `.venv\Scripts\activate`   (Windows)
3. Install the Python dependencies:
   `pip install -r requirements.txt`

The pinned dependency list is provided in `requirements.txt`:
PyQt5, pyqtgraph, NumPy, PyVISA, and PyVISA-py.

**RUNNING THE SOFTWARE**

From the source directory:
`cd SynapSSU_v_0_30`
`python SynapSSU_v0_3.py`

Instrument settings entered in the GUI are persisted to `SynapSSU_v_0_30/settings/*.json` and reloaded on the next launch.

**BUILDING A STANDALONE EXECUTABLE (OPTIONAL)**

A Windows executable can be produced with Nuitka. Use a standard CPython environment (not the Windows Store build), with Nuitka and a C compiler available (Nuitka can auto-download MinGW64 on first run):

`pip install nuitka`

Then run the provided build script from the source directory:
`cd SynapSSU_v_0_30`
`build_synapssu.bat`

The script builds in `--standalone` mode (not `--onefile`) so that the `settings` directory persists next to the executable. The resulting application is the entire `build\SynapSSU_v0_3.dist\` folder, which should be distributed together (e.g. as a .zip). The target PC still requires a native VISA backend (NI-VISA) to be installed.

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
