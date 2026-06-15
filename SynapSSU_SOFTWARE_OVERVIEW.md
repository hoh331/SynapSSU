# SynapSSU — Software Overview (Technical Reference for Discussion)

> Version: **v0.3.1** (June 2026). This document is a self-contained description of the
> SynapSSU software, written so that it can be discussed without access to the source
> code. It covers purpose, architecture, acquisition/timing model, parameters, data
> output, device protection, packaging, and known limitations. A short note on the
> current journal revision is included at the end.

---

## 1. Purpose & Scope

SynapSSU is an open-source Python application for the **electrical characterization of
artificial synaptic devices** used in neuromorphic-computing research. Its distinguishing
feature is the **coordinated, timing-controlled control of multiple source-measure units
(SMUs)** so that electrical and/or optical stimulation pulses can be applied to a device
while its response current is recorded in real time.

It targets three device classes:
- **Two-terminal memristors / memtransistors** (pulse applied to the drain terminal),
- **Three-terminal synaptic transistors** (pulse applied to the gate terminal),
- **Optoelectronic / photonic synaptic devices** (pulse applied via an external channel,
  e.g. driving a light source).

---

## 2. What It Measures

Two measurement modes (each is a GUI tab):

1. **EPSC / PPF** (Excitatory Post-Synaptic Current / Paired-Pulse Facilitation)
   Applies one or more stimulation pulses on a fixed-bias background and records the
   resulting current vs. time. One pulse → EPSC; multiple pulses with a defined
   inter-pulse delay → PPF.

2. **PD** (Potentiation / Depression; i.e. long-term potentiation/depression, LTP/LTD)
   Applies a train of *potentiation* pulses followed by a train of *depression* pulses,
   reading the channel current once per pulse cycle, and repeats for a number of
   super-cycles. Produces the characteristic conductance-vs-pulse-number curve.

---

## 3. Hardware Model

- **Up to three SMUs in fixed roles**, indexed 0/1/2:
  - SMU0 = **Drain** (read/measure terminal; also the pulse target for memristors)
  - SMU1 = **Gate** (pulse target for synaptic transistors; optional — code tolerates
    its absence)
  - SMU2 = **External** (optical-stimulation channel; only instantiated when an
    "External" pulse target is selected)
- **Instruments:** Keithley 2400 / 2450 series (or any instrument accepting the same SCPI
  command set).
- **Connection:** GPIB or USB-GPIB, through a native VISA backend (NI-VISA recommended).
  PyVISA-py is bundled as a pure-Python fallback backend.
- Communication is **synchronous SCPI**: the software writes a source level
  (`:SOUR:VOLT:LEV`) and reads back voltage/current with a blocking query (`:READ?`).

---

## 4. Software Stack & Architecture

**Stack:** Python 3.9+, PyQt5 (GUI), pyqtgraph (real-time plots), NumPy (data buffer),
PyVISA + PyVISA-py (instrument I/O).

**Architecture — two threads:**
- **GUI thread** — the Qt main loop. Hosts the widgets, the live plots, and the
  measurement parameters. Never blocks on instrument I/O.
- **Acquisition worker** — a `QThread` subclass (`IO_Thread`). Inside it, a Qt
  `QTimer` (set to `Qt.PreciseTimer`) fires a `repeating_measurement()` callback at a
  fixed interval. Each callback performs the SCPI write/read transactions and emits the
  measured row back to the GUI via a Qt **signal** (`pyqtSignal`), which the GUI uses to
  update the plot. This signal/slot hand-off is the thread-safe boundary between
  acquisition and display.

**Class structure (inheritance):**
- `CreateClass_Super` (in `module_common.py`) — base for a measurement mode: builds the
  tab, owns `run_measurement()` / `stop_measurement()` / `abort_measurement()`, manages
  the result buffer and file save.
- `IO_Thread_Super` (in `module_common.py`) — base worker thread; holds the abort `flag`
  and the `stop()` (outputs off + quit) logic.
- Each measurement mode subclasses both and overrides `tab_setup()`,
  `run_measurement_start()`, `update_plot()`, and the worker's `run()`.

---

## 5. File / Module Structure

```
SynapSSU_v_0_30/
├─ SynapSSU_v0_3.py            # entry point: App(QWidget), tab host, settings paths
├─ module_common.py           # base classes: CreateClass_Super, IO_Thread_Super
├─ module_synaptic_epsc_ppf.py# EPSC/PPF mode (tab + worker)
├─ module_synaptic_pd.py      # PD (LTP/LTD) mode (tab + worker)
├─ UI_all.py                  # reusable Qt widgets (param boxes, graph box, SMU
│                             #   connection unit, data-settings box, etc.)
├─ icon.ico                   # application icon
├─ settings/                  # per-SMU + data settings as JSON (auto-created)
├─ requirements.txt           # pinned dependencies
└─ build_synapssu.bat         # Nuitka standalone build script
```

Tabs/modules are registered in `App.setup_tabs()`; adding a mode = adding one module to
that list. (Reservoir-computing modules exist in development but are commented out in the
public version.)

---

## 6. Measurement Workflow (User-Facing)

1. **Connect SMUs** — pick the VISA port per SMU; set per-SMU NPLC, autozero, source/
   sense ranges, and current compliance.
2. **Set output location & filename.**
3. **Choose a mode tab** (EPSC/PPF or PD) and enter pulse parameters; pick the pulse
   target (Gate / Drain / External).
4. **RUN** — other tabs lock; the worker starts; plots update live.
5. **ABORT** anytime — stops, turns outputs off, and saves whatever was collected.
6. **On completion** — data is written to `.csv` and a window screenshot to `.jpg`.

---

## 7. Acquisition & Timing Model (Important)

Both modes use the same skeleton: a `Qt.PreciseTimer` fires every `time_step`
milliseconds (the "internal trigger refresh time"); each tick reads `time.time()` to get
the elapsed time and decides what to source and what to read.

**EPSC/PPF timing.** A list of pulse start times is precomputed from the pulse start,
width, count, and pulse-to-pulse delay. On every tick, `is_pulse_rightnow()` checks
whether the current elapsed time falls inside any pulse window `[t, t+width)`. If yes, the
target SMU is driven to `bias + amplitude`; if no, it is held at `bias`. The drain (and
gate, if present) are read every tick and the row is emitted. The whole run ends when
elapsed time exceeds the total measurement time.

**PD timing (state machine).** Each pulse cycle is divided into four time segments by
`is_pulse_rightnow()`:
1. after-read delay, 2. pulse-on, 3. before-read delay, 4. read.
The read segment is where the current is sampled and emitted (one point per cycle, x-axis
= absolute pulse number). A cycle counter advances through `pot_pulse_num` potentiation
pulses, then flips to `dep_pulse_num` depression pulses, then increments the super-cycle
counter until `total_num_cycles` is reached. Pulse target and amplitude are switched per
phase (potentiation vs depression).

**Timing precision — the honest picture.** `Qt.PreciseTimer` gives ~1 ms timer accuracy,
but the *effective* pulse-width granularity is bounded by `time_step`, and each tick
issues 2–3 **blocking** SCPI `:READ?` transactions over GPIB (each a few-to-tens of ms
round trip). So the real-world timing accuracy is governed by the timer step plus VISA
round-trip latency, not by the 1 ms timer alone. Claims of millisecond-scale precision
hold when the programmed pulse width is comfortably larger than `time_step`.

---

## 8. Parameter Reference

**Per-SMU settings (Connection box):** in-use flag, autozero (Yes/No), NPLC, voltage
source range (AUTO or fixed), current sense range (AUTO or fixed), **current compliance/
protection range**, trigger delay, source delay.

**EPSC/PPF tab:** drain bias `Vds`, gate bias `Vgs`; pulse target (Gate/Drain/External);
measurement time (s), pulse amplitude (V), pulse start (s), pulse duration (ms), delay
before sweep (s), measurement time step (ms), number of pulses (1 = EPSC, >1 = PPF),
delay between pulses (ms).

**PD tab:** total # of super-cycles, internal trigger refresh time (ms = `time_step`),
delay before start (s); potentiation block (target, # pulses, amplitude V, width ms);
depression block (same fields); read block (read drain bias, read gate bias, before-read
delay ms, after-read delay ms, "turn off bias while waiting" 0/1).

---

## 9. Data Output

- During a run, results accumulate in a **pre-allocated NumPy array** `result_data` of
  shape `N × M` (`M = 5`, or `7` when the external optical channel is active),
  initialized to NaN. A NaN row is used as an in-band "new curve" marker for the plot.
- **EPSC/PPF columns:** time, V(drain or pulse), I(drain), V(gate), I(gate) [+ V/I ext].
- **PD columns:** absolute pulse number, V(drain), I(drain), V(gate), I(gate).
- On stop, the array is truncated to the filled length, written to **`.csv`**, and a
  **`.jpg` screenshot** of the application window is saved to the chosen folder.

---

## 10. Device Protection & Fault Handling

Protection is **layered**:
- **Hardware current compliance** (`:SENS:CURR:PROT`) is set on each SMU before every
  run — the primary safeguard against over-current damage to the device or instrument.
- **Known-state setup:** each SMU is reset (`*RST`) and given explicit (or bounded auto)
  source/sense ranges before the run, so a measurement never starts from an undefined
  configuration. The init routine is wrapped in `try/except` and guards against
  unconnected units, so a comms/config error is reported without crashing the app.
- **Controlled shutdown:** on normal completion *or* user ABORT, all source outputs are
  switched off (`OUTP OFF`), so the device is never left under bias.
- **Single-active-measurement lock:** the other mode tabs are disabled during a run.
- **Defensive config I/O:** missing/malformed settings files degrade to defaults instead
  of aborting startup.

**Current limitation (stated honestly):** the per-tick `:READ?` calls inside the
acquisition loop are **not** individually wrapped in exception handling, so automatic
recovery from a mid-run instrument fault (e.g. a cable disconnect during a long run) is
not yet implemented. Protection is enforced at configuration time, in hardware
(compliance), and at controlled shutdown.

---

## 11. Settings Persistence

Per-SMU and data settings are saved as JSON on exit and reloaded on the next launch.
The settings directory is resolved to be **next to the running program**: next to the
script when run from source, and next to the executable when frozen (Nuitka sets
`NUITKA_ONEFILE_BINARY` for onefile builds; standalone falls back to `sys.argv[0]`). This
keeps user state discoverable in Explorer regardless of install method.

---

## 12. Packaging / Distribution

A Windows executable is built with **Nuitka** (`build_synapssu.bat`, using a dedicated
CPython venv + MSVC). The current distribution uses **`--standalone`** (a folder
containing the `.exe` plus its DLLs) rather than `--onefile`, because onefile binaries
self-extract to `%TEMP%` and are frequently blocked by Windows SmartScreen / antivirus.
The whole folder is distributed together. The native VISA backend (NI-VISA) must be
installed separately on the target PC; it is not bundled.

---

## 13. Known Limitations & Implementation Notes

- **Timing accuracy is I/O-bound**, set by `time_step` + GPIB round-trip latency (see §7),
  giving an effective loop rate in the tens of Hz. This matches the ms–s timescales of
  the synaptic phenomena targeted, but should not be over-claimed.
- **PD pot/dep timing segments** are computed once at the start of a run from the
  potentiation pulse width; the depression segment is not separately recomputed, so the
  pulse-window timing implicitly assumes comparable potentiation/depression pulse widths.
- **Acquisition-loop fault tolerance** is limited (see §10).
- **Resource footprint is light:** the data buffer is sub-megabyte for typical runs
  (e.g. ~10⁴ rows for a 10 s EPSC run) and well under 100 MB even for very long runs;
  baseline memory is dominated by the Qt/scientific-Python runtime, and CPU is low
  because the loop spends most of each tick waiting on VISA.

---

## 14. Context — Current Journal Revision

The manuscript is under peer review. Reviewer requests fall into two groups:
- **Experimental validation** (Reviewer #1; Reviewer #2-1 timing): connect real synaptic
  devices and provide measured EPSC/PPF/LTP/LTD examples, an optoelectronic example,
  electro-optical synchronization evidence, and a *quantitative* timing-error analysis.
  These require lab measurements with instruments.
- **Software documentation/engineering** (Reviewer #2-2..6): installation & dependency
  management, resource/scalability discussion, fault-handling discussion, abbreviation
  consistency, and English proofreading. These are addressable without re-measurement and
  are the subject of §10–§13 above plus the repository README and `requirements.txt`.

A v0.3.1 patch (this version) fixed two crash bugs in the data-save routine, removed a
dead Tk dependency, and made the settings path executable-aware for packaging.
