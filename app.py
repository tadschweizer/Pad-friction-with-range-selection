import streamlit as st
import tempfile
import numpy as np
from force_plotter import load_raw_data, process_file, plot_individual
import plotly.graph_objects as go  # For combined plotting

st.set_page_config(page_title="Pad Friction with Range Selection", layout="wide")
st.title("Pad Friction – Force-vs-Cycle Analyzer")

# Predefined color bank with names and emojis
COLOR_BANK = [
    ("Red",     "#e6194b", "🔴"),
    ("Green",   "#3cb44b", "🟢"),
    ("Yellow",  "#ffe119", "🟡"),
    ("Blue",    "#4363d8", "🔵"),
    ("Orange",  "#f58231", "🟠"),
    ("Purple",  "#911eb4", "🟣"),
    ("Cyan",    "#46f0f0", "🔷"),
    ("Magenta", "#f032e6", "🟪"),
    ("Lime",    "#bcf60c", "🟩"),
    ("Pink",    "#fabebe", "🩷")
]

# Upload files
uploaded_files = st.file_uploader("Upload .xlsx files", type="xlsx", accept_multiple_files=True)
if uploaded_files:
    # Load data
    dfs = {}
    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        df = load_raw_data(tmp_path)
        dfs[file.name] = (df, tmp_path)

    # Range selector
    max_cm = max(df["Position mm"].max() / 10.0 for df, _ in dfs.values())
    cm_lo, cm_hi = st.slider(
        "Select Centimeter Range", 0.0, float(round(max_cm, 1)),
        (0.0, float(round(max_cm, 1))), step=0.1
    )

    # Fixed buffer
    y_buffer = 5

    # Color assignment
    prefixes = sorted({name.split('_')[0] for name in dfs.keys()})
    st.subheader("Assign Colors to Groups")
    color_map = {}
    for idx, prefix in enumerate(prefixes):
        key = f"color_{prefix}"
        # Build options with emoji + name
        options = [f"{emoji} {name}" for name, _, emoji in COLOR_BANK]
        # Default based on index
        default_idx = idx % len(COLOR_BANK)
        choice = st.radio(
            f"{prefix}", options,
            index=default_idx, key=key, horizontal=True
        )
        # Extract name and find hex
        selected_name = choice.split(' ', 1)[1]
        hex_code = next(hex for name, hex, _ in COLOR_BANK if name == selected_name)
        color_map[prefix] = hex_code

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
            positions = (df["Position mm"] / 10.0)[
                (df["Position mm"]/10.0 >= cm_lo) & (df["Position mm"]/10.0 <= cm_hi)
            ].unique().tolist()
            avgs = [r[0] for r in results]
            prefix = label.split('_')[0]
            clr = color_map[prefix]
            combined_fig.add_trace(
                go.Scatter(
                    x=positions,
                    y=avgs,
                    mode='lines+markers',
                    name=label,
                    line=dict(color=clr, width=2),
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
