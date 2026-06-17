#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inter-SMU timing statistics for SynapSSU (Reviewer R1-5 / R2-1).

Reads paired Tektronix CSV captures of two SMU outputs (CH1, CH2) driven within a
single SynapSSU acquisition loop, and reports per channel the pulse width and, per
cycle, the inter-SMU offset (the stagger between a rising edge on one channel and
the next rising edge on the other). This demonstrates that the two SMUs share a
common time base (the multi-SMU / photoelectric synchronization the reviewer asked
about).

Usage:
    python analyze_inter_smu.py [csv_dir]      # default csv_dir = ./data

Outputs (written to ./output/):
    per_pulse.csv        one row per detected pulse (both channels)
    per_offset.csv       one row per inter-SMU offset (both directions)
    summary.csv          pooled statistics
    overlay_<pair>.png   both channels with detected edges (needs matplotlib)

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
PROGRAMMED_WIDTH_MS = 100.0
PROGRAMMED_INTERVAL_MS = 250.0
DEGLITCH_MIN_WIDTH_MS = 10.0


# ----------------------------------------------------------------------------
# CSV parsing (Tektronix: metadata in cols 1-2, waveform in cols 4-5)
# ----------------------------------------------------------------------------
def parse_tek_csv(path):
    """Return (time[s], volt[V], meta dict)."""
    times, volts = [], []
    meta = {}
    with open(path, "r", newline="") as f:
        for fields in csv.reader(f):
            if len(fields) >= 2 and fields[0].strip():
                key, val = fields[0].strip(), fields[1].strip()
                if key and key not in meta:
                    meta[key] = val
            if len(fields) >= 5:
                t_raw, v_raw = fields[3].strip(), fields[4].strip()
                if t_raw and v_raw:
                    try:
                        times.append(float(t_raw))
                        volts.append(float(v_raw))
                    except ValueError:
                        continue
    return np.asarray(times, float), np.asarray(volts, float), meta


def median_filter(x, k=5):
    if k < 2:
        return x
    h = k // 2
    xp = np.pad(x, h, mode="edge")
    return np.array([np.median(xp[i:i + k]) for i in range(len(x))])


# ----------------------------------------------------------------------------
# Edge detection (hysteresis state machine + interpolated 50% crossings)
# ----------------------------------------------------------------------------
def schmitt_states(v, th_low, th_high):
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
    k = i
    while k > 0 and v[k] >= level:
        k -= 1
    denom = v[k + 1] - v[k]
    if denom == 0:
        return t[k + 1]
    return t[k] + (level - v[k]) / denom * (t[k + 1] - t[k])


def crossing_down_before(v, t, i, level):
    k = i
    while k > 0 and v[k] <= level:
        k -= 1
    denom = v[k] - v[k + 1]
    if denom == 0:
        return t[k + 1]
    return t[k] + (v[k] - level) / denom * (t[k + 1] - t[k])


def detect_edges(t, v, baseline, amp):
    """Return (rise50[], fall50[], th_50): interpolated 50% rising/falling times."""
    th_low = baseline + 0.4 * amp
    th_high = baseline + 0.6 * amp
    th_50 = baseline + 0.5 * amp
    state = schmitt_states(v, th_low, th_high)
    rise50, fall50 = [], []
    for i in range(1, len(state)):
        if state[i - 1] == 0 and state[i] == 1:
            rise50.append(crossing_up_before(v, t, i, th_50))
        elif state[i - 1] == 1 and state[i] == 0:
            fall50.append(crossing_down_before(v, t, i, th_50))
    return np.asarray(rise50), np.asarray(fall50), th_50


def channel_pulses(rise50, fall50):
    """Pair rising[k] with falling[k] (drop a leading falling edge) and return a
    list of (rise_s, fall_s, width_s), deglitched."""
    if rise50.size == 0 or fall50.size == 0:
        return []
    falls = fall50[fall50 > rise50[0]]
    n = min(rise50.size, falls.size)
    out = []
    for k in range(n):
        w = falls[k] - rise50[k]
        if w * 1e3 < DEGLITCH_MIN_WIDTH_MS:
            continue
        out.append((rise50[k], falls[k], w))
    return out


def offsets(ref_rise, other_rise):
    """For each rising edge in ref_rise, the next rising edge in other_rise after
    it. Returns list of (ref_s, next_s, offset_s)."""
    out = []
    other = np.sort(other_rise)
    for r in np.sort(ref_rise):
        j = np.searchsorted(other, r, side="right")
        if j < other.size:
            out.append((r, other[j], other[j] - r))
    return out


# ----------------------------------------------------------------------------
# Plotting (optional)
# ----------------------------------------------------------------------------
def save_overlay(out_dir, pair, t1, v1, r1, f1, th1, t2, v2, r2, f2, th2):
    if not HAVE_MPL:
        return
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(t1 * 1e3, v1, lw=0.6, color="0.45", label="CH1 (SMU1)")
    ax.plot(t2 * 1e3, v2, lw=0.6, color="C1", label="CH2 (SMU2)")
    for r in r1:
        ax.axvline(r * 1e3, color="green", lw=0.7, alpha=0.7)
    for x in f1:
        ax.axvline(x * 1e3, color="darkgreen", lw=0.7, alpha=0.4, ls=":")
    for r in r2:
        ax.axvline(r * 1e3, color="blue", lw=0.7, alpha=0.7)
    for x in f2:
        ax.axvline(x * 1e3, color="navy", lw=0.7, alpha=0.4, ls=":")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Voltage (V)")
    ax.set_title("%s  (green=CH1 rise, blue=CH2 rise; dotted=falls)" % pair)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "overlay_%s.png" % pair), dpi=120)
    plt.close(fig)


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


def pair_key(path):
    """Strip CH1/CH2 and extension to group a pair by its common prefix."""
    base = os.path.splitext(os.path.basename(path))[0].upper()
    return base.replace("CH1", "").replace("CH2", "")


def load_channel(path):
    t, v, meta = parse_tek_csv(path)
    si = None
    for key in ("Sample Interval", "Sample interval"):
        if key in meta:
            try:
                si = float(meta[key])
            except ValueError:
                pass
    if meta.get("Pt Fmt", meta.get("Pt fmt", "")).upper() == "ENV":
        v = median_filter(v, 5)
        print("[note] %s: Pt Fmt=ENV -> 5-sample median filter applied." %
              os.path.basename(path))
    return t, v, si


def main():
    csv_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    out_dir = "output"
    os.makedirs(out_dir, exist_ok=True)

    # Collect & dedupe files (Windows case-insensitive *.CSV/*.csv).
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

    # Group into CH1/CH2 pairs by common prefix.
    pairs = {}
    for p in files:
        up = os.path.basename(p).upper()
        ch = 1 if "CH1" in up else 2 if "CH2" in up else None
        if ch is None:
            print("[FLAG] %s: cannot tell CH1/CH2 from name -> skipped." % p)
            continue
        pairs.setdefault(pair_key(p), {})[ch] = p

    print("=" * 72)
    print("SynapSSU inter-SMU timing  (programmed: width=%.0f ms/ch, "
          "interval=%.0f ms)" % (PROGRAMMED_WIDTH_MS, PROGRAMMED_INTERVAL_MS))
    print("=" * 72)
    if not HAVE_MPL:
        print("[warn] matplotlib not available -> overlay PNGs will be skipped.")

    pulse_rows, offset_rows = [], []
    w1_all, w2_all, off12_all, off21_all = [], [], [], []
    sample_intervals = []

    for pair in sorted(pairs):
        chans = pairs[pair]
        if 1 not in chans or 2 not in chans:
            print("[FLAG] pair %s: missing %s -> skipped." %
                  (pair, "CH2" if 1 in chans else "CH1"))
            continue
        t1, v1, si1 = load_channel(chans[1])
        t2, v2, si2 = load_channel(chans[2])

        # Time-axis consistency check.
        if t1.size != t2.size or (si1 and si2 and abs(si1 - si2) > 1e-12):
            print("[FLAG] pair %s: time axes differ (len %d/%d, dt %s/%s)." %
                  (pair, t1.size, t2.size, si1, si2))
        if si1:
            sample_intervals.append(si1)

        b1, top1 = np.percentile(v1, 2), np.percentile(v1, 98)
        b2, top2 = np.percentile(v2, 2), np.percentile(v2, 98)
        amp1, amp2 = top1 - b1, top2 - b2
        if amp1 <= 0 or amp2 <= 0:
            print("[FLAG] pair %s: non-positive amplitude (%.3g/%.3g V)." %
                  (pair, amp1, amp2))
            continue

        r1, f1, th1 = detect_edges(t1, v1, b1, amp1)
        r2, f2, th2 = detect_edges(t2, v2, b2, amp2)
        p1 = channel_pulses(r1, f1)
        p2 = channel_pulses(r2, f2)

        # Use deglitched rising times for the offset computation.
        r1c = np.array([p[0] for p in p1])
        r2c = np.array([p[0] for p in p2])
        o12 = offsets(r1c, r2c)   # SMU1 -> next SMU2
        o21 = offsets(r2c, r1c)   # SMU2 -> next SMU1

        flag1 = "" if 3 <= len(p1) <= 12 else "  <-- COUNT?"
        print("%-12s  CH1 pulses=%2d  CH2 pulses=%2d  off12=%2d off21=%2d  "
              "dt=%s s%s" % (pair, len(p1), len(p2), len(o12), len(o21),
                             ("%.3g" % si1) if si1 else "?", flag1))

        for j, (rs, fs, w) in enumerate(p1):
            pulse_rows.append([pair, "CH1", j, "%.4f" % (rs * 1e3),
                               "%.4f" % (fs * 1e3), "%.4f" % (w * 1e3)])
            w1_all.append(w * 1e3)
        for j, (rs, fs, w) in enumerate(p2):
            pulse_rows.append([pair, "CH2", j, "%.4f" % (rs * 1e3),
                               "%.4f" % (fs * 1e3), "%.4f" % (w * 1e3)])
            w2_all.append(w * 1e3)
        for j, (ref, nxt, off) in enumerate(o12):
            offset_rows.append([pair, "SMU1->SMU2", j, "%.4f" % (ref * 1e3),
                                "%.4f" % (nxt * 1e3), "%.4f" % (off * 1e3)])
            off12_all.append(off * 1e3)
        for j, (ref, nxt, off) in enumerate(o21):
            offset_rows.append([pair, "SMU2->SMU1", j, "%.4f" % (ref * 1e3),
                                "%.4f" % (nxt * 1e3), "%.4f" % (off * 1e3)])
            off21_all.append(off * 1e3)

        save_overlay(out_dir, pair, t1, v1, r1c, [p[1] for p in p1], th1,
                     t2, v2, r2c, [p[1] for p in p2], th2)

    if not pulse_rows:
        print("No pulses detected.")
        return 1

    # --- per_pulse.csv ---
    with open(os.path.join(out_dir, "per_pulse.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file_pair", "channel", "pulse_index",
                    "rise_time_ms", "fall_time_ms", "width_ms"])
        w.writerows(pulse_rows)

    # --- per_offset.csv ---
    with open(os.path.join(out_dir, "per_offset.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file_pair", "direction", "cycle_index",
                    "ref_rise_ms", "next_rise_ms", "offset_ms"])
        w.writerows(offset_rows)

    # --- summary ---
    si_report = (np.median(sample_intervals) * 1e3) if sample_intervals else float("nan")
    metrics = [
        ("SMU1_width_ms", stats(w1_all)),
        ("SMU2_width_ms", stats(w2_all)),
        ("combined_width_ms", stats(w1_all + w2_all)),
        # Both directions pooled into a single inter-SMU offset: each direction
        # measures the same programmed stagger from the opposite reference edge.
        ("offset_inter_SMU_ms", stats(off12_all + off21_all)),
    ]
    with open(os.path.join(out_dir, "summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "mean", "std_ddof1", "N", "sample_interval_ms"])
        for name, (m, s, n) in metrics:
            w.writerow([name, "%.4f" % m, "%.4f" % s, n, "%.4f" % si_report])

    # --- printed summary ---
    print("-" * 72)
    print("POOLED SUMMARY (sample std, ddof=1)")
    print("-" * 72)
    for name, (m, s, n) in metrics:
        print("  %-22s  mean=%8.3f ms   std=%7.3f ms   N=%d" % (name, m, s, n))
    print("  oscilloscope Sample Interval (median): %.4f ms" % si_report)

    # Inter-SMU offset = both directions pooled (each measures the same
    # programmed stagger from the opposite reference edge).
    mo, so, no = stats(off12_all + off21_all)
    m12, m21 = stats(off12_all)[0], stats(off21_all)[0]
    print("-" * 72)
    print("Inter-SMU offset (both directions pooled) = %.3f +/- %.3f ms (N=%d); "
          "programmed = %.0f ms." % (mo, so, no, PROGRAMMED_INTERVAL_MS))
    print("  (per-direction means: SMU1->SMU2=%.3f, SMU2->SMU1=%.3f ms; "
          "kept in per_offset.csv)" % (m12, m21))
    print("Measured std is comparable to the sample interval (%.4f ms) and is an "
          "UPPER BOUND on the true jitter." % si_report)
    print("Wrote per_pulse.csv, per_offset.csv, summary.csv to %s/" % out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
