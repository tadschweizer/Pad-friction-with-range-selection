# force_plotter.py

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

def plot_individual(fp, res, save_dir, cm_lo, cm_hi, y_max, suffix):
    runs = range(1, len(res) + 1)
    avg = [r[0] for r in res]
    peak = [r[1] for r in res]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(runs, avg, marker="o", label="Average Force")
    ax.plot(runs, peak, marker="o", label="Peak Force")
    ax.set_xlabel("Run Number")
    ax.set_ylabel("Grams")
    title = f"Force Metrics (cm {cm_lo:.1f}-{cm_hi:.1f}) – {os.path.splitext(os.path.basename(fp))[0].replace('_',' ')} {suffix}"
    ax.set_title(title)
    ax.grid(True)
    ax.legend()
    ax.set_ylim(0, y_max)
    return fig
