import numpy as np
import json
from castadi import scripter as s, drawn as d
from ast import literal_eval


def save_encoded_image(img: str, output_path: str):
    """
    Save the given image to the given output path.
    """
    with open(output_path, "wb") as image_file:
        image_file.write(img)


def parse_color(color):
    color = color.strip()
    if color.startswith("(") and color.endswith(")"):
        return literal_eval(color)
    return color


def parse_bubble(bjs, default_bubble=(None, None, None, None)):
    if bjs is None:
        return (None,) * 4
    return (
        bjs.get("font_size", default_bubble[0]),
        parse_color(bjs.get("bubble_color", str(default_bubble[1]))),
        parse_color(bjs.get("text_color", default_bubble[2])),
        bjs.get("font", default_bubble[3]),
    )


def get_settings(json_data):
    settings = {}

    settings["canvas_size"] = (
        json_data.get("canvas_width", 480),
        json_data.get("canvas_height", 854),
    )

    settings["panel_min_percent"] = (
        json_data.get("panel_min_width_percent", 0.21),
        json_data.get("panel_min_height_percent", 0.117),
    )

    settings["image_zoom"] = eval(json_data.get("image_zoom", "1"))

    settings["default_bubble"] = parse_bubble(json_data.get("default_bubble"))

    settings["outline_width"] = json_data.get("border_width", 5)

    settings["prompt_prefix"] = json_data.get("prompt_prefix", "")
    settings["negative_prompt"] = json_data.get("negative_prompt", "")

    settings["embeds"] = json_data.get("embeds", {"characters": {}, "concepts": {}})
    character_data = settings["embeds"].get("characters", {})
    settings["embeds"]["concepts"] = settings["embeds"].get("concepts", {})

    characters = {}
    for character in character_data:
        c = character_data[character]
        bubble = parse_bubble(c.get("bubble", None), settings["default_bubble"])
        if bubble is None:
            bubble = settings["default_bubble"]
        characters[character] = s.Character(character, c["tags"], bubble)

    settings["embeds"]["characters"] = characters

    return settings


def generate(script, raw_settings, draw=True, location=None, last_script=None):
    settings = get_settings(json.loads(raw_settings) if draw else raw_settings)
    script = s.script(script, settings["embeds"]["concepts"])

    loc_page, loc_panel = None, None

    if location is not None and last_script is not None:
        loc_page, loc_panel = location
        script = [
            old_page.update(new_page, settings)
            for old_page, new_page in zip(last_script, script)
        ]

    names, results = [], []
    new_script = []

    if draw:
        for i, page in enumerate(script):
            if not isinstance(page, d.DrawnPage):
                page = d.DrawnPage(page, settings)

            new_names, new_results = page.draw(
                settings, panel=loc_panel if i == loc_page else None
            )
            new_script.append(page)
            names.extend(new_names)
            results.extend(new_results)

        return names, results, new_script
    else:
        return [
            panel.bake(settings["embeds"]["characters"])
            for page in script
            for panel in page.panels
        ]


if __name__ == "__main__":
    with open("example/settings.json") as file:
        raw_settings = file.read()

    text = """\
-Page1(min: 0.4, 0.4)
location: space, galaxy

[misty] flying
"heyy"

[misty] landing
"yooo"
"""

    text2 = """\
-Page1(min: 0.4, 0.4)
location: space, galaxy

[misty] flying
"heyy"

[bea] flying
"yooo"
"""

    names, results, new_script = generate(text, raw_settings)
    results[-1].show()
    names, results, new_script = generate(
        text2, raw_settings, location=(0, 1), last_script=new_script
    )
    results[-1].show()
