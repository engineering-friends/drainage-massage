import time
def process_image(image_base64) -> str:
    #  "https://www.clarifai.com/img/metro-north.jpg"
    # time.sleep(40)
    time.sleep(5)
    name = image_base64.name
    return f"This is a placeholder text for {name}"
