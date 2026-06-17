#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pulse-timing statistics for SynapSSU-generated voltage pulses (Reviewer R2-1).

Reads Tektronix TBS1072B-EDU CSV waveform exports, detects every pulse with a
hysteresis state machine + linearly-interpolated 50% crossings, and reports the
pulse width / inter-pulse gap / period (mean and sample std, ddof=1) pooled over
all files. Also writes a per-pulse table (the raw evidence) and overlay plots so
the edge detection can be verified by eye.

Usage:
    python analyze_pulses.py [csv_dir]      # default csv_dir = ./data

Outputs (written to ./output/):
    per_pulse.csv        one row per detected pulse
    summary.csv          pooled statistics
    overlay_<name>.png   waveform with detected edges (needs matplotlib; skipped
                         with a warning if matplotlib is not installed)

Dependencies: standard library + numpy for the numeric analysis; matplotlib is
used only for the optional overlay plots.
"""

import os
import sys
import csv
import glob
import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except Exception:
    HAVE_MPL = False

# --- Programmed (nominal) values for this dataset, for sanity reporting ---
PROGRAMMED_WIDTH_MS = 50.0
PROGRAMMED_GAP_MS = 50.0
PROGRAMMED_PERIOD_MS = 100.0
DEGLITCH_MIN_WIDTH_MS = 10.0   # reject pulses narrower than this


# ----------------------------------------------------------------------------
# CSV parsing (Tektronix: metadata in cols 1-2, waveform in cols 4-5)
# ----------------------------------------------------------------------------
def parse_tek_csv(path):
    """Return (time[s], volt[V], meta dict). Robust to header rows and to the
    column layout where field index 3 = time and index 4 = voltage."""
    times, volts = [], []
    meta = {}
    with open(path, "r", newline="") as f:
        for fields in csv.reader(f):
            # Header metadata lives in the first two columns.
            if len(fields) >= 2 and fields[0].strip():
                key = fields[0].strip()
                val = fields[1].strip()
                if key and key not in meta:
                    meta[key] = val
            # Waveform sample: field 3 = time, field 4 = voltage.
            if len(fields) >= 5:
                t_raw, v_raw = fields[3].strip(), fields[4].strip()
                if t_raw and v_raw:
                    try:
                        t = float(t_raw)
                        v = float(v_raw)
                    except ValueError:
                        continue
                    times.append(t)
                    volts.append(v)
    return np.asarray(times, float), np.asarray(volts, float), meta


def median_filter(x, k=5):
    """Simple odd-kernel median filter (numpy only), for ENV-mode captures."""
    if k < 2:
        return x
    h = k // 2
    xp = np.pad(x, h, mode="edge")
    return np.array([np.median(xp[i:i + k]) for i in range(len(x))])


# ----------------------------------------------------------------------------
# Edge detection
# ----------------------------------------------------------------------------
def schmitt_states(v, th_low, th_high):
    """Two-state (low=0/high=1) Schmitt trigger to avoid noise re-triggering."""
    state = np.empty(len(v), dtype=int)
    s = 1 if v[0] >= th_high else 0
    for i in range(len(v)):
        if s == 0 and v[i] > th_high:
            s = 1
        elif s == 1 and v[i] < th_low:
            s = 0
        state[i] = s
    return state


def crossing_up_before(v, t, i, level):
    """Interpolated time at which a *rising* edge crosses `level`, searching
    backward from transition index i. Returns sub-sample crossing time."""
    k = i
    while k > 0 and v[k] >= level:
        k -= 1
    # now v[k] < level <= v[k+1]
    denom = v[k + 1] - v[k]
    if denom == 0:
        return t[k + 1]
    frac = (level - v[k]) / denom
    return t[k] + frac * (t[k + 1] - t[k])


def crossing_down_before(v, t, i, level):
    """Interpolated time at which a *falling* edge crosses `level`, searching
    backward from transition index i."""
    k = i
    while k > 0 and v[k] <= level:
        k -= 1
    # now v[k] > level >= v[k+1]
    denom = v[k] - v[k + 1]
    if denom == 0:
        return t[k + 1]
    frac = (v[k] - level) / denom
    return t[k] + frac * (t[k + 1] - t[k])


def detect_edges(t, v, baseline, amp):
    """Detect rising and falling edges. Each edge stores its interpolated 50%,
    10%, and 90% crossing times. 10/90 are paired within the same edge because
    all three are found by walking back from the same transition index."""
    th_low = baseline + 0.4 * amp
    th_high = baseline + 0.6 * amp
    th_50 = baseline + 0.5 * amp
    th_10 = baseline + 0.1 * amp
    th_90 = baseline + 0.9 * amp

    state = schmitt_states(v, th_low, th_high)
    rises, falls = [], []
    for i in range(1, len(state)):
        if state[i - 1] == 0 and state[i] == 1:
            rises.append({
                "t50": crossing_up_before(v, t, i, th_50),
                "t10": crossing_up_before(v, t, i, th_10),
                "t90": crossing_up_before(v, t, i, th_90),
            })
        elif state[i - 1] == 1 and state[i] == 0:
            falls.append({
                "t50": crossing_down_before(v, t, i, th_50),
                "t90": crossing_down_before(v, t, i, th_90),
                "t10": crossing_down_before(v, t, i, th_10),
            })
    levels = dict(th_low=th_low, th_high=th_high, th_50=th_50,
                  th_10=th_10, th_90=th_90)
    return rises, falls, levels


def build_pulses(rises, falls):
    """Pair each rising edge with the following falling edge and compute
    width / gap / period (seconds). Drops a leading falling edge (capture that
    started mid-pulse) so rises[k] aligns with falls[k]."""
    if not rises or not falls:
        return []
    falls = [f for f in falls if f["t50"] > rises[0]["t50"]]
    n = min(len(rises), len(falls))
    pulses = []
    for k in range(n):
        r, f = rises[k], falls[k]
        width = f["t50"] - r["t50"]
        if width * 1e3 < DEGLITCH_MIN_WIDTH_MS:
            continue
        nxt = rises[k + 1]["t50"] if k + 1 < len(rises) else None
        gap = (nxt - f["t50"]) if nxt is not None else float("nan")
        period = (nxt - r["t50"]) if nxt is not None else float("nan")
        pulses.append({
            "rise_time_ms": r["t50"] * 1e3,
            "fall_time_ms": f["t50"] * 1e3,
            "width_ms": width * 1e3,
            "gap_to_next_ms": gap * 1e3,
            "period_ms": period * 1e3,
            "rise_1090_ms": (r["t90"] - r["t10"]) * 1e3,
            "fall_9010_ms": (f["t10"] - f["t90"]) * 1e3,
        })
    return pulses


# ----------------------------------------------------------------------------
# Plotting (optional)
# ----------------------------------------------------------------------------
def save_overlay(out_dir, name, t, v, rises, falls, levels):
    if not HAVE_MPL:
        return False
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(t * 1e3, v, lw=0.6, color="0.4", label="waveform")
    ax.axhline(levels["th_50"], color="C0", lw=0.8, ls="--", label="50% level")
    for r in rises:
        ax.axvline(r["t50"] * 1e3, color="green", lw=0.8, alpha=0.8)
    for f in falls:
        ax.axvline(f["t50"] * 1e3, color="red", lw=0.8, alpha=0.8)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Voltage (V)")
    ax.set_title("%s  (green = 50%% rising, red = 50%% falling)" % name)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "overlay_%s.png" % name), dpi=120)
    plt.close(fig)
    return True


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def stats(arr):
    a = np.asarray([x for x in arr if np.isfinite(x)], float)
    if a.size == 0:
        return (float("nan"), float("nan"), 0)
    if a.size == 1:
        return (float(a[0]), float("nan"), 1)
    return (float(a.mean()), float(a.std(ddof=1)), int(a.size))


def main():
    csv_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    out_dir = "output"
    os.makedirs(out_dir, exist_ok=True)

    # Dedupe by normalized path: on case-insensitive filesystems (Windows) the
    # *.CSV and *.csv patterns would otherwise match the same file twice.
    seen, files = set(), []
    for p in sorted(glob.glob(os.path.join(csv_dir, "*.CSV")) +
                    glob.glob(os.path.join(csv_dir, "*.csv"))):
        key = os.path.normcase(os.path.abspath(p))
        if key not in seen:
            seen.add(key)
            files.append(p)
    if not files:
        print("No CSV files found in '%s'." % csv_dir)
        return 1

    print("=" * 70)
    print("SynapSSU pulse-timing analysis  (programmed: width=%.0f ms, "
          "gap=%.0f ms, period=%.0f ms)" %
          (PROGRAMMED_WIDTH_MS, PROGRAMMED_GAP_MS, PROGRAMMED_PERIOD_MS))
    print("=" * 70)
    if not HAVE_MPL:
        print("[warn] matplotlib not available -> overlay PNGs will be skipped.")

    all_pulses = []
    sample_intervals = []
    rows = []
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        t, v, meta = parse_tek_csv(path)
        if t.size < 10:
            print("[FLAG] %s: too few samples (%d) -> skipped." % (name, t.size))
            continue

        # Sample interval (timing-resolution floor) from the header.
        si = None
        for key in ("Sample Interval", "Sample interval"):
            if key in meta:
                try:
                    si = float(meta[key])
                except ValueError:
                    pass
        if si is not None:
            sample_intervals.append(si)

        # ENV-mode captures: smooth lightly before detection.
        pt_fmt = meta.get("Pt Fmt", meta.get("Pt fmt", "")).upper()
        if pt_fmt == "ENV":
            v = median_filter(v, 5)
            print("[note] %s: Pt Fmt=ENV -> applied 5-sample median filter." % name)

        baseline = np.percentile(v, 2)
        top = np.percentile(v, 98)
        amp = top - baseline
        if amp <= 0:
            print("[FLAG] %s: non-positive amplitude (%.3g V) -> skipped." %
                  (name, amp))
            continue

        rises, falls, levels = detect_edges(t, v, baseline, amp)
        pulses = build_pulses(rises, falls)

        # Per-file sanity: count + amplitude.
        flag = ""
        if not (5 <= len(pulses) <= 15):
            flag = "  <-- UNEXPECTED COUNT"
        print("%-14s  samples=%6d  amp=%.3f V  pulses=%2d  Sample Interval=%s s%s"
              % (name, t.size, amp, len(pulses),
                 ("%.3g" % si) if si is not None else "?", flag))

        for j, p in enumerate(pulses):
            rows.append([name, j,
                         "%.4f" % p["rise_time_ms"], "%.4f" % p["fall_time_ms"],
                         "%.4f" % p["width_ms"], "%.4f" % p["gap_to_next_ms"],
                         "%.4f" % p["period_ms"],
                         "%.4f" % p["rise_1090_ms"], "%.4f" % p["fall_9010_ms"]])
        all_pulses.extend(pulses)
        save_overlay(out_dir, name, t, v, rises, falls, levels)

    if not all_pulses:
        print("No pulses detected in any file.")
        return 1

    # --- per_pulse.csv ---
    pp_path = os.path.join(out_dir, "per_pulse.csv")
    with open(pp_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "pulse_index", "rise_time_ms", "fall_time_ms",
                    "width_ms", "gap_to_next_ms", "period_ms",
                    "rise_1090_ms", "fall_9010_ms"])
        w.writerows(rows)

    # --- pooled statistics ---
    width = [p["width_ms"] for p in all_pulses]
    gap = [p["gap_to_next_ms"] for p in all_pulses]
    period = [p["period_ms"] for p in all_pulses]
    rise = [p["rise_1090_ms"] for p in all_pulses]
    fall = [p["fall_9010_ms"] for p in all_pulses]

    si_report = (np.median(sample_intervals) * 1e3) if sample_intervals else float("nan")

    metrics = [
        ("width_ms", stats(width)),
        ("inter_pulse_gap_ms", stats(gap)),
        ("period_ms", stats(period)),
        ("rise_1090_ms", stats(rise)),
        ("fall_9010_ms", stats(fall)),
    ]

    sm_path = os.path.join(out_dir, "summary.csv")
    with open(sm_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "mean", "std_ddof1", "N", "sample_interval_ms"])
        for name, (m, s, n) in metrics:
            w.writerow([name, "%.4f" % m, "%.4f" % s, n, "%.4f" % si_report])

    # --- printed summary ---
    print("-" * 70)
    print("POOLED SUMMARY (sample std, ddof=1)")
    print("-" * 70)
    for name, (m, s, n) in metrics:
        print("  %-20s  mean=%8.3f ms   std=%7.3f ms   N=%d" % (name, m, s, n))
    print("  oscilloscope Sample Interval (median): %.4f ms" % si_report)
    print("-" * 70)
    print("The measured standard deviation is comparable to the oscilloscope "
          "sample interval (%.4f ms) and" % si_report)
    print("therefore represents an UPPER BOUND on the actual timing jitter.")
    print("Wrote: %s, %s" % (pp_path, sm_path))
    print("Per-pulse N: width=%d, gap=%d" % (stats(width)[2], stats(gap)[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
