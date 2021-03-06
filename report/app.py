import streamlit as st

from inference import inference
from pages import *


def main() -> None:
    st.set_page_config(
        page_title="Face inpainting",
        page_icon="🧑",
        layout="wide",
    )
    pages = {
        "Problem and data": problem,
        "Our approach": approach,
        "Hyperparameters": parameters,
        "Environment": environment,
        "Live demo": inference,
        "Sources": bibliography
    }
    name = st.sidebar.radio('Menu', pages.keys(), index=0)
    pages[name]()

if __name__ == '__main__':
    main()  