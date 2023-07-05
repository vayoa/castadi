import base64
import cv2
import numpy as np
import json
import uuid
from castadi import scripter as s, image_generator as ig, panel_generator as pg
from ast import literal_eval


def save_encoded_image(img: str, output_path: str):
    """
    Save the given image to the given output path.
    """
    with open(output_path, "wb") as image_file:
        image_file.write(img)


def get_images(panels, panels_script, embeds, image_zoom,
               prompt_prefix=None, negative_prompt=None, page_id='0',
               controlnet_payload=None):
    images = []
    for i, (panel, panel_script) in enumerate(zip(panels, panels_script)):
        x, y, width, height = panel
        baked = panel_script.bake(embeds)
        width = int(width * image_zoom)
        height = int(height * image_zoom)
        print(
            f'drawing panel {i}, size {width}x{height} location ({x},{y})...')
        img = ig.generate(
            prompt=prompt_prefix + baked,
            negative_prompt=negative_prompt or "",
            width=width,
            height=height,
            controlnet_payload=controlnet_payload
        )
        print('done panel')
        images.append(img)
        # save_encoded_image(img, f'output/panels/{page_id}-{i}.png')
    return images


def parse_color(color):
    color = color.strip()
    if color.startswith('(') and color.endswith(')'):
        return literal_eval(color)
    return color


def parse_bubble(bjs, default_bubble=(None, None, None, None)):
    if bjs is None:
        return (None, ) * 4
    return (bjs.get('font_size', default_bubble[0]),
            parse_color(bjs.get('bubble_color', str(default_bubble[1]))),
            parse_color(bjs.get('text_color', default_bubble[2])),
            bjs.get('font', default_bubble[3]))


def generate(raw_script, raw_settings):
    json_data = json.loads(raw_settings)

    canvas_size = json_data.get(
        'canvas_width', 480), json_data.get('canvas_height', 854)

    panel_min_percent = json_data.get("panel_min_width_percent", 0.21), json_data.get(
        "panel_min_height_percent", 0.117)

    image_zoom = eval(json_data.get('image_zoom', '1'))

    default_bubble = parse_bubble(json_data.get('default_bubble'))

    outline_width = json_data.get('border_width', 5)

    prompt_prefix = json_data.get('prompt_prefix', "")
    negative_prompt = json_data.get('negative_prompt', "")

    embeds = json_data.get('embeds', {'characters': {}, 'concepts': {}})
    character_data = embeds.gets('characters', {})
    concepts = embeds.get('concepts', {})
    embeds['characters'] = character_data
    embeds['concepts'] = concepts

    characters = {}
    for character in character_data:
        c = character_data[character]
        bubble = parse_bubble(c.get('bubble', None), default_bubble)
        if bubble is None:
            bubble = default_bubble
        characters[character] = s.Character(character, c['tags'], bubble)

    embeds['characters'] = characters

    script = s.script(raw_script)

    names, results = [], []

    for i, page in enumerate(script):
        panels_script = page.panels
        min_page_panel_size_perc = page.panel_min_percent or panel_min_percent
        min_page_size = (int(canvas_size[0] * min_page_panel_size_perc[0]), int(canvas_size[1] *
                         min_page_panel_size_perc[1]))

        panels = pg.get_panels(len(panels_script), panels=[(0, 0, *canvas_size)],
                               min_size=min_page_size, split_on_width=page.get_splits())
        page_id = str(uuid.uuid4())

        page.prep(characters)
        controlnet = page.mode == 'controlnet'

        canvas = pg.draw_rectangles(
            get_images(panels, panels_script, embeds, image_zoom,
                       prompt_prefix, negative_prompt, page_id) if not controlnet else None,
            panels,
            page.get_dialog() if not controlnet else None,
            reverse=controlnet,
            outline_width=outline_width,
            canvas_size=canvas_size,
            default_font_size=default_bubble[0],
            default_bubble_color=default_bubble[1],
            default_text_color=default_bubble[2],
            default_font=default_bubble[3],
        )

        if controlnet:
            names.append(f'{page_id}-layout.png')
            results.append(canvas.copy())

            # Convert the Pillow image to a NumPy array
            image_array = np.array(canvas)

            # Convert the NumPy array to BGR order (required by cv2)
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

            # Encode the image into PNG format
            _, buffer = cv2.imencode('.png', image_bgr)

            # Convert the image buffer to base64
            img_str = base64.b64encode(buffer).decode('utf-8')

            panel = [(0, 0, *canvas_size)]

            canvas = pg.draw_rectangles(
                None,
                panels,
                page.get_dialog(),
                background=get_images(panel, panels_script, characters, image_zoom,
                                      prompt_prefix, negative_prompt, page_id,
                                      controlnet_payload={
                                          "input_image": img_str,
                                          "module": "none",
                                          "model": "control_v11p_sd15s2_lineart_anime [3825e83e]",
                                          "weight": 2,
                                          "control_mode": 2,
                                      })[0],
                outline_width=outline_width,
                canvas_size=canvas_size,
                default_font_size=default_bubble[0],
                default_bubble_color=default_bubble[1],
                default_text_color=default_bubble[2],
                default_font=default_bubble[3],
            )

        names.append(f'{page_id}.jpg')
        print(f'finished generation {names[-1]}')
        results.append(canvas)

    return names, results
