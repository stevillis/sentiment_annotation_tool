import io
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

SENTIMENT_DICT = {"Positive": 1, "Negative": -1, "Neutral": 0}
REQUIRED_COLUMNS = ["review_text", "sentiment"]
CUSTOM_CSS = """
<style>
    [data-testid="stApp"] {
        // background-color:red;
    }
    div[data-testid="stHorizontalBlock"] {
        // background-color: yellow;
        align-items: end;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] {
        // background-color: blue;
        display: flex;
        justify-content: end;
    }
    div[data-testid="stElementContainer"] div[data-testid="stText"] {
        // background-color: yellow;
        display: flex;
        justify-content: end;
    }
    .st-as {
        background-color: green;
    }
</style>
"""


def get_sentiment_label(value: int) -> Optional[str]:
    return next((key for key, val in SENTIMENT_DICT.items() if val == value), None)


def go_to_index():
    st.session_state["manual_current_index"] = st.session_state[
        "manual_go_to_index_input"
    ]


def get_manual_reviews_df(uploaded_file):
    """Read and validate the uploaded CSV file."""
    try:
        manual_reviews_df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

    missing = [col for col in REQUIRED_COLUMNS if col not in manual_reviews_df.columns]
    if missing:
        st.error(f"Missing columns in uploaded file: {', '.join(missing)}")
        return None

    if "reviewed" not in manual_reviews_df.columns:
        manual_reviews_df["reviewed"] = 0

    return manual_reviews_df


def show_sample_table():
    """Display a sample table with required columns."""
    data = [
        {
            "review_text": "Pra mim nenhum! Não tenho o que reclamar da em...",
            "sentiment": -1,
        },
        {
            "review_text": "Aprendizado e valores do empregado",
            "sentiment": -1,
        },
        {
            "review_text": "Pouca preocupação com o bem estar do colaborador",
            "sentiment": -1,
        },
    ]
    st.dataframe(pd.DataFrame(data))


def update_label(manual_reviews_df, new_label):
    """Update the annotated sentiment label and mark as reviewed."""
    manual_current_index = st.session_state["manual_current_index"]

    manual_reviews_df.at[manual_current_index, "annotated_sentiment"] = int(new_label)
    manual_reviews_df.at[manual_current_index, "reviewed"] = 1

    st.session_state["manual_reviews_df"] = manual_reviews_df


def show_download_annotated_file(manual_reviews_df, uploaded_file):
    file_name, file_extension = uploaded_file.name.rsplit(".", 1)
    date_time_str = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")

    output_file_name = f"annotated_{file_name}_{date_time_str}.{file_extension}"

    # Create a copy to avoid modifying the original DataFrame
    df_to_download = manual_reviews_df.copy()

    # Ensure annotated_sentiment is int if it exists
    if "annotated_sentiment" in df_to_download.columns:
        df_to_download["annotated_sentiment"] = df_to_download[
            "annotated_sentiment"
        ].astype("Int64")

    buffer = io.StringIO()
    df_to_download.to_csv(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        label="Download annotated file",
        data=buffer.getvalue(),
        file_name=output_file_name,
        mime="text/csv",
    )


def show_annotation_ui(manual_reviews_df, uploaded_file):
    col_go_to_index, col_new_label, col_update_label = st.columns([1, 2, 1])
    with col_go_to_index:
        st.number_input(
            label="Go to index",
            step=1,
            value=st.session_state["manual_current_index"],
            min_value=0,
            max_value=manual_reviews_df.shape[0] - 1,
            key="manual_go_to_index_input",
            on_change=go_to_index,
        )

    with col_new_label:
        options = list(SENTIMENT_DICT.values())
        new_label = st.radio(
            label="New sentiment label",
            options=options,
            key="new_label",
            horizontal=True,
            format_func=get_sentiment_label,
        )

    with col_update_label:
        if st.button("Update label", key="update_label"):
            update_label(manual_reviews_df, new_label)

    col_progress_bar, col_ammount_annotated = st.columns([3, 1])
    with col_progress_bar:
        progress_value = (
            0
            if st.session_state["manual_current_index"] == 0
            else (st.session_state["manual_current_index"] + 1)
            / manual_reviews_df.shape[0]
        )
        st.progress(progress_value)

    with col_ammount_annotated:
        st.text(
            f"Qty annotated: {manual_reviews_df['reviewed'].sum()}/{manual_reviews_df.shape[0]}"
        )

    with st.container(border=True, height=240):
        if (
            manual_reviews_df.iloc[st.session_state["manual_current_index"]]["reviewed"]
            == 1
        ):
            st.write(
                "#### <span style='color: green'>Annotated review text</span>",
                unsafe_allow_html=True,
            )
        else:
            st.write(
                "#### <span style='color: red'>Review text</span>",
                unsafe_allow_html=True,
            )
        st.write(
            f"{manual_reviews_df.iloc[st.session_state['manual_current_index']]['review_text']}"
        )

    col_current_label, col_annotated_label = st.columns(2)
    with col_current_label:
        sentiment = manual_reviews_df.iloc[st.session_state["manual_current_index"]][
            "sentiment"
        ]
        st.write(f"**Original label:** {get_sentiment_label(sentiment)}")

    with col_annotated_label:
        annotated = manual_reviews_df.iloc[
            st.session_state["manual_current_index"]
        ].get("annotated_sentiment", None)
        if pd.isna(annotated):
            st.write("**Annotated label:**")
        else:
            st.write(f"**Annotated label:** {get_sentiment_label(int(annotated))}")

    show_download_annotated_file(manual_reviews_df, uploaded_file)


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    st.title("Manually annotate labels")
    st.write("Expected data format:")

    show_sample_table()

    uploaded_file = st.file_uploader(
        label="Upload your reviews CSV", type="csv", label_visibility="hidden"
    )

    if "manual_current_index" not in st.session_state:
        st.session_state["manual_current_index"] = 0

    if uploaded_file is not None:
        if (
            "manual_reviews_df" not in st.session_state
            or st.session_state.get("manual_last_uploaded_file") != uploaded_file
        ):
            manual_reviews_df = get_manual_reviews_df(uploaded_file)
            if manual_reviews_df is not None:
                st.session_state["manual_reviews_df"] = manual_reviews_df
                st.session_state["manual_last_uploaded_file"] = uploaded_file
            else:
                return

        manual_reviews_df = st.session_state["manual_reviews_df"]
        show_annotation_ui(manual_reviews_df, uploaded_file)


if __name__ == "__main__":
    main()
