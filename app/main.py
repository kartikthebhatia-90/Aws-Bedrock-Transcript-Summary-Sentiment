from __future__ import annotations

import pandas as pd
import streamlit as st

from pipeline.run_pipeline import TranscriptPipeline
from storage.sqlite_store import SQLiteStore
from utils.config import APP_DESCRIPTION, APP_TITLE, validate_env
from utils.file_io import load_chat_dataset


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📝",
    layout="wide",
)

st.title(APP_TITLE)
st.caption(APP_DESCRIPTION)

missing_env = validate_env()
if missing_env:
    st.error(f"Missing environment variables: {', '.join(missing_env)}")
    st.stop()

pipeline = TranscriptPipeline()
store = SQLiteStore()

if "dataset_loaded" not in st.session_state:
    st.session_state.dataset_loaded = False
if "dataset_df" not in st.session_state:
    st.session_state.dataset_df = None
if "selected_transcript" not in st.session_state:
    st.session_state.selected_transcript = ""
if "batch_results" not in st.session_state:
    st.session_state.batch_results = None

with st.sidebar:
    st.header("Options")

    show_history_limit = st.number_input(
        "History rows",
        min_value=1,
        max_value=500,
        value=20,
        step=1,
    )

    st.markdown("---")
    st.subheader("Dataset")

    if st.button("Load Chat Dataset.xlsx"):
        try:
            df = load_chat_dataset()
            st.session_state.dataset_df = df
            st.session_state.dataset_loaded = True
            st.success(f"Loaded dataset with {len(df)} rows.")
        except Exception as exc:
            st.error(f"Failed to load dataset: {exc}")

tab1, tab2, tab3 = st.tabs(["Analyze Transcript", "Saved History", "Dataset Tools"])

with tab1:
    st.subheader("Input Transcript")

    default_text = """Hi, I just wanted to check why my order is delayed.
I have been waiting for two weeks and nobody updated me."""

    initial_text = st.session_state.selected_transcript or default_text

    transcript_text = st.text_area(
        "Paste informal chat transcript",
        value=initial_text,
        height=220,
        key="manual_transcript_text",
    )

    if st.session_state.dataset_loaded and st.session_state.dataset_df is not None:
        df = st.session_state.dataset_df
        possible_input_cols = [col for col in df.columns if "input" in col.lower()]

        if possible_input_cols:
            st.markdown("### Use Dataset Row")

            selected_input_col = st.selectbox(
                "Dataset input column",
                options=possible_input_cols,
                key="single_input_col",
            )

            row_index = st.number_input(
                "Dataset row index",
                min_value=0,
                max_value=max(len(df) - 1, 0),
                value=0,
                step=1,
                key="single_row_index",
            )

            if st.button("Use Selected Dataset Row"):
                selected_text = str(df.iloc[int(row_index)][selected_input_col])
                st.session_state.selected_transcript = selected_text
                st.rerun()

    analyze_clicked = st.button("Analyze Transcript", type="primary")

    if analyze_clicked:
        try:
            with st.spinner("Analyzing transcript with Bedrock..."):
                result = pipeline.run(transcript_text)

            st.success("Transcript analyzed successfully.")

            left_col, right_col = st.columns(2)

            with left_col:
                st.markdown("### Classification")
                st.write(f"**Predicted Topic:** {result['predicted_topic']}")
                st.write(f"**Sentiment:** {result['sentiment']}")
                st.write(f"**Priority:** {result['priority']}")
                st.write(f"**Status:** {result['status']}")

            with right_col:
                st.markdown("### Record Info")
                st.write(f"**Record ID:** {result.get('id', '')}")
                st.write(f"**Created At:** {result.get('created_at', '')}")

            st.markdown("### Formal Summary")
            st.write(result["formal_summary"])

            st.markdown("### Recommended Action")
            st.write(result["recommended_action"])

            with st.expander("View Cleaned Raw Chat"):
                st.write(result["raw_chat"])

            st.markdown("### JSON Output")
            st.json(result)

        except Exception as exc:
            st.error(f"Pipeline failed: {exc}")

with tab2:
    st.subheader("Saved Transcript History")

    try:
        history = store.fetch_all_results(limit=int(show_history_limit))

        if not history:
            st.info("No saved records found yet.")
        else:
            history_df = pd.DataFrame(history)
            st.dataframe(history_df, use_container_width=True)

            csv_data = history_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download History as CSV",
                data=csv_data,
                file_name="transcript_history.csv",
                mime="text/csv",
            )

    except Exception as exc:
        st.error(f"Failed to load history: {exc}")

with tab3:
    st.subheader("Dataset Tools")

    if not st.session_state.dataset_loaded or st.session_state.dataset_df is None:
        st.info("Load the dataset from the sidebar first.")
    else:
        df = st.session_state.dataset_df
        st.write(f"Rows: {len(df)} | Columns: {len(df.columns)}")
        st.dataframe(df.head(20), use_container_width=True)

        possible_input_cols = [col for col in df.columns if "input" in col.lower()]

        if not possible_input_cols:
            st.warning("No input-like column found in dataset.")
        else:
            st.markdown("### Batch Analysis")

            batch_input_col = st.selectbox(
                "Batch input column",
                options=possible_input_cols,
                key="batch_input_col",
            )

            batch_size = st.slider(
                "Number of rows to analyze",
                min_value=1,
                max_value=min(len(df), 20),
                value=min(len(df), 5),
                step=1,
            )

            if st.button("Run Batch Analysis"):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    for i in range(batch_size):
                        raw_text = str(df.iloc[i][batch_input_col])
                        status_text.write(f"Processing row {i + 1} of {batch_size}...")
                        result = pipeline.run(raw_text)
                        result["source_row"] = i
                        results.append(result)
                        progress_bar.progress((i + 1) / batch_size)

                    st.session_state.batch_results = pd.DataFrame(results)
                    status_text.empty()
                    st.success("Batch analysis completed.")

                except Exception as exc:
                    st.error(f"Batch analysis failed: {exc}")

            if st.session_state.batch_results is not None:
                st.markdown("### Batch Results")
                st.dataframe(st.session_state.batch_results, use_container_width=True)

                batch_csv = st.session_state.batch_results.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download Batch Results as CSV",
                    data=batch_csv,
                    file_name="batch_analysis_results.csv",
                    mime="text/csv",
                )