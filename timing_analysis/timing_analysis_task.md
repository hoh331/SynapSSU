# Task: Oscilloscope Pulse-Timing Statistics for SynapSSU (Reviewer R2-1)

## Goal

From a set of oscilloscope CSV captures of SynapSSU-generated voltage pulses,
extract **pulse width** and **inter-pulse gap** (and period) for every individual
pulse, then compute the mean and standard deviation across all pulses pooled from
all files.

The output must be **reproducible and independently verifiable**. We are not
reporting "a number"; we are producing (1) a script anyone can re-run, (2) a
per-pulse table showing every measured value behind the statistics, and (3)
overlay plots proving the edge detection is correct. The statistics in the paper
must be traceable to these artifacts.

## Input data

- Tektronix TBS1072B-EDU CSV exports. There are ~10 files, named like
  `F00XXCH1.CSV` (channel 1 = the pulsing SMU output).
- These are the **50 ms experiment**: programmed pulse width = 50 ms,
  programmed inter-pulse gap = 50 ms (period = 100 ms).
- CSV format (important, do not assume a clean 2-column file):
  - The first ~18 rows carry instrument metadata in columns 1-2
    (e.g. `Record Length`, `Sample Interval`, `Trigger Point`, `Source`,
    `Vertical Scale`, `Model Number`, ...).
  - The **waveform data is in columns 4 and 5** of every row: column 4 = time (s),
    column 5 = voltage (V). Column 3 is empty.
  - Parse robustly: for each row, take field index 3 as time and field index 4 as
    voltage, skipping any row where these are empty or non-numeric.
  - Read `Sample Interval` from the header and report it (used as the timing-resolution
    floor, see below). Confirm `Pt Fmt` is `Y` (normal). If any file is `ENV`
    (envelope mode), apply a small median filter (kernel ~5 samples) before edge
    detection and flag it in the log.

## Edge-detection algorithm (fix this exactly, so results are reproducible)

1. Determine signal levels per file: `baseline = 2nd percentile of V`,
   `top = 98th percentile of V`, `amplitude = top - baseline`.
2. Thresholds: `th_low = baseline + 0.4*amplitude`,
   `th_high = baseline + 0.6*amplitude` (hysteresis),
   `th_50 = baseline + 0.5*amplitude`.
3. Walk the samples with a two-state machine (low/high) using the hysteresis
   thresholds to avoid noise re-triggering.
4. For each detected crossing, compute the **linearly interpolated** crossing time
   at the 50% level (interpolate between the two bracketing samples), not the raw
   sample time. This gives sub-sample resolution.
5. Reject any pulse whose 50%-width is < 10 ms (deglitch).
6. Per pulse, define:
   - **width** = (50% falling time) - (preceding 50% rising time)
   - **inter-pulse gap** = (next 50% rising time) - (current 50% falling time)
   - **period** = (next 50% rising time) - (current 50% rising time)
7. Edge transition time (report separately, do not mix into width):
   **rise (10-90%)** and **fall (90-10%)** using `th_10 = baseline+0.1*amplitude`
   and `th_90 = baseline+0.9*amplitude`. Pair each 10% and 90% crossing **within the
   same edge** (nearest crossing on the correct side of the corresponding 50%
   crossing) so edges are not mismatched across different pulses.

## Required outputs

Create all of these in an `output/` folder:

1. **`analyze_pulses.py`** — the full, self-contained analysis script. Standard
   library + numpy only. Takes a folder of CSVs as argument, prints the summary,
   and writes the files below. Must be runnable as `python analyze_pulses.py <csv_dir>`.

2. **`per_pulse.csv`** — one row per detected pulse, with columns:
   `file, pulse_index, rise_time_ms, fall_time_ms, width_ms, gap_to_next_ms,
   period_ms, rise_1090_ms, fall_9010_ms`.
   This is the raw evidence behind every statistic.

3. **`summary.csv`** and printed summary — pooled across all files:
   - width: mean, sample std (ddof=1), N
   - inter-pulse gap: mean, sample std (ddof=1), N
   - period: mean, sample std (ddof=1), N
   - rise (10-90%): mean, std, N
   - fall (90-10%): mean, std, N
   - report the oscilloscope `Sample Interval` (e.g. 0.4 ms) alongside, since the
     measured std is expected to be comparable to it.

4. **`overlay_<filename>.png`** for each file — the raw waveform with the detected
   50% rising edges and falling edges marked (e.g. vertical lines or dots), so the
   detection can be verified by eye. Also draw the th_50 level.

## Reporting / sanity checks (print these to the log)

- Total number of pulses pooled (N) for width and for gap.
- Per-file pulse count (should be ~10 each for a 1 s window at 100 ms period).
- Flag any file that yields an unexpected pulse count or amplitude.
- State explicitly: programmed width = 50 ms, programmed gap = 50 ms.
- Note in the log: "The measured standard deviation is comparable to the
  oscilloscope sample interval (X ms) and therefore represents an upper bound on
  the actual timing jitter."

## Notes / things to get right

- Use **sample** standard deviation (ddof=1), not population std.
- Do not report rise/fall as part of width. Width is at 50%, where rising and
  falling delays cancel.
- If the 50 ms data was captured under open-circuit vs under a load, that only
  affects the edge (rise/fall) interpretation, not the 50% width/gap. Record
  whichever condition applies in the log so it can be stated in the manuscript.
- Keep the code readable and commented. It will be referenced in the paper and may
  be deposited in the repository, so a third party should be able to re-run it and
  reproduce the exact numbers.

## Cross-validation reminder (for the human, not the script)

After running, verify independently before using numbers in the manuscript:
- Re-run the script yourself and confirm the printed stats.
- Read the width of 2-3 pulses directly with the oscilloscope's own measurement
  function and check they match `per_pulse.csv`.
- Open `per_pulse.csv` and confirm the per-pulse values are physically sensible
  (all widths ~50 ms, gaps ~50 ms).
