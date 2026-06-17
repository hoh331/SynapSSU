# SynapSSU Pulse-Timing Analysis (Reviewer R2-1)

Reproducible extraction of **pulse width** and **inter-pulse gap** (and period)
from oscilloscope captures of SynapSSU-generated voltage pulses, with mean and
sample standard deviation (ddof=1) pooled across all captures.

## Folder layout
```
timing_analysis/
├─ analyze_pulses.py        # the analysis script (stdlib + numpy; matplotlib optional)
├─ timing_analysis_task.md  # the full task specification / method
├─ data/                    # <-- put the Tektronix *.CSV captures here
└─ output/                  # generated: per_pulse.csv, summary.csv, overlay_*.png
```

## How to run
```
cd timing_analysis
python analyze_pulses.py data
```
(`data` is the default, so `python analyze_pulses.py` also works.)

## Outputs (in `output/`)
- **`per_pulse.csv`** — one row per detected pulse (rise/fall times, width, gap,
  period, 10–90 rise, 90–10 fall). The raw evidence behind every statistic.
- **`summary.csv`** + printed summary — pooled mean / std (ddof=1) / N for width,
  inter-pulse gap, period, rise, fall, plus the oscilloscope sample interval.
- **`overlay_<name>.png`** — waveform with detected 50% rising (green) and falling
  (red) edges marked, for visual verification. (Requires matplotlib; skipped with
  a warning otherwise.)

## Method (summary)
Per-file signal levels from the 2nd/98th percentiles; hysteresis (40%/60%) state
machine to find edges; linearly-interpolated 50% crossings for sub-sample timing;
width = falling50% − rising50% (rise/fall delays cancel at 50%); pulses narrower
than 10 ms rejected as glitches. Rise (10–90%) and fall (90–10%) reported
separately and never folded into the width. See `timing_analysis_task.md` for the
exact, fixed algorithm.

## Note on dependencies
The numeric analysis uses only the standard library + numpy. The optional overlay
plots use matplotlib; if it is not installed the statistics are still produced and
only the PNGs are skipped.

## Cross-validation before quoting numbers in the manuscript
1. Re-run the script and confirm the printed stats.
2. Read 2–3 pulse widths with the scope's own measurement cursor; check against
   `per_pulse.csv`.
3. Open `per_pulse.csv` and confirm values are physically sensible (widths ~50 ms,
   gaps ~50 ms).
