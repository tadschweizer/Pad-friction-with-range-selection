# -*- coding: utf-8 -*-
"""
Force‑vs‑Cycle Plotter – **V2.3.2**
----------------------------------
* Completes the earlier truncation at the very end of the main script.
* The script is now fully runnable without syntax errors.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

Y_BUFFER_G = 5  # grams of head‑room on the y‑axis

# ---------------------------------------------------------------------
# Spreadsheet helpers
# ---------------------------------------------------------------------

def load_raw_data(file_path: str, sheet: str = "Raw Data") -> pd.DataFrame:
    raw = pd.read_excel(file_path, sheet_name=sheet, header=None, engine="openpyxl")
    header_idx = next((i for i, r in raw.iterrows() if r.astype(str).str.contains(r"Position\s*mm", regex=True).any()), None)
    if header_idx is None:
        raise ValueError(f"{os.path.basename(file_path)} – missing 'Position mm' header")
    header = [str(c).strip() for c in raw.iloc[header_idx]]
    df = raw.iloc[header_idx + 1 :].reset_index(drop=True)
    df.columns = header
    for col in ("Position mm", "Pull Force g", "Clamp Force g"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Position mm"]).reset_index(drop=True)
    return df


def find_delimiters(df: pd.DataFrame):
    return df.index[df["Position mm"] == 0].tolist()


def get_global_max_run_length(files):
    longest = float("-inf")
    for fp in files:
        try:
            df = load_raw_data(fp)
        except Exception:
            continue
        delim = find_delimiters(df)
        if not delim:
            continue
        delim.append(len(df))
        for s, e in zip(delim[:-1], delim[1:]):
            longest = max(longest, df.iloc[s:e]["Position mm"].max() / 10.0)
    return None if longest == float("-inf") else longest

# ---------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------

def get_cm_range(root, valid_max):
    out = [None, None]

    def ok():
        try:
            lo, hi = float(min_entry.get()), float(max_entry.get())
            if lo < 0 or hi > valid_max or lo >= hi:
                raise ValueError
            out[:] = [lo, hi]
            dialog.destroy()
        except ValueError:
            messagebox.showerror("Invalid", f"Enter numbers 0–{valid_max:.2f}, min < max", parent=dialog)

    dialog = Toplevel(root)
    dialog.title("Centimetre Range"); dialog.grab_set(); dialog.focus_set()
    tk.Label(dialog, text=f"Valid: 0 to {valid_max:.2f} cm").grid(row=0, column=0, columnspan=2, pady=10)
    tk.Label(dialog, text="Min cm:").grid(row=1, column=0); min_entry = tk.Entry(dialog); min_entry.grid(row=1, column=1); min_entry.insert(0, "0.00")
    tk.Label(dialog, text="Max cm:").grid(row=2, column=0); max_entry = tk.Entry(dialog); max_entry.grid(row=2, column=1); max_entry.insert(0, f"{valid_max:.2f}")
    tk.Button(dialog, text="OK", command=ok).grid(row=3, column=0, columnspan=2, pady=10)
    root.wait_window(dialog)
    return out[0], out[1]

# ---------------------------------------------------------------------
# Core analysis helpers
# ---------------------------------------------------------------------

def process_file(fp: str, cm_lo: float, cm_hi: float):
    try:
        df = load_raw_data(fp)
    except Exception as e:
        print(f"{os.path.basename(fp)} – {e}")
        return []

    delim = find_delimiters(df)
    if not delim:
        return []
    delim.append(len(df))

    results = []
    for s, e in zip(delim[:-1], delim[1:]):
        run = df.iloc[s:e].copy()
        run["cm"] = run["Position mm"] / 10.0
        win = run[(run["cm"] >= cm_lo) & (run["cm"] <= cm_hi)]
        if win.empty:
            results.append((np.nan, np.nan))
        else:
            results.append((win["Pull Force g"].mean(), win["Pull Force g"].max()))
    return results

# ---------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------

def plot_individual(fp, res, save_dir, cm_lo, cm_hi, y_max, suffix):
    runs = range(1, len(res) + 1)
    avg = [r[0] for r in res]
    peak = [r[1] for r in res]
    plt.figure(figsize=(10, 6))
    plt.plot(runs, avg, marker="o", label="Average Force")
    plt.plot(runs, peak, marker="o", label="Peak Force")
    plt.xlabel("Run Number"); plt.ylabel("Grams")
    title = f"Force Metrics (cm {cm_lo:.1f}-{cm_hi:.1f}) – {os.path.splitext(os.path.basename(fp))[0].replace('_',' ')} {suffix}"
    plt.title(title); plt.grid(True); plt.legend(); plt.ylim(0, y_max)
    plt.savefig(os.path.join(save_dir, os.path.basename(fp).replace('.xlsx', '.png')), bbox_inches="tight")
    plt.close()


def plot_design(design, runs, avg, peak, save_dir, cm_lo, cm_hi, y_max, suffix):
    plt.figure(figsize=(10, 6))
    plt.plot(runs, avg, marker="o", label="Average of Average Force")
    plt.plot(runs, peak, marker="o", label="Average of Peak Force")
    plt.xlabel("Run Number"); plt.ylabel("Grams")
    plt.title(f"{design} – Combined Metrics (cm {cm_lo:.1f}-{cm_hi:.1f}) {suffix}")
    plt.grid(True); plt.legend(); plt.ylim(0, y_max)
    plt.savefig(os.path.join(save_dir, f"{design}_combined_{suffix.lower()}.png"), bbox_inches="tight")
    plt.close()
