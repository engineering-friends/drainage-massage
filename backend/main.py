# from dotenv import load_dotenv
# load_dotenv()
# import time
# use clarifai
import base64
import os.path
import re
from typing import Union, List

from clarifai.client.input import Inputs
from clarifai.client.model import Model
from dotenv import load_dotenv
#
load_dotenv()
def load_dotenv_backup():
    from pathlib import Path
    p = Path(".env")
    data = p.read_text()
    env = dict(re.findall(r"(\w+)=(.*)", data))
    for k, v in env.items():
        if v:
            os.environ[k] = v

def trim_extra_whitespace(text):
    # Replace multiple spaces with a single space
    text = re.sub(r" +", " ", text)

    # Replace combinations of newlines and spaces with newlines only
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)

    # Replace more than two consecutive newlines with two newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


# model_urls = {
#     "basic": "https://clarifai.com/openai/chat-completion/models/GPT-3_5-turbo",
#     "mid": "https://clarifai.com/openai/chat-completion/models/gpt-4-turbo",
#     "smart": "https://clarifai.com/openai/chat-completion/models/GPT-4",
#     "vision": "https://clarifai.com/openai/chat-completion/models/openai-gpt-4-vision",
# }
#
# clarifai_basic_llm = Clarifai(model_url=model_urls["basic"])
# clarifai_mid_llm = Clarifai(model_url=model_urls["mid"])
# clarifai_smart_llm = Clarifai(model_url=model_urls["smart"])
# clarifai_vision_llm = Clarifai(model_url=model_urls["vision"])


def convert_prompt(prompt):
    if isinstance(prompt, list):
        single_text = ""
        for p in prompt:
            if isinstance(p, str):
                single_text += p + "\n\n"
            else:
                single_text += p[-1] + "\n\n"
        prompt = trim_extra_whitespace(
            single_text
        )  # Cause clarifai doesn't support list of prompts or system prompts or anything chat
    return prompt


def ask_clarifai_text(
        model_shortname: str,
        full_prompt: Union[str, List[str]],
        inference_params=None,
):
    if inference_params is None:
        inference_params = {"temperature": 0.2, "max_tokens": 1024}

    full_prompt = convert_prompt(full_prompt)

    model_urls = {
        "basic": "https://clarifai.com/openai/chat-completion/models/GPT-3_5-turbo",
        "mid": "https://clarifai.com/openai/chat-completion/models/gpt-4-turbo",
        "smart": "https://clarifai.com/openai/chat-completion/models/GPT-4",
        # "vision": "https://clarifai.com/openai/chat-completion/models/openai-gpt-4-vision",
    }
    load_dotenv_backup()
    res = (
        Model(model_urls[model_shortname])
        .predict_by_bytes(
            trim_extra_whitespace(full_prompt).encode(), input_type="text",
            inference_params=inference_params
        )
        .outputs[0]
        .data.text.raw
    )

    return res


def ask_clarifai_vision(
        image: Union[bytes, str],
        prompt: Union[str, List[str]],
        inference_params=None,
):
    # - Get image url or bytes

    prompt = convert_prompt(prompt)

    if inference_params is None:
        inference_params = {"temperature": 0.2, "max_tokens": 100}
    image_url = None
    image_bytes = None

    if isinstance(image, bytes):
        image_bytes = image
    elif isinstance(image, str):
        if os.path.exists(image):
            image_bytes = open(image, "rb").read()
        else:
            # url
            if image.startswith("http"):
                image_url = image
            elif image.startswith("data:image"):
                # - Convert base64 like "data:image/png;base64,<base64> to bytes
                image_bytes = base64.b64decode(image.split("base64,")[1])
            else:
                raise ValueError(f"Unknown image format: {image}")

    # - Ask clarifai
    load_dotenv_backup()
    # os.environ["CLARIFAI_PAT"] = env["CLARIFAI_PAT"]
    # print("listdir", os.listdir("."))
    # print("CALMMAGE api key:", os.getenv("CLARIFAI_API_KEY"))
    # print("CALMMAGE PAT:", os.getenv("CLARIFAI_PAT"))
    res = (
        Model("https://clarifai.com/openai/chat-completion/models/openai-gpt-4-vision")
        .predict(
            inputs=[
                Inputs.get_multimodal_input(
                    input_id="",
                    image_url=image_url,
                    image_bytes=image_bytes,
                    raw_text=prompt,
                )
            ],
            inference_params=inference_params,
        )
        .outputs[0]
        .data.text.raw
    )

    return res


def get_general_description(image_bytes):
    role_message = """You are a detailed-oriented assistant. Your task is to analyze photographs of items provided by users, who wish to sell these items on online marketplaces like eBay or Craigslist. Your role is to describe these items in great detail, focusing on their characteristics, condition, and any unique features. Your descriptions should be rich and comprehensive, enabling users to search using various keywords. You should also include a price estimate for the item."""

    prompt_message = """Here's a photograph of an item I'm planning to sell online. Please provide a detailed description of the item."""

    full_prompt = [role_message, prompt_message]

    description = ask_clarifai_vision(image_bytes, full_prompt)
    return description


def get_item_title(item_description):
    role_message = """You are an assistant skilled in crafting succinct, keyword-focused titles for items being listed on online marketplaces. Your task is to create titles that are attractive and informative, highlighting key features like brand and condition in a brief format."""

    prompt_message = (
        '''Create a title for this item suitable for an online marketplace listing:\n\n"""\n{item_description}\n"""'''
    )

    full_prompt = [role_message,
                   prompt_message.format(item_description=item_description)]

    title = ask_clarifai_text("basic", full_prompt)
    return title


def get_marketplace_description(item_description):
    role_message = """Selective Editor: In this role, your primary task is to filter and refine original item descriptions for casual online marketplaces like Facebook Marketplace or Craigslist. You should focus on maintaining a straightforward, honest tone, akin to a regular person's description. Emphasize the positive aspects but avoid pretentious language. Crucially, omit irrelevant details do not belong to the descriptions, like unknown brands or pricing. Your goal is to create a description that highlights the item's best features in a simple, appealing way, using only the most relevant information from the original description."""

    prompt_message = '''Refine the following detailed description into a marketplace-friendly format:\n\n"""\n{item_description}\n"""'''

    example_input = """This photograph displays a pair of used Nike Air Max 90 sneakers. The sneakers are primarily white, a colorway that is versatile and popular. The Air Max 90 is known for its classic design and comfort, featuring the distinctive Nike Air cushioning visible in the heel.

    Key features to note in the description:

    - Brand and Model: Nike Air Max 90
    - Color: White
    - Size: Not specified (potential buyers would need this information)
    - Upper Material: Appears to be a combination of leather and synthetic materials, as is common with this model
    - Sole: Classic Air Max 90 sole with signature air bubble in the heel
    - Condition: The sneakers show signs of wear. There is visible yellowing on the plastic air bubble windows and the midsole, typical for vintage or used white sneakers. The outsole shows dirt and wear, particularly in the heel area. The upper seems to be in good condition with no apparent tears or separations, although there might be slight creasing.
    - Laces: Original white laces seem to be present, no visible damage.

    Unique features to highlight:

    - The Nike Air Max 90 is a timeless style with a strong following amongst sneaker enthusiasts.
    - The all-white colorway offers a clean look that can complement a variety of outfits.

    For a price estimate, the value of used sneakers varies greatly depending on their condition, rarity, and demand. Given the visible wear, these would be on the lower end of the price range for this model. Without original packaging and depending on the exact size and market conditions, a pair like this could potentially sell for around $40-$80 on platforms like eBay or Craigslist. Please note that this is a rough estimate and prices can fluctuate. It's recommended to check current listings for similar used Air Max 90 sneakers to set a competitive price."""

    example_result = """Up for sale is a classic pair of Nike Air Max 90 sneakers. These iconic shoes feature a clean, all-white colorway that's perfect for various styles. Noted for their legendary comfort, they include the signature Nike Air cushioning in the heel.

    Key Points:
    - Make: Nike Air Max 90
    - Color: White
    - Upper Material: Leather and synthetic blend
    - Sole: Air Max 90 style with air bubble in the heel
    - Condition: Gently used with some wear. The plastic air bubble windows and midsole show some yellowing, common in vintage sneakers. The sole has signs of use, especially in the heel, but the upper is well-maintained with minimal creasing.
    - Laces: Original white, intact.

    These sneakers are a must-have for anyone who loves timeless footwear. Their versatile look makes them an excellent addition to any wardrobe."""

    warmup_messages = [
        ("human", prompt_message.format(**{"item_description": example_input})),
        ("ai", example_result)]

    full_prompt_template = [
        ("system", role_message),
        *warmup_messages,
        ("human", prompt_message.format(**{"item_description": item_description})),
    ]

    marketplace_description = ask_clarifai_text("mid", full_prompt_template)
    return marketplace_description


def get_taxonomy_base(item_description):
    role_message = """Taxonomy Classifier: In this role, you are responsible for identifying the appropriate category for items and outlining the structure of its taxonomy. Focus on determining the category based on the item description and then define what attributes should be included in its taxonomy, according to standards of major online retailers.
    **Example Return:**
    "For a pair of sneakers, the return might look like:
    ```json
    {{
      "category": "Footwear",
      "taxonomy": {{
        "Attributes": ["Brand", "Model", "Size", "Color", "Material", "Condition"]
      }}
    }}
    ```"""

    prompt_message = (
        '''Assign a category and suggest a taxonomy structure for this item:\n\n"""\n{item_description}\n"""'''
    )

    full_prompt_template = [
        ("system", role_message),
        ("human", prompt_message.format(item_description=item_description)),
    ]
    taxonomy_base = ask_clarifai_text("basic", full_prompt_template)
    return taxonomy_base


def get_taxonomy(item_description,
                 taxonomy_base):  # ToDo prune nulls from json, if no price -- random price
    role_message = """Taxonomy Completer: Your specific task is to fill in the values for provided taxonomy attributes based on the item description. If sufficient information for an attribute is not available in the description, assign 'null' to that attribute. Regardless of the taxonomy provided, always include and fill the 'price' attribute with an exact USD value. Your output should be a JSON object where each taxonomy attribute is paired with its corresponding value or 'null'. Do not include any other fields.
    For instance, for taxonomy like
    ```json
    {{
      "category": "Footwear",
      "Attributes": ["Brand", "Model", "Color", "Material", "Price"]
    }}

    ```

    an example return would be:

    ```json
    {{
      "Brand": "Nike",
      "Model": "Air Max 90",
      "Color": "White",
      "Material": "Leather",
      "Price": 50
    }}
    ```
    """

    prompt_message = '''Based on the item description, complete the following taxonomy attributes, ensuring to include and fill the 'price' attribute:

    **Taxonomy**
    ```json
    {taxonomy_base}
    ```

    **Description**
    """
    {item_description}
    """
    '''.strip()

    full_prompt_template = [
        ("system", role_message),
        ("human", prompt_message.format(item_description=item_description,
                                        taxonomy_base=taxonomy_base)),
    ]
    taxonomy = ask_clarifai_text("basic", full_prompt_template)
    return taxonomy


def process_image(image_bytes):
    """
    Would've been a nice chain, even with some parallelism, but clarifai butchers chat prompts.
    So forced to hack, and for single flow with no streaming, this is enough.
    """
    general_description = get_general_description(image_bytes)
    item_title = get_item_title(general_description)
    marketplace_description = get_marketplace_description(general_description)
    taxonomy_base = get_taxonomy_base(general_description)
    taxonomy = get_taxonomy(general_description,
                            taxonomy_base)  # Was planning to do it with image,
    # but clarifai's requests are 30-40s when opneai's are 5-10s, so it's not worth it

    display_text = f"""
    **Title**: {item_title}

    **Description**:\n {marketplace_description}

    **Tags**:\n {taxonomy}     
    """
    display_text = trim_extra_whitespace(display_text)
    return display_text


# def test():
#     image_path = """../../resource/image_examples/avito_013.webp"""
#     image_bytes = open(image_path, "rb").read()
#     return process_image(image_bytes)


# if __name__ == "__main__":
#     print(test())


# def process_image(image_base64) -> str:
#     #  "https://www.clarifai.com/img/metro-north.jpg"
#     # time.sleep(40)
#     time.sleep(5)
#     name = image_base64.name
#     return f"This is a placeholder text for {name}"
