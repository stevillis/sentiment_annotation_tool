import io
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

SENTIMENT_DICT = {"Positive": 1, "Negative": -1, "Neutral": 0}
REQUIRED_COLUMNS = [
    "review_text",
    "sentiment",
    "predicted_sentiment",
    "predicted_score",
]
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
    st.session_state["pred_current_index"] = st.session_state["pred_go_to_index_input"]


def get_pred_reviews_df(uploaded_file):
    """Read and validate the uploaded CSV file."""
    try:
        pred_reviews_df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

    missing = [col for col in REQUIRED_COLUMNS if col not in pred_reviews_df.columns]
    if missing:
        st.error(f"Missing columns in uploaded file: {', '.join(missing)}")
        return None

    if "reviewed" not in pred_reviews_df.columns:
        pred_reviews_df["reviewed"] = 0

    return pred_reviews_df


def show_sample_table():
    """Display a sample table with required columns."""
    data = [
        {
            "review_text": "Pra mim nenhum! Não tenho o que reclamar da em...",
            "sentiment": -1,
            "predicted_sentiment": 1,
            "predicted_score": 0.713717,
        },
        {
            "review_text": "Aprendizado e valores do empregado",
            "sentiment": -1,
            "predicted_sentiment": 1,
            "predicted_score": 0.988212,
        },
        {
            "review_text": "Pouca preocupação com o bem estar do colaborador",
            "sentiment": -1,
            "predicted_sentiment": 0,
            "predicted_score": 0.970479,
        },
    ]

    st.dataframe(pd.DataFrame(data))


def update_label(pred_reviews_df, new_label):
    """Update the sentiment label and mark as reviewed."""
    pred_current_index = st.session_state["pred_current_index"]

    pred_reviews_df.at[pred_current_index, "sentiment"] = new_label
    pred_reviews_df.at[pred_current_index, "reviewed"] = 1

    st.session_state["pred_reviews_df"] = pred_reviews_df


def show_download_annotated_file(pred_reviews_df, uploaded_file):
    file_name, file_extension = uploaded_file.name.rsplit(".", 1)
    date_time_str = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")

    output_file_name = f"annotated_{file_name}_{date_time_str}.{file_extension}"

    buffer = io.StringIO()
    pred_reviews_df.to_csv(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        label="Download annotated file",
        data=buffer.getvalue(),
        file_name=output_file_name,
        mime="text/csv",
    )


def show_annotation_ui(pred_reviews_df, uploaded_file):
    col_go_to_index, col_new_label, col_update_label = st.columns([1, 2, 1])
    with col_go_to_index:
        st.number_input(
            label="Go to index",
            step=1,
            value=st.session_state["pred_current_index"],
            min_value=0,
            max_value=pred_reviews_df.shape[0] - 1,
            key="pred_go_to_index_input",
            on_change=go_to_index,
        )

    with col_new_label:
        options = list(pred_reviews_df["predicted_sentiment"].unique())
        new_label = st.radio(
            label="New sentiment label",
            options=options,
            key="new_label",
            horizontal=True,
            format_func=get_sentiment_label,
        )

    with col_update_label:
        if st.button("Update label", key="update_label"):
            update_label(pred_reviews_df, new_label)

    col_progress_bar, col_ammount_annotated = st.columns([3, 1])
    with col_progress_bar:
        progress_value = (
            0
            if st.session_state["pred_current_index"] == 0
            else (st.session_state["pred_current_index"] + 1) / pred_reviews_df.shape[0]
        )
        st.progress(progress_value)

    with col_ammount_annotated:
        st.text(
            f"Qty annotated: {pred_reviews_df['reviewed'].sum()}/{pred_reviews_df.shape[0]}"
        )

    with st.container(border=True, height=240):
        if (
            pred_reviews_df.iloc[st.session_state["pred_current_index"]]["reviewed"]
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
            f"{pred_reviews_df.iloc[st.session_state['pred_current_index']]['review_text']}"
        )

    col_current_label, col_predicted_label, col_predicted_score = st.columns(3)
    with col_current_label:
        st.write(
            f"**Current label:** {get_sentiment_label(pred_reviews_df.iloc[st.session_state['pred_current_index']]['sentiment'])}"
        )

    with col_predicted_label:
        st.write(
            f"**Predicted label:** {get_sentiment_label(pred_reviews_df.iloc[st.session_state['pred_current_index']]['predicted_sentiment'])}"
        )

    with col_predicted_score:
        st.write(
            f"**Predicted score:** {pred_reviews_df.iloc[st.session_state['pred_current_index']]['predicted_score']:.4f}"
        )

    show_download_annotated_file(pred_reviews_df, uploaded_file)


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    st.title("Annotate predicted labels")
    st.write("Expected data format:")

    show_sample_table()

    uploaded_file = st.file_uploader(
        label="Upload your reviews CSV", type="csv", label_visibility="hidden"
    )

    if "pred_current_index" not in st.session_state:
        st.session_state["pred_current_index"] = 0

    if uploaded_file is not None:
        if (
            "pred_reviews_df" not in st.session_state
            or st.session_state.get("pred_last_uploaded_file") != uploaded_file
        ):
            pred_reviews_df = get_pred_reviews_df(uploaded_file)
            if pred_reviews_df is not None:
                st.session_state["pred_reviews_df"] = pred_reviews_df
                st.session_state["pred_last_uploaded_file"] = uploaded_file
            else:
                return

        pred_reviews_df = st.session_state["pred_reviews_df"]
        show_annotation_ui(pred_reviews_df, uploaded_file)


if __name__ == "__main__":
    main()
