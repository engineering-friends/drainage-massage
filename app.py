from dotenv import load_dotenv
load_dotenv()
import os
# from PIL import Image
import streamlit as st
# from clarifai.client.auth import create_stub
# from clarifai.client.auth.helper import ClarifaiAuthHelper
from clarifai.modules.css import ClarifaiStreamlitCSS

from backend.main import process_image


# st.set_page_config(layout="wide")

ClarifaiStreamlitCSS.insert_default_css(st)

# st.markdown("Please select a specific page from the sidebar to the left")

# image = None
# step 1, option 1: upload file
image = st.sidebar.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

# step 1, option 2: paste url

# step 2: process file, display text

# hack: save .env if it doesn't exist
from pathlib import Path
p = Path(".env")
if not p.exists():
    msg = ""
    for k in ["CLARIFAI_USER_ID", "CLARIFAI_PAT", "CLARIFAI_APP_ID"]:
        v = os.getenv(k)
        if v is not None:
            msg += f"{k}={v}\n"
    p.write_text(msg)

if image is not None:
    # print(dir(image))
    image_data = image.read()
    st.image(image_data)
    with st.spinner("Thinking..."):
        text = process_image(image_data)
    st.text(text)
