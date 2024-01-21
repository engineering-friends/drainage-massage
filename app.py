import streamlit as st
# from clarifai.client.auth import create_stub
# from clarifai.client.auth.helper import ClarifaiAuthHelper
from clarifai.modules.css import ClarifaiStreamlitCSS
from dotenv import load_dotenv

from backend.main import process_image

load_dotenv()

# st.set_page_config(layout="wide")

ClarifaiStreamlitCSS.insert_default_css(st)

# st.markdown("Please select a specific page from the sidebar to the left")

# image = None
# step 1, option 1: upload file
image = st.sidebar.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

# step 1, option 2: paste url

# step 2: process file, display text

if image is not None:
    with st.spinner("Thinking..."):
        text = process_image(image)
    st.text(text)
