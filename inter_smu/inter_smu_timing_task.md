# Task: Inter-SMU Timing Statistics for SynapSSU (Reviewer R1-5 / R2-1)

## Goal

From paired oscilloscope CSV captures of two SMU outputs driven within a single
SynapSSU acquisition loop, extract, for every pulse, each channel's **pulse width**,
and for every cycle the **inter-SMU offset** (the stagger between a pulse on one
channel and the corresponding pulse on the other channel). Then compute the mean
and sample standard deviation across all pulses/cycles pooled from all file pairs.

This demonstrates that the two SMUs are coordinated on a common time base
(the photoelectric / multi-SMU synchronization the reviewer asked about).

The output must be **reproducible and independently verifiable**: (1) a script
anyone can re-run, (2) a per-pulse / per-cycle table showing every measured value
behind the statistics, and (3) overlay plots proving the edge detection is correct.

## Input data

- Tektronix TBS1072B-EDU CSV exports, in **CH1/CH2 pairs** captured simultaneously:
  e.g. `F00XXCH1.CSV` (SMU1) and `F00XXCH2.CSV` (SMU2). Both channels of a pair
  share the same time base.
- This is the **inter-SMU experiment**: programmed pulse width = 100 ms on each
  channel, programmed inter-pulse interval = 250 ms. The two channels fire in a
  staggered (non-overlapping) pattern.
- CSV format (do not assume a clean 2-column file):
  - First ~18 rows carry instrument metadata in columns 1-2 (`Record Length`,
    `Sample Interval`, `Source`, `Pt Fmt`, ...).
  - **Waveform data is in columns 4 and 5** of every row: column 4 = time (s),
    column 5 = voltage (V). Column 3 is empty.
  - Parse robustly: take field index 3 as time, field index 4 as voltage, skipping
    rows where these are empty or non-numeric.
  - Read `Sample Interval` from the header and report it (timing-resolution floor).
  - Confirm `Pt Fmt` is `Y`. If `ENV` (envelope mode), median-filter (kernel ~5)
    before detection and flag it.
  - Both files in a pair must share the same time axis. Verify the time arrays match
    (same length, same sample interval); if not, flag it.

## Edge-detection algorithm (fix this exactly, so results are reproducible)

Apply per channel, independently:

1. Levels per file: `baseline = 2nd percentile of V`, `top = 98th percentile`,
   `amplitude = top - baseline`.
2. Hysteresis thresholds: `th_low = baseline + 0.4*amplitude`,
   `th_high = baseline + 0.6*amplitude`; `th_50 = baseline + 0.5*amplitude`.
3. Two-state machine (low/high) with the hysteresis thresholds.
4. Compute **linearly interpolated** 50% crossing times (sub-sample resolution).
5. Reject pulses with 50%-width < 10 ms (deglitch).
6. Per channel, per pulse: **width** = (50% fall) - (preceding 50% rise).

## Inter-SMU offset (the key cross-channel metric)

After detecting the 50% rising-edge times for both channels:

- Let `r1[]` = sorted 50% rising times of SMU1 (CH1),
  `r2[]` = sorted 50% rising times of SMU2 (CH2).
- For each rising edge in `r1`, find the **next** rising edge in `r2` that occurs
  after it, and record `offset_12 = (that r2) - (this r1)`.
- Also compute the reverse: for each `r2`, the next `r1` after it, `offset_21`.
- Report both directions separately (the staggered pattern is asymmetric: the two
  offsets should sum to ~one period). State which one corresponds to the
  programmed 250 ms interval.
- The reproducibility of these offsets across cycles (their std) is the headline
  inter-SMU synchronization number.

## Required outputs

Create all of these in an `output/` folder:

1. **`analyze_inter_smu.py`** — full self-contained script (standard library +
   numpy only). Takes a folder of CSVs, auto-pairs `*CH1.CSV` with the matching
   `*CH2.CSV` by filename prefix, prints the summary, writes the files below.
   Runnable as `python analyze_inter_smu.py <csv_dir>`.

2. **`per_pulse.csv`** — one row per detected pulse:
   `file_pair, channel, pulse_index, rise_time_ms, fall_time_ms, width_ms`.

3. **`per_offset.csv`** — one row per measured inter-SMU offset:
   `file_pair, direction (SMU1->SMU2 or SMU2->SMU1), cycle_index,
   ref_rise_ms, next_rise_ms, offset_ms`.
   This is the raw evidence behind the synchronization statistic.

4. **`summary.csv`** and printed summary — pooled across all file pairs:
   - SMU1 width: mean, sample std (ddof=1), N
   - SMU2 width: mean, sample std (ddof=1), N
   - combined width: mean, std, N
   - offset SMU1->SMU2: mean, std, N
   - offset SMU2->SMU1: mean, std, N
   - report the `Sample Interval` alongside (measured std expected to be comparable).

5. **`overlay_<pair>.png`** for each file pair — **both** channels' raw waveforms
   on the same time axis (different colors), with detected 50% rising and falling
   edges marked, so the cross-channel timing can be verified by eye. Draw th_50.

## Reporting / sanity checks (print to log)

- Total pulses pooled per channel, and total offsets pooled per direction (N).
- Per-pair pulse count per channel and offset count.
- Flag any pair with mismatched time axes, unexpected pulse count, or amplitude.
- State explicitly: programmed width = 100 ms, programmed interval = 250 ms.
- Note: "The measured standard deviation is comparable to the oscilloscope sample
  interval (X ms) and therefore represents an upper bound on the actual timing jitter."

## Notes / things to get right

- Sample standard deviation (ddof=1).
- Width at 50% (rising/falling edge delays cancel, so finite analog edges do not
  bias the width).
- The inter-SMU offset is the cross-channel quantity that demonstrates
  synchronization. Keep the two directions separate and label clearly which equals
  the programmed 250 ms gap.
- Both channels are read within the same acquisition loop, so a small, reproducible
  offset is the expected and desired result. Do not "correct" or zero it.
- Keep the code readable and commented for repository deposit and third-party reuse.

## Cross-validation reminder (for the human, not the script)

Before using numbers in the manuscript:
- Re-run the script yourself and confirm the printed stats.
- Read 2-3 offsets directly off the oscilloscope (cursor between the two channels'
  rising edges) and check against `per_offset.csv`.
- Open `per_pulse.csv` / `per_offset.csv` and confirm values are sensible
  (widths ~100 ms, the 250 ms-direction offset ~250 ms).
