import json
import os

import streamlit as st
from clarifai.modules.css import ClarifaiStreamlitCSS
from dotenv import load_dotenv

from backend.main import process_image

load_dotenv()


st.set_page_config(layout="wide")

# st.title("Snap, List, Sell!")
st.write("Our app instantly crafts the perfect listing for your item. Just upload a photo, and we'll generate a catchy title, engaging description, and tailored text for your marketplace sale. Selling made simple!")
st.sidebar.title("Snap, List, Sell!")
# st.sidebar.write("Sidebar description placeholder")

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


def parse_text(text):
    keys = ["Title", "Description", "Tags"]
    for k in keys:
        assert f"**{k}**:" in text, f"Could not find {k} in text"
    assert text.index("**Title**:") < text.index("**Description**:") < text.index(
        "**Tags**:"), "Text is not in expected format"

    title = text[
            text.index("**Title**:") + len("**Title**:"):text.index("**Description**:")]
    description = text[
                  text.index("**Description**:") + len("**Description**:"):text.index(
                      "**Tags**:")]
    tags = text[text.index("**Tags**:") + len("**Tags**:"):]

    # parse tags
    # tags = """```json
    # { k: v} ```"""
    tags = tags[tags.index("```json") + len("```json"):tags.rindex("```")]
    tags = json.loads(tags)

    return title, description, tags


results_dir = Path("requests")
results_dir.mkdir(exist_ok=True)


def save_results(image, text, request_id, image_format="png"):
    # timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target_dir = results_dir / request_id
    target_dir.mkdir(exist_ok=True)

    # save image
    image_path = target_dir / f"image.{image_format}"
    with open(image_path, "wb") as f:
        f.write(image)

    # save text
    text_path = target_dir / "text.txt"
    with open(text_path, "w") as f:
        f.write(text)


def generate_request_id():
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return timestamp


if image is not None:
    # generate request_id
    request_id = generate_request_id()
    # save results to app state
    if "requests" not in st.session_state.keys():
        st.session_state.requests = {request_id: {"image": image}}

    image_data = image.read()
    st.image(image_data)
    with st.spinner("Generating compelling description for provided image..."):
        text = process_image(image_data)
        st.session_state.requests[request_id]["text"] = text

    # save results to disk
    if os.getenv("SAVE_RESULTS"):
        save_results(image_data, text, request_id,
                     image_format=image.name.split(".")[-1])

    # show results
    try:
        st.markdown(text)
    except Exception as e:
        print("Could not parse text, error:", e)
        st.text(text)
