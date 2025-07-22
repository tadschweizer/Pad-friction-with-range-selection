import streamlit as st
import tempfile
import os
import numpy as np
from force_plotter import load_raw_data, process_file, plot_individual
import plotly.graph_objects as go  # For combined plotting

st.set_page_config(page_title="Pad Friction with Range Selection", layout="wide")
st.title("Pad Friction – Force-vs-Cycle Analyzer")

# Predefined color bank
COLOR_BANK = [
    "#e6194b",  # red
    "#3cb44b",  # green
    "#ffe119",  # yellow
    "#4363d8",  # blue
    "#f58231",  # orange
    "#911eb4",  # purple
    "#46f0f0",  # cyan
    "#f032e6",  # magenta
    "#bcf60c",  # lime
    "#fabebe"   # pink
]

# Upload files
uploaded_files = st.file_uploader("Upload .xlsx files", type="xlsx", accept_multiple_files=True)

if uploaded_files:
    dfs = {}
    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        df = load_raw_data(tmp_path)
        dfs[file.name] = (df, tmp_path)

    max_cm = max(df["Position mm"].max() / 10.0 for df, _ in dfs.values())
    cm_lo, cm_hi = st.slider(
        "Select Centimeter Range", 0.0, float(round(max_cm, 1)),
        (0.0, float(round(max_cm, 1))), step=0.1
    )
    y_buffer = st.number_input("Add buffer to y-axis (grams)", 0, 50, 5)

    prefixes = sorted({name.split('_')[0] for name in dfs.keys()})
    st.subheader("Assign Colors to Groups from Bank")
    color_map = {}
    for i, prefix in enumerate(prefixes):
        # Cycle through COLOR_BANK if more prefixes than colors
        default = COLOR_BANK[i % len(COLOR_BANK)]
        key = f"color_{prefix}"
        # Select box for color choice
        color_map[prefix] = st.selectbox(
            f"Color for '{prefix}'",
            options=COLOR_BANK,
            index=COLOR_BANK.index(default),
            key=key
        )

    # Individual plots
    if st.button("Generate Individual Plots"):
        for label, (df, path) in dfs.items():
            results = process_file(path, cm_lo, cm_hi)
            if not results:
                st.warning(f"No usable data in {label}")
                continue
            avg_vals, peak_vals = zip(*[(r[0], r[1]) for r in results if not np.isnan(r[0])])
            y_max = max(avg_vals + peak_vals) + y_buffer
            fig = plot_individual(
                path, results,
                save_dir=None,
                cm_lo=cm_lo,
                cm_hi=cm_hi,
                y_max=y_max,
                suffix=""
            )
            st.subheader(label)
            st.pyplot(fig)

    # Combined average plot
    if st.button("Generate Combined Average Plot"):
        combined_fig = go.Figure()
        for label, (df, path) in dfs.items():
            results = process_file(path, cm_lo, cm_hi)
            if not results:
                continue
            full_positions = df["Position mm"] / 10.0
            mask = (full_positions >= cm_lo) & (full_positions <= cm_hi)
            positions = full_positions[mask].unique().tolist()
            avgs = [r[0] for r in results]
            prefix = label.split('_')[0]
            clr = color_map.get(prefix)
            combined_fig.add_trace(
                go.Scatter(
                    x=positions,
                    y=avgs,
                    mode='lines+markers',
                    name=label,
                    line=dict(color=clr),
                    marker=dict(color=clr)
                )
            )
        combined_fig.update_layout(
            title="Combined Average Force vs Position",
            xaxis_title="Position (cm)",
            yaxis_title="Average Force (g)",
            yaxis=dict(range=[0, None])
        )
        st.plotly_chart(combined_fig, use_container_width=True)

# Ensure `plotly` in requirements.txt
