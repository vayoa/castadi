import modules.scripts as scripts
import gradio as gr
from castadi import main_runner as mr, drawn as d

from modules import script_callbacks

DEFAULT_SETTINGS = r"""
{
  "canvas_width": 1080,
  "canvas_height": 1920,

  // The default min size a panel would have.
  // based on the percentage of the page size
  "panel_min_width_percent": 0.21,
  "panel_min_height_percent": 0.117,

  // The ratio of panel generation.
  // For example 1 would mean that if a panel is 1080x960 it would
  // be generated at that resulotion. If you don't have enough vram keep it low.
  "image_zoom": "4/9",
  "border_width": 5,
  "default_bubble": {
    "font_size": 16,
    "bubble_color": "(20, 20, 20)",
    "text_color": "white",
    "font": "C:\\Windows\\Fonts\\Arial.ttf"
  },

  "prompt_prefix": "(masterpiece, best quality:1.1)",
  "negative_prompt": "(bad quality, low quality:1.1)"

  // "embeds": {
  //   "concepts" : {
  //   here is an example concept:
  //   "spysuit": "black spy suit, tech"
  //   },
  //   "characters": {
  //     here is an example character:
  //     "character_name": {
  //       "tags": "guy, male, short black hair, white pants, white shirt",
  //       "bubble": {
  //         "bubble_color": "(200, 200, 200)",
  //         "text_color": "black"
  //       }
  //     }
  //   }
  // }
}
"""
DEFAULT_SCRIPT = """\
Your script, example:
-Page1

location: public park, yard, outside, park

[misty] weaving, saying hey, happy, smiling
"Heyy!!"

"This is an example"
"of what castadi can do!"

[misty] curious, surpries, happy, question
"What do you think?"
"""


def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as ui_component:
        last_script = gr.State({})
        with gr.Row():
            with gr.Tab("Script"):
                script = gr.TextArea(
                    lines=20,
                    label="start with --api for this extension to work.",
                    placeholder=DEFAULT_SCRIPT,
                )

            with gr.Tab("Settings"):
                settings = gr.Code(
                    language="json",
                    lines=20,
                    show_label=False,
                    value=DEFAULT_SETTINGS,
                )

            with gr.Column():
                with gr.Row():
                    btn = gr.Button("Generate", variant="primary")
                    page = gr.Number(label="Page", percision=0, minimum=1)
                    panel = gr.Number(label="Panel", percision=0, minimum=1)
                    chk = gr.Checkbox(label="Full Page", value=True)

                gallery = gr.Gallery(
                    label="Dummy Image",
                    show_label=False,
                    object_fit="cover",
                )

        btn.click(
            generate,
            inputs=[script, last_script, settings, chk, page, panel],
            outputs=[gallery, last_script],
        )

        return [(ui_component, "Castadi", "castadi_tab")]


def remove_json_comments(json):
    return "\n".join([l for l in json.split("\n") if not l.strip().startswith("//")])


def generate(script, last_script, settings, chk, page, panel):
    if script and settings:
        if chk:
            last_script, location = None, None
        else:
            last_script, location = d.script_from_dict(last_script), (page, panel)

        settings = remove_json_comments(settings)
        _, results, new_script = mr.generate(
            script,
            settings,
            last_script=last_script,
            location=location,
        )
        return [results, d.script_to_dict(new_script)]
    else:
        return [[], {}]


script_callbacks.on_ui_tabs(on_ui_tabs)
