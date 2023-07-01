import json
import math
import uuid
import scripter as s
import image_generator as ig
import panel_generator as pg
from ast import literal_eval


SCRIPT_FILE = 'example/script.text'
SETTINGS_FILE = 'example/settings.json'


def save_encoded_image(img: str, output_path: str):
    """
    Save the given image to the given output path.
    """
    with open(output_path, "wb") as image_file:
        image_file.write(img)


def get_images(panels, panels_script, characters, image_zoom,
               prompt_prefix=None, negative_prompt=None, page_id='0'):
    images = []
    for i, (panel, panel_script) in enumerate(zip(panels, panels_script)):
        _, _, width, height = panel
        baked = panel_script.bake(characters)
        img = ig.generate(
            prompt=prompt_prefix + baked,
            negative_prompt=negative_prompt or "",
            width=int(math.floor(width * image_zoom)),
            height=int(math.floor(height * image_zoom)),
        )
        images.append(img)
        save_encoded_image(img, f'output/panels/{page_id}-{i}.png')
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


if __name__ == '__main__':

    with open(SETTINGS_FILE, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
        character_data = json_data.get('characters', {})

        canvas_size = json_data.get(
            'canvas_width', 480), json_data.get('canvas_height', 854)

        panel_min_percent = json_data.get("panel_min_width_percent", 0.21), json_data.get(
            "panel_min_height_percent", 0.117)

        image_zoom = eval(json_data.get('image_zoom', '1'))

        default_bubble = parse_bubble(json_data.get('default_bubble'))

        outline_width = json_data.get('border_width', 5)

        prompt_prefix = json_data.get('prompt_prefix', "")
        negative_prompt = json_data.get('negative_prompt', "")

        characters = {}
        for character in character_data:
            c = character_data[character]
            bubble = parse_bubble(c.get('bubble', None), default_bubble)
            if bubble is None:
                bubble = default_bubble
            characters[character] = s.Character(character, c['tags'], bubble)

    with open(SCRIPT_FILE, 'r', encoding='utf-8') as file:
        text = file.read()

    script = s.script(text, characters)

    for i, page in enumerate(script):
        panels_script = page.panels
        min_page_panel_size_perc = page.panel_min_percent or panel_min_percent
        min_page_size = (int(canvas_size[0] * min_page_panel_size_perc[0]), int(canvas_size[1] *
                         min_page_panel_size_perc[1]))

        panels = pg.get_panels(len(panels_script), panels=[(0, 0, *canvas_size)],
                               min_size=min_page_size, split_on_width=page.get_splits())
        page_id = str(uuid.uuid4())
        print(panels)

        canvas = pg.draw_rectangles(
            get_images(panels, panels_script, characters, image_zoom,
                       prompt_prefix, negative_prompt, page_id),
            panels,
            page.get_dialog(),
            outline_width=outline_width,
            canvas_size=canvas_size,
            default_font_size=default_bubble[0],
            default_bubble_color=default_bubble[1],
            default_text_color=default_bubble[2],
            default_font=default_bubble[3],
        )

        canvas.save(f'output/pages/{page_id}.jpg')

    canvas.save('output/preview.jpg')
