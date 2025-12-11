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
    ("Pink",    "#fabebe", "🩷"),
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

    # Range selector (position-based filtering)
    max_cm = max(df["Position mm"].max() / 10.0 for df, _ in dfs.values())
    cm_lo, cm_hi = st.slider(
        "Select Centimeter Range",
        0.0,
        float(round(max_cm, 1)),
        (0.0, float(round(max_cm, 1))),
        step=0.1,
    )

    # Fixed buffer
    y_buffer = 5

    # Color assignment
    prefixes = sorted({name.split("_")[0] for name in dfs.keys()})
    st.subheader("Assign Colors to Groups")
    color_map = {}
    for idx, prefix in enumerate(prefixes):
        key = f"color_{prefix}"
        options = [f"{emoji} {name}" for name, _, emoji in COLOR_BANK]
        default_idx = idx % len(COLOR_BANK)
        choice = st.radio(
            f"{prefix}",
            options,
            index=default_idx,
            key=key,
            horizontal=True,
        )
        selected_name = choice.split(" ", 1)[1]
        hex_code = next(h for name, h, _ in COLOR_BANK if name == selected_name)
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
                path,
                results,
                save_dir=None,
                cm_lo=cm_lo,
                cm_hi=cm_hi,
                y_max=y_max,
                suffix="",
            )
            # Override figure title to filename
            try:
                fig.suptitle(label)
            except Exception:
                try:
                    fig.axes[0].set_title(label)
                except Exception:
                    pass
            st.subheader(label)
            st.pyplot(fig)

    # Combined average plot by cycle number
    if st.button("Generate Combined Average Plot"):
        combined_fig = go.Figure()
        for label, (df, path) in dfs.items():
            results = process_file(path, cm_lo, cm_hi)
            if not results:
                continue
            # Use cycle index (1-based) instead of position
            avgs = [r[0] for r in results]
            cycles = list(range(1, len(avgs) + 1))
            prefix = label.split("_")[0]
            clr = color_map[prefix]
            combined_fig.add_trace(
                go.Scatter(
                    x=cycles,
                    y=avgs,
                    mode="lines+markers",
                    name=label,
                    line=dict(color=clr, width=2),  # slightly thicker
                    marker=dict(color=clr),
                )
            )
        combined_fig.update_layout(
            title="Combined Average Force vs Cycle",
            xaxis_title="Cycle Number",
            yaxis_title="Average Force (g)",
            yaxis=dict(range=[0, None]),
        )
        st.plotly_chart(combined_fig, use_container_width=True)

    # NEW: Combined peak plot by cycle number
    if st.button("Generate Combined Peak Plot"):
        combined_peak_fig = go.Figure()
        for label, (df, path) in dfs.items():
            results = process_file(path, cm_lo, cm_hi)
            if not results:
                continue
            # Use cycle index (1-based) instead of position
            peaks = [r[1] for r in results]  # r[1] = peak force
            cycles = list(range(1, len(peaks) + 1))
            prefix = label.split("_")[0]
            clr = color_map[prefix]
            combined_peak_fig.add_trace(
                go.Scatter(
                    x=cycles,
                    y=peaks,
                    mode="lines+markers",
                    name=label,
                    line=dict(color=clr, width=2),
                    marker=dict(color=clr),
                )
            )
        combined_peak_fig.update_layout(
            title="Combined Peak Force vs Cycle",
            xaxis_title="Cycle Number",
            yaxis_title="Peak Force (g)",
            yaxis=dict(range=[0, None]),
        )
        st.plotly_chart(combined_peak_fig, use_container_width=True)

# Ensure `plotly` in requirements.txt
