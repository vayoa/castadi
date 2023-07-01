import json
import base64
import requests


def submit_post(url: str, data: dict):
    """
    Submit a POST request to the given URL with the given data.
    """
    return requests.post(url, data=json.dumps(data))


def generate(prompt, negative_prompt="", sampler_name="DPM++ 2M SDE Karras",
             batch_size=1, steps=30, cfg_scale=7.5, width=512, height=512,
             controlnet_payload=None):
    txt2img_url = 'http://127.0.0.1:7860/sdapi/v1/txt2img'
    data = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "sampler_name": sampler_name,
        "batch_size": batch_size,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "width": width,
        "height": height
    }

    if controlnet_payload is not None:
        data['alwayson_scripts'] = {"controlnet": {
            "args": [
                controlnet_payload
            ]
        }}

    response = submit_post(txt2img_url, data).json()
    return base64.b64decode(response['images'][0])
